I have verified every mechanism the nine plans rely on against the tree at `4762417`. The working tree under `src`, `tests`, `docs` and `examples` is clean at that commit, so line citations below are to committed source. I ran no tests, no browser and no application code.

# Cross-AI Plan Review, Phase 06.5, convergence cycle 2

Reviewed at commit `4762417` with repository access. Scope is pre-execution plan review. New artifacts named in the plans are treated as planned, not missing.

## 06.5-01

**Summary.** The plan now owns the whole heading-registry change, including the key-count guards and the canonical count sentence, and it specifies a concrete class-composition rule. Both cycle-1 findings against this plan are resolved by executable task content.

**Strengths**
- The composition rule reproduces today's bytes. `CvHeadingNode.render` already builds a list of a size class plus a nonempty caller class and emits `class=` only when that list is nonempty, at `src/crud_views/templatetags/crud_views.py:348-353`. Joining only nonempty size, caller and icon contributions in that order is byte-identical when the new arguments are omitted.
- The parser seam fits. Unknown kwargs raise at `crud_views.py:374-376` and `level=` must be an int literal from 1 to 6 at `:380-384`, so `size=` can reuse that validation exactly as the plan says.
- Optional location keys get validation for free. E363 iterates every merged key ending in `:icon-host` and formats it with `name_class` at `src/crud_views/lib/button_classes.py:268-278`. W362 accepts only keys in `DEFAULT_BUTTON_CLASSES` or action-mode keys at `:301-303`, which is exactly the recognition the plan extends. E361 accepts `""` as a str value at `:259-267`, so the two empty-string builtin entries are valid.
- The modal path is exact. The modal title line carries a literal space between the icon tag and the header at `src/crud_views/templates/crud_views/modal/content.html:3`. The golden is `<h5 class="modal-title"> Author</h5>` at `tests/test1/golden/heading_level/modal_detail.html:1`, and the plan keeps the literal space even when the inline icon is empty. The header hook is a method at `src/crud_views/lib/view/base.py:422-425`, so a template expression calls it once.

**Concerns**
- LOW. The builtin `""` entries for `heading-page:icon-inline` and `heading-modal:icon-inline` live in the builtin layer. Under the plan's layer-first rule, any theme or project value for the shared `heading:icon-inline` key overrides them. That is the intended semantics, but plan 02-03's documentation must say it in one sentence so a theme author is not surprised that a shared spacing value reaches the modal title.

**Suggestions**
- Add the sentence above to the precedence paragraph published by task 02-03.

**Risk: LOW.** The plan passes its own verify as written, and the guard update is ordered before plan 07's edit of the same document.

## 06.5-02

**Summary.** The site inventory is accurate and the golden exclusion is now precise. The test host nests a heading inside a heading at `tests/test1/app/templates/app/crud_views.html:13-27`, the demo hardcodes the size class at `examples/bootstrap5/project/templates/project/crud_views.html:17`, and split-card and striped-rows render the icon as a sibling at `layouts/split-card/group.html:7-9` and `layouts/striped-rows/group.html:3-5`.

**Strengths**
- No golden captures the host wrapper. A search for `class="d-flex"` across `tests/test1/golden` returns nothing. The three `action_menus/cards_*` goldens that matched a broader search capture only the card element, as the producing test extracts the card node at `tests/test1/test_action_menus_card.py:34-37`.
- No child template overrides the host's title blocks. The only other `cv_header_icon` site in the tree is the modal template, so plan 01 and plan 02 together cover every title site.
- The test-only marker fixes A2 precisely. The current exclusion at `tests/test1/test_heading_level.py:27` keys on a Bootstrap class, while card-rows and striped-rows headings sit inside `.card-header` at `layouts/card-rows/group.html:3-4` and `layouts/striped-rows/group.html:3-5`. Excluding only an explicit attribute cannot swallow those.
- The split-card icon-style change is intentional and recorded. Tabs, accordion and striped-rows already use `me-2` at `layouts/tabs-vertical/object_detail.html:15`, `layouts/accordion/group.html:8` and `layouts/striped-rows/group.html:4`, so the shared `me-2` default changes only split-card's `text-default fs-5`.

