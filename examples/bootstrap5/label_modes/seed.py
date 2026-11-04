from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from label_modes.models import Gadget

GADGETS = ["Pocket torch", "Folding ruler", "Spirit level"]


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(user_model.objects.get(username=username), Gadget)

    for name in GADGETS:
        Gadget.objects.get_or_create(name=name)
