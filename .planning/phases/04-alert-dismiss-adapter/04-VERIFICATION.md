---
phase: 04-alert-dismiss-adapter
verified: 2026-10-26T20:55:52Z
status: human_needed
score: 20/21 must-haves verified
covered_files:
  - ".planning/phases/04-alert-dismiss-adapter/04-01-PLAN.md"
  - ".planning/phases/04-alert-dismiss-adapter/04-01-SUMMARY.md"
  - ".planning/phases/04-alert-dismiss-adapter/04-02-PLAN.md"
  - ".planning/phases/04-alert-dismiss-adapter/04-02-SUMMARY.md"
  - ".planning/phases/04-alert-dismiss-adapter/04-03-PLAN.md"
  - ".planning/phases/04-alert-dismiss-adapter/04-03-SUMMARY.md"
  - "CHANGELOG.md"
  - "docs/migrating-1.0.md"
  - "docs/reference/javascript.md"
  - "docs/reference/messages.md"
  - "docs/reference/settings.md"
  - "docs/reference/theme.md"
  - "src/crud_views/static/crud_views/js/adapters.js"
  - "src/crud_views/static/crud_views/js/viewset.js"
  - "src/crud_views/templates/crud_views/tags/alert.html"
  - "tests/js/adapters.test.js"
  - "tests/js/viewset.test.js"
  - "tests/test1/golden/alerts/dismissible.html"
  - "tests/test1/test_alerts.py"
  - "tests/test1/test_messages.py"
covered_digest: "v4:sha256:448ca0cdfcebb56021f993b4a4da392b90b0f3cc29cd653745a463ef98c6c75d"
behavior_unverified: 1
overrides_applied: 0
decision_coverage:
  honored: 10
  total: 10
  not_honored: []
behavior_unverified_items:
  - truth: "The example project's flash messages still close in a real browser (ROADMAP SC4; plan 04-03 truth 6: three fresh example messages prove real Bootstrap close, missing-Alert close and injected-content close)"
    test: "Run examples/bootstrap5 (`.venv/bin/python examples/bootstrap5/manage.py runserver 127.0.0.1:8000`), log in as alice/alice, submit the Author update form three times and dismiss each resulting flash message per 04-03-03's A/B/C procedure (A: stock adapter + real bootstrap.Alert; B: `cv.adapters.alert = cv.bootstrapAdapters({}).alert`, then restore; C: fresh page, clone the attached frame into a post-load modal-like div and click the clone's X)"
    expected: "A: frame fades (`show` removed, `closed.bs.alert` fires) and is removed; B: frame removed synchronously, other adapters keep identity; C: the clone is removed via Bootstrap, the original C frame and the modal-like host stay attached; no console errors beyond /favicon.ico 404"
    why_human: "The jsdom suites prove delegation and adapter ownership with fake Alert components. Bootstrap's real fade transition and the CDN bundle are outside the repo test suite; the executor's headless-Chrome evidence (04-ACCEPTANCE.md section 6) came from an uncommitted scratch Playwright script, so it is not reproducible from the repository"
