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


def label_mode_check(context, owner: str, value) -> CheckExpression:
    """System check viewset.E210: value must be one of the label modes."""
    return CheckExpression(
        context=context,
        id="E210",
        expression=is_label_mode(value),
        msg=f"{owner} label_mode must be one of {sorted(LABEL_MODES)}, got {value!r}",
    )
