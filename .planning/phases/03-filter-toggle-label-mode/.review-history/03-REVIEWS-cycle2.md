---
phase: 03
cycle: 2
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T15:18:16.859236+00:00
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

Cycle 2 reviewed revised plans at `5b1c9d5`. All four configured instances were invoked via `review-lane invoke`; Grok required a retry after returning only a promise to review. The terminal results and coverage are recorded below; neither process success alone nor a prose promise is counted as a substantive review. No input was trimmed. [Cycle 1 and its source audit](.review-history/03-REVIEWS-cycle1.md) are preserved byte-for-byte; their unresolved counts are historical. The fixed conflict slot above is unchanged.

Coverage: fable-review complete, grok-review complete, gemini-review complete, deepseek-review complete.

## Claude Review (fable-review)

Verification is complete. Everything I needed is in hand, so here is the review.

# Cross-AI Plan Review, Cycle 2: Phase 03 at 5b1c9d5

Reviewed against the working tree at `5b1c9d5` on `introduce-gsd`. I opened every file the plan ledgers cite and traced each closure claim. One prior-session memory note (that `override_settings` works for `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`) is wrong and the plans are right; see A2 below.

## 03-01

**Summary**

The revised plan closes A1 through A6 and A11 with mechanisms that exist in source. The missing-mode policy is now explicit and matches how the class table resolves (`src/crud_views/lib/button_classes.py:144-147` only prefers the mode key when `mode` is truthy and the key exists), the tracer's configuration mechanism names the only target that works, and the DOM predicates avoid the classless wrapper spans. The remaining findings are wording precision inside one test task; none blocks execution.

**Strengths**

- **A1 closed correctly.** The plan now mandates explicit `both`/`label` branches with the legacy icon markup as the fallback for absent, None, empty or unknown `cv_label_mode`, passing the literal `"icon"` to `cv_button_class` on that path. That is the only design that keeps `tests/test1/test_button_leaves.py:574-576` (hand-built context, no mode) and the mode-less RAW_DEFAULT_FILTER assertion green, and it avoids copying the else-as-label shape of `src/crud_views/templates/crud_views/tags/button/action.html:8`. `test_filter_direct_mode_fallback` with a distinct `context:secondary:icon` override and a non-icon floor is the right guard against dropping the literal.
- **A2 closed correctly, and the plan is right where a memory note is wrong.** `from_settings` is `getattr(settings, name, default)` (`src/crud_views/lib/settings.py:13-14`) evaluated as a class-body default at line 67, and the singleton is built at import (`:320`). `override_settings` cannot change `crud_views_settings.context_actions_label_mode`. The existing suite monkeypatches exactly that attribute (`tests/test1/test_context_action_label_mode.py:263`). The class-override path is also verified: `setting_changed` resets the cache (`src/crud_views/lib/button_classes.py:111-114`) and `tests/test1/test_button_class_label_mode.py:67-70` already uses `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)` against this very toggle.
- **A3 closed.** The wrapper spans at `src/crud_views/templates/crud_views/tags/context_action_filter.html:11-12` are classless, so `./span[not(@class)]` from `tests/test1/test_context_button_label_mode.py:35-38` would misclassify both mode; the plan's `./span[not(@class) and not(@data-cv-filter-icon)]` selector is correct.
- **A5 and A6 closed.** `render_snippet` strips boundary whitespace (`src/crud_views/lib/view/base.py:371`), so the docstring requirement is apt. The both-mode separator mirrors `action.html:8` (`{% cv_icon cv_icon %} {% endif %}<span>`).
- **A11 adequately retained.** The wrapper's second stamp (`base.py:640-646`) and the truthy `{"cv_access": False}` early returns (`src/crud_views/lib/view/buttons.py:311-319`) are preserved by design; builder-only normalization really would be overwritten by the wrapper, so rejecting the A1 normalization extension is consistent.
- **Resolver call matches D-01/D-02.** `cv_get_action_label_mode("context", self.key, self)` hits the chain at `base.py:312-322` with no `target_default`; the filter data never carries `cv_context_label_mode`, so the wrapper's stamp resolves identically. The plan's explicit prohibition on adding that key is correct.
- **Tooling claims verified.** `polib` 1.2.0 is installed in `.venv`, `msgfmt` is at `/usr/bin/msgfmt`, the core German PO has no bare `Filter` msgid (only lines 47, 51, 239), the MO is tracked, and `settings_i18n.py` sits at the repo root as the taskfile expects.
- **JS scope is right.** `src/crud_views/static/crud_views/js/list.filter.js:15-18` collapses first, `:29` tolerates an empty NodeList, `:38` swallows rejection. Keeping the source untouched and extending `tests/js/list.filter.test.js` through the existing `loadScript` helper is correct.

**Concerns**

- **LOW. The invalid-configuration test names a check that does not exist for one source.** Task 03-01-02 says to inject an unknown string into "the button, view/ViewSet map and settings map, and assert the existing E210, E211 and E106 checks respectively." E211 covers only the view attribute (`src/crud_views/lib/view/action_menu.py:46-62`). A ViewSet map is validated by a Pydantic `field_validator` at construction (`src/crud_views/lib/viewset/__init__.py:105-110`) and `monkeypatch.setattr` on the instance bypasses it entirely, so there is no check to assert for that half. An executor following the text literally will look for an E211 that never fires.
- **LOW. Translation import convention conflict.** The plan says import plain `gettext as _`; `03-PATTERNS.md` tells the executor to reuse `gettext_lazy as _` from `base.py:26`. Plain `gettext` is the right choice for a value stored in the context dict and compared by `_apply_label`, and the sentinel test relies on a call at `get_context` time. The plan governs, but the two documents disagree.
- **LOW. Strict default in tests is implicit.** `tests/test1/conftest.py:41` sets `CRUD_VIEWS_STRICT=True`, so every non-strict log/fallback case needs `override_settings(CRUD_VIEWS_STRICT=False)` as at `tests/test1/test_context_action_label_mode.py:428`. The warn-once register is reset by the autouse fixture at `conftest.py:32`, so isolation works. The plan references "existing helpers" without naming either.

**Suggestions**

- Reword the invalid-configuration behavior to: button → E210, view map → E211, settings map → E106, ViewSet map → Pydantic `ValueError` at construction.
- State in Task 1 that the import is plain `gettext`, overriding the PATTERNS hint, so the sentinel test is unambiguous.
- Name the strict-off pattern (`override_settings(CRUD_VIEWS_STRICT=False)`) and the `_warned` autouse reset in Task 2's action text.

**Risk Assessment: LOW.** Every mechanism is verified in source, the default output is guarded by both the raw baseline and the normalized golden, and the three remaining items are wording fixes an executor can resolve from the read_first files.

## 03-02

**Summary**

H1 is closed: `tests/test1/test_label_mode_docs.py` is now in `files_modified`, in Task 03-02-01's `<files>` and `<read_first>`, and the action replaces the assertion at line 237 while preserving the menu-item and canonical-order checks. A7 through A10 are closed with correct locations. I found no new blocking issue; the one addition I would make is a wording choice in the migration guide.

**Strengths**

- **H1 closed and verified.** `tests/test1/test_label_mode_docs.py:236-238` asserts `"outside this configuration"` in the `### Rendering` section; `docs/reference/action_menus.md:171-172` contains it. The plan now owns the test file and keeps `"icon and short label in every mode"` (`:238`). The never-folded rule at `action_menus.md:180-184` is untouched.
- **A7 locations are exact.** The CUSTOM node is at `docs/reference/context_buttons.md:248`; the custom-template paragraph ends at `:82` and `### Active state` starts at `:84`, so inserting between them is safe. The tested first paragraph after the diagram (`:317-321`) contains every phrase `test_label_mode_docs.py:283-286` pins, and the plan explicitly preserves it. The host-fallback paragraph is at `docs/reference/buttons.md:221-222`, as cited.
- **A8 verified.** `src/crud_views/lib/view/__init__.py:2` exports four button classes and not `FilterContextButton`; the Import Paths block at `context_buttons.md:502-507` would mislead without the fix.
- **A9 is a deliberate decision.** The checklist bullet at `docs/migrating-1.0.md:399` exists; the Fixed section at `CHANGELOG.md:147` exists; the plan requires naming the existing-floor effect.
- **Every stale passage is still real.** `context_buttons.md:81-82`, `buttons.md:304-306`, `action_menus.md:171-172`, `javascript.md:83` and `:195-199`, `icons.md:72-74` and `:174-176` all describe the toggle as fixed-icon or always-icon-bearing.
- **Gates are the real ones.** `.venv/bin/pytest`, `.venv/bin/mkdocs`, `.venv/bin/ruff` exist; `npm test` is `vitest run` (`package.json:11`), so the file-filter argument works without watch mode. `.planning/phases/02-form-key-grammar/deferred-items.md` exists for the read_first.

