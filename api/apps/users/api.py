import uuid
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.utils.translation import gettext_lazy as _
from apps.utils.exceptions import WrongArguments, IntegrityError, NotSupported, NotAuthenticated, BadRequest, Blocked, NotFound
from django.conf import settings
from django.db.models import Q
from .serializers import *
from django.db import transaction as tx
from django.contrib.auth import get_user_model
from apps.utils.mails import mail_builder
from .signals import user_registered as user_registered_signal
from .serializers import UserAdminSerializer
from rest_framework.decorators import action
from .tokens import get_token_for_user
from .models import User, Role
from django.apps import apps
from apps.accounts.permissions import IsAccountAdmin, HasAccountPerm
from . import permissions
from . import filters
from .services import get_user_by_email
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .signals import user_cancel_account as user_cancel_account_signal
from .signals import user_change_email as user_change_email_signal
from .signals import user_verify_email as user_verify_email_signal
from easy_thumbnails.source_generators import pil_image
from django.contrib.auth import login, logout
from .tokens import get_user_for_token
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from apps.utils.pagination import CustomPagination

def get_user_totp_device(self, user, confirmed=None):
    devices = devices_for_user(user, confirmed=confirmed)
    for device in devices:
        if isinstance(device, TOTPDevice):
            return device
        
def is_user_already_registered(*, email:str) -> (bool, str):
    """
    Checks if a specified user is already registred.

    Returns a tuple containing a boolean value that indicates if the user exists
    and in case he does whats the duplicated attribute
    """

    user_model = get_user_model()

    if user_model.objects.filter(email=email):
        return (True, _("Email is already in use."))

    return (False, None)

def send_register_invite(user) -> bool:
    """
    Given a user, send register welcome email
    message to specified user.
    """
    cancel_token = get_token_for_user(user, "cancel_account")
    context = {"user": user, "cancel_token": cancel_token}
    email = mail_builder.invite_user(user, context)
    return bool(email.send())


def send_register_email(user) -> bool:
    """
    Given a user, send register welcome email
    message to specified user.
    """
    cancel_token = get_token_for_user(user, "cancel_account")
    context = {"user": user, "cancel_token": cancel_token}
    email = mail_builder.registered_user(user, context)
    return bool(email.send())

@tx.atomic
def public_register(password:str, email:str, first_name:str, last_name:str, **arg):
    is_registered, reason = is_user_already_registered(email=email)
    if is_registered:
        raise WrongArguments(reason)

    if len(password) < 6:
        raise WrongArguments(_("Invalid password length at least 6 characters needed"))

    user_model = get_user_model()
    user = user_model(email=email,
                      email_token=str(uuid.uuid4()),
                      new_email=email,
                      verified_email=False,
                      first_name=first_name,
                      last_name=last_name,
                      accepted_terms=True,
                      read_new_terms=True)
    user.set_password(password)
    
    try:
        user.save()
    except IntegrityError:
        raise WrongArguments(_("User is already registered."))

    send_register_email(user)
    user_registered_signal.send(sender=user.__class__, user=user)
    return user

def get_membership_by_token(token:str):
    """
    Given a token, returns a membership instance
    that matches with specified token.

    If not matches with any membership NotFound exception
    is raised.
    """
    membership_model = apps.get_model("accounts", "Membership")
    qs = membership_model.objects.filter(token=token)
    if len(qs) == 0:
        raise NotFound(_("Token does not match any valid invitation."))
    return qs[0]

@tx.atomic
def private_register_for_new_user(email:str, first_name:str, last_name:str, registered_by:object):
    """
    Given a inviation token, try register new user matching
    the invitation token.
    """
    is_registered, reason = is_user_already_registered(email=email)
    if is_registered:
        raise WrongArguments(reason)

    user_model = get_user_model()
    user = user_model(email=email,
                      token=str(uuid.uuid4()),
                      new_email=email,
                      verified_email=False,
                      first_name=first_name,
                      last_name=last_name,
                      registered_by=registered_by)
    user.set_password(str(uuid.uuid4().hex))
    
    try:
        user.save()
    except IntegrityError:
        raise WrongArguments(_("User is already registered."))

    send_register_invite(user)
    user_registered_signal.send(sender=user.__class__, user=user)
    return user

@tx.atomic
def accept_invitation_by_existing_user(token:str, user_id:int):
    user_model = get_user_model()
    user = user_model.objects.get(id=user_id)
    membership = get_membership_by_token(token)

    try:
        membership.user = user
        membership.save(update_fields=["user"])
    except IntegrityError:
        raise IntegrityError(_("This user is already a member of the account."))
    return user

