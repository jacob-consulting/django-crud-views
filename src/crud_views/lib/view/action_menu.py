"""Overflow menu for list, context and card actions (#174)."""

from collections.abc import Iterable, Iterator
from typing import Any

from crud_views.lib.check import Check, CheckExpression, CheckWarningExpression


def cv_is_inline_keys(value: Any) -> bool:
    """True for a valid inline-keys value: None, or a list/tuple of strings."""
    if value is None:
        return True
    return isinstance(value, (list, tuple)) and all(isinstance(key, str) for key in value)


def cv_inline_checks(cls, attribute: str, known_keys: Iterable[str] | None) -> Iterator[Check]:
    """viewset.E208 / viewset.W290 for a view's own cv_*_actions_inline attribute.

    Only the attribute set on the view class is checked for unknown keys: ViewSet and setting values are shared
    defaults, so keys missing on some views are expected there.
    """
    value = getattr(cls, attribute)
    valid = cv_is_inline_keys(value)
    yield CheckExpression(
        context=cls,
        id="E208",
        expression=valid,
        msg=f"{attribute} must be None or a list of strings, got {value!r}",
    )
    if not valid or value is None:
        return
    known = list(known_keys or [])
    unknown = [key for key in value if key not in known]
    yield CheckWarningExpression(
        context=cls,
        id="W290",
        expression=not unknown,
        msg=f"{attribute} names {unknown!r}, which are not among this view's actions {known!r} (typo?)",
    )
