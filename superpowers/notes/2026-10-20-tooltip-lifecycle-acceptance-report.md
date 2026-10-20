# Task 5 report: tooltip lifecycle acceptance (2026-10-20)

Branch `feat/tooltip-lifecycle` (merge base `0167b3c` on main, HEAD `3f3358a` before this report). Plan
`superpowers/plans/2026-10-20-tooltip-lifecycle.md`, spec `superpowers/specs/2026-10-20-tooltip-lifecycle-design.md`,
issue #203. Browser: Chrome 155 (Linux), example project served by `runserver` on port 8010 (8000 was taken by another
process), Bootstrap 5.3.3 from jsDelivr, default `cv.adapters`.

## Step 1: suites
- `uv run pytest tests -q`: 1511 passed, 3 skipped (112 s). No Python changed; unchanged from the baseline run.
- vitest (Node 22, `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`): 8 files, 125 tests passed
  (baseline 109; +2 adapters, +3 modal, +11 tooltip).
- `task check`: all checks passed. `task format`: 423 files left unchanged.
- `uvx 'ruff>=0.16' format --check .`: 483 files already formatted. `uv run mkdocs build --strict`: clean.

## Step 2: click half (`/library/author/`, filter toggle `#cv-filter-toggle`, marker `context`)
- Hover the toggle: 1 `.tooltip.show` ("Filter"). Click it with the mouse, move the pointer to the heading:
  `.tooltip.show` 0, `.tooltip` elements 0, `document.activeElement` is still the toggle, `aria-expanded` true and the
  panel open. The focus-retained tooltip from issue #203 case 1 is gone.
- Hover the toggle again: 1 `.tooltip.show`; move away: 0 (after a hide the focus trigger is cleared, so the still
  focused toggle behaves as hover-only until focus re-enters, as the spec says).
- Keyboard: `focus()` on the toggle shows the tooltip (1); Enter hides it (0, toggle still focused, panel toggled).

## Step 3: dispose half (object-detail modal with one marked `object-detail` button)
Temporary, uncommitted lines on the example's `library.views.AuthorDetailView`: `cv_modal = True` and
`cv_object_detail_layout = "card-rows"` (the example's default `split-card` layout renders `prop.detail` as text; only
`card-rows` renders the marked button). Reverted after the run; `git status` is clean.

Counter: `addEventListener` / `removeEventListener` overridden on the `#cv-modal` element instance from page context,
installed after a hard reload and before the first open, counting the type `hide.bs.modal`. Note for the next person:
Bootstrap's `EventHandler` registers non-native event names under their full dotted name (`normalizeParameters` falls
back to the original type when it is not in `nativeEvents`), so the listener is `hide.bs.modal`, not `hide`; in the
DevTools console that is `getEventListeners($0)["hide.bs.modal"]`.

Cycle = `cv.cvModalOpen(url)` (await `cv:modal:loaded` and `shown.bs.modal`), then `cv.adapters.modal.hide(modal)`
(await `hidden.bs.modal`). The first open was also done with a real click on the row's detail link.

| Build | Cycles | `hide.bs.modal` handlers on `#cv-modal` after each open | adds / removes | `.tooltip` left |
|---|---|---|---|---|
| branch (`6f1b80f`) | 10 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 | 10 / 9 | 0 |
| main (`git checkout main -- adapters.js modal.js tooltip.js`, hard reload) | 3 | 1, 2, 3 | 3 / 0 | 0 |

The served `tooltip.js` was checked for the string `cv:modal:unload` before each run (present on the branch, absent on
main; `cv.adapters.tooltip` keys `init, hide, dispose` versus `init`). The three scripts were restored with
`git checkout HEAD -- ...` and the served version re-checked afterwards.

## Step 4: notes, recorded not fixed
- Fast click: `t.focus(); t.click()` synchronously on the filter toggle leaves 1 `.tooltip.show` after the next tick
  (Bootstrap defers `show()` to a 0 ms timeout, the click arrives first and `hide()` returns early). The same with
  50 ms between focus and click: 0. A human click cannot beat the tick; the chrome-devtools `click` tool can, when it
  moves the pointer and clicks in one task without a prior hover.
- Touch (Chrome device emulation 390×844, touch, mobile; the `click` tool's mouse-derived events, not a real touch
  sequence): tapping the object-detail info button in the modal leaves 1 `.tooltip.show` with the hover and focus
  triggers active, so the tooltip shows and stays after the tap, as the spec predicted. On desktop, hovering that
  button shows the tooltip and a mouse click hides it (0), the approved "any click hides" behaviour (spec, decision 2).
- No console errors or warnings during any of the runs.

## Outcome
All acceptance criteria from the spec hold in the browser: the click-retained tooltip is gone, keyboard activation
hides too, an adapter with only `init` is covered by the vitest cases, and the `hide.bs.modal` handler count on
`#cv-modal` no longer grows with each modal open.
