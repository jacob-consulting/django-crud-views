# Integrate django-object-detail as the optional `crud_views_object_detail` extension

**Status:** Approved (brainstorming) — ready for implementation plan
**Date:** 2026-07-17
**Prompt:** `superpowers/prompts/2026-07-17-object-detail-per-view.md`

## Summary

`django-object-detail` is a separate, alpha-stage PyPI package (0.1.9 released; 0.2.0
tagged locally but never published) that was built specifically for `django-crud-views`.
Today it is a **mandatory core dependency**: `crud_views.lib.views.detail.DetailView`
imports it directly and layers `ObjectDetailMixin` on top of `DetailCustomView`, with a
thin adapter (`property_display` → `cv_property_display`, checks E240–E245) and
partially-cloned docs.

This design **absorbs the package into the crud_views distribution as an optional
extension app**, `crud_views_object_detail`, alongside `crud_views_workflow`,
`crud_views_polymorphic`, and `crud_views_guardian`. Crucially, this **inverts** the
dependency: core `crud_views` *drops* object-detail entirely and its `DetailView` becomes
the simple template-driven view; the rich, property-display-powered view moves out to the
new opt-in extension.

## Motivation / judgement

Integrating is the right call given the specifics:

- object-detail is alpha, single-consumer, unreleased-at-HEAD, and untouched since its
  last release — essentially no independent user base to protect.
- The two are already tightly coupled (direct import, adapter shim, cloned docs).
- object-detail has **no models** → vendoring carries no data-layer/migration risk.
- Pre-1.0 is the correct moment to make the disruptive structural change, and all
  downstream projects are maintained by a single team (technical-lead owned), so the
  import churn is acceptable.

The one real cost — losing standalone reuse of `ObjectDetailMixin` with plain Django
`DetailView` — is theoretical at current adoption. Making the feature an **opt-in
extension** (rather than a new *mandatory* app) means core actually gets **lighter**, and
object-detail joins a mental model the package already has.

## Decisions (locked during brainstorming)

1. **App structure:** separate optional extension `crud_views_object_detail`; core drops
   the object-detail dependency.
2. **Naming:** adopt crud_views idioms — app/template-dir/tag-lib renamed to
   `crud_views_object_detail`; settings become `CRUD_VIEWS_OBJECT_DETAIL_*` via a pydantic
   settings model.
3. **View naming:** core `DetailView` = simple template-driven (absorbs today's
   `DetailCustomView`); extension provides distinctly-named `ObjectDetailView` /
   `ObjectDetailViewPermissionRequired`.
4. **`DetailCustomView`:** removed outright (pre-1.0); call sites migrated to `DetailView`.
5. **Extension ripple:** polymorphic/guardian detail views extend the *simple* core
   `DetailView`; property-display is composed in by the user when wanted (Guardian's
   existing mixin-composition style).
6. **Public API:** `crud_views_object_detail.lib` (lazy PEP 562 `__getattr__`).
7. **Sibling repo:** edit `../django-object-detail/README.md` + commit now; run
   `gh repo archive` only *after* the crud_views release ships.

## Architecture

### New app: `src/crud_views_object_detail/`

Mirrors the `crud_views_workflow` layout.

```
src/crud_views_object_detail/
  __init__.py
  apps.py                       # AppConfig name="crud_views_object_detail", label="cvod"; ready() imports checks
  checks.py                     # E240–E245 cv_property_display checks (moved from core detail.py)
  lib/
    __init__.py                 # lazy PEP 562 __getattr__ public API
    config.py                   # LinkConfig, BadgeConfig, PropertyConfig, PropertyGroupConfig, x, parse_property_display
    resolvers.py                # FIELD_TYPE_MAP, ResolvedProperty, ResolvedGroup, resolve_all, ...
    conf.py                     # CrudViewsObjectDetailSettings (pydantic) reading CRUD_VIEWS_OBJECT_DETAIL_*
    mixins.py                   # ObjectDetailMixin (was django_object_detail/views.py)
    views.py                    # ObjectDetailView, ObjectDetailViewPermissionRequired
  templatetags/
    crud_views_object_detail.py # renamed from object_detail
  templates/crud_views_object_detail/
    object_detail.html
    layouts/{accordion,card-rows,list-group-3col,split-card,striped-rows,table-inline,tabs-vertical}/
      object_detail.html, group.html, property.html
    types/default/
      char.html text.html boolean.html date.html datetime.html timestamp.html
      integer.html float.html foreignkey.html manytomany.html badge.html default.html
```

