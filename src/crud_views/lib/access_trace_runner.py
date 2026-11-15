"""Synthetic GET dispatch for access diagnostics; no real handler or persistent stores."""

from types import MethodType
from urllib.parse import unquote_to_bytes, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.base import BaseStorage
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.urls import Resolver404, resolve
from django.utils.encoding import repercent_broken_unicode
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from django.views.generic.list import MultipleObjectMixin

from .access_trace import AccessRecorder, AccessTrace, get_recorder, recording
from .view.base import CrudView, CrudViewPermissionRequiredMixin


def _plan_gates(view):
    """Declaration-only projection. Unavailable metadata never decides dispatch."""
    from .ancestors import _effective_provider, _requirement_source, _selected_gates, _validate_ancestor_structure

    plan = []
    vs = view.cv_viewset
    try:
        if vs.parent is not None:
            chain = _validate_ancestor_structure(vs)
            source, pair = _requirement_source(type(view))
            selected = _selected_gates(vs, chain)
            for index in reversed(range(len(chain))):
                if index not in selected:
                    continue
                edge, ancestor = chain[index]
                pk = view.kwargs.get(edge.get_pk_name())
                plan.append(
                    {
                        "kind": "ancestor_gate",
                        "viewset": ancestor.name,
                        "object": {
                            "model": ancestor.model._meta.label_lower,
                            "pk": str(pk) if pk is not None else None,
                        },
                        "key": getattr(pair, selected[index]),
                        "source": source,
                        "provider": _effective_provider(ancestor),
                        "permission": None,
                    }
                )
    except Exception as exc:
        plan.append(
            {
                "kind": "validation",
                "viewset": vs.name,
                "result": "unavailable",
                "exception": {"class": type(exc).__name__, "message": str(exc)},
            }
        )
    try:
        requirement = view.cv_get_requirement()
        kind = requirement["kind"]
        identity = None
        if view.cv_object:
            meta = vs.model._meta
            pk = view.kwargs.get(vs.pk_name)
            identity = {
                "model": getattr(meta, "label_lower", None) or f"{meta.app_label}.{vs.model.__name__.lower()}",
                "pk": str(pk) if pk is not None else None,
            }
        if kind != "none":
            plan.append(
                {
                    "kind": {"permission": "own_permission", "group": "manage_gate"}.get(kind, "custom_gate"),
                    "viewset": vs.name,
                    "object": identity,
                    "key": requirement["value"] if kind == "permission" else None,
                    "group": requirement["value"] if kind == "group" else None,
                    "permission": None,
                    "source": f"{type(view).__module__}.{type(view).__qualname__}.cv_get_requirement",
                }
            )
        if isinstance(view, CrudViewPermissionRequiredMixin):
            plan.append(
                {
                    "kind": "action_state",
                    "viewset": vs.name,
                    "object": identity,
                    "source": "CrudViewPermissionRequiredMixin.has_permission",
                }
            )
    except Exception as exc:
        plan.append(
            {
                "kind": "own_permission",
                "viewset": vs.name,
                "result": "unavailable",
                "exception": {"class": type(exc).__name__, "message": str(exc)},
            }
        )
    return plan


def _merge_plan(recorder, plan):
    """Append unvisited requirements after observations; never manufacture a decision."""
    for row in plan:
        if row.get("result") == "unavailable":
            continue
        matches = [step for step in recorder.steps if step.kind == row["kind"] and step.viewset == row["viewset"]]
        if not matches:
            recorder.record(recorder, **row, result="not_reached")


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
    # Split before decoding: encoded ?/# belong to the path. Like Django's WSGI
    # request boundary, retain invalid UTF-8 as escapes and decode exactly once.
    path = repercent_broken_unicode(unquote_to_bytes(path)).decode()
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
    except (model.DoesNotExist, ValidationError, ValueError, TypeError):
        # A typed USERNAME_FIELD may reject an otherwise valid primary key.
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
    self._cv_trace_stub_completed = True
    return HttpResponse()


class UnsupportedTraceResponse(Exception):
    """The observed dispatch did not establish one of the supported outcomes."""


