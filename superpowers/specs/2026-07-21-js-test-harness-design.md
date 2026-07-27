# JS Test Harness Design

**Date:** 2026-07-21
**Status:** Approved

## Goal

Add a JavaScript unit-test harness for the package's first-party browser scripts, which currently
have zero test coverage. The harness tests JS logic fast and in isolation — jsdom DOM, stubbed
transport — with no Django server and no real browser.

First-party JS under test (`src/crud_views/static/crud_views/js/`):

| File | Lines | Content |
|---|---|---|
| `formset.js` | 610 | jQuery classes for formset add/delete/reorder, management-form bookkeeping, AJAX row fetch |
| `modal.js` | 109 | fetch-based Bootstrap 5 modal protocol (200/204+`X-CV-Redirect`/422) |
| `toggle.js` | 62 | vanilla-JS conditional field groups; management fields stay enabled when hidden |
| `list.filter.js` | 55 | jQuery filter bar glue |
| `viewset.js` | 28 | `cvGetConfig()` + small jQuery glue |

## Decisions

- **Goal:** fast unit tests (not browser integration). Vitest browser mode (Playwright-driven
  Chromium) is a possible future layer that composes with the same tests; out of scope here.
- **Toolchain:** Node.js is acceptable. Dev-only; the published Python package is unaffected.
- **Initial coverage scope:** the risky trio — `formset.js`, `toggle.js`, `modal.js`.
  `viewset.js` / `list.filter.js` get tests later, when they change.
- **Source edits:** light-touch, behavior-neutral attachment blocks are allowed so tests can
  reach top-level declarations. No ES-module conversion; files stay classic scripts served by
  Django unchanged.

## Architecture

**Runner:** Vitest with the jsdom environment. No build step, no bundler — Vitest is purely a
runner; tests always exercise the exact files Django serves.

### Repo layout

```
package.json              # private, engines node>=20; devDeps: vitest, jsdom, jquery
vitest.config.js          # environment: jsdom, include: tests/js/**/*.test.js
tests/js/
  helpers/
    load.js               # loadScript("formset") — read + execute the real source file
    dom.js                # fixture builders (formset markup, toggle groups, modal skeleton)
  formset.test.js
  toggle.test.js
  modal.test.js
```

`package.json` and `vitest.config.js` live at the repo root (standard tooling discovery for
editors, CI, contributors); tests live in `tests/js/` mirroring the Python test convention.
`node_modules/` is gitignored. Hatchling packaging is unaffected (only `src/` ships).

### Dependencies

- **jQuery:** real, as a pinned npm devDependency. jQuery is supplied by the consuming project,
  not the package; the example app currently loads 3.7.1, so the harness pins jQuery 3.7.x —
  `$` in tests is not a mock.
- **Bootstrap:** stubbed, not installed. jsdom has no layout/transitions;
  `bootstrap.Modal.getOrCreateInstance(...).show()` is a spy. Tests assert the modal *protocol*
  (what our code does), not Bootstrap's rendering.
- **fetch / `$.ajax` transport / `window.location` navigation:** stubbed per test with
  `vi.stubGlobal` and spies (jsdom implements none of these usefully).

## Script loading

`loadScript(name)` reads `src/crud_views/static/crud_views/js/<name>.js` as text and executes it
as a classic script against the jsdom window (wrapped in `new Function(code)`; `window`,
`document`, `$` are already global in the Vitest jsdom environment). The helper is async and
resolves after jQuery `$(document).ready()` callbacks have run (jQuery defers them by a
microtask even on an already-loaded document).

### Light-touch source edits

`new Function` wrapping (like ES modules) makes top-level `const`/`class`/`function`
declarations invisible to the outside, so each file under test gets a short attachment block at
the end:

- **`formset.js`:**
  `window.cv = window.cv || {}; Object.assign(window.cv, { CVFSConst, XBase, XFormset, XForm, CrudViewsFormset });`
  In the browser this only adds console/inspection discoverability — these were lexical globals
  reachable by other classic scripts but not `window` properties. Behavior-neutral otherwise.
- **`modal.js`:** same pattern for `CVModalConst`, `cvModalElements`, `cvModalInject`,
  `cvModalOpen`, `cvModalSubmit`. The functions are already implicit `window` globals in the
  browser (top-level function declarations), so this is strictly neutral.
- **`toggle.js`:** no edit. It is an IIFE wired entirely through events; tests drive it the way
  the browser does — dispatch `DOMContentLoaded` / `cv:modal:loaded` and assert
  visibility/disabled state. Its `window.__cvToggleInit` re-entry guard is cleared in test setup
  between loads.

