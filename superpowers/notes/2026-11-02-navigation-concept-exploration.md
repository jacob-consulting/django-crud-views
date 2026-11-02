# Concept exploration: navigation for django-crud-views

Analysis only; no code changed. Every claim below points at code. Paths without a repository prefix are in
`jacob-consulting/django-crud-views`, branch `introduce-gsd` @ `6bef437`. `tabler-test` is
`alexander-jacob/tabler-test` @ `7474883`. Django is 5.2.18 and django-guardian 3.5.2 (the versions installed for this
reading; line numbers of their sources refer to those releases).

## 1. The ask

A navigation component for django-crud-views that

- points nav items at crud views (a ViewSet's `list` view, mostly);
- nests, and we need to know how deep;
- honours django-crud-views permissions, django-guardian permissions and plain Django permissions;
- accepts generic submenu injections through a hook;
- is fast, with the caching options and their trade-offs laid out;
- is themable through templates (Bootstrap 5 core, Tabler downstream);
- works as the one global app navigation and also as several navs on one page (a global nav on top plus a tree
  nav on some pages).

At least two technical approaches, with pros and cons for every aspect.

## 2. What the code gives us today

### 2.1 There is no navigation component, by decision

The breadcrumb is the only cross-page chrome the package renders, and its docs draw the line explicitly: "The
breadcrumb deliberately covers only the crud-views hierarchy; it is not a navigation framework"
(`docs/faq.md:266-268`). Its extension point for site chrome is a static prefix list or a method override
(`docs/reference/breadcrumb.md:34-59`, `src/crud_views/lib/breadcrumb.py:110-112`).

The two real consumers each hand-roll their navigation:

- The Tabler project writes the navbar by hand with Django's `perms` wrapper and hard-coded URL names:
  `{% if perms.customers.view_customer %}` … `{% url 'customer-list' %}` … active state from
  `request.resolver_match.url_name` (`tabler-test/templates/includes/navbar.html:2, 19-26`). Nothing in it comes
  from the ViewSet.
- The example project keeps its own feature registry (`examples/bootstrap5/project/features.py:31-63`,
  `FEATURES`/`GROUPS`), a template tag that returns groups plus the active group/app
  (`examples/bootstrap5/project/templatetags/example_tags.py:13-24, 43-48`) and a Bootstrap navbar template with one
  level of dropdowns (`examples/bootstrap5/project/templates/project/nav.html:11-33`). Active detection walks from
  the view class's module to a feature (`example_tags.py:47`).

Both are what a navigation component must replace: a per-project list of targets, each with a label, an icon, a
URL name, a permission and an "am I active" rule.

### 2.2 The registry: everything a nav needs to enumerate is already there

- Every ViewSet registers itself by name in a module-level `OrderedDict` guarded by a lock
  (`src/crud_views/lib/viewset/__init__.py:43-44, 146-151`); lookup is `ViewSet.get_viewset(name)`
  (`:160-164`), and `checks_all()` already iterates the whole registry (`:166-174`).
- Views register on the ViewSet at class-creation time through the metaclass (`src/crud_views/lib/view/meta.py:15-24`,
  `register_view_class` at `viewset/__init__.py:318-326`). `get_all_views()` returns the key → class map
  (`:179-180`); `is_view_registered` / `get_view_class` resolve a key, with the `list` → `card` fallback
  (`:336-343`).
- The URL name of a view is `[app:]<name>-<key>` (`get_router_name`, `:345-352`). The URL pattern is
  `[parent_prefix/parent_pk/]*prefix/[pk/]path/` (`:362-434`); the parent chain is walked with `while` loops, so
  the nesting depth of ViewSets is unbounded (`:243-250, 368-374`). Tests exercise three levels
  (`tests/test1/app/views.py:1019, 1035`: `publisher_bc` → `book_bc` → `booknote_bc`); the docs promise
  "a grandchild simply names its immediate parent" (`docs/reference/nested.md:16, 37, 80`).
- The registry is private. There is no public "all ViewSets" accessor; `checks.py:17, 43-44`, `lib/check.py:311-314`
  and `DeleteView.cv_get_related_object_url` (`src/crud_views/lib/views/delete.py:186-204`) import `_REGISTRY`
  directly. That delete helper is also the one existing precedent for "URL to a view from an object, without view
  kwargs": it finds the ViewSet by model, builds `{pk_name: obj.pk}` plus one parent level from the FK, and
  catches `NoReverseMatch`. An approach that enumerates ViewSets needs a public iterator first.
- Timing matters: the registry is filled when the modules that instantiate the ViewSets are imported, and that
  happens through the URLconf (`tests/test1/app/urls.py:1-43` imports the views and appends
  `cv_*.urlpatterns`). Django imports the URLconf lazily on the first `resolve()`/`reverse()` (`get_resolver` is
  `lru_cache`d, `django/urls/resolvers.py:108-115, 249`). A nav definition that names ViewSets must therefore be
  resolved lazily, at first render, never at settings-import time. `get_viewset()` raises
  `ViewSetNotFoundError` for an unknown name (`viewset/__init__.py:162`), which is the natural place for a system
  check.

### 2.3 Building a URL to a view, with and without a view instance

- Inside a crud view, `cv_get_url(key, obj)` builds the sibling URL; the parent pks come from the view's own
  URL kwargs (`src/crud_views/lib/view/base.py:527-567`, parent loop at `:549-553`). `cv_get_child_url` does the
  same for a child ViewSet (`:826-846`).
- Outside a crud view there is no `self.kwargs`. A top-level `list` view needs only
  `reverse(viewset.get_router_name("list"))`. A child ViewSet's `list` needs every parent pk
  (`get_parent_url_args`, `viewset/__init__.py:236-252`). So a nav item that points at a child ViewSet is only
  resolvable when the nav has a parent object in hand (a tree nav under an object) or when the current request
  carries the parent pk in `request.resolver_match.kwargs`. This is the one hard structural constraint on
  "nav items point at crud views".

### 2.4 Labels and icons: what can be computed without a request

- `cv_get_action_short_label(context)` and friends render the view's snippet templates with
  `viewset.get_meta(context)` (`base.py:444-458`, `viewset/__init__.py:478-496`). `get_meta` only reads
  `context.to_dict()` (the object), but the `ViewContext` type requires a `view` (`src/crud_views/lib/view/context.py:16`),
  and `cv_get_dict` reads `context.router_name`, which dereferences `view.request` (`context.py:47-49`,
  `base.py:486`). A navigation rendered on a non-crud page (a dashboard) has no CrudView instance, so it cannot
  reuse these label helpers as they stand. The same holds for every existing tag: `cv_get_view` asserts that
  `context["view"]` is a CrudView (`templatetags/crud_views.py:72-75`), so nav tags need their own entry point.
  The grounded options for labels are: a label on the nav item, the model's `verbose_name_plural` the way
  `get_meta` derives it (`viewset/__init__.py:482-492`), or a new request-free classmethod on CrudView.
- Icons are easy: `cv_icon_header` falls back to `viewset.icon_header` (`base.py:422-425`), and
  `render_icon()` / `{% cv_icon %}` render any semantic name (`src/crud_views/lib/icons.py:231`,
  `src/crud_views/templatetags/crud_views.py:513-516`). The Tabler consumer already sets
  `icon_header="tabler:building-store"` on its ViewSet (`tabler-test/customers/views.py:26`).
- Active state: `cv_get_dict` sets `cv_is_active` by comparing `get_router_name(key)` with
  `request.resolver_match.url_name` (`base.py:486`). Note that `get_router_name` includes the `app:` namespace
  (`viewset/__init__.py:351-352`) while `ResolverMatch.url_name` does not; the namespaced name is `view_name`
  (`django/urls/resolvers.py:51, 61, 74`). A nav must compare against `view_name`, or the comparison silently
  fails for namespaced ViewSets. "Active ancestor" (the Publishers item lit while on a Book page) is a walk up
  `viewset.parent` (`src/crud_views/lib/viewset/parentviewset.py:47-54`).

### 2.5 The access API that links already use

Every sibling link in the package goes through one classmethod, `cv_has_access(user, obj=None)`:

| Target view | `cv_has_access` | Where | What it costs |
|---|---|---|---|
| plain `ListView` etc. (no permission mixin) | always `True` | `base.py:353-354` | nothing |
| `*PermissionRequired` | `user.has_perms((perm,))` with `perm = viewset.permissions[cv_permission]` | `base.py:926-930` | first call per user per request: two queries (user perms, group perms), then a set lookup; see 2.6 |
| Guardian list view (`GuardianQuerysetMixin`) | `True` unless the user is an inactive authenticated user | `src/crud_views_guardian/lib/mixins.py:130-131` | nothing |
| Guardian object view (`GuardianObjectPermissionMixin`) | `False` without an object; with one: optional global `has_perm`, then `ObjectPermissionChecker(user).has_perm` | `mixins.py:79-92` | one checker per call, one or two queries per object |
| Guardian child create | needs the parent object or an own child; `False` otherwise | `src/crud_views_guardian/lib/views.py:344-379` | as above |
| `ManageView` | inherits the default `True`; its real gate is the instance method `has_permission()` | `src/crud_views/lib/views/manage.py:30-38` | — |

Three consequences for a nav:

1. **`cv_has_access` is the link-visibility API, not the request gate.** The package says so itself: hiding a
   control "is presentation, not protection: every request is checked again on the server"
   (`docs/reference/theme.md`, "Authorized data in overridden templates"). A nav that calls `cv_has_access` has
   exactly the semantics of the context-action toolbar, which is the right bar to clear.
2. **Guardian list targets are always "visible"** (`mixins.py:130-131`, by design: the list page is always
   reachable, the queryset is the gate). Two things follow. An anonymous user also gets `True` there while the
   request gate redirects to login (`mixins.py:118-127`), so a nav needs an "authenticated only" rule for Guardian
   targets. And "hide the item when the user can see no object" is a separate, optional probe:
   `GuardianViewSet.get_objects_for_user(user, "view")` is public, strict, and handles inactive users
   (`src/crud_views_guardian/lib/viewset.py:122-142`); `.exists()` on it is one query per item.
3. **The secondary state gate exists too.** `cv_action_enabled(user, obj)` is evaluated after access for every
   button (`base.py:357-379`, `_cv_get_action_context` at `:717-726`). For a `list` target it is called with
   `obj=None` and defaults to `True`; a nav should call it the same way so that a project override behaves the
   same in the toolbar and in the menu.
4. **`cv_has_access` is incomplete in two places a nav will hit.** A `*PermissionRequired` view whose permission
   row is missing yields `has_perms(())`, which is `True`, while the request path asserts (`base.py:902-911` vs
   `:926-930`): the link and the request disagree. And a Guardian *child* list's `cv_has_access` never checks the
   parent permission; only `dispatch` does, through the private classmethod `_guardian_user_has_parent_perm`
   (`mixins.py:262-277, 303-323`). A tree nav that lists child ViewSets under a parent object must call that rule
   itself, which means making it public.

The template-side equivalent exists but needs a view: the filter `cv_context_has_permission` takes the current
view and a key (`templatetags/crud_views.py:467-473`). Plain Django permissions in templates come from the `perms`
wrapper, which is `user.has_perm("app.codename")` per lookup (`django/contrib/auth/context_processors.py:5-13`).

### 2.6 How cheap the permission checks are, in Django and guardian

- `ModelBackend` caches the user's permission set on the user instance for the request:
  `_user_perm_cache`, `_group_perm_cache` and `_perm_cache` (`django/contrib/auth/backends.py:104-121, 166-171`).
  The first `has_perm` costs two queries; every later check on the same `request.user` is a set lookup.
  Superusers short-circuit before any backend (`django/contrib/auth/models.py:384-397`); inactive or anonymous users
  get an empty set (`backends.py:110`). So for plain and crud-views permissions, N nav items cost two queries
  per request, not 2N.
- Passing an object disables that cache: `_get_permissions` returns an empty set when `obj is not None`
  (`backends.py:110, 127`), which is why the Guardian mixins check the global permission without the object
  (`mixins.py:59-61, 84-86`).
- guardian's backend answers `False` whenever no object is passed ("If no `obj` is given, `False` is returned",
  `guardian/backends.py:68-74`), so plain `user.has_perm("app.view_x")` never touches guardian tables.
