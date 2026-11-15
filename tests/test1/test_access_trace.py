"""Real dispatch, scalar observations and the intentionally pre-context list boundary."""

import importlib.util
import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import translation

from crud_views.lib.views import DetailView, DetailViewPermissionRequired, ListView, ListViewPermissionRequired
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Author, Book, Publisher
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import grant, register


def trace(path, user):
    assert importlib.util.find_spec("crud_views.lib.access_trace"), "the scalar trace entry point must exist"
    from crud_views.lib.access_trace import trace_access

    return trace_access(path, user)


def explode(*args, **kwargs):
    raise AssertionError("handler/context must not run")


@pytest.mark.django_db
@pytest.mark.parametrize("allowed", [True, False])
def test_core_trace_contract(allowed, monkeypatch):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="trace" + sfx)
        view = register(DetailViewPermissionRequired, vs, get=explode, get_context_data=explode)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, _view):
        obj = Publisher.objects.create(name="private contents")
        user = _user("trace actor")
        if allowed:
            grant(user, vs, "view")
        monkeypatch.setattr(Publisher, "__str__", explode)
        monkeypatch.setattr(Publisher, "__repr__", explode)
        with translation.override("en"):
            result = trace(_url(vs, "tested", pk=obj.pk), user)
        data = result.to_dict()
        assert set(data) == {
            "version",
            "path",
            "route",
            "view",
            "user",
            "outcome",
            "decided_by",
            "plan",
            "steps",
            "untraced",
        }
        assert data["version"] == 1
        assert data["outcome"] == ("allowed" if allowed else "denied")
        assert data["user"] == {"pk": str(user.pk), "username": user.username, "active": True, "anonymous": False}
        assert "other middleware and URL decorators are not traced" in data["untraced"]
        assert "private contents" not in json.dumps(data)
        own = next(step for step in data["steps"] if step["kind"] == "own_permission")
        assert own["permission"] == "app.view_publisher"
        assert own["result"] == ("passed" if allowed else "denied")
        kinds = [step["kind"] for step in data["steps"]]
        if allowed:
            assert kinds == ["route", "own_permission", "object_lookup", "action_state"]
            assert data["steps"][2]["object"] == {"model": "app.publisher", "pk": str(obj.pk)}
        else:
            assert kinds == ["route", "own_permission", "action_state"]
            assert data["steps"][-1]["result"] == "not_reached"
            assert data["decided_by"] == own["n"]
        assert all(
            set(step)
            == {
                "n",
                "kind",
                "viewset",
                "object",
                "key",
                "permission",
                "group",
                "provider",
                "source",
                "result",
                "how",
                "message",
                "exception",
                "counts",
            }
            for step in data["steps"]
        )


@pytest.mark.django_db
@pytest.mark.parametrize("error", [False, True])
def test_gate_writes_rollback_and_outer_transaction_survives(error):
    def gate(self):
        Publisher.objects.create(name="rolled back")
        self.request.session.update({"example": "value"})
        self.request.session.save()
        self.request.session.create()
        self.request.session.delete()
        self.request.session.flush()
        from django.contrib import messages

        messages.info(self.request, "not delivered")
        self.request._messages.update(HttpResponse())
        assert self.request.get_host() == "localhost"
        assert self.request.build_absolute_uri("/") == "http://localhost/"
        assert not self.request.GET
        if error:
            raise ValueError("gate failed")
        return True

    def build(sfx):
        vs = ViewSet(model=Publisher, name="rollback" + sfx)
        view = register(DetailViewPermissionRequired, vs, has_permission=gate, get=explode)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, _):
        obj = Publisher.objects.create(name="retained")
        result = trace("https://elsewhere.invalid" + _url(vs, "tested", pk=obj.pk) + "?ignored=yes", _user("writer"))
        assert result.outcome == ("error" if error else "allowed")
        assert list(Publisher.objects.values_list("name", flat=True)) == ["retained"]


@pytest.mark.django_db
def test_fresh_actor_and_user_resolution():
    def build(sfx):
        vs = ViewSet(model=Publisher, name="fresh" + sfx)
        register(DetailViewPermissionRequired, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="example")
        user = _user("fresh actor")
        user._perm_cache = {"app.view_publisher"}
        url = _url(vs, "tested", pk=obj.pk)
        assert trace(url, user).outcome == "denied"
        assert trace(url, AnonymousUser()).outcome == "login_redirect"
        user.is_active = False
        user.save()
        assert trace(url, user).user["active"] is False
        from crud_views.lib.access_trace import resolve_trace_user

        assert resolve_trace_user(str(user.pk)).pk == user.pk
        assert resolve_trace_user(user.username).is_active is False
        collision = _user(str(user.pk))
        assert resolve_trace_user(str(user.pk)).pk == collision.pk
        assert resolve_trace_user("missing user") is None


