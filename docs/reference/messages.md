# Flash messages

crud_views already *emits* flash messages: create, update and delete views push a
`django.contrib.messages` success message built from their
[`cv_message_template`](create_view.md) snippet, the ordered up/down views do the same, and
[`ActionView`](action_view.md) pushes a success or an error message per action. `{% cv_messages %}`
renders that queue as Bootstrap 5 alerts.

## Usage

Place the tag in your own base template — typically at the top of the content area, next to
[`{% cv_breadcrumb %}`](breadcrumb.md):

```html
{% load crud_views %}

<main class="container">
    {% cv_messages %}
    {% block content %}{% endblock content %}
</main>
```

It renders nothing when there are no messages, and nothing when `messages` is missing from the
template context altogether (a project without
`django.contrib.messages.context_processors.messages`), so it is safe to place unconditionally.

Each message becomes one dismissible alert:

```html
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <i class="fa-solid fa-circle-check me-2" aria-hidden="true"></i>Created publisher <strong>Penguin</strong>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
```

The close button uses Bootstrap's own `data-bs-dismiss="alert"`, so it needs Bootstrap's
JavaScript bundle on the page. Without it the alert still renders and reads correctly; only the
X does nothing.

## Levels

| Django level | Alert class | Icon |
|---|---|---|
| `DEBUG` | `alert-secondary` | `message-debug` |
| `INFO` | `alert-info` | `message-info` |
| `SUCCESS` | `alert-success` | `message-success` |
| `WARNING` | `alert-warning` | `message-warning` |
| `ERROR` | `alert-danger` | `message-error` |

A message with no level, or with a custom level the table does not cover, renders as `info`.

`DEBUG` maps to `alert-secondary`, which differs from django-bootstrap5's `{% bootstrap_messages %}`
(it mapped `DEBUG` to `warning`). Debug messages are hidden by the default message level anyway, so
this only shows up in a project that lowers `MESSAGE_LEVEL`.

`extra_tags` are appended to the alert's class list, so
`messages.info(request, "…", extra_tags="mb-0")` renders `class="alert alert-info alert-dismissible
fade show mb-0"`.

Message bodies are rendered unescaped when they are safe strings — crud_views' own message
snippets mark themselves safe and contain `<strong>…</strong>` — and escaped when they are plain
strings.

## Icons

The five icon names come from the [icon registry](icons.md), so they follow
`CRUD_VIEWS_ICONS` like every other icon. Switch one off with an empty value:

```python
CRUD_VIEWS_ICONS = {"message-info": ""}  # info alerts render text-only
```

Bootstrap Icons users get the whole set from the existing preset:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = BOOTSTRAP_ICONS
```

## Theming

The markup lives in `crud_views/tags/messages.html` and resolves through the theme path, so a
[theme app](theme.md) overrides it by shipping its own template at that path. The context is a
single key, `cv_message_alerts`, a list of dicts with `message`, `css_class` (the Bootstrap
contextual class, without the `alert-` prefix), `icon_name` and `extra_tags`. The level mapping
itself lives in `crud_views.lib.messages` (`ALERT_CLASSES`, `ICON_NAMES`) and is reusable from a
custom template tag.