- `ObjectPermissionChecker` caches per object per checker instance (`guardian/core.py:39-63, 170-187`); a new
  checker per call, as the mixins do (`mixins.py:65, 90, 323`), forgets everything. `prefetch_perms(queryset)` fills
  that cache for a whole queryset in one go (`core.py:194-215`), and `GUARDIAN_AUTO_PREFETCH` turns prefetching on
  globally (`guardian/conf/settings.py:43`, `core.py:165-173`). A tree nav over objects should hold one checker for
  the whole render and prefetch.
- `get_objects_for_user` with `accept_global_perms=True` returns the whole queryset when the user has the global
  permission (`guardian/shortcuts.py:565-573, 679-700`); the strict helper in `GuardianViewSet` pins
  `accept_global_perms=False` (`viewset.py:13, 136-142`).

### 2.7 Theme surface conventions the nav has to follow

- Theming is template override by app order, no setting (`docs/reference/theme.md`, "How resolution works";
  `CRUD_VIEWS_THEME` triggers `W110`, `src/crud_views/lib/settings.py:204-215`). `theme_path` is the constant
  `"crud_views"` (`settings.py:286-287`) and every inclusion tag is bound to `crud_views/tags/...`
  (`templatetags/crud_views.py:60-67, 151-152, 390-391`).
