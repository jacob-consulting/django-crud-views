"""The navbar scenario uses ordinary users and real destination requests."""

from types import ModuleType

import pytest
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.checks import run_checks
from django.template import Context, Template
from django.urls import get_resolver, include, path, reverse
from guardian.shortcuts import assign_perm


def test_installed_app_owns_customer_schema():
    assert apps.is_installed("navbar_demo"), "The independent navbar example must be installed"
    customer = apps.get_model("navbar_demo", "Customer")
    assert customer._meta.get_field("tenant").related_model is apps.get_model("navbar_demo", "Tenant")
    assert customer._meta.get_field("notes").get_internal_type() == "TextField"


@pytest.fixture
def scenario(db, client, django_user_model):
    from navbar_demo.models import Customer, Tenant

    tenant = Tenant.objects.create(pk=101, name="Alice tenant")
    other = Tenant.objects.create(pk=202, name="Bob tenant")
    customer = Customer.objects.create(pk=303, tenant=tenant, name="Acme Coffee", notes="Private tasting notes")
    foreign = Customer.objects.create(pk=404, tenant=other, name="Other customer", notes="Other notes")
    user = django_user_model.objects.create_user(username="alice")
    user.user_permissions.add(*Permission.objects.filter(content_type__app_label="navbar_demo"))
    assign_perm("view_tenant", user, tenant)
    assign_perm("change_tenant", user, tenant)
    client.force_login(user)
    return tenant, other, customer, foreign, user


@pytest.fixture
def local_routes(settings):
    from navbar_demo.views import cv_customer, cv_tenant

    # Preserve shared project login/home routes used by the example's base template.
    urls = ModuleType("navbar_test_urls")
    urls.urlpatterns = cv_tenant.urlpatterns + cv_customer.urlpatterns + [path("", include("project.urls"))]
    settings.ROOT_URLCONF = urls


def customer_url(key, tenant, customer=None):
    kwargs = {"navbar_tenant_pk": tenant.pk}
    if customer is not None:
        kwargs["pk"] = customer.pk
    return reverse(f"navbar_customer-{key}", kwargs=kwargs)


@pytest.mark.django_db
def test_customer_bar_has_four_ordered_sections(client, scenario):
    tenant, _, customer, _, _ = scenario
    response = client.get(customer_url("detail", tenant, customer))
    assert response.status_code == 200
    assert [item["label"] for item in response.context["cv_navbar"]["items"]] == [
        "Details",
        "Notes",
        "Orders",
        "Addresses",
    ]


@pytest.mark.django_db
def test_owned_details_notes_share_identity_and_distinct_active_sections(client, scenario, local_routes):
    tenant, _, customer, _, user = scenario
    assert not user.is_superuser
    assert not user.has_perm("navbar_demo.view_customer", customer)
    for key, label in (("detail", "Details"), ("notes", "Notes")):
        response = client.get(customer_url(key, tenant, customer))
        assert response.status_code == 200
        bar = response.context["cv_navbar"]
        assert bar["object"] == customer
        assert bar["label"] == str(customer)
        assert [item["label"] for item in bar["items"] if item["active"]] == [label]
        assert [item["url"] for item in bar["items"][:2]] == [
            customer_url("detail", tenant, customer),
            customer_url("notes", tenant, customer),
        ]
        html = Template("{% load crud_views %}{% cv_navbar %}").render(Context(response.context_data))
        assert str(customer) in html
        assert html.count('aria-current="true"') == 1
        if key == "notes":
            assert customer.notes in response.content.decode()


@pytest.mark.django_db
def test_tenant_grants_bound_real_customer_reads(client, scenario, local_routes):
    tenant, other, customer, foreign, _ = scenario
    response = client.get(reverse("navbar_tenant-list"))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [tenant]
    assert client.get(reverse("navbar_tenant-detail", kwargs={"pk": tenant.pk})).status_code == 200
    assert client.get(reverse("navbar_tenant-detail", kwargs={"pk": other.pk})).status_code == 403
    response = client.get(customer_url("list", tenant))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [customer]
    assert "cv_navbar" not in response.context
    for key in ("detail", "notes"):
        assert client.get(customer_url(key, other, foreign)).status_code == 403
        assert client.get(customer_url(key, tenant, foreign)).status_code == 404
    assert client.get(customer_url("list", other)).status_code == 403


