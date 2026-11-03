"""Cancel parity across migrated templates, Crispy controls and invalid form responses."""

import re
from copy import copy
from html import unescape
from urllib.parse import urlencode

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from lxml import html as lxml_html

from crud_views.lib.view.cancel import encode_cancel_state
from crud_views.templatetags import crud_views as tags
from tests.test1.app.models import Author
from tests.test1.test_cancel_navigation import emitted_link

MIGRATED = '{% load crud_views %}{% cv_cancel_url as url %}{% if url %}<a href="{{ url }}">Cancel</a>{% endif %}'


def cancel_control(response):
    nodes = lxml_html.fromstring(response.content).xpath(
        "//form//button[@data-cv-cancel-url] | //form//a[normalize-space(.)='Cancel']"
    )
    assert len(nodes) == 1
    return nodes[0]


def rendered_cancel(response):
    node = cancel_control(response)
    return node.get("data-cv-cancel-url") or node.get("href")


def test_cancel_url_tag_registered():
    assert "cv_cancel_url" in tags.register.tags


def migrated(response, argument=""):
    template = MIGRATED.replace("cv_cancel_url as", f"cv_cancel_url {argument} as")
    return Template(template).render(Context({"view": response.context["view"], "request": response.wsgi_request}))


def assert_owner(response):
    html = response.content.decode()
    assert len(re.findall(r"<form\b", html)) == 1
    assert html.count('name="csrfmiddlewaretoken"') == 1
    assert 'type="submit"' in html
    assert 'name="None"' not in html
    assert 'id="div_id_None"' not in html
    (form,) = lxml_html.fromstring(response.content).xpath("//form")
    # Workflow's existing page form omits action, which submits to the current URL.
    assert (form.get("action") or response.wsgi_request.get_full_path()) == response.wsgi_request.get_full_path()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["create", "update", "delete", "contact", "broadcast"])
@pytest.mark.parametrize("tag", ["button", "a"])
@pytest.mark.parametrize("query", ["", "x=&x=%3Cscript%3E%26%22%27"])
def test_invalid_posts_keep_surface_parity(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch, settings, key, tag, query
):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": tag}
    source = cv_author_origin.get_view_class("list")
    monkeypatch.setattr(source, "cv_context_actions", ["create", "broadcast"])
    monkeypatch.setattr(source, "cv_list_actions", ["update", "delete", "contact"])
    monkeypatch.setattr(cv_author_origin.get_view_class("broadcast"), "cv_icon_action", "create")
    target = cv_author_origin.get_view_class(key)
    monkeypatch.setattr(target, "cv_cancel_keys", "auto")
    prefix = f"/author_origin/{author_douglas_adams.pk}" if target.cv_object else "/author_origin"
    page = client_user_author_origin.get("/author_origin/?" + query)
    link = emitted_link(page, f"{prefix}/{key}/")
    expected = "/author_origin/?" + (query + "&" if query else "") + "cv_from_restore=1"
    before = list(Author.objects.values())
    for _ in range(2):
        response = client_user_author_origin.post(link, {})
        assert response.status_code == 200
        assert response.context["form"].errors
        assert_owner(response)
        url = rendered_cancel(response)
        assert url == expected
        copied = migrated(response)
        assert unescape(re.search(r'href="([^"]+)"', copied)[1]) == url
        assert ("&amp;" in copied) is bool(query)
        assert "<script>" not in copied
        assert cancel_control(response).tag == tag
    assert list(Author.objects.values()) == before


@pytest.mark.django_db
@pytest.mark.parametrize("argument", ["", "missing", "None", "''", "object", "unsaved"])
def test_template_object_arguments(client_user_author_origin, author_douglas_adams, argument):
    response = client_user_author_origin.get(f"/author_origin/{author_douglas_adams.pk}/update/?cv_from=detail")
    view = response.context["view"]
    context = Context(
        {"view": view, "request": response.wsgi_request, "object": view.object, "unsaved": Author(first_name="New")}
    )
    template = Template(MIGRATED.replace("cv_cancel_url as", f"cv_cancel_url {argument} as"))
    result = template.render(context)
    expected = "/author_origin/card/" if argument == "unsaved" else f"/author_origin/{view.object.pk}/detail/"
    assert unescape(re.search(r'href="([^"]+)"', result)[1]) == expected


