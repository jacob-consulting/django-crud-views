# Out-of-scope environment observations

- Plan 05, 2026-11-04: cached Vitest is 5.0.3 while package.json declares ^5.0.5. JavaScript and fragment
  checks pass on the cached version; no install or dependency change was authorized by this plan, and declared
  version coverage is not claimed. Resolve runtime alignment in normal dependency maintenance.
- Plan 05, 2026-11-04: existing Vite warnings flag ESM syntax in the CommonJS-named vitest.config.js and
  vitest.integration.config.js for a future native-loader default. Existing jsdom document-navigation diagnostics
  also appear in the passing unit suite. These unrelated configuration/runtime notices were not changed;
  the real Chromium matrix independently verifies document navigation.
