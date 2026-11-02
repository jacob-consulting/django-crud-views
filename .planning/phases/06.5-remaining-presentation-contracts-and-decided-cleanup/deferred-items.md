# Deferred execution issue — 06.5-09

## Required raw Django 6.0 gate versus existing dependency-floor policy

- **Status:** unresolved acceptance blocker; pre-existing dependency-specific golden mismatch.
- **Observed command:** `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -q -rs`.
- **Actual result:** 1 failed, 8328 passed, no skips, 832.01 seconds; no deselection.
- **Sole failure:** `tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`, line 268;
  wrapper byte 144 is a space instead of newline under crispy-forms 2.0 / crispy-bootstrap5 2023.10.
- **Existing policy:** `noxfile.py`'s `CRISPY_FLOOR_DESELECT` explicitly excludes this whole-wrapper golden
  and retains `test_filter_form_controls_match_golden`. Phase 06.4 full-floor evidence records that exclusion.
- **Scope:** all other tests passed, including the companion leaf-control golden and Django 6.0 CSP test.
  No production code, floor golden assertion, dependency, or exclusion was changed by this plan.
- **Remaining action:** reconcile plan 09's required raw full-suite gate with the already established floor
  policy, or supply an appropriate runtime, then perform the affected verification. No user waiver or install
  permission is inferred. Future broad runs use multicore per the updated repository instruction.

The failed raw gate is not converted into a pass by the known baseline policy. Other plan 09 gates are recorded
separately in `06.5-VALIDATION.md`; this issue does not authorize unrelated source changes.
