# Migrating to 1.0.0: one upgrade guide from 0.29.x

Issue: #253.

Date: 2026-10-22

## Intent

Everything pending goes into the first major release, 1.0.0, mostly because it is full of breaking changes and
theme-compatibility work. `CHANGELOG.md` records each change by release and issue, but nobody upgrades by reading
it: the steps are spread over two releases, some 0.30.0 notes are already out of date, and the breaks that raise
nothing are mixed in with the ones that do.

0.30.0 should not have shipped as a minor release: its icon registry was already a breaking change. So the guide
starts from **0.29.x** and covers 0.30.0 and everything under `## Unreleased`.

**Who reads it.** The maintainer is the only downstream maintainer. The guide is written for their own projects and
their own theme, but it lives in the public docs, so it is written generically: "your project", "a downstream
theme". Its two readers:

1. **An app on the stock bootstrap5 theme.** It overrides no crud_views template, but it still has a base template,
   settings, view attributes, maybe a Python override or custom JS, and CSS or tests that select on markup.
2. **A downstream theme maintainer**, for example a theme built on Tabler. The public `crud_views_tabler` package
   may be named (the CHANGELOG already does); Tabler, the public UI kit, may appear as the example framework.

## Goals

- A reader on 0.29.x reaches the 1.0.0 behaviour by working through one page, without reading the CHANGELOG.
- Every step describes the **net** change from 0.29.x to 1.0.0, not the route through 0.30.0. Examples of 0.30.0
  notes that later changes overtook: the boolean widget `detail/widgets/bool.html` (switched icons in 0.30.0, deleted
  in #217), and `tags/actions_menu_item_label.html` (gained `cv-icon-fw` in 0.30.0; the stock menu moved off it to
  `tags/button/menu_item_label.html`).
- Steps that came in 0.30.0 are marked so a reader already on 0.30.0 can skip them.
- Every break that renders wrong without raising sits in one checklist.

## Non-goals

- Declaring what counts as stable API after 1.0. Stability comes just before the release, and more changes may land
  first. `docs/development/stability.md` stays as it is.
- Release mechanics: the version bump, the `Development Status` classifier, the "Current version" lines.
- Migrating any downstream project. The guide is the deliverable. Nothing in the downstream projects or their
  submodules is changed, not even a scratch edit; they are only read.
- Releases before 0.29.x.
- Rewriting the CHANGELOG. The CHANGELOG stays the complete record; the guide is the route through it. (A break
  with no entry at all is the exception, see Grounding.)

## Anti-goals

