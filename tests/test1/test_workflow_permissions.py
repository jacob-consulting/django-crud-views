"""Request-level coverage of the opt-in per-transition workflow permission recipe."""

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import resolve

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import WorkflowRequest, WorkflowRequestState

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


def test_permitted_step(client, workflowrequest_new, user_workflowrequest_step, cv_workflowrequest):
    actor = user_workflowrequest_step
    obj = workflowrequest_new
    assert actor.is_superuser is False
    assert actor.has_perm("app.view_workflowrequest") is True
    assert actor.has_perm("app.process_workflowrequest") is True
    assert actor.has_perm("app.change_workflowrequest") is False
    assert {step.name for step in obj.get_available_state_transitions()} == {"wf_process", "wf_cancel"}
    history_before = list(obj.get_workflow_info_queryset().values())
    client.force_login(actor)
    url = f"/workflowrequest/{obj.pk}/workflow/"

    response = client.get(url)
    assert response.status_code == 200
    assert dict(response.context["form"].fields["transition"].choices) == {"wf_process": "Process"}
    response = client.post(url, {"transition": "wf_process", "comment": ""})
    assert response.status_code == 302
    assert resolve(response["Location"]).func.view_class.cv_viewset is cv_workflowrequest
    assert client.get(response["Location"]).status_code == 200

    obj.refresh_from_db()
    assert obj.state == WorkflowRequestState.PROCESSED
    history = list(obj.get_workflow_info_queryset())
    assert len(history) == len(history_before) + 1
    info = history[-1]
    assert info.transition == "wf_process"
    assert info.state_old == WorkflowRequestState.NEW
    assert info.state_new == WorkflowRequestState.PROCESSED
    assert info.user == actor
    assert info.workflow_object_content_type == ContentType.objects.get_for_model(obj)
    assert info.workflow_object_pk == str(obj.pk)
    assert info.workflow_object == obj
