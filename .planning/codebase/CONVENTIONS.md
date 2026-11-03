---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# Coding Conventions

**Analysis Date:** 2026-10-25

## Naming Patterns

**Files:**

- Python modules: `snake_case.py`, one concept per module (`src/crud_views/lib/views/update.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/view/label_mode.py`).
- Each distributed app keeps its library code under `lib/`: `src/crud_views/lib/`, `src/crud_views_guardian/lib/`, `src/crud_views_workflow/lib/`, `src/crud_views_polymorphic/lib/`, `src/crud_views_object_detail/lib/`.
- Templates: `view_<kind>.html` for the full page plus `view_<kind>.content.html` for the body partial shared by page and modal (`src/crud_views/templates/crud_views/view_update.html`, `view_update.content.html`). Snippets live in `crud_views/snippets/<role>/<key>.html` (e.g. `crud_views/snippets/header/update.html`, `snippets/action_short/update.html`, `snippets/message/update.html`).
- Static JS: `src/crud_views/static/crud_views/js/<feature>.js` (`modal.js`, `formset.js`, `list.filter.js`, `adapters.js`).
- Test files: `test_<feature>.py` / `test_<feature>_<aspect>.py` (`tests/test1/test_action_menus_config.py`, `test_action_menus_golden.py`); JS tests `tests/js/<script>.test.js`.

**Classes:**

- PascalCase. Concrete views: `<Kind>View` plus a `<Kind>ViewPermissionRequired` variant (`UpdateView` / `UpdateViewPermissionRequired` in `src/crud_views/lib/views/update.py`).
- Extension packages prefix their classes with the package concept: `GuardianListViewPermissionRequired`, `PolymorphicCreateSelectViewPermissionRequired`, `WorkflowViewPermissionRequired`.
- Mixins end in `Mixin` (`CreateViewParentMixin`, `CrudViewProcessFormMixin`, `ListViewTableFilterMixin`).
- Exceptions end in `Error` (`ViewSetNotFoundError`, `CrudViewError`, `ParentViewSetError` in `src/crud_views/lib/exceptions.py`).
- Checks: `Check<What>` (`CheckAttribute`, `CheckAttributeReg`, `CheckTemplateOrCode`, `CheckUnknownAttributes` in `src/crud_views/lib/check.py`).

**Functions / methods:**

- snake_case. Package-owned methods and helpers on views/viewsets use the `cv_` prefix (`cv_get_url`, `cv_get_success_key`, `cv_form_valid`, `cv_breadcrumb`, `cv_is_modal_request`, `cv_raise`).
- Workflow FSM transition methods use the `wf_` prefix.
- Private module helpers: leading underscore (`_formset_uses_ordering`, `_registry_needs_ordered_model` in `src/crud_views/checks.py`).

**Variables / class attributes:**

- Every `CrudView` configuration attribute uses the `cv_` prefix and carries a type annotation plus a trailing comment explaining it (`src/crud_views/lib/view/base.py`):
  ```python
  cv_key: str | None = None  # the key to register the view (i.e. detail, list, create, update, delete)
  cv_atomic: bool = True  # run the POST write phase in transaction.atomic(); see request_lifecycle.md
  ```
- Unknown `cv_*` attributes trigger system check W280 (`CheckUnknownAttributes`). Custom `cv_*` data attributes must be listed in `cv_check_ignore_attributes`.
- ViewSet instances are module-level and named `cv_<model>` (`cv_author = ViewSet(model=Author, name="author")` in `tests/test1/app/views.py`).
- ViewSet `name` and `cv_key` must match `^[a-z][a-z0-9_]*$`; `cv_path` must match `REGS["path"]` (`src/crud_views/lib/check.py`).
- View keys: `list`, `detail`, `create`, `update`, `delete`, `workflow`, `manage`; permission map list/detail→`view`, create→`add`, update→`change`, delete→`delete` (`cv_permission = "change"`).
- Module-level constants and class-level constants: UPPER_SNAKE (`TAG = "crud_views"`, `MANAGE_VIEWS_ENABLED_VALUES: ClassVar[...]`, `HEADER_LEVEL_MAX`).
- Module-global registries: `_REGISTRY` guarded by `_REGISTRY_LOCK` (`src/crud_views/lib/viewset/__init__.py`).

**Types:**

- Use PEP 604 unions and builtin generics (`str | None`, `list[str]`, `dict[str, Any]`) — ruff `UP` enforces this; minimum Python 3.12.
- Use `ClassVar[...]` for class constants on Pydantic models and mutable class attributes (ruff `RUF012`; ignored only in `tests/**`, `examples/**`, `**/migrations/*`).
- Put type-only imports in `if TYPE_CHECKING:` with `from __future__ import annotations` (`src/crud_views/lib/view/base.py`).
- Use `typing.Self`, `Literal[...]` for enumerated config (`inaccessible_actions: Literal["hide", "disable"] | None` on `ViewSet`).

