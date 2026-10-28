# Requirements: django-crud-views — Concept Review Follow-ups

**Defined:** 2026-10-25
**Core Value:** Every public theme name (label-mode defaults, class-table keys, icon names, leaf templates, JS adapters)
settles once, consistently, before 1.0.0 freezes it — no public name changes twice.

Sources: `superpowers/plans/2026-10-24-concept-review-followups.md`, `.planning/research/SUMMARY.md`.
Global rule for every requirement: without new configuration, goldens under `tests/test1/golden/` stay byte-identical
except where a requirement says the markup changes.

## v1 Requirements

### Label-mode defaults (plan 1A)

- [x] **LMOD-01**: Project can set `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, merged per key over `{"context": "icon", "list": "icon", "card": "both"}`; docs state per-key merge vs whole-dict replacement of the per-button maps
- [x] **LMOD-02**: `default_label_mode(location)` in `crud_views.lib.view.label_mode` is the single source of the floor default, used by `cv_button_data()`, `cv_get_action_label_mode()` and `CardListView` (no `"both" if card` / `or "icon"` / `get(key, "icon")` literals remain)
- [x] **LMOD-03**: `CardListView.cv_card_actions_label_mode` defaults to `None` (= the map); an explicit `"both"` still wins; `{"card": "label"}` restores the 0.29 card look without touching a view
- [x] **LMOD-04**: The setting is read at call time, so `override_settings` changes it in tests
- [x] **LMOD-05**: An invalid label mode outside strict mode logs and falls back instead of raising
- [x] **LMOD-06**: Check `crud_views.E108` reports an unknown location key or invalid mode; valid keys derive from `LOCATIONS`, not a literal list

### Class-key grammar (plan 1C)

- [x] **KEYS-01**: Maintainer decides the `form:*` second-segment grammar (A: `form:<kind>:<mode>`, B: variants everywhere) during phase discussion; the rule is written in `docs/reference/buttons.md#the-class-table`
- [x] **KEYS-02**: W362 accepts mode keys for form buttons per the chosen grammar and rejects malformed ones (e.g. `form:submitt:icon`, `form:container:icon`)
- [x] **KEYS-03**: `LOCATIONS` is split into explicit sets (e.g. `VARIANT_LOCATIONS`, `FORM_KINDS`) so adding `"form"` to the button-data locations cannot loosen W362
- [x] **KEYS-04**: A test parses the key count quoted in `buttons.md` and asserts it equals the size of `DEFAULT_BUTTON_CLASSES`

### Filter toggle (plan 1B, #262)

