from django.contrib import admin
from .models import CarpoolRequest, DriverOffer


@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    list_display = ['passenger', 'pickup_node', 'dropoff_node', 'status', 'created_at']
    list_filter = ['status']


@admin.register(DriverOffer)
class DriverOfferAdmin(admin.ModelAdmin):
    list_display = ['trip', 'carpool_request', 'fare', 'detour_hops', 'status']
    list_filter = ['status']
