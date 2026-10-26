from collections.abc import Iterable
from typing import ClassVar

from django.views import generic

from crud_views.lib.check import Check
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.view.action_menu import ActionGroup, cv_inline_checks, cv_split_actions
from crud_views.lib.view.card import CardAction
from crud_views.lib.view.label_mode import default_label_mode, label_mode_check
from crud_views.lib.view.variant import variant_check
from crud_views.lib.view.visibility import cv_resolve_action
from crud_views.lib.views.mixins import CardOrderMixin


class CardListView(CardOrderMixin, CrudView, generic.ListView):
    template_name = "crud_views/view_card.html"
    cv_content_template = "crud_views/view_card.content.html"

    cv_pk: bool = False
    cv_key = "card"
    cv_path = "card"
    cv_object = False
    paginate_by = None  # set per-view to enable pagination
    cv_card_actions: ClassVar[list[CardAction]] = []
    cv_card_actions_inline: list[str] | None = None  # card action keys kept as buttons (#174)
    # view default for CardAction.label_mode: label, icon or both; None: CRUD_VIEWS_LABEL_MODE_DEFAULTS["card"]
    # (#213). Read the resolved mode through cv_get_card_actions_label_mode()
    cv_card_actions_label_mode: str | None = None
    cv_card_container_class: str = "col-md-6"
    cv_card_template: str = "crud_views/tags/card.html"
    cv_context_actions = crud_views_settings.list_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/card.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/card.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/card.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/card.html"
    cv_filter_header_template: str | None = "crud_views/snippets/header/filter.html"
    cv_filter_header_template_code: str | None = None

    # icons
    cv_icon_action = "card"

    def cv_get_card_action_data(self, action: CardAction, obj, user) -> dict:
        """Unresolved button data for one card action (#149, #174); the cv_card_action tag and the menu share it."""
        # resolved once for both branches: the action's own mode, then no_label, then the view resolver (#213)
        if action.label_mode is not None:
            label_mode = action.label_mode
        elif action.no_label:
            label_mode = "icon"
        else:
            label_mode = self.cv_get_card_actions_label_mode()
        if action.child_name:
            url = self.cv_get_child_url(action.child_name, action.child_key, obj)
            child_viewset = self.cv_viewset.get_viewset(action.child_name)
            child_cls = child_viewset.get_view_class(action.child_key)
            # permission is checked on the child view, like ChildContextButton (#149)
            return {
                "cv_access": bool(child_cls.cv_has_access(user, obj)),
                "cv_action_enabled": child_cls.cv_action_enabled(user, obj),
                "cv_inaccessible_actions": child_cls.cv_get_inaccessible_actions(),
                "cv_key": action.child_name,
                "cv_url": url,
                "cv_label": action.label,
                "cv_icon_action": child_cls.cv_icon_action,
                "cv_variant": action.variant if action.variant is not None else child_cls.cv_action_variant,
                "cv_flex": action.flex,
                "cv_label_mode": label_mode,
                "cv_list_action_method": "get",
            }

        cls = self.cv_viewset.get_view_class(action.key)
        url = self.cv_get_link_url(cls, action.key, obj)
        view_context = self.cv_get_view_context(object=obj)
        label = action.label or cls.cv_get_action_short_label(context=view_context)

        # always build the full data: disable mode renders label/icon/variant without access (#149)
        data = cls.cv_get_dict(
            context=view_context,
            cv_oid=self.cv_get_oid(action.key, obj=obj),
            cv_url=url,
            cv_access=bool(cls.cv_has_access(user, obj)),
            cv_action_enabled=cls.cv_action_enabled(user, obj),
        )
        variant = action.variant if action.variant is not None else cls.cv_action_variant
        data.update(cv_label=label, cv_variant=variant, cv_flex=action.flex, cv_label_mode=label_mode)
        return data

    def cv_get_card_action_group(self, obj) -> ActionGroup:
        """Card actions split into inline buttons and menu items, matched by CardAction.key or child_name.
        All inline when no inline keys are set (#174)."""
        items = []
        for action in self.cv_card_actions:
            ctx = cv_resolve_action(self.cv_get_card_action_data(action, obj, self.request.user))
            if ctx is not None:
                items.append((action.key or action.child_name, ctx))
        inline = self.cv_get_card_actions_inline()
        if inline is None:
            return ActionGroup(inline=[ctx for _, ctx in items], menu=[])
        return cv_split_actions(items, inline)

    @classmethod
    def cv_get_card_actions_inline(cls):
        """Card action keys (CardAction.key, or child_name) kept as buttons; None: no menu (#174)."""
        return cls.cv_first_inline_keys(cls.cv_card_actions_inline, "card_actions_inline")

    @classmethod
    def cv_get_card_actions_label_mode(cls) -> str:
        """Label mode of card actions without their own: cv_card_actions_label_mode when set, else the configured
        card floor, CRUD_VIEWS_LABEL_MODE_DEFAULTS["card"] over the package default "both"."""
        if cls.cv_card_actions_label_mode is not None:
            return cls.cv_card_actions_label_mode
        return default_label_mode("card")

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        keys = [action.key or action.child_name for action in cls.cv_card_actions]
        yield from cv_inline_checks(cls, "cv_card_actions_inline", keys)
        if cls.cv_card_actions_label_mode is not None:
            yield label_mode_check(cls, "cv_card_actions_label_mode", cls.cv_card_actions_label_mode)
        for action in cls.cv_card_actions:
            owner = f"card action {action.key or action.child_name!r}"
            if action.variant is not None:
                yield variant_check(cls, owner, action.variant)
            if action.label_mode is not None:
                yield label_mode_check(cls, owner, action.label_mode)

    @property
    def cv_filter_header(self) -> str:
        return self.render_snippet(
            self.cv_get_meta(),
            self.cv_filter_header_template,
            self.cv_filter_header_template_code,
        )


class CardListViewPermissionRequired(CrudViewPermissionRequiredMixin, CardListView):
    cv_permission = "view"
