from django.urls import path
from . import views

urlpatterns = [
    path('graph/', views.graph_view, name='graph'),
    path('active-trips/', views.active_trips_view, name='active-trips'),
]
