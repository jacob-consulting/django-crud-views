from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from conditional.models import Customer, Event, Registration, Session, Speaker


def seed():
    user_model = get_user_model()
    for username in ("alice", "bob"):
        user = user_model.objects.get(username=username)
        for model in (Registration, Event, Session, Speaker, Customer):
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

    # Explicit inactive values show saved conditional state, even where a model has a creation default.
    Customer.objects.get_or_create(
        name="Consumer Customer",
        defaults={
            "kind": "consumer",
            "consumer_note": "Please send delivery updates by email.",
            "company": None,
            "price_tier": None,
            "payment_terms": "unset",
            "wholesale_terms": None,
            "distribution_region": "",
        },
    )
    Customer.objects.get_or_create(
        name="Wholesale Customer",
        defaults={
            "kind": "wholesale",
            "consumer_note": None,
            "company": "Acme Wholesale",
            "price_tier": "B",
            "payment_terms": "net30",
            "wholesale_terms": 30,
            "distribution_region": "",
        },
    )
    Customer.objects.get_or_create(
        name="Distributor Customer",
        defaults={
            "kind": "distributor",
            "consumer_note": None,
            "company": "North Distribution",
            "price_tier": "A",
            "payment_terms": "net60",
            "wholesale_terms": None,
            "distribution_region": "Northern region",
        },
    )
