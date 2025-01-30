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
## Run example application

Now let's run the example application with the `bootstrap5` theme:

```bash
cd examples/bootstrap5
task init
```
> **Note:** This will run the migrations and add a superuser with username `admin` and password `foobar4711`

[Then open the app in your browser at http://localhost:8000](http://localhost:8000)
