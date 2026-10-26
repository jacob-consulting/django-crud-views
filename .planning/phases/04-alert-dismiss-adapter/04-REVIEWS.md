---
phase: "04"
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T19:42:43.725003+00:00
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

Cycle 3 reviewed final plans at `cff77e5`. All four configured instances returned real source-cited reviews and covered all three plans. No prompt trimming was configured; no lane was dropped or retried. Raw reports are preserved mechanically in [.review-diagnostics/20261026T194243Z-gsd-review-etpnrud2](.review-diagnostics/20261026T194243Z-gsd-review-etpnrud2/). Parent orchestrator owns the final report commit and planned-state transition. No product, plan or config file was changed by this review.

## Claude Review (fable-review)

# Cross-AI Plan Review — Phase 04, cycle 3 (verification pass at cff77e5)

Repo access: full. Every claim below was checked against the working tree at cff77e5 (plans on disk are identical to HEAD; only `.planning/config.json` is dirty). I could not run throwaway probe scripts (file writes were denied), so two mechanisms were verified by reading library source instead of executing them; both are marked.

## Prior-finding closure ledger

| ID | Closed? | Evidence |
|---|---|---|
| H1 | Yes | 04-03-01 pins the root to `src/crud_views/templates`, requires non-empty matches ⊆ ALLOWED, exempts the wrapper, and proves red with a temp-tree copy of the baseline template. Current live matches are exactly `tags/alert.html:5`, `tags/actions_menu_toggle.html:4-5`, `snippets/language_selector.html:6` (four lines, three files), matching the SOURCE-AUDIT claim. `tags/actions_menu.html` has no `data-bs-` line, so "do not require each allowed path to match" is necessary, not cosmetic. |
| A1 | Yes | 04-01-02 `files` now includes `tests/test1/test_messages.py`; the two legacy assertions are `test_messages.py:139` and `:169`. No golden under `tests/test1/golden/` contains `data-bs-dismiss` (grep confirmed), so no other fixture moves with the template. |
| A2 | Yes (rejected, recorded) | 04-01 "Execution ordering" + ledger. Not re-raised. |
| A3 | Yes | `globalThis.cv` lookup at call time works through `loadScript`'s Proxy (`tests/js/helpers/load.js:25-30`, `:32-36`), and vitest binds `global.window = global` (`node_modules/vitest/dist/chunks/index.DC7d2Pf8.js:274`), so `window.cv` descriptors and `globalThis.cv` are the same slot. Avoiding `vi.unstubAllGlobals()` is correct: `tests/js/helpers/setup.js:7-8` stubs `$`/`jQuery` once for the whole run. |
| A4 | Yes | `listenerErrors` exists at `tests/js/helpers/errors.js:5-18`, records `event.error ?? event.message`, calls `preventDefault`, removes the listener in `finally`. Already used by `tests/js/tooltip.test.js:89-236`, so vitest tolerates the prevented error events. |
| A5 | Yes | 04-02-02 names two controls in one frame, nested inner removal, outer/sibling survival. |
| A6 | Yes | 04-02-02 deletes `cv.adapters.alert` and expects one TypeError via `listenerErrors`, no fallback. |
| A7 | Yes | `docs/reference/settings.md:184-188` (hook list), `docs/migrating-1.0.md:309-310` (three-adapter enumeration), `:374-375` (missing-adapters checklist) all exist and are targeted. `settings.md` is in 04-03 `files_modified` and `read_first`. |
| A8 | Yes | Recipe retains `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}`; `test_alert_colours_follow_the_class_table` (`test_alerts.py:124-127`) is the existing precedent for the colour assertion. `_section`/`_headings` in `tests/test1/test_label_mode_docs.py:29-45` are fence-aware as claimed. |
| A9 | Yes | 04-03-02 instructs replacement, not dual hooks; `docs/migrating-1.0.md:345-346` (modal) is the existing wording precedent. |
| A10 | Yes | Verified by source read, not execution: `django/utils/translation/__init__.py:63-82` materialises `_trans.gettext` on first access, and `:95-96` routes `gettext()` through `_trans.gettext` at call time, so a `monkeypatch.setattr(_trans, "gettext", …)` reaches `{% translate 'Close' %}`. |
| C2-A1 | Yes | 04-03-01 adds the tmp_path allowed/forbidden-tree test, separate from the git-show probe. |
| C2-A2 | Yes | Both 04-02 tasks require a fresh `window.cv` per case before nested mutation. |
| C2-A3 | Yes | 04-02-02 names the unmarked-descendant-inside-`role=alert` click with no call/error/removal. |

All thirteen prior findings are closed in the executable task text, not only in the ledgers.

## 04-01

**Summary.** The plan sequences a baseline-only golden commit, a six-file tracer (template + both scripts + golden + JS tracer + message assertions), and a rendering-regression task. Every referenced seam exists as described: the frame at `src/crud_views/templates/crud_views/tags/alert.html:5`, the factory and shallow merge at `src/crud_views/static/crud_views/js/adapters.js:7-8,43`, the delegated-handler analog at `viewset.js:37-44`, `_render` at `tests/test1/test_alerts.py:70-71`, and the viewset suite's once-only `beforeAll` and last-position reload test at `tests/js/viewset.test.js:27-29,91-101`.

**Strengths.**
- Byte-exact golden is viable: `.pre-commit-config.yaml` runs only `ruff-check`/`ruff-format`, so no end-of-file or whitespace hook rewrites an `.html` golden, and the frame file already ends in `\n` (verified with `od`), so the raw render ends in a newline without one being appended.
- The JS tracer consuming the Python golden gives a real contract link; RED is genuine because the committed baseline still carries `data-bs-dismiss`, so the marker-based click cannot reach the adapter until the template changes.
- The default adapter's absent-only fallback is correct for every namespace shape the factory accepts: `resolve(undefined|null)` → `null`, `resolve({})` → `{}` with no `Alert` → `component` returns `null` (`adapters.js:7-8`).
- The example project satisfies D-10's precondition: Bootstrap bundle at `examples/bootstrap5/project/templates/project/base.html:19`, `{% cv_js %}` at `:37`, `{% cv_messages %}` at `:56`, and `cv_js` emits `adapters` before `viewset` (`src/crud_views/lib/settings.py:288-289`).