class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    # TODO: throttling
    # throttle_classes = (LoginFailRateThrottle, RegisterSuccessRateThrottle)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'register':
            self.serializer_class = PublicRegisterSerializer()
        elif self.action == 'invite':
            self.serializer_class = PrivateRegisterSerializer()
        else:
            self.serializer_class = LoginSerializer()

        return self.serializer_class
    
    @action(detail=False, methods=['POST', 'GET'])
    def logout(self, request, **kwargs):
        logout(request)
        return Response(status=status.HTTP_200_OK)
            
    @action(detail=False, methods=['POST'])
    def register(self, request, **kwargs):
        serializer = PublicRegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)

        if not settings.PUBLIC_REGISTER_ENABLED:
            raise WrongArguments(_("Public registration is disabled."))

        try:
            user = public_register(**serializer.data)
        except IntegrityError as e:
            raise IntegrityError(e.detail)

        serializer = UserAdminSerializer(user)
        data = dict(serializer.data)
        data["auth_token"] = get_token_for_user(user, "authentication")

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        if request.GET.get('redirect', None):
            data["intended"] = request.GET.get('redirect', None)

        return Response(data, status=status.HTTP_201_CREATED)
            
    @action(detail=False, methods=['POST'])
    def invite(self, request, **kwargs):
        serializer = PrivateRegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)  

        data = serializer.data
        data['registered_by'] = request.user
        user = private_register_for_new_user(**data)

        serializer = UserAdminSerializer(user)
        data = dict(serializer.data)
        data["auth_token"] = get_token_for_user(user, "authentication")
        return Response(data, status=status.HTTP_201_CREATED)


    # Login view: /v1/auth
    def create(self, request, **kwargs):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)  

        email = str(serializer.data.get("email", None))
        password = str(serializer.data.get("password", None))
        invitation_token = serializer.data.get("invitation_token", None)

        user_model = get_user_model()
        qs = user_model.objects.filter(Q(email__iexact=email))

        if len(qs) > 1:
            qs = qs.filter(Q(email=email))

        if len(qs) == 0:
            raise WrongArguments(_("Email or password does not match user."))

        user = qs[0]

        if not user.check_password(password):
            raise WrongArguments(_("Email or password does not match user."))

        serializer = UserAdminSerializer(user)
        data = dict(serializer.data)
        data["auth_token"] = get_token_for_user(user, "authentication")

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        if request.GET.get('redirect', None):
            data["intended"] = request.GET.get('redirect', None)

        # if invitation_token is not None:
        #     accept_invitation_by_existing_user(invitation_token, data['id'])

        return Response(data, status=status.HTTP_200_OK)

        
class UsersViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create':
            self.serializer_class = LoginSerializer
        elif self.action == "list" \
            or self.action == "update" \
            or self.action == "partial_update" \
            or self.action == "retrieve":
            if self.request.user.is_authenticated and self.request.user.is_superuser:
                self.serializer_class = UserAdminSerializer
            else:
                self.serializer_class = UserSerializer
        
        return super().get_serializer(*args, **kwargs)

    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            self.permission_classes = (IsAdminUser,)
        elif self.action == "latest_users" \
            or self.action == "total_users" \
            or self.action == "activate" \
            or self.action == "batch_activate" \
            or self.action == "batch_deactivate" \
            or self.action == "registration_chart":
            self.permission_classes = (IsAdminUser,)
        elif self.action == "list" \
            or self.action == "create_totp" \
            or self.action == "verify_totp" \
            or self.action == "stats":
            # TODO: memberships and roles
            self.permission_classes = (IsAuthenticated,)
        elif self.action == "create" \
            or self.action == "change_password" \
            or self.action == "change_avatar" \
            or self.action == "remove_avatar" \
            or self.action == "send_verification_email":
            self.permission_classes = (IsAuthenticated,)
        elif self.action == "retrieve":
            self.permission_classes = (permissions.CanRetrieveUser,)
        elif self.action == "update"  \
            or self.action == "partial_update" \
            or self.action == "destroy":
            self.permission_classes = (permissions.IsTheSameUser,)
        elif self.action == "password_recovery" \
            or self.action == "change_password_from_recovery" \
            or self.action == "change_email" \
            or self.action == "verify_email" \
            or self.action == "cancel":
            self.permission_classes = (AllowAny,)

        return super().get_permissions()
        
    def get_queryset(self):
        qs = super().get_queryset()

        q_parameter = self.request.GET.get("q", None)
        if q_parameter is not None and q_parameter != "":
            qs = qs.filter(Q(email=q_parameter)|Q(first_name=q_parameter)|Q(last_name=q_parameter))
        return qs

    def create(self, *args, **kwargs):
        raise NotSupported(_("Not Supported"))

    def list(self, request, *args, **kwargs):
        # TODO: add membership filter
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        new_email = request.data.pop('email', None)
        if new_email is not None:
            duplicated_email = User.objects.filter(email=new_email).exists()

            if duplicated_email:
                raise WrongArguments(_("Duplicated email"))

            # We need to generate a token for the email
            request.user.email_token = str(uuid.uuid4())
            request.user.new_email = new_email
            request.user.save(update_fields=["email_token", "new_email"])
            email = mail_builder.change_email(
                request.user.new_email,
                {
                    "user": request.user,
                    "lang": request.user.lang
                }
            )
            email.send()
            
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, pk=None):
        user = self.get_object()
        stream = request.stream
        request_data = stream is not None and stream.GET or None
        user_cancel_account_signal.send(sender=user.__class__, user=user, request_data=request_data)
        user.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET', 'POST'])
    def create_totp(self, request, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not user.two_factor_enabled and device:
            # If an existing TOTP device is found, delete it to reset the token
            device.delete()        
        if not device:
            device = user.totpdevice_set.create(confirmed=False)
        return Response({"url": device.config_url}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['POST'])
    def verify_totp(self, request, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not device == None and device.verify_token(request.data.get('token', None)):
            if not device.confirmed:
                device.confirmed = True
                device.save()
            user.two_factor_enabled = True
            user.save(update_fields=["two_factor_enabled"])
            return Response(status=status.HTTP_200_OK)

        raise WrongArguments(_("Invalid, are you sure the six digit code is correct?"))
        
    @action(detail=False, methods=['POST'])
    def password_recovery(self, request, pk=None):
        email = request.data.get('email', None)

        if not email:
            raise WrongArguments(_("Invalid email"))

        user = get_user_by_email(email)
        user.token = str(uuid.uuid4())
        user.save(update_fields=["token"])

        email = mail_builder.password_recovery(user, {"user": user})
        email.send()

        return Response({"detail": _("Mail sent successfully!")}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def change_password_from_recovery(self, request, pk=None):
        """
        Change password with token (from password recovery step).
        """
        serializer = RecoverySerializer(data=request.data, many=False)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(token=serializer.data["token"])
        except User.DoesNotExist:
            raise WrongArguments(_("Token is invalid"))

        user.set_password(serializer.data["password"])
        user.token = None
        user.save(update_fields=["password", "token"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def change_password(self, request, pk=None):
        """
        Change password to current logged user.
        """
        current_password = request.data.get("current_password")
        password = request.data.get("password")

        # NOTE: GitHub users have no password yet (request.user.password == '') so
        #       current_password can be None
        if not current_password and request.user.password:
            raise WrongArguments(_("Current password parameter needed"))

        if not password:
            raise WrongArguments(_("New password parameter needed"))

        if len(password) < 6:
            raise WrongArguments(_("Invalid password length at least 6 characters needed"))

        if current_password and not request.user.check_password(current_password):
            raise WrongArguments(_("Invalid current password"))

        request.user.set_password(password)
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def change_avatar(self, request):
        """
        Change avatar to current logged user.
        """
        avatar = request.FILES.get('file', None)

        if not avatar:
            raise WrongArguments(_("Incomplete arguments"))

        try:
            pil_image(avatar)
        except Exception:
            raise WrongArguments(_("Invalid image format"))

        request.user.photo = avatar
        request.user.save(update_fields=["photo"])
        user_data = self.serializer_class(request.user).data

        return Response(user_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def remove_avatar(self, request):
        """
        Remove the avatar of current logged user.
        """
        request.user.photo = None
        request.user.save(update_fields=["photo"])
        user_data = self.serializer_class(request.user).data
        return Response(user_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def change_email(self, request, pk=None):
        """
        Verify the email change to current logged user.
        """
        serializer = ChangeEmailSerializer(data=request.data, many=False)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email_token=serializer.data["email_token"])
        except User.DoesNotExist:
            raise WrongArguments(_("Invalid, are you sure the token is correct and you "
                                       "didn't use it before?"))

        old_email = user.email
        new_email = user.new_email

        user.email = new_email
        user.new_email = None
        user.email_token = None
        user.verified_email = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email", "new_email", "email_token", "verified_email"])

        user_change_email_signal.send(sender=user.__class__,
                                      user=user,
                                      old_email=old_email,
                                      new_email=new_email)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def verify_email(self, request, pk=None):
        """
        Verify the email to current logged user.
        """
        serializer = ChangeEmailSerializer(data=request.data, many=False)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email_token=serializer.data["email_token"])
        except User.DoesNotExist:
            raise WrongArguments(_("Invalid, are you sure the token is correct and you "
                                       "didn't use it before?"))

        user.email_token = None
        user.verified_email = True
        user.save(update_fields=["email_token", "verified_email"])

        user_verify_email_signal.send(sender=user.__class__,
                                      user=user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def me(self, request, pk=None):
        """
        Get me.
        """
        user_data = self.serializer_class(request.user).data
        return Response(user_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def cancel(self, request, pk=None):
        serializer = CancelAccountSerializer(data=request.data, many=False)
        if not serializer.is_valid():
            raise WrongArguments(_("Invalid, are you sure the token is correct?"))

        try:
            max_age_cancel_account = getattr(settings, "MAX_AGE_CANCEL_ACCOUNT", None)
            user = get_user_for_token(serializer.data["cancel_token"], "cancel_account",
                                      max_age=max_age_cancel_account)

        except NotAuthenticated:
            raise WrongArguments(_("Invalid, are you sure the token is correct?"))

        if not user.is_active:
            raise WrongArguments(_("Invalid, are you sure the token is correct?"))

        user.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def send_verification_email(self, request, pk=None):
        """Send email to verify the user email address."""
        if request.user.verified_email is True:
            raise BadRequest(_("Email address already verified"))
        
        if not request.user.email_token:
            request.user.email_token = str(uuid.uuid4())
            request.user.save(update_fields=["email_token", ])
        
        email = mail_builder.send_verification(request.user, {"user": request.user})
        email.send()
        return Response({"detail": _("Mail sended successful!")}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def latest_users(self, request, *args, **kwargs):
        users = User.objects.filter(is_superuser=False,is_staff=False, is_system=False).order_by('-date_joined')[:10]
        data = UserSerializer(users, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def batch_deactivate(self, request, *args, **kwargs):
        user_ids = request.data.get('users', [])
        users = User.objects.filter(pk__in=user_ids)
        
        for user in users:
            user.is_active = False
            user.save()

        # Serialize the updated users
        serialized_data = UserSerializer(users, many=True).data

        return Response(serialized_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def batch_activate(self, request, *args, **kwargs):
        user_ids = request.data.get('users', [])
        users = User.objects.filter(pk__in=user_ids)
        
        for user in users:
            user.is_active = True
            user.save()

        serialized_data = UserSerializer(users, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'])
    def activate(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        data = UserSerializer(user).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def total_users(self, request, *args, **kwargs):
        total_users = User.objects.filter(is_superuser=False, is_staff=False, is_system=False).count()
        data = {'total': total_users}         
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'])
    def registration_chart(self, request, *args, **kwargs):
        current_date = datetime.now()
        year = request.query_params.get('year', current_date.year)
        month = request.query_params.get('month', current_date.month)        
        start_date = datetime(int(year), int(month), 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        user_stats = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lt=end_date,
            is_superuser=False,
            is_staff=False,
            is_system=False
        ).extra({'date': "TO_CHAR(date_joined, 'YYYY-MM-DD')"}).values('date').annotate(total=Count('id'))

        result = []
        for date in all_dates:
            formatted_date = date.strftime("%Y-%m-%d")
            total = next((entry['total'] for entry in user_stats if entry['date'] == formatted_date), 0)
            result.append({'total': total, 'date': formatted_date})

        data = UserJoinStatsSerializer(result, many=True).data
        return Response(data, status=status.HTTP_200_OK)



######################################################
# Role
######################################################

class RolesViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (IsAccountAdmin,)
    filter_backends = (filters.CanViewAccountFilterBackend,)
    filter_fields = ('account',)

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = (AllowAny,)
        elif self.action == "retrieve":
            self.permission_classes = (HasAccountPerm("view_account"),)

        return super().get_permissions()

    def pre_conditions_blocked(self, obj):
        if obj is not None and self.is_blocked(obj):
            raise Blocked(_("This account is currently blocked"))

    def perform_create(self, serializer):
        obj = serializer.save()
        self.pre_conditions_blocked(obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        self.pre_conditions_blocked(obj)

    def is_blocked(self, obj):
        return obj.account is not None and obj.account.blocked_code is not None

    def pre_delete(self, obj):
        move_to = self.request.query_params.get('moveTo', None)
        if move_to:
            membership_model = apps.get_model("accounts", "Membership")
            role_dest = get_object_or_404(self.model, account=obj.account, id=move_to)
            qs = membership_model.objects.filter(account_id=obj.account.pk, role=obj)
            qs.update(role=role_dest)

        super().pre_delete(obj)

    def perform_destroy(self, instance):
        try:
            self.pre_conditions_blocked(instance)
            self.pre_delete(instance)
            instance.delete()
        except Blocked as e:
            raise Blocked({"detail": str(e)})
        return Response(status=status.HTTP_204_NO_CONTENT)

