from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from flash_messages.models import Notice


def seed():
    # nothing to store: the compose page only needs Notice's "view" permission
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(user_model.objects.get(username=username), Notice, actions=("view",))
