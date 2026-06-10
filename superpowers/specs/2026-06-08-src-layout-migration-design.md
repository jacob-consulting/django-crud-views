# Design: Migrate to `src/` layout

**Date:** 2026-06-08
**Status:** Approved (design), pending implementation plan

## Problem & framing

The five distributed packages currently live at the repository root (flat
layout). The flat layout and the `src/` layout are **both** officially
sanctioned by the PyPA — this is not a conventions violation. The `src/`
layout is a *recommendation* that solves one specific problem: it prevents
Python from importing the package from the working directory instead of the
installed version, which can mask packaging bugs (a module that works in dev
but is missing from the built wheel).

The goal is to adopt the `src/` layout to gain that safety property, with a
migration that is provably behavior-neutral.

## Scope

### Moves into a new `src/` (via `git mv`, preserving history)

```
crud_views/             -> src/crud_views/
crud_views_plain/       -> src/crud_views_plain/
crud_views_workflow/    -> src/crud_views_workflow/
crud_views_polymorphic/ -> src/crud_views_polymorphic/
crud_views_guardian/    -> src/crud_views_guardian/
```

### Stays at root

`tests/`, `examples/`, `docs/`, `scripts/`, `settings_i18n.py`.

### Unchanged

Import names (`crud_views`, `crud_views_plain`, …) do not change — only the
on-disk location. Django `INSTALLED_APPS` strings, `AppConfig.name`, and
template/static discovery all key off import strings and in-package
directories, so they travel with the move untouched.

## Config edits

1. **`pyproject.toml` → `[tool.hatch.build.targets.wheel]`**: prefix each
   package entry with `src/` (`"src/crud_views"`, etc.). Hatchling
   automatically strips the leading `src/`, so the wheel's internal layout is
   byte-identical to today's.
2. **`pyproject.toml` → `[[tool.bumpversion.files]]`**: update the two
   `__init__.py` filenames to `src/crud_views/__init__.py` and
   `src/crud_views_plain/__init__.py`.
3. **`taskfile.yaml`**: `msg-make-crud_views` and `msg-comp-crud_views`
   change `dir: crud_views` -> `dir: src/crud_views`.
4. **No change needed**: `[tool.coverage.run] source` (keys off import
   names), `noxfile.py` (installs `.[...]` then runs pytest against the
   installed package), `[tool.pytest.ini_options]`, `.pre-commit-config.yaml`
   (ruff-format, path-agnostic).

## Why this is safe here

- Tests already import the package through the **editable install**
  (`task dev` → `uv pip install -e .`), never from cwd. The "must be
  installed to import" property of `src/` layout is already satisfied by the
  existing workflow. The test `conftest.py` lists `crud_views.apps.*` in
  `INSTALLED_APPS`, resolved via the installed package; `tests.lib` /
  `tests.test1.app` resolve via pytest's rootdir (repo root, anchored by
  `pyproject.toml`), independent of where the packages live.
- nox installs the project (`session.install(".[...]")`) before running the
  suite, so CI exercises the built/installed package, not the source tree.

## Risks to verify (not silently assume)

- **i18n tasks**: `msg-make-crud_views` / `msg-comp-crud_views` run
  `--settings=settings_i18n` from inside the package directory while
  `settings_i18n.py` lives at the repo root. Moving the package from
  `crud_views/` (one level down) to `src/crud_views/` (two levels down)
  changes the relative depth to that settings file. The plan must verify
  these tasks still work and, if they break, fix by setting `PYTHONPATH=.`
  on the task (preferred — keeps `settings_i18n.py` at root) rather than
  relocating the file.
- **Stale caches / IDE config**: the root `__pycache__`, the `.codegraph`
  index, and IDE run-configs under `.run/` and `.idea/` reference the old
  paths. Rebuild the codegraph index and clear `__pycache__` after the move;
  IDE run-configs are developer-local and out of scope for the package but
  should be noted.

## Acceptance criteria

The migration must be provably behavior-neutral:

1. **Before** the move: `uv build`, then record `unzip -l dist/*.whl` (the
   full file list of the wheel).
2. **After** the move + reinstall (`task dev`): `uv build` again, then diff
   the new wheel's `unzip -l` against the recorded list. **The file lists
   must be identical.**
3. `cd tests && pytest` passes (full suite green).
4. `task check` (ruff) clean.
5. i18n tasks (`msg-make-crud_views`, `msg-comp-crud_views`) run without
   error, or are fixed per the risk note above.

If the wheel contents match and the suite passes, the layout change has
introduced no behavioral difference.

## Out of scope

- Renaming any package or changing any import path.
- Restructuring `tests/`, `examples/`, or `docs/`.
- Fixing the pre-existing `noxfile.py` reference to a `bootstrap5` extra that
  is not declared in `pyproject.toml` (latent, unrelated; PEP 508 treats an
  unknown extra as a warning).
