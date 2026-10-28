---
phase: "06"
slug: form-button-leaf
plan: "06-09"
status: accepted-with-pending-human-checks
recorded_at: "2026-10-28"
executing_branch: introduce-gsd
head_at_measurement: e40b0de
writer: single (06-09 executor; no other process writes this file)
---

# Phase 06 — Acceptance record

Every result here was measured during 06-09 at HEAD `e40b0de` (branch `introduce-gsd`). Nothing is copied from a
research probe or an earlier plan's summary without re-running it. When an earlier summary is cited, it is only
for history (which commit introduced what), never as proof of a pass.

## 1. Environment (measured)

| Item | Value |
|---|---|
| Python / Django (dev venv) | 3.12.3 / 6.1.2 |
| django-crispy-forms / crispy-bootstrap5 (dev venv) | 2.7 / 2026.9 |
| django-filter / django-tables2 / django-fsm-2 / django-polymorphic / django-guardian | 26.2 / 3.0.1 / 4.2.4 / 4.11.7 / 3.5.2 |
| pytest / pytest-xdist / nox / ruff / mkdocs | 9.2.0 / 3.8.0 / 2026.10.20 / 0.17.3 / 1.6.1 |
| Node / npm (JS gate) | v24.21.0 / 11.19.0, lock sha256 `567bff55…5d2e`, jquery 3.7.1, jsdom 30.1.2, vitest 5.0.3 |
| Crispy floor sessions | django-crispy-forms 2.0, crispy-bootstrap5 2023.10 on Python 3.12.3 with Django 4.2.30 and 6.0.9 |

## 2. Python gates (Task 1)

| Gate | Command | Exit | Result | Wall time |
|---|---|---|---|---|
| Full suite (parallel) | `.venv/bin/pytest tests -n auto` | 0 | 4445 passed | 58.3 s (pytest: 57.25 s) |
| Crispy floors | `.venv/bin/nox -s crispy_floor` | 0 | Django 4.2: 1877 passed (13.17 s); Django 6.0: 1877 passed (22.82 s); version assertion and `format_html` audit (1 call, all with arguments) passed in both | 42 s |
| Payload and cycle-3 repair shard | see §4 and §5 | 0 | 102 passed | 1.79 s |
| High-threat mitigation shard | see §7 | 0 | 109 passed | 2.16 s |
| Full suite in one process (isolation check) | `.venv/bin/pytest tests -q -p no:randomly` (no `-n`) | 0 | 4445 passed | 345 s (pytest: 343.82 s) |
| Phase modules in one process, both orders (isolation check) | `.venv/bin/pytest -p no:xdist` over `test_form_button_docs`, `test_label_mode_docs`, `test_action_label_mode_config`, `test_form_button_checks`, `test_icon_host_leaves`, `test_crispy_buttons`, `test_filter`, `test_form_buttons_golden`, forward and then reversed | 0 / 0 | 762 passed / 762 passed | 32.64 s / 32.55 s |

`crispy_floor` deselects only `test_filter_form_baseline`, as 06-07 recorded. That byte golden covers whitespace
produced by crispy-bootstrap5 itself, which differs at 2023.10. `test_filter_form_controls_match_golden` still
compares the leaf buttons and hidden inputs byte for byte at the floor. Each gate was followed by
`git status --porcelain`, and the output matched the pre-run snapshot every time (only the unrelated, pre-existing
`.codegraph/.gitignore` modification shows).

**State restoration.** Private template loaders are set through pytest-django's `settings` fixture
(`tests/test1/test_form_button_docs.py::recipe_templates`, which deep-copies `TEMPLATES` and restores it at
teardown). Settings overrides use the `override_settings` context manager or decorator. The one-process
full-suite run executes all 4445 tests in sequence, sharing one Django settings object and one template engine.
The ordered phase-module runs put the modules that install loaders or overrides both before and after the
golden and leaf modules. All three pass, so no loader or override leaks into a later module. The parallel run
spreads modules over workers, so it cannot show this.

## 3. Before-change baseline history (FORM-01, D-17)

| Baseline | Commit | Files | `src` tree, parent vs commit | `git diff B^ B -- src` | Ancestor of HEAD |
|---|---|---|---|---|---|
| create / update / delete controls | `2956f3e2ceda9331799279da88df55b466947f79` | 3 goldens + test module | `dcc38f4` = `dcc38f4` | empty | yes |
| workflow controls + filter-form region | `98b71edd393caa21d36e5449aa7934c2bce4dd92` | 2 goldens + test module | `dcc38f4` = `dcc38f4` | empty | yes |

