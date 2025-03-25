from django.core.management import BaseCommand

from app.models import Person


class Command(BaseCommand):
    help = "Show Django CRUD views"

    def handle(self, *args, **options):


        person = Person.objects.filter(group__id=1).first()

        x = person.membership_set.all()

        x = 1


