# View-level context buttons (+ FilterContextButton label) — design

**Date:** 2026-06-24
**Status:** approved (pending user review of this spec)
**Issue:** #27 · **Target release:** v0.8.0 · **Roadmap:** `2026-06-24-audit-followup-roadmap-design.md`

## Goal

Let a `CrudView` declare its own context buttons, instead of only referencing buttons defined
on the shared `ViewSet`. This completes the stubbed `cv_get_context_button` (which today only
consults `ViewSet.context_buttons` and carries the comment
`# view-level context buttons are not supported yet, see issue #27`) and lets a single view
customize or add a button without polluting the whole ViewSet's button list.

Bundled with it: a small `FilterContextButton` polish so its label can be templated like every
other button.

Two parts:

- **Part A — view-level buttons.** New `cv_context_buttons` attribute on `CrudView`; view-level
  definitions override ViewSet-level on key collision.
- **Part B — FilterContextButton label.** Route its label through the shared `_apply_label`
  path so `label_template` / `label_template_code` work.

Out of scope (per scope decision): adding a permission check to `FilterContextButton` — a
filter toggle is not access-controlled (the data behind it is gated by the list view), so a
`cv_has_access` check is YAGNI.

## Current state (for context)

- `CrudView.cv_get_context_button(key)` (`src/crud_views/lib/view/base.py:310`) iterates only
  `self.cv_viewset.context_buttons` and returns the first match or `None`.
- `CrudView.cv_get_context(key, ...)` (`base.py:342`) calls `cv_get_context_button(key)`; if a
  button is found it delegates to `button.get_context(context)`, otherwise it treats the key as
  a sibling view.
- `cv_context_actions: List[str] | None = None` (`base.py:43`) is the per-view list of keys
  that **renders** in the header. Both theme templates
  (`src/crud_views/templates/crud_views/tags/context_actions.html` and the
  `crud_views_plain` copy) iterate `view.cv_context_actions` and emit `{% cv_context_action key %}`
  per key. `cv_get_context_buttons(keys=None)` (`base.py:317`, the custom-loop helper) also
  defaults its keys to `cv_context_actions`.
- `ContextButton` and subclasses live in `src/crud_views/lib/view/buttons.py` and are exported
  from `crud_views.lib.view`. The shared `_apply_label(data, context)` (`buttons.py:34`)
  overrides the seeded default label when a button sets `label_template[_code]`; every button
  subclass calls it in its `get_context` tail — except `FilterContextButton`.
- `FilterContextButton.get_context` (`buttons.py:236`) hardcodes `data["cv_action_label"] = "Filter"`
  and returns without calling `_apply_label`, so its label is not templatable. It uses its own
  template (`tags/context_action_filter.html`) and performs no `cv_has_access` check.

## Design decisions (resolved during brainstorm)

1. **Rendering model: explicit (define-only).** `cv_context_buttons` only *defines* buttons;
   nothing renders until the button's key appears in `cv_context_actions`. This keeps the
   existing definition-vs-rendering separation and means **no template changes**. (The
   alternative — auto-rendering view buttons by appending them to the effective key list — was
   considered and rejected for conflating definition with rendering.)
2. **Precedence: view overrides ViewSet.** `cv_get_context_button` checks the view's list
   first, then falls back to the ViewSet's. A view-level button with the same key as a ViewSet
   button replaces it for that one view.
3. **FilterContextButton:** label templating only; no permission check.

## Design

### Part A — view-level buttons

**New attribute on `CrudView`** (`lib/view/base.py`, near `cv_context_actions` at line 43):

```python
cv_context_buttons: List[ContextButton] | None = None  # view-level context button definitions
```

The `None` default (not `[]`) deliberately mirrors `cv_context_actions` and avoids a shared
mutable class-attribute list — the trap the audit flagged in finding M6.

**Resolution change** in `cv_get_context_button` (`base.py:310`):

