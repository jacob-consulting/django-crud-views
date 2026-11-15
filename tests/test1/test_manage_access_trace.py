"""Opt-in diagnostics preserve the hosting viewer and use a separate trace actor."""

import json

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from lxml import html

from crud_views.lib.access_trace import AccessStep, AccessTrace
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views.manage import ManageView

pytestmark = pytest.mark.django_db


@pytest.fixture
def developer(django_user_model):
    user = django_user_model.objects.create_user(username="diagnostic developer")
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


@pytest.fixture(params=["cv_author", "cv_guardian_author"])
def host(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setitem(crud_views_settings.__dict__, "manage_access_trace", True)


def submit(client, host, user, **params):
    client.force_login(user)
    return client.get(reverse(host.get_router_name("manage")), params)


def test_setting_and_disabled_no_work(client, host, developer, monkeypatch):
    assert "manage_access_trace" in CrudViewsSettings.model_fields
    assert CrudViewsSettings.model_fields["manage_access_trace"].default is False

    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled tracing must not interpret or resolve query inputs")

    monkeypatch.setattr(ManageView, "get_manage_access_trace", forbidden, raising=False)
    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", forbidden, raising=False)
    response = submit(client, host, developer, cv_access_mode="path", cv_access_user="<bad>", cv_access_path="//bad")
    assert response.status_code == 200
    assert response.context["manage_access_trace"] is None
    assert not html.fromstring(response.content).cssselect("#cv-manage-access-trace")


def test_path_runs_under_actor_not_viewer(client, host, developer, django_user_model, enabled):
    actor = django_user_model.objects.create_user(username="<script>actor</script>")
    response = submit(
        client, host, developer, cv_access_mode="path", cv_access_user=actor.username, cv_access_path="/author/manage/"
    )
    assert response.status_code == 200
    result = response.context["manage_access_trace"]
    assert result["trace"]["outcome"] == "denied"
    assert result["actor"]["pk"] == str(actor.pk)
    assert result["trace"]["user"]["pk"] == str(actor.pk)
    assert response.wsgi_request.user.pk == developer.pk
    assert response.context["manage_permissions"]["actor"]["id"] == developer.pk
    assert int(client.session["_auth_user_id"]) == developer.pk
    assert "<script>actor</script>" not in response.content.decode()
    assert "&lt;script&gt;actor&lt;/script&gt;" in response.content.decode()
    card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
    assert "denied" in card.text_content()
    assert "other middleware and URL decorators are not traced" in card.text_content()


@pytest.mark.parametrize(
    "params",
    [
        {"cv_access_mode": "path", "cv_access_user": "<script>unknown</script>", "cv_access_path": "/author/"},
        {"cv_access_mode": "path", "cv_access_user": "", "cv_access_path": "/author/"},
        {"cv_access_mode": "bad", "cv_access_user": "diagnostic developer"},
        {"cv_access_mode": "path", "cv_access_user": "diagnostic developer", "cv_access_path": ""},
    ],
)
def test_invalid_query_feedback_without_trace(client, host, developer, enabled, monkeypatch, params):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid form must not trace")

    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", forbidden, raising=False)
    response = submit(client, host, developer, **params)
    result = response.context["manage_access_trace"]
    assert result["error"] and result["trace"] is None and result["rows"] == []
    assert response.context["manage_permissions"]["actor"]["id"] == developer.pk
    assert "<script>unknown</script>" not in response.content.decode()


def test_host_gate_cannot_be_bypassed(client, host, developer, django_user_model, enabled, monkeypatch):
    outsider = django_user_model.objects.create_user(username="outside", is_superuser=True, is_staff=True)

    def forbidden(*args, **kwargs):
        raise AssertionError("Host gate must run before diagnostic input")

    monkeypatch.setattr("crud_views.lib.views.manage.resolve_trace_user", forbidden, raising=False)
    assert (
        submit(
            client,
            host,
            outsider,
            cv_access_mode="path",
            cv_access_user=developer.username,
            cv_access_path="/author/manage/",
        ).status_code
        == 403
    )


def test_explicit_builder_has_no_request_dependency(host, developer, monkeypatch):
    assert callable(getattr(ManageView, "get_manage_access_trace", None))

    def forbidden(self):
        raise AssertionError("Explicit builder must not read request")

    monkeypatch.setattr(ManageView, "request", property(forbidden), raising=False)
    result = host.get_view_class("manage")().get_manage_access_trace(host, developer, mode="path", path="/missing/")
    assert result["trace"]["outcome"] == "no_such_route"


def test_scalar_trace_errors_are_escaped(client, host, developer, enabled, monkeypatch):
    payload = "<script>alert('private')</script>"
    trace = AccessTrace(
        path=payload,
        view=payload,
        route=payload,
        outcome="error",
        decided_by=1,
        steps=[AccessStep(1, "custom_gate", result="error", exception={"class": "ValueError", "message": payload})],
    )
    monkeypatch.setattr("crud_views.lib.views.manage.trace_access", lambda *args: trace, raising=False)
    response = submit(
        client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path="/anything/"
    )
    assert payload not in response.content.decode()
    assert "&lt;script&gt;" in response.content.decode()
    assert "ValueError" in response.content.decode()
    assert "traceback" not in json.dumps(response.context["manage_access_trace"])


@pytest.mark.parametrize("kind", ["core", "guardian"])
def test_target_ancestor_is_actor_gate_but_host_ancestor_is_viewer_gate(
    client, developer, django_user_model, enabled, kind
):
    from crud_views.lib.views import DetailViewPermissionRequired
    from crud_views.lib.viewset import ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Publisher
    from tests.test1.test_ancestor_authorization import _url, isolated_routes
    from tests.test1.test_manage_requirements import grant, register

    def build(sfx):
        parent = ViewSet(model=Publisher, name="traceparent" + sfx)
        cls = GuardianViewSet if kind == "guardian" else ViewSet
        child = cls(model=Book, name="tracechild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher"))
        register(GuardianDetailViewPermissionRequired if kind == "guardian" else DetailViewPermissionRequired, child)
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        publisher = Publisher.objects.create(name="secret parent")
        obj = Book.objects.create(title="secret book", publisher=publisher)
        actor = django_user_model.objects.create_user(username="business actor", is_superuser=True)
        target = _url(child, "tested", **{child.parent.get_pk_name(): publisher.pk, child.pk_name: obj.pk})
        client.force_login(developer)
        response = client.get(
            "/author/manage/", {"cv_access_mode": "path", "cv_access_user": actor.username, "cv_access_path": target}
        )
        assert response.status_code == 200
        assert response.context["manage_access_trace"]["trace"]["outcome"] == "allowed"
        card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()
        assert "secret book" not in card and "secret parent" not in card
        hosting = _url(child, "manage", **{child.parent.get_pk_name(): publisher.pk})
        params = {"cv_access_mode": "path", "cv_access_user": actor.username, "cv_access_path": target}
        assert client.get(hosting, params).status_code == 403
        grant(developer, parent, "view")
        assert client.get(hosting, params).status_code == 200
        developer.groups.clear()
        assert client.get(hosting, params).status_code == 403


