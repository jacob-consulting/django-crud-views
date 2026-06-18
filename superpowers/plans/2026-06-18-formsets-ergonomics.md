# Formsets Ergonomics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `FormSet.fields`/`pk_field` optional (derived from the formset `klass`) and make `form_show_labels` configurable per `FormSet`.

**Architecture:** Two additive, backward-compatible changes to the formsets subsystem. `FormSet` (a Pydantic model) gains a derivation step in its existing `validate_formset` after-validator and a new `form_show_labels` field; `InlineFormSet.get_helper()` reads that field instead of a hardcoded value. The render/JS layer is untouched.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, Pydantic v2, django-crispy-forms, pytest.

**Spec:** `superpowers/specs/2026-06-18-formsets-ergonomics-design.md`

## Global Constraints

- Line length: 120 characters; double quotes; ruff format + check must pass.
- Backward compatible: every existing `FormSet(...)` declaration must keep working unchanged. Explicit `fields`/`pk_field` override derivation.
- No changes to `render_tree.py`, templates, or `formset.js` — they keep reading `formset.fields` / `formset.pk_field`.
- Out of scope: `parent_form` handling / parent-required validation (split to issue #55).
- Baseline test suite is green: `cd tests && pytest` → 403 passed, 1 skipped.

---

### Task 1: Derive `fields` / `pk_field` from `klass`

**Files:**
- Modify: `src/crud_views/lib/formsets/formsets.py:28-29` (field declarations), `:42-60` (`validate_formset`)
- Modify: `tests/test1/app/views_formset.py:94-111` (drop redundant params — demonstrates + regresses the feature)
- Test: `tests/test1/test_formsets_ergonomics.py` (new)

**Interfaces:**
- Consumes: `FormSet.klass` — a `django.forms.models.BaseInlineFormSet` subclass produced by `inlineformset_factory`, exposing `.form.base_fields` (an ordered dict of editable model field names) and `.model._meta.pk.name`.
- Produces: `FormSet(klass=...)` constructs successfully with `fields` and `pk_field` populated from `klass` when not passed; explicit values still win.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_formsets_ergonomics.py`:

```python
"""
Tests for formsets ergonomics (issue #29):
- FormSet.fields / pk_field are derived from the formset klass when omitted.
- FormSet.form_show_labels is configurable (Task 2).
"""

import pytest

from crud_views.lib.formsets import FormSet
from tests.test1.app.models import Publisher
from tests.test1.app.views_formset import BookFormSet


def test_fields_and_pk_field_derived_from_klass():
    """Omitting fields/pk_field derives them from the inline formset klass."""
    fs = FormSet(title="Books", klass=BookFormSet)
    assert fs.fields == ["title"]
    assert fs.pk_field == "id"


def test_explicit_fields_and_pk_field_override_derivation():
    """Explicit values are kept verbatim and never overwritten by derivation."""
    fs = FormSet(title="Books", klass=BookFormSet, fields=[], pk_field="custom")
    assert fs.fields == []
    assert fs.pk_field == "custom"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_formsets_ergonomics.py -v`
Expected: FAIL — `test_fields_and_pk_field_derived_from_klass` raises a Pydantic `ValidationError` (missing required `fields` / `pk_field`).

- [ ] **Step 3: Make `fields`/`pk_field` optional**

In `src/crud_views/lib/formsets/formsets.py`, change lines 28-29 from:

```python
    fields: List[str]
    pk_field: str
```

to:

```python
    fields: List[str] | None = None
    pk_field: str | None = None
```

- [ ] **Step 4: Derive the values in `validate_formset`**

In the same file, append the derivation to the end of the existing `validate_formset` method (just before `return self`):

```python
    @model_validator(mode="after")
    def validate_formset(self) -> Self:

        from .inline_formset import BaseInlineFormSet
        from crud_views.lib.ordered import get_ordered_model

        if self.klass.can_order:
            ordered_model = get_ordered_model()
            # If django-ordered-model is not installed, skip the subclass check here;
            # crud_views.checks.check_ordered_model_installed reports the missing extra at startup.
            if ordered_model is not None and not issubclass(self.klass.model, ordered_model):
                raise ValidationError(
                    f"FormSet '{self.key}' model not a subclass of OrderedModel but formset.can_order is True"
                )

        if not issubclass(self.klass, BaseInlineFormSet):
            raise ValidationError(f"FormSet '{self.key}' klass not a subclass of BaseInlineFormSet")

        # issue #29: derive fields/pk_field from the klass when not explicitly given
        if self.fields is None:
            self.fields = list(self.klass.form.base_fields.keys())
        if self.pk_field is None:
            self.pk_field = self.klass.model._meta.pk.name

        return self
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_formsets_ergonomics.py -v`
Expected: PASS (both derivation and override tests).

- [ ] **Step 6: Simplify the test-app declaration (regression)**

In `tests/test1/app/views_formset.py`, change the `publisher_formsets` block (lines 94-111) from:

```python
publisher_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        books=FormSet(
            title="Books",
            klass=BookFormSet,
            fields=["title"],
            pk_field="id",
            children=OrderedDict(
                notes=FormSet(
                    title="Notes",
                    klass=BookNoteFormSet,
                    fields=["note"],
                    pk_field="id",
                ),
            ),
        ),
    )
)
```

to:

```python
publisher_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        books=FormSet(
            title="Books",
            klass=BookFormSet,
            children=OrderedDict(
                notes=FormSet(
                    title="Notes",
                    klass=BookNoteFormSet,
                ),
            ),
        ),
    )
)
```

- [ ] **Step 7: Run the formsets regression suite**

Run: `cd tests && pytest test1/test_formsets_bugs.py test1/test_formsets_ergonomics.py -v`
Expected: PASS — the existing nested book/note flow still renders and saves with derived `fields`/`pk_field`.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/formsets/formsets.py tests/test1/app/views_formset.py tests/test1/test_formsets_ergonomics.py
git commit -m "feat(formsets): derive FormSet.fields/pk_field from klass (#29)"
```

