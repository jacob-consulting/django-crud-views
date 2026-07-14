# Asset Registry + django-crud-views-extensions — Design

**Date:** 2026-07-14
**Status:** Draft for review
**Origin:** Brainstormed in the gas2gas project (extracting the xdsoft datetimepicker
widgets from `viho_ui` for reuse); see `gas2gas/docs/integration-xdsoft-datetimepicker.md`
for the widget code being extracted.

## Goal

Two deliverables, in dependency order:

1. **Workstream 1 — django-crud-views core:** a public *asset registry* so that any
   Django app can contribute JS/CSS to the `{% cv_js %}` / `{% cv_css %}` output just
   by being in `INSTALLED_APPS`. This is a lasting core upgrade, independent of any
   particular widget.
2. **Workstream 2 — new repo `django-crud-views-extensions`:** an incubator
   distribution holding widget/field apps that build on that registry. First app:
   `crud_views_widget_datetimepicker` (xdsoft jQuery DateTimePicker). Apps mature in
   real projects and may later be merged into django-crud-views proper.

Non-goal: the widget apps do **not** need to work without django-crud-views. They may
import from `crud_views` freely.

## Constraints & context

- Today the asset lists are hardcoded in `CrudViewsSettings.javascript` / `.css`
  (`src/crud_views/lib/settings.py`) and rendered by the inclusion tags `cv_js` /
  `cv_css` via `shared/js.html` / `shared/css.html`, which pass every entry through
  `{% static %}`. There is no extension point.
- jQuery is a project-provided prerequisite (core's `formset.js` already assumes it;
  the example projects load it in their own `base.html`). The datetimepicker module
  assumes it the same way. Ordering is safe because `{% cv_js %}` sits after the
  project's jQuery tag.
- **django-pipeline is planned** in consuming projects. Pipeline builds bundles from
  *local* static files listed in `PIPELINE` **settings** (evaluated before
  `AppConfig.ready()`). The design must let a project move a module's assets into a
  pipeline bundle without double-emission and without duplicated path lists.
- German/EU deployments: CDN mode leaks visitor IPs (GDPR); vendored mode must be a
  first-class path, not an afterthought.

---

## Workstream 1 — core asset registry

### 1.1 Registry API (`src/crud_views/lib/assets.py`)

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AssetBundle:
    key: str                      # unique, e.g. "datetimepicker"
    js: tuple[str, ...] = ()      # static paths or absolute URLs
    css: tuple[str, ...] = ()
    emit: bool = True             # False: registered but not rendered by cv_js/cv_css

def register_assets(key: str, js=(), css=(), emit: bool = True) -> None: ...
def get_registered(only_emitting: bool = False) -> list[AssetBundle]: ...
```

- Called from an extension app's `AppConfig.ready()`. Registration order therefore
  follows `INSTALLED_APPS` order — deterministic.
- Registering a duplicate `key` raises `ImproperlyConfigured` immediately (this is a
  programming error, not a runtime condition).
- Entries are **static paths by default**; values starting with `http://`, `https://`
  or `//` are treated as external URLs (CDN) and rendered verbatim.
- `emit=False` keeps the bundle registered (so system checks tied to it still run)
  while suppressing tag output — the hook that makes pipeline bundling double-emission
  free (see 1.4 and 2.6).

### 1.2 Rendering

`cv_js` / `cv_css` render **core assets first, then registered bundles in
registration order**. The settings layer resolves each entry to
`{"url": <static() result or verbatim URL>}` in Python, so the shared templates
stay dumb:

```django
{# shared/js.html #}
{% for item in js %}<script type="application/javascript" src="{{ item.url }}"></script>{% endfor %}
```

(Same for `css.html` with `<link rel="stylesheet">`.) Calling `static()` in Python
rather than templating `{% static %}` is what allows mixing external URLs and static
paths in one list. `ManifestStaticFilesStorage` keeps working because `static()`
goes through the configured storage.

### 1.3 Reusable vendor helper (`src/crud_views/lib/vendor.py`)

Generic infrastructure so each extension's vendor command is ~10 lines:

```python
@dataclass(frozen=True)
class VendorSpec:
    key: str                       # matches the registry key
    version: str                   # pinned version
    base_url: str                  # e.g. "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"
    files: tuple[str, ...]         # filenames to fetch
    target: Path                   # VENDOR_DIR / <app label> / <version> /

def vendor(spec: VendorSpec) -> None          # download files + write ".vendored" stamp (key, version)
def check_vendored(spec: VendorSpec) -> list[CheckMessage]   # system check helper
```

- `vendor()` downloads into `target`, then writes a stamp file recording key +
  version. It never writes into an installed package's `static/` — the target is
  always a project directory.
- `check_vendored()` returns a warning (`crud_views.W330` missing stamp,
  `crud_views.W331` version mismatch — following the repo's existing `crud_views.E3xx/W3xx`
  check-ID range) when a module is configured
  as vendored but the stamp is missing or its version differs from the configured pin
  — drift between settings and disk is caught at startup, not in the browser.
