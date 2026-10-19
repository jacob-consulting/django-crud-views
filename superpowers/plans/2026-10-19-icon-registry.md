# Icon Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hard-coded Font Awesome classes and object detail's separate icon settings with one icon mechanism:
semantic names → layered table → `prefix:name` → per-library renderer, rendered by `{% cv_icon %}`.

**Architecture:** A new module `crud_views/lib/icons.py` owns the default table, the Bootstrap preset, the library
registry, theme registration, resolution (cached, reset on `setting_changed`) and `render_icon()`. Template tags in
`crud_views` and `crud_views_object_detail` both delegate to `render_icon()`. View classes, buttons and templates
pass semantic names instead of CSS classes. System checks make the removed settings and bad icon values loud.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12+, pytest + pytest-django, vitest (JS), MkDocs.

**Spec:** `superpowers/specs/2026-10-19-icon-registry-design.md` — read it alongside this plan.

## Global Constraints

- Python 3.12+, Django 4.2/5.2/6.0; the nox matrix must pass (`task test`).
- Ruff, line length 120, double quotes (`task format`, `task check`).
- Package source lives under `src/`; tests under `tests/test1/` (Python) and `tests/js/` (vitest).
- Clean break, no compatibility layer for removed settings or object-detail auto-prefixing.
- Package defaults are Font Awesome **free** only, styles `far` (regular) / `fas` (solid); no Bootstrap Icons in
  defaults.
- Icon markup must be escaped: only renderers return markup, names and extra classes are escaped (`format_html`).
- Resolution is cached; no per-render rebuilding of the table.
- Module path decision (spec left it to the builder): public API is `crud_views.lib.icons` (like
  `crud_views.lib.assets`), not `crud_views.icons`. Docs use this path.

## Review Focus

1. **Value with an unregistered prefix at render time** (`"xy:rocket"` with no `xy` library, e.g. a typo): renders
   nothing, does not raise, and W353/W352 report it at startup. Test in Task 1 (render) and Task 3 (check).
2. **`override_settings(CRUD_VIEWS_ICONS=…)` in tests and projects that change settings at runtime**: the cached
   table must refresh. Test in Task 1.
3. **Icon-only buttons stay accessible once icons are `aria-hidden`**: card actions with `cv_no_label` must carry a
   visually-hidden label. Test in Task 4.
4. **Object detail used with group icons that are bare names not in the table** (`icon="truck"` from 0.29 projects):
   renders `<i class="truck">` (raw-class rule), i.e. invisible but not an error. The changelog must say so
   explicitly; the example project must be migrated. Test in Task 6.
5. **Filter page reloaded with the panel open**: toggle shows `filter-close`, and one click flips both the panel and
   the icon. Test in Task 5 (Python + JS).

---

### Task 1: Icon registry core

**Files:**
- Create: `src/crud_views/lib/icons.py`
- Test: `tests/test1/test_icons_registry.py`

