---
phase: "02"
reviewers: ["fable-review", "grok-review", "gemini-review", "deepseek-review"]
reviewed_at: 2026-10-26T12:53:00.030980+00:00
plans_reviewed: ["02-01-PLAN.md"]
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

> Note: grok-review, gemini-review and deepseek-review share the opencode adapter; their consensus is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 02

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts
None. No locked decisions were changed.
<!-- gsd:plan-revision-conflicts:end -->

Retrospective review of plan 02-01 and its committed implementation through d3c63f2. All four configured external reviewer instances completed successfully and covered plan 02-01. The reports below are preserved verbatim; their citations refer to the pre-correction source snapshot. Model values record the configured pins reported by the GSD runner, not independent provider attestation.

## Claude Review (fable-review)

## 02-01

**Summary**

Plan `.planning/phases/02-form-key-grammar/02-01-PLAN.md` promised a finite form-kind grammar, independent location sets, exact W362 diagnostics, a documented grammar and a live key-count guard. The implementation on `introduce-gsd` delivers all of it. The production change is confined to one function and two constants in `src/crud_views/lib/button_classes.py:207-226`. The diff since plan start touches exactly the five product files the plan lists, with no template, golden, crispy adapter or button-data change.

One verification caveat. The focused pytest run and a Python tally script were denied in this session, so I could not execute tests myself. Test results below are traced statically from the test source and taken from the recorded evidence in `02-VALIDATION.md:89-109`. Everything else was verified by reading the current source and commit diffs.

**Strengths**

- **Grammar is finite and two-staged as decided.** `src/crud_views/lib/button_classes.py:222-224` accepts a three-segment key only when the first two segments are a variant-location/variant pair or `form` plus one of five kinds. The mode is returned unchanged, and `_is_action_mode_key` at `:229-234` still does the `LABEL_MODES` membership check. So `form:submitt:icon` falls to the unknown-key branch at `:290-297` and `form:submit:iconn` falls to the unknown-mode branch at `:282-289`. That is D-03 and D-05 exactly.
- **Decoupling from button-data locations is real, not nominal.** Commit a6322d0 removed the `from .view.button_data import LOCATIONS` import entirely. The regression test at `tests/test1/test_button_classes_checks.py:227-246` monkeypatches `button_data.LOCATIONS` to include `form` and `test-location` and asserts all eight variant-shaped keys still warn. A function-local import would read the patched module attribute at call time, so recoupling the validator to `LOCATIONS` would make this test fail. KEYS-03 is enforced, not merely stated.
- **Acceptance matrix is complete and independent of production constants.** `tests/test1/test_button_classes_checks.py:111-113` define the expected kinds, modes and variants as literals, and `:124-128` assert `bc.FORM_KINDS` equals that literal set before the parametrized matrix at `:131-151` runs 5 kinds × 3 modes × 2 sources. `None` and `""` values are covered at `:138-143`. The research pitfall "a missing kind silently removes its own case" is closed.
- **Diagnostics are asserted by type, ID, message and hint.** `:184-189` and `:195-201` check `type(message) is DjangoWarning` and the exact strings, including the locked examples and whitespace/case typos. `:204-207` proves a valid form-mode key with a non-string value yields E361 only. `:217-224` proves the hint stays sorted regardless of registration order.
- **Resolver semantics preserved and now tested for form keys.** `get_button_class` at `button_classes.py:136-147` is untouched. `tests/test1/test_button_classes.py:206-234` cover presence override, single-step fallback, `None`/`""` suppression, theme-mode over settings-base, and settings winning at the same exact key.
- **Count guard matches the plan's shape.** `tests/test1/test_button_classes.py:94-98` requires exactly one `The default table has (\d+) keys` match and compares the integer to `len(DEFAULT_BUTTON_CLASSES)`. The docs sentence at `docs/reference/buttons.md:144` now says 70. I tallied the key table at `buttons.md:95-142` by hand and it lists 70 keys, so the table and the sentence agree. The redundant "count stays 64" claim is gone (`:146-148`).
- **D-10 invariants still hold.** `tests/test1/test_label_mode.py:67` asserts `set(LABEL_MODE_DEFAULTS) == LOCATIONS` and `tests/test1/test_action_label_mode_config.py:323` still rejects a `form` floor with E108. `src/crud_views/lib/view/button_data.py:12` still has three locations.
- **Docs and changelog land where the plan said.** The grammar table, valid/invalid examples and fallback example sit under `## The class table` at `buttons.md:46-86`. The W362 row at `buttons.md:479` now names both families. The changelog bullet at `CHANGELOG.md:187-189` is under the Unreleased `### Added` heading (Unreleased starts at line 3, the next release heading is at line 308). No Breaking entry, so no migration-guide update was required.
- **Import boundary kept.** `_action_key_parts` still imports `VARIANTS` locally (`button_classes.py:217`), and the AST guard at `tests/test1/test_button_classes.py:253-264` still forbids module-level view imports.

