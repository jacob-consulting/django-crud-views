"""Destination-owned cancel authorization and actionable fallback configuration."""

import ast
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from django.core.checks import Error
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings
from django.urls import clear_url_caches, include, path
from django.views.generic.edit import FormMixin

from crud_views.lib.view.cancel import effective_cancel_keys
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from tests.test1 import test_guardian_parent_none as parent_none
from tests.test1.test_cancel_origin import cancel_url, url
from tests.test1.test_guardian_parent_none import _grant_global, _url, _user

pn = parent_none.pn


def fallback_errors(cls):
    return [m for c in cls.checks() for m in c.messages() if m.id == "viewset.E256"]


def bound(cls, user, obj=None, query=None, **kwargs):
    view = cls()
    request = RequestFactory().get("/", query or {})
    request.user = user
    request.resolver_match = SimpleNamespace(url_name=cls.cv_viewset.get_router_name(cls.cv_key))
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
    "s3file": "S3FileDeleteView",
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
    import tests.test1.app.urls  # noqa: F401 -- include the lazily loaded Resource forms

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
                    assert len(errors) == 1
                    assert isinstance(errors[0], Error)
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
    for source in Path("src").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if (
                isinstance(node, ast.keyword)
                and node.arg == "id"
                and isinstance(node.value, ast.Constant)
                and node.value.value == "E256"
            ):
                declarations.append(str(source))
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


@pytest.mark.parametrize("keys", [[{}], [[]], 42], ids=["dict-entry", "list-entry", "noniterable"])
@pytest.mark.parametrize("fallback", ["missing", "list"])
def test_core_fallback_diagnostic_handles_malformed_keys(cv_publisher, monkeypatch, keys, fallback):
    cls = cv_publisher.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_key", fallback)
    monkeypatch.setattr(cls, "cv_cancel_keys", keys)
    monkeypatch.setattr(cls, "cv_inaccessible_actions", "invalid")
    messages = [message for check in cls.checks() for message in check.messages()]
    ids = [message.id for message in messages]
    assert ids.count("viewset.E252") == 1
    assert ids.count("viewset.E256") == (1 if fallback == "missing" else 0)
    assert "viewset.E207" in ids  # A later independent diagnostic must still run.


def test_core_fallback_diagnostic_propagates_application_errors(cv_publisher, monkeypatch):
    cls = cv_publisher.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_key", "missing")
    monkeypatch.setattr(cls, "cv_cancel_keys", ["list"])
    original = cls._cv_cancel_key_usable

    def usable(cls, key):
        if key == "list":
            raise TypeError("application route failure")
        return original(key)

    monkeypatch.setattr(cls, "_cv_cancel_key_usable", classmethod(usable))
    with pytest.raises(TypeError, match="application route failure"):
        list(cls.checks())


def test_core_fallback_diagnostic_scoped_to_forms(cv_publisher, monkeypatch):
    for key in ("detail", "list"):
        cls = cv_publisher.get_view_class(key)
        monkeypatch.setattr(cls, "cv_cancel_key", "missing")
        assert not fallback_errors(cls)
    selector = ViewSet.get_viewset("vehicle").get_view_class("create_select")
    monkeypatch.setattr(selector, "cv_cancel_key", "missing")
    assert not fallback_errors(selector)  # automatic cancellation has a usable list origin
    monkeypatch.setattr(selector, "cv_cancel_keys", None)
    assert fallback_errors(selector)


@pytest.mark.django_db
def test_core_fallback_runtime_only_when_needed(cv_publisher, publisher_penguin, user_publisher_view, monkeypatch):
    cls = cv_publisher.get_view_class("update")
    monkeypatch.setattr(cls, "cv_cancel_key", "missing")
    view = bound(cls, user_publisher_view, publisher_penguin, {"cv_from": "detail"})
    assert view.cv_get_cancel_url() == url(cv_publisher, "detail", publisher_penguin.pk)
    view.request.GET = view.request.GET.copy()
    view.request.GET["cv_from"] = "invalid"
    with pytest.raises(ImproperlyConfigured, match=r"cv_cancel_key='missing'.*registered.*usable"):
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
    with pytest.raises((KeyError, ValueError)):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("error", [Http404, KeyError, DatabaseError])
