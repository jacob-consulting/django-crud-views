# django-crud-views-extensions: datetimepicker Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the new `django-crud-views-extensions` repository containing the `crud_views_widget_datetimepicker` app: xdsoft jQuery DateTimePicker widgets delivered through django-crud-views' asset registry, with CDN and vendored modes, a vendor command, and pipeline-compatibility verification.

**Architecture:** One distribution (`django-crud-views-extensions`, src layout) shipping one Django app per widget, named as if it already lived in core (`crud_views_widget_*`) so a later merge-back needs zero code changes in consuming projects. The datetimepicker app registers its assets in `AppConfig.ready()` via `crud_views.lib.assets.register_assets`; asset paths come from a Django-free `assets.py` usable from `settings.py` (django-pipeline wiring); vendoring reuses `crud_views.lib.vendor`.

**Tech Stack:** Django 5.x, django-crud-views ≥ the release containing the asset registry (0.11.0), hatchling + uv (src layout), pytest + pytest-django + pytest-mock, django-pipeline (dev/test dependency ONLY).

## Hand-over: context for a fresh session

You are implementing **Workstream 2** of the spec at
`/home/alex/projects/alex/django-crud-views/superpowers/specs/2026-07-14-asset-registry-and-extensions-design.md`.
**Read the spec first.** The widget being extracted is documented with full legacy source in
`/home/alex/projects/alex/gas2gas/docs/integration-xdsoft-datetimepicker.md` (background reading;
this plan contains everything you need inline).

- **Hard prerequisite:** Workstream 1 (plan `2026-07-14-asset-registry.md`) must be implemented in
  `/home/alex/projects/alex/django-crud-views` first. This plan imports `crud_views.lib.assets`
  and `crud_views.lib.vendor` from it. Verify before starting:
  `cd /home/alex/projects/alex/django-crud-views && git log --oneline -5` should show the asset
  registry commits (on `feat/asset-registry` or already merged to `master`). If missing: STOP and
  report back.
- **Repo to CREATE:** `/home/alex/projects/alex/django-crud-views-extensions` (sibling of the core
  checkout — the relative path `../django-crud-views` in `pyproject.toml` depends on this location).
  `git init -b master`.
- **During development** the core dependency resolves via a local editable path
  (`[tool.uv.sources]`); for a real release it becomes a normal PyPI pin `>=0.11.0`.
