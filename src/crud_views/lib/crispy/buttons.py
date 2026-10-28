"""Crispy form buttons: classes from the layered button class table, rendered through the form-button leaf.

In a crispy ``Layout`` (e.g. ``FormActions``) a button renders as one ``<button>`` through
``crud_views/tags/button/form.html`` (Phase 6); a cancel configured with ``tag="a"`` or ``form:cancel-tag`` renders as
a native ``<a>`` link instead (Phase 6.1). Its value, label, name, id and attributes are literal text, never
template code. Added with ``helper.add_input()`` it stays a crispy input, rendered by the template pack.
"""

from crispy_forms import layout
from crispy_forms.utils import TEMPLATE_PACK
from django.template.loader import render_to_string

from crud_views.lib.button_classes import get_button_class

FORM_LEAF_TEMPLATE = "crud_views/tags/button/form.html"

# the semantic icon of each form kind (D-16); a button without an icon= argument uses its kind's icon
_KIND_ICONS = {
    "submit": "save",
    "delete": "delete",
    "cancel": "cancel",
    "filter-submit": "filter",
    "filter-reset": "filter-reset",
}

# the default of icon=: "not given", so an explicit None or "" stays an intentional "no icon". Compared only in the
# constructor: an adapter records the omission as a bool, which survives the filter helper's per-instance deepcopy
# (a copied object() would be a new, truthy non-sentinel icon)
_KIND_ICON = object()


# private context keys (underscore: unreadable from templates, never published by crispy's helper attributes)
# the owner a package helper pushes for the duration of its own render_layout (filter helper)
_CV_HELPER_OWNER = "_cv_helper_owner"
# the page-tier owner carried across the formset flatten / inclusion boundaries; None means "no page owner"
_CV_PAGE_OWNER = "_cv_page_owner"

# crispy's BasicNode.get_render pushes get_response_dict() for each {% crispy %} invocation: always these keys,
# plus every public helper attribute (which is how helper.view, even view=None, reaches the context)
_RESPONSE_KEYS = frozenset({"is_formset", "template_pack", "inputs"})
_RESPONSE_METHOD_KEYS = ("form_method", "formset_method")


def _is_response_overlay(layer) -> bool:
    """True for a crispy helper response layer (current or enclosing); such a layer is never a page layer."""
    return layer.keys() >= _RESPONSE_KEYS and any(key in layer for key in _RESPONSE_METHOD_KEYS)


def _cv_helper_tier(context):
    """The current crispy invocation's helper owner: a private entry pushed above its overlay, else its ``view``.

    Scans ``Context.dicts`` from the top and stops at the nearest response overlay, the current invocation; entries
    and overlays below it belong to enclosing invocations. No fixed stack offset: FormActions and nested rows
    leave other layers above the overlay.
    """
    for layer in reversed(context.dicts):
        if _CV_HELPER_OWNER in layer:
            return layer[_CV_HELPER_OWNER]
        if _is_response_overlay(layer):
            return layer.get("view")
    return None


def _cv_page_tier(context):
    """The page owner: the transported value when present (authoritative, even None), else the nearest ``view``
    that is not None in a genuine page layer. Every crispy response overlay is skipped, never read as a page.
    """
    for layer in reversed(context.dicts):
        if _CV_PAGE_OWNER in layer:
            return layer[_CV_PAGE_OWNER]
    for layer in reversed(context.dicts):
        if _is_response_overlay(layer):
            continue
        owner = layer.get("view")
        if owner is not None:
            return owner
    return None


def _cv_form_owner(form, context):
    """The view that owns a form button (D-09): the actual render form's ``cv_view``, then the current helper's
    owner, then the page owner; None when there is no owner.

    Identity, never truthiness: the first candidate that is not None is the owner, even a falsey object, and the
    lookup stops there (D-11). Conflicting owners are not reported (D-12). Reads the context only.
    """
    owner = getattr(form, "cv_view", None)
    if owner is None:
        owner = _cv_helper_tier(context)
    if owner is None:
        owner = _cv_page_tier(context)
    return owner


def _cv_form_label_mode(owner, kind: str) -> str:
    """The label mode of a form button of ``kind`` once its owner is selected (D-09 to D-13).

    A CrudView owner (class or instance) answers through its public seam ``cv_get_action_label_mode("form", kind)``,
    so subclass overrides apply. No owner, or an ordinary view without crud_views configuration, uses the settings
    singleton's form map, then the form floor; a lower view is never borrowed.
    """
    # deferred: crud_views.lib.view needs the app registry (see render)
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.view.base import CrudView
    from crud_views.lib.view.label_mode import form_label_mode

    if isinstance(owner, CrudView) or (isinstance(owner, type) and issubclass(owner, CrudView)):
        return owner.cv_get_action_label_mode("form", kind)
    return form_label_mode(crud_views_settings.form_actions_label_mode, kind)


