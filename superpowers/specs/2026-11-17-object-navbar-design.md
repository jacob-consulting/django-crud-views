# Object navbar: opt-in section navigation for an object and its child ViewSets

**Date:** 2026-11-17
**Status:** approved discussion decisions, with separately identified implementation proposals for GSD planning.
This document is not approval to implement those proposals.
**Deliverable:** a GitHub enhancement issue containing this design and its `gsd-handover`. No implementation,
phase creation, worktree creation or roadmap scheduling is authorized by filing the issue.
**Baseline inspected:** `8cc4c05a` on `main` (phase 06.38, bulk actions, is in flight on its own branch and is
not part of this baseline).

## Problem / motivation

An object often owns several collections: a Customer has Orders, Contacts and Addresses. Today the only way to
move between the object and those collections is context buttons (`ChildContextButton` on the parent page,
`SiblingContextButton` and `ParentContextButton` on the child pages). Buttons are actions; using them as
navigation means the links sit among Update and Delete, differ from page to page, and never show where the
user currently is.

The remaining half of tabler-test finding 23 ("no page tabs for children") asked for this. Issue #363
(phase 06.33) evaluated it as a downstream experiment on the tabler-test branch
`experiment/customer-section-navigation-06-33`. The look went in the right direction. The implementation did
not: a hand-written table of thirteen URL names mapped to section titles, a template tag importing four view
classes, a project permission helper and two ad-hoc theme blocks. Nothing in it suggests how a project would
configure such a bar through django-crud-views. #363 ended with "keep downstream"; the maintainer has since
clarified that this verdict was about the draft ("I just did not like the result from the tabler-test draft"),
not about the idea. This issue designs the upstream contract and supersedes #363's outcome on that point.

## Proposed solution

Add a small, declared navbar that belongs to one object and links to that object's own views and its child
ViewSets. The developer declares a `NavBar` once and attaches it to every view that should show it:

```python
customer_navbar = NavBar(
    viewset="customer",
    items=[
        NavItem(key="detail"),        # a view of the customer itself
        NavItem(child="order"),       # child ViewSets, by name
        NavItem(child="contact"),
        NavItem(child="address"),
    ],
)


class CustomerNav(CrudViewNavBarMixin):   # one small project mixin per bar
    cv_navbar = customer_navbar


class CustomerDetailView(CustomerNav, ...): ...
class OrderListView(CustomerNav, ...): ...
class OrderUpdateView(CustomerNav, ...): ...
class OrderItemUpdateView(CustomerNav, ...): ...
```

On each of those pages the bar shows which object the user is in and marks the current section:

```
 (icon) Acme Coffee                           <- identity row
 [Details] [Orders*] [Contacts] [Addresses]   <- items, current one marked
 Orders                           [Create]    <- the view's own header and actions, unchanged
```

The feature is opt-in and self-contained: a new module, a mixin, a template tag and three templates. Views
without the mixin run today's code unchanged.

## Alternatives considered

1. **Opt-in mixin, as `CrudViewBreadcrumbMixin` does — selected.** Everything lives in one new module;
   `base.py` is not touched; a project that never imports the mixin is unaffected. Same shape as an existing
   feature the maintainer owns and downstream already uses. Cost: one more base class per participating view,
   and base-class order matters. Moving the attribute into the base later is an easy, non-breaking step; the
   reverse is not.
2. **`cv_navbar` attribute on every `CrudView` — not selected.** Least to write per view and no MRO question,
   but it adds an attribute, checks and a context entry to the core view path for every project, including
   those that never use a bar.
3. **Declared on the ViewSet side — dropped.** A NavBar that lists its views, or `ViewSet(navbar=...)` applying
   to all views, contradicts the per-view attachment the maintainer asked for and removes the explicit choice
   of which pages carry the bar. A variant that derives items from `ChildContextButton` / `SiblingContextButton`
   was dropped for the reason #363 recorded: the sibling check (`cv_has_access(user, None)`) showed a link to a
   destination that answered 403.

Presentation alternatives were compared in a mockup: (A) the bar itself carries the object label at its left
end, (B) an identity row above the bar, (C) items only, the breadcrumb names the object. B was selected (D-07).

## gsd-handover

