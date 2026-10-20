# Tooltips on Stock Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stock icon-only buttons carry a location-valued `data-cv-tooltip` marker and `cv.adapters.tooltip.init`
receives that location, so any theme gets rich tooltips by configuring the adapter alone (issue #202).

**Architecture:** Templates add `data-cv-tooltip="<location>"` next to an existing `title`. `tooltip.js` reads the
marker value and calls `init(el, {location})`. `adapters.js` and `modal.js` do not change; per-location config is a
documented recipe (reassign `cv.adapters.tooltip.init`). The tooltip lifecycle is a follow-up issue filed from the
observations the acceptance task records.

**Tech Stack:** Django templates, pytest + lxml, vanilla JS classic scripts, vitest + jsdom.

**Spec:** `superpowers/specs/2026-10-20-action-tooltips-design.md` (read it; the plan argues from it).

## Global Constraints

- Tooltip text always lives in `title`. No `data-bs-*` tooltip attributes and no placement in stock markup.
- Marker values, exactly: `context`, `list`, `card` (from `cv_location`), `context` (filter toggle), `card-order`,
  `formset`, `object-detail`. A bare `data-cv-tooltip` stays valid (location `""`).
- `tags/button/menu_item.html`, `tags/actions_menu_toggle.html`, `adapters.js` and `modal.js` are not changed.
- An adapter with `init(el)` only keeps working: the second argument is extra, never required.
- Classic scripts only: no modules, no build step, no inline code (strict CSP).
- Python: ruff, line length 120, double quotes. JS: match the surrounding style of each file.
- JS tests need Node 22: `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run` (local Node 20 fails).
- Before pushing docs, check formatting with `uvx 'ruff>=0.16' format --check .` (CI ruff formats Markdown).

## Review Focus

1. A custom adapter written before this change (`{init(el) {}}`): still called once per marker, nothing thrown.
   Pinned in Task 3.
2. An icon-only action whose label is empty (`cv_title == ""`): neither `title` nor the marker renders. Pinned in
   Task 1.
3. A labelled card button or a menu item: no marker, so no tooltip on by default. Pinned in Task 1.
4. A theme or app template with a bare `data-cv-tooltip`: `init` receives `{location: ""}`. Pinned in Task 3.
5. The property-detail button after `data-bs-title` → `title`: `aria-label` kept, so the accessible name survives
   Bootstrap's `_fixTitle`. Pinned in Task 2.

---

### Task 1: Action leaf marker and golden files

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html` (the `{% if cv_title %}` line)
- Modify: `tests/test1/golden/action_menus/*.html` (regenerated)
- Test: `tests/test1/test_button_leaves.py`

**Interfaces:**
- Produces: action buttons with `data-cv-tooltip="{{ cv_location }}"` exactly when `cv_title` is truthy.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_leaves.py` (reuse `_context_get`, `_one`,
  `ACTION_LEAF`, `MENU_ITEM_LEAF`):

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
- Test: `tests/test1/test_button_classes_templates.py`, `tests/test1/test_filter.py`, `tests/test1/od/test_layout_a11y.py`

**Interfaces:**
- Produces: markers `context` (filter toggle), `card-order`, `formset`, `object-detail`, each next to a `title`.

- [ ] **Step 1: Write the failing tests**

  - In `test_button_classes_templates.py`, extend `test_formset_controls_from_table` using
    `_render_formset_controls()`:
    `[(b.get("title"), b.get("data-cv-tooltip")) for b in doc.cssselect("button")] ==
    [("Move up", "formset"), ("Move down", "formset"), ("Add row", "formset"), ("Delete row", "formset")]`, and every
    button's `title == aria-label`.
  - Same file, in `test_card_order_and_language_from_table`: `asc.get("data-cv-tooltip") == "card-order"`,
    `desc.get("data-cv-tooltip") == "card-order"`, `asc.get("title") == "Ascending"`.
  - In `test_filter.py::test_filter_form_rendered` (it already selects `#cv-filter-toggle`):
    `toggle.get("data-cv-tooltip") == "context"` and `toggle.get("title")` non-empty.
  - In `od/test_layout_a11y.py::test_card_rows_detail_trigger_is_marked_for_tooltip_js`, replace the last assertion:
    `trigger.get("data-cv-tooltip") == "object-detail"`, `trigger.get("title") == "Currently active"`,
    `trigger.get("aria-label") == "Currently active"`, `trigger.get("data-bs-title") is None`. Update the docstring to
    say the text is in `title` (driver-neutral).

- [ ] **Step 2: Run** those tests — Expected: FAIL on the new assertions.

- [ ] **Step 3: Implement**
  - `context_action_filter.html`: add `data-cv-tooltip="context"` after `title="{{ cv_action_label }}"`.
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

### Task 3: `tooltip.js` — location context

**Files:**
- Modify: `src/crud_views/static/crud_views/js/tooltip.js` (`initTooltips` and the header comment)
- Test: `tests/js/tooltip.test.js`

**Interfaces:**
- Consumes: `cv.adapters.tooltip.init(el, ctx)`.
- Produces (on `globalThis.cv`): `initTooltips(root: ParentNode): void` — calls `tooltip.init(el, {location})` for
  each `[data-cv-tooltip]` under `root`, `location = el.getAttribute("data-cv-tooltip") || ""`. No-op without
  `cv.adapters.tooltip`, as today.

- [ ] **Step 1: Write the failing tests** in `tests/js/tooltip.test.js`:
  - In `fixture()`, the package trigger becomes `<button type="button" data-cv-tooltip="context" title="first"></button>`
    and a second one `<button type="button" data-cv-tooltip title="bare"></button>`; keep the app-owned
    `data-bs-toggle="tooltip"` button and the modal skeleton. Adjust the existing count assertions (`toHaveBeenCalledTimes`,
    `instances.size`) from 1 to 2.
  - Update "initializes through cv.adapters.tooltip": `init` called with `(contextButton, {location: "context"})` and
    with `(bareButton, {location: ""})`, `toHaveBeenCalledTimes(2)`.
  - `it("keeps working with an adapter written for init(el)")`: `window.cv.adapters.tooltip = {init(el) { seen.push(el); }}`
    → `seen` has both marked buttons, nothing thrown.
  Restore `window.cv.adapters.tooltip` in `finally`, as the existing test does.

- [ ] **Step 2: Run** `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/tooltip.test.js` —
  Expected: FAIL (`init` called with one argument).

- [ ] **Step 3: Implement** in `tooltip.js`: `tooltip.init(el, {location: el.getAttribute("data-cv-tooltip") || ""})`;
  update the header comment (marker value is the location; text in `title`).

- [ ] **Step 4: Run** the same command — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/tooltip.js tests/js/tooltip.test.js
git commit -m "feat(js): pass the marker location to cv.adapters.tooltip.init (#202)"
```

### Task 4: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/buttons.md`, `docs/reference/javascript.md`, `docs/reference/inaccessible_actions.md`,
  `CHANGELOG.md` (`## Unreleased`)

**Interfaces:**
- Consumes: the names and behaviour from Tasks 1–3 exactly as defined there.

- [ ] **Step 1: `buttons.md`** — leaf contract row for `cv_title`: "the `title` text, also marks the button with
  `data-cv-tooltip="<cv_location>"`; present only when the label is not visible". The theme recipe leaf (the
  `{% if cv_title %}title=…` line) adds `data-cv-tooltip="{{ cv_location }}"` inside the same `if`, and the prose
  after it lists the marker among what to keep.

- [ ] **Step 2: `javascript.md`**
  - Adapter table: `tooltip.init(el, {location})`, Bootstrap default unchanged (`Tooltip.getOrCreateInstance(el)`,
    ignores the context).
  - A "Tooltips" section: the marker values table (location → where: `context` toolbar and filter toggle, `list`,
    `card`, `card-order`, `formset`, `object-detail`, `""` bare marker); `cv.initTooltips(root)` for injected markup;
    the opt-out `cv.adapters.tooltip = {init() {}}`; the per-location recipe from spec decision 5, verbatim:

    ```javascript
    Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
    cv.adapters.tooltip.init = (el, {location} = {}) =>
        globalThis.tabler.Tooltip.getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"});
    ```

  - "A non-Bootstrap tooltip" recipe next to "A non-Bootstrap modal": `init` reads `title`, removes it so the native
    tooltip does not show too, creates the tooltip with that text and the location. Generic library calls
    (Tippy-style), no new dependency.

- [ ] **Step 3: `inaccessible_actions.md`** — short note: disabled buttons show neither the native `title` nor a
  tooltip (Bootstrap sets `pointer-events: none` on `.btn:disabled`); a theme that needs it wraps the button in a
  focusable element in its own leaf override.

- [ ] **Step 4: `CHANGELOG.md` → `## Unreleased`**
  - Breaking (DOM changes): icon-only action buttons, the filter toggle, card-order toggles and formset controls carry
    `data-cv-tooltip="<location>"`; formset control `title`s are translated (`Move up`, …); the object-detail
    property button uses `title` instead of `data-bs-title`. With Bootstrap's JS loaded these buttons now show
    Bootstrap tooltips; opt out with `cv.adapters.tooltip = {init() {}}`.
  - Added: `cv.adapters.tooltip.init(el, {location})`; adapters written for `init(el)` keep working.

- [ ] **Step 5: Verify** `mkdocs build --strict` — no warnings; `uvx 'ruff>=0.16' format --check .` — clean.

- [ ] **Step 6: Commit**

```bash
git add docs CHANGELOG.md
git commit -m "docs: tooltips on stock buttons and the init location context (#202)"
```

### Task 5: Acceptance and the lifecycle follow-up

**Files:** none (verification only; fixes go back to the owning task's files).

- [ ] **Step 1:** `pytest tests` — PASS. JS suite (Node 22 command) — PASS. `task check` and `task format` — no
  changes left.
- [ ] **Step 2:** `task test` (nox matrix) — PASS, or record which sessions could not run locally.
- [ ] **Step 3: Browser check** — `task run`, log in, open `/action-menus/` and an object detail page in the example
  project. With Bootstrap's bundle loaded:
  - hovering and focusing an icon-only toolbar button, a list-row button and the filter toggle shows a Bootstrap
    tooltip (`.tooltip` element in the DOM), and labelled card buttons and menu items show none;
  - inside a modal, an icon-only button's tooltip shows;
  - the native-`title` fallback without an adapter is covered by Task 3's existing no-Bootstrap test; no browser step.
- [ ] **Step 4: Record the three lifecycle observations** from the spec's "Follow-up" section, without fixing anything:
  1. click the filter toggle with the mouse, move the pointer away: does `.tooltip.show` stay until you click elsewhere?
  2. hover an icon-only modal trigger (`cv_modal = True`), click, hold the mouse still: does the tooltip float over the
     open modal, and for how long (until the pointer moves, or longer)?
  3. open and cancel the same modal ten times: note whether anything visible goes wrong (a stuck `.tooltip`, console
     errors). Memory growth is a note, not a measurement.
  Write the three answers with browser name and version into the PR description.
- [ ] **Step 5: File the follow-up issue** "Tooltip lifecycle: dispose before modal injection, hide on click" with the
  three recorded observations, the spec's "Follow-up" section as the proposed shape (`cv:modal:unload` event,
  delegated click → `tooltip.hide?.(el)`, optional `dispose` / `hide` on the adapter), and a note that it should start
  from a browser repro, not from the source deduction. Link it from the PR description.
- [ ] **Step 6:** Report results (commands and outcomes) in the PR description; close #202 from the PR.
