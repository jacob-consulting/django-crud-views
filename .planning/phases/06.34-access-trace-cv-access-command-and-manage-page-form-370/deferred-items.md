## Deferred Items

- Existing transaction-test ordering can desynchronize default/shard ContentType identities and permission vocabulary.
  status: open
  **Found by:** Plan 06.34-04 expanded recorder-enabled verification.
  **Reproduction using only unchanged tests:** `CV_ACCESS_RECORD_REQUESTS=1 PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_transactions.py::test_on_commit_error_after_real_commit_keeps_data tests/test1/test_ancestor_auth_databases.py::test_top_level_guardian_and_manage_keep_their_routing -n 0 -q` yields 1 passed, 1 failed (1.40s). Serial execution is required here to establish order, not used for broad acceptance.
  **Failure:** The routed Guardian list cannot find `view_book`; other mixed selections can fail Guardian's comparison of same-labelled ContentTypes with different IDs. The trace runner is not invoked by this reproduction.
  **Evidence:** `evidence/06.34-04/existing-order-failure.log`, `mixed-integration-failure.log`, and `mixed-trace-routing-failure.log`.
  **Scope:** No unrelated routing/transaction tests were changed. The new plan-04 rollback fixture was corrected to clean both aliases, with its own five-test ordered RED/GREEN reproduction. Routing/costs alone pass 346 tests; transaction tests alone pass 49; final trace/order/costs/import selection passes 451.
  **Follow-up:** Diagnose shared test-database metadata initialization/flush ordering before the phase-wide full-suite gate. Split passing selections do not certify a mixed full-suite run.
