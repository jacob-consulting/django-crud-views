---
phase: 06-form-button-leaf
verified: 2026-10-28T14:14:47Z
status: passed
score: 42/42 must-haves verified
covered_files: [".planning/phases/06-form-button-leaf/06-01-PLAN.md", ".planning/phases/06-form-button-leaf/06-01-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-02-PLAN.md", ".planning/phases/06-form-button-leaf/06-02-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-03-PLAN.md", ".planning/phases/06-form-button-leaf/06-03-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-04-PLAN.md", ".planning/phases/06-form-button-leaf/06-04-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-05-PLAN.md", ".planning/phases/06-form-button-leaf/06-05-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-06-PLAN.md", ".planning/phases/06-form-button-leaf/06-06-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-07-PLAN.md", ".planning/phases/06-form-button-leaf/06-07-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-08-PLAN.md", ".planning/phases/06-form-button-leaf/06-08-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-09-PLAN.md", ".planning/phases/06-form-button-leaf/06-09-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-10-PLAN.md", ".planning/phases/06-form-button-leaf/06-10-SUMMARY.md", "CHANGELOG.md", "docs/getting_started/tutorial-5-filters-permissions.md", "docs/migrating-1.0.md", "docs/reference/action_menus.md", "docs/reference/buttons.md", "docs/reference/icons.md", "docs/reference/javascript.md", "docs/reference/list_view.md", "docs/reference/settings.md", "docs/reference/theme.md", "examples/bootstrap5/project/settings.py", "noxfile.py", "src/crud_views/lib/button_classes.py", "src/crud_views/lib/crispy/buttons.py", "src/crud_views/lib/crispy/form.py", "src/crud_views/lib/formsets/layout.py", "src/crud_views/lib/icons.py", "src/crud_views/lib/settings.py", "src/crud_views/lib/view/action_menu.py", "src/crud_views/lib/view/base.py", "src/crud_views/lib/view/button_data.py", "src/crud_views/lib/view/buttons.py", "src/crud_views/lib/view/label_mode.py", "src/crud_views/lib/views/list.py", "src/crud_views/lib/viewset/__init__.py", "src/crud_views/static/crud_views/js/tooltip.js", "src/crud_views/templates/crud_views/tags/button/form.html", "src/crud_views/templatetags/crud_views.py", "src/crud_views/templatetags/crud_views_formsets.py", "src/crud_views_workflow/lib/forms.py", "tests/js/list.filter.test.js", "tests/js/modal.test.js", "tests/js/viewset.test.js", "tests/test1/golden/form_buttons/create.html", "tests/test1/golden/form_buttons/delete.html", "tests/test1/golden/form_buttons/filter.html", "tests/test1/golden/form_buttons/update.html", "tests/test1/golden/form_buttons/workflow.html", "tests/test1/test_action_label_mode_config.py", "tests/test1/test_button_classes.py", "tests/test1/test_button_classes_templates.py", "tests/test1/test_button_data.py", "tests/test1/test_crispy_buttons.py", "tests/test1/test_filter.py", "tests/test1/test_form_button_checks.py", "tests/test1/test_form_button_docs.py", "tests/test1/test_form_buttons_golden.py", "tests/test1/test_icon_host_leaves.py", "tests/test1/test_icons_registry.py", "tests/test1/test_label_mode.py", "tests/test1/test_label_mode_docs.py"]
covered_digest: "v4:sha256:6d0099cb7d0cc399cd62ccd7b63b364ab665bc2c0a2bb58845ff860a2fd0066b"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 42/42
  previous_verified: 2026-10-28T10:51:09Z
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  human_items_resolved:
    - "Hover tooltips on form buttons in icon mode — 06-UAT.md test 1: pass"
    - "Visual quality of the label/both/icon modes incl. the copied-layout path — 06-UAT.md test 2: pass"
    - "Screen-reader announcement in icon mode — 06-UAT.md test 3: pass"
    - "Migration-guide readability — 06-UAT.md test 4: pass; the IN-02 caveat noted there is closed by 92d5430"
---

# Phase 6: Form-button leaf Verification Report

**Phase Goal:** Crispy form buttons render as real `<button>` elements through a crud_views leaf, share the action-button label-mode and class-table contract, and are safe against template injection. With no configuration, POST data is unchanged.
**Verified:** 2026-10-28T14:14:47Z
**Status:** passed
**Re-verification:** Yes — after the code-review fix round (commits `aed6003`, `92d5430`, `d75fb31`) and the user's UAT (`a2ea77c`)

