# Context Button Parent-Object Access — Design

## Problem

A `ParentContextButton` that targets an **object-permission-gated parent view**
(e.g. the parent's `detail`) disappears on an **object-less** child page (a list or
card view) — even for a user who is allowed to view that parent. The built-in
`parent` button works only because it targets the parent's `list` view, whose access
check is unconditionally `True`.

Reproduction (child viewset under Guardian):

```python
context_buttons=context_buttons_default() + [
    ParentContextButton(key="projekt_detail", key_target="detail"),  # → parent DETAIL
]
```

```django
{% cv_context_button "parent" %}          {# works — targets parent LIST #}
{% cv_context_button "projekt_detail" %}  {# always "no access" — targets parent DETAIL #}
```

This is the second instance of the family fixed in
[0003 — Context Button Create Access](../instructions/0003-context-button-create-access.md)
(shipped in PR #48): a context button's access is checked **without the object the
access depends on**.

## Root cause

`ParentContextButton.get_context()` (`src/crud_views/lib/view/buttons.py`) checks
access against the **current view's object**:

```python
dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, context.object)
if cls.cv_has_access(context.view.request.user, context.object):
    dict_kwargs.update(cv_access=True)
```

A `ParentContextButton` links **up** to the parent's view, so access is governed by
the **parent object** — not `context.object`, which is the child instance (or `None`
on a list page). The check is therefore conceptually wrong; it only ever "worked"
because the default `parent` button targets the parent `list` view, whose
`cv_has_access` returns `True` regardless of the object passed
(`GuardianQuerysetMixin`). The moment the button targets an object-gated parent view
(`GuardianObjectPermissionMixin.cv_has_access(user, None) → False`), it collapses to
denied, and `_render_context_button()`
(`src/crud_views/templatetags/crud_views.py`) renders `""` for any button whose
`cv_access is not True`.

The parent **PK** is already read from `context.view.kwargs` to build the button's
URL, but the parent **instance** is never loaded for the access check — even though
the framework has a core helper for exactly that:
`CrudView.cv_get_parent_object()` (`src/crud_views/lib/view/base.py`), which loads
the immediate parent via `get_object_or_404(parent_model, pk=...)`.

## Approach (chosen)

Targeted fix (Approach A), consistent with the merged 0003 (#48). Correct the check
to use the object it should always have used — the parent instance — entirely within
core `crud_views`.

In `ParentContextButton.get_context()`, replace the two `context.object` checks with:

```python
# the button links UP to the parent, so access is governed by the PARENT object —
# not context.object (the child instance, or None on a list page).
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

`Http404` is imported from `django.http`. `cv_get_parent_object()` is the existing
core helper.

### Why this is correct and safe

- **No Guardian-side change.** `GuardianObjectPermissionMixin.cv_has_access(user,
  parent_obj)` already performs the right per-object check when given the parent
  instance. Unlike 0003 (which lived in the Guardian list mixin), this fix is purely
  in core `crud_views` and benefits every theme and permission backend uniformly.
- **Default `parent`→list button unchanged.** The parent list view's `cv_has_access`
  returns `True` regardless of object, so passing `parent_obj` instead of `None`
  changes nothing there. One uniform path; no `key_target` special-casing.
- **Graceful degradation.** An unresolvable parent PK in kwargs makes
  `cv_get_parent_object()` raise `Http404`; it is caught → `parent_obj = None` → an
  object-gated parent view denies → the button is hidden, no exception raised.
- **One extra DB query** per parent-button render (`get_object_or_404`). Acceptable;
  cache on the view if it ever shows up in profiling.

## Non-goals

- **`SiblingContextButton` is deliberately unchanged — it is collection-only, with no
  governing object.** A `SiblingContextButton` navigates to a *sibling collection*
  (another child of the same parent) and has no specific sibling object in scope. The
  shared parent does not identify a sibling instance, so there is no sensible object
  to check an object-gated sibling *view* against — which is also why such a button
  only meaningfully targets `list`/`card` (access `True`). Passing `None` is correct
  for sibling buttons. This corrects the "sibling → shared parent" assumption in the
  0003 Approach-B TODO and in the parent-object instruction; see the documentation
  changes below.
- **The unified `cv_button_has_access` hook (Approach B) stays deferred.** This is the
  second instance of the family, which strengthens the eventual case for B, but B's
  blast radius (core button rendering for all button types, a parallel
  `cv_action_enabled` hook, a compat shim for downstream `cv_has_access` overrides)
  is not warranted yet.

## Documentation changes

- `src/crud_views/lib/view/buttons.py` — add a clarifying line to
  `SiblingContextButton`'s docstring: it links to a sibling *collection*;
  object-gated sibling views are unsupported because no sibling object is in scope.
- `superpowers/instructions/0004-context-button-access-create-TODO.md` — add a
  correction under the sibling bullet recording that `SiblingContextButton` is **not**
  a "resolve the shared parent" case; the unified hook must do no object resolution
  for sibling buttons. Only create (→ parent) and parent-detail (→ parent) need a
  resolved object.

## Tests

In `tests/test1/`, using the real Publisher→Book Guardian fixtures (Book is a child
of Publisher) and the existing `_make_book_list_view` harness in `test_guardian.py`:

- Add `ParentContextButton(key="publisher_detail", key_target="detail")` to
  `cv_guardian_book`. On the book **list** page (`obj=None`):
  - user **with** object `view` permission on the publisher → `publisher_detail`
    button visible (`cv_access is True`),
  - user **without** it → `publisher_detail` hidden (`cv_access is False`).
- Regression: the default `parent` button (→ publisher list) stays visible
  (`cv_access is True`) in **both** cases.
- Unresolvable parent (bad/missing PK in kwargs) → `publisher_detail` hidden
  (`cv_access is False`), no exception raised.

## Relevant source

- `src/crud_views/lib/view/buttons.py` — `ParentContextButton.get_context()` (the
  method changed); `SiblingContextButton` (docstring clarified, behavior unchanged).
- `src/crud_views/lib/view/base.py` — `cv_get_parent_object()` (core helper to load
  the parent instance).
- `src/crud_views_guardian/lib/mixins.py` — `GuardianObjectPermissionMixin.cv_has_access`
  (`obj is None → False`; correct per-object check when given the parent instance)
  vs. `GuardianQuerysetMixin.cv_has_access` (always `True`, why the default
  parent→list button works).
- `src/crud_views/templatetags/crud_views.py` — `_render_context_button()` (renders
  `""` when `cv_access is not True`).
