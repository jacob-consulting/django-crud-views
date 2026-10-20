# JavaScript Adapters and jQuery-Free Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Core crud_views pages work without jQuery and without a global named `bootstrap`: every UI-library call
goes through `cv.adapters`, three scripts go vanilla, and the modal size becomes a semantic token.

**Architecture:** A new first core script `adapters.js` defines `cv.adapters` (`modal`, `tooltip`, `collapse`) with
Bootstrap defaults that resolve `globalThis.bootstrap` at call time, plus `cv.bootstrapAdapters(ns)` for any
Bootstrap-compatible namespace (Tabler, an ESM import). `modal.js`, `list.filter.js` and `viewset.js` are rewritten
on the DOM API and call adapters only; `tooltip.js` delegates to the tooltip adapter; `formset.js` stays on jQuery
behind a load guard. The modal shell gets its own template, the partial's close button dismisses through the adapter,
and `cv_modal_size` accepts `""`, `"sm"`, `"lg"`, `"xl"` only.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12+, pytest + pytest-django + lxml; classic browser JavaScript (no
modules, no bundler); Vitest 5 + jsdom 30 (`tests/js/`), jQuery 3.7 as a dev dependency for the formset tests;
MkDocs with awesome-pages.

**Spec:** `superpowers/specs/2026-10-20-js-adapters-jquery-free-core-design.md` (read it first; this plan argues from
it). Background: `tabler-test/docs/crud_views_upstream_questions.md` point 3.

## Global Constraints

- Scripts stay classic `<script>` files served by Django unchanged: no ES modules, no build step, no inline code
  (CSP). Navigate only through `globalThis.location.assign(...)` / `globalThis.location.href = ...`; the JS test
  harness proxies `location` to a stub (`tests/js/helpers/load.js`).
- After this plan, `viewset.js`, `modal.js`, `list.filter.js` and `tooltip.js` contain none of the tokens `bootstrap`,
  `jQuery`, `$(`, `$.` (Task 6 adds the guard test). The only file that spells `bootstrap` is `adapters.js`.
- Adapter contract (public API, exact names): `cv.adapters.modal.show(modalEl)`, `cv.adapters.modal.hide(modalEl)`,
  `cv.adapters.modal.setSize(dialogEl, size)`, `cv.adapters.tooltip.init(el)`, `cv.adapters.collapse.toggle(el)`,
  `cv.bootstrapAdapters(ns)` where `ns` is an object or a function returning one, resolved on every call.
- `cv_modal_size` values: exactly `""`, `"sm"`, `"lg"`, `"xl"`. No deprecation path for `modal-*`.
- Shell ids are the contract: `cv-modal`, `cv-modal-dialog`, `cv-modal-content`. Dismiss attribute:
  `data-cv-modal-dismiss`. Trigger: `[data-cv-modal='true']` with `data-cv-modal-size="<token>"`.
- Core script order in `CrudViewsSettings.javascript()`: adapters, viewset, formset, list_filter, modal, toggle,
  tooltip. `cv_sources("js")`, `{% cv_js %}` and `manage.py cv_assets` derive from it.
- jQuery is required only on pages with formsets (present by DOMContentLoaded) and by jQuery-based extensions.
- Python: ruff, line length 120, double quotes. Conventional Commits. Pre-commit runs ruff check + format.
- Markdown: CI runs `ruff format --check .` with ruff 0.16, which also formats Python blocks inside Markdown. The
  venv ruff is 0.15.11 and does not; before pushing docs run `uvx ruff@0.16.0 format --check .` (and `format .` to fix).
- JS tests: `task test-js` (`npx vitest run`). They need Node 22 (CI uses it, `.github/workflows/js.yml`). The
  local Node 20.20.2 fails every file with `webidl.util.markAsUncloneable is not a function` (jsdom/undici); that is
  the environment, not a regression. Use `npx -p node@22 vitest run` or a Node 22 install; otherwise rely on CI.
- Python tests: `pytest tests` from the repo root (venv at `.venv`). Golden fixtures regenerate only with
  `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`, and only when the default markup is meant
  to change.
- `CHANGELOG.md`: add entries under a new `## Unreleased` heading at the top (the release step renames it). Do not
  bump the version.
- Keep `console.log` out of shipped scripts (`list.filter.js` loses its chatter); `console.error` is the only
  logging the scripts do, for the two documented failure cases.

## Review Focus

1. A Ctrl/Cmd/Shift-click or non-primary-button click on a modal trigger must open the full page in a new tab, not
   the modal: the delegated handler skips modified clicks (test in Task 3).
2. A `[data-cv-action='submit-form']` whose `data-cv-target` names no element must do nothing, never throw (test in
   Task 5).
3. If the filter-state POST fails (network error), the panel still toggles and no unhandled rejection reaches the
   console (test in Task 4).
4. A `[data-cv-modal-dismiss]` click before any modal was opened: the Bootstrap adapter's `hide` tolerates
   `Modal.getInstance` returning `null` (test in Task 1).
5. jQuery loaded after `formset.js` but before DOMContentLoaded (deferred jQuery): the formset guard checks at
   DOMContentLoaded, so the controller still starts (test in Task 6).

---

### Task 1: `adapters.js`, settings order, harness without jQuery

**Files:**
- Create: `src/crud_views/static/crud_views/js/adapters.js`
- Create: `tests/js/adapters.test.js`
- Modify: `src/crud_views/lib/settings.py:199-209` (`javascript()`)
- Modify: `tests/js/helpers/load.js:38-46` (`loadScript`)
- Modify: `tests/test1/test_pipeline_sources.py:8-15,38`, `tests/test1/test_assets_bundles.py:5-12`,
  `tests/test1/test_pipeline_integration.py:8-15`, `tests/test1/test_pipeline_resolver.py:5-12,118-126`,
  `tests/test1/test_cv_assets_command.py:18,22`

