# Plan 06.34-09 verification

Runtime: Python 3.12.3 / Django 5.2.19 / polib 1.2.0. Every pytest command below uses
`PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python`. Initial source assertion:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -c 'import pathlib, crud_views, django, polib; assert pathlib.Path(crud_views.__file__).resolve().is_relative_to(pathlib.Path("src").resolve()); print(django.get_version(), polib.__version__)'
```

No dependencies or runtimes changed. Both catalog files were generated using installed polib from the
explicit German translations; source PO entries were appended without rewriting existing translations.

| Transcript | Exact pytest arguments after the interpreter | Result |
|---|---|---|
| red.txt | `-m pytest tests/test1/test_manage_locales.py tests/test1/test_access_trace_locales.py -n 2 -q` | 48 expected assertion failures, 19 passes; 2.07s |
| red-focused.txt / red.xml | `-m pytest tests/test1/test_access_trace_locales.py tests/test1/test_manage_locales.py::test_extraction_multiline_template_context_plural -n 2 -q --junitxml=.planning/phases/06.34-access-trace-cv-access-command-and-manage-page-form-370/evidence/06.34-09/red.xml` | 3 expected assertion failures; 1.60s |
| task1-green.txt | `-m pytest tests/test1/test_manage_locales.py -n 2 -q` | 65 passed; 2.08s |
| task2-first.txt | `-m pytest tests/test1/test_access_trace_locales.py tests/test1/test_manage_locales.py -n 2 -q` | 132 passed; 6.14s |
| integration-enabled.txt | `-m pytest tests/test1/test_access_trace*.py tests/test1/test_manage_access_trace.py tests/test1/test_manage_locales.py tests/test1/test_manage_requirements.py tests/test1/test_manage_guardian.py -n 4 -q`, with `CV_ACCESS_RECORD_REQUESTS=1` | 754 passed; 29.78s |
| final-focused.txt | `-m pytest tests/test1/test_access_trace_locales.py tests/test1/test_manage_locales.py -n 2 -q` | 134 passed; 5.72s |

The final focused run includes two catalog-test additions made during the integration run:
keyword signature extraction and contextual plural/stale-MO validation. No production files changed during
that run. The 754-test result does not claim those extra two tests; they are in the final 134-test receipt.

`integration.txt` is an unsuccessful preliminary invocation: the selector misspelled
`test_manage_guardian.py` as `test_guardian_manage.py`, so no tests ran (exit 5, 0.94s).
It also used an incorrect recorder variable. Neither that invocation nor its nonexistent coverage is
counted as acceptance. The corrected enabled command above ran successfully.

The initial extractor implementation left one expected template assertion failing because Django emits
`,count` without a space. Accepting optional whitespace fixed the extraction; no assertion was weakened.
Initial lint findings were import order and imported pytest fixture name shadowing; fixture aliases through
the existing fixture module and normal Ruff sorting resolved them.

RED records retain the unchanged generated JUnit report. `red.json` targets the actual German notice,
and `extractor-red.json` targets exact template context/plural extraction. Both classifiers return
`RED_EVIDENCE_OK`; the actual named assertions failed, with no setup/import failures. The first record's
manually entered run timestamp was corrected to the original JUnit suite timestamp during close-out.

Final lint/format/whitespace:

```text
.venv/bin/ruff check tests/test1/test_manage_locales.py tests/test1/test_access_trace_locales.py
.venv/bin/ruff format --check tests/test1/test_manage_locales.py tests/test1/test_access_trace_locales.py
git diff --check
```

All pass. Evaluation-scope resolves the three task commits, and all four changed source/test artifacts exist.
No browser, full-suite, other-runtime or complete-phase acceptance is claimed. Those remain plan 10's gates.
