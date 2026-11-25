"""Opt-in object section navigation; declarations contain configuration only."""

from html import unescape

from django.core.checks import Error
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils.functional import Promise, SimpleLazyObject
from pydantic import BaseModel

from crud_views.lib.ancestors import _resolved_ancestor, _walk_ancestors
from crud_views.lib.check import Check
from crud_views.lib.exceptions import ViewSetNotFoundError
from crud_views.lib.link_access import _LINK_ALLOWED, _known_link_ancestors, _link_access
from crud_views.lib.view.base import cv_is_modal_request
from crud_views.lib.view.context import ViewContext
from crud_views.lib.viewset import ViewSet


class NavItem(BaseModel, arbitrary_types_allowed=True):
    key: str | None = None
    child: str | None = None
    label: str | Promise | None = None
    icon: str | None = None


class NavBar(BaseModel):
    viewset: str
    items: list[NavItem]
    template: str | None = None


def _plain(value) -> str:
    """Drop HTML safety without interpreting raw text as entities or markup."""
    return str.__str__(str(value))


def _section(viewset, owner_name):
    """The direct child on this attachment's ancestry path, or None on the owner."""
    if viewset.name == owner_name:
        return None
    child = viewset
    for _, ancestor in _walk_ancestors(viewset):
        if ancestor.name == owner_name:
            return child.name
        child = ancestor
    raise ImproperlyConfigured(f"ViewSet {viewset.name!r} is outside navbar owner {owner_name!r}")


def _destination(owner_viewset, item):
    target_viewset = ViewSet.get_viewset(item.child) if item.child is not None else owner_viewset
    if item.child is not None:
        if target_viewset.parent is None or target_viewset.parent.name != owner_viewset.name:
            raise ImproperlyConfigured(f"child {item.child!r} is not a direct child of {owner_viewset.name!r}")
        key = item.key
        if key is None:
            key = next((key for key in ("list", "card") if target_viewset.is_view_registered(key)), None)
    else:
        key = item.key
    if not key or not target_viewset.is_view_registered(key):
        raise ImproperlyConfigured(f"unregistered destination key {key!r} on {target_viewset.name!r}")
    target = target_viewset.get_view_class(key)
    if "get" not in target.http_method_names or not callable(getattr(target, "get", None)):
        raise ImproperlyConfigured(f"destination {key!r} cannot handle GET")
    if bool(target.cv_object) != (item.child is None):
        raise ImproperlyConfigured(
            f"destination {key!r} must {'require' if item.child is None else 'not require'} an object"
        )
    return target_viewset, key, target


def _build(view):
    bar = view.cv_navbar
    owner_viewset = ViewSet.get_viewset(bar.viewset)
    section = _section(view.cv_viewset, bar.viewset)
    owner = getattr(view, "object", None) if section is None else _resolved_ancestor(view, bar.viewset)
    if owner is None:
        raise ImproperlyConfigured(f"{type(view).__name__}: navbar owner {bar.viewset!r} is not resolved")
    context = ViewContext(view=view, object=owner)
    items = []
    for item in bar.items:
        target_viewset, key, target = _destination(owner_viewset, item)
        if item.child is None:
            known = _known_link_ancestors(target, view)
        else:
            known = _known_link_ancestors(target, view, immediate_parent=owner)
        if (
            _link_access(
                target,
                view.request.user,
                owner if item.child is None else None,
                known,
                rendering_view=view if target_viewset is view.cv_viewset else None,
            )
            != _LINK_ALLOWED
        ):
            continue
        kwargs = dict(target.cv_get_url_extra_kwargs())
        kwargs.update(
            {edge.get_pk_name(): view.kwargs[edge.get_pk_name()] for edge, _ in _walk_ancestors(owner_viewset)}
        )
        kwargs[owner_viewset.pk_name if item.child is None else target_viewset.parent.get_pk_name()] = owner.pk
        if item.label is not None:
            label = _plain(item.label)
        elif item.child is not None:
            label = _plain(target_viewset.get_meta(context)["verbose_name_plural_translate"])
        else:
            label = _plain(unescape(target.cv_get_action_short_label(context)))
        items.append(
            {
                "label": label,
                "icon": item.icon
                if item.icon is not None
                else (target.cv_icon_action if item.child is None else target_viewset.icon_header),
                "url": reverse(target_viewset.get_router_name(key), kwargs=kwargs),
                "active": (section is None and item.child is None and view.cv_key == key)
                or (section is not None and section == item.child),
            }
        )
    if not items:
        return None
    return {
        "object": owner,
        "label": _plain(owner),
        "icon": owner_viewset.icon_header,
        "items": items,
        "template": bar.template,
    }