**Concerns**

No HIGH or MEDIUM findings. The following are LOW.

- **LOW, docs accuracy:** `docs/reference/buttons.md:60` explains `form:container:icon` as "adds a mode to a structural slot". There is no `form:container` key in the default table (`formset:container` exists, `form:container` does not). The key is rejected because `container` is not a form kind, not because a structural slot gained a mode. A reader could infer that `form:container` is a valid base key. This is exactly the kind of prose point the pending human review should catch.
- **LOW, stale wording elsewhere:** `docs/reference/icons.md:158` still says mode markers belong in `location:variant:mode` keys. It is not wrong today because form buttons do not render icons until Phase 6, but it will read as incomplete once `form:<kind>:<mode>` is the second family. Phase 6 or Phase 7 should touch it.
- **LOW, new public names undocumented:** `VARIANT_LOCATIONS` and `FORM_KINDS` are exported without underscore (`button_classes.py:207-208`) but appear nowhere in docs or the changelog. Phase 7's stability tiering will have to classify them, and a theme author could start importing them before that classification exists.
- **LOW, drift guard between kinds and defaults:** `FORM_KINDS` is a hand-maintained literal. The test at `test_button_classes_checks.py:124-128` pins it to five names, which catches accidental edits, but nothing asserts that every kind has a `form:<kind>` base entry in `DEFAULT_BUTTON_CLASSES`. If Phase 6 adds a sixth kind to the table and forgets the set, its mode keys would warn as unknown with no test pointing at the cause.
- **LOW, history contains red commits by design:** 8876078 and ea81ead each commit a failing test ahead of the fix. This follows the project's TDD commit convention, but `git bisect` across this range will land on intentionally red states.
- **LOW, encoding in the count guard:** `tests/test1/test_button_classes.py:95` uses `read_text()` without an encoding, and `buttons.md` contains U+2026 and U+2014 (lines 180-182, 206, 246). This matches the existing pattern in `tests/test1/test_label_mode_docs.py`, and both characters exist in cp1252, so it is unlikely to bite. It is still locale-dependent on Windows before Python 3.15.

**Suggestions**

- Reword `buttons.md:60` so `form:container:icon` is explained as "`container` is not a form kind" rather than as a structural slot with a mode.
- Add a one-line test that `{f"form:{kind}" for kind in FORM_KINDS} <= set(DEFAULT_BUTTON_CLASSES)` next to `test_class_key_vocabularies_are_finite_and_immutable`.
- Mention `VARIANT_LOCATIONS` and `FORM_KINDS` in the Phase 7 stability inventory now, or add a note in the Phase 7 context so they are not missed.
- Consider renaming `_action_key_parts` to something like `_mode_key_parts` in a later refactor, since it now recognizes form keys too. Cosmetic only.
- Pass `encoding="utf-8"` to the new `read_text()` call, or leave it to match the existing docs tests. Either is defensible.

**Risk Assessment**

