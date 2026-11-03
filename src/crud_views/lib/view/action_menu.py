"""Overflow menu for list, context and card actions (#174)."""

from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from crud_views.lib.button_classes import FORM_KINDS
from crud_views.lib.check import Check, CheckExpression, CheckWarningExpression
from crud_views.lib.settings import crud_views_settings

from .label_mode import LABEL_MODES, is_label_mode, is_label_mode_map


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


def cv_label_mode_checks(cls, attribute: str, known_keys: Iterable[str] | None) -> Iterator[Check]:
    """viewset.E211 / viewset.W291 for a view's own cv_*_actions_label_mode attribute (#216).

    Same rule as cv_inline_checks: only the attribute set on the view class is checked for unknown keys.
    """
    value = getattr(cls, attribute)
    valid = is_label_mode_map(value)
    yield CheckExpression(
        context=cls,
        id="E211",
        expression=valid,
        msg=(
            f"{attribute} must be None or a dict of action key -> one of {sorted(LABEL_MODES)}, got {value!r} "
            f"(cv_card_actions_label_mode is the string or None default of card views, cv_context_action_label_mode "
            f"the string or None default of a target view)"
        ),
    )
    if not valid or value is None:
        return
    known = list(known_keys or [])
    unknown = [key for key in value if key not in known]
    yield CheckWarningExpression(
        context=cls,
        id="W291",
        expression=not unknown,
        msg=f"{attribute} names {unknown!r}, which are not among this view's actions {known!r} (typo?)",
    )


_FORM_FLOOR_HINT = "kinds not named take the form floor CRUD_VIEWS_LABEL_MODE_DEFAULTS['form']"


def cv_is_form_label_mode_map(value: Any) -> bool:
    """True for a dict of finite form kind (button_classes.FORM_KINDS) -> label mode (Phase 6).

    None is not accepted here: callers that allow None (the ViewSet field) check it themselves. Unlike the open
    context / list maps, a key outside FORM_KINDS is invalid.
    """
    return isinstance(value, dict) and all(
        isinstance(key, str) and key in FORM_KINDS and is_label_mode(mode) for key, mode in value.items()
    )


def cv_form_label_mode_checks(cls, attribute: str = "cv_form_actions_label_mode") -> Iterator[Check]:
    """viewset.E211 / E210 / W291 for a view's own cv_form_actions_label_mode (Phase 6, D-16).

    A form-only policy, distinct from cv_label_mode_checks: a value that is not None or a dict, or a dict with a
    non-string key, is one E211 and stops the traversal; each invalid mode of a string-keyed dict is one E210, in
    insertion order; kinds outside the finite FORM_KINDS whose modes are valid are one W291. The ViewSet and setting
    maps are validated by their own owners (constructor / E106), never here. The mode is never resolved.
    """
    value = getattr(cls, attribute)
    if value is None:
        return
    kinds = sorted(FORM_KINDS)
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        yield CheckExpression(
            context=cls,
            id="E211",
            expression=False,
            msg=(
                f"{attribute} must be None or a dict of form kind -> one of {sorted(LABEL_MODES)}, got {value!r} "
                f"(form kinds: {kinds}; {_FORM_FLOOR_HINT})"
            ),
        )
        return
    unknown: list[str] = []
    for kind, mode in value.items():
        if not is_label_mode(mode):
            yield CheckExpression(
                context=cls,
                id="E210",
                expression=False,
                msg=f"{attribute} form kind {kind!r} must be one of {sorted(LABEL_MODES)}, got {mode!r}",
            )
        elif kind not in FORM_KINDS:
            unknown.append(kind)
    yield CheckWarningExpression(
        context=cls,
        id="W291",
        expression=not unknown,
        msg=f"{attribute} names {unknown!r}, which are not form kinds {kinds} (typo?); {_FORM_FLOOR_HINT}",
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
