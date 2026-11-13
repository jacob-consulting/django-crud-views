# django-crud-views — Concept Review Follow-ups

## What This Is

`django-crud-views` is a reusable Django package: CRUD class-based views grouped into ViewSets, Bootstrap 5 theme,
plus four extension apps (object detail, workflow, polymorphic, guardian). This milestone lands the five ranked findings
of the icons/buttons/theming concept review (`superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md`)
before 1.0.0, following the phase plan in `superpowers/plans/2026-10-24-concept-review-followups.md`. The audience is
package users and theme authors (e.g. a Tabler theme) who need a theme surface that is consistent, overridable and
frozen at 1.0.0.

## Core Value

Every public theme name (label-mode defaults, class-table keys, icon names, leaf templates, JS adapters) settles once,
consistently, before 1.0.0 freezes it — no public name changes twice.

## Requirements

### Validated

<!-- Inferred from the existing codebase (0.30.0 + unreleased). -->

- ✓ ViewSet → CrudView registry with auto-generated URL patterns, nested parent/child ViewSets — existing
- ✓ List/Detail/Create/Update/Delete/Action/Ordered views with permission-required variants — existing
- ✓ django-tables2 / django-filter / crispy-forms integration — existing
- ✓ Icon registry (`crud_views.lib.icons`: `register_icon_library`, `register_icons`, `DEFAULT_ICONS`, `BOOTSTRAP_ICONS`) — existing (0.30.0)
- ✓ Button class table (`DEFAULT_BUTTON_CLASSES`, `location:slot[:mode]` keys, W362 checks) — existing
- ✓ Label modes (`icon` / `both` / `label`) for context, list and card actions with setting/ViewSet/view maps — existing
- ✓ Leaf templates (`tags/button/action.html`, `menu_item*.html`, `container.html`) and the `cv_button_data` contract — existing
- ✓ Single alert frame `tags/alert.html` + `alert_data()` (#250) — existing (unreleased)
- ✓ Accessible card pagination with registry icons (#241) — existing (unreleased)
- ✓ `cv.adapters` JS layer for modal, tooltip, collapse — existing
- ✓ Workflow, polymorphic, guardian, object-detail extension apps — existing
- ✓ Django system checks for ViewSet/CrudView configuration — existing

- ✓ **1A** Project-wide label-mode floors, lazy accessor, E108 and instance-safe card overrides — Phase 1
- ✓ **1C** Option A `form:<kind>:<mode>` grammar, finite independent locations, W362 validation and live key-count guard — Phase 2
- ✓ **1B** Filter toggle label modes, constant translated labels, optional icons and accessible disclosure — Phase 3
- ✓ **3A** Alert dismiss through `cv.adapters.alert` (`data-cv-alert-dismiss`, fallback `el.remove()`), golden-first,
  core templates keep `data-bs-*` only in the dropdowns — Phase 4
- ✓ **3B** Table pagination from the `page-previous`/`page-next` registry icons with the card's accessible markup
  (#241); one shared `pagination:hidden-label` key (default `visually-hidden`) for both — Phase 5
- ✓ **2** Form buttons through the `tags/button/form.html` leaf (#257): `"form"` location with owner-first map
  resolution, crispy `Submit`/`Button`/`Reset` as escaped adapters, semantic icons `save`/`cancel`/`filter-reset`,
  form-only E210/E211/W291/W292, `<input>` → `<button>` (Breaking), POST data unchanged, example uses `both` — Phase 6
- ✓ **6.1** Cancel as a native link (#275): `form:cancel-tag` (`button` default / `a`), `Button(tag=...)` override,
  `cv_tag` leaf field, E365; link drops button-only attrs and falls back to a button when disabled or URL-less;
  `viewset.js` unchanged — Phase 6.1

- ✓ **6.2 retained scope** Request authorization, fragment ancestry, inactive-actor denial, named Guardian policy, nested-create state agreement and blocked-delete UI — Phase 6.2; final Playwright acceptance passed. Transferred write-boundary obligations remain active below.

- ✓ **6.4** Conditional ownership/reset, field-aware persistence and edit-only identity policy; page/modal/nested formset lifecycle, scoped A19 round trips and paired migration contracts — Phase 6.4; canonical10/10, Chrome/Orca UAT and independent security44/44 accepted. Storage/application-hook and broader concurrency/PK exclusions remain explicit.

- ✓ **6.3** Callback-safe deletion preview, exception propagation, database alignment and bounded Guardian policy review completed in the roadmap; broader custom-PK compatibility remains the separately tracked issue #286 follow-up.

- ✓ **6.5** Heading presentation, stable object-detail identity/tab selection, semantic badges and alias cleanup; PRES-01–06, paired migrations and public-surface handoff — Phase 06.5; UAT 28/28, canonical verification passed.

- ✓ **6.6** Theme-adoption seams (#277–#280): page-owned forms/helper diagnostics, atomic theme label defaults, independent action-group/alert keys, tested migrations and verified companion delivery — Phase 06.6; canonical25/25, UAT7/7 and security27/27. Runtime/browser limits and three unchanged companion failures remain explicit.

- ✓ **6.7** Dynamic Cancel defaults, independent captured query restoration, destination permissions and guarded template migration — Phase 06.7; canonical32/32 and UAT5/5 passed. Chrome/Orca stock-theme scope and unchanged success-navigation limits are recorded.

- ✓ **6.9** Permission-aware protected blocker links, ordered escaped context, full-page navigation and executable copied-template migration — Phase 06.9; canonical31/31 and explicit confirmation of all 19 UI state rules passed. Verification refreshed after the runnable Library Contract example with Alice/Bob permission contrast.

- ✓ **6.8** Short icon-action tooltips retain full accessible labels; visible labels suppress generated tooltips, with tested copied-template migration — Phase 06.8; refreshed canonical30/30 and existing UAT3/3 passed.

- ✓ **6.10** Plain escaped protected labels, one protected-first display budget (default 50, explicit None unlimited), preserved cascade links and complete deletion enforcement — Phase 06.10; all five plans, six DPV requirements and seven human UAT checks complete. Supersedes Phase 06.9 protected-destination linking; total inspection/filtering/query cost remains unbounded.

- ✓ **6.13** Opt-in workflow view permission with explicit per-transition rules, separate optional request gate, real request/history regressions and complete consumer recipe — Phase 06.13; canonical9/9, WFP-01–05 complete. Default change permission and production behavior preserved.

- ✓ **6.13.1** Model business blockers, shared explicit-actor workflow execution, opt-in native transition buttons, bounded same-database history and rollback-safe refusal recovery; WFX-01–05 delivered, two human UAT checks passed, independent code review clean and all 15 security threats closed.

- ✓ **6.14** Empty `card_root`/`card_header` insertion blocks and an executable cards-first/secondary-table recipe — Phase 06.14; canonical12/12, unchanged default bytes, inherited actions and independent navigation verified.

- ✓ **6.15** Capitalized polymorphic selector labels, exact-model detail groups and exhaustive static validation, documented and adopted in the reference consumer — Phase 06.15; canonical16/16, UAT2/2, security12/12.

- ✓ **6.16** Scalar choice labels with raw/custom ownership, explicit inherited help-text policy, exact textual empty markers and executable composition/migration guidance — Phase 06.16; canonical21/21, all five ODV requirements verified, security11/11 and clean independent review.

- ✓ **6.17** First-open projected accordion groups and lazy theme-owned tab initialization/disposal with exact-source migration recipes — Phase 06.17; canonical15/15, ODT-01–05 complete, clean deep review and security9/9.

- ✓ **6.18** Ancestor authorization for nested ViewSets: one request-local engine validates declared ancestry and enforces typed AncestorPolicy/AncestorPermissions (Read/Write and exact action pairs, full or nearest-only cascade, core or Guardian provider with separate fallback) before independent endpoint-local gates; top-level views do no ancestor work. Legacy `cv_guardian_parent_*` fields removed with paired Breaking/migrating-1.0 guidance — Phase 06.18; ANCE-01–08 complete, re-verification 52/52, UAT 71 rows (gap G-06.18-2 closed by plan 13), measured costs in 06.18-COSTS.md.

- ✓ **6.19** `Table` honours a declared `Meta.sequence` instead of overriding it; tables without one keep `actions` last. The actions column is configured through django-tables2 `Meta` (`sequence`, `exclude = ("actions",)`), documented in the list view reference and FAQ (#337) — Phase 06.19; re-scoped to a one-line fix after the convenience design (automatic `actions` append, `cv_list_actions = None` removal) was reverted, verification 9/9, full suite 12197 passed.
- ✓ **6.21** Snippets a view renders for its own page (header, paragraph, list/card filter header, success and error message) can use `{{ view }}` and, on a child ViewSet, a lazy `{{ parent_object }}` added by `CrudView.cv_get_meta()`; default snippets render unchanged. Documented once in `docs/reference/templates.md` § Snippet variables and linked from messages, nested and breadcrumb pages (#339) — Phase 06.21; verification 15/15, full suite 12216 passed.

- ✓ **6.22** Database-free `viewset.E269` checks for core view and ancestor permission keys, with an executed `Meta.permissions` recipe; concrete-model vocabulary and request-time authorization preserved — Phase 06.22; verification 22/22, security 9/9, deep review clean.

- ✓ **6.20** Independent optional ViewSet display names, lazy translation at metadata resolution, plain blank validation and default-label propagation — Phase 06.20; canonical 15/15, clean deep review, security 9/9, delivered-message and breadcrumb HTML checks.

- ✓ **6.23** Explicit header-icon suppression with plain `Icon.NONE` and `Icon.VIEWSET_DEFAULT`; None-only inheritance, preserved custom content and tested migration — Phase 06.23; canonical13/13.

- ✓ **6.24** Opt-in compact formsets with explicit columns, shared desktop headings, labelled mobile cards and independent nested composition; runnable questionnaire comparison and preserved Django validation errors — Phase 06.24; six plans complete, human UAT 1/1 and canonical verification passed.

- ✓ **6.25** General inherited CompactWidgetCompatible opt-in, bounded widget-only admission bypass and executed custom Select recipe — Phase 06.25; canonical12/12, UAT1/1, six committed browser captures, security7/7 and clean deep review.

- ✓ Independent empty-default conditional/formset legend class hooks, layered overrides and escaped nested fragment rendering — Phase 06.25.1

- ✓ Choice-driven conditional groups with shared native dropdown/radio descriptors, bounded choice clearing and explicit overrides; Customer example with simple/complex navigation and reciprocal documentation — Phase 06.27; 22/22 verified, UAT 2/2.

- ✓ **6.29** Themeable Column1–Column12 via existing registry, render-local complete classes, preserved caller/template ownership and executed recipes — Phase 06.29; canonical 10/10, clean re-review after lazy-extra correction.

- ✓ Queryset-driven conditional fields with upstream/downstream examples, strict matching, documented behavior and source-bound acceptance — Phase06.30 (#360).
- ✓ Compact row borders are local opt-in via `CompactLayout.row_border=False`; Checklist demonstrates borders, compact Request Batches the borderless default; complete-frame suppression takes precedence — Phase06.30, D15.

- ✓ Developer-only core/Guardian diagnostics, explicit group setup, bounded read-only demo developer and write-gated example actions; transactional seed conflict rollback and paired migration guidance — Phase 06.31; 21/21 verified, UAT 1/1 passed, clean independent re-review.
- ✓ **6.32** Button-only workflow transition variants and icons through existing registries, with visible labels, exact fallbacks and preserved workflow behavior — Phase 06.32; canonical 7/7, decisions 9/9, clean deep review and security 6/6.

### Active

- [ ] **4** Theme surface in `docs/development/stability.md` (icons, buttons, alerts, JS, theme hooks) + guard test
  `tests/test1/test_stability_doc.py`; closes the theme part of #89

### Out of Scope

- Renaming the `cv_context_actions_label_mode` / `cv_context_action_label_mode` pair — rejected, not deferred: both names stay stable (Phase 1 decision, LATER-02 won't rename)
- E36x check for `container-tag` — tracked separately
- #211 stale-override detection — tracked separately; #259 is now owned by Phase 6.5.
- Publishing or pushing companion changes — Phase 06.6 authorized verified five-file delivery and a scoped local commit; unrelated settings and IDE metadata remain preserved.
- The 1.0.0 version bump itself — follows after Phase 4

## Context

- Brownfield: package at 0.30.0 with a large "Unreleased" CHANGELOG section heading to 1.0.0. Codebase map in
  `.planning/codebase/`.
- Source documents: the concept review note and the phase plan under `superpowers/`. The plan fixes scope, files,
  tests and acceptance per phase; Phases 1B and 2 need their own spec (brainstorm) before implementation.
- Dependency graph: 1A → 1B; 1A + 1C → 2 → 4; 3A, 3B independent but must land before 4. 1A and 1C can run in
  parallel; 1B, 3A, 3B in parallel.
- A downstream Tabler theme (`crud_views_tabler`) consumes the theme surface; it is the reference consumer for
  Phase 4's "every imported name is documented" check.

## Constraints

- **Developer maintainability**: Every decision must remain understandable, explainable, debuggable, and maintainable
  by the project's developer. Prefer bounded solutions, explicit limits, and self-contained opt-in additions proven
  downstream. Preserve working paths unless a concrete need justifies their added complexity or runtime cost.
  Simplify or narrow designs the developer cannot confidently own; passing tests alone does not justify complexity.
  Apply the project-wide [decision rule](../CLAUDE.md#decision-rule-developer-maintainability) in discussions, plans,
  implementation, and reviews.
- **Compatibility**: Without new configuration, every template renders what it renders today — goldens under
  `tests/test1/golden/` stay byte-identical except where a phase says so (2: form buttons; 3A: alert close;
  3B: table pagination).
- **Process**: One PR / branch per plan phase (`feat/label-mode-defaults`, `feat/filter-toggle-label-mode`,
  `feat/form-key-grammar`, `feat/form-button-leaf`, `feat/alert-dismiss-adapter`, `feat/table-pagination-icons`,
  `docs/stability-theme-surface`).
- **Quality gates**: `pytest tests -n auto`, vitest, `mkdocs build --strict`, `ruff check`, `ruff format --check`
  green before each push.
- **Docs**: Every public-surface change adds a CHANGELOG entry; a `### Breaking` entry also updates
  `docs/migrating-1.0.md`.
- **Hygiene**: No downstream project names in any file; line length 120; double quotes.
- **Support matrix**: Python 3.12–3.15 × Django 4.2/5.2/6.0.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Require active configured-group membership for manage diagnostics, including staff/superusers | One shared request/action policy preserves independent CRUD and ancestor authorization | Validated (Phase 06.31) |
| Roll back the entire single-database demo seed on privilege conflicts | Prevent rejected provisioning from exposing a public credential or new privileged membership; preserve existing operator grants | Validated (Phase 06.31; CR-01 fixed and independently re-reviewed) |
| Wrap the factory tooltip initializer for placement-only documentation customization | Preserve existing lifecycle safeguards, explicit placement and library defaults without changing runtime or API | Validated (Phase 06.28; 6/6, executable recipe) |
| Admit exact stock CheckboxInput through existing compact schema and crispy markup; demonstrate it in a separate Checklist ViewSet | Bounded opt-in support preserves native Django semantics, custom-widget boundaries and existing rendering; navigation-only entry keeps one shared example catalog | Validated (Phase 06.26; 17/17, UAT 2/2) |
| Header icons inherit only for None; plain Icon constants name inheritance and suppression | A bounded getter change preserves renderers and dynamic overrides while allowing custom headings to omit inherited icons | Validated (Phase 06.23; 13/13) |
| Resolve optional singular/plural display names only in get_meta; preserve unset metadata and explicit consumer overrides | One bounded opt-in seam reaches existing label consumers without new state, queries or permission changes | Validated (Phase 06.20; 15/15) |
| Keep raw values separate from choice display metadata; resolve help text without mutating shared config | Preserve existing traversal/query costs and custom-template ownership; stock leaves render exact empty text and unlocalized choice fallbacks | Validated (Phase 06.16; canonical21/21) |
| Empty card insertion blocks plus existing ViewSet configuration | Preserve default rendering and proven navigation; themes expose their own overridden blocks and applications translate recipe captions | Validated (Phase 06.14) |

| Detail groups select only explicitly declared exact model keys; static checks traverse every entry | Preserve list/dynamic override paths without fallback mutation, object queries or optional polymorphic coupling | Validated (Phase 06.15; UAT 2/2) |
| Protected labels are static; share one visible-occurrence budget with cascade details | Remove synthetic destination requests while retaining proven cascade hooks and complete enforcement; cap presentation, not total collection cost | Validated (Phase 06.10; UAT 7/7) |
| Developer maintainability is a hard constraint on every decision | The developer must be able to explain, debug, and evolve the solution; bounded scope and incremental downstream adoption keep that ownership practical | Decided (2026-11-04; project-wide) |
| Validate protected destinations after visibility filtering; preserve the shared URL hook and cascade behavior | Link only to certified same-row destinations; unavailable destinations remain readable text | Validated (Phase 06.9) |
| Dynamic Cancel uses allowed origin, configured fallback, then permission omission; successful-save navigation stays independent | Preserve independent form captures and existing success behavior; copied templates use guarded cv_cancel_url | Validated (Phase 06.7) |
| Group findings into phases by dependency, not rank order or one change | Reviewable units; #257 depends on 1A+1C; stability policy must be last | — Pending |
| Option A: `form:<kind>:<mode>`; context/list/card retain variants | Independent finite vocabularies preserve W362 boundaries; form rendering and floors remain Phase 6 work | Validated (Phase 2) |
| Label-mode defaults are a per-location floor with package → theme → project-setting precedence; explicit owner modes remain above it | Phase 06.6 D-15 adds register_label_mode_defaults without renaming existing owner APIs or merging their maps | Phase 1 contract extended by Phase 06.6 |
| Phase 3 (Bootstrap leak fixes) is the droppable one if 1.0.0 ships early | Additive DOM changes with a one-line migration note each | — Pending |
| Milestone limited to the five findings | Keep scope reviewable; other 1.0.0 items tracked separately | — Pending |
| Keep `cv_context_actions_label_mode` / `cv_context_action_label_mode` names; freeze as stable (LATER-02 → won't rename) | No renames before freeze; docs sharpen the distinction | Decided (Phase 1 discussion) |
| `CardAction.no_label` / `cv_no_label` removed before 1.0 (LATER-01), outside Phase 1; Phase 7 lists it as "deprecated, removed in 1.0.0", never stable | Superseded by `label_mode="icon"` | Decided (Phase 1 discussion) |
| E108 is an Error for unknown location keys and invalid modes; valid keys derive from `LOCATIONS` | Typos fail loudly; Phase 6's `"form"` extends it automatically | Decided (Phase 1 discussion) |

| Preserve the public classmethod resolver and honor own instance card modes in rendering | Retains subclass hooks and request-local overrides without shared class mutation | Validated (Phase 1 gap closure) |
| Resolve the filter's declared key once for the toolbar; keep list-row resolution independent | Label templates and toolbar leaves share the mode without overriding row maps | Validated (Phase 3 review fixes) |
| Validate resolved filter modes through the shared strict/log-and-floor policy | Runtime configuration errors retain diagnostics before custom label rendering | Validated (Phase 3 review fixes) |
| Release filter label-mode support as Fixed; document copied-template migration | Default bytes remain unchanged while configured context floors now apply | Validated (Phase 3) |
| Core performs no catch/log/fallback after a custom alert adapter fails; the `el.remove()` fallback lives only in the default adapter | Adapter owns its outcome and errors; core stays a thin delegated click listener | Validated (Phase 4) |
| Alert dismiss change released as Breaking with a copied-template migration; `data-bs-*` audit scoped to core templates | Only copied `alert.html` overrides need the one-attribute edit; object-detail layouts keep Bootstrap collapse/tab attributes | Validated (Phase 4) |
| One shared `pagination:hidden-label` class key for table and card pagination (not `table:hidden-label`) | One setting restyles both components; the default card bytes stay unchanged | Validated (Phase 5) |
| Form buttons resolve their mode from the owning view (render form `cv_view`, else helper, else page) and select that owner's whole form map | Formsets and nested forms follow their own view; maps never merge across owners | Validated (Phase 6) |
| Form values render as literal escaped text, never as Django templates | Removes crispy's template-injection path; the only visible change is `<input>` → `<button>` | Validated (Phase 6) |
| Filter helpers render a private deep-copied layout prepared in `get_attributes()` with a `get_form_actions()` hook | Field-only subclasses, `form=` and `add_input()` keep working without crispy template overrides | Validated (Phase 6) |
| Table `pagination.previous`/`pagination.next` blocks carry their own availability guards and run on disabled ends; released as Breaking with a tested override recipe | Theme overrides keep all django-tables2 block names; an unguarded copied override is the one thing that must change | Validated (Phase 5) |
| Cancel-link eligibility is semantic kind `cancel` + native type `button`, never name/URL/adapter class | `Button` subclasses stay eligible; submit/reset can never become links | Validated (Phase 6.1) |
| Button-only attribute filtering lives in the normalizer (`_anchor_attrs`), not the leaf; disabled or URL-less cancels fall back to `<button>` | One authoritative escaped `href`; custom leaves receive clean `cv_flat_attrs` | Validated (Phase 6.1) |
| A `tag` returned from `get_cancel_button_kwargs()` now raises — filed under the Form buttons Breaking entry with migration guidance | 0.30 rendered it as an attribute; the behavior change must be documented | Validated (Phase 6.1) |

| Complete the retained 6.2 scope while explicitly transferring deletion and residual Guardian review to 6.3 | Preserve measured fixes without claiming unresolved callbacks/converters/database guarantees | Decided; 6.3 remains open |
| Normalize nested-create rendered state against the target URL parent while preserving permission and label inputs | Controls agree with direct requests without broadening authority | Validated (WR-01, Phase 6.2) |

| Preserve source-bound companion evidence while excluding only Git-ignored, untracked IDE metadata | Exact source/index/settings checks remain strict; ordinary IDE use must not invalidate delivery | Validated (Phase 06.6) |
| Follow successful form POST redirects in fixture regression tests | Persistence alone did not reveal an unregistered detail link on the destination list | Validated (Phase 06.6 UAT repair) |

| Keep the workflow change default; document opt-in view access with explicit transition permissions | Existing page, action, choice and execution checks remain independent; optional hook denies direct requests as well as disabling controls | Validated (Phase 06.13) |
| Authorize nested requests through one shared ancestor engine; endpoint-local gates stay independent and never waive or are waived by ancestry | One traceable mechanism across plain/core/Guardian/manage/Resource compositions; denial stops deeper lookup, state and writes | Validated (Phase 06.18) |
| Fail closed with a named ImproperlyConfigured when a permission key has no vocabulary entry (core ancestry and Guardian local gates); render-time cv_has_access returns False | An unmigrated permission must never grant or crash with a raw TypeError | Validated (Phase 06.18 gap closure, plan 13) |
| Configure the list table's actions column through django-tables2 `Meta` (`sequence`, `exclude`), not crud_views convenience logic | One `Meta` line expresses what the reverted append/exclude-merge helpers did with hidden rules and edge cases (CLAUDE.md maintainability rule) | Validated (Phase 06.19 re-scope) |
| Expose `view` and a lazy `parent_object` through `cv_get_meta()` (page snippets), preserving label, button and column rendering paths | One code path, zero extra queries unless a template uses `parent_object`; no `request`/`user` key added | Validated (Phase 06.21) |

| Validate core permission declarations from concrete-model metadata after URL registration; keep database-row and Guardian checks at request time | Catches configuration errors before requests without database access or changing authorization | Validated (Phase 06.22) |

| Compact rendering is opt-in per formset node, with explicit columns and request-local heading metadata | Keeps classic paths and independent nested composition understandable; examples reuse existing models and permissions | Validated (Phase 06.24) |

| CompactWidgetCompatible is an empty inherited developer promise; shared schema checks and rendering remain unchanged | One explicit marker and guard allow application widgets without a registry, renderer abstraction or certification claim | Validated (Phase 06.25) |

| Legend styling reuses two empty class keys and existing template tags | Keeps themes independently overridable without changing runtime machinery | Validated (Phase 06.25.1) |

| Reuse one ValueToggle descriptor in server policy and layout; keep choice inference bounded and explicit overrides authoritative | Maintains one traceable condition with native Django validation and no second engine | Validated (Phase 06.27) |

| Numbered columns resolve complete registry classes on a shallow render copy; bridge only exact installed Bootstrap source | Preserves defaults, caller extras and custom-template ownership without a new grid or cache abstraction | Validated (Phase 06.29) |

| Resolve transition presentation on copied actions with eight workflow-owned variant keys and the existing icon helper | Keeps optional-app imports safe, preserves exact submit-label fallbacks and avoids a new rendering abstraction | Validated (Phase 06.32) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-13 after completing Phases 06.30, 06.31 and 06.32*
