"""Frozen link outcomes with individually ledgered stage-3a permission denials.

The original snapshot is reconstructible from the current cells and explicit
before values. Runtime checks require no historical Git checkout or planning files.
"""

import json
import re
from contextlib import contextmanager, nullcontext
from hashlib import sha256
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.template import Context, Template
from django.test import Client, override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm

from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.view import CardAction, ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.views import CardListView, CardListViewPermissionRequired, DetailView, ListViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianUpdateViewPermissionRequired
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1 import test_guardian_child_link_visibility as child_links
from tests.test1 import test_guardian_parent_none as parent_none
from tests.test1.app.models import Book, BookNote, Genre, Publisher
from tests.test1.app.views import cv_genre
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_ancestor_resources import TopFile
from tests.test1.test_authorization_matrix import ALLOW_INACTIVE, INACTIVE_BACKENDS
from tests.test1.test_guardian_child_link_visibility import bound, configure, rendered_data, replace_list
from tests.test1.test_guardian_parent_none import _record_card_actions, _strict_policy
from tests.test1.test_navbar import navbar_routes
from tests.test1.test_navbar_permissions import lazy_host, permission_routes

links = child_links.links
plain_links = child_links.plain_links
core_links = child_links.core_links
helpers = ancestor_helpers.helpers
pn = parent_none.pn

ACTORS = ("anonymous", "inactive", "superuser", "model", "direct", "group", "direct-view")
CONTROLS = ("child-button", "card-child", "navbar-child")
OUTCOMES = {"hidden", "enabled", "disabled:permission", "disabled:state"}
BASELINE = json.loads(Path(__file__).with_name("link_access_matrix_baseline.json").read_text())


class AnonymousParentEditorBackend(BaseBackend):
    """L2: a core parent provider can grant anonymous actors its change permission."""

    def has_perm(self, user_obj, perm, obj=None):
        return not user_obj.is_authenticated and perm == "app.change_publisher"


def _case_id(*parts):
    assert len(parts) == 7 and all("/" not in part for part in parts)
    return "/".join(parts)


def _parent_cases():
    cases = list(
        product(
            CONTROLS,
            ("plain", "guardian", "mixed"),
            ("parent",),
            ("list", "create"),
            ACTORS,
            ("on", "off"),
            ("hide", "disable"),
        )
    )
    scenarios = (
        ("plain-3", "list", ("near-only",)),
        ("guardian-queryset-only", "list", ("no-parent-grant", "anonymous", "inactive")),
        ("plain-resource", "list", ACTORS),
        ("core-guardian", "create", (*ACTORS, "anonymous-backend")),
    )
    for composition, target, actors in scenarios:
        cases.extend(
            product(
                ("child-button", "card-child"), (composition,), ("parent",), (target,), actors, ("on",), ("disable",)
            )
        )
    for composition, actor in (("plain-3", "near-only"), ("guardian-queryset-only", "no-parent-grant")):
        cases.append(("request", composition, "parent", "list", actor, "on", "disable"))
    return cases


def _page_cases():
    cases = []
    for composition in ("plain", "guardian", "guardian-m2m"):
        pages = (
            ("list", "detail") if composition == "guardian-m2m" else ("list", "detail", "update", "delete", "create")
        )
        cases.extend(
            product(
                ("create-control",),
                (composition,),
                pages,
                ("create-action", "create-alias"),
                ACTORS,
                ("on", "off"),
                ("disable",),
            )
        )
    cases.extend(
        product(("home-button",), ("plain", "guardian"), ("detail",), ("list",), ACTORS, ("on",), ("disable",))
    )
    cases.extend(
        product(
            ("parent-button",),
            ("plain", "guardian"),
            ("list",),
            ("parent-list", "parent-detail"),
            ACTORS,
            ("on",),
            ("disable",),
        )
    )
    cases.extend(
        product(
            ("parent-button",),
            ("guardian-3",),
            ("list", "detail"),
            ("parent-create",),
            (*ACTORS, "near-change", "far-change"),
            ("on",),
            ("disable",),
        )
    )
    cases.extend(
        product(
            ("sibling-button",),
            ("plain", "guardian"),
            ("list", "detail"),
            ("sibling-list", "sibling-create"),
            ACTORS,
            ("on", "off"),
            ("disable",),
        )
    )
    cases.extend(product(("row-action",), ("plain", "guardian"), ("list",), ("detail",), ACTORS, ("on",), ("disable",)))
    cases.extend(
        product(("card-action",), ("plain", "guardian"), ("card",), ("detail", "create"), ACTORS, ("on",), ("disable",))
    )
    cases.extend(
        product(
            ("filter",),
            ("plain", "guardian", "guardian-m2m"),
            ("list", "detail"),
            ("create", "update"),
            ACTORS,
            ("on",),
            ("disable",),
        )
    )
    return cases


