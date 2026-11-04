# Example App Restructure Before 1.0 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganise `examples/bootstrap5` so each example teaches one feature: dissolve Showcase, drop the NEW
badges, and add Card View, Delete, Formsets + Conditional, Custom Form View, Label Modes, Messages, Disabled
Actions and a Theme pointer page, each linked to its docs page and back.

**Architecture:** Every example is its own Django app under `examples/bootstrap5/<app>/` following the existing
pattern (`apps.py`, `models.py` + migration if it has models, `views.py`, `urls.py` = `cv_x.urlpatterns`,
`seed.py` with idempotent `seed()`, `tests.py`), registered in `project/settings.py` `INSTALLED_APPS`,
`project/urls.py`, and with one `Feature` entry in `project/features.py`. Docs pages get an `!!! example "Try it
live"` box linking back to the app's landing page.

**Tech Stack:** Django 4.2–6.0, django-crud-views (core, object_detail, guardian), crispy-forms, django-tables2,
django-guardian, gettext (en + de), pytest + pytest-django + xdist.

**Spec:** `superpowers/specs/2026-11-04-examples-pre-1.0-restructure-design.md`

## Global Constraints

- **No changes under `src/`.** A package bug found on the way → stop, file a detailed GitHub issue, report back;
  the example works around nothing silently.
- Branch `feature/examples-pre-1.0-restructure` (no upstream; push with `-u origin feature/...` only when asked).
- Feature `title`, `description`, `about`, `look_at` and `DocRef.label` stay **English, untranslated**. Model
  verbose names, field labels, choices, table column headers, messages, button labels → `gettext_lazy`, with
  German translations (the `test_i18n.py` checks enforce this).
- Every `Feature.docs` page must contain an `!!! example "Try it live"` box linking to
  `https://django-crud-views-demo.onrender.com` + `reverse(feature.url_name)`; every anchor must be a real heading.
  Box wording follows the existing ones: `The [<Title> example](<url>) in the live demo shows this in action — log
  in as \`alice\` / \`alice\`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.`
- Seeded users are alice/alice and bob/bob from `project.seeding.ensure_demo_users()`; model perms via
  `project.seeding.grant_model_perms(user, Model, actions=...)`.
- All views use `project.views.BreadcrumbMixin` first in the MRO, like the existing apps.
- Wording in the Delete example: "blocked by objects you cannot see", never "not allowed".
- No customer project names anywhere.
- Final group membership (asserted by `project/tests.py::test_grouping_matches_spec`; each task updates it for
  its own app):

  ```python
  {
      "basics": ["library", "card_view", "nested", "resources", "delete_demo"],
      "forms": ["formsets", "conditional", "formsets_conditional", "custom_form"],
      "ui": ["breadcrumbs", "context_buttons", "action_menus", "label_modes", "flash_messages",
             "disabled_actions", "theming"],
      "extensions": ["workflow", "polymorphic_demo", "guardian_demo", "object_detail"],
  }
  ```
  The order in `FEATURES` within a group is the order in that dict.
- App names must not collide with Django app labels (hence `flash_messages`, not `messages`).

**Commands** (run from `examples/bootstrap5/`, with the repo venv active):

- tests: `uv run pytest -n auto -q` (one app: `uv run pytest -n auto -q <app>/tests.py`)
- migrations: `uv run manage.py makemigrations <app>`
- i18n: `task msg-make` then fill German `msgstr`s in `locale/de/LC_MESSAGES/django.po` (no empty, no
  `#, fuzzy`), then `task msg-comp`
- lint (repo root): `task format && task check`

**Per-task i18n step:** every task that adds or removes translatable strings ends with the i18n commands above and
`uv run pytest -q test_i18n.py` green before committing.

## Review Focus

1. **Bob's data leaking in the Delete example.** Alice's blocked page for "Office move" must not contain bob's task
   title anywhere — not in the alert, not in a cascade summary, not in counts (spec: bob's objects are `PROTECT`
   children only). Test in Task 5.
2. **Blocked delete via the modal and via a direct POST.** A confirmed POST on a blocked project must delete nothing
   (stock: 200 full page / 422 modal). Test in Task 5.
3. **Two ViewSets on one model.** Library's author URLs, breadcrumbs and detail links must still point at Library
   after Card View registers a second Author ViewSet (no URL-name or `cv_viewset` cross-talk). Test in Task 2.
