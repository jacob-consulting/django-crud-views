"""Resource hosts reuse the real forms, actor selection and command trace owner."""

import json
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission
from django.utils import translation
from guardian.shortcuts import assign_perm, remove_perm
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
from tests.test1.test_access_trace_command import invoke
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
    session_key, session_data = client.session.session_key, dict(client.session)
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
    assert client.session.session_key == session_key and dict(client.session) == session_data
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


def test_resource_manage_trace_inputs_enabled_idle(client, trace_host, monkeypatch):
    env = trace_host
    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", explode)
    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", explode)
    monkeypatch.setattr(env.resource, "cv_get_items", explode)
    monkeypatch.setattr(env.resource, "cv_get_item", explode)
    client.force_login(env.developer)
    response = client.get(_url(env.vs, "manage"), {"cv_access_user": env.actor.username, "cv_access_pk": "one"})
    assert response.status_code == 200
    data = response.context["manage_access_trace"]
    assert data["actor"] is None and data["trace"] is None and data["rows"] == []


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


EXIT_CODES = {"allowed": 0, "denied": 1, "not_found": 1, "login_redirect": 1, "no_such_route": 2, "error": 2}
LIMITS = [
    "other middleware and URL decorators are not traced",
    "the synthetic request uses http://localhost; host-dependent project rules are not reproduced",
]
HANDLER_LIMIT = "Allowed means this user may open the page; handler-phase checks are not evaluated."
ACTION_LIMIT = (
    "Authorization uses a synthetic GET stub; the POST handler and method-sensitive behavior are not evaluated."
)


def assert_facts(facts, text):
    """Check diagnostic values, independently of the shared presentation helpers."""
    for field in ("viewset", "key", "permission", "group", "provider", "source", "how", "message"):
        if facts.get(field):
            assert str(facts[field]) in text, (field, facts[field], text)
    if facts.get("object"):
        assert set(facts["object"]) == {"model", "pk"}
        assert facts["object"]["model"] in text and facts["object"]["pk"] in text
    if facts.get("exception"):
        for value in facts["exception"].values():
            assert value in text
    if facts.get("counts"):
        counts = facts["counts"]
        if counts["total"] is None:
            count = counts["visible"]
            expected = translation.ngettext("%(count)s row", "%(count)s rows", count) % {"count": count}
        else:
            expected = translation.gettext("sees %(visible)s of %(total)s objects") % counts
        assert expected in text


def assert_parity(env, response, *, expected):
    """Compare every executable row, not a representative sample or selected JSON fields."""
    data = response.context["manage_access_trace"]
    rows = (
        data["rows"]
        if data["mode"] == "viewset"
        else [{"key": "path", "path": data["path_input"], "trace": data["trace"]}]
    )
    panels = iter(html.fromstring(response.content).cssselect("[data-cv-access-trace]"))
    executed = 0
    for row in rows:
        if row["trace"] is None:
            assert row["instruction"] in [
                translation.gettext("needs an object pk"),
                translation.gettext("use the path field"),
            ]
            assert row["instruction"] in html.fromstring(response.content).text_content()
            continue
        executed += 1
        trace = row["trace"]
        assert trace["outcome"] == expected[row["key"]], trace
        before_reads = len(env.state.reads)
        code, stdout, stderr = invoke(row["path"], env.actor.username, "--as-json", "--no-color")
        assert code == EXIT_CODES[expected[row["key"]]] and stderr == ""
        assert json.loads(stdout) == trace
        assert trace["version"] == 1
        assert all(step["provider"] != "resource" for step in trace["steps"])
        for step in trace["steps"]:
            if step["kind"] == "own_permission" and step["result"] != "not_reached":
                assert step["provider"] == "core"
            if step["kind"] == "manage_gate" and step["result"] != "not_reached":
                assert step["provider"] == "none"
            if step["kind"] == "list_filter":
                assert step["counts"] == {"visible": 2, "total": None}
        if env.state.write:
            assert len(env.state.reads) > before_reads or row["key"] == "manage"
            assert not Publisher.objects.filter(name=WRITE_MARKER).exists()
        code, text, stderr = invoke(row["path"], env.actor.username, "--no-color")
        assert code == EXIT_CODES[expected[row["key"]]]
        panel = next(panels)
        rendered = panel.text_content()
        assert (
            panel.cssselect("[data-cv-trace-outcome] [data-cv-trace-result]")[0].get("data-cv-trace-result")
            == trace["outcome"]
        )
        if trace["outcome"] == "no_such_route":
            assert not text and row["path"] in stderr and len(stderr.splitlines()) == 1
        else:
            assert not stderr
            assert trace["path"] in text and trace["path"] in rendered
            assert trace["user"]["username"] in text and trace["user"]["username"] in rendered
            if trace["decided_by"] is not None:
                assert translation.gettext("decided at step %(number)s") % {"number": trace["decided_by"]} in rendered
                assert (
                    translation.gettext("%(outcome)s at step %(number)s.").split("%(outcome)s")[-1]
                    % {"number": trace["decided_by"]}
                    in text
                )
            for fact in trace["plan"]:
                assert_facts(fact, text)
                assert_facts(fact, rendered)
            step_nodes = panel.xpath("./ol/li")
            assert [int(node.get("value")) for node in step_nodes] == [step["n"] for step in trace["steps"]]
            for step, node in zip(trace["steps"], step_nodes, strict=True):
                line = next(line for line in text.splitlines() if line.startswith(f"{step['n']}. "))
                assert_facts(step, line)
                assert_facts(step, node.text_content())
                assert node.cssselect("[data-cv-trace-result]")[0].get("data-cv-trace-result") == step["result"]
            for notice in [*LIMITS, *([HANDLER_LIMIT] if trace["outcome"] == "allowed" else [])]:
                translated = translation.gettext(notice)
                assert translated in trace["untraced"] and translated in text and translated in rendered
            if row["key"] == "action" or "/action/" in row["path"]:
                translated = translation.gettext(ACTION_LIMIT)
                assert any(step["kind"] == "limitation" and step["message"] == translated for step in trace["steps"])
                assert translated in text and translated in rendered
        assert SECRET not in stdout + text + stderr + response.content.decode()
        assert not panel.cssselect("em, script")
        if env.state.write:
            assert not Publisher.objects.filter(name=WRITE_MARKER).exists()
    assert executed and next(panels, None) is None


