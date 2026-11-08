"""Guardian ancestor authorization: provider, independent fallbacks, actor order, local gates and removed fields.

A ``GuardianViewSet`` ancestor requires the selected permission on the resolved object by default (direct or group
grant, Guardian's content-type semantics); ``AncestorPolicy(accept_global_perms=True)`` on that ancestor additionally
accepts the model permission. A core ancestor requires the model permission. The Guardian parent mixin delegates
ancestry to the one shared guard and keeps its composition checks, actor rules and nested no-object state gate.

Every test drives real ``Client`` requests against isolated chains built in ``ancestor_scope()``.
"""

from typing import ClassVar

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings
from pydantic import PydanticUserError, ValidationError

from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.ancestor_cases import EVENTS, FixedTemplateMixin, ancestor_scope
from tests.test1.app.models import Book, BookNote, Publisher

LOGIN = "/accounts/login/"
INACTIVE_BACKENDS = [
    "django.contrib.auth.backends.AllowAllUsersModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
REMOVED_FIELDS = ("cv_guardian_parent_permission", "cv_guardian_parent_create_permission")


class TracedGuardianViewSet(GuardianViewSet):
    """Records ``<trace>_queryset`` (the endpoint's as ``child``) and ``<trace>_gate`` in ``EVENTS``."""

    trace: str = ""

    def get_queryset(self, view):
        EVENTS.append("child" if self.trace == "child" else f"{self.trace}_queryset")
        return super().get_queryset(view)

    def _ancestor_has_permission(self, user, obj, permission):
        EVENTS.append(f"{self.trace}_gate")
        return super()._ancestor_has_permission(user, obj, permission)


@pytest.fixture(autouse=True)
def events():
    EVENTS.clear()
    yield EVENTS
    EVENTS.clear()


@pytest.fixture
def scope():
    with ancestor_scope() as scope:
        yield scope


# ── chain builders ────────────────────────────────────────────────────────────


def define(scope, viewset, bases, key=None, **attrs):
    bases = bases if isinstance(bases, tuple) else (bases,)
    if key is not None:
        attrs.update(cv_key=key, cv_path=key)
    name = f"{bases[-1].__name__}{key or ''}{scope.sfx}"
    return type(name, (FixedTemplateMixin, *bases), {"cv_viewset": viewset, "__module__": __name__, **attrs})


class StateTrace:
    """A switchable action-state hook recording the object it receives."""

    enabled: ClassVar[dict] = {"value": True}
    seen: ClassVar[list] = []

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        EVENTS.append("state")
        StateTrace.seen.append(obj)
        return StateTrace.enabled["value"]


@pytest.fixture(autouse=True)
def reset_state():
    StateTrace.enabled["value"] = True
    StateTrace.seen.clear()


def guardian_book_views(scope, book_vs, list_attrs=None, detail_attrs=None):
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )

    define(scope, book_vs, GuardianListViewPermissionRequired, **(list_attrs or {}))
    define(scope, book_vs, (StateTrace, GuardianDetailViewPermissionRequired), **(detail_attrs or {}))
    define(
        scope,
        book_vs,
        (StateTrace, CreateViewParentMixin, GuardianCreateViewPermissionRequired),
        fields=["title"],
    )


def publisher_book(scope, *, pub_class=GuardianViewSet, pub_policy=None, book_policy=None, also_mount=(), **view_attrs):
    """Publisher ancestor (``pub_class``) → Guardian Book endpoint with list/detail/create views; mounted once,
    with ``also_mount`` ViewSets."""
    pub_kwargs = {"model": Publisher, "name": scope.name("agpub")}
    if pub_policy is not None:
        pub_kwargs["ancestor_policy"] = pub_policy
    pub_vs = scope.viewset(pub_class, **pub_kwargs)
    book_kwargs = {
        "model": Book,
        "name": scope.name("agbook"),
        "parent": ParentViewSet(name=pub_vs.name, attribute="publisher"),
    }
    if book_policy is not None:
        book_kwargs["ancestor_policy"] = book_policy
    book_vs = scope.viewset(GuardianViewSet, **book_kwargs)
    guardian_book_views(scope, book_vs, **view_attrs)
    scope.mount([book_vs, *also_mount])
    return pub_vs, book_vs


