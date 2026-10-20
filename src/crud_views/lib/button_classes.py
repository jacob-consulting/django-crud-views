"""Layered button class table: defaults, theme layer and ``CRUD_VIEWS_BUTTON_CLASSES`` keyed ``location:slot``."""

from django.conf import settings
from django.core.checks import CheckMessage, Error
from django.core.checks import Warning as DjangoWarning
from django.core.signals import setting_changed
from django.dispatch import receiver

DEFAULT_BUTTON_CLASSES: dict[str, str] = {
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


def get_button_class(location: str, slot: str) -> str:
    """Resolved classes for ``location:slot``; "" for None, "", an unknown key or a non-str value."""
    value = get_button_classes().get(f"{location}:{slot}")
    return value if isinstance(value, str) else ""


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

    for key in (*_THEME_BUTTON_CLASSES, *_settings_layer()):
        if key not in DEFAULT_BUTTON_CLASSES:
            messages.append(
                DjangoWarning(
                    f"Button class {key!r} is not a known key (typo?).",
                    hint="See the buttons documentation page for the list of keys.",
                    id="crud_views.W362",
                )
            )

    return messages
