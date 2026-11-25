"""Stage 3a observations: real permissions, known objects, and separate gate/SQL costs.

The before receipt is immutable phase evidence. Plan 09 adds measured after pins;
these scenarios deliberately do not assert historical before counts after migration.
"""

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import assign_perm

from crud_views.lib import ancestors
from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.navbar import NavBar, NavItem, _build
from crud_views.lib.view import CardAction, ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.views import (
    CardListView,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_ancestor_helpers import _bound
from tests.test1.test_guardian_checker_costs import list_sql_category
from tests.test1.test_navbar_costs import cache_conditions


def consumer_routes(suffix, composition="core"):
    """Three real model levels plus a sibling collection; no synthetic product views."""
    families = []

    def family(model, label, parent=None, attribute=None):
        guarded = composition == "guardian" or (composition == "mixed" and parent is None)
        vs = (GuardianViewSet if guarded else ViewSet)(
            model=model,
            name=f"consumer{label}{suffix}",
            parent=ParentViewSet(name=parent.vs.name, attribute=attribute) if parent else None,
            ancestor_policy=AncestorPolicy(cascade=True) if parent else AncestorPolicy(),
        )
        bases = (
            [
                GuardianListViewPermissionRequired,
                GuardianDetailViewPermissionRequired,
                GuardianUpdateViewPermissionRequired,
                GuardianDeleteViewPermissionRequired,
                GuardianCreateViewPermissionRequired,
            ]
            if guarded
            else [
                ListViewPermissionRequired,
                DetailViewPermissionRequired,
                UpdateViewPermissionRequired,
                DeleteViewPermissionRequired,
                CreateViewPermissionRequired,
            ]
        )
        common = {"cv_viewset": vs, "cv_context_actions": [], "cv_list_actions": []}
        field = {Publisher: "name", Book: "title", BookNote: "note"}[model]
        result = SimpleNamespace(vs=vs)
        for key, base in zip(("List", "Detail", "Update", "Delete", "Create"), bases, strict=True):
            parents = (CreateViewParentMixin, base) if key == "Create" and parent else (base,)
            setattr(result, key, type(f"Consumer{label}{key}", parents, {**common, "fields": [field]}))
        result.Card = type(f"Consumer{label}Card", (CardListView,), common.copy())
        result.Bulk = type(
            f"Consumer{label}Bulk",
            (BulkFormViewPermissionRequired,),
            {
                **common,
                "cv_key": "mark",
                "cv_path": "mark",
                "cv_permission": "change",
                "cv_success_key": "list",
                "cv_action_label_template_code": "Mark selected",
                "cv_action_short_label_template_code": "Mark",
            },
        )
        result.Source = type(
            f"Consumer{label}Source",
            (BulkSelectionMixin, ListViewPermissionRequired),
            {**common, "cv_key": "source", "cv_path": "source", "cv_bulk_actions": ("mark",)},
        )
        families.append(result)
        return result

    pub = family(Publisher, "pub")
    book = family(Book, "book", pub, "publisher")
    note = family(BookNote, "note", book, "book")
    sibling = family(BookNote, "sibling", book, "book")
    return SimpleNamespace(pub=pub, book=book, note=note, sibling=sibling, families=families), [f.vs for f in families]


def consumer_world(row_count=1):
    pub = Publisher.objects.create(name="Consumer publisher")
    book = Book.objects.create(title="Consumer book", publisher=pub)
    rows = [BookNote.objects.create(book=book, note=f"Consumer row {i}") for i in range(row_count)]
    # A page object exists independently of the rendered row count.
    page = rows[0] if rows else BookNote.objects.create(book=book, note="Page object")
    return SimpleNamespace(pub=pub, book=book, note=page, rows=rows)


def consumer_actor(ns, world, *, allowed=True):
    actor = User.objects.create_user(username="consumer")
    for family, objects in ((ns.pub, [world.pub]), (ns.book, [world.book]), (ns.note, [world.note, *world.rows])):
        for key in ("view", "change", "add", "delete") if allowed else ("view",):
            permission = family.vs.permissions[key]
            # Core bulk is intentionally a core destination, also on a Guardian ViewSet.
            assign_perm(permission, actor)
            if isinstance(family.vs, GuardianViewSet):
                for obj in objects:
                    assign_perm(permission, actor, obj)
    return User.objects.get(pk=actor.pk)


def consumer_view(family, key, actor, world, *, guarded=True):
    kwargs = {}
    for edge, ancestor in ancestors._walk_ancestors(family.vs):
        kwargs[edge.get_pk_name()] = {Publisher: world.pub, Book: world.book}[ancestor.model].pk
    cls = getattr(family, key)
    obj = {Publisher: world.pub, Book: world.book, BookNote: world.note}[family.vs.model]
    if cls.cv_object:
        kwargs["pk"] = obj.pk
    view = _bound(cls, actor, **kwargs)
    view.request.resolver_match = SimpleNamespace(url_name=family.vs.get_router_name(cls.cv_key))
    if guarded:
        assert view._cv_ancestor_guard() is None
    view.object = obj if cls.cv_object else None
    return view


def identity(obj):
    if obj is None:
        return None
    return {"model": obj._meta.label_lower, "pk": str(obj.pk), "python_id": id(obj)}


SURFACES = ["context", "parent", "sibling", "child", "row", "card-own", "card-child", "navbar", "bulk"]
SURFACES += [
    f"cancel-{target}-{state}" for target in ("object", "list") for state in ("guarded", "unguarded", "missing")
]
SCENARIOS = [
    (surface, rows)
    for surface in SURFACES
    for rows in ((0, 1, 3) if surface in {"row", "card-own", "card-child", "bulk"} else (1,))
]


@pytest.mark.django_db
@pytest.mark.parametrize("surface,row_count", SCENARIOS)
@pytest.mark.parametrize("composition", ["core", "guardian", "mixed"])
@pytest.mark.parametrize("allowed", [False, True], ids=["denied", "allowed"])
@pytest.mark.parametrize("actor_cache", ["cold", "warm"])
def test_consumer_costs(surface, row_count, composition, allowed, actor_cache, monkeypatch, record_property):
    with isolated_routes(lambda suffix: consumer_routes(suffix, composition)) as ns:
        world = consumer_world(row_count)
        setup_actor = consumer_actor(ns, world, allowed=allowed)
        # Resolve source-page ancestors before measurement, then replace only the
        # actor with a fresh instance. Guard SQL is not incremental consumer SQL.
        page = consumer_view(ns.note, "Detail", setup_actor, world)
        card = consumer_view(ns.note, "Card", setup_actor, world)
        parent_page = consumer_view(ns.book, "Detail", setup_actor, world)
        parent_card = consumer_view(ns.book, "Card", setup_actor, world)
        source = consumer_view(ns.note, "Source", setup_actor, world)
        actor = User.objects.get(pk=setup_actor.pk)
        for view in (page, card, parent_page, parent_card, source):
            view.request.user = actor
        # Read destinations require change only in this scenario, while the source
        # Detail request uses the default Read pair. Denials are real provider results.
        for family in (ns.note, ns.sibling):
            family.vs.ancestor_policy = AncestorPolicy(
                cascade=True, actions={"list": AncestorPermissions(nearest="change", higher="change")}
            )
        if surface.startswith("cancel-"):
            page.cv_cancel_keys = []
            page.cv_cancel_key = "update" if "object" in surface else "list"
            if not surface.endswith("-guarded"):
                del page._cv_ancestor_state
            if surface.endswith("-missing"):
                page.kwargs[ns.note.vs.parent.get_pk_name()] = world.book.pk + 9999
        parent_page.cv_navbar = NavBar(
            viewset=ns.book.vs.name, items=[NavItem(key="update"), NavItem(child=ns.note.vs.name)]
        )

        def observe():
            context = page.cv_get_view_context(object=world.note)
            if surface == "context":
                return ContextButton(key="edit", key_target="update").get_context(context)
            if surface == "parent":
                return ParentContextButton(key="parent", key_target="update").get_context(context)
            if surface == "sibling":
                return SiblingContextButton(key="sibling", sibling_name=ns.sibling.vs.name).get_context(context)
            if surface == "child":
                return ChildContextButton(key="child", child_name=ns.note.vs.name).get_context(
                    parent_page.cv_get_view_context(object=world.book)
                )
            if surface == "row":
                return [page.cv_get_context("update", obj=row, user=actor) for row in world.rows]
            if surface == "card-own":
                return [card.cv_get_card_action_data(CardAction(key="update"), row, actor) for row in world.rows]
            if surface == "card-child":
                return [
                    parent_card.cv_get_card_action_data(CardAction(child_name=ns.note.vs.name), world.book, actor)
                    for _ in world.rows
                ]
            if surface == "navbar":
                return _build(parent_page)
            if surface == "bulk":
                return source.cv_bulk_buttons
            return page.cv_get_cancel_url()

        events = []
        originals = {cls: cls._ancestor_has_permission for cls in (ViewSet, GuardianViewSet)}
        for cls, original in originals.items():

            def provider(vs, user, permission, obj, *, view, _original=original):
                events.append(
                    {
                        "kind": "ancestor",
                        "viewset": vs.name,
                        "permission": permission,
                        "object": identity(obj),
                        "actor": identity(user),
                    }
                )
                return _original(vs, user, permission, obj, view=view)

            monkeypatch.setattr(cls, "_ancestor_has_permission", provider)
        for family in ns.families:
            for target in (family.List, family.Detail, family.Update, family.Bulk):
                for kind, hook in (("own", "cv_has_access"), ("state", "cv_action_enabled")):
                    original = getattr(target, hook)

                    def spy(user, obj=None, _original=original, _kind=kind, _target=target):
                        events.append(
                            {
                                "kind": _kind,
                                "target": _target.__name__,
                                "object": identity(obj),
                                "actor": identity(user),
                            }
                        )
                        return _original(user, obj)

                    monkeypatch.setattr(target, hook, Mock(side_effect=spy))
        with cache_conditions([f.vs for f in ns.families], actor, vocabulary="warm", actor_cache=actor_cache):
            if actor_cache == "warm":
                observe()  # warm this actual actor's Guardian grants, without caching decisions
                source.__dict__.pop("_cv_effective_bulk_actions", None)
                source.__dict__.pop("cv_bulk_buttons", None)
                events.clear()
            with CaptureQueriesContext(connection) as capture:
                result = observe()
            categories = Counter(list_sql_category(q["sql"]) for q in capture)
            measurement = {
                "surface": surface,
                "rows": row_count,
                "composition": composition,
                "allowed": allowed,
                "actor_cache": actor_cache,
                "vocabulary": "warm",
                "queries": len(capture),
                "permission_queries": sum(v for k, v in categories.items() if "permission" in k or "grants" in k),
                "categories": dict(categories),
                "hooks": dict(Counter(event["kind"] for event in events)),
                "events": events,
                "actor": identity(actor),
                "page_object": identity(world.note),
                "guard_objects": [identity(obj) for obj in card._cv_ancestor_state.objects],
                "row_objects": [identity(row) for row in world.rows],
                "result": result if isinstance(result, (str, type(None))) else str(result),
                "sql": [q["sql"] for q in capture],
            }
            record_property("measurement", json.dumps(measurement, sort_keys=True))
            if not surface.startswith("cancel-"):
                assert categories.get("list_filter", 0) == categories.get("other", 0) == 0
            assert all(event["actor"]["python_id"] == id(actor) for event in events)
            if row_count == 0 and surface in {"row", "card-own", "card-child"}:
                assert result == [] and not events and len(capture) == 0


def test_cost_receipts():
    """The final phase gate requires both measurements; first capture deselects this test."""
    receipt = Path(
        ".planning/phases/06.50-move-remaining-link-consumers-to-the-shared-link-check-stage/06.50-COST-BASELINE.md"
    )
    text = receipt.read_text()
    assert "## Before measurements" in text
    assert "## After measurements" in text
