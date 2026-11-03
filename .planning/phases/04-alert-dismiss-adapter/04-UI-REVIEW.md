# Phase 04 — UI Review

**Audited:** 2026-10-26
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase); scope confined to the dismissible alert component and the documented custom frame recipe
**Screenshots:** not captured (no dev server on localhost:3000, 5173, 8080 or 8000 — code-only audit). Browser behaviour is taken from the headless-Chrome evidence already recorded in `04-ACCEPTANCE.md` §6, not from captures made by this audit.
**Interaction captures:** off (workflow.ui_interaction_capture is false) — interaction findings below are code-derived

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | Only user-facing string is the translated `aria-label="Close"`; docs copy matches the shipped markup byte-for-byte |
| 2. Visuals | 3/4 | Stock frame unchanged; recipe swaps the icon's `me-2` for `notice-icon` without saying the gap must come from theme CSS |
| 3. Color | 4/4 | Level colour still resolves through `alert:*` class-table keys; no hardcoded colour in any phase product file |
| 4. Typography | 4/4 | Phase diff adds no type class; `<strong>` heading + body text hierarchy unchanged |
| 5. Spacing | 4/4 | `me-2` / `mt-2` / `mb-0` only, all Bootstrap scale; no arbitrary values introduced |
| 6. Experience Design | 3/4 | Fallback `el.remove()` closes with no transition and the control gives no feedback when the adapter is missing or throws |

**Overall: 22/24**

---

## Top 3 Priority Fixes

1. **Fallback close is abrupt while the frame still carries `fade show`** (WARNING) — Without Bootstrap's `Alert` the alert vanishes in one frame, while the same markup fades over ~180 ms when Bootstrap is loaded; users on a Bootstrap-CSS-only page get an inconsistent close. — D-04 pins the fallback to plain `el.remove()`, so this is a follow-up, not a Phase 4 defect: in `adapters.js:44-48` the fallback could remove `show` first and remove the node on `transitionend` (with a short timeout guard) when `el.classList.contains("fade")`; otherwise document in `messages.md:44-46` that the fallback is instantaneous.
2. **Silent failure when `cv.adapters.alert` is missing or the adapter throws** (WARNING) — A theme that replaced the whole `cv.adapters` map after load leaves the X doing nothing visible; the `TypeError` only reaches the console. — Behaviour is intentional (D-03/D-04) and documented in `javascript.md` "Dismissible alerts" and `migrating-1.0.md:364-385`. Keep as-is, but the Phase 7 surface assessment should decide whether a `crud_views` system check or a dev-mode `console.warn` on first click is worth adding.
3. **Recipe drops the icon's horizontal gap without saying so** (WARNING) — `docs/reference/theme.md` "### Custom alert frame" passes `"notice-icon"` to `cv_icon` where the stock frame passes `"me-2"`; a reader who copies the recipe and does not write `.notice-icon` CSS gets the icon flush against the heading. — Add one bullet under "What closing and accessibility rely on stays": "`notice-icon` replaces the stock `me-2`; give it a right margin in your CSS or keep `me-2`."

Other findings (not top 3): see Pillar 6 for focus placement after removal (explicitly deferred by 04-CONTEXT.md) and Pillar 2 for the `&times;` glyph.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

Audited strings: the alert frame, both body snippets, the documented recipe, the messages.md example, the CHANGELOG Breaking entry and the migration before/after.

- `src/crud_views/templates/crud_views/tags/alert.html:5` — the only string in the component is `aria-label="{% translate 'Close' %}"`. "Close" is the correct accessible name for an icon-only dismiss control (not "OK", "X" or "Dismiss alert"); it is wrapped in `{% translate %}` and `test_dismissible_alert_close_label_is_translated` pins the translation seam.
- `docs/reference/messages.md:30-33` — the documented rendered markup matches the shipped frame and the committed golden `tests/test1/golden/alerts/dismissible.html` attribute-for-attribute (`btn-close`, `data-cv-alert-dismiss`, `aria-label="Close"`).
- `docs/reference/theme.md` "### Custom alert frame" — the recipe keeps `{% translate 'Close' %}`; `test_documented_alert_frame_override` fails on a literal label (04-ACCEPTANCE.md §5 mutant 2).
- `docs/migrating-1.0.md:368-373` — before/after shows exactly one attribute change; no stale `data-bs-dismiss` wording survives except where it is deliberately described as the legacy path.
- No generic "Submit/Click Here/Something went wrong" strings were added; the phase adds no empty or error copy because the component has no such states.

