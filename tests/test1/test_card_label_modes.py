"""CardListView.cv_card_action_label_mode and its viewset.E210 check."""

from crud_views.lib.view import CardAction
from crud_views.lib.views import CardListView
from tests.test1.app.views import AuthorCardListView

E210 = "viewset.E210"


def e210(checks) -> list[str]:
    return [m.msg for c in checks for m in c.messages() if m.id == E210]


def test_default_is_both():
    assert CardListView.cv_card_action_label_mode == "both"


def test_bad_view_label_mode_raises_e210(monkeypatch):
    assert e210(AuthorCardListView.checks()) == []
    monkeypatch.setattr(AuthorCardListView, "cv_card_action_label_mode", "nope")
    messages = e210(AuthorCardListView.checks())
    assert len(messages) == 1
    assert "'nope'" in messages[0]
    assert "cv_card_action_label_mode" in messages[0]


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
    for mode in ("label", "icon", "both"):
        monkeypatch.setattr(AuthorCardListView, "cv_card_action_label_mode", mode)
        assert e210(AuthorCardListView.checks()) == []