def url(viewset, key, parent_pk, pk=None):
    from django.urls import reverse

    kwargs = {viewset.parent.get_pk_name(): parent_pk}
    if pk is not None:
        kwargs["pk"] = pk
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def make_user(username, perms=(), **extra):
    user = User.objects.create_user(username=username, password="password", **extra)
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label="app"))
    return User.objects.get(pk=user.pk)


def client_for(user=None, backend=None):
    client = Client()
    if user is not None:
        client.force_login(user, backend=backend)
    return client


# ── provider ──────────────────────────────────────────────────────────────────

GRANT_MATRIX = [
    # object grant, model grant, ancestor fallback, allowed
    ("none", False, False, False),
    ("none", False, True, False),
    ("direct", False, False, True),
    ("direct", False, True, True),
    ("group", False, False, True),
    ("group", False, True, True),
    ("none", True, False, False),
    ("none", True, True, True),
    ("direct", True, False, True),
    ("direct", True, True, True),
]


@pytest.mark.parametrize(("object_grant", "model_grant", "fallback", "allowed"), GRANT_MATRIX)
@pytest.mark.django_db
def test_guardian_ancestor_grant_matrix(scope, object_grant, model_grant, fallback, allowed):
    _pub_vs, book_vs = publisher_book(scope, pub_policy=AncestorPolicy(accept_global_perms=fallback))
    pub_vs = book_vs.parent.viewset
    publisher = Publisher.objects.create(name="P")
    user = make_user("actor", ["view_publisher"] if model_grant else [])
    if object_grant == "direct":
        pub_vs.assign_perm("view", user, publisher)
    elif object_grant == "group":
        group = Group.objects.create(name="readers")
        user.groups.add(group)
        pub_vs.assign_perm("view", group, publisher)

    response = client_for(user).get(url(book_vs, "list", publisher.pk))
    assert response.status_code == (200 if allowed else 403)


@pytest.mark.django_db
def test_guardian_ancestor_requires_the_correct_object_and_permission(scope):
    _pub_vs, book_vs = publisher_book(scope)
    pub_vs = book_vs.parent.viewset
    publisher, other = Publisher.objects.create(name="P"), Publisher.objects.create(name="O")
    book = Book.objects.create(title="B", publisher=publisher)
    user = make_user("actor")
    pub_vs.assign_perm("view", user, other)  # another Publisher row
    pub_vs.assign_perm("change", user, publisher)  # another permission on the right row
    book_vs.assign_perm("view", user, book)  # the required codename's row on another content type
    client = client_for(user)
    assert client.get(url(book_vs, "list", publisher.pk)).status_code == 403
    assert client.get(url(book_vs, "list", other.pk)).status_code == 200


@pytest.mark.django_db
def test_core_parent_and_guardian_child_defaults(scope):
    publisher = Publisher.objects.create(name="P")

    def outcomes(pub_class, sfx):
        pub_vs = scope.viewset(pub_class, model=Publisher, name=scope.name(f"cg{sfx}pub"))
        book_vs = scope.viewset(
            GuardianViewSet,
            model=Book,
            name=scope.name(f"cg{sfx}book"),
            parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
        )
        guardian_book_views(scope, book_vs)
        return pub_vs, book_vs

    _core_pub, core_book = outcomes(ViewSet, "c")
    guard_pub, guard_book = outcomes(GuardianViewSet, "g")
    scope.mount([core_book, guard_book])

    object_only = make_user("object-only")
    guard_pub.assign_perm("view", object_only, publisher)  # the same Publisher object grant serves both
    model_only = make_user("model-only", ["view_publisher"])

    assert client_for(object_only).get(url(core_book, "list", publisher.pk)).status_code == 403
    assert client_for(model_only).get(url(core_book, "list", publisher.pk)).status_code == 200
    assert client_for(object_only).get(url(guard_book, "list", publisher.pk)).status_code == 200
    assert client_for(model_only).get(url(guard_book, "list", publisher.pk)).status_code == 403


