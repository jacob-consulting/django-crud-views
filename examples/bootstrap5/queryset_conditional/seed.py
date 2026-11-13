from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from queryset_conditional.models import RequestBatch, Service, ServiceCategory, ServiceRequest


def seed():
    for username in ("alice", "bob"):
        user = get_user_model().objects.get(username=username)
        for model in (ServiceCategory, Service, RequestBatch, ServiceRequest):
            grant_model_perms(user, model)

    services = {}
    for name, code in (
        ("Boiler inspection", "on_site"),
        ("Appliance installation", "on_site"),
        ("Technical consultation", "remote"),
        ("Document review", "general"),
    ):
        category, _ = ServiceCategory.objects.get_or_create(code=code)
        services[name], _ = Service.objects.get_or_create(name=name, defaults={"category": category})

    ServiceRequest.objects.get_or_create(
        batch=None, service=services["Boiler inspection"], defaults={"visit_address": "12 Example Street"}
    )
    batch, _ = RequestBatch.objects.get_or_create(title="Weekly service requests")
    for name, address, url in (
        ("Appliance installation", "24 Example Avenue", ""),
        ("Technical consultation", "", "https://example.com/meeting"),
        ("Document review", "", ""),
    ):
        ServiceRequest.objects.get_or_create(
            batch=batch, service=services[name], defaults={"visit_address": address, "meeting_url": url}
        )