---

### Task 2: Configurable `form_show_labels`

**Files:**
- Modify: `src/crud_views/lib/formsets/formsets.py` (add `form_show_labels` field near line 35)
- Modify: `src/crud_views/lib/formsets/inline_formset.py:57` (read the field in `get_helper`)
- Test: `tests/test1/test_formsets_ergonomics.py` (append two tests)

**Interfaces:**
- Consumes: `FormSet.form_show_labels: bool` (default `False`), and `InlineFormSet.formset` (the `FormSet` config bound at construction).
- Produces: `InlineFormSet.get_helper().form_show_labels` equals `self.formset.form_show_labels`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_formsets_ergonomics.py`:

```python
@pytest.mark.django_db
def test_form_show_labels_defaults_false():
    """Default form_show_labels is False, preserving current inline-row behavior."""
    publisher = Publisher.objects.create(name="P")
    fs = FormSet(title="Books", klass=BookFormSet)
    instance = BookFormSet(formset=fs, instance=publisher)
    assert instance.get_helper().form_show_labels is False


@pytest.mark.django_db
def test_form_show_labels_configurable():
    """form_show_labels=True on the FormSet flows through to the crispy helper."""
    publisher = Publisher.objects.create(name="P")
    fs = FormSet(title="Books", klass=BookFormSet, form_show_labels=True)
    instance = BookFormSet(formset=fs, instance=publisher)
    assert instance.get_helper().form_show_labels is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_formsets_ergonomics.py -k form_show_labels -v`
Expected: FAIL — `test_form_show_labels_configurable` fails because `get_helper()` hardcodes `False` (and `FormSet` has no `form_show_labels` field yet, raising `ValidationError` on the `form_show_labels=True` kwarg).

- [ ] **Step 3: Add the `form_show_labels` field to `FormSet`**

In `src/crud_views/lib/formsets/formsets.py`, add the field alongside the other config fields (e.g. immediately after the `pk: PK = PK.INT` line at line 35):

```python
    form_show_labels: bool = False
