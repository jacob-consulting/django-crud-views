# Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` | `"split-card"` | Which layout pack to use for group/property structure |
| `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES` | `"default"` | Which type template pack to use for value rendering |
| `CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE` | `"linebreaksbr"` | How newlines in `TextField` values are rendered. `"linebreaksbr"` converts newlines to `<br>`, `"linebreaks"` wraps paragraphs in `<p>` tags |

## Icons

Object detail renders its icons through the core icon registry, so there are no object detail icon settings. The
semantic names it uses are `boolean-true`, `boolean-false`, `property-detail` and `text-icon`; defaults are Font Awesome
(see the [default table](icons.md#default-table)). Group `icon` values are icon values and are **not** auto-prefixed:
write `bi:person` / `far:user` or add the name to `CRUD_VIEWS_ICONS`.

To keep the previous Bootstrap Icons look for object detail, restore the four names it uses:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = {k: BOOTSTRAP_ICONS[k] for k in ("boolean-true", "boolean-false", "property-detail", "text-icon")}
```

`CRUD_VIEWS_ICONS = BOOTSTRAP_ICONS` instead switches every icon in the package to Bootstrap Icons (load the Bootstrap
Icons CSS).

See [Icons](icons.md).