**Concerns**

- **LOW. The migration note targets the checklist, not the contract bullet it links to.** The checklist line at `docs/migrating-1.0.md:399` links to the contract-changes bullet at `:331-337`, which describes what a copied `context_action_filter.html` must render. A reader fixing a copy reads `:331`, not the checklist. Extending only `:399` leaves the contract bullet silent on `cv_label_mode`.
- **LOW. The doc-test replacement should pin wording the executor has not yet written.** Task 1 says "replace with positive checks that the filter follows the resolved mode and has no target-view default." Without a fixed phrase, the executor must coordinate prose and assertion in one pass; that is fine but easy to drift. The plan does say to verify the new assertions distinguish the old docs, which mitigates it.

**Suggestions**

- Add one clause to the contract bullet at `docs/migrating-1.0.md:331-337`: the context now carries the resolved `cv_label_mode`, and a copy that ignores it keeps icon-only behavior.
- Choose the pinned phrase up front (for example "follows the resolved context mode" and "no target-view default") and write it into both the doc edit and the assertion.

**Risk Assessment: LOW.** The one HIGH from cycle 1 is closed with the test file in scope and the assertion replacement specified. The remaining items are documentation placement choices.

## Cross-plan assessment

- **Closure verdicts.** H1: closed. A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11: closed or explicitly deferred with reasoning that matches source. The A1 rejection of runtime normalization and the A11 deferral of the wrapper refactor are consistent with `base.py:640-646` and need no further action.
- **Dependency ordering is right.** 03-02 consumes the dedicated test module and the summary from 03-01; `tests/test1/test_filter_toggle_label_mode.py` does not exist yet, as expected for Wave 0 work. No same-wave file overlap.
- **Scope.** No creep into the form leaf, adapters or the downstream theme. JS remains test-only.
- **Security.** Labels stay under Django autoescape, the POST keeps `X-CSRFToken` and the boolean JSON body (`list.filter.js:34-37`), and the early `cv_access: False` returns are retained. Proportionate for ASVS level 1.
- **Execution trap to call out in the summary.** A prior-session note claims `override_settings` changes the captured action map; it does not. The plan's monkeypatch instruction is the correct one and should not be "corrected" by an executor consulting memory.
- **Phase goal.** With the LOW wording fixes, the plans deliver FILT-01 through FILT-04 with the default golden intact.

`CYCLE_SUMMARY: current_high=0 current_actionable=5` (all LOW: E211/ViewSet wording, gettext import convention, strict-off pattern naming, migration contract bullet, pinned doc phrase).

---

## OpenCode Review (grok-review)

I'll verify the revised plans against the live filter, resolver, and docs code before writing the review.
The prior review's closure claims depend on specific tests and docs. I'll check those next.
## 03-01

The implementation plan matches the live filter contract and can deliver FILT-01 through FILT-04 without a JavaScript rewrite. Prior H1 does not apply here. A1–A6 and A11 are closed in the plan text and match the source. One new specification error remains: the invalid-configuration test maps a ViewSet map onto `viewset.E211`, which that check does not report.

### Strengths
- Resolver reuse is correct. `cv_get_action_label_mode` returns the view's own named entry, then the supplied button override, then the selected whole map, then `target_default` or the context floor (`src/crud_views/lib/view/base.py:312-322`). Calling it as `cv_get_action_label_mode("context", self.key, self)` with no fourth argument matches D-01 and D-02. `FilterContextButton.get_context` still seeds an untranslated `"Filter"` and never stamps a mode (`src/crud_views/lib/view/buttons.py:323-332`).
- Stamping before `_apply_label` is required. `cv_get_context` stamps `cv_label_mode` only after `get_context` returns (`src/crud_views/lib/view/base.py:640-645`), and label templates render inside `get_context` (`src/crud_views/lib/view/buttons.py:55-71`). The plan correctly forbids adding `cv_context_label_mode`, which the wrapper would pass as `target_default` (`base.py:643`).
- The missing-mode policy is now explicit and matches the leaf that must stay byte-identical. The stock template hard-codes `"icon"` (`src/crud_views/templates/crud_views/tags/context_action_filter.html:3`). `get_button_class` uses `location:slot:mode` only when `mode` is truthy and that key exists (`src/crud_views/lib/button_classes.py:144-145`). `_filter_toggle` omits `cv_label_mode` (`tests/test1/test_button_leaves.py:574-576`). Keeping the current icon markup as the fallback, and passing literal `"icon"` on that path, is what `test_filter_toggle_resolves_icon_mode` already requires (`tests/test1/test_button_class_label_mode.py:67-70`). Rejecting a new runtime normalizer is sound: this leaf bypasses `cv_button_data` (`src/crud_views/lib/view/button_data.py:85-94`), and the wrapper would overwrite a builder-only stamp.
- Leaving `list.filter.js` unchanged is justified. Collapse runs first and a false return skips mutation (`src/crud_views/static/crud_views/js/list.filter.js:15-17`); an empty `[data-cv-filter-icon]` list is a no-op (`:29`); a rejected POST cannot roll back state because the response is ignored (`:32-38`).
- The settings-map monkeypatch, filter-specific selectors, raw-whitespace docstring, both-mode spacing, and bounded translation evidence are written into Task 1 and Task 3. `context_actions_label_mode` is captured by `from_settings` at class-body time (`src/crud_views/lib/settings.py:13-14, 67`), so `override_settings` cannot change it. `render_snippet` strips boundary whitespace (`base.py:371`). The core PO has no bare `msgid "Filter"`.

### Concerns
- **MEDIUM — ViewSet maps are not `viewset.E211`.** Task 2 says to inject an unknown string into "the button, view/ViewSet map and settings map" and assert E210, E211 and E106 respectively. Button `label_mode` is an unvalidated `str | None` and `context_button_checks` reports it as E210 (`src/crud_views/lib/view/buttons.py:33, 360-361`; `src/crud_views/lib/view/label_mode.py:48`). The view attribute is E211 (`src/crud_views/lib/view/action_menu.py:46-55`, called from `base.py:194`). A ViewSet map is rejected at construction by a Pydantic `ValidationError`, not a system check (`src/crud_views/lib/viewset/__init__.py:105-111`; `tests/test1/test_action_label_mode_config.py:56-60`). E211 reads only `getattr(cls, attribute)` on the view class (`action_menu.py:51`). Monkeypatching an invalid map onto an already-built ViewSet, the way resolution tests patch `cv_author.context_actions_label_mode`, produces none of those three ids. Settings E106 is real, but only on a `CrudViewsSettings` instance field (`src/crud_views/lib/settings.py:129-135`); the existing helper constructs that instance directly (`tests/test1/test_action_label_mode_config.py:45-47`).

### Suggestions
- Split the policy test: button → `viewset.E210`; view `cv_context_actions_label_mode` → `viewset.E211`; ViewSet field → `pytest.raises(ValidationError)` at construction, and do not expect E211 after a monkeypatch; settings → `CrudViewsSettings(context_actions_label_mode=...).check_messages` equals `["crud_views.E106"]`.
- Keep the explicit rejection of runtime normalization. That part of A1 is closed and should not be reopened.

### Risk Assessment
**LOW.** The behavior is already in the resolver, template, and script. The new defect is a test-id mapping error, not an open product decision. An executor who copies the "respectively" sentence will write a check assertion that cannot go green.

## 03-02

The documentation plan now owns the doc-contract test that the previous cycle would have broken, and it names the remaining prose edits. Prior H1, A7, A8, A9 and A10 are closed as planning instructions. No new product gap.

### Strengths
- H1 is closed in the plan, and the conflict is still live in source, which is what a not-yet-executed plan should show. `tests/test1/test_label_mode_docs.py:237` still asserts `"outside this configuration"` on the Rendering section, and that sentence is still at `docs/reference/action_menus.md:171-172`. Task 03-02-01 now lists `tests/test1/test_label_mode_docs.py` in `files_modified` and in the task files, and it replaces that assertion while keeping the menu-item sentence at `test_label_mode_docs.py:238` and the never-folded rule at `docs/reference/action_menus.md:180-184`.
- The insertion point avoids the other doc test. The compact contract goes after the custom-template paragraph (`docs/reference/context_buttons.md:77-82`) and before Active state (`:84`). `test_label_mode_docs.py:277-286` only pins the first paragraph after the later Mermaid fence, including the exact `MICON` line at `context_buttons.md:258`. Updating the `CUSTOM` node at `:248` does not touch that paragraph.
- The import instruction matches the package. `src/crud_views/lib/view/__init__.py:2` exports `ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton` and not `FilterContextButton`. Import Paths currently show `from crud_views.lib.view import ...` (`docs/reference/context_buttons.md:505`). Showing `from crud_views.lib.view.buttons import FilterContextButton` is the path tests already use.
- Fixed, not Breaking, is still consistent with unchanged default English bytes, and the plan now names the already-configured context-floor effect. The checklist bullet to extend exists at `docs/migrating-1.0.md:399`. The current branch is `introduce-gsd` at `5b1c9d5`, which matches the summary instruction. `#context-label-mode-resolution` exists (`docs/reference/action_menus.md:87`).

