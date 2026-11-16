## Deferred Items

- Order-dependent failure of `tests/test1/test_manage_command_docs.py::test_published_command_examples` under xdist
  status: open
  **Found during:** 06.37-03 verification (Task 1 verify and the plan-level `-n 6` selection).
  **What:** The test sees an empty `cv_manage_view` catalogue (`data.entries: []`) when it shares an xdist worker
  with some other tests. It passes when `test_manage_command_docs.py` runs alone (9 passed).
  **Pre-existing:** Reproduced at base `c56ef82d` in a scratch worktree with the identical selection
  (`test_access_trace*.py test_manage_docs.py test_manage_command_docs.py -n 6`: 1 failed, 643 passed) and
  intermittently with the Task 1 `-n 4` selection. Plan 03 changes only docs, the docs tests and CHANGELOG.
  **Likely cause (unverified):** a test that swaps the ViewSet registry (for example via `isolated_routes`) leaves
  the worker's registry state unexpected for the catalogue example.
