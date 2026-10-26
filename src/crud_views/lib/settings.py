from functools import cached_property
from typing import Any, ClassVar

from box import Box
from django.conf import settings
from django.core.checks import CheckMessage, Error
from django.core.checks import Warning as CheckWarning
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from pydantic import BaseModel


def from_settings(name, default=None) -> Any:
    return getattr(settings, name, default)


class CrudViewsSettings(BaseModel):
    MANAGE_VIEWS_ENABLED_VALUES: ClassVar[tuple[str, ...]] = ("no", "yes", "debug_only")
    INACCESSIBLE_ACTIONS_VALUES: ClassVar[tuple[str, ...]] = ("hide", "disable")
    # the package's headings render one below the header, and h6 is the deepest
    HEADER_LEVEL_MAX: ClassVar[int] = 5

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

    # origin of cancel button and success redirect (cv_cancel_keys / cv_success_keys)
    origin_param: str = from_settings("CRUD_VIEWS_ORIGIN_PARAM", default="cv_from")

    # csp
    csp_nonce_attr: str = from_settings("CRUD_VIEWS_CSP_NONCE_ATTR", default="csp_nonce")

    # asset bundling (django-pipeline): tags emit only external entries, a bundler delivers the rest
    assets_bundled: bool = from_settings("CRUD_VIEWS_ASSETS_BUNDLED", default=False)

    # actions the user may not use: "hide" (default) or "disable" (rendered greyed out); see ViewSet /
    # CrudView overrides (cv_get_inaccessible_actions)
    inaccessible_actions: str = from_settings("CRUD_VIEWS_INACCESSIBLE_ACTIONS", default="hide")

    # level of the host's {% cv_header %} (#251): 1-5; the package's headings render one below and keep their look.
    # None = every template keeps its own level. Typed Any so check_messages sees the raw value
    header_level: Any = from_settings("CRUD_VIEWS_HEADER_LEVEL", default=None)

    # overflow menu (#174): keys that stay inline buttons; None = no menu. Overridable per ViewSet
    # (*_actions_inline) and per view (cv_*_actions_inline), resolved on the rendering view
    list_actions_inline: Any = from_settings("CRUD_VIEWS_LIST_ACTIONS_INLINE", default=None)
    context_actions_inline: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_INLINE", default=None)
    card_actions_inline: Any = from_settings("CRUD_VIEWS_CARD_ACTIONS_INLINE", default=None)

    # label mode of context / list actions (#216): action key -> "label" | "icon" | "both". Each layer is selected
    # whole, never merged: the view's map (cv_*_actions_label_mode) if not None, else the ViewSet's
    # (*_actions_label_mode), else this setting, resolved on the rendering view. Keys not named take the
    # configurable location floor default_label_mode() (CRUD_VIEWS_LABEL_MODE_DEFAULTS over the package "icon"; in
    # the toolbar the target view's cv_context_action_label_mode first, #269). The floor setting is not a field:
    # it is read raw at call time (override_settings applies) and validated by E108
    context_actions_label_mode: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", default={})
    list_actions_label_mode: Any = from_settings("CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE", default={})

    # breadcrumb
    breadcrumb_prefix: list[dict[str, Any]] = from_settings("CRUD_VIEWS_BREADCRUMB_PREFIX", default=[])

    # filter
    filter_persistence: bool = from_settings("CRUD_VIEWS_FILTER_PERSISTENCE", default=True)
    filter_pinned: bool = from_settings("CRUD_VIEWS_FILTER_PINNED", default=False)

    # view defaults
    list_actions: list[str] = from_settings("CRUD_VIEWS_LIST_ACTIONS", default=["detail", "update", "delete"])
    list_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_LIST_CONTEXT_ACTIONS", default=["parent", "list", "filter", "create"]
    )
    detail_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    create_context_actions: list[str] = from_settings("CRUD_VIEWS_CREATE_CONTEXT_ACTIONS", default=["home", "create"])
    update_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    delete_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_DELETE_CONTEXT_ACTIONS", default=["home", "detail", "update", "delete"]
    )
    manage_context_actions: list[str] = from_settings("CRUD_VIEWS_MANAGE_CONTEXT_ACTIONS", default=["home"])
    create_select_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_CREATE_SELECT_CONTEXT_ACTIONS", default=["home", "create_select"]
    )
    polymorphic_create_context_actions: list[str] = from_settings(
        "CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS", default=["home"]
    )

    def _action_settings_messages(self) -> list[CheckMessage]:
        """E105 / E106 / E108: the shape of the inline-keys lists (#174), the label-mode maps (#216) and the
        label-mode floor CRUD_VIEWS_LABEL_MODE_DEFAULTS."""
        # deferred imports: settings.py must not import the view package at module level
        from crud_views.lib.view.action_menu import cv_is_inline_keys
        from crud_views.lib.view.button_data import LOCATIONS
        from crud_views.lib.view.label_mode import (
            _UNSET,
            LABEL_MODES,
            _raw_label_mode_defaults,
            is_label_mode,
            is_label_mode_map,
        )

        messages: list[CheckMessage] = []
        for setting, value in (
            ("CRUD_VIEWS_LIST_ACTIONS_INLINE", self.list_actions_inline),
            ("CRUD_VIEWS_CONTEXT_ACTIONS_INLINE", self.context_actions_inline),
            ("CRUD_VIEWS_CARD_ACTIONS_INLINE", self.card_actions_inline),
        ):
            if not cv_is_inline_keys(value):
                messages.append(
                    Error(
                        id="crud_views.E105",
                        msg=f"setting {setting} must be None or a list of strings, got {value!r}",
                    )
                )
        # the setting is the floor of the chain, so None is not allowed here
        for setting, value in (
            ("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", self.context_actions_label_mode),
            ("CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE", self.list_actions_label_mode),
        ):
            if not isinstance(value, dict) or not is_label_mode_map(value):
                messages.append(
                    Error(
                        id="crud_views.E106",
                        msg=(
                            f"setting {setting} must be a dict of action key -> one of {sorted(LABEL_MODES)}, "
                            f"got {value!r}"
                        ),
                    )
                )
        # the per-location floor, read raw on every check (like default_label_mode): absent means the package
        # defaults, anything else must be a dict; one Error per bad entry, an unknown location before its mode
        defaults = _raw_label_mode_defaults()
        if defaults is not _UNSET:
            if not isinstance(defaults, dict):
                messages.append(
                    Error(
                        id="crud_views.E108",
                        msg=(
                            "setting CRUD_VIEWS_LABEL_MODE_DEFAULTS must be a dict of location -> one of "
                            f"{sorted(LABEL_MODES)}, got {defaults!r}"
                        ),
                    )
                )
            else:
                for location, mode in defaults.items():
                    if location not in LOCATIONS:
                        allowed = sorted(LOCATIONS)
                    elif not is_label_mode(mode):
                        allowed = sorted(LABEL_MODES)
                    else:
                        continue
                    messages.append(
                        Error(
                            id="crud_views.E108",
                            msg=(
                                f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key {location!r} must be one of "
                                f"{allowed}, got {mode!r}"
                            ),
                        )
                    )
        return messages

    @property
    def check_messages(self) -> list[CheckMessage]:
        messages: list[CheckMessage] = []

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

        if self.inaccessible_actions not in self.INACCESSIBLE_ACTIONS_VALUES:
            messages.append(
                Error(
                    id="crud_views.E104",
                    msg=(
                        f"setting CRUD_VIEWS_INACCESSIBLE_ACTIONS must be one of "
                        f"{self.INACCESSIBLE_ACTIONS_VALUES}, got {self.inaccessible_actions!r}"
                    ),
                )
            )

        if self.header_level is not None and (
            type(self.header_level) is not int or not 1 <= self.header_level <= self.HEADER_LEVEL_MAX
        ):
            messages.append(
                Error(
                    id="crud_views.E107",
                    msg=(
                        f"setting CRUD_VIEWS_HEADER_LEVEL must be None or an int from 1 to {self.HEADER_LEVEL_MAX}, "
                        f"got {self.header_level!r}"
                    ),
                )
            )

        messages.extend(self._action_settings_messages())

        # deferred import: settings.py must not import check.py at module level
        from crud_views.lib.check import REGS

        if not REGS["name"]["reg"].match(self.origin_param):
            messages.append(
                Error(
                    id="crud_views.E103",
                    msg=(f"setting CRUD_VIEWS_ORIGIN_PARAM {REGS['name']['msg']}, got {self.origin_param!r}"),
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
                "adapters": self.get_js("adapters.js"),
                "viewset": self.get_js("viewset.js"),
                "formset": self.get_js("formset.js"),
                "list_filter": self.get_js("list.filter.js"),
                "modal": self.get_js("modal.js"),
                "toggle": self.get_js("toggle.js"),
                "tooltip": self.get_js("tooltip.js"),
            }
        )

    @cached_property
    def css(self) -> dict:
        return Box(
            {
                "property": self.get_css("property.css"),
                "table": self.get_css("table.css"),
                "formset": self.get_css("formset.css"),
                "icons": self.get_css("icons.css"),
            }
        )

    @cached_property
    def as_dict(self) -> dict:
        return {
            "viewset": {
                "extends": self.extends,
                "javascript": self.javascript,
                "css": self.css,
            }
        }


crud_views_settings = CrudViewsSettings()