def test_core_state_errors_propagate(cv_publisher, user_publisher_view, monkeypatch, error):
    def fail(*args):
        raise error("state hook")

    monkeypatch.setattr(cv_publisher.get_view_class("list"), "cv_action_enabled", classmethod(fail))
    view = bound(cv_publisher.get_view_class("create"), user_publisher_view)
    with pytest.raises(error, match="state hook"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("enabled", [False, True])
def test_core_custom_create_and_rendering_adapter(cv_publisher, user_publisher_add, client, monkeypatch, enabled):
    target = cv_publisher.get_view_class("create")
    events = []

    @classmethod
    def state(cls, user, obj=None):
        events.append(("state", obj))
        return enabled

    @classmethod
    def adapter(cls, user, obj, rendering_view):
        events.append(("adapter", obj))
        assert rendering_view.request.user == user
        return cls.cv_action_enabled(user, obj)

    monkeypatch.setattr(target, "cv_action_enabled", state)
    monkeypatch.setattr(target, "_cv_action_enabled_for_rendering", adapter)
    owner = bound(cv_publisher.get_view_class("update"), user_publisher_add)
    owner.cv_cancel_keys = ["create"]
    owner.cv_cancel_key = "create"
    owner.request.GET = RequestFactory().get("/", {"cv_from": "create"}).GET
    assert owner.cv_get_cancel_url() == (url(cv_publisher, "create") if enabled else None)
    # A denied origin which is also the fallback is evaluated only once.
    assert events == [("adapter", None), ("state", None)]
    events.clear()
    context = owner.cv_get_context(key="create", obj=None, user=user_publisher_add, request=owner.request)
    assert context["cv_access"] is True
    assert context["cv_action_enabled"] is enabled
    assert events == [("adapter", None), ("state", None)]
    events.clear()
    client.force_login(user_publisher_add)
    assert client.get(url(cv_publisher, "create")).status_code == (200 if enabled else 403)
    # Authorized GET additionally renders the page's own action metadata.
    assert events == [("state", None)] + ([("adapter", None), ("state", None)] if enabled else [])


@pytest.mark.django_db
def test_core_resource_object_state(cv_s3file, user_s3file_view, monkeypatch, client):
    from tests.test1.app.resources import S3File

    obj = S3File.cv_get_items(None)[0]
    seen = []
    target = cv_s3file.get_view_class("detail")
    monkeypatch.setattr(target, "cv_action_enabled", classmethod(lambda cls, user, obj: seen.append(obj) or True))
    view = bound(cv_s3file.get_view_class("delete"), user_s3file_view, obj, {"cv_from": "detail"})
    assert view.cv_get_cancel_url() == url(cv_s3file, "detail", obj.pk)
    assert seen == [obj]
    client.force_login(user_s3file_view)
    assert client.get(view.cv_get_cancel_url()).status_code == 200


@pytest.mark.django_db
def test_core_current_key_fallback(cv_publisher, user_publisher_add, monkeypatch):
    cls = cv_publisher.get_view_class("create")
    monkeypatch.setattr(cls, "cv_cancel_key", None)
    assert bound(cls, user_publisher_add).cv_get_cancel_url() == url(cv_publisher, "create")


@pytest.mark.django_db
def test_core_nested_no_object_state_receives_url_parent(cv_book, user_book_view, publisher_penguin, monkeypatch):
    seen = []
    monkeypatch.setattr(
        cv_book.get_view_class("list"),
        "cv_action_enabled",
        classmethod(lambda cls, user, obj: seen.append(obj) or True),
    )
    view = bound(
        cv_book.get_view_class("create"), user_book_view, **{cv_book.parent.get_pk_name(): publisher_penguin.pk}
    )
    assert view.cv_get_cancel_url()
    assert seen == [publisher_penguin]


@pytest.mark.django_db
def test_core_structurally_impossible_fallback_is_configuration_error(cv_publisher, user_publisher_view, monkeypatch):
    target = cv_publisher.get_view_class("list")
    monkeypatch.setattr(target, "cv_get_url_extra_kwargs", classmethod(lambda cls: {"unexpected": "argument"}))
    view = bound(cv_publisher.get_view_class("create"), user_publisher_view)
    with pytest.raises(ImproperlyConfigured, match="registered usable destination"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
def test_guardian_form_parent_grant_does_not_authorize_list(pn, publisher_a, client, monkeypatch):
    from guardian.shortcuts import assign_perm

    user = _user("cancel_create_only")
    assign_perm("change_publisher", user, publisher_a)
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_permission", "view")
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_create_permission", "change")
    calls = []
    monkeypatch.setattr(pn.BookList, "cv_action_enabled", classmethod(lambda cls, user, obj: calls.append(obj) or True))
    client.force_login(user)
    response = client.get(_url(pn.book_vs, "create", publisher_a.pk))
    assert response.status_code == 200
    assert "data-cv-cancel-url" not in response.content.decode()
    calls.clear()  # isolate Cancel from the page's ordinary toolbar metadata
    assert response.context["view"].cv_get_cancel_url() is None
    assert calls == []  # denied destination policy precedes state
    assert client.get(_url(pn.book_vs, "list", publisher_a.pk)).status_code == 403
    response = client.post(_url(pn.book_vs, "create", publisher_a.pk), {"title": "Allowed without Cancel"})
    assert response.status_code == 302


@pytest.mark.django_db
def test_guardian_empty_list_is_accessible(pn, publisher_a, client):
    user = _user("cancel_empty_list")
    client.force_login(user)
    response = client.get(_url(pn.book_vs, "create", publisher_a.pk))
    destination = cancel_url(response)
    assert destination == _url(pn.book_vs, "list", publisher_a.pk)
    target = client.get(destination)
    assert target.status_code == 200
    assert list(target.context["object_list"]) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "grant,global_opt_in,accessible", [("object", False, True), ("global", False, False), ("global", True, True)]
)
def test_guardian_object_destination_policy(pn, publisher_a, client, monkeypatch, grant, global_opt_in, accessible):
    from guardian.shortcuts import assign_perm

    from tests.test1.app.models import Book

    book = Book.objects.create(title="Cancel object", publisher=publisher_a)
    user = _user("cancel_object")
    assign_perm("change_book", user, book)
    if grant == "object":
        assign_perm("view_book", user, book)
    else:
        user = _grant_global(user, "view_book")
    monkeypatch.setattr(pn.BookDetail, "cv_guardian_accept_global_perms", global_opt_in)
    client.force_login(user)
    response = client.get(_url(pn.book_vs, "update", publisher_a.pk, book.pk), {"cv_from": "detail"})
    assert response.status_code == 200
    destination = cancel_url(response)
    expected = (
        _url(pn.book_vs, "detail", publisher_a.pk, book.pk) if accessible else _url(pn.book_vs, "list", publisher_a.pk)
    )
    assert destination == expected
    assert client.get(destination).status_code == 200
    assert client.get(_url(pn.book_vs, "detail", publisher_a.pk, book.pk)).status_code == (200 if accessible else 403)


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["anonymous", "inactive"])
@pytest.mark.parametrize("target_key", ["list", "detail", "create"])
def test_guardian_denies_anonymous_and_inactive_destinations(pn, publisher_a, monkeypatch, actor, target_key):
    from django.contrib.auth.models import AnonymousUser

    from tests.test1.app.models import Book

    user = AnonymousUser() if actor == "anonymous" else _user("inactive_cancel", superuser=True, active=False)
    book = Book.objects.create(title="Actor gate", publisher=publisher_a)
    cls = pn.book_vs.get_view_class(target_key)
    monkeypatch.setattr(cls, "cv_action_enabled", classmethod(lambda *args: pytest.fail("state before actor gate")))
    view = bound(pn.BookUpdate, user, book, **{pn.book_vs.parent.get_pk_name(): publisher_a.pk})
    view.cv_cancel_keys = None
    view.cv_cancel_key = target_key
    assert view.cv_get_cancel_url() is None


