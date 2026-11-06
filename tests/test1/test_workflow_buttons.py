"""Production crispy rendering and request contracts for workflow presentation."""

from collections import Counter
from importlib.metadata import version

import django
import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from lxml import html
from django.template import Context, Template
from django.utils.safestring import mark_safe

from crud_views_workflow.lib.enums import WorkflowComment

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


def _render(form):
    return Template("{% load crud_views %}{% cv_render_form %}").render(Context({"form": form, "view": form.cv_view}))


def _assert_descriptions(document, rendered_forms=()):
    """Only Django 4.2/crispy 2026.3's unreferenced vendor error wrapper is exempt."""
    expected_error_groups = [
        {f"error_{index + 1}_{form[name].auto_id}" for index in range(len(errors))}
        for form in rendered_forms
        for name, errors in form.errors.items()
        if name in form.fields
    ]
    vendor_runtime = django.VERSION[:2] == (4, 2) and version("crispy-bootstrap5") == "2026.3"
    exempt = []
    for node in document.xpath('//*[@id="_error"]'):
        descendants = {child.get("id") for child in node if child.get("id")}
        if (
            vendor_runtime
            and node.tag == "div"
            and node.get("class") == "invalid-feedback"
            and descendants
            and descendants in expected_error_groups
        ):
            exempt.append(node)
    if vendor_runtime and expected_error_groups:
        assert len(exempt) == len(expected_error_groups)
    ids = [node.get("id") for node in document.xpath("//*[@id]") if node not in exempt]
    assert all(count == 1 for count in Counter(ids).values()), "duplicate owned ID"
    for node in document.xpath("//*[@aria-describedby]"):
        for token in node.get("aria-describedby").split():
            assert token != "_error", "description targets vendor wrapper"
            assert len(document.xpath("//*[@id=$value]", value=token)) == 1, "missing or ambiguous description"
    return exempt


class CachedFieldsForm(CampaignWorkflowForm):
    extra = forms.CharField(help_text="Extra guidance")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.constructor_ids = {name: self[name].auto_id for name in self.fields}
        self.constructor_subwidgets = list(self["transition"].subwidgets)
        self.fields["transition"].widget.attrs["aria-describedby"] = "external-guidance"

    def get_layout_fields(self):
        return ["transition", "comment", "extra"]


class TestTransitionButtons:
    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize(
        "name,target", [("wf_activate", CampaignState.ACTIVE), ("wf_cancel_new", CampaignState.CANCELED)]
    )
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
            targets = document.xpath("//*[@id=$id]", id=label.get("for"))
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
        assert form.helper is not None
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


