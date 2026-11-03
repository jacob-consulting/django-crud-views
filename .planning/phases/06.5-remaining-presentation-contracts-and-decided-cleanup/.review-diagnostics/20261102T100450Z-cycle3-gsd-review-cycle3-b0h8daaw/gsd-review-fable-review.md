Repository accessed at HEAD `2b672aa` with a clean `src`, `tests`, `docs` and `examples` tree; all citations below are to that working tree. Read-only: no tests, browser or application code were run.

# Cross-AI Plan Review — Phase 06.5, cycle 3

## 06.5-01

**Summary.** The plan targets the right two producers and the only stock modal site, and its composition rule reproduces current bytes. One new concern: adding heading keys to `DEFAULT_BUTTON_CLASSES` silently enrolls headings into an existing rendering guard that no plan names.

**Strengths**
- Composition is byte-compatible. `CvHeadingNode.render` already builds a list of size class plus nonempty caller class and emits `class=` only when nonempty (`src/crud_views/templatetags/crud_views.py:348-353`); joining nonempty size, caller and icon contributions in that order is identical when the new arguments are omitted.
- Parser seam fits. Unknown kwargs raise and `level=` must be an int literal 1–6 (`crud_views.py:371-384`), so `size=` reuses that validation exactly.
- The modal line is exactly `{% cv_heading "header" level=5 class="modal-title" %}{% cv_header_icon %} {% cv_header %}{% endcv_heading %}` (`src/crud_views/templates/crud_views/modal/content.html:3`); the literal space the plan preserves is real, and `test_modal_title_is_the_header` expects `"h5 modal-title"` (`tests/test1/test_heading_level.py:161-165`), which the "size, caller, icon" order yields.
- Optional keys get validation for free: E363 formats every merged key ending in `:icon-host` (`src/crud_views/lib/button_classes.py:258-270`); W362 accepts only `DEFAULT_BUTTON_CLASSES` or action-mode keys (`:301-318`), which the plan extends.
- `get_button_classes()` caches the merged dict (`button_classes.py:131-139`), so the plan's instruction to read `_settings_layer()` and `_THEME_BUTTON_CLASSES` at lookup time is necessary and correct.

**Concerns**
- **MEDIUM (new, N1).** `tests/test1/test_button_classes_templates.py` builds `SENTINEL_CLASSES` from every `DEFAULT_BUTTON_CLASSES` key (`:131-133`), fetches six real pages under that override (`:232-264`) and fails on any class token that is not a sentinel, not `cv-` prefixed and not a behaviour token, on any element carrying a sentinel (`:149-159`). Once `heading:size-1..6` join the defaults, a heading that resolves a size key becomes a "styled" element. Plan 02-01 gives the test host title an explicit `size=3`, and plan 01's rule says an explicit size always resolves the key, so the host `<h1>` on all six pages carries the sentinel. Any utility class on it (plan 02's must-have says the host title is sized "without changing mb-0") is an offender. No plan lists this file; plan 02's `-k 'heading_icons or heading_level'` never selects it; plan 09 would see it only in wave 6. The same module scans `*/static/**/*.js` and `**/*.py` across every package for `btn` tokens (`:28-48`), which the new `tabs.js` and `presentation.py` must respect.

**Suggestions**
- Decide in 01-02 whether heading keys belong to the #227 button-chain guard. Either exclude `heading*` keys from `SENTINEL_CLASSES` with that rationale, or require that every explicitly sized heading on guard-fetched pages carries only table or `cv-` classes, and add the module to the verify selection of whichever plan owns the decision.

**Risk: MEDIUM** until N1 has an owner; the producer design itself is sound.

## 06.5-02

**Summary.** Site inventory is accurate and A14 is closed by a feasible test. The guard interaction from plan 01 lands here because this plan writes the sized host heading.