@pytest.fixture
def guardian_targets(pn):
    """Custom parent-only and create targets in the same isolated child ViewSet."""
    from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
    from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin

    events = []
    state = {"enabled": True, "create_allowed": True}

    class ParentOnly(GuardianParentPermissionMixin, CustomFormNoObjectViewPermissionRequired):
        cv_viewset = pn.book_vs
        cv_key = "inspect"
        cv_path = "inspect"
        cv_permission = "view"

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            events.append(("parent-state", obj))
            return state["enabled"]

        @classmethod
        def _cv_action_enabled_for_rendering(cls, user, obj, rendering_view):
            events.append(("parent-adapter", obj))
            return cls.cv_action_enabled(user, obj)

        def get(self, request, *args, **kwargs):
            return HttpResponse("Parent-only destination")

    class NestedCreate(pn.BookCreate):
        cv_viewset = pn.book_vs
        cv_key = "special_create"
        cv_path = "special-create"

        @classmethod
        def cv_create_has_access(cls, user, rendering_view, parent_obj):
            events.append(("create-access", parent_obj))
            return state["create_allowed"] and super().cv_create_has_access(user, rendering_view, parent_obj)

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            events.append(("create-state", obj))
            return state["enabled"]

        @classmethod
        def _cv_action_enabled_for_rendering(cls, user, obj, rendering_view):
            events.append(("create-adapter", obj))
            return super()._cv_action_enabled_for_rendering(user, obj, rendering_view)

        def get(self, request, *args, **kwargs):
            return HttpResponse("Nested create destination")

    urls = ModuleType("cancel_guardian_custom_urls")
    pn.book_vs.__dict__.pop("urlpatterns", None)  # pn built its URL table before these custom registrations
    urls.urlpatterns = [*pn.pub_vs.urlpatterns, *pn.book_vs.urlpatterns, path("", include("tests.test1.project.urls"))]
    with override_settings(ROOT_URLCONF=urls):
        clear_url_caches()
        try:
            yield SimpleNamespace(parent=ParentOnly, create=NestedCreate, events=events, state=state)
        finally:
            clear_url_caches()


