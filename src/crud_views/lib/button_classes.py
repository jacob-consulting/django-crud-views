"""Layered button class table: defaults, theme layer and ``CRUD_VIEWS_BUTTON_CLASSES``, keyed ``location:slot[:mode]``.

A mode key (``card:tertiary:icon``) is read in preference to its base key when it is present; see get_button_class.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.checks import CheckMessage, Error
from django.core.checks import Warning as DjangoWarning
from django.core.signals import setting_changed
from django.dispatch import receiver

DEFAULT_BUTTON_CLASSES: dict[str, str | None] = {
    "context:primary": "btn btn-outline-primary btn-lg",
    "context:secondary": "btn btn-outline-primary btn-lg",
    "context:tertiary": "btn btn-outline-primary btn-lg",
    "context:danger": "btn btn-outline-primary btn-lg",
    "list:primary": "btn btn-outline-primary btn-xs",
    "list:secondary": "btn btn-outline-primary btn-xs",
    "list:tertiary": "btn btn-outline-primary btn-xs",
    "list:danger": "btn btn-outline-primary btn-xs",
    "card:primary": "btn btn-primary btn-sm",
    "card:secondary": "btn btn-secondary btn-sm",
    "card:tertiary": "btn btn-outline-secondary btn-sm",
    "card:danger": "btn btn-secondary btn-sm",
    "context:container": "btn-group btn-group-lg",
    "list:container": "btn-group btn-group-xs",
    "card:container": "d-flex gap-2",
    # container structure (#261): the items in a <ul class=container-list> (None: no list), each in an
    # <li class=container-item>; container-single "bare" renders a lone item without container and list
    "context:container-list": None,
    "list:container-list": None,
    "card:container-list": None,
    "context:container-item": "",
    "list:container-item": "",
    "card:container-item": "",
    "context:container-single": "container",
    "list:container-single": "container",
    "card:container-single": "container",
    "context:menu-toggle": "btn btn-outline-primary btn-lg",
    "list:menu-toggle": "btn btn-outline-primary btn-xs",
    "card:menu-toggle": "btn btn-secondary btn-sm",
    "context:menu-wrapper": "btn-group",
    "list:menu-wrapper": "btn-group",
    "card:menu-wrapper": "dropdown",
    "menu:item": "dropdown-item",
    "form:submit": "btn btn-primary",
    "form:cancel": "btn btn-secondary",
    "form:delete": "btn btn-primary",
    "form:filter-submit": "btn btn-primary",
    "form:filter-reset": "btn btn-secondary",
    "formset:control": "btn btn-light",
    "formset:container": "btn-group",
    "formset:control-danger": "btn btn-danger",
    "card-order:toggle": "btn btn-outline-secondary",
    "card-order:container": "btn-group btn-group-sm",
    # utility slots the leaves used to hard-code (#227): the current page's button, a stretched card action and
    # the screen-reader text of an icon-only button; a theme registers its framework's words here
    "context:active": "active",
    "list:active": "active",
    "card:active": "active",
    "menu:active": "active",
    "card-order:active": "active",
    "card:flex": "flex-grow-1",
    # the stock card's own parts (#243); the actions inside it are styled by card:container
    "card:root": "card mb-3",
    "card:body": "card-body",
    "card:title": "card-title",
    # alert frames (#250); the level is the slot
    "alert:error": "alert alert-danger",
    "alert:warning": "alert alert-warning",
    "alert:success": "alert alert-success",
    "alert:info": "alert alert-info",
    "alert:debug": "alert alert-secondary",
    "context:hidden-label": "visually-hidden",
    "list:hidden-label": "visually-hidden",
    "card:hidden-label": "visually-hidden",
    # the class a host-placed icon (#258) adds to its button: {name_class} is the icon library's name class; a theme
    # that needs a base class next to it writes e.g. "icon {name_class}", None switches the icon off there
    "context:icon-host": "{name_class}",
    "list:icon-host": "{name_class}",
    "card:icon-host": "{name_class}",
    "menu:icon-host": "{name_class}",
    "language:toggle": "btn btn-outline-secondary",
    "object-detail:property-detail": "btn btn-link p-0 ms-1 align-baseline text-muted",
}

REMOVED_SETTINGS: dict[str, str] = {
    "CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS": 'CRUD_VIEWS_BUTTON_CLASSES["form:filter-reset"]',
}

_THEME_BUTTON_CLASSES: dict[str, str | None] = {}

_button_classes_cache: dict[str, str | None] | None = None


def reset_button_classes_cache() -> None:
    global _button_classes_cache
    _button_classes_cache = None


@receiver(setting_changed)
def _on_setting_changed(sender, setting, **kwargs):
    if setting == "CRUD_VIEWS_BUTTON_CLASSES":
        reset_button_classes_cache()


def register_button_classes(classes: dict[str, str | None]) -> None:
    """Theme API: merge ``classes`` into the theme layer (settings still win)."""
    _THEME_BUTTON_CLASSES.update(classes)
    reset_button_classes_cache()


def _settings_layer() -> dict[str, str | None]:
    return getattr(settings, "CRUD_VIEWS_BUTTON_CLASSES", None) or {}


def get_button_classes() -> dict[str, str | None]:
    global _button_classes_cache
    classes = _button_classes_cache
    if classes is None:
        classes = {**DEFAULT_BUTTON_CLASSES, **_THEME_BUTTON_CLASSES, **_settings_layer()}
        _button_classes_cache = classes
    return classes


def get_button_class(location: str, slot: str, mode: str | None = None) -> str:
    """Resolved classes for ``location:slot``, preferring ``location:slot:mode`` when that key is present.

    "" for None, "", an unknown key or a non-str value. Presence decides the fallback, not the value: a mode
    key set to None switches that mode off instead of falling through to ``location:slot``.
    """
    classes = get_button_classes()
    key = f"{location}:{slot}"
    if mode and f"{key}:{mode}" in classes:
        key = f"{key}:{mode}"
    value = classes.get(key)
    return value if isinstance(value, str) else ""


def get_icon_host_class(location: str, value: str | None) -> str:
    """The ``location:icon-host`` slot formatted with the name class of a host-placed icon (#258).

    "" when ``value`` is not a host icon, or the slot is None, "", not a str or not a valid format string.
    """
    from .icons import resolve_icon_name_class

    name_class = resolve_icon_name_class(value)
    if name_class is None:
        return ""
    try:
        return get_button_class(location, "icon-host").format(name_class=name_class)
    except Exception:
        return ""


CONTAINER_SINGLE_MODES: tuple[str, ...] = ("container", "bare")


@dataclass(frozen=True)
class ContainerLayout:
    """Structure of one button container (#261): list class (None: no list), item class, lone item bare."""

    list_class: str | None
    item_class: str
    bare: bool


def get_container_layout(location: str, item_count: int) -> ContainerLayout:
    """The ``location:container-*`` keys for a container of ``item_count`` rendered items (#261).

    Reads the raw values: unlike get_button_class(), ``container-list`` keeps "" (a list without class) apart from
    None (no list). Non-str values fall back to the defaults' meaning. ``bare`` only ever applies to one item, and an
    empty container gets no list: zero items render as without the keys.
    """
    classes = get_button_classes()
    list_class = classes.get(f"{location}:container-list")
    item_class = classes.get(f"{location}:container-item")
    return ContainerLayout(
        list_class=list_class if isinstance(list_class, str) and item_count > 0 else None,
        item_class=item_class if isinstance(item_class, str) else "",
        bare=item_count == 1 and classes.get(f"{location}:container-single") == "bare",
    )


def _action_key_parts(key: str) -> tuple[str, str, str] | None:
    """``(location, variant, mode)`` for a three-segment key whose location and variant are known, else None.

    The imports are local on purpose: ``lib.view`` needs the app registry, and this module stays importable with
    bare settings (the checks run after ``django.setup()``).
    """
    from .view.button_data import LOCATIONS
    from .view.variant import VARIANTS

    if not isinstance(key, str):
        return None
    parts = key.split(":")
    if len(parts) == 3 and parts[0] in LOCATIONS and parts[1] in VARIANTS:
        return parts[0], parts[1], parts[2]
    return None


def _is_action_mode_key(key: str) -> bool:
    """True for a valid ``location:variant:mode`` key (#209)."""
    from .view.label_mode import LABEL_MODES

    parts = _action_key_parts(key)
    return parts is not None and parts[2] in LABEL_MODES


def button_class_check_messages() -> list[CheckMessage]:
    messages: list[CheckMessage] = []

    for name, hint in REMOVED_SETTINGS.items():
        if hasattr(settings, name):
            messages.append(
                Error(f"Setting {name} has been removed.", hint=f"Use {hint} instead.", id="crud_views.E360")
            )

    for key, value in get_button_classes().items():
        if value is not None and not isinstance(value, str):
            messages.append(
                Error(
                    f"Button class {key!r} = {value!r} is not a str.",
                    hint="Use a str of CSS classes, or None / '' for no classes.",
                    id="crud_views.E361",
                )
            )
        elif isinstance(key, str) and isinstance(value, str) and key.endswith(":icon-host"):
            try:
                value.format(name_class="x")
            except Exception as exc:
                messages.append(
                    Error(
                        f"Button class {key!r} = {value!r} is not a valid format string: {exc}",
                        hint="The only placeholder is {name_class}, e.g. 'icon {name_class}'.",
                        id="crud_views.E363",
                    )
                )
        elif (
            isinstance(key, str) and key.endswith(":container-single") and value and value not in CONTAINER_SINGLE_MODES
        ):
            messages.append(
                Error(
                    f"Button class {key!r} = {value!r} is not a container mode.",
                    hint=f"Use one of {list(CONTAINER_SINGLE_MODES)}.",
                    id="crud_views.E364",
                )
            )

    from .view.label_mode import LABEL_MODES

    for key in (*_THEME_BUTTON_CLASSES, *_settings_layer()):
        if key in DEFAULT_BUTTON_CLASSES or _is_action_mode_key(key):
            continue
        if (parts := _action_key_parts(key)) is not None:
            messages.append(
                DjangoWarning(
                    f"Button class {key!r} has an unknown label mode {parts[2]!r}.",
                    hint=f"Use one of {sorted(LABEL_MODES)}.",
                    id="crud_views.W362",
                )
            )
        else:
            messages.append(
                DjangoWarning(
                    f"Button class {key!r} is not a known key (typo?).",
                    hint="See the buttons documentation page for the list of keys.",
                    id="crud_views.W362",
                )
            )

    return messages
