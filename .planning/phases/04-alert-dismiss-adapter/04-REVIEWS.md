---
phase: "04"
reviewers: ["fable-review", "gemini-review", "grok-review"]
reviewed_at: 2026-10-26T19:56:27.404788+00:00
plans_reviewed: ["04-01-PLAN.md", "04-02-PLAN.md", "04-03-PLAN.md"]
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
model_sources:
  fable-review: "pinned"
  gemini-review: "pinned"
  grok-review: "pinned"
---

# Cross-AI Plan Review — Phase 04

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts
<!-- gsd:plan-revision-conflicts:end -->

> Note: gemini-review and grok-review share the opencode adapter; their consensus is cross-model, not cross-tool.

Fresh independent review of all three current plans. Raw reports and per-reviewer diagnostics: [20261026T195627Z-gsd-review-3wyejogb](.review-diagnostics/20261026T195627Z-gsd-review-3wyejogb/).


## Claude Review (fable-review)


# Cross-AI Plan Review: Phase 04 Alert dismiss adapter

Repository access was available. Every claim below was checked against the working tree at commit `9f9d234` on `introduce-gsd`. I could not run the installed-tool version probes, so the tool-drift numbers quoted by the research remain an open question rather than a verified fact.

## 04-01

### Summary

The plan's description of the existing code is accurate in every detail I checked. The baseline-first ordering, the single shared golden consumed by both pytest and jsdom, and the call-time adapter lookup are sound. The main risks are process friction between the `tracer tdd="true"` task type and the plan's single-commit wording, and a byte-exact golden convention that differs from the repository's existing helper. Neither blocks execution.

### Strengths

- **Existing seams are cited correctly.** `src/crud_views/static/crud_views/js/adapters.js:7-8` defines `resolve` and `component`, and line 43 is the shallow preassignment merge the plan preserves. The cancel handler at `src/crud_views/static/crud_views/js/viewset.js:38-44` is the exact Element-guard, `closest`, `preventDefault` pattern the new listener copies.
- **Template claim verified.** `src/crud_views/templates/crud_views/tags/alert.html:5` emits `data-bs-dismiss="alert"` only inside `{% if alert.dismissible %}`. Replacing that one attribute leaves `btn-close`, `role="alert"` and the translated label intact, which also keeps `tests/test1/test_button_classes_templates.py:23` happy since `btn-close` stays in `EXEMPT_TOKENS`.
- **Exactly two message assertions need updating.** `tests/test1/test_messages.py:139` and `tests/test1/test_messages.py:169` are the only `data-bs-dismiss` assertions in the test tree. The plan's "both existing dismiss-attribute assertions" is precise.
- **Helper claims hold.** `_render` exists at `tests/test1/test_alerts.py:70-71`. `_theme_templates` exists at `tests/test1/test_form_frame.py:58-68`. `viewset.test.js` loads once in `beforeAll` at `tests/js/viewset.test.js:27-29` and the reload test is last at lines 91-101. The path-resolution pattern the plan wants to copy is `tests/js/helpers/load.js:1-8`.
- **Call-time lookup survives the test harness.** `loadScript` evaluates scripts against a Proxy whose `set` falls through to the real window at `tests/js/helpers/load.js:25-36`, so a listener reading `globalThis.cv.adapters.alert` at click time sees whatever `window.cv` the test installed. Replacing `window.cv` per case works without reloading `viewset.js`.
- **No pre-commit hook will mangle the golden.** `.pre-commit-config.yaml` has only `ruff-check` and `ruff-format`. There is no end-of-file fixer, so a golden written without a trailing newline survives the commit byte-for-byte.
- **Locale is pinned.** `tests/test1/conftest.py:98-100` sets `LANGUAGE_CODE="en-us"` and `USE_I18N=True`. Wrapping the render in `translation.override("en")` protects against a test that activates German without deactivating.

### Concerns

- **MEDIUM. The tracer task's commit wording conflicts with its own `tdd="true"` flag.** The action says "Run the combined Python alert/message suite followed by the JS tracer before committing" as if one commit. The execute workflow routes `tdd="true"` tasks through the RED, GREEN, REFACTOR commit-scope contract. The plan does not say which files land in the RED commit. A RED commit containing only the new JS cases that read the still-legacy golden fails correctly, but an executor could also stage the template in RED and break the D-07 chronology.
- **MEDIUM. The golden convention diverges from the repository's helper.** `tests/test1/test_form_frame.py:50-55` writes `_norm(markup) + "\n"` and compares with `strip()`. The plan deliberately uses raw bytes with no trailing newline. The reason is good, whitespace drift detection, but the golden will show "No newline at end of file" in every diff and any future contributor who touches it with an editor that appends a newline will break the comparison with no visible change.
- **LOW. The JS tracer inherits the Python golden's icon markup.** The rendered frame includes `<i class="fa-solid fa-circle-check me-2" aria-hidden="true">` from the default icon library. Any future regeneration of that golden silently changes the fixture the JS test runs against. The plan accepts this coupling by design, but nothing records it.
- **LOW. Translation patch target is correct but fragile.** Patching `django.utils.translation._trans.gettext` works because `{% translate %}` resolves through `gettext_lazy`, which calls `_trans.gettext` at `str()` time. The first `getattr` triggers the backend import and creates the instance attribute, so `monkeypatch.setattr` succeeds. This is an implementation detail of Django's `Trans` delegate and could move in a future Django version.

### Suggestions

- State the RED commit contents explicitly: only the new `viewset.test.js` cases, which fail because the committed golden still carries `data-bs-dismiss`. State the GREEN commit contents: template, both JS files, regenerated golden, both `test_messages.py` assertions.
- Add a one-line module docstring to the golden test explaining the no-trailing-newline rule, mirroring the regeneration instructions at `tests/test1/test_form_frame.py:3-4`.
- Consider pinning `CRUD_VIEWS_ICONS` to the default in the golden test so an icon-registry change elsewhere does not break the dismissal fixture.

### Risk Assessment

**LOW.** All code claims verified. The remaining items are process clarity and fixture hygiene.

## 04-02

### Summary

The regression matrix is complete against D-03, D-04 and D-08, and the helpers it names exist. The main weakness is over-specification of test-harness choreography: the descriptor save-and-restore dance is redundant in `adapters.test.js`, whose existing `afterEach` already deletes `window.cv` and unstubs globals. The plan also allows "bounded corrections" to production code, which is the right scope control.

### Strengths

