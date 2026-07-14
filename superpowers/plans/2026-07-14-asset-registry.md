# Core Asset Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a public asset registry to django-crud-views so any Django app can contribute JS/CSS to `{% cv_js %}` / `{% cv_css %}` output by registering in `AppConfig.ready()`, plus a reusable vendor-download helper and a `{{ form.media }}` template bugfix.

**Architecture:** A module-level registry (`crud_views/lib/assets.py`) collects `AssetBundle`s during app loading; the `cv_js`/`cv_css` inclusion tags merge core assets with registered bundles at render time, resolving static paths vs. external URLs in Python so the shared templates stay dumb. A separate `crud_views/lib/vendor.py` provides download-and-stamp infrastructure for extension modules that vendor third-party JS.

**Tech Stack:** Django 5.x, pytest + pytest-django (settings via `tests/test1/conftest.py`'s `settings.configure`), pytest-mock, uv, hatchling src-layout.

## Hand-over: context for a fresh session

You are implementing **Workstream 1** of the spec at
`superpowers/specs/2026-07-14-asset-registry-and-extensions-design.md`. **Read the spec first.**
Workstream 2 (a separate `django-crud-views-extensions` repo, planned in
`superpowers/plans/2026-07-14-extensions-datetimepicker.md`) depends on this work being finished —
you do not touch it here.

- **Repo:** `/home/alex/projects/alex/django-crud-views` (canonical checkout; ignore the copy at
  `gas2gas/submodules/django-crud-views`, it is behind).
- **Layout:** `src/` layout. Package code in `src/crud_views/`, sibling theme app `src/crud_views_plain/`.
- **Branch:** As of planning (2026-07-14) the working tree was on `feat/conditional-field-groups`
  with an untracked `cred.prompt.md` (leave that file alone). Before starting: `git status` must be
  clean apart from untracked files. The repo's default branch is `main` (not master), and the
  work branch `feat/asset-registry` already exists at the `main` tip: `git switch feat/asset-registry`.
  A `.superpowers/sdd/progress.md` ledger exists — check it for completed tasks before starting.
- **Install deps (if imports fail):** `uv pip install --upgrade .[ordered,polymorphic,workflow,dev,test]`
- **Run tests:** `uv run pytest tests/test1/ -x -q` for the suite, `uv run pytest tests/test1/test_assets.py -v`
  for the new file. The full matrix (`task test` → nox) is slow; run it once at the very end.
- **Test settings:** there is no settings module; `tests/test1/conftest.py` calls `settings.configure(...)`.
  Tests using DB need `@pytest.mark.django_db`.
- **Check IDs:** the repo uses `crud_views.E3xx`/`W3xx` (existing: E300, E310, E311, W320). This plan
  introduces W330, W331. (The extensions plan will use E332.)
- **Versioning/release:** current version 0.10.2. Do NOT bump the version; the maintainer releases
  via `bump-my-version` (this feature will become 0.11.0). Only update `CHANGELOG.md` under `## Unreleased`.
- **Commit style:** short imperative subject lines, `feat:`/`fix:`/`test:`/`docs:` prefixes are fine.

## Global Constraints

- New public API surface is exactly: `AssetBundle`, `register_assets`, `get_registered` (in `crud_views.lib.assets`) and `VendorSpec`, `vendor`, `check_vendored`, `STAMP_NAME` (in `crud_views.lib.vendor`). Nothing else is exported.
- Entries starting with `http://`, `https://`, or `//` are external URLs rendered verbatim; everything else resolves through `django.templatetags.static.static()`.
- Core assets always render **before** registered bundles; registered bundles render in registration order.
- Duplicate registry key → `ImproperlyConfigured` at registration time.
- No new runtime dependencies (vendor download uses `urllib.request` from stdlib). No django-pipeline anywhere in core.
- Output of `cv_js`/`cv_css` with an empty registry must be byte-identical to today's output (regression guard).

---

### Task 1: Registry module `crud_views/lib/assets.py`

**Files:**
- Create: `src/crud_views/lib/assets.py`
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Produces: `AssetBundle(key: str, js: tuple[str, ...], css: tuple[str, ...], emit: bool)`,
  `register_assets(key, js=(), css=(), emit=True) -> None`,
  `get_registered(only_emitting=False) -> list[AssetBundle]`,
  `is_external(entry: str) -> bool`, `resolve_url(entry: str) -> str`.
  Task 2 consumes all of these; the extensions repo consumes `register_assets`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_assets.py`:

```python
import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def asset_registry():
    """Snapshot/restore the module-global registry around each test."""
    from crud_views.lib import assets

    snapshot = dict(assets._REGISTRY)
    assets._REGISTRY.clear()
    yield assets
    assets._REGISTRY.clear()
    assets._REGISTRY.update(snapshot)


def test_register_and_get(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"], css=["a/one.css"])
    asset_registry.register_assets(key="b", js=["b/two.js"])

    bundles = asset_registry.get_registered()
    assert [b.key for b in bundles] == ["a", "b"]  # registration order
    assert bundles[0].js == ("a/one.js",)
    assert bundles[0].css == ("a/one.css",)
    assert bundles[1].css == ()
    assert bundles[0].emit is True


def test_duplicate_key_raises(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    with pytest.raises(ImproperlyConfigured, match="already registered"):
        asset_registry.register_assets(key="a", js=["other.js"])


def test_only_emitting_filters(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"], emit=False)
    asset_registry.register_assets(key="b", js=["b/two.js"])

    assert [b.key for b in asset_registry.get_registered()] == ["a", "b"]
    assert [b.key for b in asset_registry.get_registered(only_emitting=True)] == ["b"]


def test_is_external(asset_registry):
    assert asset_registry.is_external("https://cdn.example.com/x.js")
    assert asset_registry.is_external("http://cdn.example.com/x.js")
    assert asset_registry.is_external("//cdn.example.com/x.js")
    assert not asset_registry.is_external("crud_views/js/viewset.js")


def test_resolve_url(asset_registry):
    assert asset_registry.resolve_url("//cdn.example.com/x.js") == "//cdn.example.com/x.js"
    # STATIC_URL in tests/test1/conftest.py is "/static/"
    assert asset_registry.resolve_url("crud_views/js/viewset.js") == "/static/crud_views/js/viewset.js"
```

Note: if `STATIC_URL` is not `/static/` in `tests/test1/conftest.py`, adjust the last assertion to the configured value (check the `settings.configure(...)` call).

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test1/test_assets.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'crud_views.lib.assets'`

- [ ] **Step 3: Write the implementation**

Create `src/crud_views/lib/assets.py`:

```python
"""Public asset registry: apps contribute JS/CSS to cv_js/cv_css via AppConfig.ready()."""

from dataclasses import dataclass
from threading import Lock
from typing import Iterable, List

from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static

_EXTERNAL_PREFIXES = ("http://", "https://", "//")


@dataclass(frozen=True)
class AssetBundle:
    key: str
    js: tuple = ()
    css: tuple = ()
    emit: bool = True


_REGISTRY: dict = {}
_LOCK = Lock()


def register_assets(key: str, js: Iterable[str] = (), css: Iterable[str] = (), emit: bool = True) -> None:
    """Register an asset bundle. Call from AppConfig.ready().

    Entries are static paths, or external URLs (http://, https://, //) rendered verbatim.
    Bundles render after core assets, in registration order (= INSTALLED_APPS order).
    """
    with _LOCK:
        if key in _REGISTRY:
            raise ImproperlyConfigured(f"crud_views asset bundle {key!r} is already registered")
        _REGISTRY[key] = AssetBundle(key=key, js=tuple(js), css=tuple(css), emit=emit)


def get_registered(only_emitting: bool = False) -> List[AssetBundle]:
    with _LOCK:
        bundles = list(_REGISTRY.values())
    if only_emitting:
        bundles = [b for b in bundles if b.emit]
    return bundles


def is_external(entry: str) -> bool:
    return entry.startswith(_EXTERNAL_PREFIXES)


def resolve_url(entry: str) -> str:
    """External URLs pass through; static paths resolve via the configured staticfiles storage."""
    return entry if is_external(entry) else static(entry)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test1/test_assets.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/assets.py tests/test1/test_assets.py
git commit -m "feat: add public asset registry (crud_views.lib.assets)"
```

---

### Task 2: Render registered bundles through `cv_js` / `cv_css`

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (the `cv_css` and `cv_js` functions, near the top of the file)
- Modify: `src/crud_views/templates/crud_views/shared/js.html`
- Modify: `src/crud_views/templates/crud_views/shared/css.html`
- Test: `tests/test1/test_assets.py` (extend)

**Interfaces:**
- Consumes: `get_registered(only_emitting=True)`, `resolve_url()` from Task 1.
- Produces: template context shape `{"js": [{"url": str}, ...]}` / `{"css": [{"url": str}, ...]}` for the shared templates. Extension apps rely on the rendering order: core first, then bundles.

**Pre-check:** `crud_views_plain` overrides some `crud_views/` templates by app precedence. Run
`ls src/crud_views_plain/templates/crud_views/shared/ 2>/dev/null` — if `js.html`/`css.html` exist
there too, apply the same template change to those copies. (At planning time only the bootstrap5
theme in `src/crud_views/templates/` had them, but verify.)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_assets.py`:

```python
from django.template import Context, Template


def _render(tag: str) -> str:
    return Template("{% load crud_views %}{% " + tag + " %}").render(Context({}))


def test_cv_js_renders_core_then_registered(asset_registry):
    asset_registry.register_assets(
        key="picker",
        js=["picker/plugin.js", "https://cdn.example.com/extra.js"],
        css=["picker/plugin.css"],
    )
    html = _render("cv_js")
    # core asset still present and resolved via static()
    assert "/static/crud_views/js/viewset.js" in html
    # registered static path resolved, external URL verbatim
    assert "/static/picker/plugin.js" in html
    assert 'src="https://cdn.example.com/extra.js"' in html
    # order: core before registered
    assert html.index("crud_views/js/viewset.js") < html.index("picker/plugin.js")


def test_cv_css_renders_registered(asset_registry):
    asset_registry.register_assets(key="picker", css=["picker/plugin.css"])
    html = _render("cv_css")
    assert "/static/crud_views/css/property.css" in html
    assert "/static/picker/plugin.css" in html
    assert html.index("property.css") < html.index("picker/plugin.css")


def test_emit_false_not_rendered(asset_registry):
    asset_registry.register_assets(key="picker", js=["picker/plugin.js"], emit=False)
    html = _render("cv_js")
    assert "picker/plugin.js" not in html


def test_empty_registry_output_unchanged(asset_registry):
    # regression guard: with nothing registered, all core assets and nothing else
    html = _render("cv_js")
    assert "/static/crud_views/js/viewset.js" in html
    assert "/static/crud_views/js/formset.js" in html
    assert "/static/crud_views/js/list.filter.js" in html
    assert "/static/crud_views/js/modal.js" in html
    assert html.count("<script") == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test1/test_assets.py -v`
Expected: the four new tests FAIL (`picker/plugin.js` missing; templates still iterate `js.values`).
`test_empty_registry_output_unchanged` may already pass — that is fine.

- [ ] **Step 3: Modify the template tags**

In `src/crud_views/templatetags/crud_views.py`, add to the imports block:

```python
from crud_views.lib import assets
```

Replace the existing `cv_css` and `cv_js` functions:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = list(crud_views_settings.css.values())
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.css)
    return {"css": [{"url": assets.resolve_url(entry)} for entry in entries]}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = list(crud_views_settings.javascript().values())
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.js)
    return {"js": [{"url": assets.resolve_url(entry)} for entry in entries]}
```

(Note: `crud_views_settings.javascript` is a method, `crud_views_settings.css` is a `cached_property` — keep the call/no-call distinction exactly as above.)

- [ ] **Step 4: Modify the shared templates**

`src/crud_views/templates/crud_views/shared/js.html` (full new content):

```django
{% for item in js %}
    <script type="application/javascript" src="{{ item.url }}"></script>
{% endfor %}
```

`src/crud_views/templates/crud_views/shared/css.html` (full new content):

```django
{% for item in css %}
    <link rel="stylesheet" href="{{ item.url }}">
{% endfor %}
```

(The `{% load static %}` lines are removed — URL resolution now happens in Python.)

- [ ] **Step 5: Run the new tests, then the whole suite**

Run: `uv run pytest tests/test1/test_assets.py -v`
Expected: all PASS

Run: `uv run pytest tests/test1/ -x -q`
Expected: PASS (any failure here means an existing template/tag consumer broke — fix before continuing).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/shared/js.html src/crud_views/templates/crud_views/shared/css.html tests/test1/test_assets.py
git commit -m "feat: cv_js/cv_css render registered asset bundles (static paths and external URLs)"
```

---

### Task 3: Vendor helper `crud_views/lib/vendor.py`

**Files:**
- Create: `src/crud_views/lib/vendor.py`
- Test: `tests/test1/test_vendor.py`

**Interfaces:**
- Produces: `VendorSpec(key, version, base_url, files, target)` with property `resolved_base_url`;
  `vendor(spec) -> list[Path]`; `check_vendored(spec) -> list[CheckMessage]`; `STAMP_NAME = ".vendored"`.
  The extensions repo builds its vendor command and system check on exactly these names.
- Check IDs: `crud_views.W330` (vendored files missing), `crud_views.W331` (vendored version mismatch).

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_vendor.py`:

```python
import json
from pathlib import Path

import pytest

from crud_views.lib.vendor import STAMP_NAME, VendorSpec, check_vendored, vendor


@pytest.fixture
def spec(tmp_path) -> VendorSpec:
    return VendorSpec(
        key="picker",
        version="1.2.3",
        base_url="https://cdn.example.com/pkg@{version}/build/",
        files=("plugin.js", "plugin.css"),
        target=tmp_path / "picker" / "1.2.3",
    )


def test_resolved_base_url(spec):
    assert spec.resolved_base_url == "https://cdn.example.com/pkg@1.2.3/build/"


def test_vendor_downloads_and_stamps(spec, mocker):
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    written = vendor(spec)

    assert [p.name for p in written] == ["plugin.js", "plugin.css"]
    assert (spec.target / "plugin.js").read_bytes() == b"content"
    fake.assert_any_call("https://cdn.example.com/pkg@1.2.3/build/plugin.js")
    stamp = json.loads((spec.target / STAMP_NAME).read_text())
    assert stamp == {"key": "picker", "version": "1.2.3"}


def test_check_missing_stamp_warns_W330(spec):
    messages = check_vendored(spec)
    assert len(messages) == 1
    assert messages[0].id == "crud_views.W330"


def test_check_version_mismatch_warns_W331(spec):
    spec.target.mkdir(parents=True)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": "picker", "version": "9.9.9"}))
    messages = check_vendored(spec)
    assert len(messages) == 1
    assert messages[0].id == "crud_views.W331"


def test_check_ok_is_silent(spec):
    spec.target.mkdir(parents=True)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": "picker", "version": "1.2.3"}))
    assert check_vendored(spec) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test1/test_vendor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crud_views.lib.vendor'`

- [ ] **Step 3: Write the implementation**

Create `src/crud_views/lib/vendor.py`:

```python
"""Reusable download-and-stamp infrastructure for extension apps that vendor third-party JS/CSS.

Extension apps build a VendorSpec from their settings and get a ~10-line management
command (call vendor()) plus a drift system check (call check_vendored()) for free.
The target directory must be a project directory on STATICFILES_DIRS — never an
installed package's static/ directory.
"""

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List

from django.core.checks import CheckMessage
from django.core.checks import Warning as CheckWarning

STAMP_NAME = ".vendored"


@dataclass(frozen=True)
class VendorSpec:
    key: str            # registry/bundle key, e.g. "datetimepicker"
    version: str        # pinned upstream version
    base_url: str       # URL template containing {version}
    files: tuple        # filenames to download
    target: Path        # destination directory (should embed the version in its path)

    @property
    def resolved_base_url(self) -> str:
        return self.base_url.format(version=self.version)


def vendor(spec: VendorSpec) -> List[Path]:
    """Download spec.files into spec.target and write a version stamp."""
    spec.target.mkdir(parents=True, exist_ok=True)
    written = []
    base = spec.resolved_base_url.rstrip("/")
    for name in spec.files:
        path = spec.target / name
        with urllib.request.urlopen(f"{base}/{name}") as response:  # noqa: S310
            path.write_bytes(response.read())
        written.append(path)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": spec.key, "version": spec.version}))
    return written


def check_vendored(spec: VendorSpec) -> List[CheckMessage]:
    """System-check helper: warn when configured pin and vendored files drift."""
    stamp = spec.target / STAMP_NAME
    if not stamp.exists():
        return [
            CheckWarning(
                f"crud_views asset bundle {spec.key!r} is configured as vendored, "
                f"but no vendored files were found at {spec.target}.",
                hint=f"Run the vendor management command for {spec.key!r}.",
                id="crud_views.W330",
            )
        ]
    data = json.loads(stamp.read_text())
    if data.get("version") != spec.version:
        return [
            CheckWarning(
                f"crud_views asset bundle {spec.key!r}: vendored version "
                f"{data.get('version')!r} does not match configured version {spec.version!r}.",
                hint=f"Re-run the vendor management command for {spec.key!r}.",
                id="crud_views.W331",
            )
        ]
    return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test1/test_vendor.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/vendor.py tests/test1/test_vendor.py
git commit -m "feat: add vendor helper (download + version stamp + drift check W330/W331)"
```

---

### Task 4: `{{ form.media }}` template bugfix

**Files:**
- Modify: `src/crud_views/templates/crud_views/view_update.content.html`
- Modify: `src/crud_views_plain/templates/crud_views/view_create.content.html`
- Modify: `src/crud_views_plain/templates/crud_views/view_update.content.html`
- Test: `tests/test1/test_assets.py` (extend)

**Interfaces:**
- Consumes: test app fixtures from `tests/test1/conftest.py`: `client_user_author_change`,
  `cv_author`, `author_douglas_adams`; view classes `AuthorUpdateView` and form `AuthorForm`
  from `tests/test1/app/views.py`. (If `AuthorForm` lives elsewhere, follow the
  `form_class = AuthorForm` reference at `tests/test1/app/views.py:121` to its import.)

Bug: the bootstrap5 theme renders `{{ form.media }}` only in `view_create.content.html`; the plain
theme renders it nowhere. Widgets declaring `class Media` silently lose their CSS/JS on update views.

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_assets.py`:

```python
from django import forms


@pytest.mark.django_db
def test_update_view_renders_form_media(client_user_author_change, cv_author, author_douglas_adams, mocker):
    from tests.test1.app.views import AuthorForm, AuthorUpdateView

    class MediaProbeInput(forms.TextInput):
        class Media:
            js = ["probe/widget-media-probe.js"]
            css = {"all": ["probe/widget-media-probe.css"]}

    class AuthorMediaForm(AuthorForm):
        class Meta(AuthorForm.Meta):
            widgets = {"first_name": MediaProbeInput()}

    mocker.patch.object(AuthorUpdateView, "form_class", AuthorMediaForm)

    response = client_user_author_change.get(f"/author/{author_douglas_adams.pk}/update/")
    assert response.status_code == 200
    assert b"widget-media-probe.js" in response.content
    assert b"widget-media-probe.css" in response.content
```

Add `@pytest.mark.django_db` if the fixtures require it (mirror the marker usage of
`tests/test1/test_permissions_full.py`).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test1/test_assets.py::test_update_view_renders_form_media -v`
Expected: FAIL on `assert b"widget-media-probe.js" in response.content`

- [ ] **Step 3: Fix the templates**

`src/crud_views/templates/crud_views/view_update.content.html` — append `{{ form.media }}` after the
form, exactly like the create template. Full new content:

```django
{% load crud_views %}

<form class="cv-form" method="post" action="{{ request.path }}" enctype="multipart/form-data" novalidate>
    {% csrf_token %}

    {{ form.non_form_errors }}

    {% cv_render_form %}
</form>

{{ form.media }}
```

`src/crud_views_plain/templates/crud_views/view_create.content.html` — full new content:

```django
{% load crud_views %}

<form class="cv-form" method="post" novalidate>
    {% csrf_token %}

    {{ form.non_form_errors }}

    {% cv_render_form %}
</form>

{{ form.media }}
```

`src/crud_views_plain/templates/crud_views/view_update.content.html` — full new content:

```django
{% load crud_views %}

<form class="cv-form" method="post" novalidate>
    {% csrf_token %}

    {{ form.non_form_errors }}

    {% cv_render_form %}
</form>

{{ form.media }}
```

- [ ] **Step 4: Run the test, then the whole suite**

Run: `uv run pytest tests/test1/test_assets.py -v`
Expected: PASS

Run: `uv run pytest tests/test1/ -x -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates/crud_views/view_update.content.html src/crud_views_plain/templates/crud_views/view_create.content.html src/crud_views_plain/templates/crud_views/view_update.content.html tests/test1/test_assets.py
git commit -m "fix: render form.media on update views (bootstrap5) and create/update views (plain theme)"
```

---

### Task 5: Documentation and changelog

**Files:**
- Create: `docs/reference/assets.md`
- Modify: `CHANGELOG.md` (under `## Unreleased` → `### Added` / `### Fixed`)

**Interfaces:**
- Consumes: the APIs from Tasks 1-3 (documented verbatim; do not invent parameters).

Note: mkdocs uses the `awesome-pages` plugin with no explicit `nav:` — a new file under
`docs/reference/` is picked up automatically. No `mkdocs.yml` change needed.

- [ ] **Step 1: Write `docs/reference/assets.md`**

```markdown
# Asset registry

Any Django app can contribute JavaScript and CSS to the output of `{% cv_js %}` and
`{% cv_css %}` by registering an asset bundle in its `AppConfig.ready()`:

    # myextension/apps.py
    from django.apps import AppConfig

    class MyExtensionConfig(AppConfig):
        name = "myextension"

        def ready(self):
            from crud_views.lib.assets import register_assets
            register_assets(
                key="myextension",
                js=["myextension/plugin.js", "myextension/init.js"],
                css=["myextension/plugin.css"],
            )

Rules:

- Entries are static paths resolved through `{% static %}` — unless they start with
  `http://`, `https://` or `//`, in which case they are rendered verbatim (CDN mode).
- Core assets always render first; registered bundles follow in registration order,
  which equals `INSTALLED_APPS` order.
- `key` must be unique; registering the same key twice raises `ImproperlyConfigured`.
- `register_assets(..., emit=False)` keeps the bundle registered (its system checks
  still run) but excludes it from tag output — use this when a bundler such as
  django-pipeline delivers the files instead.
- jQuery is **not** managed by the registry. As with core's own scripts, the project
  loads jQuery in its base template before `{% cv_js %}`.

## Vendoring third-party files

`crud_views.lib.vendor` provides shared infrastructure for extension apps that offer a
"download the pinned version locally" management command:

    from crud_views.lib.vendor import VendorSpec, vendor, check_vendored

    spec = VendorSpec(
        key="myextension",
        version="1.2.3",
        base_url="https://cdn.jsdelivr.net/npm/some-pkg@{version}/dist/",
        files=("plugin.js", "plugin.css"),
        target=vendor_dir / "myextension" / "1.2.3",
    )
    vendor(spec)            # downloads files + writes a version stamp
    check_vendored(spec)    # system-check messages on drift (W330 missing, W331 mismatch)

The target must be a project directory that is on `STATICFILES_DIRS` — never a
directory inside an installed package.
```

- [ ] **Step 2: Update `CHANGELOG.md`**

Under `## Unreleased`, extend `### Added` and add `### Fixed` (keep existing entries):

```markdown
### Added
- Asset registry: apps can contribute JS/CSS to `{% cv_js %}`/`{% cv_css %}` via
  `crud_views.lib.assets.register_assets()` in `AppConfig.ready()`. Supports static
  paths and external URLs, `emit=False` suppression for bundler setups, and a
  reusable vendor helper (`crud_views.lib.vendor`) with drift checks W330/W331.
  See `docs/reference/assets.md`.

### Fixed
- `{{ form.media }}` is now rendered on update views (bootstrap5 theme) and on
  create/update views (plain theme); previously only bootstrap5 create views loaded
  widget media.
```

- [ ] **Step 3: Full suite + commit**

Run: `uv run pytest tests/test1/ -q`
Expected: PASS

```bash
git add docs/reference/assets.md CHANGELOG.md
git commit -m "docs: document asset registry and vendor helper"
```

---

## Completion

- Run the full matrix once: `task test` (nox). Expected: PASS.
- Do NOT bump the version — hand back to the maintainer for release (this becomes 0.11.0,
  which the extensions repo will pin as its minimum).
- Open a PR from `feat/asset-registry` to `main`, or hand the branch back for review.
