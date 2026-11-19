## 06.40-01

### 1. Summary
Plan `06.40-01` establishes the core `src/crud_views/lib/navbar.py` module (`NavBar`, `NavItem`, `CrudViewNavBarMixin`), the `{% cv_navbar %}` template tag in `src/crud_views/templatetags/crud_views.py`, the initial layout-B wrapper template (`src/crud_views/templates/crud_views/tags/navbar.html`), and focused routing and system-check test suites (`tests/test1/test_navbar.py` and `tests/test1/test_navbar_checks.py`). The plan is well-scoped and accurately accounts for existing `ViewSet` key lookup fallbacks, request-resolved ancestor state, and cooperative system checks, with minor gaps around `NavBar.template` check validation and `NavItem` construction invariants.

### 2. Strengths
- **Preserves `CrudView` (`src/crud_views/lib/view/base.py:302-320`) and avoids eager ancestor queries**: Unlike `CrudViewBreadcrumbMixin.get_context_data` (`src/crud_views/lib/breadcrumb.py:280-283`), which eagerly calls `self.cv_breadcrumb()` and executes one `.get(pk=ancestor_pk)` query per ancestor in `_cv_breadcrumb_ancestors` (`src/crud_views/lib/breadcrumb.py:244`), Task 01 and Task 02 store an unevaluated `SimpleLazyObject` (precedent in `src/crud_views/lib/views/manage.py:1017-1019`) and resolve descendant owners via `_resolved_ancestor(view, owner_name)` (`src/crud_views/lib/ancestors.py:576-585`), which reads `view._cv_ancestor_state` already populated by `_authorize_ancestors` (`src/crud_views/lib/ancestors.py:464-567`).
- **Explicit literal-key guard defeats the `"list" -> "card"` lookup alias**: Both `ViewSet.get_view_class` (`src/crud_views/lib/viewset/__init__.py:375-379`) and `ViewSet.get_router_name` (`src/crud_views/lib/viewset/__init__.py:381-388`) silently rewrite `"list"` to `"card"` when `"list"` is unregistered and `"card"` is registered. Task 02 checks `viewset.is_view_registered(key)` (`src/crud_views/lib/viewset/__init__.py:372-373`) before calling either method on explicit keys, restricting the `"list" -> "card"` fallback exclusively to omitted child keys (`NavItem(child="...", key=None)`).
- **Target-topology URL reversal works at any descendant depth**: `CrudView.cv_get_child_url` (`src/crud_views/lib/view/base.py:1126-1146`) raises `ParentViewSetError` (`src/crud_views/lib/view/base.py:1131-1132`) unless `viewset.parent.name == self.cv_viewset.name`. Task 02 instead reverses `owner_viewset.get_router_name(key)` / `child_viewset.get_router_name(key)` using `owner_viewset.get_parent_url_args()` (`src/crud_views/lib/viewset/__init__.py:295-303`) and `owner_viewset.pk_name` (`src/crud_views/lib/viewset/__init__.py:79`) or `child_viewset.parent.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-60`).
- **Two-part GET eligibility check catches `ActionView`**: `ActionView` (`src/crud_views/lib/views/action.py:12-23`) inherits `django.views.generic.View.http_method_names` (which includes `"get"`) while defining only `def post(...)`. Task 03 checks both `"get" in target.http_method_names` and `callable(getattr(target, "get", None))`.
- **Registry and vocabulary cache isolation in dynamic tests**: Referencing `isolated_routes` (`tests/test1/test_ancestor_authorization.py:46-76`) ensures `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:47`), `check._VOCAB_CACHE` (`src/crud_views/lib/check.py:341-365`, keyed by `len(classes)`), URL resolver caches, and `ContentType` caches are snapshotted and restored.

### 3. Concerns
- **[MEDIUM] Missing `CheckTemplate` (`E111`) coverage for `NavBar(template=...)` (`src/crud_views/lib/check.py:232-253`)**:
  - `CrudView.checks()` (`src/crud_views/lib/view/base.py:200`), `ViewSet.checks()` (`src/crud_views/lib/viewset/__init__.py:246`), and `CrudViewBreadcrumbMixin.checks()` (`src/crud_views/lib/breadcrumb.py:106`) all validate optional template paths at startup using `CheckTemplate` (`src/crud_views/lib/check.py:232-253`). Task 03 enumerates the A-04 target/attachment checks on `cv_navbar` but does not specify whether a non-existent `NavBar(template="missing.html")` is validated at startup or left to fail at render time with `TemplateDoesNotExist`.
- **[MEDIUM] Ambiguity in `NavItem` mutual-exclusivity validation (`key` vs `child`)**:
  - Under D-04 (`06.40-ISSUE-381.md:127-146`), an owner item has `child=None` and requires `key`, whereas a child item has `child="<viewset>"` and optional `key`. Task 01 and Task 03 do not state whether `NavItem(key=None, child=None)` (neither set) or `NavBar(viewset="...", items=[])` (empty items) is rejected by a Pydantic `@model_validator` at construction or by the cooperative startup check in Task 03. If rejected by Pydantic at import time, startup check tests in `test_navbar_checks.py` cannot construct that invalid `NavItem` unless they test `ValidationError` or the check validates it at startup.
- **[LOW] `ManageView` and `cv_config` interaction with `cv_navbar` (`src/crud_views/lib/views/manage.py:664-766`, `src/crud_views/lib/manage_report.py:97-164`)**:
  - Because `CrudViewNavBarMixin` lives under `crud_views.*` and declares `cv_navbar`, `_collect_cv_names` (`src/crud_views/lib/check.py:297-307`) and `ManageView._manage_view_sections` (`src/crud_views/lib/views/manage.py:664-721`) will automatically include `cv_navbar` in the `"other"` section of participating views. Since `ManageView._manage_owned_projection` (`src/crud_views/lib/views/manage.py:728-762`) only projects `ParentViewSet` and `ContextButton` subclasses, `normalize_value` (`src/crud_views/lib/manage_report.py:97-164`) will classify a `NavBar` instance as `ValueRecord(kind="unsupported", python_type="crud_views.lib.navbar.NavBar")` for JSON export and `repr(value)` (`src/crud_views/lib/views/manage.py:851`) for HTML display. This is safe and bounded, but `NavBar` should keep a clean deterministic representation.