- **Run tests:** `uv run pytest tests/ -x -q` from the repo root (after `uv sync --extra dev`).
- **Test settings:** no settings module; `tests/conftest.py` calls `settings.configure(...)`
  (same pattern as core's `tests/test1/conftest.py`). If `django.setup()` fails on a missing
  app/module, compare with `/home/alex/projects/alex/django-crud-views/tests/test1/conftest.py`
  and add the missing `INSTALLED_APPS` entry.
- **Check IDs:** core reserved `crud_views.W330`/`W331` (vendor drift, emitted via core's
  `check_vendored`). This repo introduces `crud_views.E332` (vendored without VENDOR_DIR).
- **Upstream library:** jquery-datetimepicker by xdan (https://github.com/xdan/datetimepicker),
  npm package `jquery-datetimepicker`, pinned default version `2.5.21`, served from jsDelivr.
  jQuery itself is a project-provided prerequisite (loaded in the project's base template before
  `{% cv_js %}`) — never registered, never vendored by this app.
- **Follow-up after this plan (not in scope):** gas2gas adds this repo as an editable submodule and
  replaces `viho_ui.widgets.xdsoft` imports with `crud_views_widget_datetimepicker.widgets`.
- **Commit style:** short imperative subjects, `feat:`/`fix:`/`test:`/`docs:` prefixes.

## Global Constraints

- App name and import path are exactly `crud_views_widget_datetimepicker` (merge-back contract — never rename).
- Registry key is exactly `"datetimepicker"`.
- `assets.py` must stay importable without Django configured (no `django.conf` imports) — it is the settings-time API for pipeline users.
- Settings dict name: `CRUD_VIEWS_DATETIMEPICKER` with keys `SOURCE` (`"cdn"`|`"vendored"`, default `"cdn"`), `VERSION` (default `"2.5.21"`), `CDN_BASE` (default `"https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"`), `VENDOR_DIR` (default `None`), `EMIT` (default `True`), `LANG` (default `None` → derive from `LANGUAGE_CODE`), `DEFAULTS` (default `{}`).
- django-pipeline appears ONLY in the dev/test extra, never in runtime dependencies, never imported by package code.
- Config merge precedence (lowest → highest): per-class built-in defaults → `lang` from settings → `DEFAULTS` from settings → per-field `config` argument (with `fix_year` filling only unset keys).
- `init.js` contains no `console.log`.

---

### Task 1: Repository scaffold

**Files:**
- Create: `/home/alex/projects/alex/django-crud-views-extensions/pyproject.toml`
- Create: `.gitignore`, `README.md` (stub)
- Create: `src/crud_views_widget_datetimepicker/__init__.py` (empty)
- Create: `src/crud_views_widget_datetimepicker/apps.py` (stub — completed in Task 5)
- Create: `tests/__init__.py` (empty), `tests/conftest.py`
- Test: `tests/test_app_loads.py`

**Interfaces:**
- Produces: importable app package `crud_views_widget_datetimepicker` with
  `CrudViewsWidgetDatetimepickerConfig`; test harness all later tasks run under.

- [ ] **Step 1: Create the repo and packaging**

```bash
mkdir -p /home/alex/projects/alex/django-crud-views-extensions
cd /home/alex/projects/alex/django-crud-views-extensions
git init -b master
mkdir -p src/crud_views_widget_datetimepicker tests
touch src/crud_views_widget_datetimepicker/__init__.py tests/__init__.py
```

`pyproject.toml`:

```toml
[project]
name = "django-crud-views-extensions"
version = "0.1.0"
description = "Incubator for django-crud-views extension apps (widgets, fields)"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
dependencies = [
    "django-crud-views>=0.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-django",
    "pytest-mock",
    "django-pipeline",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/crud_views_widget_datetimepicker"]

[tool.uv.sources]
# Local development against the sibling checkout; releases use the PyPI pin above.
django-crud-views = { path = "../django-crud-views", editable = true }

[tool.pytest.ini_options]
addopts = "--strict-markers"
```

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
dist/
.pytest_cache/
```

`README.md` stub (completed in Task 8):

```markdown
# django-crud-views-extensions

Incubator for django-crud-views extension apps. Currently:

- `crud_views_widget_datetimepicker` — xdsoft jQuery DateTimePicker widgets
```

- [ ] **Step 2: App stub**

`src/crud_views_widget_datetimepicker/apps.py`:

```python
from django.apps import AppConfig


class CrudViewsWidgetDatetimepickerConfig(AppConfig):
    name = "crud_views_widget_datetimepicker"
    verbose_name = "CRUD Views Widget: xdsoft DateTimePicker"
```

- [ ] **Step 3: Test harness**

`tests/conftest.py`:

```python
from pathlib import Path

import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        BASE_DIR=Path(__file__).resolve().parent,
        SECRET_KEY="django-testing",
        DEBUG=True,
        ALLOWED_HOSTS=[],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.staticfiles",
            "django_tables2",
            "django_object_detail",
            "crispy_forms",
            "crispy_bootstrap5",
            "crud_views.apps.CrudViewsConfig",
            "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                    ],
                },
            }
        ],
        STATIC_URL="/static/",
        LANGUAGE_CODE="de-de",
        USE_TZ=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        CRUD_VIEWS_EXTENDS="base.html",
        CRISPY_ALLOWED_TEMPLATE_PACKS="bootstrap5",
        CRISPY_TEMPLATE_PACK="bootstrap5",
    )
    django.setup()
```

(If `django.setup()` raises about a missing app or import, compare with the core repo's
`tests/test1/conftest.py` and add what is missing — core pulls in its own dependencies.)

`tests/test_app_loads.py`:

```python
from django.apps import apps


def test_app_is_installed():
    config = apps.get_app_config("crud_views_widget_datetimepicker")
    assert config.verbose_name == "CRUD Views Widget: xdsoft DateTimePicker"
```

- [ ] **Step 4: Install and run**

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

Expected: 1 PASS. (First run also verifies the editable path dependency on `../django-crud-views` resolves.)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: scaffold django-crud-views-extensions (src layout, datetimepicker app stub)"
```

---

### Task 2: `assets.py` — Django-free path source of truth

**Files:**
- Create: `src/crud_views_widget_datetimepicker/assets.py`
- Test: `tests/test_assets_paths.py`

**Interfaces:**
- Produces: `APP_LABEL = "crud_views_widget_datetimepicker"`, `INIT_JS`,
  `ALL_FILES` (4-tuple for the vendor command),
  `source_files(version, minified=True) -> dict[str, list[str]]`,
  `cdn_files(cdn_base, version, minified=True) -> dict[str, list[str]]`,
  `bundle(source, version, cdn_base, minified=True) -> dict[str, list[str]]`.
  Task 5 (`apps.py`) consumes `bundle`; Task 6 consumes `ALL_FILES`; pipeline users consume `source_files`.

- [ ] **Step 1: Write the failing tests**

`tests/test_assets_paths.py`:

```python
# Deliberately no Django imports: this module must work at settings-time.
from crud_views_widget_datetimepicker.assets import (
    ALL_FILES,
    APP_LABEL,
    INIT_JS,
    bundle,
    cdn_files,
    source_files,
)

CDN = "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"


def test_source_files_minified():
    files = source_files("2.5.21")
    assert files["js"] == [
        "crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.full.min.js",
        "crud_views_widget_datetimepicker/init.js",
    ]
    assert files["css"] == ["crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.min.css"]


def test_source_files_unminified_for_pipeline():
    files = source_files("2.5.21", minified=False)
    assert files["js"][0].endswith("/jquery.datetimepicker.full.js")
    assert files["js"][1] == INIT_JS  # init.js last: plugin must load first
    assert files["css"] == ["crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.css"]


def test_cdn_files():
    files = cdn_files(CDN, "2.5.21")
    assert files["js"] == [
        "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.full.min.js"
    ]
    assert files["css"] == [
        "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.min.css"
    ]


def test_bundle_cdn_appends_static_init_js():
    b = bundle("cdn", "2.5.21", CDN)
    assert b["js"][0].startswith("https://")
    assert b["js"][1] == INIT_JS


def test_bundle_vendored_equals_source_files():
    assert bundle("vendored", "2.5.21", CDN) == source_files("2.5.21")


def test_all_files_covers_both_variants():
    assert set(ALL_FILES) == {
        "jquery.datetimepicker.full.js",
        "jquery.datetimepicker.full.min.js",
        "jquery.datetimepicker.css",
        "jquery.datetimepicker.min.css",
    }
    assert APP_LABEL == "crud_views_widget_datetimepicker"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_assets_paths.py -v`
Expected: FAIL with `ModuleNotFoundError` / `ImportError`

- [ ] **Step 3: Write the implementation**

`src/crud_views_widget_datetimepicker/assets.py`:

```python
"""Asset path definitions. Django-free by design: importable from settings.py,
so django-pipeline users can build bundles from the same single source of truth
that AppConfig.ready() feeds into the crud_views asset registry."""

APP_LABEL = "crud_views_widget_datetimepicker"
INIT_JS = f"{APP_LABEL}/init.js"

_FILES = {
    # minified: (js, css)
    True: ("jquery.datetimepicker.full.min.js", "jquery.datetimepicker.min.css"),
    False: ("jquery.datetimepicker.full.js", "jquery.datetimepicker.css"),
}

ALL_FILES = (
    "jquery.datetimepicker.full.js",
    "jquery.datetimepicker.full.min.js",
    "jquery.datetimepicker.css",
    "jquery.datetimepicker.min.css",
)


def source_files(version: str, minified: bool = True) -> dict:
    """Static paths for vendored mode / pipeline source_filenames.

    js order matters: the plugin must precede init.js (and jQuery precedes both,
    loaded by the project)."""
    base = f"{APP_LABEL}/{version}"
    js_file, css_file = _FILES[minified]
    return {"js": [f"{base}/{js_file}", INIT_JS], "css": [f"{base}/{css_file}"]}


def cdn_files(cdn_base: str, version: str, minified: bool = True) -> dict:
    """External URLs for CDN mode (plugin files only — init.js is always static)."""
    base = cdn_base.format(version=version).rstrip("/")
    js_file, css_file = _FILES[minified]
    return {"js": [f"{base}/{js_file}"], "css": [f"{base}/{css_file}"]}


def bundle(source: str, version: str, cdn_base: str, minified: bool = True) -> dict:
    """The js/css lists to register for a given SOURCE mode."""
    if source == "cdn":
        files = cdn_files(cdn_base, version, minified)
        return {"js": [*files["js"], INIT_JS], "css": files["css"]}
    return source_files(version, minified)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_assets_paths.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_widget_datetimepicker/assets.py tests/test_assets_paths.py
git commit -m "feat: Django-free asset path source of truth (source_files/cdn_files/bundle)"
```

---

### Task 3: `conf.py` — settings resolution

**Files:**
- Create: `src/crud_views_widget_datetimepicker/conf.py`
- Test: `tests/test_conf.py`

**Interfaces:**
- Consumes: Django settings `CRUD_VIEWS_DATETIMEPICKER`, `LANGUAGE_CODE`.
- Produces: `DatetimepickerConfig(source, version, cdn_base, vendor_dir: Path|None, emit, lang, defaults)`,
  `get_config() -> DatetimepickerConfig`, constants `DEFAULT_VERSION`, `DEFAULT_CDN_BASE`.
  Tasks 4-7 consume `get_config()`.

- [ ] **Step 1: Write the failing tests**

`tests/test_conf.py`:

