# Asset registry ↔ django-pipeline integration — design

Date: 2026-10-08
Status: draft, awaiting review
Builds on: `2026-07-14-asset-registry-and-extensions-design.md` (§1.4 "Pipeline posture"),
`2026-07-21-asset-registry-csp-design.md`

## Goal

Projects that deliver static files through **django-pipeline** (with compressors) must be able to
put every *local* crud-views asset — core and every registered extension bundle — into their
pipeline packages **without hand-maintaining `source_filenames` lists**, and without assets being
loaded twice.

### What the user said

- Consuming projects use django-pipeline together with compressors.
- The main pain is **hand-maintained lists**: `PIPELINE[...]["source_filenames"]` is assembled
  manually per extension (from each extension's `source_files()`) and must be kept in sync with
  `INSTALLED_APPS` by hand.
- Chosen approach: **lazy registry source list + all-or-nothing bundled mode** (approach A).
- The django-crud-views skill in the sibling `../skills` repo must be updated as part of this work.

### Assumptions

- Core keeps **no runtime dependency on django-pipeline** (no import, no extra) — unchanged from
  the July spec. django-pipeline becomes a test-only dependency.
- External (CDN) entries cannot be bundled and keep rendering through `{% cv_js %}`/`{% cv_css %}`.
- jQuery stays outside the registry; projects put it in front via `before=`.

### Success criteria

- A project adds `cv_sources(...)` to its `PIPELINE` packages plus `CRUD_VIEWS_ASSETS_BUNDLED =
  True` and gets every local crud-views asset bundled in registry order; adding or removing an
  extension app needs no settings change.
- With bundled mode on, no local crud-views asset is emitted by the tags; CDN entries still are.
- Misconfiguration (gaps, double-loading, typos, eager expansion) is reported at startup, not in
  the browser.
- With `CRUD_VIEWS_ASSETS_BUNDLED = False` (default), tag output is byte-identical to today.

## Key finding (verified against django-pipeline 4.1.0)

- `pipeline.conf.PipelineSettings.__init__` does `self.settings.update(wrapped_settings)` — a
  **shallow** copy. The package dicts and the `source_filenames` objects are kept by reference.
- `pipeline.packager.Package.sources` iterates `config.get("source_filenames", [])` **lazily**, on
  first access (first `{% javascript %}`/`{% stylesheet %}` render or `collectstatic`) — long after
  `AppConfig.ready()`.
- Therefore a lazy `Sequence` placed in `source_filenames` can resolve from the registry at that
  point. This removes the settings-time vs. `ready()`-time chicken-and-egg without patching pipeline.
- `Package.sources` keeps a path only if `find(path)` succeeds — **external URLs are silently
  dropped**. `cv_sources()` therefore excludes them explicitly.

## Section 1 — One ordered asset list; bundled mode

### Core assets join the registry ordering

- Settings stay the source of truth for core files: `crud_views_settings.javascript()` and
  `crud_views_settings.css` are unchanged (still exposed via `as_dict` / context processor).
- New in `crud_views/lib/assets.py`:
  - `CORE_KEY = "crud_views"`.
  - `iter_bundles() -> list[AssetBundle]`: a synthesized core `AssetBundle(key="crud_views", ...)`
    built from the settings above, **first**, followed by registered bundles in registration
    order. Core comes first even when an extension app precedes `crud_views` in `INSTALLED_APPS`
    (registering core in `ready()` could not guarantee that).
  - `collect(kind: Literal["js", "css"], *, only_emitting: bool = False) -> list[Asset]`: the
    ordered entries of `kind` across `iter_bundles()`. The core bundle always counts as emitting.
- `register_assets(key="crud_views", ...)` raises `ImproperlyConfigured` (reserved key).
- `get_registered()` keeps its current behaviour (registered bundles only, no core) for backwards
  compatibility.

### Rendering

`cv_js` / `cv_css` build their entries from `assets.collect(kind, only_emitting=True)`.

New setting on `CrudViewsSettings`:

```python
assets_bundled: bool = from_settings("CRUD_VIEWS_ASSETS_BUNDLED", default=False)
```

- `False`: identical output to today — core first, then emitting bundles.
- `True`: the tags render **only external entries** (`assets.is_external(asset.path)`), with SRI
  and nonce handling unchanged. Every local static path — core's included — is assumed to be
  delivered by the bundler. The tags therefore remain in the base template.

### `emit=False` under the new model

- `emit=False` bundles stay excluded from tag output in both modes.
- `cv_sources()` **includes** `emit=False` bundles: `emit=False` already meant "a bundler delivers
  this". Existing manual setups keep working; projects switching to `cv_sources()` need not touch
  their extensions' `EMIT` settings.

### Unchanged

`register_assets()` signature, `Asset`/SRI semantics, nonce resolution, `shared/js.html`,
`shared/css.html`.

## Section 2 — `cv_sources()`

### Location and import safety

`crud_views/lib/pipeline.py`. Module-level imports are **stdlib only**; `crud_views.lib.assets` and
`django.apps` are imported lazily inside resolution. `crud_views/__init__.py` and
`crud_views/lib/__init__.py` import nothing, so `from crud_views.lib.pipeline import cv_sources` is
safe in `settings.py`. The module never imports django-pipeline.

### API

```python
def cv_sources(
    kind: Literal["js", "css"],
    *,
    before: Iterable[str] = (),
    after: Iterable[str] = (),
    keys: Iterable[str] | None = None,
    exclude: Iterable[str] = (),
) -> LazySources
```

- `kind` other than `"js"`/`"css"` → `ValueError` immediately (settings time).
- `keys`: only these bundle keys (`"crud_views"` = core). `None` = all.
- `exclude`: drop these bundle keys. Applied after `keys`.
- `before` / `after`: plain static paths (or pipeline glob patterns) placed around the registry
  entries, e.g. jQuery before, project `app.js` after.

### `LazySources`

A `collections.abc.Sequence`; resolves on every `__iter__` / `__len__` / `__getitem__`:

1. `assets.collect(kind)` (all bundles, including `emit=False`).
2. Filter by `keys` / `exclude`.
3. Drop external entries.
4. Map `Asset` → `.path`.
5. `before` + registry paths + `after`, de-duplicated preserving the first occurrence.

No caching: pipeline caches `Package._sources` itself; resolution is cheap.

Additional behaviour:

- **Eager-expansion guard.** Resolving while `django.apps.apps.ready` is `False` raises
  `django.core.exceptions.AppRegistryNotReady` with the message: *"cv_sources() was resolved
  before the app registry is ready — most likely it was expanded in settings.py (e.g.
  `[*cv_sources('js')]` or `list(cv_sources('js'))`). Pass extra files via before=/after= or
  combine with `+` instead."* A broken settings file fails loudly at startup instead of producing an
  empty bundle.
- `__add__` / `__radd__` with a `list` or `tuple` return a new `LazySources` (the operand merged
  into `after` / `before` respectively), so `["js/jquery.js"] + cv_sources("js")` stays lazy.
  Adding two `LazySources` is not supported (`NotImplemented`). Docs lead with `before=`/`after=`.
- `__repr__`: `<LazySources kind='js' keys=None exclude=() before=1 after=0>` — never resolves.
- Introspection attributes for the system checks: `kind`, `keys`, `exclude` (read-only).

### Splitting across packages

Allowed by calling `cv_sources()` more than once, e.g. `exclude=["datetimepicker"]` in `"main"`
and `keys=["datetimepicker"]` in `"forms"`. "All-or-nothing" refers to tag output only; coverage
of the split is verified by W341.

### Example (documented)

```python
# settings.py
from crud_views.lib.pipeline import cv_sources

CRUD_VIEWS_ASSETS_BUNDLED = True

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

## Section 3 — System checks

New IDs in the free **`crud_views.W34x`** range (E330/W330–W332 are taken). All are warnings,
registered next to `check_asset_registry` in `crud_views/checks.py` under the same tag. They read
`getattr(settings, "PIPELINE", {})` as plain data — no pipeline import — and walk
`JAVASCRIPT` / `STYLESHEETS` → package → `source_filenames`.

**Coverage model.** Per kind, the covered set is the union over all packages of that kind of:
resolved `LazySources` paths, plus plain string entries interpreted as pipeline glob patterns
(matched with `fnmatch`). Counting plain strings gives hand-maintained setups the same safety net.

| ID | Condition | Message gist |
|---|---|---|
| W340 | `ASSETS_BUNDLED=True` and no `LazySources` anywhere in `PIPELINE` (or no `PIPELINE`) | Bundled mode is on but no pipeline package draws from the registry — local crud-views assets are delivered by nothing. Reported once. |
| W341 | `ASSETS_BUNDLED=True`, a local registry asset of kind X is not covered by any package of kind X | Names asset path + bundle key. Suppressed while W340 fires. |
| W342 | `ASSETS_BUNDLED=False` and a `LazySources` resolves assets from **emitting** bundles (core counts as emitting) | Double load: bundled *and* emitted by the tags. Hint: set `CRUD_VIEWS_ASSETS_BUNDLED = True`. |
| W343 | A `LazySources` names an unregistered key in `keys=` / `exclude=` | Typo or removed extension; hint lists known keys. |
| W344 | A `LazySources` of kind `css` sits under `JAVASCRIPT`, or vice versa | Kind mismatch pipeline would concatenate silently. |

Out of scope (YAGNI): the same asset in two packages (legitimate for per-page packages); ordering
checks against jQuery; file-existence checks (pipeline's `find()`, `collectstatic`, and W330/W331
already cover these).

## Section 4 — Tests, docs, skill, rollout

### Dependencies

- Add `django-pipeline` to the `test` extra only (not `dev`, no `[pipeline]` extra).
- **Risk to verify first:** django-pipeline 4.1 compatibility with Django 6.0 in the nox matrix.
  If incompatible, pipeline-dependent tests use `pytest.importorskip("pipeline")` plus a version
  skip; everything else does not need pipeline.

### Unit tests — `tests/test1/test_assets_pipeline.py` (no pipeline required)

- `iter_bundles()`: core first even if an extension registered earlier; reserved key raises.
- `collect()`: ordering equals the tags' pre-change ordering (regression guard).
- `cv_js` / `cv_css`: with `ASSETS_BUNDLED=True` only external entries render, SRI + nonce intact;
  with `False` output is byte-identical to before.
- `LazySources`: lazy resolution; `before`/`after` order; de-dup; `keys`/`exclude`; externals
  dropped; `emit=False` bundles included; `+`/`radd` stays lazy and rejects `LazySources + LazySources`;
  `repr` does not resolve; invalid `kind` raises `ValueError`.
- Eager-expansion guard: with `apps.ready` patched to `False`, resolution raises
  `AppRegistryNotReady` carrying the hint.
- Settings-time import safety: subprocess `python -c "import crud_views.lib.pipeline"` **without**
  `DJANGO_SETTINGS_MODULE` succeeds.
- Checks W340–W344: one positive and one negative case each via `override_settings(PIPELINE=...)`,
  including plain-string glob coverage and W341 suppression under W340.

Registry state: tests that register bundles snapshot and restore `assets._REGISTRY` (existing
pattern in `tests/test1/test_assets.py`).

### Integration test (real pipeline)

- `override_settings(PIPELINE={...cv_sources...}, STATIC_ROOT=tmp_path)`; pipeline's
  `setting_changed` receiver reloads its settings.
- `Packager().pack_javascripts()` / `pack_stylesheets()` with
  `pipeline.compressors.NoopCompressor`: output contains core files, then a registered test bundle,
  in order, wrapped by `before`/`after`; a CDN entry is absent.
- `Package.sources` equals what `cv_sources` resolves — proves laziness survives pipeline's real
  shallow copy.

### Docs

- `docs/reference/assets.md`: new section **"Bundling with django-pipeline"** — full settings
  example (jQuery via `before=`), the eager-expansion trap, `keys`/`exclude` splitting, CDN entries
  stay in the tags, re-minifying already-minified vendor files is harmless, W340–W344 table.
  Reword the existing `emit=False` bullet to point to the new section.
- `docs/reference/settings.md`: `CRUD_VIEWS_ASSETS_BUNDLED`.
- `CHANGELOG.md`: **Added** — `cv_sources()` lazy pipeline sources, `CRUD_VIEWS_ASSETS_BUNDLED`,
  checks W340–W344. **Changed** — core assets are part of the registry ordering (`iter_bundles()` /
  `collect()`); `"crud_views"` is a reserved bundle key.

### Skill update (`../skills`, in scope)

Repo `jacob-consulting/skills`, working copy `/home/alex/projects/alex/skills`, files under
`plugins/django-crud-views/`. Done **after** the package release carrying this feature, so the
`Available since X.Y.Z` markers name a real version.

- `skills/django-crud-views/SKILL.md`, section "Static assets, CSP, and SRI": new subsection
  "Bundling with django-pipeline" — the settings example, `CRUD_VIEWS_ASSETS_BUNDLED`, the
  eager-expansion trap, CDN entries stay in the tags. Add a Common Mistakes row for
  `[*cv_sources(...)]` / `list(cv_sources(...))` in settings.py.
- Frontmatter `description`: mention bundling registered assets with django-pipeline so the skill
  triggers on pipeline questions.
- `skills/django-crud-views/references/api-reference.md`: `cv_sources` / `LazySources` signature
  table under the asset registry section; `iter_bundles`, `collect`, `CORE_KEY`; the
  `CRUD_VIEWS_ASSETS_BUNDLED` setting under "Asset registry / CSP settings"; W340–W344 in the
  checks listing.
- Plugin `CHANGELOG.md` entry under `[Unreleased]`, then a plugin release via
  `scripts/release.sh django-crud-views X.Y.Z` (plugin version independent of package version).
- Verify with the executable drift-audit harness (imports resolve, `__all__` names covered,
  `CRUD_VIEWS_*` strings map to real settings fields), not by reading.
- All skills-repo git operations via `git -C /home/alex/projects/alex/skills ...` in one
  invocation; verify `HEAD == origin/main` and the tag on the remote afterwards.

### Follow-ups (out of scope)

- Extensions repo: datetimepicker docs replace the manual `source_files()` pipeline recipe with
  `cv_sources(keys=["datetimepicker"])`; `source_files()` stays (vendoring uses it).
- Bootstrap5 example app pipeline mode — not now.
- Option B from brainstorming (`{% cv_js %}` rendering the pipeline package itself, nonce-aware) —
  can be layered on later without breaking this design.

## Alternatives rejected

- **Per-bundle bundled mode** (inferred from which keys `cv_sources()` is asked for) — more
  implicit coupling between settings and tag output; all-or-nothing plus W341 covers splitting.
- **`{% cv_js %}` renders pipeline packages (option B)** — needs an optional runtime pipeline
  import in core; deferred.
- **Generated source list + drift check (option C)** — still a file to regenerate on every app
  change, which is the hand-maintenance being removed.
- **Registering core assets in `CrudViewsConfig.ready()`** — ordering would depend on
  `INSTALLED_APPS` position; synthesizing the core bundle in `iter_bundles()` guarantees core first.
