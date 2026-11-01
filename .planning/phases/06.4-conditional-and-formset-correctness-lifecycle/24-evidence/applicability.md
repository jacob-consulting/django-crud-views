# Plan 06.4-24: evidence applicability

This packet refreshes only checker evidence after the plan23 WR-05 repair. The original refresh process survived the intentional conversation interruption; the continuation observed the same PID2451426 and its full-discovery unittest child2451524. It did not restart, overwrite, or edit that live capture. Final observations below are recovered from the actual persisted execution records.

## Source continuity and immutable inputs

Before capture, the original executor measured824 paths,822 unchanged digests and exactly two changed checker inputs. The continuation independently recomputed the same complete path-set comparison while capture ran: zero additions, zero deletions,824 paths in each map,822 equal digests. The fixed exemption remains only the two checker files; unsupported source, path-set or effective runtime changes require affected gates to be rerun through the existing supported capture path. New planning/evidence documents are outside source().

| Source binding | SHA-256 |
|---|---|
| Original logical map | `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` |
| Final current logical map | `5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d` |
| Original run.py | `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` |
| Current run.py | `75f8057f55d869ccb9591a0a9868e57d606f9e65f2f0eebffa5fca8d5313ad66` |
| Original test_runner.py | `2ed3c3f11dc25f054ef7b8c153db126b2bb7a3ce058ffd877bb12d9149fff345` |
| Current test_runner.py | `a37d5e636ad612d9e4b3a330392bd61e31ca6290c04ba6f3fa0692a09903e7bf` |

The changed paths are `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py` and its sibling `test_runner.py`. Both complete maps remain in their respective source-manifest.json files, rather than being inferred from HEAD.

| Immutable input | SHA-256 |
|---|---|
|18-evidence/results.json|`a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674`|
|18-evidence/source-manifest.json|`160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf`|
|Stock tablet.png|`55c2ee11a8e16140abb64a9fe37f55feb07428322e5fa6a4ed9e76f33be16282`|
|Stock mobile.png|`314006515ef104b3a93a7b390aec27addf67733df5b37fc53752e447b731edfe`|
|Stock desktop.png|`6af0369c076c37eb02a9e132e6da01fd1b04a52bc1ec428f7e2fc59f8f2b81ef`|

The PNG paths are `.planning/ui-reviews/06.4-gap-repair/{tablet,mobile,desktop}.png`. All five hashes matched before capture and during continuation. Original18, prior21/22 evidence and existing browser captures remain historical and byte-identical. No browser recapture or native screenshot was added.

## Runtime and preservation bounds

The actual refresh packet's effective selections are JSON-identical to origin18 for every gate, including commands, runtime hashes, import paths and environment. A read-only continuation probe used the resumed harness's different Codex tmp/arg0 PATH segment; it was not used to launch or relabel the capture. The surviving capture keeps its original matching environment. Fast validation consumes the recorded selections.

Bounds remain Python3.12.3, Django4.2.30/5.2.18/6.0.9 and cached Chromium149.0.7827.55. No install, broader Python/browser/device coverage, storage-backend guarantee or physical-device/assistive-technology approval follows. Historical48,220 Python passes, ordinary JS347/integration2 and browser36cases/305assertions retain their original timestamps and provenance. Any JS/docs executions nested in fresh checker tests are checker test activity, separately attributed by the fresh self-test record.

Preserve exactly the original four CSP skip events (`tests/test1/test_assets.py::test_django6_builtin_csp_nonce_roundtrip`, reason `built-in CSP middleware requires Django 6.0`) and four crispy-floor golden deselections (`tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`). No exclusions changed.

All D-01–D-19 boundaries remain: exact owning-form/name binding and local ambiguity; native visibility; independent and ancestor disabled ownership; cancellable native reset/focus; retained unsaved values; field-aware native clearing and trusted server-disabled precedence; application/model validation; edit-only/identity no-save rejection; repeat-safe root/page/modal/row initialization; preserved fragment coordinates, responses/events and template projection; A19-only int/UUID authorization/ancestry; authorized querysets, routed atomic rollback, inactive skip and explicit managed-queryset purge. Form leaves, label modes, escaping, Cancel links, accepted modal focus, paired migration guidance and Phase7 inventory remain source-bound. A8 commit=False, A25, #210/jQuery removal, broader Guardian#286/custom-PK/backend/field/theme work and image-byte decoding/dimensions remain outside this proof. ImageField evidence is reference-only; native False-clear/None-no-change does not authorize storage deletion.

