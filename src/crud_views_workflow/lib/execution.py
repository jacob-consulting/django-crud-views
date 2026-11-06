"""Shared workflow validation and transactional execution."""

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import connections, transaction
from django.utils.translation import gettext_lazy as _

from .enums import WorkflowComment


class _WorkflowRefusal(ValidationError):
    """An expected refusal originating only from business or comment validation."""

    def __init__(self, *, field, error):
        self.field = field
        super().__init__(error)


def _check_transition_business(object, name, *, user):
    try:
        object.workflow_check_transition(name, user=user)
    except ValidationError as error:
        if hasattr(error, "error_dict"):
            raise TypeError(
                "workflow_check_transition must raise single/list ValidationError, not a dictionary"
            ) from error
        raise _WorkflowRefusal(field="transition", error=error) from error


def _check_transition_comment(policy, comment):
    if isinstance(comment, str):
        comment = comment.strip()
    comment = comment or None
    if policy == WorkflowComment.REQUIRED and comment is None:
        raise _WorkflowRefusal(field="comment", error=_("Comment is required for this transition"))
    return comment


def _run_transition(object, name, *, user, comment=None, using, on_transition=None):
    # Keep model imports lazy so the public helper can be imported during app setup.
    from django.contrib.contenttypes.models import ContentType

    from ..models import WorkflowInfo

    if not isinstance(using, str) or not using or using not in connections:
        raise ImproperlyConfigured("Workflow execution requires a configured database alias")
    for label, instance in (("object", object), ("user", user)):
        state = getattr(instance, "_state", None)
        if state is None or state.adding or instance.pk is None or state.db != using:
            raise ImproperlyConfigured(f"Workflow {label} must be saved on the selected database ({using})")

    with transaction.atomic(using=using):
        # Availability is authoritative even for callers bypassing forms. Never disclose
        # business blockers or look up an arbitrary attribute before this check.
        if not object.workflow_has_transition(user, name):
            raise SuspiciousOperation(f"Invalid transition {name}")
        _check_transition_business(object, name, user=user)
        policy = next(
            step.custom.get("comment", object.COMMENT_DEFAULT)
            for step in object.get_all_state_transitions()
            if step.name == name
        )
        comment = _check_transition_comment(policy, comment)
        state_old = object.state
        data = getattr(object, name)(by=user, comment=comment)
        object.save(using=using)
        info = WorkflowInfo.objects.using(using).create(
            transition=name,
            state_old=state_old,
            state_new=object.state,
            comment=comment,
            user=user,
            data=data,
            workflow_object_pk=str(object.pk),
            workflow_object_content_type=ContentType.objects.db_manager(using).get_for_model(object),
        )
        if on_transition is not None:
            on_transition(info)
        return info
