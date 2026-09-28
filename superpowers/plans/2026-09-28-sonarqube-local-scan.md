# SonarQube Local Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A maintainer runs `task sonar` from the repo root; it refreshes the install, runs the test suite with coverage, and uploads a SonarQube analysis of `src/` including Python coverage to `https://sonar.cnbg-n.com` as project `django-crud-views:main`.

**Architecture:** All project configuration lives in a new `sonar-project.properties` at the repo root. A new `sonar` task in `taskfile.yaml` loads the token from a gitignored `.env`, produces `coverage.xml` at the repo root, and runs the official `sonarsource/sonar-scanner-cli` Docker image with the repo mounted read-only. No Python or JS dependency is added.

**Tech Stack:** Task (go-task) 3.x (installed: 3.53.1), uv, pytest + pytest-cov + pytest-xdist (already in the `test` extra), Docker, `sonarsource/sonar-scanner-cli:12.1.0.3233_8.0.1` (already pulled locally), SonarQube server 26.5.0.

**Spec:** `superpowers/specs/2026-09-28-sonarqube-local-scan-design.md` — read it before starting.

## Global Constraints

- **Leak rule (hard):** Nothing committed to this repo — files, comments, commit messages, PR text — may reference other local projects, their names, paths, or hosts. This repo is **public**. Before every commit run the leak check in "Leak check command" below; it must print nothing.
- **Token rule (hard):** Never print, `cat`, `echo`, log, or commit the value of `SONAR_TOKEN` or the contents of `.env`. Never ask the user to paste the token into chat. Pass it to Docker by name only (`-e SONAR_TOKEN`). The `.gitignore` entry for `.env` (Task 1) must be committed before any `.env` file exists in the working tree.
- Project key: `django-crud-views:main` — exact. Project name: `django-crud-views` — exact.
- Host URL: `https://sonar.cnbg-n.com` — exact, without quotes in the properties file.
- Scanner image: `sonarsource/sonar-scanner-cli:12.1.0.3233_8.0.1` — pinned, never `latest`.
- Only `-D` flag allowed on the scanner command line: `-Dsonar.working.directory=/tmp/scannerwork`. Key, name, host, sources and report paths come from `sonar-project.properties` only.
- Analysis scope: `src/` only. `examples/` is out of scope. Migrations are excluded. JS is analysed but excluded from coverage.
- SCM stays enabled; never add `sonar.scm.disabled=true`.
- All comments and docs in English. YAML in `taskfile.yaml` uses 2-space indentation matching the existing file.
- No CHANGELOG entry (maintainer tooling, no package change — explicit spec decision, overrides the general CONTRIBUTING.md rule).
- Specs/plans live under `superpowers/`; `docs/` is mkdocs-only and is **not** touched by this plan.
- **Execute in the main checkout** (`/home/alex/projects/alex/django-crud-views`) on the existing branch — **never in a git worktree**. Tasks 3 and 5 need the host's `.venv`, Docker, the user's `.env`, and a real `.git` directory (in a worktree `.git` is a file pointing to an absolute host path that does not exist inside the scanner container, so SCM detection fails).
- Branch: `feature/sonarqube-local-scan` (already exists; contains the spec commit `021397a`). Work there. Do not push or open a PR until Task 5.

### Leak check command

The forbidden patterns are stored **outside the tracked tree** in `.git/info/leak-patterns` (one extended regex per
line; git never commits anything under `.git/`). Never copy those patterns into a tracked file, commit message, or PR
text — that would itself be the leak. If the file is missing, stop and ask the user to recreate it.

Run from the repo root. Must produce **no output**:

```bash
P="$(git rev-parse --git-common-dir)/info/leak-patterns"; test -s "$P" || echo "MISSING $P - stop and ask the user"
git diff main --name-only | xargs -r grep -n -i -E -f "$P"; git log main..HEAD --format=%B | grep -n -i -E -f "$P"
```

## Background an implementer needs

