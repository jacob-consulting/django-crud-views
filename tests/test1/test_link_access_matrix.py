"""Frozen link outcomes from the pre-refactor tree; this module never updates its snapshot."""

import json
import re
from contextlib import nullcontext
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.test import Client, override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm

from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.views import CardListView, DetailView, ListViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1 import test_guardian_child_link_visibility as child_links
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_ancestor_resources import TopFile
from tests.test1.test_authorization_matrix import ALLOW_INACTIVE, INACTIVE_BACKENDS
from tests.test1.test_guardian_child_link_visibility import bound, configure, rendered_data, replace_list
from tests.test1.test_navbar import navbar_routes
from tests.test1.test_navbar_permissions import lazy_host, permission_routes

links = child_links.links
plain_links = child_links.plain_links
core_links = child_links.core_links
helpers = ancestor_helpers.helpers

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


CASES = _parent_cases()


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
    control, composition, _, key, kind, state, mode = case
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
    assert len(ids) == len(set(ids)) == len(cells) == 544
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
