# Optional-Dependency Import Guards — Design

**Issue:** [#107](https://github.com/jacob-consulting/django-crud-views/issues/107)
**Branch:** `feature/optional-dependency-guards-107`
**Date:** 2026-07-29

## Sequencing context

This is the first of three coverage follow-ups filed after #103/#104. The agreed order is
**#107 → #105 → #106**, decided on 2026-07-29:

- **#107 first.** It is the only one of the three that fixes something actually broken today.
  #105 is insurance against a fragility measured as currently costing nothing (Django 4.2 vs
  6.0 and py3.12 vs py3.14 all produce identical missing-line sets).
- **#106 last.** Both other issues change the measured file set and the reported number;
  the `ignore:` list and any documented target should be written against a settled report.
- The posture is **advisory, not enforcing** — `main` has no branch protection, so a
  `codecov/project` gate could not enforce anything, and a red-but-non-blocking status
  trains people to ignore the signal. A threshold also needs history the project does not
  have yet: the same commit reports 93.95% on py3.12 and 93.91% on py3.14, purely because
  PEP 649 removes annotations from the statement count. #105 is what makes that denominator
  deterministic, so it is a prerequisite for any future gate.

Each of the three gets its own spec → plan → implementation cycle. This document covers #107
only.

## The finding

`src/` has five `except ImportError:` guards. Two of the three uncovered ones do not guard
optional dependencies at all — they guard **required** ones:

| Guard | Dependency | `pyproject.toml` status | Verdict |
|---|---|---|---|
| `lib/view/meta.py:3-8` | `django-filter` | required | dead |
| `lib/views/list.py:10-16` | `django-crispy-forms` | required | dead |
| `lib/formsets/render_tree.py:32-35` | `django-polymorphic` | `polymorphic` extra | genuinely optional |

The two dead guards date to `cf59cb7 "add initial code from POC"` — day one, never revisited.
They are vestigial from the era when there was a plain (non-Bootstrap) theme and a `minimal`
install: `33a468f "Restructure pyproject.toml optional dependencies"` moved
`django-crispy-forms` and `crispy-bootstrap5` out of a `bootstrap5` extra into required
dependencies and deleted the `minimal`/`bootstrap5minimal` extras that carried
`django-filter`. The plain theme itself was removed in M1.

The issue text for #107 is wrong on this point — it describes all three guards as "the
package's optional-dependency contract". Correcting it is a task in the plan.

### The two dead guards are not equally dangerous

One fallback degrades badly; the other is inert.

In `list.py`, `FormHelper = object` feeds `class ListViewFilterFormHelper(FormHelper)` at
line 69, and `layout = None` feeds `layout.Submit(...)` at line 83. Were crispy genuinely
absent, the module would import "successfully" and then die at runtime with
`AttributeError: 'NoneType' object has no attribute 'Submit'`. The fallback never worked —
it defers a clean failure into a confusing one.

In `meta.py`, `_base_metaclass = type` is not a landmine: `FilterMixin` is a plain class with
no custom metaclass, so `type(FilterMixin) is type` evaluates to `True` (verified against the
installed django-filter 25.2). The fallback computes exactly the same value the success path
computes — it is harmless-but-dead code, not a behavioural trap. It is deleted because it can
never execute, the same reason as `list.py`, not because it would break anything if it did.

A hard `ImportError` at import time is still the right behaviour for a required dependency in
both cases, but only the `list.py` fallback would have produced a confusing failure had it
ever actually fired.

## Scope

Two deletions and one test.

### 1. Delete the dead guard in `lib/view/meta.py`

Lines 1-8 become:

```python
from django_filters.views import FilterMixin

from crud_views.lib.exceptions import cv_raise

_base_metaclass = type(FilterMixin)
```

Note the reordering: ruff has `I` (isort) selected, so the third-party `django_filters`
import sorts above the first-party `crud_views` import.

### 2. Delete the dead guard in `lib/views/list.py`

Lines 1-16 become:

```python
from collections.abc import Iterable

from crispy_forms import layout
from crispy_forms.helper import FormHelper
from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
```

`crispy_forms` sorts above `django` in the third-party block. The
`# crispy may not be installed` comment goes with the guard — it is false.

Nothing else references `FormHelper`, `layout`, or `_base_metaclass` conditionally, and no
system check in `checks.py` or `lib/check.py` asserts anything about the fallbacks. Verified.

### 3. Test the real guard: `tests/test1/test_optional_polymorphic.py`

New file, named for symmetry with the existing `test_optional_ordered.py`. It follows the
idiom already established there (`test_optional_ordered.py:25-40`) — which is precisely why
`lib/ordered.py:20-21` is the one guard already covered:

