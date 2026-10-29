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

### Active

- [ ] **4** Theme surface in `docs/development/stability.md` (icons, buttons, alerts, JS, theme hooks) + guard test
  `tests/test1/test_stability_doc.py`; closes the theme part of #89

### Out of Scope

- Removing `CardAction.no_label` / `cv_no_label` guard (#254 adjacent) — tracked for 1.0.0, not among the five findings
- Renaming the `cv_context_actions_label_mode` / `cv_context_action_label_mode` pair — rejected, not deferred: both names stay stable (Phase 1 decision, LATER-02 won't rename)
- E36x check for `container-tag` — tracked separately
- #259 host placement for headings, #211 stale-override detection — tracked separately
- Tabler theme changes in its own repository — each phase only writes the Tabler follow-up into its acceptance note
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
| Group findings into phases by dependency, not rank order or one change | Reviewable units; #257 depends on 1A+1C; stability policy must be last | — Pending |
| Option A: `form:<kind>:<mode>`; context/list/card retain variants | Independent finite vocabularies preserve W362 boundaries; form rendering and floors remain Phase 6 work | Validated (Phase 2) |
| Label-mode defaults are a project-wide floor, not per-ViewSet/view | Per-ViewSet/view knobs already exist | Validated (Phase 1) |
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
*Last updated: 2026-10-29 after Phase 6.1 completion*
