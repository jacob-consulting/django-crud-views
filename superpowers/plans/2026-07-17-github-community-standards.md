# GitHub Community Standards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the five missing community-health files so the GitHub `/community` checklist is fully green.

**Architecture:** Seven new documentation files — three prose files at repo root (Code of Conduct, Contributing, Security) and four templates under `.github/` (three YAML issue forms + a Markdown PR template). No package code. Files are independent except by hyperlink.

**Tech Stack:** Markdown, GitHub issue-forms YAML schema. Repo uses uv + Taskfile, ruff, pytest, nox, conventional commits, squash-merge PRs.

## Global Constraints

- Maintainer contact: `alexander.jacob@jacob-consulting.de`.
- Repo: `jacob-consulting/django-crud-views`; docs at `https://django-crud-views.readthedocs.io/en/latest/`.
- Current version `0.16.0` → supported line is `0.16.x`.
- Conventional-commit messages; commit with explicit pathspecs (never `git add -A` — an unrelated modified file `superpowers/prompts/2027-07-17-object-detail-per-view.md` lives in the working tree and must NOT be committed).
- Do NOT change repo settings (Description and private vulnerability reporting are already set) or mkdocs nav.
- Line-wrap prose reasonably (~100 cols); no ruff/line-length rule applies to Markdown/YAML here.

---

### Task 1: Code of Conduct + Security policy

**Files:**
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`

**Interfaces:**
- Produces: `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1, contact filled) and `SECURITY.md` (linked from CONTRIBUTING in Task 2 and from `.github/ISSUE_TEMPLATE/config.yml` in Task 3 via `.../security/policy`).

- [ ] **Step 1: Create `CODE_OF_CONDUCT.md`**

Write this exact content (Contributor Covenant v2.1, enforcement contact filled in):

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, caste, color, religion, or sexual
identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the overall
  community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or advances of
  any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email address,
  without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
alexander.jacob@jacob-consulting.de.
All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining
the consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction

**Community Impact**: Use of inappropriate language or other behavior deemed
unprofessional or unwelcome in the community.

**Consequence**: A private, written warning from community leaders, providing
clarity around the nature of the violation and an explanation of why the
behavior was inappropriate. A public apology may be requested.

### 2. Warning

**Community Impact**: A violation through a single incident or series of
actions.

**Consequence**: A warning with consequences for continued behavior. No
interaction with the people involved, including unsolicited interaction with
those enforcing the Code of Conduct, for a specified period of time. This
includes avoiding interactions in community spaces as well as external channels
like social media. Violating these terms may lead to a temporary or permanent
ban.

### 3. Temporary Ban

**Community Impact**: A serious violation of community standards, including
sustained inappropriate behavior.

**Consequence**: A temporary ban from any sort of interaction or public
communication with the community for a specified period of time. No public or
private interaction with the people involved, including unsolicited interaction
with those enforcing the Code of Conduct, is allowed during this period.
Violating these terms may lead to a permanent ban.

### 4. Permanent Ban

**Community Impact**: Demonstrating a pattern of violation of community
standards, including sustained inappropriate behavior, harassment of an
individual, or aggression toward or disparagement of classes of individuals.

