# Tooltips on Stock Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stock icon-only buttons carry a location-valued `data-cv-tooltip` marker, and `cv.adapters.tooltip` gains a
location context, an optional `dispose(root)` and an optional `hide(el)`, so any theme gets rich tooltips by
configuring the adapter alone (issue #202).

**Architecture:** Templates add `data-cv-tooltip="<location>"` next to an existing `title`. `tooltip.js` reads the
marker and calls the adapter (`init(el, {location})`, `dispose(root)`, `hide(el)`), exposing `cv.initTooltips`,
`cv.disposeTooltips` and `cv.hideTooltip`. `cv.bootstrapAdapters(ns, options)` implements all three for Bootstrap-like
namespaces, with an optional `options.tooltip(el, {location})` config hook. `modal.js` calls `cv.disposeTooltips` before
replacing content and `cv.hideTooltip` on the trigger before showing.

**Tech Stack:** Django templates, pytest + lxml, vanilla JS classic scripts, vitest + jsdom.

**Spec:** `superpowers/specs/2026-10-20-action-tooltips-design.md` (read it; the plan argues from it).

## Global Constraints

- Tooltip text always lives in `title`. No `data-bs-*` tooltip attributes and no placement in stock markup.
- Marker values, exactly: `context`, `list`, `card` (from `cv_location`), `filter`, `card-order`, `formset`,
  `object-detail`. A bare `data-cv-tooltip` stays valid (location `""`).
- `tags/button/menu_item.html` and `tags/actions_menu_toggle.html` are not changed.
- `dispose` and `hide` are optional on the adapter; an adapter with only `init(el)` keeps working everywhere.
- `options.tooltip` absent → `Tooltip.getOrCreateInstance(el)` is called with **one** argument (today's call).
- `modal.js` never reads the marker; it calls `cv.disposeTooltips?.(…)` / `cv.hideTooltip?.(…)` only.
- Classic scripts only: no modules, no build step, no inline code (strict CSP).
- Python: ruff, line length 120, double quotes. JS: match the surrounding style of each file.
- JS tests need Node 22: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run` (local Node 20 fails).
- Before pushing docs, check formatting with `uvx 'ruff>=0.16' format --check .` (CI ruff formats Markdown).

## Review Focus

1. A custom adapter written before this change (`{init(el) {}}` only): opening a modal and re-rendering it must not
   throw. Pinned in Task 3 (`hideTooltip`/`disposeTooltips` no-ops) and Task 5 (open with such an adapter).
2. A modal opened from a trigger without the marker (labelled card button, menu item): `hideTooltip` is a no-op.
   Pinned in Task 3.
3. An icon-only action whose label is empty (`cv_title == ""`): neither `title` nor the marker renders. Pinned in
   Task 1.
4. Bootstrap loaded but an element never initialised (no instance) when `hide`/`dispose` run: no throw. Pinned in
   Task 4.
5. A 422 re-render while a tooltip inside the modal is showing: the old content's tooltips are disposed before the
   swap. Pinned in Task 5.

---

### Task 1: Action leaf marker and golden files

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html` (the `{% if cv_title %}` line)
- Modify: `tests/test1/golden/action_menus/*.html` (regenerated)
- Test: `tests/test1/test_button_leaves.py`

**Interfaces:**
- Produces: action buttons with `data-cv-tooltip="{{ cv_location }}"` exactly when `cv_title` is truthy.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_leaves.py` (reuse `_context_get`, `_one`,
  `ACTION_LEAF`):

```python
@pytest.mark.parametrize("location", ["context", "list", "card"])
def test_action_leaf_marks_tooltip_exactly_when_title_is_set(location):
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_location=location)), "a")
    assert a.get("title") == "Details"
    assert a.get("data-cv-tooltip") == location

    labelled = _context_get(cv_location=location, cv_label_visible=True)
    del labelled["cv_title"]
    a = _one(render_to_string(ACTION_LEAF, labelled), "a")
    assert a.get("title") is None
    assert a.get("data-cv-tooltip") is None


def test_action_leaf_empty_title_renders_no_marker():
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_title="", cv_label="")), "a")
    assert a.get("title") is None
    assert a.get("data-cv-tooltip") is None


def test_menu_item_leaf_has_no_tooltip_marker():
    item = _context_get(cv_location="context", cv_active=False)
    assert _one(render_to_string(MENU_ITEM_LEAF, item), "a.dropdown-item").get("data-cv-tooltip") is None
