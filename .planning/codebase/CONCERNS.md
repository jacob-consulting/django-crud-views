---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# Codebase Concerns

**Analysis Date:** 2026-10-25

**Baseline at analysis time:** version `0.30.0` (`pyproject.toml:3`), unreleased work on `main` @ `38b0100`.
`pytest tests -n auto --cov` → 2845 passed, 1 skipped, total coverage 96.23 % (gate `fail_under = 88`,
`pyproject.toml:154`). `ruff check src tests` is clean. Open GitHub issues: #262, #259, #257, #254, #211, #210, #89.

**Prior audits:** `AUDIT.md` (2026-06-10, v0.5.0) is fully executed. Its High/Medium findings (the `assert Exception` in
formsets, `except AttributeError` create/update discrimination, duplicate ViewSet names, the v4-only UUID regex,
mutation of settings lists, import-time `get_user_model()`, the `my_new_tag` check) are fixed and must not be
re-raised. The most recent design review is `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md`, and
its follow-up plan is `superpowers/plans/2026-10-24-concept-review-followups.md` (phases 1A–4). The items below
include that review's open findings, checked against the code, plus new findings from this pass.

---

## Tech Debt

**Label-mode defaults are hard-coded literals in several places (highest-priority pre-1.0 debt):**

- Issue: each location's default label mode is a separate literal. `"both" if card else "icon"` is in
  `src/crud_views/lib/view/button_data.py:83`, `return target_default or "icon"` and `mapping.get(key, "icon")` are in
  `src/crud_views/lib/view/base.py:311` and `:318`, `cv_card_actions_label_mode = "both"` is on the card view, and the
  filter toggle hard-codes the `"icon"` slot in `src/crud_views/templates/crud_views/tags/context_action_filter.html:3`.
  There are three knob shapes: a per-button field (`ContextButton.label_mode`), per-key dicts
  (`cv_context_actions_label_mode`, `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`, `ViewSet.context_actions_label_mode`) and
  a per-view string (`cv_context_action_label_mode`). The last two differ by one letter (`base.py:89-96`).
- Files: `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/view/base.py:286-318`,
  `src/crud_views/lib/views/card.py:46-50`, `src/crud_views/lib/view/label_mode.py`
- Impact: #257 (form buttons) and #262 (filter toggle) would each add another literal. After 1.0 every knob name is
  frozen API.
