# Link access

Use `check_link_access` to decide a link from a target view class, a user and objects you already have.
It checks parent gates, own permission and then state; it does not authorize a request or load objects.

```python
from crud_views.lib.link_access import LinkAccess, check_link_access

# Signature: check_link_access(target, user, *, obj=None, known_ancestors=()) -> LinkAccess
```

`target` and `user` can be positional or keyword arguments. `obj` and `known_ancestors` are keyword-only.
Pass known ancestors as a list or tuple, nearest first and aligned with the target's declared ancestry.
The function takes no request or rendering view.

The function, argument convention and result behavior are **stable at 1.0**, as listed in the
[public API inventory](../development/stability.md). There is no convenience import from `crud_views.lib`.

## Results

`LinkAccess` is a regular enum with exactly three members:

| Member | Meaning | Boolean value |
| --- | --- | --- |
| `LinkAccess.ALLOWED` | Permission and state passed | `True` |
| `LinkAccess.DENIED_PERMISSION` | A permission gate denied; state was not asked | `False` |
| `LinkAccess.DENIED_STATE` | Permission passed, but state denied | `False` |

Both denial members are false. Use `if result` for allowed-only presentation, or compare enum members
to distinguish outcomes. Members are not interchangeable with raw strings. Enum `.value` and construction
from private strings are not a supported serialization contract.

## Caller inputs and validation

The `target` must be a view class registered with a ViewSet, not a constructed view. A target without a
ViewSet, view instances and other non-class inputs raise `django.core.exceptions.ImproperlyConfigured`.
Pass `known_ancestors` as a finite ordered list or tuple; unsupported containers, including `None`,
iterators and QuerySets, raise before inspection or evaluation. Omitting it uses the empty tuple.

The function performs complete validation before authorization, independently of the actor or grants.
Caller-input error messages start with `check_link_access`. In addition to the class, ViewSet and container
requirements above, these six mismatches raise `ImproperlyConfigured`:

1. An ancestor does not fit its declared level, even behind a nearer `None` slot.
2. The own object does not fit the target's model or Resource class.
3. There is no own object for an object target (`cv_object=True`).
4. There is an own object for a collection target (`cv_object=False`), including list and create targets.
5. There are more ancestor slots than declared levels; every slot counts, including trailing `None`.
6. There is any ancestor slot for a top-level target, including `[None]`.

Type compatibility uses `isinstance` against the declared level's concrete model. A compatible proxy,
ordinary multi-table child or polymorphic subclass is accepted. A base or sibling instance is not accepted
for a narrower child-model target. For a Resource target, the own object must be an instance of its
Resource class (or a subclass); ancestors must belong to model ViewSets.

An unsaved own model instance is accepted when its type fits, whether its primary key is absent or already
assigned. Validation does not save or reload it. This does not guarantee permission or request success:
the reached backend and hooks still decide, and their errors still propagate.

Ancestors are nearest first and aligned with the target's declared ancestry. A short list and unknown
higher slots (`None`) are valid: they remain unchecked and never shift farther objects into nearer slots.
A missing immediate parent yields `LinkAccess.DENIED_PERMISSION` after validation, even if a higher object
was supplied. Supply only objects you already have; there is no object or ancestor loading by the checker.
Existing authorization queries and project hook work may still run, so this is not a blanket zero-query promise.

## Evaluation and errors

The order is **parent gates → own permission → state**. Declared policy selects which known ancestor
gates apply; supplied selected higher gates run outermost first. A permission denial skips state.
The state hook `cv_action_enabled(user, obj)` receives:

| Target | State-hook object |
| --- | --- |
| Object target | Its supplied own object |
| Nested collection (list or create) | Its supplied immediate parent |
| Top-level collection | `None` |

Every nested Guardian target requires a signed-in, active user, including under a parent with provider
`none`; grants or a permissive create override cannot bypass that admission. The anonymous top-level
Guardian list remains allowed by its default permission behavior (a custom state hook can still deny).

Actor admission and declared parent gates precede a nested Guardian create's `cv_create_has_access`.
A denied gate skips the hook; a false hook still denies after the gates pass. The public checker supplies
`None` as the rendering view. A rendering-view-dependent override can therefore answer differently than
a package button on the same page, where the package can supply the real view of the target's ViewSet.