```

- [ ] **Step 2: Run** `pytest tests/test1/test_button_leaves.py -v` — Expected: the parametrized test FAILS
  (`data-cv-tooltip` is `None`); the other two pass.

- [ ] **Step 3: Implement** in `action.html`: inside the existing `{% if cv_title %}…{% endif %}`, emit
  `data-cv-tooltip="{{ cv_location }}"` right after `title="{{ cv_title }}"`. Nothing else in the leaf changes.

- [ ] **Step 4: Run** `pytest tests/test1/test_button_leaves.py -v` — Expected: PASS.

- [ ] **Step 5: Regenerate golden files** — `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`, then
  `git diff tests/test1/golden/` must show **only** added `data-cv-tooltip="context|list|card"` attributes on
  elements that already carry `title`; no other change. Then `pytest tests/test1/test_action_menus_golden.py` — PASS.

- [ ] **Step 6: Run** `pytest tests` — Expected: PASS (fix any other test that asserts the full action markup by
  adding the attribute, never by weakening the assertion).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/button/action.html tests/test1/test_button_leaves.py tests/test1/golden
git commit -m "feat(buttons): mark icon-only action buttons with data-cv-tooltip (#202)"
```

### Task 2: Marker on filter toggle, card-order toggles, formset controls and property detail

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/context_action_filter.html`
- Modify: `src/crud_views/templates/crud_views/snippets/card_order.html`
- Modify: `src/crud_views/templates/crud_views/formsets/control.html`
- Modify: `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/card-rows/property.html`
- Test: `tests/test1/test_button_classes_templates.py`, `tests/test1/test_action_menus_context.py` (or
  `test_filter.py`), `tests/test1/od/test_layout_a11y.py`

**Interfaces:**
- Produces: markers `filter`, `card-order`, `formset`, `object-detail`, each next to a `title`.

- [ ] **Step 1: Write the failing tests**

  - In `test_button_classes_templates.py`, extend `test_formset_controls_from_table` (or add
    `test_formset_controls_tooltip`) using `_render_formset_controls()`:
    `[(b.get("title"), b.get("data-cv-tooltip")) for b in doc.cssselect("button")] ==
    [("Move up", "formset"), ("Move down", "formset"), ("Add row", "formset"), ("Delete row", "formset")]`, and every
    button's `title == aria-label`.
  - Same file, in `test_card_order_and_language_from_table`: `asc.get("data-cv-tooltip") == "card-order"`,
    `desc.get("data-cv-tooltip") == "card-order"`, `asc.get("title") == "Ascending"`.
  - Filter toggle (wherever a rendered list page with `#cv-filter-toggle` is already asserted, e.g.
    `test_action_menus_context.py`): `toggle.get("data-cv-tooltip") == "filter"` and `toggle.get("title")` non-empty.
  - In `od/test_layout_a11y.py::test_card_rows_detail_trigger_is_marked_for_tooltip_js`, replace the last assertion:
    `trigger.get("data-cv-tooltip") == "object-detail"`, `trigger.get("title") == "Currently active"`,
    `trigger.get("data-bs-title") is None`. Update the docstring to say the text is in `title` (driver-neutral).

- [ ] **Step 2: Run** those tests — Expected: FAIL on the new assertions.

- [ ] **Step 3: Implement**
  - `context_action_filter.html`: add `data-cv-tooltip="filter"` after `title="{{ cv_action_label }}"`.
  - `card_order.html`: add `data-cv-tooltip="card-order"` after each toggle's `title`.
  - `control.html`: each control's `title` becomes the same `{% translate '…' %}` as its `aria-label`
    (`Move up`, `Move down`, `Add row`, `Delete row`), followed by `data-cv-tooltip="formset"`.
  - `property.html`: `data-cv-tooltip data-bs-title="{{ prop.detail }}"` →
    `data-cv-tooltip="object-detail" title="{{ prop.detail }}"`; `aria-label` unchanged.

- [ ] **Step 4: Run** `pytest tests` — Expected: PASS. Do not run `makemessages`: the four strings already exist as
  `aria-label` msgids, so no `.po` change is needed.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates src/crud_views_object_detail/templates tests/test1
