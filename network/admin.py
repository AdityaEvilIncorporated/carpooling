from django.contrib import admin
from django.utils.html import format_html
from .models import Node, Edge, SiteSettings


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude']
    search_fields = ['name']


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ['from_node', 'to_node']
    list_filter = ['from_node']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['service_status']

    def service_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold;">Active</span>')
        return format_html('<span style="color:red;font-weight:bold;">Suspended</span>')

    service_status.short_description = 'Status'

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
