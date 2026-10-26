# Phase 2: Form key grammar - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Define and enforce the class-table key grammar for form buttons (source plan 1C; KEYS-01 through KEYS-04).
Document the meaning of the second segment and which keys accept a label-mode suffix. Separate class-key
validation sets from button-data locations so Phase 6 cannot accidentally loosen W362. Correct the documented
default-key count and pin it to `len(DEFAULT_BUTTON_CLASSES)` with a test.

There is no rendering or golden change. Form-button leaves, adding `form` to button-data/label-mode locations,
new form utility keys, and missing-icon rendering checks remain Phase 6 work.

</domain>

<decisions>
## Implementation Decisions

### Form kinds and modes
- **D-01:** Choose Option A: retain `form:<kind>` and accept `form:<kind>:<mode>`. Preserve all shipped form
  keys and the crispy adapters' `slot=` usage. Option B (variants everywhere) was considered and rejected after
  a comparison of consistency, independent role styling, theme maintenance, and migration costs.
- **D-02:** The five form kinds are `submit`, `cancel`, `delete`, `filter-submit`, and `filter-reset`.
  Every kind accepts all three modes: `icon`, `both`, and `label`. Do not restrict modes by kind.
- **D-03:** Context/list/card action keys retain variants as their second segment. Form keys use kinds.
  Structural and utility slots do not accept mode suffixes. In particular, `form:submitt:icon` and
  `form:container:icon` remain invalid; choosing kinds does not admit `form:primary:icon`.
- **D-04:** Keep existing mode-key lookup semantics: a present mode-specific key overrides its base key;
  otherwise the base key applies. No new mode keys need to be shipped in the default table. Existing explicit
  `None`/empty-value behavior is preserved.

### Validation feedback
- **D-05:** Retain W362 as a warning and preserve the existing diagnostic distinction. Unknown keys such as
  `form:submitt:icon` report an unknown key and point to the buttons documentation. A known kind with an invalid
  mode, such as `form:submit:iconn`, identifies that mode and lists `both`, `icon`, and `label`.
- **D-06:** Do not add form-specific guidance, lists of kinds in warnings, or new structural-slot explanations
  to diagnostics. The documented grammar supplies that guidance.
- **D-07:** Missing icons do not make a class key invalid. The form rendering checks in Phase 6 handle that concern.

### Documentation
- **D-08:** `docs/reference/buttons.md#the-class-table` is the canonical grammar explanation. Add a compact table
  distinguishing variants, form kinds, and structural slots, valid/invalid key examples, and one form-mode
  fallback example. The user selected this over a minimal paragraph without examples.
- **D-09:** Correct the quoted default-key count and test it against `len(DEFAULT_BUTTON_CLASSES)` (KEYS-04).
  Addressable mode keys are not default-table entries; do not include their possible combinations in the count.
  Determine the actual count from the current table rather than copying the source proposal's historical number.

### Carried-forward constraints
- **D-10:** E108 and `default_label_mode()` continue to follow button-data/label-mode `LOCATIONS`, not the
  class-key variant-location set. `form` does not join those locations until Phase 6. Preserve the Phase 1
  invariant tying `LABEL_MODE_DEFAULTS` to button-data locations.
- **D-11:** Keep rendered output and goldens unchanged. Follow the project CHANGELOG rule for public-surface
  changes; any Breaking entry also requires a migration-guide update.

### Agent's Discretion
- No product decision was explicitly delegated. Exact helper placement, test organization, and documentation
  wording are implementation details within the locked grammar, diagnostics, and phase boundary.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and prior decisions
- `.planning/ROADMAP.md` — Phase 2 success criteria and Phase 6 boundary.
- `.planning/REQUIREMENTS.md` — KEYS-01 through KEYS-04; FORM requirements remain Phase 6.
- `.planning/PROJECT.md` — public-name stability, compatibility, quality gates, and documentation constraints.
- `.planning/phases/01-label-mode-defaults/01-CONTEXT.md` — D-02: E108 follows button-data locations;
  adding form is reserved for Phase 6.
- `superpowers/plans/2026-10-24-concept-review-followups.md` — Phase 1C and global constraints;
  Option A is now decided by this discussion.
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — class-table grammar finding
  and original comparison of kinds versus variants.

### Documentation contract
- `docs/reference/buttons.md` — class table, mode fallback, and quoted default-key count.
- `CHANGELOG.md` — public-surface change record.
- `docs/migrating-1.0.md` — companion update if any change is classified as Breaking.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crud_views/lib/button_classes.py`: `DEFAULT_BUTTON_CLASSES` already contains all five base form keys;
  `get_button_class()` already resolves mode-specific keys by presence, with base-key fallback.
- `src/crud_views/lib/button_classes.py`: `_action_key_parts()`, `_is_action_mode_key()`, and
  `button_class_check_messages()` provide the W362 shape/mode distinction to extend.
- `tests/test1/test_button_classes_checks.py`: existing tests cover theme and settings registrations,
  malformed keys, invalid modes, value checks, and non-string keys. `form:submit:icon` currently appears
  in the rejection list and must become accepted.
- `tests/test1/test_button_classes.py`: default-table completeness and resolution tests provide the home
  or pattern for the documentation count guard.

### Established Patterns
- Class tables merge defaults, theme registrations, and settings; mode overrides use key presence rather
  than truthiness. Explicit `None` or an empty string does not fall through to the base value.
- Imports of view constants in `button_classes.py` are deferred to keep the module importable with bare
  settings. Preserve that import-time constraint when separating validation sets.
- `src/crud_views/lib/view/variant.py` and `src/crud_views/lib/view/label_mode.py` define existing variant
  and label-mode vocabularies; avoid duplicating them.

### Integration Points
- `_action_key_parts()` currently imports `LOCATIONS` from `src/crud_views/lib/view/button_data.py`.
  It must stop treating all button-data locations as variant locations before Phase 6 adds `form`.
- `src/crud_views/lib/view/button_data.py`: `LOCATIONS` currently contains context, list, and card;
  label-mode defaults and E108 rely on this separate meaning.
- `docs/reference/buttons.md` currently repeats the historical count of 64; validate the live table and
  remove inconsistent count claims without expanding the phase into generated documentation tooling.

</code_context>

<specifics>
## Specific Ideas

- Valid examples: `form:submit:icon`, `form:cancel:both`, `form:filter-reset:label`.
- Invalid examples: `form:submitt:icon`, `form:container:icon`, `form:submit:iconn`.
- Fallback example: `form:submit:icon` overrides `form:submit` when present; otherwise the base key applies.
- Keeping kinds allows submit and filter-submit to be styled independently without introducing a variant knob.

</specifics>

<deferred>
## Deferred Ideas

None added. Form-button rendering and missing-icon checks remain in the already-planned Phase 6.
Variants everywhere and enhanced form-specific warnings were rejected, not deferred.

</deferred>

---

*Phase: 02-form-key-grammar*
*Context gathered: 2026-10-26*
