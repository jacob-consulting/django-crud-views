"""Test helper: turn a rendered form into a POST payload (copied from tests/lib/helper/forms.py)."""

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
        if not name:
            continue
        if el.tag == "input":
            input_type = (el.get("type") or "text").lower()
            if input_type in ("submit", "button", "reset"):
                continue
            if input_type in ("checkbox", "radio"):
                if el.get("checked") is not None:
                    payload[name] = el.get("value", "on")
                continue
            payload[name] = el.get("value") or ""
        elif el.tag == "select":
            selected = el.cssselect("option[selected]")
            if selected:
                payload[name] = selected[0].get("value", "")
            else:
                options = el.cssselect("option")
                payload[name] = options[0].get("value", "") if options else ""
        else:  # textarea
            payload[name] = el.text or ""
    return payload


def field_keys(payload: dict, suffix: str) -> list:
    """All payload keys ending with the given suffix, e.g. '-title'."""
    return [k for k in payload if k.endswith(suffix)]


def field_key(payload: dict, suffix: str) -> str:
    """The single payload key ending with the given suffix."""
    keys = field_keys(payload, suffix)
    assert len(keys) == 1, f"expected exactly one key ending with {suffix!r}, got {keys}"
    return keys[0]
