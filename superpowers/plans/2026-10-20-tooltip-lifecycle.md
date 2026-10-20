# Tooltip Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A tooltip hidden by a click stays hidden until the next hover or focus, and tooltip instances inside
`#cv-modal` are disposed before their triggers are replaced, through two optional methods on `cv.adapters.tooltip`
and a public `cv:modal:unload` event (issue #203).

**Architecture:** `adapters.js` gains Bootstrap defaults `hide(el)` / `dispose(el)` built on `Tooltip.getInstance`.
`modal.js` dispatches `cv:modal:unload` on `#cv-modal` inside `cvModalInject`, before the `innerHTML` swap, and still
knows nothing about tooltips. `tooltip.js` adds one delegated click listener (`closest("[data-cv-tooltip]")` →
`hide?.(el)`) and one `cv:modal:unload` listener (every marker under the target → `dispose?.(el)`). No template,
Python or golden change.

**Tech Stack:** vanilla JS classic scripts, vitest + jsdom (`tests/js/`), MkDocs Markdown.

**Spec:** `superpowers/specs/2026-10-20-tooltip-lifecycle-design.md` (read it; the plan argues from it).

**Branch:** `feat/tooltip-lifecycle` off `main`; one PR that closes #203.

## Global Constraints

- JavaScript, tests and docs only. No template, Python or golden-fixture change.
- `hide(el)` and `dispose(el)` are optional on the adapter: core calls them through `?.` and an adapter written as
  `{init(el) {}}` never throws, on page load, click, modal open or 422.
- The Bootstrap defaults use `Tooltip.getInstance(el)?.hide()` / `?.dispose()`, never `getOrCreateInstance`.
- `cv:modal:unload` is a bubbling `CustomEvent` dispatched on `#cv-modal` before the `innerHTML` assignment in
  `cvModalInject`, unconditionally (also on the first open with empty content). The old content is still attached when
  listeners run.
- No new `cv.*` globals; no new parameter on `cv.bootstrapAdapters(ns)` or `cvModalOpen(url, size)`.
- `modal.js` never names, selects or imports tooltips.
- No modifier-key filtering on the click listener; keyboard activation (a synthesised `click`) hides too.
- Classic scripts only: no modules, no build step, no inline code (strict CSP). Match each file's style.
- JS tests need Node 22: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run [files]` (local Node 20 fails
  with `webidl.util.markAsUncloneable is not a function`; that is the environment).
- Before pushing docs, check `uvx 'ruff>=0.16' format --check .` (CI ruff formats Markdown).

## Review Focus

1. A click whose target is not an `Element` (a synthetic `click` on `document`): nothing thrown. Pinned in Task 3.
2. `cv:modal:unload` on an empty modal (the first open): no `getInstance` call, nothing thrown. Pinned in Task 3.
3. An adapter assigned after the scripts loaded (`cv.adapters.tooltip = {...}` in a later script): the click and unload
   listeners resolve it at event time and call its `hide` / `dispose`. Pinned in Task 3.
4. `tooltip.js` loaded twice (a theme bundle plus the registry): the click listener is bound once, so one click hides
   once. Pinned in Task 3.
5. A marked trigger with no instance (`init` replaced by a no-op, or a marker never initialised): a click or an unload
   creates nothing and throws nothing. Pinned in Task 1 (`getInstance` returns `null`) and Task 3 (no `domReady`).

---

### Task 1: Bootstrap defaults `hide` and `dispose` in `adapters.js`

**Files:**
- Modify: `src/crud_views/static/crud_views/js/adapters.js` (the `tooltip:` entry of `cv.bootstrapAdapters`)
- Test: `tests/js/adapters.test.js`

**Interfaces:**
- Produces: `cv.bootstrapAdapters(ns).tooltip` = `{init(el), hide(el), dispose(el)}`; `cv.adapters.tooltip` (the
  default, built on `() => globalThis.bootstrap`) carries the same three. Task 3's default-adapter tests rely on
  `hide` and `dispose` resolving `Tooltip.getInstance(el)`.

- [ ] **Step 1: Extend the fake namespace** in `tests/js/adapters.test.js` (`fakeNamespace()`): add a tooltip
  instance with spies and a `getInstance` that returns it:

```javascript
const tooltip = { hide: vi.fn(), dispose: vi.fn() };
// ...in the returned object:
tooltip,
Tooltip: { getOrCreateInstance: vi.fn((el) => ({ el })), getInstance: vi.fn(() => tooltip) },
```

- [ ] **Step 2: Write the failing tests** after the existing `tooltip.init` case:

```javascript
it("tooltip.hide / dispose drive Tooltip.getInstance and never create an instance", async () => {
    await loadScript("adapters");
    const ns = fakeNamespace(), t = document.getElementById("t");
    const a = window.cv.bootstrapAdapters(ns);
    a.tooltip.hide(t);
    a.tooltip.dispose(t);
    expect(ns.Tooltip.getInstance).toHaveBeenCalledWith(t);
    expect(ns.tooltip.hide).toHaveBeenCalledTimes(1);
    expect(ns.tooltip.dispose).toHaveBeenCalledTimes(1);
    expect(ns.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
});

it("tooltip.hide / dispose are silent without an instance and without Tooltip", async () => {
    await loadScript("adapters");
    const ns = fakeNamespace(), t = document.getElementById("t");
    ns.Tooltip.getInstance = vi.fn(() => null);
    const a = window.cv.bootstrapAdapters(ns);
    expect(() => { a.tooltip.hide(t); a.tooltip.dispose(t); }).not.toThrow();
    const none = window.cv.bootstrapAdapters({});
    expect(() => { none.tooltip.hide(t); none.tooltip.dispose(t); }).not.toThrow();
});
```

- [ ] **Step 3: Run the file to verify the two new cases fail**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/adapters.test.js`
Expected: 2 failed (`a.tooltip.hide is not a function`), the rest pass.

- [ ] **Step 4: Implement** the `tooltip:` entry in `adapters.js` as the spec's decision 4 fixes it: keep `init`,
  add `hide(el)` and `dispose(el)` as one-liners on `component(ns, "Tooltip")?.getInstance(el)?.hide()` /
  `?.dispose()`, in the file's existing one-line method style.

- [ ] **Step 5: Run the file to verify it passes**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/adapters.test.js`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/static/crud_views/js/adapters.js tests/js/adapters.test.js
git commit -m "feat(js): Bootstrap hide/dispose defaults on cv.adapters.tooltip (#203)"
```

---

### Task 2: `cv:modal:unload` before every content replacement in `modal.js`

**Files:**
- Modify: `src/crud_views/static/crud_views/js/modal.js` (header comment, `CVModalConst`, `cvModalInject`)
- Test: `tests/js/modal.test.js`

**Interfaces:**
- Produces: `cv.CVModalConst.unloadEvent === "cv:modal:unload"`; `cvModalInject(html)` dispatches
  `new CustomEvent("cv:modal:unload", {bubbles: true})` on `#cv-modal`, then assigns `innerHTML`, then dispatches
  `cv:modal:loaded` as today. Task 3 listens for the event on `document`; Task 4 documents it.

- [ ] **Step 1: Write the failing tests.** In `describe("cvModalOpen")`:

```javascript
it("dispatches cv:modal:unload before the swap, with the old content still attached", async () => {
    stubFetch(textResponse("<p>second</p>"));
    const modal = document.getElementById("cv-modal"), content = document.getElementById("cv-modal-content");
    content.innerHTML = "<p>first</p>";
    const seen = [];
    modal.addEventListener("cv:modal:unload", (event) => seen.push(["unload", event.target.id, content.innerHTML]));
    modal.addEventListener("cv:modal:loaded", () => seen.push(["loaded", content.innerHTML]));
    window.cv.cvModalOpen("/books/create/", "");
    await vi.waitFor(() => expect(show).toHaveBeenCalled());
    expect(seen).toEqual([["unload", "cv-modal", "<p>first</p>"], ["loaded", "<p>second</p>"]]);
    expect(window.cv.CVModalConst.unloadEvent).toBe("cv:modal:unload");
});
```

In `describe("cvModalSubmit")` (uses the local `modalForm()` helper; the listener is on `document` to pin bubbling,
with `once: true` so it does not outlive the test):

```javascript
it("dispatches cv:modal:unload on the 422 re-render too", async () => {
    stubFetch(textResponse("<form>errors</form>", { ok: false, status: 422 }));
    const unload = vi.fn();
    document.addEventListener("cv:modal:unload", unload, { once: true });
    window.cv.cvModalSubmit(modalForm());
    await vi.waitFor(() =>
        expect(document.getElementById("cv-modal-content").innerHTML).toBe("<form>errors</form>"));
    expect(unload).toHaveBeenCalledTimes(1);
});
```

A third case, synchronous, in `describe("cvModalOpen")` (the event fires unconditionally, also before the first
injection when the modal is still empty):

```javascript
it("dispatches cv:modal:unload also while the modal is still empty", () => {
    const unload = vi.fn();
    document.getElementById("cv-modal").addEventListener("cv:modal:unload", unload);
    window.cv.cvModalInject("<p>x</p>");
    expect(unload).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 2: Run the file to verify the three new cases fail**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/modal.test.js`
Expected: 3 failed (`seen` has only the `loaded` entry; `unload` not called), the rest pass.

- [ ] **Step 3: Implement in `modal.js`:**
  - `CVModalConst`: add `unloadEvent: "cv:modal:unload",` next to `loadedEvent`.
  - `cvModalInject(html)`: dispatch the unload event on `els.modal` (bubbling, same construction as the loaded one)
    as the first statement after `cvModalElements()`, before `els.content.innerHTML = html`.
  - Header comment: replace the sentence about `cv:modal:loaded` with the pair: `cv:modal:unload` is dispatched on
    `#cv-modal` before every content replacement, while the previous content is still attached (hook for tearing down
    scripts inside modal content); `cv:modal:loaded` after every injection (hook for re-initializing them).

- [ ] **Step 4: Run the file to verify it passes**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/modal.test.js`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/modal.js tests/js/modal.test.js
git commit -m "feat(js): dispatch cv:modal:unload before modal content is replaced (#203)"
```

---

### Task 3: Hide on click and dispose on unload in `tooltip.js`

**Files:**
- Modify: `src/crud_views/static/crud_views/js/tooltip.js` (inside the `__cvTooltipInit` IIFE; header comment)
- Test: `tests/js/tooltip.test.js`

**Interfaces:**
- Consumes: Task 1's default `cv.adapters.tooltip.hide(el)` / `dispose(el)`; Task 2's event name `cv:modal:unload`
  (the tests dispatch it by hand, the string must match).
- Produces: a delegated `click` listener on `document` → `cv.adapters.tooltip.hide?.(closest marker)`; a
  `cv:modal:unload` listener on `document` → private `disposeTooltips(root)` calling
  `cv.adapters.tooltip.dispose?.(el)` for every `[data-cv-tooltip]` under `event.target`. Nothing new on `cv`.

- [ ] **Step 1: Extend the fixture and the fake** in `tests/js/tooltip.test.js`:
  - `fakeBootstrap()`: each instance is `{ el, hide: vi.fn(), dispose: vi.fn() }`; add
    `getInstance: vi.fn((el) => instances.get(el) ?? null)` to `Tooltip`.
  - `fixture()`: the first marked button gets an icon child, `<button type="button" data-cv-tooltip="context"
    title="first"><i class="icon"></i></button>`. The existing cases keep passing (two markers, one app-owned).
  - Two local helpers inside the new `describe` blocks: `markedModalContent()` injects two marked buttons
    (`object-detail`, `formset`) and one app-owned `data-bs-toggle="tooltip"` button into `#cv-modal-content`,
    dispatches `cv:modal:loaded` on `#cv-modal` and returns the fake instances of the two marked ones;
    `unload()` dispatches `new CustomEvent("cv:modal:unload", { bubbles: true })` on `#cv-modal`.

- [ ] **Step 2: Write the failing tests.** `describe("hide on click")`:

```javascript
it("hides the clicked trigger's tooltip, also when the click lands on its icon", () => {
    domReady();
    const button = document.querySelector("[data-cv-tooltip]"), instance = fake.instances.get(button);
    button.querySelector("i").click();
    expect(instance.hide).toHaveBeenCalledTimes(1);
    button.click(); // a keyboard activation synthesises the same click
    expect(instance.hide).toHaveBeenCalledTimes(2);
});

it("ignores clicks on unmarked and app-owned elements", () => {
    domReady();
    document.querySelector('[data-bs-toggle="tooltip"]').click();
    document.body.click();
    expect(fake.bootstrap.Tooltip.getInstance).not.toHaveBeenCalled();
});

it("does nothing for a trigger without an instance", () => {
    // no domReady(): nothing was initialised
    const button = document.querySelector("[data-cv-tooltip]");
    expect(() => button.click()).not.toThrow();
    expect(fake.instances.size).toBe(0);
});

it("does not throw when the click target is not an element", () => {
    domReady();
    expect(() => document.dispatchEvent(new Event("click", { bubbles: true }))).not.toThrow();
});

it("binds the click listener once even when the script is loaded twice", async () => {
    await loadScript("tooltip");
    domReady();
    const button = document.querySelector("[data-cv-tooltip]");
    button.click();
    expect(fake.instances.get(button).hide).toHaveBeenCalledTimes(1);
});

it("keeps the Bootstrap hide when only init was replaced (the per-location recipe)", () => {
    domReady();
    const originalInit = window.cv.adapters.tooltip.init;
    try {
        window.cv.adapters.tooltip.init = () => {};
        const button = document.querySelector("[data-cv-tooltip]");
        button.click();
        expect(fake.instances.get(button).hide).toHaveBeenCalledTimes(1);
    } finally {
        window.cv.adapters.tooltip.init = originalInit;
    }
});

it("calls a custom adapter's hide(el) and tolerates an adapter without hide", () => {
    const original = window.cv.adapters.tooltip, hide = vi.fn();
    try {
        window.cv.adapters.tooltip = { init() {}, hide };
        const button = document.querySelector("[data-cv-tooltip]");
        button.click();
        expect(hide).toHaveBeenCalledWith(button);
        window.cv.adapters.tooltip = { init() {} };
        expect(() => button.click()).not.toThrow();
    } finally {
        window.cv.adapters.tooltip = original;
    }
});
```

`describe("dispose on cv:modal:unload")`:

```javascript
it("disposes every marked trigger under the modal once, and nothing outside it", () => {
    domReady();
    const outside = fake.instances.get(document.querySelector("[data-cv-tooltip]"));
    const inside = markedModalContent();
    unload();
    for (const instance of inside) expect(instance.dispose).toHaveBeenCalledTimes(1);
    expect(outside.dispose).not.toHaveBeenCalled();
    expect(fake.bootstrap.Tooltip.getInstance).toHaveBeenCalledTimes(2); // the app-owned button is not touched
});

it("does nothing on an empty modal (first open)", () => {
    domReady();
    expect(() => unload()).not.toThrow();
    expect(fake.bootstrap.Tooltip.getInstance).not.toHaveBeenCalled();
});

it("calls a custom adapter's dispose(el) and tolerates an adapter without dispose", () => {
    const original = window.cv.adapters.tooltip, dispose = vi.fn();
    try {
        window.cv.adapters.tooltip = { init() {}, dispose };
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = '<button type="button" data-cv-tooltip title="x"></button>';
        unload();
        expect(dispose).toHaveBeenCalledTimes(1);
        expect(dispose).toHaveBeenCalledWith(content.querySelector("[data-cv-tooltip]"));
        window.cv.adapters.tooltip = { init() {} };
        expect(() => unload()).not.toThrow();
    } finally {
        window.cv.adapters.tooltip = original;
    }
});

it("does nothing (and does not throw) on click or unload without Bootstrap's JavaScript", () => {
    vi.stubGlobal("bootstrap", undefined);
    domReady();
    markedModalContent();
    expect(() => unload()).not.toThrow();
    expect(() => document.querySelector("[data-cv-tooltip]").click()).not.toThrow();
});
```

- [ ] **Step 3: Run the file to verify the new cases fail**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/tooltip.test.js`
Expected: the hide-count, custom-adapter and dispose cases fail (`hide` / `dispose` never called); the "does nothing"
cases may already pass; the pre-existing cases pass.

- [ ] **Step 4: Implement in `tooltip.js`**, inside the IIFE, after the `cv:formset:row-added` listener:
  - `function disposeTooltips(root)`: resolve `globalThis.cv?.adapters?.tooltip` at call time like `initTooltips`;
    return early unless `tooltip?.dispose`; otherwise call `tooltip.dispose(el)` for every `[data-cv-tooltip]` under
    `root`. Not assigned to `cv`.
  - `document.addEventListener("cv:modal:unload", (event) => disposeTooltips(event.target))`, with a comment
    mirroring the `cv:modal:loaded` one (content is replaced via `innerHTML`; `modal.js` dispatches this before, while
    the old content is still attached, so instances on it can be torn down).
  - `document.addEventListener("click", ...)`: return unless `event.target instanceof Element`; `el =
    event.target.closest("[data-cv-tooltip]")`; if `el`, call `globalThis.cv?.adapters?.tooltip?.hide?.(el)`. Comment:
    a tooltip shown by the focus trigger would otherwise stay until focus leaves (Bootstrap clears all active
    triggers in `hide()`).
  - Header comment: add two lines, hidden on click and disposed before modal content is replaced, both through
    optional adapter methods.

- [ ] **Step 5: Run the file to verify it passes**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/tooltip.test.js`
Expected: all pass.

- [ ] **Step 6: Run the whole JS suite**

Run: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`
Expected: all files pass.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/static/crud_views/js/tooltip.js tests/js/tooltip.test.js
git commit -m "feat(js): hide tooltips on click and dispose them on cv:modal:unload (#203)"
```

---

### Task 4: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/javascript.md` (adapter table after the `tooltip` / `init` row; "Tooltips" section after
  the `cv.initTooltips(root)` sentence; "A non-Bootstrap tooltip" recipe; "Events" table)
- Modify: `docs/reference/modals.md` ("Extending")
- Modify: `CHANGELOG.md` ("Unreleased")

**Interfaces:**
- Consumes: the names from Tasks 1 to 3: `hide(el)`, `dispose(el)`, `cv:modal:unload`.

- [ ] **Step 1: `javascript.md`, adapter table.** Two rows directly after the `init(el, {location})` row, same
  four columns:
  - `tooltip` | `hide(el)` (optional) | a click lands on or inside a `[data-cv-tooltip]` | `Tooltip.getInstance(el)?.hide()`; does nothing without `Tooltip` or without an instance
  - `tooltip` | `dispose(el)` (optional) | for every `[data-cv-tooltip]` under `#cv-modal` on `cv:modal:unload`, before the content is replaced | `Tooltip.getInstance(el)?.dispose()`; does nothing without `Tooltip` or without an instance

- [ ] **Step 2: `javascript.md`, "Tooltips".** One paragraph after "For markup you inject yourself, call
  `cv.initTooltips(root)`...", covering, in the page's voice: a click on a trigger (mouse, or Enter / Space on a
  focused one) calls `hide(el)` and the tooltip stays hidden until the next hover or focus, which stops the tooltip
  Bootstrap keeps up while the clicked button has focus; before modal content is replaced, `cv:modal:unload` calls
  `dispose(el)` on every marker under `#cv-modal`, so Bootstrap's per-tooltip modal handlers and instances do not
  accumulate; both methods are optional, the per-location recipe below keeps the Bootstrap defaults because it
  replaces only `init`, and the native-tooltip opt-out stays a no-op throughout; markup you remove yourself gets
  `cv.adapters.tooltip.dispose?.(el)`.