human_verification:
  - test: "Repeat the three-message browser procedure (A/B/C) in the example project, as described in behavior_unverified_items above"
    expected: "All three messages close through the documented path; A and C via Bootstrap's Alert transition, B via the default adapter's el.remove() fallback"
    why_human: "Real browser transition and CDN Bootstrap; the headless run in 04-ACCEPTANCE.md was executor-automated and its driver script is not in the repo"
  - test: "Maintainer reading of the upgrade prose (harvested from 04-03-02 human-check): read docs/migrating-1.0.md 'Hooks instead of copies' JavaScript bullet (lines ~319-329) and 'The alert frame' before/after (lines ~364-385) beside docs/reference/javascript.md's `cv.adapters` whole-map paragraph (lines ~55-70) and 'Dismissible alerts' (lines 188-215), plus CHANGELOG.md Unreleased Breaking (lines 22-33) and Added (line 306). While there, decide WR-01 and IN-03 from 04-REVIEW.md: theme.md:212-214 says the dropdown templates are 'the only stock templates with Bootstrap data-bs-* attributes', but crud_views_object_detail's accordion/group.html and tabs-vertical/object_detail.html also carry data-bs-toggle/target/parent; and messages.md:40-41 says the X 'does nothing' without the core scripts, whereas viewset.js without adapters.js throws a TypeError on click"
    expected: "Both texts distinguish pre-load default filling from post-load whole-map replacement, require alert.close(el) in a later replacement and show cv.bootstrapAdapters(ns).alert; Added, reference and Breaking all name four adapters (they do, per grep). WR-01: either scope the theme.md sentence to crud_views core templates (one-line fix suggested in 04-REVIEW.md) or accept the Phase 7 deferral recorded in 04-03-PLAN.md's review ledger"
    why_human: "Semantic accuracy of upgrade prose is a judgment call; mkdocs --strict only validates anchors. The executor's own review (04-ACCEPTANCE.md section 7) is not a maintainer review, and WR-01 is a true over-claim the guard test cannot catch because it scans only src/crud_views/templates"
---

# Phase 4: Alert dismiss adapter Verification Report

**Phase Goal:** Dismissible alerts close through the `cv.adapters` seam, so a non-Bootstrap theme no longer copies the alert frame for a single `data-bs-*` attribute.
**Verified:** 2026-10-26T20:55:52Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

The phase goal is achieved in the codebase. The stock frame (`src/crud_views/templates/crud_views/tags/alert.html:5`) carries `data-cv-alert-dismiss` and no `data-bs-*` attribute; `viewset.js:46-55` delegates the click on `document` to `globalThis.cv.adapters.alert.close(frame)` resolved at click time; `adapters.js:41-49` adds `alert.close(el)` to the factory with the `Alert`-present / `el.remove()` branches. `{% cv_js %}` renders `adapters.js` before `viewset.js` (`src/crud_views/lib/settings.py:288-289`). All 35 alert-related vitest cases and the five Python alert tests were run by name here and pass. The only item that cannot be closed from the repository is the real-browser transition in the example project, which the executor automated in headless Chrome with an uncommitted script; it is routed to human verification together with the maintainer prose review the plan deferred to end-of-phase.

### Observable Truths

