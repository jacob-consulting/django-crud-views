# Phase 06 — UI Review

**Audited:** 2026-10-28
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase); design contract = `06-SPEC.md` + `06-CONTEXT.md` D-01..D-18; measured browser evidence = `06-ACCEPTANCE.md` §9
**Screenshots:** captured (21/21) to `.planning/ui-reviews/06-20261028-092739/` — real example app (`examples/bootstrap5`), three scratch `runserver`s on 8871/8872/8873 with per-mode `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": label|both|icon}`, seeded scratch SQLite copies, logged in as `alice`; pages `/library/author/create/`, `/library/author/<pk>/delete/`, `/library/author/?first_name=a&sort=last_name&dir=desc` (filter panel expanded via the session POST) at 1440×900, 768×1024 and 375×812. Ports 3000/5173/8080/8000 were answered by unrelated projects (SvelteKit app, "Weaver"), not this repo. Playwright 1.64.1 was pointed at the installed Chromium 149 headless shell (build 1228 aliased as 1248 via `PLAYWRIGHT_BROWSERS_PATH`).
**Interaction captures:** off (workflow.ui_interaction_capture is false) — hover, focus and tooltip findings below are code-derived or cite `06-ACCEPTANCE.md` §9; the pointer-hover tooltip remains unobserved by any automated run.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | Every form control carries a specific, translated verb (`Save`, `Delete`, `Cancel`, `Apply Filter`, `Reset Filter`, `Process Workflow Step`); icon mode keeps the same text as hidden label + title; fallback log lines name the kind |
| 2. Visuals | 3/4 | Icon-mode Save and Delete are identical 40×38 blue squares differing only by glyph; icon/text gap in both mode is a literal space, not a spacing token |
| 3. Color | 3/4 | `form:delete` maps to `btn btn-primary` (button_classes.py:58) — the destructive submit wears the accent; no hard-coded colours in the leaf |
| 4. Typography | 4/4 | Leaf adds no size/weight classes; Bootstrap `.btn` typography only, identical in all three modes and at all breakpoints |
| 5. Spacing | 3/4 | crispy `FormActions` wrapper `mb-3` sits last inside `.card-body` → 32 px below the buttons vs 16 px at the sides, now on CRUD forms *and* the filter card |
| 6. Experience Design | 3/4 | Keyboard focus, cancel, reset, modal submitter and missing-icon fallback are proven; no busy/double-submit guard on `type=submit`; hover tooltip on icon-only buttons still unverified |

**Overall: 20/24**

---

## Top 3 Priority Fixes

