"""Normalise a resolved action dict into the flat leaf contract used by the button templates.

The ``"form"`` location (Phase 6) has its own finite contract, ``FORM_LEAF_KEYS``: the crispy form-button adapters
(``crud_views.lib.crispy.buttons``) hand their raw data to ``cv_button_data(ctx, "form")`` and render the result.
"""

import logging

from django.forms.utils import flatatt
from django.utils.text import slugify

from ..button_classes import FORM_KINDS, get_button_classes, get_icon_host_class
from ..exceptions import is_strict
from ..icons import _icon_available, resolve_icon_name_class
from .label_mode import LABEL_MODES, _invalid_label_mode, default_label_mode, is_label_mode

logger = logging.getLogger(__name__)

LOCATIONS = frozenset({"context", "list", "card", "form"})

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

# the complete contract of a form button (location "form"); cv_title only in icon mode, cv_cancel_url only for the
# cancel kind. cv_tag (Phase 6.1) is the effective element, "a" or "button", on every form button. None of the
# action-only keys (href, submit target, modal, variant, ...) is ever part of it
FORM_LEAF_KEYS = frozenset(
    {
        "cv_location",
        "cv_key",
        "cv_type",
        "cv_name",
        "cv_value",
        "cv_label",
        "cv_id",
        "cv_label_mode",
        "cv_icon",
        "cv_icon_class",
        "cv_icon_inline",
        "cv_css_class",
        "cv_flat_attrs",
        "cv_title",
        "cv_cancel_url",
        "cv_tag",
    }
)

# the native type of a form button
FORM_TYPES = frozenset({"submit", "button", "reset"})

# the elements a form button may render as (Phase 6.1): exactly these strings, never stripped or case-folded
FORM_TAGS = frozenset({"button", "a"})

# the class-table key selecting the element of an eligible cancel; a value of None means "button"
CANCEL_TAG_KEY = "form:cancel-tag"


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
    if location == "form":
        # the third argument is the rendering category: a form button is always an "action"; its semantic kind
        # is ctx["cv_key"], never this argument
        if kind != "action":
            raise ValueError(f'kind must be "action" for location "form", got {kind!r}')
        return _form_button_data(ctx)
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
    # a mode the view stamped for the key wins (#216); unset (falsey), the location's floor from
    # default_label_mode: CRUD_VIEWS_LABEL_MODE_DEFAULTS over the package defaults (card both, context / list icon).
    # A malformed stamp raises in strict mode, else it logs once and uses that floor
    label_mode = ctx.get("cv_label_mode")
    if not label_mode:
        label_mode = default_label_mode(location)
    elif not is_label_mode(label_mode):
        label_mode = _invalid_label_mode(
            f"cv_label_mode must be one of {sorted(LABEL_MODES)}",
            location,
            label_mode,
            lambda: default_label_mode(location),
        )
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


def _literal(value) -> str:
    """The exact text of a value as a plain str: None is "", lazy text resolves in the active language.

    Never escapes; the result is no SafeString (str() of a SafeString is that SafeString), so the leaf's
    autoescaping is the one escaping boundary and marked-safe input stays literal text.
    """
    if value is None:
        return ""
    return str.__str__(str(value))


def _form_attrs(raw) -> dict:
    """Extra attributes with underscore aliases normalized to hyphens (crispy flatatt semantics); when two spellings
    name one attribute, the hyphenated one wins whatever the keyword order."""
    attrs: dict = {}
    for key, value in (raw or {}).items():
        name = str(key).replace("_", "-")
        if name in attrs and name != key:
            continue
        attrs[name] = value
    return attrs


def _attr_text(value) -> str | None:
    """An attribute value given as text, or None when it is absent (None / False)."""
    if value is None or value is False:
        return None
    return _literal(value)


def _is_form_tag(value) -> bool:
    """True for exactly ``"button"`` or ``"a"``; the type is checked first, so an unhashable is simply False."""
    return isinstance(value, str) and value in FORM_TAGS


def _selected_form_tag(ctx: dict, key: str, button_type: str) -> str:
    """The tag selected for a form button, validated before any destination or disabled fallback (D-04).

    An explicit ``cv_tag`` wins and is the only value read (D-12): an invalid one, or ``"a"`` on a control that is
    not an eligible cancel (the cancel kind with the native type ``button``, D-09), raises ValueError whatever the
    strictness. Otherwise an eligible cancel reads the raw ``form:cancel-tag`` class-table value: absent or None
    selects ``"button"`` (D-02); an invalid value raises in strict mode, else it logs and selects ``"button"`` (D-01).
    Any other control inherits ``"button"`` without reading the table (D-11).
    """
    eligible = key == "cancel" and button_type == "button"
    explicit = ctx.get("cv_tag")
    if explicit is not None:
        if not _is_form_tag(explicit):
            raise ValueError(f"form button cv_tag must be one of {sorted(FORM_TAGS)} or None, got {explicit!r}")
        if explicit == "a" and not eligible:
            raise ValueError(
                f"form button cv_tag 'a' is only for a cancel (cv_key 'cancel' with the cv_type 'button'), got"
                f" {key!r} with {button_type!r}"
            )
        return explicit
    if not eligible:
        return "button"
    configured = get_button_classes().get(CANCEL_TAG_KEY)
    if configured is None or _is_form_tag(configured):
        return configured or "button"
    message = f"button class {CANCEL_TAG_KEY!r} = {configured!r} is not one of {sorted(FORM_TAGS)} or None"
    if is_strict():
        raise ValueError(message)
    logger.warning("%s; the cancel is rendered as 'button'", message)
    return "button"