@pytest.mark.django_db
def test_prefixed_parent_field_passes_checks_and_binds_creation(client, scenario, local_routes):
    from navbar_demo.models import Customer
    from navbar_demo.views import CustomerForm, cv_customer

    tenant, other, _, _, _ = scenario
    assert cv_customer.parent.attribute == "tenant"
    assert "tenant" not in CustomerForm.base_fields
    assert not [message for message in run_checks() if message.level >= 40]
    response = client.get(customer_url("create", tenant))
    assert response.status_code == 200
    assert "cv_navbar" not in response.context
    response = client.post(customer_url("create", tenant), {"name": "New customer", "notes": "New", "tenant": other.pk})
    assert response.status_code == 302
    assert Customer.objects.get(name="New customer").tenant == tenant


def test_project_publishes_navbar_landing_route():
    assert "navbar-demo-home" in get_resolver().reverse_dict, "Project URLconf must publish the navbar landing page"
    assert reverse("navbar-demo-home") == "/object-navbar/"


@pytest.mark.django_db
def test_public_routes_preserve_owner_links_and_authenticated_entry(client, scenario):
    tenant, _, customer, _, _ = scenario
    response = client.get(reverse("navbar-demo-home"), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("navbar_tenant-list"), 302)]
    for key in ("detail", "notes", "update", "delete"):
        url = customer_url(key, tenant, customer)
        assert url.startswith("/object-navbar/")
        response = client.get(url)
        assert response.status_code == 200
        bar = response.context["cv_navbar"]
        assert bar["object"] == customer
        for item in bar["items"]:
            destination = client.get(item["url"])
            assert destination.status_code == 200
            assert destination.context["cv_navbar"]["object"] == customer
    client.logout()
    assert client.get(reverse("navbar-demo-home")).status_code == 302
    assert client.get(customer_url("detail", tenant, customer)).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["list", "detail", "notes", "create", "update", "delete"])
def test_public_routes_deny_other_tenant(client, scenario, key):
    _, other, _, foreign, _ = scenario
    obj = None if key in ("list", "create") else foreign
    url = customer_url(key, other, obj)
    assert client.get(url).status_code == 403
    if key in ("create", "update", "delete"):
        assert client.post(url, {"name": "Forged", "notes": "Forged"}).status_code == 403
    foreign.refresh_from_db()
    assert foreign.name == "Other customer"


@pytest.mark.django_db
@pytest.mark.parametrize("key,permission", [("create", "add"), ("update", "change"), ("delete", "delete")])
@pytest.mark.parametrize("missing_gate", ["customer_model", "tenant_object"])
def test_writes_require_customer_operation_and_tenant_change(client, scenario, key, permission, missing_gate):
    from guardian.shortcuts import remove_perm

    from navbar_demo.models import Customer

    tenant, _, customer, _, user = scenario
    if missing_gate == "customer_model":
        user.user_permissions.remove(
            Permission.objects.get(content_type__app_label="navbar_demo", codename=f"{permission}_customer")
        )
    else:
        remove_perm("change_tenant", user, tenant)
    url = customer_url(key, tenant, None if key == "create" else customer)
    assert client.get(url).status_code == 403
    assert client.post(url, {"name": "Forbidden", "notes": "Forbidden"}).status_code == 403
    assert Customer.objects.count() == 2
    customer.refresh_from_db()
    assert customer.name == "Acme Coffee"


