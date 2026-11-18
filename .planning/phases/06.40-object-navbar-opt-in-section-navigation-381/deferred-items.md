## Deferred Items

- Plan 05's new `navbar_demo` feature awaits its documentation reference and reciprocal links in plan 06.
  status: open
  **Owner:** 06.40-06, explicitly scheduled by 06.40-05 Task 03.
  **Evidence:** The extra broad example run passed 591 tests and 250 subtests, but `test_doc_links.py::test_every_feature_declares_doc_refs` failed because `navbar_demo.docs` is empty. The prescribed plan-05 command intentionally excludes `DocRefsPanelTest`; it passes 114 tests and 53 subtests. Run the full shared/documentation-link suites after plan 06 adds the actual reference, then close this entry.
  **Ledger:** `windows append` was attempted and rejected the existing WINDOWS rendered-table/fenced-JSON mismatch; no unrelated ledger repair was made.