**Concerns.**
- LOW (optional wording): 04-01-01 says "fixed English locale" without naming the mechanism. The golden includes the translated `aria-label`, the German catalog translates `Close` (`src/crud_views/locale/de/LC_MESSAGES/django.po:103`), and `tests/test1/test_i18n.py:36` calls `translation.activate("de")` with a paired `deactivate()` at `:45`. Pairing exists, so this is hardening under `-n auto`, not an evidenced defect: state `translation.override("en")` explicitly, as 04-01-03 already does.
- LOW (optional wording): `CV_UPDATE_GOLDEN` is shared with `test_form_frame._check_golden` (`tests/test1/test_form_frame.py:50-55`) and the other golden suites. The plan says "scoped to this test only"; naming the `-k test_dismissible_alert_golden` selector would make that unambiguous for the executor.

**Suggestions.**
- Add the two phrases above to 04-01-01's action. No structural change.

**Risk.** LOW. All mechanisms traced to source; the only open items are wording.

## 04-02

**Summary.** The plan expands the tracer into a namespace/preassignment/error matrix in `adapters.test.js` and a dynamic-dispatch/ownership matrix in `viewset.test.js`, with product edits allowed only if a case exposes a defect. The fixtures and helpers it reuses exist: `fakeNamespace` at `tests/js/adapters.test.js:4-14`, the preassigned-identity precedent at `:133-140`, the lazy-function precedent at `:115-131`, `listenerErrors` at `tests/js/helpers/errors.js:5-18`.

**Strengths.**
- The isolation story is now mechanically sound: because vitest aliases `window` to `global` (`index.DC7d2Pf8.js:274`) and `loadScript` resolves `globalThis.cv` through a Proxy over `window` at call time (`load.js:25-30`), replacing `window.cv` with a fresh object per case is exactly what the listener observes on the next click.
- The missing-key TypeError case is observable as specified: jsdom reports listener exceptions as a window `error` event carrying `error`, which `errors.js:7-10` captures.
- The two edge-probe truths (idempotency, concurrency) are stated as ordinary DOM facts and explicitly disclaim new lifecycle machinery, which keeps D-04 intact.
- Note for the executor: `adapters.test.js:18` already does `vi.unstubAllGlobals(); delete window.cv` in `afterEach`. New factory cases in that file can rely on it; the fresh-object rule in the plan matters most in `viewset.test.js`, which has no such reset.

**Concerns.**
- None evidence-backed. The enumeration test at `adapters.test.js:20-24` lists three names and must gain `alert`; the plan says so.

**Suggestions.**
- Optional: in 04-02-01, say that `adapters.test.js`'s existing `afterEach` already clears `window.cv`, so the "save/restore descriptors" instruction is additive there, not a replacement.

**Risk.** LOW.

## 04-03

**Summary.** The plan updates four references plus the paired Breaking/migration text, adds an executable recipe test and a two-part data-attribute guard, and records browser acceptance. Every doc anchor it edits exists: the script table at `docs/reference/javascript.md:13-14`, adapter table `:30-38`, "builds all three" `:57`, events "All three" `:179` (correctly left alone), old markup and Bootstrap-only sentence at `docs/reference/messages.md:29-38`, the Alerts and dropdown sections at `docs/reference/theme.md:156-171,172-181`, the Unreleased Breaking list at `CHANGELOG.md:3-7`.

**Strengths.**
- The grep in ALRT-04 will be satisfied after the change: the remaining `data-bs-` lines in the core root are `tags/actions_menu_toggle.html:4-5` and `snippets/language_selector.html:6`, both named at `theme.md:179-181`.
- The recipe test uses the existing locmem override (`tests/test1/test_form_frame.py:58-68`), already proven to shadow the frame by `test_frame_is_overridable_on_its_own` (`test_alerts.py:110-113`).
- The human-check's no-Alert step (`cv.bootstrapAdapters({}).alert`) exercises the real fallback branch, not a jsdom fake.
- Nothing else in `docs/`, `examples/`, `tests/` or `src/` references the legacy attribute beyond the files the plans already touch (`messages.md:32,36`, `test_messages.py:139,169`, `alert.html:5`; `test_modal.py:309` asserts its absence and `migrating-1.0.md:345` is the modal precedent).

**Concerns.**
- LOW (optional wording): 04-03-02's only automated verify is `mkdocs build --strict`; the "same commit contains a Breaking entry and the migration example" acceptance has no command. A `git show --stat HEAD` naming both files is enough.
- LOW (scope note, not re-raised): `src/crud_views_object_detail/.../tabs-vertical/object_detail.html:10-11` and `accordion/group.html:5,15` carry `data-bs-*` outside the core root. The ledger defers this to Phase 7; the guard's root choice keeps it out correctly.

**Suggestions.**
- Add the `git show --stat` check to 04-03-02's acceptance. Everything else stands.

**Risk.** LOW–MEDIUM. The only residual risk is the browser acceptance itself, which the plan already refuses to infer from unit tests.

## Cross-plan assessment

- Dependency ordering is correct and forced by shared files (`viewset.test.js`, `test_alerts.py`); the baseline-commit-first chronology is enforceable from git history.
- No scope creep: no class keys, focus logic, auto-dismiss or events are introduced; `LATER-06` stays deferred (`.planning/REQUIREMENTS.md:84`).
- Security: escaping stays server-side in `alert_data` (`src/crud_views/lib/messages.py` conditional_escape paths) and the recipe test renders hostile input; the click handler selects only `[data-cv-alert-dismiss]` → nearest `[role="alert"]`.
- The plans achieve ALRT-01 through ALRT-04 as written in `.planning/REQUIREMENTS.md:54-57`.

**Overall risk: LOW.** All prior findings are closed in executable text. The three new items are optional wording hardening (explicit `translation.override("en")` in 04-01-01, the `-k` selector for the golden update, a `git show --stat` check in 04-03-02); none blocks execution.


---

## OpenCode Review (grok-review)

I'll verify the three plans against the current source and the prior review ledgers, starting with the files those tasks actually touch.
Plans and prior reviews are on disk. Next I’ll check the source those tasks cite and whether the earlier findings actually closed.
Prior findings are mapped. I’ll check the tests, docs, and helpers the plans treat as already true.
The error-spy contract may be unsatisfiable if jsdom logs listener exceptions. I’ll check that against the installed harness.
## 04-01

