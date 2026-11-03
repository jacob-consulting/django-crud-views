# Phase 03 — UI Review

**Audited:** 2026-10-26
**Phase:** Filter toggle label mode
**Baseline:** Abstract 6-pillar standards, anchored to the phase's locked decisions (03-CONTEXT.md D-01–D-11); no UI-SPEC.md exists in .planning.
**Scope:** 3a51f817530d90b29ac67c965a230a7d8c132f21..HEAD — `src/crud_views/templates/crud_views/tags/context_action_filter.html`, `src/crud_views/lib/view/buttons.py`, German PO/MO, tests, docs, CHANGELOG.
**Screenshots:** not captured (no dev server reached on localhost:3000, 5173 or 8080; all returned HTTP 000)
**Interaction captures:** off (workflow.ui_interaction_capture is false)
**Method:** Code-only audit plus direct `render_to_string` of the stock leaf in every mode (icon / both / label / absent / unknown, element and host icon placement, English and German) against the test project's settings. No dependencies installed, no implementation files modified. Interaction findings are code-derived from `list.filter.js` and the JS test fixtures, not observed in a browser.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | Single constant label `Filter`, translated at render time with a non-fuzzy German entry; icon mode keeps hidden text + `title`, visible modes drop the redundant tooltip. |
| 2. Visuals | 4/4 | `both` and `label` reuse the exact body grammar of `button/action.html`; icon mode is byte-identical to the pre-change baseline and the toolbar golden. |
| 3. Color | 4/4 | All classes come from the class table (`context:<variant>:<mode>`, presence-based fallback); zero hardcoded colors or Bootstrap literals added. |
| 4. Typography | 4/4 | No font-size/weight classes introduced; visible label inherits `btn btn-lg` like every sibling context button. |
| 5. Spacing | 4/4 | Icon-to-label separator is the same literal space as `action.html`; host placement keeps it; collapsed whitespace renders identically. One cosmetic 5-space indent in `both` source output (not visible). |
| 6. Experience Design | 3/4 | Disclosure contract intact (`aria-expanded`, `aria-controls`, collapse-first, no rollback). WARNING: in `label` mode the button carries no visual expanded/collapsed cue of its own; an unknown configured mode silently renders icon form. |

**Overall: 23/24**

---

## Top 3 Priority Fixes

1. **`label` mode has no on-button state cue (WARNING)** — A sighted user who collapses the panel sees a plain `Filter` button with no affordance that it is a disclosure or that it is currently closed; only the panel's presence communicates state. Icon mode conveys this through the funnel/funnel-x swap, `label` mode conveys it only via `aria-expanded`. — Concrete fix (theme-level, no icon-mode byte change): document in `docs/reference/context_buttons.md#the-filter-toggle` a recommended rule such as `#cv-filter-toggle[aria-expanded="true"] { … }` or a `context:secondary:label` class-table entry, and/or add `{% if cv_label_mode == "label" and cv_filter_expanded %} {% cv_button_class "context" "active" %}{% endif %}` to the class attribute inside the label branch only. Record as a Phase 7 (theme surface) candidate if not taken now.
2. **Unknown configured mode degrades silently to icon form (WARNING, documented A1 limitation)** — `context_action_filter.html:1-3,10-11` treat anything that is not `both`/`label` as `icon`, so a typo like `"text"` that escapes E210/E211/E106 (for example a value monkeypatched or computed at runtime) renders icon-only with no diagnostic in the page or log. — Concrete fix: none required for this phase (the system checks are the contract), but the docs sentence in `buttons.md` ("an unknown mode renders the icon form") should stay adjacent to the check IDs so an operator debugging a non-appearing label knows to run `manage.py check`.
3. **Cosmetic source-whitespace artifact in `both` output (minor)** — The `both` branch emits `\n     <span>Filter</span>` (5 spaces: 4 from the template indent plus the literal separator). It collapses to one rendered space, so nothing is visible, but view-source and byte-level diff tools show an odd indent. — Concrete fix: none advisable; moving the literal space would change the collapsed spacing in host placement (the A6 rationale). Leave as-is; noted so a later "clean up whitespace" PR does not remove the deliberate separator.

No BLOCKER findings. Recommendations 4–6 below are informational.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

