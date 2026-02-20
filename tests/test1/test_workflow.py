"""
Tests for crud_views_workflow: WorkflowMixin, WorkflowView, WorkflowForm.
"""

import pytest
from django.test.client import Client

from tests.test1.app.models import Campaign
from crud_views_workflow.models import WorkflowInfo


# ---------------------------------------------------------------------------
# WorkflowMixin model-layer tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_state_name_new(campaign_new):
    assert campaign_new.state_name == "New"


@pytest.mark.django_db
def test_state_name_active(campaign_active):
    assert campaign_active.state_name == "Active"


@pytest.mark.django_db
def test_state_name_success(campaign_success):
    assert campaign_success.state_name == "Success"


@pytest.mark.django_db
def test_get_state_name(campaign_new):
    assert campaign_new.get_state_name(Campaign.STATE.NEW) == "New"
    assert campaign_new.get_state_name(Campaign.STATE.ACTIVE) == "Active"
    assert campaign_new.get_state_name(Campaign.STATE.SUCCESS) == "Success"
    assert campaign_new.get_state_name(Campaign.STATE.CANCELED) == "Cancelled"


@pytest.mark.django_db
def test_state_badge_new(campaign_new):
    badge = campaign_new.state_badge
    assert "New" in badge
    assert "badge" in badge
    assert "light" in badge  # STATE_BADGES[NEW] = "light"


@pytest.mark.django_db
def test_get_state_badge_active(campaign_new):
    badge = campaign_new.get_state_badge(Campaign.STATE.ACTIVE)
    assert "Active" in badge
    assert "info" in badge  # STATE_BADGES[ACTIVE] = "info"


@pytest.mark.django_db
def test_get_state_badge_unknown_returns_name(campaign_new):
    # State not in STATE_BADGES falls back to plain name
    result = campaign_new.get_state_badge(Campaign.STATE.ERROR)
    assert "Error" in result


@pytest.mark.django_db
def test_workflow_possible_transitions_new(campaign_new, user_campaign_change):
    transitions = campaign_new.workflow_get_possible_transitions(user_campaign_change)
    names = [t[0] for t in transitions]
    assert "wf_activate" in names
    assert "wf_cancel_new" in names
    # wf_done is only available from ACTIVE
    assert "wf_done" not in names


@pytest.mark.django_db
def test_workflow_possible_transitions_active(campaign_active, user_campaign_change):
    transitions = campaign_active.workflow_get_possible_transitions(user_campaign_change)
    names = [t[0] for t in transitions]
    assert "wf_done" in names
    assert "wf_cancel_active" in names
    # wf_activate is only available from NEW
    assert "wf_activate" not in names


@pytest.mark.django_db
def test_workflow_possible_transitions_success_empty(campaign_success, user_campaign_change):
    transitions = campaign_success.workflow_get_possible_transitions(user_campaign_change)
    assert transitions == []


@pytest.mark.django_db
def test_workflow_has_transition_true(campaign_new, user_campaign_change):
    assert campaign_new.workflow_has_transition(user_campaign_change, "wf_activate") is True


@pytest.mark.django_db
def test_workflow_has_transition_false_wrong_state(campaign_new, user_campaign_change):
    # wf_done requires ACTIVE state
    assert campaign_new.workflow_has_transition(user_campaign_change, "wf_done") is False


@pytest.mark.django_db
def test_workflow_has_any_transition_true(campaign_new, user_campaign_change):
    assert campaign_new.workflow_has_any_possible_transition(user_campaign_change) is True


@pytest.mark.django_db
def test_workflow_has_any_transition_false_terminal(campaign_success, user_campaign_change):
    assert campaign_success.workflow_has_any_possible_transition(user_campaign_change) is False


@pytest.mark.django_db
def test_workflow_comment_kwargs_with_comment():
    result = Campaign.workflow_comment_kwargs("hello")
    assert result == {"comment": "hello"}


@pytest.mark.django_db
def test_workflow_comment_kwargs_without_comment():
    result = Campaign.workflow_comment_kwargs(None)
    assert result == {}


@pytest.mark.django_db
def test_workflow_comment_kwargs_empty_string():
    result = Campaign.workflow_comment_kwargs("")
    assert result == {}


@pytest.mark.django_db
def test_workflow_data_empty(campaign_new):
    assert campaign_new.workflow_data == []


@pytest.mark.django_db
def test_workflow_transition_label_map(campaign_new):
    label_map = campaign_new.workflow_get_transition_label_map
    assert "wf_activate" in label_map
    assert label_map["wf_activate"] == "Activate"
    assert "wf_done" in label_map
    assert label_map["wf_done"] == "Done"
    assert "wf_cancel_new" in label_map
    assert label_map["wf_cancel_new"] == "Cancel"


@pytest.mark.django_db
def test_workflow_get_transition_label(campaign_new):
    assert campaign_new.workflow_get_transition_label("wf_activate") == "Activate"
    assert campaign_new.workflow_get_transition_label("wf_done") == "Done"


@pytest.mark.django_db
def test_workflow_get_form_kwargs(campaign_new, user_campaign_change):
    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    assert "choices" in kwargs
    assert "transition_comments" in kwargs
    choice_names = [c[0] for c in kwargs["choices"]]
    assert "wf_activate" in choice_names
    assert "wf_cancel_new" in choice_names


@pytest.mark.django_db
def test_workflow_get_form_kwargs_labels(campaign_new, user_campaign_change):
    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    choices_dict = dict(kwargs["choices"])
    assert choices_dict["wf_activate"] == "Activate"
    assert choices_dict["wf_cancel_new"] == "Cancel"