The baseline-then-tracer split matches the current frame and the only two legacy assertions. Prior findings A1, A3, and A10 are closed in the task text. A2 stays rejected. No new product gap.

**Strengths**
- The dismiss attribute is only on the dismissible branch at `src/crud_views/templates/crud_views/tags/alert.html:5`. A byte compare of `{% cv_alert %}` is the right ALRT-01 artifact: `cv_alert` renders that template directly (`src/crud_views/templatetags/crud_views.py:407-409`).
- A1 is closed. The only `data-bs-dismiss="alert"` assertions are `tests/test1/test_messages.py:139` and `:169`, and `04-01-PLAN.md:189-192` updates both in the tracer commit, with the combined pytest gate before commit.
- A3 matches the harness. `loadScript` binds `globalThis` to a Proxy that reads `window` at call time (`tests/js/helpers/load.js:25-36`). `04-01-PLAN.md:173-186` clears only `cv`/`bootstrap`, reloads real defaults, and calls `globalThis.cv.adapters.alert.close` inside the listener. That avoids both a stale `Object.assign` merge (`src/crud_views/static/crud_views/js/adapters.js:43`) and `vi.unstubAllGlobals()` wiping `$`/`jQuery` (`tests/js/helpers/setup.js:7-8`).
- A10 matches Django. `{% translate %}` calls `translation.gettext` (`django/templatetags/i18n.py:177`), which is `_trans.gettext` (`django/utils/translation/__init__.py:95-96`). `04-01-PLAN.md:220-226` patches that delegate and keeps the English golden unpatched. `LANGUAGE_CODE` is already `en-us` (`tests/test1/conftest.py:98`).
- The reload test is last (`tests/js/viewset.test.js:91-101`). New click cases are required to precede it, so they do not double-register the listener.

**Concerns**
- None. A2 remains an explicit rejection (`04-01-PLAN.md:116`, `:295`); no branch switch.

**Suggestions**
- None.

**Risk Assessment**
- LOW. The tracer commit stays green on the only suites that assert the old attribute, and the handler seam already exists at `src/crud_views/static/crud_views/js/viewset.js:37-44`.

## 04-02

This wave only proves the factory and the one listener from 04-01. A3–A6 and C2-A2/C2-A3 are executable requirements, not ledger notes. No new ownership hole.

**Strengths**
- Absence is a real branch of `component()` (`src/crud_views/static/crud_views/js/adapters.js:7-8`): a namespace with `Modal`/`Tooltip`/`Collapse` and no `Alert` is null, so removal stays inside `alert.close`. The existing enumeration test is the right place to add the fourth name (`tests/js/adapters.test.js:20-23`). Preassignment is already a whole-object merge (`tests/js/adapters.test.js:133-140` against `adapters.js:43`).
- A4 is closed. `listenerErrors` records `event.error` and removes its listener in `finally` (`tests/js/helpers/errors.js:5-18`). `04-02-PLAN.md:164-170` reuses it for throws and ignored targets. In this jsdom, `preventDefault` on that error event stops the extra `console.error` report, so a no-call assertion is not vacuous.
- A5 and A6 are named: two controls, inner removal with outer/sibling survival (`04-02-PLAN.md:158`), and `delete` of `cv.adapters.alert` as a surfaced `TypeError` with no repair (`04-02-PLAN.md:170`).
- C2-A2 is closed. `04-02-PLAN.md:118-121` and `:175` create a case-owned `cv`/`adapters` object before nested mutation. Restoring a descriptor cannot undo `delete` on a shared map, and `$`/`jQuery` stay untouched.
- C2-A3 is closed. `04-02-PLAN.md:158-160` clicks an unmarked descendant inside `role="alert"` and requires an empty `listenerErrors` array, zero adapter calls, and a still-connected frame.

**Concerns**
- None. Repeated close and detached-subtree cases stay ordinary DOM behavior. No new animation or scheduling guarantee is added.

**Suggestions**
- None.

**Risk Assessment**
- LOW. Failures here are test failures against the existing factory, not a second close path.

## 04-03

The audit root, recipe, and paired migration match the tree and the docs that would otherwise stay stale. H1, A7–A9, and C2-A1 are closed. Browser acceptance is still an explicit observation, not a unit-test stand-in.

