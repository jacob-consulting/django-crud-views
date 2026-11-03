# Deferred execution issue — 06.5-09

## Required raw Django 6.0 gate versus existing dependency-floor policy

- **Status:** acceptance blocker resolved by explicit user-authorized floor-policy reconciliation; the original
  dependency-specific golden mismatch remains historical and is not claimed fixed.
- **Observed command:** `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -q -rs`.
- **Actual result:** 1 failed, 8328 passed, no skips, 832.01 seconds; no deselection.
- **Sole failure:** `tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`, line 268;
  wrapper byte 144 is a space instead of newline under crispy-forms 2.0 / crispy-bootstrap5 2023.10.
- **Existing policy:** `noxfile.py`'s `CRISPY_FLOOR_DESELECT` explicitly excludes this whole-wrapper golden
  and retains `test_filter_form_controls_match_golden`. Phase 06.4 full-floor evidence records that exclusion.
- **Scope:** all other tests passed, including the companion leaf-control golden and Django 6.0 CSP test.
  No production code, floor golden assertion, dependency, or exclusion was changed by this plan.
- **Resolution:** the user instructed “Apply the existing crispy-floor exclusion for the single known golden
  test, preserve the original failure evidence, and rerun with multiple cores”, then “do 1” to resume task 03.
  The plan appendix reconciles acceptance to the existing exact `CRISPY_FLOOR_DESELECT` node. The full suite
  rerun used `-q -rs -n 4 --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline` and
  `--junitxml=.planning/phases/06.5-remaining-presentation-contracts-and-decided-cleanup/09-evidence/django60-floor-multicore.xml`.
  Result: **exit 0, 8328 passed in 256.14s**, no failures/errors/skips. Separate log/JUnit evidence is in
  `09-evidence/django60-floor-multicore.{log,xml}`. Both the leaf-control golden and Django 6.0 CSP test passed.
  No other exclusion or package installation was performed. WINDOWS entry 22 records the bounded waiver.

The failed raw gate is not converted into a pass by the known baseline policy or this later authorization.
Its log remains byte-identical to `de61f3c`, SHA-256
`0fe7d3374a9c8437677b306c6c6f46f422c6b4ed5d60a0d316a4a7004de6faef`.
Other passing plan 09 gates are preserved separately in `06.5-VALIDATION.md`; no relevant sources changed
and no unrelated passing suites were replayed. Plan execution is complete; independent phase verification
and the existing visual/AT/matrix coverage limitations remain with the orchestrator.
