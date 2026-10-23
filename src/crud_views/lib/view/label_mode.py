from enum import StrEnum

from ..check import CheckExpression


class LabelMode(StrEnum):
    """How a button shows its label: text only, icon only, or both."""

    LABEL = "label"
    ICON = "icon"
    BOTH = "both"


LABEL_MODES: frozenset[str] = frozenset(mode.value for mode in LabelMode)


def is_label_mode(value: object) -> bool:
    return isinstance(value, str) and value in LABEL_MODES


def is_label_mode_map(value: object) -> bool:
    """True for None, or a dict of action key (str) -> label mode: the context / list label-mode knob (#216)."""
    if value is None:
        return True
    return isinstance(value, dict) and all(isinstance(k, str) and is_label_mode(v) for k, v in value.items())


def label_mode_check(context, owner: str, value, hint: str = "") -> CheckExpression:
    """System check viewset.E210: value must be one of the label modes; hint is appended to the message."""
    return CheckExpression(
        context=context,
        id="E210",
        expression=is_label_mode(value),
        msg=f"{owner} label_mode must be one of {sorted(LABEL_MODES)}, got {value!r}{hint}",
    )