- [ ] **Step 3: `javascript.md`, "A non-Bootstrap tooltip".** Add to the Tippy-style adapter object, after `init`:
  `hide(el) { el._tippy?.hide(); },` and `dispose(el) { el._tippy?.destroy(); },` with one sentence that both are
  optional.

- [ ] **Step 4: `javascript.md`, "Events".** Lead sentence: "All three are bubbling `CustomEvent`s...". New row
  above the `cv:modal:loaded` row: `cv:modal:unload` | `#cv-modal` | before every content replacement in the modal,
  while the previous content is still attached, see [Modals](modals.md#extending).

- [ ] **Step 5: `modals.md`, "Extending".** After the `cv:modal:loaded` example, a paragraph and a paired example:
  before every content replacement the shell dispatches `cv:modal:unload` on `#cv-modal`, while the previous content
  is still attached, so a listener can tear down what it set up on `cv:modal:loaded`:

```javascript
const modal = document.getElementById("cv-modal");
modal.addEventListener("cv:modal:loaded", function () { /* initialize widgets inside the injected content */ });
modal.addEventListener("cv:modal:unload", function () { /* tear them down; the old content is still in the DOM */ });
```

- [ ] **Step 6: `CHANGELOG.md`, "Unreleased".** A new `### Fixed` heading between `### Changed` and `### Added`
  with one entry; two entries at the end of `### Added`:
  - Fixed: a Bootstrap tooltip kept open by focus after a mouse click (the filter toggle, the formset controls, any
    icon-only button) is hidden on the click and shows again on the next hover or focus (#203).
  - Added: `cv.adapters.tooltip.hide(el)` and `dispose(el)`, both optional, with the Bootstrap defaults
    `Tooltip.getInstance(el)?.hide()` / `?.dispose()`; tooltips inside the modal are disposed before its content is
    replaced, so Bootstrap's per-tooltip `hide.bs.modal` handlers on `#cv-modal` no longer accumulate (#203).
  - Added: the `cv:modal:unload` event, dispatched on `#cv-modal` before every content replacement while the previous
    content is still attached, the teardown counterpart of `cv:modal:loaded`; see `docs/reference/modals.md` (#203).

- [ ] **Step 7: Check formatting and the docs build**

Run: `uvx 'ruff>=0.16' format --check .` — Expected: already formatted (or fix and re-run).
Run: `uv run mkdocs build --strict` — Expected: no warnings (CI runs the same command; the `modals.md#extending`
anchor resolves).

- [ ] **Step 8: Commit**

```bash
git add docs/reference/javascript.md docs/reference/modals.md CHANGELOG.md
git commit -m "docs: tooltip hide/dispose adapters and the cv:modal:unload event (#203)"
```

---

### Task 5: Acceptance

**Files:**
- Create: `superpowers/notes/<run date>-tooltip-lifecycle-acceptance-report.md`
- Temporarily modify (never committed): `examples/bootstrap5/library/views.py` (`AuthorDetailView`)

- [ ] **Step 1: Suites.** `uv run pytest tests -q` — PASS (no Python changed; this proves it). JS suite (Node 22
  command, no file argument) — PASS. `task check` and `task format` — no changes left.
  `uvx 'ruff>=0.16' format --check .` — already formatted.

- [ ] **Step 2: Browser check, click half.** `task run`, log in, open `/library/author/` (its `AuthorListView` has
  `filterset_class = AuthorFilter`, so the toolbar renders `#cv-filter-toggle`). In Chrome with Bootstrap's bundle
  loaded:
  - hover the filter toggle, click it with the mouse, move the pointer away: `document.querySelectorAll(".tooltip.show").length` is `0` while the toggle still has focus;
  - Tab onto the filter toggle (tooltip shows), press Enter: `0` again;
  - move the pointer out and back in: the tooltip shows again.
  Record browser name and version.

- [ ] **Step 3: Browser check, dispose half.** The example delete modals render no marker, so give
  `AuthorDetailView` in `examples/bootstrap5/library/views.py` two temporary lines: `cv_modal = True` and
  `cv_object_detail_layout = "card-rows"`. Its `book_count` property carries a `detail` text; the example's default
  layout (`split-card`) renders that as small text, `card-rows` renders it as the marked `object-detail` button.
  Reload `/library/author/`. Bootstrap registers `hide.bs.modal` as a native `hide` listener on the modal element,
  one per tooltip created inside it, and removes it only in `dispose()`. Count them either way:
  - in the DevTools console (Console Utilities API, not available to `evaluate_script` from the chrome-devtools MCP):
    `(getEventListeners(document.getElementById("cv-modal")).hide ?? []).length`;
  - from page context, installed once after the reload and before the first open: override `addEventListener` /
    `removeEventListener` on the `#cv-modal` element instance to count `type === "hide"` additions minus removals, then
    read the counter (Bootstrap's `EventHandler` calls both through the element, so the instance override sees them).

  After each of ten open / cancel cycles of an author's detail modal the count must equal the number of marked buttons
  in the current content (1 here) and never grow. For the before picture (optional, the spec does not ask for it):
  Tasks 1 to 4 are committed by now, so `git stash` would only remove the two temporary lines. Instead
  `git checkout main -- src/crud_views/static/crud_views/js/adapters.js src/crud_views/static/crud_views/js/modal.js src/crud_views/static/crud_views/js/tooltip.js`,
  hard-reload (runserver serves the statics from source; Ctrl+Shift+R), run three cycles and note the count climbing
  by one per open, then `git checkout HEAD -- <the same three paths>` and hard-reload again. Revert the two temporary
  lines in `examples/`.

- [ ] **Step 4: Browser note, fast click.** In the console on the authors list, with the pointer away from the
  toggle: `const t = document.getElementById("cv-filter-toggle"); t.focus(); t.click();` — the focus trigger defers
  `show()` to the next tick, so the click arrives first and `hide()` returns early. Note whether a tooltip is showing
  afterwards. A human click cannot beat the next tick; this is recorded, not fixed (spec, "Left to the builder").
  Same note for touch: in Chrome device mode, with the temporary card-rows view of Step 3 still in place, tap the
  object-detail info button (the one stock trigger whose only function is its tooltip). The synthesised click follows
  `touchend` synchronously while Bootstrap defers `show()` to the next tick, so the tooltip should show and stay until
  the next tap. Record what happens; on desktop a mouse click on that button hides the tooltip it just showed, which is
  the approved "any click hides" behaviour (spec, decision 2).

- [ ] **Step 5: Write the acceptance report** at `superpowers/notes/<run date>-tooltip-lifecycle-acceptance-report.md`
  in the style of `superpowers/notes/2026-10-20-buttons-acceptance-report.md`: branch and commits, each step's command
  and outcome, browser and version, the handler counts before and after, the fast-click note. Commit it.

```bash
git add superpowers/notes/
git commit -m "notes: tooltip lifecycle acceptance report (#203)"
```

- [ ] **Step 6: Confirm the tree.** `git status` shows no leftover change in `examples/`. Open the PR from
  `feat/tooltip-lifecycle` with the report's findings in the description and `Closes #203`.
