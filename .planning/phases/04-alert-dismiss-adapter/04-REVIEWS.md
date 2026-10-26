---
phase: "04"
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T18:25:08.820269+00:00
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

Cycle 1 reviewed committed plans at `a5de03b`. All four configured instances returned real source-cited reviews and covered all three plans. No prompt trimming was configured. The initial sandbox launch hit process EPERM; the approved exact rerun completed every lane. Fable disclosed that it read source but did not rerun tests. No implementation was performed.

Evidence: [.review-diagnostics/20261026T182508Z-gsd-review-wro4ux2o](.review-diagnostics/20261026T182508Z-gsd-review-wro4ux2o/).

## Claude Review (fable-review)

I could not run the focused test suites in this session (the command needed approval), so the "50 Python / 25 JS passing" baseline is taken from the research note, not re-verified. Everything else below was checked against the files on disk.

# Cross-AI Plan Review: Phase 04 Alert dismiss adapter

**Verification basis.** Read: `adapters.js`, `viewset.js`, `tags/alert.html`, both JS suites and helpers, `test_alerts.py`, `test_messages.py`, `test_form_frame.py`, `test_label_mode_docs.py`, `lib/messages.py`, `lib/settings.py`, the five docs, CHANGELOG, `.pre-commit-config.yaml`, the example base template, the source plan 3A section, and a `data-bs-` grep over `src/`. Not run: pytest, vitest, mkdocs.

## 04-01

**Summary.** The plan matches the code it describes. The delegated-handler analog at `src/crud_views/static/crud_views/js/viewset.js:38-44`, the lazy `component()` seam at `adapters.js:7-8` and the preassignment merge at `adapters.js:43` are exactly as the plan states, and the single dismiss attribute to replace is `tags/alert.html:5`. The baseline-first ordering is sound and the byte-exact golden is safe to commit. Two ordering problems weaken it: the tracer commit leaves two existing assertions red, and no task puts the work on the phase branch.

**Strengths**
- **Byte-exact golden is safe in this repo.** `.pre-commit-config.yaml:1-6` runs only ruff hooks, so no end-of-file or whitespace fixer will rewrite an HTML golden after capture. There is no `tests/test1/golden/alerts/` today, so the new fixture cannot collide.
- **Tracer bridge is realistic.** Loading the golden into jsdom reuses the `path.resolve(fileURLToPath(...))` pattern in `tests/js/helpers/load.js:8`. The "present Alert" branch relies on `vi.stubGlobal("bootstrap", ns)`, which `tests/js/adapters.test.js:125-131` already proves reaches the lazy `() => globalThis.bootstrap` closure through the test window proxy.
- **D-04 correctly departs from the modal/collapse precedent.** `adapters.js:15` and `:33` throw `missing()` when the component is absent. The plan explicitly tells the executor not to copy that for `alert` and to remove instead. That is the right call and is consistent with `04-PATTERNS.md`.
- **Rendering regressions are grounded.** `tests/test1/test_messages.py:165-170` already does a real POST, follow and render, so 04-01-03's "real create-response flash message" is a one-line assertion change, not new infrastructure.

**Concerns**
- **MEDIUM. Task 04-01-02 commits a red suite.** `tests/test1/test_messages.py:139` and `:169` assert `data-bs-dismiss="alert"`. The tracer changes the template but its verify command deliberately runs only `test_alerts.py`; the two assertions stay red until 04-01-03. The plan admits this ("Do not call the intermediate full suite green"), but it still produces a commit where `pytest tests` fails, which breaks bisectability and collides with the executor's hard acceptance gate if it runs the combined command.
- **MEDIUM. Wrong branch.** HEAD is `introduce-gsd`. `.planning/PROJECT.md:75-77` requires `feat/alert-dismiss-adapter`, and ROADMAP success criterion 1 says the PR must show the markup diff. No task creates or switches branch before the baseline commit, so the ALRT-01 history evidence may land somewhere the PR never sees.
- **LOW. Trailing newline convention is unspecified.** The render starts with `\n` (from `alert.html:1`) and ends without one. The existing helper at `tests/test1/test_form_frame.py:50-55` appends `\n` on write and strips on read. The plan forbids strip. Either is fine, but the writer and reader must agree and the docstring should say so, or the first editor that adds a final newline silently breaks the test.
- **LOW. Global stub leakage.** `tests/js/viewset.test.js` has no `afterEach(vi.unstubAllGlobals)` (unlike `adapters.test.js:18`). A `bootstrap` stub left by a tracer case survives into later tests, including the final reload test at `:92-101`, which manages `$`/`jQuery` by hand.

**Suggestions**
- Move the two `test_messages.py` assertion updates into 04-01-02 so every commit is green. It is a two-line change and the file is not otherwise touched by that task.
- Add a first step to 04-01-01: create or check out `feat/alert-dismiss-adapter` from the integration point the maintainer wants, then record the branch and baseline hash in the summary.
- State the golden byte contract once: write `markup.encode("utf-8")`, compare against `read_bytes()`, no appended newline.
- Add a local `afterEach` in the new describe block that calls `vi.unstubAllGlobals()` and deletes `window.cv`.
- Write the handler call as `globalThis.cv.adapters.alert.close(frame)` to mirror `adapters.js:43` and avoid relying on jsdom exposing `window.cv` as a bare global.

**Risk Assessment: MEDIUM.** The design is correct and traceable to source. The risk is process: one red commit and an unaddressed branch, both cheap to fix before execution.

## 04-02

**Summary.** This plan is a regression matrix over the seam 04-01 delivers, and the matrix is the right one: object, function and late namespaces (`adapters.js:7-8`), preassigned adapters (`adapters.js:43`), nested and dynamic frames, and the D-03 no-recovery contract. It correctly anticipates that a throwing listener does not propagate through `dispatchEvent` and points at the right precedent. The main gap is that the precedent it cites does something the plan's own assertion forbids.

**Strengths**
- **Fixture extension is trivial and safe.** `fakeNamespace()` at `tests/js/adapters.test.js:4-14` is a plain object; adding `Alert: { getOrCreateInstance }` with a `close` spy follows the `Collapse` entry on line 12.
- **Error observation matches jsdom.** `tests/js/list.filter.test.js:198-203` shows the pattern: a window `error` listener that calls `preventDefault()` so jsdom does not forward the uncaught listener error to `console.error`. The plan requires `finally` cleanup, which the precedent lacks. Good.
- **Edge predicates are DOM-accurate.** `el.remove()` on a detached node is a no-op, and a click inside a detached subtree never reaches `document`. Both EDGE-ALRT-03 truths hold without new code.
- **Bounded product edits.** Listing `adapters.js` and `viewset.js` in `files_modified` while restricting fixes to "the alert branch" keeps 04-02 from reopening 04-01's contract.

**Concerns**
- **MEDIUM. "No console.error from core" can become vacuous.** The cited precedent at `list.filter.test.js:199` does `vi.spyOn(console, "error").mockImplementation(() => {})` *and* prevents default. If the executor copies both, the mocked spy swallows any core logging and the assertion only means "the mock exists". The plan needs to say: spy `console.error` as passthrough, prevent default on the window error event, assert the spy was not called, restore in `finally`. `tests/js/helpers/setup.js:11-12` mocks only `log` and `assert`, so `error` is live by default.
- **LOW. Present-component double-close is a Bootstrap behaviour, not a core one.** Under a real Bootstrap `Alert`, a second `close()` during the fade transition queues a second `_destroyElement` after `dispose()` nulled `_element`. Bootstrap's own data API has the same exposure. The plan's "no new scheduling guarantee" wording is correct, but 04-03's docs and acceptance note must not phrase the repeated-click truth as a safety promise.
- **LOW. Nested-role test needs an explicit outer-survives assertion.** `closest('[role="alert"]')` picks the innermost frame. The test should assert the outer alert is still attached, not only that the adapter received the inner one.
- **LOW. Non-Element target case already exists.** `tests/js/viewset.test.js:74-79` dispatches on `document`. Reuse it rather than adding a duplicate.

**Suggestions**
- Rewrite the error-observation instruction as a four-step recipe: passthrough spy, `preventDefault` listener capturing `event.error`, identity and `not.toHaveBeenCalled()` assertions, `finally` restore and remove.
- Add a one-line note to the two EDGE truths that they describe DOM propagation and the default adapter only, and that Bootstrap transition semantics are unchanged from the data API.
- For the "changing callback namespace" case, assert the adapter object identity is the same before and after the namespace swap, which is the real D-08 claim.

**Risk Assessment: LOW.** Pure test expansion over a contract already proven by 04-01. The one real defect is a testing-technique ambiguity that would produce a passing but meaningless assertion.

## 04-03

**Summary.** The allowlist, migration analog and docs-extraction mechanism all exist in the repo, so the plan is implementable as written. Three issues need fixing before execution: the guard test's scan root is unspecified and a natural copy of an existing test would make it fail for the wrong reason; the guard includes an allowlisted path with no match; and two stale sentences in the migration guide are not in any task.

