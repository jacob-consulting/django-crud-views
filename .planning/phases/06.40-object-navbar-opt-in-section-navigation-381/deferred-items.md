## Deferred Items

- Product split-placement recipe uses a generic content block instead of the package's CRUD content block.
  status: open
  **Owner:** 06.40-08 final acceptance; discovered by plan07 companion reference review.
  **Location:** `docs/reference/navbar.md:196`, `<main>{% block content %}{% endblock %}</main>`.
  **Required fix:** Change to `block cv_content` and extend `tests/test1/test_navbar_docs.py` with a child template that overrides cv_content through the documented split base. Verify its body renders; existing isolated snippet tests do not exercise inheritance.
  **Evidence:** The companion recipe was corrected within its four-file scope. Its inherited child template produces `\n<main>Page body</main>\n`; all four real-context recipes and exact field inventory pass. Product docs/tests were left unchanged by plan07.
  **Ledger:** WINDOWS append rejected the pre-existing table/JSON mismatch; receipt and summary also retain this handoff.

- Plan 05's new `navbar_demo` feature awaits its documentation reference and reciprocal links in plan 06.
  status: resolved
  **Owner:** 06.40-06, explicitly scheduled by 06.40-05 Task 03.
  **Evidence:** The extra broad example run passed 591 tests and 250 subtests, but `test_doc_links.py::test_every_feature_declares_doc_refs` failed because `navbar_demo.docs` is empty. The prescribed plan-05 command intentionally excludes `DocRefsPanelTest`; it passes 114 tests and 53 subtests. Run the full shared/documentation-link suites after plan 06 adds the actual reference, then close this entry.
  **Ledger:** `windows append` was attempted and rejected the existing WINDOWS rendered-table/fenced-JSON mismatch; no unrelated ledger repair was made.
  **Closure (06.40-06, 2026-11-18):** Added the real `reference/navbar.md` DocRefs, including the `placement-and-overrides` anchor, with the exact reciprocal `/object-navbar/` live URL. The supported Django 5.2 Nox command with `-n 4 -q navbar_demo/tests.py project/tests.py test_i18n.py test_doc_links.py` passes 233 tests and 75 subtests without exclusions. The complete example suite with `-n 4 -q` passes 602 tests and 272 subtests. Strict MkDocs and built-site anchor checks pass. Existing shared and documentation-link assertions are unchanged.
