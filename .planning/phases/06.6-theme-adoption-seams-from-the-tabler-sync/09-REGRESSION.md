# Phase 06.6 final regression evidence

**Automated gates passed; all seven scoped human checks passed in 06.6-UAT.md. Final canonical verification remains orchestrator-owned.**

Final source inventory SHA-256: `27675fa0d6f7f164291fb9c843578ddf774ae8068d2dc60b0990051a3508d66d`. The exact per-file inventory,
embedded stdout/stderr, JUnit, commands, measured duration, interpreter/package/module/template origins,
environment selections and browser evidence are retained in [09-final-evidence.json](09-final-evidence.json).
The report has no self-hash. `--check-final` independently revalidates actual sources and both repositories.

## Final gate results

| Gate | Result | Duration (seconds) |
| --- | --- | --- |
| conditional-formsets | 2 cases passed | 14.171 |
| configuration | 21 passed | 16.806 |
| django42-current | 8720 passed; 1 skipped | 146.182 |
| django42-floor | 8719 passed; 1 skipped | 145.61 |
| django52-current | 8720 passed; 1 skipped | 200.489 |
| django60-floor | 8720 passed; 0 skipped | 238.016 |
| docs | passed | 1.43 |
| example | 301 passed; 0 skipped | 13.637 |
| format | passed | 0.015 |
| fragments | 2 passed | 10.164 |
| javascript | 363 passed | 12.15 |
| lint | passed | 0.042 |
| modal-focus | 12 cases passed | 24.285 |
| whitespace | passed | 0.13 |

## Exact commands

All commands run from the core checkout. Broad pytest uses four workers; core versions run sequentially.
The unchanged modal-focus command adds only `--output` to keep this phase's evidence separate.

- **conditional-formsets:** `PYTHONPATH=src:. node tests/browser/conditional-formsets.cjs --case lifecycle --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/conditional-formsets.json`. Raw log: `09-evidence/conditional-formsets.log`.
- **configuration:** `NODE_OPTIONS=--test-reporter=tap PYTHONPATH=src:. env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON node --test tests/browser/theme-adoption-config.test.cjs`. Raw log: `09-evidence/configuration.log`.
- **django42-current:** `PYTHONPATH=src:. .nox/tests-3-12-django-4-2/bin/python -m pytest tests -n 4 -q --junitxml=.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/django42-current.xml`. Raw log: `09-evidence/django42-current.log`.
- **django42-floor:** `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline --junitxml=.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/django42-floor.xml`. Raw log: `09-evidence/django42-floor.log`.
- **django52-current:** `PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests -n 4 -q --junitxml=.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/django52-current.xml`. Raw log: `09-evidence/django52-current.log`.
- **django60-floor:** `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline --junitxml=.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/django60-floor.xml`. Raw log: `09-evidence/django60-floor.log`.
- **docs:** `PYTHONPATH=src:. .venv/bin/mkdocs build --strict`. Raw log: `09-evidence/docs.log`.
- **example:** `DJANGO_SETTINGS_MODULE=project.settings PYTHONPATH=src:examples/bootstrap5 .nox/tests-3-12-django-5-2/bin/python -m pytest -c examples/bootstrap5/pytest.ini examples/bootstrap5 -n 4 -q --junitxml=.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/example.xml`. Raw log: `09-evidence/example.log`.
- **format:** `PYTHONPATH=src:. .venv/bin/ruff format --check src tests examples`. Raw log: `09-evidence/format.log`.
- **fragments:** `CV_FRAGMENT_PYTHON=.nox/tests-3-12-django-5-2/bin/python PYTHONPATH=src:. node node_modules/vitest/vitest.mjs run --config vitest.integration.config.js`. Raw log: `09-evidence/fragments.log`.
- **javascript:** `PYTHONPATH=src:. node node_modules/vitest/vitest.mjs run --maxWorkers=2`. Raw log: `09-evidence/javascript.log`.
- **lint:** `PYTHONPATH=src:. .venv/bin/ruff check src tests examples`. Raw log: `09-evidence/lint.log`.
- **modal-focus:** `CV_FOCUS_PYTHON=.nox/tests-3-12-django-5-2/bin/python PYTHONPATH=src:. node tests/browser/modal-focus.cjs --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/09-evidence/modal-focus.json`. Raw log: `09-evidence/modal-focus.log`.
- **whitespace:** `PYTHONPATH=src:. git diff --check`. Raw log: `09-evidence/whitespace.log`.

## Runtime and coverage boundaries

| Core gate | Python | Django | crispy forms / Bootstrap pack |
| --- | --- | --- | --- |
| django42-current | 3.12.3 | 4.2.30 | 2.5 / 2026.3 |
| django52-current | 3.12.3 | 5.2.18 | 2.7 / 2026.9 |
| django42-floor | 3.12.3 | 4.2.30 | 2.0 / 2023.10 |
| django60-floor | 3.12.3 | 6.0.9 | 2.0 / 2023.10 |
| example | 3.12.3 | 5.2.18 | 2.7 / 2026.9 |

All core imports resolve to this checkout's `src/crud_views`; resolved pack/template origins and installed extras are embedded in each Python gate preflight.
The example gate uses its own pytest.ini and `project.settings`. Only django-ratelimit 4.1.0 was added to its cached 5.2 interpreter after verified official metadata; see [package provenance](09-evidence/example-dependency-provenance.md).
**Current-pack Django 6.0 is untested:** no cached interpreter/pack combination exists. The 6.0 floor is a distinct result. Core Python coverage is 3.12.3, not the entire declared 3.12–3.15 matrix.
The only floor deselection is `tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`. All new theme modules, alert/key-table cases and retained leaf goldens execute. Django 4.2/5.2 retain only `test_django6_builtin_csp_nonce_roundtrip`; 6.0 executes it.

