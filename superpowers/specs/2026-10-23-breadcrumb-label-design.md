# Breadcrumb label separate from the view's short label

Issue: #271

Date: 2026-10-23

## Intent

A view's short label (`cv_action_short_label_template[_code]`) does two jobs: it is the visible text of every toolbar
button pointing to the view (#269 made the target view the source of a button's appearance), and it is the
current-page item of the breadcrumb (`CrudViewBreadcrumbMixin.cv_breadcrumb_get()`). The two often want different
wording: a button names the action from outside ("New note"), the breadcrumb names the page relative to its container
("Notes › Create"). Today a project either accepts "Notes › New note" or repeats a `ContextButton(label_template_code=…)`
on every ViewSet, which is what #269 set out to remove.

This adds an opt-in, breadcrumb-only label on the view. It exists only for the case where the breadcrumb wording
differs from the short label; when it is not set, the short label is used as today.

## Goals

- A view can set a breadcrumb label for its own current-page item, as a template snippet or template code, without
  changing the label of buttons pointing to it.
- Unset, every breadcrumb renders exactly as today.

## Non-goals

- Changing any built-in view's wording. No package view (Create, Update, Workflow, …) sets the new attributes; the
  defaults stay as they are (maintainer decision).
- Changing container, object or ancestor items. `cv_breadcrumb_container_label` and `cv_breadcrumb_object_label()`
  already cover those.
- Using the full label (`cv_action_label_template[_code]`) for the breadcrumb — it is a sentence for hidden text and
  `title`, too long for a breadcrumb.
- Updating the `django-crud-views` skill plugin; that follows the release as usual.

## Anti-goals

- Any change in breadcrumb output for a view that does not set the new attributes.
- A system check that fails views leaving the attributes unset.

## Design

### Attributes and method (`src/crud_views/lib/breadcrumb.py`)

On `CrudViewBreadcrumbMixin`, next to `cv_breadcrumb_container_label`:

```python
cv_breadcrumb_label_template: str | None = None  # template snippet for the current-page item
cv_breadcrumb_label_template_code: str | None = None  # template code for the current-page item
```

```python
@classmethod
def cv_get_breadcrumb_label(cls, context) -> str:
    """Current-page label; falls back to the short action label when no breadcrumb label is set."""
    if cls.cv_breadcrumb_label_template or cls.cv_breadcrumb_label_template_code:
        return cls.render_snippet(
            cls.cv_viewset.get_meta(context),
            cls.cv_breadcrumb_label_template,
            cls.cv_breadcrumb_label_template_code,
        )
    return cls.cv_get_action_short_label(context=context)
```

- Same render path and data as `cv_get_action_short_label()` (`src/crud_views/lib/view/base.py`): the flat names from
  `ViewSet.get_meta()` (`verbose_name`, `verbose_name_plural`, their `*_translate` variants, `viewset`, `cv`, and
  `object` when the view has one) are available, and the result is stripped and marked safe. The issue's
  `{{ cv_meta.verbose_name }}` is not a real name; there is no `cv_meta` namespace and none is added.
- If both are set, the code wins — `render_snippet()` already prefers `template_code`, matching every other
  `*_template[_code]` pair.
- A classmethod, like `cv_get_action_short_label()`, so it can be called without an instance.

### Use in `cv_breadcrumb_get()`

The three places that build the current view's own item call `self.cv_get_breadcrumb_label(context=context)` instead
of `self.cv_get_action_short_label(context=context)`:

1. object view with a detail view, not the detail view itself (action item linked, before the object item);
2. object view without a detail view (action item, unlinked object item follows);
3. non-object view that is not the container (e.g. create).

Nothing else in the trail changes. The detail view and the container view have no own action item, so the new
attributes have no effect there (documented).

### System check

Inside `CrudViewBreadcrumbMixin.checks()`, add
`CheckTemplate(context=cls, id="E111", attribute="cv_breadcrumb_label_template")` (`src/crud_views/lib/check.py`).
It errors only when a template is named and cannot be found; unset is fine. `CheckTemplateOrCode`, which the action
labels use, is wrong here: it errors when neither attribute is set.

The unknown-attribute check (W280) derives its known set from crud_views classes in the MRO, so declaring the
attributes on the mixin is enough; no registry change.

## Tests (`tests/test1/test_breadcrumb.py`)

Using the existing `PublisherBc*` views (`tests/test1/app/views.py`) and `make_view()`/`titles()` helpers, with new
test views or `type()`-built subclasses as the builder prefers:

- no breadcrumb label → trail unchanged (existing tests already cover this; keep them green);
- `cv_breadcrumb_label_template_code` set → used in each of the three branches (create, update with detail, update
  without detail);
- `cv_breadcrumb_label_template` set → rendered from a template (a test template under the test app's templates);
- template code can use the meta names (e.g. `{{ verbose_name }}`) and, on an object view, `{{ object }}`;
- both set → code wins;
- the view's short label (`cv_get_action_short_label`) is unchanged when a breadcrumb label is set, i.e. buttons are
  unaffected;
- detail view with a breadcrumb label → trail unchanged (no own action item);
- check: a missing `cv_breadcrumb_label_template` yields E111; unset yields no error.

## Docs and changelog

- `docs/reference/breadcrumb.md`: add the two attributes and `cv_get_breadcrumb_label()` to the members table, plus a
  short example:

  ```python
  class NoteCreateView(CrudViewBreadcrumbMixin, CreateView):
      cv_action_short_label_template_code = "New note"  # every button pointing here
      cv_breadcrumb_label_template_code = "Create"      # Notes › Create
  ```

  Note that it applies to the current-page item only, so it has no effect on detail and container views, and list
  the template variables (`verbose_name`, `verbose_name_plural`, `object`, …).
- `CHANGELOG.md`, `## Unreleased` → `### Added`: one entry referencing #271. Not breaking, so
  `docs/migrating-1.0.md` is untouched.

## Calls made while writing this up (not discussed with the maintainer)

- Template variables are the existing flat `get_meta()` names; no `cv_meta` namespace (the issue's example used one
  that does not exist).
- E111 via `CheckTemplate` instead of the action labels' `CheckTemplateOrCode`.
- Docs section and changelog entry included; the skill plugin is not part of this change.

## Left to the builder

- Exact test view names and whether to add them to `tests/test1/app/views.py` or build them in the test module.
- Wording of the docs paragraph and changelog entry.