**Strengths**
- **Allowlist is exact.** `docs/reference/theme.md:179-181` names `tags/actions_menu.html`, `tags/actions_menu_toggle.html` and `snippets/language_selector.html`. The grep today returns four lines in three files (`language_selector.html:6`, `actions_menu_toggle.html:4-5`, `alert.html:5`), matching the plan's audit claim exactly.
- **Docs-extraction precedent exists.** `tests/test1/test_label_mode_docs.py:24-47` already has `FENCE`, `HEADING` and `_section()` helpers that return the body under a unique heading. 04-03-01 can reuse them instead of inventing a parser.
- **Migration wording has a template.** `docs/migrating-1.0.md:345-347` is the modal's `data-cv-modal-dismiss` bullet with the "a copy with `data-bs-dismiss` keeps working under the Bootstrap adapter only" clause. D-06 is the same sentence for alerts.
- **Example wiring supports the smoke.** `examples/bootstrap5/project/templates/project/base.html:19` loads the Bootstrap 5.3.3 bundle before `{% cv_js %}` at `:37`, and `lib/settings.py:288-289` orders `adapters.js` before `viewset.js`. Reassigning `cv.adapters.alert` in devtools works because the handler looks the adapter up at call time.

**Concerns**
- **MEDIUM. Guard scan root is unspecified and the obvious analog scans too wide.** `tests/test1/test_alerts.py:132-133` globs `crud_views*/templates/**/*.html`. An executor copying that pattern will hit `src/crud_views_object_detail/.../accordion/group.html:5,15` (`data-bs-toggle="collapse"`, `data-bs-parent`) and `tabs-vertical/object_detail.html:10-11` (`data-bs-toggle="pill"`). ROADMAP line 148 scopes the criterion to `src/crud_views/templates`. The plan must pin that root. Separately, those object-detail templates are an undocumented Bootstrap-DOM leak that `theme.md:172-181` does not list. Record it in the acceptance note for Phase 7.
- **MEDIUM. Allowlist contains a path with zero matches.** `tags/actions_menu.html` has no `data-bs-` attribute today. "Requires actual matches" must mean "matches is non-empty and matches ⊆ allowlist". Set equality would fail on day one.
- **MEDIUM. "Run that guard red against the pre-change template" is not executable in wave 3.** By 04-03 the template already changed in 04-01-02. Establishing the failure direction would require checking out old history mid-task.
- **MEDIUM. Two stale migration-guide lines are in no task.** `docs/migrating-1.0.md:309-310` names exactly three adapters, and the silent-breaks checklist at `:374` says hand-listed static files lose "the modal, filter and tooltip behaviour". Both become wrong after this phase. 04-03-02 covers only the new Breaking entry and the new before/after example.
- **LOW. Recipe may bypass the documented colour seam.** The plan's recipe uses custom `notice` classes. `theme.md:164-165` and `messages.md:50-52` state that colours come from the `alert:*` class-table keys. If the recipe replaces `{% cv_button_class "alert" alert.level %}` wholesale, the documented override contradicts the documented colour contract.
- **LOW. Browser smoke can be automated here.** A Playwright MCP server is available in this environment. The human-check should be run, not left pending, unless the example cannot start.

**Suggestions**
- Move `test_stock_bootstrap_data_attributes_are_dropdown_only` into 04-01-02. There it is red before the template edit and green after, which is the TDD direction the plan wants, and it keeps 04-03 docs-only.
- Specify the guard: root `src/crud_views/templates`, `ALLOWED = {...three paths...}`, assert `matched` and `matched <= ALLOWED`, report the offending paths.
- Add `migrating-1.0.md:309-310` and `:374` to 04-03-02's edit list alongside `javascript.md:13-14` and `:57`.
- In the recipe, keep `{% cv_button_class "alert" alert.level %}` for the level colour and change only the literal frame and control classes. State that without `fade` a present Bootstrap `Alert` removes the frame immediately.
- Reuse `_section()` from `test_label_mode_docs.py` for the recipe extraction and require the "Custom alert frame" heading to appear exactly once, as that helper already asserts.
- Note in `javascript.md` the contrast with `modal.show`, whose failure is logged per `javascript.md:40`. Alert failures are deliberately not logged (D-03). Readers will otherwise expect symmetry.

**Risk Assessment: MEDIUM.** The content is correct and well sourced. The guard-test specification is loose enough that a faithful executor could produce a test that fails for an out-of-scope reason or passes vacuously.

## Cross-plan assessment

**Dependency ordering** is right: baseline → tracer → regressions → docs. The only ordering defect is the red intermediate commit in 04-01, fixable by folding two assertion updates into the tracer task.

**Scope** is tight. No new class keys, lifecycle events, timers or observers, and the plans correctly refuse to copy the `missing()` throw pattern for `alert`. The D-04 supersession of the source plan's "handler removes the element" sentence (`superpowers/plans/2026-10-24-concept-review-followups.md:235`) is implemented consistently across all three plans.

**Security** posture is adequate for the change. Escaping lives in `src/crud_views/lib/messages.py:42-53` and is untouched. The handler uses fixed semantic selectors and the recipe test renders hostile content. Nothing new reaches the server.

**Goal achievement.** With the fixes above, the plans satisfy ALRT-01 through ALRT-04 and D-01 through D-10. The one item outside the plans' control is the object-detail `data-bs-toggle` leak, which is out of this phase's scope but should be surfaced for Phase 7's stability document.

**Overall risk: MEDIUM.** Driven by three specification gaps (branch, red commit, guard-test scope) rather than any design error.


---

## OpenCode Review (grok-review)

I'll verify each plan against the actual alert, adapter, and docs code before judging coverage.
The allowlist and adapter seams need a source check; I'll read the docs and tests those plans depend on.
## 04-01

The baseline-then-tracer split matches the code and ALRT-01. The stock frame still emits `data-bs-dismiss="alert"` only on the dismissible branch (`src/crud_views/templates/crud_views/tags/alert.html:5`), the factory still has three adapters and a lazy namespace (`src/crud_views/static/crud_views/js/adapters.js:3,7-8,43`), and `viewset.js` already delegates clicks with an `Element` guard and `closest()` (`src/crud_views/static/crud_views/js/viewset.js:37-44`). Task 2 is the right place to swap that one attribute and add one listener. ALRT-03 is only started here; custom and error ownership wait for 04-02, which is the correct cut.

**Strengths**
- Task 04-01-01 commits only the golden and its test before any product edit, and forbids `_norm` / strip. That is stricter than `tests/test1/test_form_frame.py:50-55`, which would hide the attribute diff.
- The JS tracer reads the golden instead of a hand-copied string, and new click cases must precede the reload test at `tests/js/viewset.test.js:91-101`.
- Message assertions that will go red are exactly `tests/test1/test_messages.py:139` and `:169`. Task 2's verify correctly omits that file; task 3 updates both, including the real create response.
- Removal stays inside `alert.close`, not the listener. That follows D-04 and rejects the older handler fallback in `.planning/research/PITFALLS.md:303-304`.

**Concerns**
- MEDIUM: The tracer can go green without the default adapter. `tests/js/viewset.test.js:27-28` loads only `viewset.js`. If the new cases replace `cv.adapters.alert` instead of loading `adapters.js` and stubbing `bootstrap` the way `tests/js/adapters.test.js:125-130` does, ALRT-03's present/absent branch is unproven until 04-02.
- LOW: Golden equality cannot prove "attribute only." Task 2 rewrites both the template and the golden. A class edit is caught only if task 3 hard-codes `alert-dismissible fade show` and `btn-close` from `alert.html:2-5`, which the task text does not quote.
- LOW: After task 2, `test_messages.py:139,169` fail. Fine inside one branch; not fine if that commit is pushed against the full pytest gate.

**Suggestions**
- In the tracer, forbid replacing `cv.adapters.alert`. Stub `globalThis.bootstrap` via `vi.stubGlobal`, assert `getOrCreateInstance` got the golden's `role="alert"` node, and assert a no-op `close` leaves it connected.
- Pin `translation.override("en")` (see `tests/test1/test_filter_toggle_label_mode.py:82`). `LANGUAGE_CODE` is `en-us` (`tests/test1/conftest.py:98`), but an active translation would change `{% translate 'Close' %}` and the raw golden.
- After the baseline commit, stop honoring `CV_UPDATE_GOLDEN` in this test so later rewrites are explicit file edits.

**Risk Assessment:** MEDIUM. The design matches the seams. The risk is a tracer that does not actually enter `bootstrapAdapters`.

## 04-02

This wave is the right regression matrix for D-03, D-04, and D-08, and it does not add a public method. It extends `fakeNamespace()` (`tests/js/adapters.test.js:4-14`) and the single listener from 04-01. The idempotency and concurrency truths are test locks, not a new lifecycle manager. That matches D-04: absence of `Alert` is the only fallback, and a present no-op or throw must not call `el.remove()`.

