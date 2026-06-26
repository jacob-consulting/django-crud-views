# Formsets Parent-Required Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the always-on, untested, placeholder-copy parent-required validation in nested formsets with a real, on-by-default rule that is overridable on the form (presence check) and on the formset (error message).

**Architecture:** Nested inline formsets receive a `parent_form` (threaded in `formsets.py:122` for `level > 0`). `InlineFormSet.clean()` enforces that a grandchild formset with data requires a non-blank parent row. *Whether a parent is "present"* is delegated to the parent form via a new `cv_is_present()` hook (the form owns its field knowledge); *what to say when a child is orphaned* is an overridable `cv_parent_required_error` class attribute on `InlineFormSet`.

**Tech Stack:** Django (4.2/5.2/6.0) model formsets, django-crispy-forms, pytest + pytest-django.

## Global Constraints

- Line length: 120 characters; double quotes; ruff format/check must pass.
- No placeholder copy (`"Child TODO …"`, `"TODO"`) may remain anywhere in shipped code.
- Translatable user-facing strings use `gettext_lazy as _`.
- Target release: **v0.10.2** (patch). Do **not** bump the version in this plan — release is a separate step.
- Tests run from `tests/`: `cd tests && pytest`.
- The rule fires only for nested formsets (`level > 0`); top-level formsets receive `parent_form=None`.
- Test app nesting under test: Publisher → books (Book) → notes (BookNote), defined in `tests/test1/app/views_formset.py`.

---

### Task 1: Add `cv_is_present()` hook to the form base

**Files:**
- Modify: `src/crud_views/lib/crispy/form.py` (class `CrispyModelForm`, line ~82)
- Test: `tests/test1/test_formsets_parent_required.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `CrispyModelForm.cv_is_present(self) -> bool` — returns `True` when the form represents a real, savable row. Default: `self.has_changed()`. Overridable by subclasses.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_formsets_parent_required.py`:

```python
"""
Tests for the parent-required validation in nested formsets (#55).

Unit tests cover the presence hook and the InlineFormSet delegation/message
in isolation; integration tests drive the rule through the real
Publisher -> books -> notes create/update flow.
"""

import pytest

from tests.test1.app.views_formset import BookFormSetForm


@pytest.mark.django_db
def test_cv_is_present_default_false_for_blank_form():
    """An unbound/blank form is not a present parent."""
    form = BookFormSetForm(cv_view=None)
    assert form.cv_is_present() is False


@pytest.mark.django_db
def test_cv_is_present_default_true_for_filled_form():
    """A bound form carrying data is a present parent."""
    form = BookFormSetForm(cv_view=None, data={"title": "Dune"})
    assert form.cv_is_present() is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_formsets_parent_required.py -v`
Expected: FAIL with `AttributeError: 'BookFormSetForm' object has no attribute 'cv_is_present'`

- [ ] **Step 3: Write minimal implementation**

In `src/crud_views/lib/crispy/form.py`, add the method to `CrispyModelForm`:

```python
    def cv_is_present(self) -> bool:
        """Does this form represent a real, savable row?

        Nested child formsets can only attach to a parent that will be saved; if
        the parent row is blank, its children have no foreign key to point at.
        Used by ``InlineFormSet.clean()`` to enforce parent-presence. Override to
        encode custom criteria (e.g. "present when ``name`` is set"). The default
        mirrors Django's notion of a blank, unchanged extra row.
        """
        return self.has_changed()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_formsets_parent_required.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/crispy/form.py tests/test1/test_formsets_parent_required.py
git commit -m "feat(formsets): add cv_is_present() presence hook to CrispyModelForm (#55)"
```

---

### Task 2: Rewrite `InlineFormSet.clean()` with overridable message + delegation

**Files:**
- Modify: `src/crud_views/lib/formsets/inline_formset.py` (imports; class `InlineFormSet`; method `clean`, lines 113-119)
- Modify: `src/crud_views/lib/formsets/formsets.py:122` (clarifying comment only)
- Test: `tests/test1/test_formsets_parent_required.py` (append)

**Interfaces:**
- Consumes: `parent_form.cv_is_present()` from Task 1 (when present); `InlineFormSet.is_empty_form(form) -> bool` (existing) as fallback.
- Produces:
  - `InlineFormSet.cv_parent_required_error` — class attribute, translatable string, overridable per subclass.
  - `InlineFormSet._parent_is_present(self) -> bool` — `True` if the parent form is present; delegates to `self.parent_form.cv_is_present()` when defined, else `not self.is_empty_form(self.parent_form)`.
  - `InlineFormSet.clean()` — adds `self.cv_parent_required_error` as a non-field error to `self.parent_form` when a nested formset has data but the parent is not present.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_formsets_parent_required.py`:

```python
from tests.test1.app.views_formset import BookNoteInlineFormSet


class _PresentStub:
    def cv_is_present(self):
        return True


