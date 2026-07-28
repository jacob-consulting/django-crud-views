# Coverage config: make Codecov measure `src/`

**Issue:** [#103](https://github.com/jacob-consulting/django-crud-views/issues/103)
**Date:** 2026-07-28
**Status:** approved, ready for planning

## Problem

The `[tool.coverage.*]` config in the root `pyproject.toml` has never taken effect. Codecov
has been tracking only the test suite — the reported ~99% project figure is `tests/`
measuring itself, and the package source has never been measured at all.

## Root cause

The issue that surfaced this names `relative_files = true` as "the load-bearing part" of the
fix. That is wrong, and the correction matters because it invalidates two of the three fixes
the issue proposes.

Coverage.py's relative directory follows the **process CWD**, not the location of the config
file. `noxfile.py` does `session.chdir("./tests")` before invoking pytest, which causes two
independent failures:

1. **No config is found.** Coverage looks for a config file in the CWD only — it does not
   walk up the tree. `tests/` contains none, so `source` and `fail_under` are both inert and
   a bare `--cov` measures every imported module, including `tests/`.
2. **`src/` paths are unmappable.** With the relative directory anchored to `tests/`, paths
   under `src/` cannot be made relative to it, so they stay absolute. Codecov resolves the
   relative `tests/` entries against the repo tree and silently discards the absolute ones.

### Empirically tested alternatives

Measured against coverage.py 7.15.2 with the package installed editable:

| Setup | Emitted filename | Codecov-mappable |
|---|---|---|
| `relative_files`, config in `tests/.coveragerc`, cwd=`tests/` | `home/alex/…/src/crud_views/checks.py` | no |
| `relative_files`, config in repo root via `--cov-config`, cwd=`tests/` | `home/alex/…/src/crud_views/checks.py` | no |
| `[paths]` remapping, cwd=`tests/` | `home/alex/…/src/crud_views/checks.py` | no |
| `relative_files`, **cwd=repo root** | `src/crud_views/checks.py` | **yes** |

The first two rows are the issue's preferred options 1 and 2. Both fail. Only running from
the repo root — the issue's option 3 — produces Codecov-mappable paths.

Running from the root also makes the existing root config live with no extra flags:
coverage discovers `pyproject.toml` in the CWD and applies `source` and `fail_under`. Also
confirmed: pytest-cov's `--cov-config` default of `.coveragerc` is special-cased by
coverage.py to mean "search the defaults", so `pyproject.toml` is found without passing
`--cov-config` explicitly.

### Role of `relative_files`

Not required for the filenames — running from the root already yields `src/…` without it.
It is still worth setting, because it empties the XML `<source>` element:

- without: `<source>/home/alex/projects/alex/django-crud-views</source>`
- with: `<source></source>`

That removes a machine-specific absolute prefix that Codecov's path-fixing would otherwise
have to guess past. The CWD is the fix; `relative_files` makes the result unambiguous.

## Changes

**`noxfile.py`** — remove `with session.chdir("./tests")` from the `tests` session and run
`pytest tests -n auto --cov --cov-report=term-missing`. The `examples` session keeps its own
`chdir` and is untouched.

**`pyproject.toml`**, `[tool.coverage.run]` — add `relative_files = true`; add the missing
`crud_views_guardian` and alphabetize `source` across all five packages in `src/`.

**`.github/workflows/tests.yml`** — `coverage.xml` is now written at the repo root, so the
upload step's `files: tests/coverage.xml` becomes `files: coverage.xml`.

**`CLAUDE.md`** — the documented quick loop moves to the repo root: `pytest tests`,
`pytest tests/test1/test_crud.py`, `pytest tests/test1/test_crud.py::test_name -v`.

Collapsing to a single working directory is part of the fix, not incidental tidying. The bug
exists because two CWDs were in play and the config matched only one of them; leaving
`cd tests && pytest` documented would keep the trap loaded for anyone running coverage
locally.

No `.gitignore` change is needed — the bare `.coverage` and `coverage.xml` patterns already
match at any depth.

## Measured impact

Full suite from the repo root, py3.12 / Django 5.2, src-only: **4429 statements, 268
missing, 94%**. All 868 tests pass, 1 skipped — identical to running from `tests/`, so the
CWD change breaks no conftest, xdist, or path behaviour.

| Package | Stmts | Miss | Cov |
|---|---:|---:|---:|
| `crud_views` | 3387 | 221 | 93.5% |
| `crud_views_guardian` | 264 | 27 | 89.8% |
| `crud_views_object_detail` | 382 | 9 | 97.6% |
| `crud_views_polymorphic` | 135 | 4 | 97.0% |
| `crud_views_workflow` | 261 | 7 | 97.3% |

`crud_views_guardian` — the package the `source` drift omitted — is the weakest of the five.
The drift hid the worst number.

## The gate

`fail_under` **stays at 88.** Measured coverage is 94%, leaving 6 points of headroom, and
this change corrects measurement rather than tightening policy; moving both at once would
make neither attributable. Note that 88 has never been enforced before this change — it
becomes a live gate on all 8 matrix rows here.

Nothing turns red on landing: this repo posts only `codecov/patch`, not `codecov/project`,
so the 99% → 94% move affects the badge and the Codecov UI only. The PR body must state
that the drop is a measurement correction, not a regression, since Codecov will also show a
wholesale change in the tracked file set as `tests/` leaves the report and `src/` enters it.

## Verification

1. `nox -s "tests-3.12(django='5.2')" -- --cov-report=xml`, then assert on the root
   `coverage.xml`: `<source></source>`, filenames beginning `src/`, zero occurrences of
   `filename="tests/`, `crud_views_guardian` present, and `fail_under` satisfied.
2. After CI, re-run the Codecov compare-API query used as evidence on #103 and confirm the
   tracked-file list contains `src/` paths rather than `Counter({'tests': 97})`.

## Out of scope

To be filed as follow-up issues, not fixed here:

- **Matrix rows clobber each other.** All three Django sessions write the same
  `coverage.xml` with no `--cov-append`, so only the last (Django 6.0 × py3.13) is uploaded.
  Now that `src/` is measured, version-gated `try/except ImportError` branches will read as
  uncovered. Deliberately deferred so the ~5-point measurement correction lands alone and
  attributable.
- **`crud_views_guardian` at 89.8%** — the weakest package, worth its own coverage work.
- **No `codecov.yml`.** Project and patch targets are inherited from Codecov's auto-defaults
  rather than declared in-repo.
