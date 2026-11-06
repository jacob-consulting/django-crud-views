from __future__ import annotations

from collections.abc import Iterable, Mapping

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from crud_views.lib.check import Check, CheckAttribute, CheckExpression, CheckWarningExpression
from crud_views.lib.icons import unregistered_prefix
from crud_views_object_detail.lib.config import PropertyConfig, PropertyGroupConfig, parse_property_display
from crud_views_object_detail.lib.resolvers import resolve_all


class ObjectDetailMixin:
    """Adds resolved object-detail property groups to a crud_views detail view.

    Set ``cv_property_display`` to a group list or a mapping from exact model
    classes to group lists. Resolved groups land in the template context as
    ``object_detail_groups``.
    """

    template_name = "crud_views/view_detail.html"
    cv_content_template = "crud_views_object_detail/view_detail.content.html"
    cv_modal_supported = True

    cv_property_display: list | Mapping[type[Model], list] | None = None

    #: Optional per-view override of the object-detail layout pack (e.g. "accordion").
    #: Falls back to ``CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT`` when None.
    cv_object_detail_layout: str | None = None

    #: Stable component token; applications own uniqueness across independent responses.
    cv_object_detail_id: str | None = None

    def cv_get_object_detail_id(self) -> str | None:
        """Return the component token; override to choose a namespace using self.request."""
        return self.cv_object_detail_id

    @property
    def property_display(self):
        return self.cv_property_display

    def get_property_display(self) -> list[PropertyGroupConfig]:
        raw = self.property_display
        if raw is None:
            return []
        if isinstance(raw, Mapping):
            model = type(self.object)
            try:
                raw = raw[model]
            except KeyError as exc:
                view = type(self)
                raise ImproperlyConfigured(
                    f"{view.__module__}.{view.__qualname__}.cv_property_display has no entry for {model._meta.label}"
                ) from exc
        return parse_property_display(raw)

    def get_object_for_detail(self):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = self.get_property_display()
        if groups:
            instance = self.get_object_for_detail()
            context["object_detail_groups"] = resolve_all(instance, groups, view=self)
        context["object_detail_layout"] = self.cv_object_detail_layout
        context["object_detail_id"] = self.cv_get_object_detail_id()
        return context

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield CheckAttribute(context=cls, id="E240", attribute="cv_property_display")
        pd = cls.cv_property_display
        if pd is not None:
            yield CheckExpression(
                context=cls,
                id="E241",
                expression=isinstance(pd, (list, Mapping)),
                msg="cv_property_display must be a list or model-to-groups mapping",
            )
            if isinstance(pd, list):
                for i, group in enumerate(pd):
                    yield from cls._checks_property_group(i, group)
            elif isinstance(pd, Mapping):
                for entry, (model, groups) in enumerate(pd.items()):
                    valid_model = isinstance(model, type) and issubclass(model, Model)
                    location = (
                        f"cv_property_display[{model._meta.label}]"
                        if valid_model
                        else f"cv_property_display[entry {entry} ({type(model).__name__})]"
                    )
                    yield CheckExpression(
                        context=cls,
                        id="E247",
                        expression=valid_model,
                        msg=f"{location} key must be a Django model class",
                    )
                    yield CheckExpression(
                        context=cls,
                        id="E241",
                        expression=isinstance(groups, list),
                        msg=f"{location} must be a list",
                    )
                    if isinstance(groups, list):
                        for i, group in enumerate(groups):
                            yield from cls._checks_property_group(i, group, location)
        yield from super().checks()

    @classmethod
    def _checks_property_group(cls, i: int, group, location: str = "cv_property_display") -> Iterable[Check]:
        if isinstance(group, PropertyGroupConfig):
            icon = group.icon
        else:
            icon = group.get("icon") if isinstance(group, dict) else None
        prefix = unregistered_prefix(icon)
        yield CheckWarningExpression(
            context=cls,
            id="W246",
            expression=prefix is None,
            msg=f"{location}[{i}]['icon'] = {icon!r} uses unregistered icon library prefix {prefix!r}",
        )
        if isinstance(group, PropertyGroupConfig):
            return  # structure already validated by pydantic
        yield CheckExpression(
            context=cls,
            id="E242",
            expression=isinstance(group, dict) and "title" in group,
            msg=f"{location}[{i}] must be a dict with a 'title' key",
        )
        yield CheckExpression(
            context=cls,
            id="E243",
            expression=isinstance(group, dict) and "properties" in group,
            msg=f"{location}[{i}] must be a dict with a 'properties' key",
        )
        if isinstance(group, dict) and "properties" in group:
            yield from cls._checks_group_properties(i, group["properties"], location)

    @classmethod
    def _checks_group_properties(cls, i: int, props, location: str = "cv_property_display") -> Iterable[Check]:
        yield CheckExpression(
            context=cls,
            id="E244",
            expression=isinstance(props, list),
            msg=f"{location}[{i}]['properties'] must be a list",
        )
        if isinstance(props, list):
            for j, prop in enumerate(props):
                yield CheckExpression(
                    context=cls,
                    id="E245",
                    expression=isinstance(prop, (str, dict, PropertyConfig)),
                    msg=f"{location}[{i}]['properties'][{j}] must be a str, dict, or PropertyConfig",
                )
