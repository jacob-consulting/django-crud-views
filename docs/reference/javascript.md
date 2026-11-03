# JavaScript

crud_views ships a handful of classic scripts (no modules, no build step, no inline code, so they work under a strict
CSP). Core pages need **neither jQuery nor a global named `bootstrap`**: every call into a UI library goes through
a small adapter object on `cv.adapters`, pre-filled with a Bootstrap 5 default.

## What the scripts need

The scripts render in this order from `{% cv_js %}` (and `cv_sources("js")` for django-pipeline):

| Script | Needs at load | Needs at use |
|---|---|---|
| `adapters.js` | nothing | nothing |
| `viewset.js` | nothing | `cv.adapters.alert`, when an alert's close control is clicked, see [Dismissible alerts](#dismissible-alerts) |
| `formset.js` | nothing | jQuery, on pages with formsets |
| `list.filter.js` | nothing | `cvGetConfig`, `cv.adapters.collapse` |
| `modal.js` | nothing | `cv.adapters.modal` |
| `toggle.js` | nothing | nothing |
| `tooltip.js` | nothing | `cv.adapters.tooltip` (does nothing without it) |

Bootstrap's bundle may load anywhere on the page for the default adapters (the namespace is resolved when an adapter is
called, not when the script loads); it still has to be present for Bootstrap's own data-API components. jQuery is
needed only on pages with formsets and by jQuery-based extensions, see [jQuery](#jquery).

## `cv.adapters`

`adapters.js` defines `cv.adapters`. Core calls adapters only through `cv.adapters.<name>`, looked up at call time, so an
assignment at any point before the user acts takes effect.

| Adapter | Method | Called by core when | Bootstrap default |
|---|---|---|---|
| `modal` | `show(modalEl)` | the partial is injected | `Modal.getOrCreateInstance(modalEl).show()`; throws a clear error when the namespace has no `Modal` |
| `modal` | `hide(modalEl)` | a `[data-cv-modal-dismiss]` element inside the shell is clicked | `Modal.getInstance(modalEl)?.hide()` |
| `modal` | `setSize(dialogEl, size)` | before `show`, with the view's `cv_modal_size` token | ensures `modal-dialog` and swaps the size class: `modal-sm` / `modal-lg` / `modal-xl` for `sm` / `lg` / `xl`; `""` and unknown tokens remove it. Other classes on the dialog (a shell override's `modal-dialog-centered`) are kept |
| `tooltip` | `init(el, {location})` | for every `[data-cv-tooltip]` under a root: page load, `cv:modal:loaded`, `cv:formset:row-added`; `location` is the marker's value, see [Tooltips](#tooltips) | `Tooltip.getOrCreateInstance(el)` (the context is ignored); does nothing without `Tooltip` |
| `tooltip` | `hide(el)` (optional) | a click lands on or inside a `[data-cv-tooltip]`, see [Tooltips](#tooltips) | `Tooltip.getInstance(el)?.hide()`; does nothing without `Tooltip` or without an instance |
| `tooltip` | `dispose(el)` (optional) | for every `[data-cv-tooltip]` under `#cv-modal` on `cv:modal:unload`, before the content is replaced | `Tooltip.getInstance(el)?.dispose()`; does nothing without `Tooltip` or without an instance |
| `collapse` | `toggle(el)` | the filter toggle button is clicked, with `#filter-collapse` | `Collapse.getOrCreateInstance(el).toggle()`; throws a clear error when the namespace has no `Collapse`; returns `false` without toggling while the panel is still animating (`.collapsing`), because Bootstrap ignores a toggle then |
| `alert` | `close(el)` | a click lands on or inside a `[data-cv-alert-dismiss]` element, with its nearest `role="alert"` ancestor, see [Dismissible alerts](#dismissible-alerts) | `Alert.getOrCreateInstance(el).close()`; removes `el` from the page when the namespace has no `Alert` |

A failing `modal.show` is logged with `console.error` and the modal flow falls back to opening the full page. A
`collapse.toggle` that throws or returns exactly `false` leaves the filter toggle's icon, `aria-expanded` and persisted
state untouched; any other return value counts as toggled, so a custom adapter may simply return nothing. An
`alert.close` that throws is not caught, see [Dismissible alerts](#dismissible-alerts).

Replace an adapter from any script that loads after core:

```javascript
cv.adapters.tooltip = {init(el, {location}) { /* your tooltip library */ }};
```

Adapters assigned **before** `adapters.js` loads are kept, so a hand-written object may also be set earlier. Create the
namespace first: `globalThis.cv ??= {}; cv.adapters ??= {};`. The merge is
shallow, per adapter: assigning `cv.adapters.modal = {...}` replaces the whole default `modal` adapter, so provide
`show`, `hide` and `setSize` together. Every adapter such an early map leaves out gets its default while
`adapters.js` loads, so a partial map assigned before core needs nothing else.

Replacing the **whole map after** core loads is different: `cv.adapters = {...}` discards the defaults, and core never
fills them in again. Such a map must provide every adapter core calls, `alert` with `close(el)` included; without it,
a click on an alert's close control throws a `TypeError` and the alert stays. Prefer replacing single entries
(`cv.adapters.modal = {...}`) or merging into the existing map (`Object.assign(cv.adapters, {...})`). A theme that
builds its own map for a Bootstrap-compatible namespace takes the alert entry from the factory:

```javascript
cv.adapters = {
    modal: myModalAdapter,
    tooltip: myTooltipAdapter,
    collapse: myCollapseAdapter,
    alert: cv.bootstrapAdapters(() => globalThis.tabler).alert,
};
```

## Bootstrap under another name

`cv.bootstrapAdapters(ns)` builds all four adapters for any Bootstrap-compatible namespace. `ns` is an object or a
function returning one; a function is resolved on every call, so load order does not matter.

**Tabler** exposes Bootstrap's components as `window.tabler`. Register one small script as an asset (loaded after core,
see [Assets](assets.md)) containing:

```javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
```

**ES modules / bundlers** have no global at all. In your bundle entry point:

```javascript
import * as bootstrap from "bootstrap";

Object.assign(cv.adapters, cv.bootstrapAdapters(bootstrap));
```

## Tooltips

`tooltip.js` initialises every element marked `data-cv-tooltip` through `cv.adapters.tooltip.init(el, {location})`,
on page load, after `cv:modal:loaded` and after `cv:formset:row-added`. The tooltip text is the element's `title`;
the marker's value names where the trigger sits:

| `location` | Trigger |
|---|---|
| `context` | icon-only context toolbar buttons, the filter toggle included (in `"icon"` mode only) |
| `list` | list row buttons |
| `card` | icon-only card buttons (a card button with a visible label has no marker) |
| `card-order` | the ascending / descending toggles of the card ordering bar |
| `formset` | the formset row controls (move up, move down, add, delete) |
| `object-detail` | the property-detail button of `crud_views_object_detail` |
| `form` | icon-only crispy form buttons (in `"icon"` mode only, see [Forms](buttons.md#forms)) |
| `""` | a bare `data-cv-tooltip` in your own templates |

Menu items and the `⋯` toggle carry no marker. With Bootstrap's JavaScript loaded, the default adapter turns every
marked `title` into a Bootstrap tooltip. To keep the browser's native tooltips instead:

```javascript
cv.adapters.tooltip = {init() {}};
```

For markup you inject yourself, call `cv.initTooltips(root)` on the inserted element.

Two optional lifecycle methods complete the adapter. A click on a trigger (with the mouse, or Enter / Space on a
focused one) calls `hide(el)`, and the tooltip stays hidden until the next hover or focus; without it Bootstrap keeps
the tooltip up for as long as the clicked button has focus. Before the modal's content is replaced, `cv:modal:unload`
calls `dispose(el)` on every marker under `#cv-modal`, so Bootstrap's per-tooltip modal handlers and instances do not
accumulate over repeated opens. An adapter without `hide` or `dispose` is simply not called for that step: the
native-tooltip opt-out above stays a no-op throughout, and the per-location recipe below keeps both Bootstrap defaults
because it replaces only `init`. For marked markup you remove yourself, call `cv.adapters.tooltip.dispose?.(el)` first.

Per-location configuration needs no package API: build the adapters, then replace `init` on the tooltip adapter. The
merge into `cv.adapters` is per adapter, so the reassignment is the whole customisation. Tooltips below the context
toolbar, for Tabler:

```javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
cv.adapters.tooltip.init = (el, {location} = {}) =>
    globalThis.tabler.Tooltip.getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"});
```

An adapter written as `init(el)` keeps working; the context is an extra argument.

## A non-Bootstrap modal

To use a native `<dialog>`, override the shell template `crud_views/modal/shell.html`. The three ids
`cv-modal`, `cv-modal-dialog` and `cv-modal-content` are the contract, core finds the shell through them:

```html
<dialog id="cv-modal">
    <div id="cv-modal-dialog">
        <div id="cv-modal-content"></div>
    </div>
</dialog>
```

Then assign the modal adapter in a script loaded after core:

```javascript
cv.adapters.modal = {
    show(modalEl) { modalEl.showModal(); },
    hide(modalEl) { modalEl.close(); },
    setSize(dialogEl, size) { dialogEl.dataset.size = size; },
};
```

The partial's close button carries `data-cv-modal-dismiss`, which calls `hide`. See [Modals](modals.md) for the
partial and the size tokens.

## A non-Bootstrap tooltip

The stock markup carries only `title` and the marker, so any tooltip library fits. Read the text from `title` and
remove the attribute, otherwise the browser shows its native tooltip as well (Bootstrap does the same internally). With
a Tippy-style library:

```javascript
cv.adapters.tooltip = {
    init(el, {location} = {}) {
        const text = el.getAttribute("title");
        if (!text) {
            return; // already initialised, or nothing to show
        }
        el.removeAttribute("title");
        tippy(el, {content: text, placement: location === "context" ? "bottom" : "top"});
    },
    hide(el) { el._tippy?.hide(); },
    dispose(el) { el._tippy?.destroy(); },
};
```

`hide` and `dispose` are optional; leave them out and core skips those steps. A hidden label
(`<location>:hidden-label`) or an `aria-label` on every stock trigger keeps the accessible name once `title` is gone.

## Dismissible alerts

The close control of a dismissible alert ([flash messages](messages.md) and `{% cv_alert ... dismissible=True %}`)
carries `data-cv-alert-dismiss`, and the alert frame carries `role="alert"`. `viewset.js` handles every such control
through one delegated `click` listener on `document`. A click on or inside a marked control finds the control's
nearest `role="alert"` ancestor and calls `cv.adapters.alert.close(frame)`, looking the adapter up at the time of the
click. Alerts inserted after page load, modal content included, therefore close without any initialisation, and an
adapter replaced at any point before the click takes effect. A marked control with no `role="alert"` ancestor is
ignored. Classes play no part, so a [custom frame](theme.md#custom-alert-frame) keeps working as long as it keeps both
hooks.

The default adapter closes the frame with Bootstrap's `Alert` component, transition included, when the namespace has
one. Only when there is no `Alert` (no Bootstrap JavaScript, or a build without the component) does it remove the frame
itself with `el.remove()`. That removal belongs to the default adapter alone; core has no second closing path:

- An error thrown by a present `Alert` component, or by your own adapter, is not caught. It surfaces as an uncaught
  error of the click; core does not log it, does not remove the frame and does not undo what the adapter already
  changed.
- An adapter that does nothing leaves the alert on the page.
- A missing `cv.adapters.alert` is not repaired: the click throws a `TypeError` (see the whole-map note under
  [`cv.adapters`](#cvadapters)).

A theme closes alerts its own way by replacing the entry from a script loaded after core:

```javascript
cv.adapters.alert = {
    close(el) {
        el.classList.add("is-leaving");
        el.addEventListener("transitionend", () => el.remove(), {once: true});
    },
};
```

## jQuery

Core scripts do not use jQuery, except `formset.js`. Pages with formsets need jQuery loaded by `DOMContentLoaded`
(before or after `{% cv_js %}`); without it `formset.js` logs one `console.error` naming jQuery. jQuery-based
extensions (the datetimepicker and typeahead apps) document their own requirement. The asset registry does not manage
jQuery, see [Assets](assets.md).

## Events

All three are bubbling `CustomEvent`s you can listen for on `document`:

| Event | Dispatched on | When |
|---|---|---|
| `cv:modal:unload` | `#cv-modal` | before every content replacement in the modal, while the previous content is still attached, see [Modals](modals.md#extending) |
| `cv:modal:loaded` | `#cv-modal` | after every content injection into the modal, see [Modals](modals.md#extending) |
| `cv:formset:row-added` | the new `div.cv-formset-row` | after a formset row was inserted, see [Formsets](formsets.md#initializing-widgets-in-added-rows) |

## The filter toggle contract

`list.filter.js` drives the element with id `filter-collapse` from the button `#cv-filter-toggle`, like the modal shell
ids this id is a contract. A project or theme overriding `crud_views/tags/context_action_filter.html` should render the
toggle with `aria-expanded` and `aria-controls="filter-collapse"`. Without `aria-expanded` the script falls back to the
panel's visibility (`hidden` or computed `display: none`) to decide the state it persists, then writes `aria-expanded`
back.

The script collapses first: a `cv.adapters.collapse.toggle` that throws or returns `false` changes nothing, neither
`aria-expanded`, nor the icon, nor the persisted state. After a successful toggle it updates `aria-expanded` and the
icon, then posts the new state; a failed request does not undo the toggle. The reset button `#filter-button-reset`
is unaffected by the label mode.

Icons are optional. The button follows its resolved [label mode](context_buttons.md#the-filter-toggle), which decides
whether it has an icon at all, and the icon switch has two forms:

- **Element icons:** the button holds two spans, `[data-cv-filter-icon="open"]` and `[data-cv-filter-icon="close"]`,
  and the script flips their `hidden` attributes.
- **Host icons:** with a [host-placed](icons.md#host-placement) icon library the button carries
  `data-cv-filter-icon-open` and `data-cv-filter-icon-close` (each a class string) and the current state's classes in
  `class`; the script removes one and adds the other. The presence of `data-cv-filter-icon-open` picks this form.

The stock template uses host icons only when both `filter` and `filter-close` resolve to usable host classes at
`context`. Any other combination (one host icon and one element icon, or `context:icon-host` switched off) renders the
two element spans, in `"icon"` and `"both"` mode alike. In `"label"` mode the button has neither form: no spans, no
host classes and no `data-cv-filter-icon-*` attributes, and the script only toggles the panel, updates
`aria-expanded` and persists the state.

The label never changes with the state. In `"icon"` mode it is visually hidden text, the `title` and the tooltip
(the button carries `data-cv-tooltip="context"`); in `"both"` and `"label"` mode it is visible text with no `title` and
no tooltip marker. The default `Filter` label and custom labels alike stay constant; a label is never an icon hook,
so keep `data-cv-filter-icon` attributes out of custom label markup. A template override owns its markup: it may
render either icon form or none, as long as it keeps the ids and ARIA attributes above.
