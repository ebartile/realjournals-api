from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "account", "attached_file", "owner", "content_type", "content_object"]
    list_display_links = ["id", "attached_file",]
    search_fields = ["id", "attached_file", "account__name", "account__slug"]
    raw_id_fields = ["account"]


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["owner"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__account=self.obj.account)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AttachmentInline(GenericTabularInline):
     model = models.Attachment
     fields = ("attached_file", "owner")
     extra = 0


admin.site.register(models.Attachment, AttachmentAdmin)
