from typing import Any

from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _
from pydantic import BaseModel, Field

from ..check import CheckExpression, CheckWarningExpression
from ..exceptions import ViewSetNotFoundError
from ..settings import crud_views_settings
from .action_menu import cv_is_inline_keys
from .context import ViewContext
from .label_mode import (
    LABEL_MODES,
    _invalid_label_mode,
    default_label_mode,
    is_label_mode,
    is_label_mode_map,
    label_mode_check,
)
from .variant import variant_check


def _is_registered(viewset, key: str) -> bool:
    """True when key is a registered view of viewset, "list" falling back to "card" like get_view_class."""
    return viewset.is_view_registered(key) or (key == "list" and viewset.is_view_registered("card"))


class ContextButton(BaseModel):
    """
    A context button is a button that is rendered in the context of a CrudView
    """

    key: str
    key_target: str | None = None
    label_template: str | None = None
    label_template_code: str | None = None
    template: str | None = None
    template_code: str | None = None
    variant: str | None = None  # None: the target view's cv_action_variant
    label_mode: str | None = None  # None: the view's context label-mode maps; one of LABEL_MODES (#264)

    @staticmethod
    def _resolve_container_key(viewset, key_target: str) -> str:
        if key_target == "list" and not viewset.is_view_registered("list") and viewset.is_view_registered("card"):
            return "card"
        return key_target

    def _problem(self, msg: str) -> str:
        return f"context button {self.key!r} ({type(self).__name__}): {msg}"

    def cv_check_target(self, viewset) -> str | None:
        """
        System check viewset.E255: why this button's target does not resolve on viewset, or None.
        Subclasses with their own get_context() may not use key_target and are skipped.
        """
        if type(self).get_context is not ContextButton.get_context or self.key_target is None:
            return None
        if not _is_registered(viewset, self.key_target):
            return self._problem(f"key_target {self.key_target!r} is not registered at ViewSet {viewset.name!r}")
        return None

    def render_label(self, data: dict, context: ViewContext) -> str:
        if self.label_template:
            return context.view.render_snippet(data, self.label_template)
        elif self.label_template_code:
            return context.view.render_snippet(data, template_code=self.label_template_code)

    def _apply_label(self, data: dict, context: ViewContext) -> None:
        """Override the seeded default labels when this button declares its own label_template[_code].

        The declared label becomes both cv_action_label and cv_action_short_label, so it is the button's
        label everywhere, including action menu items (which render the short label). render_label()
        returns None when neither is set, so the target view's default labels (already in data) are
        preserved. Shared by every button subclass so none can forget it.
        """
        cv_action_label = self.render_label(data, context)
        if cv_action_label:
            data["cv_action_label"] = cv_action_label
            data["cv_action_short_label"] = cv_action_label

    def _apply_variant(self, data: dict) -> None:
        """Override the target view's default variant when this button declares its own."""
        if self.variant is not None:
            data["cv_variant"] = self.variant

    def _inject_template(self, data: dict) -> None:
        if self.template_code:
            data["cv_template_code"] = self.template_code
        elif self.template:
            data["cv_template"] = self.template
        else:
            data["cv_template"] = crud_views_settings.context_button_template

    def get_context(self, context: ViewContext) -> dict:
        key_target = self._resolve_container_key(context.view.cv_viewset, self.key_target)

        # get target view class
        cls = context.view.cv_get_cls_assert_object(key_target, context.object)

        dict_kwargs = {
            "cv_access": False,
            "cv_url": context.view.cv_get_link_url(cls, key_target, context.object),
            # id of the hidden POST form when the target is POST-only (#178)
            "cv_oid": context.view.cv_get_oid(key=key_target, obj=context.object),
        }

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls._cv_action_enabled_for_rendering(
            context.view.request.user, context.object, context.view
        )

        # check access
        if cls.cv_has_access(context.view.request.user, context.object):
            # get the url for the target key
            dict_kwargs.update(
                cv_access=True,
            )

        # final data
        data = cls.cv_get_dict(context=context, **dict_kwargs)

        # render action label
        self._apply_label(data, context)
        self._apply_variant(data)

        self._inject_template(data)

        return data