**Strengths**
- Call-time namespace checks match `component()` / `resolve()` (`adapters.js:7-8`): object, function, late `globalThis.bootstrap`, and a namespace that has `Modal`/`Tooltip`/`Collapse` but no `Alert`.
- Preassignment is the existing shallow merge (`adapters.js:43`). Keeping the whole `alert` object and still filling `modal`/`tooltip`/`collapse` is the right assertion; `adapters.test.js:133-140` already does this for `modal`.
- Error observation follows a real jsdom constraint. `tests/js/list.filter.test.js:198-201` shows listener exceptions surface as `window` `"error"` and `console.error`, and `dispatchEvent` does not rethrow.
- Dynamic cases use role and marker, not `.alert` / `btn-close`. A copied frame that drops Bootstrap classes still closes, which is the point of the seam.

**Concerns**
- MEDIUM: "No `console.error` from core" will fail if implemented as zero `console.error` calls. jsdom itself logs listener errors (`list.filter.test.js:199`). The plan says to suppress the expected report, but the acceptance line does not say how to tell that apart from a core log.
- LOW: A missing `cv.adapters.alert` (theme replaces the whole object after load) is the TypeError in `.planning/research/PITFALLS.md:288-291`. D-03 says that must surface with the node left in place. The matrix tests a throwing `close`, not a missing key.
- LOW: Detached-subtree coverage only works if the second click is dispatched on the removed control. Dispatching on `document` does not prove bubbling stopped.

**Suggestions**
- Spy `console.error`/`warn`, ignore the jsdom listener report, and assert core did not log its own message. Remove the `window` `"error"` listener in `finally`, unlike `list.filter.test.js:208`.
- Add one case: `delete cv.adapters.alert`, click, frame still connected, original `TypeError` observed. Do not add the pitfall's `el.remove()` recovery. That would violate D-04.
- For the repeat-absent case, call `close` on the same detached reference twice and assert the sibling is untouched. `Element.remove()` is a no-op the second time; the test should not recreate the node.

**Risk Assessment:** LOW. Production edits are allowed only if a case fails, and the locked behavior is already specified against the factory that exists.

## 04-03

Docs and the allowlist match the requirement text, with two traps in how the guard and the "three" wording will be edited. ALRT-04 is `grep -rn 'data-bs-' src/crud_views/templates` against the dropdown list in `docs/reference/theme.md:179-181`. Today that grep is four lines in three files: `alert.html:5`, `actions_menu_toggle.html:4-5`, `language_selector.html:6`. `actions_menu.html:1-9` is on the theme list and has no `data-bs-` attribute. The paired Breaking entry belongs under `CHANGELOG.md:7`, and script order is already `adapters.js` then `viewset.js` (`src/crud_views/lib/settings.py:288-289`).

**Strengths**
- The frame recipe is executed through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`), including hostile `extra_tags`. That is stronger than a string search, and it matches `cv_alert`'s override path (`src/crud_views/templatetags/crud_views.py:407-409`).
- Migration is a before/after plus the legacy Bootstrap-only path (D-05/D-06), not a link-only bullet. Same-change Breaking plus `docs/migrating-1.0.md` matches the repo rule.
- Browser acceptance cannot be inferred from jsdom. The human check uses the example's real `Alert`, then `cv.bootstrapAdapters({}).alert`, then a post-load insert. A blocked browser stays unverified.
- Tool drift is recorded, not papered over by editing `package.json` / `pyproject.toml`.

**Concerns**
- MEDIUM: The guard's scan root is unnamed. `tests/test1/test_alerts.py:132-133` globs `crud_views*/templates`, which includes `src/crud_views_object_detail/.../accordion/group.html:5` and `tabs-vertical/object_detail.html:10-11`. Those `data-bs-toggle` hits are outside ALRT-04 and outside `theme.md:179-181`. Copying that glob makes the new test fail for the wrong reason. "Requires actual matches" must not mean `actions_menu.html` itself contains `data-bs-`; it does not.
- MEDIUM: "Change the factory count to four" collides with a different "three." `docs/reference/javascript.md:57` is the adapter sentence. `docs/reference/javascript.md:179` is "All three are bubbling CustomEvents" (`cv:modal:unload`, `cv:modal:loaded`, `cv:formset:row-added` at `:183-185`). A blanket replace breaks the events contract the task says to keep.
- MEDIUM: Migration never says not to leave both attributes. `.planning/research/PITFALLS.md:281-284` is a double close if `data-bs-dismiss="alert"` and `data-cv-alert-dismiss` sit on the same control. D-06 covers the old attribute alone, not the mixed case.
- LOW: `messages.md:36-38` ("needs Bootstrap's JavaScript bundle") is not executed. `mkdocs build --strict` will not catch a leftover Bootstrap-only sentence. The plan explicitly skips a docs-text framework.

**Suggestions**
- Scan only `src/crud_views/templates`. Fail any match whose path is not `crud_views/tags/actions_menu.html`, `crud_views/tags/actions_menu_toggle.html`, or `crud_views/snippets/language_selector.html`. Assert the current hits are the toggle and the language selector, not the wrapper.
- Edit `javascript.md:14` (viewset use-time needs `cv.adapters.alert`) and `:57` only. Leave `:179` alone.
- In the migration example, state that the stock control must not carry both dismiss attributes. Legacy copies keep only `data-bs-dismiss="alert"`.
- Quote `role="alert"` and `data-cv-alert-dismiss` in the recipe, and `{% load crud_views i18n %}`, or the locmem override will not resolve `{% cv_icon %}` / `{% translate 'Close' %}`.

**Risk Assessment:** MEDIUM. The contract is right. The allowlist root and the two "three" sentences are the likely false failures.

## Cross-plan

Waves are ordered correctly: baseline commit, then the one rendered path, then namespace/error/dynamic cases, then docs and gates. 04-02 may touch `adapters.js` and `viewset.js` only if a case fails; 04-03 does not reopen the DOM hook. No plan adds class-table keys, focus management, or a second removal path. That matches D-01, D-03, and D-04, and it correctly overrides `.planning/research/PITFALLS.md:301-304`.

Accepted limitation, not a hole: dismissal is `closest('[role="alert"]')`. A theme that switches non-errors to `role="status"` (`PITFALLS.md:285-287`) will not close until it keeps `role="alert"`. D-08 locks that. The recipe must show it, not grow a new `data-cv-alert` hook.

What the three plans together still do not lock automatically is the golden diff (manual in 04-01 verification and 04-03-03) and a real Bootstrap fade (human-check only). Both are declared. Do not mark D-10 verified from the Vitest fakes.

## Overall risk

MEDIUM. The phase achieves the goal if the tracer uses the real factory and the data-attribute guard is rooted at `src/crud_views/templates`. Nothing in the plans needs a new dependency, a public name beyond `data-cv-alert-dismiss` and `cv.adapters.alert.close`, or a behavior the current seams cannot express.


---

## OpenCode Review (gemini-review)

## 04-01

### 1. Summary
Plan `04-01` sequences the baseline golden commit (`ALRT-01`), the core template/JS implementation (`ALRT-02`, `ALRT-03`), and server-side alert/message regression updates across three tightly scoped tasks. The end-to-end tracer bridging the raw Python-rendered golden (`tests/test1/golden/alerts/dismissible.html`) directly into `jsdom` in `tests/js/viewset.test.js` is well-architected and prevents fixture drift between the Django template and JavaScript delegation tests. A few subtle state-isolation details in `tests/js/viewset.test.js` and global lookup conventions in `src/crud_views/static/crud_views/js/viewset.js` warrant attention during execution.

### 2. Strengths
- **Raw byte-for-byte golden comparison (`tests/test1/test_form_frame.py:44-55` vs `tests/test1/test_alerts.py:70-71`):** Unlike `_check_golden` in `tests/test1/test_form_frame.py:44-55`, which normalizes whitespace via `_norm()`, Task `04-01-01` compares raw UTF-8 bytes (`read_bytes()`) under a fixed English locale (`translation.override("en")`), guaranteeing that `src/crud_views/templates/crud_views/tags/alert.html:1-6` experiences zero unintended whitespace drift outside `data-bs-dismiss="alert"` → `data-cv-alert-dismiss`.
- **Single-source Python-to-JS fixture bridge (`tests/js/helpers/load.js:1-8`, `tests/js/viewset.test.js:1-3`):** Reading `DISMISSIBLE_ALERT_HTML` directly from `tests/test1/golden/alerts/dismissible.html` using `node:fs`, `node:path`, and `fileURLToPath(import.meta.url)` (matching `tests/js/helpers/load.js:6-8`) ensures `tests/js/viewset.test.js` tests the exact HTML emitted by `{% cv_alert %}` rather than a hand-written approximation.
- **Correct placement before the duplicate-listener reload test (`tests/js/viewset.test.js:27-29,91-101`):** `tests/js/viewset.test.js:28` loads `viewset.js` once in `beforeAll`, and `tests/js/viewset.test.js:92-101` (`it("loads without jQuery")`) calls `loadScript("viewset")` a second time, registering duplicate `document` event listeners. Task `04-01-02` explicitly places the new click tracer cases before line 91 and reuses the single `beforeAll` listener.
- **Complete message assertion coverage (`tests/test1/test_messages.py:139,169`):** Task `04-01-03` identifies both existing `assert 'data-bs-dismiss="alert"' in html` assertions in `tests/test1/test_messages.py` (line 139 in `test_cv_messages_renders_a_dismissible_alert` and line 169 in `test_create_message_renders_as_an_alert`) and pairs them with translation coverage for `{% translate 'Close' %}` (`src/crud_views/templates/crud_views/tags/alert.html:5`, `src/crud_views/locale/de/LC_MESSAGES/django.po:103-104`).

### 3. Concerns
- **[MEDIUM] `adapters.js` shallow-merge behavior can leak `window.cv.adapters` across tests in `tests/js/viewset.test.js` (`src/crud_views/static/crud_views/js/adapters.js:43`, `tests/js/viewset.test.js:31-33`):** `src/crud_views/static/crud_views/js/adapters.js:43` assigns `cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {})`. Because `cv.adapters` is the *second* argument to `Object.assign` (to preserve preassigned adapters), calling `await loadScript("adapters")` in a subsequent test will **not** overwrite an existing `window.cv.adapters.alert` if `window.cv` was left behind by an earlier test. Furthermore, `tests/js/viewset.test.js:31-33` currently only resets `document.body.innerHTML = ""` in `beforeEach` and has no `afterEach` cleanup, while `tests/js/helpers/setup.js:7-8` calls `vi.stubGlobal("$", $)` only once at module import time—so calling `vi.unstubAllGlobals()` in `viewset.test.js` would wipe out `$` and `jQuery`.
- **[LOW] Unqualified `cv` vs `globalThis.cv` in `src/crud_views/static/crud_views/js/viewset.js` (`src/crud_views/static/crud_views/js/viewset.js:1-44`, `src/crud_views/static/crud_views/js/list.filter.js:15`):** Unlike `adapters.js:4` and `modal.js:143`, `viewset.js:1-44` does not declare or initialize `globalThis.cv`. Referencing `globalThis.cv.adapters.alert.close(frame)` (as done in `src/crud_views/static/crud_views/js/list.filter.js:15`) rather than bare `cv.adapters.alert.close(frame)` is cleaner when `viewset.js` is evaluated via `new Function("window", "globalThis", code)(win, win)` in `tests/js/helpers/load.js:36`.
- **[LOW] gettext sentinel target for `{% translate 'Close' %}` (`src/crud_views/templates/crud_views/tags/alert.html:5`, `tests/test1/test_i18n.py:132-136`):** Task `04-01-03` specifies exercising translated `Close` through "an isolated gettext sentinel". Unlike `test_filter_gettext_at_render_time` (`tests/test1/test_i18n.py:132`), where `buttons._` is a module-level Python alias, `{% translate 'Close' %}` in `alert.html:5` is evaluated by `django.templatetags.i18n.TranslateNode.render`, which calls `django.utils.translation.gettext`. Monkeypatching must target `django.utils.translation.gettext` (or pair with `with translation.override("de"):` where `src/crud_views/locale/de/LC_MESSAGES/django.po:103-104` maps `"Close"` → `"Schließen"`).

### 4. Suggestions
- In `tests/js/viewset.test.js`, clean up `delete window.cv; delete window.bootstrap;` in `afterEach` (or in a `finally` block per test) rather than calling `vi.unstubAllGlobals()`, so `adapters.js:43` starts from a clean `window.cv` on every test without clobbering `tests/js/helpers/setup.js:7-8`.
- In `src/crud_views/static/crud_views/js/viewset.js`, invoke `globalThis.cv.adapters.alert.close(alertEl)` (matching `src/crud_views/static/crud_views/js/list.filter.js:15` and `viewset.js:43`'s `globalThis.location.href`).
- In `tests/test1/test_alerts.py` (Task `04-01-03`), monkeypatch `django.utils.translation.gettext` for the render-time sentinel check and/or assert `aria-label="Schließen"` under `with translation.override("de"):`.

### 5. Risk Assessment
**Risk Level: LOW**
The scope is small, the baseline commit chronology (`ALRT-01` / `D-07`) is explicitly enforced before product edits in Task `04-01-01`, and the shared golden file links Python template rendering directly to `jsdom` click delegation.

---

## 04-02

### 1. Summary
Plan `04-02` expands unit and DOM integration coverage in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` to verify lazy namespace resolution, preassigned and post-load custom adapter swaps, dynamic/modal-injected alerts, error surfacing without core recovery (`D-03`, `D-04`), and repeated-click/idempotency edge cases (`ALRT-02`, `ALRT-03`). The test matrix is thorough and aligns with the locked decisions, though the plan overlooks an existing test helper (`tests/js/helpers/errors.js`) that was built specifically for observing uncaught DOM listener errors in `jsdom`.

