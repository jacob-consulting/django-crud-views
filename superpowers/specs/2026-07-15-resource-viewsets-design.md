# Resource ViewSets — non-ORM data in django-crud-views

**Date:** 2026-07-15
**Status:** Approved design, not yet planned/implemented
**Scope:** core package (`crud_views`) only

## 1. Problem

`ViewSet` requires a Django model (`model: Type[Model]` is a required Pydantic field). Every
view resolves data through the ORM. But some data is table-shaped without living in the
database:

- S3 bucket contents (the driving use case: list objects, show detail, delete an object —
  small buckets, everything can be read in one call)
- Nested configuration object structures that should get a UI
- Any external API / computed data that wants the same chrome (breadcrumbs, sibling-aware
  context buttons, permission-checked links, tables) as the model-based pages

Today this is impossible: pk detection, permissions, labels, session keys, and querysets all
read from `model._meta` or `model.objects`.

## 2. Decision summary (what was agreed in brainstorming)

1. **Toolbox, not framework.** No generic storage-backend abstraction. A small `Resource`
   Pydantic base class + one view mixin. Reuse all existing view classes.
2. **Model-style protocol on the Resource class** (not hooks on views): data access lives as
   classmethods on the Resource, mirroring how Django models carry `objects` + `_meta`.
3. **Read + delete-shaped actions only.** List, detail, `CustomFormView` (form → hook) and
   `ActionView` (no form → hook) cover the S3 case. **No create/update** — the moment writes
   with forms appear, the right answer is a real (possibly unmanaged) model.
4. **Permissions are explicit** for Resource ViewSets — permission strings (typically backed
   by an unmanaged permission-holder model) or explicitly none (login-only). Never silently
   unprotected, never guessed.
5. **Resources are leaves in the nesting hierarchy (v1).** A Resource ViewSet may be the
   *child* of model ViewSets (any depth). A Resource may NOT be a *parent* (neither of a
   model ViewSet nor of another Resource ViewSet). See §8.
6. Honest scope assessment from brainstorming: full model-less CRUD was rated a bad idea
   ("a second product living inside the first"); this scoped read+action version was rated
   a good fit consistent with the DRF precedent of non-model ViewSets.

## 3. Where the model is load-bearing today (coupling points)

All file references are relative to `src/`.

| # | Coupling point | Location | What it reads | Resource strategy |
|---|---|---|---|---|
| 1 | Required field | `crud_views/lib/viewset/__init__.py:73` — `model: Type[Model]` | type check | widen to `Type[Model] \| Type[Resource]` |
| 2 | pk type auto-detect | `register()` validator, `viewset/__init__.py:96-107` — maps `type(self.model._meta.pk)` (`UUIDField→PK.UUID`, `AutoField→PK.INT`, …) | `model._meta.pk` | branch: read `Resource.cv_meta.pk_type` |
| 3 | Permissions | `default_permissions`, `viewset/__init__.py:358-382` — `ContentType.objects.get_for_model(model)` + `Permission.objects.filter(...)`; `permissions` cached_property at `:385` returns it | ContentType rows | branch: explicit `permissions=` dict required (or `None`) |
| 4 | Labels | `get_meta()`, `viewset/__init__.py:388-406` — `self.model._meta.verbose_name`, `.verbose_name_plural` | `model._meta` | `_meta` shim on Resource → **no branch needed** |
| 5 | Session namespace | `crud_views/lib/session.py:48-49` — `self.view.model._meta.app_label` | `model._meta.app_label` | `_meta` shim → **no branch needed** |
| 6 | Queryset + parent filter | `ViewSet.get_queryset()`, `viewset/__init__.py:204-236` — `model.objects.filter(...)` / `.all()`, walks parent chain building `{attr}__pk` filters; called from `CrudView.get_queryset` at `crud_views/lib/view/base.py:128-129` | `model.objects` | `ResourceViewMixin` overrides `get_queryset`/`get_object` → ViewSet.get_queryset never called |
| 7 | Auto ManageView | `register()` validator, `viewset/__init__.py:116-117` — creates `AutoManageView` with `model=self.model` | model attr on a CBV | skip for Resources |
| 8 | System checks | `crud_views/checks.py` + per-view `checks()` | various | skip/adapt model-specific checks for Resources |

