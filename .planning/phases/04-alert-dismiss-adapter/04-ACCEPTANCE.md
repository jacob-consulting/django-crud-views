---
phase: 04-alert-dismiss-adapter
plan: "03"
type: acceptance
created: "2026-10-26"
status: evidence-recorded
---

# Phase 04: Acceptance evidence

All results below were observed on 2026-10-26 on branch `introduce-gsd`, after the final 04-03 documentation edits
(commits `d3ec24b` and `57da26a`). Nothing is inferred. Limits are listed at the end of each section.

## 1. Environment and installed-tool drift

| Tool | Installed (observed) | Declared | Disposition |
|------|----------------------|----------|-------------|
| Python | 3.12.3 (`.venv`) | matrix 3.12-3.15 | in range |
| Django | 5.2.14 | matrix 4.2 / 5.2 / 6.0 | in range; one matrix row only |
| Ruff | 0.16.10 | `pyproject.toml` `ruff>=0.17,<0.18`; pre-commit pins v0.17.1 | **drift**: below the declared range. Not changed. Ruff results below are 0.16.10 results, not manifest-clean ones |
| Vitest | 4.1.10 | `package.json` `^5.0.3` | **drift**: below the declared range. Not changed |
| jsdom | 29.1.1 | `package.json` `^30.1.2` | **drift**: below the declared range. Not changed |
| Node | v20.20.2 | `engines` `>=20` | in range |
| MkDocs | 1.6.1 | n/a | recorded |
| Browser | Google Chrome 156.0.8078.47, headless, driven by playwright-core 1.60.0 | n/a | already on disk (npx cache); nothing was installed |

No manifest, lockfile or tool version was changed to hide the drift. The JS and Ruff gates below therefore prove the
behaviour under the installed versions only.

## 2. Final gates

All run from the repository root after the last product and documentation edit.

| Command | Result | Exit |
|---------|--------|------|
| `.venv/bin/pytest tests -n auto` | 3495 passed, 1 skipped, 25.45 s | 0 |
| `npm --prefix . test` | 8 files, 183 tests passed, no unhandled errors | 0 |
| `.venv/bin/mkdocs build --strict` (built to a scratch directory) | built, no warnings (`validation.anchors: warn` is active) | 0 |
| `.venv/bin/ruff check` | All checks passed | 0 |
| `.venv/bin/ruff format --check` | **8 files would be reformatted**, 639 already formatted | **1** |
| `.venv/bin/python examples/bootstrap5/manage.py check` | System check identified no issues (0 silenced) | 0 |
| `cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q` | 36 passed | 0 |

**`ruff format --check` is not green.** It flags the same 8 pre-existing `.planning/` Markdown files that 04-01
recorded, and this phase touched none of them:

- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/phases/01-label-mode-defaults/01-PATTERNS.md`
- `.planning/phases/01-label-mode-defaults/01-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-VERIFICATION.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/STACK.md`

Every Python and Markdown file changed in Phase 4 is formatted. The failure predates the phase (see the Phase 2
blocker in STATE.md and WINDOWS entry 4). It is reported here, not fixed and not counted as a pass.

## 3. Golden chronology (ALRT-01, D-07)

- Baseline commit: `f6982bfef24f4322cfd01f9f21c3bbed517462fe`, "test(04-01): commit dismissible alert golden baseline
  before dismiss hook change". It contains only `tests/test1/golden/alerts/dismissible.html` and
  `tests/test1/test_alerts.py`; no product file.
- The only later commit touching `tests/test1/golden/` is `910625b` (the 04-01 tracer GREEN).
- `git diff f6982bf HEAD -- tests/test1/golden/alerts/dismissible.html` changes exactly one line:
  `data-bs-dismiss="alert"` becomes `data-cv-alert-dismiss`.
- `git diff --stat 1b77934 HEAD -- tests/test1/golden/` (from before the phase) lists only
  `tests/test1/golden/alerts/dismissible.html`. No other golden changed in Phase 4.

## 4. Core template data-attribute audit (ALRT-04, D-09)

- `rg -n 'data-bs-' src/crud_views/templates` reports 3 lines: `crud_views/tags/actions_menu_toggle.html:4`, `:5` and
  `crud_views/snippets/language_selector.html:6`. Both paths are in the allowlist named in `theme.md`.
  `crud_views/tags/actions_menu.html` is an allowed wrapper with no `data-bs-*` attribute, and that is accepted.
- The lasting guard is `tests/test1/test_alerts.py::test_stock_bootstrap_data_attributes_are_dropdown_only`. It scans
  only `src/crud_views/templates` and requires a nonempty subset of the three allowed paths.
- The lasting negative test is `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path`. It uses `tmp_path`
  only: an empty tree fails, an allowed toggle tree passes, and adding `crud_views/tags/alert.html` with a
  `data-bs-*` attribute fails with that path in the message.
- **One-time historical probe**, not committed and with no Git dependency in any test: the current core tree was copied
  to a temporary directory, and its `crud_views/tags/alert.html` was replaced with
  `git show f6982bfef24f4322cfd01f9f21c3bbed517462fe:src/crud_views/templates/crud_views/tags/alert.html`. The same
  helper then failed with `Bootstrap data attributes outside the dropdown templates: ['crud_views/tags/alert.html']`.
  On the real core root it passed. The checkout was not modified (`git status --short src/` clean).
- Source audit: all seven input rows remain in `04-SOURCE-AUDIT.md`. A04-01, A04-02 and the three ALRT-04 rows
  (adjacency, empty, ordering) stay unresolved and flagged. They were not auto-dismissed.

## 5. Documented recipe (ALRT-04, D-02)

`test_documented_alert_frame_override` extracts the single `django`/`html` fence below `### Custom alert frame` in the
`## Alerts` section of `docs/reference/theme.md`. It renders that fence as the `crud_views/tags/alert.html` override.

