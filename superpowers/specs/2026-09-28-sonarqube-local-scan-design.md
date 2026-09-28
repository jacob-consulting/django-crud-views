# SonarQube analysis — local scan (phase 1)

Date: 2026-09-28
Status: approved design, pending implementation plan

## Goal

Maintainers can run a SonarQube analysis of the package sources from their machine with one command,
`task sonar`, against the SonarQube server at `https://sonar.cnbg-n.com`. The scan includes Python coverage
produced by the test suite in the same run.

Success means:

- the project appears on the server as key `django-crud-views:main`, name `django-crud-views`;
- Python coverage on the dashboard matches the local pytest-cov total (JS excluded, see below);
- the scanner log contains no unresolved coverage file paths.

## Scope

In scope:

- analysis of `src/` (all five apps: Python, JS, templates, CSS);
- `tests/` registered as test sources;
- Python coverage from `pytest --cov`;
- local execution only.

Out of scope (later phases or separate decisions):

- GitHub Actions integration;
- JS coverage (Vitest has no coverage reporter configured);
- `examples/`;
- Quality Gate / Quality Profile configuration on the server;
- a CHANGELOG entry (maintainer tooling, no package change).

## Decisions

| Topic | Decision | Reason |
|---|---|---|
| Non-Python files in `src/` | Analysed; JS excluded from coverage only | Keeps findings for the 5 JS files without a permanent 0 % coverage drag |
| Migrations | Excluded from analysis | Generated code |
| Token | Project analysis token for `django-crud-views:main`, project created manually on the server | Smallest blast radius if leaked; no dependency on project-creation rights |
| Scanner | `sonarsource/sonar-scanner-cli` Docker image, pinned tag | Docker is already required locally; no package dependency; same scanner the official GitHub Action uses later |
| Configuration source | `sonar-project.properties` only; no `-D` overrides for key, name, host, paths | One place to read the effective configuration; reusable unchanged in CI |
| Coverage report location | `coverage.xml` at repo root | Already gitignored, already produced for Codecov, paths already `src/...` |
| SCM | Enabled (scanner default) | Blame data and new-code detection |

## Components

### `sonar-project.properties` (new, repo root)

```properties
sonar.projectKey=django-crud-views:main
sonar.projectName=django-crud-views
sonar.host.url=https://sonar.cnbg-n.com

sonar.sources=src
sonar.tests=tests
sonar.exclusions=**/migrations/**
# Vitest writes no coverage report yet; JS is analysed but not counted for coverage.
sonar.coverage.exclusions=**/*.js

sonar.python.version=3.12,3.13,3.14
sonar.python.coverage.reportPaths=coverage.xml
sonar.sourceEncoding=UTF-8
```

Values are written without quotes. Comments are English.

### `.env.example` (new) and `.gitignore`

`.env.example` contains only a placeholder and a one-line pointer to where the token comes from:

```
# Project analysis token for django-crud-views:main (SonarQube: My Account -> Security)
SONAR_TOKEN=
```

`.gitignore` gains `.env` and `.scannerwork/`. The `.env` entry must land before any token is written to disk.

### `task sonar` (new, `taskfile.yaml`)

The taskfile loads `.env` via `dotenv: [".env"]` (missing file is tolerated by Task).

Steps:

1. **Precondition** — `SONAR_TOKEN` is non-empty; otherwise fail with a message pointing to `.env.example`.
2. **Refresh install** — `uv pip install --no-deps --reinstall .`. `task dev` installs the package non-editable, so
   coverage measures the copy in `.venv/.../site-packages` and `[tool.coverage.paths]` maps file names back to
   `src/`. Line numbers still come from the installed copy; reinstalling guarantees they match what the scanner
   reads from `src/`.
3. **Tests with coverage** — `uv run pytest tests -n auto --cov --cov-report=term --cov-report=xml:coverage.xml`,
   `ignore_error: true`. A red test or coverage below `fail_under = 88` must not prevent the scan; the report is
   still meaningful.
4. **Scan** —
   ```
   docker run --rm -e SONAR_TOKEN -v "{{.ROOT_DIR}}:/usr/src:ro" \
     sonarsource/sonar-scanner-cli:12.1.0.3233_8.0.1 \
     -Dsonar.working.directory=/tmp/scannerwork
   ```
   The repo is mounted read-only; the scanner's work directory lives inside the container. The only `-D` is the
   work directory, which is an execution detail of the read-only mount, not project configuration.
5. **Output** — print `https://sonar.cnbg-n.com/dashboard?id=django-crud-views:main`.

### `CONTRIBUTING.md`

A short maintainer section: one-time setup (create project and token on the server, `cp .env.example .env`,
paste token), then `task sonar`. States that Docker is required and that tests failing does not abort the scan.

## Risks and open verification points

- **Git in the container.** With SCM enabled the scanner reads `.git` from the read-only mount. If the container
  user's UID differs from the host owner, git may refuse the repository ("dubious ownership"). Verified on the
  first real scan. Remedy stays in the task (e.g. `--user "$(id -u):$(id -g)"` or a `safe.directory` setting),
  not `sonar.scm.disabled=true`.
- **Scanner image tag.** `12.1.0.3233_8.0.1` is known to work against the server (version 26.5.0). Bump
  deliberately, not implicitly via `latest`.
- **Branch-shaped key.** The `:main` suffix encodes a branch in the project key. The GitHub Actions phase must
  decide how pull-request scans are keyed; that depends on the server edition, which was not visible without
  authentication.

## Verification

Done means all of the following, observed on a real scan with a real token:

1. `task sonar` completes; scanner reports `EXECUTION SUCCESS`.
2. Scanner log has no `Cannot resolve the file path` warnings for `coverage.xml`.
3. Dashboard shows key `django-crud-views:main`, name `django-crud-views`.
4. Dashboard Python coverage is within a small margin of the local `--cov-report=term` total.
5. Migrations do not appear among analysed files; JS files appear with findings but without coverage.
6. `git status` after the run shows no new untracked files except the gitignored `coverage.xml` / `.coverage`.
7. `git grep` over the diff finds no reference to other local projects or their paths.