### Concerns
- None at MEDIUM or HIGH. Historical tooltip prose at `docs/migrating-1.0.md:171` still says the filter toggle carries `data-cv-tooltip`. That remains true for the default icon mode. Task 2 already makes the current JavaScript contract conditional (`docs/reference/javascript.md:83`). No plan change is required for the 0.30 history bullet.

### Suggestions
- None required before execution. If the executor touches `docs/migrating-1.0.md:171`, qualify it as icon mode only; do not treat that sentence as a missed gate.

### Risk Assessment
**LOW.** The previous guaranteed-red verify is fixed in the plan text. Strict MkDocs plus the updated docs test is a sufficient gate for the prose this phase owns.

## Closure of the prior cycle

| ID | Disposition | Evidence |
|---|---|---|
| H1 | Closed in plan, not yet in source | `03-02` files and Task 03-02-01 name `tests/test1/test_label_mode_docs.py` and replace the assertion at `test_label_mode_docs.py:237`. Source still has the old phrase, as expected before execution. |
| A1 | Closed; normalization rejected | Tasks 1–2 keep a mode-less raw fixture, pass literal `"icon"` on the legacy branch, and test E210/E211/E106 without extending `cv_button_data`. The ViewSet half of that check list is the new N1 below, not a reopening of A1. |
| A2 | Closed | Task 1 names `monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", ...)` and `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`, whose `setting_changed` receiver resets the cache (`src/crud_views/lib/button_classes.py:111-114`). |
| A3 | Closed | Tasks 1–2 require `./span[not(@class) and not(@data-cv-filter-icon)]` and icons inside `data-cv-filter-icon` wrappers. |
| A4 | Closed | Task 3 separates PO/MO membership, a runtime sentinel, and German render, and says identical spelling does not prove catalog provenance. |
| A5 | Closed | Task 1 requires the raw-fixture docstring against `render_snippet` stripping (`base.py:371`). |
| A6 | Closed | Task 1 requires a literal space before the both-mode visible span and forbids icon-mode byte changes. |
| A7 | Closed | Task 1 names the `CUSTOM` node, the insertion point before Active state, and the icon-bearing-only qualifier for `docs/reference/buttons.md:221-222`. |
| A8 | Closed | Task 1 shows `from crud_views.lib.view.buttons import FilterContextButton` and does not add an export. |
| A9 | Closed | Task 3 keeps Fixed, names an already-configured context floor, and extends the checklist at `docs/migrating-1.0.md:399`. |
| A10 | Closed | Task 3 records `introduce-gsd` without claiming fresh approval. `git rev-parse --abbrev-ref HEAD` is `introduce-gsd`. |
| A11 | Closed as deferred | Task 1 retains the wrapper's second stamp and evaluation of truthy `{"cv_access": False}` (`buttons.py:311-319`, `base.py:641`). |

**N1 — MEDIUM, new, 03-01 only.** Do not treat a ViewSet `context_actions_label_mode` value as `viewset.E211`. Split that assertion as in the suggestion above. No other prior finding is reopened.

Phase risk is **LOW**. Wave order is right, there is no file overlap, and the phase goal does not depend on resolving N1 before the template change. N1 should be corrected in the plan text so Task 2's check test is writable on the first attempt.

---

## OpenCode Review (gemini-review)

## 03-01

### 1. Summary
Plan `03-01` (Cycle 2 at `5b1c9d5`) implements label-mode resolution, three-way template rendering (`icon`, `both`, `label`), and runtime `gettext` translation for `FilterContextButton` and `context_action_filter.html`, along with Python and Vitest regression tests. Verification against the live codebase confirms that every Round 1 concern assigned to `03-01` (`A1`–`A6` and `A11`) is cleanly closed in the revised tasks, acceptance criteria, and review ledger. The implementation mechanics—stamping `cv_label_mode` in `FilterContextButton.get_context()` before `_apply_label()`, keeping `icon` as the template's fallback branch for absent/unrecognized direct modes, using filter-specific XPath predicates, and exercising the unchanged `list.filter.js` handler—are fully grounded in the tracked source.

### 2. Strengths
- **Closure of `A1` (direct-leaf fallback and malformed-configuration policy):**
  - Task `03-01-01` (`03-01-PLAN.md:177-180`) explicitly specifies `both` and `label` branches with the legacy `icon` branch as the `else` fallback for absent, `None`, empty, or unknown direct `cv_label_mode` values, passing a literal `"icon"` to `{% cv_button_class %}` (`src/crud_views/templates/crud_views/tags/context_action_filter.html:3`, `src/crud_views/lib/button_classes.py:144-147`). This preserves both `RAW_DEFAULT_FILTER` byte-identity and `context:secondary:icon` class lookup for hand-built contexts such as `_filter_toggle()` in `tests/test1/test_button_leaves.py:574-576`.
  - Task `03-01-02` (`03-01-PLAN.md:249-260`) and the Review Dispositions Ledger (`03-01-PLAN.md:122-126`) soundly reject adding a second runtime normalizer in `FilterContextButton.get_context()` because `CrudView.cv_get_context()` (`src/crud_views/lib/view/base.py:643-645`) restamps the raw return value of `cv_get_action_label_mode()` (`base.py:312-322`), while startup checks `viewset.E210` (`src/crud_views/lib/view/buttons.py:360-361`), `viewset.E211`, and `crud_views.E106` (`src/crud_views/lib/settings.py:128-141`) already diagnose malformed button/map values and `default_label_mode("context")` (`src/crud_views/lib/view/label_mode.py:84-117`) handles invalid floor recovery.
- **Closure of `A2` (snapshot settings vs. signal-backed class cache):** Task `03-01-01` (`03-01-PLAN.md:163-169`) explicitly directs monkeypatching `crud_views_settings.context_actions_label_mode` (which is captured once at class definition time via `from_settings` at `src/crud_views/lib/settings.py:13-14, 67`) and using `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`, which automatically resets `_button_classes_cache` on entry and exit via `_on_setting_changed` (`src/crud_views/lib/button_classes.py:111-114`).
- **Closure of `A3` and `A6` (filter-specific DOM selectors and `both`-mode spacing):** Tasks `03-01-01` and `03-01-02` (`03-01-PLAN.md:169-171, 181-183, 244-247`) require selecting the visible label via `./span[not(@class) and not(@data-cv-filter-icon)]` and element icons as descendants of `[data-cv-filter-icon]` (`src/crud_views/templates/crud_views/tags/context_action_filter.html:11-12`), avoiding the false positive in `_is_text_only()` (`tests/test1/test_context_button_label_mode.py:35-38`). They also require a literal space before `<span>{{ cv_action_label }}</span>` in `both` mode, matching `src/crud_views/templates/crud_views/tags/button/action.html:8` without altering `icon`-mode bytes.
- **Closure of `A4`, `A5`, and `A11` (bounded i18n claims, raw whitespace rationale, and wrapper retention):**
  - `EDGE-FILT-04-encoding` (`03-01-PLAN.md:39`) and Task `03-01-03` (`03-01-PLAN.md:274-292`) separate PO/MO membership (`tests/test1/test_i18n.py:65-81`), runtime `gettext` sentinel verification on `buttons.py`, and active-language `"de"` rendering without overclaiming catalog provenance from identical `"Filter"` spelling.
  - Task `03-01-01` (`03-01-PLAN.md:157-159`) documents why `RAW_DEFAULT_FILTER` checks `render_to_string` boundary whitespace even though `CrudView.render_snippet()` strips outer whitespace (`src/crud_views/lib/view/base.py:371`).
  - Task `03-01-01` (`03-01-PLAN.md:174-175`) and the ledger (`03-01-PLAN.md:127`) explicitly retain the existing `{"cv_access": False}` early returns (`src/crud_views/lib/view/buttons.py:311-319`) and `CrudView.cv_get_context()` wrapper behavior (`base.py:640-646`).

### 3. Concerns
- None. All prior Round 1 concerns for `03-01` are resolved in the plan text and verified against the codebase.

