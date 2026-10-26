"""#264: ContextButton.label_mode — precedence, toolbar-only reach and system check viewset.E210."""

import pytest
from django.test import override_settings
from lxml import html as lxml_html

from crud_views.lib.view import ContextButton, ParentContextButton
from tests.test1.app.views import AuthorDetailView, AuthorListView, cv_author
from tests.test1.test_action_label_mode_render import (
    AUTHOR_FULL,
    _button,
    _client,
    _detail_url,
    _detail_view,
    _render,
    _rows,
    _toolbar,
)

E210 = "viewset.E210"


def _with_viewset_buttons(monkeypatch, *buttons):
    monkeypatch.setattr(cv_author, "context_buttons", [*cv_author.context_buttons, *buttons])


def _update_button(label_mode):
    return ContextButton(key="update", key_target="update", label_mode=label_mode)


def _messages(checks, check_id):
    return [m.msg for c in checks for m in c.messages() if m.id == check_id]


def _is_text_only(el) -> bool:
    return (
        el.xpath("./*[@aria-hidden='true']") == [] and el.get("title") is None and bool(el.xpath("./span[not(@class)]"))
    )


# precedence: view map naming the key -> button -> first map of view / ViewSet / setting -> "icon"


def test_button_label_mode_wins_over_viewset_map(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "icon"})
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "label"


def test_view_map_naming_key_beats_button(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "both"


def test_view_map_without_key_yields_to_button(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"detail": "both"})
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "label"


def test_view_map_without_key_and_no_button_mode_is_icon(monkeypatch):
    # a view map replaces the ViewSet map as a whole, as before (#216)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"detail": "both"})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "label"})
    _with_viewset_buttons(monkeypatch, _update_button(None))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"


def test_no_button_mode_unchanged(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "both"})
    _with_viewset_buttons(monkeypatch, _update_button(None))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "both"
    assert AuthorDetailView.cv_get_action_label_mode("context", "delete") == "icon"


def test_view_level_button_beats_viewset_button(monkeypatch):
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [_update_button("both")])
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "both"


def test_list_location_ignores_button(monkeypatch):
    _with_viewset_buttons(monkeypatch, ContextButton(key="detail", key_target="detail", label_mode="label"))
    assert AuthorListView.cv_get_action_label_mode("list", "detail") == "icon"


# rendering


@pytest.mark.django_db
def test_toolbar_renders_button_mode(author_douglas_adams, monkeypatch):
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    assert _is_text_only(_button(toolbar, "update"))
    assert _button(toolbar, "detail").get("title")  # still icon-only


@pytest.mark.django_db
def test_button_label_mode_does_not_reach_rows(author_douglas_adams, monkeypatch):
    _with_viewset_buttons(monkeypatch, ContextButton(key="detail", key_target="detail", label_mode="label"))
    (td,) = _rows(_client([AUTHOR_FULL]))
    detail = _button(td.cssselect("fieldset")[0], "detail")
    assert detail.get("title")
    assert detail.xpath("./span[contains(@class, 'visually-hidden')]")


@pytest.mark.django_db
def test_cv_context_button_tag_follows_button(author_douglas_adams, monkeypatch):
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    (el,) = lxml_html.fragments_fromstring(_render(view, request, '{% cv_context_button "update" %}'))
    assert _is_text_only(el)


# checks


def test_e210_invalid_button_label_mode_at_viewset(monkeypatch):
    vs = cv_author.model_copy(update={"context_buttons": [*cv_author.context_buttons, _update_button("text")]})
    (msg,) = _messages(vs.checks(), E210)
    assert "context button 'update'" in msg
    assert "'text'" in msg


def test_e210_invalid_button_label_mode_at_view(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [_update_button("text")])
    (msg,) = _messages(AuthorDetailView.checks(), E210)
    assert "context button 'update'" in msg


def test_e210_on_default_button():
    home = ContextButton(key="home", key_target="list", label_mode="text")
    vs = cv_author.model_copy(update={"context_buttons": [home]})
    assert _messages(vs.checks(), E210)


def test_no_e210_for_valid_or_unset_label_mode():
    buttons = [_update_button("label"), ContextButton(key="detail", key_target="detail")]
    vs = cv_author.model_copy(update={"context_buttons": buttons})
    assert _messages(vs.checks(), E210) == []