**Strengths**
- H1 matches the tree. Under `src/crud_views/templates`, `data-bs-` is only `tags/alert.html:5`, `tags/actions_menu_toggle.html:4-5`, and `snippets/language_selector.html:6`. `tags/actions_menu.html` has no `data-bs-` attribute. `theme.md:179-181` names those three paths. `04-03-PLAN.md:139-145` scans only that root, requires a nonempty subset of those relative paths, and does not use the all-app glob at `tests/test1/test_alerts.py:133`. Object-detail hits stay outside that root.
- C2-A1 is closed. `04-03-PLAN.md:147-152` adds a lasting `tmp_path` test: an allowed toggle file passes, then a forbidden `crud_views/tags/alert.html` raises `AssertionError` naming that relative path. The `git show` red check stays one-time and does not become a CI git dependency. `git show <baseline>:…/alert.html` still has the old attribute, because the baseline commit does not edit the template.
- A7 targets still exist: three-adapter list at `docs/migrating-1.0.md:309-310`, missing-adapters checklist at `:374`, delegated-hook list at `docs/reference/settings.md:184-189`. `04-03-PLAN.md:122-123` and `:192-194` update them. The factory sentence to change is `docs/reference/javascript.md:57`; the lifecycle sentence to leave alone is `:179`.
- A8 is the live colour seam. The stock frame already uses `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}` (`alert.html:1-2`), and `tests/test1/test_alerts.py:124-127` proves that key reaches the class list. `04-03-PLAN.md:129-137` keeps both in the extracted recipe and renders it through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`).
- A9 is closed. `04-03-PLAN.md:190-192` forbids keeping both dismiss attributes on one control and keeps the old-hook-only Bootstrap path. `{% cv_js %}` already emits `adapters.js` then `viewset.js` (`src/crud_views/lib/settings.py:288-289`), which is the order the migration must name. Example flash messages go through `{% cv_messages %}` (`examples/bootstrap5/project/templates/project/base.html:37,56`).

**Concerns**
- None. Tool-version drift and the example browser close stay required evidence in `04-03-PLAN.md` task 04-03-03. They are not inferred passes.

**Suggestions**
- None.

**Risk Assessment**
- LOW. The lasting allowlist test can fail closed. The only non-automated acceptance is the browser procedure, and the plan forbids marking D-10 verified without it.

## Closure

H1, A1, A3–A10, and C2-A1–C2-A3 are closed against current source. A2 stays rejected. No new materially actionable issue. Overall risk is LOW.


---

## OpenCode Review (gemini-review)

## 04-01

### 1. Summary
Plan `04-01` sequences the standalone before-change golden commit (`ALRT-01`), the end-to-end dismissal tracer across the template, adapter factory, and delegated click listener (`ALRT-02`, `ALRT-03`), and the server-side alert/message rendering regressions across three well-isolated tasks. All Round 1 items assigned to `04-01` (`A1`, `A2`, `A3`, `A10`, and the byte-exact golden convention) remain closed in `cff77e5`: Task `04-01-02` updates both `tests/test1/test_messages.py` assertions (`lines 139, 169`) in the same commit as `src/crud_views/templates/crud_views/tags/alert.html:5` so the tracer commit stays green, uses `globalThis.cv.adapters.alert.close(frame)` at call time with scoped descriptor save/restore of `window.cv` and `window.bootstrap`, and Task `04-01-03` patches `django.utils.translation._trans.gettext` via `monkeypatch.context()` for the `{% translate 'Close' %}` render-time sentinel check.

### 2. Strengths
- **Byte-exact baseline golden before product edits (`src/crud_views/templates/crud_views/tags/alert.html:1-6`, `tests/test1/test_alerts.py:70-71`):** Task `04-01-01` (`04-01-PLAN.md:136-146`) writes `markup.encode("utf-8")` without appending a newline and compares via `read_bytes()` under a fixed English locale (`translation.override("en")`), avoiding the whitespace normalization in `tests/test1/test_form_frame.py:44-55` (`_norm()`) and recording `ALRT-01` (`D-07`) as a standalone commit before `alert.html:5` is modified.
- **Green tracer commit covering both `test_alerts.py` and `test_messages.py` (`tests/test1/test_messages.py:139,169`) [closes A1]:** Updating the two legacy `assert 'data-bs-dismiss="alert"' in html` checks (`test_cv_messages_renders_a_dismissible_alert` at `tests/test1/test_messages.py:139` and `test_create_message_renders_as_an_alert` at `tests/test1/test_messages.py:169`) inside Task `04-01-02` (`04-01-PLAN.md:162,190-193`) and running `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` before committing keeps every commit in the series green.
- **Scoped JS global cleanup and call-time `globalThis.cv` lookup (`src/crud_views/static/crud_views/js/adapters.js:43`, `tests/js/helpers/load.js:25-36`, `tests/js/helpers/setup.js:7-8`, `tests/js/viewset.test.js:27-33,91-101`) [closes A3]:** Snapshotting and clearing only `window.cv` and `window.bootstrap` descriptors before loading fresh defaults in `tests/js/viewset.test.js` (`04-01-PLAN.md:173-178,185-186`) ensures `adapters.js:43` (`Object.assign(cv.bootstrapAdapters(...), cv.adapters || {})`) does not retain a previous test's custom fake while preserving the module-once `$` / `jQuery` globals installed in `tests/js/helpers/setup.js:7-8`. Placing the new cases before the reload test at `tests/js/viewset.test.js:91-101` prevents duplicate document listeners.
- **Verified Django template translation seam (`src/crud_views/templates/crud_views/tags/alert.html:5`) [closes A10]:** Task `04-01-03` (`04-01-PLAN.md:223-227`) patches `django.utils.translation._trans.gettext` inside `monkeypatch.context()` under `translation.override("en")`, intercepting `"Close"` when `{% translate 'Close' %}` renders while delegating all other message IDs and restoring state on exit.

### 3. Concerns
- None. All Round 1 items for `04-01` (`A1`, `A2`, `A3`, `A10`) are closed and no new issues exist.

### 4. Suggestions
- None; the plan is ready for execution as written.

### 5. Risk Assessment
**Risk Level: LOW**
The standalone baseline commit, shared golden fixture between pytest and Vitest, atomic green tracer commit, and scoped JS descriptor cleanup eliminate execution risk.

---

## 04-02

### 1. Summary
Plan `04-02` expands the JavaScript unit and DOM regression suites in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` to cover lazy namespace resolution, preassigned and post-load custom adapter swaps, dynamic and modal-injected alerts, multiple dismiss controls, nested semantic alert frames, unmarked alert-body clicks, missing adapter keys, and custom/component error surfacing (`ALRT-02`, `ALRT-03`, `D-03`, `D-04`, `D-08`, `D-10`). All Round 1 items (`A3`, `A4`, `A5`, `A6`) and Round 2 items (`C2-A2`, `C2-A3`) are closed in `cff77e5`: each test case creates a fresh `window.cv` object before mutating or deleting nested adapter keys (`C2-A2`), and Task `04-02-02` explicitly tests clicking an unmarked body element inside a `role="alert"` frame (`C2-A3`).

### 2. Strengths
- **Case-owned `window.cv` and adapter maps before nested mutation (`src/crud_views/static/crud_views/js/adapters.js:43`, `tests/js/viewset.test.js:27-33`, `tests/js/helpers/setup.js:7-8`) [closes A3, C2-A2]:** Tasks `04-02-01` (`04-02-PLAN.md:118-121`) and `04-02-02` (`04-02-PLAN.md:83,172-175`) save the original `cv` and `bootstrap` property descriptors, assign a fresh `window.cv` object and initialize its adapters for each case before replacing or deleting `cv.adapters.alert`, and restore the descriptors in `finally`. Because mutations happen only on the case-owned object, restoring the descriptor never leaks an in-place `delete cv.adapters.alert` into subsequent tests while keeping `setup.js:7-8`'s shared `$`/`jQuery` globals intact.
- **Unmarked alert-body click and multi-control/nested-role coverage (`src/crud_views/static/crud_views/js/viewset.js:37-44`, `tests/js/viewset.test.js:59-79`) [closes A5, C2-A3]:** Task `04-02-02` (`04-02-PLAN.md:82,144-145,155-161,180-182`) tests clicking an unmarked descendant inside a `role="alert"` frame—asserting `listenerErrors` returns `[]`, zero adapter calls occur, and the frame stays connected—as well as two `[data-cv-alert-dismiss]` controls in one frame and nested `role="alert"` frames where inner removal leaves outer and sibling frames connected (`isConnected`).
- **Reuse of `listenerErrors` and clean console spy lifecycle (`tests/js/helpers/errors.js:5-18`, `tests/js/helpers/setup.js:11-12`) [closes A4, A6]:** Task `04-02-02` (`04-02-PLAN.md:164-171`) reuses `listenerErrors(fn)` from `tests/js/helpers/errors.js:5-18` to capture thrown custom adapter errors and the `TypeError` when `cv.adapters.alert` is deleted, while spying on `console.error` and `console.warn`, asserting neither is called by core, and restoring both spies in `finally`.
- **Strict absent-only fallback and idempotency/concurrency edge verification (`src/crud_views/static/crud_views/js/adapters.js:7-8,12-43`):** Tasks `04-02-01` and `04-02-02` (`04-02-PLAN.md:26-27,100-106,115-118,175-177`) verify that `el.remove()` runs only when `component(ns, "Alert")` is absent, while present no-op or throwing `Alert` instances and repeated/detached clicks behave according to standard DOM semantics without extra lifecycle state.

