from django.contrib import admin
from .models import StorageEntry

class StorageEntryAdmin(admin.ModelAdmin):
    list_display = ('owner', 'created_date', 'modified_date', 'key', 'value')
    search_fields = ('owner__username', 'key')
    list_filter = ('created_date', 'modified_date')

admin.site.register(StorageEntry, StorageEntryAdmin)