@pytest.mark.django_db
@pytest.mark.parametrize("omit_filter", [True, False])
def test_list_counts_are_before_context_parent_scoping(omit_filter):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="parent" + sfx, ancestor_policy=AncestorPolicy(provider="none"))
        register(ListView, parent)
        child = ViewSet(model=Book, name="child" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher"))
        attrs = {"get_queryset": lambda self: Book.objects.all()} if omit_filter else {}
        view = register(ListViewPermissionRequired, child, **attrs)
        return (parent, child, view), [parent, child]

    with isolated_routes(build) as (_parent, child, view):
        first = Publisher.objects.create(name="first")
        second = Publisher.objects.create(name="second")
        book = Book.objects.create(title="first", publisher=first)
        Book.objects.create(title="second", publisher=second)
        user = _user("list actor")
        grant(user, child, "view")
        # Parent URL argument is based on the parent's registry name.
        kwargs = {child.get_parent_url_args(first_only=True): first.pk}
        url = _url(child, "tested", **kwargs)
        original = view.get_context_data
        view.get_context_data = explode
        try:
            result = trace(url, user)
        finally:
            view.get_context_data = original
        assert result.outcome == "allowed"
        count = next(step.counts for step in result.steps if step.kind == "list_filter")
        assert count["visible"] == (2 if omit_filter else 1)
        # Real GET builds context and applies its separate child scoping boundary.
        request = RequestFactory().get(url)
        request.user = user
        response = view.as_view()(request, **kwargs)
        assert response.status_code == 200
        assert list(response.context_data["object_list"]) == [book]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "plain,active,grant_early",
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (False, False, False),
        (False, None, True),
        (False, None, False),
    ],
)
def test_all_none_actor_admission_observes_actual_unbound_check(plain, active, grant_early, monkeypatch):
    calls = []

    def backend(self, user, permission, obj=None):
        calls.append(permission)
        return grant_early

    monkeypatch.setattr("django.contrib.auth.backends.ModelBackend.has_perm", backend)

    def build(sfx):
        parent = ViewSet(model=Publisher, name="earlyparent" + sfx, ancestor_policy=AncestorPolicy(provider="none"))
        register(ListView, parent)
        child = ViewSet(
            model=Book, name="earlychild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        register(ListView if plain else ListViewPermissionRequired, child, get=explode)
        return (parent, child), [parent, child]

    with isolated_routes(build) as (_, child):
        obj = Publisher.objects.create(name="parent")
        user = _user("early actor")
        user.is_active = active
        if active is None:
            user = AnonymousUser()
        else:
            user.save()
        result = trace(_url(child, "tested", **{child.get_parent_url_args(first_only=True): obj.pk}), user)
        admission = next(step for step in result.steps if step.kind == "actor_admission")
        assert admission.source.endswith("._cv_ancestor_actor_response")
        assert admission.permission == (None if plain or active else "app.view_book")
        assert admission.result == ("passed" if plain or active or grant_early else "denied")
        assert len(calls) == (0 if plain else 2 if not active and grant_early else 1)


@pytest.mark.django_db(databases=["default", "shard"])
def test_actor_database_identity_is_preserved(django_user_model):
    seen = []

    def dispatch(self, request, *args, **kwargs):
        seen.append((request.user.username, request.user._state.db))
        return HttpResponse()

    def build(sfx):
        vs = ViewSet(model=Publisher, name="alias" + sfx)
        register(DetailView, vs, dispatch=dispatch)
        return vs, [vs]

    default = django_user_model.objects.create_user(username="default identity")
    other = django_user_model.objects.db_manager("shard").create_user(pk=default.pk, username="shard identity")
    with isolated_routes(build) as vs:
        result = trace(_url(vs, "tested", pk=1), other)
        assert result.outcome == "allowed"
        assert seen == [("shard identity", "shard")]


@pytest.mark.django_db
def test_real_setup_dispatch_initkwargs_and_repeated_lookup(monkeypatch):
    from django.urls import path

    from crud_views.lib.view.base import CrudView

    events = []
    original = CrudView.get_object

    def lookup(self, queryset=None):
        events.append("lookup")
        return original(self, queryset)

    monkeypatch.setattr(CrudView, "get_object", lookup)

    def setup(self, request, *args, **kwargs):
        assert self.extra_context == {"trace": "init"}
        assert request.resolver_match.kwargs == kwargs
        events.append("setup")
        super(type(self), self).setup(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        events.append("dispatch")
        return super(type(self), self).dispatch(request, *args, **kwargs)

    def build(sfx):
        vs = ViewSet(model=Publisher, name="dispatch" + sfx)
        view = register(DetailViewPermissionRequired, vs, setup=setup, dispatch=dispatch, get=explode)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        import importlib

        from django.conf import settings
        from django.urls import clear_url_caches

        module = importlib.import_module(settings.ROOT_URLCONF)
        module.urlpatterns.insert(0, path("exact/<int:pk>/", view.as_view(extra_context={"trace": "init"})))
        clear_url_caches()
        obj = Publisher.objects.create(name="object")
        user = _user("dispatch actor")
        grant(user, vs, "view")
        result = trace(f"/exact/{obj.pk}/", user)
        assert result.outcome == "allowed"
        assert events == ["setup", "dispatch", "lookup", "lookup"]
        assert len([step for step in result.steps if step.kind == "object_lookup"]) == 1


@pytest.mark.django_db
def test_state_denial_is_deciding_and_on_commit_is_discarded():
    from django.db import transaction

    committed = []

    def state(cls, user, obj):
        transaction.on_commit(lambda: committed.append(True))
        Publisher.objects.create(name="state write")
        return False

    def build(sfx):
        vs = ViewSet(model=Publisher, name="state" + sfx)
        register(DetailViewPermissionRequired, vs, cv_action_enabled=classmethod(state), get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="retained")
        user = _user("state actor")
        grant(user, vs, "view")
        result = trace(_url(vs, "tested", pk=obj.pk), user)
        assert result.outcome == "denied"
        assert result.steps[result.decided_by - 1].kind == "action_state"
        assert not committed
        assert list(Publisher.objects.values_list("name", flat=True)) == ["retained"]


@pytest.mark.django_db
def test_uuid_identity_and_missing_object():
    def build(sfx):
        vs = ViewSet(model=Author, name="uuidtrace" + sfx)
        register(DetailView, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Author.objects.create(first_name="private", last_name="author")
        url = _url(vs, "tested", pk=obj.pk)
        result = trace(url, AnonymousUser())
        assert next(step.object["pk"] for step in result.steps if step.kind == "object_lookup") == str(obj.pk)
        obj.delete()
        assert trace(url, AnonymousUser()).outcome == "not_found"
