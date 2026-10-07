from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from context_buttons.models import Ticket


def seed():
    User = get_user_model()
    # alice may do everything, bob may only look: log in as both to see which buttons disappear
    grant_model_perms(User.objects.get(username="alice"), Ticket)
    grant_model_perms(User.objects.get(username="bob"), Ticket, actions=("view",))

    for title, priority in (
        ("Printer on fire", Ticket.Priority.HIGH),
        ("Order more coffee", Ticket.Priority.NORMAL),
        ("Water the office plants", Ticket.Priority.LOW),
    ):
        Ticket.objects.get_or_create(title=title, defaults={"priority": priority})
