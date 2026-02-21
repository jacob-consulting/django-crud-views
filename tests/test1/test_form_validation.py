import pytest
from django.test.client import Client

from tests.test1.app.models import Publisher


# --- Create: validation errors ---


@pytest.mark.django_db
def test_create_missing_required_field(client_user_publisher_add: Client, cv_publisher):
    """POST with empty required field should re-render the form (200), not redirect."""
    response = client_user_publisher_add.post("/publisher/create/", {"name": ""})
    assert response.status_code == 200

    # Form should contain an error
    form = response.context["form"]
    assert form.errors
    assert "name" in form.errors

    # No object created
    assert Publisher.objects.count() == 0


@pytest.mark.django_db
def test_create_missing_field_entirely(client_user_publisher_add: Client, cv_publisher):
    """POST with missing field key should re-render the form with errors."""
    response = client_user_publisher_add.post("/publisher/create/", {})
    assert response.status_code == 200

    form = response.context["form"]
    assert form.errors
    assert "name" in form.errors
    assert Publisher.objects.count() == 0


# --- Update: validation errors ---


@pytest.mark.django_db
def test_update_blank_required_field(client_user_publisher_change: Client, cv_publisher, publisher_penguin):
    """POST update with empty required field should re-render the form."""
    pk = publisher_penguin.pk
    response = client_user_publisher_change.post(f"/publisher/{pk}/update/", {"name": ""})
    assert response.status_code == 200

    form = response.context["form"]
    assert form.errors
    assert "name" in form.errors

    # Original value unchanged
    publisher_penguin.refresh_from_db()
    assert publisher_penguin.name == "Penguin"


# --- Delete: confirm checkbox ---


@pytest.mark.django_db
def test_delete_without_confirm(client_user_publisher_delete: Client, cv_publisher, publisher_penguin):
    """POST delete without confirm checkbox should re-render the form."""
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.post(f"/publisher/{pk}/delete/", {})
    assert response.status_code == 200

    form = response.context["form"]
    assert form.errors

    # Object not deleted
    assert Publisher.objects.filter(pk=pk).exists()


# --- CSRF ---


@pytest.mark.django_db
def test_csrf_enforced_on_create(cv_publisher, user_publisher_add):
    """POST without CSRF token should be rejected (403)."""
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_publisher_add)

    response = client.post("/publisher/create/", {"name": "Test"})
    assert response.status_code == 403

    assert Publisher.objects.count() == 0


@pytest.mark.django_db
def test_csrf_enforced_on_update(cv_publisher, user_publisher_change, publisher_penguin):
    """POST update without CSRF token should be rejected (403)."""
    pk = publisher_penguin.pk
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_publisher_change)

    response = client.post(f"/publisher/{pk}/update/", {"name": "Hacked"})
    assert response.status_code == 403

    publisher_penguin.refresh_from_db()
    assert publisher_penguin.name == "Penguin"


@pytest.mark.django_db
def test_csrf_enforced_on_delete(cv_publisher, user_publisher_delete, publisher_penguin):
    """POST delete without CSRF token should be rejected (403)."""
    pk = publisher_penguin.pk
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_publisher_delete)

    response = client.post(f"/publisher/{pk}/delete/", {"confirm": True})
    assert response.status_code == 403

    assert Publisher.objects.filter(pk=pk).exists()


# --- Form re-render preserves input ---


@pytest.mark.django_db
def test_create_rerender_preserves_input(client_user_publisher_add: Client, cv_publisher):
    """On validation failure, the form should preserve the submitted values."""
    # name exceeds max_length (200) to trigger validation error
    long_name = "A" * 201
    response = client_user_publisher_add.post("/publisher/create/", {"name": long_name})
    assert response.status_code == 200

    form = response.context["form"]
    assert form.errors
    # The submitted value should be preserved in the form
    assert form.data["name"] == long_name