class ParentContextButton(ContextButton):
    """
    A context button that
    """

    def cv_check_target(self, viewset) -> str | None:
        if not viewset.parent:
            return self._problem(f"ViewSet {viewset.name!r} has no parent")
        parent = viewset.parent.viewset
        if self.key_target is None or not _is_registered(parent, self.key_target):
            return self._problem(f"key_target {self.key_target!r} is not registered at parent ViewSet {parent.name!r}")
        return None

    def get_context(self, context: ViewContext) -> dict:

        # does the view has no parent?
        if not context.view.cv_viewset.parent:
            return {}

        # get the parent view class, defined by target
        parent = context.view.cv_viewset.parent
        key_target = self._resolve_container_key(parent.viewset, self.key_target)
        cls = parent.viewset.get_view_class(key_target)

        dict_kwargs = {"cv_access": False, "cv_icon_action": cls.cv_viewset.icon_header}

        # parent url kwargs
        kwargs = {}
        for idx, arg in enumerate(context.view.cv_viewset.get_parent_url_args()):
            if idx == 0:
                if cls.cv_object:
                    kwargs[parent.viewset.pk_name] = context.view.kwargs[arg]
            else:
                kwargs[arg] = context.view.kwargs[arg]

        # parent url
        router_name = parent.viewset.get_router_name(key_target)
        cv_url = reverse(router_name, kwargs=kwargs)

        # get the url for the target key
        dict_kwargs.update(cv_url=cv_url)

        # the button links UP to the parent, so access is governed by the PARENT
        # object — not context.object (the child instance, or None on a list page).
        parent_obj = None
        if hasattr(context.view, "cv_get_parent_object"):
            try:
                parent_obj = context.view.cv_get_parent_object()
            except (Http404, KeyError):
                parent_obj = None

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls._cv_action_enabled_for_rendering(
            context.view.request.user, parent_obj, context.view
        )

        # check permission against the parent object
        if cls.cv_has_access(context.view.request.user, parent_obj):
            dict_kwargs.update(
                cv_access=True,
            )

        data = cls.cv_get_dict(context=context, **dict_kwargs)

        self._apply_label(data, context)
        self._apply_variant(data)

        self._inject_template(data)
        return data


class ChildContextButton(ContextButton):
    """
    A context button that links to a child viewset (e.g. from parent detail to child list).
    """

    child_name: str
    child_key: str = "list"

    def cv_check_target(self, viewset) -> str | None:
        try:
            child_vs = viewset.get_viewset(self.child_name)
        except ViewSetNotFoundError:
            return self._problem(f"child_name {self.child_name!r} is not a registered ViewSet")
        if not child_vs.parent or child_vs.parent.name != viewset.name:
            return self._problem(f"ViewSet {self.child_name!r} is not a child of ViewSet {viewset.name!r}")
        if not _is_registered(child_vs, self.child_key):
            return self._problem(f"child_key {self.child_key!r} is not registered at ViewSet {self.child_name!r}")
        return None

    def get_context(self, context: ViewContext) -> dict:
        if context.object is None:
            return {}

        child_vs = context.view.cv_viewset.get_viewset(self.child_name)
        cls = child_vs.get_view_class(self.child_key)

        url = context.view.cv_get_child_url(self.child_name, self.child_key, context.object)

        dict_kwargs = {
            "cv_access": False,
            "cv_url": url,
            "cv_icon_action": child_vs.icon_header,
        }

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls._cv_action_enabled_for_rendering(
            context.view.request.user, context.object, context.view
        )

        if cls.cv_has_access(context.view.request.user, context.object):
            dict_kwargs.update(cv_access=True)

        data = cls.cv_get_dict(context=context, **dict_kwargs)

        self._apply_label(data, context)
        self._apply_variant(data)

        self._inject_template(data)

        return data