**Interfaces:**
- Produces: `globalThis.cv` (created if absent); `cv.bootstrapAdapters(ns) -> {modal, tooltip, collapse}`;
  `cv.adapters` pre-filled with `cv.bootstrapAdapters(() => globalThis.bootstrap)`, merged under any entries a script
  assigned before this one loaded. Errors thrown by `modal.show` and `collapse.toggle` without the namespace match
  `/Bootstrap 5 JavaScript not loaded/`. `modal.setSize` writes `dialogEl.className`:
  `"modal-dialog"`, `"modal-dialog modal-sm"`, `"modal-dialog modal-lg"`, `"modal-dialog modal-xl"`; unknown token
  gives `"modal-dialog"`.
- Produces: `loadScript(name)` in the harness waits for jQuery's ready queue only when `typeof window.jQuery ===
  "function"`, so scripts load with `$`/`jQuery` stubbed to `undefined`.
- Produces: `crud_views_settings.javascript()["adapters"] == "crud_views/js/adapters.js"`, first key.

- [ ] **Step 1: Write the failing JS tests** in `tests/js/adapters.test.js`

```js
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fakeNamespace() {
    const instance = { show: vi.fn(), hide: vi.fn() };
    const collapse = { toggle: vi.fn() };
    return {
        instance, collapse,
        Modal: { getOrCreateInstance: vi.fn(() => instance), getInstance: vi.fn(() => instance) },
        Tooltip: { getOrCreateInstance: vi.fn((el) => ({ el })) },
        Collapse: { getOrCreateInstance: vi.fn(() => collapse) },
    };
}

describe("adapters.js", () => {
    beforeEach(() => { document.body.innerHTML = '<div id="m"><div id="d"></div></div><span id="t"></span>'; });
    afterEach(() => { vi.unstubAllGlobals(); delete window.cv; });

    it("defines cv.adapters.modal/tooltip/collapse and cv.bootstrapAdapters", async () => {
        await loadScript("adapters");
        expect(typeof window.cv.bootstrapAdapters).toBe("function");
        for (const name of ["modal", "tooltip", "collapse"]) expect(window.cv.adapters[name]).toBeDefined();
    });

    it("modal.show / hide drive Modal.getOrCreateInstance / getInstance", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), a = window.cv.bootstrapAdapters(ns), m = document.getElementById("m");
        a.modal.show(m);
        expect(ns.Modal.getOrCreateInstance).toHaveBeenCalledWith(m);
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
        a.modal.hide(m);
        expect(ns.instance.hide).toHaveBeenCalledTimes(1);
    });

    it("modal.hide tolerates a missing instance", async () => {           // Review Focus 4
        await loadScript("adapters");
        const ns = fakeNamespace(); ns.Modal.getInstance = vi.fn(() => null);
        expect(() => window.cv.bootstrapAdapters(ns).modal.hide(document.getElementById("m"))).not.toThrow();
    });

    it.each([["", "modal-dialog"], ["sm", "modal-dialog modal-sm"], ["lg", "modal-dialog modal-lg"],
             ["xl", "modal-dialog modal-xl"], ["huge", "modal-dialog"]])("setSize(%j) -> %j", async (size, cls) => {
        await loadScript("adapters");
        const d = document.getElementById("d"); d.className = "modal-dialog modal-xl";
        window.cv.bootstrapAdapters(fakeNamespace()).modal.setSize(d, size);
        expect(d.className).toBe(cls);
    });

    it("tooltip.init uses Tooltip.getOrCreateInstance and is silent without it", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), t = document.getElementById("t");
        window.cv.bootstrapAdapters(ns).tooltip.init(t);
        expect(ns.Tooltip.getOrCreateInstance).toHaveBeenCalledWith(t);
        expect(() => window.cv.bootstrapAdapters({}).tooltip.init(t)).not.toThrow();
    });

    it("collapse.toggle uses Collapse.getOrCreateInstance(el).toggle()", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), d = document.getElementById("d");
        window.cv.bootstrapAdapters(ns).collapse.toggle(d);
        expect(ns.Collapse.getOrCreateInstance).toHaveBeenCalledWith(d);
        expect(ns.collapse.toggle).toHaveBeenCalledTimes(1);
    });

    it("modal.show and collapse.toggle throw a clear error without the namespace", async () => {
        await loadScript("adapters");
        const a = window.cv.bootstrapAdapters(undefined);
        expect(() => a.modal.show(document.getElementById("m"))).toThrow(/Bootstrap 5 JavaScript not loaded/);
        expect(() => a.collapse.toggle(document.getElementById("d"))).toThrow(/Bootstrap 5 JavaScript not loaded/);
    });

    it("resolves a function namespace at call time", async () => {
        await loadScript("adapters");
        let ns = null;
        const a = window.cv.bootstrapAdapters(() => ns), m = document.getElementById("m");
        expect(() => a.modal.show(m)).toThrow();
        ns = fakeNamespace();
        a.modal.show(m);
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
    });

    it("default adapters look up globalThis.bootstrap lazily", async () => {
        await loadScript("adapters");                       // no bootstrap yet
        const ns = fakeNamespace();
        vi.stubGlobal("bootstrap", ns);                     // Bootstrap's bundle loads after cv_js
        window.cv.adapters.modal.show(document.getElementById("m"));
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
    });

    it("keeps adapters assigned before the script loaded and fills the rest", async () => {
        const custom = { show: vi.fn(), hide: vi.fn(), setSize: vi.fn() };
        window.cv = { adapters: { modal: custom } };
        await loadScript("adapters");
        expect(window.cv.adapters.modal).toBe(custom);
        expect(window.cv.adapters.tooltip).toBeDefined();
        expect(window.cv.adapters.collapse).toBeDefined();
    });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx vitest run tests/js/adapters.test.js`
Expected: FAIL, `ENOENT ... adapters.js` from `loadScript`.

- [ ] **Step 3: Write `src/crud_views/static/crud_views/js/adapters.js`**

Classic script, one IIFE. Skeleton (the resolution rule is the part the tests do not pin):

```js
// src/crud_views/static/crud_views/js/adapters.js
// cv.adapters: the only place crud_views scripts touch a UI library. Themes replace entries;
// cv.bootstrapAdapters(ns) builds all three for any Bootstrap-compatible namespace.
globalThis.cv = globalThis.cv || {};
(function (cv) {
    const SIZE_CLASSES = Object.freeze({sm: "modal-sm", lg: "modal-lg", xl: "modal-xl"});
    function resolve(ns) { return (typeof ns === "function" ? ns() : ns) || null; }
    function component(ns, name) { const n = resolve(ns); return n && n[name] ? n[name] : null; }
    function missing(name) {
        return new Error(`cv.adapters: Bootstrap 5 JavaScript not loaded (no ${name} on the namespace); load Bootstrap's bundle or assign cv.adapters.`);
    }
    cv.bootstrapAdapters = function (ns) {
        return {
            modal: {
                show(modalEl) { const Modal = component(ns, "Modal"); if (!Modal) throw missing("Modal"); Modal.getOrCreateInstance(modalEl).show(); },
                hide(modalEl) { component(ns, "Modal")?.getInstance(modalEl)?.hide(); },
                setSize(dialogEl, size) { dialogEl.className = "modal-dialog" + (SIZE_CLASSES[size] ? " " + SIZE_CLASSES[size] : ""); },
            },
            tooltip: { init(el) { component(ns, "Tooltip")?.getOrCreateInstance(el); } },
            collapse: { toggle(el) { const Collapse = component(ns, "Collapse"); if (!Collapse) throw missing("Collapse"); Collapse.getOrCreateInstance(el).toggle(); } },
        };
    };
    cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
})(globalThis.cv);
```

- [ ] **Step 4: Make the harness independent of jQuery** in `tests/js/helpers/load.js`

Replace the unconditional `await new Promise((resolve) => window.jQuery(resolve));` with the same wait guarded by
`typeof window.jQuery === "function"`. Update the comment: the wait exists for `formset.js`, which still queues its
start-up on jQuery's ready; the other scripts need no jQuery.

- [ ] **Step 5: Run the JS tests**

Run: `npx vitest run tests/js/adapters.test.js tests/js/harness.test.js`
Expected: PASS (10 + 2).

- [ ] **Step 6: Write the failing Python test** in `tests/test1/test_pipeline_sources.py`

Add `"crud_views/js/adapters.js"` as the first element of `CORE_JS` and change `assert len(sources) == 7` to
`== 8`. Add:

```python
def test_adapters_is_the_first_core_script():
    from crud_views.lib.settings import crud_views_settings

    keys = list(crud_views_settings.javascript().keys())
    assert keys == ["adapters", "viewset", "formset", "list_filter", "modal", "toggle", "tooltip"]
