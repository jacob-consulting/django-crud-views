import collections
from functools import cache
from typing import List, Iterable, Any, OrderedDict, Dict, Callable

from django.views import generic
from django_filters.conf import is_callable
from pydantic import BaseModel, Field, field_validator

from crud_views.lib.check import Check
from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.views.properties import r
from .tabs import Tab


class Property(BaseModel, arbitrary_types_allowed=True):
    name: str
    label: str | None = None
    label_tooltip: str | None = None
    renderer: Callable | None = None

    def __hash__(self):
        return hash(f"{self.name}-{self.label}")

    @property
    def label_display(self) -> str:
        return self.label or self.name.capitalize()


class PropertyGroup(BaseModel, arbitrary_types_allowed=True):
    key: str
    label: str
    properties: List[Property | str]
    show: bool = True
    template_name: str | None = None

    @field_validator("properties", mode="before")
    @classmethod
    def properties_cast_type(cls, value: Any) -> Any:
        if isinstance(value, list):
            value = [Property(name=prop) if isinstance(prop, str) else prop for prop in value]
        return value

    def get_data(self, view, obj: object) -> dict:
        data = dict()
        for prop in self.properties:
            info = view.cv_get_property_info(obj=obj, prop=prop)
            data[prop.name] = info.data
        return data


class PropertyInfo(BaseModel, arbitrary_types_allowed=True):
    """
    Runtime info
    """
    view: CrudView
    property: Property
    value: Any
    label: str
    label_tooltip: str | None = None
    is_decorated: bool = False
    is_field: bool = False
    is_property: bool = False
    renderer: Callable

    def render(self):
        return self.renderer(self.value)

    @property
    def data(self) -> dict:
        return dict(
            label=str(self.label),
            label_tooltip=self.label_tooltip,
            value=self.render()
        )


class DetailView(CrudView, generic.DetailView):
    template_name = "crud_views/view_detail.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions
    cv_properties: OrderedDict[str, List[Any]] = Field(default_factory=collections.OrderedDict)
    cv_property_groups: List[PropertyGroup] = Field(default_factory=list)
    cv_tabs: List[Tab] = []

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    # icons
    cv_icon_action = "fa-regular fa-eye"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        # todo: check property groups
        # todo: check tabs
        # yield PropertyCheck(context=cls, id="E300", attribute="attribute")   # todo

    @property
    def cv_has_visible_tabs(self) -> bool:
        # todo: visibility
        return len(self.cv_tabs) > 0

    def cv_has_visible_property_groups(self) -> bool:
        return len(self.cv_property_groups_show) > 0

    @property
    def cv_property_group_keys(self) -> List[str]:
        return [pg.key for pg in self.cv_property_groups]

    @property
    def cv_property_groups_dict(self) -> Dict[str, PropertyGroup]:
        return {pg.key: pg for pg in self.cv_property_groups}

    @property
    def cv_property_groups_show(self) -> List[PropertyGroup]:
        return [pg for pg in self.cv_property_groups if pg.show]

    def cv_get_property_group(self, group_or_key: str | PropertyGroup) -> PropertyGroup:
        groups = self.cv_property_groups_dict
        if isinstance(group_or_key, PropertyGroup):
            assert group_or_key.key in groups.keys(), f"{group_or_key.key} not in {groups.keys()}"
            return group_or_key
        elif isinstance(group_or_key, str):
            assert group_or_key in groups.keys(), f"{group_or_key} not in {groups.keys()}"
            return groups[group_or_key]
        else:
            raise TypeError(f"{group_or_key} is not a PropertyGroup or str")

    @cache
    def cv_get_property_info(self, obj: object, prop: Property) -> PropertyInfo:
        """
        Get property info which is cached so it is called only once in a template
        """

        # check if decorated at view level
        if hasattr(self, prop.name):
            attr = getattr(self, prop.name)
            if not is_callable(attr):
                raise ViewSetError(f"{prop.name} is not callable at {obj}")
            elif not getattr(attr, "cv_property", False):
                raise ViewSetError(f"{prop.name} is not decorated with cv_property at {obj}")
            renderer = prop.renderer or attr.cv_renderer or r.default
            label = getattr(attr, "cv_label", None) or prop.label_display
            label_tooltip = getattr(attr, "cv_label_tooltip", None) or prop.label_tooltip
            return PropertyInfo(
                view=self,
                property=prop,
                value=attr(),
                label=label,
                label_tooltip=label_tooltip,
                is_decorated=True,
                renderer=renderer,
            )

        # proceed with model
        if not hasattr(obj, prop.name):
            raise ViewSetError(f"{prop.name} is not a property of {obj}")

        # some defaults
        field = None
        is_property = False
        label_tooltip = None

        # get value
        value = getattr(obj, prop.name)

        # field map
        fmap = {field.name: field for field in self.model._meta.get_fields()}

        # check field first, since it may be callable
        if prop.name in fmap:
            # use form field mapping
            field = fmap[prop.name]
            label = prop.label or field.verbose_name
            label_tooltip = field.help_text
            renderer = r.field2renderer.get(field.__class__, r.default)
        elif is_callable(value):
            # custom property at model level?
            if not getattr(value, "cv_property", False):
                raise ViewSetError(f"{prop.name} is not decorated with cv_property at {obj}")
            renderer = prop.renderer or value.cv_renderer or r.default
            label = getattr(value, "cv_label", None) or prop.label_display
            label_tooltip = getattr(value, "cv_label_tooltip", None) or prop.label_tooltip
            value = value()
        else:
            # default
            label = prop.label_display
            label_tooltip = prop.label_tooltip
            renderer = prop.renderer or r.field2renderer.get(None, r.default)

        return PropertyInfo(
            view=self,
            property=prop,
            is_field=field is not None,
            is_property=is_property or field is None,
            renderer=renderer,
            value=value,
            label=str(label),
            label_tooltip=str(label_tooltip)
        )

    def cv_get_property_group_data(self, group_or_key: str | PropertyGroup) -> dict:
        group = self.cv_get_property_group(group_or_key)
        data = group.get_data(self, self.object)
        return data


class DetailViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailView):  # this file
    cv_permission = "view"
