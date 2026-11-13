# Deferred items

- Plan 03, existing JS harness: Vitest 5.0.5 reports that ESM syntax in `vitest.config.js` will need `.mjs` or a package module setting for a future native config loader default. No harness configuration or dependencies were changed; all 447 tests passed.
- Plan 03, existing JS navigation tests: jsdom reports `Not implemented: navigation to another Document` four times during the full suite. All 447 tests passed; this is not real-browser navigation evidence. Browser acceptance remains assigned to later phase plans.