git commit -m "feat(templates): data-cv-tooltip on filter, card-order, formset and property-detail triggers (#202)"
```

### Task 3: `tooltip.js` — location context, `disposeTooltips`, `hideTooltip`

**Files:**
- Modify: `src/crud_views/static/crud_views/js/tooltip.js`
- Test: `tests/js/tooltip.test.js`

**Interfaces:**
- Consumes: `cv.adapters.tooltip` with `init(el, ctx)`, optional `dispose(root)`, optional `hide(el)`.
- Produces (on `globalThis.cv`):
  - `initTooltips(root: ParentNode): void` — calls `tooltip.init(el, {location})` for each `[data-cv-tooltip]` under
    `root`, `location = el.getAttribute("data-cv-tooltip") || ""`.
  - `disposeTooltips(root: ParentNode): void` — calls `tooltip.dispose(root)` if it is a function, else nothing.
  - `hideTooltip(el: Element | null | undefined): void` — calls `tooltip.hide(el)` only when `el` is an Element with
    `data-cv-tooltip` and `tooltip.hide` is a function, else nothing.
  - All three are no-ops (no throw) when `cv.adapters.tooltip` is missing.

- [ ] **Step 1: Write the failing tests** in `tests/js/tooltip.test.js`:
  - Update the existing "initializes through cv.adapters.tooltip" test: expect
    `init` called with `(el, {location: ""})` for the fixture's bare marker.
  - `it("passes the marker value as location")`: fixture button `data-cv-tooltip="context"` →
    `init` called with `(el, {location: "context"})`.
  - `it("disposeTooltips calls adapter.dispose with the root")`: `dispose = vi.fn()`, `cv.disposeTooltips(root)` →
    `expect(dispose).toHaveBeenCalledWith(root)`.
  - `it("disposeTooltips is a no-op without adapter.dispose")`: adapter `{init}` → `not.toThrow()`.
  - `it("hideTooltip calls adapter.hide for a marked element")`: `hide = vi.fn()` → called with the element.
  - `it("hideTooltip ignores unmarked elements, null and adapters without hide")`: `hide` not called for an element
    without the marker or for `null`; with adapter `{init}` → `not.toThrow()`.
  - `it("dispose and hide do nothing without cv.adapters.tooltip")`: set `cv.adapters.tooltip = undefined` →
    neither throws.
  Restore `window.cv.adapters.tooltip` in `finally`, as the existing test does.

- [ ] **Step 2: Run** `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/tooltip.test.js` —
  Expected: FAIL (`cv.disposeTooltips is not a function`, wrong `init` args).

- [ ] **Step 3: Implement** the three functions in `tooltip.js` per the Interfaces block; update the header comment
  (location value, optional `dispose`/`hide`).

- [ ] **Step 4: Run** the same command — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/tooltip.js tests/js/tooltip.test.js
git commit -m "feat(js): tooltip location context, cv.disposeTooltips and cv.hideTooltip (#202)"
```

### Task 4: `cv.bootstrapAdapters(ns, options)` — tooltip config hook, `dispose`, `hide`

**Files:**
- Modify: `src/crud_views/static/crud_views/js/adapters.js`
- Test: `tests/js/adapters.test.js`

**Interfaces:**
- Produces: `cv.bootstrapAdapters(ns, options = {})` where `options.tooltip?: (el, {location}) => object`.
  Tooltip adapter:
  - `init(el, ctx)`: with `options.tooltip` → `Tooltip.getOrCreateInstance(el, options.tooltip(el, ctx))`;
    without it → `Tooltip.getOrCreateInstance(el)` (one argument). No-op without `Tooltip`.
  - `dispose(root)`: for each `root.querySelectorAll("[data-cv-tooltip]")`, `Tooltip.getInstance(el)?.dispose()`.
    No-op without `Tooltip`.
  - `hide(el)`: `Tooltip.getInstance(el)?.hide()`. No-op without `Tooltip`.
  - Default `cv.adapters` unchanged: `cv.bootstrapAdapters(() => globalThis.bootstrap)`.