class _CheckNavBar(Check):
    """Cooperative, metadata-only checks. E280-E284 are navbar-owned diagnostics."""

    id: str = "E280"

    def messages(self):
        from crud_views.checks import _url_configuration_loaded

        cls = self.context
        bar = cls.cv_navbar

        def error(code, scope, message):
            owner = repr(bar.viewset) if isinstance(bar, NavBar) else "<invalid>"
            return Error(f"{cls.__name__}: navbar {owner} {scope}: {message}", obj=cls, id=f"viewset.{code}")

        if not isinstance(bar, NavBar):
            yield error("E280", "bar", "cv_navbar must be a NavBar declaration or None")
            return
        if not bar.viewset or not bar.viewset.strip():
            yield error("E280", "bar", "owner name must be nonempty")
            return
        if bar.template:
            try:
                get_template(bar.template)
            except TemplateDoesNotExist:
                yield error("E284", "bar", f"template {bar.template!r} does not exist")
        if cls.cv_viewset.name == bar.viewset and not cls.cv_object:
            yield error("E281", "bar", "owner attachment must require an object")

        owner_keys, children = set(), set()
        valid_items = []
        for index, item in enumerate(bar.items):
            scope = f"item {index} (key={item.key!r}, child={item.child!r})"
            if (item.key is not None and not item.key.strip()) or (item.child is not None and not item.child.strip()):
                yield error("E280", scope, "supplied destination names and keys must be nonempty")
                continue
            if item.key is None and item.child is None:
                yield error("E280", scope, "select an owner key or direct child name")
                continue
            seen, value = (owner_keys, item.key) if item.child is None else (children, item.child)
            if value in seen:
                yield error("E283", scope, "repeated owner key or child ViewSet")
            seen.add(value)
            valid_items.append((scope, item))

        # Local declaration checks remain useful during a failed/in-progress import.
        # Never retry that import while the caller is iterating live view registries.
        if not _url_configuration_loaded(load=False):
            return
        try:
            owner = ViewSet.get_viewset(bar.viewset)
        except ViewSetNotFoundError:
            yield error("E282", "bar", "unknown owner ViewSet")
            return
        try:
            _section(cls.cv_viewset, bar.viewset)
        except ImproperlyConfigured as exc:
            yield error("E281", "bar", str(exc))
        for scope, item in valid_items:
            try:
                _destination(owner, item)
            except ViewSetNotFoundError:
                yield error("E282", scope, "unknown child ViewSet")
            except ImproperlyConfigured as exc:
                yield error("E282", scope, str(exc))


class CrudViewNavBarMixin:
    """Attach a declaration per view; build it only when a template consumes it."""

    cv_navbar: NavBar | None = None

    @classmethod
    def checks(cls):
        yield from super().checks()
        if cls.cv_navbar is not None:
            yield _CheckNavBar(context=cls)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.cv_navbar is None or cv_is_modal_request(self.request):
            context["cv_navbar"] = None
        else:
            if not hasattr(self, "_cv_navbar_data"):
                self._cv_navbar_data = SimpleLazyObject(lambda: _build(self))
            context["cv_navbar"] = self._cv_navbar_data
        return context
