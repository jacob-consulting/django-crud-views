"""Resource hosts reuse the real forms, actor selection and command trace owner."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
from lxml import html

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    DetailView,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
)
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_ancestor_authorization import _url, isolated_routes
from tests.test1.test_manage_requirements import grant, register

pytestmark = pytest.mark.django_db
HOST_USERNAME = "resource trace developer"
SECRET = "private external payload never exposed"
WRITE_MARKER = "trace write must roll back"


class HostManageView(ManageView):
    """An explicit developer-only host for inspecting disabled stock targets."""

    def has_permission(self):
        user = self.request.user
        return user.is_authenticated and user.is_active and user.get_username() == HOST_USERNAME


@pytest.fixture
def trace_host(request, monkeypatch, django_user_model):
    kind = getattr(request, "param", "standalone")
    developer = django_user_model.objects.create_user(username=HOST_USERNAME)
    developer.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    actor = django_user_model.objects.create_user(username="<em>inspected actor</em>")
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    state = SimpleNamespace(reads=[], broken=False, write=False)

    class TraceItem(Resource):
        key: str
        secret: str

        class Meta:
            pk_field = "key"

        @classmethod
        def cv_get_items(cls, request, **kwargs):
            state.reads.append((request.user.pk, kwargs))
            if state.write:
                Publisher.objects.create(name=WRITE_MARKER)
            if state.broken:
                raise ValueError("<em>loader unavailable</em>")
            return [cls(key="one", secret=SECRET), cls(key="disabled", secret=SECRET)]

        def __str__(self):
            return explode()

        def __repr__(self):
            return explode()

    def build(sfx):
        parents, coords, objects = [], {}, []
        if kind != "standalone":
            grand = ViewSet(model=Publisher, name="tracegrand" + sfx)
            parent_cls = GuardianViewSet if kind == "guardian" else ViewSet
            parent = parent_cls(
                model=Book,
                name="traceparent" + sfx,
                parent=ParentViewSet(name=grand.name, attribute="publisher"),
            )
            publisher = Publisher.objects.create(name="private parent")
            book = Book.objects.create(title="private book", publisher=publisher)
            parents = [grand, parent]
            objects = [publisher, book]
            coords = {grand.name + "_pk": publisher.pk, parent.name + "_pk": book.pk}
        vs = ViewSet(
            model=TraceItem,
            name="traceresource" + sfx,
            parent=ParentViewSet(name=parents[-1].name) if parents else None,
            resource_permissions={"view": "app.view_author", "change": "app.change_author"},
            ancestor_policy=AncestorPolicy(
                actions={"action": AncestorPermissions(nearest="view", higher="view")} if parents else {}
            ),
        )
        for base, key in [
            (ListViewPermissionRequired, "list"),
            (DetailViewPermissionRequired, "detail"),
            (ActionViewPermissionRequired, "action"),
            (DetailView, "public"),
        ]:
            combined = type("TraceResource" + key.title(), (ResourceViewMixin, base), {"__module__": __name__})
            register(
                combined,
                vs,
                key=key,
                get=explode,
                post=explode,
                cv_action=explode,
                cv_action_enabled=classmethod(lambda cls, user, obj: getattr(obj, "key", None) != "disabled"),
            )
        register(
            type("ContributedResource", (ResourceViewMixin, DetailViewPermissionRequired), {"__module__": __name__}),
            vs,
            key="extra",
            get=explode,
            cv_path_contribute=classmethod(lambda cls: "(?P<extra>[a-z]+)/"),
        )
        fallback = ViewSet(
            model=Publisher,
            name="tracehost" + sfx,
            manage_view_class="tests.test1.test_resource_manage_trace.HostManageView",
        )
        return SimpleNamespace(vs=vs, fallback=fallback, parents=parents, objects=objects, coords=coords), [
            *parents,
            vs,
            fallback,
        ]

    with isolated_routes(build) as env:
        env.developer, env.actor, env.resource, env.state, env.kind = developer, actor, TraceItem, state, kind
        for user in (developer, actor):
            for parent, obj in zip(env.parents, env.objects, strict=True):
                grant(user, parent, "view")
                if isinstance(parent, GuardianViewSet):
                    assign_perm(parent.permissions["view"], user, obj)
        grant(actor, env.vs, "view")
        grant(actor, env.vs, "change")
        yield env


def submit(client, env, mode="viewset", *, host_path=None, **params):
    client.force_login(env.developer)
    response = client.get(
        host_path or _url(env.vs, "manage", **env.coords),
        {
            "cv_access_mode": mode,
            "cv_access_user": env.actor.username,
            **params,
        },
    )
    assert response.status_code == 200
    assert response.wsgi_request.user.pk == env.developer.pk
    assert int(client.session["_auth_user_id"]) == env.developer.pk
    return response


@pytest.mark.parametrize("mode", ["path", "viewset"])
def test_resource_manage_trace_inputs_default_off(client, trace_host, monkeypatch, mode):
    env = trace_host
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", False)
    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", explode)
    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", explode)
    monkeypatch.setattr(env.resource, "cv_get_items", explode)
    monkeypatch.setattr(env.resource, "cv_get_item", explode)
    response = submit(client, env, mode, cv_access_user="<bad>", cv_access_pk="one", cv_access_path="http://[")
    assert response.context["manage_access_trace"] is None
    assert response.context["manage_permissions"]["actor"]["id"] == env.developer.pk
    assert not html.fromstring(response.content).cssselect("#cv-manage-access-trace")


@pytest.mark.parametrize("trace_host", ["standalone", "core", "guardian"], indirect=True)
@pytest.mark.parametrize("pk", ["", "one", "missing", "disabled"])
def test_resource_manage_trace_inputs(client, trace_host, pk):
    env = trace_host
    response = submit(client, env, cv_access_pk=pk, **dict.fromkeys(env.coords, "99999"), extra="ignored")
    data = response.context["manage_access_trace"]
    assert [row["key"] for row in data["rows"]] == list(env.vs.get_all_views())
    rows = {row["key"]: row for row in data["rows"]}
    assert rows["list"]["trace"]["outcome"] == "allowed", [
        s["exception"] for s in rows["list"]["trace"]["steps"] if s["exception"]
    ]
    assert rows["list"]["path"] == _url(env.vs, "list", **env.coords)
    for key in ("detail", "action", "public"):
        if not pk:
            assert rows[key]["instruction"] == "needs an object pk" and rows[key]["trace"] is None
        else:
            assert rows[key]["path"] == _url(env.vs, key, **env.coords, pk=pk)
            expected = (
                "not_found" if pk == "missing" else "denied" if pk == "disabled" and key != "public" else "allowed"
            )
            assert rows[key]["trace"]["outcome"] == expected, rows[key]["trace"]
    assert rows["extra"]["instruction"] == ("use the path field" if pk else "needs an object pk")
    assert rows["extra"]["trace"] is None
    assert env.state.reads and all(actor == env.actor.pk for actor, _ in env.state.reads)
    assert all(coords == {k: str(v) for k, v in env.coords.items()} for _, coords in env.state.reads)
    assert SECRET not in response.content.decode()


@pytest.mark.parametrize("mode", ["path", "viewset"])
@pytest.mark.parametrize("selector", ["username", "pk", "collision", "unknown", "malformed"])
def test_resource_manage_trace_actor(client, trace_host, django_user_model, mode, selector):
    env = trace_host
    selected = env.actor
    identifier = selected.username
    if selector in {"pk", "collision"}:
        identifier = str(selected.pk)
    if selector == "collision":
        selected = django_user_model.objects.create_user(username=identifier)
    elif selector in {"unknown", "malformed"}:
        identifier = "999999999" if selector == "unknown" else "<em>missing actor</em>"
    before = submit(client, env, "path", cv_access_path=_url(env.vs, "list", **env.coords))
    response = submit(client, env, mode, cv_access_user=identifier, cv_access_path=_url(env.vs, "list", **env.coords))
    data = response.context["manage_access_trace"]
    matrix = response.context["manage_permissions"]
    if selector in {"unknown", "malformed"}:
        assert data["error"] and data["actor"] is None and data["rows"] == [] and data["trace"] is None
        assert matrix["actor"]["id"] == env.developer.pk
    else:
        assert data["actor"]["pk"] == str(selected.pk)
        assert matrix["actor"]["id"] == (selected.pk if mode == "viewset" else env.developer.pk)
        if mode == "path":
            assert data["trace"]["user"]["pk"] == str(selected.pk)
    assert {k: v for k, v in matrix.items() if k != "actor"} == {
        k: v for k, v in before.context["manage_permissions"].items() if k != "actor"
    }
    assert not html.fromstring(response.content).cssselect("#cv-manage-access-trace em")


@pytest.mark.parametrize(
    "mode,user,path",
    [
        ("bad", "actor", "/"),
        ("path", "", "/"),
        ("path", "actor", ""),
        ("path", "actor", "http://["),
    ],
)
def test_resource_manage_trace_inputs_invalid(client, trace_host, monkeypatch, mode, user, path):
    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", explode)
    response = submit(client, trace_host, mode, cv_access_user=user, cv_access_path=path)
    data = response.context["manage_access_trace"]
    assert data["error"] and data["actor"] is None and not data["rows"] and data["trace"] is None
    assert not trace_host.state.reads
