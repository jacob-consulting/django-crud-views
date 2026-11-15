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
