"""Table respects the django-tables2 Meta configuration (#337).

`Table` only supplies its default ``sequence=("...", "actions")`` when the subclass declares no `Meta.sequence`;
a declared sequence is used as written. `Meta.exclude = ("actions",)` removes the actions column.
"""

import django_tables2 as tables

from crud_views.lib.table import Table

ROWS = [{"id": 1, "first_name": "Douglas", "last_name": "Adams"}]
VIEW = object()  # Table only needs a view to be passed through


class PlainTable(Table):
    id = tables.Column()
    first_name = tables.Column()
    last_name = tables.Column()


class SequencedTable(PlainTable):
    class Meta:
        sequence = ("last_name", "...", "actions")


class NoActionsTable(PlainTable):
    class Meta:
        exclude = ("actions",)


def _names(table) -> list[str]:
    return [column.name for column in table.columns]


def test_default_puts_actions_last():
    assert _names(PlainTable(ROWS, view=VIEW)) == ["id", "first_name", "last_name", "actions"]


def test_meta_sequence_is_used_as_written():
    assert _names(SequencedTable(ROWS, view=VIEW)) == ["last_name", "id", "first_name", "actions"]


def test_sequence_kwarg_wins_over_meta_sequence():
    table = SequencedTable(ROWS, view=VIEW, sequence=("first_name", "...", "actions"))
    assert _names(table) == ["first_name", "id", "last_name", "actions"]


def test_meta_exclude_removes_actions_column():
    assert _names(NoActionsTable(ROWS, view=VIEW)) == ["id", "first_name", "last_name"]