Low. The runtime path is unchanged: `DEFAULT_BUTTON_CLASSES`, `get_button_class`, the crispy adapters at `src/crud_views/lib/crispy/buttons.py:16-30`, and the templates are byte-identical. The only behavioral change is that fifteen previously warned keys are now accepted by a system check, which is strictly compatible. The future-location test gives Phase 6 a tripwire. The remaining items are documentation polish and forward-looking hygiene.

## Overall assessment

Phase 2's goal is met. The class table now has one documented, check-enforced rule for the second segment, form kinds accept all three modes without loosening W362, the validator no longer depends on button-data locations, and the documented count is pinned to the live table. Every plan `must_haves` truth traces to current source or a current test. The plan's two flagged "unclassified" probe rows (KEYS-01, KEYS-02) are not implementation gaps. KEYS-02 is fully covered by the explicit matrix, and KEYS-01 only awaits the human prose review already scheduled.

What I could not confirm: I did not execute the test suite or the docs build in this session because the commands were denied. The recorded results in `02-VALIDATION.md` (3360 passed, strict MkDocs green, Vitest green, no golden diff) are consistent with everything I traced, but they are the executor's evidence, not mine.

Recommended next step: proceed to phase verification. During the human prose review, fix the `form:container:icon` wording at `buttons.md:60` and note the two new public constant names for Phase 7.


---

## OpenCode Review (grok-review)

I'll review the implemented form-key grammar against the plan and current source, not the plan text alone.
The grammar helpers are in place. Next I’ll check docs, changelog, and whether the tests actually lock the boundaries the plan requires.
## 02-01

### Summary

Option A is implemented and check-enforced. `form:<kind>:<mode>` is accepted for the five shipped kinds, action keys still use variants, and class-key locations no longer follow `button_data.LOCATIONS`. Rendering, defaults, and W362 wording are unchanged. KEYS-01 through KEYS-04 hold in source. The flagged KEYS-01/KEYS-02 probe rows were classifier gaps, not open product decisions.

### Strengths

- Shape and mode stay two stages. `_action_key_parts` accepts only a `VARIANT_LOCATIONS`/`VARIANTS` pair or `form`/`FORM_KINDS`, then `_is_action_mode_key` checks `LABEL_MODES` (`src/crud_views/lib/button_classes.py:207-234`). `form:submitt:icon` and `form:primary:icon` stay unknown-key warnings. `form:submit:iconn` stays the unknown-mode warning (`src/crud_views/lib/button_classes.py:279-296`). That is the split `.planning/phases/02-form-key-grammar/02-01-PLAN.md:154-157` required.
- Adding `"form"` to button-data locations cannot admit `form:primary:icon`. The helper no longer imports `LOCATIONS` (`src/crud_views/lib/button_classes.py:217-223`). The regression widens `button_data.LOCATIONS` and still expects those variant keys to warn (`tests/test1/test_button_classes_checks.py:227-246`). E108 still uses button-data locations (`src/crud_views/lib/settings.py:105-166`). `LOCATIONS` is still only `context`/`list`/`card` (`src/crud_views/lib/view/button_data.py:12`).
- All 15 kind/mode pairs are accepted from settings and theme registration with no icon configured (`tests/test1/test_button_classes_checks.py:111-135`). The tracer goes through `check_button_classes()` into `get_button_class` (`tests/test1/test_button_classes_checks.py:30-33`, `src/crud_views/checks.py:404-407`). `form:submit:icon` was removed from the rejection list.
- Lookup is still presence-based and was not rewritten (`src/crud_views/lib/button_classes.py:136-147`). None and `""` suppress the base. A theme mode key beats a settings base key (`tests/test1/test_button_classes.py:206-234`). Crispy still splits `slot` once and passes no mode (`src/crud_views/lib/crispy/buttons.py:16-17`).
- The class-table anchor has the three-family table, the locked examples, and the fallback (`docs/reference/buttons.md:46-86`). The count sentence is the only match for the guard and is 70 (`docs/reference/buttons.md:144-148`, `tests/test1/test_button_classes.py:94-98`). The changelog is an Unreleased Added note, not Breaking (`CHANGELOG.md:187-189`). The product diff is those five files.

