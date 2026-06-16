# CardView: ordering, direction, filter, paging & persistence

**Date:** 2026-06-16
**Status:** Approved (design)
**Scope:** `crud_views` core + `crud_views_guardian`, bootstrap5 example app, docs, inline skill, tests.

## Problem

`CardListView` (`src/crud_views/lib/views/card.py`) is a thin `generic.ListView` that
renders objects as Bootstrap cards. Unlike `ListView` — which gets sorting and
pagination from django-tables2 (`ListViewTableMixin`) and filtering from django-filter
(`ListViewTableFilterMixin`) — the card view has:

- no ordering UI (cards have no clickable column headers like a table),
- no pagination controls,
- filtering only when `ListViewTableFilterMixin` is mixed in manually.

We want the card view to offer ordering, a direction toggle, filtering, and paging
that are equivalent to the list view, without the three features clobbering each
other's query parameters, and with optional session persistence.

## Goals

1. An **order-by combo** listing orderable fields declared via `cv_order_fields`.
2. A **direction selector** (up/down → asc/desc) for the chosen field.
3. **Filtering** analogous to `ListView` (django-filter), reusing `ListViewTableFilterMixin`.
4. **Paging** analogous to `ListView` (Django's `paginate_by`).
5. Filter and order **never override each other** in the URL/query string.
6. **Optional persistence** of order + filter in the session, as `ListView` already does.

## Non-goals (YAGNI)

- Multi-field ordering (single field + direction only).
- A separate persistence flag for ordering — order/dir ride in the same query string
  as the filter and are covered by the existing `cv_filter_persistence`.
- Reworking how `ListView`/django-tables2 does its own sorting (`sort` param) or paging.

## Design decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Order model | `cv_order_fields` = list of field names or `(name, label)` tuples; combo picks one field; separate up/down toggle picks direction. URL: `?order=price&dir=desc` → `qs.order_by("-price")`. |
| Persistence | Reuse the existing query-string persistence (`cv_filter_persistence`). One flag covers filter + order. Extend the reset logic to preserve `order`/`dir`. |
| Packaging | Reusable `CardOrderMixin` for ordering; `paginate_by` (Django-native) on `CardListView`; filtering stays the opt-in `ListViewTableFilterMixin`. |
| Order UI placement | Always-visible toolbar above the card grid (independent of the collapsible filter card). |

## Architecture

```python
class BookCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_order_fields = ["title", ("price", "Price")]   # str or (name, label)
    cv_order_default = "-created"                       # optional, leading "-" = desc
    paginate_by = 12
    filterset_class = BookFilter
    formhelper_class = BookFilterFormHelper
    cv_card_actions = [...]
```

`CardListView` inherits `CardOrderMixin`, so cards get ordering + paging out of the
box. The toolbar renders only when `cv_order_fields` is non-empty, and `paginate_by`
defaults to `None` — so existing card views are unaffected (backward compatible).

### Component 1 — `CardOrderMixin` (`src/crud_views/lib/views/mixins.py`)

Class attributes:

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `cv_order_fields` | `list[str \| tuple[str, str]]` | `[]` | Orderable fields. String ⇒ label from the model field's `verbose_name`; tuple ⇒ `(field_name, explicit_label)`. |
| `cv_order_default` | `str \| None` | `None` | Fallback ordering when no `order` GET param (e.g. `"-created"`; leading `-` = desc). |
| `cv_order_param` | `str` | `"order"` | GET param name for the field (configurable to avoid collision with a model field literally named `order`, e.g. ordered-model). |
| `cv_order_dir_param` | `str` | `"dir"` | GET param name for the direction (`asc`/`desc`). |

Behavior:

- `cv_get_order_choices()` → normalized list of `{name, label, selected}` for the combo.
- `cv_get_order()` → resolves `(field, direction)` from `request.GET`, **whitelisted
  against the names in `cv_order_fields`**. Invalid/absent `order` falls back to
  `cv_order_default`. Direction restricted to `asc`/`desc` (default `asc`). The
  whitelist prevents arbitrary `order_by()` injection from the query string.
- `get_queryset()` → `super().get_queryset()`, then `.order_by("[-]field")` when a
  valid field resolves; otherwise unchanged (model `Meta.ordering` applies).
- `get_context_data()` → adds:
  - `cv_order_choices` (normalized list, with `selected`),
  - `cv_order_current` (resolved field name or `""`),
  - `cv_order_dir` (`"asc"`/`"desc"`),
  - `cv_order_querystring` — all *other* current GET params (filter values), with
    `order`, `dir`, and `page` removed — for the toolbar's hidden inputs.

### Component 2 — Paging on `CardListView`

- Uses Django's native `paginate_by` (same attribute `ListViewTableMixin` uses; not
  `cv_`-prefixed because it is a Django-inherited attribute, like `template_name`).
  Default `None` (no paging).
