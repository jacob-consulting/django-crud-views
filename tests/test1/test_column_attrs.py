"""ColumnAttrs merging (`|`) — regression tests for #117."""

from crud_views.lib.table.attrs import ColAttr, ColumnAttrs


def test_merge_does_not_mutate_either_operand():
    a = ColumnAttrs({"td": {"class": "x"}})
    b = ColumnAttrs({"td": {"class": "y"}})

    merged = a | b

    assert dict(merged) == {"td": {"class": "x y"}}
    assert dict(a) == {"td": {"class": "x"}}
    assert dict(b) == {"td": {"class": "y"}}


def test_shared_presets_are_stable_across_repeated_merges():
    first = ColAttr.w10 | ColAttr.ID
    second = ColAttr.w10 | ColAttr.w20

    assert dict(ColAttr.w10) == {"td": {"class": "cv-col-10"}}
    assert dict(first) == {"td": {"class": "cv-col-10 cv-col-id"}}
    assert dict(second) == {"td": {"class": "cv-col-10 cv-col-20"}}


def test_class_merge_has_no_leading_or_duplicate_tokens():
    assert dict(ColumnAttrs({"td": {}}) | ColumnAttrs.td_class("y")) == {"td": {"class": "y"}}
    assert dict(ColumnAttrs.td_class("x") | ColumnAttrs.td_class("x")) == {"td": {"class": "x"}}


def test_th_and_td_are_merged_independently():
    assert dict(ColumnAttrs.th_class("a") | ColumnAttrs.td_class("b")) == {"th": {"class": "a"}, "td": {"class": "b"}}


def test_non_class_values_are_overwritten_and_nested_dicts_merged_recursively():
    a = ColumnAttrs({"td": {"style": "left", "data": {"k": "1"}}})
    b = ColumnAttrs({"td": {"style": "right", "data": {"j": "2"}}, "title": "t"})

    assert dict(a | b) == {"td": {"style": "right", "data": {"k": "1", "j": "2"}}, "title": "t"}
    assert dict(a) == {"td": {"style": "left", "data": {"k": "1"}}}