- `task dev` installs the package **non-editable** into `.venv` (`uv pip install --upgrade .[all,dev,test,examples]`). Coverage therefore measures the copy in `.venv/lib/python3.X/site-packages/`, and `[tool.coverage.paths]` in `pyproject.toml` maps file names back to `src/...`. Line numbers still come from the installed copy, so the task must reinstall the package before running tests, or coverage lines drift from `src/`.
- `[tool.coverage.report] fail_under = 88` makes pytest exit non-zero when coverage is below 88 %. The scan must still run in that case (and when tests fail) — hence `ignore_error: true` on the pytest step.
- If pytest crashes before writing a report, a **stale** `coverage.xml` from an earlier run would be uploaded. The task therefore deletes `coverage.xml` first and refuses to scan if it was not rewritten.
- Use `uv run --no-sync pytest ...`, not plain `uv run pytest`: without `--no-sync`, `uv run` syncs the project environment from the (gitignored, local) `uv.lock` and may re-install the package as editable, silently changing the environment `task dev` built.
- Existing `coverage.xml` already contains `filename="src/crud_views/..."` paths (relative), which is what SonarQube needs to match against `sonar.sources=src`.
- The scanner container runs as `uid=1000(scanner-cli)`. On the maintainer's machine the host user is also uid 1000, so reading `.git` from the read-only mount should work. If the scan log shows a git/SCM error about repository ownership, add `--user "$(id -u):$(id -g)"` to the `docker run` line (Task 4, Step 5). Do not disable SCM.
- **Worktree gotcha:** if you run this in a git worktree, an inherited `VIRTUAL_ENV` points `uv pip install` at the main checkout's `.venv`. Run tasks with `env -u VIRTUAL_ENV task sonar` there.
- The server requires authentication for every API call (anonymous requests get 401), so you cannot verify the project from the command line without the token.
- Tests live in `tests/` (Python in `tests/test1/`, JS in `tests/js/`), **not** under `src/`.

## Review Focus

1. **`.env` missing or `SONAR_TOKEN` empty** → `task sonar` stops before installing or testing, with a message that names `.env.example` and `CONTRIBUTING.md`. Tested in Task 3, Steps 2 and 4.
2. **Docker daemon not running** → task stops before the long test run with a clear message, not after 2 minutes of tests. Tested in Task 3, Step 4 (precondition order) and Step 6.
3. **pytest crashes / collection error so no `coverage.xml` is written** → the scan does not upload a stale report from a previous run. Tested in Task 3, Step 7.
4. **Tests fail or coverage < 88 %** → the scan still runs. Covered by `ignore_error: true`; verified by reading the dry run in Task 3, Step 6.
5. **`task sonar` invoked from a subdirectory** (`cd src && task sonar`) → Task resolves the root taskfile and runs in the repo root; the Docker mount uses `{{.ROOT_DIR}}`, not `$PWD`. Tested in Task 3, Step 6.

---

## File map

| File | Status | Responsibility |
|---|---|---|
| `.gitignore` | modify | Ignore `.env` and `.scannerwork/` |
| `.env.example` | create | Documents the one variable `task sonar` needs; placeholder only |
| `sonar-project.properties` | create | Complete SonarQube project configuration |
| `taskfile.yaml` | modify | New `sonar` task |
| `CONTRIBUTING.md` | modify | Maintainer section on running the analysis |

---

### Task 1: Ignore secrets before they exist

**Files:**
- Modify: `.gitignore` (append at end; file currently ends with the line `coverage-js`)
- Create: `.env.example`

**Interfaces:**
- Consumes: nothing.
- Produces: `.env` is gitignored; `.env.example` defines variable name `SONAR_TOKEN` used by Task 3.

- [ ] **Step 1: Confirm `.env` is not yet ignored and does not exist**

Run: `git check-ignore -v .env; echo "exit=$?"; test -e .env && echo ".env EXISTS - STOP" || echo "no .env"`
Expected: `exit=1` and `no .env`. If `.env EXISTS`, stop and tell the user — do not read it.

- [ ] **Step 2: Append to `.gitignore`**

Append these lines to the end of `.gitignore`:

```
# SonarQube: local token and scanner work directory
.env
.scannerwork/
```

- [ ] **Step 3: Create `.env.example`**

```
# Copy to .env (gitignored) and fill in. Used by `task sonar`.
# Project analysis token for django-crud-views:main
# (SonarQube: My Account -> Security -> Generate Token).
SONAR_TOKEN=
```

- [ ] **Step 4: Verify**

Run: `git check-ignore -v .env .scannerwork/x; git check-ignore .env.example; echo "example-ignored-exit=$?"`
Expected: two lines naming `.gitignore` for `.env` and `.scannerwork/x`, then `example-ignored-exit=1` (the example is **not** ignored).

- [ ] **Step 5: Leak check, then commit**

Run the leak check command from Global Constraints (expect no output), then:

```bash
git add .gitignore .env.example
git commit -m "chore(sonar): ignore .env and add .env.example for the SonarQube token"
```

---

### Task 2: SonarQube project configuration

**Files:**
- Create: `sonar-project.properties` (repo root)

**Interfaces:**
- Consumes: nothing.
- Produces: `sonar.python.coverage.reportPaths=coverage.xml` — Task 3 must write the report to exactly `coverage.xml` in the repo root.

- [ ] **Step 1: Create `sonar-project.properties`**

```properties
# SonarQube analysis of the package sources. Run with `task sonar` (see CONTRIBUTING.md).
sonar.projectKey=django-crud-views:main
sonar.projectName=django-crud-views
sonar.host.url=https://sonar.cnbg-n.com

sonar.sources=src
sonar.tests=tests
# Generated by Django.
sonar.exclusions=**/migrations/**
# Vitest writes no coverage report yet; JS is analysed but not counted for coverage.
sonar.coverage.exclusions=**/*.js

sonar.python.version=3.12,3.13,3.14
sonar.python.coverage.reportPaths=coverage.xml
sonar.sourceEncoding=UTF-8
```

- [ ] **Step 2: Verify values are exact and unquoted**

Run: `grep -n '"' sonar-project.properties; echo "quotes-exit=$?"; grep -c '^sonar\.' sonar-project.properties`
Expected: `quotes-exit=1` (no double quotes anywhere) and `10`.

- [ ] **Step 3: Verify the globs match what they should**

Run: `find src -path '*/migrations/*' -name '*.py' | head -3; find src -name '*.js' | wc -l`
Expected: migration files exist under `src/crud_views/migrations/` and `src/crud_views_workflow/migrations/` (so the exclusion has an effect); `5` JS files.

- [ ] **Step 4: Leak check, then commit**

```bash
git add sonar-project.properties
git commit -m "chore(sonar): add sonar-project.properties for django-crud-views:main"
```

---

### Task 3: `task sonar`

**Files:**
- Modify: `taskfile.yaml` — add a new task after the existing `test-js-watch` task (before `install-skill-claude`).

**Interfaces:**
- Consumes: `.env` / `SONAR_TOKEN` (Task 1), `sonar-project.properties` with `coverage.xml` as report path (Task 2).
- Produces: `task sonar` command; documented in Task 4.

The "tests" for this task are behavioural checks of the task itself: precondition failures and a dry run. They are written as commands with expected output; run each and compare.

- [ ] **Step 1: Confirm the task does not exist yet (RED)**

Run: `task sonar; echo "exit=$?"`
Expected: an error like `task: Task "sonar" does not exist` and non-zero exit.

- [ ] **Step 2: Add the task**

Insert into `taskfile.yaml` after the `test-js-watch` task:

```yaml
  sonar:
    desc: Run tests with coverage and upload a SonarQube analysis of src/ (needs Docker and SONAR_TOKEN in .env)
    dotenv: [".env"]
    vars:
      SCANNER_IMAGE: sonarsource/sonar-scanner-cli:12.1.0.3233_8.0.1
    preconditions:
      - sh: test -n "$SONAR_TOKEN"
        msg: "SONAR_TOKEN is not set. Copy .env.example to .env and add the project analysis token (see CONTRIBUTING.md)."
      - sh: docker info > /dev/null 2>&1
        msg: "Docker is not available. Start the Docker daemon and retry."
    cmds:
      # Never scan a report left over from an earlier run.
      - rm -f coverage.xml
      # task dev installs non-editable; reinstall so coverage line numbers match src/.
      - uv pip install --no-deps --reinstall .
      # Failing tests or coverage below fail_under must not block the scan.
      - cmd: uv run --no-sync pytest tests -n auto --cov --cov-report=term --cov-report=xml:coverage.xml
        ignore_error: true
      - |
        if [ ! -f coverage.xml ]; then
          echo "coverage.xml was not written (pytest did not finish); not scanning."
          exit 1
        fi
      - >-
        docker run --rm
        -e SONAR_TOKEN
        -v "{{.ROOT_DIR}}:/usr/src:ro"
        {{.SCANNER_IMAGE}}
        -Dsonar.working.directory=/tmp/scannerwork
      - echo "Result -> https://sonar.cnbg-n.com/dashboard?id=django-crud-views%3Amain"
```

Notes:
- Task-level `dotenv` keeps the token scoped to this task. Task silently skips a missing dotenv file, so the precondition is what reports a missing token.
- Tasks run in the taskfile's directory by default, so relative paths (`coverage.xml`, `.`) are the repo root.

- [ ] **Step 3: Verify the task is listed**

Run: `task --list | grep sonar`
Expected: one line `* sonar:  Run tests with coverage and upload ...`.

- [ ] **Step 4: Precondition — missing token (GREEN for Review Focus 1)**

With no `.env` present:

Run: `env -u SONAR_TOKEN task sonar; echo "exit=$?"`
Expected: `task: SONAR_TOKEN is not set. Copy .env.example to .env ...` and non-zero exit. Nothing is installed, no pytest output appears (confirms preconditions run before cmds).

- [ ] **Step 5: Precondition — empty token from `.env`**

