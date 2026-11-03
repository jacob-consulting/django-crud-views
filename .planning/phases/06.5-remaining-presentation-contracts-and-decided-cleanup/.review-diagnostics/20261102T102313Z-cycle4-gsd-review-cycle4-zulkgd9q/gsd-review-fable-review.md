# Cross-AI Plan Review — Phase 06.5, convergence cycle 4

Reviewed at HEAD `91f93d4` with repository access. The product tree under `src`, `tests`, `docs` and `examples` is clean at that commit, so every citation below is to committed source. Read-only: no tests, browser or application code were run. Planned new artifacts are treated as planned, not missing. One evidence limit: the sandbox blocked reading Django's German catalog under `.nox`, so the `Januar`/`Februar` fact relied on by plan 08 is carried from cycle 3, not re-read here.

## 06.5-01

**Summary.** The producer design is unchanged and still matches the two seams it modifies. The cycle-3 N1 revision assigns the guard-scope decision to plan 02 and keeps plan 01's own registry/count guards complete. That split is consistent with the wave order and with what the guard actually renders in wave 1.

**Strengths**
- Composition reproduces current bytes. `CvHeadingNode.render` builds a list of the implicit size class plus a nonempty caller class and emits `class=` only when nonempty (`src/crud_views/templatetags/crud_views.py:348-353`). "Size, caller, icon" joined only when nonempty is identical when the new arguments are omitted, and yields `"h5 modal-title"` for `test_modal_title_is_the_header` (`tests/test1/test_heading_level.py:161-165`).
- Parser seam fits. Unknown kwargs raise at `crud_views.py:374-376`; `level=` must be an int literal 1..6 (`:380-384`), so `size=` can reuse that validation.
- Registry mechanics are as the plan assumes: settings layer read uncached (`src/crud_views/lib/button_classes.py:131-132`), merged cache (`:135-141`), presence-based mode fallback (`:150-155`), E361 accepting `""` (`:259-267`), E363 formatting every merged `:icon-host` key (`:268-278`), W362 accepting only defaults or action-mode keys (`:301-318`). The two builtin `""` inline entries pass E361.
- The modal line and golden are exactly as described: `modal/content.html:3` has the literal space; `tests/test1/golden/heading_level/modal_detail.html:1` is `<h5 class="modal-title"> Author</h5>`.
- Wave-1 guard run is sound. Task 01-02's `-k button_classes` selects `test_button_classes_templates.py`. In wave 1 the sentinel set will include the new heading keys (`:132`), but no guard page can render one: the test settings set no `CRUD_VIEWS_HEADER_LEVEL` (`tests/test1/conftest.py`, no such key), so implicit sizes never resolve, and no explicit `size=` exists until plan 02. The guard pages (`:232-239`) do not fetch the modal.

**Concerns**
- LOW. The plan's "derive the resulting counts at execution" is right, but the summary should state the derived numbers for the reader of `buttons.md:147`: 74 existing keys plus six size keys, two shared icon slots and two builtin empty location-inline entries, and six `:icon-host` slots instead of five (`tests/test1/test_button_classes.py:310-313`).

**Suggestions**
- Record the final key and host-slot counts in the 01 SUMMARY so plan 07 (which edits the same document afterwards) and Phase 7 can cite them.

**Risk: LOW.**

## 06.5-02

**Summary.** The N1 closure lives here and it is precise. The partition rule excludes exactly the four heading namespaces, nothing else exists under those names today, and the positive leak-detection regression proves the button-chain guard still bites.