- The phase-start tree `49f44cd:src` is `dcc38f4bf63e5fe2e481c1e297adaf08990c8f3e`. That is the same source blob
  tree as both baseline commits, so both baselines were captured against unchanged product source.
- The first commit after the baselines that touches `src` is `df2308b` (06-02 GREEN). Both baselines therefore
  come before any product change.
- **Final golden diffs (measured).** `git diff 2956f3e^ HEAD -- tests/test1/golden` changes exactly the five
  `form_buttons/*.html` files. The golden diffs come from exactly two later commits: `552c9e7` (06-02:
  create/update/delete/workflow) and `db8f33a` (06-05: filter).
  - create, update and delete now render `<input …/>` as `<button …><span>Label</span></button>`. `type`,
    `name`, `value`, `id`, `class` and `data-cv-cancel-url` are unchanged. For example, delete keeps
    `name="delete" value="Delete" id="submit-id-delete" class="btn btn-primary"`, and cancel keeps
    `data-cv-cancel-url="/author/"`.
  - workflow has the same element change.
  - filter: Apply/Reset became leaf `<button>`s inside the pack's FormActions wrapper, with ids
    `filter-button` / `filter-button-reset`, followed by the unchanged hidden `sort`/`order`/`dir` wrapper.
- **No unrelated golden was regenerated.** The repository tracks 29 other golden files
  (`tests/test1/golden/{action_menus,alerts,…}`). `git diff --name-only 49f44cd HEAD` over all of them lists none.

## 4. Delete payload evidence (M-PAYLOAD), cited separately

| Evidence | Test | What it proves | Result |
|---|---|---|---|
| Unchanged confirmation-only POST | `tests/test1/test_crud.py::test_delete_author` | `{"confirm": True}` alone still deletes and redirects to `/author/`. This test was not modified in Phase 06. | pass |
| Rendered delete submitter | `tests/test1/test_form_buttons_golden.py::test_delete_control_submits_delete_name_and_value` | The rendered control is `type=submit name="delete" value="Delete"` | pass |
| Confirmation plus clicked submitter | `tests/test1/test_form_buttons_golden.py::test_delete_post_with_clicked_submitter` | `{"confirm": True, "delete": "Delete"}`, which is what a browser sends on click, deletes and redirects | pass |

None of these proves that a POST carrying only the submitter, without `confirm`, is valid. No such claim is made:
the delete form still requires the confirmation field.

## 5. Manual cycle-3 repair evidence (re-run here, not inherited)

| Finding | Test (real `{% crispy %}` / inclusion path) | Measured result |
|---|---|---|
| H-HELPER-TRUTHINESS: both dispatch guards | `test_crispy_buttons.py::test_filter_empty_layout_replacement_dispatches_through_the_tag` (6 cases: default/None/empty hook × before-first/between renders) | pass. The spy records `bool(helper)`, `bool(helper.layout)`, `len(helper)` and caller identity at `get_attributes`, and asserts `(True, True, 0, False)`. `render_layout` follows on every render, so the real tag dispatches with zero fields. |
| M-OUTER-HELPER-PAGE: enclosing helper and page are separate owners | `test_crispy_buttons.py::test_enclosing_helper_overlays_are_never_page_layers` | pass. Setup: page P, outer helper H, middle helper OF, and a current helper with `view=None`. Results: the inner controls get P's signature, never H or OF. With page `None` or no page, the settings map is used. An explicit inner form or helper owner still wins over P. |
| L-FORMSET-PAGE-CONTEXT: recursive Formsets/inclusion transport | `test_formset_page_tier_is_transported_exactly` (none/absent/ordinary/falsey/page), `test_formset_rows_use_the_row_form_then_row_helper_then_page`, `test_standalone_cv_x_formset_derives_the_page_tier` | pass. The row, the parent and the recursive child all receive the same page fallback through `Formsets.render`, then `formsets.html`, then `cv_x_formset`, then the row crispy render. The caller context is unchanged. |
| L-UNREGISTERED-FORM-ICON: direct unknown prefix and renderer counts | `test_form_button_checks.py::test_unknown_direct_prefix_and_unusable_renderer_are_w292`, `test_icon_availability_predicate`, `test_strict_missing_icon_raises_naming_the_kind[…unknown-prefix…]`, `test_counting_inline_renderer_runs_once_per_icon_render[icon,both]`, `test_counting_renderer_is_not_called_in_label_mode_or_checks`, `test_host_form_renders_without_inline_probes_or_false_fallback` | pass. `unknown:save` and an unusable renderer produce W292 in checks. At render time, strict mode raises and non-strict mode logs and falls back to the label. The counting renderer runs exactly once per icon/both render and zero times in label mode and in checks. Host opt-outs render without probes. |

