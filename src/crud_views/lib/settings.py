from functools import cached_property
from typing import Any, ClassVar, Dict, List, Tuple

from box import Box
from django.conf import settings
from django.core.checks import CheckMessage, Error, Warning as CheckWarning
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from pydantic import BaseModel


def from_settings(name, default=None) -> Any:
    return getattr(settings, name, default)


class CrudViewsSettings(BaseModel):
    MANAGE_VIEWS_ENABLED_VALUES: ClassVar[Tuple[str, ...]] = ("no", "yes", "debug_only")

    # basic
    extends: str | None = from_settings(
        "CRUD_VIEWS_EXTENDS",
    )
    manage_views_enabled: str = from_settings("CRUD_VIEWS_MANAGE_VIEWS_ENABLED", default="debug_only")
    manage_group: str = from_settings("CRUD_VIEWS_MANAGE_GROUP", default="CRUD_VIEWS_MANAGE")
    manage_show_users: bool = from_settings("CRUD_VIEWS_MANAGE_SHOW_USERS", default=False)
    manage_view_class: str | None = from_settings("CRUD_VIEWS_MANAGE_VIEW_CLASS", default=None)
    guardian_manage_view_class: str | None = from_settings("CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS", default=None)
    # not a supported setting; only read to warn consumers who set it (see check_messages)
    theme: str | None = from_settings("CRUD_VIEWS_THEME", default=None)

    # session
    session_data_key: str = from_settings("CRUD_VIEWS_SESSION_DATA_KEY", "viewset")

    # breadcrumb
    breadcrumb_prefix: List[Dict[str, Any]] = from_settings("CRUD_VIEWS_BREADCRUMB_PREFIX", default=[])

    # filter
    filter_persistence: bool = from_settings("CRUD_VIEWS_FILTER_PERSISTENCE", default=True)
    filter_pinned: bool = from_settings("CRUD_VIEWS_FILTER_PINNED", default=False)
    filter_icon: str = from_settings("CRUD_VIEWS_FILTER_ICON", default="fa-solid fa-filter")
    filter_reset_button_css_class: str = from_settings(
        "CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS", default="btn btn-secondary"
    )

    # view defaults
    list_actions: List[str] = from_settings("CRUD_VIEWS_LIST_ACTIONS", default=["detail", "update", "delete"])
    list_context_actions: List[str] = from_settings(
        "CRUD_VIEWS_LIST_CONTEXT_ACTIONS", default=["parent", "list", "filter", "create"]
    )
    detail_context_actions: List[str] = from_settings(
        "CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    create_context_actions: List[str] = from_settings("CRUD_VIEWS_CREATE_CONTEXT_ACTIONS", default=["home", "create"])
    update_context_actions: List[str] = from_settings(
        "CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    delete_context_actions: List[str] = from_settings(
        "CRUD_VIEWS_DELETE_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    manage_context_actions: List[str] = from_settings("CRUD_VIEWS_MANAGE_CONTEXT_ACTIONS", default=["home"])
    create_select_context_actions: List[str] = from_settings(
        "CRUD_VIEWS_CREATE_SELECT_CONTEXT_ACTIONS", default=["home", "create_select"]
    )

    @property
    def check_messages(self) -> List[CheckMessage]:
        messages: List[CheckMessage] = []

        if not self.extends:
            messages.append(Error(id="crud_views.E100", msg="setting CRUD_VIEWS_EXTENDS is not set"))
        else:
            try:
                get_template(self.extends)
            except TemplateDoesNotExist:
                messages.append(Error(id="crud_views.E100", msg=f"template {self.extends} not found"))

        if self.theme is not None:
            messages.append(
                CheckWarning(
                    id="crud_views.W110",
                    msg="setting CRUD_VIEWS_THEME has no effect and is ignored",
                    hint=(
                        "Theming is done by overriding templates, not via a setting. Ship templates "
                        "under the crud_views/ namespace and list your theme app (e.g. myapp_theme) "
                        "before crud_views in INSTALLED_APPS (see docs/reference/theme.md). "
                        "Remove CRUD_VIEWS_THEME."
                    ),
                )
            )

        if self.manage_views_enabled not in self.MANAGE_VIEWS_ENABLED_VALUES:
            messages.append(
                Error(
                    id="crud_views.E101",
                    msg=(
                        f"setting CRUD_VIEWS_MANAGE_VIEWS_ENABLED must be one of "
                        f"{self.MANAGE_VIEWS_ENABLED_VALUES}, got {self.manage_views_enabled!r}"
                    ),
                )
            )

        # deferred import: settings.py must not import breadcrumb.py at module level
        # (breadcrumb.py imports crud_views_settings)
        from pydantic import ValidationError as PydanticValidationError

        from crud_views.lib.breadcrumb import BreadcrumbItem

        for i, entry in enumerate(self.breadcrumb_prefix):
            try:
                BreadcrumbItem.model_validate(entry)
            except PydanticValidationError as exc:
                messages.append(
                    Error(
                        id="crud_views.E102",
                        msg=f"setting CRUD_VIEWS_BREADCRUMB_PREFIX entry {i} is invalid: {exc}",
                    )
                )

        return messages

    @property
    def theme_path(self) -> str:
        return "crud_views"

    @property
    def context_button_template(self) -> str:
        return from_settings(
            "CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE",
            default=f"{self.theme_path}/tags/context_action.html",
        )

    def get_js(self, path: str) -> str:
        return f"{self.theme_path}/js/{path}"

    def get_css(self, path: str) -> str:
        return f"{self.theme_path}/css/{path}"

    def javascript(self) -> dict:
        return Box(
            {
                "viewset": self.get_js("viewset.js"),
                "formset": self.get_js("formset.js"),
                "list_filter": self.get_js("list.filter.js"),
                "modal": self.get_js("modal.js"),
                "toggle": self.get_js("toggle.js"),
            }
        )

    @cached_property
    def css(self) -> dict:
        return Box(
            {
                "property": self.get_css("property.css"),
                "table": self.get_css("table.css"),
                "formset": self.get_css("formset.css"),
            }
        )

    @cached_property
    def dict(self) -> dict:
        return {
            "viewset": {
                "extends": self.extends,
                "javascript": self.javascript,
                "css": self.css,
            }
        }


crud_views_settings = CrudViewsSettings()
