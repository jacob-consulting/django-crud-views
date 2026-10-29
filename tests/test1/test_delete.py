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
BLOCKED_HEADING = "Deletion is blocked by protected relationships:"
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
    assert BLOCKED_HEADING in content
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
def test_database_protect_post_raises_and_keeps_storage(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """A confirmed POST against a database PROTECT relation keeps raising ProtectedError (unchanged lifecycle)."""
    from django.db.models import ProtectedError

    from tests.test1.app.models import Contract, Publisher

    contract = Contract.objects.create(title="Secret Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    with pytest.raises(ProtectedError):
        client_user_publisher_cascade_delete.post(f"/publisher_cascade/{pk}/delete/", {"confirm": True})
    assert Publisher.objects.filter(pk=pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()


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
