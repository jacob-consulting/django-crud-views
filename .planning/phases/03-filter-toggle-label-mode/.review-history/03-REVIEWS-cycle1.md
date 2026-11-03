---
phase: 03
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T14:57:45.522410+00:00
plans_reviewed: [03-01-PLAN.md, 03-02-PLAN.md]
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

# Cross-AI Plan Review — Phase 03

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

None.
<!-- gsd:plan-revision-conflicts:end -->

> Note: grok-review, gemini-review and deepseek-review share the opencode adapter; their consensus is cross-model, not cross-tool.

All four configured reviewer instances completed successfully through `review-lane invoke`. No lane was dropped, stubbed, budget-skipped or trimmed. Every reviewer covered both plans and supplied source citations; none opens with an evidence-discount marker. Source reviewed at `e915235e6f6d97ad9b950c75487757bf6f4f66ea`.

## Claude Review (fable-review)

# Cross-AI Plan Review: Phase 03 (Filter toggle label mode)

Reviewed against the working tree at `e915235` on `introduce-gsd`. I opened every file the plans cite and traced each claimed mechanism. One fact could not be verified: reading Django's own German catalog in `.venv` was denied, so the point about `django.contrib.admin` supplying a `Filter` translation is marked as likely, not confirmed.

## 03-01

**Summary**

The plan is accurately grounded. Every mechanism it leans on exists as described: the resolver precedence at `src/crud_views/lib/view/base.py:312-322`, the outer mode stamp at `base.py:640-646`, the filter builder at `src/crud_views/lib/view/buttons.py:308-334`, the host-or-child placement rule at `src/crud_views/templates/crud_views/tags/context_action_filter.html:1-13`, and the icon-less tolerant handler at `src/crud_views/static/crud_views/js/list.filter.js:22-30`. The tracer → matrix → i18n sequence is sound and the raw-baseline rationale is correct. The gaps are specification details that will cause executor friction rather than product defects: what the template does when no mode is supplied, how the tracer sets the settings map, and some test rows that cannot discriminate anything.

**Strengths**

- **No target default is already true at both layers.** `cv_get_context` passes `data.get("cv_context_label_mode")` as `target_default` (`base.py:643`). The filter builder never sets that key (`buttons.py:323-329`), so the outer stamp and the planned inner stamp with `(self.key, self)` resolve identically. D-01 and D-02 hold without touching the generic wrapper.
- **Raw-baseline reasoning is verified.** `_canonical` sorts attributes and class tokens and `_norm` collapses whitespace (`tests/test1/test_action_menus_golden.py:38-55`). The template has real whitespace inside the `{% if %}` that emits the data attributes, so the golden alone cannot prove byte identity.
- **The two hand-built contexts are correctly identified.** `_filter_toggle` builds `{"cv_filter_expanded", "cv_action_label", "cv_key"}` with no mode (`tests/test1/test_button_leaves.py:574-576`), and the Phase 1 selector excludes the filter with a now-stale comment (`tests/test1/test_context_action_label_mode.py:250-251`).
- **JS scope is right.** `querySelectorAll("[data-cv-filter-icon]")` on an empty NodeList is a no-op (`list.filter.js:29`), collapse runs before any mutation (`:15-18`), and the rejection is swallowed (`:38`). Existing throw/false/reject tests at `tests/js/list.filter.test.js:98-133` already prove the ordering; keeping the source untouched is correct.
- **Localization anti-false-positive design is necessary and tooling is present.** `polib` 1.2.0 is installed in the venv and `msgfmt` is at `/usr/bin/msgfmt`. The core PO has no bare `Filter` msgid today (only `Apply Filter`, `Reset Filter`, `Filter %(verbose_name_plural_translate)s`).
- **Tracer persistence path exists.** `ListViewTableFilterMixin.post` writes `filter_expanded` to session data and `cv_filter_expanded` reads it back (`src/crud_views/lib/views/mixins.py:323-355`).

**Concerns**

- **MEDIUM. Missing-mode behaviour is undecided and the plan papers over it.** The stock action leaf treats an absent mode as the label branch (`tags/button/action.html:8`, final `else`). If the filter template follows that shape, any hand-built context without `cv_label_mode` flips the bundled toggle from icon to label-only. The plan avoids the question by editing `_filter_toggle` to pass `"icon"`, which also means the RAW_DEFAULT_FILTER baseline captured without the key only stays green if the assertion is changed too. That weakens the "committed before production edits, not regenerated afterward" guarantee. Decide it: an absent or unknown mode should take the icon branch so the stock template is byte-identical for every existing caller.
- **MEDIUM. The tracer's configuration mechanism is unstated and the obvious choice does not work.** `crud_views_settings.context_actions_label_mode` is captured once by `from_settings` at class-body time (`src/crud_views/lib/settings.py:13-14, 67`) and read through `cv_first_inline_keys` (`base.py:263-272`). `override_settings` cannot change it. Task 03-01-02 says "monkeypatch for snapshot-style existing action maps", but Task 03-01-01 only says "the existing settings-map filter entry set to both". An executor who reaches for `override_settings` gets a RED that never turns GREEN. State the monkeypatch target explicitly, following `tests/test1/test_context_button_label_mode.py:24-25`.
- **LOW. The German render truth cannot be proven by rendering.** Beyond identical spelling, the test project lists `django.contrib.admin` before `crud_views` (`tests/test1/conftest.py:44, 57`), and `tests/test1/test_i18n.py:42` already documents that admin's catalog wins for `Save`. Admin's German catalog very likely carries `Filter` as well (unverified). EDGE-FILT-04-encoding claims "active German rendering uses the compiled catalog"; the render test can only show the word appears. The compiled-membership and sentinel tests are the real evidence. Reword that truth so the summary does not overclaim.
- **LOW. Several JS rows test properties that cannot fail.** "Two deferred persistence promises settled out of order never roll back DOM state" and "promise settlement never alters the label" exercise a `.catch(() => {})` that touches nothing. The existing rejected-POST test (`list.filter.test.js:125-133`) already covers the only reachable behaviour. Mapping all 14 edge rows one-to-one to tests is where the 36k estimate at low confidence will overrun.
- **LOW. The raw baseline is stricter than the shipped contract.** `render_snippet` strips the rendered result (`base.py:371`), so leading and trailing whitespace never reaches a page. Acceptable, and the "wrap conditionals around existing whitespace" instruction is the right mitigation, but note it in the test docstring so a future reformat is not mistaken for a regression.
- **LOW. `both` spacing is unspecified.** The action leaf emits a space between icon and visible label in both mode (`action.html:8`). The filter template should mirror this or the two button kinds look different side by side.

**Suggestions**

- Add to Task 1's action: "An absent or unrecognised `cv_label_mode` renders the icon branch." Keep one raw assertion without the key and one with `"icon"`.
- Add to Task 1's action: set the map with `monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"filter": "both"})` or on the publisher ViewSet, never `override_settings`.
- Collapse the concurrency rows into the existing rejected-POST test and one "label node identity after two clicks" test per fixture.
- When registering the distinctive `context:secondary:both` class in the tracer, reset `_button_classes_cache` (`src/crud_views/lib/button_classes.py:128-133`) the way the existing class-table tests do, or the custom value leaks into other modules under `-n auto`.
- Mention in Task 3 that `test_filter_button_default_label` (`tests/test1/test_context_button_template.py:52-56`) must keep passing with plain `gettext` in English.

**Risk Assessment: LOW.** All production mechanisms are verified in source, the default output is protected two ways, and no new public name is introduced. The two MEDIUM items are specification gaps an executor can close inside Task 1 once told.

## 03-02

**Summary**

The documentation plan targets exactly the right stale passages and every anchor it links exists. It is, however, internally inconsistent: Task 03-02-01 deletes the sentence "outside this configuration" from `action_menus.md`, a doc-contract test pins that exact sentence, and the task's own verify command runs that test file while `files_modified` omits it. As written the task cannot go green.

**Strengths**

- **Stale wording located precisely.** `docs/reference/context_buttons.md:80-82` ("icon-only by construction, the way the bundled … does"), `docs/reference/buttons.md:304-306` ("the filter toggle … passes `"icon"`"), `docs/reference/action_menus.md:171-172` ("outside this configuration: neither the maps nor `CRUD_VIEWS_LABEL_MODE_DEFAULTS` change it"), `docs/reference/javascript.md:83` (tooltip row) and `:187-199` (two icon forms only), `docs/reference/icons.md:72-73, 174-176`.
- **Every link target exists.** `#context-label-mode-resolution` (`action_menus.md:87`), `settings.md#label-mode-configuration` (`settings.md:82`), "The filter toggle contract" (`javascript.md:187`), "What is never folded" (`action_menus.md:180`).
- **Fixed classification is defensible.** `### Fixed` exists under Unreleased (`CHANGELOG.md:147`), and default markup is unchanged, so no `### Breaking` and no migration entry is required by the project rule.
- **Gates are the real ones.** `.venv/bin/pytest`, `.venv/bin/mkdocs`, `.venv/bin/ruff` exist; `npm test` runs `vitest run` (`package.json:11`), so the file filter argument works and there is no watch mode.

**Concerns**

