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
    """AuthorModalDetailView (ObjectDetailViewPermissionRequired) renders its object-detail groups inside the modal partial."""
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


# ---------------------------------------------------------------------------
# POST protocol (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modal_delete_success_returns_204_with_redirect(client_user_author_modal: Client, author_douglas_adams):
    from django.contrib.messages import get_messages

    from tests.test1.app.models import Author

    pk = author_douglas_adams.pk
    response = client_user_author_modal.post(f"/author_modal/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS)
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"
    assert not Author.objects.filter(pk=pk).exists()
    assert len(list(get_messages(response.wsgi_request))) == 1  # MessageMixin still queues the message


@pytest.mark.django_db
def test_modal_delete_protection_returns_422_partial(
    client_user_publisher_modal_protected_delete: Client, publisher_penguin
):
    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    response = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS
    )
    assert response.status_code == 422
    assert "crud_views/modal/content.html" in template_names(response)
    assert "Cannot delete this publisher." in response.content.decode()
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_modal_custom_form_invalid_returns_422(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.post(
        f"/author_modal/{author_douglas_adams.pk}/contact/",
        {"subject": "", "body": ""},
        headers=MODAL_HEADERS,
    )
    assert response.status_code == 422
    assert "crud_views/modal/content.html" in template_names(response)


@pytest.mark.django_db
def test_modal_custom_form_valid_returns_204(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.post(
        f"/author_modal/{author_douglas_adams.pk}/contact/",
        {"subject": "Hello", "body": "Nice to meet you."},
        headers=MODAL_HEADERS,
    )
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"


@pytest.mark.django_db
def test_non_modal_post_flows_unchanged(client_user_author_modal: Client, author_douglas_adams):
    """Without the header, a cv_modal view still redirects with 302 (regression guard)."""
    response = client_user_author_modal.post(f"/author_modal/{author_douglas_adams.pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert response.url == "/author_modal/"


# ---------------------------------------------------------------------------
# System checks (Task 4)
# ---------------------------------------------------------------------------


def check_ids(view_cls) -> list:
    return [m.id for c in view_cls.checks() for m in c.messages()]


def test_check_modal_size_invalid():
    from crud_views.lib.views import DeleteView

    class BadSizeDeleteView(DeleteView):
        cv_modal = True
        cv_modal_size = "modal-huge"

    assert "viewset.E250" in check_ids(BadSizeDeleteView)


def test_check_modal_size_valid_values():
    from crud_views.lib.views import DeleteView

    for size in ("", "modal-sm", "modal-lg", "modal-xl"):

        class GoodSizeDeleteView(DeleteView):
            cv_modal = True
            cv_modal_size = size

        assert "viewset.E250" not in check_ids(GoodSizeDeleteView)


def test_check_modal_not_supported_on_create():
    from crud_views.lib.views import CreateView

    class BadModalCreateView(CreateView):
        cv_modal = True

    assert "viewset.E251" in check_ids(BadModalCreateView)


def test_check_modal_supported_on_delete():
    from crud_views.lib.views import DeleteView

    class GoodModalDeleteView(DeleteView):
        cv_modal = True

    assert "viewset.E251" not in check_ids(GoodModalDeleteView)


# ---------------------------------------------------------------------------
# Button attributes, form action, shell (Task 5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_buttons_carry_modal_attributes(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.get("/author_modal/")
    content = response.content.decode()
    assert 'data-cv-modal="true"' in content
    assert 'data-cv-modal-size="modal-lg"' in content  # AuthorModalDeleteView


@pytest.mark.django_db
def test_list_buttons_without_modal_have_no_attributes(client_user_author_delete: Client, author_douglas_adams):
    response = client_user_author_delete.get("/author/")
    assert "data-cv-modal" not in response.content.decode()


@pytest.mark.django_db
def test_modal_partial_form_has_explicit_action(client_user_author_modal: Client, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_modal.get(f"/author_modal/{pk}/delete/", headers=MODAL_HEADERS)
    assert f'action="/author_modal/{pk}/delete/"' in response.content.decode()


@pytest.mark.django_db
def test_cv_config_renders_modal_shell(client_user_author_modal: Client):
    response = client_user_author_modal.get("/author_modal/")
    content = response.content.decode()
    assert 'id="cv-modal"' in content
    assert 'id="cv-modal-dialog"' in content
    assert 'id="cv-modal-content"' in content


# ---------------------------------------------------------------------------
# modal.js registration (Task 6) — JS behavior itself is verified manually
# in examples/bootstrap5 (see design spec, testing decision)
# ---------------------------------------------------------------------------


def test_modal_js_registered_and_shipped():
    from django.contrib.staticfiles import finders

    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.javascript()["modal"] == "crud_views/js/modal.js"
    assert finders.find("crud_views/js/modal.js")


@pytest.mark.django_db
def test_cv_js_tag_includes_modal_js(client_user_author_modal: Client):
    response = client_user_author_modal.get("/author_modal/")
    assert "crud_views/js/modal.js" in response.content.decode()