### 4. Suggestions
- None required before execution. When wrapping lines 7–8 and 11–13 of `src/crud_views/templates/crud_views/tags/context_action_filter.html`, keep `{% if %}` tags adjacent to existing newlines/indentation so the `else` (`icon`) branch produces the exact pre-edit string stored in `RAW_DEFAULT_FILTER`.

### 5. Risk Assessment
- **Risk Level: LOW**
- **Justification:** All runtime seams (`cv_get_action_label_mode`, `context_action_filter.html`, `list.filter.js`, and `django.po`/`.mo`) are small, localized, and verified in source, with pre-change raw byte assertions and normalized toolbar goldens guarding default output.

---

## 03-02

### 1. Summary
Plan `03-02` (Cycle 2 at `5b1c9d5`) updates the five reference docs (`context_buttons.md`, `action_menus.md`, `buttons.md`, `javascript.md`, `icons.md`), `docs/migrating-1.0.md`, `CHANGELOG.md`, and the documentation contract suite `tests/test1/test_label_mode_docs.py`, followed by running all five project quality gates. Every Round 1 finding (`H1` and `A7`–`A10`) has been incorporated and verified against the live files. In particular, adding `tests/test1/test_label_mode_docs.py` to `files_modified` and Task `03-02-01` resolves the previously blocking assertion failure on `docs/reference/action_menus.md:171-172`.

### 2. Strengths
- **Closure of `H1` (paired update of `test_label_mode_docs.py` and `action_menus.md`):** `tests/test1/test_label_mode_docs.py` is now listed in `files_modified` (`03-02-PLAN.md:13`) and Task `03-02-01`'s `<files>` and `<read_first>` (`03-02-PLAN.md:83-84`). Task `03-02-01` (`03-02-PLAN.md:107-114`) replaces the stale assertion at `tests/test1/test_label_mode_docs.py:236-238` (`assert "filter toggle" in rendering and "outside this configuration" in rendering`) with positive assertions for the new contract while preserving the canonical 5-step resolution checks (`test_label_mode_docs.py:194-207`) and the `## What is never folded` section (`docs/reference/action_menus.md:180-185`).
- **Closure of `A7` (Mermaid `CUSTOM` node, section placement, and `buttons.md` fallback prose):**
  - Task `03-02-01` (`03-02-PLAN.md:86-87`) places the compact filter contract in `docs/reference/context_buttons.md` right after the custom-template paragraph (`lines 77-82`) and before `### Active state` (`line 84`), leaving the first paragraph after the Mermaid diagram (`context_buttons.md:317-325`) intact for `tests/test1/test_label_mode_docs.py:277-287`.
  - Task `03-02-01` (`03-02-PLAN.md:101-105`) updates the Mermaid `CUSTOM` node at `docs/reference/context_buttons.md:248` while preserving `MICON` (`line 258`) and its edges (`test_label_mode_docs.py:279-282`), and qualifies `docs/reference/buttons.md:221-222` so the two-span standalone fallback when `context:icon-host` is off applies only to `icon` and `both` modes.
- **Closure of `A8` (executable `FilterContextButton` import path):** Task `03-02-01` (`03-02-PLAN.md:91-92`) requires showing `from crud_views.lib.view.buttons import FilterContextButton` in the examples and under `## Import Paths` (`docs/reference/context_buttons.md:502-507`), matching `src/crud_views/lib/view/__init__.py:1-17`.
- **Closure of `A9` and `A10` (floor-impact disclosure, copied-template checklist, and branch provenance):**
  - `docs/migrating-1.0.md` is now in `files_modified` (`03-02-PLAN.md:12`) and Task `03-02-03` (`03-02-PLAN.md:155, 165-167`), which extends the copied-`context_action_filter.html` checklist item (`docs/migrating-1.0.md:399-400`) and states in `CHANGELOG.md` `### Fixed` (`CHANGELOG.md:147`) that an already-configured `CRUD_VIEWS_LABEL_MODE_DEFAULTS` context floor now applies to the filter toggle.
  - Task `03-02-03` (`03-02-PLAN.md:176-179`) accurately records `introduce-gsd` as the workflow-retained branch in `03-02-SUMMARY.md` without fabricating fresh branch approval or switching branches mid-wave.

### 3. Concerns
- None. All prior Round 1 concerns (`H1`, `A7`–`A10`) are resolved and no new conflicts were found.

### 4. Suggestions
- None.

### 5. Risk Assessment
- **Risk Level: LOW**
- **Justification:** With `tests/test1/test_label_mode_docs.py` and `docs/migrating-1.0.md` brought into scope and the exact invariants of `test_label_mode_docs.py:180-325` accounted for, the documentation and verification steps in `03-02` are internally consistent and ready to execute.

---

## Cross-Plan Comparison and Overall Assessment

- **Round 1 Disposition Verification:** All 12 items from Round 1 (`H1` and `A1`–`A11`) are addressed in Cycle 2 (`5b1c9d5`) with accurate source grounding and clear scope boundaries.
- **Wave & Dependency Ordering:** Wave 1 (`03-01`) and Wave 2 (`03-02`) touch disjoint file sets (9 files in `03-01`, 8 files in `03-02`) and sequence implementation/tests before documentation/release gates.
- **Overall Risk Assessment: LOW.** Both plans are complete, consistent with the live repository, and ready for execution.

---

## OpenCode Review (deepseek-review)

I'll review the plans by examining the actual codebase to verify their claims. Let me start by reading the relevant files mentioned in the plans.
Now let me check the 03-02 plan:
Now let me examine the actual source code to verify the claims in the plans. Let me start by checking the current state of the filter template and resolver:
Now let me check the FilterContextButton implementation:
Let me search for FilterContextButton specifically:
Let me read around line 298:
Let me continue reading to find FilterContextButton:
Now let me check the filter template:
Now let me check the JavaScript file:
Now let me check the German locale file:
Now let me check if "Filter" is already translated by searching in the PO file:
So "Filter" alone is not translated. Now let me check the documentation files mentioned in the plan:
Let me search for the filter toggle documentation:
Let me check around line 171:
Let me read lines 160-190:
Let me try a different approach to read specific lines:
Now let me check if there's a test file for label mode docs:
Now let me run some tests to understand the current state:
Now let me examine the review feedback and current state more thoroughly. Based on my examination of the actual codebase, I can now provide a comprehensive review.

# Cross-AI Plan Review: Phase 03 (Filter toggle label mode)

## Plan Coverage Manifest

Total plans in this review: 2

Plan ids (give each one its own `##`-level section, headed verbatim):
- 03-01
- 03-02

## 03-01

**Summary** — This plan implements filter toggle label mode support by modifying `FilterContextButton.get_context()` to use `cv_get_action_label_mode()` and adding mode-specific rendering to the filter template. The plan correctly addresses all core requirements (FILT-01 through FILT-04) and follows the design decisions (D-01 through D-11).

**Strengths**
- **Accurate technical grounding**: The plan correctly identifies that `cv_get_action_label_mode()` exists at `src/crud_views/lib/view/base.py:299-328` and understands its precedence logic (own map → button override → selected whole map → target_default or context floor).
- **Good test strategy**: Capturing raw baseline strings before implementation (`RAW_DEFAULT_FILTER`) prevents accidental regression, which is crucial since golden comparisons normalize whitespace (`tests/test1/test_action_menus_golden.py:38-55`).
- **Proper integration approach**: Uses existing resolver without creating new APIs, maintains customization hooks (`_apply_label`, `_apply_variant`, `_inject_template`).
- **Security awareness**: Maintains Django escaping and CSRF protection (`src/crud_views/static/crud_views/js/list.filter.js:36-37`).
- **Localization approach**: Correctly identifies that German translation needs to be added to PO file (`src/crud_views/locale/de/LC_MESSAGES/django.po` currently lacks bare "Filter" msgid).

**Concerns**
1. **MEDIUM — Missing mode validation in template**: The plan modifies `context_action_filter.html` but doesn't specify how to handle invalid or missing `cv_label_mode` values. The current template hardcodes `"icon"` in `cv_button_class` call (line 3). Should follow same validation pattern as other templates.
2. **MEDIUM — JavaScript test coverage gaps**: While plan mentions extending `tests/js/list.filter.test.js`, it doesn't specify how to test `label` mode with no icon spans - needs specific assertion that `[data-cv-filter-icon]` selector returns empty NodeList.
3. **LOW — Potential golden test fragility**: The plan mentions `toolbar_publisher_list.html` golden should remain byte-identical, but golden comparisons normalize whitespace. This could hide actual template changes unless raw baseline is captured.

**Suggestions**
1. Add explicit check in Task 1: after adding `cv_label_mode = ...`, verify it's one of `{"icon", "both", "label"}` or falls back to default.
2. Update verification to include `test_template_a11y.py` which tests accessible markup.
3. Add explicit test for `label` mode ensuring no `data-cv-filter-icon-open/close` attributes are rendered.

