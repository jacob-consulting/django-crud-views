"""Integration regressions for workflow execution review findings."""

from functools import wraps

import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import RequestFactory
from django.urls import resolve
from django.utils.safestring import mark_safe
from django_fsm import transition
from guardian.shortcuts import assign_perm, remove_perm
from lxml import html

from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin
from crud_views_workflow.lib import run_transition
from crud_views_workflow.lib.enums import WorkflowComment
from crud_views_workflow.lib.execution import _WorkflowRefusal
from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Campaign, CampaignState
from tests.test1.app.views import CampaignWorkflowView

pytestmark = pytest.mark.django_db


@pytest.fixture
def stacked_action(monkeypatch):
    def configure(source, policy):
        meta = Campaign.wf_activate._django_fsm
        monkeypatch.setattr(meta, "transitions", dict(meta.transitions))
        monkeypatch.setattr(
            meta.transitions[CampaignState.NEW],
            "custom",
            {
                "label": "NEW label",
                "help_text": "NEW guidance",
                "comment": WorkflowComment.REQUIRED if policy == WorkflowComment.OPTIONAL else WorkflowComment.NONE,
            },
        )
        transition(
            field=Campaign._meta.get_field("state"),
            source=source,
            target=CampaignState.SUCCESS,
            custom={"label": "ACTIVE label", "help_text": "ACTIVE guidance", "comment": policy},
        )(Campaign.wf_activate)
        if source == CampaignState.ACTIVE:
            # An exact source must win over a wildcard even if it was added later.
            transition(
                field=Campaign._meta.get_field("state"),
                source="*",
                target=CampaignState.CANCELED,
                custom={"label": "Fallback", "help_text": "Fallback guidance", "comment": WorkflowComment.NONE},
            )(Campaign.wf_activate)

    return configure


@pytest.mark.parametrize("source", [CampaignState.ACTIVE, "*", "+"])
@pytest.mark.parametrize("policy", [WorkflowComment.REQUIRED, WorkflowComment.OPTIONAL])
def test_stacked_action_helper_uses_current_policy(campaign_new, user_campaign_change, stacked_action, source, policy):
    stacked_action(source, policy)
    campaign_new.state = CampaignState.ACTIVE
    campaign_new.save()
    if policy == WorkflowComment.REQUIRED:
        with pytest.raises(ValidationError, match="Comment is required"):
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.ACTIVE
        assert not WorkflowInfo.objects.exists()
    else:
        info = run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert (info.state_old, info.state_new, info.comment) == (CampaignState.ACTIVE, CampaignState.SUCCESS, None)


@pytest.mark.parametrize("source", [CampaignState.ACTIVE, "*", "+"])
@pytest.mark.parametrize("policy", [WorkflowComment.REQUIRED, WorkflowComment.OPTIONAL])
@pytest.mark.parametrize("presentation", ["radio", "buttons"])
def test_stacked_action_post_uses_current_policy(
    client_user_campaign_change, campaign_new, monkeypatch, stacked_action, source, policy, presentation
):
    stacked_action(source, policy)
    campaign_new.state = CampaignState.ACTIVE
    campaign_new.save()
    monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", presentation)
    response = client_user_campaign_change.post(
        f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
    )
    if policy == WorkflowComment.REQUIRED:
        assert response.status_code == 200
        assert list(response.context["form"].errors["comment"]) == ["Comment is required for this transition"]
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.ACTIVE
        assert not WorkflowInfo.objects.exists()
    else:
        assert response.status_code == 302
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.SUCCESS
        assert WorkflowInfo.objects.get().comment is None


@pytest.mark.parametrize("source", [CampaignState.ACTIVE, "*", "+"])
@pytest.mark.parametrize("state", [CampaignState.NEW, CampaignState.ACTIVE])
def test_stacked_action_help_matches_current_label(
    client_user_campaign_change, campaign_new, monkeypatch, stacked_action, source, state
):
    stacked_action(source, WorkflowComment.REQUIRED)
    campaign_new.state = state
    campaign_new.save()
    monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons")
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    document = html.fromstring(response.content)
    button = document.cssselect('button[value="wf_activate"]')[0]
    label = "NEW" if state == CampaignState.NEW else "ACTIVE"
    assert f"{label} label" in button.text_content()
    descriptions = " ".join(
        document.get_element_by_id(ref).text_content() for ref in button.get("aria-describedby").split()
    )
    assert f"{label} guidance" in descriptions
    assert "Fallback guidance" not in descriptions