**Strengths**
- The guard is exactly as the plan describes: sentinels from every default key (`tests/test1/test_button_classes_templates.py:131-133`), styled-element selection (`:144-146`), offender rule covering span descendants (`:149-159`), leaf and six-page sweep under the override (`:250-264`), positive styled counts (`:266-267`). A grep of `src` for `heading:`/`heading-` keys returns nothing, so the "location segment before the first colon" rule removes only plan 01's additions.
- The scoping does not weaken the existing heading that is already guarded by a button key: `tags/card.html:6` sizes the card title through `card:title`, which stays a sentinel, and under the guard pages' `header_level=None` it carries only that class.
- Site inventory confirmed: the test host nests `h5.d-flex > h3` (`tests/test1/app/templates/app/crud_views.html:13-27`); the demo hardcodes `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`); split-card and striped-rows render the icon as a sibling (`layouts/split-card/group.html:8-9`, `layouts/striped-rows/group.html:4-5`); `docs/reference/templates.md:47-55` still teaches the old recipe.
- A14 holds: the example has one `cv_heading` block (`:17-24`) and `cv_get_view` demands a real `CrudView` (`crud_views.py:72-75`), which the plan's real-fixture instruction satisfies.
- The exclusion replacement is unambiguous: today's xpath keys on a Bootstrap class (`tests/test1/test_heading_level.py:26-27`); a test-only attribute cannot match the `card-header` wrappers in `card-rows/group.html:3` or `striped-rows/group.html:3`.

**Concerns**
- LOW. `test_every_literal_slot_in_templates_is_a_default_key` (`test_button_classes_templates.py:51-57`) fails for any template literal naming an optional non-default key such as `heading-page:icon-host`. The plans route all heading lookups through `_heading_class`/`cv_heading_icon`, so this is a constraint to keep, not a defect. State it in 02-03's recipe so a copied template does not use a literal for an optional key.

**Suggestions**
- Add one sentence to 02-03: optional location keys are addressable through the tag, never through a template literal.

**Risk: LOW.**

## 06.5-03

**Summary.** The projection fixes the reproduced defects, and the N2 closure is now a real production change in task 03-03 with the fallback as a fifth owned file. The mechanism is correct for all five group-only packs.

**Strengths**
- Defects confirmed on source: trigger-only first selection and slug IDs (`layouts/tabs-vertical/object_detail.html:7-14`), panels always `tab-pane fade` (`layouts/tabs-vertical/group.html:2-5`), fixed `objectDetailAccordion` root and parent (`layouts/accordion/object_detail.html:2`, `group.html:15`), fresh contexts in both tags (`templatetags/crud_views_object_detail.py:38,54`).
- N2 premise confirmed: the shared fallback loops raw `groups` and calls `render_group` with no projection (`crud_views_object_detail/object_detail.html:1-4`), is the second `select_template` candidate (`:32-37`), and is the only `object_detail.html` for split-card, card-rows, table-inline, list-group-3col and striped-rows (the layouts tree lists `object_detail.html` only under accordion and tabs-vertical).
- The migration is one-directional and safe: 03-01 builds the projection once in `render_object_detail`, 03-03 iterates `component.groups` and passes `presentation`/`component`, and `render_group` with a supplied entry must not allocate. The standalone `render_group` paths still exercised by `test_layout_packs.py:69-75`, `test_heading_level.py:44-47` and `od/test_icons.py:11-15` keep their local projection.
- A11 holds: `tabs-vertical/object_detail.html:1` loads only the object-detail library, whose `cv_icon` is local (`crud_views_object_detail.py:101-104`); the accordion group already loads `crud_views` (`accordion/group.html:1`).
- Golden impact is bounded to `od_accordion.html:2`, which carries the generated value in `data-bs-target` and `aria-controls`; the normalization rule covers attribute values, not names.
- The locmem override pattern has precedent in `tests/test1/test_heading_tag.py`, `test_crispy_buttons.py` and others, so overriding only `group.html` while the fallback stays on disk is feasible.

**Concerns**
- LOW. `od/test_icons.py:40-41` asserts `'<i class="truck'`; once split-card/striped-rows and the tab button render icons through the shared inline slot (`me-2`), `render_icon("truck", css="me-2")` still yields that prefix (`src/crud_views/lib/icons.py:231-245`). This is fine, but the file is owned by no plan and only plan 09's full suite exercises it. Name it in the 03 summary as an observed-green regression.