**No models** → no `models.py`, no `migrations/`.

#### Renames (vendored code → crud_views idioms)

| Aspect | Old (`django_object_detail`) | New (`crud_views_object_detail`) |
|---|---|---|
| Python package | `django_object_detail` | `crud_views_object_detail` |
| App label | `django_object_detail` | `cvod` |
| Template dir | `templates/django_object_detail/` | `templates/crud_views_object_detail/` |
| Template-tag lib | `{% load object_detail %}` | `{% load crud_views_object_detail %}` |
| `select_template` paths | `django_object_detail/...` | `crud_views_object_detail/...` |
| Settings | `OBJECT_DETAIL_*` via `getattr` | `CRUD_VIEWS_OBJECT_DETAIL_*` via pydantic model |

Settings map (all via `CrudViewsObjectDetailSettings`, defaults preserved):

| Old setting | New setting |
|---|---|
| `OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` | `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` |
| `OBJECT_DETAIL_TEMPLATE_PACK_TYPES` | `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES` |
| `OBJECT_DETAIL_ICONS_LIBRARY` | `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY` |
| `OBJECT_DETAIL_ICONS_CLASS` | `CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS` |
| `OBJECT_DETAIL_ICONS_TYPE` | `CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE` |
| `OBJECT_DETAIL_ICONS_PREFIX` | `CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX` |
| `OBJECT_DETAIL_NAMED_ICONS` | `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` |
| `OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE` | `CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE` |

The icon-library defaults tables (`ICON_LIBRARY_DEFAULTS`, `NAMED_ICONS_DEFAULTS`) and the
`build_icon_class` / `build_named_icon_class` helpers move with `conf.py`. The `icon_class`
/ `named_icon_class` template filters keep their names inside the renamed tag lib.

#### Public API (`crud_views_object_detail/lib/__init__.py`)

Lazy PEP 562 `__getattr__` (per the extension `.lib` public-API convention). Exports:

- `ObjectDetailView`, `ObjectDetailViewPermissionRequired` (from `lib.views` — lazy;
  `views.py` imports core `CrudView`)
- `ObjectDetailMixin` (from `lib.mixins`)
- `x`, `PropertyConfig`, `PropertyGroupConfig`, `BadgeConfig`, `LinkConfig` (from
  `lib.config` — import-safe)

`views.py`:

```python
from crud_views.lib.views import DetailView
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views_object_detail.lib.mixins import ObjectDetailMixin

class ObjectDetailView(ObjectDetailMixin, DetailView):
    template_name = "crud_views/view_detail.html"
    cv_content_template = "crud_views_object_detail/view_detail.content.html"
    cv_modal_supported = True
    cv_property_display: list | None = None

    @property
    def property_display(self):
        return self.cv_property_display

class ObjectDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, ObjectDetailView):
    cv_permission = "view"
```

The content template (`crud_views_object_detail/view_detail.content.html`) is the moved
`view_detail.content.html`, updated to `{% load crud_views_object_detail %}`.

### Core `crud_views` changes

- `lib/views/detail.py`: `DetailView` becomes an **exact copy of the current
  `DetailCustomView`** (`CrudView` + Django `generic.DetailView`,
  `template_name = "crud_views/view_detail_custom.html"` with its empty `cv_content`
  block that the dev overrides). **No object-detail import.** The `cv_property_display`
  property and E240–E245 checks are **removed** (they live in the extension now).
  `DetailViewPermissionRequired = CrudViewPermissionRequiredMixin + DetailView`
  (`cv_permission = "view"`), matching the current `DetailCustomViewPermissionRequired`.
