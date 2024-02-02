import os
import json
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .pagination import CustomPagination
from rest_framework.decorators import action
from rest_framework import serializers
from .exceptions import WrongArguments
from apps.users.models import User
from django.middleware.csrf import get_token
from apps.users.tokens import get_token_for_user
from apps.users.serializers import UserAdminSerializer
from django.shortcuts import render
from django.views.generic import TemplateView
from apps.settings.models import ThemeSettings
from .models import LogEntry
from .serializers import LogEntrySerializer, LogEntryDataGridSerializer

class ConfigViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        recaptcha_enable = settings.RECAPTCHA_ENABLED
        recaptcha_sitekey = settings.RECAPTCHA_SITEKEY
        recaptcha_size = settings.RECAPTCHA_SIZE

        brand_favicon_url = settings.BRAND_FAVICON_URL
        brand_logo_url = settings.BRAND_LOGO_URL
        brand_support_url = settings.BRAND_SUPPORT_URL
        brand_terms_url = settings.BRAND_TERMS_URL
        brand_policy_url = settings.BRAND_POLICY_URL

        csrf_token = get_token(self.request)
        locales = [{"code": c, "name": n, "bidi": c in settings.LANGUAGES_BIDI} for c, n in settings.LANGUAGES]

        theme = ThemeSettings.objects.first()

        context = {
            'name': 'Real Journals',
            "terminal": settings.LANDING_HOST,
            "api": settings.API_HOST,
            'settings': {
                'layout': theme.layout, 
                'modules': {},
                'windowSize': {
                    'width': 1200,
                    'height': 900
                },
                'recaptcha': {
                    'enable': recaptcha_enable,
                    'sitekey': recaptcha_sitekey,
                    'size': recaptcha_size,
                },
                'locales': locales, 
                'theme': {
                    'mode': theme.mode,
                    'direction': theme.direction,
                    'color': theme.color,
                    'stretch': theme.stretch,
                    'layout': theme.layout
                },
                'brand': {
                    'faviconUrl': brand_favicon_url,
                    'logoUrl': brand_logo_url,
                    'supportUrl': brand_support_url,
                    'termsUrl': brand_terms_url,
                    'policyUrl': brand_policy_url,
                },
                'crsf_token': csrf_token
            }
        }
        
        return Response(context)


class LocalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("lang",)

class LocalesViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    serializer_class = LocalesSerializer

    def create(self, request, *args, **kwargs):
        serializer = LocalesSerializer(data=request.data)
        
        if not serializer.is_valid():
            raise WrongArguments(serializer.errors)

        request.session['locale'] = serializer.data.get("lang", "en")

        if request.user.is_authenticated:
            User.objects.filter(id=request.user.id).update(lang=serializer.data.get("lang"))

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def fetch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            locale = request.user.lang
        else:
            locale = request.session.get('locale', "en")

        messages = {}
        path = os.path.join(os.path.join(settings.BASE_DIR, 'locale'), locale, 'index.json')
        if os.path.exists(path):
            with open(path, 'r') as json_file:
                messages = json.load(json_file)

        return Response(messages, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        locales = [{"code": c, "name": n, "bidi": c in settings.LANGUAGES_BIDI} for c, n in settings.LANGUAGES]
        return Response(locales, status=status.HTTP_200_OK)

class LogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def summary(self, request, *args, **kwargs):
        data = {
            'error': LogEntry.objects.filter(level='ERROR', seen_at=False).count(),
            'warning': LogEntry.objects.filter(level='WARNING', seen_at=False).count(),
            'info': LogEntry.objects.filter(level='INFO', seen_at=False).count(),
            'total': LogEntry.objects.filter(seen_at=False).count(),
        }

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def mark_as_seen(self, request, pk=None):
        log_entry = self.get_object()  # Retrieve the log entry

        if log_entry:
            log_entry.seen_at = True  # Mark the log entry as seen
            log_entry.save()
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['POST'])
    def mark_all_as_seen(self, request):
        LogEntry.objects.update(seen_at=True)
        return Response(status=status.HTTP_200_OK)

