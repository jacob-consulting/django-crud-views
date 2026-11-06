"""Contracts shared by workflow forms, requests and standalone execution."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from crud_views_workflow.lib.enums import WorkflowComment
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Campaign, CampaignState
from tests.test1.app.views import CampaignWorkflowForm, CampaignWorkflowView

pytestmark = pytest.mark.django_db


class TestWorkflowTracer:
    def test_radio_business_refusal_then_success(self, client_user_campaign_change, campaign_new, monkeypatch):
        calls = []
        blocked = True

        def check(obj, name, *, user):
            calls.append((obj.pk, name, user.pk))
            if blocked:
                raise ValidationError([
                    ValidationError("Missing %(item)s", params={"item": "budget"}),
                    "Missing approval",
                ])

        monkeypatch.setattr(Campaign, "workflow_check_transition", check, raising=False)
        url = f"/campaign/{campaign_new.pk}/workflow/"
        response = client_user_campaign_change.get(url)
        assert response.status_code == 200
        assert calls == []
        assert response.context["form"].fields["transition"].widget.__class__.__name__ == "RadioSelect"

        response = client_user_campaign_change.post(url, {"transition": "wf_cancel_new", "comment": "  "})
        assert response.status_code == 200
        form = response.context["form"]
        assert list(form.errors["transition"]) == ["Missing budget", "Missing approval"]
        assert list(form.errors["comment"]) == ["Comment is required for this transition"]
        assert not form.non_field_errors()
        assert form.data["comment"] == "  "
        campaign_new.refresh_from_db()
        assert campaign_new.state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

        blocked = False
        response = client_user_campaign_change.post(url, {"transition": "wf_cancel_new", "comment": "  reason  "})
        assert response.status_code == 302
        campaign_new.refresh_from_db()
        assert campaign_new.state == CampaignState.CANCELED
        info = WorkflowInfo.objects.get()
        assert info.transition == "wf_cancel_new"
        assert info.state_old == CampaignState.NEW
        assert info.state_new == CampaignState.CANCELED
        assert info.comment == "reason"
        assert info.user_id == response.wsgi_request.user.pk
        assert info.data is None
        assert info.workflow_object_pk == str(campaign_new.pk)
        assert info.workflow_object_content_type == ContentType.objects.get_for_model(Campaign)

    def test_inheritable_clean(self, client_user_campaign_change, campaign_new, monkeypatch):
        class InheritedForm(CampaignWorkflowForm):
            def clean(self):
                cleaned = super().clean()
                assert isinstance(cleaned, dict)
                cleaned["subclass_value"] = "retained"
                return cleaned

        monkeypatch.setattr(CampaignWorkflowView, "form_class", InheritedForm)
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
        assert response.status_code == 302

    @pytest.mark.parametrize("name, comment, valid, field", [
        ("wf_cancel_new", "reason", True, None),
        ("wf_cancel_new", "  ", False, "comment"),
        ("forged", "reason", False, "transition"),
        ("", "reason", False, "transition"),
    ])
    def test_ownerless_form(self, name, comment, valid, field):
        form = WorkflowForm(
            data={"transition": name, "comment": comment}, cv_view=None,
            choices=[("wf_cancel_new", "Cancel")],
            transition_comments={"wf_cancel_new": WorkflowComment.REQUIRED},
        )
        assert form.is_valid() is valid
        if field:
            assert field in form.errors
        else:
            assert form.clean() == {"transition": name, "comment": comment}