- New `crud_views/templates/crud_views/snippets/pagination.html` (Bootstrap5) renders
  `page_obj` / `paginator` when `is_paginated`.
- New inclusion tag `{% cv_pagination %}` in `templatetags/crud_views.py` builds page
  links preserving the **full query string except `page`**, so filter + order survive
  page navigation.

### Component 3 — Order toolbar template

`crud_views/templates/crud_views/snippets/card_order.html`, rendered at the top of
`view_card.content.html`, guarded by `view.cv_order_fields`:

- `<form method="get">` containing:
  - `<select name="{{ cv_order_param }}" onchange="this.form.submit()">` over `cv_order_choices`,
  - a Bootstrap `btn-group` of two submit buttons (`name="{{ cv_order_dir_param }}"`,
    `value="asc"`/`"desc"`, fa up/down icons), the active direction highlighted,
  - hidden `<input>`s for every preserved filter param (from `cv_order_querystring`).
- `page` is intentionally omitted so changing sort resets to page 1.

Layout:

```
[ Order by: Price ▾ ]  [ ↑ ↓ ]
----------------------------------
| card |  | card |  | card |
| card |  | card |  | card |
----------------------------------
        « 1 2 3 »
```

### Component 4 — Filter ⇄ order coexistence

Three coordinated points ensure neither feature drops the other's params:

1. **Toolbar form** carries current filter params as hidden inputs (`cv_order_querystring`)
   → applying order keeps the active filter.
2. **`ListViewFilterFormHelper`** (`src/crud_views/lib/views/list.py`) — extended to add
   hidden `order` + `dir` inputs when present in `request.GET`, alongside the existing
   hidden `sort`. Harmless for `ListView` (values empty/absent there) → applying the
   filter keeps the active order.
3. **Persistence reset** (`ListViewTableFilterMixin.get()`) — the `reset_filter` branch
   currently rebuilds the URL preserving only `sort`; extend it to also preserve
   `order` + `dir`.

Because order/dir are part of the same query string that `ListViewTableFilterMixin`
already stores in the session (keyed by `cv_session_key_querystring`), the existing
`cv_filter_persistence` flag remembers order + filter together. No new flag.

## Templates touched / added

| File | Change |
|---|---|
| `crud_views/templates/crud_views/view_card.content.html` | Render order toolbar (top) + pagination (bottom). |
| `crud_views/templates/crud_views/snippets/card_order.html` | New — order combo + direction toggle. |
| `crud_views/templates/crud_views/snippets/pagination.html` | New — Bootstrap5 pagination nav. |
| `crud_views/templatetags/crud_views.py` | New `{% cv_pagination %}` inclusion tag. |

## Example app (bootstrap5)

- `examples/bootstrap5/app/views/book.py`: add `cv_order_fields = ["title", ("price", "Price")]`,
  `cv_order_default`, and `paginate_by` to `BookCardListView` (it already has the filter).
- Ensure enough seed `Book` rows exist (fixtures/management command) to demonstrate paging.

## Documentation

`docs/reference/card-list-view.md`: add sections

- **Ordering** — `cv_order_fields` formats, `cv_order_default`, the combo + direction toggle.
- **Paging** — `paginate_by`, pagination nav.
- **Coexistence & persistence** — filter and order never clobber each other; persistence
  via `cv_filter_persistence`.

## Inline skill

`skills/django-crud-views/SKILL.md` and `skills/django-crud-views/references/api-reference.md`:
document `cv_order_fields`, `cv_order_default`, `cv_order_param`/`cv_order_dir_param`,
`paginate_by`, and `CardOrderMixin` for card views.

## Tests (`tests/test1/`)

Add `cv_order_fields` + `paginate_by` (+ filter) to a card view in the test app
(isolated so existing card assertions stay green). New tests:

1. `order=title&dir=asc` orders ascending; `dir=desc` orders descending.
2. Invalid `order=<not in cv_order_fields>` is ignored (whitelist) → default/Meta ordering.
3. `cv_order_default` applied when no `order` param.
4. `paginate_by` limits cards per page; pagination nav renders when `is_paginated`.
5. Page links preserve filter + order params (no `page` duplication).
6. Applying a filter preserves the active `order`/`dir` (hidden fields in filter form).
7. Applying order preserves active filter params (hidden fields in toolbar form).
8. `reset_filter=true` preserves `order`/`dir`.
9. Toolbar is absent when `cv_order_fields` is empty (backward compatibility).

Run via `cd tests && pytest test1/test_card.py` and the guardian variant
`test1/test_guardian_card.py`; full suite via `task test`.

## Backward compatibility

- `cv_order_fields = []` and `paginate_by = None` by default → no toolbar, no paging,
  unchanged output for existing card views.
- `ListViewFilterFormHelper` changes only add hidden inputs when the params are present,
  so `ListView` behavior is unchanged.
