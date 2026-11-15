"""Planned requirements remain metadata; reached gates retain request ordering."""

import pytest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden
from django.test import RequestFactory, override_settings

from crud_views.lib.access_trace import trace_access
from crud_views.lib.views import ActionView, DetailView, DetailViewPermissionRequired, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import register


def chain(sfx, *, cascade=True, outer_none=False, inner_none=False, base=DetailViewPermissionRequired, **attrs):
    outer = ViewSet(
        model=Publisher,
        name="traceouter" + sfx,
        ancestor_policy=AncestorPolicy(provider="none" if outer_none else "model"),
    )
    register(ListView, outer)
    inner = ViewSet(
        model=Book,
        name="traceinner" + sfx,
        parent=ParentViewSet(name=outer.name, attribute="publisher"),
        ancestor_policy=AncestorPolicy(provider="none" if inner_none else "model"),
    )
    register(ListView, inner)
    leaf = ViewSet(
        model=BookNote,
        name="traceleaf" + sfx,
        parent=ParentViewSet(name=inner.name, attribute="book"),
        ancestor_policy=AncestorPolicy(cascade=cascade),
    )
    view = register(base, leaf, get=explode, **attrs)
    return (outer, inner, leaf, view), [outer, inner, leaf]


def coordinates(outer, inner, pub, book, note):
    return {outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk, "pk": note.pk}


@pytest.fixture
def rows(db):
    pub = Publisher.objects.create(name="private publisher")
    book = Book.objects.create(title="private book", publisher=pub)
    note = BookNote.objects.create(book=book, note="private note")
    return pub, book, note


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cascade,outer_none,inner_none",
    [(True, False, False), (False, False, False), (True, True, False), (True, False, True)],
)
def test_planned_and_reached_ancestor_gates(rows, cascade, outer_none, inner_none):
    with isolated_routes(lambda s: chain(s, cascade=cascade, outer_none=outer_none, inner_none=inner_none)) as ns:
        outer, inner, leaf, _ = ns
        result = trace_access(_url(leaf, "tested", **coordinates(outer, inner, *rows)), _user("no rights"))
        assert result.outcome == "denied"
        planned = [p for p in result.plan if p["kind"] == "ancestor_gate"]
        expected = (
            [outer.name, inner.name]
            if cascade and not outer_none and not inner_none
            else [outer.name if inner_none else inner.name]
        )
        assert [p["viewset"] for p in planned] == expected
        assert all(p["key"] == "view" and p["source"] == "global CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS" for p in planned)
        reached = [s for s in result.steps if s.kind == "ancestor_gate" and s.result != "not_reached"]
        assert len(reached) == 1
        assert reached[0].permission == ("app.view_publisher" if expected[0] == outer.name else "app.view_book")
        assert result.steps[result.decided_by - 1] is reached[0]
        later = result.steps[result.decided_by :]
        assert later and all(s.result == "not_reached" for s in later)
        assert all(s.permission is None for s in later)
        assert any(s.kind == "own_permission" and s.key == "view" for s in later)
        assert any(s.kind == "action_state" for s in later)


@pytest.mark.django_db
def test_plain_protected_ancestry_direct_login_response(rows):
    with isolated_routes(lambda s: chain(s, base=DetailView)) as (outer, inner, leaf, view):
        kwargs = coordinates(outer, inner, *rows)
        url = _url(leaf, "tested", **kwargs)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = view.as_view()(request, **kwargs)
        assert response.status_code == 302
        result = trace_access(url, AnonymousUser())
        assert result.outcome == "login_redirect"
        admissions = [s for s in result.steps if s.kind == "actor_admission"]
        assert len(admissions) == 1
        assert result.decided_by == admissions[0].n
        assert not any(s.kind == "ancestor_lookup" and s.result == "passed" for s in result.steps)


@pytest.mark.django_db
@pytest.mark.parametrize("mismatch", ["ancestor", "leaf", "missing"])
def test_missing_and_mismatched_relationship_deciding_lookup(rows, mismatch):
    pub, book, note = rows
    other = Publisher.objects.create(name="other")
    foreign = Book.objects.create(title="other", publisher=other)
    with isolated_routes(lambda s: chain(s, get_queryset=lambda self: BookNote.objects.all())) as ns:
        outer, inner, leaf, _ = ns
        kwargs = coordinates(outer, inner, pub, foreign if mismatch == "ancestor" else book, note)
        if mismatch == "missing":
            kwargs[outer.name + "_pk"] = 99999
        if mismatch == "leaf":
            note.book = foreign
            note.save()
        result = trace_access(_url(leaf, "tested", **kwargs), _user("all", superuser=True))
        assert result.outcome == "not_found"
        assert result.steps[result.decided_by - 1].kind == (
            "object_lookup" if mismatch == "leaf" else "ancestor_lookup"
        )
        assert all(s.result == "not_reached" for s in result.steps if s.kind == "action_state")


@pytest.mark.django_db
def test_planning_is_query_free_and_does_not_preempt_custom_refusal(rows, django_assert_num_queries):
    with isolated_routes(
        lambda s: chain(s, base=ActionView, dispatch=lambda self, *a, **kw: HttpResponseForbidden())
    ) as ns:
        outer, inner, leaf, view = ns
        from crud_views.lib import access_trace_runner

        assert hasattr(access_trace_runner, "_plan_gates")
        instance = view()
        instance.kwargs = coordinates(outer, inner, *rows)
        with django_assert_num_queries(0):
            plan = access_trace_runner._plan_gates(instance)
        assert any(p["result"] == "unavailable" for p in plan)
        result = trace_access(_url(leaf, "tested", **instance.kwargs), AnonymousUser())
        assert result.outcome == "denied"


