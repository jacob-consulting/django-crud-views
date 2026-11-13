# Deferred items

- Plan 12, existing conference example: Speaker name inputs have no individual label or placeholder (`form_show_labels=False`). The retained Speakers section legend and ARIA-linked errors passed browser checks. Preserve the current label policy per parent instruction; individual-label usability remains part of the pending H2 human judgment.

- Plan 03, existing JS harness: Vitest 5.0.5 reports that ESM syntax in `vitest.config.js` will need `.mjs` or a package module setting for a future native config loader default. No harness configuration or dependencies were changed; all 447 tests passed.
- Plan 03, existing JS navigation tests: jsdom reports `Not implemented: navigation to another Document` four times during the full suite. All 447 tests passed; this is not real-browser navigation evidence. Browser acceptance remains assigned to later phase plans.