1. **Destructive delete button uses the primary accent (`form:delete` → `btn btn-primary`)** — in `icon` mode the delete page shows two identical blue squares next to a grey one (`icon-delete-desktop.png`); the only difference between "save" and "destroy" is a 14 px glyph, and in `label`/`both` mode the delete form's primary CTA looks exactly like every create/update CTA. Pre-existing table value, but Phase 06 introduced the modes where it matters. — Change `src/crud_views/lib/button_classes.py:58` to `"form:delete": "btn btn-danger"`, regenerate `tests/test1/golden/form_buttons/delete.html` (class is the only diff), add a `### Breaking` note (class change) to CHANGELOG + `docs/migrating-1.0.md`; the `form:delete:<mode>` grammar already lets themes override per mode.
2. **Double bottom gap under every form-action row** — crispy-bootstrap5 `layout/formactions.html` wraps the group in `<div class="mb-3">`; inside `.card-body` (padding 1rem) that yields ~32 px below Save/Cancel but 16 px at the sides (`*-create-desktop.png`: buttons end y≈510, card ends y≈541; filter card `*-list-desktop.png`: 568 → 600). 06-05 moved Apply/Reset into the same wrapper, so the filter card inherited the gap too (the legacy `inputs.html` path had the same wrapper, but the phase now owns both groups). — Give both package groups a hook class: `FormActions(..., css_class="cv-form-actions")` in `CrispyFormMixin.get_form_actions` (`crispy/form.py:55`) and `ListViewFilterFormHelper.get_form_actions` (`views/list.py:130`), and add to the package CSS `.card-body > form .cv-form-actions:last-child, #filter-form .cv-form-actions:last-child { margin-bottom: 0; }`. Pin with a parsed-DOM test (class present), not a byte golden.
3. **Icon/text gap in `both` mode is a bare space character** — `form.html:1` renders `{% cv_icon cv_icon %} <span>` (same as `action.html`), so the gap is font-dependent inline whitespace rather than a token; at 1440 px it reads as ~5 px, tighter than the 8 px between the two buttons, and a theme with a condensed font or `white-space` tweaks loses it entirely. — Render the both body as `{% cv_icon cv_icon %}<span class="ms-1">{{ cv_label }}</span>` (or make `form:icon-host`'s sibling a `d-inline-flex align-items-center gap-1` button class) and apply the same to `action.html` so the two leaves stay parallel; update the three `both`-mode DOM assertions that currently compare `text_content()` of the span only (no byte golden covers `both`).

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

Verified strings (source → rendered → German):
- `crispy/form.py:35` `submit_label = _("Save")` → `<span>Save</span>` → `Speichern` (`locale/de … django.po:21`; `examples/bootstrap5/test_i18n.py` pins `value="Sichern"`? — no: the example pins its own `Sichern` for a per-form `submit_label`; the package default is `Speichern`).
- `crispy/form.py:128` `_("Delete")` → `Löschen`; cancel label comes from `cv_get_cancel_button_context` (`Cancel` → `Abbrechen`).
- `views/list.py:131-132` `_("Apply Filter")` / `_("Reset Filter")` → `Filter anwenden` / `Filter zurücksetzen`.
- `crud_views_workflow/lib/forms.py:20` `_("Process Workflow Step")` → `Workflow-Schritt verarbeiten`.
- Test-app golden pins `Create` because `tests/test1/app/forms.py` sets `AuthorForm.submit_label = "Create"` (06-01 SUMMARY) — the override path works.

Icon mode: the same literal is the hidden `<span class="visually-hidden">` text and the generated `title` (`form.html:1`), so the accessible name never diverges from the visible label of the other modes (AX names "Save"/"Delete"/"Cancel"/"Apply Filter"/"Reset Filter" measured in ACCEPTANCE §9).

Diagnostics copy (`button_data.py:146,148,257,261`): "`<kind>` has no icon; rendered with its label instead" / "has neither an available icon (%r) nor a label and renders empty" — names the kind and the icon value; actionable.

Findings:
- Minor — `Reset Filter` is a `type="reset"` button whose JS handler also *navigates* (keeps `sort/order/dir`, drops filters). The label is accurate for the user outcome; noted only because a theme that removes `list.filter.js` gets a plain field reset with no navigation and the label still reads the same. No change required.
- No generic labels (`Submit`, `OK`, `Click here`) in any form-button path: `grep -rn "Submit(\"submit\"" src` finds only the two package constructors above, both with explicit translated values.

### Pillar 2: Visuals (3/4)

Observed (desktop captures):
- `label`: `Save`/`Cancel`, `Delete`/`Cancel`, `Apply Filter`/`Reset Filter` as primary + secondary pairs; clear focal CTA on each form.
- `both`: floppy + "Save", trash + "Delete", xmark + "Cancel", funnel + "Apply Filter", rotate-left + "Reset Filter". Glyphs are semantically right and distinct from the header's context icons (list/eye/pencil/trash/gear), except trash, which is deliberately shared with the delete action.
- `icon`: 40×38 px squares (ACCEPTANCE §9). Icon-only buttons carry a hidden label, `title` and `data-cv-tooltip="form"` (`form.html:1`); `font_renderer` emits `<i class="…" aria-hidden="true">` (`icons.py:228`), so the glyph is not double-announced.
- Mobile 375 px (`icon-create-mobile.png`, `icon-list-mobile.png`): buttons keep their size, no wrap, no clipping of the hidden label (`visually-hidden` is absolutely positioned).

Findings:
- WARNING — In `icon` mode Save and Delete are visually interchangeable (same size, same `btn-primary`, glyph the only cue). See Fix 1.
- WARNING — Both-mode icon/text separation is a literal space in the template (Fix 3). Visible but token-less.
- Minor — The host-icon path (`form:icon-host` = `{name_class}`) puts the icon class on the `<button>` itself; in `both` mode that leaves no inline element and relies on the theme's `::before`. Covered by `test_form_host_icon_goes_on_the_button`; not screenshot-verified here (the example uses the inline Font Awesome path).
- Pass — Visual hierarchy between the form's CTA row and the header context toolbar holds in all three modes: the toolbar is `btn-outline-primary` with one active fill, the form row is one filled primary + one filled secondary.

### Pillar 3: Color (3/4)

Class table (`button_classes.py:56-60,88,97`): `form:submit` / `form:delete` / `form:filter-submit` = `btn btn-primary`; `form:cancel` / `form:filter-reset` = `btn btn-secondary`; `form:hidden-label` = `visually-hidden`; `form:icon-host` = `{name_class}`. The leaf itself contains no colour literals (`grep '#[0-9a-f]\|rgb(' tags/button/form.html` → 0). The ten hex values found under `static/crud_views/css/` are in `formset.css` / `property.css`, untouched by this phase.

Accent distribution on a create page: one filled primary (Save) + one active toolbar button; on a delete page the same, plus the delete context button is active-filled in the toolbar, so the page shows *two* filled blue "delete" affordances and zero red ones.

Findings:
- WARNING — `form:delete` wears the accent (Fix 1). Bootstrap's own convention and the package's `formset:control-danger` = `btn btn-danger` (line 63) show the table already has a danger vocabulary; the delete submit is the one destructive form control that does not use it.
- Pass — Filter Apply/Reset reuse primary/secondary consistently with Save/Cancel; the expanded-filter toggle switches to the `filter-close` glyph (distinct from `filter-reset`'s rotate-left, as 06-04 required).
- Pass — Missing-icon fallback drops to label classes (`form:<kind>:label` lookups) rather than leaving a bare primary square (`test_non_strict_missing_icon_logs_and_uses_the_label`).

### Pillar 4: Typography (4/4)

`form.html` and `action.html` introduce no `fs-*`, `fw-*`, `small`, `lead` or heading classes; `grep -ohE 'text-(xs|sm|lg|xl)|fw-|fs-' tags/button/*.html` → 0. All glyph sizing comes from `.btn` line-height; captured label/both buttons are 38 px tall in every mode and viewport, identical to the pre-phase `<input>` goldens. The `visually-hidden` span adds no layout. No findings.

### Pillar 5: Spacing (3/4)

- Between buttons: inline whitespace between two `inline-block` `.btn`s (≈8 px at this font). Same mechanism as before the phase (goldens show a newline between controls). Acceptable, consistent with the action toolbar.
- Row to fields: `FormActions` follows the last `div.mb-3` field row → 16 px. Correct.
- Row to card edge: pack wrapper `mb-3` + `.card-body` padding → ~32 px bottom vs 16 px left (measured in `label-create-desktop.png`, `both-delete-desktop.png`, `*-list-desktop.png`). See Fix 2.
- Icon-mode button: 40×38 px with Bootstrap `.btn` padding; the `<i>` sits centred (no `me-*` since there is no visible text). Good.
- Filter card: fields → actions → hidden-input wrapper order confirmed (`filter.html` golden; `test_filter_endpoint_fields_then_actions_then_hidden_wrapper`). The hidden-input wrapper is another `div.mb-3 > div` that is *visually empty* — it contributes 16 px of dead space under the actions inside `#filter-form` in addition to the FormActions `mb-3` (two empty-looking margins stacked). Pre-existing pack behaviour (L-HIDDEN-WRAPPER), but it is why the filter card bottom gap reads larger than the CRUD card's.
- No arbitrary values introduced (`grep -rn '\[.*px\]' src/crud_views/templates` → 0).

Findings:
- WARNING — Stacked bottom margins (Fix 2).
- Minor — Both-mode icon gap is whitespace (Fix 3).

### Pillar 6: Experience Design (3/4)

State coverage (code + ACCEPTANCE §9):
- Keyboard: real `<button>`s, `:focus-visible` ring observed on Save/Cancel/Apply/Reset in all modes; Enter on Cancel navigates (ACCEPTANCE §9).
- Cancel: `type="button"` + `data-cv-cancel-url` (`form.html:1`, `viewset.js:40-43` via `closest()`), so clicks on the `<i>`/`<span>` children work (JS suite + §9).
- Filter reset: `type="reset"` + navigation preserving `sort/order/dir` (`list.filter.js:42-`; §9 measured `?sort=last_name&dir=desc`).
- Submitter payload: native `SubmitEvent.submitter` → only the clicked button's name/value posted, CSRF + `confirm` retained (`modal.test.js`; §4 payload evidence).
- Destructive confirmation: delete form keeps the required `Confirm deletion` checkbox (`label-delete-desktop.png`); the submit is not gated client-side on the checkbox (server validation only) — unchanged from before.
- Missing icon: strict `ValueError` naming the kind / non-strict log + label fallback with no orphan `title`/tooltip (`button_data.py:146-148, 257-261`; `test_form_button_checks.py`). Static W292 pre-warns for package forms.
- Tooltip plumbing: `tooltip.js:28` passes `{location: "form"}`; the Bootstrap adapter (`adapters.js:25`) ignores `location` and just calls `getOrCreateInstance`, so the new location value cannot break initialisation. Focus-triggered tooltips were observed in §9; **pointer-hover tooltips were not** (headless harness limitation, WINDOWS #9) and this audit's static captures cannot show them either.
- Disabled: no `cv_disabled` key by design (SPEC); a caller `disabled=True` kwarg becomes a bare attribute through `cv_flat_attrs` (flatatt boolean rule) — works, untested visually.

Findings:
- WARNING — No busy state: nothing disables the submit button or shows progress after click (`grep -i 'disabled\|submitting' modal.js viewset.js` → 0). The phase made the buttons real `<button>`s, which is the precondition for a one-line `form.addEventListener("submit", …)` guard; it was not added. Double-click on Delete posts twice (second one 404s harmlessly, but a create form can duplicate). Recommend a `data-cv-submitting` guard in `viewset.js` that sets `disabled` after the first `submit` event (keep `FormData(form, submitter)` semantics by disabling *after* the event, not in it).
- WARNING — Hover discoverability of icon-only buttons is unverified by any automated evidence; with `interaction_capture` off this audit could not add it. Icon mode ships as opt-in (floor `label`, example `both`), which limits exposure.
- Minor — In icon mode the delete page's header toolbar already shows a filled trash button (active context action) directly above a second filled trash button (the submit). Two identical affordances with different consequences on one screen; Fix 1 resolves it.
- Pass — Legacy `add_input()` controls keep rendering (D-01) and the `helper.inputs = []` behaviour change is documented with an executable migration (`test_form_button_docs.py`).

Registry audit: skipped (no `components.json`; Django/Bootstrap project, not shadcn).

---

## Files Audited

Source:
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/tags/button/form.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/tags/button/action.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/tags/list_filter.html`, `context_action_filter.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/crispy/buttons.py`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/crispy/form.py`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/views/list.py` (filter helper, lines 120-140)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/views/mixins.py` (filter persistence, lines 320-360)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/button_classes.py` (form keys 56-63, 88, 97)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/icons.py` (form icon names, `font_renderer`)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/view/button_data.py` (missing-icon policy)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/tooltip.js`, `adapters.js`, `viewset.js`, `list.filter.js`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/locale/de/LC_MESSAGES/django.po`, `src/crud_views_workflow/locale/de/LC_MESSAGES/django.po`
- `/home/alex/projects/alex/django-crud-views/.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/formactions.html`
- `/home/alex/projects/alex/django-crud-views/tests/test1/golden/form_buttons/{create,update,delete,workflow,filter}.html`
- `/home/alex/projects/alex/django-crud-views/examples/bootstrap5/project/settings.py`, `project/urls.py`, `library/views.py`

Captures (`.planning/ui-reviews/06-20261028-092739/`, gitignored): `{label,both,icon}-{create,delete,list}-{desktop,mobile}.png`, `{label,both,icon}-create-tablet.png`.

Phase artefacts: `06-CONTEXT.md`, `06-SPEC.md`, `06-ACCEPTANCE.md`, `06-01..09-PLAN.md`, `06-01..09-SUMMARY.md`, `deferred-items.md`, `.planning/WINDOWS.md` (entries 6, 9).