@pytest.mark.parametrize("trace_host", ["standalone", "core", "guardian"], indirect=True)
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("mode", ["path", "viewset"])
@pytest.mark.parametrize("case", ["direct", "group", "denied", "missing", "disabled", "error", "rollback", "no_pk"])
def test_resource_manage_trace_parity(client, trace_host, language, mode, case):
    env = trace_host
    if case in {"group", "denied"}:
        permissions = Permission.objects.filter(
            codename__in=["view_author", "change_author"], content_type__app_label="app"
        )
        env.actor.user_permissions.remove(*permissions)
        if case == "group":
            group = Group.objects.create(name="mapped Resource group")
            group.permissions.add(*permissions)
            env.actor.groups.add(group)
    env.state.broken = case == "error"
    env.state.write = case == "rollback"
    pk = case if case in {"missing", "disabled"} else "" if case == "no_pk" else "one"
    path = _url(env.vs, "detail", **env.coords, pk=pk) if pk else _url(env.vs, "list", **env.coords)
    with translation.override(language):
        response = submit(client, env, mode, cv_access_pk=pk, cv_access_path=path)
        assert not Publisher.objects.filter(name=WRITE_MARKER).exists()
        outcome = {"denied": "denied", "missing": "not_found", "disabled": "denied", "error": "error"}.get(
            case, "allowed"
        )
        expected = (
            {"path": outcome}
            if mode == "path"
            else {
                "manage": "denied",
                "list": "denied" if case == "denied" else "error" if case == "error" else "allowed",
                "detail": outcome,
                "action": outcome,
                "public": "not_found" if case == "missing" else "error" if case == "error" else "allowed",
            }
        )
        assert_parity(env, response, expected=expected)
        traces = (
            [row["trace"] for row in response.context["manage_access_trace"]["rows"] if row["trace"]]
            if mode == "viewset"
            else [response.context["manage_access_trace"]["trace"]]
        )
        if case in {"direct", "group", "rollback"}:
            assert any(
                step["object"] == {"model": "resources.traceitem", "pk": "one"}
                for trace in traces
                for step in trace["steps"]
            )
        if case == "denied":
            assert any(
                step["kind"] == "own_permission"
                and step["result"] == "denied"
                and step["permission"] == "app.view_author"
                for trace in traces
                for step in trace["steps"]
            )
        if case == "error":
            assert any(
                step["exception"] == {"class": "ValueError", "message": "<em>loader unavailable</em>"}
                for trace in traces
                for step in trace["steps"]
            )
            assert "&lt;em&gt;loader unavailable&lt;/em&gt;" in response.content.decode()
        if case == "rollback":
            assert env.state.reads, "external reads remain observable despite database rollback"


