# Manage diagnostics

The manage page is a read-only developer view of permissions and configuration. It requires an active,
authenticated member of `CRUD_VIEWS_MANAGE_GROUP`, including staff and superusers, and an enabled manage mode.
Nested pages also enforce their ancestors before reading diagnostic auth/grant data. See
[manage access and group setup](settings.md#manage-diagnostics). The optional [Access check](#access-check)
card adds diagnostics without changing those hosting-page access rules.

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
arbitrary object. Use [Access check](#access-check) or [cv_access](#cv_access) for a concrete URL's result.
Neither changes the signed-in user or creates an impersonation session.

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
The one context value `manage_docs_base_url` supplies every card/section link. Preserve the eleven unconditional
help anchors above in your hosted page, plus `access-check` when the opt-in card is enabled. See
[the public template and builder inventory](theme.md#structured-manage-contracts).

## Access check

Set `CRUD_VIEWS_MANAGE_ACCESS_TRACE = True` to show the Access check card under Permissions. Its default is
`False`: no card is rendered and all `cv_access_*` GET parameters are ignored. The command below is unaffected.
When enabled, anyone admitted to the hosting manage page may trace any user and any project CRUD path,
including paths whose ancestors the viewer cannot open. The hosting page still requires its normal developer
group, mode and ancestor checks. Opting in deliberately discloses object existence and another user's access
(for example, not found versus denied). Object identities contain only model and PK, not titles or content;
exception class/message disclosure can still expose information supplied by project code.

Both linkable GET forms use a typed **username or primary key**, with no user picker. A matching username wins
over another user's matching PK in both forms. Unknown users produce feedback and no trace. Inactive users are
accepted as inputs; the real gates decide their result. Only the CLI offers an anonymous selector.

- **For this ViewSet:** enter a user and optionally an object PK. This replaces only the Permissions actor row
  with **Access for: username (checked below)**, using the existing effective model permissions and strict Guardian
  counts. The viewer/session and holder rows stay unchanged. Every registered view appears, including backend-only
  and POST-only views, with an expandable trace. An object view without a PK says **needs an object pk**.
  Extra URL arguments (such as child redirects or polymorphic create), or an invalid PK converter value, say
  **use the path field**. Nested parent coordinates come from the hosting manage URL, never from form inputs.
- **For any URL:** enter a user and project path, or a full URL whose path is used. This returns one full trace
  without replacing the Permissions actor row. No request is sent to the supplied host.

The form parameters are `cv_access_mode` (`viewset` or `path`), `cv_access_user`, `cv_access_pk` and
`cv_access_path`. Empty, invalid and unknown-user submissions keep the viewer's matrix row. Native disclosures
work without JavaScript. Both forms share the command's trace semantics below.

## cv_access

Trace authorization through real dispatch and a stub handler:

```bash
python manage.py cv_access /customer/5/order/12/update/ sam
python manage.py cv_access /customer/5/order/12/update/ 42 --as-json --no-color
python manage.py cv_access 'https://example.com/customer/5/order/12/update/?page=2#item' sam
python manage.py cv_access /author/list/ --anonymous
python manage.py cv_access /author/list/ sam --as-json | jq
```

Replace paths/users with your project's routes and accounts. Users are loaded fresh from the project's user
model; username matches take precedence over primary keys, including numeric usernames. Supply either a user
selector accepted by the username field or the primary key; a username conversion failure still permits the
primary-key lookup. Unknown selectors produce normal command/form feedback. Supply either a user
or `--anonymous`, never both. Full URLs are reduced to their path: host, query and fragment do not affect tracing.
The extracted URI path is decoded once, as for a Django request, including URLs returned by `reverse()`.
Literal plus signs stay unchanged; encoded question marks, hashes and percent signs remain path content.
Text output contains Path, Route, View and User headers, a declaration-only Plan, numbered Steps, Limitations
and the outcome with its deciding step. An allowed trace ends with:

```text
This user may open the page; handler-phase checks are not evaluated.
```

Terminal output uses green for passed/allowed, red for denial, dim for skipped/not reached, and yellow for errors.
JSON colors keys and result/outcome values. Ordinary pipes and `--no-color` are uncolored; `--force-color`
explicitly enables ANSI colors even in a pipe, so do not force color when a JSON parser expects plain JSON.
The command uses fixed colors once Django enables coloring, not the configurable `DJANGO_COLORS` role palette.

### Outcomes and streams

| Outcome code | Exit | Meaning |
|---|---|---|
| `allowed` | `0` | May open the page; handler-phase checks remain unevaluated. |
| `denied` | `1` | An observed authorization refusal (403). |
| `not_found` | `1` | A lookup/refusal raised or returned 404. |
| `login_redirect` | `1` | A recognized actual login response, not an arbitrary redirect. |
| `error` | `2` | Exception or unsupported response, with class/message evidence. |
| `no_such_route` | `2` | Path does not resolve to a CrudView. |

Traces go to stdout in both formats, including denied/not-found/error traces; the nonzero status does not add
another error line. An unknown user or wrong invocation produces a diagnostic on stderr and no trace document
(exit 2), even with `--as-json`. Text no-route output is the one-line stderr message
`No such CRUD view route: /missing/`. JSON no-route output is a full stdout document, with empty stderr.
For an unresolved `/missing/`, `python manage.py cv_access /missing/ --anonymous --as-json --no-color` emits:

```json
{
  "path": "/missing/",
  "route": null,
  "view": null,
  "user": {"pk": null, "username": null, "active": false, "anonymous": true},
  "outcome": "no_such_route",
  "decided_by": 1,
  "plan": [],
  "steps": [{"n": 1, "kind": "route", "viewset": null, "object": null, "key": null,
    "permission": null, "group": null, "provider": null, "source": null, "result": "not_found",
    "how": null, "message": null, "exception": null, "counts": null}],
  "untraced": ["other middleware and URL decorators are not traced",
    "the synthetic request uses http://localhost; host-dependent project rules are not reproduced"],
  "version": 1
}
```

### Version 1 document

`crud_views.lib.access_trace.trace_access(path, user)` returns an `AccessTrace`; `to_dict()` projects only
JSON-compatible scalar data. `user=None` selects anonymous. `resolve_trace_user(identifier)` uses the same
username-first lookup and returns a fresh user or `None` when unknown. CLI/web resolve unknown inputs before
tracing. Check `version` before consuming the result. Codes are stable English identifiers; messages are translated.

| Field | Meaning |
|---|---|
| `version` | Integer `1`. |
| `path` | Normalized project path. |
| `route` | Resolved route name, or null. |
| `view` | Dotted resolved view class, or null. |
| `user` | Mapping with string/null `pk`, string/null `username`, boolean `active` and `anonymous`. |
| `outcome` | One of the six outcome codes above. |
| `decided_by` | One-based deciding step number, or null. |
| `plan` | Ordered declaration-only requirement mappings; may contain unavailable metadata. |
| `steps` | Ordered `AccessStep` mappings, including unreached and unevaluated steps. |
| `untraced` | List of human-readable diagnostic limitations. |

### Step fields

All step fields are present, with null for inapplicable data. Plan rows use a subset of these descriptive fields
without a step number; plans describe intended requirements, not evidence that a gate ran. Permission codenames
may stay null for unreached requirements even when their keys/source are known.
The stock Django permission hook reports the permission it already read from the library's cached property.
Overridden `get_permission_required()` hooks or `permission_required` properties remain opaque: the trace
records their gate result without evaluating another requirement source or calling the hook again.

| Field | Meaning |
|---|---|
| `n` | One-based step number. |
| `kind` | Observation kind from the vocabulary below. |
| `viewset` | ViewSet name, or null. |
| `object` | Identity mapping with `model` label and string/null `pk`, or null; no object title. |
| `key` | Requirement, action or limitation key, or null. |
| `permission` | Full permission codename, or null. |
| `group` | Required group name, or null. |
| `provider` | Owning permission provider, such as `model`, `guardian` or `none`, or null. |
| `source` | Requirement declaration or observed callable provenance, or null. |
| `result` | Step result code, or null. |
| `how` | Observed branch explanation code, or null; not a second permission decision. |
| `message` | Human-readable explanation, or null. |
| `exception` | Mapping with `class` and `message`, or null; no traceback. |
| `counts` | Mapping with integer `visible` and integer/null `total`, or null. |

Kinds are `route`, `validation`, `actor_admission`, `ancestor_lookup`, `ancestor_gate`, `own_permission`,
`object_lookup`, `object_grant`, `list_filter`, `action_state`, `manage_gate`, `custom_gate`, `login_middleware`
and `limitation`. Step results include `passed`, `denied`, `not_found`, `login_redirect`, `error`, `skipped`,
`not_reached`, `not_evaluated` and `unavailable` (planning metadata). Use codes for scripts and message text for
people. Sources retain requirements such as `ancestor_policy.read` or configured action/global defaults.
Observed `how` values include `anonymous`, `inactive`, `active`, `no_rule`, `disabled`, `group_member`,
`not_member`, `observed_boundary`, and Guardian's `object grant`, `model fallback`, `active superuser`.
The last three describe the real successful grant branch, including direct/group grants, not another permission probe.

### Custom method boundaries

A `custom_gate` source identifies the class/method of the actual observed bound callable, with
`how=observed_boundary`. Its message says the inner denying implementation is unknown. Inner `super()` calls
and multiple project overrides are opaque: the named class is not proof of the inner culprit. Even an inherited
library method may be the observed boundary above an uninstrumented refusal. If an instrumented gate reports
the deciding refusal, its evidence is retained instead. This diagnostic does not inspect arbitrary project code.

### List count boundary

Guardian's **sees n of m objects** reports pre-context counts: `total` is the actual pre-Guardian queryset,
and `visible` is the final get_queryset return, including outer project filtering. These counts exclude later
`_scope_child_queryset` parent scoping, pagination and rendering filters. A project override omitting the parent filter
can therefore yield more traced rows than the page renders. Default ViewSet querysets already carry parent filtering.
For example, an unscoped four-row queryset may report **sees 3 of 4 objects** while context parent scoping leaves
two rendered rows. Counts describe this boundary, not the rendered page. Resource lists report only their row count
(`visible`, with `total=null`), because no Guardian filter comparison exists.

### Diagnostic limits

Tracing calls real authorization gates with a synthetic GET and a stub handler. It does not render the page,
submit a form or execute an action. Ordered ancestor failures stop deeper lookups; a missing deeper object is
not probed after an earlier denial. Protected core/Guardian gates enforce their own active-user rules; a plain
unprotected view can admit an inactive user. Guardian list admission still includes actor, ancestor and state
checks: an admitted list can be allowed with zero visible objects. A nested Guardian create checks its parents
and parent action state, without inventing a child-object or child-model add permission.

The trace always rolls back its **default-database transaction**, using a savepoint inside an existing transaction.
It leaves no saved session and no delivered messages. This is not a cross-database or external-service sandbox:
project gates/loaders may read external services, write another database or cause external effects. Process state,
including process-wide caches populated during a trace, is not rolled back. Review project hooks before treating
the tool as free of external side effects.

The synthetic origin is `http://localhost`, with an empty query, no submitted body and no caller-supplied headers
or project middleware context. Full-URL input does not recreate its host or original request. Host-, header-,
query-, body- or method-dependent project rules may therefore differ. Custom methods are opaque at the
[observed boundary](#custom-method-boundaries); arbitrary returned responses (including an early 200 or an
unrecognized redirect) yield `error` with `UnsupportedTraceResponse`, not a fabricated allowed/login result.
POST-only and action endpoints use an authorization-only GET-stub adaptation: their real POST handler and
method-sensitive behavior are not evaluated, and this is not a claim that a real GET would avoid 405.

Steps with `result=not_evaluated` identify applicable handler-phase checks:

- The selected **workflow transition** permission is checked on submit.
- The **nested-list** database configuration check happens when the page is built.
- The **delete-preview** configuration/database check happens when the page is built.
- Database configuration for nested **form/action/workflow writes** is checked on submit.

These limits are distinct from [pre-context list counts](#list-count-boundary); changing a count does not execute
the later database check. Allowed means **may open the page**, not permission to perform every submit operation.
Real Resource `cv_get_item()` / `cv_get_items()` loaders run under the fresh traced user, including external reads,
missing-item and action-state behavior; Resource lists report row counts. No Resource manage page is created.

When installed, Django's `LoginRequiredMiddleware` or its subclass runs its real `process_view()` with the
resolved view. The rest of the middleware chain does not run: **other middleware and URL decorators are not traced**.
The result exposes identity-only model/PK values with no object title or rendered content, but an exception class
and message is deliberately included. Project exception messages may contain sensitive data; no traceback is emitted.
