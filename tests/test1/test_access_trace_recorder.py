"""Recorder scope and observation neutrality for ordinary requests and direct gates."""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import pytest
from django.http import HttpResponseRedirect
from django.test import RequestFactory

from crud_views.lib.access_trace import AccessRecorder, get_recorder, recording, trace_access
from crud_views.lib.view.base import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import grant, register


def test_external_fixture_matches_switch():
    assert (get_recorder() is not None) == (os.environ.get("CV_ACCESS_RECORD_REQUESTS") == "1")


def test_nested_and_exceptional_context_restore():
    initial = get_recorder()
    outer, inner = AccessRecorder(), AccessRecorder()
    with recording(outer):
        with pytest.raises(ValueError), recording(inner):
            inner.record(inner, "route", result="passed")
            raise ValueError("stop")
        assert get_recorder() is outer
        assert not outer.steps
    assert get_recorder() is initial


def test_copied_concurrent_contexts_have_independent_recordings():
    outer = AccessRecorder()

    def run(value):
        recorder = AccessRecorder()
        with recording(recorder):
            recorder.record(recorder, "route", source=value, result="passed")
            assert get_recorder() is recorder
        assert get_recorder() is outer
        return recorder.steps[0].source

    with recording(outer), ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(copy_context().run, run, value) for value in ("first", "second")]
        assert [future.result() for future in futures] == ["first", "second"]
        assert not outer.steps


def test_same_owner_dedup_preserves_changed_terminal_results():
    recorder = AccessRecorder()
    first, second = object(), object()
    for result in ("passed", "passed", "denied", "error"):
        recorder.record(first, "action_state", result=result)
    recorder.record(second, "action_state", result="passed")
    assert [step.result for step in recorder.steps] == ["passed", "denied", "error", "passed"]
    assert [step.n for step in recorder.steps] == [1, 2, 3, 4]


def test_separate_classmethod_invocations_never_coalesce():
    recorder = AccessRecorder()

    class Gate:
        @classmethod
        def check(cls, actor):
            # Like library projection gates: actor is evaluated, never retained.
            recorder.record(cls, "own_permission", permission="app.view_publisher", result="passed")
            return actor is not None

    first, second = object(), object()
    assert Gate.check(first)
    assert Gate.check(second)
    assert Gate.check(first)
    assert len(recorder.steps) == 3
    assert all(owner is not first and owner is not second for owner in recorder._owners.values())


def test_capture_is_lazy_private_and_cleared():
    class Unevaluated:
        def __len__(self):
            raise AssertionError("capture must not count")

        __bool__ = __repr__ = __len__

    recorder = AccessRecorder()
    owner, before, after = object(), Unevaluated(), Unevaluated()
    response = HttpResponseRedirect("/accounts/login/")
    recorder.capture_filter(owner, before, after)
    capture = getattr(recorder, "capture_login_response", None)
    assert callable(capture), "actual login response identity must remain private"
    capture(owner, response)
    assert recorder._filters[id(owner)][0] is before
    assert recorder._login_responses[id(owner)] is response
    assert not recorder.steps
    recorder.clear()
    assert not recorder._owners and not recorder._filters and not recorder._login_responses


def test_import_before_settings_and_flag_enabled_collection():
    env = {**os.environ, "PYTHONPATH": "src:.", "CV_ACCESS_RECORD_REQUESTS": "1"}
    env.pop("DJANGO_SETTINGS_MODULE", None)
    code = (
        "import sys; from crud_views.lib.access_trace import AccessRecorder, recording; "
        "assert 'django.conf' not in sys.modules; "
        "assert AccessRecorder().steps == []"
    )
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test1/test_access_trace_recorder.py", "--collect-only", "-q"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_external_fixture_matches_switch" in result.stdout


@pytest.mark.django_db
def test_ordinary_requests_and_direct_calls_observed_without_changing_calls(client, monkeypatch):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="record" + sfx)
        view = register(DetailViewPermissionRequired, vs)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        user = _user("recorder actor")
        grant(user, vs, "view")
        obj = Publisher.objects.create(name="example")
        url = _url(vs, "tested", pk=obj.pk)
        client.force_login(user)
        recorder = get_recorder() or AccessRecorder()
        with recording(recorder):
            assert client.get(url).status_code == 200
            assert any(step.kind == "own_permission" for step in recorder.steps)
            reached = len([step for step in recorder.steps if step.kind == "own_permission"])
            request = RequestFactory().get(url)
            request.user = user
            instance = view()
            instance.setup(request, pk=obj.pk)
            assert instance.has_permission()
            assert len([step for step in recorder.steps if step.kind == "own_permission"]) == reached + 1
            outer_steps = len(recorder.steps)
            assert trace_access(url, user).outcome == "allowed"
            assert len(recorder.steps) == outer_steps
            assert get_recorder() is recorder
            calls = []

            def state(cls, user, obj):
                calls.append(True)
                return len(calls) == 1

            monkeypatch.setattr(view, "cv_action_enabled", classmethod(state))
            assert instance.has_permission()
            assert not instance.has_permission()
            assert len(calls) == 2
            assert recorder.steps[-1].kind == "action_state"
            assert recorder.steps[-1].result == "denied"


