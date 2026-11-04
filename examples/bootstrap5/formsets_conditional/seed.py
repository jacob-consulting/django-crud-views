from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from formsets_conditional.models import Conference, Session, Speaker

#: session title → speaker names, for the conference that has sessions
SESSIONS = {
    "Opening Keynote": ["Ada Lovelace"],
    "Deep Dive Workshop": ["Grace Hopper", "Alan Turing"],
}


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        user = user_model.objects.get(username=username)
        for model in (Conference, Session, Speaker):
            grant_model_perms(user, model)

    conference, _ = Conference.objects.get_or_create(
        name="Python Summit",
        defaults={
            "with_billing": True,
            "billing_company": "Acme Corp",
            "billing_vat_id": "DE123456789",
            "with_sessions": True,
        },
    )
    for title, names in SESSIONS.items():
        session, _ = Session.objects.get_or_create(conference=conference, title=title)
        for name in names:
            Speaker.objects.get_or_create(session=session, name=name)
    Conference.objects.get_or_create(name="Local Meetup", defaults={"with_billing": False, "with_sessions": False})