No finding justifies deducting a point. The adversarial check that applies (translated accessible name, docs/markup agreement) passed with test evidence.

### Pillar 2: Visuals (3/4)

- **Focal point and hierarchy unchanged.** `alert.html:4` renders `icon → <strong>heading</strong> → body`, the icon from the registry (`icons.py:44-48`, e.g. `fas:circle-check` for success) with `me-2`. The phase diff (`git diff --stat 1b77934 HEAD -- src/`) touches only line 5's attribute; the golden diff is that one attribute. Visual output is otherwise byte-identical, as the objective requires.
- **Icon-only control is labelled.** `btn-close` is Bootstrap's background-image X with no text; `aria-label` supplies the name. Pass.
- **WARNING — recipe icon spacing.** `theme.md` recipe line 3 calls `{% cv_icon alert.icon_name "notice-icon" %}` where the stock frame uses `"me-2"`. The recipe text says "the class names are yours" but never says the gap is gone. A verbatim copy with no `.notice-icon` rule renders the icon touching the `<strong>` heading. Fix listed as priority 3.
- **Minor — recipe close glyph.** The recipe's control is `<button … aria-label="…"><span aria-hidden="true">&times;</span></button>`. `aria-hidden` on the glyph is correct, but `&times;` inherits the frame's font size with no `line-height`/`padding` guidance, so the hit target is smaller than Bootstrap's 1em×1em padded `btn-close` unless the theme styles `.notice-close`. Informational; the recipe is explicitly a starting point.
- **Fallback path visual.** Covered under Experience Design (priority 1): the frame keeps `fade show` but is removed with no transition when `Alert` is absent.

Score 3: the shipped component is visually unchanged (verified by golden), but the documented recipe — which this audit was asked to cover — leaves two visual gaps unstated.

### Pillar 3: Color (4/4)

- `alert.html:2` — frame colour is `{% cv_button_class "alert" alert.level %}`; defaults in `src/crud_views/lib/button_classes.py:79-80ff` (`alert alert-danger`, `alert alert-warning`, …). The recipe keeps this call (`theme.md` recipe line 2) and `test_documented_alert_frame_override` fails when it is replaced by a hard-coded colour (04-ACCEPTANCE.md §5 mutant 3).
- Hardcoded colours in phase product files: `grep -nE '#[0-9a-fA-F]{3,8}|rgb\(' alert.html adapters.js viewset.js` → none.
- Accent usage: the alert is a semantic-colour component (success/warning/danger/info/secondary), not a primary-accent element; no `btn-primary`/`text-primary` added. Level-to-colour mapping is one key per level, no overuse.
- Icon colour inherits the frame text colour (no explicit `text-*` class), which keeps the 60/30/10 balance of the host page untouched.

No deduction.

### Pillar 4: Typography (4/4)

- Distinct type classes in the frame and both bodies: none (`grep -ohE 'text-(xs|sm|…)|font-|fw-|fs-'` → 0 hits). Hierarchy is a single `<strong>` for the heading (`alert.html:4`) followed by inline body text or a `<ul>` (`snippets/alert/list.html`).
- The phase adds no type class to the template or the recipe; the recipe reuses `<strong>`.
- `aria-label` text is not rendered, so no visible size/weight change.

No deduction; nothing in scope to flag.

### Pillar 5: Spacing (4/4)

- Spacing utilities in the frame and bodies: `me-2` (icon gap, `alert.html:4`), `mt-2` + `mb-0` (`snippets/alert/list.html:1`). All on Bootstrap's 0.25rem scale; no arbitrary `[…px]` values and no inline `style`.
- Phase diff adds no spacing class. The close button's placement comes from Bootstrap's `.alert-dismissible` padding-right and `.btn-close` absolute positioning — unchanged CSS, as `messages.md:44-46` states.
- The recipe's dropped `me-2` is scored under Visuals (priority 3), not double-counted here.

No deduction.

### Pillar 6: Experience Design (3/4)