**Strengths**
- The test host nests `h5.d-flex > h3` with no classes on the inner heading (`tests/test1/app/templates/app/crud_views.html:14-22`); the demo hardcodes `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`); split-card and striped-rows render the icon as a sibling (`layouts/split-card/group.html:8-9`, `layouts/striped-rows/group.html:4-5`).
- The exclusion fix is precise: today's xpath keys on `h5[contains(@class,'d-flex')]` (`tests/test1/test_heading_level.py:26-27`); an attribute marker cannot match the `card-header` wrappers of card-rows or striped-rows.
- Golden impact is bounded. `_render_group` renders with `icon=None` (`test_heading_level.py:45`), so moving the group icon inside the heading leaves `od_split-card.html` and `od_striped-rows.html` unchanged; only intentional diffs remain.
- A14 is executable: the example has exactly one `cv_heading` block (`:17-24`), Django renders `{% block %}` inside a standalone template, and the plan asserts exactly one matching fragment.

**Concerns**
- **MEDIUM (N1, shared with plan 01).** The host title with explicit `size=3` is the element the guard will style; the plan's "without changing mb-0" wording invites the executor to copy the demo's utility class onto the test host.
- **LOW.** `cv_get_view` asserts `isinstance(view, CrudView)` (`src/crud_views/templatetags/crud_views.py:72-75`) and both `cv_header` and the `view.cv_get_header_icon` expression need it, so the extracted-fragment test must supply a real `CrudView` instance, not a `SimpleNamespace`. Plan 01's real modal test already needs one, so this is a note, not a gap.

**Suggestions**
- State the test host title's class list explicitly in 02-01 and run `test_button_classes_templates` in its verify, or take the plan 01 route.
- Name the real view fixture the fragment test reuses.

**Risk: MEDIUM** because of N1; otherwise LOW.

## 06.5-03

**Summary.** The projection fixes the reproduced defects and A11 is closed. One consumer is unlisted: the shared fallback layout template.

**Strengths**
- Defects confirmed on source: trigger-only `forloop.first` selection and slugified IDs (`layouts/tabs-vertical/object_detail.html:7-14`), panels always `tab-pane fade` (`layouts/tabs-vertical/group.html:2-5`), fixed `objectDetailAccordion` root (`layouts/accordion/object_detail.html:2`, `group.html:15`), fresh contexts in both tags (`templatetags/crud_views_object_detail.py:38,54`).
- A11 is real and fixed: the tab template loads only `crud_views_object_detail` (`object_detail.html:1`); its `cv_icon` is the local tag (`crud_views_object_detail.py:101-104`); the accordion group already loads `crud_views` (`accordion/group.html:1`).
- Golden normalization is bounded to one file: only `od_accordion.html` carries generated targets (`tests/test1/golden/heading_level/od_accordion.html:2`); `od_tabs-vertical.html` holds only the panel `<h5 class="mb-1">`, which the plan keeps.
- `ResolvedGroup` has no render state (`src/crud_views_object_detail/lib/resolvers.py:58-63`) and `test_layout_packs.py:68-75` renders a bare group, which the local one-group projection keeps green.

**Concerns**
- **LOW (new, N2).** `crud_views_object_detail/object_detail.html` is the second `select_template` candidate (`crud_views_object_detail.py:33-37`) and the actual `render_object_detail` consumer for the five non-interactive packs; it calls `{% render_group group layout=layout %}` with no projection (`object_detail.html:1-4`). Under the plan, those groups get a local generated namespace instead of the component's entries, so a supplied `cv_object_detail_id` or group id never reaches a copied non-interactive layout. The file is in no plan. Decide whether the fallback passes `presentation`/`component` (one line, keeps "one projection usable by stock and copied layouts") or document that only interactive packs receive component identity.

**Suggestions**
- Add the fallback template to 03-02's files with the chosen disposition.

**Risk: LOW-MEDIUM.**

## 06.5-04

**Summary.** The collision-scope mechanism is viable on verified Django internals and the page/modal recipe uses the real request signal.

**Strengths**
- `RenderContext.get`/`__getitem__` read only `dicts[-1]` and `push_state` pushes one frame per isolated template render (`.nox/tests-3-12-django-5-2/.../django/template/context.py:195-216`); `ExtendsNode.render` renders the parent without a push (`django/template/loader_tags.py:133-153`). The earliest non-base frame therefore spans includes and inheritance of one outer render and dies with it, as the plan assumes.
- `cv_is_modal_request` reads `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:57-59`); the content template passes nothing today (`view_detail.content.html:1-4`); `resolve_group` constructs by keyword (`resolvers.py:246-253`); `parse_property_display` is `PropertyGroupConfig(**group)` (`config.py:88-90`), so `id` is a pure additive key.
- A4 rejection cites the CONTEXT exclusion and keeps runtime validation; A5 is executable.

