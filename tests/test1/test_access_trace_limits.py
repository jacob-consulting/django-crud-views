"""Handler-phase checks are disclosed, never executed by authorization tracing."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseNotAllowed
from django.test import RequestFactory

from crud_views.lib.views import (
    ActionView,
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from crud_views.lib.views.form import CustomFormNoObjectView, CustomFormView
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_workflow.lib.views import WorkflowView
from tests.test1.app.models import Book, Publisher
from tests.test1.test_access_trace import explode, trace
from tests.test1.test_ancestor_authorization import _url, isolated_routes
from tests.test1.test_manage_requirements import register


def limitations(result):
    return {step.key: step for step in result.steps if step.kind == "limitation"}


@pytest.mark.django_db
@pytest.mark.parametrize("reject", [True, False])
def test_post_only_backend_diagnosis_is_instance_local(reject):
    class PostOnly(ActionView):
        http_method_names = ["post", "options"]
        cv_backend = True

        def dispatch(self, request, *args, **kwargs):
            if reject and request.method != "POST":
                return HttpResponseNotAllowed(["POST"])
            return super().dispatch(request, *args, **kwargs)

    def build(sfx):
        vs = ViewSet(model=Publisher, name="postonly" + sfx)
        view = register(PostOnly, vs, post=explode, action=explode, get_context_data=explode)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        obj = Publisher.objects.create(name="object")
        url = _url(vs, "tested", pk=obj.pk)
        original = view.http_method_names
        result = trace(url, AnonymousUser())
        assert result.outcome == ("error" if reject else "allowed")
        step = limitations(result)["method"]
        assert step.result == "not_evaluated"
        assert "GET" in step.message and "POST" in step.message
        assert "handler" in step.message
        assert view.http_method_names is original
        assert original == ["post", "options"]
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        assert view.as_view()(request, pk=obj.pk).status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("denied", [True, False])
@pytest.mark.parametrize(
    "base,nested,keys",
    [
        (WorkflowView, False, {"workflow_transition"}),
        (WorkflowView, True, {"workflow_transition", "write_database"}),
        (ListView, True, {"nested_list_database"}),
        (DeleteView, False, {"delete_preview"}),
        (DeleteView, True, {"delete_preview", "write_database"}),
        (CreateView, True, {"write_database"}),
        (UpdateView, True, {"write_database"}),
        (CustomFormView, True, {"write_database"}),
        (CustomFormNoObjectView, True, {"write_database"}),
        (ActionView, True, {"method", "write_database"}),
        (DetailView, False, set()),
        (ListView, False, set()),
    ],
)
def test_handler_families_are_not_evaluated_even_after_denial(base, nested, keys, denied):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="limitparent" + sfx, ancestor_policy=AncestorPolicy(provider="none"))
        register(ListView, parent)
        vs = ViewSet(
            model=Book,
            name="limited" + sfx,
            parent=ParentViewSet(name=parent.name, attribute="publisher") if nested else None,
        )
        attrs = {
            "get": explode,
            "post": explode,
            "get_context_data": explode,
            "get_form": explode,
            "form_valid": explode,
            "cv_get_delete_preview": explode,
            "cv_form_valid_process": explode,
            "action": explode,
        }
        if denied:
            from django.core.exceptions import PermissionDenied

            def refusal(self, *args, **kwargs):
                raise PermissionDenied("early custom refusal")

            attrs["dispatch"] = refusal
        register(base, vs, **attrs)
        return vs, [parent, vs]

    with isolated_routes(build) as vs:
        parent = Publisher.objects.create(name="parent")
        obj = Book.objects.create(title="book", publisher=parent)
        kwargs = {vs.get_parent_url_args(first_only=True): parent.pk} if nested else {}
        if vs.get_view_class("tested").cv_object:
            kwargs["pk"] = obj.pk
        result = trace(_url(vs, "tested", **kwargs), AnonymousUser())
        assert result.outcome == ("denied" if denied else "allowed")
        notes = limitations(result)
        assert set(notes) == keys
        assert all(step.result == "not_evaluated" and step.message for step in notes.values())
        for key, step in notes.items():
            if key in {"workflow_transition", "write_database"}:
                assert "submit" in step.message
            if key in {"nested_list_database", "delete_preview"}:
                assert "page is built" in step.message
        if not denied:
            assert any("may open the page" in note for note in result.untraced)


@pytest.mark.django_db
def test_login_refusal_still_includes_handler_limits(settings):
    from django.contrib.auth import middleware

    if not hasattr(middleware, "LoginRequiredMiddleware"):
        settings.MIDDLEWARE = []
    else:
        settings.MIDDLEWARE = ["django.contrib.auth.middleware.LoginRequiredMiddleware"]

    def build(sfx):
        vs = ViewSet(model=Publisher, name="loginlimits" + sfx)
        register(DeleteView, vs, get=explode, get_context_data=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        result = trace(_url(vs, "tested", pk=999), AnonymousUser())
        assert result.outcome == ("login_redirect" if settings.MIDDLEWARE else "not_found")
        assert limitations(result)["delete_preview"].result == "not_evaluated"
