# Design: List-to-Card Key Fallback

## Problem

When a ViewSet has a `CardListView` (key `"card"`) but no `ListView` (key `"list"`), any view that references `"list"` via `cv_success_key`, `cv_cancel_key`, `cv_home_key`, or the default "home" ContextButton raises `ViewSetKeyFoundError`.

Users must manually override these keys on every view in the ViewSet, which is repetitive and error-prone.

## Solution

In `ViewSet.get_view_class()`, before raising `ViewSetKeyFoundError`, if the requested key is `"list"` and `"card"` is registered, return the card view class instead.

## Changes

### 1. `crud_views/lib/viewset/__init__.py`

Modify `get_view_class()` to add the `"list"` → `"card"` fallback before the error raise.

### 2. `tests/test1/test_card.py`

Add tests:
- ViewSet with only CardListView: `get_view_class("list")` returns the card view class
- ViewSet with both ListView and CardListView: `get_view_class("list")` returns the list view class (no fallback)
- ViewSet with neither: `get_view_class("list")` raises `ViewSetKeyFoundError`
- Integration: CreateView in a card-only ViewSet redirects successfully after form submit

### 3. `docs/reference/card-list-view.md`

Document that `"list"` keys automatically fall back to `"card"` when no ListView is registered.

### 4. `skills/django-crud-views/SKILL.md`

Mention the fallback in the CardListView section.

## Behavior

- `"list"` requested, `"list"` registered → returns list view (no change)
- `"list"` requested, `"list"` not registered, `"card"` registered → returns card view (fallback)
- `"list"` requested, neither registered → raises `ViewSetKeyFoundError` (no change)
- Any other key requested → no fallback, existing behavior unchanged