# ── independent fallbacks ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_ancestor_and_local_fallback_are_independent(scope):
    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="Visible", publisher=publisher)
    model_reader = make_user("model-reader", ["view_publisher", "view_book"])

    # the child view's fallback cannot relax a strict Publisher ancestor
    _pub, strict_book = publisher_book(
        scope,
        list_attrs={"cv_guardian_accept_global_perms": True},
        detail_attrs={"cv_guardian_accept_global_perms": True},
    )
    client = client_for(model_reader)
    assert client.get(url(strict_book, "list", publisher.pk)).status_code == 403
    assert client.get(url(strict_book, "detail", publisher.pk, book.pk)).status_code == 403


@pytest.mark.django_db
def test_ancestor_fallback_cannot_relax_a_strict_child_object_gate(scope):
    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="Visible", publisher=publisher)
    model_reader = make_user("model-reader", ["view_publisher", "view_book"])

    _pub, book_vs = publisher_book(scope, pub_policy=AncestorPolicy(accept_global_perms=True))
    client = client_for(model_reader)
    response = client.get(url(book_vs, "list", publisher.pk))
    assert response.status_code == 200
    assert f"{book.pk};" not in response.content.decode()  # strict local queryset
    assert client.get(url(book_vs, "detail", publisher.pk, book.pk)).status_code == 403  # strict local object


@pytest.mark.django_db
def test_ancestor_fallback_applies_to_every_descendant(scope):
    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired

    pub_vs = scope.viewset(
        GuardianViewSet,
        model=Publisher,
        name=scope.name("dpub"),
        ancestor_policy=AncestorPolicy(accept_global_perms=True),
    )
    book_vs = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("dbook"),
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
    )
    note_vs = scope.viewset(
        GuardianViewSet,
        model=BookNote,
        name=scope.name("dnote"),
        parent=ParentViewSet(name=book_vs.name, attribute="book"),
    )
    define(scope, book_vs, GuardianListViewPermissionRequired)
    define(scope, note_vs, GuardianListViewPermissionRequired)
    scope.mount([book_vs, note_vs])

    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="B", publisher=publisher)
    user = make_user("model-publisher", ["view_publisher"])
    book_vs.assign_perm("view", user, book)  # Book stays strict as an ancestor of BookNote
    client = client_for(user)
    assert client.get(url(book_vs, "list", publisher.pk)).status_code == 200
    from django.urls import reverse

    note_url = reverse(
        note_vs.get_router_name("list"),
        kwargs={book_vs.parent.get_pk_name(): publisher.pk, note_vs.parent.get_pk_name(): book.pk},
    )
    assert client.get(note_url).status_code == 200
    # without the Book object grant the strict Book ancestor denies; the Publisher fallback does not spread
    book_vs.remove_perm("view", user, book)
    assert client_for(User.objects.get(pk=user.pk)).get(note_url).status_code == 403


# ── actor order ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(("behavior", "status"), [("redirect", 302), ("403", 403), ("404", 404)])
@pytest.mark.parametrize("provider", [None, "none"])
@pytest.mark.django_db
def test_guardian_actor_responses_precede_lookup(scope, events, behavior, status, provider):
    pub_vs = scope.viewset(
        TracedGuardianViewSet,
        model=Publisher,
        name=scope.name("actpub"),
        trace="outer",
        ancestor_policy=AncestorPolicy(provider=provider),
    )
    book_vs = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("actbook"),
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
    )
    attrs = {"cv_guardian_anonymous_behavior": behavior}
    guardian_book_views(scope, book_vs, list_attrs=attrs, detail_attrs=attrs)
    scope.mount([book_vs])

    missing = url(book_vs, "list", 999999)
    response = Client().get(missing)
    assert response.status_code == status
    if behavior == "redirect":
        assert response["Location"].startswith(LOGIN)
    assert events == []  # no ancestor lookup for any configured anonymous response

    for superuser in (False, True):
        inactive = make_user(f"inactive{superuser}", is_active=False, is_superuser=superuser)
        with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
            assert client_for(inactive, INACTIVE_BACKENDS[0]).get(missing).status_code == 403
    assert events == []

    # an active superuser follows backend semantics: Guardian grants every object permission
    publisher = Publisher.objects.create(name="P")
    root = User.objects.create_superuser(username="root", password="password")
    assert client_for(root).get(url(book_vs, "list", publisher.pk)).status_code == 200