CASES = [*_parent_cases(), *_page_cases()]


def _outcome(raw):
    resolved = cv_resolve_action(raw)
    if resolved is None:
        return "hidden"
    if resolved["cv_disabled"]:
        return f"disabled:{resolved['cv_disabled_reason']}"
    return "enabled"


def _actor(kind, parents, *, children=()):
    """Fresh actor and permission caches, with explicit model and object channels."""
    if kind in {"anonymous", "anonymous-backend"}:
        return AnonymousUser()
    user = User.objects.create_user(
        username=f"matrix_{kind}", is_active=kind != "inactive", is_superuser=kind == "superuser"
    )
    if kind in {"model", "inactive"}:
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label="app"))
    if kind == "near-only":
        user.user_permissions.add(*Permission.objects.filter(codename__in=["view_book", "view_booknote"]))
    if kind in {"direct", "group", "direct-view", "inactive", "near-change", "far-change"}:
        grantee = user
        if kind == "group":
            grantee = Group.objects.create(name="matrix_grants")
            user.groups.add(grantee)
        for index, obj in enumerate(parents):
            actions = ["view"]
            if (
                kind not in {"direct-view", "near-change", "far-change"}
                or (kind == "near-change" and index == len(parents) - 1)
                or (kind == "far-change" and index == 0)
            ):
                actions.append("change")
            for action in actions:
                assign_perm(f"{obj._meta.app_label}.{action}_{obj._meta.model_name}", grantee, obj)
        for obj in children:
            for action in ("view", "change", "delete"):
                assign_perm(f"{obj._meta.app_label}.{action}_{obj._meta.model_name}", grantee, obj)
    return User.objects.get(pk=user.pk)


def _get(actor, url):
    """An inactive request must stay signed in, rather than duplicate anonymous."""
    inactive = actor.is_authenticated and not actor.is_active
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS) if inactive else nullcontext():
        client = Client()
        if actor.is_authenticated:
            if inactive:
                client.force_login(actor, backend=ALLOW_INACTIVE)
            else:
                client.force_login(actor)
        response = client.get(url)
        if inactive:
            assert response.wsgi_request.user.is_authenticated
            assert not response.wsgi_request.user.is_active
        return response


def _target_settings(monkeypatch, target, state, mode):
    monkeypatch.setattr(target, "cv_action_enabled", classmethod(lambda cls, user, obj=None: state == "on"))
    monkeypatch.setattr(target, "cv_inaccessible_actions", mode)


def _scenario_routes(suffix, *, resource=False):
    pub = ViewSet(model=Publisher, name=f"matrix_pub{suffix}")
    book = ViewSet(model=Book, name=f"matrix_book{suffix}", parent=ParentViewSet(name=pub.name, attribute="publisher"))
    parent = pub if resource else book
    child = ViewSet(
        model=TopFile if resource else BookNote,
        name=f"matrix_leaf{suffix}",
        parent=ParentViewSet(name=parent.name, **({} if resource else {"attribute": "book"})),
        **({"resource_permissions": {"view": "app.view_s3file"}} if resource else {}),
    )
    common = {"cv_viewset": parent, "cv_context_actions": []}
    detail = type("MatrixHost", (DetailView,), common)
    card = type("MatrixCards", (CardListView,), {**common, "cv_card_actions_label_mode": "label"})
    bases = (ResourceViewMixin, ListViewPermissionRequired) if resource else (ListViewPermissionRequired,)
    target = type("MatrixLeaf", bases, {"cv_viewset": child, "cv_context_actions": []})
    return SimpleNamespace(parent=parent, child=child, detail=detail, card=card, list=target), [pub, book, child]


def _parent_control(case, family, parent, actor, monkeypatch):
    control, composition, _, key, _, state, mode = case
    target = family.child.get_view_class(key)
    _target_settings(monkeypatch, target, state, mode)
    renderer = "card" if control == "card-child" else "context"
    if composition == "plain-3":
        button, action = configure(family, key)
        view = bound(family.detail if renderer == "context" else family.card, actor, parent)
        view.kwargs = {family.parent.parent.get_pk_name(): parent.publisher_id}
        raw = (
            button.get_context(view.cv_get_view_context(object=parent))
            if renderer == "context"
            else view.cv_get_card_action_data(action, parent, actor)
        )
    else:
        raw = rendered_data(family, renderer, actor, parent, key=key)
    if control == "request":
        assert _outcome(raw) == "enabled"
        return f"page:{_get(actor, raw['cv_url']).status_code}"
    return _outcome(raw)