@pytest.mark.django_db
@pytest.mark.parametrize("key,prefix", [("inspect", "parent"), ("special_create", "create")])
@pytest.mark.parametrize("permission", ["view", None])
def test_guardian_parent_only_and_create_targets(
    pn, guardian_targets, publisher_a, publisher_b, client, monkeypatch, key, prefix, permission
):
    from guardian.shortcuts import assign_perm

    user = _user("cancel_parent_only")
    assign_perm("view_publisher", user, publisher_a)
    assert not user.has_perm("app.view_book")
    assert not user.has_perm("app.add_book")
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_permission", permission)
    monkeypatch.setattr(pn.BookCreate, "cv_cancel_keys", [key])
    monkeypatch.setattr(pn.BookCreate, "cv_cancel_key", key)
    client.force_login(user)
    response = client.get(_url(pn.book_vs, "create", publisher_a.pk), {"cv_from": key})
    assert response.status_code == 200
    destination = cancel_url(response)
    assert destination == _url(pn.book_vs, key, publisher_a.pk)
    expected = ([("create-access", publisher_a)] if prefix == "create" else []) + [
        (f"{prefix}-adapter", publisher_a),
        (f"{prefix}-state", publisher_a),
    ]
    assert guardian_targets.events == expected
    guardian_targets.events.clear()
    assert client.get(destination).status_code == 200
    assert guardian_targets.events == [(f"{prefix}-state", publisher_a)]
    guardian_targets.events.clear()

    view = bound(pn.BookCreate, user, **{pn.book_vs.parent.get_pk_name(): publisher_b.pk})
    if permission is not None:
        assert view.cv_get_cancel_url() is None
        assert guardian_targets.events == []
        assert client.get(_url(pn.book_vs, key, publisher_b.pk)).status_code == 403
    guardian_targets.state["enabled"] = False
    view.kwargs[pn.book_vs.parent.get_pk_name()] = publisher_a.pk
    assert view.cv_get_cancel_url() is None
    assert client.get(destination).status_code == 403
    guardian_targets.events.clear()
    view.kwargs[pn.book_vs.parent.get_pk_name()] = 999999
    assert view.cv_get_cancel_url() is None
    assert guardian_targets.events == []
    assert client.get(_url(pn.book_vs, key, 999999)).status_code == 404


