"""#174: cv_split_actions / ActionGroup / cv_context_button_foldable."""

import copy

import pytest

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.action_menu import ActionGroup, cv_context_button_foldable, cv_split_actions


def _items(*keys):
    return [(key, {"cv_key": key}) for key in keys]


def _keys(ctxs):
    return [c["cv_key"] for c in ctxs]


def test_none_means_feature_off():
    assert cv_split_actions(_items("detail", "update"), None) is None


def test_empty_list_folds_everything():
    group = cv_split_actions(_items("detail", "update", "delete"), [])
    assert _keys(group.inline) == []
    assert _keys(group.menu) == ["detail", "update", "delete"]


def test_named_keys_stay_inline_order_kept():
    group = cv_split_actions(_items("detail", "update", "delete", "up", "down"), ["down", "detail"])
    # inline keeps the action order, not the inline-list order
    assert _keys(group.inline) == ["detail", "down"]
    assert _keys(group.menu) == ["update", "delete", "up"]


def test_tuple_inline_keys():
    group = cv_split_actions(_items("detail", "update"), ("detail",))
    assert _keys(group.inline) == ["detail"]


def test_unknown_inline_key_ignored():
    group = cv_split_actions(_items("detail", "update"), ["nope"])
    assert _keys(group.inline) == []
    assert _keys(group.menu) == ["detail", "update"]


def test_matches_configured_key_not_cv_key():
    # ContextButton(key="home", key_target="list") resolves to cv_key="list"
    group = cv_split_actions([("home", {"cv_key": "list"}), ("update", {"cv_key": "update"})], ["home"])
    assert _keys(group.inline) == ["list"]


def test_disabled_items_split_like_others():
    items = [("detail", {"cv_key": "detail"}), ("delete", {"cv_key": "delete", "cv_disabled": True})]
    group = cv_split_actions(items, ["detail"])
    assert group.menu == [{"cv_key": "delete", "cv_disabled": True}]


def test_unfoldable_stays_inline_under_empty_list():
    items = [("filter", {"cv_key": "filter", "pin": True}), ("update", {"cv_key": "update"})]
    group = cv_split_actions(items, [], foldable=lambda ctx: not ctx.get("pin"))
    assert _keys(group.inline) == ["filter"]
    assert _keys(group.menu) == ["update"]


def test_input_not_mutated():
    items = _items("detail", "update")
    before = copy.deepcopy(items)
    cv_split_actions(items, ["detail"])
    assert items == before


def test_all_is_inline_then_menu():
    group = ActionGroup(inline=[{"a": 1}], menu=[{"b": 2}])
    assert group.all == [{"a": 1}, {"b": 2}]


@pytest.mark.parametrize(
    ("ctx", "expected"),
    [
        ({"cv_template": None}, True),
        ({}, True),
        ({"cv_template": "DEFAULT"}, True),
        ({"cv_template": "my/button.html"}, False),
        ({"cv_template": "DEFAULT", "cv_template_code": "<b>x</b>"}, False),
    ],
)
def test_context_button_foldable(ctx, expected):
    ctx = {k: (crud_views_settings.context_button_template if v == "DEFAULT" else v) for k, v in ctx.items()}
    assert cv_context_button_foldable(ctx) is expected


def test_filter_button_template_is_not_foldable():
    ctx = {"cv_template": f"{crud_views_settings.theme_path}/tags/context_action_filter.html"}
    assert cv_context_button_foldable(ctx) is False