- **`fakeNamespace` and the enumeration test exist exactly as described.** `tests/js/adapters.test.js:4-14` builds the fake namespace and `tests/js/adapters.test.js:20-24` loops over `modal`, `tooltip`, `collapse`. Adding `alert` to both is a two-line change.
- **Late-global and preassignment precedents exist.** `tests/js/adapters.test.js:115-131` covers a function namespace resolved at call time and `vi.stubGlobal("bootstrap", ns)`. `tests/js/adapters.test.js:133-140` proves preassigned adapter identity survives `loadScript`. The alert cases can copy these shapes directly.
- **`listenerErrors` exists and does what the plan needs.** `tests/js/helpers/errors.js:5-18` installs a window `error` listener, collects `event.error`, calls `preventDefault` so jsdom's virtual console stays quiet, and removes the listener in `finally`. The plan's instruction not to expect `dispatchEvent` to throw matches the helper's own comment at lines 1-4.
- **The detached-subtree concurrency truth is correct DOM behavior.** A click dispatched inside a subtree removed from the document bubbles only within that subtree and never reaches the document listener. The test will pass without any production change, which is the point.
- **Missing-key case has a precedent for the failure mode.** With `cv.adapters.alert` deleted, `globalThis.cv.adapters.alert.close(frame)` throws a `TypeError` after `preventDefault` has already run. The plan's expectation of one captured `TypeError`, frame attached, no logging, matches D-03.

### Concerns

- **MEDIUM. Descriptor save-and-restore is redundant in `adapters.test.js`.** `tests/js/adapters.test.js:18` already runs `vi.unstubAllGlobals(); delete window.cv;` after every test, and every test begins with `await loadScript("adapters")`. There is no "original" `cv` object to protect in that file. Mandating the C2-A2 descriptor dance there adds boilerplate without isolating anything. The discipline matters only in `viewset.test.js`, where `setup.js` stubs for `$` and `jQuery` must survive and the listener is shared across cases.
- **MEDIUM. A whole-object `cv.adapters` replacement after load becomes a silent breakage for themes.** `docs/reference/javascript.md:50-53` documents hand-written adapter objects. A theme that currently does `cv.adapters = {modal, tooltip, collapse}` after `adapters.js` loads will, after this phase, have every close button throw a `TypeError` with the alert left on screen. Plan 04-02 tests that behavior, which is correct under D-03, but neither 04-02 nor 04-03 explicitly documents this upgrade hazard. See the related 04-03 concern.
- **LOW. "Namespace with Modal/Tooltip/Collapse but no Alert" is the real Tabler-shaped case and deserves a comment.** `cv.bootstrapAdapters(() => globalThis.tabler)` at `docs/reference/javascript.md:64` is the documented alternate namespace. Tabler does bundle Bootstrap's `Alert`, so the fallback branch fires only for truly partial namespaces, but the test should say which real scenario it models.
- **LOW. Two listeners after reload.** The final test at `tests/js/viewset.test.js:91-101` reloads `viewset.js` and installs duplicate listeners. The plan correctly places new cases before it. Any future contributor adding alert cases after that test will see double adapter calls and a confusing failure. A comment at the insertion point would prevent that.

### Suggestions

- Scope the descriptor save-and-restore instruction to `viewset.test.js` only. In `adapters.test.js`, rely on the existing `afterEach` and the `vi.stubGlobal("bootstrap", ns)` precedent at line 128.
- Name the "other components but no Alert" case for what it models: a partial namespace or a Bootstrap build without the alert plugin.
- Extend the existing "keep it last" comment at `tests/js/viewset.test.js:91` to say that alert dismissal cases must stay above it.

### Risk Assessment

**LOW.** Coverage is thorough and the helpers exist. The concerns are about test ergonomics and one documentation gap handed to 04-03.

## 04-03

### Summary

Every documentation location the plan names was found at the quoted position, the allowlist matches the actual `data-bs-` audit, and the historical-red probe is feasible because the baseline commit contains the unchanged template. Two gaps remain: the plan does not explicitly require documenting the whole-object adapter replacement hazard, and the browser smoke will almost certainly land as "pending" because the executor agent has no browser tooling.

### Strengths

- **Audit baseline verified exactly.** `git grep 'data-bs-' src/crud_views/templates` returns four lines in three files: `crud_views/tags/actions_menu_toggle.html:4-5`, `crud_views/snippets/language_selector.html:6`, and `crud_views/tags/alert.html:5`. After the attribute change, the two remaining files are both named at `docs/reference/theme.md:179-181`. `actions_menu.html` is named there but has no `data-bs-` attribute, so the plan's "subset, not equality" semantics are the only correct contract.
- **Scan scope matches the roadmap and excludes extension templates on purpose.** `src/crud_views_object_detail/templates/.../accordion/group.html:5,15` and `tabs-vertical/object_detail.html:10-11` carry `data-bs-toggle`. They sit outside `src/crud_views/templates`, which is what ALRT-04 names. The plan's deferral of those to Phase 7 is accurate.
- **Every stale documentation line is real.** `docs/reference/javascript.md:14` says `viewset.js` needs nothing at use. Line 57 says "builds all three adapters". Line 179 says "All three are bubbling CustomEvents" and correctly must stay, since it counts events. `docs/reference/messages.md:29-38` shows the old markup and claims closing needs Bootstrap's bundle. `docs/reference/settings.md:184,187-188` lists only submit-form and cancel-url hooks. `docs/migrating-1.0.md:309-310` enumerates three adapters and line 374 lists adapters whose absence loses "modal, filter and tooltip behaviour".
- **A migration precedent already exists for the exact pattern.** `docs/migrating-1.0.md:345-346` documents the modal's `data-cv-modal-dismiss` with the sentence that a copy with `data-bs-dismiss` "keeps working under the Bootstrap adapter only". The alert bullet can mirror it, and `tests/test1/test_modal.py:308-309` shows the matching test shape.
- **`_section` behaves as the plan assumes.** `tests/test1/test_label_mode_docs.py:35-45` matches a heading string verbatim, requires exactly one occurrence, and the fence-aware `_headings` at lines 29-32 ignores `#` lines inside code blocks. A unique "### Custom alert frame" heading will extract cleanly.
- **The historical probe is feasible.** The baseline commit from 04-01-01 contains only the golden and test, so `git show <baseline>:src/crud_views/templates/crud_views/tags/alert.html` returns the legacy template with the `data-bs-dismiss` line. Copying the core tree to a temp directory and swapping that file gives a real red specimen without touching the checkout.
- **Recipe escaping is safe by construction.** `src/crud_views/lib/messages.py:45-54` returns `conditional_escape` results for heading, text and items and unconditional `escape` for `extra_tags`. A recipe that renders `{{ alert.extra_tags }}` cannot introduce injection, and `SafeString` returns prevent double-escaping under autoescape.
- **Docs-sync exemption is correctly understood.** `examples/bootstrap5/test_docs_sync.py:21-24` only matches fences preceded by a `cv-sync` marker, so the new theme recipe is exempt and the plan rightly adds its own render test instead.