**Risk Assessment**: MEDIUM - Implementation is straightforward but edge cases around template validation and backward compatibility need careful handling. The main risks are:
- Template changes breaking existing custom templates that override `context_action_filter.html`
- Golden tests potentially passing even with minor whitespace changes
- JavaScript interaction needing to work correctly in `label` mode with no icons

## 03-02

**Summary** — This documentation update plan correctly identifies all documentation files that need updating and provides clear update instructions. The plan addresses the HIGH severity issue (H1) identified in previous reviews by including `tests/test1/test_label_mode_docs.py` in `files_modified`.

**Strengths**
- **Complete doc coverage**: Identifies all 5 documentation files that mention filter toggle behavior: `context_buttons.md:77-82`, `buttons.md:304-306`, `action_menus.md:168-184`, `javascript.md:83,187-202`, `icons.md`.
- **Correct technical understanding**: Recognizes the need to update test assertions in `test_label_mode_docs.py:236-238` that currently check for "outside this configuration" phrase.
- **Proper changelog approach**: Uses "Fixed" classification since default output remains unchanged.
- **Quality gate awareness**: Includes all required validation commands.

**Concerns**
1. **MEDIUM — Missing reference to icons.md specifics**: Plan mentions updating `icons.md` but doesn't specify what needs changing there (likely the description of filter rendering two icons).
2. **LOW — No mention of translation documentation**: Should document that "Filter" is now translatable.
3. **LOW — Potential documentation inconsistency**: If Phase 1 implementation changes but documentation references don't match exactly, could cause confusion.

**Suggestions**
1. Add specific note about what to update in `icons.md` - likely the description of filter rendering two icons.
2. Include verification that all cross-references between docs still work.
3. Add note to documentation about translation of "Filter" label.

**Risk Assessment**: LOW - Documentation updates are straightforward and the plan correctly identifies all necessary changes. The main risk was the test assertion conflict (H1) which has been addressed.

## Overall Assessment

**MEDIUM** overall risk. The implementation plan (03-01) has moderate risk due to template changes needing to maintain backward compatibility, while the documentation plan (03-02) is low risk. The phased approach (implementation then documentation) is sound.

**Key verification points** from code inspection:
- `src/crud_views/lib/view/buttons.py:326` shows `data["cv_action_label"] = "Filter"` hardcoded - needs `_("Filter")`
- `src/crud_views/templates/crud_views/tags/context_action_filter.html:3` hardcodes `"icon"` mode in `cv_button_class` call - needs `cv_label_mode`
- No `cv_label_mode` currently stamped in `FilterContextButton.get_context()` - needs to be added
- German PO file lacks "Filter" translation - needs to be added
- `src/crud_views/static/crud_views/js/list.filter.js:29` already tolerates empty icon NodeList - good for `label` mode
- `tests/test1/test_label_mode_docs.py:237` asserts "outside this configuration" - needs updating per H1

**Dependency ordering**: Correct - 03-02 depends on 03-01 and can't run first.

**Security considerations**: Appropriately addressed - maintains existing CSRF protection, Django escaping, and trust boundaries.

**Performance implications**: Minimal - one extra resolver call per filter render.

**Phase goal achievement**: With careful implementation addressing the MEDIUM concerns, the plans should successfully deliver FILT-01 through FILT-04 with default golden intact.

---

## Consensus Summary

### Agreed Strengths

- Fable, Grok, Gemini and DeepSeek confirm the prior H1 documentation-test conflict is closed at the **planning** level: 03-02 now owns the affected test and mandates the paired assertion/prose change. This is reviewer sign-off on plan adequacy, not a claim that implementation or product tests have already run.
- The resolver/customization ordering, unchanged JavaScript scope, raw-byte baseline alongside normalized goldens, and separate translation evidence all use existing mechanisms.
- Both plans preserve the implementation-before-documentation dependency and the project quality gates.

### Agreed Concerns

**C2-A1 (MEDIUM)** is corroborated by Grok and Fable and confirmed by direct source inspection: the planned E211 assertion incorrectly includes ViewSet maps, whose construction uses Pydantic validation. DeepSeek repeats the earlier missing-mode and icon-less coverage concerns, but those instructions are already explicit in 03-01. Its general MEDIUM risk assessment is not a HIGH finding.

### Divergent Views and adjudication

Fable raises five LOW suggestions. Two identify instructions still absent or inaccurate; three are already incorporated as requirements rather than needing another implementation recipe.

| Current finding | Verdict and current plan/source evidence |
|---|---|
| **C2-A1 — MEDIUM: ViewSet validation is incorrectly grouped with E211** | **Actionable.** `03-01-PLAN.md:274–275` asks for E211 for the “view/ViewSet map.” `src/crud_views/lib/view/action_menu.py:46–62` checks the view attribute; `src/crud_views/lib/viewset/__init__.py:105–110` validates ViewSet maps during Pydantic construction. Split the planned cases: button E210, view E211, settings E106, ViewSet constructor validation error. This refines the previously accepted A1 policy without reopening normalization scope. |
| **C2-A2 — LOW: migration contract paragraph omitted** | **Actionable.** `03-02-PLAN.md:200–203` updates the checklist but does not name the detailed contract at `docs/migrating-1.0.md:331–339`, which still directs copied filters to render icons unconditionally. Add the resolved-mode/optional-icon clause there, or explicitly defer it with rationale in the PLAN. The existing checklist and compact-contract link do not themselves revise that separate paragraph. |
| Fable: plain gettext versus PATTERNS lazy import hint | Already incorporated. `03-01-PLAN.md:200–201` explicitly requires `django.utils.translation.gettext as _` evaluated during `get_context`; Task 3 (`:323–330`) verifies runtime sentinel behavior. The older PATTERNS hint at `03-PATTERNS.md:44` does not override this explicit task. No additional PLAN requirement is missing. |
| Fable: name strict-off helper and warning reset | Already incorporated behavior: `03-01-PLAN.md:277–281` requires strict ValueError and non-strict package-icon/warn-once behavior using the existing helper; `:236` includes existing tests/read-first sources. `tests/test1/conftest.py:32` supplies isolation. An executor must select non-strict settings to satisfy that explicit case; spelling another helper call is not otherwise invisible work. |
| Fable: preselect exact prose phrase for doc tests | Already incorporated. `03-02-PLAN.md:139–145` requires positive resolved-mode/no-target assertions paired with the prose, preserving invariants and distinguishing the old docs. Choosing exact wording is an implementation detail. |
| DeepSeek: missing/invalid mode handling and normalizer | Already incorporated/rejected explicitly at `03-01-PLAN.md:160`, `:203–209`, `:272–282`; fallback class lookup is literal icon and malformed map/button runtime normalization is deliberately rejected. |
| DeepSeek: no icon-less JS or no-attribute assertions | Already incorporated at `03-01-PLAN.md:249–253`, `:267–270`, `:284–293`; both icon data attributes, wrappers and descendants are forbidden in label mode, with real-handler fixtures and failure cases. |
| DeepSeek: normalized golden masks bytes | Separate raw fixtures are mandatory before production edits (`03-01-PLAN.md:176–185`); normalized goldens remain an independent gate. |
| DeepSeek: icons.md specifics, translated-label prose and cross-links | Already incorporated at `03-02-PLAN.md:128`, `:173–177`, `:148`, `:126`; strict MkDocs and semantic comparison remain gates. |
| DeepSeek: add accessibility suite | `03-02-PLAN.md:257` runs the full Python suite; focused presentation and ARIA assertions are specified in 03-01. No suite is omitted. |

### Previous-cycle closure ledger

All twelve round-one groups are closed or explicitly deferred in the revised plans. Fable, Grok and Gemini independently sign off every group; DeepSeek explicitly signs off H1. Current citations below govern where external reviewer plan-line offsets differ from the checkout.

| Round-one ID | Disposition evidence in current plans |
|---|---|
| H1 | 03-02:14, :115, :139–150 own and update the stale doc assertion. Source still contains the old assertion at test_label_mode_docs.py:237 because implementation is future work; the planning omission is closed with reviewer verification. |
| A1 | 03-01:160 explicitly rejects new runtime normalization; :203–209 and :272–282 prescribe direct fallback and configuration policy. C2-A1 above is a new specific correction to one test instruction. |
| A2 | 03-01:188–193 requires snapshot monkeypatch and signal-backed class override isolation. |
| A3 | 03-01:194–195 and :267–270 require filter-specific predicates. |
| A4 | 03-01:39 and :323–330 separate catalog, runtime and active-language claims. |
| A5 | 03-01:180–183 explains boundary whitespace protection. |
| A6 | 03-01:208–209 requires literal spacing without changing icon bytes. |
| A7 | 03-02:118–119 and :131–137 cover insertion point, diagram and host fallback. |
| A8 | 03-02:123–125 requires the actual module import and Import Paths update. |
| A9 | 03-02:191–203 names existing-floor impact and copied-template checklist. C2-A2 requests coverage of the separate detailed paragraph. |
| A10 | 03-02:212–215 records observed branch provenance without invented approval. |
| A11 | 03-01:161 and :200–202 explicitly retain existing duplicate resolution/hidden-context evaluation. |