```

- [ ] **Step 7: Run it to verify it fails**

Run: `pytest tests/test1/test_pipeline_sources.py -v`
Expected: FAIL on the key list and on `CORE_JS`.

- [ ] **Step 8: Add the entry** `"adapters": self.get_js("adapters.js")` as the first item of the `Box` in
`CrudViewsSettings.javascript()` (`src/crud_views/lib/settings.py:199`).

- [ ] **Step 9: Update the other pinned lists**

`tests/test1/test_assets_bundles.py:5`, `tests/test1/test_pipeline_integration.py:8`,
`tests/test1/test_pipeline_resolver.py:5`: prepend `"crud_views/js/adapters.js"` to `CORE_JS`.
`tests/test1/test_pipeline_resolver.py:123-124`: `["js"] * 7`, `rows[:7]`.
`tests/test1/test_cv_assets_command.py:18`: the first data row is now `["crud_views", "js", "tag",
"crud_views/js/adapters.js"]`; line 22: `1 + 11 + 2`.

- [ ] **Step 10: Run the Python suite**

Run: `pytest tests -q`
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add src/crud_views/static/crud_views/js/adapters.js src/crud_views/lib/settings.py tests/js/adapters.test.js tests/js/helpers/load.js tests/test1/test_pipeline_sources.py tests/test1/test_assets_bundles.py tests/test1/test_pipeline_integration.py tests/test1/test_pipeline_resolver.py tests/test1/test_cv_assets_command.py
git commit -m "feat(js): cv.adapters with Bootstrap defaults and cv.bootstrapAdapters(ns)"
```

---

### Task 2: Modal templates and semantic size tokens

**Files:**
- Create: `src/crud_views/templates/crud_views/modal/shell.html`
- Modify: `src/crud_views/templates/crud_views/tags/cv_config.html`,
  `src/crud_views/templates/crud_views/modal/content.html:4`,
  `src/crud_views/lib/view/base.py:83,127-132`, `tests/test1/app/views.py:899`
- Test: `tests/test1/test_modal.py`

**Interfaces:**
- Produces: `crud_views/modal/shell.html` rendering the three ids; `tags/cv_config.html` = the `#cv-config` div plus
  `{% include "crud_views/modal/shell.html" %}`; the partial's close button carries `data-cv-modal-dismiss` and no
  `data-bs-dismiss`; `CrudView.cv_modal_size` documented as `"" | "sm" | "lg" | "xl"`; check `viewset.E250` message:
  `cv_modal_size must be one of '', 'sm', 'lg', 'xl' (Bootstrap class names such as 'modal-lg' are no longer
  accepted, use 'lg'), got {value!r}`.
- Consumes: nothing from Task 1.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_modal.py`

Change `test_check_modal_size_valid_values` to iterate `("", "sm", "lg", "xl")`. Add (reuse the file's
`check_ids` helper and `MODAL_HEADERS`; for the message, collect the Django messages the same way `check_ids` does
and read `.msg`):

```python
def test_check_modal_size_rejects_bootstrap_class_names():
    from crud_views.lib.views import DeleteView

    class OldSizeDeleteView(DeleteView):
        cv_modal = True
        cv_modal_size = "modal-lg"

    messages = [m for m in check_messages(OldSizeDeleteView) if m.id == "viewset.E250"]
    assert len(messages) == 1
    assert "'modal-lg'" in messages[0].msg and "use 'lg'" in messages[0].msg