### Concerns

- **MEDIUM. The whole-object adapter replacement hazard is not an explicit documentation requirement.** The plan updates the adapter enumeration and the "lost behaviour" checklist, but a theme author reading `docs/reference/javascript.md:50-53` today learns that a hand-written `cv.adapters` object is supported. After this phase, such an object without `alert` makes every close button throw. The migration guide should name this case directly and point to `cv.bootstrapAdapters(ns).alert` as the one-line fix for Bootstrap-compatible namespaces.
- **MEDIUM. The browser smoke will realistically remain unverified by the executor.** The `gsd-executor` agent's tool set is Read, Write, Edit, Bash, Grep, Glob and Skill. It has no browser automation. The plan's human-check is well written and routes to end-of-phase verification, but the acceptance note should be expected to say "pending" rather than treat that as a surprise. The example is otherwise ready: `examples/bootstrap5/project/templates/project/base.html:19` loads Bootstrap 5.3.3 before `{% cv_js %}` at line 37 and renders `{% cv_messages %}` at line 56.
- **LOW. D-06's legacy-path statement needs one qualifier.** Bootstrap's dismiss trigger locates the frame with `closest(".alert")`, not `role="alert"`. A copied legacy template that also dropped the `alert` CSS class never closed through Bootstrap either. The migration text should say legacy copies keep working "when the frame still carries Bootstrap's `alert` class".
- **LOW. Tool-version drift could not be re-verified here.** The sandbox blocked the version probes. `package.json:20-21` declares `jsdom ^30.1.2` and `vitest ^5.0.3`, `pyproject.toml:61` declares `ruff>=0.17,<0.18`, and `.pre-commit-config.yaml` pins `ruff-pre-commit v0.17.1`. If the venv Ruff really is 0.16.10, the hook formats with a different Ruff than `ruff format --check` uses, which can produce check failures that the hook itself introduced. The plan's instruction to disposition drift honestly is the right call.
- **LOW. `settings.md` appears in `files_modified` but not in the artifact list.** Harmless, but the artifact list is what downstream verification reads.

### Suggestions

- Add to 04-03-02: an explicit migration sentence for projects that assign a whole `cv.adapters` object after load, naming `alert.close(el)` as the required method and `cv.bootstrapAdapters(ns).alert` as the shortcut.
- Qualify the D-06 statement with the `.alert` class requirement, mirroring the modal wording at `docs/migrating-1.0.md:345-346`.
- In 04-03-03, pre-authorize the executor to record "browser acceptance pending, procedure recorded" as the expected outcome so it does not spend effort trying to launch a browser it cannot drive.

### Risk Assessment

**LOW to MEDIUM.** Documentation targets are all real and correctly located. The medium items are a missing migration sentence and a predictable "pending" on the browser gate.

## Cross-plan assessment

**Dependency ordering is correct.** 04-01 owns the template and both JS files, 04-02 extends the same test files, 04-03 depends on the implemented contract and the baseline hash. No same-wave file overlap exists.

**The phase achieves its goal.** After 04-01, the stock frame carries no Bootstrap data attribute and the only `data-bs-` templates left under `src/crud_views/templates` are the two dropdown files already documented. After 04-02, the adapter ownership contract is pinned by behavior tests rather than string matching. After 04-03, the public references, Breaking entry and migration guide agree with the code.

**Scope discipline is good.** No new class keys, no focus management, no lifecycle events, no installs. The "bounded corrections only if exposed" clause in 04-02 is the right guard against drift into refactoring.

**Where the plans over-reach**, it is in test-harness choreography rather than product scope. The descriptor save-and-restore instruction belongs only in `viewset.test.js`. The seven-row "spec-less edge" bookkeeping and the repeated STRIDE tables add length without changing what the executor does.

**One accepted deviation to acknowledge.** `.planning/PROJECT.md:75-77` names `feat/alert-dismiss-adapter` as the phase branch. The plans execute on `introduce-gsd` by maintainer decision recorded in the A2 disposition. That is consistent with how Phases 1 to 3 ran.

**Overall risk: LOW.** The code claims are accurate, the tests exist where the plans say they do, and the one behavior change is a single attribute plus an additive adapter. The findings above are refinements, not blockers.


---


## OpenCode Review (gemini-review)


## 04-01

### 1. Summary

Plan `04-01` sequences the phase's foundational deliverables: committing a byte-exact pre-change golden for a dismissible alert (`ALRT-01`, `D-07`), implementing `cv.bootstrapAdapters(ns).alert.close(el)` in `src/crud_views/static/crud_views/js/adapters.js` and the delegated `[data-cv-alert-dismiss]` click listener in `src/crud_views/static/crud_views/js/viewset.js`, switching `src/crud_views/templates/crud_views/tags/alert.html:5` from `data-bs-dismiss="alert"` to `data-cv-alert-dismiss`, and updating the flash-message assertions in `tests/test1/test_messages.py:139,169` in the same tracer commit so the test suite remains green across commits. Verification against the repository source confirms that all referenced files, template tags, and test helpers match the plan's assumptions.

### 2. Strengths

- **Strict golden chronology and byte-level fidelity (`ALRT-01`, `D-07`):** Unlike `tests/test1/test_form_frame.py:44-55`, where `_norm()` collapses whitespace via `re.sub(r">\s+<", "><", markup)`, Task `04-01-01` writes raw UTF-8 bytes (`markup.encode("utf-8")`) and compares via `read_bytes()`. Because `src/crud_views/templates/crud_views/tags/alert.html:1-6` begins with `{% load crud_views i18n %}\n`, raw byte comparison preserves leading/interior whitespace and guarantees the subsequent diff in `04-01-02` is strictly the `data-bs-dismiss="alert"` → `data-cv-alert-dismiss` attribute replacement.
- **Green atomic commits across Python and JS suites:** `tests/test1/test_messages.py:139` (`test_cv_messages_renders_a_dismissible_alert`) and `tests/test1/test_messages.py:169` (`test_create_message_renders_as_an_alert`) currently assert `'data-bs-dismiss="alert"' in html`. Including both updates in Task `04-01-02` alongside `src/crud_views/templates/crud_views/tags/alert.html:5` avoids a broken intermediate commit.
- **Exact alignment with existing adapter and delegation idioms:**
  - `src/crud_views/static/crud_views/js/adapters.js:7-8,43` already provides `component(ns, name)` and `cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {})`. Adding `alert: { close(el) { ... } }` inside `cv.bootstrapAdapters` with `component(ns, "Alert")` and `el.remove()` fallback only when `Alert` is absent cleanly implements `D-03` and `D-04`.
  - `src/crud_views/static/crud_views/js/viewset.js:38-44` already uses `if (!(e.target instanceof Element)) return;` and `e.target.closest(...)` before `e.preventDefault()`. Looking up `globalThis.cv.adapters.alert.close(frame)` at click time matches `src/crud_views/static/crud_views/js/list.filter.js:15` (`globalThis.cv.adapters.collapse.toggle(panel)`).
