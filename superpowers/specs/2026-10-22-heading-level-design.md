# Configurable heading level: one setting for the view header, package headings follow

Issue: #251.

Date: 2026-10-22

## Intent

The package's own headings are hardcoded, mostly as `h5`. On a real page the host renders the view title above
them, so the outline jumps (`h1` → `h5`, or `h2` → `h5`) and axe's `heading-order` check flags it. A downstream
project fixed this by overriding every template in the inventory below. The intent is that a project fixes it with
**one setting and no template overrides**. Avoiding template overrides downstream is the purpose of the recent
template refactoring work, and the maintainer named it as the point of this issue.

**Why the setting names the header level, not the package's level.** The issue proposed
`CRUD_VIEWS_HEADING_LEVEL`, the level of the package's headings. In the design conversation the maintainer rejected
that as unintuitive. A developer would have to work out "one below my view title, which the package can't see".
The setting instead asks something the developer already knows: **what level is your `{% cv_header %}`?** The package
derives its own headings from that.

Background: the package never renders the page/view title element itself. `{% cv_header %}`
(`src/crud_views/templatetags/crud_views.py:304`) returns the bare `view.cv_header` string, and the host's base
template (`CRUD_VIEWS_EXTENDS`) wraps it in whatever element it likes. This design keeps that ownership with the host.
It adds a tag the host *may* use so its header and the package's headings read the same setting and can't drift apart.

## Goals

- One setting, `CRUD_VIEWS_HEADER_LEVEL` (int 1–5, default `None`). It is the level of the view header
  (`{% cv_header %}`) in the host's base template.
- When it is set, every heading in the inventory renders at `CRUD_VIEWS_HEADER_LEVEL + 1`, the accordion included.
- When it is not set (default), every template in the inventory renders exactly what it renders today, including the
  accordion's `h2`. No CHANGELOG `### Breaking` entry.
- The look stays the same at any level (see "Size class").
- Inside a modal, the modal title follows the setting as the header, so the dialog has the same outline as the page.
- One block tag renders opening tag, classes and closing tag together, so a template never writes `<h…>` and `</h…>`
  separately.
- The host's base template can render the view header with the same tag at exactly `CRUD_VIEWS_HEADER_LEVEL`.

| Host's view title is… | Setting | Package headings |
|---|---|---|
| the page `h1` | `1` | `h2` |
| an `h2` under a site `h1` | `2` | `h3` |
| not set | `None` | unchanged (`h5`; accordion `h2`) |

## Inventory (in scope)

| Template | Today | Role |
|---|---|---|
| `crud_views/tags/card.html` | `h5`, class `card:title` key | one per card in a card list |
| `crud_views_workflow/view_workflow.history.html` | `h5` | section on the workflow page |
| `crud_views_workflow/view_workflow.action.html` | `h5` | section on the workflow page |
| `crud_views_object_detail/layouts/{card-rows,list-group-3col,split-card,striped-rows,table-inline,tabs-vertical}/group.html` | `h5` (with existing classes) | one per property group |
| `crud_views_object_detail/layouts/accordion/group.html` | `h2 class="accordion-header"` | one per property group |
| `crud_views/modal/content.html` | `h5 class="modal-title"` | the view header inside a modal (`"header"` mode) |

All content headings sit directly under the view header; none are nested in each other. In the accordion layout the accordion header
*is* the group heading (`accordion/object_detail.html` has no heading of its own), so it gets the same level as the
group titles of the other layouts.

## Non-goals

- `view_manage.html`, `view_guardian_manage.html`, `shared/config.html`: debug pages.
- The package rendering the page/view header itself. The base template stays the host's territory, and using the
  header tag is optional.
- A per-render override (tag argument or view attribute) for a page that embeds one of these pieces under an extra
  section heading. It stays the possible follow-up described in the issue. Until then a template override covers it.
- Per-heading levels (a key per heading). Every in-scope heading sits at the same depth.

## Anti-goals

- A setting whose number means "one below something else". That is the version the maintainer rejected.
- Anything that forces a downstream project to override templates to get a correct outline.
- Changed default output.

## Design

### Setting

`CrudViewsSettings.header_level: Any = from_settings("CRUD_VIEWS_HEADER_LEVEL", default=None)` in
`src/crud_views/lib/settings.py`. It is typed `Any`, like the E105/E106 settings, so Pydantic does not coerce `"2"` or
`True` (or crash on `"abc"`) before the system check sees the raw value (builder-check finding, my call).

System check: when not `None`, it must be an `int` (not `bool`) in 1–5. Otherwise an `Error` with the next free ID in
`crud_views.E1xx` (E100–E106 are taken today, so `crud_views.E107`). The upper bound is 5 because content headings sit
one level below and `h6` is the deepest.

### Tag: `{% cv_heading %}…{% endcv_heading %}`

A block tag in `crud_views/templatetags/crud_views.py`. It has two modes:

- **Content heading** (the package's templates): `{% cv_heading level=5 class="…" %}…{% endcv_heading %}`.
  `level` is the template's own level today, used when the setting is not set. When the setting is set, the rendered
  level is `header_level + 1`.
- **Header** (the host's base template, and the package's modal title):
  `{% cv_heading "header" level=1 class="…" %}…{% endcv_heading %}`. The rendered level is `header_level` when set,
  otherwise `level`.

`class` is optional. It accepts a template variable as well as a literal, so `card.html` keeps using the `card:title`
class key (for example via `{% cv_button_class "card" "title" as title_class %}`, if `cv_button_class` supports `as`;
otherwise the builder picks an equivalent).

The body is rendered with the caller's context, so `{% block card_title %}` and other content inside it keep working.
The `Node` sets `child_nodelists` so a template extending `card.html` can still override `card_title` inside the tag.

### Size class

Bootstrap sizes headings by tag, so a bare `h2` would look larger than today's `h5`. In both modes, when the
rendered level differs from `level`, the tag prepends Bootstrap's size class for the template's own level: `h{level}`.

- Card at setting `1`: `<h2 class="h5 card-title">`, which looks like today's `h5`.
- Accordion at setting `2`: `<h3 class="h2 accordion-header">`. `.h2` carries the same Bootstrap rules as the `h2`
  tag, so the accordion header looks as it does today. The visible text size there comes from `.accordion-button`
  anyway.

- Modal title at setting `1`: `<h1 class="h5 modal-title">`.
- Host base template `{% cv_heading "header" level=1 class="h3" %}` at setting `1`: `<h1 class="h3">`. The host
  normally writes the level it sets, so the rule never fires for it. One rule for both modes, with no extra size argument
  (my call).

When the rendered level equals `level`, no size class is added, so the default output is byte-identical to today.

### Modal (maintainer decision, 2026-10-22)

The object-detail view and custom form views can render in a modal. `crud_views/modal/content.html` shows the view
title, then the same `cv_content_template` the full page uses. The modal title is the view header in that context, so
it uses `"header"` mode: `{% cv_heading "header" level=5 class="modal-title" %}{% cv_header_icon %} {% cv_header %}{% endcv_heading %}`.
With the setting unset the modal is unchanged. With it set, the modal title is at the header level and the content
headings sit one below it, the same outline as the full page. The issue had the modal out of scope. The maintainer
brought it in on 2026-10-22 so that one rule holds everywhere: the setting is the level of your header, wherever the
header is.

### Templates

Every inventory template replaces its hardcoded `<h…>…</h…>` with `{% cv_heading level=N class="…" %}`, using the
existing classes and its current level as `N`. The object-detail templates need `{% load crud_views %}` next to their
existing `{% load crud_views_object_detail %}` (the builder checks that `crud_views_object_detail` may depend on
`crud_views` templatetags; it already depends on the core package).

### Example project (in scope, my call)

`examples/bootstrap5/project/templates/project/crud_views.html:16-30` puts the view title in an `h3` nested inside an
`h5` with a `<div>` between them. That is invalid markup, and the page has no `h1`. The example should show the
intended setup:

- Render the view title with `{% cv_heading "header" level=1 class="h3" %}{% cv_header_icon %} {% cv_header %}{% endcv_heading %}`,
  keeping its current look and the flex layout next to the context actions, without nesting headings.
- Set `CRUD_VIEWS_HEADER_LEVEL = 1` in `examples/bootstrap5/project/settings.py`.

The outline is then `h1` view title → `h2` cards / workflow sections / property groups.

The example's other pages have stray headings around the view title (`example_about.html` puts an `h6` before the
`h1`; `snippet_panels.html` has an `h5` and accordion `h2`s). They are fixed to fit that outline too, because the
example is the demo of this fix (my call). No automated axe run is added.

## Tests

- Golden snapshots of every inventory template with the setting unset: output unchanged from today. Golden files live
  under `tests/test1/golden/`.
- With `CRUD_VIEWS_HEADER_LEVEL = 1`: every inventory heading renders as `h2`. The `h5` templates get the `h5` size
  class. The accordion gets none, because its rendered level equals its own level.
- With `CRUD_VIEWS_HEADER_LEVEL = 2`: every inventory heading renders as `h3` with its size class, the accordion as
  `<h3 class="h2 accordion-header">`.
- The `"header"` mode renders exactly the setting's level, falls back to `level` when unset, and adds `h{level}` only
  when the two differ.
- Modal partial (`X-CV-Modal` request on a modal-enabled detail view): unchanged with the setting unset; at setting `1`
  the title is `<h1 class="h5 modal-title">` and the property groups are `h2`.
- Block content and caller context render inside the tag (`card_title` block override still works).
- System check: `None` and 1–5 pass; `0`, `6`, `"2"`, `True` raise `crud_views.E107`.

## Docs and CHANGELOG

- `docs/reference/settings.md`: a row for `CRUD_VIEWS_HEADER_LEVEL` that explains it as "the level of your
  `{% cv_header %}`", with the table above and a link to the tag docs.
- `docs/reference/templates.md` (or the closest page about base templates): `{% cv_heading %}`, both modes, and a base
  template example using `"header"` mode.
- `CHANGELOG.md`: an `### Added` entry. No `### Breaking` entry, so `docs/migrating-1.0.md` is unchanged.
- Bring the issue #251 body in line with this design (setting name and meaning, 1–5 range, accordion) before the PR
  opens.

## Left to the builder

- The tag's implementation (a `Node` subclass with `parse` up to `endcv_heading`), argument parsing details and error
  messages for bad arguments.
- How `card.html` gets the `card:title` class into the tag.
- Exact docs page and wording.
