# Badges

Render a property as a Bootstrap badge using `BadgeConfig` or a color string shorthand:

```python
from crud_views_object_detail.lib import x, BadgeConfig

"properties": [
    # String shorthand — fixed color
    x("status", badge="primary"),

    # Color map — value-dependent color
    x("status", badge=BadgeConfig(
        color_map={"active": "success", "inactive": "secondary"},
    )),

    # Color function — dynamic color
    x("priority", badge=BadgeConfig(
        color_fn=lambda v: "danger" if v > 8 else "warning",
    )),

    # Label map — display a different label than the raw value
    x("status", badge=BadgeConfig(
        color_map={"A": "success", "I": "secondary"},
        label_map={"A": "Active", "I": "Inactive"},
    )),

    # Pill badge
    x("category", badge=BadgeConfig(color="info", pill=True)),
]
```

| Parameter   | Description |
|-------------|-------------|
| `color`     | Fixed color name (e.g. `"primary"`, `"danger"`, or a theme-owned name) |
| `color_map` | `dict` mapping values to color names |
| `color_fn`  | Callable that receives the value and returns a color name or `None` |
| `label_map` | `dict` mapping values to display labels |
| `pill`      | `True` to use rounded-pill style |

## Resolution and template context

Color resolution uses `color_fn` first, then a nonempty `color_map`, then fixed `color`.
An empty map falls through to the fixed color. A missing entry in a nonempty map or a callback returning
`None` leaves the ordinary value rendering in place, without a neutral badge fallback. A `None` property
value skips the color callback entirely. The callback runs once per property resolution; rendering a
resolved property does not call it again.

Badge templates receive the resolved property as `prop`, plus its original value as `value`:

| Field | Meaning |
|-------|---------|
| `prop.badge_color` | Original resolved color name, or `None` when unresolved |
| `prop.badge_pill` | Requested pill state for a resolved badge; otherwise `False` |
| `prop.badge_css` | Compatible Bootstrap classes, or `None` when unresolved |
| `prop.badge_label` | Label-map result, or `None`; truthy labels win, empty labels fall back to `display_value` |
| `prop.value` / `value` | Original property value |
| `prop.choice_label` | Separate automatic choice display result, or `None` |
| `display_value` | Choice display result when present, otherwise raw `value` |

Arbitrary color names pass through unchanged. Supported names and their visual styling belong to the theme.
The stock template uses `text-bg-{color}` and appends `rounded-pill` when requested.
An empty color string still resolves to the existing `text-bg-` class; only `None` means no resolved color.
Label resolution stays independent: an unresolved color can still have a mapped label, but ordinary templates
receive raw `value` alongside `display_value` (and do not use the badge label).

Color maps/functions, label maps and link resolution always receive stored values. A truthy
explicit badge label wins over the automatic choice label, even with `choices_display=False`.
An empty mapped label falls back to `display_value`. Preserve the raw-`None` guard: badge
templates show the marker for raw `None`, while an empty string can still render an empty
badge. The stock text empty-string policy does not apply to badges.

A resolved badge takes precedence over the property's explicit `template=`. Customize the badge template
in your type pack to change badge output. When no color resolves, the explicit property template wins;
without one, choice text precedes the ordinary typed template path.

## Native semantic badge template

For a type pack named `native`, set `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "native"` and save this as
`crud_views_object_detail/types/native/badge.html` in your project's template directory:

```django
{% if value is None %}<span class="text-body-tertiary">&mdash;</span>{% else %}<span class="status{% if prop.badge_color == 'brand-custom' %} status-brand{% endif %}{% if prop.badge_pill %} status-pill{% endif %}">{% if prop.badge_label %}{{ prop.badge_label }}{% else %}{{ display_value }}{% endif %}</span>{% endif %}
```

Define `status`, `status-brand`, and `status-pill` in your theme's stylesheet. This recipe maps `brand-custom`
directly to a native color class and the pill flag to a native shape class, without parsing Bootstrap CSS.
Extend the explicit color mapping for other names your theme supports. An unrecognized resolved name still
reaches this template, but receives no color class from this minimal mapping.

Keep Django autoescaping enabled: labels and values are text, including strings containing HTML.
The recipe is exercised against real property resolution and template selection, including a counting callback,
both pill states, missing colors, and explicit-template collisions. It is a template contract example;
complete visual acceptance of a non-Bootstrap theme requires that theme's own styles and review.

!!! example "Try it live"
    The [Object Detail example](https://django-crud-views-demo.onrender.com/object-detail/product/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.