- **Scoped global cleanup in `viewset.test.js`:** `tests/js/helpers/setup.js:7-8` installs `$` and `jQuery` via `vi.stubGlobal` once at suite startup, and `tests/js/viewset.test.js:91-101` relies on those globals still being present until the final reload test. Saving and restoring only the `window.cv` and `window.bootstrap` property descriptors in `04-01-02` avoids wiping `$` / `jQuery` with `vi.unstubAllGlobals()`.

### 3. Concerns

- **LOW — Relative path depth in `tests/js/viewset.test.js` differs from `tests/js/helpers/load.js`:** The "Artifacts this phase produces" section of `04-01` states that `DISMISSIBLE_ALERT_HTML` in `tests/js/viewset.test.js` is read from `tests/test1/golden/alerts/dismissible.html` using "`node:fs`, `node:path` and `fileURLToPath` (the existing helper's path-resolution pattern)". In `tests/js/helpers/load.js:8`, the file sits under `tests/js/helpers/` (three levels below repo root, using `"../../../..."`), whereas `tests/js/viewset.test.js` sits under `tests/js/` (two levels below repo root, so the relative path to the golden is `"../test1/golden/alerts/dismissible.html"` or `"../../tests/test1/golden/alerts/dismissible.html"`). Copying `../../../` verbatim from `load.js:8` into `viewset.test.js` will resolve outside the repository.
- **LOW — German translation for `"Close"` already exists in compiled catalog (`src/crud_views/locale/de/LC_MESSAGES/django.po:103-104`):** Task `04-01-03` tests `{% translate 'Close' %}` in `src/crud_views/templates/crud_views/tags/alert.html:5` by monkeypatching `django.utils.translation._trans.gettext` under `translation.override("en")`. While that works (because `django.templatetags.i18n.TranslateNode.render` delegates through `django.utils.translation.gettext` → `_trans.gettext`), `src/crud_views/locale/de/LC_MESSAGES/django.po:103-104` (and compiled `django.mo`) already ships `msgid "Close"` → `msgstr "Schließen"`. Only testing a monkeypatched English sentinel misses a direct check that the shipped German catalog translates `aria-label="Schließen"` under `translation.override("de")`.

### 4. Suggestions

- In Task `04-01-02`, explicitly resolve the golden path in `tests/js/viewset.test.js` as `path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../test1/golden/alerts/dismissible.html")`.
- In Task `04-01-03`, alongside the `_trans.gettext` sentinel check, assert that rendering a dismissible alert under `with translation.override("de"):` produces `aria-label="Schließen"`, matching the real catalog pattern in `tests/test1/test_i18n.py:84-90`.

### 5. Risk Assessment

**LOW** — The template change is a single attribute rename (`src/crud_views/templates/crud_views/tags/alert.html:5`), the JS additions follow established seams in `adapters.js` and `viewset.js`, and no existing golden file in `tests/test1/golden/` contains a dismissible alert (verified: `tests/test1/golden/form_frame/delete_protection.html:1` is non-dismissible).

---

## 04-02

### 1. Summary

Plan `04-02` expands unit and DOM regression coverage in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` to verify lazy namespace resolution (`object`, `function`, late `globalThis.bootstrap`, namespace with `Modal`/`Tooltip`/`Collapse` but no `Alert`), preassigned `cv.adapters.alert` preservation, custom adapter replacement at call time, error surfacing without core logging or fallback removal (`D-03`, `D-04`), dynamic/modal-injected alert dismissal (`D-08`), and repeated-call/rapid-click edge cases (`EDGE-ALRT-03-idempotency`, `EDGE-ALRT-03-concurrency`).

### 2. Strengths

- **Thorough separation of adapter vs. handler responsibilities (`D-03`, `D-04`):** Task `04-02-01` and Task `04-02-02` explicitly verify that `el.remove()` only runs inside the default adapter when `component(ns, "Alert")` is absent — never when a present `Alert.getOrCreateInstance(el).close()` is a no-op or throws, and never as a fallback in `viewset.js` when a custom `cv.adapters.alert.close(el)` throws or is missing.
- **Proper observation of uncaught listener exceptions in jsdom:** Because exceptions thrown inside a `document.addEventListener("click", ...)` callback are reported as `window` `"error"` events rather than thrown synchronously out of `dispatchEvent()`, Task `04-02-02` reuses `listenerErrors(fn)` from `tests/js/helpers/errors.js:5-18`, which attaches a temporary `window` `"error"` listener, calls `event.preventDefault()`, and returns the captured `Error` instances.
- **Preservation of listener count in `tests/js/viewset.test.js`:** `tests/js/viewset.test.js:27-29` loads `viewset.js` once in `beforeAll`, and `tests/js/viewset.test.js:91-101` reloads `viewset.js` at the end of the file (`// reloads the script (adds listeners), so keep it last`). Task `04-02-02` places all new click-delegation tests before line 91 so duplicate listeners cannot mask call-count assertions.
- **Protection against shared object mutation across tests (Round 2 `C2-A2`):** Assigning a fresh `window.cv` / `adapters` object per test before deleting or mutating `cv.adapters.alert` prevents mutating a shared reference that `Object.defineProperty` descriptor restoration alone would not undo.

### 3. Concerns

