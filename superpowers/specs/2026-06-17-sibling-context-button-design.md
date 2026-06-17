# `SiblingContextButton` — design

**Date:** 2026-06-17
**Status:** approved (pending user review of this spec)

## Goal

Add a new context button type that lets a **child** view link sideways to a **sibling**
collection — another child of the same parent — reusing the parent PK already present in the
current URL.

Example: parent `Author` has children `Book` and `Article`. On a Book page at
`/author/<author_pk>/book/…`, an **"Articles"** button links to
`/author/<author_pk>/article/` — the sibling collection under the same author.

It is a composition of the two existing relationship buttons: it resolves the parent like
`ParentContextButton`, then hops down to a named sibling child like `ChildContextButton`.

## Naming

`SiblingContextButton`, with `sibling_name` / `sibling_key`. The existing button names
describe the **target relationship** (`ParentContextButton` → parent, `ChildContextButton`
→ child); the target here is a sibling, so `Sibling` slots into that family unambiguously.
Rejected: `ParentChildContextButton` (names the mechanism, collides conceptually with
`ChildContextButton`) and `SiblingChildContextButton` (redundant — a sibling is already a
child of the parent).

## Current state (for context)

- `ContextButton` (`src/crud_views/lib/view/buttons.py`) is the base; it carries `key`,
  label fields, and (as of the context-button-templating work) `template` / `template_code`
  plus `_inject_template`.
- `ParentContextButton.get_context`: returns `dict()` when the view has no parent; else
  resolves `parent = context.view.cv_viewset.parent`, builds the parent URL from the current
  view's kwargs via `get_parent_url_args()`, and checks access on the parent view class.
- `ChildContextButton.get_context`: takes `child_name` / `child_key`, resolves the child
  viewset from the registry, and builds the child URL using the **current object** as the
  parent PK (`cv_get_child_url`). Returns `dict()` when there is no object.
- `ViewSet.get_parent_url_args()` walks the parent chain returning the ordered list of parent
  PK URL-arg names (e.g. `["author_pk"]`). A child and its siblings share the same parent
  chain, so their parent URL args are identical.
- `ViewSet.get_router_name(key)` yields the URL name (with the `list`→`card` fallback);
  `_resolve_container_key` performs the same `list`→`card` fallback for a target key.
- Buttons are exported from `crud_views.lib.view` (`ContextButton`, `ParentContextButton`,
  `ChildContextButton`).

## Design

### Class

`SiblingContextButton(ContextButton)` — subclasses `ContextButton` directly (not
`ChildContextButton`, whose URL building uses the current object rather than URL kwargs).

```python
class SiblingContextButton(ContextButton):
    sibling_name: str            # registry name of the sibling viewset (same parent)
    sibling_key: str = "list"    # target view key in the sibling viewset
```

Usage contrast:

```python
ChildContextButton(key="books", child_name="book")              # on the PARENT view → down to a child
SiblingContextButton(key="articles", sibling_name="article")    # on a CHILD view → sideways to a sibling
```

### `get_context` mechanics

1. **Child-only guard.** `if not context.view.cv_viewset.parent: return dict()` — no parent
   means no button (this is what restricts the button to child views), mirroring
   `ParentContextButton`.
2. **Resolve the sibling viewset:** `sibling_vs = context.view.cv_viewset.get_viewset(self.sibling_name)`
   (the global registry, as `ChildContextButton` does).
3. **Resolve the target key/class:**
   `sibling_key = self._resolve_container_key(sibling_vs, self.sibling_key)`,
   `cls = sibling_vs.get_view_class(sibling_key)`.
4. **Build the URL from the current view's kwargs.** The sibling shares the current view's
   parent chain, so:
   ```python
   kwargs = {arg: context.view.kwargs[arg] for arg in sibling_vs.get_parent_url_args()}
   cv_url = reverse(sibling_vs.get_router_name(sibling_key), kwargs=kwargs)
   ```
5. **Icon:** `cv_icon_action = sibling_vs.icon_header` (mirrors `ChildContextButton`).
6. **Access / visibility** via the sibling view class, with no object (the target is a
   collection):
   ```python
   dict_kwargs = dict(cv_access=False, cv_url=cv_url, cv_icon_action=sibling_vs.icon_header)
   dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, None)
   if cls.cv_has_access(context.view.request.user, None):
       dict_kwargs.update(cv_access=True)
   ```
7. **Assemble + label + template:** `data = cls.cv_get_dict(context=context, **dict_kwargs)`,
   then render the label (`render_label`) and inject the button template
   (`self._inject_template(data)`), then `return data` — identical tail to
   `ChildContextButton`.

### Access semantics (documented limitation)

Access is checked with `obj=None` (model-level on the sibling view). Object-level / Guardian
permissions keyed on the parent object are **not** consulted — the parent object is not
loaded on the child view, only its PK is in the URL. This matches the practical behavior of
the other relationship buttons and is noted in the docs; no extra work is built for it
(YAGNI).

### Errors / edges

- No parent on the current view → empty result, no button.
- Unknown `sibling_name` → `ViewSetNotFoundError` propagates, consistent with
  `ChildContextButton`; at the template-tag layer this is governed by `CRUD_VIEWS_STRICT`
  (raised in strict mode, logged otherwise).
- No new Django system check.

### Exports

Add `SiblingContextButton` to `crud_views.lib.view` next to the other button types.

## Deliverables beyond the core class

### Example app (bootstrap5)

`examples/bootstrap5` currently has single-child chains (`Author → Book → BookReview`,
`Foo → Bar → Baz`, `Group → Person`). To demonstrate siblings, give one existing parent a
**second** child collection so two siblings exist, then place a `SiblingContextButton` on
each sibling's list view linking to the other. The implementation plan picks the concrete
parent + new sibling model (smallest viable: a second child model under `Author` or under
`Book`, with its viewset, templates wiring, and a migration). The demo's `cv_context_actions`
includes the sibling button key so it renders in the running app.

### Documentation

- `docs/reference/context_buttons.md`: add a `SiblingContextButton` section (parameter table
  for `key` / `sibling_name` / `sibling_key` / label + template fields, the child-only
  behavior, the access limitation, and an Author→Book/Article example).
- `docs/faq.md`: add a short FAQ entry — "How do I link from one child collection to a
  sibling collection?" — showing `SiblingContextButton` on the child view.

### Inline skill (`skills/django-crud-views`)

- `SKILL.md`: add a `SiblingContextButton` subsection after the `ChildContextButton` section
  (~line 226), with the usage contrast (parent → `ChildContextButton`, child →
  `SiblingContextButton`) and a minimal example.
- `references/api-reference.md`: add `SiblingContextButton` to the context-button catalog
  (~line 308) and to the import line.

## Testing (tests/test1)

- Add a **second child** viewset under an existing parent in the test app (a sibling of
  `cv_book` under `cv_publisher`, or a second child under another parent), so a parent with
  ≥2 children exists. Reuse an existing model with a parent FK if available; otherwise add a
  minimal test model.
- Tests:
  - On a sibling's list/detail view, `SiblingContextButton` renders a URL pointing at the
    other sibling's collection, carrying the parent PK taken from the current URL kwargs.
  - The button is hidden (`cv_access` not `True`) when the user lacks access to the sibling.
  - The button renders nothing (`dict()`) when placed on a parent (no-parent) view.
  - Unknown `sibling_name` surfaces an error (or empty under non-strict), matching
    `ChildContextButton` behavior.

## Backwards compatibility

Purely additive: a new button class and exports. No change to existing buttons, viewsets, or
templates.