### Evidence quality and cycle count

All final external output is preserved verbatim above. Grok’s first attempt returned only a promise and a leading evidence-discount marker; it was not weighted as a review. Its retry returned a substantive source-citing review covering both plans, with the first attempt retained in per-run diagnostics. All four final reviewers have source citations and no leading evidence-discount marker. Grok’s optional suggestion about a historical migration tooltip sentence expressly requires no plan change and is not actionable. Gemini's plan line numbers sometimes refer to earlier positions; the independently read current-plan citations in this synthesis resolve those offsets. DeepSeek includes a narrative “run some tests” line but provides no command/result record; it is not validation evidence. The orchestrator ran no product suite, and the review prompt prohibited tests and edits.

No new HIGH was raised. H1 has explicit current reviewer sign-off, so it is fully resolved for this plan review. Historical HIGH tables are not recounted. Non-HIGH counts exclude advice already in tasks or explicit scope dispositions. The current MEDIUM validation item and LOW migration item remain unincorporated.

CYCLE_SUMMARY: current_high=0 current_actionable=2

## Current HIGH Concerns

None.

## Current Actionable Non-HIGH Concerns

- C2-A1 (MEDIUM): split ViewSet construction validation from view-map E211 in 03-01 Task 2.
- C2-A2 (LOW): add the resolved-mode/optional-icon migration contract paragraph to 03-02 Task 3, or explicitly defer it.


## Verification coverage

Source-grounding runs against revised plans at 5b1c9d5, using the deterministic CLI seams.
The orchestrator ran no product test suite; external reviewer prose is not a test-result record. Every unique literal path is listed with a quoted current plan occurrence;
repeated citations share the checked declaration. Direct reads corroborate names and mechanisms, not signatures.

## Authority and severity

```json
{
  "authority": "intel",
  "severity": {
    "VERIFIED": {
      "severity": "none",
      "hardBlock": false
    },
    "MISSING": {
      "severity": "needs-acknowledgement",
      "hardBlock": false
    },
    "AMBIGUOUS": {
      "severity": "MEDIUM",
      "hardBlock": false
    },
    "UNCHECKABLE": {
      "severity": "INFO",
      "hardBlock": false
    }
  },
  "phase_status": {
    "verdict": "consistent",
    "phase": "03",
    "stateStatus": "Ready to execute",
    "roadmapStatus": "Planned",
    "stateRank": 1,
    "roadmapRank": 1,
    "authority": "STATE.md"
  }
}
```

The effective authority remains **intel**. Its API-SURFACE.md declares the inventory incomplete and no
api-map.json is present. All Python declarations/signatures and template/browser/CLI semantics are
**UNCHECKABLE / INFO** under that adapter; no empty index absence is called MISSING. Supplemental direct
source evidence follows. Filesystem existence is VERIFIED independently of language analysis.
No hard block is emitted. New test symbols and execution reports are explicitly skipped phase outputs.

## Cited path inventory

