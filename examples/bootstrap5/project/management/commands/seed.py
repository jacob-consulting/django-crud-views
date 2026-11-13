from importlib import import_module

from django.core.management.base import BaseCommand
from django.db import transaction

from project.features import FEATURES
from project.seeding import ensure_demo_users, ensure_developer_read_access


class Command(BaseCommand):
    help = "Seed demo users and demo data for all example apps. Idempotent."

    @transaction.atomic
    def handle(self, *args, **options):
        users = ensure_demo_users()
        ensure_developer_read_access(users["developer"])
        self.stdout.write("users: alice/alice, bob/bob, developer/developer")
        for feature in FEATURES:
            import_module(f"{feature.app}.seed").seed()
            self.stdout.write(f"seeded {feature.app}")
        self.stdout.write(self.style.SUCCESS("Done."))
