from __future__ import annotations

from typing import Iterable

from crud_views.lib.check import Check, CheckAttribute, CheckExpression
from crud_views_object_detail.lib.config import PropertyConfig, PropertyGroupConfig, parse_property_display
from crud_views_object_detail.lib.resolvers import resolve_all


class ObjectDetailMixin:
    """Adds resolved object-detail property groups to a crud_views detail view.

    Set ``cv_property_display`` as a list of group dicts (the DSL accepted by
    ``parse_property_display``). Resolved groups land in the template context as
    ``object_detail_groups``.
    """

    template_name = "crud_views/view_detail.html"
    cv_content_template = "crud_views_object_detail/view_detail.content.html"
    cv_modal_supported = True

    cv_property_display: list | None = None

    #: Optional per-view override of the object-detail layout pack (e.g. "accordion").
    #: Falls back to ``CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT`` when None.
    cv_object_detail_layout: str | None = None

    @property
    def property_display(self):
        return self.cv_property_display

    def get_property_display(self) -> list[PropertyGroupConfig]:
        raw = self.property_display
        if raw is None:
            return []
        if raw and isinstance(raw[0], PropertyGroupConfig):
            return raw
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
        return context

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield CheckAttribute(context=cls, id="E240", attribute="cv_property_display")
        pd = cls.cv_property_display
        if pd is not None:
            yield CheckExpression(
                context=cls,
                id="E241",
                expression=isinstance(pd, list),
                msg="cv_property_display must be a list",
            )
            if isinstance(pd, list):
                for i, group in enumerate(pd):
                    if isinstance(group, PropertyGroupConfig):
                        continue
                    yield CheckExpression(
                        context=cls,
                        id="E242",
                        expression=isinstance(group, dict) and "title" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'title' key",
                    )
                    yield CheckExpression(
                        context=cls,
                        id="E243",
                        expression=isinstance(group, dict) and "properties" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'properties' key",
                    )
                    if isinstance(group, dict) and "properties" in group:
                        props = group["properties"]
                        yield CheckExpression(
                            context=cls,
                            id="E244",
                            expression=isinstance(props, list),
                            msg=f"cv_property_display[{i}]['properties'] must be a list",
                        )
                        if isinstance(props, list):
                            for j, prop in enumerate(props):
                                yield CheckExpression(
                                    context=cls,
                                    id="E245",
                                    expression=isinstance(prop, (str, dict, PropertyConfig)),
                                    msg=(
                                        f"cv_property_display[{i}]['properties'][{j}] must be a str, "
                                        "dict, or PropertyConfig"
                                    ),
                                )
        yield from super().checks()  # noqa