class _TableClassMixin:
    """
    Sets the crispy ``field_classes`` of the instance from the button class table, before crispy
    appends a project supplied ``css_class``. ``slot`` (``"location:slot"``) picks the table key.

    ``icon`` is rendering configuration, never an HTML attribute: omitted, the slot's form kind picks its semantic
    icon (submit ``save``, delete ``delete``, cancel ``cancel``, filter-submit ``filter``, filter-reset
    ``filter-reset``); an explicit None or ``""`` means no icon.

    ``tag`` is rendering configuration too (Phase 6.1): None (the default) inherits ``form:cancel-tag``, ``"button"``
    keeps the native button and ``"a"`` asks for a native link. Only a cancel (the ``form:cancel`` slot with the
    native type ``button``) may ask for a link; any other value raises ValueError here, on both the layout and the
    legacy ``helper.add_input()`` path. Whether a link actually renders is decided per render (destination, disabled).

    On the layout path ``render()`` replaces crispy's: it never renders the value as a template and gives the
    selected template only the normalized form-button data (``FORM_LEAF_KEYS``), no ``input`` object.
    """

    slot: str
    # the bundled leaf; a subclass ``template`` or an explicit ``template=`` argument wins (``%s`` is the pack)
    template = FORM_LEAF_TEMPLATE

    def __init__(self, name, value, *, slot: str | None = None, icon=_KIND_ICON, tag=None, **kwargs):
        self._cv_slot = slot or self.slot
        # icon= omitted: the slot's kind picks the icon at render time; a bool copies as itself
        self._cv_kind_icon = icon is _KIND_ICON
        self._cv_icon = None if self._cv_kind_icon else icon
        # tag= is the explicit intent only (None inherits); the class table is read per render, never cached here
        self._cv_check_tag(tag)
        self._cv_tag = tag
        self.field_classes = get_button_class(*self._cv_slot.split(":", 1))
        self._cv_css_id = kwargs.get("css_id")
        self._cv_css_class = kwargs.get("css_class")
        self._cv_attrs = {k: v for k, v in kwargs.items() if k not in ("css_id", "css_class", "template")}
        super().__init__(name, value, **kwargs)

    def _cv_check_tag(self, tag) -> None:
        """Reject an unsupported explicit ``tag`` (D-01/D-03) and a link on a control that is not a cancel (D-09).

        None and exactly ``"button"`` are always accepted without looking at the slot, so legacy helper inputs with any
        slot stay quiet. ``"a"`` needs the ``form:cancel`` slot and the native type ``button``.
        """
        if tag is None or (isinstance(tag, str) and tag == "button"):
            return
        if not isinstance(tag, str) or tag != "a":
            raise ValueError(f"{type(self).__name__} tag must be 'button', 'a' or None, got {tag!r}")
        if self._cv_slot != "form:cancel" or self.input_type != "button":
            raise ValueError(
                f"{type(self).__name__} tag='a' is only for a cancel (slot 'form:cancel' with the native type"
                f" 'button'), got slot {self._cv_slot!r} with the native type {self.input_type!r}"
            )

    def _cv_form_kind(self) -> str:
        """The semantic form kind of the slot: ``form:<FORM_KINDS member>``, else ValueError (layout path only)."""
        from crud_views.lib.button_classes import FORM_KINDS

        location, _, kind = self._cv_slot.partition(":")
        if location != "form" or kind not in FORM_KINDS:
            raise ValueError(
                f"{type(self).__name__} slot must be 'form:<kind>' with a kind of {sorted(FORM_KINDS)} to render in"
                f" a layout, got {self._cv_slot!r}"
            )
        return kind

    def _cv_button_context(self) -> dict:
        """The raw form-button data this button hands to ``cv_button_data(ctx, "form")``."""
        kind = self._cv_form_kind()
        return {
            "cv_key": kind,
            "cv_type": self.input_type,
            "cv_name": self.name,
            "cv_value": self.value,
            "cv_id": self.id,
            "cv_css_id": self._cv_css_id,
            "cv_css_class": self._cv_css_class,
            "cv_attrs": dict(self._cv_attrs),
            "cv_icon": _KIND_ICONS[kind] if self._cv_kind_icon else self._cv_icon,
            # the raw tag intent: None inherits form:cancel-tag; the normalizer decides the effective tag
            "cv_tag": self._cv_tag,
        }

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        # deferred: crud_views.lib.view needs the app registry, and this module is imported by public form modules
        # (e.g. crud_views_workflow.lib) before django.setup()
        from crud_views.lib.view.button_data import cv_button_data

        raw = self._cv_button_context()
        raw["cv_label_mode"] = _cv_form_label_mode(_cv_form_owner(form, context), raw["cv_key"])
        data = cv_button_data(raw, "form")
        return render_to_string(self.get_template_name(template_pack), data)


class Submit(_TableClassMixin, layout.Submit):
    slot = "form:submit"


class Button(_TableClassMixin, layout.Button):
    slot = "form:cancel"


class Reset(_TableClassMixin, layout.Reset):
    slot = "form:filter-reset"