- **HIGH. Guaranteed red verify.** `tests/test1/test_label_mode_docs.py:236-237` asserts `"filter toggle" in rendering and "outside this configuration" in rendering` on the `### Rendering` section of `action_menus.md`. Task 03-02-01 removes that claim and then runs `tests/test1/test_label_mode_docs.py`. Add the test file to `files_modified`, and have the task replace the assertion with one that pins the new wording (for example "follows the resolved mode" plus the never-folded clause).
- **MEDIUM. Placement of the new section in `context_buttons.md` can break another doc test.** `test_label_mode_docs.py:277-286` splits "## How a context button is rendered" at the mermaid fence and asserts specific phrases in the first paragraph after it. Inserting the compact filter contract between the diagram and that paragraph fails the test. State where the section goes (after the existing custom-template paragraph at lines 77-82 is the natural spot).
- **LOW. Migration guide has filter-template bullets the plan leaves untouched.** `docs/migrating-1.0.md:243, 331, 399` tell projects that copied `context_action_filter.html` how to update it. A copied template now silently ignores `cv_label_mode`. No `### Breaking` entry forces an update, but one line on the existing checklist bullet at `:399` would serve the doc's purpose. Decide deliberately rather than by omission.
- **LOW. Branch versus process rule.** `PROJECT.md:76-78` names `feat/filter-toggle-label-mode`; work is on `introduce-gsd`, and `STATE.md:80` records the user chose to stay on the current branch for Phase 1. Task 03-02-02's "inspect the final diff" should say which branch the phase lands on so the one-PR-per-phase rule is consciously kept or waived.
- **LOW. The docs example must not be mirrored into tests.** `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` is correct for a project's settings module but, as noted under 03-01, does not work through `override_settings`. The test-settings note at `action_menus.md:176-178` is the right place for one sentence if any is added.

**Suggestions**

- Add `tests/test1/test_label_mode_docs.py` to `files_modified` and to Task 03-02-01's action: update the `### Rendering` assertion, re-run the doc tests, confirm `:277-306` still pass.
- Specify the insertion point for the new filter section in `context_buttons.md`.
- Decide on the migration-guide checklist line and record the decision in the summary either way.
- Record the landing branch in `03-02-SUMMARY.md`.

**Risk Assessment: MEDIUM.** The content plan is correct and small, but one verify step is certain to fail as written, and a second doc test is easy to break by placement. Both are cheap fixes to the plan text.

## Cross-plan assessment

- **Dependency ordering is right.** 03-02 consumes `03-01-SUMMARY.md` and the implemented behaviour; no same-wave file conflicts. Both plans declare all four FILT IDs, so the shared-ID gate defers marking until the second summary exists.
- **Scope.** No creep into form buttons, adapters, or the downstream theme. The only over-reach is test volume in 03-01's JS rows.
- **Security.** Nothing new crosses a trust boundary. Labels stay under Django autoescape, the CSRF header and JSON body are unchanged (`list.filter.js:34-37`), and the early `cv_access: False` returns are preserved (`buttons.py:311-319`). The threat registers are proportionate for ASVS level 1.
- **Performance.** One extra classmethod call per filter render. Negligible.
- **Phase goal.** With the three plan-text fixes (missing-mode default, doc-test update, section placement), the plans deliver FILT-01 through FILT-04 with the default golden intact.

---

## OpenCode Review (grok-review)

I'll verify both plans against the live filter, resolver, and docs code before writing the review.
## 03-01

The implementation plan matches the live filter contract and can deliver FILT-01 through FILT-04 without a JavaScript rewrite. The remaining risk is the whitespace-sensitive icon branch, not a missing mechanism.

### Strengths
- Resolver reuse is correct. `cv_get_action_label_mode` already does own map, then button override, then the selected whole map, then `target_default` or the context floor (`src/crud_views/lib/view/base.py:312-322`). Calling it as `cv_get_action_label_mode("context", self.key, self)` with no fourth argument matches D-01 and D-02. `FilterContextButton.get_context` currently seeds an untranslated `"Filter"` and never stamps a mode (`src/crud_views/lib/view/buttons.py:323-332`).
- Stamping before `_apply_label` is required. `cv_get_context` stamps `cv_label_mode` only after `get_context` returns (`src/crud_views/lib/view/base.py:640-645`), and label templates render inside `get_context` (`src/crud_views/lib/view/buttons.py:55-71`).
- Leaving `list.filter.js` unchanged is justified. Collapse runs first and a false return skips mutation (`src/crud_views/static/crud_views/js/list.filter.js:15-17`); an empty `[data-cv-filter-icon]` list is a no-op (`:29`); a rejected POST cannot roll back state because the response is ignored (`:32-38`).
- The raw-byte guard is the right compatibility check. The toolbar golden sorts attributes and class tokens and collapses whitespace (`tests/test1/test_action_menus_golden.py:38-55`), so it cannot prove the current 14-line template (`src/crud_views/templates/crud_views/tags/context_action_filter.html:1-13`) stayed intact.
- Host versus child placement is already `if cv_open_class and cv_close_class` (`context_action_filter.html:3,9-13`). `HOST_ICONS` already maps `filter` and `filter-close` (`tests/lib/helper/icons.py:11-12`). W292 will not start firing: it skips buttons whose `get_context` is not `ContextButton.get_context` (`src/crud_views/lib/view/buttons.py:391-397`).

### Concerns
- **MEDIUM — missing `cv_label_mode` is not the same as mode `"icon"` for class lookup.** The leaf hard-codes the third argument as `"icon"` (`context_action_filter.html:3`). `get_button_class` uses `location:slot:mode` only when `mode` is truthy and that key exists (`src/crud_views/lib/button_classes.py:144-147`). `_filter_toggle` omits `cv_label_mode` (`tests/test1/test_button_leaves.py:574-576`). Replacing the literal with `cv_label_mode` without an `"icon"` fallback drops `context:secondary:icon` for any direct include. The live page is covered by `test_filter_toggle_resolves_icon_mode` (`tests/test1/test_button_class_label_mode.py:67-68`) only after the builder stamps `"icon"`. The default raw fixture will not catch this, because no default `context:secondary:icon` key exists.
- **MEDIUM — do not copy `action.html`'s else-as-label fallback.** `action.html:8` treats every non-icon, non-both value as text. This leaf's raw baseline is today's icon markup, including when the context has no mode. An `{% if cv_label_mode == "icon" %}` wrapper around the old branch fails that fixture; an else-as-label branch fails it too.
- **LOW — do not copy `cv_context_label_mode` into the filter dict.** The live wrapper passes `data.get("cv_context_label_mode")` as `target_default` (`base.py:643`). Filter data does not have that key today. Adding it would apply the list view's singular mode on the rendered page even if `get_context` itself omits the fourth argument.

### Suggestions
- Keep the current icon markup as the fallback for a missing mode, and pass `"icon"` into `cv_button_class` on that path. Pass `cv_label_mode` only for `both` and `label`.
- Put `{% load crud_views %}` first and wrap new branches around the existing icon-class tags. Those tags are currently unconditional on line 1; moving them must not change the icon-path bytes.
- In `both`, keep a space between the icon and the visible span, as `action.html:8` does, and do not put `data-cv-filter-icon` on the label span. `{% cv_icon %}` already emits `aria-hidden="true"` (`src/crud_views/lib/icons.py:220`).

### Risk Assessment
**MEDIUM.** The behavior is already in the resolver, template, and script. The plan fails only if the icon branch is reformatted or the hard-coded `"icon"` class argument is dropped for partial contexts.

## 03-02

The documentation plan names the right stale sentences, but its own verify command contradicts the edit it requires. As written, task 03-02-01 fails `pytest` if the executor follows the action text.

### Strengths
- The stale claims are real. `docs/reference/context_buttons.md:81-82` says the bundled filter template passes a literal `"icon"` because it is icon-only by construction. `docs/reference/buttons.md:304-306` repeats that. `docs/reference/action_menus.md:171-172` says neither the maps nor `CRUD_VIEWS_LABEL_MODE_DEFAULTS` change it. `docs/reference/javascript.md:83` and `:195-199` describe the filter toggle as always tooltip-marked and always icon-bearing. `docs/reference/icons.md:174-176` omits label mode.
- Linking `action_menus.md#context-label-mode-resolution` instead of copying the five-step list matches the existing heading (`docs/reference/action_menus.md:194` area; the test already requires that anchor at `tests/test1/test_label_mode_docs.py:194-201`).
- Fixed, not Breaking, is consistent with unchanged default English bytes. `LANGUAGE_CODE` is `en-us` (`tests/test1/conftest.py:98`), and `_("Filter")` stays `"Filter"` there. The escape hatch for a real break plus `docs/migrating-1.0.md` matches the repository rule.
- Full gates are actually listed, and failing ones must not be reported green. `CHANGELOG.md:147` already has an Unreleased `### Fixed` section to extend.

### Concerns
- **HIGH — 03-02-01 deletes a phrase its verify command pins.** `tests/test1/test_label_mode_docs.py:237` asserts that the Rendering section contains both `"filter toggle"` and `"outside this configuration"`. That phrase is the sentence at `docs/reference/action_menus.md:171-172`, which the task tells the executor to correct. `files_modified` does not include the test file. Following the action fails `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_label_mode_docs.py -q`. Keeping the phrase to go green leaves the old contract in the canonical rendering section.
- **MEDIUM — the floor change is a documented contract change, and the Fixed entry does not have to say so.** Today the docs promise that `CRUD_VIEWS_LABEL_MODE_DEFAULTS` does not affect this toggle (`action_menus.md:171-172`). After 03-01, `{"context": "both"}` or `{"context": "label"}` changes filter markup with no new setting. Default goldens stay identical, so Fixed is defensible, but a project that already set the context floor gets no migration bullet unless the executor independently decides it is Breaking. The task text only requires describing icon/both/label, the translated label, constant text, and unchanged defaults.
- **LOW — `docs/reference/buttons.md:221-222` still says the filter always falls back to two icon spans when `context:icon-host` is off.** That remains true for icon and both, and becomes false for label. The task names the "passes `"icon"`" sentence, not this paragraph. Nothing in `test_label_mode_docs.py` pins it, so the gate will not catch a miss.

