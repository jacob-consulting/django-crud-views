# src/ Layout Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the five distributed packages into a `src/` directory, adopting the PyPA `src/` layout, with a wheel-diff proof that the change is behavior-neutral.

**Architecture:** `git mv` the five package directories under a new `src/`, then update the three config files that reference on-disk paths (`pyproject.toml` hatch + bumpversion, `taskfile.yaml`). Import names are unchanged, so Django app strings, templates, and tests are unaffected. Correctness is proven by diffing the built wheel's file list before and after.

**Tech Stack:** Python 3.12+, hatchling build backend, uv, bump-my-version, Taskfile, pytest, ruff.

**Reference spec:** `docs/superpowers/specs/2026-06-08-src-layout-migration-design.md`

---

## File Structure

| Path | Change | Responsibility |
|---|---|---|
| `src/` | Create | New parent dir holding all distributed packages |
| `src/crud_views/` …`_plain` `_workflow` `_polymorphic` `_guardian` | Move | The five packages (was repo root) |
| `pyproject.toml` | Modify | Hatch wheel package paths + bumpversion `__init__.py` paths |
| `taskfile.yaml` | Modify | i18n task working directories |
| `/tmp/wheel-before.txt`, `/tmp/wheel-after.txt` | Create (transient) | Wheel file-list snapshots for the acceptance diff |

---

## Task 1: Capture the baseline wheel file list

**Files:**
- Create: `/tmp/wheel-before.txt` (transient artifact, not committed)

- [ ] **Step 1: Ensure a clean working tree**

Run: `git status --porcelain`
Expected: empty output (the spec commit is already in; nothing uncommitted).

- [ ] **Step 2: Build the current wheel and record its file list**

```bash
rm -rf dist
uv build
unzip -l dist/*.whl | awk '{print $4}' | grep -v '^$' | sort > /tmp/wheel-before.txt
wc -l /tmp/wheel-before.txt
```
Expected: a wheel builds under `dist/`, and `/tmp/wheel-before.txt` contains a sorted list of every file path inside it (dozens of lines, including `.py`, template `.html`, and static files under each `crud_views*` package).

- [ ] **Step 3: Sanity-check the baseline contains all five packages**

```bash
for p in crud_views crud_views_plain crud_views_workflow crud_views_polymorphic crud_views_guardian; do
  echo -n "$p: "; grep -c "^$p/" /tmp/wheel-before.txt
done
```
Expected: each package reports a non-zero count.

---

## Task 2: Move the five packages into `src/` with git mv

**Files:**
- Create: `src/`
- Move: the five `crud_views*` directories

- [ ] **Step 1: Create src/ and move each package preserving history**

```bash
mkdir -p src
git mv crud_views src/crud_views
git mv crud_views_plain src/crud_views_plain
git mv crud_views_workflow src/crud_views_workflow
git mv crud_views_polymorphic src/crud_views_polymorphic
git mv crud_views_guardian src/crud_views_guardian
```

- [ ] **Step 2: Verify the moves are staged as renames**

Run: `git status --short`
Expected: lines beginning with `R` (rename) for files under each package, e.g. `R  crud_views/apps.py -> src/crud_views/apps.py`. No `D`/`A` pairs for source files.

- [ ] **Step 3: Confirm root is clean of the old dirs**

Run: `ls -d crud_views* 2>/dev/null; ls -d src/crud_views*`
Expected: the first `ls` prints nothing (no `crud_views*` at root); the second lists all five under `src/`.

- [ ] **Step 4: Commit the move on its own**

```bash
git add -A
git commit -m "refactor: move crud_views packages under src/ (git mv, preserves history)"
```

---

## Task 3: Update hatchling wheel package paths

**Files:**
- Modify: `pyproject.toml` → `[tool.hatch.build.targets.wheel]`

- [ ] **Step 1: Prefix each package entry with `src/`**

Replace the existing block:

```toml
[tool.hatch.build.targets.wheel]
packages = [
    "crud_views",
    "crud_views_plain",
    "crud_views_workflow",
    "crud_views_polymorphic",
    "crud_views_guardian",
]
```

with:

```toml
[tool.hatch.build.targets.wheel]
packages = [
    "src/crud_views",
    "src/crud_views_plain",
    "src/crud_views_workflow",
    "src/crud_views_polymorphic",
    "src/crud_views_guardian",
]
```

Hatchling strips the leading `src/` automatically, mapping `src/crud_views` → `crud_views` inside the wheel.

- [ ] **Step 2: Verify the edit**

Run: `grep -A7 'targets.wheel' pyproject.toml`
Expected: all five entries now begin with `src/`.

---

## Task 4: Update bump-my-version file paths

**Files:**
- Modify: `pyproject.toml` → the two `[[tool.bumpversion.files]]` entries that point at `__init__.py`

- [ ] **Step 1: Update the crud_views __init__ path**

Change:

```toml
[[tool.bumpversion.files]]
filename = "crud_views/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

to:

```toml
[[tool.bumpversion.files]]
filename = "src/crud_views/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

- [ ] **Step 2: Update the crud_views_plain __init__ path**

Change:

```toml
[[tool.bumpversion.files]]
filename = "crud_views_plain/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

to:

```toml
[[tool.bumpversion.files]]
filename = "src/crud_views_plain/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

