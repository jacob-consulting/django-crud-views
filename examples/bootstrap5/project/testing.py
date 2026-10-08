"""Test helper: turn a rendered form into a POST payload (adapted from tests/lib/helper/forms.py)."""

from lxml import html


def form_payload(response) -> dict:
    """
    Extract all submittable fields of a rendered <form> into a POST payload dict,
    the way a browser would submit it (unchecked checkboxes are omitted).
    Picks the form with the most named fields (pages may contain e.g. a navbar form).
    """
    doc = html.fromstring(response.content)
    forms = doc.cssselect("form")
    assert forms, "no form found in response"
    form = max(forms, key=lambda f: len([e for e in f.cssselect("input,select,textarea") if e.get("name")]))

    payload = {}
    for el in form.cssselect("input, select, textarea"):
        name = el.get("name")
        if name:
            value = _field_value(el)
            if value is not _NOT_SUBMITTED:
                payload[name] = value
    return payload


_NOT_SUBMITTED = object()


def _field_value(el):
    """The value a browser submits for one named field, or _NOT_SUBMITTED."""
    if el.tag == "select":
        return _select_value(el)
    if el.tag == "textarea":
        return el.text or ""
    input_type = (el.get("type") or "text").lower()
    if input_type in ("submit", "button", "reset"):
        return _NOT_SUBMITTED
    if input_type in ("checkbox", "radio"):
        return el.get("value", "on") if el.get("checked") is not None else _NOT_SUBMITTED
    return el.get("value") or ""


def _select_value(el) -> str:
    """The selected option's value, or the first option's (the browser default)."""
    options = el.cssselect("option[selected]") or el.cssselect("option")
    return options[0].get("value", "") if options else ""


def field_keys(payload: dict, suffix: str) -> list:
    """All payload keys ending with the given suffix, e.g. '-title'."""
    return [k for k in payload if k.endswith(suffix)]


def field_key(payload: dict, suffix: str) -> str:
    """The single payload key ending with the given suffix."""
    keys = field_keys(payload, suffix)
    assert len(keys) == 1, f"expected exactly one key ending with {suffix!r}, got {keys}"
    return keys[0]