State coverage of the dismiss interaction, from `viewset.js:46-55` and `adapters.js:41-49`:

| State | Handling | Evidence |
|-------|----------|----------|
| Click on control / descendant | nearest `[role="alert"]` → `cv.adapters.alert.close(frame)`, `preventDefault` | `viewset.js:49-54`; jsdom tracer + 04-ACCEPTANCE §6 case A (183 ms Bootstrap fade, `closed.bs.alert`) |
| Keyboard | control is `<button type="button">`, so Enter/Space fire `click`; no custom key handling needed | `alert.html:5` |
| Alert inserted after load | delegated listener, no init | 04-ACCEPTANCE §6 case C (clone in modal-like host, 164 ms) |
| Bootstrap `Alert` absent | `el.remove()` synchronously | `adapters.js:47`; §6 case B |
| Adapter throws / missing key | error surfaces, frame stays, no log | `javascript.md` "Dismissible alerts"; 04-02 matrix |
| Non-dismissible | no control rendered | `alert.html:5` `{% if alert.dismissible %}` |
| Loading / empty | n/a for this component | — |
| Destructive confirmation | n/a (dismissal is non-destructive) | — |

Findings:

- **WARNING — inconsistent close motion (priority 1).** The frame always carries `alert-dismissible fade show` (`alert.html:2`) but the fallback removes the node without touching `show`, so the same markup animates on one page and snaps on another. 04-ACCEPTANCE §6 B records "removed synchronously". Documented as intentional (D-04) but it is a visible behavioural fork for the user, so it is scored.
- **WARNING — no user-visible feedback on adapter failure (priority 2).** A whole-map replacement without `alert` leaves the X inert; the `TypeError` is console-only. Documented (`migrating-1.0.md:364-385`, `javascript.md` "Dismissible alerts" bullet 3) and pinned by tests, so it is a deliberate contract rather than a defect, but from the user's seat an unresponsive control with no message is a degraded state.
- **Follow-up, not scored — focus after removal.** When the focused `btn-close` is removed (either path), focus drops to `<body>`; a keyboard user loses their place. `04-CONTEXT.md` deferred focus management out of Phase 4 and Bootstrap's own `Alert.close()` has the same behaviour, so this is not a regression. Record for LATER alongside LATER-06.
- **Pass — no-JS degradation.** Without the core scripts the alert renders and reads correctly; only the X is inert (`messages.md:41-42`). Without Bootstrap JS but with core scripts the X still works (case B). This is an improvement over the pre-phase state, where the X depended on Bootstrap's bundle.
- **Pass — repeated / rapid clicks.** 04-02 pins once-per-click dispatch and harmless repeated fallback removal.

Score 3: the interaction is robust and better than before, but the two documented-by-design states (abrupt fallback, silent failure) are real UX seams rather than polish items.

---

## Registry Safety

Not applicable: `components.json` absent (`NO_SHADCN`), and no UI-SPEC.md lists third-party registries. Section skipped per the audit procedure.

---

## Files Audited

Product (phase diff, `git diff --stat 1b77934 HEAD -- src/`):
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/tags/alert.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/adapters.js`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/viewset.js`

Unchanged dependencies read for context:
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/tags/messages.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/snippets/alert/text.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/snippets/alert/list.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/messages.py` (`alert_data`)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/button_classes.py` (`alert:*` keys)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/icons.py` (`message-*` icons)

Golden and docs:
- `/home/alex/projects/alex/django-crud-views/tests/test1/golden/alerts/dismissible.html`
- `/home/alex/projects/alex/django-crud-views/docs/reference/theme.md` ("## Alerts", "### Custom alert frame")
- `/home/alex/projects/alex/django-crud-views/docs/reference/messages.md`
- `/home/alex/projects/alex/django-crud-views/docs/reference/javascript.md` ("## Dismissible alerts")
- `/home/alex/projects/alex/django-crud-views/docs/migrating-1.0.md` (alert frame entries)
- `/home/alex/projects/alex/django-crud-views/CHANGELOG.md` (Unreleased Breaking)

Planning inputs: 04-01/02/03 PLAN.md and SUMMARY.md, 04-CONTEXT.md, 04-ACCEPTANCE.md.