- [ ] **Step 3: Verify both __init__ paths now point under src/**

Run: `grep 'filename' pyproject.toml`
Expected: `pyproject.toml`, `src/crud_views/__init__.py`, `src/crud_views_plain/__init__.py`, `docs/index.md`, `README.md`. Only the two `__init__.py` lines should have changed.

- [ ] **Step 4: Dry-run bumpversion to confirm it finds every file**

```bash
uv run bump-my-version bump --dry-run --verbose patch 2>&1 | tail -30
```
Expected: it reports it would update all five listed files (no "could not find" / file-not-found errors). It does NOT write anything (`--dry-run`).

---

## Task 5: Update i18n task working directories

**Files:**
- Modify: `taskfile.yaml` → `msg-make-crud_views`, `msg-comp-crud_views`

- [ ] **Step 1: Point both message tasks at the new package location**

Change:

```yaml
  msg-make-crud_views:
    dir: crud_views
    cmd: python -m django makemessages -l de --settings=settings_i18n

  msg-comp-crud_views:
    dir: crud_views
    cmd: python -m django compilemessages --settings=settings_i18n
```

to:

```yaml
  msg-make-crud_views:
    dir: src/crud_views
    cmd: python -m django makemessages -l de --settings=settings_i18n

  msg-comp-crud_views:
    dir: src/crud_views
    cmd: python -m django compilemessages --settings=settings_i18n
```

- [ ] **Step 2: Verify the edit**

Run: `grep -A1 'msg-make-crud_views\|msg-comp-crud_views' taskfile.yaml`
Expected: both `dir:` lines read `src/crud_views`.

- [ ] **Step 3: Commit the config edits**

```bash
git add pyproject.toml taskfile.yaml
git commit -m "refactor: update hatch, bumpversion, and i18n paths for src/ layout"
```

---

## Task 6: Reinstall editable and prove the wheel is identical

This is the acceptance gate — the build must produce a byte-identical file list.

**Files:**
- Create: `/tmp/wheel-after.txt` (transient artifact, not committed)

- [ ] **Step 1: Reinstall the project editable from the new layout**

```bash
uv pip install --upgrade '.[ordered,polymorphic,workflow,dev,test]'
```
Expected: install succeeds; the editable install now points at `src/`.

- [ ] **Step 2: Confirm the package imports from src/**

```bash
python -c "import crud_views, os; print(os.path.dirname(crud_views.__file__))"
```
Expected: a path ending in `/src/crud_views`.

- [ ] **Step 3: Rebuild the wheel and record the new file list**

```bash
rm -rf dist
uv build
unzip -l dist/*.whl | awk '{print $4}' | grep -v '^$' | sort > /tmp/wheel-after.txt
```

- [ ] **Step 4: Diff the before/after file lists — MUST be identical**

```bash
diff /tmp/wheel-before.txt /tmp/wheel-after.txt && echo "IDENTICAL"
```
Expected: `IDENTICAL` with no diff output. If anything differs, STOP — the hatch config in Task 3 is wrong (likely the `src/` prefix is not being stripped); do not proceed until the lists match.

---

## Task 7: Run the test suite and linter

**Files:** none modified

- [ ] **Step 1: Run the full test suite against the installed package**

```bash
cd tests && pytest -q; cd ..
```
Expected: all tests pass (the suite was 276 passing before this work; the count should be unchanged).

- [ ] **Step 2: Run ruff check and format verification**

```bash
uv run ruff check .
uv run ruff format --check .
```
Expected: both clean (no errors, nothing would be reformatted).

---

## Task 8: Verify (and if needed, fix) the i18n tasks

The `settings_i18n.py` file stays at repo root; the package moved one level deeper, so the task's cwd→root relationship changed.

**Files:**
- Possibly modify: `taskfile.yaml` (only if the verification below fails)

- [ ] **Step 1: Try the compile-messages task as-is**

```bash
task msg-comp-crud_views
```
Expected (success path): it runs without a `ModuleNotFoundError: settings_i18n` and without an `ImproperlyConfigured` error. If it succeeds, skip Steps 2–3.

- [ ] **Step 2: If it failed with a settings-not-found error, add PYTHONPATH**

Only if Step 1 errored on locating `settings_i18n`. Update both tasks to put the repo root on the path (the task runs from `src/crud_views`, so root is two levels up):

```yaml
  msg-make-crud_views:
    dir: src/crud_views
    cmd: PYTHONPATH=../.. python -m django makemessages -l de --settings=settings_i18n

  msg-comp-crud_views:
    dir: src/crud_views
    cmd: PYTHONPATH=../.. python -m django compilemessages --settings=settings_i18n
```

- [ ] **Step 3: Re-run to confirm the fix**

```bash
task msg-comp-crud_views
```
Expected: runs without the settings import error.

- [ ] **Step 4: Commit any i18n fix (skip if Step 1 already passed)**

```bash
git add taskfile.yaml
git commit -m "fix: set PYTHONPATH for i18n tasks under src/ layout"
```

---

## Task 9: Clear stale caches and rebuild the code index

**Files:** none committed (caches are gitignored)

- [ ] **Step 1: Remove stale bytecode caches**

```bash
find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
```
Expected: the stray root `__pycache__` and any in-tree caches are gone.

- [ ] **Step 2: Rebuild the codegraph index for the new paths**

```bash
codegraph index 2>/dev/null || echo "Rebuild .codegraph via your usual codegraph command (paths changed)"
```
Expected: the index is regenerated, or a reminder is printed if the CLI name differs. This is developer-local only.

- [ ] **Step 3: Final verification of a clean, complete migration**

```bash
git status --porcelain
git log --oneline -4
ls src/
```
Expected: working tree clean; the last commits show the move + config edits; `src/` lists all five packages.

---

## Self-Review notes

- **Spec coverage:** moves (Task 2), hatch config (Task 3), bumpversion (Task 4), taskfile i18n (Task 5), editable reinstall + wheel-diff acceptance (Task 6), tests + ruff (Task 7), i18n risk verification with the PYTHONPATH fix (Task 8), stale-cache/codegraph risk (Task 9). All spec sections map to a task.
- **Out-of-scope items** (package renames, tests/examples/docs restructure, the undeclared `bootstrap5` extra) are intentionally not touched.
- **Acceptance gate** is the Task 6 `diff … && echo IDENTICAL` — a hard stop if the wheel contents change.