class SiblingContextButton(ContextButton):
    """
    A context button on a child view that links to a sibling collection — another child of
    the same parent — reusing the parent PK already present in the current URL.

    Collection-only: a sibling button has no specific sibling object in scope, so object-gated
    sibling views (detail/update/delete) are unsupported — access is checked with obj=None,
    which is correct only for collection targets (list/card, whose access is unconditional).
    """

    sibling_name: str
    sibling_key: str = "list"

    def cv_check_target(self, viewset) -> str | None:
        try:
            sibling_vs = viewset.get_viewset(self.sibling_name)
        except ViewSetNotFoundError:
            return self._problem(f"sibling_name {self.sibling_name!r} is not a registered ViewSet")
        if not _is_registered(sibling_vs, self.sibling_key):
            return self._problem(f"sibling_key {self.sibling_key!r} is not registered at ViewSet {self.sibling_name!r}")
        return None

    def get_context(self, context: ViewContext) -> dict:
        # only rendered on child views (those with a parent)
        if not context.view.cv_viewset.parent:
            return {}

        sibling_vs = context.view.cv_viewset.get_viewset(self.sibling_name)
        sibling_key = self._resolve_container_key(sibling_vs, self.sibling_key)
        cls = sibling_vs.get_view_class(sibling_key)

        # the sibling shares the current view's parent chain, so reuse its URL args
        kwargs = {arg: context.view.kwargs[arg] for arg in sibling_vs.get_parent_url_args()}
        cv_url = reverse(sibling_vs.get_router_name(sibling_key), kwargs=kwargs)

        dict_kwargs = {
            "cv_access": False,
            "cv_url": cv_url,
            "cv_icon_action": sibling_vs.icon_header,
        }

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls._cv_action_enabled_for_rendering(
            context.view.request.user, None, context.view
        )

        if cls.cv_has_access(context.view.request.user, None):
            dict_kwargs.update(cv_access=True)

        data = cls.cv_get_dict(context=context, **dict_kwargs)

        self._apply_label(data, context)
        self._apply_variant(data)

        self._inject_template(data)

        return data


class FilterContextButton(ContextButton):
    """
    A context button that
    """

    key: str = "filter"
    template: str | None = Field(
        default_factory=lambda: f"{crud_views_settings.theme_path}/tags/context_action_filter.html"
    )

    def get_context(self, context: ViewContext) -> dict:
        from ..views import ListViewTableFilterMixin

        dict_kwargs = {"cv_access": False}

        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
            return dict_kwargs

        # pinned filter is always visible -> no toggle button
        if getattr(context.view, "cv_filter_pinned", False):
            return dict_kwargs

        list_url = context.view.cv_get_url(key=context.view.cv_key)

        data = {"cv_access": True}  # it toggles the filter of the list page the user is already on
        # no target view, so cv_key is the button's own key, not a view key like every other button (#208)
        data["cv_key"] = self.key
        # the resolved mode of the button's declared key (#262); no target view, so no target default: the view's
        # own map, this button's label_mode, the first map of view / ViewSet / setting, then the context floor
        mode = context.view.cv_get_action_label_mode("context", self.key, self)
        if not is_label_mode(mode):
            mode = _invalid_label_mode(
                f"context action {self.key!r} cv_label_mode must be one of {sorted(LABEL_MODES)}",
                "context",
                mode,
                lambda: default_label_mode("context"),
            )
        data["cv_label_mode"] = mode
        data["cv_action_label"] = _("Filter")  # translated per render, in the active language
        data["cv_icon_action"] = "filter"
        data["cv_filter_expanded"] = context.view.cv_filter_expanded
        data["cv_url"] = list_url
        self._apply_label(data, context)
        self._apply_variant(data)
        self._inject_template(data)

        return data


def context_buttons_default(*args, **kwargs) -> Any:
    return [
        ContextButton(
            key="home",
            key_target="list",
            # I don't think we need templates here because the title should be the one of the
            # list page where it links to
        ),
        ParentContextButton(key="parent", key_target="list"),
        FilterContextButton(),
    ]


def context_button_checks(context, viewset, buttons: list[ContextButton] | None):
    """
    System checks viewset.E255 for explicitly configured context buttons, and the variant and label mode (E210) of
    every button. Buttons equal to a default
    are skipped: their target is legitimately absent on e.g. a detail-only or root ViewSet (#132).
    """
    defaults = context_buttons_default()
    for button in buttons or []:
        if button.variant is not None:
            yield variant_check(context, f"context button {button.key!r}", button.variant)
        if button.label_mode is not None:
            yield label_mode_check(context, f"context button {button.key!r}", button.label_mode)
        if button in defaults:
            continue
        problem = button.cv_check_target(viewset)
        yield CheckExpression(context=context, id="E255", expression=problem is None, msg=problem or "")