### Concerns

**LOW** — The settings section of the same page still states the old W362 rule. `docs/reference/buttons.md:239` says a key warns unless it is in the default table or is `location:variant:mode`. `form:submit:icon` is neither, so that sentence says it warns. The validator accepts it (`src/crud_views/lib/button_classes.py:222-225`), and the class-table section and the system-check row both say so (`docs/reference/buttons.md:54-62`, `docs/reference/buttons.md:479`). The plan asked for the W362 reference row (`02-01-PLAN.md:275`), which was updated. This second statement was left behind, so the page documents two rules.

### Suggestions

- Extend `docs/reference/buttons.md:239` to the same `form:kind:mode` wording as line 479. `docs/reference/settings.md:153` and `docs/migrating-1.0.md:290-291` still say `location:slot` / `location:variant:mode` only. Those were out of this plan's file list. A link is enough until the next docs pass.
- `docs/reference/buttons.md:86` tells theme authors the rest "belong to Phase 6". The boundary is right, but that label is not a public name. Say the form leaves and floors are not in this release.
- Phase 4 should classify `VARIANT_LOCATIONS` and `FORM_KINDS`. They are public module attributes and are not in the theme-surface doc yet.

### Risk Assessment

Low. The grammar, diagnostics, location split, count guard, and no-render constraint match the plan. I did not re-run the suite. Recorded validation is 3360 passed on Python 3.12.3 / Django 5.2.14, with the Ruff 0.16.10 versus `>=0.17,<0.18` mismatch and the unrun matrix already noted. Neither changes this review.

## Overall assessment

Plan 02-01 meets its phase goal. The only open item is the stale W362 sentence at `docs/reference/buttons.md:239`. That should be fixed before the grammar page is treated as the single rule, but it does not weaken the check.


---

## OpenCode Review (gemini-review)

## 02-01

### Summary

Plan `.planning/phases/02-form-key-grammar/02-01-PLAN.md` and its implementation on `introduce-gsd` (commits `8876078`, `a6322d0`, `340d29a`, `ea81ead`, `d3c63f2`) cleanly deliver `KEYS-01` through `KEYS-04` and decisions `D-01` through `D-11`. The class-table validator in `src/crud_views/lib/button_classes.py` now enforces Option A (`form:<kind>:<mode>`) using explicit immutable sets decoupled from `button_data.LOCATIONS`, while preserving `DEFAULT_BUTTON_CLASSES`, `get_button_class()`, `W362`/`E361` diagnostics, and bare-settings importability. Two minor documentation prose issues in `docs/reference/buttons.md` were found during the manual prose check required by `.planning/phases/02-form-key-grammar/02-01-PLAN.md:65-74,295`.

### Strengths

