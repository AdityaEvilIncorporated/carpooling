from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from .models import User, Wallet


@receiver(post_save, sender=User)
def make_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)


@receiver(pre_social_login)
def link_google_to_existing(sender, request, sociallogin, **kwargs):
    if sociallogin.is_existing:
        return
    try:
        email = sociallogin.account.extra_data.get('email', '')
        if email:
            existing = User.objects.get(email=email)
            sociallogin.connect(request, existing)
    except User.DoesNotExist:
        pass
