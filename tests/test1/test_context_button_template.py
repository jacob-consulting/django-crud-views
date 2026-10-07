"""ContextButton template / template_code fields and the settings default."""

import pytest
from django.urls import reverse

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.buttons import ContextButton, FilterContextButton


def test_settings_default_template():
    assert crud_views_settings.context_button_template == "crud_views/tags/context_action.html"


def test_settings_template_override(monkeypatch):
    from django.conf import settings as dj_settings

    monkeypatch.setattr(dj_settings, "CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE", "x/y.html", raising=False)
    # property reads Django settings live
    assert crud_views_settings.context_button_template == "x/y.html"


def test_inject_template_default():
    data = {}
    ContextButton(key="edit", key_target="update")._inject_template(data)
    assert data == {"cv_template": "crud_views/tags/context_action.html"}


def test_inject_template_file():
    data = {}
    ContextButton(key="edit", key_target="update", template="app/edit.html")._inject_template(data)
    assert data == {"cv_template": "app/edit.html"}


def test_inject_template_code_wins():
    data = {}
    ContextButton(
        key="edit", key_target="update", template="app/edit.html", template_code="<a>{{ cv_url }}</a>"
    )._inject_template(data)
    assert data == {"cv_template_code": "<a>{{ cv_url }}</a>"}


def test_filter_button_default_template():
    assert FilterContextButton().template == "crud_views/tags/context_action_filter.html"


def _publisher_list_view(client, cv_publisher):
    url = reverse(cv_publisher.get_router_name("list"))
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_filter_button_default_label(client_user_publisher_view, cv_publisher):
    view = _publisher_list_view(client_user_publisher_view, cv_publisher)
    ctx = FilterContextButton().get_context(view.cv_get_view_context())
    assert ctx["cv_action_label"] == "Filter"


@pytest.mark.django_db
def test_filter_button_templated_label(client_user_publisher_view, cv_publisher):
    view = _publisher_list_view(client_user_publisher_view, cv_publisher)
    ctx = FilterContextButton(label_template_code="Suchen").get_context(view.cv_get_view_context())
    assert ctx["cv_action_label"] == "Suchen"


def _author_detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_author_view_change", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


@pytest.fixture
def cv_author_custom_edit(monkeypatch, cv_author):
    """cv_author plus whole-button variants of the edit button (inline code and file template)."""
    buttons = [
        *cv_author.context_buttons,
        ContextButton(key="edit_code", key_target="update", template_code='<a class="custom-code">Edit</a>'),
        ContextButton(key="edit_file", key_target="update", template="app/custom_edit_button.html"),
    ]
    monkeypatch.setattr(cv_author, "context_buttons", buttons)
    return cv_author


def _render_action(view, request, key):
    from django.template import Context, Template

    tpl = Template("{% load crud_views %}{% cv_context_action key object %}")
    return tpl.render(Context({"view": view, "request": request, "key": key, "object": view.object})).strip()


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["edit_code", "edit_file"])
def test_context_action_custom_template_hidden_without_access(
    client_user_author_view, cv_author_custom_edit, author_douglas_adams, key
):
    view, request = _author_detail_view(client_user_author_view, cv_author_custom_edit, author_douglas_adams)
    assert _render_action(view, request, key) == ""


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["edit_code", "edit_file"])
def test_context_action_custom_template_rendered_with_access(
    client_author_view_change, cv_author_custom_edit, author_douglas_adams, key
):
    view, request = _author_detail_view(client_author_view_change, cv_author_custom_edit, author_douglas_adams)
    assert "custom-" in _render_action(view, request, key)