@pytest.mark.parametrize("mode", ["path", "viewset"])
@pytest.mark.parametrize("selector", ["username", "pk", "collision", "unknown", "invalid_pk"])
def test_both_forms_share_username_first_selection(client, host, developer, django_user_model, enabled, mode, selector):
    actor = django_user_model.objects.create_user(username="nonnumeric actor")
    identifier = actor.username
    if selector in {"pk", "collision"}:
        identifier = str(actor.pk)
    if selector == "collision":
        actor = django_user_model.objects.create_user(username=identifier)
    elif selector == "unknown":
        identifier = "987654321"
    elif selector == "invalid_pk":
        identifier = "not-a-valid-pk"
    response = submit(client, host, developer, cv_access_mode=mode, cv_access_user=identifier,
                      cv_access_path="/author/manage/")
    data = response.context["manage_access_trace"]
    assert data["user_input"] == identifier
    if selector in {"unknown", "invalid_pk"}:
        assert data["error"] and data["actor"] is None and not data["rows"] and data["trace"] is None
    else:
        assert data["actor"]["pk"] == str(actor.pk) and not data["error"]
        if mode == "viewset":
            assert response.context["manage_permissions"]["actor"]["id"] == actor.pk
            assert [row["key"] for row in data["rows"]] == list(host.get_all_views())
        else:
            assert data["trace"]["user"]["pk"] == str(actor.pk)


@pytest.mark.parametrize("empty_matrix", [False, True])
@pytest.mark.parametrize("state", ["other", "self", "disabled", "empty", "invalid", "unknown", "path"])
def test_only_successful_viewset_selection_changes_actor_label(
    client, host, developer, django_user_model, enabled, monkeypatch, empty_matrix, state
):
    from crud_views.lib.viewset import ViewSet

    actor = django_user_model.objects.create_user(username="selected actor")
    if empty_matrix:
        monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {}))
    before = submit(client, host, developer).context["manage_permissions"]
    selected = actor if state == "other" else developer
    params = {"cv_access_mode": "viewset", "cv_access_user": selected.username}
    if state == "disabled":
        monkeypatch.setitem(crud_views_settings.__dict__, "manage_access_trace", False)
    elif state == "empty":
        params = {}
    elif state == "invalid":
        params["cv_access_mode"] = "invalid"
    elif state == "unknown":
        params["cv_access_user"] = "missing actor"
    elif state == "path":
        params.update(cv_access_mode="path", cv_access_path="/author/manage/")
    response = submit(client, host, developer, **params)
    checked = state in {"self", "other"}
    matrix = response.context["manage_permissions"]
    assert matrix["actor"]["id"] == (selected.pk if checked else developer.pk)
    assert {k: v for k, v in matrix.items() if k != "actor"} == {k: v for k, v in before.items() if k != "actor"}
    label = html.fromstring(response.content).cssselect("[data-manage-actor]")[0].text_content()
    assert ("(checked below)" in label) is checked
    assert ("(you)" in label) is not checked
    assert response.wsgi_request.user.pk == developer.pk