**Interfaces:**
- Produces (all in `crud_views.lib.icons`):
  - `DEFAULT_ICONS: dict[str, str]` — exact table below.
  - `BOOTSTRAP_ICONS: dict[str, str]` — exact table below.
  - `BUILTIN_LIBRARIES: dict[str, dict]` — `{"far": {"renderer": "font", "class": "fa-regular fa-{name}"}, "fas": {"renderer": "font", "class": "fa-solid fa-{name}"}, "bi": {"renderer": "font", "class": "bi bi-{name}"}}`.
  - `register_icon_library(prefix: str, renderer: str | Callable = "font", **config) -> None` — theme API; stores `{"renderer": renderer, **config}`, resets the cache.
  - `register_icons(icons: dict[str, str]) -> None` — theme API; merges into theme layer, resets the cache.
  - `get_icons() -> dict[str, str]` — resolved table: `DEFAULT_ICONS ⊕ theme ⊕ settings.CRUD_VIEWS_ICONS`, cached.
  - `get_libraries() -> dict[str, dict]` — `BUILTIN_LIBRARIES ⊕ theme ⊕ settings.CRUD_VIEWS_ICON_LIBRARIES`, whole
    entries replaced per prefix, cached.
  - `resolve_icon(value: str | None) -> tuple[str, str] | None` — `None` for empty; `("", value)` for a raw CSS class;
    `(prefix, name)` otherwise. One lookup step: a semantic name maps to its table value, which is then split on the
    **first** `:` only; if the table value has no colon it is a raw class.
  - `render_icon(value: str | None, css: str = "") -> SafeString` — empty string for empty values and for unknown
    prefixes; raw class → `<i class="{value}[ {css}]" aria-hidden="true"></i>`; otherwise calls the library
    renderer.
  - Renderer callable contract: `renderer(name: str, *, css: str, config: dict) -> SafeString`. `"font"` is the
    built-in renderer (`font_renderer`): `<i class="{config['class'].format(name=name)}[ {css}]" aria-hidden="true"></i>`.
    A string other than `"font"` is a dotted path, imported with `django.utils.module_loading.import_string`.
  - `reset_icon_cache() -> None` — connected to `django.core.signals.setting_changed` for the keys
    `CRUD_VIEWS_ICONS` and `CRUD_VIEWS_ICON_LIBRARIES`.
  - Private, for tests: `_THEME_ICONS: dict`, `_THEME_LIBRARIES: dict` (module-level).

Default table (`DEFAULT_ICONS`), all verified free in Font Awesome 6.7.2:

| name | value | name | value |
|---|---|---|---|
| `list` | `far:rectangle-list` | `sort-asc` | `fas:arrow-up-short-wide` |
| `card` | `fas:rectangle-list` | `sort-desc` | `fas:arrow-down-wide-short` |
| `detail` | `far:eye` | `table-sort-asc` | `fas:angles-up` |
| `create` | `far:square-plus` | `table-sort-desc` | `fas:angles-down` |
| `update` | `far:pen-to-square` | `formset-up` | `fas:caret-up` |
| `delete` | `far:trash-can` | `formset-down` | `fas:caret-down` |
| `order-up` | `far:circle-up` | `formset-add` | `fas:plus` |
| `order-down` | `far:circle-down` | `formset-delete` | `fas:square-xmark` |
| `manage` | `fas:gear` | `field-marker` | `fas:angles-right` |
| `workflow` | `fas:diagram-project` | `boolean-true` | `fas:circle-check` |
| `actions-menu` | `fas:ellipsis` | `boolean-false` | `fas:circle-xmark` |
| `filter` | `fas:filter` | `property-detail` | `fas:circle-info` |
| `filter-close` | `fas:filter-circle-xmark` | `text-icon` | `far:file-lines` |
| `language` | `fas:language` | | |

