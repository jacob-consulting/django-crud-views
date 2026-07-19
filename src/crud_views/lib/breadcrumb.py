"""
Breadcrumb support for CrudViews.

BreadcrumbItem/Breadcrumb are late-resolving: items carry a URL pattern *name* plus
args/kwargs and are resolved to concrete URLs only when rendered.
"""

from typing import Any, Dict, Iterable, List, Tuple

from django.core.checks import CheckMessage, Warning as CheckWarning
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.urls import reverse
from pydantic import BaseModel, field_validator, model_validator

from crud_views.lib.check import Check
from crud_views.lib.exceptions import CrudViewError, cv_raise
from crud_views.lib.settings import crud_views_settings


class BreadcrumbItem(BaseModel):
    title: str
    url_name: str | None = None  # Django URL pattern name, resolved late via reverse()
    args: tuple = ()
    kwargs: dict = {}

    @field_validator("title", mode="before")
    @classmethod
    def coerce_title(cls, value: Any) -> str:
        # accept gettext_lazy promises
        return str(value)

    @model_validator(mode="after")
    def check_url_arguments(self) -> "BreadcrumbItem":
        if self.url_name is None:
            self.args = ()
            self.kwargs = {}
        elif self.args and self.kwargs:
            raise ValueError("BreadcrumbItem accepts args or kwargs, not both (reverse() restriction)")
        return self

    def resolve(self) -> Dict[str, str | None]:
        if self.url_name is None:
            url = None
        else:
            url = reverse(self.url_name, args=self.args or None, kwargs=self.kwargs or None)
        return {"title": self.title, "url": url}


class Breadcrumb(BaseModel):
    items: Tuple[BreadcrumbItem, ...] = ()

    def resolve_items(self) -> List[Dict[str, str | None]]:
        return [item.resolve() for item in self.items]


class CheckBreadcrumbKeyObject(Check):
    """Warn when an overridden cv_breadcrumb_key_object names an unregistered view key."""

    id: str = "W270"
    key: str
    default_key: str
    msg: str = (
        "cv_breadcrumb_key_object »{key}« is not registered at »{context}« — "
        "object breadcrumb items will render without a link (typo?)"
    )

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(key=self.key)
        return context

    def messages(self) -> Iterable[CheckMessage]:
        if self.key == self.default_key:
            return  # default with a missing detail view is a legitimate configuration
        if not self.context.cv_viewset.is_view_registered(self.key):
            yield CheckWarning(id=self.get_id(), msg=self.get_message())