- **Decoupled, finite grammar sets with preserved bare-settings import safety (`KEYS-02`, `KEYS-03`, `D-01`–`D-03`, `D-10`):** `src/crud_views/lib/button_classes.py:207-226` defines `VARIANT_LOCATIONS: frozenset[str] = frozenset({"context", "list", "card"})` and `FORM_KINDS: frozenset[str] = frozenset({"submit", "cancel", "delete", "filter-submit", "filter-reset"})` at module scope while keeping `from .view.variant import VARIANTS` (`src/crud_views/lib/button_classes.py:217`) and `from .view.label_mode import LABEL_MODES` (`src/crud_views/lib/button_classes.py:231,277`) function-local. This satisfies `.planning/phases/02-form-key-grammar/02-01-PLAN.md:154-160` without importing `crud_views.lib.view` at module load time (verified by the AST guard in `tests/test1/test_button_classes.py:253-264`), and leaves `src/crud_views/lib/view/button_data.py:12` (`LOCATIONS`) and `src/crud_views/lib/view/label_mode.py:23,84-117` (`LABEL_MODE_DEFAULTS`, `default_label_mode`) untouched.
- **Preserved two-stage `W362` diagnostic distinction (`KEYS-02`, `D-05`, `D-06`):** Because `_action_key_parts()` (`src/crud_views/lib/button_classes.py:211-226`) returns the 3-tuple whenever `(location, slot)` matches either `VARIANT_LOCATIONS × VARIANTS` or `"form" × FORM_KINDS` and `_is_action_mode_key()` (`src/crud_views/lib/button_classes.py:229-234`) checks `parts[2] in LABEL_MODES`, `button_class_check_messages()` (`src/crud_views/lib/button_classes.py:279-297`) routes `form:submit:iconn` to the unknown-mode branch (`"Button class 'form:submit:iconn' has an unknown label mode 'iconn'."`) while routing `form:submitt:icon`, `form:container:icon`, and `form:primary:icon` to the unknown-key branch (`"Button class ... is not a known key (typo?)."`).
- **Thorough boundary and isolation test coverage (`KEYS-02`, `KEYS-03`, `D-02`–`D-07`):** `tests/test1/test_button_classes_checks.py:111-247` defines independent expected tuples (`FORM_KINDS`, `MODES`, `VARIANTS`) rather than deriving test parameters from production constants (fulfilling `.planning/phases/02-form-key-grammar/02-01-PLAN.md:201-204`). It tests all 5 kinds × 3 modes across both `settings` and `theme` sources (`lines 131-144`), exact `DjangoWarning` class/ID/message/hint assertions for both `W362` branches (`lines 154-202`), `E361`-only non-string value handling (`lines 204-207`), and future `button_data.LOCATIONS` expansion via `monkeypatch.setattr(button_data, "LOCATIONS", button_data.LOCATIONS | {"form", "test-location"})` (`lines 227-247`).
- **Executable default-key count contract and form fallback tests (`KEYS-04`, `D-04`, `D-09`):** `tests/test1/test_button_classes.py:94-98` (`test_documented_default_key_count_matches_table`) enforces a single canonical match for `r"The default table has (\d+) keys\b"` in `docs/reference/buttons.md:144` and compares `int(counts[0])` against `len(DEFAULT_BUTTON_CLASSES)` (`70`), while `tests/test1/test_button_classes.py:206-235` verifies presence-based override, base fallback, `None`/`""` suppression, and theme-mode vs settings-base precedence for form keys without modifying `get_button_class()` (`src/crud_views/lib/button_classes.py:136-147`) or `src/crud_views/lib/crispy/buttons.py:16-30`.

### Concerns

- **[LOW] (Unresolved implementation/plan prose defect) Internal GSD phase numbering leaked into user-facing reference docs:** `.planning/phases/02-form-key-grammar/02-01-PLAN.md:270-271` instructed the task to note that `"form label floors/leaves/missing-icon checks belong to Phase 6 (D-01,D-04,D-07,D-10)"`, and `docs/reference/buttons.md:85-86` was written literally as: `"Form label floors, form button leaves, and missing-icon rendering checks belong to Phase 6."` No other file under `docs/` references internal GSD planning phase numbers (`Phase 6` has no meaning to package users or theme authors reading MkDocs output).
- **[LOW] (Unresolved implementation defect) Secondary `W362` prose in `docs/reference/buttons.md` still omits `form:kind:mode`:** While `.planning/phases/02-form-key-grammar/02-01-PLAN.md:275-276` updated the `## The class table` grammar (`docs/reference/buttons.md:51-62`) and the `## System checks` table row (`docs/reference/buttons.md:479`) to cover both `location:variant:mode` and `form:kind:mode`, the prose under `## CRUD_VIEWS_BUTTON_CLASSES` at `docs/reference/buttons.md:239-240` was overlooked and still reads: `"A key that is neither in the table above nor a valid location:variant:mode is reported by crud_views.W362 (a typo, or an unknown label mode)."`
- **[LOW] (Plan/environment risk — tracked, non-blocking) Ruff version mismatch and unexecuted matrix combinations:** As noted in `.planning/phases/02-form-key-grammar/02-01-PLAN.md:332-337` and `.planning/phases/02-form-key-grammar/02-01-SUMMARY.md:119-122,153-155`, the local `.venv` has Ruff `0.16.10` whereas `pyproject.toml` specifies `>=0.17,<0.18`. This was properly handled without scope-expanding dependency edits during Phase 02.

