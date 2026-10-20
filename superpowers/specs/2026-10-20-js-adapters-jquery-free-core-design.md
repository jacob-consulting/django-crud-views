# JavaScript adapters and a jQuery-free core

Date: 2026-10-20
Status: draft, reviewed with the maintainer section by section

## Intent

django-crud-views' browser scripts assume two things no project declares: a global named exactly `bootstrap`, and
jQuery. Three of the six core scripts need jQuery (`viewset.js`, `modal.js`, `list.filter.js`); `formset.js` is
built on it. `modal.js` throws without `bootstrap.Modal`, `tooltip.js` silently skips without `bootstrap.Tooltip`,
and `list.filter.js` toggles the filter panel through Bootstrap's jQuery bridge, `$(el).collapse("toggle")`, which
Bootstrap only registers when it finds jQuery at DOMContentLoaded (or at load time when Bootstrap itself is
deferred).

Building the Tabler theme (`tabler-test/docs/crud_views_upstream_questions.md`, point 3) showed the cost. Tabler's
bundle contains Bootstrap 5's components and Popper, but exposes them as `window.tabler`, and a Tabler page has no
jQuery. The theme had to load jQuery and a `bootstrap-shim.js` that aliases the global and re-registers the jQuery
plugins after the fact, and every script had to be deferred in exactly the right order. A project that bundles
Bootstrap with Vite or webpack hits the same wall: no global at all.

The goal is that **core pages need neither jQuery nor a global named `bootstrap`**:

- every call into a UI library goes through a small **adapter** object on `cv.adapters`, pre-filled with a
  Bootstrap default that looks up `globalThis.bootstrap` at call time;
- a theme replaces an adapter from any script loaded after core; a Bootstrap-compatible theme such as Tabler does
  it in one line with a factory;
- `viewset.js`, `modal.js` and `list.filter.js` use the DOM API; jQuery is a requirement only for pages with
  formsets and for jQuery-based extensions;
- the modal's size is a **semantic token** mapped by the adapter, not a Bootstrap class name written in Python.

## Goals

- `cv.adapters.modal`, `cv.adapters.tooltip`, `cv.adapters.collapse` with Bootstrap defaults and a documented
  contract.
- `cv.bootstrapAdapters(ns)`: the three adapters for any Bootstrap-compatible namespace (`bootstrap`, `tabler`, an
  ESM import).
- `viewset.js`, `modal.js`, `list.filter.js` without jQuery; `tooltip.js` and `list.filter.js` without a direct
  `bootstrap` reference.
- `formset.js` loads cleanly without jQuery and reports the missing dependency only when a formset is on the page.
- The modal shell in its own template, `crud_views/modal/shell.html`; the partial's close button dismisses through
  the adapter.
- `cv_modal_size` takes `""`, `"sm"`, `"lg"`, `"xl"`; the old `modal-*` values fail check E250 with a migration hint.
- The Tabler theme needs no shim: `bootstrap-shim.js` goes, jQuery stays only if the project uses formsets.

## Non-goals

- Removing jQuery from `formset.js` (620 lines, a documented API that passes jQuery selections). It stays on jQuery.
- Replacing Bootstrap as the default UI library. The shipped markup, the data-API components (dropdown, accordion,
  tabs) and the `.modal` classes stay Bootstrap. This spec makes a non-Bootstrap modal, tooltip or collapse a
  three-object job for a theme; it does not ship one.
- Declaring the adapter in Django settings or checking it with `manage.py check`. The choice is made in JavaScript
  at runtime; Django does not know which adapter runs (decision with the maintainer).
- Updating `crud_views_tabler` (in the `tabler-test` repo). That comes later; the "Tabler check" section says what
  the theme would do.
- Updating the `django-crud-views` skill repository. Follow-up after release.
- New modal sizes (fullscreen), stacked modals, adapters for the data-API components, which need no call from us.

## Anti-goals

