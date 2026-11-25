"""Stage 3a observations: real permissions, known objects, and separate gate/SQL costs.

The before receipt is immutable phase evidence. After pins describe the same
fixtures and cache preparation; gate calls remain separate from permission SQL.
"""

import json
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
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
from tests.test1.test_guardian_child_link_visibility import plain_child_cost_pin
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


def consumer_cost_pin(surface, rows, composition, allowed, actor_cache):
    """Measured stage-3a cells, factored only by identical observed conditions."""
    repeated = surface in {"row", "card-own", "card-child"}
    occurrences = rows if repeated else 1
    cancel = surface.startswith("cancel-")
    missing = cancel and surface.endswith("-missing")
    lookup = int(cancel and not surface.endswith("-guarded"))
    if not occurrences or missing:
        return {
            "queries": lookup,
            "permission_queries": 0,
            "categories": {"other": 1} if lookup else {},
            "hooks": {"ancestor": 0, "own": 0, "state": 0},
        }

    object_action = surface in {"context", "row", "card-own", "bulk", "cancel-object-guarded"}
    if (cancel and (composition == "guardian" or surface.endswith("-unguarded"))) or surface == "parent":
        gates = 1
    elif surface == "navbar":
        gates = 3 if allowed else 2
    else:
        gates = 2 if allowed or object_action else 1
    own = (2 if surface == "navbar" else 1) if allowed else 0
    hooks = {"ancestor": gates * occurrences, "own": own * occurrences, "state": own * occurrences}

    categories = {}
    if actor_cache == "cold":
        if composition == "core" or (composition == "mixed" and cancel and lookup):
            categories["model_or_vocabulary_permissions"] = 2
        elif composition == "mixed":
            categories.update(checker_user_grants=1, checker_group_grants=1)
            if allowed or object_action:
                categories["model_or_vocabulary_permissions"] = 2
        else:
            if cancel:
                objects = 2 if allowed and "object" in surface else 1
            elif surface == "bulk":
                objects = 2
                if allowed:
                    categories["model_or_vocabulary_permissions"] = 2
            elif surface in {"context", "row", "card-own"}:
                objects = 2 + (occurrences if allowed else 0)
            else:
                objects = 2 if allowed else 1
            categories.update(checker_user_grants=objects, checker_group_grants=objects)
    permission_queries = sum(categories.values())
    if lookup:
        categories["other"] = 1
    return {
        "queries": permission_queries + lookup,
        "permission_queries": permission_queries,
        "categories": categories,
        "hooks": hooks,
    }


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
        rendering = {
            "card-own": card,
            "card-child": parent_card,
            "child": parent_page,
            "navbar": parent_page,
            "bulk": source,
        }.get(surface, page)
        known = {
            ancestor.name: obj
            for (_, ancestor), obj in zip(
                ancestors._walk_ancestors(rendering.cv_viewset),
                getattr(rendering, "_cv_ancestor_state", SimpleNamespace(objects=())).objects,
                strict=False,
            )
        }
        if surface in {"child", "card-child", "navbar"}:
            known[ns.book.vs.name] = world.book

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
                "rendering_objects": {name: identity(obj) for name, obj in known.items()},
                "row_objects": [identity(row) for row in world.rows],
                "result": result if isinstance(result, (str, type(None))) else str(result),
                "sql": [q["sql"] for q in capture],
            }
            record_property("measurement", json.dumps(measurement, sort_keys=True))
            pin = consumer_cost_pin(surface, row_count, composition, allowed, actor_cache)
            assert {key: measurement[key] for key in pin if key != "hooks"} == {
                key: value for key, value in pin.items() if key != "hooks"
            }
            assert {kind: measurement["hooks"].get(kind, 0) for kind in pin["hooks"]} == pin["hooks"]
            if surface.startswith("cancel-"):
                lookups = [query["sql"] for query in capture if list_sql_category(query["sql"]) == "other"]
                assert all('from "app_book"' in sql.lower() for sql in lookups)
                assert bool(result) is (allowed and not surface.endswith("-missing"))
            elif surface in {"navbar", "bulk"}:
                assert bool(result) is allowed
                if surface == "navbar" and allowed:
                    assert len(result["items"]) == 2
            else:
                items = result if isinstance(result, list) else [result]
                assert all(item["cv_access"] is allowed and item["cv_action_enabled"] is True for item in items)
            if not surface.startswith("cancel-"):
                assert categories.get("list_filter", 0) == categories.get("other", 0) == 0
            assert all(event["actor"]["python_id"] == id(actor) for event in events)
            for event in events:
                if event["kind"] == "ancestor":
                    if event["viewset"] in known:
                        assert event["object"] == identity(known[event["viewset"]])
                    else:
                        # Only unguarded Cancel can obtain a fresh object during capture.
                        assert surface.endswith("-unguarded") and event["viewset"] == ns.book.vs.name
                        assert event["object"]["model"] == "app.book"
                        assert event["object"]["pk"] == str(world.book.pk)
                elif event["target"] in {ns.note.Update.__name__}:
                    assert event["object"] in [identity(row) for row in world.rows] or event["object"] == identity(
                        world.note
                    )
                elif event["kind"] == "own" and event["target"] in {
                    ns.note.List.__name__,
                    ns.sibling.List.__name__,
                    ns.note.Bulk.__name__,
                }:
                    assert event["object"] is None
            if row_count == 0 and surface in {"row", "card-own", "card-child"}:
                assert result == [] and not events and len(capture) == 0