### Suggestions

- In `docs/reference/buttons.md:84-86`, replace the internal milestone reference (`"Form label floors, form button leaves, and missing-icon rendering checks belong to Phase 6."`) with user-facing wording (or drop the sentence after `"Crispy form buttons continue using their existing slot= calls without choosing a mode, so their rendering is unchanged."`).
- In `docs/reference/buttons.md:239-240`, update `"neither in the table above nor a valid location:variant:mode"` to `"neither in the table above nor a valid location:variant:mode or form:kind:mode"` (matching `docs/reference/buttons.md:479`).

### Risk Assessment

- **Overall Risk:** Low.
- **Runtime / Compatibility Risk:** None. `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:15-95`), `get_button_class()` (`src/crud_views/lib/button_classes.py:136-147`), `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/view/label_mode.py`, templates, and goldens are unchanged.
- **Security Risk:** None. Input validation in `_action_key_parts()` safely guards non-string keys (`src/crud_views/lib/button_classes.py:219-220`), allow-lists are finite `frozenset` constants (`lines 207-208`), and HTML escaping in `{% cv_button_class %}` remains covered by `tests/test1/test_button_classes.py:164-170`.

## Overall Assessment

Plan `02-01` and its implementation satisfy all four phase requirements (`KEYS-01`, `KEYS-02`, `KEYS-03`, `KEYS-04`) and all locked context decisions (`D-01`–`D-11`). The code changes in `src/crud_views/lib/button_classes.py` and the test suites in `tests/test1/test_button_classes_checks.py` and `tests/test1/test_button_classes.py` are exact, minimal, and well-isolated for Phase 6. Addressing the two minor prose items in `docs/reference/buttons.md:86` and `docs/reference/buttons.md:239` will complete the human documentation review flagged in `.planning/phases/02-form-key-grammar/02-01-PLAN.md:65-74,295`.


---

## OpenCode Review (deepseek-review)

I'll review the implementation of Phase 02 plan 02-01 by examining the actual code and comparing it to the plan requirements.
Now let me examine specific test files to understand the implementation:
Let me check the count test:
Let me run a test to verify the implementation:
Now let me check if the implementation handles the split between VARIANT_LOCATIONS and button_data LOCATIONS:
Let me check the count test:
Now let me look at the system check to see if it properly reports form kind mode errors:
Now let me check if the CHANGELOG has been updated:
Now let me look at the button_data.py to see if form is in LOCATIONS yet:
Perfect! Now let me check if there are any missing form:hidden-label or form:icon-host keys:
Interesting! The plan mentioned adding these keys in Phase 2 but they're not there. Let me check if the test suite still passes:
Now let me examine the detailed implementation to provide a comprehensive review:

## 02-01

### Summary

The implementation successfully delivers the class-key grammar validation and documentation as specified in the plan. The code shows clear evidence that:

1. **VARIANT_LOCATIONS** and **FORM_KINDS** are defined as frozen sets in `button_classes.py:207-208`
2. The `_action_key_parts` function has been updated to recognize both variant locations and form kinds
3. Comprehensive test coverage exists for all five form kinds across three modes
4. Documentation has been updated with the correct grammar table and count (70 keys)
5. The changelog entry exists

### Strengths

**src/crud_views/lib/button_classes.py:207-208**: `VARIANT_LOCATIONS` and `FORM_KINDS` are properly defined as frozen sets, keeping class-key grammar independent from button-data locations.

