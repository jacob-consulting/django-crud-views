# Icon registry: semantic icon names and pluggable icon libraries

Date: 2026-10-19
Status: draft, reviewed by builder check

## Intent

django-crud-views hard-codes Font Awesome class strings in view classes, settings, templates and JavaScript, and
`crud_views_object_detail` has a second, unrelated icon mechanism (Bootstrap Icons by default). Building a Tabler
theme (`tabler-test/docs/crud_views_upstream_questions.md`, section 1) showed the cost: the theme had to map Font
Awesome class strings to Tabler SVGs at render time, a table that felt like a hack and still left half the icons as
Font Awesome.

The goal is **one icon mechanism for the whole package** in which:

- the package refers to its icons by **semantic name** (`detail`, `delete`, `filter`, …), never by library class;
- what each name looks like comes from a **layered table**: package defaults → theme → project settings;
- **how** an icon becomes HTML (font `<i>`, inline SVG, sprite, anything) is decided by a **renderer registered per
  library prefix**, so libraries can be mixed and a customer's own library is just one more prefix;
- everything renders through **one template tag**.

## Goals

- Semantic names for every icon the package (core + object detail + polymorphic + workflow) renders.
- Icon values of the form `prefix:name` (`far:eye`, `bi:person`, `xy:rocket`), resolved through a library registry.
- Projects can override any default and add their own semantic names (`"person": "far:user"`) and use them anywhere
  an icon value is accepted.
- A theme app can register libraries and default icons without project configuration.
- Package defaults use **Font Awesome only** (no mixing). A complete **Bootstrap Icons preset** ships as opt-in.
- A project that does nothing renders the same core icons as today (object detail changes, see below).

## Non-goals

- Updating `crud_views_tabler` (in the `tabler-test` repo). That comes later and will consume this mechanism.
- Shipping SVG icon sets or an SVG renderer for a specific library. The renderer interface must allow SVG; the
  package only ships what its defaults need (a font/CSS-class renderer).
- Changing button classes, jQuery, context-action variants or template logic/markup separation (sections 2–5 of
  the upstream questions doc).

## Anti-goals

- Any Font Awesome knowledge left in core code paths outside the default icon table (e.g. `fa-fw` in templates,
  `fa-filter` in JS). If a theme still has to know Font Awesome class names to restyle core, this failed.
- Defaults that require two icon libraries to be loaded.

## Decisions made with the maintainer

- **Precedence:** package defaults → theme defaults → project settings; project settings always win.
- **Clean break, no compatibility layer** (package is 0.29, alpha). Changelog note is sufficient.
  - `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`, `_ICONS_CLASS`, `_ICONS_TYPE`, `_ICONS_PREFIX`, `_NAMED_ICONS` are
    removed.
  - Object detail group icons (`icon="person"`) are no longer auto-prefixed. Projects either write `bi:person` /
    `far:user` or add `"person"` to `CRUD_VIEWS_ICONS`.
- **Font Awesome only** in the package defaults; object detail's defaults move from Bootstrap Icons to Font Awesome.
- **Ship a complete Bootstrap Icons preset.**
- **Upstream only**; Tabler theme later.

## Design

### Icon values

An icon value is a string in one of three forms, resolved in this order:

1. **Semantic name** — no colon, present in the resolved icon table (`"detail"`, `"person"`). Looked up, the result
   is resolved again as a `prefix:name` value. One lookup step only; a table entry pointing to another semantic
   name is not followed (keeps resolution predictable; the system check flags it).
2. **`prefix:name`** — `prefix` is looked up in the library registry, its renderer receives `name`.
3. **Anything else** (no colon, not a known name, e.g. `"fa-solid fa-truck"`) — rendered as a raw CSS class:
   `<i class="…">`. Kept because it costs nothing and lets hand-written class strings keep working.

Empty / `None` renders nothing.

### Library registry

`CRUD_VIEWS_ICON_LIBRARIES`: dict of prefix → library config. Built-in renderer:

- `"font"` (CSS-class renderer): config `{"renderer": "font", "class": "fa-regular fa-{name}"}` → renders
  `<i class="fa-regular fa-eye {extra}" aria-hidden="true"></i>`.

A renderer may also be given as a dotted path to a callable (`"myproject.icons.render_xy"`). Callable signature
(builder may refine): `(name: str, *, css_class: str, attrs: dict) -> SafeString`.

Built-in library entries:

| Prefix | Config |
|---|---|
| `far` | font, `fa-regular fa-{name}` |
| `fas` | font, `fa-solid fa-{name}` |
| `bi` | font, `bi bi-{name}` |