### Suggestions
- Add `tests/test1/test_label_mode_docs.py` to `files_modified`. Replace the assertion at line 237 with the new contract: the filter follows the resolved context mode, has no target-view default, and is still never folded (`action_menus.md:184` should stay).
- In the Fixed entry, name both `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` and the context floor. State that default icon markup is unchanged and that an already-configured context floor now applies to this toggle.
- Qualify `buttons.md:221-222` the same way as `icons.md:174-176`: two-span fallback only in icon-bearing modes.

### Risk Assessment
**MEDIUM.** The prose scope is right, but the phase gate fails until the docs contract test is updated in the same task. That is a planning defect, not an open product decision.

## Cross-plan

03-01 can land without 03-02; the code requirements do not depend on the docs test. 03-02 cannot verify as written after 03-01, because correcting `action_menus.md:171-172` breaks `tests/test1/test_label_mode_docs.py:237`. No file overlap, and wave order is right. Phase risk is **MEDIUM**: implementation is grounded in existing seams; the docs plan will red-fail its own pytest unless that assertion is part of the edit.

---

## OpenCode Review (gemini-review)

## 03-01

### 1. Summary
Plan `03-01` implements label-mode resolution, three-way template rendering (`icon`, `both`, `label`), and runtime `gettext` translation for `FilterContextButton` and `context_action_filter.html`, backed by Python and Vitest regression suites. Grounded against the live source, the core mechanism is sound: stamping `cv_label_mode` inside `FilterContextButton.get_context()` before `_apply_label()` ensures both direct context callers and custom label templates receive the resolved mode, while `list.filter.js` already tolerates icon-less markup without production JS edits. The primary implementation risks lie in how `context_action_filter.html` handles missing or malformed `cv_label_mode` values when rendered outside `cv_button_data()`, and a subtle XPath pitfall in test assertions because `#cv-filter-toggle` wraps its icons in classless `<span data-cv-filter-icon="...">` elements.

### 2. Strengths
- **Stamping `cv_label_mode` in `FilterContextButton.get_context()` before `_apply_label()` (`src/crud_views/lib/view/buttons.py:323-333`, `src/crud_views/lib/view/base.py:640-646`):** `CrudView.cv_get_context()` (`base.py:640-646`) only stamps `cv_label_mode` *after* `_cv_get_action_context()` (`base.py:660`) has returned. Inside `FilterContextButton.get_context()`, `self._apply_label(data, context)` (`buttons.py:330`) invokes `self.render_label(data, context)` (`buttons.py:55-60`) before `cv_get_context()` ever runs. Stamping `data["cv_label_mode"] = context.view.cv_get_action_label_mode("context", self.key, self)` prior to `self._apply_label()` guarantees that both custom `label_template[_code]` snippets and direct `FilterContextButton().get_context(...)` callers (`tests/test1/test_context_button_template.py:56, 63`) see `cv_label_mode`.
- **Passing `(location="context", key=self.key, button=self)` with `target_default=None` (`src/crud_views/lib/view/base.py:299-322`):** In `CrudView.cv_get_action_label_mode()` (`base.py:312-322`), passing `self` explicitly avoids `cls._cv_find_context_button()` (`base.py:316`) missing an unregistered direct `FilterContextButton` instance, uses `self.key` (`buttons.py:303`) so subclass/custom keys like `key="search"` resolve against their own map entry, and leaves `target_default=None` so the list view's own `cv_context_action_label_mode` is never borrowed as a target default (satisfying D-01 and D-02).
- **Pre-edit raw byte baseline alongside normalized golden (`tests/test1/test_action_menus_golden.py:38-55`, `src/crud_views/templates/crud_views/tags/context_action_filter.html:1-14`):** `_canonical()` and `_norm()` in `test_action_menus_golden.py:38-55` sort attributes, sort `class` tokens, strip inter-tag whitespace (`re.sub(r">\s+<", "><", markup)`), and collapse whitespace runs. Because `test_toolbar_list_with_filter` (`test_action_menus_golden.py:130-132`) cannot detect whitespace drift or attribute/class reordering inside `context_action_filter.html:1-14`, capturing `RAW_DEFAULT_FILTER` in Task `03-01-01` before editing the template is essential to prove true byte-identity.
- **Zero-churn JS verification (`src/crud_views/static/crud_views/js/list.filter.js:15-38`, `tests/js/list.filter.test.js:46-133`):** Tracing `list.filter.js` confirms no production JS changes are needed:
  - `list.filter.js:15-17` runs `if (globalThis.cv.adapters.collapse.toggle(panel) === false) { return; }` before `button.setAttribute("aria-expanded", ...)` (`line 18`) and `fetch(...)` (`lines 34-38`).
  - `list.filter.js:22-30` checks `if (button.dataset.cvFilterIconOpen !== undefined)` and otherwise runs `button.querySelectorAll("[data-cv-filter-icon]").forEach(...)`, which is a safe no-op when `"label"` mode emits neither attribute nor icon spans.
  - `list.filter.js:26-27` executes `button.classList.remove(...(next ? open : close))` before `button.classList.add(...(next ? close : open))`, so shared base tokens between `open` and `close` (e.g., `"icon"`) are removed and immediately re-added on both swaps.
- **Anti-false-positive i18n checks (`tests/test1/test_i18n.py:35-45, 65-82`, `src/crud_views/locale/de/LC_MESSAGES/django.po`):** Because English `"Filter"` and German `"Filter"` are identical strings, Task `03-01-03` rightly requires checking `polib` non-fuzzy entry state (`test_i18n.py:66-73`), `GNUTranslations` compiled catalog key membership (`test_i18n.py:76-81`), and a monkeypatched non-ASCII `gettext` sentinel on `buttons.py`.

### 3. Concerns
- **[MEDIUM] XPath/CSS selector collision between icon wrapper `<span>`s and the visible label `<span>` (`src/crud_views/templates/crud_views/tags/context_action_filter.html:11-13`, `tests/test1/test_context_action_label_mode.py:43-44, 274-282`, `tests/test1/test_context_button_label_mode.py:35-38`):**
  - In `tags/button/action.html:8`, icons render as direct `<i aria-hidden="true">` children and the visible label renders as `<span>{{ cv_label }}</span>`. Existing test helpers in `test_context_button_label_mode.py:35-38` (`_is_text_only`) and `test_context_action_label_mode.py:43-44, 274-282` (`_has_icon_and_text`, `_icon_and_short_label`) therefore use `./*[@aria-hidden='true']` for icons and `./span[not(@class)]` for the visible label.
  - In `tags/context_action_filter.html:11-12`, however, element icons are wrapped in `<span data-cv-filter-icon="open">` and `<span data-cv-filter-icon="close">`—which are **direct `<span>` children without a `class` attribute**, while the `<i aria-hidden="true">` elements are grandchildren!
  - Consequently, on `#cv-filter-toggle`:
    1. `el.xpath("./*[@aria-hidden='true']")` is **always empty (`[]`)** even when element icons are present.
    2. `el.xpath("./span[not(@class)]")` matches the two `data-cv-filter-icon` spans in `"icon"` and `"both"` modes!
    3. Calling `_is_text_only(el)` from `test_context_button_label_mode.py:35` on `#cv-filter-toggle` in `"both"` mode will return `True` (a false positive) because `./*[@aria-hidden='true']` is `[]`, `title` is `None`, and `./span[not(@class)]` is non-empty!
- **[MEDIUM] Direct template renders or malformed `cv_label_mode` values bypass `cv_button_data()` normalization (`src/crud_views/templates/crud_views/tags/context_action_filter.html:1-14`, `src/crud_views/lib/view/button_data.py:85-94`, `src/crud_views/lib/view/base.py:312-322`):**
  - Ordinary action buttons pass through `cv_button_data()` (`button_data.py:85-94`), which normalizes missing/falsy `cv_label_mode` to `default_label_mode(location)` and validates malformed values via `_invalid_label_mode()` (raising `ValueError` in strict mode or logging once and falling back to the floor in non-strict mode, as tested in `tests/test1/test_context_action_label_mode.py:436-457`).
  - `FilterContextButton` renders `context_action_filter.html` directly via `CrudView.render_snippet()` (`src/crud_views/templatetags/crud_views.py:135-146`), and `CrudView.cv_get_action_label_mode()` (`base.py:313-321`) returns map/button values without calling `is_label_mode()`.
  - If `context_action_filter.html` branches with `{% if cv_label_mode != "label" %}` for icons and `{% if cv_label_mode == "icon" %}...{% else %}<span>{{ cv_action_label }}</span>{% endif %}` for the label, any direct template render omitting `cv_label_mode` (or passing an unvalidated value) will render a hybrid button (icon spans + visible label + no `title`/`data-cv-tooltip` + un-moded `cv_button_class`).
