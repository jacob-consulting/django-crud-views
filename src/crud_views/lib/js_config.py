"""Theme-owned UI library namespace and tooltip placement defaults."""

import re

_js_namespace = "bootstrap"
_tooltip_placements: dict[str, str] = {}
_LOCATIONS = frozenset({"context", "list", "card", "card-order", "formset", "object-detail", "form", ""})
_PLACEMENTS = frozenset({"top", "bottom", "left", "right", "auto"})


def register_js_namespace(name: str) -> None:
    """Register a single global identifier at startup; the last valid call wins."""
    global _js_namespace
    if not isinstance(name, str) or re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name) is None:
        raise ValueError("JS namespace must match ^[A-Za-z_$][A-Za-z0-9_$]*$")
    _js_namespace = name


def register_tooltip_placements(placements: dict[str, str]) -> None:
    """Replace the whole placement mapping; invalid calls preserve previous state."""
    global _tooltip_placements
    if not isinstance(placements, dict):
        raise ValueError("Tooltip placements must be a dict of locations to placements")
    for location, placement in placements.items():
        if not isinstance(location, str) or location not in _LOCATIONS:
            raise ValueError("Unknown tooltip location")
        if not isinstance(placement, str) or placement not in _PLACEMENTS:
            raise ValueError("Unknown tooltip placement")
    _tooltip_placements = placements.copy()


def get_js_namespace() -> str:
    """Return the current namespace for internal rendering consumers."""
    return _js_namespace


def get_tooltip_placements() -> dict[str, str]:
    """Return an independent snapshot of the current placements."""
    return _tooltip_placements.copy()