- **LOW — Existing `afterEach` in `tests/js/adapters.test.js:18` already calls `vi.unstubAllGlobals(); delete window.cv;`:** Task `04-02-01` instructs saving and restoring `window.cv` and `window.bootstrap` descriptors and preserving `$/jQuery` in `tests/js/adapters.test.js`. In reality, `tests/js/adapters.test.js:17-18` already defines `afterEach(() => { vi.unstubAllGlobals(); delete window.cv; });` at the top of `describe("adapters.js", ...)` and does not use jQuery, whereas `tests/js/viewset.test.js` has no `afterEach` cleanup and does require `$` / `jQuery` preservation (`tests/js/viewset.test.js:2,91-101`). While saving/restoring descriptors in `finally` in `adapters.test.js` is harmless, the executor should be aware that `adapters.test.js:18` already resets `window.cv` and stubbed globals after every test.
- **LOW — Orphan `[data-cv-alert-dismiss]` `defaultPrevented` behavior should be asserted explicitly:** In `src/crud_views/static/crud_views/js/viewset.js`, when `[data-cv-alert-dismiss]` has no enclosing `[role="alert"]` (`const frame = el.closest('[role="alert"]'); if (!frame) return;`), returning before `e.preventDefault()` leaves `event.defaultPrevented === false` (matching `modal.js:125-129` where `event.preventDefault()` only runs when `modal && modal.contains(dismiss)`). Task `04-02-02` states "matched controls must prevent the default" and "missing role frame ... call no adapter and change no DOM", which is consistent, but explicitly asserting `expect(event.defaultPrevented).toBe(false)` for an orphan `[data-cv-alert-dismiss]` outside `[role="alert"]` will lock in the guard order (`if (!frame) return;` before `e.preventDefault()`).

### 4. Suggestions

- In Task `04-02-02`, use a scoped `beforeEach` / `afterEach` inside `describe("delegated alert ownership", ...)` in `tests/js/viewset.test.js` to snapshot/restore the `window.cv` and `window.bootstrap` descriptors and initialize a fresh `await loadScript("adapters")` per test, rather than duplicating `try / finally` descriptor boilerplate across every individual `it(...)` block.
- Add `expect(event.defaultPrevented).toBe(false)` to the orphan `[data-cv-alert-dismiss]` test case in `tests/js/viewset.test.js` to verify `if (!frame) return;` precedes `e.preventDefault()`.

### 5. Risk Assessment

**LOW** — Plan `04-02` is primarily a JS behavioral test expansion in `tests/js/adapters.test.js` and `tests/js/viewset.test.js` with bounded fixes to `adapters.js` / `viewset.js` only if exposed. All test helpers (`loadScript`, `listenerErrors`, `fakeNamespace`) already exist in the repository.

---

## 04-03

### 1. Summary

Plan `04-03` updates the documentation and release notes (`docs/reference/javascript.md`, `docs/reference/messages.md`, `docs/reference/theme.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`), adds executable tests in `tests/test1/test_alerts.py` for the documented custom alert frame recipe and the core `data-bs-*` template allowlist (`ALRT-04`), and runs the full project quality gates plus the example project flash-message smoke check (`D-10`).

### 2. Strengths

- **Accurate scoping of the `data-bs-*` template audit (`ALRT-04`, Round 1 `H1` & Round 2 `C2-A1`):** Grepping `data-bs-` across `src/` shows matches in `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5,15` and `tabs-vertical/object_detail.html:10-11`, whereas `src/crud_views/templates` has matches only in `crud_views/tags/alert.html:5` (removed in `04-01`), `crud_views/tags/actions_menu_toggle.html:4-5`, and `crud_views/snippets/language_selector.html:6` (while `crud_views/tags/actions_menu.html` is the wrapper listed in `docs/reference/theme.md:179` with no `data-bs-` attribute of its own). Scoping `_assert_core_bootstrap_data_attributes(root)` in `04-03-01` to `src/crud_views/templates` with `matches <= ALLOWED` and adding the `tmp_path` negative test (`test_core_bootstrap_data_attribute_guard_rejects_forbidden_path`) makes the check both accurate and permanently non-vacuous without depending on git history at test runtime.
- **Executable documentation recipe (`D-02`, Review `A8`):** Extracting the `"Custom alert frame"` snippet from `docs/reference/theme.md` and rendering it through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`) with `CRUD_VIEWS_BUTTON_CLASSES={"alert:error": ...}` and hostile inputs verifies that the documented override actually loads `crud_views i18n`, calls `{% cv_button_class "alert" alert.level %}`, includes `alert.body_template`, and preserves `role="alert"` and `data-cv-alert-dismiss`.
- **Comprehensive cross-reference updates (Review `A7`):** Beyond the three primary docs (`javascript.md`, `messages.md`, `theme.md`), `04-03-01` and `04-03-02` also update `docs/reference/settings.md:184-189` (which enumerates delegated `data-cv-*` attributes handled by `viewset.js`) and `docs/migrating-1.0.md:309,374` (which enumerate `cv.adapters.*` and what breaks when `adapters.js` is missing).

### 3. Concerns

- **LOW — `_section()` heading format and code-fence language in `test_documented_alert_frame_override` (`tests/test1/test_alerts.py`):** Task `04-03-01` instructs extracting "the fence under the uniquely named 'Custom alert frame' heading using the established fence-aware `_section` pattern in `test_label_mode_docs.py`". In `tests/test1/test_label_mode_docs.py:24,35-45`:
  1. `_section(text, heading)` matches `m.group(0) == heading` (line 39), which requires the leading markdown hashes (e.g. `"### Custom alert frame"`, not bare `"Custom alert frame"`).
  2. `FENCE` in `tests/test1/test_label_mode_docs.py:24` is `re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)`, which only matches `python` blocks, whereas template examples in `docs/reference/theme.md:125,140,148` use ```` ```html ```` or ```` ```django ````. Reusing `FENCE` from `test_label_mode_docs.py` or passing `"Custom alert frame"` without `### ` will fail with an `AssertionError`.
- **LOW — `CHANGELOG.md:294` under `## Unreleased` → `### Added` still lists only three adapters:** In `CHANGELOG.md:294`, the Unreleased `### Added` bullet currently reads:
  `- cv.adapters (modal, tooltip, collapse) and cv.bootstrapAdapters(ns); see docs/reference/javascript.md.`
  While Task `04-03-02` adds a `### Breaking` entry to `CHANGELOG.md` and updates the three-adapter list in `docs/migrating-1.0.md:309`, it does not mention updating `CHANGELOG.md:294` to include `alert` (`modal`, `tooltip`, `collapse`, `alert`).

### 4. Suggestions

- In Task `04-03-01`, specify the exact markdown heading level in `docs/reference/theme.md` (`### Custom alert frame` under `## Alerts`) and extract its code block with a `django`/`html` fence pattern (`re.compile(r"^```(?:django|html)\n(.*?)^```", re.MULTILINE | re.DOTALL)`).
- In Task `04-03-02`, also update `CHANGELOG.md:294` from `(`modal`, `tooltip`, `collapse`)` to `(`modal`, `tooltip`, `collapse`, `alert`)` so `CHANGELOG.md`'s Unreleased `### Added` section stays consistent with `### Breaking` and `docs/reference/javascript.md`.