# ── local gates after ancestry ────────────────────────────────────────────────


@pytest.mark.django_db
def test_guardian_local_gates_remain_after_ancestry(scope):
    from django.urls import reverse

    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired

    top_vs = scope.viewset(GuardianViewSet, model=Publisher, name=scope.name("topcreate"))
    define(scope, top_vs, GuardianCreateViewPermissionRequired, fields=["name"])
    _pub, book_vs = publisher_book(scope, also_mount=[top_vs])
    pub_vs = book_vs.parent.viewset
    publisher = Publisher.objects.create(name="P")
    granted = Book.objects.create(title="Granted", publisher=publisher)
    hidden = Book.objects.create(title="Hidden", publisher=publisher)
    user = make_user("actor")
    pub_vs.assign_perm("view", user, publisher)
    pub_vs.assign_perm("change", user, publisher)
    book_vs.assign_perm("view", user, granted)
    client = client_for(user)

    content = client.get(url(book_vs, "list", publisher.pk)).content.decode()
    assert f"{granted.pk};" in content and f"{hidden.pk};" not in content
    assert client.get(url(book_vs, "detail", publisher.pk, granted.pk)).status_code == 200
    assert client.get(url(book_vs, "detail", publisher.pk, hidden.pk)).status_code == 403
    StateTrace.enabled["value"] = False
    assert client.get(url(book_vs, "detail", publisher.pk, granted.pk)).status_code == 403
    StateTrace.enabled["value"] = True

    # nested create: the parent gate only, no model add_book
    create = url(book_vs, "create", publisher.pk)
    assert client.get(create).status_code == 200
    assert client.post(create, {"title": "New"}).status_code == 302
    assert Book.objects.get(title="New").publisher_id == publisher.pk

    # top-level Guardian create keeps its local model add requirement
    top_url = reverse(top_vs.get_router_name("create"))
    assert client.get(top_url).status_code == 403
    assert client_for(make_user("adder", ["add_publisher"])).get(top_url).status_code == 200


@pytest.mark.django_db
def test_none_structural_parent_still_drives_create_state(scope, events):
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired, GuardianListViewPermissionRequired

    pub_vs = scope.viewset(TracedGuardianViewSet, model=Publisher, name=scope.name("spub"), trace="outer")
    book_vs = scope.viewset(
        TracedGuardianViewSet,
        model=Book,
        name=scope.name("sbook"),
        trace="inner",
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
        ancestor_policy=AncestorPolicy(provider="none"),
    )
    note_vs = scope.viewset(
        GuardianViewSet,
        model=BookNote,
        name=scope.name("snote"),
        parent=ParentViewSet(name=book_vs.name, attribute="book"),
    )
    define(scope, note_vs, (StateTrace, CreateViewParentMixin, GuardianCreateViewPermissionRequired), fields=["note"])
    define(scope, note_vs, GuardianListViewPermissionRequired)  # the success URL
    scope.mount([note_vs])
    from django.urls import reverse

    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="B", publisher=publisher)
    create = reverse(
        note_vs.get_router_name("create"),
        kwargs={book_vs.parent.get_pk_name(): publisher.pk, note_vs.parent.get_pk_name(): book.pk},
    )
    user = make_user("actor")
    client = client_for(user)

    # the farther protected Publisher supplies the permission (nearest write: change)
    assert client.post(create, {"note": "Denied"}).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]
    assert StateTrace.seen == []
    pub_vs.assign_perm("change", user, publisher)

    events.clear()
    assert client.post(create, {"note": "Written"}).status_code == 302
    assert events[:3] == ["outer_queryset", "outer_gate", "inner_queryset"]  # none: resolved, no gate
    assert "inner_gate" not in events
    note = BookNote.objects.get(note="Written")
    assert note.book_id == book.pk  # the immediate parent supplies the attachment
    assert StateTrace.seen and all(type(obj) is Book and obj.pk == book.pk for obj in StateTrace.seen)

    StateTrace.enabled["value"] = False
    StateTrace.seen.clear()
    events.clear()
    assert client.post(create, {"note": "Disabled"}).status_code == 403
    assert events.index("state") > events.index("inner_queryset")  # state after ancestry
    assert not BookNote.objects.filter(note="Disabled").exists()
    assert [type(obj) for obj in StateTrace.seen] == [Book]


