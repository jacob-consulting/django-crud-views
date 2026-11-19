<a id="object-navbar"></a>

# ViewSet Navigation

ViewSet Navigation connects an object's views and child ViewSets with a shared navigation bar.
It keeps the object's identity and section links visible on selected owner and descendant pages.
It is opt-in per view. The default layout puts plain identity above wrapping section links, before your existing
view header and actions. [Context buttons](context_buttons.md) remain independent and may coexist with it;
omit redundant buttons in your application only if you want to.

!!! example "Try it live"
    [Try the ViewSet Navigation example](https://django-crud-views-demo.onrender.com/object-navbar/).
    Sign in as `alice` / `alice` or `bob` / `bob` to manage separate tenants, or `charlie` / `charlie` for
    read-only Customer, Order and Item access in Alice's tenant, without Addresses or writes. All three
    credentials are listed in the ViewSet Navigation introduction and [Live demo](../getting_started/demo.md),
    which explains daily resets and wake-up time. Shared login/home notices are not a list of this scenario's accounts.

## Declare once, attach per view

Public imports and keyword-only declaration fields:

```python
from django.utils.translation import gettext_lazy as _
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem

customer_navbar = NavBar(
    viewset="customer",
    items=[
        NavItem(key="detail", label=_("Details")),
        NavItem(key="notes", label=_("Notes"), icon=""),
        NavItem(child="order"),
        NavItem(child="address"),
    ],
)


class CustomerNavbarMixin(CrudViewNavBarMixin):
    cv_navbar = customer_navbar
```

`NavBar(viewset: str, items: list[NavItem], template: str | None = None)` names the owner ViewSet.
`NavItem(key: str | None = None, child: str | None = None, label: str | Promise | None = None,
icon: str | None = None)` selects one destination. `Promise` means Django lazy translation values such as
`gettext_lazy`. Both declarations are Pydantic models: pass fields by keyword. `items=[]` is valid and renders nothing.
Names are late-bound strings, so the declaration may precede ViewSet and view registration.

Given your registered `cv_customer`, `cv_order`, and `cv_item` ViewSets (with parent relationships
Customer → Order → Item), attach the project mixin **before** the concrete view base:

```python
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired


class CustomerDetail(CustomerNavbarMixin, DetailViewPermissionRequired):
    cv_viewset = cv_customer


class CustomerNotes(CustomerNavbarMixin, DetailViewPermissionRequired):
    cv_viewset = cv_customer
    cv_key = "notes"
    cv_path = "notes"


class OrderList(CustomerNavbarMixin, ListViewPermissionRequired):
    cv_viewset = cv_order


class ItemDetail(CustomerNavbarMixin, DetailViewPermissionRequired):
    cv_viewset = cv_item
```

Configure the page templates/forms/tables as usual; the mixin only supplies navigation. See
[nested ViewSets](nested.md) for parent declarations, and the live example's source panel for a complete app.
Intermediate views need not carry the mixin. One participating view has one bar; a mixin with `cv_navbar=None`
is a no-op. Setting `cv_navbar` without the mixin does not attach a bar and is not currently diagnosed.

On the owner ViewSet, attachment requires `cv_object=True`: ordinary detail/update/delete pages qualify,
ordinary list/create pages do not. This is a capability rule, not a view-key allowlist. Descendant views may
be collection or object pages. On an owner page the identity is that page's object; on a descendant page it is
the already-resolved owner ancestor, even several levels up. Identity and every link use that same owner.
A nested owner retains higher ancestor URL coordinates (for example Tenant → Customer → Order → Item).

## Exact destinations and active sections

Every item must select a registered view with a callable `get` and `"get"` in `http_method_names`.
An owner item names an object view by `key`; a child item names a **direct** child ViewSet and a view that
does not require a child object. At most one item may name each child, and owner keys cannot repeat.

```python
alternative_navbar = NavBar(
    viewset="customer",
    items=[
        NavItem(key="detail"),
        NavItem(key="notes", label=_("Notes")),  # second registered detail view
        NavItem(key="update", label=_("Edit customer")),
        NavItem(child="order", key="create", label=_("New order")),
        NavItem(child="address", key="directory", label=_("Address directory")),
    ],
)
```

Here `update`, Order `create` and the custom Address `directory` must be registered separately; `directory`
must handle GET with `cv_object=False`. The navbar does not create routes or infer form configuration.
Omitting a child key selects `list`, falling back to `card` **only when list is unregistered**. An explicit
key selects exactly that destination. A denied list never falls back to card, and an explicit missing list is an error.

On owner pages the visible item whose key equals the current view key is active. On any descendant page the
visible item for the owner's direct child along the ancestry path is active: an Item page highlights Orders.
The active link remains clickable and carries `aria-current="true"`. If the matching item is missing or hidden,
no item is active. These are normal full-page links, without AJAX, embedded lists, tab roles or unsaved-change warnings.

## Labels, access and empty output

Owner items default to the destination's short action label and action icon. Child items default to their
ViewSet's plural display name and header icon, including explicit Create/custom collection destinations.
`label=` and `icon=` override these defaults; `icon=""` intentionally suppresses an icon. Labels stay visible.
Identity is the owner's header icon and `str(owner)` as plain text, never a link derived from the first item.

The rendered default short-action label is entity-decoded **once** into plain text. Raw captions and explicit
labels retain literal entity sequences: an explicit `"A &amp; B"` displays those characters literally.
Markup, including values marked safe, displays as text. Keep template autoescaping enabled; do not apply `safe`.
Private normalization helpers are not public API.

For each owner item, destination access is checked with the owner object. For each child item, the existing
child-link admission helper is called once with that same owner. Only after admission does the destination's
existing state check run, again with the navbar owner (not a child row). Denied or state-disabled items are
hidden, even if ordinary action buttons would be disabled. Accessible empty collections remain visible: there
are no row counts, badges, existence probes or row-count-based hiding.

!!! warning "Visibility is not destination authorization"
    Child admission checks the destination and its immediate-parent policy. The navbar adds no farther-ancestor
    gate. A visible link can still return 403 under the destination's full ancestor policy, or 404 under a project
    queryset restriction. Requests remain authoritative for permissions, tenants and writes. The live example
    enables ancestor cascading and uses strict Guardian Tenant object grants, plus model permissions below Tenant.

Reached configuration errors propagate; invalid policy or URL configuration is not silently treated as denial.
If no items survive, the entire bar, including identity and spacing, is absent. Modals omit the bar. Context
creation is lazy: omitting all three tags **and** both partials performs zero navbar construction or admission work.
Repeated template/context access on the same view/request shares one result; declarations do not cache users.
Pages without participation add no navbar work or queries.

## Placement and overrides

In your base template, load the library and place the tag before the existing view header/card:

<!-- navbar-recipe: tag -->
```django
{% load crud_views %}{% cv_navbar %}
```

For independent placement, use either no-argument component tag from the same library:

<!-- navbar-recipe: identity-tag -->
```django
{% load crud_views %}{% cv_navbar_identity %}
```

<!-- navbar-recipe: items-tag -->
```django
{% load crud_views %}{% cv_navbar_items %}
```

`cv_navbar` renders the full wrapper. `cv_navbar_identity` renders only identity, and `cv_navbar_items`
renders only the section links. All three reuse the same named lazy `cv_navbar` value and preserve the
full caller context and request. Components can appear alone or in either order.

The default wrapper composes the two component tags, identity first. Its public leaves remain:


| Path | Responsibility |
|---|---|
| `crud_views/tags/navbar.html` | Layout B: identity above items |
| `crud_views/tags/navbar_identity.html` | Plain owner identity |
| `crud_views/tags/navbar_items.html` | Translated navigation landmark and visible links |

All three independently guard `cv_navbar` and emit exactly nothing when it is empty. The items leaf owns its
landmark label (`Sections for %(object)s`), so it does not rely on a neighbouring identity element or ID.
Use the documented [navbar context](templates.md#viewset-navigation-context); templates consume resolved items,
without permission calls. Keep normal link focus, active markers, translated landmark naming and text wrapping.

### Global wrapper

Place this in your project/theme's `templates/crud_views/tags/navbar.html`, resolved before the shipped template.
This is layout A as an **application wrapper override**, arranging identity and items on one wrapping row;
the package ships only layout B and has no layout/location setting:

<!-- navbar-recipe: wrapper -->
```django
{% if cv_navbar %}{% load crud_views %}<div class="d-flex flex-wrap gap-2 mb-3">
  {% cv_navbar_identity %}
  {% cv_navbar_items %}
</div>{% endif %}
```

### Individual leaf

Override just `templates/crud_views/tags/navbar_identity.html`; the default items leaf still renders:

<!-- navbar-recipe: identity -->
```django
{% if cv_navbar %}{% load crud_views %}<p class="fw-medium text-break">
  {% if cv_navbar.icon %}{% cv_icon cv_navbar.icon %} {% endif %}{{ cv_navbar.label }}
</p>{% endif %}
```

The items leaf is independently replaceable at its listed path using `cv_navbar.items` with `item.label`,
`item.icon`, `item.url` and `item.active`. Preserve a named `<nav>`, ordinary anchors, escaping and wrapping.

### Split placement

Place the component tags at separate locations in your base using the same context:

<!-- navbar-recipe: split -->
```django
{% load crud_views %}{% cv_navbar_identity %}
<main>{% block cv_content %}{% endblock %}</main>
{% cv_navbar_items %}
```

Do not also place `cv_navbar`, which would duplicate the UI. Both components share the lazy result.
To put items first, swap the two component calls. Keep `cv_content` so child templates retain their page body.

Split includes already worked and remain supported. The component tags add a convenient placement API;
existing layouts need no migration. This equivalent recipe uses the unchanged public leaf paths:

<!-- navbar-recipe: split-includes -->
```django
{% include "crud_views/tags/navbar_identity.html" %}
<main>{% block cv_content %}{% endblock %}</main>
{% include "crud_views/tags/navbar_items.html" %}
```

### Owner as page heading

A theme may use the owner identity as the page heading, followed by section links and a subordinate
view header. The stock layout keeps its plain identity and ordinary view header unchanged. This complete
base fragment preserves the existing extension blocks; integrate it into your theme's own header rather
than treating its surrounding HTML as a new shared block API:

<!-- navbar-recipe: owner-heading -->
```django
{% load crud_views %}
{% block cv_breadcrumb %}{% cv_breadcrumb %}{% endblock %}
{% if cv_navbar %}
  <h1 class="d-flex flex-wrap align-items-center gap-2 text-break">
    {% if cv_navbar.icon %}{% cv_icon cv_navbar.icon %}{% endif %}
    {{ cv_navbar.label }}
  </h1>
  {% cv_navbar_items %}
{% endif %}
<header class="mb-3">
  {% cv_heading_icon view.cv_get_header_icon location="page" as title_icon %}
  {% if cv_navbar %}<h2 class="text-break {{ title_icon.host_class }}">{% else %}<h1 class="text-break {{ title_icon.host_class }}">{% endif %}
    {{ title_icon.inline_html }}
    {% block cv_header %}{% cv_header %}{% endblock %}
  {% if cv_navbar %}</h2>{% else %}</h1>{% endif %}
  {% block cv_context %}{% cv_context_actions object %}{% endblock %}
  {% block cv_paragraph %}{% cv_paragraph %}{% endblock %}
</header>
<main>
  {% block cv_filter %}{% endblock %}
  {% block cv_content %}{% endblock %}
</main>
```

The owner is `h1` and the view is `h2`; without navigation, the view becomes `h1`. Equal owner and view
titles are intentionally retained. Missing, unconfigured, fully hidden and modal navigation all leave the
ordinary header, actions, filters and content available. The breadcrumb appears once, outside the guard.
Keep autoescaping enabled for `cv_navbar.label`; icons use the registered renderer and links use the
resolved items component. Actions are independent of navbar visibility and stay below the section links.

This conditional hierarchy uses explicit theme-owned markup. `CRUD_VIEWS_HEADER_LEVEL` controls existing
package header/content heading helpers globally; it does not inspect `cv_navbar`. A theme must coordinate
its content-heading policy with this layout, including absent-navbar and modal fallbacks. Do not mutate the
setting per render, or assume a literal `cv_heading "header" level=...` overrides a configured header level.

Retain wrapping, complete long labels and visible keyboard focus at narrow widths; test the surrounding
theme header and action layout at those widths. The [class-registration recipe](theme.md#navbar-class-registration)
can select tabs and link spacing without copying the items template. Wrapper and identity class keys apply
only when those stock leaves are used: this fragment owns their replacement markup. Do not also render
the full navbar or identity component here, which would duplicate the owner.

### Per-bar wrapper

Set `template="myapp/customer_navbar.html"` on `NavBar`. This selects only `cv_navbar`'s full wrapper for
that declaration. Component tags always select their corresponding theme leaves with normal loader precedence,
even from a custom wrapper; they ignore the per-bar wrapper choice. Direct includes keep the paths you chose.
Create that template with the same context contract:

<!-- navbar-recipe: per-bar -->
```django
{% if cv_navbar %}{% load crud_views %}<aside class="mb-3">
  {% cv_navbar_identity %}
  {% cv_navbar_items %}
</aside>{% endif %}
```

All override paths use the normal [theme loader order](theme.md#how-resolution-works). For class-only changes,
use the [six navbar keys](buttons.md#the-class-table) and [registration recipe](theme.md#navbar-class-registration);
use template overrides for structural changes. Include the normal [assets](assets.md) for the stock wrapping styles.

## Validation and supported scope

Pydantic validates declaration field types at construction. Cooperative Django startup checks on participating,
configured views validate destinations after URL configuration is loaded. Diagnostics name the attachment,
owner and offending item: `viewset.E280` for malformed declarations/names, `E281` for invalid attachment,
`E282` for unknown/unusable destinations, `E283` for duplicate owner keys/children, and `E284` for a missing
custom wrapper. This includes POST-only targets, explicit missing keys, non-direct children and owner collection
attachments. An empty items list is intentionally valid. Preserve `super().checks()` in custom mixins.

There are no groups, dropdowns, nested items, global application menu or downstream theme adoption in this API.
It does not change context buttons, ancestor policy or existing URL construction. Custom route extras still
use the destination's existing URL-kwargs hook; arbitrary dynamic route captures are not inferred.
Declarations, attachment, all three tags, three templates and documented context are [stable at 1.0](../development/stability.md).
Builders, resolvers and check carriers remain internal.

## Measured costs

Measured on Python 3.12.3 / Django 5.2.19 / django-guardian 3.5.2 with SQLite in-memory databases. These are
**navbar-only SQL counts after request/object/ancestor loading**, with two visible items (one owner and one child),
at owner and grandchild depth and for tag, split and repeated placements. They are fixture measurements, not a
whole-page budget or a universal zero-query promise. The regression is `tests/test1/test_navbar_costs.py`.

| Composition | Vocabulary | Actor model cache | Total SQL | Permission SELECTs | ContentType SELECTs |
|---|---|---|---:|---:|---:|
| plain | cold | cold | 6 | 4 | 2 |
| plain | cold | warm | 4 | 2 | 2 |
| plain | warm | cold | 2 | 2 | 0 |
| plain | warm | warm | 0 | 0 | 0 |
| guardian | cold | cold | 8 | 6 | 2 |
| guardian | cold | warm | 8 | 6 | 2 |
| guardian | warm | cold | 4 | 4 | 0 |
| guardian | warm | warm | 4 | 4 | 0 |
| mixed | cold | cold | 10 | 8 | 2 |
| mixed | cold | warm | 8 | 6 | 2 |
| mixed | warm | cold | 6 | 6 | 0 |
| mixed | warm | warm | 4 | 4 | 0 |

Cold vocabulary resets ViewSet permission caches, the shared check vocabulary, Django ContentTypes **and**
Guardian's separate content-type cache. Warm vocabulary resolves those outside measurement, without admission
or state calls. Cold actor clears Django's model-permission caches on the actual user; warm actor calls
`get_all_permissions()` before measurement. Guardian admission creates fresh checkers: warm actor does **not**
mean warm Guardian object permissions. Plain means core owner/child; guardian means Guardian owner/child;
mixed means Guardian owner with core child. Custom permission backends or state hooks may cost more.

All 72 measured combinations built once, called owner access once and child admission once, and ran one state
check per admitted item. They read no Publisher/Book/BookNote rows and performed no collection probes or
actor/session reads. Repeated access added no hooks or SQL. See also [child-link costs](context_buttons.md)
and [ancestor authorization](nested.md#ancestor-authorization); [breadcrumbs](breadcrumb.md) have their own work.

The component-tag follow-up separately exercises 48 additional combinations: component pairs and reversed,
mixed/repeated component, wrapper and direct-include consumers across the same depth/cache/composition axes.
These checks retain the SQL totals above, one build and once-only per-item hooks. The historical 72-combination
receipt describes the original placements; it is not relabeled as component-tag evidence.
