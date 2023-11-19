from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from .models import Journal
from apps.attachments.admin import  AttachmentInline




admin.site.register(Journal)