@pytest.mark.parametrize("kind", ["business", "comment"])
def test_public_helper_keeps_refusal_marker_private(campaign_new, user_campaign_change, monkeypatch, kind):
    original = ValidationError(
        [
            ValidationError(mark_safe("%(reason)s"), code="blocked", params={"reason": mark_safe("<b>First</b>")}),
            "Second",
        ]
    )

    def check(obj, name, *, user):
        if kind == "business":
            raise original

    monkeypatch.setattr(Campaign, "workflow_check_transition", check)
    with pytest.raises(ValidationError) as caught:
        run_transition(campaign_new, "wf_cancel_new", user=user_campaign_change)
    assert type(caught.value) is ValidationError
    assert isinstance(caught.value.__cause__, _WorkflowRefusal)
    if kind == "business":
        assert caught.value.messages == ["<b>First</b>", "Second"]
        assert all(type(message) is str for message in caught.value.messages)
        assert [error.code for error in caught.value.error_list] == ["blocked", None]
        assert caught.value.__cause__.__cause__ is original
    else:
        assert caught.value.messages == ["Comment is required for this transition"]
    assert not WorkflowInfo.objects.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("stage", ["transition", "on_transition", "cv_on_commit"])
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_nested_public_helper_failure_propagates(
    client_user_campaign_change, campaign_new, user_campaign_change, monkeypatch, stage, atomic, modal
):
    dependent = Campaign.objects.create(name="Dependent")
    original = ValidationError("Dependent blocked")
    invalid = []

    def check(obj, name, *, user):
        if obj.pk == dependent.pk:
            raise original

    def dependent_action(*args, **kwargs):
        run_transition(dependent, "wf_activate", user=user_campaign_change)

    real_transition = Campaign.wf_activate

    @wraps(real_transition)
    def execute(obj, *args, **kwargs):
        result = real_transition(obj, *args, **kwargs)
        if obj.pk == campaign_new.pk:
            dependent_action()
        return result

    if stage == "transition":
        monkeypatch.setattr(Campaign, "wf_activate", execute)
    else:
        monkeypatch.setattr(CampaignWorkflowView, stage, dependent_action)
    monkeypatch.setattr(Campaign, "workflow_check_transition", check)
    monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", atomic)
    monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
    monkeypatch.setattr(CampaignWorkflowView, "cv_form_invalid_hook", lambda view, context: invalid.append(context))
    with pytest.raises(ValidationError) as caught:
        client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/",
            {"transition": "wf_activate", "comment": ""},
            headers={"X-CV-Modal": "true"} if modal else {},
        )
    assert type(caught.value) is ValidationError
    assert caught.value.messages == ["Dependent blocked"]
    assert caught.value.__cause__.__cause__ is original
    assert invalid == []
    committed = stage == "cv_on_commit"
    assert Campaign.objects.get(pk=campaign_new.pk).state == (CampaignState.ACTIVE if committed else CampaignState.NEW)
    assert Campaign.objects.get(pk=dependent.pk).state == CampaignState.NEW
    assert WorkflowInfo.objects.count() == int(committed)
    if committed:
        assert WorkflowInfo.objects.get().workflow_object_pk == str(campaign_new.pk)


@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("outcome", ["allow", "initial-denial", "permission", "action", "scope"])
def test_guardian_workflow_late_refusal_retains_scoped_authorization(
    campaign_new, user_campaign_change, monkeypatch, modal, outcome
):
    executing = False
    loads, checked = [], []
    if outcome != "initial-denial":
        assign_perm("app.change_campaign", user_campaign_change, campaign_new)

    class ScopedWorkflow(CampaignWorkflowView):
        def get_queryset(self):
            queryset = super().get_queryset().filter(name=campaign_new.name)
            return queryset.none() if executing and outcome == "scope" else queryset

        def get_object(self, queryset=None):
            loads.append(queryset)
            return super().get_object(queryset=queryset)

    class GuardianWorkflow(GuardianObjectPermissionMixin, ScopedWorkflow):
        def _check_object_perm(self, user, perm, obj):
            checked.append(obj)
            return super()._check_object_perm(user, perm, obj)

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            return not (executing and outcome == "action")

        def cv_form_valid_process(self, context):
            nonlocal executing
            executing = True
            if outcome == "permission":
                remove_perm("app.change_campaign", user_campaign_change, campaign_new)
            return super().cv_form_valid_process(context)

    def check(obj, name, *, user):
        if executing:
            raise ValidationError("Late business blocker")

    monkeypatch.setattr(Campaign, "workflow_check_transition", check)
    monkeypatch.setattr(GuardianWorkflow, "cv_modal", modal)
    url = f"/campaign/{campaign_new.pk}/workflow/"
    request = RequestFactory().post(
        url, {"transition": "wf_activate", "comment": "  kept  "}, headers={"X-CV-Modal": "true"} if modal else {}
    )
    request.user = user_campaign_change
    request.session = {}
    request._messages = FallbackStorage(request)
    request.resolver_match = resolve(url)
    if outcome == "allow":
        response = GuardianWorkflow.as_view()(request, **request.resolver_match.kwargs)
        assert response.status_code == (422 if modal else 200)
        form = response.context_data["form"]
        assert list(form.errors["transition"]) == ["Late business blocker"]
        assert form.data["comment"] == "  kept  "
        assert response.context_data["object"] is checked[-1]
    else:
        with pytest.raises(Http404 if outcome == "scope" else PermissionDenied):
            GuardianWorkflow.as_view()(request, **request.resolver_match.kwargs)
    assert loads[0] is None
    if outcome == "initial-denial":
        assert not executing and len(loads) == 1 and len(checked) == 1
    else:
        assert len(loads) == 2
        assert loads[1].db == "default"
        if outcome != "scope":
            assert campaign_new.name in loads[1].query.sql_with_params()[1]
            assert len(checked) == 2 and checked[0] is not checked[1]
            assert all(obj._state.db == "default" for obj in checked)
    assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
    assert not WorkflowInfo.objects.exists()
