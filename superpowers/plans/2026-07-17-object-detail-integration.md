# django-object-detail Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Absorb the external `django-object-detail` package into the crud_views distribution as the optional in-tree extension `crud_views_object_detail`, drop object-detail from core, make core `DetailView` the simple template-driven view, and provide the rich property-display view as `ObjectDetailView`.

**Architecture:** Vendor the object-detail engine (config/resolvers/conf/templatetags/templates) into `src/crud_views_object_detail/`, renamed to crud_views idioms. The rich detail behavior collapses onto a single crud_views-aware `ObjectDetailMixin` (carries `cv_property_display`, resolves groups into context, contributes the E240–E245 checks, and sets the object-detail templates). `ObjectDetailView = ObjectDetailMixin + core DetailView`. Core `crud_views` loses the object-detail dependency; its `DetailView` becomes what `DetailCustomView` is today, and `DetailCustomView` is removed. Polymorphic/guardian detail views become simple; property-display is composed in via `ObjectDetailMixin`.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, Pydantic v2, django-crispy-forms, django-tables2, Bootstrap 5. Build: hatchling. Tests: pytest + pytest-django (quick) / nox (matrix). Lint: ruff.

## Global Constraints

- Line length 120; double quotes; ruff-format runs on pre-commit (Python only — Markdown/HTML/YAML unaffected).
- Conventional-commit messages. Commit with **explicit pathspecs — never `git add -A`** (working tree carries example `db.sqlite3` and other untracked files that must not be committed).
- Quick test loop: `cd tests && pytest <path>`. Full matrix: `task test`. Example smoke tests live under `examples/bootstrap5/` and run with `cd examples/bootstrap5 && pytest`.
- All `CrudView` attributes use the `cv_` prefix. View keys: `list/detail/create/update/delete`. Permission mapping: detail→`view`.
- Extension public API is exposed at `<app>.lib` via lazy PEP 562 `__getattr__` (import-safety convention).
- The vendored app has **no external dependencies** (only `django` + `pydantic`, already core deps): there is **no `[object_detail]` extra**; enabling it is an `INSTALLED_APPS` step only.
- Vendoring source: `../django-object-detail` (checked out locally; still present until archived post-release).
- Settings prefix rename: `OBJECT_DETAIL_*` → `CRUD_VIEWS_OBJECT_DETAIL_*`. Template dir/tag-lib rename: `django_object_detail` → `crud_views_object_detail`.
- Spec: `superpowers/specs/2026-07-17-object-detail-integration-design.md`.

---

### Task 1: Scaffold the extension app — vendor `config.py` + `resolvers.py`, create a dedicated test app, wire packaging

**Files:**
- Create: `src/crud_views_object_detail/__init__.py`
- Create: `src/crud_views_object_detail/apps.py`
- Create: `src/crud_views_object_detail/lib/__init__.py`
- Create: `src/crud_views_object_detail/lib/config.py`
- Create: `src/crud_views_object_detail/lib/resolvers.py`
- Create: `tests/test1/od_app/__init__.py`, `apps.py`, `models.py` (no `migrations/` package — the test project uses `run_syncdb`, matching `tests/test1/app`)
- Test: `tests/test1/od/__init__.py`, `tests/test1/od/test_config.py`, `tests/test1/od/test_resolvers.py`
- Modify: `tests/test1/conftest.py` (add apps to `INSTALLED_APPS`)
- Modify: `pyproject.toml` (`[tool.hatch.build.targets.wheel].packages`)

**Interfaces:**
- Produces: `crud_views_object_detail.lib.config` — `LinkConfig`, `BadgeConfig`, `PropertyConfig`, `PropertyGroupConfig`, `x(path, **kwargs)`, `parse_property_display(raw) -> list[PropertyGroupConfig]`.
- Produces: `crud_views_object_detail.lib.resolvers` — `FIELD_TYPE_MAP`, `ResolvedProperty`, `ResolvedGroup`, `resolve_property(instance, config, view=None)`, `resolve_group(...)`, `resolve_all(instance, groups, view=None) -> list[ResolvedGroup]`.
- Produces: test app `od_app` with object-detail's test models (used by engine tests in this and later tasks).

- [ ] **Step 1: Create the package skeleton**

```bash
cd /home/alex/projects/alex/django-crud-views
mkdir -p src/crud_views_object_detail/lib
: > src/crud_views_object_detail/__init__.py
```

Write `src/crud_views_object_detail/apps.py`:

```python
from django.apps import AppConfig


class CrudViewsObjectDetailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_object_detail"
    label = "cvod"
    verbose_name = "Crud Views Object Detail"
```

- [ ] **Step 2: Vendor `config.py` and `resolvers.py` with import renames**

```bash
cd /home/alex/projects/alex/django-crud-views
cp ../django-object-detail/django_object_detail/config.py    src/crud_views_object_detail/lib/config.py
cp ../django-object-detail/django_object_detail/resolvers.py src/crud_views_object_detail/lib/resolvers.py
# rename internal package imports
sed -i 's/from django_object_detail\.config/from crud_views_object_detail.lib.config/g' \
    src/crud_views_object_detail/lib/resolvers.py
# verify no stale references remain
grep -rn "django_object_detail" src/crud_views_object_detail/lib/config.py src/crud_views_object_detail/lib/resolvers.py || echo "OK: no stale refs"
```

Expected: `OK: no stale refs`.

- [ ] **Step 3: Write the (partial) public API `lib/__init__.py`**

Only config helpers are safe to export now (resolvers/views come later). Use the lazy pattern from `crud_views_workflow/lib/__init__.py`:

```python
"""Public API surface for crud_views_object_detail (lazy PEP 562 __getattr__)."""

from importlib import import_module

__all__ = [
    "BadgeConfig",
    "LinkConfig",
    "PropertyConfig",
    "PropertyGroupConfig",
    "x",
]

_EXPORTS = {
    "BadgeConfig": ("crud_views_object_detail.lib.config", "BadgeConfig"),
    "LinkConfig": ("crud_views_object_detail.lib.config", "LinkConfig"),
    "PropertyConfig": ("crud_views_object_detail.lib.config", "PropertyConfig"),
    "PropertyGroupConfig": ("crud_views_object_detail.lib.config", "PropertyGroupConfig"),
    "x": ("crud_views_object_detail.lib.config", "x"),
}


def __getattr__(name: str):
    try:
        module_path, attr = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_path), attr)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
```

- [ ] **Step 4: Create the dedicated test-model app `od_app`**

```bash
cd /home/alex/projects/alex/django-crud-views
mkdir -p tests/test1/od_app
: > tests/test1/od_app/__init__.py
cp ../django-object-detail/tests/models.py tests/test1/od_app/models.py
```

Do **not** create a `migrations/` package: the test project (like `tests/test1/app`, which has no migrations) builds schema from model state via `run_syncdb`. A migrations package would suppress that and break table creation.

Write `tests/test1/od_app/apps.py`:

```python
from django.apps import AppConfig


class OdAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.test1.od_app"
    label = "od_app"
```

Inspect `tests/test1/od_app/models.py`; if any model sets an explicit `Meta.app_label`, change it to `od_app` (or remove it so it inherits from `OdAppConfig.label`). No migrations are needed — `run_syncdb` builds the tables.

- [ ] **Step 5: Register both apps in the test settings**

In `tests/test1/conftest.py`, inside the `INSTALLED_APPS` list passed to `settings.configure(...)`, add after the existing `"django_object_detail",` line:

```python
            "crud_views_object_detail",
            "tests.test1.od_app",
```

(Keep `"django_object_detail"` for now — it is removed in Task 7. Both coexist harmlessly.)

- [ ] **Step 6: Port config + resolver tests**