### 2. Strengths
- **Clear separation between missing `Alert` fallback and present-component ownership (`src/crud_views/static/crud_views/js/adapters.js:7-8,12-43`):** Task `04-02-01` tests not only a missing/null namespace, but also a namespace containing `Modal`, `Tooltip`, and `Collapse` without `Alert`, as well as a present no-op `Alert` and a throwing `Alert.getOrCreateInstance` / `close()`. This directly verifies `D-03` and `D-04` (that `el.remove()` is only the absent-`Alert` branch inside the default adapter, never a post-call fallback or error recovery path).
- **Dynamic and semantic DOM targeting (`src/crud_views/static/crud_views/js/viewset.js:37-44`, `tests/js/viewset.test.js`):** Task `04-02-02` tests nested `[role="alert"]` containers, clicks on child elements inside `[data-cv-alert-dismiss]`, custom non-Bootstrap classes, and alerts injected into a modal subtree after `viewset.js` has loaded.
- **Explicit verification of idempotency and rapid clicks (`EDGE-ALRT-03-idempotency`, `EDGE-ALRT-03-concurrency`):** Both spec-less edge cases are verified against standard DOM semantics without introducing unnecessary production state, timers, or lifecycle events.

### 3. Concerns
- **[MEDIUM] Plan misses existing `listenerErrors` helper in `tests/js/helpers/errors.js` and points to a leaky pattern in `tests/js/list.filter.test.js` (`tests/js/helpers/errors.js:1-18`, `tests/js/tooltip.test.js:2,140-236`, `tests/js/list.filter.test.js:198-208,309-320`):** Plan `04-02` (lines 64-65 and Task `04-02-02` `<read_first>` / `<action>`) instructs writing a test-local temporary `window` `"error"` listener modeled after `tests/js/list.filter.test.js:198-213`. However, `tests/js/helpers/errors.js:5-18` (`export function listenerErrors(fn)`) already exists in the codebase (used across `tests/js/tooltip.test.js:2,140-236`) and already captures `event.error ?? event.message`, calls `event.preventDefault()`, and removes the `window` `"error"` listener in `finally`. Meanwhile, `tests/js/list.filter.test.js:199,310` calls `vi.spyOn(console, "error").mockImplementation(() => {})` without ever calling `mockRestore()`, leaking a mocked `console.error` across tests.
- **[LOW] Ignored-target assertions in `tests/js/viewset.test.js` need `listenerErrors` to catch listener exceptions (`tests/js/viewset.test.js:69,77`, `tests/js/helpers/errors.js:1-4`):** Existing `tests/js/viewset.test.js:69,77` uses `expect(() => button.click()).not.toThrow()`, which (as documented in `tests/js/helpers/errors.js:1-4`) cannot observe exceptions thrown inside a DOM event listener in `jsdom`. If Task `04-02-02`'s ignored-target tests (orphan `[data-cv-alert-dismiss]` outside `[role="alert"]`, non-`Element` target) only check adapter spy call counts without `listenerErrors(...)`, an unhandled `TypeError` inside the listener could go unnoticed if `event.preventDefault()` or error handling changes.

### 4. Suggestions
- Import and reuse `listenerErrors` from `./helpers/errors.js` (`tests/js/helpers/errors.js:5-18`) in `tests/js/viewset.test.js` both for custom-adapter throw tests (`expect(listenerErrors(() => button.click())).toEqual([boom])`) and for ignored-target tests (`expect(listenerErrors(() => orphanButton.click())).toEqual([])`).
- When spying on `console.error` and `console.warn` in Task `04-02-02` to assert that core logs nothing on adapter throws, restore both spies in `finally` (`errSpy.mockRestore(); warnSpy.mockRestore();`) so they do not persist into subsequent tests like `tests/js/list.filter.test.js:199`.
- Update `tests/js/adapters.test.js:20-24` (`it("defines cv.adapters.modal/tooltip/collapse and cv.bootstrapAdapters")`) to include `"alert"` in the adapter name loop (`for (const name of ["modal", "tooltip", "collapse", "alert"])`) and update the test title accordingly.