@pytest.mark.django_db
def test_public_customer_crud_binds_parent_and_needs_no_record_grants(client, scenario):
    from guardian.models import UserObjectPermission

    from navbar_demo.models import Customer

    tenant, other, _, _, _ = scenario
    assert (
        client.post(
            customer_url("create", tenant), {"name": "Created", "notes": "First", "tenant": other.pk}
        ).status_code
        == 302
    )
    customer = Customer.objects.get(name="Created")
    assert customer.tenant == tenant
    assert not UserObjectPermission.objects.filter(
        content_type__app_label="navbar_demo", content_type__model="customer"
    ).exists()
    assert client.get(customer_url("notes", tenant, customer)).status_code == 200
    assert (
        client.post(
            customer_url("update", tenant, customer), {"name": "Updated", "notes": "Second", "tenant": other.pk}
        ).status_code
        == 302
    )
    customer.refresh_from_db()
    assert (customer.name, customer.notes, customer.tenant) == ("Updated", "Second", tenant)
    assert client.post(customer_url("delete", tenant, customer), {"confirm": True}).status_code == 302
    assert not Customer.objects.filter(pk=customer.pk).exists()


@pytest.mark.django_db
def test_customer_reads_require_model_permission_even_with_tenant_grant(client, scenario):
    tenant, _, customer, _, user = scenario
    user.user_permissions.remove(
        Permission.objects.get(content_type__app_label="navbar_demo", codename="view_customer")
    )
    for key in ("list", "detail", "notes"):
        assert client.get(customer_url(key, tenant, None if key == "list" else customer)).status_code == 403


@pytest.mark.django_db
def test_initial_migration_is_app_local_and_matches_models():
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader

    migration = MigrationLoader(connection).disk_migrations[("navbar_demo", "0001_initial")]
    assert migration.initial
    assert migration.dependencies == []
    assert {operation.name for operation in migration.operations} == {"Tenant", "Customer"}


@pytest.fixture
def hierarchy(scenario):
    from navbar_demo.models import Address, Item, Order

    tenant, other, customer, foreign, user = scenario
    order = Order.objects.create(pk=505, customer=customer, name="Coffee order")
    foreign_order = Order.objects.create(pk=606, customer=foreign, name="Other order")
    item = Item.objects.create(pk=707, order=order, name="Coffee beans")
    foreign_item = Item.objects.create(pk=808, order=foreign_order, name="Other beans")
    address = Address.objects.create(pk=909, customer=customer, name="Alice delivery")
    foreign_address = Address.objects.create(pk=1010, customer=foreign, name="Bob delivery")
    return (
        (tenant, customer, order, item, address),
        (other, foreign, foreign_order, foreign_item, foreign_address),
        user,
    )


def business_url(model, key, branch, obj=None):
    tenant, customer, order, item, address = branch
    kwargs = {"navbar_tenant_pk": tenant.pk}
    if model != "customer":
        kwargs["navbar_customer_pk"] = customer.pk
    if model == "item":
        kwargs["navbar_order_pk"] = order.pk
    if key not in ("list", "create"):
        kwargs["pk"] = (obj or {"customer": customer, "order": order, "item": item, "address": address}[model]).pk
    return reverse(f"navbar_{model}-{key}", kwargs=kwargs)


def business_snapshot():
    return {
        name: list(apps.get_model("navbar_demo", name).objects.order_by("pk").values())
        for name in ("Customer", "Order", "Item", "Address")
    }


@pytest.mark.django_db
@pytest.mark.parametrize("model", ["customer", "order", "item", "address"])
def test_full_business_crud_binds_each_parent(client, hierarchy, model):
    from guardian.models import UserObjectPermission

    own, foreign, _ = hierarchy
    model_class = apps.get_model("navbar_demo", model)
    parent_field = {"customer": "tenant", "order": "customer", "item": "order", "address": "customer"}[model]
    parent_index = {"customer": 0, "order": 1, "item": 2, "address": 1}[model]
    for key in ("list", "detail", "create", "update", "delete"):
        assert client.get(business_url(model, key, own)).status_code == 200
    data = {"name": "Created", "notes": "Text", parent_field: foreign[parent_index].pk}
    assert client.post(business_url(model, "create", own), data).status_code == 302
    created = model_class.objects.get(name="Created")
    assert getattr(created, parent_field) == own[parent_index]
    data["name"] = "Updated"
    assert client.post(business_url(model, "update", own, created), data).status_code == 302
    created.refresh_from_db()
    assert created.name == "Updated"
    assert getattr(created, parent_field) == own[parent_index]
    assert client.post(business_url(model, "delete", own, created), {"confirm": True}).status_code == 302
    assert not model_class.objects.filter(pk=created.pk).exists()
    assert (
        not UserObjectPermission.objects.filter(content_type__app_label="navbar_demo")
        .exclude(content_type__model="tenant")
        .exists()
    )