```bash
cd /home/alex/projects/alex/django-crud-views
mkdir -p tests/test1/od
: > tests/test1/od/__init__.py
cp ../django-object-detail/tests/test_config.py    tests/test1/od/test_config.py
cp ../django-object-detail/tests/test_resolvers.py tests/test1/od/test_resolvers.py
# rename package imports in the ported tests
sed -i -E 's/from django_object_detail(\.[a-z_]+)?/from crud_views_object_detail.lib\1/g; s/from tests\.models/from tests.test1.od_app.models/g; s/from \.models/from tests.test1.od_app.models/g' \
    tests/test1/od/test_config.py tests/test1/od/test_resolvers.py
grep -rn "django_object_detail" tests/test1/od/ || echo "OK: no stale refs in tests"
```

Open both ported files and fix any remaining import paths (e.g. `from crud_views_object_detail.lib import x` for the top-level helper, model import path). The helper `x`, `PropertyConfig`, etc. import from `crud_views_object_detail.lib`; `resolve_all`/`FIELD_TYPE_MAP` import from `crud_views_object_detail.lib.resolvers`.

- [ ] **Step 7: Run the ported engine tests**

Run: `cd tests && pytest test1/od/test_config.py test1/od/test_resolvers.py -v`
Expected: PASS (all config + resolver tests green).

- [ ] **Step 8: Add the app to the wheel packages**

In `pyproject.toml`, under `[tool.hatch.build.targets.wheel]`, add `"src/crud_views_object_detail"` to the `packages` list.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views_object_detail/__init__.py src/crud_views_object_detail/apps.py \
        src/crud_views_object_detail/lib/__init__.py src/crud_views_object_detail/lib/config.py \
        src/crud_views_object_detail/lib/resolvers.py \
        tests/test1/od_app tests/test1/od tests/test1/conftest.py pyproject.toml
git commit -m "feat(object_detail): scaffold crud_views_object_detail app; vendor config + resolvers"
```

---

### Task 2: Vendor `conf.py` as the `CrudViewsObjectDetailSettings` pydantic model

**Files:**
- Create: `src/crud_views_object_detail/lib/conf.py`
- Test: `tests/test1/od/test_conf.py`, `tests/test1/od/test_icons.py`

**Interfaces:**
- Produces: `crud_views_object_detail.lib.conf` — singleton `crud_views_object_detail_settings` with fields `template_pack_layout`, `template_pack_types`, `icons_library`, `icons_class`, `icons_type`, `icons_prefix`, `named_icons`, `property_text_newline`; module functions `build_icon_class(icon_name) -> str`, `build_named_icon_class(name) -> str`.

- [ ] **Step 1: Write `lib/conf.py` (pydantic model reading `CRUD_VIEWS_OBJECT_DETAIL_*`)**

```python
from functools import cached_property

from django.conf import settings
from pydantic import BaseModel

_UNSET = object()

ICON_LIBRARY_DEFAULTS = {
    "bootstrap": {"class": "bi", "type": None, "prefix": "bi"},
    "fontawesome": {"class": "fa", "type": "regular", "prefix": "fa"},
}

NAMED_ICONS_DEFAULTS = {
    "bootstrap": {
        "boolean-true": "check-circle-fill",
        "boolean-false": "x-circle-fill",
        "property-detail": "info-circle",
        "text-icon": "journal-text",
    },
    "fontawesome": {
        "boolean-true": "circle-check",
        "boolean-false": "circle-xmark",
        "property-detail": "circle-info",
        "text-icon": "file-lines",
    },
}


def _from_settings(name, default=_UNSET):
    return getattr(settings, name, default)


