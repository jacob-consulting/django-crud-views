---
phase: "04"
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T19:30:00.562150+00:00
plans_reviewed: [04-01-PLAN.md, 04-02-PLAN.md, 04-03-PLAN.md]
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
  deepseek-review: "openrouter/deepseek/deepseek-v3.2 (reasoning=high)"
model_sources:
  fable-review: "pinned"
  grok-review: "pinned"
  gemini-review: "pinned"
  deepseek-review: "pinned"
---

# Cross-AI Plan Review — Phase 04

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts
<!-- gsd:plan-revision-conflicts:end -->

> Note: grok-review, gemini-review and deepseek-review share the opencode adapter; their consensus is cross-model, not cross-tool.

Cycle 2 reviewed revised plans at `6b0dcec`. All four configured instances returned real source-cited reviews and covered all three plans; no trimming was configured. Raw reports are preserved mechanically in [.review-diagnostics/20261026T193000Z-gsd-review-rwrnvte2](.review-diagnostics/20261026T193000Z-gsd-review-rwrnvte2/). No product or plan files were edited by this review. Parent orchestrator owns the review commit.

## Claude Review (fable-review)

All source checks are done. Here is the cycle-2 review, verified against the files on disk at `6b0dcec`.

# Cross-AI Plan Review, Phase 04, cycle 2

**Verification basis.** Read on disk: `adapters.js`, `viewset.js`, `tags/alert.html`, `lib/messages.py`, `templatetags/crud_views.py:391-409`, `lib/settings.py:288-294`, both JS suites and all four helpers, `test_alerts.py`, `test_messages.py`, `test_form_frame.py`, `test_label_mode_docs.py`, `javascript.md`, `messages.md`, `theme.md`, `settings.md`, `migrating-1.0.md`, CHANGELOG head, `.pre-commit-config.yaml`, `tests/test1/conftest.py`, the German catalog, Django 5.2's `translation/__init__.py` and `templatetags/i18n.py`, the example base template, `test_docs_sync.py`, the full cycle-1 review and the three ledgers. I ran a `data-bs-` grep over `src/`. I did not run pytest, vitest or mkdocs. Branch preservation is settled and not revisited.

**Prior findings status.** H1 and A1, A3 through A10 are addressed in the plan text and are verifiable against source. A2 is explicitly rejected per the settled branch decision. Details per plan below.

## 04-01

**Summary.** The plan now matches source at every seam it names. The baseline task is byte-exact and safe to commit, the tracer commit is green because both legacy assertions move into it, and the JS isolation recipe is correct for how `loadScript` evaluates shipped code. No open concern from cycle 1 remains in this plan. Two small execution details are worth tightening.

**Strengths**
- **A1 closed.** `tests/test1/test_messages.py:139` and `:169` are the only two `data-bs-dismiss` assertions in the file, and the task's `<files>` list and acceptance criteria now include both. The combined verify command runs both suites before the commit.
- **Byte-exact golden is safe here.** `.pre-commit-config.yaml` has only `ruff-check` and `ruff-format`, and `.git/hooks` holds no installed hooks, so nothing appends or strips a trailing newline after capture. `cv_alert` renders via `template.template.render(context)` (`templatetags/crud_views.py:407-409`), so the raw render includes the template's final newline and the `encode`/`read_bytes` contract is deterministic.
- **A3 closed and mechanically right.** `loadScript` binds `globalThis` to a Proxy whose reads and writes fall through to the jsdom `window` (`tests/js/helpers/load.js:25-36`). A listener that reads `globalThis.cv.adapters.alert.close` at call time therefore sees whatever `window.cv` is at click time, which is exactly what the per-case descriptor reset relies on. Deleting `window.cv` before reloading `adapters.js` is required because `adapters.js:43` merges with `cv.adapters || {}` and would otherwise keep a stale custom `alert`.
- **A10 closed on the real seam.** `{% translate 'Close' %}` with no context resolves through `translation.gettext` (`django/templatetags/i18n.py:177`), which is `_trans.gettext` (`django/utils/translation/__init__.py:85,95`). `Trans.__getattr__` stores the real callable on first access, so `monkeypatch.setattr(_trans, "gettext", …)` records and restores the correct original.
- **Locale is pinned correctly.** `tests/test1/conftest.py:98-100` sets `LANGUAGE_CODE="en-us"` and `USE_I18N=True`; the German catalog maps `Close` to `Schließen` (`locale/de/.../django.po:103-104`), so `translation.override("en")` is the right guard for the golden.
- **D-04 departs from the modal/collapse precedent on purpose.** `adapters.js:15` and `:33` throw `missing()`; the plan forbids copying that for `alert` and removes instead.

**Concerns**
- **LOW. The JS golden path is unstated.** The tracer reads the golden "using node:fs, node:path and fileURLToPath". From `tests/js/viewset.test.js` the relative path is `../test1/golden/alerts/dismissible.html`. Writing it once in the task avoids an executor guessing against `JS_DIR` in `load.js:8`, which points at `src/`, not `tests/`.
- **LOW. Regeneration method in the tracer is open.** Task 2 says "replace only the dismiss attribute in the shared frame and golden". Hand-editing the golden and rerunning with `CV_UPDATE_GOLDEN` both work. State one so the executor does not run the env var over the whole `test_alerts.py` module, which would be harmless today but sets a bad habit for the `form_frame` goldens the var also drives.

**Suggestions**
- Add the relative golden path to the 04-01-02 action text.
- Say "regenerate with `CV_UPDATE_GOLDEN=1 pytest … -k test_dismissible_alert_golden`, then `git diff` must show one attribute".

**Risk Assessment: LOW.** All cycle-1 process risks are resolved. What remains is wording precision.

## 04-02

**Summary.** The regression matrix is complete for D-03, D-04 and D-08, and it now uses the repo's own `listenerErrors` helper correctly. The error-observation recipe is sound for jsdom: the helper's `event.preventDefault()` on the window error event (`tests/js/helpers/errors.js:9`) stops jsdom from forwarding the uncaught listener error to the virtual console, so a passthrough `console.error` spy with zero calls is a meaningful "core logged nothing" assertion. No cycle-1 concern remains open.

