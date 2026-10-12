"""#149: context buttons (toolbar, cv_context_button, cv_context_url, cv_get_context_buttons) in disable mode."""

import pytest
from django.template import Context, Template
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import ContextButton
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorDeleteView, AuthorDetailView, AuthorUpdateView


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change_149", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


def _detail(client, cv_author, author):
    resp = client.get(reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk}))
    assert resp.status_code == 200
    return resp


def _render(resp, source):
    return Template("{% load crud_views %}" + source).render(
        Context({"view": resp.context["view"], "request": resp.context["request"]})
    )


@pytest.mark.django_db
def test_toolbar_hide_is_default(client_user_author_view, cv_author, author_douglas_adams):
    doc = lxml_html.fromstring(_detail(client_user_author_view, cv_author, author_douglas_adams).content)
    assert doc.cssselect('[cv-context-container] [cv-key="delete"]') == []


@pytest.mark.django_db
def test_toolbar_disabled_for_permission(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    doc = lxml_html.fromstring(resp.content)
    (btn,) = doc.cssselect('[cv-context-container] [cv-key="delete"]')
    assert btn.tag == "button"
    assert btn.get("disabled") is not None
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert btn.get("data-cv-modal") is None
    assert f"/author/{author_douglas_adams.pk}/delete/" not in resp.content.decode()
    # update targets AuthorUpdateView, still "hide": absent
    assert doc.cssselect('[cv-context-container] [cv-key="update"]') == []


@pytest.mark.django_db
def test_toolbar_disabled_for_state(client_author_view_change, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorUpdateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    doc = lxml_html.fromstring(_detail(client_author_view_change, cv_author, author_douglas_adams).content)
    (btn,) = doc.cssselect('[cv-context-container] [cv-key="update"]')
    assert btn.get("data-cv-disabled") == "state"
    assert btn.get("href") is None


@pytest.mark.django_db
def test_context_button_tag_and_url(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    out = _render(resp, '{% cv_context_button "delete" %}|{% cv_context_url "delete" as u %}[{{ u }}]')
    button, url = out.split("|")
    assert "<button" in button
    assert " disabled" in button
    assert "href=" not in button
    assert url == "[None]"


@pytest.mark.django_db
def test_context_url_none_in_hide_mode(client_user_author_view, cv_author, author_douglas_adams):
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    assert _render(resp, '{% cv_context_url "delete" as u %}[{{ u }}]') == "[None]"


@pytest.mark.django_db
def test_get_context_buttons_flags_disabled(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    view = _detail(client_user_author_view, cv_author, author_douglas_adams).context["view"]
    by_key = {b["cv_key"]: b for b in view.cv_get_context_buttons()}
    assert by_key["delete"]["cv_disabled"] is True
    assert by_key["delete"]["cv_url"] is None
    assert by_key["detail"]["cv_disabled"] is False
    assert "update" not in by_key


@pytest.mark.django_db
def test_loop_render_disabled_entry(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    out = _render(
        resp, "{% for ctx in view.cv_get_context_buttons %}<li>{% cv_render_context_button ctx %}</li>{% endfor %}"
    )
    doc = lxml_html.fromstring(f"<ul>{out}</ul>")
    (btn,) = doc.cssselect('[cv-key="delete"]')
    assert btn.get("disabled") is not None
    (detail,) = doc.cssselect('[cv-key="detail"]')
    assert detail.get("href")


@pytest.mark.django_db
def test_custom_template_code_receives_disabled_data(
    client_user_author_view, cv_author, author_douglas_adams, monkeypatch
):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(
        AuthorDetailView,
        "cv_context_buttons",
        [
            ContextButton(
                key="del_custom",
                key_target="delete",
                template_code=(
                    '<i data-d="{{ cv_disabled }}" data-r="{{ cv_disabled_reason }}" data-u="{{ cv_url }}"></i>'
                ),
            )
        ],
    )
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    assert (
        _render(resp, '{% cv_context_button "del_custom" %}')
        == '<i data-d="True" data-r="permission" data-u="None"></i>'
    )