Prefixes follow Font Awesome's own short names (`far`, `fas`) and Bootstrap Icons' class prefix (`bi`). More Font
Awesome styles (`fal`, `fab`, …) are just more entries. Shipping `bi` is required for the Bootstrap preset; it costs
nothing if unused.

### Icon table

`CRUD_VIEWS_ICONS`: dict of semantic name → icon value. Open: projects may add any name.

Default table (Font Awesome; reproduces 0.29.4 core output):

| Name | Default | Used by (0.29.4 location) |
|---|---|---|
| `list` | `far:rectangle-list` | `lib/views/list.py` |
| `card` | `fas:rectangle-list` | `lib/views/card.py` |
| `detail` | `far:eye` | `lib/views/detail.py` |
| `create` | `far:square-plus` | `lib/views/create.py`, polymorphic `create_select.py` |
| `update` | `far:pen-to-square` | `lib/views/update.py` |
| `delete` | `far:trash-can` | `lib/views/delete.py` |
| `order-up` | `far:circle-up` | `lib/views/action_ordered.py` |
| `order-down` | `far:circle-down` | `lib/views/action_ordered.py` |
| `manage` | `fas:gear` | `lib/views/manage.py` (action + header) |
| `workflow` | `fas:diagram-project` | `crud_views_workflow/lib/views.py` (action + header) |
| `actions-menu` | `fas:ellipsis` | setting `CRUD_VIEWS_ACTIONS_MENU_ICON`, `tags/actions_menu_toggle.html` |
| `filter` | `fas:filter` | setting `CRUD_VIEWS_FILTER_ICON`, filter button, `list.filter.js` |
| `filter-close` | `fas:filter-circle-xmark` | `list.filter.js:28` (shown while the filter panel is open) |
| `sort-asc` / `sort-desc` | `fas:arrow-up-short-wide` / `fas:arrow-down-wide-short` | `snippets/card_order.html` |
| `table-sort-asc` / `table-sort-desc` | see note | `table/bootstrap5.html:16-17` |
| `formset-up` / `formset-down` | `fas:caret-up` / `fas:caret-down` | `formsets/control.html` |
| `formset-add` / `formset-delete` | `fas:plus` / `fas:square-xmark` | `formsets/control.html` |
| `field-marker` | `fas:angles-right` | `detail/widgets/display.html`, `bool.html` |
| `boolean-true` / `boolean-false` | `fas:circle-check` / `fas:circle-xmark` | object detail `types/default/boolean.html`; core `detail/widgets/bool.html` |
| `property-detail` | `fas:circle-info` | object detail `property.html` (card-rows) |
| `text-icon` | `far:file-lines` | object detail `property.html` (list-group-3col) |
| `language` | `fas:language` | `snippets/language_selector.html` |

Notes:

- **Free Font Awesome only (my call):** every default must exist in the free Font Awesome 6 set, since that is what
  projects load (the example uses 6.7.2 free from cdnjs). Checked against the 6.7.2 free SVGs: all entries above
  exist in the given style. `far:circle-info` (object detail's current Font Awesome mode) is Pro-only and renders
  blank on free; the table therefore uses `fas:circle-info`. Any name added later must be checked the same way.

- **Table sort icons:** 0.29.4 uses Font Awesome 4 syntax (`fa fa-angle-double-down` for ascending,
  `fa fa-angle-double-up` for descending), which probably needs FA v4 shims to render in FA 6, and the direction
  looks inverted. Builder: verify in the example app, pick FA 6 names (`fas:angles-up` / `fas:angles-down` or
  similar) with the correct direction, and note the visual change in the changelog.
- **Boolean merge (my call):** core's `detail/widgets/bool.html` (today `fa-regular fa-square-check` /
  `fa-square`) uses `boolean-true` / `boolean-false` too, so there is one pair instead of two. Visual change for
  core's bool widget; changelog note.
- No default for header icons (`cv_icon_header`, ViewSet `icon_header`) except `manage` and `workflow` — unchanged.

### Bootstrap Icons preset

`crud_views.icons.BOOTSTRAP_ICONS`: a dict covering **every** name in the default table with `bi:` values. Usage:

```python
from crud_views.icons import BOOTSTRAP_ICONS
CRUD_VIEWS_ICONS = {**BOOTSTRAP_ICONS, "detail": "bi:search"}
```

Object detail's current Bootstrap names (`check-circle-fill`, `x-circle-fill`, `info-circle`, `journal-text`) go
into this preset so a project on Bootstrap Icons today restores object detail's look with one line. Builder picks
the remaining Bootstrap equivalents.

