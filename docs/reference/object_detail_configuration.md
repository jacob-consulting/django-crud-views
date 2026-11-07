# Configuration

## Property Paths

Properties are referenced by field name. Use `__` to traverse relationships:

```python
"properties": [
    "title",                    # simple field
    "author__name",             # FK traversal
    "author__country__code",    # multi-hop FK
    "tags",                     # M2M (renders all related objects)
    "get_absolute_url",         # method or property
]
```

## The `x()` Helper

For more control over individual properties, use the `x()` shorthand to build a `PropertyConfig`:

```python
from crud_views_object_detail.lib import x

"properties": [
    "title",
    x("author__name", title="Writer"),
    x("published_date", detail="When the book was first published"),
    x("rating", type="integer"),
    x("notes", template="myapp/custom_notes.html"),
]
```

| Parameter  | Description |
|------------|-------------|
| `path`     | Field name or `__`-separated path (required) |
| `title`    | Override the auto-derived label |
| `detail`   | Inherit (`None`), force model help (`True`), suppress (`False`/`""`), or explicit text; see [help precedence](object_detail_settings.md#help-text-precedence) |
| `type`     | Override the auto-detected type (e.g. `"date"`, `"boolean"`) |
| `template` | Path to a custom template for rendering the value |
| `link`     | `LinkConfig` or URL name string (see [Links](object_detail_links.md)) |
| `badge`    | `BadgeConfig` or color string (see [Badges](object_detail_badges.md)) |
| `choices_display` | `True` (default) displays scalar model choice labels; `False` keeps stored codes |

## Choice labels and raw values

Plain field paths display Django choice labels by default. String, integer and boolean scalar
fields are supported, including terminal scalar fields reached through single-object FK/O2O paths.
The terminal model's `get_FIELD_display()` supplies the label and unknown-code fallback.
Automatic `verbose_name` titles and explicit `title` overrides still work. Setting `type` does
not disable choice display: use `choices_display=False` to restore raw presentation.

For a model with `process` choices such as `("natural", "Naturally processed")`:

<!-- object-detail-value-recipe: choices -->
```python
from crud_views_object_detail.lib import x

cv_property_display = [
    {
        "title": "Processing",
        "properties": [
            "process",
            x("process", title="Stored process", choices_display=False),
            {"path": "process", "choices_display": False},
        ],
    }
]
```

A declared nonempty label for a blank value (including `None`) remains meaningful text.
Missing related owners stay empty: only an absent **supported scalar choice owner** projects
an empty display string, including with the raw opt-out. Its raw `None` or `[]` stays unchanged.
This does not normalize other missing paths. Collections, including one-member collections,
keep their existing values, order and duplicates; choice labels are not mapped over them.
Terminal FK/O2O relation fields themselves retain relation rendering. Non-choice fields,
model methods/properties and view-callable fallbacks retain ordinary behavior.

### Display metadata and template ownership

`ResolvedProperty.value` and template `value` remain raw. `prop.choice_label` is a separate
display result; `None` means no display result, not proof that the model lacks choices.
An empty result can represent an absent supported scalar choice owner. The value-template
context supplies `display_value`: `choice_label` when it is not `None`, otherwise raw `value`.
Unknown-code fallback may preserve non-string types. Django choice labels use the language
active when resolved and are not retranslated when pre-resolved groups render. Supported lazy
help/detail text instead follows the active language at rendering.

Dispatch is **resolved badge → explicit property template → choice text → ordinary type**.
Choice text uses the type pack's `char.html`, then its `default.html`, then the stock
`char.html` fallback. Custom templates retain output ownership and raw `value`; opt into `display_value`
when wanted. Badge and link inputs remain raw. See [badge fallback](object_detail_badges.md#resolution-and-template-context).

## Copied text value template

Use this body for a copied `char.html` or `default.html` value leaf. The exact check keeps
`0`, `False` and whitespace-only strings visible; do not use a broad falsy test or trim text.
Django autoescaping stays enabled for both labels and raw strings.
The choice branch uses `unlocalize` so an unknown numeric code such as `10000` stays
ungrouped even when thousand separators are enabled. This affects output only:
`value`, `prop.choice_label` and `display_value` retain their original types.
Ordinary numeric output keeps its existing localization.

<!-- object-detail-value-recipe: text-leaf -->
```django
{% load l10n %}{% if display_value is None or display_value == "" %}<span class="text-body-tertiary">&mdash;</span>{% elif prop.choice_label is not None %}{{ display_value|unlocalize }}{% else %}{{ display_value }}{% endif %}
```

Stock `char`, `text` and fallback `default` show this muted em dash for exact `None`/`""`
after choice display is selected. Rows, labels and explicit detail remain present.
For copied `text.html`, keep its existing `property_text_newline` branch and apply
`linebreaks` or `linebreaksbr` to `display_value` in the nonempty branch.
Badge, relation and collection empties keep their existing policies. Custom templates can
choose different output; see the [value context inventory](object_detail_layout_packs.md#template-projection-and-stable-targets).

## Groups

Each entry in `cv_property_display` is a group with a title and a list of properties:

```python
cv_property_display = [
    {
        "title": "Basic Info",
        "description": "Core book metadata",
        "icon": "bi:book",
        "properties": [
            "title",
            "author__name",
            x("isbn", detail="International Standard Book Number"),
        ],
    },
]
```

| Parameter     | Description |
|---------------|-------------|
| `title`       | Group heading (required) |
| `id`          | Optional stable group key; strict ASCII token, independent of translated title |
| `description` | Subtitle or help text |
| `icon`        | Icon value: `prefix:name`, a semantic name from `CRUD_VIEWS_ICONS` or a raw CSS class (see [Icons](icons.md)) |
| `properties`  | List of strings, dicts, or `PropertyConfig` objects |

Properties can be mixed freely — plain strings, dicts with `PropertyConfig` fields, or `x()` / `PropertyConfig` instances.

## Component and group identity

Set `cv_object_detail_id = "author-page"` on an object-detail view for stable component
targets, or override `cv_get_object_detail_id()` for request-aware identity. The view
projects this as `object_detail_id`; the stock content template forwards it to the tag.
A raw tag can pass the same input explicitly:

```django
{% load crud_views_object_detail %}
{% render_object_detail object groups=object_detail_groups component_id="author-page" %}
```

Both supplied component tokens and group `id` keys must match `[A-Za-z][A-Za-z0-9_-]*`.
Empty strings, whitespace, non-ASCII tokens, punctuation outside `_-`, and non-string
values fail; `None` means omitted. Duplicate group keys within one component fail too.
For stable links use explicit group keys, such as `{"id": "bio", "title": "Biography",
"properties": ["name"]}`. Otherwise the fallback is positional: reordering changes
the group's target. Display titles can be repeated, empty or translated without collisions.
See the [exact target formula and collision boundary](object_detail_layout_packs.md#template-projection-and-stable-targets).

### Page and modal identity

Use this mixin before your object-detail view base. It reads the actual request header;
`cv_modal` enables modal behavior and is not the request discriminator.

```python
from crud_views.lib.view.base import cv_is_modal_request


class AuthorIdentityMixin:
    def cv_get_object_detail_id(self):
        return "author-modal" if cv_is_modal_request(self.request) else "author-page"
```

Normal requests use `author-page`; `X-CV-Modal: true` requests use `author-modal`.
Repeated renders preserve these targets. Additional repeated instances need their own
distinct tokens (for example `author-sidebar`): this two-context recipe alone cannot
distinguish two modals or two page components. Applications own uniqueness when independently
fetched responses or untransported fresh backend renders are assembled into one page.

## View-Callable Fallback

If a `path` cannot be resolved on the model instance (the first segment is not an attribute or method on the instance), the resolver will try to call `view.<path>(instance)` instead.

This lets you compute display values using view-level context (e.g. `self.request`, view kwargs, or logic that doesn't belong on the model):

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired


class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {
            "title": "View-Computed",
            "properties": [
                x("view_computed_summary", title="Summary"),
            ],
        },
    ]

    def view_computed_summary(self, instance):
        return f"{instance.title} by {instance.author_list()} ({instance.pages} pages)"
```

**Rules:**

- The view method must be callable — non-callable attributes on the view are ignored (value becomes `None`)
- If the path **is** found on the model (even as `None`), the view fallback never runs — model always takes priority
- This works automatically when using `ObjectDetailView` / `ObjectDetailMixin`, or when using the
  `{% render_object_detail %}` template tag from within a Django CBV template (Django adds `view`
  to context via `ContextMixin`)
