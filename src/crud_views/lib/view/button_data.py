"""Normalise a resolved action dict into the flat leaf contract used by the button templates."""

import logging

from ..button_classes import get_icon_host_class
from ..exceptions import is_strict
from ..icons import resolve_icon_name_class
from .label_mode import LABEL_MODES, is_label_mode

logger = logging.getLogger(__name__)

LOCATIONS = frozenset({"context", "list", "card"})

KINDS = frozenset({"action", "menu-item"})

LEAF_KEYS = frozenset(
    {
        "cv_location",
        "cv_disabled",
        "cv_disabled_reason",
        "cv_tag",
        "cv_href",
        "cv_submit_target",
        "cv_modal",
        "cv_modal_size",
        "cv_active",
        "cv_key",
        "cv_label",
        "cv_short_label",
        "cv_label_mode",
        "cv_title",
        "cv_icon",
        "cv_variant",
        "cv_flex",
        "cv_icon_class",
        "cv_icon_inline",
    }
)


def icon_host_keys(icon: str | None, location: str) -> tuple[str, bool]:
    """``(cv_icon_class, cv_icon_inline)`` for an icon on a button at ``location`` (#258).

    A host-placed icon puts the ``location:icon-host`` class on the button and renders nothing inside it (a slot
    set to None switches it off: no class, nothing inline); any other icon renders inline as an element.
    """
    if resolve_icon_name_class(icon) is None:
        return "", True
    return get_icon_host_class(location, icon), False


def cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict:
    """Turn a resolved action dict into a flat leaf contract dict. Never mutates ctx.

    Every decision the button templates used to take in branches (element, disabled, form post
    or modal, label mode, title) is taken here, once.
    """
    if location not in LOCATIONS:
        raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    if "cv_no_label" in ctx:
        raise ValueError(
            "cv_no_label is no longer a leaf input; use CardAction.label_mode or cv_label_mode"
            " (it is also picked up from the page template context, so check for a stray cv_no_label variable there)"
        )
    card = location == "card"

    disabled = bool(ctx.get("cv_disabled"))
    modal = bool(ctx.get("cv_modal")) and not disabled
    is_post = ctx.get("cv_list_action_method") == "post"
    tag = "button" if disabled or (is_post and not ctx.get("cv_modal")) else "a"

    if card:
        label = (
            ctx.get("cv_label") or ctx.get("cv_action_short_label") or ctx.get("cv_action_label") or ctx.get("cv_key")
        ) or ""
        short_label = label
    else:
        label = ctx.get("cv_action_label", "") or ""
        short_label = ctx.get("cv_action_short_label") or ctx.get("cv_action_label") or ""
    # cards default to both; context and list to icon, unless the view stamped a mode for the key (#216)
    label_mode = ctx.get("cv_label_mode") or ("both" if card else "icon")
    if not is_label_mode(label_mode):
        raise ValueError(f"cv_label_mode must be one of {sorted(LABEL_MODES)}, got {label_mode!r}")
    if not label:
        label_mode = "icon"
    if kind == "action" and label_mode == "icon" and not ctx.get("cv_icon_action"):
        # an icon-only button without an icon renders nothing visible: fail in strict mode, else show the label (#264)
        where = f"{location} action {ctx.get('cv_action_key') or ctx.get('cv_key', '')!r}"
        if is_strict():
            raise ValueError(
                f"{where} renders icon-only but has no icon; give it an icon (cv_icon_action, or icon_header of the"
                " ViewSet a parent, child or sibling button points to), or a label mode of 'label' or 'both'"
                " (ContextButton.label_mode or a label-mode map)"
            )
        if label:
            label_mode = "label"
            logger.warning("%s has no icon; rendered with its label instead", where)
        else:
            logger.warning("%s has neither an icon nor a label and renders empty", where)
    if not card and label_mode != "icon":
        # the visible text of a labelled toolbar or row button is the short label; icon mode keeps the full
        # label as the hidden text and the title (#216)
        label = short_label

    data = {
        "cv_location": location,
        "cv_disabled": disabled,
        "cv_disabled_reason": ctx.get("cv_disabled_reason", ""),
        "cv_tag": tag,
        "cv_modal": modal,
        "cv_modal_size": ctx.get("cv_modal_size", ""),
        "cv_active": bool(ctx.get("cv_is_active")) and not disabled,
        "cv_key": ctx.get("cv_key", ""),
        "cv_label": label,
        "cv_short_label": short_label,
        "cv_label_mode": label_mode,
        "cv_icon": ctx.get("cv_icon_action"),
        "cv_variant": ctx.get("cv_variant") or "secondary",
        "cv_flex": card and bool(ctx.get("cv_flex")),
    }
    # a menu item always shows its icon and uses the menu slot; a text-only action button shows none (#258)
    icon_class, icon_inline = icon_host_keys(data["cv_icon"], "menu" if kind == "menu-item" else location)
    if kind == "action" and label_mode == "label":
        icon_class = ""
    data["cv_icon_class"] = icon_class
    data["cv_icon_inline"] = icon_inline
    if tag == "a":
        data["cv_href"] = ctx["cv_url"]
    elif not disabled:
        data["cv_submit_target"] = f"cv_form_{ctx['cv_oid']}"
    if label_mode == "icon":
        data["cv_title"] = label
    return data
