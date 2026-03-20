from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('network/', include('network.urls')),
    path('trips/', include('trips.urls')),
    path('requests/', include('requests_app.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
]
