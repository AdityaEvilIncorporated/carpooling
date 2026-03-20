from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
import os

class Command(BaseCommand):
    help = 'Sets the site domain for Google OAuth'

    def add_arguments(self, parser):
        parser.add_argument('--domain', default='127.0.0.1:8000')

    def handle(self, *args, **options):
        from allauth.socialaccount.models import SocialApp

        domain = options['domain']
        site, created = Site.objects.get_or_create(id=1)
        site.domain = domain
        site.name = domain
        site.save()

        client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

        app, created = SocialApp.objects.get_or_create(provider='google')
        app.name = 'Google'
        app.client_id = client_id
        app.secret = secret
        app.save()
        app.sites.add(site)

        self.stdout.write(self.style.SUCCESS(f'Site domain is now: {site.domain}'))