This shard also contains the three delete tests in §4: 102 passed, exit 0, 1.79 s.

## 6. Requirement traceability (FORM-01 … FORM-13)

| Req | Producing commits | Evidence (all passing in the measured full suite unless marked) | Docs |
|---|---|---|---|
| FORM-01 | `2956f3e`, `98b71ed` | §3 history; `test_form_buttons_golden.py::test_form_button_baselines` | 06-SPEC.md "Golden history" |
| FORM-02 | `df2308b`, `648b36b` | `test_button_data.py::test_form_location_contract_constants`, `test_form_result_keys_and_presence`, `test_form_rejects_*`; `test_button_classes_templates.py` (the `{% cv_button %}` tag never renders the form location) | buttons.md "The form leaf contract" |
| FORM-03 | `df2308b`, `0bac48e` | `test_crispy_buttons.py::test_form_floor_selects_the_body`; `test_icon_host_leaves.py::test_form_element_{icon,both}_mode`, `test_form_label_mode_suppresses_every_icon` | buttons.md "Forms" |
| FORM-04 | `df2308b`, `0bac48e` | `test_icon_host_leaves.py::test_form_host_icon_goes_on_the_button`, `test_form_host_slot_none_or_empty_switches_the_icon_off`, `test_form_host_classes_are_escaped_attributes`; `test_button_classes.py` (key count 73) | buttons.md key table |
| FORM-05 | `df2308b`, `9e19f9a`, `242f3d7` | `test_crispy_buttons.py::test_constructor_visible_legacy_state_is_crispys`, `test_template_precedence`, `test_reserved_attributes_resolve_to_one`; crispy_floor 1877×2 | theme.md "Custom form-button templates" |
| FORM-06 | `552c9e7`, `d43a206`, `e009205` | §3 golden diffs; §4 payload; `test_filter.py::test_filter_hidden_controls_unchanged`; JS `modal.test.js` native submitter suite | migrating-1.0.md "Form buttons" |
| FORM-07 | `df2308b`, `9e19f9a` | `test_crispy_buttons.py::test_layout_values_stay_literal` (includes `{{ request.user }}` in both body and value), `test_hostile_literals_never_create_nodes_or_attributes` | buttons.md "Literal text" |
| FORM-08 | `d43a206`, `66c5e9c`, `2bfefb1` | `test_filter.py::test_filter_endpoint_renders_apply_and_reset_as_leaf_buttons`, `test_filter_endpoint_fields_then_actions_then_hidden_wrapper`; JS `list.filter.test.js` reset suite; browser §9 | list_view.md "Custom filter helpers" |
| FORM-09 | `0bac48e`, `0960031` | `test_icons_registry.py::test_form_icon_defaults`; `test_crispy_buttons.py::test_kind_default_icons`, `test_workflow_form_uses_the_workflow_icon`, `test_per_form_submit_icon_wins` | icons.md "Form buttons" |
| FORM-10 | `379d079`, `0960031`, `d43a206`, `648b36b` | `test_crispy_buttons.py::test_package_forms_render_their_semantic_icons[both/icon]`; `test_filter.py::test_filter_actions_honor_the_list_view_form_modes`; browser §9 (both/icon on save, delete, cancel and both filter buttons) | action_menus.md "Form label-mode resolution" |
| FORM-11 | `379d079`, `b8df8c1`, `d8c9871` | `test_action_label_mode_config.py::test_form_maps_are_selected_whole`, `test_settings_map_reaches_the_leaf_and_only_the_floor_is_live`, `test_view_map_reaches_the_endpoint`; owner tests in §5 | settings.md, action_menus.md |
| FORM-12 | `d8c9871`, `648b36b` | `test_form_button_checks.py` (E211/E210/W291/E106/W292, strict raise, logged fallback) | buttons.md check rows; action_menus.md "Form checks" |
| FORM-13 | `b9b9f92` (+ this record) | `test_label_mode_docs.py::test_form_buttons_breaking_entry_pairs_with_migration`, `test_example_enables_form_both_only`; mkdocs strict; example gates §8; downstream follow-up §10 | CHANGELOG Breaking, migrating-1.0.md |

