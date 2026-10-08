"""Accessible markup of the action, filter-toggle and formset-control templates."""

import pytest
from django.template import Context, Template
from lxml import html

from tests.lib.helper.user import user_viewset_permission


def _doc(response):
    assert response.status_code == 200
    return html.fromstring(response.content)


def _assert_icon_action_named(el):
    """Icon-only action: the name comes from visually hidden text matching the title,
    not from aria-label (an aria-label that differs from the visible content is what
    WCAG 2.5.3 / Sonar S7927 flag)."""
    assert el.get("aria-label") is None
    (hidden,) = el.cssselect("span.visually-hidden")
    assert hidden.text_content().strip()
    assert hidden.text_content().strip() == el.get("title")
    assert all(i.get("aria-hidden") == "true" for i in el.cssselect("i"))


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
        _assert_icon_action_named(a)


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
        _assert_icon_action_named(a)


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
    assert up.tag == "button"
    assert up.get("type") == "button"
    assert up.get("data-cv-action") == "submit-form"
    _assert_icon_action_named(up)
    assert doc.cssselect(f"form#{up.get('data-cv-target')}"), "the targeted POST form must exist"
    (detail,) = doc.cssselect('[cv-list-container] [cv-key="detail"]')
    assert detail.tag == "a"
    assert detail.get("href")


@pytest.mark.django_db
def test_filter_toggle_is_a_labelled_button(client):
    from django.contrib.auth.models import User

    from tests.test1.app.views import cv_publisher_order

    user = User.objects.create_user(username="a11y_filter", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client.force_login(user)
    doc = _doc(client.get("/publisher_order/card/"))
    (toggle,) = doc.cssselect("#cv-filter-toggle")
    assert toggle.tag == "button"
    assert toggle.get("type") == "button"
    assert toggle.get("role") is None
    _assert_icon_action_named(toggle)


def test_formset_controls_have_labels_and_hidden_icons():
    from types import SimpleNamespace

    tpl = Template('{% include "crud_views/formsets/control.html" %}')
    rendered = tpl.render(
        Context({"formset": SimpleNamespace(can_order=True, can_delete=True), "form": SimpleNamespace(prefix="p-0")})
    )
    doc = html.fromstring(rendered)
    groups = doc.cssselect("fieldset.btn-group")
    assert len(groups) == 3
    labels = [g.get("aria-label") for g in groups]
    assert all(labels), labels
    assert len(set(labels)) == len(labels), labels
    buttons = doc.cssselect("button")
    assert len(buttons) == 4
    assert all(b.get("aria-label") for b in buttons)
    assert all(i.get("aria-hidden") == "true" for i in doc.cssselect("i"))
