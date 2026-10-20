# Design: Tooltip lifecycle, hide on click and dispose on modal content replacement

Issue: [#203](https://github.com/jacob-consulting/django-crud-views/issues/203)

Follow-up to [#202](2026-10-20-action-tooltips-design.md) ("Follow-up: tooltip lifecycle"). Brainstormed 2026-10-20
with the maintainer; the focus for this change is maintainability, low complexity and easy theming in downstream
projects.

## Why

Since #202 the stock icon-only buttons carry `data-cv-tooltip` and, with Bootstrap's JavaScript loaded, show Bootstrap
tooltips by default. Two lifecycle gaps follow from that.

1. **Confirmed in Chrome 155 (issue #203, case 1).** Click the filter toggle or a formset "Add row" control with the
   mouse and move the pointer away: the tooltip stays. Bootstrap's focus trigger is set on `focusin` and cleared only on
   `focusout`, and `_leave` returns early while any trigger is active, so the tooltip clears only when focus leaves the
   button.
2. **Established from Bootstrap's source (5.3.8, `Tooltip._setListeners` and `Tooltip.dispose`).** Every tooltip
   created inside a modal attaches a `hide.bs.modal` handler on `el.closest(".modal")`; only `dispose()` removes it.
   `#cv-modal` is one persistent element whose content `cvModalInject` replaces on every open and on every 422
   re-render, so each cycle adds one handler per marked button to `#cv-modal` and never removes it. Each handler keeps
   its detached trigger and Tooltip instance alive. The acceptance run's ten cycles were on a delete modal, and
   `view_delete.content.html` renders no marked button (labelled crispy buttons; the shell's close button carries only
   `aria-label`), so that observation says nothing about this case. Modals that do carry markers are the object-detail
   modal (property-detail buttons) and any modal form with a formset (row controls); a page where such modals are
   opened all day grows without bound. The maintainer decided the source evidence is enough and no browser measurement
   is needed.

The modal-trigger case from the #202 follow-up (a tooltip floating over an opened modal) was not reproduced in Chrome.
The click half covers it on any browser where it occurs.

## Goals

- A tooltip hidden by a click stays hidden until the next hover or focus, on every stock trigger, on a normal page and
  inside a modal.
- Tooltip instances inside `#cv-modal` are disposed before their triggers are replaced, so Bootstrap's modal handlers
  and instances do not accumulate.
- A public teardown hook for modal content, the mirror of `cv:modal:loaded`, usable by the extensions
  (datetimepicker, typeahead) and by projects, without `modal.js` learning anything about tooltips.
- Both lifecycle methods are optional on the adapter. An adapter that implements only `init(el, {location})` keeps
  working everywhere; a theme built on `cv.bootstrapAdapters(ns)` gets both for free.

## Non-goals

- Disposing or hiding on modal **hide**. Bootstrap's own `hide.bs.modal` handler hides tooltips when the modal closes;
  the content stays in the DOM until the next injection, where `cv:modal:unload` disposes it.
- Lifecycle hooks for formset rows. `formset.js` only ever adds rows (`cv:formset:row-added`); it never removes one.
- App-owned `[data-bs-toggle="tooltip"]` elements inside modal content. As with `init`, `tooltip.js` touches only
  `[data-cv-tooltip]`; the host application owns its own tooltips.
- New `cv.*` globals (`cv.hideTooltip`, `cv.disposeTooltips`) and new parameters on `cv.bootstrapAdapters(ns)` or
  `cvModalOpen(url, size)`. These were in the first draft of the #202 spec and were cut in its review; nothing here
  needs them.
- Tooltips on disabled buttons, on menu items and on the "More actions" toggle: unchanged from #202.
- Any change to templates, Python code or golden fixtures. This change is JavaScript, tests and docs only.

## Anti-goals (would make this a failure even if it works)

- A custom adapter written as `{init(el) {...}}` throwing on a click or on a modal open.
- `modal.js` importing, selecting or naming tooltips.
- A tooltip that reappears after the click without a new hover or focus (Bootstrap's `hide()` resets all three active
  triggers; a hide that leaves a trigger active would show it again on the next `mouseover`).

## Decisions

### 1. Adapter contract (`cv.adapters.tooltip`)

| Method | Required | Called by core when | Bootstrap default |
|---|---|---|---|
| `init(el, {location})` | yes | for every `[data-cv-tooltip]` under a root: page load, `cv:modal:loaded`, `cv:formset:row-added` | `Tooltip.getOrCreateInstance(el)` (unchanged) |
| `hide(el)` | no | a click lands on or inside a `[data-cv-tooltip]` | `Tooltip.getInstance(el)?.hide()` |
| `dispose(el)` | no | for every `[data-cv-tooltip]` under `#cv-modal` on `cv:modal:unload`, before the content is replaced | `Tooltip.getInstance(el)?.dispose()` |

All three are per-element. `tooltip.js` iterates for `dispose` exactly as it does for `init`, so an adapter author
writes only per-element functions and never a root walker (designer's call; the issue left open which side iterates).
Core calls the optional methods through optional chaining (`tooltip.hide?.(el)`, `tooltip.dispose?.(el)`), so an
adapter without them is a no-op for that step and never an error. The Bootstrap defaults use `getInstance`, not
`getOrCreateInstance`: a trigger that was never initialised (for example because `init` was replaced by a no-op) must
not gain an instance on click or on unload. Both defaults are silent without `Tooltip` on the namespace, like `init`.

### 2. Click half (`tooltip.js`)

One delegated `click` listener on `document`, registered inside the existing `__cvTooltipInit` guard so it is bound once
even if the script loads twice:

- guard `event.target instanceof Element` (as `modal.js` does; text nodes and the document itself are not elements);
- `event.target.closest("[data-cv-tooltip]")`, so a click on the icon inside a button hides the button's tooltip;
- call `tooltip.hide?.(el)` on the current `globalThis.cv?.adapters?.tooltip`, resolved at click time like `init`.

No modifier-key filtering: a Ctrl-click or middle-click on a list-row link opens a new tab and should hide the tooltip
just the same (designer's call). Keyboard activation (Enter or Space on a focused button) synthesises a `click` and
hides the tooltip too; it stays hidden until focus leaves and returns, which is the behaviour a sighted keyboard user
expects after activating the control (designer's call, said in the docs paragraph). The listener does not check
whether a tooltip is shown; Bootstrap's `hide()` returns early when nothing is shown and a custom adapter owns that
check itself.

Why this fixes case 1: Bootstrap's `hide()` sets all three `_activeTrigger` flags to `false`, so `_leave` is no longer
short-circuited and the tooltip stays hidden until the next `mouseenter` or `focusin`. By the time the click
arrives the hover trigger (and, from mousedown on, the focus trigger) has already shown the tooltip, so `hide()`
finds it shown.

The listener runs alongside `modal.js`'s own delegated click listener for `[data-cv-modal]` triggers and
`list.filter.js`'s toggle. They are independent and their order does not matter.

### 3. Dispose half (`modal.js` and `tooltip.js`)

`modal.js`:

- `CVModalConst` gains `unloadEvent: "cv:modal:unload"`.
- `cvModalInject(html)` dispatches `new CustomEvent(CVModalConst.unloadEvent, {bubbles: true})` on `#cv-modal`
  **before** the `innerHTML` assignment, then assigns, then dispatches `cv:modal:loaded` as today. One line covers both
  callers (`cvModalOpen` on 200 and `cvModalSubmit` on 422).
- The event fires unconditionally, also on the very first open when the content is still empty; listeners find nothing
  and do nothing. One branch less (designer's call).
- The header comment documents the pair: `cv:modal:unload` before every content replacement, `cv:modal:loaded` after.

The ordering is a correctness requirement, not a courtesy: Bootstrap's `Tooltip.dispose()` removes its modal handler
with `EventHandler.off(this._element.closest(".modal"), ...)`. Once the trigger is detached, `closest` returns `null`
and `EventHandler.off` silently does nothing, so a dispose after the swap would leak the handler exactly as not
disposing does. Listeners of `cv:modal:unload` can rely on the old content still being attached under `#cv-modal`.

`tooltip.js`:

- listens on `document` for `cv:modal:unload` and calls `tooltip.dispose?.(el)` for every `[data-cv-tooltip]` under
  `event.target`, mirroring the `cv:modal:loaded` listener;
- the walker is a private sibling of `initTooltips` inside the IIFE; it is not exported on `cv` (see non-goals). A
  project that injects and removes its own marked markup calls `cv.adapters.tooltip.dispose?.(el)` on its elements.

`modal.js` still knows nothing about tooltips; it dispatches an event, as it already does for `loaded`.

### 4. Bootstrap defaults (`adapters.js`)

```javascript
tooltip: {
    init(el) { component(ns, "Tooltip")?.getOrCreateInstance(el); },
    hide(el) { component(ns, "Tooltip")?.getInstance(el)?.hide(); },
    dispose(el) { component(ns, "Tooltip")?.getInstance(el)?.dispose(); },
},
```

Bootstrap's `dispose()` clears the pending show/hide timeout, removes the `hide.bs.modal` handler, restores `title`
from `data-bs-original-title`, removes the tip element if one is shown and drops the instance from the element data
map. The disposed triggers are discarded with the old content, so the restored `title` is never seen.

`cv.bootstrapAdapters(ns)` keeps its one parameter and `cv.adapters` keeps its per-adapter merge.

### 5. Theming

- A theme that wires `Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))` gets `hide` and
  `dispose` for free.
- A project that followed the per-location recipe (`cv.adapters.tooltip.init = ...` after building the adapters) keeps
  the Bootstrap `hide` and `dispose` defaults: only `init` was replaced on the adapter object.
- A project with `cv.adapters.tooltip = {init() {}}` (native tooltips) stays a no-op throughout: no instance is ever
  created, `hide` and `dispose` are absent, and `getInstance` is never called.
- A non-Bootstrap adapter opts in by implementing the two methods. The Tippy-style recipe in the docs gains
  `hide(el) { el._tippy?.hide(); }` and `dispose(el) { el._tippy?.destroy(); }`.
- The event is public: `cv:modal:unload` is the teardown hook for the extensions, which today initialise on
  `cv:modal:loaded` and have nothing to tear down on. This change only documents it; the extensions adopt it in their
  own repository.

### 6. What stays the same

No template, Python or golden-fixture changes. `init` is unchanged. The three initialisation points are unchanged. The
modal protocol (headers, 204/422, fallbacks) is unchanged. `toggle.js`, `list.filter.js`, `formset.js` are untouched.

## Acceptance (from the issue)

- Click the filter toggle with the mouse and move away: no `.tooltip.show` remains, and the tooltip does not come back
  until the next hover or focus.
- Open and cancel a modal with marked buttons ten times: the `hide.bs.modal` listener count on `#cv-modal` does not
  grow (with Bootstrap's bundle: one handler per marked button in the currently injected content, none for the
  discarded ones). This is a builder check in the browser, not an automated test, and it needs a modal that renders
  markers: the example projects open only delete views in modals, which have none. Use the test project's
  `AuthorModalDetailView` (an `ObjectDetailView` with `cv_modal = True`, property-detail buttons marked
  `object-detail`) or a temporary, uncommitted `cv_modal = True` on an example `ObjectDetailView`. Record the modal
  used and the counts in the acceptance report under `superpowers/notes/`.
- An adapter that implements only `init(el, {location})` keeps working on page load, click, modal open and 422.
- vitest cases below; adapter table rows for `hide` and `dispose` in `docs/reference/javascript.md`.

## Tests

JavaScript (vitest, `tests/js/`; Node 22 is required locally, see the harness notes):

- `tooltip.test.js`. The fake Bootstrap gains `getInstance` and per-instance `hide`/`dispose` spies.
  - a click on a marked button calls the instance's `hide` once; a click on an element inside the button (an `<i>`)
    hides the button's tooltip; a click on an unmarked button or on the app-owned `data-bs-toggle` button calls
    nothing;
  - `cv:modal:unload` dispatched on `#cv-modal` calls `dispose` once per marker under the modal content and not for
    markers outside the modal or for the app-owned button;
  - a custom adapter receives `hide(el)` and `dispose(el)` with the element as the only argument;
  - an adapter written as `{init(el) {}}` does not throw on click or on unload; neither does a missing `bootstrap`
    global (`getInstance` absent or returning `null`).
- `modal.test.js`.
  - `cvModalInject` dispatches `cv:modal:unload` on `#cv-modal` before `cv:modal:loaded`, and at unload time the
    previous content is still under `#cv-modal-content` (assert inside the listener);
  - the 422 path in `cvModalSubmit` dispatches it too;
  - `cv.CVModalConst.unloadEvent` is `"cv:modal:unload"`.
- `adapters.test.js`. `tooltip.hide` and `tooltip.dispose` call `Tooltip.getInstance(el)?.hide()` / `?.dispose()`;
  both are silent when `getInstance` returns `null` and when the namespace has no `Tooltip`.

Python: none. No server-rendered output changes.

## Docs

- `docs/reference/javascript.md`: two adapter table rows (`hide(el)`, `dispose(el)`) under the `tooltip` row; in
  "Tooltips", one paragraph on the lifecycle (hidden on click, mouse or keyboard; disposed before modal content is
  replaced; both optional; what the opt-out and the per-location recipe keep); the non-Bootstrap recipe gains `hide`
  and `dispose`;
  the "Events" table gains the `cv:modal:unload` row and its lead sentence covers three events.
- `docs/reference/modals.md`, "Extending": `cv:modal:unload` as the teardown counterpart of `cv:modal:loaded`, with the
  guarantee that the old content is still attached, and a two-line example that pairs the two.
- `modal.js` header comment: the event pair.
- `CHANGELOG.md`, "Unreleased": under Fixed, the tooltip retained after a mouse click; under Added, `hide(el)` and
  `dispose(el)` on `cv.adapters.tooltip` with their Bootstrap defaults, and the `cv:modal:unload` event.

## Left to the builder

- The exact shape of the test fakes and whether the fast-click case is worth a test: a click that arrives before
  Bootstrap's deferred `show()` ran (delay 0, next tick) hits `hide()` while nothing is shown, `hide()` returns early,
  and the pending show then fires. A human click cannot beat the next tick; check it once in the browser and note the
  result in the acceptance report rather than redesign.
- Wording and placement in the docs, following each page's style.
- Whether the private dispose walker in `tooltip.js` is a named function or inlined in the listener.

## Calls made by the designer (not discussed with the maintainer)

- `dispose(el)` is per element; `tooltip.js` walks the markers (decision 1).
- No modifier-key filtering on the click listener (decision 2).
- `cv:modal:unload` fires unconditionally, including on the first open with empty content (decision 3).
- The Bootstrap defaults use `getInstance`, never `getOrCreateInstance` (decision 1).
- The Tippy recipe's `hide`/`dispose` bodies (decision 5).
- Keyboard activation hides the tooltip like a mouse click does (decision 2).
- The browser check for the handler count uses an object-detail modal, since the example delete modals carry no
  markers (acceptance).

## Review record (2026-10-20)

A builder check (fresh reviewer, no access to the maintainer) found nothing important left. It verified that
`list.filter.js` and `formset.js` only call `preventDefault()` on their clicks, so a bubble-phase listener on
`document` sees them; that `formset.js` never removes rows; that nothing in this repository assigns
`cv.adapters.tooltip` or keeps state on `cv:modal:loaded` that would need teardown; and that the delete modal used in
the #203 acceptance run renders no marked button. Its two confirmations (keyboard activation, which modal to measure)
are settled above as designer's calls.