@pytest.mark.django_db
@pytest.mark.parametrize("model", ["customer", "order", "item", "address"])
@pytest.mark.parametrize("reverse_direction", [False, True])
def test_copied_descendant_urls_cannot_cross_tenants(client, hierarchy, django_user_model, model, reverse_direction):
    own, foreign, user = hierarchy
    if reverse_direction:
        user = django_user_model.objects.create_user(username="bob")
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label="navbar_demo"))
        assign_perm("view_tenant", user, foreign[0])
        assign_perm("change_tenant", user, foreign[0])
        client.force_login(user)
        own, foreign = foreign, own
    before = business_snapshot()
    for key in ("list", "detail", "create", "update", "delete"):
        url = business_url(model, key, foreign)
        assert client.get(url).status_code == 403
        if key in ("create", "update", "delete"):
            assert client.post(url, {"name": "Forbidden", "confirm": True}).status_code == 403
    # Correctly scoped parent path plus a valid foreign record must also fail.
    index = {"customer": 1, "order": 2, "item": 3, "address": 4}[model]
    assert client.get(business_url(model, "detail", own, foreign[index])).status_code == 404
    assert business_snapshot() == before


@pytest.mark.django_db
def test_read_only_actor_has_no_addresses_or_write_mutations(client, hierarchy, django_user_model):
    own, foreign, _ = hierarchy
    reader = django_user_model.objects.create_user(username="reader")
    reader.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="navbar_demo", codename__in=["view_customer", "view_order", "view_item"]
        )
    )
    assign_perm("view_tenant", reader, own[0])
    client.force_login(reader)
    before = business_snapshot()
    for model in ("customer", "order", "item", "address"):
        for key in ("list", "detail", "create", "update", "delete"):
            response = client.get(business_url(model, key, own))
            expected = 200 if model != "address" and key in ("list", "detail") else 403
            assert response.status_code == expected
            if key in ("create", "update", "delete"):
                assert (
                    client.post(business_url(model, key, own), {"name": "Forbidden", "confirm": True}).status_code
                    == 403
                )
        assert client.get(business_url(model, "detail", foreign)).status_code == 403
    assert business_snapshot() == before


@pytest.mark.django_db
def test_deep_item_navigation_retains_customer_and_active_clickable_orders(client, hierarchy):
    own, _, _ = hierarchy
    reference = client.get(business_url("customer", "detail", own)).context["cv_navbar"]
    for model, keys in (("order", ("list", "detail", "create", "update")), ("item", ("detail", "update"))):
        for key in keys:
            response = client.get(business_url(model, key, own))
            assert response.status_code == 200
            bar = response.context["cv_navbar"]
            assert bar["object"] == own[1]
            assert bar["label"] == reference["label"]
            assert [item["url"] for item in bar["items"]] == [item["url"] for item in reference["items"]]
            active = [item for item in bar["items"] if item["active"]]
            assert [item["label"] for item in active] == ["Orders"]
            assert client.get(active[0]["url"]).status_code == 200
    assert "cv_navbar" not in client.get(business_url("order", "delete", own)).context


@pytest.mark.django_db
def test_descendant_schema_and_explicit_edges_pass_checks_without_migration_drift():
    from django.core.management import call_command

    from navbar_demo.views import cv_address, cv_customer, cv_item, cv_order

    for viewset, parent, attribute in (
        (cv_customer, "navbar_tenant", "tenant"),
        (cv_order, "navbar_customer", "customer"),
        (cv_item, "navbar_order", "order"),
        (cv_address, "navbar_customer", "customer"),
    ):
        assert (viewset.parent.name, viewset.parent.attribute) == (parent, attribute)
        assert viewset.ancestor_policy.cascade is True
    assert not [message for message in run_checks() if message.level >= 40]
    call_command("makemigrations", "navbar_demo", check=True, dry_run=True)
