# Deferred items: Phase 01 label-mode defaults

## Out-of-scope discoveries

- **01-04, plan-level `ruff format --check` gate:** the repo-wide check reports 6 files that would be reformatted. All
  six are pre-existing planning markdown files whose Python code fences ruff now formats:
  `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`,
  `.planning/phases/01-label-mode-defaults/01-PATTERNS.md`, `.planning/phases/01-label-mode-defaults/01-RESEARCH.md`,
  `.planning/research/ARCHITECTURE.md`, `.planning/research/STACK.md`. Phase 1 did not modify any of them. With
  `--exclude .planning` the check passes (521 files already formatted). Fix: exclude `.planning` in the ruff config
  or reformat those files in a separate housekeeping change.