URL pattern mechanics (`urlpatterns` at `viewset/__init__.py:324-355`) are already
model-agnostic: `re_path` with pk regexes from `crud_views/lib/viewset/path_regs.py`
(`PrimaryKeys.INT/HEX/UUID/KEY/STR`). `PK.STR` is `[A-Za-z0-9_\-]+` — note this matches
base64url alphabet exactly, which §9 exploits for S3 keys.

## 4. Component 1: `Resource` base class

New file: `src/crud_views/lib/resource.py` (exact location up to the implementation plan;
must be importable as `from crud_views.lib import Resource` alongside the existing exports).

```python
from typing import Self

from django.http import Http404
from pydantic import BaseModel

from crud_views.lib.viewset import ViewSet


class ResourceMeta:
    """
    Duck-types the subset of Django's ``model._meta`` (Options) API that
    crud_views reads, so ViewSet.get_meta() and SessionData keep working
    UNCHANGED on Resources. Add attributes here only when a coupling point
    actually reads them.
    """

    verbose_name: str = "item"
    verbose_name_plural: str = "items"
    app_label: str = "resources"     # session-data namespace, crud_views/lib/session.py:49
    pk_field: str = "pk"             # name of the Resource attribute that identifies a row
    pk_type: str = ViewSet.PK.STR    # regex for URL patterns, see path_regs.PrimaryKeys
    ordering: str | None = None      # informational; dev sorts in cv_get_items


class Resource(BaseModel):
    """
    Base class for non-ORM table-shaped data rendered through a ViewSet.

    Subclasses define fields like a normal Pydantic model, an inner Meta class
    (same idiom as Django models), and implement cv_get_items(). Rows are
    Pydantic instances -> Django templates and django-tables2 use plain
    attribute access, so the existing list/detail templates work as-is, and
    raw input (e.g. an S3 API response) is validated at conversion time.
    """

    class Meta(ResourceMeta):
        pass

    # -- meta shim ------------------------------------------------------------

    # ``Resource._meta`` (class-level access) returns an Options-shaped object
    # exposing the merged Meta attributes (user Meta with ResourceMeta
    # defaults filled in). This is the shim that makes coupling points 4 and 5
    # work without branching. Mechanism (classproperty / __init_subclass__ /
    # descriptor) is deliberately left to the implementation plan — see §13.

    # -- identity ---------------------------------------------------------------

    @property
    def pk(self):
        """Value of the Meta.pk_field attribute (read through the merged
        _meta so Meta defaults apply). Templates and URL-building code can
        uniformly say object.pk, like with Django models."""
        return getattr(self, self._meta.pk_field)

    # -- data-access protocol (the "model-style protocol", option A) ------------

    @classmethod
    def cv_get_items(cls, request, **url_kwargs) -> list[Self]:
        """
        THE hook the developer implements: return all rows.

        url_kwargs are the resolved URL kwargs of the requesting view. For a
        nested Resource ViewSet they contain the parent pk(s), e.g.
        ``publisher_pk`` — the developer uses them to scope the listing
        (see §8). Must return a plain list (Django's Paginator needs len()
        and slicing; both work on lists).
        """
        raise NotImplementedError

    @classmethod
    def cv_get_item(cls, request, pk, **url_kwargs) -> Self:
        """
        Return a single row by pk. Default: linear scan over cv_get_items()
        comparing str(row.pk) == str(pk); raises Http404 when not found.
        Deliberately dumb — fine for "read them all at once"-sized data.
        Override when a direct lookup is cheaper (e.g. head_object on S3).
        """
        for item in cls.cv_get_items(request, **url_kwargs):
            if str(item.pk) == str(pk):
                return item
        raise Http404(f"{cls.Meta.verbose_name} with pk={pk!r} not found")
```

Notes for the implementer:

- The `_meta` shim must expose **exactly** `verbose_name`, `verbose_name_plural`,
  `app_label` as instance-attribute-style access (`Resource._meta.verbose_name`), because
  `ViewSet.get_meta()` calls `.capitalize()` on them and `SessionData.app_label` reads
  `app_label`. Grep for further `model._meta` reads before finalizing — the table in §3
  was verified on 2026-07-15 but new reads may have landed since.
