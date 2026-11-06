# Deferred items

- Plan 05: the existing Vitest configuration emits a Vite notice about ESM syntax in `vitest.config.js` being loaded as CommonJS with a future native config loader. The JavaScript suite passes 365 tests. This configuration predates the workflow changes and was not modified.
- Plan 05 runtime limit: the available local Vitest is 5.0.3 while `package.json` declares `^5.0.5`. Verification used the existing executable without installing dependencies; it does not prove the declared newer version.