### 4. Suggestions
- Explicitly decide and document in Task 01 / Task 03 whether `NavItem(key=None, child=None)` is a Pydantic `ValidationError` at construction or a startup `Check` error in `CrudViewNavBarMixin.checks()`.
- Include a startup template existence check (or `CheckTemplate`-equivalent check) when `NavBar.template` is a non-empty string, or explicitly document that `NavBar.template` is resolved at render time.

### 5. Risk Assessment
**LOW** — All core hooks (`_resolved_ancestor`, `_walk_ancestors`, `is_view_registered`, `get_parent_url_args`, `Check`) already exist and are verified in `src/crud_views/lib/`.

---

## 06.40-02

### 1. Summary
Plan `06.40-02` extracts the identity (`navbar_identity.html`) and items (`navbar_items.html`) leaf partials from `navbar.html`, locks down the public template context (`cv_navbar.object`, `label`, `icon`, `items`; `item.label`, `icon`, `url`, `active`), and tests global overrides, split placement, per-bar templates, modal/omitted zero-work guarantees, SafeString escaping, and accessible markup in `tests/test1/test_navbar_templates.py`. The plan is well-aligned with D-08, D-10, D-11, and D-16, with two technical subtleties in `SafeString` escaping and icon rendering that need careful handling during implementation.

### 2. Strengths
- **Independent leaf guards and self-contained landmark**: Having `navbar_items.html` own `<nav aria-label="...">` with translated `Sections for %(object)s` derived from `cv_navbar.label` (`06.40-UI-SPEC.md:145, 186-187`) avoids cross-partial `aria-labelledby` DOM ID coupling when projects use split placement or override only `navbar_identity.html`.
- **`aria-current="true"` avoids semantic conflict with `aria-current="page"`**: On descendant pages (e.g., `ItemUpdateView`), the active `Orders` link targets the `Order` collection URL rather than the current `Item` page URL. Using `aria-current="true"` (`06.40-UI-SPEC.md:152-156`) accurately represents section state and avoids colliding with the example suite's top-navbar check `nav.count('aria-current="page"') == 1` (`examples/bootstrap5/project/tests.py:544`).
- **Avoids adding a global CSS bundle entry in `CrudViewsSettings.css` (`src/crud_views/lib/settings.py:354-363`)**: Because `core_bundle()` (`src/crud_views/lib/assets.py:88-96`) emits every entry in `crud_views_settings.css` via `{% cv_css %}` (`src/crud_views/templatetags/crud_views.py:67-70`), adding a new stylesheet to `CrudViewsSettings.css` would alter `<head>` HTML on nonparticipating pages and violate AC5. Using scoped Bootstrap utilities (`nav`, `nav-pills`, `flex-wrap`, `mw-100`, `text-break`) inside the navbar templates preserves byte-identical output on pages without a navbar.

### 3. Concerns
- **[HIGH] `SafeString` stripping vs. double-escaping on `cv_get_action_short_label` (`src/crud_views/lib/view/base.py:578-592, 638-643`)**:
  - In Django (`django/utils/safestring.py`), calling `str(val)` on a `SafeString` returns the `SafeString` itself (preserving `SafeData`). Furthermore, for owner items without an explicit `label=` override, the default label comes from `target.cv_get_action_short_label(context=context)` (`src/crud_views/lib/view/base.py:638-643`), which calls `cls.render_snippet(...)` (`src/crud_views/lib/view/base.py:578-592`). `render_snippet` renders a Django template (`crud_views/snippets/action_short/*.html`) with autoescaping and wraps the output in `mark_safe(result.strip())` (`src/crud_views/lib/view/base.py:592`).
  - If the navbar template applies `|force_escape` to `{{ item.label }}` (or if the builder calls `django.utils.html.escape` and the template autoescapes again), any character already escaped by `render_snippet` in `cv_get_action_short_label` (such as `&amp;` or `&#x27;`) will be **double-escaped** to `&amp;amp;` or `&amp;#x27;`.
  - Conversely, if `str(owner)` on a model or a user-supplied `NavItem(label=mark_safe("<script>"))` returns a `SafeString` and is NOT stripped to a plain Python `str` (`str.__str__(val)`), normal Django template autoescaping will let raw HTML through.
- **[MEDIUM] Host-placed icon rendering without a `navbar:icon-host` key in `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/icons.py:229-231` vs `src/crud_views/lib/button_classes.py:246-250`)**:
  - Task 02 states: "owner icon is decorative via existing renderer, including supported host/element icon placement and empty-string suppression."
  - In `src/crud_views/lib/button_classes.py:129-133`, `*:icon-host` keys exist only for `context`, `list`, `card`, `menu`, `form`, and `heading` (`src/crud_views/lib/button_classes.py:25`), and A-05 (`06.40-ISSUE-381.md:384-386`) forbids adding new keys to `DEFAULT_BUTTON_CLASSES`. Calling `{% cv_icon_class ... "navbar" %}` (`src/crud_views/templatetags/crud_views.py:658-661`) would look up `"navbar:icon-host"`, get `""`, and drop host icons.
  - Instead, calling `{% cv_icon ... %}` (`src/crud_views/templatetags/crud_views.py:652-655` -> `render_icon` in `src/crud_views/lib/icons.py:221-254`) handles `placement: "host"` libraries automatically via `font_renderer` lines `229-231` (`classes = config.get("standalone", "{name_class}").format(name_class=classes)`).