```python
def test_render_tree_imports_without_polymorphic(monkeypatch):
    """render_tree must import cleanly when django-polymorphic is absent."""
    monkeypatch.setitem(sys.modules, "polymorphic", None)
    monkeypatch.setitem(sys.modules, "polymorphic.formsets", None)

    import crud_views.lib.formsets.render_tree as rt

    reloaded = importlib.reload(rt)
    assert reloaded.BasePolymorphicInlineFormSet is None

    # restore — see below
```

A second test asserting the installed case (`BasePolymorphicInlineFormSet is not None`) mirrors
`test_get_ordered_model_returns_class_when_installed` and costs nothing.

#### The restore hazard

The existing `ordered` test restores with `monkeypatch.undo()` followed by a single
`importlib.reload`. That is sufficient there because it reloads the *importing* module.
It is **not** sufficient here.

`lib/formsets/formsets.py:20` does `from .render_tree import XForm, XFormSet`, binding those
classes at its own import time. Reloading `render_tree` creates new class objects while
`formsets.py` keeps pointing at the originals. `tests/test1/test_conditional_formset.py:109`
imports `XFormSet` from `render_tree` inside the test body, so it picks up whichever object is
current. That is a latent `isinstance` mismatch.

How exposed is it today? Less than it first appears: `pytest-random-order` is installed but
**opt-in** — it is not in `addopts`, so collection order is deterministic, and
`test_conditional_formset.py` sorts before `test_optional_polymorphic.py` alphabetically and
would run first. So the contamination would not bite today. But that safety is an accident of
file naming, `-n auto` distributes tests across xdist workers rather than running them in
strict collection order, and `--random-order` is available for ad-hoc runs. Restoring both
modules costs one extra line and removes the dependency on that accident entirely.

**Reloading twice does not fix it — proven during implementation.** `XForm` and `XFormSet` are
mutually forward-referencing pydantic models, and `importlib.reload` re-executes a module in its
*existing* `__dict__`. On the restore reload, `class XForm(...)` runs before
`class XFormSet(...)`, so pydantic resolves the `"XFormSet"` forward ref against the stale
hidden-polymorphic generation still bound in that dict. The binding is baked into the
pydantic-core schema permanently and survives `model_rebuild(force=True)`.

The restore must therefore **snapshot both module namespaces before mutating anything and replay
them afterwards**, so no new class generation is created for the restore path at all:

```python
    render_tree_snapshot = vars(render_tree).copy()
    formsets_snapshot = vars(formsets_mod).copy()
    # ... hide polymorphic, reload, assert ...
    monkeypatch.undo()
    vars(render_tree).clear()
    vars(render_tree).update(render_tree_snapshot)
    vars(formsets_mod).clear()
    vars(formsets_mod).update(formsets_snapshot)
```

Reproducer for the broken variant — fails on the second-reload restore, passes on snapshot/replay:

```bash
.venv/bin/python -m pytest tests/test1/test_optional_polymorphic.py \
    tests/test1/test_formsets_validation_gate.py -p random_order --random-order-seed=2 -q
```

`ValidationError ... Input should be a valid dictionary or instance of XFormSet
[input_value=XFormSet(...), input_type=XFormSet]` — two generations of one class.

## Verification

1. `render_tree.py:34-35` move from missed to hit (the `except` clause line executes when the
   `ImportError` is handled, so both lines are gained, not just the assignment).
2. `meta.py` and `list.py` contribute no uncovered lines (they contribute none at all now).
3. Misses drop from the 268 baseline to **261**: 5 currently-uncovered lines disappear with the
   deletions (`meta.py:7-8`, `list.py:14-16`) and 2 become covered (`render_tree.py:34-35`).
   The denominator also shrinks slightly, since each deleted `try:` was itself a counted
   statement — so expect the percentage to rise by a little less than the miss count implies.
4. The suite passes with `-n auto`, **and** passes under `--random-order` across several seeds.
   The default deterministic order does not exercise the restore path meaningfully (see the
   restore-hazard note), so a single default-order green run proves nothing about it. Randomised
   runs are the check that matters.
5. `task format && task check` clean — ruff will enforce the import reordering.

## Out of scope

- Anything in #105 (matrix row clobbering) or #106 (`codecov.yml`).
- Re-modularising `django-crispy-forms` / `django-filter` back into extras. That would make
  the deleted guards live contracts again, but it is a packaging change of a different size
  and is not wanted today.
- The two already-covered guards, `lib/ordered.py:20` and `templatetags/crud_views.py:29`.

## Follow-ups

- Correct the #107 issue body, which mischaracterises all three guards as an
  optional-dependency contract.
