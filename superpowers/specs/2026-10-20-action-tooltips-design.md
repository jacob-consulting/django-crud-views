# Design: Tooltips on stock buttons through `cv.adapters.tooltip`

Issue: [#202](https://github.com/jacob-consulting/django-crud-views/issues/202)

Revised 2026-10-20 after review: scope reduced to the marker, the location context and the docs. The tooltip
lifecycle (dispose before modal injection, hide on click, `bootstrapAdapters` options) moved to a follow-up, see
"Follow-up" at the end.

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
- A documented recipe for per-location Bootstrap config (placement) that needs no package API: reassign
  `cv.adapters.tooltip.init` after `cv.bootstrapAdapters(ns)`.
- A documented recipe for a non-Bootstrap driver (Tippy-style).

## Non-goals

- Tooltips on dropdown menu items (`tags/button/menu_item.html` stays unchanged; tooltips on menu items are noise).
- The "More actions" dropdown toggle (`tags/actions_menu_toggle.html`). Bootstrap's `Data.set` refuses a second
  component instance on one element and logs `Bootstrap doesn't allow more than one instance per element`.
  `tooltip.js` runs at load, so a Tooltip on the toggle would be bound first and every click would hit that refusal
  for the Dropdown. Including it would need a wrapper element, a markup change for themes. It keeps its `aria-label`
  and gets no `title` or marker.
- Tooltips on labelled card buttons (the label is visible; no `cv_title`, so no marker).
- Tooltips on disabled buttons. Bootstrap sets `pointer-events: none` on `.btn:disabled`, so neither the native `title`
  nor a tooltip shows on hover. Not a regression; the documented workaround (a wrapper element) changes leaf markup.
  Recorded as a known limitation in `docs/reference/inaccessible_actions.md`.
- A setting to turn tooltips on or off (option B in the issue was rejected).
- Placement or any other library-specific attribute (`data-bs-placement`, `data-bs-title`, ...) in stock markup. That
  belongs in the adapter.
- **Tooltip lifecycle.** No `dispose`, no `hide`, no options on `cv.bootstrapAdapters`, no change to `modal.js` or
  `adapters.js`. The cases this would address are reasoned from Bootstrap's source and not yet observed; they are
  listed under "Follow-up" with the observations to make first.

## Anti-goals (would make this a failure even if it works)

- Stock markup that only works with Bootstrap (e.g. text only in `data-bs-title`).
- Breaking existing custom adapters that implement `init(el)` and ignore a second argument.
- Labelled card buttons or menu items gaining tooltips.

## Decisions

### 1. Behaviour change: on by default (issue option A)

With the marker in place and the default adapters (`cv.bootstrapAdapters(() => globalThis.bootstrap)`), a stock
Bootstrap 5 project that loads `bootstrap.bundle` gets Bootstrap tooltips on every marked button instead of the native
`title` tooltip. Tooltips stay opt-in at the JS level: no Tooltip component on the namespace, no tooltip; the native
`title` remains the fallback. A project that wants native tooltips sets `cv.adapters.tooltip = {init() {}}`. CHANGELOG
notes this under the DOM changes, with the opt-out line.

Bootstrap's Tooltip moves `title` to `data-bs-original-title` on init and restores it on `dispose()`, so the native
fallback survives either way.

### 2. Marker values

The marker's value is the location. Text always lives in `title`.

| Template | Element | Marker | Condition |
|---|---|---|---|
| `tags/button/action.html` | context, list, card action buttons | `data-cv-tooltip="{{ cv_location }}"` (`context` / `list` / `card`) | exactly when `cv_title` is set (same `{% if %}` as `title`) |
| `tags/context_action_filter.html` | filter toggle | `data-cv-tooltip="context"` | always (next to existing `title`) |
| `snippets/card_order.html` | ascending / descending toggles | `data-cv-tooltip="card-order"` | always (next to existing `title`) |
| `formsets/control.html` | up / down / add / delete controls | `data-cv-tooltip="formset"` | always |
| `crud_views_object_detail/.../card-rows/property.html` | property detail button | `data-cv-tooltip="object-detail"` | unchanged condition |
| `tags/button/menu_item.html` | menu item | none | unchanged |

The filter toggle sits in the context toolbar and takes its classes from the `context:<variant>` row of the class
table, so its marker says `context` too: a theme that places toolbar tooltips by location covers it without a special
case. The other values (`card-order`, `formset`, `object-detail`) are the class-table locations of those buttons.

Further changes in the same templates:

- `formsets/control.html`: `title` becomes the translated text `aria-label` already carries (`Move up`, `Move down`,
  `Add row`, `Delete row`), replacing the untranslated lowercase `up` / `down` / `add` / `delete`. Nothing in
  `formset.js`, the CSS or the tests selects on those `title` values.
- `property.html`: `data-bs-title="{{ prop.detail }}"` is replaced by `title="{{ prop.detail }}"` (driver-neutral).
  `aria-label` stays, so Bootstrap's `_fixTitle` leaves the accessible name alone.

A bare `data-cv-tooltip` (empty value) remains valid: `tooltip.js` selects on the attribute's presence, and the
location is then `""`. App or theme templates that already use the bare marker keep working.

The `cv_location` values come from the leaf contract (`crud_views/lib/view/button_data.py`); no new leaf key is added.

### 3. `tooltip.js`

- `initTooltips(root)` calls `tooltip.init(el, {location: el.getAttribute("data-cv-tooltip") || ""})` for every
  `[data-cv-tooltip]` under `root`. The second argument is an object (not a string) so fields can be added later
  without another signature change. Adapters written for `init(el)` keep working: they ignore the argument.
- Nothing else changes: the same three initialisation points (page load, `cv:modal:loaded`,
  `cv:formset:row-added`), `cv.initTooltips` exposed as today.
- `data-cv-tooltip` is a public, documented contract (themes and app templates already use it).

### 4. Adapter contract (`cv.adapters.tooltip`)

| Method | Required | Called by core when |
|---|---|---|
| `init(el, {location})` | yes | for every `[data-cv-tooltip]` under a root: page load, `cv:modal:loaded`, `cv:formset:row-added` |

The Bootstrap default stays `component(ns, "Tooltip")?.getOrCreateInstance(el)`; the context argument is ignored
there. `adapters.js` does not change.

### 5. Per-location config is a recipe, not an API

`cv.bootstrapAdapters(ns)` keeps its one parameter. A theme that wants per-location Bootstrap config reassigns `init`
on the adapter object the call returned; the merge into `cv.adapters` is per adapter, so the reassignment is the whole
customisation:

```javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
cv.adapters.tooltip.init = (el, {location} = {}) =>
    globalThis.tabler.Tooltip.getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"});
```

Documented in `docs/reference/javascript.md` next to the existing Tabler line. The theme owns the null check on its
own namespace, as it owns the load order of its bundle.

### 6. `modal.js`, `adapters.js`

Unchanged.

### 7. Formset rows

No dispose hook for formsets. New rows are server-rendered and inserted (not cloned from an initialised template), and
`cv:formset:row-added` already re-runs `initTooltips` on them, so `title` survives and new rows get tooltips.

## Tests

Python (pytest):

- Golden HTML under `tests/test1/golden/action_menus/*` updated for the new attribute (only additions on icon-only
  buttons; labelled card buttons and menu items unchanged).
- A test asserting the action leaf emits `data-cv-tooltip="<location>"` exactly when `cv_title` is set, for each of
  `context`, `list`, `card`, and not for a labelled card button.
- Filter toggle (`context`), card-order toggles and formset controls carry the marker with the right value; formset
  control `title`s are the translated strings.
- Object-detail property button carries `title` and `data-cv-tooltip="object-detail"` and no `data-bs-title`.

JavaScript (vitest, `tests/js/`):

- `tooltip.test.js`: `init` receives `{location}` from the marker value; `""` for a bare marker; an adapter written as
  `init(el)` is still called once per marker. Fixture text moves from `data-bs-title` to `title`.

## Docs

- `docs/reference/buttons.md`: the theme recipe's leaf keeps `data-cv-tooltip="{{ cv_location }}"` next to `title`
  inside the `{% if cv_title %}`; the leaf contract row for `cv_title` mentions the marker.
- `docs/reference/javascript.md`: adapter table row `init(el, {location})`; a "Tooltips" section with the marker
  location values, the opt-out line, the per-location recipe of decision 5, and a non-Bootstrap recipe (Tippy-style:
  read `title`, remove it so the native tooltip does not show too, create the tooltip) next to "A non-Bootstrap modal".
- `docs/reference/inaccessible_actions.md`: disabled buttons do not show tooltips (Bootstrap `pointer-events: none`),
  with the wrapper-element workaround as a theme concern.
- `CHANGELOG.md`: DOM changes (marker on stock buttons, formset titles translated, `data-bs-title` → `title` on the
  property-detail button), the on-by-default behaviour change with the opt-out line, and `init(el, {location})`.

## Follow-up: tooltip lifecycle (separate issue, not in this change)

With tooltips on by default, three cases are worth observing in a browser before deciding whether core needs
lifecycle hooks. All three are deductions from Bootstrap 5.3's `tooltip.js` and `dom/data.js`, none has been seen.

1. **Tooltip retained by focus after a mouse click.** Bootstrap's focus trigger sets `_activeTrigger.focus` on
   `focusin` and clears it only on `focusout`; `_leave` returns early while any trigger is active. On browsers that
   focus a button on click, clicking the filter toggle or a formset "Add row" button and moving the mouse away should
   leave the tooltip showing until the user clicks elsewhere. Check: click the filter toggle with the mouse, move away,
   watch whether `.tooltip.show` stays.
2. **Tooltip over an opened modal.** The hover trigger stays active until `mouseleave`. Open a modal from an icon-only
   trigger and hold the mouse still: the tooltip should float above the modal (tooltips stack above modals) until the
   pointer moves and the backdrop takes the hit test. Check how long it lasts in practice.
3. **Instances on replaced modal content.** Bootstrap keeps instances in a `Map` keyed by element, so instances on
   content replaced by `cvModalInject` (open after close, 422 re-render) stay referenced until navigation. Themes
   already put marked buttons inside modal content, so this predates #202. Check memory growth over repeated open and
   cancel cycles if it matters.

Suggested shape if any case is confirmed, kept out of this change deliberately:

- `modal.js` dispatches a bubbling `cv:modal:unload` CustomEvent on `#cv-modal` before `cvModalInject` replaces the
  content, mirroring `cv:modal:loaded`. `tooltip.js` listens and calls `tooltip.dispose?.(event.target)`. `modal.js`
  learns nothing about tooltips, and extensions (datetimepicker, typeahead) get the teardown hook they lack today.
- `tooltip.js` adds one delegated `click` listener and calls `tooltip.hide?.(el)` for any `[data-cv-tooltip]`
  trigger. Bootstrap's `hide()` resets all three active triggers, so the tooltip stays hidden until the next hover or
  focus. This covers cases 1 and 2 alike without touching `modal.js`.
- Both methods optional on the adapter; Bootstrap defaults `Tooltip.getInstance(el)?.dispose()` under the root and
  `Tooltip.getInstance(el)?.hide()`.

## Left to the builder

- Exact test file placement for the Python tests and whether to extend existing golden fixtures or add new ones.
- Wording and placement of the docs sections, following the existing style of each page.
- Whether `.po` catalogues need regenerating for the formset strings (they already exist as `aria-label` translations,
  so probably not).

## Calls made by the designer (not discussed with the maintainer)

- Marker value `object-detail` for the property-detail button.
- The "More actions" dropdown toggle is excluded (see non-goals).
- The marker selector is hard-coded in `tooltip.js`; no shared constant.

## Review record (2026-10-20)

The first draft of this spec added `dispose(root)` and `hide(el)` to the adapter, `cv.disposeTooltips` and
`cv.hideTooltip`, a second parameter on `cv.bootstrapAdapters` and a third on `cvModalOpen`. The review found that
issue #202 asks for the marker and the translated titles only, that per-location config needs no API (decision 5),
and that the lifecycle cases were deduced from source rather than observed. The maintainer chose to ship the marker now
and gate the lifecycle on the observations above. The review also moved the filter toggle's marker from `filter` to
`context` (decision 2) and confirmed the dropdown-toggle reason against Bootstrap's `Data.set`.
