from django.contrib.auth.models import Group
from django.core.management import BaseCommand

from crud_views.lib.settings import crud_views_settings


class Command(BaseCommand):
    help = "Ensure the configured manage diagnostics group exists, without changing memberships or permissions."

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=crud_views_settings.manage_group)
        status = "Created" if created else "Already present"
        self.stdout.write(f"{status}: {group.name}")
