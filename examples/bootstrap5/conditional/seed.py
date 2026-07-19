from django.contrib.auth import get_user_model

from conditional.models import Event, Registration, Session, Speaker
from project.seeding import grant_model_perms


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        for model in (Registration, Event, Session, Speaker):
            grant_model_perms(user, model)

    Registration.objects.get_or_create(name="Jane Doe", defaults={"with_company": False})
    Registration.objects.get_or_create(
        name="Acme Corp Attendee",
        defaults={
            "with_company": True,
            "company_name": "Acme Corp",
            "vat_id": "DE123456789",
            "note": "Please seat near the stage.",
        },
    )

    event, _ = Event.objects.get_or_create(
        name="Annual Conference", defaults={"with_sessions": True, "with_speakers": True}
    )
    for title in ("Opening Keynote", "Deep Dive Workshop", "Closing Panel"):
        Session.objects.get_or_create(event=event, title=title)
    for name in ("Ada Lovelace", "Grace Hopper"):
        Speaker.objects.get_or_create(event=event, name=name)
    Event.objects.get_or_create(name="Simple Meetup", defaults={"with_sessions": False})