4. **Conditional formset without JavaScript.** Posting the combined form with the toggle off must purge/skip the
   gated rows server-side, including their nested Speakers. Test in Task 7.
5. **Seed idempotency and reset.** `call_command("seed")` twice must not duplicate rows or Guardian grants in any
   new app (existing `test_seed_twice_is_idempotent` covers counts only for apps it lists — extend it in each task
   or assert in the app's own `tests.py`).

---

### Task 1: Spike — two ViewSets over one model (throwaway)

**Files:** scratch only (`/tmp/claude-1000/...scratchpad/` or an uncommitted app); nothing is committed.

- [ ] **Step 1:** In a scratch copy, add `cv_author_card = ViewSet(model=Author, name="author_card")` with a
  `CardListViewPermissionRequired` list (`cv_path=""`) and an `ObjectDetailViewPermissionRequired` detail, include
  its urlpatterns under `card-view/`.
- [ ] **Step 2:** Run `uv run manage.py check` and render `/library/author/`, `/library/author/<pk>/`,
  `/card-view/author_card/`, `/card-view/author_card/<pk>/` as alice.
- [ ] **Step 3:** Confirm: no system-check errors; Library links stay under `/library/`; card links stay under
  `/card-view/`; breadcrumbs name the right container.
- [ ] **Step 4:** Report the result. If anything breaks, file a GitHub issue (package bug) and switch Task 2 to
  a Book-only card ViewSet only if that works; otherwise stop and ask. Delete the scratch code.

### Task 2: Card View example (Basics)

**Files:**
- Create: `card_view/{__init__,apps,views,urls,seed,tests}.py` (no models; uses `library.models.Author`)
- Modify: `project/settings.py` (after `"library"`), `project/urls.py` (`card-view/`), `project/features.py`
  (entry right after Library), `project/tests.py::test_grouping_matches_spec`, `library/seed.py` (enough authors),
  `docs/reference/card-list-view.md` (Try-it-live box → Card View)

**Interfaces:**
- Produces: `card_view.views.cv_author_card = ViewSet(model=Author, name="author_card", icon_header=...)`;
  landing URL name `author_card-list` (confirm the exact generated name in Task 1 and use it as `url_name`).

- [ ] **Step 1: Failing tests** in `card_view/tests.py` (move/adapt from `showcase/tests.py::RecipeCardTest`):
  - `test_card_landing_page_renders_with_snippets`: 200, contains an author's name and `snippet-panels`.
  - `test_signed_order_single_combo`: contains `data-cv-action="submit-on-change"`,
    `<option value="-created_dt" selected>Newest first</option>` (html=True), no `name="dir"`.
  - `test_signed_order_applies`: `?order=last_name` vs `?order=-last_name` reverses two authors' positions.
  - `test_paginates_with_seed_data`: after `call_command("seed")`, the landing page has a page-2 link.
  - `test_library_links_unaffected` (Review Focus 3): Library author detail page contains
    `reverse("author-list")` and no `/card-view/` URL; card detail page contains no `/library/author/` update URL.
- [ ] **Step 2:** `uv run pytest -q card_view/tests.py` → FAIL (no module).
- [ ] **Step 3:** Implement `AuthorCardListView(BreadcrumbMixin, CardListViewPermissionRequired)` with
  `cv_path = ""`, `paginate_by = 6`, `cv_order_fields = [("-created_dt", _("Newest first")), ("created_dt",
  _("Oldest first")), ("last_name", _("Last name A-Z")), ("-last_name", _("Last name Z-A"))]`,
  `cv_order_default = "-created_dt"`, `cv_card_actions` with detail (primary, flex), update, delete (icon,
  tertiary); plus detail/create/update/delete views for `cv_author_card` modelled on Library's. `about` must say it
  is the same data as Library, listed as cards. Docs: `card-list-view.md` (anchor
  `signed-choices-single-combo-no-buttons`) and `list_view.md` is not needed. Make `library/seed.py` create ≥ 7
  authors so there are two card pages.
- [ ] **Step 4:** Update the Try-it-live box in `docs/reference/card-list-view.md` to the Card View URL.
- [ ] **Step 5:** `uv run pytest -n auto -q` → PASS (incl. `test_doc_links.py`, `project/tests.py`); i18n step.
- [ ] **Step 6:** Commit `feat(examples): Card View example over the Library authors`.

### Task 3: Remove the NEW badges

**Files:** `project/features.py` (drop `badge=` on Breadcrumbs and Conditional and the `Feature.badge` field),
`project/templates/project/home.html:28-30`, `project/templates/project/nav.html:24`,
`project/tests.py::test_badges_shown_in_dropdown` (delete), locale (`"NEW"` msgid goes away).

- [ ] **Step 1:** Add `test_no_badges_rendered` in `project/tests.py`: home page and a feature page contain no
  `class="badge text-bg-success`. Run → FAIL.
- [ ] **Step 2:** Remove field, kwargs, markup and the old test. Run `uv run pytest -n auto -q project` → PASS.
- [ ] **Step 3:** i18n step (obsolete msgid removed, no fuzzy left). Commit `chore(examples): drop the NEW badges`.

### Task 4: Move Showcase's ActionView docs link to Action Menus

The spec moves the "favorite" toggle to Action Menus. Action Menus already has the same kind of action
(`ChoreDoneView`: POST toggle, `cv_backend_only`, short label), so **no new action is added** (plan call, mirrors
the spec's rule for the fieldsets). Only the docs link moves.

**Files:** `project/features.py` (Action Menus `docs` += `DocRef(page="reference/action_view.md", label="ActionView —
custom actions")`, `look_at` mentions `ChoreDoneView` as the custom action), `docs/reference/action_view.md`
(Try-it-live box → Action Menus `chore-list`).

- [ ] **Step 1:** `uv run pytest -q test_doc_links.py` currently PASS; make the edits; run again → PASS
  (the new DocRef forces the box to point at `/action-menus/chore/`).
- [ ] **Step 2:** Commit `docs(examples): ActionView docs point at the Action Menus example`.

### Task 5: Delete example (Basics)

**Files:**
- Create: `delete_demo/{__init__,apps,models,views,urls,seed,tests}.py`, `delete_demo/migrations/0001_initial.py`
- Modify: settings, urls (`delete/`), features (last in Basics), grouping test,
  `docs/reference/delete_view.md` and `docs/reference/modals.md` (Try-it-live boxes),
  `docs/getting_started/demo.md` (add Delete to the "bob differs" list: per-object permissions like Guardian)

**Interfaces:**
- Models (all `gettext_lazy` verbose names):
  - `Project(title CharField, owner FK AUTH_USER_MODEL CASCADE, is_shared BooleanField default False)`
  - `Milestone(project FK Project CASCADE related_name="milestones", title)` — cascade children
  - `Task(project FK Project PROTECT related_name="tasks", owner FK AUTH_USER_MODEL CASCADE, title)` — protecting
- `cv_project = GuardianViewSet(model=Project, name="project")`, `cv_task = GuardianViewSet(model=Task,
  name="task")` (flat, not nested). `ProjectDeleteView` has `cv_show_related_objects = True`, `cv_modal = True`,
  and `cv_check_delete_protection(self) -> list[str]` returning
  `[gettext("A shared project cannot be deleted. Stop sharing it first.")]` when `self.object.is_shared`.
- Seed (`seed()`, idempotent via `get_or_create`, Guardian grants via `cv_project.assign_perm` /
  `cv_task.assign_perm` for view/change/delete to each object's owner):
  - alice `"Website relaunch"`: 2 Tasks owned by alice → case 1.
  - alice `"Office move"`: 1 Task `"Book the movers"` owned by **bob**, no grant to alice → case 2.
  - alice `"Annual report"`, `is_shared=True`, no tasks → case 3.
  - alice `"Old prototype"`: 2 Milestones, no tasks → deletable with cascade preview.
  - bob gets a project of his own so his list isn't empty.

- [ ] **Step 1: Failing tests** in `delete_demo/tests.py` (log in as seeded alice after `call_command("seed")`):
  - `test_case1_lists_own_blocking_tasks`: GET delete of "Website relaunch" contains
    `Deletion is blocked by protected relationships:` and both task titles, and no confirmation form
    (`name="delete"` absent).
  - `test_case2_hides_bobs_task` (Review Focus 1): GET delete of "Office move" contains
    `Other objects still reference this one` and does **not** contain `Book the movers` anywhere in the body.
  - `test_case3_business_rule`: GET delete of "Annual report" contains the shared-project message, no form.
  - `test_deletable_shows_cascade_preview`: GET delete of "Old prototype" shows both milestone titles and the form.
  - `test_blocked_post_deletes_nothing` (Review Focus 2): POST the confirmation to "Office move" (full page and
    with the modal header the package uses) → status 200 / 422, project still exists.
  - `test_modal_delete`: the delete link on the detail page carries the modal attributes `cv_modal` renders
    (copy the assertion style from `showcase/tests.py` if one exists, else assert on `data-cv-modal`).
  - `test_seed_idempotent` (Review Focus 5): seed twice → same counts of Project, Task, Milestone and
    `UserObjectPermission`.
- [ ] **Step 2:** `uv run pytest -q delete_demo/tests.py` → FAIL.
- [ ] **Step 3:** Models, migration, views (list/detail/create/update/delete for Project; list/detail for Task,
  Guardian `*PermissionRequired` variants; create views assign creator perms like
  `guardian_demo.views.DocumentCreateView.cv_form_valid`), seed, URLs, Feature entry. `about`: three blocked cases
  + one deletable; say case 2 is "blocked by objects you cannot see". `docs`: `delete_view.md` anchors
  `cascading-deletes-display`, `protected-objects`, `delete-protection`; `modals.md`.
- [ ] **Step 4:** Update the Try-it-live boxes in `delete_view.md` (new box at top, like other pages) and
  `modals.md` (replace Showcase); update `demo.md`.
- [ ] **Step 5:** `uv run pytest -n auto -q` → PASS; i18n step. If case 2 leaks bob's data with stock templates,
  that is a package bug → stop, file an issue, report.
- [ ] **Step 6:** Commit `feat(examples): Delete example — cascade preview, protection, hidden blockers`.

### Task 6: Remove the Showcase app

**Files:** delete `showcase/` entirely; modify settings, `project/urls.py`, `project/features.py` (entry),
grouping test, `docs/reference/object_detail_view.md` (drop the Showcase link from its box, keep Object Detail),
locale (recipe msgids go away). Leave the synthetic Showcase URL inside `test_doc_links.py`'s unit-test string —
it is test data, not a link.

- [ ] **Step 1:** `grep -rn -i "showcase\|recipe" examples/bootstrap5 docs README.md render.yaml --include=*` and
  list every hit; each must be removed or be the synthetic test string.
- [ ] **Step 2:** Delete and edit. Object Detail already shows labelled fieldset groups (`PRODUCT_DISPLAY`), so the
  fieldsets part is dropped (spec rule).
- [ ] **Step 3:** `uv run manage.py check` and `uv run pytest -n auto -q` → PASS; re-run Step 1's grep → only the
  synthetic string. i18n step.
- [ ] **Step 4:** Commit `chore(examples): remove Showcase; its parts live in Card View, Delete and Action Menus`.

### Task 7: Formsets + Conditional example (Forms)

**Files:** create `formsets_conditional/` (with models + migration); modify settings, urls
(`formsets-conditional/`), features (after Conditional), grouping test, Try-it-live boxes in
`docs/reference/formsets.md` and `docs/reference/conditional.md`.

**Interfaces:**
- Models: `Conference(name, with_billing Bool, billing_company blank/null, billing_vat_id blank/null,
  with_sessions Bool)`, `Session(conference FK CASCADE related_name="sessions", title)`,
  `Speaker(session FK CASCADE related_name="speakers", name)`.
- `ConferenceForm(ConditionalGroupModelForm)` with `cv_conditional_groups` toggling the billing fields via
  `ModelFieldToggle("with_billing")` (pattern: `conditional/views.py::RegistrationForm`).
- `cv_conference_formsets = FormSets(...)`: `sessions` first-level with
  `conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge")`; `speakers` nested
  under `sessions` (`parent` key), **no** `conditional` (E310). Pattern: `formsets/views.py` for nesting,
  `conditional/views.py` for the conditional.

- [ ] **Step 1: Failing tests:**
  - `test_create_with_billing_sessions_and_speakers`: POST management forms + 1 session + 2 speakers with both
    toggles on → 1 Conference, 1 Session, 2 Speakers saved.
  - `test_billing_cleared_when_untoggled`: update with `with_billing` off → billing fields saved as None/empty.
  - `test_sessions_purged_with_nested_speakers` (Review Focus 4): update an existing conference with
    `with_sessions` off (no JS, plain POST) → 0 Sessions and 0 Speakers for it.
  - `test_no_check_errors`: `call_command("check")` raises nothing (no E310).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement views (list/detail/create/update/delete, `FormSetMixin` on
  create/update), seed (2 conferences, one with sessions + speakers). `about` names the E310 rule and that this
  is the supported way to combine them. `docs`: `formsets.md`, `conditional.md` anchor
  `kind-2-conditional-formset` and the first-level limitation heading (use its real slug).
- [ ] **Step 4:** Boxes in `formsets.md` / `conditional.md` gain the new example (keep existing links).
- [ ] **Step 5:** Full suite PASS; i18n step; commit `feat(examples): combined formsets + conditional example`.

### Task 8: Custom Form View example (Forms)

**Files:** create `custom_form/` (model + migration); settings, urls (`custom-form/`), features (last in Forms),
grouping test, box in `docs/reference/custom_form_view.md`.

**Interfaces:**
- Model `Contact(name, email EmailField, last_reminded_dt DateTimeField null)`, `cv_contact = ViewSet(...)`.
- `ContactRemindView(BreadcrumbMixin, MessageMixin, CrispyViewMixin, CustomFormViewPermissionRequired)`:
  `cv_key = "remind"`, `cv_path = "remind"`, form with a required `note` CharField; `cv_form_valid` sets
  `last_reminded_dt = now()`.
- `ContactInviteView(... CustomFormNoObjectViewPermissionRequired)`: `cv_key = "invite"`, form with `email`;
  `cv_form_valid` creates a `Contact`. Both appear in the list's context actions.

- [ ] **Step 1: Failing tests:** remind POST sets `last_reminded_dt` and shows the success message; remind POST
  without `note` re-renders with an error and does not update; invite POST creates a contact; both pages 200.
- [ ] **Step 2–4:** Run → FAIL; implement + seed; docs anchors `basic-usage`, `non-object-view`; box.
- [ ] **Step 5:** Full suite PASS; i18n step; commit `feat(examples): Custom Form View example`.

### Task 9: Label Modes & Icons example (UI)

Read first: PR #305's changes to `docs/reference/buttons.md`, `action_menus.md` ("Context label-mode
resolution"), `context_buttons.md`.

**Files:** create `label_modes/` (model + migration); settings, urls (`label-modes/`), features (after Action Menus),
grouping test, boxes in `docs/reference/buttons.md`, `docs/reference/icons.md`, `docs/reference/settings.md`.

**Interfaces:**
- Model `Gadget(name)`; `cv_gadget = ViewSet(...)`.
- `GadgetListView`: `cv_list_actions_label_mode` gives `detail: "label"`, `update: "both"`, `delete: "icon"`;
  `GadgetDetailView`: `cv_context_actions_label_mode = {"list": "label", "update": "both", "delete": "icon"}`.
  So each page shows all three modes side by side.

- [ ] **Step 1: Failing tests:** on the list and detail page, the update button shows icon + visible label, the
  delete button has no visible label but an accessible name and a tooltip (assert on the markup #305 renders for
  icon mode — read its tests in `tests/test1/` for the exact attributes), the detail/list button shows a label
  without icon.
- [ ] **Step 2–4:** Run → FAIL; implement + seed; docs: `buttons.md` (variants heading), `icons.md`
  (`icon-values` or `default-table`), `settings.md` `label-mode-configuration`; boxes.
- [ ] **Step 5:** Full suite PASS; i18n step; commit `feat(examples): label modes and icons example`.

### Task 10: Messages and Disabled Actions examples (UI, two apps)

**Files:** create `flash_messages/` (no model; a `CustomFormNoObjectViewPermissionRequired` on a tiny ViewSet —
if a ViewSet needs a model, add `Notice(text)`), and `disabled_actions/` (model + migration); settings, urls
(`messages/`, `disabled-actions/`), features (after Label Modes, in that order), grouping test, boxes in
`docs/reference/messages.md`, `docs/reference/action_enabled.md`, `docs/reference/inaccessible_actions.md`.

**Interfaces:**
- `flash_messages`: a form with `level` ChoiceField (debug, info, success, warning, error) and `text`;
  `cv_form_valid` calls `messages.add_message(request, <level>, text)`; the page also renders one
  `{% cv_alert %}` inline. Lower `MESSAGE_LEVEL` is **not** changed (debug is shown hidden — say so in `about`).
- `disabled_actions`: `Ticket(title, locked Bool)`; `TicketUpdateView.cv_action_enabled(cls, user, obj=None)`
  returns `not (obj and obj.locked)`; `TicketUpdateView.cv_inaccessible_actions = "disable"`,
  `TicketDeleteView` keeps the default `"hide"` with the same `cv_action_enabled` — the two side by side.

- [ ] **Step 1: Failing tests:**
  - messages: POST each of info/success/warning/error → the redirected page contains `alert alert-<cls>` with the
    text (classes from `messages.md` "Levels" table: info→`alert-info`, success→`alert-success`,
    warning→`alert-warning`, error→`alert-danger`).
  - disabled actions: for a locked ticket the list row has a disabled update button and no delete button; GET/POST
    on the locked ticket's update URL is refused (assert the status the package returns, per `action_enabled.md`
    "Enforcement Points"); an unlocked ticket shows both.
- [ ] **Step 2–4:** Run → FAIL; implement + seed; docs anchors: `messages.md` `levels`, `a-single-alert-cv_alert`
  (verify slug); `action_enabled.md` `default-and-override-signature`; `inaccessible_actions.md` `configuration`.
- [ ] **Step 5:** Full suite PASS; i18n step; commit `feat(examples): messages and disabled actions examples`.

### Task 11: Theme pointer page (UI)

**Files:** create `theming/{__init__,apps,views,urls,seed,tests}.py` and
`theming/templates/theming/index.html`; settings, urls (`theming/`), features (last in UI), grouping test,
box in `docs/reference/theme.md` (and `templates.md`).

**Interfaces:**
- `theming.views.TABLER_DEMO_URL: str = ""` — the one constant to set to the onrender.com URL later.
- `ThemeIndexView(BreadcrumbMixin, generic.TemplateView)`, URL name `theming-index`; `seed()` is a no-op.
  Check first that the feature chrome (about box, code panel, breadcrumb, nav active state) works for a
  non-CrudView page; `project/tests.py::test_every_feature_landing_page_shows_breadcrumb` and
  `test_every_feature_page_shows_about` must pass for it. If the chrome only works for a CrudView, stop and report
  (choosing between a minimal ViewSet-backed page and changing the project chrome is the user's call).

- [ ] **Step 1: Failing tests:** page returns 200 for a logged-in user (like the other landing pages); it links to
  `DocRef(page=...).url` for theme, templates, buttons and icons; with `TABLER_DEMO_URL = ""` it shows the
  translated "coming soon" text and contains no `onrender.com` link apart from the site's own demo chrome; with
  `mock.patch("theming.views.TABLER_DEMO_URL", "https://example.onrender.com/")` it shows that link.
- [ ] **Step 2–4:** Run → FAIL; implement; docs refs `theme.md`, `templates.md`; boxes.
- [ ] **Step 5:** Full suite PASS; i18n step; commit `feat(examples): theme pointer page with Tabler placeholder`.

### Task 12: Changelog, docs build, final verification

**Files:** `CHANGELOG.md` (one `### Internal` entry under the unreleased section: example app restructure for
1.0 — list removed Showcase, new examples).

- [ ] **Step 1:** Add the entry. No `### Breaking`, `docs/migrating-1.0.md` untouched.
- [ ] **Step 2:** From repo root: `task format && task check` → clean.
- [ ] **Step 3:** `uv run mkdocs build --strict` (repo root) → no warnings about the edited pages.
- [ ] **Step 4:** In `examples/bootstrap5`: `uv run manage.py migrate && uv run manage.py seed && uv run manage.py
  seed` succeeds (the dev `db.sqlite3` is the user's — back it up first or point `DATABASES` at a scratch copy);
  `uv run pytest -n auto -q` → all pass. Repo root: `pytest tests -q -n auto` → pass (sanity; no `src/` changes).
- [ ] **Step 5:** `git diff --stat origin/main -- src/` → empty.
- [ ] **Step 6:** Commit `docs: changelog for the example app restructure`. Do not push or open a PR unless asked.
