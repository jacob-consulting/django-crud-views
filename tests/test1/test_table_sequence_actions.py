"""Table column order honours Meta.sequence; the actions column is dropped when the view declares
``cv_list_actions = None`` (#337, origin: tabler-test finding 26)."""

from types import SimpleNamespace

import django_tables2 as tables
import pytest

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


class NoEllipsisTable(PlainTable):
    class Meta:
        sequence = ("last_name",)


def test_no_meta_sequence_keeps_actions_last():
    table = PlainTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["id", "first_name", "last_name", "actions"]


def test_meta_sequence_is_honoured_and_actions_appended():
    table = SequencedTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["last_name", "id", "first_name", "actions"]


def test_meta_sequence_with_middle_ellipsis_keeps_actions_last():
    table = MiddleEllipsisTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["last_name", "first_name", "id", "actions"]


def test_meta_sequence_without_ellipsis_keeps_actions_last():
    table = NoEllipsisTable(ROWS, view=_view(["detail"]))
    assert _names(table) == ["last_name", "id", "first_name", "actions"]
    assert NoEllipsisTable.cv_default_sequence() == ("last_name", "...", "actions")


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
    assert NoEllipsisTable.cv_default_sequence() == ("last_name", "...", "actions")


class ExcludingTable(PlainTable):
    pseudonym = tables.Column()

    class Meta:
        exclude = ("pseudonym",)


def test_none_list_actions_drops_actions_column():
    table = PlainTable(ROWS, view=_view(None))
    assert _names(table) == ["id", "first_name", "last_name"]


def test_empty_list_actions_keeps_actions_column():
    # [] is what a view, or ListView via CRUD_VIEWS_LIST_ACTIONS = [], carries today: the (empty) column stays
    table = PlainTable(ROWS, view=_view([]))
    assert _names(table)[-1] == "actions"


def test_empty_tuple_list_actions_keeps_actions_column():
    table = PlainTable(ROWS, view=_view(()))
    assert _names(table)[-1] == "actions"


def test_none_list_actions_with_actions_in_meta_sequence_drops_column_without_error():
    table = ActionsFirstTable(ROWS, view=_view(None))
    assert _names(table) == ["id", "first_name", "last_name"]


def test_meta_exclude_is_merged_not_replaced():
    table = ExcludingTable(ROWS, view=_view(None))
    assert _names(table) == ["id", "first_name", "last_name"]


def test_exclude_kwarg_is_merged_with_actions_exclusion():
    table = PlainTable(ROWS, view=_view(None), exclude=("first_name",))
    assert _names(table) == ["id", "last_name"]
    bare = PlainTable(ROWS, view=_view(None), exclude=None)  # django-tables2's own default
    assert _names(bare) == ["id", "first_name", "last_name"]


def test_exclude_kwarg_as_string_still_hides_the_column():
    # django-tables2 accepts `iterable or str`: a bare name must not be iterated character-wise
    table = PlainTable(ROWS, view=_view(None), exclude="first_name")
    assert _names(table) == ["id", "last_name"]


def test_meta_exclude_actions_still_works_as_manual_opt_out():
    class ManualTable(PlainTable):
        class Meta:
            exclude = ("actions",)

    table = ManualTable(ROWS, view=_view(["detail"]))
    assert "actions" not in _names(table)


def test_view_without_cv_list_actions_attribute_keeps_actions_column():
    table = PlainTable(ROWS, view=SimpleNamespace())
    assert _names(table)[-1] == "actions"


@pytest.mark.django_db
def test_author_list_renders_no_actions_header_when_list_actions_is_none(
    client_user_author_view, cv_author, author_douglas_adams, monkeypatch
):
    from tests.lib.helper.boostrap5 import Table as RenderedTable
    from tests.test1.app.views import AuthorListView

    monkeypatch.setattr(AuthorListView, "cv_list_actions", None)
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200
    rendered = RenderedTable(response)
    assert rendered.action_index is None
    assert "Actions" not in [header.text for header in rendered.headers]
