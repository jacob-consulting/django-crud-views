# Modal Event Prefix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The stock modal adapter observes `hide.{prefix}.modal` / `hidden.{prefix}.modal` using the registered data
prefix, and its missing-component error no longer names Bootstrap.

**Architecture:** One function in `adapters.js` (`modalLifecycle`) reads `data-data-prefix` from `#cv-config` when it
first attaches listeners to a modal element, and builds the two event names from it. `missing()` gets neutral wording.
No Python, template or API change.

**Tech Stack:** Plain browser JavaScript, vitest + jsdom, MkDocs, pytest (docs tests).

**Spec:** `superpowers/specs/2026-11-22-modal-event-prefix-design.md` (issue #403).

## Global Constraints

- Worktree: `/home/alex/projects/workspaces/cv-issue-403/django-crud-views`, branch `fix/403-modal-event-prefix`.
  Run every command from there. One-time setup: `task dev` and `npm ci`.
- Without `#cv-config`, without `data-data-prefix`, or with prefix `bs`, the adapter listens to exactly
  `hide.bs.modal` and `hidden.bs.modal`.
- Only the prefixed names are bound, never both.
- The prefix is read once per modal element, at first `onHidden` or `show`. No re-binding.
- No new registration function, `#cv-config` attribute, `cv.bootstrapAdapters()` argument, Python or template
  change, or dev dependency.
- Not breaking: `docs/migrating-1.0.md` is untouched. CHANGELOG entry goes under `## Unreleased` → `### Fixed`.
- Line length 120 in Markdown and JS, double quotes in JS.
- Broad pytest runs use `-n auto`.

## Review Focus

- A present but empty `data-data-prefix=""`: the adapter must not throw and `show` must still work; it does not fall
  back to `bs` (empty is not a registration output). Test in Task 1.
- A hyphenated prefix (`my-lib`, allowed by `register_data_prefix`): events `hide.my-lib.modal` are observed.
  Case in Task 1.
- Two modal elements whose first use straddles a config change: each keeps the prefix it was bound with. Test in
  Task 1.
- A theme that still wires `cv.bootstrapAdapters(() => globalThis.coreui)` by hand (the CoreUI theme today) with a
  registered prefix: covered by the `object` / `function` kinds of the parametrised lifecycle test in Task 1.
- A real CoreUI bundle with real fade transitions: no automated test can show it; Task 4 (browser check).

---

### Task 1: Modal event names follow the data prefix

**Files:**
- Modify: `src/crud_views/static/crud_views/js/adapters.js:31-66` (`modalLifecycle`)
- Test: `tests/js/adapters.test.js:319-372` (the three modal lifecycle tests) plus three new tests

**Interfaces:**
- Consumes: `pageConfig({namespace, prefix, placements})` and `fakeNamespace()`, both already in the test file.
- Produces: nothing new. `cv.adapters.modal` and `cv.bootstrapAdapters(ns).modal` keep their signatures.

- [ ] **Step 1: Parametrise the three existing lifecycle tests by prefix**

Wrap the tests at lines 319–330 (`%s modal lifecycle waits …`), 347–358 (`queues a replacement open …`) and 360–371
(`cancels pending shows …`) in this block. Leave the `published native-dialog adapter` test between them where it
is, outside the block. In each moved test call `configure()` directly after `await loadScript("adapters")` (so the
config is always inserted after the script) and replace the literals `"hide.bs.modal"` / `"hidden.bs.modal"` with
`hide` / `hidden`.

```js
    // Event names follow data-data-prefix on #cv-config (#403); an absent element or attribute means bs.
    const MODAL_EVENT_CASES = [
        ["no #cv-config", () => {}, "bs"],
        ["#cv-config without data-data-prefix", () => pageConfig().removeAttribute("data-data-prefix"), "bs"],
        ["prefix bs", () => pageConfig({prefix: "bs"}), "bs"],
        ["prefix coreui", () => pageConfig({prefix: "coreui"}), "coreui"],
        ["hyphenated prefix", () => pageConfig({prefix: "my-lib"}), "my-lib"],
    ];
    describe.each(MODAL_EVENT_CASES)("modal lifecycle events, %s", (_label, configure, key) => {
        const hide = `hide.${key}.modal`, hidden = `hidden.${key}.modal`;
        // the three moved tests
    });
```

- [ ] **Step 2: Add three new tests after that block**

```js
    it("observes only the registered prefix's modal events", async () => {
        await loadScript("adapters"); pageConfig({prefix: "coreui"});
        const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
        const modal = document.getElementById("m"), callback = vi.fn();
        adapter.onHidden(modal, callback);
        modal.dispatchEvent(new Event("hide.bs.modal"));
        adapter.show(modal);
        expect(ns.instance.show).toHaveBeenCalledTimes(1); // not queued behind another library's hide
        modal.dispatchEvent(new Event("hidden.bs.modal"));
        expect(callback).not.toHaveBeenCalled();
        modal.dispatchEvent(new Event("hide.coreui.modal")); modal.dispatchEvent(new Event("hidden.coreui.modal"));
        expect(callback).toHaveBeenCalledTimes(1);
    });

    it("reads the prefix once per modal element", async () => {
        await loadScript("adapters"); const config = pageConfig({prefix: "coreui"});
        const adapter = window.cv.bootstrapAdapters(fakeNamespace()).modal;
        const first = document.getElementById("m"), second = document.getElementById("t");
        const firstCallback = vi.fn(), secondCallback = vi.fn();
        adapter.onHidden(first, firstCallback);
        config.setAttribute("data-data-prefix", "bs");
        adapter.onHidden(second, secondCallback);
        first.dispatchEvent(new Event("hidden.bs.modal")); expect(firstCallback).not.toHaveBeenCalled();
        first.dispatchEvent(new Event("hidden.coreui.modal")); expect(firstCallback).toHaveBeenCalledTimes(1);
        second.dispatchEvent(new Event("hidden.coreui.modal")); expect(secondCallback).not.toHaveBeenCalled();
        second.dispatchEvent(new Event("hidden.bs.modal")); expect(secondCallback).toHaveBeenCalledTimes(1);
    });

    it("tolerates a present but empty prefix without falling back to bs", async () => {
        await loadScript("adapters"); pageConfig({prefix: ""});
        const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
        const modal = document.getElementById("m"), callback = vi.fn();
        expect(() => adapter.onHidden(modal, callback)).not.toThrow();
        adapter.show(modal); expect(ns.instance.show).toHaveBeenCalledTimes(1);
        modal.dispatchEvent(new Event("hidden.bs.modal")); expect(callback).not.toHaveBeenCalled();
    });
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `npx vitest run tests/js/adapters.test.js`
Expected: FAIL in the `prefix coreui` and `hyphenated prefix` cases, in `observes only the registered prefix's modal
events`, in `reads the prefix once per modal element` and in the empty-prefix test; the `bs` cases pass.

- [ ] **Step 4: Implement in `modalLifecycle(modalEl)`**

Inside the function, after the `modalLifecycles.set(modalEl, state)` line, read the prefix exactly as `tooltip.init`
does (`document.getElementById("cv-config")?.getAttribute("data-data-prefix") ?? "bs"`), and register the two
existing listeners on `` `hide.${prefix}.modal` `` and `` `hidden.${prefix}.modal` ``. Listener bodies are unchanged.
Add one comment line above the read: the library's event names carry its data prefix (`bs`, `coreui`), read once
per shell.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npx vitest run tests/js/adapters.test.js`
Expected: PASS, all tests.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/static/crud_views/js/adapters.js tests/js/adapters.test.js
git commit -m "fix(403): modal adapter observes hide/hidden events of the registered data prefix"
```

### Task 2: Library-neutral missing-component error

**Files:**
- Modify: `src/crud_views/static/crud_views/js/adapters.js:9-11` (`missing`)
- Test: `tests/js/adapters.test.js` (`modal.show and collapse.toggle throw a clear error without the namespace`)

**Interfaces:**
- Produces: the error message
  `cv.adapters: UI library JavaScript not loaded (no ${name} on the namespace); load the library's bundle or assign cv.adapters.`

- [ ] **Step 1: Change the test's assertions**

```js
        expect(() => a.modal.show(document.getElementById("m")))
            .toThrow("cv.adapters: UI library JavaScript not loaded (no Modal on the namespace); load the library's bundle or assign cv.adapters.");
        expect(() => a.collapse.toggle(document.getElementById("d")))
            .toThrow("cv.adapters: UI library JavaScript not loaded (no Collapse on the namespace); load the library's bundle or assign cv.adapters.");
```

- [ ] **Step 2: Run to verify it fails**

Run: `npx vitest run tests/js/adapters.test.js -t "throw a clear error"`
Expected: FAIL, the received message contains "Bootstrap 5 JavaScript not loaded".

- [ ] **Step 3: Change the template string in `missing(name)` to the message above**

- [ ] **Step 4: Run to verify it passes, then the whole JS suite**

Run: `npx vitest run tests/js/adapters.test.js -t "throw a clear error"` — Expected: PASS.
Run: `npm test` — Expected: PASS, no test elsewhere depends on the old wording.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/adapters.js tests/js/adapters.test.js
git commit -m "fix(403): missing-component error no longer names Bootstrap"
```

### Task 3: Documentation and CHANGELOG

**Files:**
- Modify: `docs/reference/javascript.md` (lines 74–75, 80, 132–134, 138–139)
- Modify: `docs/reference/theme.md` (Data-attribute prefix section near line 137, lines 205–207, 217–218)
- Modify: `docs/reference/modals.md` (lines 42–43)
- Modify: `CHANGELOG.md` (`## Unreleased` → `### Fixed`)

Replace each quoted sentence with the text given. Re-wrap to 120 columns.

- [ ] **Step 1: `docs/reference/javascript.md`**

1. Replace "Registration changes component lookup and tooltip placement only; other methods, fixed modal events and
   lifecycle limits are unchanged." with:
   "Namespace registration changes component lookup, placement registration changes tooltip placement, and the data
   prefix names the modal events the stock adapter observes (see `onHidden` below). Other methods and lifecycle
   limits are unchanged."
2. In the `onHidden` table row, replace "listens to this modal’s `hidden.bs.modal` event after hiding and focus-trap
   release" with:
   "listens to this modal’s `hidden.{prefix}.modal` event after hiding and focus-trap release; `{prefix}` is the
   registered [data prefix](theme.md#data-attribute-prefix), so `hidden.bs.modal` by default"
3. Replace "This dispatch contract does not certify native CoreUI/Tabler bundles. A selected missing bundle does not
   fall back to Bootstrap; existing missing-component behavior applies, including legacy Bootstrap wording in
   modal/collapse errors." with:
   "It also names the modal events the stock adapter observes, `hide.{prefix}.modal` and `hidden.{prefix}.modal`:
   `bs` for Bootstrap and Tabler, `coreui` for CoreUI. The prefix is read from `#cv-config` once per modal element,
   when the adapter first attaches its listeners (the first `onHidden` or `show`); a later change is not followed.
   A library whose event names differ from its data prefix needs its own `cv.adapters.modal`. A selected missing
   bundle does not fall back to Bootstrap; modal and collapse then throw an error naming the missing component."
4. Replace "while its tooltip adapter still reads registered placement defaults." with:
   "while its tooltip adapter still reads registered placement defaults and its modal adapter the registered data
   prefix."

- [ ] **Step 2: `docs/reference/theme.md`**

1. In the "Data-attribute prefix" section, directly after the sentence ending "register that independently using
   [JavaScript namespace and tooltip placements](#javascript-namespace-and-tooltip-placements).", add:
   "The stock modal adapter does follow the prefix: it observes `hide.{prefix}.modal` and `hidden.{prefix}.modal`."
2. Replace "existing missing-component behavior applies, including legacy Bootstrap wording in modal/collapse
   errors." with:
   "modal and collapse throw an error naming the missing component."
3. Replace "This is compatible-namespace dispatch, not native CoreUI/Tabler certification; other adapter lifecycle
   contracts, including fixed modal events, are unchanged." with:
   "The stock modal adapter observes `hide.{prefix}.modal` and `hidden.{prefix}.modal` with the registered data
   prefix (`bs` by default, `coreui` in the example above), read once per modal element at its first use. A library
   whose event names differ from its data prefix must assign its own
   [`cv.adapters.modal`](javascript.md#cvadapters)."

- [ ] **Step 3: `docs/reference/modals.md`**

Replace "Namespace registration preserves the stock adapter's fixed modal events and lifecycle requirements; it does
not certify native CoreUI/Tabler behavior." with:
"The stock adapter observes `hide.{prefix}.modal` / `hidden.{prefix}.modal`, where `{prefix}` is the registered
[data prefix](theme.md#data-attribute-prefix) (`bs` by default). A fork that renames its events with its data
attributes, such as CoreUI, therefore registers its prefix as well."

- [ ] **Step 4: `CHANGELOG.md`**

Add as the first entry under `## Unreleased` → `### Fixed`:

```markdown
- **Modal events on prefixed libraries** (#403): the stock modal adapter observes `hide.{prefix}.modal` /
  `hidden.{prefix}.modal` with the registered data prefix, so closing a CoreUI modal is seen again (session release,
  focus return, replacement open). `bs` stays the default; the prefix is read once per modal element. The
  missing-component error no longer names Bootstrap.
```

- [ ] **Step 5: Verify**

Run: `grep -rn "fixed modal events\|legacy Bootstrap wording\|does not certify native\|CoreUI/Tabler certification" docs/`
Expected: no output.
Run: `git diff --stat -- docs/migrating-1.0.md` — Expected: no output.
Run: `mkdocs build --strict` — Expected: exit 0.
Run: `pytest tests -n auto` — Expected: all pass (several tests read these docs).
Run: `npm test` — Expected: all pass (`adapters.test.js` reads `javascript.md`).

- [ ] **Step 6: Commit**

```bash
git add docs/reference/javascript.md docs/reference/theme.md docs/reference/modals.md CHANGELOG.md
git commit -m "docs(403): state the modal event rule and drop the certification disclaimers"
```

### Task 4: Browser check against real CoreUI 5.9.1 (needs the maintainer's browser)

**Files:** none in this repository.

The CoreUI theme (`/home/alex/projects/alex/django-crud-views-coreui`) installs this package editable from
`../django-crud-views`, which is the `main` checkout. "Before" therefore needs no change. For "after", point the
theme's environment at the worktree, and restore it afterwards:

```bash
cd /home/alex/projects/alex/django-crud-views-coreui
uv pip install -e /home/alex/projects/workspaces/cv-issue-403/django-crud-views   # after
uv pip install -e ../django-crud-views                                            # restore
```

- [ ] **Step 1: Before (main).** `task run`, open a modal view from a keyboard-focused opener, close it. Record:
  which of `hidden.coreui.modal` / `hidden.bs.modal` the console listeners from the issue's reproduction log, and
  where focus lands. Then trigger a replacement open during the fade-out and record whether it shows.
- [ ] **Step 2: After (branch).** Same two scenarios. Expected: focus returns to the opener; the replacement shows.
- [ ] **Step 3: Stock Bootstrap.** Same two scenarios on `examples/bootstrap5` from the worktree. Expected: as on
  `main`.
- [ ] **Step 4: Record** the results on issue #403 with the branch commit and CoreUI 5.9.1, and restore the theme's
  environment.