@pytest.mark.django_db
def test_tag_errors_are_not_suppressed(client_user_author_origin, cv_author_origin, monkeypatch):
    response = client_user_author_origin.get("/author_origin/create/")
    view = response.context["view"]
    no_view = Context({"request": response.wsgi_request})
    with pytest.raises(KeyError):
        tags.cv_cancel_url(no_view)
    no_request = Context({"view": view})
    with pytest.raises(KeyError):
        tags.cv_cancel_url(no_request)
    monkeypatch.setattr(view, "cv_cancel_key", "missing")
    context = Context({"view": view, "request": response.wsgi_request})
    with pytest.raises(ImproperlyConfigured, match="configure a registered usable destination"):
        tags.cv_cancel_url(context)


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["create", "delete"])
@pytest.mark.parametrize("allowed", [False, True])
@pytest.mark.parametrize("tag", ["a", "button"])
def test_custom_action_groups_filter_omitted_cancel(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch, settings, key, allowed, tag
):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": tag}
    target = cv_author_origin.get_view_class(key)
    calls = []

    class CustomActions(target.form_class):
        def get_cancel_button_kwargs(self):
            calls.append("kwargs")
            return {**super().get_cancel_button_kwargs(), "css_class": "custom-cancel"}

        def get_form_actions(self):
            return FormActions(
                *[button for button in [self.get_submit_button(), self.get_cancel_button()] if button is not None]
            )

    class CustomDelete(CustomActions):
        @property
        def helper(self):
            helper = FormHelper()
            helper.form_tag = False
            helper.layout = Layout(
                "confirm",
                FormActions(
                    *[button for button in [self.get_delete_button(), self.get_cancel_button()] if button is not None]
                ),
            )
            return helper

    monkeypatch.setattr(target, "form_class", CustomDelete if key == "delete" else CustomActions)
    for destination in ["list", "card"]:
        monkeypatch.setattr(
            cv_author_origin.get_view_class(destination),
            "cv_has_access",
            classmethod(lambda cls, user, obj=None: allowed),
        )
    prefix = f"/author_origin/{author_douglas_adams.pk}" if key == "delete" else "/author_origin"
    response = client_user_author_origin.post(f"{prefix}/{key}/?cv_from=list", {})
    assert response.status_code == 200
    assert_owner(response)
    html = response.content.decode()
    assert (
        bool(
            lxml_html.fromstring(html).xpath(
                "//form//a[normalize-space(.)='Cancel'] | //form//button[@data-cv-cancel-url]"
            )
        )
        is allowed
    )
    assert ("custom-cancel" in html) is allowed
    assert bool(calls) is allowed
    assert bool(migrated(response)) is allowed
    if allowed:
        assert rendered_cancel(response) == "/author_origin/"


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["delete", "contact"])
@pytest.mark.parametrize("tag", ["button", "a"])
def test_modal_replacement_retains_capture(client_user_author_modal, author_douglas_adams, settings, key, tag):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": tag}
    page = client_user_author_modal.get("/author_modal/?x=&x=modal")
    # Existing list actions do not include contact; use the actual origin's public link generator.
    view = page.context["view"]
    link = view.cv_get_link_url(view.cv_get_cls(key), key, author_douglas_adams)
    for _ in range(2):
        response = client_user_author_modal.post(link, {}, headers={"X-CV-Modal": "true"})
        assert response.status_code == 422
        assert_owner(response)
        assert rendered_cancel(response) == "/author_modal/?x=&x=modal&cv_from_restore=1"
        assert "modal-body" in response.content.decode()
        assert unescape(re.search(r'href="([^"]+)"', migrated(response))[1]) == rendered_cancel(response)


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_workflow_invalid_submission_inherits_cancel(
    client_user_campaign_change, user_campaign_change, cv_campaign, campaign_new, monkeypatch, modal
):
    from tests.lib.helper.user import user_viewset_permission

    user_viewset_permission(user_campaign_change, cv_campaign, "view")
    monkeypatch.setattr(cv_campaign.get_view_class("workflow"), "cv_modal", modal)
    monkeypatch.setattr(
        cv_campaign.get_view_class("list"), "get_queryset", lambda self: self.model.objects.order_by("pk")
    )
    page = client_user_campaign_change.get("/campaign/?x=&x=workflow")
    link = emitted_link(page, f"/campaign/{campaign_new.pk}/workflow/")
    for _ in range(2):
        response = client_user_campaign_change.post(link, {}, headers={"X-CV-Modal": "true"} if modal else {})
        assert response.status_code == (422 if modal else 200)
        assert_owner(response)
        assert rendered_cancel(response) == "/campaign/?x=&x=workflow&cv_from_restore=1"
    campaign_new.refresh_from_db()
    assert campaign_new.state == "new"


