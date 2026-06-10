# Optional `ordered` Dependency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `django-ordered-model` (the `ordered` extra) genuinely optional by removing its only top-level import from the core `crud_views` app and reporting a missing install via a Django system check instead of a crash.

**Architecture:** Introduce one shared lazy-import helper, `get_ordered_model()`, returning the `OrderedModel` class or `None`. `formsets.py` and `action_ordered.py` use it to skip their `issubclass` checks when the package is absent (instead of importing at module top level). A new registered system check, `check_ordered_model_installed`, walks the `ViewSet` registry and emits an `Error` when an ordered view or `can_order` formset exists but the package cannot be imported.

**Tech Stack:** Django system checks framework, Pydantic v2 validators, pytest.

---

## File Structure

- **Create** `crud_views/lib/ordered.py` — the single `get_ordered_model()` helper. One responsibility: lazily resolve the optional `OrderedModel` class.
- **Modify** `crud_views/lib/formsets/formsets.py` — remove top-level `ordered_model` import; use the helper in `validate_formset`.
- **Modify** `crud_views/lib/views/action_ordered.py` — use the helper in `OrderedCheckBase.__init__`; remove the `# todo: move to system checks` note.
- **Modify** `crud_views/checks.py` — add `check_ordered_model_installed`.
- **Create** `tests/test1/test_optional_ordered.py` — tests for the helper, import safety, and the system check.

---

## Task 1: Lazy-import helper `get_ordered_model()`

**Files:**
- Create: `crud_views/lib/ordered.py`
- Test: `tests/test1/test_optional_ordered.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_optional_ordered.py`:

```python
import sys

import pytest

from crud_views.lib import ordered


def test_get_ordered_model_returns_class_when_installed():
    """When django-ordered-model is installed, the helper returns the class."""
    from ordered_model.models import OrderedModel

    assert ordered.get_ordered_model() is OrderedModel


def test_get_ordered_model_returns_none_when_absent(monkeypatch):
    """When ordered_model cannot be imported, the helper returns None instead of raising."""
    # Hide ordered_model and its submodule from the import system.
    monkeypatch.setitem(sys.modules, "ordered_model", None)
    monkeypatch.setitem(sys.modules, "ordered_model.models", None)

    assert ordered.get_ordered_model() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_optional_ordered.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crud_views.lib.ordered'`

- [ ] **Step 3: Write minimal implementation**

Create `crud_views/lib/ordered.py`:

```python
"""Lazy access to the optional django-ordered-model dependency.

`django-ordered-model` is an optional extra (`crud_views[ordered]`). Core code
must never import it at module top level, or the extra stops being optional.
Use this helper to resolve the class on demand.
"""

from __future__ import annotations

from typing import Type


def get_ordered_model() -> Type | None:
    """Return the ``OrderedModel`` class, or ``None`` if the package is absent.

    Setting ``sys.modules['ordered_model'] = None`` (as tests do to simulate a
    missing install) makes the import raise ``ImportError``, which we treat the
    same as the package not being installed.
    """
    try:
        from ordered_model.models import OrderedModel
    except ImportError:
        return None
    return OrderedModel
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_optional_ordered.py -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add crud_views/lib/ordered.py tests/test1/test_optional_ordered.py
git commit -m "feat: add get_ordered_model lazy-import helper for optional ordered extra"
```

---

## Task 2: Remove the top-level import from `formsets.py`

**Files:**
- Modify: `crud_views/lib/formsets/formsets.py` (remove line 14; edit `validate_formset`)
- Test: `tests/test1/test_optional_ordered.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_optional_ordered.py`:

```python
import importlib


def test_formsets_module_imports_without_ordered_model(monkeypatch):
    """crud_views.lib.formsets.formsets must import cleanly when ordered_model is absent."""
    monkeypatch.setitem(sys.modules, "ordered_model", None)
    monkeypatch.setitem(sys.modules, "ordered_model.models", None)

    import crud_views.lib.formsets.formsets as formsets_mod

    # Reload under the hidden-package condition; must not raise ImportError.
    reloaded = importlib.reload(formsets_mod)
    assert hasattr(reloaded, "FormSet")

    # Restore a clean module state for other tests.
    monkeypatch.undo()
    importlib.reload(reloaded)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_optional_ordered.py::test_formsets_module_imports_without_ordered_model -v`
Expected: FAIL — `ImportError` raised from the top-level `from ordered_model.models import OrderedModel` during reload.

- [ ] **Step 3: Write minimal implementation**

In `crud_views/lib/formsets/formsets.py`, delete the top-level import on line 14:

```python
from ordered_model.models import OrderedModel
```

Then change `validate_formset` (currently lines 43-57) from:

```python
    @model_validator(mode="after")
    def validate_formset(self) -> Self:

        from .inline_formset import BaseInlineFormSet

        if self.klass.can_order:
            if not issubclass(self.klass.model, OrderedModel):
                raise ValidationError(
                    f"FormSet '{self.key}' model not a subclass of OrderedModel but formset.can_order is True"
                )

        if not issubclass(self.klass, BaseInlineFormSet):
            raise ValidationError(f"FormSet '{self.key}' klass not a subclass of BaseInlineFormSet")

        return self
```

to:

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

        return self
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_optional_ordered.py -v`
Expected: PASS (all tests so far)

- [ ] **Step 5: Run the existing formset/ordered suites to confirm no regression**

Run: `cd tests && pytest test1/test_action_ordered.py test1/test_form_validation.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/formsets/formsets.py tests/test1/test_optional_ordered.py
git commit -m "fix: remove top-level ordered_model import from formsets (make ordered extra optional)"
```

---

## Task 3: Use the helper in `action_ordered.py`

**Files:**
- Modify: `crud_views/lib/views/action_ordered.py` (`OrderedCheckBase.__init__`, lines 5-12)

- [ ] **Step 1: Update `OrderedCheckBase` to use the helper**

In `crud_views/lib/views/action_ordered.py`, change `OrderedCheckBase` from:

```python
class OrderedCheckBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ordered_model.models import OrderedModel

        # todo: move to system checks
        if not issubclass(self.model, OrderedModel):
            raise ValueError(f"{self.model} is not a subclass of OrderedModel")
