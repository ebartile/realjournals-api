from django.contrib import admin
from .models import User, Role
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from apps.accounts.models import Account, Membership

admin.site.unregister(Group)


class MembershipsInline(admin.TabularInline):
    model = Membership
    fk_name = "user"
    verbose_name = _("Account Member")
    verbose_name_plural = _("Account Members")
    fields = ("account", "role", "invited_by", "is_admin",)
    show_change_link = True
    extra = 0

    # def account_id(self, obj):
    #     return obj.account.id if obj.account else None
    # account_id.short_description = _("id")

    # def account_name(self, obj):
    #     return obj.account.name if obj.account else None
    # account_name.short_description = _("name")

    # def account_slug(self, obj):
    #     return obj.account.slug if obj.account else None
    # account_slug.short_description = _("slug")

    # def account_is_private(self, obj):
    #     return obj.account.is_private if obj.account else None
    # account_is_private.short_description = _("is private")
    # account_is_private.boolean = True

    # def account_owner(self, obj):
    #     if obj.account and obj.account.owner:
    #         return "{} (@{})".format(obj.account.owner.get_full_name(), obj.account.owner.username)
    #     return None
    # account_owner.short_description = _("owner")

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False

class OwnedAccountsInline(admin.TabularInline):
    model = Account
    fk_name = "owner"
    verbose_name = _("Account Ownership")
    verbose_name_plural = _("Account Ownerships")
    fields = ("id", "name", "slug", "is_private")
    read_only_fields = ("id", "name", "slug", "is_private")
    show_change_link = True
    extra = 0

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False


class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username","email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "date_of_birth", "bio", "photo")}),
        (_("Extra info"), {"fields": ("location", "lang", "timezone", "token", "postal_code", "followable","state", "city", "country",
                                      "email_token", "new_email", "verified_email", "accepted_terms", "read_new_terms",
                                      "currency", "continent", "registered_by")}),
        (_("Permissions"), {"fields": ("is_active", "is_superuser", "is_staff", "is_system")}),
        (_("Restrictions"), {"fields": (("max_private_accounts", "max_memberships_private_accounts"),
                                        ("max_public_accounts", "max_memberships_public_accounts", "two_factor_enabled"))}),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "last_seen", "email_verified_at",  )}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

    form = UserChangeForm
    add_form = UserCreationForm
    read_only_fields = ("username", "token", "email_token", "new_email", "last_login", "date_joined", "last_seen", "email_verified_at")
    list_display = ("username", "email", "first_name", "last_name")
    list_filter = ("is_superuser", "is_active", "verified_email")
    search_field = ("email", "first_name", "last_name")
    filter_horizontal = ()
    ordering = ("-date_joined",)
    inlines = [OwnedAccountsInline, MembershipsInline]


admin.site.register(User, UserAdmin)

