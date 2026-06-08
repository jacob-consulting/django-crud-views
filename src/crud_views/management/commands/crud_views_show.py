from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Show Django CRUD views"

    def handle(self, *args, **options):
        pass