def _live_cell(case, request, monkeypatch, core_links):
    control, composition, page, key, kind, state, mode = case
    if page != "parent":
        return _page_cell(case, request, monkeypatch)
    parent = Publisher.objects.create(name="Matrix parent")
    if control == "navbar-child":
        with navbar_routes(lambda suffix: permission_routes(suffix, composition=composition, key=key)) as family:
            actor = _actor(kind, [parent])
            if kind == "anonymous":
                # As in test_actor_and_provider_controls: the test project disables Guardian's
                # anonymous database user, which the unrelated owner-detail item would need.
                family.bar.items = [item for item in family.bar.items if item.child]
            _target_settings(monkeypatch, family.target, state, mode)
            _, context = lazy_host(family, actor, parent)
            bar = context["cv_navbar"]
            destination = reverse(
                family.child.get_router_name(key), kwargs={family.child.parent.get_pk_name(): parent.pk}
            )
            items = bar["items"] if bar else []
            return "enabled" if any(item["url"] == destination for item in items) else "hidden"
    if composition in {"plain-3", "plain-resource"}:
        with isolated_routes(
            lambda suffix: _scenario_routes(suffix, resource=composition == "plain-resource")
        ) as family:
            if composition == "plain-3":
                parent = Book.objects.create(title="Near parent", publisher=parent)
            return _parent_control(case, family, parent, _actor(kind, [parent]), monkeypatch)
    if composition == "core-guardian":
        helper = request.getfixturevalue("helpers")
        common = {"cv_viewset": helper.cpub, "cv_context_actions": []}
        family = SimpleNamespace(
            child=helper.core_book.vs,
            detail=type("MatrixCoreHost", (DetailView,), common),
            card=type("MatrixCoreCard", (CardListView,), common),
        )
        backends = [
            *settings.AUTHENTICATION_BACKENDS,
            "tests.test1.test_link_access_matrix.AnonymousParentEditorBackend",
        ]
        with override_settings(AUTHENTICATION_BACKENDS=backends) if kind == "anonymous-backend" else nullcontext():
            return _parent_control(case, family, parent, _actor(kind, [parent]), monkeypatch)
    family = core_links if composition in {"plain", "mixed"} else request.getfixturevalue("links")
    if composition == "guardian-queryset-only":

        class QuerysetOnly(GuardianQuerysetMixin, ListViewPermissionRequired):
            cv_context_actions = []

        replace_list(family, QuerysetOnly, monkeypatch)
    return _parent_control(case, family, parent, _actor(kind, [parent]), monkeypatch)


@contextmanager
def _page_scene(composition, page, request, monkeypatch):
    """Reuse shipped/core and isolated Guardian pages; add only their missing pages."""
    publisher = Publisher.objects.create(name="Page parent")
    if composition == "guardian-3":
        family = request.getfixturevalue("helpers")
        book = Book.objects.create(title="Page middle", publisher=publisher)
        note = BookNote.objects.create(note="Page leaf", book=book)
        yield SimpleNamespace(
            vs=family.note.vs, parent=family.book.vs, sibling=None, parents=[publisher, book], obj=note
        )
        return
    if composition == "plain":
        vs = request.getfixturevalue("cv_book")
        parent, sibling = vs.parent.viewset, cv_genre
        if page == "card":
            card = type("MatrixBookCards", (CardListViewPermissionRequired,), {})
            card.cv_viewset = vs
            monkeypatch.setitem(vs._views, "card", card)
    else:
        family = request.getfixturevalue("pn")
        _strict_policy(family, monkeypatch)
        if composition == "guardian":
            vs, parent, sibling = family.book_vs, family.pub_vs, family.free_genre_vs
        else:
            vs, parent, sibling = family.genre_vs, family.sib_pub_vs, None
            # pn has the M2M list/create; the filter also needs registered detail/update targets.
            for key, base in (
                ("detail", GuardianDetailViewPermissionRequired),
                ("update", GuardianUpdateViewPermissionRequired),
            ):
                view_cls = type(f"MatrixGenre{key.title()}", (base,), {"fields": ["name"]})
                view_cls.cv_viewset = vs
                monkeypatch.setitem(vs._views, key, view_cls)
    if composition == "guardian-m2m":
        obj = Genre.objects.create(name="Page genre")
        obj.publishers.add(publisher)
    else:
        obj = Book.objects.create(title="Page book", publisher=publisher)
    routed = [parent, vs, *([sibling] if sibling else [])]
    # Register the added pages in an isolated URLconf; the original project's URL lists are cached.
    cached_urls = [(viewset, viewset.__dict__.pop("urlpatterns", None)) for viewset in routed]
    scene = SimpleNamespace(vs=vs, parent=parent, sibling=sibling, parents=[publisher], obj=obj)
    try:
        with isolated_routes(lambda suffix: (scene, routed)):
            yield scene
    finally:
        for viewset, patterns in cached_urls:
            viewset.__dict__.pop("urlpatterns", None)
            if patterns is not None:
                viewset.__dict__["urlpatterns"] = patterns