### 5. Risk Assessment
**Risk Level: LOW**
All changes in `04-02` are confined to the JS unit/DOM test suites (plus any bounded fixes in `adapters.js` / `viewset.js`). Reusing `tests/js/helpers/errors.js` and isolating `window.cv` / `console` spies eliminates the main test-hygiene risks.

---

## 04-03

### 1. Summary
Plan `04-03` updates the three reference docs (`javascript.md`, `messages.md`, `theme.md`), adds executable tests in `tests/test1/test_alerts.py` for the documented custom alert frame recipe and the stock `data-bs-*` template audit, updates `CHANGELOG.md` and `docs/migrating-1.0.md` in a paired commit, and runs the full project quality gates and example browser smoke check (`ALRT-04`, `D-02`, `D-05`, `D-06`, `D-09`, `D-10`). However, there is a high-likelihood test implementation trap in Task `04-03-01`'s `test_stock_bootstrap_data_attributes_are_dropdown_only` regarding the template glob scope and set comparison, as well as two stale 3-adapter references in `docs/migrating-1.0.md` that Task `04-03-02` should update.

### 2. Strengths
- **Executable documentation recipe test (`docs/reference/theme.md:156-170`, `tests/test1/test_alerts.py:110-114`, `tests/test1/test_form_frame.py:58-68`):** Extracting the fenced HTML under `Custom alert frame` from `docs/reference/theme.md` and rendering it through `_theme_templates({"crud_views/tags/alert.html": ...})` with dismissible/non-dismissible states, text/list bodies, and hostile `extra_tags`/content ensures the documented override recipe in `theme.md` cannot rot.
- **Careful distinction between adapter count and event count in `docs/reference/javascript.md` (`docs/reference/javascript.md:14,57,179`):** Task `04-03-01` accurately updates `cv.bootstrapAdapters(ns)` at `docs/reference/javascript.md:57` from "all three adapters" to "all four adapters" and updates `viewset.js`'s "Needs at use" column at line 14, while explicitly preserving "All three are bubbling `CustomEvent`s" at line 179.
- **Honest gate and browser-smoke accounting (`examples/bootstrap5/project/templates/project/base.html:19-38,56`):** Task `04-03-03` explicitly prohibits substituting `manage.py check`, `test_docs_sync.py`, or `jsdom` unit tests for real browser transition verification on the example project, and requires recording installed tool version drift (`vitest`, `jsdom`, `ruff`) rather than altering `package.json` or `pyproject.toml`.

### 3. Concerns
- **[HIGH] `test_stock_bootstrap_data_attributes_are_dropdown_only` will fail if it copies `test_alerts.py:133`'s glob or asserts exact set equality with the 3 allowlisted files (`tests/test1/test_alerts.py:130-143`, `src/crud_views/templates/crud_views/tags/actions_menu.html:1-9`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/tabs-vertical/object_detail.html:10-11`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5,15`):**
  1. In `tests/test1/test_alerts.py:133`, the existing `test_only_the_alert_templates_write_alert_markup` scans `src.glob("crud_views*/templates/**/*.html")` across all five apps. However, `src/crud_views_object_detail/templates/` contains four `data-bs-*` lines (`tabs-vertical/object_detail.html:10-11` has `data-bs-toggle="pill"` / `data-bs-target`, and `accordion/group.html:5,15` has `data-bs-toggle="collapse"` / `data-bs-target` / `data-bs-parent`). Per `ALRT-04` (`grep -rn 'data-bs-' src/crud_views/templates`), the test must scan `src / "crud_views" / "templates"`, **not** `crud_views*/templates`.
  2. Within `src/crud_views/templates`, `crud_views/tags/actions_menu.html:1-9` contains **zero** `data-bs-*` attributes (it only has `class="dropdown-menu dropdown-menu-end"` and includes `actions_menu_toggle.html`). After `alert.html` is updated, only **two** files match `data-bs-`: `crud_views/tags/actions_menu_toggle.html:4-5` and `crud_views/snippets/language_selector.html:6`. If the test asserts `found == {"crud_views/tags/actions_menu.html", "crud_views/tags/actions_menu_toggle.html", "crud_views/snippets/language_selector.html"}` instead of `assert found and found <= ALLOWED` (or `found == {"crud_views/tags/actions_menu_toggle.html", "crud_views/snippets/language_selector.html"}`), the test will fail.
- **[MEDIUM] Existing sections in `docs/migrating-1.0.md` still list only three adapters and omit alert dismissal from the `adapters.js` silent-break checklist (`docs/migrating-1.0.md:309-310,374-375`):**
  - `docs/migrating-1.0.md:309-310` currently reads: `- **JavaScript:** cv.adapters.modal, cv.adapters.tooltip and cv.adapters.collapse replace Bootstrap's API for a theme on another framework`.
  - `docs/migrating-1.0.md:374-375` currently reads: `- [ ] Hand-listed static files without crud_views/js/adapters.js lose the modal, filter and tooltip behaviour`.
  - `docs/reference/settings.md:184-189` also lists the delegated attributes handled by `viewset.js` (`[data-cv-action="submit-form"]` and `[data-cv-cancel-url]`) without `[data-cv-alert-dismiss]`.
  If Task `04-03-02` only adds a new before/after block without updating `docs/migrating-1.0.md:309-310` and `374-375` (plus the theme silent-breaks checklist at lines `385-410`), `migrating-1.0.md` will contradict itself on the same page.

### 4. Suggestions
- In Task `04-03-01`, explicitly scope `test_stock_bootstrap_data_attributes_are_dropdown_only` to `(Path(__file__).resolve().parents[2] / "src" / "crud_views" / "templates").rglob("*.html")` and assert:
  - `found == {"crud_views/tags/actions_menu_toggle.html", "crud_views/snippets/language_selector.html"}` (or `assert found and found <= {"crud_views/tags/actions_menu.html", "crud_views/tags/actions_menu_toggle.html", "crud_views/snippets/language_selector.html"}`).
- In Task `04-03-02`, specify the exact update locations in `docs/migrating-1.0.md`:
  - `### CSS and tests that select on markup` (`docs/migrating-1.0.md:199-200`, under `- **Alerts** (#250)`): note `data-cv-alert-dismiss` replacing `data-bs-dismiss="alert"`.
  - `### Hooks instead of copies` (`docs/migrating-1.0.md:309-310`): add `cv.adapters.alert` to the list of JavaScript adapters.
  - `### Contract changes in templates you still override` (next to `- **The modal:**` at `docs/migrating-1.0.md:345-347`): place the before/after `tags/alert.html` snippet (`D-05`), core script order (`adapters.js` before `viewset.js` / `{% cv_js %}`), and the recommendation + legacy `data-bs-dismiss="alert"` explanation (`D-06`).
  - `## Silent breaks` (`docs/migrating-1.0.md:374-375` and `385-410`): add alert closing to the `crud_views/js/adapters.js` bullet at line 374 and note copied `tags/alert.html` behavior on non-Bootstrap pages.

### 5. Risk Assessment
**Risk Level: LOW**
Aside from ensuring the template scan path and set assertion in `test_stock_bootstrap_data_attributes_are_dropdown_only` match `src/crud_views/templates` and updating the existing adapter lists in `docs/migrating-1.0.md`, the documentation and verification tasks are well-structured and low-risk.

---

## Cross-Plan & Overall Assessment

- **Goal & Requirement Coverage:** All four phase requirements (`ALRT-01` through `ALRT-04`) and all ten locked context decisions (`D-01` through `D-10`) are traced to specific tasks and verification commands across Waves 1–3 (`04-01` → `04-02` → `04-03`).
- **Dependency Ordering:** Wave ordering is sound. Task `04-01-01` isolates the pre-change golden commit (`ALRT-01`) before Task `04-01-02` touches `alert.html`, `adapters.js`, or `viewset.js`. Plan `04-02` builds on `04-01`'s adapter and listener implementation without file conflicts, and Plan `04-03` locks down the public documentation, migration notes, and static/browser verification gates last.
- **Top Actionable Fixes Before/During Execution:**
  1. In `04-03-01` (`tests/test1/test_alerts.py`), scan `src/crud_views/templates` (not `src.glob("crud_views*/templates/**/*.html")` as in `test_alerts.py:133`, which hits `crud_views_object_detail`) and account for `crud_views/tags/actions_menu.html` having zero `data-bs-` matches.
  2. In `04-01-02` and `04-02-02` (`tests/js/viewset.test.js`), reuse `listenerErrors` from `tests/js/helpers/errors.js:5-18` and reset `delete window.cv; delete window.bootstrap;` between tests so `adapters.js:43`'s `Object.assign(..., cv.adapters || {})` does not leak custom adapters across tests.
  3. In `04-03-02` (`docs/migrating-1.0.md`), update the existing three-adapter list at line 309 and the missing-`adapters.js` silent break at line 374 alongside the new before/after alert migration snippet.


---

## OpenCode Review (deepseek-review)