class CrudViewsObjectDetailSettings(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    @cached_property
    def template_pack_layout(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT")
        return "split-card" if v is _UNSET else v

    @cached_property
    def template_pack_types(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES")
        return "default" if v is _UNSET else v

    @cached_property
    def icons_library(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY")
        return "bootstrap" if v is _UNSET else v

    @cached_property
    def icons_class(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("class", "")

    @cached_property
    def icons_type(self):
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("type")

    @cached_property
    def icons_prefix(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX")
        if v is not _UNSET:
            return v
        return ICON_LIBRARY_DEFAULTS.get(self.icons_library, {}).get("prefix", "")

    @cached_property
    def named_icons(self) -> dict:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS")
        if v is not _UNSET:
            return v
        return NAMED_ICONS_DEFAULTS.get(self.icons_library, {})

    @cached_property
    def property_text_newline(self) -> str:
        v = _from_settings("CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE")
        return "linebreaksbr" if v is _UNSET else v


crud_views_object_detail_settings = CrudViewsObjectDetailSettings()


def build_icon_class(icon_name: str) -> str:
    s = crud_views_object_detail_settings
    base = f"{s.icons_class}-{s.icons_type}" if s.icons_type else s.icons_class
    return f"{base} {s.icons_prefix}-{icon_name}"


def build_named_icon_class(name: str) -> str:
    icon_name = crud_views_object_detail_settings.named_icons.get(name, "")
    if not icon_name:
        return ""
    return build_icon_class(icon_name)
```

Note: `cached_property` means settings are read once per process. Tests that override settings must instantiate a fresh `CrudViewsObjectDetailSettings()` (mirror how the ported tests exercise conf — adjust in Step 3).

- [ ] **Step 2: Verify import**

Run: `cd tests && python -c "import django; from tests.test1 import conftest" 2>/dev/null; cd .. && python -c "from crud_views_object_detail.lib.conf import build_icon_class"`
Expected: no error (module imports; Django settings resolved lazily via the singleton's cached_property on first access).

- [ ] **Step 3: Port conf + icons tests**

```bash
cp ../django-object-detail/tests/test_conf.py  tests/test1/od/test_conf.py
cp ../django-object-detail/tests/test_icons.py tests/test1/od/test_icons.py
sed -i -E 's/from django_object_detail(\.[a-z_]+)?/from crud_views_object_detail.lib\1/g; \
           s/OBJECT_DETAIL_/CRUD_VIEWS_OBJECT_DETAIL_/g' \
    tests/test1/od/test_conf.py tests/test1/od/test_icons.py
```

Open both files. Replace any direct calls to the old `get_layout_pack()`/`get_icons_*()` functions with the new field access (`crud_views_object_detail_settings.template_pack_layout`, etc.) or a freshly-constructed `CrudViewsObjectDetailSettings()` when the test uses `@override_settings`. Keep `build_icon_class` / `build_named_icon_class` assertions unchanged.

- [ ] **Step 4: Run conf + icons tests**

Run: `cd tests && pytest test1/od/test_conf.py test1/od/test_icons.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_object_detail/lib/conf.py tests/test1/od/test_conf.py tests/test1/od/test_icons.py
git commit -m "feat(object_detail): vendor settings as CrudViewsObjectDetailSettings pydantic model"
```

---

### Task 3: Vendor template tags + all templates (renamed), port templatetag + layout-pack tests

**Files:**
- Create: `src/crud_views_object_detail/templatetags/__init__.py`
- Create: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`
- Create: `src/crud_views_object_detail/templates/crud_views_object_detail/**` (whole tree)
- Test: `tests/test1/od/test_templatetags.py`, `tests/test1/od/test_layout_packs.py`, `tests/test1/od/templates/test_custom_value.html`

**Interfaces:**
- Produces: template-tag library `{% load crud_views_object_detail %}` with tags `render_object_detail`, `render_group`, `render_property`, `render_property_value` and filters `icon_class`, `named_icon_class`.
- Produces: templates under `crud_views_object_detail/layouts/<pack>/…` and `crud_views_object_detail/types/default/…`.

- [ ] **Step 1: Copy the template tree and rename the directory**

```bash
cd /home/alex/projects/alex/django-crud-views
mkdir -p src/crud_views_object_detail/templates
cp -r ../django-object-detail/django_object_detail/templates/django_object_detail \
      src/crud_views_object_detail/templates/crud_views_object_detail
# rename all in-template references to the old dir + tag lib
grep -rl "django_object_detail" src/crud_views_object_detail/templates | while read f; do
  sed -i 's#django_object_detail#crud_views_object_detail#g' "$f"
done
sed -i 's/{% load object_detail %}/{% load crud_views_object_detail %}/g' \
    $(grep -rl "load object_detail" src/crud_views_object_detail/templates 2>/dev/null) 2>/dev/null || true
grep -rn "django_object_detail\|load object_detail" src/crud_views_object_detail/templates || echo "OK: templates clean"
```

Expected: `OK: templates clean`.

- [ ] **Step 2: Vendor the template-tag module (renamed)**

```bash
mkdir -p src/crud_views_object_detail/templatetags
: > src/crud_views_object_detail/templatetags/__init__.py
cp ../django-object-detail/django_object_detail/templatetags/object_detail.py \
   src/crud_views_object_detail/templatetags/crud_views_object_detail.py
```

Then edit `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`:
- Replace the conf import block:
  `from django_object_detail.conf import (build_icon_class, build_named_icon_class, get_layout_pack, get_property_text_newline, get_types_pack)`
  →
  `from crud_views_object_detail.lib.conf import build_icon_class, build_named_icon_class, crud_views_object_detail_settings`
- Replace `from django_object_detail.config import parse_property_display` → `from crud_views_object_detail.lib.config import parse_property_display`
- Replace `from django_object_detail.resolvers import ResolvedGroup, resolve_all` → `from crud_views_object_detail.lib.resolvers import ResolvedGroup, resolve_all`
- Replace every `get_layout_pack()` → `crud_views_object_detail_settings.template_pack_layout`
- Replace every `get_types_pack()` → `crud_views_object_detail_settings.template_pack_types`
- Replace `get_property_text_newline()` → `crud_views_object_detail_settings.property_text_newline`
- Replace every `select_template` path prefix `django_object_detail/` → `crud_views_object_detail/`

Verify:
```bash
grep -n "django_object_detail\|get_layout_pack\|get_types_pack\|get_property_text_newline" \
    src/crud_views_object_detail/templatetags/crud_views_object_detail.py || echo "OK: tag module clean"
```
Expected: `OK: tag module clean`.

- [ ] **Step 3: Port templatetag + layout-pack tests**

```bash
mkdir -p tests/test1/od/templates
cp ../django-object-detail/tests/test_templatetags.py  tests/test1/od/test_templatetags.py
cp ../django-object-detail/tests/test_layout_packs.py  tests/test1/od/test_layout_packs.py
cp ../django-object-detail/tests/templates/test_custom_value.html tests/test1/od/templates/test_custom_value.html
sed -i -E 's/from django_object_detail(\.[a-z_]+)?/from crud_views_object_detail.lib\1/g; \
           s/\{% load object_detail %\}/{% load crud_views_object_detail %}/g; \
           s/django_object_detail\//crud_views_object_detail\//g; \
           s/OBJECT_DETAIL_/CRUD_VIEWS_OBJECT_DETAIL_/g; \
           s/from tests\.models/from tests.test1.od_app.models/g; s/from \.models/from tests.test1.od_app.models/g' \
    tests/test1/od/test_templatetags.py tests/test1/od/test_layout_packs.py
grep -rn "django_object_detail\|load object_detail" tests/test1/od/test_templatetags.py tests/test1/od/test_layout_packs.py || echo "OK"
```

Open both files; fix remaining references (the `{% load %}` inside inline template strings, the custom-template path `test_custom_value.html`, and settings-override key names). Ensure the custom-value template is discoverable — if the tests reference it by a `DIRS` path, register `tests/test1/od/templates` via the test's own inline `Template`/`get_template`, or move the file next to where the test loads it.

- [ ] **Step 4: Run templatetag + layout-pack tests**

Run: `cd tests && pytest test1/od/test_templatetags.py test1/od/test_layout_packs.py -v`
Expected: PASS (all layout packs + type templates render).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_object_detail/templatetags src/crud_views_object_detail/templates \
        tests/test1/od/test_templatetags.py tests/test1/od/test_layout_packs.py tests/test1/od/templates
git commit -m "feat(object_detail): vendor template tags + layout/type templates (renamed)"
```

---

### Task 4: Add `ObjectDetailMixin` (crud_views-idiom) + `ObjectDetailView`, content template, finalize public API

**Files:**
- Create: `src/crud_views_object_detail/lib/mixins.py`
- Create: `src/crud_views_object_detail/lib/views.py`
- Create: `src/crud_views_object_detail/templates/crud_views_object_detail/view_detail.content.html`
- Modify: `src/crud_views_object_detail/lib/__init__.py` (add view + mixin exports)
- Test: `tests/test1/od/test_object_detail_view.py`

**Interfaces:**
- Produces: `crud_views_object_detail.lib.mixins.ObjectDetailMixin` — a crud_views-aware mixin carrying `cv_property_display: list | None = None`, `template_name = "crud_views/view_detail.html"`, `cv_content_template = "crud_views_object_detail/view_detail.content.html"`, `cv_modal_supported = True`; methods `property_display` (property → `cv_property_display`), `get_property_display()`, `get_object_for_detail()`, `get_context_data()` (adds `object_detail_groups`), and classmethod `checks()` yielding E240–E245 then `yield from super().checks()`.
- Produces: `crud_views_object_detail.lib.views.ObjectDetailView` (= `ObjectDetailMixin` + core `DetailCustomView`) and `ObjectDetailViewPermissionRequired` (`cv_permission = "view"`).
- Consumes: core `crud_views.lib.views.DetailCustomView` (Task 7 switches this base to the renamed `DetailView`).

- [ ] **Step 1: Write the failing view test**

`tests/test1/od/test_object_detail_view.py`:

```python
from crud_views_object_detail.lib.config import PropertyConfig


def _error_ids(view_cls):
    return {e.id for chk in view_cls.checks() for e in chk.messages()}


def test_object_detail_view_property_display_adapter():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_property_display = [{"title": "A", "properties": ["x"]}]

    assert V().property_display == [{"title": "A", "properties": ["x"]}]


def test_object_detail_view_missing_display_yields_e240():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"

    assert "viewset.E240" in _error_ids(V)


def test_object_detail_view_property_config_accepted():
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "properties": [PropertyConfig(path="name")]}]

    assert "viewset.E245" not in _error_ids(V)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tests && pytest test1/od/test_object_detail_view.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_object_detail.lib.views`).

- [ ] **Step 3: Write `lib/mixins.py`**

Base the group-resolution logic on `../django-object-detail/django_object_detail/views.py`, but make it crud_views-aware (reads `cv_property_display`, contributes checks, sets templates). Move the E240–E245 logic verbatim from `src/crud_views/lib/views/detail.py`:

```python
from __future__ import annotations

from typing import Iterable

from crud_views.lib.check import Check, CheckAttribute, CheckExpression
from crud_views_object_detail.lib.config import PropertyConfig, PropertyGroupConfig, parse_property_display
from crud_views_object_detail.lib.resolvers import resolve_all


class ObjectDetailMixin:
    """Adds resolved object-detail property groups to a crud_views detail view.

    Set ``cv_property_display`` as a list of group dicts (the DSL accepted by
    ``parse_property_display``). Resolved groups land in the template context as
    ``object_detail_groups``.
    """

    template_name = "crud_views/view_detail.html"
    cv_content_template = "crud_views_object_detail/view_detail.content.html"
    cv_modal_supported = True

    cv_property_display: list | None = None

    @property
    def property_display(self):
        return self.cv_property_display

    def get_property_display(self) -> list[PropertyGroupConfig]:
        raw = self.property_display
        if raw is None:
            return []
        if raw and isinstance(raw[0], PropertyGroupConfig):
            return raw
        return parse_property_display(raw)

    def get_object_for_detail(self):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = self.get_property_display()
        if groups:
            instance = self.get_object_for_detail()
            context["object_detail_groups"] = resolve_all(instance, groups, view=self)
        return context

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield CheckAttribute(context=cls, id="E240", attribute="cv_property_display")
        pd = cls.cv_property_display
        if pd is not None:
            yield CheckExpression(
                context=cls, id="E241", expression=isinstance(pd, list),
                msg="cv_property_display must be a list",
            )
            if isinstance(pd, list):
                for i, group in enumerate(pd):
                    if isinstance(group, PropertyGroupConfig):
                        continue
                    yield CheckExpression(
                        context=cls, id="E242",
                        expression=isinstance(group, dict) and "title" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'title' key",
                    )
                    yield CheckExpression(
                        context=cls, id="E243",
                        expression=isinstance(group, dict) and "properties" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'properties' key",
                    )
                    if isinstance(group, dict) and "properties" in group:
                        props = group["properties"]
                        yield CheckExpression(
                            context=cls, id="E244", expression=isinstance(props, list),
                            msg=f"cv_property_display[{i}]['properties'] must be a list",
                        )
                        if isinstance(props, list):
                            for j, prop in enumerate(props):
                                yield CheckExpression(
                                    context=cls, id="E245",
                                    expression=isinstance(prop, (str, dict, PropertyConfig)),
                                    msg=f"cv_property_display[{i}]['properties'][{j}] must be a str, dict, or PropertyConfig",
                                )
        yield from super().checks()  # noqa
```

- [ ] **Step 4: Write `lib/views.py`**

```python
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailCustomView  # Task 7 switches this to the renamed DetailView
from crud_views_object_detail.lib.mixins import ObjectDetailMixin


class ObjectDetailView(ObjectDetailMixin, DetailCustomView):
    pass


class ObjectDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, ObjectDetailView):
    cv_permission = "view"
```

- [ ] **Step 5: Move the content template into the extension**

```bash
cp src/crud_views/templates/crud_views/view_detail.content.html \
   src/crud_views_object_detail/templates/crud_views_object_detail/view_detail.content.html
sed -i 's/{% load object_detail %}/{% load crud_views_object_detail %}/' \
   src/crud_views_object_detail/templates/crud_views_object_detail/view_detail.content.html
```

Confirm the file now reads:
```django
{% load crud_views_object_detail %}
{% if object_detail_groups %}
    {% render_object_detail object object_detail_groups %}
{% endif %}
```

- [ ] **Step 6: Finalize the public API `lib/__init__.py`**

Extend `__all__` and `_EXPORTS` with (views are lazy — they import core `crud_views` view classes):

```python
    "ObjectDetailMixin",
    "ObjectDetailView",
    "ObjectDetailViewPermissionRequired",
```
```python
    "ObjectDetailMixin": ("crud_views_object_detail.lib.mixins", "ObjectDetailMixin"),
    "ObjectDetailView": ("crud_views_object_detail.lib.views", "ObjectDetailView"),
    "ObjectDetailViewPermissionRequired": ("crud_views_object_detail.lib.views", "ObjectDetailViewPermissionRequired"),
```

- [ ] **Step 7: Run the view tests**

Run: `cd tests && pytest test1/od/test_object_detail_view.py -v`
Expected: PASS.

- [ ] **Step 8: Run the whole object_detail engine suite (regression)**

Run: `cd tests && pytest test1/od/ -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views_object_detail/lib/mixins.py src/crud_views_object_detail/lib/views.py \
        src/crud_views_object_detail/lib/__init__.py \
        src/crud_views_object_detail/templates/crud_views_object_detail/view_detail.content.html \
        tests/test1/od/test_object_detail_view.py
git commit -m "feat(object_detail): add ObjectDetailMixin + ObjectDetailView with cv_property_display + E240-E245 checks"
```

---

### Task 5: Flip polymorphic & guardian detail bases to simple; migrate their rich consumers to compose `ObjectDetailMixin`

At this point core rich `DetailView` still exists. This task makes polymorphic/guardian detail views simple and migrates every polymorphic/guardian consumer that used `cv_property_display` to compose `ObjectDetailMixin`. Suite stays green because core rich `DetailView` is untouched here.

**Files:**
- Modify: `src/crud_views_polymorphic/lib/detail.py`
- Modify: `src/crud_views_guardian/lib/views.py`
- Modify: `tests/test1/app/views.py` (`VehicleDetailView`, `GuardianAuthorDetailView`, `GuardianPublisherDetailView`, `GuardianBookDetailView`)
- Modify: `examples/bootstrap5/polymorphic_demo/views.py` (`VehicleDetailView`)
- Modify: `examples/bootstrap5/guardian_demo/views.py` (`DocumentDetailView`)

**Interfaces:**
- Consumes: `ObjectDetailMixin`, `ObjectDetailViewPermissionRequired` from `crud_views_object_detail.lib`.
- Produces: `PolymorphicDetailView` / `PolymorphicDetailViewPermissionRequired` now extend core **simple** detail; guardian detail views now simple.

- [ ] **Step 1: Point polymorphic detail at the simple base**

In `src/crud_views_polymorphic/lib/detail.py`, change the import and base:

```python
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailCustomView
from .utils import PolymorphicCrudViewMixin


class PolymorphicDetailView(PolymorphicCrudViewMixin, DetailCustomView):
    pass


class PolymorphicDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDetailView):
    cv_permission = "view"
```

- [ ] **Step 2: Point guardian detail at the simple base**

In `src/crud_views_guardian/lib/views.py`:
- Change the import `DetailViewPermissionRequired` → `DetailCustomViewPermissionRequired` is **already imported**; make `GuardianDetailViewPermissionRequired` compose the *custom* (simple) base:

```python
class GuardianDetailViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailCustomViewPermissionRequired
):
    pass
```

Leave `GuardianDetailCustomViewPermissionRequired` as-is for now (removed in Task 7). Remove the now-unused `DetailViewPermissionRequired` from the import list at the top of the file **only if** no other class references it (grep first).

- [ ] **Step 3: Migrate polymorphic/guardian rich consumers to compose `ObjectDetailMixin`**

In each file below, add `from crud_views_object_detail.lib import ObjectDetailMixin` and prepend the mixin to the class bases (the mixin's `cv_property_display`, templates, and checks then apply):

- `tests/test1/app/views.py`:
  - `class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):`
  - `class GuardianAuthorDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):`
  - `class GuardianPublisherDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):`
  - `class GuardianBookDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):`
- `examples/bootstrap5/polymorphic_demo/views.py`: `class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):`
- `examples/bootstrap5/guardian_demo/views.py`: `class DocumentDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):`

Their `cv_property_display = [...]` bodies stay unchanged.

- [ ] **Step 4: Run polymorphic + guardian tests**

Run: `cd tests && pytest test1/ -k "polymorphic or guardian or Vehicle or Guardian" -v`
Expected: PASS.

- [ ] **Step 5: Run example smoke tests for the two apps**

Run: `cd examples/bootstrap5 && pytest polymorphic_demo guardian_demo -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_polymorphic/lib/detail.py src/crud_views_guardian/lib/views.py \
        tests/test1/app/views.py examples/bootstrap5/polymorphic_demo/views.py \
        examples/bootstrap5/guardian_demo/views.py
