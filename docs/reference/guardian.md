# Per-Object Permissions (django-guardian)

The `crud_views_guardian` sub-package adds per-object permission support via
[django-guardian](https://django-guardian.readthedocs.io/). Users opt in by
swapping `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` →
`Guardian*ViewPermissionRequired`.

!!! example "Try it live"
    The [Guardian example](https://django-crud-views-demo.onrender.com/guardian/document/) and the
    [Delete example](https://django-crud-views-demo.onrender.com/delete/project/) in the live demo show this in
    action — log in as `alice` / `alice` and as `bob` / `bob` to compare what each of them sees. See
    [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Installation

```bash
pip install django-crud-views[guardian]
```

## Setup

```python
INSTALLED_APPS = [
    ...
    "guardian",
    "crud_views_guardian.apps.CrudViewsGuardianConfig",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

ANONYMOUS_USER_NAME = None
```

Then run migrations:

```bash
python manage.py migrate
```

## Usage

Replace `ViewSet` with `GuardianViewSet` and each `*ViewPermissionRequired` with
its `Guardian*` equivalent:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_author = GuardianViewSet(model=Author, name="author")


class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author
    ...


class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    ...
```

## Assigning Per-Object Permissions

```python
# Grant user permission to view a specific author
cv_author.assign_perm("view", user, author_instance)

# Grant a group permission
cv_author.assign_perm("change", group, author_instance)

# Revoke permission
cv_author.remove_perm("view", user, author_instance)

# Get all objects a user can view
qs = cv_author.get_objects_for_user(user, "view")
```

### Configured content-type defaults

`GuardianViewSet.default_permissions` discovers Permission rows on the type selected by Guardian's
`GUARDIAN_GET_CONTENT_TYPE`, including custom permissions on that type. It removes only the exact terminal
`_<content_type.model>` suffix to form each key and retains the fully qualified permission value.
With the default concrete resolver, Car uses `app.view_car` and PublisherProxy uses `app.view_publisher`.
With `polymorphic.contrib.guardian.get_polymorphic_base_content_type`, a Car ViewSet uses `app.view_vehicle`,
discovers Vehicle's custom permissions, and returns Car querysets. Child-only Car permissions are not inferred
or unioned with Vehicle's permissions. Core `ViewSet` discovery is unchanged.

Explicit application `permissions` property overrides retain their exact keys and qualified values. An
incompatible explicit mapping remains a configuration/programming error, including Guardian's original
`MixedContentTypeError`; it is never translated into empty or widened access. Nonempty discovered defaults are
cached per ViewSet for the process lifetime, while empty discovery retries. Set the resolver before startup;
later resolver/permission changes require a fresh ViewSet or restart, without runtime hot-reload guarantees.
See the executable [configured-content-type migration](../migrating-1.0.md#guardian-configured-content-type-permissions)
for grant/query/removal and a registered list. This is an immediate change to inferred defaults, without a grace period.

## Strict Mode (Default)

By default, `cv_guardian_accept_global_perms = False`: a user with a model-level
`view_author` Django permission is **not** granted access to individual objects.
Only explicit per-object grants (via `assign_perm`) count.

To allow model-level permissions as a fallback for a specific view:

```python
class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True
```

The fallback is a **view** setting and nothing else. Each view class reads its own `cv_guardian_accept_global_perms`,
so two views of one `GuardianViewSet` can follow different policies. The ViewSet does not pass a value on to its views.
The flag covers only the view's own object gate or list filter, never an ancestor of a nested request; an ancestor's
model fallback is its own `AncestorPolicy(accept_global_perms=True)`, see
[Ancestor fallback and view fallback](#ancestor-fallback-and-view-fallback).

`GuardianViewSet` no longer accepts a `cv_guardian_accept_global_perms` key. The key never changed access, and
passing it now (as `True` or `False`, as a keyword or in `GuardianViewSet.model_validate({...})`) fails with a
Pydantic `ValidationError` that names the per-view replacement, and nothing is registered. Set the attribute on each
view class that should accept global permissions instead; see
[Migrating to 1.0.0](../migrating-1.0.md#the-guardianviewset-global-permission-key).

### The ViewSet helper is always strict

`GuardianViewSet.get_objects_for_user(user, perm)` has a fixed policy of its own and no option to change it. It never
accepts global model permissions. It does count object grants and group grants. An active superuser gets every
object, and an inactive user gets none. A view's `cv_guardian_accept_global_perms` does not change what the helper
returns, so a list view with the fallback can show rows the helper does not return.

The shared `STRICT_HELPER_POLICY` is a `MappingProxyType` over an unexposed literal mapping:
`{"policy": "strict", "accept_global_perms": False, "use_groups": True}`. Assignment raises `TypeError`.
Manage context exposes detached `dict` copies; editing one response cannot change helper authority or later
responses. This prevents accidental mapping/context mutation, not arbitrary monkeypatching of application modules.

### Permission key diagnostics

`assign_perm`, `remove_perm` and `get_objects_for_user` accept exact configured **string** keys from
`viewset.permissions`. Unknown/empty/non-string inputs raise `ValueError`, replacing earlier `KeyError` (and
unhashable-input `TypeError` or the inactive-user empty-result shortcut). Validation precedes inactive-user return,
target queryset access and Guardian shortcut calls/permission writes. A valid key for an inactive actor still
returns an empty queryset. Non-string input is a programming error, including `None`, integers, bytes, lists and
dicts; it is not an alternative way to request no permissions.

The exact message is `Invalid permission key {perm!r}. Valid keys: {alternatives}.`, with
`alternatives = ", ".join(repr(key) for key in sorted(self.permissions))`. Alternatives are the actual configured
keys, not a fixed CRUD list. Case, whitespace and Unicode normalization are not changed. A configuration with keys
`zebra`, `réviser`, `alpha` reports `Invalid permission key 'view'. Valid keys: 'alpha', 'réviser', 'zebra'.`
See the executable [Guardian permission-key migration](../migrating-1.0.md#guardian-permission-keys).

### Inactive users

A user who is logged in but whose account is inactive (`is_active = False`, possible with a backend such as
`AllowAllUsersModelBackend`) gets no authority from any Guardian path. That applies to ordinary users, users with
object or group grants, users with only global permissions, and superusers. Every `Guardian*ViewPermissionRequired` view
answers such a user with 403 before it resolves a parent, an object or a formset fragment. That includes list and card
views, which return no rows, and an HTTP DELETE, which gets 403 rather than 405. The callable helpers deny such a user too:
`cv_has_access`, `cv_create_has_access`, `get_objects_for_user` (an empty queryset) and the delete-preview label
filter. Anonymous users keep their configured `cv_guardian_anonymous_behavior`. Deactivating a user or revoking a
grant takes effect on that user's next request.

## Create Views

`CreateView` cannot check per-object permission on an object that does not exist
yet. Two cases:

**Top-level creates** (no parent viewset): Django's standard model-level
`add_<model>` permission is checked. Grant this globally to users who should
be able to create objects.

**Child creates** (with parent viewset): The parent object exists. The request's ancestors are authorized like
every nested request (see [Parent Viewsets](#parent-viewsets)): create is a Write, so the immediate parent needs
`change` by default, checked by the parent ViewSet's own provider — an object grant for a `GuardianViewSet`
parent, a model permission for a core `ViewSet` parent. No model-level `add_<model>` check is made on the child
model, and none is added when the parent is unprotected or cascade is off. The parent's `cv_action_enabled` state
check still runs with the resolved parent.

Child create views **must** use `GuardianCreateViewPermissionRequired` (not
plain `CreateViewPermissionRequired`). Using the plain variant causes the
create button to always be hidden (falls back to a model-level `add_<model>`
check that guardian users typically don't have) and prevents the form page
from loading.

### Create button visibility for child viewsets

`cv_has_access` is a classmethod with no access to the request or URL kwargs.
When the create button is rendered from a child list page, `obj=None`, so the
parent cannot be looked up inside `cv_has_access` alone.

`GuardianListViewPermissionRequired` resolves this: its `cv_get_context`
override detects the child create case, fetches the parent object from the
URL kwargs via `cv_get_parent_object()`, and calls `cv_create_has_access` on
the create view class with the resolved parent.

The default `cv_create_has_access` checks the immediate parent with that parent's provider and fallback and the
create's nearest Write key (`change` by default); a parent with `provider="none"` skips only that permission.
It never evaluates a farther ancestor; the create request itself still does. Override it on the create view class
for custom logic:

```python
class BookCreateView(CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookCreateForm

    @classmethod
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        """
        rendering_view: the list view instance (has .request, .kwargs, etc.)
        parent_obj: resolved parent model instance, or None if lookup failed
        """
        if parent_obj is None:
            return False
        # custom logic, e.g. check role membership beyond the standard perm
        from guardian.core import ObjectPermissionChecker

        return ObjectPermissionChecker(user).has_perm("change_publisher", parent_obj)
```

When `cv_create_has_access` is not overridden, no extra configuration is needed for the standard case. The
create view's own `cv_guardian_accept_global_perms` plays no part in it: a model grant on a Guardian parent counts
only with that parent's `AncestorPolicy(accept_global_perms=True)`.

The URL-bound list override above is unchanged. On a child list page the parent comes from the URL, so `cv_access`
and `cv_action_enabled` of the create control are both computed from that parent. If the parent cannot be resolved
late (`Http404` or `KeyError`), both fields are `False` and no custom `cv_action_enabled` hook is called with `None`.

### What the create access helpers accept

`cv_has_access(user, obj)` and `cv_create_has_access(user, rendering_view, parent_obj)` on a nested
`GuardianCreateViewPermissionRequired` check **permission only**. The action state (`cv_action_enabled`) is a
separate field; see [Conditionally disabling an action](action_enabled.md). The object you pass decides which parent
the permission is checked on:

| Input | Result |
|---|---|
| An instance of the parent model | The permission is checked on that parent. |
| An instance of the create view's own model, with a `ForeignKey` to its parent | The parent is read through the configured attribute (`ParentViewSet.get_attribute()`, the `attribute` you declared or the parent ViewSet's name), and the permission is checked on it. For a Book the helpers answer exactly as they would for that Book's Publisher. |
| An own-model instance of a `ManyToMany` nesting (`many_to_many_through_attribute`) | Denied. The object exposes a related manager, not one parent, so it cannot tell which URL parent a create would use. |
| `None`, an instance of an unrelated model, or an own-model instance whose parent relation is empty or missing | Denied, superusers included. |

Before 1.0 these helpers returned `True` for any object that was not a parent instance, so a Book was granted
"add book" whatever the user held on its Publisher. Now an own child honors its actual parent's permission, and an
unrelated object denies. See [Migrating to 1.0.0](../migrating-1.0.md#nested-guardian-create-access).

The `ManyToMany` case fails closed on purpose. A helper, filter or control that only receives the child object has no
selected parent, and picking the first or only related parent would invent authority the URL never granted. What
does work for `ManyToMany` nesting:

- the helpers with an explicit parent instance, `Genre` create checked against `publisher_a`;
- the URL-bound child list, whose create control resolves the parent from the URL;
- direct create GET and POST under an authorized URL parent, including an unprotected (`provider="none"`) parent
  and the independent state rule.

On list pages, place the control through the URL-aware
[resolved button loop](../faq.md#render-a-custom-loop-of-buttons). Route-aware create controls for a `ManyToMany`
child's own page would need an explicit selected-parent contract. They are a possible future enhancement and are not
part of 1.0.

Top-level creates are unchanged: `cv_has_access(user, obj)` checks the model-level `add_<model>` permission, and
object grants never stand in for it.

## Parent Viewsets

Nested Guardian requests are authorized by the shared ancestor mechanism described in
[Ancestor authorization](nested.md#ancestor-authorization), the same one core ViewSets use: request order,
Read/Write pairs, exact `actions` entries for custom endpoints, cascade depth, ancestor querysets, the
default-database boundary, Resource leaves and the mutation and link-visibility limits all apply unchanged. This
section covers what is specific to Guardian: how a `GuardianViewSet` is checked when it is the *ancestor*, and how
that differs from the endpoint's own object gate.

The shipped Guardian child views keep their own gates after ancestry: the child object permission, the list
filter, actor rules (`cv_guardian_anonymous_behavior`, inactive users), action state and create attachment. Custom
compositions need the mixins described in [Custom child-view compositions](#custom-child-view-compositions).

### Core or Guardian parent

The parent's own ViewSet class decides how it is checked. A core `ViewSet` parent requires a **model** permission;
a `GuardianViewSet` parent requires an **object** grant on the resolved parent, direct or through a group, and is
strict by default. A Guardian child under a Guardian parent:

```python
from crud_views.lib.viewset import ParentViewSet
from crud_views.lib.views import CreateViewParentMixin
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianCreateViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)

from myapp.models import Book, Publisher

cv_publisher = GuardianViewSet(model=Publisher, name="publisher")  # as an ancestor: object grants, strict
cv_book = GuardianViewSet(model=Book, name="book", parent=ParentViewSet(name="publisher"))


class BookListView(GuardianListViewPermissionRequired):  # Read: view on this Publisher object
    cv_viewset = cv_book


class BookDetailView(GuardianDetailViewPermissionRequired):  # plus view on this Book object
    cv_viewset = cv_book


class BookUpdateView(GuardianUpdateViewPermissionRequired):  # Write: change on this Publisher object
    cv_viewset = cv_book
    fields = ["title"]


class BookCreateView(CreateViewParentMixin, GuardianCreateViewPermissionRequired):  # no add_book needed
    cv_viewset = cv_book
    fields = ["title"]
```

With the same Book views, the grant a user holds on Publisher decides:

| Grant on Publisher | Core `ViewSet` parent | `GuardianViewSet` parent (default) |
|---|---|---|
| object grant only (direct or group) | denied | satisfied |
| model grant only | satisfied | denied |

The child's own gates stay independent in every row: a Publisher grant never replaces the Book object grant of
the detail or update view. `provider="guardian"` on a core `ViewSet` is rejected; make the parent a
`GuardianViewSet` to keep object-based parent protection.

### Ancestor fallback and view fallback

Two settings accept model permissions, and they never affect each other:

- `AncestorPolicy(accept_global_perms=True)` on a `GuardianViewSet` lets the required **model** permission satisfy
  that ViewSet's gate when it is an *ancestor*, for every descendant request that checks it.
- `cv_guardian_accept_global_perms = True` on a Guardian view lets model permissions satisfy that **view's own**
  object gate or list filter. It never relaxes an ancestor.

```python
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired

from myapp.models import Book, BookNote, Publisher

cv_publisher = GuardianViewSet(
    model=Publisher,
    name="publisher",
    ancestor_policy=AncestorPolicy(accept_global_perms=True),  # as an ancestor: model or object grant
)
cv_book = GuardianViewSet(model=Book, name="book", parent=ParentViewSet(name="publisher"))  # as an ancestor: strict
cv_note = GuardianViewSet(model=BookNote, name="note", parent=ParentViewSet(name="book"))


class BookDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book  # its own gate stays strict: a Book object grant


class NoteListView(GuardianListViewPermissionRequired):
    cv_viewset = cv_note
    cv_guardian_accept_global_perms = True  # its own list filter only, not the Book or Publisher ancestors
```

A request to the Note list checks Publisher `view` (model or object grant) and Book `view` (object grant only),
then the list's own filter, which here also accepts the Note model permission. In both directions:

- Publisher's ancestor fallback does not relax the strict Book detail gate: a Publisher model grant opens the
  Publisher gate, and the Book page still needs a Book object grant.
- The Note list's view fallback does not relax the strict Book ancestor: a Book *model* grant does not open the
  Note list; a Book object grant does.

Publisher's fallback applies to every descendant that reaches it: Book and Note requests alike. Book's own
`AncestorPolicy.accept_global_perms` would matter only where Book is the ancestor, such as these Note requests; it
never changes the Book views' own gates.

### Migrating from the removed parent fields

`cv_guardian_parent_permission` and `cv_guardian_parent_create_permission` are gone. Declaring either one — as a
constructor keyword or on a `GuardianViewSet` subclass, even as `None` or with an old default value — fails with
a Pydantic `ValidationError` naming the replacement when the ViewSet is constructed, and nothing is registered.
Nothing is translated automatically:

| Before | Now |
|---|---|
| `cv_guardian_parent_permission` (`"view"`) for list, detail, update and delete | list and detail are Read and keep `view`; update and delete are Write and need `change` on the parent by default. To keep `view` for them, declare `AncestorPolicy(write=AncestorPermissions(nearest="view", higher="view"))` on the child ViewSet |
| `cv_guardian_parent_create_permission` (default `None`: use the parent key, `"view"`) for create | create is Write and needs `change` on the parent by default. The old `None` meant "inherit the parent key"; it is not the new provider `"none"` |
| another parent key for the child's requests | `AncestorPolicy(read=...)`, `write=...` or exact `actions` entries on the **child** ViewSet |
| `cv_guardian_parent_permission=None` (skip the parent check) | `AncestorPolicy(provider="none")` on the **parent** ViewSet: it then skips its gate for every descendant; a `"none"` parent is still resolved and its state checks still run |
| a Guardian child under a core `ViewSet` parent, checked with object grants on the parent | the core parent now requires model permissions; make the parent a `GuardianViewSet` to keep object grants |
| the child view's `cv_guardian_accept_global_perms` relaxed the parent check | the view flag keeps only its own gate; set `AncestorPolicy(accept_global_perms=True)` on the parent ViewSet if model grants should satisfy it — a shared choice for all its descendants |
| nested generic actions, custom forms, workflow views | an exact `actions` entry with a complete pair on the child ViewSet, or the request fails (`viewset.E268`) |
| a nested manage page | still requires its manage setting or group, and now also normal ancestry; see [GuardianManageView](#guardianmanageview) |

Access can change in both directions with the parent class: a user holding only an object grant on a core
parent loses access, a user holding only a model grant on it gains access. Nested Guardian create gains no
model-level `add_<model>` requirement in any mode. `GuardianViewSet.get_objects_for_user()` stays strict; see
[The ViewSet helper is always strict](#the-viewset-helper-is-always-strict).

### Parent-to-child collection links

`ChildContextButton` and child `CardAction` links to Guardian list/card collections check the immediate parent —
the exact parent object used to build their destination URL — with that parent's provider and fallback and the
collection's nearest Read key. For example, a user with `view` on Publisher A can open its detail/card page, but
if the Books child ViewSet declares
`AncestorPolicy(read=AncestorPermissions(nearest="change", higher="view"))`, its Books action is hidden or
disabled and that collection request returns 403. Grant `change` on Publisher A: the action becomes usable and
the collection returns 200, even with no visible Books. A grant on Publisher B does not authorize Publisher A's
link. Farther ancestors are not evaluated while rendering; the collection request still checks them.

This applies to the shipped `GuardianListViewPermissionRequired` and `GuardianCardListViewPermissionRequired`
and compatible queryset compositions supplying the existing parent permission helper. A legal
`GuardianQuerysetMixin` composition without that helper retains its delegated access result after the actor
check; rendering does not add parent authorization to it. Prefer the shipped classes when that gate is required.

For a `GuardianViewSet` parent, object/group grants count, and model-level parent permissions count only with
the parent's `AncestorPolicy(accept_global_perms=True)`; the target view's `cv_guardian_accept_global_perms`
does not apply to the parent. A core `ViewSet` parent is checked with its model permission. Active superusers
retain the existing parent permission behavior. Anonymous and inactive actors are denied for these nested
collection links. A parent with `provider="none"` skips only the parent permission check; actor handling, custom
access denials and the independent `cv_action_enabled` state check still apply. Custom `cv_has_access(user, obj)`
overrides receive the same supplied parent object. Child create links keep their parent/create permission and
state policy, without an additional collection check.

Denied actions use the target's [hide/disable mode](inaccessible_actions.md); disabled actions have the
permission reason and no usable URL. State denial remains separate. The parent is reused without another
parent-row fetch, but Guardian permission queries can still run for each eligible link, including repeated
cards. No permission cache or ancestry lookup is added. Destination request authorization remains authoritative.

#### Limits and configuration failures

The collection-link check does not extend to general `cv_has_access(user, child)` calls, child-page sibling
links, object detail/update/delete/action destinations, independent table columns, permission filters,
navigation, DataPanel/DataView or other off-page callers. In particular, `LinkChildColumn` does not gain this
check. Supplying an explicit parent works for M2M rendering without inferring ancestry or proving child
membership; matching model types likewise does not establish a parent relationship.

A configuration error in the parent check — a required key missing from the parent's permission map, or
authorization records on another database than `default` — raises `ImproperlyConfigured` while the **hosting page renders its child action**, because this collection
rendering path invokes the parent helper. This configuration failure is preserved, not caught or converted to
hidden/disabled output.

[Issue #318](https://github.com/jacob-consulting/django-crud-views/issues/318) supersedes
[#312](https://github.com/jacob-consulting/django-crud-views/issues/312) for the core declaration guard and this
bounded collection-link correction, without resolving all earlier visibility gaps. The independently opt-in
URL helper in [#314](https://github.com/jacob-consulting/django-crud-views/issues/314) remains separate. No public
parent-access or general URL-resolution API is introduced by this correction.

### Custom child-view compositions

Prefer the shipped `Guardian*ViewPermissionRequired` classes. `GuardianParentPermissionMixin` applies Guardian's
actor rules and runs the shared ancestor authorization of the URL ancestors; it does not replace authorization of
the child row or queryset. A custom nested object view must
also include `GuardianObjectPermissionMixin`, and a nested list/card view must include `GuardianQuerysetMixin`,
before the core view class in the inheritance list. For example:

```python
from crud_views.lib.views import UpdateViewPermissionRequired
from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin, GuardianParentPermissionMixin


class BookUpdateView(GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookForm
```

System check `crud_views_guardian.E001` names a missing or unreachable companion mixin. An incomplete or incorrectly ordered nested composition also
raises `ImproperlyConfigured` at request dispatch and permission evaluation, before it can load or mutate child
rows. Nested create views keep their parent permission/state gate without requiring a child-object mixin.
Top-level views retain their existing permission delegation. Custom overrides must preserve cooperative `super()`
calls; the check does not prove that an application override enforces authorization.

## Formset fragments

The AJAX request that adds a formset row runs the same gates as the editor page it belongs to. On a Guardian update
view, a user without the object permission, with a revoked grant, or whose action state is disabled gets 403 and no
row, so the row's choices are never rendered for them. A missing target, or a target under another URL parent, gets
404. See [The AJAX template endpoint](formsets.md#the-ajax-template-endpoint).

## Group Permissions

Guardian group permissions are respected by default (`use_groups=True`).

```python
from guardian.shortcuts import assign_perm

assign_perm(cv_author.permissions["view"], group, author_instance)
```

## Cascading Deletes with Per-Object Permissions

When `cv_show_related_objects = True` on a Guardian delete view, the related objects
list is filtered using per-object `view` permissions instead of model-level permissions:

- Objects the user has per-object `view` permission for: eligible for details within the display budget
- Objects the user lacks per-object `view` permission for: no labels or placeholders; existing aggregate counts remain

The same filter applies to the labels of protected objects (`on_delete=PROTECT`), the objects that block the
deletion. A protected object's label reaches the template only when the user holds `view` on that object, through an
object grant or a group grant. Labels of objects the user may not view are dropped before the template gets its
context, while the page still shows one generic "blocked" notice through `has_protected_objects`. The summary counts
are unchanged. See [Delete protection previews](delete_view.md#protected-objects).

Protected labels are plain text: selected `protected_objects` entries contain exactly `obj` and `url=None`,
regardless of `cv_link_related_objects`. No protected destination lookup or certification runs. Selected cascade
entries retain the existing optional URL hook and ordinary full-page navigation, including from a modal.

The effective Guardian/application filter runs before display selection. `CRUD_VIEWS_DELETE_PREVIEW_LIMIT` defaults
to 50; an unset `cv_delete_preview_limit` inherits it, including ordinary base-view inheritance of explicit values.
A positive integer caps the combined visible occurrences; explicit `None` means unlimited. Protected entries
consume slots first, then depth-first cascades, counting repeats and the root. Hidden ancestors are omitted and
their permitted children promoted. Full summary counts and application redaction remain independent of selection;
selected solo-root details still render with an empty summary. Actual visible overflow shows one
`delete_preview_truncated` notice, separate from `delete_preview_incomplete`; empty cascade details have no frame.
See [display configuration and diagnostics](delete_view.md#display-limit) for raw validation and runtime errors.

Hidden or beyond-cap blockers still prevent deletion and omit the whole form on pages and modals. The cap changes
neither per-object visibility/global fallback nor inspection, providers, authorization or write-time enforcement.
Complete inspection and filtering costs remain; unlimited mode adds all permitted presentation work. Neither
policy bounds total graph memory or total queries. See [attributed component costs](delete_view.md#collection-cost-and-overrides).

Each related/protected model uses guardian's own content type (`GUARDIAN_GET_CONTENT_TYPE`) and a bare
`view_<ct.model>` codename with that model as `klass`. The **delete view's** `cv_guardian_accept_global_perms` enables
the global grant `<ct.app_label>.view_<ct.model>` for labels, independently of access to the deletion target. With the
default concrete resolver, `PublisherProxy` labels consult `app.view_publisher`; `app.view_publisherproxy` alone
does not authorize them. With a polymorphic base-content-type resolver, `Car` labels consult `app.view_vehicle`.
Strict mode ignores global fallback; object/group grants remain effective without global permission. The removed
ViewSet key and the strict ViewSet helper play no part in this projection.

A model without a grantable view permission contributes no ordinary-user labels, without the former lookup
exceptions. Authenticated active superusers retain core-view visibility; inactive users remain denied. Auto-created
through tables are decided without any ContentType lookup or row write: only authenticated active superusers see
their rows. Their projection cache materializes **every PK in the through table**, including unrelated rows, once
per projection, rather than limiting the query to cascade candidates.

Registered Car ViewSets also use Guardian's selected type for inferred defaults: a valid `view_vehicle` grant
under the polymorphic-base resolver works in the strict helper, registered list and object views. Explicit
incompatible mappings still raise `guardian.exceptions.MixedContentTypeError`; see
[Configured content-type defaults](#configured-content-type-defaults). These named controls do not certify every
custom-PK/database-cast/collation combination or resolve the separate unclassified AUTH-06 review predicate.

`GuardianDeleteRelatedObjectsMixin` replaces the core model-level filter rather than adding to it. A custom
`cv_filter_related_objects` on a Guardian delete view should call `super()` (which applies the Guardian filter) and
narrow its result further, never re-run the core model-level filter after it or return the raw collection; see
[Custom related-object filters](delete_view.md#custom-related-object-filters).

```python
class PublisherDeleteView(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
```

Performance: permitted PK sets are cached per `(model, using)` per projection, using bulk
`guardian.shortcuts.get_objects_for_user` filtering. This adds no large-cascade bound; core inspection still
materializes full rows for supported deletion paths even with previews disabled (see
[Collection cost and overrides](delete_view.md#collection-cost-and-overrides)).

### Delete-preview database topology

Candidate rows and their permission queryset are bound to each candidate's `_state.db`. Before ordinary, global,
superuser or through-row fast paths, projection requires the persisted actor to be on that alias, with User, Group,
Permission, ContentType, auth join tables, related-manager queries and configured Guardian user/group permission
tables routed there too. It does not substitute another actor having the same PK. The configured content type must
also belong to that alias; auto-created through rows continue to skip content-type lookup.

An unsupported topology yields no labels, preserving blocked state, completeness and aggregate counts. This is a
conservative display result, not a new authorization policy or general central-auth/multi-database support.
Configured anonymous-object display uses Guardian's resolved anonymous actor under the same checks. Cross-alias
global fallback with unrecognized custom auth backend paths is not certified and yields no labels. Recognized
ModelBackend/ObjectPermissionBackend routes and fresh same-alias actor state are required for that supported path;
request.user is not replaced.

The tested multi-database topology uses independent `default`/`shard` databases with colliding PKs, co-located actor,
auth tables and object/group grants, and request-local routing established before authentication/session middleware.
Positive object/group/global/active-superuser and through-row display is checked on both aliases; independent
misrouting and interleaved-request controls deny labels. Ordered-model sibling queries inside a custom delete method
must follow the same trusted routing. These tests do not promise arbitrary shared-auth schemas, backend SQL paths,
database casts/collations, or cross-database transactions. The broader AUTH-06 residual and Guardian precision
backstop remain unresolved; named integer/UUID/key tests and error characterizations do not close them.

## Working Example

See `examples/bootstrap5/guardian_demo/` for a complete working example. After running
migrations, use the seed management command to set up demo users and data:

```bash
python manage.py seed
```

This creates the `alice` and `bob` demo users and assigns per-object permissions on the
seeded `Document` objects (see `guardian_demo/seed.py`):

| Document          | Owner | alice                | bob                  |
|-------------------|-------|----------------------|----------------------|
| Roadmap 2027      | alice | view, change, delete | —                    |
| Team Handbook     | alice | view, change, delete | view                 |
| Meeting Notes     | bob   | —                    | view, change, delete |
| Release Checklist | bob   | view, change         | view, change, delete |

The seed also creates notes under two documents. `Note` is a nested `GuardianViewSet` under `Document` (see
[Parent Viewsets](#parent-viewsets) above), and each note carries its own object grants:

| Document          | Note                                 | Author | alice                | bob                  |
|-------------------|--------------------------------------|--------|----------------------|----------------------|
| Team Handbook     | "Added the onboarding checklist."    | alice  | view, change, delete | view                 |
| Release Checklist | "Tag the release before publishing." | bob    | view                 | view, change, delete |
| Release Checklist | "Changelog reviewed."                | alice  | view, change, delete | view, change, delete |

Listing a document's notes needs `view` on the document and adding one needs `change` on it, so bob reads the
Team Handbook's notes but cannot add one.

## GuardianManageView

When `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` is enabled (or a user is in the `CRUD_VIEWS_MANAGE` group), guardian-enabled viewsets show an enhanced manage page at `/<prefix>/manage/`.

Every manage page, core and Guardian, shows an **Ancestor policy** table: the ViewSet's declared values next to
the effective ones. "As an ancestor of nested requests" lists `provider` and `accept_global_perms`; "Requests to
this ViewSet" lists `cascade`, the `read` and `write` pairs and each exact `actions` entry, or states that they
do not apply to a top-level ViewSet. A template reads the same values from the `ancestor_policy` context entry
(`as_ancestor` and `requests`; `requests` is `None` at top level). It is configuration only, not an access result
for the current user.

In addition, GuardianManageView adds:

**Guardian Configuration** — the `guardian_config` context entry:

- `parent_viewset` — the parent ViewSet's name with its effective ancestor provider and whether it adds the model
  fallback, e.g. `publisher (ancestor provider: guardian + model fallback)`; `None` at top level
- `ancestor_policy` — this ViewSet's effective ancestor `provider` and `accept_global_perms`, the same values as
  the core entry
- `get_objects_for_user` — the helper's fixed strict policy (object and group grants only)

The removed `cv_guardian_parent_permission` and `cv_guardian_parent_create_permission` rows are gone.

**Global permission fallback** — one row per registered view with its own `cv_guardian_accept_global_perms` and the
effective policy:

| Effective policy | When |
|---|---|
| strict | the view has its own object gate or list filter (object or queryset mixin), and its flag is `False` |
| global fallback | the same, with the flag `True` |
| not applicable | the view never consults the flag: a plain or manage view, or a create view (top-level or nested); ancestors use the ancestor policy instead |

The values come from each view class, never from the ViewSet. Below the table the page states that
`get_objects_for_user()` is independent of these view policies and always strict.

A template that overrides the manage page reads the values from the context: `guardian_config.get_objects_for_user`
holds `{"policy": "strict", "accept_global_perms": False, "use_groups": True}`, and each `views.<key>.guardian_policy`
holds `global_fallback_applicable`, `cv_guardian_accept_global_perms` (`None` when not applicable) and
`effective_policy` (`"strict"`, `"global fallback"` or `"not applicable"`). The `guardian_config` key
`cv_guardian_accept_global_perms` is gone.

Who may open the manage page locally has not changed: `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (`"yes"`, `"debug_only"`
with `DEBUG`, or `"no"`) and membership of the `CRUD_VIEWS_MANAGE_GROUP` group (default `CRUD_VIEWS_MANAGE`)
still decide, not object permissions. A **nested** manage page is a Read endpoint and additionally passes normal
ancestor authorization first: a public manage setting or manage-group membership does not bypass the ancestors,
and an ancestor grant does not bypass the manage setting or group.

**Permission Holders** — extends the standard group listing with an "Objects (guardian)" column showing how many objects each group has per-object access to.

**Views table** — each registered view shows a `guardian_mixin` row listing which guardian mixins are active (`ObjectPermissionMixin`, `QuerysetMixin`, `ParentMixin`).

GuardianManageView is wired automatically by `GuardianViewSet.register()` — no manual configuration required.

### Customizing the Manage View Class

To use a custom manage view class for a specific viewset, set `manage_view_class` to a dotted import path:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet


class MyCustomGuardianManageView(GuardianManageView):
    template_name = "myapp/custom_guardian_manage.html"


cv_author = GuardianViewSet(
    model=Author,
    name="author",
    manage_view_class="myapp.views.MyCustomGuardianManageView",
)
```

To apply a custom class globally to all guardian viewsets, set in `settings.py`:

```python
CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS = "myapp.views.MyCustomGuardianManageView"
```

The per-viewset `manage_view_class` field takes priority over the global setting.

For plain `ViewSet` (non-guardian), the equivalent is:

```python
CRUD_VIEWS_MANAGE_VIEW_CLASS = "myapp.views.MyCustomManageView"
```

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).
