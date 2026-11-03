I verified the plans against the checkout. Every file the plans cite exists at the stated seams, all three cached interpreters and the vitest/mkdocs/ruff entry points are present, and the research's defect claims (title-slug IDs, no active panel, standalone modal icon, alias accepted with False) reproduce in source. The review below is organized per plan as required; `file:line` references are to the current working tree.

## 06.5-01

**Summary.** The plan correctly targets the only two producers (`CvHeadingNode.render` at `src/crud_views/templatetags/crud_views.py:339-353` and the layered table in `src/crud_views/lib/button_classes.py:135-155`) and the one stock modal site (`src/crud_views/templates/crud_views/modal/content.html:3`). The size/level split is sound and default bytes can stay identical. Two mechanics are unsettled, and one existing guard test will fail as written.

**Strengths**
- The size rule matches current behavior exactly: today `classes = [f"h{self.level}"] if rendered != self.level else []` (`crud_views.py:348`), so "implicit size only on level change" preserves every golden in `tests/test1/golden/heading_level/`.
- Correct reading of the registry: `get_button_class` uses presence not truthiness (`button_classes.py:151-153`), and host validation already keys on `:icon-host` with `value.format(name_class="x")` (`button_classes.py:258-262`), so the new `heading*:icon-host` keys get E363 for free.
- The plan knows W362 only accepts `key in DEFAULT_BUTTON_CLASSES or _is_action_mode_key(key)` (`button_classes.py:300-302`) and explicitly extends recognition for the optional location keys without prefilling `None` defaults.
- Host-vs-element split reuses `resolve_icon_name_class` (`src/crud_views/lib/icons.py:248-267`), the same detector `icon_host_keys` uses for buttons (`src/crud_views/lib/view/button_data.py:99-108`), so a disabled host slot cannot fall back to an inline duplicate.

**Concerns**
- **HIGH: the KEYS-04 guard will fail in this plan's own verify.** `tests/test1/test_button_classes.py:95` asserts `len(EXPECTED_KEYS) == 74` and `:102-106` parses "The default table has 74 keys" from `docs/reference/buttons.md:147`. Adding six `heading:size-N` plus shared/location icon keys to `DEFAULT_BUTTON_CLASSES` breaks both. `docs/reference/buttons.md` is not in plan 01's or plan 02's `files_modified`, yet task 01-02's verify selects `-k 'button_classes'`. Plan 07-03 touches `buttons.md` only for the alias.
- **MEDIUM: no class-composition mechanism for host classes.** `cv_heading` accepts exactly one `class=` expression (`crud_views.py:370-373`). The action says "attach host_class to the actual heading alongside modal-title" but the only template-level composition is `|add`, and `""|add:" modal-title"` yields a leading space, so `class=" modal-title"` and the `modal_detail.html` golden (`tests/test1/test_heading_level.py:95-99`, `:165`) would change. Acceptance "size omission preserves existing tag bytes" is unachievable without defining this.
- **LOW:** "explicit size always resolves the key" produces `<h3 class="h3">` when rendered level equals size. Harmless, but the contract should say so, or suppress when equal.
- **LOW:** the modal template has a literal space between `{% cv_header_icon %}` and `{% cv_header %}` (`modal/content.html:3`); the migrated template must keep it or the modal golden drifts for element icons.

**Suggestions**
- Add `docs/reference/buttons.md` and the `EXPECTED_KEYS` update to plan 01-02's files, and quote the new count.
- Give `cv_heading` an optional `icon=` kwarg taking the `HeadingIconPresentation`: append `host_class` to the class list and emit `inline_html` before the body. One tag, no string concatenation in templates, and the `class=""` edge case stays byte-identical.
- State that `_heading_class` reads `_settings_layer()` uncached (or hooks the same `setting_changed` reset at `button_classes.py:120-122`), since the merged `_button_classes_cache` cannot answer layer-first questions.

**Risk: MEDIUM.** Design is right; the plan will not pass its own verify until the key-count guard and class composition are addressed.

## 06.5-02

