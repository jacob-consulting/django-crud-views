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
    "page-previous": "fas:chevron-left",
    "page-next": "fas:chevron-right",
    "formset-up": "fas:caret-up",
    "formset-down": "fas:caret-down",
    "formset-add": "fas:plus",
    "formset-delete": "fas:square-xmark",
    "field-marker": "fas:angles-right",
    "boolean-true": "fas:circle-check",
    "boolean-false": "fas:circle-xmark",
    "property-detail": "fas:circle-info",
    "text-icon": "far:file-lines",
    "message-success": "fas:circle-check",
    "message-info": "fas:circle-info",
    "message-warning": "fas:triangle-exclamation",
    "message-error": "fas:circle-exclamation",
    "message-debug": "fas:bug",
    # the form-button kinds (Phase 6): submit saves, cancel leaves the form, filter-reset clears the filter form
    # (delete and filter-submit reuse "delete" and "filter")
    "save": "far:floppy-disk",
    "cancel": "fas:xmark",
    "filter-reset": "fas:rotate-left",
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
        "page-previous": "chevron-left",
        "page-next": "chevron-right",
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
        "message-success": "check-circle-fill",
        "message-info": "info-circle-fill",
        "message-warning": "exclamation-triangle-fill",
        "message-error": "exclamation-octagon-fill",
        "message-debug": "bug-fill",
        "save": "floppy",
        "cancel": "x-lg",
        "filter-reset": "arrow-counterclockwise",
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
    """A callable for a library's ``renderer`` value; None when it is unusable (import fails, not callable)."""
    if renderer == "font":
        return font_renderer
    if isinstance(renderer, str):
        try:
            renderer = import_string(renderer)
        except Exception:
            return None
    return renderer if callable(renderer) else None


_renderers_cache: dict[str, Callable | None] | None = None


def _get_renderers() -> dict[str, Callable | None]:
    """Resolved renderer per prefix; library entries that are not a dict are left out (E355 reports them)."""
    global _renderers_cache
    renderers = _renderers_cache
    if renderers is None:
        renderers = {
            prefix: _resolve_renderer(config.get("renderer", "font"))
            for prefix, config in get_libraries().items()
            if isinstance(config, dict)
        }
        _renderers_cache = renderers
    return renderers


def _icon_str(value: object) -> str | None:
    """``value`` stripped when it is a str with non-whitespace content, else None (None, "", "  ", 5, ...)."""
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return None


def resolve_icon(value: str | None) -> tuple[str, str] | None:
    """Return None for empty, ("", raw_class) for a raw class, else (prefix, name).

    Empty applies to the incoming value and to the table value it maps to: a ``CRUD_VIEWS_ICONS`` entry of
    None or "" switches that icon off. A non-str value (incoming or in the table) renders nothing as well.
    """
    value = _icon_str(value)
    if value is None:
        return None
    value = _icon_str(get_icons().get(value, value))
    if value is None:
        return None
    if ":" not in value:
        return "", value
    prefix, name = value.split(":", 1)
    return prefix, name


def font_renderer(name: str, *, css: str, config: dict) -> SafeString:
    """Built-in CSS-class renderer. An unusable ``class`` (missing, not a str, not a valid format string) renders
    nothing; the system check E354 reports it."""
    template = config.get("class")
    if not template or not isinstance(template, str):
        return SafeString("")
    try:
        classes = template.format(name=name)
        if config.get("placement") == "host":
            # a host library's class is the bare name class; a standalone icon wraps it (#258)
            classes = config.get("standalone", "{name_class}").format(name_class=classes)
    except Exception:
        return SafeString("")
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
    if not isinstance(config, dict):
        return SafeString("")
    renderer = _get_renderers().get(prefix)
    if renderer is None:
        return SafeString("")
    return renderer(name, css=css, config=config)


def resolve_icon_name_class(value: str | None) -> str | None:
    """The bare name class of a host-placed icon (``placement: "host"``, #258), else None.

    None for an empty value, a raw class, an unknown prefix and any library that is not a usable ``font`` library
    with host placement: those icons render as an element.
    """
    resolved = resolve_icon(value)
    if resolved is None or not resolved[0]:
        return None
    prefix, name = resolved
    config = get_libraries().get(prefix)
    if not isinstance(config, dict) or config.get("placement") != "host" or config.get("renderer", "font") != "font":
        return None
    template = config.get("class")
    if not isinstance(template, str):
        return None
    try:
        return template.format(name=name)
    except Exception:
        return None


def _icon_available(value: str | None) -> bool:
    """True when ``value`` resolves to an icon the registry can render, decided without rendering (Phase 6, D-16).

    Unavailable: an empty value, a semantic name the icon table maps to None / "", a ``prefix:name`` whose prefix
    has no dict library entry or no usable renderer, and a built-in font library (explicit ``"font"`` or the omitted
    default) whose ``class`` is not a nonempty str that formats with the icon name. A raw CSS class (no prefix) is
    available. A custom renderer counts as available: resolving the callable is allowed, calling it is not, so no
    renderer runs here. Placement is not decided here: a valid host icon is available, and a ``*:icon-host`` slot
    set to None is the caller's placement opt-out. The registry checks (E351 / E354 / E355 / W352) stay the
    diagnostics of the library configuration itself.
    """
    resolved = resolve_icon(value)
    if resolved is None:
        return False
    prefix, name = resolved
    if not prefix:
        return True
    config = get_libraries().get(prefix)
    if not isinstance(config, dict):
        return False
    renderer = _get_renderers().get(prefix)
    if renderer is None:
        return False
    if renderer is font_renderer:
        template = config.get("class")
        if not template or not isinstance(template, str):
            return False
        try:
            template.format(name=name)
        except Exception:
            return False
    return True