- [ ] **Step 1: Write the failing tests** in `tests/js/adapters.test.js`. Extend `fakeNamespace()`: `Tooltip` gains
  `getInstance: vi.fn(() => tip)` with `tip = {dispose: vi.fn(), hide: vi.fn()}` returned on the namespace.
  - `it("tooltip.init without options calls getOrCreateInstance with the element only")`:
    `expect(ns.Tooltip.getOrCreateInstance.mock.calls[0]).toEqual([el])` and `.length === 1`.
  - `it("tooltip.init passes options.tooltip(el, ctx) as config")`: `cfg = vi.fn(() => ({placement: "bottom"}))`,
    `bootstrapAdapters(ns, {tooltip: cfg}).tooltip.init(el, {location: "context"})` →
    `cfg` called with `(el, {location: "context"})`, `getOrCreateInstance` called with `(el, {placement: "bottom"})`.
  - `it("tooltip.dispose disposes every marked trigger under the root")`: root with two `[data-cv-tooltip]` and one
    unmarked button → `getInstance` called for the two marked only, `tip.dispose` twice.
  - `it("tooltip.hide hides the element's instance")`: `tip.hide` once.
  - `it("tooltip dispose/hide tolerate a missing instance")`: `getInstance = vi.fn(() => null)` → neither throws.
  - `it("tooltip init/dispose/hide do nothing without Tooltip")`: namespace `{}` → none throws.

- [ ] **Step 2: Run** `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/adapters.test.js` —
  Expected: FAIL.

- [ ] **Step 3: Implement** per the Interfaces block; update the file's header comment to mention `options`.

- [ ] **Step 4: Run** the same command, then the whole JS suite — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/adapters.js tests/js/adapters.test.js
git commit -m "feat(js): bootstrapAdapters tooltip options, dispose and hide (#202)"
```

### Task 5: `modal.js` — dispose before inject, hide the trigger before show

**Files:**
- Modify: `src/crud_views/static/crud_views/js/modal.js` (`cvModalInject`, `cvModalOpen`, the click handler)
- Test: `tests/js/modal.test.js`

**Interfaces:**
- Consumes: `cv.disposeTooltips(root)`, `cv.hideTooltip(el)` from Task 3 (both may be undefined).
- Produces: `cvModalOpen(url: string, size: string, trigger?: Element)`; exported as `cv.cvModalOpen` as today.
  `cvModalInject(html)` calls `cv.disposeTooltips?.(els.content)` before setting `innerHTML`. After a successful
  fetch, `cv.hideTooltip?.(trigger)` runs immediately before `cv.adapters.modal.show(els.modal)`. The click handler
  passes the `[data-cv-modal]` element as `trigger`.

- [ ] **Step 1: Write the failing tests** in `tests/js/modal.test.js`. In `beforeEach`, set
  `window.cv.disposeTooltips = vi.fn()` and `window.cv.hideTooltip = vi.fn()` (keep the `adapters` reset).
  - `it("disposes tooltips in the old content before injecting on open")`: pre-fill `#cv-modal-content` with
    `<p id="old"></p>`; make `disposeTooltips` record `content.querySelector("#old") !== null` at call time;
    after `cvModalOpen` → called once with `#cv-modal-content`, and the recorded value is `true`.
  - `it("disposes tooltips before swapping in a 422 re-render")`: same check through `cvModalSubmit`.
  - `it("hides the trigger's tooltip right before showing the modal")`: click a `[data-cv-modal]` link →
    `hideTooltip` called with that link, and
    `hideTooltip.mock.invocationCallOrder[0] < show.mock.invocationCallOrder[0]`.
  - `it("does not hide when the fetch falls back to navigation")`: non-OK response → `hideTooltip` not called.
  - `it("opens without tooltip.js loaded")`: delete `window.cv.disposeTooltips` and `window.cv.hideTooltip` →
    `show` still called, content injected.
  - Review Focus 1: `it("opens with an init-only tooltip adapter")`: in `beforeAll`, also `loadScript("tooltip")` and
    keep the real `cv.disposeTooltips` / `cv.hideTooltip` in variables before `beforeEach` replaces them with mocks.
    In this test restore the real ones, set `cv.adapters.tooltip = {init: vi.fn()}`, pre-fill the content with a
    marked button and click a marked `[data-cv-modal]` link → `show` called, content injected, nothing thrown.

- [ ] **Step 2: Run** `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/modal.test.js` —
  Expected: FAIL.

- [ ] **Step 3: Implement** per the Interfaces block. Update the file's header comment (tooltips disposed before
  injection; trigger tooltip hidden before show).