## Acceptance boundary

All19 decisions and31 original fallback flags remain explicit and unresolved where previously flagged. H1 is pending actual corrected stock/native discoverability, readability, keyboard/focus and assistive-technology judgment. H2 remains pending, descriptor-less and **flagged-unverified**: **Switching a conditional file field off must not silently authorize deletion of the stored file content.** No human actor/time/response is inferred. T35/T36/T40 and current independent review obligations remain open until their actual owners reassess them. Passing artifact validation is not human approval, independent review or phase acceptance. Plans25/26 own review/canonical binding; no phase completion, ready=true, Phase7 advancement, merge or release is claimed.

## Observed final capture and validation

Actual refresh window: `2026-11-01T20:37:33.046885+00:00` through `2026-11-01T20:48:09.535801+00:00`. The three fresh gates completed with exit0 and their original process stdout/stderr persisted in results.json. All67 discovered self-tests passed; all35 exact corruption subprocesses returned1 with their declared rejection diagnostic; the ordinary complete positive returned0. The recovered terminal result was independently checked with the prescribed fast aggregate check and17-gate provenance assertion. No failed refresh attempt occurred.

| Final binding | SHA-256 |
|---|---|
|results.json| `0584675c935c5d7a81043a3c412a9bb43df5072532db49682aa5604e575effbd` |
|source-manifest.json file| `7dc2541183e999d8709d4c173a9db50f21a0bab52312e22767db896b80a0bf9b` |

### Original and fresh execution attribution

Every retained row below is JSON-identical to origin18, including its command, environment, timestamps, return code, outputs and provenance. Only the three fresh rows describe checker executions in this refresh.

| Gate | Origin | Exit | Execution start | Execution finish | Duration seconds |
|---|---|---|---|---|---|
|conditional-browser|retained unchanged|0|2026-11-01T16:58:16.474983+00:00|2026-11-01T16:59:09.258227+00:00|52.783|
|django4.2-disabled-full|retained unchanged|0|2026-11-01T16:32:17.204167+00:00|2026-11-01T16:40:47.822487+00:00|510.618|
|django4.2-enabled-full|retained unchanged|0|2026-11-01T16:20:07.409092+00:00|2026-11-01T16:28:20.047930+00:00|492.639|
|django4.2-focused|retained unchanged|0|2026-11-01T16:16:32.341088+00:00|2026-11-01T16:17:24.733433+00:00|52.392|
|django4.2-missing-runtime|retained unchanged|1|2026-11-01T16:20:03.640028+00:00|2026-11-01T16:20:04.914028+00:00|1.274|
|django5.2-disabled-full|retained unchanged|0|2026-11-01T16:40:48.027625+00:00|2026-11-01T16:53:07.473104+00:00|739.446|
|django5.2-enabled-full|retained unchanged|0|2026-11-01T16:20:07.409309+00:00|2026-11-01T16:32:17.024508+00:00|729.615|
|django5.2-focused|retained unchanged|0|2026-11-01T16:17:24.935804+00:00|2026-11-01T16:18:40.347201+00:00|75.411|
|django5.2-missing-runtime|retained unchanged|1|2026-11-01T16:20:04.996552+00:00|2026-11-01T16:20:06.123693+00:00|1.127|
|django6.0-disabled-full|retained unchanged|0|2026-11-01T16:42:44.249498+00:00|2026-11-01T16:56:56.488711+00:00|852.239|
|django6.0-enabled-full|retained unchanged|0|2026-11-01T16:28:20.265677+00:00|2026-11-01T16:42:44.065553+00:00|863.8|
|django6.0-focused|retained unchanged|0|2026-11-01T16:18:40.580690+00:00|2026-11-01T16:20:03.379680+00:00|82.799|
|django6.0-missing-runtime|retained unchanged|1|2026-11-01T16:20:06.185867+00:00|2026-11-01T16:20:07.335313+00:00|1.149|
|evidence-self-tests|fresh|0|2026-11-01T20:37:34.134784+00:00|2026-11-01T20:48:05.433651+00:00|631.299|
|javascript|retained unchanged|0|2026-11-01T16:56:57.813369+00:00|2026-11-01T16:57:10.126486+00:00|12.313|
|javascript-integration|retained unchanged|0|2026-11-01T16:57:13.795043+00:00|2026-11-01T16:57:24.345026+00:00|10.55|
|modal-browser|retained unchanged|0|2026-11-01T16:59:11.080322+00:00|2026-11-01T16:59:34.610238+00:00|23.53|
|ruff-check|fresh|0|2026-11-01T20:48:07.146657+00:00|2026-11-01T20:48:07.223173+00:00|0.077|
|ruff-format|fresh|0|2026-11-01T20:48:08.363139+00:00|2026-11-01T20:48:08.412053+00:00|0.049|
|strict-docs|retained unchanged|0|2026-11-01T16:57:26.707806+00:00|2026-11-01T16:57:28.092025+00:00|1.384|

