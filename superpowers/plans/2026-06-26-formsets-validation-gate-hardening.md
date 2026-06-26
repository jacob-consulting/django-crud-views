# Formsets Validation Gate Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the formset validity gate order-independent so an error added to a parent form by a child formset's `clean()` reliably rejects the submission instead of slipping through to `save()`.

**Architecture:** Add a two-phase `FormSets.all_valid()` that triggers every formset's `clean()` (phase 1, results discarded) then re-collects validity (phase 2) from the now-complete, shared per-form error state. `cv_form_is_valid()` calls it instead of its single-pass tally. The existing `raise` in `InlineFormSet.clean()` is kept as harmless defense-in-depth but is no longer load-bearing.

**Tech Stack:** Django (4.2/5.2/6.0) model formsets, pytest + pytest-django.

## Global Constraints

- Line length 120; double quotes; ruff format/check must pass.
- Target release: fold into the **unreleased `0.10.2`** CHANGELOG section. No version bump in this work.
- Run tests from `tests/`: `cd tests && pytest`.
- Scope is the gate only (no first-class cross-form-validation API).
- Do NOT modify `FormSets.is_valid()` / `XFormSet.is_valid()` traversal — both phases reuse it as-is.
- Do NOT remove or weaken the `raise ValidationError` in `InlineFormSet.clean()`.
- Do NOT add a re-validation guard inside `cv_form_valid()` (save) — the gate is the single source of truth and `cv_form_valid()` runs only after `cv_form_is_valid()` returns True (`src/crud_views/lib/views/mixins.py:35-41`).
- Test app nesting under test: Publisher → books (Book) → notes (BookNote), in `tests/test1/app/views_formset.py`; `BookNoteInlineFormSet` is the nested (`level > 0`) formset.

---

### Task 1: Order-independent gate via two-phase `all_valid()`

**Files:**
- Modify: `src/crud_views/lib/formsets/formsets.py` (add `all_valid()` to class `FormSets`, immediately after `is_valid()` at lines 306-308)
- Modify: `src/crud_views/lib/formsets/mixins.py` (method `cv_form_is_valid`, lines 69-92)
- Test: `tests/test1/test_formsets_validation_gate.py` (create)

**Interfaces:**
- Consumes: existing `FormSets.is_valid(self) -> Iterable[Tuple[Any, bool]]` (`formsets.py:306`); `InlineFormSet._parent_is_present()`, `InlineFormSet.has_any_form_with_data`, `InlineFormSet.parent_form` (all existing on the nested formset).
- Produces: `FormSets.all_valid(self) -> bool` — True only if every form and formset in the hierarchy is valid, independent of traversal order. Called by `cv_form_is_valid`.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_formsets_validation_gate.py`:

```python
"""
Tests for the order-independent formset validity gate.

A child formset's clean() may add_error() to a PARENT form. The gate must reject the
submission even when the parent form's validity was already collected earlier in the
traversal. This is verified WITHOUT a raise (the live InlineFormSet.clean() also raises,
which would otherwise mask the gate behavior).
"""

import pytest
from django.forms.models import BaseInlineFormSet
from django.test.client import Client

from tests.lib.helper.forms import field_key, form_payload
from tests.test1.app.models import BookNote, Publisher
from tests.test1.app.views_formset import BookNoteInlineFormSet


@pytest.mark.django_db
def test_cross_form_add_error_without_raise_rejects_submission(
    monkeypatch, client_user_publisher_formset: Client, cv_publisher_formset
):
    """A child clean() that add_error()s its parent WITHOUT raising must still reject."""

    def add_error_only(self):
        # Django's base formset clean populates cleaned_data; then annotate the parent
        # WITHOUT raising — exactly the cross-form pattern the hardened gate must catch.
        BaseInlineFormSet.clean(self)
        if self.parent_form and self.has_any_form_with_data and not self._parent_is_present():
            self.parent_form.add_error(None, "boom: parent missing")

    monkeypatch.setattr(BookNoteInlineFormSet, "clean", add_error_only)

    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Ace Books"
    # fill the nested note, leave the parent book row blank -> orphan
    payload[field_key(payload, "-note")] = "orphan"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 200  # rejected, re-rendered (not 302, not a crash)
    assert b"boom: parent missing" in response.content
    assert not Publisher.objects.filter(name="Ace Books").exists()
    assert not BookNote.objects.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_formsets_validation_gate.py -v`
Expected: FAIL on the current single-pass gate. The orphan slips through the gate and reaches `save()`, which raises `ValueError: save() prohibited ... unsaved related object 'book'` (the Django test client re-raises it). Either way the test does NOT pass — confirming the gate leaks cross-form errors.

- [ ] **Step 3: Add `all_valid()` to `FormSets`**

In `src/crud_views/lib/formsets/formsets.py`, immediately after the `is_valid()` method (currently lines 306-308) in class `FormSets`, add:

```python
    def all_valid(self) -> bool:
        """Return True only if every form and formset in the hierarchy is valid.

        Two-phase and order-independent: a child formset's clean() may add_error() to a
        parent form, but in a single traversal the parent's validity is collected before
        the child's clean() runs. Phase 1 triggers every clean(); phase 2 re-derives
        validity from the now-complete (shared) error state. Django's is_valid() runs
        full_clean only once, so phase 2 re-runs no clean() and does no DB work, and it
        delegates to Django's own per-formset validity (which already skips DELETE-marked
        and empty extra forms).
        """
        # Phase 1: trigger every formset's clean() (where cross-form add_error happens).
        # Discard results — collected in hierarchy order, before later cleans ran.
        list(self.is_valid())
        # Phase 2: re-collect; reflects errors added to any form during phase 1.
        return all(valid for _, valid in self.is_valid())