@pytest.mark.django_db
def test_protected_delete_omits_form_and_cancel(client_user_author_origin, author_douglas_adams):
    author_douglas_adams.pseudonym = "protected"
    author_douglas_adams.save()
    for method in ["get", "post"]:
        response = getattr(client_user_author_origin, method)(
            f"/author_origin/{author_douglas_adams.pk}/delete/?cv_from=list"
        )
        assert response.status_code == 200
        assert "<form" not in response.content.decode()
        assert "data-cv-cancel-url" not in response.content.decode()


@pytest.mark.django_db
def test_request_override_uses_current_context(client_user_author_origin, cv_author_origin, monkeypatch):
    response = client_user_author_origin.get("/author_origin/create/")
    view = response.context["view"]
    request = copy(response.wsgi_request)
    request.GET = request.GET.copy()
    request.GET["cv_from_cancel"] = encode_cancel_state(view, "list", "x=override")
    monkeypatch.setattr(view, "cv_get_link_url", lambda *a, **kw: pytest.fail("Cancel must not capture its form"))
    assert (
        tags.cv_cancel_url(Context({"view": view, "request": request}))
        == "/author_origin/?x=override&cv_from_restore=1"
    )
    assert view.request.GET == {}


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["create", "update"])
def test_capture_does_not_change_save_location(client_user_author_origin, cv_author_origin, author_douglas_adams, key):
    page = client_user_author_origin.get("/author_origin/?x=old")
    view = page.context["view"]
    link = view.cv_get_link_url(view.cv_get_cls(key), key, author_douglas_adams)
    response = client_user_author_origin.post(link, {"first_name": "Saved", "last_name": "Name"})
    assert response.status_code == 302
    assert response["Location"] == "/author_origin/"


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["delete", "contact"])
def test_capture_does_not_change_modal_success_location(client_user_author_modal, author_douglas_adams, key):
    page = client_user_author_modal.get("/author_modal/?x=old")
    view = page.context["view"]
    link = view.cv_get_link_url(view.cv_get_cls(key), key, author_douglas_adams)
    data = {"confirm": True} if key == "delete" else {"subject": "Hello", "body": "Message"}
    response = client_user_author_modal.post(link, data, headers={"X-CV-Modal": "true"})
    assert response.status_code == 204
    assert response["X-CV-Redirect"] == "/author_modal/"


@pytest.mark.parametrize("key", ["create", "update"])
def test_cancel_does_not_enable_unsupported_modals(cv_author_origin, monkeypatch, key):
    cls = cv_author_origin.get_view_class(key)
    monkeypatch.setattr(cls, "cv_modal", True)
    assert "viewset.E251" in [message.id for check in cls.checks() for message in check.messages()]


@pytest.mark.django_db
def test_template_autoescapes_resolver_url(client_user_author_origin, monkeypatch):
    response = client_user_author_origin.get("/author_origin/create/")
    url = '/author_origin/?q="quoted"&next=<script>alert(1)</script>'
    monkeypatch.setattr(response.context["view"], "cv_get_cancel_url", lambda **kwargs: url)
    result = migrated(response)
    assert (
        result
        == '<a href="/author_origin/?q=&quot;quoted&quot;&amp;next=&lt;script&gt;alert(1)&lt;/script&gt;">Cancel</a>'
    )


@pytest.mark.django_db
def test_invalid_capture_survives_repeated_posts(client_user_author_origin, author_douglas_adams):
    link = f"/author_origin/{author_douglas_adams.pk}/update/?" + urlencode(
        {"cv_from": "detail", "cv_from_cancel": "invalid"}
    )
    for _ in range(2):
        response = client_user_author_origin.post(link, {})
        assert rendered_cancel(response) == "/author_origin/card/"
        assert "/author_origin/card/" in migrated(response)
