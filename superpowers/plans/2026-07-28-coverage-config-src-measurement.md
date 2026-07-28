# Coverage Config / `src/` Measurement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Codecov measure the package source in `src/` instead of the test suite, by running pytest from the repository root so coverage.py finds its config and emits repo-relative paths.

**Architecture:** The root `pyproject.toml` already carries a `[tool.coverage.*]` config that has never been read, because `noxfile.py` chdirs into `tests/` and coverage.py neither walks up to find a config nor can make `src/` paths relative to `tests/`. Removing that single `chdir` fixes both halves at once — the existing config becomes live automatically, and paths come out as `src/…`. Everything else in this plan is following that change to its consequences: the emitted `coverage.xml` moves to the repo root (two workflows reference it), three documents tell contributors to `cd tests`, and a regression test pins the `source` list to the actual contents of `src/`.

**Tech Stack:** coverage.py 7.15.2, pytest + pytest-cov + pytest-xdist, nox (uv backend), GitHub Actions, `codecov/codecov-action@v5`, `tomllib` (stdlib).

**Spec:** `superpowers/specs/2026-07-28-coverage-config-src-measurement-design.md`
**Issue:** [#103](https://github.com/jacob-consulting/django-crud-views/issues/103) — see also the [correction comment](https://github.com/jacob-consulting/django-crud-views/issues/103#issuecomment-5109148896), which supersedes the issue's "Suggested fix" section.
**Branch:** `feature/coverage-config-src-measurement-103` (already created; spec already committed there)

---

## Starting Point — read this first (written 2026-07-28)

Everything below was established in the planning session. **You do not need to re-derive any of it, and re-running the experiments is a waste of time — they are recorded here with their results.**

### Where things stand

- **Branch:** `feature/coverage-config-src-measurement-103`, three commits ahead of `main` (`main` tip is `cf3f038`). All three are documentation only — spec `6590916`, spec amendment `5ff0666`, this plan `977dc93`. **No implementation work has started.** Task 1 Step 1 is the first thing to do.
- **Working tree:** three untracked files at the repo root — `PR-ruff-0.16-explicit-select.md`, `feature-ruff-0.16-explicit-select.patch`, and a long `docs(view)__…patch`. These are **leftovers from earlier, unrelated work on #102**. Do not commit them, do not delete them, do not let them into the PR.
- **Issue #103's "Suggested fix" section is wrong** and has been publicly corrected — see the [correction comment](https://github.com/jacob-consulting/django-crud-views/issues/103#issuecomment-5109148896). Read the comment, not the issue body, for the mechanism.
- **No PR exists yet.** Task 3 Step 5 opens it.

### The finding that drives the whole plan

Coverage.py's relative directory follows the **process CWD**, not the location of the config file. `relative_files = true` only strips the prefix from files living *under* that directory, and `src/` is not under `tests/`. This is why the issue's proposed fixes fail.

Tested against coverage.py 7.15.2 with the package installed editable:

| Setup | Emitted filename | Codecov-mappable |
|---|---|---|
| `relative_files`, `tests/.coveragerc` (issue option 1) | `home/alex/…/src/crud_views/checks.py` | no |
| `relative_files`, root config via `--cov-config` (issue option 2) | `home/alex/…/src/crud_views/checks.py` | no |
| `[paths]` remapping, cwd=`tests/` | `home/alex/…/src/crud_views/checks.py` | no |
| `relative_files`, **cwd = repo root** (issue option 3) | `src/crud_views/checks.py` | **yes** |

Two corollaries worth not rediscovering:

- Running from the root makes the root config live with **no `--cov-config` flag**. Coverage discovers `pyproject.toml` in the CWD, and pytest-cov's `.coveragerc` default is special-cased by coverage.py to mean "search the defaults". Confirmed directly: from the root, `coverage.Coverage()` reports `config_file: …/pyproject.toml`, `source: [4 packages]`, `fail_under: 88.0`.
- `relative_files` is **not** needed for the filenames — running from the root yields `src/…` without it. It is worth setting for a different reason: it empties the XML `<source>` element. Without it the report carries `<source>/home/alex/projects/alex/django-crud-views</source>`, a machine-specific prefix Codecov's path-fixing must guess past.

### Baseline measurements (py3.12 / Django 5.2, this machine)

Already taken with the full suite run from the repo root. **868 passed, 1 skipped — identical to running from `tests/`**, so the CWD change breaks no conftest, xdist, or path behaviour. That is the main execution risk, and it is already retired.

src-only total: **4429 statements, 268 missing, 94%**.

| Package | Stmts | Miss | Cov |
|---|---:|---:|---:|
| `crud_views` | 3387 | 221 | 93.5% |
| `crud_views_guardian` | 264 | 27 | 89.8% |
| `crud_views_object_detail` | 382 | 9 | 97.6% |
| `crud_views_polymorphic` | 135 | 4 | 97.0% |
| `crud_views_workflow` | 261 | 7 | 97.3% |

### Decisions already made — do not relitigate

- **Scope is minimal.** No `codecov.yml`, no matrix combining. Both were considered and deliberately deferred to follow-up issues.
- **`fail_under` stays at 88.** The number was going to be retuned out of fear the figure would drop below the gate; it doesn't — 94% leaves 6 points of headroom. Keeping measurement and policy changes separate is the point.
- **One working directory everywhere.** The alternative — change nox only, leave `cd tests && pytest` documented — was rejected because the bug exists precisely because two CWDs were in play. Hence the `CLAUDE.md` / `CONTRIBUTING.md` / PR-template edits.
- **Nothing turns red on landing.** This repo posts only `codecov/patch`, not `codecov/project` (verified against `cf3f038`'s statuses), so the 99% → 94% move affects the badge and Codecov UI only.

### Environment

- Local venv: `.venv/bin/python` — Python 3.12.3, Django 5.2.14, coverage.py 7.15.2.
- CI matrix is Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0, minus Django 4.2 × py3.14 = **8 rows**. Codecov uploads only from the py3.13 row.
- `taskfile.yaml` (lowercase, not `Taskfile.yml`) provides `task format`, `task check`, `task test`. It needs **no change** — `task test` shells out to nox.

## Global Constraints

- Line length 120, double quotes, ruff-formatted. `ruff-format` runs as a pre-commit hook.
- Python floor is 3.12, so `tomllib` is available in the stdlib — do not add a `toml` dependency.
- `fail_under` **stays at 88**. Do not retune it. This change corrects measurement, not policy.
- Do not add a `codecov.yml`. Do not add `--cov-append` or otherwise merge matrix rows. Both are explicitly out of scope and tracked as follow-ups.
- The `examples` nox session keeps its own `session.chdir("./examples/bootstrap5")`. Only the `tests` session loses its chdir.
- All work happens on `feature/coverage-config-src-measurement-103`. Do not commit to `main`.
- Every commit message references `#103`.

---

### Task 1: Pin the coverage `source` list to `src/`, and fix it

The `source` list omits `crud_views_guardian`. Nobody noticed because the entire config was inert. This task adds the test that would have caught it, then makes the config correct.

**Files:**
- Create: `tests/test1/test_coverage_config.py`
- Modify: `pyproject.toml:129-131` (the `[tool.coverage.run]` block)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a corrected `[tool.coverage.run]` block containing `relative_files = true` and a five-element sorted `source` list. Task 2 depends on this config being both correct and discoverable from the repo root.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_coverage_config.py`:

```python
"""Guards against drift between the coverage config and the packages in src/.

`crud_views_guardian` was missing from `[tool.coverage.run].source` for a long time
without anyone noticing, because the whole config was inert — coverage.py never found
it while pytest ran from `tests/`. See issue #103.
"""

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _coverage_run_config() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["tool"]["coverage"]["run"]


def test_coverage_source_lists_every_src_package():
    """Every distributed package must be measured, in sorted order."""
    packages = sorted(p.name for p in (REPO_ROOT / "src").iterdir() if (p / "__init__.py").is_file())
    assert _coverage_run_config()["source"] == packages


def test_coverage_emits_relative_paths():
    """Without this, coverage.xml carries an absolute machine-specific <source> prefix."""
    assert _coverage_run_config()["relative_files"] is True
```

`parents[2]` resolves to the repo root: `parents[0]` is `test1`, `parents[1]` is `tests`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test1/test_coverage_config.py -v`

Expected: both tests FAIL.
- `test_coverage_source_lists_every_src_package` — AssertionError; the config list is 4 items in unsorted order (`crud_views`, `crud_views_polymorphic`, `crud_views_workflow`, `crud_views_object_detail`), the computed list is 5 items sorted.
- `test_coverage_emits_relative_paths` — `KeyError: 'relative_files'`.

Both failures are the point. Do not proceed until you have seen them.

- [ ] **Step 3: Fix the config**

In `pyproject.toml`, replace:

```toml
[tool.coverage.run]
source = ["crud_views", "crud_views_polymorphic", "crud_views_workflow", "crud_views_object_detail"]
```

with:

```toml
[tool.coverage.run]
relative_files = true
source = [
    "crud_views",
    "crud_views_guardian",
    "crud_views_object_detail",
    "crud_views_polymorphic",
    "crud_views_workflow",
]
```

Leave `[tool.coverage.report]` exactly as it is — `show_missing`, `skip_empty`, and `fail_under = 88` are all unchanged.

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test1/test_coverage_config.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test1/test_coverage_config.py pyproject.toml
git commit -m "test(coverage): pin source list to src/ packages; add guardian, relative_files (#103)"
```

---

### Task 2: Run the test suite from the repository root

This is the actual fix. Removing the `chdir` makes coverage.py discover the root `pyproject.toml` and anchor relative paths to the repo root. The emitted `coverage.xml` moves from `tests/` to the root, so both workflows that upload it must change in the same commit or CI breaks.

**Files:**
- Modify: `noxfile.py:16-17`
- Modify: `.github/workflows/tests.yml:29`
- Modify: `.github/workflows/publish.yml:27`
- Modify: `CLAUDE.md:23-30`
- Modify: `CONTRIBUTING.md:27`
- Modify: `.github/PULL_REQUEST_TEMPLATE.md:19`

**Interfaces:**
- Consumes: the corrected `[tool.coverage.run]` block from Task 1.
- Produces: `coverage.xml` at the repository root, containing `<source></source>`, filenames beginning `src/`, and no `tests/` entries. Task 3 asserts on exactly these properties.

- [ ] **Step 1: Remove the chdir from the nox `tests` session**

In `noxfile.py`, replace lines 16-17:

```python
    with session.chdir("./tests"):
        session.run("pytest", "-n", "auto", "--cov", "--cov-report=term-missing", *session.posargs)
```

with:

```python
    session.run("pytest", "tests", "-n", "auto", "--cov", "--cov-report=term-missing", *session.posargs)
```

Note the de-indent — the `session.run` is no longer inside a `with` block. Do not touch the `examples` session at line 30; it keeps its own chdir.

No `--cov-config` flag is needed. pytest-cov's default of `.coveragerc` is special-cased by coverage.py to mean "search the defaults", so `pyproject.toml` in the CWD is found.

- [ ] **Step 2: Point both workflows at the new coverage.xml location**

In `.github/workflows/tests.yml`, line 29, change:

```yaml
          files: tests/coverage.xml
```

to:

```yaml
          files: coverage.xml
```

Then make the identical change in `.github/workflows/publish.yml`, line 27. This second one is easy to miss — it is a separate copy of the upload step that runs on release, and leaving it would make every release upload a nonexistent file.

- [ ] **Step 3: Update the three documents that say `cd tests`**

In `CLAUDE.md`, replace lines 23-30:

```markdown
# Run tests directly for quick iteration (from tests/ directory)
cd tests && pytest

# Run a single test file
cd tests && pytest test1/test_crud.py

# Run a single test
cd tests && pytest test1/test_crud.py::test_name -v
```

with:

```markdown
# Run tests directly for quick iteration (from the repo root)
pytest tests

# Run a single test file
pytest tests/test1/test_crud.py

# Run a single test
pytest tests/test1/test_crud.py::test_name -v
```

In `CONTRIBUTING.md`, line 27, change:

```markdown
   - quick: `cd tests && pytest`
```

to:

```markdown
   - quick: `pytest tests`
```

In `.github/PULL_REQUEST_TEMPLATE.md`, line 19, change:

```markdown
- [ ] Tests pass (`cd tests && pytest`)
```

to:

```markdown
- [ ] Tests pass (`pytest tests`)
```

- [ ] **Step 4: Verify the suite still passes from the new working directory**

Run: `.venv/bin/python -m pytest tests -n auto -q`

Expected: **870 passed, 1 skipped** — the 868 pre-existing passes plus Task 1's 2 new tests. The exact count matters less than the absence of failures and errors; what you are checking is that no conftest, fixture, or path behaviour depends on the old working directory.

- [ ] **Step 5: Verify coverage now measures `src/`**

Run:

```bash
.venv/bin/python -m pytest tests -n auto --cov --cov-report=xml -q
```

Expected: the run reports roughly 94% and does **not** fail the `fail_under = 88` gate. A `coverage.xml` appears at the repository root.

Then assert on its contents:

```bash
echo "source element: $(grep -o '<source>[^<]*</source>' coverage.xml)"
echo "test files:     $(grep -c 'filename="tests/' coverage.xml)"
echo "guardian files: $(grep -c 'crud_views_guardian' coverage.xml)"
grep -o 'filename="[^"]*"' coverage.xml | sort -u | head -3
```

Expected, all four:
- `source element: <source></source>` — empty, no absolute prefix
- `test files:     0`
- `guardian files:` a non-zero count
- filenames beginning `src/`, e.g. `filename="src/crud_views/apps.py"`

If `<source>` contains an absolute path, `relative_files` did not take effect — recheck Task 1 Step 3. If any `tests/` files appear, the `source` list is not being applied — confirm you are running from the repo root.

- [ ] **Step 6: Commit**

```bash
git add noxfile.py .github/workflows/tests.yml .github/workflows/publish.yml \
        CLAUDE.md CONTRIBUTING.md .github/PULL_REQUEST_TEMPLATE.md
git commit -m "fix(ci): run pytest from repo root so coverage measures src/ (#103)"
```

---

### Task 3: Changelog, full matrix check, and pull request

**Files:**
- Modify: `CHANGELOG.md` (the `## Unreleased` section)

**Interfaces:**
- Consumes: the root `coverage.xml` produced by Task 2.
- Produces: an open PR against `main`.

- [ ] **Step 1: Add the changelog entry**

`CHANGELOG.md` already has an `## Unreleased` section with a `### Changed` subsection. Add a `### Fixed` subsection directly after the existing `### Changed` block (before the `## 0.19.0` heading):

```markdown
### Fixed

- Coverage is now measured for the package source. `pytest` runs from the repository
  root instead of `tests/`, so coverage.py finds the `[tool.coverage.*]` config in
  `pyproject.toml` — previously it found none, measured the test suite instead of
  `src/`, and emitted absolute paths that Codecov silently discarded. The reported
  project figure drops from ~99% to ~94% as a result: that is a measurement
  correction, not a regression. `crud_views_guardian`, missing from the coverage
  `source` list, is now included. (#103)
```

- [ ] **Step 2: Run the lint and format gates**

Run: `task format && task check`
Expected: both clean, no diff left unstaged. If `ruff format` rewrites `noxfile.py` after the de-indent in Task 2, stage the result.

- [ ] **Step 3: Run one full nox session end to end**

Run: `uv run nox -s "tests-3.12(django='5.2')" -- --cov-report=xml`

Expected: the session passes and the `fail_under = 88` gate is satisfied. This exercises the real CI invocation path — the previous verification ran pytest directly, which does not prove the nox session works after the chdir removal.

Note: `fail_under` is being enforced for the first time ever, across all 8 matrix rows. Local headroom is 6 points (94% vs 88%), but this is the one place CI could surprise you.

- [ ] **Step 4: Commit and push**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): coverage now measures src/ (#103)"
git push -u origin feature/coverage-config-src-measurement-103
```

- [ ] **Step 5: Open the pull request**

```bash
gh pr create --title "fix(ci): coverage config never read — measure src/ instead of tests/ (#103)" --body "$(cat <<'EOF'
Fixes #103.

## What was wrong

The `[tool.coverage.*]` config in the root `pyproject.toml` was never read. `noxfile.py`
chdir'd into `tests/`, and coverage.py neither walks up to find a config nor can make
`src/` paths relative to `tests/`. So `--cov` measured every imported module including the
test suite, and emitted absolute paths for `src/` that Codecov silently discarded.

**Codecov has never measured this package.** The ~99% figure was the test suite measuring
itself.

## What changed

`pytest` now runs from the repository root. That single change fixes both halves: the
existing config becomes live, and paths come out as `src/crud_views/…`.

Note that the fix is *not* the one suggested in the issue — `relative_files = true` is not
load-bearing; the working directory is. Both of the issue's preferred options were tested
and leave `src/` unmappable; see the [correction comment](https://github.com/jacob-consulting/django-crud-views/issues/103#issuecomment-5109148896).

- `noxfile.py` — drop `session.chdir("./tests")` from the `tests` session
- `pyproject.toml` — add `relative_files = true`; add the missing `crud_views_guardian` to `source`
- `tests.yml` / `publish.yml` — `coverage.xml` moved to the repo root
- `CLAUDE.md`, `CONTRIBUTING.md`, PR template — quick loop is now `pytest tests` from the root
- `tests/test1/test_coverage_config.py` — new; pins `source` to the actual contents of `src/`

## Expect the number to drop

Project coverage goes from ~99% to **~94%** (4429 statements, 268 missing). This is a
measurement correction, not a regression — `tests/` leaves the report and `src/` enters it,
so the tracked file set changes wholesale. Only `codecov/patch` posts a status on this repo,
so nothing turns red.

`fail_under` stays at 88 — retuning the gate in the same PR as the measurement fix would
make neither attributable. Note it becomes an enforced gate for the first time here.

| Package | Stmts | Miss | Cov |
|---|---:|---:|---:|
| `crud_views` | 3387 | 221 | 93.5% |
| `crud_views_guardian` | 264 | 27 | 89.8% |
| `crud_views_object_detail` | 382 | 9 | 97.6% |
| `crud_views_polymorphic` | 135 | 4 | 97.0% |
| `crud_views_workflow` | 261 | 7 | 97.3% |

`crud_views_guardian` — the package the `source` drift omitted — is the weakest of the five.

## Follow-ups, deliberately not in this PR

- Matrix rows clobber each other: all three Django sessions write the same `coverage.xml`
  with no `--cov-append`, so only Django 6.0 × py3.13 is uploaded. Version-gated
  `try/except ImportError` branches will now read as uncovered.
- No `codecov.yml`; project and patch targets are inherited from Codecov's auto-defaults.
- `crud_views_guardian` coverage at 89.8%.
EOF
)"
```

- [ ] **Step 6: Wait for CI, then verify Codecov actually changed**

Wait for all checks. `gh pr checks` is known to exit 0 while Codecov is still pending on this repo, so query the API directly:

```bash
gh api repos/jacob-consulting/django-crud-views/commits/$(git rev-parse HEAD)/status \
  --jq '.statuses[] | "\(.context)\t\(.state)"'
```

Then confirm the fix actually landed on Codecov's side — this is the real acceptance test, since a green build proves nothing about what Codecov ingested:

```bash
PR=$(gh pr view --json number --jq .number)
curl -s "https://api.codecov.io/api/v2/github/jacob-consulting/repos/django-crud-views/compare/?pullid=$PR" \
  | python3 -c "
import json, sys
from collections import Counter
files = json.load(sys.stdin).get('files', [])
print(Counter(f['head_name'].split('/')[0] for f in files))
print('src/ files tracked:', sum(1 for f in files if f['head_name'].startswith('src/')))"
```

Expected: the counter is dominated by `src`, and the `src/` count is non-zero. Before this change the same query returned `Counter({'tests': 97})` with zero `src/` files.

If `src/` is still absent, stop and re-inspect the uploaded `coverage.xml` in the CI logs — do not merge.

- [ ] **Step 7: Report and hand off**

Report the CI status, the Codecov compare result, and the new project percentage. Do **not** merge — the squash-merge decision is the maintainer's.

---

## Self-Review

**Spec coverage:** every change in the spec maps to a task — `pyproject.toml` and the drift guard to Task 1; `noxfile.py`, both workflows, and the three documents to Task 2; `CHANGELOG.md` to Task 3. The spec's two verification steps are Task 2 Step 5 and Task 3 Step 6. `fail_under` staying at 88 is a global constraint. The three out-of-scope items appear in the PR body as follow-ups.

**Placeholders:** none. Every code and config change is quoted verbatim with its before and after.

**Consistency:** `_coverage_run_config()` is defined once in Task 1 and used by both tests in that file; no later task references it. The `source` list in Task 1 Step 3 is byte-identical to the sorted list Task 1 Step 1's test computes. The `coverage.xml` properties asserted in Task 2 Step 5 are the same ones Task 2's Interfaces block promises.

**Known soft spot:** the expected test count in Task 2 Step 4 (870) is derived, not observed — the pre-change baseline was 868 passed / 1 skipped and Task 1 adds 2 tests. Treat a mismatch as worth investigating, not as an automatic failure.

---

## Resuming Mid-Plan

If you are picking this up after some tasks are already done, establish where you are before touching anything:

```bash
git log --oneline main..HEAD
```

Map the commits you find onto the plan:

| Last commit subject | Completed through | Resume at |
|---|---|---|
| `docs(plan): …` | plan only, nothing implemented | Task 1, Step 1 |
| `test(coverage): pin source list …` | Task 1 | Task 2, Step 1 |
| `fix(ci): run pytest from repo root …` | Task 2 | Task 3, Step 1 |
| `docs(changelog): …` | Task 3 Step 4 | Task 3, Step 5 (open the PR) |

Then check whether a PR is already open with `gh pr view --json number,state,url` before running Task 3 Step 5, so you don't open a duplicate.

The single highest-value confirmation, if you want one cheap check that the work is behaving, is Task 2 Step 5's assertions on the root `coverage.xml`. Empty `<source>`, filenames starting `src/`, zero `tests/` entries — that quartet is the whole point of the change.
