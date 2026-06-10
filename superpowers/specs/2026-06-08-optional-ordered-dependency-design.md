# Make the `ordered` dependency genuinely optional

**Date:** 2026-06-08
**Status:** Approved

## Problem

`django-ordered-model` (imported as `ordered_model`) is declared as an
**optional** dependency in `pyproject.toml` under the `ordered` extra:

```toml
ordered = [
    "django-ordered-model (>=3.4.3)"
]
```

But it is not actually optional. `crud_views/lib/formsets/formsets.py:14`
imports it unconditionally at module top level:

```python
from ordered_model.models import OrderedModel
```

The formsets feature (`FormSet`, `FormSets`, `FormSetMixin`) is core
functionality unrelated to row ordering. Because of this top-level import,
every user of `crud_views.lib.formsets` is forced to have
`django-ordered-model` installed, even when they never use `can_order`.

The only use of `OrderedModel` in that file is a single `issubclass()` check
inside `FormSet.validate_formset`, and that check is only reached when
`self.klass.can_order` is `True`.

The other consumer, `crud_views/lib/views/action_ordered.py:8`, already
imports `ordered_model` lazily (inside `OrderedCheckBase.__init__`) and is
therefore correct.

## Key constraint

`cv_formsets: FormSets` is a **class attribute** on formset views, so the
`FormSets`/`FormSet` objects are constructed at import time. The
`FormSet.validate_formset` Pydantic validator runs then. A `can_order=True`
formset therefore triggers the `OrderedModel` check during app loading.

Consequence: merely deferring the import is not enough. If the package is
absent, a raw `ImportError` would be raised at app-load time, **before** any
Django system check could run. The fix must let construction survive a
missing package so the system check can report the problem cleanly.

## Design

Three coordinated changes.

### 1. Remove the top-level import (`crud_views/lib/formsets/formsets.py`)

- Delete the module-level `from ordered_model.models import OrderedModel`.
- In `validate_formset`, replace the `OrderedModel` issubclass check (only
  reached when `self.klass.can_order` is `True`) with a guarded lazy import:
  - **Import succeeds** → run `issubclass(self.klass.model, OrderedModel)`
    exactly as today, raising `ValidationError` if the model is not an
    `OrderedModel`.
  - **Import fails** (package absent) → **do not raise here**; skip the check
    and let the system check report the missing dependency. This keeps
    app-load from crashing and lets the check fire.

This mirrors the already-correct lazy pattern in `action_ordered.py`.

### 2. Add a system check (`crud_views/checks.py`)

Add a new `@register`ed check, `check_ordered_model_installed`, that walks the
existing `ViewSet` registry and emits a Django `Error` when `ordered_model` is
**not importable** but something needs it:

- a registered view is an `OrderedUpView`/`OrderedDownView` subclass, **or**
- a view's `cv_formsets` contains any `FormSet` with `can_order=True`.

The error message instructs the user to install the extra:
`pip install django-crud-views[ordered]`.

This also retires the `# todo: move to system checks` note in
`action_ordered.py`.

### 3. Tests

- Assert that `crud_views.lib.formsets` imports cleanly when `ordered_model`
  is not importable (simulate absence).
- Assert that `check_ordered_model_installed` returns an error when an ordered
  view / `can_order` formset exists but the package is mocked-absent, and
  returns no error when the package is present.

## Out of scope

The `workflow`, `polymorphic`, and `guardian` extras live in separate Django
apps (`crud_views_workflow`, `crud_views_polymorphic`,
`crud_views_guardian`) gated by `INSTALLED_APPS`, so they are already
correctly optional. Only `ordered` leaks into the core `crud_views` app.
