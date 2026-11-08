"""
Phase 06.18 plan 08 — the deliberate migration of repository authorization fixtures (D-13, D-28, D-40, D-41).

The removed child-side ``cv_guardian_parent_permission`` / ``cv_guardian_parent_create_permission`` fields became
the shared ancestor policy. These cases pin each changed historical expectation together with its negative
control, so the migrated fixtures elsewhere cannot hide a weakened gate:

* core versus Guardian parent: an object-only Publisher grant satisfies only a Guardian parent, a model-only grant
  only a core parent — migrating can remove *and* add access (D-40); converting the parent class to
  ``GuardianViewSet`` retains object-based protection;
* the default Write pair: child update/delete need Publisher ``change``; Publisher ``view`` alone, a child-only and
  a parent-only grant each fail their own gate (D-13);
* ancestor fallback is the Publisher ViewSet's own ``AncestorPolicy.accept_global_perms``: it applies to every
  descendant selecting it, whatever each child view's local ``cv_guardian_accept_global_perms``, and never relaxes
  a strict child object gate (D-41);
* nested Guardian create keeps the parent state gate and gains no child model-add gate (D-21/D-22);
* the old declarations themselves are rejected, never translated (D-28).

Routes are built behind a temporary ROOT_URLCONF by ``isolated_routes``; the project URLconf is imported at module
import so the registry snapshot always contains the shared app ViewSets.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from guardian.shortcuts import assign_perm
from pydantic import ValidationError

import tests.test1.project.urls  # noqa: F401  (register the shared app ViewSets before any registry snapshot)
from crud_views.lib.viewset import _REGISTRY, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

PARENTS = ("core", "guardian", "fallback")


@pytest.fixture
def routes():
    """Per parent kind — core ``ViewSet``, strict ``GuardianViewSet`` and ``GuardianViewSet`` with ancestor fallback —
    two Guardian Book descendants selecting it: ``book`` (strict list, detail, update, delete, create with a state
    hook) and ``alt`` (a list whose own ``cv_guardian_accept_global_perms`` is enabled)."""
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    state = {"enabled": True, "calls": []}

    def build(sfx):
        parents = {
            "core": ViewSet(model=Publisher, name=f"amcore{sfx}"),
            "guardian": GuardianViewSet(model=Publisher, name=f"amg{sfx}"),
            "fallback": GuardianViewSet(
                model=Publisher, name=f"amfb{sfx}", ancestor_policy=AncestorPolicy(accept_global_perms=True)
            ),
        }
        ns = SimpleNamespace(parents=parents, book={}, alt={}, views={}, state=state)
        for kind, parent in parents.items():
            book = GuardianViewSet(
                model=Book, name=f"amb{kind}{sfx}", parent=ParentViewSet(name=parent.name, attribute="publisher")
            )
            alt = GuardianViewSet(
                model=Book, name=f"ama{kind}{sfx}", parent=ParentViewSet(name=parent.name, attribute="publisher")
            )
            common = {"cv_viewset": book, "cv_context_actions": []}

            @classmethod
            def enabled(cls, user, obj=None):
                state["calls"].append(obj)
                return state["enabled"]

            ns.views[kind] = SimpleNamespace(
                List=type("List", (GuardianListViewPermissionRequired,), {**common, "cv_list_actions": []}),
                Detail=type("Detail", (GuardianDetailViewPermissionRequired,), dict(common)),
                Update=type("Update", (GuardianUpdateViewPermissionRequired,), {**common, "fields": ["title"]}),
                Delete=type("Delete", (GuardianDeleteViewPermissionRequired,), dict(common)),
                Create=type(
                    "Create",
                    (CreateViewParentMixin, GuardianCreateViewPermissionRequired),
                    {**common, "fields": ["title"], "cv_action_enabled": enabled},
                ),
                AltList=type(
                    "AltList",
                    (GuardianListViewPermissionRequired,),
                    {
                        "cv_viewset": alt,
                        "cv_context_actions": [],
                        "cv_list_actions": [],
                        "cv_guardian_accept_global_perms": True,
                    },
                ),
            )
            ns.book[kind] = book
            ns.alt[kind] = alt
        return ns, [*parents.values(), *ns.book.values(), *ns.alt.values()]

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Penguin Book", publisher=penguin)
    return SimpleNamespace(penguin=penguin, other=other, book=book)


def _parent_kwargs(routes, kind, publisher):
    return {f"{routes.parents[kind].name}_pk": publisher.pk}


def _book_url(routes, kind, key, publisher, **extra):
    return _url(routes.book[kind], key, **_parent_kwargs(routes, kind, publisher), **extra)


def _alt_url(routes, kind, publisher):
    return _url(routes.alt[kind], "list", **_parent_kwargs(routes, kind, publisher))


def _publisher_object_grant(user, *actions, obj):
    for action in actions:
        assign_perm(f"app.{action}_publisher", user, obj)


def _book_object_grant(user, *actions, obj):
    for action in actions:
        assign_perm(f"app.{action}_book", user, obj)


def _titles(response):
    return sorted(book.title for book in response.context["object_list"])


# ── core parent versus Guardian parent: both possible access changes (D-40) ──


@pytest.mark.parametrize(
    ("kind", "grant", "allowed"),
    [
        ("core", "object", False),  # access loss: an object grant no longer satisfies a core parent
        ("core", "model", True),  # access gain: a model grant now satisfies a core parent
        ("guardian", "object", True),  # converting the parent to GuardianViewSet retains object protection
        ("guardian", "model", False),  # ... and a model-only grant does not satisfy it
    ],
)
@pytest.mark.django_db
def test_core_and_guardian_parent_accept_opposite_publisher_grants(routes, world, kind, grant, allowed):
    """List (Read: view) and create (Write: change) under each parent kind with only one kind of Publisher grant."""
    if grant == "model":
        user = _user("actor", (Publisher, "view"), (Publisher, "change"))
    else:
        user = _user("actor")
        _publisher_object_grant(user, "view", "change", obj=world.penguin)
    client = _client(user)

    expected = 200 if allowed else 403
    assert client.get(_book_url(routes, kind, "list", world.penguin)).status_code == expected
    assert client.get(_book_url(routes, kind, "create", world.penguin)).status_code == expected
    response = client.post(_book_url(routes, kind, "create", world.penguin), {"title": "Migrated"})
    assert response.status_code == (302 if allowed else 403)
    assert list(Book.objects.filter(title="Migrated").values_list("publisher_id", flat=True)) == (
        [world.penguin.pk] if allowed else []
    )


@pytest.mark.django_db
def test_core_parent_object_grant_on_other_publisher_and_no_grant_deny(routes, world):
    """Controls: the core parent's model gate has no object scope to abuse, and no grant denies both kinds."""
    nobody = _client(_user("nobody"))
    for kind in ("core", "guardian"):
        assert nobody.get(_book_url(routes, kind, "list", world.penguin)).status_code == 403
    other_grant = _user("other_grant")
    _publisher_object_grant(other_grant, "view", obj=world.other)
    client = _client(other_grant)
    assert client.get(_book_url(routes, "guardian", "list", world.penguin)).status_code == 403
    assert client.get(_book_url(routes, "guardian", "list", world.other)).status_code == 200
    assert client.get(_book_url(routes, "core", "list", world.other)).status_code == 403