**Summary.** Migrates the two host pages and the two plain icon-bearing group layouts, and publishes an executed recipe. The site inventory is accurate: the test host nests `<h3>` inside `<h5 class="d-flex">` (`tests/test1/app/templates/app/crud_views.html:14-27`), the demo hardcodes `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`), and split-card/striped-rows render the icon as a sibling outside the heading (`layouts/split-card/group.html:8-9`, `layouts/striped-rows/group.html:4-5`). The proposed golden exclusion rule is the weak point.

**Strengths**
- No golden under `tests/test1/golden/` captures the host wrapper (grep for the flex wrapper or `<h3>` returned nothing), so rewriting the test host does not cascade into unrelated goldens.
- `tests/test1/od/test_icons.py:36-45` asserts `'<i class="truck'`; `render_icon("truck", css="me-2")` still yields `class="truck me-2"`, so moving icons to the shared inline slot keeps those assertions green.
- The executable-docs pattern (`tests/test1/test_conditional_migration_docs.py:31-38`) is the right analog for `test_heading_docs.py`.

**Concerns**
- **MEDIUM: "card-header ancestor" exclusion is ambiguous.** `test_heading_level.py:27` currently excludes `ancestor-or-self::h5[contains(@class,'d-flex')]`. The replacement "page card-header ancestor" collides with `layouts/card-rows/group.html:3-4` and `layouts/striped-rows/group.html:3-5`, which put their `cv_heading` inside `<div class="card-header">`. `od_card-rows` / `od_striped-rows` goldens are built via `_render_group` and would be emptied, tripping `assert actual` at `:97`.
- **LOW:** `tests/test1/test_manage.py:273` selects `h3, h4` on a page that may extend the host; a `<h1 class="h3">` title changes that list. Add to read_first.
- **LOW:** split-card today styles its icon `text-default fs-5 me-2` (`split-card/group.html:8`); the shared default `me-2` drops size/color. The plan says to record it, but it must land as an intentional-markup entry in plan 09's CHANGELOG, not just a SUMMARY note.
- **LOW:** `tests/test1/od/test_icons.py` is affected by 02-02 and 03-01 but owned by no plan.

**Suggestions**
- Mark the host title with a host-specific attribute (e.g. `data-cv-host-title`) and exclude on that, not on a Bootstrap class.
- Add `test_manage.py` and `od/test_icons.py` to read_first.

**Risk: MEDIUM.** Scope is right; the exclusion rule needs a precise selector.

## 06.5-03

**Summary.** The strongest plan. It fixes the two real defects (`forloop.first` on the trigger but `tab-pane fade` without `active` in `layouts/tabs-vertical/group.html:2`, and title-slug IDs plus fixed `objectDetailAccordion` in `accordion/object_detail.html:2`) by projecting identity once in `render_object_detail`, which today renders a fresh context with only `groups`/`layout` (`templatetags/crud_views_object_detail.py:38`).

**Strengths**
- The encoding is injective. After `cvod-c{n}-{token}` the next segment is one of `-s{m}-`, `-i{d}`, `-root`, `-tabs`, `-content`, and the token grammar `[A-Za-z][A-Za-z0-9_-]*` cannot produce a `-s`/`-i` ambiguity because lengths are explicit. All characters are selector-safe for `data-bs-target="#..."`.
- Explicitly keeps `group`/`prop` in context, so copied layouts and `test_layout_packs.py:48-70`, `test_layout_a11y.py` keep working, and `render_group(..., presentation=None, component=None)` is backward compatible with `{% render_group group layout=layout %}` callers (`object_detail.html:3`, `test_heading_level.py:46`).
- Standalone `render_group` gets a local projection and omits `data-bs-parent`, closing a real gap in the accordion template (`accordion/group.html:14-16`).
- Golden normalization is bounded to generated attribute values; `od_accordion.html` is the only heading golden carrying a target.

