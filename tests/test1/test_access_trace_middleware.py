"""Call only the real installed login middleware with the resolved callback."""

from functools import wraps
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth import middleware as auth_middleware
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.urls import clear_url_caches, path, resolve

from crud_views.lib.views import DetailView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace import explode, trace
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_manage_requirements import register

LOGIN = "django.contrib.auth.middleware.LoginRequiredMiddleware"
HAS_LOGIN = hasattr(auth_middleware, "LoginRequiredMiddleware")
requires_login = pytest.mark.skipif(not HAS_LOGIN, reason="LoginRequiredMiddleware introduced in Django 5.1")
LoginBase = getattr(auth_middleware, "LoginRequiredMiddleware", object)
events = []


class Unrelated:
    def __init__(self, get_response):
        explode()


class First(LoginBase):
    def process_view(self, request, callback, args, kwargs):
        events.append(("first", callback, args, kwargs))
        assert request.build_absolute_uri("/") == "http://localhost/"
        return None


class Second(LoginBase):
    mode = "login"

    def process_view(self, request, callback, args, kwargs):
        events.append(("second", callback, args, kwargs))
        if self.mode == "raise403":
            raise PermissionDenied("middleware refusal")
        if self.mode == "raise404":
            raise Http404("middleware missing")
        if self.mode == "raise500":
            raise ValueError("middleware error")
        if self.mode != "login":
            return HttpResponse(status=int(self.mode))
        response = super().process_view(request, callback, args, kwargs)
        events.append(("response", response))
        return response


class Never(LoginBase):
    def process_view(self, *args):
        explode()


@pytest.fixture
def middleware_route(settings):
    import importlib

    events.clear()
    settings.ALLOWED_HOSTS = []

    def build(sfx):
        vs = ViewSet(model=Publisher, name="middleware" + sfx)
        view = register(DetailView, vs, get=explode)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        obj = Publisher.objects.create(name="object")
        original = view.as_view()

        @wraps(original)
        def decorated(*args, **kwargs):
            explode()

        module = importlib.import_module(settings.ROOT_URLCONF)
        module.urlpatterns.insert(0, path("middleware/<int:pk>/", decorated))
        clear_url_caches()
        yield vs, view, f"/middleware/{obj.pk}/", decorated


@requires_login
@pytest.mark.django_db
@pytest.mark.parametrize("installed,anonymous", [(False, True), (True, True), (True, False)])
def test_installed_real_login_middleware_controls_plain_view(middleware_route, settings, installed, anonymous):
    _, _, url, callback = middleware_route
    settings.MIDDLEWARE = [__name__ + ".Unrelated"] + ([LOGIN] if installed else [])
    result = trace(url, AnonymousUser() if anonymous else _user("middleware"))
    assert result.outcome == ("login_redirect" if installed and anonymous else "allowed")
    login_steps = [s for s in result.steps if s.kind == "login"]
    assert len(login_steps) == int(installed)
    if installed:
        assert result.steps[1] is login_steps[0]
        assert login_steps[0].source == LOGIN + ".process_view"
        if anonymous:
            assert result.decided_by == login_steps[0].n
    assert resolve(url).func is callback


@requires_login
@pytest.mark.django_db
@pytest.mark.parametrize("exempt", [True, False])
def test_callback_metadata_and_configured_subclass_order(middleware_route, settings, exempt):
    _, _, url, callback = middleware_route
    callback.login_required = not exempt
    callback.login_url = "https://login.example/signin/"
    callback.redirect_field_name = "return_to"
    settings.MIDDLEWARE = [__name__ + ".First", __name__ + ".Second"]
    if not exempt:
        settings.MIDDLEWARE.append(__name__ + ".Never")
    result = trace("https://discarded.example" + url + "?ignored=true", AnonymousUser())
    assert result.outcome == ("allowed" if exempt else "login_redirect")
    reached = [s for s in result.steps if s.kind == "login"]
    assert [s.source for s in reached] == [__name__ + ".First.process_view", __name__ + ".Second.process_view"]
    assert [event[0] for event in events] == ["first", "second", "response"]
    assert all(event[1] is callback for event in events[:2])
    match = resolve(url)
    assert events[0][2:] == (match.args, match.kwargs)
    if not exempt:
        response = events[-1][1]
        parts = urlsplit(response["Location"])
        assert parts.netloc == "login.example"
        assert parse_qs(parts.query) == {"return_to": ["http://localhost" + url]}
    assert settings.ALLOWED_HOSTS == []


@requires_login
@pytest.mark.django_db
@pytest.mark.parametrize(
    "mode,outcome",
    [
        ("403", "denied"),
        ("404", "not_found"),
        ("500", "error"),
        ("200", "error"),
        ("raise403", "denied"),
        ("raise404", "not_found"),
        ("raise500", "error"),
    ],
)
def test_subclass_denials_and_errors_keep_login_boundary(middleware_route, settings, monkeypatch, mode, outcome):
    _, view, url, _ = middleware_route
    monkeypatch.setattr(Second, "mode", mode)
    monkeypatch.setattr(view, "setup", explode)
    settings.MIDDLEWARE = [__name__ + ".Second", __name__ + ".Never"]
    result = trace(url, AnonymousUser())
    assert result.outcome == outcome
    step = result.steps[result.decided_by - 1]
    assert step.kind == "login"
    assert step.source == __name__ + ".Second.process_view"
    if outcome == "error":
        assert step.exception["class"] == ("ValueError" if mode == "raise500" else "UnsupportedTraceResponse")


@pytest.mark.django_db
def test_absent_feature_branch_and_fixed_notice(middleware_route, monkeypatch, settings):
    _, _, url, _ = middleware_route
    monkeypatch.delattr(auth_middleware, "LoginRequiredMiddleware", raising=False)
    settings.MIDDLEWARE = [__name__ + ".Unrelated"]
    result = trace(url, AnonymousUser())
    assert result.outcome == "allowed"
    assert not [s for s in result.steps if s.kind == "login"]
    for report in (result, trace("/missing-route/", AnonymousUser())):
        assert "other middleware and URL decorators are not traced" in report.untraced


@requires_login
@pytest.mark.django_db
def test_login_precedes_failing_planning_and_setup(middleware_route, settings, monkeypatch):
    _, view, url, _ = middleware_route
    monkeypatch.setattr(view, "cv_get_requirement", classmethod(explode))
    monkeypatch.setattr(view, "setup", explode)
    settings.MIDDLEWARE = [LOGIN]
    result = trace(url, AnonymousUser())
    assert result.outcome == "login_redirect"
    assert [s.kind for s in result.steps] == ["route", "login"]
    assert "other middleware and URL decorators are not traced" in result.untraced