I'll review the three plans for Phase 4 of the django-crud-views project. Let me start by examining the repository structure to understand the current codebase.
Now let me examine the key files mentioned in the plans:
Now let me look at the tests directory to understand the current test structure:
Now let me look at the golden test pattern to understand the existing golden test approach:
Now let me examine the documentation files to understand what needs to be updated:
Now let me examine the current CHANGELOG to understand the format:
Now let me examine the context files to understand the project structure better:
Now I have a good understanding of the codebase and the plans. Let me review each plan systematically.

## Plan Coverage Manifest

Total plans in this review: 3

Plan ids (give each one its own `##`-level section, headed verbatim):
- 04-01
- 04-02
- 04-03

## 04-01

**Summary**: This plan establishes the foundational implementation of the alert dismiss adapter by creating a baseline golden test, implementing the core adapter functionality, and updating message rendering tests to use the new attribute.

**Strengths**:
- **Strong baseline approach**: Committing a golden of the current dismissible alert before changes (`src/crud_views/templates/crud_views/tags/alert.html:5`) provides clear diff visibility for ALRT-01
- **Proper test isolation**: Using the existing `CV_UPDATE_GOLDEN` pattern (`tests/test1/test_form_frame.py:52`) maintains consistency with project conventions
- **Clear dependency injection**: Leverages existing `cv.bootstrapAdapters` factory pattern (`src/crud_views/static/crud_views/js/adapters.js:12-42`) for seamless integration
- **Semantic DOM traversal**: Uses `closest("[data-cv-alert-dismiss]")` and `nearest role="alert"` approach which follows existing pattern in `viewset.js` (`src/crud_views/static/crud_views/js/viewset.js:40`)
- **Conservative scope**: Only changes the dismiss attribute while preserving all other markup, respecting D-01 and D-07

**Concerns**:
- **HIGH**: Missing test for `alert.close` method signature in `adapters.js`: Plan doesn't specify the exact implementation pattern for the new `alert.close(el)` method. Should follow existing `modal.show/hide` pattern with proper error handling
- **MEDIUM**: No explicit handling for multiple `data-cv-alert-dismiss` buttons within same alert: Could cause issues if nested or multiple close controls exist
- **LOW**: Golden test may normalize whitespace differently: `_norm` function in `tests/test1/test_form_frame.py:45-47` strips/replaces whitespace which may hide actual rendering differences

**Suggestions**:
- Add explicit test for `alert.close` method signature matching existing adapter patterns
- Ensure the delegated handler checks for `closest("[data-cv-alert-dismiss]")` then `closest('[role="alert"]')` to handle nested controls properly
- Update the `adapters.js` factory comment from "three adapters" to "four adapters" as mentioned in D-09

**Risk Assessment**: **MEDIUM** - The core functionality is well-scoped but missing explicit implementation details for the new adapter method could lead to inconsistent patterns.

## 04-02

**Summary**: This plan expands test coverage to verify namespace resolution, dynamic content handling, and custom adapter ownership behaviors, addressing edge cases identified in the research.

**Strengths**:
- **Comprehensive namespace testing**: Tests object, function, and late global namespaces which aligns with existing `component(ns, name)` resolver (`src/crud_views/static/crud_views/js/adapters.js:8`)
- **Proper error ownership**: Tests that custom adapter errors surface without core recovery, respecting D-03
- **Dynamic content coverage**: Tests alerts inserted after script load, addressing D-08 requirement
- **Existing test patterns**: Leverages `fakeNamespace()` helper from `tests/js/adapters.test.js` and `loadScript()` pattern
- **Edge case coverage**: Includes repeated calls, detached elements, and concurrent clicks

**Concerns**:
- **MEDIUM**: Test for "present Alert component owns close even when it does nothing or throws" may be difficult to implement without mocking Bootstrap's internal `getOrCreateInstance` behavior
- **MEDIUM**: "Two rapid clicks while the adapter leaves its frame attached invoke the current adapter once each" test could have race conditions in test environment
- **LOW**: Extensive error observation setup (`window error observer`) adds complexity to tests; could be simplified with spies

**Suggestions**:
- Use `vi.spyOn()` for Bootstrap component fakes rather than complex error observers
- Consider testing the "no forced removal after throwing adapter" with a simple mock that throws and asserts no `el.remove()` call
- Add test for namespace with other components but no `Alert` (tests fallback removal)

**Risk Assessment**: **LOW** - The plan thoroughly addresses edge cases and maintains consistent patterns with existing test suite.

## 04-03

**Summary**: This plan finalizes the implementation by updating documentation, adding migration guidance, and running comprehensive validation gates to ensure all requirements are met.

**Strengths**:
- **Complete documentation update**: Updates all three reference docs (`javascript.md`, `messages.md`, `theme.md`) as required by D-09
- **Paired Breaking/migration**: Updates both `CHANGELOG.md` and `docs/migrating-1.0.md` together, following project convention (`CLAUDE.md`)
- **Practical recipe**: Adds executable frame override recipe to `theme.md` with actual rendering test (`test_documented_alert_frame_override`)
- **Comprehensive validation**: Runs all quality gates (Python tests, JS tests, docs build, Ruff, example project)
- **Honest acceptance tracking**: Creates `04-ACCEPTANCE.md` to track browser verification separately from unit tests

**Concerns**:
- **HIGH**: `test_stock_bootstrap_data_attributes_are_dropdown_only` may fail on current codebase: `grep -rn 'data-bs-' src/crud_views/templates` shows alert.html contains `data-bs-dismiss="alert"` which violates the requirement until changed
- **MEDIUM**: Browser acceptance test depends on running example project; may be environment-dependent
- **MEDIUM**: Documentation sync test (`test_docs_sync.py`) may not catch all documentation inconsistencies

**Suggestions**:
- Run the data-attribute audit early to identify all `data-bs-` occurrences before implementation
- Ensure the `theme.md` update includes the exact three allowed dropdown template paths currently documented
- Add a simple smoke test for the migration example to verify it renders correctly

**Risk Assessment**: **MEDIUM** - Documentation updates are comprehensive but depend on successful implementation from previous plans; the data-attribute audit is critical path.

## Overall Assessment

**Cross-Plan Issues**:
1. **Dependency ordering**: Plans correctly sequence 04-01 → 04-02 → 04-03 with proper dependencies
2. **Missing integration test**: No plan explicitly tests the full flow from Django template rendering → JS event delegation → adapter → Bootstrap component/removal
3. **Tool version drift**: Plans acknowledge but don't resolve installed vs declared version mismatches (Vitest 4.1.10 vs ^5.0.3)

**Security Considerations**:
- V1 Encoding preserved: Existing escaping tests maintained (`tests/test1/test_alerts.py:41-55`)
- V3 Web Frontend Security: Semantic selectors (`[data-cv-alert-dismiss]`, `[role="alert"]`) prevent arbitrary DOM removal
- No new injection vectors: Attribute change only, no new template interpolation

**Performance Implications**:
- Minimal overhead: Single delegated click handler added to `viewset.js`
- Lazy resolution: `component(ns, "Alert")` resolves at call time, not load time
- No per-alert initialization: Delegated handler handles dynamic content

**Plan Completeness**: The plans collectively address all requirements (ALRT-01 through ALRT-04) and decisions (D-01 through D-10). Each plan has clear objectives, verifiable acceptance criteria, and maintains project conventions.

**Primary Risk**: The success depends on proper implementation of the new `alert.close` adapter method following existing patterns. If implemented inconsistently, it could break theme compatibility or have unexpected error handling behavior.

**Recommendation**: Proceed with implementation, paying close attention to:
1. Matching existing adapter patterns in `adapters.js`
2. Running the data-attribute audit early to identify all `data-bs-` occurrences
3. Ensuring the delegated handler properly handles edge cases (nested controls, missing roles)


---

## Consensus Summary

### Agreed Strengths

- All four reviewers confirm the baseline-first chronology, semantic delegated handler, lazy adapter factory and locked absent-only fallback fit existing source (`alert.html:5`, `adapters.js:7–8,43`, `viewset.js:37–44`).
- The rendered golden shared by Python and JS supplies a real fixture-to-handler-to-adapter tracer; dynamic content and theme ownership are covered without new initialization or lifecycle state.
- Paired Breaking/migration guidance, executable frame recipe and explicit browser-evidence limits cover the public contract. No reviewer found a need for new dependencies or class-table keys.

### Agreed Concerns

**H1 — HIGH, audit-test scan contract (Gemini HIGH; Fable/Grok overlapping MEDIUM).**
`04-03-PLAN.md:127–132` does not name the scan root or explicitly distinguish allowed paths from paths required to match. The existing analog at `tests/test1/test_alerts.py:132–133` scans every app; `crud_views_object_detail` contains out-of-scope Bootstrap hooks, while the allowed wrapper `src/crud_views/templates/crud_views/tags/actions_menu.html:1–9` contains none. Scope the guard to `src/crud_views/templates`, require a nonempty match set and `matched <= ALLOWED`, and report forbidden paths. Specify a viable red-direction check using the committed pre-change alert snapshot in a temporary scan tree (or another explicit approach that does not check out old source). This is a specification gap, not a claim the intended implementation already exists. Corroboration makes it a counted HIGH under the convergence consensus gate.

