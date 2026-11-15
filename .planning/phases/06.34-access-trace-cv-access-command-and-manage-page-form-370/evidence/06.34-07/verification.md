# Plan 06.34-07 verification receipt

Source checkout: `/home/alex/projects/alex/django-crud-views`.
Runtime: Python 3.12.3 / Django 5.2.19, `.nox/tests-3-12-django-5-2/bin/python`.
All pytest commands use `PYTHONPATH=src:.`. Package-origin assertion passed before tests and again at close-out:

```text
import pathlib, crud_views
assert pathlib.Path(crud_views.__file__).resolve().is_relative_to(pathlib.Path("src").resolve())
```

| Receipt | Selection | Workers | Result / pytest time |
|---|---|---|---|
| task1-red | Named default-off setting test | 2 | 1 intended assertion failure / 1.23s |
| task1-green | test_manage_access_trace.py test_manage_group.py | 2 | 34 passed / 2.20s |
| task2-red | Named selected matrix actor test | 2 | 1 intended assertion failure / 1.46s |
| task2-green | test_manage_access_trace.py test_manage_guardian.py test_authorization_templates.py | 2 | 228 passed / 28.42s |
| task2-final | test_manage_access_trace.py, including strict Guardian row spy | 2 | 76 passed / 5.06s |
| task3-red | Named allowed registry class test | 2 | 1 intended assertion failure / 1.24s |
| task3-green | test_manage_access_trace.py test_manage_cards.py test_button_classes_templates.py | 2 | 172 passed / 7.07s |
| path-red | Named malformed path feedback test | 2 | 1 intended 500 != 200 assertion / 1.50s |
| path-green | test_manage_access_trace.py | 2 | 91 passed / 5.60s |
| final-integration | Complete command below, including external recorder | 4 | 754 passed / 36.42s |

Final integration:

```text
CV_ACCESS_RECORD_REQUESTS=1 PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_access_trace*.py tests/test1/test_manage_access_trace.py tests/test1/test_manage_cards.py tests/test1/test_manage_group.py tests/test1/test_manage_guardian.py tests/test1/test_authorization_templates.py tests/test1/test_button_classes_templates.py -n 4 -q
```

Raw final reports are in the adjacent `.log` files. Each RED JSON preserves the actual unchanged JUnit document,
command, exit code, target assertion and semantic assessment; each returned `RED_EVIDENCE_OK` before GREEN.
The JUnit suite timestamp and filesystem modification time identify the report. The malformed-path probe was
rerun with Django client exception propagation disabled to assert the actual 500 response, rather than using an
uncaught runtime exception as RED evidence.

Final Ruff check and format check cover settings.py, views/manage.py, button_classes.py and the new test module.
All pass; git diff whitespace check passes. No skipped tests or selection exceeding 60 seconds. Exact inventory
and documentation synchronization is explicitly plan08-owned; compiled translations plan09; browser/full-suite
and supported-version acceptance plan10. This receipt makes no claim for those gates.