def test_check_modal_size_none_is_reported_not_crashed():
    from crud_views.lib.views import DeleteView

    class NoneSizeDeleteView(DeleteView):
        cv_modal = True
        cv_modal_size = None

    assert "viewset.E250" in check_ids(NoneSizeDeleteView)


@pytest.mark.django_db
def test_modal_partial_close_button_dismisses_through_crud_views(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/delete/", headers=MODAL_HEADERS)
    content = response.content.decode()
    assert 'class="btn-close" data-cv-modal-dismiss' in content
    assert "data-bs-dismiss" not in content


@pytest.mark.django_db
def test_modal_trigger_renders_size_token(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.get("/author_modal/")
    assert 'data-cv-modal-size="lg"' in response.content.decode()


def test_modal_shell_template_renders_the_three_ids():
    from django.template.loader import render_to_string

    html = render_to_string("crud_views/modal/shell.html")
    for element_id in ("cv-modal", "cv-modal-dialog", "cv-modal-content"):
        assert f'id="{element_id}"' in html
```

(`check_messages` does not exist yet: add it next to `check_ids` in the same file, returning the message objects
`check_ids` derives its ids from.)

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_modal.py -v`
Expected: FAIL: valid-values test (E250 fires for `"sm"`), class-name test (no E250 for `"modal-lg"`), dismiss test,
size-token test (`app/views.py` still says `"modal-lg"`, which now also fails E250 at import of the test app:
fix Step 4 first if the whole module errors), shell template missing.

- [ ] **Step 3: Templates**

Create `crud_views/modal/shell.html` with exactly the shell markup now inside `tags/cv_config.html` (the
`div.modal.fade#cv-modal` block). Reduce `tags/cv_config.html` to the `#cv-config` div followed by
`{% include "crud_views/modal/shell.html" %}`. In `modal/content.html` replace `data-bs-dismiss="modal"` with
`data-cv-modal-dismiss` on the close button; keep `class="btn-close"` and the `aria-label`.

- [ ] **Step 4: Python**

`src/crud_views/lib/view/base.py:83`: comment `# "" | "sm" | "lg" | "xl" (semantic; the modal adapter maps them)`.
Lines 127-132: `expression=cls.cv_modal_size in ("", "sm", "lg", "xl")` and the message from Interfaces.
`tests/test1/app/views.py:899`: `cv_modal_size = "lg"`.

- [ ] **Step 5: Run the tests**

Run: `pytest tests/test1/test_modal.py tests/test1/od/test_object_detail_view.py tests/test1/test_card_action_post.py -v`
Expected: PASS (`modal-huge` in the object-detail test still fails E250, as intended).

- [ ] **Step 6: Run the full Python suite and the goldens**

Run: `pytest tests -q`
Expected: PASS. `tests/test1/golden/action_menus/list_full.html` contains `data-cv-modal-size=""`, which is
unchanged; do not regenerate here.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/templates/crud_views/modal/shell.html src/crud_views/templates/crud_views/tags/cv_config.html src/crud_views/templates/crud_views/modal/content.html src/crud_views/lib/view/base.py tests/test1/app/views.py tests/test1/test_modal.py
git commit -m "feat(modal)!: shell template, data-cv-modal-dismiss and semantic cv_modal_size tokens"
```

---

### Task 3: `modal.js` on the DOM API and the modal adapter

**Files:**
- Modify: `src/crud_views/static/crud_views/js/modal.js`
- Modify: `tests/js/modal.test.js`, `tests/js/helpers/dom.js:1-9` (`modalSkeleton`)

**Interfaces:**
- Consumes: `cv.adapters.modal.{show, hide, setSize}` (Task 1), the shell ids and `data-cv-modal-dismiss` (Task 2).
- Produces: unchanged exports `cv.cvModalOpen(url, size)`, `cv.cvModalSubmit(form)`, `cv.cvModalInject(html)`,
  `cv.cvModalElements()`, `cv.CVModalConst` extended with `dismissAttr: "data-cv-modal-dismiss"`,
  `sizeAttr: "data-cv-modal-size"`, `trigger: "[data-cv-modal='true']"`. `cvModalElements()` throws only
  `/#cv-modal not found/`. The HTTP protocol (`X-CV-Modal`, 204 + `X-CV-Redirect`, 422, fallbacks) is untouched.

- [ ] **Step 1: Update the fixture and write the failing tests**

`modalSkeleton()` in `helpers/dom.js`: keep the markup, and in the test file inject the close button where needed
(`<button type="button" class="btn-close" data-cv-modal-dismiss></button>` inside `#cv-modal-content`).

In `tests/js/modal.test.js`:
- `beforeEach`: after `modalSkeleton()`, set `show = vi.fn(); hide = vi.fn(); setSize = vi.fn();
  window.cv = { ...window.cv, adapters: { modal: { show, hide, setSize } } };` (no `bootstrap` stub anywhere).
- Rewrite the assertions on `#cv-modal-dialog`'s `className` as `expect(setSize).toHaveBeenCalledWith(
  document.getElementById("cv-modal-dialog"), "lg")` (and `""`, `"xl"` in the respective tests).
- `show` assertions become `expect(show).toHaveBeenCalledWith(document.getElementById("cv-modal"))`.
- Delete `throws a descriptive error when Bootstrap is missing`; keep the `#cv-modal not found` guard.
- Add:

```js
it("dismiss clicks inside the shell call adapter.hide with #cv-modal", () => {
    document.getElementById("cv-modal-content").innerHTML = '<button type="button" data-cv-modal-dismiss></button>';
    const button = document.querySelector("[data-cv-modal-dismiss]");
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    button.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    expect(hide).toHaveBeenCalledWith(document.getElementById("cv-modal"));
});

it("logs and falls back to navigation when adapter.show throws", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    show.mockImplementation(() => { throw new Error("no bootstrap"); });
    stubFetch(textResponse("<p>x</p>"));
    window.cv.cvModalOpen("/books/create/", "");
    await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
    expect(error).toHaveBeenCalledTimes(1);
});

it("leaves modified clicks to the browser", () => {                         // Review Focus 1
    stubFetch(textResponse("<p>x</p>"));
    document.body.insertAdjacentHTML("beforeend", `<a href="/books/1/delete/" data-cv-modal="true" data-cv-modal-size="lg">del</a>`);
    const link = document.querySelector("a[data-cv-modal]");
    for (const init of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { button: 1 }]) {
        const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
        link.dispatchEvent(event);
        expect(event.defaultPrevented).toBe(false);
    }
    expect(fetch).not.toHaveBeenCalled();
});

it("loads and wires its handlers without jQuery", async () => {
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    await expect(loadScript("modal")).resolves.toBeUndefined();
    vi.unstubAllGlobals();   // then re-stub $ and jQuery from the jquery import if later tests in the file need them
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `npx vitest run tests/js/modal.test.js`
Expected: FAIL (`bootstrap` undefined in `cvModalElements`, `hide` never called, click handler reads `$`).

- [ ] **Step 3: Rewrite the library-facing and jQuery parts of `modal.js`**

Keep `CVModalConst` (add the three keys), `cvModalInject`, the fetch chains and their fallbacks. Change:
- `cvModalElements()`: drop the `bootstrap` check.
- `cvModalOpen`: inside the success branch call `cv.adapters.modal.setSize(els.dialog, size)` and
  `cv.adapters.modal.show(els.modal)`; the existing `.catch` now also does `console.error(error)` before
  `globalThis.location.assign(url)`.
- Replace the `$(document).ready` block with three `document.addEventListener` registrations at script execution:
  `click` → if `event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey` return; then
  `closest(CVModalConst.trigger)` opens with `href` and `data-cv-modal-size`; else `closest("[" +
  CVModalConst.dismissAttr + "]")` within `#cv-modal` calls `cv.adapters.modal.hide(els.modal)`; `submit` →
  `event.target.closest("#cv-modal-content")` posts. All three `preventDefault()`.

- [ ] **Step 4: Run the tests**

Run: `npx vitest run tests/js/modal.test.js tests/js/adapters.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/modal.js tests/js/modal.test.js tests/js/helpers/dom.js
git commit -m "refactor(js): modal.js without jQuery, show/hide/size through cv.adapters.modal"
```

---

### Task 4: Filter toggle: `aria-expanded`, `list.filter.js` on fetch and the collapse adapter

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/context_action_filter.html`,
  `src/crud_views/static/crud_views/js/list.filter.js`
- Modify: `tests/js/list.filter.test.js`, `tests/test1/test_filter.py`, `tests/test1/test_template_a11y.py:86-90`
- Regenerate: `tests/test1/golden/action_menus/toolbar_publisher_list.html`

**Interfaces:**
- Consumes: `cvGetConfig()` from `viewset.js` (global function, unchanged: `{csrfToken, request: {path,
  query_string}}`), `cv.adapters.collapse.toggle(el)` (Task 1).
- Produces: the toggle button renders `aria-expanded="true"|"false"` from `cv_filter_expanded` and
  `aria-controls="filter-collapse"`. The script owns the state in that attribute; it posts
  `{"filter_expanded": <bool>}` as JSON (`Content-Type: application/json; charset=utf-8`, `X-CSRFToken`) to
  `config.request.path` with `fetch`, and the reset button navigates to `path + "?sort=<sort>&reset_filter=true"` or
  `path + "?reset_filter=true"`.

- [ ] **Step 1: Write the failing Python tests**

`tests/test1/test_filter.py`, next to `_filter_icon_states`:

```python
def _filter_toggle_attrs(response) -> dict:
    from lxml import html

    (toggle,) = html.fromstring(response.content).cssselect("#cv-filter-toggle")
    return {"aria-expanded": toggle.get("aria-expanded"), "aria-controls": toggle.get("aria-controls")}


@pytest.mark.django_db
def test_filter_toggle_aria_expanded_follows_state(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    assert _filter_toggle_attrs(client_user_publisher_view.get("/publisher/")) == {
        "aria-expanded": "false",
        "aria-controls": "filter-collapse",
    }
    client_user_publisher_view.post("/publisher/", data='{"filter_expanded": true}', content_type="application/json")
    assert _filter_toggle_attrs(client_user_publisher_view.get("/publisher/"))["aria-expanded"] == "true"
```

`tests/test1/test_template_a11y.py:86-90`, after `assert toggle.get("role") is None`:
`assert toggle.get("aria-expanded") in ("true", "false")` and `assert toggle.get("aria-controls") == "filter-collapse"`.

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_filter.py tests/test1/test_template_a11y.py -v`
Expected: FAIL on the missing attributes.

- [ ] **Step 3: Template**

In `tags/context_action_filter.html` add to the `<button>`:
`aria-expanded="{% if cv_filter_expanded %}true{% else %}false{% endif %}" aria-controls="filter-collapse"`.

- [ ] **Step 4: Run the Python tests and regenerate the one golden**

Run: `pytest tests/test1/test_filter.py tests/test1/test_template_a11y.py -v` → PASS.
Run: `pytest tests/test1/test_action_menus_golden.py -q` → FAIL on `toolbar_publisher_list.html` only.
Run: `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py -q`, then `git diff tests/test1/golden/`:
the only change is the two new attributes on `#cv-filter-toggle`. Anything else means a template regression: stop
and fix before continuing.

- [ ] **Step 5: Write the failing JS tests** in `tests/js/list.filter.test.js`

Fixture: add `aria-expanded="false" aria-controls="filter-collapse"` to the button and a
`<button type="button" id="filter-button-reset"></button>`. `beforeEach`: `fetchMock = vi.fn(() =>
Promise.resolve({ ok: true })); vi.stubGlobal("fetch", fetchMock); toggle = vi.fn(); window.cv = { ...window.cv,
adapters: { collapse: { toggle } } };` plus the existing `cvGetConfig` stub (let it take the query string as a
parameter of `fixture()`). Replace the two existing tests' jQuery assertions and add:

```js
it("flips aria-expanded, posts the new state as JSON and toggles the panel", async () => {
    const f = fixture();
    await loadScript("list.filter");
    f.toggle.click();
    expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
    expect(toggle).toHaveBeenCalledWith(document.getElementById("filter-collapse"));
    expect(fetchMock).toHaveBeenCalledWith("/books/", {
        method: "POST",
        headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ filter_expanded: true }),
    });
    f.toggle.click();
    expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
    expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ filter_expanded: false }));
});

it("changes nothing when the collapse adapter throws", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});   // jsdom reports listener errors here
    toggle.mockImplementation(() => { throw new Error("no bootstrap"); });
    const f = fixture();
    await loadScript("list.filter");
    f.toggle.click();
    expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
    expect(f.open.classList.contains("d-none")).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
});

it("still toggles when the state POST fails", async () => {                  // Review Focus 3
    fetchMock.mockImplementation(() => Promise.reject(new Error("offline")));
    const f = fixture();
    await loadScript("list.filter");
    f.toggle.click();
    expect(toggle).toHaveBeenCalledTimes(1);
    expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
    await new Promise((r) => setTimeout(r, 0));               // the rejection is handled, no unhandled error
});

it.each([["sort=name&page=2", "/books/?sort=name&reset_filter=true"], ["", "/books/?reset_filter=true"]])(
    "reset navigates with %j", async (queryString, expected) => {
        fixture({ queryString });
        await loadScript("list.filter");
        document.getElementById("filter-button-reset").click();
        expect(nav.href).toBe(expected);
    });

it("loads and works without jQuery", async () => {
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    const f = fixture();
    await loadScript("list.filter");
    f.toggle.click();
    expect(toggle).toHaveBeenCalledTimes(1);
});
```

(`nav` is exported by `helpers/load.js`; import it.)

- [ ] **Step 6: Run them to verify they fail**

Run: `npx vitest run tests/js/list.filter.test.js`
Expected: FAIL (`$` calls, `$.post`, `collapse` plugin).

- [ ] **Step 7: Rewrite `list.filter.js`**

One IIFE. `wire()` attaches `click` listeners to `#cv-filter-toggle` and `#filter-button-reset` when present; it runs
on `DOMContentLoaded`, or immediately when `document.readyState !== "loading"` (same pattern as `tooltip.js`). Toggle
handler order: `preventDefault()`; `next = toggle.getAttribute("aria-expanded") !== "true"`;
`cv.adapters.collapse.toggle(document.getElementById("filter-collapse"))`; set `aria-expanded`; toggle `d-none`
on both `[data-cv-filter-icon]` spans; `fetch(...)` with a `.catch(() => {})`. `cvGetConfig()` is read inside the
handlers. Reset handler: as today, using `globalThis.location.href`. No `#filter-button` handler, no `console.log`.

- [ ] **Step 8: Run the tests**

Run: `npx vitest run tests/js/list.filter.test.js` → PASS. `pytest tests -q` → PASS.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/context_action_filter.html src/crud_views/static/crud_views/js/list.filter.js tests/js/list.filter.test.js tests/test1/test_filter.py tests/test1/test_template_a11y.py tests/test1/golden/action_menus/toolbar_publisher_list.html
git commit -m "refactor(js): filter toggle owns its state in aria-expanded, posts with fetch, collapses via cv.adapters"
```

---

### Task 5: `viewset.js` on the DOM API

**Files:**
- Modify: `src/crud_views/static/crud_views/js/viewset.js`
- Modify: `tests/js/viewset.test.js`

**Interfaces:**
- Produces: `cvGetConfig()` unchanged. Delegated handlers on `document`: click on
  `[data-cv-action='submit-form']` → `preventDefault()` and `form.requestSubmit()` on the element with id
  `data-cv-target` (`form.submit()` when `requestSubmit` is not a function; nothing when the id resolves to no
  element); `change` on `[data-cv-action='submit-on-change']` → `el.form.submit()`; click on `[data-cv-cancel-url]`
  → `preventDefault()` and `globalThis.location.href = url`.

- [ ] **Step 1: Write the failing tests** (append to `tests/js/viewset.test.js`; import `nav` from the helper)

```js
describe("data-cv-action='submit-form'", () => {
    function actionForm({ target = "cv-form-1" } = {}) {
        document.body.innerHTML = `
            <form id="cv-form-1" method="post"></form>
            <button type="button" data-cv-action="submit-form" data-cv-target="${target}">go</button>`;
        const form = document.getElementById("cv-form-1");
        form.requestSubmit = vi.fn();
        return { form, button: document.querySelector("[data-cv-action='submit-form']") };
    }

    it("requestSubmits the target form and prevents the default", () => {
        const { form, button } = actionForm();
        const event = new MouseEvent("click", { bubbles: true, cancelable: true });
        button.dispatchEvent(event);
        expect(form.requestSubmit).toHaveBeenCalledTimes(1);
        expect(event.defaultPrevented).toBe(true);
    });

    it("does nothing when the target does not exist", () => {              // Review Focus 2
        const { form, button } = actionForm({ target: "missing" });
        expect(() => button.click()).not.toThrow();
        expect(form.requestSubmit).not.toHaveBeenCalled();
    });
});

describe("data-cv-cancel-url", () => {
    it("navigates to the cancel url instead of following the href", () => {
        document.body.innerHTML = `<a href="/wrong/" data-cv-cancel-url="/books/">cancel</a>`;
        const event = new MouseEvent("click", { bubbles: true, cancelable: true });
        document.querySelector("a").dispatchEvent(event);
        expect(event.defaultPrevented).toBe(true);
        expect(nav.href).toBe("/books/");
    });
});

it("loads without jQuery", async () => {
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    await expect(loadScript("viewset")).resolves.toBeUndefined();
    vi.unstubAllGlobals();
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `npx vitest run tests/js/viewset.test.js`
Expected: FAIL (`$(this).attr(...)` path; `requestSubmit` never called).

- [ ] **Step 3: Rewrite the handler block of `viewset.js`** per Interfaces; keep `cvGetConfig()` verbatim.

- [ ] **Step 4: Run the tests**

Run: `npx vitest run tests/js/viewset.test.js` → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/viewset.js tests/js/viewset.test.js
git commit -m "refactor(js): viewset.js delegated handlers without jQuery"
```

---

### Task 6: Tooltip adapter, formset guard, token guard test

**Files:**
- Modify: `src/crud_views/static/crud_views/js/tooltip.js:20-23`, `src/crud_views/static/crud_views/js/formset.js:615-620`
- Modify: `tests/js/tooltip.test.js`, `tests/js/formset.test.js`
- Create: `tests/test1/test_js_no_jquery_guard.py`

**Interfaces:**
- Consumes: `cv.adapters.tooltip.init(el)` (Task 1).
- Produces: `cv.initTooltips(root)` unchanged in name and triggers. `formset.js` start-up: at DOMContentLoaded (or
  immediately when already loaded) → no `.cv-formset-content` on the page: return; no jQuery (`globalThis.$?.fn?.jquery`
  falsy): `console.error` once, message matches `/jQuery/`, return; else `globalThis.cv.formsetController = new
  CrudViewsFormset()`.

- [ ] **Step 1: Tooltip tests**

In `tests/js/tooltip.test.js` `beforeAll`: `await loadScript("adapters"); await loadScript("tooltip");` (keep the
`bootstrap` stub: the default adapter resolves it lazily, so the existing tests keep passing unchanged). Add:

```js
it("initializes through cv.adapters.tooltip", () => {
    const init = vi.fn();
    window.cv.adapters.tooltip = { init };
    domReady();
    expect(init).toHaveBeenCalledWith(document.querySelector("[data-cv-tooltip]"));
    expect(init).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `npx vitest run tests/js/tooltip.test.js` → the new test FAILS (`init` not called).

- [ ] **Step 3: Change the loop body** in `tooltip.js` to `cv.adapters.tooltip.init(el)` and remove the
`globalThis.bootstrap?.Tooltip` lookup. Update the header comment.

- [ ] **Step 4: Run** `npx vitest run tests/js/tooltip.test.js` → PASS.

- [ ] **Step 5: Formset guard tests** (new `describe("start-up guard")` in `tests/js/formset.test.js`; each test
re-runs `loadScript("formset")` and starts with `delete window.cv?.formsetController`)

```js
it("starts the controller when a formset and jQuery are present", async () => {
    formsetFixture();
    await loadScript("formset");
    expect(window.cv.formsetController).toBeDefined();
});

it("stays silent on a page without formsets", async () => {
    document.body.innerHTML = "";
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    await loadScript("formset");
    expect(error).not.toHaveBeenCalled();
    expect(window.cv.formsetController).toBeUndefined();
});

it("reports jQuery once when a formset is present and jQuery is not", async () => {
    formsetFixture();
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    await expect(loadScript("formset")).resolves.toBeUndefined();
    expect(error).toHaveBeenCalledTimes(1);
    expect(error.mock.calls[0][0]).toMatch(/jQuery/);
    expect(window.cv.formsetController).toBeUndefined();
});

it("waits for DOMContentLoaded, so jQuery may load after formset.js", async () => {   // Review Focus 5
    formsetFixture();
    Object.defineProperty(document, "readyState", { value: "loading", configurable: true });
    vi.stubGlobal("$", undefined); vi.stubGlobal("jQuery", undefined);
    await loadScript("formset");
    expect(window.cv.formsetController).toBeUndefined();
    vi.stubGlobal("$", jquery); vi.stubGlobal("jQuery", jquery);          // import jquery from "jquery"
    document.dispatchEvent(new Event("DOMContentLoaded"));
    expect(window.cv.formsetController).toBeDefined();
    Object.defineProperty(document, "readyState", { value: "complete", configurable: true });
});
```

Restore `$`/`jQuery` after each of these (re-stub from the `jquery` import) so the rest of the file keeps working.

- [ ] **Step 6: Run to verify they fail**

Run: `npx vitest run tests/js/formset.test.js` → the silent/report/wait tests FAIL (`$ is not a function` at load).

- [ ] **Step 7: Replace the tail of `formset.js`** (`$(function () {...})`) with:

```js
(function () {
    function start() {
        if (!document.querySelector(".cv-formset-content")) {
            return;
        }
        if (!globalThis.$?.fn?.jquery) {
            console.error("crud_views formset.js: pages with formsets need jQuery; load it before DOMContentLoaded.");
            return;
        }
        // the page's controller: its constructor binds all formset events
        globalThis.cv.formsetController = new CrudViewsFormset();
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
```

- [ ] **Step 8: Run** `npx vitest run` (whole suite) → PASS.

- [ ] **Step 9: Token guard test** `tests/test1/test_js_no_jquery_guard.py`:

```python
import re
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parents[2] / "src" / "crud_views" / "static" / "crud_views" / "js"
FORBIDDEN = re.compile(r"\bbootstrap\b|\bjQuery\b|\$\(|\$\.")


@pytest.mark.parametrize("name", ["viewset.js", "modal.js", "list.filter.js", "tooltip.js"])
def test_core_script_has_no_jquery_or_bootstrap_token(name):
    source = (JS_DIR / name).read_text()
    assert not FORBIDDEN.search(source), f"{name} still references jQuery or a bootstrap global"
```

Run: `pytest tests/test1/test_js_no_jquery_guard.py -v` → PASS (if a file still matches, a comment mentioning
`bootstrap` is the usual cause: reword it).

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/static/crud_views/js/tooltip.js src/crud_views/static/crud_views/js/formset.js tests/js/tooltip.test.js tests/js/formset.test.js tests/test1/test_js_no_jquery_guard.py
git commit -m "refactor(js): tooltip via cv.adapters, formset.js guarded without jQuery, token guard test"
```

---

### Task 7: Documentation, changelog, example

**Files:**
- Create: `docs/reference/javascript.md`
- Modify: `docs/reference/.pages` (Theming group, after `assets.md`: `- javascript.md`), `docs/reference/modals.md`,
  `docs/reference/assets.md:42-43,82,102,109,127`, `docs/reference/formsets.md` (after the "This round trip" paragraph,
  ~line 140), `docs/reference/settings.md:115-119` ("JavaScript architecture"), `docs/reference/theme.md` (link),
  `docs/development/index.md:24-25` (Node 22), `CHANGELOG.md`,
  `examples/bootstrap5/project/templates/project/base.html:25-29`

- [ ] **Step 1: `docs/reference/javascript.md`** with these sections: *What the scripts need* (the load-order table
from the spec section 7); *`cv.adapters`* (the contract table from spec section 1, verbatim method names); *Bootstrap
under another name* (Tabler: a registered asset with
`Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));`; ESM: `import * as bootstrap from
"bootstrap"; cv.adapters = cv.bootstrapAdapters(bootstrap);`); *A non-Bootstrap modal* (a `<dialog>` example
overriding `crud_views/modal/shell.html` and assigning `cv.adapters.modal` with `showModal()` / `close()`);
*jQuery* (formsets and jQuery-based extensions only; present by DOMContentLoaded); *Events* (`cv:modal:loaded`,
`cv:formset:row-added`, moved here from or cross-linked with the modal and formset pages).

- [ ] **Step 2: Existing pages**
- `modals.md`: sizes `"", "sm", "lg", "xl"` in the example and prose; "Requirements" → Bootstrap's bundle on
  `window.bootstrap` or an adapter (link), no jQuery; a "Theming the modal" paragraph: `crud_views/modal/shell.html`,
  the three ids, `crud_views/modal/content.html` and `data-cv-modal-dismiss`.
- `assets.md`: line 42-43 → "jQuery is not managed by the registry and core no longer needs it; pages with formsets
  (and jQuery-based extensions) load it anywhere before DOMContentLoaded"; keep the `before=["js/jquery.js"]`
  example with that wording at 82/102/109; line 127 → "project CDN dependencies (Bootstrap; jQuery if you use
  formsets)". Update the `cv_assets` sample output at ~135 if it lists the first core row.
- `formsets.md`: one sentence: formset pages need jQuery, link to `javascript.md`.
- `settings.md:115`: the paragraph names `viewset.js` for everything; say list actions and cancel buttons are
  `viewset.js`, the filter toggle is `list.filter.js`, modals `modal.js`, and link to `javascript.md`.
- `theme.md`: a "JavaScript" bullet or paragraph linking to `javascript.md`.
- `development/index.md:24-25`: "needs Node.js 22" (what CI runs; jsdom 30 does not start on Node 20).
- `examples/bootstrap5/project/templates/project/base.html:25`: comment above the jQuery tag: "jQuery: only needed
  for formsets (this example uses them); core crud_views pages run without it."

- [ ] **Step 3: `CHANGELOG.md`** under `## Unreleased`:
- Breaking: `cv_modal_size` takes `""`, `"sm"`, `"lg"`, `"xl"`; `modal-*` values fail `viewset.E250` with the
  replacement in the message. The modal partial's close button uses `data-cv-modal-dismiss` (a project override of
  `crud_views/modal/content.html` with `data-bs-dismiss` keeps working under the Bootstrap adapter). `{% cv_config %}`
  renders the shell through `crud_views/modal/shell.html`.
- Changed: jQuery is no longer required by core pages (formsets and jQuery-based extensions only); `adapters.js` is
  the first core script (pipeline bundles pick it up through `cv_sources`); the filter toggle carries
  `aria-expanded` / `aria-controls`; `modal.js`, `list.filter.js`, `viewset.js` use the DOM API.
- Added: `cv.adapters` (`modal`, `tooltip`, `collapse`) and `cv.bootstrapAdapters(ns)`; `docs/reference/javascript.md`.

- [ ] **Step 4: Verify docs build and formatting**

Run: `.venv/bin/mkdocs build --strict` → no warnings. Run: `uvx ruff@0.16.0 format --check .` → clean (run
`uvx ruff@0.16.0 format .` to fix Python blocks inside the Markdown).

- [ ] **Step 5: Commit**

```bash
git add docs CHANGELOG.md examples/bootstrap5/project/templates/project/base.html
git commit -m "docs: JavaScript adapters reference, jQuery optional, semantic modal sizes"
```

---

### Task 8: Verification against the spec's acceptance list

**Files:** none changed in this repo; local, uncommitted edits in `tabler-test` (reverted at the end).

- [ ] **Step 1: Full suites**

Run: `pytest tests -q` → PASS. Run: `npx vitest run` (Node 22) → PASS. Run: `.venv/bin/ruff check . && uvx ruff@0.16.0
format --check .` → clean. Run: `cd examples/bootstrap5 && python manage.py check` → no E250.

- [ ] **Step 2: Bootstrap page without jQuery** (`examples/bootstrap5`, `task run`): temporarily delete the jQuery
`<script>` from `project/templates/project/base.html`. In the browser, as `alice`: open the Showcase recipe list;
open a modal delete, cancel it with the close button, reopen and confirm; trigger a validation error inside a modal
form; hover a tooltip; toggle the filter and reload (state persisted); run a POST list action; use a cancel button;
change the card order combo. Console: no errors. Open a page with a formset: exactly one `console.error` naming
jQuery. Restore the jQuery tag.

- [ ] **Step 3: Tabler page, no shim, no jQuery** (spec "Tabler check"): in `tabler-test`, `uv pip install -e
/home/alex/projects/alex/django-crud-views`; replace `crud_views_tabler/templates/crud_views/shared/js.html` with the
core loop plus one deferred inline-free script file containing
`Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));`; remove the jQuery and
`bootstrap-shim.js` tags. Repeat the Step 2 checks. Then `git checkout -- .` and `git clean -fd` in `tabler-test` and
reinstall its pinned crud_views.

- [ ] **Step 4: Acceptance grep**

Run: `grep -nE '\bbootstrap\b|\bjQuery\b|\$\(|\$\.' src/crud_views/static/crud_views/js/{viewset,modal,list.filter,tooltip}.js`
→ no output.

- [ ] **Step 5: Record the outcome** in the PR description: the acceptance list from the spec with a check per line,
and the two manual runs (Bootstrap without jQuery, Tabler without shim) with date and browser.
