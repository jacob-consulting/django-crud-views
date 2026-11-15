"""Optional, context-local observations. Importable before Django configuration.

Gates remain the authority: this module only records results they already computed.
The public trace contains scalar values; private owners and querysets are discarded
when a trace is assembled.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field


@dataclass
class AccessStep:
    n: int
    kind: str
    viewset: str | None = None
    object: dict | None = None
    key: str | None = None
    permission: str | None = None
    group: str | None = None
    provider: str | None = None
    source: str | None = None
    result: str | None = None
    how: str | None = None
    message: str | None = None
    exception: dict | None = None
    counts: dict | None = None


@dataclass
class AccessTrace:
    path: str
    route: str | None = None
    view: str | None = None
    user: dict = field(default_factory=dict)
    outcome: str = "error"
    decided_by: int | None = None
    plan: list = field(default_factory=list)
    steps: list[AccessStep] = field(default_factory=list)
    untraced: list[str] = field(default_factory=list)
    version: int = field(default=1, init=False)

    def to_dict(self):
        return asdict(self)


def _object_identity(obj):
    """Use only PK and class metadata, never object formatting or deferred fields."""
    if obj is None:
        return None
    meta = type(obj)._meta
    pk_field = getattr(meta, "pk", None)
    pk = obj.__dict__.get(pk_field.attname) if pk_field is not None else obj.pk
    model = getattr(meta, "label_lower", None) or f"{meta.app_label}.{type(obj).__name__.lower()}"
    return {"model": model, "pk": str(pk) if pk is not None else None}


class AccessRecorder:
    def __init__(self):
        self.steps = []
        self._owners = {}
        self._seen = []
        self._filters = {}

    def record(self, owner, kind, **facts):
        """Record scalar facts once per owner and identical report, never cache a gate."""
        self._owners[id(owner)] = owner
        viewset = getattr(owner, "cv_viewset", None)
        if viewset is not None:
            facts.setdefault("viewset", viewset.name)
        step = AccessStep(n=0, kind=kind, **facts)
        projection = asdict(step)
        identity = (id(owner), projection)
        if identity in self._seen:
            return None
        self._seen.append(identity)
        step.n = len(self.steps) + 1
        self.steps.append(step)
        return step

    def capture_filter(self, owner, before, after):
        """Retain unevaluated references; only the explicit trace stub counts them."""
        self._owners[id(owner)] = owner
        self._filters[id(owner)] = (before, after)

    def clear(self):
        self._owners.clear()
        self._seen.clear()
        self._filters.clear()


_recorder = ContextVar("crud_views_access_recorder", default=None)


def get_recorder():
    return _recorder.get()


@contextmanager
def recording(recorder):
    token = _recorder.set(recorder)
    try:
        yield recorder
    finally:
        _recorder.reset(token)


def trace_access(path, user):
    from .access_trace_runner import _run_trace

    return _run_trace(path, user)


def resolve_trace_user(identifier):
    from .access_trace_runner import _resolve_trace_user

    return _resolve_trace_user(identifier)
