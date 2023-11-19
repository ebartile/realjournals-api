from django.contrib import admin
from .models import Account, Membership, Broker
from apps.users.models import Role
from apps.notifications.admin import NotifyPolicyInline
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.html import format_html
from django.urls import reverse

class MembershipAdmin(admin.ModelAdmin):
    list_display = ['account', 'user']
    list_display_links = list_display
    raw_id_fields = ["account"]

    def has_add_permission(self, request):
        return False

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["user", "invited_by"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__account=self.obj.account)

        elif db_field.name in ["role"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                account=self.obj.account)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # Hack! Hook parent obj just in time to use in formfield_for_foreignkey
        self.parent_obj = obj
        return super(MembershipInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["user", "invited_by"]):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__account=self.parent_obj)

        elif (db_field.name in ["role"]):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                account=self.parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0

class AccountAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "has_be_configured", "slug", "is_private","owner_url",
                    "blocked_code", "is_featured", "created_date"]
    list_display_links = ["id", "name", "slug"]
    list_filter = ("is_private", "blocked_code", "is_featured", "created_date")
    list_editable = ["is_featured", "blocked_code"]
    search_fields = ["id", "name", "slug", "owner__username", "owner__email", "owner__full_name"]
    inlines = [RoleInline,
               MembershipInline,
               NotifyPolicyInline]

    fieldsets = (
        (None, {
            "fields": ("name",
                       "slug",
                       "is_featured",
                       "has_be_configured",
                       "description",
                       "logo",
                       ("created_date",))
        }),
        (_("Privacy"), {
            "fields": (("owner", "blocked_code"),
                       "is_private",
                       ("anon_permissions", "public_permissions"),
            )
        })
    )

    def owner_url(self, obj):
        if obj.owner:
            url = reverse('admin:{0}_{1}_change'.format(obj.owner._meta.app_label,
                                                        obj.owner._meta.model_name),
                          args=(obj.owner.pk,))
            return format_html("<a href='{url}' title='{user}'>{user}</a>", url=url, user=obj.owner)
        return ""
    owner_url.short_description = _('owner')

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["owner"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__account=self.obj.account)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def delete_model(self, request, obj):
        obj.delete_related_content()
        super().delete_model(request, obj)

    ## Actions
    actions = [
        "make_public",
        "make_private",
    ]

    @transaction.atomic
    def make_public(self, request, queryset):
        total_updates = 0

        for account in queryset.exclude(is_private=False):
            account.is_private = False

            account.public_permissions = list(set((account.public_permissions or []) + anon_permissions))

            account.save()
            total_updates += 1

        self.message_user(request, _("{count} successfully made public.").format(count=total_updates))
    make_public.short_description = _("Make public")

    @transaction.atomic
    def make_private(self, request, queryset):
        total_updates = 0

        for account in queryset.exclude(is_private=True):
            account.is_private = True
            account.public_permissions = []

            account.save()
            total_updates += 1

        self.message_user(request, _("{count} successfully made private.").format(count=total_updates))
    make_private.short_description = _("Make private")

    def delete_queryset(self, request, queryset):
        # NOTE: Override delete_queryset so its use the same approach used in
        # accounts.models.Account.delete_related_content.
        #
        # More info https://docs.djangoproject.com/en/2.2/ref/contrib/admin/actions/#admin-actions

        from apps.events.apps import (connect_events_signals,
                                    disconnect_events_signals)
        from apps.accounts.apps import (connect_memberships_signals,
                                    disconnect_memberships_signals)

        disconnect_events_signals()
        disconnect_memberships_signals()

        try:
            super().delete_queryset(request, queryset)
        finally:
            # connect_events_signals()
            connect_memberships_signals()


class BrokerAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "supports_stocks", "supports_options", "supports_forex", "supports_futures", "supports_crypto", "supports_metatrader_4", "supports_metatrader_5", "supports_file_import", "supports_auto_sync_import", "created_date")
    list_filter = ("supports_stocks", "supports_options", "supports_forex", "supports_futures", "supports_crypto", "supports_metatrader_4", "supports_metatrader_5", "supports_file_import", "supports_auto_sync_import")
    list_editable = ("supports_stocks", "supports_options", "supports_forex", "supports_futures", "supports_crypto", "supports_metatrader_4", "supports_metatrader_5", "supports_file_import", "supports_auto_sync_import")
    search_fields = ("name", "description")


admin.site.register(Broker, BrokerAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Membership, MembershipAdmin)

