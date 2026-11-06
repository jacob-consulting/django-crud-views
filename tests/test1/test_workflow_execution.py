"""Contracts shared by workflow forms, requests and standalone execution."""

import inspect
from functools import wraps

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation, ValidationError

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
                raise ValidationError(
                    [
                        ValidationError("Missing %(item)s", params={"item": "budget"}),
                        "Missing approval",
                    ]
                )

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

    @pytest.mark.parametrize(
        "name, comment, valid, field",
        [
            ("wf_cancel_new", "reason", True, None),
            ("wf_cancel_new", "  ", False, "comment"),
            ("forged", "reason", False, "transition"),
            ("", "reason", False, "transition"),
        ],
    )
    def test_ownerless_form(self, name, comment, valid, field):
        form = WorkflowForm(
            data={"transition": name, "comment": comment},
            cv_view=None,
            choices=[("wf_cancel_new", "Cancel")],
            transition_comments={"wf_cancel_new": WorkflowComment.REQUIRED},
        )
        assert form.is_valid() is valid
        if field:
            assert field in form.errors
        else:
            assert form.clean() == {"transition": name, "comment": comment}


class TestWorkflowHelper:
    def test_exact_public_signature(self, campaign_new, user_campaign_change):
        import crud_views_workflow.lib as workflow

        helper = getattr(workflow, "run_transition", None)
        assert callable(helper), "run_transition must be exported from crud_views_workflow.lib"
        assert "run_transition" in workflow.__all__
        assert str(inspect.signature(helper)) == "(object, name, *, user, comment=None)"
        with pytest.raises(TypeError):
            helper(campaign_new, "wf_activate")
        with pytest.raises(TypeError):
            helper(campaign_new, "wf_activate", user_campaign_change)

    def test_complete_history_and_view_parity(
        self, campaign_new, user_campaign_change, client_user_campaign_change, monkeypatch
    ):
        from crud_views_workflow.lib import run_transition

        original = Campaign.wf_activate

        @wraps(original)
        def transition(obj, *, by, comment):
            original(obj, by=by, comment=comment)
            return {"actor": by.pk, "comment": comment}

        monkeypatch.setattr(Campaign, "wf_activate", transition)
        info = run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment="  note  ")
        assert isinstance(info, WorkflowInfo)
        assert info.pk is not None
        assert info.user == user_campaign_change
        assert info.state_old == CampaignState.NEW
        assert info.state_new == CampaignState.ACTIVE
        assert info.comment == "note"
        assert info.data == {"actor": user_campaign_change.pk, "comment": "note"}
        assert info.workflow_object_pk == str(campaign_new.pk)
        assert info.workflow_object_content_type == ContentType.objects.get_for_model(Campaign)
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.ACTIVE
        other = Campaign.objects.create(name="View parity")
        response = client_user_campaign_change.post(
            f"/campaign/{other.pk}/workflow/", {"transition": "wf_activate", "comment": "  note  "}
        )
        assert response.status_code == 302
        view_info = WorkflowInfo.objects.get(workflow_object_pk=str(other.pk))
        for attr in ("transition", "user_id", "state_old", "state_new", "comment", "data",
                     "workflow_object_content_type_id"):
            assert getattr(info, attr) == getattr(view_info, attr)

    @pytest.mark.parametrize("name", [None, "", "unknown", "save", "__class__", "wf_done"])
    def test_unavailable_names_never_expose_blockers(self, campaign_new, user_campaign_change, monkeypatch, name):
        from crud_views_workflow.lib import run_transition

        def forbidden_check(*args, **kwargs):
            pytest.fail("Unavailable transition disclosed business validation")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden_check)
        with pytest.raises(SuspiciousOperation):
            run_transition(campaign_new, name, user=user_campaign_change)
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("gate", ["permission", "condition"])
    def test_fsm_gates_precede_business(self, campaign_new, user_campaign_change, monkeypatch, gate):
        from crud_views_workflow.lib import run_transition

        step = next(step for step in campaign_new.get_all_state_transitions() if step.name == "wf_activate")
        if gate == "permission":
            monkeypatch.setattr(step, "permission", lambda obj, user: False)
        else:
            monkeypatch.setattr(step, "conditions", [lambda obj: False])

        def forbidden_check(*args, **kwargs):
            pytest.fail("Unavailable transition disclosed business validation")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden_check)
        with pytest.raises(SuspiciousOperation):
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert not WorkflowInfo.objects.exists()

    def test_anonymous_actor_precondition(self, campaign_new, monkeypatch):
        from crud_views_workflow.lib import run_transition

        def forbidden(*args, **kwargs):
            pytest.fail("Unsupported actor reached business or dispatch")

        monkeypatch.setattr(Campaign, "workflow_check_transition", forbidden)
        monkeypatch.setattr(Campaign, "wf_activate", forbidden)
        with pytest.raises(ImproperlyConfigured, match="authenticated.*saved|saved.*authenticated"):
            run_transition(campaign_new, "wf_activate", user=AnonymousUser())
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("comment", [None, "", " \t ", "  reason  "])
    @pytest.mark.parametrize("policy", list(WorkflowComment))
    @pytest.mark.parametrize("use_default", [False, True])
    def test_comment_policies(self, campaign_new, user_campaign_change, monkeypatch, policy, comment, use_default):
        from crud_views_workflow.lib import run_transition

        step = next(step for step in campaign_new.get_all_state_transitions() if step.name == "wf_activate")
        if use_default:
            monkeypatch.delitem(step.custom, "comment")
            monkeypatch.setattr(Campaign, "COMMENT_DEFAULT", policy)
        else:
            monkeypatch.setitem(step.custom, "comment", policy)
        expected = comment.strip() or None if isinstance(comment, str) else None
        if policy == WorkflowComment.REQUIRED and expected is None:
            with pytest.raises(ValidationError, match="Comment is required"):
                run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment=comment)
            assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
            assert not WorkflowInfo.objects.exists()
        else:
            info = run_transition(campaign_new, "wf_activate", user=user_campaign_change, comment=comment)
            assert info.comment == expected

    @pytest.mark.parametrize("messages", ["One blocker", ["First blocker", "Second blocker"]])
    def test_business_error_order(self, campaign_new, user_campaign_change, monkeypatch, messages):
        from crud_views_workflow.lib import run_transition

        def check(obj, name, *, user):
            raise ValidationError(messages)

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        with pytest.raises(ValidationError) as caught:
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert caught.value.messages == ([messages] if isinstance(messages, str) else messages)
        assert not WorkflowInfo.objects.exists()

    def test_dictionary_errors_propagate_clearly(self, campaign_new, user_campaign_change, monkeypatch):
        from crud_views_workflow.lib import run_transition

        def check(obj, name, *, user):
            raise ValidationError({"name": "Unsupported field error"})

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        with pytest.raises(TypeError, match="single/list ValidationError, not a dictionary"):
            run_transition(campaign_new, "wf_activate", user=user_campaign_change)
        assert not WorkflowInfo.objects.exists()
