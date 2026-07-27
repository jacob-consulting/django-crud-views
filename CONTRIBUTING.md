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
   - JS unit tests (requires Node 20+): `task test-js`
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