## Companion integration and actual delivery

The independently recorded Python 3.14.7 / Django 6.1.2 companion runtime remains additional integration coverage, not a supported core-series substitute.
Fresh final-source candidate and exact-patch replay each pass all eight real browser families, 11 focused native/class-table/parity/package tests, and 34 companion pytest cases.
The broad Django suite retains its actual failed status: 114 tests / three unchanged baseline failures, compared with 109 / four at the pinned baseline. Complete failing classes and identities are checked, and passing suites cannot hide reduced collection or newly skipped cases.
The source inventories retain 167 paths, nine shadows and 205 required customization purposes. No required override grows or is retired without proof.
Actual companion commit: `3315eef6671f502d859bba877322a5853388c508`. Current two-file core delivery evidence commit: `f0510f1628db8ae57dc72f0d75a8e8788aa8e1b5`.
Private settings, unrelated source/index bytes and the five-file patch are unchanged. Provisional/committed probes, refreshed CSRF denied POSTs, complete cancel activations and native assets are retained in the canonical reports.
Chromium 149.0.7827.55 exercised Tabler 1.6.1 CSS/theme/main JS and the existing jQuery 3.7.1 fixture asset. Each observed asset has hashes/SRI; equality uses unique URL/content records, not network completion order.

## Preserved attempts and repaired findings

The original floor-selection RED is retained in `09-evidence/red.json` / `red.log` and classified RED_EVIDENCE_OK. Passing-suite shrink/skip regressions retain `shrink-red.xml` / `shrink-red.log`.
The first full matrix, the missing example dependency, and stale docs-sync assertion remain embedded in `09-evidence/prior-gates.json`. Later source-drift runs are retained in the additional `prior-gates-*.json` files. These runs are historical, not rebound to final source.
The helper preflight ordering error was corrected before running its first suite. Failed `--case csrf-post` CLI invocation is retained; the actual harness supports owned-form, label-floor and all, so the complete eight-family run supplied the denied-write proof.
Review repair CR-01 (RED1d1d5f0 / GREEN38df8ac) retains hidden row/PK fields after source-bound layout hooks without mutating caller helpers. The focused 719-test selection passed current 5.2 and both 4.2/6.0 floors; copied logs/JUnit are in `09-evidence/cr01-*-green.*`.
CR-02 now compares collection and skips before a passing-suite early return. The security harness now checks denied writes with a post-login rotated CSRF cookie, a permission403 rather than CSRF failure, and identical persisted snapshots.
The stale parent-helper fence in docs/reference/formsets.md was synchronized with the earlier phase removal; no product behavior was changed by that documentation repair.

## Acceptance limits

No new unresolved implementation stub, missing mandatory automatic command, scenario waiver or skipped required theme case is accepted. Seven human usability checks passed, including the corrected parent formset save destination; W1 spacing was accepted. Browser/version was not supplied. Screen-reader/AT behavior, other engines, mobile/touch devices and high-contrast modes remain unverified.
Independent security/code review and canonical phase verification remain orchestrator-owned. See [acceptance](06.6-ACCEPTANCE.md) and [public surface](06.6-PUBLIC-SURFACE.md). Phase 7 stability classification is not performed.


## Post-UAT fixture correction

User UAT found that successful parent create/update redirected to a fixture list whose ID LinkDetailColumn called an unregistered detail view. Commit f237abd uses a plain ID column and adds enforced-CSRF POST redirect GET assertions for both create and update. Both assertions failed before the fix; all 12 focused formset tests passed afterward, and the user retested successfully.

The final validator binds every gate to the complete source inventory and exact command/JUnit contract. All 14 gates were therefore freshly executed after the two-file fixture/test change; no prior test result was rebound. The parent separately ran 5.2 without JUnit (8716 passed, one existing skip); its log is retained but does not replace the canonical gate. All original matrix evidence remains in prior-gates-8f8dae91557c.json.

Fresh candidate and exact-patch replay passed all eight families, followed by provisional and committed actual-source probes. The first attempt to reuse the old delivered slot was correctly rejected as stale; its complete commands/error are retained in delivery-post-uat-stale-attempt.json. The successful refresh rebuilt both slots. Companion source and user settings remain unchanged.

Seven human checks passed and W1 spacing was accepted in [06.6-UAT.md](06.6-UAT.md). The checker itself validates automated evidence only and retains its fixed pending-human-observations return value; the separate human_acceptance record stores the actual UAT result and artifact hash. Browser/version was not supplied; no assistive-technology claim is inferred.

## Final IDE metadata correction

After the post-UAT checker passed, six ignored local .idea files appeared in the companion checkout and the strict source check correctly stopped on the unclassified files. RED cd10b31 demonstrates the classification defect; GREEN 9957754 omits only Git-ignored, untracked paths under the repository-root .idea directory. Tracked/nonignored IDE files, arbitrary ignored source, symlinks, private settings and index preservation remain checked. The four new real-repository regression cases pass; the utility selection totals 153 tests.

Six user IDE files were preserved in place; ide-metadata-before.json and ide-metadata-preservation.json contain hashes only. Fresh candidate-post-ide.json/replay-post-ide.json, provisional/committed delivery probes and all 14 gates bind the corrected validator source. The prior post-UAT matrix remains historical in a prior-gates report; no old test execution was rebound. Human UAT seven-pass status and browser/AT limits remain unchanged.
