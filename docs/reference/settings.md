# Settings

## Basic settings

| Key                  | Description                                              | Type  | Default      |
|----------------------|----------------------------------------------------------|-------|--------------|
| THEME                |                                                          | `str` | `plain`      |
| EXTENDS              |                                                          | `str` | `None`       |
| MANAGE_VIEWS_ENABLED | Show manage view button, values are: `yes,no,debug_only` | `str` | `debug_only` |

## Session

Session settings.

| Key              | Description                                                | Type  | Default   |
|------------------|------------------------------------------------------------|-------|-----------|
| SESSION_DATA_KEY | The session key used to store data for `django-crud-views` | `str` | `viewset` |

## Filter

Settings for filter.

| Key                           | Description                                     | Type   | Default            |
|-------------------------------|-------------------------------------------------|--------|--------------------|
| FILTER_PERSISTENCE            | Store filter in Django session                  | `bool` | True               |
| FILTER_ICON                   | Filter icon (boostrap5 only)                    | `str`  | fa-solid fa-filter |
| FILTER_RESET_BUTTON_CSS_CLASS | Filter reset button css flass (bootstrap5 only) | `str`  | btn btn-secondary  |

## View Context Actions

Default context actions for CRUD views.

| Key                           | Description   | Type        | Default                  |
|-------------------------------|---------------|-------------|--------------------------|
| LIST_CONTEXT_ACTIONS          | Global switch | `List[str]` | `parent, filter, create` |
| DETAIL_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home, update, delete`   |
| CREATE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home`                   |
| UPDATE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home`                   |
| DELETE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home`                   |
| MANAGE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home`                   |
| CREATE_SELECT_CONTEXT_ACTIONS | Global switch | `List[str]` | `home`                   |

## List Actions

Default list actions for list view.

| Key          | Description   | Type        | Default                  |
|--------------|---------------|-------------|--------------------------|
| LIST_ACTIONS | Global switch | `List[str]` | `detail, update, delete` |

## django-object-detail

Settings for the [django-object-detail](https://django-object-detail.readthedocs.io/en/latest/) package used by the [DetailView](detail_view.md). These are standard Django settings (not prefixed with `CRUD_VIEWS_`).

| Key                                  | Description                                          | Type   | Default        |
|--------------------------------------|------------------------------------------------------|--------|----------------|
| `OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` | Layout pack for group/property structure              | `str`  | `"split-card"` |
| `OBJECT_DETAIL_TEMPLATE_PACK_TYPES`  | Type template pack for value rendering                | `str`  | `"default"`    |
| `OBJECT_DETAIL_ICONS_LIBRARY`        | Icon library: `"bootstrap"` or `"fontawesome"`        | `str`  | `"bootstrap"`  |
| `OBJECT_DETAIL_ICONS_CLASS`          | Base CSS class (`"bi"` or `"fa"`)                     | `str`  | per library    |
| `OBJECT_DETAIL_ICONS_TYPE`           | Icon type (`None` for Bootstrap, `"regular"` for FA)  | `str`  | per library    |
| `OBJECT_DETAIL_ICONS_PREFIX`         | Icon name prefix (`"bi"` or `"fa"`)                   | `str`  | per library    |
| `OBJECT_DETAIL_NAMED_ICONS`          | Dict mapping named icons to icon names                | `dict` | per library    |

Example configuration for Font Awesome with Bootstrap 5:

```python
OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
OBJECT_DETAIL_ICONS_TYPE = "solid"
```
