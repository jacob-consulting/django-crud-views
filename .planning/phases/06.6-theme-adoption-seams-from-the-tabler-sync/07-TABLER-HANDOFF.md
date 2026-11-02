# Tabler adoption handoff — plan 06.6-07

The five-file adaptation in [07-tabler-adaptation.patch](07-tabler-adaptation.patch) passed a fresh exact-base replay against the current core. Plan 10 owns applying and committing these bytes in the supplied companion repository. This plan made no companion source/index changes and preserved the user's settings-only commit.

## Bound inputs and retained evidence

| Input | Identity |
| --- | --- |
| Companion repository | `/home/alex/projects/alex/tabler-test` (one repository containing both components) |
| Exact companion archive | `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` |
| Preserved live companion HEAD | `0b3baa896ef5b11aa010238c92d3bceb4663e337` |
| Baseline core revision | `cb26af4dfef2afb31d774a219abfad1c675cdff1` |
| Tested current core commit | `e62ac6e` |
| Tested core inventory SHA-256 | `7d0e479c206ee44fbbde72118e57fa3dbf3e6c6e9b9d063208829a5661ecf200` |
| Patch SHA-256 | `7163d9d80940ead44851f72a0fa9a57af93b37b23e19a3f94d7746f060903b99` |
| Patched companion tree SHA-256 | `a79f83983515f0331793afcc92ac682713d5b87818e73237590b6e4e31dc9560` |
| Recorded interpreter | `/home/alex/projects/alex/tabler-test/.venv/bin/python` |
| Companion runtime | Python 3.14.7; Django 6.1.2; crispy-forms 2.7; crispy-bootstrap5 2026.9 |
| Browser | Chromium 149.0.7827.55, cached Playwright runtime |

[06-companion-baseline.json](06-companion-baseline.json) binds the original archives, test-only configuration, preserved work, and raw baseline suite logs. [07-browser-results.json](07-browser-results.json) contains the candidate run. [07-tabler-replay.json](07-tabler-replay.json) embeds the exact patch, applicability/application commands, full focused and broad suite logs, fresh browser results, source/template origins, asset hashes, full before/after inventories, delivery map, and original-source preservation checks. Required evidence is embedded; temporary copies were removed after each run.

The recorded interpreter is resolved afresh from the baseline under the executing harness's core root. Neither ambient interpreter overrides nor an inferred sibling checkout are required. The isolated configuration uses pinned public settings, never the user's live private settings file.

## Theme section: exact delivery map

All paths are relative to the companion root. Full before/after SHA-256 values are in the replay's `delivery_map`; abbreviated values below are for review only.

| Path | Before → after SHA-256 prefix | Change |
| --- | --- | --- |
| `src/crud_views_tabler/apps.py` | `7a07548d0b95` → `3d7118ac71ab` | Register exactly `{"form": "both"}` through the public label-floor API. |
| `src/crud_views_tabler/buttons.py` | `8b791f963b2b` → `f0ffcc2045fa` | Four exact action-group and alert utility defaults. |
| `src/crud_views_tabler/icons.py` | `bd1cce25fcf9` → `8cf3b06095ba` | Map save/check, cancel/arrow-left, and filter-reset/filter-x; retain native renderer. |
| `src/crud_views_tabler/templates/crud_views/tags/alert.html` | `ece8c7856dab` → `5a93bcf26a61` | Consume alert class keys and `data-cv-alert-dismiss`, retaining the Tabler layout. |
| `src/crud_views_tabler/tests.py` | `915ec8b0b27d` → `73d9b3f2cf21` | Extend literal whole-dictionary equality, enforce precise native/CRUD message parity, add native action and cancel regressions. |

The class defaults are `form:actions="d-flex flex-wrap gap-2"`, `form:filter-actions="d-flex flex-wrap gap-1"`, `alert:dismissible="alert-dismissible fade show"`, and `alert:close="btn-close"`. The native `django_tabler.icons` registry/rendering module is unchanged.

## Pack section: retained without a patch

`crispy_tabler` templates and `django_tabler.crispy` already forward the action group's `css_class`. The fresh browser's `pack_probe` proves the empty render is byte-identical and a hostile sentinel is escaped inside the native wrapper. There is no pack file delta and no separate pack repository. Preserve the additive native wrapper classes.

## Exhaustive override reconciliation

The independently scanned manifests cover **167 paths before and after**, **nine template shadows before and after**, and **205 required customization purposes before and after**. No required purpose was added, removed, renamed, or retired. The replay retains every path in `path_dispositions`, every required section in `purpose_dispositions`, and the three supported registration sections separately in `adoption_dispositions`.

`CrudViewsTablerConfig`, `TABLER_BUTTON_CLASSES`, and `TABLER_ICONS` are data/API adoption. The icon render callback and bespoke system checks remain counted as required behavior. All shadows, including `modal/shell.html`, stay counted. No helper or template behavior was reclassified to reduce the count.

The four affected render probes retain real resolved origins and before/after hashes:

| Existing shadow | Disposition and proof |
| --- | --- |
| `crud_views/snippets/form_frame.html` | Retain the card wrappers; raw ownership and full/modal replacement checks pass. |
| `crud_views/tags/list_filter.html` | Retain; actual GET filter ownership and separate action-group checks pass. |
| `crud_views/tags/list_filter.inner.html` | Retain; real native filter/reset and trailing hidden input checks pass. |
| `crud_views/tags/alert.html` | Migrate only utility classes/hook; strict parity and all dismissal variants pass. |

