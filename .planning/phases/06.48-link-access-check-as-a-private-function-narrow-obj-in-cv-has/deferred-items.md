# Phase 06.48 deferred items

## Existing example pagination warnings

Plan 09's example gate at `f242c65b64fa898b0f64b9d8a23155bb329dc48c` passed 637 tests and 300 subtests,
with six Django `UnorderedObjectListWarning` instances for the workflow `Campaign` queryset. The warnings
appear in the five feature-page discovery checks and `CampaignWorkflowTest.test_list_renders_with_snippets`.
The entire `examples/` tree is unchanged from `dbf1e6c4`; fixing its queryset ordering is outside this phase.
No test failed or was skipped. Receipt: `/tmp/cv-0648-09-after/examples.log`.

## Existing WINDOWS ledger rendering mismatch

The optional attempt to append plan 09's authorized verification-scope deviation declined: the rendered
header/separator of `.planning/WINDOWS.md` disagrees with its fenced JSON source. The SDK reported that
no data row differs. The ledger was left untouched; repairing a pre-existing cross-phase report is outside
this plan. Plan 09 records its exception and cache-reproduction evidence in its cost report and summary.