```

- [ ] **Step 4: Wire `cv_form_is_valid` to use it**

In `src/crud_views/lib/formsets/mixins.py`, replace the body of `cv_form_is_valid` (lines 69-92) so the formset tally goes through `all_valid()`. The method becomes:

```python
    def cv_form_is_valid(self, context: dict) -> bool:
        """
        Check if the form is valid.
        Crud Views modules may extend this method with further checks.
        """

        # the main form
        form_valid = super().cv_form_is_valid(context)

        # get the formsets
        formsets = context.get("formsets", None)
        if formsets is None:
            if self.cv_formsets_required:
                raise ValueError("Formsets are required but not defined, cv_formsets_required=True")
            else:
                return form_valid

        # order-independent: a child formset's clean() may add_error() to a parent form,
        # which a single-pass tally would miss. See FormSets.all_valid().
        return form_valid and formsets.all_valid()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_formsets_validation_gate.py -v`
Expected: PASS — the gate now catches the parent-form error, returns False, the view re-renders (200) with "boom: parent missing", and nothing is saved.

- [ ] **Step 6: Run the formset regression suites**

Run: `cd tests && pytest test1/test_formsets.py test1/test_formsets_bugs.py test1/test_formsets_ergonomics.py test1/test_formsets_parent_required.py -v`
Expected: PASS — confirms no false positives (valid nested create/update, add-via-extra-row, delete a book row + its notes, invalid-row re-render all still behave), and the parent-required feature still works.

- [ ] **Step 7: Lint**

Run: `task check && task format`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/mixins.py tests/test1/test_formsets_validation_gate.py
git commit -m "fix(formsets): order-independent validity gate via two-phase all_valid()"
```

---

### Task 2: Changelog entry

**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a "Fixed" bullet in the existing unreleased `0.10.2` section.

- [ ] **Step 1: Add the changelog bullet**

Open `CHANGELOG.md`, find the existing `## 0.10.2` section (added by the parent-required work; it already has `### Fixed` and `### Added` subsections). Add this bullet to the END of the existing `### Fixed` list, matching the surrounding style:

```markdown
- **Formsets:** the validity gate is now order-independent — an error added to a parent
  form by a child formset's `clean()` reliably rejects the submission instead of slipping
  through to `save()`. (follow-up to #55)
```

- [ ] **Step 2: Verify**

Run: `git diff CHANGELOG.md`
Expected: a single new bullet under the existing `0.10.2` → `### Fixed` list; no new version heading, no other changes.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note order-independent formset validity gate"
```

---

## Self-Review

**Spec coverage:**
- Core fix — two-phase `FormSets.all_valid()` → Task 1, Step 3. ✓
- `cv_form_is_valid()` uses `all_valid()` → Task 1, Step 4. ✓
- Keep the `raise` (untouched); no save-side guard; no traversal change → enforced by Global Constraints; Task 1 modifies only `all_valid()` + the gate. ✓
- Decisive test: cross-form `add_error` WITHOUT raise rejects + saves nothing, fails on old gate → Task 1, Steps 1-2 (RED) and 5 (GREEN). ✓
- No false positives / DELETE + empty handling → Task 1, Step 6 (existing suites). ✓
- Parent-required unchanged → Task 1, Step 6 (`test_formsets_parent_required.py`). ✓
- CHANGELOG 0.10.2 updated → Task 2. ✓

**Risk/contingency (from spec):** if a Django version in the CI matrix does not reflect the
mutation on the second pass (Task 1, Step 6 across 4.2/5.2/6.0 would reveal this), the
documented fallback is to replace the `all_valid()` body with an explicit hierarchy
error-walk (check each non-DELETE form's `errors` plus each formset's `non_form_errors()`)
behind the same method signature and call site. Only pursue if a matrix run fails.

**Placeholder scan:** No TBD/TODO/"implement later"; all code shown in full. (The string
`"boom: parent missing"` is an intentional test sentinel, not a placeholder.)

**Type consistency:** `all_valid()` defined in Task 1 Step 3 is the exact name consumed in
Step 4. `is_valid()` reused matches the existing signature. The monkeypatched `clean`
references real members (`_parent_is_present`, `has_any_form_with_data`, `parent_form`).
