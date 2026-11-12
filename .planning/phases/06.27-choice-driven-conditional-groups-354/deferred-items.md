## Deferred Items

- Existing JavaScript runtime differs from package.json: installed Vitest 5.0.3 and jsdom 30.1.2 versus declared ^5.0.5 and ^30.1.3. Plan 01's 55 toggle tests passed on the installed runtime; no dependencies changed. Reconcile or explicitly retain this limitation during Plan 05's environment verification.
  status: open
- Existing Vite advisory reports ESM syntax in CommonJS vitest.config.js with the future native config loader. Current 55 toggle tests pass; configuration changes are outside Plan 01.
  status: open
