"""``django.contrib.messages`` levels -> alert style, for the ``{% cv_messages %}`` tag."""

from collections.abc import Iterable

from django.contrib.messages import constants

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
    info alert instead of raising. ``message`` is the raw message body, not ``str(message)``: that is what
    keeps a ``SafeString`` (every ``cv_message_template`` snippet is one) from being escaped again.
    """
    alerts = []
    for message in messages or ():
        level = getattr(message, "level", None)
        if level not in ALERT_CLASSES:
            level = constants.INFO
        alerts.append(
            {
                "message": getattr(message, "message", message),
                "css_class": ALERT_CLASSES[level],
                "icon_name": ICON_NAMES[level],
                "extra_tags": getattr(message, "extra_tags", None) or "",
            }
        )
    return alerts
