# Design: Dynamic Cancel Button Target (origin key in the link)

## Problem

`CrudView.cv_cancel_key` (default `"list"`) names the sibling view the cancel button returns to.
It is a class attribute, so the target is fixed per view. The user's navigation path cannot influence
it:

```
list view   -> update -> cancel -> list view     (works today)
detail view -> update -> cancel -> detail view   (impossible today: cancel goes to the list)
```

The cancel URL has one producer, `CrudView.get_cancel_button_context()`
(`src/crud_views/lib/view/base.py:448`), which calls `cv_get_url(key=self.cv_cancel_key, obj=obj)`.
It has two consumers:

- `CrispyFormMixin.get_cancel_button_kwargs()` (`src/crud_views/lib/crispy/form.py:64`) bakes the URL
  into `data-cv-cancel-url`; `static/crud_views/js/viewset.js:24` navigates on click.
- The `{% cv_cancel_button %}` tag (`src/crud_views/templatetags/crud_views.py:181`) renders
  `tags/button_cancel.html` with `href="{{ cv_url }}"`.

Nothing in the request tells the form view where the user came from.

## Solution

The view the user came from (the *origin*) is carried as a query parameter on the generated sibling
link. The parameter holds a **view key** (`list`, `detail`, ...), never a URL, so there is no open
redirect surface. The form view validates the key against an explicit per-view allow-list,
`cv_cancel_keys`, and uses it as the cancel target. Everything else falls back to `cv_cancel_key`.

The feature is opt-in per target view. With `cv_cancel_keys` unset (the default) no link changes and
the cancel URL is byte-identical to today.

```python
class AuthorUpdateView(CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    cv_cancel_keys = ["list", "detail"]   # dynamic targets; cv_cancel_key = "list" stays the fallback
```

Rendered links (only into views that declare `cv_cancel_keys`):

```
/author/<pk>/update/?cv_from=detail     from the detail page
/author/<pk>/update/?cv_from=list       from the list page
```

Three alternatives were evaluated (query-string key, session-stored last origin, HTTP Referer). The
query-string key was chosen because it is stateless, deterministic across tabs, reloads and
bookmarks, testable from a single request, and correct on validation re-render without extra form
fields.

## Changes

### 1. Setting — `src/crud_views/lib/settings.py`

```python
# cancel button
cancel_origin_param: str = from_settings("CRUD_VIEWS_CANCEL_ORIGIN_PARAM", default="cv_from")
```

`check_messages` gains check **`crud_views.E103`**: the name must match the existing key regex
`REGS["name"]` in `src/crud_views/lib/check.py:14` (`^[a-z][a-z0-9_]*$`). This rejects whitespace,
dashes, uppercase, and every character a query string would need to encode. The check is idempotent
like the existing ones (`tests/test1/test_settings_checks.py` asserts idempotence).

### 2. Core API — `src/crud_views/lib/view/base.py`

New class attribute next to `cv_cancel_key` (line 66):

```python
cv_cancel_key: str | None = "list"        # unchanged: static fallback
cv_cancel_keys: list[str] | None = None   # origin keys the cancel button may return to; None = static
```

New methods:

```python
def cv_get_origin_key(self) -> str | None:
    """The sibling view the user came from, as sent by the origin link; None when absent/invalid."""
    value = self.request.GET.get(crud_views_settings.cancel_origin_param)
    if not value or not check.REGS["name"]["reg"].match(value):
        return None
    return value

def cv_get_cancel_key(self, obj=None) -> str | None:
    """The key the cancel button returns to: a validated origin, else cv_cancel_key."""
    if obj is None:
        obj = getattr(self, "object", None)
    if not self.cv_cancel_keys:
        return self.cv_cancel_key
    origin = self.cv_get_origin_key()
    if origin not in self.cv_cancel_keys:
        return self.cv_cancel_key
    try:
        cls = self.cv_viewset.get_view_class(origin)   # keeps the list -> card fallback
    except ViewSetKeyFoundError:
        return self.cv_cancel_key
    if cls.cv_object and obj is None:                   # a create view cannot return to "detail"
        return self.cv_cancel_key
    return origin

def cv_get_link_url(self, cls, key: str, obj=None) -> str:
    """URL of a sibling link; carries this view's key when the target resolves cancel dynamically."""
    url = self.cv_get_url(key=key, obj=obj)          # reverse() only, never has a query string
    if cls.cv_cancel_keys and self.cv_key in cls.cv_cancel_keys:
        url += "?" + urlencode({crud_views_settings.cancel_origin_param: self.cv_key})
    return url
```

