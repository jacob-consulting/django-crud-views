# Context Button Parent-Object Access

A `ParentContextButton` that targets an **object-permission-gated parent view** (e.g. the
parent's `detail`) is rendered as "no access" (the button disappears) on an **object-less**
page such as a child list view — even when the user is allowed to view that parent. The
built-in `parent` button works, because it targets the parent's `list` view, whose access
check is unconditionally `True`. Pointing the button at the parent `detail` exposes the bug.

This is the same family of problem as
[0003 — Context Button Create Access](0003-context-button-create-access.md): a context
button's access is checked **without the object that access depends on**.

Example that reproduces it (a child viewset under Guardian):

```python
cv_projekt_note = GuardianViewSet(
    model=ProjektNote,
    name="projekt_note",
    parent=ParentViewSet(name="projekt"),
    context_buttons=context_buttons_default() + [
        # links up to the PARENT's detail view (object-permission gated)
        ParentContextButton(key="projekt_detail", key_target="detail",
                            label_template_code="Projektbeschreibung"),
        ...
    ],
)
```

```django
{% cv_context_button "parent" %}          {# works — targets parent LIST #}
{% cv_context_button "projekt_detail" %}  {# always "no access" — targets parent DETAIL #}
```

On the note list page (`/.../projekt/<pid>/note/`) the `projekt_detail` button renders nothing,
even for a user who is a member/Verwalter of the projekt and can open its detail page directly.

## Why it happens

`ParentContextButton.get_context()` (`crud_views/lib/view/buttons.py`, ~line 110) checks access
against the **current view's object**:

```python
# resolves the parent PK for the URL ...
kwargs = {... context.view.kwargs[arg] ...}
cv_url = reverse(router_name, kwargs=kwargs)
...
# ... but checks access with context.object, not the parent object
if cls.cv_has_access(context.view.request.user, context.object):
    dict_kwargs.update(cv_access=True)
```

On a list page `context.object` is `None` (list views have no object — `cv_object = False`).
For an object-permission-gated parent view (Guardian `GuardianObjectPermissionMixin`),
`cv_has_access(user, None)` returns `False` (`crud_views_guardian/lib/mixins.py`, the
`if obj is not None: ... return False` branch). Then `_render_context_button()`
(`crud_views/templatetags/crud_views.py`, ~line 34) returns `""` for any button whose
`cv_access is not True`, so the button disappears.

The parent **PK** is already resolved from `context.view.kwargs` to build the URL, but the
parent **object instance** is never loaded for the access check — even though the framework
has a core helper for exactly that: `CrudView.cv_get_parent_object()`
(`crud_views/lib/view/base.py`, ~line 411), which loads the immediate parent via
`get_object_or_404(parent_model, pk=...)`.

The default `parent` button avoids the bug only because the parent `list` view's
`cv_has_access` is hard-coded `True` (`GuardianQuerysetMixin`). Any `ParentContextButton`
pointing at an object-gated parent view hits the denial.

## What it should do

`{% cv_context_button "projekt_detail" %}` (parent → detail) must reflect whether the user can
access the **parent object** — visible for a user who can view the parent, hidden otherwise —
the same way opening the parent detail page directly is governed by the parent object's
permission.

## Ideas

- **Preferred (small, targeted):** in `ParentContextButton.get_context()`, resolve the parent
  object and check access against it. The current view already carries the parent PK in its
  kwargs:

  ```python
  parent_obj = None
  if hasattr(context.view, "cv_get_parent_object"):
      try:
          parent_obj = context.view.cv_get_parent_object()
      except (Http404, KeyError):
          parent_obj = None
  dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, parent_obj)
  if cls.cv_has_access(context.view.request.user, parent_obj):
      dict_kwargs.update(cv_access=True)
  ```

  Note: `cv_get_parent_object()` runs a DB query (`get_object_or_404`) — one extra lookup per
  parent button render. Acceptable; cache on the view if it shows up.

- **`SiblingContextButton` has the analogous gap.** It checks `cv_has_access(user, None)`
  (`buttons.py`, ~line 191). For `sibling_key="list"` that's fine (list access is `True`), but a
  sibling button pointing at an object-gated sibling view would be wrongly hidden. The governing
  object there is the **shared parent**, also reachable via `cv_get_parent_object()`. Fix it the
  same way if/when sibling buttons target object-gated views.

- **Longer-term (cleaner) — the unified hook from 0003.** Add
  `CrudView.cv_button_has_access(user, rendering_view, obj)` (default → `cv_has_access(user,
  obj)`). Each target view that needs a specific object (create → parent; parent-detail →
  parent; sibling → parent) overrides it and resolves that object from `rendering_view`. Then
  `ContextButton`, `ParentContextButton`, `SiblingContextButton`, and the "key is a view" branch
  in `base.py` all call the one hook, and the per-button-type access logic plus the Guardian
  list-mixin special case collapse into a single, consistent path. This is the recommended
  end-state for the whole context-button access family (0003 + this).

- **Avoid:** restricting parent buttons to `key_target="list"` by convention — it blocks a
  legitimate, common case (a tab/button that jumps to the parent's detail page).

## Tests

In `tests/test1/`, using the Author→Book Guardian fixtures (book is a child of author):

- Add `ParentContextButton(key="author_detail", key_target="detail")` to the book viewset.
  On the book **list** page assert:
  - a user **with** object `view` permission on the author → button visible,
  - a user **without** it → button hidden.
- Regression: the default `parent` button (→ author list) stays visible in both cases.
- Parent object unresolvable from URL kwargs → button hidden, no exception raised.

## Relevant source

- `crud_views/lib/view/buttons.py` — `ParentContextButton.get_context()` (checks
  `cv_has_access(user, context.object)`); `SiblingContextButton.get_context()` (same gap).
- `crud_views/lib/view/base.py` — `cv_get_parent_object()` (core helper to load the parent
  instance).
- `crud_views_guardian/lib/mixins.py` — `GuardianObjectPermissionMixin.cv_has_access`
  (`obj is None → False`) vs. `GuardianQuerysetMixin.cv_has_access` (always `True`, why the
  default parent→list button works).
- `crud_views/templatetags/crud_views.py` — `_render_context_button()` (renders `""` when
  `cv_access is not True`).