**Suggestions**
- None beyond the summary note.

**Risk: LOW-MEDIUM** (template plumbing across three tasks; the formula and fallback wiring are sound).

## 06.5-04

**Summary.** Stable identity threading and the collision boundary are viable on verified Django internals. The N2 extension in 04-01 covers the supplied-group case through the real view and the unchanged fallback.

**Strengths**
- Threading points verified: `mixins.py:44-51` adds context; `view_detail.content.html:3` passes nothing today; `PropertyGroupConfig` has no `id` (`config.py:56-62`); `parse_property_display` is `PropertyGroupConfig(**group)` (`:88-90`); `resolve_group` constructs by keyword (`resolvers.py:248-253`). Appending `id` is additive.
- The modal recipe is real: `cv_is_modal_request` reads `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:57-59`), sent by `modal.js:140,177`; `AuthorModalDetailView` sets `cv_modal = True` (`tests/test1/app/views.py:893-896`), so the flag is not the discriminator.
- The frame rule holds on the Django 5.2 tree: `RenderContext.get` reads `dicts[-1]` (`django/template/context.py:195-200`), `push_state` pushes one frame per isolated render (`:207-216`), `BaseContext.__copy__` shallow-copies the frame list (`:40-44`) so includes and `only` includes share the frame objects, `ExtendsNode` renders the parent with `isolated_context=False` (`loader_tags.py:158-159`), and the backend `tpl.render(dict, request)` builds a new `Context` via `make_context` (`backends/django.py:102-103`). The outer render's `dicts[1]` is therefore the right owner, and fresh backend renders need the explicit transport the plan specifies.
- 04-01's test uses the same shipped fallback with copied `group.html`, resolved explicit IDs and the request-aware hook; this is the supplied-identity half of N2.

**Concerns**
- LOW. The only other `render_object_detail` consumer in the tree is `src/crud_views/templates/crud_views/view_detail.content.html:1-3`, which loads a tag library named `object_detail` that does not exist (`src/*/templatetags/` contains only `crud_views`, `crud_views_formsets`, `crud_views_object_detail`). Nothing references it; it last changed in the `src/` move commit. It cannot carry `object_detail_id` and would raise `TemplateSyntaxError` if ever rendered. Not a plan defect and outside the phase's cleanup exclusion, but plan 04/09 documentation must name the object-detail app's content template as the only supported threading point. See open question below.

**Suggestions**
- In 04-01's action, state that `crud_views_object_detail/view_detail.content.html` is the sole stock path for `object_detail_id`.

**Risk: MEDIUM** by nature (Django-internal frames), mitigated by the mandatory three-series include/inheritance/reuse tests.

## 06.5-05

**Summary.** H3 remains fully resolved; the asset registration and lifecycle hooks are as described. No regression.

**Strengths**
- `register_assets` raises on any existing key (`src/crud_views/lib/assets.py:66-67`), `get_registered` exists (`:71-76`), core renders first (`:99-101`), the object-detail app has no `ready()` (`src/crud_views_object_detail/apps.py:5-9`), and the test host emits `{% cv_js %}` (`tests/test1/app/templates/app/base.html:34`).
- Lifecycle events are exactly `cv:modal:loaded`/`cv:modal:unload` (`modal.js:23-24`); the tooltip analog scans descendants only (`tooltip.js:27`), which the plan corrects.
- H3 mechanics confirmed: `load.js:8,32-33` roots reads in core only; `runtime-contract.test.js:8-10` lists required files, `:17-20` discovers every ordinary test, `:24-32` copies only core static JS, `:63-82` requires exact file equality and all-pass, `:84-102` keeps the interpreter negatives. Tasks 05-01/05-02 own both files and run the contract.
- No shipped script references `bootstrap.` outside `adapters.js` today; the plan's explicit stock-only disposition (A6) is recorded.

