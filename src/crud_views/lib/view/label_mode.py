import logging
import threading
from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType

from ..check import CheckExpression

logger = logging.getLogger(__name__)


class LabelMode(StrEnum):
    """How a button shows its label: text only, icon only, or both."""

    LABEL = "label"
    ICON = "icon"
    BOTH = "both"


LABEL_MODES: frozenset[str] = frozenset(mode.value for mode in LabelMode)

# the package floor per button location: read-only, CRUD_VIEWS_LABEL_MODE_DEFAULTS is merged over it per key
LABEL_MODE_DEFAULTS: Mapping[str, str] = MappingProxyType(
    {"context": "icon", "list": "icon", "card": "both", "form": "label"}
)

# marks CRUD_VIEWS_LABEL_MODE_DEFAULTS as absent (an explicit None is invalid, not absent)
_UNSET = object()

# (location, repr(value)) pairs already warned about: once per process, renders are hot paths
_warned: set[tuple[str, str]] = set()
_warned_lock = threading.Lock()


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


def _raw_label_mode_defaults() -> object:
    """The raw CRUD_VIEWS_LABEL_MODE_DEFAULTS, read at call time (override_settings applies); _UNSET if absent."""
    from django.conf import settings

    return getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)


def _invalid_label_mode(source: str, location: str, value: object, fallback: Callable[[], str]) -> str:
    """A malformed label mode: raise in strict mode, else warn once per (location, value) and use fallback().

    ``source`` describes what is malformed and what it must be. In strict mode this raises before fallback runs,
    so the error names the original source even when the fallback is malformed too. Otherwise fallback() is
    resolved first (it may re-enter this helper), and the lock guards only the check-and-add on the register:
    neither the fallback nor the logging runs under it.
    """
    from ..exceptions import is_strict

    if is_strict():
        raise ValueError(f"{source}, got {value!r}")
    resolved = fallback()
    pair = (location, repr(value))
    with _warned_lock:
        first = pair not in _warned
        if first:
            _warned.add(pair)
    if first:
        logger.warning("%s, got %r; the %s button uses %r", source, value, location, resolved)
    return resolved


def default_label_mode(location: str) -> str:
    """The label-mode floor of a button location: CRUD_VIEWS_LABEL_MODE_DEFAULTS merged per key over
    LABEL_MODE_DEFAULTS.

    Read on every call. A location outside button_data.LOCATIONS is a caller bug and raises in every mode. A
    malformed setting, or a malformed mode for this location, raises in strict mode and otherwise falls back to
    the package default for the location (logged once); unknown keys in the setting are ignored here (E108).
    """
    # deferred: button_data imports this module
    from .button_data import LOCATIONS

    if not isinstance(location, str) or location not in LOCATIONS:
        raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")
    raw = _raw_label_mode_defaults()
    if raw is _UNSET:
        return LABEL_MODE_DEFAULTS[location]
    if not isinstance(raw, dict):
        return _invalid_label_mode(
            f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS must be a dict of location -> one of {sorted(LABEL_MODES)}",
            location,
            raw,
            lambda: LABEL_MODE_DEFAULTS[location],
        )
    if location not in raw:
        return LABEL_MODE_DEFAULTS[location]
    value = raw[location]
    if is_label_mode(value):
        return value
    return _invalid_label_mode(
        f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key {location!r} must be one of {sorted(LABEL_MODES)}",
        location,
        value,
        lambda: LABEL_MODE_DEFAULTS[location],
    )
