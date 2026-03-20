from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.driver_dashboard, name='driver-dashboard'),
    path('create/', views.create_trip, name='create-trip'),
    path('detail/<int:trip_id>/', views.trip_detail, name='trip-detail'),
    path('cancel/<int:trip_id>/', views.cancel_trip, name='cancel-trip'),
    path('start/<int:trip_id>/', views.start_trip, name='start-trip'),
    path('api/update-node/<int:trip_id>/', views.UpdateNodeView.as_view(), name='update-node'),
    path('api/requests/<int:trip_id>/', views.carpool_requests_api, name='carpool-requests-api'),
]