### 5. Risk Assessment

**LOW** — Documentation, changelog, and guard tests are well-scoped, `examples/bootstrap5/test_docs_sync.py:21-24` only checks `<!-- cv-sync: ... -->` blocks (so adding an unmarked recipe in `docs/reference/theme.md` will not break `test_docs_sync.py`), and `04-03-03` explicitly accounts for environment version drift and browser availability without falsifying verification status.

---

## Cross-Plan Assessment & Overall Summary

- **Dependency & Wave Ordering:** Wave 1 (`04-01`) → Wave 2 (`04-02`) → Wave 3 (`04-03`) is properly ordered. `04-01` establishes the pre-change golden commit first (`04-01-01`), lands the core template/JS implementation and message test updates (`04-01-02`), and completes Python rendering regressions (`04-01-03`); `04-02` deepens the JS unit/delegation matrix on top of `04-01`; `04-03` updates the reference/migration docs, adds the recipe and `data-bs-*` allowlist tests, and runs all final gates.
- **Goal Achievement:** All four phase requirements (`ALRT-01` through `ALRT-04`) and all ten user decisions (`D-01` through `D-10`) are completely and accurately addressed with no scope creep.
- **Overall Risk:** **LOW** — All prior high/medium review findings (`H1`, `A1`–`A10`, `C2-A1`–`C2-A3`) have been cleanly integrated into the plans; only minor implementation notes (`LOW` severity) remain.


---


## OpenCode Review (grok-review)


I'll verify each plan against the current source, starting with the alert frame, adapters, and the tests the plans claim already exist.
The planning directory is not in the tree; I'll check the tests, docs, and templates the plans treat as existing.
The throw-path plan asserts core never logs; I'll check whether jsdom itself writes `console.error` for listener exceptions.
## 04-01

The baseline-then-tracer split matches the current code. The stock dismiss hook is only the dismissible branch of `src/crud_views/templates/crud_views/tags/alert.html:5`, the factory is still three adapters with a lazy namespace and a shallow merge (`src/crud_views/static/crud_views/js/adapters.js:3,7-8,43`), and `viewset.js` already delegates clicks with an `Element` guard and `closest()` (`src/crud_views/static/crud_views/js/viewset.js:37-44`). Task 02 is the right place to swap that one attribute and add one listener. ALRT-03 is only started here; custom and error ownership correctly wait for 04-02.

**Strengths**
- The only live `data-bs-dismiss="alert"` assertions are `tests/test1/test_messages.py:139` and `:169`. Putting both in the tracer commit, and running the combined pytest gate before that commit, keeps the series bisectable. No golden under `tests/test1/golden/` contains `data-bs-dismiss`.
- Raw `read_bytes()` is the right ALRT-01 instrument. `tests/test1/test_form_frame.py:44-55` normalizes whitespace, which would hide a drift this phase must show.
- Call-time `globalThis.cv.adapters.alert.close` matches the Proxy in `tests/js/helpers/load.js:32-36`. Reloading `adapters.js` after deleting `window.cv` yields fresh defaults without stacking the `viewset.js` listener. The reload test at `tests/js/viewset.test.js:91-101` stays last.
- `{% translate 'Close' %}` resolves through `gettext_lazy` to `_trans.gettext` (`django/template/base.py:860-867`, `django/utils/translation/__init__.py:95-111`). Patching that seam, not a template-tag alias, is the right test. The msgid is already in `src/crud_views/locale/de/LC_MESSAGES/django.po:103-104`; no catalog change is required.
- D-04 correctly overrides the source plan. `superpowers/plans/2026-10-24-concept-review-followups.md:234-235` puts `el.remove()` in the handler; this plan keeps removal inside the adapter.

**Concerns**
- LOW: Task 01 says "fixed English locale" but does not name `translation.override`. The suite default is `LANGUAGE_CODE="en-us"` (`tests/test1/conftest.py:98`), so an unpinned golden still renders `Close` today. Pin the override in the golden test itself so task 03's gettext patch cannot leak into the bytes.

**Suggestions**
- In the tracer, dispatch `MouseEvent("click", {bubbles: true, cancelable: true})` the way `tests/js/viewset.test.js:61-64` already does, or `defaultPrevented` is not meaningful.
- Record the baseline hash in `04-01-SUMMARY.md` as a full SHA. 04-03's historical probe depends on it.

**Risk Assessment:** LOW. The mechanism, the two message assertions, and the commit split are grounded in the current tree.

## 04-02

This wave is the right place for namespace, preassignment, dynamic content, and error ownership. It reuses `listenerErrors` (`tests/js/helpers/errors.js:5-17`), the existing `fakeNamespace` (`tests/js/adapters.test.js:4-14`), and the once-loaded listener. It does not add a second removal path, which is what D-03 and D-04 require. The source plan's `component(ns, "Alert")?.getOrCreateInstance(el).close()` would not remove on a missing component and would still throw if `getOrCreateInstance` returned null; the explicit branch in 04-01 plus these tests is the safer contract.

**Strengths**
- Late namespace lookup is already proven for modal (`tests/js/adapters.test.js:115-123`). Requiring the alert branch to call `component()` inside `close`, not at factory build, extends a real seam.
- `Object.assign` at `adapters.js:43` keeps a preassigned adapter as a whole object and fills the rest. The existing modal case at `tests/js/adapters.test.js:133-139` is the right pattern for `alert`.
- Case-owned `window.cv` objects are necessary. Restoring a property descriptor does not undo mutations of the object it pointed at. Avoiding `vi.unstubAllGlobals` is also necessary: `tests/js/helpers/setup.js:7-8` installs `$` / `jQuery` for the whole file, and `adapters.test.js:18` already wipes globals in its own file.
- An unmarked body inside `role="alert"` is a real miss the earlier "outside the frame" case would not cover. `tags/messages.html:1` only includes the frame, so the nearest-role rule is the whole message contract.
- Missing `cv.adapters.alert` throws `TypeError` on the planned lookup. `listenerErrors` is the right observer: `dispatchEvent` does not rethrow listener exceptions (`tests/js/helpers/errors.js:1-4`).

