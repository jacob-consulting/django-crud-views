"""Observed boundaries, response provenance and rollback through real dispatch."""

import json
from types import MethodType

import pytest
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.test import RequestFactory

from crud_views.lib.access_trace import AccessRecorder, get_recorder, recording
from crud_views.lib.views import DetailView, DetailViewPermissionRequired, ListView
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin
from tests.test1.app.models import Book, Publisher
from tests.test1.test_access_trace import explode, trace
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import grant, register


def custom_decision(result, owner, method, outcome):
    custom = [s for s in result.steps if s.kind == "custom_gate" and s.result == outcome]
    assert len(custom) == 1
    step = custom[0]
    assert step.source == f"{owner.__module__}.{owner.__qualname__}.{method}"
    assert step.how == "observed_boundary"
    assert "inner" in step.message and "unknown" in step.message
    assert result.decided_by == step.n
    assert "traceback" not in json.dumps(result.to_dict())
    return step


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["false", "denied", "missing", "403", "404", "super-deny"])
def test_custom_refusal_has_one_observed_boundary(mode):
    calls = []

    class Project(DetailViewPermissionRequired):
        def has_permission(self):
            calls.append("permission")
            if mode == "denied":
                raise PermissionDenied("private gate denied")
            if mode == "missing":
                raise Http404("private gate missing")
            if mode == "super-deny":
                assert super().has_permission()
                return False
            return mode != "false"

        def dispatch(self, request, *args, **kwargs):
            calls.append("dispatch")
            if mode in {"403", "404"}:
                return HttpResponse(status=int(mode))
            return super().dispatch(request, *args, **kwargs)

    def build(sfx):
        vs = ViewSet(model=Publisher, name="custom" + sfx)
        register(Project, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="object")
        user = _user("custom")
        grant(user, vs, "view")
        result = trace(_url(vs, "tested", pk=obj.pk), user)
        outcome = "not_found" if mode in {"missing", "404"} else "denied"
        assert result.outcome == outcome
        custom_decision(result, Project, "dispatch" if mode in {"403", "404"} else "has_permission", outcome)
        assert calls == (["dispatch"] if mode in {"403", "404"} else ["dispatch", "permission"])