**Concerns**
- **MEDIUM:** collision registry is introduced in 03-02 ("render-local registry ... explicitly carry into nested fresh contexts") and redesigned in 04-02 ("own on the earliest non-base render-context frame"). Two implementations of one mechanism across waves invite rework; 03-02 should implement the explicit-transport half and leave frame ownership entirely to 04.
- **LOW:** `tabindex=0` on every panel is the APG recommendation only when the panel has no focusable content; say that in the contract so themes do not treat it as mandatory.
- **LOW:** the panel still renders a visible `cv_heading level=5` with the title (`tabs-vertical/group.html:6`) and `test_heading_level.py:108` depends on its `mb-1` class; the plan should state that this heading is unchanged.

**Suggestions**
- Name the standalone tab panel's `aria-label` source (escaped `group.title`) in acceptance.
- Add `od/test_icons.py` to files, since `test_group_icon_tabs_vertical*` exercise the migrated button.

**Risk: LOW-MEDIUM.**

## 06.5-04

**Summary.** Adds stable supplied identity and bounds collision detection to one outer render. I traced the Django mechanics the plan relies on: `Template.render` pushes a render-context frame, `ExtendsNode` uses `_render` without pushing, `IncludeNode` pushes a new frame on the same `RenderContext`, and the backend `tpl.render(dict, request)` used by the tags creates a new `Context`. So "earliest non-base frame" plus explicit transport into the fresh backend contexts is a workable boundary.

**Strengths**
- Three-series verify is mandatory, which is right for an approach touching `render_context.dicts`.
- `mixins.py:44-51` is the correct threading point and the plan keeps `self.object`; `parse_property_display` at `config.py:88` makes `id` a pure additive key.
- The page/modal namespace obligation is placed on the application, matching D-05/D-07.

**Concerns**
- **MEDIUM: config errors surface only at request time.** Dict groups are validated by E242–E245 at check time (`mixins.py:72-110`), but an invalid or duplicate supplied `id` would raise from `PropertyGroupConfig` inside `get_property_display` (`mixins.py:34-39`) during a request. For a feature justified by a Selenium suite, a check (next free `E24x`) for token grammar and intra-view duplicate group ids is cheap and consistent.
- **MEDIUM:** "a request-aware hook can select distinct page/modal namespace values" — the same view serves both (`AuthorModalDetailView`, `tests/test1/app/views.py:895-900`, with `cv_modal = True`). The plan should name the mechanism the example uses to detect a modal request (the existing `X-CV-Modal` header path) so the recipe is not left to the executor.
- **LOW:** `resolve_group` at `resolvers.py:248` constructs `ResolvedGroup`; confirm kwargs so appending `id` is positional-safe (plan already says append).

**Suggestions**
- Add a system check for supplied ids; add a test that `override_settings`/`RequestContext` reuse does not leak between two `render_to_string` calls.

**Risk: MEDIUM.** Mechanism verified feasible; needs the check and the modal-detection detail.

## 06.5-05

**Summary.** Adds an extension-owned asset that instantiates Bootstrap `Tab` for owned tablists on page load and `cv:modal:loaded`, disposing on `cv:modal:unload`. The lifecycle hooks exist (`modal.js:23-24`, used by `tooltip.js:40-55`), and `register_assets` (`assets.py:56-67`) is the documented path. Two integration gaps and one design inconsistency.

**Strengths**
- Reuses the tooltip init/dispose shape including late-load handling (`tooltip.js:33-37`) and fixes its descendants-only limitation.
- Bootstrap already instantiates only *active* triggers on window load, so initializing all owned triggers via `getOrCreateInstance` is a safe superset; dispose removes the namespaced keydown handler.

