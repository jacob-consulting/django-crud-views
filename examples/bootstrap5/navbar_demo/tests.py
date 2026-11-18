"""The navbar scenario uses ordinary users and real destination requests."""

from types import ModuleType

import pytest
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.checks import run_checks
from django.template import Context, Template
from django.urls import include, path, reverse
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