```python
def cv_get_context_button(self, key: str) -> ContextButton | None:
    # view-level buttons take precedence over ViewSet-level (issue #27)
    for cb in self.cv_context_buttons or []:
        if cb.key == key:
            return cb
    for cb in self.cv_viewset.context_buttons:
        if cb.key == key:
            return cb
    return None
```

The `# not supported yet` comment is removed.

**Usage:**

```python
class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["update", "delete", "reviews"]   # "reviews" listed → it renders
    cv_context_buttons = [                                  # defines "reviews" for this view only
        ChildContextButton(key="reviews", child_name="review", label_template_code="Reviews"),
    ]
```

Override example: declaring a `cv_context_buttons` entry whose `key` matches an existing
ViewSet button (e.g. `"parent"`) replaces the ViewSet's definition for that view; the key is
already in `cv_context_actions`, so rendering is unchanged.

### Part B — FilterContextButton label

In `FilterContextButton.get_context` (`buttons.py:236`), keep `"Filter"` as the seeded default,
then call the shared label helper before returning:

```python
data["cv_action_label"] = "Filter"          # default when no label_template[_code] is set
data["cv_icon_action"] = crud_views_settings.filter_icon
data["cv_url"] = list_url
self._apply_label(data, context)             # NEW — honor label_template / label_template_code
self._inject_template(data)
return data
```

No `cv_has_access` check is added.

## Rendering pipeline impact

Effectively none. Because rendering still flows through `cv_context_actions`, both theme
templates are untouched and `cv_get_context_buttons` is untouched. The only behavioral change
is the lookup inside `cv_get_context_button` (Part A) and the label line in
`FilterContextButton` (Part B).

## Errors / edges

- A key in `cv_context_actions` that matches no button (view-level or ViewSet-level) resolves
  as a sibling view key, exactly as today — no behavior change.
- `cv_context_buttons = None` (the default) behaves identically to the current code.
- No new Django system check (validation of `cv_context_buttons` keys / duplicate-key handling
  belongs to the #28 "expand system checks" release, not here).

## Exports

No new exports. `cv_context_buttons` reuses the existing `ContextButton` family already
exported from `crud_views.lib.view`.

## Testing (tests/test1)

- A view declaring a `cv_context_buttons` entry **renders** that button when its key is in
  `cv_context_actions`, and does **not** render it when the key is absent (explicit-model
  assertion).
- A view-level button **overrides** a same-key ViewSet button — assert the view's definition
  wins (e.g. a distinguishable label or target).
- Fallback: a view with `cv_context_buttons = None`/unset still resolves ViewSet-level buttons
  unchanged.
- Access filtering still applies: a view-level button whose target denies access is hidden
  (`cv_access` not `True`).
- `FilterContextButton` with `label_template_code` renders the custom label; with no label set
  it still renders `"Filter"`.
- Exercise both bootstrap5 and plain themes where the rendered markup differs.

Reuse existing `tests/test1` models/fixtures (`cv_author`/`cv_book` and the parent-child
chains already present); no new model is required for Part A.

## Documentation, skill & CHANGELOG

- **`docs/reference/context_buttons.md`** — add a "View-level context buttons" section:
  the `cv_context_buttons` attribute, the view-overrides-ViewSet rule, and the requirement to
  list the key in `cv_context_actions` to render. Note `FilterContextButton`'s now-templatable
  label where filter buttons are discussed.
- **`skills/django-crud-views/SKILL.md`** — add a `cv_context_buttons` subsection in the
  context-buttons area (after the `SiblingContextButton` section, ~line 311) showing a
  view-level declaration and the override use-case.
- **`skills/django-crud-views/references/api-reference.md`** — note `cv_context_buttons` in the
  context-button catalog (~line 308).
- **`CHANGELOG.md`** — `Added`: view-level context buttons via `cv_context_buttons`;
  `FilterContextButton` label templating.

## Backwards compatibility

Purely additive. The new attribute defaults to `None` (current behavior); the resolution
change only adds a higher-precedence lookup that is empty by default. The `FilterContextButton`
change preserves the `"Filter"` default and only activates when a label template is set. No
existing views, viewsets, or templates change behavior.