**Concerns**
- LOW: The detached-subtree click cannot fail if the handler is wrong. A click on a node that is not an ancestor of `document` never reaches the document listener. That case proves jsdom propagation, not the adapter. Do not treat it as handler coverage.
- LOW: "assert neither console was called by core" is easy to over-assert. `tests/js/list.filter.test.js:199` notes that jsdom reports listener errors on `console.error`. On jsdom 29.1.1, `preventDefault` inside an `error` listener suppresses that report, so `not.toHaveBeenCalled()` currently passes if `listenerErrors` runs. The proof of D-03 is the original error in that array plus an attached frame, not a silent console.

**Suggestions**
- Build the "other components, no Alert" namespace by copying `fakeNamespace()` and deleting `Alert`, rather than a new helper that drifts from `Modal` / `Tooltip` / `Collapse`.
- For the throw cases, assert `errors[0] === thrown` (same object), not `toBeInstanceOf(Error)`.

**Risk Assessment:** LOW. The product code should not need to change if 04-01 followed D-03/D-04. These tests are the lock.

## 04-03

The doc anchors this plan edits all exist: the script table at `docs/reference/javascript.md:13-14`, "builds all three" at `:57`, the events sentence "All three are bubbling CustomEvents" at `:179` (correctly left alone), the old markup and Bootstrap-only close sentence at `docs/reference/messages.md:29-38`, the Alerts and dropdown sections at `docs/reference/theme.md:156-184`, the settings delegation paragraph at `docs/reference/settings.md:184-188`, and the Unreleased Breaking list at `CHANGELOG.md:7`. The allowlist matches `theme.md:179-181`. After the attribute swap, `src/crud_views/templates` has `data-bs-` only in `tags/actions_menu_toggle.html:4-5` and `snippets/language_selector.html:6`. `tags/actions_menu.html` is a wrapper with no `data-bs-` attribute, so "nonempty subset, do not require every allowed path" is the correct contract. Object-detail `data-bs-*` lives under `src/crud_views_object_detail/templates`, outside ALRT-04's grep root.

**Strengths**
- Rendering the documented recipe through `_theme_templates` (`tests/test1/test_form_frame.py:58-68`) and fence-aware headings (`tests/test1/test_label_mode_docs.py:29-45`) is the right check. `examples/bootstrap5/test_docs_sync.py:7-10` ignores unmarked fences, so a docs-sync pass would not prove the recipe.
- Keeping `{% cv_button_class "alert" alert.level %}` matches `alert.html:2`. `tests/test1/test_alerts.py:124-127` already shows that key is overridable.
- The paired Breaking entry and migration example follow the repo rule, and `docs/migrating-1.0.md:309-310` and `:374` really do still name only three adapters and "modal, filter and tooltip".
- The lasting `tmp_path` rejection test does not need git. That is the right permanent guard.
- Browser evidence is not inferred from jsdom. Bootstrap's real `close()` fades and then destroys; a fake `close` that leaves the node attached is a different proof.

**Concerns**
- MEDIUM: The human-check consumes the only fresh message before the dynamic case. Step 2 assigns `cv.bootstrapAdapters({}).alert` and closes that message. Step 3 then says to clone "a still-present fresh message" and close it, and only afterwards restore the adapter. Followed literally, there is no node left to clone, and if one is produced it closes through the empty namespace, not through Bootstrap's transition. D-10's injected-alert observation can be skipped or mislabeled without a failing command.
- MEDIUM: Task 01's acceptance still requires the historical alert to fail the helper in a temporary tree, while the action says that `git show <baseline>` probe must not be a lasting test. The automated verify is only pytest and mkdocs. An executor matching acceptance to a test will put `git show` in pytest. That fails after a squash, rebase, or shallow clone even when the allowlist is correct. The synthetic `tmp_path` forbidden file already proves the helper rejects `crud_views/tags/alert.html`.
- LOW: The smoke says "authenticated create/update UI" and does not name a user. The example login is `/login/` (`examples/bootstrap5/project/urls.py:24`); seeded users are `alice`/`alice` and `bob`/`bob` (`examples/bootstrap5/project/seeding.py:6-8`), shown on the home page. Neither is a superuser. Create still needs a model `add` permission granted by `seed`.