Table sort direction (my call, resolving the spec's "verify"): ascending shows **up**, matching `sort-asc` on card
order. 0.29.4 showed down for ascending; changelog notes it.

Bootstrap preset (`BOOTSTRAP_ICONS`), all `bi:`: `list` list-ul, `card` card-list, `detail` eye, `create`
plus-square, `update` pencil-square, `delete` trash, `order-up` arrow-up-circle, `order-down` arrow-down-circle,
`manage` gear, `workflow` diagram-3, `actions-menu` three-dots, `filter` funnel, `filter-close` x-circle,
`sort-asc` sort-up, `sort-desc` sort-down, `table-sort-asc` chevron-double-up, `table-sort-desc` chevron-double-down,
`formset-up` caret-up-fill, `formset-down` caret-down-fill, `formset-add` plus-lg, `formset-delete` x-square-fill,
`field-marker` chevron-double-right, `boolean-true` check-circle-fill, `boolean-false` x-circle-fill,
`property-detail` info-circle, `text-icon` journal-text, `language` translate.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_icons_registry.py`. A module fixture snapshots and
  restores `_THEME_ICONS` / `_THEME_LIBRARIES` and calls `reset_icon_cache()` around each test.

```python
def test_default_semantic_name_renders_font_awesome():
    assert render_icon("detail") == '<i class="fa-regular fa-eye" aria-hidden="true"></i>'

def test_prefixed_value_and_extra_css():
    assert render_icon("bi:person", css="me-2") == '<i class="bi bi-person me-2" aria-hidden="true"></i>'

def test_raw_class_fallback():
    assert render_icon("fa-solid fa-truck") == '<i class="fa-solid fa-truck" aria-hidden="true"></i>'

@pytest.mark.parametrize("value", [None, ""])
def test_empty_renders_nothing(value):
    assert render_icon(value) == ""

def test_unknown_prefix_renders_nothing():
    assert render_icon("xy:rocket") == ""

def test_escaping():
    out = render_icon('bi:x"><script>', css='"><b>')
    assert "<script>" not in out and "<b>" not in out

def test_resolve_splits_on_first_colon_only():
    assert resolve_icon("xy:a:b") == ("xy", "a:b")

def test_one_lookup_step_only():
    with override_settings(CRUD_VIEWS_ICONS={"alias": "detail"}):
        assert resolve_icon("alias") == ("", "detail")   # table value without colon = raw class

def test_precedence_package_theme_project():
    register_icons({"detail": "bi:eye", "update": "bi:pencil"})
    with override_settings(CRUD_VIEWS_ICONS={"detail": "fas:magnifying-glass", "person": "far:user"}):
        icons = get_icons()
        assert icons["detail"] == "fas:magnifying-glass"   # project beats theme
        assert icons["update"] == "bi:pencil"              # theme beats package
        assert icons["delete"] == "far:trash-can"          # package default kept
        assert icons["person"] == "far:user"               # project-defined name

def test_override_settings_refreshes_cache():
    assert get_icons()["detail"] == "far:eye"
    with override_settings(CRUD_VIEWS_ICONS={"detail": "bi:eye"}):
        assert get_icons()["detail"] == "bi:eye"
    assert get_icons()["detail"] == "far:eye"

def test_library_entry_replaced_whole():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"far": {"renderer": "font", "class": "x-{name}"}}):
        assert render_icon("far:eye") == '<i class="x-eye" aria-hidden="true"></i>'

def test_custom_renderer_dotted_path():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "tests.test1.test_icons_registry.xy_renderer"}}):
        assert render_icon("xy:rocket", css="big") == '<svg data-icon="rocket" class="big"></svg>'

def test_theme_library_registration():
    register_icon_library("tb", renderer="font", **{"class": "ti ti-{name}"})
    assert render_icon("tb:eye") == '<i class="ti ti-eye" aria-hidden="true"></i>'

def test_bootstrap_preset_covers_exactly_default_names():
    assert BOOTSTRAP_ICONS.keys() == DEFAULT_ICONS.keys()
    assert all(v.startswith("bi:") for v in BOOTSTRAP_ICONS.values())

def test_defaults_are_font_awesome_only():
    assert all(v.split(":", 1)[0] in ("far", "fas") for v in DEFAULT_ICONS.values())
```

  `xy_renderer` is a module-level helper in the test file returning
  `format_html('<svg data-icon="{}" class="{}"></svg>', name, css)`.

- [ ] **Step 2: Run** `pytest tests/test1/test_icons_registry.py -v` — Expected: FAIL (module does not exist).
- [ ] **Step 3: Implement `src/crud_views/lib/icons.py`** per the Interfaces block. Cache = module-level `None`
  sentinels for the two resolved dicts; read Django settings lazily via `getattr(settings, …, {})` (not via
  `CrudViewsSettings`, whose fields are evaluated at import). Connect the `setting_changed` receiver at module level.
- [ ] **Step 4: Run** `pytest tests/test1/test_icons_registry.py -v` — Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(icons): icon registry with semantic names, libraries and renderers"`

---