@pytest.mark.parametrize("object_pk", [None, "valid", "invalid"])
def test_route_inventory_and_own_pk_boundaries(host, developer, object_pk):
    obj = host.model.objects.create(name="not rendered")
    pk = str(obj.pk) if object_pk == "valid" else "not-a-pk" if object_pk else None
    data = host.get_view_class("manage")().get_manage_access_trace(host, developer, mode="viewset", object_pk=pk)
    assert [r["key"] for r in data["rows"]] == list(host.get_all_views())
    rows = {row["key"]: row for row in data["rows"]}
    for key in ("detail", "update", "delete"):
        row = rows[key]
        if object_pk is None:
            assert row["instruction"] == "needs an object pk" and row["trace"] is None
        elif object_pk == "invalid":
            assert row["instruction"] == "use the path field" and row["trace"] is None
        else:
            assert row["path"] == reverse(host.get_router_name(key), kwargs={host.pk_name: pk})
            assert row["trace"] and not row["instruction"]
    for key in ("list", "create", "manage"):
        assert rows[key]["path"] == reverse(host.get_router_name(key))
        assert rows[key]["trace"] and not rows[key]["instruction"]


def test_nested_parent_coordinates_and_extra_routes(client, developer, enabled):
    from crud_views.lib.views import CreateView, DetailView, ListView
    from crud_views.lib.views.child import RedirectChildView
    from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
    from crud_views_polymorphic.lib.create import PolymorphicCreateView
    from tests.test1.app.models import Book, BookNote, Publisher
    from tests.test1.test_ancestor_authorization import _url, isolated_routes
    from tests.test1.test_manage_requirements import register

    def build(sfx):
        grand = ViewSet(model=Publisher, name="acgrand" + sfx, ancestor_policy=AncestorPolicy(provider="none"))
        parent = ViewSet(model=Book, name="acparent" + sfx, ancestor_policy=AncestorPolicy(provider="none"),
                         parent=ParentViewSet(name=grand.name, attribute="publisher"))
        leaf = ViewSet(model=BookNote, name="acleaf" + sfx, pk_name="note_id",
                       parent=ParentViewSet(name=parent.name, attribute="book"))
        for base, key in [(ListView, "list"), (CreateView, "create"), (DetailView, "detail"),
                          (RedirectChildView, "redirect_child"), (PolymorphicCreateView, "polymorphic")]:
            register(base, leaf, key=key)
        register(CreateView, leaf, key="post_only", http_method_names=["post"], cv_backend_only=True)
        register(CreateView, leaf, key="custom", cv_path_contribute=classmethod(lambda cls: "(?P<extra>[a-z]+)/"))
        return (grand, parent, leaf), [grand, parent, leaf]

    with isolated_routes(build) as (grand, parent, leaf):
        pub = Publisher.objects.create(name="hidden publisher")
        book = Book.objects.create(title="hidden book", publisher=pub)
        note = BookNote.objects.create(note="hidden note", book=book)
        coords = {parent.parent.get_pk_name(): pub.pk, leaf.parent.get_pk_name(): book.pk}
        client.force_login(developer)
        response = client.get(_url(leaf, "manage", **coords), {
            "cv_access_mode": "viewset", "cv_access_user": developer.username, "cv_access_pk": note.pk,
            **{k: "987654" for k in coords}, "extra": "tampered", "polymorphic_ctype_id": "1",
            "redirect": "bad", "redirect_key": "bad",
        })
        assert response.status_code == 200
        data = response.context["manage_access_trace"]
        assert [r["key"] for r in data["rows"]] == list(leaf.get_all_views())
        rows = {r["key"]: r for r in data["rows"]}
        assert rows["detail"]["path"] == _url(leaf, "detail", **coords, note_id=note.pk)
        assert rows["list"]["path"] == _url(leaf, "list", **coords)
        for key in ("redirect_child", "polymorphic", "custom"):
            assert rows[key]["instruction"] == "use the path field" and rows[key]["trace"] is None
        assert rows["post_only"]["trace"]
        assert any(step["result"] == "not_evaluated" for step in rows["post_only"]["trace"]["steps"])
        assert "hidden note" not in html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0].text_content()