**Concerns**
- None new.

**Risk: MEDIUM** by nature (Django-internal frames), mitigated by the mandated three-series include/inheritance/reuse tests.

## 06.5-05

**Summary.** H3 is fully resolved at plan level. The asset registration path and lifecycle hooks are as described.

**Strengths**
- `loadScript(name)` resolves one core directory relative to `import.meta.url` via `fileURLToPath` and `path.resolve` (`tests/js/helpers/load.js:8,32-33`); the plan's package map uses the same resolution, so a relative path preserved in the sandbox resolves there too.
- `runtime-contract.test.js` discovers every `tests/js/**/*.test.js` (`:17-20`), copies only the listed paths including `src/crud_views/static/crud_views/js` (`:24-32`), requires the exact discovered set to pass (`:69-83`) and keeps the integration negatives (`:86-102`). Task 05-02 adds the extension static directory, adds `object-detail-tabs` to `requiredFiles` (`:8-10`), and preserves the Node-only PATH/env scrubbing (`:33-42`). Both harness files are in `files_modified` and the verify runs the contract with an explicit fails_when.
- `register_assets` raises only on duplicate or reserved keys (`src/crud_views/lib/assets.py:63-68`), `get_registered()` exists (`:71-76`), core renders first (`:99-101`), and the object-detail app has no `ready()` yet (`src/crud_views_object_detail/apps.py:5-9`).
- Every `cv_js` count/list assertion uses the clearing `asset_registry` fixture (`tests/test1/conftest.py:11-20`; `tests/test1/test_assets.py:54-93,248-264,333-353`; `test_pipeline_integration.py:53-103`), so the cycle-1 dismissal holds.

**Concerns**
- **LOW (note under N1).** `tabs.js` is scanned by `test_button_classes_templates.py:28-48` for `btn` tokens; keep selectors on `nav-link`/`data-bs-toggle`, never `btn`.

**Suggestions**
- None beyond the note.

**Risk: LOW.**

## 06.5-06

**Summary.** Narrow and correct; no change from cycle 2.

**Strengths**
- `_resolve_badge_css` branches callback, nonempty map, fixed color, and short-circuits on `None` (`resolvers.py:94-110`); `resolve_property` calls it once and constructs by keyword (`:191-204`); `badge_css` precedes `template` in the selector (`crud_views_object_detail.py:80-92`). Appending fields after `badge_label` (`resolvers.py:44-55`) is positional-safe.

**Concerns.** None.

**Risk: LOW.**

## 06.5-07

**Summary.** Alias inventory is complete; no alias use exists outside the planned files.

**Strengths**
- Field, after-validator branch, runtime branch and template guard are at `src/crud_views/lib/view/card.py:11,31-32`, `src/crud_views/lib/views/card.py:49-52`, `src/crud_views/lib/view/button_data.py:126-130`. A grep of `examples`, `src` and `docs` for `no_label` outside the plan 07/09 files returns nothing.
- A13 and A8 are executable in 07-01; plan 01 ordering closes the `buttons.md` half of H1.

**Concerns.** None new.

**Risk: LOW.**

## 06.5-08

**Summary.** A16 is closed with a stricter rule than the analog, and the H2 asset set is real.

**Strengths**
- The host declares Bootstrap 5.3.3 CSS/bundle, Font Awesome 6.7.2 and jQuery 3.7.1 with SRI (`tests/test1/app/templates/app/base.html:13-30`) and loads `{% cv_js %}` (`:34`), so the registered tab script reaches the stock page.
- The analog validates its port in both entry points (`tests/browser/conditional-formsets.cjs:28-31`; `tests/browser/conditional_formsets_server.py:485-487`); the plan reserves 8143 and 8144, validates format and range, and separates unset from empty. The config test lives outside `tests/js`, so `vitest.config.js:6` never discovers it and the sandbox never copies it.