- **No downstream project and no client is named anywhere in a committed file** (`crud_views_tabler` excepted,
  maintainer's decision): not in the guide, not in this spec,
  the plan, commits or the PR. The local list of downstream projects and the words that must never appear live in
  the maintainer's private notes (Claude memory `never-name-client-projects-in-docs`), not in the repo. Before every
  commit, grep the staged diff for those words.
- No step that isn't backed by a CHANGELOG entry and the code. Don't guess.
- Don't copy the reference docs. Link to them.

## The page

`docs/migrating-1.0.md`, titled "Migrating to 1.0.0", listed in `docs/.pages` right after Home. The CHANGELOG's
`## Unreleased` heading gets a one-line pointer to it.

Sections, in order:

1. **Who this is for.** Coming from 0.29.x. Readers on 0.30.0 skip the steps marked *0.30*.
2. **Step zero, for everyone.** Upgrade, run `manage.py check`, fix every error and warning. A table lists the codes
   these releases introduce or tighten (for example `crud_views.E350`, `E360`, `E361`, `W362`, `E106`,
   `viewset.E209`, `E210`, `E211`, `E250`, `W246`, `W291`) and what each one replaces. Also the runtime errors:
   `TypeError` from an old `cv_get_context()` signature, `ValueError` from `cv_no_label`.
3. **An app on the stock bootstrap5 theme**, organised by where the reader looks in their project:
   - base template: `django-bootstrap5` is no longer a dependency, `{% cv_messages %}`, `crud_views/css/icons.css`
     for projects that list their CSS by hand;
   - settings: the removed icon settings, `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`, the `BOOTSTRAP_ICONS` recipe;
   - views and Python: `cv_modal_size` tokens, `cv_get_context(location=...)`, `cv_no_label`, `CardAction.variant`
     and the card label mode default, bare object-detail group icons, removed crispy button tags;
   - JavaScript: `cv.cvModalOpen` size tokens, jQuery no longer required by core, Bootstrap tooltips and the
     `cv.adapters.tooltip` opt-out;
   - CSS and tests that select on markup: the DOM changes (button attribute order, pagination, tooltips, sort icon
     direction, `hidden` instead of `d-none`, formset control titles, and so on).
4. **A downstream theme**:
   - templates to delete, because a hook now covers what the override did;
   - templates to move: the 0.30-era leaves that are now logic templates (`tags/context_action.html`,
     `list_action.html`, `card_action.html`, `actions_menu_item.html`, `actions_menu_item_label.html`) → the
     `tags/button/` leaves; `tags/messages.html` → `tags/alert.html`;
   - the hooks that replace copied templates: the button class table (including the alert and card keys and the
     utility slots), the icon registry (`register_icon_library`, `register_icons`, icon names such as `page-previous`
     and `message-<level>`), `snippets/form_frame.html`, the card blocks, the alert frame and its bodies,
     `cv.adapters`;
   - contract changes in templates a theme may still override: `cv_icon_action` and friends hold icon names
     rendered with `{% cv_icon %}`, `cv_label_mode` replaces `cv_label_visible`, the `#filter-collapse` id and the
     filter toggle's `aria-*`, `data-cv-modal-dismiss`, `data-cv-class` on the formset controls.
5. **Silent breaks.** One checklist of everything that renders wrong and raises nothing. Known at the time of writing:
   - an old `tags/messages.html` override renders `class="alert alert-"` with an empty body;
   - a hand-written `data-cv-modal-size="modal-lg"` or `cv.cvModalOpen(url, "modal-lg")` gets the default size;
   - a `context_action_filter.html` override with `class="d-none"` shows the wrong icon after the first click;
   - an override of `tags/actions_menu_item_label.html` no longer affects the stock menu;
   - a bare object-detail group icon `icon="truck"` renders an invisible `<i class="truck">`;
   - `<i class="{{ cv_icon_action }}">` in a custom template renders an invisible icon;
   - `formsets/control.html` overrides without `data-cv-class` no longer recolour the delete toggle;
   - CSS or tests that target `.disabled > span.page-link`, the `&laquo;` / `&raquo;` arrows or the old button
     class strings.

How each step reads: "if you have X, do Y", with a short before/after only where it saves the reader a lookup, and
a link to the reference page and the issue number.

## Grounding

- Source of truth: `## 0.30.0` and `## Unreleased` in `CHANGELOG.md`, checked against the code and templates on
  `main`. Where they disagree, the code wins, and the mismatch is reported to the maintainer.
- Coverage check: scan the downstream projects from the private notes **read-only**, starting with the most
  important one (vendored at 0.29.0, with a theme app overriding 14 `crud_views/` and 17
  `crud_views_object_detail/` templates), then the Tabler theme. Every usage the 1.0 changes touch must map to a
  step in the guide. Anything that doesn't is a gap in the guide. The scan's findings, with a per-project checklist,
  go to a scratch file outside the repo and are never committed.
- The coverage scan is part of done, not optional. The private note exists and lists both the forbidden words and
  the project paths.
- *Builder's call, made in the design:* a real 0.29 → 1.0 break that the code shows but the CHANGELOG doesn't
  record gets a bullet added under `## Unreleased` → `### Breaking` **and** a step in the guide. The guide is
  never knowingly incomplete, and every step is still backed by a CHANGELOG entry.
- *Builder's call, made in the design:* a reference page the guide links to that turns out to be wrong about the
  code is fixed in this change, not just reported. Each fix is listed in the acceptance note.

## Keeping it current until 1.0

More breaking changes may land before the release. The maintainer's call: a written rule, no CI test. One line goes
into `CLAUDE.md` under Conventions: a change that adds a `### Breaking` entry to the CHANGELOG also updates
`docs/migrating-1.0.md`.

## Also in this change

- A CHANGELOG bullet under `## Unreleased` → `### Added` for the guide (#253).
- `task docs` (or `mkdocs build`) builds without new warnings; every link and anchor in the guide resolves.

## Left to the builder

- The exact wording, the order of steps within a section, and when a before/after snippet pays off.
- Whether the error-code table and the silent checklist link back to their steps or repeat them in one line.
- How to mark 0.30 steps (a tag in the heading, an admonition, or a column).
