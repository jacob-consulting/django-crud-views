# Asset registry ↔ django-pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let projects put every local crud-views asset (core + registered extension bundles) into
their django-pipeline packages via a lazy `cv_sources()` list, suppress double-emission with an
all-or-nothing `CRUD_VIEWS_ASSETS_BUNDLED` mode, catch misconfiguration with checks W340–W345, and
make the registry inspectable with `manage.py cv_assets`.

**Architecture:** `crud_views/lib/assets.py` gains a synthesized core bundle (always first) and a
keyed `collect()`; the `{% cv_js %}`/`{% cv_css %}` tags read `tag_entries()`, which drops local
entries in bundled mode. A new settings-time-safe module `crud_views/lib/pipeline.py` provides
`cv_sources()` → `LazySources` (a `Sequence` resolved on access, after `AppConfig.ready()`), plus
one shared delivery resolver (`asset_rows()`) used by the checks and the `cv_assets` command.
Core never imports django-pipeline; it reads `settings.PIPELINE` as plain data.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, pydantic settings model, pytest + pytest-django,
django-pipeline 4.x (test-only dependency).

**Spec:** `superpowers/specs/2026-10-08-asset-registry-pipeline-design.md`

## Global Constraints

- Core has **no runtime dependency on django-pipeline**: no import in `src/`, no `[pipeline]`
  extra; `django-pipeline` goes into the `test` extra only.
- `crud_views/lib/pipeline.py` imports **stdlib only at module level** (Django and
  `crud_views.lib.assets` are imported inside functions).
- `CRUD_VIEWS_ASSETS_BUNDLED` default `False`; with `False`, `{% cv_js %}`/`{% cv_css %}` output is
  byte-identical to before.
- Reserved bundle key: `"crud_views"` (`assets.CORE_KEY`).
- New check IDs: `crud_views.W340` … `crud_views.W345`, all `Warning`s, tag `"crud_views"`.
- Management command name: `cv_assets`.
- Line length 120, double quotes, ruff format (`task format`, `task check`).
- Tests must not use `override_settings(PIPELINE=...)` / pytest-django's `settings` fixture for
  `PIPELINE` — use the `pipeline_setting` fixture (Task 4). Reason: django-pipeline's
  `pipeline.conf.reload_settings` receiver does `settings.update(value)` and raises `TypeError`
  when `override_settings` exits with `value=None`, producing random-order-dependent failures.
- Changelog entry required (`CHANGELOG.md`, new `## Unreleased` section).
- Never mention customer project names anywhere (code, docs, commits, skill).

## Implementer environment