**Concerns**
- LOW. The example project's template is not rendered by any pytest module. Task 02-01 changes it, but the only executed proof of the recipe is the documentation fence in task 02-03. A drift between the example file and the published fence would go unnoticed.

**Suggestions**
- In task 02-03, render the example template through a locmem override, or assert that its title block equals the published fence.

**Risk: LOW.**

## 06.5-03

**Summary.** The projection design matches the code. Triggers mark only the first item active at `layouts/tabs-vertical/object_detail.html:8`, panels always start `tab-pane fade` without `active` at `layouts/tabs-vertical/group.html:2`, both sides slugify the title, the accordion root is fixed at `layouts/accordion/object_detail.html:2`, and both tags render fresh contexts at `templatetags/crud_views_object_detail.py:38,54`. A11 was real and is fixed: the tab template loads only the object-detail library at `object_detail.html:1`, while the accordion group already loads `crud_views` at `accordion/group.html:1`.

**Strengths**
- The length-prefixed encoding is injective for the stated grammar, and every emitted character is selector-safe.
- Titles are typed `LazyStr` at `src/crud_views_object_detail/lib/config.py:58`. Keeping titles out of IDs avoids lazy-proxy and translation instability by construction.
- The standalone `render_group` path is preserved. `test_layout_packs.py:68-75` renders a bare group and expects the `tab-pane` marker, and `test_heading_level.py:44-47` constructs `ResolvedGroup` by keyword, so the local one-group projection and the appended optional field keep both green.
- Golden normalization is bounded to one file. Only `od_accordion.html` carries a generated target, at `tests/test1/golden/heading_level/od_accordion.html:2`.

**Concerns**
- LOW. That golden line carries the generated value in both `data-bs-target` and `aria-controls`. Task 03-03 names control, panel and parent attributes. Add `aria-controls` to the normalized set, or the golden comparison fails on the second attribute.
- LOW. `tests/test1/od/test_layout_a11y.py` holds no tab or accordion assertions today, only property-row and tooltip checks at `:11-58`. Task 03-03 describes migrating old target assertions in that file. There are none to migrate, so the new ID and selection assertions are additions.

**Suggestions**
- Name `aria-controls` explicitly in the normalization list.

**Risk: LOW-MEDIUM.** The remaining risk is template plumbing, not the formula.

## 06.5-04

**Summary.** The collision-scope mechanism is viable on Django internals, and the page/modal recipe now uses a real request signal. `cv_is_modal_request` exists at `src/crud_views/lib/view/base.py:57-59` and reads the header the modal script sends at `src/crud_views/static/crud_views/js/modal.js:140,177`. The test application has a modal detail view with `cv_modal = True` at `tests/test1/app/views.py:894-896`.

**Strengths**
- The "earliest non-base frame" rule holds. In the cached Django 5.2 tree, `RenderContext` reads and writes only `dicts[-1]` at `django/template/context.py:195-204`, `push_state` pushes a frame per isolated render at `:207-216`, and `BaseContext.__copy__` shallow-copies the frame list at `:40-44`, so the frame dict objects are shared by `context.new()`. `ExtendsNode` renders the parent without a push at `django/template/loader_tags.py:159`, and `IncludeNode` goes through `template.render` at `:208-210`. The outermost render therefore owns `dicts[1]`, and sibling includes, inherited blocks and `only` includes all see the same dict object.
- Threading points are correct. The mixin adds context at `src/crud_views_object_detail/lib/mixins.py:44-51`, `resolve_group` constructs by keyword at `resolvers.py:246-253`, and the content template calls the tag at `view_detail.content.html:3`.
- A4 is closed by an explicit, CONTEXT-grounded rejection, which is the allowed route. The plan keeps runtime grammar validation and render-local collision errors.