**src/crud_views/lib/button_classes.py:223-224**: The `_action_key_parts` function correctly implements the Option A grammar: it accepts either `(location in VARIANT_LOCATIONS and slot in VARIANTS)` OR `(location == "form" and slot in FORM_KINDS)`.

**tests/test1/test_button_classes_checks.py:30-33**: The tracer test `test_form_submit_icon_key_reaches_checks_and_lookup` proves the real check/lookup path works.

**tests/test1/test_button_classes_checks.py:228-247**: The `test_future_button_data_locations_cannot_widen_class_key_grammar` test successfully isolates class-key grammar from button-data locations by monkeypatching `LOCATIONS` and verifying variant-shaped keys at the new locations are still rejected.

**tests/test1/test_button_classes.py:94-99**: The count guard `test_documented_default_key_count_matches_table` parses the documentation and asserts equality with `len(DEFAULT_BUTTON_CLASSES)`.

**docs/reference/buttons.md:51-62**: The grammar table clearly distinguishes action variants, form kinds, and structural slots, with explicit examples including `form:submit:icon`, `form:cancel:both`, and rejection explanations for `form:submitt:icon`, `form:container:icon`, etc.

### Concerns

**MEDIUM**: Missing `form:hidden-label` and `form:icon-host` keys. The plan mentioned in RESEARCH.md S3 that these keys should be added in Phase 2 to support form leaf rendering in Phase 6. Without them, Phase 6 form leaf implementation will need to add them or handle missing keys.

**src/crud_views/lib/button_classes.py**: The current `DEFAULT_BUTTON_CLASSES` lacks `form:hidden-label` and `form:icon-host`, which means:
- Icon-only form buttons won't have visually hidden labels
- Host-placed icon libraries won't work on form buttons

**LOW**: Documentation could be more explicit about the separation between validation grammar and rendering eligibility. While the docs mention "crispy form buttons continue using their existing slot calls without choosing a mode", it could be clearer that form validation doesn't imply form rendering support yet.

### Suggestions

1. **Add missing form keys**: Consider adding `form:hidden-label: "visually-hidden"` and `form:icon-host: "{name_class}"` to `DEFAULT_BUTTON_CLASSES` to prepare for Phase 6 form leaf implementation.

2. **Update tests**: The `test_icon_host_default_slots` in `test_button_classes.py` should include `"form"` to verify the icon-host key exists once added.

3. **Clarify Phase 6 dependency**: The documentation could more explicitly state that while form mode keys are now valid, actual form button rendering with modes will be implemented in Phase 6.

### Risk Assessment

**Correctness**: HIGH - The implementation correctly validates all form kind/mode combinations, maintains backward compatibility, and preserves exact warning diagnostics.

**Scope**: MEDIUM - The plan boundary is respected (validation-only, no rendering changes). The missing `form:hidden-label` and `form:icon-host` keys are a minor scope gap but don't affect current functionality.

**Dependencies**: LOW - No dependencies on other phases; Phase 6 can build on this foundation.

**Security**: LOW - No security implications; this is validation-only with no rendering changes.

**Phase Goals Met**: YES - KEYS-01 through KEYS-04 are satisfied. The documented grammar is implemented and enforced, the key count is pinned, and class-key validation is isolated from button-data locations.


---

## Consensus Summary

### Agreed Strengths

All four reviewers find that KEYS-01 through KEYS-04 are satisfied: finite kind/variant grammar, separate class-key locations, preserved diagnostics and resolver semantics, unchanged defaults/rendering, and a live 70-key documentation count guard. They cite actual implementation and tests. No review lacks repository access or source citations. Claude could not execute tests because its commands were denied; Grok explicitly did not rerun tests. Their static reviews are not independent test executions.

### Agreed Concerns

