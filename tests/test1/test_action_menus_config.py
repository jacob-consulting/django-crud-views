"""#174: inline-keys settings, ViewSet fields, view attributes, resolution and checks."""

import pytest
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view import CardAction
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDetailView,
    AuthorListView,
    cv_author,
)


def test_settings_defaults():
    s = CrudViewsSettings()
    assert s.list_actions_inline is None
    assert s.context_actions_inline is None
    assert s.card_actions_inline is None


@pytest.mark.parametrize("field", ["list_actions_inline", "context_actions_inline", "card_actions_inline"])
@pytest.mark.parametrize("value", ["detail", ["detail", 1], {"detail": True}, 3])
def test_invalid_setting_e105(field, value):
    messages = CrudViewsSettings(**{field: value}).check_messages
    assert [m.id for m in messages] == ["crud_views.E105"]
    assert f"CRUD_VIEWS_{field.upper()}" in messages[0].msg


@pytest.mark.parametrize("value", [None, [], ["detail"], ("detail", "up")])
def test_valid_setting_values(value):
    assert CrudViewsSettings(list_actions_inline=value).check_messages == []


def test_viewset_rejects_invalid_value():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Author

    with pytest.raises(ValidationError):
        ViewSet(model=Author, name="author_bad_inline_174", list_actions_inline="detail")


def test_viewset_accepts_tuple():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="author_tuple_inline_174", context_actions_inline=("update",))
    assert list(vs.context_actions_inline) == ["update"]


def test_default_resolves_to_none():
    assert AuthorListView.cv_get_list_actions_inline() is None
    assert AuthorDetailView.cv_get_context_actions_inline() is None
    assert AuthorCardListView.cv_get_card_actions_inline() is None


def test_setting_is_last_fallback(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "list_actions_inline", ["detail"])
    assert AuthorListView.cv_get_list_actions_inline() == ["detail"]


def test_viewset_beats_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_inline", ["detail"])
    monkeypatch.setattr(cv_author, "context_actions_inline", ["update"])
    assert AuthorDetailView.cv_get_context_actions_inline() == ["update"]


def test_view_empty_list_beats_viewset(monkeypatch):
    # [] is meaningful ("fold everything"): it must not fall through like a falsy value
    monkeypatch.setattr(cv_author, "card_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", [])
    assert AuthorCardListView.cv_get_card_actions_inline() == []


def _ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [
        (AuthorListView, "cv_list_actions_inline"),
        (AuthorDetailView, "cv_context_actions_inline"),
        (AuthorCardListView, "cv_card_actions_inline"),
    ],
)
@pytest.mark.parametrize("value", ["detail", ["detail", None]])
def test_e208_invalid_view_value(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    assert "viewset.E208" in _ids(view_cls)


def test_no_inline_messages_by_default():
    for view_cls in (AuthorListView, AuthorDetailView, AuthorCardListView):
        ids = _ids(view_cls)
        assert "viewset.E208" not in ids
        assert "viewset.W290" not in ids


def test_w290_unknown_list_key(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail", "detial"])
    messages = [m for c in AuthorListView.checks() for m in c.messages() if m.id == "viewset.W290"]
    assert len(messages) == 1
    assert "detial" in messages[0].msg
    assert messages[0].level == 30  # django.core.checks.WARNING


def test_w290_known_keys_no_warning(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ("detail", "update"))
    assert "viewset.W290" not in _ids(AuthorListView)


def test_w290_context_key(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home", "upd"])
    assert "viewset.W290" in _ids(AuthorDetailView)


def test_w290_card_matches_key_and_child_name(monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [CardAction(key="detail"), CardAction(child_name="book", label="Books")],
    )
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "book"])
    assert "viewset.W290" not in _ids(AuthorCardListView)
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["books"])
    assert "viewset.W290" in _ids(AuthorCardListView)


def test_w290_never_for_viewset_or_setting(monkeypatch):
    # shared defaults name keys some views lack (Review Focus 3): no warning, and no render-time error
    monkeypatch.setattr(cv_author, "list_actions_inline", ["detail", "up", "down"])
    monkeypatch.setattr(crud_views_settings, "context_actions_inline", ["nonexistent"])
    for view_cls in (AuthorListView, AuthorDetailView):
        assert "viewset.W290" not in _ids(view_cls)
