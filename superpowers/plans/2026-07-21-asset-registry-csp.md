# Asset Registry: Optional CSP Compliance (Nonces + SRI) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The `{% cv_js %}` / `{% cv_css %}` asset tags emit CSP nonces automatically (django-csp on Django 4.2/5.2 and Django 6 built-in CSP) and registrants can attach SRI `integrity`/`crossorigin` metadata per asset — with byte-identical output for projects without CSP.

**Architecture:** A frozen `Asset` dataclass replaces plain-string registry entries (strings still accepted, normalized at registration). A `_resolve_nonce(context)` helper in the templatetag layer auto-detects the nonce (request attribute → Django 6 `get_nonce()` → `csp_nonce` context var), force-evaluating via `str()` because Django 6's `LazyNonce` is falsy until evaluated. Two new system checks validate SRI metadata.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12–3.14, pytest, pydantic settings model, ruff.

**Spec:** `superpowers/specs/2026-07-21-asset-registry-csp-design.md` (read it first).

## Global Constraints

- No new runtime dependencies; **never import `django-csp`** (`csp` package). `django.middleware.csp` exists only on Django ≥ 6.0 — always guard with `try/except ImportError`.
- Zero behavior change without CSP: with no nonce source and no SRI metadata, rendered HTML must be **byte-identical** to current output.
- `register_assets()` signature unchanged; plain-string entries keep working.
- Nonce detection: **existence checks + `str()` force-evaluation, never truthiness** (Django 6 `LazyNonce.__bool__` is `False` until first evaluated).
- Line length 120, double quotes (ruff enforces; pre-commit runs `ruff-format`).
- New check IDs: `crud_views.E330` (malformed integrity), `crud_views.W331` (integrity on same-origin path). Existing IDs in use: E100s, E300, E310, E311, W320, W321 — do not collide.
- New setting: `CRUD_VIEWS_CSP_NONCE_ATTR`, default `"csp_nonce"`.
- Run tests from the `tests/` directory: `cd tests && pytest test1/test_assets.py -v`. Full suite: `cd tests && pytest`. The venv is `.venv` at repo root (activate or use `.venv/bin/pytest` — note tests/ has its own pytest config via `tests/test1/conftest.py` which calls `django.setup()` in `pytest_configure`).
- Local dev Django is 5.2.14, so the Django 6 e2e test (Task 5) is expected to **skip locally**; it runs in the nox/CI matrix.

## Background knowledge for the worker (verified facts)

