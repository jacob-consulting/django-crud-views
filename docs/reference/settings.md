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