**Concerns**
- **MEDIUM: bypasses `cv.adapters`.** `adapters.js:53-94` defines `modal`, `tooltip`, `collapse`, `alert`; no other shipped script references `bootstrap.` directly (grep). PROJECT.md lists the adapter layer as the theme seam and relies on it for "absence of global bootstrap". A stock asset with direct `bootstrap.Tab` becomes the first non-adapter Bootstrap dependency and lands in Phase 7's frozen inventory. The research's "no competing keyboard handler" argument does not require skipping a thin `cv.adapters.tab = {init(el), dispose(el)}`.
- **MEDIUM: registry-pinning tests not in scope.** `tests/test1/test_assets_bundles.py:10-12` pins the rendered script list; `test_pipeline_sources.py`/`test_pipeline_resolver.py` enumerate bundles for `cv_sources`. Only tests using the `asset_registry` fixture (`tests/test1/conftest.py:12-20`) see a cleared registry; the rest will now see `crud_views_object_detail`. None of these files is listed in plan 05.
- **LOW:** `CrudViewsObjectDetailConfig` (`apps.py:5-8`) has no `ready()` today; `override_settings(INSTALLED_APPS=...)` re-runs ready, so the identical-registration guard must compare against `get_registered()` rather than catch-and-ignore. The plan says this; just make sure the test exercises `apps.set_installed_apps`.

**Suggestions**
- Route through a minimal adapter entry; keep Bootstrap's keyboard behavior as is.
- Add `test_assets_bundles.py`, `test_pipeline_sources.py`, `test_pipeline_resolver.py` and the pipeline docs to read_first/files.

**Risk: MEDIUM.**

## 06.5-06

**Summary.** Small, well-bounded. `_resolve_badge_css` (`resolvers.py:94-110`) already branches callback → nonempty map → fixed color and short-circuits on `None`; the plan refactors it into one result and appends two fields. Existing precedence tests (`od/test_resolvers.py:316-374`) and the `badge_css`-before-`template` selector (`templatetags/crud_views_object_detail.py:79-85`) are correctly identified.

**Strengths**
- Appending fields preserves every kwargs-based constructor in `od/test_templatetags.py`; no positional callers found in src.
- Keeps the empty-map fallthrough and nonempty-map miss as distinct cases, which D-13 requires.
- The stock `types/default/badge.html` is untouched, so default bytes are unchanged.

**Concerns**
- **LOW:** `if prop.badge_css:` is truthiness; a resolved `""` color yields `text-bg-` (truthy). The plan preserves this; document it as existing behavior rather than contract.
- **LOW:** `_resolve_badge_label` stays a separate call; fine, but the acceptance "one result" should say color/pill/css, not label.

**Risk: LOW.**

## 06.5-07

**Summary.** Removes the alias and the obsolete template guard with a targeted before-validator. The source inventory is complete: field and after-validator (`src/crud_views/lib/view/card.py:11,31-32`), runtime branch (`src/crud_views/lib/views/card.py:51-52`), guard (`src/crud_views/lib/view/button_data.py:126-130`), and every fixture/test/doc that spells the alias (grep listed 20 sites; all are in the plan's files or plan 09's).

**Strengths**
- Before-validator on raw mapping membership is the right tool; `CardAction` has no `extra` config, so unrelated keys stay ignored exactly as today.
- Catches the validator-bypass test (`test_card_label_mode_render.py:474-476`) and the doc-contract marker `"no_label=True"` (`test_label_mode_docs.py:217`) that would otherwise break silently.
- Fixture migration at `tests/test1/app/views.py:80` keeps rendering identical because both spellings resolve to `"icon"` at `views/card.py:49-52`.

**Concerns**
- **LOW:** between wave 1 and wave 6, `docs/migrating-1.0.md:142,157` and `CHANGELOG.md:137-140` will state that `cv_no_label` raises and `CardAction(no_label=True)` keeps working, contradicting code. Acceptable on a branch, but plan 09 must *amend* those existing Unreleased entries, not append new ones.
- **LOW:** `model_validate_json` delivers a Python dict to a before-validator in Pydantic v2 (observed 2.14), so `Mapping` membership works; add the pinned version to the summary since the plan relies on it.

**Risk: LOW.**

## 06.5-08

**Summary.** A dedicated loopback fixture and Chromium runner on port 8145, modeled on `tests/browser/conditional_formsets_server.py` and `conditional-formsets.cjs`. The case list is the right one (keyboard before click, one/two groups, page/modal isolation, stable selectors, native projection). The asset-sourcing gap is the main risk.

