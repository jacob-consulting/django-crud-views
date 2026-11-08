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


def _build(family: str, depth: int, sfx: str, viewset_kwargs: dict) -> AncestorRoutes:
    from crud_views.lib.viewset import ParentViewSet, ViewSet

    if family == "core":
        viewset_class = ViewSet
    else:
        from crud_views_guardian.lib.viewset import GuardianViewSet

        viewset_class = GuardianViewSet

    list_base, detail_base, create_bases = _view_classes(family)
    routes = AncestorRoutes(family=family, depth=depth)
    chain = CHAIN[: depth + 1]
    previous = None
    for index, (model, attribute, fields) in enumerate(chain):
        name = f"anc{family[0]}{model._meta.model_name}{sfx}"
        kwargs = dict(model=model, name=name, **viewset_kwargs.get(index, {}))
        if previous is not None:
            kwargs["parent"] = ParentViewSet(name=previous.name, attribute=attribute)
        viewset = viewset_class(**kwargs)
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


@contextmanager
def ancestor_routes(family: str, depth: int, viewset_kwargs: dict | None = None):
    """Build, mount and finally remove one isolated chain; ``viewset_kwargs`` maps level index → extra kwargs."""
    from crud_views.lib import check as check_module
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

    sfx = uuid.uuid4().hex[:8]
    modname = f"tests.test1._ancestor_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    settings_snapshot = dict(crud_views_settings.__dict__)
    names: list[str] = []
    try:
        routes = _build(family, depth, sfx, viewset_kwargs or {})
        names = routes.names
        module = types.ModuleType(modname)
        module.urlpatterns = [pattern for viewset in routes.viewsets for pattern in viewset.urlpatterns]
        module.urlpatterns.append(path("", include("tests.test1.project.urls")))
        sys.modules[modname] = module
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield routes
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            for name in names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        crud_views_settings.__dict__.clear()
        crud_views_settings.__dict__.update(settings_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


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
