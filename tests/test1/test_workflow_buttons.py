"""Production crispy rendering and request contracts for workflow presentation."""

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from lxml import html

from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Campaign, CampaignState
from tests.test1.app.views import CampaignWorkflowForm, CampaignWorkflowView

pytestmark = pytest.mark.django_db


def _headers(modal):
    return {"X-CV-Modal": "true"} if modal else {}


def _document(response):
    return html.fromstring(response.content)


def _buttons(document):
    return document.cssselect('button[type="submit"][name="transition"]')


class TestTransitionButtons:
    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize("name,target", [("wf_activate", CampaignState.ACTIVE), ("wf_cancel_new", CampaignState.CANCELED)])
    def test_native_choice_request(self, client_user_campaign_change, campaign_new, monkeypatch, modal, name, target):
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons", raising=False)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_label", 'Choose <action> & "state"')
        url = f"/campaign/{campaign_new.pk}/workflow/"
        response = client_user_campaign_change.get(url, headers=_headers(modal))
        assert response.status_code == 200
        document = _document(response)
        buttons = _buttons(document)
        assert [button.get("value") for button in buttons] == ["wf_activate", "wf_cancel_new"]
        assert not document.cssselect('[name="transition"]:not(button), button[name="submit"]')
        (group,) = document.cssselect('[role="group"]')
        assert group.get("aria-label") == 'Choose <action> & "state"'
        assert not {"form-control", "form-select"} & set(group.get("class", "").split())
        label = group.getparent().cssselect("label")[0]
        assert label.get("for") is None
        for label in document.cssselect("label[for]"):
            targets = document.xpath('//*[@id=$id]', id=label.get("for"))
            assert len(targets) == 1
            assert targets[0].tag != "button"
        assert all("disabled" not in button.attrib for button in buttons)
        response = client_user_campaign_change.post(
            url, {"transition": name, "comment": "reason"}, headers=_headers(modal)
        )
        assert response.status_code == (204 if modal else 302)
        assert response.headers["X-CV-Redirect" if modal else "Location"]
        assert Campaign.objects.get(pk=campaign_new.pk).state == target
        assert WorkflowInfo.objects.get().transition == name

    @pytest.mark.parametrize("modal", [False, True])
    def test_business_preview_is_offered_only_and_cached(
        self, client_user_campaign_change, campaign_new, monkeypatch, modal
    ):
        calls = []

        def check(obj, name, *, user):
            calls.append(name)
            if name == "wf_activate":
                raise ValidationError(["First blocker", "Second blocker"])

        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons", raising=False)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/", headers=_headers(modal))
        document = _document(response)
        first, second = _buttons(document)
        assert "disabled" in first.attrib and "disabled" not in second.attrib
        assert first.getparent().xpath(".//li/text()") == ["First blocker", "Second blocker"]
        assert calls == ["wf_activate", "wf_cancel_new"]
        form = response.context["form"]
        str(form["transition"])
        str(form["transition"])
        form.helper
        assert calls == ["wf_activate", "wf_cancel_new"]

    @pytest.mark.parametrize("gate", ["permission", "condition"])
    def test_unavailable_choice_has_no_preview(self, client_user_campaign_change, campaign_new, monkeypatch, gate):
        calls = []
        step = next(t for t in campaign_new.get_all_state_transitions() if t.name == "wf_activate")
        if gate == "permission":
            monkeypatch.setattr(step, "permission", lambda obj, user: False)
        else:
            monkeypatch.setattr(step, "conditions", [lambda obj: False])
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons", raising=False)
        monkeypatch.setattr(Campaign, "workflow_check_transition", lambda obj, name, user: calls.append(name))
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
        assert [b.get("value") for b in _buttons(_document(response))] == ["wf_cancel_new"]
        assert calls == ["wf_cancel_new"]

    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize("name", [None, "forged", "save", "wf_done", "wf_activate"])
    def test_invalid_or_blocked_post(self, client_user_campaign_change, campaign_new, monkeypatch, modal, name):
        def check(obj, name, *, user):
            raise ValidationError("Business refusal")

        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons", raising=False)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        payload = {"comment": "  retained  "}
        if name is not None:
            payload["transition"] = name
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", payload, headers=_headers(modal)
        )
        assert response.status_code == (422 if modal else 200)
        assert "transition" in response.context["form"].errors
        (group,) = _document(response).cssselect('[role="group"]')
        assert "is-invalid" in group.get("class", "").split()
        assert "form-control" not in group.get("class", "").split()
        assert Campaign.objects.get(pk=campaign_new.pk).state == CampaignState.NEW
        assert not WorkflowInfo.objects.exists()

    @pytest.mark.parametrize("presentation", ["radio", "buttons"])
    def test_custom_submit_slot(self, client_user_campaign_change, campaign_new, monkeypatch, presentation):
        called = []

        class CustomSubmit(CampaignWorkflowForm):
            submit_label = "Custom workflow submit"

            def get_submit_button(self):
                called.append(True)
                return super().get_submit_button()

        monkeypatch.setattr(CampaignWorkflowView, "form_class", CustomSubmit)
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", presentation, raising=False)
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
        document = _document(response)
        if presentation == "radio":
            assert called
            assert document.cssselect('input[type="radio"][name="transition"]')
            assert document.cssselect('button[name="submit"]')[0].text_content().strip() == "Custom workflow submit"
        else:
            assert called == []
            assert len(_buttons(document)) == 2

    def test_invalid_presentation_fails_clearly(self, client_user_campaign_change, campaign_new, monkeypatch):
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "typo", raising=False)
        with pytest.raises(ImproperlyConfigured, match="cv_transition_presentation"):
            client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