- **Delete** `lib/views/detail_custom.py`. Remove `DetailCustomView` /
  `DetailCustomViewPermissionRequired` from `lib/views/__init__.py` and `__all__`.
- Templates:
  - `view_detail_custom.html` (empty `cv_content` shell) stays in core and is the default
    template for core `DetailView`.
  - `view_detail.html` (the `{% include view.cv_content_template %}` shell) stays in core
    and is used by the extension's `ObjectDetailView` (`template_name = "crud_views/view_detail.html"`).
  - `view_detail.content.html` (object-detail specific) **moves** to the extension as
    `crud_views_object_detail/view_detail.content.html`.
- `pyproject.toml`:
  - Remove `django-object-detail (>=0.1.7)` from `[project.dependencies]`.
  - **No optional-dependency group** for object-detail: after vendoring it has no external
    dependencies (only `django` + `pydantic`, already core deps), so an extra would install
    nothing and only mislead. The app ships in the wheel; enabling it is purely an
    `INSTALLED_APPS` step (documented). This is the one intentional divergence from the
    workflow/polymorphic/guardian pattern, where the extra installs a real external dep.
  - Add `src/crud_views_object_detail` to `[tool.hatch.build.targets.wheel].packages`.
- `tests/test1/conftest.py` and `examples/bootstrap5/project/settings.py`: replace
  `"django_object_detail"` with `"crud_views_object_detail"` in `INSTALLED_APPS`.

### Extension ripple

- **crud_views_polymorphic** (`lib/detail.py`): `PolymorphicDetailView` now extends the
  simple core `DetailView` (loses `property_display` by default). Update
  `lib/__init__.py` exports accordingly (names unchanged).
- **crud_views_guardian** (`lib/views.py`):
  - `GuardianDetailViewPermissionRequired` composes `Guardian*Mixin` +
    simple-core `DetailViewPermissionRequired`.
  - **Remove** `GuardianDetailCustomViewPermissionRequired` (redundant now).
  - Rich + guardian is user-composed:
    `class Foo(GuardianObjectPermissionMixin, ObjectDetailViewPermissionRequired)`.
  - `GuardianManageView.get_view_data` mixin-label logic unaffected.

### Docs integration

- Move object-detail docs into crud_views docs under an object-detail area:
  - `getting_started`: `configuration.md`, `links.md`, `badges.md`, `layout_packs.md`
  - `reference`: `field_types.md`, `settings.md` (merge settings into crud_views settings
    reference or a dedicated object-detail settings page)
  - `docs/.../screenshots/*` (7 layout PNGs)
- Rewrite `docs/reference/detail_view.md`: core `DetailView` = template-driven; add
  `object_detail_view.md` for `ObjectDetailView` + `cv_property_display`. Wire `.pages`
  nav (reference + getting_started).
- Update cross-references: `docs/development/stability.md` (remove `DetailCustomView`, add
  extension classes), `docs/reference/modals.md`, `docs/reference/index.md`,
  `docs/reference/guardian.md`, `docs/reference/polymorphic_view.md`.
- Rename doc terminology from "django-object-detail" to the in-tree extension.

### Example app: `examples/bootstrap5/object_detail/`

- Registered app + **nav item** + **"NEW" badge** on the index page (via
  `examples/bootstrap5/project/features.py`, following the existing feature pattern).
- **Two models** (nesting + varied types):
  - `Product`: fields covering `boolean`, `date`, `datetime`, `integer`, `float`/
    `Decimal`, `char`, `text`, `URLField`, plus `@property`/method (e.g. computed status)
    and a **view-computed** value; M2M (e.g. `tags`).
  - `Supplier` (FK from Product) and `Warehouse` (O2O from Product) to demonstrate
    FK-traversal and FK→O2O / reverse-O2O traversal (`supplier__name`,
    `warehouse__address__city`).
