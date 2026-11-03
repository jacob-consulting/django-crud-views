---
phase: "04"
slug: "alert-dismiss-adapter"
status: validated
nyquist_compliant: true
wave_0_complete: true
updated: "2026-10-26"
created: "2026-10-26"
---

# Phase 04 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Existing pytest/Django and Vitest/jsdom |
| Config | pyproject.toml; vitest.config.js; tests/js/helpers/setup.js |
| Quick Python | `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` |
| Quick JS | `npm --prefix . test -- tests/js/adapters.test.js tests/js/viewset.test.js` |
| Full Python | `.venv/bin/pytest tests -n auto` |
| Full JS | `npm --prefix . test` |
| Docs | `.venv/bin/mkdocs build --strict` |
| Estimated quick runtime | Under 10 seconds; research baseline 50 Python and 25 JS tests passed |

Installed JS/Ruff versions differ from manifests; execution must record the actual versions and disposition,
without claiming manifest-version validation. See 04-RESEARCH.md. No new framework is required.

## Sampling Rate

- After each task commit: run relevant quick suite; every baseline golden comparison runs without update mode.
- After each implementation wave: run both quick suites and full JS tests.
- Before phase verification: full Python/JS, strict docs, Ruff check/format, source audit and example smoke.
- Max focused feedback latency: 10 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 04-01 | 1 | ALRT-01 | T-04-01 | Exact baseline before product edits | golden/history | `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` | Suite exists; new golden/test | green (f6982bf baseline-only; 04-ACCEPTANCE §3) |
| 04-01-02 | 04-01 | 1 | ALRT-02, ALRT-03 | T-04-02 | Marker selects nearest frame; fallback belongs to adapter; message assertions move with template | rendered tracer | Quick Python followed by Quick JS | Suites exist; new tracer | green (RED ca2069c, GREEN 910625b) |
| 04-01-03 | 04-01 | 1 | ALRT-02 | T-04-01 | Escaping, translated name and non-dismissible behavior | render/response | Quick Python | Extend existing suites | green (3d63404) |
| 04-02-01 | 04-02 | 2 | ALRT-03 | T-04-03 | Present component owns no-op/throw; lazy namespace preserved | JS regression | Quick JS | Extend existing suite | green (c5327b9) |
| 04-02-02 | 04-02 | 2 | ALRT-02, ALRT-03 | T-04-03, T-04-04 | Dynamic/nearest selection; two controls; surfaced errors/missing key; repeated clicks | JS regression | Quick JS followed by `npm --prefix . test` | Extend suite; reuse listenerErrors | green (3990826; full JS 183 passed) |
| 04-03-01 | 04-03 | 3 | ALRT-04 | T-04-05 | Unique full heading/template fence; recipe colour/escaping; core-only subset audit; settings hook list | render/docs/audit | Quick Python and `.venv/bin/mkdocs build --strict` | Suite/docs exist; new recipe/guard tests | green (d3ec24b; 57 focused passed, strict docs clean) |
| 04-03-02 | 04-03 | 3 | ALRT-04 | T-04-06 | Migration distinguishes pre-load defaults from post-load replacement; Added/Breaking enumerate four adapters | docs | `.venv/bin/mkdocs build --strict` plus semantic documentation review | Existing | green (57da26a; strict docs clean, executor semantic review passed, 04-ACCEPTANCE §7) |
| 04-03-03 | 04-03 | 3 | ALRT-01..04 | T-04-01..06 | Three fresh browser messages with active adapter/restoration recorded; all quality gates evidenced | smoke/full suite/history | Full gates below | Existing tools; new acceptance artifact | green with exception: all gates run, ruff format red on 8 pre-existing .planning files (04-ACCEPTANCE §2); browser A/B/C observed (§6) |