### Current Actionable Non-HIGH Concerns

| ID | Severity / origin | PLAN.md revision needed |
|---|---|---|
| A1 | MEDIUM / Fable, Grok | Keep the tracer commit green: move both legacy message-attribute assertion updates (`tests/test1/test_messages.py:139,169`) into 04-01-02, update its file/read/verify contract and leave broader rendering regressions in task 3. Remove the plan's deliberate intermediate-red exception. |
| A2 | MEDIUM / Fable | Add an explicit branch disposition to PLAN.md: preserve the established `introduce-gsd` branch under the recorded maintainer choice and plan-phase branch invariant; reject the proposed new branch. Do not silently accept the reviewer's request to switch. The existing plan contains no such rationale. |
| A3 | MEDIUM / Gemini; LOW / Fable, Grok | Make JS isolation and lookup explicit in 04-01/02: use `globalThis.cv` at call time and scoped cleanup/reset of `window.cv` and the Bootstrap stub. Do not blindly call `vi.unstubAllGlobals()` in viewset tests because setup stubs `$`/`jQuery` once (`tests/js/helpers/setup.js:7–8`). Ensure the tracer actually uses fresh real adapters rather than a preserved custom object (`adapters.js:43`). |
| A4 | MEDIUM / Gemini; overlapping test-technique comments Fable/Grok | Reuse existing `listenerErrors` (`tests/js/helpers/errors.js:5–18`) in 04-02, including expected throws and ignored-target dispatches; assert original error identity or an empty error list. Assert no core console calls and restore error/warn spies in finally. This replaces a new local error observer without changing D-03. |
| A5 | MEDIUM / DeepSeek; LOW / Fable | Add an explicit multiple-controls-in-one-alert regression and strengthen nested-role assertions: one call per chosen control, the nearest frame selected, outer frame and siblings remain connected. Current nested/descendant coverage does not expressly name two controls in the same frame. |
| A6 | LOW / Grok | Add missing-adapter-key coverage: delete `cv.adapters.alert`, dispatch a marked click, observe TypeError through `listenerErrors`, retain the frame and perform no fallback/logging. Do not repair the theme's object in core. |
| A7 | MEDIUM / Fable, Gemini | Expand 04-03's documentation edit list: update existing three-adapter enumeration at `docs/migrating-1.0.md:309–310`, missing-adapters checklist at `:374–375`, relevant alert markup/override checklist prose and `docs/reference/settings.md:184–189` delegated-hook description. These existing statements otherwise remain stale despite a new migration example. Add settings.md to files_modified/read_first. |
| A8 | LOW / Fable; recipe-completeness suggestions Grok | State that the custom frame recipe retains `{% cv_button_class "alert" alert.level %}` and `{% load crud_views i18n %}`, changing literal frame/control classes while keeping the existing level-colour seam (`theme.md:164–165`, `messages.md:50–52`). Extract its uniquely named heading using the established docs-test pattern. The current recipe task does not expressly preserve this colour accessor. |
| A9 | MEDIUM / Grok | In 04-03 migration guidance explicitly tell copied templates to replace the old dismiss attribute, not retain both hooks on one control; otherwise both Bootstrap and core can attempt close. Preserve D-06's legacy-old-attribute-only compatibility statement. |
| A10 | LOW / Gemini | Name a viable translation test seam in 04-01-03: template `{% translate %}` does not use a Python button module alias. Patch the actual Django translation seam locally or use a verified real locale/label; restore state and keep the golden pinned to English. |

### Divergent Views and Verified Dispositions

- **DeepSeek HIGH, missing adapter signature/pattern — closed by plan evidence.** `04-01-PLAN.md:173–179` explicitly defines `alert.close(el)`, calls `component(ns, "Alert")` then `getOrCreateInstance(el).close()`, and confines removal to absence. Its tracer behavior at `:162–165` specifies the concrete element and call count. No signature is being assumed to exist; it is declared new in the artifact section. This existence-class claim is contradicted by the cited plan, so is not counted as an unresolved HIGH.
- **DeepSeek HIGH, audit fails on current legacy markup — closed by dependency/evidence.** `04-03-PLAN.md:6` depends on 04-01/02, while `04-01-PLAN.md:181–185` replaces the old hook. `04-03:130–131` deliberately asks for a red historical check. The fact current source has the old attribute is expected; H1 above separately captures the real scan-root/set ambiguity.
- **DeepSeek missing full integration tracer / normalized golden — already incorporated.** `04-01:135–140` forbids normalization/strip, and `:167–185,189–195` runs a raw Python comparison and then JS against that same rendered golden with the real adapters script. No new integration plan is needed.
- **Grok tracer could stub the adapter — already prohibited by the existing contract, clarified under A3.** `04-01:170–171` requires the real adapters script and a fake only for the external component. A fresh fixture/reset is still worth making explicit.
- **Fable console mock makes logging assertion vacuous — not a valid claim.** A mocked spy still records calls; asserting that it was never called detects core logging. The real useful change is A4's reuse of the already-existing listener-error helper plus explicit spy restoration. No production catch/log/recovery is justified.
- **Factory count versus lifecycle-event count — already explicit.** `04-03:114–116` specifically preserves the separate three-event statement. No blanket replacement is authorized.
- **Golden newline/class drift — already explicit acceptance.** Raw bytes/no strip/no normalization and the manual baseline-to-final attribute-only diff are required in `04-01:135–146,181–189,252–255`; the frame classes are read from the source and tested in task 3. A byte writer must not append an extra newline. This is execution detail within the existing requirement, not an untracked new deliverable.
- **Namespace absence, repeated calls, no-op/throw fakes and detached controls — already incorporated.** `04-02:98–116,137–155` covers these. Fake components are intentional; browser Bootstrap transition behavior remains in 04-03 acceptance. Repeated-click truths promise no additional Bootstrap animation safety.
- **Browser availability / docs-sync limits — already incorporated.** `04-03:188–194,216–230` requires actual browser observations or an explicit blocker. No unit/system-check result substitutes for browser evidence. A browser MCP assertion from a reviewer does not itself prove this session can complete the smoke.
- **Object-detail Bootstrap hooks — advisory future surface debt.** Confirmed under the extension package, outside ALRT-04's core scan root. Record for Phase 7 as appropriate; do not widen this phase's implementation or allowlist to disguise those hooks. This cross-phase observation is not a blocker for the bounded core alert change.

### Unresolved Counts

`CYCLE_SUMMARY: current_high=1 current_actionable=10`

The two refuted DeepSeek HIGHs remain verbatim in its raw section above with explicit source/plan dispositions here. H1 is corroborated and counted. All four reviewers supplied source citations; none carries an evidence discount marker. No suppressed unconfirmed HIGH remains. The ten non-HIGH items require executable plan incorporation or explicit ledger rejection/deferral before convergence. No plan-revision conflict has been recorded.

## Verification coverage

### Authority and limits

The deterministic `drift-guard authority --raw` seam returned **intel**, despite the project's `plan_review.source_grounding_authority` being `grep`. The generated `.planning/intel/API-SURFACE.md` says its map has zero entries; absence is unknown, not evidence of a missing symbol. Primary index-based declaration/signature resolution is therefore **UNCHECKABLE**. Direct repository reads and rg provided supplementary declaration and file-presence evidence, summarized below; signatures were not certified under grep/intel. `drift-guard severity` returned none/no block for VERIFIED, INFO/no block for UNCHECKABLE and MEDIUM/no block for AMBIGUOUS. No source-grounding hard blocker or missing local declaration was found.

The full auditable enumeration includes quoted plan lines for every occurrence in [source-grounding.json](.review-diagnostics/20261026T182508Z-gsd-review-wro4ux2o/source-grounding.json). New symbols and files from each plan's **Artifacts this phase produces** section were excluded from existence checking. GSD-generated execution summaries are also recorded as future generated context, not missing pre-existing source. Browser APIs, dependency APIs and CLI syntax are listed as UNCHECKABLE declarations; grounded existing use-sites and proven commands do not claim signature validation.

### Source reference ledger