- [ ] **Step 4: Run** the full JS suite — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/modal.js tests/js/modal.test.js
git commit -m "feat(js): modal disposes tooltips before injecting and hides the trigger's tooltip (#202)"
```

### Task 6: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/buttons.md`, `docs/reference/javascript.md`, `docs/reference/inaccessible_actions.md`,
  `CHANGELOG.md` (`## Unreleased`)

**Interfaces:**
- Consumes: the names and behaviour from Tasks 1–5 exactly as defined there.

- [ ] **Step 1: `buttons.md`** — leaf contract row for `cv_title`: "the `title` text, also marks the button with
  `data-cv-tooltip="<cv_location>"`; present only when the label is not visible". The theme recipe leaf (around the
  `{% if cv_title %}title=…` line) adds `data-cv-tooltip="{{ cv_location }}"` inside the same `if`, and the prose
  after it lists the marker among what to keep.

- [ ] **Step 2: `javascript.md`**
  - Adapter table: `tooltip.init(el, {location})`, new rows `tooltip.dispose(root)` (optional; before modal content
    is replaced) and `tooltip.hide(el)` (optional; on the modal trigger before show), with their Bootstrap defaults.
  - A "Tooltips" subsection: the marker values table (location → where), `cv.initTooltips` /
    `cv.disposeTooltips` / `cv.hideTooltip`, the `cv.bootstrapAdapters(ns, {tooltip})` hook with the spec's Tabler
    placement example, and the opt-out `cv.adapters.tooltip = {init() {}}`.
  - "A non-Bootstrap tooltip" recipe next to "A non-Bootstrap modal": `init` reads `title`, removes it, creates the
    tooltip with that text and the location; `hide` hides it; `dispose(root)` destroys instances for
    `[data-cv-tooltip]` under `root`. Generic library calls (Tippy-style), no new dependency.

- [ ] **Step 3: `inaccessible_actions.md`** — short note: disabled buttons show neither the native `title` nor a
  tooltip (Bootstrap sets `pointer-events: none` on `.btn:disabled`); a theme that needs it wraps the button in a
  focusable element in its own leaf override.

- [ ] **Step 4: `CHANGELOG.md` → `## Unreleased`**
  - Breaking (DOM changes): icon-only action buttons, the filter toggle, card-order toggles and formset controls carry
    `data-cv-tooltip="<location>"`; formset control `title`s are translated (`Move up`, …); the object-detail
    property button uses `title` instead of `data-bs-title`. With Bootstrap's JS loaded these buttons now show
    Bootstrap tooltips; opt out with `cv.adapters.tooltip = {init() {}}`.
  - Added: `init(el, {location})`, optional `dispose(root)` / `hide(el)` on `cv.adapters.tooltip`;
    `cv.bootstrapAdapters(ns, {tooltip})`; `cv.disposeTooltips`, `cv.hideTooltip`.

- [ ] **Step 5: Verify** `mkdocs build --strict` — no warnings; `uvx 'ruff>=0.16' format --check .` — clean.

- [ ] **Step 6: Commit**

```bash
git add docs CHANGELOG.md
git commit -m "docs: tooltips on stock buttons, adapter dispose/hide and bootstrapAdapters options (#202)"
```

### Task 7: Acceptance

**Files:** none (verification only; fixes go back to the owning task's files).

- [ ] **Step 1:** `pytest tests` — PASS. JS suite (Node 22 command) — PASS. `task check` and `task format` — no
  changes left.
- [ ] **Step 2:** `task test` (nox matrix) — PASS, or record which sessions could not run locally.
- [ ] **Step 3: Browser check** — `task run`, log in, open `/action-menus/` and an object detail page in the example
  project. With Bootstrap's bundle loaded:
  - hovering and focusing an icon-only toolbar button, a list-row button and the filter toggle shows a Bootstrap
    tooltip (`.tooltip` element in the DOM), and labelled card buttons and menu items show none;
  - open an action with `cv_modal = True` from an icon-only button: no tooltip remains over the open modal;
  - inside the modal, an icon-only button's tooltip shows; submitting a form that re-renders (422) leaves no stuck
    `.tooltip` element;
  - the native-`title` fallback without an adapter is covered by Task 3's "do nothing without `cv.adapters.tooltip`"
    test and the existing no-Bootstrap test; no browser step for it.
- [ ] **Step 4:** Report results (commands and outcomes) in the PR description; close #202 from the PR.
