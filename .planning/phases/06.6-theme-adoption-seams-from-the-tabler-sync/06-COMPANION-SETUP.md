# Phase 06.6 companion baseline and evidence setup

## Current prerequisite: blocked

Read-only preflight on 2026-11-02 found the supplied source and interpreter, but
the companion interpreter cannot import `pytest`, `pytest_django`, or `xdist`.
Their distributions (`pytest`, `pytest-django`, `pytest-xdist`) are absent.
Task 06-02 therefore remains blocked before capture. At the final precondition
check, HEAD had also advanced externally to
`0b3baa896ef5b11aa010238c92d3bceb4663e337` (`chore: add allowed host`) and status
was clean. The executor issued no companion writes. Capture requires the pinned
HEAD; do not reset this newer user work to satisfy that check. The orchestrator
must reconcile the changed source prerequisite before capture resumes.
No packages were installed,
no companion files were edited, and no baseline JSON was manufactured.
Plans 07/09 acceptance remains gated on a real baseline. Independent plans may proceed.

The missing input is a verified companion environment containing these test
dependencies and the existing project extras. Installation requires the plan's
package legitimacy/authorization gate. Once provisioned, the executor rechecks
the runtime and runs the capture/check commands below; no blanket implementation
approval or replacement theme is needed.

## Exact source and runtime

| Input | Value |
| --- | --- |
| Companion root | `/home/alex/projects/alex/tabler-test` |
| Origin | `https://github.com/alexander-jacob/tabler-test.git` |
| Pinned companion commit | `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` |
| Theme | `src/crud_views_tabler` |
| Crispy template pack | `src/django_tabler/templates/crispy_tabler` |
| Crispy layout Python | `src/django_tabler/crispy` |
| Pre-change core commit | `cb26af4dfef2afb31d774a219abfad1c675cdff1` |
| Companion executable | `/home/alex/projects/alex/tabler-test/.venv/bin/python` |
| Runtime prefix | `/home/alex/projects/alex/tabler-test/.venv` |
| Observed versions | Python 3.14.7; Django 6.1.2; django-crispy-forms 2.7; crispy-bootstrap5 2026.9 |

The executable path retains its venv symlink; dereferencing it loses the selected
environment. Django 6.1 is the companion's integration runtime and does not expand
the core package's published support matrix.

`example/config/settings.py` was user-modified at initial inspection and became
clean with the external commit above. Preserve its current bytes and index state.
Never copy its contents into evidence. Baseline archives come from Git commits,
not mutable worktrees. Each run uses disposable sibling `tabler-test/` and
`django-crud-views/` directories, preserving the editable-source layout.

## Resume and reproduce

Run from the current core repository root after resolving the missing dependencies:

```bash
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --capture-baseline --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06-companion-baseline.json
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --check-baseline --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06-companion-baseline.json
```

Defaults bind the exact roots/revisions above. Optional `CV_THEME_SOURCE` and
`CV_PACK_SOURCE` must name the same supplied monorepo; `CV_THEME_CORE_BASE` must
match the pinned core commit. `CV_THEME_PYTHON` may select the verified absolute
companion executable during capture. Thereafter its path, prefix and versions
are recorded; conflicting `CV_THEME_PYTHON`/`CV_FOCUS_PYTHON` values fail closed.
No system-Python or sibling-directory fallback is permitted.

If source acquisition fails, restore/provide the supplied repository with the
recorded origin and commit available; do not substitute another package, silently
fetch, reset the user's checkout, or waive the baseline. The tool reports the
specific missing source/runtime condition before copying or running suites.

Capture runs these exact suites from the isolated companion copy using the
recorded executable (shown as `$COMPANION_PYTHON` for readability):

```bash
"$COMPANION_PYTHON" example/manage.py test django_tabler crud_views_tabler dashboard catalog customers --parallel 4
"$COMPANION_PYTHON" -m pytest tests -n 4 -q
```

The isolated `PYTHONPATH` selects companion `src`, sibling core `src`, companion
root and `example`. Django uses test-only configuration; pytest retains its own
settings configuration. Module origins and every discovered shadow/pack template
origin plus content hash are probed before tests. Original source/index digests
are compared after capture. A captured failing suite is recorded as failed with
its actual test identities; capture success never implies suite success.

## Baseline and replay schema contract

The utility is import-pure and standard-library-only. Import by
`importlib.util.spec_from_file_location`, register the module before executing,
and call helpers explicitly. Importing or collecting its hermetic tests never
discovers or reads the production companion repository.

Baseline JSON includes canonical root/origin/revision, complete archived tracked
path/hash inventories for both repositories, runtime, preserved-state digests,
isolated roots, module/template origins with the raw origin command, asset URLs,
complete suite logs and parsed counts/failure identities. `status: captured` and
`tests_outcome: passed|failed` are separate fields. Embedded logs retain argv,
cwd, exit code, duration, sanitized stdout/stderr and their digest. Temporary
paths describe the execution; validation does not require them to survive.