**Concerns**
- LOW. Any fresh backend render inside a page starts a new boundary, not only independent responses. The library's own formset layout helper renders through `render_to_string`, and other backend `tpl.render(dict, request)` calls behave the same. The plan 09 wording "includes and inheritance, not independent responses" should add "and not content rendered through a fresh backend render inside the page".

**Suggestions**
- Add that sentence to the boundary documentation in task 09-01 and to the migration note in 09-02.

**Risk: MEDIUM.** The mechanism is Django-internal by design. The required include, inheritance, reused-Context and three-series tests are the right guard.

## 06.5-05

**Summary.** The registration and lifecycle design is sound, but one existing JavaScript guard will fail the phase's full vitest gate as planned. This is a new HIGH.

**Strengths**
- `register_assets` raises on a duplicate key at `src/crud_views/lib/assets.py:66-67`, and `get_registered()` exists at `:71-76`, so the identical-registration guard is implementable without touching `assets.py`.
- Core renders first at `assets.py:99-101`, the object-detail app has no `ready()` yet at `src/crud_views_object_detail/apps.py:5-9`, and the app is installed in tests at `tests/test1/conftest.py:55`. This is the first shipped extension bundle; no other app calls `register_assets`.
- `tooltip.js` is the right analog, including the late-load branch at `src/crud_views/static/crud_views/js/tooltip.js:32-36` and the descendants-only limitation at `:27` the plan corrects.
- A6 is closed by an explicit disposition. The adapter module defines modal, tooltip, collapse and alert at `adapters.js:51-100`; the plan leaves it unchanged and plan 09-03 inventories the direct dependency.

**Concerns**
- HIGH, new, H3. The new `tests/js/object-detail-tabs.test.js` cannot run in the existing Node-only contract. `tests/js/helpers/load.js:8,33` resolves scripts only under `src/crud_views/static/crud_views/js`. `tests/js/runtime-contract.test.js:17-20` collects every `tests/js/**/*.test.js`, copies only that core directory into a sandbox at `:24-32`, and asserts that every collected file passes at `:69-80`. A test for `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` therefore fails there with a missing file. Task 05-01's own verify runs only the new file and would pass, but plan 09's required `node node_modules/vitest/vitest.mjs run` gate fails. Neither `load.js` nor `runtime-contract.test.js` is in any plan's `files_modified`.

**Suggestions**
- In task 05-01, add `tests/js/helpers/load.js` and `tests/js/runtime-contract.test.js` to files and read_first. Give the loader a package-aware path and add the extension static directory to the sandbox copy list. Keep the sandbox Node-only.

**Risk: MEDIUM-HIGH until H3 is fixed.** Everything else in the plan is grounded.

## 06.5-06

**Summary.** The narrowest plan and still correct. `_resolve_badge_css` branches callback, nonempty map, fixed color and short-circuits on `None` at `src/crud_views_object_detail/lib/resolvers.py:94-110`. `resolve_property` calls it once and constructs by keyword at `:191-204`. Template selection prefers `badge_css` over an explicit template at `templatetags/crud_views_object_detail.py:80-92`.

**Strengths**
- Appending two defaulted fields after `badge_label` at `resolvers.py:44-55` preserves every keyword and positional caller.
- The empty-string color case is named as existing behavior, and the context passed to native templates at `:95-98` stays intact.

**Concerns**
- None beyond a LOW naming note. The `-k 'test_templatetags'` selection may also match a core module of that name. Harmless, but the summary should report the actual selected count.

**Risk: LOW.**

## 06.5-07

**Summary.** The alias inventory is complete and the ordering with plan 01 closes the shared-document half of H1. The field is at `src/crud_views/lib/view/card.py:11`, the combined-use rejection at `:31-32`, the runtime branch at `src/crud_views/lib/views/card.py:49-52`, the template guard at `src/crud_views/lib/view/button_data.py:126-130`. `no_label=False` is accepted today at `tests/test1/test_card_action_label_mode_field.py:26-27`, the validator bypass is at `test_card_label_mode_render.py:474-476`, and the documentation marker is at `test_label_mode_docs.py:214-223`.