- `verbose_name.capitalize()` is applied by `get_meta()` — Meta values should be lowercase,
  same convention as Django.
- Pydantic v2 note: `Meta` as a plain inner class inside a `BaseModel` subclass is ignored
  by Pydantic's schema machinery (it only special-cases `model_config`), so this is safe;
  add a test proving a `Resource` subclass with fields + Meta round-trips validation.
- Subclassing inheritance: `class Meta(ResourceMeta)` on the base; user subclasses write
  `class Meta:` freely — the shim should fall back to `ResourceMeta` defaults for missing
  attributes (read via `getattr(cls.Meta, name, getattr(ResourceMeta, name))` or by making
  user Metas implicitly merged; implementation plan decides, behavior must be: unspecified
  Meta attrs get defaults).

## 5. Component 2: ViewSet changes

All in `src/crud_views/lib/viewset/__init__.py` unless noted.

### 5.1 Accept Resources

```python
model: Type[Model] | Type[Resource]   # was: Type[Model]
```

Add a helper used by every branch point:

```python
@property
def is_resource(self) -> bool:
    return not issubclass(self.model, Model)   # or: issubclass(self.model, Resource)
```

(Implementation should check `issubclass(self.model, Resource)` explicitly and let Pydantic
validation reject anything that is neither — a plain class must fail loudly at definition
time.)

### 5.2 pk detection (`register()` validator, currently lines 96-107)

```python
if self.pk is None:
    if self.is_resource:
        self.pk = self.model._meta.pk_type       # explicit, no field-type mapping
    else:
        ... existing pk_field_map lookup on model._meta.pk ...
```

`pk` remains overridable per ViewSet (it is a plain regex string — a dev can pass a custom
regex exactly as today).

### 5.3 Permissions — new explicit field

```python
# NEW field on ViewSet:
resource_permissions: Dict[str, str] | None = None
```

Behavior:

- **Model ViewSet:** unchanged — `permissions` cached_property returns `default_permissions`
  (ContentType + Permission DB query, lines 358-386). `resource_permissions` must be `None`
  (validator error otherwise — avoid two sources of truth).
- **Resource ViewSet:** `default_permissions` must NEVER run (`ContentType.objects.get_for_model`
  would raise/return nonsense for a non-model). `permissions` returns:
  - the explicit dict, e.g.
    `{"view": "storage.view_s3object", "delete": "storage.delete_s3object"}` — keys are the
    short permission keys views reference via `cv_permission` ("view", "change", "delete",
    custom ones); values are full `app_label.codename` strings, typically defined on an
    unmanaged permission-holder model (§7);
  - or `{}` when the dev passed `resource_permissions=None` **and** uses only
    non-`PermissionRequired` view variants. A Resource ViewSet where a
    `*PermissionRequired` view is registered but its `cv_permission` key is missing from
    the dict must fail at startup via the existing system-check machinery
    (`CrudViewPermissionRequiredMixin` check at `crud_views/lib/view/base.py:540` already
    looks up `cls.cv_viewset.permissions.get(cls.cv_permission)` — verify it produces a
    check Error, not a silent None, for this path).

Rationale (from brainstorming): nobody should silently ship an unprotected delete-from-S3
button; explicit-or-declared-absent, never defaulted.

### 5.4 Skip auto ManageView for Resources (lines 116-117)

`register()` creates an `AutoManageView` bound to `self.model`. ManageView is model/session
tooling; for v1, wrap in `if not self.is_resource:`. (Follow-up may revisit.)

### 5.5 `get_queryset()` (lines 204-236)

Leave untouched. Resource views never call it (the mixin overrides `get_queryset` at the
view level, see §6). Optionally add a defensive
`cv_raise(not self.is_resource, "ViewSet.get_queryset called for a Resource ViewSet — did you forget ResourceViewMixin on a view?")`
— cheap and turns a confusing ORM error into an actionable one.

### 5.6 System checks

- `ViewSet.checks()` (lines 142-151) — name/prefix/template checks are model-agnostic, keep.
- Any check reading model fields/meta must be skipped or adapted for `is_resource`.
  The implementation plan must enumerate them (grep `checks.py` + per-view `checks()`
  classmethods for `model` access).
