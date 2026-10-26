"""CardListView.cv_card_actions_label_mode, its resolver and its viewset.E210 check."""

import pytest
from django.test import override_settings

from crud_views.lib.view import CardAction
from crud_views.lib.views import CardListView
from tests.test1.app.views import AuthorCardListView

E210 = "viewset.E210"


def e210(checks) -> list[str]:
    return [m.msg for c in checks for m in c.messages() if m.id == E210]


def test_default_attribute_is_none_and_resolves_both():
    # the raw attribute is unset; the resolver supplies the package card floor (D-14, D-15)
    assert CardListView.cv_card_actions_label_mode is None
    assert CardListView.cv_get_card_actions_label_mode() == "both"
    assert AuthorCardListView.cv_get_card_actions_label_mode() == "both"


def test_card_resolver_reads_setting():
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"}):
        assert CardListView.cv_get_card_actions_label_mode() == "label"
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "icon"}):
            assert CardListView.cv_get_card_actions_label_mode() == "icon"
        assert CardListView.cv_get_card_actions_label_mode() == "label"
    # leaving override_settings restores the package floor, and the raw attribute never changed
    assert CardListView.cv_get_card_actions_label_mode() == "both"
    assert CardListView.cv_card_actions_label_mode is None


def test_card_explicit_mode_bypasses_floor(monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", "both")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"}):
        assert AuthorCardListView.cv_get_card_actions_label_mode() == "both"
    # a valid explicit attribute never reads the floor, so an invalid strict floor cannot raise
    invalid_floor = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope"}, CRUD_VIEWS_STRICT=True)
    with invalid_floor:
        assert AuthorCardListView.cv_get_card_actions_label_mode() == "both"
        monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", None)
        with pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS key 'card'"):
            AuthorCardListView.cv_get_card_actions_label_mode()


@pytest.mark.parametrize("value", ["", "Both", " both", "both ", "LABEL", "b\u03bfth"])
def test_card_attribute_exact_modes(value, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", value)
    messages = e210(AuthorCardListView.checks())
    assert len(messages) == 1
    assert repr(value) in messages[0]
    assert "cv_card_actions_label_mode" in messages[0]


def test_card_lookalike_is_greek_omicron():
    # the source spells the lookalike with an escape (RUF001); at runtime it must be a real U+03BF
    assert ord("b\u03bfth"[1]) == 0x3BF


def test_bad_view_label_mode_raises_e210(monkeypatch):
    assert e210(AuthorCardListView.checks()) == []
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", "nope")
    messages = e210(AuthorCardListView.checks())
    assert len(messages) == 1
    assert "'nope'" in messages[0]
    assert "cv_card_actions_label_mode" in messages[0]


def test_bad_action_label_mode_raises_e210(monkeypatch):
    # CardAction validates at construction, so bypass the validator to model a value that arrived another way
    action = CardAction(key="detail")
    object.__setattr__(action, "label_mode", "loud")
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [action])
    messages = e210(AuthorCardListView.checks())
    assert len(messages) == 1
    assert "'loud'" in messages[0]
    assert "card action 'detail'" in messages[0]


def test_good_values_yield_no_check(monkeypatch):
    actions = [
        CardAction(key="detail", label_mode="icon"),
        CardAction(key="update", label_mode="label"),
        CardAction(key="delete", label_mode="both"),
        CardAction(key="detail"),
    ]
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", actions)
    for mode in (None, "label", "icon", "both"):
        monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", mode)
        assert e210(AuthorCardListView.checks()) == []
