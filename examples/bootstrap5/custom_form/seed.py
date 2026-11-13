from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from custom_form.models import Contact

CONTACTS = [("Ada Lovelace", "ada@example.com"), ("Grace Hopper", "grace@example.com")]


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(
            user_model.objects.get(username=username), Contact, actions=("view", "add", "change", "delete")
        )

    for name, email in CONTACTS:
        Contact.objects.get_or_create(email=email, defaults={"name": name})
