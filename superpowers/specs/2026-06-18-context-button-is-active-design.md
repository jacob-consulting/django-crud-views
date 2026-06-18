# `cv_is_active` for all context buttons — design

**Date:** 2026-06-18
**Status:** Approved (pending spec review)

## Problem

When rendering a context button, e.g. `{% cv_context_button "notizen" %}`, the
template should be able to tell whether the button points at the page currently
being viewed (to render it as "active"/highlighted).

A var for this already exists — `cv_is_active` — but it is only populated for
the **view-key** branch of `CrudView.cv_get_context()`. Buttons defined as
`ContextButton` (and its subclasses) never receive it, so `{% if cv_is_active %}`
is always falsy for them.

## Current behaviour

- `CrudView.cv_get_context()` (`view/base.py:324`) has two branches:
  - **context-button branch** (`base.py:336-338`): returns
    `context_button.get_context(context)` early — no `cv_is_active`.
  - **view-key branch** (`base.py:341-347`): sets
    `cv_is_active=self.cv_viewset.get_router_name(key) == context.router_name`
    in `dict_kwargs`.
- Every navigational button funnels through the classmethod
  `CrudView.cv_get_dict(cls, context, **extra)` (`base.py:188`):
  - `ContextButton.get_context` (`buttons.py:60`)
  - `ParentContextButton.get_context` (`buttons.py:115`)
  - `ChildContextButton.get_context` (`buttons.py:149`)
  - `SiblingContextButton.get_context` (`buttons.py:194`)
  - the view-key branch (`base.py:365`)
- `cv_is_active` is already consumed by the default template
  `crud_views/tags/context_action.html:3`
  (`{% if cv_is_active %}active{% endif %}`) and documented in `docs/faq.md:32`.
- `ViewContext.router_name` (`view/context.py:35`) returns
  `self.view.request.resolver_match.url_name`.

## Goal

Populate `cv_is_active` for **all** context buttons by computing it once in the
shared funnel `cv_get_dict`, using router-name matching (the semantics the var
already has). No new variable, no template changes for consumers.

Non-goals: new match semantics (exact-URL / prefix were considered and
rejected — router-name is the most accurate); a second `cv_is_current` var
(rejected as duplicate); defensive guarding of `resolver_match` (keep parity
with existing exposure).

## Design

### 1. Compute `cv_is_active` in `cv_get_dict`

In `CrudView.cv_get_dict()` (`view/base.py:188`), set:

```python
data["cv_is_active"] = cls.cv_viewset.get_router_name(cls.cv_key) == context.router_name
```

`cls` is always the **target** view class, so the router name is taken from the
target's own viewset. This is correct for same-viewset buttons (where
`cls.cv_viewset` equals the current viewset) and **more** correct for
cross-viewset buttons (child/sibling/parent), where router names are namespaced
per viewset.

Place the assignment after the base `data = dict(...)` literal and before
`data.update(extra)`, so an explicit `cv_is_active` passed via `extra` (none do
today) would still win — consistent with how `cv_get_dict` already lets `extra`
override.

### 2. Remove the redundant view-key computation

Delete `cv_is_active=self.cv_viewset.get_router_name(key) == context.router_name`
from the view-key branch `dict_kwargs` (`base.py:345`). The funnel now sets it.
For that branch `cls.cv_viewset == self.cv_viewset` and `cls.cv_key == key`, so
the computed value is identical — no behaviour change.

### 3. Deliberate exception: `FilterContextButton`

`FilterContextButton.get_context` (`buttons.py:215`) builds its own `data` dict
and does **not** call `cv_get_dict`, so it will not receive `cv_is_active`. This
is intentional: a filter toggle is not a navigation target. Left as-is.

### 4. Resolver-match exposure

`context.router_name` raises if `request.resolver_match` is `None`. This matches
today's exposure at the removed line 345; real requests always have a
`resolver_match`. No extra guarding (decided).

## Outcome

`{% cv_context_button "notizen" %}` now exposes `cv_is_active`. The default
`context_action.html` already adds the `active` class when it is true, so the
button highlights on its own page with no template change required.

## Tests (`tests/test1/`)

1. A `ContextButton`'s rendered context has `cv_is_active is True` when the
   current request resolves to the button's target view.
2. The same button has `cv_is_active is False` when the current request is a
   different view.
3. (Regression) the view-key branch still yields the correct `cv_is_active`
   after the line-345 removal.

Use the established resolver stub pattern (cf. `test_guardian.py:379`, which
stubs `resolver_match.url_name` for `cv_is_active`).

## Documentation

- `docs/faq.md` — the `cv_is_active` entry: clarify it is populated for **all**
  context buttons (not only view-key buttons).
- `docs/reference/context_buttons.md` — note `cv_is_active` is available in
  button templates for active-state styling, if not already covered.
- `CHANGELOG.md` — Unreleased entry.

## Files touched

| File | Change |
|---|---|
| `src/crud_views/lib/view/base.py` | add `cv_is_active` in `cv_get_dict`; remove redundant line 345 |
| `tests/test1/` | tests for context-button `cv_is_active` true/false + view-key regression |
| `docs/faq.md` | clarify `cv_is_active` applies to all context buttons |
| `docs/reference/context_buttons.md` | mention `cv_is_active` for templates |
| `CHANGELOG.md` | Unreleased entry |