```

to:

```python
class OrderedCheckBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from crud_views.lib.ordered import get_ordered_model

        ordered_model = get_ordered_model()
        # When django-ordered-model is absent, the model cannot be an OrderedModel;
        # crud_views.checks.check_ordered_model_installed reports the missing extra at startup.
        if ordered_model is not None and not issubclass(self.model, ordered_model):
            raise ValueError(f"{self.model} is not a subclass of OrderedModel")
```

- [ ] **Step 2: Run the ordered view suite to confirm no regression**

Run: `cd tests && pytest test1/test_action_ordered.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add crud_views/lib/views/action_ordered.py
git commit -m "refactor: use get_ordered_model helper in OrderedCheckBase, drop todo"
```

---

## Task 4: System check `check_ordered_model_installed`

**Files:**
- Modify: `crud_views/checks.py`
- Test: `tests/test1/test_optional_ordered.py`

The check must (a) detect whether anything needs `ordered_model`, and (b) only
error when the package is absent. "Needs it" means a registered view subclasses
`OrderedUpView`/`OrderedDownView`, or a view's `cv_formsets` contains a
`FormSet` with `can_order=True` (including nested children).

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_optional_ordered.py`:

```python
from crud_views.lib import ordered as ordered_helper


@pytest.mark.django_db
def test_check_passes_when_ordered_model_installed():
    """With the package installed and ordered views registered, the check is silent."""
    from crud_views.checks import check_ordered_model_installed

    errors = check_ordered_model_installed()
    assert errors == []


@pytest.mark.django_db
def test_check_errors_when_ordered_model_absent(monkeypatch):
    """When the package is absent but ordered views are registered, the check errors."""
    from crud_views import checks

    # The test app's Author viewset registers up/down ordered views, so the check
    # must flag the missing dependency.
    monkeypatch.setattr(checks.ordered_helper, "get_ordered_model", lambda: None)

    errors = checks.check_ordered_model_installed()
    assert len(errors) == 1
    assert errors[0].id == "crud_views.E300"
    assert "ordered" in errors[0].msg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_optional_ordered.py::test_check_errors_when_ordered_model_absent -v`
Expected: FAIL — `AttributeError`/`ImportError`: `check_ordered_model_installed` does not exist.

- [ ] **Step 3: Write the implementation**

Replace the entire contents of `crud_views/checks.py` with:

```python
from django.core.checks import Error, Tags as DjangoTags
from django.core.checks import register

from crud_views.lib import ordered as ordered_helper
from crud_views.lib.formsets.formsets import FormSet
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.action_ordered import OrderedDownView, OrderedUpView
from crud_views.lib.viewset import ViewSet, _REGISTRY, _REGISTRY_LOCK


class Tags(DjangoTags):
    """Do this if none of the existing tags work for you:
    https://docs.djangoproject.com/en/1.8/ref/checks/#builtin-tags
    """

    my_new_tag = "my_new_tag"


@register(Tags.my_new_tag)
def check_taggit_is_installed(app_configs=None, **kwargs):
    "Check that django-taggit is installed when usying myapp."

    errors = crud_views_settings.check_messages

    for check in ViewSet.checks_all():
        for message in check.messages():
            errors.append(message)
    return errors


def _formset_uses_ordering(formset: FormSet) -> bool:
    """True if this formset or any nested child enables can_order."""
    if formset.klass.can_order:
        return True
    return any(_formset_uses_ordering(child) for child in formset.children.values())


def _registry_needs_ordered_model() -> bool:
    """True if any registered view requires django-ordered-model."""
    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            if issubclass(view, (OrderedUpView, OrderedDownView)):
                return True
            formsets = getattr(view, "cv_formsets", None)
            if formsets is not None:
                if any(_formset_uses_ordering(fs) for fs in formsets.values()):
                    return True
    return False


@register(Tags.my_new_tag)
def check_ordered_model_installed(app_configs=None, **kwargs):
    """Error if an ordered view / can_order formset is used without django-ordered-model."""
    if ordered_helper.get_ordered_model() is not None:
        return []
    if not _registry_needs_ordered_model():
        return []
    return [
        Error(
            "django-ordered-model is required by an ordered view or a can_order formset, "
            "but it is not installed.",
            hint="Install the optional extra: pip install django-crud-views[ordered]",
            id="crud_views.E300",
        )
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_optional_ordered.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Commit**

```bash
git add crud_views/checks.py tests/test1/test_optional_ordered.py
git commit -m "feat: add check_ordered_model_installed system check for optional ordered extra"
```

---

## Task 5: Full verification

- [ ] **Step 1: Run the entire test suite**

Run: `cd tests && pytest`
Expected: PASS (all tests, including the pre-existing ~268)

- [ ] **Step 2: Lint and format**

Run: `task check && task format`
Expected: ruff reports no errors; formatter makes no changes.

- [ ] **Step 3: Confirm no remaining top-level optional import**

Run: `grep -rn "^from ordered_model\|^import ordered_model" crud_views/`
Expected: no output (every reference is inside a function via `get_ordered_model`).

- [ ] **Step 4: Final commit (only if lint/format changed anything)**

```bash
git add -A
git commit -m "chore: lint/format after optional ordered dependency work"
```
