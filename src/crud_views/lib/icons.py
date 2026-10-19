"""Semantic icon registry: names -> ``prefix:name`` values -> library renderers."""

from collections.abc import Callable

from django.conf import settings
from django.core.checks import CheckMessage, Error
from django.core.checks import Warning as DjangoWarning
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.safestring import SafeString

DEFAULT_ICONS: dict[str, str] = {
    "list": "far:rectangle-list",
    "card": "fas:rectangle-list",
    "detail": "far:eye",
    "create": "far:square-plus",
    "update": "far:pen-to-square",
    "delete": "far:trash-can",
    "order-up": "far:circle-up",
    "order-down": "far:circle-down",
    "manage": "fas:gear",
    "workflow": "fas:diagram-project",
    "actions-menu": "fas:ellipsis",
    "filter": "fas:filter",
    "filter-close": "fas:filter-circle-xmark",
    "language": "fas:language",
    "sort-asc": "fas:arrow-up-short-wide",
    "sort-desc": "fas:arrow-down-wide-short",
    "table-sort-asc": "fas:angles-up",
    "table-sort-desc": "fas:angles-down",
    "formset-up": "fas:caret-up",
    "formset-down": "fas:caret-down",
    "formset-add": "fas:plus",
    "formset-delete": "fas:square-xmark",
    "field-marker": "fas:angles-right",
    "boolean-true": "fas:circle-check",
    "boolean-false": "fas:circle-xmark",
    "property-detail": "fas:circle-info",
    "text-icon": "far:file-lines",
}

BOOTSTRAP_ICONS: dict[str, str] = {
    name: f"bi:{icon}"
    for name, icon in {
        "list": "list-ul",
        "card": "card-list",
        "detail": "eye",
        "create": "plus-square",
        "update": "pencil-square",
        "delete": "trash",
        "order-up": "arrow-up-circle",
        "order-down": "arrow-down-circle",
        "manage": "gear",
        "workflow": "diagram-3",
        "actions-menu": "three-dots",
        "filter": "funnel",
        "filter-close": "x-circle",
        "sort-asc": "sort-up",
        "sort-desc": "sort-down",
        "table-sort-asc": "chevron-double-up",
        "table-sort-desc": "chevron-double-down",
        "formset-up": "caret-up-fill",
        "formset-down": "caret-down-fill",
        "formset-add": "plus-lg",
        "formset-delete": "x-square-fill",
        "field-marker": "chevron-double-right",
        "boolean-true": "check-circle-fill",
        "boolean-false": "x-circle-fill",
        "property-detail": "info-circle",
        "text-icon": "journal-text",
        "language": "translate",
    }.items()
}

BUILTIN_LIBRARIES: dict[str, dict] = {
    "far": {"renderer": "font", "class": "fa-regular fa-{name}"},
    "fas": {"renderer": "font", "class": "fa-solid fa-{name}"},
    "bi": {"renderer": "font", "class": "bi bi-{name}"},
}

_THEME_ICONS: dict[str, str] = {}
_THEME_LIBRARIES: dict[str, dict] = {}

_icons_cache: dict[str, str] | None = None
_libraries_cache: dict[str, dict] | None = None


def reset_icon_cache() -> None:
    global _icons_cache, _libraries_cache, _renderers_cache
    _icons_cache = None
    _libraries_cache = None
    _renderers_cache = None


@receiver(setting_changed)
def _on_setting_changed(sender, setting, **kwargs):
    if setting in ("CRUD_VIEWS_ICONS", "CRUD_VIEWS_ICON_LIBRARIES"):
        reset_icon_cache()


def register_icon_library(prefix: str, renderer: str | Callable = "font", **config) -> None:
    _THEME_LIBRARIES[prefix] = {"renderer": renderer, **config}
    reset_icon_cache()


def register_icons(icons: dict[str, str]) -> None:
    _THEME_ICONS.update(icons)
    reset_icon_cache()


def get_icons() -> dict[str, str]:
    global _icons_cache
    icons = _icons_cache
    if icons is None:
        icons = {**DEFAULT_ICONS, **_THEME_ICONS, **(getattr(settings, "CRUD_VIEWS_ICONS", None) or {})}
        _icons_cache = icons
    return icons


