# Formsets: order-independent validation gate (hardening)

**Date:** 2026-06-26
**Follow-up to:** #55 (parent-required validation). Deferred observation from that PR's final review.
**Target release:** v0.10.2 (fold into the existing unreleased CHANGELOG section)

## Problem

The formset validity gate is sensitive to the order in which formsets are validated. A
child formset's `clean()` may add an error to a **parent** form (the parent-required rule
in `InlineFormSet.clean()` does exactly this via `self.parent_form.add_error(...)`). But by
the time the child's `clean()` runs, the parent formset's validity has already been
collected, so the late error is not counted by the gate.

Trace:

- `cv_form_is_valid()` (`src/crud_views/lib/formsets/mixins.py:69`) calls
  `list(formsets.is_valid())` and tallies the booleans.
- `FormSets.is_valid()` → `XFormSet.is_valid()` (`render_tree.py:193`) yields
  `(parent_formset, parent.is_valid())` **first**, then descends into each form's child
  formsets. The child's `clean()` — where `parent_form.add_error(...)` happens — runs
  *after* the parent's `True` was already collected.
- Net effect: an error added to a parent form by a child's `clean()` does not fail the gate.
  Since `cv_form_valid()` (save) is reached only when the gate returns `True`
  (`src/crud_views/lib/views/mixins.py:35-41`), the submission proceeds to `save()` and can
  crash (e.g. `ValueError: save() prohibited ... unsaved related object`) or mis-save.

Today this is masked because `InlineFormSet.clean()` also raises `ValidationError`, which
fails the **child's own** `is_valid()` (evaluated fresh) and so is caught by the gate. The
`raise` is therefore load-bearing, and the architecture stays fragile for any future
cross-form validation that annotates another form without also raising on itself.

## Decision

Harden the gate so it is **order-independent**: validity is derived from the *complete*
error state of the hierarchy after every `clean()` has run, not from booleans collected mid
traversal. This makes the existing `raise` belt-and-suspenders rather than load-bearing, and
makes cross-form `add_error()` reliably reject a submission.

Scope is the gate only (Option 1 from the brainstorm). We are **not** adding a documented,
first-class cross-form-validation API (Option 2) — there is no use case beyond the
parent-required rule, which the gate hardening covers.

## Core fix: two-phase validity

Django's `BaseFormSet._errors` stores *references* to each form's `ErrorDict`, and
`formset.is_valid()` re-derives its result from the current per-form / non-form error state
on every call (it runs `full_clean` only once, then reads the shared, mutable error state).
So collecting validity a **second** time — after all `clean()`s have run — reflects every
cross-form `add_error()`, without re-running any `clean()` and without DB work.

New method on `FormSets` (`src/crud_views/lib/formsets/formsets.py`), encapsulating the
two-phase rationale in one documented place:

```python
def all_valid(self) -> bool:
    """Return True only if every form and formset in the hierarchy is valid.

    Two-phase, order-independent: a child formset's clean() may add_error() to a
    parent form, and in a single traversal the parent's validity is collected before
    the child's clean() runs. Phase 1 triggers every clean(); phase 2 re-derives
    validity from the now-complete (shared) error state. is_valid() runs full_clean
    only once, so phase 2 re-runs no clean() and does no DB work.
    """
    # Phase 1: trigger every formset's clean() (where cross-form add_error happens).
    # Discard these results — collected in hierarchy order, before later cleans ran.
    list(self.is_valid())
    # Phase 2: re-collect. Reflects errors added to any form during phase 1.
    return all(valid for _, valid in self.is_valid())
```

`cv_form_is_valid()` then replaces its inline single-pass tally with `formsets.all_valid()`:

```python
def cv_form_is_valid(self, context: dict) -> bool:
    form_valid = super().cv_form_is_valid(context)
    formsets = context.get("formsets", None)
    if formsets is None:
        if self.cv_formsets_required:
            raise ValueError("Formsets are required but not defined, cv_formsets_required=True")
        return form_valid
    return form_valid and formsets.all_valid()
```