- `src/crud_views/lib/view/buttons.py:330` seeds `cv_action_label = _("Filter")` via `django.utils.translation.gettext` at `get_context` time (render-time, so language switches per request). Previously the string was an untranslated literal.
- `src/crud_views/locale/de/LC_MESSAGES/django.po:46-48` adds `msgid "Filter"` / `msgstr "Filter"` with a source reference; non-fuzzy; MO recompiled. The German word is identical by coincidence, which is correct German, and the i18n tests prove catalog membership rather than relying on gettext's identical-string fallback (`tests/test1/test_i18n.py#test_filter_catalog_entry`).
- The label is constant across toggles (D-04). In `icon` mode it is the accessible name via `visually-hidden` plus `title`/`data-cv-tooltip`; in `both`/`label` it is visible and the tooltip is dropped, matching the `action.html` convention of no tooltip when a visible label exists (D-05). This avoids the "tooltip repeats the label" anti-pattern.
- Finding (no deduction): `Filter` is a bare noun; it names the panel rather than the action, and the sibling reset action already uses `Apply Filter` / `Filter anwenden`. The noun reads correctly as a disclosure label and is locked by D-04/D-09, so no change is proposed.
- Generic-label grep (`Submit|Click Here|OK`) over the phase diff: no hits in production templates.

### Pillar 2: Visuals (4/4)

Rendered output inspected directly (English, default icon/class tables):

- `icon` / absent / unknown mode: `<span data-cv-filter-icon="open">…</span><span data-cv-filter-icon="close" hidden>…</span><span class="visually-hidden">Filter</span>` — byte-identical to `RAW_DEFAULT_FILTER` and to `tests/test1/golden/action_menus/toolbar_publisher_list.html`. The `icon` mode contract of D-05 is met exactly; the icon-only button retains an accessible name and a tooltip.
- `both`: the same two icon spans followed by ` <span>Filter</span>`; `title`/`data-cv-tooltip` absent. Structure matches `button/action.html` line 9 (`{% cv_icon %} <span>{{ cv_label }}</span>`), so a toolbar mixing the filter toggle with other `both`-mode context buttons has uniform icon+label rhythm.
- `both` + host placement: `class="btn btn-outline-primary btn-lg icon-funnel"`, `data-cv-filter-icon-open="icon-funnel" data-cv-filter-icon-close="icon-x"`, body ` <span>Filter</span>` — host icon on the button, label separated by the literal space (D-03/A6).
- `label`: body is `<span>Filter</span>` only; no icon classes on the button, no spans, no `data-cv-filter-icon-*`. D-06 met.
- Hierarchy: the toggle keeps `btn-lg` within `btn-group-lg`, same weight as siblings; no competing focal point introduced.
- Cross-reference: the missing on-button state cue in `label` mode is scored under Pillar 6, not here, to avoid double-counting.
- Not visually confirmed (no screenshots): host-icon pseudo-element spacing against the visible label depends on the consumer's icon library CSS; the template provides the separator, which is the most it can do.

### Pillar 3: Color (4/4)

- Class attribute (`context_action_filter.html:3`): `both`/`label` call `{% cv_button_class "context" cv_variant|default:"secondary" cv_label_mode %}`; the fallback branch passes the literal `"icon"`. `get_button_class` (`src/crud_views/lib/button_classes.py:136-146`) prefers `context:<variant>:<mode>` when present and otherwise `context:<variant>`, so with the default table all three modes render `btn btn-outline-primary btn-lg` — no new accent usage, and themes can differentiate per mode without template edits.
- Hardcoded color grep (`#hex`, `rgb(`, `btn-primary`, `text-`) over the phase diff: 0 hits in templates or Python.
- Accent distribution unchanged: the filter toggle keeps the same outline-primary treatment as its siblings; no element gained emphasis.

### Pillar 4: Typography (4/4)

- No `fs-*`, `fw-*`, `small`, `lead` or heading classes added; the visible label `<span>` inherits the `btn`/`btn-lg` type scale exactly as `action.html` labels do.
- `visually-hidden` on the icon-mode label is unchanged (`context:hidden-label` → `visually-hidden`, `button_classes.py:84`).
- Finding (no deduction): the `label`-mode button is text-only at `btn-lg`, which is the same size as icon siblings — consistent, if visually heavier; a theme can tune it through `context:secondary:label`.

### Pillar 5: Spacing (4/4)

- Separator: `both` emits a literal space before the visible span (`context_action_filter.html:13`), the same separator `action.html:9` uses between icon and label. In element placement the preceding newline + indent collapses with it to a single rendered space (the `hidden` span between them generates no box, so the two whitespace runs are adjacent and collapse). In host placement the literal space is the only separator between the `::before` host icon and the text — this is why it must not be removed.
- `label`: body `\n    <span>Filter</span>\n` — leading/trailing whitespace inside an inline-block button is stripped at line boundaries; no visible padding change.
- Button padding, `btn-group` gaps and container layout untouched (`context:container*` keys unchanged).
- Arbitrary spacing values: none. Cosmetic: `both` source shows a 5-space indent before `<span>` (see Priority Fix 3); not rendered.

### Pillar 6: Experience Design (3/4)

