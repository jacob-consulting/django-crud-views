"""Shared, isolated route fixtures for the ancestor-authorization suites.

Chains (the endpoint is the last level; every earlier level is an ancestor):

- depth 1: Publisher → Book
- depth 3: Publisher → Book → BookNote → AncestorAttachment

``family="core"`` builds core ViewSets with plain (non-permission) views; ``family="guardian"`` builds
GuardianViewSets with the Guardian permission-required views. Every ViewSet uses a unique name, its own URL module
and a fixed template, and disables navigation actions, so measured requests do not depend on other test modules.
Leaving the context restores the registry, the settings singleton, URL caches and permission vocabulary.
"""

import sys
import types
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.http import HttpResponse
from django.template import Context, Template
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse

from crud_views.lib.viewset import ParentViewSet, ViewSet
from tests.test1.app.models import AncestorAttachment, Book, BookNote, Publisher

# (model, ParentViewSet attribute linking it to the previous level, fields of its create form)
CHAIN = (
    (Publisher, None, ["name"]),
    (Book, "publisher", ["title"]),
    (BookNote, "book", ["note"]),
    (AncestorAttachment, "note", ["text"]),
)

FIXED_TEMPLATE = Template(
    "{% for obj in object_list %}{{ obj.pk }};{% endfor %}|{{ object.pk }}|{% if form %}{{ form.as_p }}{% endif %}"
)


class FixedTemplateMixin:
    """Render one fixed template without context processors or navigation, identical for every mode."""

    cv_context_actions = []
    cv_list_actions = []

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(FIXED_TEMPLATE.render(Context(context)))


@dataclass
class AncestorRoutes:
    family: str
    depth: int
    viewsets: list = field(default_factory=list)  # outermost ancestor first, endpoint last
    names: list = field(default_factory=list)

    @property
    def endpoint(self):
        return self.viewsets[-1]

    @property
    def ancestors(self):
        return self.viewsets[:-1]

    def url(self, key: str, objects: list, obj=None) -> str:
        """Reverse ``key`` on the endpoint; ``objects`` are the ancestor instances, outermost first."""
        kwargs = {}
        parent = self.endpoint.parent
        for ancestor_obj in reversed(objects):
            kwargs[parent.get_pk_name()] = ancestor_obj.pk
            parent = parent.viewset.parent
        if obj is not None:
            kwargs[self.endpoint.pk_name] = obj.pk
        return reverse(self.endpoint.get_router_name(key), kwargs=kwargs)

    def reset_vocabulary(self) -> None:
        """Forget the per-ViewSet permission vocabulary and content types (a cold process)."""
        from django.contrib.contenttypes.models import ContentType

        from crud_views.lib import check as check_module

        ContentType.objects.clear_cache()
        check_module._VOCAB_CACHE.clear()
        for viewset in self.viewsets:
            viewset._default_permissions = None


def _view_classes(family: str):
    from crud_views.lib.views import CreateView, CreateViewParentMixin, DetailView, ListView

    if family == "core":
        return ListView, DetailView, (CreateViewParentMixin, CreateView)
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )

    return (
        GuardianListViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        (CreateViewParentMixin, GuardianCreateViewPermissionRequired),
    )


def _build(family: str, depth: int, scope: "AncestorScope", viewset_kwargs: dict) -> AncestorRoutes:
    from crud_views.lib.viewset import ParentViewSet, ViewSet

    if family == "core":
        viewset_class = ViewSet
    else:
        from crud_views_guardian.lib.viewset import GuardianViewSet

        viewset_class = GuardianViewSet

    list_base, detail_base, create_bases = _view_classes(family)
    routes = AncestorRoutes(family=family, depth=depth)
    chain = CHAIN[: depth + 1]
    sfx = scope.sfx
    previous = None
    for index, (model, attribute, fields) in enumerate(chain):
        name = f"anc{family[0]}{model._meta.model_name}{sfx}"
        kwargs = dict(model=model, name=name, **viewset_kwargs.get(index, {}))
        if previous is not None:
            kwargs["parent"] = ParentViewSet(name=previous.name, attribute=attribute)
        viewset = scope.viewset(viewset_class, **kwargs)
        routes.names.append(name)
        routes.viewsets.append(viewset)

        attrs = {"cv_viewset": viewset, "__module__": __name__}
        type(f"Anc{model.__name__}List{sfx}", (FixedTemplateMixin, list_base), dict(attrs))
        type(f"Anc{model.__name__}Detail{sfx}", (FixedTemplateMixin, detail_base), dict(attrs))
        if index == len(chain) - 1 and previous is not None:
            type(
                f"Anc{model.__name__}Create{sfx}",
                (FixedTemplateMixin, *create_bases),
                {**attrs, "fields": fields},
            )
        previous = viewset
    return routes


