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
own statements. The maintainer updated D-04 through D-06 and D-12 on 2026-11-18.

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
participating view names its bar explicitly.

### D-04 — What an item is

An item is one of:

- a view of the owner ViewSet, by key (`NavItem(key="detail")`). More than one is allowed, for example a second
  detail view `detail2`;
- one collection per direct child ViewSet. `child` selects the ViewSet and `key` selects its list or card view.
  The default key is `list`, with the usual fallback to `card` on a card-only ViewSet.
  A custom key must match the registered collection view exactly.

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
the owner's own views and direct child collections.

For example, attach `CustomerNav` to an Item edit view under Acme Coffee. With the declaration in D-04,
the caption reads “Acme Coffee”, Orders is active, and its link opens Acme’s `open_orders` collection.
The Details and Addresses links also point to Acme. Omitting the mixin on the Item view omits the bar.

The owner itself may be nested (tenant → customer → orders, with the bar on customer). The parent gate of D-09
consults only the immediate parent, so an item can still lead to a request denied at a higher ancestor. This
is the limitation every child link in the library already has (`_immediate_parent_access` documents it); the
reference documentation states it for the bar. *(Proposed by the assistant, approved after the design review.)*

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

An item the user cannot open is hidden, not disabled. An accessible section with no records still shows. The
bar is never an authorization boundary: every destination keeps its own check, which stays authoritative. The
bar's answer for an item must agree with the destination's answer for that user and object; #363 found a real
case where the sibling-button check did not. *(Carried over from #363 D-12/D-13, approved.)*

For child items this means the bar applies the parent gate itself. The check `ChildContextButton` uses asks,
for a plain `ViewSet`, only for the child's own model permission; the request additionally runs the ancestor
guard on the parent, and only Guardian compositions add that gate to links today. The bar therefore combines
the existing child-link check with the existing bounded parent gate for rendering
(`ancestors._immediate_parent_access`). Context buttons are not changed by this issue, so on one page the bar
may hide an item that a `ChildContextButton` still shows; giving the core child-link check the same gate is a
separate, unscheduled issue (#380). *(Maintainer's choice after the design review, 2026-11-17.)*

### D-10 — Links, modals, narrow screens

Items are plain links to the existing full-page destinations. No AJAX navigation, no embedded child lists, no
unsaved-changes warning. The bar is not rendered inside modal dialogs. On narrow screens the items wrap; no
horizontally scrolling strip. *(Carried over from #363 D-07/D-09/D-11, approved.)*

### D-11 — Labels, icons, identity, empty bar

- A child item takes the child ViewSet's plural name and header icon. An owner item takes that view's short
  action label. Both can be set per item (`label=`, `icon=`).
- The identity row shows `str(object)` and the owner ViewSet's header icon and links to the first item.
  Anything richer (the draft's avatar) is a project override of the identity partial.
- If no item is accessible, nothing renders, identity included.

*(Proposed by the assistant, approved.)*

### D-12 — Active item

On a descendant page, highlight the item for the owner's direct child on the path to the page.
Orders stays active and clickable on Order and Item pages, including when its link opens a custom list.
If that section has no visible item, the bar has no active item.

On a view of the owner ViewSet, the item with that view's key is active. An owner view that
carries the bar but is not an item (for example `update`) shows the bar with no item active. An owner view
without an object (list, create) cannot carry the bar; a startup check reports it.
*(Proposed by the assistant, approved.)*

### D-13 — Built as an opt-in mixin

Alternative 1 above. The feature must be traceable in one module, must not change `base.py`'s behaviour for
views without the mixin, and must add no queries to pages without a bar. The project-wide maintainability rule
in `CLAUDE.md` applies: if planning finds the design growing beyond what the maintainer can explain and own,
narrow the scope and say so rather than adding machinery.

### D-14 — Not in this issue

Record counts or badges on items; dropdowns, groups or nested items; the global application menu explored in
`superpowers/notes/2026-11-02-navigation-concept-exploration.md` (a separate, unscheduled subject whose
decisions this issue neither adopts nor changes); adopting the feature in tabler-test (a downstream follow-up
once this ships); any change to context buttons, ancestor authorization or URL building. Aligning the core
child-link check of context buttons with the request gate is recorded as an unscheduled finding in #380.

## Proposed defaults and bounded implementation contract

Not discussed with the maintainer. The planner may change these with a stated reason; anything that would
alter a D-decision goes back to the maintainer.

### A-01 — Public names and shape

- New module `crud_views/lib/navbar.py` holding `NavBar`, `NavItem`, `CrudViewNavBarMixin` and the checks.
- `NavBar(viewset: str, items: list[NavItem], template: str | None = None)`.
- `NavItem(key: str | None = None, child: str | None = None, label=None, icon=None)`. An owner item
  requires a key. A child item uses the collection key and default described in D-04.
- Pydantic models, as `ContextButton` and `BreadcrumbItem` are. Names are strings so a bar can be declared
  before the child ViewSets exist.
- `CrudViewNavBarMixin.cv_navbar: NavBar | None = None`. A mixin with `None` is a no-op, so a project base
  mixin can be shared by views with and without a bar.

### A-02 — Resolution and template context

- The mixin adds `cv_navbar` to the template context from `get_context_data`, as the breadcrumb mixin adds
  `cv_breadcrumb`. Resolve lazily and at most once per request, so a page that never renders the tag, and a
  modal partial (`cv_is_modal_request`), pay nothing.
- Resolve the owner as in D-05. On a direct child, `cv_get_parent_object()` reuses the parent the guard
  resolved. On deeper pages use the named owner's entry in the request's resolved ancestry where available.
  Measure the query cost on both Order and Item pages.
- Resolved shape handed to the templates: the object, its label, icon and URL, and a list of items each with
  label, icon, URL and an `active` flag. Templates receive data, not view classes.
- URLs: the existing helpers are bound to the rendering view's own ViewSet (`cv_get_router_and_args`) or only
  work from a parent page (`cv_get_child_url` raises `ParentViewSetError` from a child page). The bar is
  rendered at multiple depths, so it reverses the router names itself from the owner object's pk, as
  `ParentContextButton` and `SiblingContextButton` do (`buttons.py`). The same item must produce the same URL
  from owner, child and grandchild pages. Test with distinct Customer, Order and Item PKs.

### A-03 — Access calls

- Owner item: `target_view_class.cv_has_access(user, object)`.
- Child item (D-09): `child_view_class._cv_child_link_has_access(user, object)`, the call `ChildContextButton`
  makes, **and** `_immediate_parent_access(child_view_class, user, object, rendering_view=view)` from
  `crud_views/lib/ancestors.py`. For Guardian compositions the first call already includes the second
  (`crud_views_guardian/lib/mixins.py`); the planner decides whether to skip the repeat or accept it, and
  counts the queries either way.
- `_immediate_parent_access` raises `ImproperlyConfigured` for the misconfigurations its docstring lists. On a
  page with a bar that surfaces while rendering; document it, as the Guardian child-link documentation does.
- No new permission rules: both calls exist and are used for rendering today. Pin the #363 case with a test on
  a plain `ViewSet` child: a user with `change` on the owner and `view` on the child model but without `view`
  on the owner sees no item for the child list, which answers 403. For every item shown in the test matrix
  with a top-level owner, the destination answers 200.
- With a nested owner, URL arguments above the owner come from the rendering view's URL kwargs, as
  `SiblingContextButton` takes them.
- `cv_action_enabled` (the state gate context buttons also consult) is not consulted for nav items in this
  proposal; see the open review points.

### A-04 — Startup checks

Report, with the existing check infrastructure and ids allocated by the planner:

- an unknown owner, unknown child or child outside the owner's direct children;
- a key that fails to resolve on its target ViewSet, an owner target without an object, or a child target
  that is not a collection view;
- repeated owner keys or repeated child ViewSets, including different collection keys for the same child;
- attachment to an owner page without an object or a ViewSet outside the owner's descendant tree.

`cv_navbar` set on a view without the mixin needs its own report. The unknown-attribute warning
(`viewset.W280`) does not cover it: W280 accepts a name once any registered view's MRO declares it
(`lib/check.py`, `_registry_vocabulary`), so as soon as one view uses the mixin, a second view that sets
`cv_navbar` without it gets no warning and silently shows no bar. Because that view does not have the mixin,
the check cannot come from the mixin's `checks()`. Add one registry-wide Django system check, owned by the
navbar module and registered alongside the existing ones in `crud_views/checks.py`, that reports any
registered view with a non-`None` `cv_navbar` that is not a `CrudViewNavBarMixin` subclass. `base.py` stays
untouched. *(Assistant's call after the design review.)*

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
- A working demonstration in `examples/bootstrap5` (extend `nested` or add a small app; planner's choice)
  with an owner, at least two child ViewSets and a second owner detail view, reachable from the example index
  and covered by the example tests.
- Tests in `tests/test1/`: resolution on owner, child and grandchild views, active section, hidden items per
  permission (model permissions and Guardian), empty bar, modal request, checks, query counts, template
  override and `NavBar(template=...)`.
- `CHANGELOG.md` feature entry; not a breaking change. Update the packaged skill/reference documentation and
  `docs/development/stability.md` in the tier the planner and maintainer agree on (see open review points).

### A-07 — Cost

Pages without the mixin: nothing. Pages with a bar: one access check per item per render, using checks the
links already use; Guardian checks may query. State the measured query counts in the reference documentation.
No cross-request caching.

## Acceptance criteria

1. A project declares one `NavBar`, attaches it through a mixin to the owner's detail view and to
   selected descendant views, places `{% cv_navbar %}` in its base template, and gets the identity row and items on
   every participating page with no further project code.
2. The active item follows D-12 on list, detail, create, update and custom views of a child ViewSet, on each
   owner item view, and on an owner view that is not an item. On an Item edit page under an Order, verify
   the Customer caption and the same section links as on Customer detail for a user with access to them.
   Orders is active and opens the configured Order collection even when the intermediate view omits the mixin.
3. Every link keeps the same owner object. Items the user cannot open are absent; for every item shown under a
   top-level owner, the destination answers 200 for that user, for plain and Guardian child ViewSets. The #363
   case is pinned on a plain child ViewSet. A bar with no accessible item renders nothing. The
   immediate-parent limitation for nested owners is documented.
4. The bar does not appear in modal responses.
5. Views without the mixin render byte-for-byte as before and run no additional queries; `base.py` behaviour is
   unchanged. Context buttons behave as before, alone and alongside a bar.
6. Misconfigurations listed in A-04 are reported at startup with messages that name the bar, the item and the
   view.
7. A project can override the look globally, place identity and items separately, and give one bar its own
   template, each demonstrated by a test or the example.
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
2. **`cv_action_enabled`.** Context buttons distinguish "no permission" from "not applicable to this object
   now". A-03 ignores the second for nav items, because collection destinations are always applicable and an
   owner detail view rarely is not. Confirm, or decide that a not-applicable owner item is hidden.
3. **Access calls.** The plain-ViewSet case was reproduced once on the phase 06.38 branch (`70071301`) with a
   throwaway test in `tests/test1`: a user with `view` on Book and `change` but not `view` on Publisher got
   `_cv_child_link_has_access` True, `_immediate_parent_access` False, and 403 from the Book list. The Guardian
   path after #312 was read, not run; the planner verifies it before building on it.
4. **Owner lookup.** Verify how the #336 guard exposes the resolved owner on a grandchild request before
   choosing the implementation for D-05.

## Weaknesses

These proposals are open for maintainer review. D-04 through D-06 and D-12 record the approved rules for
collection keys, descendant pages and the active section.

1. **A visible link can still lead to a 403.** A-03 checks permission but omits `cv_action_enabled`.
   A permission-required destination can deny a GET when that hook returns false. Custom views can also
   restrict their querysets. Describe which built-in checks the navbar honors and hide a destination when
   its state check denies access. Test a state-disabled detail page and an accessible empty collection.
   Limit the promise of a successful GET to the supported cases covered by those tests.
   [Existing state-gate tests](../../tests/test1/test_action_enabled.py)

2. **The parent permission can be checked twice.** Some Guardian collection views already check the
   immediate parent inside `_cv_child_link_has_access`. A-03 adds the same check again, while a plain
   child still needs it. Trace both paths with the same example: someone who may change Customer and view
   Order but lacks the required Customer view permission must see no Orders link. Measure the cost on an
   allowed link too. If a shared fix belongs in #380, review it there before adding a second permission path.
   [Guardian child-link tests](../../tests/test1/test_guardian_child_link_visibility.py)

3. **An object key can name a POST-only action.** A-04 accepts an owner target with `cv_object=True`,
   which also describes `ActionView`. Following its link sends a GET. Narrow owner destinations to detail
   pages, including custom detail keys such as Financials, and report an invalid target at startup. Child
   destinations already have a clear boundary in D-04: a list or card view selected by its collection key.
   [ActionView](../../src/crud_views/lib/views/action.py)

4. **A deep page and a nested owner pose different problems.** On Customer → Order → Item, looking up only
   the immediate parent gives the caption for Order. Use the request’s resolved Customer and test with
   distinct PKs for all three objects. A Customer bar under Tenant adds a separate concern: a link can pass
   the immediate-parent check and still be denied at Tenant. The earlier proposal to start with top-level
   owners would simplify this case and still allow Item pages. Adopting it would require revisiting D-06.

5. **The breadcrumb precedent builds data eagerly.** Its `get_context_data()` calls the builder even when
   the template omits the tag. Give the navbar one lazy accessor shared by the tag and both partials.
   Verify that omitting the bar skips its permission work and that rendering both partials builds it once.
   [Breadcrumb mixin](../../src/crud_views/lib/breadcrumb.py)

6. **A missing mixin introduces a package-wide check.** A-04 scans every registered view to find a
   `cv_navbar` declaration without the mixin. Keep target and relationship checks on participating views.
   Document the attachment example and defer the global scan until a downstream project encounters this mistake.

7. **The caption's destination depends on item order and visibility.** Under D-11, “Acme Coffee” could
   open Orders when Details is hidden. Make the caption plain text by default and let the section links
   handle navigation. This would revise D-11 and still allow an app to link the caption in its identity partial.