- Version is part of the directory name, so bumping the pin can never serve stale
  cached files.

### 1.4 Pipeline posture (core)

Core gains **no django-pipeline dependency, import, or extra** — there is no runtime
touchpoint. Pipeline-compat is achieved structurally: extension modules expose their
file lists as settings-time-safe functions (2.4), and `emit=False` suppresses tag
output for bundled modules. Core's own assets (`viewset.js`, …) keep the current
mechanism; migrating them onto the registry (and thus making them `emit`-suppressible
too) is a possible follow-up, out of scope here.

### 1.5 Bugfix: `{{ form.media }}` on the update view

`crud_views/view_update.content.html` (bootstrap5 theme) does not render
`{{ form.media }}`, while `view_create.content.html` does. Independent of this design
(which no longer relies on form media), that is a bug for anyone using standard
`Media`-declaring widgets. Fix: add `{{ form.media }}` after the form, matching the
create template. Check the plain theme for the same omission.

### 1.6 Core tests

- Registry: registration order, duplicate-key error, `emit=False` exclusion,
  `get_registered()` filtering.
- Rendering: external URL passthrough vs `static()` resolution; core assets precede
  registered ones; output unchanged when nothing is registered (regression guard).
- Vendor helper: download + stamp with mocked HTTP; `check_vendored()` on missing /
  matching / mismatching stamp.
- Update-view template renders `form.media` for a widget with a `Media` class.

---

## Workstream 2 — `django-crud-views-extensions`

### 2.1 Repo layout

```
django-crud-views-extensions/
├── src/
│   └── crud_views_widget_datetimepicker/
│       ├── apps.py                # ready(): resolve settings, register_assets(...)
│       ├── widgets.py             # DateTimePickerInput, DatePickerInput, TimePickerInput
│       ├── assets.py              # source_files() — Django-free, settings-time safe
│       ├── checks.py              # vendored-drift system check via core helper
│       ├── management/commands/cv_vendor_datetimepicker.py
│       └── static/crud_views_widget_datetimepicker/init.js
├── tests/                         # pytest + test project; incl. pipeline profile (2.7)
├── examples/                      # optional pipeline-wired example project
└── pyproject.toml                 # hatchling; depends on django-crud-views >= <registry release>
```

Key decisions:

- **`src` layout**, matching core's own post-migration layout and viho/viho-ui.
  With several sibling apps in one distribution this also prevents accidental
  repo-root imports in tests.
- **One top-level Django app per widget**, named with the reserved prefix
  `crud_views_widget_*` — i.e. named *as if it already lived in core*. Because
  `INSTALLED_APPS` entries and import paths use app names (never the distribution
  name), merging a matured app back into django-crud-views later is a directory move
  plus packaging changes — **zero code changes in consuming projects**; only their
  pip requirement line changes.
- No pip extras: the datetimepicker app has no Python dependencies beyond
  django-crud-views itself. Installation = pip install + `INSTALLED_APPS` entry.

### 2.2 Settings

One dict per extension module, consistent with future widgets:

```python
CRUD_VIEWS_DATETIMEPICKER = {
    "SOURCE": "cdn",            # "cdn" | "vendored"
    "VERSION": "2.5.21",        # single pin used by both modes
    "CDN_BASE": "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/",
    "VENDOR_DIR": None,         # REQUIRED when SOURCE="vendored"; on STATICFILES_DIRS
    "EMIT": True,               # False once assets move into a pipeline bundle
    "LANG": None,               # None → derive from LANGUAGE_CODE ("de-de" → "de")
    "DEFAULTS": {},             # merged over built-in per-widget config defaults
}
```

- All keys optional except that `SOURCE="vendored"` without `VENDOR_DIR` raises a
  system check error (no guessed `BASE_DIR` magic).
- `VERSION` has a maintained default so CDN mode works with an empty dict.

### 2.3 App wiring (`apps.py`)

`ready()` resolves the settings dict, then:

- CDN mode: registers `CDN_BASE.format(version=...)` + filenames (minified variants)
  plus the app's own static `init.js`.
- Vendored mode: registers static paths
  `crud_views_widget_datetimepicker/<version>/<file>` (minified variants) + `init.js`.
- Passes `emit=EMIT` through to `register_assets`.
- Registers the drift system check (vendored mode only).

### 2.4 `assets.py` — single source of truth for paths

Django-free, importable from `settings.py` (for pipeline) and from `apps.py`:

```python
FILES = {
    True:  ("jquery.datetimepicker.full.min.js", "jquery.datetimepicker.min.css"),
    False: ("jquery.datetimepicker.full.js",     "jquery.datetimepicker.css"),
}

def source_files(version: str, minified: bool = True) -> dict[str, list[str]]:
    base = f"crud_views_widget_datetimepicker/{version}"
    js_file, css_file = FILES[minified]
    return {
        "js":  [f"{base}/{js_file}", "crud_views_widget_datetimepicker/init.js"],
        "css": [f"{base}/{css_file}"],
    }
```

A pipeline-adopting project builds its bundle from the same function that feeds the
registry — no duplicated lists, no settings-time/ready()-time chicken-and-egg:

```python
# settings.py of a consuming project, later
from crud_views_widget_datetimepicker.assets import source_files
_dtp = source_files(DTP_VERSION, minified=False)   # pipeline does the minifying
PIPELINE = {"javascript": {"main": {"source_filenames": [..., *_dtp["js"]], ...}}}
CRUD_VIEWS_DATETIMEPICKER = {..., "EMIT": False}
```

Bundle order must keep jQuery → plugin → `init.js`; pipeline preserves
`source_filenames` order — documented explicitly.

### 2.5 Widgets (`widgets.py`)

The three classes from viho_ui's `xdsoft.py`, with these changes:

- **No `Media` classes** — assets come exclusively from the registry. This makes the
  historic gotchas (update view missing `form.media`, modal-injected content lacking
  assets) structurally impossible.
- **No custom widget template** — the viho template was just an include of Django's
  stock input template; the widgets use the stock templates of their base classes.
- Behavior kept: `config` dict merged over per-class defaults, serialized as JSON into
  the `xdsoft-datetime-config` attribute; `fix_year` shortcut on `DateTimePickerInput`
  (sets `minDate`/`maxDate`/`yearStart`/`yearEnd`).
- Locale/format: built-in per-class format defaults stay (`d.m.Y H:i:s` / `d.m.Y` /
  `H:i`); `LANG` (or `LANGUAGE_CODE` fallback) is injected as `lang` into every
  config; `DEFAULTS` from settings merges over built-ins; per-field `config` wins.

### 2.6 `init.js`

Authored file, always served from the app's static dir (never vendored/CDN):

- On document ready: scan `input[xdsoft-datetime-config]`, parse JSON, call
  `jQuery.datetimepicker.setLocale(config.lang)` then `.datetimepicker(config)` per
  element.
- On `cv:modal:loaded` (fired on `#cv-modal` by core's modal transport): re-run the
  same initialization scoped to `#cv-modal` — modal support works out of the box.
- No `console.log` statements.

### 2.7 Vendor command + pipeline verification tests

- `cv_vendor_datetimepicker`: builds a `VendorSpec` from the settings dict (all four
  file variants: `full.js`, `full.min.js`, `.css`, `.min.css`) and calls core's
  `vendor()`. Prints a reminder that `VENDOR_DIR` must be on `STATICFILES_DIRS`.
- **Pipeline verification (django-pipeline as a dev/test dependency only):** a test
  settings profile where `PIPELINE` is built from `source_files(VERSION,
  minified=False)` and `EMIT` is `False`. Tests assert: the bundle compiles and
  contains plugin + `init.js` in order; `cv_js`/`cv_css` output no longer contains the
  picker assets; a rendered form page carries exactly one copy of each asset. This
  exercises 2.4, `emit=False`, and the unminified vendoring together.
- Remaining tests: widget attr/JSON rendering (incl. `fix_year`, `DEFAULTS` merge,
  lang injection); CDN vs vendored registration paths; vendor command with mocked
  download; system checks (vendored without `VENDOR_DIR`, stamp drift); a test that
  `source_files()` output matches exactly what the vendor command writes.

### 2.8 Rollout / maturity path

1. Core registry release of django-crud-views (Workstream 1).
2. New extensions repo; gas2gas adds it as an editable submodule, replaces
   `viho_ui.widgets.xdsoft` imports with `crud_views_widget_datetimepicker.widgets`,
   and drops the viho-ui widget usage. This is the maturity test bed.
3. When a widget app is deemed mature it may move into the django-crud-views repo
   unchanged (same app name); the extensions distribution then drops it in a major
   bump.

---

## Trade-offs accepted

- **Sitewide asset loading:** with `EMIT: True`, picker CSS/JS load on every page of
  a crud-views project (~70 KB, cached). Price of "add to `INSTALLED_APPS` and
  everything works, including modals". Projects that care can flip to a pipeline
  bundle or accept it.
- **CDN default:** zero-setup onboarding wins the default; docs recommend vendored
  for production (GDPR, CSP, supply chain) and mark CDN as not pipeline-bundleable.
- **Version-compat coupling:** extensions requires the core release carrying the
  registry; a minimum-version pin, no matrix testing while both are single-maintainer.

## Alternatives rejected

- **Widget app inside django-crud-views now** — core stays unopinionated about form
  widgets; incubator preserves iteration freedom; merge-back path kept open by naming.
- **Sibling repo per widget** — per-repo overhead × N widgets for a solo maintainer;
  one shared extensions repo instead.
- **Form `Media` as the delivery mechanism** — page-scoped but structurally broken for
  modal-injected content and bitten by the update-template omission; registry-only is
  one mechanism instead of two. (The update-template omission gets fixed anyway, 1.5.)
- **Filesystem autodiscovery (`crud_views_assets.py` magic module)** — explicit
  `register_assets()` in `ready()` is one line and greppable/debuggable.
- **`django-crud-views[pipeline]` extra** — no code imports pipeline; an extra would
  advertise a runtime integration that doesn't exist. Dev/test dependency instead.