`get_cancel_button_context()` changes one line:

```python
url = self.cv_get_url(key=self.cv_get_cancel_key(obj), obj=obj)
```

`cv_get_url()` is untouched, so `get_success_url()` and every other caller stay clean.

The `obj` default in `cv_get_cancel_key()` exists so templates can call the method without
arguments: `{% cv_context_url view.cv_get_cancel_key as url %}` (Django calls zero-argument
callables). This is what downstream code needs, see "Downstream adoption".

The object guard mirrors `cv_get_cls_assert_object()` (`base.py:299`), which raises when a target
requires an object and none is given. A `CustomFormNoObjectView` or `CreateView` therefore can only
return to non-object origins such as `list`.

Per-view system check **`E252`** (`CheckExpression`, next to E250/E251 in `checks()`): every entry
of `cv_cancel_keys` is registered on the ViewSet (`cv_viewset.is_view_registered(key)`, with
`"list"` also accepted when only `"card"` is registered, matching `get_view_class()`). Checks run
after all views are registered, as `CheckBreadcrumbKeyObject` already relies on.

`cv_cancel_keys` is a declared class attribute, so `CheckUnknownAttributes` (W280) is unaffected.
`cv_get_dict()` (`base.py:259`) adds `"cv_cancel_keys": cls.cv_cancel_keys` next to
`"cv_cancel_key"`, and `manage.py:109` lists it in the manage view's attribute table.

### 3. Link emission — three sites

All sibling links are built in exactly three places. Each switches from `cv_get_url()` to
`cv_get_link_url()`:

| Site | Today | Change |
|---|---|---|
| `CrudView.cv_get_context()` (`base.py:426`) | `"cv_url": self.cv_get_url(key=key, obj=obj)` | `self.cv_get_link_url(cls, key, obj)`; `cls` is resolved two lines earlier |
| `ContextButton.get_context()` (`src/crud_views/lib/view/buttons.py:54`) | `context.view.cv_get_url(key=key_target, obj=context.object)` | move the `cls` lookup (line 57) above the URL line, then `context.view.cv_get_link_url(cls, key_target, context.object)` |
| `cv_card_action` tag (`src/crud_views/templatetags/crud_views.py:329`) | `view.cv_get_url(action.key, obj=obj)` | `view.cv_get_link_url(cls, action.key, obj)`; `cls` is already resolved above |

Not changed, by design: `ParentContextButton`, `ChildContextButton`, `SiblingContextButton`, and
`cv_get_child_url()` link across ViewSets. An origin is always a sibling in the same ViewSet.
The `FilterContextButton` links to the list itself.

Consumers inherit automatically:

- `GuardianQuerysetMixin.cv_get_context()` (`src/crud_views_guardian/lib/mixins.py:112`) calls
  `super()` and only patches `cv_access`.
- `{% cv_context_url %}`, `{% cv_context_button %}`, `cv_get_context_buttons()` and the
  `{% cv_list_action %}` / `{% cv_context_action %}` tags all read `ctx["cv_url"]`.
- Theme overrides of `tags/list_action.html`, `tags/context_action.html`, `tags/card_action.html`
  render `href="{{ cv_url }}"` and need no change.

### 4. Survival across validation bounces — four templates

The origin must survive every re-render after an invalid POST. The re-render happens inside the
same request (`CrudViewProcessFormMixin.cv_form_invalid()`, `src/crud_views/lib/views/mixins.py:71`,
and `DeleteView.post()` delete-protection re-check, `delete.py:165`), and Django fills `request.GET`
from the query string on POST requests too. The only thing that drops the query string is the form
`action`. All four content templates post to `{{ request.path }}`; each becomes
`{{ request.get_full_path }}`:

- `src/crud_views/templates/crud_views/view_create.content.html:3`
- `src/crud_views/templates/crud_views/view_update.content.html:3`
- `src/crud_views/templates/crud_views/view_delete.content.html:17`
- `src/crud_views/templates/crud_views/view_custom_form.content.html:3` (used by both
  `CustomFormView` and `CustomFormNoObjectView`, `src/crud_views/lib/views/form.py:19,51`)

