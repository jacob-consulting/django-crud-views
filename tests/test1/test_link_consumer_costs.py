"""Current observations with immutable stage-3a evidence and separate gate/SQL costs.

The before receipt is immutable phase evidence. After pins describe the same
fixtures and cache preparation; gate calls remain separate from permission SQL.
"""

import json
import platform
import subprocess
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from importlib.metadata import version
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from xml.etree import ElementTree

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import assign_perm, remove_perm

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
from crud_views.templatetags.crud_views import cv_context_has_permission
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
CREATE_SCENARIOS = [
    (surface, rows)
    for surface in (
        "context-create",
        "child-create",
        "sibling-create",
        "card-create",
        "filter-create",
        "cancel-create-guarded",
        "cancel-create-unguarded",
        "cancel-create-missing",
    )
    for rows in ((0, 1, 3) if surface == "card-create" else (1,))
]
COST_CASES = [
    (surface, rows, composition, allowed, cache, "warm")
    for (surface, rows), composition, allowed, cache in product(
        SCENARIOS, ("core", "guardian", "mixed"), (False, True), ("cold", "warm")
    )
]
COST_CASES += [
    (surface, rows, "guardian", allowed, cache, vocabulary)
    for (surface, rows), allowed, cache, vocabulary in product(
        [*CREATE_SCENARIOS, *(case for case in SCENARIOS if case[0].startswith("cancel-"))],
        (False, True),
        ("cold", "warm", "fresh"),
        ("cold", "warm"),
    )
    if (surface, rows) in CREATE_SCENARIOS or cache == "fresh" or vocabulary == "cold"
]


CURRENT_RECEIPT_DIR = Path(__file__).resolve().parents[2] / (
    ".planning/phases/06.51-remove-retained-guardian-link-exceptions-stage-3b-413"
)


def current_cost_provenance():
    """Bind the raw measurement artifact to its actual working source and runtime."""
    root = Path(__file__).resolve().parents[2]
    sources = sorted((root / "src").rglob("*.py"))
    sources.extend(
        root / "tests/test1" / name
        for name in (
            "test_link_consumer_costs.py",
            "test_navbar_costs.py",
            "test_guardian_checker_costs.py",
            "test_ancestor_helpers.py",
            "test_ancestor_authorization.py",
            "app/models.py",
            "conftest.py",
        )
    )
    return {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "working_source_sha256": {
            str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in sources
        },
        "runtime": {
            "python": platform.python_version(),
            **{
                name: version(name)
                for name in (
                    "django",
                    "django-guardian",
                    "pytest",
                    "pytest-django",
                    "pytest-xdist",
                )
            },
        },
    }


