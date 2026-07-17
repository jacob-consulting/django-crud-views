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
| `color`     | Fixed Bootstrap color name (e.g. `"primary"`, `"danger"`) |
| `color_map` | `dict` mapping values to color names |
| `color_fn`  | Callable that receives the value and returns a color name |
| `label_map` | `dict` mapping values to display labels |
| `pill`      | `True` to use rounded-pill style |