Checked against the working tree at HEAD `a2ea77c` on branch `introduce-gsd` (working tree clean for `src`, `tests`, `docs`, `examples`). The previous report (`verified: 2026-10-28T10:51:09Z`, committed `8c73ced`, 42/42, `human_needed`) had no `gaps:` section, so this pass is a staleness re-verification, not a gap-closure one: `git diff --stat 8c73ced..HEAD -- src tests docs examples CHANGELOG.md noxfile.py` lists exactly the five files the orchestrator named (`docs/migrating-1.0.md` +4, `docs/reference/list_view.md` +5/-2, `src/crud_views/lib/views/list.py` +7/-1, `tests/test1/test_button_data.py` +5/-11, `tests/test1/test_crispy_buttons.py` +26). Every truth those files support was re-verified in full (three levels plus behavior); every other truth got a regression check (file unchanged since the previous `verified:` timestamp plus a named-test re-run where cheap). Nothing was taken from `06-REVIEW-FIX.md` or the SUMMARYs: each fix claim was re-derived by reading the diff, running the named tests here, and an independent render script outside pytest. The orchestrator's full-suite result (`pytest tests -q -n auto`: 4632 passed, 1 skipped) is context only.

## Goal Achievement

### Observable Truths

Roadmap Success Criteria first (SC1-SC5), then the plan-level truths (T6-T35) and the 06-10 gap-closure truths (G1-G7), numbered as in the previous report. "regression" = unchanged file + named test re-run; "full" = three-level verification this pass because a supporting file changed.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| SC1 | With nothing configured, create/update/delete/cancel and both filter buttons render as `<button type="…">` with the same text, classes, `name`, `value`, `id`; `test_delete` posts `{"delete": "Delete"}` unchanged; `#filter-button-reset` preserved; before-change goldens show the diff | ✓ VERIFIED (regression) | Goldens, `form.html`, `crispy/buttons.py`, `button_data.py` unchanged since `8c73ced`. The only `list.py` change wraps `copy.deepcopy` in a `try` and re-raises; the success path is byte-identical. Ran `test_form_buttons_golden.py` (all) + `test_crud.py::test_delete_author`: pass (73-pass sweep C) |
| SC2 | `{"form": "both"}` shows icon + text; `{"form": "icon"}` shows icon-only with visually hidden label, `title`, `data-cv-tooltip="form"`; setting → ViewSet → view maps apply, including on the copied filter-layout path | ✓ VERIFIED (regression) | `label_mode.py`, `button_data.py`, `crispy/buttons.py`, `form.html` unchanged. Ran `test_copied_filter_layout_keeps_kind_icons` (12) + `test_copied_adapter_*` (10) in sweep A: pass. Independent probe renders an icon-mode cancel `Button` with `title` + `data-cv-tooltip="form"` (attribute list below). UAT tests 1-2 confirmed hover tooltips and the visual result on a real pointer |
| SC3 | A label or value containing `<b>`, `"><script>` or `{{ request.user }}` renders as escaped plain text in body and `value` | ✓ VERIFIED (regression) | Escaping boundary (`_literal()`, adapter `render()` never calling `BaseInput.render`) untouched. Ran `test_form_button_docs.py` (hostile-literal recipes) in sweep C: pass |
| SC4 | Workflow submit shows `workflow` icon; per-form `submit_icon` wins; icon-only form button with no icon → W292, raises in strict mode, else logs and renders label; E210/E211/W291 cover form maps | ✓ VERIFIED (full) | `button_data.py:246-261` unchanged. The IN-03 rewrite of `test_form_icon_normalization_keeps_nonblank_strings_exactly` removed the dead `else` branch and now asserts unconditionally that the mode is kept, the string is stored by identity and no warning is logged (15 cases); the unavailable-string policy is still asserted by `..._unavailable_nonblank_string_is_not_none`. Ran `-k form_icon_normalization`: 164 passed |
| SC5 | CHANGELOG `### Breaking` entry and `docs/migrating-1.0.md` "Form buttons" section exist; example shows `both`; Tabler follow-up in the acceptance note | ✓ VERIFIED (full) | `CHANGELOG.md` and the example unchanged. `docs/migrating-1.0.md:240-243` gained the IN-02 paragraph inside the existing "Form buttons" bullet (no new Breaking entry needed: it documents existing behavior). Ran `test_form_button_docs.py` + `test_label_mode_docs.py`: pass. UAT test 4 (migration-guide readability) passed |
| T6 | D-17/D-18: spec authored after Phase 1/2 contracts; baselines committed before every product edit | ✓ VERIFIED (regression) | Unchanged history; the fix round added no contract change |
| T7 | D-01..D-12 settled in the spec and implemented | ✓ VERIFIED (regression) | T12/T16/T20/T21 re-checked below |
| T8 | D-13/D-14: standalone package Submit renders via `cv_button_data(ctx, "form")`; third-kind validation | ✓ VERIFIED (regression) | `crispy/buttons.py:166-172` unchanged; independent probe renders `Submit("submit", "Go", …)` through the leaf |
| T9 | `{% cv_button "form" %}` raises before resolution | ✓ VERIFIED (regression) | `templatetags/crud_views.py` unchanged |
| T10 | Public form-module imports work before `django.setup()` | ✓ VERIFIED (regression) | `crispy/buttons.py` unchanged; `list.py` added no module-level import (`copy` already imported) |
| T11 | D-15: empty, Unicode, lazy, SafeString and template-looking values remain literal | ✓ VERIFIED (regression) | As SC3 |
| T12 | D-05..D-08: template precedence, `%s` pack substitution, `cv_*`-only custom context | ✓ VERIFIED (regression) | Unchanged files |
| T13 | D-14/D-17: repeated and interleaved renders preserve names/values/IDs/CSS without mutating adapters | ✓ VERIFIED (regression) | Adapter unchanged; `test_copied_filter_layout_keeps_kind_icons` (3 interleaved rounds) in sweep A: pass |
| T14 | D-13: `form` in `LOCATIONS`/`LABEL_MODE_DEFAULTS`; `form:hidden-label`, `form:icon-host` keys | ✓ VERIFIED (regression) | `button_classes.py` unchanged |
| T15 | D-13: form maps selected whole; floor live, map import-time | ✓ VERIFIED (regression) | Unchanged files; independent probe's `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"})` took effect on the floor |
| T16 | D-09..D-12: owner = first non-None of render form `cv_view` → helper → page | ✓ VERIFIED (regression) | `list.py:177-178` (`context.push({_CV_HELPER_OWNER: …})`) unchanged |
| T17 | D-14: all five kinds support the three bodies; icon mode has hidden label, `title`, form tooltip marker | ✓ VERIFIED (regression) | `form.html` unchanged; probe shows `title`/`data-cv-tooltip` on an icon-mode cancel |
| T18 | D-16: kind icons resolve independently of the submitted name for every layout-path package button; missing-icon policy fires only for genuinely unavailable icons | ✓ VERIFIED (regression) | `crispy/buttons.py:131` `_cv_kind_icon` bool unchanged; sweep A (22 copied-adapter/layout cases): pass |
| T19 | Empty/disabled host classes no inline duplicate; repeated renders follow current registry; no cross-form `submit_icon` leak | ✓ VERIFIED (regression) | Unchanged files |
| T20 | D-01/D-02: custom `add_input` controls stay legacy inputs; hidden sort/order/direction inputs unchanged | ✓ VERIFIED (full) | `list.py:109-121` (`add_input(layout.Hidden(…))`) unchanged by `aed6003`; `test_filter.py` (all) in sweep C: pass |
| T21 | D-03/D-04: declared layouts cloned per instance; actions exactly once; None omits / empty kept; `helper.form` identity kept | ✓ VERIFIED (full, behavior test) | `list.py:153-159`: `copy.deepcopy(current)` kept; `except (TypeError, copy.Error)` re-raises `TypeError(f"{type(self).__name__}.layout must be deep-copyable (each helper renders its own copy): {exc}") from exc`. Success path identical. Ran `test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once`, `test_filter_custom_layout_class_keeps_its_behavior_while_isolated`, new `test_filter_layout_that_cannot_be_deep_copied_names_the_helper[class|assigned]`: pass. Independent probe: class layout with a `threading.Lock` member raises at helper creation naming `ProbeHelper`, chained cause `TypeError`; assigned layout raises at `get_attributes()` naming `Plain`; the caller's layout keeps its 2 fields; a copyable layout is still isolated (`h.layout is not ok`) |
| T22 | D-09/D-14/D-17: default Apply/Reset use the leaf with stable IDs; custom helper constructors receive `(view, request)` | ✓ VERIFIED (regression) | `list.py:102-133` unchanged |
| T23 | D-17: before/after filter golden evidence uses the identical extractor | ✓ VERIFIED (regression) | `test_form_buttons_golden.py` unchanged; pass |
| T24 | D-16: form-only E211/E210/W291; settings E106; ViewSet validator | ✓ VERIFIED (regression) | Unchanged files |
| T25 | D-16: static W292 inspects the right controls and never instantiates forms/helpers | ✓ VERIFIED (regression) | `view/buttons.py` unchanged |
| T26 | D-15/D-16: dynamic missing-icon policy in icon mode (strict raise / log + label); empty label keeps empty payload | ✓ VERIFIED (full) | `button_data.py:246-261` unchanged; the rewritten IN-03 test no longer branches on its own outcome; `..._strict_icon_mode_raises_naming_none`, `..._lenient_icon_mode_logs_and_uses_the_label`, `..._unavailable_nonblank_string_is_not_none` still assert the policy unconditionally (164 passed) |
| T27 | D-14/D-16: one availability predicate shared by static checks and the normalizer | ✓ VERIFIED (regression) | Unchanged files |
| T28 | D-17: native and modal submission include only the clicked button's name/value; CSRF preserved | ✓ VERIFIED (regression) | No JS or template changed since the previous pass (diffstat); the locked JS gate (123 passed at `8c73ced`) stands |
| T29 | D-14/D-17: nested icon/text clicks cancel once; filter reset keeps `sort`/`order`/`dir` and its stable ID | ✓ VERIFIED (regression) | Same |
| T30 | Expanded form tests pass at crispy 2.0 / crispy-bootstrap5 2023.10 on Django 4.2 and 6.0 | ✓ VERIFIED (regression) | `noxfile.py` unchanged; the fix-round test additions use only `threading`, `crispy_forms.layout.HTML/Layout` and `pytest.raises` (crispy-version-independent); not re-run here (> 10 s, builds two virtualenvs) |
| T31 | Docs keep field-only helper examples, show `FormActions` opt-in and None omission; E108 rows list `LOCATIONS` | ✓ VERIFIED (full) | `docs/reference/list_view.md:169-176`: the field-only `AuthorFilterFormHelper` example kept; the new sentence states the deep-copy requirement and when the `TypeError` fires, which matches `list.py` (`__init__` → `_cv_prepare_layout()` at creation; assigned layout → `get_attributes`/`render_layout` on the next render) and the probe. Docs tests pass |
| T32 | Paired Breaking/migration entries; example `both`; downstream follow-up generic | ✓ VERIFIED (full) | The IN-02 paragraph is additive prose inside the existing "Form buttons" bullet; the Breaking/migration pairing test in `test_form_button_docs.py` passes |
| T33 | Consumers that cleared `helper.inputs` have an executable migration | ✓ VERIFIED (regression) | Recipe test in `test_form_button_docs.py`: pass |
| T34 | Acceptance records baselines, suites, floors, browser flows and downstream follow-up | ✓ VERIFIED (regression) | `06-ACCEPTANCE.md` unchanged since the previous pass; the browser flows it deferred to a human are now recorded as passed in `06-UAT.md` |
| T35 | No unresolved high/critical form-render security finding reported as passed | ✓ VERIFIED (regression) | `06-SECURITY.md` unchanged (18/18 closed); the escaping boundary untouched; the new `TypeError` path discloses only the helper class name and `deepcopy`'s own message |
| G1 | 06-10: package Submit/Reset inside class-level and caller-assigned filter layouts render kind icons through real crispy under both/icon, strict, without warnings | ✓ VERIFIED (full, behavior test) | `test_crispy_buttons.py` gained 26 lines (the IN-01 test) before the 06-10 section; `test_copied_filter_layout_keeps_kind_icons` (12) unchanged and passing in sweep A |
| G2 | 06-10: deep-copied adapters retain slot-derived icons for all five kinds; explicit None/empty and overrides stay distinct | ✓ VERIFIED (regression) | `test_copied_adapter_keeps_icon_contract` (5) + `..._preserves_explicit_icon` (5): pass |
| G3 | 06-10 / FORM-02: the form normalizer emits `cv_icon` as a nonblank `str` or `None` without mutating the caller's context | ✓ VERIFIED (full) | `button_data.py:246-248` unchanged; `test_form_icon_normalization_*` (164, incl. `..._never_mutates_the_input`): pass |
| G4 | 06-10 / D-16: invalid icons quiet in label/both; icon-only strict raises naming `None`; lenient logs; valid strings keep the registry policies | ✓ VERIFIED (full, behavior test) | The rewritten `..._keeps_nonblank_strings_exactly` now asserts `_warnings(caplog) == []` for every parameter, which is a stronger, unconditional check than before; the other four policy tests unchanged: pass |
| G5 | 06-10: repeated/interleaved copied-layout renders preserve isolation, order, one action group, hidden GET controls, IDs/CSS | ✓ VERIFIED (behavior test) | Sweep A; the new IN-01 test additionally asserts the source layout is untouched when the copy fails |
| G6 | 06-10: CR-01/WR-01/WR-02 marked fixed only with measured evidence; IN-01/IN-02/IN-03 explicit | ✓ VERIFIED (full) | `06-REVIEW-DISPOSITION.md` now `open: 0 / total: 6`: IN-01..IN-03 `fixed` sourcing `06-REVIEW-FIX.md`, CR-01/WR-01/WR-02 keep their 06-10 commit/test citations. `verify.commits aed6003 92d5430 d75fb31 48659b2 d1906e1 a2ea77c 35635eb 8c73ced`: `all_valid: true`. Each IN fix re-derived here: IN-01 code+docs+test (T21/T31), IN-02 docs vs. runtime attribute order (probe), IN-03 test diff (SC4/G4) |
| G7 | 06-10: FORM-01/FORM-02 unclassified assumptions stay flagged | ✓ VERIFIED (regression) | `06-ACCEPTANCE.md` and `06-10-PLAN.md` unchanged |