**Strengths**
- **A4 closed.** `listenerErrors` exists at `errors.js:5-18`, captures `event.error ?? event.message`, and removes its listener in `finally`. The plan asserts identity for throws and an empty array for ignored targets, which is stronger than the `list.filter.test.js:198-213` precedent that leaks a mocked `console.error`.
- **A5 and A6 closed.** Two controls in one frame, nested-role inner removal with outer and sibling attachment asserted, and `delete cv.adapters.alert` producing a `TypeError` with no repair are all named explicitly.
- **Edge truths are DOM-accurate.** `Element.remove()` on a detached node is a no-op and an event dispatched inside a detached subtree never bubbles to `document`, so both EDGE-ALRT-03 predicates hold without product code.
- **Fixture extension is trivial.** `fakeNamespace()` at `adapters.test.js:4-14` is a plain object; `Alert` follows the `Collapse` entry on line 12.
- **Ordering respected.** New cases precede the reload test at `viewset.test.js:91-101`, which installs duplicate listeners.

**Concerns**
- **LOW. The "no-op present component" fake must leave the element attached deliberately.** A `close: vi.fn()` does that by default, so the test passes as written. The only trap is a fake that mirrors Bootstrap by removing the element, which would mask an accidental second removal in the adapter. The plan's phrase "a fake close that leaves the element attached" covers it; just keep that as the acceptance wording.
- **LOW. `console.warn` is already live.** `setup.js:11-12` mocks only `log` and `assert`, so both `error` and `warn` spies observe real calls. Nothing to change, but the ledger's "spies record calls even with mocked implementations" sentence should not be read as permission to add `mockImplementation`; a passthrough spy is cleaner and the plan already says to restore in `finally`.

**Suggestions**
- In 04-02-01's "changing callback namespace" case, additionally assert the adapter object identity is unchanged across the namespace swap. That is the exact D-08 claim and costs one line.
- Reuse the existing non-Element dispatch at `viewset.test.js:74-79` rather than duplicating it.

**Risk Assessment: LOW.** Pure test expansion over a contract 04-01 delivers, with bounded product edits only on a red case.

## 04-03

**Summary.** H1 is fixed as specified: the guard scans exactly `src/crud_views/templates`, requires a nonempty subset of the three allowed paths, does not require the wrapper to match, and establishes red direction from the baseline commit's template in a temporary tree. The docs edit list now covers the stale sentences A7 identified. The recipe retains the colour seam and load tags (A8), and the migration text forbids dual hooks (A9). Three small gaps remain, none blocking.

