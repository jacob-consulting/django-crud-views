## Deferred Items

- Repository-wide `ruff format --check` reports eight pre-existing planning Markdown files.
  status: open
  **Files:** the seven listed in `.planning/phases/02-form-key-grammar/deferred-items.md`, plus
  `.planning/phases/02-form-key-grammar/02-VERIFICATION.md` (added by `6ce34b2`, Phase 2 verification).
  **Impact:** `ruff format --check src tests` passes (288 files); no Phase 3 file is reported. Found during 03-02-03;
  out of scope, not reformatted.

- Installed tooling differs from the manifests: Ruff 0.16.10 (pyproject `>=0.17,<0.18`), Vitest 4.1.10
  (`^5.0.3`), jsdom 29.1.1 (`^30.1.2`).
  status: open
  **Impact:** All gates ran on the installed versions; none establishes a manifest-aligned run. No installs or
  upgrades were authorized in this phase.