| Symbol / path | Verdict | Evidence / exclusion |
|---|---|---|
| `.planning/PROJECT.md` | VERIFIED | .planning/PROJECT.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:81. |
| `.planning/ROADMAP.md` | VERIFIED | .planning/ROADMAP.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:82. |
| `.planning/STATE.md` | VERIFIED | .planning/STATE.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:83. |
| `.planning/phases/04-alert-dismiss-adapter/04-01-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. Plan 04-01-PLAN.md:265. |
| `.planning/phases/04-alert-dismiss-adapter/04-02-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. Plan 04-02-PLAN.md:204. |
| `.planning/phases/04-alert-dismiss-adapter/04-03-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. Plan 04-03-PLAN.md:266. |
| `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. Plan 04-03-PLAN.md:15. |
| `.planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md` | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:84. |
| `.planning/phases/04-alert-dismiss-adapter/04-PATTERNS.md` | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-PATTERNS.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:86. |
| `.planning/phases/04-alert-dismiss-adapter/04-RESEARCH.md` | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-RESEARCH.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:85. |
| `.planning/phases/04-alert-dismiss-adapter/04-SOURCE-AUDIT.md` | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-SOURCE-AUDIT.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:87. |
| `.planning/phases/04-alert-dismiss-adapter/04-VALIDATION.md` | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-VALIDATION.md:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:88. |
| `crud_views/snippets/language_selector.html` | VERIFIED | src/crud_views/templates/crud_views/snippets/language_selector.html:1; template name resolved under templates root. Plan 04-03-PLAN.md:129. |
| `crud_views/tags/actions_menu.html` | VERIFIED | src/crud_views/templates/crud_views/tags/actions_menu.html:1; template name resolved under templates root. Plan 04-03-PLAN.md:128. |
| `crud_views/tags/actions_menu_toggle.html` | VERIFIED | src/crud_views/templates/crud_views/tags/actions_menu_toggle.html:1; template name resolved under templates root. Plan 04-03-PLAN.md:129. |
| `docs/migrating-1.0.md` | VERIFIED | docs/migrating-1.0.md:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:13. |
| `docs/reference/javascript.md` | VERIFIED | docs/reference/javascript.md:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:8. |
| `docs/reference/messages.md` | VERIFIED | docs/reference/messages.md:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:9. |
| `docs/reference/theme.md` | VERIFIED | docs/reference/theme.md:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:10. |
| `examples/bootstrap5/manage.py` | VERIFIED | examples/bootstrap5/manage.py:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:177. |
| `examples/bootstrap5/project/templates/project/base.html` | VERIFIED | examples/bootstrap5/project/templates/project/base.html:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:177. |
| `examples/bootstrap5/test_docs_sync.py` | VERIFIED | examples/bootstrap5/test_docs_sync.py:1 exists; supplementary direct file evidence. Plan 04-03-PLAN.md:177. |
| `home/alex/.codex/gsd-core/templates/summary.md` | VERIFIED | /home/alex/.codex/gsd-core/templates/summary.md:1 exists (runtime reference). Plan 04-01-PLAN.md:77. |
| `home/alex/.codex/gsd-core/workflows/execute-plan.md` | VERIFIED | /home/alex/.codex/gsd-core/workflows/execute-plan.md:1 exists (runtime reference). Plan 04-01-PLAN.md:76. |
| `reference/javascript.md` | VERIFIED | docs/reference/javascript.md:1; link relative to docs/migrating-1.0.md. Plan 04-03-PLAN.md:58. |
| `reference/messages.md` | VERIFIED | docs/reference/messages.md:1; link relative to docs/migrating-1.0.md. Plan 04-03-PLAN.md:62. |
| `src/crud_views/lib/messages.py` | VERIFIED | src/crud_views/lib/messages.py:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:203. |
| `src/crud_views/static/crud_views/js/adapters.js` | VERIFIED | src/crud_views/static/crud_views/js/adapters.js:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:11. |
| `src/crud_views/static/crud_views/js/viewset.js` | VERIFIED | src/crud_views/static/crud_views/js/viewset.js:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:12. |
| `src/crud_views/templates/crud_views/tags/alert.html` | VERIFIED | src/crud_views/templates/crud_views/tags/alert.html:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:10. |
| `tests/js/adapters.test.js` | VERIFIED | tests/js/adapters.test.js:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:194. |
| `tests/js/helpers/load.js` | VERIFIED | tests/js/helpers/load.js:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:160. |
| `tests/js/helpers/setup.js` | VERIFIED | tests/js/helpers/setup.js:1 exists; supplementary direct file evidence. Plan 04-02-PLAN.md:133. |
| `tests/js/list.filter.test.js` | VERIFIED | tests/js/list.filter.test.js:1 exists; supplementary direct file evidence. Plan 04-02-PLAN.md:133. |
| `tests/js/viewset.test.js` | VERIFIED | tests/js/viewset.test.js:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:13. |
| `tests/test1/golden/alerts/dismissible.html` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. Plan 04-01-PLAN.md:9. |
| `tests/test1/test_alerts.py` | VERIFIED | tests/test1/test_alerts.py:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:8. |
| `tests/test1/test_form_frame.py` | VERIFIED | tests/test1/test_form_frame.py:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:133. |
| `tests/test1/test_messages.py` | VERIFIED | tests/test1/test_messages.py:1 exists; supplementary direct file evidence. Plan 04-01-PLAN.md:14. |
| `cv.bootstrapAdapters` | VERIFIED | src/crud_views/static/crud_views/js/adapters.js:12 Plan 04-01-PLAN.md:98. |
| `component` | VERIFIED | src/crud_views/static/crud_views/js/adapters.js:8 Plan 04-01-PLAN.md:41. |
| `resolve` | VERIFIED | src/crud_views/static/crud_views/js/adapters.js:7 Plan 04-01-PLAN.md:104. |
| `loadScript` | VERIFIED | tests/js/helpers/load.js:32 Plan 04-01-PLAN.md:106. |
| `fakeNamespace` | VERIFIED | tests/js/adapters.test.js:4 Plan 04-02-PLAN.md:77. |
| `_render` | VERIFIED | tests/test1/test_alerts.py:70 Plan 04-01-PLAN.md:108. |
| `_theme_templates` | VERIFIED | tests/test1/test_form_frame.py:58 Plan 04-01-PLAN.md:109. |
| `cv_alert` | VERIFIED | src/crud_views/templatetags/crud_views.py:396 Plan 04-01-PLAN.md:52. |
| `cv_js` | VERIFIED | src/crud_views/templatetags/crud_views.py:67 Plan 04-03-PLAN.md:119. |
| `CV_UPDATE_GOLDEN` | VERIFIED | tests/test1/test_action_menus_golden.py:4 Plan 04-01-PLAN.md:138. |
| `fileURLToPath` | VERIFIED | tests/js/helpers/load.js:3 Plan 04-01-PLAN.md:96. |
| `beforeAll` | VERIFIED | tests/js/viewset.test.js:27 Plan 04-01-PLAN.md:107. |
| `cv.adapters.alert` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:25. |
| `alert.close(el)` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:98. |
| `data-cv-alert-dismiss` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:25. |
| `DISMISSIBLE_ALERT_HTML` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:48. |
| `test_dismissible_alert_golden` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:36. |
| `test_dismissible_alert_preserves_frame_contract` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:94. |
| `test_documented_alert_frame_override` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-03-PLAN.md:54. |
| `test_stock_bootstrap_data_attributes_are_dropdown_only` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-03-PLAN.md:93. |
| `rendered alert dismissal tracer` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-01-PLAN.md:97. |
| `alert adapter ownership` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-02-PLAN.md:78. |
| `delegated alert ownership` | SKIPPED_NEW | Declared in Artifacts this phase produces; produced by planned tasks. Plan 04-02-PLAN.md:79. |
| `Element` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:176. |
| `Object.assign` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:105. |
| `Object.values` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. |
| `Object.hasOwn` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. |
| `closest` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:60. |
| `preventDefault` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. |
| `dispatchEvent` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-02-PLAN.md:151. |
| `getOrCreateInstance` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:163. |
| `isConnected` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-02-PLAN.md:107. |
| `vi.fn` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. |
| `vi.spyOn` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. |
| `read_bytes` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:53. |
| `--prefix` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:194. |
| `-q` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-01-PLAN.md:150. |
| `-n auto` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-03-PLAN.md:201. |
| `--strict` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-03-PLAN.md:143. |
| `--check` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. Plan 04-03-PLAN.md:209. |
| `alert_data` | UNCHECKABLE | External translated name; no declaration asserted Plan 04-01-PLAN.md:215. |
| `gettext` | VERIFIED | src/crud_views/templates/crud_views/tags/alert.html:5 Plan 04-01-PLAN.md:213. |

### Cross-artifact fact drift

- Phase status: deterministic result **lag**, STATE `Ready to plan` and ROADMAP `Planned`. A single nonterminal lifecycle step is not a drift finding.
- ROADMAP success criteria versus plan truths: baseline chronology, Bootstrap/missing-component/dynamic handling, core-only data-attribute audit, references, paired release/migration changes and example acceptance are represented consistently. H1 concerns execution precision, not a contradictory scope claim.
- Requirement IDs: ALRT-01 through ALRT-04 match roadmap/requirements and are assigned to tasks and frontmatter. No contradictory ID was found.
- CONTEXT terminology/decisions: D-01 through D-10 remain consistent with the plans: no new class keys; adapter-owned errors; fallback only on missing component; current-adapter semantic delegation; migrated copied-template guidance.
- Actual Bootstrap browser transitions, future test implementations, dependency-version compliance and execution outcomes are not verified by this review. Fable did not run suites; research's previous 50 Python/25 JS results were not represented as new cycle-1 test runs.
