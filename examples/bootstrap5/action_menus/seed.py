from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from action_menus.models import Chore, Step


def seed():
    user_model = get_user_model()
    # alice may do everything; bob may only look: archive shows disabled for him, the rest disappears
    for model in (Chore, Step):
        grant_model_perms(user_model.objects.get(username="alice"), model)
        grant_model_perms(user_model.objects.get(username="bob"), model, actions=("view",))

    for title in ("Take out the trash", "Water the plants", "Clean the windows", "Fix the bike", "Do the laundry"):
        chore, _ = Chore.objects.get_or_create(title=title)
        Step.objects.get_or_create(chore=chore, text=f"Plan: {title}")