@pytest.mark.django_db
def test_missing_action_is_actual_validation_error(rows):
    with isolated_routes(lambda s: chain(s, base=ActionView)) as (outer, inner, leaf, _):
        result = trace_access(_url(leaf, "tested", **coordinates(outer, inner, *rows)), AnonymousUser())
        assert result.outcome == "error"
        step = result.steps[result.decided_by - 1]
        assert step.kind == "validation"
        assert step.exception["class"] == "ImproperlyConfigured"
        assert "actions['tested']" in step.exception["message"]


class AuthShardRouter:
    def db_for_read(self, model, **hints):
        return "shard" if model._meta.label_lower == "auth.group" else None


@pytest.mark.django_db
@pytest.mark.parametrize("failure", ["map", "auth_route", "queryset_route"])
def test_reached_failure_keeps_routing_before_vocabulary(rows, failure, monkeypatch):
    with isolated_routes(chain) as (outer, inner, leaf, _):
        outer._default_permissions = {}
        user = _user("routing", superuser=True)
        url = _url(leaf, "tested", **coordinates(outer, inner, *rows))
        if failure == "queryset_route":
            original = ViewSet.get_queryset
            monkeypatch.setattr(
                ViewSet,
                "get_queryset",
                lambda self, view: Publisher.objects.using("shard") if self is outer else original(self, view),
            )
        with override_settings(DATABASE_ROUTERS=[AuthShardRouter()] if failure == "auth_route" else []):
            result = trace_access(url, user)
        assert result.outcome == "error"
        step = result.steps[result.decided_by - 1]
        assert step.kind == ("ancestor_lookup" if failure == "queryset_route" else "ancestor_gate")
        assert step.permission is None
        assert ("permission key" if failure == "map" else "selected database 'shard'") in step.exception["message"]
        assert not any(s.kind == "ancestor_lookup" and s.viewset == inner.name for s in result.steps)


@pytest.mark.django_db
@pytest.mark.parametrize("all_none", [False, True])
def test_inactive_plain_actor_follows_actual_ancestry_policy(rows, all_none):
    with isolated_routes(lambda s: chain(s, outer_none=all_none, inner_none=all_none, base=DetailView)) as ns:
        outer, inner, leaf, _ = ns
        user = _user("inactive")
        user.is_active = False
        user.save()
        result = trace_access(_url(leaf, "tested", **coordinates(outer, inner, *rows)), user)
        assert result.outcome == ("allowed" if all_none else "denied")
        assert len([s for s in result.steps if s.kind == "actor_admission"]) == 1


@pytest.mark.django_db
def test_valid_planning_has_no_database_queries(rows, django_assert_num_queries):
    from crud_views.lib.access_trace_runner import _plan_gates

    with isolated_routes(chain) as (outer, inner, leaf, view):
        leaf.ancestor_policy = AncestorPolicy(actions={"tested": AncestorPermissions(nearest="change", higher="view")})
        instance = view()
        instance.kwargs = coordinates(outer, inner, *rows)
        with django_assert_num_queries(0):
            plan = _plan_gates(instance)
        assert [p["key"] for p in plan if p["kind"] == "ancestor_gate"] == ["view", "change"]
        assert all(p["source"] == "actions['tested']" for p in plan if p["kind"] == "ancestor_gate")


@pytest.mark.django_db
def test_invalid_plan_metadata_does_not_preempt_login(rows):
    base = type("LoginFirstAction", (LoginRequiredMixin, ActionView), {"__module__": __name__})
    with isolated_routes(lambda s: chain(s, base=base)) as (outer, inner, leaf, _):
        result = trace_access(_url(leaf, "tested", **coordinates(outer, inner, *rows)), AnonymousUser())
        assert result.outcome == "login_redirect"
        assert any(row.get("result") == "unavailable" for row in result.plan)
        assert not any(step.kind == "validation" and step.result == "error" for step in result.steps)


@pytest.mark.django_db
def test_one_level_leaf_mismatch_is_object_lookup_before_state(rows):
    _pub, book, _ = rows
    other = Publisher.objects.create(name="other")

    def build(sfx):
        parent = ViewSet(model=Publisher, name="leafparent" + sfx)
        register(ListView, parent)
        child = ViewSet(
            model=Book, name="leafchild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        register(
            DetailViewPermissionRequired,
            child,
            get=explode,
            get_queryset=lambda self: Book.objects.all(),
            cv_action_enabled=classmethod(explode),
        )
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        result = trace_access(
            _url(child, "tested", **{parent.name + "_pk": other.pk, "pk": book.pk}),
            _user("leaf mismatch", superuser=True),
        )
        assert result.outcome == "not_found"
        assert result.steps[result.decided_by - 1].kind == "object_lookup"
        assert any(s.kind == "ancestor_gate" and s.result == "passed" for s in result.steps)
        assert all(s.result == "not_reached" for s in result.steps if s.kind == "action_state")