### Task 2: `{% cv_icon %}` tag and fixed-width class

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (add tag)
- Modify: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py` (add the same tag name)
- Create: `src/crud_views/static/crud_views/css/icons.css`
- Modify: `src/crud_views/lib/settings.py:214-221` (add `"icons": self.get_css("icons.css")` to the `css` Box)
- Test: `tests/test1/test_icons_tag.py`

**Interfaces:**
- Consumes: `render_icon(value, css="")` from Task 1.
- Produces: template tag `{% cv_icon value %}` / `{% cv_icon value css="me-2" %}` in both tag libraries
  (`crud_views` and `crud_views_object_detail`), implemented as `simple_tag` returning `render_icon(value, css)`.
  CSS class `cv-icon-fw` (fixed width, centred; `width: 1.25em; display: inline-block; text-align: center`) served by
  `{% cv_css %}`.

- [ ] **Step 1: Write failing tests**: render `Template("{% load crud_views %}{% cv_icon v css='me-2' %}")` with
  `v="detail"` → `'<i class="fa-regular fa-eye me-2" aria-hidden="true"></i>'`; same via
  `{% load crud_views_object_detail %}`; `v=None` → `""`; `{% cv_css %}` output contains `crud_views/css/icons.css`.
- [ ] **Step 2: Run** `pytest tests/test1/test_icons_tag.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** the two tags and the CSS file/entry.
- [ ] **Step 4: Run** `pytest tests/test1/test_icons_tag.py tests/test1/test_assets.py -v` — Expected: PASS (update
  asset tests only where they enumerate the core CSS list).
- [ ] **Step 5: Commit** `git commit -m "feat(icons): cv_icon template tag and cv-icon-fw class"`

---

### Task 3: System checks for icons

**Files:**
- Modify: `src/crud_views/lib/icons.py` (add `icon_check_messages() -> list[CheckMessage]`)
- Modify: `src/crud_views/checks.py` (new `@register(TAG) def check_icons(...)`)
- Test: `tests/test1/test_icons_checks.py`

**Interfaces:**
- Consumes: `get_icons()`, `get_libraries()`, `resolve_icon()` from Task 1; `_REGISTRY`, `_REGISTRY_LOCK` and
  `viewset.get_all_views()` from `crud_views.lib.viewset` (pattern: `_registry_needs_ordered_model` in `checks.py`).
- Produces check IDs (new, unused range):
  - `crud_views.E350` — a removed setting is defined (one message per setting): `CRUD_VIEWS_ACTIONS_MENU_ICON`
    (hint: `CRUD_VIEWS_ICONS["actions-menu"]`), `CRUD_VIEWS_FILTER_ICON` (hint: `CRUD_VIEWS_ICONS["filter"]`),
    `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`, `…_ICONS_CLASS`, `…_ICONS_TYPE`, `…_ICONS_PREFIX`,
    `…_NAMED_ICONS` (hint: `CRUD_VIEWS_ICONS` / `BOOTSTRAP_ICONS` from `crud_views.lib.icons`). Detect with
    `hasattr(settings, name)`.
  - `crud_views.E351` — a library's renderer dotted path cannot be imported.
  - `crud_views.W352` — a table entry whose value has an unregistered prefix, or whose value is itself a key of the
    table (name → name).
  - `crud_views.W353` — a view's `cv_icon_action` / `cv_icon_header` or a ViewSet's `icon_header` contains `:` with an
    unregistered prefix. Message names the viewset/view and attribute. Bare values are not flagged.

- [ ] **Step 1: Write failing tests**, one per ID, using `override_settings` and calling `check_icons()` directly;
  plus `test_default_config_has_no_icon_messages` asserting `check_icons() == []` with the test project's settings.
  For W353 define a throwaway ViewSet/view in the test with `icon_header="xy:truck"` and remove it from `_REGISTRY`
  in teardown (follow the existing pattern in `tests/test1/test_context_button_check.py`).
- [ ] **Step 2: Run** `pytest tests/test1/test_icons_checks.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** `icon_check_messages()` (E350–W352) and the view walk (W353) in `check_icons`.
- [ ] **Step 4: Run** `pytest tests/test1/test_icons_checks.py -v` — Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(icons): system checks for removed settings and icon values"`

---

### Task 4: Core views, buttons and templates use semantic names

**Files:**
- Modify view defaults: `src/crud_views/lib/views/{list,card,detail,create,update,delete,action_ordered,manage}.py`,
  `src/crud_views_polymorphic/lib/create_select.py:43`, `src/crud_views_workflow/lib/views.py:29-30`