- **New check (E-number from the next free slot):** Resource ViewSet with a registered
  `*PermissionRequired` view whose `cv_permission` key is not in `resource_permissions`
  → Error with a message telling the dev to add the key or use the non-permission variant.

## 6. Component 3: `ResourceViewMixin`

Lives next to `Resource` (same new module). This is the whole "views" story — **no new view
classes**:

```python
class ResourceViewMixin:
    """
    Put FIRST in bases, before any crud_views view class:

        class S3ObjectListView(ResourceViewMixin, ListViewPermissionRequired): ...

    Overrides the two ORM entry points so every existing view class
    (ListView, DetailView, CustomFormView, ActionView, ...) works on Resources.
    """

    def get_queryset(self):
        # replaces CrudView.get_queryset (crud_views/lib/view/base.py:128),
        # which delegates to ViewSet.get_queryset (ORM + parent filtering)
        return self.model.cv_get_items(self.request, **self.kwargs)

    def get_object(self, queryset=None):
        # replaces SingleObjectMixin.get_object; pk kwarg name is the
        # ViewSet's pk_name (default "pk")
        pk = self.kwargs[self.cv_viewset.pk_name]
        return self.model.cv_get_item(self.request, pk, **self.kwargs)
```

Implementation caveats to verify while building (each becomes a test):

1. **`ListView` pagination**: Django's `MultipleObjectMixin.paginate_queryset` works on
   lists — confirm with a paginated Resource list test.
2. **django-tables2**: `ListViewTableMixin` builds a table from `get_queryset()` results;
   tables2 supports list-of-objects data, including column ordering. Confirm sorting a
   Resource table doesn't call queryset-only APIs (tables2 falls back to
   `order_by` on sequences). If `cv_list_actions` / row-URL building calls `object.pk` —
   that works via the `pk` property (§4).
3. **`DetailView`/`CustomFormView`/`ActionView`** all resolve through
   `SingleObjectMixin.get_object` → covered by the override. `ActionView.post`
   (`crud_views/lib/views/action.py:13-22`) sets `self.object = self.get_object()`, calls
   `self.action(context)` (dev hook returning bool), then `cv_action_success/error` →
   messages + `cv_action_success_hook`/`cv_action_error_hook`. Nothing ORM-specific.
4. **`CustomFormView`** (`crud_views/lib/views/form.py:11`) is
   `CrudViewProcessFormMixin + CrudView + FormMixin + DetailView`; dev sets `cv_key`,
   `cv_path`, `form_class`, implements `cv_form_valid(context)`. This is the
   delete-with-confirm building block for S3. `CustomFormNoObjectView` (form.py:41,
   `cv_object = False` → no pk in URL) works without even needing `get_object`.
5. **Success URLs / redirects**: `get_success_url` builds sibling URLs via the router
   names — model-agnostic, but a deleted object's detail URL must not be the redirect
   target; the existing delete flow redirects to list — mirror that in docs/example.
6. **Templates**: `cv_get_meta` (`view/base.py:464`) → `ViewSet.get_meta` reads
   `model._meta.verbose_name*` — satisfied by the `_meta` shim, zero template changes.
7. **`SessionData`** (`session.py:48-49`) reads `view.model._meta.app_label` — shim covers
   it; add a test that a Resource list view with filters/session survives a request cycle.

## 7. Permissions recipe (documentation content, no code changes)

Django permissions require a ContentType. The documented pattern for Resource ViewSets is a
**permission-holder model**: unmanaged, no table, no default permissions, only custom ones:

```python
# app: storage
class S3ObjectPermissions(models.Model):
    class Meta:
        managed = False                      # no table
        default_permissions = ()             # no add/change/delete/view auto-perms
        permissions = [
            ("view_s3object", "Can view S3 objects"),
            ("delete_s3object", "Can delete S3 objects"),
        ]
```

Migration note: `managed = False` models still get migrations for permission creation —
`makemigrations` handles this; the migration creates only the Permission/ContentType rows.

```python
s3_viewset = ViewSet(
    model=S3Object,                          # the Resource subclass
    name="s3object",
    resource_permissions={
        "view": "storage.view_s3object",
        "delete": "storage.delete_s3object",
    },
)
```

