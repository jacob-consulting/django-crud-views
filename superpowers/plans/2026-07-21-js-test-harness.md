# JS Test Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Vitest + jsdom unit-test harness for the package's first-party browser scripts (`formset.js`, `toggle.js`, `modal.js`), plus CI and Taskfile integration.

**Architecture:** Vitest runs pure unit tests in a jsdom environment. A `loadScript()` helper reads each shipped file verbatim from `src/crud_views/static/crud_views/js/` and executes it via `new Function("window", code)` against a window Proxy whose `location` is a stub (jsdom's real `location` is unforgeable and cannot be spied on). Because that wrapping hides top-level declarations, `formset.js` and `modal.js` get a short behavior-neutral `window.cv` attachment block. Fixtures mirror the real Django templates. Spec: `superpowers/specs/2026-07-21-js-test-harness-design.md`.

**Tech Stack:** Vitest, jsdom, jQuery 3.7.x (real, devDependency), istanbul-lib-instrument (coverage), GitHub Actions, Taskfile.

## Global Constraints

- Source files under test are `src/crud_views/static/crud_views/js/{formset,toggle,modal}.js`. The ONLY allowed source edits: the `window.cv` attachment blocks (Tasks 3, 4) and the one-line DELETE-detection bugfix (Task 4). No other refactoring.
- `toggle.js` gets **no** source edit.
- jQuery devDependency pinned to 3.7.x (the version the example app loads).
- `package.json`: `"private": true`, `"engines": { "node": ">=20" }`. CI uses Node 22.
- **Commit `package-lock.json`** (CI runs `npm ci`). Gitignore `node_modules` and `coverage-js`.
- JS style: 4-space indent, double quotes (match `modal.js`/`toggle.js`).
- In tests, define globals visible to the scripts under test ONLY via `vi.stubGlobal(...)` — in Vitest's jsdom environment, bare-identifier lookups in evaluated code resolve against the Node global, and `vi.stubGlobal` sets the value on both `globalThis` and `window`. Plain `window.foo = ...` assignments in test code are NOT reliably visible as bare identifiers.
- All `npm`/`npx` commands run from the repo root. Vitest commands: `npx vitest run` (all), `npx vitest run tests/js/<file>` (one file).
- Python tests are untouched; never run `pytest` for this plan except when told to.

## File Structure

| File | Responsibility |
|---|---|
| `package.json`, `package-lock.json` | dev-only Node tooling manifest |
| `vitest.config.js` | jsdom environment, test include, setup file, (Task 7: coverage) |
| `tests/js/helpers/setup.js` | jQuery global, console silencing, per-test nav reset |
| `tests/js/helpers/load.js` | `loadScript()`, `nav` stub, window Proxy |
| `tests/js/helpers/dom.js` | fixture builders mirroring the real templates |
| `tests/js/harness.test.js` | loader smoke tests |
| `tests/js/toggle.test.js` | toggle.js suite |
| `tests/js/modal.test.js` | modal.js suite |
| `tests/js/formset.test.js` | formset.js suite (Tasks 4–6) |
| `.github/workflows/js.yml` | CI job |
| `taskfile.yaml`, `CONTRIBUTING.md`, `docs/development/index.md`, `CHANGELOG.md` | integration + docs |

---

### Task 1: Harness scaffolding

**Files:**
- Create: `package.json` (via npm), `vitest.config.js`, `tests/js/helpers/setup.js`, `tests/js/helpers/load.js`, `tests/js/harness.test.js`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `loadScript(name: string): Promise<void>` — executes `src/crud_views/static/crud_views/js/<name>.js`, resolves after jQuery ready callbacks ran. `nav = { assign: vi.fn(), href: "" }` — the `window.location` seen by loaded scripts. `resetNav()` — reinstalls fresh spies (called automatically in a global `beforeEach`). All exported from `tests/js/helpers/load.js`.

- [ ] **Step 1: Write the failing smoke test**

Create `tests/js/harness.test.js`:

```js
import { describe, expect, it } from "vitest";
import { loadScript } from "./helpers/load.js";

describe("harness", () => {
    it("executes shipped scripts against the jsdom window", async () => {
        expect(window.__cvToggleInit).toBeUndefined();
        await loadScript("toggle");
        expect(window.__cvToggleInit).toBe(true);
    });

    it("provides real jQuery as a global", () => {
        expect(window.$).toBeDefined();
        expect(window.$.fn.jquery).toMatch(/^3\.7\./);
    });
});
```

- [ ] **Step 2: Run it to verify failure**

Run: `npx vitest run` — Expected: FAIL (vitest not installed / config missing).

- [ ] **Step 3: Install tooling and write config + helpers**

```bash
npm init -y
npm pkg set private=true --json
npm pkg set name="django-crud-views-js-tests" description="Dev-only JS unit-test harness (see superpowers/specs/2026-07-21-js-test-harness-design.md)" engines.node=">=20" scripts.test="vitest run" "scripts.test:watch"="vitest" scripts.coverage="vitest run --coverage"
npm pkg delete main keywords author license
npm install --save-dev vitest jsdom jquery@3.7.1
```

(Afterwards verify `package.json` contains `"private": true` as a boolean, not the string `"true"`; fix by hand if needed.)

Create `vitest.config.js`:

```js
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        environment: "jsdom",
        include: ["tests/js/**/*.test.js"],
        setupFiles: ["tests/js/helpers/setup.js"],
    },
});
```

Create `tests/js/helpers/setup.js`:

```js
import $ from "jquery";
import { beforeEach, vi } from "vitest";
import { resetNav } from "./load.js";

// The shipped files resolve `$` / `jQuery` as bare globals; stubGlobal sets
// them on both globalThis and the jsdom window.
vi.stubGlobal("$", $);
vi.stubGlobal("jQuery", $);

// formset.js logs debug chatter via console.log/console.assert.
vi.spyOn(console, "log").mockImplementation(() => {});
vi.spyOn(console, "assert").mockImplementation(() => {});

beforeEach(() => {
    resetNav();
});
```

Create `tests/js/helpers/load.js`:

```js
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { vi } from "vitest";

const JS_DIR = fileURLToPath(new URL("../../../src/crud_views/static/crud_views/js/", import.meta.url));

// jsdom's window.location is unforgeable (cannot be spied on or replaced) and
// its navigation methods are no-ops. The shipped files always navigate via
// `window.location.*`, so loadScript executes them against a Proxy whose
// `location` is this stub; everything else falls through to the real window.
export const nav = {
    assign: vi.fn(),
    href: "",
};

export function resetNav() {
    nav.assign = vi.fn();
    nav.href = "";
}

function testWindow() {
    return new Proxy(window, {
        get: (target, prop) => (prop === "location" ? nav : Reflect.get(target, prop)),
        set: (target, prop, value) => Reflect.set(target, prop, value),
    });
}

export async function loadScript(name) {
    const code = fs.readFileSync(`${JS_DIR}${name}.js`, "utf-8");
    new Function("window", code)(testWindow());
    // jQuery defers $(document).ready() callbacks by a microtask even when the
    // document is already complete; wait for them so wiring is done on return.
    await new Promise((resolve) => window.jQuery(resolve));
}
```

Append to `.gitignore`:

```
node_modules
coverage-js
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run` — Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json vitest.config.js tests/js .gitignore
git commit -m "test(js): add Vitest + jsdom harness scaffolding"
```

---

### Task 2: toggle.js suite

**Files:**
- Create: `tests/js/toggle.test.js`
- No source edits (spec: toggle.js is tested purely through events).

**Interfaces:**
- Consumes: `loadScript` from Task 1.
- Produces: nothing used by later tasks.

Background for the implementer: `toggle.js` (read it first) is an IIFE. On `DOMContentLoaded` or `cv:modal:loaded` it finds `[cv-data-toggle-group]` elements, locates the checkbox named by `cv-data-toggle-field` (exact name or `-<name>` suffix) within the nearest `<form>` (else document), then shows/enables or hides/disables the group's inputs on checkbox change — EXCEPT management-form inputs (`-TOTAL_FORMS`, `-INITIAL_FORMS`, `-MIN_NUM_FORMS`, `-MAX_NUM_FORMS` suffixes), which always stay enabled. The `DOMContentLoaded` event has already fired when tests run, so tests dispatch it manually.

- [ ] **Step 1: Write the failing tests**

Create `tests/js/toggle.test.js`:

```js
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fixture({ field = "active", checked = true, checkboxName = field } = {}) {
    document.body.innerHTML = `
        <form>
            <input type="checkbox" name="${checkboxName}" ${checked ? "checked" : ""}>
            <div cv-data-toggle-group cv-data-toggle-field="${field}">
                <input type="text" name="title">
                <select name="genre"></select>
                <textarea name="notes"></textarea>
                <input type="hidden" name="book-None-0-TOTAL_FORMS" value="2">
            </div>
        </form>`;
    return {
        group: document.querySelector("[cv-data-toggle-group]"),
        checkbox: document.querySelector("input[type=checkbox]"),
    };
}

function wire() {
    document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
}

describe("toggle.js", () => {
    beforeAll(async () => {
        await loadScript("toggle");
    });

    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("keeps a group with a checked toggle visible and enabled", () => {
        const { group } = fixture({ checked: true });
        wire();
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("hides and disables a group whose toggle is unchecked", () => {
        const { group } = fixture({ checked: false });
        wire();
        expect(group.style.display).toBe("none");
        expect(group.querySelector("[name=title]").disabled).toBe(true);
        expect(group.querySelector("[name=genre]").disabled).toBe(true);
        expect(group.querySelector("[name=notes]").disabled).toBe(true);
    });

    it("keeps management-form hidden inputs enabled even when the group is off", () => {
        const { group } = fixture({ checked: false });
        wire();
        expect(group.querySelector("[name$=-TOTAL_FORMS]").disabled).toBe(false);
    });

    it("reacts to checkbox change in both directions", () => {
        const { group, checkbox } = fixture({ checked: true });
        wire();
        checkbox.click();
        expect(group.style.display).toBe("none");
        expect(group.querySelector("[name=title]").disabled).toBe(true);
        checkbox.click();
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("finds the checkbox by formset-prefixed suffix name", () => {
        const { group } = fixture({ field: "active", checkboxName: "book-None-0-active", checked: false });
        wire();
        expect(group.style.display).toBe("none");
    });

    it("scopes the checkbox lookup to the nearest form", () => {
        document.body.innerHTML = `
            <form id="a"><input type="checkbox" name="active" checked></form>
            <form id="b">
                <input type="checkbox" name="active">
                <div cv-data-toggle-group cv-data-toggle-field="active">
                    <input type="text" name="title">
                </div>
            </form>`;
        wire();
        const group = document.querySelector("[cv-data-toggle-group]");
        expect(group.style.display).toBe("none");
        document.querySelector("#a input").click();
        expect(group.style.display).toBe("none");
    });

    it("leaves a group without a matching checkbox untouched", () => {
        document.body.innerHTML = `
            <div cv-data-toggle-group cv-data-toggle-field="nope">
                <input type="text" name="title">
            </div>`;
        expect(() => wire()).not.toThrow();
        const group = document.querySelector("[cv-data-toggle-group]");
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("wires groups injected into the modal via cv:modal:loaded", () => {
        document.body.innerHTML = `<div id="cv-modal-content"></div>`;
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = `
            <form>
                <input type="checkbox" name="active">
                <div cv-data-toggle-group cv-data-toggle-field="active">
                    <input type="text" name="title">
                </div>
            </form>`;
        content.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        expect(content.querySelector("[cv-data-toggle-group]").style.display).toBe("none");
    });

    it("does not double-bind an already-wired group", () => {
        const { checkbox } = fixture();
        const spy = vi.spyOn(checkbox, "addEventListener");
        wire();
        wire();
        expect(spy.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
    });
});
```

- [ ] **Step 2: Run to verify current state**

Run: `npx vitest run tests/js/toggle.test.js` — Expected: all 9 PASS (toggle.js already implements this; these are characterization tests locking behavior in). If any test fails, STOP and debug the test — do not modify `toggle.js`.

- [ ] **Step 3: Run the full suite**

Run: `npx vitest run` — Expected: 11 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/js/toggle.test.js
git commit -m "test(js): characterization tests for toggle.js conditional groups"
```

---

### Task 3: modal.js attachment block + suite

**Files:**
- Create: `tests/js/helpers/dom.js`, `tests/js/modal.test.js`
- Modify: `src/crud_views/static/crud_views/js/modal.js` (append attachment block only)

**Interfaces:**
- Consumes: `loadScript`, `nav` from Task 1.
- Produces: `modalSkeleton()` in `tests/js/helpers/dom.js` (used only here). Source attachment: `window.cv.{CVModalConst, cvModalElements, cvModalInject, cvModalOpen, cvModalSubmit}`.

Background: read `modal.js` first. Protocol: `cvModalOpen(url, size)` GETs with `X-CV-Modal: true`; 200 → inject partial into `#cv-modal-content`, set dialog size class + `data-cv-url`, dispatch `cv:modal:loaded`, `bootstrap.Modal.getOrCreateInstance(modal).show()`; non-OK response or network error → `window.location.assign(url)`. `cvModalSubmit(form)` POSTs FormData; `X-CV-Redirect` header → navigate there; 422 → re-inject partial; anything else / error → navigate to fallback (`data-cv-url`, else form action).

- [ ] **Step 1: Write the failing tests**

Create `tests/js/helpers/dom.js` (markup mirrors `src/crud_views/templates/crud_views/tags/cv_config.html` — keep in sync when that template changes):

```js
export function modalSkeleton() {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog" id="cv-modal-dialog">
                <div class="modal-content" id="cv-modal-content"></div>
            </div>
        </div>`;
}
```

Create `tests/js/modal.test.js`:

```js
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript, nav } from "./helpers/load.js";
import { modalSkeleton } from "./helpers/dom.js";

function textResponse(html, { ok = true, status = 200, headers = {} } = {}) {
    return {
        ok,
        status,
        headers: { get: (name) => headers[name] ?? null },
        text: () => Promise.resolve(html),
    };
}

function stubFetch(responseOrError) {
    const impl = responseOrError instanceof Error
        ? () => Promise.reject(responseOrError)
        : () => Promise.resolve(responseOrError);
    const fetchMock = vi.fn(impl);
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
}

describe("modal.js", () => {
    let show;

    beforeAll(async () => {
        await loadScript("modal");
    });

    beforeEach(() => {
        modalSkeleton();
        show = vi.fn();
        vi.stubGlobal("bootstrap", { Modal: { getOrCreateInstance: vi.fn(() => ({ show })) } });
    });

    describe("cvModalOpen", () => {
        it("GETs the url with the X-CV-Modal header", async () => {
            const fetchMock = stubFetch(textResponse("<p>hi</p>"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(fetchMock).toHaveBeenCalledWith("/books/create/", { headers: { "X-CV-Modal": "true" } });
        });

        it("injects the partial, sets url + size and shows the modal on 200", async () => {
            stubFetch(textResponse("<p>partial</p>"));
            const loaded = vi.fn();
            document.getElementById("cv-modal").addEventListener("cv:modal:loaded", loaded);
            window.cv.cvModalOpen("/books/create/", "modal-lg");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(document.getElementById("cv-modal-content").innerHTML).toBe("<p>partial</p>");
            expect(document.getElementById("cv-modal-dialog").className).toBe("modal-dialog modal-lg");
            expect(document.getElementById("cv-modal").getAttribute("data-cv-url")).toBe("/books/create/");
            expect(loaded).toHaveBeenCalled();
            expect(nav.assign).not.toHaveBeenCalled();
        });

        it("resets the dialog class when no size is given", async () => {
            stubFetch(textResponse("<p>x</p>"));
            document.getElementById("cv-modal-dialog").className = "modal-dialog modal-lg";
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(document.getElementById("cv-modal-dialog").className).toBe("modal-dialog");
        });

        it("falls back to full-page navigation on a non-OK response", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
            expect(show).not.toHaveBeenCalled();
            expect(document.getElementById("cv-modal-content").innerHTML).toBe("");
        });

        it("falls back to full-page navigation on a network error", async () => {
            stubFetch(new Error("offline"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });
    });

    describe("cvModalSubmit", () => {
        function modalForm({ action = "/books/create/", modalUrl = null } = {}) {
            if (modalUrl) {
                document.getElementById("cv-modal").setAttribute("data-cv-url", modalUrl);
            }
            document.getElementById("cv-modal-content").innerHTML =
                `<form action="${action}"><input type="text" name="title" value="t"></form>`;
            return document.querySelector("#cv-modal-content form");
        }

        it("POSTs FormData with the X-CV-Modal header", async () => {
            const fetchMock = stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/books/" } }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalled());
            const [url, options] = fetchMock.mock.calls[0];
            expect(url).toBe("/books/create/");
            expect(options.method).toBe("POST");
            expect(options.headers).toEqual({ "X-CV-Modal": "true" });
            expect(options.body).toBeInstanceOf(FormData);
        });

        it("navigates to the X-CV-Redirect target on success", async () => {
            stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/books/" } }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/"));
        });

        it("swaps in the re-rendered partial on 422", async () => {
            stubFetch(textResponse("<form>errors</form>", { ok: false, status: 422 }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() =>
                expect(document.getElementById("cv-modal-content").innerHTML).toBe("<form>errors</form>"));
            expect(nav.assign).not.toHaveBeenCalled();
        });

        it("navigates to data-cv-url on an unexpected status", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalSubmit(modalForm({ modalUrl: "/books/create/?step=1" }));
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/?step=1"));
        });

        it("navigates to the form action when no data-cv-url is set", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });

        it("navigates to the fallback on a network error", async () => {
            stubFetch(new Error("offline"));
            window.cv.cvModalSubmit(modalForm({ modalUrl: "/books/create/" }));
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });
    });

    describe("guards", () => {
        it("throws a descriptive error when #cv-modal is missing", () => {
            document.body.innerHTML = "";
            expect(() => window.cv.cvModalElements()).toThrow(/#cv-modal not found/);
        });

        it("throws a descriptive error when Bootstrap is missing", () => {
            vi.stubGlobal("bootstrap", undefined);
            expect(() => window.cv.cvModalElements()).toThrow(/Bootstrap 5 JavaScript not loaded/);
        });
    });

    describe("delegated handlers", () => {
        it("opens the modal from a [data-cv-modal] link click", async () => {
            const fetchMock = stubFetch(textResponse("<p>x</p>"));
            document.body.insertAdjacentHTML("beforeend",
                `<a href="/books/1/delete/" data-cv-modal="true" data-cv-modal-size="modal-xl">del</a>`);
            document.querySelector("a[data-cv-modal]").click();
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(fetchMock).toHaveBeenCalledWith("/books/1/delete/", { headers: { "X-CV-Modal": "true" } });
            expect(document.getElementById("cv-modal-dialog").className).toBe("modal-dialog modal-xl");
        });

        it("intercepts form submits inside the modal content", async () => {
            const fetchMock = stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/done/" } }));
            document.getElementById("cv-modal-content").innerHTML = `<form action="/books/create/"></form>`;
            const form = document.querySelector("#cv-modal-content form");
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/done/"));
            expect(fetchMock.mock.calls[0][1].method).toBe("POST");
        });
    });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `npx vitest run tests/js/modal.test.js` — Expected: FAIL — `window.cv` is undefined (no attachment block yet).

- [ ] **Step 3: Append the attachment block to modal.js**

At the end of `src/crud_views/static/crud_views/js/modal.js` append:

```js
// Test seam: expose the modal API on a shared namespace. The functions above
// are already implicit window globals in the browser (top-level declarations);
// this only adds `CVModalConst` and namespaced access for the unit tests.
window.cv = window.cv || {};
Object.assign(window.cv, {CVModalConst, cvModalElements, cvModalInject, cvModalOpen, cvModalSubmit});
```

- [ ] **Step 4: Run to verify pass**

Run: `npx vitest run tests/js/modal.test.js` — Expected: 15 passed. Then `npx vitest run` — Expected: 26 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/js/modal.test.js tests/js/helpers/dom.js src/crud_views/static/crud_views/js/modal.js
git commit -m "test(js): modal.js protocol tests; expose modal API on window.cv"
```

---

### Task 4: formset fixtures + XFormset tests + DELETE reorder fix

**Files:**
- Modify: `tests/js/helpers/dom.js` (add formset builders), `src/crud_views/static/crud_views/js/formset.js` (attachment block + one-line bugfix), `CHANGELOG.md`
- Create: `tests/js/formset.test.js`

**Interfaces:**
- Consumes: `loadScript` (Task 1).
- Produces (used by Tasks 5 and 6, all in `tests/js/helpers/dom.js`):
  - `formsetFixture(opts?): { prefix: string }` — renders a full `<form class="cv-form">` fixture into `document.body`. Options (all optional): `key="book"`, `pk="None"`, `index=0`, `rows=2`, `canOrder=true`, `canDelete=true`, `editOnly=false`, `fields=["name"]`, `pkField="id"`, `rowValues: string[]` (per-row `name` value; `""` makes a row empty; default `"row <i>"`), `rowDeleted: number[]` (row indices with `DELETE=1`).
  - `rowHtml(i: number, opts?): string` — one `.cv-formset-row` HTML string (same options).
  - `formsetPrefix(opts?): string` — `"<key>-<pk>-<index>"`, default `"book-None-0"`.
  - Source attachment: `window.cv.{CVFSConst, XBase, XFormset, XForm, CrudViewsFormset}`.

Background — read `formset.js` fully first. Key facts:
- `XFormset` is constructed with `(ctl, prefix)`; it reads JSON config from the `cv-data-formset` attribute of `.cv-formset-content`, parses `pk`/`index` out of `prefix_key` via `RegExp("^(.*)(None|<pk>)-(\\d+)$")`, and reads management-form inputs by `attr("value")`.
- `reorder()` numbers ORDER inputs 1..n for visible rows in DOM order; rows that are empty (all `fields` + pk field blank) or deleted get ORDER `""`.
- **Known bug (fixed in this task):** the deleted check reads `del.checked`, but the package renders DELETE as a *hidden* input (`Field("DELETE", type="hidden")` in `src/crud_views/lib/formsets/inline_formset.py:82`) and `XForm.set_delete()` writes value `"1"`/`"0"`. `.checked` is always `false` on hidden inputs, so delete-marked rows wrongly keep ORDER numbers. Server-side impact is nil today (Django's `ordered_forms` excludes deleted forms) but the JS behavior contradicts its own intent.
- The fixture markup mirrors `src/crud_views/templates/crud_views/formsets/formset.html` and `control.html`; JSON keys mirror `XFormSet.data` / `XForm.data` in `src/crud_views/lib/formsets/render_tree.py`.

- [ ] **Step 1: Add formset builders to `tests/js/helpers/dom.js`**

Append (and extend the file's header comment to mention the formset templates):

```js
// formsetFixture()/rowHtml() mirror:
//   src/crud_views/templates/crud_views/formsets/formset.html (+ control.html)
//   JSON: XFormSet.data / XForm.data in src/crud_views/lib/formsets/render_tree.py
// Keep in sync when those change.
const FORMSET_DEFAULTS = {
    key: "book",
    pk: "None",
    index: 0,
    rows: 2,
    canOrder: true,
    canDelete: true,
    editOnly: false,
    fields: ["name"],
    pkField: "id",
    rowValues: null,
    rowDeleted: [],
};

export function formsetPrefix(opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    return `${o.key}-${o.pk}-${o.index}`;
}

export function rowHtml(i, opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    const prefix = formsetPrefix(o);
    const formPrefix = `${prefix}-${i}`;
    const value = o.rowValues?.[i] ?? `row ${i}`;
    const deleted = o.rowDeleted.includes(i) ? "1" : "0";
    const formData = JSON.stringify({
        key: o.key,
        prefix: formPrefix,
        prefix_key: `${o.pk}-${o.index}-${i}`,
        formset_prefix: prefix,
        pk: o.pk,
    });
    const orderInput = o.canOrder
        ? `<input type="hidden" name="${formPrefix}-ORDER" value="${i + 1}">`
        : "";
    const deleteInput = o.canDelete
        ? `<input type="hidden" name="${formPrefix}-DELETE" value="${deleted}">`
        : "";
    const orderButtons = o.canOrder
        ? `<button type="button" class="btn btn-light cv-form-ctrl-up" cv-data-formset-form-prefix="${formPrefix}"></button>
           <button type="button" class="btn btn-light cv-form-ctrl-down" cv-data-formset-form-prefix="${formPrefix}"></button>`
        : "";
    const addButton = o.editOnly
        ? ""
        : `<button type="button" class="btn btn-light cv-form-ctrl-add" cv-data-formset-form-prefix="${formPrefix}"></button>`;
    const deleteButton = o.canDelete
        ? `<button type="button" class="btn btn-light cv-form-ctrl-delete" cv-data-formset-form-prefix="${formPrefix}"></button>`
        : "";
    return `
        <div class="cv-formset-row" cv-data-formset-form='${formData}'
             cv-data-formset-prefix="${prefix}" cv-data-formset-form-prefix="${formPrefix}">
            <div class="cv-formset-form">
                <input type="hidden" name="${formPrefix}-${o.pkField}" value="">
                <input type="text" name="${formPrefix}-${o.fields[0]}" value="${value}">
                ${orderInput}
                ${deleteInput}
                <div class="cv-form-ctrl">${orderButtons}${addButton}${deleteButton}</div>
            </div>
        </div>`;
}

export function formsetFixture(opts = {}) {
    const o = { ...FORMSET_DEFAULTS, ...opts };
    const prefix = formsetPrefix(o);
    const data = JSON.stringify({
        key: o.key,
        prefix,
        prefix_key: `${o.pk}-${o.index}`,
        hierarchy: [o.key],
        parent_prefix: "",
        parent_prefix_key: "",
        can_delete: o.canDelete,
        can_delete_extra: true,
        can_order: o.canOrder,
        edit_only: o.editOnly,
        path: "/formset-rows/",
        fields: o.fields,
        pk_field: o.pkField,
        pk: o.pk,
    });
    const rowsHtml = Array.from({ length: o.rows }, (_, i) => rowHtml(i, o)).join("");
    document.body.innerHTML = `
        <form class="cv-form">
            <fieldset class="cv-formset-fieldset" cv-data-formset-key="${o.key}" cv-data-formset-prefix="${prefix}">
                <div class="cv-formset-content" cv-data-formset='${data}' cv-data-formset-prefix="${prefix}">
                    <input type="hidden" name="${prefix}-TOTAL_FORMS" value="${o.rows}">
                    <input type="hidden" name="${prefix}-INITIAL_FORMS" value="${o.rows}">
                    <input type="hidden" name="${prefix}-MIN_NUM_FORMS" value="0">
                    <input type="hidden" name="${prefix}-MAX_NUM_FORMS" value="1000">
                    ${rowsHtml}
                </div>
            </fieldset>
        </form>`;
    return { prefix };
}
```

- [ ] **Step 2: Write the failing XFormset tests**

Create `tests/js/formset.test.js`:

```js
import { beforeAll, describe, expect, it } from "vitest";
import { loadScript } from "./helpers/load.js";
import { formsetFixture } from "./helpers/dom.js";

function orderValues() {
    return [...document.querySelectorAll("input[name$=-ORDER]")].map((el) => el.value);
}

describe("formset.js", () => {
    beforeAll(async () => {
        await loadScript("formset");
    });

    describe("XFormset", () => {
        it("parses config, pk and index from the fixture", () => {
            formsetFixture();
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(fs.prefix).toBe("book-None-0");
            expect(fs.pk).toBeNull();
            expect(fs.index).toBe(0);
            expect(fs.can_order).toBe(true);
            expect(fs.can_delete).toBe(true);
            expect(fs.rows).toHaveLength(2);
        });

        it("parses a concrete parent pk", () => {
            formsetFixture({ pk: "7" });
            const fs = new window.cv.XFormset(null, "book-7-0");
            expect(fs.pk).toBe("7");
            expect(fs.index).toBe(0);
        });

        it("reads and writes the management form", () => {
            formsetFixture({ rows: 2 });
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(fs.get_total_forms()).toBe(2);
            expect(fs.get_initial_forms()).toBe(2);
            expect(fs.get_min_num_forms()).toBe(0);
            expect(fs.get_max_num_forms()).toBe(1000);
            fs.increment_total_forms();
            expect(fs.get_total_forms()).toBe(3);
        });

        it("renumbers ORDER inputs 1..n in DOM order", () => {
            formsetFixture({ rows: 3 });
            document.querySelectorAll("input[name$=-ORDER]").forEach((el) => (el.value = "9"));
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "2", "3"]);
        });

        it("blanks ORDER for empty rows", () => {
            formsetFixture({ rows: 3, rowValues: ["a", "", "b"] });
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "", "2"]);
        });

        it("blanks ORDER for delete-marked rows (hidden DELETE input)", () => {
            formsetFixture({ rows: 3, rowDeleted: [1] });
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "", "2"]);
        });

        it("blanks ORDER for delete-marked rows (checkbox DELETE input)", () => {
            formsetFixture({ rows: 2 });
            const del = document.querySelector('input[name="book-None-0-1-DELETE"]');
            del.type = "checkbox";
            del.checked = true;
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", ""]);
        });

        it("does nothing when the formset is not orderable", () => {
            formsetFixture({ canOrder: false });
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(() => fs.reorder()).not.toThrow();
            expect(document.querySelectorAll("input[name$=-ORDER]")).toHaveLength(0);
        });
    });
});
```

- [ ] **Step 3: Run to verify failure**

Run: `npx vitest run tests/js/formset.test.js` — Expected: FAIL — `window.cv.XFormset` is undefined.

- [ ] **Step 4: Append the attachment block to formset.js**

At the end of `src/crud_views/static/crud_views/js/formset.js`, AFTER the existing `$(function () {...})` block, append:

```js
// Test seam: expose the formset classes on a shared namespace. In the browser
// these are top-level lexical globals reachable by other classic scripts but
// not inspectable via window; this adds namespaced access for the unit tests.
window.cv = window.cv || {};
Object.assign(window.cv, {CVFSConst, XBase, XFormset, XForm, CrudViewsFormset});
```

- [ ] **Step 5: Run to isolate the RED bug test**

Run: `npx vitest run tests/js/formset.test.js` — Expected: all pass EXCEPT `blanks ORDER for delete-marked rows (hidden DELETE input)` — actual `["1", "2", "3"]` because `del.checked` is always false on hidden inputs. This failure is the point: it reproduces the bug. (If the checkbox variant also fails, debug the fixture, not the source.)

- [ ] **Step 6: Fix the DELETE detection in formset.js**

In `XFormset.reorder()`, delete the line declaring `delete_checkbox = true,  // todo: from json` and change

```js
                deleted = delete_checkbox ? del.checked : del.value === "on";
```

to

```js
                // DELETE may render as a hidden input (crud_views default, value "1"/"0")
                // or as Django's checkbox
                deleted = del.type === "checkbox" ? del.checked : del.value === "1";
```

- [ ] **Step 7: Run to verify all pass**

Run: `npx vitest run` — Expected: 34 passed.

- [ ] **Step 8: Add the CHANGELOG entry**

At the top of `CHANGELOG.md`, directly under the `# Django CRUD Views - Changelog` heading, insert:

```markdown
## Unreleased

### Fixed

- `formset.js`: rows marked for deletion now lose their `ORDER` value during client-side
  reordering. The check read `.checked` on the hidden `DELETE` input (always false); it now
  inspects the input type. No server-side impact — Django's `ordered_forms` already
  excluded deleted forms.
```

(If an `## Unreleased` section already exists, add only the `### Fixed` entry to it.)

- [ ] **Step 9: Commit**

```bash
git add tests/js/formset.test.js tests/js/helpers/dom.js src/crud_views/static/crud_views/js/formset.js CHANGELOG.md
git commit -m "fix(formsets): blank ORDER for delete-marked rows in JS reorder; XFormset tests"
```

---

### Task 5: XForm behavior tests

**Files:**
- Modify: `tests/js/formset.test.js` (add a `describe("XForm")` block)

**Interfaces:**
- Consumes: `formsetFixture`, `rowHtml` (Task 4); `window.cv.XForm` (constructed as `new window.cv.XForm(ctl, formPrefix)` — `ctl` only needs `add_form_control_for_new_rows(rows)` for `add()`; pass `null` elsewhere).
- Produces: nothing used later.

Background: `XForm` wraps one `.cv-formset-row`. `delete()` toggles the hidden DELETE input between `"1"`/`"0"` (via the `value` *attribute*) and swaps the delete button between `btn-danger`/`btn-light`. `up()`/`down()` move the row in the DOM, then reorder. `add()` calls `$.ajax` GET against the formset's `path` and inserts `response.html` after the last row (when invoked from the last row) or before `row_next` otherwise, increments TOTAL_FORMS, reorders, and calls `ctl.add_form_control_for_new_rows(response.rows)`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/js/formset.test.js` (inside the outer `describe("formset.js")`; extend the imports line with `vi` from vitest and `rowHtml` from `./helpers/dom.js`):

```js
    describe("XForm", () => {
        it("computes row position facts", () => {
            formsetFixture({ rows: 3 });
            const middle = new window.cv.XForm(null, "book-None-0-1");
            expect(middle.rows_total).toBe(3);
            expect(middle.row_index).toBe(1);
            expect(middle.row_is_first).toBe(false);
            expect(middle.row_is_last).toBe(false);
            expect(middle.row_previous.attr("cv-data-formset-form-prefix")).toBe("book-None-0-0");
            expect(middle.row_next.attr("cv-data-formset-form-prefix")).toBe("book-None-0-2");

            const first = new window.cv.XForm(null, "book-None-0-0");
            expect(first.row_is_first).toBe(true);
            expect(first.row_previous).toBeNull();

            const last = new window.cv.XForm(null, "book-None-0-2");
            expect(last.row_is_last).toBe(true);
            expect(last.row_next).toBeNull();
        });

        it("delete() toggles the hidden DELETE input and button styling", () => {
            formsetFixture();
            const del = document.querySelector('input[name="book-None-0-0-DELETE"]');
            const btn = document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-0"]');

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(del.getAttribute("value")).toBe("1");
            expect(btn.classList.contains("btn-danger")).toBe(true);
            expect(btn.classList.contains("btn-light")).toBe(false);

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(del.getAttribute("value")).toBe("0");
            expect(btn.classList.contains("btn-light")).toBe(true);
        });

        function rowOrderInDom() {
            return [...document.querySelectorAll(".cv-formset-row")]
                .map((el) => el.getAttribute("cv-data-formset-form-prefix"));
        }

        it("up() moves the row before its predecessor and renumbers", () => {
            formsetFixture({ rows: 3 });
            new window.cv.XForm(null, "book-None-0-1").up();
            expect(rowOrderInDom()).toEqual(["book-None-0-1", "book-None-0-0", "book-None-0-2"]);
            expect(document.querySelector('input[name="book-None-0-1-ORDER"]').value).toBe("1");
            expect(document.querySelector('input[name="book-None-0-0-ORDER"]').value).toBe("2");
        });

        it("up() on the first row is a no-op", () => {
            formsetFixture({ rows: 2 });
            new window.cv.XForm(null, "book-None-0-0").up();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1"]);
        });

        it("down() moves the row after its successor and renumbers", () => {
            formsetFixture({ rows: 3 });
            new window.cv.XForm(null, "book-None-0-1").down();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-2", "book-None-0-1"]);
            expect(document.querySelector('input[name="book-None-0-1-ORDER"]').value).toBe("3");
        });

        it("down() on the last row is a no-op", () => {
            formsetFixture({ rows: 2 });
            new window.cv.XForm(null, "book-None-0-1").down();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1"]);
        });

        describe("add()", () => {
            function stubAjax(newIndex) {
                return vi.spyOn($, "ajax").mockImplementation((options) => {
                    options.success({ html: rowHtml(newIndex), rows: [`book-None-0-${newIndex}`] });
                });
            }

            it("requests a new row with the formset's coordinates", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-1").add();
                const options = ajax.mock.calls[0][0];
                expect(options.url).toBe("/formset-rows/");
                expect(options.type).toBe("get");
                expect(options.data).toEqual({
                    template: "book",
                    pk: "None",
                    num: 2,
                    formset_parent_prefix_key: "",
                });
                ajax.mockRestore();
            });

            it("appends after the last row, bumps TOTAL_FORMS and wires controls", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-1").add();
                expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1", "book-None-0-2"]);
                expect(document.querySelector('input[name="book-None-0-TOTAL_FORMS"]').getAttribute("value")).toBe("3");
                expect(ctl.add_form_control_for_new_rows).toHaveBeenCalledWith(["book-None-0-2"]);
                ajax.mockRestore();
            });

            it("inserts before the next row when adding from a middle row", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-0").add();
                expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-2", "book-None-0-1"]);
                ajax.mockRestore();
            });
        });
    });
```

- [ ] **Step 2: Run to verify state**

Run: `npx vitest run tests/js/formset.test.js` — Expected: all PASS (characterization of existing behavior — Task 4's fix already landed). If a test fails, debug the TEST/fixture first; only touch `formset.js` if you can demonstrate the browser would misbehave identically, and then STOP and report instead of fixing (out of this task's scope).

- [ ] **Step 3: Run the full suite**

Run: `npx vitest run` — Expected: 44 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/js/formset.test.js
git commit -m "test(js): XForm row behavior tests (move, delete, add)"
```

---

### Task 6: CrudViewsFormset controller tests

**Files:**
- Modify: `tests/js/formset.test.js` (add a `describe("CrudViewsFormset")` block)

**Interfaces:**
- Consumes: `formsetFixture` (Task 4); `window.cv.CrudViewsFormset` (constructed with no arguments AFTER the fixture exists).

Background: the constructor binds click handlers to the up/down/add/delete buttons and a submit handler on `form.cv-form` that reorders all formsets and calls `preventDefault()` if reordering fails. Regression guard (fixed 2026-07-19): on the *global* init pass, absent control types (e.g. no up/down buttons on a non-orderable formset) must NOT abort initialization.

- [ ] **Step 1: Write the tests**

Add to `tests/js/formset.test.js`:

```js
    describe("CrudViewsFormset", () => {
        it("initializes on a non-orderable formset without aborting (regression)", () => {
            formsetFixture({ canOrder: false });
            expect(() => new window.cv.CrudViewsFormset()).not.toThrow();
            // delete still works, proving handlers were bound despite missing up/down
            document.querySelector("button.cv-form-ctrl-delete").click();
            expect(document.querySelector('input[name="book-None-0-0-DELETE"]').getAttribute("value")).toBe("1");
        });

        it("initializes on an edit-only formset without an add button", () => {
            formsetFixture({ editOnly: true });
            expect(() => new window.cv.CrudViewsFormset()).not.toThrow();
            document.querySelector("button.cv-form-ctrl-delete").click();
            expect(document.querySelector('input[name="book-None-0-0-DELETE"]').getAttribute("value")).toBe("1");
        });

        it("wires the control buttons to row actions", () => {
            formsetFixture({ rows: 2 });
            new window.cv.CrudViewsFormset();
            document.querySelector('button.cv-form-ctrl-down[cv-data-formset-form-prefix="book-None-0-0"]').click();
            const prefixes = [...document.querySelectorAll(".cv-formset-row")]
                .map((el) => el.getAttribute("cv-data-formset-form-prefix"));
            expect(prefixes).toEqual(["book-None-0-1", "book-None-0-0"]);
        });

        it("reorders all formsets on submit and lets the submit proceed", () => {
            formsetFixture({ rows: 2 });
            new window.cv.CrudViewsFormset();
            document.querySelectorAll("input[name$=-ORDER]").forEach((el) => (el.value = "9"));
            const form = document.querySelector("form.cv-form");
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(false);
            expect([...document.querySelectorAll("input[name$=-ORDER]")].map((el) => el.value)).toEqual(["1", "2"]);
        });

        it("blocks the submit when reordering fails outright", () => {
            formsetFixture({ rows: 2 });
            const controller = new window.cv.CrudViewsFormset();
            const form = document.querySelector("form.cv-form");
            // make reorder_formsets throw: the controller can no longer find form.cv-form
            form.className = "";
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
        });
    });
```

- [ ] **Step 2: Run to verify state**

Run: `npx vitest run tests/js/formset.test.js` — Expected: all PASS (characterization). Note: the submit tests dispatch a native cancelable `submit` event; jQuery's handler runs and `defaultPrevented` reflects its decision. If the "blocks the submit" test fails because jQuery's submit binding no longer matches after the class removal, the handler was bound directly to the element and still fires — debug with `npx vitest run -t "blocks the submit"` before touching anything.

- [ ] **Step 3: Run the full suite**

Run: `npx vitest run` — Expected: 49 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/js/formset.test.js
git commit -m "test(js): CrudViewsFormset controller init and submit tests"
```

---

### Task 7: Coverage wiring

**Files:**
- Modify: `package.json` (deps), `vitest.config.js`, `tests/js/helpers/load.js`

**Interfaces:**
- Consumes: everything prior.
- Produces: `npm run coverage` reporting on the three source files.

Rationale: sources execute via `new Function`, which neither the v8 nor the istanbul provider can see on its own. The loader therefore instruments the source with `istanbul-lib-instrument` (keyed by the real file path); counters accumulate in `globalThis.__coverage__`, which Vitest's istanbul provider collects and reports.

- [ ] **Step 1: Install coverage tooling**

```bash
npm install --save-dev @vitest/coverage-istanbul istanbul-lib-instrument
```

- [ ] **Step 2: Configure coverage**

In `vitest.config.js`, add inside `test: {}`:

```js
        coverage: {
            provider: "istanbul",
            include: ["src/crud_views/static/crud_views/js/**"],
            reporter: ["text", "html"],
            reportsDirectory: "coverage-js",
        },
```

- [ ] **Step 3: Instrument in the loader**

In `tests/js/helpers/load.js`, add the import and change `loadScript`:

```js
import { createInstrumenter } from "istanbul-lib-instrument";

const instrumenter = createInstrumenter({ esModules: false });
```

```js
export async function loadScript(name) {
    const file = `${JS_DIR}${name}.js`;
    // Instrument for coverage: the code runs via new Function, invisible to the
    // istanbul provider; instrumented counters land in globalThis.__coverage__
    // where vitest collects them. Cheap enough to do unconditionally.
    const code = instrumenter.instrumentSync(fs.readFileSync(file, "utf-8"), file);
    new Function("window", code)(testWindow());
    // jQuery defers $(document).ready() callbacks by a microtask even when the
    // document is already complete; wait for them so wiring is done on return.
    await new Promise((resolve) => window.jQuery(resolve));
}
```

- [ ] **Step 4: Verify tests still pass, then verify coverage**

Run: `npx vitest run` — Expected: 49 passed.
Run: `npm run coverage` — Expected: 49 passed plus a text coverage table listing `formset.js`, `modal.js`, `toggle.js` with non-zero statement coverage (roughly 80%+ for toggle/modal; formset lower), and nothing outside `src/crud_views/static/crud_views/js/`.

Contingency: if the table is empty, the provider is dropping externally-produced coverage entries. Check `coverage-js/index.html`; if genuinely empty, revert Steps 2–3 (`git checkout -- vitest.config.js tests/js/helpers/load.js`, `npm uninstall @vitest/coverage-istanbul istanbul-lib-instrument`), commit the plan WITHOUT coverage, and report coverage wiring as a follow-up — coverage is a local-only nice-to-have per the spec; do not burn time on it.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json vitest.config.js tests/js/helpers/load.js
git commit -m "test(js): istanbul coverage for the static JS sources"
```

---

### Task 8: CI workflow, Taskfile, docs, changelog

**Files:**
- Create: `.github/workflows/js.yml`
- Modify: `taskfile.yaml`, `CONTRIBUTING.md`, `docs/development/index.md`, `CHANGELOG.md`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/js.yml`:

```yaml
name: JS Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  js-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npx vitest run
```

- [ ] **Step 2: Add Taskfile tasks**

In `taskfile.yaml`, after the existing `test:` task, add:

```yaml
  test-js:
    desc: Run the JS unit tests (Vitest + jsdom, requires Node 20+)
    cmds:
      - test -d node_modules || npm ci
      - npx vitest run
    silent: true

  test-js-watch:
    desc: Run the JS unit tests in watch mode
    cmds:
      - test -d node_modules || npm ci
      - npx vitest
    silent: true
```

Verify: `task test-js` — Expected: 49 passed.

- [ ] **Step 3: Document**

In `CONTRIBUTING.md`, change the "Run the tests" list item:

```markdown
3. Run the tests:
   - quick: `cd tests && pytest`
   - full matrix (Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0): `task test`
   - JS unit tests (requires Node 20+): `task test-js`
```

In `docs/development/index.md`, after the `## Setup` section (before `## Run example application`), add:

````markdown
## JS tests

The package's static JavaScript (`formset.js`, `modal.js`, `toggle.js`) has a
[Vitest](https://vitest.dev/) unit-test suite. It needs [Node.js](https://nodejs.org/) 20+:

```bash
task test-js
```
````

- [ ] **Step 4: Changelog**

In `CHANGELOG.md`, inside the `## Unreleased` section created in Task 4, add an `### Added` subsection above `### Fixed`:

```markdown
### Added

- JS unit-test harness (Vitest + jsdom) for the package's static JavaScript
  (`formset.js`, `modal.js`, `toggle.js`), with a `JS Tests` CI workflow and a
  `task test-js` shortcut. Dev-only; does not affect the package.
```

- [ ] **Step 5: Final verification**

Run: `npx vitest run` — Expected: 49 passed.
Run: `cd tests && pytest -q && cd ..` — Expected: all Python tests still pass (the formset.js/modal.js edits are the only source changes; Python tests don't execute JS, this is a sanity check).

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/js.yml taskfile.yaml CONTRIBUTING.md docs/development/index.md CHANGELOG.md
git commit -m "ci(js): JS test workflow, task test-js, contributor docs"
```