- **One `ObjectDetailView` per layout theme** (all 7 packs: accordion, card-rows,
  list-group-3col, split-card, striped-rows, table-inline, tabs-vertical) so every theme
  is browsable from the ViewSet.
- Showcases ported from object-detail's `example/catalog` (evaluated for completeness):
  badges (`color`, `color_map`, `color_fn`, `label_map`, `pill`), property `link`,
  per-type custom `template`, M2M fan-out, method/computed properties, and view-computed
  property. Seed data via a `seed.py`/fixture like the other example apps.
- Smoke test: each theme's detail view returns HTTP 200 and renders its layout markers.

### Sibling repo `../django-object-detail`

- Edit `README.md`: prominent notice that the package is now integrated into
  django-crud-views as `crud_views_object_detail`, with a pointer, and that the repo is
  archived. Commit in that repo.
- **Defer** `gh repo archive jacob-consulting/django-object-detail` until the crud_views
  release that contains the integration has shipped and is green — run on explicit go.
- No PyPI action needed: local `0.2.0` was never published; released `0.1.9` stays as-is.

## Testing

- Port object-detail's test suite (resolvers, config, templatetags, views, conf, icons,
  layout packs) into `tests/` with renamed namespaces (`crud_views_object_detail.*`,
  `CRUD_VIEWS_OBJECT_DETAIL_*`, `{% load crud_views_object_detail %}`).
- `tests/test1/test_detail_view.py`: E240–E245 checks now target `ObjectDetailView`;
  keep coverage of the `cv_property_display` adapter and structural validation.
- Core `DetailView` (simple) gets/keeps its own template-driven test.
- polymorphic/guardian detail tests updated for the simple-base change; add a
  compose-for-rich test (`GuardianObjectPermissionMixin + ObjectDetailViewPermissionRequired`).
- Example smoke tests (per-theme 200).
- Import-safety test extended to cover `crud_views_object_detail.lib` (model-free, but the
  lazy surface must not import view modules eagerly).
- Full matrix green via `task test` (Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0).

## Breaking changes / upgrade notes (deliberate, pre-1.0)

CHANGELOG "Changed"/"Removed" + an upgrade note:

- Rich detail moved to `crud_views_object_detail`. Migrate:
  `DetailView` + `cv_property_display` → `ObjectDetailView`
  (`from crud_views_object_detail.lib import ObjectDetailView`) and add
  `crud_views_object_detail` to `INSTALLED_APPS` (no extra to install — the app ships in
  the wheel).
- `DetailCustomView` → `DetailView` (core `DetailView` is now the template-driven view).
- `GuardianDetailCustomViewPermissionRequired` removed → use
  `GuardianDetailViewPermissionRequired`.
- Polymorphic/guardian detail views no longer render `property_display` by default —
  compose `ObjectDetailView`/`ObjectDetailMixin` where needed.
- Settings renamed `OBJECT_DETAIL_*` → `CRUD_VIEWS_OBJECT_DETAIL_*`.
- Version bump per the project's bump-my-version + publish flow.

## Implementation phasing (for the plan)

1. **Create the extension app** — vendor + rename the engine into
   `src/crud_views_object_detail/`; port its tests; green in isolation.
2. **Flip core** — `DetailView` → simple; remove `DetailCustomView`; move content
   template + checks to the extension; update `pyproject.toml`, `conftest`, example
   settings.
3. **Extension ripple** — polymorphic/guardian detail bases + guardian class removal.
4. **Docs merge** — move/rewrite detail + object-detail docs, fix cross-refs, nav.
5. **Example app** — new `object_detail` example (7 themes, 2 models, showcases, nav +
   badge, smoke tests).
6. **Sibling repo** — README notice + commit (archive deferred to post-release).

## Out of scope

- Redesigning the object-detail rendering engine, layout packs, or type templates
  (vendor as-is, renamed only).
- New layout packs or field types.
- Changes to non-detail core views.
