# Context button templating & manual placement — design

**Date:** 2026-06-17
**Status:** approved (pending user review of this spec)

## Goal

Today, context buttons are defined once on a `ViewSet` (`context_buttons`) and rendered
only through the automatic `{% cv_context_actions %}` container loop, which iterates a
view's `cv_context_actions` keys. The button's *rendering template* is fixed — a button's
shape can't differ between views (e.g. the `edit` button should look different in the
detail view than elsewhere), and there's no way to place a single button by hand in a
custom layout.

This design adds three capabilities, all additive (the default container keeps working
unchanged):

1. **Per-button templating** — a `ContextButton` carries its own render template
   (`template` / `template_code`), defaulting to a project-wide setting. Different
   shapes are achieved by defining variant buttons in the viewset registry (e.g. an
   `edit` button and an `edit_detail` button with a different template).
2. **Manual placement** — a by-key tag and a custom-loop API so buttons can be dropped
   anywhere in a template instead of only through the container loop.
3. **Permission gating** — a filter to ask, in a template, whether the user may access a
   given key, so surrounding markup (wrappers, headings, separators) can be conditional.

The "different shape in the detail view" requirement is met by combining these: define a
variant button in the viewset, trim `cv_context_actions`, and place the variant manually
in the detail template.

## Non-goals

- **View-level button instances** (issue #27 — allowing `cv_context_actions` to contain
  `ContextButton` instances, not just string keys). Considered and dropped: with registry
  buttons templated and placeable by key, the user can keep `cv_context_actions` minimal
  and place buttons manually, so view-level instances add surface area without new
  capability here. The issue stays open for a future need.
- **Changing the default container's no-access rendering.** The container keeps rendering
  inaccessible buttons as *disabled/greyed*; existing themes depend on it. The new by-key
  tag uses a *hide-on-no-access* contract instead. This divergence is deliberate (see
  §"Two render contracts").

## Current state (for context)

- `ContextButton` (`src/crud_views/lib/view/buttons.py`) is a Pydantic model with
  `key`, `key_target`, `label_template`, `label_template_code`. Subclasses:
  `ParentContextButton`, `ChildContextButton`, `FilterContextButton`.
- `ContextButton.get_context(context)` resolves the target view class, sets `cv_access`
  (permission) and `cv_action_enabled` (contextual visibility), builds the data dict via
  `cls.cv_get_dict(...)`, and renders the label.
- `FilterContextButton.get_context` already hardcodes
  `data["cv_template"] = f"{theme_path}/tags/context_action_filter.html"` (`buttons.py:176`)
  — proof that a per-button template via `cv_template` already flows through the renderer.
- `ViewSet.context_buttons` (`viewset/__init__.py:79`) holds the registry; default set is
  `home`, `parent` (`ParentContextButton`), `filter` (`FilterContextButton`).
- A view declares `cv_context_actions: List[str]` — ordered keys rendered top-right. Each
  key is resolved by `CrudView.cv_get_context` (`view/base.py:305`): if it matches a
  registry button (`cv_get_context_button`, `base.py:289`) that button's context is used;
  otherwise the key is treated as a plain *view key* (nav button).
- Template tag `cv_context_action` (`templatetags/crud_views.py:67`) renders one key:
  `template = ctx.get("cv_template", f"{theme_path}/tags/context_action.html")` then
  `render_to_string(template, ctx)`. The hardcoded fallback is the default template.
- Container tag `cv_context_actions` (`crud_views.py:74`, template `tags/context_actions.html`)
  loops `view.cv_context_actions` and emits `{% cv_context_action key object %}` for each.
- `tags/context_action.html` renders a disabled/greyed button when `cv_access is False`
  and nothing when `cv_action_enabled is False`.
- `CrudView.render_snippet(data, template=None, template_code=None)` (`base.py:131`) is the
  existing primitive that renders either a file template or an inline template string — the
  render path this design reuses.
- Themes: `crud_views` (Bootstrap 5) and `crud_views_plain`. Both ship the
  `tags/context_action*.html` templates.

## Design

### 1. Templating on `ContextButton` (foundation)

Add to the **base** `ContextButton` (inherited by all subclasses):

```python
template: str | None = None        # file template path for the whole button
template_code: str | None = None   # inline template source for the whole button
```

These name the **button** template (the full anchor/markup), distinct from the existing
`label_template` / `label_template_code`, which render only the label text inside it.

`get_context()` injects the chosen template into the returned data dict, with this
precedence:

1. `self.template_code` set → `data["cv_template_code"] = self.template_code`
2. else `self.template` set → `data["cv_template"] = self.template`
3. else → `data["cv_template"] = crud_views_settings.context_button_template`
   (the new default; see §Settings)

`FilterContextButton` drops its hardcoded `data["cv_template"] = …` and instead sets its
field default `template = f"{theme_path}/tags/context_action_filter.html"` (resolved from
settings at construction, consistent with how the class already references `theme_path`).

### 2. Settings change

- New setting `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE`, default
  `f"{theme_path}/tags/context_action.html"` (the current hardcoded fallback), exposed as
  `crud_views_settings.context_button_template`.
- The **view-key branch** of `cv_get_context` (`base.py:321+`, the non-button path) also
  sets `cv_template` to this default. With both branches injecting a template, every
  rendered action carries one.