**Suggestions**
- Rewrite the smoke as three separate messages: Bootstrap close and wait for the transition; a new message closed after the empty-namespace assignment; restore or reload; then insert a new message into a modal-like subtree and close it with the restored adapter. Name `alice`/`alice` and the create URL you actually use.
- Run the baseline `git show` once, record the rejected relative path and hash in `04-ACCEPTANCE.md`, and do not add a pytest that calls git.
- Extract the recipe with `ANY_FENCE` (`tests/test1/test_label_mode_docs.py:26`), not the python-only `FENCE` at `:24`. A Django template fence will not match ```` ```python ````.

**Risk Assessment:** MEDIUM. The reference and allowlist work is sound. The phase can still be marked done with D-10's browser half incomplete if the smoke is followed as written.

## Cross-plan

Waves are ordered correctly: 04-02's regressions need the listener and `alert.close` from 04-01, and 04-03 must describe the implemented contract, not the source plan's handler-side `el.remove()`. ALRT-01 through ALRT-04 are each assigned. No plan adds class-table keys, focus management, or a new lifecycle event. `docs/reference/javascript.md:179` stays three events while the factory becomes four adapters.

The implementation path is faithful to the current frame, factory, and click handlers. The residual risk is evidence, not design: do not let a vacuous detached-click test or a git-backed audit, or a smoke script that deletes the node it later clones, stand in for the locked close contract.


---


## Consensus Summary

All three configured reviewers returned source-cited reviews covering all three plans. No reviewer raised a HIGH concern. Fable and Gemini rate the overall plan LOW risk; Grok rates 04-03 MEDIUM because of the browser-evidence procedure. Source checks support the implementation approach and dependency order. Four bounded follow-ups remain: two MEDIUM documentation/acceptance clarifications and two LOW documentation/test-extraction clarifications. This review does not revise the plans or reopen previously resolved findings automatically.

### Agreed Strengths

- **Baseline chronology and real rendered tracer:** all reviewers confirm the existing alert hook and both message assertions, and endorse committing the raw golden before changing the template, then consuming it in JavaScript. Evidence: `src/crud_views/templates/crud_views/tags/alert.html:5`, `tests/test1/test_messages.py:139`, `tests/test1/test_messages.py:169`, and `.planning/phases/04-alert-dismiss-adapter/04-01-PLAN.md:114`.
- **Adapter ownership and dynamic dispatch:** all endorse lazy namespace resolution, call-time adapter lookup, absence-only removal, and using the existing listener-error observer. Evidence: `src/crud_views/static/crud_views/js/adapters.js:7`, `src/crud_views/static/crud_views/js/adapters.js:43`, `tests/js/helpers/errors.js:5`, and `.planning/phases/04-alert-dismiss-adapter/04-02-PLAN.md:163`.
- **Correct audit scope and release coverage:** all confirm the core-only template scan, nonempty subset allowlist, permanent synthetic negative test, and paired Breaking/migration update. The wrapper need not contain a data attribute, and extension apps are outside this requirement. Evidence: `.planning/phases/04-alert-dismiss-adapter/04-03-PLAN.md:139`, `docs/reference/theme.md:179`, and `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html:4`.

### Agreed Concerns

- **R04-04 — LOW, template-fence extraction (Gemini, Grok):** task 04-03-01 points to the existing section-extraction pattern, whose companion `FENCE` accepts Python only. Specify the full Markdown heading and a `django`/`html` fence when implementing the recipe test; do not copy the Python-only matcher. Evidence: `tests/test1/test_label_mode_docs.py:24`, `tests/test1/test_label_mode_docs.py:35`, and `.planning/phases/04-alert-dismiss-adapter/04-03-PLAN.md:133`. This is an implementation clarification, not proof the current plan requires the wrong matcher.
- **Cleanup ergonomics (Fable, Gemini):** `tests/js/adapters.test.js:18` already cleans globals after each case, making additional descriptor restoration partly redundant there. It remains important in the shared-listener suite. This is optional boilerplate reduction, not a correctness gap; preserve the existing fresh-object isolation requirement in `.planning/phases/04-alert-dismiss-adapter/04-02-PLAN.md:172`.

### Actionable Follow-ups

| ID | Severity | Plan/task | Source-grounded follow-up |
|---|---|---|---|
| R04-01 | MEDIUM | 04-03-02 | Explicitly warn that replacing the entire `cv.adapters` map **after** core loads must retain/provide `alert.close(el)`. `src/crud_views/static/crud_views/js/adapters.js:43` fills defaults only during initialization; the planned missing-key case deliberately throws (`04-02-PLAN.md:169`). Document per-entry replacement or preserving defaults; Bootstrap-compatible themes can use `cv.bootstrapAdapters(ns).alert`. The current migration task updates enumerations but does not name this case (`04-03-PLAN.md:185`). Raised by Fable; mechanism independently confirmed. |
| R04-02 | MEDIUM | 04-03-03 | Make browser acceptance use three explicit fresh messages: real Bootstrap close; absent-Alert fallback; restore/reload, then create and clone a fresh message into dynamically inserted content. Record which adapter each observation exercised. The current prose removes the second message before requesting a still-present fresh one and restores the adapter only afterward (`04-03-PLAN.md:256`). Raised by Grok; this clarifies reproducibility and avoids labeling a fallback observation as a Bootstrap transition. |
| R04-03 | LOW | 04-03-02 | Add `alert` to the existing Unreleased Added adapter enumeration at `CHANGELOG.md:294`, alongside the planned new Breaking entry and migration changes. Raised by Gemini; stale enumeration independently confirmed. |
| R04-04 | LOW | 04-03-01 | Use a heading-aware template-fence extractor as described under Agreed Concerns. Raised by Gemini and Grok. |

The shortened plan filenames in this table refer to `.planning/phases/04-alert-dismiss-adapter/`. None of these follow-ups requires changing the selected product contract.

### Divergent Views and Dispositions

- **Whole-map replacement needs a precise load-order qualifier.** Fable cites the existing hand-written adapter guidance, but `docs/reference/javascript.md:50` specifically documents pre-load assignment, which remains safe because defaults are merged at initialization. R04-01 concerns a later whole-map replacement. Per-entry replacement (`docs/reference/javascript.md:44`) also preserves the other defaults.
- **Historical Git probe is already separated from permanent tests.** Grok's MEDIUM concern is not an unresolved test-design defect: `.planning/phases/04-alert-dismiss-adapter/04-03-PLAN.md:151` explicitly requires the lasting regression to have no Git dependency, and line 158 explicitly keeps the historical probe outside that test. Preserve and execute both instructions; do not add a Git-dependent pytest.
- **Browser access is an execution-time question.** Fable's prediction that an executor cannot use a browser is not established by repository evidence. The plan already requires an explicit pending result when access is unavailable (`04-03-PLAN.md:225`, `04-03-PLAN.md:261`). Grok's claim that the phase can be marked complete without browser evidence overstates the plan: its action explicitly prohibits marking D-10 fully verified without browser and required-gate evidence. R04-02 improves the procedure without weakening that gate.
- **TDD commit wording merits care, but baseline chronology is explicit.** Fable requests explicit RED/GREEN file sets. Keep a RED test-only commit if required by the executor's TDD contract and put the coordinated template/adapter/golden/message changes in GREEN. `04-01-PLAN.md:114` already forbids any template or JS edit before the baseline commit. The reviewer’s hypothetical premature staging does not establish a D-07 gap. Do not interpret “green tracer commit” as permission to skip required RED evidence.
- **Raw bytes and the translation sentinel are intentional.** `04-01-PLAN.md:137` already specifies a fixed English locale, no appended newline, and documentation of that byte convention. The sentinel checks whether the template invokes translation; a real German-catalog assertion is optional additional coverage. Do not normalize the golden to match older helpers. Gemini's relative-path reminder is useful implementation guidance, not an erroneous path specified by the plan.
- **Error and detached-event evidence have bounded meaning.** `tests/js/helpers/errors.js:8` captures the original exception and prevents the default error report. `04-02-PLAN.md:165` already requires original-error identity, retained DOM/mutations, and no core logging; a silent console alone is insufficient. Detached-subtree clicks establish the explicitly stated DOM-propagation boundary, not independent proof of handler correctness. Other matched-event tests supply that proof.

### Evidence and Limits

Reviews were collected against commit `9f9d234ec1bec035226f6a24ff62308377e412d4`. Each reviewer covered 04-01, 04-02 and 04-03 and cited repository source. No reviewer required an evidence-quality discount marker. Grok reported that it could not see the planning directory in its source tree; it still received the full plans in the supplied prompt and inspected the implementation files, so this is a limit on direct plan-file access, not a source-free review.

No prompt budget trimming was configured, and no lane failed or was retried. This pass did not execute the implementation, full test suite, docs build, or browser acceptance. Historical environment-version claims remain subject to the planned execution-time recheck. Existing user changes to config and other untracked planning files were left intact.

To incorporate the four follow-ups, run `$gsd-plan-phase 4 --reviews`.
