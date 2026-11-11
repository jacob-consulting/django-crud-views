# Compact widget compatibility

Issue: https://github.com/jacob-consulting/django-crud-views/issues/349

Status: design from the maintainer discussion; implementation is not part of this planning task.

## Intent

Let application developers take responsibility for custom widgets in compact formsets without requiring
django-crud-views to approve each widget class. The motivating case is the downstream `ProductSelect`,
which adds `data-beans` attributes through `create_option()` and otherwise renders normally.

## Public contract

Export an empty `CompactWidgetCompatible` marker mixin from `crud_views.lib.formsets`, defined in
`crud_views/lib/formsets/compact.py`. It provides no rendering methods, registration or configuration.

```python
from django import forms
from crud_views.lib.formsets import CompactWidgetCompatible


class ProductSelect(CompactWidgetCompatible, forms.Select):
    # Keep the application's existing create_option() implementation.
    pass
```

The marker is general: it is not restricted to Select or subclasses of the four supported stock widgets.
Normal Python inheritance carries the promise to subclasses; developers remain responsible for their overrides.

Marked widgets bypass widget-specific allowlist, template, input-type and select-option/multiple-selection
checks. Custom templates and other widget families are permitted through this explicit opt-in. Acceptance
does not certify their rendering. Unmarked widgets retain the existing exact-stock checks and rejections.

All layout/schema checks remain: field existence and coverage, hidden and identity/control exclusions,
nonempty effective labels, and uniform row field types, widget types, labels and required state. Metadata
inspection must not render widgets or evaluate choices. Classic formsets retain their existing path.

## Developer responsibility

The developer promises that the complete widget/template integration works in compact cells: associated
accessible labels or group semantics, shared desktop headings, mobile row labels, readable help/errors,
and prefixed IDs/names and any initialization needed in dynamically added rows. Necessary option labels
must remain visible. Marking a widget does not repair CSS, templates or JavaScript, nor does it guarantee
equal heights or certify arbitrary rendering overrides. The existing row-consistency check compares types
and metadata, not rendered HTML.

## Approaches considered

- **Select-only marker:** small change for ProductSelect, but requires further library changes whenever
  developers want to opt in another widget family. Superseded by the maintainer's general opt-in choice.
- **Package-owned option-attribute hook:** narrower customization, but adds a widget API and requires
  rewriting working application code. Not selected.
- **General marker:** selected; preserves conservative defaults and makes application-owned compatibility
  explicit without inspecting arbitrary Python implementations.

## Scope and acceptance

Prove a marked Select preserves option attributes and compact rendering, errors and row fragments. Prove
a marked non-Select widget and a valid custom template are accepted. Keep all unmarked rejection cases,
schema validation and query-free metadata behavior covered. Document a working public-import recipe.

Built-in CheckboxInput support is a separate issue: its crispy label branch currently does not apply the
compact label class. No checkbox template/CSS changes or new stock widget support belong here. A developer
can mark an adapted checkbox widget, but adding the marker alone does not fix that presentation issue.

No registry, adapter framework, HTML inspection, dependency additions or rendering lifecycle changes.
This is additive; document it under Unreleased without a new Breaking entry.

## GSD handover

### Approved decisions

These decisions come from the maintainer discussion for #349. Carry them forward without reopening the
Select-only alternative.

- **D-01 — General explicit opt-in:** provide a compatibility marker mixin that developers can add to their
  widget classes. It is not restricted to Select or the currently supported stock widget families.
- **D-02 — Developer-owned compatibility:** the marker expresses the developer's promise that the widget
  works with compact rendering. It adds no rendering behavior and does not certify arbitrary overrides.
- **D-03 — Preserve defaults:** existing stock widgets continue to work. Custom widgets do not gain
  automatic admission merely by being Django widget subclasses; the new extension requires the marker.
- **D-04 — Separate checkbox support:** built-in CheckboxInput support, including the desktop/mobile
  label fix and its tests, belongs in a separate issue. The marker does not itself fix checkbox rendering.

- **D-05 — Full widget-specific bypass:** marked widgets bypass all widget-specific checks (type allowlist,
  template names, input type and select option/multiple-selection settings). All shared compact schema
  checks remain, including field coverage, hidden/identity/control exclusions, labels and row consistency.
  Explicitly approved by the maintainer on 2026-11-11, resolving O-01. A marked custom-template widget,
  radio group or multiselect can pass admission even if its rendering is unsuitable; its author owns
  adaptation and verification. No automatic markup validation is added.

### Open decisions

None. D-01–D-05 settle the behavior and scope; carry them into GSD planning without asking the maintainer
to select them again. The bounded implementation details below do not require another design decision.

### Bounded implementation proposals

The working API is `CompactWidgetCompatible`, exported from `crud_views.lib.formsets`, with ordinary
inherited marker semantics. These are proposed implementation details rather than additional claims of
explicit maintainer approval. Keep the implementation small; no registry, adapter framework or renderer
changes. Preserve the existing metadata/query boundary and formset lifecycle. Exact fixtures, private
code arrangement and verification commands can be settled during GSD planning within the approved scope.

### Handoff status

Ready for GSD planning with approved decisions D-01–D-05 and no open behavior decisions. The existing
implementation tasks are inputs to GSD planning, subordinate to these decisions. Implementation has not
started. This handover does not itself start a phase, implementation or creation of the separate checkbox issue.