- Any reference to `globalThis.bootstrap`, `bootstrap.`, `$` or `jQuery` left in `viewset.js`, `modal.js`,
  `list.filter.js` or `tooltip.js` after this. The only place that spells `bootstrap` is the default adapter.
- A Tabler special case in core (`globalThis.bootstrap ?? globalThis.tabler`). The factory makes that the theme's
  one line, not core's guess.
- A deprecation period for `modal-sm` / `modal-lg` / `modal-xl`. Semantic tokens only, from this release (decision
  with the maintainer).
- Converting the scripts to ES modules or adding a build step. They stay classic scripts served by Django unchanged
  (`superpowers/specs/2026-07-21-js-test-harness-design.md`).

## Decisions made with the maintainer

| Topic | Decision |
|---|---|
| Where the adapter is chosen | At runtime in JavaScript, by assigning to `cv.adapters`; nothing in Django settings, no system check |
| Modal adapter shape | Option 1 of the brainstorm: one object with `show(modalEl)`, `hide(modalEl)`, `setSize(dialogEl, size)`; core keeps the fetch protocol |
| `cv_modal_size` | Semantic tokens `""`, `"sm"`, `"lg"`, `"xl"` only; E250 rejects the old class names; no transition period |
| Scope | Modal, tooltip and filter collapse adapters plus jQuery removal from the three small scripts in one release, so the Tabler theme needs no shim |
| `formset.js` | Stays on jQuery; guarded so it does not throw at load without jQuery |

## Design

### 1. `cv.adapters` and the Bootstrap factory

A new first core script, `crud_views/js/adapters.js`, defines the namespace and the defaults. It is the first entry
of `CrudViewsSettings.javascript()` (key `adapters`), so it precedes every other core script in `{% cv_js %}` and in
`cv_sources("js")` for django-pipeline.

```js
globalThis.cv = globalThis.cv || {};

cv.bootstrapAdapters = function (ns) {
    // ns: a Bootstrap-compatible namespace object (window.bootstrap, window.tabler, an ESM import)
    // or a function returning one, resolved on every call so load order does not matter.
    ...
    return {modal: {show, hide, setSize}, tooltip: {init}, collapse: {toggle}};
};

// Defaults: Bootstrap's own bundle. Adapters a theme script set before core loaded are kept.
cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
```

The adapter contract, the part of the public API themes code against:

| Adapter | Method | Called by core when | Bootstrap default |
|---|---|---|---|
| `modal` | `show(modalEl)` | the partial is injected | `Modal.getOrCreateInstance(modalEl).show()`; throws a clear error when the namespace has no `Modal` |
| `modal` | `hide(modalEl)` | a `[data-cv-modal-dismiss]` element inside the shell is clicked | `Modal.getInstance(modalEl)?.hide()` |
| `modal` | `setSize(dialogEl, size)` | before `show`, with the view's `cv_modal_size` token | `dialogEl.className = "modal-dialog"` plus `modal-sm` / `modal-lg` / `modal-xl` for `sm` / `lg` / `xl`; unknown tokens and `""` give the bare base class |
| `tooltip` | `init(el)` | for every `[data-cv-tooltip]` under a root: page load, `cv:modal:loaded`, `cv:formset:row-added` | `Tooltip.getOrCreateInstance(el)`; silently does nothing without `Tooltip` (today's behaviour) |
| `collapse` | `toggle(el)` | the filter toggle button is clicked, with `#filter-collapse` | `Collapse.getOrCreateInstance(el).toggle()`; throws a clear error when the namespace has no `Collapse` |

Rules:

- The namespace is resolved **at call time**, never at load time. Bootstrap's bundle may load before or after
  `{% cv_js %}`; Tabler's bundle may be deferred. A theme passes either the object or `() => globalThis.tabler`.
- Core calls adapters **only through `cv.adapters.<name>`**, looked up at call time, so an assignment at any point
  before the user acts takes effect.
- Theme scripts that use the factory load **after** core. The asset registry guarantees that for registered bundles
  (`register_assets()` renders after the core bundle, and `cv_sources("js")` keeps the same order for pipeline).
  A hand-written adapter object may also be assigned before core loads; core merges, it does not overwrite.
- Errors thrown by `show` and `toggle` are the developer's signal that the page has no usable Bootstrap. The modal's
  open flow catches them like any other failure: it logs the error with `console.error` and falls back to full-page
  navigation, so the user is never stranded. (Today the missing-Bootstrap check runs before the fetch and nothing
  falls back.) The filter toggle lets the error surface; the icon and `aria-expanded` are flipped back so the button
  does not lie.

### 2. Modal

**Templates.** The shell moves out of the config tag into `crud_views/modal/shell.html`:

```html
<div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" id="cv-modal-dialog">
        <div class="modal-content" id="cv-modal-content"></div>
    </div>
</div>
```

`crud_views/tags/cv_config.html` keeps the `#cv-config` element and includes the shell. `{% cv_config %}` is
unchanged for projects. The three ids are the documented contract between shell and script; a theme that overrides
the shell keeps them.

`crud_views/modal/content.html` replaces `data-bs-dismiss="modal"` on the close button with `data-cv-modal-dismiss`.
Core routes the click to `cv.adapters.modal.hide()`. Project overrides of the partial that still carry
`data-bs-dismiss` keep working under the Bootstrap adapter, because Bootstrap's own data API handles them; under
another adapter they need the new attribute. `btn-close` stays (Bootstrap structural class, see the buttons spec).

**`modal.js`** keeps everything that is protocol: the `X-CV-Modal` header, 204 + `X-CV-Redirect`, 422 re-render,
fallback navigation, injection into `#cv-modal-content`, the `cv:modal:loaded` event, and the `data-cv-url`
bookkeeping. Changes:

- Delegated listeners on `document` with `closest()`: click on `[data-cv-modal='true']` opens; click on
  `[data-cv-modal-dismiss]` hides; `submit` of a form inside `#cv-modal-content` posts. Registered at script
  execution; no ready wait.
- `cvModalElements()` checks only for `#cv-modal`. The Bootstrap check is gone from core.
- `els.dialog.className = ...` becomes `cv.adapters.modal.setSize(els.dialog, size)`;
  `bootstrap.Modal.getOrCreateInstance(els.modal).show()` becomes `cv.adapters.modal.show(els.modal)`.
- `cv.cvModalOpen`, `cv.cvModalSubmit`, `cv.cvModalInject`, `cv.cvModalElements`, `cv.CVModalConst` stay exposed.

**Python.** `CrudView.cv_modal_size` documents `"" | "sm" | "lg" | "xl"`. Check E250 accepts exactly those four and
its message names the migration: `cv_modal_size must be one of '', 'sm', 'lg', 'xl' (Bootstrap class names such as
'modal-lg' are no longer accepted, use 'lg'), got 'modal-lg'`. The context value `cv_modal_size` and the four
templates that render `data-cv-modal-size="{{ cv_modal_size }}"` (`tags/context_action.html`,
`tags/list_action.html`, `tags/card_action.html`, `tags/actions_menu_item.html`) pass the token through unchanged.

### 3. Tooltip

`tooltip.js` keeps its structure (`initTooltips(root)`, the three triggers, `cv.initTooltips`). The loop body
becomes `cv.adapters.tooltip.init(el)`. The "no Bootstrap, do nothing" rule moves into the default adapter.

### 4. Filter collapse

`crud_views/tags/context_action_filter.html` gains `aria-expanded="true|false"` from `cv_filter_expanded` and
`aria-controls="filter-collapse"`. The button already renders both icons and hides one with `d-none`.

`list.filter.js` is rewritten without jQuery:

- Wiring runs at DOMContentLoaded, or immediately when the script executes after it (same pattern as `tooltip.js`).
- The toggle handler computes the new state from the button's own `aria-expanded` (open or closed is core's
  knowledge, not a visibility test), writes it back, flips the two icon spans' `d-none`, posts
  `{"filter_expanded": <bool>}` as JSON with `fetch` (`X-CSRFToken` from `cvGetConfig()`, same endpoint and body as
  today), and calls `cv.adapters.collapse.toggle(document.getElementById("filter-collapse"))`.
