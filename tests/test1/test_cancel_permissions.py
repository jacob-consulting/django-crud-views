"""Destination-owned cancel authorization and actionable fallback configuration."""

import ast
from pathlib import Path

import pytest
from django.core.checks import Error
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http import Http404
from django.test import RequestFactory
from django.views.generic.edit import FormMixin

from crud_views.lib.view import CrudView
from crud_views.lib.view.cancel import effective_cancel_keys
from crud_views.lib.viewset import ViewSet, _REGISTRY, _REGISTRY_LOCK
from tests.test1.test_cancel_origin import cancel_url, url


def fallback_errors(cls):
    return [m for c in cls.checks() for m in c.messages() if m.id == "viewset.E256"]


def bound(cls, user, obj=None, query=None, **kwargs):
    view = cls()
    request = RequestFactory().get("/", query or {})
    request.user = user
    view.setup(request, **kwargs)
    view.object = obj
    return view


# Captured before E256 existed, from normal imports and a collect-all run. Each
# registered form has a named disposition; local fixtures are deliberately absent.
VALID_FORMS = {
    "author": "AuthorCreateView AuthorUpdateView AuthorDeleteView AuthorContactView",
    "author_modal": "AuthorModalDeleteView AuthorModalContactView",
    "author_origin": "AuthorOriginCreateView AuthorOriginUpdateView AuthorOriginDeleteView "
    "AuthorOriginContactView AuthorOriginBroadcastView",
    "author_wide_card": "AuthorWideCardCreateView AuthorWideCardUpdateView",
    "book": "BookCreateView BookUpdateView BookDeleteView",
    "book_bc": "BookBcUpdateView",
    "campaign": "CampaignWorkflowView",
    "genre": "GenreCreateView",
    "guardian_author": "GuardianAuthorCreateView GuardianAuthorUpdateView GuardianAuthorDeleteView",
    "guardian_author_origin": "GuardianAuthorOriginUpdateView",
    "guardian_book": "GuardianBookCreateView GuardianBookUpdateView GuardianBookDeleteView",
    "guardian_publisher": "GuardianPublisherCreateView GuardianPublisherUpdateView GuardianPublisherDeleteView",
    "guardian_publisher_cascade": "GuardianPublisherCascadeDeleteView",
    "publisher": "PublisherCreateView PublisherUpdateView PublisherDeleteView",
    "publisher_bc": "PublisherBcCreateView PublisherBcUpdateView",
    "publisher_bc_nodetail": "PublisherBcNodetailUpdateView",
    "publisher_cascade": "PublisherCascadeDeleteView",
    "publisher_form_protected": "PublisherFormProtectedDeleteView",
    "publisher_linked": "PublisherLinkedDeleteView",
    "publisher_modal_protected": "PublisherModalProtectedDeleteView",
    "publisher_protected": "PublisherProtectedDeleteView",
    "vehicle": "VehicleCreateSelectView VehicleCreateView VehicleUpdateView VehicleDeleteView",
}
COLLECTED_VALID = {
    "publisher_formset": "PublisherFormSetCreateView PublisherFormSetUpdateView",
    "readme": "ReadmeAuthorCreate ReadmeAuthorUpdate ReadmeAuthorDelete",
}
COLLECTED_INVALID = {
    "profile_check": "_ProfileCreateView",
    "profile_formset_check": "_ProfileFormsetCreateView _ProfileFormsetUpdateView",
    "profile_purge_conflict_check": "_ProfilePurgeConflictCreateView",
    "profile_shared_toggle_check": "_ProfileSharedToggleCreateView",
    "profile_ui_formset_check": "_ProfileUIFormsetCreateView",
}


def test_registered_cancel_fallback_inventory(monkeypatch, record_property):
    import tests.test1.app.views  # noqa: F401

    snapshot = dict(_REGISTRY)
    expected = {
        (name, cls): name in COLLECTED_INVALID
        for name, classes in (VALID_FORMS | COLLECTED_VALID | COLLECTED_INVALID).items()
        for cls in classes.split()
        if name in snapshot
    }
    inventory = {}
    try:
        for name, vs in snapshot.items():
            for cls in vs.get_all_views().values():
                if not issubclass(cls, FormMixin):
                    continue
                identity = (name, cls.__name__)
                inventory[identity] = (cls.cv_cancel_key, effective_cancel_keys(cls))
                assert identity in expected, (identity, inventory[identity])
                errors = fallback_errors(cls)
                assert bool(errors) is expected[identity], (identity, inventory[identity], errors)
                if expected[identity]:
                    assert len(errors) == 1 and isinstance(errors[0], Error)
                    assert cls.__name__ in errors[0].msg
                    assert "cv_cancel_key='list'" in errors[0].msg
                    # These diagnostic-only fixtures intentionally have no list.
                    # Their own registered no-object form is an explicit usable route.
                    with monkeypatch.context() as patch:
                        patch.setattr(cls, "cv_cancel_key", cls.cv_key)
                        assert not fallback_errors(cls)
        assert set(inventory) == set(expected)
        assert set(VALID_FORMS) <= set(snapshot)
        record_property("cancel_fallback_inventory", repr(inventory))
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(snapshot)


