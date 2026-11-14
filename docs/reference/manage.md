# Manage diagnostics

The manage page is a read-only developer view of permissions and configuration. It requires an active,
authenticated member of `CRUD_VIEWS_MANAGE_GROUP`, including staff and superusers, and an enabled manage mode.
Nested pages also enforce their ancestors before reading diagnostic auth/grant data. See
[manage access and group setup](settings.md#manage-diagnostics). This page adds no settings or access exceptions.

Permissions and Views occupy the main column; supporting cards stack beneath them on narrow screens.
Each card's **?** link opens its section here in a new tab. Links are keyboard focusable, have a descriptive
accessible name, and use `target="_blank" rel="noopener"`. Requirement badges are not links: use the Views
help link and its footer key. Native disclosure summaries remain a single keyboard/click target.

## System checks

Checks run for this ViewSet on page load. With no messages, the side strip says
“no issues · n system checks for this ViewSet”. Messages appear above Permissions with severity, check ID,
message and any hint. The scope includes `viewset.checks()` and the separately registered ancestor,
conditional and icon checks; Guardian adds its composition check. IDs in `SILENCED_SYSTEM_CHECKS` are omitted.
The count measures only the materialized `viewset.checks()` entries, not the additional collectors.
Project-wide settings, assets and class-registry checks are outside this card: it does not replace `manage.py check`.

## Permissions

Each column is a key from `viewset.permissions`, with its Django codename below it. Custom permissions are
included. A **model** cell means a model-level permission; **n objects** means Guardian object access/grants.
A dash means neither is shown. These two badges can coexist.

- **Access for: username (you)** is the signed-in actor's effective result. Model permission uses `user.has_perm()`,
  including groups and active-superuser status. Guardian counts use the strict helper, including group grants.
- **Groups** and **Users** describe direct holders, identified by primary key. A user's inherited group rights
  belong in the group's row, not another direct-user row. Every group shows its member count.
- Users appear only with `CRUD_VIEWS_MANAGE_SHOW_USERS=True` (default `False`). The first 20 rows are visible;
  remaining rows fold into a native **+ n more** disclosure. Hidden users' names are not embedded in hidden markup.
- The active-superuser count is always shown. Their names appear only when SHOW_USERS is on. Inactive superusers
  do not count. This explains why a permission without direct holders can still be effective for an actor.

Empty states say “No permissions configured.”, “No groups hold these permissions directly.” or
“No users hold these permissions directly.” as applicable. For Guardian, counts follow the configured generic
or direct-foreign-key user/group permission models. The actor's count is effective access; holder counts are
direct grants, not a claim that all holder accounts can currently log in.

Strict means **no global model-permission fallback**, not “ignore superusers”: Guardian's active-superuser
all-object shortcut remains. A strict object count can therefore cover every object for an active superuser.
See [Guardian helper policy](guardian.md#guardianmanageview). This is not a per-view access result for an
arbitrary object, and no another-user form, impersonation or access-trace command is provided.

## Views

Each registered view has a closed native disclosure at `#cv-view-<key>`. The summary shows its key, relative route,
real dotted class path and requirement badges. Permission badges name a permission key; group badges name the
required group; neutral badges say “no permission required” or “custom”. Parent badges describe the nearest
applicable ancestor requirement. Tooltips carry full permission/group explanations, with textual and screen-reader
labels so color is not the only meaning. Guardian adds **strict**, **global fallback** or **not applicable**.

Expanded rows are grouped into Navigation, Templates, Icons, Guardian where applicable, then Other. Other
includes remaining `cv_*` data attributes, excludes methods/descriptors and `cv_viewset`, and marks unknown names.
Keys omit `cv_`; classes retain dotted paths and other values use shortened, escaped representations.
An annotated attribute without a value says “not declared”. Malformed requirement metadata is explicitly
reported rather than treated as proof of access; endpoint validation and authorization remain independent.

A value is **set** when a project class declares it in its own namespace, including inherited project
declarations. Classes in `crud_views*` packages count as library defaults, as in W280. Registration records
project declarations before adding the automatic manage action, so that addition is not misreported as a project
choice. Effective fallbacks have a separate source label, such as ViewSet or a setting. Settings copied into
library class attributes still count as defaults.

One **Show defaults** switch controls Views and Presentation. With JavaScript, default rows start hidden and
sections report **n defaults hidden**. Without JavaScript, every row remains visible after opening its native
disclosure. Defaults have muted values and stronger keys; the switch choice is not saved. The external
`manage.js`/`manage.css` assets need no inline scripts, inline event handlers or inline styles, preserving the
existing [CSP boundary](settings.md#content-security-policy-csp). Badges keep native `title` help without JS;
the existing tooltip adapter owns enhanced tooltips.

## Presentation

This closed disclosure describes ViewSet-wide presentation: context-button targets, templates/actions, label
modes and the effective manage class. Its summary counts set/default entries. It shares the Views default switch.
The header help link is a sibling of the summary; scoped `::details-content` styling exposes it while closed in
supporting browsers. Older browsers can reach it after expanding the card.

Context-button rows show key, type, target and label without evaluating runtime access or calling dynamic labels.
Built-in context, parent, child, sibling and filter buttons use their declared target fields. Top-level parent
buttons say “top level, never shown”. Custom renderers fall back to type/template information. Child and sibling
targets are descriptions, not sample-object links. A view's `context_actions` selects which buttons appear;
view-specific `cv_context_buttons` is in that view's Other section. See [Context Buttons](context_buttons.md).

## ViewSet

Identity includes name, model dotted path, prefix, app, `pk`/`pk_name`, verbose names, ordering and the rendered
header icon plus its name. Effective values retain their source, such as model Meta or a setting.
A ViewSet field counts as set only if passed to its normal constructor; validator-inferred fields are defaults.
Constructor declaration provenance does not support Pydantic `model_construct`, which bypasses that record.

## Hierarchy

Parents show the full chain upwards. Their manage links use coordinates already present in the current URL;
no sample object is fetched. If required coordinates are unavailable, the route remains descriptive.
Children show model, manage URL name and relative pattern without links. To open a child's manage page,
open its list under a parent object and use the manage action. A Resource child says “Resource, no manage page”.
No Resource manage route is introduced. See [Nested ViewSets](nested.md).

## URL names

Each row shows the registered URL name and readable route, **relative to where the ViewSet is included**.
A project `include()` prefix is not known to the ViewSet and is not invented here. The same generated routes
appear in view summaries and button target descriptions. Parameters such as `<pk>` describe coordinates;
they are not links or chosen database objects.

## Ancestor policy

The card at `#cv-ancestor-policy` has two parts: **As ancestor of nested requests** and **Requests to this ViewSet**.
Each row shows a setting and its effective value, with an inherited marker where nothing is declared. There is
no separate Declared column. Top-level request policy is not applicable. This is **configuration only, not an
access result**. Endpoint requirements and ancestor policy remain independent; see
[Ancestor authorization](nested.md#ancestor-authorization).

## Guardian

Guardian pages use the same cards and add a compact **get_objects_for_user (strict)** card. Its helper policy is
`{"policy": "strict", "accept_global_perms": False, "use_groups": True}`. It excludes global fallback and includes
group grants, while retaining Guardian's active-superuser all-object shortcut. Hierarchy and ancestor policy
carry parent/provider information; this card does not repeat it.

Each view's own fallback policy appears in its summary badge and expanded Guardian section alongside its mixins.
An object gate or queryset filter can be strict or accept global fallback. Plain/manage/create views that do
not consult the flag show not applicable. A nested Guardian create describes its parent requirement; detail,
update and delete retain their own object permission too. See [GuardianManageView](guardian.md#guardianmanageview).

## Templates and actions

Presentation shows effective `extends`, `inaccessible_actions`, and context/list/card action-inline lists.
An explicit empty `extends` still uses the runtime setting fallback; its row preserves the explicit empty
`declared_value` separately from that effective value/source. See [Base template](templates.md) and
[inaccessible actions](inaccessible_actions.md).

## Label modes

Presentation reports effective context, list and form label modes with their sources. It does not change how
buttons resolve their label mode. See [Label mode](action_menus.md#label-mode).

## Documentation base

Stock help links use `https://django-crud-views.readthedocs.io/en/stable/reference/manage/`.
Before a release, the new sections may not exist on `stable` yet. Projects hosting their own documentation can
override one class attribute using the existing `manage_view_class` option; no new Django setting is needed.

```python
# myapp/views.py
from crud_views.lib.views.manage import ManageView


class ProjectManageView(ManageView):
    manage_docs_base_url = "https://docs.example.com/reference/manage/"


# Pass manage_view_class="myapp.views.ProjectManageView" to your ViewSet constructor.
```

For Guardian, subclass `crud_views_guardian.lib.views.GuardianManageView` instead. Existing global
`CRUD_VIEWS_MANAGE_VIEW_CLASS` / `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS` configuration also applies.
The one context value `manage_docs_base_url` supplies every card/section link. Preserve all 11 anchors above in
your hosted page. See [the public template and builder inventory](theme.md#structured-manage-contracts).
