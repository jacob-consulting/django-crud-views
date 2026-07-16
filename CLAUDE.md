# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`django-crud-views` is a reusable Django package that provides CRUD (Create, Read, Update, Delete) class-based views grouped into **ViewSets**. Views within a ViewSet are aware of their siblings and can link to each other while respecting Django's permission system. The package ships as four separate Django apps in a single distribution:

- `crud_views` — core package (Bootstrap 5 theme)
- `crud_views_workflow` — django-fsm state machine integration
- `crud_views_polymorphic` — django-polymorphic model support
- `crud_views_guardian` — django-guardian per-object permission support

## Development Commands

```bash
# Setup: create venv and install all deps (requires uv and task)
task dev

# Run tests via nox (matrix: Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0)
task test

# Run tests directly for quick iteration (from tests/ directory)
cd tests && pytest

# Run a single test file
cd tests && pytest test1/test_crud.py

# Run a single test
cd tests && pytest test1/test_crud.py::test_name -v

# Lint and format
task format   # ruff format
task check    # ruff check --fix

# Build package
task build    # uv build

# Serve docs locally
task docs     # mkdocs serve on localhost:8001

# Version bump
task bump-patch
```

Pre-commit hook: `ruff-format` runs on commit.

## Architecture

### Core Abstraction: ViewSet → CrudView

The central pattern is `ViewSet` (a Pydantic model in `crud_views/lib/viewset/__init__.py`) which acts as a registry and URL router for a collection of `CrudView` subclasses. Each `CrudView` registers itself with a ViewSet via `cv_viewset = my_viewset` at class definition time (handled by `CrudViewMetaClass`).

A ViewSet auto-discovers the model's PK type (UUID, int, slug) and generates `urlpatterns` for all registered views. URL pattern: `[parent_prefix/parent_pk/]prefix/[pk/]view_path/`.

### Key class hierarchy

- `CrudView` (metaclass-driven base in `crud_views/lib/view/base.py`) — not a Django view itself, but a mixin providing ViewSet integration
- Concrete views in `crud_views/lib/views/` extend both `CrudView` and Django's generic CBVs:
  - `ListView` (list.py), `DetailView` (detail.py), `CreateView` (create.py), `UpdateView` (update.py), `DeleteView` (delete.py)
  - `ActionView` (action.py), `OrderedUpView`/`OrderedDownView` (action_ordered.py)
- Each has a `*PermissionRequired` variant that adds `CrudViewPermissionRequiredMixin`
- `CrispyModelViewMixin` / `CrispyModelForm` (`crud_views/lib/crispy/`) integrate django-crispy-forms
- `ListViewTableMixin` / `ListViewTableFilterMixin` integrate django-tables2 and django-filter

### Nested (Parent-Child) ViewSets

ViewSets support nesting via `ParentViewSet`. A child ViewSet declares `parent=ParentViewSet(name="parent_viewset_name")`. The parent's PK is included in URL patterns, and querysets are automatically filtered to the parent. `CreateViewParentMixin` auto-sets the parent FK on create.

### Extension packages

- **Workflow** (`crud_views_workflow/lib/`): `WorkflowViewPermissionRequired` renders django-fsm transitions as form actions. `WorkflowModelMixin` adds audit history. Models use `FSMField` + `@transition` decorators with `wf_` prefix.
- **Polymorphic** (`crud_views_polymorphic/lib/`): Provides `PolymorphicCreateSelectView` (content type picker) → `PolymorphicCreateView` (type-specific form) flow. Uses `polymorphic_forms = {ModelClass: FormClass}` mapping.
- **Guardian** (`crud_views_guardian/lib/`): `GuardianViewSet` replaces `ViewSet` and provides per-object permission checking via django-guardian. Views use `GuardianListViewPermissionRequired`, etc.

### Settings

All settings live in `crud_views/lib/settings.py` as a Pydantic model (`CrudViewsSettings`) reading from Django settings with `CRUD_VIEWS_*` prefix. Key settings: `CRUD_VIEWS_EXTENDS` (base template), `CRUD_VIEWS_MANAGE_VIEWS_ENABLED`.

### Django System Checks

`crud_views/checks.py` registers Django system checks that validate ViewSet and CrudView configurations at startup (naming conventions, template existence, required attributes).

### Template Tags

`crud_views/templatetags/crud_views.py` and `crud_views_formsets.py` provide template tags for rendering view components.

## Testing

Tests are in `tests/test1/`. The test project (`tests/test1/conftest.py`) configures Django in-memory with `pytest_configure()`. Test models (Author with UUID PK, Publisher with int PK, Book as child of Publisher, Vehicle as polymorphic, Campaign as workflow) are defined in `tests/test1/app/models.py`.

Test fixtures follow naming convention: `cv_<model>` for ViewSets, `user_<model>_<permission>` for users, `client_user_<model>_<permission>` for logged-in clients.

## Conventions

- All `CrudView` class attributes use `cv_` prefix
- View keys match CRUD operations: `list`, `detail`, `create`, `update`, `delete`, `workflow`, `manage`
- Permission mapping: list/detail→view, create→add, update→change, delete→delete
- Workflow transition methods use `wf_` prefix
- Line length: 120 characters (ruff)
- Quote style: double quotes
- Build system: hatchling
- Version management: bump-my-version (syncs pyproject.toml, `__init__.py`, docs, README)