def _terminal_since(recorder, cursor=0):
    return [step for step in recorder.steps[cursor:] if step.result in {"denied", "not_found", "error"}]


def _exception_outcome(exc):
    return "denied" if isinstance(exc, PermissionDenied) else "not_found" if isinstance(exc, Http404) else "error"


def _method_source(view, name, bound):
    """Name the actual bound callable's definer, never guess an inner super frame."""
    function = getattr(bound, "__func__", bound)
    for cls in type(view).__mro__:
        if cls.__dict__.get(name) is function:
            return f"{cls.__module__}.{cls.__qualname__}.{name}"
    return f"{function.__module__}.{function.__qualname__}"


def _observe_custom_methods(view, recorder):
    """Observe calls through the instance; super() continues along its original MRO."""

    def wrap(name, bound):
        source = _method_source(view, name, bound)

        def observe(*args, **kwargs):
            cursor = len(recorder.steps)
            try:
                value = bound(*args, **kwargs)
            except Exception as exc:
                report(cursor, _exception_outcome(exc))
                raise
            result = None
            if name == "has_permission" and value is False:
                result = "denied"
            elif isinstance(value, HttpResponseBase):
                result = {403: "denied", 404: "not_found"}.get(value.status_code)
            if result is not None:
                report(cursor, result)
            return value

        def report(cursor, result):
            if not _terminal_since(recorder, cursor):
                recorder.record(
                    view,
                    "custom_gate",
                    result=result,
                    source=source,
                    how="observed_boundary",
                    message=_(
                        "This observed method boundary refused access; the inner denying implementation is unknown."
                    ),
                )

        return observe

    for name in ("has_permission", "get_object", "dispatch"):
        bound = getattr(view, name, None)
        if callable(bound):
            setattr(view, name, wrap(name, bound))


def _observe_denial_response(view, recorder):
    bound = getattr(view, "handle_no_permission", None)
    if getattr(bound, "__func__", None) is not AccessMixin.handle_no_permission:
        return

    def observe(*args, **kwargs):
        response = bound(*args, **kwargs)
        recorder.capture_login_response(view, response)
        if not _terminal_since(recorder):
            recorder.record(
                view,
                "actor_admission",
                result="denied",
                source=_method_source(view, "handle_no_permission", bound),
                message=_("Django's inherited access handler returned a login response."),
            )
        return response

    view.handle_no_permission = observe


def _classify_response(response, view, recorder):
    status = response.status_code if isinstance(response, HttpResponseBase) else None
    if status == 403:
        return "denied"
    if status == 404:
        return "not_found"
    if (
        status is not None
        and 300 <= status < 400
        and any(response is captured for captured in recorder._login_responses.values())
    ):
        return "login_redirect"
    if (
        status is not None
        and 200 <= status < 300
        and getattr(view, "_cv_trace_stub_completed", False)
        and not _terminal_since(recorder)
    ):
        return "allowed"
    raise UnsupportedTraceResponse(
        _("Unsupported trace response (status %(status)s): no successful stub or recognized terminal response.")
        % {"status": status}
    )


def _run_login_middleware(request, match, recorder):
    try:
        from django.contrib.auth.middleware import LoginRequiredMiddleware
    except ImportError:  # Django 4.2 has no login middleware.
        return None
    for dotted_path in settings.MIDDLEWARE:
        cls = import_string(dotted_path)
        if not isinstance(cls, type) or not issubclass(cls, LoginRequiredMiddleware):
            continue
        middleware = cls(lambda request: HttpResponse())
        source = _method_source(middleware, "process_view", middleware.process_view)
        try:
            response = middleware.process_view(request, match.func, match.args, match.kwargs)
            if response is None:
                result = "passed"
            else:
                if isinstance(response, HttpResponseBase) and 300 <= response.status_code < 400:
                    recorder.capture_login_response(middleware, response)
                result = _classify_response(response, None, recorder)
                if result == "login_redirect":
                    result = "denied"
        except Exception as exc:
            recorder.record(middleware, "login_middleware", result=_exception_outcome(exc), source=source)
            raise
        recorder.record(middleware, "login_middleware", result=result, source=source)
        if response is not None:
            return response
    return None