class CrudViewBreadcrumbMixin:
    """
    Adds a Breadcrumb to the view context as ``cv_breadcrumb``, built from the
    ViewSet hierarchy: [prefix items] › (ancestors …) › container › object › action.
    Render it with the ``{% cv_breadcrumb %}`` template tag.
    """

    cv_breadcrumb_key_object: str = "detail"  # view key object items link to
    cv_breadcrumb_container_label: str | None = None  # overrides the container (list/card) label

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()  # noqa
        yield CheckBreadcrumbKeyObject(
            context=cls,
            key=cls.cv_breadcrumb_key_object,
            default_key=CrudViewBreadcrumbMixin.cv_breadcrumb_key_object,
        )

    # -- extension points -------------------------------------------------

    def cv_breadcrumb_prefix(self) -> List[BreadcrumbItem]:
        """Items prepended to the trail; default reads CRUD_VIEWS_BREADCRUMB_PREFIX."""
        return [BreadcrumbItem.model_validate(entry) for entry in crud_views_settings.breadcrumb_prefix]

    def cv_breadcrumb_object_label(self, obj) -> str:
        """Label for an object item; override to avoid expensive __str__ implementations."""
        return str(obj)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def cv_breadcrumb_container_key(viewset) -> str | None:
        """The viewset's container view key: "list", falling back to "card", else None."""
        for key in ("list", "card"):
            if viewset.is_view_registered(key):
                return key
        return None

    def _cv_breadcrumb_container_label(self, viewset, context) -> str:
        # the label override lives on the viewset's own container view class, so it
        # also applies when this viewset appears as an ancestor of a child view
        key = self.cv_breadcrumb_container_key(viewset)
        if key is not None:
            label = getattr(viewset.get_view_class(key), "cv_breadcrumb_container_label", None)
            if label:
                return str(label)
        return viewset.get_meta(context)["verbose_name_plural_translate"]

    # -- trail building ---------------------------------------------------

    def cv_breadcrumb(self) -> Breadcrumb:
        """Cached accessor; the trail is built at most once per view instance/request."""
        if not hasattr(self, "_cv_breadcrumb_cache"):
            self._cv_breadcrumb_cache = self.cv_breadcrumb_get()
        return self._cv_breadcrumb_cache

    def cv_breadcrumb_get(self) -> Breadcrumb:
        obj = getattr(self, "object", None)
        context = self.cv_get_view_context(object=obj)  # noqa
        viewset = self.cv_viewset
        items: List[BreadcrumbItem] = []

        # 1. own-view segment, innermost first (reversed at the end)
        if self.cv_object:  # noqa
            has_detail = viewset.is_view_registered(self.cv_breadcrumb_key_object)
            if has_detail and self.cv_key != self.cv_breadcrumb_key_object:  # noqa
                # action label (current page) + object item linking to the detail view
                name, _, kwargs = self.cv_get_router_and_args(self.cv_key, obj=obj)  # noqa
                items.append(
                    BreadcrumbItem(title=self.cv_get_action_short_label(context=context), url_name=name, kwargs=kwargs)
                )
                name, _, kwargs = self.cv_get_router_and_args(self.cv_breadcrumb_key_object, obj=obj)  # noqa
                items.append(BreadcrumbItem(title=self.cv_breadcrumb_object_label(obj), url_name=name, kwargs=kwargs))
            elif has_detail:
                # this IS the detail view: object item only
                name, _, kwargs = self.cv_get_router_and_args(self.cv_breadcrumb_key_object, obj=obj)  # noqa
                items.append(BreadcrumbItem(title=self.cv_breadcrumb_object_label(obj), url_name=name, kwargs=kwargs))
            else:
                # no detail view: action label (current page) + unlinked object item
                name, _, kwargs = self.cv_get_router_and_args(self.cv_key, obj=obj)  # noqa
                items.append(
                    BreadcrumbItem(title=self.cv_get_action_short_label(context=context), url_name=name, kwargs=kwargs)
                )
                items.append(BreadcrumbItem(title=self.cv_breadcrumb_object_label(obj)))
        else:
            container_key = self.cv_breadcrumb_container_key(viewset)
            if self.cv_key != container_key:  # noqa
                items.append(BreadcrumbItem(title=self.cv_get_action_short_label(context=context)))

        # container item of this viewset
        container_key = self.cv_breadcrumb_container_key(viewset)
        if container_key is not None:
            name, _, kwargs = self.cv_get_router_and_args(container_key, obj=obj)  # noqa
            items.append(
                BreadcrumbItem(
                    title=self._cv_breadcrumb_container_label(viewset, context), url_name=name, kwargs=kwargs
                )
            )

        # 2. ancestor segments (Task 4)
        items.extend(self._cv_breadcrumb_ancestors(context))

        items.reverse()
        return Breadcrumb(items=tuple(self.cv_breadcrumb_prefix()) + tuple(items))

    def _cv_breadcrumb_ancestors(self, context) -> List[BreadcrumbItem]:
        """
        Items for the ancestor chain, innermost ancestor first (caller reverses).
        Costs one scoped query per ancestor level; results are part of the per-request
        breadcrumb cache (cv_breadcrumb).
        """
        viewset = self.cv_viewset
        items: List[BreadcrumbItem] = []

        parents = []
        parent = viewset.parent
        while parent is not None:
            parents.append(parent)
            parent = parent.viewset.parent
        if not parents:
            return items

        # URL kwarg names of the ancestor chain, outermost first
        arg_names = viewset.get_parent_url_args()
        arg_names.reverse()
        cv_raise(
            len(parents) == len(arg_names),
            f"breadcrumb ancestor chain mismatch at {viewset!r}: "
            f"{len(parents)} parents but {len(arg_names)} parent url args",
            CrudViewError,
        )
        arg_values = [self.kwargs[name] for name in arg_names]  # noqa

        # innermost ancestor first: parents[0] is the immediate parent
        for i, parent in enumerate(parents):
            x = len(parents) - i
            chain_names, chain_values = arg_names[:x], arg_values[:x]
            ancestor_pk = chain_values[-1]

            # scoped fetch: parent.viewset.get_queryset(view) filters by the ancestor's
            # own parent pks from this view's url kwargs, so a tampered pk combination
            # 404s instead of leaking a foreign object's label
            try:
                ancestor = parent.viewset.get_queryset(view=self).get(pk=ancestor_pk)
            except ObjectDoesNotExist:
                raise Http404(f"breadcrumb ancestor {parent.viewset.name}={ancestor_pk!r} not found")

            grand_kwargs = dict(zip(chain_names[:-1], chain_values[:-1]))

            # ancestor object item, linked to its detail view when registered
            if parent.viewset.is_view_registered(self.cv_breadcrumb_key_object):
                item_kwargs = dict(grand_kwargs)
                item_kwargs[parent.viewset.pk_name] = ancestor_pk
                items.append(
                    BreadcrumbItem(
                        title=self.cv_breadcrumb_object_label(ancestor),
                        url_name=parent.viewset.get_router_name(self.cv_breadcrumb_key_object),
                        kwargs=item_kwargs,
                    )
                )
            else:
                items.append(BreadcrumbItem(title=self.cv_breadcrumb_object_label(ancestor)))

            # ancestor container item (list/card)
            container_key = self.cv_breadcrumb_container_key(parent.viewset)
            if container_key is not None:
                items.append(
                    BreadcrumbItem(
                        title=self._cv_breadcrumb_container_label(parent.viewset, context),
                        url_name=parent.viewset.get_router_name(container_key),
                        kwargs=grand_kwargs,
                    )
                )
        return items

    # -- django integration ----------------------------------------------

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # noqa
        context["cv_breadcrumb"] = self.cv_breadcrumb()
        return context