```python
from pathlib import Path

from crud_views_widget_datetimepicker.conf import DEFAULT_CDN_BASE, DEFAULT_VERSION, get_config


def test_defaults_with_no_setting(settings):
    if hasattr(settings, "CRUD_VIEWS_DATETIMEPICKER"):
        del settings.CRUD_VIEWS_DATETIMEPICKER
    cfg = get_config()
    assert cfg.source == "cdn"
    assert cfg.version == DEFAULT_VERSION
    assert cfg.cdn_base == DEFAULT_CDN_BASE
    assert cfg.vendor_dir is None
    assert cfg.emit is True
    assert cfg.lang == "de"  # derived from LANGUAGE_CODE="de-de" in conftest
    assert cfg.defaults == {}


def test_explicit_settings_win(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "9.9.9",
        "VENDOR_DIR": "/tmp/vendored",
        "EMIT": False,
        "LANG": "en",
        "DEFAULTS": {"step": 15},
    }
    cfg = get_config()
    assert cfg.source == "vendored"
    assert cfg.version == "9.9.9"
    assert cfg.vendor_dir == Path("/tmp/vendored")
    assert cfg.emit is False
    assert cfg.lang == "en"
    assert cfg.defaults == {"step": 15}
```

(`settings` is the pytest-django fixture; it restores overrides after each test.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_conf.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

`src/crud_views_widget_datetimepicker/conf.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from django.conf import settings

DEFAULT_VERSION = "2.5.21"
DEFAULT_CDN_BASE = "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"


@dataclass(frozen=True)
class DatetimepickerConfig:
    source: str = "cdn"
    version: str = DEFAULT_VERSION
    cdn_base: str = DEFAULT_CDN_BASE
    vendor_dir: Optional[Path] = None
    emit: bool = True
    lang: str = "en"
    defaults: dict = field(default_factory=dict)


def get_config() -> DatetimepickerConfig:
    raw = getattr(settings, "CRUD_VIEWS_DATETIMEPICKER", {}) or {}
    vendor_dir = raw.get("VENDOR_DIR")
    lang = raw.get("LANG") or settings.LANGUAGE_CODE.split("-")[0]
    return DatetimepickerConfig(
        source=raw.get("SOURCE", "cdn"),
        version=raw.get("VERSION", DEFAULT_VERSION),
        cdn_base=raw.get("CDN_BASE", DEFAULT_CDN_BASE),
        vendor_dir=Path(vendor_dir) if vendor_dir else None,
        emit=raw.get("EMIT", True),
        lang=lang,
        defaults=dict(raw.get("DEFAULTS", {})),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_conf.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_widget_datetimepicker/conf.py tests/test_conf.py
git commit -m "feat: settings resolution for CRUD_VIEWS_DATETIMEPICKER"
```

---

### Task 4: Widgets

**Files:**
- Create: `src/crud_views_widget_datetimepicker/widgets.py`
- Test: `tests/test_widgets.py`

**Interfaces:**
- Consumes: `get_config()` from Task 3.
- Produces: `DateTimePickerInput(fix_year=None, config=None, **kwargs)`,
  `DatePickerInput(config=None, **kwargs)`, `TimePickerInput(config=None, **kwargs)`.
  Consuming projects assign these in `ModelForm.Meta.widgets`. All render a JSON config in the
  `xdsoft-datetime-config` HTML attribute. **No `Media` classes** — assets come from the registry.

- [ ] **Step 1: Write the failing tests**

`tests/test_widgets.py`:

```python
import json

from crud_views_widget_datetimepicker.widgets import (
    DatePickerInput,
    DateTimePickerInput,
    TimePickerInput,
)


def _config(widget) -> dict:
    return json.loads(widget.attrs["xdsoft-datetime-config"])


def test_datetime_defaults():
    cfg = _config(DateTimePickerInput())
    assert cfg["format"] == "d.m.Y H:i:s"
    assert cfg["lang"] == "de"  # from LANGUAGE_CODE="de-de"


def test_date_defaults():
    cfg = _config(DatePickerInput())
    assert cfg["format"] == "d.m.Y"
    assert cfg["timepicker"] is False


def test_time_defaults():
    cfg = _config(TimePickerInput())
    assert cfg["format"] == "H:i"
    assert cfg["timepicker"] is True
    assert cfg["datepicker"] is False


def test_fix_year():
    cfg = _config(DateTimePickerInput(fix_year=2026))
    assert cfg["minDate"] == "2026-01-01"
    assert cfg["maxDate"] == "2026-12-31"
    assert cfg["yearStart"] == "2026"
    assert cfg["yearEnd"] == "2026"


def test_merge_precedence(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"step": 30, "format": "Y-m-d"}}
    cfg = _config(DateTimePickerInput(config={"step": 15}))
    assert cfg["format"] == "Y-m-d"  # settings DEFAULTS beat built-ins
    assert cfg["step"] == 15         # per-field config beats settings DEFAULTS


def test_no_media_class():
    assert not hasattr(DateTimePickerInput, "Media")


def test_widgets_render_stock_input():
    html = DateTimePickerInput().render("starts_at", None)
    assert "xdsoft-datetime-config" in html
    assert "<input" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_widgets.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

`src/crud_views_widget_datetimepicker/widgets.py`:

```python
"""Form widgets wrapping the xdsoft jQuery DateTimePicker.

The widgets only emit a JSON config in the ``xdsoft-datetime-config`` attribute;
``init.js`` (delivered via the crud_views asset registry) turns matching inputs
into pickers. No Media classes on purpose: assets are page-global via cv_js/cv_css.
"""

import json
from copy import copy

from django.forms import DateInput, DateTimeInput
from django.forms.widgets import TimeInput

from .conf import get_config


class XdsoftConfigMixin:
    """Merge order (lowest to highest): class defaults, lang from settings,
    settings DEFAULTS, per-field config."""

    defaults: dict = {}

    def __init__(self, *args, config=None, **kwargs):
        cfg = get_config()
        merged = copy(self.defaults)
        merged["lang"] = cfg.lang
        merged.update(cfg.defaults)
        merged.update(config or {})
        super().__init__(*args, **kwargs)
        self.attrs["xdsoft-datetime-config"] = json.dumps(merged)


class DateTimePickerInput(XdsoftConfigMixin, DateTimeInput):
    """https://xdsoft.net/jqplugins/datetimepicker/ — for DateTimeField."""

    defaults = {"format": "d.m.Y H:i:s"}

    def __init__(self, *args, fix_year=None, config=None, **kwargs):
        config = dict(config or {})
        if fix_year is not None:
            config.setdefault("minDate", f"{fix_year}-01-01")
            config.setdefault("maxDate", f"{fix_year}-12-31")
            config.setdefault("yearStart", f"{fix_year}")
            config.setdefault("yearEnd", f"{fix_year}")
        super().__init__(*args, config=config, **kwargs)


class DatePickerInput(XdsoftConfigMixin, DateInput):
    """For DateField."""

    defaults = {"format": "d.m.Y", "timepicker": False}


class TimePickerInput(XdsoftConfigMixin, TimeInput):
    """For TimeField."""

    defaults = {"format": "H:i", "timepicker": True, "datepicker": False}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_widgets.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_widget_datetimepicker/widgets.py tests/test_widgets.py
git commit -m "feat: DateTimePickerInput/DatePickerInput/TimePickerInput widgets (registry-only, no Media)"
```

---

### Task 5: App wiring — registration, system checks, init.js

**Files:**
- Modify: `src/crud_views_widget_datetimepicker/apps.py`
- Create: `src/crud_views_widget_datetimepicker/checks.py`
- Create: `src/crud_views_widget_datetimepicker/static/crud_views_widget_datetimepicker/init.js`
- Test: `tests/test_registration.py`

**Interfaces:**
- Consumes: `register_assets` (core Task 1), `check_vendored`/`VendorSpec` (core Task 3),
  `bundle`/`ALL_FILES`/`APP_LABEL` (Task 2), `get_config` (Task 3).
- Produces: registry bundle `key="datetimepicker"`; system check `crud_views.E332`
  (vendored without `VENDOR_DIR`); W330/W331 pass through from core's `check_vendored`.

- [ ] **Step 1: Write the failing tests**

`tests/test_registration.py`:

```python
from django.template import Context, Template

from crud_views_widget_datetimepicker.checks import check_datetimepicker


def test_bundle_registered_at_startup():
    # conftest has no CRUD_VIEWS_DATETIMEPICKER -> CDN mode defaults applied in ready()
    from crud_views.lib.assets import get_registered

    bundles = {b.key: b for b in get_registered()}
    assert "datetimepicker" in bundles
    b = bundles["datetimepicker"]
    assert b.js[0].startswith("https://cdn.jsdelivr.net/npm/jquery-datetimepicker@")
    assert b.js[-1] == "crud_views_widget_datetimepicker/init.js"
    assert b.emit is True


def test_cv_js_includes_picker_assets():
    html = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    assert "jquery.datetimepicker.full.min.js" in html
    assert "/static/crud_views_widget_datetimepicker/init.js" in html
    # ordering: core viewset.js before the picker plugin
    assert html.index("crud_views/js/viewset.js") < html.index("jquery.datetimepicker")


def test_check_vendored_without_vendor_dir_errors(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored"}
    messages = check_datetimepicker()
    assert [m.id for m in messages] == ["crud_views.E332"]


def test_check_vendored_missing_files_warns(settings, tmp_path):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": str(tmp_path)}
    messages = check_datetimepicker()
    assert [m.id for m in messages] == ["crud_views.W330"]


def test_check_cdn_is_silent(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "cdn"}
    assert check_datetimepicker() == []


def test_init_js_content():
    from pathlib import Path

    import crud_views_widget_datetimepicker as pkg

    init = (
        Path(pkg.__file__).parent
        / "static"
        / "crud_views_widget_datetimepicker"
        / "init.js"
    ).read_text()
    assert "xdsoft-datetime-config" in init
    assert "cv:modal:loaded" in init
    assert "console.log" not in init
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_registration.py -v`
Expected: FAIL (`checks` module missing; bundle not registered; init.js missing)

- [ ] **Step 3: Implement `apps.py`**

Replace `src/crud_views_widget_datetimepicker/apps.py`:

```python
from django.apps import AppConfig


class CrudViewsWidgetDatetimepickerConfig(AppConfig):
    name = "crud_views_widget_datetimepicker"
    verbose_name = "CRUD Views Widget: xdsoft DateTimePicker"

    def ready(self):
        from crud_views.lib.assets import register_assets

        from . import checks  # noqa: F401  (import registers the system check)
        from .assets import bundle
        from .conf import get_config

        cfg = get_config()
        b = bundle(cfg.source, cfg.version, cfg.cdn_base)
        register_assets(key="datetimepicker", js=b["js"], css=b["css"], emit=cfg.emit)
```

- [ ] **Step 4: Implement `checks.py`**

`src/crud_views_widget_datetimepicker/checks.py`:

```python
from django.core.checks import Error, register

from crud_views.lib.vendor import VendorSpec, check_vendored

from .assets import ALL_FILES, APP_LABEL
from .conf import get_config


@register("crud_views")
def check_datetimepicker(app_configs=None, **kwargs):
    cfg = get_config()
    if cfg.source != "vendored":
        return []
    if cfg.vendor_dir is None:
        return [
            Error(
                "CRUD_VIEWS_DATETIMEPICKER: SOURCE is 'vendored' but VENDOR_DIR is not set.",
                hint="Set VENDOR_DIR to a project directory that is listed in STATICFILES_DIRS.",
                id="crud_views.E332",
            )
        ]
    spec = VendorSpec(
        key="datetimepicker",
        version=cfg.version,
        base_url=cfg.cdn_base,
        files=ALL_FILES,
        target=cfg.vendor_dir / APP_LABEL / cfg.version,
    )
    return check_vendored(spec)
```

- [ ] **Step 5: Write `init.js`**

`src/crud_views_widget_datetimepicker/static/crud_views_widget_datetimepicker/init.js`:

```javascript
(function () {
    "use strict";

    function initPickers(root) {
        $(root).find("input[xdsoft-datetime-config]").each(function () {
            var config = JSON.parse($(this).attr("xdsoft-datetime-config"));
            if (config.lang) {
                jQuery.datetimepicker.setLocale(config.lang);
            }
            $(this).datetimepicker(config);
        });
    }

    $(function () {
        initPickers(document);

        // crud_views modal support: content is injected after document-ready,
        // core fires cv:modal:loaded on #cv-modal after each injection.
        var modal = document.getElementById("cv-modal");
        if (modal) {
            modal.addEventListener("cv:modal:loaded", function () {
                initPickers(modal);
            });
        }
    });
})();
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/ -v`
Expected: all PASS (including earlier tasks' tests — `ready()` now registers on startup; if a
previously passing test breaks because of the registration, the test is asserting stale state, fix
the test, not the app).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views_widget_datetimepicker/apps.py src/crud_views_widget_datetimepicker/checks.py src/crud_views_widget_datetimepicker/static tests/test_registration.py
git commit -m "feat: register datetimepicker assets on app ready; system checks; init.js with modal re-init"
```

---

### Task 6: Vendor management command

**Files:**
- Create: `src/crud_views_widget_datetimepicker/management/__init__.py` (empty)
- Create: `src/crud_views_widget_datetimepicker/management/commands/__init__.py` (empty)
- Create: `src/crud_views_widget_datetimepicker/management/commands/cv_vendor_datetimepicker.py`
- Test: `tests/test_vendor_command.py`

**Interfaces:**
- Consumes: `vendor`/`VendorSpec` from core, `ALL_FILES`/`APP_LABEL` (Task 2), `get_config` (Task 3).
- Produces: `manage.py cv_vendor_datetimepicker` — downloads the four pinned files into
  `VENDOR_DIR/crud_views_widget_datetimepicker/<version>/`.

- [ ] **Step 1: Write the failing tests**

`tests/test_vendor_command.py`:

```python
import json

import pytest
from django.core.management import CommandError, call_command

from crud_views.lib.vendor import STAMP_NAME


def test_command_requires_vendor_dir(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored"}
    with pytest.raises(CommandError, match="VENDOR_DIR"):
        call_command("cv_vendor_datetimepicker")


def test_command_vendors_all_files(settings, tmp_path, mocker):
    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "2.5.21",
        "VENDOR_DIR": str(tmp_path),
    }
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    call_command("cv_vendor_datetimepicker")

    target = tmp_path / "crud_views_widget_datetimepicker" / "2.5.21"
    names = sorted(p.name for p in target.iterdir())
    assert names == sorted(
        [
            STAMP_NAME,
            "jquery.datetimepicker.css",
            "jquery.datetimepicker.full.js",
            "jquery.datetimepicker.full.min.js",
            "jquery.datetimepicker.min.css",
        ]
    )
    assert json.loads((target / STAMP_NAME).read_text())["version"] == "2.5.21"


def test_vendored_paths_match_source_files(settings, tmp_path, mocker):
    """Guard: what the command writes is exactly what source_files() points at."""
    from crud_views_widget_datetimepicker.assets import source_files

    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "2.5.21",
        "VENDOR_DIR": str(tmp_path),
    }
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    call_command("cv_vendor_datetimepicker")

    for minified in (True, False):
        files = source_files("2.5.21", minified=minified)
        for static_path in [*files["js"], *files["css"]]:
            if static_path.endswith("init.js"):
                continue  # init.js ships inside the app's static/, not VENDOR_DIR
            assert (tmp_path / static_path).exists(), static_path
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_vendor_command.py -v`
Expected: FAIL with `Unknown command: 'cv_vendor_datetimepicker'`

- [ ] **Step 3: Write the command**

`src/crud_views_widget_datetimepicker/management/commands/cv_vendor_datetimepicker.py`:

```python
from django.core.management.base import BaseCommand, CommandError

from crud_views.lib.vendor import VendorSpec, vendor

from ...assets import ALL_FILES, APP_LABEL
from ...conf import get_config


class Command(BaseCommand):
    help = (
        "Download the pinned jquery-datetimepicker version (all four file variants) "
        "into CRUD_VIEWS_DATETIMEPICKER['VENDOR_DIR']."
    )

    def handle(self, *args, **options):
        cfg = get_config()
        if cfg.vendor_dir is None:
            raise CommandError("CRUD_VIEWS_DATETIMEPICKER['VENDOR_DIR'] must be set.")
        spec = VendorSpec(
            key="datetimepicker",
            version=cfg.version,
            base_url=cfg.cdn_base,
            files=ALL_FILES,
            target=cfg.vendor_dir / APP_LABEL / cfg.version,
        )
        for path in vendor(spec):
            self.stdout.write(f"vendored {path}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Vendored jquery-datetimepicker {cfg.version}. "
                f"Make sure {cfg.vendor_dir} is listed in STATICFILES_DIRS."
            )
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_vendor_command.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_widget_datetimepicker/management tests/test_vendor_command.py
git commit -m "feat: cv_vendor_datetimepicker management command"
```

---

### Task 7: Pipeline compatibility verification

**Files:**
- Test: `tests/test_pipeline_compat.py`

**Interfaces:**
- Consumes: `source_files` (Task 2), `register_assets` (core). django-pipeline is a dev/test
  dependency only — nothing in `src/` may import it.

These tests verify the spec's pipeline story end-to-end: unminified sources bundle in the right
order, and `EMIT: False` prevents double emission via `cv_js`.

- [ ] **Step 1: Write the tests** (no failing-first cycle here — this task adds only tests; they must pass against the code from Tasks 2-5)

`tests/test_pipeline_compat.py`:

```python
"""Verifies the django-pipeline integration story WITHOUT any runtime coupling:
a project builds its PIPELINE config from source_files() and sets EMIT: False."""

from django.template import Context, Template

from crud_views_widget_datetimepicker.assets import source_files


def _write_dummy_sources(static_dir, version):
    files = source_files(version, minified=False)
    for path in [*files["js"], *files["css"]]:
        f = static_dir / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"/* {path} */\n")
    return files


def test_pipeline_bundle_compiles_in_order(settings, tmp_path):
    import pipeline.conf

    version = "9.9.9"
    static_src = tmp_path / "static_src"
    static_root = tmp_path / "static_root"
    files = _write_dummy_sources(static_src, version)

    settings.STATICFILES_DIRS = [str(static_src)]
    settings.STATIC_ROOT = str(static_root)
    settings.STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "pipeline.finders.PipelineFinder",
    ]
    settings.PIPELINE = {
        "PIPELINE_ENABLED": True,
        "JAVASCRIPT": {"main": {"source_filenames": files["js"], "output_filename": "bundle/main.js"}},
        "STYLESHEETS": {"main": {"source_filenames": files["css"], "output_filename": "bundle/main.css"}},
        "JS_COMPRESSOR": None,
        "CSS_COMPRESSOR": None,
        "COMPILERS": [],
    }
    # pipeline caches its settings object; force re-read after override
    pipeline.conf.settings = pipeline.conf.PipelineSettings(settings.PIPELINE)

    from pipeline.packager import Packager

    packager = Packager()
    package = packager.package_for("js", "main")
    packager.pack_javascripts(package)

    bundle = (static_root / "bundle" / "main.js").read_text()
    # plugin before init.js — the order jQuery-plugin bootstrapping requires
    assert bundle.index("jquery.datetimepicker.full.js") < bundle.index("init.js")

    package_css = packager.package_for("css", "main")
    packager.pack_stylesheets(package_css)
    assert (static_root / "bundle" / "main.css").exists()


def test_emit_false_suppresses_cv_js_output(settings):
    from crud_views.lib import assets as registry

    # simulate a project that moved the picker into a pipeline bundle
    snapshot = dict(registry._REGISTRY)
    try:
        registry._REGISTRY.clear()
        registry.register_assets(
            key="datetimepicker",
            js=source_files("2.5.21", minified=False)["js"],
            css=source_files("2.5.21", minified=False)["css"],
            emit=False,
        )
        html = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
        assert "datetimepicker" not in html
        assert "crud_views/js/viewset.js" in html  # core untouched
    finally:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(snapshot)
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test_pipeline_compat.py -v`
Expected: 2 PASS.

Known friction: django-pipeline's settings caching differs between versions. If the packager
ignores the overridden `PIPELINE` despite the `pipeline.conf.settings` re-read above, consult the
installed version's `pipeline/conf.py` and adapt the re-read line — the assertion targets
(bundle exists, plugin-before-init order) stay the same.

- [ ] **Step 3: Run the whole suite + commit**

Run: `uv run pytest tests/ -q`
Expected: PASS

```bash
git add tests/test_pipeline_compat.py
git commit -m "test: verify django-pipeline bundling story (source order, EMIT suppression)"
```

---

### Task 8: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the full README**

```markdown
# django-crud-views-extensions

Incubator for [django-crud-views](https://github.com/jacob-consulting/django-crud-views)
extension apps. Apps here are named as if they lived in django-crud-views itself
(`crud_views_widget_*`); once mature, an app may move into the main package with no
code changes for consuming projects.

Requires django-crud-views >= 0.11 (asset registry).

## crud_views_widget_datetimepicker

Form widgets wrapping the [xdsoft jQuery DateTimePicker](https://github.com/xdan/datetimepicker):
`DateTimePickerInput`, `DatePickerInput`, `TimePickerInput`.

Prerequisite: jQuery loaded in your base template before `{% cv_js %}` (same rule as
django-crud-views core).

### Install

    pip install django-crud-views-extensions

    INSTALLED_APPS = [
        ...
        "crud_views",
        "crud_views_widget_datetimepicker",
    ]

That's it — the widget's JS/CSS are delivered through `{% cv_js %}`/`{% cv_css %}` on
every page (including crud-views modals) via the asset registry. By default the plugin
files load from jsDelivr (CDN mode).

### Use

    from crud_views_widget_datetimepicker.widgets import DateTimePickerInput

    class AppointmentForm(CrispyModelForm):
        class Meta:
            model = Appointment
            fields = ["title", "starts_at"]
            widgets = {"starts_at": DateTimePickerInput()}

Options: `config={...}` (any xdsoft option, e.g. `step`, `minTime`), and
`DateTimePickerInput(fix_year=2026)` to lock the picker to one calendar year.

### Settings

    CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "cdn",        # "cdn" (default) | "vendored"
        "VERSION": "2.5.21",    # pinned upstream version, used by both modes
        "CDN_BASE": "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/",
        "VENDOR_DIR": None,     # required for vendored mode; must be on STATICFILES_DIRS
        "EMIT": True,           # False: keep registered but let a bundler deliver the files
        "LANG": None,           # None: derived from LANGUAGE_CODE
        "DEFAULTS": {},         # merged into every widget's picker config
    }

### Vendored mode (recommended for production / GDPR)

    CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static"}
    STATICFILES_DIRS = [BASE_DIR / "vendored_static"]

    python manage.py cv_vendor_datetimepicker

A system check warns on startup when the vendored files are missing (`crud_views.W330`)
or don't match the pinned `VERSION` (`crud_views.W331`).

### django-pipeline

CDN mode cannot be bundled. For pipeline, use vendored mode and build your bundle from
the same path list the app uses internally — then switch off tag emission:

    from crud_views_widget_datetimepicker.assets import source_files

    _dtp = source_files("2.5.21", minified=False)   # pipeline minifies itself
    PIPELINE = {
        "JAVASCRIPT": {"main": {"source_filenames": [..., *_dtp["js"]], ...}},
        "STYLESHEETS": {"main": {"source_filenames": [..., *_dtp["css"]], ...}},
    }
    CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": ..., "EMIT": False}

Keep the order jQuery → plugin → init.js in your bundle (`source_files()` already
returns plugin before init.js).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with install, settings, vendoring and pipeline wiring"
```

---

## Completion

- `uv run pytest tests/ -q` — all green.
- Hand back to the maintainer. Follow-ups outside this plan: publish/submodule the repo,
  integrate into gas2gas (replace `viho_ui.widgets.xdsoft` imports), and release
  django-crud-views 0.11.0 if not already done.