- `cv_context_action` (the container's per-key tag) drops its hardcoded fallback string;
  the default now lives once in settings (always injected, see above). It also learns to
  honour `cv_template_code`: if `ctx.get("cv_template_code")` is set it renders inline via
  `view.render_snippet(ctx, template_code=...)`, otherwise it renders the file template
  `ctx["cv_template"]`. **Note** it keeps its existing disabled-on-no-access behavior — it
  does *not* adopt the hide contract; only the new manual API hides (see §"Two render
  contracts").

### 3. By-key placement tag — `cv_context_button`

New `simple_tag(takes_context=True)`:

```django
{% cv_context_button "edit_detail" %}
{% cv_context_button "edit_detail" object %}
```

Behavior:
- Resolve the key the same way the container does: `view.cv_get_context(key=key, obj=obj)`
  (which finds a registry button or a view key).
- Render-or-nothing per the **hide-on-no-access** contract: emit `""` when the resolved
  context indicates the button is absent / `cv_action_enabled is False` / `cv_access is
  not True`. Otherwise render the button via its template (see §4).
- Wrapped with the existing `@ignore_exception(ViewSetKeyFoundError, default_value="")`
  guard, matching `cv_context_action`, so an unknown key is silently empty.

This is the core of the originally-sketched `cv_context_button(key)` tag.

### 4. Render rules (shared helper)

Both `cv_context_button` and the loop render the same way. A small module helper in the
template-tags module:

```python
def _render_context_button(view, ctx) -> str:
    if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
        return ""   # hide-on-no-access contract
    if ctx.get("cv_template_code"):
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    return view.render_snippet(ctx, template=ctx["cv_template"])
```

Reuses `render_snippet` (already supports both file and inline). `cv_template_code` wins
over `cv_template` when both are present.

### 5. Custom-loop API

Accessor on `CrudView`:

```python
def cv_get_context_buttons(self, keys: list[str] | None = None, obj=None) -> list[dict]:
    """Resolved, access-filtered button contexts. keys defaults to cv_context_actions."""
```

- For each key, resolve via `cv_get_context`; **filter out** entries that fail the
  hide-on-no-access contract (so a custom loop never produces empty wrapper markup).
- Each returned dict carries its `cv_template` / `cv_template_code`.

Companion tag to render an already-resolved entry (avoids re-resolving inside the loop):

```django
{% for ctx in view.cv_get_context_buttons %}
  <div class="my-wrap">{% cv_render_context_button ctx %}</div>
{% endfor %}
```

`cv_render_context_button` is a `simple_tag(takes_context=True)` that calls
`_render_context_button(view, ctx)`.

### 6. Permission-check filter — `cv_context_has_permission`

Django filters can't access the template context, so the **view** is the piped value and
the key is the argument, enabling direct use in `{% if %}`:

```django
{% if view|cv_context_has_permission:"edit_detail" %}
  <h3>Edit</h3>
  {% cv_context_button "edit_detail" %}
{% endif %}
```

Implementation: resolve `cls = view.cv_viewset.get_view_class(key)` and return
`cls.cv_has_access(view.request.user, view.object)` (object defaults to the view's current
object; `None` for list-type views). Wraps the same `cv_has_access` gate the buttons use.
Returns `False` on unknown key rather than raising.

## Two render contracts (deliberate)

| Placement | No access | No `cv_action_enabled` |
|---|---|---|
| `{% cv_context_actions %}` container (default, unchanged) | disabled/greyed button | hidden |
| `{% cv_context_button %}` / loop / filter (new) | hidden | hidden |

You reach for the manual API precisely when you want the hide behavior. The container is
left untouched so existing themes don't break.

## Themes

Both `crud_views` and `crud_views_plain` are unaffected at the template level for the new
tags — `cv_context_button` / `cv_render_context_button` reuse each button's own template
(default = the theme's existing `tags/context_action.html`). No new theme template files
are required by the core design; projects supply custom button templates as needed. The
`context_button_template` setting resolves per active theme via `theme_path`.

## Public API summary

- `ContextButton.template`, `ContextButton.template_code` (new fields, all subclasses).
- Setting `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` / `crud_views_settings.context_button_template`.
- `CrudView.cv_get_context_buttons(keys=None, obj=None) -> list[dict]`.
- Template tags: `{% cv_context_button key obj %}`, `{% cv_render_context_button ctx %}`.
- Template filter: `view|cv_context_has_permission:"key"`.

## Backwards compatibility

- `cv_context_actions` semantics, the container tag, and `cv_context_action` rendering are
  unchanged for existing keys (the settings default reproduces the old hardcoded template).
- `FilterContextButton` output is unchanged (its default `template` equals the path it
  used to hardcode).
- All additions are opt-in; existing viewsets/views/templates render identically.

## Testing (tests/test1)

- `ContextButton.template` / `template_code` flow into `cv_template` / `cv_template_code`
  with correct precedence and the settings default fallback.
- `cv_context_button`: renders an accessible button; renders `""` for no-access, disabled
  (`cv_action_enabled False`), and unknown key.
- `cv_get_context_buttons`: returns only accessible entries, in `cv_context_actions` order
  by default and in an explicit `keys` order when given.
- `cv_render_context_button`: renders a pre-resolved ctx via file template and via
  `template_code`.
- `cv_context_has_permission`: `True` / `False` against a permitted vs. forbidden user
  (reuse existing permission-based client fixtures); `False` on unknown key.
- `FilterContextButton` still renders via the filter template (regression).
- Default container behavior unchanged (regression).
