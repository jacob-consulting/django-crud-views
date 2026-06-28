# Event form: stack the `with_sessions` checkbox onto its own row

**Date:** 2026-06-28
**Status:** Approved (design)

## Problem

The bootstrap5 `EventForm` example places `name` and `with_sessions` side by side
on one row. The companion registration example was just updated to stack its
fields one-per-row; the event form should match for consistency.

## Goal

Move `name` and `with_sessions` onto separate rows (checkbox on a new line) in the
event create/update form example.

## Non-goals

- No change to the sessions formset. It already renders as its own
  `<fieldset><legend>Sessions</legend>` (via the formset rendering + the
  `cv-data-toggle-group` wrapper that `toggle.js` keys off), so the registration
  example's "group in a fieldset" change has no analogue here.
- No library, template, or `ToggleGroup`/`ConditionalFormSet` change.

## Design

In `examples/bootstrap5/app/views/conditional.py`, `EventForm.get_layout_fields`:

```python
def get_layout_fields(self):
    from crud_views.lib.formsets import Formsets

    return [
        Row(Column6("name")),
        Row(Column6("with_sessions")),
        Formsets(),
    ]
```

`Column6` (half-width) is retained, matching the registration example. The
`Formsets()` placeholder is unchanged.

## Testing

Example code with no dedicated unit test. Verify by rendering `/event/create/`
with Django's test client (the bootstrap5 example has a superuser `admin`) and
confirming:

- the `with_sessions` field is no longer on the same row as `name`,
- the page still renders the sessions formset fieldset (`cv-formset-fieldset`,
  `<legend>Sessions</legend>`) and the `cv-data-toggle-field="with_sessions"`
  toggle marker.

## Backward compatibility

Example-only layout change. No public API or rendering-contract impact.