def _record_page_contexts(monkeypatch, view_cls):
    """Record the final override result and its row identity, not a nearby context action."""
    records = []
    original = view_cls.cv_get_context

    def record(self, key=None, obj=None, user=None, request=None, *, location=None):
        data = original(self, key=key, obj=obj, user=user, request=request, location=location)
        records.append((key, obj, data))
        return data

    monkeypatch.setattr(view_cls, "cv_get_context", record)
    return records


def _page_cell(case, request, monkeypatch):
    control, composition, page, target_name, kind, state, mode = case
    with _page_scene(composition, page, request, monkeypatch) as scene:
        actor = _actor(kind, scene.parents, children=[scene.obj])
        page_cls = scene.vs.get_view_class(page)
        buttons = []
        target_vs = scene.vs
        if control == "create-control":
            target_key = "create"
            action_key = "create" if target_name == "create-action" else "create_alias"
            buttons.append(ContextButton(key="create_alias", key_target="create", label_template_code="Create alias"))
        elif control == "home-button":
            action_key, target_key = "home", "list"
        elif control == "parent-button":
            target_vs = scene.parent
            target_key = target_name.removeprefix("parent-")
            action_key = "parent" if target_key == "list" else f"parent_{target_key}"
            if target_key != "list":
                buttons.append(ParentContextButton(key=action_key, key_target=target_key, label_template_code="Parent"))
        elif control == "sibling-button":
            target_vs = scene.sibling
            target_key = target_name.removeprefix("sibling-")
            action_key = f"sibling_{target_key}"
            assert not scene.vs.is_view_registered(action_key)
            buttons.append(
                SiblingContextButton(
                    key=action_key, sibling_name=target_vs.name, sibling_key=target_key, label_template_code="Sibling"
                )
            )
        else:
            action_key = target_key = target_name
        target = target_vs.get_view_class(target_key)
        _target_settings(monkeypatch, target, state, mode)
        monkeypatch.setattr(target, "cv_context_action_label_mode", "label")
        monkeypatch.setattr(page_cls, "cv_context_buttons", buttons)
        monkeypatch.setattr(
            page_cls, "cv_context_actions", [] if control in {"filter", "row-action", "card-action"} else [action_key]
        )
        monkeypatch.setattr(page_cls, "cv_list_actions", [action_key] if control == "row-action" else [], raising=False)
        if control == "card-action":
            monkeypatch.setattr(page_cls, "cv_card_actions", [CardAction(key=action_key, label="Row action")])
            monkeypatch.setattr(page_cls, "cv_card_actions_label_mode", "label")
            records = _record_card_actions(monkeypatch, page_cls)
        else:
            records = _record_page_contexts(monkeypatch, page_cls)
        kwargs = {
            vs_arg: obj.pk for vs_arg, obj in zip(reversed(scene.vs.get_parent_url_args()), scene.parents, strict=True)
        }
        if page_cls.cv_object:
            kwargs[scene.vs.pk_name] = scene.obj.pk
        response = _get(actor, reverse(scene.vs.get_router_name(page), kwargs=kwargs))
        if response.status_code != 200:
            assert not records, "a refused page must not manufacture a control"
            return f"page:{response.status_code}"
        if control == "filter":
            view = response.context["view"]
            template = Template('{% load crud_views %}{{ view|cv_context_has_permission:"' + target_key + '" }}')
            return template.render(Context({"view": view, "request": view.request}))
        matches = [
            data
            for key, obj, data in records
            if key == action_key and (control not in {"row-action", "card-action"} or obj == scene.obj)
        ]
        assert matches, f"served page did not record its {control}: {action_key}"
        outcomes = {_outcome(data) for data in matches}
        assert len(outcomes) == 1, "repeated records disagree"
        return outcomes.pop()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case,core_links",
    [pytest.param(case, "guardian" if case[1] == "mixed" else "model", id=_case_id(*case)) for case in CASES],
    indirect=["core_links"],
)
def test_link_matrix_cell(case, core_links, request, monkeypatch):
    actual = _live_cell(case, request, monkeypatch, core_links)
    assert actual == BASELINE["cells"][_case_id(*case)]


