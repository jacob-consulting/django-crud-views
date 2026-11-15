"""Real GET fidelity across the complete approved family/actor cross-product.

These are rendering views, not the exploding-handler fixtures used by runner tests.
Expected HTTP statuses are independent of trace results; login redirects must name
the configured login endpoint and preserve the requested path.
"""

from itertools import product
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth import middleware as auth_middleware
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ImproperlyConfigured
from django.test import Client
from guardian.shortcuts import assign_perm

from crud_views.lib.access_trace import trace_access
from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ActionView, DetailView, DetailViewPermissionRequired, ListView
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_actors import ALLOW_INACTIVE, GUARDIAN_BACKEND
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import register

ACTORS = ("anonymous", "inactive", "no_rights", "model_permission", "object_grant", "superuser")
FAMILIES = (
    "plain",
    "core",
    "guardian_object",
    "guardian_list",
    "nested_guardian_create",
    "manage",
    "resource",
    "cascade_on",
    "cascade_off",
)
# Column order is ACTORS. Strict Guardian grants do not inherit model permissions.
EXPECTED_STATUS = {
    "plain": (200, 200, 200, 200, 200, 200),
    "core": (302, 403, 403, 200, 403, 200),
    "guardian_object": (302, 403, 403, 403, 200, 200),
    "guardian_list": (302, 403, 200, 200, 200, 200),
    "nested_guardian_create": (302, 403, 403, 403, 200, 200),
    "manage": (302, 403, 403, 403, 403, 403),
    "resource": (302, 403, 403, 200, 403, 200),
    "cascade_on": (302, 403, 403, 403, 403, 200),
    "cascade_off": (302, 403, 403, 403, 200, 200),
}
STATUS_OUTCOME = {200: "allowed", 302: "login_redirect", 403: "denied", 404: "not_found"}


class GridItem(Resource):
    key: str

    class Meta:
        pk_field = "key"

    @classmethod
    def cv_get_items(cls, request, **kwargs):
        return [cls(key="one")]


@pytest.fixture
def grid(settings, monkeypatch, db):
    settings.AUTHENTICATION_BACKENDS = [ALLOW_INACTIVE, GUARDIAN_BACKEND]
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    pub = Publisher.objects.create(name="Grid publisher")
    book = Book.objects.create(title="Grid book", publisher=pub)
    note = BookNote.objects.create(book=book, note="Grid note")

    def build(sfx):
        core = ViewSet(model=Publisher, name="gridcore" + sfx)
        register(DetailView, core, key="plain")
        register(DetailViewPermissionRequired, core, key="core")
        register(ListView, core, key="list")
        guardian = GuardianViewSet(model=Publisher, name="gridguardian" + sfx)
        register(GuardianDetailViewPermissionRequired, guardian, key="detail")
        register(GuardianListViewPermissionRequired, guardian, key="list")
        child = GuardianViewSet(
            model=Book, name="gridcreate" + sfx, parent=ParentViewSet(name=guardian.name, attribute="publisher")
        )
        register(GuardianCreateViewPermissionRequired, child, key="create", fields=["title"])
        resource = ViewSet(
            model=GridItem, name="gridresource" + sfx, resource_permissions={"view": "app.view_publisher"}
        )
        resource_base = type("GridResourceDetail", (ResourceViewMixin, DetailViewPermissionRequired), {})
        register(resource_base, resource, key="detail")
        # Mixed ancestry deliberately separates outer model rights from inner object grants.
        inner = GuardianViewSet(
            model=Book, name="gridinner" + sfx, parent=ParentViewSet(name=core.name, attribute="publisher")
        )
        register(ListView, inner, key="list")
        routed = [core, guardian, child, resource, inner]
        paths = {
            "plain": lambda: _url(core, "plain", pk=pub.pk),
            "core": lambda: _url(core, "core", pk=pub.pk),
            "guardian_object": lambda: _url(guardian, "detail", pk=pub.pk),
            "guardian_list": lambda: _url(guardian, "list"),
            "nested_guardian_create": lambda: _url(child, "create", **{guardian.name + "_pk": pub.pk}),
            "manage": lambda: _url(core, "manage"),
            "resource": lambda: _url(resource, "detail", pk="one"),
        }
        leaves = {}
        for cascade in (True, False):
            family = "cascade_on" if cascade else "cascade_off"
            leaf = GuardianViewSet(
                model=BookNote,
                name="grid" + family.replace("_", "") + sfx,
                parent=ParentViewSet(name=inner.name, attribute="book"),
                ancestor_policy=AncestorPolicy(cascade=cascade),
            )
            register(GuardianDetailViewPermissionRequired, leaf, key="detail")
            routed.append(leaf)
            leaves[family] = leaf
            paths[family] = lambda leaf=leaf: _url(
                leaf, "detail", **{core.name + "_pk": pub.pk, inner.name + "_pk": book.pk, "pk": note.pk}
            )
        return SimpleNamespace(
            paths=paths, core=core, guardian=guardian, inner=inner, leaves=leaves, resource=resource
        ), routed

    with isolated_routes(build) as routes:
        routes.pub, routes.book, routes.note = pub, book, note
        yield routes


