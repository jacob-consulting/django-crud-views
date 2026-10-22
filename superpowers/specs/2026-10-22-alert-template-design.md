# One data-driven alert template for messages, the delete page and the guardian manage page

Issue: #250.

Date: 2026-10-22

## Intent

Six places in the package write Bootstrap alert markup by hand:

| Template | Alerts | Body |
|---|---|---|
| `tags/messages.html` (`{% cv_messages %}`) | one per message | text, dismissible |
| `snippets/delete/protection_errors.html` | one, `alert-danger` | heading + `<ul class="mb-0 mt-2"><li>` |
| `snippets/delete/related_objects.html` | three: danger, warning, warning | heading + list; heading + list; heading + `related_objects_tree.html` |
| `crud_views_guardian/.../view_guardian_manage.html` | one, `alert-warning` | the guardian config `<table>` |

The issue counted the first three. Design recon found the guardian one as well, and the maintainer brought it into
scope on 2026-10-22.

**Why.** The maintainer's reason is that this *unifies the messages and alerts*: the package gets one way to render
an alert instead of six hand-written copies. Theming improves as a result, though it isn't the goal. A theme
restyles every alert by overriding one frame template. Today crud_views_tabler overrides `tags/messages.html` and
`protection_errors.html`, and the related-objects alerts stay plain Bootstrap under Tabler because nobody wanted to
copy a third one. The colour words (`ALERT_CLASSES` in `lib/messages.py`, and `alert-danger` / `alert-warning`
written into the snippets) and the list markup with its spacing classes can't be reached today without copying
templates.