def get_libraries() -> dict[str, dict]:
    global _libraries_cache
    libraries = _libraries_cache
    if libraries is None:
        libraries = {
            **BUILTIN_LIBRARIES,
            **_THEME_LIBRARIES,
            **(getattr(settings, "CRUD_VIEWS_ICON_LIBRARIES", None) or {}),
        }
        _libraries_cache = libraries
    return libraries


def _resolve_renderer(renderer) -> Callable | None:
    """A callable for a library's ``renderer`` value; None when a dotted path cannot be imported."""
    if renderer == "font":
        return font_renderer
    if isinstance(renderer, str):
        try:
            return import_string(renderer)
        except ImportError:
            return None
    return renderer


_renderers_cache: dict[str, Callable | None] | None = None


def _get_renderers() -> dict[str, Callable | None]:
    global _renderers_cache
    renderers = _renderers_cache
    if renderers is None:
        renderers = {
            prefix: _resolve_renderer(config.get("renderer", "font")) for prefix, config in get_libraries().items()
        }
        _renderers_cache = renderers
    return renderers


def resolve_icon(value: str | None) -> tuple[str, str] | None:
    """Return None for empty, ("", raw_class) for a raw class, else (prefix, name)."""
    if not value:
        return None
    value = get_icons().get(value, value)
    if ":" not in value:
        return "", value
    prefix, name = value.split(":", 1)
    return prefix, name


def font_renderer(name: str, *, css: str, config: dict) -> SafeString:
    template = config.get("class")
    if not template:
        return SafeString("")
    classes = template.format(name=name)
    if css:
        classes = f"{classes} {css}"
    return format_html('<i class="{}" aria-hidden="true"></i>', classes)


def render_icon(value: str | None, css: str = "") -> SafeString:
    resolved = resolve_icon(value)
    if resolved is None:
        return SafeString("")
    prefix, name = resolved
    if not prefix:
        return font_renderer(name, css=css, config={"class": "{name}"})
    libraries = get_libraries()
    config = libraries.get(prefix)
    if config is None:
        return SafeString("")
    renderer = _get_renderers().get(prefix)
    if renderer is None:
        return SafeString("")
    return renderer(name, css=css, config=config)


REMOVED_SETTINGS: dict[str, str] = {
    "CRUD_VIEWS_ACTIONS_MENU_ICON": 'CRUD_VIEWS_ICONS["actions-menu"]',
    "CRUD_VIEWS_FILTER_ICON": 'CRUD_VIEWS_ICONS["filter"]',
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
}


def unregistered_prefix(value: str | None) -> str | None:
    """Return the prefix of a ``prefix:name`` value when no library is registered for it, else None."""
    if not value or not isinstance(value, str) or ":" not in value:
        return None
    prefix = value.split(":", 1)[0]
    return None if prefix in get_libraries() else prefix


def icon_check_messages() -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    for name, hint in REMOVED_SETTINGS.items():
        if hasattr(settings, name):
            messages.append(
                Error(f"Setting {name} has been removed.", hint=f"Use {hint} instead.", id="crud_views.E350")
            )

    libraries = get_libraries()
    for prefix, config in libraries.items():
        renderer = config.get("renderer", "font")
        if renderer == "font" and not config.get("class"):
            messages.append(
                Error(
                    f"Icon library {prefix!r} uses the font renderer but has no 'class'.",
                    hint="Add a 'class' format string such as 'fa-solid fa-{name}'.",
                    id="crud_views.E354",
                )
            )
        if isinstance(renderer, str) and renderer != "font":
            try:
                import_string(renderer)
            except ImportError as exc:
                messages.append(
                    Error(
                        f"Renderer {renderer!r} of icon library {prefix!r} cannot be imported: {exc}",
                        hint="Set renderer to 'font', a callable or an importable dotted path.",
                        id="crud_views.E351",
                    )
                )

    icons = get_icons()
    for key, value in icons.items():
        missing = unregistered_prefix(value)
        if missing is not None:
            messages.append(
                DjangoWarning(
                    f"Icon {key!r} = {value!r} uses unregistered library prefix {missing!r}.",
                    hint="Register the library in CRUD_VIEWS_ICON_LIBRARIES.",
                    id="crud_views.W352",
                )
            )
        elif value in icons:
            messages.append(
                DjangoWarning(
                    f"Icon {key!r} = {value!r} refers to another icon name; use 'prefix:name' or a raw class.",
                    hint="Use a 'prefix:name' value or a raw CSS class.",
                    id="crud_views.W352",
                )
            )

    return messages
