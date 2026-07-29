# Optional-Dependency Import Guards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete two `except ImportError` guards that protect required dependencies and can never fire, and add a test covering the one guard that protects a genuinely optional dependency.

**Architecture:** `src/` has five optional-dependency import guards. Two of them (`django-filter` in `lib/view/meta.py`, `django-crispy-forms` in `lib/views/list.py`) guard dependencies that `pyproject.toml` lists as **required** — they are vestigial from a removed plain-theme/minimal-install era, and they can never execute. They get deleted. The two are not equally dangerous: `list.py`'s sentinels (`FormHelper = object`, `layout = None`) would turn a clean `ImportError` into a baffling `AttributeError` deep in rendering had they ever fired, while `meta.py`'s `_base_metaclass = type` was inert — `type(FilterMixin) is type`, so it computed the same value as the success path. Both are deleted as dead code; only the first was also a landmine. The third (`django-polymorphic` in `lib/formsets/render_tree.py`) is a real contract and gets a test following the idiom already established in `tests/test1/test_optional_ordered.py`.

**Tech Stack:** pytest + pytest-xdist + pytest-random-order, `monkeypatch.setitem(sys.modules, ...)` + `importlib.reload`, coverage.py 7.15.2, ruff 0.16 (with isort `I` selected).

**Spec:** `superpowers/specs/2026-07-29-optional-dependency-guards-design.md`
**Issue:** [#107](https://github.com/jacob-consulting/django-crud-views/issues/107)
**Branch:** `feature/optional-dependency-guards-107` (already created; spec already committed there)

---

## Starting Point — read this first

Everything below was established in the design session. **Do not re-derive it; the experiments are recorded with their results.**

### Where things stand

- **Branch:** `feature/optional-dependency-guards-107`, two commits ahead of `main` (`main` tip is `be4993d`). Both are documentation only — spec `7164773`, spec correction `c951d74`. **No implementation work has started.** Task 1 Step 1 is the first thing to do.
- **Working tree:** clean.
- **No PR exists yet.** Task 3 opens it.
- This is the first of three coverage follow-ups. The agreed order is **#107 → #105 → #106**. Do not touch #105 or #106 work here.

### Baseline measurements (py3.12 / Django 5.2, this machine)

Taken with the full suite from the repo root. **871 passed, 1 skipped. 4429 statements, 268 missing, 93.95%.**

The five `except ImportError` guards in `src/`, audited:

| Guard | Dependency | Required or optional | Covered? |
|---|---|---|---|
| `lib/view/meta.py:3-8` | `django-filter` | **required** | no — lines 7, 8 missing |
| `lib/views/list.py:10-16` | `django-crispy-forms` | **required** | no — lines 14, 15, 16 missing |
| `lib/formsets/render_tree.py:32-35` | `django-polymorphic` | optional (`polymorphic` extra) | no — lines 34, 35 missing |
| `lib/ordered.py:20-21` | `django-ordered-model` | optional (`ordered` extra) | **yes** — covered by `test_optional_ordered.py` |
| `templatetags/crud_views.py:29-30` | (runtime guard in a function) | — | **yes** |

Expected end state: misses **268 → 261**. Five uncovered lines disappear with the deletions, two become covered by the new test. The denominator also shrinks a little, because each deleted `try:` was itself a counted statement — so the percentage rises by slightly less than the miss delta implies.

### Decisions already made — do not relitigate

- **Delete, don't test, the two dead guards.** Writing stubbing tests for them would cement dead code and make it harder to remove later.
- **Do not re-modularise crispy/django-filter into extras.** That would make the guards live contracts again, but it is a packaging change of a different size and is not wanted.
- **Nothing depends on the fallbacks.** No system check in `checks.py` or `lib/check.py` references `FormHelper`, `layout`, or `_base_metaclass`. Verified.
- **`pytest-random-order` is opt-in.** It is installed but not in `addopts`, so default collection order is deterministic. The restore hazard in Task 1 would not bite today — but the fix costs one line, so do it anyway rather than depending on an alphabetical accident.

### There is no RED step in Task 1

This matters, and it is the one place an implementer is likely to fake a result. The new test **passes the moment it is written**, because the guard it exercises already exists — this is coverage of existing behaviour, not test-driven development of new behaviour. Do not invent or report a failing run.

The honest equivalent of RED here is a **coverage delta measured directly**: `render_tree.py` lines 34-35 are missing before the test exists and present after. Task 1 Step 2 measures the "before" and Step 5 measures the "after". Those two measurements are the evidence.

### Environment

- Local venv: `.venv/bin/python` — Python 3.12.3, Django 5.2.14, coverage.py 7.15.2.
- Run the suite **from the repository root** (`pytest tests`), not from `tests/`. This changed in #103; running from `tests/` breaks coverage config discovery.
- `task format` / `task check` wrap ruff. Pre-commit runs `ruff-format`.

## Global Constraints

- Line length 120, double quotes, ruff-formatted. `ruff lint select` is `["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]` — **`I` means isort is enforced**, so moved imports must land in the correct block and order.
- Python floor is 3.12.
- Do not change `fail_under` (88). Do not add a `codecov.yml`. Do not touch `noxfile.py` or the workflows — that is #105/#106 territory.
- All work happens on `feature/optional-dependency-guards-107`. Do not commit to `main`.
- Every commit message references `#107`.

---

### Task 1: Cover the real guard (`django-polymorphic`)

Adds a test file for the one import guard that protects a genuinely optional dependency, following the idiom already used for `django-ordered-model`.

**Files:**
- Create: `tests/test1/test_optional_polymorphic.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: coverage of `src/crud_views/lib/formsets/render_tree.py:34-35`. No later task imports from this file.

- [ ] **Step 1: Read the existing idiom you are copying**

Read `tests/test1/test_optional_ordered.py:25-40`. That is `test_formsets_module_imports_without_ordered_model`, and it is the pattern this task follows: hide the package in `sys.modules`, reload, assert, restore.

The one thing you must change: that test restores with a single `importlib.reload`, which is enough there because it reloads the *importing* module. Here it is not enough — see Step 3.

- [ ] **Step 2: Record the "before" coverage of the target lines**

There is no failing test to run (see "There is no RED step in Task 1" above). Measure the coverage gap directly instead:

```bash
.venv/bin/python -m pytest tests -n auto --cov --cov-report=term-missing -q 2>&1 | grep "render_tree.py"
```

Expected: a line for `src/crud_views/lib/formsets/render_tree.py` whose missing-lines column **includes `34-35`**, e.g. `34-35, 46, 87, 146, 255-257`.

Write down the exact missing-line list. You will compare against it in Step 5. If `34-35` is *not* in the list, stop — something differs from the baseline and the rest of this task is built on a false premise.

- [ ] **Step 3: Write the test file**

Create `tests/test1/test_optional_polymorphic.py`:

```python
"""Covers the django-polymorphic import guard in lib/formsets/render_tree.py.

`polymorphic` is a genuinely optional dependency (the `polymorphic` extra), so
`render_tree` must import cleanly without it. Mirrors test_optional_ordered.py,
which does the same for django-ordered-model. See issue #107.
"""

import importlib
import sys


def test_render_tree_exposes_polymorphic_base_when_installed():
    """With django-polymorphic installed, the real class is bound."""
    from crud_views.lib.formsets import render_tree

    assert render_tree.BasePolymorphicInlineFormSet is not None


def test_render_tree_imports_without_polymorphic(monkeypatch):
    """render_tree must import cleanly when django-polymorphic is absent."""
    # Hide polymorphic and the submodule the guard actually imports from.
    monkeypatch.setitem(sys.modules, "polymorphic", None)
    monkeypatch.setitem(sys.modules, "polymorphic.formsets", None)

    from crud_views.lib.formsets import render_tree

    reloaded = importlib.reload(render_tree)
    assert reloaded.BasePolymorphicInlineFormSet is None

    # Restore — see the note below. Do NOT restore with a second
    # importlib.reload; snapshot and replay the namespaces instead.
```

**Restore: snapshot/replay, not a second reload.** An earlier draft of this plan
prescribed `importlib.reload(reloaded)` plus a reload of `formsets` to restore. That is
wrong and was proven wrong during implementation. `XForm` and `XFormSet` are mutually
forward-referencing pydantic models; `importlib.reload` re-executes the module in its
*existing* `__dict__`, so when the second reload runs `class XForm(...)`, pydantic resolves
the `"XFormSet"` forward ref against the generation still bound in that dict — the one from
the hidden-polymorphic reload, because the new `class XFormSet(...)` has not executed yet.
That stale binding is baked into the pydantic-core schema permanently and is not repairable
with `model_rebuild(force=True)`.

Reproducer (fails with the second-reload restore, passes with snapshot/replay):

```bash
.venv/bin/python -m pytest tests/test1/test_optional_polymorphic.py \
    tests/test1/test_formsets_validation_gate.py -p random_order --random-order-seed=2 -q
```

Failure signature: `ValidationError ... Input should be a valid dictionary or instance of
XFormSet [type=model_type, input_value=XFormSet(...), input_type=XFormSet]` — two
generations of one class. Note this only appears when the guard test runs *before*
`test_formsets_validation_gate.py`; in default alphabetical order it runs after, which is
why a default-order run looks clean.

Snapshot both module namespaces before mutating anything and replay them afterwards, so no
new class generation is ever created for the restore path:

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

- [ ] **Step 4: Run the new tests**

Run: `.venv/bin/python -m pytest tests/test1/test_optional_polymorphic.py -v`

Expected: **2 passed.** They pass immediately — that is correct and expected, not a mistake. The behaviour already exists; this test covers it.

- [ ] **Step 5: Verify the coverage delta — this is the real evidence**

```bash
.venv/bin/python -m pytest tests -n auto --cov --cov-report=term-missing -q 2>&1 | grep "render_tree.py"
```

Expected: the missing-lines column **no longer contains `34` or `35`**. Everything else in that list (`46, 87, 146, 255-257`) is unrelated and must still be there.

Compare against what you wrote down in Step 2. If `34-35` is still listed, the reload is not taking effect — check that both `sys.modules` keys are set, including the `polymorphic.formsets` submodule.

- [ ] **Step 6: Prove the restore does not leak**

The default test order does not meaningfully exercise the restore path, so a single green run proves nothing about it. Run the full suite under randomised order across several seeds:

```bash
for seed in 1 2 3 4 5; do
  .venv/bin/python -m pytest tests -n auto -q -p random_order --random-order-seed=$seed 2>&1 | tail -1
done
```

Expected: five lines, each reporting **873 passed, 1 skipped** with no failures or errors (the 871 baseline plus this task's 2 tests).

If any seed fails inside `test_conditional_formset.py` with an `isinstance`/type-identity error, the restore is incomplete — confirm Step 3's snapshot/replay (both the `render_tree` and `formsets` namespaces) runs after `monkeypatch.undo()`.

- [ ] **Step 7: Commit**

```bash
git add tests/test1/test_optional_polymorphic.py
git commit -m "test(formsets): cover the django-polymorphic import guard (#107)"
```

---

### Task 2: Delete the two dead guards

These guard **required** dependencies and cannot fire. Deleting them removes five uncovered lines and, more importantly, removes fallbacks that would corrupt behaviour rather than fail cleanly.

**Files:**
- Modify: `src/crud_views/lib/view/meta.py:1-8`
- Modify: `src/crud_views/lib/views/list.py:1-16`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `meta.py` exporting `_base_metaclass` unconditionally, `list.py` importing `layout` and `FormHelper` unconditionally. No later task depends on these names.

- [ ] **Step 1: Simplify `lib/view/meta.py`**

Replace lines 1-8:

```python
from crud_views.lib.exceptions import cv_raise

try:
    from django_filters.views import FilterMixin

    _base_metaclass = type(FilterMixin)
except ImportError:
    _base_metaclass = type
```

with:

```python
from django_filters.views import FilterMixin

from crud_views.lib.exceptions import cv_raise

_base_metaclass = type(FilterMixin)
```

Note the reordering — `I` (isort) is enforced, and third-party `django_filters` sorts above first-party `crud_views`. Leave `class CrudViewMetaClass(_base_metaclass):` and everything below untouched.

- [ ] **Step 2: Simplify `lib/views/list.py`**

Replace lines 1-16:

```python
from collections.abc import Iterable

from django.utils.translation import gettext as _
from django.views import generic

from crud_views.lib.check import Check, CheckTemplateOrCode
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin

# crispy may not be installed
try:
    from crispy_forms import layout
    from crispy_forms.helper import FormHelper
except ImportError:
    FormHelper = object
    layout = None
```

with:

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

`crispy_forms` sorts above `django` in the third-party block. The `# crispy may not be installed` comment goes with the guard — it is false and must not be kept.

- [ ] **Step 3: Run the full suite**

Run: `.venv/bin/python -m pytest tests -n auto -q`

Expected: **873 passed, 1 skipped** — the 871 pre-#107 baseline plus Task 1's 2 tests. Task 2 adds and removes no tests.

What matters is zero failures and zero errors; treat a different total as worth investigating rather than an automatic failure.

- [ ] **Step 4: Run the lint and format gates**

Run: `task format && task check`

Expected: both clean. If ruff reorders the imports differently from Step 1/Step 2, **accept ruff's ordering** — it is the authority, and the blocks above are what it should produce.

- [ ] **Step 5: Verify the guards are gone from the coverage report**

```bash
.venv/bin/python -m pytest tests -n auto --cov --cov-report=term-missing -q 2>&1 | grep -E "meta\.py|list\.py|^TOTAL"
```

Expected:
- `lib/view/meta.py` — missing column no longer lists `7` or `8`.
- `lib/views/list.py` — missing column no longer lists `14`, `15`, or `16`.
- `TOTAL` — **261 missing** (down from 268).

If TOTAL is not 261, do not force it. Report the number you got and what the per-file lines show; the arithmetic is 5 lines deleted plus 2 newly covered, and a mismatch means an assumption needs revisiting rather than a number needs massaging.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/view/meta.py src/crud_views/lib/views/list.py
git commit -m "refactor(imports): drop dead ImportError guards for required deps (#107)"
```

---

### Task 3: Changelog, issue correction, and pull request

**Files:**
- Modify: `CHANGELOG.md` (the `## Unreleased` section)

**Interfaces:**
- Consumes: the deletions from Task 2 and the test from Task 1.
- Produces: an open PR against `main`.

- [ ] **Step 1: Add the changelog entry**

`CHANGELOG.md` has an `## Unreleased` section containing `### Changed` and `### Fixed` subsections. Add this bullet to the **end of the existing `### Changed` list**, not as a new subsection:

```markdown
- Importing `crud_views` now fails immediately with `ImportError` if `django-filter` or
  `django-crispy-forms` is missing, instead of importing successfully and failing later with
  a confusing `AttributeError` during rendering. Both are required dependencies, so this only
  affects broken installations. The dead `try`/`except ImportError` guards that produced the
  old behaviour have been removed. (#107)
```

- [ ] **Step 2: Commit and push**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): dead import guards removed (#107)"
git push -u origin feature/optional-dependency-guards-107
```

- [ ] **Step 3: Correct the issue body**

The #107 issue text describes all three guards as "the package's optional-dependency contract". That is false for two of them — they guard required dependencies. Post a correcting comment rather than silently editing the body:

```bash
gh issue comment 107 --body "$(cat <<'EOF'
Correction to this issue's framing, found while designing the fix.

Only **one** of the three guards protects an optional dependency. `django-filter` and
`django-crispy-forms` are both **required** dependencies in `pyproject.toml`, so the guards in
`lib/view/meta.py` and `lib/views/list.py` cannot fire in any valid installation.

They are vestigial: `33a468f "Restructure pyproject.toml optional dependencies"` moved
`django-crispy-forms` out of a `bootstrap5` extra into required deps and deleted the
`minimal`/`bootstrap5minimal` extras that carried `django-filter`. The guards themselves date to
`cf59cb7 "add initial code from POC"` and were never revisited. The plain theme they served was
removed in M1.

They are also worse than merely uncovered. In `list.py`, `FormHelper = object` feeds
`class ListViewFilterFormHelper(FormHelper)` and `layout = None` feeds `layout.Submit(...)` — so
if crispy really were absent the module would import "successfully" and then die with
`AttributeError: 'NoneType' object has no attribute 'Submit'`. The fallback never worked.

So the fix is: **delete** those two, and **test** the one real guard (`django-polymorphic` in
`lib/formsets/render_tree.py`), following the existing `test_optional_ordered.py` idiom.
EOF
)"
```

- [ ] **Step 4: Open the pull request**

```bash
gh pr create --title "refactor(imports): delete dead ImportError guards, cover the real one (#107)" --body "$(cat <<'EOF'
Fixes #107.