State coverage (code-derived; `list.filter.js` unchanged in this range):

- **Disclosure state:** `aria-expanded` and `aria-controls="filter-collapse"` present in all three modes (`context_action_filter.html:5-6`); `id="cv-filter-toggle"` stable so the handler wires in every mode.
- **Collapse-first / failure semantics:** `list.filter.js:16-18` returns before any DOM change when the adapter returns false or throws; `:33-39` does not roll back on a rejected POST. JS fixtures cover label-only markup, both/element, both/host, mixed, out-of-order persistence (`tests/js/list.filter.test.js`). D-06 met.
- **Icon state:** host swap via `data-cv-filter-icon-open/close`, element swap via `[data-cv-filter-icon]` `hidden` toggling; label mode has neither and the `querySelectorAll` loop is a no-op.
- **Persistence:** POST `filter_expanded` boolean with CSRF header unchanged.
- **Visibility:** both early `cv_access=False` returns kept (`buttons.py:316-322`); no-filter and pinned pages render no toggle.
- **Translation:** gettext per render; German render verified.

Findings justifying 3 rather than 4:

- **WARNING — no on-button expanded cue in `label` mode.** With neither icon swap nor `active` class, the only state signal on the control is `aria-expanded`. Screen-reader users get it; sighted users must infer from the panel. The locked decision D-06 defines label mode as "visible text without icon spans" and does not require a cue, so this is a quality gap, not a contract breach. See Priority Fix 1.
- **WARNING — unknown configured mode renders icon form silently** (template fallback branch; A1 disposition recorded in 03-01-SUMMARY). Diagnostics live in system checks only. See Priority Fix 2.
- **Informational (4):** `both` and `label` modes drop `title`, so hover no longer shows a tooltip; intentional per D-05 and consistent with other context buttons.
- **Informational (5):** downstream themes that override `context_action_filter.html` keep icon-only output until they branch on `cv_label_mode`; documented in `docs/migrating-1.0.md` and CHANGELOG (#262). No in-repo action.
- **Informational (6):** a project whose `CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]` floor is already `both`/`label` will see the stock toggle change on upgrade; called out in the Fixed entry (CHANGELOG.md:156-162). Correctly classified as Fixed rather than Breaking since default output is unchanged.

---

## Verification and Limits

- Diff `3a51f81..HEAD` inspected for all production files: template (12 lines), `buttons.py` (6 lines), PO (4 lines), MO (binary). `list.filter.js` and `tests/test1/golden/` have no diff.
- Rendered the stock leaf with `render_to_string` under the test project's settings for: mode absent, `icon`, `both`, `label`, `weird`; expanded false/true; default element icons and `HOST_LIBRARY`/`HOST_ICONS` host placement; `en` and `de`. Output matched the claims in 03-01-SUMMARY and the docs table in `context_buttons.md:115-119`.
- Test counts (3457 Python passed, 149 JS passed) are attributed execution evidence from 03-02-SUMMARY; this audit did not rerun the suites.
- Screenshot ignore gate ran before server detection; `.planning/ui-reviews/.gitignore` covers image extensions and `interaction/`. No captures were generated.
- No `components.json`; the shadcn registry audit is inapplicable. No `.claude/skills` or `.agents/skills` directories exist.
- This review establishes Phase 03 contract compliance for the filter toggle; it is not a visual or accessibility certification of the whole toolbar.

## Files Audited

- .planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md
- .planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md, 03-01-SUMMARY.md
- .planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md, 03-02-SUMMARY.md
- .planning/phases/02-form-key-grammar/02-UI-REVIEW.md (format reference)
- src/crud_views/templates/crud_views/tags/context_action_filter.html (HEAD and diff)
- src/crud_views/templates/crud_views/tags/button/action.html (reference leaf)
- src/crud_views/lib/view/buttons.py (diff)
- src/crud_views/lib/button_classes.py (`DEFAULT_BUTTON_CLASSES`, `get_button_class`)
- src/crud_views/templatetags/crud_views.py (`cv_icon_class`, `cv_button_class`)
- src/crud_views/static/crud_views/js/list.filter.js (unchanged, behavior reference)
- src/crud_views/locale/de/LC_MESSAGES/django.po (diff)
- tests/test1/test_filter_toggle_label_mode.py (helpers and raw baseline)
- tests/test1/golden/action_menus/toolbar_publisher_list.html
- tests/lib/helper/icons.py
- docs/reference/context_buttons.md (filter section), CHANGELOG.md (Fixed entry)

## Recommendation Count

- Priority fixes: 2 WARNING (label-mode state cue; silent unknown-mode fallback), 1 minor (whitespace artifact)
- Minor recommendations: 3 informational