def test_link_matrix_snapshot_is_complete():
    ids = [_case_id(*case) for case in CASES]
    cells = BASELINE["cells"]
    assert len(ids) == len(set(ids)) == len(cells) == 1178
    assert set(ids) == set(cells)
    assert all(
        re.fullmatch(r"hidden|enabled|disabled:permission|disabled:state|True|False|page:[0-9]{3}", value)
        for value in cells.values()
    )
    assert set(cells.values()) >= OUTCOMES
    for composition, actor in (("plain-3", "near-only"), ("guardian-queryset-only", "no-parent-grant")):
        assert cells[_case_id("request", composition, "parent", "list", actor, "on", "disable")] == "page:403"
        for control in ("child-button", "card-child"):
            assert cells[_case_id(control, composition, "parent", "list", actor, "on", "disable")] == "enabled"
    for control in ("child-button", "card-child"):
        assert cells[_case_id(control, "core-guardian", "parent", "create", "inactive", "on", "disable")] == (
            "disabled:permission"
        )
        assert cells[_case_id(control, "core-guardian", "parent", "create", "anonymous-backend", "on", "disable")] == (
            "enabled"
        )
    for composition, page in (("guardian", "list"), ("guardian-m2m", "detail")):
        assert cells[_case_id("filter", composition, page, "create", "direct", "on", "disable")] == "False"
    for target in ("create-action", "create-alias"):
        assert cells[_case_id("create-control", "guardian", "create", target, "direct", "on", "disable")] == (
            "disabled:permission"
        )
    for page in ("list", "detail"):
        assert cells[_case_id("sibling-button", "guardian", page, "sibling-create", "direct", "on", "disable")] == (
            "disabled:permission"
        )
        for actor in ("near-change", "far-change"):
            expected = "enabled" if (actor == "near-change") == (page == "list") else "disabled:permission"
            assert (
                cells[_case_id("parent-button", "guardian-3", page, "parent-create", actor, "on", "disable")]
                == expected
            )
    families = {}
    for control, composition, page, target, actor, state, mode in _page_cases():
        family = (control, composition, page, target, state)
        families.setdefault(family, []).append(cells[_case_id(control, composition, page, target, actor, state, mode)])
    denied_families = {
        ("create-control", composition, "create", target, "off")
        for composition in ("plain", "guardian")
        for target in ("create-action", "create-alias")
    }
    for family, values in families.items():
        if family not in denied_families:
            assert any(not value.startswith("page:") for value in values), family
    for control, composition, page, target, state in denied_families:
        for actor in ACTORS:
            on = cells[_case_id(control, composition, page, target, actor, "on", "disable")]
            off = cells[_case_id(control, composition, page, target, actor, state, "disable")]
            assert off == (on if on.startswith("page:") else "page:403")
    assert any(
        cells[_case_id(control, composition, page, target, "inactive", state, mode)]
        != cells[_case_id(control, composition, page, target, "anonymous", state, mode)]
        for control, composition, page, target, actor, state, mode in _page_cases()
        if actor == "inactive"
    )


def test_stage3a_matrix_changes_are_permission_denials():
    """Verify the whole frozen before dataset, not only the listed changed cells."""
    receipt = BASELINE["stage3a"]
    changes = receipt["changes"]
    cells = BASELINE["cells"]
    assert changes
    assert changes.keys() <= cells.keys()
    for cell_id, change in changes.items():
        assert change["after"] == cells[cell_id]
        if cell_id.startswith("filter/"):
            assert (change["before"], change["after"]) == ("True", "False")
        else:
            assert change["before"] in {"enabled", "disabled:state"}
            assert change["after"] in {"hidden", "disabled:permission"}
        assert set(change["decisions"]) <= {"D-40", "D-41", "D-42", "D-43", "D-44", "D-52", "D-55"}
        assert change["decisions"] and change["reason"]
        assert change["behavior_change"] in range(1, 9)

    before = {key: value for key, value in BASELINE.items() if key != "stage3a"}
    before["cells"] = {cell_id: changes.get(cell_id, {}).get("before", outcome) for cell_id, outcome in cells.items()}
    original_sha256 = "c72c34ac59cc48281d897d3ab81292dd2d262bca6e2be0722ab51b278dfea43c"
    assert receipt["before_sha256"] == original_sha256
    assert sha256((json.dumps(before, indent=2) + "\n").encode()).hexdigest() == original_sha256