Modal mode needs nothing extra: `cvModalSubmit()` in `static/crud_views/js/modal.js` posts to the
form's `action` attribute and injects the 422 response back into the modal, so the re-rendered
cancel button keeps its target. The modal GET fetches the link's `href`, which already carries the
parameter.

Guarantee stated by this spec: the origin survives every validation bounce on create, update,
delete confirm (including delete protection), custom form, and custom form without object, in
full-page and modal mode.

### 5. Tests — `tests/test1/test_cancel_origin.py` (new) and existing files

Style: request the page through the test client, then assert on `response.context["view"]` and on
rendered HTML, as `tests/test1/test_context_url_tag.py` does.

Test views: a dedicated ViewSet in `tests/test1/app/views.py`, following the existing pattern of
several ViewSets over one model (`author_wide_card`, `author_modal`, `publisher_bc`):

- `cv_author_origin = ViewSet(model=Author, name="author_origin")` with list (table), card, detail,
  create, update, delete, a custom form view (`cv_key = "contact"`), and a no-object custom form
  view. Update, delete, and both custom form views declare `cv_cancel_keys = ["list", "detail"]`;
  the create view declares `cv_cancel_keys = ["list", "detail"]` to exercise the object guard.
  One ViewSet-level `ContextButton(key="edit", key_target="update")` is added to its
  `context_buttons`.
- `cv_guardian_author_origin = GuardianViewSet(model=Author, name="guardian_author_origin")` with
  detail and update (`cv_cancel_keys = ["detail"]`).

The existing Author, Publisher and Guardian views are not touched, so no existing test's exact URL
expectations change. Twenty-three existing test files compare update or delete URLs exactly.

Backward compatibility:

- A view without `cv_cancel_keys`: links from list and detail carry no parameter; cancel URL equals
  the `cv_cancel_key` URL. Run against the existing Publisher views (int PK) to also cover
  non-UUID PKs.

Link emission:

- Detail page: the update and delete links carry `?cv_from=detail`; the detail link does not
  (target has no `cv_cancel_keys`).
- List page: row action links to update carry `?cv_from=list`.
- Card list page: the update card action carries `?cv_from=card`.
- A ViewSet-level `ContextButton` (`key_target="update"`) carries the parameter.

Resolution:

- Update page opened with `?cv_from=detail`: cancel URL is the detail URL (crispy path,
  `data-cv-cancel-url`, and the `{% cv_cancel_button %}` tag path, `href`).
- `?cv_from=list`: cancel URL is the list URL.
- Value not in `cv_cancel_keys`, unregistered key, regex-invalid values (`" detail"`,
  `"de-tail"`, `"Detail"`, `"a/b"`, empty): all fall back to `cv_cancel_key`.
- Create view with `cv_cancel_keys=["list", "detail"]` and `?cv_from=detail`: falls back
  (no object); with `?cv_from=list`: list.
- `CustomFormNoObjectView` with `?cv_from=detail`: falls back.
- `cv_get_cancel_key()` called without `obj` uses `self.object`.

Validation bounces (one per view type, all with `?cv_from=detail` and an invalid POST):

- Update, create (with `?cv_from=list`), delete confirm (confirm unchecked), delete protection
  error re-render, custom form, custom form without object (with `?cv_from=list`). Each asserts the
  response is 200, the re-rendered form action equals `request.get_full_path()`, and the cancel URL
  still points at the origin.
- Modal delete: POST with `X-CV-Modal: true` and an invalid form returns 422 and the partial still
  carries the origin cancel URL (extend `tests/test1/test_modal.py`).

Configuration:

- `CRUD_VIEWS_CANCEL_ORIGIN_PARAM = "origin"` via `override_settings` plus a fresh
  `CrudViewsSettings()` instance: links carry `?origin=detail` and resolution honors it.
- `tests/test1/test_settings_checks.py`: `CrudViewsSettings(cancel_origin_param="bad param")`
  yields exactly one `crud_views.E103`; valid names yield none.
- `tests/test1/test_check_messages.py` (or the existing check test for E250/E251): a view with
  `cv_cancel_keys=["nope"]` yields `E252`; `["list"]` on a card-only ViewSet does not.

Guardian:

- One test in `tests/test1/test_guardian.py`: a Guardian update view with `cv_cancel_keys` resolves
  the detail origin.