- **[LOW] Redundant `cv_get_action_label_mode()` call and evaluation on hidden/pinned filter contexts (`src/crud_views/lib/view/base.py:640-646`, `src/crud_views/lib/view/buttons.py:311-320`):**
  - Unlike `ParentContextButton` (`buttons.py:139`), `ChildContextButton` (`buttons.py:212`), and `SiblingContextButton` (`buttons.py:266`), which return `{}` when hidden, `FilterContextButton.get_context()` returns `{"cv_access": False}` (`buttons.py:311-319`), which is truthy.
  - When `CrudView.cv_get_context(key="filter", ..., location="context")` (`base.py:640-646`) runs on a non-filtered view or a view with `cv_filter_pinned = True`, `if location is not None and data:` is `True`, so `cv_get_context()` calls `self.cv_get_action_label_mode("context", "filter", button, None)` even though `cv_access` is `False` and `cv_resolve_action()` (`base.py:573, 593`) will immediately discard the dict. And when the filter *is* shown, `cv_get_action_label_mode()` is called once in `FilterContextButton.get_context()` and a second time in `CrudView.cv_get_context()`.

### 4. Suggestions
- In `tests/test1/test_filter_toggle_label_mode.py`, write dedicated DOM predicates for `#cv-filter-toggle` rather than reusing `_is_text_only` or `_has_icon_and_text` from `test_context_button_label_mode.py` / `test_context_action_label_mode.py`:
  - Select the visible label span with `./span[not(@class) and not(@data-cv-filter-icon)]`.
  - Select element icons with `./span[@data-cv-filter-icon]/i[@aria-hidden='true']`.
- In `src/crud_views/templates/crud_views/tags/context_action_filter.html`, make `"icon"` the default fallback branch when `cv_label_mode` is neither `"both"` nor `"label"` (and pass `cv_label_mode|default:"icon"` to `{% cv_button_class %}`), so direct template renders without `cv_label_mode` still produce valid `"icon"` markup while keeping byte-identical output for default renders.
- Consider validating or normalizing the resolved mode in `FilterContextButton.get_context()` (or in `cv_get_action_label_mode()`) with `is_label_mode()` / `_invalid_label_mode()` if non-strict recovery for malformed `FilterContextButton(label_mode=...)` or map entries is desired on parity with `cv_button_data()` (`src/crud_views/lib/view/button_data.py:88-94`).

### 5. Risk Assessment
- **Risk Level: LOW**
- **Justification:** The production code changes are confined to `FilterContextButton.get_context()` (`src/crud_views/lib/view/buttons.py:308-334`), `src/crud_views/templates/crud_views/tags/context_action_filter.html`, and `src/crud_views/locale/de/LC_MESSAGES/django.po`/`.mo`. Capturing raw pre-change template output in Task `03-01-01` before editing `context_action_filter.html` provides an immediate, deterministic guard against accidental markup or whitespace regressions.

---

## 03-02

### 1. Summary
Plan `03-02` updates five reference documentation files (`context_buttons.md`, `action_menus.md`, `buttons.md`, `javascript.md`, `icons.md`) and `CHANGELOG.md` to document the filter toggle's label-mode support, optional icon hooks, and translated default label, then runs the full project quality gates. While the documentation targets and `CHANGELOG.md` `### Fixed` classification are well-chosen, verification against `tests/test1/test_label_mode_docs.py` uncovered a **blocking test failure** that Task `03-02-01` will trigger because `test_label_mode_docs.py:237` explicitly asserts the old `"outside this configuration"` prose in `docs/reference/action_menus.md`, and `test_label_mode_docs.py` is not included in `03-02`'s `files_modified`.

### 2. Strengths
- **Complete inventory of stale "fixed icon" claims across reference docs (`docs/reference/context_buttons.md:77-82`, `docs/reference/action_menus.md:171-172`, `docs/reference/buttons.md:304-306`, `docs/reference/javascript.md:83, 187-199`, `docs/reference/icons.md:72-74, 153-155, 174-176`):** Task `03-02-01` catches every prose location where the filter toggle was previously described as hard-coding `"icon"`, always carrying a `context` tooltip marker, or unconditionally rendering two icons.
- **Single canonical resolution order (`docs/reference/action_menus.md:87-100`, `tests/test1/test_label_mode_docs.py:245-275`):** Linking `context_buttons.md` to `action_menus.md#context-label-mode-resolution` and `settings.md#label-mode-configuration` avoids duplicating the 5-step resolution list and aligns with the cross-link invariants enforced by `test_label_mode_docs.py:245-267`.
- **Accurate `CHANGELOG.md` classification (`CHANGELOG.md:147`, `superpowers/plans/2026-10-24-concept-review-followups.md:42`):** Recording `#262` under `### Fixed` in `CHANGELOG.md` matches the source phase plan (`Breaking: no (default stays icon)`) and respects the `CLAUDE.md` rule that only `### Breaking` entries require a companion update in `docs/migrating-1.0.md`.

### 3. Concerns
- **[HIGH] `tests/test1/test_label_mode_docs.py:236-238` asserts the exact stale prose in `docs/reference/action_menus.md:171-172` that Task `03-02-01` removes, but `test_label_mode_docs.py` is missing from `files_modified` and `<files>`:**
  - `docs/reference/action_menus.md:171-172` currently reads:
    `The filter toggle of filtered list views renders from its own template and is outside this configuration: neither the maps nor CRUD_VIEWS_LABEL_MODE_DEFAULTS change it.`
  - `tests/test1/test_label_mode_docs.py:236-238` (`test_canonical_label_mode_resolution_sections`) explicitly asserts:
    ```python
    rendering = _section(text, "### Rendering")
    assert "filter toggle" in rendering and "outside this configuration" in rendering
    assert "icon and short label in every mode" in rendering
    ```
  - Task `03-02-01` instructs the executor to correct that sentence in `docs/reference/action_menus.md` and then run `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_label_mode_docs.py -q` as its verification gate.
  - Because `tests/test1/test_label_mode_docs.py` is not in `03-02-PLAN.md` `files_modified` or Task `03-02-01` `<files>` / `<read_first>`, editing `docs/reference/action_menus.md:171-172` will immediately break `test_canonical_label_mode_resolution_sections` at `test_label_mode_docs.py:237`!
- **[MEDIUM] Mermaid flowchart in `docs/reference/context_buttons.md:247-249` still claims `nothing below applies (e.g. the filter toggle)`:**
  - In `docs/reference/context_buttons.md:247-249`, the diagram under `## How a context button is rendered` has:
    ```mermaid
    BTN --> OWN{"button has template<br/>or template_code?"}
    OWN -- "yes" --> CUSTOM(["your template renders the whole button,<br/>nothing below applies<br/>(e.g. the filter toggle)"])
    ```
  - Because `FilterContextButton` has a default `template` (`src/crud_views/lib/view/buttons.py:304-306`), this node sits *above* subgraphs `MODE ["1 · label mode"]` (`lines 253-259`) and `LABEL ["2 · label"]` (`lines 266-270`). Leaving `(e.g. the filter toggle)` on `nothing below applies` contradicts the new behavior where `FilterContextButton` resolves its mode through `1 · label mode` (steps M1, M2, M3, and `MICON`) and its label through `2 · label`, and custom templates receive `cv_label_mode`.
  - Note also that `tests/test1/test_label_mode_docs.py:277-287` parses `## How a context button is rendered` and asserts exact invariants on `MICON` and the first paragraph after the diagram (`below.strip().split("\n\n")[0]`); any edits to that section must keep those assertions green.
- **[MEDIUM] `FilterContextButton` is not exported from `crud_views.lib.view` (`src/crud_views/lib/view/__init__.py:1-17`, `docs/reference/context_buttons.md:502-507`):**
  - `src/crud_views/lib/view/__init__.py:2` exports `ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton`, but **not** `FilterContextButton` (which lives in `crud_views.lib.view.buttons`, as seen in `tests/test1/test_context_button_template.py:7`).
  - Task `03-02-01` adds `FilterContextButton(label_mode="label")` and `FilterContextButton(key="search")` examples to `docs/reference/context_buttons.md`. If those examples omit the import or imply `from crud_views.lib.view import FilterContextButton` (matching `docs/reference/context_buttons.md:31, 103, 114, 179, 505`), users copying the example will hit `ImportError: cannot import name 'FilterContextButton' from 'crud_views.lib.view'`.

### 4. Suggestions
- Add `tests/test1/test_label_mode_docs.py` to `03-02-PLAN.md` `files_modified`, Task `03-02-01` `<files>`, and Task `03-02-01` `<read_first>`, and update `test_canonical_label_mode_resolution_sections` (`tests/test1/test_label_mode_docs.py:236-238`) to assert the updated filter-toggle rendering contract in `docs/reference/action_menus.md` instead of `"outside this configuration"`.
- In Task `03-02-01`, update the `CUSTOM` node in the Mermaid diagram of `docs/reference/context_buttons.md:248` (e.g., remove `(e.g. the filter toggle)` or clarify that `cv_label_mode` is still resolved while the custom/filter template owns its markup) while preserving the `MICON` node and first-paragraph invariants checked by `tests/test1/test_label_mode_docs.py:277-287`.
- In `docs/reference/context_buttons.md`, explicitly show `from crud_views.lib.view.buttons import FilterContextButton` in the `FilterContextButton` section and under `## Import Paths` (`docs/reference/context_buttons.md:502-507`).

