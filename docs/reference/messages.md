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
    <button type="button" class="btn-close" data-cv-alert-dismiss aria-label="Close"></button>
</div>
```

The close button carries `data-cv-alert-dismiss`, and closing goes through the core scripts: `adapters.js`, then
`viewset.js`, both rendered in that order by `{% cv_js %}` (see [What the scripts need](javascript.md#what-the-scripts-need)).
A click hands the alert's `role="alert"` frame to `cv.adapters.alert.close`. With Bootstrap's JavaScript on the page the
default adapter closes it through Bootstrap's `Alert` component, fade included; without it the adapter removes the
alert from the page, so the X works with or without Bootstrap's JavaScript. A theme can replace the adapter, see
[Dismissible alerts](javascript.md#dismissible-alerts). Without the core scripts the alert still renders and reads
correctly, but the X does not close it: with neither script it does nothing, and with `viewset.js` but no
`adapters.js` each click throws a `TypeError` in the console.

The classes are unchanged: `alert-dismissible fade show` and `btn-close` are still Bootstrap CSS classes, so the
stock look still needs Bootstrap's CSS. A theme that styles alerts differently overrides the frame, see
[Custom alert frame](theme.md#custom-alert-frame).

## Levels

| Django level | Class key (default) | Icon |
|---|---|---|
| `DEBUG` | `alert:debug` (`alert alert-secondary`) | `message-debug` |
| `INFO` | `alert:info` (`alert alert-info`) | `message-info` |
| `SUCCESS` | `alert:success` (`alert alert-success`) | `message-success` |
| `WARNING` | `alert:warning` (`alert alert-warning`) | `message-warning` |
| `ERROR` | `alert:error` (`alert alert-danger`) | `message-error` |

A message with no level, or with a custom level the table does not cover, renders as `info`. The colours are
[class table](buttons.md) keys, so a theme on another framework registers its own `alert:*` classes instead of
overriding a template.

`DEBUG` maps to `alert-secondary` by default, which differs from django-bootstrap5's `{% bootstrap_messages %}`
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

## A single alert: `{% cv_alert %}`

The same frame renders one alert from a template, which is how the delete page and the guardian manage page draw
theirs:

```django
{% load crud_views i18n %}

{% cv_alert "error" heading=_("This object cannot be deleted:") items=delete_protection_errors %}
{% cv_alert "info" text=_("Nothing to show yet.") %}
{% cv_alert "warning" body_template="myapp/snippets/quota.html" %}
```

| Argument | Meaning |
|---|---|
| `level` | `error`, `warning`, `success`, `info` or `debug`; anything else renders as `info` |
| `heading` | bold text before the body |
| `text` | the body of a text alert |
| `items` | a list; the alert renders it as a `<ul>` |
| `body_template` | a template rendered as the body instead; it sees the calling template's context |
| `dismissible` | add the close button (default `False`; `{% cv_messages %}` alerts are dismissible) |
| `extra_tags` | classes appended to the alert's class list |

The body is the list body when `items` is non-empty, the text body otherwise, unless `body_template` names
another. A custom body template reads the caller's variables, so wrap the tag in `{% with %}` to hand it data.
`heading`, `text` and each item are escaped unless they are safe strings, also inside
`{% autoescape off %}`.

From Python, `crud_views.lib.messages.alert_data(level, heading=…, text=…, items=…, body_template=…,
dismissible=…, extra_tags=…)` builds the dict the frame reads (`alert` in the template), and
`message_alerts(messages)` builds one per message.

## Theming

Every alert in the package goes through one frame. Three templates, each overridable on its own through a
[theme app](theme.md):

- `crud_views/tags/alert.html` — the frame: the box, the icon, the heading and the close button. It includes
  `alert.body_template` and never branches on the body type.
- `crud_views/snippets/alert/text.html` — the text body (`{{ alert.text }}`).
- `crud_views/snippets/alert/list.html` — the list body, `<ul class="mb-0 mt-2"><li>` by default.

The frame reads one dict, `alert`, with `level`, `icon_name`, `heading`, `text`, `items`, `body_template`,
`dismissible` and `extra_tags`, all escaped already. `crud_views/tags/messages.html` is a loop that includes the
frame once per message; a theme does not override it.
