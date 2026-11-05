"""Request-level coverage of the opt-in per-transition workflow permission recipe."""

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import resolve

from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import WorkflowRequest, WorkflowRequestState
from tests.test1.app.views import CampaignWorkflowView

pytestmark = pytest.mark.django_db


@pytest.fixture
def workflowrequest_new():
    return WorkflowRequest.objects.create(name="Test workflow request")


@pytest.fixture
def cv_workflowrequest():
    from tests.test1.app.views import cv_workflowrequest as viewset

    return viewset


@pytest.fixture
def user_workflowrequest_step(cv_workflowrequest):
    actor = User.objects.create_user(username="user_workflowrequest_step", password="password")
    user_viewset_permission(actor, cv_workflowrequest, "view")
    content_type = ContentType.objects.get_for_model(WorkflowRequest)
    assert content_type.app_label == "app"
    permission = Permission.objects.get(content_type=content_type, codename="process_workflowrequest")
    actor.user_permissions.add(permission)
    return actor


@pytest.fixture
def user_workflowrequest_change(cv_workflowrequest):
    actor = User.objects.create_user(username="user_workflowrequest_change", password="password")
    user_viewset_permission(actor, cv_workflowrequest, "view")
    user_viewset_permission(actor, cv_workflowrequest, "change")
    return actor


@pytest.fixture
def user_workflowrequest_view(cv_workflowrequest):
    actor = User.objects.create_user(username="user_workflowrequest_view", password="password")
    user_viewset_permission(actor, cv_workflowrequest, "view")
    return actor


@pytest.fixture
def user_workflowrequest_step_only():
    actor = User.objects.create_user(username="user_workflowrequest_step_only", password="password")
    permission = Permission.objects.get(
        content_type=ContentType.objects.get_for_model(WorkflowRequest), codename="process_workflowrequest"
    )
    actor.user_permissions.add(permission)
    return actor


def _persisted_snapshot(obj):
    obj.refresh_from_db()
    return obj.state, list(obj.get_workflow_info_queryset().values())


@pytest.mark.parametrize(
    ("actor_fixture", "transition", "label", "target"),
    [
        ("user_workflowrequest_step", "wf_process", "Process", WorkflowRequestState.PROCESSED),
        ("user_workflowrequest_change", "wf_cancel", "Cancel", WorkflowRequestState.CANCELED),
    ],
)
def test_permitted_step(
    client, workflowrequest_new, cv_workflowrequest, request, actor_fixture, transition, label, target
):
    actor = request.getfixturevalue(actor_fixture)
    obj = workflowrequest_new
    assert actor.is_superuser is False
    assert actor.has_perm("app.view_workflowrequest") is True
    assert actor.has_perm("app.process_workflowrequest") is (transition == "wf_process")
    assert actor.has_perm("app.change_workflowrequest") is (transition == "wf_cancel")
    assert {step.name for step in obj.get_available_state_transitions()} == {"wf_process", "wf_cancel"}
    history_before = list(obj.get_workflow_info_queryset().values())
    client.force_login(actor)
    url = f"/workflowrequest/{obj.pk}/workflow/"

    response = client.get(url)
    assert response.status_code == 200
    assert dict(response.context["form"].fields["transition"].choices) == {transition: label}
    response = client.post(url, {"transition": transition, "comment": ""})
    assert response.status_code == 302
    assert resolve(response["Location"]).func.view_class.cv_viewset is cv_workflowrequest
    assert client.get(response["Location"]).status_code == 200

    obj.refresh_from_db()
    assert obj.state == target
    history = list(obj.get_workflow_info_queryset())
    assert len(history) == len(history_before) + 1
    info = history[-1]
    assert info.transition == transition
    assert info.state_old == WorkflowRequestState.NEW
    assert info.state_new == target
    assert info.user == actor
    assert info.workflow_object_content_type == ContentType.objects.get_for_model(obj)
    assert info.workflow_object_pk == str(obj.pk)
    assert info.workflow_object == obj


def test_forbidden_step(client, workflowrequest_new, user_workflowrequest_step):
    obj = workflowrequest_new
    assert {step.name for step in obj.get_available_state_transitions()} == {"wf_process", "wf_cancel"}
    client.force_login(user_workflowrequest_step)
    url = f"/workflowrequest/{obj.pk}/workflow/"
    response = client.get(url)
    assert response.status_code == 200
    assert dict(response.context["form"].fields["transition"].choices) == {"wf_process": "Process"}

    before = _persisted_snapshot(obj)
    response = client.post(url, {"transition": "wf_cancel", "comment": ""})
    assert response.status_code == 200
    assert "transition" in response.context["form"].errors
    assert _persisted_snapshot(obj) == before


@pytest.mark.parametrize("method", ["get", "post"])
def test_page_permission(client, workflowrequest_new, user_workflowrequest_step_only, method):
    obj = workflowrequest_new
    actor = user_workflowrequest_step_only
    assert actor.has_perm("app.view_workflowrequest") is False
    assert obj.workflow_has_transition(actor, "wf_process") is True
    client.force_login(actor)

    before = _persisted_snapshot(obj)
    response = getattr(client, method)(
        f"/workflowrequest/{obj.pk}/workflow/", {"transition": "wf_process", "comment": ""}
    )
    assert response.status_code == 403
    assert _persisted_snapshot(obj) == before


def test_basic_empty(client, workflowrequest_new, user_workflowrequest_view):
    assert WorkflowViewPermissionRequired.cv_permission == "change"
    assert CampaignWorkflowView.cv_permission == "change"
    obj = workflowrequest_new
    client.force_login(user_workflowrequest_view)
    url = f"/workflowrequest/{obj.pk}/workflow/"
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["has_workflow_choices"] is False
    assert dict(response.context["form"].fields["transition"].choices) == {}
    assert b"There are no workflow steps available from the current state." in response.content

    before = _persisted_snapshot(obj)
    response = client.post(url, {"transition": "wf_process", "comment": ""})
    assert response.status_code == 200
    assert "transition" in response.context["form"].errors
    assert _persisted_snapshot(obj) == before
