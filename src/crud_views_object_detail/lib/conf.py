from functools import cached_property

from django.conf import settings
from pydantic import BaseModel

_UNSET = object()

ICON_LIBRARY_DEFAULTS = {
    "bootstrap": {"class": "bi", "type": None, "prefix": "bi"},
    "fontawesome": {"class": "fa", "type": "regular", "prefix": "fa"},
}

NAMED_ICONS_DEFAULTS = {
    "bootstrap": {
        "boolean-true": "check-circle-fill",
        "boolean-false": "x-circle-fill",
        "property-detail": "info-circle",
        "text-icon": "journal-text",
    },
    "fontawesome": {
        "boolean-true": "circle-check",
        "boolean-false": "circle-xmark",
        "property-detail": "circle-info",
        "text-icon": "file-lines",
    },
}


def _from_settings(name, default=_UNSET):
    return getattr(settings, name, default)


class CrudViewsObjectDetailSettings(BaseModel):
    @cached_property
    def template_pack_layout(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT")
        return "split-card" if v is _UNSET else v

    @cached_property
    def template_pack_types(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES")
        return "default" if v is _UNSET else v

    @cached_property
    def icons_library(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY")
        return "bootstrap" if v is _UNSET else v

    @cached_property
    def icons_class(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("class", "")

    @cached_property
    def icons_type(self):
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("type")

    @cached_property
    def icons_prefix(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("prefix", "")

    @cached_property
    def named_icons(self) -> dict:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS")
        if v is not _UNSET:
            return v
        return NAMED_ICONS_DEFAULTS.get(self.icons_library, {})

    @cached_property
    def property_text_newline(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE")
        return "linebreaksbr" if v is _UNSET else v


crud_views_object_detail_settings = CrudViewsObjectDetailSettings()


def build_icon_class(icon_name: str) -> str:
    s = crud_views_object_detail_settings
    base = f"{s.icons_class}-{s.icons_type}" if s.icons_type else s.icons_class
    return f"{base} {s.icons_prefix}-{icon_name}"


def build_named_icon_class(name: str) -> str:
    icon_name = crud_views_object_detail_settings.named_icons.get(name, "")
    if not icon_name:
        return ""
    return build_icon_class(icon_name)
