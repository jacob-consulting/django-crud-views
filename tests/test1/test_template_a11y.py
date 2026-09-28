"""Accessible markup of the action, filter-toggle and formset-control templates."""

import pytest
from django.template import Context, Template
from lxml import html

from tests.lib.helper.user import user_viewset_permission


def _doc(response):
    assert response.status_code == 200
    return html.fromstring(response.content)


@pytest.mark.django_db
def test_context_actions_are_labelled_links_without_button_role(
    client_user_author_view, cv_author, author_douglas_adams
):
    doc = _doc(client_user_author_view.get(f"/author/{author_douglas_adams.pk}/detail/"))
    actions = doc.cssselect("[cv-context-container] a[cv-key]")
    assert actions
    for a in actions:
        assert a.get("href")
        assert a.get("role") is None
        assert a.get("aria-label")
        assert all(i.get("aria-hidden") == "true" for i in a.cssselect("i"))


@pytest.mark.django_db
def test_get_list_actions_are_labelled_links_without_button_role(
    client_user_author_view, cv_author, author_douglas_adams
):
    doc = _doc(client_user_author_view.get("/author/"))
    links = doc.cssselect("[cv-list-container] a[cv-key]")
    assert links
    for a in links:
        assert a.get("href")
        assert a.get("role") is None
        assert a.get("aria-label")


@pytest.mark.django_db
def test_post_list_action_is_a_button_that_submits_its_form(client, cv_author, author_douglas_adams, monkeypatch):
    from django.contrib.auth.models import User

    from tests.test1.app.views import AuthorListView

    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "up"])
    user = User.objects.create_user(username="a11y_post", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)

    doc = _doc(client.get("/author/"))
    (up,) = doc.cssselect('[cv-list-container] [cv-key="up"]')
    assert up.tag == "button" and up.get("type") == "button"
    assert up.get("data-cv-action") == "submit-form"
    assert up.get("aria-label")
    assert doc.cssselect(f"form#{up.get('data-cv-target')}"), "the targeted POST form must exist"
    (detail,) = doc.cssselect('[cv-list-container] [cv-key="detail"]')
    assert detail.tag == "a" and detail.get("href")


@pytest.mark.django_db
def test_filter_toggle_is_a_labelled_button(client):
    from django.contrib.auth.models import User

    from tests.test1.app.views import cv_publisher_order

    user = User.objects.create_user(username="a11y_filter", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client.force_login(user)
    doc = _doc(client.get("/publisher_order/card/"))
    (toggle,) = doc.cssselect("#cv-filter-toggle")
    assert toggle.tag == "button" and toggle.get("type") == "button"
    assert toggle.get("role") is None
    assert toggle.get("aria-label")


def test_formset_controls_have_labels_and_hidden_icons():
    from types import SimpleNamespace

    tpl = Template('{% include "crud_views/formsets/control.html" %}')
    rendered = tpl.render(
        Context({"formset": SimpleNamespace(can_order=True, can_delete=True), "form": SimpleNamespace(prefix="p-0")})
    )
    doc = html.fromstring(rendered)
    groups = doc.cssselect('[role="group"]')
    labels = [g.get("aria-label") for g in groups]
    assert all(labels) and len(set(labels)) == len(labels), labels
    buttons = doc.cssselect("button")
    assert len(buttons) == 4
    assert all(b.get("aria-label") for b in buttons)
    assert all(i.get("aria-hidden") == "true" for i in doc.cssselect("i"))
