## Deferred Items

- Installed Ruff is 0.16.10 while pyproject.toml requires >=0.17,<0.18.
  status: open
  **Impact:** Available lint and product formatting pass, but do not establish a manifest-aligned gate.
  **Scope:** Existing environment; no package installation or manifest change authorized by this plan.

- Repository-wide `ruff format --check` reports seven pre-existing planning Markdown files.
  status: open
  **Files:** `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`,
  `.planning/phases/01-label-mode-defaults/01-PATTERNS.md`,
  `.planning/phases/01-label-mode-defaults/01-RESEARCH.md`,
  `.planning/phases/02-form-key-grammar/02-RESEARCH.md`, `.planning/research/ARCHITECTURE.md`,
  `.planning/research/STACK.md`.
  **Impact:** Product files pass `ruff format --check src tests`; these unrelated snippets were preserved.
