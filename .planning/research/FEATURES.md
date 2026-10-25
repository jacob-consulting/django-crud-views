# Feature Research

**Domain:** Theme surface of a reusable Django UI package (django-crud-views 0.30.0 → 1.0.0): label modes, button
class table, form-button leaf, alert dismiss adapter, table pagination, stability policy
**Researched:** 2026-10-25
**Confidence:** MEDIUM-HIGH overall. Codebase and installed third-party sources (crispy-forms 2.6, crispy-bootstrap5
2026.3, django-tables2 3.0.0 in `.venv`) read directly: HIGH. Bootstrap 5.3 and WAI-ARIA APG pages fetched via
webfetch (the classify-confidence seam rates webfetch LOW; these are the official primary docs, so treat as MEDIUM).
Comparable-package conventions (Wagtail, django-unfold, django-components, design systems) are from training
knowledge, not re-verified this session: LOW-MEDIUM, used only for framing, never as the basis for a requirement.

## How comparable packages do it (framing)

| Concern | django-crispy-forms / crispy-bootstrap5 | django-tables2 | Wagtail / unfold / design systems | crud_views today → target |
|---|---|---|---|---|
| Form buttons | `Submit`/`Button`/`Reset` render `<input>` via `baseinput.html`; `StrictButton` renders `<button>{{ content\|safe }}</button>` (verified: `bootstrap5/layout/button.html`) | n/a | `<button>` everywhere; icon + text; icon-only uses visually-hidden text (Wagtail `w-sr-only`, GOV.UK/Primer pattern) | `<input>` with class-table classes → `<button>` through `tags/button/form.html` |
| Theme override unit | Template pack (whole directory) | One template per table, block structure (`pagination.previous`, `pagination.range`, `pagination.next`) | Component templates + design tokens | Class table + icon registry + small leaves; Tabler theme overrides **zero** button templates |
| Pagination | n/a | `&laquo;`/`&raquo;` with `aria-hidden` + translated "previous"/"next" text, `active` class only, ellipsis as `<a>` without href (verified in 3.0.0) | Icon + hidden text, `aria-current="page"` | Card pagination (#241) is the target shape; table pagination still on tables2's shape |
| JS behaviour hooks | none | none | Stimulus controllers (Wagtail) / Alpine (unfold) via `data-*` | `cv.adapters.{modal,tooltip,collapse}` + `data-cv-*`; alert is the last `data-bs-*` holdout outside dropdowns |
| Stability promise | semver, template pack contract loosely documented | semver, templates de-facto API | Wagtail documents "public API" explicitly and deprecates over two releases | `stability.md` lists only `button_classes` |

The common lesson: packages that let themes restyle **without copying templates** (class table + leaf contract) win
on upgrade cost; packages whose templates are the API (tables2, crispy packs) produce the drift the review found
(Tabler's 105-line table copy). Every feature below should move toward "register, do not copy".

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these makes the theme surface feel broken or inaccessible to a project or theme author.

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T1 | **1A: one project-wide default label mode per location** (`CRUD_VIEWS_LABEL_MODE_DEFAULTS`, per-key merge over `{"context": "icon", "list": "icon", "card": "both"}`) | Every design system has "icon buttons in dense rows, labelled buttons in forms" as a *global* decision. Today it needs a view attribute per page or knowledge of three literals. | LOW | One accessor `default_label_mode(location)`. Valid keys must be **derived from `LOCATIONS`** (not a second literal set) so Phase 2 adding `"form"` extends E108 automatically. Docs must state "this map merges per key; the per-button maps replace whole" in one sentence next to each other. |
| T2 | **E108 for the defaults setting** (unknown location, invalid mode, non-dict) | Every other label-mode knob is checked (E106/E210/E211); an unchecked one is the odd one out and fails at render (`ValueError`). | LOW | Mirror E210 message wording. Keep it an Error, not a Warning: a typo silently falls back otherwise. |
| T3 | **Zero-config output unchanged** (goldens byte-identical for 1A, 1B, 1C, 4) | Pre-1.0 users upgrade minors expecting no visual drift; the milestone constraint says so. | LOW | Golden tests are the guard. |
| T4 | **1B: filter toggle honours the label mode** (`icon` / `both` / `label`) | It is the only toolbar button that ignores `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`; users perceive it as a bug (#262). | MEDIUM | Three-way branch × two icon placements (element vs host) × JS icon swap. In `label` mode there is nothing to swap; JS must no-op on icons and still flip `aria-expanded`, call `cv.adapters.collapse.toggle`, persist. |
| T5 | **Filter toggle keeps disclosure semantics in every mode** | WAI-ARIA disclosure/toggle pattern: state lives in `aria-expanded` + `aria-controls`; the **label must not change with state** (APG button pattern: "it is critical the label on a toggle does not change when its state changes"). | LOW | Text "Filter" stays constant in `both`/`label`; only the icon swaps. Do not introduce "Show filter"/"Hide filter" text swaps. `title` only in `icon` mode (same rule as `action.html`: `cv_title` present only for icon mode). |
| T6 | **1C: one documented grammar for `form:*` keys, enforced by W362** | A theme author reads the key rule once and expects the checker to agree with the docs. Today the checker rejects what #257 needs. | LOW | Option A (`form:<kind>:<mode>`, `FORM_KINDS` frozenset) is the low-churn path; the five kinds are fixed in number and role. |
| T7 | **Docs key count pinned by test** | The number in `buttons.md` is what theme authors check their tables against (64 vs 70 drift found). | LOW | Parse the integer from the docs line in `test_default_table_is_complete`. Every later phase that adds a key (2, 3B) trips it, which is the intent. |
| T8 | **2: form buttons are real `<button type="…">` elements** | Every modern design system (Bootstrap docs, Wagtail, GOV.UK, Primer) uses `<button>`; `<input>` cannot hold an icon. | HIGH | Always emit an explicit `type` (a `<button>` without `type` inside a `<form>` is a submit; cancel must be `type="button"`). Keep `name` and `value` so POST data is unchanged; `modal.js` `FormData(form, submitter)` and the `viewset.js` cancel handler already work with `<button>`. |
| T9 | **2: accessible name for icon-only form buttons from visually-hidden text, not `title` alone** | APG: accessible name comes from content, `aria-label` or `aria-labelledby`. `title` is not reliably announced and invisible on touch. Matches the existing `action.html` icon body. | LOW (reuses leaf body) | Needs a **`form:hidden-label`** class key (default `visually-hidden`). The plan says "no new keys" for Phase 2, but the leaf reads `{% cv_button_class cv_location 'hidden-label' %}`; with no `form:hidden-label` key it resolves to `""` and the "hidden" label becomes visible in icon mode. Gap to fix in the Phase 2 spec (and the key count). Same question for `form:icon-host` (see D5). |
| T10 | **2: escaping of label, value, title** | crispy's `<button>` template renders `{{ button.content\|safe }}` (verified in crispy-bootstrap5 2026.3); a label with markup must not render as HTML. Django users assume autoescape. | LOW | Render through the crud_views leaf with autoescape; never set crispy `content`. Test with `<b>` in `submit_label` and in a cancel label whose source is a `SafeString` snippet (must stay safe, not double-escaped). |
| T11 | **2: helper `inputs` reach the leaf too** | Users expect *all* form buttons, including the list filter's Apply/Reset, to change. | MEDIUM | **Pitfall found:** `ListViewFilterFormHelper` adds its buttons with `helper.add_input()`. crispy-bootstrap5 renders `helper.inputs` in `bootstrap5/inputs.html` / `whole_uni_formset.html` with `{% include "bootstrap5/layout/baseinput.html" %}` per input: the layout object's `render()` is **never called** for inputs. Overriding `render()` (plan design point 3) covers `FormActions` layouts (create/update/delete) but not the filter buttons. Phase 2 must move the filter Submit/Reset into `helper.layout` (e.g. a `FormActions`) while `Hidden` sort/order fields stay inputs, or render them from `list_filter.inner.html`. Do not override the template pack's `inputs.html` (breaks crispy-tabler and other packs). |
| T12 | **2: ids, names, POST data and JS hooks preserved** | Tests, CSS and downstream JS select on ids (`filter-button`, `filter-button-reset`) and names. | LOW | Reproduce crispy's id rule (`{input_type}-id-{slug(name)}` when no `css_id`) and its multi-word `name\|slugify` rule, or byte-compat claims fail. `#filter-button-reset` click handler in `list.filter.js` must still bind. |
| T13 | **2: `Hidden` stays `<input type="hidden">`** | Hidden fields are not buttons. | LOW | Only `Submit`/`Button`/`Reset` move to the leaf; `layout.Hidden` untouched. |
| T14 | **2: breaking change documented** (CHANGELOG `### Breaking`, `migrating-1.0.md` "Form buttons") | `input[type=submit]` selectors in project CSS, Selenium/Playwright tests and theme tests break. | LOW | Give the replacement selectors (`button[type=submit]`, `[cv-key="submit"]`). |
| T15 | **2: default form mode `label`** | Today's forms are text-only; primary form actions are conventionally labelled (design systems discourage icon-only primary actions). | LOW | Comes from the 1A map entry `"form": "label"`, not a literal. |
| T16 | **3A: alert close works without Bootstrap JS** | A non-Bootstrap theme (Tabler-without-bootstrap, `<dialog>`-style setups) should not have to copy `tags/alert.html` for one attribute; the modal already solved this with `data-cv-modal-dismiss`. | LOW | `data-cv-alert-dismiss` + delegated handler → `cv.adapters.alert.close(el)`; fallback `el.remove()`. Bootstrap's `Alert.getOrCreateInstance(el).close()` removes the element and fades if `.fade.show` are present (verified, Bootstrap 5.3 docs). |
| T17 | **3A: close button stays a `<button type="button">` with translated `aria-label`** | Bootstrap docs require `<button>` for the close control; an icon-only close needs an accessible name. | LOW | Already true; keep it in the frame. |
| T18 | **3B: both paginations share one accessible structure** | Two conventions on one site (card vs table list) read as a bug; screen-reader users get "laquo previous" vs "previous". | LOW | Registry icons `page-previous`/`page-next` (icon renderer already emits `aria-hidden="true"`), translated hidden text, current page marked, disabled ends non-focusable (`<a>` without `href`, or `<span>`), translated `<nav aria-label>`. |
| T19 | **3B: keep django-tables2's block names** in `table/bootstrap5.html` | Projects and the Tabler theme `{% extends %}` or copy this template and override `pagination.previous`/`pagination.range`/`pagination.next`. | LOW | Change block *contents*, never block names. |
| T20 | **4: a written promise for every name a theme imports** (icons API + names, class keys, leaf templates + context, `LEAF_KEYS`, `alert_data`, `cv.adapters.*`, DOM contract, theme hooks) | A theme author cannot plan a release without knowing what semver covers. Wagtail-style "public API" lists are the norm for packages with a theme ecosystem. | LOW | Include the "adding a name is minor, renaming/removing is major" rule for icon names and class keys. |
| T21 | **4: guard test that the doc lists every public name** | Without it the list rots exactly like the key count did. | LOW | Read `stability.md`, assert dotted names and template paths. Derive the expected set from code where possible (`DEFAULT_ICONS`, `DEFAULT_BUTTON_CLASSES`, `LEAF_KEYS`, `LOCATIONS`) rather than a hand-maintained list in the test, or the test only moves the drift. |

### Differentiators (Competitive Advantage)

Aligned with the Core Value ("every public theme name settles once"). These are what crispy packs and tables2 templates
do not offer.

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| D1 | **Form buttons share the action-button label-mode contract** (`icon`/`both`/`label`, setting → ViewSet → view per-key maps, `cv-key`, `data-cv-tooltip="form"`) | One mental model for every button on the page; Tabler-style themes restyle form buttons with class keys (`form:submit:icon` → `btn-icon`) and override **no** template. No crispy template pack offers this. | HIGH | Depends on 1A + 1C. Keep the per-key map shape identical to context/list (`cv_first_inline_keys`, whole replacement). |
| D2 | **Semantic icons for form actions** (`save`, `cancel`, `filter-reset`; reuse `delete`, `filter`, `workflow`) | Themes map three names and every form gains icons; per-form `submit_icon` override for domain-specific actions (workflow). | LOW | `filter-reset`, not `reset` (cancel is also `name="reset"`). Sync test forces `BOOTSTRAP_ICONS`; Tabler's set-equality test fails loudly until mapped, which is desired. |
| D3 | **Strict-mode safety net for icon-only without icon** (raise under `CRUD_VIEWS_STRICT`, log + render label in production; W292 for static cases) | Turns the most common label-mode mistake into a message instead of an empty, unnamed button. | LOW | Extend to form buttons and the filter toggle. |
| D4 | **Adapter-driven alert dismiss with graceful fallback** | Framework-neutral behaviour layer completed (modal, tooltip, collapse, alert); the "all four adapters" story is simple to document. | LOW | Optional extra worth considering: the adapter receives the element, so a theme can add focus management (see Anti-features A9 for why upstream should not). |
| D5 | **Host-placement parity for form buttons** (`form:icon-host`) | Icon-font themes that paint icons via `::before` on the button get form buttons for free. | LOW-MEDIUM | Decide explicitly in the Phase 2 spec: either add `form:icon-host` (one key, consistent with `context`/`list`/`card`/`menu`) or document "form buttons render inline icons only". Leaving it implicit means `cv_icon_class` silently resolves to nothing. Recommendation: support it (the leaf body is copied from `action.html` anyway, and adding the key later is a minor change but adds a branch every theme must re-copy). |
| D6 | **`table:hidden-label` class key and the card snippet using its key too** | Both paginations become theme-controllable without template copies; this is what could delete Tabler's 105-line table copy eventually. | LOW | Note: `snippets/pagination.html` (#241) hard-codes `visually-hidden` today rather than `card:hidden-label`. For true parity 3B should switch the snippet to the key as well (golden-neutral, since the default is the same string). |
| D7 | **Docs-vs-code guard tests** (key count, stability list) | Self-maintaining reference docs: the thing most reusable packages get wrong. | LOW | Same mechanism in 1C and 4; consider one helper. |
| D8 | **Project-wide one-liners replace per-view recipes** (`{"card": "label"}` restores 0.29 cards; `{"form": "both"}` labels+icons every form) | Migration guide recipes shrink to one setting. | LOW | Update `migrating-1.0.md` recipes when 1A lands. |

### Anti-Features (Commonly Requested, Often Problematic)

| # | Feature | Why Requested | Why Problematic | Alternative |
|---|---------|---------------|-----------------|-------------|
| A1 | Per-ViewSet / per-view / per-variant entries in `CRUD_VIEWS_LABEL_MODE_DEFAULTS` | "Flexibility" | Duplicates the existing per-key maps and per-button fields; a sixth resolution layer makes the five-step order worse. | The map is a project-wide floor keyed by location only; finer control stays in the existing maps. |
| A2 | Themes setting label modes (e.g. `register_label_modes()`) | Tabler wanted its primary toolbar action labelled | A theme styles, a project decides what has text (review, F5 Tabler). Two writers of one default breaks predictability. | Themes register class keys like `context:secondary:icon`; projects set the defaults map. |
| A3 | Whole-dict replacement for the defaults map | Consistency with the per-key maps | `{"form": "both"}` would silently reset `card` to `icon` and change every card page. | Per-key merge (like the class table); document the difference explicitly. |
| A4 | Option B for `form:*` (`form:primary`/`secondary`/`danger`) now | Grammar purity | Renames five shipped keys and the `slot=` keyword weeks before freeze; a theme (`form:delete`) already registers them. Violates "no public name changes twice". | Option A; record the decision and the three meanings of the second segment in `buttons.md`. |
| A5 | Rendering form buttons via `tags/button/action.html` | One leaf fewer | Adds submit/cancel/name/value branches to the leaf every theme overrides. | Separate `tags/button/form.html` with the same label-mode bodies and contract keys. |
| A6 | Building `<button>` content for crispy's `StrictButton`/`button.html` | Reuse crispy | `{{ button.content\|safe }}`: any label markup becomes HTML; also leaves markup under the template pack, not crud_views. | Thin adapters whose `render()` renders the crud_views leaf. |
| A7 | Overriding crispy template-pack templates (`bootstrap5/inputs.html`, `baseinput.html`) to reach helper inputs | Quick way to catch `add_input()` buttons | Breaks or is shadowed by other packs (crispy-tabler); couples crud_views to one pack's internals. | Move crud_views' own buttons into `helper.layout`; document that third-party `add_input()` buttons stay crispy-rendered. |
| A8 | Icon-only as the default for form buttons, or an "auto" mode by viewport | Compact UI | Primary/destructive form actions need visible text (discoverability, i18n, cognitive accessibility); responsive modes need CSS/JS the leaf contract doesn't have. | Default `label`; projects opt into `both`/`icon`. |
| A9 | Upstream focus management / animations / undo for alert dismiss | Bootstrap docs warn focus is lost when a dismissed alert is removed | Where focus should go is page-specific; upstream guessing it is wrong as often as right and enlarges the frozen JS contract. | Adapter receives the element; document the Bootstrap `closed.bs.alert` focus advice in `messages.md`/`javascript.md` for projects. |
| A10 | Auto-dismissing (timed) alerts, toast conversion | Common in admin UIs | Timed removal fails WCAG 2.2.1 (timing adjustable) unless pausable; out of scope for a frame fix. | Out of scope; a theme can implement via the adapter. |
| A11 | Removing `data-bs-dismiss` support from overrides / data-API detection | "Clean" | Existing theme copies (Tabler's `tags/alert.html`) keep `data-bs-dismiss`; that must keep working under Bootstrap's data API. | Stock frame switches to `data-cv-alert-dismiss`; overrides with `data-bs-dismiss` continue to work (document it, as for the modal). |
| A12 | Rewriting the table pagination with first/last, page-size picker, jump-to-page, or new ellipsis logic | "While we're there" | DOM change beyond parity; new strings, new keys, new tests; not in the finding. | Parity with #241 only. Optional micro-fix: render tables2's `...` as a non-link `<span>` instead of `<a>` without href (it is not a link). |
| A13 | Replacing django-tables2's template with an own pagination include | DRY with the card snippet | Breaks every `{% extends "django_tables2/bootstrap5.html" %}`-style override and tables2's block contract; table and card paginators differ (`table.page` + `querystring_replace` vs `page_obj` + `base_qs`). | Same markup, two templates; a shared test asserts the shape. |
| A14 | Freezing private helpers (`_get_renderers`, `_icon_str`) because a theme imports them | The theme needs them | Freezes implementation detail. | Keep private; optionally add a public `is_library_renderer(prefix, callable)`-style helper (plan: optional). |
| A15 | Listing every template in `stability.md` as public | "Completeness" | Freezes internal includes; every refactor becomes major. | Only leaves, frames and the templates `theme.md` tells themes to override; everything else explicitly "may change". |
| A16 | Generating `stability.md` from code | Avoid drift | Policy text needs prose (what "minor" vs "major" means per surface); generated docs hide intent. | Hand-written doc + guard test that asserts presence (D7). |

## Per-feature expected behaviour (acceptance-level)

| Feature | Expected behaviour | Edge cases to cover |
|---|---|---|
| 1A | `default_label_mode(loc)` = settings value if set else package default; read by `cv_button_data`, `cv_get_action_label_mode`, `CardListView` (`cv_card_actions_label_mode=None` → map), W292 | explicit `cv_card_actions_label_mode="both"` still wins; `no_label=True` still → `icon`; unknown key → E108; `"form"` key valid only once `"form"` ∈ `LOCATIONS` (or accept it in 1A from a shared constant to avoid a two-step change) |
| 1B | `icon`: today's markup byte-identical; `both`: icon + visible "Filter", no `title`; `label`: text only, no icon spans, no `data-cv-filter-icon-*` | host placement + `both` (class on button, text visible); JS: no spans and no data attrs → icon swap skipped, `aria-expanded` still flips, state persisted; `cv_filter_expanded=True` initial render in each mode |
| 1C | W362 accepts `form:<kind>:<mode>` for the five kinds, rejects `form:submitt:icon`, `form:container:icon`, any part key with a mode | docs paragraph on the three meanings; count pinned |
| 2 | zero config: `<button>` with same text/classes/name/value/id; `{"form":"both"}`: icon+text on save/delete/cancel/filter-submit/filter-reset; `{"form":"icon"}`: hidden label + `title` + `data-cv-tooltip="form"` | filter buttons (helper inputs, T11); workflow submit icon; per-form `submit_icon` wins; `css_class` appended; extra kwargs → attrs (`data_cv_cancel_url` → `cv_cancel_url`); escaping; modal submit via `event.submitter`; `type="reset"` still navigates via JS |
| 3A | click on `[data-cv-alert-dismiss]` → `cv.adapters.alert.close(closest('[role="alert"]'))`; Bootstrap: fade + remove; no Bootstrap: `el.remove()` | alerts injected after load (modal content) — use **delegated** handler on `document`; theme override with `data-bs-dismiss` still works; `grep data-bs- templates` lists only dropdown templates |
| 3B | registry arrows + hidden translated text, `aria-current="page"` on the current item, disabled ends as non-focusable, translated nav label | prefer `aria-current` on the link/span rather than the `<li>` (Bootstrap 5.3 puts it on the `<a>`; on a `<span>` it may be omitted) — align card snippet and table template on one choice; two `<nav>` landmarks on one page need distinct labels |
| 4 | `stability.md` lists icons, buttons, alerts, JS, theme hooks with the minor/major rule; guard test green; every name Tabler imports listed (except the two private ones) | runs last, after names of 1A–3B settle |

## Feature Dependencies

```
1A defaults map (LOCATIONS-derived keys, E108)
    ├──requires──> nothing
    ├──enables───> 1B filter toggle label mode (reads "context" default via cv_get_action_label_mode)
    └──enables───> 2  form leaf ("form": "label" entry; E108 must accept "form")

1C form:<kind>:<mode> grammar (W362, FORM_KINDS, key-count test)
    └──enables───> 2  form leaf (form:submit:icon etc. pass W362)

2  form leaf
    ├──requires──> 1A, 1C
    ├──requires──> form:hidden-label key (+ decision on form:icon-host)   ← gap in plan ("no new keys")
    ├──requires──> filter buttons moved from helper.inputs to helper.layout ← gap in plan (render() not called for inputs)
    ├──requires──> icons save / cancel / filter-reset (DEFAULT_ICONS + BOOTSTRAP_ICONS sync)
    └──trips─────> 1C key-count test (intended)

3A alert adapter ──independent──> (lands before 4)
3B table pagination ──independent──> (lands before 4); adds table:hidden-label → trips 1C count test

4  stability.md + guard test
    └──requires──> 1A, 1C, 2, 3A, 3B (every frozen name final)

1B ──shares───> 2 (both: "every button reads its default from one map, renders one of three bodies")
1B ──conflicts─> none, but touches list.filter.js; 2 touches list.py filter helper → coordinate filter-reset id/handler
```

### Dependency Notes

- **1A before 1B and 2:** otherwise each adds a literal default the map then has to remove (a public behaviour change
  twice).
- **1C before 2:** otherwise #257 ships `form:<kind>:<mode>` keys the W362 check rejects, or ships Option B renames.
- **1C's count test before 2 and 3B:** both add keys (`form:hidden-label`, possibly `form:icon-host`,
  `table:hidden-label`); the test makes them update the docs number in the same PR.
- **1A key set vs Phase 2:** if E108 validates against a literal `{"context","list","card"}`, `{"form": "both"}` is
  rejected until Phase 2 edits the check. Deriving from `LOCATIONS` makes Phase 2's `LOCATIONS` change the only edit.
- **3A, 3B before 4:** their DOM attributes (`data-cv-alert-dismiss`) and keys (`table:hidden-label`) are part of the
  frozen surface. If Phase 3 is dropped, Phase 4 must document the alert close as a known Bootstrap leak in `theme.md`.

## MVP Definition

### Launch With (1.0.0)

- [ ] 1A defaults map + E108 — foundation; removes three literals; prevents a fourth.
- [ ] 1C grammar decision (A) + W362 + pinned count — key names freeze at 1.0.
- [ ] 2 form leaf incl. T8–T15 and the two plan gaps (form `hidden-label` key; helper inputs) — last button family
  outside the leaf model; breaking change only acceptable before 1.0.
- [ ] 4 stability list + guard test — the actual freeze.
- [ ] 1B filter toggle label mode — small, user-visible bug (#262); rides on 1A.

### Add After Validation (1.0.x / 1.x, non-breaking)

- [ ] 3A alert adapter — droppable for 1.0 per plan; if dropped, document the leak; adding it later is an additive
  DOM attribute change (still a DOM contract change → do it before 1.0 if at all possible).
- [ ] 3B table pagination parity — droppable; additive DOM change.
- [ ] Public `is_library_renderer` helper for themes (optional per plan).

### Future Consideration (2.0+ or never)

- [ ] Option B variant keys for forms — only if a real theme needs variant-level form styling.
- [ ] Host placement for headings (#259), container-tag check, stale-override detection (#211) — tracked separately.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| 1A defaults map + E108 | HIGH | LOW | P1 |
| 1C `form:*` grammar + count test | MEDIUM (theme authors) | LOW | P1 |
| 2 form buttons through leaf | HIGH | HIGH | P1 |
| 4 stability doc + guard test | HIGH (theme authors) | LOW | P1 |
| 1B filter toggle label mode | MEDIUM | MEDIUM | P1 |
| 3A alert dismiss adapter | MEDIUM (non-Bootstrap themes) | LOW | P2 |
| 3B table pagination parity | MEDIUM (a11y, consistency) | LOW | P2 |
| D5 `form:icon-host` | LOW | LOW | P2 (decide in Phase 2 spec) |
| D6 card snippet uses `card:hidden-label` | LOW | LOW | P2 (fold into 3B) |

## Competitor Feature Analysis

| Feature | crispy-forms (+ bootstrap5 pack) | django-tables2 | Our Approach |
|---------|----------------------------------|----------------|--------------|
| Form button markup | `<input>` (`Submit`/`Button`/`Reset`) or `StrictButton` `<button>{{ content\|safe }}` | n/a | `<button>` via crud_views leaf, autoescaped, label modes, class keys |
| Restyling buttons | override template pack or pass `css_class` per call | n/a | class table keys incl. `form:<kind>:<mode>`, zero template copies |
| Icon support | none built in (manual HTML in `content`) | n/a | semantic icon registry names per form action |
| Pagination a11y | n/a | `&laquo;` + `aria-hidden` + text "previous"; `active` class only; untranslated `aria-label="Table navigation"`; ellipsis as href-less `<a>` | registry icons, hidden translated label via class key, `aria-current`, non-focusable disabled ends, translated nav label; same as card pagination |
| JS behaviour | none | none | `cv.adapters.*` with framework-neutral `data-cv-*` hooks and DOM-removal fallback |
| Stability contract | semver; template contents de-facto API | semver; block names de-facto API | explicit theme-surface list + guard test |

## Sources

- Code read directly (HIGH): `src/crud_views/lib/crispy/buttons.py`, `lib/crispy/form.py`, `lib/views/list.py`
  (`ListViewFilterFormHelper.add_input`), `lib/view/button_data.py` (`LOCATIONS`), `lib/button_classes.py`
  (`*:hidden-label` keys exist for context/list/card only), `lib/icons.py:220` (`aria-hidden="true"`),
  `templates/crud_views/tags/{alert,context_action_filter}.html`, `tags/button/action.html`,
  `snippets/pagination.html`, `table/bootstrap5.html`, `static/crud_views/js/list.filter.js`.
- Installed third-party source (HIGH): crispy-forms 2.6 `layout.py` (`BaseInput`, `Submit` `field_classes`, id rule);
  crispy-bootstrap5 2026.3 `layout/baseinput.html`, `layout/button.html` (`content|safe`), `inputs.html`,
  `whole_uni_formset.html` (inputs included directly, `render()` bypassed); django-tables2 3.0.0
  `templates/django_tables2/bootstrap5.html` (pagination blocks, `querystring_replace`).
- Bootstrap 5.3 Alerts docs, https://getbootstrap.com/docs/5.3/components/alerts/ (close(), getOrCreateInstance,
  removal from DOM, focus-loss warning) — webfetch, seam tier LOW, official source.
- Bootstrap 5.3 Pagination docs, https://getbootstrap.com/docs/5.3/components/pagination/ (descriptive nav label,
  SR text for icon links, `aria-current` on `<a>`, disabled as `<a>` without href or `<span>`) — webfetch, seam LOW.
- WAI-ARIA APG Button Pattern, https://www.w3.org/WAI/ARIA/apg/patterns/button/ (accessible name sources, toggle
  label must not change) — webfetch, seam LOW, normative-adjacent W3C guidance.
- Project documents: `.planning/PROJECT.md`, `superpowers/plans/2026-10-24-concept-review-followups.md`,
  `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` (Tabler ledger, #257 analysis).
- Training knowledge, not re-verified (LOW-MEDIUM): Wagtail public-API/deprecation policy and `w-sr-only` icon-button
  pattern; django-unfold/Alpine, django-components conventions; WCAG 2.2.1 for timed alerts.

---
*Feature research for: Django reusable UI package theme surface (django-crud-views pre-1.0)*
*Researched: 2026-10-25*