### 3. Concerns
- None. All Round 1 (`A3`–`A6`) and Round 2 (`C2-A2`, `C2-A3`) items are closed and no new issues exist.

### 4. Suggestions
- None; the test matrix and isolation mechanics are complete.

### 5. Risk Assessment
**Risk Level: LOW**
Per-case `window.cv` object creation prior to nested key mutation (`C2-A2`) and explicit unmarked in-alert click verification (`C2-A3`) close the remaining test-isolation and selector-precision edge cases.

---

## 04-03

### 1. Summary
Plan `04-03` updates the four reference documents (`javascript.md`, `messages.md`, `theme.md`, `settings.md`), adds executable tests in `tests/test1/test_alerts.py` for the documented custom alert frame override recipe and the core `data-bs-*` template allowlist guard (both positive/allowlist and permanent `tmp_path` negative rejection), pairs the `CHANGELOG.md` `### Breaking` entry with the `docs/migrating-1.0.md` before/after guide and checklist updates, and runs the full project quality gates and example browser acceptance check (`ALRT-01` through `ALRT-04`, `D-01` through `D-10`). All Round 1 (`H1`, `A7`, `A8`, `A9`) and Round 2 (`C2-A1`) items are closed in `cff77e5`.

### 2. Strengths
- **Core-only `data-bs-*` allowlist guard plus permanent `tmp_path` negative regression (`tests/test1/test_alerts.py:130-143`, `docs/reference/theme.md:179-181`, `src/crud_views/templates/crud_views/tags/actions_menu.html:1-9`) [closes H1, C2-A1]:** Task `04-03-01` (`04-03-PLAN.md:94-97,139-160,166-168`) scopes `_assert_core_bootstrap_data_attributes(root)` to `src/crud_views/templates`, requires `matches` to be nonempty and a subset of `ALLOWED` (`crud_views/tags/actions_menu.html`, `crud_views/tags/actions_menu_toggle.html`, `crud_views/snippets/language_selector.html`), proves one-time historical red via `git show` on the baseline `alert.html` in a temporary copy, and adds `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` using `tmp_path` to permanently verify that an allowed tree passes and adding a forbidden `crud_views/tags/alert.html` with `data-bs-` raises `AssertionError` naming `crud_views/tags/alert.html` without any Git dependency.
- **Executable custom alert frame recipe preserving the colour seam (`docs/reference/theme.md:156-170`, `tests/test1/test_alerts.py:110-128`, `tests/test1/test_label_mode_docs.py:29-45`) [closes A8]:** Task `04-03-01` (`04-03-PLAN.md:127-137`) includes `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}` in the `Custom alert frame` recipe in `docs/reference/theme.md`, extracts the fenced code block using the fence-aware `_section` pattern from `tests/test1/test_label_mode_docs.py:29-45`, and renders it through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`) with an overridden `alert:*` colour key, dismissible/non-dismissible states, and hostile `extra_tags`/content.
- **Complete alignment of `settings.md` and `migrating-1.0.md` checklists and single-hook migration rule (`docs/reference/settings.md:184-189`, `docs/migrating-1.0.md:199-200,306,309-310,345-347,374-375,385-410`) [closes A7, A9]:** Task `04-03-01` (`04-03-PLAN.md:122-123`) adds alert dismissal in `viewset.js` and `data-cv-alert-dismiss` to `docs/reference/settings.md:184-189`. Task `04-03-02` (`04-03-PLAN.md:185-196`) updates `docs/migrating-1.0.md`'s adapter enumeration (`lines 309-310`), missing-`adapters.js` checklist item (`lines 374-375`), and alert/markup/override bullets, and warns users to replace `data-bs-dismiss="alert"` rather than keeping both attributes.
- **Honest quality gates and browser smoke verification (`examples/bootstrap5/project/templates/project/base.html:19-38`, `04-03-PLAN.md:216-265`):** Task `04-03-03` runs all automated gates (`pytest`, `npm test`, `mkdocs build --strict`, `ruff check`, `ruff format --check`, `examples/bootstrap5/manage.py check`, `test_docs_sync.py`), discloses tool-version drift without modifying manifests, and requires real browser observations (or an explicit recorded blocker) for the example flash-message transition check.

### 3. Concerns
- None. All Round 1 (`H1`, `A7`–`A9`) and Round 2 (`C2-A1`) items are closed and no new issues exist.

### 4. Suggestions
- None; all tasks and verification steps are complete and grounded in the source tree.

### 5. Risk Assessment
**Risk Level: LOW**
The permanent `tmp_path` negative regression (`C2-A1`) alongside the core-only subset check (`H1`), executable recipe test (`A8`), and cross-document checklist updates (`A7`, `A9`) make `04-03` low-risk and ready for execution.

---

## Cross-Plan Convergence Verification (Cycle 3 — `cff77e5`)

| Item | Severity | Plan | Status in `cff77e5` | Verification Evidence |
|---|---|---|---|---|
| **H1** | HIGH | `04-03` | **Closed** | `04-03-PLAN.md:94-97,139-145,154-160,310` scans strictly `src/crud_views/templates`, asserts nonempty matches `<= ALLOWED`, and proves red via `git show` in a temporary directory. |
| **A1** | MEDIUM | `04-01` | **Closed** | `04-01-PLAN.md:14,162,190-193,202,286` updates `tests/test1/test_messages.py:139,169` in `04-01-02` and runs both Python suites before commit. |
| **A2** | MEDIUM | `04-01` | **Closed (Rejected)** | `04-01-PLAN.md:116-118,295` explicitly retains `introduce-gsd` under orchestrator branch management. |
| **A3** | MEDIUM | `04-01`, `04-02` | **Closed** | `04-01-PLAN.md:173-178,185-186,287` and `04-02-PLAN.md:118-121,163-164,172-175,234` use `globalThis.cv.adapters.alert.close(frame)` and scoped `cv`/`bootstrap` cleanup. |
| **A4** | MEDIUM | `04-02` | **Closed** | `04-02-PLAN.md:81,87,164-168,235` reuses `listenerErrors` from `tests/js/helpers/errors.js:5-18` and restores `console.error`/`warn` spies in `finally`. |
| **A5** | MEDIUM | `04-02` | **Closed** | `04-02-PLAN.md:82,145,155-158,181-182,236` tests two controls in one frame and outer/sibling survival on inner nested alert removal. |
| **A6** | LOW | `04-02` | **Closed** | `04-02-PLAN.md:82,147,169-171,182-183,237` deletes `cv.adapters.alert` and asserts `TypeError` via `listenerErrors` with no fallback or logging. |
| **A7** | MEDIUM | `04-03` | **Closed** | `04-03-PLAN.md:11,122-123,192-194,201,311` updates `docs/reference/settings.md:184-189` and `docs/migrating-1.0.md:199-200,309-310,374-375`. |
| **A8** | LOW | `04-03` | **Closed** | `04-03-PLAN.md:127-137,164-166,312` retains `{% load crud_views i18n %}` and `{% cv_button_class "alert" alert.level %}` in the `theme.md` recipe and tests an overridden colour key. |
| **A9** | MEDIUM | `04-03` | **Closed** | `04-03-PLAN.md:190-192,201-202,313` instructs replacing `data-bs-dismiss="alert"` with only `data-cv-alert-dismiss`. |
| **A10** | LOW | `04-01` | **Closed** | `04-01-PLAN.md:223-227,288` patches `django.utils.translation._trans.gettext` in `monkeypatch.context()` for `"Close"` under `translation.override("en")`. |
| **C2-A1** | LOW | `04-03` | **Closed** | `04-03-PLAN.md:94-97,147-152,167-168,329` adds permanent `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` using `tmp_path`. |
| **C2-A2** | LOW | `04-02` | **Closed** | `04-02-PLAN.md:83,118-121,172-175,253` creates a fresh case-owned `window.cv` and adapter map before mutating/deleting nested keys and restores descriptors in `finally`. |
| **C2-A3** | LOW | `04-02` | **Closed** | `04-02-PLAN.md:82,144,158-160,180-181,254` clicks an unmarked body element inside `role="alert"` and asserts no error, no adapter call, and retained frame connection. |

**Overall Risk Assessment: LOW.** All Round 1 (`H1`, `A1`–`A10`) and Round 2 (`C2-A1`–`C2-A3`) items are verified closed, and no new actionable issues exist. The phase plans have converged and are ready for execution.


---

## OpenCode Review (deepseek-review)

I'll review the three implementation plans for the alert dismiss adapter phase. Let me start by examining the current repository structure and the referenced files to verify claims.


Now let me check some key source files to understand the current state and verify plan claims:


Now let me check if there are any existing alert tests:




Let me check for existing golden tests:


Now let me check the JS test files to understand the existing patterns:




Let me check if there are any existing review files:




Now I'll examine the current alert template to see the exact current state and understand what data attributes it has:






Now let me check the current git status to understand the baseline:


Now let me look at a few key files to understand the project structure better:








Based on my examination of the plans and codebase, I'll now provide a comprehensive review of the three implementation plans.

# Cross-AI Plan Review for Alert Dismiss Adapter Phase

## 04-01

**Summary**: This plan establishes a baseline golden of current alert markup, then implements the core alert dismiss adapter feature with both Python and JavaScript components. It correctly addresses ALRT-01 through ALRT-03 with a clear three-task structure.

**Strengths**:
- Clear baseline-first approach (task 04-01-01) ensures ALRT-01 is satisfied via commit history
- Well-defined tracer task (04-01-02) that covers both Python template changes and JavaScript adapter/viewset implementation
- Good attention to preservation of existing contracts (frame classes, translation, accessibility) in task 04-01-03
- Correct identification of key files: `src/crud_views/templates/crud_views/tags/alert.html:5` (current `data-bs-dismiss="alert"`) needs to change to `data-cv-alert-dismiss`
- Good understanding of existing adapter patterns in `src/crud_views/static/crud_views/js/adapters.js:43` with `Object.assign(cv.bootstrapAdapters(...), cv.adapters || {})`

**Concerns**:
- **MEDIUM**: Task 04-01-02's verification uses `npm --prefix . test -- tests/js/adapters.test.js tests/js/viewset.test.js` but doesn't verify the golden file exists before JavaScript tests run (circular dependency risk)
- **LOW**: The golden comparison uses byte-level comparison without normalization, which may cause issues with whitespace differences across environments
- **LOW**: Task doesn't specify how to handle the case where `DISMISSIBLE_ALERT_HTML` golden doesn't exist yet for first run of JS tests

**Suggestions**:
1. Add a pre-check in task 04-01-02 to ensure the golden file exists before attempting to load it in JavaScript tests
2. Consider adding a fallback for JS tests if golden file missing (e.g., inline test markup)
3. Clarify error handling in adapter: what happens if `globalThis.cv.adapters.alert` doesn't exist?

**Risk Assessment**: **MEDIUM** - The plan is generally sound but has execution dependency issues and potential edge cases with the golden-first approach.

## 04-02

**Summary**: This plan expands test coverage for namespace variations, error handling, and dynamic content scenarios. It builds on 04-01 to prove robustness of the alert adapter implementation.

**Strengths**:
- Comprehensive test matrix covering namespace variations (null, object, function, late global)
- Good attention to error handling per D-03 (custom adapter errors surface without core recovery)
- Important edge cases covered: nested alerts, multiple controls, missing adapter key, unmarked body clicks
- Correct reuse of existing test helpers (`listenerErrors`, `fakeNamespace`)
- Good focus on preserving existing patterns while expanding coverage

**Concerns**:
- **HIGH**: Task 04-02-01 modifies `src/crud_views/static/crud_views/js/adapters.js` (already modified in 04-01-02), creating potential merge conflicts if tasks run out of order
- **MEDIUM**: The plan mentions restoring window property descriptors but doesn't specify how to handle cases where original properties were enumerable/configurable differently
- **LOW**: No specific mention of testing Bootstrap's `Alert.getOrCreateInstance(el).close()` throwing during component failure

**Suggestions**:
1. Make 04-02 tasks strictly additive to adapters.js (only add new tests, no modifications to production code already changed in 04-01)
2. Add explicit test for `Alert.getOrCreateInstance(el).close()` throwing to ensure error surfaces per D-03
3. Consider adding a test for namespace with `Alert` component that has `getOrCreateInstance` but no `close` method

**Risk Assessment**: **MEDIUM** - Good test coverage but potential for conflicts with 04-01 and some edge cases not explicitly covered.

## 04-03

**Summary**: This plan handles documentation updates, migration guidance, and final verification. It completes the phase with proper references and acceptance criteria.

**Strengths**:
- Comprehensive documentation coverage across JavaScript, messages, theme, and migration guides
- Good integration of frame override recipe that preserves existing colour seam (`{% cv_button_class "alert" alert.level %}`)
- Correct data attribute audit focusing only on `src/crud_views/templates` per ALRT-04
- Excellent browser acceptance procedure that actually tests real interactions
- Good handling of tool version drift disclosure

**Concerns**:
- **HIGH**: The data attribute audit in task 04-03-01 could fail if other templates have `data-bs-*` attributes not in the allowlist
- **MEDIUM**: Browser acceptance test depends on example project running and Bootstrap CDN availability
- **LOW**: Migration guidance could be confusing about when to upgrade copied templates

**Suggestions**:
1. Double-check ALL `data-bs-*` attributes in the codebase before implementing the audit
2. Add a fallback plan if browser tests can't run (e.g., manual verification requirement)
3. Make migration guidance clearer about trade-offs of upgrading vs keeping legacy markup

**Risk Assessment**: **MEDIUM** - Documentation and verification are thorough, but audit and browser tests have external dependencies.

## Overall Risk Assessment: **MEDIUM**

The plans are well-structured and address the phase requirements comprehensively. Key risks include:
1. Dependency ordering between tasks (golden files, JS tests, production code modifications)
2. External dependencies (Bootstrap CDN, example project availability for browser tests)
3. Potential for missed edge cases in error handling

The plans demonstrate good understanding of the codebase and phase requirements. With careful execution addressing the concerns above, this phase should successfully implement the alert dismiss adapter feature.


---
## Consensus Summary

### Verified closure of prior findings

Gemini and Grok explicitly verify every earlier finding closed and raise no new concerns or suggestions. Fable verifies the same closures and labels its remaining notes optional wording, with no evidenced defect. Independent source checks below refute DeepSeek's two new HIGH claims rather than treating them as unresolved or silently suppressing them. All fourteen earlier items are covered in executable tasks or A2's explicit rejection.

| Finding group | Verified executable contract in cff77e5 |
|---|---|
| H1 | 04-03-01 scans only src/crud_views/templates; nonempty matches must be a subset of the exact three-path allowlist; the wrapper need not match. Historical red uses baseline alert.html in a temporary tree without changing checkout. |
| A1–A3 | 04-01 keeps baseline chronology, includes both legacy message assertion updates in the tracer commit, explicitly preserves introduce-gsd and uses scoped fresh real adapters with globalThis.cv lookup. |
| A4–A6 | 04-02 reuses listenerErrors, restores console spies, covers multiple controls/nested survivors and surfaces missing-adapter TypeError without fallback/logging/repair. |
| A7–A10 | 04-03 updates stale settings/migration lists, preserves the tested colour seam and single dismiss hook; 04-01 names the actual locally restored template translation delegate. |
| C2-A1 | 04-03:147–152 permanently tests an allowed tmp_path tree, then adds a forbidden alert file and requires AssertionError naming its relative path; no Git dependency enters the lasting test. |
| C2-A2 | 04-02:118–121,172–175 creates a case-owned cv/adapters object before nested mutation, then restores untouched original property descriptors; no shared jQuery unstubbing. |
| C2-A3 | 04-02:144,158–160 clicks an unmarked body inside role=alert and requires no error, call or removal. |

Prior raw reviews are preserved in [.review-history/04-REVIEWS-cycle1.md](.review-history/04-REVIEWS-cycle1.md) and [.review-history/04-REVIEWS-cycle2.md](.review-history/04-REVIEWS-cycle2.md). Their counts are historical. Current executable tasks and explicit review dispositions control execution.

### Current unresolved findings

None.

`CYCLE_SUMMARY: current_high=0 current_actionable=0`

The fixed plan-revision conflict slot is preserved unchanged and contains zero open conflicts. All four reviewers supplied source citations, so no evidence-quality discount marker was needed. No HIGH remains partially resolved. No actionable MEDIUM/LOW finding remains solely in this review.

### Grounded dispositions of DeepSeek's new claims

- **HIGH: overlapping adapters.js edits might conflict if tasks run out of order — refuted by declared dependencies.** 04-02 has wave2 and depends_on04-01 in frontmatter, and its action permits only bounded corrections if a regression exposes a defect. 04-03 depends on both. Reversing that order would violate the plan. Nothing runs these production edits concurrently, so this is not an unresolved architecture risk.
- **HIGH: audit could fail on forbidden attributes — intended acceptance behavior, not a defect.** 04-03 explicitly scopes the root and allowlist and permanently proves rejection of forbidden paths. Current rg evidence under the core root is the legacy alert plus the two allowed dropdown files; the tracer removes the legacy hook. Rejecting a later unexpected data-bs attribute is the guard's required purpose. The source and task contract refute the supposed missing audit coverage.
- **Golden availability/circularity — already resolved by chronology and verification.** 04-01-01 creates and commits the exact baseline before task2. 04-01-02 runs the Python golden comparison before JavaScript consumes the same file. A missing file makes that comparison fail. Inline fallback markup would undermine the required rendered-fixture bridge and is not authorized.
- **Whitespace across environments — chosen existing contract.** D-07 and04-01 deliberately require raw bytes under a fixed English render and an attribute-only diff, not normalization. No evidence of a new nondeterministic value was cited.
- **Descriptor flags — already preserved by exact descriptor restoration.** 04-01:173–177 saves/restores the original descriptors or deletes originally absent properties. 04-02 now performs mutations on fresh case-owned objects. Enumerable/configurable flags are part of those descriptors, not a missing separate contract.
- **Present component errors/missing adapter — already specified.** 04-02:103,115–116 covers throwing getOrCreateInstance and close; :147,169–171 covers a missing alert adapter key with surfaced TypeError and retained frame. A malformed third-party component's missing method follows the same uncaught component-owned failure path; no recovery or lifecycle manager is warranted.
- **Browser/CDN blocker and copied-template guidance — already explicit.** 04-03:185–196 recommends adopting the new hook even with Bootstrap and distinguishes the legacy-old-hook-only path. :250–265 gives reproducible real-browser steps and an explicit unverified blocker branch. Unit fakes never count as Bootstrap transition evidence.

### Other final-cycle notes

Fable's optional wording is already bounded by executable acceptance: 04-01-01 requires a fixed English locale, a golden update scoped to that test only and raw-byte comparison; 04-03-02 requires the paired Breaking/migration change in one commit. Explicit spelling of translation.override("en"), a -k selector or git show --stat is an implementation/verification choice within those existing tasks, not an unplanned behavior. Its note about adapters.test.js's existing afterEach clarifies existing cleanup; C2-A2 already requires fresh case-owned objects and preserved shared jQuery state. No additional plan revision is required for these notes.

Fable could not run throwaway probes and explicitly verified the translation/error mechanisms by source. Grok verified the installed harness's prevented-error/no-console behavior. This review does not claim a new full pytest/Vitest/docs run. Fable's prose says thirteen prior findings while its table lists all fourteen; that counting typo does not omit a task or change the verified closure set.


## Verification coverage

### Source authority and limits

The deterministic authority seam again returned intel despite the project's explicit grep preference. The generated API map remains empty, so index-based declaration resolution is **UNCHECKABLE**, not MISSING. Direct repository reads/rg supplement file/declaration existence; unsupported signatures, browser/dependency APIs and dynamic Django translation access remain explicitly UNCHECKABLE. No local declaration was found missing. New hooks, helpers, tests, temporary fixture paths and generated execution summaries are excluded as declared phase products.

The refreshed [source-grounding.json](.review-diagnostics/20261026T194243Z-gsd-review-etpnrud2/source-grounding.json) records 89 reference rows with every current plan-line quote, evidence, exclusion and limit. Severity seams return no block for VERIFIED and INFO/no block for UNCHECKABLE. New code, future execution results, real browser transitions and manifest-version compliance are not certified by plan review.

### Uncheckable and excluded references

| Reference | Verdict | Limit / exclusion |
|---|---|---|
| `.planning/phases/04-alert-dismiss-adapter/04-01-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-01-PLAN.md:299. |
| `.planning/phases/04-alert-dismiss-adapter/04-02-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-02-PLAN.md:263. |
| `.planning/phases/04-alert-dismiss-adapter/04-03-SUMMARY.md` | SKIPPED_NEW | Declared new phase artifact or generated execution SUMMARY context. 04-03-PLAN.md:338. |
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
| `dispatchEvent` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-02-PLAN.md:171. |
| `getOrCreateInstance` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:166. |
| `isConnected` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-02-PLAN.md:110. |
| `read_bytes` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:53. |
| `--prefix` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:204. |
| `-q` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-01-PLAN.md:153. |
| `-n auto` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:238. |
| `--strict` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:173. |
| `--check` | UNCHECKABLE | External platform/library/CLI declaration not defined in repo; use-sites inspected, signatures not asserted by grep/intel. 04-03-PLAN.md:246. |
| `alert_data` | UNCHECKABLE | External translated name; no declaration asserted 04-01-PLAN.md:229. |
| `crud_views/tags/alert.html` | UNCHECKABLE | Runtime/external citation fragment; no source absence claimed. 04-01-PLAN.md:10. |
| `_assert_core_bootstrap_data_attributes` | SKIPPED_NEW | Declared private test helper in 04-03 Artifacts section; created by planned task. 04-03-PLAN.md:95. |
| `monkeypatch.context` | UNCHECKABLE | External pytest API; use local installed API, no repo declaration/signature certified. 04-01-PLAN.md:223. |
| `django.utils.translation._trans.gettext` | UNCHECKABLE | Django dynamically resolves _trans.gettext through Trans.__getattr__; installed gettext wrapper reads it at call time. No static property declaration exists; explicitly acknowledged dynamically resolved seam. 04-01-PLAN.md:224. |
| `translation.override` | UNCHECKABLE | External Django context manager; existing repository use-sites, no repo-owned declaration/signature certified. 04-01-PLAN.md:225. |
| `git show` | UNCHECKABLE | Existing Git command reads a committed snapshot without changing checkout; no repo-owned declaration. 04-03-PLAN.md:155. |
| `ALLOWED` | SKIPPED_NEW | Declared helper-local set in 04-03 Artifacts section; new test-local name. 04-03-PLAN.md:97. |
| `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` | SKIPPED_NEW | Declared new test in04-03 Artifacts section, produced by task04-03-01. 04-03-PLAN.md:94. |
| `tmp_path` | UNCHECKABLE | External pytest fixture supplied by existing test framework; no repo-owned declaration/signature certified. 04-03-PLAN.md:96. |
| `AssertionError` | UNCHECKABLE | Python builtin; no repo-owned declaration/signature certified. 04-03-PLAN.md:150. |

### Cross-artifact fact drift

- Deterministic phase status is lag: STATE Ready to plan versus ROADMAP Planned. This single nonterminal step is not a finding.
- Roadmap criteria and plan truths consistently cover baseline chronology, component/missing-component/dynamic dismissal, the core-only audit, references, paired release/migration changes and actual example acceptance.
- ALRT-01 through ALRT-04 match the roadmap/requirements and task/frontmatter assignments.
- D-01 through D-10 remain consistent: unchanged literal frame styling, no new class keys, adapter-owned errors and absence-only fallback, semantic call-time delegation and accurate copied-template migration. No focus/auto-dismiss or new lifecycle events were introduced.