## What this is

`src/` had five `except ImportError:` guards. Three were uncovered. It turns out only one of
those three protects anything.

| Guard | Dependency | Status | Action |
|---|---|---|---|
| `lib/view/meta.py:3-8` | `django-filter` | **required** | deleted |
| `lib/views/list.py:10-16` | `django-crispy-forms` | **required** | deleted |
| `lib/formsets/render_tree.py:32-35` | `django-polymorphic` (optional) | real contract | tested |

## Why delete rather than test

`django-filter` and `django-crispy-forms` are required dependencies, so those guards cannot fire.
They are vestigial from the removed plain-theme / minimal-install era — `33a468f` moved crispy out
of a `bootstrap5` extra into required deps and dropped the `minimal` extras carrying django-filter,
while the guards themselves date to the initial POC commit `cf59cb7`.

They are also actively harmful. In `list.py`, `FormHelper = object` feeds
`class ListViewFilterFormHelper(FormHelper)` and `layout = None` feeds `layout.Submit(...)`. Had
crispy ever actually been absent, the module would have imported "successfully" and then died with
`AttributeError: 'NoneType' object has no attribute 'Submit'` somewhere in rendering. A hard
`ImportError` at import time is the correct behaviour for a required dependency.

Testing them would have cemented dead code and made it harder to remove.