A test asserts that `BOOTSTRAP_ICONS` and the default table have exactly the same keys, so adding a semantic name
without a Bootstrap entry fails CI.

### Layering

Resolved once (lazily, cached) at first use:

```
icons     = package defaults  ⊕ theme registrations  ⊕ settings.CRUD_VIEWS_ICONS
libraries = package built-ins ⊕ theme registrations  ⊕ settings.CRUD_VIEWS_ICON_LIBRARIES
```

`⊕` is a per-key dict merge; later wins. A project lists only what it changes or adds. For libraries the unit is
the whole entry: a project entry for `far` replaces the built-in `far` config, it is not merged field by field.

**Theme API:** a theme registers from its `AppConfig.ready()`, e.g.

```python
from crud_views.icons import register_icon_library, register_icons
register_icon_library("tabler", renderer="crud_views_tabler.icons.render")
register_icons({"detail": "tabler:eye", ...})
```

Exact function names are the builder's call. If two apps register the same key, later in `INSTALLED_APPS` wins
(document it; no conflict detection needed). Registration after the table has been resolved should raise or warn
rather than be silently ignored (builder's call).

Project-defined names that collide with a package name added in a later release: the project entry wins (it always
does). Document; no mechanism.

### Rendering

One template tag in `crud_views` templatetags: `{% cv_icon value %}` with optional extra classes, e.g.
`{% cv_icon cv_icon_action class="me-2" %}` (exact argument syntax: builder). It:

- resolves the value as above,
- passes extra CSS classes through to the renderer (needed for `me-2`, `text-success`, `fs-5`, …),
- marks the icon `aria-hidden="true"` by default (labels are already provided as visually-hidden text where
  needed today),
- renders nothing for empty values.

A Python helper (`render_icon(value, css_class="")`) backs the tag so Python code and object detail's filters use
the same path.

`fa-fw` in `tags/actions_menu_item_label.html` (fixed width in menus) is Font Awesome–specific; replace it with a
library-neutral class/CSS (e.g. a `cv-icon-fw` class with a fixed width in crud_views' CSS) and keep the empty
placeholder span for items without an icon.

The existing `tags/icon.html` and the tags `cv_filter_icon`, `cv_filter_icon_class` and the header-icon tag that
render through it are switched to the new mechanism or removed (builder's call; clean break allowed).

### Where icon values come from (unchanged surface, new values)

- `cv_icon_action`, `cv_icon_header` on views and `icon_header` on ViewSets stay. They accept any icon value.
  Their defaults become semantic names (`cv_icon_action = "detail"`). Comments saying "font awesome icon" go.
- These values flow into templates as context (`cv_icon_action` in `lib/view/base.py:357`, `buttons.py:135,210,266,
  311`, `manage.py:128`, `card.py:55`). Templates render them with `{% cv_icon %}` instead of `<i class="{{ … }}">`.
- `cv_get_filter_icon()` (`lib/views/list.py:36`, `card.py:92`) returns a semantic name.
- Object detail group `icon` values are icon values (no auto-prefix any more).
- `CRUD_VIEWS_ACTIONS_MENU_ICON` and `CRUD_VIEWS_FILTER_ICON` are removed; replaced by table entries
  `actions-menu` and `filter`.

### Templates to change (0.29.4 inventory)

Every `<i class=…>` in shipped templates goes through `{% cv_icon %}`:

- `tags/context_action.html`, `tags/context_action_filter.html`, `tags/list_action.html`, `tags/card_action.html`,
  `tags/actions_menu_toggle.html`, `tags/actions_menu_item_label.html`, `tags/icon.html`, `tags/list_filter.inner.html`
- `snippets/card_order.html`, `snippets/language_selector.html`, `table/bootstrap5.html`, `formsets/control.html`,
  `detail/widgets/display.html`, `detail/widgets/bool.html`
- object detail: `layouts/*/group.html` (accordion, split-card, striped-rows), `layouts/tabs-vertical/object_detail.html`,
  `layouts/card-rows/property.html`, `layouts/list-group-3col/property.html`, `types/default/boolean.html`

The builder should grep for `fa-`, `bi-` and `<i class` across `src/` to catch anything this list misses
(polymorphic, workflow, guardian templates included).

### Filter toggle JavaScript

`list.filter.js:28` toggles `fa-filter fa-filter-circle-xmark` on an `<i>`. Replace with: the filter button renders
both icons, one hidden (e.g. wrapped in elements with a state class / `d-none`), and the JS toggles which one is
visible. No icon library names in JS.

Meaning (my call): the icon reflects the **panel state**, not whether filter values are set. `filter` = panel
closed (click to open), `filter-close` = panel open (click to close). This is what today's toggling intends, hence
the name `filter-close` rather than `filter-clear`.

Bug fix included (my call): today `context_action_filter.html` always starts with the `filter` icon even when the
session has the panel expanded, so after a reload with the panel open the icons are reversed. The button template
gets the expanded state (e.g. `cv_filter_expanded`) and renders the matching icon visible. Pinned filters show no
toggle (`buttons.py:303`), unchanged. Changelog line.

### Object detail migration

- Remove `ICON_LIBRARY_DEFAULTS`, `NAMED_ICONS_DEFAULTS`, the `icons_*` / `named_icons` settings properties,
  `build_icon_class`, `build_named_icon_class` (`src/crud_views_object_detail/lib/conf.py`).
- Replace the `icon_class` / `named_icon_class` filters with the core mechanism (templates use `{% cv_icon %}`).
- Update `tests/test1/od/test_icons.py` and object-detail docs (`docs/reference/object_detail_settings.md`,
  `object_detail_configuration.md`, layout packs) accordingly.
- Example project (`examples/bootstrap5/project/settings.py`) uses the old setting; update it.

### System checks

In `crud_views/checks.py` (IDs follow existing numbering; builder picks):

- **Error** if any removed setting is still defined: `CRUD_VIEWS_ACTIONS_MENU_ICON`, `CRUD_VIEWS_FILTER_ICON`,
  `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`, `_ICONS_CLASS`, `_ICONS_TYPE`, `_ICONS_PREFIX`, `_NAMED_ICONS`. Hint
  names the replacement. This makes the clean break loud.
- **Warning** for a table entry whose prefix is not a registered library, or whose value is itself a semantic name.
- **Warning** for view / ViewSet icon values (`cv_icon_action`, `cv_icon_header`, `icon_header`) with an unknown
  prefix. Bare values that are neither a known name nor contain a colon are raw CSS classes and are not flagged.
- **Error** for a library whose renderer dotted path cannot be imported.

Object detail group icons are configured per view at runtime; checking them is optional.

### Documentation

- New reference page "Icons": icon values, the default table, `CRUD_VIEWS_ICONS`, `CRUD_VIEWS_ICON_LIBRARIES`,
  custom renderers, project-defined names, Bootstrap preset, theme registration, precedence, collision note.
- Update `docs/reference/settings.md` (remove two settings, add two), object-detail docs, tutorial pages that set
  `cv_icon_*` / `icon_header` (values may stay as raw FA classes, but prefer `prefix:name` in examples).
- CHANGELOG: breaking changes (removed settings, object-detail default library, group icons no longer
  auto-prefixed, boolean widget icons, table sort icons) with migration snippets.
- The django-crud-views skill (if maintained in this repo) mentions `CRUD_VIEWS_FILTER_ICON` etc.; update it.

## Constraints

- Python 3.12+, Django 4.2/5.2/6.0 (nox matrix must pass).
- Ruff, 120 chars, double quotes.
- Rendered HTML must stay safe: icon names and extra classes are escaped; only renderers return markup.
- Rendering cost: resolution is a dict lookup plus a string format; the table and library registry are resolved
  once and cached, not per render.

## Left to the builder

- Module layout (`crud_views/icons.py` or `crud_views/lib/icons/`), function names, tag argument syntax.
- Renderer callable signature details and whether template-based renderers are supported in addition to callables.
- Bootstrap equivalents for names that have no obvious match.
- Exact system check IDs and messages.
- How the filter toggle hides the inactive icon.
- Whether to keep `tags/icon.html` as the font renderer's template or render in Python.

## Calls I made (not discussed with the maintainer)

- Library prefixes `far` / `fas` / `bi`.
- The semantic name list and spelling (`order-up`, `formset-add`, `field-marker`, …).
- Merging core's checkbox icons into `boolean-true` / `boolean-false`.
- Raw-CSS-class fallback for values with no colon that are not known names.
- One-step resolution (a name cannot point to another name).
- Removed settings raise a system **error**, not just a warning.
- `aria-hidden="true"` by default.
- `fa-fw` replaced by a library-neutral fixed-width class.
- Defaults restricted to free Font Awesome; `property-detail` uses `fas:circle-info` (regular is Pro-only).
- Filter icon names `filter` / `filter-close` reflect panel state; initial-state bug fixed.
- Library entries replace per prefix, not merged field by field.