| Path | Quoted current plan reference | Verdict | Evidence |
|---|---|---|---|
| `.planning/PROJECT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:92` — “@.planning/PROJECT.md” | VERIFIED | Filesystem presence; `.planning/PROJECT.md:1` |
| `.planning/ROADMAP.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:93` — “@.planning/ROADMAP.md” | VERIFIED | Filesystem presence; `.planning/ROADMAP.md:1` |
| `.planning/STATE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:94` — “@.planning/STATE.md” | VERIFIED | Filesystem presence; `.planning/STATE.md:1` |
| `.planning/phases/02-form-key-grammar/deferred-items.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:191` — “<read_first>CHANGELOG.md Unreleased Fixed; docs/migrating-1.0.md; .planning/PROJECT.md quality gates; .planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md; .planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md environment caveats; .planning/phases/02-form-key-grammar/deferred-items.md</read_first>” | VERIFIED | Filesystem presence; `.planning/phases/02-form-key-grammar/deferred-items.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:390` — “Create .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md with baseline capture commit/source HEAD,” | SKIPPED — phase output | Declared in the current plan’s Artifacts this phase produces section |
| `.planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:85` — “It produces .planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md as its execution report, including the” | SKIPPED — phase output | Declared in the current plan’s Artifacts this phase produces section |
| `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:95` — “@.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:97` — “@.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:96` — “@.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:98` — “@.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:99` — “@.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md:1` |
| `.venv/bin/mkdocs` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:148` — “<automated>.venv/bin/mkdocs build --strict</automated>” | VERIFIED | Filesystem presence; `.venv/bin/mkdocs` (binary/executable, no text line) |
| `.venv/bin/pytest` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:167` — “<precondition>The Phase 1 cv_get_action_label_mode and default_label_mode implementations exist in the tracked view modules, and .venv/bin/pytest plus the installed npm test harness are runnable.</precondition>” | VERIFIED | Filesystem presence; `.venv/bin/pytest` (binary/executable, no text line) |
| `.venv/bin/ruff` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:263` — “<automated>.venv/bin/ruff check</automated>” | VERIFIED | Filesystem presence; `.venv/bin/ruff` (binary/executable, no text line) |
| `/home/alex/.codex/gsd-core/templates/summary.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:88` — “@/home/alex/.codex/gsd-core/templates/summary.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/templates/summary.md:1` |
| `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:87` — “@/home/alex/.codex/gsd-core/workflows/execute-plan.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/workflows/execute-plan.md:1` |
| `CHANGELOG.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:15` — “- CHANGELOG.md” | VERIFIED | Filesystem presence; `CHANGELOG.md:1` |
| `CLAUDE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `CLAUDE.md:1` |
| `docs/migrating-1.0.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:13` — “- docs/migrating-1.0.md” | VERIFIED | Filesystem presence; `docs/migrating-1.0.md:1` |
| `docs/reference/action_menus.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:9` — “- docs/reference/action_menus.md” | VERIFIED | Filesystem presence; `docs/reference/action_menus.md:1` |
| `docs/reference/buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:10` — “- docs/reference/buttons.md” | VERIFIED | Filesystem presence; `docs/reference/buttons.md:1` |
| `docs/reference/context_buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:8` — “- docs/reference/context_buttons.md” | VERIFIED | Filesystem presence; `docs/reference/context_buttons.md:1` |
| `docs/reference/icons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:12` — “- docs/reference/icons.md” | VERIFIED | Filesystem presence; `docs/reference/icons.md:1` |
| `docs/reference/javascript.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:11` — “- docs/reference/javascript.md” | VERIFIED | Filesystem presence; `docs/reference/javascript.md:1` |
| `docs/test` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:145` — “docs before completing the paired docs/test change. Link related pages; keep the compact D-08 scope.” | UNCHECKABLE | Reference is a fragment/glob or uncreated artifact; no missing-source inference |
| `settings_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:316` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `settings_i18n.py:1` |
| `src/crud_views/lib/button_classes.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/button_classes.py:1` |
| `src/crud_views/lib/settings.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/settings.py:1` |
| `src/crud_views/lib/view/__init__.py` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:116` — “<read_first>docs/reference/context_buttons.md custom-template, rendering diagram and Import Paths sections; docs/reference/action_menus.md context resolution, Rendering and never-folded sections; docs/reference/buttons.md host fallback and mode class lookup; tests/test1/test_label_mode_docs.py test_canonical_label_mode_resolution_sections and test_label_mode_reference_links_and_diagram; src/crud_views/lib/view/__init__.py; src/crud_views/templates/crud_views/tags/context_action_filter.html; .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/__init__.py:1` |
| `src/crud_views/lib/view/base.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:61` — “to: src/crud_views/lib/view/base.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/base.py:1` |
| `src/crud_views/lib/view/button_data.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/button_data.py:1` |
| `src/crud_views/lib/view/buttons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:8` — “- src/crud_views/lib/view/buttons.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/buttons.py:1` |
| `src/crud_views/lib/view/label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/label_mode.py:1` |
| `src/crud_views/lib/views/mixins.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:73` — “to: src/crud_views/lib/views/mixins.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/views/mixins.py:1` |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:11` — “- src/crud_views/locale/de/LC_MESSAGES/django.mo” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.mo` (binary/executable, no text line) |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:10` — “- src/crud_views/locale/de/LC_MESSAGES/django.po” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.po:1` |
| `src/crud_views/static/crud_views/js/list.filter.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:69` — “to: src/crud_views/static/crud_views/js/list.filter.js” | VERIFIED | Filesystem presence; `src/crud_views/static/crud_views/js/list.filter.js:1` |
| `src/crud_views/templates/crud_views/tags/button/action.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/button/action.html:1` |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:9` — “- src/crud_views/templates/crud_views/tags/context_action_filter.html” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/context_action_filter.html:1` |
| `src/crud_views/templatetags/crud_views.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:65` — “to: src/crud_views/templatetags/crud_views.py” | VERIFIED | Filesystem presence; `src/crud_views/templatetags/crud_views.py:1` |
| `taskfile.yaml` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:316` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `taskfile.yaml:1` |
| `tests/js/list.filter.test.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:16` — “- tests/js/list.filter.test.js” | VERIFIED | Filesystem presence; `tests/js/list.filter.test.js:1` |
| `tests/lib/helper/icons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/lib/helper/icons.py:1` |
| `tests/test1/test_action_menus_context.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:296` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_context.py:1` |
| `tests/test1/test_action_menus_golden.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_golden.py:1` |
| `tests/test1/test_button_class_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_button_class_label_mode.py:1` |
| `tests/test1/test_button_leaves.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:13` — “- tests/test1/test_button_leaves.py” | VERIFIED | Filesystem presence; `tests/test1/test_button_leaves.py:1` |
| `tests/test1/test_context_action_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:14` — “- tests/test1/test_context_action_label_mode.py” | VERIFIED | Filesystem presence; `tests/test1/test_context_action_label_mode.py:1` |
| `tests/test1/test_context_button_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_label_mode.py:1` |
| `tests/test1/test_context_button_template.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_template.py:1` |
| `tests/test1/test_filter.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:296` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_filter.py:1` |
| `tests/test1/test_filter_pinned.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_filter_pinned.py:1` |
| `tests/test1/test_filter_toggle_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:12` — “- tests/test1/test_filter_toggle_label_mode.py” | SKIPPED — phase output | Declared in the current plan’s Artifacts this phase produces section |
| `tests/test1/test_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:15` — “- tests/test1/test_i18n.py” | VERIFIED | Filesystem presence; `tests/test1/test_i18n.py:1` |
| `tests/test1/test_label_mode_docs.py` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:14` — “- tests/test1/test_label_mode_docs.py” | VERIFIED | Filesystem presence; `tests/test1/test_label_mode_docs.py:1` |

## Declaration and field inventory

| Symbol | Quoted current plan reference | Effective-authority verdict | Supplemental source evidence |
|---|---|---|---|
| `FilterContextButton` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:26` — “- "EDGE-FILT-01-empty: A None button mode and an empty or unrelated view map reach the live context floor; the selected view map replaces lower maps. Direct FilterContextButton instances use their own override and declared key, never the list view's singular target default (D-01, D-02)."” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:298` — “class FilterContextButton(ContextButton):” |
| `FilterContextButton.get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:308` — “def get_context(self, context: ViewContext) -> dict:” |
| `CrudView` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:104` — “CrudView.cv_get_action_label_mode(location, key, button=None, target_default=None) returns a mode. For context,” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:61` — “class CrudView(metaclass=CrudViewMetaClass):” |
| `cv_get_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:44` — “contains: "cv_get_action_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:299` — “def cv_get_action_label_mode(” |
| `cv_get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:624` — “def cv_get_context(” |
| `cv_context_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:122` — “no target view and therefore ignores the current list view's singular cv_context_action_label_mode (D-01/D-02).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:100` — “cv_context_action_label_mode: str \| None = None” |
| `ViewContext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/context.py:9` — “class ViewContext(BaseModel, arbitrary_types_allowed=True):” |
| `_apply_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:61` — “def _apply_label(self, data: dict, context: ViewContext) -> None:” |
| `_apply_variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:74` — “def _apply_variant(self, data: dict) -> None:” |
| `_inject_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:79` — “def _inject_template(self, data: dict) -> None:” |
| `cv_button_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:525` — “def cv_button_class(location, slot, mode=None):” |
| `cv_icon_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:519` — “def cv_icon_class(value, location):” |
| `cv_icon` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:513` — “def cv_icon(value, css=""):” |
| `cv_context_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:187` — “cv_context_action rendering path and the existing session POST/GET path. Observe its behavioral failure before” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:228` — “def cv_context_action(context, key, obj=None):” |
| `ListViewTableFilterMixin` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:299` — “class ListViewTableFilterMixin(FilterView):” |
| `ListViewTableFilterMixin.post` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:336` — “def post(self, request, *args, **kwargs):” |
| `cv_filter_expanded` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:323` — “def cv_filter_expanded(self) -> bool:” |
| `default_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/label_mode.py:84` — “def default_label_mode(location: str) -> str:” |
| `HOST_LIBRARY` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:252` — “otherwise render the existing two children, including a host icon's standalone form (D-03). Use HOST_LIBRARY and” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:3` — “HOST_LIBRARY = {” |
| `HOST_ICONS` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:253` — “HOST_ICONS from the existing helper, and test both mixed directions plus empty/None host-slot configuration.” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:7` — “HOST_ICONS = {” |
| `ELIGIBLE` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:264` — “Replace the obsolete fixed-filter-mode comment beside ELIGIBLE in test_context_action_label_mode.py with a precise” | UNCHECKABLE / INFO | `tests/test1/test_context_action_label_mode.py:251` — “ELIGIBLE = './*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]'” |
| `_filter_toggle` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:170` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_button_leaves.py:574` — “def _filter_toggle(expanded: bool):” |
| `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:120` — “Show CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:67` — “context_actions_label_mode: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", default={})” |
| `label_template_code` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:261` — “Cover both label_template mechanisms” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:29` — “label_template_code: str \| None = None” |
| `label_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:261` — “priority. Cover both label_template mechanisms, variant mode keys and an empty custom label's fallback (D-07).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:28` — “label_template: str \| None = None” |
| `template_code` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:259` — “test-local in-memory templates for file-based custom labels and whole-button overrides, alongside template_code;” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:31` — “template_code: str \| None = None” |
| `label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:33` — “label_mode: str \| None = None  # None: the view's context label-mode maps; one of LABEL_MODES (#264)” |
| `variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:261` — “priority. Cover both label_template mechanisms, variant mode keys and an empty custom label's fallback (D-07).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:32` — “variant: str \| None = None  # None: the target view's cv_action_variant” |
| `self.key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:303` — “key: str = "filter"” |
| `cv_access` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:311` — “dict_kwargs = {"cv_access": False}” |
| `cv_key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:325` — “data["cv_key"] = self.key” |
| `cv_action_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:326` — “data["cv_action_label"] = "Filter"” |
| `cv_icon_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:327` — “data["cv_icon_action"] = "filter"” |
| `cv_url` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:329` — “data["cv_url"] = list_url” |
| `cv_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:47` — “contains: "cv_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:645` — “data = {**data, "cv_label_mode": mode, "cv_action_key": key}” |
| `target_default` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:300` — “cls, location: str, key: str, button: ContextButton \| None = None, target_default: str \| None = None” |
| `gettext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:38` — “- "EDGE-FILT-04-empty: The core German PO contains a non-fuzzy translated Filter entry and the compiled catalog contains the key explicitly; a missing entry cannot pass through gettext's identical-string fallback (D-09)."” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:95` — “def gettext(message):” |
| `override_settings` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/test/utils.py:468` — “class override_settings(TestContextDecorator):” |
| `translation.override` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:327` — “call with a different sentinel and custom-label precedence. Use translation.override("de") for the authenticated” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:189` — “class override(ContextDecorator):” |
| `render_to_string` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:181` — “compare render_to_string output directly: retain leading/trailing whitespace, attribute ordering and class ordering.” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/template/loader.py:52` — “def render_to_string(template_name, context=None, request=None, using=None):” |
| `cv_button_data` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/button_data.py:52` — “def cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict:” |
| `context_button_checks` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:350` — “def context_button_checks(context, viewset, buttons: list[ContextButton] \| None):” |
| `_action_settings_messages` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:236` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:100` — “def _action_settings_messages(self) -> list[CheckMessage]:” |
| `crud_views_settings` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:320` — “crud_views_settings = CrudViewsSettings()” |
| `setting_changed` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/button_classes.py:111` — “@receiver(setting_changed)” |
| `CRUD_VIEWS_BUTTON_CLASSES` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:191` — “use override_settings(CRUD_VIEWS_BUTTON_CLASSES=...) and its existing setting_changed cache-reset path on entry/exit;” | UNCHECKABLE / INFO | `src/crud_views/lib/button_classes.py:124` — “return getattr(settings, "CRUD_VIEWS_BUTTON_CLASSES", None) or {}” |
| `test_canonical_label_mode_resolution_sections` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:45` — “contains: "test_canonical_label_mode_resolution_sections"” | UNCHECKABLE / INFO | `tests/test1/test_label_mode_docs.py:180` — “def test_canonical_label_mode_resolution_sections():” |
| `test_label_mode_reference_links_and_diagram` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:116` — “<read_first>docs/reference/context_buttons.md custom-template, rendering diagram and Import Paths sections; docs/reference/action_menus.md context resolution, Rendering and never-folded sections; docs/reference/buttons.md host fallback and mode class lookup; tests/test1/test_label_mode_docs.py test_canonical_label_mode_resolution_sections and test_label_mode_reference_links_and_diagram; src/crud_views/lib/view/__init__.py; src/crud_views/templates/crud_views/tags/context_action_filter.html; .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_label_mode_docs.py:245` — “def test_label_mode_reference_links_and_diagram():” |
| `render_snippet` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “Explain in the fixture docstring that boundary whitespace is deliberately protected even where render_snippet strips” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:357` — “def render_snippet(cls, data: dict, template: str \| None = None, template_code: str \| None = None) -> str:” |

## Produced symbols excluded

- `_publisher_view` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `_render_filter` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `_filter_node` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `RAW_DEFAULT_FILTER` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `test_filter_raw_default_bytes` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; declared new phase artifact, skipped.
- `test_filter_both_tracer` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:50` — “contains: "test_filter_both_tracer"”; declared new phase artifact, skipped.
- `test_filter_mode_placement_matrix` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; declared new phase artifact, skipped.
- `test_filter_host_slot_fallback` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_mode_resolution` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_declared_key_and_direct_button` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_live_floor` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_customization` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_visibility` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_label_escaping` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_catalog_entry` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:126` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; declared new phase artifact, skipped.
- `test_filter_gettext_at_render_time` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:126` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; declared new phase artifact, skipped.
- `test_filter_german_render` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:127` — “test_filter_german_render; existing JS fixtures gain mode/label/initial-state options and described behavior cases.”; declared new phase artifact, skipped.
- `test_filter_direct_mode_fallback` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:123` — “test_filter_direct_mode_fallback, and test_filter_invalid_configuration_policy;”; declared new phase artifact, skipped.
- `test_filter_invalid_configuration_policy` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:123` — “test_filter_direct_mode_fallback, and test_filter_invalid_configuration_policy;”; declared new phase artifact, skipped.

## Additional uncheckable contracts

All signatures named in the interfaces section remain UNCHECKABLE. No existing decorator is cited as a
required API; @path entries are context imports. Pydantic/context attributes are covered above; no dataclass
or struct is required. Bare filenames alias full paths in the inventory. No missing source declaration was
confirmed by direct reads. The following semantics are UNCHECKABLE under intel:

- `gettext.GNUTranslations` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:324` — “the installed polib facility, and compiled membership as well as gettext result using gettext.GNUTranslations;”; UNCHECKABLE semantic/CLI contract.
- `polib` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:324` — “the installed polib facility, and compiled membership as well as gettext result using gettext.GNUTranslations;”; UNCHECKABLE semantic/CLI contract.
- `monkeypatch.setattr` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:188` — “implementation. Set the snapshot map with monkeypatch.setattr(crud_views_settings, "context_actions_label_mode",”; UNCHECKABLE semantic/CLI contract.
- `override_settings` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|”; UNCHECKABLE semantic/CLI contract.
- `NodeList` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:112` — “The JavaScript handler already tolerates an empty icon NodeList and preserves state after a rejected POST.”; UNCHECKABLE semantic/CLI contract.
- `cv_context_label_mode` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:198` — “_inject_template, per D-01/D-02/D-07. Do not introduce cv_context_label_mode, which the wrapper would treat as a target”; UNCHECKABLE semantic/CLI contract.
- `cv_filter_expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.”; UNCHECKABLE semantic/CLI contract.
- `cv-filter-toggle` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:71` — “pattern: "cv-filter-toggle"”; UNCHECKABLE semantic/CLI contract.
- `aria-expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:70` — “via: Stable toggle/panel IDs, aria-expanded, and optional host or child icon hooks”; UNCHECKABLE semantic/CLI contract.
- `aria-controls` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:250` — “render a visible label without title/tooltip while retaining type, IDs, cv-key, aria-expanded and aria-controls”; UNCHECKABLE semantic/CLI contract.
- `data-cv-filter-icon` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:193` — “direct path. Inspect icons as descendants of data-cv-filter-icon wrappers and visible labels with”; UNCHECKABLE semantic/CLI contract.
- `context:secondary:both` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:190` — “override_settings alone does not change this captured action map. For a distinct context:secondary:both class value,”; UNCHECKABLE semantic/CLI contract.
- `context:secondary:icon` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:192` — “do not register theme classes persistently. Also test a distinct context:secondary:icon override for the mode-less”; UNCHECKABLE semantic/CLI contract.
- `X-CSRFToken` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:30` — “- "EDGE-FILT-02-encoding: Each successful toggle sends the existing request path, POST method, X-CSRFToken and JSON content type with a boolean filter_expanded payload; label characters do not enter that payload (D-06, D-10)."”; UNCHECKABLE semantic/CLI contract.
- `filter_expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:30` — “- "EDGE-FILT-02-encoding: Each successful toggle sends the existing request path, POST method, X-CSRFToken and JSON content type with a boolean filter_expanded payload; label characters do not enter that payload (D-06, D-10)."”; UNCHECKABLE semantic/CLI contract.
- `E210` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `E211` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `E106` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `--check` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:338` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.
- `--check-format` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:338` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.
- `--strict` — `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:148` — “<automated>.venv/bin/mkdocs build --strict</automated>”; UNCHECKABLE semantic/CLI contract.
- `--prefix` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:219` — “<automated>npm --prefix . test -- tests/js/list.filter.test.js</automated>”; UNCHECKABLE semantic/CLI contract.
- `-q` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:217` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py tests/test1/test_button_leaves.py -q</automated>”; UNCHECKABLE semantic/CLI contract.
- `-n auto` — `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:257` — “<automated>.venv/bin/pytest tests -n auto</automated>”; UNCHECKABLE semantic/CLI contract.
- `--check` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:338` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.

Browser querySelectorAll/textContent, Promise settlement and DOM identity are uncheckable semantics.
Direct evidence: list.filter.js:15 collapse first, :29 optional icon loop, :34–38 per-click captured payload and
rejection-only handler, :51 reset; context_action_filter.html:4–13 disclosure/icon/label attributes.
CLI names pytest/npm/mkdocs/ruff/msgfmt and all command signatures remain UNCHECKABLE; executable presence
is distinct from running checks. Catalog references resolve to existing test_i18n.py:66–88 patterns.
Future baseline commit capture is execution work, not an invented verified commit.

## Cross-artifact fact drift

The phase-status CLI result above is consistent. Other comparisons are independent judgment checks:

| Same fact | Authority | Current plan evidence | Verdict |
|---|---|---|---|
| Mode/default-output contract | ROADMAP.md:115–116 | 03-01 must_haves truths and Task 1 raw/default behavior | Consistent; raw fixture is additive |
| Icon-less persistence | ROADMAP.md:117–118 | 03-01 Task 2 requires no hooks, collapse and boolean POST | Consistent |
| Constant visible text | ROADMAP.md:119 | 03-01 truths and Task 2 require node/text identity | Consistent |
| German translation | ROADMAP.md:120 | 03-01 Task 3 requires PO/MO membership, runtime sentinel, German render | Consistent; distinct evidence claims refine the criterion |
| FILT-01..04 | ROADMAP.md:112 | Both plan frontmatter requirements | Identical IDs |
| No target default and declared key | CONTEXT.md:23–29 | 03-01 resolver instruction and 03-02 examples | Consistent |
| Host fallback, label constancy, accessibility | CONTEXT.md:32–45 | 03-01 three-mode and error matrices | Consistent |
| Customization, compact docs, gettext | CONTEXT.md:48–55 | 03-01 Tasks 1/3 and 03-02 Task 1 | Consistent |
| Stable behavior and release gates | CONTEXT.md:58–61 | 03-01 no JavaScript change; 03-02 Fixed/migration and full gates | Consistent |

No authoritative pair contradicts. Discretion/deferred ideas are excluded. A source-plan branch name and
observed retained branch describe provenance versus execution, not a conflicting domain fact; branch changes
remain outside scope. Scope omissions and cross-plan disagreements belong to the checker, not this drift pass.