@pytest.mark.django_db
def test_guardian_create_custom_access_denial(pn, guardian_targets, publisher_a):
    user = _user("cancel_custom_denial")
    guardian_targets.state["create_allowed"] = False
    view = bound(pn.BookCreate, user, **{pn.book_vs.parent.get_pk_name(): publisher_a.pk})
    view.cv_cancel_key = "special_create"
    assert view.cv_get_cancel_url() is None
    assert guardian_targets.events == [("create-access", publisher_a)]


@pytest.mark.django_db
@pytest.mark.parametrize("error", [Http404, KeyError, DatabaseError])
def test_guardian_custom_parent_failures_propagate(pn, publisher_a, monkeypatch, error):
    def fail(self):
        raise error("custom Guardian parent")

    monkeypatch.setattr(pn.BookCreate, "cv_get_parent_object", fail)
    view = bound(pn.BookCreate, _user("cancel_custom_failure"), **{pn.book_vs.parent.get_pk_name(): publisher_a.pk})
    with pytest.raises(error, match="custom Guardian parent"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("global_opt_in", [False, True])
def test_guardian_parent_global_policy(pn, publisher_a, client, monkeypatch, global_opt_in):
    from guardian.shortcuts import assign_perm

    user = _grant_global(_user("cancel_global_parent"), "view_publisher")
    assign_perm("change_publisher", user, publisher_a)
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_permission", "view")
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_create_permission", "change")
    monkeypatch.setattr(pn.BookList, "cv_guardian_accept_global_perms", global_opt_in)
    client.force_login(user)
    response = client.get(_url(pn.book_vs, "create", publisher_a.pk))
    assert response.status_code == 200
    if global_opt_in:
        assert cancel_url(response) == _url(pn.book_vs, "list", publisher_a.pk)
        assert client.get(cancel_url(response)).status_code == 200
    else:
        assert "data-cv-cancel-url" not in response.content.decode()
        assert client.get(_url(pn.book_vs, "list", publisher_a.pk)).status_code == 403


@pytest.mark.django_db
def test_guardian_child_object_state_once_after_parent_and_object_policy(pn, publisher_a, publisher_b, monkeypatch):
    from guardian.shortcuts import assign_perm

    from tests.test1.app.models import Book

    book = Book.objects.create(title="Object state", publisher=publisher_a)
    user = _user("cancel_object_state")
    assign_perm("view_publisher", user, publisher_a)
    monkeypatch.setattr(pn.book_vs, "cv_guardian_parent_permission", "view")
    events = []
    monkeypatch.setattr(
        pn.BookDetail, "cv_action_enabled", classmethod(lambda cls, user, obj: events.append(obj) or False)
    )
    view = bound(pn.BookUpdate, user, book, {"cv_from": "detail"}, **{pn.book_vs.parent.get_pk_name(): publisher_a.pk})
    view.cv_cancel_key = "detail"
    assert view.cv_get_cancel_url() is None  # parent granted, child denied
    assert events == []
    assign_perm("view_book", user, book)
    assert view.cv_get_cancel_url() is None  # child granted, state denied
    assert events == [book]
    events.clear()
    view.kwargs[pn.book_vs.parent.get_pk_name()] = publisher_b.pk
    assert view.cv_get_cancel_url() is None
    assert events == []


@pytest.mark.django_db
def test_guardian_invalid_child_composition_rejected(pn, publisher_a, monkeypatch):
    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin

    class InvalidChild(GuardianParentPermissionMixin, DetailViewPermissionRequired):
        pass

    InvalidChild.cv_viewset = pn.book_vs
    monkeypatch.setitem(pn.book_vs._views, "detail", InvalidChild)
    view = bound(
        pn.BookUpdate, _user("invalid_composition"), publisher_a, **{pn.book_vs.parent.get_pk_name(): publisher_a.pk}
    )
    view.cv_cancel_key = "detail"
    with pytest.raises(ImproperlyConfigured, match="require GuardianObjectPermissionMixin"):
        view.cv_get_cancel_url()


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["object", "queryset"])
@pytest.mark.parametrize("actor", ["anonymous", "inactive", "active"])
def test_guardian_standalone_mixin_actor_and_top_level_policy(pn, publisher_a, monkeypatch, family, actor):
    from django.contrib.auth.models import AnonymousUser
    from guardian.shortcuts import assign_perm

    from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin, GuardianQuerysetMixin

    if family == "object":

        class Target(GuardianObjectPermissionMixin, DetailViewPermissionRequired):
            pass
    else:

        class Target(GuardianQuerysetMixin, ListViewPermissionRequired):
            pass

    Target.cv_viewset = pn.pub_vs
    key = "detail" if family == "object" else "list"
    monkeypatch.setitem(pn.pub_vs._views, key, Target)
    user = AnonymousUser() if actor == "anonymous" else _user("standalone_cancel", active=actor == "active")
    if actor == "active":
        assign_perm("view_publisher", user, publisher_a)
    events = []
    monkeypatch.setattr(Target, "cv_action_enabled", classmethod(lambda cls, user, obj: events.append(obj) or True))
    view = bound(Target, user, publisher_a)
    view.cv_cancel_key = key
    result = view.cv_get_cancel_url()
    assert bool(result) is (actor == "active")
    assert events == ([publisher_a if family == "object" else None] if actor == "active" else [])


