from enum import IntEnum
from functools import cached_property
from typing import Dict, Any
from typing import List

from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from crud_views_workflow.models import WorkflowInfo


class WorkflowMixin:
    """
    Mixin for state workflow models

    Requires the following class attributes:

        class STATE:
            NEW = "new"
            CREATED = "created"

        STATE_CHOICES = (
            (STATE.NEW, _("New")),
            (STATE.CREATED, _("Created")),
        )

        STATE_BADGES = {
            # neutral
            STATE.NEW: "info",
            STATE.CREATED: "info",
        }

        STATE_BADGES_DEFAULT = "info"
    """

    STATE_BADGES_DEFAULT = "info"

    class Comment(IntEnum):
        NONE = 0
        OPTIONAL = 1
        REQUIRED = 2

    def state_increment(self):
        self.state_version += 1  # noqa

    def get_state_name(self, state) -> str:
        assert self.STATE_CHOICES, "STATE_CHOICES must be defined"  # noqa
        if not state:
            return ""
        return dict(self.STATE_CHOICES)[state]  # noqa

    @property
    def state_name(self) -> str:
        assert self.state, "FSM state column missing"  # noqa
        return self.get_state_name(self.state)  # noqa

    def get_state_badge(self, state) -> str:
        assert self.STATE_BADGES, "STATE_BADGES must be defined"  # noqa
        name = self.get_state_name(state)
        if state in self.STATE_BADGES:  # noqa
            klass = self.STATE_BADGES.get(state, self.STATE_BADGES_DEFAULT)  # noqa
            html = render_to_string("crud_views_workflow/workflow/badge.html", {
                "state": state,
                "name": name,
                "class": klass
            })
            return mark_safe(html)
        else:
            return name

    @property
    def state_badge(self) -> str:
        return self.get_state_badge(self.state)  # noqa

    @staticmethod
    def workflow_comment_kwargs(comment: str | None = None) -> Dict:
        return dict(comment=comment) if comment else dict()

    def get_workflow_info_queryset(self):
        return WorkflowInfo.objects.filter(
            workflow_object_id=self.id,  # noqa
            workflow_object_content_type=ContentType.objects.get_for_model(self)).order_by("timestamp")  # noqa

    @property
    def workflow_data(self) -> List[Dict]:
        items = []
        queryset = self.get_workflow_info_queryset()
        for info in queryset:
            items.append(dict(
                timestamp=info.timestamp,
                user=info.user,
                state_old=info.state_old,
                state_new=info.state_new,
                state_old_badge=self.get_state_badge(info.state_old),
                state_new_badge=self.get_state_badge(info.state_new),
                transition=info.transition,
                transition_label=self.workflow_get_transition_label(info.transition),
                comment=info.comment
            ))
        return items

    def workflow_get_possible_transitions(self, user) -> List[tuple[Any, Any, Any]]:
        actions = []
        for transition in self.get_available_user_state_transitions(user):  # noqa
            label = transition.custom.get('label', transition.name)
            comment = transition.custom.get('comment', WorkflowMixin.Comment.NONE)
            actions.append((transition.name, label, comment))
        return actions

    def workflow_has_any_possible_transition(self, user) -> bool:
        return len(self.workflow_get_possible_transitions(user)) > 0

    def workflow_has_transition(self, user, transition) -> bool:
        for v, x, y in self.workflow_get_possible_transitions(user):
            if v == transition:
                return True
        return False

    @cached_property
    def workflow_get_transition_label_map(self) -> Dict[str, str]:
        return {t.name: t.custom.get('label', t.name) for t in self.get_all_state_transitions()}

    def workflow_get_transition_label(self, name) -> str:
        return self.workflow_get_transition_label_map[name]

    def workflow_get_form_kwargs(self, user):
        kwargs, choices, initial, transition_comments = dict(), [], [], dict()
        for value, label, comment in self.workflow_get_possible_transitions(user):
            choices.append((value, label))
            transition_comments[value] = comment
        kwargs["choices"] = choices
        kwargs["transition_comments"] = transition_comments
        return kwargs