Roadmap Success Criteria (contract) first, then plan truths that add detail; duplicates of a roadmap SC are folded into it.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| R1 | A golden of today's dismissible alert is committed first, so the PR shows the markup diff (ALRT-01) | ✓ VERIFIED | `git show --stat f6982bf`: only `tests/test1/golden/alerts/dismissible.html` (+7) and `tests/test1/test_alerts.py` (+22); `git diff f6982bf~1 f6982bf -- src/` empty; `git merge-base --is-ancestor f6982bf 910625b` true; `git diff f6982bf HEAD -- …/dismissible.html` is exactly one line `data-bs-dismiss="alert"` → `data-cv-alert-dismiss`; `git diff --stat 1b77934 HEAD -- tests/test1/golden/` lists only that golden |
| R2 | Clicking an alert's close button closes it through `cv.adapters.alert.close`, with Bootstrap's `Alert` present; without it the alert is removed; alerts injected after page load close too (ALRT-02/03) | ✓ VERIFIED | Behavior-dependent; behavioral evidence: `npx vitest run tests/js/viewset.test.js -t "rendered alert dismissal tracer"` → 2 passed (present Alert: `getOrCreateInstance(frame)` once + `close()` once, frame attached; absent: frame removed, sibling kept, `defaultPrevented` true); `-t "inserted into modal-like content"` → 1 passed; `-t "delegated alert ownership"` → 16 passed; `tests/js/adapters.test.js -t "alert adapter ownership"` → 16 passed. Code: `viewset.js:47-55`, `adapters.js:44-48` |
| R3 | The stock frame renders `data-cv-alert-dismiss` and no `data-bs-dismiss`; `grep -rn 'data-bs-' src/crud_views/templates` lists only the dropdown templates named in `theme.md` (ALRT-04) | ✓ VERIFIED | `cat -A alert.html` line 5 shows `data-cv-alert-dismiss`; grep returns 3 lines in `tags/actions_menu_toggle.html:4,5` and `snippets/language_selector.html:6`, both listed under theme.md "## Templates that follow Bootstrap's DOM"; `test_stock_bootstrap_data_attributes_are_dropdown_only` and `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` pass. Warning WR-01 on theme.md wording — see Anti-Patterns |
| R4 | The example project's flash messages still close; `javascript.md`, `messages.md`, `theme.md`, the CHANGELOG Breaking entry and the migration bullet are updated (ALRT-04) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Docs part verified: javascript.md:14,39,44,59-69,188-215; messages.md:27-44; theme.md:177-214; settings.md:184,189; CHANGELOG.md:22-33 (Breaking) and :306 (Added, four adapters); migrating-1.0.md:175-177,205-206,314-329,364-385,417-434; `mkdocs build --strict` exit 0 here. Example wiring present: `examples/bootstrap5/project/templates/project/base.html` loads bootstrap.bundle (l.19), `{% cv_js %}` (l.37), `{% cv_messages %}` (l.56); no `alert.html` override under `examples/`. Real-browser closing is evidenced only by the executor's uncommitted headless-Chrome run (04-ACCEPTANCE.md §6) — routed to human verification |
| P1-2 | A stock dismissible alert reaches the current `cv.adapters.alert.close` through its rendered `data-cv-alert-dismiss` control and nearest `role=alert` frame (D-08) | ✓ VERIFIED | `viewset.js:49-54` (`closest("[data-cv-alert-dismiss]")` → `closest('[role="alert"]')` → `globalThis.cv.adapters.alert.close(frame)`); tracer test loads the real golden via `fs.readFileSync(../test1/golden/alerts/dismissible.html)` (viewset.test.js:11-12) |
| P1-3 | With `Alert` present the default adapter delegates close to its instance; with `Alert` absent it removes the frame (D-04) | ✓ VERIFIED | `adapters.js:44-48`; tracer tests + "hands the frame to a present Alert component", "removes exactly the supplied frame when no bootstrap global exists" pass |
| P1-4 | Alerts inserted after script loading close through the same document listener without initialization (D-08) | ✓ VERIFIED | "closes an alert inserted into modal-like content after the scripts loaded" and "removes an inserted modal alert through the fallback and keeps the modal" pass |
| P1-5 | Frame classes, role, translated close label, content escaping and non-dismissible rendering retain their contract (D-01, D-07) | ✓ VERIFIED | `test_dismissible_alert_preserves_frame_contract` (class `alert alert-success alert-dismissible fade show`, `btn-close`, `type=button`, aria-label Close, no `data-bs-dismiss`), `test_dismissible_alert_close_label_is_translated` (gettext sentinel), `test_dismissible_alert_escapes_heading_text_and_extra_tags`, `test_cv_alert_is_not_dismissible_by_default` — all pass; golden diff is one attribute |
| P1-6 | Real create-response messages render the new dismiss hook with their original safe content and classes (D-10) | ✓ VERIFIED | `test_create_message_renders_as_an_alert` (real client POST `/publisher/create/` + follow, lxml-parsed frame/control, `data-bs-dismiss` absent) passes; `test_cv_messages_renders_a_dismissible_alert` passes |
| P2-1 | Themes can preassign the whole alert adapter or replace it after loading; the next click uses that exact adapter (D-08) | ✓ VERIFIED | `adapters.js:52` `Object.assign(cv.bootstrapAdapters(...), cv.adapters || {})`; tests "keeps a preassigned alert adapter by identity and fills the other defaults", "uses the alert adapter assigned after load for the next click" pass |
| P2-2 | Object, function and late global namespaces are resolved when close runs; a namespace with other components but no `Alert` uses removal (D-04, D-08) | ✓ VERIFIED | `adapters.js:7-8,45`; tests "resolves a changing callback namespace on every call", "uses a bootstrap global assigned or replaced after the defaults were built", "removes the frame for a build without the alert component" pass |
| P2-3 | A custom no-op keeps the alert; custom errors surface without core logging, forced removal or rollback (D-03) | ✓ VERIFIED | `viewset.js:54` has no try/catch; tests "surfaces a custom adapter's error after its own mutation, with no logging or forced removal", adapter-swap no-op case pass |
| P2-4 | A present `Alert` owns close even when it does nothing or throws; absence alone selects fallback (D-04) | ✓ VERIFIED | Tests "leaves the frame attached when a present component's close does nothing", "surfaces the original error from a present component's (lookup|close)", "surfaces a present component's error through the default adapter" pass |
| P2-5 | Nested control clicks select the nearest `role=alert`, including inserted modal content; orphan, unmarked and non-Element targets do nothing (D-08) | ✓ VERIFIED | Tests "closes only the nearest of nested frames…", `it.each` "ignores %s: no adapter call, no error, no DOM change" (4), "leaves a cancelable click on an orphan marked control un-prevented" pass; `viewset.js:48,50,52` guards |
| P2-6 | EDGE-ALRT-03-idempotency: repeated default close on a detached element is harmless; a present-component frame receives each call | ✓ VERIFIED | Tests "repeats the missing-component fallback harmlessly on the same detached element", "hands every repeated close of an attached frame to a present no-op component" pass |
| P2-7 | EDGE-ALRT-03-concurrency: two rapid clicks invoke the adapter once each; a detached subtree's click never reaches document delegation | ✓ VERIFIED | Tests "calls the current adapter once per rapid click while the frame stays attached", "does not reach document delegation from a frame the fallback already detached" pass |
| P3-1 | Theme authors can use a complete custom-class frame recipe retaining `role=alert`, `data-cv-alert-dismiss`, content and an accessible close control (D-01, D-02) | ✓ VERIFIED | theme.md:195-214 "### Custom alert frame" single `django` fence with `{% load crud_views i18n %}`, `cv_button_class "alert"`, `role="alert"`, conditional `data-cv-alert-dismiss` `type=button` with `{% translate 'Close' %}`; `test_documented_alert_frame_override` extracts and renders that fence as a locmem override and passes |
| P3-2 | The JavaScript reference describes four adapters, current lookup, script requirements and absent-only fallback with surfaced errors (D-03/04/08/09) | ✓ VERIFIED | javascript.md:14 (viewset.js needs `cv.adapters.alert` at use), :39 (`alert` / `close(el)` row), :44, :59-69 (whole-map + `cv.bootstrapAdapters(...).alert`), :188-215 (Dismissible alerts: delegation, call-time lookup, post-load content, `el.remove()` only when no `Alert`, errors uncaught, missing key TypeError) |
| P3-3 | Paired Breaking and migration text shows before/after attributes, recommends conversion even with Bootstrap, distinguishes pre-load defaults from post-load whole-map replacement, describes the legacy Bootstrap-only path (D-05/06/08/09) | ✓ VERIFIED | CHANGELOG.md:22-33; migrating-1.0.md:364-385 (before/after fence at 370/372, "Migrate even if you keep Bootstrap", "Do not keep both attributes", legacy data-API path), :319-329 (pre-load vs post-load, `alert: cv.bootstrapAdapters(ns).alert`); both commit together in 57da26a |
| P3-4 | Unreleased Added enumeration and canonical reference consistently name modal, tooltip, collapse and alert (D-09) | ✓ VERIFIED | CHANGELOG.md:306 "`cv.adapters` (`modal`, `tooltip`, `collapse`, `alert`)"; javascript.md adapter table has the four rows; adapters.js:3 comment "all four" |
| P3-7 | Full Python, JS, docs and Ruff gates have actual outcomes with installed-tool drift disclosed; baseline history proves the sole allowed golden change (D-07, D-10) | ✓ VERIFIED | 04-ACCEPTANCE.md §1-3 records versions (Ruff 0.16.10 vs >=0.17, Vitest 4.1.10 vs ^5, jsdom 29.1.1 vs ^30 — disclosed, not hidden) and `ruff format --check` exit 1 on 8 pre-existing .planning files; orchestrator gates: pytest 3495 passed/1 skipped, vitest 183 passed; my own `git diff --stat 1b77934 HEAD -- tests/test1/golden/` confirms the single golden change |