**Score:** 42/42 truths verified (0 present, behavior-unverified)

### Deferred Items

None. Phase 7 ("Theme-surface stability policy") addresses public theme-name documentation only; nothing from this phase is deferred to it.

### Advisory (New Scope, Unevidenced)

Re-verification ran, so this section is reported explicitly. No new-scope 🛑 Blocker was raised in Step 7, so nothing was downgraded under the convergence evidence gate (#3304).

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| — | None | — | — |

### Required Artifacts

`gsd_run query verify.artifacts 06-10-PLAN.md`: `all_passed: true`, 7/7 (exit 0). The nine earlier plans' artifacts were tool-verified in the previous passes and none of their files changed since except the five listed below, which were re-checked by hand at all levels.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/crud_views/lib/views/list.py` | Per-instance deep-copied filter layouts; stock Apply/Reset through the leaf; now a `TypeError` naming the helper when the layout cannot be deep-copied | ✓ VERIFIED | `:153-159` `try: copy.deepcopy(current) except (TypeError, copy.Error) … raise TypeError(…) from exc`; docstring `:145` states the requirement. Wired: `ListViewFilterFormHelper` is the filter helper base used by `ListViewTableFilterMixin` and documented in `docs/reference/list_view.md`; the IN-01 test instantiates it through `_new_filter_helper`/`_filter_helper_class` and renders through the real `{% crispy %}` tag |
| `tests/test1/test_crispy_buttons.py` | Copied-layout/adapter regressions plus the IN-01 non-copyable-layout test | ✓ VERIFIED | `:1732-1755` `test_filter_layout_that_cannot_be_deep_copied_names_the_helper[class|assigned]`: asserts the message regex, `__cause__` is a `TypeError`, `len(locked.fields) == 2`. 26 selected cases pass; ruff clean |
| `tests/test1/test_button_data.py` | Icon normalization regressions, now without an outcome-dependent branch | ✓ VERIFIED | `:867-874`: unconditional `cv_label_mode == mode`, `cv_icon is icon`, `_warnings(caplog) == []`; 164 cases pass; ruff clean |
| `docs/migrating-1.0.md` | "Form buttons" section with the `<input>` → `<button>` migration, now stating extra-attribute order | ✓ VERIFIED | `:240-243`: after `type`, `name`, `value`, `id`, `class` (and cancel URL / icon-only title) in sorted order, boolean attributes last, `data-a` before `data-b`. Matches `form.html` (attribute emission order) + `button_data.py:280` (`flatatt`, which sorts key/value pairs then boolean attributes) and the runtime probe |
| `docs/reference/list_view.md` | Custom filter helper docs, now stating the deep-copy requirement and when it fails | ✓ VERIFIED | `:172-176`; matches `list.py` and the probe. One cosmetic hard line break mid-sentence ("A helper without a `layout`\nrenders …") renders as one Markdown paragraph (ℹ️ Info) |
| `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/view/button_data.py`, `form.html`, `view/buttons.py`, `base.py`, `icons.py`, `button_classes.py`, `crud_views_workflow/lib/forms.py`, `noxfile.py`, other docs, example, goldens, JS | As in the previous report | ✓ VERIFIED (regression) | Unchanged since `8c73ced` (diffstat) |
| `.planning/…/06-REVIEW-DISPOSITION.md`, `06-ACCEPTANCE.md`, `06-VALIDATION.md` | Evidence-backed dispositions / dated acceptance / 06-10 validation rows | ✓ VERIFIED | Disposition updated to `open: 0` with the three IN rows sourcing `06-REVIEW-FIX.md`; the other two unchanged |

### Key Link Verification

`gsd_run query verify.key-links 06-10-PLAN.md` again reports "Target not referenced in source" for all 4 links (exit 0, `all_verified: false`): the verb greps for the target file path inside the source file, which Python imports never contain. Each link was verified by symbol and behavior; only the first touches a changed file.

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `views/list.py` | `crispy/buttons.py` | `_cv_prepare_layout` deepcopy preserves the adapter's omitted-icon boolean | WIRED | `list.py:154` still `copy.deepcopy(current)` on the success path; the new `except` only re-raises. `test_copied_filter_layout_keeps_kind_icons` (12) passes, so copied `Submit`/`Reset` still render `fa-filter`/`fa-rotate-left` |
| `crispy/buttons.py` | `view/button_data.py` | `_cv_button_context` resolves slot defaults before `cv_button_data` normalizes | WIRED (regression) | Both files unchanged |
| `tests/test1/test_crispy_buttons.py` | `tags/button/form.html` | `_filter_render` invokes the real crispy tag | WIRED | `_filter_render` is also what the new IN-01 `assigned` case drives to reach `_cv_prepare_layout` on the next render |
| `06-REVIEW-DISPOSITION.md` | `06-10-SUMMARY.md` / `06-REVIEW-FIX.md` | Fixed findings cite their evidence | WIRED | All six rows cite a source; the three new ones cite `06-REVIEW-FIX.md`, whose commits exist (`verify.commits`) and whose claims were re-derived here |
| `view/buttons.py` | `view/button_data.py` | static W292 and dynamic fallback agree on modes/icons | WIRED (regression) | Unchanged files |
| `docs/migrating-1.0.md` | `form.html` + `button_data.py:280` | documented attribute order matches emitted order | WIRED | Probe: `['type','name','value','id','class','data-a','data-b','formnovalidate']` and, icon-mode cancel, `[…,'class','data-cv-cancel-url','title','data-cv-tooltip','data-a','data-z']` |
| `docs/reference/list_view.md` | `views/list.py` | documented failure point matches code | WIRED | Probe: class layout fails in `__init__`; assigned layout fails at `get_attributes()` |
| All other 06-01..06-09 links | As in the previous report | WIRED (regression) | Source files unchanged |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `form.html` | `cv_type/cv_name/cv_value/cv_id/cv_label` | adapter → `_form_button_data` literals | Yes | ✓ FLOWING |
| `form.html` | `cv_label_mode` | `_cv_form_owner` → `cv_get_action_label_mode("form", kind)` → map/floor | Yes (probe: floor override reached the leaf) | ✓ FLOWING |
| `form.html` | `cv_icon` | `_KIND_ICONS[kind]` / explicit icon / hooks → normalized `str | None` | Yes, incl. deep-copied adapters | ✓ FLOWING |
| `form.html` | `cv_flat_attrs` | caller kwargs → `flatatt` (sorted, booleans last) | Yes (probe) | ✓ FLOWING |
| `form.html` | `cv_cancel_url` | `data_cv_cancel_url` kwarg, cancel kind only | Yes (probe) | ✓ FLOWING |
| `filter.html` golden | hidden `sort/order/dir` | `request.GET` → `add_input(Hidden)` | Yes | ✓ FLOWING |
| `ListViewFilterFormHelper.layout` | prepared instance layout | `copy.deepcopy(class or assigned layout)` | Yes; failure now typed and named | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Sweep A: IN-01 test + 06-10 copied-layout/adapter + layout-isolation regressions | `.venv/bin/pytest -p no:randomly -q tests/test1/test_crispy_buttons.py -k "cannot_be_deep_copied or copied_filter_layout or copied_adapter or filter_class_layout_is_cloned or filter_custom_layout_class"` | 26 passed, 238 deselected | ✓ PASS |
| Sweep B: icon normalization incl. the rewritten IN-03 test | `.venv/bin/pytest -p no:randomly -q tests/test1/test_button_data.py -k form_icon_normalization` | 164 passed | ✓ PASS |
| Sweep C: docs recipes (migrating-1.0.md changed), label-mode docs, filter, goldens, `test_delete_author` | `.venv/bin/pytest -p no:randomly -q tests/test1/test_form_button_docs.py tests/test1/test_label_mode_docs.py tests/test1/test_filter.py tests/test1/test_form_buttons_golden.py tests/test1/test_crud.py::test_delete_author` | 73 passed in 7.47 s | ✓ PASS |
| IN-02 attribute order (label mode) | `.venv/bin/python <scratchpad>/probe_reverify_06.py` (Django configured via `tests/test1/conftest.pytest_configure()`, no pytest) | `Submit("submit","Go",data_b="1",data_a="2",formnovalidate=True)` → `type name value id class data-a data-b formnovalidate` | ✓ PASS |
| IN-02 attribute order (icon-mode cancel) | same script | `… class data-cv-cancel-url title data-cv-tooltip data-a data-z` — extras after the cancel URL and the generated title, sorted | ✓ PASS |
| IN-01 class layout with a `threading.Lock` member | same script | `TypeError` at `ProbeHelper(view, request)`: `ProbeHelper.layout must be deep-copyable (each helper renders its own copy): cannot pickle '_thread.lock' object`; `__cause__` is `TypeError` | ✓ PASS |
| IN-01 assigned layout | same script | `TypeError` naming `Plain` at `helper.get_attributes()`; the caller's layout keeps both fields; a copyable layout is still isolated per instance | ✓ PASS |
| Lint/format on the three changed Python files | `.venv/bin/ruff check …; .venv/bin/ruff format --check …` | All checks passed; 3 files already formatted | ✓ PASS |
| Documented commits exist | `verify.commits aed6003 92d5430 d75fb31 48659b2 d1906e1 a2ea77c 35635eb 8c73ced` | `all_valid: true` (8/8) | ✓ PASS |
| Only the five named files changed outside `.planning/` | `git diff --stat 8c73ced..HEAD -- src tests docs examples CHANGELOG.md noxfile.py` | exactly those 5 files, +47/-14 | ✓ PASS |
| `nox -s crispy_floor` | not run (> 10 s) | fix-round test additions are crispy-version-independent | ? SKIP |
| JS gate | not re-run | no JS/template file changed since the 123-pass run at `8c73ced` | ? SKIP |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no plan or summary names a probe.

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| none declared | — | — | N/A |

### Requirements Coverage

All 13 IDs are declared across the PLAN frontmatters; REQUIREMENTS.md maps exactly FORM-01..FORM-13 to Phase 6 — no orphaned requirements. The REQUIREMENTS.md rows (`:129-141`) still read "Gaps Found"; that column is orchestrator-maintained and should be updated from this report.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| FORM-01 | 01, 09 | Golden of today's markup committed before any change | ✓ SATISFIED | SC1; goldens unchanged |
| FORM-02 | 01, 02, 06, 09, 10 | `"form"` location; `cv_button_data(ctx,"form")` provides `cv_type/cv_name/cv_value/cv_id/cv_cancel_url`; `cv_key` is the kind | ✓ SATISFIED | T8, T14, G3; probe shows all five on a rendered button |
| FORM-03 | 02, 04, 09 | Leaf renders three bodies with `cv_button_class "form" cv_key cv_label_mode` | ✓ SATISFIED | SC2, T17 |
| FORM-04 | 02, 04, 09 | `form:hidden-label` and `form:icon-host` | ✓ SATISFIED | T14, T19; UAT test 3 (screen reader) passed |
| FORM-05 | 01, 02, 05, 07, 08, 09, 10 | Submit/Button/Reset keep signature, render through leaf; `css_class` appended; extra kwargs as attributes | ✓ SATISFIED | T8, T12, T13; extra-kwarg order now documented and probed (IN-02) |
| FORM-06 | 01, 02, 05, 07, 09 | No config → `<button type>` with same text/classes/name/value/id; POST unchanged | ✓ SATISFIED | SC1, T28 |
| FORM-07 | 02, 07, 09 | Values/labels autoescaped plain text, never evaluated | ✓ SATISFIED | SC3, T11 |
| FORM-08 | 01, 05, 07, 08, 09, 10 | Filter Apply/Reset in layout `FormActions`; `#filter-button-reset` preserved; hidden inputs unchanged | ✓ SATISFIED | T20, T21, T22, T29, G5; the deep-copy failure mode is now typed, named, tested and documented (IN-01) |
| FORM-09 | 04, 08, 09, 10 | Kind → icon mapping; workflow uses `workflow`; per-form `submit_icon` wins | ✓ SATISFIED | SC4, T18, G2 |
| FORM-10 | 03, 04, 05, 06, 08, 09, 10 | `{"form":"both"}` icon+text; `{"form":"icon"}` hidden label + `title` + `data-cv-tooltip="form"` | ✓ SATISFIED | SC2, G1; UAT tests 1-2 passed on a real pointer |
| FORM-11 | 01, 03, 06, 08, 09 | Setting → ViewSet → view per-key maps | ✓ SATISFIED | T15 |
| FORM-12 | 06, 08, 09, 10 | E210/E211/W291 form maps; W292; strict raises else logs and renders label | ✓ SATISFIED | T24-T26, G4 (IN-03 test now asserts the quiet path unconditionally) |
| FORM-13 | 08, 09 | CHANGELOG Breaking + migrating-1.0.md "Form buttons"; example `both`; downstream follow-up in acceptance note | ✓ SATISFIED | SC5, T31-T33; UAT test 4 passed; IN-02 caveat closed |

### Decision Coverage

`check decision-coverage-verify` reported `skipped: true, blocking: false` ("CONTEXT.md missing") for every invocation form tried here (`06`, the phase directory, `--phase 06`) although `06-CONTEXT.md` exists; non-blocking. `06-CONTEXT.md` is unchanged since the previous pass, which recorded honored 18 / total 18, so that result stands.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `test_crispy_buttons.py` (incl. IN-01 `:1732-1755`) | FORM-02/05/07/08/09/10 | all | 0 | no | Behavioral (real crispy tag, parsed DOM, `pytest.raises` with message regex + chained-cause type + caller-layout purity) | OK |
| `test_button_data.py` (IN-03 rewrite `:867-874`) | FORM-02/12 | all | 0 | no | Value (identity, exact mode, empty warning list) — the outcome-dependent branch is gone | OK (previous note resolved) |
| `test_form_button_checks.py`, `test_form_buttons_golden.py`, `test_filter.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, `tests/js/*.test.js` | FORM-01/03/04/06/08/10/11/12/13 | all | 0 | golden: PARTIAL by design (before-change oracle) | Value/Behavioral | OK |

**Disabled tests on requirements:** 0 (no `skip`/`xfail` markers in the three changed test/source files). **Circular patterns detected:** 0. **Insufficient assertions:** 0.

### Anti-Patterns Found

Scanned the five files changed since the previous pass.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `tests/test1/test_button_data.py` | 866-881 (previous pass, IN-03) | adaptive assertion with an unreachable `else` | — resolved | Replaced by unconditional assertions (`d75fb31`) |
| `src/crud_views/lib/views/list.py` | 153 (previous pass, IN-01) | deep-copyable requirement undocumented | — resolved | Docstring + `docs/reference/list_view.md` + typed, named `TypeError` (`aed6003`) |
| `src/crud_views/lib/view/button_data.py` | 280 (previous pass, IN-02) | sorted extra-attribute order not in the migration note | — resolved | `docs/migrating-1.0.md:240-243` (`92d5430`) |
| `docs/reference/list_view.md` | 175-176 | hard line break mid-sentence ("A helper without a `layout`" / "renders every field …") | ℹ️ Info | Cosmetic; one Markdown paragraph when rendered |
| `src/crud_views/lib/views/list.py` | 155 | `except (TypeError, copy.Error)` re-raises as `TypeError`; a `copy.Error` (rare) changes type | ℹ️ Info | Deliberate (fix report: keep the type `deepcopy` already raised for `TypeError` handlers); chained with `from exc`, so nothing is lost |
| `src/crud_views_workflow/lib/forms.py` | 27-33 | `LABEL-PLACEHOLDER` / `HELP-PLACEHOLDER` field labels | ℹ️ Info | Pre-existing, runtime-replaced labels; file unchanged |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers in any changed file. Working tree clean for `src`, `tests`, `docs`, `examples`.

**Convergence evidence gate (#3304):** no 🛑 Blocker was raised on this pass, so nothing needed the carried-forward / regression / deterministic-evidence triage.

### Human Verification Required

None outstanding. The four items carried by the previous report were executed by the user and recorded in `06-UAT.md` (`a2ea77c`, status `complete`, 4 passed / 0 issues / 0 pending):

1. Hover tooltips in icon mode on a real pointer — pass.
2. Visual quality of label/both/icon on create, delete and list-filter pages, including a custom filter layout holding package Submit/Reset — pass.
3. Screen-reader announcement in icon mode (hidden-span label, modal delete flow, reset) — pass.
4. Migration-guide readability — pass; the one caveat noted there (IN-02 sorted extra-attribute order unmentioned) is closed by `92d5430`, verified above.

The single planner-deferred `<human-check>` (`06-09-PLAN.md:90`: three modes with keyboard/tooltip interactions, modal submit/cancel/apply/reset) is covered by UAT tests 1-3 together with the browser observations in `06-ACCEPTANCE.md §9`. The `human-check` mention in `06-10-PLAN.md:234` is a prose reference to this report, not a deferred check. No new behavior introduced by the fix round needs a human: the new failure path is deterministic and tested, and the doc additions are matched to runtime output by the probe.

### Gaps Summary

No gaps. The fix round changed five files and none regressed a must-have: `list.py`'s success path is byte-identical (the deepcopy is wrapped, not bypassed), the two test edits strengthen assertions rather than weaken them, and both doc additions describe behavior that the runtime probe reproduced exactly. All four human-only items are now closed by the committed UAT, and the code-review disposition shows `open: 0 / total: 6`. With no failed truth, no missing/stub artifact, no unwired link, no blocker and an empty human-verification list, the status is `passed`.

---

_Verified: 2026-10-28T14:14:47Z_
_Verifier: Claude (gsd-verifier)_
