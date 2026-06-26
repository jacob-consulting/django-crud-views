# Formsets: parent-required validation cleanup (#55)

**Date:** 2026-06-26
**Issue:** [#55](https://github.com/jacob-consulting/django-crud-views/issues/55) (split from #29)
**Target release:** v0.10.2 (patch)

## Problem

`FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:122`) threads a `parent_form`
kwarg into each nested inline formset:

```python
"parent_form": form if level > 0 else None,
```

Its only consumer is `InlineFormSet.clean()` (`src/crud_views/lib/formsets/inline_formset.py:113-119`),
which enforces "a nested child formset with data requires its parent row to be non-empty" — but
with leftover placeholder copy from the original TODO/HACK prototype:

```python
def clean(self):
    super().clean()
    if self.parent_form:
        if self.has_any_form_with_data:
            if self.is_empty_form(self.parent_form):
                self.parent_form.add_error(field=None, error="Child TODO requires at least one TODO set")
                raise ValidationError("Parent form is required")
```

The rule is **always-on, untested, exercised by no example**, and carries placeholder text.

## Decision

This is **not** dead code to delete. The rule protects a real data-integrity invariant: a
grandchild row cannot hold a foreign key to a parent row that was never saved. Keep the rule,
make it real, on by default, and overridable.

The decision of *what counts as a "present" parent* belongs to the **form**, because the form
owns its required/optional field knowledge. The decision of *what to say when a child is
orphaned* belongs to the **formset**, where enforcement lives.

Rejected alternatives:
- *Remove the rule, keep the hook* (#29 brainstorm's lean) — rejected: the invariant is real.
- *Opt-in flag, off by default* — rejected: the constraint is almost always correct, so it
  should hold by default with an escape hatch.
- *Keep always-on, only fix the message* — rejected: leaves the presence decision as an
  un-overridable formset-side heuristic, which is exactly the coupling we want to remove.

## API surface

Two override points, split by ownership of knowledge.

### A. Presence check — on the form

Default lives on `CrispyModelForm` (the base for formset forms):

```python
def cv_is_present(self) -> bool:
    """Does this form represent a real, savable parent row?

    A nested child formset can only attach to a parent that will be saved; if the
    parent row is blank, its children have no foreign key to point at. Override to
    encode custom criteria (e.g. "present when `name` is set"). The default mirrors
    Django's notion of a blank, unchanged extra row.
    """
    return self.has_changed()
```

(The exact default — `has_changed()` vs. the inverse of today's `is_empty_form` heuristic —
is settled in TDD so existing behavior for the blank-extra-row case is preserved.)

### B. Error message — on the InlineFormSet

```python
class InlineFormSet(BaseInlineFormSet):
    cv_parent_required_error = _("Cannot add entries here without filling in the parent.")
```

Translatable, overridable per-formset subclass (users already subclass `InlineFormSet`,
e.g. `BookNoteInlineFormSet`). Replaces the `"Child TODO …"` placeholder.

## Control flow

```python
def clean(self):
    super().clean()
    # Only nested formsets (level > 0) receive a parent_form; top-level formsets
    # attach to the view's object, not to a parent row.
    if self.parent_form and self.has_any_form_with_data and not self._parent_is_present():
        self.parent_form.add_error(None, self.cv_parent_required_error)

def _parent_is_present(self) -> bool:
    hook = getattr(self.parent_form, "cv_is_present", None)
    return hook() if callable(hook) else not self.is_empty_form(self.parent_form)
```

- The error surfaces on the **parent form** as a non-field error (`add_error(None, …)`),
  shown right on the blank parent row. Adding the error invalidates the parent formset, which
  fails the whole submission.
- The redundant `raise ValidationError("Parent form is required")` is **dropped** — `add_error`
  already rejects the submission. (If TDD shows the submission is not actually rejected by
  `add_error` alone, keep a `raise`, but with no placeholder copy.)
- `is_empty_form` stays as the fallback heuristic for parents that are not `CrispyModelForm`.
- The threading in `formsets.py:122` is unchanged except for a clarifying comment on the
  `level > 0` line.

## Testing

Written first (TDD), confirmed RED, then implementation.

### Unit tests (pieces in isolation, no HTTP)

- `cv_is_present()` default — returns `False` for a blank/unchanged form, `True` for a form
  with data.
- `_parent_is_present()` — delegates to the hook when the parent form defines `cv_is_present()`;
  falls back to `is_empty_form` when it does not.
- `cv_parent_required_error` — default is a real translatable string and contains no `"TODO"`
  placeholder copy.

### Integration tests (POST level, against Publisher → books → notes)

The test app's existing nested setup (`tests/test1/app/views_formset.py`:
Publisher → books (Book) → notes (BookNote)) exercises a `level > 0` formset where the rule fires.

1. **Orphan rejected** — POST a `BookNote` (grandchild) with data while its parent `Book` row is
   blank → submission invalid, `cv_parent_required_error` on the parent book form, nothing saved.
2. **Valid nested save** — parent `Book` filled + child `BookNote` filled → saves cleanly.
3. **No false positive** — blank parent row with no grandchild data → no error.
4. **Form override** — a test form overriding `cv_is_present()` changes when the rule fires.
5. **Message override** — subclass sets `cv_parent_required_error` → custom copy surfaces.

Tests live in `tests/test1/test_formsets_bugs.py` (or a focused new file).

## Docs & release

- **Docs:** Formsets have no mkdocs page today; a full formsets guide is out of scope here.
  Scope is thorough docstrings on `cv_is_present()` and `cv_parent_required_error`, plus a
  `CHANGELOG.md` entry under a new `0.10.2` section describing the fixed behavior and the two
  override points. Full formset docs remain a separate concern.
- **Release:** Patch **v0.10.2**. The placeholder rule never worked correctly (untested, TODO
  copy), so making it real reads as a fix, not a breaking change.

## Acceptance

- No placeholder copy (`"Child TODO …"`) remains anywhere.
- The rule is on by default, overridable via `cv_is_present()` (form) and
  `cv_parent_required_error` (formset).
- Behavior is covered by unit and integration tests.
- Behavior is documented in docstrings and `CHANGELOG.md`.