**Strengths**
- A13 is executable: non-mapping passthrough, existing-instance validation and the invalid-input error are all named in task 07-01.
- A8 is executable without a dependency change.
- The plan correctly leaves the contradictory Unreleased bullets at `CHANGELOG.md:131-140` and the migration-guide claims at `docs/migrating-1.0.md:47,142,157` to plan 09, and says phase completion depends on it.

**Concerns**
- LOW. Between wave 2 and wave 6 the branch states both "removed" and "keeps working". That is already acknowledged, and no task authorizes a release between them.

**Risk: LOW.**

## 06.5-08

**Summary.** H2 is resolved by the allowed route. The required assets are exactly the host's, with SRI already declared: Bootstrap 5.3.3 CSS and bundle at `tests/test1/app/templates/app/base.html:14-19`, Font Awesome 6.7.2 at `:22-24`, jQuery 3.7.1 at `:27-30`, and `{% cv_js %}` at `:34` so the registered tab script loads through the registry. Ports 8143 and 8144 are taken at `modal-focus.cjs:21` and `conditional-formsets.cjs:28`; 8145 is free. The `CV_FOCUS_*` overrides exist at `conditional-formsets.cjs:12,123-125`.

**Strengths**
- The preflight is concrete: observed CSS, JS and font responses, SRI acceptance where declared, `bootstrap.Tab.VERSION`, loaded fonts, recorded URLs, status, integrity and body hashes, and a distinct exit code. Unavailable assets can no longer masquerade as a pass or a skip.
- A9 is sound. Django's own catalog translates the month names, and wrapping dispatch plus `TemplateResponse.render()` in `translation.override` does not depend on locale middleware.
- A3 and A5 are exercised with real DOM focus destinations and the real request header.

**Concerns**
- LOW. Playwright cannot return bodies for cached or redirected responses. The plan should require a fresh browser context without HTTP cache for the preflight and treat an unreadable body as a prerequisite failure.
- LOW. The analog servers reject the reserved port at `conditional_formsets_server.py:486-487`. The new runner should reject 8143 and 8144 for its own override the same way.

**Suggestions**
- Add both rules to task 08-01's action text.

**Risk: MEDIUM.** New harness code with a declared network precondition. The failure policy is now explicit.

## 06.5-09

**Summary.** The migration, pairing and handoff work is executable, and the A10 estimate now carries a rationale. `docs/reference/object_detail_layout_packs.md` is 70 lines of screenshots, so the recipe authoring is real work. The `cv_sources` signature exposes `keys` at `src/crud_views/lib/pipeline.py:127-141`, so the A12 recipe is valid. `.venv/bin/mkdocs` and `.venv/bin/ruff` exist.

**Strengths**
- A7 targets the actual contradictory bullets at `CHANGELOG.md:131-140`.
- The plan now states that focused task commands are incremental and that every final gate is required.

**Concerns**
- MEDIUM, inherited from H3. The required full vitest gate fails until plan 05 fixes the sandbox and loader. Plan 09 need not change if plan 05 does.
- LOW. The default `vitest run` config includes only `tests/js` at `vitest.config.js:6`; the integration bridge lives in `tests/js-integration` and reads `CV_FRAGMENT_PYTHON` at `tests/js-integration/formset.test.js:92`. The verification text mentions the bridge but never names `npm run test:integration`. State whether it runs, and why if not.
- LOW. Plan 02-03 keeps `cv_header_icon` as a working tag. The Phase 7 inventory should mark it retained but superseded so the freeze does not advertise two heading-icon contracts.

**Suggestions**
- Add the integration-suite decision and the `cv_header_icon` status to task 09-03.

**Risk: LOW-MEDIUM.**

## Cross-plan conclusions

**Dependency order** is sound: 01 and 06 in wave 1, 02 and 07 in wave 2, 03 in wave 3, 04 and 05 in wave 4, 08 in wave 5, 09 in wave 6. Every shared file is ordered by `depends_on`: `buttons.md` 01 before 07, `test_heading_level.py` 02 before 03, `resolvers.py` 06 before 04, `presentation.py` and the identity test 03 before 04.

