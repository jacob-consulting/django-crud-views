"""Normalise a resolved action dict into the flat leaf contract used by the button templates."""

LOCATIONS = frozenset({"context", "list", "card"})

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
        "cv_label_visible",
        "cv_title",
        "cv_icon",
        "cv_variant",
        "cv_flex",
    }
)


def cv_button_data(ctx: dict, location: str) -> dict:
    """Turn a resolved action dict into a flat leaf contract dict. Never mutates ctx.

    Every decision the button templates used to take in branches (element, disabled, form post
    or modal, label visibility, title) is taken here, once.
    """
    if location not in LOCATIONS:
        raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")
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
    label_visible = card and bool(label) and not ctx.get("cv_no_label")

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
        "cv_label_visible": label_visible,
        "cv_icon": ctx.get("cv_icon_action"),
        "cv_variant": ctx.get("cv_variant") or "secondary",
        "cv_flex": card and bool(ctx.get("cv_flex")),
    }
    if tag == "a":
        data["cv_href"] = ctx["cv_url"]
    elif not disabled:
        data["cv_submit_target"] = f"cv_form_{ctx['cv_oid']}"
    if not label_visible:
        data["cv_title"] = label
    return data
