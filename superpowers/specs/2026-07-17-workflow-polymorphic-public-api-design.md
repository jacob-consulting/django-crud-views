# Public-API surface for `crud_views_workflow` & `crud_views_polymorphic` (issue #76)

**Date:** 2026-07-17
**Issue:** [#76](https://github.com/jacob-consulting/django-crud-views/issues/76) — Expand public API surface for workflow & polymorphic (needed by examples) before 1.0
**Status:** Approved design, ready for implementation plan

## Problem

The M3 examples rewrite (`examples/bootstrap5/`) is meant to use only the **public**
crud_views API per `docs/development/stability.md`. Five names used by the flagship
examples have no curated public export today — the examples import them from internal
submodules, which contradicts the public-API-only goal for canonical copy-me reference
code.

Names lacking a curated public export:

| Name | Package | Current (deep) path | Used by example |
|------|---------|---------------------|-----------------|
| `BadgeEnum` | workflow | `crud_views_workflow.lib.enums` | `workflow/models.py` |
| `WorkflowComment` | workflow | `crud_views_workflow.lib.enums` | `workflow/models.py` |
| `WorkflowForm` | workflow | `crud_views_workflow.lib.forms` | `workflow/views.py` |
| `PolymorphicContentTypeForm` | polymorphic | `crud_views_polymorphic.lib.create_select` | `polymorphic_demo/views.py` |
| `PolymorphicDeleteViewPermissionRequired` | polymorphic | `crud_views_polymorphic.lib.delete` | `polymorphic_demo/views.py` |

Latent inconsistency found while scoping: `crud_views_polymorphic/lib/__init__.py`
re-exports the create/create_select/detail/update view classes but **never imports the
`delete` module** — so `PolymorphicDeleteView` (which the stability doc already lists as
public) *and* `PolymorphicDeleteViewPermissionRequired` are both absent from `.lib`.

## Chosen approach

**Approach B — flatten a curated public surface into each extension's `.lib` package**,
mirroring how the M2 formsets surface was carved out (`crud_views.lib.formsets` re-exports
its public names, and the stability doc names that package as the public path).

- `crud_views_workflow.lib` and `crud_views_polymorphic.lib` become the single canonical
  public import path for each extension.
- The stability doc names those paths and lists the newly-public names.
- Examples and reference-doc snippets switch to the `.lib` paths.

Rejected alternatives:
- **A — doc-only "bless the deep submodule paths".** Zero code churn (examples already use
  those paths), but declares whole internal modules public and leaves polymorphic's
  half-flattened `.lib` inconsistent. Concedes rather than curates.
- **C — top-level package export** (`from crud_views_workflow import WorkflowForm`). Shortest
  imports, but the top-level `__init__` is deliberately empty and eagerly importing
  views/models there risks `AppRegistryNotReady`. Rejected.

## Critical constraint: import safety (workflow only)

`tests/test1/test_import_safety.py::test_workflow_mixins_import_without_app_registry`
encodes a real contract: a **consumer model module** imports `WorkflowModelMixin` via
`crud_views_workflow.lib.mixins` **while Django is still populating apps** (before
`django.setup()`). Importing any submodule runs the parent `crud_views_workflow/lib/__init__.py`
first.

Verified behaviour (before setup, `settings.configure()` only):

| Module | Import before setup |
|--------|---------------------|
| `crud_views_workflow.lib.views` | ❌ `AppRegistryNotReady` (imports `..models` + `CustomFormView` → auth mixins at module top) |
| `crud_views_workflow.lib.forms` | ✅ safe |
| `crud_views_workflow.lib.enums` | ✅ safe |
| `crud_views_workflow.lib.mixins` | ✅ safe (guaranteed by existing test) |

Therefore **eagerly** importing `WorkflowView`/`WorkflowViewPermissionRequired` into
`crud_views_workflow/lib/__init__.py` would make every submodule import (including
`.lib.mixins`) run an `__init__` that pulls `.lib.views` → `AppRegistryNotReady`, breaking
the contract and real consumer models.

Refactoring `views.py` to defer its model import does **not** help: it also imports
`CustomFormView`, whose `django.contrib.auth.mixins` dependency is inherently
un-importable before `django.setup()`.

**Resolution:** the workflow `.lib` surface is **lazy** (PEP 562). Polymorphic has no such
constraint (its consumer models subclass django-polymorphic, never importing from
`crud_views_polymorphic.lib`), so it stays **eager** — matching its existing style.

## Component design

### 1. `crud_views_workflow/lib/__init__.py` — lazy curated surface

- Import-light module body: **no** eager imports of `.views`, `.forms`, `.enums`, `.mixins`.
- Declare `__all__` = `["WorkflowView", "WorkflowViewPermissionRequired", "WorkflowModelMixin",
  "BadgeEnum", "WorkflowComment", "WorkflowForm"]`.
- A private mapping name → `(submodule, attr)`, e.g.
  `"WorkflowView": ("crud_views_workflow.lib.views", "WorkflowView")`.
- Module-level `def __getattr__(name)`: on first access, `importlib.import_module` the target
  submodule, `getattr` the attribute, cache it in the module globals, return it; raise
  `AttributeError` for unknown names.
- Module-level `def __dir__()`: return `sorted(list(globals()) + __all__)`.
- A short comment explaining **why** the surface is lazy (the pre-registry model-mixin
  import contract; `.views` is un-importable before `django.setup()`).
- `WorkflowInfo` (a model) is **not** re-exported here; it keeps its canonical
  `crud_views_workflow.models` path and its swappable-user import contract.

Effect: `from crud_views_workflow.lib import WorkflowModelMixin, BadgeEnum, WorkflowComment`
from a model module (pre-registry) lazily pulls only the safe `.lib.mixins` / `.lib.enums`.
`WorkflowView` pulls the unsafe `.lib.views` **only when actually requested**, which happens
in view modules after setup.

### 2. `crud_views_polymorphic/lib/__init__.py` — eager surface completed

Keep the existing explicit-import + `__all__` style; add:

- `from crud_views_polymorphic.lib.delete import PolymorphicDeleteView, PolymorphicDeleteViewPermissionRequired`
- `PolymorphicContentTypeForm` to the existing `create_select` import.
- Extend `__all__` with `PolymorphicDeleteView`, `PolymorphicDeleteViewPermissionRequired`,
  `PolymorphicContentTypeForm`.

### 3. `docs/development/stability.md`

- **Workflow section:** add `BadgeEnum`, `WorkflowComment`, `WorkflowForm`; state the public
  import path is `crud_views_workflow.lib`. Keep `WorkflowInfo` documented as the model at
  `crud_views_workflow.models`.
- **Polymorphic section:** add `PolymorphicContentTypeForm`; state the public import path is
  `crud_views_polymorphic.lib` (`PolymorphicDeleteView`/`*PermissionRequired` are already
  listed as names — they are now actually exported).

### 4. Examples — switch to public `.lib` paths

- `examples/bootstrap5/workflow/models.py`:
  `from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin`
- `examples/bootstrap5/workflow/views.py`:
  `from crud_views_workflow.lib import WorkflowForm, WorkflowViewPermissionRequired`
- `examples/bootstrap5/polymorphic_demo/views.py`: consolidate the polymorphic imports into
  one `from crud_views_polymorphic.lib import (…, PolymorphicContentTypeForm,
  PolymorphicDeleteViewPermissionRequired)`.

### 5. Reference docs — switch import snippets to public `.lib` paths

- `docs/reference/workflow_view.md`: `BadgeEnum`, `WorkflowComment`, `WorkflowForm`,
  `WorkflowModelMixin`, `WorkflowView`, `WorkflowViewPermissionRequired` imports →
  `crud_views_workflow.lib`.
- `docs/reference/polymorphic_view.md`: `PolymorphicContentTypeForm`,
  `PolymorphicDeleteViewPermissionRequired` imports → `crud_views_polymorphic.lib`.

## Testing (TDD)

Written RED first, then implemented to green.

1. **Workflow public surface** (new test): every name in
   `crud_views_workflow.lib.__all__` is importable via `from crud_views_workflow.lib import
   <name>`, resolves to the same object as its deep-path import, and `__all__` has no stray
   or missing names.
2. **Polymorphic public surface** (new test): same assertions for
   `crud_views_polymorphic.lib.__all__`, explicitly covering `PolymorphicDeleteView`,
   `PolymorphicDeleteViewPermissionRequired`, `PolymorphicContentTypeForm`.
3. **Workflow import safety** (extend `test_import_safety.py`): in a subprocess with
   `settings.configure()` and **no** `django.setup()`:
   - `import crud_views_workflow.lib` succeeds (package body is lazy), and
   - `from crud_views_workflow.lib import WorkflowModelMixin` succeeds (lazily pulls only the
     safe `.lib.mixins`).
   This locks in the lazy design against regression.

Existing deep-path imports in the test suite are left unchanged — those paths remain valid;
keeping them proves both the deep and the new public paths work.

## Out of scope

- Migrating test-suite imports to the `.lib` paths (deep paths stay valid; only examples and
  reference docs move, per the issue).
- Any top-level (`crud_views_workflow` / `crud_views_polymorphic`) package exports.
- Touching the `crud_views` core or `crud_views_guardian` surfaces.

## Files touched

- `src/crud_views_workflow/lib/__init__.py` (new lazy surface)
- `src/crud_views_polymorphic/lib/__init__.py` (add delete views + content-type form)
- `docs/development/stability.md`
- `examples/bootstrap5/workflow/models.py`
- `examples/bootstrap5/workflow/views.py`
- `examples/bootstrap5/polymorphic_demo/views.py`
- `docs/reference/workflow_view.md`
- `docs/reference/polymorphic_view.md`
- `tests/test1/` — new public-surface test(s) + extended `test_import_safety.py`
- `CHANGELOG.md` (unreleased entry)