def _add_limitations(cls, recorder):
    """Describe handler families using declarations only, even when dispatch denied."""
    from .views.action import ActionView
    from .views.delete import DeleteView
    from .views.mixins import CrudViewProcessFormMixin

    vs = cls.cv_viewset
    nested = vs.parent is not None and not vs.is_resource

    def note(key, message):
        recorder.record(recorder, "limitation", viewset=vs.name, key=key, result="not_evaluated", message=message)

    if issubclass(cls, ActionView) or ("post" in cls.http_method_names and "get" not in cls.http_method_names):
        note(
            "method",
            _(
                "Authorization uses a synthetic GET stub; "
                "the POST handler and method-sensitive behavior are not evaluated."
            ),
        )
    if any(
        base.__module__ == "crud_views_workflow.lib.views" and base.__name__ == "WorkflowView" for base in cls.__mro__
    ):
        note("workflow_transition", _("Workflow transition permissions are checked on submit and are not evaluated."))
    if nested and issubclass(cls, MultipleObjectMixin):
        note("nested_list_database", _("Nested-list database configuration is checked when the page is built."))
    if issubclass(cls, DeleteView):
        note("delete_preview", _("Delete-preview configuration is checked when the page is built."))
    if nested and issubclass(cls, (CrudViewProcessFormMixin, ActionView)):
        note("write_database", _("Write database configuration is checked on submit and is not evaluated."))


def _run_trace(path, user):
    recorder = AccessRecorder()
    traced_class = None
    trace = AccessTrace(
        path=path,
        untraced=[
            _("other middleware and URL decorators are not traced"),
            _("the synthetic request uses http://localhost; host-dependent project rules are not reproduced"),
        ],
    )
    with recording(recorder):
        try:
            trace.path = _normalize_path(path)
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
                    traced_class = cls
                    trace.route = match.view_name
                    trace.view = f"{cls.__module__}.{cls.__qualname__}"
                    recorder.record(recorder, "route", result="passed")
                    request = _TraceRequest(trace.path, actor)
                    request.resolver_match = match
                    view = None
                    response = _run_login_middleware(request, match, recorder)
                    if response is None:
                        view = cls(**match.func.view_initkwargs)
                        view.get = MethodType(_handler_stub, view)
                        view.setup(request, *match.args, **match.kwargs)
                        view.get = MethodType(_handler_stub, view)
                        if "post" in view.http_method_names and "get" not in view.http_method_names:
                            view.http_method_names = [*view.http_method_names, "get"]
                        view._cv_trace_stub_completed = False
                        _observe_custom_methods(view, recorder)
                        _observe_denial_response(view, recorder)
                        trace.plan = _plan_gates(view)
                        response = view.dispatch(request, *match.args, **match.kwargs)
                    trace.outcome = _classify_response(response, view, recorder)
                finally:
                    transaction.set_rollback(True, using="default")
        except Resolver404:
            trace.outcome = "no_such_route"
            recorder.record(recorder, "route", result="not_found")
        except Exception as exc:
            # Normalize only after atomic has restored a usable outer transaction.
            trace.outcome = _exception_outcome(exc)
            exception = {"class": type(exc).__name__, "message": str(exc)}
            terminal = _terminal_since(recorder)
            if terminal and terminal[-1].result == trace.outcome:
                terminal[-1].exception = exception
            else:
                recorder.record(
                    recorder,
                    "custom_gate",
                    result=trace.outcome,
                    exception=exception,
                )
        finally:
            _merge_plan(recorder, trace.plan)
            if traced_class is not None:
                _add_limitations(traced_class, recorder)
            if trace.outcome == "allowed":
                trace.untraced.append(
                    _("Allowed means this user may open the page; handler-phase checks are not evaluated.")
                )
            trace.steps = list(recorder.steps)
            terminal = _terminal_since(recorder)
            trace.decided_by = terminal[-1].n if terminal else None
            recorder.clear()
    return trace