- Logic templates vs leaves: thin logic templates (`tags/context_action.html`, `tags/actions_menu_item.html`) are
  not to be copied; themes override the leaves under `tags/button/` and register classes
  (`docs/reference/theme.md`, "Worked example"). Classes come from one table with `location:slot[:mode]` keys,
  registered from `AppConfig.ready()` with project settings winning per key (`src/crud_views/lib/button_classes.py:125-156`).
  Icons: `register_icon_library` / `register_icons` (`src/crud_views/lib/icons.py:125-134`). Assets:
  `register_assets` (`src/crud_views/lib/assets.py:53-71`). All three keep module-level registries reset through
  `setting_changed` (`icons.py:112-123`, `button_classes.py:114-123`).
- Two vocabularies are closed and check-enforced. `cv_button_data` raises for any location outside
  `LOCATIONS = {"context", "list", "card", "form"}` (`src/crud_views/lib/view/button_data.py:19, 116-117`), and
  `default_label_mode` raises for a location it does not know (`src/crud_views/lib/view/label_mode.py:95-98`), so a
  `nav` location means adding it there, to `LABEL_MODE_DEFAULTS` and to the E108 vocabulary. `W362` warns for
  every theme or settings class key that is neither in `DEFAULT_BUTTON_CLASSES` nor a valid mode key
  (`button_classes.py:301-319`), so `nav:*` keys must ship in the default table or every theme that registers
  them gets the warning. There is no theme layer for label modes yet (issue #278, listed in
  `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md:103`).
- Dropdowns are the documented exception: "A dropdown is more than a set of classes … These templates carry
  Bootstrap 5 dropdown markup … and are the ones to override when your framework builds dropdowns differently"
  (`theme.md`, "Templates that follow Bootstrap's DOM"). The Tabler theme app follows the recipe: registers
  library, icons, classes and assets in `ready()` and overrides eight templates
  (`tabler-test/crud_views_tabler/apps.py:14-29`, template list under `crud_views_tabler/templates/crud_views/`).
- Page chrome is the project's: `CRUD_VIEWS_EXTENDS` names the base template (`tabler-test/config/settings.py:158`),
  and that template maps the crud_views blocks onto the Tabler page while the navbar is an ordinary include of the
  project (`tabler-test/templates/crud_views_page.html`, `templates/layouts/app.html:5`).

### 2.8 What the two CSS frameworks can render

- Bootstrap 5.3 documents a single level of navbar dropdowns and does not mention submenus; its dropdown is "not
  … a true ARIA menu" and authors add `role`/`aria-*` themselves (navbar and dropdown pages, fetched 2026-11-02).
  Its JS closes every other open dropdown on any click outside that dropdown's own toggle or menu
  (`Dropdown.clearMenus`, `bootstrap.bundle.js` 5.3.3 `:3813-3841`), so a second-level toggle inside an open menu
  needs custom JS or hover CSS; `.dropend` exists only as a caret and placement rule (`bootstrap.css` 5.3.3,
  `.dropend .dropdown-toggle::after`, `.dropend .dropdown-menu[data-bs-popper]`).
- Tabler 1.6.1 styles sidebar dropdowns three levels deep: in `.navbar-vertical` the `.dropdown-menu` becomes
  `position: static` and `.dropdown-menu .dropdown-menu .dropdown-item` and
  `.dropdown-menu .dropdown-menu .dropdown-menu .dropdown-item` get increasing indents (`tabler.css`
  `:13938-13943` and the `.navbar-expand-*` variants at `:14049-14052`); its JS hides sibling sidebar dropdowns and
  handles the folded sidebar (`tabler.js` `:5973-5993`). The horizontal Tabler navbar in `tabler-test` has no
  dropdown at all today (`includes/navbar.html`).

So "nested structures possible, until what level?" has two answers: the data model can be unbounded (the ViewSet
tree already is), the renderer is bounded by the framework: 1 dropdown level in a Bootstrap horizontal navbar
without extra JS, 3 levels in a Tabler vertical sidebar, unbounded for a plain `<ul>` tree with collapse.

### 2.9 Precedents for the mechanics the nav needs