@pytest.mark.django_db
def test_core_cancel_kwargs_hook_cannot_restore_denied_destination(cv_publisher, user_publisher_view, monkeypatch):
    from tests.test1.app.views import PublisherForm

    events = []
    policy = {"enabled": True, "raise": False}

    class CustomForm(PublisherForm):
        def get_cancel_button_kwargs(self):
            events.append("kwargs")
            if policy["raise"]:
                raise ValueError("custom kwargs failed")
            # Repeated calls to super must reuse the authoritative result within this render.
            assert super().get_cancel_button_kwargs() == super().get_cancel_button_kwargs()
            return {**super().get_cancel_button_kwargs(), "css_class": "custom"}

    def state(cls, user, obj):
        events.append("state")
        return policy["enabled"]

    monkeypatch.setattr(cv_publisher.get_view_class("list"), "cv_action_enabled", classmethod(state))
    form = CustomForm(cv_view=bound(cv_publisher.get_view_class("create"), user_publisher_view))
    assert form.get_cancel_button() is not None
    assert events == ["state", "kwargs"]
    assert not hasattr(form, "_cv_cancel_button_context")
    events.clear()
    policy["enabled"] = False
    assert form.get_cancel_button() is None
    assert events == ["state"]
    events.clear()
    policy["enabled"] = True
    policy["raise"] = True
    with pytest.raises(ValueError, match="custom kwargs failed"):
        form.get_cancel_button()
    assert events == ["state", "kwargs"]
    assert not hasattr(form, "_cv_cancel_button_context")