- Repo: `/home/alex/projects/alex/django-crud-views`, branch `feature/asset-registry-pipeline`, worked
  **in this checkout — no git worktree** (an inherited `VIRTUAL_ENV` would send installs to another
  checkout's venv and make the import/pipeline tests exercise the wrong code).
- Python/tools: always `.venv/bin/pytest`, `.venv/bin/python`, `.venv/bin/mkdocs`. Do not use `uv run`
  (it creates a `uv.lock`, which this repo deliberately does not have). Installs:
  `env -u VIRTUAL_ENV uv pip install -p .venv/bin/python -e ".[polymorphic,workflow,ordered,test]"`.
- Lint: `task format` (ruff format) and `task check` (ruff check --fix). Ruff selects
  `E, F, I, UP, B, C4, SIM, RUF` — imports must sit at the top of a file (E402) and be sorted (I).
- Commits: the pre-commit hook runs `ruff-format`; if it reformats files the commit aborts — re-`git add`
  and commit again. Never `--no-verify`. No attribution lines in commit messages.
- Do not dispatch subagents; do not push; do not touch `main`.

## Review Focus

1. **Test-order pollution through pipeline's `setting_changed` receiver** — once any test imported
   `pipeline.conf`, an `override_settings(PIPELINE=...)` exit crashes. Expect: no test touches
   `PIPELINE` via `override_settings`; pinned by `test_pipeline_setting_fixture_sends_no_signal`
   (Task 4).
2. **Bare string for `keys`/`exclude`/`before`/`after`** (`keys="datetimepicker"`) — a reasonable
   user expects one key, not ten single-character keys. Expect: a bare `str` is treated as a
   one-element tuple; pinned by `test_bare_string_arguments_are_single_items` (Task 3).
3. **Odd `PIPELINE` shapes** — `PIPELINE` missing/`None`, a section missing, a package without
   `source_filenames`, `source_filenames` as a tuple, non-`str` entries (e.g. `pathlib.Path`).
   Expect: no crash; non-`str` entries are ignored for coverage; pinned by
   `test_pipeline_sources_tolerates_odd_shapes` (Task 4).
4. **Bundled mode with only core installed** — tags must render no stray markup (empty output),
   so the base template keeps working. Pinned by `test_bundled_core_only_renders_nothing` (Task 2).
5. **`keys=[]` vs `keys=None`** — an empty list means "no registry entries" (only
   `before`/`after`), not "all". Pinned by `test_keys_empty_list_selects_nothing` (Task 3).

---

## File Structure

| File | Responsibility |
|---|---|
| `src/crud_views/lib/assets.py` (modify) | `CORE_KEY`, `BundleEntry`, `core_bundle()`, `iter_bundles()`, `collect()`, `tag_entries()`; reserved-key guard |
| `src/crud_views/lib/settings.py` (modify) | `assets_bundled` setting |
| `src/crud_views/templatetags/crud_views.py` (modify) | `cv_js`/`cv_css` read `assets.tag_entries()` |
| `src/crud_views/lib/pipeline.py` (create) | `cv_sources()`, `LazySources`, `PipelineSource`, `pipeline_sources()`, `AssetRow`, `asset_rows()` |
| `src/crud_views/checks.py` (modify) | `check_asset_pipeline` (W340–W345) |
| `src/crud_views/management/commands/cv_assets.py` (create) | the listing command |
| `tests/test1/conftest.py` (modify) | `PIPELINE={}` setting; shared `asset_registry`, `bundled`, `pipeline_setting` fixtures |
| `tests/test1/test_assets.py` (modify) | drop the local `asset_registry` fixture (moved to conftest) |
| `tests/test1/test_assets_bundles.py` (create) | Tasks 1–2 tests |
| `tests/test1/test_pipeline_sources.py` (create) | Task 3 tests |
| `tests/test1/test_pipeline_resolver.py` (create) | Task 4 tests |
| `tests/test1/test_pipeline_checks.py` (create) | Task 5 tests |
| `tests/test1/test_cv_assets_command.py` (create) | Task 6 tests |
| `tests/test1/test_pipeline_integration.py` (create) | Task 7 tests (real django-pipeline) |
| `tests/test1/app/static/pipeline_test/extra.js`, `app.js` (create) | static fixtures for Task 7 |
| `pyproject.toml` (modify) | `django-pipeline` in `test` extra |
| `docs/reference/assets.md`, `docs/reference/settings.md`, `CHANGELOG.md` (modify) | Task 8 |
| `../skills/plugins/django-crud-views/...` (modify) | Task 9 |

Shared test constants (repeat them in each test file that needs them):

```python
CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]
CORE_CSS = ["crud_views/css/property.css", "crud_views/css/table.css", "crud_views/css/formset.css"]
```

---

### Task 1: Core bundle, keyed `collect()`, `tag_entries()`

**Constraints that bind this task:** No `override_settings(PIPELINE=...)`; settings are read at import, so patch `crud_views_settings` attributes in tests. Tag output must stay byte-identical (existing `tests/test1/test_assets.py` is the guard).

**Files:**
- Modify: `src/crud_views/lib/assets.py`
- Modify: `src/crud_views/templatetags/crud_views.py:54-67` (`cv_css`, `cv_js`)
- Modify: `tests/test1/conftest.py` (add `asset_registry` fixture at module level)
- Modify: `tests/test1/test_assets.py:9-18` (remove the fixture there)
- Create: `tests/test1/test_assets_bundles.py`

**Interfaces:**
- Produces:
  - `assets.CORE_KEY: str = "crud_views"`
  - `@dataclass(frozen=True) class BundleEntry: key: str; emit: bool; asset: Asset`
  - `assets.core_bundle() -> AssetBundle`
  - `assets.iter_bundles(only_emitting: bool = False) -> list[AssetBundle]` (core first)
  - `assets.collect(kind: str, *, only_emitting: bool = False) -> list[BundleEntry]` (`ValueError` for kind ∉ {"js","css"})
  - `assets.tag_entries(kind: str) -> list[BundleEntry]` (Task 1: = `collect(kind, only_emitting=True)`; Task 2 adds the bundled filter)
  - Fixture `asset_registry` in `tests/test1/conftest.py` (yields the `crud_views.lib.assets` module with an empty registry)
- Note: the spec writes `collect() -> list[Asset]`; the plan returns `BundleEntry` so the bundle key
  and `emit` travel with each asset (needed by checks and `cv_assets`).

- [ ] **Step 1: Move the `asset_registry` fixture to conftest**

In `tests/test1/conftest.py` add at module level (below the imports, outside `pytest_configure`):

```python
@pytest.fixture
def asset_registry():
    """Snapshot/restore the module-global asset registry around each test."""
    from crud_views.lib import assets

    snapshot = dict(assets._REGISTRY)
    assets._REGISTRY.clear()
    yield assets
    assets._REGISTRY.clear()
    assets._REGISTRY.update(snapshot)
```

Add `import pytest` to the conftest imports if absent. Delete the identical fixture from
`tests/test1/test_assets.py` (lines 9-18).

Run: `.venv/bin/pytest tests/test1/test_assets.py -q`
Expected: all pass (fixture now comes from conftest).

- [ ] **Step 2: Write the failing tests**

Create `tests/test1/test_assets_bundles.py`:

```python
import pytest
from django.core.exceptions import ImproperlyConfigured

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]
CORE_CSS = ["crud_views/css/property.css", "crud_views/css/table.css", "crud_views/css/formset.css"]


def test_core_bundle_mirrors_settings(asset_registry):
    bundle = asset_registry.core_bundle()
    assert bundle.key == "crud_views" == asset_registry.CORE_KEY
    assert [a.path for a in bundle.js] == CORE_JS
    assert [a.path for a in bundle.css] == CORE_CSS
    assert bundle.emit is True


def test_iter_bundles_core_first(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    assert [b.key for b in asset_registry.iter_bundles()] == ["crud_views", "a"]


def test_collect_core_first_then_registration_order(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"], css=["b/two.css"])
    entries = asset_registry.collect("js")
    assert [e.asset.path for e in entries] == [*CORE_JS, "a/one.js", "b/two.js"]
    assert [e.key for e in entries] == ["crud_views"] * 6 + ["a", "b"]
    assert [e.asset.path for e in asset_registry.collect("css")] == [*CORE_CSS, "b/two.css"]


def test_collect_emit_false(asset_registry):
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    all_paths = [e.asset.path for e in asset_registry.collect("js")]
    emitting = [e.asset.path for e in asset_registry.collect("js", only_emitting=True)]
    assert "h/x.js" in all_paths
    assert "h/x.js" not in emitting
    assert asset_registry.collect("js")[-1].emit is False


def test_collect_invalid_kind(asset_registry):
    with pytest.raises(ValueError, match="'js' or 'css'"):
        asset_registry.collect("svg")


def test_core_key_is_reserved(asset_registry):
    with pytest.raises(ImproperlyConfigured, match="reserved"):
        asset_registry.register_assets(key="crud_views", js=["x.js"])


def test_tag_entries_default_equals_emitting_collect(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    paths = [e.asset.path for e in asset_registry.tag_entries("js")]
    assert paths == [*CORE_JS, "a/one.js", "https://cdn.example.com/x.js"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_assets_bundles.py -q`
Expected: FAIL — `AttributeError: module 'crud_views.lib.assets' has no attribute 'core_bundle'` (and similar).

- [ ] **Step 4: Implement in `src/crud_views/lib/assets.py`**

Add after `AssetBundle` / before `_REGISTRY`:

```python
CORE_KEY = "crud_views"
KINDS = ("js", "css")


@dataclass(frozen=True)
class BundleEntry:
    """One asset together with the bundle it belongs to (key and emit travel with the asset)."""

    key: str
    emit: bool
    asset: Asset
```

In `register_assets`, as the first statement inside the function body (before `with _LOCK:`):

```python
    if key == CORE_KEY:
        raise ImproperlyConfigured(f"crud_views asset bundle key {CORE_KEY!r} is reserved for the core assets")
```

Append at the end of the module:

```python
def core_bundle() -> AssetBundle:
    """The package's own assets as a bundle, built from CrudViewsSettings (the source of truth)."""
    from crud_views.lib.settings import crud_views_settings

    return AssetBundle(
        key=CORE_KEY,
        js=normalize_entries(crud_views_settings.javascript().values()),
        css=normalize_entries(crud_views_settings.css.values()),
    )


def iter_bundles(only_emitting: bool = False) -> list[AssetBundle]:
    """Core bundle first (regardless of INSTALLED_APPS order), then registered bundles in registration order."""
    return [core_bundle(), *get_registered(only_emitting=only_emitting)]


def collect(kind: str, *, only_emitting: bool = False) -> list[BundleEntry]:
    """All entries of one kind ("js" or "css") across iter_bundles(), in render order."""
    if kind not in KINDS:
        raise ValueError(f"asset kind must be 'js' or 'css', got {kind!r}")
    return [
        BundleEntry(key=bundle.key, emit=bundle.emit, asset=asset)
        for bundle in iter_bundles(only_emitting=only_emitting)
        for asset in getattr(bundle, kind)
    ]


def tag_entries(kind: str) -> list[BundleEntry]:
    """The entries {% cv_js %} / {% cv_css %} render."""
    return collect(kind, only_emitting=True)
```

- [ ] **Step 5: Switch the tags to `tag_entries()`**

In `src/crud_views/templatetags/crud_views.py` replace the bodies of `cv_css` and `cv_js`:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = [entry.asset for entry in assets.tag_entries("css")]
    return {"css": _asset_items(entries), "nonce": _resolve_nonce(context)}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = [entry.asset for entry in assets.tag_entries("js")]
    return {"js": _asset_items(entries), "nonce": _resolve_nonce(context)}
```

- [ ] **Step 6: Run the new and the existing asset tests**

Run: `.venv/bin/pytest tests/test1/test_assets_bundles.py tests/test1/test_assets.py -q`
Expected: PASS (existing tag tests are the byte-identical regression guard).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/assets.py src/crud_views/templatetags/crud_views.py tests/test1/conftest.py tests/test1/test_assets.py tests/test1/test_assets_bundles.py
git commit -m "feat(assets): core bundle first in a keyed collect(); reserve the crud_views key"
```

---

### Task 2: `CRUD_VIEWS_ASSETS_BUNDLED` — tags emit only external entries

**Constraints that bind this task:** `CRUD_VIEWS_ASSETS_BUNDLED` default `False`; with `False` tag output is byte-identical to before. Imports at the top of test files (E402).

**Files:**
- Modify: `src/crud_views/lib/settings.py` (after the `csp_nonce_attr` field)
- Modify: `src/crud_views/lib/assets.py` (`tag_entries`)
- Modify: `tests/test1/conftest.py` (add `bundled` fixture)
- Modify: `tests/test1/test_assets_bundles.py`

**Interfaces:**
- Consumes: `assets.collect`, `assets.is_external`, `assets.tag_entries` (Task 1)
- Produces:
  - `crud_views_settings.assets_bundled: bool` (from `CRUD_VIEWS_ASSETS_BUNDLED`, default `False`)
  - `tag_entries(kind)` drops local entries when `assets_bundled` is true
  - Fixture `bundled` in conftest: sets `crud_views_settings.assets_bundled = True` for one test

- [ ] **Step 1: Add the `bundled` fixture to `tests/test1/conftest.py`**

```python
@pytest.fixture
def bundled(monkeypatch):
    """Turn on CRUD_VIEWS_ASSETS_BUNDLED for one test (settings are read at import, so patch the model)."""
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "assets_bundled", True)
    return crud_views_settings
```

- [ ] **Step 2: Write the failing tests** (append to `tests/test1/test_assets_bundles.py`; move the
`from django.template import Context, Template` import to the **top** of the file with the other imports — E402)

```python
from django.template import Context, Template  # -> top of file


def _render(tag: str, context: dict | None = None) -> str:
    return Template("{% load crud_views %}{% " + tag + " %}").render(Context(context or {}))


def test_assets_bundled_default_false():
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.assets_bundled is False


def test_bundled_tag_entries_keep_only_external(asset_registry, bundled):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    assert [e.asset.path for e in asset_registry.tag_entries("js")] == ["https://cdn.example.com/x.js"]


def test_bundled_renders_external_with_sri_and_nonce(asset_registry, bundled):
    from types import SimpleNamespace

    from crud_views.lib.assets import Asset

    asset_registry.register_assets(
        key="cdn",
        js=["cdn/init.js", Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc")],
    )
    html = _render("cv_js", {"request": SimpleNamespace(csp_nonce="n1")})
    assert html.count("<script") == 1
    assert 'src="https://cdn.example.com/x.js"' in html
    assert 'nonce="n1"' in html
    assert 'integrity="sha384-abc" crossorigin="anonymous"' in html
    assert "cdn/init.js" not in html
    assert "crud_views/js/viewset.js" not in html


def test_bundled_core_only_renders_nothing(asset_registry, bundled):
    assert _render("cv_js").strip() == ""
    assert _render("cv_css").strip() == ""


def test_not_bundled_renders_local_and_external(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    html = _render("cv_js")
    assert html.count("<script") == 8
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_assets_bundles.py -q`
Expected: FAIL — `AttributeError: 'CrudViewsSettings' object has no attribute 'assets_bundled'` (monkeypatch raises on missing attribute) and the default test fails.

- [ ] **Step 4: Implement**

In `src/crud_views/lib/settings.py`, directly after the `csp_nonce_attr` field:

```python
    # asset bundling (django-pipeline): tags emit only external entries, a bundler delivers the rest
    assets_bundled: bool = from_settings("CRUD_VIEWS_ASSETS_BUNDLED", default=False)
```

In `src/crud_views/lib/assets.py` replace `tag_entries`:

```python
def tag_entries(kind: str) -> list[BundleEntry]:
    """The entries {% cv_js %} / {% cv_css %} render.

    With CRUD_VIEWS_ASSETS_BUNDLED a bundler (django-pipeline) delivers every local static path, so
    only external (CDN) entries remain for the tags.
    """
    from crud_views.lib.settings import crud_views_settings

    entries = collect(kind, only_emitting=True)
    if crud_views_settings.assets_bundled:
        entries = [entry for entry in entries if is_external(entry.asset.path)]
    return entries
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test1/test_assets_bundles.py tests/test1/test_assets.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/settings.py src/crud_views/lib/assets.py tests/test1/conftest.py tests/test1/test_assets_bundles.py
git commit -m "feat(assets): CRUD_VIEWS_ASSETS_BUNDLED limits cv_js/cv_css to external entries"
```

---

### Task 3: `cv_sources()` / `LazySources`

**Constraints that bind this task:** `src/crud_views/lib/pipeline.py` imports **stdlib only at module level**; it never imports django-pipeline. No `override_settings(PIPELINE=...)`.

**Files:**
- Create: `src/crud_views/lib/pipeline.py`
- Create: `tests/test1/test_pipeline_sources.py`

**Interfaces:**
- Consumes: `assets.collect`, `assets.is_external`, `BundleEntry` (Task 1)
- Produces (in `crud_views.lib.pipeline`):
  - `KINDS = ("js", "css")`, `SECTIONS = {"js": "JAVASCRIPT", "css": "STYLESHEETS"}`
  - `NOT_READY_MESSAGE: str`
  - `class LazySources(collections.abc.Sequence)` with `__init__(kind, *, before=(), after=(), keys=None, exclude=())`, read-only properties `kind: str`, `keys: tuple[str, ...] | None`, `exclude: tuple[str, ...]`, method `registry_entries() -> list[BundleEntry]` (local entries after keys/exclude, includes `emit=False`)
  - `cv_sources(kind, *, before=(), after=(), keys=None, exclude=()) -> LazySources`

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_pipeline_sources.py`:

```python
import os
import subprocess
import sys

import pytest
from django.core.exceptions import AppRegistryNotReady

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]
CORE_CSS = ["crud_views/css/property.css", "crud_views/css/table.css", "crud_views/css/formset.css"]