def actor_for(kind, grid):
    if kind == "anonymous":
        return AnonymousUser()
    perms = (
        [(Publisher, "view"), (Publisher, "change"), (Book, "view"), (Book, "change"), (BookNote, "view")]
        if kind in {"model_permission", "inactive"}
        else []
    )
    user = _user("grid_" + kind, *perms, superuser=kind == "superuser")
    if kind in {"object_grant", "inactive"}:
        for permission, obj in [
            ("view_publisher", grid.pub),
            ("change_publisher", grid.pub),
            ("view_book", grid.book),
            ("view_booknote", grid.note),
        ]:
            assign_perm(permission, user, obj)
    if kind == "inactive":
        user.is_active = False
        user.save(update_fields=["is_active"])
    return user


def compare_get(path, actor, expected_status, settings):
    client = Client()
    if actor.is_authenticated:
        client.force_login(get_user_model().objects.get(pk=actor.pk), backend=ALLOW_INACTIVE)
    response = client.get(path)
    actual_actor = response.wsgi_request.user
    assert actual_actor.pk == actor.pk
    assert actual_actor.is_authenticated == actor.is_authenticated
    assert actual_actor.is_active == actor.is_active
    assert response.status_code == expected_status
    if expected_status == 302:
        destination = urlsplit(response["Location"])
        assert destination.path == urlsplit(settings.LOGIN_URL).path
        assert parse_qs(destination.query) == {"next": [path]}
    fresh = get_user_model().objects.get(pk=actor.pk) if actor.is_authenticated else AnonymousUser()
    result = trace_access(path, fresh)
    assert result.path == path
    assert result.outcome == STATUS_OUTCOME[expected_status]
    assert result.user["pk"] == (str(actor.pk) if actor.pk is not None else None)
    assert result.user["anonymous"] == actor.is_anonymous
    assert result.user["active"] == actor.is_active
    terminal = [s for s in result.steps if s.result in {"denied", "not_found", "error"}]
    if expected_status == 200:
        assert result.decided_by is None
        assert terminal == []
    else:
        assert terminal
        # A Guardian provider reports the same refusal before its owning engine gate.
        first = terminal[0]
        deciding = result.steps[result.decided_by - 1]
        assert (deciding.viewset, deciding.permission) == (first.viewset, first.permission)
        assert result.decided_by == next(s.n for s in terminal if s.kind != "object_grant")
        assert all(s.result in {"not_reached", "not_evaluated"} for s in result.steps[result.decided_by :])
    return response, result


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("actor_kind", ACTORS)
def test_real_get_fidelity_grid(grid, settings, family, actor_kind):
    actor = actor_for(actor_kind, grid)
    status = EXPECTED_STATUS[family][ACTORS.index(actor_kind)]
    response, result = compare_get(grid.paths[family](), actor, status, settings)
    untouched = {s.kind for s in result.steps if s.result == "not_reached"}
    if status != 200:
        deciding = result.steps[result.decided_by - 1]
        expected_kind = (
            "manage_gate"
            if family == "manage"
            else "own_permission"
            if family in {"core", "resource"}
            else "actor_admission"
            if actor_kind in {"anonymous", "inactive"}
            else "ancestor_gate"
            if family in {"nested_guardian_create", "cascade_on", "cascade_off"}
            else "own_permission"
        )
        assert deciding.kind == expected_kind
        if family == "manage":
            assert untouched == set()  # Manage has only its group gate, no model/action-state gate.
        else:
            assert "action_state" in untouched
        if expected_kind in {"actor_admission", "ancestor_gate"} and family != "nested_guardian_create":
            assert "own_permission" in untouched
        if family.startswith("cascade"):
            expected_parent = grid.core if family == "cascade_on" and actor_kind != "model_permission" else grid.inner
            if expected_kind == "ancestor_gate":
                assert deciding.viewset == expected_parent.name
    elif family == "plain":
        assert untouched == set()
        assert any(s.kind == "object_lookup" and s.result == "passed" for s in result.steps)
    elif family == "guardian_list":
        visible = 1 if actor_kind in {"object_grant", "superuser"} else 0
        assert len(response.context["object_list"]) == visible
        assert [s.counts for s in result.steps if s.kind == "list_filter"] == [{"total": 1, "visible": visible}]
    else:
        assert untouched == set()
        assert any(s.kind == "action_state" and s.result == "passed" for s in result.steps)
    if family == "nested_guardian_create":
        assert not any(s.kind == "own_permission" for s in result.steps)
        assert any(s.kind == "limitation" and s.result == "not_evaluated" for s in result.steps)