- [x] **FILT-01**: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` renders icon + "Filter" (no `title`); `"label"` renders text only; default `icon` output byte-identical (`toolbar_publisher_list.html` golden)
- [x] **FILT-02**: `list.filter.js` toggles `aria-expanded` and persists state for a toggle without icon spans (vitest label-only case)
- [x] **FILT-03**: The toggle's text stays constant; only `aria-expanded` and the icon change (WAI-ARIA toggle-button rule)
- [x] **FILT-04**: The "Filter" label is a translated msgid (German catalog updated)

### Form-button leaf (plan 2, #257)

- [ ] **FORM-01**: Golden of today's form-button markup is committed before any change, so the PR shows the diff
- [x] **FORM-02**: `"form"` is a button-data location; `cv_button_data(ctx, "form")` provides `cv_type`, `cv_name`, `cv_value`, `cv_id`, `cv_cancel_url` (cancel only); `cv_key` is the kind
- [x] **FORM-03**: New leaf `crud_views/tags/button/form.html` renders the three label-mode bodies with classes from `{% cv_button_class "form" cv_key cv_label_mode %}`
- [x] **FORM-04**: Class keys `form:hidden-label` (default `visually-hidden`) and `form:icon-host` exist, so icon-only form buttons keep an accessible hidden label and host-placed icon libraries render
- [x] **FORM-05**: crispy `Submit` / `Button` / `Reset` keep their constructor signature and render through the leaf; `css_class` is still appended; extra kwargs render as attributes
- [x] **FORM-06**: With nothing configured, form buttons render as `<button type="…">` with the same text, classes, `name`, `value`, `id`; POST data unchanged
- [x] **FORM-07**: Button values/labels are rendered as autoescaped plain text, never evaluated as a Django template; a label containing `<b>` renders escaped (button text and `value` attribute tested)
- [x] **FORM-08**: List filter Apply/Reset move from `helper.add_input()` into a layout `FormActions`, so they render through the leaf; `#filter-button-reset` id preserved; hidden sort/order inputs unchanged
- [ ] **FORM-09**: Icons `save`, `cancel`, `filter-reset` exist in `DEFAULT_ICONS` and `BOOTSTRAP_ICONS`; submit→`save`, delete→`delete`, cancel→`cancel`, filter-submit→`filter`, filter-reset→`filter-reset`; workflow submit uses `workflow`; per-form `submit_icon` wins
- [ ] **FORM-10**: `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` shows icon + text on save, delete, cancel and both filter buttons; `{"form": "icon"}` uses the hidden label with `title` and `data-cv-tooltip="form"`
- [ ] **FORM-11**: Setting → ViewSet `form_actions_label_mode` → view `cv_form_actions_label_mode` per-key maps resolve like the context/list maps
- [ ] **FORM-12**: Checks E210/E211/W291 cover form label-mode maps; W292 reports icon-only form buttons without an icon; strict mode raises at render, otherwise logs and renders the label
- [ ] **FORM-13**: CHANGELOG `### Breaking` (`<input>` → `<button>`, no template evaluation of values) and `docs/migrating-1.0.md` "Form buttons" section; example project enables `both` for submit, delete, cancel; Tabler follow-up written into the acceptance note

### Alert dismiss (plan 3A)

- [x] **ALRT-01**: Golden of today's dismissible alert is committed before the change
- [x] **ALRT-02**: `tags/alert.html` renders `data-cv-alert-dismiss` instead of `data-bs-dismiss="alert"`; one delegated click handler calls `cv.adapters.alert.close(el)`
- [x] **ALRT-03**: `cv.adapters.alert.close` uses Bootstrap's `Alert` when present and falls back to `el.remove()` inside the adapter; vitest covers both
- [x] **ALRT-04**: `grep -rn 'data-bs-' src/crud_views/templates` lists only the dropdown templates named in `theme.md`; docs (`javascript.md`, `messages.md`, `theme.md`), CHANGELOG Breaking and migration bullet updated

### Table pagination (plan 3B)

- [x] **PAGE-01**: Golden of today's paginated table is committed before the change
- [x] **PAGE-02**: `table/bootstrap5.html` renders `page-previous` / `page-next` registry icons with translated hidden labels, `aria-current="page"`, disabled ends as `<a class="page-link" aria-disabled="true">`, translated `<nav>` label; existing tables2 block names kept
- [x] **PAGE-03**: One shared `pagination:hidden-label` class key (default `visually-hidden`) is read by both table and card pagination
- [x] **PAGE-04**: Both paginations produce the same accessible structure; CHANGELOG Breaking (DOM), migration bullet, `.po` files updated

### Stability policy (plan 4)

- [ ] **STAB-01**: `docs/development/stability.md` lists the theme surface (icons, buttons, alerts, JavaScript adapters/events/DOM contract, theme hooks, leaf templates) with explicit names, no wildcards
- [ ] **STAB-02**: Names are classified into stable / provisional / internal tiers
- [ ] **STAB-03**: `tests/test1/test_stability_doc.py` checks both directions: every documented name exists, and every public theme name is documented
- [ ] **STAB-04**: A public `is_library_renderer(prefix, callable)` (or equivalent) helper replaces the theme's need for `_get_renderers` / `_icon_str`
- [ ] **STAB-05**: The stability doc lists dependency floors (crispy-forms, crispy-bootstrap5, django-tables2, Bootstrap)
- [ ] **STAB-06**: `theme.md` cross-references "what a theme may rely on"; theme part of #89 closed

## v2 Requirements

Deferred; tracked for 1.0.0 outside this milestone.

