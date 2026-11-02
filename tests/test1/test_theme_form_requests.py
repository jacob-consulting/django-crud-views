"""Real page/modal owners, template provenance and enforced-CSRF write contracts."""

from pathlib import Path

import pytest
from django.test import Client
from lxml import html

from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Author, Campaign, CampaignState
from tests.test1.app.views import AuthorCreateView, AuthorUpdateView, CampaignWorkflowView
from tests.test1.test_theme_form_ownership import _RawForms, assert_owned_form_markup

pytestmark = pytest.mark.django_db
MODES = [(kind, False) for kind in ("create", "update", "custom", "delete", "workflow")] + [
    (kind, True) for kind in ("custom", "delete", "workflow")
]
ROOT = Path(__file__).resolve().parents[2] / "src"


def _snapshot():
    return (
        list(Author.objects.order_by("pk").values()),
        list(Campaign.objects.order_by("pk").values()),
        list(WorkflowInfo.objects.order_by("pk").values()),
    )


def _workflow_templates(response, modal, choices, record_property):
    actual = {template.name: template.origin.name for template in response.templates if template.name}
    expected = (
        ["crud_views/view_custom_form.content.html"]
        if modal
        else ["crud_views_workflow/view_workflow.content.html", "crud_views_workflow/view_workflow.action.html"]
    )
    for name in expected:
        assert Path(actual[name]).resolve() == ROOT / name.split("/")[0] / "templates" / name
    if modal:
        assert "crud_views/modal/content.html" in actual
        assert "crud_views_workflow/view_workflow.content.html" not in actual
        assert "crud_views_workflow/view_workflow.action.html" not in actual
        assert "crud_views_workflow/view_workflow.history.html" not in actual
    else:
        assert "crud_views_workflow/view_workflow.history.html" in actual
    assert response.context["has_workflow_choices"] is choices
    record_property("workflow_branch", {"modal": modal, "choices": choices, "templates": actual})


def _owned(response, url, kind, modal):
    # Sibling action/language forms must not contaminate the target's token count.
    sibling = '<form method="post"><input name="csrfmiddlewaretoken" value="auxiliary"></form>'
    markup = response.content.decode()
    owner = assert_owned_form_markup(sibling + markup + sibling)
    assert owner["attrs"]["method"] == "post"
    assert "novalidate" in owner["attrs"]
    if kind == "workflow" and not modal:
        assert "action" not in owner["attrs"]
        assert "enctype" not in owner["attrs"]
    else:
        assert owner["attrs"]["action"] == url
        if kind != "delete":
            assert owner["attrs"]["enctype"] == "multipart/form-data"
    document = html.fromstring(markup)
    form = document.cssselect("form.cv-form")[0]
    for control in document.cssselect("input, select, textarea, button[type=submit]"):
        assert next(control.iterancestors("form"), None) is form
    cancel = form.cssselect("a[href]")[0]
    assert cancel.get("type") not in ("submit", "reset")
    assert not form.cssselect("button[type=reset], input[type=reset]")
    return owner, form