# ── removed fields ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("field", REMOVED_FIELDS)
@pytest.mark.parametrize("value", ["view", "change", None])
@pytest.mark.django_db
def test_removed_fields_fail_before_registration(scope, field, value):
    from crud_views.lib.viewset import _REGISTRY

    name = scope.name("removed")
    before = set(_REGISTRY)
    with pytest.raises(ValidationError, match=f"{field}.*ancestor_policy"):
        GuardianViewSet(model=Publisher, name=name, **{field: value})
    assert set(_REGISTRY) == before

    def declare(base, annotation):
        namespace = {"__module__": __name__, "__annotations__": {field: annotation}, field: value}
        return type(f"Declares{annotation is ClassVar}", (base,), namespace)

    FieldDeclaration = declare(GuardianViewSet, str | None)
    ClassVarDeclaration = declare(GuardianViewSet, ClassVar[str | None])
    Inherited = type("Inherited", (ClassVarDeclaration,), {"__module__": __name__})

    for declared in (FieldDeclaration, ClassVarDeclaration, Inherited):
        with pytest.raises(ValidationError, match=f"{field}.*ancestor_policy"):
            declared(model=Publisher, name=name)
        assert set(_REGISTRY) == before

    # an unannotated declaration is already refused by Pydantic when the class is defined
    with pytest.raises(PydanticUserError):
        type("Unannotated", (GuardianViewSet,), {"__module__": __name__, field: value})

    # the corrected declaration registers under the same name, with its manage view
    corrected = scope.viewset(GuardianViewSet, model=Publisher, name=name)
    assert _REGISTRY[name] is corrected
    assert corrected.has_view("manage")
    assert not hasattr(corrected, field)


def test_removed_viewset_global_perms_flag_stays_rejected():
    with pytest.raises(ValidationError, match="cv_guardian_accept_global_perms"):
        GuardianViewSet(model=Publisher, name="never_registered", cv_guardian_accept_global_perms=True)


# ── composition and order ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_guardian_composition_guards_are_preserved(scope):
    from crud_views.lib.views import DetailView, DetailViewPermissionRequired
    from crud_views_guardian.checks import check_guardian_composition
    from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin

    pub_vs = scope.viewset(GuardianViewSet, model=Publisher, name=scope.name("cpub"))
    book_vs = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("cbook"),
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
    )
    broken = define(scope, book_vs, (GuardianParentPermissionMixin, DetailViewPermissionRequired), key="broken")
    define(scope, book_vs, DetailView)  # a deliberately plain child
    scope.mount([book_vs])

    errors = [m for m in check_guardian_composition() if m.obj is broken]
    assert [m.id for m in errors] == ["crud_views_guardian.E001"]

    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="B", publisher=publisher)
    user = make_user("actor")
    client = client_for(user)
    with pytest.raises(ImproperlyConfigured, match="GuardianObjectPermissionMixin"):
        client.get(url(book_vs, "broken", publisher.pk, book.pk))

    # the plain child has no local gate; the shared guard still protects its Guardian ancestor
    plain = url(book_vs, "detail", publisher.pk, book.pk)
    assert client.get(plain).status_code == 403
    pub_vs.assign_perm("view", user, publisher)
    assert client.get(plain).status_code == 200


class ObjectTrace:
    def get_object(self, queryset=None):
        EVENTS.append("local_object")
        return super().get_object(queryset)