def test_gate_signatures_unchanged():
    import inspect

    assert str(inspect.signature(CrudViewPermissionRequiredMixin.has_permission)) == "(self)"
    assert list(inspect.signature(DetailViewPermissionRequired.cv_action_enabled).parameters) == ["user", "obj"]


@pytest.mark.django_db
@pytest.mark.parametrize("early", [False, True])
@pytest.mark.parametrize("unused_property", ["raising", "cached"])
def test_requirement_hook_runs_once_without_reading_unused_property(
    early, unused_property, monkeypatch, django_assert_num_queries
):
    from django.contrib.auth.models import AnonymousUser

    from crud_views.lib.views import ListViewPermissionRequired

    calls = []

    def requirements(self):
        calls.append("requirements")
        # A dynamic requirement must not be called a second time for reporting.
        return () if calls.count("requirements") == 1 else ("app.different_permission",)

    def permission(self):
        raise AssertionError("unused permission property was read")

    def check(perms):
        calls.append(("check", tuple(perms)))
        return not perms

    def build(sfx):
        vs = ViewSet(model=Publisher, name="requirementhook" + sfx)
        attrs = {"get_permission_required": requirements, "cv_permission": "custom"}
        if unused_property == "raising":
            attrs["permission_required"] = property(permission)
        view = register(ListViewPermissionRequired, vs, **attrs)
        return view, [vs]

    with isolated_routes(build) as view:
        for recorder in (None, AccessRecorder()):
            calls.clear()
            actor = AnonymousUser()
            monkeypatch.setattr(actor, "has_perms", check)
            instance = view()
            instance.setup(RequestFactory().get("/"))
            instance.request.user = actor
            if unused_property == "cached":
                instance.__dict__["permission_required"] = "app.unused_permission"
            with recording(recorder), django_assert_num_queries(0):
                if early:
                    assert instance._cv_ancestor_actor_response(protected=False) is None
                else:
                    assert instance.has_permission()
            assert calls == ["requirements", ("check", ())]
            if recorder:
                step = recorder.steps[0]
                assert step.permission is None


@pytest.mark.django_db
def test_custom_requirements_keep_real_and_traced_request_outcomes(client):
    from django.http import HttpResponse

    from crud_views.lib.views import ListViewPermissionRequired

    calls = []

    def requirements(self):
        calls.append(True)
        return ()

    def build(sfx):
        vs = ViewSet(model=Publisher, name="customrequirement" + sfx)
        register(
            ListViewPermissionRequired,
            vs,
            cv_permission="custom",
            get_permission_required=requirements,
            get=lambda self, request: HttpResponse(),
        )
        return vs, [vs]

    with isolated_routes(build) as vs:
        url = _url(vs, "tested")
        for recorder in (None, AccessRecorder()):
            calls.clear()
            with recording(recorder):
                assert client.get(url).status_code == 200
            assert calls == [True]
        calls.clear()
        assert trace_access(url, None).outcome == "allowed"
        assert calls == [True]


@pytest.mark.django_db
@pytest.mark.parametrize("early", [False, True])
@pytest.mark.parametrize("raise_on_extra_read", [False, True])
def test_classproperty_requirements_remain_opaque_without_extra_reads(
    early, raise_on_extra_read, monkeypatch, django_assert_num_queries
):
    from django.contrib.auth.models import AnonymousUser
    from django.utils.functional import classproperty

    from crud_views.lib.views import ListViewPermissionRequired

    reads = []
    checks = []

    @classproperty
    def permission_required(cls):
        reads.append(cls)
        if raise_on_extra_read and len(reads) > 3:
            raise RuntimeError("unexpected extra descriptor evaluation")
        return ()

    def check(perms):
        checks.append(tuple(perms))
        return not perms

    def build(sfx):
        vs = ViewSet(model=Publisher, name="descriptorrequirement" + sfx)
        view = register(ListViewPermissionRequired, vs, permission_required=permission_required)
        return view, [vs]

    with isolated_routes(build) as view:
        for recorder in (None, AccessRecorder()):
            reads.clear()
            checks.clear()
            actor = AnonymousUser()
            monkeypatch.setattr(actor, "has_perms", check)
            instance = view()
            instance.setup(RequestFactory().get("/"))
            instance.request.user = actor
            with recording(recorder), django_assert_num_queries(0):
                if early:
                    assert instance._cv_ancestor_actor_response(protected=False) is None
                else:
                    assert instance.has_permission()
            # Django's stock get_permission_required reads its source three times.
            assert reads == [view] * 3
            assert checks == [()]
            if recorder:
                assert recorder.steps[0].permission is None