class _AbsentStub:
    def cv_is_present(self):
        return False


class _NoHookEmptyStub:
    """A parent form without the hook that looks like a blank extra row."""

    cleaned_data = {}

    def is_valid(self):
        return True


def _bare_inline_formset(parent_form):
    """Build an InlineFormSet without Django's heavy __init__ to test pure logic."""
    fs = object.__new__(BookNoteInlineFormSet)
    fs.parent_form = parent_form
    return fs


def test_parent_is_present_delegates_to_hook_true():
    fs = _bare_inline_formset(_PresentStub())
    assert fs._parent_is_present() is True


def test_parent_is_present_delegates_to_hook_false():
    fs = _bare_inline_formset(_AbsentStub())
    assert fs._parent_is_present() is False


def test_parent_is_present_falls_back_to_is_empty_form():
    """A parent form without cv_is_present falls back to the is_empty_form heuristic."""
    fs = _bare_inline_formset(_NoHookEmptyStub())
    assert fs._parent_is_present() is False  # empty form -> not present


def test_parent_required_error_has_no_placeholder_copy():
    msg = str(BookNoteInlineFormSet.cv_parent_required_error)
    assert "TODO" not in msg
    assert msg  # non-empty
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_formsets_parent_required.py -v`
Expected: FAIL — `AttributeError: 'BookNoteInlineFormSet' object has no attribute '_parent_is_present'` and `cv_parent_required_error`.

- [ ] **Step 3: Write the implementation**

In `src/crud_views/lib/formsets/inline_formset.py`:

Replace the import block (lines 5-10) — drop the now-unused `ValidationError`, add the translation helper:

```python
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, LayoutObject, Field, BaseInput
from crud_views.lib.crispy import Column4, Column2
from django.forms import BaseForm
from django.forms.models import BaseInlineFormSet, ModelForm
from django.utils.translation import gettext_lazy as _
```

Add the class attribute just inside `class InlineFormSet(BaseInlineFormSet):` (before `__init__`):

```python
class InlineFormSet(BaseInlineFormSet):
    # Shown on a blank parent row when a nested child formset has data but the
    # parent it would attach to is not present. Override per subclass to customise.
    cv_parent_required_error = _("Cannot add entries here without filling in the parent.")
```

Replace `clean()` (current lines 113-119) with:

```python
    def clean(self):
        super().clean()
        # Only nested formsets (level > 0) receive a parent_form; top-level
        # formsets attach to the view's object, not to a parent row. A grandchild
        # row with data needs a saved parent to hold its foreign key.
        if self.parent_form and self.has_any_form_with_data and not self._parent_is_present():
            self.parent_form.add_error(None, self.cv_parent_required_error)

    def _parent_is_present(self) -> bool:
        hook = getattr(self.parent_form, "cv_is_present", None)
        return hook() if callable(hook) else not self.is_empty_form(self.parent_form)
```

In `src/crud_views/lib/formsets/formsets.py`, add a clarifying comment on line 122. The kwargs dict becomes:

```python
            kwargs = {
                "formset": self,
                "instance": form.instance,
                "prefix": prefix,
                # nested formsets (level > 0) carry their parent row's form so
                # InlineFormSet.clean() can enforce parent-presence; top-level
                # formsets attach to the view object and get None.
                "parent_form": form if level > 0 else None,
            }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_formsets_parent_required.py -v`
Expected: PASS (all unit tests green)

- [ ] **Step 5: Run the full formsets suite to check for regressions**

Run: `cd tests && pytest test1/test_formsets.py test1/test_formsets_bugs.py test1/test_formsets_ergonomics.py -v`
Expected: PASS (no regressions)

- [ ] **Step 6: Lint**

Run: `task check && task format`
Expected: no errors; `ValidationError` no longer reported as unused (it was removed).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/formsets/inline_formset.py src/crud_views/lib/formsets/formsets.py tests/test1/test_formsets_parent_required.py
git commit -m "fix(formsets): real, overridable parent-required validation; drop placeholder copy (#55)"
```

---

### Task 3: Integration tests through the real create/update flow

**Files:**
- Test: `tests/test1/test_formsets_parent_required.py` (append)

**Interfaces:**
- Consumes: the rewritten `InlineFormSet.clean()` (Task 2) and `cv_is_present()` (Task 1), exercised end-to-end via the `client_user_publisher_formset` fixture and `form_payload`/`field_key` helpers.
- Produces: nothing (verification only).

- [ ] **Step 1: Write the integration tests**

Append to `tests/test1/test_formsets_parent_required.py`:

```python
from django.test.client import Client

from tests.lib.helper.forms import field_key, form_payload
from tests.test1.app.models import Book, BookNote, Publisher


@pytest.mark.django_db
def test_orphan_note_on_blank_book_is_rejected(
    client_user_publisher_formset: Client, cv_publisher_formset
):
    """A note (grandchild) with data under a blank book row must be rejected."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Ace Books"
    # fill the nested note but leave the parent book row blank -> orphan
    payload[field_key(payload, "-note")] = "orphan note"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 200  # re-rendered, not redirected
    assert b"Cannot add entries here" in response.content
    assert not Publisher.objects.filter(name="Ace Books").exists()
    assert not BookNote.objects.exists()


@pytest.mark.django_db
def test_filled_book_with_note_saves(
    client_user_publisher_formset: Client, cv_publisher_formset
):
    """A present parent book with a child note saves cleanly."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Tor"
    payload[field_key(payload, "-title")] = "Mistborn"
    payload[field_key(payload, "-note")] = "fantasy"

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 302
    book = Book.objects.get(title="Mistborn")
    assert BookNote.objects.filter(book=book, note="fantasy").exists()


@pytest.mark.django_db
def test_all_blank_rows_no_false_positive(
    client_user_publisher_formset: Client, cv_publisher_formset
):
    """Blank parent row with no grandchild data must not trigger the rule."""
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    payload = form_payload(response)
    payload["name"] = "Empty House"
    # leave both the book row and the note row blank

    response = client_user_publisher_formset.post("/publisher-formset/create/", payload)

    assert response.status_code == 302
    publisher = Publisher.objects.get(name="Empty House")
    assert publisher.books.count() == 0
```

- [ ] **Step 2: Run the integration tests**

Run: `cd tests && pytest test1/test_formsets_parent_required.py -v`
Expected: PASS (all unit + integration tests green)

- [ ] **Step 3: Run the full test suite**

Run: `cd tests && pytest`
Expected: PASS (no regressions across the suite)

- [ ] **Step 4: Commit**

```bash
git add tests/test1/test_formsets_parent_required.py
git commit -m "test(formsets): integration coverage for parent-required validation (#55)"
```

---

### Task 4: Changelog entry

**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a `0.10.2` section documenting the fixed behavior and the two override points.

- [ ] **Step 1: Add the changelog section**

Open `CHANGELOG.md` and add a new section above the existing `0.10.1` entry, matching the file's existing heading/date style (use the current date for the entry):

```markdown
## 0.10.2

### Fixed
- **Formsets:** the parent-required validation for nested formsets is now a real,
  tested rule instead of an always-on placeholder. A grandchild formset with data
  is rejected when its parent row is blank (its foreign key would have nothing to
  point at). Removed the leftover `"Child TODO …"` placeholder message. (#55)

### Added
- **Formsets:** two override points for parent-presence validation:
  - `CrispyModelForm.cv_is_present()` — override on a form to define when it counts
    as a present, savable parent row (defaults to `has_changed()`).
  - `InlineFormSet.cv_parent_required_error` — override the message shown on the
    blank parent row.
```

- [ ] **Step 2: Verify formatting**

Run: `git diff CHANGELOG.md`
Expected: the new `0.10.2` section sits directly above `0.10.1` and matches surrounding style.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): add 0.10.2 formsets parent-required entry (#55)"
```

---

## Self-Review

**Spec coverage:**
- Decision (keep rule, on by default, overridable) → Tasks 1-2. ✓
- API: `cv_is_present()` on the form → Task 1. ✓
- API: `cv_parent_required_error` on the formset → Task 2. ✓
- Control flow (delegation, error on parent form, drop redundant `raise`, `is_empty_form` fallback, comment on `formsets.py:122`) → Task 2. ✓
- Unit tests (default presence, delegation, fallback, message-no-placeholder) → Tasks 1-2. ✓
- Integration tests (orphan rejected, valid nested save, no false positive) → Task 3. ✓
- Docs (docstrings + CHANGELOG 0.10.2) → Tasks 1-2 (docstrings), Task 4 (changelog). ✓
- Acceptance: no placeholder copy remains (verified by `test_parent_required_error_has_no_placeholder_copy` + import removal). ✓

**Note on spec scenario 4 (form override) and scenario 5 (message override):** these are covered at the unit level — `test_parent_is_present_delegates_to_hook_*` proves the `cv_is_present()` override path drives the rule, and `test_parent_required_error_has_no_placeholder_copy` plus the overridable class attribute prove message customization — rather than wiring a second viewset/URL just to exercise overrides through HTTP.

**Placeholder scan:** No TBD/TODO/"implement later" in plan steps; all code shown in full. ✓

**Type consistency:** `cv_is_present` (Task 1) is the exact name consumed by `_parent_is_present` (Task 2). `cv_parent_required_error` used consistently across Tasks 2 and 4. `is_empty_form` matches the existing method. ✓

**Open implementation detail from spec:** the spec flagged that `add_error` alone may not reject the submission. The plan's `test_orphan_note_on_blank_book_is_rejected` asserts `status_code == 200` and nothing saved — if that fails, add a `raise ValidationError(self.cv_parent_required_error)` (no placeholder) at the end of the `clean()` branch and re-run; otherwise leave `clean()` as written.