### Actual fresh self-test identities

- `test_runner.CheckerControlEvidence.test_command_identity_normalizes_only_transport_directory`
- `test_runner.CheckerControlEvidence.test_complete_packet_cli_and_pending_handoff_positive`
- `test_runner.CheckerControlEvidence.test_contradictory_success_outcomes_reject_everywhere`
- `test_runner.CheckerControlEvidence.test_duplicate_keys_reject_at_both_cli_entry_points`
- `test_runner.CheckerControlEvidence.test_exact_summary_and_detail_inventory`
- `test_runner.CheckerControlEvidence.test_internal_payload_result_cannot_supply_final_acceptance`
- `test_runner.CheckerControlEvidence.test_malformed_outcomes_are_not_rejections`
- `test_runner.CheckerControlEvidence.test_missing_detailed_inventory_rejects_cli_aggregate_and_handoff`
- `test_runner.CheckerControlEvidence.test_real_staged_controls_and_final_positive`
- `test_runner.ConditionalCaptureEvidence.test_changed_deleted_or_non_png_owned_bytes_reject_without_touching_originals`
- `test_runner.ConditionalCaptureEvidence.test_current_three_stock_and_explicit_empty_native_are_valid`
- `test_runner.ConditionalCaptureEvidence.test_device_viewport_and_containment_observations`
- `test_runner.ConditionalCaptureEvidence.test_dimension_numeric_contract`
- `test_runner.ConditionalCaptureEvidence.test_exact_stock_and_native_inventories`
- `test_runner.ConditionalCaptureEvidence.test_historical_human_markers_stay_pending`
- `test_runner.ConditionalCaptureEvidence.test_missing_capture_inventory_rejects_aggregate_cli_and_handoff`
- `test_runner.ConditionalCaptureEvidence.test_missing_or_false_rendered_icon_observations`
- `test_runner.ConditionalCaptureEvidence.test_overflow_controls_use_capture_diagnostic`
- `test_runner.ConditionalCaptureEvidence.test_oversized_glyph_height_rejects_cli_and_handoff`
- `test_runner.ConditionalCaptureEvidence.test_oversized_glyph_width_rejects_cli_and_handoff`
- `test_runner.ConditionalCaptureEvidence.test_paths_are_bounded_and_distinct`
- `test_runner.ConditionalCaptureEvidence.test_stale_digest_rejects_despite_historical_canonical_success`
- `test_runner.CurrentCapture.test_all_invalid_selections_fail_before_any_process`
- `test_runner.CurrentCapture.test_changed_valid_browser_selection_reruns_affected_gate`
- `test_runner.CurrentCapture.test_effective_selections_affect_only_relevant_gates`
- `test_runner.CurrentCapture.test_matching_selection_reuses_real_docs_and_historical_check_ignores_current_overrides`
- `test_runner.CurrentCapture.test_wr02_invalid_python_fails_before_unrelated_command`
- `test_runner.CurrentCapture.test_wr02_invalid_runtime_subprocess_preserves_output`
- `test_runner.EvidenceRefresh.test_changed_effective_selection_rejects_before_output_writes`
- `test_runner.EvidenceRefresh.test_changed_product_input_and_command_reject_real_refresh_cli`
- `test_runner.EvidenceRefresh.test_invalid_runtime_preflight_preserves_outputs`
- `test_runner.EvidenceRefresh.test_missing_fresh_gates_controls_and_forged_timestamps_reject_everywhere`
- `test_runner.EvidenceRefresh.test_mutated_origin_and_missing_manifest_reject_everywhere`
- `test_runner.EvidenceRefresh.test_original_gate_survives_real_refresh_cli_check_and_handoff`
- `test_runner.EvidenceRefresh.test_source_continuity_rejects_product_runtime_and_path_set_changes`
- `test_runner.HandoffEvidence.test_false_readiness_rejects`
- `test_runner.HandoffEvidence.test_malformed_packet_subprocess_rejects`
- `test_runner.HandoffEvidence.test_missing_case_reference_rejects`
- `test_runner.HandoffEvidence.test_missing_findings_and_links_reject`
- `test_runner.HandoffEvidence.test_missing_human_state_or_prohibition_rejects`
- `test_runner.HandoffEvidence.test_pending_packet_is_structurally_valid_but_not_ready`
- `test_runner.HandoffEvidence.test_stale_report_hash_rejects`
- `test_runner.HandoffEvidence.test_stale_source_provenance_rejects`
- `test_runner.HandoffEvidence.test_unattributed_human_approval_rejects`
- `test_runner.HandoffEvidence.test_unreviewed_finding_cannot_close`
- `test_runner.HandoffEvidence.test_wr05_is_required_for_g6`
- `test_runner.HistoricalCounterexamples.test_focused_accepts_strengthened_reclean_identity_family`
- `test_runner.HistoricalCounterexamples.test_wr01_rejects_filtered_javascript_with_consistent_green_counts`
- `test_runner.HistoricalCounterexamples.test_wr01_rejects_non_strict_docs`
- `test_runner.QualityEvidence.test_duplicate_case`
- `test_runner.QualityEvidence.test_duplicate_file`
- `test_runner.QualityEvidence.test_failed_case`
- `test_runner.QualityEvidence.test_false_console`
- `test_runner.QualityEvidence.test_false_counts`
- `test_runner.QualityEvidence.test_filtered_collection_command`
- `test_runner.QualityEvidence.test_filtered_command`
- `test_runner.QualityEvidence.test_missing_case`
- `test_runner.QualityEvidence.test_missing_file`
- `test_runner.QualityEvidence.test_real_complete_ordinary_capture`
- `test_runner.QualityEvidence.test_required_bridge_is_independent`
- `test_runner.QualityEvidence.test_required_integration_case_missing`
- `test_runner.QualityEvidence.test_scoped_copy_checks_but_cannot_claim_complete`
- `test_runner.QualityEvidence.test_skipped_case`
- `test_runner.QualityEvidence.test_stale_collection_source`
- `test_runner.QualityEvidence.test_wrong_lint_subcommands_and_flags`
- `test_runner.QualityEvidence.test_wrong_node_executable`
- `test_runner.QualityEvidence.test_wrong_vitest_subcommand`