- **[MEDIUM] Unbroken 80-character token wrapping inside flex items (`<li class="nav-item">`)**:
  - In CSS Flexbox (`.nav` sets `display: flex`), flex items (`<li class="nav-item">`) default to `min-width: auto`. Putting `.text-break` only on `<a class="nav-link">` or `<span>` without `mw-100` (or `min-width: 0`) on BOTH `<li class="nav-item mw-100">` and `<a class="nav-link mw-100 text-break">` allows the `<li>` flex item to expand past the 320px viewport width when given an 80-character unbroken token in Plan 08 Task 01.
- **[LOW] Unevaluated `SimpleLazyObject` copying (`django/utils/functional.py`)**:
  - Task 01 notes: "only add a private cached-build sentinel if a real copy path requires it." Caching the built result on `self._cv_navbar_cache` inside the builder method (3 lines, identical to `CrudViewBreadcrumbMixin.cv_breadcrumb` in `src/crud_views/lib/breadcrumb.py:151-155`) unconditionally prevents duplicate builds even if `SimpleLazyObject` is shallow-copied before first evaluation.

### 4. Suggestions
- In `src/crud_views/lib/navbar.py`, strip `SafeData` to a plain `str` on `owner` captions and `NavItem.label` overrides via `str.__str__(str(value))` so standard template autoescaping escapes them exactly once (including inside `<nav aria-label="...">`), and test an action short label containing `&` or `'` to ensure it is not double-escaped.
- Use `{% cv_icon cv_navbar.icon %}` and `{% cv_icon item.icon %}` in the templates (which already support `placement="host"` via `standalone` in `src/crud_views/lib/icons.py:229-231`), rather than `cv_icon_class`.
- Place `mw-100` on `<li class="nav-item mw-100">` as well as `mw-100 text-break` on `<a class="nav-link ...">` and the identity caption element.
- Unconditionally memoize the builder result on `self` (e.g., `self._cv_navbar_data` with an `_UNSET` sentinel) in addition to wrapping it in `SimpleLazyObject`.

### 5. Risk Assessment
**MEDIUM** — `SafeString` handling across `str(owner)`, `NavItem(label=...)`, and `cv_get_action_short_label()` (`mark_safe` from `render_snippet`) can easily cause either XSS (if `SafeString` is not stripped on `str(owner)`) or double-escaping (if `|force_escape` is applied after `render_snippet`).

---

## 06.40-03

### 1. Summary
Plan `06.40-03` verifies the D-09 admission sequence (permission check first, state check second, once-only `_cv_child_link_has_access(user, owner)` per child item) across core and Guardian views in `tests/test1/test_navbar_permissions.py`, and records isolated hook/query cost measurements and byte-for-byte nonparticipant preservation in `tests/test1/test_navbar_costs.py` and `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md`.

### 2. Strengths
- **Correctly reverses context-button evaluation order for the navbar**: Existing context buttons (`src/crud_views/lib/view/buttons.py:109-118, 238-243`) and `CrudView._cv_get_action_context` (`src/crud_views/lib/view/base.py:910-916`) call `_cv_action_enabled_for_rendering` before `cv_has_access` / `_cv_child_link_has_access`. Plan 03 Task 01 enforces D-09 (`cv_has_access` / `_cv_child_link_has_access` first; `_cv_action_enabled_for_rendering(user, owner, rendering_view)` only when access passes) locally in `navbar.py` without touching `buttons.py` or `base.py`.
- **Single-call compatibility with Guardian collection and create views**: Verified against `GuardianQuerysetMixin._cv_child_link_has_access` (`src/crud_views_guardian/lib/mixins.py:297-305`), `GuardianCreateViewPermissionRequired._cv_child_link_has_access` (`src/crud_views_guardian/lib/views.py:387-390`), and `GuardianCreateViewPermissionRequired._cv_action_enabled_for_context` (`src/crud_views_guardian/lib/views.py:305-313`), which resolves `cls._cv_guardian_create_parent(owner)` (`src/crud_views_guardian/lib/views.py:294`: `if isinstance(obj, parent_model): return obj`) without extra queries when passed the navbar `owner`.
- **Propagates reached `ImproperlyConfigured` policy errors**: Matches `_operation_requirements` (`src/crud_views/lib/ancestors.py:363`), `_permission_name` (`src/crud_views/lib/ancestors.py:454-461`), and `_immediate_parent_access` (`src/crud_views/lib/ancestors.py:683-686`).

### 3. Concerns
- **[LOW] Process-wide permission vocabulary cache sensitivity in cold/warm SQL tests (`src/crud_views/lib/viewset/__init__.py:474-510`)**:
  - `ViewSet.default_permissions` (`src/crud_views/lib/viewset/__init__.py:489-490`) caches `self._default_permissions` on the `ViewSet` instance once populated, and `ContentType.objects.get_for_model` caches in `ContentType.objects`. Under `pytest -n 4`, worker test order can warm `_default_permissions` before a "cold vocabulary" test runs unless the test explicitly resets `viewset._default_permissions = None` and `ContentType.objects.clear_cache()` (as done in `tests/test1/test_guardian_child_link_visibility.py:1068-1151`).
- **[LOW] `_immediate_parent_access` `rendering_view` parameter (`src/crud_views/lib/ancestors.py:654-686` vs `src/crud_views/lib/view/base.py:528-541`)**:
  - `CrudView._cv_child_link_has_access(cls, user, parent_obj)` (`src/crud_views/lib/view/base.py:528-535`) calls `_immediate_parent_access(cls, user, parent_obj)` without `rendering_view`. Because the navbar already passes the request-resolved `owner` object as `parent_obj`, `_immediate_parent_access` uses `parent_obj` directly without needing `_resolved_parent(rendering_view)` (`src/crud_views/lib/ancestors.py:676-679`), and calling `target._cv_child_link_has_access(user, owner)` satisfies D-09 verbatim.