**Concerns**
- LOW. The shipped-source scanner (`test_button_classes_templates.py:28-48`) will scan `tabs.js` for `btn` tokens. The plan's selectors are `data-cv-od-tabs`/tab triggers, so this is a constraint to keep, not a gap.

**Suggestions**
- None.

**Risk: LOW.**

## 06.5-06

**Summary.** Narrowest plan; still correct against source.

**Strengths**
- `_resolve_badge_css` branches callback, nonempty map, fixed color, and short-circuits on `None` (`resolvers.py:94-110`); `_resolve_badge_label` is separate (`:113-117`); `resolve_property` calls each once and constructs by keyword (`:190-204`); `ResolvedProperty` ends with `badge_label` (`:44-55`), so appending is positional-safe.
- `render_property_value` prefers `badge_css` over an explicit template (`crud_views_object_detail.py:79-92`) and passes `prop`/`value`/`od_settings` (`:95-98`); the stock badge reads `prop.badge_css`/`prop.badge_label` only (`types/default/badge.html`).

**Concerns.** None.

**Risk: LOW.**

## 06.5-07

**Summary.** Alias inventory complete and unchanged from cycle 3.

**Strengths**
- Field and combination branch (`src/crud_views/lib/view/card.py:11,31-32`), runtime branch (`src/crud_views/lib/views/card.py:49-52`), template guard (`button_data.py:126-130`), validator bypass (`test_card_label_mode_render.py:474-476`), docs marker (`test_label_mode_docs.py:214-223`), fixture (`tests/test1/app/views.py:79-80`) and the `no_label=False`-accepting test (`test_card_action_label_mode_field.py:26-27`) are all in plan 07's files or plan 09's.
- The grep of `src`, `examples` and `docs` finds no alias use outside those files; the remaining `no_label` hits in `tests/test1/test_label_mode.py:35`, `test_action_label_mode_config.py:249` and `test_backend_only_labels.py:22` are unrelated identifiers.

**Concerns.** None new. The interim "removed" versus "keeps working" contradiction between waves 2 and 6 (`docs/migrating-1.0.md:142,157`, `CHANGELOG.md:131-140`) is acknowledged and owned by 09-02.

**Risk: LOW.**

## 06.5-08

**Summary.** H2 and A16 closures stand. The declared assets and reserved ports are real.

**Strengths**
- Assets and SRI are exactly those in `tests/test1/app/templates/app/base.html:13-30`; port reservations match `conditional_formsets_server.py:485-487`, `conditional-formsets.cjs:28-31` and `modal-focus.cjs:21`.
- The fixture reaches the real `cv_is_modal_request` signal and `ObjectDetailView` path, and keyboard-before-click is the right first assertion given Bootstrap's constructor-installed keydown handler.

**Concerns**
- LOW. The German month fact (`gettext_lazy("January")` → `Januar`) was verified by cycle 3 at `django.po:991-995`; this cycle could not re-read that file. No change to the plan is needed, but the 08 summary should record the actual rendered strings.

**Suggestions**
- None.

**Risk: MEDIUM** (new browser harness, declared network precondition, explicit failure policy).

## 06.5-09

**Summary.** Migration, pairing, integration lane and handoff are executable; nothing regressed.