@pytest.mark.parametrize("trace_host", ["standalone", "core", "guardian"], indirect=True)
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize(
    "case", ["member", "nonmember", "inactive", "disabled", "debug_on", "debug_off", "extra", "no_route"]
)
def test_resource_manage_trace_parity_targets(client, trace_host, monkeypatch, settings, language, case):
    env = trace_host
    if case != "nonmember":
        env.actor.groups.add(Group.objects.get(name=crud_views_settings.manage_group))
    if case == "inactive":
        env.actor.is_active = False
        env.actor.save(update_fields=["is_active"])
    monkeypatch.setattr(
        crud_views_settings,
        "manage_views_enabled",
        "no" if case == "disabled" else "debug_only" if case.startswith("debug_") else "yes",
    )
    settings.DEBUG = case == "debug_on"
    path = _url(env.vs, "manage", **env.coords)
    if case == "extra":
        path = _url(env.vs, "extra", **env.coords, pk="one", extra="provided")
    elif case == "no_route":
        path = "/absent-resource-route/"
    expected = (
        "no_such_route"
        if case == "no_route"
        else "denied"
        if case in {"nonmember", "inactive", "disabled", "debug_off"}
        else "allowed"
    )
    with translation.override(language):
        response = submit(client, env, "path", host_path=_url(env.fallback, "manage"), cv_access_path=path)
        assert_parity(env, response, expected={"path": expected})
        trace = response.context["manage_access_trace"]["trace"]
        if case not in {"extra", "no_route"}:
            assert not env.state.reads
            if case != "inactive":
                assert any(
                    step["kind"] == "manage_gate"
                    and step["result"] == ("passed" if expected == "allowed" else "denied")
                    for step in trace["steps"]
                )
        if case == "extra":
            assert env.state.reads and all(coords["extra"] == "provided" for _, coords in env.state.reads)


@pytest.mark.parametrize("trace_host", ["core", "guardian"], indirect=True)
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("target", ["manage", "detail"])
@pytest.mark.parametrize("case", ["missing", "denied", "denied_nearest", "mismatch"])
def test_resource_manage_trace_parity_ancestors(client, trace_host, language, target, case):
    env = trace_host
    env.actor.groups.add(Group.objects.get(name=crud_views_settings.manage_group))
    coords = dict(env.coords)
    if case == "missing":
        coords[env.parents[0].name + "_pk"] = 999999
    elif case == "denied":
        permission = Permission.objects.get(content_type__app_label="app", codename="view_publisher")
        env.actor.user_permissions.remove(permission)
    elif case == "denied_nearest":
        permission = Permission.objects.get(content_type__app_label="app", codename="view_book")
        env.actor.user_permissions.remove(permission)
        if env.kind == "guardian":
            remove_perm("app.view_book", env.actor, env.objects[-1])
    else:
        other = Publisher.objects.create(name="other outer parent")
        coords[env.parents[0].name + "_pk"] = other.pk
    if target == "detail":
        coords["pk"] = "one"
    with translation.override(language):
        response = submit(client, env, "path", cv_access_path=_url(env.vs, target, **coords))
        expected = "denied" if case.startswith("denied") else "not_found"
        assert_parity(env, response, expected={"path": expected})
        trace = response.context["manage_access_trace"]["trace"]
        deciding = next(step for step in trace["steps"] if step["n"] == trace["decided_by"])
        assert deciding["kind"] == ("ancestor_gate" if case.startswith("denied") else "ancestor_lookup")
        assert not env.state.reads


def test_resource_manage_trace_parity_omits_middleware(client, trace_host, monkeypatch):
    from django.contrib.sessions.middleware import SessionMiddleware

    calls = []
    original = SessionMiddleware.process_request

    def record(self, request):
        calls.append(request.path)
        return original(self, request)

    monkeypatch.setattr(SessionMiddleware, "process_request", record)
    env = trace_host
    path = _url(env.vs, "detail", pk="one")
    response = submit(client, env, "path", cv_access_path=path)
    assert calls == [_url(env.vs, "manage")]
    assert_parity(env, response, expected={"path": "allowed"})
    assert calls == [_url(env.vs, "manage")], "UI and CLI traces do not replay the normal middleware stack"


def test_resource_manage_trace_parity_fallback_host_remains_protected(client, trace_host, monkeypatch):
    env = trace_host
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", explode)
    client.force_login(env.actor)
    response = client.get(
        _url(env.fallback, "manage"),
        {
            "cv_access_mode": "path",
            "cv_access_user": env.developer.username,
            "cv_access_path": _url(env.vs, "manage"),
        },
    )
    assert response.status_code == 403
    assert not env.state.reads