### 4. Suggestions
- In `tests/test1/test_navbar_costs.py`, explicitly reset `vs._default_permissions = None`, `ContentType.objects.clear_cache()`, and re-fetch the `User` row before each cold-cache measurement so results are deterministic across `pytest -n 4` workers.

### 5. Risk Assessment
**LOW** — The permission and state hooks are already implemented and tested in Phase 06.39 (`tests/test1/test_guardian_child_link_visibility.py` and `tests/test1/test_action_enabled.py`); Plan 03 only wires and measures them from `navbar.py`.

---

## 06.40-04

### 1. Summary
Plan `06.40-04` creates the self-contained `examples/bootstrap5/navbar_demo` app with `Tenant` and `Customer` models, `0001_initial.py` migration, `GuardianViewSet` for `Tenant`, core `ViewSet` for `Customer` with `Details` and `Notes` detail views, URL routing under `/object-navbar/`, and initial tenant-boundary tests. While using `navbar_tenant` and `navbar_customer` as `ViewSet` names wisely avoids a registry collision with `conditional`'s `customer` ViewSet (`examples/bootstrap5/conditional/views.py:272`), it introduces a critical `ParentViewSet(attribute=...)` requirement that is currently omitted from the plan text.

### 2. Strengths
- **Avoids global `_REGISTRY` name collision with `examples/bootstrap5/conditional/views.py:272`**: `examples/bootstrap5/conditional/views.py:272` already registers `cv_customer = ViewSet(model=Customer, name="customer", ...)`. Because `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:47, 207-211`) is process-global and raises `CrudViewError("ViewSet name customer is already registered...")` when `project/urls.py` imports all example apps, prefixing the ViewSet names (`navbar_tenant`, `navbar_customer`) prevents a startup crash.
- **Defers `FEATURES` registration until `seed.py` exists in Plan 05**: Because `examples/bootstrap5/project/management/commands/seed.py:18-19` iterates `FEATURES` and runs `import_module(f"{feature.app}.seed").seed()`, withholding `FEATURES` registration in Plan 04 keeps `manage.py seed` working at Wave 3.

### 3. Concerns
- **[HIGH] `ParentViewSet.get_attribute()` defaults to `self.viewset.name` (`"navbar_tenant"`), which will fail `_validate_relationship` (`src/crud_views/lib/viewset/parentviewset.py:62-65`, `src/crud_views/lib/ancestors.py:158-174`)**:
  - In `src/crud_views/lib/viewset/parentviewset.py:62-65`:
    ```python
    def get_attribute(self) -> str:
        return self.attribute if self.attribute else self.viewset.name
    ```
  - And in `src/crud_views/lib/ancestors.py:158-173`, `_validate_relationship` calls `model._meta.get_field(edge.get_attribute())` and raises `_AncestryError` (`viewset.E266` in `src/crud_views/checks.py:68-74` and `ImproperlyConfigured` on every request in `_authorize_ancestors` at `src/crud_views/lib/ancestors.py:476`) if the child model does not have a field with that exact name.
  - Because Task 01 names the parent `ViewSet` `name="navbar_tenant"` while the `Customer` model's `ForeignKey` is named `tenant` (`Customer has name, notes and Tenant FK`), `ParentViewSet(name="navbar_tenant")` **must** specify `attribute="tenant"` (e.g., `ParentViewSet(name="navbar_tenant", attribute="tenant")`, and optionally `prefix="tenant"` / `prefix="customer"` on the ViewSets if clean URL paths `/object-navbar/tenant/.../customer/...` are desired). Without `attribute="tenant"`, every `Customer` request and system check will fail with `Customer has no field 'navbar_tenant'`.
- **[LOW] `CustomerNotesView` short action label default (`src/crud_views/lib/views/detail.py:16-17`)**:
  - A second subclass of `DetailViewPermissionRequired` / `ObjectDetailViewPermissionRequired` with `cv_key = "notes"` and `cv_path = "notes"` inherits `cv_action_short_label_template = "crud_views/snippets/action_short/detail.html"` (`src/crud_views/lib/views/detail.py:17`), which renders `"Details"`. Either `CustomerNotesView` should set `cv_action_short_label_template_code = _("Notes")` and `cv_action_label_template_code = _("Notes")` (and `cv_header_template_code`), or `NavItem(key="notes", label=_("Notes"))` must override it. Setting the view's own label templates is cleaner because `ManageView` and context buttons also read them.

### 4. Suggestions
- Explicitly specify `ParentViewSet(name="navbar_tenant", attribute="tenant")` on `cv_customer` (and `prefix="tenant"` / `prefix="customer"` on `cv_tenant` / `cv_customer` if clean URLs are desired) in Task 01.
- Set `cv_action_short_label_template_code = _("Notes")`, `cv_action_label_template_code = _("Notes")`, and `cv_header_template_code = _("Notes for {{ object }}")` (or equivalent) on the `Customer` Notes view class.

### 5. Risk Assessment
**MEDIUM** — The `ParentViewSet(name="navbar_tenant", attribute="tenant")` mismatch would cause immediate `_AncestryError` / `E266` failures in Task 01 unless `attribute="tenant"` is set.

---

## 06.40-05

### 1. Summary
Plan `06.40-05` completes the `examples/bootstrap5/navbar_demo` hierarchy (`Order`, `Item`, `Address`), adds migration `0002_order_item_address.py`, seeds `alice`, `bob`, and `charlie` in `navbar_demo/seed.py` and `project/seeding.py`, adds the landing template `navbar_demo/home.html`, registers `navbar_demo` in `project/features.py`, and places `{% cv_navbar %}` in `examples/bootstrap5/project/templates/project/crud_views.html`. However, source verification against `examples/bootstrap5/project/tests.py` and `examples/bootstrap5/test_doc_links.py` reveals three concrete cross-test breakages caused by registering `navbar_demo` in `FEATURES` in Plan 05 without updating `examples/bootstrap5/project/tests.py` or satisfying the project-wide feature test invariants.

