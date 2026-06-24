# Bootstrap5 example: view-level context button — design

**Date:** 2026-06-24
**Status:** approved (pending user review of this spec)
**Relates to:** issue #27 (view-level context buttons, shipped on `main`); example demo only.

## Goal

Demonstrate the view-level context button feature (`cv_context_buttons`, from #27) in the
`examples/bootstrap5` project. Add a button that appears on a **single view** of a ViewSet —
contrasting with the example's existing **ViewSet-level** custom buttons.

## Why here (current state)

The `foo → bar/qux → baz` chain in the example is the dedicated context-button demo area, and
it already shows ViewSet-level custom buttons:

- `cv_bar` (`examples/bootstrap5/app/views/bar.py:20-29`) defines
  `context_buttons=context_buttons_default() + [SiblingContextButton(key="quxes", sibling_name="qux", ...)]`.
  `BarListView.cv_context_actions` (`bar.py:54`) lists `"quxes"`, so the **"Quxes"** button shows
  on the bar **list** page — and, being ViewSet-level, is available to every bar view that lists it.
- `cv_qux` mirrors this with a `"bars"` sibling button.

All existing example buttons are ViewSet-level. There is no example of a button scoped to one
view. `Bar` has a child `Baz` (`cv_baz` parent is `bar`, `baz.py:19`), and `BazListView` exists
(key `"list"`), so a bar→baz child link is available.

`BarDetailView` (`bar.py:57-70`) currently sets no `cv_context_actions`, so it inherits the
default `["home", "detail", "update", "delete"]`.

## Design

Single-file change: `examples/bootstrap5/app/views/bar.py`.

1. Extend the existing button import:
   ```python
   from crud_views.lib.view import SiblingContextButton, ChildContextButton
   ```

2. On `BarDetailView`, add a view-level button and list its key so it renders:
   ```python
   class BarDetailView(DetailViewPermissionRequired):
       model = Bar
       cv_viewset = cv_bar
       # View-level button: appears ONLY on this detail view, not on bar's list/update/etc.
       cv_context_buttons = [
           ChildContextButton(key="bazzes", child_name="baz", label_template_code="Bazzes"),
       ]
       cv_context_actions = ["home", "detail", "update", "delete", "bazzes"]
       cv_property_display = [ ... ]  # unchanged
   ```

`cv_context_actions` mirrors the inherited default detail actions
(`["home", "detail", "update", "delete"]`) with `"bazzes"` appended, so the Bar detail page
keeps its existing buttons and gains the new one.

### Behavior demonstrated

- **"Bazzes"** renders only on a Bar's **detail** page, linking to that bar's child `baz`
  collection (`/foo/<foo_pk>/bar/<bar_pk>/baz/`). The current bar object becomes the parent PK
  in the child URL — which is why `ChildContextButton` belongs on an object view.
- It does **not** appear on the Bar **list** page, which shows the ViewSet-level **"Quxes"**
  button instead. Same ViewSet, two buttons at different scopes — the teaching contrast.

### Why `ChildContextButton`

It requires the current object to build the child URL, so it is only meaningful on an object
view (detail) — naturally reinforcing why a button would be scoped to one view. The label is
set via `label_template_code="Bazzes"`. `child_key` defaults to `"list"` (the registered baz
list view).

## Out of scope (non-goals)

- No library/source changes — the `cv_context_buttons` feature already shipped in #27.
- No new model or migration — `bar → baz` already exists.
- No docs or CHANGELOG changes — `docs/reference/context_buttons.md` already documents
  view-level buttons; this is an example-only addition.
- No override demo — this example shows the view-only (additive) case, per the brainstorm
  decision. The override aspect of #27 is intentionally not demonstrated here.

## Testing / verification

- Run the example and navigate foo → bar → a bar's detail page; confirm the **"Bazzes"**
  button appears and links to that bar's `/.../baz/` list.
- Confirm the button is **absent** on the bar list page (which still shows **"Quxes"**).
- The example's existing smoke coverage (`examples/bootstrap5/app/tests.py` and/or the
  `bs5_test` management command) must still render every page without error — guarding against
  a repeat of the #56 unregistered-context-key 500. If the smoke test does not already hit the
  Bar detail page, the implementation should ensure it does (or add a minimal assertion that
  the Bar detail page renders 200 with the "Bazzes" button present).

## Backwards compatibility

Additive and example-only. No change to the library, other example views, or existing Bar
pages beyond the added button on the detail view.