## 7. Decision traceability (D-01 … D-18) and threats

| Decision | Evidence |
|---|---|
| D-01 / D-02 legacy `add_input()` keeps rendering, quietly | `test_crispy_buttons.py::test_legacy_helper_inputs_stay_inputs_without_warnings`, `test_filter_legacy_add_input_controls_stay_quiet_inputs` (caplog empty); list_view.md legacy path |
| D-03 field-only helper, actions exactly once | `test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once`; `test_form_button_docs.py::test_documented_field_only_helper_appends_the_stock_actions_once`; `test_filter.py::test_filter_endpoint_repeated_requests_never_accumulate_actions` |
| D-04 `get_form_actions()` replace/empty/None | `test_filter_action_hook_none_empty_and_equal_labels`; `test_documented_replacement_hook_keeps_fields_and_hidden_inputs` |
| D-05 / D-07 / D-08 `template=` > subclass > bundled, `%s` pack | `test_crispy_buttons.py::test_template_precedence[Submit,Button,Reset]` (includes `%s/custom/pack.html`) |
| D-06 `cv_*` context, no `input` | `test_custom_template_gets_only_normalized_fields` (outer `input=` is not visible) |
| D-09 / D-11 / D-12 owner order, ordinary owner stops, no warnings | `test_owner_priority`, `test_enclosing_helper_overlays_are_never_page_layers`, `test_private_helper_owner_entry_wins_for_its_invocation_only` (warnings as errors) |
| D-10 no owner: setting map, then floor | `test_formset_page_tier_is_transported_exactly[none,absent]`; `test_settings_map_reaches_the_leaf_and_only_the_floor_is_live` |
| D-13 lazy `form` floor `label`, whole maps | `test_label_mode.py::test_form_floor_is_lazy_and_nested`, `test_form_floor_invalid`; `test_form_maps_are_selected_whole` |
| D-14 normalized contract, hidden label/title/tooltip | `test_form_result_keys_and_presence`; `test_form_element_icon_mode`; browser §9 accessible names |
| D-15 literal values, Breaking/migration | `test_layout_values_stay_literal`, `test_hostile_literals_never_create_nodes_or_attributes`, `test_documented_pill_template_renders_literal_text`; `test_form_buttons_breaking_entry_pairs_with_migration` |
| D-16 icon mapping and diagnostics | `test_kind_default_icons`, `test_workflow_form_uses_the_workflow_icon`, `test_form_button_checks.py` |
| D-17 baselines first, payload kept, example `both`, downstream recorded | §3, §4, `test_example_enables_form_both_only`, §10 |
| D-18 Phase 1/2 contracts verified on the executing branch | 06-SPEC.md "Prerequisite evidence" (HEAD `49f44cd`, 201 passed); those contracts' tests are part of the measured 4445 |

**Threat register (ASVS L1; high blocks).** All 18 threats in the phase plans have the disposition `mitigate`. The
high-severity ones were re-run explicitly in the high-threat shard (109 passed, exit 0) plus the JS shard
(`06-js-verify.sh tests/js/modal.test.js tests/js/viewset.test.js tests/js/list.filter.test.js`: 3 files,
123 tests passed).