git commit -m "refactor(detail): polymorphic/guardian detail views become simple; compose ObjectDetailMixin for property-display"
```

---

### Task 6: Migrate all remaining rich `DetailView` consumers → `ObjectDetailView`

Mechanical migration of the plain (non-poly/non-guardian) consumers. Transformation rule: replace the import of `DetailViewPermissionRequired` (from `crud_views.lib.views`) with `ObjectDetailViewPermissionRequired` (from `crud_views_object_detail.lib`), and the class base `DetailViewPermissionRequired` → `ObjectDetailViewPermissionRequired`. Non-permission `DetailView` → `ObjectDetailView` likewise. After this task, core rich `DetailView` has zero references (still exists; removed in Task 7).

**Files (each edited then tested):**
- Modify: `tests/test1/app/views.py` — `AuthorDetailView`, `AuthorWideCardDetailView`, `PublisherDetailView`, `BookDetailView`, `ContractDetailView`, `CampaignDetailView`, `AuthorModalDetailView`
- Modify: `tests/test1/test_detail_view.py`, `tests/test1/test_modal.py`, `tests/test1/test_readme_snippet.py`
- Modify: `examples/bootstrap5/library/views.py` (`AuthorDetailView`, `BookDetailView`), `nested/views.py` (`CompanyDetailView`, `DepartmentDetailView`, `EmployeeDetailView`, `OfficeDetailView`), `formsets/views.py` (`QuestionnaireDetailView`), `showcase/views.py` (`RecipeDetailView`), `workflow/views.py` (`CampaignDetailView`)
- Modify: `README.md` snippet (if it uses `DetailViewPermissionRequired` with `cv_property_display`)

**Interfaces:**
- Consumes: `crud_views_object_detail.lib.ObjectDetailView`, `ObjectDetailViewPermissionRequired`.

- [ ] **Step 1: Migrate the test app views**

In `tests/test1/app/views.py`:
- Add import: `from crud_views_object_detail.lib import ObjectDetailView, ObjectDetailViewPermissionRequired`
- Remove `DetailViewPermissionRequired` from the `from crud_views.lib.views import (...)` block **iff** unused afterward (grep).
- Change bases: `AuthorDetailView`, `AuthorWideCardDetailView`, `PublisherDetailView`, `BookDetailView`, `ContractDetailView`, `CampaignDetailView`, `AuthorModalDetailView` → base `ObjectDetailViewPermissionRequired`.
- `AuthorCustomDetailView(DetailCustomViewPermissionRequired)` stays unchanged (it is the simple/custom case; renamed to `DetailViewPermissionRequired` in Task 7).

- [ ] **Step 2: Update the detail-view tests**

In `tests/test1/test_detail_view.py`:
- Change the top import `from django_object_detail import PropertyConfig` → `from crud_views_object_detail.lib import PropertyConfig`.
- Replace every `from crud_views.lib.views.detail import DetailView` → `from crud_views_object_detail.lib.views import ObjectDetailView` and every local `class …(DetailView)` → `class …(ObjectDetailView)`.
- The `AuthorDetailView` / `CampaignDetailView` imports (`from tests.test1.app.views import …`) stay — those classes are now `ObjectDetailView`-based and still expose the same checks.

In `tests/test1/test_modal.py`: the test at line ~65 asserts DetailView renders object-detail groups in the modal; update any reference to the concrete class to `AuthorModalDetailView` (now `ObjectDetailViewPermissionRequired`). No behavior change expected.

In `tests/test1/test_readme_snippet.py`: change import + base of `ReadmeAuthorDetail` to `ObjectDetailViewPermissionRequired`.

- [ ] **Step 3: Run the affected test modules**

Run: `cd tests && pytest test1/test_detail_view.py test1/test_modal.py test1/test_readme_snippet.py -v`
Expected: PASS.

- [ ] **Step 4: Migrate the example apps**

Apply the same transformation in each example `views.py` (import from `crud_views_object_detail.lib`, base → `ObjectDetailViewPermissionRequired`):
`library/views.py`, `nested/views.py`, `formsets/views.py`, `showcase/views.py`, `workflow/views.py`.

- [ ] **Step 5: Run example smoke tests**

Run: `cd examples/bootstrap5 && pytest library nested formsets showcase workflow -v`
Expected: PASS.

- [ ] **Step 6: Update the README snippet**

If `README.md` contains a detail-view snippet using `DetailViewPermissionRequired` + `cv_property_display`, update it to import `ObjectDetailViewPermissionRequired` from `crud_views_object_detail.lib` and note the `crud_views_object_detail` `INSTALLED_APPS` entry. Verify with the README snippet test:
Run: `cd tests && pytest test1/test_readme_snippet.py -v`
Expected: PASS.

- [ ] **Step 7: Confirm core rich DetailView is now unreferenced**

```bash
grep -rn "cv_property_display" src/crud_views/ && echo "UNEXPECTED: core still references property display" || echo "OK: core clean"
grep -rn "import DetailView\b\|DetailViewPermissionRequired" src/ examples/ tests/ --include=*.py \
  | grep -v "crud_views_object_detail\|ObjectDetail" | grep -v "PolymorphicDetail\|GuardianDetail"