## The one real guard

`tests/test1/test_optional_polymorphic.py` follows the idiom already established in
`test_optional_ordered.py` — which is exactly why `lib/ordered.py:20-21` was the one guard already
covered.

It restores more carefully than that older test does: `formsets.py` binds `XForm`/`XFormSet` at its
own import time, so reloading `render_tree` alone would leave the two modules disagreeing about
class identity. The test snapshots both module namespaces before mutating anything and replays them
afterwards, so no new class generation is ever created for the restore path. (`pytest-random-order`
is opt-in here so this would not bite today, but the safety is otherwise an accident of alphabetical
file ordering.)

## Numbers

Misses drop **268 → 261**: five uncovered lines deleted, two newly covered. The denominator also
shrinks slightly, since each removed `try:` was itself a counted statement.

Verified under `--random-order` across five seeds to prove the reload restore does not leak.

## Sequencing

First of three coverage follow-ups from #103. The agreed order is **#107 → #105 → #106** — real
fix first, then the row-clobbering fragility, then policy last once the number has settled.
EOF
)"
```

- [ ] **Step 5: Wait for CI**

`gh pr checks` omits Codecov on this repo, and the `/commits/$SHA/status` endpoint returns an empty pending set forever on PR heads. Query check-runs instead:

```bash
gh api "repos/jacob-consulting/django-crud-views/commits/$(git rev-parse HEAD)/check-runs" \
  --jq '.check_runs[] | "\(.name)\t\(.status)\t\(.conclusion // "-")"'