def consumer_cost_pin(surface, rows, composition, allowed, actor_cache, vocabulary="warm"):
    """Fresh measured cells; historical receipts never call this function."""
    repeated = surface in {"row", "card-own", "card-child", "card-create"}
    occurrences = rows if repeated else 1
    cancel = surface.startswith("cancel-")
    missing = cancel and surface.endswith("-missing")
    lookup = int(cancel and not surface.endswith("-guarded"))
    if not occurrences or missing:
        return {
            "queries": lookup,
            "permission_queries": 0,
            "domain_lookups": lookup,
            "categories": {"other": 1} if lookup else {},
            "hooks": {"ancestor": 0, "own": 0, "create": 0, "state": 0},
        }

    if composition == "guardian" and (cancel or "create" in surface):
        create = "create" in surface
        unguarded = cancel and surface.endswith("-unguarded")
        if create:
            # One higher gate when known, then immediate gate plus the default
            # create hook's repeated immediate check. Grants are still reused.
            parent_levels = 1 if unguarded else 2
            gates = parent_levels + int(allowed)
            objects = vocabulary_types = parent_levels
        else:
            gates = 1 if unguarded or ("list" in surface and not allowed) else 2
            objects = gates + int(allowed and "object" in surface)
            vocabulary_types = gates + int(allowed)
        categories = {}
        if actor_cache != "warm":
            categories.update(checker_user_grants=objects, checker_group_grants=objects)
        if vocabulary == "cold":
            categories.update(content_type=vocabulary_types, model_or_vocabulary_permissions=vocabulary_types)
        if lookup:
            categories["other"] = lookup
        return {
            "queries": sum(categories.values()),
            "permission_queries": sum(
                value for key, value in categories.items() if key not in {"content_type", "other"}
            ),
            "domain_lookups": lookup,
            "categories": categories,
            "hooks": {
                "ancestor": gates * occurrences,
                "own": int(allowed and not create) * occurrences,
                "create": int(allowed and create) * occurrences,
                "state": int(allowed and surface != "filter-create") * occurrences,
            },
        }

    object_action = surface in {"context", "row", "card-own", "bulk", "cancel-object-guarded"}
    if (cancel and (composition == "guardian" or surface.endswith("-unguarded"))) or surface == "parent":
        gates = 1
    elif surface == "navbar":
        gates = 3 if allowed else 2
    else:
        gates = 2 if allowed or object_action else 1
    own = (2 if surface == "navbar" else 1) if allowed else 0
    hooks = {"ancestor": gates * occurrences, "own": own * occurrences, "create": 0, "state": own * occurrences}

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
        "domain_lookups": lookup,
        "categories": categories,
        "hooks": hooks,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("surface,row_count,composition,allowed,actor_cache,vocabulary", COST_CASES)