Alternative: point at any existing model's permissions. Or pass
`resource_permissions=None` and use non-`PermissionRequired` views (login-only via
project middleware/mixins — dev's responsibility, must be stated in docs).

## 8. Nesting rules

**Rule: models can sit anywhere in the hierarchy; Resources can only be leaves (v1).**

### 8.1 Supported: Resource ViewSet as child of model ViewSet(s)

```python
class S3Object(Resource):
    key: str
    size: int
    modified: datetime

    class Meta:
        verbose_name = "file"
        verbose_name_plural = "files"
        pk_field = "key_b64"      # see §9
        app_label = "storage"

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        publisher = Publisher.objects.get(pk=url_kwargs["publisher_pk"])
        raw = list_bucket(prefix=f"publishers/{publisher.slug}/")   # dev's S3 code
        return [cls.model_validate(row) for row in raw]


files_viewset = ViewSet(
    model=S3Object,
    name="file",
    parent=ParentViewSet(name="publisher"),   # publisher is a normal model ViewSet
    resource_permissions={...},
)
```

Why this works without new machinery:

- URL nesting (`publisher/<pk>/file/...`) is generated at ViewSet level
  (`get_path_parent` walks `parent.get_pk_name()` — `viewset/__init__.py:159-175`) —
  storage-agnostic.
- Breadcrumbs / parent context buttons resolve the **parent** object through the parent's
  own model-based machinery — untouched.
- The ORM parent-filtering in `ViewSet.get_queryset` (the `{attr}__pk` walk, lines
  209-227) is bypassed by `ResourceViewMixin.get_queryset`; **the developer is responsible
  for scoping** the listing using the parent pk kwargs (`publisher_pk` etc., names from
  `ParentViewSet.get_pk_name()` — `parentviewset.py:56-60`).
- Multi-level model parents (model → model → resource) work identically: all ancestor pks
  arrive in `url_kwargs`.

### 8.2 NOT supported (v1): Resource as parent — of anything

Declared non-goal. Two concrete breakages if attempted:

1. Parent-object resolution (breadcrumbs, `ParentContextButton`, parent verbose names)
   assumes the parent ViewSet's model is ORM-queryable.
2. A model child's auto-filter builds `filter(parent_attr__pk=...)` — a model can't FK a
   non-DB parent.

Both are solvable (route parent resolution through `cv_get_item`; filter on a plain field
holding the parent's pk) — that is the sketched **v2** if the nested-config projects need
breadcrumbed Resource trees. v1 must raise a clear startup error (system check or
`register()` validation) when `ParentViewSet(name=...)` points at a Resource ViewSet.

Poor-man's nesting for config trees, today, without v2: register flat Resource ViewSets
whose URL prefix carries extra kwargs via `cv_path_contribute`, or simply encode the tree
path inside the pk (§9 pattern generalizes: pk = base64url of a path).

## 9. S3 keys as pk (URL-safety)

S3 keys contain `/` (`reports/2026/q1.pdf`); no default pk regex admits slashes and the URL
grammar `[parent/]prefix/[pk/]view_path/` can't take a greedy segment.

**Documented pattern (no package changes):** expose a URL-safe computed pk:

```python
import base64

class S3Object(Resource):
    key: str          # real S3 key, shown in tables
    size: int

    class Meta:
        pk_field = "key_b64"
        pk_type = ViewSet.PK.STR   # r"[A-Za-z0-9_\-]+" — exactly the base64url alphabet

    @property
    def key_b64(self) -> str:
        return base64.urlsafe_b64encode(self.key.encode()).decode().rstrip("=")
```

Decode in `cv_get_item` override (or keep the default linear scan, which compares the
encoded values — no decode needed). Note `pk_field` may name a **property**, not only a
Pydantic field — the `pk` property does `getattr`, so this must be supported and tested.

Padding note: strip `=` (not in `PK.STR`); `urlsafe_b64decode` needs padding restored
(`s + "=" * (-len(s) % 4)`) — put this helper in the docs example, not the package.

## 10. Explicit non-goals (v1)

| Non-goal | Why | Escape hatch |
|---|---|---|
| Create/update views for Resources | writes ⇒ data has a home ⇒ use a (possibly unmanaged) model | `CustomFormNoObjectView` + dev hook for odd cases |
| django-filter integration | queryset-bound | dev filters inside `cv_get_items` (request is available) |
| Continuation-token pagination (large S3) | "not the tool for it" (user decision) | materialize the list; Django Paginator on lists works |
| Resource as nesting parent | see §8.2 | v2 sketch in §8.2 |
| Special pk types / encoders in the package | keep toolbox small | §9 documented pattern |
| ManageView for Resources | model/session tooling | skipped at registration |
| guardian/workflow/polymorphic integration | all deeply ORM-bound | out of scope, unaffected |

## 11. Testing plan (tests/test1/)

Test infrastructure: add a Resource (e.g. `S3File` with a faked in-memory "bucket" — a
module-level list of dicts, monkeypatchable) + permission-holder model to
`tests/test1/app/models.py`, viewsets in the app's viewset module, following existing
fixture conventions (`cv_<name>`, `user_<model>_<perm>`, `client_user_<model>_<perm>` in
`tests/test1/conftest.py`).

Must-have tests:

1. Resource subclass definition: Meta defaults merge, `pk` property, `_meta` shim exposes
   verbose names + app_label; pk_field naming a property works.
2. ViewSet registration: pk_type respected, custom `pk` regex override, plain class (not
   Resource/Model) rejected, `resource_permissions` on model ViewSet rejected.
3. List view: renders rows (tables2 + plain), pagination over a list, empty list.
4. Detail view: found / 404 via default `cv_get_item`.
5. CustomFormView delete flow: GET renders confirm form, POST valid → `cv_form_valid`
   called → row removed from fake bucket → redirect to list + message.
6. ActionView: POST → `action()` hook, success and error paths, messages, redirect.
7. Permissions: `*PermissionRequired` variants 403 without / pass with the unmanaged-model
   permission; startup check fires when a `cv_permission` key is missing from
   `resource_permissions`.
8. Nesting: model parent → resource child: URL contains parent pk, `cv_get_items` receives
   `publisher_pk`, breadcrumbs render; Resource-as-parent raises the startup error.
9. Session data: Resource view request cycle persists/reads session (app_label shim).
10. Regression: entire existing suite green — model ViewSet behavior byte-identical
    (special attention: `default_permissions` still lazy/cached, `AutoManageView` still
    created for models).

## 12. Documentation

- New docs page (mkdocs, `docs/`): "Resources — non-model data" with the full S3 example:
  Resource class, permission-holder model, ViewSet, list/detail/delete views, base64url pk
  pattern, nesting-under-model example, non-goals table.
- README: one paragraph + link.
- CHANGELOG entry under Unreleased.

## 13. Open items deliberately left to the implementation plan

- Exact module path/name (`crud_views/lib/resource.py` suggested) and public export surface.
- `_meta` shim implementation technique (classproperty vs `__init_subclass__`-built Options
  object) — behavior is specified in §4, mechanism is free.
- Check IDs (next free E/W numbers in `crud_views/checks.py` / check registry).
- Whether `ResourceViewMixin` should also guard against being combined with
  `CreateView`/`UpdateView`/`DeleteView` (suggest: system check Error — cheap and explicit,
  consistent with decision 3).

## 14. How this session got here (context for a fresh session)

Brainstormed 2026-07-15. Key exchanges: (a) initial ask was generic "list of dicts without
a model" — assessed honestly: full model-less CRUD rejected, scoped read+action accepted;
(b) user proposed the Pydantic base class for the meta story — adopted, extended with the
`_meta` shim insight; (c) user chose model-style protocol (option A) over view hooks;
(d) user cut scope to "toolbox": list/detail/custom-form/action only, no create/update,
small data only (S3 read-all-at-once); (e) nesting rules confirmed: model→resource child OK
(dev parses parent kwargs in `cv_get_items`), resource-as-parent explicitly v2.
Discovery that shaped the design: `ActionView` and `CustomFormView`/`CustomFormNoObjectView`
already exist and already have exactly the dev-hook shape the user asked for — so the
feature is "make existing views resolve objects from a Resource", not "build new views".

Next step per superpowers flow: **writing-plans** skill → implementation plan in
`superpowers/plans/`.