def cv_icon_mode_checks(cls):
    """System check viewset.W292: a context toolbar key that renders icon-only although its target has no icon (#264).

    The mode is resolved as at render time, including the target view's cv_context_action_label_mode (#269) and the
    context floor of CRUD_VIEWS_LABEL_MODE_DEFAULTS. A key whose resolution raises because that floor is invalid in
    strict mode is skipped: crud_views.E108 reports the setting, and the other checks still run.

    Only what is known statically: keys folded into the action menu (a menu item always shows its label), buttons
    with their own template or get_context() and unregistered targets are skipped; cv_button_data() covers the rest
    at render time.
    """
    if not is_label_mode_map(cls.cv_get_context_actions_label_mode()):
        return  # viewset.E211 / crud_views.E106 report it
    if not cv_is_inline_keys(cls.cv_get_context_actions_inline()):
        return  # the inline-keys checks report it
    viewset = cls.cv_viewset
    inline = cls.cv_get_context_actions_inline()
    for key in cls.cv_context_actions or []:
        if inline is not None and key not in inline:
            continue
        button = cls._cv_find_context_button(cls.cv_context_buttons, viewset, key)
        if button is None:
            target = key
        elif (
            type(button).get_context is not ContextButton.get_context
            or button.template
            or button.template_code
            or button.key_target is None
        ):
            continue
        else:
            target = ContextButton._resolve_container_key(viewset, button.key_target)
        if not _is_registered(viewset, target):
            continue
        target_cls = viewset.get_view_class(target)
        # the target view's own toolbar mode (#269); an invalid value counts as unset, viewset.E210 reports it
        target_default = target_cls.cv_context_action_label_mode
        if not is_label_mode(target_default):
            target_default = None
        try:
            mode = cls.cv_get_action_label_mode("context", key, button, target_default)
        except ValueError:
            continue  # an invalid CRUD_VIEWS_LABEL_MODE_DEFAULTS floor in strict mode: crud_views.E108 reports it
        if mode != "icon":
            continue
        yield CheckWarningExpression(
            context=cls,
            id="W292",
            expression=bool(target_cls.cv_icon_action),
            msg=(
                f"context action {key!r} of {cls.__name__} renders icon-only but has no icon; give it an icon or a "
                "label mode ('label' or 'both')"
            ),
        )


def _declared(klass: type, name: str) -> Any:
    """The attribute as declared in the MRO (the property or function object itself, never bound), else None."""
    for base in klass.__mro__:
        if name in vars(base):
            return vars(base)[name]
    return None


def _inherits(klass: type, name: str, owner: type) -> bool:
    """True when ``klass`` still uses ``owner``'s own implementation of ``name`` (no subclass override)."""
    return _declared(klass, name) is vars(owner)[name]


def _static_form_classes(cls) -> list[type]:
    """The crispy package form classes a view selects without a request, in order and without duplicates.

    Only Django's own get_form_class (``form_class``) and the polymorphic mixin's (each value of a concrete dict
    ``polymorphic_forms``) are understood; any other get_form_class is request-dependent and skipped. Nothing is
    called or instantiated.
    """
    from crud_views.lib.crispy.form import CrispyFormMixin

    getter = _declared(cls, "get_form_class")
    module = getattr(getter, "__module__", None) or ""
    if module.startswith("django.views."):
        candidates = [_declared(cls, "form_class")]
    elif module.startswith("crud_views_polymorphic.") and (
        getattr(getter, "__qualname__", "") == "PolymorphicCrudViewMixin.get_form_class"
    ):
        mapping = _declared(cls, "polymorphic_forms")
        candidates = list(mapping.values()) if isinstance(mapping, dict) else []
    else:
        return []
    forms: list[type] = []
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, CrispyFormMixin) and candidate not in forms:
            forms.append(candidate)
    return forms