**Strengths**
- Separate port and files (8143/8144 are taken by `modal-focus.cjs:22` and `conditional-formsets.cjs:28`), preserving 6.4 evidence.
- Improves on the analog by discovering Playwright/Chromium rather than hardcoding a home-directory npx cache (`conditional-formsets.cjs:123-125`).
- Fails on skipped cases, page errors and unloaded assets; records versions and hashes.

**Concerns**
- **HIGH: network-bound gate.** The only stock host loads Bootstrap, FontAwesome and jQuery from CDNs (`tests/test1/app/templates/app/base.html:13-24`); there is no local copy (`node_modules/bootstrap`, `@fortawesome` absent). "Serve ... pinned Bootstrap 5.3.3" does not say from where, and the icon-font assertions depend on cdnjs. Research recommended local/recorded assets precisely so a failed download cannot masquerade as failure or success. As written the phase gate is not reproducible offline or in CI.
- **MEDIUM:** "verify stable selectors ... including translated titles" needs a language switch in the fixture (`LANGUAGE_CODE`/`Accept-Language`); not specified.
- **LOW:** the two existing runners disagree on how Node is selected (`modal-focus.cjs:11-17` reads `06-JS-RUNTIME.json`; `conditional-formsets.cjs:12`). Pick one and say which.

**Suggestions**
- Vendor the exact Bootstrap/icon files under `tests/browser/assets/` with recorded SHA-256, or declare network a precondition and fail fast with a distinct exit code.

**Risk: MEDIUM-HIGH** until asset provenance is fixed.

## 06.5-09

**Summary.** Closes with executed recipes, paired Breaking/migration entries, full three-series/JS/docs/lint gates, the existing `lifecycle` browser case (`conditional-formsets.cjs:57`, verified present) and a Phase 7 inventory. `06.5-VALIDATION.md` exists in draft, so "update" is correct.

**Strengths**
- Full-matrix honesty: three Python 3.12 series are not represented as the 3.12–3.15 matrix.
- Inventory validation test asserts names against real exports, consistent with the Phase 7 `test_stability_doc.py` direction.
- Traceability is already reconciled (`REQUIREMENTS.md:169,172` promote LATER-01/04), so research open question 5 needs no work.

**Concerns**
- **MEDIUM:** `docs/reference/object_detail_layout_packs.md` is screenshots only today (no override guidance), so 09-01 is a large authoring task compressed into a tracer; the `tokens` estimate (24k) looks low for three recipes plus full projection docs.
- **LOW:** the CHANGELOG Unreleased section already contains alias/guard statements (`CHANGELOG.md:131-140`); the plan must edit them in place to keep 1.0.0 notes self-consistent.

**Risk: LOW-MEDIUM.**

## Cross-plan assessment

**Dependency ordering** is sound: 01 → 02 → 03 → {04, 05} → 08 → 09, with 06/07 in wave 1. File overlaps are serialized (02/03 on `test_heading_level.py`; 03/04 on `presentation.py`; 04 after 06 on `resolvers.py`). Two gaps: `buttons.md` has no owner for the new heading keys, and `od/test_icons.py` plus the asset-pinning tests are affected by 02/03/05 without being listed.

**Goal coverage.** PRES-01 through PRES-06 each have a producer, a consumer migration and executed evidence. The one place the plans would not achieve the goal as written is PRES-06's real-browser gate, which depends on CDN availability.

**Scope.** No creep found. The alias and badge plans are tight; the heading registry adds roughly ten keys, which is proportionate.

**Security.** Threat registers are concrete and the escaping paths cited (`conditional_escape` in the heading node, autoescaped tag context) are the real ones. Supplied-ID grammar removes selector-injection risk.

**Overall risk: MEDIUM.** Fix before execution: (1) KEYS-04 count and `buttons.md` ownership in plan 01; (2) heading class composition in plan 01; (3) golden exclusion selector in plan 02; (4) browser asset provenance in plan 08. Recommended but not blocking: a system check for supplied group ids (plan 04), routing tab instantiation through `cv.adapters` (plan 05), and adding the registry-pinning tests to plan 05.
