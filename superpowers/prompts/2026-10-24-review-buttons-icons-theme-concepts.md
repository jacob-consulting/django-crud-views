# Concept Review: Icons, Buttons and Theming since 0.30.0

This is prompt work, not a spec. The result is one analysis document, no code changes.

# Skill
/django-crud-views use it

# Scope

Analyze two commit ranges together, as one body of work:

1. **The 0.30.0 release**, the icon registry: `3310379..cc095e1`
   (`feat(icons)!: semantic icon registry with libraries, renderers and system checks (#198)`,
   its review follow-ups (#199), the changelog and the version bump).
2. **Every unreleased commit** on top of it: `cc095e1..HEAD` (38 commits at the time of writing,
   `git log --oneline cc095e1..HEAD`). Skip pure dependency bumps.

Read them with their context, not only their diffs:

- `CHANGELOG.md`, sections `## Unreleased` and `## 0.30.0`
- `docs/migrating-1.0.md`
- `docs/reference/buttons.md`, `icons.md`, `theme.md`, `context_buttons.md`, `card-list-view.md`, `messages.md`,
  `javascript.md`, `assets.md`, `settings.md`, `breadcrumb.md`, `templates.md`
- the acceptance reports in `superpowers/notes/2026-10-2*.md`, they say what each feature was meant to achieve
- the open issues #257, #259, #262, #254, #211 on GitHub (jacob-consulting/django-crud-views)
- the code behind it: `src/crud_views/lib/icons.py`, `src/crud_views/lib/button_classes.py`,
  `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/messages.py`,
  `src/crud_views/lib/breadcrumb.py`, `src/crud_views/checks.py`, `src/crud_views/templates/crud_views/tags/**`,
  `src/crud_views/static/crud_views/js/*.js`

# Step 1: sort the commits by feature

Group the commits into features. A feature is one concept a theme author or a project developer has to
understand, not one PR. Derive the list from the commits; this is a starting point, not the answer:

- semantic icon registry (names, `prefix:name` libraries, renderers, `{% cv_icon %}`, checks)
- icon host placement, the icon class on the button itself (#258)
- JavaScript adapters and the jQuery-free core (#200), tooltips through `cv.adapters.tooltip` (#204, #205)
- button variants, the class table and the logic/markup leaf split (#201), utility classes in the table (#227)
- label mode: cards (#213), the class table key `location:variant:mode` (#209), context and list buttons (#216),
  per context button (#264), target-view default for the toolbar (#269)
- button containers: list markup and lone item (#261), empty container, container tag, translated label (#265, #266)
- one alert frame (#250) and `{% cv_messages %}` replacing django-bootstrap5 (#222, #226)
- the form frame template (#239) and the form fixes (#236, #191)
- cards: blocks and class keys (#243), accessible pagination from the icon registry (#241), translated empty text (#246)
- `hidden` attribute instead of `d-none` (#232)
- heading level (#251), breadcrumb label (#271)
- removals: dead detail templates (#217), old button tags, `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`

For each feature list its commits, its public surface (settings, `cv_*` attributes, template names, context keys,
class table keys, icon names, JS hooks, system checks) and the docs that describe it.

# Step 2: analyze each feature

Answer these questions per feature. Short answers with evidence, `file:line` or commit hash. "Fine" is an
acceptable answer when it is true.

**Consistent?** Same naming across settings, attributes, template context and class table keys? Same resolution
order everywhere (setting → ViewSet → view → button)? Same fallback behaviour? Same error vs warning policy in the
checks? Where do two features solve the same problem differently (for example label mode on cards vs context vs
list, icon names vs class table keys, `hidden` vs `visually-hidden` vs the class table)?

**Easy to understand?** Could a Django developer who has never seen the package configure it from the reference
docs alone? Count the concepts they must hold at once. Name the places where the docs explain the mechanism but
not the reason, or where the migration guide and the reference disagree.

**Something missing?** Gaps a theme or a project hits at once: a button location without a class key, an icon
without a registry name, a template without a documented contract, a setting without a check, a behaviour
without a test. Also the inverse: knobs nobody needs.

**Good and durable concepts?** Would the concept survive a second theme, a third icon library, a non-Bootstrap
CSS framework, Django 6 and the 1.0.0 stability promise in `docs/development/stability.md`? Which parts are
Bootstrap leaking through a neutral-looking API (dropdown DOM, `visually-hidden`, `btn-*`, `data-bs-*`,
`modal-*` tokens)? Which decisions would be expensive to reverse after 1.0.0?

**Security?** Look for `mark_safe`, `format_html`, `|safe`, autoescape blocks and string concatenation into
`class`, `title`, `aria-label`, `data-*` and `href` attributes. Which inputs are developer-controlled (settings,
class attributes) and which can carry user or database content (labels rendered from templates, object `__str__`,
tooltip titles, breadcrumb labels, messages)? Does the pluggable icon renderer let a theme inject unescaped
markup, and is that documented as its responsibility? Does anything undo the CSP work
(`superpowers/plans/2026-05-18-csp-compatibility.md`): inline styles, inline handlers, `javascript:` URLs? Do
the `CRUD_VIEWS_STRICT` fail-soft paths hide a problem in production that would be a bug in DEBUG?

**What could be improved?** Concrete, one line each, with the reason. Mark each as "before 1.0.0" or "can wait".

# The theme author's perspective

Run the whole analysis from the viewpoint of someone building **crud_views_tabler**, a theme for
[tabler.io](https://tabler.io): Bootstrap 5 based, Tabler Icons (`ti ti-*` webfont or inline SVG), `btn-icon`
icon-only buttons, its own card, page header, alert and empty-state markup, dropdowns and tooltips through
`window.tabler`. `docs/reference/theme.md` and `docs/reference/javascript.md` already mention it.

For every feature say which of the three mechanisms the theme would use, and whether the mechanism suffices:

1. **register**: the icon registry, the class table (`CRUD_VIEWS_BUTTON_CLASSES`), the JS adapters, assets
2. **override a leaf**: `tags/button/action.html`, `menu_item.html`, `container.html`, `alert.html`, the form frame,
   the card blocks
3. **copy a template**: anything where the theme must ship a full copy of a crud_views template and keep it in
   sync (see #211)

Count how many templates the Tabler theme must copy, and why registration or a leaf override does not reach. Each
copied template is a maintenance cost and a hidden-breakage risk; say which of them the current design could
avoid with a small change. Note also what a theme cannot do at all today.

# Issue #257: label mode for form buttons

Read issue #257 (label / icon / both for submit, delete, cancel, filter-submit, filter-reset). Judge how its design
fits the concepts above:

- Does it reuse the label-mode resolution (setting → ViewSet → view) and the class table keys exactly as the
  context, list and card buttons do, or does it introduce a fourth variant of the same idea?
- The issue proposes a default of `label` for form buttons while context and list default differently. Is that
  defensible, or an inconsistency a developer will trip over?
- New icon names `save`, `cancel`, `reset`: do they follow the registry's naming, and do they exist in
  `BOOTSTRAP_ICONS` and the Tabler mapping?
- `<input>` becomes `<button>`: which other features depend on the form buttons being `<input>` (crispy layout,
  `viewset.js` cancel handling, `data-cv-cancel-url`, tests, the modal shell)?
- Would the form buttons render through `tags/button/action.html`, so a Tabler theme overrides one leaf for every
  button on the site, or would they need their own leaf? Which is right?
- Is there anything in #257 that should change *before* it is implemented, given what the review found?
- How do the related issues #262 (filter toggle label mode) and #259 (host placement for headings and modal
  titles) interact with it: one feature or three?

# Step 3: synthesis

Finish with:

- the five findings that matter most, ranked, each with the feature it belongs to and the fix you would propose
- the list of things that must be settled before 1.0.0 because changing them later breaks every theme
- the list of things that are fine as they are, so nobody reopens them

# Output

One Markdown document at `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md`. Structure: Scope,
Feature map (Step 1), one section per feature (Step 2, each with the Tabler sub-section), Issue #257, Synthesis,
Not checked.

# Constraints

- don't guess; when a question needs running code or a test to answer, run it and say so
- be precise: cite `file:line`, commit hashes, issue numbers, setting names as they are spelled in the code
- ground every claim in the repository or the issues; mark an opinion as an opinion
- be honest: a feature that is fine gets one line, not a page
- no code changes, no spec, no plan; this is analysis
- end with a "Not checked" section listing what you did not look at
