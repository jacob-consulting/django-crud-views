# Plan 06.34-08 verification

Executed on 2026-11-15 with current checkout source on Python 3.12.3 / cached Django 5.2.19.
Initial package-origin check:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -c 'import pathlib, crud_views; assert pathlib.Path(crud_views.__file__).resolve().is_relative_to(pathlib.Path("src").resolve())'
```

No dependencies installed or runtimes upgraded. Commands used the pinned repository root and normal git commits.

## Checks and timing

| Check | Outcome | Pytest/build time | Transcript |
|---|---|---|---|
| Task 1 documentation tests before publication | 6 expected missing-documentation failures | 1.87s | task1-red.txt |
| Task 1 initial publication | 3 passed; 3 test expectation issues (core omits Guardian help; line-wrapped prose) | 2.04s | task1-green.txt |
| Task 1 after fixture/text assertion corrections | 6 passed | 1.89s | task1-green-final.txt |
| Task 2 limits/link test before publication | 1 expected missing-section failure, 6 passed | 2.04s | task2-red.txt |
| Task 2 final | 7 passed | 2.05s | task2-green.txt |
| Task 2 strict MkDocs | Passed | 1.47s | task2-docs.txt |
| Task 3 before inventory synchronization | 20 expected documentation/count/recipe failures, 302 passed | 30.88s | task3-red.txt |
| Task 3 required six-module selection | 332 passed | 30.70s | task3-green.txt |
| Final docs/release focused selection, including all six real command outcomes | 29 passed | 3.35s | final-focused.txt |
| Final expanded recorder-enabled integration | 856 passed | 36.77s | final-integration.txt |
| Final strict MkDocs | Passed | 1.36s | final-docs.txt |

The tests precede their corresponding documentation changes. These are documentation contract failures, not
production behavior changes or formal TDD-gate/classifier claims. Existing assertions remain intact. The new
help test follows core's existing omission of Guardian-only help; the unchanged existing test still checks the
full eleven-anchor union. Word-boundary assertions normalize prose whitespace without relaxing semantic checks.

## Exact selections

Tasks 1 and 2:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_access_trace_docs.py -n 2 -q
```

Task 3 required selection:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_manage_release.py tests/test1/test_button_classes.py tests/test1/test_theme_adoption_docs.py tests/test1/test_manage_docs.py tests/test1/test_access_trace_docs.py tests/test1/test_authorization_templates.py -n 2 -q
```

Final focused additions:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_access_trace_docs.py tests/test1/test_manage_release.py -n 2 -q
```

Final integration includes every module from the required selection, after the last test/docs edits:

```text
CV_ACCESS_RECORD_REQUESTS=1 PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_manage_release.py tests/test1/test_button_classes.py tests/test1/test_theme_adoption_docs.py tests/test1/test_manage_docs.py tests/test1/test_access_trace*.py tests/test1/test_authorization_templates.py tests/test1/test_manage_access_trace.py tests/test1/test_manage_guardian.py -n 4 -q
```

Final docs and style checks:

```text
.venv/bin/python -m mkdocs build --strict --site-dir /tmp/cv-0634-docs
.venv/bin/ruff check tests/test1/test_access_trace_docs.py tests/test1/test_manage_release.py tests/test1/test_button_classes.py tests/test1/test_theme_adoption_docs.py
.venv/bin/ruff format --check tests/test1/test_access_trace_docs.py tests/test1/test_manage_release.py tests/test1/test_button_classes.py tests/test1/test_theme_adoption_docs.py
git diff --check
```

Independent AST key extraction confirms 121 core defaults, nineteen manage keys and ten trace keys. The first
attempt to literal-evaluate the whole default dictionary encountered existing gettext calls; extracting literal
keys instead succeeded. Live tests also assert 139 combined defaults and eighteen workflow defaults, including
fresh subprocess setup and installed-app transitions. Expected keys/defaults remain explicitly declared in tests.

Generated HTML at `/tmp/cv-0634-docs/reference/manage/index.html` contains all seventeen checked anchors:
system-checks, permissions, views, presentation, viewset, hierarchy, url-names, ancestor-policy, guardian,
templates-and-actions, label-modes, access-check, cv_access, diagnostic-limits, custom-method-boundaries,
list-count-boundary and version-1-document. Twelve are actual combined enabled-card help destinations.

All required checks ran; none exceeded 60 seconds. No new stub, skipped test or unrun required verification.
Full suite/supported runtime matrix, translation and visual-browser acceptance remain with plans 09–10.
No production source, shared state, requirement, approved plan or unrelated original dirty file was changed.
