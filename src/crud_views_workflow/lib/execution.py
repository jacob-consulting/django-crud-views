"""Shared workflow validation and transactional execution."""

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError
from django.db import connections, router, transaction
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
        # Business messages are literal text, even when their author used mark_safe.
        # Interpolate first: even a plain "%s" can inherit a SafeString parameter's
        # type. Copy the leaves without params so interpolation happens exactly once.
        # add_error unwraps ValidationError subclasses, so sanitize each leaf itself.
        messages = [ValidationError(str.__str__(next(iter(item))), code=item.code) for item in error.error_list]
        raise _WorkflowRefusal(field="transition", error=messages) from error


def _check_transition_comment(policy, comment):
    if isinstance(comment, str):
        comment = comment.strip()
    comment = comment or None
    if policy == WorkflowComment.REQUIRED and comment is None:
        raise _WorkflowRefusal(field="comment", error=_("Comment is required for this transition"))
    return comment


def run_transition(object, name, *, user, comment=None):
    """Execute an available transition and return its saved WorkflowInfo.

    The object and authenticated actor must already be saved on the selected
    write database. Direct decorated-method calls do not use these checks.
    """
    try:
        return _run_transition(
            object, name, user=user, comment=comment, using=router.db_for_write(type(object), instance=object)
        )
    except _WorkflowRefusal as refusal:
        # Only the view's own private engine call may trigger refusal redisplay.
        # A consumer invoking this public helper from a transition/callback must
        # propagate failure without being mistaken for the outer action's checks.
        raise ValidationError(refusal) from refusal


def _run_transition(object, name, *, user, comment=None, using, on_transition=None):
    # Keep model imports lazy so the public helper can be imported during app setup.
    from django.contrib.contenttypes.models import ContentType

    from ..models import WorkflowInfo

    if not isinstance(using, str) or not using or using not in connections:
        raise ImproperlyConfigured("Workflow execution requires a configured database alias")
    if not getattr(user, "is_authenticated", False):
        raise ImproperlyConfigured("Workflow user must be authenticated and saved on the selected database")
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
            for step in object.get_available_user_state_transitions(user)
            if step.name == name
        )
        comment = _check_transition_comment(policy, comment)
        state_old = object.state
        data = getattr(object, name)(by=user, comment=comment)
        object.save(using=using)
        content_type = ContentType.objects.db_manager(using).get_for_model(object)
        # Scalar FK values avoid consulting a history router while constructing
        # an unsaved WorkflowInfo; both identities already belong to this alias.
        info = WorkflowInfo.objects.using(using).create(
            transition=name,
            state_old=state_old,
            state_new=object.state,
            comment=comment,
            user_id=user.pk,
            data=data,
            workflow_object_pk=str(object.pk),
            workflow_object_content_type_id=content_type.pk,
        )
        if on_transition is not None:
            on_transition(info)
        return info
