# Deferred items

- 2026-11-09, plan 06.20-02: full-suite run on Django 6.1.2 emits four `RemovedInDjango2028Warning` instances from `test_delete_collection_loader_error_propagates_unchanged` at `src/crud_views/lib/deletion.py:349`; the test's `Book.from_db()` override needs the future `fetch_mode` keyword. Existing deletion tests and production path are unchanged by this phase. Owner: deletion-test maintenance; outside the label plan. Full suite passes (12066 tests).