### 5. Risk Assessment
- **Risk Level: MEDIUM**
- **Justification:** Although Plan `03-02` only touches documentation and release notes, `tests/test1/test_label_mode_docs.py:237` is a hard automated gate in Task `03-02-01` that will deterministically fail when `docs/reference/action_menus.md:171-172` is updated unless `tests/test1/test_label_mode_docs.py` is added to the plan's scope and updated in tandem.

---

## Cross-Plan Comparison and Overall Assessment

- **Wave & Dependency Ordering:** Wave 1 (`03-01`) → Wave 2 (`03-02`) has clean separation of concerns with zero file overlap between plans. `03-01` lands all runtime, template, catalog, and behavior test changes; `03-02` updates documentation and `CHANGELOG.md` and runs the full phase verification gates.
- **Requirement Coverage:** All four phase requirements (`FILT-01`, `FILT-02`, `FILT-03`, `FILT-04`) and locked decisions (`D-01` through `D-11`) are accounted for across the five tasks.
- **Top Action Items Before Execution:**
  1. **Must-fix in `03-02`:** Add `tests/test1/test_label_mode_docs.py` to `03-02-PLAN.md` (`files_modified` and Task `03-02-01` `<files>`/`<read_first>`) and update line 237 (`assert "filter toggle" in rendering and "outside this configuration" in rendering`) to match the new `docs/reference/action_menus.md` prose.
  2. **Watch out in `03-01`:** Ensure `tests/test1/test_filter_toggle_label_mode.py` distinguishes `<span data-cv-filter-icon="...">` from the visible label `<span>` (`./span[not(@class) and not(@data-cv-filter-icon)]`), and ensure `context_action_filter.html` defaults to `"icon"` when `cv_label_mode` is unset.
  3. **Watch out in `03-02`:** Show the exact import path `from crud_views.lib.view.buttons import FilterContextButton` in `docs/reference/context_buttons.md` (since `crud_views.lib.view.__init__.py` does not re-export `FilterContextButton`), and update the Mermaid `CUSTOM` node at `docs/reference/context_buttons.md:248`.

---

## OpenCode Review (deepseek-review)

I'll review the plans by examining the actual codebase to verify their claims. Let me start by reading the relevant files mentioned in the plans.
Now let me examine the actual source files mentioned in the plan to verify the claims:
Let me check the current state of `cv_get_action_label_mode` in `base.py`:
Let me read the actual implementation:
Let me search for the specific function:
Now let me check the filter template:
Now let me check if there's an existing test file for filter toggle:
Let me check if there's already a test for filter toggle label mode:
Now let me check the current state of the documentation files:
Now let me check the action_menus.md file:
Now let me check the buttons.md file:
Now let me check if there's a plan 03-02:
Now let me examine the current state of the JavaScript file:
Now let me check the German locale:
Let me check if "Filter" is already translated:
Now let me check if there are any existing tests for filter toggle:
Now let me check the test files mentioned in the plan to understand the current state:
Now let me run a quick check to understand the current state of the codebase:
Let me check the current state of the code by reading files directly. Based on my examination of the actual codebase, I can now provide a review.

## 03-01

**Summary** — This plan implements filter toggle label mode support by modifying `FilterContextButton.get_context()` to use `cv_get_action_label_mode()` and adding mode-specific rendering to the filter template. It correctly addresses the core requirements (FILT-01 through FILT-04) and follows the design decisions (D-01 through D-11).

**Strengths**
- **Accurate technical analysis**: Plan correctly identifies that `cv_get_action_label_mode()` exists in `src/crud_views/lib/view/base.py:299-328` and understands its precedence logic
- **Good test strategy**: Capturing raw baseline strings before implementation prevents accidental regression
- **Proper integration**: Uses existing resolver without creating new APIs, maintains customization hooks
- **Security awareness**: Maintains Django escaping and CSRF protection
- **Localization approach**: Correctly identifies that German translation needs to be added to PO file

**Concerns** (MEDIUM)
1. **Missing validation for `cv_label_mode` in template**: The plan modifies `context_action_filter.html` but doesn't specify how to handle invalid or missing `cv_label_mode` values. Should follow same validation as other templates.
2. **Potential golden test fragility**: The plan mentions `toolbar_publisher_list.html` golden should remain byte-identical, but golden comparisons normalize whitespace (`tests/test1/test_action_menus_golden.py:38-55`). This could hide actual template changes.
3. **Incomplete JS test coverage**: While plan mentions extending `tests/js/list.filter.test.js`, it doesn't specify how to test the `label` mode with no icon spans - needs specific assertion that `[data-cv-filter-icon]` selector returns empty NodeList.

**Suggestions**
1. Add explicit check in Task 1: after adding `cv_label_mode = ...`, verify it's one of `{"icon", "both", "label"}` or falls back to default
2. Update verification to include `test_template_a11y.py` which tests accessible markup
3. Add explicit test for `label` mode ensuring no `data-cv-filter-icon-open/close` attributes are rendered

**Risk Assessment**: MEDIUM - Implementation is straightforward but edge cases around template validation and backward compatibility need careful handling.

## 03-02

**Summary** — This documentation update plan correctly identifies all documentation files that need updating and provides clear update instructions.

**Strengths**
- **Complete doc coverage**: Identifies all 5 documentation files that mention filter toggle behavior
- **Correct technical understanding**: Recognizes that `context_buttons.md:77-82`, `buttons.md:304-306`, `action_menus.md:168-184`, and `javascript.md:83,187-202` need updates
- **Proper changelog approach**: Uses "Fixed" classification since default output remains unchanged
- **Quality gate awareness**: Includes all required validation commands

**Concerns** (LOW)
1. **Missing reference to `icons.md`**: Plan mentions updating `icons.md` but doesn't specify what needs changing there
2. **Potential documentation inconsistency**: If Phase 1 implementation changes but documentation references don't match exactly, could cause confusion
3. **No mention of translation documentation**: Should document that "Filter" is now translatable

**Suggestions**
1. Add specific note about what to update in `icons.md` - likely the description of filter rendering two icons
2. Include verification that all cross-references between docs still work
3. Add note to documentation about translation of "Filter" label

**Risk Assessment**: LOW - Documentation updates are straightforward and the plan correctly identifies all necessary changes.

## Overall Risk Assessment

**MEDIUM** - The implementation risk is moderate due to template changes needing to maintain backward compatibility. The main risks are:
1. Template changes breaking existing custom templates that override `context_action_filter.html`
2. Golden tests potentially passing even with minor whitespace changes
3. JavaScript interaction needing to work correctly in `label` mode with no icons

However, the plans are well-researched and grounded in actual code inspection. The phased approach (implementation then documentation) is sound. The dependency on Phase 1 (label mode defaults) is correctly identified and handled.

**Key verification points**:
- `src/crud_views/lib/view/buttons.py:326` shows `data["cv_action_label"] = "Filter"` hardcoded - needs `_("Filter")`
- `src/crud_views/templates/crud_views/tags/context_action_filter.html` hardcodes `"icon"` mode in `cv_button_class` call - needs `cv_label_mode`
- No `cv_label_mode` currently stamped in `FilterContextButton.get_context()` - needs to be added
- German PO file lacks "Filter" translation - needs to be added

---

## Consensus Summary

### Agreed Strengths

- All reviewers endorse reusing the resolver and stamping `cv_label_mode` before custom labels; the current outer
  wrapper stamps too late for those templates (`src/crud_views/lib/view/buttons.py:330`, `src/crud_views/lib/view/base.py:640`).
- The production JavaScript already supports absent icons and collapse-first failure behavior. Tests can extend
  coverage without changing it (`src/crud_views/static/crud_views/js/list.filter.js:15`, `:29`, `:38`).
- Raw pre-change fixtures complement the normalized toolbar golden, whose normalization cannot establish byte identity
  (`tests/test1/test_action_menus_golden.py:38`). The locale membership/sentinel approach avoids identical-string false positives.
- The implementation → documentation wave order is sound, and the Fixed classification is supported by the source plan.

### Agreed Concerns

- **H1 — HIGH, confirmed, unresolved (Fable, Grok, Gemini):** 03-02 corrects the obsolete “outside this configuration”
  filter documentation, then runs a test that requires those exact words. `tests/test1/test_label_mode_docs.py:237`
  asserts the old phrase in the Rendering section; `docs/reference/action_menus.md:171` contains it.
  `03-02-PLAN.md:99` requires correcting it, `:111` runs the affected test, and the test is absent from `files_modified`
  (`:7`) and the task's files (`:88`). Add that test file to scope and replace its old assertion with the new filter
  contract while preserving the existing canonical-resolution and never-folded checks. Source inspection independently
  confirms the existence-class assertion; no test execution was needed to establish the conflict.
- **A1 — MEDIUM, unresolved (all four):** the plans do not settle absent/malformed `cv_label_mode` behavior on the
  specialized leaf. A missing value can change both body mode and mode-specific classes for direct template callers;
  malformed configured values bypass the ordinary button-data normalizer. Define the missing/unknown/invalid policy,
  keep an unchanged raw fixture without the key, and test distinct `context:secondary:icon` classes on that path.
  Evidence: `src/crud_views/lib/button_classes.py:144`, `src/crud_views/lib/view/button_data.py:85`,
  `tests/test1/test_button_leaves.py:574`. Valid modes and a bad *floor* are already planned; they do not answer this.

### Divergent Views

