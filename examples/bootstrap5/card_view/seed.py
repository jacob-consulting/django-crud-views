from django.contrib.auth import get_user_model
from library.models import Author
from project.seeding import grant_model_perms


def seed():
    # The data is Library's authors (seeded by library.seed); this app only needs the same permissions.
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(user_model.objects.get(username=username), Author)