```

- [ ] **Step 4: Read the field in the inline helper**

In `src/crud_views/lib/formsets/inline_formset.py`, change line 57 from:

```python
        helper.form_show_labels = False
```

to:

```python
        helper.form_show_labels = self.formset.form_show_labels
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_formsets_ergonomics.py -k form_show_labels -v`
Expected: PASS (both default and configurable tests).

- [ ] **Step 6: Run the full suite**

Run: `cd tests && pytest -q`
Expected: PASS — 407 passed, 1 skipped (403 baseline + 4 new tests). The gate is **zero failures**, not a specific number.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/inline_formset.py tests/test1/test_formsets_ergonomics.py
git commit -m "feat(formsets): make FormSet.form_show_labels configurable (#29)"
```

---

### Task 3: Documentation and skill updates

**Files:**
- Modify: `CHANGELOG.md` (add a "Changed" entry under `## Unreleased`)
- Modify: `~/.claude/skills/django-crud-views/SKILL.md:341-345`
- Modify: `~/.claude/skills/django-crud-views/references/api-reference.md:440-444`

**Interfaces:**
- Consumes: the finished behavior from Tasks 1 and 2.
- Produces: documentation reflecting optional `fields`/`pk_field` and the new `form_show_labels`.

- [ ] **Step 1: Add the CHANGELOG entry**

In `CHANGELOG.md`, under `## Unreleased`, add a `### Changed` section (create it if absent, placing it after the existing `### Fixed` block) with:

```markdown
### Changed

- Formsets: `FormSet.fields` and `FormSet.pk_field` are now optional and derived from the formset `klass` (the inline form's fields and the child model's primary-key name) when omitted; pass them explicitly only to override. New `FormSet.form_show_labels` (default `False`) controls crispy label rendering for inline-formset rows instead of the previously hardcoded value.
```

- [ ] **Step 2: Update the SKILL.md formset example**

In `~/.claude/skills/django-crud-views/SKILL.md`, replace the `FormSet(...)` block (lines 341-345):

```python
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            fields=["name", "quantity", "price"],
            pk_field="id",
        )
```

with:

```python
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            # fields and pk_field are derived from klass; pass them only to override.
            # form_show_labels=True,  # show crispy labels on inline rows (default False)
        )
```

- [ ] **Step 3: Update the api-reference.md formset example**

In `~/.claude/skills/django-crud-views/references/api-reference.md`, replace the `FormSet(...)` block (lines 440-445):

```python
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            fields=["name", "quantity", "price"],
            pk_field="id",
            # children={"sub_items": FormSet(...)}  # optional nested formsets
        )
```

with:

```python
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            # fields and pk_field are derived from klass; pass them only to override.
            # form_show_labels=True,  # show crispy labels on inline rows (default False)
            # children={"sub_items": FormSet(...)}  # optional nested formsets
        )
```

- [ ] **Step 4: Verify formatting and lint on the production changes**

Run: `cd /home/alex/projects/alex/django-crud-views && ruff format --check src tests && ruff check src tests`
Expected: "All checks passed!" and no formatting diffs.

- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(formsets): document optional fields/pk_field and form_show_labels (#29)"
```

> The skill files live outside the repo (`~/.claude/skills/...`) and are not part of this git commit; they are edited in place in Steps 2-3.

---

## Self-Review Notes

- **Spec coverage:** Part 1 (derive fields/pk_field) → Task 1. Part 2 (configurable form_show_labels, Scope A) → Task 2. Testing plan items 1-2 → Task 1 Step 1; items 3-4 → Task 2 Step 1; regression item 5 → Task 1 Steps 6-7 + Task 2 Step 6. Docs & skill → Task 3. Part 3 explicitly out of scope (#55).
- **Type consistency:** `fields: List[str] | None`, `pk_field: str | None`, `form_show_labels: bool` are used identically across tasks. `get_helper()` reads `self.formset.form_show_labels`; `FormSet` defines it.
- **Backward compatibility:** the bootstrap5 example apps keep their explicit `fields`/`pk_field` declarations unchanged — they remain valid and now also serve as "explicit override still works" demonstrations.
