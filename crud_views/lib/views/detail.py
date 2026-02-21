from typing import Iterable

from django.views import generic
from django_object_detail import PropertyConfig
from django_object_detail.config import PropertyGroupConfig
from django_object_detail.views import ObjectDetailMixin

from crud_views.lib.check import Check, CheckAttribute, CheckExpression
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DetailView(ObjectDetailMixin, CrudView, generic.DetailView):
    template_name = "crud_views/view_detail.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    # icons
    cv_icon_action = "fa-regular fa-eye"

    cv_property_display: list | None = None

    @property
    def property_display(self):
        return self.cv_property_display

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        # cv_property_display must be set
        yield CheckAttribute(context=cls, id="E240", attribute="cv_property_display")
        # structural validation
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
                                    msg=f"cv_property_display[{i}]['properties'][{j}] must be a str, dict, or PropertyConfig",
                                )


class DetailViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailView):  # this file
    cv_permission = "view"
