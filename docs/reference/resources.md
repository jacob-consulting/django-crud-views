# Resources — non-ORM data in ViewSets

`ViewSet` normally wraps a Django model. `Resource` lets it wrap anything
table-shaped that isn't backed by the database — S3 bucket listings, config
trees, results from an external API — and still get the same chrome: list and
detail pages, breadcrumbs, sibling-aware action buttons, and permission
checking.

## What and why

A `Resource` is a small Pydantic base class plus one view mixin
(`ResourceViewMixin`). It reuses every existing view class — there are no new
view types. The supported toolbox is:

- **List** — render rows in a table, with pagination.
- **Detail** — show a single row.
- **Custom-form actions** — a form-backed action on a row, e.g. delete-with-confirm.
- **Form-less actions** — a `POST`-triggered side effect with no form.

**Explicitly out of scope: create and update.** The moment a Resource needs
writable forms, the data has a home — model it as a real (possibly
`managed = False`) Django model and use the normal `CreateView`/`UpdateView`
instead. Resources are for rendering data that already lives somewhere else.

## Defining a Resource

Subclass `Resource` like a Pydantic model, with an inner `Meta` (same idiom as
Django's model `Meta`) and a `cv_get_items` classmethod that returns all rows:

```python
import hashlib

import django_tables2 as tables

from crud_views.lib.resource import Resource
from crud_views.lib.table import Table
from crud_views.lib.viewset import ViewSet


class S3File(Resource):
    key: str
    size: int

    class Meta:
        verbose_name = "s3 file"
        verbose_name_plural = "s3 files"
        app_label = "app"
        pk_field = "key_md5"
        pk_type = ViewSet.PK.HEX

    @property
    def key_md5(self) -> str:
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        # dev's S3 code goes here — read the whole bucket listing (or a
        # cached/paged-once copy of it) and return a plain list of instances
        return [cls.model_validate(row) for row in list_bucket()]


cv_s3file = ViewSet(
    model=S3File,
    name="s3file",
)
```

`pk_field`/`pk_type` are set here because S3 keys contain `/`, which no
default pk regex admits — see [Primary keys](#primary-keys-for-path-like-data)
below for the full explanation and an alternative (reversible) pattern.

`Meta` fields (all optional, with Django-model-like lowercase defaults):

| Attribute | Default | Purpose |
|---|---|---|
| `verbose_name` | `"item"` | Singular label (capitalized by the view layer) |
| `verbose_name_plural` | `"items"` | Plural label |
| `app_label` | `"resources"` | Session-data namespace (`SessionData.app_label`) |
| `pk_field` | `"pk"` | Name of the attribute (field **or property**) identifying a row |
| `pk_type` | `ViewSet.PK.STR` | URL pattern regex — see [Primary keys](#primary-keys-for-path-like-data) |
| `ordering` | `None` | Informational only; sort inside `cv_get_items` |

`cv_get_items(cls, request, **url_kwargs)` is the one hook every Resource
must implement — it must return a plain `list` (Django's `Paginator` needs
`len()` and slicing, which lists support and generators don't). `url_kwargs`
are the resolved URL kwargs of the requesting view; for a nested Resource
ViewSet they include the parent pk(s) (see [Nesting](#nesting)).

`cv_get_item(cls, request, pk, **url_kwargs)` resolves a single row by pk.
The default implementation does a linear scan over `cv_get_items()` comparing
`str(row.pk) == str(pk)` and raises `Http404` when nothing matches —
deliberately simple, and fine at "read the whole bucket in one call" scale.
Override it when a direct lookup is cheaper, e.g. an S3 `head_object` call
instead of listing everything.

## Primary keys for path-like data

S3 keys (and many other path-like identifiers) contain `/`, which no default
pk regex admits, so the raw `key` can't be used as the URL pk directly. Expose
a computed, URL-safe pk instead via `pk_field` (which may name a **property**,
not only a declared field) and pick one of two patterns:

### base64url (reversible)

```python
import base64

class S3File(Resource):
    key: str          # the real S3 key, shown in tables
    size: int

    class Meta:
        pk_field = "key_b64"
        pk_type = ViewSet.PK.STR   # r"[A-Za-z0-9_\-]+" — the base64url alphabet

    @property
    def key_b64(self) -> str:
        return base64.urlsafe_b64encode(self.key.encode()).decode().rstrip("=")
```

`PK.STR`'s regex doesn't include `=`, so strip the padding on encode and
restore it on decode:

```python
def decode_key_b64(s: str) -> str:
    padded = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(padded).decode()
```

Because the encoding is reversible, you can still override `cv_get_item` with
a direct lookup (decode the pk, then look the key up directly) instead of the
default linear scan.

### md5 hash (one-way, zero extra code)

```python
import hashlib

class S3File(Resource):
    key: str

    class Meta:
        pk_field = "key_md5"
        pk_type = ViewSet.PK.HEX   # r"[0-9a-z]+" — hexdigests fit, no padding games

    @property
    def key_md5(self) -> str:
        return hashlib.md5(self.key.encode()).hexdigest()
```

This works with **zero extra code**, because the default `cv_get_item` linear
scan compares computed pks directly — there's no decode step to implement.

**Trade-off:** the hash is one-way, so resolving a single object is
permanently list-and-match (no direct-lookup shortcut). The base64 pattern
keeps that option open. Neither matters at "read them all at once" scale;
pick whichever reads more naturally for your data. Collisions are negligible
for this use case; use `sha256(...)[:16]` instead if keys are user-supplied
and you want extra headroom. A minor downside of the hash approach: the URL
can't be hand-decoded when debugging.

## Permissions

Resource ViewSets never derive permissions from `ContentType` — there's no
model to look one up for. Permissions are **explicit**: pass a
`resource_permissions` mapping, or pass `None` and accept that only
non-`PermissionRequired` views are in play.

The documented pattern is an unmanaged **permission-holder model** that
exists only so Django creates the `ContentType`/`Permission` rows — no table,
no default `add`/`change`/`delete`/`view` permissions, only the custom ones
you declare:

```python
# app: storage
class S3FilePermissions(models.Model):
    class Meta:
        managed = False              # no table
        default_permissions = ()     # no add/change/delete/view auto-perms
        permissions = [
            ("view_s3file", "Can view S3 files"),
            ("delete_s3file", "Can delete S3 files"),
        ]
```

`managed = False` models still get migrations — `makemigrations` picks this
up, but the generated migration itself is a state-only `CreateModel` (no
table is created). The `ContentType`/`Permission` rows are created
separately by Django's `post_migrate` `create_permissions` signal handler,
which runs whenever `migrate` executes.

Wire it into the ViewSet:

```python
cv_s3file = ViewSet(
    model=S3File,
    name="s3file",
    resource_permissions={
        "view": "storage.view_s3file",
        "delete": "storage.delete_s3file",
    },
)
```

Keys are the short permission keys views reference via `cv_permission`
(`"view"`, `"change"`, `"delete"`, or a custom key); values are full
`app_label.codename` strings. They don't have to point at a dedicated
permission-holder model — any existing model's permissions work too.

`resource_permissions=None` means: no permissions declared. Use it only when
every view on the ViewSet is a plain (non-`PermissionRequired`) variant;
login-only protection is then the project's responsibility (middleware or a
login-required mixin), not the library's.

If you register a `*PermissionRequired` view whose `cv_permission` isn't a
key in `resource_permissions`, a startup system check (**E260**) fails with a
message telling you to add the key or switch to the non-permission view
variant — Resources never fail silently into "unprotected."

`resource_permissions` is only valid on Resource-backed ViewSets; setting it
on a model ViewSet raises at ViewSet construction time.

## Views

Add `ResourceViewMixin` **first** in the view's base classes, before any
crud_views view class — it overrides `get_queryset`/`get_object` so every
existing view class resolves rows through `cv_get_items`/`cv_get_item`
instead of the ORM:

```python
class S3FileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    ...
```

### List

```python
class S3FileTable(Table):
    key = tables.Column()
    size = tables.Column()


class S3FileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_s3file
    table_class = S3FileTable
    cv_list_actions = ["detail", "delete", "touch"]
```

Pagination and table rendering work unchanged — Django's `Paginator` and
django-tables2 both operate on plain lists.

### Detail

Resources use `DetailCustomView` (a fully custom template) rather than the
property-grid `DetailView`, since there's no model field metadata to
introspect:

```python
class S3FileDetailView(ResourceViewMixin, DetailCustomViewPermissionRequired):
    cv_viewset = cv_s3file
    template_name = "app/s3file_detail.html"
```

```html
{% extends cv_extends %}

{% block cv_content %}
<div class="s3file-detail">
    <h2>{{ object.key }}</h2>
    <p class="size">{{ object.size }}</p>
</div>
{% endblock cv_content %}
```

### Delete-with-confirm (custom-form action)

There is no `DeleteView` port for Resources — `CustomFormView` plus a
`cv_form_valid` hook **is** the delete story. Use the plain
`CrispyDeleteForm` so the user confirms in the browser (a checked checkbox is
required before the `POST` is accepted):

```python
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired


class S3FileDeleteView(ResourceViewMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    cv_key = "delete"
    cv_path = "delete"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    form_class = CrispyDeleteForm
    cv_icon_action = "fa-regular fa-trash-can"
    cv_action_label_template_code = "Delete"
    cv_action_short_label_template_code = "Delete"
    cv_message_template_code = "Deleted »{{ object }}«"
    cv_header_template_code = "Delete S3 file"
    cv_paragraph_template_code = "Confirm deletion of »{{ object }}«"

    def cv_form_valid(self, context):
        # the dev hook: this is where delete_object(Bucket=..., Key=obj.key) goes
        delete_from_bucket(self.object.key)
```

`cv_header_template_code`, `cv_paragraph_template_code`,
`cv_action_label_template_code` and `cv_action_short_label_template_code` are
ordinary `CrudView` attributes (not Resource-specific), but a custom-form
action view like this one has no other source for its header/action labels —
set them explicitly or a startup system check will flag the view. The same
applies to `cv_icon_action`: the generic `CustomFormView`/`ActionView` bases
declare no icon (unlike the built-in CRUD views), so set one or the action
button renders with its tooltip label only.

On success, the view redirects to `cv_success_key` (default `"list"`) — never
back to the just-deleted object's detail page.

### Form-less action

Use `ActionView` for a `POST`-triggered side effect that doesn't need a form:

```python
from crud_views.lib.views import ActionViewPermissionRequired


class S3FileTouchView(ResourceViewMixin, ActionViewPermissionRequired):
    cv_key = "touch"
    cv_path = "touch"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    cv_icon_action = "fa-regular fa-hand-pointer"
    cv_action_label_template_code = "Touch"
    cv_action_short_label_template_code = "Touch"
    cv_message_template_code = "Touched »{{ object }}«"
    cv_message_template_error_code = "Touch failed for »{{ object }}«"

    def action(self, context) -> bool:
        touch_object(self.object.key)
        return True
```

As with any `ActionView`, a truthy return emits the success message; a falsy
return emits the error message. See [ActionView](action_view.md) for the full
hook reference.

## Nesting

**Rule: models can sit anywhere in the hierarchy; Resources are leaves.** A
Resource ViewSet may be the *child* of one or more model ViewSets (any
depth). A Resource may **not** be a *parent* — of a model ViewSet or of
another Resource ViewSet.

A Resource child scoped to a model parent:

```python
class PublisherFile(Resource):
    key: str
    size: int = 0

    class Meta:
        verbose_name = "publisher file"
        verbose_name_plural = "publisher files"
        pk_field = "key_md5"
        pk_type = ViewSet.PK.HEX

    @property
    def key_md5(self) -> str:
        return hashlib.md5(self.key.encode()).hexdigest()

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        # THE nesting contract: the parent pk arrives as a URL kwarg
        # (named after ParentViewSet.get_pk_name(), e.g. "publisher_pk");
        # scoping the listing is the developer's job — there is no ORM
        # filter to fall back on.
        prefix = f"publisher-{url_kwargs['publisher_pk']}/"
        return [cls.model_validate(row) for row in list_bucket() if row["key"].startswith(prefix)]


cv_publisher_file = ViewSet(
    model=PublisherFile,
    name="publisherfile",
    parent=ParentViewSet(name="publisher"),   # publisher is a normal model ViewSet
    resource_permissions={"view": "storage.view_s3file"},
)
```

URL nesting, breadcrumbs and parent context buttons all resolve through the
parent's own model-based machinery, unaffected by the child being a Resource.
Multi-level model parents (model → model → resource) work the same way — all
ancestor pks arrive in `url_kwargs`.

Declaring `ParentViewSet(name=...)` that points at a Resource ViewSet fails a
startup system check (**E261**) — "Resources can only be leaves in the
nesting hierarchy."

## A note on pydantic warnings

If you build a `Resource` subclass hierarchy where an intermediate base class
has a computed `pk` (via `pk_field`) and a concrete subclass then declares a
**real** `pk` field, Pydantic emits a `UserWarning` about the `pk` field
shadowing an inherited attribute. This is expected — the library neutralizes
the shadowing so the subclass's real `pk` field value wins — and the warning
can be filtered:

```python
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)

    class Concrete(IntermediateBase):
        pk: str
```

## Limitations

| Limitation | Why | Escape hatch |
|---|---|---|
| No create/update views | writes ⇒ the data has a home ⇒ model it as a real (possibly unmanaged) model | `CustomFormNoObjectView` + a dev hook for odd one-off cases |
| No django-filter integration | `FilterSet` is welded to querysets | filter inside `cv_get_items` (the `request` is available there); an in-memory filter helper is a possible future addition |
| Pagination is in-memory only, no continuation tokens | not the right tool for very large listings | materialize the list yourself; Django's `Paginator` works fine on lists |
| Resources are leaves — cannot be a nesting parent | parent-object resolution and FK-based child filtering assume an ORM-queryable parent | none in v1; register flat Resource ViewSets, or encode a path into the pk (§ [Primary keys](#primary-keys-for-path-like-data)) |
| No `ManageView` | model/session tooling, doesn't apply | — |
| No django-guardian / workflow / polymorphic integration | all three are deeply ORM-bound | `GuardianViewSet` rejects a Resource model with a pydantic `ValidationError` at construction time; workflow and polymorphic simply have no Resource equivalent |
| Ordering/card mixins that call queryset methods (e.g. the ordered card-list mixin's `order_by`) | Resources are plain lists, not querysets | sort inside `cv_get_items` instead |

---

See also: [ActionView](action_view.md), [CustomFormView](custom_form_view.md),
[DetailCustomView](detail_custom_view.md), [ListView](list_view.md).