def test_consumer_costs(
    surface, row_count, composition, allowed, actor_cache, vocabulary, monkeypatch, record_property
):
    # Repository-only capture metadata is not a source-distribution prerequisite.
    if (
        CURRENT_RECEIPT_DIR.is_dir()
        and (surface, row_count, composition, allowed, actor_cache, vocabulary) == COST_CASES[0]
    ):
        record_property("provenance", json.dumps(current_cost_provenance(), sort_keys=True))
    with isolated_routes(lambda suffix: consumer_routes(suffix, composition)) as ns:
        world = consumer_world(row_count)
        setup_actor = consumer_actor(ns, world, allowed=not allowed if actor_cache == "fresh" else allowed)
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
            page.cv_cancel_key = "update" if "object" in surface else "create" if "create" in surface else "list"
            if not surface.endswith("-guarded"):
                del page._cv_ancestor_state
            if surface.endswith("-missing"):
                page.kwargs[ns.note.vs.parent.get_pk_name()] = world.book.pk + 9999
        parent_page.cv_navbar = NavBar(
            viewset=ns.book.vs.name, items=[NavItem(key="update"), NavItem(child=ns.note.vs.name)]
        )
        rendering = {
            "card-own": card,
            "card-create": card,
            "card-child": parent_card,
            "child": parent_page,
            "child-create": parent_page,
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
        if surface in {"child", "child-create", "card-child", "navbar"}:
            known[ns.book.vs.name] = world.book

        def observe():
            context = page.cv_get_view_context(object=world.note)
            if surface == "context":
                return ContextButton(key="edit", key_target="update").get_context(context)
            if surface == "context-create":
                return ContextButton(key="new", key_target="create").get_context(context)
            if surface == "filter-create":
                return cv_context_has_permission(page, "create")
            if surface == "parent":
                return ParentContextButton(key="parent", key_target="update").get_context(context)
            if surface == "sibling":
                return SiblingContextButton(key="sibling", sibling_name=ns.sibling.vs.name).get_context(context)
            if surface == "sibling-create":
                return SiblingContextButton(
                    key="new", sibling_name=ns.sibling.vs.name, sibling_key="create"
                ).get_context(context)
            if surface == "child":
                return ChildContextButton(key="child", child_name=ns.note.vs.name).get_context(
                    parent_page.cv_get_view_context(object=world.book)
                )
            if surface == "child-create":
                return ChildContextButton(key="new", child_name=ns.note.vs.name, child_key="create").get_context(
                    parent_page.cv_get_view_context(object=world.book)
                )
            if surface == "row":
                return [page.cv_get_context("update", obj=row, user=actor) for row in world.rows]
            if surface == "card-own":
                return [card.cv_get_card_action_data(CardAction(key="update"), row, actor) for row in world.rows]
            if surface == "card-create":
                return [card.cv_get_card_action_data(CardAction(key="create"), row, actor) for row in world.rows]
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

        previous_actor = previous_result = None
        if actor_cache == "fresh":
            # Exercise the old retained user, then change real grants and fetch a
            # new User. No checker invalidation or decision cache is introduced.
            previous_actor = actor
            previous_result = observe()
            grant = assign_perm if allowed else remove_perm
            for family, obj in ((ns.pub, world.pub), (ns.book, world.book), (ns.note, world.note)):
                grant(family.vs.permissions["change"], actor)
                grant(family.vs.permissions["change"], actor, obj)
            actor = User.objects.get(pk=actor.pk)
            assert actor is not previous_actor
            for view in (page, card, parent_page, parent_card, source):
                view.request.user = actor
            if not surface.endswith("-missing"):
                previous_items = previous_result if isinstance(previous_result, list) else [previous_result]
                assert all(
                    (item["cv_access"] if isinstance(item, dict) else bool(item)) is not allowed
                    for item in previous_items
                )

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
            for target in (family.List, family.Detail, family.Update, family.Bulk, family.Create):
                hooks = [("own", "cv_has_access"), ("state", "cv_action_enabled")]
                if target is family.Create and hasattr(target, "cv_create_has_access"):
                    hooks.append(("create", "cv_create_has_access"))
                for kind, hook in hooks:
                    original = getattr(target, hook)

                    def spy(user, obj=None, *args, _original=original, _kind=kind, _target=target):
                        events.append(
                            {
                                "kind": _kind,
                                "target": _target.__name__,
                                "object": identity(args[0] if _kind == "create" else obj),
                                "actor": identity(user),
                                "rendering_view": id(obj) if _kind == "create" and obj is not None else None,
                            }
                        )
                        return _original(user, obj, *args)

                    monkeypatch.setattr(target, hook, Mock(side_effect=spy))
        if actor_cache == "warm":
            observe()  # warm this actual actor's Guardian grants, without caching decisions
            source.__dict__.pop("_cv_effective_bulk_actions", None)
            source.__dict__.pop("cv_bulk_buttons", None)
            events.clear()
        # Set vocabulary AFTER actor warm-up, so warm-user/cold-vocabulary is
        # an independent control rather than accidentally warming both axes.
        with cache_conditions([f.vs for f in ns.families], actor, vocabulary=vocabulary, actor_cache=actor_cache):
            with CaptureQueriesContext(connection) as capture:
                result = observe()
            categories = Counter(list_sql_category(q["sql"]) for q in capture)
            measurement = {
                "surface": surface,
                "rows": row_count,
                "composition": composition,
                "allowed": allowed,
                "actor_cache": actor_cache,
                "vocabulary": vocabulary,
                "queries": len(capture),
                "permission_queries": sum(v for k, v in categories.items() if "permission" in k or "grants" in k),
                "categories": dict(categories),
                "domain_lookups": categories.get("other", 0),
                "hooks": dict(Counter(event["kind"] for event in events)),
                "events": events,
                "actor": identity(actor),
                "previous_actor": identity(previous_actor),
                "previous_result": str(previous_result) if previous_actor else None,
                "page_object": identity(world.note),
                "guard_objects": [identity(obj) for obj in card._cv_ancestor_state.objects],
                "rendering_objects": {name: identity(obj) for name, obj in known.items()},
                "row_objects": [identity(row) for row in world.rows],
                "result": result if isinstance(result, (str, type(None))) else str(result),
                "sql": [q["sql"] for q in capture],
            }
            record_property("measurement", json.dumps(measurement, sort_keys=True))
            pin = consumer_cost_pin(surface, row_count, composition, allowed, actor_cache, vocabulary)
            assert {key: measurement[key] for key in pin if key != "hooks"} == {
                key: value for key, value in pin.items() if key != "hooks"
            }
            assert {kind: measurement["hooks"].get(kind, 0) for kind in pin["hooks"]} == pin["hooks"]
            assert measurement["hooks"].keys() <= pin["hooks"].keys()
            if surface.startswith("cancel-"):
                lookups = [query["sql"] for query in capture if list_sql_category(query["sql"]) == "other"]
                assert all('from "app_book"' in sql.lower() for sql in lookups)
                assert bool(result) is (allowed and not surface.endswith("-missing"))
            elif surface in {"navbar", "bulk", "filter-create"}:
                assert bool(result) is allowed
                if surface == "navbar" and allowed:
                    assert len(result["items"]) == 2
            else:
                items = result if isinstance(result, list) else [result]
                assert all(item["cv_access"] is allowed and item["cv_action_enabled"] is True for item in items)
            if not surface.startswith("cancel-"):
                assert categories.get("list_filter", 0) == categories.get("other", 0) == 0
            if not allowed or surface == "filter-create":
                assert measurement["hooks"].get("state", 0) == 0
            assert all(event["actor"]["python_id"] == id(actor) for event in events)
            for index, event in enumerate(events):
                if event["kind"] == "create":
                    # The default hook repeats exactly the preceding nearest gate;
                    # its invocation is independent of SQL/grant loading.
                    assert events[index - 1]["kind"] == "ancestor"
                    assert events[index + 1] == events[index - 1]
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
                elif event["target"] in {ns.note.Create.__name__, ns.sibling.Create.__name__}:
                    assert event["kind"] != "own"
                    assert event["object"]["model"] == "app.book"
                    assert event["object"]["pk"] == str(world.book.pk)
                    if ns.book.vs.name in known:
                        assert event["object"] == identity(known[ns.book.vs.name])
                    if event["kind"] == "create":
                        same_viewset = surface in {"context-create", "card-create", "filter-create"}
                        if surface.startswith("cancel-"):
                            assert event["rendering_view"] not in {None, id(page)}  # request-bound copy
                        else:
                            assert event["rendering_view"] == (id(rendering) if same_viewset else None)
            if row_count == 0 and surface in {"row", "card-own", "card-child", "card-create"}:
                assert result == [] and not events and len(capture) == 0


def read_cost_receipts():
    receipt = Path(__file__).resolve().parents[2] / (
        ".planning/phases/06.50-move-remaining-link-consumers-to-the-shared-link-check-stage/06.50-COST-BASELINE.md"
    )
    if not receipt.is_file():
        pytest.skip("Phase cost receipts are repository-only evidence, excluded from source distributions.")
    raw = receipt.read_bytes()
    assert sha256(raw).hexdigest() == "8fad0731238a4c0843713dcb8c59f057f81079827b757db7fce000030c5c04c7"
    before, after = raw.decode().split("\n## After measurements", 1)
    return before, json.loads(after.split("```json\n", 1)[1].split("\n```", 1)[0])


def validate_cost_receipts(before, after):
    # This fixed digest protects every original byte, including source/artifact hashes
    # and all before cells. No historical Git, XML temp path or network is needed.
    assert sha256(before.encode()).hexdigest() == "4e9436029aff6629e0a9c38d703beb50015b39d664e6486cb925a2fe09ab7c55"
    # Freeze the already recorded payload, not a second historical pin algorithm.
    assert sha256(json.dumps(after, sort_keys=True).encode()).hexdigest() == (
        "ae30e6886626925c8b35b509c0d6dcf70b8dbddab19d224600247434fc7f7085"
    )
    expected = after["consumers"]
    assert len(expected) == 276
    assert sha256((json.dumps(sorted(expected)) + "\n").encode()).hexdigest() == (
        "ac61567f2a4545bf517511b0a3a6843fe0d796cb6a2458cc671ab6ee5d0d3d4b"
    )
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
                [pin["queries"], pin["permission_queries"], *(pin["hooks"][k] for k in ("ancestor", "own", "state"))],
                original_counts[key],
                strict=True,
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


def current_measurement_key(measurement):
    return "|".join(
        str(measurement[key])
        for key in (
            "surface",
            "rows",
            "composition",
            "allowed",
            "actor_cache",
            "vocabulary",
        )
    )


def current_measurement_pin(measurement):
    return {
        **{key: measurement[key] for key in ("queries", "permission_queries", "domain_lookups", "categories")},
        "hooks": {kind: measurement["hooks"].get(kind, 0) for kind in ("ancestor", "own", "create", "state")},
    }


def read_current_cost_receipt():
    receipt = CURRENT_RECEIPT_DIR / "06.51-COST-BASELINE.md"
    if not receipt.is_file():
        pytest.skip("Phase cost receipts are repository-only evidence, excluded from source distributions.")
    payload = json.loads(receipt.read_text().split("## Current measurements\n\n```json\n", 1)[1].split("\n```", 1)[0])
    return payload, (CURRENT_RECEIPT_DIR / "06.51-COST-MEASUREMENTS.xml").read_bytes()


def validate_current_cost_receipt(receipt, raw_xml):
    """Cross-check current pins against independent raw SQL/events and receipt rows."""
    assert receipt["xml_sha256"] == sha256(raw_xml).hexdigest()
    document = ElementTree.fromstring(raw_xml)
    suites = document.findall("testsuite")
    assert len(suites) == 1
    suite = suites[0]
    assert all(suite.attrib[key] == "0" for key in ("failures", "errors", "skipped"))
    assert int(suite.attrib["tests"]) == len(COST_CASES) == len(set(COST_CASES))
    assert len(suite.findall("testcase")) == len(COST_CASES)
    expected_keys = {"|".join(map(str, case)) for case in COST_CASES}
    measured = {}
    for case in suite.findall("testcase"):
        properties = [p for p in case.findall("properties/property") if p.attrib["name"] == "measurement"]
        assert len(properties) == 1
        measurement = json.loads(properties[0].attrib["value"])
        key = current_measurement_key(measurement)
        assert key in expected_keys
        assert key not in measured
        assert measurement["queries"] == len(measurement["sql"])
        categories = dict(Counter(list_sql_category(sql) for sql in measurement["sql"]))
        assert categories == measurement["categories"]
        assert measurement["domain_lookups"] == categories.get("other", 0)
        assert measurement["permission_queries"] == sum(
            value for category, value in categories.items() if "permission" in category or "grants" in category
        )
        assert measurement["hooks"] == dict(Counter(event["kind"] for event in measurement["events"]))
        assert all(event["actor"] == measurement["actor"] for event in measurement["events"])
        measured[key] = current_measurement_pin(measurement)
        pin = consumer_cost_pin(
            *(
                measurement[field]
                for field in (
                    "surface",
                    "rows",
                    "composition",
                    "allowed",
                    "actor_cache",
                    "vocabulary",
                )
            )
        )
        assert measured[key] == pin
    assert measured.keys() == expected_keys == receipt["consumers"].keys()
    assert receipt["consumers"] == measured
    provenance = [p for p in suite.findall(".//property") if p.attrib["name"] == "provenance"]
    assert len(provenance) == 1
    assert receipt["provenance"] == json.loads(provenance[0].attrib["value"])
    assert len(receipt["provenance"]["source_revision"]) == 40
    assert "tests/test1/test_link_consumer_costs.py" in receipt["provenance"]["working_source_sha256"]
    assert all(len(value) == 64 for value in receipt["provenance"]["working_source_sha256"].values())


def test_current_cost_receipt():
    validate_current_cost_receipt(*read_current_cost_receipt())


@pytest.mark.parametrize(
    "damage",
    [
        "missing-row",
        "extra-row",
        "wrong-count",
        "wrong-category",
        "wrong-hook",
        "wrong-source",
        "wrong-runtime",
        "wrong-xml-hash",
        "lost-measurement",
        "lost-provenance",
        "raw-sql",
        "raw-hook",
        "raw-actor",
        "scenario-key",
    ],
)
def test_current_cost_receipt_rejects_damaged_evidence(damage):
    original, raw_xml = read_current_cost_receipt()
    receipt = deepcopy(original)
    key = next(iter(receipt["consumers"]))
    if damage == "missing-row":
        del receipt["consumers"][key]
    elif damage == "extra-row":
        receipt["consumers"]["unknown"] = receipt["consumers"][key]
    elif damage == "wrong-count":
        receipt["consumers"][key]["queries"] += 1
    elif damage == "wrong-category":
        receipt["consumers"][key]["categories"]["other"] = 99
    elif damage == "wrong-hook":
        receipt["consumers"][key]["hooks"]["create"] += 1
    elif damage == "wrong-source":
        receipt["provenance"]["source_revision"] = "0" * 40
    elif damage == "wrong-runtime":
        receipt["provenance"]["runtime"]["django"] = "changed"
    elif damage == "wrong-xml-hash":
        receipt["xml_sha256"] = "0" * 64
    else:
        document = ElementTree.fromstring(raw_xml)
        properties = document.findall(".//properties")
        if damage == "lost-provenance":
            parent = next(p for p in properties if any(c.attrib["name"] == "provenance" for c in p))
            parent.remove(next(c for c in parent if c.attrib["name"] == "provenance"))
        else:
            parent = next(p for p in properties if any(c.attrib["name"] == "measurement" for c in p))
            prop = next(c for c in parent if c.attrib["name"] == "measurement")
            if damage == "raw-actor":
                prop = next(
                    c
                    for p in properties
                    for c in p
                    if c.attrib["name"] == "measurement" and json.loads(c.attrib["value"])["events"]
                )
            if damage == "lost-measurement":
                parent.remove(prop)
            else:
                data = json.loads(prop.attrib["value"])
                if damage == "raw-sql":
                    data["sql"].append("SELECT 1")
                elif damage == "raw-hook":
                    data["events"].append({"kind": "state", "actor": data["actor"]})
                elif damage == "raw-actor":
                    data["actor"]["python_id"] = -1
                else:
                    data["surface"] = "unknown"
                prop.attrib["value"] = json.dumps(data)
        raw_xml = ElementTree.tostring(document)
        # Rehash deliberately: semantic corruption must fail independently of
        # the easy byte-hash mismatch check.
        receipt["xml_sha256"] = sha256(raw_xml).hexdigest()
    with pytest.raises(AssertionError):
        validate_current_cost_receipt(receipt, raw_xml)


def test_current_pin_change_does_not_reinterpret_history(monkeypatch):
    receipt, raw_xml = read_current_cost_receipt()
    original = consumer_cost_pin

    def changed(*args):
        pin = original(*args)
        pin["queries"] += 1
        return pin

    monkeypatch.setattr(__name__ + ".consumer_cost_pin", changed)
    with pytest.raises(AssertionError):
        validate_current_cost_receipt(receipt, raw_xml)
    validate_cost_receipts(*read_cost_receipts())


def test_repository_receipt_absence_skips_only_audits(monkeypatch):
    original = Path.is_file
    names = {"06.50-COST-BASELINE.md", "06.51-COST-BASELINE.md"}
    monkeypatch.setattr(Path, "is_file", lambda path: False if path.name in names else original(path))
    for read in (read_cost_receipts, read_current_cost_receipt):
        with pytest.raises(pytest.skip.Exception, match="repository-only"):
            read()
    assert len(COST_CASES) == 444  # Runtime parametrization never reads repository receipts.


def test_cost_receipts():
    """Historical rows, categories, deltas and complete bytes retain their original meaning."""
    validate_cost_receipts(*read_cost_receipts())


def test_historical_cost_receipts_are_independent_of_current_pins(monkeypatch):
    monkeypatch.setattr(__name__ + ".consumer_cost_pin", lambda *args: {})
    monkeypatch.setattr(__name__ + ".SCENARIOS", [])
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