### 2. Strengths
- **Bounded tenant/model permission architecture**: Granting Guardian object permissions (`view`, `change`) only on `Tenant` and ordinary Django model permissions on `Customer`, `Order`, `Item`, and `Address` with `DEFAULT_CASCADE = True` (`src/crud_views/lib/ancestor_policy.py:19-22`) enforces tenant isolation at every descendant depth (`Order`, `Item`, `Address`) without per-record Guardian grants.
- **Preserves `ensure_developer_read_access` invariant (`examples/bootstrap5/project/seeding.py:42-90`)**: Task 02 explicitly avoids granting `developer` unallowlisted permissions on the new models, respecting the strict check in `ensure_developer_read_access` (`examples/bootstrap5/project/seeding.py:76-85`).
- **Whitespace-neutral `{% block cv_navbar %}` placement in `examples/bootstrap5/project/templates/project/crud_views.html:10-14`**: Placing `{% block cv_navbar %}{% cv_navbar %}{% endblock cv_navbar %}` adjacent to `cv_breadcrumb` ensures nonparticipating example pages render without added blank lines or wrapper elements.

### 3. Concerns
- **[HIGH] `examples/bootstrap5/project/tests.py:457-477` (`FeatureGroupsTest.test_grouping_matches_spec`) is hardcoded and NOT in `files_modified`**:
  - In `examples/bootstrap5/project/tests.py:457-477`, `FeatureGroupsTest.test_grouping_matches_spec` asserts exact equality of `{group.key: [f.app for f in features]}` against a hardcoded dictionary where `"ui"` is `["breadcrumbs", "context_buttons", "action_menus", "label_modes", "flash_messages", "disabled_actions", "theming"]`.
  - Task 03 registers `navbar_demo` in `examples/bootstrap5/project/features.py` with `group="ui"`, but `examples/bootstrap5/project/tests.py` is **not** in `files_modified` of Plan 05 (or any other plan). When the example test suite runs in Plan 08 (`.venv/bin/nox -s tests examples ...`), `FeatureGroupsTest.test_grouping_matches_spec` will **fail** with `AssertionError`.
- **[HIGH] `navbar_demo` landing page (`navbar-demo-home`) must satisfy four `FEATURES` invariants in `examples/bootstrap5/project/tests.py`**:
  - Every `feature` in `FEATURES` is automatically tested by `examples/bootstrap5/project/tests.py`:
    1. `HomePageTest.test_every_feature_landing_page_renders` (`project/tests.py:75-81`): GETs `reverse(feature.url_name)` as an unseeded superuser -> must return HTTP 200.
    2. `ExampleAboutTest.test_every_feature_page_shows_about` (`project/tests.py:238-248`): GETs `reverse(feature.url_name)` -> must render `{% example_about %}` (`id="example-about"`).
    3. `BreadcrumbAdoptionTest.test_every_feature_landing_page_shows_breadcrumb` (`project/tests.py:278-285`): GETs `reverse(feature.url_name)` -> must render `{% cv_breadcrumb %}` (`aria-label="breadcrumb"` and `"Home"`). For a standalone `TemplateView` without a `ViewSet`, compare `ThemeIndexView` (`examples/bootstrap5/theming/views.py:21-34` and `examples/bootstrap5/theming/templates/theming/index.html:7-9, 39`), which inherits `BreadcrumbMixin`, implements `cv_breadcrumb_get()`, puts `context["cv_breadcrumb"] = self.cv_breadcrumb()` in `get_context_data()`, and renders `{% example_about %}`, `{% cv_breadcrumb %}`, and `{% snippet_panels %}`.
    4. `DocRefsPanelTest.test_every_feature_page_lists_its_doc_refs` (`project/tests.py:394-403`): GETs `reverse(feature.url_name)` -> must render `{% snippet_panels %}` containing `"References to documentation"` and all `feature.docs` links.
  - Task 03 does not list `examples/bootstrap5/theming/views.py` or `examples/bootstrap5/theming/templates/theming/index.html` in `read_first` and does not mention that `navbar_demo/home.html` and its view must include `BreadcrumbMixin` (`cv_breadcrumb_get`), `{% example_about %}`, `{% cv_breadcrumb %}`, and `{% snippet_panels %}`.
- **[MEDIUM] Registering `navbar_demo` in `FEATURES` in Plan 05 with `docs=()` breaks `project/tests.py` and `test_doc_links.py` between Wave 4 and Wave 5**:
  - Task 03 states: "Link to Object navbar reference using Feature.docs/DocRef, registered in plan 06 after the documentation exists. Register navbar_demo in FEATURES now that its seed exists".
  - However, `examples/bootstrap5/test_doc_links.py:105-107` (`test_every_feature_declares_doc_refs`) asserts `assert feature.docs` for every entry in `FEATURES`, and `examples/bootstrap5/project/tests.py:394-403` (`test_every_feature_page_lists_its_doc_refs`) asserts `"References to documentation"` is present on `reverse(feature.url_name)` (which `snippet_panels.html` omits when `docs=()`). Thus `project/tests.py` and `test_doc_links.py` will fail at the end of Wave 4 until Plan 06 Task 03 populates `docs=(DocRef(...),)`.
- **[MEDIUM] `ParentViewSet(attribute=...)` requirement for `navbar_order`, `navbar_item`, and `navbar_address` (`src/crud_views/lib/viewset/parentviewset.py:62-65`)**:
  - Just as in Plan 04, because the ViewSets are named `navbar_customer` and `navbar_order` while the model `ForeignKey` fields on `Order`, `Address`, and `Item` are `customer` and `order`, `cv_order` and `cv_address` must declare `ParentViewSet(name="navbar_customer", attribute="customer")` and `cv_item` must declare `ParentViewSet(name="navbar_order", attribute="order")`.