- Modify: `src/crud_views/lib/view/base.py:104-105` (drop "font awesome icon" comments; type/semantics: any icon value)
- Modify: `src/crud_views/lib/settings.py` (remove fields `actions_menu_icon`, `filter_icon`)
- Modify: `src/crud_views/lib/view/buttons.py:311` (`"filter"`), `src/crud_views/lib/views/list.py:36` and
  `card.py:92` (`cv_get_filter_icon()` returns `"filter"`), `src/crud_views/templatetags/crud_views.py:163`
  (`"cv_menu_icon": "actions-menu"`)
- Modify templatetags: `cv_header_icon` and `cv_filter_icon` become `simple_tag`s returning `render_icon(...)`;
  delete `cv_header_icon_class`, `cv_filter_icon_class` and `src/crud_views/templates/crud_views/tags/icon.html`.
- Modify templates (every `<i class=…>` → `{% cv_icon … %}`): `tags/context_action.html`, `tags/list_action.html`,
  `tags/card_action.html`, `tags/actions_menu_toggle.html`, `tags/actions_menu_item_label.html` (`fa-fw` →
  `css="cv-icon-fw"`, placeholder span `class="cv-icon-fw d-inline-block"`), `snippets/card_order.html`
  (`sort-asc`/`sort-desc`), `snippets/language_selector.html`, `table/bootstrap5.html` (`table-sort-asc` when
  `sort == column.name`, `table-sort-desc` for `-column.name`), `formsets/control.html`,
  `detail/widgets/display.html` (`field-marker`), `detail/widgets/bool.html` (`field-marker`, `boolean-true`,
  `boolean-false`)
- Regenerate: `tests/test1/golden/action_menus/*.html`
- Test: `tests/test1/test_icons_templates.py`; update existing tests that assert FA classes
  (`test_action_menus_config.py`, `test_action_menus_list.py`, `test_language_selector.py`, `test_filter.py`,
  `test_card.py`, `test_manage.py`, `test_resource_views.py`, `test_template_a11y.py` — whichever fail)

**Interfaces:**
- Consumes: `{% cv_icon %}` (Task 2), `render_icon` (Task 1).
- Produces: view class defaults — `ListView.cv_icon_action = "list"`, `CardView "card"`, `DetailView "detail"`,
  `CreateView "create"`, `UpdateView "update"`, `DeleteView "delete"`, `OrderedUpView "order-up"`,
  `OrderedDownView "order-down"`, `ManageView` action+header `"manage"`, polymorphic create-select `"create"`,
  `WorkflowView` action+header `"workflow"`. Context variable `cv_icon_action` / `cv_menu_icon` now carries icon
  values, never markup.

- [ ] **Step 1: Write failing tests** in `test_icons_templates.py`: (a) a list page's detail action contains
  `fa-regular fa-eye`, rendered from the semantic default; (b) with
  `override_settings(CRUD_VIEWS_ICONS={"detail": "bi:search"})` the same page contains `bi bi-search` and not
  `fa-eye`; (c) the actions-menu toggle contains `fa-solid fa-ellipsis`; (d) a menu item label contains
  `cv-icon-fw`; (e) `grep`-style assertion: no file under `src/*/templates` or `src/crud_views/static/crud_views/js`
  contains `"fa-"` or `"bi-"` (walk files in the test); (f) a card action with `CardAction(no_label=True)` renders a
  `visually-hidden` span with the label.