@pytest.mark.parametrize(("kind", "modal"), MODES)
def test_owned_form_request_matrix(kind, modal, request, monkeypatch, record_property):
    author = request.getfixturevalue("author_douglas_adams")
    if kind == "workflow":
        obj = request.getfixturevalue("campaign_new")
        user = request.getfixturevalue("user_campaign_change")
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        url = f"/campaign/{obj.pk}/workflow/"
        data = {"transition": "wf_activate", "comment": ""}
    else:
        permission = {"create": "add", "update": "change"}.get(kind)
        user = request.getfixturevalue(f"user_author_{permission}" if permission else "user_author_modal")
        prefix = "author" if permission else "author_modal"
        operation = "contact" if kind == "custom" else kind
        url = f"/{prefix}/create/" if kind == "create" else f"/{prefix}/{author.pk}/{operation}/"
        data = (
            {"first_name": "Owned", "last_name": "Request", "pseudonym": "Preserved"}
            if kind in ("create", "update")
            else {"subject": "Ownership", "body": "Native submission"}
            if kind == "custom"
            else {"confirm": "on"}
        )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    headers = {"X-CV-Modal": "true"} if modal else {}
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    if kind == "workflow":
        _workflow_templates(response, modal, True, record_property)
    owner, form = _owned(response, url, kind, modal)
    for name in data:
        assert form.xpath(".//*[@name=$name]", name=name)
    submitter = owner["submitters"][0]
    data[submitter["name"]] = submitter["value"]
    before = _snapshot()
    for token in (None, "invalid"):
        payload = dict(data)
        if token is not None:
            payload["csrfmiddlewaretoken"] = token
        assert client.post(url, payload, headers=headers).status_code == 403
        assert _snapshot() == before
    token = owner["tokens"][0]
    invalid = client.post(url, {"csrfmiddlewaretoken": token}, headers=headers)
    assert invalid.status_code == (422 if modal else 200)
    assert invalid.context["form"].errors
    _owned(invalid, url, kind, modal)
    if kind == "workflow":
        _workflow_templates(invalid, modal, True, record_property)
    assert _snapshot() == before
    result = client.post(url, {**data, "csrfmiddlewaretoken": token}, headers=headers)
    assert result.status_code == (204 if modal else 302)
    assert result.headers["X-CV-Redirect" if modal else "Location"]
    assert result.wsgi_request.POST[submitter["name"]] == submitter["value"]
    if kind == "create":
        assert Author.objects.filter(first_name="Owned", last_name="Request", pseudonym="Preserved").exists()
    elif kind == "update":
        author.refresh_from_db()
        assert (author.first_name, author.last_name, author.pseudonym) == ("Owned", "Request", "Preserved")
    elif kind == "delete":
        assert not Author.objects.filter(pk=author.pk).exists()
    elif kind == "workflow":
        obj.refresh_from_db()
        assert obj.state == CampaignState.ACTIVE
        assert WorkflowInfo.objects.filter(workflow_object_pk=str(obj.pk), transition="wf_activate").count() == 1
    else:
        assert _snapshot() == before  # Existing contact view intentionally has no write hook.


@pytest.mark.parametrize("modal", [False, True])
def test_workflow_no_choices_preserves_distinct_bodies(
    modal, campaign_success, user_campaign_change, monkeypatch, record_property
):
    monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_campaign_change)
    url = f"/campaign/{campaign_success.pk}/workflow/"
    headers = {"X-CV-Modal": "true"} if modal else {}
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    _workflow_templates(response, modal, False, record_property)
    if modal:
        owner, _ = _owned(response, url, "workflow", modal)
        token = owner["tokens"][0]
    else:
        scanner = _RawForms()
        scanner.feed(response.content.decode())
        assert scanner.forms == []
        assert b"csrfmiddlewaretoken" not in response.content
        assert b"There are no workflow steps available from the current state." in response.content
        # Obtain a legitimate token from another owner to test the omitted workflow's POST endpoint.
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", True)
        token = assert_owned_form_markup(client.get(url, headers={"X-CV-Modal": "true"}).content.decode())["tokens"][0]
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", False)
    before = _snapshot()
    result = client.post(url, {"transition": "wf_activate", "csrfmiddlewaretoken": token}, headers=headers)
    assert result.status_code == (422 if modal else 200)
    _workflow_templates(result, modal, False, record_property)
    assert _snapshot() == before


@pytest.mark.parametrize("view", [AuthorCreateView, AuthorUpdateView])
def test_create_update_modal_support_stays_rejected(view, monkeypatch):
    assert view.cv_modal_supported is False
    monkeypatch.setattr(view, "cv_modal", True)
    assert any(message.id == "viewset.E251" for check in view.checks() for message in check.messages())
