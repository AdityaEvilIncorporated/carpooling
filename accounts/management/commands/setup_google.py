from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Sets the site domain for Google OAuth'

    def add_arguments(self, parser):
        parser.add_argument('--domain', default='127.0.0.1:8000')

    def handle(self, *args, **options):
        domain = options['domain']
        site, created = Site.objects.get_or_create(id=1)
        site.domain = domain
        site.name = domain
        site.save()
        self.stdout.write(self.style.SUCCESS(f'Site domain is now: {site.domain}'))
