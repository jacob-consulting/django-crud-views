## Deferred Items

- Existing Vite config-loader warning in JavaScript test runs.
  status: open
  **Found during:** Plan 06.41-04 validation.
  **What:** Vitest 5.0.5 warns that `vitest.config.js` uses ESM syntax while loaded as CommonJS, which the planned future native loader does not support. Current focused and full JavaScript suites pass. The config predates this plan; changing module configuration is outside the bulk toolbar scope.

- Existing broken-windows ledger rejects append operations.
  status: open
  **Found during:** Plan 06.41-07 validation.
  **What:** `gsd-tools windows append --kind unrun-verify` rejected `.planning/WINDOWS.md` because its rendered table header or separator disagrees with its fenced JSON source. No ledger data was changed. Plan 07's browser checks (JavaScript-off visibility, Enter on selection checkboxes, and card checkbox paint/click behavior) remain recorded in its SUMMARY for end-of-phase review.