**H1 closure.** Signed off as FULLY RESOLVED. Task 01-02 updates `EXPECTED_KEYS`, the cardinality assertion at `tests/test1/test_button_classes.py:95-96`, the host-slot count at `:310-313` and the single canonical sentence parsed at `:102-106` from `docs/reference/buttons.md:147`, with that document in plan 01's files. Plan 07 depends on plan 01 and preserves the count. No other guard pins the count: `test_icon_host_leaves.py:364` asserts one value, not a cardinality.

**H2 closure.** Signed off as FULLY RESOLVED at plan level. Provenance, preconditions, recording and failure policy are explicit, and offline reproduction is declared out of scope rather than implied. Two LOW hardening notes remain above.

**Locked decisions.** D-01 to D-17 are unchanged. D-01 to D-04 are implemented by plans 01 and 02, D-05 to D-08 by 03, 04, 05 and 08, D-09 and D-10 by 07, D-11 to D-14 by 06, D-15 to D-17 by 08 and 09. The A4 and A6 rejections cite the CONTEXT exclusions and keep existing adapters, so neither reopens a decision. No plan invents a scope simplification.

**New HIGH this cycle.** H3 in plan 05, confirmed from source.

## Prior-finding closure table

| ID | Severity | Disposition this cycle | Evidence |
|---|---|---|---|
| H1 | HIGH | Closed, fully resolved | plan 01 task 01-02 plus plan 07 ordering; guards at `test_button_classes.py:95-106,310-313`, `buttons.md:147` |
| H2 | HIGH | Closed, fully resolved | plan 08 preflight, SRI reuse, hashes, exit 2; assets at `base.html:14-30` |
| A1 | MEDIUM | Closed | `icon_class` composition at `crud_views.py:348-353`; modal space at `modal/content.html:3` |
| A2 | MEDIUM | Closed | test-only marker; exclusion at `test_heading_level.py:27` |
| A3 | LOW | Closed | 03-01 rationale, 08-01 focus destinations, 09-01 docs |
| A4 | MEDIUM | Closed by justified rejection | CONTEXT excludes optional diagnostics; runtime checks retained |
| A5 | MEDIUM | Closed | `cv_is_modal_request` at `base.py:57-59` used in 04-01, 08-01, 09-01 |
| A6 | MEDIUM | Closed by explicit disposition | adapters unchanged at `adapters.js:51-100`; inventoried in 09-03 |
| A7 | LOW | Closed | 09-02 edits `CHANGELOG.md:131-140` |
| A8 | LOW | Closed | recorded in 07-01 and 09-03 |
| A9 | MEDIUM | Closed | `gettext_lazy` month names under `translation.override` |
| A10 | MEDIUM | Closed | explicit 36k rationale in plan 09 |
| A11 | MEDIUM | Closed | tab template load at `tabs-vertical/object_detail.html:1` |
| A12 | LOW | Closed | `keys` kwarg at `pipeline.py:127-141`, executed recipe in 09-02 |
| A13 | LOW | Closed | non-mapping passthrough and tests in 07-01 |

## Genuinely unresolved findings

- **H3, HIGH, plan 05.** The new vitest file cannot load its subject through `tests/js/helpers/load.js:8,33` and fails inside the Node-only sandbox at `tests/js/runtime-contract.test.js:17-32,69-80`, so plan 09's full JavaScript gate fails. Add both files to plan 05 and extend the loader and the sandbox copy list.
- **LOW, plan 03.** Include `aria-controls` in the golden normalization set.
- **LOW, plan 04 and 09.** State that fresh backend renders inside a page also start a new collision boundary.
- **LOW, plan 08.** Require a cache-free browser context for the preflight and reject the reserved ports.
- **LOW, plan 09.** Decide and record whether the integration suite runs, and mark `cv_header_icon` as superseded in the inventory.
- **LOW, plan 01 and 02.** Document that the builtin empty page and modal inline entries yield to any shared theme or project value.
- **LOW, plan 02.** Exercise the example template, not only the documentation fence.
