# Ruff upgrade to latest with an explicit rule set — design spec

Date: 2026-07-27
Status: approved design, pending implementation plan

## Goal

Stop riding ruff's default rule set. Adopt ruff 0.16.x with an **explicit**
`[tool.ruff.lint] select`, so that upgrading ruff becomes a dependency bump rather than
a behaviour change, and unify the four places that currently disagree about which ruff
version this project uses.

## Background

The pin `ruff==0.15.21` landed in PR #100 (commit `8a7d599`), replacing a bare `ruff`.
It was a *version* pin, not a rule-strictness setting: the project has never had a
`[tool.ruff.lint]` section and has always used whatever Astral shipped as the default
selection.

Ruff 0.16.0 expanded that default from **59 enabled rules to 413**. The pin froze the
old defaults; that is the entire reason the upgrade looked disruptive.

Version state before this change — four locations, three versions:

| Location | Version |
|---|---|
| `pyproject.toml` dev extra | `ruff==0.15.21` |
| `.github/workflows/lint.yml` | `ruff==0.15.21` |
| `.github/workflows/publish.yml` | `ruff==0.15.21` |
| `.pre-commit-config.yaml` | `rev: v0.15.2` |
| local `.venv` (observed) | `0.15.22` |

`ruff format --check` under 0.16.0 reports *377 files already formatted* — the
formatter is unaffected. **This work is lint-only, with zero reformatting churn.**

## Decisions

1. **Explicit `select`, floating version.** The rule set is fixed in config; the ruff
   version floats. Future ruff releases change nothing unless `select` is edited.
2. **Uniform rules across `src/`, `tests/`, `examples/`**, with a single deliberate
   exception: `RUF012` is ignored in `tests/`, `examples/` and generated migrations
   (see "The RUF012 exception").
3. **Rename `CrudViewsSettings.dict` → `as_dict`** to remove the annotation-shadowing
   hazard at its root rather than suppressing the rule.
4. **Single PR, phased commits** — mechanical changes isolated from judgment calls so
   review can focus on the latter.

## Configuration

```toml
[tool.ruff]
line-length = 120
extend-exclude = ["superpowers/**"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]
allowed-confusables = ["›"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["RUF012"]
"examples/**" = ["RUF012"]
"**/migrations/*" = ["RUF012"]
```

`allowed-confusables` whitelists the breadcrumb separator `›`, which `RUF001`/`RUF002`
otherwise flags in six places as a possible mis-typed `>`. It is the component's
deliberate separator, so the character is declared intentional once in config rather
than suppressed at each site. See commit C.

Families deliberately excluded, with the measured cost had they been included:
`S` (bandit) 1731 — dominated by `S101` assert-in-tests; `PL` (pylint) 827; `TRY` 42;
`PIE` 16; `FURB` 6; `BLE` 5; `PERF` 5.

Version unification:

| Location | After |
|---|---|
| `pyproject.toml` dev extra | `ruff>=0.16` |
| `.github/workflows/lint.yml` | `pip install 'ruff>=0.16'` |
| `.github/workflows/publish.yml` | `pip install 'ruff>=0.16'` |
| `.pre-commit-config.yaml` | `rev: v0.16.0` |

**Known constraint:** pre-commit's `rev:` must resolve to a concrete git tag and
therefore cannot float. It stays pinned and is advanced with `pre-commit autoupdate`.
This is the one location that can drift again; it is pinned deliberately rather than
appearing to float. Because `select` is explicit, a drifted pre-commit rev changes
which *bugs are fixed*, not which *rules apply*.

## The RUF012 exception

`RUF012` (mutable-class-default) produces 205 findings under a uniform rule set — 57%
of all manual work — and they land where the rule is worth least:

| Location | Count | Assessment |
|---|---|---|
| `tests/` | 97 | Test fixture classes; `ClassVar` annotations add noise, not safety. |
| `examples/` | 99 | Teaching code; annotations obscure the pattern being taught. |
| `src/**/migrations/` | 4 | Django-**generated**; hand annotations are lost on the next `makemigrations`. |
| real package code | 5 | Genuine. Kept. |

Ignoring it in the first three locations cuts manual work from 357 to 150 while
retaining every legitimate finding. The five kept hits are in
`crud_views/lib/conditional/group.py`, `crud_views/lib/views/card.py`,
`crud_views/lib/views/mixins.py`, `crud_views_workflow/lib/forms.py`,
`crud_views_workflow/models.py`.

This is the only per-file-ignore. Any future addition should clear a comparable bar:
the rule must be actively harmful or inapplicable in that tree, not merely tedious.

## Violation budget

Under the configuration above: **481 findings, 331 auto-fixable, 150 manual.**

| Tree | Total | Auto-fixable | Manual |
|---|---|---|---|
| `src/` | 361 | 227 | 134 |
| `tests/` | 89 | 76 | 13 |
| `examples/` | 31 | 28 | 3 |

Measured with ruff 0.16.0. Figures are a baseline for planning, not an acceptance
criterion — the acceptance criterion is `ruff check .` exiting clean.

## Code changes

### Commit A — configuration only

Add `[tool.ruff.lint] select` and `per-file-ignores`; unify the four version
locations. This commit alone turns CI red; it is not intended to stand on its own and
must not be merged independently.

### Commit B — autofixes

`ruff check --fix` with **no** `--unsafe-fixes`. 331 changes, dominated by
`UP006` PEP 585 annotations (92), `RUF100` unused-noqa (49), `I001` import sorting
(47) in `src/`, plus the `tests/`/`examples/` equivalents. Purely mechanical;
reviewable in bulk.

`--unsafe-fixes` is deliberately not used. The 83 hidden fixes are left for a future,
separately-reviewed change.

### Commit C — manual fixes in `src/` (134)

**Counts below are total findings per rule.** Several rules are partially auto-fixed by
commit B (ruff marks them `[-]`: a fix exists for some instances only), so these do not
sum to 134. The aggregate is authoritative; the implementation plan will re-measure
per-rule remainders against the post-commit-B tree.

Bulk mechanical-but-unautomated work:

| Rule | Findings | Nature |
|---|---|---|
| `UP035` deprecated-import | 55 | `typing.List` → `list` import cleanup; partially auto-fixed, remainder paired with the `UP006` changes. |
| `C408` unnecessary-collection-call | 40 | `dict()` → `{}`. Mechanical, individually trivial. |
| `B007` unused-loop-control-variable | 9 | Rename to `_`. |
| `SIM102`/`SIM108`/`SIM118`/`SIM212`/`SIM110`/… | ~24 | Local simplifications, one at a time. |
| `RUF022` unsorted-`__all__` | 6 | Sort. Touches public export order only. |
| `RUF012` mutable-class-default | 5 | Add `ClassVar[...]`. |
| `E501` line-too-long | 2 | Wrap at 120. |

Requiring individual judgment — every instance located:

| Rule | Location | Resolution |
|---|---|---|
| `B023` ×4 | `crud_views/checks.py:125–128` | Suppress with `# noqa: B023` + explanatory comment. **Not a defect:** `_walk` is defined at `:120` and invoked only at `:135` (recursive) and `:138`, both inside the same loop iteration; the closure never escapes, so late binding cannot be observed. Restructuring a recursive closure to satisfy a style rule carries more risk than the warning it silences. |
| `RUF002` ×4 | `crud_views/lib/breadcrumb.py:83` | **False positive — do not "fix".** All four are the `›` separator in the breadcrumb docstring, which is the component's deliberate, documented separator. Resolve in config, not in the docstring: add `allowed-confusables = ["›"]` under `[tool.ruff.lint]`. |
| `RUF013` ×3 | `lib/check.py:45`, `lib/view/base.py:185` (×2) | Genuine. Make `Optional` explicit (`X \| None`). Annotation-only. |
| `B904` ×2 | `lib/breadcrumb.py:226`, `lib/views/mixins.py:267` | `raise … from err` / `from None` inside `except`. Improves tracebacks; confirm the surfaced message is unchanged. |
| `B905` ×2 | `lib/breadcrumb.py:228`, `lib/view/base.py:461` | `zip(..., strict=)`. **Choose the value deliberately** — `strict=True` converts a silent truncation into a runtime error and is a genuine behaviour change. Inspect whether unequal lengths are reachable; prefer `strict=False` where truncation is intended and relied upon. |
| `RUF005` ×2 | `lib/formsets/formsets.py:91`, `lib/viewset/__init__.py:306` | Unpacking over concatenation. Equivalent. |
| `SIM105` ×1 | `lib/views/mixins.py:296` | `contextlib.suppress(KeyError)`. Only if it does not obscure intent. |

The `allowed-confusables` entry means the final `[tool.ruff.lint]` block is:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]
allowed-confusables = ["›"]
```

### Commit D — `settings.as_dict` rename

`src/crud_views/lib/settings.py` defines `@cached_property def dict(self)` (line 163)
while line 38 annotates `breadcrumb_prefix: List[Dict[str, Any]]`. `UP006` would
rewrite that to `dict[str, Any]`; under PEP 649 deferred annotation evaluation on
Python 3.14 the bare `dict` resolves to the class's own property rather than the
builtin, breaking the 3.14 matrix row.

`dict` is the only attribute on that class shadowing a builtin used in annotations
(verified by enumerating every class attribute and property).

Changes: rename the property to `as_dict`; update the sole call site
`src/crud_views/lib/context_processor.py:5`; apply `UP006`/`UP035` to the file.
Add a `## Unreleased` CHANGELOG entry recording the rename.

### Commit E — `tests/` and `examples/` manual fixes (16) and docs re-sync

Remaining manual items: `RUF059` unused-unpacked-variable (6), `RUF005` (3),
`E501` (2), `UP035` (2), `B011` assert-false (1), `B018` useless-expression
(1, `examples/bootstrap5/project/tests.py:72` — likely a dead assertion; inspect
rather than delete blindly), `C416` (1).

`examples/bootstrap5/test_docs_sync.py` requires 28 marked code blocks across 8 docs
pages to appear **verbatim** (whitespace-normalised, blank lines ignored) in their
referenced example source. Seven example files are mirrored this way:
`formsets/views.py`, `library/models.py`, `library/seed.py`, `library/urls.py`,
`library/views.py`, `nested/views.py`, `project/views.py`.

Every lint fix landing inside a mirrored region must be reflected in the corresponding
tutorial block in this same commit.

## Verification

- `cd tests && pytest` — full suite.
- `task test` — nox matrix, Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0. The 3.14 row
  is what would catch a regression of the annotation-shadowing hazard.
- `pytest examples/bootstrap5/test_docs_sync.py` — docs/examples parity.
- `ruff check .` and `ruff format --check .` clean.
- `pre-commit run --all-files` — confirms the pinned hook rev agrees with the config.

Commits B and C must not change behaviour. The only intentional behaviour changes in
this branch are the `as_dict` rename (D) and any `B905` `strict=True` decision (C);
both are called out in review and the CHANGELOG.

## Out of scope

- `--unsafe-fixes` (83 hidden fixes).
- Adopting `S`, `PL`, `TRY`, `PIE`, `FURB`, `BLE`, `PERF`.
- Any version bump or release. The `as_dict` rename is recorded under `## Unreleased`
  and ships with the next release.

## Rollout

Single branch `feature/ruff-0.16-explicit-select`, commits A–E in order. PR → wait for
CI → fix any ruff findings → squash-merge to `main` → wait for main CI, per project
convention.