def read_cost_receipts():
    receipt = Path(
        ".planning/phases/06.50-move-remaining-link-consumers-to-the-shared-link-check-stage/06.50-COST-BASELINE.md"
    )
    before, after = receipt.read_text().split("\n## After measurements", 1)
    return before, json.loads(after.split("```json\n", 1)[1].split("\n```", 1)[0])


def validate_cost_receipts(before, after):
    # This fixed digest protects every original byte, including source/artifact hashes
    # and all before cells. No historical Git, XML temp path or network is needed.
    assert sha256(before.encode()).hexdigest() == "4e9436029aff6629e0a9c38d703beb50015b39d664e6486cb925a2fe09ab7c55"
    expected = {}
    for composition, cache, allowed, (surface, rows) in product(
        ("core", "guardian", "mixed"), ("cold", "warm"), (False, True), SCENARIOS
    ):
        key = "|".join(map(str, (composition, cache, allowed, surface, rows)))
        expected[key] = consumer_cost_pin(surface, rows, composition, allowed, cache)
    assert len(expected) == 276
    assert after["consumers"] == expected
    original_counts = {}
    for line in before.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 10 and cells[0] in {"core", "guardian", "mixed"}:
            composition, cache, grants, surface, rows = cells[:5]
            key = "|".join((composition, cache, str(grants == "allowed"), surface, rows))
            original_counts[key] = list(map(int, cells[5:]))
    assert original_counts.keys() == expected.keys()
    assert after["deltas"] == {
        key: [
            a - b
            for a, b in zip(
                [pin["queries"], pin["permission_queries"], *pin["hooks"].values()], original_counts[key], strict=True
            )
        ]
        for key, pin in expected.items()
    }

    navbar = {}
    for composition, page, placement, vocabulary, cache in product(
        ("plain", "guardian", "mixed"),
        ("owner", "deep"),
        ("tag", "split", "repeated", "components", "mixed-repeated"),
        ("cold", "warm"),
        ("cold", "warm"),
    ):
        key = f"test_navbar_isolated_costs[{cache}-{vocabulary}-{placement}-{page}-{composition}]"
        total = 2 if composition != "plain" and page == "owner" else 0
        total += (4 if vocabulary == "cold" else 0) + (2 if cache == "cold" and composition != "guardian" else 0)
        content_types = 2 if vocabulary == "cold" else 0
        categories = {
            k: v for k, v in {"content_type": content_types, "permissions": total - content_types}.items() if v
        }
        navbar[key] = {
            "composition": composition,
            "page": page,
            "placement": placement,
            "vocabulary": vocabulary,
            "actor_cache": cache,
            "queries": total,
            "permission_queries": total - content_types,
            "categories": categories,
            "builds": 1,
            "hooks": [1, 1, 1, 1],
            "ancestor_calls": 1,
        }
    assert after["navbar"] == navbar

    bulk = {}
    for nested, card, rows, actions in product((False, True), (False, True), (1, 5), (0, 1, 4)):
        shape = f"{'card' if card else 'table'}-{'nested' if nested else 'top'}"
        key = f"test_bulk_source_query_cost[{actions}-{rows}-{shape}]"
        total = 8 + int(nested) - int(card)
        categories = {"actor": 1, "session": 1, "permissions": 2, "other": 1}
        categories["child_or_relation_rows" if nested else "parent_rows"] = 2 if card else 3
        if nested:
            categories["parent_rows"] = 1
        bulk[key] = {
            "nested": nested,
            "card": card,
            "rows": rows,
            "actions": actions,
            "queries": total,
            "baseline_queries": total,
            "permission_queries": 2,
            "categories": categories,
            "own_calls": actions,
            "state_calls": actions,
            "ancestor_calls": actions if nested else 0,
        }
    assert after["bulk"] == bulk

    child = {}
    for provider, vocabulary, cache, renderer in product(
        ("model", "guardian"), ("cold", "warm"), ("fresh", "warm"), ("context", "card")
    ):
        key = f"test_query_plain_child_link_cost[{provider}-{vocabulary}-{cache}-{renderer}]"
        child[key] = [
            {
                "layer": "plain_destination",
                "parent_provider": provider,
                "renderer": renderer,
                "actor_cache": cache,
                "vocabulary": vocabulary,
                "results": plain_child_cost_pin(provider == "guardian", vocabulary, cache),
            }
        ]
    for renderer in ("context", "card"):
        child[f"test_query_cold_and_warm_discovery[{renderer}]"] = [
            {
                "layer": "adapter",
                "renderer": renderer,
                "helper_calls": 2,
                "results": {
                    "cold": {"total": 6, "categories": {"content_type": 2, "permissions": 4}},
                    "warm": {"total": 0, "categories": {}},
                },
            }
        ]
        child[f"test_query_create_uses_only_its_existing_parent_check[{renderer}]"] = [
            {
                "layer": "create_baseline",
                "renderer": renderer,
                "baseline": 2,
                "baseline_categories": {"permissions": 2},
                "rendered": 0,
                "categories": {},
                "helper_calls": 1,
            }
        ]
    child["test_query_unaffected_core_and_ordinary_actions"] = [
        {
            "layer": "mixed_core_guardian",
            "renderer": "context",
            "total": 2,
            "categories": {"permissions": 2},
            "helper_calls": 1,
        },
        {"layer": "mixed_core_guardian", "renderer": "card", "total": 0, "categories": {}, "helper_calls": 1},
        {
            "layer": "ordinary_baseline",
            "baseline": 0,
            "baseline_categories": {},
            "rendered": 0,
            "categories": {},
            "helper_calls": 0,
        },
    ]
    assert after["guardian_child"] == child


def test_cost_receipts():
    """All measured rows and categories agree with the independently exercised runtime pins."""
    validate_cost_receipts(*read_cost_receipts())


@pytest.mark.parametrize(
    "damage", ["missing-row", "missing-category", "lost-before-hash", "wrong-pin", "missing-navbar"]
)
def test_cost_receipts_reject_incomplete_or_changed_evidence(damage):
    before, original = read_cost_receipts()
    after = deepcopy(original)
    key = "core|cold|True|context|1"
    if damage == "missing-row":
        del after["consumers"][key]
    elif damage == "missing-category":
        del after["consumers"][key]["permission_queries"]
    elif damage == "lost-before-hash":
        before = before.replace("318080b9d6b53254f6c84a4b1e85ff238e8565fceba653699f0ef8883ee6420e", "lost")
    elif damage == "wrong-pin":
        after["consumers"][key]["hooks"]["ancestor"] += 1
    else:
        after["navbar"].pop(next(iter(after["navbar"])))
    with pytest.raises(AssertionError):
        validate_cost_receipts(before, after)
