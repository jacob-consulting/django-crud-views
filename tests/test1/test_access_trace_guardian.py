"""Guardian reports actual gates and pre-context list counts without extra reads."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.test import RequestFactory, override_settings

from crud_views.lib.access_trace import AccessRecorder, recording, trace_access
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianParentPermissionMixin,
    GuardianQuerysetMixin,
)
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import register


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fallback,superuser,active,model_grant,object_grant,how",
    [
        (False, True, True, False, True, "active superuser"),
        (True, True, True, True, True, "active superuser"),
        (True, False, True, True, False, "model fallback"),
        (True, False, True, False, True, "object grant"),
        (False, False, True, False, True, "object grant"),
        (False, True, True, False, False, None),
        (True, True, False, True, True, None),
        (False, False, True, False, False, None),
    ],
)
def test_object_branch_result_and_exact_call_order(
    monkeypatch, fallback, superuser, active, model_grant, object_grant, how
):
    import guardian.core

    obj = Publisher.objects.create(name="never expose content")
    calls = []
    user = SimpleNamespace(is_authenticated=True, is_active=active, is_superuser=superuser)
    user.has_perm = lambda perm: calls.append(("model", perm)) or model_grant
    checker = SimpleNamespace(has_perm=lambda perm, row: calls.append(("object", perm, row.pk)) or object_grant)
    factory = Mock(return_value=checker)
    monkeypatch.setattr(guardian.core, "ObjectPermissionChecker", factory)
    view = GuardianObjectPermissionMixin()
    view.cv_guardian_accept_global_perms = fallback
    view.cv_permission = "view"
    recorder = AccessRecorder()
    with recording(recorder):
        allowed = view._check_object_perm(user, "app.view_publisher", obj)
    assert allowed is (how is not None)
    expected = [] if not active else ([("model", "app.view_publisher")] if fallback else [])
    if active and not (fallback and model_grant):
        expected.append(("object", "view_publisher", obj.pk))
    assert calls == expected
    assert factory.call_count == int(active and not (fallback and model_grant))
    assert len(recorder.steps) == 1, "the final object result must be observed once"
    step = recorder.steps[0]
    assert (step.kind, step.result, step.how) == ("own_permission", "passed" if allowed else "denied", how)
    assert step.object == {"model": "app.publisher", "pk": str(obj.pk)}
    assert step.permission == "app.view_publisher" and step.provider == "guardian"
    assert step.source == "GuardianObjectPermissionMixin._check_object_perm"


@pytest.mark.django_db
@pytest.mark.parametrize("mixin", [GuardianObjectPermissionMixin, GuardianQuerysetMixin])
@pytest.mark.parametrize("actor", ["anonymous", "inactive", "active"])
@pytest.mark.parametrize("behavior", ["redirect", "403", "404"])
def test_local_actor_admission_is_observed_without_queries(mixin, actor, behavior, django_assert_num_queries):
    view = mixin()
    user = (
        AnonymousUser() if actor == "anonymous" else SimpleNamespace(is_authenticated=True, is_active=actor == "active")
    )
    view.request = SimpleNamespace(user=user)
    view.cv_guardian_anonymous_behavior = behavior
    recorder = AccessRecorder()
    exception = Http404 if actor == "anonymous" and behavior == "404" else PermissionDenied
    with recording(recorder), django_assert_num_queries(0):
        for _ in range(2):
            if actor == "inactive" or (actor == "anonymous" and behavior != "redirect"):
                with pytest.raises(exception):
                    view.has_permission()
            else:
                assert view.has_permission() is (actor == "active")
    assert len(recorder.steps) == 1, "identical repeated admissions are deduplicated, not cached"
    step = recorder.steps[0]
    expected = (
        "passed" if actor == "active" else "not_found" if actor == "anonymous" and behavior == "404" else "denied"
    )
    assert step.result == expected and step.kind == "actor_admission"
    assert step.source == f"{mixin.__name__}.has_permission"
    if actor == "anonymous":
        assert behavior in step.message
    if actor == "active":
        user.is_active = False
        with recording(recorder), pytest.raises(PermissionDenied), django_assert_num_queries(0):
            view.has_permission()
        assert [s.result for s in recorder.steps] == ["passed", "denied"]


def local_routes(sfx, *, base, **attrs):
    vs = GuardianViewSet(model=Publisher, name="traceguardian" + sfx)
    view = register(base, vs, **attrs)
    return (vs, view), [vs]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fallback,grant,superuser,visible",
    [(False, False, False, 0), (False, True, False, 1), (True, True, False, 2), (False, False, True, 2)],
)
def test_list_counts_use_narrowed_input_and_final_outer_filter(fallback, grant, superuser, visible):
    rows = [Publisher.objects.create(name=str(i)) for i in range(4)]
    user = _user("list", superuser=superuser)
    base = type("LocalList", (GuardianQuerysetMixin, ListViewPermissionRequired), {})

    def get_queryset(self):
        return super(view, self).get_queryset().exclude(pk=rows[2].pk)

    with isolated_routes(
        lambda s: local_routes(
            s, base=base, cv_guardian_accept_global_perms=fallback, get_queryset=get_queryset, get=explode
        )
    ) as (vs, view):
        # Narrow before Guardian by overriding the ViewSet's already-established source.
        original = GuardianViewSet.get_queryset
        if grant:
            vs.assign_perm("view", user, rows[0])
            user.user_permissions.add(Permission.objects.get(codename="view_publisher"))
        with patch.object(
            GuardianViewSet, "get_queryset", lambda self, view: original(self, view).exclude(pk=rows[3].pk)
        ):
            result = trace_access(_url(vs, "tested"), user)
        assert result.outcome == "allowed"
        assert [s.counts for s in result.steps if s.kind == "list_filter"] == [{"total": 3, "visible": visible}]
        assert any(s.kind == "own_permission" and s.result == "passed" for s in result.steps)


@pytest.mark.django_db
def test_nested_unscoped_list_counts_precede_context_parent_scoping(client, monkeypatch):
    parents = [Publisher.objects.create(name=str(i)) for i in range(2)]
    rows = [Book.objects.create(title=str(i), publisher=parents[i % 2]) for i in range(4)]
    user = _user("nested list")

    def build(sfx):
        parent = GuardianViewSet(model=Publisher, name="countparent" + sfx)
        child = GuardianViewSet(
            model=Book, name="countchild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        view = register(GuardianListViewPermissionRequired, child, cv_key="list")
        return (parent, child, view), [parent, child]

    with isolated_routes(build) as (parent, child, _view):
        parent.assign_perm("view", user, parents[0])
        for row in rows[:3]:
            child.assign_perm("view", user, row)
        original = GuardianViewSet.get_queryset
        monkeypatch.setattr(
            GuardianViewSet,
            "get_queryset",
            lambda self, view: Book.objects.all() if self is child else original(self, view),
        )
        url = _url(child, "list", **{parent.name + "_pk": parents[0].pk})
        result = trace_access(url, user)
        assert result.outcome == "allowed"
        assert [s.counts for s in result.steps if s.kind == "list_filter"] == [{"total": 4, "visible": 3}]
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert {row.pk for row in response.context["object_list"]} == {rows[0].pk, rows[2].pk}


@pytest.mark.django_db
def test_ordinary_filter_capture_never_evaluates_querysets(monkeypatch, django_assert_num_queries):
    import guardian.shortcuts

    base = type("LocalList", (GuardianQuerysetMixin, ListViewPermissionRequired), {})
    with isolated_routes(lambda s: local_routes(s, base=base)) as (vs, view):
        instance = view()
        instance.request = SimpleNamespace(user=_user("lazy"))
        instance.kwargs = {}
        assert vs.permissions  # warm the existing vocabulary outside the assertion
        before = Publisher.objects.all()
        after = before.none()
        monkeypatch.setattr(GuardianViewSet, "get_queryset", lambda self, view: before)
        monkeypatch.setattr(guardian.shortcuts, "get_objects_for_user", lambda *a, **kw: after)
        recorder = AccessRecorder()
        with recording(recorder), django_assert_num_queries(0):
            assert instance.get_queryset() is after
        assert recorder._filters.get(id(instance)) == (before, after)
        assert before._result_cache is None and after._result_cache is None


@pytest.mark.django_db
def test_object_state_is_separate_from_grant():
    obj = Publisher.objects.create(name="state")
    user = _user("state", superuser=True)
    base = type("LocalDetail", (GuardianObjectPermissionMixin, DetailViewPermissionRequired), {})
    with isolated_routes(
        lambda s: local_routes(s, base=base, get=explode, cv_action_enabled=classmethod(lambda cls, user, obj: False))
    ) as (vs, _):
        result = trace_access(_url(vs, "tested", pk=obj.pk), user)
        assert result.outcome == "denied"
        own = [s for s in result.steps if s.kind == "own_permission"]
        assert len(own) == 1 and own[0].how == "active superuser" and own[0].result == "passed"
        deciding = result.steps[result.decided_by - 1]
        assert deciding.kind == "action_state" and deciding.object == {"model": "app.publisher", "pk": str(obj.pk)}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fallback,superuser,active,model_grant,object_grant,how",
    [
        (False, True, True, False, True, "active superuser"),
        (True, True, True, True, True, "active superuser"),
        (True, False, True, True, False, "model fallback"),
        (True, False, True, False, True, "object grant"),
        (False, False, True, False, True, "object grant"),
        (False, True, True, False, False, None),
        (True, True, False, True, True, None),
    ],
)
def test_ancestor_branch_result_and_exact_order(
    monkeypatch, fallback, superuser, active, model_grant, object_grant, how
):
    from crud_views_guardian.lib import ancestors

    obj = Publisher.objects.create(name="ancestor")
    calls = []
    user = SimpleNamespace(is_authenticated=True, is_active=active, is_superuser=superuser)
    user.has_perm = lambda perm: calls.append(("model", perm)) or model_grant
    checker = SimpleNamespace(has_perm=lambda perm, row: calls.append(("object", perm, row.pk)) or object_grant)
    factory = Mock(return_value=checker)
    monkeypatch.setattr(ancestors, "_request_checker", factory)
    vs = SimpleNamespace(name="ancestor", ancestor_policy=AncestorPolicy(accept_global_perms=fallback))
    view = SimpleNamespace(cv_guardian_accept_global_perms=not fallback)
    recorder = AccessRecorder()
    with recording(recorder):
        allowed = ancestors._guardian_ancestor_has_permission(vs, user, "app.view_publisher", obj, view=view)
    assert allowed is (how is not None)
    expected = [] if not active else ([("model", "app.view_publisher")] if fallback else [])
    if active and not (fallback and model_grant):
        expected.append(("object", "app.view_publisher", obj.pk))
    assert calls == expected
    assert factory.call_count == int(active and not (fallback and model_grant))
    assert len(recorder.steps) == 1, "provider must report its successful branch or final refusal"
    step = recorder.steps[0]
    assert (step.kind, step.result, step.how) == ("object_grant", "passed" if allowed else "denied", how)
    assert step.viewset == "ancestor" and step.object == {"model": "app.publisher", "pk": str(obj.pk)}
    assert step.source == "ancestor_policy.accept_global_perms"


def nested_routes(sfx, *, base=GuardianCreateViewPermissionRequired, fallback=False, outer_core=False, **attrs):
    outer = (ViewSet if outer_core else GuardianViewSet)(model=Publisher, name="guardouter" + sfx)
    inner = GuardianViewSet(
        model=Book,
        name="guardinner" + sfx,
        parent=ParentViewSet(name=outer.name, attribute="publisher"),
        ancestor_policy=AncestorPolicy(accept_global_perms=fallback),
    )
    leaf = GuardianViewSet(
        model=BookNote, name="guardleaf" + sfx, parent=ParentViewSet(name=inner.name, attribute="book")
    )
    key = (
        "create"
        if base is GuardianCreateViewPermissionRequired
        else "detail"
        if base is GuardianDetailViewPermissionRequired
        else "list"
    )
    view = register(base, leaf, key=key, get=explode, **attrs)
    return (outer, inner, leaf, view, key), [outer, inner, leaf]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fallback,outer_core,state", [(False, False, True), (True, False, True), (False, True, True), (False, False, False)]
)
def test_nested_create_parent_only_requirements_and_state(fallback, outer_core, state):
    pub = Publisher.objects.create(name="outer")
    book = Book.objects.create(title="inner", publisher=pub)
    user = _user("create", (Publisher, "view"), (Book, "change"))
    states = []

    def state_hook(cls, actor, obj):
        states.append(obj.pk)
        assert type(obj) is Book
        return state

    with isolated_routes(
        lambda s: nested_routes(s, fallback=fallback, outer_core=outer_core, cv_action_enabled=classmethod(state_hook))
    ) as (outer, inner, leaf, view, key):
        if not outer_core:
            outer.assign_perm("view", user, pub)
        if not fallback:
            inner.assign_perm("change", user, book)
        url = _url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk})
        result = trace_access(url, user)
        assert result.outcome == ("allowed" if state else "denied")
        assert view.cv_get_requirement()["kind"] == "none"
        assert not any(s.kind == "own_permission" or s.permission == "app.add_booknote" for s in result.steps)
        gates = [s for s in result.steps if s.kind == "ancestor_gate"]
        assert [(s.viewset, s.permission, s.provider) for s in gates] == [
            (outer.name, "app.view_publisher", "model" if outer_core else "guardian"),
            (inner.name, "app.change_book", "guardian"),
        ]
        grants = [s for s in result.steps if s.kind == "object_grant"]
        assert len(grants) == (1 if outer_core else 2)
        assert grants[-1].how == ("model fallback" if fallback else "object grant")
        assert states == [book.pk]
        steps = [s for s in result.steps if s.kind == "action_state"]
        assert len(steps) == 1 and steps[0].object == {"model": "app.book", "pk": str(book.pk)}
        assert steps[0].result == ("passed" if state else "denied")
        if not state:
            assert result.decided_by == steps[0].n


@pytest.mark.django_db
@pytest.mark.parametrize("base", [GuardianObjectPermissionMixin, GuardianQuerysetMixin, GuardianParentPermissionMixin])
@pytest.mark.parametrize("actor", ["anonymous", "inactive", "active"])
@pytest.mark.parametrize("behavior", ["redirect", "403", "404"])
def test_nested_adapters_have_one_helper_owned_admission(base, actor, behavior, django_assert_num_queries):
    user = (
        AnonymousUser() if actor == "anonymous" else SimpleNamespace(is_authenticated=True, is_active=actor == "active")
    )
    view = base()
    view.request = SimpleNamespace(user=user)
    view.cv_guardian_anonymous_behavior = behavior
    view.handle_no_permission = Mock(return_value=SimpleNamespace(status_code=302))
    recorder = AccessRecorder()
    exception = Http404 if actor == "anonymous" and behavior == "404" else PermissionDenied
    with recording(recorder), django_assert_num_queries(0):
        if actor == "inactive" or (actor == "anonymous" and behavior != "redirect"):
            with pytest.raises(exception):
                view._cv_ancestor_actor_response(protected=True)
        else:
            response = view._cv_ancestor_actor_response(protected=True)
            assert response is (view.handle_no_permission.return_value if actor == "anonymous" else None)
    assert len(recorder.steps) == 1
    step = recorder.steps[0]
    assert step.kind == "actor_admission" and step.source == "_guardian_actor_response"
    assert step.result == (
        "passed" if actor == "active" else "not_found" if actor == "anonymous" and behavior == "404" else "denied"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("behavior", ["redirect", "403", "404"])
@pytest.mark.parametrize("actor", ["anonymous", "inactive", "active"])
def test_top_level_parent_dispatch_actor_report(behavior, actor):
    user = AnonymousUser() if actor == "anonymous" else _user("top parent", superuser=True)
    if actor == "inactive":
        user.is_active = False
        user.save()
    with isolated_routes(
        lambda s: local_routes(
            s, base=GuardianCreateViewPermissionRequired, cv_guardian_anonymous_behavior=behavior, get=explode
        )
    ) as (vs, _):
        result = trace_access(_url(vs, "tested"), user)
        admissions = [s for s in result.steps if s.kind == "actor_admission"]
        assert len(admissions) == 1
        assert admissions[0].source == (
            "_guardian_actor_response" if actor == "anonymous" else "GuardianParentPermissionMixin.dispatch"
        )
        assert result.outcome == (
            "allowed"
            if actor == "active"
            else "not_found"
            if actor == "anonymous" and behavior == "404"
            else "login_redirect"
            if actor == "anonymous" and behavior == "redirect"
            else "denied"
        )


@pytest.mark.django_db
def test_invalid_composition_precedes_actor_and_reports_original_error(monkeypatch):
    from tests.test1.test_guardian_composition import UnsafeUpdate

    monkeypatch.setattr(UnsafeUpdate, "cv_viewset", SimpleNamespace(parent=object()))
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    recorder = AccessRecorder()
    with recording(recorder), pytest.raises(ImproperlyConfigured, match="GuardianObjectPermissionMixin"):
        UnsafeUpdate.as_view()(request)
    assert len(recorder.steps) == 1
    assert recorder.steps[0].kind == "validation" and recorder.steps[0].result == "error"


@pytest.mark.django_db
def test_ancestor_routing_refusal_precedes_provider_and_vocabulary():
    from tests.test1.test_access_trace_ancestors import AuthShardRouter

    pub = Publisher.objects.create(name="routing")
    book = Book.objects.create(title="routing", publisher=pub)
    with isolated_routes(nested_routes) as (outer, inner, leaf, _view, key):
        user = _user("routing", superuser=True)
        outer._default_permissions = {}
        with override_settings(DATABASE_ROUTERS=[AuthShardRouter()]):
            result = trace_access(_url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk}), user)
        assert result.outcome == "error"
        step = result.steps[result.decided_by - 1]
        assert step.kind == "ancestor_gate" and "selected database 'shard'" in step.exception["message"]
        assert step.permission is None
        assert not any(s.kind == "object_grant" for s in result.steps)


@pytest.mark.django_db
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(
    "base",
    [GuardianCreateViewPermissionRequired, GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired],
)
@pytest.mark.parametrize("behavior", ["redirect", "403", "404"])
@pytest.mark.parametrize("inactive", [False, True])
def test_actor_refusal_is_deciding_before_any_lookup_or_count(nested, base, behavior, inactive):
    user = _user("inactive", superuser=True) if inactive else AnonymousUser()
    if inactive:
        user.is_active = False
        user.save()

    def build(sfx):
        if nested:
            ns, routed = nested_routes(sfx, base=base, cv_guardian_anonymous_behavior=behavior)
            outer, inner, leaf, _view, key = ns
            kwargs = {outer.name + "_pk": 9999, inner.name + "_pk": 9999}
        else:
            (leaf, _view), routed = local_routes(sfx, base=base, cv_guardian_anonymous_behavior=behavior)
            key, kwargs = "tested", {}
        if base is GuardianDetailViewPermissionRequired:
            kwargs["pk"] = 9999
        return (leaf, key, kwargs), routed

    with isolated_routes(build) as (leaf, key, kwargs):
        result = trace_access(_url(leaf, key, **kwargs), user)
        assert result.outcome == (
            "denied" if inactive or behavior == "403" else "not_found" if behavior == "404" else "login_redirect"
        )
        deciding = result.steps[result.decided_by - 1]
        assert deciding.kind == "actor_admission"
        assert len([s for s in result.steps if s.kind == "actor_admission"]) == 1
        assert not any(s.kind in {"ancestor_lookup", "object_lookup", "list_filter"} for s in result.steps)


@pytest.mark.django_db
@pytest.mark.parametrize("ancestor_fallback,local_fallback", [(False, True), (True, False), (True, True)])
def test_ancestor_and_local_fallback_policies_are_independent(ancestor_fallback, local_fallback):
    pub = Publisher.objects.create(name="outer")
    book = Book.objects.create(title="inner", publisher=pub)
    note = BookNote.objects.create(book=book, note="private")
    user = _user("independent", (Book, "view"), (BookNote, "view"))
    with isolated_routes(
        lambda s: nested_routes(
            s,
            base=GuardianDetailViewPermissionRequired,
            fallback=ancestor_fallback,
            cv_guardian_accept_global_perms=local_fallback,
        )
    ) as (outer, inner, leaf, _view, key):
        outer.assign_perm("view", user, pub)
        result = trace_access(
            _url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk, "pk": note.pk}), user
        )
        assert result.outcome == ("allowed" if ancestor_fallback and local_fallback else "denied")
        ancestor = [s for s in result.steps if s.kind == "object_grant" and s.viewset == inner.name]
        assert len(ancestor) == 1 and ancestor[0].how == ("model fallback" if ancestor_fallback else None)
        local = [s for s in result.steps if s.kind == "own_permission"]
        assert len(local) == 1
        assert local[0].result == ("not_reached" if not ancestor_fallback else "passed" if local_fallback else "denied")
        assert local[0].how == ("model fallback" if ancestor_fallback and local_fallback else None)


@pytest.mark.django_db
def test_parent_state_denial_prevents_list_filter_counts():
    pub = Publisher.objects.create(name="outer")
    book = Book.objects.create(title="inner", publisher=pub)
    user = _user("disabled list", superuser=True)
    with isolated_routes(
        lambda s: nested_routes(
            s,
            base=GuardianListViewPermissionRequired,
            cv_action_enabled=classmethod(lambda *args: False),
            get_queryset=explode,
        )
    ) as (outer, inner, leaf, _view, key):
        result = trace_access(_url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk}), user)
        assert result.outcome == "denied"
        deciding = result.steps[result.decided_by - 1]
        assert deciding.kind == "action_state" and deciding.object == {"model": "app.book", "pk": str(book.pk)}
        assert not any(s.kind == "list_filter" for s in result.steps)


@pytest.mark.django_db
def test_repeated_object_gates_execute_again_but_identical_reports_deduplicate(monkeypatch):
    import guardian.core

    obj = Publisher.objects.create(name="repeat")
    checker = Mock()
    checker.has_perm.side_effect = [True, True, False]
    monkeypatch.setattr(guardian.core, "ObjectPermissionChecker", Mock(return_value=checker))
    user = _user("repeat")
    base = type("LocalDetail", (GuardianObjectPermissionMixin, DetailViewPermissionRequired), {})
    with isolated_routes(lambda s: local_routes(s, base=base)) as (_vs, view):
        instance = view()
        request = RequestFactory().get("/")
        request.user = user
        instance.setup(request, pk=obj.pk)
        recorder = AccessRecorder()
        with recording(recorder):
            assert instance.get_object().pk == obj.pk
            assert instance.get_object().pk == obj.pk
            with pytest.raises(PermissionDenied):
                instance.get_object()
        assert checker.has_perm.call_count == 3
        assert [s.result for s in recorder.steps if s.kind == "own_permission"] == ["passed", "denied"]
        assert len([s for s in recorder.steps if s.kind == "action_state"]) == 1
