I'll verify the revised plans against the repository, starting with the H3 and A14–A18 seams.
Plans are at `2b672aa`. I'll check the H3 harness and A14–A18 source seams against the revised tasks.
Reviewed at `2b672aa` against current source. Plans are pre-execution: cited defects are still in the tree. Intel `API-SURFACE` is empty and `api-map.json` is absent, so signatures are uncheckable; the checks below are direct source reads. H1/H2 and A1–A13 stay closed.

## 06.5-01

**Summary.** Size and one host/element icon still belong on `CvHeadingNode` (`src/crud_views/templatetags/crud_views.py:348-376`) and the modal line (`src/crud_views/templates/crud_views/modal/content.html:3`). The plan owns the class-table guards and composes `icon_class` outside the single `class=` argument.

**Strengths.** Implicit size matches `h{level}` only when the rendered level changes (`crud_views.py:348`). The modal golden’s leading space (`tests/test1/golden/heading_level/modal_detail.html:1`) is the literal separator the plan keeps. Task 01-02 updates `EXPECTED_KEYS`, `len == 74` (`tests/test1/test_button_classes.py:94-106`), the five-host guard (`:310-313`), and the one count sentence (`docs/reference/buttons.md:147`) before that verify. W362 still accepts only default or action-mode keys (`src/crud_views/lib/button_classes.py:301-318`), which the plan extends rather than bypassing.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-02

**Summary.** Host pages still nest `h5.d-flex > h3` (`tests/test1/app/templates/app/crud_views.html:13-22`) and hard-code `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`). Split-card and striped-rows still put the icon outside the heading.

**Strengths.** `data-test-page-title` replaces the `h5.d-flex` exclusion (`tests/test1/test_heading_level.py:26-27`) without matching `card-header` wrappers. Consumers use `icon_class`, not string joins.

**Concerns.** None. **A14 sign-off: FULLY RESOLVED.** Task 02-01 reads `examples/bootstrap5/project/templates/project/crud_views.html`, extracts the unique `cv_heading_icon` assignment plus the complete `cv_heading` block, compiles that unchanged fragment, and fails on zero or multiple sites. That is direct example coverage, not the docs-fence test in 02-03.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-03

**Summary.** Triggers use `forloop.first` and slugified titles (`layouts/tabs-vertical/object_detail.html:6-15`); panels are always `tab-pane fade` (`layouts/tabs-vertical/group.html:2-5`). The accordion root is fixed (`layouts/accordion/object_detail.html:2`). `render_object_detail` renders a fresh context with only `groups` and `layout` (`templatetags/crud_views_object_detail.py:38`).

**Strengths.** Not mutating `ResolvedGroup` (`resolvers.py:58-64`) is required. `{% load crud_views %}` is required on `tabs-vertical/object_detail.html:1`, which currently loads only `crud_views_object_detail`. `cv_icon` there is the local tag (`crud_views_object_detail.py:101-104`); both `cv_icon` implementations call `render_icon`, so load order does not change icon bytes. Accordion group already loads `crud_views` (`accordion/group.html:1`).

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-04

**Summary.** Group config has no `id` (`config.py:56-62`). `cv_is_modal_request` is `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:57-59`); `modal.js:140` and `:177` send that header. `AuthorModalDetailView` sets `cv_modal = True` (`tests/test1/app/views.py:894-896`), so the flag alone is not the discriminator.

**Strengths.** Appending `ResolvedGroup.id` keeps existing keyword constructors valid. Collision state stays on the earliest non-base render frame, with explicit transport into the fresh contexts at `crud_views_object_detail.py:38,54`. Startup checks stay out of scope.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW. The frame rule is specified and required on Django 4.2/5.2/6.0.

## 06.5-05

**Summary.** Page-load `Tab` construction does not cover HTML injected after `window` load. `modal.js:23-24` already names `cv:modal:loaded` / `cv:modal:unload`. `register_assets` raises on any existing key (`src/crud_views/lib/assets.py:66-67`); `get_registered()` exists at `:71-76`.

**Strengths.** Root-itself matching, no `show()`, and unmarked roots with no `bootstrap` lookup are explicit. Rejecting `cv.adapters.tab` remains a stated boundary. Core still renders first (`assets.py:99-101`).

**Concerns.** None. **H3 sign-off: FULLY RESOLVED.** Current `tests/js/helpers/load.js:8,32-33` loads only core, and `tests/js/runtime-contract.test.js:17-32,69-82` discovers every `tests/js/**/*.test.js` while copying only core static and requiring every discovered file to pass. Task 05-01 adds `loadScript(name, packageName="crud_views")` with a finite checkout map resolved from `import.meta.url`. Task 05-02 copies `src/crud_views_object_detail/static/crud_views_object_detail/js` at that same relative path, adds `object-detail-tabs` to `requiredFiles`, and runs `runtime-contract.test.js` without weakening discovery, pass counts, Node-only PATH, or the missing/invalid interpreter negatives.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-06

