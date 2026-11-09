# Table Honours `Meta.sequence` and Omits the Actions Column for `cv_list_actions = None` — Implementation Plan

> **Amended 2026-11-09 (Phase 06.19 discussion, issue #337):** the opt-out that omits the actions column is
> `cv_list_actions = None`, not an empty list. An empty list, whether written on a view or inherited from
> `CRUD_VIEWS_LIST_ACTIONS = []`, keeps today's (empty) column. `.planning/phases/06.19-*/06.19-CONTEXT.md` D-10 to D-14
> record the decision; every passage below was updated accordingly.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `crud_views.lib.table.Table` respects a subclass's `Meta.sequence` (appending `actions` last) and omits the
`actions` column when the owning view declares `cv_list_actions = None`.

**Architecture:** Both changes live in `Table.__init__` in `src/crud_views/lib/table/table.py`, which already
receives the owning view as the `view` kwarg and already injects a `sequence` default. The sequence default becomes
conditional on the class's `Meta.sequence`; a new `exclude` merge adds `actions` when the view has no list actions.
Nothing in the views, templates, settings or permission pass changes.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, django-tables2 >= 2.5.3 (2.x and 3.x both supported), pytest with
pytest-django and pytest-xdist.

**Spec:** The approved description is embedded below under [Spec (approved in chat)](#spec-approved-in-chat). It was
agreed in a brainstorming conversation on 2026-11-09 and has no separate design document; this plan is the record.
Origin: finding 26 of `../tabler-test/docs/crud_views_upstream_findings_roastery.md` (the Acme Roasters demo).
Issue: [#337](https://github.com/jacob-consulting/django-crud-views/issues/337).

## Global Constraints

- Line length 120, double quotes, `ruff format` / `ruff check` clean (pre-commit runs `ruff-format`).
- No new queries, no per-request permission work inside table construction. The actions-column decision is static.
- django-tables2 floor stays `>=2.5.3`; use only `Table.__init__` kwargs (`sequence`, `exclude`) and `cls._meta`
  attributes that exist in both 2.x and 3.x (`_meta.sequence`, `_meta.exclude` are tuples/lists, `()` when undeclared).
- Run broad test selections with `pytest -n auto` (user preference); single-test runs may be serial.
- `CHANGELOG.md` entry goes under `## Unreleased` → `### Changed`. No `### Breaking` entry, so `docs/migrating-1.0.md`
  is not touched.
- Changelog and docs cite issue `#337`; "tabler-test finding 26" may be mentioned as the origin.

## Spec (approved in chat)

**Column order.** `Table.__init__` stops unconditionally forcing `sequence=("...", "actions")`. When the caller passes
no `sequence` kwarg:

- If the table class declares a non-empty `Meta.sequence`, that sequence is used; if it does not already contain
  `"actions"`, `"actions"` is appended at the end. (django-tables2 appends `"..."` itself when a sequence has none,
  and a trailing `"actions"` after `"..."` keeps actions last.)
- If the class declares no `Meta.sequence`, the previous default `("...", "actions")` is kept exactly as before, so
  every existing table without a `Meta.sequence` keeps its current column order.
- A caller-supplied `sequence` kwarg wins unchanged, as today.

**Omitted actions column.** When `view.cv_list_actions is None`, the table excludes the `actions` column. The
exclusion is merged with `Meta.exclude` and any caller `exclude` kwarg so neither clobbers the other (django-tables2
does `self.exclude = exclude or self._meta.exclude`, so passing `exclude` alone would drop `Meta.exclude`). An empty
list or tuple keeps the column exactly as today, whether written on a view or inherited from
`CRUD_VIEWS_LIST_ACTIONS = []` (copied onto `ListView.cv_list_actions` at import): a project-wide empty setting must
not remove the column, and `[]` from the setting is indistinguishable from `[]` on a view, so `None` carries the
explicit meaning. Nothing in the package resolves `None` to the setting today (`cv_resolved_actions` iterates
`keys or []`), so `None` and `[]` both already render an empty column and the new meaning changes no existing output
except removing that empty column for `None`. A view stub without the attribute keeps the column.
The decision is static (class attribute of the view), never per user: hiding the column when every action is
inaccessible for the current user would require the permission pass before table construction and is deliberately
out of scope. `Meta.exclude = ("actions",)` remains a valid manual opt-out.

**Bookkeeping.** One `### Changed` changelog entry and a short docs subsection in `docs/reference/list_view.md`.
The column-order change is classified as a behaviour change, not breaking: a `Meta.sequence` that was silently
ignored before now takes effect, which is the order its author wrote.

## Review Focus

1. A `Meta.sequence` with `"..."` in the middle, e.g. `("number", "...", "state")`: `actions` must still land last,
   after `state`. Test added to Task 1.
2. A `Meta.sequence` that already lists `"actions"` (e.g. first): the order is respected as written and `actions` is
   not duplicated. Test added to Task 1.
3. `cv_list_actions = None` on a table whose `Meta.sequence` names `"actions"`: no error, column simply absent
   (django-tables2 filters sequence names that are not bound columns). Test added to Task 2.
4. A table with `Meta.exclude = ("pseudonym",)` under a view with `cv_list_actions = None`: both columns absent. Test
   added to Task 2.
5. `Table` subclasses instantiated outside a crud view (e.g. a formset table or a view stub without
   `cv_list_actions`): construction must not raise `AttributeError`. Test added to Task 2.

---

## File Structure

- Modify: `src/crud_views/lib/table/table.py` — `Table.__init__`, plus two small classmethod helpers
  `cv_default_sequence()` and `cv_exclude_actions(view)` so the two rules are readable and testable on their own.
- Create: `tests/test1/test_table_sequence_actions.py` — unit tests constructing `Table` subclasses directly with a
  stub view, plus one end-to-end test on `/author/`.
- Modify: `docs/reference/list_view.md` — new subsection after "Column Types".
- Modify: `docs/reference/resources.md` — `PublisherFileListView` example: `cv_list_actions = []` → `None`.
- Modify: `CHANGELOG.md` — one `### Changed` entry.

Reference code the implementer will touch (current state, `src/crud_views/lib/table/table.py:23-41`):

```python
class Table(TableWithViewContext):
    actions = ActionColumn(verbose_name=_("Actions"))

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            # as default make sure actions are at the end
            kwargs["sequence"] = ("...", "actions")
        super().__init__(*args, **kwargs)
```

`TableWithViewContext.__init__` (same file, lines 15-20) pops `view` from kwargs and raises `ValueError` when it is
missing, then sets `self.view` after `super().__init__`. The owning list view passes `{"view": self}` from
`ListViewTableMixin.get_table_kwargs()` (`src/crud_views/lib/views/mixins.py:302`). `cv_list_actions` is declared on
`CrudView` (`src/crud_views/lib/view/base.py:100`, default `None`) and set on `ListView` to
`crud_views_settings.list_actions` (`src/crud_views/lib/views/list.py:27`, package default
`["detail", "update", "delete"]`).

---

### Task 1: Honour `Meta.sequence`, appending `actions`

**Files:**
- Modify: `src/crud_views/lib/table/table.py:23-41`
- Create: `tests/test1/test_table_sequence_actions.py`

**Interfaces:**
- Produces: `Table.cv_default_sequence() -> tuple[str, ...]` (classmethod). Returns the `sequence` kwarg to use when
  the caller passes none.
- Produces: the test module's `_view(actions)` stub helper and `_names(table)` helper, reused by Task 2.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_table_sequence_actions.py`:

```python
"""Table column order honours Meta.sequence; the actions column is dropped when the view has no list actions
(tabler-test finding 26)."""

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
```

Note the inherited `actions` column is declared on `Table` before the subclass's own columns, so without a
`Meta.sequence` django-tables2's `"..."` would place it first; the `("...", "actions")` default is what keeps it last.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test1/test_table_sequence_actions.py -v`
Expected: `test_meta_sequence_is_honoured_and_actions_appended`, `test_meta_sequence_with_middle_ellipsis_keeps_actions_last`,
`test_meta_sequence_naming_actions_is_used_as_written` FAIL on column order (actions column misplaced / `id` first);
`test_cv_default_sequence_values` FAILS with `AttributeError: ... has no attribute 'cv_default_sequence'`. The other
two PASS already.

- [ ] **Step 3: Implement `Table.cv_default_sequence()` and use it in `__init__`**

In `src/crud_views/lib/table/table.py`, on `Table`:

```python
    @classmethod
    def cv_default_sequence(cls) -> tuple[str, ...]:
        """The ``sequence`` used when the caller passes none: a declared ``Meta.sequence`` with ``actions`` appended
        unless it names it already, else the historical ``("...", "actions")`` (actions last)."""
        declared = tuple(cls._meta.sequence or ())
        if not declared:
            return ("...", "actions")
        if "actions" in declared:
            return declared
        return (*declared, "actions")

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            kwargs["sequence"] = self.cv_default_sequence()
        super().__init__(*args, **kwargs)
```

`cls._meta.sequence` is django-tables2's `TableOptions.sequence`, `()` when `Meta` declares none. Keep the existing
`order_actions` staticmethod untouched.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test1/test_table_sequence_actions.py -v`
Expected: all 6 PASS.

- [ ] **Step 5: Run the existing table and list suites for regressions**

Run: `pytest tests/test1/test_table_template.py tests/test1/test_basic.py tests/test1/test_filter.py tests/test1/test_ancestor_resolution.py -n auto -q`
Expected: all PASS (no existing test table declares `Meta.sequence`, so orders are unchanged).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/table/table.py tests/test1/test_table_sequence_actions.py
git commit -m "feat(table): honour Meta.sequence and append the actions column last

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Drop the actions column when the view has no list actions

**Files:**
- Modify: `src/crud_views/lib/table/table.py` (the `Table.__init__` from Task 1)
- Modify: `tests/test1/test_table_sequence_actions.py` (append)

**Interfaces:**
- Consumes: `_view()`, `_names()`, `PlainTable`, `SequencedTable`, `ActionsFirstTable` from Task 1's test module.
- Produces: `Table.cv_exclude_actions(view) -> bool` (staticmethod). True only when the view has a
  `cv_list_actions` attribute and it is `None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_table_sequence_actions.py`:

```python
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
```

`tests.lib.helper.boostrap5.Table.action_index` returns the index of the header whose text is `"Actions"`, or `None`.
`monkeypatch` restores the class attribute afterwards; do not mutate `AuthorListView` any other way (the test registry
leaks noted in the project's history came from views defined inline, not from attribute patches).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test1/test_table_sequence_actions.py -v`
Expected: the `None`, merged-exclude, kwarg-exclude, actions-in-sequence and end-to-end tests FAIL because `actions`
is still present; the `[]`, `()`, manual opt-out and missing-attribute tests PASS already; Task 1 tests PASS.

- [ ] **Step 3: Implement `Table.cv_exclude_actions(view)` and the `exclude` merge in `__init__`**

In `src/crud_views/lib/table/table.py`, on `Table`:

```python
    @staticmethod
    def cv_exclude_actions(view) -> bool:
        """True when the owning view declares ``cv_list_actions = None`` (no row actions). An empty list keeps the
        column, as does a view without the attribute. Static: the current user's access is not consulted."""
        return hasattr(view, "cv_list_actions") and view.cv_list_actions is None

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            kwargs["sequence"] = self.cv_default_sequence()
        if self.cv_exclude_actions(kwargs.get("view")):
            # django-tables2 uses `exclude or Meta.exclude`, so merge both sources instead of replacing them
            merged = (*self._meta.exclude, *kwargs.get("exclude", ()), "actions")
            kwargs["exclude"] = tuple(dict.fromkeys(merged))
        super().__init__(*args, **kwargs)
```

`kwargs.get("view")` is read, not popped: `TableWithViewContext.__init__` still pops it and raises when missing.
`dict.fromkeys` deduplicates while preserving order.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test1/test_table_sequence_actions.py -v`
Expected: all 15 PASS.

- [ ] **Step 5: Run lint and the bounded regression selection**

Run: `ruff format src tests && ruff check --fix src tests`
Expected: no changes reported for the new code beyond formatting, no lint errors.

Run: `pytest tests/test1 -n auto -q`
Expected: all PASS. (If the machine is shared, use a bounded `-n 4`.)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/table/table.py tests/test1/test_table_sequence_actions.py
git commit -m "feat(table): drop the actions column when the view has no list actions

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Changelog and docs

**Files:**
- Modify: `CHANGELOG.md` (under `## Unreleased` → `### Changed`, currently starting at line 379; add the entry as the
  first bullet of that section)
- Modify: `docs/reference/list_view.md` (after the "Column Types" table, before the pagination text)

**Interfaces:**
- Consumes: the behaviour from Tasks 1 and 2 exactly as specified; names `Meta.sequence`, `cv_list_actions`,
  `Meta.exclude`.

- [ ] **Step 1: Add the changelog entry**

Insert as the first bullet under `### Changed` in `## Unreleased`:

```markdown
- `Table` now honours a subclass's `Meta.sequence` and appends the `actions` column after it unless the sequence
  names `actions` itself; tables without a `Meta.sequence` keep the previous order (declared columns, then
  `actions`). A list view with `cv_list_actions = None` no longer renders an empty "Actions" column: `actions` is
  excluded, merged with `Meta.exclude`. An empty list keeps the column as before. The decision is static; the
  current user's access is not consulted. `Meta.exclude = ("actions",)` remains a table-side opt-out. A
  `Meta.sequence` that was silently ignored before now takes effect (#337).
```

- [ ] **Step 2: Add the docs subsection**

In `docs/reference/list_view.md`, directly after the "Column Types" table, add:

````markdown
### Column order and the actions column

`Table` adds an `actions` column for the row actions (`cv_list_actions`). Without a `Meta.sequence` the declared
columns come first and `actions` last. Declare `Meta.sequence` to order columns yourself; `actions` is appended
after it unless you place it explicitly:

```python
class AuthorTable(Table):
    last_name = tables.Column()
    first_name = tables.Column()

    class Meta:
        sequence = ("last_name", "...")  # last_name, first_name, actions
```

A list view with `cv_list_actions = None` renders no actions column. An empty list keeps the column. This follows
the view's configuration, not the current user's permissions: a user who can reach none of the configured actions
still sees the (empty) column. To drop the column for other reasons, exclude it on the table:
`Meta.exclude = ("actions",)`.
````

- [ ] **Step 2b: Switch the Resource docs example to `None`**

In `docs/reference/resources.md`, the `PublisherFileListView` example (a read-only file list) sets
`cv_list_actions = []` to mean "no row actions". Change it to `cv_list_actions = None` so the example shows the
column disappearing. Leave test-app views that use `[]` unchanged unless a test asserts on the column.

- [ ] **Step 3: Build the docs to check the page renders**

Run: `.venv/bin/mkdocs build --strict -q 2>&1 | tail -5` (or `task docs` and open the List View page)
Expected: no warnings or errors mentioning `list_view.md`.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md docs/reference/list_view.md docs/reference/resources.md
git commit -m "docs(table): document Meta.sequence handling and the empty actions column

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Verification before completion

- `pytest tests/test1 -n auto -q` passes on the default interpreter.
- `ruff format --check src tests && ruff check src tests` clean.
- Optional broader gate when time allows: `task test` (nox matrix). django-tables2 2.x vs 3.x differences do not
  touch `sequence`/`exclude` handling, so the default session is sufficient evidence for merge.

---

## GSD handoff: decisions and context

All decisions below were made in the brainstorming conversation on 2026-11-09 between the maintainer and Claude.
Items marked **(Claude's call)** were proposed by Claude and approved by the maintainer without change.

### Scope

- **In scope:** tabler-test finding 26 only. Findings 27 (cross-ViewSet link column / success target), 28 (ViewSet
  `verbose_name` override) and 29 (snippet context gets `view`) were explicitly deferred by the maintainer in this
  conversation ("focus only on 26"). Finding 27 additionally depends on the maintainer's 2026-11-04 opt-in URL helper
  decision (`superpowers/notes/2026-11-04-opt-in-url-helper-decision.md`, issue #314), which states destination
  selection across ViewSets stays explicit and that the helper does not close finding 27 by itself.
- **Size:** a small change, approved in chat; no separate design document. This plan is the spec of record.

### Behaviour decisions

1. **`Meta.sequence` is honoured; `actions` appended last unless named.** Replaces the unconditional
   `sequence=("...", "actions")` injection that beat a subclass's `Meta.sequence`.
2. **No `Meta.sequence` → unchanged default `("...", "actions")`.** (Claude's call: preserve proven code paths; every
   existing table without a `Meta.sequence` renders exactly as before, including tables with `Meta.fields` whose
   declared columns currently precede model fields.)
3. **Caller `sequence` kwarg still wins.** Unchanged.
4. **Actions column omitted only for `cv_list_actions = None`.** (Amended 2026-11-09, maintainer's proposal in the
   Phase 06.19 discussion.) An empty list keeps the column whether it comes from a view or from
   `CRUD_VIEWS_LIST_ACTIONS = []`, because a project-wide empty setting must not remove the column and the two are
   indistinguishable on the class. `None` was free to carry the meaning: nothing resolves it to the setting today, so
   `None` and `[]` both rendered an empty column before this change. No system check warns on `[]` (rejected).
5. **Static decision, never per user.** Hiding the column when every configured action is inaccessible to the current
   user is out of scope: it would require the permission pass before table construction, a cross-cutting runtime
   cost the project's maintainability rule (CLAUDE.md "Decision Rule") rejects. (Claude's call, approved.) The docs
   state this limitation explicitly.
6. **`exclude` is merged, not replaced.** django-tables2 evaluates `exclude or Meta.exclude`, so the implementation
   merges `Meta.exclude`, any caller `exclude` kwarg and `"actions"`.
7. **`Meta.exclude = ("actions",)` stays the manual opt-out.** No new attribute or setting is introduced.
8. **Classification: behaviour change, not breaking.** A `Meta.sequence` that was silently ignored now applies; the
   resulting order is the one the author wrote. Hence `### Changed`, no `### Breaking`, no `docs/migrating-1.0.md`
   update. (Claude's call, approved.)

### Implementation decisions (Claude's calls within the approved spec)

- Two small helpers on `Table`, `cv_default_sequence()` (classmethod) and `cv_exclude_actions(view)` (staticmethod),
  keep the two rules independently testable and readable; no new module, mixin or setting.
- `cv_exclude_actions` uses `hasattr` before reading `cv_list_actions`, so `Table` subclasses constructed with a view
  stub or a non-crud view (e.g. formset tables) never raise.
- Tests construct `Table` subclasses directly with a `SimpleNamespace(cv_list_actions=...)` stub (the only view
  attribute read at construction) plus one end-to-end test on `/author/` using `monkeypatch.setattr` on
  `AuthorListView.cv_list_actions`. No new ViewSets or views are registered, avoiding the registry-leak pattern that
  broke PR #336's CI.
- Docs: one subsection in `docs/reference/list_view.md`; the tutorial is not changed.

### Downstream follow-up (not part of this plan)

- `../tabler-test/example/sales/views/orders.py`: `OrderTableBase.__init__`'s sequence workaround can be removed once
  this ships (declare `Meta.sequence = (*columns, "...")` instead), and `AllOrdersTable.Meta.exclude = ("actions",)`
  can be replaced by `cv_list_actions = None` on `AllOrdersListView`. Update the finding's status line in
  `crud_views_upstream_findings_roastery.md`.
- Issue #337 was filed on 2026-11-09 during the Phase 06.19 discussion; the changelog and docs cite it.
