"""``django.contrib.messages`` levels -> alert style, for the ``{% cv_messages %}`` tag."""

from collections.abc import Iterable

from django.contrib.messages import constants
from django.utils.html import conditional_escape, escape

ALERT_CLASSES: dict[int, str] = {
    constants.DEBUG: "secondary",
    constants.INFO: "info",
    constants.SUCCESS: "success",
    constants.WARNING: "warning",
    constants.ERROR: "danger",
}

ICON_NAMES: dict[int, str] = {
    constants.DEBUG: "message-debug",
    constants.INFO: "message-info",
    constants.SUCCESS: "message-success",
    constants.WARNING: "message-warning",
    constants.ERROR: "message-error",
}


def message_alerts(messages: Iterable[object] | None) -> list[dict]:
    """Render-ready dicts for a message queue, one per message.

    A missing or unknown level falls back to ``INFO``, so a plain string or a custom level renders as an
    info alert instead of raising.

    A falsy body (``None``, ``""``) comes back as ``""``, so it renders an empty alert rather than the text
    ``"None"`` — the ``message.message|default:""`` the replaced tag used.

    Both the body and ``extra_tags`` come back escaped: a ``SafeString`` body (every ``cv_message_template``
    snippet is one) passes through untouched, anything else is escaped here rather than left to the template's
    autoescape state. The ``{% bootstrap_messages %}`` tag this replaces built its alerts with ``format_html``,
    which escapes unconditionally, so a host rendering the tag inside ``{% autoescape off %}`` keeps that
    guarantee. Output under autoescape-on is unchanged.
    """
    alerts = []
    for message in messages or ():
        level = getattr(message, "level", None)
        if level not in ALERT_CLASSES:
            level = constants.INFO
        body = getattr(message, "message", message)
        alerts.append(
            {
                "message": conditional_escape(body) if body else "",
                "css_class": ALERT_CLASSES[level],
                "icon_name": ICON_NAMES[level],
                "extra_tags": escape(getattr(message, "extra_tags", None) or ""),
            }
        )
    return alerts