**Settings:**

- Every package setting is a field on `CrudViewsSettings` (`src/crud_views/lib/settings.py`), read via `from_settings("CRUD_VIEWS_<NAME>", default=...)`. Access through the singleton `crud_views_settings`. Validation lives in `check_messages`, not in import-time code.
- Configuration resolves in layers: view attribute (`cv_*`) → ViewSet field → `CRUD_VIEWS_*` setting; `None` means "fall through".

## Code Style

**Formatting:**

- ruff format (`ruff>=0.17,<0.18`), configured in `pyproject.toml`:
  - `line-length = 120`
  - `quote-style = "double"`, `indent-style = "space"`
  - `extend-exclude = ["superpowers/**"]`
- Pre-commit (`.pre-commit-config.yaml`) runs `ruff-check` and `ruff-format` (ruff-pre-commit v0.17.1).
- CI (`.github/workflows/lint.yml`) runs `ruff format --check .` and `ruff check .` — format before pushing (`task format`, `task check`).
- JS: 4-space indent, double quotes, `const`/`let`, no jQuery in shipped code paths (guarded by `tests/test1/test_js_no_jquery_guard.py`).

**Linting:**

- `[tool.ruff.lint] select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]`.
- `allowed-confusables = ["›"]` — breadcrumb separator.
- Per-file ignore: `RUF012` for `tests/**`, `examples/**`, `**/migrations/*`.
- SonarQube Cloud analyses every push (`.sonarcloud.properties`); suppress specific false positives inline with `// NOSONAR <rule>` (see `tests/js/helpers/load.js`).

## Import Organization

**Order (ruff `I`, isort-compatible):**

1. `from __future__ import annotations` (when used)
2. Standard library (`from collections.abc import Iterable`, `from functools import cached_property`)
3. Third-party (`django`, `pydantic`, `box`, `django_tables2`, `crispy_forms`)
4. First-party absolute (`from crud_views.lib.exceptions import ...`)
5. Relative imports inside a package (`from ..settings import crud_views_settings`, `from .meta import CrudViewMetaClass`)

Example (`src/crud_views/lib/view/base.py`):

```python
from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from crud_views.lib.viewset import ViewSet

from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from crud_views.lib.check import Check, CheckAttribute
from crud_views.lib.exceptions import CrudViewError, cv_raise

from ..settings import crud_views_settings
from .meta import CrudViewMetaClass
```

**Rules:**

- Never call `get_user_model()` or touch models at import time; templatetags and workflow mixins must import before `django.setup()` (enforced by `tests/test1/test_import_safety.py`). Import Django models lazily inside functions when needed.
- Optional dependencies (`django-polymorphic`, `django-ordered-model`, `django-fsm-2`, `django-guardian`) are imported only in their extension packages or behind guards (`tests/test1/test_optional_ordered.py`, `test_optional_polymorphic.py`).
- Translation: `from django.utils.translation import gettext_lazy as _` for class-level/module-level strings; `gettext as _` only in call-time code.

**Path Aliases:**

- None. Use absolute `crud_views...` imports across packages, relative imports within a package.

## Error Handling

**Patterns:**

- Raise package exceptions from `src/crud_views/lib/exceptions.py`. Use `cv_raise(expression, msg, exception=ViewSetError)` for assertion-style guards:
  ```python
  # src/crud_views/lib/view/base.py
  cv_raise(self.cv_permission is not None, f"cv_permission not set at {self}")
  ```
- Misconfiguration must surface as Django system checks, not runtime crashes. Add a `Check*` instance to the class's `checks()` generator with a unique id (`E2xx` for views, `W280` for unknown attributes); `Check.get_id()` emits `viewset.<id>`. Registered under tag `crud_views` in `src/crud_views/checks.py`.
  ```python
  yield CheckExpression(
      context=cls,
      id="E250",
      expression=cls.cv_modal_size in ("", "sm", "lg", "xl"),
      msg=f"cv_modal_size must be one of '', 'sm', 'lg', 'xl', got {cls.cv_modal_size!r}",
  )
  ```
- Check messages name the offending setting/attribute and the received value (`{value!r}`), are idempotent across runs (`tests/test1/test_settings_checks.py`).
- Rendering-time tolerance: wrap optional rendering paths with `@ignore_exception(ExcType, default_value=...)`. It re-raises in strict mode (`CRUD_VIEWS_STRICT`, defaults to `DEBUG`) and otherwise logs a warning with `exc_info=True`. Tests run with `CRUD_VIEWS_STRICT=True`.
- Permission/lookup failures use Django's idioms: `get_object_or_404`, `Http404` for tampered parent PKs, `PermissionRequiredMixin` for 403.
- POST write phases run inside `transaction.atomic()` when `cv_atomic = True`; hook exceptions must propagate so the transaction rolls back (`tests/test1/test_transactions.py`).
- JS: throw descriptive `Error`s for missing required DOM (`cvModalElements()` in `modal.js`), and fall back to full-page navigation on any unexpected network response.

