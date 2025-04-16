from functools import cached_property
from typing import Any, List

from box import Box
from django.conf import settings
from django.core.checks import CheckMessage, Error
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from pydantic import BaseModel, PrivateAttr


class Default: pass


_messages = []


def default_list(*args, **kwargs) -> Any:
    return list()


def from_settings(name, default=None) -> Any:
    return getattr(settings, name, default)


class CrudViewsSettings(BaseModel):
    # basic
    theme: str = from_settings("CRUD_VIEWS_THEME", default="plain")
    extends: str = from_settings("CRUD_VIEWS_EXTENDS", )
    manage_views_enabled: str = from_settings("CRUD_VIEWS_MANAGE_VIEWS_ENABLED",
                                              default="debug_only")  # no, yes, debug_only

    # session
    session_data_key: str = from_settings("CRUD_VIEWS_SESSION_DATA_KEY", "viewset")

    # filter
    filter_persistence: bool = from_settings("CRUD_VIEWS_FILTER_PERSISTENCE", default=True)
    filter_icon: str = from_settings("CRUD_VIEWS_FILTER_ICON", default="fa-solid fa-filter")
    filter_reset_button_css_class: str = from_settings("CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS",
                                                       default="btn btn-secondary")

    # view defaults
    list_actions: List[str] = from_settings("CRUD_VIEWS_LIST_ACTIONS", default=["detail", "update", "delete"])
    list_context_actions: List[str] = from_settings("CRUD_VIEWS_LIST_CONTEXT_ACTIONS",
                                                    default=["parent", "list", "filter", "create"])
    detail_context_actions: List[str] = from_settings("CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS",
                                                      default=["home", "detail", "update", "delete"])
    create_context_actions: List[str] = from_settings("CRUD_VIEWS_CREATE_CONTEXT_ACTIONS", default=["home", "create"])
    update_context_actions: List[str] = from_settings("CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS",
                                                      default=["home", "detail", "update", "delete"])
    delete_context_actions: List[str] = from_settings("CRUD_VIEWS_DELETE_CONTEXT_ACTIONS",
                                                      default=["home", "detail", "update", "delete"])
    manage_context_actions: List[str] = from_settings("CRUD_VIEWS_MANAGE_CONTEXT_ACTIONS", default=["home"])
    create_select_context_actions: List[str] = from_settings("CRUD_VIEWS_CREATE_SELECT_CONTEXT_ACTIONS",
                                                             default=["home", "create_select"])

    _check_messages: List[CheckMessage] = PrivateAttr(default_factory=default_list)

    @property
    def check_messages(self) -> List[CheckMessage]:

        def check_template(t):
            try:
                get_template(t)
            except TemplateDoesNotExist as exc:
                self._check_messages.append(Error(id="E100", msg=f"template {t} not found"))

        check_template(self.extends)

        return self._check_messages

    @property
    def theme_path(self) -> str:
        return f"crud_views"

    def get_js(self, path: str) -> str:
        return f"{self.theme_path}/js/{path}"

    def get_css(self, path: str) -> str:
        return f"{self.theme_path}/css/{path}"

    def javascript(self) -> dict:
        return Box({
            "viewset": self.get_js("viewset.js"),
            "formset": self.get_js("formset.js"),
            "list_filter": self.get_js("list.filter.js"),
        })

    @cached_property
    def css(self) -> dict:
        return Box({
            "property": self.get_css("property.css"),
            "table": self.get_css("table.css"),
        })

    @cached_property
    def dict(self) -> dict:
        return {
            "viewset": {
                "theme": self.theme,
                "extends": self.extends,
                "javascript": self.javascript,
                "css": self.css,
            }
        }


crud_views_settings = CrudViewsSettings()