This change adds a tag, three small templates and five class keys. That is more upstream surface than the
maintainer usually accepts for a theme hook (see #240 and #242, both closed). It is accepted here because the
unification itself is the goal.

## Goals

- One frame template, `crud_views/tags/alert.html`, renders every alert in the package (all five apps).
- A theme changes three things independently: the frame (one template), the list body (one template) and the
  colours (`alert:*` class keys).
- `{% cv_messages %}` keeps its escaping guarantees and its fallback of unknown or missing levels to `info`.
  The behaviours `tests/test1/test_messages.py` pins stay the same in substance (assertions on the dict shape
  change; see Tests).
- Stock output for messages is unchanged. Stock output for the delete and guardian alerts changes only in ways
  the CHANGELOG lists.

## Non-goals

- The structure of `related_objects_tree.html`. It is already its own snippet, and it stays the body of one
  alert unchanged.
- Which alerts the delete page shows and in which order. That is page logic and stays in
  `view_delete.content.html`, `protection_errors.html` and `related_objects.html`, which keep their names and
  now call `{% cv_alert %}`.
- The `.cv-related-objects mb-3` wrapper around the delete alerts, and the `<h4>Guardian Configuration</h4>`
  above the guardian table. Neither is an alert.
- Updating crud_views_tabler in this change. It is a separate repo, and its follow-up is described under "What
  a theme overrides afterwards".
- Backwards-compatible message dict keys. The maintainer chose a clean break on 2026-10-22 (see "Breaking
  change").
- Any setting, or a new check ID. An unknown `alert:*` key in a theme layer or in `CRUD_VIEWS_BUTTON_CLASSES`
  already gets the existing "unknown key" warning.

## Anti-goals

- A frame that branches on the body type. The body template is chosen once, in Python, and the frame only
  `{% include %}`s it, so a theme's frame cannot pick the wrong body.
- A second colour vocabulary. `level` is the same five words as the `message-*` icon names.
- A theme that has to override `messages.html`. After this change it is a logic-only loop, like the button
  templates that hold only logic.

## Design

### Data: `alert_data()`

The helper lives in `crud_views/lib/messages.py` next to `message_alerts()`, which already turns a message into
alert data.

```python
LEVELS: dict[int, str] = {
    constants.DEBUG: "debug",
    constants.INFO: "info",
    constants.SUCCESS: "success",
    constants.WARNING: "warning",
    constants.ERROR: "error",
}


def alert_data(level, *, heading="", text="", items=None, body_template=None, dismissible=False, extra_tags=""):
    ...
    return {
        "level": level,                    # error | warning | success | info | debug; anything else -> "info"
        "icon_name": f"message-{level}",
        "heading": ...,                    # conditional_escape'd; "" when falsy
        "text": ...,                       # conditional_escape'd; "" when falsy
        "items": [...],                    # each conditional_escape'd (str() first for model instances)
        "body_template": body_template,    # default: list body when items, else text body
        "dismissible": dismissible,
        "extra_tags": ...,                 # escape'd
    }
```

- `ALERT_CLASSES` and `ICON_NAMES` are removed. `LEVELS` replaces them, and the icon name is derived from the
  level.
- `message_alerts()` stays and keeps its docstring guarantees, now built on `alert_data`:
  `[alert_data(LEVELS[level], text=body, dismissible=True, extra_tags=...) for message in messages]`. The
  falsy-body-to-`""` rule and the unknown-level-to-`info` rule stay where they are.
- Escaping: `heading`, `text` and every item are escaped in Python with `conditional_escape`, so a
  `SafeString` passes through untouched. `extra_tags` goes through `escape`. This is the same rule
  `message_alerts()` follows today, applied to every field, so an alert renders the same under
  `{% autoescape off %}`.
- Default body templates: `crud_views/snippets/alert/list.html` when `items` is non-empty, otherwise
  `crud_views/snippets/alert/text.html`.

### Tags

- `{% cv_messages %}` stays an inclusion tag on `tags/messages.html` and returns
  `{"cv_message_alerts": message_alerts(...)}`. Only the template changes.
- New `{% cv_alert level heading=… text=… items=… body_template=… dismissible=… extra_tags=… %}` renders one
  alert, for use in templates. It is a `simple_tag(takes_context=True)` that renders
  `f"{theme_path}/tags/alert.html"` with `alert` **pushed onto the caller's context**, not into a fresh one.
  The body template therefore sees the caller's variables: `related_objects_tree.html` reads `items`, and the
  guardian body reads `guardian_config`. Translated headings use the normal template-argument syntax
  `heading=_("…")`.

### Templates

```
crud_views/tags/alert.html            the frame: box, icon, heading, close button; {% include alert.body_template %}
crud_views/snippets/alert/text.html   {{ alert.text }}
crud_views/snippets/alert/list.html   <ul class="mb-0 mt-2">{% for item in alert.items %}<li>{{ item }}</li>…</ul>
crud_views/tags/messages.html         {% for alert in cv_message_alerts %}{% include "crud_views/tags/alert.html" %}{% endfor %}
```

The stock frame, in outline:

```django
<div class="{% cv_button_class "alert" alert.level %}{% if alert.dismissible %} alert-dismissible fade show{% endif %}{% if alert.extra_tags %} {{ alert.extra_tags }}{% endif %}"
     role="alert">
    {% cv_icon alert.icon_name "me-2" %}{% if alert.heading %}<strong>{{ alert.heading }}</strong>{% endif %}{% include alert.body_template %}
    {% if alert.dismissible %}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>{% endif %}
</div>
```

`alert-dismissible fade show` and `btn-close` / `data-bs-dismiss` stay in the frame as literal Bootstrap markup.
They control how the alert behaves rather than how it looks, the same line #227 drew for the dropdown hooks. A
theme on another framework overrides the frame.

### Colours: `alert:*` class keys

Five rows join `DEFAULT_BUTTON_CLASSES`, and the table grows from 46 to 51 keys:

| Key | Default |
|---|---|
| `alert:error` | `alert alert-danger` |
| `alert:warning` | `alert alert-warning` |
| `alert:success` | `alert alert-success` |
| `alert:info` | `alert alert-info` |
| `alert:debug` | `alert alert-secondary` |

The frame reads them with `{% cv_button_class "alert" alert.level %}`. The keys are plain two-segment keys like
`card:root`, so `LOCATIONS` doesn't change.

### The callers

```django
{# snippets/delete/protection_errors.html #}
{% cv_alert "error" heading=_("This object cannot be deleted:") items=delete_protection_errors %}

{# snippets/delete/related_objects.html, inside the existing .cv-related-objects wrapper and its ifs #}
{% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") items=protected_objects %}
{% cv_alert "warning" heading=_("The following related objects will also be deleted:") items=related_summary_items %}
{% with items=related_objects %}
{% cv_alert "warning" heading=_("Details about the related objects to be deleted:") body_template="crud_views/snippets/delete/related_objects_tree.html" %}
{% endwith %}

{# crud_views_guardian view_guardian_manage.html #}
{% cv_alert "warning" body_template="<guardian config table snippet>" %}
```

- `related_summary_items` is the summary as ready strings (`"Book: 3"`), built in `DeleteView.get_context_data`
  next to `related_summary`. `related_summary` stays in the context, because templates that projects already
  override may read it.
- The guardian config `<table>` moves unchanged into its own snippet in the guardian app's templates directory.
  The builder picks the name, for example `crud_views/snippets/guardian/config_table.html`.
- The translated heading strings keep their exact msgids, so the German `.po` entries still apply. Only the
  `#:` source references move.

### Output changes (stock theme)

- Messages: unchanged (whitespace aside).
- Delete and guardian alerts gain `role="alert"` and the level's `message-*` icon (`message-error` /
  `message-warning`) before the heading.
- The summary list items render as `Book: 3`, as before, but now come from a Python string instead of
  `{{ model_name }}: {{ count }}`.

All of these go in the CHANGELOG, and `tests/test1/golden/form_frame/delete_protection.html` is regenerated.

### Breaking change

The message dicts drop `css_class` and `message`, and `level` and `text` replace them. Any template override of
`tags/messages.html` that reads the old keys renders `class="alert alert-"` with an empty body, and nothing
raises an error. That includes crud_views_tabler today: it requires `django-crud-views>=0.30.0` with no upper
bound, and its override reads both keys.

The maintainer chose a clean break (2026-10-22): no compatibility keys and no deprecation period. The CHANGELOG
entry is marked **Breaking** and tells readers to replace a `messages.html` override with a `tags/alert.html`
override. The crud_views_tabler follow-up ships with the release that carries this change.

## What a theme overrides afterwards

- **crud_views_tabler:** `tags/alert.html` only. Its frame puts the icon in `.alert-icon` and the heading in
  `<h4 class="alert-heading">`, and wraps the body in `.alert-description`, so the stock `list.html` can stay.
  Its `tags/messages.html` and `snippets/delete/protection_errors.html` overrides are deleted (two overrides
  become one), and the related-objects and guardian alerts pick up the Tabler layout with no override. This is
  a follow-up in that repo.
- **A theme without `ul/li`:** also overrides `snippets/alert/list.html`, and every list alert follows it.
- **A theme with other colour classes:** registers `alert:*` keys and needs no template.

## Tests

- `test_messages.py`: assertions on `alert["css_class"]` become assertions on `alert["level"]` and the rendered
  class. The level mapping, the info fallback, extra tags, safe/unsafe bodies, the falsy body and the
  autoescape-off case all stay.
- `alert_data` unit tests: default body choice, escaping of heading/text/items, model-instance items, the
  unknown level falling back to info.
- `{% cv_alert %}`: renders through the frame. The body template sees the caller's context. A theme override of
  `tags/alert.html`, of `snippets/alert/list.html`, or an `alert:*` key each takes effect on its own (the issue's
  "independently" criterion).
- Delete page: protection, protected, summary and tree alerts all render through the frame, and the
  summary items come out as `"Model: n"`.
- `test_form_frame.py::test_protection_alert_overridable_on_its_own` keeps passing as written:
  `protection_errors.html` stays an overridable file.
- Guardian manage page renders the config table inside the frame.
- A guard test: no shipped template outside `tags/alert.html` and `snippets/alert/` contains `class="alert`,
  across all five apps' template directories.
- The button-class table count test moves from 46 to 51.

## Docs

- `docs/reference/messages.md`: the levels table shows `alert:*` keys instead of classes. Adds a section on
  `{% cv_alert %}` and `alert_data`.
- `docs/reference/theme.md`: the three templates (frame, text body, list body), the `alert:*` keys, and an
  update to the delete-alert paragraph.
- `docs/reference/delete_view.md`: the template list mentions `related_summary_items` and the alert frame.
- The button class keys reference lists the five new keys.
- `CHANGELOG.md`: the feature; a **Breaking** entry for the renamed message dict keys and for
  `ALERT_CLASSES`/`ICON_NAMES` being removed, with the migration note; and the output changes above.

## Calls made in this design (not the maintainer's)

- `alert_data` lives in `lib/messages.py`, not in a new `lib/alerts.py`.
- `{% cv_alert %}` pushes onto the caller's context, so body templates see the caller's variables. The
  related-objects tree gets its `items` from a `{% with %}` around the tag.
- The delete and guardian alerts gain `role="alert"` and the level icon; the frame doesn't make either optional.
- The behaviour hooks (`alert-dismissible fade show`, `btn-close`, `data-bs-dismiss`) stay as literals in the
  frame and get no class keys.
- `related_summary` stays in the delete context next to the new `related_summary_items`.
- The guardian table moves into its own body snippet.

## Left to the builder

- Whitespace and line breaks in the new templates, as long as message output stays equivalent under the
  existing normalising tests.
- The guardian snippet's file name.
- Whether `alert_data` takes a level that is already known, or validates it with the same info fallback (either
  satisfies the goals).