**Summary.** Badge CSS is one walk: `None` returns first, then callback, nonempty map, then fixed color (`resolvers.py:94-110`). Template choice is `badge_css` before explicit `template` (`crud_views_object_detail.py:80-86`).

**Strengths.** Appending `badge_color` / `badge_pill` preserves keyword construction. Unresolved defaults stay `None` / `False`. The stock badge template is untouched.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-07

**Summary.** `no_label` is still a field (`src/crud_views/lib/view/card.py:11`). The after-validator only rejects it when true beside `label_mode` (`:31-32`). Runtime treats a truthy value as icon mode (`src/crud_views/lib/views/card.py:49-52`). Deleting the field without a before-validator would drop `no_label=False`.

**Strengths.** Membership, not truthiness, matches D-09. Non-mappings return unchanged. Plan 07 depends on plan 01 and must not rewrite the heading count. Contradictory changelog bullets stay for plan 09.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-08

**Summary.** Server tests cannot prove ArrowDown on tabs injected after `window` load. The host loads Bootstrap 5.3.3, Font Awesome 6.7.2, and jQuery 3.7.1 from CDNs with SRI (`tests/test1/app/templates/app/base.html:13-30`).

**Strengths.** Keyboard-before-click, distinct `author-page` / `author-modal` tokens via `cv_is_modal_request`, and fail-closed asset preflight remain in the task. The config test stays outside `tests/js`, so the Node-only suite does not gain a Python requirement.

**Concerns.** None. **A16 sign-off: FULLY RESOLVED.** `tests/browser/conditional_formsets_server.py:485-487` rejects 8143; `modal-focus.cjs:21` binds 8143; the conditional runner defaults to 8144 (`conditional-formsets.cjs:28-31`). Task 08-01 rejects 8143, 8144, empty, nonnumeric, fractional, and out-of-range values in both the Node runner and the Python entry point before discovery, Django init, bind, or ready, and `presentation-config.test.cjs` invokes those entry points.

**Suggestions.** None.

**Risk.** MEDIUM. New browser process code, with a fail-closed network precondition. Port isolation itself is specified.

## 06.5-09

**Summary.** Copied tabs still need `presentation.control_id`, `panel_id`, and `selected`. `CHANGELOG.md:131-140` still says the template guard raises and `CardAction(no_label=True)` is unaffected. `cv_sources` filters bundles by `keys` (`src/crud_views/lib/pipeline.py:86-90,127-141`).

**Strengths.** Task 09-02 edits those changelog bullets in place and executes an explicit `keys=` recipe. The 36k budget does not cut acceptance. Focused `<verify>` blocks are incremental; the plan-level gate still requires the three full suites, both JS lanes, docs, ruff, and both browser commands.

**Concerns.** None.
- **A15 sign-off: FULLY RESOLVED.** `src/crud_views/lib/formsets/layout.py:19,30` starts a fresh `render_to_string` context. Tasks 09-01/02 document that untransported fresh backend renders are a new collision boundary even inside one assembled page, and contrast them with includes and the library’s own transported `render_object_detail` / `render_group` calls. Formset rendering is not changed.
- **A17 sign-off: FULLY RESOLVED.** Ordinary Vitest includes only `tests/js` (`vitest.config.js:6`). Task 09-03 and the plan gate run `vitest.integration.config.js` with `CV_FRAGMENT_PYTHON` set to the Django 5.2 interpreter. The existing suite asserts six pytest passes and six DOM/FormData records (`tests/js-integration/formset.test.js:140-145`; `tests/test1/test_fragment_authorization.py:1310-1313`).
- **A18 sign-off: FULLY RESOLVED.** `cv_header_icon` remains a real tag (`src/crud_views/templatetags/crud_views.py:312-315`). Task 09-03 inventories it as retained standalone behavior and superseded as the heading-icon recipe, with a render regression. Phase 7 still assigns tiers.

**Suggestions.** None.

**Risk.** LOW.

## Cross-plan

Wave order holds: 01/06, then 07 after 01, 02, 03, then 04/05, then 08, then 09. Shared `buttons.md` work is ordered. D-01–D-17 are unchanged. Form-leaf, auth, deletion, and conditional contracts are not reopened.

| ID | Verdict | Why |
|---|---|---|
| H3 | CLOSED | Plan 05 owns package-aware `load.js` and sandbox inclusion of the real extension asset; `runtime-contract.test.js` stays Node-only and must pass the new file. |
| A14 | CLOSED | Plan 02-01 compiles the title fragment read from the example file itself. |
| A15 | CLOSED | Plan 09 documents and tests untransported `render_to_string` boundaries versus transported library renders. |
| A16 | CLOSED | Plan 08 rejects 8143/8144 and invalid overrides in both entry points before bind. |
| A17 | CLOSED | Plan 09 names the integration config and the existing six-record fragment gate. |
| A18 | CLOSED | Plan 09 inventories retained `cv_header_icon` separately from the new heading contract. |

**Unresolved findings:** none.