Carry the approved decisions below into planning without reopening them absent a concrete conflict. Keep the
proposals in the following section distinct from decisions made by the maintainer. The prose and acceptance
criteria are part of the handover, not just this decision index. Decisions marked *(proposed by the assistant,
approved)* were put to the maintainer as proposals and approved on 2026-11-17; the others are the maintainer's
own statements. The maintainer updated D-04 through D-06, D-09 and D-12, and approved the dedicated
example in D-15, on 2026-11-18.

### D-01 — Purpose, and what this supersedes

Design an upstream configuration contract for object-context navigation. #363's "keep downstream, no upstream
navigation API" outcome is superseded: it judged the tabler-test draft, which is visually acceptable but "a
plain hack" with no contract. #363 and its branch remain useful as visual reference and as evidence (see
D-09 and the acceptance criteria); none of its code is to be ported.

### D-02 — An additional choice, not a replacement

The navbar is "another choice for building apps". It does not replace context buttons. `ChildContextButton`,
`SiblingContextButton` and `ParentContextButton` keep their behaviour, are not deprecated, and may be used on
the same page as a navbar. Whether a page drops its child buttons once it has a bar is the project's decision.

### D-03 — Declaration and attachment

A bar is a declared `NavBar` instance. A view gets it through a class attribute, `cv_navbar = customer_navbar`,
which "follows the attachment of views to viewsets" (`cv_viewset = ...`). Attachment is per view: each
participating view chooses its bar. In the example above, `CustomerNav` pairs the declaration with
`CrudViewNavBarMixin`. Each view that should display the Customer bar inherits `CustomerNav`.

### D-04 — What an item is

Every item selects a registered view that accepts GET. The destination determines how the URL uses the owner's PK.

- An owner item selects an object view (`cv_object=True`) by its key on the owner ViewSet.
  The owner's PK identifies the object to open. A bar may include several such items, for example
  `NavItem(key="detail")`, a second detail view with key `detail2`, and `NavItem(key="update")`.
- A bar may include one item per direct child ViewSet. Its destination needs no child object
  (`cv_object=False`). The link uses the owner's PK as the parent PK.
  For example, `NavItem(child="order", key="create")` opens the new order form for this Customer.
  A custom no-object page such as an order summary works by the same rule. An explicit key selects that
  exact view. Omitting the key selects `list`, falling back to `card` if `list` is unregistered.

```python
items=[
    NavItem(key="detail"),      # Details
    NavItem(key="detail2"),     # e.g. Financials: a second detail view of the customer
    NavItem(child="order", key="open_orders"),  # Orders opens this collection
    NavItem(child="contact"),
    NavItem(child="address"),
]
```

Both owner items are object views of the customer, resolve the same object and link to their own URL with the
same pk.

