"""Real page/modal owners, template provenance and enforced-CSRF write contracts."""

import json
from pathlib import Path
from types import ModuleType

import pytest
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import path
from lxml import html

from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views_polymorphic.lib.create_select import PolymorphicCreateSelectViewPermissionRequired
from crud_views_workflow.models import WorkflowInfo
from tests.test1.app.models import Author, Campaign, CampaignState, Car, Publisher, Vehicle
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
    record_property("workflow_branch", json.dumps({"modal": modal, "choices": choices, "templates": actual}))


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
    cancel = form.cssselect("[data-cv-cancel-url]")[0]
    assert cancel.get("type") == "button"
    assert cancel.get("data-cv-cancel-url")
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


@pytest.mark.parametrize(("kind", "modal"), MODES)
def test_forbidden_actor_cannot_write(kind, modal, request, monkeypatch, user_a):
    author = request.getfixturevalue("author_douglas_adams")
    if kind == "workflow":
        campaign = request.getfixturevalue("campaign_new")
        monkeypatch.setattr(CampaignWorkflowView, "cv_modal", modal)
        url = f"/campaign/{campaign.pk}/workflow/"
    elif kind in ("custom", "delete"):
        url = f"/author_modal/{author.pk}/{'contact' if kind == 'custom' else kind}/"
    else:
        url = "/author/create/" if kind == "create" else f"/author/{author.pk}/update/"
    authorized = Client(enforce_csrf_checks=True)
    authorized.force_login(request.getfixturevalue("user_author_add"))
    token = assert_owned_form_markup(authorized.get("/author/create/").content.decode())["tokens"][0]
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_a)
    client.cookies["csrftoken"] = authorized.cookies["csrftoken"].value
    headers = {"X-CV-Modal": "true"} if modal else {}
    before = _snapshot()
    assert client.get(url, headers=headers).status_code == 403
    payload = {
        "csrfmiddlewaretoken": token,
        "first_name": "Denied",
        "last_name": "Write",
        "confirm": "on",
        "subject": "Denied",
        "body": "Write",
        "transition": "wf_activate",
    }
    assert client.post(url, payload, headers=headers).status_code == 403
    assert _snapshot() == before


@pytest.mark.parametrize("modal", [False, True])
def test_protected_form_omission(modal, request, publisher_penguin):
    user = request.getfixturevalue("user_publisher_modal_protected_delete")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    url = f"/publisher_modal_protected/{publisher_penguin.pk}/delete/"
    headers = {"X-CV-Modal": "true"} if modal else {}
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    scanner = _RawForms()
    scanner.feed(response.content.decode())
    assert scanner.forms == []
    assert b"csrfmiddlewaretoken" not in response.content
    assert b"Cannot delete this publisher." in response.content
    other = Client(enforce_csrf_checks=True)
    other.force_login(request.getfixturevalue("user_author_add"))
    token = assert_owned_form_markup(other.get("/author/create/").content.decode())["tokens"][0]
    client.cookies["csrftoken"] = other.cookies["csrftoken"].value
    response = client.post(url, {"confirm": "on", "csrfmiddlewaretoken": token}, headers=headers)
    assert response.status_code == (422 if modal else 200)
    assert b"Cannot delete this publisher." in response.content
    assert b"csrfmiddlewaretoken" not in response.content
    assert Publisher.objects.filter(pk=publisher_penguin.pk).exists()


class PlainContactForm(forms.Form):
    message = forms.CharField()


class PlainContactView(CustomFormViewPermissionRequired):
    model = Author
    cv_key = "contact"
    form_class = PlainContactForm
    cv_header_template_code = "Plain contact"
    cv_paragraph_template_code = "Send a plain message"


class PlainSelectionView(PolymorphicCreateSelectViewPermissionRequired):
    model = Vehicle


@pytest.mark.parametrize("kind", ["plain", "selection"])
def test_owned_form_payload_preservation(kind, request, monkeypatch, settings, author_douglas_adams):
    from tests.test1.app.urls import urlpatterns
    from tests.test1.app.views import cv_author, cv_vehicle

    # Actual library views on local routes; only the form/provider configuration differs.
    monkeypatch.setattr(PlainContactView, "cv_viewset", cv_author)
    monkeypatch.setattr(PlainSelectionView, "cv_viewset", cv_vehicle)
    urls = ModuleType("ownership_urls")
    urls.urlpatterns = [
        *urlpatterns,
        path("ownership/plain/<uuid:pk>/", PlainContactView.as_view()),
        path("ownership/select/", PlainSelectionView.as_view()),
    ]
    settings.ROOT_URLCONF = urls
    client = Client(enforce_csrf_checks=True)
    client.force_login(request.getfixturevalue("user_author_view" if kind == "plain" else "user_vehicle_add"))
    url = f"/ownership/plain/{author_douglas_adams.pk}/" if kind == "plain" else "/ownership/select/"
    car_type = ContentType.objects.get_for_model(Car)
    data = {"message": "Plain payload"} if kind == "plain" else {"polymorphic_ctype_id": str(car_type.pk)}
    response = client.get(url)
    assert response.status_code == 200
    assert not hasattr(response.context["form"], "helper")
    owner = assert_owned_form_markup(response.content.decode())
    assert owner["attrs"]["action"] == url
    assert owner["attrs"]["enctype"] == "multipart/form-data"
    document = html.fromstring(response.content)
    form = document.cssselect("form.cv-form")[0]
    for control in document.cssselect("input, select, textarea"):
        assert next(control.iterancestors("form"), None) is form
    if kind == "selection":
        assert form.xpath(".//select[@name='polymorphic_ctype_id']/option[@value=$value]", value=str(car_type.pk))
    before = (_snapshot(), list(Vehicle.objects.values()))
    for token in (None, "invalid"):
        payload = dict(data)
        if token is not None:
            payload["csrfmiddlewaretoken"] = token
        assert client.post(url, payload).status_code == 403
        assert (_snapshot(), list(Vehicle.objects.values())) == before
    invalid = client.post(url, {"csrfmiddlewaretoken": owner["tokens"][0]})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    assert_owned_form_markup(invalid.content.decode())
    assert not hasattr(invalid.context["form"], "helper")
    result = client.post(url, {**data, "csrfmiddlewaretoken": owner["tokens"][0]})
    assert result.status_code == 302
    if kind == "selection":
        assert result.url == f"/vehicle/create/ct/{car_type.pk}/"
    else:
        assert result.url == "/author/"
    assert (_snapshot(), list(Vehicle.objects.values())) == before


def test_existing_polymorphic_selection_route(user_vehicle_add):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_vehicle_add)
    url = "/vehicle/create/select/"
    response = client.get(url)
    owner, form = _owned(response, url, "create", False)
    car_type = ContentType.objects.get_for_model(Car)
    assert form.xpath(".//select[@name='polymorphic_ctype_id']/option[@value=$value]", value=str(car_type.pk))
    submitter = owner["submitters"][0]
    payload = {"polymorphic_ctype_id": str(car_type.pk), submitter["name"]: submitter["value"]}
    assert client.post(url, payload).status_code == 403
    invalid = client.post(url, {"csrfmiddlewaretoken": owner["tokens"][0]})
    assert invalid.status_code == 200
    assert_owned_form_markup(invalid.content.decode())
    result = client.post(url, {**payload, "csrfmiddlewaretoken": owner["tokens"][0]})
    assert result.status_code == 302
    assert result.url == f"/vehicle/create/ct/{car_type.pk}/"
    assert Vehicle.objects.count() == 0
