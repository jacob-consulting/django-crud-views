from importlib import import_module

from django.core.management.base import BaseCommand

from project.features import FEATURES
from project.seeding import ensure_demo_users


class Command(BaseCommand):
    help = "Seed demo users and demo data for all example apps. Idempotent."

    def handle(self, *args, **options):
        ensure_demo_users()
        self.stdout.write("users: admin/admin (superuser), alice/alice, bob/bob")
        for feature in FEATURES:
            import_module(f"{feature.app}.seed").seed()
            self.stdout.write(f"seeded {feature.app}")
        self.stdout.write(self.style.SUCCESS("Done."))
