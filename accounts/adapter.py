from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        user = request.user
        if hasattr(user, 'is_driver') and user.is_driver():
            return '/trips/dashboard/'
        return '/requests/dashboard/'

    def get_signup_redirect_url(self, request):
        user = request.user
        if hasattr(user, 'is_driver') and user.is_driver():
            return '/trips/dashboard/'
        return '/requests/dashboard/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.role:
            user.role = 'passenger'
            user.save()
        return user

    def get_login_redirect_url(self, request):
        return '/accounts/profile/'
