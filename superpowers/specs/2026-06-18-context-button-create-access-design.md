# Context Button Create Access — Design

## Problem

A custom `ContextButton` that targets a child viewset's `create` view renders as
"no access" (hidden/disabled) on a list page — even for a user who is allowed to
create — whenever its `key` differs from its `key_target`. The built-in `"create"`
button works for the same user on the same page, because its key happens to equal
the view key.

Reproduction (child viewset, create gated by Guardian):

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

The viewset config is correct — this is a gap in how Guardian create-access is
resolved for context buttons.

## Root cause

For a child create on a list page, `obj is None`, so
`GuardianCreateView.cv_has_access(user, None)` returns `False` by design
(`crud_views_guardian/lib/views.py`, "Case 2"). The real per-object decision needs
the parent object and is delegated to `cv_create_has_access(user, rendering_view,
parent_obj)`.

That delegation lives in exactly one place: `GuardianQuerysetMixin.cv_get_context()`
(`crud_views_guardian/lib/mixins.py`). It re-derives `cv_access` and
`cv_action_enabled` after `super().cv_get_context()` has built the button dict — but
it looks the target view up by the **literal `key`** passed to the tag:

```python
if obj is None and key is not None and self.cv_viewset.has_parent:
    if self.cv_viewset.is_view_registered(key):   # keyed on `key`, not key_target
        target_cls = self.cv_viewset.get_view_class(key)
    ...
        ctx["cv_access"] = target_cls.cv_create_has_access(user, self, parent_obj)
        ctx["cv_action_enabled"] = target_cls.cv_action_enabled(user, parent_obj)
```

Both buttons reach the same override, but:

- `key="create"` is **not** a registered context button, so `super()` takes the
  "key is a view" branch; the override then sees `is_view_registered("create")` is
  true and re-derives access. → works.
- `key="create_button"` **is** a registered context button, so `super()` returns
  `ContextButton.get_context()`, whose only access check is `cls.cv_has_access(user,
  None)` → `False`. The override then skips it, because
  `is_view_registered("create_button")` is false. → always denied.

So the re-derivation keys off the button **`key`** instead of the button's
**`key_target`**.

Note: a create button on a *parent/child detail page* already works today, because
there `obj` is the parent instance and `GuardianCreateView.cv_has_access` "Case 3"
performs the per-object check directly. The gap is specific to **list pages** where
`obj is None`.

## Approach (chosen)

Resolve the button's `key_target` before the target-view lookup in
`GuardianQuerysetMixin.cv_get_context()`.

```python
if obj is None and key is not None and self.cv_viewset.has_parent:
    context_button = self.cv_get_context_button(key)
    target_key = context_button.key_target if context_button and context_button.key_target else key
    if self.cv_viewset.is_view_registered(target_key):
        target_cls = self.cv_viewset.get_view_class(target_key)
    else:
        target_cls = None
    # unchanged below: cv_permission == "add" guard, parent resolution,
    # and the cv_access / cv_action_enabled overwrite
```

Everything downstream is unchanged. `super().cv_get_context()` has already built the
dict with the correct URL, label, and template against the create view class; the
override overwrites only the two access fields (`cv_access`, `cv_action_enabled`).
The result for `"create_button"` becomes identical to `"create"`.

### Why this is safe

- No change to core `crud_views`; no change to the `cv_has_access` contract; no
  downstream impact.
- Bare `key="create"` still works (`context_button` is `None` → `target_key = key`).
- Guarded by the existing `obj is None and self.cv_viewset.has_parent` condition.
- `cv_action_enabled` is already re-derived alongside `cv_access` in the existing
  override, so there is no separate enabled-state regression.

### Scope / limitation

Covers any `ContextButton` (or subclass) rendered through a view using the Guardian
list mixin whose `key_target` points at a child create. A create button on a
*non-list, no-object* view is not covered by this fix — but that case is currently
hypothetical (parent/child detail pages already work via Case 3). The broader,
uniform solution is captured separately as a future TODO (Approach B,
`superpowers/instructions/0004-context-button-access-create-TODO.md`).

## Tests

In `tests/test1/`, using the Author→Book Guardian fixtures (Book is a child
viewset). Add `ContextButton(key="create_button", key_target="create")` to the Book
viewset and assert, on the Book list page:

- `"create_button"` and the built-in `"create"` yield the **same** `cv_access` —
  both visible for a user with parent create permission, both hidden without it.
- `"create_button"` and `"create"` yield the **same** `cv_action_enabled`.
- Unresolvable parent → denied, no exception raised.
- Top-level (no-parent) create access is unchanged.

## Relevant source

- `crud_views_guardian/lib/mixins.py` — `GuardianQuerysetMixin.cv_get_context()`:
  the only create-access re-derivation (the single method changed).
- `crud_views/lib/view/base.py` — `cv_get_context()` / `cv_get_context_button()`:
  the context-button vs. "key is a view" branching.
- `crud_views/lib/view/buttons.py` — `ContextButton.get_context()`: generic access
  via `cv_has_access`, no create path.
- `crud_views_guardian/lib/views.py` — `GuardianCreateView.cv_has_access`
  (`obj is None → False`, Case 3 for parent obj) and `cv_create_has_access`.
- `crud_views/templatetags/crud_views.py` — `cv_context_button` →
  `view.cv_get_context`.
