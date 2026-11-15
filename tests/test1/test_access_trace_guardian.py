"""Guardian reports actual gates and pre-context list counts without extra reads."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import PermissionDenied
from django.http import Http404

from crud_views.lib.access_trace import AccessRecorder, recording, trace_access
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet
from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin, GuardianQuerysetMixin
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher
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