| Need | Existing precedent |
|---|---|
| Declarative objects validated at import | `ViewSet`, `ParentViewSet`, `BreadcrumbItem` are Pydantic models with validators (`viewset/__init__.py:47`, `parentviewset.py:13`, `breadcrumb.py:24-54`); `LazyStr` keeps `gettext_lazy` labels lazy (`src/crud_views/lib/lazy.py`) |
| Late URL resolution | `BreadcrumbItem(url_name=…, kwargs=…).resolve()` reverses at render time (`breadcrumb.py:48-54`) |
| Dotted-path hook from settings | `manage_view_class` resolved with `import_string` (`viewset/__init__.py:328-334`) |
| Registry filled from `AppConfig.ready()` | icons, button classes, assets (2.7) |
| Per-request memo | `cv_breadcrumb()` caches on the view instance (`breadcrumb.py:151-155`); its query count is pinned by `django_assert_num_queries(2)` then `(0)` (`tests/test1/test_breadcrumb.py:297-302`), the test shape a nav should copy |
| Settings read at call time, not snapshotted | `crud_views_settings` is an import-time singleton that `override_settings` cannot change (`settings.py:337`; tests monkeypatch it, `tests/test1/conftest.py:883-889`), while `_raw_label_mode_defaults()` deliberately reads its setting per call (`label_mode.py:56-60`; recorded as "no merged-map cache", `.planning/STATE.md:231`) |
| No Django cache anywhere | nothing in `src/` uses `django.core.cache`, `lru_cache` or `{% cache %}`; the test project configures no `CACHES` (`tests/test1/conftest.py:35-125`) |
| Per-process memo with a documented staleness rule | `ViewSet.default_permissions` (`viewset/__init__.py:437-470`, docstring: cached once non-empty, not refreshed) |
| Per-page chrome from a view mixin | `CrudViewBreadcrumbMixin.get_context_data` adds `cv_breadcrumb` (`breadcrumb.py:280-283`) |
| Global template context | `crud_views_context` context processor exposes `crud_views_settings.as_dict` (`src/crud_views/lib/context_processor.py`, `settings.py:327-335`) |
| Enumerating a ViewSet's views for display | `ManageView.get_view_data` (`manage.py:93-135`) |
| A hook that mutates view lists at registration | `register_view_class` appends `manage` to `cv_context_actions` when enabled (`viewset/__init__.py:321-326`) |
| System checks over the registry | `ViewSet.checks_all()` (`viewset/__init__.py:166-174`), `src/crud_views/checks.py` |

## 3. Decisions that are independent of the approach

These cut across every approach; each approach below only changes *where* the tree comes from.

### 3.1 What a nav item is

Four kinds cover the ask:

1. **ViewSet target**: `viewset="customer"`, `key="list"` (default). Label, icon, URL, access and active state
   are derived (2.2–2.5). A `key` other than `list`/`card` is allowed only for non-object views (`cv_object is
   False`, `base.py:70`), so `create` works, `detail` does not without an object.