### 4. Suggestions
- Add `examples/bootstrap5/project/tests.py` to `files_modified` in Plan 05 (or Plan 06) and update `FeatureGroupsTest.test_grouping_matches_spec` (`examples/bootstrap5/project/tests.py:457-477`) to include `"navbar_demo"` in `"ui"`.
- In Plan 05 Task 03, follow `examples/bootstrap5/theming/views.py:21-34` and `examples/bootstrap5/theming/templates/theming/index.html:1-41` so the `navbar-demo-home` view inherits `BreadcrumbMixin` (implementing `cv_breadcrumb_get` and setting `context["cv_breadcrumb"] = self.cv_breadcrumb()`) and `navbar_demo/home.html` renders `{% example_about %}`, `{% cv_breadcrumb %}`, and `{% snippet_panels %}`.
- Specify `attribute="customer"` on `cv_order` and `cv_address`'s `ParentViewSet`, and `attribute="order"` on `cv_item`'s `ParentViewSet`.
- Ensure `<nav>` in `tags/navbar_items.html` does not use the `navbar` CSS class (`<nav class="navbar...">`), because `navbar_html(resp)` in `examples/bootstrap5/project/tests.py:499-503` slices the top site navbar using `body.index('<nav class="navbar')`.

### 5. Risk Assessment
**HIGH** — Without updating `examples/bootstrap5/project/tests.py:457-477` (`test_grouping_matches_spec`), equipping `navbar-demo-home` with `BreadcrumbMixin` + `{% example_about %}` + `{% cv_breadcrumb %}` + `{% snippet_panels %}`, and setting `ParentViewSet(attribute=...)` on the prefixed ViewSets, the example test suite in `examples/bootstrap5/project/tests.py` will fail.

---

## 06.40-06

### 1. Summary
Plan `06.40-06` authors `docs/reference/navbar.md`, updates cross-references in `docs/reference/index.md`, `nested.md`, `context_buttons.md`, `breadcrumb.md`, `templates.md`, `theme.md`, `docs/getting_started/demo.md`, `docs/development/stability.md`, and `CHANGELOG.md`, wires `Feature.docs` in `examples/bootstrap5/project/features.py`, and adds executable documentation/contract tests in `tests/test1/test_navbar_docs.py`. The plan is thorough, but must respect strict regex assertions in existing documentation test suites (`tests/test1/test_snippet_docs.py`).

### 2. Strengths
- **Aligns `Feature.docs` with `examples/bootstrap5/test_doc_links.py:139-147`**: Task 03 explicitly notes that `test_docs_page_links_back_to_demo` requires `DEMO_BASE + reverse(feature.url_name)` (`https://django-crud-views-demo.onrender.com/object-navbar/`) inside a `!!! example` admonition on *every* page listed in `Feature.docs`, and therefore restricts `navbar_demo`'s `DocRef` tuple to pages carrying that reciprocal admonition.
- **Executable doc verification in `tests/test1/test_navbar_docs.py`**: Tests actual imports, `NavBar`/`NavItem` declarations with `gettext_lazy`, template overrides, and `docs/development/stability.md` inventory entries against live package symbols rather than brittle prose-matching.

### 3. Concerns
- **[HIGH] `tests/test1/test_snippet_docs.py:27-42` enforces an exact 8-row regex match on `## Snippet variables` in `docs/reference/templates.md`**:
  - In `tests/test1/test_snippet_docs.py:27-36`:
    ```python
    def _section(path, heading):
        text = path.read_text()
        assert text.count(heading) == 1, f"Missing or duplicated section: {heading}"
        return text.split(heading, 1)[1].split("\n## ", 1)[0]

    def test_snippet_variables_table_lists_exactly_the_eight_names():
        section = _section(TEMPLATES, SECTION)
        rows = re.findall(r"^\| `([a-z_]+)` \| (.*?) \|$", section, re.M)
        assert tuple(name for name, _ in rows) == VARIABLES
    ```
  - Because `## Snippet variables` (`docs/reference/templates.md:161-214`) is the final `## ` section in `docs/reference/templates.md`, any new markdown table row matching ``^| `([a-z_]+)` | ... |$`` added at the end of `docs/reference/templates.md` without a preceding `## ` heading will be captured by `_section(TEMPLATES, "## Snippet variables")` and cause `test_snippet_variables_table_lists_exactly_the_eight_names` to fail!
  - In `docs/reference/templates.md`, `{% cv_navbar %}` belongs in the `## What to put in it` table (`docs/reference/templates.md:16-23`, where cells start with ``| `{% cv_... %}` |`` which does not match ``r"^\| `([a-z_]+)` \|"``), and any mention of `cv_navbar` context at the bottom of `docs/reference/templates.md` must be a bullet point (like lines `199-214`) or under its own `## ` section.
- **[LOW] Verification command in Task 03 omits `project/tests.py`**:
  - Task 03 runs `.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py test_doc_links.py`, which does not run `project/tests.py` (where `DocRefsPanelTest`, `FeatureGroupsTest`, `BreadcrumbAdoptionTest`, `ExampleAboutTest`, and `NavGroupsTest` verify the new `FEATURES` entry). Running `project/tests.py` here will catch any `FEATURES` integration issue immediately in Wave 5 instead of waiting for Wave 6 (Plan 08).

### 4. Suggestions
- In Task 02, add `{% cv_navbar %}` to the `## What to put in it` table in `docs/reference/templates.md:16-23` and mention `cv_navbar`'s template context as a bullet linking to `[Object navbar](navbar.md)` (never as a ``| `...` |`` table inside `## Snippet variables`).
- Add `tests/test1/test_snippet_docs.py` to Task 02's `verify` command and `project/tests.py` to Task 03's `verify` command.

