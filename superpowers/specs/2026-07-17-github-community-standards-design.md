# Meet GitHub Community Standards — Design

**Target:** https://github.com/jacob-consulting/django-crud-views/community
**Date:** 2026-07-17
**Status:** Approved (brainstorming complete)

## Context

GitHub's Community Standards checklist (the `/community` page) grades a repo on a
fixed set of community-health files. `django-crud-views` currently satisfies
three rows and is missing five. This work adds the five missing files/dirs so the
checklist is fully green. All items are documentation / repo-hygiene — no package
code changes, no runtime/semver impact.

## Ground-truth findings

Checklist status as of 2026-07-17:

| Standard | Status |
|----------|--------|
| Description | ✅ set — "Django CRUD Views" (verified via `gh repo view`) |
| README | ✅ `README.md` |
| License | ✅ `LICENSE` — MIT, © Jacob Consulting GmbH |
| Code of conduct | ❌ missing |
| Contributing | ❌ missing |
| Security policy | ❌ missing |
| Issue templates | ❌ missing (`.github/` has only `workflows/`) |
| Pull request template | ❌ missing |

Supporting facts:
- Maintainer contact: `alexander.jacob@jacob-consulting.de` (from `pyproject.toml`).
- **Private vulnerability reporting is already enabled** on the repo (verified via
  `gh api .../private-vulnerability-reporting` → `{"enabled":true}`), so the
  SECURITY.md "Report a vulnerability" flow works with no settings change.
- Existing contributor setup docs live at `docs/development/index.md` (uv, Taskfile,
  `task dev`, running the example). CONTRIBUTING links to these rather than
  duplicating them.
- Project conventions (from `CLAUDE.md`): conventional commits, `task format` /
  `task check` (ruff), TDD with pytest, nox matrix (Python 3.12/3.13/3.14 ×
  Django 4.2/5.2/6.0), PR → CI → squash-merge, CHANGELOG `## Unreleased` entries.
- Project URLs (from `pyproject.toml`): docs at readthedocs, issues/repo/changelog
  on GitHub.

No manual repo-settings work remains — both non-file checklist concerns
(Description, private reporting) are already satisfied.

## Scope

Add five community-health items: Code of Conduct, Contributing guide, Security
policy, Issue templates (YAML forms), Pull request template. Out of scope: mkdocs
nav changes, repo-settings changes (already done), any package code.

## Design

### 1. `CODE_OF_CONDUCT.md` (repo root)

Contributor Covenant **v2.1**, used verbatim from the official source, with the
enforcement-contact placeholder filled in as `alexander.jacob@jacob-consulting.de`.
v2.1 is the version GitHub's checklist recognizes. No wording changes beyond the
contact line.

### 2. `CONTRIBUTING.md` (repo root)

DRY — points to `docs/development/` for environment setup instead of repeating it.
Sections:
- **Getting started** — one line + link to `docs/development/index.md` (uv, Taskfile,
  `task dev`).
- **Development workflow** — branch off `main`; run tests (`cd tests && pytest`, or
  full matrix via `task test`); `task format` and `task check` before committing.
- **Commit & PR conventions** — conventional commits; TDD (test-first); keep the
  diff focused; add a `## Unreleased` entry to `CHANGELOG.md`; open a PR → CI must
  pass → maintainer squash-merges.
- **Reporting issues** — link to the issue tracker and the templates.
- **Code of Conduct** — link to `CODE_OF_CONDUCT.md`.

### 3. `SECURITY.md` (repo root)

- **Supported versions** — honest pre-1.0 policy: only the latest released minor
  (currently `0.16.x`) receives security fixes; users should upgrade before
  reporting. A small table: `0.16.x` ✅, `< 0.16` ❌.
- **Reporting** — primary channel GitHub Security tab → "Report a vulnerability"
  (private reporting, already enabled); email fallback
  `alexander.jacob@jacob-consulting.de`. Explicit "do not open a public issue for
  security problems." State a best-effort acknowledgement window (e.g. within a few
  business days) without a hard SLA.

### 4. `.github/ISSUE_TEMPLATE/` — YAML issue forms

- **`bug_report.yml`** — `name: Bug report`, `labels: [bug]`. Body fields:
  - `markdown` intro.
  - `input` **django-crud-views version** (required).
  - `input` **Django version** (required).
  - `input` **Python version** (required).
  - `dropdown` **Affected app** — options: `crud_views (core)`,
    `crud_views_workflow`, `crud_views_polymorphic`, `crud_views_guardian`,
    `unsure` (required).
  - `textarea` **Description** (required).
  - `textarea` **Steps to reproduce** (required).
  - `textarea` **Expected vs. actual behavior** (required).
- **`feature_request.yml`** — `name: Feature request`, `labels: [enhancement]`. Body:
  - `textarea` **Problem / motivation** (required).
  - `textarea` **Proposed solution** (required).
  - `textarea` **Alternatives considered** (optional).
  - `dropdown` **Affected area** (same options as bug, optional).
- **`config.yml`** — `blank_issues_enabled: false`; `contact_links`:
  - Documentation → `https://django-crud-views.readthedocs.io/en/latest/`.
  - Security policy → `https://github.com/jacob-consulting/django-crud-views/security/policy`
    (renders SECURITY.md; steers security reports away from public issues).

### 5. `.github/PULL_REQUEST_TEMPLATE.md`

Concise skeleton:
- **Summary** — what and why.
- **Related issue** — `Closes #`.
- **Type of change** — checkbox list (bug fix / feature / docs / refactor / chore).
- **Checklist** — tests pass (`cd tests && pytest`); `task format` + `task check`
  clean; `CHANGELOG.md` `## Unreleased` updated; docs updated if behavior changed.

## File structure

```
CODE_OF_CONDUCT.md                        (new, root)
CONTRIBUTING.md                           (new, root)
SECURITY.md                               (new, root)
.github/PULL_REQUEST_TEMPLATE.md          (new)
.github/ISSUE_TEMPLATE/bug_report.yml     (new)
.github/ISSUE_TEMPLATE/feature_request.yml(new)
.github/ISSUE_TEMPLATE/config.yml         (new)
```

Each file has one clear responsibility; none depends on another except by
hyperlink. Root placement puts the three prose files where GitHub surfaces them
most prominently, alongside `LICENSE`/`README`/`CHANGELOG`.

## Testing / verification

- **YAML validity** — each issue-form and `config.yml` parses as valid YAML and
  conforms to GitHub's issue-forms schema (required top-level keys present:
  `name`, `description`, `body`; each `body` item has a valid `type`). Verify by
  parsing locally (e.g. `python -c "import yaml, sys; yaml.safe_load(open(f))"`)
  for each file.
- **Link check** — internal links (CONTRIBUTING → docs/development, → CoC;
  SECURITY email; config.yml URLs) resolve to real targets.
- **Ground truth** — after merge to `main`, the GitHub `/community` page shows all
  eight rows green. (Cannot be asserted pre-merge; note as the acceptance check.)
- **No packaging regression** — new root files are not picked up by the hatchling
  build in a way that changes the wheel; confirm `task build` still succeeds and
  the wheel contents are unchanged apart from intended metadata.

## Out of scope

- mkdocs navigation changes (community-health files stay at root/`.github`).
- Repo-settings changes — Description and private vulnerability reporting are
  already in place.
- Any `src/` package code.
