## Deferred Items

- Existing Vite config-loader warning in JavaScript test runs.
  status: open
  **Found during:** Plan 06.41-04 validation.
  **What:** Vitest 5.0.5 warns that `vitest.config.js` uses ESM syntax while loaded as CommonJS, which the planned future native loader does not support. Current focused and full JavaScript suites pass. The config predates this plan; changing module configuration is outside the bulk toolbar scope.