- [ ] **Step 2: Run** `pytest tests/test1/test_icons_templates.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** the view defaults, button/tag changes, settings field removal and template changes listed
  above. Add `<span class="visually-hidden">{{ cv_label }}</span>` next to the icon in the `cv_no_label` branches of
  `card_action.html`. Test (e) also covers `list.filter.js`; leave it failing until Task 5 by marking (e) with
  `pytest.mark.xfail(strict=True, reason="list.filter.js, Task 5")`.
- [ ] **Step 4: Regenerate golden files** `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`, then
  review `git diff tests/test1/golden` — only icon markup (`aria-hidden`, class order, `cv-icon-fw`, card
  visually-hidden label) may change.
- [ ] **Step 5: Run** `pytest tests` — Expected: PASS (fix tests asserting old FA strings to the new rendering).
- [ ] **Step 6: Commit** `git commit -m "feat(icons): core views and templates render icons via cv_icon"`

---

### Task 5: Filter toggle shows panel state without library names in JS

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py` (filter button data, ~line 300-315)
- Modify: `src/crud_views/templates/crud_views/tags/context_action_filter.html`
- Modify: `src/crud_views/static/crud_views/js/list.filter.js:28`
- Test: `tests/test1/test_filter.py` (extend), `tests/js/list.filter.test.js` (new)

**Interfaces:**
- Consumes: `SessionData.from_view(view).get("filter_expanded", False)` (as in `lib/views/mixins.py:326`).
- Produces: button context `cv_filter_expanded: bool`; template renders two spans
  `<span data-cv-filter-icon="open" …>{% cv_icon "filter" %}</span>` and
  `<span data-cv-filter-icon="close" …>{% cv_icon "filter-close" %}</span>`, the inactive one with class `d-none`.
  JS on click: `$(this).find("[data-cv-filter-icon]").toggleClass("d-none")`.

- [ ] **Step 1: Write failing tests**: Python — GET a filter list page with the session's `filter_expanded` False →
  the `open` span is visible and `close` has `d-none`; set it True (POST like the existing filter-state test in
  `test_filter.py`) and reload → reversed. JS — load `list.filter` with a fixture containing `#cv-filter-toggle`, the
  two spans and `#filter-collapse`; click → visibility of both spans flips. Follow `tests/js/viewset.test.js`
  (`loadScript`); stub `$.post` and the collapse toggle.
- [ ] **Step 2: Run** `pytest tests/test1/test_filter.py -v` and `npx vitest run tests/js/list.filter.test.js` —
  Expected: FAIL.
- [ ] **Step 3: Implement** the button context, template and JS line. Remove the `xfail` marker from Task 4's test (e).
- [ ] **Step 4: Run** `pytest tests/test1/test_filter.py tests/test1/test_icons_templates.py -v` and `npx vitest run`
  — Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(filter): toggle icon follows panel state, no icon classes in JS"`

---

### Task 6: Object detail migration

**Files:**
- Modify: `src/crud_views_object_detail/lib/conf.py` (remove `ICON_LIBRARY_DEFAULTS`, `NAMED_ICONS_DEFAULTS`,
  `icons_*`/`named_icons` properties, `build_icon_class`, `build_named_icon_class`)
