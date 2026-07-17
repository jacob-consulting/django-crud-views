# Workflow & Polymorphic Public-API Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `crud_views_workflow` and `crud_views_polymorphic` a curated public API surface at their `.lib` packages so the flagship examples import only public names before the 1.0 freeze (issue #76).

**Architecture:** Flatten a curated surface into each extension's `lib/__init__.py`, mirroring the M2 `crud_views.lib.formsets` precedent. Polymorphic stays **eager** (no import-safety constraint); workflow is **lazy** (PEP 562 `__getattr__`) because a consumer *model* module imports `WorkflowModelMixin` from `crud_views_workflow.lib` before `django.setup()`, and `crud_views_workflow.lib.views` cannot be imported before the app registry is ready. Then update the stability doc, examples, reference docs, and CHANGELOG.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, pytest + pytest-django.

## Global Constraints

- Public API path for each extension is `crud_views_workflow.lib` / `crud_views_polymorphic.lib` (the curated surface). Deep submodule paths (`.lib.enums`, `.lib.views`, `.lib.delete`, …) remain valid but are no longer the documented path.
- `crud_views_workflow.lib` must stay import-safe before `django.setup()`: importing the package, or importing `WorkflowModelMixin` / `BadgeEnum` / `WorkflowComment` / `WorkflowForm` from it, must NOT trigger import of `crud_views_workflow.lib.views` (models + `django.contrib.auth.mixins`).
- `WorkflowInfo` is a model and keeps its canonical `crud_views_workflow.models` path — it is NOT re-exported into `.lib`.
- Line length 120, double quotes, ruff format/check must pass.
- Do not modify the `crud_views` core or `crud_views_guardian` surfaces. Do not add top-level (`crud_views_workflow` / `crud_views_polymorphic`) package exports.
- Test-suite imports using deep paths stay as-is (both paths remain valid); only examples and reference docs migrate.

**Commands:**
- Main test suite: `cd tests && pytest <path>::<name> -v`
- Example test suite: `cd examples/bootstrap5 && pytest`
- Lint/format: `task check && task format` (ruff)

---

### Task 1: Complete the eager polymorphic `.lib` surface

**Files:**
- Modify: `src/crud_views_polymorphic/lib/__init__.py`
- Test: `tests/test1/test_public_api_surface.py` (create)

**Interfaces:**
- Produces: `crud_views_polymorphic.lib` exports (via `__all__`) `PolymorphicContentTypeForm`, `PolymorphicDeleteView`, `PolymorphicDeleteViewPermissionRequired` in addition to the existing create/create_select/detail/update view classes.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_public_api_surface.py`:

```python
"""Issue #76: curated public-API surface for the workflow & polymorphic extensions."""


def test_polymorphic_lib_exports_every_name_in_all():
    import crud_views_polymorphic.lib as poly_lib

    for name in poly_lib.__all__:
        assert hasattr(poly_lib, name), f"{name} is in __all__ but not importable from crud_views_polymorphic.lib"


def test_polymorphic_lib_exposes_delete_and_content_type_form():
    from crud_views_polymorphic.lib import (
        PolymorphicContentTypeForm,
        PolymorphicDeleteView,
        PolymorphicDeleteViewPermissionRequired,
    )
    from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm as _form
    from crud_views_polymorphic.lib.delete import (
        PolymorphicDeleteView as _delete,
        PolymorphicDeleteViewPermissionRequired as _delete_perm,
    )

    assert PolymorphicContentTypeForm is _form
    assert PolymorphicDeleteView is _delete
    assert PolymorphicDeleteViewPermissionRequired is _delete_perm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_public_api_surface.py::test_polymorphic_lib_exposes_delete_and_content_type_form -v`
Expected: FAIL with `ImportError: cannot import name 'PolymorphicDeleteView' from 'crud_views_polymorphic.lib'`

- [ ] **Step 3: Complete the polymorphic `.lib` surface**

Replace the entire contents of `src/crud_views_polymorphic/lib/__init__.py` with:

```python
from crud_views_polymorphic.lib.create import PolymorphicCreateView, PolymorphicCreateViewPermissionRequired
from crud_views_polymorphic.lib.create_select import (
    PolymorphicContentTypeForm,
    PolymorphicCreateSelectView,
    PolymorphicCreateSelectViewPermissionRequired,
)
from crud_views_polymorphic.lib.delete import PolymorphicDeleteView, PolymorphicDeleteViewPermissionRequired
from crud_views_polymorphic.lib.detail import PolymorphicDetailView, PolymorphicDetailViewPermissionRequired
from crud_views_polymorphic.lib.update import PolymorphicUpdateView, PolymorphicUpdateViewPermissionRequired