- DeepSeek calls the normalized golden and icon-less tests insufficient, but 03-01 already requires separate raw
  fixtures, zero icon hooks and a real-handler label-only matrix. Those are existing plan requirements, not open work.
- Missing-mode compatibility and malformed-mode validation need separate policy statements inside A1. Fable/Grok
  favor legacy icon fallback for direct contexts; Gemini/DeepSeek also ask about parity with strict/log recovery for
  malformed configured values. Do not infer that one fallback automatically satisfies both contracts.
- Gemini calls out the extra resolver call and hidden truthy contexts; Fable explicitly judges the extra call negligible.
  The hidden-context wrapper behavior already exists. A11 asks for an explicit scope decision, not a wrapper rewrite.
- Fable questions test volume; 03-01 explicitly retains all 14 edge predicates and says the request cases assert local
  behavior rather than backend ordering (`03-01-PLAN.md:233`, `:315`). Treat that recommendation as already addressed by
  the stated coverage intent; no new ordering guarantee or mandatory test reduction follows.

### Remaining actionable MEDIUM/LOW findings

These are unique action groups, deduplicated across reviewers. Each remains visible here until incorporated into a
PLAN task/acceptance criterion or explicitly deferred/rejected there. Scope-sensitive advice asks for a decision,
not automatic expansion of production work.

| ID | Severity | Reviewers | Required PLAN change |
|---|---|---|---|
| A1 | MEDIUM | All four | Define absent/unknown/malformed mode policy, preserve a mode-less raw render, and test explicit icon-mode class lookup; distinguish malformed configuration recovery from direct-template compatibility. |
| A2 | MEDIUM | Fable | Give Task 03-01-01 the snapshot-map monkeypatch target (`crud_views_settings.context_actions_label_mode`) and isolated class-override method. `override_settings` works for the lazy floor/class map, not the captured action map. Use its signal-reset path or explicit registry restoration, rather than assuming cache-reset alone restores registered classes. |
| A3 | MEDIUM | Gemini | Require filter-specific DOM predicates: exclude `[data-cv-filter-icon]` wrappers from visible-label selectors and inspect descendant icons. Generic action helpers can falsely classify both mode as text-only (`tests/test1/test_context_button_label_mode.py:35`). |
| A4 | LOW | Fable | Bound the i18n truth: a German page render shows active-language behavior; PO/MO membership proves the shipped catalog, and a sentinel proves runtime gettext. Do not claim that identical rendered text proves which merged catalog supplied it. |
| A5 | LOW | Fable | Explain in the raw-baseline test/docstring that `render_to_string` byte identity intentionally includes boundary whitespace removed by `CrudView.render_snippet` (`src/crud_views/lib/view/base.py:371`). |
| A6 | LOW | Fable, Grok | Specify visible icon-to-label spacing for both mode, consistent with the action leaf, while leaving icon-mode bytes intact. |
| A7 | MEDIUM | Fable, Grok, Gemini | Name the remaining doc edits: the CUSTOM Mermaid node at `context_buttons.md:248`, an insertion point preserving the first paragraph checked at `test_label_mode_docs.py:277`, and the icon-bearing-only host fallback qualifier at `buttons.md:221`. |
| A8 | MEDIUM | Gemini | Give the new examples their actual import, `from crud_views.lib.view.buttons import FilterContextButton`, and update the Import Paths section if appropriate; `crud_views.lib.view` does not export it (`src/crud_views/lib/view/__init__.py:2`). |
| A9 | MEDIUM | Grok, Fable | Explicitly describe that an already-configured context floor now affects the filter, and deliberately add or defer a copied-filter-template migration-checklist note. A Fixed entry need not become Breaking for this documentation decision. |
| A10 | LOW | Fable | Record the current landing branch and the session-authorized branch exception in the execution-summary instructions; do not silently apply PROJECT.md's per-phase branch list or change branches. |
| A11 | LOW | Gemini (Fable: negligible) | Explicitly retain/defer or address the duplicate wrapper resolution and pre-existing hidden-context evaluation. Preserve the no-target-default and early-visibility contract; the feedback does not require changing the generic wrapper. |

### Already incorporated or non-actionable feedback

| Finding | Existing plan coverage / source adjudication |
|---|---|
| DeepSeek: normalized golden cannot prove raw bytes | 03-01:155–160 requires raw fixtures before production edits and keeps normalized goldens separate. |
| DeepSeek: missing label-only/zero-icon JS coverage | 03-01:202–203, :207–211, :225–235 explicitly requires icon-less fixtures, no hooks, real handler and label/node checks. |
| DeepSeek: icons.md update unspecified | 03-02:105 expressly qualifies the two-icon description by mode and placement. A7 separately captures the additional buttons.md paragraph. |
| DeepSeek: translation documentation missing | 03-02:96 expressly states the default Filter label is translated. |
| DeepSeek: docs cross-link verification and Phase 1 consistency | 03-02:89, :94, :106–117 requires source reading, canonical links, strict MkDocs and behavior comparison. |
| DeepSeek: add the accessibility suite | 03-02:182 already runs the full Python test suite; 03-01:211–212 requires ARIA and no-title behavior. |
| Grok: never add cv_context_label_mode target default | 03-01:26, :104–106, :165–168 explicitly rejects a target default; direct and rendered conflict tests are required at :245–248. |
| Grok: preserve template tag/whitespace ordering | 03-01:169–173 explicitly preserves exact icon-branch bytes and forbids reformatting it. |
| Fable: keep English custom-label test passing | 03-01:276 already runs test_context_button_template.py; :281–282 retains default English raw/golden assertions. |
| Fable: simplify deferred-request test rows | 03-01:233–237 and :315 deliberately retain local-state regression coverage with no server-ordering promise. |
| Fable: admin probably supplies Filter translation | Reviewer explicitly could not verify that catalog. Treat it as an open provenance caveat under A4, never a confirmed missing/override defect. |
| Fable: class-cache leakage | Conditional risk, not an observed leak: `src/crud_views/lib/button_classes.py:111` already resets on CRUD_VIEWS_BUTTON_CLASSES setting changes. A2 requires choosing the existing isolated mechanism; no new cache subsystem is needed. |

### Cycle outcome and consensus gate

Four source-citing reviewers completed. The only HIGH is corroborated by three reviewers and independently
confirmed in source, so the consensus gate does not suppress it. No past-review HIGHs or risk-assessment labels
are counted as new findings. Eleven distinct non-HIGH action groups remain unincorporated; raw reviewer repeats
already covered by a plan are excluded as listed above. No review finding is claimed resolved by implementation.

`CYCLE_SUMMARY: current_high=1 current_actionable=11`

## Verification coverage

The source-grounding and cross-artifact passes ran independently of the external review. No product suites ran.
`drift-guard authority --raw` returned **intel**, even though project config contains a grep preference. The effective
CLI authority is used unchanged. `.planning/intel/API-SURFACE.md:5` declares its inventory incomplete and
`api-map.json` is absent. Python declarations, Python signatures, Django template semantics, browser APIs and CLI
signatures are therefore **UNCHECKABLE**, never MISSING because of the empty index. Direct source reads below
provide supplemental existence/mechanism evidence; they do not upgrade semantic or signature validation.

The `drift-guard severity` seam was called with effective authority `intel` for every used verdict class:
VERIFIED → none/false; UNCHECKABLE → INFO/false; MISSING → needs-acknowledgement/false;
AMBIGUOUS → MEDIUM/false (`severity`/`hardBlock`). No missing or ambiguous source declaration was found by
supplemental inspection. No hard block or author acknowledgement is triggered. File presence is directly checked
on the filesystem, independent of language analysis.

### Cited path inventory

Each unique literal path has a quoted plan occurrence; repeated citations refer to the same checked artifact.
Generated paths are excluded only where the plans explicitly say they are produced. Existing modified files remain checked.