**Concerns.** None new.

**Risk: MEDIUM** (new browser harness, declared network precondition, failure policy explicit).

## 06.5-09

**Summary.** A15, A17 and A18 are closed by executable task content.

**Strengths**
- A17: `vitest.config.js:6` includes only `tests/js`; `vitest.integration.config.js:6` selects `tests/js-integration`; the lane requires `CV_FRAGMENT_PYTHON` (`tests/js-integration/formset.test.js:91-110`), asserts "6 passed" and six records (`:140-146`) and keeps the invalid-interpreter regression (`:153-168`). The 09-03 command and fails_when mirror exactly that.
- A15: `Formsets.render` and `FormControl.render` use `render_to_string` with a fresh dict (`src/crud_views/lib/formsets/layout.py:16-19,29-30`), which builds a new `Context` and frame stack; the plan's wording now separates those from library calls that transport the scope, and tests both.
- A18: `cv_header_icon` stays registered (`crud_views.py:312-315`); after plans 01 and 02 its three sites (modal, test host, example) are migrated, and 09-03 inventories it as retained-but-superseded with a standalone regression.

**Concerns.** None new.

**Suggestions**
- **LOW.** `docs/reference/javascript.md` "Conditional and formset initialization" (`:255-287`) is the documented home of public repeat-safe `cv.init*` entry points; add one cross-reference line for `cv.initObjectDetailTabs` so Phase 7's JS inventory has a single page, in addition to the layout-pack reference 09-01 writes.

**Risk: LOW-MEDIUM.**

## Cross-plan findings

**Cycle-2 finding verification**

| ID | Verdict | Evidence |
|---|---|---|
| H3 | **Signed off, fully resolved at plan level** | Loader and sandbox mechanics at `load.js:8,32-33`, `runtime-contract.test.js:8-10,17-32,63-102`; tasks 05-01/05-02 own both files, preserve discovery, pass and negative assertions, and run the contract in verify. |
| A14 | Closed | Example block unique at `examples/.../crud_views.html:17-24`; standalone block rendering and single-fragment assertion feasible; real `CrudView` needed in context (note). |
| A15 | Closed | Frame semantics at `context.py:195-216`, `loader_tags.py:133-153`; untransported fresh renders at `formsets/layout.py:19,30`; 09-01/09-02 wording and tests distinguish the cases. |
| A16 | Closed | Reservation and format rules in both entry points, stricter than `conditional-formsets.cjs:28-31` and `conditional_formsets_server.py:485-487`; config test outside ordinary discovery. |
| A17 | Closed | Integration lane named with interpreter; expectations match `formset.test.js:91-168`. |
| A18 | Closed | Tag retained at `crud_views.py:312-315`; inventoried and regression-tested in 09-03; distinction documented in 02-03. |

**Dependency order** is unchanged and sound: 01/06, then 02/07, 03, 04/05, 08, 09. Shared files remain serialized.

**New actionable findings**

| ID | Severity | Plans | Finding |
|---|---|---|---|
| N1 | MEDIUM | 01, 02 | The #227 guard derives sentinels from all `DEFAULT_BUTTON_CLASSES` keys and fetches six real pages (`tests/test1/test_button_classes_templates.py:131-133,149-159,232-267`). Heading keys plus an explicitly sized host title make the `<h1>` a guarded element; any utility class on it fails the guard. No plan owns the file or decision. |
| N2 | LOW | 03 | The shared fallback `crud_views_object_detail/object_detail.html:1-4`, selected at `crud_views_object_detail.py:33-37` for five packs, passes no projection to `render_group`; supplied identity never reaches copied non-interactive layouts. Not in any plan's files. |

**Not findings:** `tests/test1/test_assets.py` and the pipeline tests all use the clearing fixture, so plan 05's startup registration breaks no pinned count. The split-card and striped-rows goldens render `icon=None` and do not change. The `_render_group` goldens for tabs do not include trigger markup.

**Overall risk: MEDIUM.** Plans are executable and the cycle-2 inventory is closed. Fix N1 before execution (an ownership decision, not a redesign); N2 is a one-line disposition in plan 03.
