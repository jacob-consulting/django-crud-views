"""Opt-in object section navigation; declarations contain configuration only."""

from html import unescape

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.functional import Promise, SimpleLazyObject
from pydantic import BaseModel

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


def _build(view):
    bar = view.cv_navbar
    owner_viewset = ViewSet.get_viewset(bar.viewset)
    owner = getattr(view, "object", None)
    if owner is None or view.cv_viewset is not owner_viewset:
        raise ImproperlyConfigured(f"{type(view).__name__}: navbar owner {bar.viewset!r} is not resolved")
    context = ViewContext(view=view, object=owner)
    items = []
    for item in bar.items:
        if not item.key or not owner_viewset.is_view_registered(item.key):
            raise ImproperlyConfigured(f"Navbar {bar.viewset!r}: unregistered owner key {item.key!r}")
        target = owner_viewset.get_view_class(item.key)
        if not target.cv_has_access(view.request.user, owner):
            continue
        if not target._cv_action_enabled_for_rendering(view.request.user, owner, view):
            continue
        kwargs = dict(target.cv_get_url_extra_kwargs())
        kwargs[owner_viewset.pk_name] = owner.pk
        label = (
            _plain(item.label)
            if item.label is not None
            else _plain(unescape(target.cv_get_action_short_label(context)))
        )
        items.append(
            {
                "label": label,
                "icon": item.icon if item.icon is not None else target.cv_icon_action,
                "url": reverse(owner_viewset.get_router_name(item.key), kwargs=kwargs),
                "active": view.cv_key == item.key,
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


class CrudViewNavBarMixin:
    """Attach a declaration per view; build it only when a template consumes it."""

    cv_navbar: NavBar | None = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.cv_navbar is None or cv_is_modal_request(self.request):
            context["cv_navbar"] = None
        else:
            if not hasattr(self, "_cv_navbar_data"):
                self._cv_navbar_data = SimpleLazyObject(lambda: _build(self))
            context["cv_navbar"] = self._cv_navbar_data
        return context
