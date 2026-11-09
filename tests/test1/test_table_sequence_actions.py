"""Table column order honours Meta.sequence; the actions column is dropped when the view declares
``cv_list_actions = None`` (#337, origin: tabler-test finding 26)."""

from types import SimpleNamespace

import django_tables2 as tables

from crud_views.lib.table import Table

ROWS = [{"id": 1, "first_name": "Douglas", "last_name": "Adams", "pseudonym": ""}]


def _view(actions):
    """The only view attribute Table reads at construction time."""
    return SimpleNamespace(cv_list_actions=actions)


def _names(table):
    return list(table.columns.names())


class PlainTable(Table):
    id = tables.Column()
    first_name = tables.Column()
    last_name = tables.Column()


class SequencedTable(PlainTable):
    class Meta:
        sequence = ("last_name", "...")


class MiddleEllipsisTable(PlainTable):
    class Meta:
        sequence = ("last_name", "...", "id")


class ActionsFirstTable(PlainTable):
    class Meta:
        sequence = ("actions", "...")


def test_no_meta_sequence_keeps_actions_last():
    table = PlainTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["id", "first_name", "last_name", "actions"]


def test_meta_sequence_is_honoured_and_actions_appended():
    table = SequencedTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["last_name", "id", "first_name", "actions"]


def test_meta_sequence_with_middle_ellipsis_keeps_actions_last():
    table = MiddleEllipsisTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["last_name", "first_name", "id", "actions"]


def test_meta_sequence_naming_actions_is_used_as_written():
    table = ActionsFirstTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["actions", "id", "first_name", "last_name"]


def test_sequence_kwarg_wins_over_meta_sequence():
    # a caller sequence is passed through untouched: Meta.sequence is ignored and nothing is appended
    table = SequencedTable(ROWS, view=_view(["detail"]), sequence=("first_name", "...", "actions"))
    assert _names(table) == ["first_name", "id", "last_name", "actions"]
    bare = SequencedTable(ROWS, view=_view(["detail"]), sequence=("first_name", "..."))
    assert _names(bare) == ["first_name", "actions", "id", "last_name"]  # inherited `actions` is first in "..."


def test_cv_default_sequence_values():
    assert PlainTable.cv_default_sequence() == ("...", "actions")
    assert SequencedTable.cv_default_sequence() == ("last_name", "...", "actions")
    assert ActionsFirstTable.cv_default_sequence() == ("actions", "...")