```
Expected: `OK: core clean`; the second grep shows only definitions in core (`detail.py`, `__init__.py`) and any residual — investigate any consumer hit before proceeding.

- [ ] **Step 8: Full suite regression**

Run: `cd tests && pytest -q`
Expected: PASS (1 skip acceptable).

- [ ] **Step 9: Commit**

```bash
git add tests/test1/app/views.py tests/test1/test_detail_view.py tests/test1/test_modal.py \
        tests/test1/test_readme_snippet.py \
        examples/bootstrap5/library/views.py examples/bootstrap5/nested/views.py \
        examples/bootstrap5/formsets/views.py examples/bootstrap5/showcase/views.py \
        examples/bootstrap5/workflow/views.py README.md
git commit -m "refactor(detail): migrate all rich-detail consumers to ObjectDetailView"
```

---

### Task 7: Core flip — rename `DetailCustomView` → `DetailView`, delete the old rich `DetailView`, remove object-detail from core

Now core rich `DetailView` is unused. Make core `DetailView` the simple view (rename from `DetailCustomView`), delete the old rich view module, retarget the extension + poly/guardian bases at the renamed class, migrate the `DetailCustomView` consumers, and drop the external dependency.

**Files:**
- Modify: `src/crud_views/lib/views/detail_custom.py` → renamed class content becomes `DetailView`
- Delete: old rich `src/crud_views/lib/views/detail.py` content (replace with the simple view) — see Step 1
- Modify: `src/crud_views/lib/views/__init__.py`
- Modify: `src/crud_views_object_detail/lib/views.py` (base → `DetailView`)
- Modify: `src/crud_views_polymorphic/lib/detail.py` (base → `DetailView`)
- Modify: `src/crud_views_guardian/lib/views.py` (remove `GuardianDetailCustomViewPermissionRequired`; base → `DetailViewPermissionRequired`)
- Modify: `tests/test1/app/views.py` (`AuthorCustomDetailView`), `tests/test1/app/resources.py`, `examples/bootstrap5/resources/views.py`
- Modify: `pyproject.toml` (remove `django-object-detail` dep), `tests/test1/conftest.py` + `examples/bootstrap5/project/settings.py` (remove `django_object_detail` from `INSTALLED_APPS`)
- Modify: `docs/development/stability.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces: core `crud_views.lib.views.DetailView` = simple template-driven view (== old `DetailCustomView`); `DetailViewPermissionRequired` (`cv_permission="view"`). `DetailCustomView` no longer exists.

- [ ] **Step 1: Make core `detail.py` the simple view**

Replace the entire contents of `src/crud_views/lib/views/detail.py` with the old `DetailCustomView` definition (renamed):

```python
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DetailView(CrudView, generic.DetailView):
    template_name = "crud_views/view_detail_custom.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions

    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    cv_icon_action = "fa-regular fa-eye"


class DetailViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailView):
    cv_permission = "view"
```

- [ ] **Step 2: Delete `detail_custom.py` and fix exports**

```bash
git rm src/crud_views/lib/views/detail_custom.py
```