*(Shape proposed by the assistant, approved; the `detail2` case is the maintainer's.)*

### D-05 — How the bar knows its object

The declaration names the owner ViewSet. On an owner page the caption comes from `str(self.object)`.
On a descendant page, follow the declared parent ViewSets to the owner and use that ancestor object from
the current request. On an Item edit page the chain is Item → Order → Customer. The Customer supplies
the caption and the owner PK for the links. An item's key selects its destination.

### D-06 — Where the bar can appear

Attach the shared mixin to each owner object view or descendant view that should display the bar. An
intermediate view can omit the mixin. Each participating view displays one bar. Its items target
the owner's own views and pages on its direct child ViewSets as described in D-04.

For example, attach `CustomerNav` to an Item edit view under Acme Coffee. With the declaration in D-04,
the caption reads “Acme Coffee”, Orders is active, and its link opens Acme’s `open_orders` collection.
The Details and Addresses links also point to Acme. Omitting the mixin on the Item view omits the bar.

The owner itself may be nested. On a Customer page under Tenant XYZ, the current view has already enforced
its configured ancestor permissions. The navbar carries XYZ's PK into its links. For an Orders item, the
child-link hook checks access to the destination and its immediate parent, Customer. Rendering the item
adds no permission check on Tenant. Following the link starts a new request with the destination's own
ancestor policy. If that policy requires a stronger Tenant permission, the destination can return 403.
*(Approved 2026-11-18.)*

### D-07 — Layout B: identity row above the items

The default presentation is an identity row naming the object, the items below it, then the view's own header,
icon and actions, unchanged. The bar does not retitle or replace the view header.

### D-08 — The app controls template and location

"It is very important that when implementing this for an app the app can override the template and the
location."

- **Location:** the project's base template (`CRUD_VIEWS_EXTENDS`) places a `{% cv_navbar %}` tag where it wants
  it, as it places `{% cv_breadcrumb %}` today. The tag renders nothing on a view without a bar. No setting
  selects a location.
- **Template:** layout B ships as three templates — a wrapper that includes an identity partial and an items
  partial. A project may override any of them, include the two partials at different places in its base
  template, or give one bar its own template (`NavBar(template=...)`).
- The tag and both partials share one result per request. The first template that uses the navbar builds it.
  *(Approved 2026-11-18.)*
- **Only B ships.** No second built-in layout and no setting to choose between layouts. Layout A (label and
  items in one row) is the worked example in the documentation for overriding the template.

Placement in the project's base template:

```django
{% block cv_navbar %}{% cv_navbar %}{% endblock %}   {# wherever the app's base template wants it #}
```

The shipped templates:

```
tags/navbar.html            includes the two below: the default, layout B
tags/navbar_identity.html   icon + object label
tags/navbar_items.html      the items, active one marked
```

| The app wants                               | It does                                                        |
|---------------------------------------------|----------------------------------------------------------------|
| a different look everywhere                 | overrides the templates in the project                         |
| identity and items in different places      | includes the two partials itself in its base template          |
| one bar that looks different from the others | `NavBar(viewset="order", items=[...], template="myapp/order_navbar.html")` |

*(Mechanism proposed by the assistant, approved.)*

### D-09 — Access

Hide an item when its permission checks fail. If they pass, ask the target view whether it is enabled for
the navbar's owner object. Hide the item if the answer is false. On a Customer navbar, both Financials
(an owner view) and Orders (a child collection) receive the same Customer. An accessible Orders collection
still shows when it has zero rows. The destination enforces access on each request, including any
project-specific queryset restrictions. *(State check approved 2026-11-18.)*

For each child item, the bar calls `target._cv_child_link_has_access(user, owner)` once, as
`ChildContextButton` and child `CardAction` do. With #380, the hook checks the child's access and applies
the destination's immediate-parent policy for both plain and shipped Guardian collections. Farther ancestors
can still deny the destination request. *(Approved 2026-11-18.)*

### D-10 — Links, modals, narrow screens

Items are plain links to the existing full-page destinations. No AJAX navigation, no embedded child lists, no
unsaved-changes warning. The bar is not rendered inside modal dialogs. On narrow screens the items wrap; no
horizontally scrolling strip. *(Carried over from #363 D-07/D-09/D-11, approved.)*

### D-11 — Labels, icons, identity, empty bar

- A child item takes the child ViewSet's plural name and header icon. An owner item takes that view's short
  action label. Both can be set per item (`label=`, `icon=`).
- The default identity row shows the owner ViewSet's header icon beside `str(object)` as plain text.
  A project can override `tags/navbar_identity.html` to link the caption or add an avatar.
- If no item is accessible, nothing renders, identity included.

*(Proposed by the assistant, approved.)*

### D-12 — Active item

On a descendant page, highlight the item for the owner's direct child on the path to the page.
Orders stays active and clickable on Order and Item pages, whichever destination the item opens.
If that section has no visible item, the bar has no active item.

On a view of the owner ViewSet, the visible item with that view's key is active. For example, on the
Customer update page, Update is active if the bar includes that item. If the key is absent, no item is active.
An owner view without an object (list, create) cannot carry the bar; a startup check reports it.
*(Proposed by the assistant, approved.)*

### D-13 — Built as an opt-in mixin

Alternative 1 above. The feature must be traceable in one module, must not change `base.py`'s behaviour for
views without the mixin, and must add no queries to pages without a bar. The project-wide maintainability rule
in `CLAUDE.md` applies: if planning finds the design growing beyond what the maintainer can explain and own,
narrow the scope and say so rather than adding machinery.

Navbar-specific startup checks run on views that inherit the mixin and have a configured bar.
Defer a dedicated check for a forgotten mixin until downstream use demonstrates a need. *(Approved 2026-11-18.)*

### D-14 — Not in this issue

Record counts or badges on items; dropdowns, groups or nested items; the global application menu explored in
`superpowers/notes/2026-11-02-navigation-concept-exploration.md` (a separate, unscheduled subject whose
decisions this issue neither adopts nor changes); adopting the feature in tabler-test (a downstream follow-up
once this ships); any change to context buttons, ancestor authorization or URL building. Aligning the core
child-link check of context buttons with the immediate-parent gate is supplied by the separate #380 fix;
this navbar consumes that hook as described in D-09/A-03.

### D-15 — Dedicated navbar and authorization example

Add one self-contained app within `examples/bootstrap5`, focused on the new navbar and authorization.
It owns its models, views, navbar, seed data and tests. Do not extend an existing complex app, import models
from another example app, or require cross-links to other example apps. Shared project infrastructure such
as login, base styling and the example index is fine.

The model hierarchy is Tenant → Customer → (Order → Item, Address). Seed two tenants with business data:

| User | Tenant | Access |
|---|---|---|
| Alice | A | Full CRUD within her tenant |
| Bob | B | Full CRUD within his tenant |
| Charlie | A | Read customers, orders and items; no addresses or writes |

Alice and Bob are key account managers. Each of these three users is restricted to their assigned tenant,
including when following a copied direct URL to a descendant such as an Item. Charlie provides a restricted
comparison against Alice on the same data; no permission-management UI is needed.

Customer owns the navbar, with Details, a second Customer detail page, Orders and Addresses. The second
detail page is another view of the same Customer. On an Item page the Customer identity and links remain
stable and Orders is active. Charlie's navbar hides Addresses, and direct Address and write requests are
also denied. Seed an accessible empty Orders collection to show that an empty section remains visible.

Use Guardian object permissions on Tenant and ordinary Django model permissions on Customer, Order, Item
and Address. Tenant grants restrict entry to the assigned tenant; model grants control operations below it.
Keep ancestor cascading enabled so descendant requests enforce the Tenant gate at every depth. Alice and
Bob receive the business-model CRUD permissions; Charlie receives only the three permitted view permissions.
New business records require no individual Guardian grants. Guardian at every level was considered and
rejected because individual-record sharing is unnecessary and would add grant-management code.

This example uses the navbar access contract in D-06/D-09; it does not add higher-ancestor permission checks
to navbar rendering. The current page and destination request enforce their configured ancestor policies.

*(Approved 2026-11-18. The tenant-level Guardian approach was proposed by the assistant and approved.)*

## Proposed defaults and bounded implementation contract

Not discussed with the maintainer. The planner may change these with a stated reason; anything that would
alter a D-decision goes back to the maintainer.

### A-01 — Public names and shape

- New module `crud_views/lib/navbar.py` holding `NavBar`, `NavItem`, `CrudViewNavBarMixin` and the checks.
- `NavBar(viewset: str, items: list[NavItem], template: str | None = None)`.
- `NavItem(key: str | None = None, child: str | None = None, label=None, icon=None)`. An owner item
  requires a key. A child item uses the destination key and default described in D-04.
- Pydantic models, as `ContextButton` and `BreadcrumbItem` are. Names are strings so a bar can be declared
  before the child ViewSets exist.
- `CrudViewNavBarMixin.cv_navbar: NavBar | None = None`. A mixin with `None` is a no-op, so a project base
  mixin can be shared by views with and without a bar.

### A-02 — Resolution and template context

- For a participating full-page view, the mixin keeps one Django `SimpleLazyObject` on the view instance
  and exposes it as `cv_navbar` in the template context. Pass the navbar builder as the callable.
  The first access builds the data, and later accesses reuse it. For a modal request (`cv_is_modal_request`),
  expose `None` so even a template that includes a navbar partial skips the builder.
- On an owner page use `self.object`. On a descendant page use `_resolved_ancestor(view, owner_name)`
  from `crud_views/lib/ancestors.py`. It returns the owner object already loaded for this request.
  Verify that retrieving the Customer on Order and Item pages adds no database query.
- Templates receive the owner object, its label and its icon. Each visible item has a label, icon, URL and
  an `active` flag.
- URLs: the existing helpers are bound to the rendering view's own ViewSet (`cv_get_router_and_args`) or only
  work from a parent page (`cv_get_child_url` raises `ParentViewSetError` from a child page). The bar is
  rendered at multiple depths, so it reverses the router names itself from the owner object's pk, as
  `ParentContextButton` and `SiblingContextButton` do (`buttons.py`). The same item must produce the same URL
  from owner, child and grandchild pages. Test with distinct Customer, Order and Item PKs.

### A-03 — Access calls

- Owner item: `target_view_class.cv_has_access(user, object)`.
- For a child item, call `target_view_class._cv_child_link_has_access(user, owner)` once (D-09).
- The hook propagates `ImproperlyConfigured` for reached parent-policy misconfigurations: missing required
  permission keys, missing operation requirements or authorization records routed away from `default`.
  Document failures during bar rendering, as the child-link references do.
- With a nested owner, URL arguments above the owner come from the rendering view's URL kwargs, as
  `SiblingContextButton` takes them.
- For both item types, once permissions pass, call `target._cv_action_enabled_for_rendering(user, owner, view)`
  once with the resolved navbar owner and the rendering view. This is the helper context buttons already use (D-09).

### A-04 — Startup checks

Use the mixin's `checks()` method to validate each participating view's configured bar. Report the following
configuration errors through the existing check infrastructure.

- an unknown owner, unknown child or child outside the owner's direct children;
- a key that fails to resolve on its target ViewSet;
- a destination that cannot handle GET (the resolved class must allow `"get"` in `http_method_names`
  and have a callable `get` handler);
- an owner target with `cv_object=False` or a child target with `cv_object=True`;
- repeated owner keys or repeated child ViewSets, including different destination keys for the same child;
- attachment to an owner page without an object or a ViewSet outside the owner's descendant tree.

### A-05 — Templates and theme surface

- `tags/navbar.html` (includes the two below), `tags/navbar_identity.html`, `tags/navbar_items.html` under the
  theme path, plus the `{% cv_navbar %}` tag in `templatetags/crud_views.py`.
- Bootstrap 5 markup in core: `<nav aria-label=...>` with `nav nav-pills flex-wrap`, `active` and
  `aria-current="page"` on the current item. The `aria-label` is translatable.
- No new class keys in the first version; themes restyle by overriding the templates. If the planner finds
  that the theme conventions require class keys here, note that the button-class count is guarded in docs and
  tests and both must be updated together.
- The example project's base template places the tag in its own block, next to the breadcrumb block.

### A-06 — Documentation, example, tests, release notes

- `docs/reference/navbar.md`: declaration, attachment through a project mixin, the object rule, access rule,
  supported depth and the unsupported cases, the three override levels, and layout A as the override example.
  Reciprocal links from `nested.md`, `context_buttons.md` and the breadcrumb reference.
- Implement the dedicated example in D-15 within `examples/bootstrap5`, reachable from the example index
  and covered by example tests. Verify the Alice/Bob tenant boundary, Charlie's hidden Addresses section and
  denied direct requests/writes, both Customer detail entries, Customer navigation from Item pages, and the
  visible empty Orders collection. Creating a new app is decided; extending `nested` is no longer an option.
- Tests in `tests/test1/`: resolution on owner, child and grandchild views, active section, hidden items per
  permission (model permissions and Guardian), empty bar, modal request, checks, query counts, template
  override and `NavBar(template=...)`.
- `CHANGELOG.md` feature entry; not a breaking change. Update the packaged skill/reference documentation and
  `docs/development/stability.md` in the tier the planner and maintainer agree on (see open review points).

### A-07 — Cost

Rendering the bar runs the permission checks for each item and one state check for each item that passes.
The default state hook needs no query. Guardian checks and custom hooks may query. State the measured query
counts in the reference documentation.
No cross-request caching.

## Acceptance criteria

1. A project declares one `NavBar`, attaches it through a mixin to the owner's detail view and to
   selected descendant views, places `{% cv_navbar %}` in its base template, and gets the identity row and items on
   every participating page with no further project code. The default identity row renders the caption
   as plain text even when the first declared item is hidden.
2. The active item follows D-12 on list, detail, create, update and custom views of a child ViewSet, on each
   owner item view, and on an owner view that is not an item. On an Item edit page under an Order, verify
   the Customer caption and the same section links as on Customer detail for a user with access to them.
   Orders is active and opens the configured Order page even when the intermediate view omits the mixin.
   Verify that a configured owner Update item opens the Customer's edit form and is active there.
   Verify that explicit child keys for Create and a custom no-object page open with the Customer's PK.
   With Customer nested under Tenant, verify that both owner and child links retain the Tenant PK from the URL.
3. Every link keeps the same owner object. In one navbar integration test, render a child item with its state
   enabled. For each permission outcome, verify the destination's child-link hook receives the user and resolved
   owner once. Denial hides the item and skips the state check. When permission passes, the enabled item appears.
   A permission-required owner detail view whose state hook denies access is hidden and its
   GET returns 403. A child collection whose hook denies access for that owner is also hidden. An accessible
   empty collection is visible and its GET returns 200, for both plain and Guardian child ViewSets. A bar with
   no visible items renders nothing. Document the immediate-parent limitation for nested owners.
4. On a participating view, a template that omits the navbar makes zero navbar builder and permission calls.
   A modal response also makes zero such calls and renders no navbar.
5. Views without the mixin render byte-for-byte as before and run no additional queries; `base.py` behaviour is
   unchanged. Context buttons behave as before, alone and alongside a bar.
6. Misconfigurations listed in A-04 are reported at startup with messages that name the bar, the item and the
   view. Include a registered POST-only owner action.
7. A project can override the look globally, place identity and items separately, and give one bar its own
   template, each demonstrated by a test or the example. Rendering the identity and items partials in
   separate places on one page invokes the navbar builder exactly once.
8. Items wrap on a narrow viewport without horizontal page scroll (checked in the example app).
9. Reference documentation and a working example exist as in A-06; the full test matrix passes.

## Implementation references

- `src/crud_views/lib/breadcrumb.py` — the precedent: opt-in mixin, context entry, per-request cache, checks,
  container-key fallback, ancestor resolution.
- `src/crud_views/lib/view/buttons.py` — `ChildContextButton` (child URL and `_cv_child_link_has_access`),
  `SiblingContextButton` (the `obj=None` check the bar must not copy).
- `src/crud_views/lib/view/base.py` — `cv_has_access`, `_cv_child_link_has_access`, `cv_get_child_url`,
  `cv_get_parent_object`, `cv_get_router_and_args`, `cv_is_modal_request`.
- `src/crud_views_guardian/lib/mixins.py` — Guardian's `_cv_child_link_has_access`.
- `examples/bootstrap5/project/templates/project/crud_views.html` — where the breadcrumb tag is placed.
- `docs/reference/context_buttons.md`, `docs/reference/nested.md`.
- Issue #363 and tabler-test branch `experiment/customer-section-navigation-06-33`
  (`example/config/templatetags/acme_nav.py`, `example/templates/project/customer_navigation/`) — visual
  reference and the access finding only.
- tabler-test `docs/crud_views_upstream_findings_roastery.md`, finding 23.

## Open review points

1. **Timing.** This issue schedules nothing. The 2026-11-02 navigation decisions placed a navigation feature
   after 1.0 as a provisional surface; they concern the global application menu, not this bar. Whether the
   object navbar ships before 1.0, and in which stability tier, is the maintainer's call at scheduling time.

## Weaknesses

D-04 through D-06 and D-12 record the approved rules for destinations, descendant pages and the active section.

1. **State-disabled destinations (resolved 2026-11-18).** D-09 and A-03 reuse the destination's existing state
   check after permission passes. Acceptance criterion 3 covers a disabled detail page and an accessible empty collection.
   [Existing state-gate tests](../../tests/test1/test_action_enabled.py)

2. **Duplicate parent permission check (resolved by #380, 2026-11-18).** The navbar uses the child-link hook
   in D-09. The #380 tests cover the Publisher/Book denial, Guardian behavior and permission query costs.
   Acceptance criterion 3 covers the navbar's use of the hook.
   [Guardian child-link tests](../../tests/test1/test_guardian_child_link_visibility.py)

3. **POST-only destinations (resolved 2026-11-18).** D-04 requires every destination to accept GET.
   An owner Update view qualifies because GET opens its form for the owner. A POST-only action fails
   the startup check in A-04.
   [ActionView](../../src/crud_views/lib/views/action.py)

4. **Deep pages and nested owners (resolved 2026-11-18).** On an Item page, the Customer bar reuses the
   Customer resolved by the current request. When Customer belongs to a Tenant, links retain that Tenant's
   PK. Each destination enforces its own ancestor policy as described in D-06.

5. **Lazy navbar rendering (resolved 2026-11-18).** D-08 and A-02 specify one request-local result shared
   by the tag and both partials. Acceptance criteria 4 and 7 cover omitted bars, modals and split placement.
   [Existing use of SimpleLazyObject for template data](../../src/crud_views/lib/views/manage.py)

6. **Missing mixin (resolved 2026-11-18).** Setting `cv_navbar` alone can leave the bar absent without a
   warning. D-03 shows how to pair the declaration and mixin. D-13 limits navbar checks to participating views.

7. **Caption link (resolved 2026-11-18).** D-11 makes the caption plain text by default. Section links
   provide navigation. A project can link the caption in its identity partial.
