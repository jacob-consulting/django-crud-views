"""#216: labelled context and list buttons as rendered by crud_views/tags/button/action.html."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ContextButton
from tests.lib.helper.guardian import user_guardian_object_perm
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorCreateView,
    AuthorCustomDetailListView,
    AuthorDetailView,
    AuthorListView,
    GuardianAuthorListView,
    cv_author,
    cv_author_custom_detail,
)

AUTHOR_FULL = (cv_author, ("view", "add", "change", "delete"))
AUTHOR_VIEW = (cv_author, ("view",))


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"label_216_{uuid.uuid4().hex[:8]}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _toolbar(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath("//fieldset[@cv-context-container]")[0]


def _rows(client):
    resp = client.get(reverse(cv_author.get_router_name("list")))
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath("//td[.//fieldset[@cv-list-container]]")


def _detail_url(author):
    return reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})


def _detail_view(client, author):
    resp = client.get(_detail_url(author))
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


def _render(view, request, snippet, **extra):
    tpl = Template("{% load crud_views %}" + snippet)
    return tpl.render(Context({"view": view, "request": request, **extra})).strip()


def _buttons(container) -> dict[str, bytes]:
    return {el.get("cv-key"): lxml_html.tostring(el) for el in container.xpath("./*[@cv-key]")}


def _button(container, key):
    (el,) = container.xpath(f'./*[@cv-key="{key}"]')
    return el


@pytest.mark.django_db
def test_toolbar_labelled_create_leaves_the_other_buttons_byte_identical(author_douglas_adams, monkeypatch):
    client = _client([AUTHOR_FULL])
    url = reverse(cv_author.get_router_name("list"))
    before = _buttons(_toolbar(client, url))
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    toolbar = _toolbar(client, url)
    after = _buttons(toolbar)
    assert {k: v for k, v in after.items() if k != "create"} == {k: v for k, v in before.items() if k != "create"}
    assert after["create"] != before["create"]
    create = _button(toolbar, "create")
    assert create.get("title") is None
    assert create.get("data-cv-tooltip") is None
    assert create.xpath("./*[@aria-hidden='true']")  # the icon
    (span,) = create.xpath("./span")
    assert span.get("class") is None
    assert span.text == "Create"


@pytest.mark.django_db
def test_toolbar_label_mode_renders_text_without_icon(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "label"})
    create = _button(_toolbar(_client([AUTHOR_FULL]), reverse(cv_author.get_router_name("list"))), "create")
    assert create.xpath("./*[@aria-hidden='true']") == []
    assert create.get("title") is None
    (span,) = create.xpath("./span")
    assert span.text == "Create"


@pytest.mark.django_db
def test_context_button_is_matched_by_its_configured_key(author_douglas_adams, monkeypatch):
    # "home" targets the list view and renders cv-key="list"; the map names "home"
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"home": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    home = _button(toolbar, "list")
    assert home.get("title") is None
    assert home.xpath("./span[not(@class)]")
    assert _button(toolbar, "detail").get("title")  # still icon-only


@pytest.mark.django_db
def test_row_labelled_detail_next_to_icon_only_update(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"})
    (td,) = _rows(_client([AUTHOR_FULL]))
    fieldset = td.cssselect("fieldset")[0]
    detail = _button(fieldset, "detail")
    assert detail.get("title") is None
    assert [s.text for s in detail.xpath("./span")] == ["Detail"]
    update = _button(fieldset, "update")
    assert update.get("title")
    assert update.xpath("./span[contains(@class, 'visually-hidden')]")


@pytest.mark.django_db
def test_row_same_variant_different_modes_get_different_classes(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:secondary:both": "btn btn-xs x-both"}):
        (td,) = _rows(_client([AUTHOR_FULL]))
    fieldset = td.cssselect("fieldset")[0]
    assert _button(fieldset, "detail").get("class") == "btn btn-xs x-both"
    assert _button(fieldset, "update").get("class") == "btn btn-outline-primary btn-xs"


@pytest.mark.django_db
def test_labelled_post_row_action_keeps_submit_target(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"ping": "both"})
    (td,) = _rows(_client([AUTHOR_FULL]))
    ping = _button(td.cssselect("fieldset")[0], "ping")
    assert ping.tag == "button"
    assert ping.get("data-cv-action") == "submit-form"
    assert ping.get("data-cv-target", "").startswith("cv_form_")
    assert ping.get("title") is None
    assert ping.xpath("./span[not(@class)]")


@pytest.mark.django_db
def test_folded_labelled_key_has_no_title_and_icon_key_keeps_it(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"detail": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
    assert detail.get("title") is None
    assert "Detail" in detail.text_content()
    assert toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0].get("title")


@pytest.mark.django_db
def test_manual_placement_follows_the_view(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    view, request = _detail_view(_client([(cv_author, ("view", "change"))]), author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert ">Update</span>" in html
    assert "visually-hidden" not in html
    assert "title=" not in html


@pytest.mark.django_db
def test_labelled_key_without_access_is_hidden(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    toolbar = _toolbar(_client([AUTHOR_VIEW]), reverse(cv_author.get_router_name("list")))
    assert toolbar.xpath('./*[@cv-key="create"]') == []


@pytest.mark.django_db
def test_labelled_key_rendered_disabled(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCreateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    create = _button(_toolbar(_client([AUTHOR_VIEW]), reverse(cv_author.get_router_name("list"))), "create")
    assert create.tag == "button"
    assert create.get("disabled") is not None
    assert create.get("data-cv-disabled") == "permission"
    assert create.get("title") is None
    assert [s.text for s in create.xpath("./span")] == ["Create"]


@pytest.mark.django_db
def test_custom_template_code_sees_label_mode(author_douglas_adams, monkeypatch):
    custom = ContextButton(key="edit_big", key_target="update", template_code='<a cv-key="big">{{ cv_label_mode }}</a>')
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [custom])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "edit_big"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"edit_big": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    assert toolbar.xpath('./a[@cv-key="big"]')[0].text == "both"


@pytest.mark.django_db
def test_cv_get_context_without_location_is_unstamped(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    view, request = _detail_view(_client([(cv_author, ("view", "change"))]), author_douglas_adams)
    kwargs = {"obj": author_douglas_adams, "user": request.user, "request": request}
    plain = view.cv_get_context("update", **kwargs)
    assert "cv_label_mode" not in plain
    stamped = view.cv_get_context("update", location="context", **kwargs)
    assert stamped["cv_label_mode"] == "both"
    assert view.cv_get_context("no_such_key", location="context", **kwargs) == {}
    (custom_loop,) = view.cv_get_context_buttons(["update"], obj=author_douglas_adams)
    assert custom_loop["cv_label_mode"] == "both"


# the per-key tags and the guardian override each pass the location themselves (final review)


@pytest.mark.django_db
def test_plain_list_view_rows_render_through_the_per_key_tag(author_douglas_adams, monkeypatch):
    # view_list.content.html loops {% cv_list_action key object %}: no table, no container
    monkeypatch.setattr(AuthorCustomDetailListView, "cv_list_actions_label_mode", {"detail": "both"})
    resp = _client([(cv_author_custom_detail, ("view",))]).get(reverse(cv_author_custom_detail.get_router_name("list")))
    assert resp.status_code == 200
    (detail,) = lxml_html.fromstring(resp.content).xpath('//td/*[@cv-key="detail"]')
    assert detail.get("title") is None
    assert [span.text for span in detail.xpath("./span")] == ["Detail"]


@pytest.mark.django_db
def test_per_key_context_action_tag_follows_the_view(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    view, request = _detail_view(_client([(cv_author, ("view", "change"))]), author_douglas_adams)
    html = _render(view, request, "{% cv_context_action 'update' object %}", object=author_douglas_adams)
    assert ">Update</span>" in html
    assert "visually-hidden" not in html
    assert "title=" not in html


@pytest.mark.django_db
def test_guardian_override_forwards_the_location(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, monkeypatch
):
    # GuardianQuerysetMixin (list and card views) overrides cv_get_context(); the row path goes through it
    monkeypatch.setattr(GuardianAuthorListView, "cv_list_actions_label_mode", {"detail": "both"})
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    resp = client_guardian.get(reverse(cv_guardian_author.get_router_name("list")))
    assert resp.status_code == 200
    (td,) = lxml_html.fromstring(resp.content).xpath("//td[.//fieldset[@cv-list-container]]")
    detail = _button(td.cssselect("fieldset")[0], "detail")
    assert detail.get("title") is None
    assert [span.text for span in detail.xpath("./span")] == ["Detail"]


# CRUD_VIEWS_LABEL_MODE_DEFAULTS["list"] on real table rows


def _text_only(el) -> bool:
    spans = el.xpath("./span")
    return (
        el.xpath("./*[@aria-hidden='true']") == []
        and el.get("title") is None
        and len(spans) == 1
        and spans[0].get("class") is None
        and bool((spans[0].text or "").strip())
    )


def _icon_only(el) -> bool:
    return (
        bool(el.xpath("./*[@aria-hidden='true']"))
        and bool(el.get("title"))
        and bool(el.xpath("./span[contains(@class, 'visually-hidden')]"))
    )


@pytest.mark.django_db
def test_list_floor_renders_unmapped_rows(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", None)
    monkeypatch.setattr(cv_author, "list_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "list_actions_label_mode", {})
    client = _client([AUTHOR_FULL])
    list_url = reverse(cv_author.get_router_name("list"))

    (td,) = _rows(client)
    keys = [el.get("cv-key") for el in td.cssselect("fieldset")[0].xpath("./*[@cv-key]")]
    assert keys == ["detail", "update", "delete"]
    assert all(_icon_only(_button(td.cssselect("fieldset")[0], k)) for k in keys)  # unconfigured: unchanged

    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": "label"}):
        (td,) = _rows(client)
        toolbar = _toolbar(client, list_url)
    fieldset = td.cssselect("fieldset")[0]
    for key in keys:
        assert _text_only(_button(fieldset, key)), lxml_html.tostring(_button(fieldset, key))
    # the context floor is independent: the toolbar stays icon-only
    assert all(_icon_only(el) for el in toolbar.xpath("./*[@cv-key]"))

    # an explicitly mapped key keeps its mode; the view map replaces the lower maps whole
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"update": "icon"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": "label"}):
        (td,) = _rows(client)
    fieldset = td.cssselect("fieldset")[0]
    assert _icon_only(_button(fieldset, "update"))
    assert _text_only(_button(fieldset, "detail"))
    assert _text_only(_button(fieldset, "delete"))