In `src/crud_views/lib/views/__init__.py`:
- Remove the line `from .detail_custom import DetailCustomView, DetailCustomViewPermissionRequired`.
- Remove `"DetailCustomView"` and `"DetailCustomViewPermissionRequired"` from `__all__`.
- Keep `from .detail import DetailView, DetailViewPermissionRequired`.

- [ ] **Step 3: Retarget the extension + poly/guardian at the renamed core `DetailView`**

- `src/crud_views_object_detail/lib/views.py`: change import `from crud_views.lib.views import DetailCustomView` → `from crud_views.lib.views import DetailView`; base `class ObjectDetailView(ObjectDetailMixin, DetailView):`.
- `src/crud_views_polymorphic/lib/detail.py`: change `from crud_views.lib.views import DetailCustomView` → `from crud_views.lib.views import DetailView`; base `class PolymorphicDetailView(PolymorphicCrudViewMixin, DetailView):`.
- `src/crud_views_guardian/lib/views.py`:
  - In the import block change `DetailCustomViewPermissionRequired` → `DetailViewPermissionRequired` (and drop the `DetailCustom` name).
  - `GuardianDetailViewPermissionRequired` composes `... DetailViewPermissionRequired`.
  - **Delete** the `GuardianDetailCustomViewPermissionRequired` class.

- [ ] **Step 4: Migrate the former `DetailCustomView` consumers → `DetailView`**

- `tests/test1/app/views.py`: `AuthorCustomDetailView(DetailCustomViewPermissionRequired)` → `DetailViewPermissionRequired`; update the import (remove `DetailCustomViewPermissionRequired`, ensure `DetailViewPermissionRequired` imported from `crud_views.lib.views`).
- `tests/test1/app/resources.py`: `S3FileDetailView`, `PublisherFileDetailView` — `DetailCustomViewPermissionRequired` → `DetailViewPermissionRequired`; fix import.
- `examples/bootstrap5/resources/views.py`: `S3FileDetailView` — same swap; fix import.
- Any references to `GuardianDetailCustomViewPermissionRequired` in tests/examples → `GuardianDetailViewPermissionRequired` (grep to find):
```bash
grep -rn "DetailCustom" src/ tests/ examples/ docs/ --include=*.py --include=*.md
```
Resolve every hit.

- [ ] **Step 5: Drop object-detail from core packaging + installed apps**

- `pyproject.toml`: remove the `"django-object-detail (>=0.1.7)",` line from `[project.dependencies]`.
- `tests/test1/conftest.py`: remove `"django_object_detail",` from `INSTALLED_APPS` (keep `"crud_views_object_detail"` and `"tests.test1.od_app"`).
- `examples/bootstrap5/project/settings.py`: replace `"django_object_detail",` with `"crud_views_object_detail",`.

- [ ] **Step 6: Update stability docs + CHANGELOG**

- `docs/development/stability.md`: remove `DetailCustomView` from the stable-list line; add a note that rich detail is `ObjectDetailView` in `crud_views_object_detail`.
- `CHANGELOG.md` under `## [Unreleased]`, add a `### Changed` / `### Removed` block:

```markdown
### Changed
- Rich property-display detail moved to the new optional `crud_views_object_detail` app as `ObjectDetailView`. Core `DetailView` is now the simple template-driven view (formerly `DetailCustomView`). Add `crud_views_object_detail` to `INSTALLED_APPS` and migrate `DetailView` + `cv_property_display` usages to `ObjectDetailView` (`from crud_views_object_detail.lib import ObjectDetailView`). Compose `ObjectDetailMixin` for polymorphic/guardian detail views that need property display.
- Object-detail settings renamed `OBJECT_DETAIL_*` → `CRUD_VIEWS_OBJECT_DETAIL_*`.

### Removed
- `DetailCustomView` / `DetailCustomViewPermissionRequired` (use `DetailView` / `DetailViewPermissionRequired`).
- `GuardianDetailCustomViewPermissionRequired` (use `GuardianDetailViewPermissionRequired`).
- External `django-object-detail` dependency (vendored in-tree).
```

- [ ] **Step 7: Full suite + import-safety regression**

Run: `cd tests && pytest -q`
Expected: PASS (1 skip acceptable).

Run: `cd tests && pytest test1/test_import_safety.py -v` (extend it if present to import `crud_views_object_detail.lib` before `django.setup()`; the config helpers must resolve without importing `lib.views`).
Expected: PASS.

- [ ] **Step 8: Example suite regression**

Run: `cd examples/bootstrap5 && pytest -q`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views/lib/views/detail.py src/crud_views/lib/views/__init__.py \
        src/crud_views_object_detail/lib/views.py src/crud_views_polymorphic/lib/detail.py \
        src/crud_views_guardian/lib/views.py tests/test1/app/views.py tests/test1/app/resources.py \
        examples/bootstrap5/resources/views.py pyproject.toml tests/test1/conftest.py \
        examples/bootstrap5/project/settings.py docs/development/stability.md CHANGELOG.md
