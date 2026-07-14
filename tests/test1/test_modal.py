"""
Tests for cv_modal: Bootstrap 5 modal rendering via X-CV-Modal content negotiation.
Spec: superpowers/specs/2026-07-14-bootstrap-modals-design.md
"""

import pytest
from django.test.client import Client

MODAL_HEADERS = {"X-CV-Modal": "true"}


def template_names(response) -> list:
    return [t.name for t in response.templates if t.name]


# ---------------------------------------------------------------------------
# GET rendering (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_without_header_renders_full_page(client_user_author_modal: Client, author_douglas_adams):
    """No X-CV-Modal header -> unchanged full page (deep links, no-JS)."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/delete/")
    assert response.status_code == 200
    assert "crud_views/view_delete.html" in template_names(response)
    assert "crud_views/modal/content.html" not in template_names(response)


@pytest.mark.django_db
def test_get_with_header_renders_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """X-CV-Modal: true on a cv_modal view -> modal partial, no page chrome."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    names = template_names(response)
    assert "crud_views/modal/content.html" in names
    assert "crud_views/view_delete.html" not in names
    content = response.content.decode()
    assert "modal-header" in content
    assert "modal-body" in content
    assert "<html" not in content


@pytest.mark.django_db
def test_get_with_header_on_non_modal_view_renders_full_page(
    client_user_author_delete: Client, cv_author, author_douglas_adams
):
    """Header on a cv_modal=False view is ignored."""
    response = client_user_author_delete.get(f"/author/{author_douglas_adams.pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/view_delete.html" in template_names(response)


@pytest.mark.django_db
def test_modal_view_sets_vary_header(client_user_author_modal: Client, author_douglas_adams):
    """Responses of modal-enabled views carry Vary: X-CV-Modal (with and without the header)."""
    url = f"/author_modal/{author_douglas_adams.pk}/delete/"
    for headers in ({}, MODAL_HEADERS):
        response = client_user_author_modal.get(url, headers=headers)
        assert "X-CV-Modal" in response.headers.get("Vary", "")


@pytest.mark.django_db
def test_detail_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """DetailView renders its object-detail groups inside the modal partial."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/detail/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in template_names(response)
    assert "Douglas" in response.content.decode()


@pytest.mark.django_db
def test_custom_form_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """CustomFormView renders its form inside the modal partial."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/contact/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in template_names(response)
    assert "<form" in response.content.decode()
