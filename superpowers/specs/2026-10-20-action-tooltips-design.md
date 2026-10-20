# Design: Tooltips on stock buttons through `cv.adapters.tooltip`

Issue: [#202](https://github.com/jacob-consulting/django-crud-views/issues/202)

## Why

Since #201 the stock button leaves render icon-only buttons with a plain `title` but without `data-cv-tooltip`.
`tooltip.js` only initialises `[data-cv-tooltip]`, so `cv.adapters.tooltip` never reaches toolbar, list-row and
icon-only card buttons, the filter toggle, the card-order toggles or the formset controls. A downstream theme (the
Tabler prototype `crud_views_tabler` is the first) that wires a real tooltip implementation through the adapter still
gets only the browser's native tooltip, and has to override leaves just to add the marker, which is what #201 set out
to make unnecessary.

The maintainer's goal for this change: **multiple tooltip drivers, maximum flexibility in downstream themes.** The stock
markup must not assume any tooltip library. A theme should get rich tooltips, with per-location behaviour such as
placement, by configuring the adapter and nothing else: no template overrides.

## Goals

- Every stock icon-only trigger carries a `data-cv-tooltip` marker whose **value names its location**, and keeps its
  text in `title`.
- `tooltip.js` passes the location to the adapter, so adapters never parse the marker themselves.
- `cv.bootstrapAdapters(ns, options)` takes an optional tooltip options function, so any Bootstrap-compatible theme
  (Bootstrap, Tabler, ...) can set per-location Bootstrap Tooltip config in one line.
- An optional `dispose(root)` on the tooltip adapter, called by core before modal content is replaced, so a tooltip
  showing at that moment does not stay stuck on the page.
- An optional `hide(el)` on the tooltip adapter, called by core on the button that opened a modal just before the
  modal shows, so that button's tooltip does not float over the open modal (tooltips stack above modals). The button
  keeps its tooltip for later.
- A documented recipe for a non-Bootstrap driver (Tippy-style).

## Non-goals

- Tooltips on dropdown menu items (`tags/button/menu_item.html` stays unchanged; tooltips on menu items are noise).
- The "More actions" dropdown toggle (`tags/actions_menu_toggle.html`). It carries `data-bs-toggle="dropdown"`, and
  Bootstrap cannot put a Tooltip and a Dropdown on the same element; including it would need a wrapper element, a markup
  change for themes. It keeps its `aria-label` and gets no `title` or marker. (Designer's call.)
- Tooltips on labelled card buttons (the label is visible; no `cv_title`, so no marker).
- Tooltips on disabled buttons. Bootstrap sets `pointer-events: none` on `.btn:disabled`, so neither the native `title`
  nor a tooltip shows on hover. Not a regression; the documented workaround (a wrapper element) changes leaf markup.
  Recorded as a known limitation in `docs/reference/inaccessible_actions.md`.
- A setting to turn tooltips on or off (option B in the issue was rejected).
- Placement or any other library-specific attribute (`data-bs-placement`, `data-bs-title`, ...) in stock markup. That
  belongs in the adapter.
- Calling `dispose` when the modal hides. Core only sees the dismiss-button path; Escape and backdrop clicks go
  straight to the UI library, and Bootstrap's Tooltip already hides itself on `hide.bs.modal`.

## Anti-goals (would make this a failure even if it works)

- Stock markup that only works with Bootstrap (e.g. text only in `data-bs-title`).
- Breaking existing custom adapters that implement only `init(el)`.
- Labelled card buttons or menu items gaining tooltips.

## Decisions

### 1. Behaviour change: on by default (issue option A)

With the marker in place and the default adapters (`cv.bootstrapAdapters(globalThis.bootstrap)`), a stock Bootstrap 5
project that loads `bootstrap.bundle` gets Bootstrap tooltips on every marked button instead of the native `title`
tooltip. Tooltips stay opt-in at the JS level: no Tooltip component on the namespace, no tooltip; the native `title`
remains the fallback. A project that wants native tooltips sets `cv.adapters.tooltip = {init() {}}`. CHANGELOG notes
this under the DOM changes, with the opt-out line.

### 2. Marker values

The marker's value is the location. Text always lives in `title`.

| Template | Element | Marker | Condition |
|---|---|---|---|
| `tags/button/action.html` | context, list, card action buttons | `data-cv-tooltip="{{ cv_location }}"` (`context` / `list` / `card`) | exactly when `cv_title` is set (same `{% if %}` as `title`) |
| `tags/context_action_filter.html` | filter toggle | `data-cv-tooltip="filter"` | always (next to existing `title`) |
| `snippets/card_order.html` | ascending / descending toggles | `data-cv-tooltip="card-order"` | always (next to existing `title`) |
| `formsets/control.html` | up / down / add / delete controls | `data-cv-tooltip="formset"` | always |
| `crud_views_object_detail/.../card-rows/property.html` | property detail button | `data-cv-tooltip="object-detail"` | unchanged condition |
| `tags/button/menu_item.html` | menu item | none | unchanged |

Further changes in the same templates:

- `formsets/control.html`: `title` becomes the translated text `aria-label` already carries (`Move up`, `Move down`,
  `Add row`, `Delete row`), replacing the untranslated lowercase `up` / `down` / `add` / `delete`.
- `property.html`: `data-bs-title="{{ prop.detail }}"` is replaced by `title="{{ prop.detail }}"` (driver-neutral).
  `aria-label` stays.

A bare `data-cv-tooltip` (empty value) remains valid: `tooltip.js` selects on the attribute's presence, and the
location is then `""`. App or theme templates that already use the bare marker keep working.

The `cv_location` values come from the leaf contract (`crud_views/lib/view/button_data.py`); no new leaf key is added.

### 3. `tooltip.js`

- `initTooltips(root)` calls `tooltip.init(el, {location: el.getAttribute("data-cv-tooltip") || ""})` for every
  `[data-cv-tooltip]` under `root`. The second argument is an object (not a string) so fields can be added later
  without another signature change. Adapters written for `init(el)` keep working.
- New `disposeTooltips(root)`: if `cv.adapters.tooltip.dispose` is a function, calls `tooltip.dispose(root)`; otherwise
  does nothing. Exposed as `cv.disposeTooltips` next to `cv.initTooltips`.
- New `hideTooltip(el)`: if `el` has `data-cv-tooltip` and `cv.adapters.tooltip.hide` is a function, calls
  `tooltip.hide(el)`; otherwise does nothing. Exposed as `cv.hideTooltip`.
- `data-cv-tooltip` is a public, documented contract (themes and app templates already use it). `tooltip.js` uses it
  to find triggers; the default Bootstrap `dispose(root)` in `adapters.js` and custom adapters may select on it too.
  `modal.js` does not touch it. (Designer's call: no shared selector constant.)

### 4. Adapter contract (`cv.adapters.tooltip`)

| Method | Required | Called by core when |
|---|---|---|
| `init(el, {location})` | yes | for every `[data-cv-tooltip]` under a root: page load, `cv:modal:loaded`, `cv:formset:row-added` |
| `dispose(root)` | no | before modal content under `root` is replaced; skipped when the adapter has no `dispose` |
| `hide(el)` | no | on a marked modal trigger, just before the modal is shown; skipped when the adapter has no `hide`. Must leave the tooltip usable afterwards (hide, not destroy) |

`dispose` takes a **root**, not an element: the adapter decides which of its instances live under it. (The Bootstrap
default walks `[data-cv-tooltip]` under the root.)

### 5. `cv.bootstrapAdapters(ns, options)`

- New optional second argument `options`, an object. This change defines one key: `options.tooltip`, a function
  `(el, {location}) => config`. Its return value is passed as the config to `Tooltip.getOrCreateInstance(el, config)`.
  Without it, no config is passed (today's behaviour). A function, not a lookup table: one form covers every case.
- Default tooltip `init(el, ctx)`: `component(ns, "Tooltip")?.getOrCreateInstance(el, options.tooltip?.(el, ctx))`.
  Still does nothing without `Tooltip`.
- Default tooltip `dispose(root)`: for every `[data-cv-tooltip]` under `root`, `Tooltip.getInstance(el)?.dispose()`.
  Does nothing without `Tooltip`. Bootstrap's `dispose()` removes a showing tooltip's element from the page.
- Default tooltip `hide(el)`: `Tooltip.getInstance(el)?.hide()`. Does nothing without `Tooltip` or without an instance.
- The default `cv.adapters` stays `cv.bootstrapAdapters(() => globalThis.bootstrap)` (no options).

Example a theme can now write:

```javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler, {
    tooltip: (el, {location}) => (location === "context" ? {placement: "bottom"} : {}),
}));
```

### 6. `modal.js`

`cvModalInject(html)` calls `cv.disposeTooltips?.(els.content)` before `els.content.innerHTML = html`. This covers
both a modal opening (old content from a previous modal) and a 422 re-render of a modal form. `modal.js` does not touch
the marker or the adapter directly.

The click handler passes the trigger element into `cvModalOpen(url, size, trigger)`. After a successful fetch, just
before `cv.adapters.modal.show(els.modal)`, `cvModalOpen` calls `cv.hideTooltip?.(trigger)` (guarded like
`disposeTooltips`). On the fallback paths (non-OK response, fetch error) the page navigates, so no hide is needed. `cv.disposeTooltips` is guarded with `?.` because `tooltip.js` loads after
`modal.js` and pages may omit it.

### 7. Formset rows

No dispose hook for formsets. New rows are server-rendered and inserted (not cloned from an initialised template), and
`cv:formset:row-added` already re-runs `initTooltips` on them, so `title` survives and new rows get tooltips.

## Tests

Python (pytest):

- Golden HTML under `tests/test1/golden/action_menus/*` updated for the new attribute (only additions on icon-only
  buttons; labelled card buttons and menu items unchanged).
- A test asserting the action leaf emits `data-cv-tooltip="<location>"` exactly when `cv_title` is set, for each of
  `context`, `list`, `card`, and not for a labelled card button.
- Filter toggle, card-order toggles and formset controls carry the marker with the right value; formset control
  `title`s are the translated strings.
- Object-detail property button carries `title` and `data-cv-tooltip="object-detail"` and no `data-bs-title`.

JavaScript (vitest, `tests/js/`):

- `tooltip.test.js`: `init` receives `{location}` from the marker value; `""` for a bare marker; `disposeTooltips` calls
  `dispose(root)` when present and is a no-op when the adapter has no `dispose`; `hideTooltip` calls `hide(el)` for a
  marked element, and is a no-op for an unmarked element or an adapter without `hide`.
- `adapters.test.js`: `bootstrapAdapters(ns, {tooltip})` passes the function's return value to
  `getOrCreateInstance(el, config)` with `(el, {location})`; without options no config is passed; default `dispose`
  calls `getInstance(el)?.dispose()` for markers under the root; default `hide` calls `getInstance(el)?.hide()`; all are
  no-ops without `Tooltip`.
- `modal.test.js`: `disposeTooltips` is called with the content element before its HTML is replaced, on open and on a
  422 re-render; injection still works when `cv.disposeTooltips` is undefined; `hideTooltip` is called with the
  clicked trigger before `modal.show`, and opening still works when `cv.hideTooltip` is undefined.

## Docs

- `docs/reference/buttons.md`: the theme recipe's leaf keeps `data-cv-tooltip="{{ cv_location }}"` next to `title`
  inside the `{% if cv_title %}`; the leaf contract row for `cv_title` mentions the marker.
- `docs/reference/javascript.md`: adapter table gets `init(el, {location})`, `dispose(root)` and `hide(el)`; a section on the
  `cv.bootstrapAdapters(ns, options)` tooltip hook with the placement example; a non-Bootstrap recipe (Tippy-style:
  read `title`, remove it so the native tooltip does not show too, create the tooltip; `hide` hides the instance on the element; `dispose` destroys instances
  under the root) next to "A non-Bootstrap modal"; the list of marker location values.
- `docs/reference/inaccessible_actions.md`: disabled buttons do not show tooltips (Bootstrap `pointer-events: none`),
  with the wrapper-element workaround as a theme concern.
- `CHANGELOG.md`: DOM changes (marker on stock buttons, formset titles translated, `data-bs-title` → `title` on the
  property-detail button), the on-by-default behaviour change with the opt-out line, and the new adapter API
  (`init` context, `dispose`, `hide`, `bootstrapAdapters` options).

## Left to the builder

- Exact test file placement for the Python tests and whether to extend existing golden fixtures or add new ones.
- Wording and placement of the docs sections, following the existing style of each page.
- Whether `.po` catalogues need regenerating for the formset strings (they already exist as `aria-label` translations,
  so probably not).

## Calls made by the designer (not discussed with the maintainer)

- Marker value `filter` for the filter toggle (its button-class location is `context`) and `object-detail` for the
  property-detail button.
- Default `dispose` walks `[data-cv-tooltip]` under the root rather than tracking instances.
- `cv.disposeTooltips` guarded with `?.` in `modal.js`.
- The "More actions" dropdown toggle is excluded (see non-goals).
- `cv.hideTooltip` checks the marker itself, so `modal.js` can pass any trigger without knowing about tooltips.
- The marker selector is hard-coded where needed (`tooltip.js`, the Bootstrap `dispose`); no shared constant.