### 5. Risk Assessment
**LOW** — Provided `docs/reference/templates.md` does not add ``| `identifier` |`` rows inside `## Snippet variables` and `project/tests.py` is run alongside `test_doc_links.py`.

---

## 06.40-07

### 1. Summary
Plan `06.40-07` acquires or verifies an isolated checkout of `https://github.com/jacob-consulting/skills` at `../skills-navbar-06-40`, updates the four tracked skill files (`SKILL.md`, `references/templates-and-navigation.md`, `references/api-reference.md`, `CHANGELOG.md`), runs the companion repo's native `scripts/validate.py` validator, commits the changes locally on a `docs/navbar-06.40` branch, and records the receipt in `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md`.

### 2. Strengths
- **Respects repository separation (`docs/development/index.md:87-91`)**: Correctly targets the external `jacob-consulting/skills` repository rather than creating stale skill files inside `django-crud-views` or mutating user-global installed skill mirrors under `~/.claude/` or `~/.config/`.
- **Safe checkout and worktree hygiene**: Task 01 verifies `git rev-parse --show-toplevel`, remote URL identity, and `git ls-files` on all four target paths before editing, and uses a dedicated branch without pushing or publishing.

### 3. Concerns
- **[MEDIUM] Relative path `../skills-navbar-06-40` when executing from a GSD worktree (`CLAUDE.md:72-86`)**:
  - Per `CLAUDE.md:72-86`, phase worktrees live at `/home/alex/projects/workspaces/cv-phase-06-40/django-crud-views`, where `..` is `/home/alex/projects/workspaces/cv-phase-06-40/` (the GSD workspace container), whereas from `/home/alex/projects/alex/django-crud-views`, `..` is `/home/alex/projects/alex/`.
  - While `../skills-navbar-06-40` works consistently within a single checkout's working directory because Task 01 clones it at `../skills-navbar-06-40` if absent, the executor must ensure `../skills-navbar-06-40` is cleaned up or not accidentally included in any parent workspace archive, and `06.40-COMPANION-DELIVERY.md` should record the resolved absolute path alongside the commit SHA.
- **[LOW] Network/auth dependency for `git clone https://github.com/jacob-consulting/skills`**:
  - If an existing local clone of `jacob-consulting/skills` is already present on the machine or if SSH (`git@github.com:jacob-consulting/skills.git`, matching `docs/development/index.md:17`) is configured instead of HTTPS credentials, `git clone https://...` might fail if the repo is private or HTTPS auth is unconfigured. Checking for an existing local clone or falling back to `git@github.com:jacob-consulting/skills.git` is safer.

### 4. Suggestions
- In Task 01, allow cloning from a local reference checkout or `git@github.com:jacob-consulting/skills.git` if `https://github.com/jacob-consulting/skills` requires SSH authentication, while still verifying the remote URL identity (`jacob-consulting/skills`).

### 5. Risk Assessment
**LOW** — Self-contained documentation and metadata updates in an isolated companion checkout with explicit failure gates.

---

## 06.40-08

### 1. Summary
Plan `06.40-08` executes live Playwright browser verification (`06.40-BROWSER-CHECK.js` -> `06.40-BROWSER.json`, `06.40-desktop.png`, `06.40-narrow-focus.png`) at 1280px, 320px, and 200% reflow against an isolated SQLite database (`.pytest_cache/navbar_browser_settings.py`), followed by the full supported source and installed test matrices (`nox -s tests examples crispy_floor manage_report_floor package`, `mkdocs build --strict`, `ruff`, `npm test`), recording final evidence in `06.40-ACCEPTANCE.md` and `06.40-VALIDATION.md`.

### 2. Strengths
- **Isolated temporary SQLite database for live browser testing**: Creating `.pytest_cache/navbar_browser_settings.py` that overrides only `DATABASES["default"]["NAME"]` prevents `migrate` and `seed` from mutating `examples/bootstrap5/db.sqlite3` (`examples/bootstrap5/project/settings.py:102-107`).
- **Complete coverage of project quality and packaging gates (`noxfile.py:20-222`, `scripts/check_dist.py:1-89`)**: Task 02 exercises both normal and `CV_ACCESS_RECORD_REQUESTS=1` passes (`noxfile.py:36-57`), `crispy_floor` (`noxfile.py:189-200`, including `_FORMAT_HTML_AUDIT` at `noxfile.py:170-186`), `manage_report_floor` at Pydantic `2.2.1` (`noxfile.py:88-108`), and `scripts/check_dist.py` (`noxfile.py:216-222`).

### 3. Concerns
- **[MEDIUM] `ALLOWED_HOSTS` in `examples/bootstrap5/project/settings.py:18-19` when `DEV_TUNNEL_HOSTNAME` is set in the shell environment**:
  - Look at `examples/bootstrap5/project/settings.py:18-19`:
    ```python
    _tunnel_host = os.environ.get("DEV_TUNNEL_HOSTNAME", "")
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", _tunnel_host] if _tunnel_host else []
    ```
  - When `DEBUG = True` and `ALLOWED_HOSTS = []`, Django allows `127.0.0.1` and `localhost`. Setting `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]` explicitly in `.pytest_cache/navbar_browser_settings.py` is harmless and ensures `127.0.0.1:8765` is always accepted regardless of environment variables.
- **[MEDIUM] Cleanup of background `runserver 127.0.0.1:8765` process and transient `.pytest_cache/navbar_browser_settings.py`**:
  - Task 01 starts `runserver 127.0.0.1:8765 --noreload` and creates `.pytest_cache/navbar_browser_settings.py` plus a temporary SQLite file. If `runserver` is not terminated in a `finally`/cleanup step after `browser_run_code` finishes, port `8765` remains bound and the background process can linger.
