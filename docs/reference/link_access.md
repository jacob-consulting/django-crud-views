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

The regular enum has three distinct members: `LinkAccess.ALLOWED`, `LinkAccess.DENIED_PERMISSION` and
`LinkAccess.DENIED_STATE`. Only `ALLOWED` is true in a boolean check. Compare enum members to distinguish
the two false denial results; members are not interchangeable with raw strings.

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