- Fix approach: Phase 1A in `superpowers/plans/2026-10-24-concept-review-followups.md`. Add one setting,
  `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, merged per key over `{"context": "icon", "list": "icon", "card": "both"}`, and
  have `cv_button_data`, `cv_get_action_label_mode` and the filter toggle read it. Decide before 1.0 whether to rename
  `cv_context_action_label_mode` to `cv_action_label_mode`.

**The class-table key grammar gives the second segment two meanings:**

- Issue: in `location:slot[:mode]` the slot is a *variant* for action buttons (`context:primary`) but a *kind* for
  form buttons (`form:submit`, `form:cancel`, `form:filter-submit`). The W362 shape check (`_action_key_parts`) only
  accepts a mode segment after a variant, so `form:submit:icon` is rejected, and the test suite pins that
  (`tests/test1/test_button_classes_checks.py:79`).
- Files: `src/crud_views/lib/button_classes.py:56-60`, `src/crud_views/lib/button_classes.py:207-218`
- Impact: #257 collides with the check. The key names freeze at 1.0.
- Fix approach: Phase 1C of the follow-up plan. Choose option A (keep kinds, extend the shape to
  `form:<kind>:<mode>`) or option B (form buttons carry variants), and document the choice in `docs/reference/buttons.md`.

**Form buttons are outside the button leaf model:**

- Issue: crispy's `Submit`/`Button`/`Reset` (`src/crud_views/lib/crispy/buttons.py:16-18`) render as `<input>`
  through crispy's own `baseinput.html`. They get no `cv-key`, no `data-cv-tooltip`, no location and no leaf template,
  so a theme cannot change their markup.
- Files: `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/crispy/form.py:76`,
  `src/crud_views/lib/view/button_data.py:12` (`LOCATIONS`)
- Impact: this is the last button family a theme cannot restyle (#257).
- Fix approach: Phase 2 of the follow-up plan. Add a `tags/button/form.html` leaf fed by `cv_button_data(ctx, "form")`.
  If the button content is built with icon markup, build it with `format_html`/`conditional_escape`, because crispy's
  `button.html` renders `{{ button.content|safe }}`.

**Bootstrap leaks in shipped templates:**

- Issue: the alert close button uses `data-bs-dismiss="alert"` and `btn-close`
  (`src/crud_views/templates/crud_views/tags/alert.html:5`), which bypasses `cv.adapters`. The table pagination still
  renders `&laquo;`/`&raquo;` (`src/crud_views/templates/crud_views/table/bootstrap5.html:69`, `:91`), while card
  pagination moved to the icon registry (#241).
- Files: `src/crud_views/templates/crud_views/tags/alert.html`, `src/crud_views/templates/crud_views/table/bootstrap5.html`
- Impact: a non-Bootstrap theme has to copy these templates (Tabler copies both).
- Fix approach: Phases 3A and 3B. Add a `data-cv-alert-dismiss` adapter call (the same pattern as
  `data-cv-modal-dismiss`) and `page-previous`/`page-next` icons in the table template.

**jQuery is still needed for formsets:**

- Issue: `src/crud_views/static/crud_views/js/formset.js` (644 lines) uses `$(...)` (for example lines 53, 227 and 584),
  while every other script is jQuery-free (`docs/reference/javascript.md:15`).
- Files: `src/crud_views/static/crud_views/js/formset.js`
- Impact: pages with formsets need jQuery, which a strict CSP and modern themes do not want (#210).
- Fix approach: port it to plain DOM APIs. `tests/js/formset.test.js` is the safety net.

**Settings are evaluated at import time, and the theme path is baked into template-tag registration:**

- Issue: `crud_views_settings = CrudViewsSettings()` (`src/crud_views/lib/settings.py:279`) reads every
  `from_settings(...)` value in the class body (`settings.py:24-45`). Inclusion tags register with
  `f"{crud_views_settings.theme_path}/..."` at module import (`src/crud_views/templatetags/crud_views.py:60`, `:66`,
  `:107`, `:112`, `:117` and on).
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: `override_settings(CRUD_VIEWS_*)` has no effect. Tests have to `monkeypatch.setattr(crud_views_settings, ...)`
  (`tests/test1/test_context_actions_isolation.py:39`, `tests/test1/test_heading_level.py:116`). `CRUD_VIEWS_THEME`
  cannot change after the templatetag module loads.
- Fix approach: read settings lazily, or connect a `setting_changed` receiver that rebuilds `crud_views_settings`.
  Resolve inclusion-tag template names at render time with `simple_tag` plus `render_to_string`.

**0.29 compatibility paths kept until 1.0:**

- Issue: `CardAction.no_label` is still accepted next to `label_mode` (`src/crud_views/lib/view/card.py:11`, `:30-31`,
  `src/crud_views/lib/views/card.py:49`). A `cv_no_label` context key raises a `ValueError` guard in `cv_button_data`.
  Nothing warns about a stale `tags/card_action.html` override that still reads `cv_no_label` (#254).
- Files: `src/crud_views/lib/view/card.py`, `src/crud_views/lib/views/card.py`, `src/crud_views/lib/view/button_data.py`
- Impact: extra branches in a hot render path, plus silent visual regressions in stale overrides.
- Fix approach: remove both at 1.0.0 and list the removal in `CHANGELOG.md` `### Breaking` and `docs/migrating-1.0.md`.

**Stale and internal artifacts tracked at the repo root:**

