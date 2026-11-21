# Phase 06.44 — Plan 02 acceptance evidence

Execution date: 2026-11-21. Task 1 base: `17df2d197aaef62335dca81941c1f238d819e50f`.
This report covers the approved D-01–D-04 delivery. All required execution checks passed; full-suite exit was 0.

## Runtime and source selection

- Node 24.21.0; installed jquery 3.7.1, jsdom 31.0.0 and Vitest 5.1.0 exactly match package-lock.json.
- Reused Plan 01's ignored local node_modules symlink. No npm install/ci, shared dependency mutation, package addition or manifest change.
- Python 3.12.3 / Django 6.0.10 from the prescribed `.nox/tests-3-12-django-6-0/bin/python`.
  `PYTHONPATH=src:.` import-origin assertion resolves crud_views inside this workspace's src directory.
- Docs use the separate prescribed .venv interpreter, MkDocs 1.6.1. Ruff 0.17.3.
- CSS and manage smoke use Playwright 1.64.1, Chromium 159.0.8154.6.
  The retained compact lifecycle receipt records its original Chromium 149.0.7827.55 run.

## Command outcomes

Durations below are actual elapsed seconds measured around each final command, rounded to whole seconds by the shell clock.
The commands execute from this worktree; Python runs use four workers.

| Check | Exit | Outcome | Seconds |
|---|---|---|---|
| Task 1 focused guard and runtime sandbox | 0 | 29 passed; 26 guard fixtures, 3 runtime checks | 9.96 (runner) |
| Task 1 tracer repeat | 0 | 29 passed | 10.07 (runner) |
| Task 2 focused docs | 0 | 31 passed | 3.32 (runner) |
| Final affected Python files | 0 | 365 passed | 11 |
| Full Python suite | 0 | 16,548 passed, no skips (533.39s runner time) | 535 |
| Ordinary Node suite | 0 | 483 passed, 12 files, no skips | 14 |
| Required Node/Python integration | 0 | 2 passed, no skips | 22 |
| Strict MkDocs | 0 | Successful strict build | 4 |
| Full synthetic CSS browser | 0 | All 6 required cases passed | 1 |
| Existing real manage smoke | 0 | All 3 required cases passed | 4 |
| Compact lifecycle receipt checker | 0 | CONDITIONAL_EVIDENCE_OK, 1 case / 19 stored assertions | 0 |
| Ruff check | 0 | All checks passed | 0 |
| Ruff format --check | 0 | 775 files already formatted | 0 |
| Migration/manifests fixed hashes | 0 | All three phase-start hashes match | not timed |
| Historical PNG fixed hashes | 0 / 0 | Before/after receipt check, all four match | not timed |
| git diff --check | 0 | No whitespace errors | not timed |

Exact final commands:

- **focused:** `PYTHONPATH=src:. /home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python -m pytest tests/test1/test_formsets_compact.py tests/test1/test_formsets_compact_docs.py tests/test1/test_formset_row_legends.py tests/test1/test_manage_presentation.py tests/test1/test_manage_docs.py -n 4 -q`
- **full-python:** `PYTHONPATH=src:. /home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python -m pytest tests -n 4 -q`
- **node:** `npm test`
- **integration:** `CV_FRAGMENT_PYTHON=/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python npm run test:integration`
- **mkdocs:** `PYTHONPATH=src:. /home/alex/projects/alex/django-crud-views/.venv/bin/python -m mkdocs build --strict`
- **css:** `node tests/browser/css-tokens.cjs --case all --output .planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/evidence/css-tokens.json`
- **manage:** `node tests/browser/manage-presentation.cjs --python /home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python --case smoke --output .planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/evidence/manage-smoke.json`
- **lifecycle:** `CV_FOCUS_NODE=/home/alex/.nvm/versions/node/v24.21.0/bin/node CV_FOCUS_PYTHON=/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python node tests/browser/conditional-formsets.cjs --case compact-lifecycle --compact-capture-root .planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/evidence/compact-captures --check-evidence .planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/evidence/compact-lifecycle.json`
- **ruff:** `/home/alex/projects/alex/django-crud-views/.venv/bin/python -m ruff check .`
- **format:** `/home/alex/projects/alex/django-crud-views/.venv/bin/python -m ruff format --check .`