## Isolation model

- Each test **file** gets a fresh jsdom window (Vitest default).
- Within a file: the script is loaded once in `beforeAll` (so jQuery document-level delegated
  handlers do not stack); each test rebuilds its DOM fixture in `beforeEach`.
- Stateful entry points (`new cv.CrudViewsFormset()`, toggle wiring via event dispatch) are
  invoked per test against the fresh fixture.
- Harness setup silences `console.log` / `console.assert` noise from `formset.js` debug calls.

## Initial test scope (~40–50 tests)

### `toggle.test.js` — behavior-level, driven purely by events

- checked toggle → group visible, inputs enabled; unchecked → hidden, inputs disabled
- management-form hidden inputs (`-TOTAL_FORMS` etc.) stay **enabled** even when the group is
  disabled (the regression rule documented in the file's own comment)
- checkbox lookup by exact name and by `-name` suffix, scoped to the nearest `<form>`
- missing checkbox → group untouched, no throw
- `cv:modal:loaded` wires groups inside injected content; already-wired groups are not
  double-bound

### `modal.test.js` — protocol branches, stubbed `fetch`, spy `bootstrap.Modal`

- open: GET carries `X-CV-Modal: true`; 200 → HTML injected, size class + `data-cv-url` set,
  `cv:modal:loaded` dispatched (bubbling), `.show()` called
- open: non-OK response and fetch rejection each fall back to full-page navigation
- submit: `X-CV-Redirect` header → navigate; 422 → swap re-rendered partial; any other status
  and network error → navigate to fallback URL (`data-cv-url`, else form action)
- guard errors: missing `#cv-modal` / missing Bootstrap throw their descriptive messages
- delegated handlers: click on `[data-cv-modal='true']` opens with href+size; submit inside
  `#cv-modal-content` is intercepted

### `formset.test.js` — deepest suite

Fixture builder markup is derived from the real `crud_views` formset templates — minimal but
structurally faithful. **This fixture fidelity is the harness's key risk:** if templates and
fixtures drift, tests keep passing against stale markup. Mitigation: fixture builder documents
which templates it mirrors; template changes must update fixtures.

- `XFormset`: management-form get/set/increment; pk + index parsing from `prefix_key`
- `reorder()`: filled rows numbered 1..n; empty rows and DELETE-marked rows get blank ORDER;
  no-op when `can_order` is false
- `XForm`: first/last/next/previous row math; `delete()` toggles the hidden DELETE value and
  button styling; `up()`/`down()` move DOM rows and renumber; no-ops at the edges
- `add()`: stubbed `$.ajax` success inserts returned HTML at the right position, increments
  TOTAL_FORMS, wires new-row controls, reorders
- `CrudViewsFormset`: form submit blocked when reorder fails; global init on a page with a
  non-orderable/edit-only formset binds the controls that exist without aborting (regression
  fixed 2026-07-19)

## CI and developer workflow

- **CI:** new workflow `.github/workflows/js.yml` (push to main + PRs, matching the other
  workflows) with a single job: checkout → `actions/setup-node` (Node 22 LTS, npm cache) →
  `npm ci` → `npx vitest run`. Separate from `tests.yml` so the Python matrix and the JS job
  run independently and failures are attributable at a glance. No matrix — one Node version
  suffices for browser-target JS.
- **Taskfile:** new `test-js` task (`npm ci` if `node_modules` is missing, then
  `npx vitest run`) and `test-js-watch`. `task test` (nox) stays Python-only.
- **Docs:** CONTRIBUTING/README dev-setup gains one line: "JS tests: `task test-js`
  (requires Node 20+)."
- **package.json:** `private: true`, `engines: { node: ">=20" }` (local dev machines run
  Node 20; CI uses 22), scripts `test` / `test:watch`.
- **Coverage:** dropped during implementation. The sources execute via `new Function` in the
  test loader, which Vitest's coverage providers cannot see; instrumenting with
  `istanbul-lib-instrument` in the loader produced counters in `globalThis.__coverage__`,
  but the istanbul provider verifiably drops externally-produced entries (all-zero report).
  Coverage wiring is a follow-up; candidate approach: standalone `nyc`/`istanbul-lib-report`
  over the loader-produced `__coverage__` object.

## Out of scope / follow-ups

- Tests for `viewset.js` and `list.filter.js` (add when those files change)
- Vitest browser mode (real Chromium via Playwright) as an integration layer
- Coverage reporting (dropped in implementation — see CI section) and a Codecov `javascript` flag
- Any refactor of the JS files beyond the attachment blocks