- **[LOW] `_FORMAT_HTML_AUDIT` in `noxfile.py:170-186` enforces `format_html` argument count across `src/`**:
  - `nox -s crispy_floor` runs `_FORMAT_HTML_AUDIT` (`noxfile.py:170-186`), which parses every `.py` file under `src/` with `ast` and fails if any `format_html(...)` call has fewer than 2 arguments (`len(node.args) + len(node.keywords) < 2`, because Django 6.0 removed 1-arg `format_html()`). If `src/crud_views/lib/navbar.py` calls `format_html`, it must always pass at least one format argument.

### 4. Suggestions
- In Task 01, ensure the background `runserver 127.0.0.1:8765 --noreload` process is explicitly killed (`kill $SERVER_PID`) and the temporary SQLite file and `.pytest_cache/navbar_browser_settings.py` are removed once `06.40-BROWSER.json` and the screenshots are captured.
- Ensure any `format_html` usage in `src/crud_views/lib/navbar.py` passes at least one positional or keyword value argument so `_FORMAT_HTML_AUDIT` (`noxfile.py:170-186`) passes on Django 6.0.

### 5. Risk Assessment
**MEDIUM** — Live Playwright viewport/reflow verification and the multi-Python/multi-Django Nox matrix are the most environment-sensitive steps in the phase, and depend on resolving the Plan 04/05 `examples/bootstrap5/project/tests.py` and `ParentViewSet(attribute=...)` issues first.

---

## Cross-Plan Comparison & Overall Assessment

| Plan | Wave | Primary Scope | Risk | Key Cross-Plan Dependency / Finding |
|---|---|---|---|---|
| `06.40-01` | 1 | Core `navbar.py`, `{% cv_navbar %}`, routing & startup checks | LOW | Supplies `NavBar`, `NavItem`, `CrudViewNavBarMixin` to Plans 02–06 |
| `06.40-02` | 2 | Leaf templates (`navbar_identity.html`, `navbar_items.html`), lazy context & escaping | MEDIUM | Must strip `SafeData` on `str(owner)`/`NavItem.label` without double-escaping `cv_get_action_short_label`; must put `mw-100` on `<li class="nav-item">` for Plan 08 reflow |
| `06.40-03` | 3 | Access-before-state, Guardian child hooks, SQL cost & byte preservation | LOW | Produces `06.40-COST.md` consumed by Plan 06 (`docs/reference/navbar.md`) |
| `06.40-04` | 3 | `navbar_demo` `Tenant`/`Customer` models, `0001_initial`, routes & tests | MEDIUM | Prefixed ViewSet `navbar_tenant` requires `ParentViewSet(name="navbar_tenant", attribute="tenant")` on `cv_customer` (`src/crud_views/lib/viewset/parentviewset.py:62-65`) |
| `06.40-05` | 4 | `Order`/`Item`/`Address`, `seed.py`, `home.html`, `FEATURES` & base template | HIGH | Must update `examples/bootstrap5/project/tests.py:457-477` (`test_grouping_matches_spec`), set `attribute=` on `ParentViewSet`, and include `BreadcrumbMixin` + `{% example_about %}` + `{% cv_breadcrumb %}` + `{% snippet_panels %}` on `navbar-demo-home` |
| `06.40-06` | 5 | Reference docs, `stability.md`, `CHANGELOG.md`, `DocRef`s & doc tests | LOW | Must not add ``\| `name` \|`` rows inside `## Snippet variables` in `docs/reference/templates.md` (`tests/test1/test_snippet_docs.py:33-36`) |
| `06.40-07` | 6 | Companion skill updates in `../skills-navbar-06-40` | LOW | Parallel with Plan 08; required before final sign-off in `06.40-ACCEPTANCE.md` |
| `06.40-08` | 6 | Playwright 320px/1280px/200% reflow & full Nox acceptance matrix | MEDIUM | Runs `examples/bootstrap5/project/tests.py` and `tests/test1/test_snippet_docs.py`, which will fail unless Plans 04–06 address the findings above |

### Top Priority Fixes Before Execution
1. **`ParentViewSet(attribute=...)` in Plans `06.40-04` and `06.40-05` (`src/crud_views/lib/viewset/parentviewset.py:62-65`, `src/crud_views/lib/ancestors.py:158-174`)**: Because the example ViewSets use prefixed names (`navbar_tenant`, `navbar_customer`, `navbar_order`) while the model FK fields are `tenant`, `customer`, and `order`, every `ParentViewSet` declaration in `examples/bootstrap5/navbar_demo/views.py` must set `attribute="tenant"`, `attribute="customer"`, or `attribute="order"` explicitly.
2. **Update `examples/bootstrap5/project/tests.py:457-477` and `navbar_demo/home.html` in Plan `06.40-05`**: Add `examples/bootstrap5/project/tests.py` to `files_modified` so `FeatureGroupsTest.test_grouping_matches_spec` includes `"navbar_demo"` under `"ui"`, and ensure the `navbar-demo-home` view and `navbar_demo/home.html` template include `BreadcrumbMixin` (`cv_breadcrumb_get`), `{% example_about %}`, `{% cv_breadcrumb %}`, and `{% snippet_panels %}` (following `examples/bootstrap5/theming/views.py:21-34` and `examples/bootstrap5/theming/templates/theming/index.html:1-41`).
3. **Preserve `## Snippet variables` table invariant in Plan `06.40-06` (`tests/test1/test_snippet_docs.py:27-42`)**: Do not add ``| `var_name` | ... |`` markdown table rows inside the `## Snippet variables` section of `docs/reference/templates.md`.
4. **Single-pass `SafeString` escaping in Plan `06.40-01` / `06.40-02` (`src/crud_views/lib/view/base.py:578-592, 638-643`)**: Convert `SafeData` on `str(owner)` and `NavItem.label` to plain `str` (`str.__str__(str(val))`) in Python rather than applying `|force_escape` on already-rendered `cv_get_action_short_label` output.