```bash
cp .env.example .env
env -u SONAR_TOKEN task sonar; echo "exit=$?"
rm .env
```
Expected: same `SONAR_TOKEN is not set` message and non-zero exit (the example's `SONAR_TOKEN=` is empty). Confirm `.env` is removed afterwards: `test -e .env || echo removed`.

- [ ] **Step 6: Dry run with a dummy token, from a subdirectory (Review Focus 2, 4, 5)**

```bash
(cd src && SONAR_TOKEN=dummy task --dry sonar)
```
Expected output, in order: `rm -f coverage.xml`, `uv pip install --no-deps --reinstall .`, the `uv run --no-sync pytest ...` line, the `if [ ! -f coverage.xml ]` block, a `docker run --rm -e SONAR_TOKEN -v "/home/.../django-crud-views:/usr/src:ro" sonarsource/sonar-scanner-cli:12.1.0.3233_8.0.1 -Dsonar.working.directory=/tmp/scannerwork` line whose mount path is the **repo root** (not `.../src`), and the echo. The literal string `dummy` must **not** appear anywhere in the output (token passed by name only). If Docker is stopped, a non-dry `task sonar` must fail with `Docker is not available` before any cmd runs — check with `systemctl is-active docker` and only test this if Docker is already stopped; do not stop the user's Docker.

- [ ] **Step 7: Stale-report guard (Review Focus 3)**

Simulate pytest not producing a report by running just the guard block with no file:

```bash
cd "$(git rev-parse --show-toplevel)"
cp coverage.xml /tmp/claude-cov-backup.xml 2>/dev/null || true
rm -f coverage.xml
sh -c 'if [ ! -f coverage.xml ]; then echo "coverage.xml was not written (pytest did not finish); not scanning."; exit 1; fi'; echo "exit=$?"
mv /tmp/claude-cov-backup.xml coverage.xml 2>/dev/null || true
```
Expected: the message and `exit=1`.

- [ ] **Step 8: Verify the install + test part end to end (no upload)**

Run the three local steps exactly as the task will:

```bash
rm -f coverage.xml && uv pip install --no-deps --reinstall . && uv run --no-sync pytest tests -n auto --cov --cov-report=term --cov-report=xml:coverage.xml; echo "pytest-exit=$?"; grep -m2 -o 'filename="[^"]*"' coverage.xml
```
Expected: test summary (baseline at time of writing: all passing, total coverage ≥ 88 %), and `filename="src/crud_views/__init__.py"`-style paths starting with `src/`. Record the `TOTAL` coverage percentage — Task 5 compares against it.

- [ ] **Step 9: Lint YAML indirectly and confirm other tasks still resolve**

Run: `task --list > /dev/null && echo ok; task --dry test-js`
Expected: `ok` and the existing test-js commands printed (the file still parses; nothing else changed).

- [ ] **Step 10: Leak check, then commit**

```bash
git add taskfile.yaml
git commit -m "chore(sonar): add task sonar (coverage + dockerised sonar-scanner)"
```

---

### Task 4: Document the maintainer workflow

**Files:**
- Modify: `CONTRIBUTING.md` — insert a new section between `## Commits and pull requests` and `## Reporting bugs and requesting features`.

**Interfaces:**
- Consumes: `task sonar` (Task 3), `.env.example` (Task 1), project key/host (Task 2).
- Produces: nothing consumed later.

- [ ] **Step 1: Insert the section**

````markdown
## SonarQube analysis (maintainers)

The package sources (`src/`) are analysed on [SonarQube](https://sonar.cnbg-n.com) as project
`django-crud-views:main`. The analysis runs locally; it needs Docker and a token.

One-time setup:

1. On the SonarQube server, generate a project analysis token for `django-crud-views:main`
   (My Account → Security → Generate Token).
2. `cp .env.example .env` and set `SONAR_TOKEN` in `.env`. The file is gitignored — never commit it.

Run:

```bash
task sonar
```

This reinstalls the package into `.venv`, runs the test suite with coverage (writing `coverage.xml`), and runs the
`sonar-scanner-cli` Docker image against the repository, mounted read-only. Failing tests or coverage below the
threshold do not abort the scan. The configuration lives in `sonar-project.properties`.
````

- [ ] **Step 2: Verify placement and rendering**

Run: `grep -n '^## ' CONTRIBUTING.md`
Expected: `## SonarQube analysis (maintainers)` appears after `## Commits and pull requests` and before `## Reporting bugs and requesting features`. Open the file and confirm the nested ```` ```bash ```` block is closed and the following heading is not swallowed.

- [ ] **Step 3: Leak check, then commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs(contributing): document task sonar for maintainers"
```

---

### Task 5: First real scan, verification, PR

This task needs a token only the user can provide. **Stop and hand over to the user** at Step 1.

**Files:** none changed unless Step 4 finds the git ownership issue (then `taskfile.yaml`).

- [ ] **Step 1: User checkpoint**

Tell the user, verbatim in substance:
> Ready for the first real scan. Please (1) create the project on https://sonar.cnbg-n.com with key `django-crud-views:main` and name `django-crud-views` if it does not exist, (2) generate a project analysis token for it, (3) run `cp .env.example .env` and put the token into `.env` yourself. Don't paste the token here. Tell me when done — or run `! task sonar` yourself.

Wait for the user's confirmation. Do not read `.env`.

- [ ] **Step 2: Run the scan and capture the log**

Run: `task sonar 2>&1 | tee "$SCRATCH/sonar-run.log" | tail -40`, where `$SCRATCH` is your session scratchpad directory (or any directory outside the repo).
Expected at the end: `EXECUTION SUCCESS` and the `Result -> ...` line.

- [ ] **Step 3: Check the log for coverage and config problems**

```bash
LOG="$SCRATCH/sonar-run.log"
grep -n -i 'cannot resolve the file path\|could not resolve\|coverage report' "$LOG"
grep -n -i 'project key\|projectKey\|Project configuration\|scm\|blame' "$LOG" | head -20
grep -n 'sqa_\|sqp_\|squ_' "$LOG"; echo "token-in-log-exit=$?"
```
Expected: a line saying the coverage report `coverage.xml` was parsed, **no** `Cannot resolve the file path` lines; key `django-crud-views:main`; SCM provider git detected with blame info; `token-in-log-exit=1` (no token-shaped strings in the log).

- [ ] **Step 4: If SCM/git failed, fix it in the task (never disable SCM)**

Work down this ladder only as far as needed; rerun Steps 2–3 after each change.

a. Log shows a git **ownership** problem ("dubious ownership", "not owned by current user", repository not
   recognised): add `--user "$(id -u):$(id -g)"` after `--rm` in the `docker run` of `taskfile.yaml`. Commit:

   ```bash
   git add taskfile.yaml
   git commit -m "fix(sonar): run scanner as host user so git blame works on the mounted repo"
   ```

b. Log shows a **read-only file system** error on `.git/...` (JGit touching `.git/index` during blame): remove `:ro`
   from the mount (`-v "{{.ROOT_DIR}}:/usr/src"`). This is safe because the scanner work directory is already
   `/tmp/scannerwork` inside the container. It amends the spec's "mounted read-only" decision, so update the spec's
   scan step and CONTRIBUTING.md ("mounted read-only" → "mounted into the container") in the same commit:

   ```bash
   git add taskfile.yaml CONTRIBUTING.md superpowers/specs/2026-09-28-sonarqube-local-scan-design.md
   git commit -m "fix(sonar): mount the repo read-write; git blame needs to write .git/index (amends spec)"
   ```

c. Anything else SCM-related: stop and report the exact log lines to the user. Do **not** add
   `sonar.scm.disabled=true`.

- [ ] **Step 5: Dashboard verification (with the user)**

Ask the user to open `https://sonar.cnbg-n.com/dashboard?id=django-crud-views%3Amain` and confirm:
1. name `django-crud-views`, key `django-crud-views:main`;
2. overall coverage is within ~2 points of the Task 3 Step 8 `TOTAL` (Sonar computes coverage for Python only here, JS is excluded, migrations are excluded; small differences come from Sonar's own line counting). A gap > 5 points, or 0 %, means paths did not match — investigate before continuing;
3. no files under `migrations/` in Code → `src`;
4. the 5 JS files are listed with no coverage requirement.

- [ ] **Step 6: Working tree is clean**

Run: `git status --porcelain`
Expected: empty (`coverage.xml`, `.coverage`, `.env` are ignored; no `.scannerwork` on the host).

- [ ] **Step 7: Final leak check over the whole branch**

Run the leak check command. Expected: no output. Also `git diff main --stat` should list only: `.gitignore`, `.env.example`, `sonar-project.properties`, `taskfile.yaml`, `CONTRIBUTING.md`, the spec and this plan.

- [ ] **Step 8: Push and open the PR**

```bash
git push -u origin feature/sonarqube-local-scan
gh pr create --base main --title "chore: local SonarQube analysis (task sonar)" --body "$(cat <<'EOF'
Adds a local SonarQube analysis of `src/` against https://sonar.cnbg-n.com (project `django-crud-views:main`).

- `sonar-project.properties`: project configuration (sources `src/`, tests `tests/`, migrations excluded, JS excluded from coverage, Python coverage from `coverage.xml`)
- `task sonar`: reinstall, pytest with coverage, dockerised `sonar-scanner-cli` (pinned), repo mounted read-only
- `.env.example` + `.gitignore`: token stays local
- CONTRIBUTING.md: maintainer instructions

GitHub Actions integration is a later phase.

Spec: superpowers/specs/2026-09-28-sonarqube-local-scan-design.md
EOF
)"
```

Then follow the project PR lifecycle: wait for CI (`gh pr checks --watch`), and also query check-runs via the API before merging because `gh pr checks` omits codecov (`gh api repos/jacob-consulting/django-crud-views/commits/$(git rev-parse HEAD)/check-runs --jq '.check_runs[] | [.name,.conclusion] | @tsv'`). Fix any ruff findings. **Ask the user before squash-merging.**