**Strengths**
- **H1 verified against source.** Today's grep under `src/crud_views/templates` returns four lines in `actions_menu_toggle.html:4-5`, `language_selector.html:6` and `alert.html:5`. After the tracer, the only matches are the toggle and the language selector, both inside the allowlist from `theme.md:179-181`; `actions_menu.html` has no `data-bs-` attribute, so the subset contract is the only one that passes on day one. The extension-app hits in `crud_views_object_detail` (`accordion/group.html:5,15`, `tabs-vertical/object_detail.html:10-11`) are correctly excluded by the pinned root.
- **Red direction is executable in wave 3.** The 04-01-01 baseline commit predates the template edit, so `git show <baseline>:src/crud_views/templates/crud_views/tags/alert.html` yields the old attribute without touching the checkout.
- **A7 closed with exact targets.** `migrating-1.0.md:309-310` (three-adapter enumeration), `:374` (silent-breaks checklist naming modal, filter and tooltip), `:345-347` (the modal's `data-cv-modal-dismiss` precedent), and `settings.md:184-188` (delegated-hook list) are all named in the tasks and `settings.md` is now in `files_modified`.
- **A8 and A9 closed.** The recipe keeps `{% cv_button_class "alert" alert.level %}` and `{% load crud_views i18n %}`, which `test_alert_colours_follow_the_class_table` (`test_alerts.py:125-128`) proves is the live colour seam. The migration text now says a migrated control carries only the new hook.
- **Example wiring supports the smoke.** `base.html:19` loads Bootstrap 5.3.3 before `{% cv_js %}` at `:37`, and `lib/settings.py:288-289` orders `adapters.js` before `viewset.js`. `cv.bootstrapAdapters({}).alert` resolves `component({}, "Alert")` to `null` (`adapters.js:8`) and so exercises the removal branch in a real browser.

**Concerns**
- **LOW. `_section` works, `FENCE` does not.** `test_label_mode_docs.py:35-45` `_section(text, heading)` takes the full heading line including hashes, and the plan should say which level the new heading has. The `FENCE` regex on line 24 matches only ```` ```python ```` fences. The recipe is a Django fence, so the executor needs a separate ```` ```django ```` pattern. The plan's "fence-aware _section pattern" phrasing could be read as reusing `FENCE`.
- **LOW. Red direction is a one-time manual probe, not a lasting test.** Since the helper takes a root, a permanent red-direction case costs nothing: write one offending file under `tmp_path`, call the helper on it, assert it raises. That removes the Git dependency the plan is rightly avoiding and keeps the guard non-vacuous after the baseline commit is forgotten.
- **LOW. The object-detail Bootstrap leak is deferred but not written anywhere durable.** The ledger defers it to Phase 7, yet 04-03-03 only records "the generic downstream-theme follow-up". `ROADMAP.md:138-139` already anticipates a "known Bootstrap-DOM template" list in `theme.md` for Phase 7. One sentence in `04-ACCEPTANCE.md` naming the two extension templates is enough.
- **LOW. "Available browser automation" may not be available to the executor.** The `gsd-executor` agent's tool list has no Playwright MCP. The plan's explicit "record the blocker and leave unverified" branch handles this correctly, so this is a note for the orchestrator, not a plan defect.

**Suggestions**
- In 04-03-01, write the heading verbatim (for example `### Custom alert frame`) and add a `DJANGO_FENCE` regex next to the imported `_section`.
- Add a `tmp_path` red-direction case to `test_stock_bootstrap_data_attributes_are_dropdown_only` and keep the historical `git show` probe as recorded evidence only.
- Add the object-detail templates to the 04-ACCEPTANCE.md "follow-ups" list for Phase 7.
- In `javascript.md`, state the asymmetry with `modal.show` (`javascript.md:40` says a failing `modal.show` is logged). Alert failures are deliberately not logged under D-03, and readers will otherwise expect symmetry.

**Risk Assessment: LOW.** The guard specification is now precise enough that a faithful executor cannot produce a vacuous or wrongly-failing test. Remaining items are polish.

## Cross-plan assessment

**Dependency ordering** is correct and unchanged: baseline commit, tracer, regressions, docs and gates. The tracer's six-file scope is justified because it is the only way to keep `pytest tests` green at every commit.

**Scope** stays tight. No class-table keys, lifecycle events, timers, observers or second removal paths. D-04's supersession of the source plan's handler-removal sentence is applied consistently in all three plans.

**Security** posture is adequate. Escaping lives in `lib/messages.py:42-53` and is untouched; the recipe test renders hostile content through the real override path; the handler uses fixed semantic selectors.

**Goal achievement.** With the plans as committed, ALRT-01 through ALRT-04 and D-01 through D-10 are achievable. The two items outside the plans' control are real-browser Bootstrap transition evidence and the Phase 7 record of the extension-app Bootstrap hooks.

**Overall risk: LOW.** Every cycle-1 HIGH and MEDIUM is either incorporated with source-verifiable mechanics or explicitly rejected on settled grounds. Nothing I found requires another revision cycle before execution.

`CYCLE_SUMMARY: current_high=0 current_actionable=0` (the LOW items above are suggestions, not blockers)


---

## OpenCode Review (grok-review)

I'll verify the revised plans against the source and the prior review, then report only remaining issues.
Prior review items are mapped. Next I’ll check the cited tests, docs, and script loader against the revised plans.
## 04-01

Prior H1 does not apply here. A1, A3, and A10 are closed in this plan.

A1 is closed: the only `data-bs-dismiss="alert"` assertions are `tests/test1/test_messages.py:139` and `:169`, and 04-01-02 updates both before the combined pytest commit. A3 is closed: call-time `globalThis.cv` matches the Proxy in `tests/js/helpers/load.js:32-36`, and `loadScript` re-evaluates, so deleting `window.cv` and reloading adapters yields fresh defaults. A10 is closed: `{% translate %}` resolves through `gettext_lazy` to `_trans.gettext` (`django/utils/translation/__init__.py:95-111`). A live render with that patch produced `aria-label="CLOSE-SENTINEL"`.

The plan is execution-ready. The baseline commit, the shared-frame swap, and the real golden-to-listener tracer match the current template and test seams.

**Strengths**
- `tags/alert.html:5` is the only stock `data-bs-dismiss`. `tags/messages.html:1` includes that frame, so one attribute change covers flash messages.
- The golden is raw `cv_alert` output. A fixed `en` render is deterministic, including the leading and trailing newlines. Byte comparison without `_norm` will show only the attribute swap.
- The tracer reads that golden and drives the real listener. `viewset.js:91-101` stays last, so new clicks do not double-register.

**Concerns**
- LOW: a must-have says post-load alerts close, but 04-01-02 only clicks the golden. Dynamic insertion is not in this plan's verify commands. The document listener will do it; evidence waits for 04-02-02.

**Suggestions**
- When asserting the absent-Alert sibling, add a sibling node beside the inserted golden. The golden itself is a single frame.

**Risk Assessment**
LOW. The public hook and default adapter are specified against the real factory (`adapters.js:7-8,43`) and the existing Element/`closest`/`preventDefault` pattern (`viewset.js:37-44`).

## 04-02

A3, A4, A5, and A6 are closed. `listenerErrors` (`tests/js/helpers/errors.js:5-18`) sees listener exceptions; with `preventDefault`, this vitest/jsdom run does not also call `console.error`. A detached click does not reach `document`, so the detached-subtree case is valid here. Two controls and the missing `alert` key are explicit.

The matrix matches the locked ownership rules and the existing factory. No new lifecycle API is introduced.

**Strengths**
- Absence is `component(ns, "Alert")` returning null (`adapters.js:8`), including a namespace that has Modal/Tooltip/Collapse and no Alert. Present no-op or throw must not call `el.remove()`.
- Preassignment is the existing shallow merge (`adapters.js:43`). The late-global pattern is already in `tests/js/adapters.test.js:125-139`.
- Nested `role="alert"` selection is `closest` from the control, not Bootstrap's `.alert` class. That is what a custom frame without `alert` classes needs.

**Concerns**
- LOW: 04-02-02 deletes `cv.adapters.alert` and only restores `window.cv` / `bootstrap` descriptors. `viewset.test.js:27-33` loads the listener once and only clears `innerHTML`, so an in-place delete survives a descriptor restore and can poison the next case in the same file.

**Suggestions**
- Restore the deleted `alert` key in `finally`, or delete `window.cv` and reload adapters the way 04-01 does.
- Click the alert body, not only an outside node, for the missing-marker case. That rejects a handler that closes any `role="alert"` click.

**Risk Assessment**
LOW. These are test-isolation details. The product rules (no handler fallback, no catch/log, fallback only when Alert is absent) are unambiguous and testable.

## 04-03

H1, A7, A8, and A9 are closed against current docs and templates.

H1: `theme.md:179-181` names `tags/actions_menu.html`, `tags/actions_menu_toggle.html`, and `snippets/language_selector.html`. Under `src/crud_views/templates`, `data-bs-` is only `alert.html:5`, `actions_menu_toggle.html:4-5`, and `language_selector.html:6`. `actions_menu.html` is a wrapper with no `data-bs-` attribute. A nonempty subset of those three paths, plus a temp-tree red using the baseline `alert.html`, matches ALRT-04. Object-detail `data-bs-` hits are outside that root; leaving them out is correct.

A7: `settings.md:184-189`, `migrating-1.0.md:309-310`, and `:374-375` are the stale sentences, and both tasks name them. A8: the recipe keeps `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}`, and `_section` in `tests/test1/test_label_mode_docs.py:35-45` can extract one heading. A9: the migration says replace the old attribute, do not keep both.

Docs, the allowlist, and the paired Breaking/migration change match the files they cite. The browser gate is not inferred from unit tests.

**Strengths**
- The recipe is rendered through `_theme_templates` and `cv_alert`, so a copied frame is executed, not string-matched. `alert_data()` still escapes heading, text, items, and `extra_tags` (`src/crud_views/lib/messages.py:35-53`).
- `javascript.md:179` ("All three are bubbling CustomEvents") stays distinct from the factory count at `javascript.md:57`. `settings.py:288-289` already emits `adapters.js` then `viewset.js`.
- 04-03-03 records tool drift and refuses to treat `manage.py check` or jsdom as Bootstrap transition proof.

**Concerns**
- None that reopen H1 or A7-A9.

**Suggestions**
- In the use-time cell, say dismiss clicks need `cv.adapters.alert`. Cancel and submit-form still need nothing (`viewset.js:15-44`).
- The smoke should seed and log in as `alice` / `alice` (`examples/bootstrap5/project/management/commands/seed.py:14`). The blocker clause already prevents a false pass.

**Risk Assessment**
LOW. The audit root, allowlist, and historical red specimen match the tree that exists today.

## Cross-plan

H1 and A1-A10 are addressed. A2 stays rejected; no branch switch. Dependency order is sound: baseline commit, then the green tracer (template, adapter, listener, both message assertions), then ownership tests, then docs. `04-03` does not audit the pre-change template in the lasting test; the red specimen is the baseline file in a temp tree.

No phase goal is uncovered. Stock dismissal is one attribute, one document listener, and `alert.close` inside the factory. Dynamic content, custom errors, and the no-Bootstrap fallback are specified where they can be proven. Overall risk is LOW.


---

## OpenCode Review (gemini-review)

## 04-01

### 1. Summary
Plan `04-01` sequences the baseline golden commit (`ALRT-01`), the end-to-end dismissal tracer across the template, adapter factory, and delegated listener (`ALRT-02`, `ALRT-03`), and the server-side alert/message rendering regressions across three well-isolated tasks. All Cycle 1 concerns for `04-01` (`A1`, `A2`, `A3`, `A10`, and the byte-exact newline convention) are fully resolved in the revised plan at `6b0dcec`: Task `04-01-02` updates both `tests/test1/test_messages.py` assertions (`lines 139, 169`) in the same commit as `src/crud_views/templates/crud_views/tags/alert.html:5` so the tracer commit stays green, uses `globalThis.cv.adapters.alert.close(frame)` at call time with scoped descriptor save/restore of `window.cv` and `window.bootstrap`, and Task `04-01-03` patches `django.utils.translation._trans.gettext` via `monkeypatch.context()` for the `{% translate 'Close' %}` render-time sentinel test.

### 2. Strengths
- **Byte-exact baseline golden before product edits (`src/crud_views/templates/crud_views/tags/alert.html:1-6`, `tests/test1/test_alerts.py:70-71`):** Task `04-01-01` writes `markup.encode("utf-8")` without appending a newline and compares via `read_bytes()` under a fixed English locale (`translation.override("en")`), avoiding the whitespace normalization in `tests/test1/test_form_frame.py:44-55` (`_norm()`) and ensuring `ALRT-01` (`D-07`) is recorded as a standalone commit before `alert.html:5` is touched.
- **Green tracer commit covering both `test_alerts.py` and `test_messages.py` (`tests/test1/test_messages.py:139,169`) [addresses A1]:** Moving the two legacy `assert 'data-bs-dismiss="alert"' in html` updates (`test_cv_messages_renders_a_dismissible_alert` at `tests/test1/test_messages.py:139` and `test_create_message_renders_as_an_alert` at `tests/test1/test_messages.py:169`) into Task `04-01-02` and running `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` before committing prevents an intermediate broken test suite.
- **Scoped JS state isolation and call-time `globalThis.cv` lookup (`src/crud_views/static/crud_views/js/adapters.js:43`, `tests/js/helpers/setup.js:7-8`, `tests/js/viewset.test.js:27-33,91-101`) [addresses A3]:** Snapshotting and clearing only `window.cv` and `window.bootstrap` descriptors before loading fresh defaults in `tests/js/viewset.test.js` ensures `adapters.js:43` (`Object.assign(cv.bootstrapAdapters(...), cv.adapters || {})`) does not carry over a prior test's adapter, while preserving the module-once `$` / `jQuery` globals installed in `tests/js/helpers/setup.js:7-8`. Placing the new cases before the reload test at `tests/js/viewset.test.js:91-101` avoids duplicate document listeners.
- **Verified Django template translation seam (`src/crud_views/templates/crud_views/tags/alert.html:5`, `.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:85,95-96`) [addresses A10]:** `{% translate 'Close' %}` resolves through `django.utils.translation.gettext`, which delegates directly to `_trans.gettext(message)`. Patching `django.utils.translation._trans.gettext` inside `monkeypatch.context()` intercepts only `"Close"` at template render time and cleanly restores state on exit.

### 3. Concerns
- None. All Cycle 1 concerns for `04-01` (`A1`, `A2`, `A3`, `A10`) have been resolved in the plan text and verified against the codebase.

### 4. Suggestions
- None; the task specifications and verification gates are ready for execution as written.

### 5. Risk Assessment
**Risk Level: LOW**
The baseline commit ordering, single-source golden fixture shared between pytest and Vitest, green tracer commit boundary, and scoped global cleanup eliminate the execution risks identified in Cycle 1.

---

## 04-02

### 1. Summary
Plan `04-02` expands the JavaScript unit and DOM regression suites in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` to cover lazy namespace resolution, preassigned and post-load custom adapter swaps, dynamic and modal-injected alerts, multiple dismiss controls, nested semantic alert frames, missing adapter keys, and custom/component error surfacing (`ALRT-02`, `ALRT-03`, `D-03`, `D-04`, `D-08`, `D-10`). All Cycle 1 concerns (`A3`, `A4`, `A5`, `A6`) are resolved: the plan reuses `listenerErrors` from `tests/js/helpers/errors.js:5-18`, restores `console.error` / `console.warn` spies in `finally`, tests two controls in one frame and outer/sibling frame survival on nested dismissal, and covers deleting `cv.adapters.alert`.

### 2. Strengths
- **Reuse of `listenerErrors` and clean console spy lifecycle (`tests/js/helpers/errors.js:5-18`, `tests/js/helpers/setup.js:11-12`) [addresses A4]:** Task `04-02-02` imports `listenerErrors(fn)` from `tests/js/helpers/errors.js:5-18`—which attaches a temporary `window` `"error"` listener, calls `event.preventDefault()`, and removes the listener in `finally`—both for expected throws and for ignored-target dispatches, while restoring `console.error` and `console.warn` spies in `finally` so mocks never leak across tests.
- **Strict absent-only fallback and error ownership (`src/crud_views/static/crud_views/js/adapters.js:7-8,12-43`) [addresses A6]:** Tasks `04-02-01` and `04-02-02` verify that `el.remove()` runs only inside the default adapter when `component(ns, "Alert")` is absent (including when `Modal`/`Tooltip`/`Collapse` are present on `ns`), while present no-op `Alert`, throwing `getOrCreateInstance` / `close`, throwing custom adapters, and a deleted `cv.adapters.alert` key (`TypeError`) leave the DOM untouched and surface the original exception without core logging or fallback removal.
- **Multi-control, nested-role, and dynamic DOM coverage (`src/crud_views/static/crud_views/js/viewset.js:37-44`, `tests/js/viewset.test.js:59-79`) [addresses A5]:** Task `04-02-02` tests two `[data-cv-alert-dismiss]` controls inside the same `[role="alert"]` frame, nested `[role="alert"]` frames where dismissing the inner alert leaves the outer alert and siblings connected (`isConnected`), and post-load modal-injected alerts without Bootstrap CSS classes.
- **Explicit idempotency and rapid-click verification (`EDGE-ALRT-03-idempotency`, `EDGE-ALRT-03-concurrency`):** Both spec-less edge predicates are tested directly against standard DOM detachment and event bubbling semantics without adding production state or timers.

### 3. Concerns
- None. All Cycle 1 concerns for `04-02` (`A3`, `A4`, `A5`, `A6`) have been resolved.

### 4. Suggestions
- None; the regression matrix is complete and ready for execution.

### 5. Risk Assessment
**Risk Level: LOW**
The plan is confined to well-isolated unit and DOM tests in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` (with bounded fixes to `adapters.js` / `viewset.js` only if a test exposes a defect) and follows established repository helpers.

---

## 04-03

### 1. Summary
Plan `04-03` updates the four reference documents (`javascript.md`, `messages.md`, `theme.md`, `settings.md`), adds executable tests in `tests/test1/test_alerts.py` for the documented custom alert frame override recipe and the core `data-bs-*` template allowlist guard, pairs the `CHANGELOG.md` `### Breaking` entry with the `docs/migrating-1.0.md` before/after guide and checklist updates, and runs the full project quality gates and example browser acceptance check (`ALRT-01` through `ALRT-04`, `D-01` through `D-10`). All Cycle 1 concerns (`H1`, `A7`, `A8`, `A9`) are thoroughly addressed in the revised plan.

### 2. Strengths
- **Exact core scan root, subset assertion, and non-mutating historical red check (`tests/test1/test_alerts.py:130-143`, `docs/reference/theme.md:179-181`, `src/crud_views/templates/crud_views/tags/actions_menu.html:1-9`) [addresses H1]:** Task `04-03-01` scopes `_assert_core_bootstrap_data_attributes(root)` strictly to `src/crud_views/templates` (avoiding `tests/test1/test_alerts.py:133`'s `crud_views*/templates` glob that hits `src/crud_views_object_detail/templates/`), asserts `matches` is nonempty and `matches <= ALLOWED` (so `crud_views/tags/actions_menu.html:1-9` having no `data-bs-*` attribute does not cause a false failure), and verifies the failure direction by copying `src/crud_views/templates` to a temporary directory and writing the baseline commit's `alert.html` via `git show` without altering the checkout.
- **Executable custom alert frame recipe preserving the colour seam (`docs/reference/theme.md:156-170`, `tests/test1/test_alerts.py:110-128`, `tests/test1/test_label_mode_docs.py:29-45`) [addresses A8]:** Task `04-03-01` includes `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}` in the `Custom alert frame` recipe in `docs/reference/theme.md`, extracts the fenced code block using the fence-aware `_section` pattern from `tests/test1/test_label_mode_docs.py:29-45`, and renders it through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`) with an overridden `alert:*` colour key, dismissible/non-dismissible states, and hostile `extra_tags`/content.
- **Complete alignment of `settings.md` and `migrating-1.0.md` checklists (`docs/reference/settings.md:184-189`, `docs/migrating-1.0.md:199-200,306,309-310,345-347,374-375,385-410`) [addresses A7, A9]:** Task `04-03-01` adds `[data-cv-alert-dismiss]` and alert dismissal in `viewset.js` to `docs/reference/settings.md:184-189`. Task `04-03-02` updates the existing JavaScript adapter list at `docs/migrating-1.0.md:309-310`, the missing-`adapters.js` silent-break item at `docs/migrating-1.0.md:374-375`, and the alert/markup/override items, while explicitly instructing users to replace `data-bs-dismiss="alert"` with `data-cv-alert-dismiss` rather than keeping both attributes on the same control.
- **Auditable quality gates and honest browser smoke verification (`examples/bootstrap5/project/templates/project/base.html:19-38`, `.planning/phases/04-alert-dismiss-adapter/04-VALIDATION.md:88-110`):** Task `04-03-03` runs all automated gates (`pytest`, `npm test`, `mkdocs build --strict`, `ruff check`, `ruff format --check`, `examples/bootstrap5/manage.py check`, `test_docs_sync.py`), discloses tool-version drift without modifying manifests, and requires real browser observations (or an explicit recorded blocker) for the example flash-message transition check.

### 3. Concerns
- None. Prior `H1` and `A7`–`A9` are completely resolved.

### 4. Suggestions
- None; all tasks and verification steps are well-specified and grounded in the source tree.

### 5. Risk Assessment
**Risk Level: LOW**
With the core template scan root and subset contract pinned (`H1`), the colour accessor preserved in the tested recipe (`A8`), and all cross-document adapter/hook lists included (`A7`, `A9`), `04-03` is low-risk and ready to execute.

---

## Cross-Plan Summary & Convergence Verification

| Cycle 1 Item | Status in `6b0dcec` | Verification |
|---|---|---|
| **H1** (HIGH — audit scan root, subset check, temp-tree red check) | **Resolved** | `04-03-PLAN.md:88-90,126-139` pins `src/crud_views/templates`, `nonempty and matches <= ALLOWED`, and temporary-tree `git show` red verification. |
| **A1** (MEDIUM — green tracer commit) | **Resolved** | `04-01-PLAN.md:14,159,189-198` updates `tests/test1/test_messages.py:139,169` in `04-01-02` and runs both Python suites before commit. |
| **A2** (MEDIUM — explicit branch disposition) | **Resolved** | `04-01-PLAN.md:115-117,272` records preserving `introduce-gsd` under orchestrator branch management. |
| **A3** (MEDIUM — scoped JS globals & `globalThis.cv` lookup) | **Resolved** | `04-01-PLAN.md:169-174,184` and `04-02-PLAN.md:118-119,150-163` snapshot/restore only `cv`/`bootstrap` and call `globalThis.cv.adapters.alert.close(frame)`. |
| **A4** (MEDIUM — reuse `listenerErrors` & restore console spies) | **Resolved** | `04-02-PLAN.md:78,83,151-156` reuses `tests/js/helpers/errors.js:5-18` and restores `console.error`/`warn` spies in `finally`. |
| **A5** (MEDIUM — two controls in one frame & nested outer survival) | **Resolved** | `04-02-PLAN.md:138,146-149,169` tests two controls per frame and verifies outer/sibling frames remain connected. |
| **A6** (LOW — missing `cv.adapters.alert` key) | **Resolved** | `04-02-PLAN.md:140,156-159,170` deletes `cv.adapters.alert` and asserts `TypeError` via `listenerErrors` with no removal or logging. |
| **A7** (MEDIUM — update `settings.md` & `migrating-1.0.md` lists) | **Resolved** | `04-03-PLAN.md:11,114-116,164-167` updates `settings.md:184-189` and `migrating-1.0.md:199-200,309-310,374-375`. |
| **A8** (LOW — preserve `cv_button_class` colour seam in recipe) | **Resolved** | `04-03-PLAN.md:119-125` retains `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}` and tests an overridden colour key. |
| **A9** (MEDIUM — warn against dual dismiss attributes) | **Resolved** | `04-03-PLAN.md:162-164` instructs replacing `data-bs-dismiss="alert"` completely so migrated controls carry only `data-cv-alert-dismiss`. |
| **A10** (LOW — patch `django.utils.translation._trans.gettext`) | **Resolved** | `04-01-PLAN.md:220-226` patches `_trans.gettext` in `monkeypatch.context()` for `"Close"` under `translation.override("en")`. |

**Overall Risk Assessment: LOW.** All prior HIGH and actionable concerns are resolved; no new blocking or actionable concerns remain. The plans are ready for execution.


---

## OpenCode Review (deepseek-review)

I'll review these three implementation plans for the alert dismiss adapter phase. Let me start by examining the actual codebase to verify claims and check for concerns.
Now let me check the test files mentioned in the plans:
Let me check the test messages file:
Now let me check the golden directory structure:
Let me check the JS test files:
Let me also check the documentation files:
Now let me check for existing data-bs- attributes in templates:
Perfect! Now I have a good understanding of the current state. Let me check the viewset test file:
Now I have enough context. Let me analyze each plan:

## 04-01

**Summary**: This plan establishes the baseline golden and implements the core dismiss adapter functionality. It correctly identifies the need for a baseline commit before any changes (D-07) and implements the required changes to templates, JavaScript adapters, and tests.

**Strengths**:
1. **src/crud_views/templates/crud_views/tags/alert.html:5** - Correctly targets the exact line needing change from `data-bs-dismiss="alert"` to `data-cv-alert-dismiss`
2. **src/crud_views/static/crud_views/js/adapters.js** - Plans to add `alert.close(el)` method following existing pattern with `component(ns, "Alert")` lookup
3. **src/crud_views/static/crud_views/js/viewset.js** - Adds new click handler following existing delegate pattern (lines 38-44 show similar pattern for cancel URLs)
4. **tests/test1/golden/** - Creates specific alert golden directory structure, consistent with existing golden patterns
5. **tests/test1/test_messages.py** - Updates message assertions to match new attribute

**Concerns**:
1. **HIGH**: Missing explicit test for `data-cv-alert-dismiss` attribute in non-dismissible alerts. Plan mentions updating dismiss-attribute assertions but doesn't specify testing that non-dismissible alerts should NOT have this attribute.
2. **MEDIUM**: The `cv.adapters.alert.close` implementation needs to handle the case where `el.remove()` is called on an already detached element (if rapid double-click). This could cause errors.
3. **MEDIUM**: No explicit test for Bootstrap's `getOrCreateInstance(el).close()` throwing exceptions and ensuring they propagate per D-03.

**Suggestions**:
1. Add explicit test in `test_alerts.py` verifying non-dismissible alerts don't have the close button at all.
2. Add guard in `alert.close(el)` to check `el.isConnected` before calling `el.remove()`.
3. Add test case for throwing `Alert.getOrCreateInstance` or `.close()` methods.

**Risk Assessment**: **MEDIUM** - Core functionality is well-scoped but missing edge case handling for error conditions and rapid interactions.

## 04-02

**Summary**: This plan expands test coverage for namespace resolution, dynamic content, and error handling. It builds on 04-01 with comprehensive testing.

**Strengths**:
1. **tests/js/adapters.test.js** - Extends existing `fakeNamespace()` pattern (lines 4-14) to include `Alert` component testing
2. **tests/js/viewset.test.js** - Adds dynamic content tests using existing `loadScript()` pattern
3. **tests/js/helpers/errors.js** - Reuses existing `listenerErrors()` helper for error handling tests
4. **src/crud_views/static/crud_views/js/adapters.js** - Tests namespace resolution with late assignment, consistent with existing adapter patterns

**Concerns**:
1. **MEDIUM**: The plan tests "two rapid clicks while the adapter leaves its frame attached" but doesn't address race condition where first click detaches frame and second click might target wrong element.
2. **MEDIUM**: Missing test for scenario where `cv.adapters.alert` key is deleted between click detection and adapter call.
3. **LOW**: No explicit test for `el.closest('[role="alert"]')` returning null when role attribute is missing or misspelled.

**Suggestions**:
1. Add test for `cv.adapters.alert` being deleted between marker detection and adapter call.
2. Test `el.closest('[role="alert"]')` with malformed/missing role attributes.
3. Consider adding microtask delay test for rapid successive clicks.

**Risk Assessment**: **MEDIUM** - Good test coverage but missing some edge cases around dynamic adapter state changes.

## 04-03

**Summary**: This plan handles documentation, migration guidance, and final validation. It correctly identifies all documentation files needing updates.

**Strengths**:
1. **docs/reference/javascript.md** - Updates adapter count from 3 to 4 and documents new `alert.close` method
2. **docs/reference/messages.md** - Updates flash message markup guidance
3. **docs/reference/theme.md** - Adds custom alert frame recipe with `{% cv_button_class "alert" alert.level %}` preserving color seam
4. **CHANGELOG.md** and **docs/migrating-1.0.md** - Paired updates as required by CLAUDE.md
5. **tests/test1/test_alerts.py** - Adds `_assert_core_bootstrap_data_attributes()` with explicit ALLOWED list

**Concerns**:
1. **HIGH**: The ALLOWED list `crud_views/tags/actions_menu.html` doesn't actually contain `data-bs-` attributes according to grep results. Only `actions_menu_toggle.html`, `language_selector.html`, and `alert.html` (being changed) contain them.
2. **MEDIUM**: The browser acceptance test depends on manual browser interaction which may not be automated or reproducible.
3. **MEDIUM**: No test for the migration guide's claim that "legacy copied templates still close via Bootstrap's own data API."

**Suggestions**:
1. Fix ALLOWED list to match actual grep results: `actions_menu_toggle.html`, `language_selector.html`
2. Add automated test that old `data-bs-dismiss="alert"` still works with Bootstrap when core scripts aren't loaded.
3. Consider adding screenshot-based golden test for browser acceptance.

**Risk Assessment**: **MEDIUM** - Documentation updates are thorough but contain inaccuracies in the data-bs- attribute audit.

## Overall Review

The three plans form a coherent progression from baseline → implementation → documentation. Key strengths:
1. Follows existing patterns in the codebase
2. Respects established conventions (golden tests, adapter factory, delegate handlers)
3. Comprehensive test coverage across Python and JavaScript
4. Proper documentation updates with paired CHANGELOG/migration updates

Main risks:
1. Missing edge cases in error handling and rapid interactions
2. Inaccurate data-bs- attribute audit in plan 04-03
3. Manual browser acceptance testing

The plans achieve the phase goals (ALRT-01 through ALRT-04) and respect all documented decisions (D-01 through D-10). With the suggested fixes, this should be a solid implementation plan.


---
## Consensus Summary

### Prior finding verification

Gemini and Fable explicitly sign off the first-cycle revisions against source. The current plans make H1 and A1–A10 visible to execution, including A2's explicit rejection of a branch switch. Prior raw findings remain in [.review-history/04-REVIEWS-cycle1.md](.review-history/04-REVIEWS-cycle1.md); their old counts are historical.

| Item | Verified current plan contract |
|---|---|
| H1 | 04-03:137–152 pins the core-template root, nonempty subset allowlist, wrapper exception and temporary-tree historical red proof without changing checkout. |
| A1 | 04-01:189–202 moves both message assertions into the tracer and runs the combined Python gate. |
| A2 | 04-01:115–120,295 preserves introduce-gsd and rejects the phase-branch switch. |
| A3 | 04-01:171–186 and 04-02:157–166 use fresh real defaults, scoped cv/bootstrap descriptor cleanup and globalThis.cv lookup at call time. |
| A4 | 04-02:153–164 reuses listenerErrors for throws and ignored targets; console spies are asserted and restored. |
| A5 | 04-02:150–154 explicitly tests two controls, inner-frame removal and outer/sibling survival. |
| A6 | 04-02:162–164 tests deleted alert key as surfaced TypeError with no fallback/logging/repair. |
| A7 | 04-03:120–121,182–184 adds settings hook prose and updates existing migration adapter/checklist statements. |
| A8 | 04-03:128–134 retains load tags and level-colour accessor and renders the recipe under an overridden colour key. |
| A9 | 04-03:180–183 requires replacement with only the new hook while preserving old-hook-only compatibility. |
| A10 | 04-01:223–227 names a locally restored Django _trans.gettext sentinel under English override; installed gettext delegates through that method. |

### Agreed Strengths

The shared rendered golden, baseline-only first commit, current-adapter semantic dispatch, absent-only default fallback, namespace/error/dynamic matrix and paired migration contract remain grounded in the existing source. No reviewer identified a need for new dependencies, class-table keys or alert lifecycle machinery.

### Current actionable findings

No unresolved HIGH remains. Three LOW improvements still need executable-plan incorporation or an explicit disposition:

| ID | Origin | Required PLAN.md change |
|---|---|---|
| C2-A1 | Fable / LOW | Add a lasting tmp_path negative case for _assert_core_bootstrap_data_attributes: place an offending data-bs attribute in a forbidden relative file, call the same helper and assert rejection naming that file. Keep the historical git-show probe as separate one-time evidence. The current plan explicitly keeps that red probe out of lasting tests. |
| C2-A2 | Grok / LOW | Make 04-02's fixture ownership explicit: clear/create a fresh cv object before mutating its adapter map, or separately restore the original alert key in finally. Restoring a window property descriptor that points to the same mutated object does not undo delete cv.adapters.alert. Reuse 04-01's fresh-default setup without erasing shared jQuery globals. |
| C2-A3 | Grok / LOW | Name an ignored click inside an alert body that has role=alert but no dismiss marker. Assert no adapter call, no error and unchanged frame. An outside-document-node click alone cannot detect a handler that incorrectly closes on every alert click. |

Fable's own report prints current_actionable=0 because it regards LOW suggestions as non-blocking. The outer convergence contract is stricter: a useful LOW that remains outside PLAN.md is actionable regardless of blocker status. C2-A1 is therefore counted; C2-A2/C2-A3 are distinct concrete test-specification improvements from Grok.

`CYCLE_SUMMARY: current_high=0 current_actionable=3`

All prior H1/A1–A10 are closed by source-verified executable changes or the explicit A2 branch rejection. The two new DeepSeek HIGH assertions are refuted below, so neither is an unresolved HIGH or a silently suppressed claim. All four reviews carry source citations; no leading evidence-quality discount marker applies. There are no open plan-revision conflicts.


### Verified dispositions of other current comments

- **DeepSeek HIGH: no non-dismissible absence test — refuted.** 04-01:216,228,234–235 explicitly requires no close control for non-dismissible output; 04-03:131–135,156–157 also renders the documented non-dismissible case. The current stock marker location is the conditional close control (`src/crud_views/templates/crud_views/tags/alert.html:5`); the phase changes that attribute only. This is an existence-class assertion contradicted by plan/source evidence, not an unresolved HIGH.
- **DeepSeek HIGH: allowed wrapper has no data attributes — refuted.** 04-03:140–143 explicitly says the match set is a subset and the wrapper need not match. Gemini and Fable independently verify that exact fix. A zero-hit allowed path is intentional, not an inaccurate requirement. Preserve the documented three-path allowlist.
- **DeepSeek detached removal/race suggestions — not actionable.** 04-02:26–27,103,115–116,139–144,162–167 already specifies repeated removal, present-component throws, missing roles/key and detached-subtree dispatch. The handler is synchronous: it introduces no microtask gap between marker detection and adapter lookup. A detached Element.remove is harmless; no isConnected guard, delay or new scheduling contract is warranted. Present Bootstrap transition handling remains the component's responsibility.
- **DeepSeek browser screenshots / legacy-bootstrap unit test — no missing implementation contract.** 04-03:225–257 requires actual browser observations or an explicit blocker with a reproducible procedure. Legacy old-hook-only behavior is expressly preserved at 04-03:178–183 and does not enter the new handler. Screenshot goldens and tests of third-party Bootstrap's unchanged data API are optional scope expansion, not a gap in this bounded alert change.
- **Fable golden path/regeneration details — implementation choices already bounded.** 04-01 declares the exact golden path and requires the real render's raw bytes, a scoped update convention, attribute-only replacement and a final byte comparison. The executor can resolve the named path and must not regenerate unrelated goldens. These comments do not expose a hidden acceptance requirement.
- **Fable identity/no-op/non-Element details — already incorporated.** 04-02:109–116 constructs the adapter before changing namespace and explicitly forbids recreation; 04-01:166 and 04-02:103,114 require a no-op present component to leave the frame attached. Ignored/non-Element error absence is explicit in 04-02:153–160. No new test-only lifecycle state is needed.
- **Fable fence comment — source clarification.** The reusable _section uses _headings and ANY_FENCE, which handles all fenced languages (`tests/test1/test_label_mode_docs.py:26–45`); only the separate FENCE constant at :24 is Python-specific. 04-03:131–135 asks to reuse the fence-aware _section pattern, not that Python-only constant. The same task authors both uniquely named heading and recipe extractor, so it must choose matching heading/fence syntax. No existing symbol or claimed mechanism is missing.
- **Object-detail surface note — explicitly deferred in the plan.** 04-03's Review Dispositions Ledger already records this as Phase 7 work. It is durable in committed PLAN.md and the prior review cites the two extension templates. The bounded core scan must not be widened. Adding another duplicate acceptance-note reminder is optional.
- **Logging asymmetry / browser tool availability — already represented.** 04-03:115–119 explains surfaced alert errors and no core logging; :225–257 distinguishes real browser proof from unit/system checks and records a blocker if the executor lacks access. A unit fake never proves Bootstrap transitions. No new catch, fallback or automatic verification claim is introduced.

## Verification coverage

The authority seam again returns **intel** despite the explicit grep preference; the generated API map remains empty. Primary index resolution is UNCHECKABLE, not MISSING. Direct rg/Read supplements file/declaration existence; no signature compatibility is certified by either index or grep. The installed Django gettext wrapper was additionally inspected and calls _trans.gettext(message), acknowledging that seam as dynamically resolved.

The updated [source-grounding.json](.review-diagnostics/20261026T193000Z-gsd-review-rwrnvte2/source-grounding.json) enumerates 86 path/symbol references, quotes every corresponding current plan line and records direct evidence, exclusions and limits. No local declaration was found missing. New files/helpers/public hooks declared in Artifacts this phase produces and future execution summaries are excluded from existing-source checks. External/browser/CLI declarations and all unsupported signatures remain UNCHECKABLE. Severity seams yield no block for VERIFIED and INFO/no block for UNCHECKABLE.

### Uncheckable and excluded references

| Reference | Verdict | Limit / exclusion |
|---|---|---|
| `.planning/phases/04-alert-dismiss-adapter/04-01-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-01-PLAN.md:299. |
| `.planning/phases/04-alert-dismiss-adapter/04-02-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-02-PLAN.md:239. |
| `.planning/phases/04-alert-dismiss-adapter/04-03-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-03-PLAN.md:314. |
| `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-03-PLAN.md:16. |
| `tests/test1/golden/alerts/dismissible.html` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-01-PLAN.md:9. |
| `cv.adapters.alert` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:25. |
| `alert.close(el)` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:98. |
| `data-cv-alert-dismiss` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:25. |
| `DISMISSIBLE_ALERT_HTML` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:48. |
| `test_dismissible_alert_golden` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:36. |
| `test_dismissible_alert_preserves_frame_contract` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:94. |
| `test_documented_alert_frame_override` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-03-PLAN.md:55. |
| `test_stock_bootstrap_data_attributes_are_dropdown_only` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-03-PLAN.md:94. |
| `rendered alert dismissal tracer` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-01-PLAN.md:97. |
| `alert adapter ownership` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-02-PLAN.md:78. |
| `delegated alert ownership` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. 04-02-PLAN.md:79. |
| `Element` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:183. |
| `Object.assign` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:105. |
| `closest` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:60. |
| `dispatchEvent` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-02-PLAN.md:164. |
| `getOrCreateInstance` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:166. |
| `isConnected` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-02-PLAN.md:109. |
| `read_bytes` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:53. |
| `--prefix` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:204. |
| `-q` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:153. |
| `-n auto` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:228. |
| `--strict` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:163. |
| `--check` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:236. |
| `alert_data` | UNCHECKABLE | External translated name; no declaration asserted 04-01-PLAN.md:229. |
| `crud_views/tags/alert.html` | UNCHECKABLE | Runtime/external citation fragment; no source absence claimed. 04-01-PLAN.md:10. |
| `_assert_core_bootstrap_data_attributes` | SKIPPED_NEW | Declared private test helper in 04-03 Artifacts section; created by planned task. 04-03-PLAN.md:94. |
| `monkeypatch.context` | UNCHECKABLE | External pytest API; use local installed API, no repo declaration/signature certified. 04-01-PLAN.md:223. |
| `django.utils.translation._trans.gettext` | UNCHECKABLE | Django dynamically resolves _trans.gettext through Trans.__getattr__; installed gettext wrapper reads it at call time. No static property declaration exists; explicitly acknowledged dynamically resolved seam. 04-01-PLAN.md:224. |
| `translation.override` | UNCHECKABLE | External Django context manager; existing repository use-sites, no repo-owned declaration/signature certified. 04-01-PLAN.md:225. |
| `git show` | UNCHECKABLE | Existing Git command reads a committed snapshot without changing checkout; no repo-owned declaration. 04-03-PLAN.md:146. |
| `ALLOWED` | SKIPPED_NEW | Declared helper-local set in 04-03 Artifacts section; new test-local name. 04-03-PLAN.md:95. |

### Cross-artifact fact drift

- Phase-status seam: **lag**, STATE Ready to plan versus ROADMAP Planned; a one-step nonterminal lag is not a finding.
- Roadmap success criteria versus must-have truths and task acceptance: consistent baseline chronology, component/fallback/dynamic paths, core-only audit, release/reference/migration updates and actual example evidence.
- Requirements: ALRT-01 through ALRT-04 match the roadmap and task/frontmatter assignments.
- Locked terminology: D-01 through D-10 remain consistent; no class-table expansion, forced recovery, focus/auto-dismiss or new lifecycle event is introduced.
- Future implementation, real browser transitions and manifest-version validation are not established by this plan review. Fable did not run suites; Gemini read source; Grok additionally reports a focused live translation sentinel probe. This cycle does not claim a full pytest/Vitest/docs run.