**Strengths**
- A17: `vitest.config.js` includes `tests/js` only; `vitest.integration.config.js` selects `tests/js-integration`; the lane requires `CV_FRAGMENT_PYTHON` (`tests/js-integration/formset.test.js:91-110`), asserts "6 passed" and six records (`:140-146`) and keeps the invalid-interpreter regression (`:153-168`). The 09-03 command and fails_when match.
- A15: `Formsets.render` and `FormControl.render` use `render_to_string` with fresh dicts (`src/crud_views/lib/formsets/layout.py:16-19,29-30`), the untransported case the plan documents.
- A18: `cv_header_icon` stays registered (`crud_views.py:312-315`); after plans 01/02 its three sites are migrated and 09-03 inventories it as retained-but-superseded.
- `cv_sources(keys=...)` filtering is at `src/crud_views/lib/pipeline.py:86-90,127-141`; `.venv/bin/mkdocs`, `.venv/bin/ruff`, `node_modules/vitest/vitest.mjs` and all three cached interpreters exist.

**Concerns**
- LOW. The stale core template noted under plan 04 will appear in any "leaf files on disk" scan Phase 7 performs. 09-03 should record it as a known pre-existing stale file outside this phase so the inventory does not list it as a supported entry point.

**Suggestions**
- Add that one line to the public-surface handoff.

**Risk: LOW-MEDIUM.**

## Cross-plan conclusions

**Dependency order** is unchanged and sound: 01/06, then 02/07, then 03, then 04/05, then 08, then 09. Shared files stay serialized: `buttons.md` 01 before 07; `test_heading_level.py` 02 before 03; `resolvers.py` 06 before 04; `presentation.py` and the identity test 03 before 04; `test_button_classes_templates.py` is owned once, by 02-01.

**Locked decisions.** D-01 to D-17 are unchanged in the plans. D-01–D-04 are delivered by 01/02, D-05–D-08 by 03/04/05/08, D-09/D-10 by 07, D-11–D-14 by 06, D-15–D-17 by 08/09. The A4 and A6 rejections cite CONTEXT exclusions and keep existing adapters; no decision is reopened and no scope is simplified away.

**Prior closures.** H1, H2, H3 and A1–A18 remain closed. I found no regression in the cycle-4 revisions; the N1 and N2 edits touch only `test_button_classes_templates.py`, the fallback template and the identity tests.

**Independent N1/N2 closure**

| ID | Severity | Verdict | Independent evidence |
|---|---|---|---|
| N1 | MEDIUM | **FULLY RESOLVED at plan level** | Guard derives sentinels from every default key and flags non-sentinel classes on sentinel-bearing elements (`tests/test1/test_button_classes_templates.py:131-159,250-267`). No existing key uses a `heading*` location, so 02-01's four-namespace exclusion removes exactly plan 01's additions. `card:title` keeps guarding the card heading (`tags/card.html:6`). Plan 01's wave-1 guard run passes because the test settings set no header level and no explicit `size=` exists before plan 02. The added positive leak regression keeps button/span detection proven. |
| N2 | LOW | **FULLY RESOLVED at plan level** | Fallback confirmed at `crud_views_object_detail/object_detail.html:1-4`, selected at `templatetags/crud_views_object_detail.py:32-37`, and the sole `object_detail.html` for the five group-only packs. 03-03 owns the file, passes `entry.group`/`presentation`/`component`, forbids re-allocation, and tests all five packs through the real fallback with a supplied component. 04-01 extends to resolved explicit group IDs and the request-aware hook via the real view. Standalone `render_group` callers (`test_layout_packs.py:69-75`, `test_heading_level.py:44-47`, `od/test_icons.py:11-15`) keep a local projection. |

**Genuinely unresolved findings**

- **LOW, open question, plans 04 and 09.** `src/crud_views/templates/crud_views/view_detail.content.html:1-3` is a stale core template that loads a nonexistent `object_detail` tag library and calls `render_object_detail` without `layout`. It has no consumer (`cv_content_template` points at the object-detail app's copy, `mixins.py:20`), so it is not a product regression and falls under the phase's "unrelated cleanup" exclusion. It needs only a recorded disposition: name the object-detail app's content template as the sole supported `object_detail_id` path in 04-01, and list the stale file in 09-03's handoff so Phase 7's on-disk leaf inventory does not classify it. No HIGH or MEDIUM finding is open.
