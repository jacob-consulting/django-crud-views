# Design: a structured manage page for django-crud-views

**Date:** 2026-11-14
**Status:** approved by the maintainer. Upstream issue:
[django-crud-views#366](https://github.com/jacob-consulting/django-crud-views/issues/366).
**Mockup:** [`2026-11-14-manage-page-mockup.html`](2026-11-14-manage-page-mockup.html), next to this file
(self-contained apart from Tabler 1.6.1 CSS from jsDelivr; open it in a browser).
**Origin:** written in the tabler-test demo project, where it is finding 35 in
`docs/crud_views_upstream_findings_roastery.md`; "the demo" below is that project.
**Code references:** commit `4510cee9`, paths relative to `src/`.
**Decision numbers:** D-01 to D-30. They match the numbers used in #366 and its comments, so they are not
renumbered and are grouped by topic, not in numeric order.

## How to read the mockup

- It is modelled on the demo's `/customer/manage/` page (a Guardian ViewSet with 6 views) in the Tabler theme. The
  upstream implementation uses stock Bootstrap 5 markup, and themes recolour it through class-registry keys (D-15).
  Tabler's soft badges (`bg-*-lt`) are therefore a theme choice, not part of the upstream design.
- The views (`list`, `detail`, …) and the Presentation card expand on click. The **Show defaults** switch works.
  `detail` is drawn open, to show an expanded view.
- The "?" buttons go to the closest **existing** readthedocs pages, so they work today. The implementation links
  to sections of a new `reference/manage/` page instead (D-24).
- Only `list` and `detail` have full content when expanded. The other views are stubs, and every **Other**
  section ends in a "…" row that stands for the remaining attributes.
- The checks strip only shows the "no issues" state. The alert state (D-17) is not drawn.
- `customer` is a top-level ViewSet whose views all require a permission or the manage group. The parent badge
  and the "no permission" and "custom" badges (D-08) therefore appear only in the key in the Views card footer.
- The Users section and the superuser's name are drawn as with `CRUD_VIEWS_MANAGE_SHOW_USERS` on.
- The mockup is one self-contained file, so it has an inline `<script>`, a `<style>` block and `style` attributes.
  The implementation has none of them (D-30).

## Why

The manage page is developer-only (#361) and hard to read. `/customer/manage/` is about 10,800 px tall with 216
table rows: one `<h3>`, twelve `<h4>`, every section a `table table-striped`, separated by `<br><hr><br>`. Most of
the page is a 25-row key/value table per view, and most of those rows are `None` or the library's stock value.
Values print as raw Python (`True`, `None`, `['home']`). Declared and effective values look the same.

The maintainer opens the page for two things: **permissions** and **view configuration**. Both are scattered:
- "Who holds which permission" is split across three tables:
  - Permissions, which covers only the current user;
  - Permission Holders, which covers groups;
  - Global permission fallback, which is per view.
- "Which permission does this view need" (`cv_permission`) is not shown at all.
- What a project changed on a view is not shown either, unless it is one of the 25 fixed keys. The demo's
  `cv_modal`, `cv_show_related_objects`, `cv_message_template_code`, `cv_list_actions_inline`,
  `cv_object_detail_layout` and `cv_property_display` are invisible.

Defects in the current page:
- **Bug:** the `class` row shows `<class 'crud_views.lib.view.meta.CrudViewMetaClass'>` for every view.
  `get_view_data()` iterates `get_all_views()`, which returns view *classes*, so `str(view.__class__)` is the
  metaclass (`crud_views/lib/views/manage.py:172`).
- **Gap:** user-level Guardian object grants are invisible. Sam's actual access (`view_customer` and
  `change_customer` on 4 customers) does not appear, because `GuardianManageView.get_permission_holders()` only
  counts group grants (`crud_views_guardian/lib/views.py:426`) and the users list only covers direct model
  permissions.
- **Gap:** superusers hold every permission and appear nowhere.
- **No `.table-responsive`:** the manage tables don't scroll on narrow screens.

Relevant upstream code:
- `crud_views/lib/views/manage.py`
- `crud_views/templates/crud_views/view_manage.html`
- `crud_views_guardian/lib/views.py` (`GuardianManageView`)
- `crud_views_guardian/templates/crud_views/view_guardian_manage.html`
- `crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html`
- `crud_views/lib/button_classes.py` (class registry)
- `crud_views/lib/check.py` (W280, `CheckUnknownAttributes`)
- `crud_views/lib/viewset/__init__.py` (`register_view_class`, validators)

## Goals, non-goals, anti-goals

**Goals:**
- A developer answers "who holds which permission" and "how is this view configured, and what is special about
  it" at a glance.
- The stock Bootstrap 5 page looks structured, not only the Tabler one.
- Every card leads to its documentation.

**Non-goals:**
- **Access and impersonation:**
  - No change to manage access (#361).
  - No impersonation.
  - No access evaluation for another user. The page shows the signed-in user's own result (D-05). Checking another
    user, with an object and a trace of how access is decided, belongs to
    [#370](https://github.com/jacob-consulting/django-crud-views/issues/370) (D-29).
  - No manage page for Resource ViewSets. Upstream registers none (`crud_views/lib/viewset/__init__.py:205-208`).
- **Page features:**
  - No editing from the manage page.
  - No new settings.
  - No tabs.
  - No views-as-columns comparison grid.
- **Docs:** no full reference pages for core permissions/`cv_permission`, the `cv_*` view attributes, ViewSet fields
  or the system-check catalogue. The new manage docs page (D-24) covers what the page shows and links onward.

**Anti-goals (failure even if it works):**
- **A copied theme template:** a Tabler-only override template that drifts from upstream while the stock page stays
  flat.
- **Colour-only meaning:** colour as the only carrier of meaning.
- **Broken overrides:** breaking existing project templates that extend `crud_views/view_manage.html`.

## Approaches considered (how it is built)

1. **Templates only.** Rewrite the two templates and detect defaults with `{% if value is None %}`.
   - Smallest diff.
   - Cannot tell a stock template path from a custom one.
   - Pivoting the permission table in template loops is ugly.
   - **Rejected.**
2. **The view prepares the data, the template lays it out.** Presentation-ready structures in Python, `is_default`
   flags, existing blocks and context keys kept, badge colours through the class registry. **Chosen.**
3. **Like 2, plus a Tabler-only manage template in the theme.**
   - Full control over the look.
   - Copied templates drift silently, and the stock page stays flat.
   - **Rejected.**

Page-structure alternatives were compared as mockups:
- **A, tabs.** Rejected: hides content from browser search and needs hash handling.
- **B, one page of cards.** Chosen.
- **C, overview plus a views-as-columns grid.** Rejected: too wide once a ViewSet has workflow or custom action views.

## Decisions

### Purpose and layout

- **D-01 — Reader and focus.**
  - The reader is a developer, i.e. a manage-group member (#361).
  - The page is optimised for permissions and view configuration.
  - Everything else (ViewSet facts, hierarchy, ancestor policy, Guardian) stays on the page but is secondary.
- **D-02 — One page of cards (layout "B").** A single page, so browser search, printing and anchors keep working.
  On large screens:
  - **Main column:** checks alert (only when a check fails, D-17), Permissions, Views, Presentation (collapsed,
    D-21).
  - **Side column:** checks strip (D-17), ViewSet (D-18), Hierarchy (D-19), URL names (D-20), Ancestor policy,
    Guardian.
  - Below the large breakpoint the side column stacks under the main one.
  - **Ancestor policy card:**
    - Two labelled parts, "as ancestor of nested requests" and "requests to this ViewSet".
    - Two columns: the setting and its effective value, with an "inherited" marker where nothing is declared.
      There is no separate Declared column: a declared value is either `None` (inherited) or equal to the effective
      one (`view_manage.html:77-110`), so the marker carries the same information and the card fits the side
      column.
    - It keeps the "configuration only, not an access result" note and `id="cv-ancestor-policy"` as its anchor.
    - Rejected: keeping today's three-column table. Values such as "nearest: change, higher: view" would appear
      twice per row and wrap in a column a third of the page wide.
  - **Guardian card:** on Guardian pages only. A plain card rather than the current warning alert, showing
    `get_objects_for_user` (strict). `parent_viewset`, provider and `accept_global_perms` are not repeated there,
    because the Hierarchy and Ancestor policy cards already show them.
- **D-03 — Stock Bootstrap 5 only.**
  - Cards, list groups, tables, badges, a form switch and `<details>`.
  - No theme-specific markup upstream.
  - Every table sits inside `.table-responsive`.

### Permissions card

- **D-04 — Holder × permission matrix.**
  - **Columns:** the ViewSet's permissions (`viewset.permissions`). Each header shows the key with the codename as a
    sub-label, custom permissions included.
  - **Rows:** the signed-in user first (D-05), then holders in two labelled sections, **Groups** then **Users**.
    Holders are rows so that many of them make the table longer, not wider.
  - **Cells:** **model** (model-level permission), **n objects** (Guardian object grants), or a dash.
  - A footer legend explains the two badges.
- **D-05 — "Access for: you" row.**
  - The signed-in user's result is **one row at the top of the matrix**, labelled "Access for: *username* (you)".
    It replaces today's three-column `has_perm` table and uses the same cells as every other row:
    - **model** when `user.has_perm()` is true for that permission. Unlike the Users rows, this is the effective
      result: it includes rights through groups and superuser status.
    - **n objects**, on Guardian pages, for the objects the user reaches through object grants, their groups'
      grants included (`get_objects_for_user`, strict, one count per permission).
    - a dash otherwise.
  - Why it exists: `docs/reference/settings.md` ("Diagnose the signed-in account") and `guardian.md` tell
    developers to sign in as the affected user and read this result.
  - The row's data method takes a user, so #370 can feed it another user (D-29).
  - Rejected:
    - dropping the current-user result, which removes a documented workflow with nothing in its place;
    - per-view marks from `cv_has_access(user)`. Without an object, that method returns `False` for every Guardian
      object view and `True` for a Guardian list as soon as the permission key exists
      (`crud_views_guardian/lib/mixins.py:129-146, 201-208`), so every user would read the same line. The view
      badges (D-08) say which permission each view needs.
- **D-06 — Users behind the existing setting.**
  - The Users section renders only when `CRUD_VIEWS_MANAGE_SHOW_USERS` is on. Its default (False) is unchanged.
  - It lists users with a direct model permission or a direct Guardian object grant. Rights that come through a
    group show in that group's row.
  - Beyond about 20 users, the rest fold under a "+ n more" `<details>`.
- **D-07 — Guardian object grants for users and groups.**
  - `GuardianManageView` counts object grants per user and permission, next to the per-group counts.
  - Both counts go through Guardian's per-model lookups, `get_user_obj_perms_model()` and
    `get_group_obj_perms_model()`, so direct-foreign-key grant tables are counted and both cover the same tables.
  - The old `get_permission_holders()` keeps its query on the generic `GroupObjectPermission` (D-14).
- **D-26 — Superusers and group sizes.**
  - Each group row shows its member count.
  - A line under the matrix states how many active superusers exist ("hold every permission"). Their names appear
    only with `CRUD_VIEWS_MANAGE_SHOW_USERS`.
  - Why: Django grants an active superuser every permission, so without this the matrix can show a permission as
    held by nobody while several accounts have it. Two count queries per page.
  - Rejected: the superuser line alone (an empty group would still look like a holder), and leaving both out.
- **Auth queries.** Every query on auth or grant tables in this card runs only after `_check_nested_auth(...)`, with
  `provider="guardian"` on Guardian pages, as today's methods do (`crud_views/lib/views/manage.py:74,106`,
  `crud_views_guardian/lib/views.py:419`).

### Views card

- **D-08 — One summary line per view.**
  - Shows `cv_key`, the route (D-20), and the real view class as a dotted path (this fixes the metaclass bug).
  - **Requirement badges.** A view's requirement has two parts, and the line shows both:
    - its **own** requirement, one of:
      - **permission**, the permission key;
      - **group**, for the manage view;
      - **no permission required**, for view variants without `cv_permission`;
      - **custom**, when the view overrides the gate and describes nothing (D-27).
    - on a nested ViewSet, the **parent requirement** from the ancestor policy, as a second badge (e.g. `change`
      plus `parent: view`). It names the nearest ancestor's permission for the view's operation; the Ancestor
      policy card has the higher ancestors.
    - A nested Guardian **create** has no own requirement: `GuardianParentPermissionMixin.has_permission()` returns
      `True` there (`crud_views_guardian/lib/mixins.py:381-385`). It shows only `parent: change`. Nested Guardian
      detail, update and delete keep their own object permission (`get_object()`, `mixins.py:117-123`) and show
      both badges.
  - **Guardian policy badge**, on Guardian pages: the effective global-fallback policy, **global fallback**,
    **strict** or **not applicable**.
  - The separate "Global permission fallback" table is removed. Its content is in this badge and in the expanded
    view's Guardian section.
- **D-09 — Collapsed by default.** Each view is a native `<details>` element with the stable anchor
  `#cv-view-<key>`. All views start collapsed. The `<summary>` contains no link (D-24).
- **D-10 — The expanded view is one two-column key/value table.**
  - Keys sit in a fixed-width column that never wraps. Values take the remaining width.
  - Sections are thin heading rows, curated ones first:
    - **Navigation:** context and list actions, home/success/cancel keys, list action method, backend-only.
    - **Templates.**
    - **Icons.**
    - **Guardian**, on Guardian pages only: `guardian_mixin`, and `cv_guardian_accept_global_perms` with its
      effective policy.
    - **Other** (D-25): every remaining `cv_*` attribute.
  - **One key per row**, always in the same section and order, so two views compare line by line.
  - Keys are displayed without the `cv_` prefix.
  - Rejected:
    - three side-by-side columns, because values wrapped and it looked unclean;
    - set values first with defaults at the bottom, because a key's position would depend on whether it's set.
- **D-25 — "Other" section: every remaining `cv_*` attribute.**
  - After the curated sections, **Other** lists every `cv_*` data attribute of the view that no curated row shows,
    view-level `cv_context_buttons` included. Without it the page hides what makes a view special.
  - The attributes are found the way W280 finds them (`_collect_cv_names`, `crud_views/lib/check.py:296-306`):
    declared on a class in the MRO, data only (no methods, properties or other descriptors). `cv_viewset` is left
    out.
  - Rows are in alphabetical order, so two views still compare line by line.
  - Set/default follows D-11, and the Show defaults switch hides default rows here too.
  - An attribute W280 would flag as unknown is marked as such in its row.
  - Values: a class shows as its dotted path, anything else as a shortened `repr`. A name that is only annotated
    and has no value (e.g. `cv_formsets` on a view that doesn't set it) shows "not declared".
  - Rejected: keeping only the fixed key list of today's page.
- **D-11 — Effective values; "set" means set by a project class.**
  - Each row shows the value in effect.
  - Where `None` is a placeholder that resolves elsewhere, the row shows the resolved value and its source, e.g.
    `icon_header` → `building-store (from ViewSet)`.
  - **The rule:** an attribute is **set** when a class in the view's MRO whose module is outside the `crud_views*`
    packages has it in its own `vars()`. Everything else is a **default**. That includes library class values and
    values the library copied from a `CRUD_VIEWS_*` setting at import (e.g. `ListView.cv_context_actions` from
    `CRUD_VIEWS_LIST_CONTEXT_ACTIONS`).
  - This is the test W280 already uses (`CheckUnknownAttributes._suspects`, `crud_views/lib/check.py:387-394`).
    Reuse that code; don't write a second MRO walk.
  - **Exception, `cv_context_actions`:** `ViewSet.register_view_class()` writes
    `view_class.cv_context_actions = [*actions, "manage"]` onto the project class
    (`crud_views/lib/viewset/__init__.py:351-354`), so the attribute sits in every project view's `vars()` whether
    or not the project declared it. In the demo all five customer views have it; only `CustomerDetailView`
    declares it.
    - `register_view_class()` therefore records, before it assigns, whether the class declared the attribute
      itself, and the page uses that record.
    - The record is consulted for every registered class in the MRO, not only the leaf. A project view that
      subclasses another registered view would otherwise inherit the base's library-written copy and show "set".
  - Accepted consequences:
    - a project-wide setting shows greyed out on every view; it stays visible while defaults are shown;
    - a project package whose name starts with `crud_views` (a theme such as `crud_views_tabler`) counts as
      library code, as it does for W280.
  - Rejected: comparing against crud_views' shipped defaults, which would need provenance tracking for settings
    copied at import.
- **D-12 — Dimmed and switchable.**
  - Default rows are greyed out.
  - In every row the key stays visually stronger than the value: keys are darker and medium weight, default values
    are muted.
  - One **Show defaults** switch in the Views card header shows or hides default rows for all views at once, and in
    the Presentation card too (D-21).
  - With JS, default rows are **hidden on load**. The page exists to show what is special, and most rows are
    defaults.
  - A section whose rows are all hidden says "n defaults hidden", so an expanded view never looks empty or broken.
  - Without JS, all rows are visible.
  - The choice isn't stored.
  - The four `*_template_code` entries may collapse into one row when all of them are empty.
  - Rejected: defaults shown on load (the long lists return by default), and remembering the choice in
    `localStorage` (more JS and a stored key).

### ViewSet facts (side column)

- **D-17 — System checks for this ViewSet.** Run on page load.
  - **No messages:** a small strip at the top of the side column: "✓ no issues · n system checks for this ViewSet".
  - **Warnings or errors:** an alert at the top of the main column, above Permissions, listing each message with its
    check id (e.g. `viewset.W280`).
  - **Scope:** `viewset.checks()` plus the checks that are registered separately, restricted to this ViewSet:
    - the ancestor declaration checks including E269 (`crud_views/checks.py:198`);
    - the conditional checks (`crud_views/checks.py:394`);
    - the icon check (`crud_views/checks.py:584`);
    - on Guardian pages, `crud_views_guardian.E001` (`crud_views_guardian/checks.py`).

    Without them the strip would say "no issues" while `manage.py check` fails. Project-wide checks (settings,
    assets, button classes) are not shown.
  - Those registered functions return messages for all ViewSets, and the icon check's messages carry no object to
    filter by (`crud_views/checks.py:592-601`). Each function is therefore split so that its per-ViewSet part can
    be called alone.
  - Messages whose id is in `SILENCED_SYSTEM_CHECKS` are left out, as Django's own runner does.
  - The "n" in the strip counts the `viewset.checks()` entries only.
  - Cost, measured in the demo: the 178 `viewset.checks()` for `customer` take about 10 ms on the first run and
    1 ms after. The separately registered checks are not measured.
- **D-18 — ViewSet identity card.**
  - Shows name, prefix, pk/pk_name and app.
  - Adds the model as a dotted path.
  - Adds verbose name and plural, ordering, and the header icon (drawn, plus its name).
  - Values the ViewSet doesn't set show the effective value with its source, e.g. `customer · customers (model
    Meta)`.
- **D-22 — "Set" for ViewSet fields.**
  - A ViewSet field is **set** when the project passed it to the constructor. This is D-11 applied to the ViewSet
    instance.
  - pydantic's `model_fields_set` is not that list. The validators assign `pk` and `prefix`
    (`crud_views/lib/viewset/__init__.py:182-196, 285-286`), and an assignment adds the field to the set. The
    passed names are therefore recorded before the validators run (e.g. the input keys in a `mode="before"`
    validator).
  - For the demo's `customer` the set fields are model, name, icon_header, ancestor_policy and context_buttons.
- **D-19 — Hierarchy card.**
  - **Parents:** the full chain up to the top level, each linked to its manage page.
  - **Children:** every registered ViewSet whose `parent` is this one, with its model, plus the URL name and pattern
    of its manage page (e.g. `order-manage → /customer/<customer_pk>/order/manage/`).
  - A Resource child has no manage route. It is listed with its model and the note "Resource, no manage page".
  - **Links go up only.** A nested manage URL needs a parent object, and the parent's manage page has none. Going
    up, any required ancestor pks come from the current URL.
  - The card says how to get to a child's manage page: open the child's list under a parent object and use its
    manage action. Every registered view gets that action (`crud_views/lib/viewset/__init__.py:351-354`).
  - Rejected:
    - linking through a sample object, which costs extra queries and permission checks and gives no link for an
      empty table;
    - a new route for nested manage pages that needs no parent object, which would change URL routing and nested
      permissions.
- **D-20 — URL names card.** Each view's route name and route, e.g. `customer-list → /customer/`.
  - The route is a regex (`^customer/(?P<pk>\d+)/detail/$`, built in `crud_views/lib/viewset/__init__.py:455`). It
    is shown through Django's `django.contrib.admindocs.views.simplify_regex`, which gives
    `/customer/<pk>/detail/`. The import works without `admindocs` in `INSTALLED_APPS`.
  - It is the ViewSet's own route. A prefix added by the project's `include()` isn't known to the ViewSet, so the
    column is labelled "route (relative to where the ViewSet is included)".

### Presentation card (main column)

- **D-21 — Presentation, collapsed.**
  - A `<details>` card below Views, collapsed on load. Its header shows "n set · m defaults · applies to all views".
  - It sits in the main column because the button targets need the width.
  - Rows follow D-10 to D-12, with "set" as defined in D-22.
  - **Context buttons:** a table with key, button type, **what it points to**, and label. "Points to" is derived from
    each button type's own fields:
    - `ContextButton` with `key_target`: the route name and route;
    - `ParentContextButton`: the parent's view, or "top level, never shown";
    - `ChildContextButton`: the route from `child_name`/`child_key`;
    - `SiblingContextButton`: the sibling ViewSet's view;
    - `FilterContextButton`: "toggles the list filter", plus its template;
    - a custom subclass: falls back to its type and template.

    Child and sibling targets are shown without links (same reason as D-19). A note says that each view's
    `context_actions` row decides where a button appears, and that a view's own `cv_context_buttons` show in its
    **Other** section.
  - **Templates and actions:**
    - `extends`;
    - `inaccessible_actions`, showing the effective value and naming the setting it comes from, if any;
    - the three `*_actions_inline` lists.
  - **Label modes:** the context, list and form label modes.
  - **Other:** `manage_view_class`, showing the effective class.

### Badges and documentation links

- **D-23 — Short permission and group badges.**
  - **Blue = permission:** the badge text is the permission key (`view`, `add`, a custom key like `roast`). Its
    tooltip says "needs permission: sales.add_customer", the full Django permission string. The parent badge uses
    the same colour with the text `parent: <key>`.
  - **Magenta = group membership:** the badge text is the group name, i.e. the configured `CRUD_VIEWS_MANAGE_GROUP`.
    Its tooltip says "needs group membership: CRUD_VIEWS_MANAGE". The library draws it for the manage view only; a
    project view gets one through D-27.
  - **Neutral = no permission required, or custom.**
  - Colour is never the only carrier of meaning:
    - each badge has a tooltip;
    - a `visually-hidden` prefix ("permission", "group") is there for screen readers;
    - the Views card footer has a key: blue = required permission, magenta = required group, green = Guardian
      policy, "hover a badge for details".
  - **Tooltips:** badges carry a `title` and the `data-cv-tooltip` marker. The tooltip adapter only touches marked
    elements (`crud_views/static/crud_views/js/tooltip.js:27`), so the marker is what lets a theme style them. The
    stock page gets Bootstrap tooltips through the stock adapter (`adapters.js:93`), and `title` is the fallback
    without JS.
- **D-24 — Documentation links through one new docs page, `docs/reference/manage.md`.**
  - **Where the links are:**
    - every card header gets a small round **"?"** button at the top right, after any existing card actions
      (e.g. after the Show defaults switch);
    - so do the checks strip and the Presentation sections "Templates and actions" and "Label modes".
  - **Badges are not links.** Their documentation is reached through the Views card's "?" button and the badge key
    in the card footer. The badges sit inside each view's `<summary>` (D-09), and a link there gives the line two
    click behaviours and adds tab stops before every view.
  - **How they open:** in a new tab (`target="_blank" rel="noopener"`, `aria-label="Documentation: <card>"`).
  - **Where they point:** every link goes to a section of the new manage page in the docs, one section per card. Each
    section explains its card and links on to the detailed pages:
    - `reference/nested/#ancestor-authorization`
    - `reference/guardian/#guardianmanageview`
    - `reference/context_buttons/`
    - `reference/action_menus/#label-mode`
    - `reference/settings/#manage-diagnostics`
  - **Why one page:** the anchors belong to this feature, so renaming headings elsewhere cannot silently break the
    page's links.
  - **Docs version:** links go to the **`stable`** docs. Readthedocs builds only `latest` and `stable`, and
    `stable` matches released code. Accepted consequence: until a release, links point at sections `stable`
    doesn't have yet.
  - **Base URL:** not a setting. It is an attribute of `ManageView`, passed to the template as one context value.
    A project that hosts its own docs sets it on a subclass named in `CRUD_VIEWS_MANAGE_VIEW_CLASS` /
    `manage_view_class`, which exist today.
  - **Help-button class:** comes from the class registry, e.g. `manage:help`; the stock class is
    `btn btn-sm btn-outline-secondary`.
  - **Rejected:**
    - linking each card straight to existing pages: four cards have no matching page (permissions/`cv_permission`,
      view attributes, ViewSet fields, system checks), and the links would depend on other pages' headings;
    - writing those missing reference pages in this issue, which doubles the scope (now a non-goal);
    - badges as links, and plain badges with a linked requirement row in the expanded view (one more row per
      view);
    - a template block for the base URL: the URL is used by about fifteen links.

### Access description and the follow-up

- **D-27 — A view describes its own requirement.**
  - A public classmethod on `CrudView` returns what the view needs. The return value is small:
    - the view's **own** requirement: a permission key, a group, none, or "custom";
    - whether the **ancestor policy applies** to it.
  - The parent part of the badge is not returned by the method. The page reads it from the ancestor policy data it
    already computes (`ManageView.get_ancestor_policy_data()`), so no view duplicates it.
  - Each class that owns a gate implements the method next to it: `CrudViewPermissionRequiredMixin` from
    `cv_permission`, `ManageView` from `CRUD_VIEWS_MANAGE_GROUP`, the Guardian parent mixin for the nested create
    case, and the views of `crud_views_workflow`, `crud_views_polymorphic` and `crud_views_object_detail` where
    their gate differs.
  - The D-08 badges are drawn from this method, not from `cv_permission` directly. A project view that overrides
    `has_permission()` overrides the method to describe itself; otherwise it shows "custom".
  - Why a method: the answer depends on which mixins a view is built from, #370's trace needs the same answer, and
    a description kept next to the gate changes with it.
  - Risk: a description can drift from the real gate. The tests pair each shipped view class with a request that
    proves the described requirement is the enforced one.
  - Rejected:
    - the logic inside `ManageView` only: it would have to know every mixin in every package, custom views would
      always show "custom", and #370 would need its own copy;
    - reading `cv_permission` only: wrong for nested Guardian views.
- **D-29 — What #370 adds to this page. Not part of #366.**
  - The "Access for" row (D-05) gets a form: a typed username (no dropdown of all accounts), an optional object
    pk, and a Check button. It is a GET form and changes nothing.
  - Without an object pk the result is the matrix row for that user. With one, each view also gets a yes or no
    for that object.
  - The trace (which grant or ancestor rule decided) comes from one function shared by the page and the command
    line. Today that logic is bound to a request (`_cv_ancestor_guard()` in `dispatch`), which is #370's open
    design question.
  - #366 only has to keep this possible: the row's data method takes a user (D-05), and the requirement method
    exists (D-27).

### Building it

- **D-13 — The view prepares, the template lays it out.**
  - `ManageView` builds presentation-ready structures:
    - permission columns, the signed-in user's row and holder rows;
    - each view's summary and its sectioned entries, with an `is_default` flag on each entry;
    - the ViewSet facts, hierarchy, URL names, presentation rows and check results.
  - `GuardianManageView` extends the same structures (object counts including user grants, Guardian entries and
    badges) instead of keeping a parallel table.
  - Templates contain no default detection and no pivoting.
  - The new data methods take the ViewSet and the user as arguments and don't read `self.request`. Today's
    methods do (`crud_views/lib/views/manage.py:74,106`). A command can then call them without a web request:
    the configuration dump planned in
    [#371](https://github.com/jacob-consulting/django-crud-views/issues/371) and the access trace of #370.
  - The core template renders the complete Guardian page from that data. The Guardian template stays as a file but
    adds nothing the page depends on, because a project may replace it entirely and fill only `guardian_config`
    (`tests/test1/test_authorization_templates.py:77`).
- **D-14 — Compatibility.**
  - The existing block names stay, and each **wraps its whole new card**: `permission_holders` the Permissions
    card, `ancestor_policy` the Ancestor policy card, `guardian_config` the Guardian card. Every other card gets
    one new block.
  - A project override of an old block replaces that card at the card's position and is fed by the old context
    keys. The overriding project loses the new card (the "you" row and the superuser line included) until it
    updates its template; the migration notes say so.
  - The existing context keys stay with their current shapes: `cv`, `data`, `views`, `permission_holders`,
    `show_users`, `ancestor_policy`, and on Guardian pages `guardian_config` and `views[*].guardian_policy`. New
    structures go under new keys.
  - The cards are fed by **new** data methods. `get_view_data()` and `get_permission_holders()` keep their output
    and only feed the old keys, so project overrides of those methods don't affect the new cards.
  - The old keys `data`, `views` and `permission_holders` are computed lazily, on first use by a template. No stock
    template reads them, and `get_permission_holders()` costs a query per permission
    (`crud_views/lib/views/manage.py:77-92`).
  - User grants (D-07) appear only in the new matrix data.
  - The `class` fix applies to both the old and the new data.
  - Visible output changes are documented in the migration notes.
  - Rejected: old blocks as empty hooks below the cards. Nothing would be lost, but an overriding project would
    show the same information twice.
- **D-30 — No inline JavaScript (CSP).**
  - The page ships no inline `<script>`, no inline event handler (`onclick`, `onchange`, …) and no `javascript:`
    URL. The package documents itself as usable under a CSP without `unsafe-inline`
    (`docs/reference/settings.md`, "Content Security Policy (CSP)"), and the manage page must not break that.
  - The Show defaults switch (D-12) is therefore driven by an external static file, loaded through `{% cv_js %}`
    like the package's other scripts, with event delegation on a `data-cv-*` attribute. Either a new file in
    `crud_views/static/crud_views/js/` or an addition to an existing one.
  - Tooltips already work this way (`tooltip.js`, D-23). `<details>` needs no script.
  - The same documented policy covers inline styles. Fixed widths and similar come from CSS classes in the
    package's stylesheet, not from `style` attributes.
- **D-15 — Badge and row classes through the class registry.**
  - The keys follow the `workflow:badge-<colour>` pattern, e.g. `manage:badge-model`, `manage:badge-objects`,
    `manage:badge-permission`, `manage:badge-group`, `manage:badge-policy-<state>`, `manage:row-default`,
    `manage:help`. Exact names are a planning choice.
  - The keys are added to the registry's defaults; a theme key the defaults don't know is flagged by
    `crud_views.W362` (`crud_views/lib/button_classes.py:384-417`).
  - Stock defaults are Bootstrap 5 classes (`text-bg-*`, `text-body-secondary`).
  - Themes register their own. tabler-test will register `bg-*-lt`.
- **D-28 — Existing tests and docs that pin the old page.** These change with the page:
  - `tests/test1/test_ancestor_manage.py:485-486` asserts rows of the "Global permission fallback" table that D-08
    removes;
  - `tests/test1/test_ancestor_manage.py:343-348` (`_policy_table`) parses the three-column
    `table table-striped#cv-ancestor-policy`; the helper is rewritten for the two-column card (D-02), and the tests
    that use it keep asserting the same declared/inherited and effective facts;
  - `tests/test1/test_authorization_templates.py:77` overrides the `guardian_config` block and must keep passing
    (D-14);
  - `docs/reference/guardian.md#guardianmanageview` and `docs/reference/theme.md:762` describe the current tables
    and context;
  - `docs/reference/settings.md` ("Diagnose the signed-in account") is reworded for the "Access for: you" row;
  - both packages ship a `de` locale, which gets the new strings.
- **D-16 — Handoff.** The upstream deliverable is #366 with its `gsd-handover` section. Filing it doesn't implement
  the feature, create a phase or create a worktree.

## Left to the builder

- Exact names: context keys, blocks and class keys.
- Where `register_view_class()` keeps its record of a declared `cv_context_actions` (D-11), and where the ViewSet
  keeps the passed field names (D-22).
- The name and exact return type of the requirement method (D-27).
- How the separately registered check functions are split into per-ViewSet parts (D-17).
- How lists and tuples are displayed.
- The "+ n more" threshold.
- Card order inside the side column.
- Wording of labels, badges and tooltips (translatable).
- The section structure of `docs/reference/manage.md`.
- Example-app and docs coverage, in proportion to the change.

## Acceptance criteria

**Layout and data**
- Core and Guardian manage pages render the card layout of D-02. No `<br><hr><br>` remains.
- At 390 px viewport width, the page doesn't overflow sideways.
- Nested ViewSets render the full ancestor policy (cascade, read, write, actions) in the two-column card, with the
  "inherited" marker where nothing is declared.

**Permissions**
- Permissions render as the D-04 matrix.
- The "Access for: you" row shows, per permission, **model** for the signed-in user's `has_perm` result (a right
  held only through a group counts) and, on Guardian pages, the number of objects reachable through grants. There
  are no per-view marks.
- With `CRUD_VIEWS_MANAGE_SHOW_USERS` on, user-level Guardian grants are listed with per-permission counts. With it
  off, there is no Users section, on both core and Guardian pages.
- Group rows show member counts, and the superuser line shows the count of active superusers.

**Views**
- The `class` entry shows the view class's dotted path (regression test).
- `is_default` follows D-11 and D-22, unit-tested on the data rather than the HTML:
  - library value → default;
  - value copied from a setting → default;
  - attribute on a project class → set;
  - a placeholder `None` → shows the resolved value and its source;
  - `cv_context_actions` that only gained the library's `manage` entry → default; declared on the project class →
    set; inherited from a registered base class that didn't declare it → default;
  - a ViewSet field is set only when the project passed it: `pk` and `prefix` filled in by the validators are
    defaults.
- The **Other** section lists a project-set attribute outside the curated rows (e.g. `cv_modal`) as set, and
  contains no method or property.
- The Show defaults switch hides and shows default rows in Views (Other included) and in Presentation. With JS,
  defaults are hidden on load, and a section with only default rows shows "n defaults hidden". Without JS, all
  rows are visible.
- The requirement badges render each case: permission, group (manage view), no permission required, custom, own
  plus parent requirement (nested detail), and parent requirement only (nested Guardian create).
- For every shipped view class, a request test proves that the requirement the method describes is the one
  enforced.
- A view's `<summary>` contains no link.
- The rendered core and Guardian pages contain no inline `<script>`, no `on*` attribute, no `javascript:` URL and
  no `style` attribute (test on the HTML). The switch works under a CSP without `unsafe-inline`.

**ViewSet facts and Presentation**
- System checks:
  - a ViewSet with a failing check shows the alert at the top of the main column, with the check id;
  - a clean ViewSet shows the "no issues" strip with the number of checks;
  - a ViewSet that fails only a separately registered check (e.g. E269) shows the alert;
  - a message silenced through `SILENCED_SYSTEM_CHECKS` is not shown.
- Hierarchy:
  - on a top-level ViewSet, children are listed with their manage URL name and pattern, unlinked;
  - on a nested ViewSet, the parent chain links to the parents' manage pages, and those links resolve;
  - a Resource child is listed without a manage route, and the page renders without error.
- Routes render in the readable form (`/customer/<pk>/detail/`), not as regexes.
- Context-button targets render for `key_target`, parent, child, sibling and filter buttons. A custom subclass
  renders without error.
- Presentation is collapsed on load.

**Badges and docs**
- Requirement badges show the short key or group name, with the D-23 tooltip, the `data-cv-tooltip` marker and the
  hidden prefix. The Views card shows the key.
- `docs/reference/manage.md` exists, is linked from the reference index, and has one section per card.
- A test collects every docs anchor the templates link to and asserts that each exists as a heading in that page.
- Every "?" button points at `https://django-crud-views.readthedocs.io/en/stable/reference/manage/#…` and opens
  in a new tab. The base URL comes from the manage view class; a subclass with another base URL changes every
  link.

**Compatibility**
- A template that extends `crud_views/view_manage.html` and overrides `permission_holders` and `guardian_config`
  still renders (test), and each override appears in place of its card, not next to it.
- A Guardian page whose Guardian template is replaced by one that fills only `guardian_config` still shows the
  matrix with object counts and the per-view Guardian badges.
- The old context keys trigger no query when no template reads them (query-count test).
- Badge and help classes resolve through the class registry with Bootstrap 5 defaults. A test registers a custom
  class and sees it rendered.

**Docs and example**
- Docs updated: the manage page reference, the migration notes and the pages named in D-28.
- The `de` locales of both packages contain the new strings.
- The bootstrap5 example updated.

## Downstream adoption in tabler-test (separate task, after release)

- Register Tabler classes for the `manage:*` keys in `crud_views_tabler`.
- Drop the finding-25 overflow rule (`#cv-ancestor-policy` scroll below 768 px) once the tables are in
  `.table-responsive`.
- Update finding 35.