def test_grid_inventory_is_exact_and_unskipped(request):
    cells = [item for item in request.session.items if item.originalname == "test_real_get_fidelity_grid"]
    assert len(cells) == 54
    assert {(item.callspec.params["family"], item.callspec.params["actor_kind"]) for item in cells} == set(
        product(FAMILIES, ACTORS)
    )
    assert set(EXPECTED_STATUS) == set(FAMILIES)
    assert all(len(row) == 6 for row in EXPECTED_STATUS.values())
    assert all(not any(item.iter_markers(mark)) for item in cells for mark in ("skip", "skipif", "xfail"))


def test_manage_member_real_success(grid, settings):
    actor = actor_for("no_rights", grid)
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    _, result = compare_get(grid.paths["manage"](), actor, 200, settings)
    gates = [s for s in result.steps if s.kind == "manage_gate"]
    assert len(gates) == 1 and gates[0].how == "group_member"


def test_mixed_ancestry_both_providers_pass(grid, settings):
    actor = _user("mixed", (Publisher, "view"))
    assign_perm("view_book", actor, grid.book)
    assign_perm("view_booknote", actor, grid.note)
    _, result = compare_get(grid.paths["cascade_on"](), actor, 200, settings)
    assert [(s.provider, s.permission, s.result) for s in result.steps if s.kind == "ancestor_gate"] == [
        ("model", "app.view_publisher", "passed"),
        ("guardian", "app.view_book", "passed"),
    ]


@pytest.mark.parametrize("missing", ["ancestor", "object", "resource"])
def test_missing_lookup_matches_real_404(grid, settings, missing):
    actor = actor_for("superuser", grid)
    if missing == "ancestor":
        path = _url(
            grid.leaves["cascade_on"],
            "detail",
            **{grid.core.name + "_pk": 999999, grid.inner.name + "_pk": grid.book.pk, "pk": grid.note.pk},
        )
    elif missing == "object":
        path = _url(grid.core, "core", pk=999999)
    else:
        path = _url(grid.resource, "detail", pk="absent")
    _, result = compare_get(path, actor, 404, settings)
    assert result.steps[result.decided_by - 1].kind == ("ancestor_lookup" if missing == "ancestor" else "object_lookup")
    assert any(s.kind == "action_state" and s.result == "not_reached" for s in result.steps)


def test_configuration_error_matches_real_request(grid, settings):
    def build(sfx):
        child = ViewSet(
            model=Book, name="gridinvalid" + sfx, parent=ParentViewSet(name=grid.core.name, attribute="publisher")
        )
        register(ActionView, child, key="undeclared")
        return child, [child]

    with isolated_routes(build) as child:
        path = _url(child, "undeclared", **{grid.core.name + "_pk": grid.pub.pk, "pk": grid.book.pk})
        with pytest.raises(ImproperlyConfigured, match="actions") as actual:
            Client().get(path)
        result = trace_access(path, AnonymousUser())
        assert result.outcome == "error"
        step = result.steps[result.decided_by - 1]
        assert step.kind == "validation"
        assert step.exception == {"class": type(actual.value).__name__, "message": str(actual.value)}


def test_no_route_matches_real_404(grid):
    path = "/this-grid-route-does-not-exist/"
    assert Client().get(path).status_code == 404
    result = trace_access(path, AnonymousUser())
    assert result.outcome == "no_such_route"
    assert result.steps[result.decided_by - 1].kind == "route"


def test_actual_login_middleware_or_supported_absence(grid, settings):
    # 4.2 has no LoginRequiredMiddleware: exercise its actual absence, without a skip or fake replacement.
    installed = hasattr(auth_middleware, "LoginRequiredMiddleware")
    if installed:
        settings.MIDDLEWARE = [*settings.MIDDLEWARE, "django.contrib.auth.middleware.LoginRequiredMiddleware"]
    _, result = compare_get(grid.paths["plain"](), AnonymousUser(), 302 if installed else 200, settings)
    gates = [s for s in result.steps if s.kind == "login_middleware"]
    assert len(gates) == int(installed)
    if installed:
        assert result.steps[result.decided_by - 1] is gates[0]
        assert gates[0].source == "django.contrib.auth.middleware.LoginRequiredMiddleware.process_view"
        assert result.plan == []
    assert any("other middleware" in str(note).lower() for note in result.untraced)
