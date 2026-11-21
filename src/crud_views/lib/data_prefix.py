"""Theme-owned native data-API attribute prefix."""

import re

_data_prefix = "bs"


def register_data_prefix(prefix: str) -> None:
    """Register a theme's prefix at startup; the last valid call wins.

    Invalid values raise ValueError without changing the previous registration.
    """
    global _data_prefix
    if not isinstance(prefix, str) or re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", prefix) is None:
        raise ValueError("Data prefix must match ^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
    _data_prefix = prefix


def get_data_prefix() -> str:
    """Return the current prefix for internal rendering consumers."""
    return _data_prefix