| Path | Plan evidence | Verdict | Evidence |
|---|---|---|---|
| `.planning/PROJECT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:92` — “@.planning/PROJECT.md” | VERIFIED | Filesystem presence; `.planning/PROJECT.md:1` |
| `.planning/ROADMAP.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:93` — “@.planning/ROADMAP.md” | VERIFIED | Filesystem presence; `.planning/ROADMAP.md:1` |
| `.planning/STATE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:94` — “@.planning/STATE.md” | VERIFIED | Filesystem presence; `.planning/STATE.md:1` |
| `.planning/phases/02-form-key-grammar/deferred-items.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:127` — “<read_first>CHANGELOG.md Unreleased Fixed; docs/migrating-1.0.md; .planning/PROJECT.md quality gates; .planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md; .planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md environment caveats; .planning/phases/02-form-key-grammar/deferred-items.md</read_first>” | VERIFIED | Filesystem presence; `.planning/phases/02-form-key-grammar/deferred-items.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:326` — “Create .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md with baseline capture commit/source HEAD,” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `.planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:77` — “It produces .planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md as its execution report, including the” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:95` — “@.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:97` — “@.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:96` — “@.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:98` — “@.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:99` — “@.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md:1` |
| `.venv/bin/mkdocs` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:109` — “<automated>.venv/bin/mkdocs build --strict</automated>” | VERIFIED | Filesystem presence; `.venv/bin/mkdocs` (binary/executable, no text line) |
| `.venv/bin/pytest` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:145` — “<precondition>The Phase 1 cv_get_action_label_mode and default_label_mode implementations exist in the tracked view modules, and .venv/bin/pytest plus the installed npm test harness are runnable.</precondition>” | VERIFIED | Filesystem presence; `.venv/bin/pytest` (binary/executable, no text line) |
| `.venv/bin/ruff` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:188` — “<automated>.venv/bin/ruff check</automated>” | VERIFIED | Filesystem presence; `.venv/bin/ruff` (binary/executable, no text line) |
| `/home/alex/.codex/gsd-core/templates/summary.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:88` — “@/home/alex/.codex/gsd-core/templates/summary.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/templates/summary.md:1` |
| `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:87` — “@/home/alex/.codex/gsd-core/workflows/execute-plan.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/workflows/execute-plan.md:1` |
| `CHANGELOG.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:13` — “- CHANGELOG.md” | VERIFIED | Filesystem presence; `CHANGELOG.md:1` |
| `CLAUDE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `CLAUDE.md:1` |
| `docs/migrating-1.0.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:127` — “<read_first>CHANGELOG.md Unreleased Fixed; docs/migrating-1.0.md; .planning/PROJECT.md quality gates; .planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md; .planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md environment caveats; .planning/phases/02-form-key-grammar/deferred-items.md</read_first>” | VERIFIED | Filesystem presence; `docs/migrating-1.0.md:1` |
| `docs/reference/action_menus.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:9` — “- docs/reference/action_menus.md” | VERIFIED | Filesystem presence; `docs/reference/action_menus.md:1` |
| `docs/reference/buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:10` — “- docs/reference/buttons.md” | VERIFIED | Filesystem presence; `docs/reference/buttons.md:1` |
| `docs/reference/context_buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:8` — “- docs/reference/context_buttons.md” | VERIFIED | Filesystem presence; `docs/reference/context_buttons.md:1` |
| `docs/reference/icons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:12` — “- docs/reference/icons.md” | VERIFIED | Filesystem presence; `docs/reference/icons.md:1` |
| `docs/reference/javascript.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:11` — “- docs/reference/javascript.md” | VERIFIED | Filesystem presence; `docs/reference/javascript.md:1` |
| `settings_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:255` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `settings_i18n.py:1` |
| `src/crud_views/lib/view/base.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:61` — “to: src/crud_views/lib/view/base.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/base.py:1` |
| `src/crud_views/lib/view/buttons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:8` — “- src/crud_views/lib/view/buttons.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/buttons.py:1` |
| `src/crud_views/lib/views/mixins.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:73` — “to: src/crud_views/lib/views/mixins.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/views/mixins.py:1` |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:11` — “- src/crud_views/locale/de/LC_MESSAGES/django.mo” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.mo` (binary/executable, no text line) |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:10` — “- src/crud_views/locale/de/LC_MESSAGES/django.po” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.po:1` |
| `src/crud_views/static/crud_views/js/list.filter.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:69` — “to: src/crud_views/static/crud_views/js/list.filter.js” | VERIFIED | Filesystem presence; `src/crud_views/static/crud_views/js/list.filter.js:1` |
| `src/crud_views/templates/crud_views/tags/button/action.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/button/action.html:1` |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:9` — “- src/crud_views/templates/crud_views/tags/context_action_filter.html” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/context_action_filter.html:1` |
| `src/crud_views/templatetags/crud_views.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:65` — “to: src/crud_views/templatetags/crud_views.py” | VERIFIED | Filesystem presence; `src/crud_views/templatetags/crud_views.py:1` |
| `taskfile.yaml` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:255` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `taskfile.yaml:1` |
| `tests/js/list.filter.test.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:16` — “- tests/js/list.filter.test.js” | VERIFIED | Filesystem presence; `tests/js/list.filter.test.js:1` |
| `tests/lib/helper/icons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:196` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/lib/helper/icons.py:1` |
| `tests/test1/test_action_menus_context.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:237` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_context.py:1` |
| `tests/test1/test_action_menus_golden.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_golden.py:1` |
| `tests/test1/test_button_class_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:196` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_button_class_label_mode.py:1` |
| `tests/test1/test_button_leaves.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:13` — “- tests/test1/test_button_leaves.py” | VERIFIED | Filesystem presence; `tests/test1/test_button_leaves.py:1` |
| `tests/test1/test_context_action_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:14` — “- tests/test1/test_context_action_label_mode.py” | VERIFIED | Filesystem presence; `tests/test1/test_context_action_label_mode.py:1` |
| `tests/test1/test_context_button_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:196` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_label_mode.py:1` |
| `tests/test1/test_context_button_template.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_template.py:1` |
| `tests/test1/test_filter.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:237` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_filter.py:1` |
| `tests/test1/test_filter_pinned.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:196` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_filter_pinned.py:1` |
| `tests/test1/test_filter_toggle_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:12` — “- tests/test1/test_filter_toggle_label_mode.py” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `tests/test1/test_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:15` — “- tests/test1/test_i18n.py” | VERIFIED | Filesystem presence; `tests/test1/test_i18n.py:1` |
| `tests/test1/test_label_mode_docs.py` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:111` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_label_mode_docs.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_label_mode_docs.py:1` |

### Cited declaration and field inventory

Each row is separately UNCHECKABLE under the incomplete effective intel index, with direct source evidence for
reviewer claim adjudication. Declaration existence is observed; method signatures and runtime behavior are not
certified by grep or this index. No decorator is cited as an existing dependency (the plans' `@path` entries are
context includes). There are no dataclass/struct fields; the field rows below are Pydantic attributes/context keys.