REMOVED_SETTINGS: dict[str, str] = {
    "CRUD_VIEWS_ACTIONS_MENU_ICON": 'CRUD_VIEWS_ICONS["actions-menu"]',
    "CRUD_VIEWS_FILTER_ICON": 'CRUD_VIEWS_ICONS["filter"]',
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
    "CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS": "CRUD_VIEWS_ICONS / BOOTSTRAP_ICONS from crud_views.lib.icons",
}


ICON_VALUE_HINT = "Use a semantic name, 'prefix:name', a raw CSS class, or None for no icon."


def is_icon_value(value: object) -> bool:
    """True for the accepted icon value types: None (no icon) and str. Checks report anything else (E356)."""
    return value is None or isinstance(value, str)


def unregistered_prefix(value: str | None) -> str | None:
    """Return the prefix of a ``prefix:name`` value when no library is registered for it, else None."""
    if not value or not isinstance(value, str) or ":" not in value:
        return None
    prefix = value.split(":", 1)[0]
    return None if prefix in get_libraries() else prefix


PLACEMENTS = frozenset({"element", "host"})

_STANDALONE_HINT = "The only placeholder is {name_class}, e.g. 'icon {name_class}'."


def _standalone_check_messages(prefix: str, standalone) -> list[CheckMessage]:
    """E354 for a host library's ``standalone`` value: a str format string with ``{name_class}`` only (#258)."""
    if not isinstance(standalone, str):
        return [
            Error(
                f"Icon library {prefix!r}: 'standalone' must be a str format string, got {type(standalone).__name__}.",
                hint=_STANDALONE_HINT,
                id="crud_views.E354",
            )
        ]
    try:
        standalone.format(name_class="x")
    except Exception as exc:
        return [
            Error(
                f"Icon library {prefix!r}: 'standalone' {standalone!r} is not a valid format string: {exc}",
                hint=_STANDALONE_HINT,
                id="crud_views.E354",
            )
        ]
    return []


_RENDERER_HINT = "Set renderer to 'font', a callable or an importable dotted path."


def _library_check_messages(prefix: str, config) -> list[CheckMessage]:
    """E355 (config not a dict / renderer unusable), E354 (font class), E351 (dotted path import) for one library."""
    if not isinstance(config, dict):
        return [
            Error(
                f"Icon library {prefix!r} config must be a dict, got {type(config).__name__}.",
                hint="Use e.g. {'renderer': 'font', 'class': 'fa-solid fa-{name}'}.",
                id="crud_views.E355",
            )
        ]
    renderer = config.get("renderer", "font")
    placement = config.get("placement", "element")
    if placement not in PLACEMENTS:
        return [
            Error(
                f"Icon library {prefix!r}: placement must be one of {sorted(PLACEMENTS)}, got {placement!r}.",
                hint="Use 'element' (an icon element inside the button) or 'host' (the icon class on the button).",
                id="crud_views.E355",
            )
        ]
    if placement == "host" and renderer != "font":
        return [
            Error(
                f"Icon library {prefix!r}: placement 'host' needs the 'font' renderer.",
                hint="Use renderer 'font' with a 'class' format string, or placement 'element'.",
                id="crud_views.E355",
            )
        ]
    if renderer == "font":
        template = config.get("class")
        if not template:
            return [
                Error(
                    f"Icon library {prefix!r} uses the font renderer but has no 'class'.",
                    hint="Add a 'class' format string such as 'fa-solid fa-{name}'.",
                    id="crud_views.E354",
                )
            ]
        if not isinstance(template, str):
            return [
                Error(
                    f"Icon library {prefix!r}: 'class' must be a str format string, got {type(template).__name__}.",
                    hint="Use a format string such as 'fa-solid fa-{name}'.",
                    id="crud_views.E354",
                )
            ]
        try:
            template.format(name="x")
        except Exception as exc:
            return [
                Error(
                    f"Icon library {prefix!r}: 'class' {template!r} is not a valid format string: {exc}",
                    hint="The only placeholder is {name}, e.g. 'fa-solid fa-{name}'.",
                    id="crud_views.E354",
                )
            ]
        if placement == "host":
            return _standalone_check_messages(prefix, config.get("standalone", "{name_class}"))
        return []
    if isinstance(renderer, str):
        try:
            renderer = import_string(renderer)
        except Exception as exc:
            return [
                Error(
                    f"Renderer {renderer!r} of icon library {prefix!r} cannot be imported: {type(exc).__name__}: {exc}",
                    hint=_RENDERER_HINT,
                    id="crud_views.E351",
                )
            ]
    if not callable(renderer):
        return [
            Error(
                f"Icon library {prefix!r}: renderer must be 'font', a dotted path or a callable, got {renderer!r}.",
                hint=_RENDERER_HINT,
                id="crud_views.E355",
            )
        ]
    return []


def icon_check_messages() -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    for name, hint in REMOVED_SETTINGS.items():
        if hasattr(settings, name):
            messages.append(
                Error(f"Setting {name} has been removed.", hint=f"Use {hint} instead.", id="crud_views.E350")
            )

    for prefix, config in get_libraries().items():
        messages.extend(_library_check_messages(prefix, config))

    icons = get_icons()
    for key, value in icons.items():
        if not is_icon_value(value):
            messages.append(
                Error(
                    f"Icon {key!r} = {value!r} is not a str.",
                    hint=ICON_VALUE_HINT,
                    id="crud_views.E356",
                )
            )
            continue
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
