"""Alert data for the one alert frame: ``{% cv_messages %}``, ``{% cv_alert %}`` and the delete page (#250)."""

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

LEVELS: dict[int, str] = {
    constants.DEBUG: "debug",
    constants.INFO: "info",
    constants.SUCCESS: "success",
    constants.WARNING: "warning",
    constants.ERROR: "error",
}

TEXT_BODY = "crud_views/snippets/alert/text.html"
LIST_BODY = "crud_views/snippets/alert/list.html"


def alert_data(
    level,
    *,
    heading="",
    text="",
    items=None,
    body_template: str | None = None,
    dismissible: bool = False,
    extra_tags: str = "",
) -> dict:
    """Render-ready data for ``crud_views/tags/alert.html``.

    ``level`` is one of ``LEVELS``' values; anything else renders as ``info``. The body template is chosen here,
    once, so the frame only includes it: the list body when there are ``items``, else the text body.

    ``heading``, ``text`` and each item come back escaped: a ``SafeString`` passes through untouched, anything
    else (a model instance is ``str()``-ed first) is escaped here rather than left to the template's autoescape
    state, so a host rendering the alert inside ``{% autoescape off %}`` keeps the guarantee. ``extra_tags`` is
    escaped unconditionally.
    """
    if level not in LEVELS.values():
        level = "info"
    items = [conditional_escape(item) for item in items or ()]
    if body_template is None:
        body_template = LIST_BODY if items else TEXT_BODY
    return {
        "level": level,
        "icon_name": f"message-{level}",
        "heading": conditional_escape(heading) if heading else "",
        "text": conditional_escape(text) if text else "",
        "items": items,
        "body_template": body_template,
        "dismissible": dismissible,
        "extra_tags": escape(extra_tags or ""),
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