class TestWorkflowDescriptions:
    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize("required", [False, True])
    def test_comment_markers_and_guidance(
        self, client_user_campaign_change, campaign_new, monkeypatch, modal, required
    ):
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons")
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_help_text", "General guidance")
        monkeypatch.setattr(CampaignWorkflowView, "cv_comment_help_text", "Comment guidance")
        step = next(t for t in campaign_new.get_all_state_transitions() if t.name == "wf_cancel_new")
        monkeypatch.setitem(step.custom, "help_text", "Action guidance")
        if not required:
            monkeypatch.setitem(step.custom, "comment", WorkflowComment.OPTIONAL)
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/", headers=_headers(modal))
        document = _document(response)
        buttons = _buttons(document)
        marked = [b for b in buttons if b.cssselect('[aria-hidden="true"]')]
        assert len(marked) == int(required)
        assert sum("Comment required" in b.text_content() for b in buttons) == int(required)
        assert len(document.xpath('//*[normalize-space(text())="* Comment required"]')) == int(required)
        group = document.cssselect('[role="group"]')[0]
        assert group.getparent().cssselect("label .asteriskField")
        assert group.getprevious().text_content().strip() == "General guidance"
        assert "Action guidance" in buttons[1].getparent().text_content()
        _assert_descriptions(document)

    @pytest.mark.parametrize("modal", [False, True])
    @pytest.mark.parametrize("presentation", ["radio", "buttons"])
    @pytest.mark.parametrize("text", [None, "", "Plain & complete", mark_safe("<b>Literal & {{ value }}</b>")])
    def test_literal_and_absent_help(
        self, client_user_campaign_change, campaign_new, monkeypatch, modal, presentation, text
    ):
        raw = {
            key: (mark_safe(f"{key} {text}") if hasattr(text, "__html__") else f"{key} {text}") if text else text
            for key in ("General", "Comment", "Action")
        }
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", presentation)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_help_text", raw["General"])
        monkeypatch.setattr(CampaignWorkflowView, "cv_comment_help_text", raw["Comment"])
        step = next(t for t in campaign_new.get_all_state_transitions() if t.name == "wf_activate")
        monkeypatch.setitem(step.custom, "help_text", raw["Action"])
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/", headers=_headers(modal))
        form = response.context["form"]
        outputs = [response.content.decode(), _render(form)]
        form._workflow_refresh()
        outputs.append(_render(form))
        for output in outputs:
            document = html.fragment_fromstring(output, create_parent="main")
            assert not document.cssselect("b")
            content = document.text_content()
            for key in ("General", "Comment", "Action"):
                if text and (key != "Action" or presentation == "buttons"):
                    assert content.count(str(raw[key])) == 1
                elif not text:
                    assert "None" not in content
            if not text:
                # Required-comment legend is separate from optional help wrappers.
                assert not document.xpath('//*[contains(@id,"helptext") or contains(@id,"-help")]')
            if presentation == "buttons":
                _assert_descriptions(document)

    @pytest.mark.parametrize("presentation", ["radio", "buttons"])
    @pytest.mark.parametrize("modal", [False, True])
    def test_all_none_omits_visible_comment_wrapper(
        self, client_user_campaign_change, campaign_new, monkeypatch, presentation, modal
    ):
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", presentation)
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        for step in campaign_new.get_all_state_transitions():
            monkeypatch.setitem(step.custom, "comment", WorkflowComment.NONE)
        response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/", headers=_headers(modal))
        document = _document(response)
        assert document.cssselect('input[type="hidden"][name="comment"]')
        assert not document.cssselect('textarea[name="comment"]')
        assert not document.xpath('//label[contains(.,"Please provide a comment")]')
        assert len(document.cssselect("form.cv-form .row")) == 1

    def test_repeated_forms_unique_ids_and_error_paragraphs(
        self, client_user_campaign_change, campaign_new, user_campaign_change, monkeypatch
    ):
        from tests.test1.app.views import cv_campaign
        from tests.test1.test_theme_form_requests import _grant_cancel_view

        _grant_cancel_view(user_campaign_change, cv_campaign)
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons")
        monkeypatch.setattr(CampaignWorkflowView, "form_class", CachedFieldsForm)

        def check(obj, name, *, user):
            raise ValidationError(["First reason", "Second reason"])

        monkeypatch.setattr(Campaign, "workflow_check_transition", check)
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_cancel_new", "comment": "", "extra": ""}
        )
        view = response.context["view"]
        first = response.context["form"]
        second = view.get_form()
        view.prefix = "prefixed"
        third = view.get_form()
        rendered_forms = [first, second, third]
        outputs = [_render(form) for form in rendered_forms]
        document = html.fragment_fromstring(
            '<p id="external-guidance">External guidance</p>' + "".join(outputs), create_parent="main"
        )
        _assert_descriptions(document, rendered_forms)
        for form in rendered_forms:
            assert form.constructor_ids == {name: form[name].auto_id for name in form.fields}
            assert all(value.startswith("cv-wf-") for value in form.constructor_ids.values())
        assert len(document.cssselect("[data-cv-cancel-url]")) == 3
        assert len({node.get("id") for node in document.cssselect("[data-cv-cancel-url]")}) == 3
        for group in document.cssselect('[role="group"]'):
            assert "external-guidance" in group.get("aria-describedby", "").split()
            assert "is-invalid" in group.get("class", "").split()
            assert "invalid-feedback" in group.getnext().get("class", "")
            for button in group.cssselect("button"):
                assert "external-guidance" in button.get("aria-describedby", "").split()

    @pytest.mark.parametrize("kind", ["duplicate", "missing", "ambiguous"])
    def test_description_guard_negative_controls(self, kind):
        markup = {
            "duplicate": '<main><p id="owned"></p><p id="owned"></p></main>',
            "missing": '<main><button aria-describedby="missing"></button></main>',
            "ambiguous": '<main><p id="description"></p><p id="description"></p><button aria-describedby="description"></button></main>',
        }[kind]
        with pytest.raises(AssertionError):
            _assert_descriptions(html.fromstring(markup))

    @pytest.mark.parametrize("modal", [False, True])
    def test_zero_choices_preserve_existing_branch(
        self, client_user_campaign_change, campaign_success, monkeypatch, modal
    ):
        monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons")
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        response = client_user_campaign_change.get(
            f"/campaign/{campaign_success.pk}/workflow/", headers=_headers(modal)
        )
        document = _document(response)
        assert not _buttons(document)
        assert bool(document.cssselect("form.cv-form")) is modal
        if not modal:
            assert "There are no workflow steps available" in document.text_content()
