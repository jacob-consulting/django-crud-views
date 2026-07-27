# Development

This section describes how to setup the development environment and how to create themes and extensions.

## Requirements

You need these tools development:

- [uv](https://docs.astral.sh/uv/guides/install-python/)
- [taskfile](https://taskfile.dev/installation/)

## Setup

Set up your local development environment:

```bash
git clone git@github.com:jacob-consulting/django-crud-views.git
cd django-crud-views
task dev
```

## JS tests

The package's static JavaScript (`formset.js`, `modal.js`, `toggle.js`) has a
[Vitest](https://vitest.dev/) unit-test suite. It needs [Node.js](https://nodejs.org/) 20+:

```bash
task test-js
```

## Run example application

Now let's run the example application with the `bootstrap5` theme:

```bash
cd examples/bootstrap5
task run
```
> **Note:** This will run the migrations, seed demo data, and start the dev server. It adds a superuser with username `admin` and password `admin` (see `project/seeding.py`).

[Then open the app in your browser at http://localhost:8000](http://localhost:8000)

## Claude Code skill

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill for building with `django-crud-views`
is maintained in a separate repository: [jacob-consulting/skills](https://github.com/jacob-consulting/skills).
It is no longer bundled inside this repository.