Task 1: `npm test -- tests/js/css-tokens.test.js tests/js/runtime-contract.test.js`.
Task 2: `PYTHONPATH=src:. /home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python -m pytest tests/test1/test_formsets_compact_docs.py tests/test1/test_manage_docs.py -n 4 -q`.
The fixed SHA-256 Python assertions are the exact commands from Plan 02 verification step 8 and Plan 01 Task 3.
The historical-PNG assertion ran before and after the final compact receipt check; each returned exit 0.
No new lifecycle capture was needed because source freshness passed.

## Observable contract coverage

The local guard preserves each declaration occurrence before checking ownership and reads. Its independently specified six chains and twelve selector/property consumers must remain present. It rejects bare/overwritten/nested Bootstrap reads, wrong pairs/literals, unknown cv reads, upstream cv declarations (including duplicates), other Bootstrap declarations, misplaced help declarations, variable references outside values, malformed/unbalanced syntax and explicitly unsupported syntax. The sole permitted Bootstrap declaration is the exact manage help selector/property/chain, once.

The canonical unique CSS tokens section must contain the exact two-column table, six unique approved pairs, and no missing or duplicate rows. A token in prose cannot replace a row. Positive fixtures cover actual source (including keyframes and quoted selectors), whitespace/comments and nested media/grouped rules. The sandbox copies the two CSS fixtures and canonical docs, requires css-tokens discovery, has Node alone on PATH, and still proves missing/invalid Python fails the required integration lane.

Both consumer tests section-bound their links and resolve the canonical unique heading; referenced root/inheritance/nested-dark/help guidance is required. Copied compact headings explicitly retain row/component hooks and add gx-3. Release notes add only Added/Changed entries for this phase; unrelated Breaking entries remain intact.

## Browser evidence

- `css-tokens.json`: stock-light-1280, stock-dark-1280, stock-light-390, stock-dark-390, theme-root-mapping, literal-fallback. All passed.
- Stock cases compare all twelve consumers and both grids against immutable baseline revision `04f95c30a6b368697ad92248071fec0477689186`, including gutter/alignment/padding/margin/geometry and responsive visibility. Nested dark differs from light before parity can pass.
- Mapping checks cover all six theme-root aliases, precedence over conflicting Bootstrap properties and the root-only control. Literal fallback checks run without Bootstrap.
- `manage-smoke.json`: core-normal-390, guardian-normal-390, ordinary-denied. All passed; receipt validates expected cases/assets and cleanup. Owned server stopped and temporary database/directory removed. Two phase-local screenshots are retained with recorded SHA-256 values.
- `compact-lifecycle.json`: reused Plan 01's 19-assertion result and revalidated current source hashes plus exact retained PNG paths with `--compact-capture-root`. Plan 01's 45 passing evidence-unit tests are reused: neither tested runner nor evidence-unit source changed.
- Historical PNGs and `browser-lifecycle.json` were not rewritten. Plan 01's original failure receipts remain retained.
- Lifecycle humanReview remains pending in its historical schema; these results establish automated checks, not human visual approval.

## Source fingerprints