git rm --cached src/crud_views/lib/views/detail_custom.py 2>/dev/null || true
git commit -m "refactor(detail)!: core DetailView is now the simple view; remove DetailCustomView and object-detail dep"
```

---

### Task 8: Documentation integration

**Files:**
- Create: `docs/reference/object_detail_view.md`
- Create: `docs/getting_started/object_detail/*` (configuration, links, badges, layout_packs) or `docs/reference/object_detail/*` — choose the reference area
- Create: `docs/reference/object_detail_field_types.md`, `docs/reference/object_detail_settings.md`
- Create: `docs/**/screenshots/*` (7 layout PNGs)
- Modify: `docs/reference/detail_view.md`, `docs/reference/.pages`, `docs/reference/index.md`, `docs/reference/modals.md`, `docs/reference/polymorphic_view.md`, `docs/reference/guardian.md`
- Delete: `docs/reference/detail_custom_view.md`

**Interfaces:** documentation only — no code contracts.

- [ ] **Step 1: Copy object-detail docs pages + screenshots**

```bash
cd /home/alex/projects/alex/django-crud-views
cp ../django-object-detail/docs/reference/field_types.md docs/reference/object_detail_field_types.md
cp ../django-object-detail/docs/reference/settings.md    docs/reference/object_detail_settings.md
cp ../django-object-detail/docs/getting_started/configuration.md docs/reference/object_detail_configuration.md
cp ../django-object-detail/docs/getting_started/links.md         docs/reference/object_detail_links.md
cp ../django-object-detail/docs/getting_started/badges.md        docs/reference/object_detail_badges.md
cp ../django-object-detail/docs/getting_started/layout_packs.md  docs/reference/object_detail_layout_packs.md
mkdir -p docs/reference/screenshots
cp ../django-object-detail/docs/screenshots/*.png docs/reference/screenshots/
```

- [ ] **Step 2: Rename terminology inside the copied docs**

```bash
for f in docs/reference/object_detail_*.md; do
  sed -i 's/django-object-detail/crud_views_object_detail/g; s/django_object_detail/crud_views_object_detail/g; \
          s/OBJECT_DETAIL_/CRUD_VIEWS_OBJECT_DETAIL_/g; s/{% load object_detail %}/{% load crud_views_object_detail %}/g' "$f"
  sed -i 's#\.\./screenshots/#screenshots/#g; s#screenshots/#screenshots/#g' "$f"
done
grep -rn "django-object-detail\|django_object_detail\|OBJECT_DETAIL_[^C]" docs/reference/object_detail_*.md || echo "OK"
```

Manually fix code examples so imports read `from crud_views_object_detail.lib import x, PropertyConfig, ...` and view examples use `ObjectDetailView` (not the old `ObjectDetailMixin + django.views.generic.DetailView` pattern).

- [ ] **Step 3: Rewrite `docs/reference/detail_view.md`**

Replace its content so it documents **core `DetailView`** as the simple template-driven view (renders `cv_content_template` / a dev-supplied template; no property display), and cross-links to `object_detail_view.md` for property groups. Remove the `property_display`/django-object-detail table sections (those move to `object_detail_view.md`).

- [ ] **Step 4: Write `docs/reference/object_detail_view.md`**

New page documenting `ObjectDetailView` / `ObjectDetailViewPermissionRequired`, the `cv_property_display` DSL (groups, properties as str/dict/`x()`/`PropertyConfig`), links, badges, layout packs, and the compose pattern for guardian/polymorphic (`class Foo(ObjectDetailMixin, GuardianDetailViewPermissionRequired)`). Reuse the migrated tables from the old `detail_view.md` and the copied object-detail pages.

- [ ] **Step 5: Wire nav + fix cross-references**

- `docs/reference/.pages`: replace `detail_custom_view.md` entry; add `detail_view.md`, `object_detail_view.md`, and the `object_detail_*` pages (grouped, e.g. after `detail_view.md`).
- `docs/reference/index.md`: update the DetailView line; add an ObjectDetailView line.
- `docs/reference/modals.md`: the modal-supported list — `ObjectDetailView` (rich) supports modals; keep `DetailView` reference accurate.
- `docs/reference/polymorphic_view.md` and `docs/reference/guardian.md`: update any `cv_property_display` examples to the compose pattern.
- `git rm docs/reference/detail_custom_view.md`.

- [ ] **Step 6: Build docs locally to catch broken links/nav**

Run: `task docs` (mkdocs serve) — or `mkdocs build --strict` if available.
Expected: build succeeds; no missing-file/nav warnings for the new pages.

- [ ] **Step 7: Commit**

```bash
git add docs/reference/*.md docs/reference/.pages docs/reference/screenshots
git rm docs/reference/detail_custom_view.md
git commit -m "docs: integrate object-detail docs; split DetailView (simple) vs ObjectDetailView (rich)"
```

---

### Task 9: Example app `object_detail` — models, seed, viewset with one detail view per theme, nav + index badge

**Files:**
- Create: `examples/bootstrap5/object_detail/__init__.py`, `apps.py`, `models.py`, `seed.py`, `views.py`, `urls.py`, `migrations/__init__.py`, `migrations/0001_initial.py`
- Modify: `examples/bootstrap5/project/settings.py` (`INSTALLED_APPS`), `examples/bootstrap5/project/urls.py` (include), `examples/bootstrap5/project/features.py` (Feature entry + `badge` field), `examples/bootstrap5/project/templates/project/home.html` (render badge)

**Interfaces:**
- Produces: URL names `product-list`, `product-detail-<theme>` for the seven layout packs; landing `product-list`.

- [ ] **Step 1: Write the two models (`Product`, `Supplier`, `Warehouse`)**

`examples/bootstrap5/object_detail/models.py`:

```python
from decimal import Decimal

from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=200, help_text="Supplier company name")
    website = models.URLField(blank=True, help_text="Supplier website")
    rating = models.FloatField(default=0.0, help_text="Supplier rating (0-5)")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.city})"


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, help_text="Product name")
    description = models.TextField(blank=True, help_text="Full description")
    sku = models.SlugField(max_length=40, help_text="Stock keeping unit")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"), help_text="Retail price")
    weight_kg = models.FloatField(default=0.0, help_text="Weight in kilograms")
    stock = models.PositiveIntegerField(default=0, help_text="Units in stock")
    is_active = models.BooleanField(default=True, help_text="Available for sale")
    homepage = models.URLField(blank=True, help_text="Product page")
    release_date = models.DateField(null=True, blank=True, help_text="Release date")
    created_at = models.DateTimeField(default=timezone.now, help_text="Record created")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    warehouse = models.OneToOneField(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="product")
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def margin_label(self) -> str:
        return "premium" if self.price >= Decimal("100") else "standard"

    def stock_status(self) -> str:
        return "in stock" if self.stock > 0 else "out of stock"
```

- [ ] **Step 2: `apps.py`, `urls.py`, `seed.py`**

`apps.py`:
```python
from django.apps import AppConfig


class ObjectDetailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "object_detail"
```

`urls.py`:
```python
from object_detail.views import cv_product

urlpatterns = cv_product.urlpatterns
```

`seed.py` — follow the pattern of `examples/bootstrap5/resources/seed.py` (a `seed()` function creating a Supplier, Warehouse, Tags, and 2–3 Products). Look at that file first and mirror its structure and how it's invoked by the project seed management command (`examples/bootstrap5/project/management/`).

- [ ] **Step 3: Write the viewset with one `ObjectDetailView` per theme**

`examples/bootstrap5/object_detail/views.py`:

```python
from crud_views.lib.views import CreateViewPermissionRequired, ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import BadgeConfig, ObjectDetailViewPermissionRequired, x

from object_detail.models import Product

cv_product = ViewSet(
    model=Product,
    name="product",
    icon_header="fa-regular fa-box",
)

# shared property_display showing default rendering of many field types + traversal + methods
PRODUCT_DISPLAY = [
    {
        "title": "Basics",
        "icon": "box",
        "properties": [
            "name",
            "sku",
            "description",
            x("price"),
            x("weight_kg", title="Weight (kg)"),
            "stock",
            x("is_active", badge=BadgeConfig(color_map={True: "success", False: "secondary"},
                                             label_map={True: "Active", False: "Inactive"}, pill=True)),
            "homepage",
            "release_date",
            "created_at",
        ],
    },
    {
        "title": "Supplier (FK traversal)",
        "icon": "truck",
        "properties": [
            x("supplier", link="product-detail-split-card"),
            x("supplier__name", title="Supplier name"),
            x("supplier__website", title="Supplier website"),
            x("supplier__rating", title="Supplier rating"),
        ],
    },
    {
        "title": "Warehouse (O2O traversal)",
        "icon": "warehouse",
        "properties": [
            x("warehouse__code", title="Warehouse code"),
            x("warehouse__city", title="City"),
            x("warehouse__country", title="Country"),
        ],
    },
    {
        "title": "Tags (M2M) & computed",
        "icon": "tags",
        "properties": [
            "tags",
            x("margin_label", title="Margin"),
            x("stock_status", title="Stock status"),
            x("view_summary", title="Summary (view-computed)"),
        ],
    },
]

THEMES = [
    "split-card", "accordion", "tabs-vertical", "card-rows",
    "list-group-3col", "striped-rows", "table-inline",
]


class ProductListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_product


class ProductCreateView(CreateViewPermissionRequired):
    cv_viewset = cv_product
    cv_form_class = None  # follow library/views.py CreateView pattern for the real form class


def _make_detail_view(theme: str):
    attrs = {
        "cv_viewset": cv_product,
        "cv_key": f"detail-{theme}",
        "cv_path": f"detail-{theme}",
        "cv_object_detail_layout": theme,  # see Step 4 note on per-view layout override
        "cv_property_display": PRODUCT_DISPLAY,
    }

    def view_summary(self, instance):
        return f"{instance.name} — {instance.stock_status()} ({instance.margin_label})"

    attrs["view_summary"] = view_summary
    return type(f"Product{theme.title().replace('-', '')}DetailView", (ObjectDetailViewPermissionRequired,), attrs)


PRODUCT_DETAIL_VIEWS = [_make_detail_view(theme) for theme in THEMES]
```

- [ ] **Step 4: Per-view layout override**

The object-detail layout pack is normally global (`CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT`). To render **all themes in one app**, add a per-view override:
- In `src/crud_views_object_detail/lib/mixins.py`, add attribute `cv_object_detail_layout: str | None = None` and, in `get_context_data`, when set, pass it through so the template tags select that pack. Simplest: set `context["object_detail_layout"] = self.cv_object_detail_layout or crud_views_object_detail_settings.template_pack_layout` and update `render_object_detail`/`render_group`/`render_property` to accept an optional `layout` kwarg (defaulting to the setting) instead of always calling `crud_views_object_detail_settings.template_pack_layout`.
- Add a unit test in `tests/test1/od/test_object_detail_view.py` asserting a view with `cv_object_detail_layout="accordion"` renders the accordion layout marker. Write the test first (RED), then implement (this is a small TDD cycle inside this step).

Run: `cd tests && pytest test1/od/test_object_detail_view.py -k layout -v`
Expected: PASS after implementing.

Commit this engine change separately:
```bash
git add src/crud_views_object_detail/lib/mixins.py src/crud_views_object_detail/templatetags/crud_views_object_detail.py tests/test1/od/test_object_detail_view.py
git commit -m "feat(object_detail): per-view cv_object_detail_layout override"
```

- [ ] **Step 5: Register the app (settings, urls, nav + badge)**

- `examples/bootstrap5/project/settings.py`: add `"object_detail",` to the example-apps section of `INSTALLED_APPS`.
- `examples/bootstrap5/project/urls.py`: include `object_detail.urls` (mirror how other example apps are included).
- `examples/bootstrap5/project/features.py`: add a `badge: str = ""` field to the `Feature` dataclass, and append a `Feature(app="object_detail", title="Object Detail", badge="NEW", url_name="product-list", icon="fa-regular fa-box", description=..., about=..., look_at=...)` entry.
- `examples/bootstrap5/project/templates/project/home.html`: render the badge in the card title, e.g. after `{{ feature.title }}`:
  `{% if feature.badge %}<span class="badge text-bg-success ms-2">{{ feature.badge }}</span>{% endif %}`

- [ ] **Step 6: Generate the migration**

```bash
cd examples/bootstrap5 && python manage.py makemigrations object_detail
```
Expected: `0001_initial.py` created.

- [ ] **Step 7: Evaluate against the object-detail example for showcase completeness**

Diff the showcases: confirm every important feature from `../django-object-detail/example/catalog/views.py` is represented in `PRODUCT_DISPLAY` — badges (`color`, `color_map`, `color_fn`, `label_map`, `pill`), property `link`, per-type custom `template`, FK traversal, FK→O2O / reverse-O2O traversal, M2M fan-out, model method, and view-computed property. Add any missing showcase (e.g. a `color_fn` badge on `price`, and a custom-template property such as a star-rating on `supplier__rating`) to `PRODUCT_DISPLAY`. Note in an app docstring anything intentionally omitted.

- [ ] **Step 8: Commit**

```bash
git add examples/bootstrap5/object_detail examples/bootstrap5/project/settings.py \
        examples/bootstrap5/project/urls.py examples/bootstrap5/project/features.py \
        examples/bootstrap5/project/templates/project/home.html
git commit -m "docs(examples): add object_detail example app (7 layout themes, nested models, showcases, nav badge)"
```

---

### Task 10: Example app smoke tests

**Files:**
- Create: `examples/bootstrap5/object_detail/tests.py`

**Interfaces:** consumes the seeded data + URL names from Task 9.

- [ ] **Step 1: Write per-theme render tests**

Mirror `examples/bootstrap5/resources/tests.py`. For each theme in `THEMES`, assert the detail URL returns 200 for a logged-in permitted user and the response contains the layout's distinctive marker (reuse the markers asserted in `tests/test1/od/test_layout_packs.py`). Include a list-view 200 test.

```python
import pytest
from django.urls import reverse

from object_detail.views import THEMES


@pytest.mark.django_db
@pytest.mark.parametrize("theme", THEMES)
def test_product_detail_theme_renders(client_admin, seeded_product, theme):
    url = reverse(f"product-detail-{theme}", kwargs={"pk": seeded_product.pk})
    response = client_admin.get(url)
    assert response.status_code == 200
```

Adapt fixture names (`client_admin`, `seeded_product`) to the example project's conftest — inspect `examples/bootstrap5/conftest.py` / existing app tests for the real fixtures and seeding entry point.

- [ ] **Step 2: Run**

Run: `cd examples/bootstrap5 && pytest object_detail -v`
Expected: PASS (all 7 themes + list).

- [ ] **Step 3: Commit**

```bash
git add examples/bootstrap5/object_detail/tests.py
git commit -m "test(examples): smoke-test object_detail app across all layout themes"
```

---

### Task 11: Full-matrix verification + system-check pass

**Files:** none (verification + any fixups surfaced).

- [ ] **Step 1: Run the crud_views system checks against the example project**

Run: `cd examples/bootstrap5 && python manage.py check`
Expected: no errors (E240–E245 now sourced from `crud_views_object_detail`; no stray references to removed views).

- [ ] **Step 2: Full quick suite**

Run: `cd tests && pytest -q`
Expected: PASS (1 skip acceptable).

- [ ] **Step 3: Lint**

Run: `task check && task format`
Expected: clean (ruff auto-fixes applied; re-commit if files changed).

- [ ] **Step 4: Full nox matrix**

Run: `task test`
Expected: green across Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0.

- [ ] **Step 5: Commit any lint/fixups**

```bash
git add -u
git commit -m "chore: lint + fixups for object-detail integration" || echo "nothing to commit"
```

---

### Task 12: Sibling repo `../django-object-detail` — README notice (archive deferred)

**Files:**
- Modify: `../django-object-detail/README.md`

**Interfaces:** none.

- [ ] **Step 1: Prepend an integration/archive notice to the README**

Edit `../django-object-detail/README.md`, adding at the very top:

```markdown
> **⚠️ This project has been integrated into [django-crud-views](https://github.com/jacob-consulting/django-crud-views) as the `crud_views_object_detail` app and is no longer maintained here.**
> Use `pip install django-crud-views` and add `crud_views_object_detail` to `INSTALLED_APPS`.
> See the django-crud-views docs for `ObjectDetailView`. This repository is archived.
```

- [ ] **Step 2: Commit in the sibling repo**

```bash
git -C ../django-object-detail add README.md
git -C ../django-object-detail commit -m "docs: integrated into django-crud-views (crud_views_object_detail); archived"
```

- [ ] **Step 3: Archive is deferred**

Do **not** run `gh repo archive` here. Record for the human: after the django-crud-views release containing this integration ships and is green, run (with explicit confirmation):
```bash
gh repo archive jacob-consulting/django-object-detail
```

---

## Post-plan (human-owned, not a task)

- Version bump + release via the project's bump-my-version + `publish.yml` → PyPI flow (see `superpowers/.../release-process`). This is a breaking change → bump accordingly (pre-1.0 minor).
- After release ships green: archive `jacob-consulting/django-object-detail` (Task 12 Step 3).

## Self-Review notes

- **Spec coverage:** app scaffold+rename (T1–T4) ✓; settings pydantic model (T2) ✓; templatetag/template rename (T3) ✓; mixin+view+public API (T4) ✓; core flip + DetailCustomView removal + dep drop (T5–T7) ✓; polymorphic/guardian ripple (T5,T7) ✓; docs merge + detail split (T8) ✓; example app 7 themes + nested models + showcases + nav badge (T9) + evaluation of source example (T9 Step 7) ✓; smoke tests (T10) ✓; breaking-change CHANGELOG (T7) ✓; sibling README + deferred archive (T12) ✓; test porting (T1–T4) ✓.
- **Spec refinement:** checks live on `ObjectDetailMixin.checks()` (collected via `ViewSet.checks_all()`), not a separate `checks.py`/`apps.ready()` — cleaner and makes composed guardian/polymorphic views validated too. Per-view `cv_object_detail_layout` added (T9 Step 4) to browse all themes in one app.
- **Type consistency:** `cv_property_display` (mixin attr), `resolve_all(instance, groups, view=)`, `ObjectDetailView`/`ObjectDetailViewPermissionRequired`, `crud_views_object_detail_settings.*` fields used consistently across tasks.