Regression matrix: Bootstrap instance close; no component removal; late global/object/function namespaces;
preassigned and call-time replacement adapters; no-op and throwing custom adapters (including mutation before
throw); throwing present Bootstrap component; nested click, nearest role, orphan marker, unrelated/non-Element
targets; dynamic modal-like insertion; non-dismissible output; escaping, translated labels and frame/body overrides.
For listener exceptions and ignored targets reuse listenerErrors from tests/js/helpers/errors.js; assert
original errors or an empty array. Include two controls in one frame, outer/sibling retention and the
missing-adapter TypeError and an unmarked alert-body click with no call/error/removal. Each new JS case owns
a fresh cv/adapters object before nested mutation; restore untouched original descriptors and console spies,
preserving shared jQuery stubs.
The orphan-control click explicitly leaves defaultPrevented=false. The detached-subtree case proves only
the declared DOM-propagation boundary; attached matched-event cases prove handler dispatch.

## Wave 0 Requirements

- [x] Add deterministic dismissible golden/test and commit BEFORE any template change (ALRT-01).
- [x] Add meaningful regressions to existing adapter/delegation suites.
- [x] Update message and alert attribute assertions together; preserve all other output.
- [x] Final planner task IDs and phase-unique threat references replace provisional mapping above.

The before-change golden is task 04-01-01's separate first commit. The product tracer is 04-01-02 and
shares that exact golden between Python rendering and jsdom interaction. Both message assertion updates
belong to the tracer's GREEN stage, whose combined Python/JS gates must pass before its implementation
commit. RED first changes only viewset.test.js and fails against the committed legacy golden; a RED commit,
when required by execution, is test-only and follows the baseline. The six-file tracer is
deliberate; 04-01-03 adds broader regressions afterward. No framework/scaffold installation is needed.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real example flash messages close | ALRT-02, ALRT-04 | Browser transition and script integration | Produce three fresh messages A/B/C. Close A with real Bootstrap; close B with only the alert entry replaced by the missing-Alert factory; restore/reload before creating C, clone C into dynamic content and close the clone with restored Bootstrap. Record the adapter, outcome and console errors for each case or its actual blocker. |
| Migration load order and release enumeration | ALRT-04 | Semantic documentation accuracy beyond a successful build | Compare rendered migration with the adapter reference: pre-load maps receive missing defaults, post-load whole replacements must supply alert.close, and per-entry/default-preserving fixes are named. Compare existing Unreleased Added with all four reference adapters and the new Breaking entry. |
| Golden chronology | ALRT-01 | Commit ordering | Confirm a baseline-only commit precedes template change; final golden diff changes only dismissal attribute. |

Run example docs sync from examples/bootstrap5: `../../.venv/bin/pytest test_docs_sync.py -q`.
The plain `rg -n 'data-bs-' src/crud_views/templates` command is an audit: validate its output against
the exact dropdown paths named in theme.md, not merely its exit status.

Automated allowlist coverage is planned in `test_stock_bootstrap_data_attributes_are_dropdown_only`:
scan exactly `src/crud_views/templates`, using paths relative to that root. Only
`crud_views/tags/actions_menu.html`, `crud_views/tags/actions_menu_toggle.html` and
`crud_views/snippets/language_selector.html` are allowed; require nonempty matches and matches <= ALLOWED,
not equality. The wrapper need not match. Report forbidden paths. For historical red, copy the core tree
to a temporary directory and replace its alert template with the baseline commit's snapshot via git show;
invoke the same helper there and confirm the alert path fails, without changing the checkout. Baseline:
four matching lines in alert.html, actions_menu_toggle.html and language_selector.html.

Permanent negative coverage: `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` builds an
allowed tree under tmp_path and confirms success, adds a forbidden alert file, and requires AssertionError
naming that relative path. This lasts independently of the one-time historical git-show probe.

Recipe verification uses the full heading `### Custom alert frame` below `## Alerts` and exactly one
django/html fence. The Python-only FENCE matcher from the analogous docs test does not apply; missing or
ambiguous headings/fences fail before the real recipe render. Record the historical probe's rejected path
and full baseline SHA separately in acceptance evidence; no permanent pytest may depend on Git history.