def _static_form_controls(form_class: type) -> list[tuple[str, Any]]:
    """(form kind, icon) of each control a package form helper renders, for the hooks that are still the package's.

    The provider is chosen before the controls: CrispyDeleteForm's helper renders delete (delete_icon) and cancel,
    never its inherited submit; otherwise CrispyFormMixin's helper (also the workflow form) renders submit
    (submit_icon) and cancel. An overridden helper or action provider makes the whole form dynamic, an overridden
    button hook that one control; icon attributes that are not None or a str (e.g. a property) are dynamic too.
    """
    from crud_views.lib.crispy.buttons import _KIND_ICONS
    from crud_views.lib.crispy.form import CrispyDeleteForm, CrispyFormMixin

    controls: list[tuple[str, Any]] = []
    if issubclass(form_class, CrispyDeleteForm):
        if not _inherits(form_class, "helper", CrispyDeleteForm):
            return []
        if _inherits(form_class, "get_delete_button", CrispyDeleteForm) and _inherits(
            form_class, "get_delete_button_kwargs", CrispyDeleteForm
        ):
            controls.append(("delete", _declared(form_class, "delete_icon")))
    else:
        if not (
            _inherits(form_class, "helper", CrispyFormMixin)
            and _inherits(form_class, "get_form_actions", CrispyFormMixin)
        ):
            return []
        if _inherits(form_class, "get_submit_button", CrispyFormMixin) and _inherits(
            form_class, "get_submit_button_kwargs", CrispyFormMixin
        ):
            controls.append(("submit", _declared(form_class, "submit_icon")))
    if _inherits(form_class, "get_cancel_button", CrispyFormMixin) and _inherits(
        form_class, "get_cancel_button_kwargs", CrispyFormMixin
    ):
        controls.append(("cancel", _KIND_ICONS["cancel"]))
    return [(kind, icon) for kind, icon in controls if icon is None or isinstance(icon, str)]


def _static_filter_controls(cls) -> list[tuple[type, str, str]]:
    """(helper class, form kind, icon) of a filter view's configured helper, when its default actions are known."""
    from crud_views.lib.crispy.buttons import _KIND_ICONS
    from crud_views.lib.views.list import ListViewFilterFormHelper
    from crud_views.lib.views.mixins import ListViewTableFilterMixin

    if not issubclass(cls, ListViewTableFilterMixin) or not _inherits(cls, "get_filterset", ListViewTableFilterMixin):
        return []
    helper = _declared(cls, "formhelper_class")
    if not (isinstance(helper, type) and issubclass(helper, ListViewFilterFormHelper)):
        return []
    if not _inherits(helper, "get_form_actions", ListViewFilterFormHelper):
        return []
    return [(helper, kind, _KIND_ICONS[kind]) for kind in ("filter-submit", "filter-reset")]


_FORM_ICON_HINTS = {"submit": "submit_icon or CRUD_VIEWS_ICONS", "delete": "delete_icon or CRUD_VIEWS_ICONS"}


def cv_form_icon_mode_checks(cls):
    """System check viewset.W292 for crispy form buttons (Phase 6, D-16): an icon-only control without a usable icon.

    Static reach only: the concrete form classes the view selects without a request (form_class, or each distinct
    class of a concrete dict polymorphic_forms) whose helper, action provider and button hooks are still the package
    implementations, and the configured filter helper when it inherits the default get_form_actions. Forms and
    helpers are never instantiated and no hook, get_form_class or renderer runs; everything else is covered at render
    time by cv_button_data (strict ValueError, else a logged label fallback). Availability is the shared
    icons._icon_available predicate. The mode is resolved through the public resolver; a resolution that raises
    (an invalid floor or map in strict mode) is skipped, so E108 / E210 / E211 / E106 still report it.
    """
    from crud_views.lib.icons import _icon_available

    mapping = cls.cv_get_form_actions_label_mode()
    if not isinstance(mapping, dict) or not is_label_mode_map(mapping):
        return  # viewset.E211 / E210 or crud_views.E106 report the selected map
    controls: list[tuple[type, str, Any]] = []
    for form_class in _static_form_classes(cls):
        controls.extend((form_class, kind, icon) for kind, icon in _static_form_controls(form_class))
    controls.extend(_static_filter_controls(cls))
    # each form class appears once (_static_form_classes deduplicates repeated polymorphic entries) and each kind
    # once per class, so every (class, kind) is reported at most once per traversal
    for owner, kind, icon in controls:
        try:
            mode = cls.cv_get_action_label_mode("form", kind)
        except ValueError:
            continue  # an invalid floor or map in strict mode: crud_views.E108 / viewset.E210 / E211 report it
        if mode != "icon" or _icon_available(icon):
            continue
        hint = _FORM_ICON_HINTS.get(kind, "CRUD_VIEWS_ICONS")
        yield CheckWarningExpression(
            context=cls,
            id="W292",
            expression=False,
            msg=(
                f"form button {kind!r} of {owner.__name__} renders icon-only but its icon {icon!r} is not available; "
                f"set a usable icon ({hint}) or the form label mode 'label' or 'both'"
            ),
        )