Self-test stdout/stderr ended with:

```text
----------------------------------------------------------------------
Ran 67 tests in 631.064s

OK
```

### Actual35 negative subprocess outcomes

Each command and exact stdout/stderr is retained in checker_control_evidence; stdout is empty for every rejection. These are fresh processes using temporary mutated copies, not synthesized fixture gates. The temporary mutation directories have been cleaned by the capture.

| Control identity | Exit | Exact stderr, trailing newline omitted |
|---|---|---|
| `capture-digest` | 1 | `MATRIX_REJECTED: Conditional capture digest mismatch: desktop` |
| `capture-height-overflow` | 1 | `MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` |
| `capture-missing` | 1 | `MATRIX_REJECTED: Conditional capture inventory invalid: stock` |
| `capture-observation` | 1 | `MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` |
| `capture-width-overflow` | 1 | `MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` |
| `control-missing-evidence` | 1 | `MATRIX_REJECTED: Checker control evidence inventory incomplete` |
| `control-missing-summary` | 1 | `MATRIX_REJECTED: Checker control summary inventory incomplete` |
| `control-success-outcome` | 1 | `MATRIX_REJECTED: Checker control exit invalid: exit-code` |
| `control-wrong-command` | 1 | `MATRIX_REJECTED: Checker control command invalid: exit-code` |
| `control-wrong-diagnostic` | 1 | `MATRIX_REJECTED: Checker control diagnostic mismatch: exit-code` |
| `disabled-node-absence` | 1 | `MATRIX_REJECTED: django4.2-disabled-full: forged Node-free environment` |
| `disabled-opt-in` | 1 | `MATRIX_REJECTED: django4.2-disabled-full: forged Node-free environment` |
| `docs-non-strict` | 1 | `MATRIX_REJECTED: strict-docs: wrong quality command` |
| `exit-code` | 1 | `MATRIX_REJECTED: django4.2-focused: green suite failed/empty` |
| `inline-clear-assertion` | 1 | `MATRIX_REJECTED: Missing/false assertion inline-file-clear-unchanged` |
| `integration-missing` | 1 | `MATRIX_REJECTED: Missing/extra matrix gates` |
| `js-duplicate-case` | 1 | `MATRIX_REJECTED: JS missing/duplicate case selection` |
| `js-duplicate-file` | 1 | `MATRIX_REJECTED: JS missing/duplicate file` |
| `js-failed-case` | 1 | `MATRIX_REJECTED: JS failed/skipped required case` |
| `js-false-counts` | 1 | `MATRIX_REJECTED: JS inconsistent counts` |
| `js-filtered-command` | 1 | `MATRIX_REJECTED: javascript: wrong quality command` |
| `js-missing-case` | 1 | `MATRIX_REJECTED: JS missing/duplicate case selection` |
| `js-missing-file` | 1 | `MATRIX_REJECTED: JS missing/duplicate file` |
| `js-skipped-case` | 1 | `MATRIX_REJECTED: JS failed/skipped required case` |
| `js-wrong-executable` | 1 | `MATRIX_REJECTED: javascript: wrong quality command` |
| `negative-control-setup-error` | 1 | `MATRIX_REJECTED: django4.2-missing-runtime: setup/collection failure is not runtime proof` |
| `raw-balance-assertion` | 1 | `MATRIX_REJECTED: Missing/false assertion fragment-raw-balance` |
| `required-case-list` | 1 | `MATRIX_REJECTED: Corrupted required-case list` |
| `ruff-format-missing-check` | 1 | `MATRIX_REJECTED: ruff-format: wrong quality command` |
| `ruff-wrong-subcommand` | 1 | `MATRIX_REJECTED: ruff-check: wrong quality command` |
| `source-hash` | 1 | `MATRIX_REJECTED: Missing/stale source manifest` |
| `tracer-absent` | 1 | `MATRIX_REJECTED: django4.2-focused: required tracer missing/skipped/failed` |
| `tracer-failed` | 1 | `MATRIX_REJECTED: django4.2-focused: green suite failed/empty` |
| `tracer-skipped` | 1 | `MATRIX_REJECTED: django4.2-focused: unexpected skip/reason` |
| `tracer-zero-selected` | 1 | `MATRIX_REJECTED: django4.2-focused: inconsistent/empty counts` |

### Actual clean final positive

```json
{
  "command": [
    "/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python",
    "/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",
    "--check",
    "--output",
    "/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/24-evidence/results.json"
  ],
  "returncode": 0,
  "stderr": "",
  "stdout": "PHASE64_MATRIX_OK 20 gates source=5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d\n"
}
```

The separately run prescribed check returned `PHASE64_MATRIX_OK 20 gates source=5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d`; exact retained comparison returned `RETAINED_GATE_PROVENANCE_OK 17`. The same aggregate verification was repeated at the tracer feedback gate before task24-02. All immutable five input digests were rechecked after capture.
