# Icon host placement: icon libraries that put the icon class on the button itself

Issue: #258. Follow-up for headings: #259.

Date: 2026-10-23

## Intent

Every icon reaches the button leaf as its own element: `tags/button/action.html` calls `{% cv_icon cv_icon %}`, which
renders `<i class="…" aria-hidden="true">` inside the button. Some design systems draw icons differently. The icon is a
class on an element and is painted by `::before`; there is never markup inside the element for it. With such a library
the bundled leaves can't be used, and the only route today is a project copy of the leaf. That brings back the
copy-the-leaf situation that 1.0 set out to remove.

The maintainer described the design system in the issue comment
(https://github.com/jacob-consulting/django-crud-views/issues/258#issuecomment-6360149210):

- **Standalone icon:** an empty element with a base class plus the name class: `<span class="icon icon-check">`.
- **Icon on a host element:** the element itself gets the class. Whether the base class is added depends on the
  host type, not on the library. Buttons, links and dropdown items take only the name class
  (`btn btn-with-icon icon-plus`, `dropdown-item link-icon icon-edit`). Headings take base plus name
  (`heading icon icon-info`; out of scope here, see #259).
- A trailing icon is not an option of its own. It is a different icon name, so just another entry in the icon table.
- The mode marker (`btn-with-icon` / `btn-icon-only`) already fits the existing `*:both` / `*:icon` class slots.

The maintainer's focus words for this series apply: maintainability, low complexity, easy to theme downstream, and no
more upstream surface than the issue needs.

## Goals

- An icon library can declare `placement: "host"`. For such a library, the button leaves put the icon's class on the
  button element and render no icon element inside it.
- The class a host adds is configurable per location through the button class table, so a theme decides whether a
  host gets a base class.
- The same library still renders correctly at every standalone call site (alerts, pagination, formset controls, …),
  with a base class configured in the library.
- The filter toggle works with a host library: it swaps the two icon classes on the button.
- With no host library configured, every template renders exactly what it renders today (existing goldens unchanged).
  No CHANGELOG `### Breaking` entry.

## Scope: host call sites

| Template | Location key | What changes in `host` placement |
|---|---|---|
| `crud_views/tags/button/action.html` | `context`, `list`, `card` (the leaf's `cv_location`) | class appended to `class="…"`; no inner icon, no space before the label |
| `crud_views/tags/button/menu_item.html` + `menu_item_label.html` | `menu` | class appended; no inner icon and no `cv-icon-fw` placeholder span |
| `crud_views/tags/actions_menu_toggle.html` (the "More actions" button) | its `cv_location` | class appended; no inner icon |
| `crud_views/tags/context_action_filter.html` (filter toggle) | `context` | class of the current state on the button; JS swaps classes |

The menu toggle is not named in the issue. It is included because it is a context / list / card button too and would
otherwise show an empty button with a host library (decided in the design conversation as part of "card, context and
list buttons as well as menu actions").

`crud_views/tags/actions_menu_item_label.html` also renders an icon, but it is a legacy template kept only for 0.30
overrides; the stock menu no longer includes it (`docs/reference/action_menus.md`). It stays unchanged.

## Non-goals

- **Headings and modal titles** (`{% cv_header_icon %}`, object-detail group headers): filed as #259.
- **Form buttons** (submit, delete, cancel, filter submit/reset): they are crispy `<input>`s today; #257 turns them
  into `<button>`s with a label mode. They come later and will pick up host placement then.
- **Other element sites** (alerts, pagination, card order, formset controls, table sort, language selector,
  object-detail property/boolean icons): they keep calling `{% cv_icon %}` and render a standalone element. No
  template change.
- **Custom renderers in host placement.** `host` is a `font` renderer feature only (see "System checks").

## Anti-goals

- Any change in output for a project that does not use a host library.
- A second copy of the label-mode logic. Hidden label, `title`, `data-cv-tooltip`, disabled handling stay exactly as
  they are; host placement only decides where the icon's class goes.
- Icons configured in two places. The icon table and the library definition stay the only place that names an icon;
  the class table only says what a host location wraps around the name class.

## Configuration (decided)

### Library

```python
CRUD_VIEWS_ICON_LIBRARIES = {
    "ui": {
        "renderer": "font",
        "class": "icon-{name}",              # the bare name class
        "placement": "host",                 # default "element" = today
        "standalone": "icon {name_class}",   # default "{name_class}"
    },
}
# or from a theme: register_icon_library("ui", renderer="font", placement="host",
#                                       **{"class": "icon-{name}", "standalone": "icon {name_class}"})
```

- `placement`: `"element"` (default) or `"host"`.
- `class`: unchanged meaning, a format string with `{name}`. For a host library it is the bare name class.
- `standalone`: only read for a `host` library. A format string with `{name_class}` (the formatted `class`). It is what
  a standalone call site (`{% cv_icon %}`) puts on the `<i>` element. Default `"{name_class}"`.

The maintainer chose this placement for the standalone base class (option B) over a class-table slot
`icon:standalone` (it would make the icon module read the button class table and put a non-button key into the
button table) and over a separate `host_class` key next to an unchanged `class` (it departs from the issue's
`placement` API and repeats the name pattern).

`register_icon_library` takes `class` only through the dict form (as documented in `icons.md` today); the issue's
`class_=` sketch is not adopted, no API change.

### Class table

Four new slots, all defaulting to `"{name_class}"`:

```python
"context:icon-host": "{name_class}",
"list:icon-host": "{name_class}",
"card:icon-host": "{name_class}",
"menu:icon-host": "{name_class}",
```

A theme or project can set e.g. `"card:icon-host": "icon {name_class}"`. The mode markers stay where they are:

```python
CRUD_VIEWS_BUTTON_CLASSES = {
    "context:secondary:both": "btn btn-with-icon",
    "context:secondary:icon": "btn btn-icon-only",
}
```

These slots are read with `get_button_class(location, "icon-host")` and then formatted with `name_class=…`. They
need entries in `DEFAULT_BUTTON_CLASSES` so W362 accepts them.

### Resulting HTML

```html
<!-- standalone, e.g. an alert -->
<i class="icon icon-check me-2" aria-hidden="true"></i>
<!-- context button, icon mode -->
<a href="…" class="btn btn-icon-only icon-edit" title="Edit" data-cv-tooltip="context" cv-key="update"><span class="visually-hidden">Edit</span></a>
<!-- context button, both mode -->
<a href="…" class="btn btn-with-icon icon-plus" cv-key="create"><span>New item</span></a>
<!-- menu item -->
<a href="…" class="dropdown-item icon-edit" cv-key="update"> Edit</a>
```

(Exact whitespace inside the menu item follows `menu_item_label.html`; the builder keeps whatever the template
yields without the icon, but must not leave a stray leading space that differs between modes for no reason.)

## Calls made while writing this up (check these)

These were settled by the author, not by the maintainer:

- **`label` mode shows no icon, also for a host icon.** `cv_button_data` sets `cv_icon_class = ""` when the label mode
  is `label`, exactly as the element icon is not rendered in `label` mode today. A design system that wants a marker
  on text-only buttons uses the `*:label` mode slot.
- **Filter toggle with mixed placements:** host rendering is used only when both `filter` and `filter-close` resolve
  to host icons. Otherwise the button renders today's two spans (each `{% cv_icon %}` then renders its standalone form)
  and the JS takes the span path.
- **An `*:icon-host` slot set to `None` or `""`** switches the icon off at that location: no class on the host and no
  inline icon. This matches the existing convention that `None` in `CRUD_VIEWS_ICONS` or in a mode key switches a
  thing off. It is valid for the check, and `buttons.md` documents it.
- **The menu toggle** is in scope although the issue does not name it (see "Scope").
- `actions_menu_item_label.html` (legacy) stays unchanged.

## How it works (decided)

### Icon module (`crud_views/lib/icons.py`)

- A helper, e.g. `resolve_icon_host_class(value) -> str | None`: resolves `value` like `render_icon` does and returns
  the formatted name class when the resolved library is a `font` library with `placement == "host"`, else `None`
  (element placement, raw class, unknown prefix, empty value).
- `font_renderer` for a host library formats `standalone` with `name_class` and renders that on the `<i>`
  (`css` appended as today). For an element library it is unchanged.
- An unusable `standalone` (not a str, bad format string) renders nothing, like an unusable `class` today; the check
  reports it.

### Leaf contract (`crud_views/lib/view/button_data.py`)

`cv_button_data()` gains two leaf keys (and `LEAF_KEYS` lists them):

- `cv_icon_class`: `get_button_class(location, "icon-host").format(name_class=…)` for a host icon, else `""`.
- `cv_icon_inline`: `False` for a host icon, else `True`.

For an icon that is `None`/empty, `cv_icon_class` is `""` and `cv_icon_inline` is `True` (the leaf's existing
`{% if cv_icon %}` handling stays). An unusable `icon-host` format string yields `""` (check reports it).

The menu-item leaf uses `menu` as its location for `icon-host`, regardless of the leaf's `cv_location`.

### Templates

- `action.html`: `{% if cv_icon_class %} {{ cv_icon_class }}{% endif %}` appended inside `class="…"`; the icon and the
  space after it render only when `cv_icon_inline`.
- `menu_item.html` / `menu_item_label.html`: same pattern with the `menu` host class; no `cv-icon-fw` placeholder when
  the icon is hosted.
- `actions_menu_toggle.html`: its context (`cv_actions_menu`) gets the host class for `cv_menu_icon` at
  `cv_location`, through the new template tag or a context key; the inner `{% cv_icon %}` renders only for an inline
  icon.
- `context_action_filter.html`: in host placement the button carries the current state's class in `class="…"`,
  plus `data-cv-filter-icon-open="<class>"` and `data-cv-filter-icon-close="<class>"`, and renders no icon spans. In
  element placement it is unchanged.

### Template tag

`{% cv_icon_class value location %}` returns the host class string for `value` at `location` (the formatted
`location:icon-host` slot), or `""` when the icon is not a host icon. Theme and project templates use it to do the
same as the leaves outside them. The bundled templates that are not leaves (menu toggle, filter toggle) use it too.

### Filter toggle JS (`list.filter.js`)

After toggling `aria-expanded`, when the button has `data-cv-filter-icon-open`, remove the old state's classes and
add the new state's classes on the button (split on whitespace; both values may hold several classes). Otherwise the
existing span toggle runs. A vitest case covers the host path next to the existing one.

## System checks

Extend `_library_check_messages` (same ids as today's library errors, E354 / E355):

- `placement` other than `"element"` / `"host"` → error.
- `placement: "host"` with a renderer other than `"font"` → error.
- `standalone` not a str, or not a valid format string with `{name_class}` as its only placeholder → error.

Extend `button_class_check_messages`: an `*:icon-host` value that is not a valid format string with `{name_class}` as
its only placeholder → error (builder picks the id next to E361).

## Docs and changelog

- `docs/reference/icons.md`: a "Host placement" section with the library keys, the HTML it yields, the standalone
  base class, the `{% cv_icon_class %}` tag and the filter toggle behaviour.
- `docs/reference/buttons.md`: the four `*:icon-host` slots in the key list, with the `btn-with-icon` /
  `btn-icon-only` example.
- `docs/reference/theme.md`: one paragraph on registering a host library plus the slots from a theme.
- `docs/reference/action_menus.md`: the menu item and menu toggle in host placement (`menu:icon-host`), in the
  section on the menu leaves.
- `docs/reference/javascript.md`: the class swap on the filter toggle and
  its two `data-cv-filter-icon-*` attributes.
- Leaf contract tables (in `buttons.md`): the two new keys `cv_icon_class` and `cv_icon_inline`.
- `docs/migrating-1.0.md` (maintainer's request, although the change is not breaking). It is the upgrade guide for
  themes, and a theme that copied a leaf only to put the icon class on the button can delete that copy now:
  - "Templates to delete": copies of `tags/button/action.html`, `tags/button/menu_item.html`,
    `tags/actions_menu_toggle.html` or `tags/context_action_filter.html` made only to put the icon class on the
    button. Register the library with `placement: "host"` instead (link to the new icons section).
  - "Hooks instead of copies", the **Icons** bullet: 1.0 adds `placement` and `standalone` to the library config
    (#258); the **Button classes** bullet: the `*:icon-host` slots.
  - "Contract changes in templates you still override": a leaf copy that should honour host placement adds
    `{{ cv_icon_class }}` to `class` and renders `{% cv_icon cv_icon %}` only when `cv_icon_inline`; a filter-toggle
    copy takes over the `data-cv-filter-icon-open` / `-close` attributes for host libraries.
- `CHANGELOG.md`: `### Added` entry (not `### Breaking`).
- Do not name downstream or client projects anywhere (generic "a design system" only).

## Tests

- Goldens: every existing leaf golden is unchanged.
- New leaf tests with a host library registered via settings: `action.html` in all three label modes and locations,
  a disabled button, a button without icon, a mixed page where one button uses a `fas:` icon (stays inline);
  `menu_item.html`; the menu toggle; the filter toggle in both states.
- `cv_button_data` unit tests for the two new keys, including a configured `icon-host` slot with a base class.
- `render_icon` for a host library with and without `standalone`.
- `{% cv_icon_class %}` tag.
- Checks: each new error.
- JS: `list.filter.test.js` host-class swap (run with Node 22, see project memory).

## Left to the builder

- Helper and variable names, and whether the leaves compute the host class in `cv_button_data` or via the tag (the
  leaf contract keys above are decided; how they are filled is not).
- Whether the menu toggle gets its class from a context key in `cv_actions_menu` or from `{% cv_icon_class %}` in the
  template.
- Example project: whether to add a small demo of a host library (CSS `::before` with a couple of icons). Nice to
  have, not required.
