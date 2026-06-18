# Context Button Parent Label

A `ParentContextButton` **ignores its own `label_template_code` / `label_template`**. The
button renders with the *target* (parent) view's default action label instead of the label the
caller asked for. Its siblings — `ContextButton`, `ChildContextButton`, `SiblingContextButton` —
all honor these fields, so a button declared the same way reads differently depending only on its
class.

This is independent of the access bug in
[0004 — Context Button Parent-Object Access](0004-context-button-parent-object-access.md)
(fixed in `140f281`): even when the parent button is correctly *visible*, its *text* is wrong.

Example that reproduces it (a child viewset under Guardian):

```python
cv_projekt_note = GuardianViewSet(
    model=ProjektNote,
    name="projekt_note",
    parent=ParentViewSet(name="projekt"),
    context_buttons=context_buttons_default() + [
        ParentContextButton(key="projekt_detail", key_target="detail",
                            label_template_code="Projektbeschreibung"),
        ...
    ],
)
```

On the note list page (`/.../projekt/<pid>/note/`) the button renders as
**"Projekt »None« anzeigen."** — the parent `detail` view's default
`cv_action_label_template_code` rendered with `object = None` (no object is in scope on the child
list page) — instead of the requested **"Projektbeschreibung"**.

## Why it happens

In `crud_views/lib/view/buttons.py`, every other button type renders the label explicitly after
building `data`:

```python
# ContextButton.get_context (~line 64), ChildContextButton (~161), SiblingContextButton (~210)
data = cls.cv_get_dict(context=context, **dict_kwargs)
cv_action_label = self.render_label(data, context)   # <-- applies label_template_code/label_template
if cv_action_label:
    data["cv_action_label"] = cv_action_label
self._inject_template(data)
```

`ParentContextButton.get_context()` (~line 125) omits that block:

```python
data = cls.cv_get_dict(context=context, **dict_kwargs)
self._inject_template(data)          # <-- no render_label() call
return data
```

`cls.cv_get_dict()` already seeds `data["cv_action_label"]` with the *target view's* label
(`base.py:196`, `cv_action_label=cls.cv_get_action_label(...)`). Because
`ParentContextButton` never overwrites it, the caller's `label_template_code` is silently
dropped. `render_label()` itself is inherited from `ContextButton` and works fine — it is simply
never called on this path.

## What it should do

`ParentContextButton(label_template_code="Projektbeschreibung")` must render with that label, the
same as `ContextButton` / `ChildContextButton` / `SiblingContextButton` do. When neither
`label_template` nor `label_template_code` is set, fall back to the target view's default label
(current behavior) — `render_label()` returns `None` in that case, so the existing
`if cv_action_label:` guard preserves the fallback.

## Ideas

- **Preferred (small, targeted):** add the same three lines the sibling classes already use to
  `ParentContextButton.get_context()`, just before `self._inject_template(data)`:

  ```python
  data = cls.cv_get_dict(context=context, **dict_kwargs)
  cv_action_label = self.render_label(data, context)
  if cv_action_label:
      data["cv_action_label"] = cv_action_label
  self._inject_template(data)
  return data
  ```

- **Longer-term (cleaner):** the label-rendering block is now duplicated verbatim in four
  `get_context()` methods. Lift it into a small `ContextButton` helper (e.g.
  `_apply_label(data, context)`) and call it from each, so a new button type can't forget it.
  The `ParentContextButton` omission is exactly the failure mode that duplication invites.

## Tests

In `tests/test1/`, using the Author→Book Guardian fixtures (book is a child of author):

- Add `ParentContextButton(key="author_detail", key_target="detail",
  label_template_code="Author Home")` to the book viewset. On the book **list** page, assert the
  rendered button text is `Author Home` (not the author detail view's default label).
- Regression: a `ParentContextButton` with **no** label field still renders the target view's
  default label.
- Cross-check (already passing): `ContextButton`, `ChildContextButton`, and
  `SiblingContextButton` with the same `label_template_code` render that text — `ParentContextButton`
  must match them.

## Relevant source

- `crud_views/lib/view/buttons.py` — `ParentContextButton.get_context()` (missing the
  `render_label()` call); `ContextButton` (~line 64), `ChildContextButton` (~line 161),
  `SiblingContextButton` (~line 210) for the pattern it should follow; `ContextButton.render_label()`
  (~line 28, inherited, works).
- `crud_views/lib/view/base.py` — `cv_get_dict()` / `cv_get_action_label()` (~line 196) seed the
  default `cv_action_label` that the parent button wrongly keeps.
