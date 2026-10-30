import re

import pytest
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


@pytest.mark.django_db
def test_related_objects_not_shown_by_default(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """Default DeleteView does not include related_objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" not in response.context


@pytest.mark.django_db
def test_related_objects_shown_when_enabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """DeleteView with cv_show_related_objects=True includes related objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" in response.context
    assert "related_summary" in response.context
    summary = response.context["related_summary"]
    assert summary["book"] == 2


@pytest.mark.django_db
def test_related_objects_rendered_in_template(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Related objects are rendered in the delete page HTML."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Book

    Book.objects.create(title="Hitchhiker's Guide", publisher=publisher_penguin)

    from django.contrib.auth.models import User

    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    content = response.content.decode()
    assert "Hitchhiker" in content
    assert "book" in content.lower()


@pytest.mark.django_db
def test_delete_protection_shown_on_get(
    client_user_publisher_protected_delete, cv_publisher_protected, publisher_penguin
):
    """GET on a protected object shows errors instead of the delete form."""
    pk = publisher_penguin.pk
    response = client_user_publisher_protected_delete.get(f"/publisher_protected/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Cannot delete" in content
    assert "delete_protection_errors" in response.context
    assert "<form" not in content


@pytest.mark.django_db
def test_delete_protection_post_still_blocks(
    client_user_publisher_protected_delete, cv_publisher_protected, publisher_penguin
):
    """POST on a protected object still prevents deletion (defense in depth)."""
    pk = publisher_penguin.pk
    response = client_user_publisher_protected_delete.post(f"/publisher_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    from tests.test1.app.models import Publisher

    assert Publisher.objects.filter(pk=pk).exists()
    assert "Cannot delete" in response.content.decode()


@pytest.mark.django_db
def test_permission_filtering_hides_restricted_objects(cv_publisher_cascade, publisher_penguin):
    """User without view permission on Book sees counts, not individual objects."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Book

    Book.objects.create(title="Secret Book A", publisher=publisher_penguin)
    Book.objects.create(title="Secret Book B", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_no_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Secret Book A" not in content
    assert "Secret Book B" not in content
    assert "book" in content.lower()  # summary still shows model name


@pytest.mark.django_db
def test_permission_filtering_shows_permitted_objects(cv_publisher_cascade, publisher_penguin):
    """User with view permission on Book sees individual object details."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Visible Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_with_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")
    perm = Permission.objects.get(codename="view_book")
    user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content


DANGER_ALERT = 'class="alert alert-danger" role="alert"'
BLOCKED_HEADING = "Deletion is blocked by protected relationships"
BLOCKED_LIST_HEADING = BLOCKED_HEADING + ":"
BLOCKED_SENTENCE = "Other objects still reference this one; remove or reassign them before deleting it."
MODAL_HEADERS = {"X-CV-Modal": "true"}


def _norm(html: str) -> str:
    return re.sub(r"\s+", " ", html)


def _context_instances(value, model, depth: int = 0) -> list:
    """Every ``model`` instance reachable through lists/tuples/sets/dicts of a context value."""
    if depth > 8:
        return []
    if isinstance(value, model):
        return [value]
    if isinstance(value, dict):
        return [hit for v in value.values() for hit in _context_instances(v, model, depth + 1)]
    if isinstance(value, (list, tuple, set)):
        return [hit for v in value for hit in _context_instances(v, model, depth + 1)]
    return []


def _response_instances(response, model) -> list:
    return [hit for layer in response.context for hit in _context_instances(layer.flatten(), model)]


@pytest.mark.django_db
def test_protected_objects_hidden_without_view_permission(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """D-07/D-08: a protected-only collection the user may not view keeps one blocked notice, no labels."""
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    context = response.context
    assert context["related_summary"] == {}
    assert list(context["protected_objects"]) == []
    assert context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_HEADING in content
    assert BLOCKED_SENTENCE in content
    assert BLOCKED_LIST_HEADING not in content
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_protected_objects_hidden_without_view_permission_modal(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    """The modal partial carries the same independent notice when summary and labels are empty."""
    from tests.test1.app.models import Contract
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in [t.name for t in response.templates]
    assert response.context["related_summary"] == {}
    assert list(response.context["protected_objects"]) == []
    assert response.context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_HEADING in content
    assert BLOCKED_SENTENCE in content
    assert BLOCKED_LIST_HEADING not in content
    assert "Secret Contract" not in content


@pytest.mark.django_db
def test_protected_objects_shown_with_view_permission(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """A user granted view_contract sees the protected label inside the single blocked notice."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Contract

    contract = Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert list(response.context["protected_objects"]) == [contract]
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert BLOCKED_LIST_HEADING in content
    assert BLOCKED_SENTENCE not in content
    assert "<li>Publishing Contract</li>" in content


@pytest.mark.django_db
def test_no_protected_objects_no_notice(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert response.context["has_protected_objects"] is False
    assert list(response.context["protected_objects"]) == []
    assert DANGER_ALERT not in _norm(response.content.decode())


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_database_protect_post_returns_blocked_response_and_keeps_storage(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch, modal
):
    from tests.test1.app.models import Contract, Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView, ("cv_form_valid_hook", "cv_on_commit"))
    contract = Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_cascade/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert "<form" not in response.content.decode()
    assert BLOCKED_SENTENCE in response.content.decode()
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


@pytest.mark.django_db
def test_blocked_page_omits_confirmation_form(client_user_publisher_cascade_delete, publisher_penguin):
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    assert content.count(DANGER_ALERT) == 1
    assert "<form" not in content
    assert "id_confirm" not in content
    assert 'name="delete"' not in content


@pytest.mark.django_db
@pytest.mark.parametrize("labelled", [False, True])
def test_blocked_notice_copy_hidden_and_labelled(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, publisher_penguin, labelled
):
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    if labelled:
        user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    if labelled:
        assert BLOCKED_LIST_HEADING in content
        assert "<li>Publishing Contract</li>" in content
        assert BLOCKED_SENTENCE not in content
    else:
        assert BLOCKED_LIST_HEADING not in content
        assert content.count(BLOCKED_SENTENCE) == 1
        assert "Publishing Contract" not in content
    assert "<form" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("blocked", [False, True])
def test_blocked_state_without_related_preview(client_user_publisher_delete, publisher_penguin, blocked):
    from tests.test1.app.models import Contract, Publisher

    if blocked:
        Contract.objects.create(title="Hidden", publisher=publisher_penguin)
    url = f"/publisher/{publisher_penguin.pk}/delete/"
    response = client_user_publisher_delete.get(url)
    assert response.context["has_protected_objects"] is blocked
    assert "protected_objects" not in response.context
    assert "related_summary" not in response.context
    assert ("<form" in response.content.decode()) is not blocked
    response = client_user_publisher_delete.post(url, {"confirm": True})
    assert response.status_code == (200 if blocked else 302)
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists() is blocked


@pytest.mark.django_db
def test_custom_protection_post_modal_422_keeps_storage(
    client_user_publisher_modal_protected_delete, cv_publisher_modal_protected, publisher_penguin
):
    """Custom cv_check_delete_protection errors re-render (422 in the modal), never write."""
    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    response = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS
    )
    assert response.status_code == 422
    assert Publisher.objects.filter(pk=pk).exists()
    full = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", {"confirm": True}
    )
    assert full.status_code == 200
    assert Publisher.objects.filter(pk=pk).exists()


# ── AUTH-01: HTTP DELETE is rejected (D-01/D-02) ─────────────────────────────


def _allow(response) -> set[str]:
    return {m.strip() for m in response.headers.get("Allow", "").split(",") if m.strip()}


def _spy_lifecycle(monkeypatch, view_class, names=("get_context_data", "cv_post_hook", "cv_form_valid_process")):
    calls = []
    for name in names:
        original = getattr(view_class, name)

        def spy(self, *args, _name=name, _original=original, **kwargs):
            calls.append(_name)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(view_class, name, spy)
    return calls


@pytest.mark.django_db
def test_http_delete_rejected_with_405(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.delete(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 405
    allow = _allow(response)
    assert "DELETE" not in allow
    assert {"GET", "POST", "OPTIONS"} <= allow
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_options_allow_omits_delete(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.options(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    allow = _allow(response)
    assert "DELETE" not in allow
    assert {"GET", "POST", "OPTIONS"} <= allow


@pytest.mark.django_db
def test_http_delete_rejected_on_subclass_restoring_method_name(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin, monkeypatch
):
    """A subclass putting "delete" back into http_method_names is still stopped by the dispatch guard."""
    from django.views.generic import View

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    monkeypatch.setattr(PublisherCascadeDeleteView, "http_method_names", list(View.http_method_names))
    calls = _spy_lifecycle(monkeypatch, PublisherCascadeDeleteView)
    pk = publisher_penguin.pk
    url = f"/publisher_cascade/{pk}/delete/"
    response = client_user_publisher_cascade_delete.delete(url)
    assert response.status_code == 405
    assert "DELETE" not in _allow(response)
    options = client_user_publisher_cascade_delete.options(url)
    assert options.status_code == 200
    assert "DELETE" not in _allow(options)
    assert _allow(options) == _allow(response)
    assert calls == []
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_rejection_keeps_modal_vary(client_user_author_modal, author_douglas_adams):
    from tests.test1.app.models import Author

    pk = author_douglas_adams.pk
    for headers in ({}, MODAL_HEADERS):
        response = client_user_author_modal.delete(f"/author_modal/{pk}/delete/", headers=headers)
        assert response.status_code == 405
        assert "X-CV-Modal" in response.headers.get("Vary", "")
    assert Author.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_keeps_earlier_core_gates(client, cv_publisher_cascade, publisher_penguin):
    """Authentication and core permission gates still run before the method rejection."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    url = f"/publisher_cascade/{pk}/delete/"
    anonymous = client.delete(url)
    assert anonymous.status_code == 302
    assert "login" in anonymous.headers["Location"]

    user = User.objects.create_user(username="user_no_delete", password="password")
    client.force_login(user)
    assert client.delete(url).status_code == 403
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_http_delete_missing_target_core(client_user_publisher_cascade_delete, cv_publisher_cascade):
    """The core permission phase loads the object, so a missing target still 404s before the 405 guard."""
    assert client_user_publisher_cascade_delete.delete("/publisher_cascade/999999/delete/").status_code == 404


@pytest.mark.django_db
def test_delete_views_construct_without_custom_delete_warning(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """The guard leaves Django's delete() untouched, so Django 4.2 emits no DeleteViewCustomDeleteWarning."""
    import warnings

    from django.views.generic.edit import DeletionMixin

    from crud_views.lib.views import DeleteView, DeleteViewPermissionRequired
    from crud_views_guardian.lib.views import GuardianDeleteViewPermissionRequired
    from crud_views_polymorphic.lib import PolymorphicDeleteViewPermissionRequired
    from tests.test1.app.views import (
        AuthorModalDeleteView,
        GuardianPublisherCascadeDeleteView,
        PublisherCascadeDeleteView,
        VehicleDeleteView,
    )

    classes = [
        PublisherCascadeDeleteView,
        GuardianPublisherCascadeDeleteView,
        VehicleDeleteView,
        AuthorModalDeleteView,
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for view_class in classes:
            view_class()
        url = f"/publisher_cascade/{publisher_penguin.pk}/delete/"
        client_user_publisher_cascade_delete.get(url)
        client_user_publisher_cascade_delete.delete(url)
    assert [w for w in caught if w.category.__name__ == "DeleteViewCustomDeleteWarning"] == []
    for view_class in (
        DeleteView,
        DeleteViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        PolymorphicDeleteViewPermissionRequired,
        *classes,
    ):
        assert view_class.delete is DeletionMixin.delete


@pytest.mark.django_db
def test_delete_protection_form_clean(publisher_penguin):
    """Form clean() raising ValidationError prevents deletion."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import cv_publisher_form_protected

    user = User.objects.create_user(username="user_form_clean_test", password="password")
    user_viewset_permission(user, cv_publisher_form_protected, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.post(f"/publisher_form_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    assert Publisher.objects.filter(pk=pk).exists()
    assert "Form-level" in response.content.decode()


@pytest.mark.django_db
def test_successful_cascade_delete(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    """With cv_show_related_objects=True, POST still deletes object and cascaded relations."""
    from tests.test1.app.models import Book, Publisher

    book = Book.objects.create(title="Doomed Book", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(f"/publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()
    assert not Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_related_objects_linking(publisher_penguin):
    """With cv_link_related_objects=True, related objects with ViewSets are rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Linked Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    # Grant view permissions so related objects are visible
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    # Related book should be rendered as a clickable link
    import re

    assert re.search(r"<a\s[^>]*>Linked Book</a>", content)


@pytest.mark.django_db
def test_related_objects_linking_context_has_dict_tree(publisher_penguin):
    """With cv_link_related_objects=True, context['related_objects'] is a list of dicts with url keys."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Context Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_ctx_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200

    related_objects = response.context["related_objects"]
    assert isinstance(related_objects, list)
    assert len(related_objects) > 0
    # Each node should be a dict with obj, url, children keys
    node = related_objects[0]
    assert "obj" in node
    assert "url" in node
    assert "children" in node


@pytest.mark.django_db
def test_related_objects_no_linking_when_disabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """With cv_link_related_objects=False (default), related objects are NOT rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Unlinked Book", publisher=publisher_penguin)

    # Grant view permissions so objects are visible in the tree
    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Unlinked Book" in content
    # The related object text should NOT appear inside an <a> tag
    import re

    assert not re.search(r"<a\s[^>]*>Unlinked Book</a>", content)


def _grant_view_publisher_and_book():
    from django.contrib.auth.models import Permission, User

    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        user_obj.user_permissions.add(Permission.objects.get(codename=codename))


@pytest.mark.django_db
def test_related_summary_items_are_ready_strings(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    assert response.context["related_summary_items"] == ["book: 2"]


@pytest.mark.django_db
def test_delete_alerts_render_through_the_frame(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """#250: the protected, summary and tree alerts all come out of tags/alert.html."""
    from tests.test1.app.models import Book, Contract

    _grant_view_publisher_and_book()
    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = re.sub(r"\s+", " ", response.content.decode())
    assert content.count('class="alert alert-danger" role="alert"') == 1
    assert content.count('class="alert alert-warning" role="alert"') == 2
    assert "<li>book: 1</li>" in content
    assert "Book A" in content


def test_delete_alert_headings_translate():
    from django.template.loader import render_to_string
    from django.utils import translation

    with translation.override("de"):
        html = render_to_string(
            "crud_views/snippets/delete/protection_errors.html", {"delete_protection_errors": ["x"]}
        )
    assert "Dieses Objekt kann nicht gelöscht werden:" in html
    assert 'role="alert"' in html


@pytest.mark.django_db
@pytest.mark.parametrize("labelled", [False, True])
def test_blocked_notice_renders_in_german(
    client_user_publisher_cascade_delete, user_publisher_cascade_delete, publisher_penguin, labelled
):
    from django.contrib.auth.models import Permission
    from django.utils import translation

    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    if labelled:
        user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_contract"))
    with translation.override("de"):
        response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    content = _norm(response.content.decode())
    heading = "Das Löschen wird durch geschützte Beziehungen verhindert"
    sentence = (
        "Andere Objekte verweisen noch auf dieses Objekt; entfernen Sie diese Verweise oder ordnen Sie sie neu zu, "
        "bevor Sie es löschen."
    )
    assert "<form" not in content
    if labelled:
        assert f"<strong>{heading}:</strong>" in content
        assert "<li>Publishing Contract</li>" in content
        assert sentence not in content
    else:
        assert f"<strong>{heading}</strong>" in content
        assert sentence in content
        assert "Publishing Contract" not in content
    assert BLOCKED_HEADING not in content
    assert BLOCKED_SENTENCE not in content


def _assert_guard_in_mro(view_class):
    from django.views import generic

    from crud_views.lib.view import CrudView
    from crud_views.lib.views.delete import _DeleteMethodGuardMixin

    mro = view_class.__mro__
    assert mro.index(CrudView) < mro.index(_DeleteMethodGuardMixin) < mro.index(generic.DeleteView)


def _spy_raw_delete_handler(monkeypatch) -> list:
    """Spy on Django's DeletionMixin.delete itself, so concrete classes keep ``delete is DeletionMixin.delete``."""
    from django.views.generic.edit import DeletionMixin

    entered = []
    original = DeletionMixin.delete

    def spy(self, request, *args, **kwargs):
        entered.append(request.method)
        return original(self, request, *args, **kwargs)

    monkeypatch.setattr(DeletionMixin, "delete", spy)
    return entered


@pytest.mark.django_db
def test_registered_core_class_restoring_delete_stays_guarded(
    client_user_publisher_delete, cv_publisher, publisher_penguin, monkeypatch
):
    """A18/A22: the registered PublisherDeleteView, patched to list "delete" again, inherits the dispatch guard."""
    from django.views.generic import View

    from crud_views.lib.views import DeleteView
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherDeleteView

    _assert_guard_in_mro(PublisherDeleteView)
    original = PublisherDeleteView.http_method_names
    inherited = list(DeleteView.http_method_names)
    url = f"/publisher/{publisher_penguin.pk}/delete/"
    with monkeypatch.context() as patch:
        patch.setattr(PublisherDeleteView, "http_method_names", [*View.http_method_names])
        assert "delete" in PublisherDeleteView.http_method_names
        entered = _spy_raw_delete_handler(patch)
        response = client_user_publisher_delete.delete(url)
        options = client_user_publisher_delete.options(url)
        assert response.status_code == 405
        assert options.status_code == 200
        assert "DELETE" not in _allow(response)
        assert _allow(options) == _allow(response)
        assert entered == []
    assert PublisherDeleteView.http_method_names is original
    assert "delete" not in PublisherDeleteView.http_method_names
    assert DeleteView.http_method_names == inherited
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()


@pytest.mark.django_db
def test_database_restrict_preview_and_post_keep_storage(client_user_publisher_cascade_delete, publisher_penguin):
    from tests.test1.app.models import Publisher, Royalty

    royalty = Royalty.objects.create(publisher=publisher_penguin, title="Hidden Royalty")
    url = f"/publisher_cascade/{publisher_penguin.pk}/delete/"
    response = client_user_publisher_cascade_delete.get(url)
    assert response.context["has_protected_objects"] is True
    assert response.context["protected_objects"] == []
    assert _response_instances(response, Royalty) == []
    assert "<form" not in response.content.decode()
    response = client_user_publisher_cascade_delete.post(url, {"confirm": True})
    assert response.status_code == 200
    assert BLOCKED_SENTENCE in response.content.decode()
    assert "<form" not in response.content.decode()
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()
    assert Royalty.objects.filter(pk=royalty.pk).exists()


def _delete_probe(monkeypatch, atomic):
    """Exercise the registered route with real writes and an intentionally stale preview."""
    from crud_views.lib.views.delete import RelatedObjects
    from tests.test1.app.views import PublisherDeleteView

    calls = []
    monkeypatch.setattr(PublisherDeleteView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherDeleteView, "cv_get_related_objects", lambda self: RelatedObjects([], {}, []))
    monkeypatch.setattr(PublisherDeleteView, "cv_form_valid_hook", lambda self, context: calls.append("success"))
    monkeypatch.setattr(PublisherDeleteView, "cv_on_commit", lambda self, context: calls.append("commit"))
    original = PublisherDeleteView._cv_protection_response

    def response(self, context):
        calls.append("blocked")
        return original(self, context)

    monkeypatch.setattr(PublisherDeleteView, "_cv_protection_response", response)
    return PublisherDeleteView, calls


def _protector(error_name, publisher):
    from tests.test1.app.models import Contract, Royalty

    model = Contract if error_name == "ProtectedError" else Royalty
    return model.objects.create(publisher=publisher, title="Hidden protector")


def _error_type(error_name):
    from django.db.models import ProtectedError, RestrictedError

    return ProtectedError if error_name == "ProtectedError" else RestrictedError


@pytest.mark.django_db
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("method", ["get", "post"])
def test_delete_preview_override_called_once(
    client_user_publisher_delete, publisher_penguin, monkeypatch, preview, method
):
    from crud_views.lib.views.delete import RelatedObjects
    from tests.test1.app.models import Contract
    from tests.test1.app.views import PublisherDeleteView

    contract = Contract.objects.create(title="Never projected", publisher=publisher_penguin)
    seen = []

    def related(self):
        seen.append(self.object.pk)
        return RelatedObjects([], {}, [contract])

    monkeypatch.setattr(PublisherDeleteView, "cv_get_related_objects", related)
    monkeypatch.setattr(PublisherDeleteView, "cv_show_related_objects", preview)
    response = getattr(client_user_publisher_delete, method)(
        f"/publisher/{publisher_penguin.pk}/delete/", {"confirm": True}
    )
    assert seen == [publisher_penguin.pk]
    assert response.context["has_protected_objects"] is True
    assert _response_instances(response, Contract) == []
    assert ("protected_objects" in response.context) is preview


@pytest.mark.django_db
def test_delete_default_collection_uses_write_router(client_user_publisher_delete, publisher_penguin, monkeypatch):
    from crud_views.lib.views import delete

    seen = []
    original = delete.NestedObjects

    class RecordingCollector(original):
        def __init__(self, using, *args, **kwargs):
            seen.append(using)
            super().__init__(using, *args, **kwargs)

    routed = []

    def db_for_write(model, **hints):
        routed.append(model)
        return "default"

    monkeypatch.setattr(delete.router, "db_for_write", db_for_write)
    monkeypatch.setattr(delete, "NestedObjects", RecordingCollector)
    response = client_user_publisher_delete.get(f"/publisher/{publisher_penguin.pk}/delete/")
    assert response.context["has_protected_objects"] is False
    assert seen == ["default"]
    assert type(publisher_penguin) in routed


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_blocked_invalid_confirmation_keeps_invalid_path(
    client_user_publisher_delete, publisher_penguin, monkeypatch, modal
):
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherDeleteView

    protector = _protector("ProtectedError", publisher_penguin)
    monkeypatch.setattr(PublisherDeleteView, "cv_modal", True)
    calls = _spy_lifecycle(
        monkeypatch, PublisherDeleteView, ("cv_form_invalid_hook", "cv_form_valid_hook", "cv_on_commit")
    )
    response = client_user_publisher_delete.post(
        f"/publisher/{publisher_penguin.pk}/delete/", {}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert response.context["form"].errors
    assert "<form" not in response.content.decode()
    assert calls == ["cv_form_invalid_hook"]
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()
    assert type(protector).objects.filter(pk=protector.pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("nested", [False, True])
def test_delete_callback_protection_error_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, nested
):
    from django.db import connection

    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    unrelated = Publisher.objects.create(name="Unrelated")
    protector = _protector(error_name, unrelated)
    error = _error_type(error_name)("Callback failure", {protector})
    raised = []

    def callback(self, context):
        calls.append("commit")
        assert not connection.in_atomic_block
        try:
            if nested:
                unrelated.delete()
            raise error
        except _error_type(error_name) as exc:
            raised.append(exc)
            raise

    monkeypatch.setattr(view, "cv_on_commit", callback)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[0]
    assert not Publisher.objects.filter(pk=target.pk).exists()
    assert Publisher.objects.filter(pk=unrelated.pk).exists()
    assert calls == ["success", "commit"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_success_hook_protection_error_keeps_atomic_semantics(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Success hook failure", set())

    def success(self, context):
        calls.append("success")
        raise error

    monkeypatch.setattr(view, "cv_form_valid_hook", success)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is error
    assert Publisher.objects.filter(pk=target.pk).exists() is atomic
    assert calls == ["success"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("stage", ["before", "after", "write_then_protected"])
def test_delete_model_override_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name, stage
):
    from django.db.models import Model

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    if stage == "write_then_protected":
        _protector(error_name, target)
    error = _error_type(error_name)("Model override failure", set())
    raised = []

    def delete(self, *args, **kwargs):
        try:
            if stage == "before":
                raise error
            Publisher.objects.create(name="Side effect")
            Model.delete(self, *args, **kwargs)
            raise error
        except _error_type(error_name) as exc:
            raised.append(exc)
            raise

    monkeypatch.setattr(Publisher, "delete", delete)
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[0]
    assert Publisher.objects.filter(pk=target.pk).exists() is (stage != "after" or atomic)
    assert Publisher.objects.filter(name="Side effect").exists() is (stage != "before" and not atomic)
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("signal_name", ["pre_delete", "post_delete"])
def test_delete_signal_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name, signal_name
):
    from django.db.models import signals

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Signal failure", set())

    def receiver(**kwargs):
        calls.append(signal_name)
        raise error

    signal = getattr(signals, signal_name)
    signal.connect(receiver, sender=Publisher, weak=False)
    try:
        with pytest.raises(_error_type(error_name)) as caught:
            client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
        assert caught.value is error
        assert Publisher.objects.filter(pk=target.pk).exists()
        assert calls == [signal_name]
    finally:
        signal.disconnect(receiver, sender=Publisher)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_signal_commit_protection_error_propagates(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from django.db import connection, transaction
    from django.db.models.signals import post_delete

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    error = _error_type(error_name)("Signal callback failure", set())

    def callback():
        calls.append("signal_commit")
        assert not connection.in_atomic_block
        raise error

    def receiver(**kwargs):
        transaction.on_commit(callback)

    post_delete.connect(receiver, sender=Publisher, weak=False)
    try:
        with pytest.raises(_error_type(error_name)) as caught:
            client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
        assert caught.value is error
        assert not Publisher.objects.filter(pk=target.pk).exists()
        assert calls == (["success", "signal_commit"] if atomic else ["signal_commit"])
    finally:
        post_delete.disconnect(receiver, sender=Publisher)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_delete_success_real_commit_order(client_user_publisher_delete, monkeypatch, atomic, modal):
    from django.db import connection
    from django.db.models import Model

    from tests.test1.app.models import Publisher

    view, calls = _delete_probe(monkeypatch, atomic)
    monkeypatch.setattr(view, "cv_modal", True)
    target = Publisher.objects.create(name="Target")

    def delete(self):
        calls.append("delete")
        return Model.delete(self)

    def callback(self, context):
        assert not connection.in_atomic_block
        calls.append("commit")

    monkeypatch.setattr(Publisher, "delete", delete)
    monkeypatch.setattr(view, "cv_on_commit", callback)
    response = client_user_publisher_delete.post(
        f"/publisher/{target.pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (204 if modal else 302)
    if modal:
        assert response.headers["X-CV-Redirect"]
    assert calls == ["delete", "success", "commit"]
    assert not Publisher.objects.filter(pk=target.pk).exists()


def _collection_snapshot():
    from tests.test1.app.models import Book, BookNote, Contract, Publisher, Royalty

    return {
        model: list(
            model.objects.exclude(**({"name": "Side effect"} if model is Publisher else {})).order_by("pk").values()
        )
        for model in (Publisher, Book, BookNote, Contract, Royalty)
    }


def _assert_collection_extension_propagates(client, target, calls, atomic, error_name, before):
    from tests.test1.app.models import Publisher

    with pytest.raises(_error_type(error_name)) as caught:
        client.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert _collection_snapshot() == before
    assert Publisher.objects.filter(name="Side effect").exists() is not atomic
    assert "success" not in calls
    assert "commit" not in calls
    assert "blocked" not in calls
    return caught.value


def _assert_handler_error(error, original, error_name, objects):
    from django.db.models.deletion import Collector

    if error_name == "ProtectedError":
        assert error is not original  # Django replaces even custom-handler errors with an aggregate.
        assert set(objects) <= set(error.protected_objects)
        tb = error.__traceback__
        while tb.tb_next is not None:
            tb = tb.tb_next
        assert tb.tb_frame.f_code is Collector.collect.__code__
    else:
        assert error is original


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("mode", ["raise", "nested_delete", "return"])
def test_delete_custom_relationship_handler_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, mode
):
    from crud_views.lib.views.delete import _cv_has_native_collection_graph
    from tests.test1.app.models import Book, Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    book = Book.objects.create(title="Cascade", publisher=target)
    unrelated = Publisher.objects.create(name="Unrelated")
    protector = _protector(error_name, target if mode == "return" else unrelated)
    raised = []

    def handler(collector, field, objects, using):
        calls.append("handler")
        Publisher.objects.create(name="Side effect")
        # Changing the handler back now must not retroactively certify the collection.
        if mode == "return":
            from django.db.models import CASCADE

            monkeypatch.setattr(field.remote_field, "on_delete", CASCADE)
            return
        try:
            if mode == "nested_delete":
                unrelated.delete()
            raise _error_type(error_name)("Custom handler", {book})
        except _error_type(error_name) as error:
            raised.append(error)
            raise

    monkeypatch.setattr(Book._meta.get_field("publisher").remote_field, "on_delete", handler)
    assert not _cv_has_native_collection_graph(target)
    before = _collection_snapshot()
    error = _assert_collection_extension_propagates(
        client_user_publisher_delete, target, calls, atomic, error_name, before
    )
    assert calls == ["handler"]
    if mode != "return":
        _assert_handler_error(error, raised[0], error_name, [protector if mode == "nested_delete" else book])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_nested_relationship_handler_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from crud_views.lib.views.delete import _cv_has_native_collection_graph
    from tests.test1.app.models import Book, BookNote, Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    book = Book.objects.create(title="Cascade", publisher=target)
    note = BookNote.objects.create(book=book, note="Nested")
    original = _error_type(error_name)("Nested handler", {note})

    def handler(collector, field, objects, using):
        calls.append("nested_handler")
        Publisher.objects.create(name="Side effect")
        raise original

    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", handler)
    assert not _cv_has_native_collection_graph(target)
    before = _collection_snapshot()
    error = _assert_collection_extension_propagates(
        client_user_publisher_delete, target, calls, atomic, error_name, before
    )
    assert calls == ["nested_handler"]
    _assert_handler_error(error, original, error_name, [note])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("configured", ["SET", "SET_DEFAULT"])
def test_delete_callable_relationship_default_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name, configured
):
    from django.db.models import SET, SET_DEFAULT

    from crud_views.lib.views.delete import _cv_has_native_collection_graph
    from tests.test1.app.models import Book, Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    Book.objects.create(title="Cascade", publisher=target)
    _protector(error_name, target)

    def default():
        calls.append("default")
        return Publisher.objects.create(name="Side effect").pk

    field = Book._meta.get_field("publisher")
    if configured == "SET":
        monkeypatch.setattr(field.remote_field, "on_delete", SET(default))
    else:
        monkeypatch.setattr(field.remote_field, "on_delete", SET_DEFAULT)
        # Materialize the original cached default before replacing it, so teardown restores it too.
        original_default = field._get_default
        monkeypatch.setattr(field, "default", default)
        monkeypatch.setattr(field, "_get_default", default)
        assert original_default is not default
    assert not _cv_has_native_collection_graph(target)
    assert calls == []
    before = _collection_snapshot()
    _assert_collection_extension_propagates(client_user_publisher_delete, target, calls, atomic, error_name, before)
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_unknown_collection_loader_propagates_after_real_commit(
    client_user_publisher_delete, monkeypatch, atomic, error_name
):
    from django.db.models import Model

    from crud_views.lib.views.delete import _cv_has_native_collection_graph
    from tests.test1.app.models import Book, Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    Book.objects.create(title="Cascade", publisher=target)
    _protector(error_name, target)

    def from_db(cls, db, field_names, values):
        calls.append("loader")
        Publisher.objects.create(name="Side effect")
        return Model.from_db.__func__(cls, db, field_names, values)

    monkeypatch.setattr(Book, "from_db", classmethod(from_db))
    assert not _cv_has_native_collection_graph(target)
    assert calls == []
    before = _collection_snapshot()
    _assert_collection_extension_propagates(client_user_publisher_delete, target, calls, atomic, error_name, before)
    assert calls == ["loader"]


@pytest.mark.parametrize(
    "handler_name,eligible",
    [
        ("CASCADE", True),
        ("PROTECT", True),
        ("RESTRICT", True),
        ("SET_NULL", True),
        ("DO_NOTHING", True),
        ("custom", False),
        ("SET-value", False),
        ("SET-callable", False),
        ("SET_DEFAULT", False),
    ],
)
def test_delete_native_collection_graph_eligibility(monkeypatch, handler_name, eligible):
    from django.db import models

    from crud_views.lib.views.delete import _cv_has_native_collection_graph
    from tests.test1.app.models import Book, Publisher

    def unknown(*args):
        pytest.fail("Metadata classifier executed a callback")

    if handler_name == "custom":
        handler = unknown
    elif handler_name.startswith("SET-"):
        handler = models.SET(unknown if handler_name == "SET-callable" else 1)
    else:
        handler = getattr(models, handler_name)
    monkeypatch.setattr(Book._meta.get_field("publisher").remote_field, "on_delete", handler)
    # No database access is permitted by this test; no relation has rows.
    assert _cv_has_native_collection_graph(Publisher()) is eligible


@pytest.mark.parametrize(
    "extension", ["manager", "queryset", "init", "from_db", "pre_init", "post_init", "private", "field", "missing"]
)
def test_delete_native_collection_graph_rejects_unknown_metadata(monkeypatch, extension):
    from types import SimpleNamespace

    from django.db import models
    from django.db.models import signals

    from crud_views.lib.views import delete
    from tests.test1.app.models import Book, Publisher

    target = Publisher()
    if extension == "manager":

        class CustomManager(models.Manager):
            pass

        monkeypatch.setitem(Book._meta.__dict__, "base_manager", CustomManager())
    elif extension == "queryset":

        class CustomQuerySet(models.QuerySet):
            pass

        monkeypatch.setattr(Book._base_manager, "_queryset_class", CustomQuerySet)
    elif extension == "init":
        monkeypatch.setattr(Book, "__init__", lambda self: None)
    elif extension == "from_db":
        monkeypatch.setattr(Book, "from_db", classmethod(lambda *args: None))
    elif extension == "private":
        monkeypatch.setattr(Book._meta, "private_fields", [SimpleNamespace(bulk_related_objects=lambda *args: [])])
    elif extension in ("field", "missing"):
        relation = SimpleNamespace(field=object()) if extension == "field" else object()
        monkeypatch.setattr(delete, "get_candidate_relations_to_delete", lambda opts: [relation])
    else:
        signal = getattr(signals, extension)

        def receiver(**kwargs):
            pytest.fail("Metadata classifier initialized a model")

        signal.connect(receiver, sender=Book, weak=False)
        try:
            assert not delete._cv_has_native_collection_graph(target)
        finally:
            signal.disconnect(receiver, sender=Book)
        return
    assert not delete._cv_has_native_collection_graph(target)


def test_delete_native_collection_graph_terminates_cycles(monkeypatch):
    from types import SimpleNamespace

    from crud_views.lib.views import delete
    from tests.test1.app.models import Book, Publisher, PublisherProxy

    # Native ordinary field metadata with a self-referential cascade; no database query or schema needed.
    field = Book._meta.get_field("publisher")
    monkeypatch.setattr(
        delete,
        "get_candidate_relations_to_delete",
        lambda opts: [SimpleNamespace(field=field, related_model=Publisher)],
    )
    assert delete._cv_has_native_collection_graph(Publisher())
    assert delete._cv_has_native_collection_graph(PublisherProxy())


@pytest.mark.django_db
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_target_collection_provenance(publisher_penguin, error_name):
    from crud_views.lib.views.delete import _cv_has_native_collection_graph, _cv_is_target_collection_protection
    from tests.test1.app.models import Publisher

    _protector(error_name, publisher_penguin)
    native_graph = _cv_has_native_collection_graph(publisher_penguin)
    assert native_graph
    method = publisher_penguin.delete
    with pytest.raises(_error_type(error_name)) as caught:
        method()
    assert _cv_is_target_collection_protection(caught.value, publisher_penguin, method, native_graph)
    assert not _cv_is_target_collection_protection(caught.value, publisher_penguin, method, False)
    assert not _cv_is_target_collection_protection(caught.value, Publisher(), method, True)
    assert not _cv_is_target_collection_protection(caught.value, publisher_penguin, lambda: None, True)
    assert not _cv_is_target_collection_protection(
        _error_type(error_name)("No frames", set()), publisher_penguin, method, True
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
@pytest.mark.parametrize("modal", [False, True])
def test_delete_native_target_backstop_keeps_storage(
    client_user_publisher_cascade_delete, monkeypatch, atomic, error_name, modal
):
    from crud_views.lib.views.delete import RelatedObjects
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import PublisherCascadeDeleteView

    target = Publisher.objects.create(name="Native target")
    protector = _protector(error_name, target)
    view = PublisherCascadeDeleteView
    monkeypatch.setattr(view, "cv_atomic", atomic)
    monkeypatch.setattr(view, "cv_modal", True)
    preview_calls = []

    def stale_preview(self):
        preview_calls.append(self.object.pk)
        return RelatedObjects([], {}, [])

    monkeypatch.setattr(view, "cv_get_related_objects", stale_preview)
    calls = _spy_lifecycle(monkeypatch, view, ("cv_form_valid_hook", "cv_on_commit"))
    before = _collection_snapshot()
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_cascade/{target.pk}/delete/", {"confirm": True}, headers=MODAL_HEADERS if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert response.context["has_protected_objects"] is True
    content = _norm(response.content.decode())
    assert content.count(f"<strong>{BLOCKED_HEADING}</strong>") == 1
    assert content.count(BLOCKED_SENTENCE) == 1
    assert BLOCKED_LIST_HEADING not in content
    assert "<form" not in content
    assert protector.title not in content
    assert _response_instances(response, type(protector)) == []
    assert preview_calls == [target.pk]
    assert _collection_snapshot() == before
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("error_name", ["ProtectedError", "RestrictedError"])
def test_delete_unknown_collector_type_propagates(client_user_publisher_delete, monkeypatch, atomic, error_name):
    from django.db.models import base
    from django.db.models.deletion import Collector

    from tests.test1.app.models import Publisher

    _, calls = _delete_probe(monkeypatch, atomic)
    target = Publisher.objects.create(name="Target")
    _protector(error_name, target)
    raised = []

    class UnknownCollector(Collector):
        def collect(self, *args, **kwargs):
            try:
                return super().collect(*args, **kwargs)
            except _error_type(error_name) as error:
                raised.append(error)
                raise

    monkeypatch.setattr(base, "Collector", UnknownCollector)
    before = _collection_snapshot()
    with pytest.raises(_error_type(error_name)) as caught:
        client_user_publisher_delete.post(f"/publisher/{target.pk}/delete/", {"confirm": True})
    assert caught.value is raised[-1]
    assert _collection_snapshot() == before
    assert calls == []