## Final Execution Gates and Evidence

Run from repository root unless stated otherwise:

- `.venv/bin/pytest tests -n auto`
- `npm --prefix . test`
- `.venv/bin/mkdocs build --strict`
- `.venv/bin/ruff check`
- `.venv/bin/ruff format --check`
- `.venv/bin/python examples/bootstrap5/manage.py check`
- From examples/bootstrap5: `../../.venv/bin/pytest test_docs_sync.py -q`

Record actual browser/version, page/action, rendered marker/script order, Bootstrap transition close,
fresh-message missing-Alert close and post-load inserted message close in `04-ACCEPTANCE.md`. Identify A/B/C,
each active adapter, and restoration before creating/cloning C. The original C must remain attached while
the dynamically inserted clone closes with the restored Bootstrap adapter. Record unavailable cases separately.
Plan 04-03 contains the exact reproducible browser procedure. Missing browser/server/CDN evidence stays
unverified and routes to end-of-phase human verification. System check/docs sync are not browser evidence.
Retain all five unresolved classifier assumptions from `04-SOURCE-AUDIT.md`; two resolved ALRT-03
repeated-call/click predicates are explicit 04-02 must-haves. No new lifecycle guarantee is claimed.

Planning verification: all three plans passed frontmatter/structure checks; baseline focused suites passed
50 Python / 25 JS tests again during Round 3 review incorporation (0860fcf); these are pre-change results.
All four R04-01..04 findings now have executable plan actions and verification/acceptance. Product
implementation, the documentation semantic review and browser acceptance remain pending. Installed-tool drift
and any pre-existing full-gate failures must be recorded honestly, without weakening gates or changing manifests.

## Validation Sign-Off

- [x] All tasks have automated verification or Wave 0 dependencies.
- [x] No three consecutive tasks lack automated feedback.
- [x] Wave 0 covers all missing references; no watch flags.
- [x] Focused feedback latency stays under 10 seconds (focused Python 1.25 s, full JS 1.80 s).
- [x] Required quality gates and example smoke have evidence (04-ACCEPTANCE.md). `ruff format --check` exits 1 on
  the 8 pre-existing `.planning/` Markdown files only; recorded as an exception, not as green.
- [x] Set nyquist_compliant only after validation is actually complete.

## Execution Results (2026-10-26)

Observed after the final 04-03 edits; details and limits in `04-ACCEPTANCE.md`.

| Gate / evidence | Result |
|-----------------|--------|
| Full Python | 3495 passed, 1 skipped |
| Full JS | 183 passed (Vitest 4.1.10 / jsdom 29.1.1 installed, below `^5.0.3` / `^30.1.2`) |
| Strict docs | clean |
| Ruff check | passed (Ruff 0.16.10 installed, below `>=0.17,<0.18`) |
| Ruff format check | exit 1: 8 pre-existing `.planning/` Markdown files, none touched in Phase 4 |
| Example system check | no issues |
| Example docs sync | 36 passed |
| Golden chronology | baseline `f6982bfef24f4322cfd01f9f21c3bbed517462fe`; later diff is only the dismiss attribute; no other golden changed |
| Data-attribute audit | only `actions_menu_toggle.html` and `language_selector.html` match; historical baseline `alert.html` rejected in a temporary tree |
| Browser A (real Bootstrap) | Chrome 156 headless: `show` removed, `closed.bs.alert`, frame removed after 183 ms |
| Browser B (missing Alert) | only the alert entry swapped to `cv.bootstrapAdapters({}).alert`: frame removed synchronously; other adapters kept identity; restored |
| Browser C (post-load clone) | fresh page, default adapter: clone removed after 164 ms via Bootstrap; original C and modal-like host still attached |

**Approval:** automated validation complete. The documentation semantic review was run by the executor only.
Browser acceptance was automated (headless Chrome, not a person watching). Both go to end-of-phase human
verification.

## Validation Audit 2026-10-26

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