1. **Django 6 built-in CSP** (`django/middleware/csp.py`): `ContentSecurityPolicyMiddleware.process_request` sets **private** `request._csp_nonce = LazyNonce()`. Public access is `django.middleware.csp.get_nonce(request)` (returns `None` if middleware didn't run) or the `django.template.context_processors.csp` context processor exposing `{{ csp_nonce }}`. `build_policy(config, nonce)` puts the nonce into the header only where the `CSP.NONCE` sentinel appears in `SECURE_CSP` — so force-generating an unused nonce is harmless.
2. **django-csp** (separate package, Django 4.2/5.2): middleware sets **public** `request.csp_nonce` (also lazy). We never import it; we just read the attribute, name configurable via `CRUD_VIEWS_CSP_NONCE_ATTR`.
3. **Current rendering chain:** `src/crud_views/templatetags/crud_views.py` defines inclusion tags `cv_css`/`cv_js` (`takes_context=True`) → build `{"css": [{"url": ...}]}` from `crud_views_settings.css` / `.javascript()` (plain string paths) plus `assets.get_registered(only_emitting=True)` bundles → templates `src/crud_views/templates/crud_views/shared/js.html` and `css.html` render plain `<script>`/`<link>` tags.
4. **Registry:** `src/crud_views/lib/assets.py` — module globals `_REGISTRY`/`_LOCK`, `AssetBundle` frozen dataclass with `js: tuple`/`css: tuple` of strings, `register_assets()`, `get_registered()`, `is_external()` (prefixes `http://`, `https://`, `//`), `resolve_url()`.
5. **Settings model:** `src/crud_views/lib/settings.py` — pydantic `CrudViewsSettings` with fields like `session_data_key: str = from_settings("CRUD_VIEWS_SESSION_DATA_KEY", "viewset")`; singleton `crud_views_settings = CrudViewsSettings()` at module end. **Py3.14/PEP 649 gotcha:** the class has a `cached_property` named `dict`; never annotate a field with a bare shadowed builtin name — `str` is safe here.
6. **Checks:** `src/crud_views/checks.py` — functions decorated `@register(TAG)` with `TAG = "crud_views"`, returning lists of `Error`/`DjangoWarning` (imported as `from django.core.checks import Warning as DjangoWarning`).
7. **Existing tests:** `tests/test1/test_assets.py` has an `asset_registry` fixture that snapshots/clears/restores `assets._REGISTRY`, and a `_render(tag)` helper: `Template("{% load crud_views %}{% " + tag + " %}").render(Context({}))`. Two existing assertions compare `bundles[0].js == ("a/one.js",)` — **Task 1 changes these to `Asset` tuples.**

---

### Task 1: `Asset` dataclass + registry normalization

**Files:**
- Modify: `src/crud_views/lib/assets.py`
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Asset(path: str, integrity: str | None = None, crossorigin: str | None = None)` (frozen dataclass, exported from `crud_views.lib.assets`); `normalize_entries(entries: Iterable) -> tuple[Asset, ...]`; `AssetBundle.js`/`.css` now tuples of `Asset`. `resolve_url()`/`is_external()` still take `str` (callers pass `asset.path`).

- [ ] **Step 1: Write the failing tests** — append to `tests/test1/test_assets.py`:

```python
def test_asset_normalization(asset_registry):
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(
        key="mixed",
        js=[
            "plain/path.js",
            Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc"),
        ],
        css=[Asset(path="plain/path.css")],
    )
    bundle = asset_registry.get_registered()[0]
    assert bundle.js == (
        Asset(path="plain/path.js"),
        Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc"),
    )
    assert bundle.css == (Asset(path="plain/path.css"),)
    assert bundle.js[0].integrity is None
    assert bundle.js[0].crossorigin is None


def test_normalize_entries(asset_registry):
    from crud_views.lib.assets import Asset, normalize_entries

    asset = Asset(path="a.js", integrity="sha384-abc", crossorigin="anonymous")
    assert normalize_entries(["a.js", asset]) == (Asset(path="a.js"), asset)
    assert normalize_entries([]) == ()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_assets.py -v -k "normaliz"`
Expected: FAIL/ERROR with `ImportError: cannot import name 'Asset'`

- [ ] **Step 3: Implement in `src/crud_views/lib/assets.py`** — add the `Asset` dataclass above `AssetBundle`, add `normalize_entries`, and normalize inside `register_assets`:

```python
@dataclass(frozen=True)
class Asset:
    """A single JS/CSS asset: a static path or external URL, with optional SRI metadata.

    integrity is meant for external URLs (see system checks E330/W331); when set and
    crossorigin is None, tags render crossorigin="anonymous".
    """

    path: str
    integrity: str | None = None
    crossorigin: str | None = None


def normalize_entries(entries: Iterable) -> tuple:
    """Normalize a mix of str and Asset entries to a tuple of Asset."""
    return tuple(entry if isinstance(entry, Asset) else Asset(path=entry) for entry in entries)
```

In `register_assets`, change the registry line to:

```python
        _REGISTRY[key] = AssetBundle(key=key, js=normalize_entries(js), css=normalize_entries(css))
```

(keep `emit=emit` — full line: `AssetBundle(key=key, js=normalize_entries(js), css=normalize_entries(css), emit=emit)`). Update the `register_assets` docstring first line to: `Entries are static paths, external URLs (http://, https://, //) rendered verbatim, or Asset instances carrying SRI metadata.` Update the module docstring or `AssetBundle` comment only if ruff complains — otherwise leave.

- [ ] **Step 4: Fix the two now-broken existing assertions** in `tests/test1/test_assets.py::test_register_and_get` — the registry stores `Asset` objects now:

```python
    from crud_views.lib.assets import Asset

    bundles = asset_registry.get_registered()
    assert [b.key for b in bundles] == ["a", "b"]  # registration order
    assert bundles[0].js == (Asset(path="a/one.js"),)
    assert bundles[0].css == (Asset(path="a/one.css"),)
```

- [ ] **Step 5: Run the whole asset test file** (the rendering tests must still pass — `cv_js`/`cv_css` break because they iterate bundle entries as strings; fix the tags minimally now by passing `entry.path`):

Run: `cd tests && pytest test1/test_assets.py -v`
Expected: rendering tests FAIL (`Asset` object passed to `resolve_url`). In `src/crud_views/templatetags/crud_views.py` change both tags to unpack registered entries — this is a temporary bridge that Task 3 rewrites:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = list(assets.normalize_entries(crud_views_settings.css.values()))
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.css)
    return {"css": [{"url": assets.resolve_url(entry.path)} for entry in entries]}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = list(assets.normalize_entries(crud_views_settings.javascript().values()))
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.js)
    return {"js": [{"url": assets.resolve_url(entry.path)} for entry in entries]}