def test_resolves_core_then_registry_without_externals(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"], css=["a/one.css"])
    assert list(cv_sources("js")) == [*CORE_JS, "a/one.js"]
    assert list(cv_sources("css")) == [*CORE_CSS, "a/one.css"]


def test_resolution_is_lazy(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("js")  # created before the bundle exists, like in settings.py
    asset_registry.register_assets(key="late", js=["late/x.js"])
    assert "late/x.js" in list(sources)
    assert len(sources) == 7
    assert sources[-1] == "late/x.js"


def test_before_after_and_dedupe(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js"])
    result = list(cv_sources("js", before=["js/jquery.js", "a/one.js"], after=["js/app.js", "js/jquery.js"]))
    assert result == ["js/jquery.js", "a/one.js", *CORE_JS, "js/app.js"]


def test_emit_false_bundles_included(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    assert "h/x.js" in list(cv_sources("js"))


def test_keys_and_exclude(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"])
    assert list(cv_sources("js", keys=["b"])) == ["b/two.js"]
    assert list(cv_sources("js", exclude=["crud_views", "a"])) == ["b/two.js"]
    assert list(cv_sources("js", keys=["crud_views", "a"], exclude=["crud_views"])) == ["a/one.js"]


def test_keys_empty_list_selects_nothing(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    assert list(cv_sources("js", keys=[], before=["js/jquery.js"])) == ["js/jquery.js"]


def test_bare_string_arguments_are_single_items(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["dtp/x.js"])
    sources = cv_sources("js", keys="dtp", before="js/jquery.js", after="js/app.js")
    assert sources.keys == ("dtp",)
    assert list(sources) == ["js/jquery.js", "dtp/x.js", "js/app.js"]
    assert cv_sources("js", exclude="dtp").exclude == ("dtp",)


def test_add_and_radd_stay_lazy(asset_registry):
    from crud_views.lib.pipeline import LazySources, cv_sources

    combined = ["js/jquery.js"] + cv_sources("js", keys=["late"]) + ("js/app.js",)
    assert isinstance(combined, LazySources)
    asset_registry.register_assets(key="late", js=["late/x.js"])
    assert list(combined) == ["js/jquery.js", "late/x.js", "js/app.js"]


def test_adding_two_lazy_sources_is_unsupported():
    from crud_views.lib.pipeline import cv_sources

    with pytest.raises(TypeError):
        cv_sources("js") + cv_sources("js")


def test_invalid_kind():
    from crud_views.lib.pipeline import cv_sources

    with pytest.raises(ValueError, match="'js' or 'css'"):
        cv_sources("svg")


def test_not_ready_raises_with_hint(monkeypatch):
    from django.apps import apps

    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("js")
    monkeypatch.setattr(apps, "ready", False)
    with pytest.raises(AppRegistryNotReady, match="before=/after="):
        list(sources)


def test_repr_does_not_resolve(monkeypatch):
    from django.apps import apps

    from crud_views.lib.pipeline import cv_sources

    sources = cv_sources("css", keys=["a"], before=["x.css"])
    monkeypatch.setattr(apps, "ready", False)
    assert repr(sources) == "<LazySources kind='css' keys=('a',) exclude=() before=1 after=0>"


def test_importable_without_django_settings():
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    code = (
        "from crud_views.lib.pipeline import cv_sources\n"
        "from django.conf import settings\n"
        "s = cv_sources('js', before=['js/jquery.js'])\n"
        "assert not settings.configured\n"
        "print(repr(s))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "LazySources kind='js'" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_pipeline_sources.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'crud_views.lib.pipeline'`

- [ ] **Step 3: Implement `src/crud_views/lib/pipeline.py`**

```python
"""django-pipeline integration for the crud_views asset registry.

Settings-time safe: module-level imports are stdlib only, so ``settings.py`` can do
``from crud_views.lib.pipeline import cv_sources``. Never imports django-pipeline: it only produces
values pipeline reads, and reads ``settings.PIPELINE`` as plain data.
"""

from collections.abc import Iterable, Sequence

KINDS = ("js", "css")
SECTIONS = {"js": "JAVASCRIPT", "css": "STYLESHEETS"}

NOT_READY_MESSAGE = (
    "cv_sources() was resolved before the app registry is ready - most likely it was expanded in settings.py "
    "(e.g. [*cv_sources('js')] or list(cv_sources('js'))). Pass extra files via before=/after= or combine "
    "with + instead."
)


def _as_tuple(value: Iterable[str] | str) -> tuple[str, ...]:
    """A bare string is one item, not an iterable of characters."""
    return (value,) if isinstance(value, str) else tuple(value)


def _ensure_ready() -> None:
    from django.apps import apps
    from django.core.exceptions import AppRegistryNotReady

    if not apps.ready:
        raise AppRegistryNotReady(NOT_READY_MESSAGE)


def _dedupe(paths: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result


class LazySources(Sequence):
    """A pipeline ``source_filenames`` value that resolves from the asset registry on every access.

    django-pipeline keeps the object by reference and first iterates it when a package is rendered or
    collected - after AppConfig.ready(), when every bundle is registered.
    """

    def __init__(
        self,
        kind: str,
        *,
        before: Iterable[str] | str = (),
        after: Iterable[str] | str = (),
        keys: Iterable[str] | str | None = None,
        exclude: Iterable[str] | str = (),
    ):
        if kind not in KINDS:
            raise ValueError(f"cv_sources() kind must be 'js' or 'css', got {kind!r}")
        self._kind = kind
        self._before = _as_tuple(before)
        self._after = _as_tuple(after)
        self._keys = None if keys is None else _as_tuple(keys)
        self._exclude = _as_tuple(exclude)

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def keys(self) -> tuple[str, ...] | None:
        return self._keys

    @property
    def exclude(self) -> tuple[str, ...]:
        return self._exclude

    def registry_entries(self) -> list:
        """Local registry entries (BundleEntry) this list draws from, after keys/exclude; includes emit=False."""
        _ensure_ready()
        from crud_views.lib import assets

        return [
            entry
            for entry in assets.collect(self._kind)
            if (self._keys is None or entry.key in self._keys)
            and entry.key not in self._exclude
            and not assets.is_external(entry.asset.path)
        ]

    def _resolve(self) -> list[str]:
        registry_paths = [entry.asset.path for entry in self.registry_entries()]
        return _dedupe([*self._before, *registry_paths, *self._after])

    def __iter__(self):
        return iter(self._resolve())

    def __len__(self) -> int:
        return len(self._resolve())

    def __getitem__(self, index):
        return self._resolve()[index]

    def _with(self, before: tuple[str, ...], after: tuple[str, ...]) -> "LazySources":
        return LazySources(self._kind, before=before, after=after, keys=self._keys, exclude=self._exclude)

    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            return self._with(self._before, self._after + tuple(other))
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, (list, tuple)):
            return self._with(tuple(other) + self._before, self._after)
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"<LazySources kind={self._kind!r} keys={self._keys!r} exclude={self._exclude!r} "
            f"before={len(self._before)} after={len(self._after)}>"
        )


def cv_sources(
    kind: str,
    *,
    before: Iterable[str] | str = (),
    after: Iterable[str] | str = (),
    keys: Iterable[str] | str | None = None,
    exclude: Iterable[str] | str = (),
) -> LazySources:
    """Lazy pipeline ``source_filenames``: local registry assets of one kind ("js"/"css"), core first.

    keys=None selects every bundle ("crud_views" = core); exclude drops bundles; before/after wrap the
    registry entries (e.g. jQuery before, the project's app.js after). External (CDN) entries are left
    out - pipeline cannot bundle them; {% cv_js %}/{% cv_css %} keep rendering them.
    """
    return LazySources(kind, before=before, after=after, keys=keys, exclude=exclude)
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test1/test_pipeline_sources.py -q`
Expected: PASS. If `test_importable_without_django_settings` fails with `ModuleNotFoundError: crud_views`, the venv lacks the editable install — run `task dev`, not a code change.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/pipeline.py tests/test1/test_pipeline_sources.py
git commit -m "feat(pipeline): lazy cv_sources() for django-pipeline source_filenames"
```

---

### Task 4: Shared delivery resolver (`pipeline_sources`, `asset_rows`)

**Constraints that bind this task:** `lib/pipeline.py` module-level imports stay stdlib-only. Never `override_settings(PIPELINE=...)` or pytest-django's `settings` fixture for `PIPELINE` — use `pipeline_setting` (reason: django-pipeline's `reload_settings` receiver raises `TypeError` on override exit → random-order failures).

**Files:**
- Modify: `src/crud_views/lib/pipeline.py`
- Modify: `tests/test1/conftest.py` (add `PIPELINE={}` to `settings.configure(...)` and the `pipeline_setting` fixture)
- Create: `tests/test1/test_pipeline_resolver.py`

**Interfaces:**
- Consumes: `LazySources` (Task 3), `assets.collect`, `assets.tag_entries`, `assets.is_external` (Tasks 1–2)
- Produces (in `crud_views.lib.pipeline`):
  - `@dataclass(frozen=True) class PipelineSource: kind: str; package: str; sources: object`
  - `pipeline_sources(conf: dict | None = None) -> list[PipelineSource]` (`conf=None` → `getattr(settings, "PIPELINE", None) or {}`)
  - `@dataclass(frozen=True) class AssetRow: key: str; kind: str; path: str; external: bool; integrity: str | None; crossorigin: str | None; emit: bool; delivery: tuple[str, ...]` with property `delivery_label -> str` (`", ".join(delivery)`) and property `bundled -> bool` (any delivery starts with `"pipeline:"`)
  - `asset_rows(conf: dict | None = None) -> list[AssetRow]` — js rows then css rows, each in `collect()` order
  - Delivery values: `"tag"`, `"tag (CDN)"`, `"pipeline:<package>"` (one per covering package), `"none"`, `"none (emit=False)"`; an asset can carry several (e.g. `("tag", "pipeline:main")` = double load)
  - Fixture `pipeline_setting` in conftest: callable `set(conf)` that sets `settings.PIPELINE` without firing `setting_changed`

- [ ] **Step 1: Test settings + fixture**

In `tests/test1/conftest.py` `settings.configure(...)`, add after `DJANGO_TABLES2_TEMPLATE=...`:

```python
        # django-pipeline reads settings.PIPELINE at import of pipeline.conf; must exist
        PIPELINE={},
```

Add the fixture at module level:

```python
@pytest.fixture
def pipeline_setting(monkeypatch):
    """Set settings.PIPELINE for one test WITHOUT override_settings.

    override_settings fires setting_changed; django-pipeline's receiver (pipeline.conf.reload_settings)
    does settings.update(value) and raises TypeError when the value reverts to None, giving
    order-dependent failures once any test imported pipeline. A plain setattr fires no signal.
    """
    from django.conf import settings

    def _set(conf):
        monkeypatch.setattr(settings, "PIPELINE", conf)

    return _set
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test1/test_pipeline_resolver.py`:

```python
from pathlib import Path

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]


def _rows(conf=None, kind="js"):
    from crud_views.lib.pipeline import asset_rows

    return {r.path: r for r in asset_rows(conf) if r.kind == kind}


def test_pipeline_setting_fixture_sends_no_signal(pipeline_setting):
    from django.conf import settings
    from django.test.signals import setting_changed

    calls = []

    def receiver(**kwargs):
        calls.append(kwargs)

    setting_changed.connect(receiver)
    try:
        pipeline_setting({"JAVASCRIPT": {}})
        assert settings.PIPELINE == {"JAVASCRIPT": {}}
    finally:
        setting_changed.disconnect(receiver)
    assert calls == []


def test_pipeline_sources_walks_sections(pipeline_setting):
    from crud_views.lib.pipeline import PipelineSource, cv_sources, pipeline_sources

    js = cv_sources("js")
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": js, "output_filename": "m.js"}},
            "STYLESHEETS": {"main": {"source_filenames": ("css/a.css",), "output_filename": "m.css"}},
        }
    )
    assert pipeline_sources() == [
        PipelineSource(kind="js", package="main", sources=js),
        PipelineSource(kind="css", package="main", sources=("css/a.css",)),
    ]


def test_pipeline_sources_tolerates_odd_shapes(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import asset_rows, pipeline_sources

    pipeline_setting(None)
    assert pipeline_sources() == []
    assert pipeline_sources({"JAVASCRIPT": None}) == []
    conf = {"JAVASCRIPT": {"nosrc": {"output_filename": "x.js"}, "paths": {"source_filenames": (Path("x.js"),)}}}
    assert [s.package for s in pipeline_sources(conf)] == ["nosrc", "paths"]
    assert all(r.delivery == ("tag",) for r in asset_rows(conf) if r.kind == "js")


def test_delivery_default_tags(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    rows = _rows({})
    assert rows["crud_views/js/viewset.js"].delivery == ("tag",)
    assert rows["a/one.js"].delivery == ("tag",)
    assert rows["https://cdn.example.com/x.js"].delivery == ("tag (CDN)",)
    assert rows["https://cdn.example.com/x.js"].external is True
    assert rows["h/x.js"].delivery == ("none (emit=False)",)
    assert rows["h/x.js"].emit is False


def test_delivery_bundled(asset_registry, bundled):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"])
    conf = {
        "JAVASCRIPT": {
            "main": {"source_filenames": cv_sources("js", exclude=["b"])},
            "extra": {"source_filenames": cv_sources("js", keys=["a"])},
        }
    }
    rows = _rows(conf)
    assert rows["crud_views/js/viewset.js"].delivery == ("pipeline:main",)
    assert rows["a/one.js"].delivery == ("pipeline:main", "pipeline:extra")
    assert rows["a/one.js"].delivery_label == "pipeline:main, pipeline:extra"
    assert rows["a/one.js"].bundled is True
    assert rows["https://cdn.example.com/x.js"].delivery == ("tag (CDN)",)
    assert rows["b/two.js"].delivery == ("none",)
    assert rows["b/two.js"].bundled is False


def test_delivery_double_load_when_not_bundled(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    rows = _rows({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    assert rows["crud_views/js/viewset.js"].delivery == ("tag", "pipeline:main")


def test_plain_string_globs_count_as_coverage(asset_registry, bundled):
    rows = _rows({"JAVASCRIPT": {"main": {"source_filenames": ["crud_views/js/*.js"]}}})
    assert all(rows[p].delivery == ("pipeline:main",) for p in CORE_JS)


def test_kind_mismatch_does_not_cover(asset_registry, bundled):
    from crud_views.lib.pipeline import cv_sources

    rows = _rows({"STYLESHEETS": {"main": {"source_filenames": cv_sources("js")}}})
    assert rows["crud_views/js/viewset.js"].delivery == ("none",)


def test_rows_order_js_then_css(asset_registry):
    from crud_views.lib.pipeline import asset_rows

    rows = asset_rows({})
    kinds = [r.kind for r in rows]
    assert kinds == ["js"] * 6 + ["css"] * 3
    assert [r.path for r in rows[:6]] == CORE_JS
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_pipeline_resolver.py -q`
Expected: FAIL — `ImportError: cannot import name 'asset_rows' from 'crud_views.lib.pipeline'` (the signal test passes already — fine, it pins the fixture).

- [ ] **Step 4: Implement** — append to `src/crud_views/lib/pipeline.py`, and change the top imports to:

```python
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
```

```python
@dataclass(frozen=True)
class PipelineSource:
    """One pipeline package's source_filenames, tagged with the kind of its PIPELINE section."""

    kind: str
    package: str
    sources: object  # LazySources or an iterable of plain path / glob strings


def pipeline_sources(conf: dict | None = None) -> list[PipelineSource]:
    """Walk PIPELINE["JAVASCRIPT"] / ["STYLESHEETS"] as plain data (never imports pipeline)."""
    if conf is None:
        from django.conf import settings

        conf = getattr(settings, "PIPELINE", None)
    conf = conf or {}
    result = []
    for kind, section in SECTIONS.items():
        for package, config in (conf.get(section) or {}).items():
            result.append(PipelineSource(kind=kind, package=package, sources=config.get("source_filenames", ())))
    return result


def _coverage(sources: list[PipelineSource]) -> list[tuple[PipelineSource, Callable[[str], bool]]]:
    """Per package a path predicate; LazySources resolve once, plain strings match as glob patterns."""
    result = []
    for source in sources:
        if isinstance(source.sources, LazySources):
            result.append((source, frozenset(source.sources).__contains__))
        else:
            patterns = tuple(p for p in source.sources if isinstance(p, str))
            result.append((source, lambda path, patterns=patterns: any(fnmatchcase(path, p) for p in patterns)))
    return result


@dataclass(frozen=True)
class AssetRow:
    """One registry asset and how it reaches the browser."""

    key: str
    kind: str
    path: str
    external: bool
    integrity: str | None
    crossorigin: str | None
    emit: bool
    delivery: tuple[str, ...]

    @property
    def delivery_label(self) -> str:
        return ", ".join(self.delivery)

    @property
    def bundled(self) -> bool:
        return any(d.startswith("pipeline:") for d in self.delivery)


def asset_rows(conf: dict | None = None) -> list[AssetRow]:
    """Every registry asset (core first, all bundles incl. emit=False) with its delivery.

    The single resolver behind the W34x checks and ``manage.py cv_assets``; "tag" delivery comes from
    assets.tag_entries(), the exact list {% cv_js %}/{% cv_css %} render.
    """
    from crud_views.lib import assets

    coverage = _coverage(pipeline_sources(conf))
    rows = []
    for kind in KINDS:
        tagged = {(entry.key, entry.asset.path) for entry in assets.tag_entries(kind)}
        for entry in assets.collect(kind):
            path = entry.asset.path
            external = assets.is_external(path)
            delivery = []
            if (entry.key, path) in tagged:
                delivery.append("tag (CDN)" if external else "tag")
            if not external:
                delivery += [f"pipeline:{s.package}" for s, covers in coverage if s.kind == kind and covers(path)]
            if not delivery:
                delivery.append("none" if entry.emit else "none (emit=False)")
            rows.append(
                AssetRow(
                    key=entry.key,
                    kind=kind,
                    path=path,
                    external=external,
                    integrity=entry.asset.integrity,
                    crossorigin=entry.asset.crossorigin,
                    emit=entry.emit,
                    delivery=tuple(delivery),
                )
            )
    return rows
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test1/test_pipeline_resolver.py tests/test1/test_pipeline_sources.py -q`
Expected: PASS. Also run `.venv/bin/pytest tests/test1/test_pipeline_sources.py::test_importable_without_django_settings -q` again — the new top-level imports must stay stdlib-only.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/pipeline.py tests/test1/conftest.py tests/test1/test_pipeline_resolver.py
git commit -m "feat(pipeline): shared asset delivery resolver (asset_rows)"
```

---

### Task 5: System checks W340–W345

**Constraints that bind this task:** All new checks are `Warning`s with IDs `crud_views.W340`–`W345`, tag `"crud_views"`. Read `settings.PIPELINE` as plain data; never import django-pipeline in `src/`. Tests set `PIPELINE` only via the `pipeline_setting` fixture.

**Files:**
- Modify: `src/crud_views/checks.py` (new function after `check_asset_registry`)
- Create: `tests/test1/test_pipeline_checks.py`

**Interfaces:**
- Consumes: `pipeline.pipeline_sources`, `pipeline.asset_rows`, `pipeline.LazySources`, `pipeline.KINDS` (Tasks 3–4); `assets.iter_bundles`, `assets.get_registered`, `assets.is_external`, `assets.CORE_KEY`; `crud_views_settings.assets_bundled`
- Produces: `crud_views.checks.check_asset_pipeline(app_configs=None, **kwargs) -> list[CheckMessage]`, registered under tag `"crud_views"`

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_pipeline_checks.py`:

```python
def _ids(messages):
    return [m.id for m in messages]


def _check():
    from crud_views.checks import check_asset_pipeline

    return check_asset_pipeline()


def test_no_pipeline_not_bundled_is_clean(asset_registry, pipeline_setting):
    pipeline_setting({})
    assert _check() == []


def test_w340_bundled_without_cv_sources(asset_registry, bundled, pipeline_setting):
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": ["js/app.js"]}}})
    assert _ids(_check()) == ["crud_views.W340"]


def test_w341_gap(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["dtp/init.js"])
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", exclude=["dtp"])}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W341"]
    assert "dtp/init.js" in messages[0].msg
    assert "'dtp'" in messages[0].msg


def test_w341_clean_when_fully_covered(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    assert _check() == []


def test_w342_double_load(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    assert _ids(_check()) == ["crud_views.W342"]


def test_w342_not_for_emit_false_only(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", keys=["hidden"])}}})
    assert _check() == []


def test_w343_unknown_keys(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    pipeline_setting(
        {"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", keys=["hidden", "typo"], exclude=["gone"])}}}
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W343", "crud_views.W343"]
    assert "'typo'" in messages[0].msg
    assert "'gone'" in messages[1].msg


def test_w344_kind_mismatch(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("css", keys=[])}}})
    assert _ids(_check()) == ["crud_views.W344"]


def test_w345_mixed_bundle(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    asset_registry.register_assets(key="cdnonly", js=["https://cdn.example.com/only.js"])
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W345"]
    assert "'dtp'" in messages[0].msg
    assert "cv_assets --external" in messages[0].hint


def test_w345_not_without_bundled_mode(asset_registry, pipeline_setting):
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    pipeline_setting({})
    assert _check() == []


def test_check_registered_under_crud_views_tag():
    from django.core.checks import registry

    from crud_views.checks import check_asset_pipeline

    assert check_asset_pipeline in registry.registry.get_checks()
    assert "crud_views" in check_asset_pipeline.tags
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_pipeline_checks.py -q`
Expected: FAIL — `ImportError: cannot import name 'check_asset_pipeline'`

- [ ] **Step 3: Implement** — in `src/crud_views/checks.py` add `from crud_views.lib import pipeline as pipeline_helper` to the imports and append after `check_asset_registry`:

```python
@register(TAG)
def check_asset_pipeline(app_configs=None, **kwargs):
    """Validate the django-pipeline integration (cv_sources / CRUD_VIEWS_ASSETS_BUNDLED)."""
    messages = []
    sources = pipeline_helper.pipeline_sources()
    lazies = [s for s in sources if isinstance(s.sources, pipeline_helper.LazySources)]
    known_keys = [assets.CORE_KEY, *(bundle.key for bundle in assets.get_registered())]

    for source in lazies:
        lazy = source.sources
        where = f"PIPELINE[{pipeline_helper.SECTIONS[source.kind]!r}][{source.package!r}]"
        if lazy.kind != source.kind:
            messages.append(
                DjangoWarning(
                    f"cv_sources({lazy.kind!r}) is used in {where}, a {source.kind} package.",
                    hint=f"Use cv_sources({source.kind!r}) there; pipeline would concatenate the files silently.",
                    id="crud_views.W344",
                )
            )
        for key in (*(lazy.keys or ()), *lazy.exclude):
            if key not in known_keys:
                messages.append(
                    DjangoWarning(
                        f"cv_sources() in {where} names unknown asset bundle {key!r}.",
                        hint=f"Known bundle keys: {', '.join(known_keys)}.",
                        id="crud_views.W343",
                    )
                )

    if crud_views_settings.assets_bundled:
        if not lazies:
            messages.append(
                DjangoWarning(
                    "CRUD_VIEWS_ASSETS_BUNDLED is on, but no PIPELINE package uses cv_sources(): local "
                    "crud_views assets are delivered by nothing.",
                    hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",
                    id="crud_views.W340",
                )
            )
        else:
            for row in pipeline_helper.asset_rows():
                if not row.external and not row.bundled:
                    section = pipeline_helper.SECTIONS[row.kind]
                    messages.append(
                        DjangoWarning(
                            f"Asset {row.path!r} (bundle {row.key!r}) is not in any PIPELINE[{section!r}] package.",
                            hint="Bundled mode suppresses its tag; include the bundle in a cv_sources() call.",
                            id="crud_views.W341",
                        )
                    )
        for bundle in assets.iter_bundles():
            for kind in pipeline_helper.KINDS:
                entries = getattr(bundle, kind)
                external = [a for a in entries if assets.is_external(a.path)]
                if external and len(external) < len(entries):
                    messages.append(
                        DjangoWarning(
                            f"Asset bundle {bundle.key!r} mixes CDN and local {kind} entries; pipeline cannot "
                            "bundle the CDN ones, so its local entries may load before them.",
                            hint="Switch the extension to a vendored/local mode. List the affected entries with: "
                            "manage.py cv_assets --external",
                            id="crud_views.W345",
                        )
                    )
    else:
        for source in lazies:
            if any(entry.emit for entry in source.sources.registry_entries()):
                where = f"PIPELINE[{pipeline_helper.SECTIONS[source.kind]!r}][{source.package!r}]"
                messages.append(
                    DjangoWarning(
                        f"cv_sources() in {where} bundles assets that {{% cv_js %}}/{{% cv_css %}} also emit: "
                        "they load twice.",
                        hint="Set CRUD_VIEWS_ASSETS_BUNDLED = True.",
                        id="crud_views.W342",
                    )
                )
    return messages
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test1/test_pipeline_checks.py tests/test1/test_assets.py -q`
Expected: PASS

- [ ] **Step 5: Run the full suite in random order with a fixed seed (pollution guard)**

Run: `.venv/bin/pytest tests -q --random-order-seed=4711 -n auto`
Expected: PASS (no new failures vs. `main`).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/checks.py tests/test1/test_pipeline_checks.py
git commit -m "feat(checks): W340-W345 for the django-pipeline asset integration"
```

---

### Task 6: `manage.py cv_assets`

**Constraints that bind this task:** Command name `cv_assets`. Never import django-pipeline in `src/`. Tests set `PIPELINE` only via `pipeline_setting`.

**Files:**
- Create: `src/crud_views/management/commands/cv_assets.py`
- Create: `tests/test1/test_cv_assets_command.py`

**Interfaces:**
- Consumes: `pipeline.asset_rows()`, `AssetRow.delivery_label` (Task 4)
- Produces: command `cv_assets` with options `--external`, `--kind {js,css}`, `--format {table,json}` (dest `output_format`, default `table`). JSON = list of objects `{key, kind, path, external, integrity, crossorigin, emit, delivery}` with `delivery` a list of strings.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_cv_assets_command.py`:

```python
import json
from io import StringIO

from django.core.management import call_command


def _run(*args) -> str:
    out = StringIO()
    call_command("cv_assets", *args, stdout=out)
    return out.getvalue()


def test_table_lists_core_and_registered(asset_registry, pipeline_setting):
    pipeline_setting({})
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    lines = _run().splitlines()
    assert lines[0].split() == ["KEY", "KIND", "DELIVERY", "PATH"]
    assert lines[1].split() == ["crud_views", "js", "tag", "crud_views/js/viewset.js"]
    assert any(line.split()[:2] == ["dtp", "js"] and "tag (CDN)" in line and "cdn.example.com" in line for line in lines)
    assert len(lines) == 1 + 9 + 2


def test_external_filter(asset_registry, pipeline_setting):
    pipeline_setting({})
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    lines = _run("--external").splitlines()
    assert len(lines) == 2
    assert "https://cdn.example.com/dtp.js" in lines[1]


def test_kind_filter(asset_registry, pipeline_setting):
    pipeline_setting({})
    lines = _run("--kind", "css").splitlines()
    assert len(lines) == 1 + 3
    assert all(line.split()[1] == "css" for line in lines[1:])


def test_integrity_shown(asset_registry, pipeline_setting):
    from crud_views.lib.assets import Asset

    pipeline_setting({})
    asset_registry.register_assets(key="cdn", js=[Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc")])
    assert "[sha384-abc]" in _run("--external")


def test_json_format(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    data = json.loads(_run("--format", "json", "--kind", "js"))
    by_path = {item["path"]: item for item in data}
    assert set(data[0]) == {"key", "kind", "path", "external", "integrity", "crossorigin", "emit", "delivery"}
    assert by_path["dtp/init.js"]["delivery"] == ["pipeline:main"]
    assert by_path["https://cdn.example.com/dtp.js"] == {
        "key": "dtp",
        "kind": "js",
        "path": "https://cdn.example.com/dtp.js",
        "external": True,
        "integrity": None,
        "crossorigin": None,
        "emit": True,
        "delivery": ["tag (CDN)"],
    }


def test_empty_selection_prints_header_only(asset_registry, pipeline_setting):
    pipeline_setting({})
    # no rows: each column is as wide as its header cell, columns joined by two spaces
    assert _run("--external").splitlines() == ["KEY  KIND  DELIVERY  PATH"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_cv_assets_command.py -q`
Expected: FAIL — `CommandError: Unknown command: 'cv_assets'`

- [ ] **Step 3: Implement `src/crud_views/management/commands/cv_assets.py`**

```python
import dataclasses
import json

from django.core.management import BaseCommand

from crud_views.lib.pipeline import asset_rows


class Command(BaseCommand):
    help = (
        "List the crud_views asset registry (core + registered bundles) and how each asset is delivered: "
        "tag, tag (CDN), pipeline:<package> or none. Use --external to list the CDN assets to vendor."
    )

    def add_arguments(self, parser):
        parser.add_argument("--external", action="store_true", help="Only external (CDN) entries.")
        parser.add_argument("--kind", choices=("js", "css"), help="Only this asset kind.")
        parser.add_argument(
            "--format", choices=("table", "json"), default="table", dest="output_format", help="Output format."
        )

    def handle(self, *args, external=False, kind=None, output_format="table", **options):
        rows = [row for row in asset_rows() if (not external or row.external) and (kind is None or row.kind == kind)]
        if output_format == "json":
            self.stdout.write(json.dumps([dataclasses.asdict(row) for row in rows], indent=2))
            return
        lines = [("KEY", "KIND", "DELIVERY", "PATH")]
        for row in rows:
            path = f"{row.path}  [{row.integrity}]" if row.integrity else row.path
            lines.append((row.key, row.kind, row.delivery_label, path))
        widths = [max(len(line[i]) for line in lines) for i in range(3)]
        for line in lines:
            self.stdout.write("  ".join(line[i].ljust(widths[i]) for i in range(3)) + "  " + line[3])
```

Note: `dataclasses.asdict` keeps `delivery` as a tuple; `json.dumps` writes it as a list.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test1/test_cv_assets_command.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/management/commands/cv_assets.py tests/test1/test_cv_assets_command.py
git commit -m "feat: cv_assets management command lists registry assets and their delivery"
```

---

### Task 7: Real django-pipeline integration tests

**Constraints that bind this task:** django-pipeline goes into the `test` extra only (no `dev`, no `[pipeline]` extra, no import in `src/`). Never `override_settings(PIPELINE=...)`; patch `pipeline.conf.settings` with `monkeypatch.setitem` as shown.

**Files:**
- Modify: `pyproject.toml` (`test` extra)
- Create: `tests/test1/app/static/pipeline_test/extra.js`, `tests/test1/app/static/pipeline_test/app.js`
- Create: `tests/test1/test_pipeline_integration.py`

**Interfaces:**
- Consumes: `cv_sources` (Task 3); fixtures `asset_registry` (Task 1)
- Produces: nothing new for other tasks

- [ ] **Step 1: Add the test dependency and install**

In `pyproject.toml` `[project.optional-dependencies] test = [...]` add `"django-pipeline",` after `"polib",`.

Run: `env -u VIRTUAL_ENV uv pip install -p .venv/bin/python -e ".[polymorphic,workflow,ordered,test]"`
Expected: django-pipeline installed (`python -c "import pipeline"` succeeds).

- [ ] **Step 2: Verify Django 6.0 compatibility first (risk from the spec)**

Run: `nox -s "tests-3.13(django='6.0')" -- tests/test1/test_assets.py -q` after Step 1, then once Step 4 exists rerun with `tests/test1/test_pipeline_integration.py`.
Note: the nox session already passes `tests` before posargs, so this runs the whole suite plus the named file — slow, not wrong.
Expected: `pipeline.packager` imports and works on Django 6.0. Outcomes:
- Fails at **import** → `pytest.importorskip("pipeline.packager")` (Step 4) skips cleanly.
- Imports but **breaks at runtime** on a matrix row → mark only the affected integration tests with
  `pytest.mark.skipif(<exact condition>, reason="django-pipeline <version> incompatible with Django <x>: <error>")`.
- Either way: write the finding into the task report (it goes into the PR description). Do not add
  Django-version code paths to `src/`.

- [ ] **Step 3: Static fixtures**

`tests/test1/app/static/pipeline_test/extra.js`:

```js
/* pipeline_test extra marker */
window.pipelineTestExtra = true;
```

`tests/test1/app/static/pipeline_test/app.js`:

```js
/* pipeline_test app marker */
window.pipelineTestApp = true;
```

- [ ] **Step 4: Write the tests**

Create `tests/test1/test_pipeline_integration.py`:

```python
from pathlib import Path

import pytest

pytest.importorskip("pipeline.packager")

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]


@pytest.fixture
def noop_compressors(monkeypatch):
    """Pipeline's default compressor (yuglify) needs a binary; patch pipeline.conf without setting_changed."""
    from pipeline.conf import settings as pipeline_settings

    monkeypatch.setitem(pipeline_settings, "JS_COMPRESSOR", "pipeline.compressors.NoopCompressor")
    monkeypatch.setitem(pipeline_settings, "CSS_COMPRESSOR", "pipeline.compressors.NoopCompressor")
    monkeypatch.setitem(pipeline_settings, "DISABLE_WRAPPER", True)


def _js_packages():
    from crud_views.lib.pipeline import cv_sources

    return {
        "main": {
            "source_filenames": cv_sources("js", after=["pipeline_test/app.js"]),
            "output_filename": "out/main.js",
        }
    }


def test_package_sources_resolve_from_registry(asset_registry):
    from pipeline.packager import Packager

    asset_registry.register_assets(key="extra", js=["pipeline_test/extra.js", "https://cdn.example.com/x.js"])
    package = Packager(js_packages=_js_packages(), css_packages={}).package_for("js", "main")
    assert package.sources == [*CORE_JS, "pipeline_test/extra.js", "pipeline_test/app.js"]


def test_pack_concatenates_in_registry_order(asset_registry, noop_compressors, tmp_path):
    from django.contrib.staticfiles import finders
    from django.core.files.storage import FileSystemStorage
    from pipeline.packager import Packager

    asset_registry.register_assets(key="extra", js=["pipeline_test/extra.js", "https://cdn.example.com/x.js"])
    storage = FileSystemStorage(location=str(tmp_path), base_url="/static/")
    packager = Packager(storage=storage, js_packages=_js_packages(), css_packages={})
    packager.pack_javascripts(packager.package_for("js", "main"))

    output = (tmp_path / "out" / "main.js").read_text()
    expected = [*CORE_JS, "pipeline_test/extra.js", "pipeline_test/app.js"]
    positions = [output.index(Path(finders.find(path)).read_text()[:60]) for path in expected]
    assert positions == sorted(positions)
    assert "cdn.example.com" not in output
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test1/test_pipeline_integration.py -v`
Expected: PASS (2 tests). If `find_source_storage` is slow it is still fine; if the first 60 chars of
two core files coincide (e.g. identical license headers), switch to `[:200]` — do not drop the order assert.

- [ ] **Step 6: Full suite, random order, two seeds**

Run: `.venv/bin/pytest tests -q --random-order-seed=4711 -n auto` and again with `--random-order-seed=1234`
Expected: PASS both. A failure mentioning `reload_settings` / `NoneType` means a test used `override_settings(PIPELINE=...)` — replace it with `pipeline_setting`.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml tests/test1/app/static/pipeline_test tests/test1/test_pipeline_integration.py
git commit -m "test: verify cv_sources against real django-pipeline packaging"
```

---

### Task 8: Docs + changelog

**Constraints that bind this task:** Changelog entry under a new `## Unreleased` section. Never mention customer project names. Docs build with `.venv/bin/mkdocs` (not `uv run`).

**Files:**
- Modify: `docs/reference/assets.md` (reword the `emit=False` bullet; append a new section)
- Modify: `docs/reference/settings.md` (new section before `## django-tables2 compatibility`)
- Modify: `CHANGELOG.md` (new top section)

**Interfaces:** none (documentation only)

- [ ] **Step 1: Reword the `emit=False` bullet in `docs/reference/assets.md`**

Replace:

```markdown
- `register_assets(..., emit=False)` keeps the bundle registered but excludes it from
  tag output — use this when a bundler such as django-pipeline delivers the files
  instead. Vendored bundles are validated separately via `check_vendored()`, which an
  extension app wires into its own system checks; it is not run automatically.
```

with:

```markdown
- `register_assets(..., emit=False)` keeps the bundle registered but excludes it from
  tag output. To deliver crud-views assets through django-pipeline, prefer
  [bundled mode](#bundling-with-django-pipeline), which covers core and every bundle at once.
  Vendored bundles are validated separately via `check_vendored()`, which an
  extension app wires into its own system checks; it is not run automatically.
- The key `crud_views` is reserved for the package's own assets.
```

- [ ] **Step 2: Append to `docs/reference/assets.md`**

````markdown
## Bundling with django-pipeline

Projects using [django-pipeline](https://django-pipeline.readthedocs.io/) can put every *local*
crud-views asset — core and all registered bundles — into their pipeline packages without listing
files by hand:

```python
# settings.py
from crud_views.lib.pipeline import cv_sources

CRUD_VIEWS_ASSETS_BUNDLED = True  # {% cv_js %}/{% cv_css %} now emit only CDN entries

PIPELINE = {
    "JAVASCRIPT": {
        "main": {
            "source_filenames": cv_sources("js", before=["js/jquery.js"], after=["js/app.js"]),
            "output_filename": "js/main.js",
        },
    },
    "STYLESHEETS": {
        "main": {
            "source_filenames": cv_sources("css", after=["css/app.css"]),
            "output_filename": "css/main.css",
        },
    },
}
```

`cv_sources()` returns a lazy list: django-pipeline reads it when a package is rendered or
collected, after every app has registered its assets. Adding or removing an extension app needs no
settings change. Order: `before`, core assets, registered bundles (`INSTALLED_APPS` order), `after`.

!!! warning "Do not expand it in settings.py"
    `[*cv_sources("js")]` or `list(cv_sources("js"))` resolves too early and raises
    `AppRegistryNotReady`. Put extra files into `before=`/`after=`, or combine with `+`:
    `["js/jquery.js"] + cv_sources("js")` stays lazy.

Arguments:

| Argument | Meaning |
|---|---|
| `kind` | `"js"` or `"css"` |
| `before` / `after` | static paths placed around the registry entries (e.g. jQuery, which the registry does not manage) |
| `keys` | only these bundle keys (`"crud_views"` = core); `None` = all, `[]` = none |
| `exclude` | drop these bundle keys |

Split across packages by calling it more than once, e.g.
`cv_sources("js", exclude=["datetimepicker"])` in `"main"` and
`cv_sources("js", keys=["datetimepicker"])` in `"forms"`.

### What can and cannot be bundled

- Pipeline only concatenates files on disk; **CDN entries cannot be bundled**. `cv_sources()`
  leaves them out and `{% cv_js %}`/`{% cv_css %}` keep rendering them (with SRI and nonce) — keep
  the tags in your base template.
- **Core has no CDN entries**: with only core installed, bundled mode makes both tags render nothing.
- **Extensions must be in a local (vendored) mode to be fully bundled.** An extension in CDN mode
  would get its local init script bundled while its plugin stays a CDN tag (check W345).
  For `crud_views_widget_datetimepicker`: `SOURCE="vendored"` plus `manage.py cv_vendor_datetimepicker`.
- Re-minifying already-minified vendor files with pipeline's compressors is harmless.
- Template order in bundled mode: project CDN dependencies (Bootstrap, jQuery) →
  `{% cv_css %}{% cv_js %}` → `{% stylesheet "main" %}{% javascript "main" %}`.

### Listing assets: `cv_assets`

```
$ python manage.py cv_assets
KEY             KIND  DELIVERY        PATH
crud_views      js    pipeline:main   crud_views/js/viewset.js
...
datetimepicker  js    tag (CDN)       https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.full.min.js
datetimepicker  js    pipeline:main   crud_views_widget_datetimepicker/init.js
```

Delivery is `tag`, `tag (CDN)`, `pipeline:<package>`, `none` (delivered by nothing) or
`none (emit=False)`. Options: `--external` (only CDN entries — the list to vendor for production),
`--kind js|css`, `--format table|json`. The JSON output also gives you the CDN hosts for a CSP
`script-src`/`style-src` allowlist.

### Checks

| ID | Meaning |
|---|---|
| `crud_views.W340` | Bundled mode is on, but no `PIPELINE` package uses `cv_sources()`. |
| `crud_views.W341` | Bundled mode: a local asset is in no pipeline package of its kind. |
| `crud_views.W342` | Not bundled, but `cv_sources()` bundles assets the tags also emit (double load). |
| `crud_views.W343` | `keys=`/`exclude=` names an unknown bundle key. |
| `crud_views.W344` | `cv_sources("css")` under `JAVASCRIPT` or vice versa. |
| `crud_views.W345` | Bundled mode: a bundle mixes CDN and local entries — vendor that extension. |

Plain string entries in `source_filenames` (including glob patterns) count as coverage too, so
hand-maintained lists get the same checks.
````

- [ ] **Step 3: `docs/reference/settings.md`** — insert before `## django-tables2 compatibility`:

```markdown
## Asset bundling

| Key                       | Description                                                                                       | Type   | Default |
|---------------------------|---------------------------------------------------------------------------------------------------|--------|---------|
| CRUD_VIEWS_ASSETS_BUNDLED | `{% cv_js %}`/`{% cv_css %}` emit only external (CDN) entries; a bundler such as django-pipeline delivers all local assets. See [Bundling with django-pipeline](assets.md#bundling-with-django-pipeline). | `bool` | `False` |
```

- [ ] **Step 4: `CHANGELOG.md`** — insert directly below `# Django CRUD Views - Changelog`:

```markdown
## Unreleased

### Added

- django-pipeline support for the asset registry: `cv_sources()` (`crud_views.lib.pipeline`) is a lazy
  `source_filenames` value that fills pipeline packages with core and all registered local assets;
  `CRUD_VIEWS_ASSETS_BUNDLED = True` limits `{% cv_js %}`/`{% cv_css %}` to CDN entries.
- System checks `crud_views.W340`–`W345` for the pipeline integration (missing packages, gaps,
  double loading, unknown keys, kind mismatch, mixed CDN/local bundles).
- `manage.py cv_assets` lists every registered asset and how it is delivered (`--external`,
  `--kind`, `--format json`).

### Changed

- Core assets are part of the registry ordering (`crud_views.lib.assets.iter_bundles()` / `collect()`),
  always first; the bundle key `crud_views` is reserved.

### Internal

- django-pipeline is a test-only dependency.
```

- [ ] **Step 5: Build docs**

Baseline: **before Step 1**, build the untouched docs and keep the output:
`.venv/bin/mkdocs build --strict -d /tmp/cv-docs-baseline 2>&1 | tee /tmp/cv-docs-baseline.log`.
After the edits: `.venv/bin/mkdocs build --strict -d /tmp/cv-docs-new 2>&1 | tee /tmp/cv-docs-new.log`.
Expected: the new log has **no warnings that the baseline log lacks** (in particular none about
`assets.md#bundling-with-django-pipeline`). Pre-existing warnings are not this task's to fix — list them
in the report. `admonition` is already enabled in `mkdocs.yml`.

- [ ] **Step 6: Lint + full tests, commit**

Run: `task format && task check && .venv/bin/pytest tests -q -n auto`
Expected: clean, PASS.

```bash
git add docs/reference/assets.md docs/reference/settings.md CHANGELOG.md
git commit -m "docs: bundling crud-views assets with django-pipeline"
```

---

### Task 9: Update the django-crud-views skill (`../skills`) — after the package release

> **Not part of the subagent-driven run of Tasks 1–8.** It waits on a release the user has not
> requested and pushes to a shared repo. The controller does it after the release, and first writes
> the drift-audit harness (Step 6) out in full as code.

**Gate:** Do this only after the package release carrying this feature exists (the next minor,
expected **0.25.0**). Releasing and merging require the user's explicit request — if no release
has happened, stop here and ask the user. Use the actual released version wherever `0.25.0`
appears below.

**Files** (repo `/home/alex/projects/alex/skills`, all git ops via `git -C /home/alex/projects/alex/skills`):
- Modify: `plugins/django-crud-views/skills/django-crud-views/SKILL.md` (frontmatter `description`; section "Static assets, CSP, and SRI"; Common Mistakes table)
- Modify: `plugins/django-crud-views/skills/django-crud-views/references/api-reference.md` (settings block "Asset registry / CSP settings"; import cheatsheet; section "Asset registry (`crud_views.lib.assets`)")
- Modify: `plugins/django-crud-views/CHANGELOG.md` (`[Unreleased]`)

**Interfaces:** documents `cv_sources`, `LazySources`, `CRUD_VIEWS_ASSETS_BUNDLED`, `iter_bundles`, `collect`, `CORE_KEY`, `cv_assets`, W340–W345.

- [ ] **Step 1: Frontmatter description** — in `SKILL.md` replace
`registering static assets, CSP nonces, or SRI hashes via register_assets;` with
`registering static assets, CSP nonces, or SRI hashes via register_assets, or bundling them into django-pipeline with cv_sources;`

- [ ] **Step 2: New subsection in SKILL.md** — insert before the line
`> \`AssetBundle.js\` / \`.css\` hold \`Asset\` instances, not strings (changed in 0.18.0).`:

````markdown
### Bundling with django-pipeline

*Available since 0.25.0.*

```python
# settings.py
from crud_views.lib.pipeline import cv_sources

CRUD_VIEWS_ASSETS_BUNDLED = True   # cv_js/cv_css then emit only CDN entries

PIPELINE = {
    "JAVASCRIPT": {"main": {
        "source_filenames": cv_sources("js", before=["js/jquery.js"], after=["js/app.js"]),
        "output_filename": "js/main.js",
    }},
    "STYLESHEETS": {"main": {"source_filenames": cv_sources("css"), "output_filename": "css/main.css"}},
}
```

- `cv_sources()` is **lazy** — pipeline reads it after `AppConfig.ready()`, so core plus every
  registered bundle lands in the package with no hand-maintained list. Never expand it in settings
  (`[*cv_sources(...)]` raises `AppRegistryNotReady`); use `before=`/`after=` or `list + cv_sources(...)`.
- `keys=[...]` / `exclude=[...]` select bundles (`"crud_views"` = core) to split across packages.
- CDN entries cannot be bundled: they stay `{% cv_js %}`/`{% cv_css %}` tags, so keep the tags in
  the base template. Core has none; an extension must be in its vendored mode to be fully bundled
  (W345 warns otherwise). `python manage.py cv_assets --external` lists the CDN entries.
- Checks: W340 (bundled, no `cv_sources()` in `PIPELINE`), W341 (asset in no package), W342 (not
  bundled → double load), W343 (unknown key), W344 (js/css mismatch), W345 (bundle mixes CDN and local).
````

- [ ] **Step 3: Common Mistakes rows** — append to the table under `## Common Mistakes`:

```markdown
| `PIPELINE` built with `[*cv_sources("js"), ...]` → `AppRegistryNotReady` at startup | Keep it lazy: `cv_sources("js", before=[...], after=[...])` or `[...] + cv_sources("js")` (0.25.0) |
| Extension bundled by pipeline in CDN mode — its init script runs before the CDN plugin (W345) | Switch the extension to vendored mode (e.g. datetimepicker `SOURCE="vendored"` + `cv_vendor_datetimepicker`); find CDN entries with `manage.py cv_assets --external` |
```

- [ ] **Step 4: api-reference.md**

Under `### Asset registry / CSP settings` add to the code block:

```python
CRUD_VIEWS_ASSETS_BUNDLED = False        # True: cv_js/cv_css emit only CDN entries; pipeline bundles the rest (0.25.0)
```

In the import cheatsheet, after the `crud_views.lib.assets` line, add:

```python
from crud_views.lib.pipeline import cv_sources   # django-pipeline source_filenames (settings-time safe)
```

In `## Asset registry (`crud_views.lib.assets`)` extend the table:

```markdown
| `CORE_KEY` | `"crud_views"` | Reserved key of the core bundle (0.25.0). |
| `iter_bundles` | `(only_emitting=False)` | Core bundle first, then registered bundles (0.25.0). |
| `collect` | `(kind, *, only_emitting=False)` | `list[BundleEntry(key, emit, asset)]` in render order (0.25.0). |
| `cv_sources` (`crud_views.lib.pipeline`) | `(kind, *, before=(), after=(), keys=None, exclude=())` | Returns `LazySources`; resolves on access; drops CDN entries; includes `emit=False` bundles (0.25.0). |
```

Replace the `**Checks:**` paragraph with:

```markdown
**Checks:** `crud_views.E330` (integrity not `sha256-`/`sha384-`/`sha512-` prefixed),
`crud_views.W332` (integrity on a same-origin static path), and for the pipeline integration (0.25.0)
`W340`–`W345` (see SKILL.md "Bundling with django-pipeline").

**Command:** `manage.py cv_assets [--external] [--kind js|css] [--format table|json]` lists every
asset with its delivery (`tag`, `tag (CDN)`, `pipeline:<package>`, `none`, `none (emit=False)`) (0.25.0).
```

- [ ] **Step 5: Plugin CHANGELOG** — under `## [Unreleased]` in `plugins/django-crud-views/CHANGELOG.md`:

```markdown
### Added
- Package 0.25.0 notes: bundling registry assets into django-pipeline with the lazy `cv_sources()`,
  `CRUD_VIEWS_ASSETS_BUNDLED`, checks W340–W345, the `cv_assets` listing command; Common Mistakes
  rows for eager `cv_sources()` expansion and bundling an extension in CDN mode.
```

- [ ] **Step 6: Drift audit (executable, not by reading)**

Re-create the audit harness in the session scratchpad (it is not persisted): configure Django
against the installed package, then assert (a) every `from crud_views* import X` in SKILL.md and
api-reference.md resolves — use two separate regexes for single-line and parenthesised imports;
(b) every `CRUD_VIEWS_*` string maps to a `CrudViewsSettings` field (`CRUD_VIEWS_MANAGE` is a group
name, `CRUD_VIEWS_OBJECT_DETAIL_*` lives in `crud_views_object_detail/lib/conf.py`). Plant a bogus
import (`from crud_views.lib.pipeline import nope`) and confirm the harness fails, then remove it.
Expected: harness passes for the edited skill, including `cv_sources` and `CRUD_VIEWS_ASSETS_BUNDLED`.

- [ ] **Step 7: Commit and push (skills repo, one invocation)**

```bash
git -C /home/alex/projects/alex/skills add plugins/django-crud-views && \
git -C /home/alex/projects/alex/skills commit -m "django-crud-views: document django-pipeline bundling (package 0.25.0)" && \
git -C /home/alex/projects/alex/skills push origin main && \
test "$(git -C /home/alex/projects/alex/skills rev-parse HEAD)" = "$(git -C /home/alex/projects/alex/skills rev-parse origin/main)"
```

Plugin release (`scripts/release.sh django-crud-views X.Y.Z`, `--dry-run` first, then push with
`--follow-tags` and verify the tag via `git ls-remote --tags origin`) only when the user asks for it.

---

## Self-review notes (spec coverage)

- Spec §1 core bundle / reserved key / `collect` / tags → Tasks 1–2. `get_registered()` unchanged → Task 1 (no edits to it).
- Spec §2 `cv_sources`, guard, `+`, repr, introspection, unknown keys ignored at resolution → Task 3 (unknown keys: `registry_entries` simply matches nothing).
- Spec §3 W340–W345, coverage incl. plain-string globs → Tasks 4–5.
- Spec §3b `cv_assets`, shared resolver → Tasks 4, 6.
- Spec §4 test dep + Django 6 risk + integration → Task 7; docs/changelog → Task 8; skill → Task 9.
- Deviation from spec, recorded: the spec's integration test used `override_settings(PIPELINE=...)`;
  the plan uses `Packager(js_packages=..., css_packages=...)` plus `monkeypatch.setitem` on
  `pipeline.conf.settings`, because pipeline's `reload_settings` receiver breaks on `override_settings`
  exit. `collect()` returns `BundleEntry` instead of `Asset`.