| Symbol | Quoted plan reference | Effective-authority verdict | Supplemental declaration/context evidence |
|---|---|---|---|
| `FilterContextButton` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:26` — “- "EDGE-FILT-01-empty: A None button mode and an empty or unrelated view map reach the live context floor; the selected view map replaces lower maps. Direct FilterContextButton instances use their own override and declared key, never the list view's singular target default (D-01, D-02)."” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:298` — “class FilterContextButton(ContextButton):” |
| `FilterContextButton.get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:308` — “def get_context(self, context: ViewContext) -> dict:” |
| `CrudView` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:104` — “CrudView.cv_get_action_label_mode(location, key, button=None, target_default=None) returns a mode. For context,” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:61` — “class CrudView(metaclass=CrudViewMetaClass):” |
| `cv_get_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:44` — “contains: "cv_get_action_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:299` — “def cv_get_action_label_mode(” |
| `cv_get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:624` — “def cv_get_context(” |
| `cv_context_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:93` — “no target view and therefore ignores the current list view's singular cv_context_action_label_mode (D-01/D-02).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:100` — “cv_context_action_label_mode: str \| None = None” |
| `ViewContext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/context.py:9` — “class ViewContext(BaseModel, arbitrary_types_allowed=True):” |
| `_apply_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:61` — “def _apply_label(self, data: dict, context: ViewContext) -> None:” |
| `_apply_variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:74` — “def _apply_variant(self, data: dict) -> None:” |
| `_inject_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:79` — “def _inject_template(self, data: dict) -> None:” |
| `cv_button_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:525` — “def cv_button_class(location, slot, mode=None):” |
| `cv_icon_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:519` — “def cv_icon_class(value, location):” |
| `cv_icon` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:513` — “def cv_icon(value, css=""):” |
| `cv_context_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:162` — “cv_context_action rendering path and the existing session POST/GET path. Observe its behavioral failure before” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:228` — “def cv_context_action(context, key, obj=None):” |
| `ListViewTableFilterMixin` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:299` — “class ListViewTableFilterMixin(FilterView):” |
| `ListViewTableFilterMixin.post` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:336` — “def post(self, request, *args, **kwargs):” |
| `cv_filter_expanded` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:323` — “def cv_filter_expanded(self) -> bool:” |
| `default_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:145` — “<precondition>The Phase 1 cv_get_action_label_mode and default_label_mode implementations exist in the tracked view modules, and .venv/bin/pytest plus the installed npm test harness are runnable.</precondition>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/label_mode.py:84` — “def default_label_mode(location: str) -> str:” |
| `HOST_LIBRARY` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:210` — “otherwise render the existing two children, including a host icon's standalone form (D-03). Use HOST_LIBRARY and” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:3` — “HOST_LIBRARY = {” |
| `HOST_ICONS` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:211` — “HOST_ICONS from the existing helper, and test both mixed directions plus empty/None host-slot configuration.” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:7` — “HOST_ICONS = {” |
| `ELIGIBLE` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:222` — “Replace the obsolete fixed-filter-mode comment beside ELIGIBLE in test_context_action_label_mode.py with a precise” | UNCHECKABLE / INFO | `tests/test1/test_context_action_label_mode.py:251` — “ELIGIBLE = './*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]'” |
| `_filter_toggle` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:148` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_button_leaves.py:574` — “def _filter_toggle(expanded: bool):” |
| `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:91` — “Add a compact filter section to context_buttons.md with CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:67` — “context_actions_label_mode: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", default={})” |
| `label_template_code` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:39` — “- "EDGE-FILT-04-encoding: Render-time gettext is proved by a distinct Unicode sentinel, active German rendering uses the compiled catalog, and label_template/label_template_code still override the translated default (D-07, D-09)."” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:29` — “label_template_code: str \| None = None” |
| `label_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:39` — “- "EDGE-FILT-04-encoding: Render-time gettext is proved by a distinct Unicode sentinel, active German rendering uses the compiled catalog, and label_template/label_template_code still override the translated default (D-07, D-09)."” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:28` — “label_template: str \| None = None” |
| `template_code` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:217` — “test-local in-memory templates for file-based custom labels and whole-button overrides, alongside template_code;” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:31` — “template_code: str \| None = None” |
| `label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:201` — “- Renamed search buttons use search map entries even when filter conflicts; unregistered direct instances retain label_mode; valid explicit modes bypass an invalid strict floor.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:33` — “label_mode: str \| None = None  # None: the view's context label-mode maps; one of LABEL_MODES (#264)” |
| `variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:219` — “priority. Cover both label_template mechanisms, variant mode keys and an empty custom label's fallback (D-07).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:32` — “variant: str \| None = None  # None: the target view's cv_action_variant” |
| `self.key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:303` — “key: str = "filter"” |
| `cv_access` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:311` — “dict_kwargs = {"cv_access": False}” |
| `cv_key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:325` — “data["cv_key"] = self.key” |
| `cv_action_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:326` — “data["cv_action_label"] = "Filter"” |
| `cv_icon_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:327` — “data["cv_icon_action"] = "filter"” |
| `cv_url` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:329` — “data["cv_url"] = list_url” |
| `cv_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:47` — “contains: "cv_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:645` — “data = {**data, "cv_label_mode": mode, "cv_action_key": key}” |
| `target_default` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:300` — “cls, location: str, key: str, button: ContextButton \| None = None, target_default: str \| None = None” |
| `gettext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:38` — “- "EDGE-FILT-04-empty: The core German PO contains a non-fuzzy translated Filter entry and the compiled catalog contains the key explicitly; a missing entry cannot pass through gettext's identical-string fallback (D-09)."” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:95` — “def gettext(message):” |
| `override_settings` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:215` — “matrix tests, monkeypatch for snapshot-style existing action maps and override_settings for the live floor.” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/test/utils.py:468` — “class override_settings(TestContextDecorator):” |
| `translation.override` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:266` — “call with a different sentinel and custom-label precedence. Use translation.override("de") for the authenticated” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:189` — “class override(ContextDecorator):” |
| `render_to_string` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:158` — “compare render_to_string output directly: retain leading/trailing whitespace, attribute ordering and class ordering.” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/template/loader.py:52` — “def render_to_string(template_name, context=None, request=None, using=None):” |

### Explicitly produced symbols (skipped)

- `_publisher_view` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; skipped because the Artifacts section declares creation.
- `_render_filter` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; skipped because the Artifacts section declares creation.
- `_filter_node` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; skipped because the Artifacts section declares creation.
- `RAW_DEFAULT_FILTER` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; skipped because the Artifacts section declares creation.
- `test_filter_raw_default_bytes` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; skipped because the Artifacts section declares creation.
- `test_filter_both_tracer` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:50` — “contains: "test_filter_both_tracer"”; skipped because the Artifacts section declares creation.
- `test_filter_mode_placement_matrix` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; skipped because the Artifacts section declares creation.
- `test_filter_host_slot_fallback` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; skipped because the Artifacts section declares creation.
- `test_filter_mode_resolution` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; skipped because the Artifacts section declares creation.
- `test_filter_declared_key_and_direct_button` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; skipped because the Artifacts section declares creation.
- `test_filter_live_floor` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, and test_filter_label_escaping;”; skipped because the Artifacts section declares creation.
- `test_filter_customization` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, and test_filter_label_escaping;”; skipped because the Artifacts section declares creation.
- `test_filter_visibility` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, and test_filter_label_escaping;”; skipped because the Artifacts section declares creation.
- `test_filter_label_escaping` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, and test_filter_label_escaping;”; skipped because the Artifacts section declares creation.
- `test_filter_catalog_entry` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:125` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; skipped because the Artifacts section declares creation.
- `test_filter_gettext_at_render_time` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:125` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; skipped because the Artifacts section declares creation.
- `test_filter_german_render` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:126` — “test_filter_german_render; existing JS fixtures gain mode/label/initial-state options and described behavior cases.”; skipped because the Artifacts section declares creation.

### Additional coverage limits and shared contracts

- All signatures in 03-01:103–113 (`CrudView.cv_get_action_label_mode`, `FilterContextButton.get_context`,
  `_apply_label`, `_apply_variant`, `_inject_template`, `cv_button_class`, `cv_icon_class`,
  `ListViewTableFilterMixin.post`) are UNCHECKABLE under intel; direct declaration lines above are evidence of names only.
- `gettext.GNUTranslations` (03-01:264), `polib` (03-01:263), and `translation.override` (03-01:266) are
  UNCHECKABLE external Python APIs. Existing use is present at `tests/test1/test_i18n.py:66`, `:68`, `:81`, `:88`.
- `NodeList` (03-01:113), `querySelectorAll`/`textContent`/DOM node identity (03-01:35, :229) and promises are
  UNCHECKABLE browser semantics under the empty intel index. Supplemental source `list.filter.js:29` iterates
  an optionally empty icon collection; `:39` persists a captured boolean with only a rejection handler.
- CLI/executable names and flags cited by verification are UNCHECKABLE by the intel symbol adapter:
  `.venv/bin/pytest` (`-q`, `-n auto`), `npm` (`--prefix .`, `test --`), `.venv/bin/mkdocs` (`build --strict`),
  `.venv/bin/ruff` (`check`, `format --check`), `msgfmt` (`--check`, `--check-format`, `-o`).
  Plan references: 03-01:177–180, :240–243, :274–277; 03-02:109–112, :182–191.
  Executable existence was checked; successful help/command invocation is not represented as signature analysis.
- Template/DOM literals `cv-filter-toggle`, `filter-collapse`, `aria-expanded`, `aria-controls`, `cv-key`,
  `data-cv-tooltip`, `data-cv-filter-icon-open`, `data-cv-filter-icon-close`, `data-cv-filter-icon`,
  `cv_open_class`, `cv_close_class`, `cv_variant`, icon keys `filter`/`filter-close`, class keys
  `context:secondary:both`/`context:hidden-label` are UNCHECKABLE template contracts under intel.
  Plan evidence: 03-01:28–39, :159–172, :211–216, :229–235; 03-02:101–105.
  Direct anchors: `src/crud_views/templates/crud_views/tags/context_action_filter.html:1` (class resolution),
  `:5` (toggle ID), `:6` (ARIA), `:10` (host attributes), `:12` (child hooks), `:14` (hidden label).
- Persistence field `filter_expanded`, request `POST`, `X-CSRFToken`, JSON content type and `reset_filter` are
  UNCHECKABLE semantic contracts under intel; source anchors are `src/crud_views/static/crud_views/js/list.filter.js:34`,
  `:36`, `:39`, `:54` and `src/crud_views/lib/views/mixins.py:336`. Plans 03-01:30, :74, :229–237 explicitly
  preserve and test these. No server request ordering guarantee is inferred.
- Bare filename references `toolbar_publisher_list.html`, `buttons.py`, `list.filter.js`, and documentation names
  resolve to the fully qualified files in the inventory (the golden is `tests/test1/golden/toolbar_publisher_list.html`).
  Produced `03-01-SUMMARY.md` / `03-02-SUMMARY.md` are skipped, including downstream plan dependencies.
- Repository/commit baseline capture is future execution work (03-01:155–158); no future commit ID is asserted verified.

## Cross-artifact fact-drift pass

Phase status came from `drift-guard phase-status --phase 03`:

```json
{
  "verdict": "consistent",
  "phase": "03",
  "stateStatus": "Ready to execute",
  "roadmapStatus": "Planned",
  "stateRank": 1,
  "roadmapRank": 1,
  "authority": "STATE.md"
}
```

No contradiction was found in the three prescribed judgment pairs:

| Fact | Authority evidence | Plan evidence | Result |
|---|---|---|---|
| Modes and byte-identical icon default | ROADMAP.md:115–116: configured both/label, default icon unchanged | 03-01:27, :159–173, :211–216: same presentation/default contract | Consistent; additional raw fixtures strengthen the criterion |
| Icon-less behavior and persistence | ROADMAP.md:117–118: label still toggles/persists | 03-01:29–33, :229–237: same behavior, explicit failure/order coverage | Consistent |
| Constant visible text | ROADMAP.md:119: only icon/ARIA change | 03-01:35–37, :229–237: preserve node/text through state changes | Consistent |
| German translation | ROADMAP.md:120: translated Filter with German catalog | 03-01:38–39, :255–282: PO/MO membership and render-time translation | Consistent |
| Requirement IDs | ROADMAP.md:112: FILT-01 through FILT-04 | Both plan frontmatters 03-01:18 and 03-02:15 | Same set |
| No target default; declared key | CONTEXT.md:22–29: D-01/D-02 | 03-01:162–165; 03-02:91–94 | Consistent |
| Host-pair fallback; constant label; mode accessibility | CONTEXT.md:32–47: D-03 through D-06 | 03-01:167–172, :211–237 | Consistent |
| Customization, compact docs, translated default | CONTEXT.md:48–55: D-07 through D-09 | 03-01:220–226, :261–271; 03-02:91–106 | Consistent |
| Stable behavior and release gates | CONTEXT.md:58–61: D-10/D-11 | 03-01:235–237; 03-02:129–142, :182–191 | Consistent |

The context's Discretion/Deferred Ideas are excluded from authority checks. Roadmap “short spec” wording is
satisfied by the recorded maintainer decisions and is not treated as an extra contradictory product contract.
Scope omissions and cross-plan agreements belong to the plan checker, not a duplicate drift finding.