### 6. Docs

- `docs/reference/settings.md`: new "Cancel button" table with `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`
  (type `str`, default `cv_from`, check `crud_views.E103`).
- `docs/reference/update_view.md`: configuration table gains `cv_cancel_key` (missing today) and
  `cv_cancel_keys` rows; new section "Dynamic cancel target" with the example, the link format, the
  fallback rules, and the validation-bounce guarantee. The example code block is marked
  `<!-- cv-sync: library/views.py -->` so `examples/bootstrap5/test_docs_sync.py` enforces it.
- `docs/reference/create_view.md`, `delete_view.md`, `custom_form_view.md`: configuration tables
  gain the two rows and a one-line pointer to the update view section.
- `docs/reference/card-list-view.md:198`: mention that card actions carry the origin too.
- `CHANGELOG.md` under "Unreleased": Added (attribute, setting, checks E103/E252), Changed (form
  templates post to `get_full_path`).

### 7. Examples project — `examples/bootstrap5/library`

- `AuthorUpdateView` and `AuthorDeleteView` in `library/views.py` get
  `cv_cancel_keys = ["list", "detail"]` (this is the block the docs sync marker points at).
- `project/features.py`: the `library` entry's `look_at` text mentions `cv_cancel_keys`.
- `library/tests.py`: two tests, cancel from the detail origin returns to detail, cancel from the
  list origin returns to the list.

### 8. Skill — sibling repo `~/projects/alex/skills`, `plugins/django-crud-views/skills/django-crud-views/`

- `SKILL.md`: new section "Cancel button target" after the CardListView "List Key Fallback" note
  (line 228): the attribute, the example, the setting, and the two checks, marked
  "Available since 0.21.0".
- `references/api-reference.md`: `cv_cancel_key` / `cv_cancel_keys` in the CrudView attribute
  table, `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` in the settings table, E103/E252 in the checks list.
- `CHANGELOG.md`: entry under "Unreleased".
- Verification: rerun the executable drift audit (import resolution, `__all__` coverage,
  `CRUD_VIEWS_*` names against `CrudViewsSettings`) so the new setting name is proven to exist.
- Commit directly to `main` and push with `git -C /home/alex/projects/alex/skills ...` in one
  invocation; verify `HEAD == origin/main` afterwards.

## Behavior summary

| Situation | Cancel target |
|---|---|
| `cv_cancel_keys` unset | `cv_cancel_key` (unchanged) |
| Origin present, in `cv_cancel_keys`, registered, object requirement met | origin |
| Origin absent | `cv_cancel_key` |
| Origin not in `cv_cancel_keys` | `cv_cancel_key` |
| Origin fails the key regex | `cv_cancel_key` |
| Origin unregistered on the ViewSet | `cv_cancel_key` |
| Origin needs an object, view has none (create, no-object custom form) | `cv_cancel_key` |
| `"list"` origin on a card-only ViewSet | card view (existing fallback) |

Links gain the parameter only when the **target** view declares `cv_cancel_keys` and the
**current** view's key is listed in it. Links to views without `cv_cancel_keys` are unchanged.

## Downstream adoption (themes and custom form mixins)

Verified against a third-party theme built on this package: nothing breaks when the package is
upgraded. A theme is unaffected as long as its link templates render `href="{{ cv_url }}"` from the
package context, its custom `ContextButton` subclasses call `super().get_context()`, and its own
form templates either post without an `action` attribute or include the package's content
templates.

Custom form mixins that build the cancel link themselves, by reading `view.cv_cancel_key` and
calling `cv_get_url()` directly instead of `get_cancel_button_context()`, keep working but do not
see dynamic targets. To adopt them, such code switches to `view.cv_get_cancel_key()` (with a
`getattr` fallback where test fakes define only `cv_cancel_key`). Templates that use
`{% cv_context_url view.cv_cancel_key %}` switch to `{% cv_context_url view.cv_get_cancel_key %}`.
This is why `cv_get_cancel_key()` defaults `obj` to the view's object: Django templates call
zero-argument methods, so no new template tag is needed.

## Out of scope

- A dynamic `cv_success_key` ("detail, edit, save, back to detail"). The same resolver pattern
  applies; it is a separate change.
- Session- or Referer-based origin detection (rejected alternatives).
- Changes to downstream projects.