- The reset handler keeps its behaviour: navigate to the list path with `reset_filter=true`, preserving `sort`.
- The click handler on the Apply Filter button (`#filter-button`) is removed. It reads `aria-expanded` from a submit
  button that never has it and writes to a form field that does not exist; it is dead code from an earlier design.
- The `console.log` chatter goes.

The server side (`ListViewTableFilterMixin.post`, session persistence, `cv_filter_expanded`) is unchanged.

### 5. `viewset.js`

`cvGetConfig()` stays as is. The three delegated jQuery handlers become `document.addEventListener` plus `closest()`:

- click on `[data-cv-action='submit-form']`: `preventDefault()`, then submit the form named by `data-cv-target`
  with `requestSubmit()` (fires the `submit` event like jQuery's `.submit()` did; `submit()` as fallback where
  `requestSubmit` is missing);
- `change` on `[data-cv-action='submit-on-change']`: `el.form.submit()` as today;
- click on `[data-cv-cancel-url]`: `preventDefault()`, `globalThis.location.href = url`.

### 6. `formset.js`

Only the tail changes. The `$(function () { ... })` start-up block becomes a DOMContentLoaded start (immediate when
already loaded) that:

1. returns when the page has no `.cv-formset-content`;
2. otherwise, without `globalThis.jQuery`, logs one `console.error` naming the requirement ("formsets need jQuery on
   this page; load it before DOMContentLoaded") and returns;
3. otherwise constructs `CrudViewsFormset` as today.

Nothing else in the file runs `$` at load time (every other use is inside a method), so the file loads cleanly on a
page without jQuery. jQuery no longer has to precede `{% cv_js %}`: it has to be present by DOMContentLoaded on
pages with formsets.

### 7. Load order summary

| Script | Needs at load | Needs at use |
|---|---|---|
| `adapters.js` | nothing | — |
| `viewset.js` | `cv` | nothing |
| `formset.js` | nothing | jQuery, on pages with formsets |
| `list.filter.js` | `cvGetConfig` | `cv.adapters.collapse` |
| `modal.js` | `cv` | `cv.adapters.modal` |
| `toggle.js` | nothing | nothing |
| `tooltip.js` | nothing | `cv.adapters.tooltip` |

Bootstrap's bundle: anywhere on the page for the default adapters (resolved at call time); it still must be present
for the data-API components, as today. jQuery: only pages with formsets, and the datetimepicker / typeahead
extensions, which document their own requirement.

## Acceptance

- A page with Bootstrap's bundle on `window.bootstrap` and **no jQuery**: modals open, re-render on 422, dismiss
  via the close button and redirect on success; tooltips show; the filter toggle opens and closes the panel and
  persists the state; POST list and context actions submit; cancel buttons navigate; the card order combo submits;
  no console errors.
- The same page with a formset and no jQuery: exactly one console error naming jQuery; everything else works.
- A Tabler page with `Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))` after core, no
  jQuery, no shim, every script deferred: all of the above.
- `cv_modal_size = "modal-lg"` fails `manage.py check` with E250 and the migration hint; `"lg"` passes and renders
  `data-cv-modal-size="lg"`; the Bootstrap adapter gives the dialog `modal-dialog modal-lg`.
- A project that does nothing renders the same DOM as 0.30.0 except: the close button attribute
  (`data-cv-modal-dismiss` instead of `data-bs-dismiss="modal"`), `aria-expanded` and `aria-controls` on the filter
  toggle, the `data-cv-modal-size` values, and one more script tag (`adapters.js`).
- No `bootstrap`, `$` or `jQuery` token in `viewset.js`, `modal.js`, `list.filter.js`, `tooltip.js` (grep).

## Testing

JavaScript (vitest, `tests/js/`):

- `adapters.test.js` (new): the factory with a fake namespace: `show`, `hide`, `setSize` for each token and for an
  unknown token, `init`, `toggle`; lazy resolution (namespace appears after the factory call); `show` and `toggle`
  throw without the namespace, `init` does not; core merges pre-existing adapters instead of overwriting.
- `modal.test.js`: stub `cv.adapters.modal` instead of `bootstrap`; a `[data-cv-modal-dismiss]` click calls `hide`
  with `#cv-modal`; `setSize` receives the token; an adapter error during open logs and falls back to navigation.
- `list.filter.test.js`: `fetch` mock instead of `$.post`; `aria-expanded` flips and the JSON body carries the new
  state; `cv.adapters.collapse.toggle` receives `#filter-collapse`; reset navigation with and without `sort`; the
  adapter error path restores icon and `aria-expanded`.
- `viewset.test.js`: the existing cases against the vanilla handlers; `submit-form` uses `requestSubmit`.
- `formset.test.js`: without `jQuery` on the global, loading logs one error when formset markup is present and
  nothing otherwise; existing cases unchanged.
- `tooltip.test.js`: against `cv.adapters.tooltip`.
- `helpers/load.js`: the jQuery-ready wait applies only to `formset`; the other scripts are awaited via
  DOMContentLoaded semantics. jQuery stays a devDependency for the formset tests.

Python (pytest, `tests/test1/`):

- E250 accepts `""`, `"sm"`, `"lg"`, `"xl"` and rejects `"modal-lg"` with the hint in the message.
- `{% cv_config %}` renders the shell with the three ids; `modal/content.html` renders `data-cv-modal-dismiss` and no
  `data-bs-dismiss`; the filter toggle renders `aria-expanded` matching `cv_filter_expanded`.
- `test_pipeline_sources.py`: `adapters.js` is the first core entry; the settings order is
  adapters, viewset, formset, list_filter, modal, toggle, tooltip.
- Existing tests that set `cv_modal_size = "modal-lg"` (`test_modal.py`, `od/test_object_detail_view.py`,
  `test_card_action_post.py`, `app/views.py`) move to `"lg"`.

Manual: the bootstrap5 example with the jQuery tag removed from `base.html` (formset pages then show the one error),
and again with it present.

## Tabler check

Against `crud_views_tabler` in `tabler-test` as of its current state, what the theme would do after this release:

| Today | After |
|---|---|
| `shared/js.html` loads jQuery 3.7.1 from CDN and `bootstrap-shim.js`, all deferred, before the core scripts | `shared/js.html` override can go entirely, or keep only `defer`; the theme registers `crud_views_tabler/adapters.js` through `register_assets()` and it renders after core |
| `bootstrap-shim.js` aliases `window.bootstrap = window.tabler` and re-registers the jQuery plugins | deleted; `adapters.js` is `Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));` |
| jQuery on every page | jQuery only if the project uses formsets or the datetimepicker extension |
| Deferred order matters (Tabler before jQuery before the bridge) | irrelevant: the namespace is resolved at call time |
| Modal templates | none to override: Tabler renders Bootstrap's modal markup and ships `Modal`, `Tooltip`, `Collapse` with `getOrCreateInstance` / `getInstance` (checked in `@tabler/core` 1.6.1 from jsDelivr) |

Not verified: that Tabler's copied Bootstrap components keep `getInstance` and `jQueryInterface` in future versions.
They are a vendored fork, not an npm dependency on Bootstrap.

## Files to change (0.30.0 inventory)

JavaScript (`src/crud_views/static/crud_views/js/`): new `adapters.js`; rewrite `viewset.js`, `modal.js`,
`list.filter.js`; edit `tooltip.js` (loop body), `formset.js` (tail).

Templates (`src/crud_views/templates/crud_views/`): `tags/cv_config.html`, new `modal/shell.html`,
`modal/content.html`, `tags/context_action_filter.html`.

Python: `lib/settings.py` (`javascript()`), `lib/view/base.py` (`cv_modal_size` comment, E250).

Tests: as listed under Testing; `tests/js/helpers/dom.js` modal skeleton (close button fixture).

Examples: every `cv_modal_size = "modal-*"` under `examples/`; `examples/bootstrap5/project/templates/project/base.html`
keeps its jQuery tag (the examples use formsets) with a comment saying why.

## Documentation

- `docs/reference/modals.md`: requirements (Bootstrap's bundle on `window.bootstrap`, or an adapter; jQuery no longer
  listed), the size tokens, the shell template and its ids, `data-cv-modal-dismiss`.
- `docs/reference/javascript.md` (new): the `cv` namespace, `cv.adapters` and the contract table above,
  `cv.bootstrapAdapters(ns)`, recipes for Tabler, an ESM build (`cv.adapters = cv.bootstrapAdapters(bootstrap)`
  after `import * as bootstrap from "bootstrap"`), and a native `<dialog>` modal as the non-Bootstrap example; the
  load-order table; which pages need jQuery.
- `docs/reference/assets.md`: the jQuery statements (lines 42–43, 82, 102, 109, 127 in 0.30.0) change to "optional,
  formsets and jQuery-based extensions only"; the pipeline example keeps `before=["js/jquery.js"]` as an example of
  `before`, with that wording.
- `docs/reference/formsets.md`: jQuery requirement stated there.
- `docs/reference/theme.md`: link to the JavaScript page.
- `docs/reference/action_menus.md`: unchanged (the dropdown is a data-API component).
- System check reference (wherever E250 is listed): new message.
- `CHANGELOG.md`, Unreleased: breaking (`cv_modal_size` tokens, `data-cv-modal-dismiss`, `cv_config` includes
  `modal/shell.html`), changed (jQuery optional, `adapters.js` first core script, `aria-expanded` on the filter
  toggle), added (`cv.adapters`, `cv.bootstrapAdapters`).
- Follow-up outside this repo: the `django-crud-views` skill (settings, modals, assets, migration pages).

## Constraints

- Classic scripts, no modules, no bundler; CSP-safe (no inline code; the theme's adapter file is a static asset and
  gets the nonce through the registry).
- Navigation only through `globalThis.location.*`, which the test harness proxies.
- `requestSubmit()` needs Safari 16 or newer (2022); the fallback to `submit()` covers older browsers at the cost of
  not firing `submit` listeners there.
- `cv_sources("js")` and the pipeline docs follow the settings order automatically; the W345 and `cv_assets` tooling
  is unaffected.
- The partial, the shell and the four button templates remain overridable by name as before; no template is renamed.

## Left to the builder

- Exact wording of the two adapter error messages and the formset console error.
- Internal structure of `adapters.js` (IIFE, helper names) and how the factory resolves a function versus an object.
- Fixture details in the vitest tests and how `helpers/load.js` awaits DOMContentLoaded for the non-formset scripts.
- Where `docs/reference/javascript.md` sits in the mkdocs nav, and the changelog wording.
- Whether the modal open flow logs with `console.error` before or after the fallback navigation call.

## Calls I made (not discussed with the maintainer)

- The factory is named `cv.bootstrapAdapters` and accepts an object or a function; core resolves lazily by default.
- Core merges pre-existing `cv.adapters` entries rather than overwriting, so a hand-written adapter may load first.
- `adapters.js` is a separate first script rather than a block inside `viewset.js`.
- `collapse.toggle` throws without Bootstrap, like the modal; `tooltip.init` stays silent, like today.
- The modal open flow catches adapter errors, logs them and falls back to full-page navigation.
- `submit-form` uses `requestSubmit()` so `submit` listeners keep firing as they did with jQuery's `.submit()`.
- The Apply Filter click handler is removed as dead code; `console.log` chatter in `list.filter.js` goes.
- `aria-expanded` and `aria-controls` are added to the filter toggle; the state lives there.
- The formset guard logs only when formset markup is present, so pages without formsets stay silent.
- No system check inspects the overridden shell for the three ids.
- Shipped as the next release with breaking entries, following the 0.30.0 precedent for breaking changes in 0.x.
