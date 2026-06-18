# Context Button Access — Unified `cv_button_has_access` Hook (TODO / Approach B)

> Deferred follow-up to the create-access fix shipped via Approach A
> (`superpowers/specs/2026-06-18-context-button-create-access-design.md`).
> Approach A resolves the button's `key_target` inside the Guardian list mixin and
> fully covers list pages. This TODO captures the cleaner, uniform refactor for a
> future iteration.

## Goal

Decide a context button's access in **one place**, regardless of which view renders
it, so the Guardian list-mixin special case can be deleted and access is uniform
across list / detail / sibling / child / parent render paths.

## Sketch

1. **`crud_views/lib/view/base.py`** — add a classmethod hook on `CrudView`:

   ```python
   @classmethod
   def cv_button_has_access(cls, user, rendering_view, obj):
       return cls.cv_has_access(user, obj)
   ```

   Swap the access check in the "key is a view" branch (`base.py:359`) to call it.

2. **`crud_views/lib/view/buttons.py`** — replace `cls.cv_has_access(...)` at the
   **4 button sites** (lines ~53, 110, 146, 191 — `ContextButton`,
   `ParentContextButton`, `ChildContextButton`, `SiblingContextButton`), each
   passing `context.view` as `rendering_view`.

3. **`crud_views_guardian/lib/views.py`** — `GuardianCreateView` overrides
   `cv_button_has_access` to resolve the parent from
   `rendering_view.cv_get_parent_object()` and call `cv_create_has_access(...)`.

4. **`crud_views_guardian/lib/mixins.py`** — delete the `GuardianQuerysetMixin.cv_get_context`
   override entirely (the create-access re-derivation moves into the hook).

## Why this is bigger than it looks (the wrinkles)

- **`cv_action_enabled` is a separate gate.** The deleted mixin override re-derives
  **both** `cv_access` *and* `cv_action_enabled` with the resolved parent object. The
  `cv_button_has_access` hook only covers access. Each button computes
  `cv_action_enabled` independently with `context.object` (= `None` on a list, e.g.
  `buttons.py:50`). So this refactor must **also** introduce a parallel
  `cv_button_action_enabled(user, rendering_view, obj)` hook (or fold both into one
  combined hook) — otherwise the create button's enabled state regresses on list
  pages.

- **Compat shim.** Downstream code overriding `cv_has_access` (5 definitions in-tree,
  plus user subclasses) keeps working because the default hook delegates to
  `cv_has_access`. But `GuardianCreateView` button behavior then lives across both
  `cv_button_has_access` **and** `cv_has_access` "Case 3" — keep them coherent, or
  collapse Case 3 into the hook.

- **Parent-resolution helper.** `cv_get_parent_object()` must be safe to call from an
  arbitrary `rendering_view` that may have no parent / no matching URL kwargs
  (catch `Http404`/`KeyError`, fall back to denied), mirroring the current override.

- **Blast radius.** This touches core button rendering for **all themes and all
  button types**, not just Guardian/create. Regression-test all 4 button types
  across base, Guardian, and plain themes.

## When to pick this up

Only once a **real** non-list, no-object render path needs create-access that
Approach A doesn't cover. Until then, Approach A is sufficient and far lower risk.

## Acceptance

- All Approach A tests still pass unchanged.
- The Guardian list-mixin `cv_get_context` override is gone, with no regression to
  `cv_access` or `cv_action_enabled` on list, detail, sibling, child, or parent
  pages.
- Top-level (no-parent) create access unchanged.
