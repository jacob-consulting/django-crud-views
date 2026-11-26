# Plan 06.52-03 execution receipts

Each JSON receipt records the actual argument vector, environment, working directory, HEAD,
committed source/test tree IDs, working-input fingerprint, elapsed seconds, exit status and the
SHA256 of its adjacent unmodified console log. Pytest receipts for the final gates also record
the interpreter, imported package source, dependency versions and reported counts.

The `full-source*.json` receipts additionally contain the SHA256 of every tracked file under `src`, `tests`
and `docs`, plus `pyproject.toml`, `mkdocs.yml` and `CHANGELOG.md`. The working fingerprint is
SHA256 of the sorted JSON path/hash mapping. This captures the release-note edit that was still
uncommitted at test start. A later HEAD can reuse the result only after checking these bytes;
planning-only commits do not change the tested source. It is a source-checkout result with
`PYTHONPATH=src:.` and `CV_ACCESS_RECORD_REQUESTS=0`, not an installed-distribution or version-matrix run.

The full command is:

```text
PYTHONPATH=src:. CV_ACCESS_RECORD_REQUESTS=0 .nox/tests-3-12-django-6-0/bin/python -m pytest tests -n 6 -q
```

The strict documentation command is `.venv/bin/mkdocs build --strict`. Ruff checks the three
phase-owned Python files listed in its receipts. `preservation.py` is the exact read-only audit
used for `preservation.log`; it compares protected tests/goldens/matrix/query pins and other
production files against `1d538046`, each original private definition, the original object fence,
historical Breaking text, preserved documentation assertions and user configuration snapshots.

The unchanged matrix/cost result is reused from `../06.52-02-SUMMARY.md`: 1,665 passing cases
in 14.37 seconds. `preservation.log` binds that reuse to the unchanged relevant source.

Expected RED failures remain in the task receipts. Their full JUnit reports and semantic
assessments live in `../06.52-03-taskN-red.{xml,json}` and were accepted by the GSD
`tdd-red-evidence` classifier. `task1-green` records an initial wording/assertion correction;
`task1-green-fixed` records its successful resolution. Use the final passing receipts and
the plan summary for acceptance results, rather than interpreting historical RED logs as open defects.

The first `full-source` run found one changed documentation sentence pinned by a protected navbar
test (20,396 passed, one failed). The exact request/redirect wording was restored in `nested.md`.
`docs-regression-fixed` covers all 77 link/navbar documentation cases and `strict-docs-fixed` covers
the corrected build. `full-source-fixed` is the subsequent full regression gate on those corrected inputs.