| Threat | Sev | Measured mitigation evidence | Status |
|---|---|---|---|
| T-06-02 leaf/attributes injection | high | `test_hostile_literals_never_create_nodes_or_attributes`, `test_layout_values_stay_literal` | mitigated |
| T-06-03 value compiled as template | high | `test_layout_values_stay_literal` (`{{ request.user }}` stays literal in body and value) | mitigated |
| T-06-05 owner confusion | high | §5 owner tests, `test_interleaved_owners_do_not_leak` | mitigated |
| T-06-09 shared filter layout mutation | high | `test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once`, §5 truthiness test | mitigated |
| T-06-13 modal FormData/CSRF | high | JS `modal.test.js` native submitter suite (CSRF and confirm kept, only the clicked submitter sent) | mitigated |
| T-06-15 published template recipe | high | `test_documented_pill_template_renders_literal_text` (hostile literal, no `<script>`, no extra attributes) | mitigated |
| T-06-SC dependency installation | high | No package installed or changed in 06-09. The JS wrapper re-verified the lock sha256 and 71 lock-matched packages. Floor sessions installed only the declared pins. | mitigated (see open advisory below) |
| T-06-01/04/06/07/08/10/11/12/14/16/17 | medium | §3; `test_reserved_attributes_resolve_to_one`; `test_interleaved_renders_of_one_shared_adapter_are_independent`; `test_form_host_classes_are_escaped_attributes`; `test_slot_selects_the_semantic_kind_not_the_name`; `test_filter_hidden_controls_unchanged`; `test_checks_never_instantiate_forms_or_helpers`; `test_non_strict_missing_icon_logs_and_uses_the_label`; viewset/list.filter JS suites; the Breaking pairing test; this record | mitigated |

**No unresolved high or critical form-render security finding is reported as passed.** One related item remains
open and is **not** a form-render finding: WINDOWS #6 / `deferred-items.md`, high-severity `npm audit`
advisories in the transitive dev-only `undici` (via jsdom). It affects only the JS test harness, not shipped code.
It is deferred to a separate dependency-update change because Phase 06 forbids lockfile changes. It remains
`open` and is not marked fixed here.

## Specless edge classifier: unresolved assumptions (kept visible)

The source edge JSON reports `applicable=30`, `unclassified=2`. The 28 classified edges are resolved by the tests
already cited. The two unclassified rows are **not** reclassified as resolved here:

| Requirement | Category | Status | Note |
|---|---|---|---|
| FORM-01 | unclassified | FLAGGED, unresolved | The history requirement itself is verified (§3). The classifier's edge shape for it is still unknown. |
| FORM-02 | unclassified | FLAGGED, unresolved | The form contract itself is verified (§6). The classifier's edge shape for it is still unknown. |

## 8. Docs, JS, lint, format and example gates (Task 2)

| Gate | Command | Exit | Result |
|---|---|---|---|
| Strict docs | `.venv/bin/mkdocs build --strict` | 0 | built in 0.93 s, 0 warnings (output: gitignored `site/`) |
| Full JS | `bash .planning/phases/06-form-button-leaf/06-js-verify.sh` | 0 | 8 files, 223 tests passed in 2.90 s. Runtime, lock sha256, 71 packages and 72 engine ranges re-asserted. |
| Lint | `.venv/bin/ruff check` (run as `--no-fix`, so nothing is rewritten) | 0 | All checks passed |
| Format, whole repo | `.venv/bin/ruff format --check` | **1** | **Not green.** 9 files would be reformatted, 653 already formatted. See below. |
| Format, code | `.venv/bin/ruff format --check src tests examples noxfile.py` | 0 | 451 files already formatted |
| Format, files changed in Phase 06 | every `*.py` and `*.md` added or modified in `49f44cd..HEAD` | 0 | 31 Python and 24 Markdown files already formatted |
| Example system checks (URLconf registered) | `cd examples/bootstrap5 && ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q` | 0 | 1 passed |
| Example docs sync | `cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q` | 0 | 36 passed |
| Example consumer (L-EXAMPLE-COVERAGE) | `cd examples/bootstrap5 && ../../.venv/bin/pytest test_i18n.py project/tests.py::HomePageTest::test_every_feature_landing_page_renders test_doc_links.py -q` | 0 | 72 passed, 1 warning. Collected: `test_i18n.py` 11, `HomePageTest::test_every_feature_landing_page_renders` 1, `test_doc_links.py` 60. |

**Whole-repo format gate: not passed (pre-existing, unrelated).** These are the 9 files, all Markdown
planning documents whose embedded Python code blocks ruff would reformat:

- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/phases/01-label-mode-defaults/01-PATTERNS.md`
- `.planning/phases/01-label-mode-defaults/01-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-VERIFICATION.md`
- `.planning/phases/06-form-button-leaf/06-PATTERNS.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/STACK.md`

How this was established as baseline drift: each file was piped from the phase-start commit `49f44cd` through
`ruff format --check --stdin-filename`, and all 9 already failed there. `git diff 49f44cd HEAD` is empty for all
9, so Phase 06 did not change any of them. `06-PATTERNS.md` is a planning artifact last changed in `b8d2b4f`,
before execution started. This is the same drift as WINDOWS #4, which stays open. The files were not
reformatted, because they are outside this phase's scope.

**Example settings were loaded.** The example `pytest.ini` sets `DJANGO_SETTINGS_MODULE = project.settings`.
Importing those settings yields `CRUD_VIEWS_LABEL_MODE_DEFAULTS == {'form': 'both'}`, which is the 06-08 change.
`test_i18n.py::test_demo_pages_render_german` asserts that the translated create-submit value
`value="Sichern"` is present, and it passed. The single warning is Django's `UnorderedObjectListWarning` for
the workflow example's `Campaign` list. It comes from pagination and is unrelated to form buttons. The root
`pytest tests` run does not collect this example tree, so these results are separate evidence. They do not
replace the root suite, and the root suite does not replace them.

**Repeatability.** After each gate (parallel and one-process pytest, nox, JS, ruff, mkdocs, the three example
runs, the browser runs), `git status --porcelain` matched the pre-run snapshot. Only the unrelated
`.codegraph/.gitignore` modification appears, and it was there before 06-09 started. The gates write only to
ignored or scratch locations: `site/`, `.nox/`, `node_modules/`, and the session scratchpad.

## 9. Browser acceptance (real Chromium, automated)

**Harness.** Headless Chromium `HeadlessChrome/149.0.7827.55` (the locally installed Playwright
chrome-headless-shell build, run with `--no-sandbox` because the host forbids unprivileged user namespaces). It
was driven over the Chrome DevTools Protocol by a scratch Node script that uses only built-in WebSocket and
fetch; no package was installed. Each mode ran in isolation:

- its own `runserver` process (ports 8771/8772/8773)
- its own settings module (`from project.settings import *`, overriding only `DATABASES` with a scratch
  SQLite copy and `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": <mode>}`)
- its own seeded database copy (`manage.py migrate` + `manage.py seed`)
- a scratch browser profile

Real pointer events (`Input.dispatchMouseEvent`) and key events (`Input.dispatchKeyEvent`) were used. Accessible
names come from Chromium's accessibility tree (`Accessibility.getPartialAXTree`). Pages are the example's
`/library/author/create/`, `/library/author/<pk>/delete/`, `/library/author/?sort=last_name&dir=desc` (filter)
and `/showcase/recipe/` (the modal delete; `RecipeDeleteView.cv_modal = True`). The run was logged in as the
seeded demo user `alice`. No console errors or uncaught exceptions occurred in any mode.

