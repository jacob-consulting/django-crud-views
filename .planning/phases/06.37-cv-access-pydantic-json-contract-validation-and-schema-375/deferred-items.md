## Deferred Items

- Order-dependent failure of `tests/test1/test_manage_command_docs.py::test_published_command_examples` under xdist
  status: resolved in `fd9becd8` (code review WR-03)
  **Found during:** 06.37-03 verification (Task 1 verify and the plan-level `-n 6` selection).
  **What:** The test sees an empty `cv_manage_view` catalogue (`data.entries: []`) when it shares an xdist worker
  with some other tests. It passes when `test_manage_command_docs.py` runs alone (9 passed).
  **Pre-existing:** Reproduced at base `c56ef82d` in a scratch worktree with the identical selection
  (`test_access_trace*.py test_manage_docs.py test_manage_command_docs.py -n 6`: 1 failed, 643 passed) and
  intermittently with the Task 1 `-n 4` selection. Plan 03 changes only docs, the docs tests and CHANGELOG.
  **Likely cause (unverified):** a test that swaps the ViewSet registry (for example via `isolated_routes`) leaves
  the worker's registry state unexpected for the catalogue example.
  **Cause (confirmed in 06.37-REVIEW.md WR-03):** `isolated_routes` snapshotted `_REGISTRY` before the project's
  views were imported. They then registered inside the block (via `include("tests.test1.project.urls")`), the
  `finally` restored the empty snapshot, and the already-imported modules never registered again on that worker.
  **Resolution:** `isolated_routes` (`tests/test1/test_ancestor_authorization.py`) imports
  `tests.test1.project.urls` before taking the snapshot. The deterministic reproduction
  (`test_access_trace_contract.py::test_real_outcome_traces_validate_and_match_the_cli` then
  `test_manage_command_docs.py::test_published_command_examples`, `-p no:randomly`) went from 1 failed, 6 passed
  to 7 passed; the original `-n 6` selection passed three runs in a row (658 passed each).