@pytest.mark.django_db
@pytest.mark.parametrize("inner_denies", [True, False])
def test_super_frames_are_not_inferred(inner_denies):
    calls = []

    class Uncalled(DetailViewPermissionRequired):
        def has_permission(self):
            raise AssertionError("uncalled MRO definer")

    class Inner(Uncalled):
        def has_permission(self):
            calls.append("inner")
            return not inner_denies

    class Outer(Inner):
        def has_permission(self):
            calls.append("outer")
            allowed = super().has_permission()
            return allowed if inner_denies else False

    def build(sfx):
        vs = ViewSet(model=Publisher, name="frames" + sfx)
        register(Outer, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        result = trace(_url(vs, "tested", pk=1), _user("frames"))
        custom_decision(result, Outer, "has_permission", "denied")
        assert calls == ["outer", "inner"]
        assert "Uncalled" not in json.dumps(result.to_dict())


@pytest.mark.django_db
def test_library_boundary_above_project_override_does_not_invent_inner_owner():
    calls = []

    class Inner(DetailViewPermissionRequired):
        def get_object(self, queryset=None):
            calls.append(queryset)
            raise Http404("inner failure")

    class Outer(GuardianObjectPermissionMixin, Inner):
        pass

    def build(sfx):
        vs = ViewSet(model=Publisher, name="libraryouter" + sfx)
        register(Outer, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        result = trace(_url(vs, "tested", pk=1), _user("inner"))
        custom_decision(result, GuardianObjectPermissionMixin, "get_object", "not_found")
        assert calls == [None]


@pytest.mark.django_db
def test_propagated_library_denial_keeps_its_deciding_step():
    class Wrapper(DetailViewPermissionRequired):
        def has_permission(self):
            return super().has_permission()

    def build(sfx):
        vs = ViewSet(model=Publisher, name="propagated" + sfx)
        register(Wrapper, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        result = trace(_url(vs, "tested", pk=1), _user("propagated"))
        assert result.outcome == "denied"
        assert result.steps[result.decided_by - 1].kind == "own_permission"
        assert not [s for s in result.steps if s.kind == "custom_gate" and s.result == "denied"]


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["early200", "302", "405", "500", "non-http", "swallowed", "discard-login"])
def test_unsupported_responses_never_claim_success_or_login(mode):
    class Unsupported(DetailViewPermissionRequired):
        def dispatch(self, request, *args, **kwargs):
            if mode == "swallowed":
                self.has_permission()
                return self.get(request, *args, **kwargs)
            if mode == "discard-login":
                original = self.handle_no_permission()
                return HttpResponseRedirect(original["Location"])
            if mode == "non-http":
                return None
            if mode == "302":
                return HttpResponseRedirect("/accounts/login/?next=/")
            return HttpResponse(status=200 if mode == "early200" else int(mode))

    def build(sfx):
        vs = ViewSet(model=Publisher, name="unsupported" + sfx)
        register(Unsupported, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="object")
        result = trace(_url(vs, "tested", pk=obj.pk), AnonymousUser())
        assert result.outcome == "error"
        step = result.steps[result.decided_by - 1]
        assert step.exception["class"] == "UnsupportedTraceResponse"
        assert "status" in step.exception["message"]


@pytest.mark.django_db
def test_custom_handle_no_permission_redirect_is_opaque():
    def build(sfx):
        vs = ViewSet(model=Publisher, name="opaque" + sfx)
        register(DetailViewPermissionRequired, vs, handle_no_permission=lambda self: HttpResponseRedirect("/login/"))
        return vs, [vs]

    with isolated_routes(build) as vs:
        assert trace(_url(vs, "tested", pk=1), AnonymousUser()).outcome == "error"


@pytest.mark.django_db
@pytest.mark.parametrize("discard", [False, True])
def test_plain_ancestry_login_uses_exact_response_and_no_lookup(discard):
    class Plain(ListView):
        def dispatch(self, request, *args, **kwargs):
            response = super().dispatch(request, *args, **kwargs)
            return HttpResponseRedirect(response["Location"]) if discard else response

    def build(sfx):
        parent = ViewSet(model=Publisher, name="protected" + sfx)
        register(ListView, parent)
        child = ViewSet(model=Book, name="plain" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher"))
        view = register(Plain, child, get=explode)
        return (child, view), [parent, child]

    with isolated_routes(build) as (vs, view):
        kwargs = {vs.get_parent_url_args(first_only=True): 999}
        url = _url(vs, "tested", **kwargs)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        assert view.as_view()(request, **kwargs).status_code == 302
        result = trace(url, request.user)
        assert result.outcome == ("error" if discard else "login_redirect")
        if not discard:
            assert result.steps[result.decided_by - 1].kind == "actor_admission"
        assert not [s for s in result.steps if s.kind == "ancestor_lookup"]


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("ending", ["allowed", "denied", "error", "database-error"])
def test_default_rollback_preserves_outer_savepoint_and_callbacks(ending):
    callbacks = []

    def gate(self):
        Publisher.objects.create(name="discarded")
        transaction.on_commit(lambda: callbacks.append("trace"))
        if ending == "error":
            raise ValueError("gate error")
        if ending == "database-error":
            Publisher.objects.create(pk=self.kwargs["pk"], name="duplicate")
        return ending != "denied"

    def build(sfx):
        vs = ViewSet(model=Publisher, name="savepoint" + sfx)
        register(DetailViewPermissionRequired, vs, has_permission=gate, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        user = _user("savepoint")
        with transaction.atomic():
            obj = Publisher.objects.create(name="outer")
            transaction.on_commit(lambda: callbacks.append("outer"))
            result = trace(_url(vs, "tested", pk=obj.pk), user)
            assert result.outcome == ("error" if ending == "database-error" else ending)
            assert list(Publisher.objects.values_list("name", flat=True)) == ["outer"]
            Publisher.objects.create(name="after")
        assert callbacks == ["outer"]
        assert Publisher.objects.count() == 2
        if ending in {"error", "database-error"}:
            expected = "ValueError" if ending == "error" else IntegrityError.__name__
            assert result.steps[result.decided_by - 1].exception["class"] == expected


@pytest.mark.django_db
def test_memory_stores_and_fresh_actor_leave_viewer_untouched(monkeypatch):
    from django.contrib.messages.storage.fallback import FallbackStorage
    from django.contrib.sessions.backends.db import SessionStore

    for name in ("save", "create", "delete", "flush", "cycle_key", "update"):
        monkeypatch.setattr(SessionStore, name, explode)
    monkeypatch.setattr(FallbackStorage, "_store", explode)
    seen = []

    def gate(self):
        actor = self.request.user
        assert not hasattr(actor, "_perm_cache")
        assert not hasattr(actor, "_prefetched_objects_cache")
        seen.append(actor)
        session = self.request.session
        session.update({"a": 1})
        session.save()
        session.create()
        session.cycle_key()
        assert session["a"] == 1
        session.delete()
        session.flush()
        assert not session.items()
        messages.info(self.request, "ephemeral")
        self.request._messages.update(HttpResponse())
        return True

    def build(sfx):
        vs = ViewSet(model=Publisher, name="stores" + sfx)
        register(DetailViewPermissionRequired, vs, has_permission=gate, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        user = _user("viewer")
        user.groups.add(Group.objects.create(name="viewer group"))
        user = type(user).objects.prefetch_related("groups").get(pk=user.pk)
        user._perm_cache = {"stale"}
        cache = user._prefetched_objects_cache
        obj = Publisher.objects.create(name="object")
        external = AccessRecorder()
        with recording(external):
            result = trace(_url(vs, "tested", pk=obj.pk), user)
            assert get_recorder() is external
            assert external.steps == []
        assert result.outcome == "allowed"
        assert seen[0] is not user
        assert user._perm_cache == {"stale"}
        assert user._prefetched_objects_cache is cache


@pytest.mark.django_db
def test_setup_cannot_replace_the_stub():
    class Setup(DetailView):
        def setup(self, *args, **kwargs):
            super().setup(*args, **kwargs)
            self.get = MethodType(explode, self)

    def build(sfx):
        vs = ViewSet(model=Publisher, name="setup" + sfx)
        register(Setup, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="object")
        assert trace(_url(vs, "tested", pk=obj.pk), AnonymousUser()).outcome == "allowed"
