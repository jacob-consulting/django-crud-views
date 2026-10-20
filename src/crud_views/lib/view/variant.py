from enum import StrEnum

from ..check import CheckExpression


class Variant(StrEnum):
    """Semantic button variants: how prominent or dangerous an action is, independent of the theme."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    DANGER = "danger"


VARIANTS: frozenset[str] = frozenset(variant.value for variant in Variant)


def is_variant(value: object) -> bool:
    return isinstance(value, str) and value in VARIANTS


def variant_check(context, owner: str, value) -> CheckExpression:
    """System check viewset.E209: value must be one of the semantic variants."""
    return CheckExpression(
        context=context,
        id="E209",
        expression=is_variant(value),
        msg=f"{owner} variant must be one of {sorted(VARIANTS)}, got {value!r}",
    )
