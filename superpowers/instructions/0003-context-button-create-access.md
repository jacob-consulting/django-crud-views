# Context Button Create Access

A custom `ContextButton` that targets a child viewset's `create` view is rendered as
"no access" (hidden/disabled) — even for a user who is allowed to create — whenever its
`key` differs from its `key_target`. The built-in `"create"` button works for the same
user on the same page, because its key happens to equal the view key.

Example that reproduces it (a child viewset, create gated by Guardian):

```python
cv_projekt_note = GuardianViewSet(
    model=ProjektNote,
    name="projekt_note",
    parent=ParentViewSet(name="projekt"),
    context_buttons=context_buttons_default() + [
        ContextButton(key="create_button", key_target="create"),  # key != key_target
    ],
)
```

```django
{% cv_context_button "create" %}          {# works #}
{% cv_context_button "create_button" %}   {# always "no access" #}
```

The viewset config is correct — this is a gap in how Guardian create-access is resolved
for context buttons.

## Why it happens

For a child viewset, `GuardianCreateView.cv_has_access(user, obj)`
(`crud_views_guardian/lib/views.py`) returns `False` when `obj is None` — which is the
case on a list page, where a create button has no object. The real per-object decision
needs the parent object and is delegated to
`cv_create_has_access(user, rendering_view, parent_obj)`.

That delegation lives in exactly one place: the Guardian list mixin's `cv_get_context()`
override (`crud_views_guardian/lib/mixins.py`). It looks the target view up by the
**literal `key`** passed to the tag:

```python
if obj is None and key is not None and self.cv_viewset.has_parent:
    if self.cv_viewset.is_view_registered(key):          # keyed on `key`, not key_target
        target_cls = self.cv_viewset.get_view_class(key)
    ...
        ctx["cv_access"] = target_cls.cv_create_has_access(user, self, parent_obj)
```

Both buttons go through the same `view.cv_get_context(key=...)`, but:

- `key="create"` is **not** a registered context button, so `super()` takes the
  "key is a view" branch; the override then sees `is_view_registered("create")` is true
  and re-derives access via `cv_create_has_access(...)`. → works.
- `key="create_button"` **is** a registered context button, so `super()` returns
  `ContextButton.get_context()` (`crud_views/lib/view/buttons.py`), whose only access check
  is `cls.cv_has_access(user, None)` → `False` (it has no `cv_create_has_access` path).
  Then the override skips it, because `is_view_registered("create_button")` is false. →
  always denied.

So: the create-access re-derivation keys off the button **key** instead of the button's
**`key_target`**, and the generic `ContextButton.get_context()` has no create-access path
of its own. Any `ContextButton` whose key ≠ view key (more generally, any one targeting a
child `create` via `key_target`) never gets the parent-object check.

## What it should do

`{% cv_context_button "create_button" %}` must produce the same `cv_access` and
`cv_action_enabled` as `{% cv_context_button "create" %}` for the same user, page, and
parent object — without regressing top-level (no-parent) create buttons or non-create
buttons.

## Ideas

- **Preferred (small):** in `crud_views_guardian/lib/mixins.py`, resolve the button's
  `key_target` before the target-view lookup:

  ```python
  context_button = self.cv_get_context_button(key)
  target_key = context_button.key_target if context_button and context_button.key_target else key
  if self.cv_viewset.is_view_registered(target_key):
      target_cls = self.cv_viewset.get_view_class(target_key)
  else:
      target_cls = None
  ```

  Fixes the reported case and any `ContextButton` pointing at a child create via
  `key_target`. Stays Guardian-specific (correct — `cv_create_has_access` is a Guardian
  concept). Limitation: only covers buttons rendered through a view that uses the Guardian
  list mixin (i.e. list pages); a create button on a sibling/parent detail page would still
  not be covered.

- **Longer-term (cleaner):** give `CrudView` a single `cv_button_has_access(user,
  rendering_view, obj)` hook, defaulting to `cv_has_access(user, obj)`.
  `GuardianCreateView` overrides it to resolve the parent from `rendering_view` and call
  `cv_create_has_access(...)`. Then `ContextButton.get_context()` and the "key is a view"
  branch in `base.py` both call the hook, and the Guardian list-mixin special case can be
  deleted. Access for a button is then decided in one place, regardless of which view
  renders it. Bigger blast radius: touches core `crud_views` button rendering and the
  access-check contract, so it needs a compat shim for downstream `cv_has_access`
  overrides and a parent-resolution helper usable without the list mixin.

- **Avoid:** documenting "just reuse `key="create"`" as the only answer — it blocks
  legitimate cases such as a second, differently-styled create button on the same page,
  which is exactly what surfaced this.

## Tests

In `tests/test1/`, using the Author→Book Guardian fixtures (book is a child viewset):
add `ContextButton(key="create_button", key_target="create")` to the book viewset and
assert that on the book list page `"create_button"` and the built-in `"create"` yield the
same `cv_access` — both visible for a user with parent create permission, both hidden
without it — and the same `cv_action_enabled`. Also: unresolvable parent → denied, no
exception; top-level (no-parent) create access unchanged.

## Relevant source

- `crud_views/lib/view/buttons.py` — `ContextButton.get_context()`: generic access via
  `cv_has_access`, no create path.
- `crud_views/lib/view/base.py` — `cv_get_context()` / `cv_get_context_button()`: the
  context-button vs. "key is a view" branching.
- `crud_views_guardian/lib/mixins.py` — list-mixin `cv_get_context()` override: the only
  create-access re-derivation (currently keyed on `key`).
- `crud_views_guardian/lib/views.py` — `GuardianCreateView.cv_has_access` (`obj is None →
  False`) and `cv_create_has_access`.
- `crud_views/templatetags/crud_views.py` — `cv_context_button` → `view.cv_get_context`.