@pytest.mark.django_db
def test_workflow_get_form_kwargs_comment_types(campaign_new, user_campaign_change):
    from crud_views_workflow.mixins import WorkflowMixin
    kwargs = campaign_new.workflow_get_form_kwargs(user_campaign_change)
    tc = kwargs["transition_comments"]
    assert tc["wf_activate"] == WorkflowMixin.Comment.NONE
    assert tc["wf_cancel_new"] == WorkflowMixin.Comment.REQUIRED


# ---------------------------------------------------------------------------
# WorkflowView HTTP tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_workflow_view_get(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_workflow_view_get_shows_transitions(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    assert response.context["has_workflow_choices"] is True


@pytest.mark.django_db
def test_workflow_view_get_terminal_state_no_choices(client_user_campaign_change: Client, campaign_success):
    response = client_user_campaign_change.get(f"/campaign/{campaign_success.pk}/workflow/")
    assert response.status_code == 200
    assert response.context["has_workflow_choices"] is False


@pytest.mark.django_db
def test_workflow_view_post_activate(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == Campaign.STATE.ACTIVE


@pytest.mark.django_db
def test_workflow_view_post_creates_workflow_info(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })
    assert WorkflowInfo.objects.filter(
        workflow_object_id=pk,
        transition="wf_activate",
        state_old=Campaign.STATE.NEW,
        state_new=Campaign.STATE.ACTIVE,
    ).exists()


@pytest.mark.django_db
def test_workflow_view_post_required_comment_missing(client_user_campaign_change: Client, campaign_new):
    """POST with required-comment transition but empty comment → form error, state unchanged."""
    pk = campaign_new.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_cancel_new",
        "comment": "",
    })
    assert response.status_code == 200  # form invalid, re-render
    campaign_new.refresh_from_db()
    assert campaign_new.state == Campaign.STATE.NEW  # state unchanged


@pytest.mark.django_db
def test_workflow_view_post_required_comment_provided(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_cancel_new",
        "comment": "Need to cancel this campaign",
    })
    assert response.status_code == 302
    campaign_new.refresh_from_db()
    assert campaign_new.state == Campaign.STATE.CANCELED
    info = WorkflowInfo.objects.get(workflow_object_id=pk, transition="wf_cancel_new")
    assert info.comment == "Need to cancel this campaign"


@pytest.mark.django_db
def test_workflow_view_post_optional_comment_without(client_user_campaign_change: Client, campaign_active):
    pk = campaign_active.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_done",
        "comment": "",
    })
    assert response.status_code == 302
    campaign_active.refresh_from_db()
    assert campaign_active.state == Campaign.STATE.SUCCESS


@pytest.mark.django_db
def test_workflow_view_post_optional_comment_with(client_user_campaign_change: Client, campaign_active):
    pk = campaign_active.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_done",
        "comment": "Campaign completed successfully",
    })
    assert response.status_code == 302
    campaign_active.refresh_from_db()
    assert campaign_active.state == Campaign.STATE.SUCCESS
    info = WorkflowInfo.objects.get(workflow_object_id=pk, transition="wf_done")
    assert info.comment == "Campaign completed successfully"


@pytest.mark.django_db
def test_workflow_view_post_unavailable_transition_form_error(client_user_campaign_change: Client, campaign_new):
    """Submitting a transition not available for the current state is rejected by form validation."""
    pk = campaign_new.pk
    response = client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_done",  # only available from ACTIVE, not NEW
        "comment": "",
    })
    # form validation rejects the choice; view re-renders the form
    assert response.status_code == 200
    campaign_new.refresh_from_db()
    assert campaign_new.state == Campaign.STATE.NEW  # state unchanged


@pytest.mark.django_db
def test_workflow_history_after_multiple_transitions(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk

    # Transition 1: Activate
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })

    # Transition 2: Done (with comment)
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_done",
        "comment": "All done",
    })

    campaign_new.refresh_from_db()
    assert campaign_new.state == Campaign.STATE.SUCCESS

    assert WorkflowInfo.objects.filter(workflow_object_id=pk).count() == 2

    history = campaign_new.workflow_data
    assert len(history) == 2
    assert history[0]["transition"] == "wf_activate"
    assert history[0]["state_old"] == Campaign.STATE.NEW
    assert history[0]["state_new"] == Campaign.STATE.ACTIVE
    assert history[1]["transition"] == "wf_done"
    assert history[1]["state_old"] == Campaign.STATE.ACTIVE
    assert history[1]["state_new"] == Campaign.STATE.SUCCESS
    assert history[1]["comment"] == "All done"


@pytest.mark.django_db
def test_workflow_history_transition_labels(client_user_campaign_change: Client, campaign_new):
    pk = campaign_new.pk
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })
    campaign_new.refresh_from_db()
    history = campaign_new.workflow_data
    assert history[0]["transition_label"] == "Activate"


@pytest.mark.django_db
def test_workflow_history_records_user(client_user_campaign_change: Client, campaign_new, user_campaign_change):
    pk = campaign_new.pk
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })
    info = WorkflowInfo.objects.get(workflow_object_id=pk, transition="wf_activate")
    assert info.user == user_campaign_change


@pytest.mark.django_db
def test_workflow_info_null_comment_when_empty(client_user_campaign_change: Client, campaign_new):
    """A blank comment is stored as NULL in WorkflowInfo."""
    pk = campaign_new.pk
    client_user_campaign_change.post(f"/campaign/{pk}/workflow/", {
        "transition": "wf_activate",
        "comment": "",
    })
    info = WorkflowInfo.objects.get(workflow_object_id=pk, transition="wf_activate")
    assert info.comment is None


@pytest.mark.django_db
def test_workflow_view_get_contains_campaign_name(client_user_campaign_change: Client, campaign_new):
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    assert campaign_new.name.encode() in response.content