- Issue: `AUDIT.md` (tracked) describes v0.5.0 and file paths that no longer exist (`lib/formsets/x.py`,
  `crud_views_plain`). `superpowers/` holds 212 tracked internal planning files. `github-support-request.md` and
  `settings_i18n.py` sit at the root.
- Files: `AUDIT.md`, `superpowers/`, `github-support-request.md`, `settings_i18n.py`
- Impact: misleads contributors and agents, who may "fix" findings that are already fixed.
- Fix approach: move `AUDIT.md` to `superpowers/notes/` or add a "superseded" banner at the top. Keep `superpowers/`
  out of the sdist (check the hatch sdist include list).

**Placeholder management command shipped to users:**

- Issue: `src/crud_views/management/commands/crud_views_show.py` has a `handle()` that only does `pass` ("placeholder
  command: prints nothing yet"), and it has 0 % coverage.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: shows up in `manage.py help` and does nothing.
- Fix approach: delete it, or implement it as a ViewSet/URL dump using `ViewSet` registry data.

**Misleading exception name:**

- Issue: `ViewSetKeyFoundError` (`src/crud_views/lib/exceptions.py:11`) is raised when a key is *not* found.
- Files: `src/crud_views/lib/exceptions.py`, and the call sites in `src/crud_views/templatetags/crud_views.py:227-269`
  and `src/crud_views/lib/table/columns.py:48`
- Fix approach: add `ViewSetKeyNotFoundError` with the old name as an alias, and remove the alias at 1.0.

**Small leftovers:**

- A commented-out debug print in `src/crud_views/lib/table/attrs.py:57`.
- `python-box` is a hard dependency (`pyproject.toml:29`), used only to wrap two dicts in
  `src/crud_views/lib/settings.py:245-265`.
- `crispy-bootstrap5` is a hard dependency (`pyproject.toml:34`), although the theme layer aims to be framework-neutral.

---

## Known Bugs

**The polymorphic create view trusts `polymorphic_ctype_id` from the URL:**

- Symptoms: `PolymorphicCrudViewMixin.polymorphic_model` runs `ContentType.objects.get(id=...)` without catching
  `DoesNotExist` and without checking that the type belongs to the viewset model's subclass tree or to
  `cv_polymorphic_include`/`cv_polymorphic_exclude`. An unknown id returns a 500. An unrelated content type, such as
  `auth.User`, reaches `get_form_class`, which raises
  `ValueError(f"No form found ... {self.object.__class__}")`. On a create view `self.object` is unset or `None`, so the
  message is wrong or raises a second error. The include/exclude filtering exists only in
  `PolymorphicCreateSelectView.get_form` (`create_select.py:58-66`), so a crafted URL can open the create form for an
  excluded subtype if `polymorphic_forms` maps it.
- Files: `src/crud_views_polymorphic/lib/utils.py:38-75`, `src/crud_views_polymorphic/lib/create.py:17-26`,
  `src/crud_views_polymorphic/lib/create_select.py:56-72`
- Trigger: GET `.../create/ct/999999/`, or a ctype id of an excluded subtype. Found by reading the code; not reproduced
  at runtime in this pass.
- Workaround: none. Make `polymorphic_forms` hold only the allowed subtypes.
- Fix: validate the id against `get_polymorphic_child_models_content_types(self.cv_viewset.model)` after applying
  include/exclude, raise `Http404` or `BadRequest`, and fix the message to name `self.polymorphic_model`.

**ManageView assumes the user model has a `username` field:**

- Symptoms: with `CRUD_VIEWS_MANAGE_SHOW_USERS = True`, `get_permission_holders` runs
  `.values_list("username").order_by("username")`, which raises `FieldError` for a custom user model without a
  `username` field (for example an email login).
- Files: `src/crud_views/lib/views/manage.py:48-58`
- Trigger: a custom `AUTH_USER_MODEL` with `USERNAME_FIELD = "email"` and no `username` column.
- Fix: use `user_model.USERNAME_FIELD`.

**An invalid `ContextButton.label_mode` crashes the page at render when strict mode is off:**

- Symptoms: `cv_button_data` raises `ValueError` for a mode outside `LABEL_MODES` (`button_data.py:84-85`) even in
  production. Everywhere else in the module, non-strict mode logs and degrades instead.
- Files: `src/crud_views/lib/view/button_data.py:83-85`
- Trigger: a developer typo that skipped `manage.py check` (E210/E211 catch it at check time).
- Fix: in non-strict mode, log a warning and fall back to the location default (this ties in with Phase 1A).

**A failed modal submit drops user input:**

- Symptoms: `cvModalSubmit` re-renders only on HTTP 422. Any other non-redirect response (400, 403, 500) navigates to
  the fallback URL, and the typed form data is lost without a message.
- Files: `src/crud_views/static/crud_views/js/modal.js:85-105`
- Trigger: a CSRF failure or server error while a form is posted in a modal.
- Fix: keep the modal open and inject an error alert for 4xx/5xx responses, or render the response body when it is
  HTML.

**The docs give the wrong number of class-table keys:**

- Symptoms: `docs/reference/buttons.md:112` says "The default table has 64 keys", but `DEFAULT_BUTTON_CLASSES` has 70
  (pinned by `tests/test1/test_button_classes.py:84`).
- Fix: correct the number, and generate the table from `DEFAULT_BUTTON_CLASSES` in the docs build so it cannot drift
  again.

---

## Security Considerations

**Manage view access modes let anonymous users in:**

- Risk: `ManageView.has_permission` returns `True` for everyone when `CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "yes"`, and
  for everyone (anonymous included) when it is `"debug_only"` (the default) and `DEBUG = True`. The page lists the
  groups that hold each permission and, with `CRUD_VIEWS_MANAGE_SHOW_USERS`, the usernames.
- Files: `src/crud_views/lib/views/manage.py:30-39`, `src/crud_views/lib/settings.py:27-28`,
  `src/crud_views_guardian/lib/views.py:236-270`
- Current mitigation: the default needs `DEBUG`, and the `"no"` value removes the views
  (`src/crud_views/lib/viewset/__init__.py:311`).
- Recommendations: require `request.user.is_authenticated` in every mode. Rename `"yes"` or document it as "everyone,
  including anonymous". Consider requiring `is_staff` for `"debug_only"`, since staging servers often run with
  `DEBUG = True`.

**The delete confirmation lists protected objects and related counts without permission filtering:**

- Risk: with `cv_show_related_objects = True`, `cv_filter_related_objects` filters only the cascade tree. `summary`
  (counts per model) and `protected` (rendered by `str()` in the error alert,
  `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:5`) pass through unfiltered. A user with
  delete permission on X sees the names of objects they have no view permission on. The guardian mixin keeps the same
  behaviour.
- Files: `src/crud_views/lib/views/delete.py:147-184`, `src/crud_views_guardian/lib/views.py:39-50`
- Current mitigation: `cv_show_related_objects` defaults to `False` (`delete.py:38`).
- Recommendations: replace unviewable protected objects with a counted placeholder ("2 protected objects you cannot
  view"), and say in `docs/` whether the summary counts are disclosed on purpose.

**Runtime guards written as `assert`:**

- Risk: `assert` disappears under `python -O`. The affected guards are `assert callable(wf_method)`
  (`src/crud_views_workflow/lib/views.py:103`), `assert not isinstance(user, str)`
  (`src/crud_views_guardian/lib/mixins.py:126`, `src/crud_views_guardian/lib/views.py:185`) and the parent
  assertions (`src/crud_views/lib/view/base.py:812`, `:820`, `src/crud_views/lib/views/create.py:49`).
- Current mitigation: in the workflow, `workflow_has_transition()` re-validates the transition first (`views.py:98-99`)
  and raises `SuspiciousOperation`.
- Recommendations: replace the asserts with `cv_raise(...)` (`src/crud_views/lib/exceptions.py:27`) or explicit
  exceptions.

**Workflow transitions race without a row lock:**

- Risk: two concurrent POSTs can both pass `workflow_has_transition` against the same unlocked state and both apply a
  transition. `self.object.save()` writes every field (a lost update), and two `WorkflowInfo` rows are written.
- Files: `src/crud_views_workflow/lib/views.py:97-135`
- Current mitigation: documented as a limitation in `docs/reference/request_lifecycle.md:288-290`.
  `WorkflowModelMixin.state_increment` (`src/crud_views_workflow/lib/mixins.py:23-24`) exists but nothing enforces it.
- Recommendations: add an opt-in `cv_workflow_lock = True` that re-fetches with `select_for_update()` inside the
  atomic block, or document django-fsm's `ConcurrentTransitionMixin`.

**A permission template filter fails closed and hides errors:**

- Risk: `cv_context_has_permission` catches bare `Exception` and returns `False`
  (`src/crud_views/templatetags/crud_views.py:461-467`), even under `CRUD_VIEWS_STRICT`. A misconfigured key hides the
  button instead of raising.
- Recommendations: catch only `ViewSetKeyFoundError`, and re-raise when `is_strict()` is true, as `ignore_exception`
  (`src/crud_views/lib/exceptions.py:39-60`) already does.

**Values from developer config rendered unvalidated:**

- Risk: the `<location>:container-tag` value is rendered as `<{{ cv_layout.tag }}` in
  `templates/crud_views/tags/button/container.html` with no validation, so `"div onclick=x"` would add an attribute.
  E364 validates `container-single` but nothing validates `container-tag` (`src/crud_views/lib/button_classes.py:184-204`).
  `BreadcrumbItem.coerce_title` keeps `SafeData` (`src/crud_views/lib/breadcrumb.py:33-37`), so a model `__str__`
  returning `mark_safe()` renders as HTML in every breadcrumb.
- Current mitigation: both values come from settings or model code, never from the request.
- Recommendations: add an E36x check that matches `container-tag` against `^[a-z][a-z0-9-]*$`, and add one sentence on
  the `SafeData` behaviour to `docs/reference/breadcrumb.md`.

**Strong areas (preserve these):** `alert_data`/`message_alerts` escape unconditionally (`src/crud_views/lib/messages.py:37-84`).
The `cv_from` origin is checked against a name regex and `cv_cancel_keys` (`src/crud_views/lib/view/base.py:683-688`).
The formset AJAX endpoint raises `BadRequest` for an unknown template (`src/crud_views/lib/formsets/mixins.py:41-66`).
List ordering is whitelisted (`src/crud_views/lib/views/mixins.py:203-220`). Pages carry no inline scripts (CSP-friendly).

---

## Performance Bottlenecks

**Delete view collects related objects repeatedly and resolves URLs with an N+1 pattern:**

- Problem: `DeleteView.post` calls `get_context_data` (`src/crud_views/lib/views/delete.py:200-203`), which runs
  `NestedObjects.collect` when `cv_show_related_objects` is on, and `self.object.delete()` then collects again. With
  `cv_link_related_objects`, `cv_get_related_object_url` scans the whole global `_REGISTRY` for every related object
  and follows the parent FK with `getattr` (one query per object) (`delete.py:98-117`, `:186-191`).
- Cause: context building is shared between GET and POST, and there is no per-model viewset index.
- Improvement path: skip the related-object collection on POST unless the form is invalid. Build a
  `{model: viewset}` map once per request. Use `select_related` on the parent attribute.

**Guardian access checks run per row and per action:**

- Problem: each `cv_has_access(user, obj)` creates a new `ObjectPermissionChecker(user)`
  (`src/crud_views_guardian/lib/mixins.py:68-70`, `src/crud_views_guardian/lib/views.py:202-204`), so list and card
  pages run about rows × actions permission queries. The callers are `src/crud_views/lib/view/buttons.py:104`, `:228`
  and `src/crud_views/lib/views/card.py:59`, `:82`.
- Cause: the checker is not cached per request, and `prefetch_perms()` is never called for the page's objects.
- Improvement path: cache one checker per `(request, user)` on the view and call
  `checker.prefetch_perms(page_object_list)` before rendering rows.

**`_PermittedPks` loads every permitted pk into memory:**

- Problem: `set(get_objects_for_user(...).values_list("pk"))` covers the whole table, per model
  (`src/crud_views_guardian/lib/views.py:61-69`).
- Improvement path: intersect with the pks actually present in the related tree (`.filter(pk__in=tree_pks)`).

**ManageView runs one query batch per permission:**

- Problem: for each permission it runs a user query and a group query (`src/crud_views/lib/views/manage.py:41-71`).
- Improvement path: fetch groups and users once with `permissions__in=` and group them in Python. This matters little
  because the view is a debug/admin page.

**Card lists are unpaginated by default:**

- Problem: `CardListView.paginate_by = None` (`src/crud_views/lib/views/card.py:25`), while table lists default to 10
  (`src/crud_views/lib/views/mixins.py:293`).
- Improvement path: use a default page size, or document the choice next to `paginate_by`.

---

## Fragile Areas

**The theme contract (class table, leaf keys, icon names, JS adapters):**

- Files: `src/crud_views/lib/button_classes.py` (70 default keys), `src/crud_views/lib/view/button_data.py:16-36`
  (`LEAF_KEYS`), `src/crud_views/lib/icons.py:13-96` (34 icon names, `BOOTSTRAP_ICONS`),
  `src/crud_views/static/crud_views/js/adapters.js`, `templates/crud_views/tags/button/{action,menu_item,menu_item_label,container}.html`
- Why fragile: external themes (the `crud_views_tabler` prototype) depend on all of these, but
  `docs/development/stability.md` lists only `crud_views.lib.button_classes` (#89). When a theme override goes stale
  after an upgrade, it fails silently (#211). Examples are the `cv_container_tag` key removed in #266 and old
  `tags/messages.html` keys rendering `class="alert alert-"`.
- Safe modification: treat every key, icon name and leaf variable as public API. Golden HTML tests under
  `tests/test1/golden/` must stay byte-identical unless a change is intentional. Each `### Breaking` CHANGELOG entry
  also updates `docs/migrating-1.0.md`.
- Test coverage: good upstream (sync tests for the icon and key sets). Nothing tests a third-party theme.

**Label-mode resolution order:**

- Files: `src/crud_views/lib/view/base.py:286-318`, `src/crud_views/lib/views/card.py:46-50`,
  `src/crud_views/lib/view/button_data.py:78-102`
- Why fragile: five resolution steps for context buttons and a different order for list rows. Dict maps are replaced
  whole across layers (`cv_first_inline_keys`), while the class table merges per key. The order needed a Mermaid
  diagram (`docs/reference/context_buttons.md`).
- Safe modification: change it only together with `tests/test1/test_context_button_label_mode.py`,
  `test_context_action_label_mode.py`, `test_action_label_mode_*.py` and the golden files.

**Nested formsets:**

- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`,
  `src/crud_views/lib/formsets/inline_formset.py`, `src/crud_views/lib/formsets/mixins.py`,
  `src/crud_views/static/crud_views/js/formset.js`
- Why fragile: the prefix scheme is `{key}-{parent_prefix}-{pk}-{index}`, kept in sync between Python and 644 lines of
  jQuery. The save path depends on `form.has_changed()`. The polymorphic formset branch is complex. `assert`s guard
  invariants (`formsets.py:208`, `:380`; `inline_formset.py:64`, `:67`).
- Safe modification: run `tests/js/formset.test.js` (vitest) and the Python formset tests together. Never change the
  prefix format on one side only.
- Test coverage: `inline_formset.py` 81 % (lines 46-48, 138-150 uncovered), `formsets/mixins.py` 87 %.

**Global registries and import order:**

- Files: `src/crud_views/lib/viewset/__init__.py:41-42` (`_REGISTRY`, `_REGISTRY_LOCK`), `src/crud_views/lib/assets.py:52`,
  `src/crud_views/lib/view/meta.py` (registration at class definition)
- Why fragile: ViewSets register when their module is imported, and duplicate names raise
  (`viewset/__init__.py:134-139`). Re-importing view modules (test reloads, autoreload edge cases) or defining two
  ViewSets with the same name in different apps fails at import. `lib.view.base` depends on the app registry through
  Django's `auth.mixins` import (see the M8 note in `AUDIT.md`).
- Safe modification: define ViewSets at module level in `views.py`, never inside functions, and give them
  project-unique names.

---

## Scaling Limits

**Linear registry scans:**

- Current capacity: fine for tens of ViewSets.
- Limit: `cv_get_related_object_url` (`src/crud_views/lib/views/delete.py:102`) and the system checks
  (`src/crud_views/lib/check.py:311-314`) iterate the whole `_REGISTRY`. The cost grows as ViewSets × related objects
  on delete pages.
- Scaling path: keep a `model → [viewset]` index on registration.

**Session-stored view state:**

- Current capacity: one session key (`CRUD_VIEWS_SESSION_DATA_KEY`, default `"viewset"`) holds filter and sort state
  for every ViewSet (`src/crud_views/lib/session.py:64-80`).
- Limit: it grows with the number of ViewSets a user visits and is written on every request that touches it. Cookie
  sessions hit the 4 KB limit.
- Scaling path: prune entries per ViewSet, or document that the session backend must be DB or cache.

**Process-lifetime permission cache:**

- Current capacity: `ViewSet.default_permissions` is cached for the process once it finds permissions
  (`src/crud_views/lib/viewset/__init__.py:425-445`). Empty results are not cached (#151).
- Limit: permissions added at runtime (new custom permissions) stay invisible until a restart.

---

## Dependencies at Risk

**Django 4.2 is past end of support but still in the matrix:**

- Risk: Django 4.2 LTS left extended support in April 2026. `DJANGO_VERSIONS = ["4.2", "5.2", "6.0"]` (`noxfile.py:3`),
  the `django (>=4.2.0)` floor (`pyproject.toml:27`) and the classifiers (`pyproject.toml:14`) still advertise it.
- Impact: CI time is spent on an unsupported Django, and 4.2-specific compatibility code blocks newer APIs.
- Migration plan: drop 4.2 in the 1.0 release, raise the floor to `>=5.2`, and add a `### Breaking` CHANGELOG entry
  plus a `docs/migrating-1.0.md` note.

**Untested dependency floors with no upper bounds:**

- Risk: `pydantic (>=2.2.1)`, `django-tables2 (>=2.5.3)`, `django-filter (>=21.1)` and `django-crispy-forms (>=2.0)`
  (`pyproject.toml:26-35`) are only tested at their latest versions. Nox varies only Django (`noxfile.py:13-14`) and
  `uv.lock` is gitignored. A tables2 or filter major release can break users with no CI warning, and an old floor
  version can break without anyone noticing.
- Migration plan: add a nox "minimum versions" session (`uv pip install --resolution lowest-direct`) and raise the
  floors to versions that are actually tested.

**crispy-bootstrap5 and python-box as hard dependencies:**

- Risk: `crispy-bootstrap5` ties every install to Bootstrap 5 form templates even for non-Bootstrap themes.
  `python-box` is used only for attribute access in `src/crud_views/lib/settings.py:245-265`.
- Migration plan: move `crispy-bootstrap5` behind a `bootstrap5` extra, or keep it and document it as the default
  form pack. Replace `Box` with `types.SimpleNamespace` or a plain dict.

**jQuery (implicit, page-level):**

- Risk: `formset.js` expects a global `$` that the package does not ship or declare.
- Migration plan: #210.

---

## Missing Critical Features

**A stability policy for the theme surface:**

- Problem: `docs/development/stability.md` (93 lines) does not list `crud_views.lib.icons` (`register_icon_library`,
  `register_icons`, `render_icon`, `BOOTSTRAP_ICONS`, the 34 names), `crud_views.lib.messages.alert_data`,
  `cv_button_data`/`LEAF_KEYS`, the leaf template names or `cv.adapters` (#89).
- Blocks: a credible 1.0.0 promise to theme authors. Phase 4 of the follow-up plan closes it after phases 1A, 1C, 2 and
  3A settle the names.

**Detecting stale template overrides:**

- Problem: nothing warns when a project or theme override reads context keys that were removed (#211, #254).
- Blocks: safe upgrades for theme authors. Silent breakages so far: `cv_no_label`, `cv_container_tag`, old
  `tags/messages.html` keys, the `cv_get_filter_icon()` hook.

**Label mode for the filter toggle and form buttons:**

- Problem: the filter toggle is always icon-only (#262), and form buttons have no label mode (#257).
- Blocks: consistent toolbars in icon-heavy themes.

**Host icon placement for headings and modal titles:**

- Problem: #259 (low priority).

**Static type checking:**

- Problem: there is no mypy or pyright configuration, despite heavy annotations and Pydantic models
  (`pyproject.toml` `[tool.ruff]` only). `AUDIT.md` explicitly deferred this.
- Blocks: catching signature drift in `cv_get_context(..., *, location=)`-style overrides (#216) before users hit
  `TypeError`.

---

## Test Coverage Gaps

The figures come from the run on 2026-10-25. `tests/coverage.xml` is a stale July artifact (gitignored).

**Table columns:**

- What's not tested: `LinkChildColumn.render` and the `NaturalTimeColumn`/`NaturalDayColumn` constructors.
- Files: `src/crud_views/lib/table/columns.py` (68 %, lines 30-36, 40-44, 75-80, 85-90)
- Risk: child-link columns break without anyone noticing (they mutate `extra_context` per row).
- Priority: Medium

**Child views and ParentViewSet edge cases:**

- What's not tested: `src/crud_views/lib/views/child.py` (70 %, lines 22-24, 28, 35-37) and the error branches of
  `src/crud_views/lib/viewset/parentviewset.py` (79 %, lines 30, 32, 41-45).
- Risk: nested URL and parent-attribute resolution regress for unusual FK names.
- Priority: Medium

**Polymorphic invalid input:**

- What's not tested: a bad or excluded `polymorphic_ctype_id` on `PolymorphicCreateView` (see Known Bugs).
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`
- Risk: 500s, and creation of excluded subtypes.
- Priority: High

**Guardian viewset helpers:**

- What's not tested: `src/crud_views_guardian/lib/viewset.py` (82 %, lines 53-55, 59-61, 65-67).
- Risk: guardian-specific URL and permission helpers regress.
- Priority: Medium

**Security behaviour of the manage and delete views:**

- What's not tested: anonymous access to `ManageView` under `"yes"`/`"debug_only"`, a custom user model without
  `username`, and the absence of filtering for protected objects and counts in the delete confirmation.
- Files: `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/views/delete.py`
- Risk: information disclosure stays unnoticed.
- Priority: High

**Formset internals:**

- What's not tested: `src/crud_views/lib/formsets/inline_formset.py` lines 138-150 and
  `src/crud_views/lib/formsets/mixins.py` lines 83-86, 112-122, 174-175.
- Risk: nested save/delete edge cases on the code path that writes user data.
- Priority: Medium

**Other untested pieces:**

- `src/crud_views/management/commands/crud_views_show.py` (0 %, placeholder). `src/crud_views_workflow/checks.py`
  (84 %). `src/crud_views/lib/views/action_ordered.py` lines 8-15 (the import guard when `django-ordered-model` is
  missing). No suite runs under `python -O`, so assert-based guards are never exercised with asserts disabled.
- Priority: Low

---

*Concerns audit: 2026-10-25*