@dataclass
class AncestorScope:
    """ViewSets and one URL module created inside ``ancestor_scope()``; all of them are removed on exit.

    A ViewSet's name is recorded as soon as its construction (and thus registration) succeeds, so a scope that fails
    halfway still removes every ViewSet it registered.
    """

    sfx: str
    names: list = field(default_factory=list)
    modname: str | None = None
    _override: object = None

    def name(self, base: str) -> str:
        return f"{base}{self.sfx}"

    def viewset(self, viewset_class=None, **kwargs):
        from crud_views.lib.viewset import ViewSet

        viewset = (viewset_class or ViewSet)(**kwargs)
        self.names.append(viewset.name)
        return viewset

    def view(self, base: type, viewset, name: str | None = None, **attrs) -> type:
        """Define (and so register) a view class of ``viewset`` derived from ``base``."""
        class_name = f"{name or base.__name__}{self.sfx}"
        return type(class_name, (base,), {"cv_viewset": viewset, "__module__": __name__, **attrs})

    def mount(self, viewsets: list) -> None:
        """Use a fresh URL module as ROOT_URLCONF; its ``urlpatterns`` are built lazily when Django resolves them."""
        modname = f"tests.test1._ancestor_urls_{self.sfx}"
        module = types.ModuleType(modname)

        def urlpatterns(name):
            if name != "urlpatterns":
                raise AttributeError(name)
            patterns = [pattern for viewset in viewsets for pattern in viewset.urlpatterns]
            patterns.append(path("", include("tests.test1.project.urls")))
            return patterns

        module.__getattr__ = urlpatterns
        sys.modules[modname] = module
        self.modname = modname
        self._override = override_settings(ROOT_URLCONF=modname)
        self._override.enable()
        clear_url_caches()

    def _unmount(self) -> None:
        if self._override is not None:
            self._override.disable()
            self._override = None
        if self.modname is not None:
            sys.modules.pop(self.modname, None)
        clear_url_caches()


@contextmanager
def ancestor_scope():
    """Isolate registry, settings singleton, URLconf and permission vocabulary for ad-hoc ViewSets."""
    from crud_views.lib import check as check_module
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

    scope = AncestorScope(sfx=uuid.uuid4().hex[:8])
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    settings_snapshot = dict(crud_views_settings.__dict__)
    try:
        yield scope
    finally:
        scope._unmount()
        with _REGISTRY_LOCK:
            for name in scope.names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        crud_views_settings.__dict__.clear()
        crud_views_settings.__dict__.update(settings_snapshot)


@contextmanager
def ancestor_routes(family: str, depth: int, viewset_kwargs: dict | None = None):
    """Build, mount and finally remove one isolated chain; ``viewset_kwargs`` maps level index → extra kwargs."""
    with ancestor_scope() as scope:
        routes = _build(family, depth, scope, viewset_kwargs or {})
        scope.mount(routes.viewsets)
        yield routes


def chain_objects(depth: int) -> tuple[list, list]:
    """Create one instance per ancestor level and two endpoint rows; return (ancestors, endpoint rows)."""
    publisher = Publisher.objects.create(name="Ancestor Publisher")
    book = Book.objects.create(title="Ancestor Book", publisher=publisher)
    if depth == 1:
        rows = [book, Book.objects.create(title="Ancestor Book 2", publisher=publisher)]
        return [publisher], rows
    note = BookNote.objects.create(book=book, note="Ancestor Note")
    rows = [AncestorAttachment.objects.create(note=note, text=f"Attachment {i}") for i in (1, 2)]
    return [publisher, book, note], rows


def grant_all(user, routes: AncestorRoutes, ancestors: list, rows: list) -> None:
    """Grant every permission any mode needs: view/add/change model perms (core) or object perms (Guardian).

    The same grants are used for every measured mode, so baseline and later measurements describe identical
    operations: core gets model ``view``/``add``/``change`` on every chain model; Guardian gets object ``view`` and
    ``change`` on every ancestor object and endpoint row (no model permissions).
    """
    from django.contrib.auth.models import Permission

    if routes.family == "core":
        for viewset in routes.viewsets:
            model_name = viewset.model._meta.model_name
            for action in ("view", "add", "change"):
                user.user_permissions.add(
                    Permission.objects.get(codename=f"{action}_{model_name}", content_type__app_label="app")
                )
        return
    for viewset, obj in zip(routes.ancestors, ancestors, strict=True):
        for action in ("view", "change"):
            viewset.assign_perm(action, user, obj)
    for obj in rows:
        for action in ("view", "change"):
            routes.endpoint.assign_perm(action, user, obj)


# ── traced chains for the request-order suites ────────────────────────────────

# named request events in call order; cleared by the ``events`` fixture of the request suites
EVENTS: list[str] = []
# (trace, fully qualified permission) of every ancestor gate evaluation, in call order
CHECKED: list[tuple[str, str]] = []


class TracedViewSet(ViewSet):
    """A ViewSet recording its queryset calls (``<trace>_queryset``; the endpoint's as ``child``) and its ancestor
    gate evaluations (``<trace>_gate``) in ``EVENTS``; the evaluated permission also goes to ``CHECKED``."""

    trace: str = ""

    def get_queryset(self, view):
        EVENTS.append("child" if self.trace == "child" else f"{self.trace}_queryset")
        return super().get_queryset(view)

    def _ancestor_has_permission(self, user, obj, permission):
        EVENTS.append(f"{self.trace}_gate")
        CHECKED.append((self.trace, permission))
        return super()._ancestor_has_permission(user, obj, permission)


def traced_chain(
    scope: "AncestorScope", spec, policies: dict | None = None, viewset_classes: dict | None = None, prefix: str = ""
):
    """Register one traced ViewSet per ``(model, parent attribute, trace)`` of ``spec`` (outermost first, endpoint
    last); ``policies`` / ``viewset_classes`` map a level index to its ``AncestorPolicy`` / ViewSet class and
    ``prefix`` keeps the names of several chains in one scope apart."""
    policies = policies or {}
    viewset_classes = viewset_classes or {}
    viewsets = []
    for index, (model, attribute, trace) in enumerate(spec):
        kwargs = {"model": model, "name": scope.name(f"tr{prefix}{trace}"), "trace": trace}
        if viewsets:
            kwargs["parent"] = ParentViewSet(name=viewsets[-1].name, attribute=attribute)
        if index in policies:
            kwargs["ancestor_policy"] = policies[index]
        viewsets.append(scope.viewset(viewset_classes.get(index, TracedViewSet), **kwargs))
    return AncestorRoutes(family="core", depth=len(spec) - 1, viewsets=viewsets)
