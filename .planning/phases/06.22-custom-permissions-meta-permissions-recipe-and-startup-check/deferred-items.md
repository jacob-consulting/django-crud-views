# Deferred items — Phase 06.22

- **Existing Django deprecation warning (observed in plan 03 full-suite gate):** Four parametrizations of
  `tests/test1/test_delete.py::test_delete_collection_loader_error_propagates_unchanged` emit
  `RemovedInDjango2028Warning: Book.from_db() must accept a fetch_mode keyword argument`, surfaced at
  `src/crud_views/lib/deletion.py:349`. Those test and source files are unchanged by this phase; updating the
  existing probe's loader signature is outside the permission declaration/docs scope. The gate passed with
  `12074 passed, 4 warnings in 473.06s` on four workers. No fix or test suppression was applied.
