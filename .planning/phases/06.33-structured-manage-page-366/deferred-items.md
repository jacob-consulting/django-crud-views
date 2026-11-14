## Deferred Items

- Seven declared compatible Python/Django combinations lack prepared test environments.
  status: open
  **Scope:** Python 3.13 × Django 4.2/5.2/6.0; Python 3.14/3.15 × Django 5.2/6.0.
  **Evidence:** Interpreters 3.13.15, 3.14.7 and 3.15.0rc2 exist, but Django, pytest, xdist, Pydantic and Guardian are absent. The package-build 3.13 environment also lacks test dependencies. Plan 10 prohibits installs. The active CI workflow only runs for main pushes/main pull requests; this source branch is unpublished and has no workflow_dispatch entry point. These combinations remain unverified, never passing. Python 3.14/3.15 × Django 4.2 are explicitly excluded by nox rather than missing verification.
  **Next:** Run the declared nox CI matrix when publication is authorized or prepared environments become available.

- Existing Vitest/Vite configuration and jsdom navigation notices remain outside the manage change.
  status: open
  **Evidence:** The 457-test unit and 2-test integration suites pass. Vite warns about ESM syntax in CommonJS-loaded config files; jsdom reports unsupported document navigation in existing tests. Plan 07 already recorded the config warning. No unrelated test/config change was made.

- Django 4.2 emits 59 existing default-form-template deprecation warnings.
  status: open
  **Evidence:** The final complete 35-module replay passes 1,633 tests; warnings originate from Django's transitional default.html form rendering in native request fixtures. No production template or supported dependency floor changed.