**Score:** 20/21 truths verified (1 present, behavior-unverified)

Plan truths P1-1 (baseline commit), P3-5 (core-template data-bs allowlist) and P3-6 (three-message browser proof) restate R1, R3 and R4 respectively and are counted there.

### Deferred Items

None. No truth failed, so nothing was checked against later phases for deferral. (WR-01 below is a warning, not a failed truth; Phase 7 "Theme-surface stability policy" is the natural home for widening the theme.md Bootstrap-DOM list to extension packages, as 04-03-PLAN.md's review ledger already recorded.)

### Required Artifacts

`gsd query verify.artifacts` exit 0 for all three plans (6/6, 4/4, 7/7). Level 3/4 checked manually.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/test1/golden/alerts/dismissible.html` | Exact rendered baseline, later changed only at the dismiss attribute | ✓ VERIFIED | 7 lines, raw bytes incl. leading newline; consumed by `test_dismissible_alert_golden` (read_bytes) and `viewset.test.js:11` (readFileSync) |
| `tests/test1/test_alerts.py` | Fixed-locale raw golden comparison, frame regressions, recipe test, allowlist guard | ✓ VERIFIED | 344 lines; `test_dismissible_alert_golden` (l.166), `_dismissible_frame`, contract/translation/escaping tests, `test_documented_alert_frame_override` (l.257), `_assert_core_bootstrap_data_attributes` (l.319), guard + tmp_path negative test |
| `src/crud_views/templates/crud_views/tags/alert.html` | Shared neutral dismiss hook | ✓ VERIFIED | Line 5 `data-cv-alert-dismiss`; only the attribute changed vs baseline (`git diff --stat 1b77934 HEAD` = 1 line) |
| `src/crud_views/static/crud_views/js/adapters.js` | Factory `alert.close` with component-local fallback | ✓ VERIFIED | l.41-49; wired via `cv.adapters` merge l.52; consumed by viewset.js:54 and both test suites |
| `src/crud_views/static/crud_views/js/viewset.js` | Delegated semantic alert dispatch | ✓ VERIFIED | l.46-55; listener registered on `document`; rendered by `{% cv_js %}` after adapters.js (settings.py:288-289) |
| `tests/js/viewset.test.js` | Golden-to-handler-to-default-adapter tracer + delegated ownership | ✓ VERIFIED | `DISMISSIBLE_ALERT_HTML` l.11; "rendered alert dismissal tracer" l.102 (2 cases); "delegated alert ownership" l.159 (16 cases); all run and pass |
| `tests/js/adapters.test.js` | Namespace/preassignment/absence/error/repeat matrix | ✓ VERIFIED | `fakeNamespace` with `Alert` l.14; `namespaceWithoutAlert` l.19; "alert adapter ownership" l.167 (16 cases); all run and pass |
| `docs/reference/javascript.md` | Four-adapter and alert ownership contract | ✓ VERIFIED | See P3-2 |
| `docs/reference/messages.md` | New dismiss markup and core-script requirement | ✓ VERIFIED | l.27-44 |
| `docs/reference/theme.md` | Custom alert frame recipe and exact dropdown boundary | ✓ VERIFIED | "### Custom alert frame" l.195; dropdown boundary l.201-214 (see WR-01) |
| `docs/reference/settings.md` | Delegated alert hook, link to JS contract | ✓ VERIFIED | l.184, l.189 |
| `docs/migrating-1.0.md` | Compact before/after and legacy-template guidance | ✓ VERIFIED | l.364-385 and lists at 175-177, 205-206, 314-329, 417-434 |
| `CHANGELOG.md` | Unreleased Breaking entry + four-adapter Added enumeration | ✓ VERIFIED | l.22-33 under `## Unreleased / ### Breaking`; l.306 Added |
| `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md` | Browser, history and gate evidence | ✓ VERIFIED | Present, 168 lines, records drift and the non-green `ruff format --check` honestly; browser §6 is executor-automated (human item) |

### Key Link Verification

`gsd query verify.key-links` exit 0 for all three plans (4/4, 2/2, 3/3).

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/test1/test_alerts.py` | golden `dismissible.html` | `read_bytes` exact comparison | WIRED | test_alerts.py:176-181 |
| `tests/js/viewset.test.js` | golden `dismissible.html` | `readFileSync` into jsdom, click rendered control | WIRED | viewset.test.js:11-13, 113 |
| `tags/alert.html` | `viewset.js` | `data-cv-alert-dismiss` marker + closest role frame | WIRED | alert.html:5 ↔ viewset.js:49-51 |
| `viewset.js` | `adapters.js` | `globalThis.cv.adapters.alert.close` at click time | WIRED | viewset.js:54 ↔ adapters.js:41-49,52 |
| `adapters.js` | `tests/js/adapters.test.js` | real `bootstrapAdapters` with fake namespaces | WIRED | adapters.test.js:167-380 |
| `viewset.js` | `tests/js/viewset.test.js` | real listener + `listenerErrors` observer | WIRED | viewset.test.js:159-478 |
| `tests/test1/test_alerts.py` | `docs/reference/theme.md` | `_section` + `TEMPLATE_FENCE` extraction, `_theme_templates` render | WIRED | test_alerts.py:249-283 |
| `docs/migrating-1.0.md` | `docs/reference/javascript.md` | relative links `reference/javascript.md#dismissible-alerts` | WIRED | migrating-1.0.md:322,378; mkdocs --strict exit 0 |
| `docs/migrating-1.0.md` | `docs/reference/messages.md` | relative link | WIRED | migrating-1.0.md:378 |
| `{% cv_js %}` | `adapters.js` → `viewset.js` order | settings.py Box order | WIRED | settings.py:288-289; example base.html:37 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `tags/alert.html` | `alert.*` | `crud_views.lib.messages.alert_data()` via `cv_alert` / `cv_messages` (django.contrib.messages queue) | Yes — `test_create_message_renders_as_an_alert` drives a real POST → redirect → rendered flash | ✓ FLOWING |
| `viewset.js` listener | `frame` | DOM `closest()` from the real click target | Yes — tracer dispatches a bubbling MouseEvent on the golden's rendered control | ✓ FLOWING |
| `adapters.js` `alert.close` | `Alert` | `component(ns, "Alert")` resolved per call from `globalThis.bootstrap` | Yes — late/replaced global tests | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Golden equals real render; frame contract; allowlist guard; tmp_path negative; recipe render | `.venv/bin/pytest tests/test1/test_alerts.py::test_dismissible_alert_golden ::test_dismissible_alert_preserves_frame_contract ::test_stock_bootstrap_data_attributes_are_dropdown_only ::test_core_bootstrap_data_attribute_guard_rejects_forbidden_path ::test_documented_alert_frame_override -q` | 5 passed | ✓ PASS |
| Real create response and `cv_messages` render the new hook | `.venv/bin/pytest tests/test1/test_messages.py -q -k "create_message or renders_a_dismissible"` | 3 passed, 20 deselected | ✓ PASS |
| Present-Alert delegation / absent-Alert removal through the real listener on the real golden | `npx vitest run tests/js/viewset.test.js -t "rendered alert dismissal tracer"` | 2 passed | ✓ PASS |
| Post-load injected alert closes without init | `npx vitest run tests/js/viewset.test.js -t "inserted into modal-like content"` | 1 passed | ✓ PASS |
| Delegated ownership matrix (nearest frame, ignored targets, swap, errors, missing key, rapid/detached) | `npx vitest run tests/js/viewset.test.js -t "delegated alert ownership"` | 16 passed | ✓ PASS |
| Default adapter namespace/absence/error/repeat matrix | `npx vitest run tests/js/adapters.test.js -t "alert adapter ownership"` | 16 passed | ✓ PASS |
| Docs build with anchor validation | `.venv/bin/mkdocs build --strict -d <scratch>` | built, exit 0 | ✓ PASS |
| Core-template data-bs scan | `grep -rn 'data-bs-' src/crud_views/templates` | 3 lines, 2 files, both in theme.md's list | ✓ PASS |
| Real-browser Bootstrap transition in the example project | (requires runserver + browser) | not run here | ? SKIP → human |

### Probe Execution

Not applicable: no `scripts/*/tests/probe-*.sh` exist and no PLAN/SUMMARY declares a probe.

### Requirements Coverage

All four IDs REQUIREMENTS.md maps to Phase 4 (lines 121-124) are claimed by at least one plan's `requirements:` field. No orphaned requirements.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ALRT-01 | 04-01, 04-03 | Golden of today's dismissible alert committed before the change | ✓ SATISFIED | R1 |
| ALRT-02 | 04-01, 04-02, 04-03 | `tags/alert.html` renders `data-cv-alert-dismiss` instead of `data-bs-dismiss="alert"`; one delegated click handler calls `cv.adapters.alert.close(el)` | ✓ SATISFIED | R2, R3, P1-2, P1-5, P1-6, P2-5 |
| ALRT-03 | 04-01, 04-02, 04-03 | `cv.adapters.alert.close` uses Bootstrap's `Alert` when present, falls back to `el.remove()` inside the adapter; vitest covers both | ✓ SATISFIED | P1-3, P2-1..P2-7; adapters.js:44-48; 34 vitest cases |
| ALRT-04 | 04-03 | grep lists only the dropdown templates named in theme.md; docs (javascript.md, messages.md, theme.md), CHANGELOG Breaking and migration bullet updated | ✓ SATISFIED (with warning) | R3, R4 docs part, P3-1..P3-4; WR-01 wording over-claim in theme.md is a warning, not a requirement failure — the requirement's grep scope is `src/crud_views/templates` |

### Decision Coverage

`check.decision-coverage-verify`: All trackable CONTEXT.md decisions are honored by shipped artifacts (10/10, none not honored).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| tests/test1/test_alerts.py | ALRT-01/02/04 | 36 | 0 | No — golden provenance is the pre-change system (the intended legacy oracle for ALRT-01; chronology proven in git) | Value / Behavioral (lxml-parsed attributes, hostile input escaping, gettext sentinel) | OK |
| tests/test1/test_messages.py | ALRT-02 | 23 | 0 | No | Behavioral (real POST → redirect → parsed frame) | OK |
| tests/js/viewset.test.js | ALRT-02/03 | 25 | 0 | No | Behavioral (DOM attachment, call identity `toBe(frame)`, `defaultPrevented`, original error identity, console spies) | OK |
| tests/js/adapters.test.js | ALRT-03 | 34 | 0 | No | Behavioral (call counts/args, `isConnected`, sibling preservation, thrown identity) | OK |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0. **Insufficient assertions:** 0.

Disconfirmation pass: (1) partially met — ALRT-04's theme.md sentence over-claims (WR-01); (2) a passing test that does not prove the stated behavior — none found; the 04-02 fakes do not prove Bootstrap's real fade, which the plan itself says and routes to the browser smoke (human item); (3) error path without a test — `viewset.js` loaded without `adapters.js` (`globalThis.cv` undefined → TypeError on click, IN-03) has no test and is understated in messages.md:40-41.

### Anti-Patterns Found

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers in any file this phase modified (CHANGELOG hits at lines 98, 144, 504, 1073-1075, 1190, 1206 are historical release notes outside the Unreleased section the phase edited).

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `docs/reference/theme.md` | 212-214 | Over-claim: "the only stock templates with Bootstrap `data-bs-*` attributes" — `src/crud_views_object_detail/.../layouts/accordion/group.html:5,15` and `layouts/tabs-vertical/object_detail.html:10-11` also carry `data-bs-toggle/target/parent`; the guard test scans only `src/crud_views/templates` (WR-01) | ⚠️ Warning | A non-Bootstrap theme author trusting the sentence overrides the three dropdown templates and still gets non-functional accordion/tab ObjectDetailView layouts. Fix is one sentence (scope to `crud_views` core templates, name the two object-detail layouts) or an explicit Phase 7 deferral |
| `docs/reference/messages.md` | 40-41 | "only the X does nothing" without core scripts — with `viewset.js` but no `adapters.js` the click throws `TypeError` (IN-03) | ℹ️ Info | Understatement; `{% cv_js %}` users are unaffected |
| `src/crud_views/static/crud_views/js/viewset.js` | 51 | `[role="alert"]` exact match ignores token lists like `role="alert status"` (IN-01) | ℹ️ Info | Docs consistently say `role="alert"`; robustness nit |
| `tests/test1/test_alerts.py` | 24-30 | `BOOTSTRAP_DATA_ALLOWED` hand-copied from theme.md rather than derived (IN-02) | ℹ️ Info | Silent drift possible if the doc list changes |

### Human Verification Required

### 1. Example-project browser dismissal (A/B/C)

**Test:** Start `examples/bootstrap5` (`.venv/bin/python examples/bootstrap5/manage.py runserver 127.0.0.1:8000`), log in at `/login/` as `alice`/`alice`, submit the Author update form three times (each redirects to `/library/author/` with one flash message). A: click the X with the stock adapter and real `bootstrap.Alert`. B: in the console run `const saved = cv.adapters.alert; cv.adapters.alert = cv.bootstrapAdapters({}).alert;`, click the X, then `cv.adapters.alert = saved`. C: on a fresh page, clone the attached frame into a newly appended `div`, click the clone's X.
**Expected:** A: frame fades and is removed (no console errors besides `/favicon.ico` 404). B: frame removed synchronously; `cv.adapters.modal/tooltip/collapse` unchanged. C: clone removed via the Bootstrap transition; original frame and host div still attached.
**Why human:** Real Bootstrap transition from the CDN bundle; the repo's jsdom tests use fake `Alert` components, and the executor's headless-Chrome evidence (04-ACCEPTANCE.md §6) came from an uncommitted scratch script.

### 2. Maintainer reading of the upgrade prose (deferred 04-03-02 human-check) and WR-01/IN-03 decision

**Test:** Read `docs/migrating-1.0.md` lines ~319-329 and ~364-385 beside `docs/reference/javascript.md` lines ~55-70 and 188-215, and `CHANGELOG.md` lines 22-33 and 306. Then read `docs/reference/theme.md` lines 212-214 against `grep -rn 'data-bs-' src/` (object-detail accordion and tabs-vertical layouts) and `docs/reference/messages.md` lines 40-41.
**Expected:** Both texts distinguish pre-load default filling from post-load whole-map replacement, require `alert.close(el)` in a later replacement, show `cv.bootstrapAdapters(ns).alert`, and all three name four adapters. For WR-01, either apply the one-sentence scope fix from 04-REVIEW.md or record the Phase 7 deferral explicitly in 04-REVIEW-DISPOSITION.md (currently `open`).
**Why human:** Semantic accuracy is a judgment call; `mkdocs --strict` validates anchors only, and the executor's own §7 review is not a maintainer review.

### Gaps Summary

No gaps. Every artifact exists, is substantive and is wired; the baseline chronology, the single-attribute golden diff, the core-template `data-bs-*` boundary and the four-adapter documentation set all hold against the actual tree, and every behavior-dependent truth (present/absent `Alert`, post-load insertion, ownership, idempotency, rapid clicks) has a named passing test run here. Status is `human_needed` solely because (a) the example project's real-browser dismissal is runtime behavior the repository's tests cannot exercise and the executor's headless run is not reproducible from committed files, and (b) the planner deferred the migration/reference prose review to end-of-phase, and that review should also settle the theme.md over-claim (WR-01) that the code review left `open`.

---

_Verified: 2026-10-26T20:55:52Z_
_Verifier: Claude (gsd-verifier)_