| File | SHA-256 |
|---|---|
| tests/js/css-tokens.test.js | 768a374257be147eda3061fed914453b5ca3e90131e357d0b60c5b15c8ded962 |
| tests/js/runtime-contract.test.js | f4fcda3603624848455cbb498e62a4975a15d4a9e6ed33b865243913c087ec1e |
| docs/reference/theme.md | 9ec4d6cb9ac6f9d6b2c7f2d9befc788d3d3534c7d3b7bb2cab4ea2e8e9df867e |
| docs/reference/formsets.md | c086fc9da1090e123f4fedfe3fb2d4465aabd597e1d4adfc03f65e135f538d9d |
| docs/reference/manage.md | b204fe8aa46fe9014752ec7e7ee2ce2e8920f834811b1d6e8757799f862408fb |
| CHANGELOG.md | fefb7c2d35659b301b974e51236380696aec3b8881918219e57880bae166bb72 |
| tests/test1/test_formsets_compact_docs.py | 128ddf2970d78a993db061cb2da38e49b23f4492287216fdabcc4b4cfbae1e77 |
| tests/test1/test_manage_docs.py | 2e2e035dcacc4cfe8973cfd627fb2d91ed55c8e6990bd6a94d2e5370d3ccc722 |
| src/crud_views/static/crud_views/css/manage.css | 8b617bf32db046ad6f6daa379dd7c79a4b5b0efe2f05b2521c6b691f6d19670c |
| src/crud_views/static/crud_views/css/formset.css | e216fdbfe50dc9424184290922d8e03fd532e6d8dc472ef100bfe879258c4e27 |
| src/crud_views/templates/crud_views/formsets/compact_headings.html | d0795718526dd8ae9bf753d03dcd792e621a1b41fbf0905747c2dba4c47df02d |
| src/crud_views/lib/formsets/compact.py | bc007fffce7b30be1ad0259baef1b7891ae9a5901cad3ab332371908d5d33f0e |

Migration: `1dca0d49f8abbc51854b8a45a7622b761403df2a9784112a0f060f0ef1327792`.
package.json: `07daa4860e87e73ac3ad459848eaadc218281036f8d4a7e958aab6c49999b440`.
package-lock.json: `aba033d067d60e33ab912e946471ef3c72f76f020dcfb4cbd6ab224b0cd0da39`.

## Failure history and corrections

1. Task 1 intentional RED: 23 invalid-fixture failures / 3 positive passes, exit 1. Complete unchanged TAP and semantic assessment are embedded in `task02-01-red.json`; classifier returned RED_EVIDENCE_OK.
2. First Task 1 GREEN attempt: 19 failed / 10 passed, exit 1, because value normalization removed the space before the parenthesis in an @media prelude, causing unsupported-at-rule diagnostics. A single shipped-source diagnostic run had 1 failure / 25 deliberately unselected tests. Kept selector normalization separate from value normalization; the complete rerun and tracer both passed 29/29. No skipped fixture is accepted in final evidence.
3. Task 2 intentional RED: 2 missing-link assertion failures / 29 passes, exit 1. Complete unchanged JUnit and console report are embedded in `task02-02-red.json`; RED_EVIDENCE_OK. The stored runStartedAt uses the reporter's actual testsuite timestamp.
4. Initial Ruff check: exit 1, two E501 lines of length 124 in the new docs tests. Applied the repository formatter to those two files; final broad lint and format checks passed. All final Python verification uses formatted sources.
5. Existing Vite future-config-loader warnings and jsdom navigation diagnostics appeared in successful Node output. They are not new implementation failures and were not suppressed or changed.

## Scope and remaining limits

No production source changes in Plan 02; Plan 01 supplies the twelve CSS reads and two gutter-class edits. No golden changes, migration edits, new dependencies/tokens/settings/endpoints/class keys or extension/downstream work. No new stubs or skipped required cases. The scanner is intentionally test-local and bounded, not a general CSS parser; unsupported new syntax requires a deliberate guard update.

Only the prescribed Python 3.12 / Django 6.0 runtime is tested here. Synthetic browser style comparisons do not claim downstream CoreUI/Tabler adoption or a complete compatibility matrix. There are no formal requirement IDs, so the ID-driven spec-less probe is inapplicable; D-01–D-04 remain the acceptance criteria. No phase completion, ship, push or release is claimed.