**Consequence**: A permanent ban from any sort of public interaction within the
community.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.1, available at
[https://www.contributor-covenant.org/version/2/1/code_of_conduct.html][v2.1].

Community Impact Guidelines were inspired by
[Mozilla's code of conduct enforcement ladder][Mozilla CoC].

For answers to common questions about this code of conduct, see the FAQ at
[https://www.contributor-covenant.org/faq][FAQ]. Translations are available at
[https://www.contributor-covenant.org/translations][translations].

[homepage]: https://www.contributor-covenant.org
[v2.1]: https://www.contributor-covenant.org/version/2/1/code_of_conduct.html
[Mozilla CoC]: https://github.com/mozilla/diversity
[FAQ]: https://www.contributor-covenant.org/faq
[translations]: https://www.contributor-covenant.org/translations
```

- [ ] **Step 2: Create `SECURITY.md`**

Write this exact content:

```markdown
# Security Policy

## Supported Versions

`django-crud-views` is pre-1.0. Only the latest released minor version receives
security fixes. Please upgrade to the latest release before reporting a problem.

| Version | Supported          |
| ------- | ------------------ |
| 0.16.x  | :white_check_mark: |
| < 0.16  | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report a vulnerability privately using GitHub's
[private vulnerability reporting](https://github.com/jacob-consulting/django-crud-views/security/advisories/new)
(the "Report a vulnerability" button on the repository's **Security** tab).

If you cannot use GitHub's private reporting, email
**alexander.jacob@jacob-consulting.de** instead.

Please include, as far as you can:

- a description of the vulnerability and its impact,
- the affected version(s) and, if relevant, which app (`crud_views`,
  `crud_views_workflow`, `crud_views_polymorphic`, `crud_views_guardian`),
- steps to reproduce or a proof of concept.

We aim to acknowledge reports within a few business days and will keep you
informed as we work on a fix. Once a fix is released, we are happy to credit
reporters who wish to be named.
```

- [ ] **Step 3: Verify both files exist and are well-formed**

Run:
```bash
ls -1 CODE_OF_CONDUCT.md SECURITY.md
grep -c "alexander.jacob@jacob-consulting.de" CODE_OF_CONDUCT.md SECURITY.md
grep -n "0.16.x" SECURITY.md
```
Expected: both files listed; the email appears once in each file; the `0.16.x` row is present.

- [ ] **Step 4: Commit**

```bash
git add CODE_OF_CONDUCT.md SECURITY.md
git commit -m "docs: add Code of Conduct and Security policy"
```

---

### Task 2: Contributing guide

**Files:**
- Create: `CONTRIBUTING.md`

**Interfaces:**
- Consumes: links to `docs/development/index.md`, `CODE_OF_CONDUCT.md` (Task 1), `CHANGELOG.md`, the issue tracker.
- Produces: `CONTRIBUTING.md` referenced by the PR template (Task 3) implicitly.

- [ ] **Step 1: Create `CONTRIBUTING.md`**

Write this exact content:

```markdown
# Contributing to django-crud-views

Thanks for your interest in improving `django-crud-views`! This guide covers how
to set up the project, make a change, and open a pull request.

By participating in this project you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Getting started

Development setup (uv + Taskfile) is documented in the
[Development guide](https://django-crud-views.readthedocs.io/en/latest/development/)
(source: `docs/development/index.md`). In short:

```bash
git clone git@github.com:jacob-consulting/django-crud-views.git
cd django-crud-views
task dev
```

## Development workflow

1. Create a branch off `main`.
2. Make your change following the existing patterns. Write tests first (this
   project follows test-driven development).
3. Run the tests:
   - quick: `cd tests && pytest`
   - full matrix (Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0): `task test`
4. Format and lint before committing:
   - `task format` (ruff format)
   - `task check` (ruff check --fix)
5. Add an entry under `## Unreleased` in `CHANGELOG.md` describing your change.

## Commits and pull requests

- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit
  messages (e.g. `fix:`, `feat:`, `docs:`, `refactor:`).
- Keep pull requests focused; a PR should do one thing.
- Open your PR against `main`. Continuous integration must pass (lint, docs, and
  the full test matrix).
- A maintainer will review and **squash-merge** your PR.

## Reporting bugs and requesting features

Please use the [issue tracker](https://github.com/jacob-consulting/django-crud-views/issues)
and pick the appropriate template (Bug report or Feature request).

For security vulnerabilities, do **not** open a public issue — see our
[Security Policy](SECURITY.md).
```

- [ ] **Step 2: Verify the file and its links**

Run:
```bash
ls -1 CONTRIBUTING.md
grep -nE "CODE_OF_CONDUCT.md|SECURITY.md|CHANGELOG|development/|issues" CONTRIBUTING.md
test -f CODE_OF_CONDUCT.md && test -f docs/development/index.md && echo "link targets exist"
```
Expected: file listed; the internal links are present; link targets exist on disk.

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add contributing guide"
```

---

### Task 3: Issue forms + PR template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

**Interfaces:**
- Consumes: the readthedocs URL and the `.../security/policy` URL for `config.yml` contact links.
- Produces: the issue-template chooser and PR template GitHub renders on new issues/PRs.

- [ ] **Step 1: Create `.github/ISSUE_TEMPLATE/bug_report.yml`**

Write this exact content:

```yaml
name: Bug report
description: Report a problem with django-crud-views
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to file a bug report. Please fill in the
        fields below so we can reproduce and fix the problem quickly.
  - type: input
    id: cv-version
    attributes:
      label: django-crud-views version
      placeholder: "0.16.0"
    validations:
      required: true
  - type: input
    id: django-version
    attributes:
      label: Django version
      placeholder: "5.2"
    validations:
      required: true
  - type: input
    id: python-version
    attributes:
      label: Python version
      placeholder: "3.13"
    validations:
      required: true
  - type: dropdown
    id: affected-app
    attributes:
      label: Affected app
      options:
        - crud_views (core)
        - crud_views_workflow
        - crud_views_polymorphic
        - crud_views_guardian
        - unsure
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What went wrong?
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      description: A minimal, reproducible example is ideal.
    validations:
      required: true
  - type: textarea
    id: expected-actual
    attributes:
      label: Expected vs. actual behavior
    validations:
      required: true
```

- [ ] **Step 2: Create `.github/ISSUE_TEMPLATE/feature_request.yml`**

Write this exact content:

```yaml
name: Feature request
description: Suggest an idea or improvement for django-crud-views
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem / motivation
      description: What problem would this solve? What are you trying to do?
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: What would you like to happen?
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
    validations:
      required: false
  - type: dropdown
    id: affected-area
    attributes:
      label: Affected area
      options:
        - crud_views (core)
        - crud_views_workflow
        - crud_views_polymorphic
        - crud_views_guardian
        - unsure
    validations:
      required: false
```

- [ ] **Step 3: Create `.github/ISSUE_TEMPLATE/config.yml`**

Write this exact content:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://django-crud-views.readthedocs.io/en/latest/
    about: Read the docs before opening an issue — your question may be answered there.
  - name: Report a security vulnerability
    url: https://github.com/jacob-consulting/django-crud-views/security/policy
    about: Please report security issues privately, not as a public issue.
```

- [ ] **Step 4: Create `.github/PULL_REQUEST_TEMPLATE.md`**

Write this exact content:

```markdown
## Summary

<!-- What does this PR do, and why? -->

## Related issue

<!-- e.g. Closes #123 -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor / internal change
- [ ] Chore / tooling

## Checklist

- [ ] Tests pass (`cd tests && pytest`)
- [ ] `task format` and `task check` are clean
- [ ] `CHANGELOG.md` has an entry under `## Unreleased`
- [ ] Documentation updated (if behavior changed)
```

- [ ] **Step 5: Verify all four files parse and exist**

Run:
```bash
ls -1 .github/ISSUE_TEMPLATE/bug_report.yml .github/ISSUE_TEMPLATE/feature_request.yml .github/ISSUE_TEMPLATE/config.yml .github/PULL_REQUEST_TEMPLATE.md
for f in .github/ISSUE_TEMPLATE/bug_report.yml .github/ISSUE_TEMPLATE/feature_request.yml .github/ISSUE_TEMPLATE/config.yml; do
  python -c "import yaml,sys; yaml.safe_load(open('$f')); print('OK', '$f')"
done
```
Expected: all four files listed; each of the three YAML files prints `OK`.

- [ ] **Step 6: Verify issue-forms required keys**

Run:
```bash
python - <<'PY'
import yaml
for f in ("bug_report", "feature_request"):
    d = yaml.safe_load(open(f".github/ISSUE_TEMPLATE/{f}.yml"))
    assert "name" in d and "body" in d, f
    assert all("type" in item for item in d["body"]), f
    print("form ok:", f)
PY
```
Expected: `form ok: bug_report` and `form ok: feature_request`.

- [ ] **Step 7: Commit**

```bash
git add .github/ISSUE_TEMPLATE/bug_report.yml .github/ISSUE_TEMPLATE/feature_request.yml .github/ISSUE_TEMPLATE/config.yml .github/PULL_REQUEST_TEMPLATE.md
git commit -m "docs: add issue forms and pull request template"
```

---

### Task 4: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Confirm all seven files are present**

Run:
```bash
ls -1 CODE_OF_CONDUCT.md CONTRIBUTING.md SECURITY.md \
  .github/PULL_REQUEST_TEMPLATE.md \
  .github/ISSUE_TEMPLATE/bug_report.yml \
  .github/ISSUE_TEMPLATE/feature_request.yml \
  .github/ISSUE_TEMPLATE/config.yml
```
Expected: all seven paths printed, none missing.

- [ ] **Step 2: Internal-link sanity check**

Run:
```bash
grep -q "CODE_OF_CONDUCT.md" CONTRIBUTING.md && grep -q "SECURITY.md" CONTRIBUTING.md && echo "CONTRIBUTING links OK"
grep -q "security/advisories/new" SECURITY.md && echo "SECURITY private-report link OK"
```
Expected: both `OK` lines print.

- [ ] **Step 3: Packaging sanity (new root files don't break the build)**

Run:
```bash
task build
```
Expected: build succeeds (wheel + sdist produced). The new root Markdown files are not source and should not alter the wheel's Python contents.

- [ ] **Step 4: Confirm the unrelated working-tree file was never staged**

Run:
```bash
git status --short
git log --oneline -4
```
Expected: `superpowers/prompts/2027-07-17-object-detail-per-view.md` still shows as modified/unstaged (untouched); the last commits are Tasks 1–3, none referencing that file.

**Acceptance (post-merge, cannot assert locally):** after this branch merges to
`main`, the GitHub `/community` page shows all eight rows green (Code of conduct,
Contributing, Security policy, Issue templates, Pull request template now
satisfied).

---

## Self-Review

**Spec coverage:**
- CODE_OF_CONDUCT.md → Task 1. ✓
- SECURITY.md → Task 1. ✓
- CONTRIBUTING.md (DRY, links docs/development) → Task 2. ✓
- Issue forms (bug/feature/config, YAML) → Task 3. ✓
- PR template → Task 3. ✓
- Verification (YAML parse, links, build, community-page acceptance) → Task 3 steps 5–6 + Task 4. ✓
- Out-of-scope items (settings, mkdocs nav) → not touched. ✓

**Placeholder scan:** Full content is inline for every file, including the complete
Contributor Covenant v2.1 text with the contact filled in. No TBD/TODO. ✓

**Consistency:** Version `0.16.x` used in SECURITY.md matches Global Constraints;
the four app names are identical across bug_report.yml, feature_request.yml, and
SECURITY.md; the `.../security/policy` URL in config.yml and the
`.../security/advisories/new` URL in SECURITY.md are both valid GitHub security
endpoints for this repo. Commit messages use conventional-commit `docs:` prefix
throughout. Explicit pathspecs everywhere (no `git add -A`). ✓