def test_fallback_diagnostic_identifier_is_unique():
    declarations = []
    for path in Path("src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.keyword) and node.arg == "id":
                if isinstance(node.value, ast.Constant) and node.value.value == "E256":
                    declarations.append(str(path))
    assert declarations == ["src/crud_views/lib/view/base.py"]


@pytest.mark.parametrize("static,expected", [(False, False), (True, True)])
def test_core_fallback_startup_diagnostic(cv_publisher, monkeypatch, static, expected):
    cls = cv_publisher.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_key", "missing")
    if static:
        monkeypatch.setattr(cls, "cv_cancel_keys", None)
    assert bool(fallback_errors(cls)) is expected
    monkeypatch.setattr(cls, "cv_cancel_keys", ["create"])
    assert not fallback_errors(cls)
    monkeypatch.setattr(cls, "cv_cancel_keys", [])
    assert fallback_errors(cls)
    monkeypatch.setattr(cls, "cv_cancel_key", None)
    assert not fallback_errors(cls)


def test_core_fallback_diagnostic_scoped_to_forms(cv_publisher, monkeypatch):
    for key in ("detail", "list"):
        cls = cv_publisher.get_view_class(key)
        monkeypatch.setattr(cls, "cv_cancel_key", "missing")
        assert not fallback_errors(cls)
    selector = ViewSet.get_viewset("vehicle").get_view_class("create_select")
    monkeypatch.setattr(selector, "cv_cancel_key", "missing")
    assert fallback_errors(selector)


@pytest.mark.django_db
def test_core_fallback_runtime_only_when_needed(cv_publisher, publisher_penguin, user_publisher_view, monkeypatch):
    cls = cv_publisher.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_key", "missing")
    view = bound(cls, user_publisher_view, publisher_penguin, {"cv_from": "detail"})
    assert view.cv_get_cancel_url() == url(cv_publisher, "detail", publisher_penguin.pk)
    view.request.GET = view.request.GET.copy()
    view.request.GET["cv_from"] = "invalid"
    with pytest.raises(ImproperlyConfigured, match="cv_cancel_key='missing'.*registered.*usable"):
        view.cv_get_cancel_url()
    monkeypatch.setattr(cls, "cv_cancel_key", "detail")
    view.object = None
    with pytest.raises(ImproperlyConfigured, match="cv_cancel_key='detail'"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_core_fallback_permission_then_state(cv_publisher, publisher_penguin, user_publisher_view, monkeypatch, mode):
    detail = cv_publisher.get_view_class("detail")
    listing = cv_publisher.get_view_class("list")
    events = []
    monkeypatch.setattr(
        detail, "cv_has_access", classmethod(lambda cls, user, obj: events.append(("deny", obj)) or False)
    )
    monkeypatch.setattr(detail, "cv_action_enabled", classmethod(lambda *args: pytest.fail("state after denial")))
    monkeypatch.setattr(listing, "cv_inaccessible_actions", mode)
    view = bound(cv_publisher.get_view_class("update"), user_publisher_view, publisher_penguin, {"cv_from": "detail"})
    assert view.cv_get_cancel_url() == url(cv_publisher, "list")
    assert events == [("deny", publisher_penguin)]
    monkeypatch.setattr(listing, "cv_has_access", classmethod(lambda *args: False))
    assert view.cv_get_cancel_url() is None


@pytest.mark.django_db
def test_core_omitted_cancel_keeps_submission(client_user_publisher_change, cv_publisher, publisher_penguin):
    endpoint = url(cv_publisher, "update", publisher_penguin.pk)
    response = client_user_publisher_change.get(endpoint)
    assert response.status_code == 200
    assert "data-cv-cancel-url" not in response.content.decode()
    response = client_user_publisher_change.post(endpoint, {"name": "Updated without Cancel"})
    assert response.status_code == 302
    publisher_penguin.refresh_from_db()
    assert publisher_penguin.name == "Updated without Cancel"


@pytest.mark.django_db
@pytest.mark.parametrize("error", [Http404, KeyError, DatabaseError])
def test_core_custom_parent_errors_propagate(cv_book, user_book_view, publisher_penguin, monkeypatch, error):
    cls = cv_book.get_view_class("create")

    def fail(self):
        raise error("custom parent hook")

    monkeypatch.setattr(cls, "cv_get_parent_object", fail)
    view = bound(cls, user_book_view, **{cv_book.parent.get_pk_name(): publisher_penguin.pk})
    with pytest.raises(error, match="custom parent hook"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
def test_core_missing_parent_unavailable_and_missing_kwargs_propagate(cv_book, user_book_view):
    cls = cv_book.get_view_class("create")
    view = bound(cls, user_book_view, **{cv_book.parent.get_pk_name(): 999999})
    assert view.cv_get_cancel_url() is None
    view.kwargs.clear()
    with pytest.raises(KeyError):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("error", [Http404, KeyError, DatabaseError])
def test_core_state_errors_propagate(cv_publisher, user_publisher_view, monkeypatch, error):
    def fail(*args):
        raise error("state hook")

    monkeypatch.setattr(cv_publisher.get_view_class("list"), "cv_action_enabled", classmethod(fail))
    with pytest.raises(error, match="state hook"):
        bound(cv_publisher.get_view_class("create"), user_publisher_view).cv_get_cancel_url()