### Why this is robust, not clever-fragile

Phase 2 delegates to Django's own `formset.is_valid()`, which already skips DELETE-marked
forms and tolerates empty `extra` rows. We inherit correct handling of those cases instead
of hand-rolling an error walk that could over-reject (false positives on legitimately blank
or deleted rows).

## Decisions

- **Keep the `raise` in `InlineFormSet.clean()`.** It becomes redundant (the hardened gate
  now also catches the parent-form error), but it is harmless defense-in-depth and provides
  a clear non-field error path. Not load-bearing anymore.
- **No extra guard in `cv_form_valid()` (save).** The gate is the single source of truth and
  `cv_form_valid()` runs only after `cv_form_is_valid()` returns `True`
  (`views/mixins.py:35-41`). A redundant re-validation before save would double-traverse for
  no gain. Hardening the gate fixes the save path.
- **No change to `FormSets.is_valid()` / `XFormSet.is_valid()` traversal.** Reused as-is by
  both phases; the ordering fix lives entirely in the new `all_valid()`.

## Testing

The decisive test must exercise a cross-form `add_error()` **without** an accompanying
`raise`, since the live `InlineFormSet.clean()` still raises and would otherwise mask the
gate behavior.

1. **Gate catches order-late cross-form error (regression — the core test).**
   Drive the real Publisher → books → notes create flow. Monkeypatch the notes
   `InlineFormSet.clean()` so that, when the child has data under a blank parent, it calls
   `self.parent_form.add_error(None, "<msg>")` **without raising**. POST an orphan payload
   (note filled, parent book blank). Assert: `status_code == 200` (rejected, re-rendered),
   the error message is present, and no `Publisher`/`Book`/`BookNote` rows were created.
   This test **fails on the current single-pass gate** (302/crash) and **passes** with
   `all_valid()`.

2. **No false positives — valid submissions still save.** The existing
   `tests/test1/test_formsets.py` suite (nested create, update, add-via-extra-row, delete a
   book row + its notes, invalid-row re-render) must stay green — confirms the two-phase gate
   does not over-reject, and that DELETE-marked and empty `extra` rows are handled correctly.

3. **Parent-required behavior unchanged.** The `tests/test1/test_formsets_parent_required.py`
   suite must stay green — the feature still works (now via both the `raise` and the gate).

4. **Unit test for `all_valid()` (if feasible without heavy tree construction).** Otherwise
   the integration tests above are sufficient coverage.

## Risk / contingency

The two-phase approach relies on Django's shared-`ErrorDict`-reference behavior and on
`is_valid()` re-deriving from cached error state. This is verified empirically by test (1)
across the CI matrix (Django 4.2 / 5.2 / 6.0, Python 3.12 / 3.13 / 3.14). If any version does
not reflect the mutation on the second pass, the documented fallback is an explicit
hierarchy error-walk in `all_valid()` that checks each non-DELETE form's `errors` plus each
formset's `non_form_errors()` directly — same public method, same call site, more verbose
body.

## Release & docs

- Fold into the **unreleased `0.10.2`** CHANGELOG section (the parent-required entry is
  already there; 0.10.2 is not yet tagged). Add a "Fixed" bullet: the formset validity gate
  is now order-independent, so an error added to a parent form by a child formset's `clean()`
  reliably rejects the submission instead of slipping through to `save()`.
- No public API beyond the new `FormSets.all_valid()` method (documented via its docstring).
- No version bump in this work — release is a separate step.

## Acceptance

- `cv_form_is_valid()` uses `FormSets.all_valid()`; validity no longer depends on traversal
  order.
- A test proves a cross-form `add_error()` without `raise` rejects the submission and saves
  nothing (fails on the old gate, passes on the new one).
- All existing formset and parent-required tests stay green.
- CHANGELOG `0.10.2` updated.
