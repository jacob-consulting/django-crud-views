# Pinned filter (`cv_filter_pinned`) — design

**Date:** 2026-06-17
**Status:** approved (pending user review of this spec)
**Source instruction:** `superpowers/instructions/0002-filter-improvements.md`

## Goal

The UX department wants the list/card filter to be **visible by default** instead of
hidden behind the collapse toggle. Add an opt-in, configurable "pinned" mode: when
enabled, the filter is permanently expanded and the toggle (filter context button) is
hidden. Default behavior is unchanged (filter collapsed, toggle present).

## Behavioral model

`cv_filter_pinned = True` ⇒ **pinned mode**:
- The filter form is always rendered, expanded.
- The filter context button (the `#cv-filter-toggle`) is **hidden** — the user cannot
  collapse the filter.
- Filter **field values** still persist to the session exactly as today (governed by
  `cv_filter_persistence`). The `filter_expanded` session key is irrelevant in this mode
  (there is no toggle to record).

`cv_filter_pinned = False` (default) ⇒ today's behavior: filter collapsed by default,
toggle button present, expanded-state persisted to session.

Applies to **both** `ListView` and `CardListView`, because both obtain filtering from the
same `ListViewTableFilterMixin`.

## Current state (for context)

- `ListViewTableFilterMixin` (`src/crud_views/lib/views/mixins.py`) drives filtering;
  `get_context_data` sets `cv_filter_expanded` from `SessionData(...).get("filter_expanded", False)`.
- `FilterButton` (`src/crud_views/lib/view/buttons.py`, `key="filter"`) renders the toggle
  button via `tags/context_action_filter.html`. It already returns a no-button result
  (`dict(cv_access=False)`) when the view is **not** a `ListViewTableFilterMixin`.
- bootstrap5 `tags/list_filter.html` wraps the filter in
  `<div class="collapse{% if cv_filter_expanded %} show{% endif %}" id="filter-collapse">`.
- plain `tags/list_filter.html` has **no** collapse wrapper — the filter is already always
  visible there.
- `list.filter.js` binds the `#cv-filter-toggle` click handler; when the button is absent
  the handler binds to an empty set (no-op).

## Approach

Reuse the existing button auto-hide path rather than mutating `cv_context_actions`.
`FilterButton.get_context` already hides the button for non-filter views; extend the same
guard to also hide it when the view is pinned. This is theme-agnostic (one Python change
covers bootstrap5 and plain) and leaves the toggle JS untouched.

*Rejected alternative:* auto-stripping `"filter"` from `cv_context_actions` at view
registration — more invasive and duplicates the button's own self-hiding logic.

## Changes

### 1. Setting (`src/crud_views/lib/settings.py`)
Add a Pydantic setting mirroring `filter_persistence`:
```python
filter_pinned: bool = from_settings("CRUD_VIEWS_FILTER_PINNED", default=False)
```

### 2. Mixin (`src/crud_views/lib/views/mixins.py`, `ListViewTableFilterMixin`)
- Add class attribute:
  ```python
  cv_filter_pinned: bool = crud_views_settings.filter_pinned
  ```
- In `get_context_data`, expose the flag and force-expand when pinned:
  ```python
  pinned = self.cv_filter_pinned
  context["cv_filter_pinned"] = pinned
  filter_expanded = True if pinned else SessionData.from_view(self).get("filter_expanded", False)
  context["cv_filter_expanded"] = filter_expanded
  ```
- The `post`/`get` session logic is unchanged. (In pinned mode the toggle never POSTs, so
  `filter_expanded` is never written; field-value persistence in `get` is unaffected.)

### 3. Button hide (`src/crud_views/lib/view/buttons.py`, `FilterButton.get_context`)
After the existing `isinstance(context.view, ListViewTableFilterMixin)` guard, add:
```python
if getattr(context.view, "cv_filter_pinned", False):
    return dict_kwargs  # pinned filter has no toggle button
```
(`dict_kwargs` is the existing `dict(cv_access=False)` no-button result.)

### 4. bootstrap5 template (`src/crud_views/templates/crud_views/tags/list_filter.html`)
When `cv_filter_pinned`, render the filter card **without** the `collapse` wrapper (plain
always-visible card); otherwise keep the existing collapse markup. Sketch:
```django
{% if cv_filter_pinned %}
    <div class="card">
        {# header + body, same inner content as today #}
    </div>
    <br>
{% else %}
    <div class="collapse{% if cv_filter_expanded %} show{% endif %}" id="filter-collapse">
        {# unchanged existing markup #}
    </div>
{% endif %}
```
The inner header/body blocks (`cv_filter_header_icon`, `cv_filter_header`,
`cv_content_filter`, the `#filter-form`) are identical in both branches — factor to avoid
duplication if practical.

### 5. plain template
No change — the plain `list_filter.html` is already always-visible; the shared button-hide
(change 3) removes its now-useless toggle when pinned.

### 6. Documentation (`docs/`)
- `docs/reference/list_view.md` — in "Filtering with django-filter", add a `cv_filter_pinned`
  subsection: always-open + toggle hidden, default `False`, field-value persistence still
  applies.
- `docs/reference/card-list-view.md` — note `cv_filter_pinned` applies to card lists too
  (same mixin).
- `docs/reference/settings.md` — add a `CRUD_VIEWS_FILTER_PINNED` row (`bool`, default
  `False`).

### 7. In-project skill (`skills/django-crud-views/`)
- `references/api-reference.md` — add `cv_filter_pinned = False` near the existing
  `cv_filter_persistence` example; mention it in the Filtering section; update the `filter`
  button description to note it is hidden when the filter is pinned.
- `SKILL.md` — one line in the filter guidance mentioning the pinned option.

## Testing (`tests/test1/`)
New tests (django-filter is already used by existing test views):
- **a)** Pinned `ListView` renders the filter form expanded and emits **no**
  `#cv-filter-toggle` button.
- **b)** Non-pinned `ListView` is unchanged: filter collapsed (no forced `show`), button present.
- **c)** Pinned `CardListView` behaves like (a).
- **d)** `CRUD_VIEWS_FILTER_PINNED=True` flips the default; a per-view `cv_filter_pinned`
  attribute overrides the setting either way.
- **e)** With pinning on, submitting filter values still persists them to the session when
  `cv_filter_persistence` is enabled (field-value persistence unaffected).

Assertions key off response HTML: presence/absence of `id="cv-filter-toggle"` and the
filter form / pinned card. Follow the existing patterns in `tests/test1/test_basic.py` and
`tests/test1/test_card_order.py` (logged-in client fixtures, `client.get(...)`,
`assertContains`/`assertNotContains`).

## Constraints & non-goals
- Default **off** — zero behavior change for existing projects.
- Do not alter the session field-value persistence logic or `cv_filter_persistence`.
- No change to the plain theme's filter template.
- Spec location: `superpowers/specs/` (never under `docs/`).

## Acceptance criteria
- A view with `cv_filter_pinned = True` (or the global setting on) shows the filter open
  and no toggle button, for both ListView and CardListView, in the bootstrap5 theme.
- Non-pinned views are byte-for-byte unchanged in behavior.
- Field-value session persistence still works in pinned mode.
- Docs (3 files) and skill (2 files) document the flag and setting.
- New tests cover (a)–(e) and pass; full suite stays green.
