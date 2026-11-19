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

## Implementation examples from Tabler

These examples illustrate the approved decisions; they add no new API or requirements. The inspected
Tabler checkout was clean at `b9b568db792d806a67ea627217608185b0562018`.

### Owner heading with the existing items component (finding 38)

The following is an excerpt from the theme's `page.html`. Its `page_header_top` slot belongs to the
Tabler layout and sits above the existing view title/subtitle/action row; it is not an upstream block API.

```django
{% block page_header_top %}{% if cv_navbar %}
<div class="cv-tabler-owner">
  {% cv_breadcrumb %}
  <div class="d-flex align-items-center gap-3 mt-2 mb-3">
    {% if cv_navbar.icon %}<span class="avatar avatar-md bg-primary-lt">{% cv_icon cv_navbar.icon %}</span>{% endif %}
    <h1 class="page-title text-break">{{ cv_navbar.label }}</h1>
  </div>
  {% block cv_navbar %}<div class="cv-tabler-navbar d-print-none mb-3">{% cv_navbar_items %}</div>{% endblock %}
</div>
{% endif %}{% endblock %}
{% block breadcrumb %}{% if not cv_navbar %}{% cv_breadcrumb %}{% endif %}{% endblock %}
```

The containing template loads `crud_views`. Owner text remains autoescaped, the icon uses the registered
renderer, and the items component keeps its own accessible landmark. The ordinary title/subtitle/actions
remain outside the `if cv_navbar` guard. The breadcrumb moves into the owner header when present and
stays in its ordinary location otherwise.

The same template preserves the action extension points below the tabs:

```django
{% block actions %}{% block cv_context %}{% cv_context_actions object %}{% endblock cv_context %}{% endblock %}
```

See [the actual theme template](https://github.com/alexander-jacob/tabler-test/blob/b9b568db792d806a67ea627217608185b0562018/src/crud_views_tabler/templates/crud_views_tabler/page.html#L10)
and [its parent layout](https://github.com/alexander-jacob/tabler-test/blob/b9b568db792d806a67ea627217608185b0562018/src/django_tabler/templates/django_tabler/layouts/app.html#L13).
The full downstream template also suppresses duplicate view headings; that behavior is deliberately
excluded from this issue. For the upstream recipe, retain the view heading and choose a coherent heading
hierarchy in the surrounding theme.

### Class registration replacing the styling workaround (finding 36)

This is an illustrative consumer recipe for the approved new keys, **not code already in Tabler**.
Add the entries to a theme's existing registration in `AppConfig.ready()` after the keys ship:

```python
from crud_views.lib.button_classes import register_button_classes

register_button_classes({
    "navbar:nav": "nav nav-tabs flex-wrap gap-1",
    "navbar:link": "nav-link mw-100 text-break gap-2",
    "navbar:link-active": "active",
})
```

This selects real tab classes while retaining wrapping and long-label utilities. Tabler's links are flex
rows, so `gap-2` gives icon/label separation where literal template whitespace collapses. It is an example
spacing choice, not an exact reproduction of the current `.375rem` gap or a change to upstream defaults.
Wrapper, identity and item keys retain their defaults unless separately overridden; this split placement
renders its own owner/wrapper markup, so their keys apply only when the corresponding stock templates run.

The [current CSS workaround](https://github.com/alexander-jacob/tabler-test/blob/b9b568db792d806a67ea627217608185b0562018/src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css#L95)
restyles `.nav-pills` as underline tabs. It demonstrates why class keys are useful; do not port that CSS
into core. The recipe is a starting point for theme validation, not a claim of pixel-identical Tabler output.

### Existing downstream regression examples

[Theme rendering tests](https://github.com/alexander-jacob/tabler-test/blob/b9b568db792d806a67ea627217608185b0562018/tests/crud_views_tabler/test_theme.py#L196) check breadcrumb → owner heading →
tabs → view heading → update action order, a single breadcrumb, the section landmark and active-link
semantics, registered icon rendering, and the ordinary header when no navbar is present.
[Roastery tests](https://github.com/alexander-jacob/tabler-test/blob/b9b568db792d806a67ea627217608185b0562018/example/sales/tests/test_navbar.py#L145) separately check that Update/Delete remain
below the tabs. Adapt those assertions to upstream fixtures; do not import the downstream application,
its duplicate-heading helper, print policy, or removal of redundant context buttons.

## References

- [Downstream findings 36–38](../../../tabler-test/docs/crud_views_upstream_findings_roastery.md)
- [Original navbar design](2026-11-17-object-navbar-design.md)
- [Navbar reference](../../docs/reference/navbar.md)
- [Theme contract](../../docs/reference/theme.md#viewset-navigation-templates)
- [Class registry](../../src/crud_views/lib/button_classes.py)