```

Expected: all runs `completed/success`, including `codecov/patch`.

Note that `codecov/patch` measures only `src/` now, and this PR's `src/` diff is pure deletion — so patch coverage may report as trivially satisfied or as having no measurable lines. Either is fine; a *failure* is not.

- [ ] **Step 6: Report and hand off**

Report the check-run results and the new TOTAL missing count. Do **not** merge — the squash-merge decision is the maintainer's.

---

## Self-Review

**Spec coverage:** every section of the spec maps to a task. Spec §Scope item 1 (delete `meta.py` guard) → Task 2 Step 1. Item 2 (delete `list.py` guard) → Task 2 Step 2. Item 3 (test the polymorphic guard) → Task 1. The spec's restore-hazard subsection → Task 1 Step 3's snapshot/replay restore plus Step 6's seeded runs. The spec's five Verification points → Task 1 Steps 5-6 and Task 2 Steps 3-5. The spec's single Follow-up (correct the issue body) → Task 3 Step 3. The spec's Out-of-scope list is reflected in Global Constraints.

**Placeholders:** none. Every file edit is quoted verbatim with before and after; every command has an expected result.

**Type consistency:** `BasePolymorphicInlineFormSet` is the only symbol asserted on, spelled identically in Task 1's two tests and in the spec. `_base_metaclass`, `FormHelper`, and `layout` appear only in Task 2 and match the current source exactly. The test file name `test_optional_polymorphic.py` is identical in Task 1 Step 3, Step 7's `git add`, and the PR body.

**Known soft spots:**
- The expected suite total in Task 2 Step 3 (873 passed / 1 skipped) is derived from the 871 baseline plus 2 new tests, not observed. Treat a mismatch as worth investigating, not as automatic failure.
- Task 1 has no RED step, by nature. The coverage delta between Step 2 and Step 5 is the substitute, and it is the one result an implementer must actually measure rather than assert.