```

Re-run: `cd tests && pytest test1/test_assets.py -v` → Expected: ALL PASS.

- [ ] **Step 6: Full suite + commit**

Run: `cd tests && pytest`
Expected: all pass (~530 passed, 1 skipped).

```bash
git add src/crud_views/lib/assets.py src/crud_views/templatetags/crud_views.py tests/test1/test_assets.py
git commit -m "feat(assets): Asset dataclass with SRI metadata, str|Asset registry entries"
```

---

### Task 2: `CRUD_VIEWS_CSP_NONCE_ATTR` setting + nonce resolution helper

**Files:**
- Modify: `src/crud_views/lib/settings.py` (one field)
- Modify: `src/crud_views/templatetags/crud_views.py` (helper)
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Consumes: `crud_views_settings` singleton.
- Produces: `crud_views_settings.csp_nonce_attr: str` (default `"csp_nonce"`); `_resolve_nonce(context) -> str | None` importable as `from crud_views.templatetags.crud_views import _resolve_nonce`. `context` needs only `.get(key)` (dict works in tests).

- [ ] **Step 1: Write the failing tests** — append to `tests/test1/test_assets.py`:

```python
class _FakeLazyNonce:
    """Mimics Django 6 LazyNonce: falsy until first evaluated via str()."""

    def __init__(self, value="lazy123"):
        self.value = value
        self.evaluated = False

    def __bool__(self):
        return self.evaluated

    def __str__(self):
        self.evaluated = True
        return self.value


def _request(**attrs):
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    for name, value in attrs.items():
        setattr(request, name, value)
    return request


def test_resolve_nonce_absent():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({}) is None
    assert _resolve_nonce({"request": _request()}) is None


def test_resolve_nonce_request_attr_django_csp_convention():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({"request": _request(csp_nonce="abc123")}) == "abc123"


def test_resolve_nonce_forces_lazy_evaluation():
    # Django 6 LazyNonce is falsy until evaluated — truthiness checks would drop it.
    from crud_views.templatetags.crud_views import _resolve_nonce

    lazy = _FakeLazyNonce()
    assert _resolve_nonce({"request": _request(csp_nonce=lazy)}) == "lazy123"
    assert lazy.evaluated is True


def test_resolve_nonce_context_var_fallback():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({"csp_nonce": _FakeLazyNonce("ctx456")}) == "ctx456"


def test_resolve_nonce_request_attr_beats_context_var():
    from crud_views.templatetags.crud_views import _resolve_nonce

    context = {"request": _request(csp_nonce="fromrequest"), "csp_nonce": "fromcontext"}
    assert _resolve_nonce(context) == "fromrequest"


def test_resolve_nonce_configurable_attr(settings):
    from crud_views.lib.settings import crud_views_settings
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert crud_views_settings.csp_nonce_attr == "csp_nonce"
    original = crud_views_settings.csp_nonce_attr
    crud_views_settings.csp_nonce_attr = "my_nonce"
    try:
        assert _resolve_nonce({"request": _request(my_nonce="custom789")}) == "custom789"
    finally:
        crud_views_settings.csp_nonce_attr = original
```

Note: if the `settings` fixture (pytest-django) is unavailable in this suite, drop the parameter — the test mutates the pydantic singleton directly and restores it in `finally`. If pydantic rejects attribute assignment (`ValidationError`/frozen model), use `object.__setattr__(crud_views_settings, "csp_nonce_attr", "my_nonce")` and restore the same way.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_assets.py -v -k "resolve_nonce"`
Expected: FAIL with `ImportError: cannot import name '_resolve_nonce'`

- [ ] **Step 3: Implement.** In `src/crud_views/lib/settings.py`, after the `# session` block (`session_data_key` field), add:

```python
    # csp
    csp_nonce_attr: str = from_settings("CRUD_VIEWS_CSP_NONCE_ATTR", default="csp_nonce")
```

In `src/crud_views/templatetags/crud_views.py`, below the `_querystring_impl` line, add:

```python
def _resolve_nonce(context) -> "str | None":
    """CSP nonce auto-detect: request attribute (django-csp convention), Django 6's
    built-in middleware, then a csp_nonce context variable. Checks existence and
    force-evaluates via str() — Django 6's LazyNonce is falsy until first evaluated."""
    request = context.get("request")
    if request is not None:
        nonce = getattr(request, crud_views_settings.csp_nonce_attr, None)
        if nonce is None:
            try:
                from django.middleware.csp import get_nonce  # Django >= 6.0 only
            except ImportError:
                pass
            else:
                nonce = get_nonce(request)
        if nonce is not None:
            return str(nonce) or None
    nonce = context.get("csp_nonce")
    if nonce is not None:
        return str(nonce) or None
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_assets.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/settings.py src/crud_views/templatetags/crud_views.py tests/test1/test_assets.py
git commit -m "feat(assets): CSP nonce auto-detection helper + CRUD_VIEWS_CSP_NONCE_ATTR setting"
```

---

### Task 3: Render nonce + SRI attributes in `cv_js` / `cv_css`

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py`
- Modify: `src/crud_views/templates/crud_views/shared/js.html`
- Modify: `src/crud_views/templates/crud_views/shared/css.html`
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Consumes: `Asset`, `normalize_entries`, `_resolve_nonce` from Tasks 1–2.
- Produces: tag context `{"js"|"css": [{"url", "integrity", "crossorigin"}], "nonce": str | None}`; templates render the attributes conditionally.

- [ ] **Step 1: Write the failing tests** — append to `tests/test1/test_assets.py` (the module-level `_render` helper already exists; add a context-aware variant next to it):

```python
def _render_ctx(tag: str, ctx: dict) -> str:
    return Template("{% load crud_views %}{% " + tag + " %}").render(Context(ctx))


def test_no_nonce_output_byte_identical(asset_registry):
    # Hard guarantee: without a nonce source, output is exactly the pre-CSP format.
    html = _render("cv_js")
    assert "nonce" not in html
    assert "integrity" not in html
    assert "crossorigin" not in html
    assert '<script type="application/javascript" src="/static/crud_views/js/viewset.js"></script>' in html


def test_nonce_rendered_on_all_script_tags(asset_registry):
    html = _render_ctx("cv_js", {"request": _request(csp_nonce="abc123")})
    assert html.count('nonce="abc123"') == 5  # all 5 core scripts


def test_nonce_rendered_on_link_tags(asset_registry):
    html = _render_ctx("cv_css", {"request": _request(csp_nonce="abc123")})
    assert html.count('nonce="abc123"') == 3  # property.css, table.css, formset.css


