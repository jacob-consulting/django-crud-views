"""#178: POST-only views in cv_context_actions submit a hidden form, inline and from the toolbar's action menu."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorDetailView, AuthorUpView, cv_author


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="toolbar_post_178", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


def _doc(client, author):
    resp = client.get(reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk}))
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content)


def _toolbar(doc):
    return doc.xpath("//fieldset[@cv-context-container]")[0]


def _assert_form(doc, target, author, path):
    forms = doc.cssselect(f"form#{target}")
    assert len(forms) == 1
    form = forms[0]
    assert form.get("action") == f"/author/{author.pk}/{path}/"
    assert form.get("method") == "post"
    assert form.cssselect("input[name='csrfmiddlewaretoken']")
    # outside the btn-group: a hidden child would break Bootstrap's first/last-child corner rounding
    assert not form.xpath("ancestor::fieldset")


@pytest.mark.django_db
def test_inline_post_action_submits_form(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "up"])
    doc = _doc(client_full, author_douglas_adams)
    toolbar = _toolbar(doc)
    up = toolbar.xpath('./*[@cv-key="up"]')[0]
    assert up.tag == "button"
    assert up.get("type") == "button"
    assert up.get("href") is None
    assert up.get("data-cv-action") == "submit-form"
    assert "btn-lg" in up.get("class")
    assert up.get("title")
    _assert_form(doc, up.get("data-cv-target"), author_douglas_adams, "up")


@pytest.mark.django_db
def test_menu_post_action_submits_form(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "update", "up"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    doc = _doc(client_full, author_douglas_adams)
    item = _toolbar(doc).cssselect('.dropdown-item[cv-key="up"]')[0]
    assert item.tag == "button"
    assert item.get("href") is None
    assert item.get("data-cv-action") == "submit-form"
    _assert_form(doc, item.get("data-cv-target"), author_douglas_adams, "up")


@pytest.mark.django_db
@pytest.mark.parametrize("inline", [None, []])
def test_get_actions_render_no_form(client_full, author_douglas_adams, monkeypatch, inline):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)
    doc = _doc(client_full, author_douglas_adams)
    assert not doc.cssselect("form[id^='cv_form_']")
    assert not _toolbar(doc).cssselect("[data-cv-action='submit-form']")


@pytest.mark.django_db
@pytest.mark.parametrize("inline", [None, ["detail"]])
def test_disabled_post_action_renders_no_form(client_user_author_view, author_douglas_adams, monkeypatch, inline):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "up"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    doc = _doc(client_user_author_view, author_douglas_adams)
    up = _toolbar(doc).xpath('.//*[@cv-key="up"]')[0]
    assert up.get("disabled") is not None
    assert up.get("data-cv-action") is None
    assert not doc.cssselect("form[id^='cv_form_']")


@pytest.mark.django_db
def test_unregistered_key_skipped(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "no_such_view", "up"])
    doc = _doc(client_full, author_douglas_adams)
    assert len(doc.cssselect("form[id^='cv_form_']")) == 1


@pytest.mark.django_db
def test_form_post_is_not_405(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "up"])
    doc = _doc(client_full, author_douglas_adams)
    form = doc.cssselect("form[id^='cv_form_']")[0]
    resp = client_full.post(form.get("action"))
    assert resp.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("inline", [None, ["detail"]])
def test_context_button_wrapping_post_target(client_full, author_douglas_adams, monkeypatch, inline):
    from crud_views.lib.view import ContextButton

    buttons = [
        ContextButton(key="raise", key_target="up", label_template_code="Raise"),
        ContextButton(key="lower", key_target="down", label_template_code="Lower"),
    ]
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", buttons)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "raise", "lower"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)
    doc = _doc(client_full, author_douglas_adams)
    triggers = _toolbar(doc).cssselect("[data-cv-action='submit-form']")
    targets = {t.get("cv-key"): t.get("data-cv-target") for t in triggers}
    assert set(targets) == {"up", "down"}
    assert targets["up"] != targets["down"]
    _assert_form(doc, targets["up"], author_douglas_adams, "up")
    _assert_form(doc, targets["down"], author_douglas_adams, "down")


@pytest.mark.django_db
def test_manual_placement_pairs_button_and_form(client_full, author_douglas_adams):
    from django.template import RequestContext, Template

    resp = client_full.get(reverse(cv_author.get_router_name("detail"), kwargs={"pk": author_douglas_adams.pk}))
    view, request = resp.context["view"], resp.context["request"]
    tpl = Template("{% load crud_views %}{% cv_context_action_form 'up' %}{% cv_context_button 'up' %}")
    doc = lxml_html.fromstring(f"<div>{tpl.render(RequestContext(request, {'view': view}))}</div>")
    button = doc.cssselect("[data-cv-action='submit-form']")[0]
    _assert_form(doc, button.get("data-cv-target"), author_douglas_adams, "up")
    # GET target: the form tag renders nothing
    assert (
        Template("{% load crud_views %}{% cv_context_action_form 'update' %}")
        .render(RequestContext(request, {"view": view}))
        .strip()
        == ""
    )