@pytest.mark.django_db
def test_instance_level_button_mode_reaches_rendering(author_douglas_adams):
    # buttons a view instance sets on itself are honoured, like cv_get_context_button() does (#27)
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    view.cv_context_buttons = [_update_button("label")]
    data = view.cv_get_context(key="update", obj=author_douglas_adams, user=request.user, location="context")
    assert data["cv_label_mode"] == "label"


# viewset.W292: an icon-only toolbar key whose target has no icon

W292 = "viewset.W292"


def _target(key):
    return cv_author.get_view_class(key)


def _w292(view=AuthorDetailView):
    return _messages(view.checks(), W292)


@pytest.mark.parametrize("icon", [None, ""])
def test_w292_key_without_button(monkeypatch, icon):
    monkeypatch.setattr(_target("update"), "cv_icon_action", icon)
    (msg,) = _w292()
    assert "'update'" in msg
    assert "AuthorDetailView" in msg


def test_w292_plain_button_target_without_icon(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    (msg,) = _w292()
    assert "'edit'" in msg


def test_w292_silent_with_button_label_mode(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update", label_mode="label"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    assert _w292() == []


def test_w292_silent_with_map(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    assert _w292() == []


def test_w292_silent_with_icon():
    assert _w292() == []


def test_w292_skips_menu_folded_key(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["detail"])
    assert _w292() == []


def test_w292_checks_inline_key(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    assert len(_w292()) == 1


def test_w292_skips_custom_template_button(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update", template_code="<b>x</b>"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    assert _w292() == []


def test_w292_skips_get_context_override(monkeypatch):
    monkeypatch.setattr(_target("list"), "cv_icon_action", None)
    _with_viewset_buttons(monkeypatch, ParentContextButton(key="up", key_target="list"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["up", "filter"])
    assert _w292() == []


def test_w292_skips_unregistered_target(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["nope"])
    assert _w292() == []


# final review fixes


@pytest.mark.django_db
def test_strict_error_names_the_configured_key(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    with pytest.raises(ValueError, match=r"context action 'edit' "):
        _client([AUTHOR_FULL]).get(_detail_url(author_douglas_adams))


@pytest.mark.parametrize("inline", [5, "update"])
def test_w292_does_not_crash_on_invalid_inline(monkeypatch, inline):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)
    ids = [m.id for c in AuthorDetailView.checks() for m in c.messages()]
    assert "viewset.W292" not in ids


# W292 and CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]


@pytest.mark.parametrize("floor", ["label", "both"])
def test_w292_silent_with_context_floor(monkeypatch, floor):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": floor}):
        assert _w292() == []
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": floor, "card": floor}):
        (msg,) = _w292()  # other locations do not reach the toolbar
    assert "'update'" in msg


@pytest.mark.parametrize(
    "explicit",
    [
        lambda mp: mp.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "icon"}),
        lambda mp: mp.setattr(cv_author, "context_actions_label_mode", {"update": "icon"}),
        lambda mp: mp.setattr(_target("update"), "cv_context_action_label_mode", "icon"),
        lambda mp: _with_viewset_buttons(mp, _update_button("icon")),
    ],
    ids=["view-map", "viewset-map", "target-view", "button"],
)
def test_w292_explicit_icon_still_warns_with_floor(monkeypatch, explicit):
    # a valid both floor silences W292 only for keys that actually use it
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    monkeypatch.setattr(_target("delete"), "cv_icon_action", None)
    explicit(monkeypatch)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both"}):
        (msg,) = _w292()
    assert "'update'" in msg


@pytest.mark.parametrize("floor", [{"context": "nope"}, None], ids=["bad-mode", "non-dict"])
def test_invalid_floor_check_viewsets_returns_e108(monkeypatch, floor):
    from crud_views.checks import check_viewsets

    # an icon-less, unmapped target: W292 has to resolve the mode through the invalid floor
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    # an unrelated diagnostic of the same view that must survive too
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"udpate": "both"})
    with override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
        messages = check_viewsets()
        # strict rendering still raises for that key
        with pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
            AuthorDetailView.cv_get_action_label_mode("context", "update")
    ids = [m.id for m in messages]
    assert "crud_views.E108" in ids
    w291 = [m for m in messages if m.id == "viewset.W291" and "udpate" in m.msg]
    assert w291
    assert [m for m in messages if m.id == W292 and "AuthorDetailView" in m.msg] == []
