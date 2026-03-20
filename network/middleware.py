from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

ALWAYS_ALLOWED = ['/admin/', '/accounts/login/', '/accounts/logout/', '/accounts/register/', '/static/']


class ServiceSuspendedMiddleware(MiddlewareMixin):

    def process_request(self, request):
        path = request.path
        if any(path.startswith(u) for u in ALWAYS_ALLOWED):
            return None
        if request.user.is_authenticated and request.user.is_staff:
            return None
        from .models import SiteSettings
        try:
            s = SiteSettings.get_settings()
            if not s.is_active:
                return HttpResponse(
                    '<html><body style="font-family:sans-serif;text-align:center;padding:60px">'
                    '<h1 style="color:red">Service Suspended</h1>'
                    '<p>The carpooling service is down for maintenance.</p>'
                    '<a href="/admin/">Admin Login</a></body></html>',
                    status=503
                )
        except Exception:
            pass
        return None
