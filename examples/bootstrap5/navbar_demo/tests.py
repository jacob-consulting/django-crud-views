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
        assert [item["url"] for item in bar["items"]] == [
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
            assert destination.context["object"] == customer
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