@pytest.mark.django_db
def test_guardian_order_matches_core_order(scope, events, monkeypatch):
    from crud_views.lib.view import ancestors
    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin, GuardianParentPermissionMixin

    pub_vs = scope.viewset(TracedGuardianViewSet, model=Publisher, name=scope.name("opub"), trace="outer")
    book_vs = scope.viewset(
        TracedGuardianViewSet,
        model=Book,
        name=scope.name("obook"),
        trace="inner",
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
    )
    note_vs = scope.viewset(
        TracedGuardianViewSet,
        model=BookNote,
        name=scope.name("onote"),
        trace="child",
        parent=ParentViewSet(name=book_vs.name, attribute="book"),
    )
    orders = {
        "parent_first": (ObjectTrace, StateTrace, GuardianParentPermissionMixin, GuardianObjectPermissionMixin),
        "object_first": (ObjectTrace, StateTrace, GuardianObjectPermissionMixin, GuardianParentPermissionMixin),
    }
    for key, mixins in orders.items():
        define(scope, note_vs, (*mixins, DetailViewPermissionRequired), key=key)
    scope.mount([note_vs])
    from django.urls import reverse

    publisher = Publisher.objects.create(name="P")
    book = Book.objects.create(title="B", publisher=publisher)
    note = BookNote.objects.create(book=book, note="N")
    calls = []
    original = ancestors.authorize_ancestors

    def counted(view):
        calls.append(type(view))
        return original(view)

    monkeypatch.setattr(ancestors, "authorize_ancestors", counted)

    user = make_user("actor")
    client = client_for(user)
    for key in orders:
        target = reverse(
            note_vs.get_router_name(key),
            kwargs={
                book_vs.parent.get_pk_name(): publisher.pk,
                note_vs.parent.get_pk_name(): book.pk,
                "pk": note.pk,
            },
        )
        events.clear()
        calls.clear()
        assert client.get(target).status_code == 403
        assert events == ["outer_queryset", "outer_gate"]  # no deeper queryset, local object or state
        assert len(calls) == 1

    pub_vs.assign_perm("view", user, publisher)
    book_vs.assign_perm("view", user, book)
    note_vs.assign_perm("view", user, note)
    for key in orders:
        target = reverse(
            note_vs.get_router_name(key),
            kwargs={
                book_vs.parent.get_pk_name(): publisher.pk,
                note_vs.parent.get_pk_name(): book.pk,
                "pk": note.pk,
            },
        )
        events.clear()
        calls.clear()
        assert client.get(target).status_code == 200
        assert events[:4] == ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate"]
        assert events.index("local_object") > events.index("inner_gate")
        assert len(calls) == 1


# ── revocation ────────────────────────────────────────────────────────────────

REVOCATIONS = {
    # id: (ancestor ViewSet class, ancestor fallback, grant kind); the grant satisfies the Publisher gate until revoked
    "guardian-direct": (GuardianViewSet, False, "direct"),
    "guardian-group-grant": (GuardianViewSet, False, "group-grant"),
    "guardian-group-membership": (GuardianViewSet, False, "group-membership"),
    "guardian-fallback-model": (GuardianViewSet, True, "model"),
    "core-model": (ViewSet, False, "model"),
    "core-model-group": (ViewSet, False, "model-group"),
}


@pytest.mark.parametrize("case", REVOCATIONS)
@pytest.mark.django_db
def test_revocation_applies_on_next_request(scope, case):
    """A grant revoked between two requests of the same session denies the next request: nothing is cached across
    requests (each request loads its actor afresh; provider checkers are request-local)."""
    pub_class, fallback, kind = REVOCATIONS[case]
    _pub_vs, book_vs = publisher_book(
        scope, pub_class=pub_class, pub_policy=AncestorPolicy(accept_global_perms=fallback)
    )
    pub_vs = book_vs.parent.viewset
    publisher = Publisher.objects.create(name="P")
    user = make_user("actor")
    group = Group.objects.create(name="ancestor-readers")
    view_publisher = Permission.objects.get(codename="view_publisher", content_type__app_label="app")
    if kind == "direct":
        pub_vs.assign_perm("view", user, publisher)
    elif kind in ("group-grant", "group-membership"):
        user.groups.add(group)
        pub_vs.assign_perm("view", group, publisher)
    elif kind == "model":
        user.user_permissions.add(view_publisher)
    else:  # model-group
        user.groups.add(group)
        group.permissions.add(view_publisher)
    client = client_for(user)  # one session for both requests
    target = url(book_vs, "list", publisher.pk)

    assert client.get(target).status_code == 200

    if kind == "direct":
        pub_vs.remove_perm("view", user, publisher)
    elif kind == "group-grant":
        pub_vs.remove_perm("view", group, publisher)
    elif kind == "group-membership":
        user.groups.remove(group)
    elif kind == "model":
        user.user_permissions.remove(view_publisher)
    else:
        group.permissions.remove(view_publisher)

    assert client.get(target).status_code == 403
