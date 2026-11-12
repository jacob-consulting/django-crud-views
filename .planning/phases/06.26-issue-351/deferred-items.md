# Phase 06.26 deferred items

- Plan 03 release checks emit an existing Vite warning: `vitest.config.js` and
  `vitest.integration.config.js` use ESM syntax while loaded as CommonJS, which the future native config
  loader will not support. Both existing commands pass after selecting the integration Python interpreter.
  No JS configuration was changed in this phase; any config-module migration is outside its scope.
- Final full pytest passes with four existing `RemovedInDjango2028Warning` warnings in the deletion exception
  tests: `Book.from_db()` must eventually accept `fetch_mode`. Reported from
  `src/crud_views/lib/deletion.py:349`; unrelated to checkbox documentation and unchanged here.
