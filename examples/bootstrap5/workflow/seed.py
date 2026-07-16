from django.contrib.auth import get_user_model

from project.seeding import grant_model_perms
from workflow.models import Campaign


def seed():
    User = get_user_model()
    admin = User.objects.get(username="admin")
    for username in ("alice", "bob"):
        grant_model_perms(User.objects.get(username=username), Campaign)

    Campaign.objects.get_or_create(name="Spring Newsletter")  # stays in draft

    summer, created = Campaign.objects.get_or_create(name="Summer Sale")
    if created:
        summer.wf_activate(by=admin)
        summer.save()

    winter, created = Campaign.objects.get_or_create(name="Winter Launch")
    if created:
        winter.wf_activate(by=admin)
        winter.save()
        winter.wf_complete(by=admin, comment="Wrapped up early")
        winter.save()
