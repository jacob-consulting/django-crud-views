"""Manage traces observe the configured group gate without broadening admission."""

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.test import RequestFactory

from crud_views.lib.access_trace import AccessRecorder, recording, trace_access
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from tests.test1 import test_access_trace_ancestors as ancestors
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_access_trace_ancestors import chain, coordinates
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import register

rows = ancestors.rows


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["yes", "no", "debug_only"])
@pytest.mark.parametrize("debug", [False, True])
@pytest.mark.parametrize("actor", ["anonymous", "inactive", "member", "nonmember", "superuser"])
def test_manage_trace_actual_branch(mode, debug, actor, monkeypatch, settings):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    monkeypatch.setattr(crud_views_settings, "manage_group", "Project developers")
    settings.DEBUG = debug

    def build(sfx):
        vs = ViewSet(model=Publisher, name="tracemanage" + sfx)
        register(ManageView, vs, get=explode)
        return vs, [vs]

    user = AnonymousUser() if actor == "anonymous" else _user("manage actor", superuser=actor == "superuser")
    if actor == "inactive":
        user.is_active = False
        user.save()
    if actor in {"inactive", "member"}:
        user.groups.add(Group.objects.create(name="Project developers"))
    with isolated_routes(build) as vs:
        result = trace_access(_url(vs, "tested"), user)
    allowed = actor == "member" and (mode == "yes" or (mode == "debug_only" and debug))
    assert result.outcome == ("allowed" if allowed else "login_redirect" if actor == "anonymous" else "denied")
    gates = [s for s in result.steps if s.kind == "manage_gate" and s.result != "not_reached"]
    assert len(gates) == 1
    gate = gates[0]
    assert gate.group == "Project developers"
    assert gate.provider == "none"
    assert mode in gate.message
    assert gate.result == ("passed" if allowed else "denied")
    expected_branch = (
        actor
        if actor in {"anonymous", "inactive"}
        else "disabled"
        if mode == "no" or (mode == "debug_only" and not debug)
        else "group_member"
        if actor == "member"
        else "not_member"
    )
    assert gate.how == expected_branch
    if not allowed:
        assert result.decided_by == gate.n


@pytest.mark.django_db
def test_manage_projection_invocations_are_independent_without_extra_queries(monkeypatch, django_assert_num_queries):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")

    def build(sfx):
        vs = ViewSet(model=Publisher, name="projection" + sfx)
        view = register(ManageView, vs)
        return view, [vs]

    first, second = _user("first"), _user("second")
    first.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
    with isolated_routes(build) as view:
        recorder = AccessRecorder()
        with recording(recorder), django_assert_num_queries(4):
            for actor in [first, first, second]:
                request = RequestFactory().get("/")
                request.user = actor
                instance = view()
                instance.setup(request)
                assert instance.has_permission() is (actor is first)
            assert view.cv_has_access(first)
        assert [s.result for s in recorder.steps] == ["passed", "passed", "denied", "passed"]


@pytest.mark.django_db
def test_nested_denial_prevents_local_manage_gate(rows, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    with isolated_routes(lambda s: chain(s, base=ManageView)) as (outer, inner, leaf, _):
        user = _user("developer")
        user.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
        kwargs = coordinates(outer, inner, *rows)
        kwargs.pop("pk")
        result = trace_access(_url(leaf, "tested", **kwargs), user)
        assert result.outcome == "denied"
        assert result.steps[result.decided_by - 1].kind == "ancestor_gate"
        assert all(s.result == "not_reached" for s in result.steps if s.kind == "manage_gate")
