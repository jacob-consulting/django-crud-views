# Phase 06.7 deferred observations

No failing product or test gate is waived here. These existing tooling/example observations are outside Cancel implementation scope:

- `npm test` passes, while Vite warns that `vitest.config.js` uses ESM syntax in a CommonJS-loaded file under its future native-loader default. Four jsdom navigation notices are also retained in the raw JavaScript output. Real Cancel navigation is separately exercised in Chromium.
- The complete Bootstrap example suite passes with ten warnings: four Django URLField default-scheme deprecation warnings and six unordered Campaign pagination warnings. No example setting/query ordering was changed to suppress them.
- `test_assets.py::test_django6_builtin_csp_nonce_roundtrip` is intentionally version-gated below Django 6.0; it remains recorded in WINDOWS entry 3. The sole approved crispy-floor golden exclusion remains WINDOWS entry 22.
- Human keyboard/focus/visual Cancel acceptance and UI consideration confirmation remain pending in WINDOWS entry 30; automated browser results are not human approval.

The request-less custom Cancel regression and unsupported filter-fixture assumptions discovered by the full matrices were repaired under explicit ownership authorization. They are resolved deviations (WINDOWS 29 and 31), not deferred failures.