- **LATER-01**: Remove `CardAction.no_label` and the `cv_no_label` guard (#254 adjacent)
- **LATER-02**: Decide rename of `cv_context_actions_label_mode` / `cv_context_action_label_mode`
- **LATER-03**: E36x check for `container-tag`
- **LATER-04**: #259 host placement for headings
- **LATER-05**: #211 stale-override detection
- **LATER-06**: Class keys for alert frame classes (`btn-close`, `alert-dismissible fade show`)
- **LATER-07**: Lowest-version crispy test session / Django 4.2 support decision for 1.0.0

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-view / per-variant entries in the defaults map | Per-ViewSet/view knobs already exist; the map is the project-wide floor |
| Themes setting label modes | Label mode is project/view configuration, not theme |
| Using crispy `StrictButton` / `HTML()` for buttons | Unescaped content |
| Overriding crispy-bootstrap5 templates globally | Breaks other template packs (crispy-tabler) |
| Alert focus management / auto-dismiss | Beyond the leak fix |
| Pagination extras beyond matching card pagination | Scope is consistency only |
| Bootstrap 6 support | Alpha; adapters fallback covers absence of global `bootstrap` |
| Tabler theme changes in its own repo | Each phase writes the Tabler follow-up into its acceptance note |
| The 1.0.0 version bump | Follows after the stability phase |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LMOD-01 | Phase 1 (plan 1A) | Complete |
| LMOD-02 | Phase 1 (plan 1A) | Complete |
| LMOD-03 | Phase 1 (plan 1A) | Complete |
| LMOD-04 | Phase 1 (plan 1A) | Complete |
| LMOD-05 | Phase 1 (plan 1A) | Complete |
| LMOD-06 | Phase 1 (plan 1A) | Complete |
| KEYS-01 | Phase 2 (plan 1C) | Complete |
| KEYS-02 | Phase 2 (plan 1C) | Complete |
| KEYS-03 | Phase 2 (plan 1C) | Complete |
| KEYS-04 | Phase 2 (plan 1C) | Complete |
| FILT-01 | Phase 3 (plan 1B) | Complete |
| FILT-02 | Phase 3 (plan 1B) | Complete |
| FILT-03 | Phase 3 (plan 1B) | Complete |
| FILT-04 | Phase 3 (plan 1B) | Complete |
| ALRT-01 | Phase 4 (plan 3A) | Complete |
| ALRT-02 | Phase 4 (plan 3A) | Complete |
| ALRT-03 | Phase 4 (plan 3A) | Complete |
| ALRT-04 | Phase 4 (plan 3A) | Complete |
| PAGE-01 | Phase 5 (plan 3B) | Complete |
| PAGE-02 | Phase 5 (plan 3B) | Complete |
| PAGE-03 | Phase 5 (plan 3B) | Complete |
| PAGE-04 | Phase 5 (plan 3B) | Complete |
| FORM-01 | Phase 6 (plan 2) | Pending |
| FORM-02 | Phase 6 (plan 2) | Complete |
| FORM-03 | Phase 6 (plan 2) | Complete |
| FORM-04 | Phase 6 (plan 2) | Complete |
| FORM-05 | Phase 6 (plan 2) | Complete |
| FORM-06 | Phase 6 (plan 2) | Complete |
| FORM-07 | Phase 6 (plan 2) | Complete |
| FORM-08 | Phase 6 (plan 2) | Complete |
| FORM-09 | Phase 6 (plan 2) | Pending |
| FORM-10 | Phase 6 (plan 2) | Pending |
| FORM-11 | Phase 6 (plan 2) | Pending |
| FORM-12 | Phase 6 (plan 2) | Pending |
| FORM-13 | Phase 6 (plan 2) | Pending |
| STAB-01 | Phase 7 (plan 4) | Pending |
| STAB-02 | Phase 7 (plan 4) | Pending |
| STAB-03 | Phase 7 (plan 4) | Pending |
| STAB-04 | Phase 7 (plan 4) | Pending |
| STAB-05 | Phase 7 (plan 4) | Pending |
| STAB-06 | Phase 7 (plan 4) | Pending |

**Coverage:**
- v1 requirements: 41 total
- Mapped to phases: 41
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-25*
*Last updated: 2026-10-25 after roadmap creation*
