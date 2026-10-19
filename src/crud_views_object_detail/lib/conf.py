from functools import cached_property

from django.conf import settings
from pydantic import BaseModel

_UNSET = object()


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
    def property_text_newline(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE")
        return "linebreaksbr" if v is _UNSET else v


crud_views_object_detail_settings = CrudViewsObjectDetailSettings()
