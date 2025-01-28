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
    theme: str = from_settings("VIEWSET_THEME", default="plain")
    extends: str = from_settings("VIEWSET_EXTENDS", )
    manage_views_enabled: str = from_settings("VIEWSET_MANAGE_VIEWS_ENABLED",
                                              default="debug_only")  # no, yes, debug_only

    # session
    session_data_key: str = from_settings("VIEWSET_SESSION_DATA_KEY", "viewset")

    # filter
    filter_persistence: bool = from_settings("VIEWSET_FILTER_PERSISTENCE", default=True)
    filter_icon: str = from_settings("VIEWSET_FILTER_ICON", default="fa-solid fa-filter")
    filter_header_template: str | None = from_settings("VIEWSET_FILTER_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/filter.html")
    filter_header_template_code: str | None = from_settings("VIEWSET_FILTER_HEADER_TEMPLATE_CODE")
    filter_reset_button_css_class: str = from_settings("VIEWSET_FILTER_RESET_BUTTON_CSS_CLASS",
                                                       default="btn btn-secondary")

    # manage
    manage_context_actions: List[str] = from_settings("VIEWSET_MANAGE_CONTEXT_ACTIONS", default=["home"])
    manage_action_label_template: str | None = from_settings("VIEWSET_MANAGE_ACTION_LABEL_TEMPLATE",
                                                             default="crud_views/snippets/action/manage.html")
    manage_action_label_template_code: str | None = from_settings("VIEWSET_MANAGE_ACTION_LABEL_TEMPLATE_CODE",
                                                                  default=None)
    manage_action_short_label_template: str | None = from_settings("VIEWSET_MANAGE_ACTION_SHORT_LABEL_TEMPLATE",
                                                                   default="crud_views/snippets/action_short/manage.html")
    manage_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_MANAGE_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    manage_header_template: str | None = from_settings("VIEWSET_MANAGE_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/manage.html")
    manage_header_template_code: str | None = from_settings("VIEWSET_MANAGE_HEADER_TEMPLATE_CODE")
    manage_paragraph_template: str | None = from_settings("VIEWSET_MANAGE_PARAGRAPH_TEMPLATE",
                                                          default="crud_views/snippets/paragraph/manage.html")
    manage_paragraph_template_code: str | None = from_settings("VIEWSET_MANAGE_PARAGRAPH_TEMPLATE_CODE")

    # list
    list_actions: List[str] = from_settings("VIEWSET_LIST_ACTIONS", default=["detail", "update", "delete"])
    list_context_actions: List[str] = from_settings("VIEWSET_LIST_CONTEXT_ACTIONS",
                                                    default=["parent", "filter", "create"])
    list_action_label_template: str | None = from_settings("VIEWSET_LIST_ACTION_LABEL_TEMPLATE",
                                                           default="crud_views/snippets/action/list.html")
    list_action_label_template_code: str | None = from_settings("VIEWSET_LIST_ACTION_LABEL_TEMPLATE_CODE")
    list_action_short_label_template: str | None = from_settings("VIEWSET_LIST_ACTION_SHORT_LABEL_TEMPLATE",
                                                                 default="crud_views/snippets/action_short/list.html")
    list_action_short_label_template_code: str | None = from_settings("VIEWSET_LIST_ACTION_SHORT_LABEL_TEMPLATE_CODE",
                                                                      default=None)
    list_header_template: str | None = from_settings("VIEWSET_LIST_HEADER_TEMPLATE",
                                                     default="crud_views/snippets/header/list.html")
    list_header_template_code: str | None = from_settings("VIEWSET_LIST_HEADER_TEMPLATE_CODE", )
    list_paragraph_template: str | None = from_settings("VIEWSET_LIST_PARAGRAPH_TEMPLATE",
                                                        default="crud_views/snippets/paragraph/list.html")
    list_paragraph_template_code: str | None = from_settings("VIEWSET_LIST_PARAGRAPH_TEMPLATE_CODE")

    # detail
    detail_context_actions: List[str] = from_settings("VIEWSET_DETAIL_CONTEXT_ACTIONS",
                                                      ["home", "update", "delete"])
    detail_action_label_template: str | None = from_settings("VIEWSET_DETAIL_ACTION_LABEL_TEMPLATE",
                                                             default="crud_views/snippets/action/detail.html")
    detail_action_label_template_code: str | None = from_settings("VIEWSET_DETAIL_ACTION_LABEL_TEMPLATE_CODE",
                                                                  default=None, )
    detail_action_short_label_template: str | None = from_settings("VIEWSET_DETAIL_ACTION_SHORT_LABEL_TEMPLATE",
                                                                   default="crud_views/snippets/action_short/detail.html")
    detail_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_DETAIL_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    detail_header_template: str | None = from_settings("VIEWSET_DETAIL_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/detail.html")
    detail_header_template_code: str | None = from_settings("VIEWSET_DETAIL_HEADER_TEMPLATE_CODE")
    detail_paragraph_template: str | None = from_settings("VIEWSET_DETAIL_PARAGRAPH_TEMPLATE",
                                                          default="crud_views/snippets/paragraph/detail.html")
    detail_paragraph_template_code: str | None = from_settings("VIEWSET_DETAIL_PARAGRAPH_TEMPLATE_CODE")

    # create
    create_context_actions: List[str] = from_settings("VIEWSET_CREATE_CONTEXT_ACTIONS", default=["home", ])
    create_action_label_template: str | None = from_settings("VIEWSET_CREATE_ACTION_LABEL_TEMPLATE",
                                                             default="crud_views/snippets/action/create.html")
    create_action_label_template_code: str | None = from_settings("VIEWSET_CREATE_ACTION_LABEL_TEMPLATE_CODE")
    create_action_short_label_template: str | None = from_settings("VIEWSET_CREATE_ACTION_SHORT_LABEL_TEMPLATE",
                                                                   default="crud_views/snippets/action_short/create.html")
    create_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_CREATE_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    create_header_template: str | None = from_settings("VIEWSET_CREATE_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/create.html")
    create_header_template_code: str | None = from_settings("VIEWSET_CREATE_HEADER_TEMPLATE_CODE")
    create_paragraph_template: str | None = from_settings("VIEWSET_CREATE_PARAGRAPH_TEMPLATE",
                                                          default="crud_views/snippets/paragraph/create.html")
    create_paragraph_template_code: str | None = from_settings("VIEWSET_CREATE_PARAGRAPH_TEMPLATE_CODE")
    create_message_template: str | None = from_settings("VIEWSET_CREATE_MESSAGE_TEMPLATE",
                                                        default="crud_views/snippets/message/create.html")
    create_message_template_code: str | None = from_settings("VIEWSET_CREATE_MESSAGE_TEMPLATE_CODE")

    # update
    update_context_actions: List[str] = from_settings("VIEWSET_UPDATE_CONTEXT_ACTIONS", ["home", ])
    update_action_label_template: str | None = from_settings("VIEWSET_UPDATE_ACTION_LABEL_TEMPLATE",
                                                             default="crud_views/snippets/action/update.html")
    update_action_label_template_code: str | None = from_settings("VIEWSET_UPDATE_ACTION_LABEL_TEMPLATE_CODE",
                                                                  default=None)
    update_action_short_label_template: str | None = from_settings("VIEWSET_UPDATE_ACTION_SHORT_LABEL_TEMPLATE",
                                                                   default="crud_views/snippets/action_short/update.html")
    update_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_UPDATE_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    update_header_template: str | None = from_settings("VIEWSET_UPDATE_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/update.html")
    update_header_template_code: str | None = from_settings("VIEWSET_UPDATE_HEADER_TEMPLATE_CODE")
    update_paragraph_template: str | None = from_settings("VIEWSET_UPDATE_PARAGRAPH_TEMPLATE",
                                                          default="crud_views/snippets/paragraph/update.html")
    update_paragraph_template_code: str | None = from_settings("VIEWSET_UPDATE_PARAGRAPH_TEMPLATE_CODE")
    update_message_template: str | None = from_settings("VIEWSET_UPDATE_MESSAGE_TEMPLATE",
                                                        default="crud_views/snippets/message/update.html")
    update_message_template_code: str | None = from_settings("VIEWSET_UPDATE_MESSAGE_TEMPLATE_CODE")

    # delete
    delete_context_actions: List[str] = from_settings("VIEWSET_DELETE_CONTEXT_ACTIONS", ["home", ])
    delete_action_label_template: str | None = from_settings("VIEWSET_DELETE_ACTION_LABEL_TEMPLATE",
                                                             default="crud_views/snippets/action/delete.html")
    delete_action_label_template_code: str | None = from_settings("VIEWSET_DELETE_ACTION_LABEL_TEMPLATE_CODE",
                                                                  default=None)
    delete_action_short_label_template: str | None = from_settings("VIEWSET_DELETE_ACTION_SHORT_LABEL_TEMPLATE",
                                                                   default="crud_views/snippets/action_short/delete.html")
    delete_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_DELETE_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    delete_header_template: str | None = from_settings("VIEWSET_DELETE_HEADER_TEMPLATE",
                                                       default="crud_views/snippets/header/delete.html")
    delete_header_template_code: str | None = from_settings("VIEWSET_DELETE_HEADER_TEMPLATE_CODE")
    delete_paragraph_template: str | None = from_settings("VIEWSET_DELETE_PARAGRAPH_TEMPLATE",
                                                          default="crud_views/snippets/paragraph/delete.html")
    delete_paragraph_template_code: str | None = from_settings("VIEWSET_DELETE_PARAGRAPH_TEMPLATE_CODE")
    delete_message_template: str | None = from_settings("VIEWSET_DELETE_MESSAGE_TEMPLATE",
                                                        default="crud_views/snippets/message/delete.html")
    delete_message_template_code: str | None = from_settings("VIEWSET_DELETE_MESSAGE_TEMPLATE_CODE")

    # up
    up_action_label_template: str | None = from_settings("VIEWSET_UP_ACTION_LABEL_TEMPLATE",
                                                         default="crud_views/snippets/action/up.html")
    up_action_label_template_code: str | None = from_settings("VIEWSET_UP_ACTION_LABEL_TEMPLATE_CODE")
    up_action_short_label_template: str | None = from_settings("VIEWSET_UP_ACTION_SHORT_LABEL_TEMPLATE",
                                                               default="crud_views/snippets/action_short/up.html")
    up_action_short_label_template_code: str | None = from_settings("VIEWSET_UP_ACTION_SHORT_LABEL_TEMPLATE_CODE",
                                                                    default=None)
    up_action_message_template: str | None = from_settings("VIEWSET_UP_ACTION_MESSAGE_TEMPLATE",
                                                           default="crud_views/snippets/message/up.html")
    up_action_message_template_code: str | None = from_settings("VIEWSET_UP_ACTION_MESSAGE_TEMPLATE_CODE")

    # down
    down_action_label_template: str | None = from_settings("VIEWSET_DOWN_ACTION_LABEL_TEMPLATE",
                                                           default="crud_views/snippets/action/down.html")
    down_action_label_template_code: str | None = from_settings("VIEWSET_DOWN_ACTION_LABEL_TEMPLATE_CODE")
    down_action_short_label_template: str | None = from_settings("VIEWSET_DOWN_ACTION_SHORT_LABEL_TEMPLATE",
                                                                 default="crud_views/snippets/action_short/down.html")
    down_action_short_label_template_code: str | None = from_settings("VIEWSET_DOWN_ACTION_SHORT_LABEL_TEMPLATE_CODE",
                                                                      default=None)
    down_action_message_template: str | None = from_settings("VIEWSET_DOWN_ACTION_MESSAGE_TEMPLATE",
                                                             default="crud_views/snippets/message/down.html")
    down_action_message_template_code: str | None = from_settings("VIEWSET_DOWN_ACTION_MESSAGE_TEMPLATE_CODE",
                                                                  default=None)

    # child
    child_action_label_template: str | None = from_settings("VIEWSET_CHILD_ACTION_LABEL_TEMPLATE",
                                                            default="crud_views/snippets/action/child.html")
    child_action_label_template_code: str | None = from_settings("VIEWSET_CHILD_ACTION_LABEL_TEMPLATE_CODE",
                                                                 default=None)
    child_action_short_label_template: str | None = from_settings("VIEWSET_CHILD_ACTION_SHORT_LABEL_TEMPLATE",
                                                                  default="crud_views/snippets/action_short/child.html")
    child_action_short_label_template_code: str | None = from_settings("VIEWSET_CHILD_ACTION_SHORT_LABEL_TEMPLATE_CODE",
                                                                       default=None)
    child_action_message_template: str | None = from_settings("VIEWSET_CHILD_ACTION_MESSAGE_TEMPLATE",
                                                              default="crud_views/snippets/message/child.html")
    child_action_message_template_code: str | None = from_settings("VIEWSET_CHILD_ACTION_MESSAGE_TEMPLATE_CODE",
                                                                   default=None)

    # polymorphic create select
    create_select_context_actions: List[str] = from_settings("VIEWSET_CREATE_SELECT_CONTEXT_ACTIONS",
                                                             default=["home", ])
    create_select_action_label_template: str | None = from_settings("VIEWSET_CREATE_SELECT_ACTION_LABEL_TEMPLATE",
                                                                    default="crud_views/snippets/action/create_select.html")
    create_select_action_label_template_code: str | None = from_settings(
        "VIEWSET_CREATE_SELECT_ACTION_LABEL_TEMPLATE_CODE")
    create_select_action_short_label_template: str | None = from_settings(
        "VIEWSET_CREATE_SELECT_ACTION_SHORT_LABEL_TEMPLATE",
        default="crud_views/snippets/action_short/create_select.html")
    create_select_action_short_label_template_code: str | None = from_settings(
        "VIEWSET_CREATE_SELECT_ACTION_SHORT_LABEL_TEMPLATE_CODE")
    create_select_header_template: str | None = from_settings("VIEWSET_CREATE_SELECT_HEADER_TEMPLATE",
                                                              default="crud_views/snippets/header/create_select.html")
    create_select_header_template_code: str | None = from_settings("VIEWSET_CREATE_SELECT_HEADER_TEMPLATE_CODE",
                                                                   default=None)
    create_select_paragraph_template: str | None = from_settings("VIEWSET_CREATE_SELECT_PARAGRAPH_TEMPLATE",
                                                                 default="crud_views/snippets/paragraph/create_select.html")
    create_select_paragraph_template_code: str | None = from_settings("VIEWSET_CREATE_SELECT_PARAGRAPH_TEMPLATE_CODE",
                                                                      default=None)
    create_select_message_template: str | None = from_settings("VIEWSET_CREATE_SELECT_MESSAGE_TEMPLATE",
                                                               default="crud_views/snippets/message/create_select.html")
    create_select_message_template_code: str | None = from_settings("VIEWSET_CREATE_SELECT_MESSAGE_TEMPLATE_CODE",
                                                                    default=None)

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