## Logging

**Framework:** stdlib `logging`

**Patterns:**

- One module logger: `logger = logging.getLogger(__name__)` (`src/crud_views/lib/exceptions.py`, `lib/views/delete.py`, `lib/view/button_data.py`, `crud_views_guardian/lib/mixins.py`).
- Use lazy %-formatting, never f-strings: `logger.warning("%s has no icon; rendered with its label instead", where)`.
- `logger.debug(..., exc_info=True)` for swallowed, expected failures (e.g. unreversible detail URL); `logger.warning` for degraded rendering.
- No `print()` in package code.

## Comments

**When to Comment:**

- Explain *why* and reference the GitHub issue: `# overflow menu (#174): keys that stay inline buttons; None = no menu`. Issue references `(#NNN)` are the norm in comments, docstrings, and test docstrings.
- Every `cv_*` attribute and every settings field carries a trailing or preceding comment describing semantics and the `None` fallback.
- Reference design specs by path when relevant (`superpowers/specs/2026-07-14-bootstrap-modals-design.md`).

**Docstrings:**

- Triple double-quoted. Short methods use one-liners (`"""Run all ViewSet, CrudView and settings checks."""`); classes and longer methods use the multi-line form with text on its own line:
  ```python
  def cv_form_valid(self, context: dict):
      """
      Handle valid form, save (update) the from instance
      """
  ```
- No enforced Google/NumPy style; prose explaining behaviour and fallbacks.
- JS files open with a `/** ... */` block describing the protocol and events (`modal.js`).

## Function Design

**Size:** Keep functions small; long logic is split into helper functions in the same module. `src/crud_views/lib/view/base.py` (880 lines) is the largest file — add new view behaviour to focused modules in `src/crud_views/lib/view/` (e.g. `action_menu.py`, `label_mode.py`, `visibility.py`) rather than growing `base.py`.

**Parameters:** Prefer keyword arguments for clarity (`self.cv_get_url(key=..., obj=obj)`, `CheckAttributeReg(context=cls, id="E200", attribute="cv_key", ...)`).

**Return Values:**

- Checks are generators: `def checks(cls) -> Iterable[Check]: yield ...; yield from ...`.
- Hooks named `cv_*_hook` / `cv_form_valid` mutate `self.object` and return nothing.
- Use `@cached_property` for per-request memoization (breadcrumbs memoize ancestor lookups).

## Module Design

**Class configuration over code:** Views are configured by class attributes; behaviour is overridden via `cv_*` hook methods. Concrete views set defaults, e.g. `src/crud_views/lib/views/update.py`:

```python
class UpdateView(CrudViewProcessFormMixin, CrudView, generic.UpdateView):
    template_name = "crud_views/view_update.html"
    cv_key = "update"
    cv_path = "update"
    cv_context_actions = crud_views_settings.update_context_actions
    cv_header_template: str | None = "crud_views/snippets/header/update.html"
    cv_icon_action = "update"

class UpdateViewPermissionRequired(CrudViewPermissionRequiredMixin, UpdateView):
    cv_permission = "change"
```

- MRO order: package mixins first, then `CrudView`, then the Django generic CBV.
- Config objects (`ViewSet`, `ParentViewSet`, `Check`, `CrudViewsSettings`, `ContextButton`) are Pydantic `BaseModel`s; validate with `field_validator`/`model_validator`.

**Exports:**

- Public names are re-exported from package `__init__.py` with an explicit, sorted `__all__` (`src/crud_views/lib/views/__init__.py`, `crud_views_polymorphic/lib/__init__.py`, `crud_views_workflow/lib/__init__.py`). `tests/test1/test_public_api_surface.py` asserts every `__all__` name resolves to the same object as its deep path — update `__all__` when adding public classes.

**Barrel Files:**

- Used: `crud_views/lib/views/__init__.py`, `crud_views/lib/view/__init__.py`, `crud_views/lib/crispy/__init__.py`, `crud_views/lib/table/__init__.py`, and each extension's `lib/__init__.py`.

## Project Process Conventions

- Conventional Commits with scope and issue refs: `feat(buttons): label mode per context button (#264) (#268)`, `docs(context-buttons): ...`, `fix:`, `refactor:` (`CONTRIBUTING.md`).
- Every change adds an entry under `## Unreleased` in `CHANGELOG.md`. Until 1.0.0, a `### Breaking` entry also requires updating `docs/migrating-1.0.md`.
- Test-driven development: write the failing test first (`CONTRIBUTING.md`).
- Versioning: `bump-my-version` syncs `pyproject.toml`, `src/crud_views/__init__.py`, `docs/index.md`, `README.md`.
- i18n: user-visible strings wrapped in `_()`; catalogs per package (`task msg-make`, `task msg-comp`, locale `de`), verified by `tests/test1/test_i18n.py`.

---

*Convention analysis: 2026-10-25*