2. **Plain URL target**: `url_name="dashboard:index"` (+ `args`/`kwargs`) or a literal `url`, with an optional
   `permission="auth.view_user"` → `user.has_perm` (the Tabler navbar's three non-crud items).
3. **Group**: a label and children, no link; hidden when no visible child remains (the overflow-menu rule "if
   every menu action is hidden, no toggle is rendered", `docs/reference/action_menus.md:267`).
4. **Provider**: a callable that returns items at render time (the "generic injection as submenu" hook, 3.4).

All four are Pydantic models like `BreadcrumbItem`, with `LazyStr` labels and an icon value in the registry's
format (`icons.py:186-211`).

### 3.2 Resolution context

Resolution needs `request` (user, `resolver_match` for active state and parent pks, language), and optionally the
current `view` and `object` when the nav is rendered from a crud page. That is exactly what the breadcrumb and the
context actions have, and what a dashboard page does not: the resolver must work with `view=None`.

### 3.3 Permission rule per item (the matrix)

| Item | Visible when | Grounding |
|---|---|---|
| ViewSet target, plain view | always | `base.py:353` |
| ViewSet target, `*PermissionRequired` | `cls.cv_has_access(user, None)` and `cls.cv_action_enabled(user, None)` | `base.py:926-930, 357-367` |
| ViewSet target, Guardian list | user authenticated and active (own rule, because `cv_has_access` is `True` for anonymous); optional `non_empty=True` probe via `viewset.get_objects_for_user(user, "view").exists()` | `mixins.py:118-131`, `viewset.py:122-142` |
| ViewSet target, Guardian child list under a parent object (tree nav) | the parent rule dispatch applies, `_guardian_user_has_parent_perm(user, parent_obj)`, made public | `mixins.py:303-323` |
| ViewSet target, Guardian object view (tree nav only) | `cls.cv_has_access(user, obj)` with a shared, prefetched checker | `mixins.py:79-92`, `guardian/core.py:194-215` |
| URL target with `permission` | `user.has_perm(permission)` (or `has_perms` for a list) | `models.py:384-411` |
| URL target without `permission` | always, or `login_required=True` for `is_authenticated` | — |
| Group | at least one visible child | `action_menus.md:267` |
| Any item with `groups=[...]` (decision 2b) | additionally, the user is in any listed group, or is an active superuser | `manage.py:38`, `templatetags/crud_views.py:495-502` |
| Any item | `inaccessible_actions`: hide (default) or render disabled, the same knob the buttons use | `base.py:263-270`, `settings.INACCESSIBLE_ACTIONS_VALUES` |

Every rule above is request-free except the Guardian probe, so the matrix costs two queries per request for the
whole nav (2.6) plus one query per opted-in Guardian probe.

### 3.4 The injection hook

Two grounded shapes:

- **Registry function**, `register_nav_provider(slot, provider)` from `AppConfig.ready()`, mirroring
  `register_assets(key, …)` (`assets.py:56-69`) and the icon/class registries. A provider is
  `callable(context) -> list[NavItem]`. Extension apps (guardian's manage pages, workflow) and projects inject the
  same way, order is `INSTALLED_APPS` order, and `setting_changed` resets apply.
- **Dotted path in settings**, `CRUD_VIEWS_NAV_PROVIDERS = {"main": ["myapp.nav.reports"]}`, resolved with
  `import_string` like `manage_view_class` (`viewset/__init__.py:328-334`). Simpler to read in one place; no
  `ready()` needed; but an extension app cannot contribute without the project listing it.

Both can coexist (the class table does exactly that: registry layer under a settings layer,
`button_classes.py:131-142`). A provider's items are cached under the same rules as static items; a provider that
hits the database is the project's cost and should say so in its docstring, as the breadcrumb does for ancestors
(`breadcrumb.py:208-210`).

### 3.5 Nesting depth

- Data: unbounded tree (groups in groups, provider items with children).
- Renderer: a `max_depth` per nav template; deeper levels are flattened into the last allowed level with
  `dropdown-header` rows in Bootstrap (its own class), or rendered as nested `<ul>` in a sidebar/tree template.
- Check: a `W`-level system check when a static tree is deeper than the renderer's documented depth, in the style
  of the W362 key checks (`button_classes.py:250`).
- ViewSet nesting is not nav nesting: a child ViewSet's `list` cannot be a static item (2.3). It appears either as
  a child of an object node in a tree nav or as a contextual item when the request already carries the parent pk.

### 3.6 Active state

`request.resolver_match.view_name == viewset.get_router_name(key)` for exact; "ancestor active" when the
resolved view's ViewSet, or any ViewSet up its `parent` chain, is the item's ViewSet. Rendered as `active` plus
`aria-current="page"` like the breadcrumb does (`src/crud_views/templates/crud_views/tags/breadcrumb.html:6`).

### 3.7 One nav or many

Named nav *instances* rather than one nav: `{% cv_nav "main" %}` and `{% cv_nav "sidebar" %}` render different
trees with different templates on the same page; a tree nav is a third instance whose provider takes the page's
`object`. The Tabler layout has two obvious slots already: the header include and the `page-header` column
(`templates/layouts/app.html:5-19`). Per-request memoisation keyed by nav name (3.8) keeps a second render of the
same tree free.

### 3.8 Caching: the options

| # | Option | What is cached, keyed by | Invalidation | Pros | Cons |
|---|---|---|---|---|---|
| C0 | Nothing beyond Django's own | `request.user._perm_cache` (2.6); `get_resolver` lru (2.2) | per request | always correct; two queries per request for any number of plain/crud-views items; zero new code | each render re-walks the tree, re-renders labels, re-reverses URLs; Guardian probes cost one query each, every time |
| C1 | Per-request memo | resolved item list per `(nav name, object pk)` on `request` (attribute, like `_cv_breadcrumb_cache` on the view) | end of request | a global nav and a tree nav, or a nav rendered in two blocks, cost one resolution; safe with user switching | nothing across requests |
| C2 | Per-process tree shape | the *static* tree: validated items, ViewSet/view class refs, router names, lazy labels; built lazily on first render (after the URLconf), reset on `setting_changed` like `icons.py:112-123`; the setting itself read per call like `_raw_label_mode_defaults`, not through the import-time singleton (2.9) | process restart or settings change | validation and `get_viewset` lookups happen once; cheap; thread-safe with a lock like `_REGISTRY_LOCK`; testable with `override_settings` | must keep labels lazy (`LazyStr`) and never store a reversed URL that depends on request kwargs; provider items are excluded by definition |
| C3 | Per-user resolved tree in Django's cache | `cache.get_or_set(key, resolve, timeout)` keyed by nav name, `user.pk`, language, and a permission version | TTL, plus explicit bumps: `m2m_changed` on `User.user_permissions`, `User.groups`, `Group.permissions`; guardian `UserObjectPermission`/`GroupObjectPermission` saves for probes; `user_logged_in` | removes the two permission queries and all Guardian probes; works across requests and workers with a shared cache | stale visibility until TTL or signal; signal coverage is never complete (direct SQL, custom backends, `is_active` flips); needs `CACHES`, which nothing in the package uses today and the test project does not configure (2.9); active state must not be part of the cached value (it is per page) |
| C4 | Rendered HTML fragment, `{% cache %}` | `make_template_fragment_key("cv_nav_main", [user.pk, LANGUAGE_CODE])` (`django/core/cache/utils.py`, docs "Template fragment caching") | TTL or `cache.delete(key)` | the cheapest possible render; standard Django, no new code | active state is baked in, so the key must include the current `view_name` (one copy per page per user, low hit rate) or the active class must be set client-side by matching `href` against `location.pathname`; theme markup is frozen into the cache; inner tags that read `request` stop being per-request |
| C5 | Session | resolved visibility per nav in `request.session` (precedent: `src/crud_views/lib/session.py` keeps per-view UI state) | on login/logout, TTL | no shared cache needed | stale on permission changes; grows the session; wrong for per-object tree navs |
| C6 | Guardian-specific | one `ObjectPermissionChecker` per render with `prefetch_perms(queryset)`; `get_objects_for_user(...).exists()` only when `non_empty=True` | per render | turns N object checks into one query | only helps tree navs over objects; the global `GUARDIAN_AUTO_PREFETCH` setting is a project decision |

Recommendation independent of approach: ship **C1 + C2 + C6** as the default (correct by construction, two
queries per request for any number of plain/crud-views items, one per opted-in Guardian probe), and offer **C3**
as an opt-in (`CRUD_VIEWS_NAV_CACHE = {"timeout": 300}` plus the documented signal set), with the explicit
statement that a cached nav may show a stale item for up to `timeout` seconds and that the request gates still
apply. C4 is a project-level choice we should document rather than build (the active-state problem makes it a
poor default). C5 adds a second place where authorization state lives, which the stability work has been removing
(`.planning/PROJECT.md`, Phase 6.2 "request authorization"); I would not offer it.

### 3.9 Theming contract

- **Leaves**: `crud_views/tags/nav/item.html` (a link), `nav/group.html` (a toggle with children),
  `nav/container.html` (the `<ul>`), each receiving a flat `cv_nav_*` dict the way buttons receive
  `cv_button_data` (`src/crud_views/lib/view/button_data.py`): `cv_label`, `cv_url`, `cv_icon`, `cv_icon_class`,
  `cv_active`, `cv_active_ancestor`, `cv_depth`, `cv_disabled`, `cv_children`, `cv_key`, `cv_viewset`.
- **Logic template** `tags/nav.html` recurses over children and is not to be copied, like
  `tags/context_action.html`.
- **Class table keys** under a new `nav` location: `nav:container`, `nav:item`, `nav:item:active`, `nav:link`,
  `nav:link:active`, `nav:group-toggle`, `nav:menu`, `nav:menu-item`, `nav:icon-host`, `nav:hidden-label`. They
  must be in `DEFAULT_BUTTON_CLASSES` (W362, 2.7) and `nav` must join `LOCATIONS` and `LABEL_MODE_DEFAULTS`
  (2.7). Themes register them from `ready()`; projects override per key (`button_classes.py:125-142`). Tabler's
  values are known from its navbar: `nav-item`, `nav-link`, `nav-link-icon`, `nav-link-title`, and `active` on
  the `<li>` rather than on the link, which is why both an item and a link active slot are needed
  (`includes/navbar.html:13-17`; Bootstrap's own navbar puts `active` on `.nav-link`, and the example project
  follows Bootstrap, `project/nav.html:17, 24`).
- **The dropdown exception, again**: the group leaf carries Bootstrap `data-bs-toggle="dropdown"` markup in core;
  it joins the documented list of "templates that follow Bootstrap's DOM" (`theme.md`), and the Tabler theme
  overrides it for the sidebar (where Tabler keeps `data-bs-toggle="dropdown"` but static positioning,
  `tabler.css:13920-13943`).
- **Label modes and icons** reuse `LABEL_MODES` (`src/crud_views/lib/view/label_mode.py`) and the icon registry,
  so a folded Tabler sidebar (`navbar-folded`, `tabler.css:13846+`) is `icon` mode.
- **Accessibility**: `aria-current="page"` on the active link, `aria-expanded` on group toggles, and no
  `role="menu"` (Bootstrap's own guidance, 2.8).

### 3.10 Checks, docs and the planning process

- **Check IDs.** Per-ViewSet/view `Check` objects use the `viewset.*` namespace; `W270` (breadcrumb) is the only
  occupant of the 27x block, so `viewset.E271–E279` / `W271–W279` are free and adjacent. Global `@register`
  functions use `crud_views.*`, where `E370–E399` is free (the ranges in use end at `E36x`/`W362`,
  `button_classes.py:250-321`). No document lists the scheme; this is read from the code.
- **Docs placement.** `docs/reference/.pages:26-32` already has an "Actions & navigation" group (action_enabled,
  inaccessible_actions, action_view, context_buttons, breadcrumb, modals); a `navigation.md` belongs there, and
  the base-template table in `docs/reference/templates.md:7-17` gains `{% cv_nav %}` next to `cv_breadcrumb`.
- **Process.** The GSD milestone's core value is that every public theme name settles once before 1.0.0
  (`.planning/PROJECT.md`, "Core Value") and Phase 7 "must remain last" (`.planning/ROADMAP.md`). Phase 7's guard
  test is derived from `DEFAULT_ICONS`, `DEFAULT_BUTTON_CLASSES`, `LEAF_KEYS`, `LOCATIONS`, the leaf files on
  disk and the JS adapter keys (`ROADMAP.md:558-560`), so nav icons, keys, a location and leaves are pulled into
  the freeze automatically the moment they exist. A navigation phase is therefore either an inserted `6.x` phase
  before Phase 7 with `NAV-xx` requirements and traceability rows in `.planning/REQUIREMENTS.md`, or the first
  phase of the next milestone after 1.0.0. The phase shape to copy is `phases/03-filter-toggle-label-mode/`
  (CONTEXT → RESEARCH → PATTERNS → PLANs → SUMMARYs → REVIEW/SECURITY/VALIDATION/VERIFICATION/UAT).

## 4. The approaches

### Approach A: declared tree, resolved by the package ("nav is data")

The project (or a theme, or an extension app) declares the tree. Items are Pydantic models; ViewSet targets are
referenced by name and resolved lazily; providers plug in by slot.

```python
# settings.py or myproject/nav.py
from crud_views.lib.nav import Nav, NavItem, NavGroup, NavProvider

CRUD_VIEWS_NAVS = {
    "main": Nav(items=[
        NavItem(label=_("Dashboard"), icon="dashboard", url_name="dashboard:index"),
        NavItem(viewset="customer"),                       # label, icon, url, access, active: derived
        NavItem(viewset="product"),
        NavGroup(label=_("Admin"), icon="settings", groups=["admins"], items=[
            NavItem(label=_("Users"), url_name="dashboard:users", permission="auth.view_user"),
            NavProvider("crud_views.nav.manage_pages"),  # one item per ViewSet with a manage view
        ]),
    ]),
}
```

```django
{% load crud_views %}
{% cv_nav "main" %}                 {# header #}
{% cv_nav "tree" object=object %}   {# a tree nav fed by a provider that takes the page object #}
```

Resolution: `Nav.resolve(context) -> list[ResolvedItem]` applies the matrix of 3.3, the active rule of 3.6 and
C1/C2 caching; `{% cv_nav %}` is an inclusion tag on `crud_views/tags/nav.html` which recurses into the leaves.
Checks: unknown ViewSet name (`ViewSetNotFoundError`), object-view key without an object, tree deeper than the
renderer, unknown provider path; registered next to the existing ones in `crud_views/checks.py`.

| Aspect | Pro | Con |
|---|---|---|
| Nav items point at crud views | one line per ViewSet; everything derived from the registry (2.2–2.5) | a child ViewSet still cannot be a static item (2.3); needs the tree/provider path |
| Nesting | unbounded tree, bounded by renderer `max_depth` with a check | depth semantics differ per theme; docs must state the per-template depth |
| crud-views / guardian / Django permissions | the matrix of 3.3 is applied once, in one resolver, with the same `cv_has_access` the toolbar uses | Guardian list targets need the extra "authenticated" rule and an opt-in probe; this is a new rule to document, not an existing one |
| Injection hook | first-class `NavProvider` items, either registry or dotted path (3.4) | providers cannot be validated statically; checks can only verify importability |
| Speed | C1/C2 by default; C3 opt-in; the static tree is validated once | per-request resolution still walks every item; a 200-item nav is 200 `reverse()` calls unless C3 |
| Themable | leaf/logic split, class keys, dropdown exception: exactly the button recipe (3.9) | a second recursive logic template to keep in sync with the overflow menu's |
| Global and multiple navs | named instances, any number per page, tree navs through providers with `object` | the project has to declare each nav; nothing appears by itself |
| Fit with the codebase | Pydantic + lazy resolution + registry + checks: all precedents exist (2.9) | the largest surface of the three approaches (new settings, new tags, new leaves, new checks) right before the 1.0 freeze (`.planning/ROADMAP.md`, Phase 7) |

### Approach B: ViewSet-derived nav ("nav is metadata on the ViewSet")

No separate tree. A ViewSet declares where it lives in the navigation; the package derives the tree from the
registry at first render, the way `checks_all()` and the manage page already enumerate it.

```python
cv_customer = ViewSet(model=Customer, name="customer", icon_header="tabler:building-store",
                      nav=NavMeta(group="sales", order=10, label=_("Customers")))
cv_book = ViewSet(model=Book, name="book", parent=ParentViewSet(name="publisher"))  # no nav: child, appears under its parent's objects only
```

```python
CRUD_VIEWS_NAV_GROUPS = [NavGroup(key="sales", label=_("Sales"), icon="cart", order=10), ...]
CRUD_VIEWS_NAV_EXTRA = {"sales": ["myapp.nav.reports"]}   # provider hook per group
```

Non-crud pages (dashboard, users) are the leftover: they need either a `NavItem` list in settings anyway, or the
project writes them by hand around `{% cv_nav %}`. Nested ViewSets become nested nav automatically only in a
tree nav: under a `publisher` object node, the resolver lists the child ViewSets whose `parent.name` is
`publisher` (the inverse of `cv_get_child_url`'s check at `base.py:832-833`) and reverses their `list` with the
object's pk (`base.py:839-845`).

| Aspect | Pro | Con |
|---|---|---|
| Nav items point at crud views | every registered ViewSet with `nav=` is in the menu, in registry order (`OrderedDict`) with `order` to override; zero duplication between URLconf and nav | the nav is only as complete as the ViewSets: dashboards and non-crud pages are second-class |
| Nesting | one level (group → ViewSet) statically; the ViewSet parent chain gives object trees for free | no arbitrary groups in groups without adding a parent key to `NavGroup`, which recreates approach A's tree |
| Permissions | identical to A (same resolver) | identical to A |
| Injection hook | per-group provider list | a provider cannot create a group; groups are settings |
| Speed | the static tree is derived once from `_REGISTRY` (C2 is natural: it already is a process-level registry) | identical per-request cost to A |
| Themable | identical to A | identical to A |
| Global and multiple navs | one global nav falls out of the registry; tree navs from the parent chain | a second, differently shaped global nav (e.g. a settings sidebar) has nowhere to live |
| Fit with the codebase | smallest declaration surface; follows `context_buttons`/`icon_header` which already sit on the ViewSet (`viewset/__init__.py:74-80`) | a new public ViewSet field before the freeze; `ViewSet` is a Pydantic model, so `nav=` must be validated with lazy group lookup (groups are settings, read at validation time: order of evaluation problem); needs a public registry iterator first, since `_REGISTRY` is private (2.2) |

### Approach C: primitives only ("bring your own markup")

The package answers the four questions per target, and the theme or project keeps writing the navbar it writes
today. Tags:

```django
{% load crud_views %}
{% cv_nav_access "customer" as can_customers %}            {# matrix of 3.3 for the list view #}
{% cv_nav_url "customer" as customers_url %}               {# reverse(get_router_name("list")) #}
{% cv_nav_active "customer" as customers_active %}         {# exact or ancestor, 3.6 #}
{% cv_nav_label "customer" as customers_label %}           {# verbose_name_plural or cv_nav_label #}
{% if can_customers %}
<li class="nav-item{% if customers_active %} active{% endif %}">
  <a class="nav-link" href="{{ customers_url }}"{% if customers_active %} aria-current="page"{% endif %}>
    <span class="nav-link-icon">{% cv_icon "customer"|cv_viewset_icon %}</span>
    <span class="nav-link-title">{{ customers_label }}</span>
  </a>
</li>
{% endif %}
```

or one combined `{% cv_nav_target "customer" as t %}` returning `{url, access, active, label, icon}`.

| Aspect | Pro | Con |
|---|---|---|
| Nav items point at crud views | exactly what `tabler-test/templates/includes/navbar.html` needs to stop hard-coding `perms.customers.view_customer` and `customer-list`; replaces four lines with one tag | nothing enumerates; the project still lists every target |
| Nesting | whatever the markup author writes | the package offers no tree, no depth rule, no checks |
| Permissions | the same matrix, exposed per target | easy to forget the tag and fall back to `perms`, so inconsistency with the toolbar creeps back |
| Injection hook | none in the package; a project tag can call a provider | the "generic injection" requirement is not met |
| Speed | nothing to cache beyond C0; each tag is a dict lookup plus one `reverse()` | no C1 memo across tags unless they share one per-request resolver |
| Themable | trivially: the theme owns all markup; no leaf contract to freeze before 1.0 | no shared rendering means no shared accessibility and no class-table integration |
| Global and multiple navs | any number, any shape | all by hand |
| Fit with the codebase | smallest change; precedent in `cv_context_url`/`cv_context_has_permission` (`templatetags/crud_views.py:276-286, 467-473`), which do this for sibling views | does not deliver a "navigation component", only ingredients |

### Approach D (variant worth naming): view-mixin tree nav

For the per-page tree ("a tree like nav additionally on certain pages"), the breadcrumb pattern is the direct
precedent: a `CrudViewNavTreeMixin` with `cv_nav_tree(self) -> list[NavItem]`, cached on the view like
`cv_breadcrumb()` (`breadcrumb.py:151-155`), added to the context in `get_context_data` (`:280-283`), rendered by
`{% cv_nav_tree %}`. The default implementation lists the child ViewSets of the view's ViewSet under the current
object (B's parent-chain walk) and applies the matrix of 3.3 with one prefetched Guardian checker (C6). It has
`self.kwargs`, so child `list` URLs are reversible (2.3), and it has `self.object`, so Guardian object views can
be linked. Pro: it needs no global nav at all and composes with A, B or C for the header. Con: it is per-view
opt-in, like the breadcrumb, so it cannot be the global nav.

## 5. Comparison at a glance

| Requirement | A: declared tree | B: ViewSet metadata | C: primitives | D: view-mixin tree |
|---|---|---|---|---|
| Items point at crud views | yes, by name | yes, by declaration on the ViewSet | yes, per tag | children of the current object |
| Nested, depth | unbounded data, renderer-bounded | 1 static level + object trees | author's choice | ViewSet parent chain |
| crud-views permissions | `cv_has_access` + `cv_action_enabled` | same | same | same, with object |
| guardian permissions | authenticated rule + optional probe | same | same | object checker, prefetched |
| Django permissions | `permission=` on URL items | needs URL items from A anyway | `permission` arg | n/a |
| Injection hook | `NavProvider` (registry or dotted) | per-group providers | none | override `cv_nav_tree` |
| Fast | C1+C2 default, C3 opt-in | same | C0 | per-view cache like breadcrumb |
| Themable via templates | leaves + class keys + dropdown exception | same | theme owns markup | leaves |
| Global + multiple navs | named instances | one global + object trees | any | per page only |
| New public surface before 1.0 | large | medium (a ViewSet field) | small | small |

## 6. Recommendation

Build it in two layers, in this order:

1. **The resolver and the primitives (C) first.** One request-free function per target: access (the matrix of
   3.3), URL, active state, label, icon. Expose them as tags. This alone lets `tabler-test`'s navbar and the
   example project's `features.py` drop their hand-written permission and URL logic, and it fixes the two
   inconsistencies found in 2.4 and 2.5 (namespace-blind active check; Guardian list targets visible to anonymous
   users) in one place.
2. **The declared tree (A) on top**, with named instances, providers, the leaf contract and C1/C2 caching, C3
   opt-in. B's `nav=` ViewSet field can be added later as sugar that *generates* A items; it is not needed for
   either requirement and it is the one option that touches `ViewSet`'s public signature before the freeze.
3. **D for the tree nav**, as a mixin that produces A items from the current object; the same leaves render it.

Why not B as the primary: it cannot express the non-crud items every real navbar has (both consumers have them:
dashboard, users, admin), it needs settings-time group lookups inside a Pydantic validator, and it adds a field to
the one class whose surface Phase 7 is about to freeze.

## 7. Decisions (2026-11-02)

Taken with the maintainer after this exploration; they bind the design that follows.

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | Where does the tree live? | **Registry plus setting.** Apps and themes register items from `AppConfig.ready()`; the project's `CRUD_VIEWS_NAVS` layers on top and wins per key, as the class table, icons and assets do (`button_classes.py:131-142`). | Only a registry lets an extension app or a reusable Tabler theme contribute a menu entry without the project listing it; it is also the shape every other theme hook already has. |
| 2 | Guardian list targets | **Signed-in and active is enough** by default, matching today's `cv_has_access` (`mixins.py:130-131`); anonymous users never see guardian items. "Hide when the user can see no object" is a per-item opt-in (`non_empty=True`, one query per item through `GuardianViewSet.get_objects_for_user`). | Zero queries by default and the same rule as the toolbar's `list` button; the probe stays available where a narrow grant makes an empty table confusing. |
| 2b | Group membership as a gate | **Added.** Any item, node or leaf, may carry `groups=[...]`: visible when the user is in **any** of them; **active superusers bypass** it, mirroring `has_perm` (`django/contrib/auth/models.py:393`); it is an extra **AND** on top of the permission rule, never a replacement. Costs one memoised query per request for the user's group names. Unknown group names cannot be checked at startup; strict mode logs them once at first render. | Precedent: the manage view gates on `CRUD_VIEWS_MANAGE_GROUP` (`manage.py:38`) and `cv_user_in_group` exists (`templatetags/crud_views.py:495-502`). A node gate carves role-based sections cheaply. |
| 3 | Cross-request cache | **Opt-in, default off.** C1 (per-request memo) and C2 (process-level static tree) are the default speed story; C3 ships behind a setting with the staleness window and the signal set documented. C4/C5 are not built. | Phases 6.2–6.4 tightened authorization; a stale menu by default would undo part of that. The request gates stay in force either way. |
| 4 | Depth promise | **Two stock templates, no new adapter.** `nav/navbar.html` renders one dropdown level (Bootstrap's documented limit, 2.8); `nav/sidebar.html` renders unbounded nested lists with collapse. A warning check fires for a tree deeper than its template. The Tabler theme overrides the group leaf and gets its three sidebar levels. | Bootstrap's dropdown JS closes sibling menus (2.8); collapse does not. A `cv.adapters.nav` entry stays possible later because only the group leaf would call it. |
| 5 | Timing with 1.0 | **After 1.0, provisional at first.** The policy reserves deprecation for changing or removing a listed name (`stability.md:7-17, 87-93`); adding names in a minor release is ordinary. The nav surface is listed as provisional under Phase 7's tiering and promoted to stable once two consumers (core, Tabler) have rendered it. | Freezing a first-version leaf contract that no downstream has consumed would repeat the button leaf's early churn without the rounds that settled it. |
| 6 | The two `cv_has_access` gaps | **Fix both first, as a prerequisite of the navigation work**, in the existing link path (toolbar and cards included): a missing permission row returns `False` (`base.py:926-930`), and the Guardian child list's `cv_has_access` applies the parent rule when a parent object is given, which means making `_guardian_user_has_parent_perm` public (`mixins.py:303-323`). | The nav would otherwise inherit and spread both; the second fix is also the rule the tree nav needs. |

What the decisions change in the sections above: the item model (3.1) gains `groups`; the permission matrix
(3.3) gains the group row and keeps the guardian default; the hook (3.4) is the two-layer shape; caching (3.8) is
C1 + C2 + C6 by default with C3 opt-in; theming (3.9) ships `navbar` and `sidebar` templates; the process (3.10)
is a post-1.0 phase preceded by a small fix phase for the two gaps. The recommended order in section 6 stands:
primitives and resolver, then the declared tree, then the view-mixin tree nav; the ViewSet `nav=` field remains
optional sugar.

## 8. Next step

The two fixes of decision 6 come first, each with a test that pins the link and the request to the same answer.
Then a design doc for the navigation itself (`superpowers/specs/`) that carries the decisions above into the
item model, the resolver API, the leaf contract and the check IDs, followed by a plan.