- Gemini and Grok identify the stale W362 sentence under the settings section, which omitted form-kind mode keys. Fixed by linking to the canonical grammar and naming both families.
- Gemini and Grok identify internal phase numbering in public documentation; DeepSeek asks for a clearer validation-versus-rendering boundary. Fixed with user-facing wording explicitly stating that accepting class keys does not enable mode selection or icon rendering for crispy buttons.

### Divergent Views

- DeepSeek's sole MEDIUM finding requests `form:hidden-label` and `form:icon-host` in this phase. Source adjudication rejects the claimed plan requirement: `02-01-PLAN.md:161-163` preserves `DEFAULT_BUTTON_CLASSES`, `02-01-PLAN.md:270-271` defers form rendering, and `02-RESEARCH.md:65-78` explicitly keeps defaults unchanged. The asserted research "S3" requirement is absent. These keys may be considered by Phase 06; adding them now would conflict with the agreed boundary.
- DeepSeek's "Correctness: HIGH" label is accompanied by an affirmative correctness assessment, not a HIGH-severity defect. It is retained verbatim above and is not counted as a blocker.
- Claude alone catches the inaccurate explanation of `form:container:icon`: no `form:container` base key exists. Fixed to say that `container` is not a form kind.
- Claude and Grok suggest classifying the two new constants in the stability inventory. This belongs to Phase 07 (Grok's Phase 4 reference is incorrect; see ROADMAP.md). No public stability guarantee is added by this review.

## Finding Disposition

| Finding or suggestion | Decision | Evidence / follow-up |
|---|---|---|
| Stale W362 prose (Gemini/Grok, LOW) | Fixed | Settings section now links to the canonical grammar and names both mode-key families. |
| Internal phase numbering / unclear rendering boundary (Gemini/Grok/DeepSeek, LOW) | Fixed | Public docs explicitly distinguish key acceptance from crispy rendering support. |
| `form:container` explanation (Claude, LOW) | Fixed | Docs now state `container` is not a form kind. |
| Missing form utility keys (DeepSeek, MEDIUM) | Rejected for Phase 02 | PLAN.md:161-163 and RESEARCH.md:65-78 preserve defaults; form leaves remain Phase 06. |
| Public constant stability classification (Claude/Grok, LOW) | Deferred to Phase 07 | `VARIANT_LOCATIONS` and `FORM_KINDS` need classification with the planned theme-surface policy. |
| Icons reference / settings and migration summaries (Claude/Grok, LOW/suggestion) | Deferred to relevant docs pass | Icons prose describes current action rendering; settings/migration summaries already link to the buttons reference. Canonical Phase 02 grammar is corrected. |
| Form-kind/default-key synchronization assertion (Claude, LOW) | Deferred to form expansion | Existing tests independently pin all five kinds and defaults. A future kind/default change should add the corresponding regression in Phase 06. |
| Locale-independent count-test read (Claude, LOW) | Deferred | Existing repository docs tests use the same read_text convention; this review makes no test-platform refactor. |
| Intentionally RED history (Claude, LOW) | Accepted convention | Separate failing-test commits are the recorded GSD execution history; no history rewrite. |
| Ruff version mismatch / unrun interpreter matrix (Gemini, LOW) | Existing limitation retained | See deferred-items.md and 02-01-SUMMARY.md. |
| Rename private shape helper (Claude, suggestion) | Deferred cosmetic refactor | Updated docstring already covers both variants and kinds; runtime behavior is correct. |

## Post-review Validation

Only `docs/reference/buttons.md` changed as a result of review. No production code, default entry, resolver, template or golden changed.

- `.venv/bin/pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q`: **350 passed**.
- `.venv/bin/mkdocs build --strict`: **passed**.
- The earlier full execution validation remains recorded in `02-01-SUMMARY.md`: 3360 Python passed, one existing skip; 126 Vitest passed.

**Adjudicated outcome:** no confirmed HIGH or MEDIUM defect. Three documentation corrections applied; forward-looking LOW suggestions remain explicitly tracked above. This external review does not replace the pending phase verification or the user's end-of-phase prose review.