| Check | label | both | icon |
|---|---|---|---|
| Save (create) | `<button type=submit name=submit value=Save id=submit-id-submit class="btn btn-primary">`, text only, AX name "Save" | icon + visible text, AX "Save" | icon + `.visually-hidden` "Save", `data-cv-tooltip="form"`, 40×38 px, AX "Save" |
| Delete (delete page) | `name=delete value=Delete id=submit-id-delete`, AX "Delete" | icon + text, AX "Delete" | icon + hidden label, AX "Delete" |
| Cancel | `type=button name=reset value=Cancel data-cv-cancel-url=/library/author/`, AX "Cancel" | icon + text, AX "Cancel" | icon + hidden label, AX "Cancel" |
| Apply / Reset filter | `#filter-button` submit / `#filter-button-reset` reset, AX "Apply Filter" / "Reset Filter" | icon + text | icon + hidden labels; AX names unchanged |
| Keyboard focus (Tab from top) | Save reached after 16 Tabs, Cancel on the next Tab, both `:focus-visible`; filter Apply then Reset, both `:focus-visible` | same | same |
| Tooltip on keyboard focus | none generated (label mode) | none generated (both mode shows text) | the tooltip bound to the trigger (`aria-describedby`) shows "Save", "Cancel", "Apply Filter", "Reset Filter" |
| Cancel by pointer on a nested child | click on the label `<span>` navigates to `/library/author/` | click on the `<i>` icon navigates to the list | click on the `<i>` icon navigates to the list |
| Cancel by keyboard (Enter on focused Cancel) | navigates to the list | navigates to the list | navigates to the list |
| Filter apply | `?first_name=a&last_name=&submit=Apply+Filter&sort=last_name&dir=desc` | same | same |
| Filter reset (click on nested child) | `?sort=last_name&dir=desc`: filter value cleared, sort/dir kept | same | same |
| Modal submit (click on the delete button's nested child) | modal opened from the recipe list's Delete trigger (`data-cv-modal="true"`); `confirm` checked; clicking the `<span>` posted, redirected to `/showcase/recipe/` with "Deleted recipe “Soufflé au Fromage”" | clicking the `<i>` deleted "Lamb Tagine" | clicking the `<i>` deleted "Lamb Tagine"; the modal buttons carry the hidden labels "Delete" / "Cancel" |

Note on cancel targets: sometimes cancel landed on `/library/author/?sort=last_name&dir=desc` rather than the
bare `/library/author/`. That is the existing cancel-origin behavior returning to the list state remembered in
that browser profile, not a form-button change. The `data-cv-cancel-url` attribute itself was always
`/library/author/`.

**Observed with automation but not accepted by automation (human-needed, pending):**

1. **Tooltip on pointer hover.** Not observed. In this headless harness, synthetic `mouseMoved` events over the
   lower-page form buttons did not set `:hover`, although `elementFromPoint` hit the button's icon and click
   events at the same coordinates worked. The same probe did show a hover tooltip on a context button near the
   top of the page. The focus-triggered tooltips above use the same Bootstrap Tooltip instance, so this looks
   like a harness limitation. It is still **not verified**.
2. **Visual quality** in all three modes: spacing, icon alignment, hidden-label clipping, the both-mode icon gap,
   and how icon-only buttons look next to their siblings. This includes the label fallback for a missing icon
   (06-06 D7).
3. **Screen-reader announcement.** Accessible names come from the AX tree only. No assistive technology was run.
4. **Readability of the migration prose** for downstream consumers (06-08 D5).

These items stay **pending** until a human observes them. The phase verification step owns that.

## 10. Downstream theme follow-up (recorded, not performed)

No downstream repository was opened, named or edited. A consuming theme with its own icon library should do the
following:

1. **Map the three new semantic icon names** through `CRUD_VIEWS_ICONS` or the theme's icon preset:
   - `save` to the library's `device-floppy` glyph
   - `cancel` to its `x` glyph
   - `filter-reset` to its `filter-off` glyph

   Add those glyph assets to the theme's icon bundle or sprite if it ships a subset. `delete`, `filter` and
   `workflow` already exist.
2. **Update selectors and assertions** that target `input[type=submit]`, `input[type=button]` or
   `input[type=reset]` for crispy layout controls, so they target `button[...]`:
   - CSS
   - JS
   - template tests
   - end-to-end tests

   Selectors by id (`#submit-id-submit`, `#filter-button`, `#filter-button-reset`) and by name/value keep
   working, because those attributes are unchanged.
3. **Update the theme's own stock delete-form assertions.** The delete control is now
   `<button type="submit" name="delete" value="Delete" …><span>Delete</span></button>`. The POST still carries
   `confirm` plus the clicked `delete=Delete`.
4. **Non-Bootstrap themes only:** set `CRUD_VIEWS_BUTTON_CLASSES["form:hidden-label"]` to the theme's
   screen-reader-only class, and the `form:<kind>` keys to its button classes.
5. **No new template override is required.** The bundled leaf `crud_views/tags/button/form.html` is
   theme-neutral: every class comes from `{% cv_button_class %}` and every icon from `{% cv_icon %}`, both of
   which the theme already configures. A theme that had overridden crispy's `bootstrap5/layout/baseinput.html`
   for layout buttons must move that markup to a form-button template that uses `cv_*` variables
   (docs/reference/theme.md "Custom form-button templates"). Legacy `helper.add_input()` controls still
   use crispy's input template (D-01).

## 11. Acceptance status

- **Accepted (automated evidence above):** FORM-01 … FORM-13 Python, JS, floor, docs, lint, code formatting,
  example and browser behavior. The two unclassified edge assumptions stay flagged.
- **Not green, pre-existing and recorded:** the whole-repo `ruff format --check` (9 planning Markdown files,
  WINDOWS #4); the dev-only `undici` audit advisory (WINDOWS #6).
- **Pending human observation:** §9 items 1–4.
