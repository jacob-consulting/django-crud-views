# Deferred execution-tooling issue

- **Found in plan 07:** The best-effort `gsd-tools windows append --kind deviation`
  call for the resolved D-50 acceptance-test gap was rejected. The existing
  `.planning/WINDOWS.md` rendered table header/separator disagrees with its fenced
  JSON (the tool explicitly reported no differing data row). The file is unchanged
  from the phase-start baseline; this is unrelated to stage-3b product behavior.
  Do not hand-edit the generated table. Repair the existing ledger's format in a
  separate bookkeeping task, then record the already-resolved test-scope deviation
  from commit `94966020`. All 88 affected module tests passed; this is not an open
  product defect or a skipped required verification.
