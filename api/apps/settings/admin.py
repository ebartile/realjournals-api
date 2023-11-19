from django.contrib import admin
from .models import TerminalModule, TerminalPageModule, AdminModule, AdminPageModule, ThemeSettings, TerminalDimensions, AdminDimensions

class TerminalModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', )
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active', )

class AdminModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', )
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active', )

class TerminalDimensionsInline(admin.TabularInline):  # You can also use StackedInline for a different display style
    model = TerminalDimensions
    extra = 0  # Set this to control the number of empty forms to display

class AdminDimensionsInline(admin.TabularInline):  # You can also use StackedInline for a different display style
    model = AdminDimensions
    extra = 0  # Set this to control the number of empty forms to display

@admin.register(TerminalPageModule)
class TerminalPageModuleAdmin(admin.ModelAdmin):
    list_display = ('account', 'page', 'module', 'status', 'order', 'created_at', 'updated_at')
    list_filter = ('page', 'status')
    search_fields = ('page', 'module__name', 'account__name')
    inlines = [TerminalDimensionsInline]  # Add the DimensionsInline as an inline

@admin.register(AdminPageModule)
class AdminPageModuleAdmin(admin.ModelAdmin):
    list_display = ('page', 'module', 'status', 'order', 'created_at', 'updated_at')
    list_filter = ('page', 'status')
    search_fields = ('page', 'module__name', 'account__name')
    inlines = [AdminDimensionsInline]  # Add the DimensionsInline as an inline

class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ('mode', 'direction', 'color', 'stretch')
    list_filter = ('mode', 'direction', 'color', 'stretch')

# Register your models and their respective admin classes
admin.site.register(AdminModule, AdminModuleAdmin)
admin.site.register(TerminalModule, TerminalModuleAdmin)
admin.site.register(ThemeSettings, ThemeSettingsAdmin)
