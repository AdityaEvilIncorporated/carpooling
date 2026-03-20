from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.passenger_dashboard, name='passenger-dashboard'),
    path('submit/', views.submit_request, name='submit-request'),
    path('offers/<int:request_id>/', views.view_offers, name='view-offers'),
    path('confirm/<int:offer_id>/', views.confirm_offer, name='confirm-offer'),
    path('cancel/<int:request_id>/', views.cancel_request, name='cancel-request'),
    path('detail/<int:request_id>/', views.request_detail, name='request-detail'),
    path('driver/<int:trip_id>/', views.driver_requests_view, name='driver-requests'),
    path('offer/<int:request_id>/trip/<int:trip_id>/', views.make_offer, name='make-offer'),
    path('withdraw/<int:offer_id>/', views.withdraw_offer, name='withdraw-offer'),
    path('complete-trip/<int:trip_id>/', views.complete_trip_view, name='complete-trip'),
]
