# ViewSet Navigation: theme class keys and owner-heading layouts

**Date:** 2026-11-19
**Status:** design approved by the maintainer on 2026-11-19; issue handover, not implementation authorization.
**Issue:** [#384](https://github.com/jacob-consulting/django-crud-views/issues/384).
**Scope:** a small follow-up issue to phase 06.40 / #381, covering tabler-test findings 36 and 38.
Finding 37 (Guardian checker reuse) belongs in a separate issue. This document does not schedule a phase
or authorize product implementation.

## Problem / motivation

Let themes style ViewSet Navigation through the established class registry and use the owner identity as
the page heading. Tabler already builds that layout from the documented context and component tags; its
remaining obstacles are hard-coded classes and a contract that forbids the heading arrangement.

Keep the stock Bootstrap appearance and plain identity unchanged. Reuse existing template seams,
`register_button_classes()` and `CRUD_VIEWS_BUTTON_CLASSES`; introduce no new rendering API or settings.
Developer maintainability is a hard constraint: this is template and documentation work, with no changes
to permission admission, owner resolution, URLs or the lazy navbar builder.

## Alternatives considered

1. **Class keys plus theme guidance — selected by the maintainer.** Preserve default rendering, expose
   styling through the existing registry, and document a theme-owned owner heading. Themes retain ownership
   of page structure and heading levels; a custom heading requires a small template customization.
2. **Also ship a configurable heading variant — not selected.** Reduces theme markup but adds rendering
   configuration and heading-level decisions whose correct values depend on the surrounding page.

## gsd-handover

Carry these approved decisions and the acceptance criteria into GSD planning. Finding 38 is explicitly
included alongside finding 36. Filing this issue does not create a phase, schedule work, or authorize
implementation; finding 37 remains separate and is not a dependency of this work.

### D-01 — Bounded theme-support follow-up

Implement the selected class-keys-plus-guidance approach. Preserve the stock layout and proven runtime
paths; reuse existing registry and template mechanisms. Developer maintainability remains a hard constraint.

### D-02 — Class keys (finding 36)

Use six ordinary keys in the existing registry. These names and defaults were proposed by the assistant
and approved with the design. `navbar:nav` styles the list inside the `nav` landmark.

| Key | Default |
|---|---|
| `navbar:wrapper` | `cv-navbar mb-3` |
| `navbar:identity` | `cv-navbar-identity mb-2 fw-medium mw-100 text-break` |
| `navbar:nav` | `nav nav-pills flex-wrap gap-1` |
| `navbar:item` | `nav-item mw-100` |
| `navbar:link` | `nav-link mw-100 text-break` |
| `navbar:link-active` | `active` |

The active key adds classes only to active links; `aria-current="true"` remains independent of styling.
Follow existing registry precedence and empty-value behavior. Do not retain hard-coded copies of these
classes outside the keys. A theme can choose `nav nav-tabs flex-wrap gap-1` and add link spacing through
`navbar:link` without copying the items template.

### D-03 — Owner as page heading (finding 38)

Replace the universal prohibition in the theme contract with a distinction between the stock layout and
theme-owned layouts. A theme may use the owner identity as its page heading, put section links below it,
and render the view title/subtitle and actions as a subordinate section header. Preserve the view's actions
and extension points. The theme owns a coherent heading hierarchy; the package does not infer heading levels.

Document a recipe using escaped `cv_navbar.label`, the existing icon renderer and `{% cv_navbar_items %}`,
guarded by `cv_navbar`, with the ordinary header retained when the bar is absent. Explain integration with
the theme's own header blocks rather than inventing a new shared block contract.

### D-04 — Accessibility and component boundaries

Keep independent empty guards, visible labels, decorative icons, translated navigation naming, clickable
active links, keyboard focus and wrapping. `NavBar(template=...)` continues to select only the full wrapper;
component tags continue to resolve their theme leaves independently.

### D-05 — Acceptance and documentation

- Default classes and markup semantics remain equivalent; ordinary pages retain the stock layout.
- Theme registration and project settings can override all six keys through existing precedence rules,
  including empty classes; active semantics survive an empty or replaced active class.
- Full, component and direct-include rendering use the keys; existing wrapper selection, empty/modal
  suppression and one lazy result remain intact.
- The owner-heading recipe renders escaped identity and section links while retaining view actions and a
  useful header without a navbar. Guidance assigns heading hierarchy and narrow-screen layout to the theme.
- Update the navbar reference, theme/class-key inventory, relevant stability inventory and changelog.
  Add focused rendering/recipe coverage and run the affected existing suites with bounded pytest workers.

### D-06 — Non-goals and implementation discretion

No Guardian optimization, heading variant, automatic duplicate-title suppression, per-bar component-template
configuration, Tabler source changes or redesign of the shipped example. Requiring a template copy merely
to change classes, or broadening this into permission infrastructure, would defeat the selected approach.

The implementer chooses test organization and recipe placement using existing conventions. Any genuine
breaking change must be identified explicitly and follow the paired changelog/migration rule.

### D-07 — Separate Guardian follow-up (finding 37)

Repeated Guardian permission queries deserve their own design and query-count acceptance criteria.
That work must consider custom destination hooks, parent checks and request isolation. No checker-sharing
mechanism is approved here; theme improvements must be able to proceed independently.

## References

- [Downstream findings 36–38](../../../tabler-test/docs/crud_views_upstream_findings_roastery.md)
- [Original navbar design](2026-11-17-object-navbar-design.md)
- [Navbar reference](../../docs/reference/navbar.md)
- [Theme contract](../../docs/reference/theme.md#viewset-navigation-templates)
- [Class registry](../../src/crud_views/lib/button_classes.py)
