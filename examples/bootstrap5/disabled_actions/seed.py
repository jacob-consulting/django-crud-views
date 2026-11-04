from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from disabled_actions.models import Ticket

TICKETS = [("Reset the VPN token", False), ("Quarterly audit report", True), ("Replace the coffee machine", False)]


def seed():
    # alice and bob may do everything: what greys out or disappears here is state, not permission
    user_model = get_user_model()
    for username in ("alice", "bob"):
        grant_model_perms(user_model.objects.get(username=username), Ticket)

    for title, locked in TICKETS:
        Ticket.objects.get_or_create(title=title, defaults={"locked": locked})
