## Deferred Items

- `isolated_routes` registry snapshot can drop the shared app ViewSets (found during 06.18-05)
  status: open
  **What:** `tests/test1/test_ancestor_authorization.py::isolated_routes` snapshots `_REGISTRY` before it builds the temporary URLconf, which includes `tests.test1.project.urls`. If that URLconf (and with it `tests.test1.app.views`) is imported for the first time inside the isolated block, the restore drops the shared ViewSets (`publisher`, `book`, ...) while the modules stay cached in `sys.modules`, so later tests in the same worker fail with `ViewSetNotFoundError: publisher`.
  **Reproduce:** `pytest tests/test1/test_ancestor_helpers.py tests/test1/test_nested_viewset.py -p no:randomly` (serial) at `d398706b`: 16 failed. Under xdist/random order it is usually masked.
  **Scope:** pre-existing shared test helper outside 06.18-05's file list; 06.18-05's new modules import the project URLconf before the snapshot (`test_ancestor_resolution._register_project_viewsets`). Proper fix: do the same inside `isolated_routes` (import the project URLconf before taking the snapshot).