The pinned companion has no `crud_views/tags/form.html` or `crud_views_workflow/view_workflow.action.html` bypass copy. Actual template resolution inherits the core owned-form and workflow implementations. Do not add either override. There are no proven removable overrides in this patch; retain the nine existing shadows until a separate behavior-backed retirement is available.

## Acceptance results and limits

Both candidate and fresh replay passed these eight real HTTP/browser families:

| Family | Retained assertions |
| --- | --- |
| `owned-form` | One target form/token, no raw nesting, native `element.form` and `FormData` ownership including submitter, multipart POST; auxiliary sibling forms have independent tokens. |
| `label-floor` | Five action kinds × three modes = 15 records; exact native SVG paths and labels; theme/project/owner precedence and restoration; native reset value/event and established GET navigation. |
| `action-groups` | Ordinary/filter defaults, custom values, explicit empty values, separate slots, actual pack wrapper, escaped sentinel, filter's trailing hidden state. |
| `alert-dismiss` | Twelve native/CRUD × class variant × click/Enter/Space records; native Bootstrap hook only, CRUD core hook only, exactly one adapter call, other notice retained. |
| `modal-replace` | Real custom/delete/workflow/no-choice modal GET and invalid 422 replacement with focus/close restoration; full-page create/update retained and opt-in rejected by E251; eight distinct workflow full/modal × choices/no-choice × GET/POST records. |
| `conditional-formset` | Parent create/update, actual conditional visibility and fragment insertion, management count/native ownership, invalid POST values and focus retained. |
| `cancel-navigation` | URL-bearing click/Enter/Space performs the actual GET; no submit/reset. |
| `csrf-post` | Missing/invalid tokens rejected with 403 and unchanged data; five valid-token writes; invalid forms, protected delete, no-choice workflow and unauthorized access remain guarded. |

The label-floor family separately records **54 URL-less cancel activations**: absent/None/explicit-empty × requested button/anchor × both/icon/label × click/Enter/Space. Every result is a native `button type=button`. Absent/None remains a no-op and preserves the edit; explicit empty retains a real same-URL document GET and replacement. The harness does not intercept or suppress that navigation. Neither branch submits or resets.

The focused companion selection passed **11/11 tests**, including strict whole-dictionary equality, all `ThemeAdoptionTests`, `MessagesParityTests`, and dependency-free `PackageTests`. Removing each new icon mapping causes the exact native render assertion to fail. Parity permits only the verified dispatch-attribute substitution plus whitespace normalization; missing/wrong/dual hooks and unrelated body/role changes are rejected. Standalone `django_tabler` messages retain `data-bs-dismiss="alert"` and require no core adapter.

The full Django suite collected **114 tests** and retained **three failures**, versus **109 tests / four failures** at baseline. Pytest passed **34/34** on both runs. The remaining failures are:

- `crud_views_tabler.tests.ThemeRenderingTests.test_delete_form_is_the_stock_crispy_delete_form`
- `crud_views_tabler.tests.ThemeRenderingTests.test_related_objects_alerts_get_the_tabler_layout`
- `catalog.tests.ProductFormCoverageTests.test_form_actions_and_group_labels`

Their original and replay logs are embedded; the validator requires baseline identity membership and the entire failing test classes, including setup/assertions, to remain source-identical. All required phase scenarios and new focused tests pass independently. The broad suite's actual failed outcome is preserved, not relabeled green.

The final harness configuration suite passed 20 tests; source/evidence validation passed 109 tests using four workers. Ruff and `git diff --check` passed. Original source/index preservation and owned browser/server/temp cleanup passed on both complete runs.

These are automated Chromium checks, not human visual or assistive-technology acceptance. The reports retain the three actual Tabler 1.6.1 assets with byte hashes/SRI and the exact existing jQuery 3.7.1 fixture asset required for the core formset script. The isolated parent-formset route supplies that existing core fixture dependency; no companion template was edited to inject it. Four expected invalid-modal HTTP 422 console messages are recorded separately; unexpected console errors and page errors are empty. Supported core Django-version gates remain separate from this companion's Django 6.1 runtime.

## Reproduction and plan 10 delivery

From the core repository:

```bash
env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON node --test tests/browser/theme-adoption-config.test.cjs
env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON node tests/browser/theme-adoption.cjs --case all --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/07-browser-results.json
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python tests/browser/theme_adoption_sources.py --verify-replay --output .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/07-tabler-replay.json
```

To independently rerun the retained patch, set `CV_THEME_REPLAY_PATCH` to the absolute retained patch path and invoke the same `--case all` harness with a new output file. Preparation applies `git apply --check` and `git apply` to a fresh pinned archive before running the same suites and browser cases. The canonical replay also embeds that patch and the exhaustive reconciliation fields for `--verify-replay`; retain those fields when regenerating a canonical report.

For plan 10, validate the baseline/replay first, preserve the settings-only HEAD and all unrelated work, and apply only the five mapped paths. The `--delivered-source recorded` operand resolves the recorded companion root and copies current public tracked bytes into another isolated probe. Its partial `--case label-floor` result merges into `form_probe` without overwriting other delivery slots or claiming complete delivery. Run the plan 10 pre/post-commit delivery gates before closing THEME-05. This handoff grants no phase-wide completion and records no companion delivery commit.

The necessary optional core-fixture dependencies were installed in the existing companion venv after verifying their official package identities: django-fsm-2 4.3.0, django-guardian 3.5.2, django-ordered-model 3.7.4, django-polymorphic 4.11.7 (plus django-stubs-ext 6.1.2). `uv pip check` passed. The baseline's recorded interpreter/version fingerprint remains valid. No credentials or private settings contents are retained in the patch or reports.