# ── the default Write pair: child update/delete need Publisher change (D-13) ──


@pytest.mark.parametrize(
    ("parent_actions", "child_actions", "allowed"),
    [
        (("view",), ("view", "change", "delete"), False),  # the old parent "view" no longer suffices for Write
        (("view", "change"), ("view", "change", "delete"), True),
        (("view", "change"), (), False),  # parent-only: the local object gate still denies
        ((), ("view", "change", "delete"), False),  # child-only: the ancestor gate denies
    ],
)
@pytest.mark.django_db
def test_default_write_pair_requires_parent_change(routes, world, parent_actions, child_actions, allowed):
    user = _user("editor")
    _publisher_object_grant(user, *parent_actions, obj=world.penguin)
    _book_object_grant(user, *child_actions, obj=world.book)
    client = _client(user)
    pk = world.book.pk

    expected = 200 if allowed else 403
    assert client.get(_book_url(routes, "guardian", "update", world.penguin, pk=pk)).status_code == expected
    assert client.get(_book_url(routes, "guardian", "delete", world.penguin, pk=pk)).status_code == expected
    response = client.post(_book_url(routes, "guardian", "update", world.penguin, pk=pk), {"title": "Edited"})
    assert response.status_code == (302 if allowed else 403)
    world.book.refresh_from_db()
    assert world.book.title == ("Edited" if allowed else "Penguin Book")


@pytest.mark.django_db
def test_default_read_pair_keeps_parent_view_for_detail(routes, world):
    """Control: Read operations keep the old parent 'view' requirement."""
    user = _user("reader")
    _publisher_object_grant(user, "view", obj=world.penguin)
    _book_object_grant(user, "view", obj=world.book)
    client = _client(user)
    assert client.get(_book_url(routes, "guardian", "detail", world.penguin, pk=world.book.pk)).status_code == 200
    reader_without_parent = _user("reader_without_parent")
    _book_object_grant(reader_without_parent, "view", obj=world.book)
    response = _client(reader_without_parent).get(
        _book_url(routes, "guardian", "detail", world.penguin, pk=world.book.pk)
    )
    assert response.status_code == 403