def test_sri_attributes_rendered(asset_registry):
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(
        key="cdn",
        js=[Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc")],
        css=[Asset(path="https://cdn.example.com/x.css", integrity="sha384-def", crossorigin="use-credentials")],
    )
    js = _render_ctx("cv_js", {})
    assert 'src="https://cdn.example.com/x.js" integrity="sha384-abc" crossorigin="anonymous"' in js
    css = _render_ctx("cv_css", {})
    assert 'integrity="sha384-def" crossorigin="use-credentials"' in css


def test_crossorigin_without_integrity(asset_registry):
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(key="cdn", js=[Asset(path="https://cdn.example.com/x.js", crossorigin="anonymous")])
    html = _render_ctx("cv_js", {})
    assert 'src="https://cdn.example.com/x.js" crossorigin="anonymous"' in html
    assert "integrity" not in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_assets.py -v -k "nonce_rendered or sri or byte_identical or crossorigin_without"`
Expected: byte-identical test PASSES already; the others FAIL (no nonce/integrity in output).

- [ ] **Step 3: Implement.** In `src/crud_views/templatetags/crud_views.py`, add below `_resolve_nonce`:

```python
def _asset_items(entries) -> list:
    items = []
    for asset in entries:
        crossorigin = asset.crossorigin
        if asset.integrity and crossorigin is None:
            crossorigin = "anonymous"  # required for cross-origin SRI fetches
        items.append({"url": assets.resolve_url(asset.path), "integrity": asset.integrity, "crossorigin": crossorigin})
    return items
```

Rewrite the two tags to use it and pass the nonce:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = list(assets.normalize_entries(crud_views_settings.css.values()))
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.css)
    return {"css": _asset_items(entries), "nonce": _resolve_nonce(context)}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = list(assets.normalize_entries(crud_views_settings.javascript().values()))
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.js)
    return {"js": _asset_items(entries), "nonce": _resolve_nonce(context)}
```

Replace `src/crud_views/templates/crud_views/shared/js.html` entirely with (single line inside the loop; attribute order src → nonce → integrity → crossorigin):

```html
{% for item in js %}
    <script type="application/javascript" src="{{ item.url }}"{% if nonce %} nonce="{{ nonce }}"{% endif %}{% if item.integrity %} integrity="{{ item.integrity }}"{% endif %}{% if item.crossorigin %} crossorigin="{{ item.crossorigin }}"{% endif %}></script>
{% endfor %}
```

Replace `src/crud_views/templates/crud_views/shared/css.html` entirely with:

```html
{% for item in css %}
    <link rel="stylesheet" href="{{ item.url }}"{% if nonce %} nonce="{{ nonce }}"{% endif %}{% if item.integrity %} integrity="{{ item.integrity }}"{% endif %}{% if item.crossorigin %} crossorigin="{{ item.crossorigin }}"{% endif %}>
{% endfor %}
```

(`nonce` here is already a plain `str` or `None` — `_resolve_nonce` did the `str()` forcing; `{% if %}` on a plain string is safe.)

- [ ] **Step 4: Run the asset tests, then the full suite**

Run: `cd tests && pytest test1/test_assets.py -v` → Expected: ALL PASS
Run: `cd tests && pytest` → Expected: all pass (~535+ passed, 1 skipped)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/shared/js.html src/crud_views/templates/crud_views/shared/css.html tests/test1/test_assets.py
git commit -m "feat(assets): render CSP nonce and SRI attributes in cv_js/cv_css"
```

---

### Task 4: System checks E330 (malformed integrity) + W331 (SRI on same-origin path)

**Files:**
- Modify: `src/crud_views/checks.py`
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Consumes: `assets.get_registered()`, `assets.is_external()`, `Asset` from Task 1.
- Produces: `check_asset_registry(app_configs=None, **kwargs) -> list` registered under the existing `TAG = "crud_views"`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test1/test_assets.py`:

```python
def test_check_asset_registry_ok(asset_registry):
    from crud_views.checks import check_asset_registry
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(
        key="cdn",
        js=["plain/local.js", Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc")],
    )
    assert check_asset_registry() == []


def test_check_asset_registry_e330_malformed_integrity(asset_registry):
    from crud_views.checks import check_asset_registry
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(key="cdn", js=[Asset(path="https://cdn.example.com/x.js", integrity="md5-abc")])
    messages = check_asset_registry()
    assert [m.id for m in messages] == ["crud_views.E330"]
    assert "cdn" in messages[0].msg and "https://cdn.example.com/x.js" in messages[0].msg


def test_check_asset_registry_w331_integrity_on_local_path(asset_registry):
    from crud_views.checks import check_asset_registry
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(key="picker", css=[Asset(path="picker/plugin.css", integrity="sha384-abc")])
    messages = check_asset_registry()
    assert [m.id for m in messages] == ["crud_views.W331"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_assets.py -v -k "check_asset_registry"`
Expected: FAIL with `ImportError: cannot import name 'check_asset_registry'`

- [ ] **Step 3: Implement** — in `src/crud_views/checks.py`, add `from crud_views.lib import assets` to the imports, then append at module end:

```python
_INTEGRITY_PREFIXES = ("sha256-", "sha384-", "sha512-")


@register(TAG)
def check_asset_registry(app_configs=None, **kwargs):
    """Validate SRI metadata on registered asset bundles."""
    messages = []
    for bundle in assets.get_registered():
        for asset in bundle.js + bundle.css:
            if asset.integrity is None:
                continue
            if not asset.integrity.startswith(_INTEGRITY_PREFIXES):
                messages.append(
                    Error(
                        f"Asset {asset.path!r} in bundle {bundle.key!r} has an invalid integrity value "
                        f"{asset.integrity!r}.",
                        hint="Use a sha256-/sha384-/sha512- prefixed hash, e.g. from: "
                        "openssl dgst -sha384 -binary FILE | openssl base64 -A",
                        id="crud_views.E330",
                    )
                )
            if not assets.is_external(asset.path):
                messages.append(
                    DjangoWarning(
                        f"Asset {asset.path!r} in bundle {bundle.key!r} sets integrity on a same-origin static path.",
                        hint="SRI is meant for external URLs; on own static files it breaks on every asset "
                        "edit and adds no security value. Remove the integrity attribute.",
                        id="crud_views.W331",
                    )
                )
    return messages
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_assets.py -v` → Expected: ALL PASS
Run: `cd tests && pytest` → Expected: all pass (system checks run during test setup — ensure nothing new fires on the clean registry)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/checks.py tests/test1/test_assets.py
git commit -m "feat(checks): E330/W331 validate SRI metadata on asset bundles"
```

---

### Task 5: Django 6 built-in CSP end-to-end test (version-gated)

**Files:**
- Test: `tests/test1/test_assets.py`

**Interfaces:**
- Consumes: everything from Tasks 1–3; Django 6's `ContentSecurityPolicyMiddleware`, `CSP` enum.
- Produces: regression coverage for the `LazyNonce` round-trip (tag nonce == header nonce) on the Django 6.0 matrix rows.

- [ ] **Step 1: Write the test** — append to `tests/test1/test_assets.py` (add `import re` and `import django` to the file's imports):

```python
@pytest.mark.skipif(django.VERSION < (6, 0), reason="built-in CSP middleware requires Django 6.0")
def test_django6_builtin_csp_nonce_roundtrip(asset_registry):
    from django.http import HttpResponse
    from django.middleware.csp import ContentSecurityPolicyMiddleware
    from django.test import RequestFactory, override_settings
    from django.utils.csp import CSP

    rendered = {}

    def get_response(request):
        html = _render_ctx("cv_js", {"request": request})
        rendered["html"] = html
        return HttpResponse(html)

    with override_settings(SECURE_CSP={"script-src": [CSP.SELF, CSP.NONCE]}):
        middleware = ContentSecurityPolicyMiddleware(get_response)
        response = middleware(RequestFactory().get("/"))

    match = re.search(r'nonce="([^"]+)"', rendered["html"])
    assert match, rendered["html"]
    nonce = match.group(1)
    assert rendered["html"].count(f'nonce="{nonce}"') == 5  # same nonce on all 5 core scripts
    assert f"'nonce-{nonce}'" in response["Content-Security-Policy"]
```

Why this shape: the middleware sets private `request._csp_nonce`; our resolver finds it via `django.middleware.csp.get_nonce`, `str()` forces `LazyNonce` generation, and `process_response` then substitutes the `CSP.NONCE` sentinel in the header — asserting header == tag nonce proves the full loop.

- [ ] **Step 2: Run it**

Run: `cd tests && pytest test1/test_assets.py -v -k "django6"`
Expected locally (Django 5.2.14): `SKIPPED (built-in CSP middleware requires Django 6.0)`. If a Django 6 nox env exists, optionally verify for real: `nox -s "tests-3.13(django='6.0')" -- test1/test_assets.py -k django6` (check `noxfile.py` for exact session naming before running; skip this if session names differ — CI covers it).

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_assets.py
git commit -m "test(assets): Django 6 built-in CSP nonce round-trip (version-gated)"
```

---

### Task 6: Documentation + changelog

**Files:**
- Modify: `docs/reference/settings.md`
- Modify: `CHANGELOG.md`

**Interfaces:** none (docs only). Facts to document come from Tasks 1–5; do not invent new APIs.

- [ ] **Step 1: Update the CSP section** in `docs/reference/settings.md`. Replace the paragraph at lines 61–63 (starting `django-crud-views is compatible with strict Content Security Policy headers.`) with:

```markdown
django-crud-views is compatible with strict Content Security Policy headers. The package does not use inline scripts, inline event handlers, inline styles, or `javascript:` URIs.

Projects can enforce a CSP without `unsafe-inline` for both `script-src` and `style-src` directives. For nonce-based strict CSP (`'strict-dynamic'`), the asset tags emit nonces automatically — see [Nonce support](#nonce-support).
```

Replace the line `No nonces or hashes are required.` (end of the "JavaScript architecture" subsection, line 94) with:

```markdown
For host-allowlist policies (`script-src 'self'`) no nonces or hashes are required. Nonce-based policies are supported automatically — see below.

### Nonce support

Under a strict CSP (`script-src 'nonce-…' 'strict-dynamic'`), browsers ignore host allowlists, so every `<script>` tag needs a `nonce` attribute. `{% cv_js %}` and `{% cv_css %}` detect the request's CSP nonce automatically and render it on every tag — no configuration needed:

- **Django 6.0+ built-in CSP**: enable `django.middleware.csp.ContentSecurityPolicyMiddleware` and include the `CSP.NONCE` sentinel in `SECURE_CSP`. The tags use `django.middleware.csp.get_nonce()`.
- **Django 4.2/5.2 with [django-csp](https://django-csp.readthedocs.io/)**: the tags read the `request.csp_nonce` attribute set by `CSPMiddleware`.
- **Custom setups**: store the nonce on the request under the attribute named by `CRUD_VIEWS_CSP_NONCE_ATTR` (default `csp_nonce`), or expose it as a `csp_nonce` template context variable.

Without CSP middleware the output is unchanged — no nonce attributes are rendered. The tags need the `django.template.context_processors.request` context processor (part of Django's default template configuration).

| Key                        | Description                                                        | Type  | Default     |
|----------------------------|--------------------------------------------------------------------|-------|-------------|
| CRUD_VIEWS_CSP_NONCE_ATTR  | Request attribute the asset tags read the CSP nonce from           | `str` | `csp_nonce` |

### Subresource integrity (SRI)

Asset bundles registered via `register_assets()` accept `Asset` instances alongside plain path strings, carrying `integrity` and `crossorigin` attributes for external URLs:

```python
from crud_views.lib.assets import Asset, register_assets

register_assets(
    key="my_widget",
    js=[
        "my_widget/widget.js",  # own static file — no SRI needed
        Asset(
            path="https://cdn.example.com/lib.min.js",
            integrity="sha384-…",  # crossorigin="anonymous" is added automatically
        ),
    ],
)
```

System checks validate SRI metadata at startup: `crud_views.E330` rejects integrity values without a `sha256-`/`sha384-`/`sha512-` prefix, and `crud_views.W331` warns when integrity is set on a same-origin static path (SRI there breaks on every asset edit and adds no security value).
```

- [ ] **Step 2: Changelog.** In `CHANGELOG.md`, if there is no `## Unreleased` section under the top `# Changelog` heading, add one above `## 0.17.0`:

```markdown
## Unreleased

### Added

- Asset registry CSP support: `{% cv_js %}` / `{% cv_css %}` auto-detect the CSP nonce (django-csp's `request.csp_nonce` on Django 4.2/5.2 and the built-in CSP middleware on Django 6.0) and render `nonce` attributes on all script/link tags. New setting `CRUD_VIEWS_CSP_NONCE_ATTR` (default `csp_nonce`). Output is unchanged when no CSP middleware is present.
- `Asset` dataclass for `register_assets()` entries with SRI `integrity`/`crossorigin` metadata for external URLs; new system checks `crud_views.E330` (malformed integrity) and `crud_views.W331` (integrity on same-origin path).
```

- [ ] **Step 3: Verify docs build and lint**

Run: `.venv/bin/mkdocs build --strict 2>&1 | tail -5` (from repo root; if mkdocs isn't in `.venv`, use `task docs` briefly or skip — CI builds docs)
Expected: no errors/warnings about settings.md.
Run: `task check && task format` (or `.venv/bin/ruff check --fix . && .venv/bin/ruff format .`)
Expected: clean.

- [ ] **Step 4: Final full test run + commit**

Run: `cd tests && pytest`
Expected: all pass.

```bash
git add docs/reference/settings.md CHANGELOG.md
git commit -m "docs: CSP nonce auto-detection and SRI usage for the asset registry"
```

---

## Completion

After all tasks: follow the project PR lifecycle — create a feature branch retroactively if work happened on `main` (it should NOT — branch as `feature/asset-registry-csp` before Task 1), push, open a PR, wait for CI, fix ruff findings if any, squash-merge to `main`, wait for main CI. Follow-up (not in this plan): update the plugin SKILL.md in the skills monorepo (`~/projects/alex/skills`) after the next release.
