# Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` | `"split-card"` | Which layout pack to use for group/property structure |
| `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES` | `"default"` | Which type template pack to use for value rendering |
| `CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE` | `"linebreaksbr"` | How newlines in `TextField` values are rendered. `"linebreaksbr"` converts newlines to `<br>`, `"linebreaks"` wraps paragraphs in `<p>` tags |
| `CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT` | `False` | Automatically show terminal model field help text unless overridden by the view or property |

## Help-text precedence

`cv_object_detail_show_help_text = None` (the view default) inherits the project setting.
A Python `True` or `False` on the view overrides it. Property `detail` is resolved first:

| Property `detail` | Result |
|-------------------|--------|
| Omitted or `None` | Inherit view → project → `False` |
| `True` | Terminal field help text, or no text if absent |
| `False` or `""` | Suppress regardless of inherited policy |
| Non-empty string or supported lazy translation string | Explicit text regardless of policy |

Booleans are instructions, never rendered words. The string `"False"` is explicit text.
For example, with a `text` model field that declares help text:

<!-- object-detail-value-recipe: help-instructions -->
```python
from django.utils.translation import gettext_lazy as _
from crud_views_object_detail.lib import x

properties = [
    "text",                          # inherit
    x("text", detail=None),          # inherit
    x("text", detail=True),          # force terminal model help
    x("text", detail=False),         # suppress
    x("text", detail=""),            # suppress
    x("text", detail="Used for invoices."),
    x("text", detail=_("Invoice guidance")),
]
```

Only terminal field metadata supplies automatic text: `customer__country` uses
`country.help_text`, never intermediate relationship help. Computed values have no automatic
help, but can use explicit descriptions. Policy selection adds no queries. Normal views,
direct resolvers and raw `render_object_detail` tags share this selection; raw tags forward
the context `view`, and without a view use project policy. Already-resolved groups retain
their selected detail when rendered in a different context; supported lazy text is evaluated
in the rendering language.

### Setting lifetime and tests

Only Python `True`/`False` are supported project values; quoted strings and integers are
unsupported. This is startup configuration, not a live-reload API: the cached accessor reads
once per settings instance. Tests using runtime setting overrides need fresh singleton
references in both modules (as well as the usual `settings` fixture or `override_settings`):

<!-- object-detail-value-recipe: settings-fixture -->
```python
import pytest
from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.templatetags import crud_views_object_detail as tags


@pytest.fixture(autouse=True)
def fresh_object_detail_settings(monkeypatch):
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
```

If a test changes settings more than once, refresh the singleton before resolving under the
new setting. This fixture is a test harness, not a production cache invalidation API.

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