- Modify: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py` (remove `icon_class`,
  `named_icon_class` filters)
- Modify templates: `layouts/{accordion,split-card,striped-rows}/group.html`, `layouts/tabs-vertical/object_detail.html`
  (`{% cv_icon group.icon css="me-2" %}`, keep each template's existing extra classes such as `text-default fs-5`),
  `layouts/card-rows/property.html` (`property-detail`), `layouts/list-group-3col/property.html` (`text-icon`,
  `css="me-1"`), `types/default/boolean.html` (`boolean-true` `css="text-success"`, `boolean-false`
  `css="text-danger"`)
- Rewrite: `tests/test1/od/test_icons.py`; update `tests/test1/od/test_templatetags.py`, `test_layout_packs.py`,
  `test_config.py`, `test_resolvers.py` where they assert `bi-…` output
- Modify: `examples/bootstrap5/object_detail/views.py` (group icons `"truck"` → `"fas:truck"`, `"box"` → `"fas:box"`,
  `"warehouse"` → `"fas:warehouse"`, `"tags"` → `"fas:tags"`), `examples/bootstrap5/project/settings.py:142-143`
  (remove both `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*` lines)

**Interfaces:**
- Consumes: `{% cv_icon %}` from the `crud_views_object_detail` tag library (Task 2).

- [ ] **Step 1: Rewrite `tests/test1/od/test_icons.py`** to assert: group `icon="fas:truck"` renders
  `fa-solid fa-truck` in each of the four group layouts; `icon="truck"` renders `<i class="truck" …>` (raw-class
  rule, Review Focus 4); a boolean True renders `fa-solid fa-circle-check text-success`; property detail renders
  `fa-solid fa-circle-info`; with `CRUD_VIEWS_ICONS=BOOTSTRAP_ICONS` the boolean renders `bi bi-check-circle-fill`.
- [ ] **Step 2: Run** `pytest tests/test1/od -v` — Expected: FAIL.
- [ ] **Step 3: Implement** the removals and template changes; migrate the example project.
- [ ] **Step 4: Run** `pytest tests` and `pytest examples/bootstrap5` — Expected: PASS; `python -m django check`
  in the example project (or its test equivalent) reports no E350.
- [ ] **Step 5: Commit** `git commit -m "feat(object-detail)!: use the core icon registry"`

---

### Task 7: Documentation, examples and changelog

**Files:**
- Create: `docs/reference/icons.md`
- Modify: `docs/reference/settings.md` (remove `CRUD_VIEWS_FILTER_ICON` line 40 and `CRUD_VIEWS_ACTIONS_MENU_ICON`
  line 79; add `CRUD_VIEWS_ICONS`, `CRUD_VIEWS_ICON_LIBRARIES` linking to icons.md),
  `docs/reference/object_detail_settings.md` (remove icon settings section, link to icons.md),
  `docs/reference/object_detail_view.md`, `docs/reference/theme.md` (theme registration via
  `register_icon_library` / `register_icons` in `AppConfig.ready()`), `docs/reference/action_menus.md`,
  `docs/reference/custom_form_view.md`, `docs/reference/create_view.md` (any icon examples → `prefix:name` or
  semantic names; keep `cv-sync` blocks identical to the example files they reference)
- Modify: `CHANGELOG.md` (unreleased section)
- Modify: the django-crud-views skill in this repo if it documents the removed settings (`grep -rn
  "FILTER_ICON\|ACTIONS_MENU_ICON\|OBJECT_DETAIL_ICONS" --include=*.md .` outside `docs/` and `superpowers/`)

**Interfaces:**
- Consumes: public names from Task 1 (`crud_views.lib.icons.BOOTSTRAP_ICONS`, `register_icon_library`,
  `register_icons`), check IDs from Task 3, semantic names from Task 1.

- [ ] **Step 1: Write `docs/reference/icons.md`** covering, in this order: icon values (three forms and the
  resolution order), the default table, `CRUD_VIEWS_ICONS` (override + own names, merge semantics), libraries and
  `CRUD_VIEWS_ICON_LIBRARIES` (font renderer config, custom renderer contract with an SVG example), Bootstrap preset,
  theme registration and precedence (`INSTALLED_APPS` order between themes), name-collision note, checks E350–W353.
- [ ] **Step 2: Update the other docs** listed above.
- [ ] **Step 3: CHANGELOG** "Breaking" entries with migration snippets: removed `CRUD_VIEWS_ACTIONS_MENU_ICON`,
  `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*`; object detail defaults now Font Awesome (one-line
  `BOOTSTRAP_ICONS` restore); group icons no longer auto-prefixed (`icon="truck"` → `"fas:truck"` or a
  `CRUD_VIEWS_ICONS` entry); `tags/icon.html`, `cv_header_icon_class`, `cv_filter_icon_class` removed; core bool
  widget icons changed; table sort icons now FA 6 with ascending = up; icons `aria-hidden` by default; `fa-fw` →
  `cv-icon-fw`. "Fixed": filter toggle icon after reload. "Added": icon registry.
- [ ] **Step 4: Run** `pytest examples/bootstrap5/test_docs_sync.py -v` and `task docs` build (or
  `mkdocs build --strict`) — Expected: PASS, no broken links.
- [ ] **Step 5: Run the full matrix** `task test` and `npx vitest run` — Expected: all green.
- [ ] **Step 6: Commit** `git commit -m "docs(icons): icon registry reference, migration notes"`