Temporary mutations of `theme.md`, each restored and checked byte-identical with `cmp`, were all caught:

- marker removed
- literal (untranslated) `aria-label`
- hard-coded colour instead of `cv_button_class`
- unconditional close control
- `role="alert"` removed
- a second template fence
- the heading renamed
- the heading duplicated

Adding `|safe` to the heading was **not** caught, and that is correct: `alert_data()` escapes the values before the
frame sees them. So the recipe cannot unescape them, and the test asserts the escaped output.

## 6. Browser acceptance (D-10, ALRT-02)

- **Setup:** `.venv/bin/python examples/bootstrap5/manage.py runserver 127.0.0.1:8000 --noreload`. The example
  database was already migrated and seeded: `alice` holds `library.add/change/delete/view_author`, and 3 authors
  exist.
- **Login:** `http://127.0.0.1:8000/login/` with `alice` / `alice`, which redirected to `http://127.0.0.1:8000/`.
- **Messages:** each message came from a real successful submit of the Author update form,
  `http://127.0.0.1:8000/library/author/0e90310d-4361-4bbc-8c44-e6aaf8f92ec6/update/` ("Ursula Le Guin"), with
  unchanged values. Each submit redirected to `http://127.0.0.1:8000/library/author/`. Update was used instead of
  create so the local example database gains no rows.
- **Driver:** headless Google Chrome 156.0.8078.47, driven by a scratch Playwright script. The script is not
  committed.

Each of the three result pages showed the same markup and script order:

- exactly one dismissible frame, `class="alert alert-success alert-dismissible fade show"`, text
  `Updated author “Ursula Le Guin”`
- the control carries `data-cv-alert-dismiss`, has no `data-bs-dismiss`, and has `aria-label="Close"`
- script order: `crud_views/js/adapters.js` is script #2 and `crud_views/js/viewset.js` is script #3 (0-based
  `document.scripts` index among scripts with a `src`)
- `bootstrap.Alert` is a function, `bootstrap.Alert.VERSION` is `5.3.3` from the jsDelivr CDN, and the active
  `cv.adapters.alert.close` is the stock default (its source resolves `component(ns, "Alert")`)

| Case | Message | Active alert adapter | Action | Observation | Console / errors |
|------|---------|----------------------|--------|-------------|------------------|
| A: real Bootstrap | A, fresh, from submit 1 | stock default, real global `bootstrap.Alert` 5.3.3 | clicked A's close control | Frame still attached right after the click, `show` removed at +1 ms, `closed.bs.alert` fired, frame removed after 183 ms, so the Bootstrap fade transition ran | no window errors; one console error, `GET /favicon.ico` 404 (server log), unrelated |
| B: missing Alert | B, fresh, from submit 2 (A already removed) | only `cv.adapters.alert` replaced with `cv.bootstrapAdapters({}).alert`. The global `bootstrap.Alert` was still loaded, but the adapter's namespace has no `Alert` | clicked B's close control | Frame removed synchronously, by the fallback; `modal`, `tooltip` and `collapse` keep their identity. The saved adapter was restored in `finally`, and the restored entry was confirmed to be the stock default | none |
| C: post-load clone, restored Bootstrap | C, fresh, from submit 3; a new page load after B's restoration | stock default with real `bootstrap.Alert`, confirmed on the C page before cloning | cloned the still-attached C frame into a new `div.modal-like > div.modal-like-content` appended after load; clicked the clone's close control with no initialiser | Clone attached right after the click, `show` removed at +1 ms, `closed.bs.alert` fired, clone removed after 164 ms. The original C stayed attached, and the modal-like host stayed attached | none |

**Limits:**

- The run was automated in a headless browser. It is not a person watching the fade. The transition is evidenced by
  the removal of `show`, the 164 to 183 ms delay and Bootstrap's `closed.bs.alert` event.
- Only Chrome was exercised.
- Case B proves the missing-component path of the default adapter through the factory, with a namespace that lacks
  `Alert`, while Bootstrap's JavaScript stayed loaded. No page without Bootstrap's JavaScript at all was tried; the
  04-02 jsdom matrix covers that.
- No custom (non-factory) theme adapter was driven in the browser. The 04-02 jsdom matrix covers custom adapters and
  their error ownership.

## 7. Documentation semantic review (04-03-02 human-check)

Reviewed by the executor on the rendered build; this is not yet a maintainer review.

- The `migrating-1.0.md` "Hooks instead of copies" JavaScript bullet and the `javascript.md` `cv.adapters` section
  both make the same three points:
  - a partial map assigned before `adapters.js` gets its missing defaults;
  - a whole-map replacement after core loads must provide `alert.close(el)`, or the click throws a `TypeError`;
  - the fixes are per-entry replacement or `Object.assign`, plus `cv.bootstrapAdapters(ns).alert`.
- Neither text implies that a missing post-load key falls back to the default.
- The CHANGELOG Unreleased Added line lists `modal`, `tooltip`, `collapse` and `alert`. That matches the reference's
  four adapters and the new Breaking entry. The "All three" lifecycle-events sentence in `javascript.md` is
  unchanged.
- Outcome: pass. Final sign-off is left to end-of-phase human verification.

## 8. Follow-up for downstream themes

Not acted on here, and no other project was changed. A downstream theme that ships its own `crud_views/tags/alert.html`
should adopt `data-cv-alert-dismiss` on the close control. When it styles the frame its own way, it should keep the
semantic hooks: `role="alert"` on the frame, the marker, the dismissible condition, `type="button"` and the translated
`aria-label`. A theme that replaces the whole `cv.adapters` map after core loads must add an `alert` entry.