def _emits_disabled(attrs: dict) -> bool:
    """True when the extra attributes emit a ``disabled`` attribute in any letter case (HTML presence semantics:
    every value except False and None is emitted, even ``""``, ``0`` or ``"false"``)."""
    return any(
        isinstance(name, str) and name.lower() == "disabled" and value is not False and value is not None
        for name, value in attrs.items()
    )


def _form_button_data(ctx: dict) -> dict:
    """The FORM_LEAF_KEYS contract of one form button. Never mutates ctx.

    Input keys: ``cv_key`` (a FORM_KINDS member), ``cv_type`` (submit / button / reset), ``cv_name``, ``cv_value``,
    optional ``cv_label`` (default: the value's text), ``cv_id`` (the generated id), ``cv_css_id``,
    ``cv_css_class``, ``cv_attrs`` (the extra attributes), ``cv_label_mode``, ``cv_icon`` and ``cv_tag`` (the
    explicit tag intent; None or absent inherits ``form:cancel-tag``).
    """
    key = ctx.get("cv_key")
    if not isinstance(key, str) or key not in FORM_KINDS:
        raise ValueError(f"form button cv_key must be one of {sorted(FORM_KINDS)}, got {key!r}")
    button_type = ctx.get("cv_type")
    if not isinstance(button_type, str) or button_type not in FORM_TYPES:
        raise ValueError(f"form button cv_type must be one of {sorted(FORM_TYPES)}, got {button_type!r}")
    selected_tag = _selected_form_tag(ctx, key, button_type)

    label_mode = ctx.get("cv_label_mode")
    if not label_mode:
        label_mode = default_label_mode("form")
    elif not is_label_mode(label_mode):
        label_mode = _invalid_label_mode(
            f"cv_label_mode must be one of {sorted(LABEL_MODES)}",
            "form",
            label_mode,
            lambda: default_label_mode("form"),
        )

    name = _literal(ctx.get("cv_name"))
    value = _literal(ctx.get("cv_value"))
    label = _literal(ctx["cv_label"]) if "cv_label" in ctx else value

    # the leaf contract: a nonblank str or None. Anything else (a non-str, a blank string) is "no icon" everywhere:
    # availability, diagnostics, host classes and the leaf; an accepted string is kept exactly, never stripped
    icon = ctx.get("cv_icon")
    if not isinstance(icon, str) or not icon.strip():
        icon = None
    if label_mode == "icon" and not _icon_available(icon):
        # an icon-only form button without a usable icon renders nothing visible (D-16): fail in strict mode, else
        # show the literal label, on every render. Decided without rendering: the leaf's one cv_icon call stays the
        # only renderer invocation
        where = f"form button {key!r}"
        if is_strict():
            raise ValueError(
                f"{where} renders icon-only but its icon {icon!r} is not available; set a usable icon (icon=,"
                " submit_icon, delete_icon or CRUD_VIEWS_ICONS) or the form label mode 'label' or 'both'"
            )
        label_mode = "label"
        if label:
            logger.warning(
                "%s renders icon-only but its icon %r is not available; rendered with its label instead", where, icon
            )
        else:
            logger.warning("%s has neither an available icon (%r) nor a label and renders empty", where, icon)

    # reserved attributes resolve once: type, name and value come from the button itself
    attrs = _form_attrs(ctx.get("cv_attrs"))
    for reserved in ("type", "name", "value"):
        attrs.pop(reserved, None)
    extra_id = _attr_text(attrs.pop("id", None))
    css_id = ctx.get("cv_css_id")
    button_id = _literal(css_id) if css_id else extra_id if extra_id is not None else _literal(ctx.get("cv_id"))
    classes = [_literal(c) for c in (ctx.get("cv_css_class"), _attr_text(attrs.pop("class", None))) if c]
    cancel_url = _attr_text(attrs.pop("data-cv-cancel-url", None)) if key == "cancel" else None
    # the effective tag (D-06, D-08, D-10, D-14): a link needs the selected "a", a nonempty destination and no emitted
    # disabled attribute; anything else keeps the native button, its disabled attribute serialized as before
    tag = "a" if selected_tag == "a" and cancel_url and not _emits_disabled(attrs) else "button"
    if label_mode == "icon":
        # the generated title and tooltip marker win over caller attributes of the same name
        attrs.pop("title", None)
        attrs.pop("data-cv-tooltip", None)
    flat_attrs = flatatt({k: v if isinstance(v, bool) or v is None else _literal(v) for k, v in attrs.items()})

    if label_mode == "label":
        icon_class, icon_inline = "", True
    else:
        icon_class, icon_inline = icon_host_keys(icon, "form")

    data = {
        "cv_location": "form",
        "cv_key": key,
        "cv_type": button_type,
        # crispy's baseinput rule: a name of more than one word is submitted slugified, a single word as it is
        "cv_name": slugify(name) if len(name.split()) > 1 else name,
        "cv_value": value,
        "cv_label": label,
        "cv_id": button_id,
        "cv_label_mode": label_mode,
        "cv_icon": icon,
        "cv_icon_class": icon_class,
        "cv_icon_inline": icon_inline,
        "cv_css_class": " ".join(classes),
        "cv_flat_attrs": flat_attrs,
        "cv_tag": tag,
    }
    if label_mode == "icon":
        data["cv_title"] = label
    if key == "cancel":
        data["cv_cancel_url"] = cancel_url
    return data
