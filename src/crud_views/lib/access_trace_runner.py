"""Synthetic GET dispatch for access diagnostics; no real handler or persistent stores."""

from types import MethodType
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.base import BaseStorage
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import Resolver404, resolve
from django.utils.translation import gettext as _
from django.views.generic.list import MultipleObjectMixin

from .access_trace import AccessRecorder, AccessTrace, get_recorder, recording
from .view.base import CrudView


class _MemorySession(SessionBase):
    """SessionBase's mapping API backed only by this request's dictionary."""

    def load(self):
        return {}

    def exists(self, session_key):
        return False

    def create(self):
        self._session_key = self._get_new_session_key()

    def save(self, must_create=False):
        if self.session_key is None:
            self.create()

    def delete(self, session_key=None):
        self._session_key = None


class _MemoryMessages(BaseStorage):
    def _get(self, *args, **kwargs):
        return [], True

    def _store(self, messages, response, *args, **kwargs):
        return []


class _TraceRequest(HttpRequest):
    def __init__(self, path, user):
        super().__init__()
        self.path = self.path_info = path
        self.method = "GET"
        self.META.update(SERVER_NAME="localhost", SERVER_PORT="80", QUERY_STRING="", wsgi_url_scheme="http")
        self.user = user
        self.session = _MemorySession()
        self._messages = _MemoryMessages(self)

    def get_host(self):
        return "localhost"

    def _get_scheme(self):
        return "http"


def _normalize_path(path):
    path = urlsplit(path).path or "/"
    return path if path.startswith("/") else "/" + path


def _fresh_actor(user):
    if user is None or user.is_anonymous:
        return AnonymousUser()
    return get_user_model()._default_manager.db_manager(user._state.db).get(pk=user.pk)


def _resolve_trace_user(identifier):
    model = get_user_model()
    manager = model._default_manager
    try:
        return manager.get(**{model.USERNAME_FIELD: identifier})
    except model.DoesNotExist:
        pass
    try:
        pk = model._meta.pk.to_python(identifier)
    except (ValidationError, ValueError, TypeError):
        return None
    try:
        return manager.get(pk=pk)
    except model.DoesNotExist:
        return None


def _handler_stub(self, request, *args, **kwargs):
    if self.cv_object:
        self.object = self.get_object()
    elif isinstance(self, MultipleObjectMixin):
        self.object_list = self.get_queryset()
        count = self.object_list.count() if isinstance(self.object_list, QuerySet) else len(self.object_list)
        recorder = get_recorder()
        captured = recorder._filters.get(id(self))
        total = None if self.cv_viewset.is_resource else count
        if captured is not None:
            before, _after = captured
            total = before.count() if isinstance(before, QuerySet) else len(before)
        recorder.record(self, "list_filter", result="passed", counts={"visible": count, "total": total})
    return HttpResponse()


def _run_trace(path, user):
    recorder = AccessRecorder()
    trace = AccessTrace(
        path=_normalize_path(path),
        untraced=[
            _("other middleware and URL decorators are not traced"),
            _("the synthetic request uses http://localhost; host-dependent project rules are not reproduced"),
        ],
    )
    with recording(recorder):
        try:
            with transaction.atomic(using="default"):
                try:
                    actor = _fresh_actor(user)
                    trace.user = {
                        "pk": str(actor.pk) if actor.pk is not None else None,
                        "username": str(actor.get_username()) if not actor.is_anonymous else None,
                        "active": bool(actor.is_active),
                        "anonymous": bool(actor.is_anonymous),
                    }
                    match = resolve(trace.path)
                    cls = getattr(match.func, "view_class", None)
                    if cls is None or not issubclass(cls, CrudView):
                        raise Resolver404(trace.path)
                    trace.route = match.view_name
                    trace.view = f"{cls.__module__}.{cls.__qualname__}"
                    recorder.record(recorder, "route", result="passed")
                    view = cls(**match.func.view_initkwargs)
                    view.get = MethodType(_handler_stub, view)
                    request = _TraceRequest(trace.path, actor)
                    request.resolver_match = match
                    view.setup(request, *match.args, **match.kwargs)
                    response = view.dispatch(request, *match.args, **match.kwargs)
                    if response.status_code == 403:
                        trace.outcome = "denied"
                    elif response.status_code == 404:
                        trace.outcome = "not_found"
                    elif response.status_code == 302 and actor.is_anonymous:
                        trace.outcome = "login_redirect"
                    elif response.status_code == 200:
                        trace.outcome = "allowed"
                    else:
                        trace.outcome = "error"
                finally:
                    transaction.set_rollback(True, using="default")
        except Resolver404:
            trace.outcome = "no_such_route"
            recorder.record(recorder, "route", result="not_found")
        except Exception as exc:
            trace.outcome = (
                "denied" if isinstance(exc, PermissionDenied) else "not_found" if isinstance(exc, Http404) else "error"
            )
            if not any(step.result == trace.outcome for step in recorder.steps):
                recorder.record(
                    recorder,
                    "custom_gate",
                    result=trace.outcome,
                    exception={"class": type(exc).__name__, "message": str(exc)},
                )
        finally:
            trace.steps = list(recorder.steps)
            terminal = [step for step in trace.steps if step.result in {"denied", "not_found", "error"}]
            trace.decided_by = terminal[-1].n if terminal else None
            recorder.clear()
    return trace