# ── ancestor fallback is owned by the parent and independent of each child (D-41) ──


@pytest.mark.parametrize("descendant", ["book", "alt"])
@pytest.mark.parametrize(("kind", "allowed"), [("guardian", False), ("fallback", True)])
@pytest.mark.django_db
def test_parent_fallback_applies_to_every_descendant_whatever_its_local_flag(routes, world, descendant, kind, allowed):
    """A model-only Publisher grant: the strict parent denies both descendants (the ``alt`` list's own flag cannot
    relax it); the fallback parent admits both (the strict ``book`` list's own setting cannot block it)."""
    client = _client(_user("global_reader", (Publisher, "view")))
    url = (
        _book_url(routes, kind, "list", world.penguin)
        if descendant == "book"
        else _alt_url(routes, kind, world.penguin)
    )
    assert client.get(url).status_code == (200 if allowed else 403)


@pytest.mark.django_db
def test_permissive_parent_does_not_relax_strict_child_gates(routes, world):
    """Fallback parent + model-only Publisher and Book grants: the strict child list shows no rows and the strict
    child detail denies; the permissive descendant's own flag shows the row; a Book object grant opens detail."""
    user = _user("global_reader", (Publisher, "view"), (Book, "view"))
    client = _client(user)

    assert _titles(client.get(_book_url(routes, "fallback", "list", world.penguin))) == []
    assert _titles(client.get(_alt_url(routes, "fallback", world.penguin))) == ["Penguin Book"]
    detail = _book_url(routes, "fallback", "detail", world.penguin, pk=world.book.pk)
    assert client.get(detail).status_code == 403

    _book_object_grant(user, "view", obj=world.book)
    assert _client(user).get(detail).status_code == 200


@pytest.mark.django_db
def test_strict_parent_with_permissive_child_still_needs_the_parent_object_grant(routes, world):
    """Strict parent + permissive child: global Book view shows the row only once the Publisher object grant exists."""
    user = _user("mixed", (Publisher, "view"), (Book, "view"))
    url = _alt_url(routes, "guardian", world.penguin)
    assert _client(user).get(url).status_code == 403
    _publisher_object_grant(user, "view", obj=world.penguin)
    response = _client(user).get(url)
    assert response.status_code == 200
    assert _titles(response) == ["Penguin Book"]


# ── nested Guardian create: parent state, no child model-add gate (D-21/D-22) ──


@pytest.mark.django_db
def test_nested_guardian_create_needs_parent_change_and_state_but_no_child_add(routes, world):
    from django.contrib.auth.models import Permission

    user = _user("creator")
    _publisher_object_grant(user, "change", obj=world.penguin)
    assert not Permission.objects.filter(user=user, codename="add_book").exists()
    client = _client(user)
    url = _book_url(routes, "guardian", "create", world.penguin)

    routes.state["calls"].clear()
    assert client.get(url).status_code == 200
    assert client.post(url, {"title": "Created"}).status_code == 302
    assert Book.objects.get(title="Created").publisher_id == world.penguin.pk
    assert routes.state["calls"]
    assert all(type(obj) is Publisher and obj.pk == world.penguin.pk for obj in routes.state["calls"])

    # the state gate still applies with the resolved parent
    routes.state["enabled"] = False
    assert client.get(url).status_code == 403
    assert client.post(url, {"title": "Disabled"}).status_code == 403
    routes.state["enabled"] = True

    # Publisher view alone does not satisfy the Write pair; another Publisher's change grant does not either
    viewer = _user("viewer")
    _publisher_object_grant(viewer, "view", obj=world.penguin)
    _publisher_object_grant(viewer, "change", obj=world.other)
    assert _client(viewer).post(url, {"title": "Viewer"}).status_code == 403
    assert not Book.objects.filter(title__in=["Disabled", "Viewer"]).exists()


# ── the old declarations are rejected, never translated (D-28) ───────────────


@pytest.mark.parametrize(
    "legacy",
    [
        {"cv_guardian_parent_permission": "view", "cv_guardian_parent_create_permission": "change"},
        {"cv_guardian_parent_permission": None, "cv_guardian_parent_create_permission": None},
        {"cv_guardian_parent_permission": None},
        {"cv_guardian_parent_create_permission": "change"},
    ],
)
@pytest.mark.django_db
def test_old_fixture_declarations_are_rejected_before_registration(legacy):
    from crud_views_guardian.lib.viewset import GuardianViewSet

    name = "am_legacy_probe"
    with pytest.raises(ValidationError, match=r"removed before 1\.0"):
        GuardianViewSet(
            model=Book, name=name, parent=ParentViewSet(name="guardian_publisher", attribute="publisher"), **legacy
        )
    assert name not in _REGISTRY
