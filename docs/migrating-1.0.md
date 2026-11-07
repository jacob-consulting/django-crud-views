# Migrating to 1.0.0

1.0.0 collects the breaking changes and theme-compatibility work of 0.30.0 and of the releases since. This page is
the route from **0.29.x** to 1.0.0. The [CHANGELOG](https://github.com/jacob-consulting/django-crud-views/blob/main/CHANGELOG.md)
stays the complete record, ordered by release and issue; this page orders the same changes by what you have to
touch.

## Object-detail values and help

Object-detail presentation (#327) changes three defaults: scalar model choices show readable
labels instead of stored codes; automatic model help is hidden; and stock char/text/default
leaves show the muted em dash for `""` as well as `None`. Rows, titles and explicit detail
remain. Zero, False and whitespace-only strings are still values. No data migration is needed.

Restore automatic terminal-field help project-wide in Django settings:

<!-- object-detail-value-recipe: restore-project-help -->
```python
CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
```

Or opt in for one view using an existing Book `cv_book` ViewSet:

<!-- object-detail-value-recipe: restore-view-help -->
```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired


class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_object_detail_show_help_text = True
    cv_property_display = [{"title": "Book", "properties": ["title", "publisher__name"]}]
```

Use `cv_object_detail_show_help_text=False` to hide automatic help on one view, or `None`
to inherit the project setting. Property `detail=True` forces terminal help;
`detail=False` or `detail=""` suppresses it. Omitted/None inherits and explicit nonempty/lazy
text wins. See the [exact precedence and cached setting lifetime](reference/object_detail_settings.md#help-text-precedence).
Intermediate relationship help is no longer a fallback for missing terminal help.

Restore stored-code presentation per property; explicit `type` alone does not opt out:

<!-- object-detail-value-recipe: restore-raw-choice -->
```python
from crud_views_object_detail.lib import x

process_property = x("process", choices_display=False)
```

There is no project/view choice-display switch. Scalar string/integer/boolean choices and
terminal scalar choices across FK/O2O paths are supported; collection choice mapping remains
unsupported. See [raw/display ownership and missing-owner semantics](reference/object_detail_configuration.md#choice-labels-and-raw-values).

### Copied value templates

Update copied `char.html`, `text.html` and `default.html` leaves to use `display_value` for
output and the exact `is None or == ""` check. Keep `text.html`'s existing newline filter
branch. Execute/adapt the [copied text leaf](reference/object_detail_configuration.md#copied-text-value-template).
For badges use the updated [native badge recipe](reference/object_detail_badges.md#native-semantic-badge-template):
retain the raw `value is None` guard and truthy `prop.badge_label` override, then fall back
to `display_value`. Do not apply the text empty-string marker to badges.

`value` and `prop.value` stay raw for custom templates, badge maps/functions and links;
`prop.choice_label` and `display_value` are separate presentation data. Explicit property
templates still own their output (after resolved badges). Keep autoescaping enabled and do
not mark model labels/help safe. Consumer-owned templates and group filtering are not removed
automatically. Subclass complete object-detail views directly; see the adjacent
[composition warning and core/Guardian/polymorphic examples](reference/object_detail_view.md#compose-pattern-guardian-polymorphic).

## Workflow validation and database alignment

Workflow validation/execution (#322) adds `workflow_check_transition(self, name, *, user)`, public
`run_transition(object, name, *, user, comment=None)` and opt-in `cv_transition_presentation="buttons"`.
The [complete adoption recipe](reference/workflow_view.md#business-validation-and-native-transition-buttons)
keeps existing form subclasses and the default page permission. These additive APIs do not require switching
an existing radio view to buttons. `WorkflowForm.clean()` now returns the cleaned mapping for subclasses.

### Align workflow reads, actor identity and writes

**Before:** workflow operations used unbound managers and could follow separate object read/write, history and
content-type router choices. Suitable split-read/write setups could work, without a general cross-database atomicity
guarantee.

**After:** the selected workflow write database must contain the required object, authenticated actor, `WorkflowInfo`
and `ContentType` tables/rows. Both actual inputs must already be saved and loaded from that alias. Object save,
history/content-type operations and the execution transaction bind explicitly to it; history readback follows the
persisted object's alias. Separate history/content-type routers cannot redirect these operations. Replica-loaded
inputs with a different write alias are rejected with `ImproperlyConfigured`, even when PKs match.

For workflow requests, align the application's authenticated-actor resolution and scoped object queryset with
that database, retaining every existing authorization, tenant, parent and object gate. The view's instance-hinted
`cv_get_db_alias()` selection is pinned once for the valid write path; overriding it alone does not reload or align
previously loaded inputs. DeleteView's separate support for a differently loaded target is unchanged and does not
apply to workflow.

For programmatic use, establish both saved inputs on the intended write database through application-authorized
queries before calling the helper:

```python
from crud_views_workflow.lib import run_transition

# These application-scoped querysets have already enforced actor/object identity and access.
actor = authorized_actors.using(write_alias).get(pk=authenticated_actor_pk)
order = authorized_orders.using(write_alias).get(pk=order_pk)
info = run_transition(order, "wf_confirm", user=actor, comment="Reviewed")
```

The helper still selects the write alias with `router.db_for_write(type(order), instance=order)`; the router must
agree with these inputs. It has no alias argument and does not establish request-level queryset/parent policy.
Do not mutate `_state.db`, copy a model to another alias, or substitute a same-PK actor: matching PKs do not prove
identity equivalence. Applications retaining replica-loaded workflow inputs or separate history storage remain
unsupported. No router-topology inspection, automatic split-storage diagnosis or cross-database transaction is added.

### Adopt literal help and shared comment visibility

**Before:** view-supplied workflow help could be interpreted as HTML by crispy templates, and an all-NONE comment
could leave a visible label/wrapper around a hidden field. **After:** `cv_transition_help_text` and
`cv_comment_help_text` are escaped literal text in both presentations; all offered policies NONE omits the visible
comment wrapper, label and help. A hidden input may remain. One OPTIONAL/REQUIRED action keeps one shared textarea;
only the chosen action determines comment requiredness.

Replace HTML help values with plain translated guidance. If an application needs authored HTML, place trusted
static markup in an application-owned template instead of passing it through workflow help or marking user text
safe. Update copied layouts/tests that depended on the empty comment wrapper; retain fields and bound errors when
the comment is visible. Button-mode field labels are literal too.

### Optional buttons and custom renderers

Radio remains the default. Ordinary `WorkflowForm` constructors, fields, `clean()`, `get_layout_fields()` and radio
`get_submit_button()` customization continue to work. When opting into buttons, retain the chosen transition widget
and remove a generic submit from any replacement `get_form_actions()`/helper; preserve eligible navigation Cancel.
Follow the [widget template contract](reference/theme.md#workflow-transition-widget) for copied renderers. Do not
replace the entire layout just to suppress the default submit. Pre-rendered/cached HTML bypasses normal bound refresh.

Button-mode IDs, including Cancel, are instance-namespaced. Use the provided IDs/description tokens rather than
hard-coded selectors. Keep a non-activating group label, full captions, per-action comment markers and the conditional
translated legend. The widget owns no form/CSRF token. Native Enter on a single-line field can submit the first
submit control in tree order when enabled; it does not skip a disabled first control. The stock textarea uses Enter
for a newline.

Expected business/comment refusals now render field errors after write rollback, without success effects. Errors
from the transition/save/history/`on_transition` itself still propagate, even if they are `ValidationError`.
Follow-up writes must use the selected database; external effects belong after commit. There is no stale-object
concurrency guarantee. Direct decorated calls still bypass the helper's validation, save and history contract.

## Action tooltips

Context/list icon-only actions now use the existing nonempty short caption as `cv_title`, with full-caption
fallback. Their full hidden `cv_label` stays unchanged; shortening the tooltip does not shorten the accessible
caption. Effective `label` / `both` modes and missing-icon fallbacks to visible text have no generated title or
tooltip marker. Empty tooltip text emits neither attribute. All visibly labelled context/list/card overflow items
omit automatic titles and tooltip markers, regardless of the action's inline mode. The overflow toggle is unchanged.

**Copied button and menu leaves must migrate immediately.** Use the complete, executable
[action leaf](reference/buttons.md#copied-action-leaf) and
[menu leaf](reference/buttons.md#copied-menu-leaf) recipes. An existing action copy that already consumes guarded
`cv_title` and full hidden `cv_label` needs no markup edit, but must adopt the changed field semantics in its
documentation and tests. A copied menu must remove its native-title branch; preserving that historical output is
not a supported migration path. Keep autoescaping, the hidden full caption, classes and active/disabled handling,
plus the link, POST and modal hooks shown in the recipes.

Cards retain their caption precedence: explicit card label, short caption, full caption, then key. Form buttons
retain their separate resolved-caption and extra-attribute ownership: generated icon titles use the form label;
application-supplied tooltip attributes in visible form modes remain application-owned. A raw custom
`ContextButton` template must normalize through the existing tag, as in the
[raw-context recipe](reference/buttons.md#raw-contextbutton-template), before expecting flat leaf fields.
Custom button labels and application-owned attributes are preserved. Full-caption/helper APIs remain available;
there is no new tooltip setting or runtime diagnostic.

The confirmed defect was the long tooltip on icon-only list actions. A separate visible-label defect was not
established; their existing no-generated-tooltip behavior is preserved. The caption changes do not change
hover/focus behavior, initialization, hide/dispose, adapter opt-out or application-owned tooltips; see
[Tooltips](reference/javascript.md#tooltips). Filter toggles, property-detail tooltips, formsets and card-order
controls are outside this action-caption change.

## Dynamic Cancel navigation

Standard create/update/delete/custom forms now default to `cv_cancel_keys="auto"`. Cancel accepts
registered usable list/card origins and, for object forms, same-object detail. Detail → Create is
excluded. Explicit lists may allow custom registered keys. Set `cv_cancel_keys=None` (or `[]`) to
retain static cancellation to `cv_cancel_key`, default `"list"` with card fallback. Singular
`cv_cancel_key=None` instead means the current view as fallback.

Copied templates must migrate immediately. **Before — unsupported key-only Cancel integration:**

```django
{% cv_context_url view.cv_get_cancel_key as url %}
<a href="{{ url }}">Cancel</a>
```

**After — resolve the URL and omit inaccessible Cancel:**

<!-- cancel-recipe: guarded-template -->
```django
{% load crud_views i18n %}
{% cv_cancel_url as url %}
{% if url %}<a href="{{ url }}" class="btn btn-secondary">{% translate "Cancel" %}</a>{% endif %}
```

Keep your translated label and theme classes, preserve autoescaping, and do not apply `safe`.
`cv_get_cancel_url(obj=None, user=None, request=None)` uses the bound object's/request's context by
default and returns a URL or `None`. The context-taking tag `cv_cancel_url(context, obj=None)` uses
the template's `view` and `request`. The retained `cv_get_cancel_key()` is a key helper for other
callers, not a supported reduced-function Cancel integration.

`get_cancel_button()` now returns `Button | None`; `get_cancel_button_kwargs()` remains a dict hook.
Filter `None` before constructing custom `FormActions`/layouts, retain Submit/Delete, and keep the
page-owned form (`helper.form_tag=False`). Execute the
[custom group and delete-helper recipes](reference/update_view.md#custom-form-action-groups) in your integration.

An allowed accessible origin takes priority, then the accessible configured fallback. If neither is
accessible, omit Cancel while retaining authorized form submission. A needed fallback with no usable
registered route is a configuration error: startup `viewset.E256`, runtime `ImproperlyConfigured`.
Configure an existing usable destination, including when neither list nor card exists. `viewset.E255`
continues to diagnose context buttons; it is not the Cancel fallback code.

Generated links now include signed captured query state alongside the origin key. Their default href
bytes intentionally change. Action-menu comparisons validate route/origin/signature/capture first,
then normalize only reserved navigation fields in comparison copies; existing golden files stay intact.
Applications asserting exact old links should follow the emitted links and check decoded state.

Cancel restores filters, sorting, page, repeated and empty values. A returned list remembers that query
when persistence is enabled; explicit empty clears memory, disabled persistence leaves memory untouched,
and other open forms retain independent captures. Signed `query=null` is legacy uncaptured state;
`query=""` explicitly restores an empty query. See [settings](reference/settings.md#origin-parameter)
for derived/renamed parameter names, token/JSON/query/pair bounds, visible URL data and signing-key rotation.
Parser bounds do not guarantee a portable full request-line size; upstream 414/400 rejection can happen
before Django receives a request, so fallback cannot be promised for those requests.

Save, successful deletion, `cv_success_keys` and modal redirect headers retain their existing behavior.
Save does not restore Cancel's capture. Invalid submissions retain capture; polymorphic selectors forward
cancel-only state. Supported delete/custom/workflow modal paths remain supported; create/update modal
opt-in remains unsupported (`viewset.E251`). No new protected-delete Cancel control, cross-ViewSet return,
history, scroll, browser-only state or unsaved-input restoration is introduced.

## Who this is for

- **An app on the stock bootstrap5 theme.** You override no crud_views template, but you have a base template,
  settings, views, maybe a Python override or some JavaScript, and CSS or tests that select on the markup. Read
  [Step zero](#step-zero-run-the-checks), [An app on the stock bootstrap5 theme](#an-app-on-the-stock-bootstrap5-theme)
  and [Silent breaks](#silent-breaks).
- **A downstream theme**, such as `crud_views_tabler`, that ships its own copies of crud_views templates. Read all of
  it: a theme is also an app.
- **An app on django-guardian**, one that shows delete previews with `cv_show_related_objects`, or one whose clients
  send HTTP `DELETE`: also read
  [Request authorization and Guardian configuration](#request-authorization-and-guardian-configuration).

Each step says what changed between 0.29.x and 1.0.0, not the route through 0.30.0. Steps marked **[0.30]** came
with the icon registry in 0.30.0: if you are already on 0.30.0, skip them.

## Step zero: run the checks

Upgrade, then run

```shell
python manage.py check
```

and fix everything it reports. Most removed settings and renamed values fail a system check with the replacement in
the message:

| Code | Raised when | Do this |
|---|---|---|
| `crud_views.E350` **[0.30]** | a removed icon setting is still defined: `CRUD_VIEWS_ACTIONS_MENU_ICON`, `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`, `_ICONS_CLASS`, `_ICONS_TYPE`, `_ICONS_PREFIX`, `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` | move the value into `CRUD_VIEWS_ICONS`, see [Settings](#settings) |
| `crud_views.E360` | `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` is still defined | `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "..."}` |
| `viewset.E250` | `cv_modal_size` is a Bootstrap class such as `"modal-lg"` | use the token: `""`, `"sm"`, `"lg"` or `"xl"` |
| `viewset.E263` | an effective `cv_get_related_objects()` override remains | use the [safe provider and display filter](#safe-deletion-preview-overrides); runtime rejects it without invocation |
| `viewset.E264` | an inspectable model `delete` cannot bind keyword `using` | accept/forward `using` or `**kwargs`; [opaque methods fail at runtime](#delete-method-signatures-and-database-selection) |
| `crud_views.E109` | invalid raw `CRUD_VIEWS_DELETE_PREVIEW_LIMIT`, even with a valid view override | use a positive integer or explicit `None`; project value is startup-captured |
| `viewset.E265` | invalid explicit/inherited `cv_delete_preview_limit` | use a positive integer, explicit `None`, or omit to inherit project; invalid effective values also raise `ImproperlyConfigured` on GET/POST |
| `viewset.W246` **[0.30]** | an object detail group `icon` uses a `prefix:` that is not registered | register the library in `CRUD_VIEWS_ICON_LIBRARIES`, or fix the prefix |

Two removals raise at runtime instead, the first time the page renders:

- `TypeError` from a `cv_get_context()` override with the old signature: see
  [Views and Python code](#views-and-python-code).
- A validation error for removed `CardAction.no_label`: see [Removed card label keyword](#removed-card-label-keyword).

A `GuardianViewSet(..., cv_guardian_accept_global_perms=...)` fails earlier still, with a Pydantic `ValidationError`
when the module that builds it is imported: see
[The GuardianViewSet global-permission key](#the-guardianviewset-global-permission-key).

The new features bring their own checks. They only fire on a misconfigured new setting or attribute, so an upgraded
project that uses none of them never sees them: `crud_views.E351`, `E354`, `E355`, `E356`, `W352`, `W353`
([icon libraries](reference/icons.md)), `crud_views.E361`, `W362` ([button classes](reference/buttons.md)),
`viewset.E209` ([variants](reference/buttons.md)), `viewset.E210` ([card label mode](reference/card-list-view.md)),
`crud_views.E106`, `viewset.E211`, `W291` ([toolbar and row label modes](reference/action_menus.md)),
`crud_views.E108` ([label-mode defaults](reference/settings.md#label-mode-configuration)). The form label-mode maps
reuse `crud_views.E106`, `viewset.E210`, `E211`, `W291` and `W292` ([Form checks](reference/action_menus.md#form-checks)).

`crud_views.E108` reports a `CRUD_VIEWS_LABEL_MODE_DEFAULTS` that is not a dict, a key that is not a button location
(`"context"`, `"list"`, `"card"`, `"form"`) and a mode that is not exactly `"label"`, `"icon"` or `"both"`. At render an
unknown key is ignored. An invalid mode raises `ValueError` in strict mode (`CRUD_VIEWS_STRICT`, which defaults to
`DEBUG`); otherwise it logs one warning and the location falls back to its theme registration, then its package floor.

A clean `check` is not the end: some changes render differently and raise nothing. They are collected under
[Silent breaks](#silent-breaks).

## An app on the stock bootstrap5 theme

Your base template, settings, views, JavaScript, and the CSS and tests that select on markup.

### Base template and your own templates

- **If your base template uses `django_bootstrap5`:** crud_views no longer depends on `django-bootstrap5`, so it is
  no longer installed for you. Replace `{% bootstrap_messages %}` with `{% cv_messages %}` from the `crud_views` tag
  library; it renders the same `django.contrib.messages` queue as Bootstrap 5 alerts
  ([Flash messages](reference/messages.md), #221). If you keep other tags such as `{% bootstrap_css %}` or
  `{% bootstrap_javascript %}`, add `django-bootstrap5` to your own dependencies and keep `django_bootstrap5` in
  `INSTALLED_APPS`. Without either, `{% load django_bootstrap5 %}` raises `TemplateSyntaxError`.
- **If you list crud_views' static files by hand** instead of rendering `{% cv_css %}` / `{% cv_js %}` or using
  `cv_sources()`: add `crud_views/css/icons.css` **[0.30]** (it provides `.cv-icon-fw` for the menu icons) and put
  `crud_views/js/adapters.js` before every other crud_views script ([JavaScript](reference/javascript.md#what-the-scripts-need)).
- **If your templates use `{% cv_submit_button %}`, `{% cv_cancel_button %}` or `{% cv_delete_button %}`:** the tags
  and their templates are gone. The crispy forms build their buttons with `Submit`, `Button` and `Reset` from
  `crud_views.lib.crispy` ([Forms](reference/buttons.md#forms)).
- **If your templates use `{% cv_filter_icon %}`, `{% cv_header_icon_class %}` or `{% cv_filter_icon_class %}`,
  or `{% include "crud_views/tags/icon.html" %}` [0.30]:** render the icon with `{% cv_icon "filter" %}`, or
  `{% cv_icon value css="me-2" %}` for any icon value ([Icons](reference/icons.md)).
- **If your templates use the `cv_is_true`, `cv_is_false` or `cv_is_list` filters:** they are removed together with
  the unused `crud_views/detail/` templates (#217).

### Settings

**Icon settings [0.30]** (`crud_views.E350`). The icons now come from one table, `CRUD_VIEWS_ICONS`
([Icons](reference/icons.md#crud_views_icons)). Before, in 0.29:

```python
CRUD_VIEWS_ACTIONS_MENU_ICON = "fa-solid fa-bars"
CRUD_VIEWS_FILTER_ICON = "fa-solid fa-magnifying-glass"
```

After, in 1.0:

```python
CRUD_VIEWS_ICONS = {"actions-menu": "fas:bars", "filter": "fas:magnifying-glass"}
```

The `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*` settings and `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` are gone too. Object
detail now uses Font Awesome like the rest of the package. To keep Bootstrap Icons there:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = {k: BOOTSTRAP_ICONS[k] for k in ("boolean-true", "boolean-false", "property-detail", "text-icon")}
```

`CRUD_VIEWS_ICONS = BOOTSTRAP_ICONS` switches every icon of the package to Bootstrap Icons
([Bootstrap Icons preset](reference/icons.md#bootstrap-icons-preset)).

**`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`** (`crud_views.E360`) moves into the button class table:
  `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "btn btn-secondary"}` ([Buttons](reference/buttons.md#crud_views_button_classes)).

### Views and Python code

**If you override `cv_get_context()`:** it takes a keyword-only `location`, and every button path passes it. An
override with the old signature raises `TypeError` on the first toolbar. Accept it and pass it on (#216):

```python
def cv_get_context(self, key=None, obj=None, user=None, request=None, *, location=None):
    context = super().cv_get_context(key, obj, user, request, location=location)
    ...
    return context
```

The other changes to views:

- **`cv_modal_size`** (`viewset.E250`) takes the tokens `""`, `"sm"`, `"lg"` and `"xl"`: `cv_modal_size = "modal-lg"`
  becomes `cv_modal_size = "lg"` ([Modals](reference/modals.md)).
- **Remove obsolete `cv_no_label` template context** from overrides and use `cv_label_mode`
  (`"label"`, `"icon"` or `"both"`). Stray legacy context is harmless and unprojected; the obsolete guard is gone.
  Python `CardAction.no_label` is rejected on presence, including `False`; see the
  [replacement recipe](#removed-card-label-keyword).
- **Card buttons show their icon next to their label** (#213). To get the 0.29 label-only buttons back on every card
  view of the project, set `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` in your settings. For one view, set
  `cv_card_actions_label_mode = "label"` on the card view; for one button, `CardAction(label_mode="label")`
  ([Label mode](reference/card-list-view.md#label-mode)). An unknown value fails `viewset.E210`, an unknown setting
  entry `crud_views.E108`.
- **Card label-mode attribute:** `CardListView.cv_card_actions_label_mode` now reads `None` by default instead of
  the resolved string `"both"`; `None` means the `"card"` entry of `CRUD_VIEWS_LABEL_MODE_DEFAULTS`
  ([setting](reference/settings.md#label-mode-configuration),
  [resolution](reference/action_menus.md#card-label-mode-resolution)). Without
  configuration cards still resolve to `"both"` and render as before, but this is a Python-level change: a subclass,
  override or template that reads the raw attribute as a mode now gets `None`.
  `cv_get_card_actions_label_mode()` resolves class-level defaults and stays callable on the class; calling it
  through an instance still reads class configuration. Read the effective per-action `cv_label_mode` stamped on
  the button context or returned by `cv_get_card_action_data()`. A view that assigns the attribute on a class or
  instance keeps its choice, including `as_view()` and per-request assignment. `CardAction(label_mode="icon")`
  renders icon-only.
- **`CardAction.variant` defaults to the target view's variant.** A card action pointing at a create view without an
  explicit `variant` now renders `btn-primary`; set `variant="secondary"` to keep the 0.29 look
  ([Variants](reference/buttons.md#variants)).
- **Object detail group icons [0.30] are no longer prefixed for you.** `icon="truck"` must become
  `icon="fas:truck"` (or `"bi:truck"`), or `"truck"` must be added to `CRUD_VIEWS_ICONS`. Nothing flags a bare name:
  it is read as a raw CSS class and renders an invisible `<i class="truck">`
  ([Groups](reference/object_detail_configuration.md#groups)).
- **If you override `cv_get_filter_icon()` on a list or card view [0.30]:** nothing calls it any more, and nothing
  says so. The filter toggle and the filter panel header both use the `filter` icon; set
  `CRUD_VIEWS_ICONS["filter"]` instead.
- `cv_icon_action` and `cv_icon_header` on your views need no change: a raw CSS class such as
  `"fa-solid fa-truck"` still renders as before. Semantic names (`"detail"`) and `prefix:name` values
  (`"fas:truck"`) work too ([Icon values](reference/icons.md#icon-values)).

## Presentation contracts

### Heading hosts and sizing

Update copied page, modal and group title templates now. Use the executable
[page and modal recipes](reference/templates.md#page-title-recipe),
[plain group recipe](reference/icons.md#plain-group-title-recipe) and
[title-button recipe](reference/icons.md#title-button-recipe). Each calls
`cv_heading_icon` and consumes `host_class` on the title-bearing element plus
`inline_html` exactly once. For interactive titles the button owns the host class,
not the enclosing heading. Empty/disabled icons leave visible text intact.

`cv_heading` keeps semantic heading levels; `size` selects `heading:size-1` through
`heading:size-6`, independently of the semantic level. Map or suppress these classes
using the [native heading class table](reference/theme.md#native-heading-class-table).
Style shared `heading:icon-host` / `heading:icon-inline` slots or their
`heading-page`, `heading-modal`, and `heading-group` overrides.

The old page `cv_header_icon` body block placement is superseded by the projection:
override `cv_get_header_icon()` or registry/classes instead. Keep `cv_header` for
visible-title customization. The **tag** `cv_header_icon` remains callable for standalone
icon rendering; it is not the host-aware heading recipe. Split-card group icons now
use heading-group slots; copied `text-default fs-5` styling must move there if desired.
Intentional markup changes remove nested page heading wrappers, put host icons on titles,
and render element-library icons once. Redeploy copied templates with these changes.

### Interactive object-detail templates and targets

Replace copied object and group templates together using the executed
[tabs and accordion recipes](reference/object_detail_layout_packs.md#copied-interactive-templates).
Use `component.groups` and forward `presentation` / `component` to `render_group`.
Both triggers and panels read the same `selected` flag; the first tab and panel are active.
Accordions remain initially collapsed. Keep the stock marker and panel reading/focus stop,
or follow the reference's theme qualification and verify your own focus sequence.

Old title-slug selectors and fixed accordion root IDs are obsolete. Supply
`cv_object_detail_id` / `cv_get_object_detail_id()` (or tag `component_id`) and explicit
group `id` keys, then update links, Selenium selectors and scripts to the
[length-prefixed formula](reference/object_detail_layout_packs.md#template-projection-and-stable-targets).
Use the executable [page/modal hook](reference/object_detail_configuration.md#page-and-modal-identity)
to distinguish actual modal requests; additional instances require distinct tokens.
Generated IDs intentionally change across renders; explicit group keys preserve targets
through translation and reordering. Stable IDs do not add fragment-driven activation or persistence.

Applications own unique namespaces for independently fetched modal content and fresh
backend renders without scope transport whose output is later assembled into one page.
Includes/inheritance and explicitly transported library rendering still detect collisions;
see the precise [collision detection boundary](reference/object_detail_layout_packs.md#collision-detection-boundary).
Redeploy templates and collected/bundled static assets together. The additive semantic badge
fields do not require a template migration: default Bootstrap output remains unchanged.
Native themes can use the tested [badge recipe](reference/object_detail_badges.md#native-semantic-badge-template)
and [minimal native layout](reference/object_detail_layout_packs.md#minimal-native-layout).

### Filtered object-detail assets

The installed object-detail extension registers `crud_views_object_detail/js/tabs.js`.
Default `cv_sources("js")` (`keys=None`) already includes the registered extension.
An explicit core-only filter, `keys=["crud_views"]`, omits it. Replace that filter
with both bundle keys; this does not change pipeline filtering semantics:

```python
from crud_views.lib.pipeline import cv_sources

sources = cv_sources("js", keys=["crud_views", "crud_views_object_detail"])
```

Use `sources` as the pipeline package's `source_filenames`; keep it lazy in settings.
Do not add a duplicate direct script when your bundle already includes it. Load Bootstrap
before initializing stock tabs. Rebuild/redeploy static bundles along with copied templates.

### Removed card label keyword

Before migration, `CardAction(key="detail", no_label=True)` requested icon-only output.
That keyword is removed: **every supplied value**, including `False`, `None`, and use
alongside `label_mode`, now raises a Pydantic validation error naming `label_mode`.
Omit it to inherit, or choose the supported explicit mode:

```python
from crud_views.lib.view.card import CardAction

action = CardAction(key="detail", label_mode="icon")
inherited = CardAction(key="detail")
```

Before migration, copied leaves read `cv_no_label`. Use `cv_label_mode` in replacement
leaves; within an existing action context (including its resolved access permission,
URL, label and icon), forward the mode to the real renderer:

```django
{% load crud_views %}
{% with cv_label_mode="icon" %}{% cv_button "card" %}{% endwith %}
```

A stray legacy template `cv_no_label` variable is ignored, never projected, and no longer
raises through an obsolete guard. This differs from Python's presence-based rejection.
The accepted `cv_context_actions_label_mode` and `cv_context_action_label_mode` APIs both
remain unchanged; their plural/singular names have distinct meanings and are not aliases
being removed. Existing card/action mode precedence remains intact.

### JavaScript

- **`cv.cvModalOpen(url, size)` and hand-written `data-cv-modal-size`** take the same tokens as `cv_modal_size`:
  `cv.cvModalOpen(url, "lg")`, `data-cv-modal-size="lg"`. No check can see these; an old `"modal-lg"` silently opens
  the default size.
- **jQuery** is only needed on pages with formsets and by jQuery-based extensions
  ([jQuery](reference/javascript.md#jquery)). The core scripts use the DOM API and talk to Bootstrap through
  `cv.adapters` ([`cv.adapters`](reference/javascript.md#cvadapters)).
- **Tooltips.** Icon-only buttons, the filter toggle, the card-order toggles and the formset controls carry
  `data-cv-tooltip`. With Bootstrap's JavaScript loaded they now show Bootstrap tooltips instead of the browser's
  `title` tooltip (#202). To keep the browser tooltip: `cv.adapters.tooltip = {init() {}}`
  ([Tooltips](reference/javascript.md#tooltips)).
- **Dismissible alerts** close through `cv.adapters.alert`, called by `viewset.js` after `adapters.js`; with
  `{% cv_js %}` there is nothing to do. A script of yours that replaces the whole `cv.adapters` map after core loads
  must provide `alert` as well ([Hooks instead of copies](#hooks-instead-of-copies)), and a copied alert frame
  needs the new close hook ([Contract changes](#contract-changes-in-templates-you-still-override)).

### CSS and tests that select on markup

None of these raise anything. Check your stylesheets, your JavaScript selectors and any test that asserts on HTML:

- **Table sort icons [0.30]** are Font Awesome 6 (`table-sort-asc` = `fas:angles-up`, `table-sort-desc` =
  `fas:angles-down`), and ascending now points up.
- **Icons [0.30]** render with `aria-hidden="true"`; the menu icons use `cv-icon-fw` instead of `fa-fw`.
- **Card list pagination** (#241): the arrows are the `page-previous` / `page-next` icons followed or preceded by a
  visually hidden "previous" / "next", not `&laquo;` / `&raquo;`. A disabled end is
  `<a class="page-link" aria-disabled="true">` without `href`, not a `<span>`. The current page carries
  `aria-current="page"`.
- **Table pagination**: the stock django-tables2 template uses the same markup. The visible "previous" / "next"
  text with `&laquo;` / `&raquo;` becomes the icons with hidden labels. The current page is a
  `<span class="page-link">` in `li.active[aria-current="page"]` instead of a link. The missing direction is now
  rendered as a disabled `li` instead of being left out, and the `<nav>`'s label is the translated "pagination"
  instead of "Table navigation" ([Table pagination overrides](#table-pagination-overrides)).
- **`hidden` instead of `d-none`** (#232): the filter toggle's icon spans and the hidden POST forms behind list and
  card actions use the `hidden` attribute. The filter toggle carries `aria-expanded`, `aria-controls="filter-collapse"`
  and `cv-key="filter"`.
- **Buttons:** one attribute order for every button; card buttons carry `cv-key`; card POST actions render
  `<button type="button">`; the active toolbar action carries `aria-current="page"`; a list or card button whose
  target is the current view renders `active`; the card row carries `cv-card-container`; card menu forms render
  before the row.
- **Form buttons:** the crispy form buttons are `<button>` elements instead of `<input>`
  ([Form buttons](#form-buttons)). The cancel button renders `btn btn-secondary` (was `btn btn btn-secondary`), the
  filter reset `btn btn-secondary` (was `btn btn-inverse btn btn-secondary`), and the Delete label is translated.
- **Tooltip markup** (#202): the formset controls' `title` is the translated text of their `aria-label` ("Move up",
  "Move down", "Add row", "Delete row"), no longer `up` / `down` / `add` / `delete`. The object-detail
  property-detail button uses `title` instead of `data-bs-title`.
- **Action tooltips** (#304): context/list icon titles use short captions, while full hidden captions remain;
  context-menu native titles are removed. Update copied leaves and title assertions ([Action tooltips](#action-tooltips)).
- **Alerts** (#250): the delete page's protection and related-objects alerts and the guardian manage page's config
  alert gain `role="alert"` and an icon before the heading.
- **Alert close control:** the dismissible alert's close button carries `data-cv-alert-dismiss` instead of
  `data-bs-dismiss="alert"` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- **Empty button containers** (#265): a toolbar, list row or card whose actions are all hidden for the user renders
  no container at all, so `[cv-list-container]` (or `cv-context-container`, `cv-card-container`) is not in every row
  any more. Selectors that expect it must handle its absence.
- **Container label** (#266): the toolbar and list row `aria-label` is translated ("Aktionen" on a German page).

## Form ownership and theme adoption

Migrate application helpers and copied form templates immediately when upgrading. There is no compatibility
period for nested helper-owned forms. The DOM fix and the helper/template policy changes are distinct:
stock create/update/custom/delete frames remove the inner form and second CSRF input while preserving the
outer attributes and controls; workflow now uses the same boundary. Only the target content owns this one
form/token; auxiliary sibling forms retain their independent tokens. All nested forms, including unclassed ones,
are invalid. No form/button golden changes beyond the reviewed ownership correction are required.

### Page-owned forms and helpers

Library helpers already use `form_tag=False`. Set it on your custom helper too; `cv_render_form` rejects
`form_tag=True` with `ImproperlyConfigured` in both strict and non-strict modes. A computed helper remains valid:

```python
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from crud_views.lib.crispy import Submit


class ContactForm(forms.Form):
    name = forms.CharField()

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False
        helper.layout = Layout("name", Submit("submit", "Send", icon="save"))
        return helper
```

Move intended method/action/id/enctype/other outer attributes to the page template. They are never transferred
from the helper. Supply `form_id` in context; retain the normal request and CSRF context:

```django
{% load crud_views %}
<form class="cv-form" id="{{ form_id }}" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>
    {% csrf_token %}
    {{ form.non_field_errors }}
    {% cv_render_form %}
</form>
```

Nonempty raw `form_action`, `form_id`, `attrs`, `form_class`, and a `form_method` other than `"post"` warn when
strict mode is off and raise `ImproperlyConfigured` when it is on. Ordinary defaults are quiet; an explicit
assignment equal to a default is not promised detectable. Helper method/classes may still affect pack internals;
field/label/media/layout settings remain separate. `cv_render_form` selects the helper once and suppresses only
its inner token without mutating the caller's helper/layout. Do not put `safe` on caller-controlled attributes.
Redundant parent helper overrides that only set `form_tag=False` may be removed; inherited library providers
recover W292 inspection without form construction. Custom overrides retain their existing diagnostic boundary.

### Copied form and workflow templates

Update both kinds of copies below. A legacy template resolving `form.helper` again, or calling implicit crispy,
can emit duplicate tokens even though the page calls `cv_render_form`. Such bypasses cannot be automatically
diagnosed. The fix is to migrate the copy, not to strip HTML or override global crispy templates.

### Selected inner helper

Replace a copied `crud_views/tags/form.html` with this inner body. The selected render-local helper is provided by
`cv_render_form`; do not reselect it:

```django
{% load crispy_forms_tags %}
{% crispy form cv_form_helper %}
```

### Workflow action body

In a copied `crud_views_workflow/view_workflow.action.html`, remove the unused `crispy_forms_tags` load and retain
the heading, non-form errors, branch and outer token while replacing the direct crispy call. Extend the shared
frame and fill `cv_form_body` around the entire choices/empty branch to receive theme framing:

```django
{% extends "crud_views/snippets/form_frame.html" %}
{% load i18n crud_views %}
{% block cv_form_body %}
{% if has_workflow_choices %}
    {% cv_heading level=5 %}{% translate "Workflow Action" %}{% endcv_heading %}
    <form class="cv-form" method="post" novalidate>
        {% csrf_token %}
        {{ form.non_form_errors }}
        {% cv_render_form %}
    </form>
{% else %}
    {% translate "There are no workflow steps available from the current state." %}
{% endif %}
{% endblock %}
```

History remains before and outside this action frame. In a copied history template, wrap only the table with a
div using `workflow:history-wrapper`; put `workflow:history-table` on the table itself. Keep the heading outside
the scrolling wrapper and omit the entire history section when empty. The stock defaults are `table-responsive`
and `table`; broad overflow styling on the whole workflow content can be removed after adopting this structure.

A copied `crud_views_workflow/badge.html` continues to own its chosen markup and receives the existing `state`,
`name` and `class` plus additive `badge_class`. Remove a redundant badge copy and use the
[conditional class-registration recipe](reference/theme.md#optional-workflow-classes), or explicitly consume
`badge_class` with the documented [missing/disabled distinction](reference/workflow_view.md#themeable-state-badges).
`BadgeEnum`, `STATE_BADGES` and `STATE_BADGE_DEFAULT` remain unchanged.

Protected delete and full-page no-choice workflow still omit their own forms. Workflow modals deliberately retain
the inherited `crud_views/view_custom_form.content.html`, including the generic no-choice form, and reject
unavailable transitions. Do not replace their `cv_content_template` with this full-page workflow body.
Create/update and parent formsets remain unsupported modal types; E251 still rejects opt-in.

### Standalone library form wrappers

Standalone crispy rendering of a library `CrispyModelForm` now produces fields and its token without its former
helper-owned outer form. Add your own wrapper. Keep the crispy token and **do not add another CSRF tag**:

```django
{% load crispy_forms_tags %}
<form class="cv-form" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>
    {% crispy form form.helper %}
</form>
```

This standalone POST recipe needs the normal request/CSRF context. It differs from the page-owned renderer above,
where the page emits a token and the inner render suppresses it. Standalone custom helpers and GET filters retain
their own wrapper/token policy. See the [complete ownership reference](reference/theme.md#page-owned-form-helpers).

### Theme defaults and additive utilities

Use [the registration recipe](reference/theme.md#register-theme-defaults) to register label defaults. Per-location
precedence is package → theme → project; explicit view/button modes remain above it, and whole-owner-map selection
is unchanged. Later theme calls win per key; invalid registration raises atomically. Invalid project values use
the theme/package fallback in non-strict mode. No accepted singular/plural API is renamed.

`form:actions` and `form:filter-actions` have empty defaults and add classes to the selected pack's wrapper.
Custom action providers opt in through [the public super-based recipe](reference/theme.md#custom-action-group-opt-in).
`alert:dismissible` and `alert:close` preserve Bootstrap defaults; replace/omit their values while retaining
`role="alert"`, the conditional close control, translated accessible name and `data-cv-alert-dismiss`.

The current crispy 2.7 / crispy-bootstrap5 2026.9 and crispy 2.0 / crispy-bootstrap5 2023.10 floor were tested
separately. Only the installed floor pack's exact audited source uses the local compatibility bridge; custom
origins/sources keep their own rendering and must consume the class value. There is no generic pack rewrite.
General theme adoption is covered by executable recipes and isolated browser/replay evidence; that evidence
does not claim a fully green downstream suite or live companion delivery. No downstream-specific configuration
is required by these public contracts.

## Form buttons

The `Submit`, `Button` and `Reset` of `crud_views.lib.crispy` render through the form-button leaf
`crud_views/tags/button/form.html` when they sit in a crispy layout ([Forms](reference/buttons.md#forms)). Every
package form does that: create, update, custom form, delete, workflow and the list filter. Nothing raises for the
changes below unless noted.

### Markup and submitted data

- Each button is a `<button>` instead of an `<input>`, with its text in a `<span>`:

    ```html
    <!-- before -->
    <input type="submit" name="submit" value="Create" class="btn btn-primary" id="submit-id-submit"/>
    <!-- after -->
    <button type="submit" name="submit" value="Create" id="submit-id-submit" class="btn btn-primary"><span>Create</span></button>
    ```

    The names, values, ids, classes and the cancel button's `data-cv-cancel-url` stay as they were, and so do the
    filter's `filter-button` and `filter-button-reset` ids. Selectors and tests that match `input[type="submit"]`,
    `input[name="reset"]`, `input#filter-button` or the attribute order must match `button` instead.
    Extra attributes passed to a button (`Submit("submit", "Go", data_b="1", data_a="2")`) render after `type`,
    `name`, `value`, `id` and `class` (and the cancel URL and icon-only title, when present) in sorted order, as
    Django's `flatatt` emits them, with boolean attributes last; crispy kept the keyword order. The example renders
    `data-a` before `data-b`.
- A click posts the clicked button's `name=value`, as the input did, and in the modal `modal.js` sends the same
  submitter. The delete view still needs only its confirmation field: a click posts `confirm` and `delete=Delete`,
  and a test that posts `{"confirm": True}` alone keeps working.
- A name of several words is still submitted slugified, as crispy did (`"Search the Site"` becomes
  `search-the-site`); a one-word name is submitted as written. The generated ids keep crispy's `<type>-id-<name>`.
- The filter's Apply and Reset now render in their own `FormActions` group (`<div class="mb-3">`) after the fields.
  The template pack's inputs wrapper follows it with only the hidden `sort`, order and direction inputs, with
  unchanged names and values and its own `mb-3` margin. No global crispy template override is needed or shipped.

### Values are literal text

Crispy rendered the value of a layout button as a Django template. The leaf does not: values, labels, names, ids and
attribute values are escaped once and shown as written. `Submit("submit", "{{ request.user }}")` used to show the
user's name and now shows `{{ request.user }}`. Compute such a label in Python instead, for example in
`get_submit_button_kwargs()`, where the form's view and its request are at hand (`self.cv_view.request`).

Each reserved attribute is set once ([Literal text](reference/buttons.md#literal-text)): an extra `type`, `name` or
`value` keyword is dropped, `css_id` wins over an extra `id`, and an extra `class` is appended after the table
classes and `css_class`. In `"icon"` mode the generated `title` and `data-cv-tooltip="form"` win over yours.
A `tag` keyword is no longer rendered as an attribute: it accepts only `None`, `"button"` and `"a"`, which selects a
[cancel link](reference/buttons.md#cancel-links), and any other value raises `ValueError` when the button is built.
If you passed `tag` as a plain HTML attribute, for example from `get_cancel_button_kwargs()`, rename it to a
`data_` keyword (`data_tag="..."` renders `data-tag`).

### Custom button templates

A `template=` argument and a `template` attribute on your subclass keep working, `%s` pack names included, in this
order: `template=`, the subclass attribute, the bundled leaf. The template now receives the form leaf contract
instead of crispy's `input` object, and nothing of the surrounding page:

| Before | After |
|---|---|
| `{{ input.value }}` | `{{ cv_value }}` (submitted), `{{ cv_label }}` (shown) |
| `{{ input.name }}` | `{{ cv_name }}` |
| `{{ input.id }}` | `{{ cv_id }}` |
| `{{ input.input_type }}` | `{{ cv_type }}` |
| `{{ input.field_classes }}` | `{% cv_button_class "form" cv_key cv_label_mode %}` and `{{ cv_css_class }}` |
| `{{ input.flat_attrs }}` | `{{ cv_flat_attrs }}` |

A template that still reads `input.*` renders empty attributes and raises nothing. The full recipe is
[Custom form-button templates](reference/theme.md#custom-form-button-templates). A theme that restyled the package
buttons by overriding crispy's `layout/baseinput.html` no longer reaches them: register `form:*` classes or override
`crud_views/tags/button/form.html`.

### Cancel links

Optional: the cancel button stays a `<button>` with `data-cv-cancel-url` unless you opt in, so a project on the
defaults needs no action. To render it as a native `<a href>` link, set the class-table key `form:cancel-tag` to
`"a"` in a theme registration or `CRUD_VIEWS_BUTTON_CLASSES`, or pass `tag="a"` to one cancel
([Cancel links](reference/buttons.md#cancel-links)). A disabled cancel and one without a destination stay buttons.

A custom button template keeps rendering what it renders: a template that knows nothing of `cv_tag` keeps its
`<button>` and its `data-cv-cancel-url` navigation even when links are selected. To render the link, branch on the
new `cv_tag` field: emit `<a href="{{ cv_cancel_url }}">` without `type`, `name`, `value` and `data-cv-cancel-url`
when it is `"a"`, and the button otherwise. See
[Cancel links in custom form-button templates](reference/theme.md#cancel-links-in-custom-form-button-templates).
JavaScript or tests that select the cancel as `button[name="reset"]` must also accept `a#button-id-reset` once links
are on.

### Slots

A button in a layout needs `slot="form:<kind>"` with one of the five form kinds `submit`, `cancel`, `delete`,
`filter-submit` and `filter-reset`; any other slot (`"formset:control"`, `"form:primary"`) raises `ValueError` when
the button renders. Pick the kind that matches what the button does and restyle it with `css_class`, or for every
button of that kind with a `form:<kind>` or `form:<kind>:<mode>` key in `CRUD_VIEWS_BUTTON_CLASSES`. There are no
other kinds or variants. Buttons added with `helper.add_input()` are not checked.

### Filter helpers

A `ListViewFilterFormHelper` subclass that declares only its fields keeps working: Apply and Reset are appended once
after them ([Custom filter helpers](reference/list_view.md#custom-filter-helpers)).

- **If you cleared `helper.inputs = []` (or `self.inputs = []`) to hide Apply and Reset:** that no longer hides them,
  it only drops the hidden sort, order and direction inputs. Nothing warns. Override `get_form_actions()` to return
  `None` and leave the inputs alone, see
  [Removing the filter buttons](reference/list_view.md#removing-the-filter-buttons).
- **If you added your own buttons with `add_input(Submit(...))`:** they keep rendering as crispy inputs with their old
  markup, in the inputs wrapper after the visible actions, without label mode or icon and without a warning. To give
  them the new leaf, return them from `get_form_actions()` in a `FormActions`; keep hidden inputs as inputs.

### Label modes and icons

Form buttons show their text by default: the `"form"` floor of `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is `"label"`, so
nothing gains an icon until a project asks for one with the floor or a form map
([Form label-mode resolution](reference/action_menus.md#form-label-mode-resolution)). In `"icon"` mode a button
without a usable icon raises `ValueError` under `CRUD_VIEWS_STRICT` and otherwise logs a warning and keeps its label;
see [Form buttons](reference/icons.md#form-buttons) for the icons and their order.

## Conditional groups and formset lifecycle

### Conditional bound markers and lifecycle

Update copied `crud_views/conditional/toggle_group.html` and `crud_views/formsets/formsets.html` overrides to render
`cv_toggle_field` and `x_formset.cv_toggle_field` directly. Their value is now the complete bound checkbox name
(`editor-0-active`, for example), not the unprefixed declaration name. Remove hand-added prefixes and suffix-based
checkbox selectors. Use the executable [copied-wrapper recipe](reference/conditional.md#copied-conditional-wrapper),
which preserves escaping, inner content and the optional legend.

For custom DOM insertion, call `cv.initConditional(root)` and `cv.initFormsets(root)` as in the
[initialization recipe](reference/javascript.md#conditional-and-formset-initialization). They accept Document,
Element and DocumentFragment roots and are repeat-safe, including late checkbox retries. Page load, modal loaded/422
replacement and outer row-added events initialize automatically. Duplicate exact checkboxes in one owning form log
the local ambiguity diagnostic; separate forms with repeated names remain independent. An initially unresolved group
leaves its own presentation unmanaged; a previously bound group retains its last owned state while missing or
ambiguous, composed with ancestor and independent disabled ownership. Restore exactly one matching checkbox and
reinitialize to apply its current state. Keep native `button type="button"`
row controls, their [semantic hooks and projection](reference/formsets.md#template-projection-and-native-controls),
management inputs and balanced fragment wrappers. Internal controller constructors are not an insertion API.

In copied row controls, use the executable [native capability recipe](reference/formsets.md#native-row-capability-recipe):
`'DELETE' in form.fields` determines deletion eligibility, including `can_delete_extra=False`. Do not require a DELETE
field for permitted Add/Move or submit, or infer initial/extra eligibility from the row's current visual order.
The original bound index remains authoritative after insertion or movement. `edit_only` and `can_order` remain
independent capabilities; browser controls do not grant write authority.

Deploy the updated templates and static assets using your normal static-file process, refresh caches as appropriate,
and reload already-open pages so markup and scripts agree. No deployment-specific rollout policy is required.
Conditional visibility is immediate; disabled state composes independent reasons and all bound ancestors, while native
reset respects cancellation and owning-form scope. This does not settle final dynamic-row reset policy (A8).
Existing form leaf/label/escaping, Cancel links and modal completed-hide/focus contracts remain in force.

For contributor acceptance, run ordinary Node-only `npm test` **and** the required explicit-runtime
[`npm run test:integration` command](reference/javascript.md#javascript-test-commands), with `CV_FRAGMENT_PYTHON`
pointing to the prepared interpreter and checkout `PYTHONPATH`. Missing integration runtime is a failure, not a skip.
This documentation is a repair handoff, not Phase 06.4 acceptance or human visual/storage-policy approval.

### Conditional clearing and E312

Replace assumptions that every off field becomes `None` with the exact
[clearing matrix](reference/conditional.md#clearing-matrix). Supported native text/Boolean/nullable scalar/relation,
file/image and many-to-many pairs each use their native empty value, including omitted/defaulted and unchanged inline
fields. Unsupported automatic pairs now produce Error `crud_views.E312`, replacing Warning W320. Request-added
unsupported fields raise group/field-specific `ImproperlyConfigured` during `clean()`, including active submissions.
Keep E310/E311/W321 handling; supply and test explicit `empty_values` for unsupported pairs.

The executable [file-reference recipe](reference/conditional.md#explicit-file-reference-recipe) demonstrates explicit
`False`/`""` to clear and `None` to retain a reference. Stored bytes are retained; no cleanup policy is added.
Server-side `Field.disabled=True` retains Django's trusted initial and validation, ahead of any explicit off override.
Inherited clean nonfield errors and model/uniqueness/database invariants remain authoritative. Remove descriptions
that off groups are "never validated"; only ordinary errors on editable off fields are suppressed.

ImageField reference clearing is supported with reference-only evidence: False/None/disabled/unchanged-inline cases
do not exercise image-byte decoding. Actual discarded multipart uploads use FileField. Consuming applications keep
Django's existing Pillow prerequisite for ImageField upload decoding; no image-validation or new dependency claim
is made here. The documentation tests execute the actual recipe for both stored-reference field types.

### Formset row validation before saving

Review custom inline cleaning and callers that relied on silently ignored edit-only additions or untrusted existing
IDs. Active collections now reject these submissions before any main/sibling/nested save hook: `cv_additions_not_allowed`
for nonempty edit-only extras; generic `cv_invalid_row` for missing, malformed, foreign, filtered or mismatched retained
identities. Removing an Add button does not establish server policy. Keep nonform errors and management fields in
copied templates; invalid pages render HTTP 200 and invalid modals HTTP 422. See the
[validation contract](reference/formsets.md#validation-before-saves), the executable
[integer/UUID projection recipes](reference/formsets.md#exact-json-projections) and their actual runtime comparisons
in `tests/test1/test_conditional_migration_docs.py`; server rejection/zero-save cases live in `test_formsets_policy.py`.

Mandatory policy is reapplied after native `full_clean()` replaces cached errors, including when a later custom
clean recleans an earlier collection. See the executed
[repeated-validation regression recipe](reference/formsets.md#repeated-validation-regression-recipe): prohibited
extras and invalid identities remain rejected across repeated validation, for package and accepted native/custom
adapters, before any save. This does not make internal tree constructors/methods or an A8 `commit=False` policy public.

Conditional formsets that are off retain default skip (rows untouched) and explicit purge (managed queryset deleted),
with the existing parent-change permission and routed transaction. Native/custom validation and rollback remain
authoritative. Second/deeper sibling fragments now retain declaration indices and nested modal editor paths; remove
workarounds for the former first-child limitation. Request keys and `{html, rows}` responses are unchanged, and request
`pk` remains the actual authorized parent identity or unsaved `None`, distinct from projected PK grammar/enum metadata.
Integer/UUID-only prefixes, authorized ancestry and application-owned ModelChoice querysets remain the boundary.

## Request authorization and Guardian configuration

1.0 closes several request paths that reached data or writes past the documented permission checks, and settles
how django-guardian's global-permission fallback is configured. Most apps need no change. The steps below are for
code that relied on the old behavior, and for copied templates and Python overrides.

### HTTP DELETE on delete views

Before 1.0 every delete view inherited Django's `DeletionMixin.delete()`. An HTTP `DELETE` request deleted the object
without the confirmation form, without `cv_check_delete_protection()` and without the form hooks. That inherited route
was never a documented package API, and it is closed: `DELETE` now gets 405 on the core, Guardian and polymorphic
delete views.

- **Clients and tests** that send `DELETE` must post the confirmation form instead, as the bundled form does, for
  example `client.post(url, {"confirm": True})`. The POST runs validation, the protection check, the hooks and the
  transaction.
- **A subclass that adds `"delete"` back to `http_method_names`** does not reopen the route: the request still gets
  405, and `Allow` and `OPTIONS` still leave `DELETE` out. There is no opt-in for a `DELETE` lifecycle.
- The earlier gates are unchanged, so an anonymous user is still redirected to the login page. A user without the
  permission still gets 403, a missing object on a core view 404, and an inactive Guardian user 403. See
  [HTTP methods](reference/delete_view.md#http-methods).

### Custom Guardian child-view compositions

A custom child view that omits its Guardian child mixin or places it after the core object/list view can
bypass child authorization. Such compositions now produce `crud_views_guardian.E001` during system checks and
raise `ImproperlyConfigured` before request processing, including when system checks were not run.
Use the corresponding shipped `Guardian*ViewPermissionRequired` class, or add `GuardianObjectPermissionMixin`
for object views / `GuardianQuerysetMixin` for list and card views before the core view class. Preserve cooperative
`super()` calls in overrides. The shipped Guardian views, parent-only create gate and top-level behavior are unchanged.
See [Custom child-view compositions](reference/guardian.md#custom-child-view-compositions).

### The GuardianViewSet global-permission key

`GuardianViewSet(cv_guardian_accept_global_perms=...)` never changed access: every view read its own attribute. The
key is removed and now fails with a `ValidationError` naming the replacement. Before:

```python
cv_author = GuardianViewSet(model=Author, name="author", cv_guardian_accept_global_perms=True)


class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author
```

After, on each view that should accept global model permissions:

```python
cv_author = GuardianViewSet(model=Author, name="author")


class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True
```

If you passed `False`, drop the key: strict is the default. Views you leave alone keep their policy, because the key
never reached them. `GuardianViewSet.get_objects_for_user()` stays strict whatever the views say. It has no
global-permission option, so code that needs global fallback for a query calls guardian's own `get_objects_for_user`
with `accept_global_perms=True`. See [Strict Mode](reference/guardian.md#strict-mode-default).

### Delete previews and protected objects

With `cv_show_related_objects`, `protected_objects` now holds ordered `obj`/`url` entries for protected objects the
user may view, selected within the display budget. `obj` is the model instance; `url` is always `None`. Preview
labels, tree and summary keys still depend on that option. `has_protected_objects` is now present on every delete
GET/POST context regardless of the option, and combines native and provider blockers before permission filtering.
`delete_preview_incomplete` is also always present. Inspection reads supported metadata without executing deletion
handlers, factories or model deletion. Unknown/custom effects leave boundaries and partial counts, including on
ordinary ordered-model Author and polymorphic Car pages. The aggregate disclosure policy is unchanged; incomplete
summaries qualify their integer counts in the heading. See the [provider contract](reference/delete_view.md#inspection-and-provider-api).

The shared `CRUD_VIEWS_DELETE_PREVIEW_LIMIT` now defaults to **50**. An unset `cv_delete_preview_limit` inherits the
project setting; ordinary base-view inheritance preserves explicit values. Set a positive integer or explicit
`None` for unlimited, which never means inherit. The project value is startup-captured. Raw booleans, strings,
floats, zero, negative integers and containers are invalid: `crud_views.E109` always reports invalid project
configuration, while a valid explicit view override remains usable. `viewset.E265` reports invalid view values;
an invalid effective value raises `ImproperlyConfigured` before GET/POST context preparation even with previews
off or non-strict operation.

Visibility filtering precedes protected-first selection and depth-first cascades. Every displayed occurrence,
including repeated objects and the root, consumes a slot. Hidden rows have no placeholder and their permitted
children are promoted in order. Full summaries and application redaction remain independent of selected details.
Only selected cascade entries call the existing optional URL hook. Protected navigation is removed; selected
cascade links retain ordinary full-page navigation. `delete_preview_truncated` is detailed-preview-only and emits
one translated "This preview is shortened. Additional objects are not shown." notice for actual visible overflow,
not an exact cap or hidden-only tail. Unlimited mode never emits it. Keep the independent incomplete warning.
Selected solo-root details render with an empty summary: root alone at limit one fills the cap, while root plus a
visible child exceeds it. Omit the detail frame when no cascade occurrence is selected.

The cap reduces selected presentation work; it does not bound total graph memory, filtering cost or total queries.
Full inspection and visibility filtering still run. Unlimited mode restores all permitted labels and optional URL
work. See [component costs and overrides](reference/delete_view.md#collection-cost-and-overrides) for attributed
core/Guardian measurements and application-hook limits. Deletion authority and complete blocking remain unchanged.

- **A copied `crud_views/view_delete.content.html`**: include the snippet on the new flag as well. A copy that still
  tests `related_summary or protected_objects` drops the whole snippet when the user may view no protected object.
  Use `related_summary or has_protected_objects or related_objects or delete_preview_truncated` and keep the
  incomplete warning independent of that include.

- **A copied `crud_views/snippets/delete/related_objects.html`**: show the blocked notice on the flag and list only
  `protected_objects`, which is already filtered. Bind it as caller-context `items` and use the dedicated body
  template; generic alert `items=protected_objects` rendering no longer accepts this item shape. Use the complete recipe in
  [Copied delete templates](#copied-delete-templates-with-incomplete-previews) so hidden labels still get explanatory text. Do not fetch protected objects
  another way.

- **A custom `cv_filter_related_objects`** now has to filter `related.protected` as well as the tree. Return only
  protected objects the user may view, never the raw `related.protected`. Start from
  `super().cv_filter_related_objects(user, related)`, which is the core model-level filter on a core view and the
  Guardian object-grant filter on a Guardian view, and narrow its result. On a Guardian view, do not also run the core
  model-level filter: it hides labels that an object grant permits. Leave `has_protected_objects` and the summary
  alone: the flag is computed before your hook runs. See
  [Custom related-object filters](reference/delete_view.md#custom-related-object-filters).
- **Guardian delete views:** the delete view's own `cv_guardian_accept_global_perms` decides whether a global
  `<ct.app_label>.view_<ct.model>` permission, resolved through guardian's content type, shows related/protected
  labels, not only whether it opens the page. An object grant shows a label without any global permission. Under
  the default concrete resolver `PublisherProxy` uses `app.view_publisher`, never a proxy-only
  `app.view_publisherproxy` grant; `Car` under a polymorphic base resolver uses `app.view_vehicle`. Strict mode
  ignores global fallback. See [Guardian cascading deletes](reference/guardian.md#cascading-deletes-with-per-object-permissions).

### Blocked deletions

Every delete page now has `has_protected_objects`, derived from native plus provider blockers even with
`cv_show_related_objects = False`. The stock content template omits the entire confirmation form while blocked,
including its checkbox, submit and form-contained cancel control, matching the custom-protection page. In a copied
`crud_views/view_delete.content.html`, keep the custom-protection branch and snippet include guard
`{% if related_summary or has_protected_objects or related_objects or delete_preview_truncated %}`, and wrap the entire form in
`{% if not has_protected_objects %}`. The complete content/snippet recipe below also retains the independent
incomplete warning, custom-protection branch and hidden-label notice.

A copied alert leaf must render `alert.text` or `alert.body_template` as well as heading/items; otherwise the generic
sentence disappears. Labels remain escaped and permission-filtered, and summary counts keep their existing policy.

A confirmed POST stopped by the early check returns **200** full page / **422** modal with storage intact.
The fresh-write race backstop applies only to exact Django `Model.delete`: adapted native collection emits a private
marker when native protection is observed before any custom collection callback has been entered. `post` translates
that marker after the atomic block unwinds. It does not infer origin from graph certification or traceback frames.
Native `PROTECT` stops immediately; `RESTRICT` reconciles the supported native closure. Provider-deleted rows do not
clear a native restricted row outside that closure.

Other actual model methods receive `delete(using=...)` once, retaining ordered sibling reordering and polymorphic
parent semantics. Their stale protection errors propagate. Custom callbacks, factories, private collectors, loaders,
signals and lifecycle hooks also retain their errors. A custom callback that returns before a later native block
makes that later native error propagate too: its effects may already have happened. With `cv_atomic=False`, database
effects can survive that failure; external I/O cannot be rolled back even with an atomic block. Commit callback
failure leaves committed deletion intact. Friendly native markers do not certify external rollback.
Delegate custom `post` to the standard path for HTTP handling; direct `cv_form_valid_process` callers own the gates.

Inspection uses full display rows, not `NestedObjects` or executable collection. Large cascades still materialize;
there is no large-graph bound. ORM reads can run application converters/managers/read signals. Providers and filters
must be read-only trusted application code, not a sandbox. Read/provider/render failures propagate.

### Safe deletion preview overrides

Remove every `cv_get_related_objects()` override immediately. Startup check **`viewset.E263`** and runtime
`ImproperlyConfigured` name `cv_get_delete_preview` and `cv_filter_related_objects` as replacements; the legacy method
is never invoked. Its base implementation remains a read-only accessor, and the old `RelatedObjects` import works.

This example assumes your existing `Document.delete(*, using)` deletes `PreviewNote` rows whose integer
`document_key` equals the document PK, then delegates to Django. That method's only extra deletion effect is these
notes. Move the old preview's extra rows into a boundary contribution; narrow only already-permitted display data.
Import your existing ViewSet from a module that does not import this view. The example deliberately leaves other
boundaries unresolved. Do not attest this contract for an arbitrary model or library override.

```python
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.deletion import DeletePreviewContribution
from crud_views.lib.views import DeleteViewPermissionRequired
from myapp.models import Document, PreviewNote
from myapp.viewsets import cv_document


class DocumentDeleteView(CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm
    cv_show_related_objects = True

    def cv_get_delete_preview(self, boundaries, *, using):
        contributions = list(super().cv_get_delete_preview(boundaries, using=using))
        for boundary in boundaries:
            if boundary.kind == "model_delete" and boundary.model is Document:
                notes = tuple(PreviewNote.objects.using(using).filter(document_key__in=boundary.source_pks))
                contributions.append(DeletePreviewContribution(boundary, deleted=notes, complete=True))
        return contributions

    def cv_filter_related_objects(self, user, related):
        related = super().cv_filter_related_objects(user, related)
        # Additional business redaction after core/Guardian authorization, never raw protected rows.
        return related._replace(protected=[row for row in related.protected if not getattr(row, "is_archived", False)])
```

Use the corresponding Guardian base class in a Guardian project. Its `super()` supplies the Guardian projection;
do not reapply the core model-permission filter afterward. The filter runs only with display enabled. The provider
runs even with display disabled, before the unfiltered blocked flag is computed. Never call deletion to simulate a
preview. Each boundary must match all six fields of the current supplied descriptor: `kind`, `model`, `field_name`,
`using`, **ordered** `source_pks` and `field_model`. Model-delete boundaries retain `field_model=None`.
Saved same-alias model tuples are required; invalid, duplicate, stale or cross-alias contributions raise `ValueError`.
`complete=True` attests only this boundary, not purity or completeness of other effects.

### Describing custom deletion effects

Suppose `Attachment.document` uses your custom `delete_attachments(collector, field, sub_objs, using)` handler,
whose complete effect is to cascade-delete those Attachment rows, with no further attachment relations or effects.
Describe that effect with reads on `using`; do not call the handler. Keep `complete=False` until you can attest the
whole effect. This standalone view is an alternative to the preceding one; combine their provider loops if you
need both descriptions. Any custom root-model method remains a separate unresolved boundary here.

**Immediate provider migration:** `DeletePreviewBoundary` appends the immutable `field_model` identity field.
Select supplied field descriptors by their declaring owner as well as source model and field name, as below.
Old copied **ownerless** `on_delete` or `private_relation` descriptors now raise `ValueError` before confirmation;
there is no grace period. Do not reconstruct an ambiguous source/name descriptor. A reconstructed descriptor must
equal a supplied descriptor in all six fields, including owner, alias and the exact ordered source batch.
Model-delete descriptors keep `field_model=None` and their existing construction remains valid.

Here `model is Document` and `source_pks` identify the inspected Document rows; `field_model is Attachment`
identifies who declares `document`, not those source rows. Each reverse relation, unsupported parent link and
private relation retains its declaring field model. A newly added `OtherAttachment.document` has a separate
boundary, including when it has no rows. The provider below must leave that boundary incomplete until another
explicit description attests it. One owner's contribution cannot complete another owner's effects.

```python
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.deletion import DeletePreviewContribution
from crud_views.lib.views import DeleteViewPermissionRequired
from myapp.models import Attachment, Document
from myapp.viewsets import cv_document


class DocumentEffectsDeleteView(CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm
    cv_show_related_objects = True

    def cv_get_delete_preview(self, boundaries, *, using):
        contributions = list(super().cv_get_delete_preview(boundaries, using=using))
        for boundary in boundaries:
            if (
                boundary.kind == "on_delete"
                and boundary.model is Document
                and boundary.field_model is Attachment
                and boundary.field_name == "document"
            ):
                rows = tuple(Attachment.objects.using(using).filter(document_id__in=boundary.source_pks))
                contributions.append(DeletePreviewContribution(boundary, deleted=rows, complete=True))
        return contributions
```

If your read-only policy also finds protected rows, return them as `protected=(row, ...)`: this is an additive veto
even without native protection. Contributions cannot remove native blockers or expand native `RESTRICT` closure.
Do not use `complete=True` merely to remove a warning. Full API fields and limits are in
[Inspection and provider API](reference/delete_view.md#inspection-and-provider-api).

### Copied delete templates with incomplete previews

Save this complete content override as `myapp/delete.content.html` and set your delete view's
`cv_content_template` to that path. It uses the package form frame and your copied snippet. The independent warning
survives previews disabled, hidden labels and custom protection. No extra acknowledgement replaces the ordinary
confirmation.

<!-- protected-delete-recipe: content -->
```django
{% extends "crud_views/snippets/form_frame.html" %}
{% load crud_views i18n %}
{% block cv_form_body %}
    {% if delete_preview_incomplete %}
        {% cv_alert "warning" text=_("This preview is incomplete. Custom deletion behavior may affect additional objects.") %}
    {% endif %}
    {% if delete_protection_errors %}
        {% include "crud_views/snippets/delete/protection_errors.html" %}
    {% else %}
        {% if related_summary or has_protected_objects or related_objects or delete_preview_truncated %}
            {% include "myapp/delete_related.html" %}
        {% endif %}
        {% if not has_protected_objects %}
            <form class="cv-form" method="post" action="{{ request.get_full_path }}" novalidate>
                {% csrf_token %}
                {{ form.non_form_errors }}
                {% cv_render_form %}
            </form>
        {% endif %}
    {% endif %}
{% endblock %}
```

Save the companion snippet as `myapp/delete_related.html`. Keep both notice branches; use only the filtered labels.
Partial counts stay numeric, qualified by the heading. A copied alert leaf must render body/text too.

<!-- protected-delete-recipe: related -->
```django
{% load crud_views i18n %}
<div class="cv-related-objects mb-3">
    {% if delete_preview_truncated %}
        {% cv_alert "warning" text=_("This preview is shortened. Additional objects are not shown.") %}
    {% endif %}
    {% if has_protected_objects %}
        {% if protected_objects %}
            {% with items=protected_objects %}
                {% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") body_template="myapp/delete_protected.html" %}
            {% endwith %}
        {% else %}
            {% cv_alert "error" heading=_("Deletion is blocked by protected relationships") text=_("Other objects still reference this one; remove or reassign them before deleting it.") %}
        {% endif %}
    {% endif %}
    {% if related_summary %}
        {% if delete_preview_incomplete %}
            {% cv_alert "warning" heading=_("Some related objects that will also be deleted (partial counts):") items=related_summary_items %}
        {% else %}
            {% cv_alert "warning" heading=_("The following related objects will also be deleted:") items=related_summary_items %}
        {% endif %}
    {% endif %}
    {% if related_objects %}
        {% with items=related_objects %}
            {% cv_alert "warning" heading=_("Details about the related objects to be deleted:") body_template="crud_views/snippets/delete/related_objects_tree.html" %}
        {% endwith %}
    {% endif %}
</div>
```

Save the independent protected-list body as `myapp/delete_protected.html`. This body is included inside the shared
alert frame; it owns neither the heading, icon, role nor dismissal. Its marker makes the custom recipe observable.
Keep explicit autoescape even when an outer template disables it (trusted Django safe strings retain their usual
semantics). Each entry has exactly `obj` and `url`; model fields are accessed as `node.obj.field`. Protected entries
always have `url=None` and render plain text, even with linking enabled. The old `if node.url`/`else` body remains
shape-compatible and always takes the text branch. There is no parallel legacy collection of model instances in context.

<!-- protected-delete-recipe: body -->
```django
{% autoescape on %}<ul data-protected-delete-recipe="body">{% for node in items %}<li>{% if node.url %}<a href="{{ node.url }}">{{ node.obj }}</a>{% else %}{{ node.obj }}{% endif %}</li>{% endfor %}</ul>{% endautoescape %}
```

The three marked fences above are the complete content/snippet/body chain. Recipe consumers capture exact UTF-8/LF
bytes after the opening fence through the final body newline, without trimming or dedenting. Each marker must be
unique and immediately precede its `django` fence; missing, duplicate, separated or wrong-language markers fail
validation. Tests and browser evidence use those same bytes and SHA-256 identities.

`cv_show_related_objects` enables detailed context; `cv_link_related_objects` enables optional **cascade** links.
Visibility filtering and display selection happen before cascade URL generation. Anchors perform ordinary full-page
navigation, including from a delete modal; the actual destination request remains authoritative. Protected labels
never become links. See [cascade linking](reference/delete_view.md#linking-related-objects).
Outer copied templates need the new `delete_preview_truncated` notice and independent summary/detail guards even
when their protected body remains compatible. Show exactly one translated shortening notice above all object lists
only when a further visible occurrence is omitted. Keep `delete_preview_incomplete` separate: both warnings can
appear together. Render a selected solo root even when `related_summary` is empty; that root consumes a slot.
With a limit of one, root alone is exact-at-cap, while root plus one visible child is overflow. Application-redacted
summaries must not hide retained details, and empty cascade details must not render a heading or empty list.
Collector/provider `protected` values and `cv_filter_related_objects(user, related)` inputs remain model instances;
only the filtered template context changes. Keep the independent `has_protected_objects` guard even if the list is
empty or absent with previews disabled. Migrate copied generic alert-items snippets immediately.

### Delete method signatures and database selection

Custom and library model methods execute once as `delete(using=...)`, preserving their real semantics. A method
without keyword `using` (including a positional-only parameter) fails startup check **`viewset.E264`** and raises
`ImproperlyConfigured` before invocation. Opaque signatures fail at runtime and require an inspectable adapter.
For your own model, accept and forward `using`; for example:

```python
def delete(self, *, using=None, keep_parents=False):
    return super().delete(using=using, keep_parents=keep_parents)
```

An inspectable `def delete(self, **kwargs): return super().delete(**kwargs)` adapter also works. Do not catch a
`TypeError` from inside deletion and retry, or bypass ordered/polymorphic overrides through `Model.delete`.

`cv_get_delete_db_alias()` is the new pinned accessor. After authorized saved-object resolution it calls the
`cv_get_db_alias()` selection hook once, validates the configured alias and shares it across inspection, deletion,
default atomic and `on_commit`. Its delete default uses `router.db_for_write(type(self.object), instance=self.object)`.
Before a saved target exists it raises `ImproperlyConfigured`. Direct process callers must supply one and own
authorization/confirmation. A selector may intentionally choose another alias: native execution reloads the same
model/PK there immediately before collection, using current non-PK and actual parent-link values rather than cached
parent descriptors. Custom methods still execute on the original authorized instance with `using` and own their
relation routing and external effects. Request inputs do not select the alias. See
[Execution order](reference/delete_view.md#execution-order) for native origin/PK state, missing-selected-row
propagation, null-join semantics and concurrency limits.

Migrate custom delete atomic overrides from repeated `cv_get_db_alias()` calls to the accessor:

```python
from django.db import transaction


def cv_get_atomic(self):
    return transaction.atomic(using=self.cv_get_delete_db_alias(), savepoint=False)
```

Preserve your `cv_atomic` policy when needed, or call `super().cv_get_atomic()`. Application hook queries must use
the intended alias explicitly. Atomic overrides and routers remain trusted; no cross-database transaction or
rollback of external effects is supplied. Generic create/update/resource lifecycle remains unchanged.

### Guardian permission keys

`GuardianViewSet.assign_perm`, `remove_perm` and `get_objects_for_user` now raise **`ValueError`**, rather than
`KeyError`, for an unknown key. Replace downstream `except KeyError` expectations with `ValueError` where handling
an invalid application selection is appropriate. Empty strings and **all non-string inputs** (`None`, integers,
bytes, lists, dicts) are programming errors with the same diagnostic, not silent denial. Validation precedes the
inactive-user shortcut, target queryset access and Guardian calls/writes. A valid key for an inactive user still
returns an empty queryset. No case, whitespace or Unicode normalization is performed.

For a `GuardianViewSet` with configured keys `zebra`, `réviser`, `alpha`, requesting `view` produces exactly:

```text
Invalid permission key 'view'. Valid keys: 'alpha', 'réviser', 'zebra'.
```

The message uses `repr` of the supplied value and the actual sorted configured keys:
`ValueError(f"Invalid permission key {perm!r}. Valid keys: {', '.join(repr(key) for key in sorted(self.permissions))}.")`.
Use the configured key exactly, and let programming errors propagate. Here `cv_document` is your existing
**GuardianViewSet**, and a valid `permission_key` is a string from its `permissions` mapping:

```python
from myapp.viewsets import cv_document


def visible_documents(user, permission_key):
    return cv_document.get_objects_for_user(user, permission_key)
```

The helper remains strict and reads an immutable `MappingProxyType` policy; per-view global fallback is independent.
Manage dictionaries are detached display copies, not mutable authority. Supported delete-preview database topology
requires actor/auth/grant/content-type routes co-located with candidate rows; unsupported topology hides labels
without clearing protection or aggregates. See [Guardian database topology](reference/guardian.md#delete-preview-database-topology).
The configured Car helper/list mismatch is repaired as described below. That bounded repair does not settle the
separate unclassified AUTH-06 residual or unspecified custom-PK/database-cast/collation precision backstop.

### Guardian configured content-type permissions

`GuardianViewSet` now discovers default permissions through Guardian's configured `GUARDIAN_GET_CONTENT_TYPE`
resolver. Previously a Car ViewSet inferred `app.view_car` even when Guardian selected Vehicle, so a valid
`view_vehicle` grant could raise `MixedContentTypeError` in the helper or list. Under a polymorphic-base resolver,
`GuardianViewSet(model=Car)` now infers `app.view_vehicle`; its queryset still contains Car instances.
With the default concrete resolver, Car retains `app.view_car`, while PublisherProxy uses `app.view_publisher`.

Set `GUARDIAN_GET_CONTENT_TYPE = "polymorphic.contrib.guardian.get_polymorphic_base_content_type"` in Django settings
before starting the application. After migrations have created Vehicle's permissions, put the following in your
ViewSet module. Here `myapp.models.Car` inherits from `Vehicle`. Include `cv_car.urlpatterns` in your project's URL
configuration as for other ViewSets. The functions accept an existing user/group and select a saved Car by PK.
Call `grant_car_view(user, car.pk)`, query `visible_cars(user)`, and use
`revoke_car_view(user, car)` to remove that grant. The registered strict list uses the same permission mapping.

```python
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from myapp.models import Car

cv_car = GuardianViewSet(model=Car, name="configured_car")


class CarListView(GuardianListViewPermissionRequired):
    cv_viewset = cv_car


def grant_car_view(user_or_group, car_pk):
    car = Car.objects.get(pk=car_pk)
    cv_car.assign_perm("view", user_or_group, car)
    return car


def visible_cars(user, queryset=None):
    return cv_car.get_objects_for_user(user, "view", qs=queryset)


def revoke_car_view(user_or_group, car):
    cv_car.remove_perm("view", user_or_group, car)
```

Audit existing grants against the selected content type before deploying; this discovery correction does not copy
or convert stored permission rows. Defaults include only Permission rows on that selected type. For example,
Vehicle's `inspect_status_vehicle` becomes key `inspect_status` with value `app.inspect_status_vehicle`.
Only the exact terminal `_<selected_type.model>` suffix is removed. Child-only `child_only_car` is no longer an
inferred key when the selected type is Vehicle; move the intended permission/grants to Vehicle or deliberately
choose a compatible resolver and mapping. There is no compatibility grace period or child/base permission union.

An application's explicit `permissions` property override remains authoritative: exact string keys and qualified
values are forwarded unchanged. No trimming, normalization or automatic child-to-base translation occurs.
An explicit `app.view_car` mapping under a Vehicle resolver remains incompatible and raises Guardian's original
`MixedContentTypeError`; fix the configuration rather than catching it as empty access. Invalid keys still raise
`ValueError` with the actual sorted available keys, including selected-type custom keys.

Nonempty discovered defaults are cached on the ViewSet for its process lifetime; empty discovery retries.
Configure the resolver before startup. Changes to permissions or the resolver after discovery need a fresh
ViewSet or process restart; runtime setting hot reload is not promised. The strict helper, per-view global
fallback, object/group grants, active-superuser behavior, inactive denial and manage policy remain unchanged.

### The Guardian manage page

The context of `GuardianManageView` no longer has `guardian_config.cv_guardian_accept_global_perms`; a template that
reads it renders an empty cell. Read the strict helper policy from `guardian_config.get_objects_for_user`, and each
view's own policy from `views.<key>.guardian_policy`:

```django
{% for view_key, view in views.items %}
    {{ view_key }}: {{ view.guardian_policy.effective_policy }}
{% endfor %}
```

`effective_policy` is `"strict"`, `"global fallback"` or `"not applicable"`. `global_fallback_applicable` and the view's
`cv_guardian_accept_global_perms` (`None` when not applicable) sit next to it. Who may open the page is unchanged. See
[GuardianManageView](reference/guardian.md#guardianmanageview).

### Nested Guardian create access

The helpers `cv_has_access(user, obj)` and `cv_create_has_access(user, view, parent_obj)` of a nested
`GuardianCreateViewPermissionRequired` used to return `True` for any object that was not a parent instance. Now:

- **A parent instance** works as before.
- **An own child with a `ForeignKey` parent**, such as a Book on its detail page, is resolved to its actual parent
  through `ParentViewSet.get_attribute()`. "Add book" on a Book page therefore follows the user's permission on that
  Book's Publisher; before, it always passed. Keep passing the page object; do not swap in the parent yourself.
- **An unrelated object, an own child without its parent, or `None`** denies, superusers included. If you called the
  helper with such an object, pass the parent instance instead.
- **An own child with a `ManyToMany` parent** (`many_to_many_through_attribute`) denies: the object belongs to several
  parents and cannot say which one a create would use. An object-only control, `cv_context_has_permission:"create"`
  on that child's page, or a helper call with the child, is therefore unavailable. Do not select the first or only
  related parent to get it back. Pass an explicit parent instance to the helpers, or link to the child list under the
  URL parent: its create control and the create URL itself still work for an authorized parent. Route-aware create
  controls for such pages need an explicit selected-parent contract, which 1.0 does not provide.

The helpers check permission only. A rendered create control also needs its action state: on a child page the
control's `cv_action_enabled` hook receives the actual parent (the Publisher), while its label template still sees the
page object (the Book). So `cv_context_has_permission` can be `True` while the control renders nothing. The recipes in
[Context Buttons](reference/context_buttons.md#cv_context_has_permission-gate-surrounding-markup) and the
[FAQ](faq.md#gate-surrounding-markup-by-permission) show what to use where. On a child **list** page the URL-bound
control is unchanged, and the filter stays `False` there because the page has no object.

The parent `None` policy changed with it. `cv_guardian_parent_permission = None` (or the create key) skips only the
permission check now. A missing URL parent is a 404, a create under a parent whose `cv_action_enabled` is `False` is a
403, and the helpers return `True` for the parent and a `ForeignKey` own child without any grant. Top-level create
still needs the model-level `add_<model>` permission. See
[What the create access helpers accept](reference/guardian.md#what-the-create-access-helpers-accept).

### Inactive users and formset row requests

These are fixes and need no change unless your app relied on the old behavior:

- **Inactive users** (logged in through a backend such as `AllowAllUsersModelBackend` with `is_active = False`) get
  403 from every Guardian view and nothing from the Guardian helpers, superusers included. There is no setting to
  restore their access. See [Inactive users](reference/guardian.md#inactive-users).
- **Formset row requests** run the editor page's gates first: 403 or 404 for users who may not open the editor.
  Their coordinates are then checked against the declaration and the stored ancestry, and a malformed or forged
  request gets 400. `formset.js` sends valid requests. Custom JavaScript or tests that build `template`, `pk`, `num`
  and `formset_parent_prefix_key` by hand must send the values the page renders: `None` for the root of a create
  page and for unsaved rows (also with UUID keys), `0` as the top-level index, and the declared child index at each
  nesting level. Second/deeper child declarations now retain the same index in page and fragment rendering,
  including nested actions in newly inserted modal rows. Integer/UUID-only prefixes remain the supported boundary; see
  [The AJAX template endpoint](reference/formsets.md#the-ajax-template-endpoint).

## A downstream theme

Templates to delete or move, the hooks that replace copied templates, and contract changes in templates you still override.

Most of 1.0's theme work replaces copied templates with registered values and small leaves: the
[button class table](reference/buttons.md#the-class-table), the [icon registry](reference/icons.md#registering-icons-from-a-theme),
the [form frame](reference/theme.md#framing-the-form-pages), the [alert frame](reference/theme.md#alerts) and the
[card blocks](reference/card-list-view.md#custom-card-template). Upgrading a theme is mostly deleting copies.
`crud_views_tabler` ships its own update for 1.0.

### Templates to delete

Go through your theme's `templates/crud_views/` directory. Delete each of these copies:

- **`tags/messages.html`** (#250). It is a loop over `tags/alert.html` now, and the dicts it receives have `level`
  and `text` instead of `css_class` and `message`. A copy that reads the old keys renders `class="alert alert-"` with
  an empty body. Override `tags/alert.html` (box, icon, heading, close button), `snippets/alert/text.html` or
  `snippets/alert/list.html`, and register the colours as `alert:error`, `alert:warning`, `alert:success`,
  `alert:info` and `alert:debug` ([Alerts](reference/theme.md#alerts)). A `tags/alert.html` override uses the new close
  hook ([Contract changes](#contract-changes-in-templates-you-still-override)). Python code that imports
  `ALERT_CLASSES` or `ICON_NAMES` from `crud_views.lib.messages` uses `LEVELS` and the `message-<level>` icon names
  instead.
- **`tags/button_submit.html`, `tags/button_cancel.html`, `tags/button_delete.html`.** Nothing renders them any more;
  the form buttons come from crispy's `Submit`, `Button` and `Reset` and take their classes from the `form:*` keys
  ([Forms](reference/buttons.md#forms)).
- **`tags/icon.html` [0.30]** and **`crud_views/detail/`** (#217). Nothing renders them.
- **`view_create.content.html`, `view_update.content.html`, `view_custom_form.content.html`,
  `view_delete.content.html`**, if you copied them to wrap the form in a card or similar (#239). They extend
  `snippets/form_frame.html` now: override its `cv_form_frame` block instead
  ([Framing the form pages](reference/theme.md#framing-the-form-pages)). A 0.29 copy also misses two fixes: its
  `<form>` has no `enctype="multipart/form-data"`, so file fields upload nothing on create and custom-form pages
  (#236), and the create copy renders `{{ form.media }}` twice (#191). The delete page's protection alert moved to
  `snippets/delete/protection_errors.html`.
- **Copies made only to change a heading level** (#251): `tags/card.html`, `modal/content.html`,
  `crud_views_workflow/view_workflow.action.html` and `view_workflow.history.html`, and the object-detail
  `crud_views_object_detail/layouts/*/group.html`. Set `CRUD_VIEWS_HEADER_LEVEL` to the level of your
  `{% cv_header %}` instead. These headings then render one level below it and keep their look
  ([Heading levels](reference/templates.md#heading-levels)).
- **Copies of `tags/button/action.html`, `tags/button/menu_item.html`, `tags/actions_menu_toggle.html` or
  `tags/context_action_filter.html` made only to put the icon class on the button itself** (an icon library that
  paints `::before` on the button, #258). Register the library with `placement: "host"` instead; the stock leaves
  then add the icon's class to the button, and the `*:icon-host` button classes add a base class where a kind of
  button needs one ([Host placement](reference/icons.md#host-placement)).
- **`snippets/pagination.html`**, if you overrode it only for the arrows (#241). Register the `page-previous` and
  `page-next` icons instead. If you keep it for other markup, take over the accessible markup described under
  [CSS and tests](#css-and-tests-that-select-on-markup).

### Templates to move

The 0.29 templates that rendered one button are **logic templates** now: one line that calls a tag. Old copies still
render, but they bypass the leaf contract, so new options (label modes, variants, disabled actions) don't reach
them. Move the markup into the leaves and delete the copies
([Logic templates and leaves](reference/buttons.md#logic-templates-and-leaves)).

The leaves receive the flat [leaf contract](reference/buttons.md#the-leaf-contract), not the keys your 0.29 copy
reads. Markup moved over unchanged renders `href=""` and no icon, and raises nothing. Rename as you move:

| 0.29 key | Leaf key |
|---|---|
| `cv_url` | `cv_href` (present only when `cv_tag` is `"a"`) |
| `cv_icon_action` | `cv_icon`, rendered with `{% cv_icon cv_icon %}` |
| `cv_action_label`, `cv_label` | `cv_label` |
| `cv_action_short_label` | `cv_short_label` |
| `cv_is_active` | `cv_active` |
| `cv_form_{{ cv_oid }}`, `cv_list_action_method` | `cv_submit_target` (present only for a POST action) |
| `cv_access`, `cv_action_enabled` | gone: an action the user may not see never reaches the leaf; `cv_disabled` and `cv_disabled_reason` mark a disabled one |
| `cv_no_label` | `cv_label_mode` |

Which template takes the markup:

| 0.29 copy | Move the markup to |
|---|---|
| `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` | `tags/button/action.html`, one leaf for all three locations (`cv_location`) |
| `tags/actions_menu_item.html` | `tags/button/menu_item.html` |
| `tags/actions_menu_item_label.html` | `tags/button/menu_item_label.html`; the stock menu no longer includes the old one |
| `tags/context_actions.html`, `columns/actions.html` | `tags/button/container.html` (receives `cv_buttons`, `cv_group`, `cv_location`; the element is the `<location>:container-tag` key) |

- **`tags/card_action.html` copies that branch on `cv_no_label`** break silently. The card action context no longer
  carries `cv_no_label`; it carries `cv_label_mode`. So a copy renders the label on every button, including
  supported icon-only actions (`CardAction(label_mode="icon")`). Removed Python `no_label` inputs fail validation
  before rendering; see [Removed card label keyword](#removed-card-label-keyword).
  The leaf branches on `cv_label_mode` (`"label"`, `"icon"`, `"both"`)
  ([The leaf contract](reference/buttons.md#the-leaf-contract)).

### Hooks instead of copies

Register these from your theme's `AppConfig.ready()`; a project's own settings still win over them.

- **Button classes:** `register_button_classes({...})` with `location:slot` keys, optionally
  `location:variant:mode` ([The class table](reference/buttons.md#the-class-table)). 1.0 adds the utility slots
  `*:active`, `card:flex` and `*:hidden-label` (#227), the card keys `card:root`, `card:body`, `card:title` (#243),
  the alert keys `alert:*` (#250), the `*:icon-host` keys for host-placed icons (#258), and the `form:*` keys for the
  crispy buttons. A theme on a framework that spells
  `active` or `visually-hidden` differently registers its own words and overrides no leaf
  ([A theme recipe](reference/buttons.md#a-theme-recipe)).
- **Icons [0.30]:** `register_icon_library(prefix, renderer=..., **config)` and `register_icons({...})`
  ([Registering icons from a theme](reference/icons.md#registering-icons-from-a-theme)). 1.0 adds the names
  `page-previous`, `page-next` and `message-success`, `message-info`, `message-warning`, `message-error`,
  `message-debug` ([Default table](reference/icons.md#default-table)), and the library keys `placement` and
  `standalone` for an icon library that puts the icon class on the button itself (#258,
  [Host placement](reference/icons.md#host-placement)).
- **The form frame:** `snippets/form_frame.html`, block `cv_form_frame` (#239).
- **The card:** extend `tags/card.html` and fill `card_title`, `card_content` and `card_actions` (#243). A copy of
  `view_card.content.html` misses the translated empty state, "No items found." (#246).
- **The alert frame:** `tags/alert.html` and its two bodies (#250). Its close control carries
  `data-cv-alert-dismiss` ([Contract changes](#contract-changes-in-templates-you-still-override)); a styled copy
  starts from the [Custom alert frame](reference/theme.md#custom-alert-frame) recipe.
- **Heading levels:** `CRUD_VIEWS_HEADER_LEVEL`, plus `{% cv_heading %}` for the headings in your theme's own
  templates, so they follow the same setting (#251, [Heading levels](reference/templates.md#heading-levels)).
- **JavaScript:** `cv.adapters.modal`, `cv.adapters.tooltip`, `cv.adapters.collapse` and `cv.adapters.alert` replace
  Bootstrap's API for a theme on another framework ([`cv.adapters`](reference/javascript.md#cvadapters)).
  `alert.close(el)` is new: it closes a dismissible alert
  ([Dismissible alerts](reference/javascript.md#dismissible-alerts)). How the theme assigns its adapters matters:
    - A partial map assigned **before** `adapters.js` loads needs nothing: every entry it leaves out, `alert`
      included, gets its default while `adapters.js` loads.
    - A theme that replaces the **whole map after** core loads (`cv.adapters = {...}`) discards the defaults, and
      core does not fill them in again. Its map must provide `alert` with `close(el)`, or every alert close button
      throws a `TypeError` and the alert stays. Replace single entries (`cv.adapters.modal = {...}`) or merge into
      the existing map (`Object.assign(cv.adapters, {...})`) instead; a map for a Bootstrap-compatible namespace
      takes the entry from the factory, `alert: cv.bootstrapAdapters(ns).alert`.

### Contract changes in templates you still override

- **Icon values [0.30].** `cv_icon_action`, `cv_icon_header` and `cv_menu_icon` hold icon values (`"detail"`,
  `"fas:truck"`), not CSS classes. Render them with `{% cv_icon cv_icon_action %}`; `<i class="{{ cv_icon_action }}">`
  renders an invisible icon for every stock action. The object-detail filters `icon_class` and `named_icon_class`
  are gone: an old copy of an object-detail layout or type template fails with `TemplateSyntaxError`. Use
  `{% cv_icon group.icon css="me-2" %}` and `{% cv_icon "boolean-true" %}`.
- **`fa-fw` [0.30]** in menu icons becomes `cv-icon-fw` from `crud_views/css/icons.css`.
- **Host-placed icons** (#258). A leaf you still override renders today's markup for every library without
  `placement: "host"`. To support a host library too, take over what the stock leaves do: append
  `{{ cv_icon_class }}` to the button's `class` when it is set, and render `{% cv_icon cv_icon %}` only when
  `cv_icon_inline` is true ([The leaf contract](reference/buttons.md#the-leaf-contract)). The menu toggle reads
  `cv_menu_icon_class` / `cv_menu_icon_inline`. A filter-toggle copy renders, for a host library and in the
  icon-bearing modes, the current state's class on the button plus `data-cv-filter-icon-open` /
  `data-cv-filter-icon-close` instead of the two spans
  ([The filter toggle contract](reference/javascript.md#the-filter-toggle-contract)).
- **Action menus:** `cv_menu_wrapper_class` and `cv_toggle_class` are no longer in the context of
  `tags/actions_menu.html` and `tags/actions_menu_toggle.html`; use `{% cv_button_class cv_location "menu-wrapper" %}`
  and `"menu-toggle"`. These two templates are still the ones to override for a framework with a different dropdown
  ([Templates that follow Bootstrap's DOM](reference/theme.md#templates-that-follow-bootstraps-dom)).
- **The filter toggle** (`tags/context_action_filter.html`). Its context carries the resolved `cv_label_mode`
  (#262), which decides whether the toggle has icons; a copy that ignores it renders the icon form in every mode.
  The icon instructions below apply to the icon-bearing modes, `"icon"` and `"both"`. A 0.29 copy renders one
  `<i class="{{ cv_icon_action }}">`, and 0.29's `list.filter.js` swapped its Font Awesome classes. In 1.0
  `cv_icon_action` is the icon name `"filter"`, so that `<i>` is invisible, and the script toggles two marked spans
  instead: render `<span data-cv-filter-icon="open">{% cv_icon "filter" %}</span>` and
  `<span data-cv-filter-icon="close">{% cv_icon "filter-close" %}</span>`, and hide the inactive one with the
  `hidden` attribute (#232). A 0.30 copy already has the two spans but hides them with `class="d-none"`: switch to
  `hidden`. In `"label"` mode the stock toggle renders its constant visible label without icon spans, host icon
  classes or `data-cv-filter-icon-*` attributes. In every mode render `aria-expanded` and
  `aria-controls="filter-collapse"`; the `#filter-collapse` id is a contract
  ([The filter toggle contract](reference/javascript.md#the-filter-toggle-contract)). For adopting the resolved modes,
  constant labels and optional icon hooks, see [The filter toggle](reference/context_buttons.md#the-filter-toggle).
- **The alert frame** (`tags/alert.html`). The close control carries `data-cv-alert-dismiss` instead of Bootstrap's
  `data-bs-dismiss="alert"`; `viewset.js` hands its nearest `role="alert"` frame to `cv.adapters.alert.close`.
  Replace the attribute completely, so the control carries only the new hook:

    ```django
    {# before #}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>
    {# after #}
    <button type="button" class="btn-close" data-cv-alert-dismiss aria-label="{% translate 'Close' %}"></button>
    ```

    Keep `role="alert"` on the frame. Closing needs the core scripts `adapters.js` and then `viewset.js`, which
    `{% cv_js %}` renders in that order ([What the scripts need](reference/javascript.md#what-the-scripts-need)). The
    default adapter uses Bootstrap's `Alert` when its JavaScript is loaded and otherwise removes the alert
    ([Dismissible alerts](reference/javascript.md#dismissible-alerts), [Flash messages](reference/messages.md)).
    Migrate even if you keep Bootstrap. A copy that keeps only `data-bs-dismiss="alert"` still closes through
    Bootstrap's own data API, as long as it keeps Bootstrap's frame markup (the `alert` class) and Bootstrap's
    JavaScript is loaded; it never reaches `cv.adapters.alert`, so it gains neither a theme's adapter nor the removal
    without Bootstrap's `Alert` until you switch it. Do not keep both attributes: such a control is dismissed by
    Bootstrap and by core. The frame's `alert-dismissible fade show` and `btn-close` classes are still literal
    Bootstrap CSS; to style them your way, start from the tested
    [Custom alert frame](reference/theme.md#custom-alert-frame) recipe.

- **The modal:** the close button in `modal/content.html` uses `data-cv-modal-dismiss`. A copy with `data-bs-dismiss`
  keeps working under the Bootstrap adapter only. `{% cv_config %}` renders the modal shell from `modal/shell.html`,
  which you can override on its own ([Theming the modal](reference/modals.md#theming-the-modal)).
- **Formset controls** (`formsets/control.html`): add `data-cv-class` and `data-cv-class-danger` to the delete
  toggle (`formset.js` reads the classes from them), or it is no longer recoloured. Add `data-cv-tooltip="formset"`
  and the translated `title`s.
- **Object detail property-detail button:** `title` and `data-cv-tooltip="object-detail"` instead of `data-bs-title`,
  classes from the `object-detail:property-detail` key.
- **Table sort icons [0.30]** in `table/bootstrap5.html`: `{% cv_icon "table-sort-asc" %}` and
  `{% cv_icon "table-sort-desc" %}` instead of Font Awesome 4 classes.
- **Button container** (`tags/button/container.html`, #266): `cv_container_tag` is gone; the three logic templates
  no longer pass it. A copy of the container leaf that reads it renders `<>`: read `cv_layout.tag` and
  `cv_layout.label` from `{% cv_container_layout %}`, and render nothing when `cv_layout.empty`. A copy of
  `context_actions.html`, `columns/actions.html` or `card.html` that passed another tag sets
  `<location>:container-tag` instead ([Container element and label](reference/buttons.md#container-element-and-label)).
- **Active state:** `snippets/card_order.html` and the leaves take `active` from the `*:active` keys (#227). A copy
  with a hard-coded `active` keeps working.

### Table pagination overrides

`crud_views/table/bootstrap5.html` keeps the django-tables2 block names `pagination`, `pagination.previous`,
`pagination.range` and `pagination.next`. What changed is when `pagination.previous` and `pagination.next` run. Before
1.0 each block sat inside an availability test, so it rendered only when the page existed. In 1.0 it runs on every
paginated page, available direction or not, and holds the test itself, so a theme can restyle the disabled end in
the same block. A copied override that calls `table.page.previous_page_number` or `table.page.next_page_number`
without a test now raises `django.core.paginator.EmptyPage` on the first or the last page. Test
`table.page.has_previous` before calling `previous_page_number`, and `table.page.has_next` before calling
`next_page_number`.

If you overrode the blocks only to swap the `&laquo;` / `&raquo;` arrows, delete the override instead. Map the
`page-previous` and `page-next` icons in `CRUD_VIEWS_ICONS` and style the hidden labels with the
`pagination:hidden-label` key. This works for table and card pagination alike ([Pagination](reference/list_view.md#pagination)).
A structural copy that you keep has to adopt the shared key and the accessible structure:

- The `<nav>` label is the translated msgid `pagination`, which the stock `pagination` block already renders.
- An available direction is an `li` with the classes `previous page-item` or `next page-item` and a link. A missing
  direction is an `li` with `previous page-item disabled` or `next page-item disabled` and
  `<a class="page-link" aria-disabled="true">` without `href` or `tabindex`.
- Both states render `{% cv_icon "page-previous" %}` before the translated hidden `previous` label, and the hidden
  `next` label before `{% cv_icon "page-next" %}`. The label's class comes from
  `{% cv_button_class "pagination" "hidden-label" %}`; `cv_icon` supplies the decorative `aria-hidden` icon.
- The current page in `pagination.range` is a `<span class="page-link">` in an `li` with `aria-current="page"`. Leave
  the range block alone unless you need a different range; an override of `pagination.range` works as before.

Save the override as a child template under its own name, for example
`myproject/templates/myproject/table.html`. It extends `crud_views/table/bootstrap5.html`. A copy saved at
`crud_views/table/bootstrap5.html` in your project's `DIRS` also works, because Django resolves `{% extends %}` to the
package's template, but it then replaces the stock template for every table that uses it. Select your own template at
startup in your settings:

```python
DJANGO_TABLES2_TEMPLATE = "myproject/table.html"
```

django-tables2 reads that setting when a table class is created, so changing it later does not retarget an existing
class. A `Meta.template_name` on a table class, or a `template_name` passed to the table, takes precedence; if you
set one, it must name the same child. This copy overrides both direction blocks, adds `rel` to the available links,
and keeps every hook of the stock markup:

```django
{% extends "crud_views/table/bootstrap5.html" %}
{% load crud_views i18n %}

{% block pagination.previous %}
{% if table.page.has_previous %}
    <li class="previous page-item">
        <a href="{% cv_querystring table.prefixed_page_field=table.page.previous_page_number %}" class="page-link" rel="prev">{% cv_icon "page-previous" %}<span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'previous' %}</span></a>
    </li>
{% else %}
    <li class="previous page-item disabled">
        <a class="page-link" aria-disabled="true">{% cv_icon "page-previous" %}<span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'previous' %}</span></a>
    </li>
{% endif %}
{% endblock pagination.previous %}

{% block pagination.next %}
{% if table.page.has_next %}
    <li class="next page-item">
        <a href="{% cv_querystring table.prefixed_page_field=table.page.next_page_number %}" class="page-link" rel="next"><span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'next' %}</span>{% cv_icon "page-next" %}</a>
    </li>
{% else %}
    <li class="next page-item disabled">
        <a class="page-link" aria-disabled="true"><span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'next' %}</span>{% cv_icon "page-next" %}</a>
    </li>
{% endif %}
{% endblock pagination.next %}
```

The card pagination (`crud_views/snippets/pagination.html`) has no blocks, and its default markup is unchanged by
this; its earlier migration is under [CSS and tests that select on markup](#css-and-tests-that-select-on-markup).

## Silent breaks

- [ ] Short action titles replace full context/list icon titles, and context-menu native titles are removed;
  migrate copied button/menu leaves and title assertions immediately ([Action tooltips](#action-tooltips)).

Everything that renders differently and raises nothing, as one checklist. A clean `manage.py check` says nothing
about these.

**In your project:**

- [ ] **[0.30]** Object detail group icons with a bare name (`icon="truck"`) render an invisible `<i class="truck">`:
  use `"fas:truck"` ([Views and Python code](#views-and-python-code)).
- [ ] `cv.cvModalOpen(url, "modal-lg")` and `data-cv-modal-size="modal-lg"` open the default size: use `"lg"`
  ([JavaScript](#javascript)).
- [ ] Hand-listed static files without `crud_views/js/adapters.js` lose the modal, filter and tooltip behaviour and
  alert dismissal ([Base template and your own templates](#base-template-and-your-own-templates)).
- [ ] A script that replaces the whole `cv.adapters` map after core loads without an `alert` entry makes every alert
  close button throw ([Hooks instead of copies](#hooks-instead-of-copies)).
- [ ] **[0.30]** Hand-listed static files without `crud_views/css/icons.css` lose the menu icon width.
- [ ] **[0.30]** An overridden `cv_get_filter_icon()` is no longer called ([Views and Python code](#views-and-python-code)).
- [ ] CSS, JavaScript selectors and tests that match the old markup: sort icons, pagination
  (`.disabled > span.page-link`, `&laquo;` / `&raquo;`), `d-none`, button attribute order and class strings,
  formset control titles, empty button containers that no longer render, the alert close control's
  `data-bs-dismiss="alert"` ([CSS and tests that select on markup](#css-and-tests-that-select-on-markup)).
- [ ] Card buttons show their icon next to the label, and card actions without a `variant` take the target view's
  variant ([Views and Python code](#views-and-python-code)).
- [ ] Form buttons are `<button>` elements: selectors and tests on `input[type="submit"]` or `input[name="reset"]` find
  nothing ([Markup and submitted data](#markup-and-submitted-data)).
- [ ] A form button value or label written as template code (`{{ request.user }}`) shows that text
  ([Values are literal text](#values-are-literal-text)).
- [ ] `helper.inputs = []` on a filter helper no longer hides Apply and Reset and drops the hidden sort inputs
  ([Filter helpers](#filter-helpers)).
- [ ] On a nested Guardian ViewSet, `cv_has_access`, `cv_create_has_access` and `cv_context_has_permission:"create"`
  deny an unrelated object and a `ManyToMany` own child, and a `ForeignKey` own child follows its parent's permission:
  a create control on such pages can disappear ([Nested Guardian create access](#nested-guardian-create-access)).
- [ ] A custom `cv_filter_related_objects` that returns `related.protected` unfiltered shows labels the user may not
  view ([Delete previews and protected objects](#delete-previews-and-protected-objects)).

**In a theme, or in project template overrides:**

- [ ] A `tags/messages.html` copy renders `class="alert alert-"` with an empty body
  ([Templates to delete](#templates-to-delete)).
- [ ] A `tags/alert.html` copy with `data-bs-dismiss="alert"` closes only through Bootstrap's JavaScript and ignores
  `cv.adapters.alert` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A copy of a form page's content template uploads no files on create and custom-form pages
  ([Templates to delete](#templates-to-delete)).
- [ ] Copies of `tags/button_submit.html`, `tags/button_cancel.html`, `tags/button_delete.html` and `tags/icon.html`
  are no longer rendered ([Templates to delete](#templates-to-delete)).
- [ ] A `tags/button/container.html` copy that reads `cv_container_tag` renders `<>`, and a logic-template copy that
  passes `cv_container_tag` loses its tag ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A `tags/card_action.html` copy that branches on `cv_no_label` shows the label on icon-only buttons
  ([Templates to move](#templates-to-move)).
- [ ] Markup moved into a leaf with its 0.29 keys renders `href=""` and no icon ([Templates to move](#templates-to-move)).
- [ ] A `tags/actions_menu_item_label.html` copy no longer changes the stock menu
  ([Templates to move](#templates-to-move)).
- [ ] **[0.30]** `<i class="{{ cv_icon_action }}">` (or `cv_icon_header`, `cv_menu_icon`) renders an invisible icon
  ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] `tags/actions_menu.html` and `tags/actions_menu_toggle.html` copies that read `cv_menu_wrapper_class` or
  `cv_toggle_class` render an empty `class` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A `tags/context_action_filter.html` copy shows no icon (0.29) or the wrong icon after the first click (0.30),
  and a copy that still ignores `cv_label_mode` stays icon-only where the project configures `"both"` or `"label"`
  for the toggle ([Contract changes](#contract-changes-in-templates-you-still-override),
  [The filter toggle](reference/context_buttons.md#the-filter-toggle)).
- [ ] A `formsets/control.html` copy without `data-cv-class` / `data-cv-class-danger` no longer recolours the delete
  toggle ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A custom form-button template that reads `input.value` renders empty attributes, and an override of crispy's
  `layout/baseinput.html` no longer styles the package form buttons ([Custom button templates](#custom-button-templates)).
- [ ] A `view_card.content.html` copy keeps the untranslated "No items found." ([Hooks instead of copies](#hooks-instead-of-copies)).
- [ ] A `view_delete.content.html` or `snippets/delete/related_objects.html` copy that tests `protected_objects`
  hides the blocked-deletion notice when the user may view no protected object
  ([Delete previews and protected objects](#delete-previews-and-protected-objects)).
- [ ] A copied protected list that treats entries as model instances, or passes them as generic alert `items=`,
  must use `node.obj`/`node.url` and an independent `body_template` inside the shared alert
  ([complete copied-template migration](#copied-delete-templates-with-incomplete-previews)).
- [ ] A Guardian manage template that reads `guardian_config.cv_guardian_accept_global_perms` renders an empty cell
  ([The Guardian manage page](#the-guardian-manage-page)).

## Modal adapter completed-hide lifecycle

Hand-written `cv.adapters.modal` objects must now provide `onHidden(modalEl, callback)` alongside
`show`, `hide` and `setSize`. There is no compatibility grace period. The method subscribes to completed
hiding and returns an idempotent unsubscribe function; it must not invoke the callback during subscription.
Notify after the modal is hidden and its focus trap/inertness is released, for Close, Escape, backdrop and
API dismissal alike. A prevented hide must not notify. Core consumes the callback once per open session
and unsubscribes on completed hide, failed open or replacement by a new session.

`cv.bootstrapAdapters(ns)` supplies this automatically, including Bootstrap and Tabler consumers.
Custom asynchronous adapters must await their completed-hide event; calling the callback immediately after
starting a hide animation is too early. Synchronous adapters may notify after completing hide and trap release.
Missing hooks and hooks that do not return a function log a descriptive error and navigate to the full page
before injecting/showing a modal. See the complete [native-dialog recipe](reference/javascript.md#a-non-bootstrap-modal).

The modal recovers focus lost during a 422 replacement and restores the opener after completed dismissal.
If the opener is removed, disabled or hidden, a usable main landmark is preferred, then an external focusable
control; the body is the last resort. Initial-show focus remains the adapter's responsibility.
