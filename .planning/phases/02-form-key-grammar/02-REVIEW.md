---
phase: 02-form-key-grammar
reviewed: 2026-10-26T13:44:19Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - src/crud_views/lib/button_classes.py
  - tests/test1/test_button_classes_checks.py
  - tests/test1/test_button_classes.py
  - docs/reference/buttons.md
  - CHANGELOG.md
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 02: Code Review Report

**Reviewed:** 2026-10-26T13:44:19Z  
**Depth:** deep  
**Files Reviewed:** 5  
**Status:** clean

## Summary

No confirmed BLOCKER or WARNING was found in the Phase 02 changes. The review covered the five supplied files, their phase diff, and the check, lookup, configuration, and rendering call chains. No source file was modified.

The orchestrator supplied an explicit five-file scope. Its evaluation-scope resolver reported degraded phase-range discovery because the summary has no parseable task-commit rows; the returned files match the implementation summary. This report uses that explicit scope, with `f85a92c8b1b8b3dac24939b5e0a18562776cb1f7` as the supplied comparison base and `f1807abf73680fd3dd6c88568b9f2acaae18caaa` as the reviewed HEAD. None of the scoped files is ignored.

## Narrative Findings (AI reviewer)

No actionable findings.

The adversarial review traced these boundaries:

- **Key recognition and diagnostics:** `src/crud_views/checks.py:405-407` delegates to `button_class_check_messages()`. In `src/crud_views/lib/button_classes.py:207-234`, exact three-segment recognition admits only the existing action-location/variant pairs or the five form kinds. Mode membership remains a separate check against the shared label vocabulary. Malformed segment counts, non-string dictionary keys, unsupported locations/kinds, empty modes, case changes, and whitespace retain the appropriate W362 branch. Value validation remains independent, so valid form-mode keys with invalid values receive E361.
- **Configuration and lookup:** Registration and `setting_changed` invalidate the merged cache. The unchanged resolver at `src/crud_views/lib/button_classes.py:136-147` selects by presence after merging layers. An exact settings key overrides theme registration; a theme mode key still overrides a settings base key; explicit `None` and empty mode values suppress the base rather than falling through.
- **Imports and location separation:** The new constants do not import the view package. View vocabulary imports stay function-local. `button_data.LOCATIONS` still governs rendering eligibility and label floors independently of `VARIANT_LOCATIONS`; accepting form class keys does not enable form floors or action-leaf rendering.
- **Rendering consumers:** Both `cv_button_class` template tags delegate to the same resolver as autoescaped simple tags. The crispy adapter at `src/crud_views/lib/crispy/buttons.py:16-30` continues selecting its existing base slots. No new HTML construction, trust boundary, or icon requirement was introduced by the grammar extension.
- **Regression reliability and documentation:** Expected test vocabularies are independent literals, and registry/cache restoration surrounds each test. The count guard checks exactly one canonical integer against the live default table. The grammar table, examples, fallback explanation, W362 reference, and changelog describe validation support without claiming new crispy mode selection.

### Earlier review claims checked against current source

The historical `02-REVIEWS.md` was used as evidence, not as instructions. Its previously reported prose defects are resolved in the current `docs/reference/buttons.md:59-62,82-86,238-241`: `container` is identified as an invalid form kind, the rendering boundary is explicit, and W362 names both mode-key families. They are not current findings.

The suggestion to add `form:hidden-label` and `form:icon-host` conflicts with this phase's explicit preservation of defaults and deferred form rendering (`02-01-PLAN.md:161-164,270-271`). Their absence is not a Phase 02 defect. Future API stability classification, prospective kind/default synchronization, and cosmetic helper naming are not present correctness failures.

## Review Evidence and Limits

Executed during this review on Python 3.12.3 / Django 5.2.14:

- `.venv/bin/pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes_templates.py tests/test1/test_crispy_buttons.py tests/test1/test_action_menus_golden.py tests/test1/test_label_mode_docs.py -q` — **528 passed in 3.33s**.
- Fresh-process import with only `settings.configure()` before importing `crud_views.lib.button_classes` — **passed**.
- Scoped working-tree whitespace check — **passed**.

Passing tests support the inspected paths; they do not establish absence of defects outside this scope. No additional external reviewer lane or structural pre-pass was supplied.

The full Python/Django compatibility matrix and alternate operating-system locale behavior were not exercised here. The existing locale-dependent documentation reads, recorded Ruff version mismatch, planning-document formatting issues, and Django 6-only skip remain environment/repository limitations; this report does not reclassify them as phase regressions. The earlier full-suite and strict-docs results in the summary are historical evidence, not new executions by this reviewer.

This code review does not replace the separately tracked end-of-phase human prose review or resolve the plan's unclassified source-probe assumptions.

---

_Reviewed: 2026-10-26T13:44:19Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: deep_