__all__ = [
    "PolymorphicContentTypeForm",
    "PolymorphicCreateSelectView",
    "PolymorphicCreateSelectViewPermissionRequired",
    "PolymorphicCreateView",
    "PolymorphicCreateViewPermissionRequired",
    "PolymorphicDeleteView",
    "PolymorphicDeleteViewPermissionRequired",
    "PolymorphicDetailView",
    "PolymorphicDetailViewPermissionRequired",
    "PolymorphicUpdateView",
    "PolymorphicUpdateViewPermissionRequired",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_public_api_surface.py -v -k polymorphic`
Expected: PASS (both polymorphic tests)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_polymorphic/lib/__init__.py tests/test1/test_public_api_surface.py
git commit -m "feat(polymorphic): export delete views and content-type form from lib (#76)"
```

---

### Task 2: Lazy workflow `.lib` surface (import-safe)

**Files:**
- Modify: `src/crud_views_workflow/lib/__init__.py` (currently empty)
- Test: `tests/test1/test_public_api_surface.py` (append)
- Test: `tests/test1/test_import_safety.py` (append)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `crud_views_workflow.lib` lazily exports (via `__all__` + module `__getattr__`) `BadgeEnum`, `WorkflowComment`, `WorkflowForm`, `WorkflowModelMixin`, `WorkflowView`, `WorkflowViewPermissionRequired`. Importing the package, or any of the non-view names, before `django.setup()` must not raise.

- [ ] **Step 1: Write the failing surface test**

Append to `tests/test1/test_public_api_surface.py`:

```python
def test_workflow_lib_exports_every_name_in_all():
    import crud_views_workflow.lib as wf_lib

    for name in wf_lib.__all__:
        assert getattr(wf_lib, name) is not None, f"{name} is in __all__ but not resolvable from crud_views_workflow.lib"


def test_workflow_lib_names_resolve_to_the_same_objects_as_deep_paths():
    from crud_views_workflow.lib import (
        BadgeEnum,
        WorkflowComment,
        WorkflowForm,
        WorkflowModelMixin,
        WorkflowView,
        WorkflowViewPermissionRequired,
    )
    from crud_views_workflow.lib.enums import BadgeEnum as _badge
    from crud_views_workflow.lib.enums import WorkflowComment as _comment
    from crud_views_workflow.lib.forms import WorkflowForm as _form
    from crud_views_workflow.lib.mixins import WorkflowModelMixin as _mixin
    from crud_views_workflow.lib.views import WorkflowView as _view
    from crud_views_workflow.lib.views import WorkflowViewPermissionRequired as _view_perm

    assert BadgeEnum is _badge
    assert WorkflowComment is _comment
    assert WorkflowForm is _form
    assert WorkflowModelMixin is _mixin
    assert WorkflowView is _view
    assert WorkflowViewPermissionRequired is _view_perm


def test_workflow_lib_unknown_attribute_raises_attribute_error():
    import pytest

    import crud_views_workflow.lib as wf_lib

    with pytest.raises(AttributeError):
        _ = wf_lib.NoSuchName
```

- [ ] **Step 2: Write the failing import-safety tests**

Append to `tests/test1/test_import_safety.py`:

```python
def test_workflow_lib_package_imports_without_app_registry():
    """The crud_views_workflow.lib package body must be lazy: importing the package before the
    app registry is ready must not drag in .lib.views (WorkflowInfo model + auth mixins)."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        import crud_views_workflow.lib

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_workflow_lib_model_mixin_public_path_imports_without_app_registry():
    """`from crud_views_workflow.lib import WorkflowModelMixin` is the documented public path and is
    used by consumer model modules loaded before the app registry is ready -- it must not raise."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowForm, WorkflowModelMixin

        assert WorkflowModelMixin is not None
        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_public_api_surface.py::test_workflow_lib_names_resolve_to_the_same_objects_as_deep_paths test1/test_import_safety.py::test_workflow_lib_model_mixin_public_path_imports_without_app_registry -v`
Expected: both FAIL — surface test with `ImportError: cannot import name 'BadgeEnum' from 'crud_views_workflow.lib'`; safety test asserts non-zero return code (the import fails in the subprocess).

- [ ] **Step 4: Implement the lazy workflow surface**

Replace the (empty) contents of `src/crud_views_workflow/lib/__init__.py` with:

```python
"""Public API surface for crud_views_workflow.

Resolved lazily (PEP 562 module __getattr__) on purpose. Consumer *model* modules import
WorkflowModelMixin from crud_views_workflow.lib while Django is still populating apps (before
django.setup()). Importing any submodule runs this package __init__ first, so eager imports here
would drag in crud_views_workflow.lib.views -- which imports the WorkflowInfo model and
CustomFormView (django.contrib.auth.mixins) at module top and therefore cannot be imported before
the app registry is ready. Lazy resolution keeps the model mixin, enums, and form pulling only
import-safe submodules; WorkflowView is loaded only when explicitly requested, which happens from
view modules after setup. See tests/test1/test_import_safety.py.
"""

from importlib import import_module

__all__ = [
    "BadgeEnum",
    "WorkflowComment",
    "WorkflowForm",
    "WorkflowModelMixin",
    "WorkflowView",
    "WorkflowViewPermissionRequired",
]

_EXPORTS = {
    "BadgeEnum": ("crud_views_workflow.lib.enums", "BadgeEnum"),
    "WorkflowComment": ("crud_views_workflow.lib.enums", "WorkflowComment"),
    "WorkflowForm": ("crud_views_workflow.lib.forms", "WorkflowForm"),
    "WorkflowModelMixin": ("crud_views_workflow.lib.mixins", "WorkflowModelMixin"),
    "WorkflowView": ("crud_views_workflow.lib.views", "WorkflowView"),
    "WorkflowViewPermissionRequired": ("crud_views_workflow.lib.views", "WorkflowViewPermissionRequired"),
}


def __getattr__(name: str):
    try:
        module_path, attr = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_path), attr)
    globals()[name] = value  # cache so subsequent lookups skip __getattr__
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_public_api_surface.py test1/test_import_safety.py -v`
Expected: PASS (all surface + all import-safety tests, including the pre-existing ones)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_workflow/lib/__init__.py tests/test1/test_public_api_surface.py tests/test1/test_import_safety.py
git commit -m "feat(workflow): lazy public-API surface at crud_views_workflow.lib (#76)"
```

---

### Task 3: Switch example imports to the public `.lib` paths

**Files:**
- Modify: `examples/bootstrap5/workflow/models.py:4-5`
- Modify: `examples/bootstrap5/workflow/views.py:16-17`
- Modify: `examples/bootstrap5/polymorphic_demo/views.py:9-16`

**Interfaces:**
- Consumes: the public surfaces produced by Task 1 and Task 2.

- [ ] **Step 1: Update `workflow/models.py`**

In `examples/bootstrap5/workflow/models.py`, replace these two lines:

```python
from crud_views_workflow.lib.enums import BadgeEnum, WorkflowComment
from crud_views_workflow.lib.mixins import WorkflowModelMixin
```

with a single public import:

```python
from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin
```

- [ ] **Step 2: Update `workflow/views.py`**

In `examples/bootstrap5/workflow/views.py`, replace these two lines:

```python
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
```

with a single public import:

```python
from crud_views_workflow.lib import WorkflowForm, WorkflowViewPermissionRequired
```

- [ ] **Step 3: Update `polymorphic_demo/views.py`**

In `examples/bootstrap5/polymorphic_demo/views.py`, replace this block (the `.lib` import plus the two deep-path imports):

```python
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicCreateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired
```

with one consolidated public import (alphabetized):

```python
from crud_views_polymorphic.lib import (
    PolymorphicContentTypeForm,
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicCreateViewPermissionRequired,
    PolymorphicDeleteViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
)
```

- [ ] **Step 4: Run the example test suite**

Run: `cd examples/bootstrap5 && pytest`
Expected: PASS (no regressions; the workflow and polymorphic_demo apps import and their tests pass)

- [ ] **Step 5: Run the full main test suite**

Run: `cd tests && pytest`
Expected: PASS (no regressions across the package)

- [ ] **Step 6: Commit**

```bash
git add examples/bootstrap5/workflow/models.py examples/bootstrap5/workflow/views.py examples/bootstrap5/polymorphic_demo/views.py
git commit -m "docs(examples): import workflow & polymorphic names from public lib paths (#76)"
```

---

### Task 4: Update stability doc, reference docs, and CHANGELOG

**Files:**
- Modify: `docs/development/stability.md`
- Modify: `docs/reference/workflow_view.md` (lines 45-47, 108-109, 150, 198, 230-231)
- Modify: `docs/reference/polymorphic_view.md` (lines 58-65)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: the public surfaces from Tasks 1 and 2. Documentation only — no runtime code.

- [ ] **Step 1: Update the stability doc — workflow section**

In `docs/development/stability.md`, replace the `### crud_views_workflow` body:

```markdown
`WorkflowView`, `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, the `WorkflowInfo`
model, and the `on_transition` hook.
```

with:

```markdown
Public import path: `crud_views_workflow.lib` —
`WorkflowView`, `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, `WorkflowForm`,
`BadgeEnum`, `WorkflowComment`. The `WorkflowInfo` model stays at `crud_views_workflow.models`,
and the `on_transition` hook is the documented overridable method on `WorkflowView`.
```

- [ ] **Step 2: Update the stability doc — polymorphic section**

In `docs/development/stability.md`, replace the `### crud_views_polymorphic` body:

```markdown
`PolymorphicCreateSelectView`, `PolymorphicCreateView`, `PolymorphicUpdateView`,
`PolymorphicDeleteView`, `PolymorphicDetailView` — each with its `*PermissionRequired`
variant.
```

with:

```markdown
Public import path: `crud_views_polymorphic.lib` —
`PolymorphicCreateSelectView`, `PolymorphicCreateView`, `PolymorphicUpdateView`,
`PolymorphicDeleteView`, `PolymorphicDetailView` — each with its `*PermissionRequired`
variant — plus the `PolymorphicContentTypeForm` used by the create-select flow.
```

- [ ] **Step 3: Update `docs/reference/workflow_view.md` import snippets**

Change every `crud_views_workflow.lib.<submodule>` import to the public `crud_views_workflow.lib` path. Make these exact replacements:

- Lines 45-47:
  ```python
  from crud_views_workflow.lib.enums import WorkflowComment
  from crud_views_workflow.lib.enums import BadgeEnum
  from crud_views_workflow.lib.mixins import WorkflowModelMixin
  ```
  →
  ```python
  from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin
  ```
- Lines 108-109:
  ```python
  from crud_views_workflow.lib.forms import WorkflowForm
  from crud_views_workflow.lib.views import WorkflowView
  ```
  →
  ```python
  from crud_views_workflow.lib import WorkflowForm, WorkflowView
  ```
- Line 150:
  ```python
  from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
  ```
  →
  ```python
  from crud_views_workflow.lib import WorkflowViewPermissionRequired
  ```
- Line 198:
  ```python
  from crud_views_workflow.lib.enums import WorkflowComment
  ```
  →
  ```python
  from crud_views_workflow.lib import WorkflowComment
  ```
- Lines 230-231:
  ```python
  from crud_views_workflow.lib.enums import BadgeEnum
  from crud_views_workflow.lib.mixins import WorkflowModelMixin
  ```
  →
  ```python
  from crud_views_workflow.lib import BadgeEnum, WorkflowModelMixin
  ```

- [ ] **Step 4: Update `docs/reference/polymorphic_view.md` import snippets**

Fold the two deep-path imports (lines 64-65) into the existing `crud_views_polymorphic.lib` block that begins at line 58. Add `PolymorphicContentTypeForm` and `PolymorphicDeleteViewPermissionRequired` to that block's name list (keep it alphabetized alongside the names already there) and delete lines 64-65:

```python
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired
```

- [ ] **Step 5: Add the CHANGELOG entry**

In `CHANGELOG.md`, insert a new section directly under the top `# Django CRUD Views - Changelog` heading and above `## 0.15.0`:

```markdown
## Unreleased

### Added

- Public API: `crud_views_workflow.lib` and `crud_views_polymorphic.lib` now expose curated
  public surfaces. `crud_views_workflow.lib` re-exports `WorkflowView`,
  `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, `WorkflowForm`, `BadgeEnum`, and
  `WorkflowComment` (resolved lazily so consumer model modules stay import-safe before the app
  registry is ready). `crud_views_polymorphic.lib` now also exports `PolymorphicDeleteView`,
  `PolymorphicDeleteViewPermissionRequired`, and `PolymorphicContentTypeForm`. The deep submodule
  paths continue to work. These names are added to the API stability policy (#76).
```

- [ ] **Step 6: Verify docs build and links**

Run: `cd tests && pytest`
Expected: PASS (doctest/reference-import checks, if any, still pass; no code changed in this task).

Run: `task docs` briefly (or `mkdocs build` if available) to confirm the docs still build without error, then stop it.
Expected: build succeeds with no broken-reference errors.

- [ ] **Step 7: Commit**

```bash
git add docs/development/stability.md docs/reference/workflow_view.md docs/reference/polymorphic_view.md CHANGELOG.md
git commit -m "docs: document public lib surfaces for workflow & polymorphic (#76)"
```

---

### Task 5: Final verification & lint

**Files:** none (verification only).

- [ ] **Step 1: Run ruff format and check**

Run: `task format && task check`
Expected: no changes needed / all checks pass. If ruff reformats, review the diff and amend the relevant commit.

- [ ] **Step 2: Run the full main test suite**

Run: `cd tests && pytest`
Expected: PASS, no regressions (should match the pre-change count plus the new surface + import-safety tests).

- [ ] **Step 3: Run the example test suite**

Run: `cd examples/bootstrap5 && pytest`
Expected: PASS.

- [ ] **Step 4: Confirm no lingering deep-path imports in examples/reference docs**

Run:
```bash
cd /home/alex/projects/alex/django-crud-views
grep -rn "crud_views_workflow.lib.enums\|crud_views_workflow.lib.forms\|crud_views_workflow.lib.views\|crud_views_workflow.lib.mixins" examples/ docs/reference/
grep -rn "crud_views_polymorphic.lib.create_select\|crud_views_polymorphic.lib.delete" examples/ docs/reference/
```
Expected: no matches (all example/reference imports now use the public `.lib` path). Matches under `tests/` are expected and intentionally left.

---

## Self-Review

**Spec coverage:**
- Workflow lazy `.lib` surface → Task 2 ✓
- Polymorphic eager `.lib` completion (delete views + content-type form) → Task 1 ✓
- Stability doc → Task 4 (steps 1-2) ✓
- Examples switch → Task 3 ✓
- Reference docs switch → Task 4 (steps 3-4) ✓
- TDD surface tests → Tasks 1 & 2 ✓
- Import-safety regression tests → Task 2 (step 2) ✓
- CHANGELOG → Task 4 (step 5) ✓
- `WorkflowInfo` stays at `.models` → enforced in Task 2 code + Task 4 step 1 ✓
- Out-of-scope (tests left on deep paths; no top-level/core/guardian changes) → honored ✓

**Placeholder scan:** none — every code and doc step shows exact content.

**Type/name consistency:** `__all__` name lists, `_EXPORTS` keys, test imports, example imports, and doc snippets use the same six workflow names and the three new polymorphic names throughout.