Errors are not converted to denial results:

- A broken declared ancestry can fail during validation with its own message, rather than the public
  caller-input prefix.
- A reached gate can raise `ImproperlyConfigured` for a missing ancestor permission key or a view without
  operation requirements. A missing own permission key denies instead of raising.
- Reached nested gates can raise the database configuration error described below.
- Arbitrary project hook exceptions propagate, including exceptions for otherwise type-compatible
  unsaved inputs.

Input and gate errors share the existing `ImproperlyConfigured` exception type; no new exception class
distinguishes them. The public input prefix is the diagnostic distinction.

### Database checks at reached gates

The existing error says `nested ViewSets support only the 'default' database`. It is a reached-gate rule,
not an unconditional validation of every supplied object's database:

| Reached gate | Authorization database checks | Object database check |
| --- | --- | --- |
| Nested ancestor gate with a non-none provider | Actor and authorization tables | Supplied ancestor object |
| Nested permission-enforcing core own gate | Actor and authorization tables | No own-object database check |
| Nested permission-enforcing Guardian own gate | Actor and authorization tables | Supplied own object |

Core own permission does not inspect its own object's database. Guardian's own-object check applies
when the object permission gate is reached. Top-level targets do not run these nested database checks;
a denied actor or earlier gate can stop evaluation before a later check. Unknown or unselected ancestor
gates do not perform these checks, and a provider-`none` ancestor has no such database check.
The public wrapper preserves each gate's existing order; it does not promise that all actor denials
precede all configuration errors.

## Limits and custom callers

An allowed link does not authorize a request. It does not establish membership, consult ViewSet querysets,
run project `dispatch` or `has_permission`, or account for middleware. For example, supplying a child with
another parent is accepted by input validation when both types fit; the request may return 404 because
that child does not belong to the supplied parent or is outside the ViewSet queryset.

On a CRUD page, a project has `cv_get_parent_object` but no public accessor for resolved higher ancestors.
A custom button supplying only that parent can differ from a package button when the target asks a
stricter higher-level permission than the page. Unknown levels stay unchecked; the function does not
discover a full hierarchy for the caller.

The [parent-only non-create limitation](guardian.md#parent-only-non-create-limitation) also applies:
an ordinary link can be hidden even when the request would allow it. Cancel retains its documented
special handling for that shape.

The permission-only function stays private. Templates can use
[`cv_context_has_permission`](context_buttons.md#cv_context_has_permission-gate-surrounding-markup)
for permission-only decisions; it never evaluates state. Use this public full checker when custom Python
code needs both permission and state. Independent table columns (`LinkChildColumn` included), DataPanel/DataView,
breadcrumbs and site menus do not automatically adopt it; project use is opt-in.

## Object target

Here `TargetView` is a registered Book detail view under a Publisher ViewSet. `user` is an authorized actor,
and `book` and its `publisher` are already loaded. Supply the own object separately from its ancestors:

```python
from crud_views.lib.link_access import LinkAccess, check_link_access

result = check_link_access(TargetView, user, obj=book, known_ancestors=[publisher])
if result == LinkAccess.ALLOWED:
    show_link = True
else:
    show_link = False
```

## Nested collection

Here `BookList` is a registered core Book list view nested under a Publisher ViewSet. `user` has the
required parent permission and the list's state permits access. `publisher` is the already-loaded route
parent. A list has no own object, so omit `obj`; its state hook receives the publisher:

```python
from crud_views.lib.link_access import LinkAccess, check_link_access

result = check_link_access(BookList, user, known_ancestors=[publisher])
show_link = result == LinkAccess.ALLOWED
```

## Off-page caller

A dashboard or background caller can supply its own loaded ancestors without constructing a request or
view instance. Here `NoteList` is a registered Guardian BookNote list view in a Publisher → Book → BookNote
hierarchy with cascading ancestor checks. `user` is signed in and active, has `view` grants on the loaded
`book` and `publisher`, and passes the list's state hook. The Book is the immediate parent; Publisher is
the next level. No own BookNote is needed for this collection target:

```python
from crud_views.lib.link_access import LinkAccess, check_link_access

result = check_link_access(NoteList, user, known_ancestors=[book, publisher])
if result:
    show_link = True
else:
    show_link = False
```
