"""Overflow menu for list, context and card actions (#174)."""

from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from crud_views.lib.check import Check, CheckExpression, CheckWarningExpression
from crud_views.lib.settings import crud_views_settings


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


@dataclass
class ActionGroup:
    """Resolved action data of one container, split into inline buttons and menu items (#174)."""

    inline: list[dict] = field(default_factory=list)
    menu: list[dict] = field(default_factory=list)

    @property
    def all(self) -> list[dict]:
        """Inline items, then menu items (e.g. for the hidden POST form loop)."""
        return [*self.inline, *self.menu]


def cv_split_actions(
    items: Iterable[tuple[str, dict]],
    inline_keys: Sequence[str] | None,
    foldable: Callable[[dict], bool] | None = None,
) -> ActionGroup | None:
    """Split resolved (match_key, data) pairs into inline buttons and menu items.

    None when inline_keys is None (feature off). An item stays inline when its configured key is in inline_keys
    or foldable(data) is False; everything else goes to the menu. Both lists keep the input order. Hidden actions
    must already be dropped (cv_resolve_action). Never mutates the data dicts.
    """
    if inline_keys is None:
        return None
    keep = set(inline_keys)
    group = ActionGroup()
    for key, ctx in items:
        if key in keep or (foldable is not None and not foldable(ctx)):
            group.inline.append(ctx)
        else:
            group.menu.append(ctx)
    return group


def cv_context_button_foldable(ctx: dict) -> bool:
    """A context button can go into the menu unless it renders a whole custom button (template / template_code),
    e.g. the filter toggle."""
    if ctx.get("cv_template_code"):
        return False
    return ctx.get("cv_template") in (None, crud_views_settings.context_button_template)
