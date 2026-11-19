"""Independent tenant data: Guardian grants stop at Tenant, business grants are model-level."""

from django.db import transaction
from guardian.shortcuts import assign_perm
from project.seeding import ensure_demo_users, grant_model_perms

from navbar_demo.models import Address, Customer, Item, Order, Tenant


@transaction.atomic
def seed():
    users = ensure_demo_users()
    for username, tenant_id, customer_id, order_id, item_id, address_id, customer_name in (
        ("alice", 101, 303, 505, 707, 909, "Acme Coffee"),
        ("bob", 202, 404, 606, 808, 1010, "Bayside Books"),
    ):
        tenant, _ = Tenant.objects.get_or_create(pk=tenant_id, defaults={"name": f"Tenant {username.title()}"})
        customer, _ = Customer.objects.get_or_create(
            pk=customer_id,
            defaults={"tenant": tenant, "name": customer_name, "notes": f"{customer_name} account notes."},
        )
        order, _ = Order.objects.get_or_create(pk=order_id, defaults={"customer": customer, "name": "First order"})
        Item.objects.get_or_create(pk=item_id, defaults={"order": order, "name": "Sample item"})
        Address.objects.get_or_create(pk=address_id, defaults={"customer": customer, "name": "Delivery address"})
        for model in (Customer, Order, Item, Address):
            grant_model_perms(users[username], model)
        for permission in ("view_tenant", "change_tenant"):
            assign_perm(permission, users[username], tenant)
        if username == "alice":
            assign_perm("view_tenant", users["charlie"], tenant)
            Customer.objects.get_or_create(
                pk=405,
                defaults={"tenant": tenant, "name": "New customer", "notes": "Ready for a first order."},
            )
    for model in (Customer, Order, Item):
        grant_model_perms(users["charlie"], model, actions=("view",))