`classify_tree(files, core_files)` creates an exhaustive path/hash map, separate
shadow map, and symbol/section classifications. Each section is a required
customization purpose, supported data-only adoption, or an explicit non-customization
reason. Mixed files retain behavior sections alongside registrations. Validators
derive coverage independently from source, so adjusted totals cannot hide omitted
templates, checks, symbols or new source files. Distinct stable purpose IDs are
the counting unit. Renames retain identity; a new behavior cannot borrow an old ID.
Retirement requires passing assertions and concrete adoption paths.

Plan 07's `07-tabler-replay.json` must embed:

- `baseline_sha256`, exact textual `patch` and `patch_sha256`;
- `inventory` for the reconstructed full candidate tree and `retired_purposes`;
- `core_inventory` for current core `src/`, `tests/`, `docs/`, and existing
  `pyproject.toml`, `package.json`, `package-lock.json`;
- `runtime`, two passing `suites`, `isolated_roots`, `origins`, and the complete
  `origin_command` from the isolated candidate;
- `status: passed`, eight `cases`, effective `adoption`, focused `test_nodes`,
  15 `actions`, and 54 `cancel_no_url` activation records.

Use `digest()` for canonical JSON hashes and `inventory()` for byte hashes;
`source_sha256` is `digest(inventory(candidate_files))`, not a Git commit SHA.
Case IDs are `owned-form`, `csrf-post`, `label-floor`, `action-groups`,
`alert-dismiss`, `modal-replace`, `conditional-formset`, `cancel-navigation`.
Each case and each nonempty assertion must pass. `FOCUSED_TESTS`,
`ADOPTION_CLASSES`, `ADOPTION_ICONS`, `validate_phase_evidence`, and the passing
fixtures in `test_theme_adoption_sources.py` define exact field values.

Action records cover submit/delete/cancel/filter-submit/filter-reset in both,
icon and label modes. They bind actual native SVG paths, visible/hidden text,
accessible names and reset behavior to candidate source. Cancel records cover
absent/None/explicit-empty destinations, requested button/anchor tags, all three
modes, and click/Enter/Space separately. Absent/None preserve edited input without
navigation; explicit empty must finish a same-URL GET document replacement.
All records forbid submit/reset/POST side effects. Suppressing navigation or
merely assigning an empty `location` value is insufficient evidence.

```bash
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --verify-replay --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/07-tabler-replay.json
```

## Delivery handoff to plans 07 and 10

`--delivered-source recorded` resolves the baseline beside this utility's core
root, independent of cwd or isolated siblings. Explicit paths must be absolute
and match that identity. Delivery validation never applies patches or commits.

Before source delivery, plan 10 calls `private_snapshot(root, external_directory)`
and provides the returned private file via `CV_THEME_PRIVATE_SNAPSHOT`. Keep it
outside both repositories. It contains preservation material and index records;
only digests/status may enter the public bundle. Delivery compares the full tree
against replay-approved bytes plus the preserved original dirty delta, including
unrelated staged hunks in the same file. Original private settings remain intact.

Both commands below merge into the one canonical bundle:

```bash
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --delivered-source recorded --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --delivered-source recorded --require-committed --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json
```

Plan 07's browser writer must atomically merge a `form_probe` slot with complete
sanitized `commands`, passing `assertions`, phase evidence and `bindings`. Copy
`CV_THEME_PROBE_RUN_ID` into `form_probe.run_id`: delivery generates a fresh ID
and rejects an exit-zero browser that reuses prior results. Preserve prior slots.
The Python driver always reruns focused Django tests, `owned-form`, and
`label-floor`, then rechecks source/index preservation before writing its slot.

Bindings must contain exactly:

```text
source_sha256 = digest(inventory(candidate_files))
preserved_dirty_sha256 = digest(baseline["preserved"])
index_preserved = true
runtime_sha256 = digest(baseline["runtime"])
config_sha256 = digest(baseline["test_configuration"])
core_sha256 = digest(replay["core_inventory"])
```

The bundle progresses through `form_probe`, `delivered_probe`, `committed_probe`.
Partial/provisional results cannot certify completion or overwrite a complete
result. Revalidation retains historical completion and requires fresh current
evidence. Failures retain their real logs and a failed status. `validate_bundle`
checks embedded evidence after temporary directories are removed; no required
sidecar logs are permitted. Live revalidation still needs the private snapshot.

Committed validation requires separate `companion_receipt` and `core_receipt`,
each with `repository_root`, `before_head`, `after_head`, `tree`, `delta_sha256`.
Read commit objects in their own repositories. The companion commit must contain
exactly the replay-approved source delta and no unrelated staged content. The
core receipt identifies its scoped `10-companion-delivery.json` evidence commit;
it cannot substitute for the companion source commit.

## Utility verification

The required broad collection command passed on 2026-11-02: **93 passed in 4.47s**.
It uses only disposable Git/source fixtures and clears companion overrides:

```bash
env -u CV_THEME_SOURCE -u CV_PACK_SOURCE -u CV_THEME_CORE_BASE PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests -k theme_adoption_sources -n 4 -q
```

This proves the utility's positive/negative contracts, including preserved staged
hunks, wrong-repository receipts, post-hook drift, source-bound origins and fresh
cancel records. It does not replace either real companion suite or browser run.
