I'll verify each plan against the current source, starting with the heading, identity, badge, and alias seams the plans depend on.
The plans match the current defects and are executable, but two mechanisms will fail their own gates unless the class-table accounting and heading class composition are made explicit.

## 06.5-01

**Summary.** The modal title is still `{% cv_heading "header" level=5 class="modal-title" %}{% cv_header_icon %} {% cv_header %}` (`src/crud_views/templates/crud_views/modal/content.html:3`), and `CvHeadingNode` always appends `h{template level}` when the rendered level changes (`src/crud_views/templatetags/crud_views.py:348-352`). Putting size and one host/element icon behind the existing class table is the right seam. The plan does not say whether those keys join `DEFAULT_BUTTON_CLASSES`, and that choice breaks the plan's own verify command.

**Strengths**
- Size stays independent of semantic level: the tag already reads `header_level` at render time and rejects unknown kwargs (`crud_views.py:339-376`). Adding `size=` fits that parser.
- Host versus element is already decided by `resolve_icon_name_class` (`src/crud_views/lib/icons.py:248-267`) before `render_icon` (`:231-245`). A suppressed host slot must not fall through to an inline icon; the plan says that.
- Layer-first lookup is required. `get_button_class` merges one dict (`src/crud_views/lib/button_classes.py:135-155`), so project shared cannot beat theme location unless `_heading_class` inspects layers separately. The plan does that and leaves button lookup alone.
- W362 only accepts keys in `DEFAULT_BUTTON_CLASSES` or action-mode keys (`button_classes.py:301-318`). Extending that check for optional heading keys is necessary.

**Concerns**
- **HIGH:** `tests/test1/test_button_classes.py:94-106` pins `len(EXPECTED_KEYS) == 74` and parses "The default table has 74 keys" from `docs/reference/buttons.md:147`. Task 01-02's verify runs `-k button_classes`. `docs/reference/buttons.md` is not in this plan or any later plan's `files_modified`. Adding the six size keys plus `heading:icon-host` also breaks `test_icon_host_default_slots`, which asserts exactly five `:icon-host` keys (`test_button_classes.py:310-313`). A parallel heading table avoids the count test but is not what the plan says.
- **MEDIUM:** `cv_heading` takes one `class` expression and does not interpolate `{{ }}` inside a quoted argument (`crud_views.py:349-351,371-374`). There is no class-join filter. "Attach `host_class` alongside `modal-title`" is not implementable as written. A trailing-space concat will fail `test_modal_title_is_the_header`, which requires `class == "h5 modal-title"` (`tests/test1/test_heading_level.py:161-165`). That test is not in this plan's verify, and the modal golden (`tests/test1/golden/heading_level/modal_detail.html:1`) still expects a leading space from the current template.
- **LOW:** `cv_header` is a rendering property (`src/crud_views/lib/view/base.py:427-433`). The plan correctly says to call the icon hook once.

**Suggestions**
- Decide in the task: either add the builtin heading keys to `DEFAULT_BUTTON_CLASSES` and put `docs/reference/buttons.md` plus the 74-key sentence in `files_modified`, or keep a separate heading table and say KEYS-04 stays 74.
- Add a tag argument or escaped joiner so structural classes and `host_class` are composed without a trailing space, and assert the exact `class` string the heading-level test already uses.

**Risk Assessment.** HIGH until the key-table fork is explicit. The modal path itself is sound.

## 06.5-02

**Summary.** The two host pages and the two sibling-icon layouts are the right migration set. The test host nests the title in `h5.d-flex > h3` (`tests/test1/app/templates/app/crud_views.html:13-22`). The demo hardcodes `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`). Split-card and striped-rows render the icon outside the heading (`layouts/split-card/group.html:8-9`, `layouts/striped-rows/group.html:4-5`). Other group layouts have no group icon.

**Strengths**
- Replacing the `h5` wrapper with a non-heading flex container fixes an invalid heading outline instead of styling around it.
- Keeping `mb-0` and moving only the size token into `size=3` matches D-01. Card and workflow headings already use `cv_heading` (`src/crud_views/templates/crud_views/tags/card.html:6`) and should stay on the implicit size path.
- Publishing fences that actually compile is the right migration proof. `docs/reference/templates.md:47-52` is the page that still teaches the old recipe.

**Concerns**
- **MEDIUM:** `HEADINGS` excludes `ancestor-or-self::h5[contains(@class, 'd-flex')]` (`tests/test1/test_heading_level.py:26-27`). After the wrapper is removed, the page title enters every card/workflow golden unless the xpath is changed first. Those golden files are not in `files_modified`. The same verify runs `heading_level`, including `modal_detail`, whose golden is also unlisted and will change if plan 01 drops the space in `modal/content.html:3`.
- **MEDIUM:** Split-card's icon is `text-default fs-5 me-2` (`split-card/group.html:8`). The plan's builtin group override is absent, and shared `icon-inline` is `me-2`. Default split-card icons lose size and color unless that is written down as the intended diff.
- **LOW:** `tests/test1/test_manage.py:273` collects `h3, h4`. A page title that becomes `<h1 class="h3">` drops out of that list. The manage page extends the test host, so confirm it still has other `h3`/`h4` nodes before treating a failure as unrelated.

**Suggestions**
- Change the heading-level exclusion and re-read `modal_detail.html` in this plan, or add those golden paths to `files_modified`.
- State the split-card default: preserve `fs-5 text-default` in `heading-group:icon-inline`, or record the shrinkage as the intentional markup diff.

**Risk Assessment.** MEDIUM. Site inventory is accurate; the golden exclusion is the part that will fail the stated verify.

## 06.5-03

**Summary.** This is the plan that fixes the reproduced defects. Triggers mark only `forloop.first` (`layouts/tabs-vertical/object_detail.html:8-14`) while panels are always `tab-pane fade` with no `active`/`show` (`layouts/tabs-vertical/group.html:2-5`). Both sides slugify `group.title`. The accordion root is the fixed `objectDetailAccordion` (`layouts/accordion/object_detail.html:2`, `group.html:15`). `render_object_detail` renders a new context with only `groups` and `layout` (`templatetags/crud_views_object_detail.py:38`), so outer loop state cannot reach the panel. Projecting identity once and passing it into `render_group` is the correct fix.

**Strengths**
- Not mutating `ResolvedGroup` (`resolvers.py:58-64`) is required. The same groups are rendered twice by layout tests (`tests/test1/od/test_layout_packs.py:61-72`).
- `getattr(group, "id", None)` lets this plan ship before plan 04 adds the field.
- Standalone `render_group` currently emits `data-bs-parent="#objectDetailAccordion"` with no such parent (`accordion/group.html:15`). Omitting that attribute is a real fix.
- Normalizing only generated IDs in `od_accordion.html` is right. `_headings()` serializes the button, including `data-bs-target` (`tests/test1/golden/heading_level/od_accordion.html:2`). Layout smoke tests key off markers, not IDs (`test_layout_packs.py:48-67`).

**Concerns**
- **MEDIUM:** `render_group` also starts a fresh context (`crud_views_object_detail.py:54`). The parent template must pass `presentation` as a tag argument; the child template cannot see the parent's loop variable. The plan says this, but the tag signature change has to keep the current positional `group` call working for the seven packs until each template is migrated.
- **MEDIUM:** `tabs-vertical/object_detail.html` loads only `crud_views_object_detail` (`:1`). `cv_heading_icon` will live in `crud_views`. The plan never says to add `{% load crud_views %}`.
- **LOW:** `tabindex=0` on every panel is broader than the tabs pattern when the panel contains links (`test_layout_packs.py:24-30`). Plan 08 should assert where Tab lands, not only that it leaves the tablist.

**Suggestions**
- Show the exact `{% render_group %}` call and the dict `render_group` passes to the layout template.
- Add the missing `{% load crud_views %}` to the tab and accordion templates in the task action.

**Risk Assessment.** MEDIUM. The projection design matches the code. The remaining risk is template plumbing, not the ID formula.

## 06.5-04

**Summary.** Stable identity belongs on config and the view, not on slugified titles. `PropertyGroupConfig` has no `id` (`config.py:56-62`), `resolve_group` copies title/description/icon/properties only (`resolvers.py:246-253`), and the content template calls `render_object_detail` with no component id (`view_detail.content.html:3`). The collision boundary is the hard part, and the plan names it more carefully than a "use render_context" handwave.

**Strengths**
- Appending `ResolvedGroup.id` with default `None` keeps existing keyword constructors (`test_heading_level.py:45`, `test_layout_packs.py:11-33`).
- Rejecting unsafe tokens without trim/suffix matches D-07. A before-validator on the config model is the same layer as the existing property normalizers (`config.py:64-77`).
- `cv_sources` is unrelated; this plan correctly does not invent URL-fragment activation.
- Requiring Django 4.2, 5.2, and 6.0 for the scope tests is justified: the registry is Django-internal.

**Concerns**
- **MEDIUM:** `RenderContext.get`/`__setitem__` see only `dicts[-1]` (`django/template/context.py:192-200` in the 4.2 env). `Template.render` pushes a fresh frame and pops it. Storing on the current frame misses sibling includes. Storing on `dicts[0]` (the builtins dict, `context.py:32-33`) survives `Context` reuse and false-collides, which the plan forbids but an executor will do if they call `setdefault`.
- **MEDIUM:** `tpl.render({...}, request)` builds a new `Context` (`crud_views_object_detail.py:38`). Nested tags inside the layout do not share the caller's render-context. The private scope object must be an explicit template variable, and nested tags must prefer that variable over a new frame. The plan says "transport" but does not name the variable or the lookup order.
- **LOW:** `Context.__copy__` shares render-context dict objects (`context.py:157-159`). An isolated `{% include only %}` can still see a registry stored on an earlier frame object. The include/inheritance tests are what make this safe; they are specified, not optional.

**Suggestions**
- Specify: walk `context.render_context.dicts`, skip index 0, store on the earliest remaining frame only while `push_state` is active, and pass that scope object into the fresh render dict under a private name that `render_object_detail` reads before allocating a new scope.
- Validate the full projected ID set before `tpl.render`, so a colliding component raises `ImproperlyConfigured` with no partial markup from that call.

**Risk Assessment.** MEDIUM. The contract is right. A wrong frame choice will pass a single-template test and fail the include cases the plan already requires.

## 06.5-05

**Summary.** Page-load keyboard can work once the first pill has `.active` and `data-bs-toggle="pill"`, because Bootstrap constructs the active toggle on window load. Injected modal HTML cannot. `modal.js` already dispatches `cv:modal:loaded` and `cv:modal:unload` (`src/crud_views/static/crud_views/js/modal.js:23-24`), and `tooltip.js:32-55` is the right lifecycle analog. A marked initializer that only calls `Tab.getOrCreateInstance` is the correct amount of JS.

**Strengths**
- Registering through `register_assets` from `AppConfig.ready` matches the registry (`src/crud_views/lib/assets.py:56-68`). Core assets render first (`assets.py:99-101`), so `tabs.js` loads after `modal.js`.
- `crud_views_object_detail` is already installed in tests (`tests/test1/conftest.py:55`). `cv_sources()` reads the registry (`src/crud_views/lib/pipeline.py:127-141`), so a default bundle picks the file up without a core `javascript()` edit (`settings.py:302-312`).
- Not touching `modal.js` preserves the accepted focus owner. Repeat-init via `getOrCreateInstance` avoids a second keydown handler.
- The asset fixture clears `_REGISTRY` and restores it (`conftest.py:12-20`). Tests that use it will not see the new bundle unless they re-register. The plan's own asset test can register explicitly.

**Concerns**
- **MEDIUM:** `register_assets` raises on any existing key, including an identical one (`assets.py:66-67`). `ready()` runs at startup. A second `ready()` in the asset test raises unless `apps.py` compares the existing bundle and returns. The plan says that, and correctly does not swallow a conflicting path. The comparison has to use `get_registered()`, because this plan does not modify `assets.py`.
- **LOW:** Projects that pass an explicit `keys=` list to `cv_sources()` will not get `tabs.js` until they add the bundle key. Plan 09 should say that; this plan should not special-case it in core settings.
- **LOW:** Keeping `data-bs-toggle="pill"` is correct for clicks. The custom initializer must not call `show()`, or it will steal selection on re-init. The plan says that.

**Suggestions**
- In `ready()`, if `crud_views_object_detail` is already registered with the same js tuple, return; if it is registered with a different tuple, let `register_assets` raise.
- Test root-itself matching. `tooltip.js:27` only queries descendants.

**Risk Assessment.** LOW. The lifecycle is copied from a working neighbor, and the duplicate-registration edge is named.

## 06.5-06

**Summary.** Badge CSS is one function of value and config (`resolvers.py:94-110`): `None` value returns before the callback, a truthy `color_map` wins over fixed color, an empty map falls through, and `color is None` is the miss. Template choice is `badge_css` before explicit `template` (`crud_views_object_detail.py:80-86`). The stock badge already renders `prop.badge_css` and `prop.badge_label` (`types/default/badge.html:1`). Appending `badge_color` and `badge_pill` from that same result is the right change.

**Strengths**
- `resolve_property` already calls the CSS helper once (`resolvers.py:191-204`) and constructs `ResolvedProperty` by keyword. Appending fields does not break `ResolvedProperty(path=..., label=..., value=...)` in `test_templatetags.py` and `test_layout_a11y.py`.
- Preserving empty-string color (`text-bg-` because the check is `is None`, not truthiness) avoids a silent behavior change.
- A native recipe that reads `prop.badge_color` instead of parsing `text-bg-*` matches D-12 and D-14. No new `BadgeConfig` keys are needed (`config.py:18-27`).

**Concerns**
- **LOW:** `_resolve_badge_label` is a second walk (`resolvers.py:113-117`). The plan must not call `color_fn` again from a template or from a leftover `_resolve_badge_css` that does not share the private result. It says this; the callback-count test is the proof.
- **LOW:** An unresolved badge must leave `badge_color is None` and `badge_pill is False`, including a nonempty map miss. If the helper returns the requested pill flag even when color is `None`, native templates will draw a pill around ordinary values. The plan's "None/False unresolved" rule prevents that only if both fields are set from the same "no badge" branch.

**Suggestions**
- One private result object: `color`, `pill`, `css`. `resolve_property` assigns all three. Do not derive pill from `"rounded-pill" in badge_css`.

**Risk Assessment.** LOW. This is the narrowest plan and it tracks the existing branches.

## 06.5-07

**Summary.** `CardAction.no_label` is still a field (`src/crud_views/lib/view/card.py:11`), the after-validator only rejects it when it is true and combined with `label_mode` (`card.py:31-32`), and the runtime treats a truthy `no_label` as icon mode (`src/crud_views/lib/views/card.py:49-52`). `no_label=False` is accepted today (`tests/test1/test_card_action_label_mode_field.py:26-27`). Pydantic's default extra policy ignores unknown keys, so deleting the field without a before-validator would silently drop `no_label=False`. The plan's membership check is the right fix. The template guard is a separate `in ctx` check (`button_data.py:126-130`) and is fed page context via `context.flatten()` (`templatetags/crud_views.py:211`).

**Strengths**
- Presence, not truthiness, matches D-09, including `False` and `None`.
- The app fixture still constructs `CardAction(..., no_label=True)` (`tests/test1/app/views.py:79-80`). Migrating that fixture is required or the default suite cannot import views.
- Keeping singular/plural label-mode names and not setting `extra='forbid'` matches D-09 and D-15.
- `test_label_mode_docs.py:214-223` currently requires a resolution step containing `no_label=True`. The plan includes that test file.

**Concerns**
- **MEDIUM:** `docs/migrating-1.0.md:142` and `:157` still say `CardAction(no_label=True)` keeps working, and `:47` still points at the `cv_no_label` `ValueError`. Plan 07 updates the reference pages and leaves migration/CHANGELOG to plan 09. That split is declared, but any release cut between the plans would document both "removed" and "still works".
- **LOW:** `model_validate` of a non-mapping (an existing model instance) must not assume `data` is a dict. The plan's `isinstance(data, Mapping)` guard is the right shape; the task should say to return non-mappings unchanged.

**Suggestions**
- Keep one negative test that `no_label=False` raises and names `label_mode="icon"`, and one that an unrelated extra is still ignored.
- Do not grep the repo for the spelling `no_label`; migration prose and the negative test must keep it.

**Risk Assessment.** LOW. The removal is local, and the silent-ignore trap is explicitly closed.

## 06.5-08

**Summary.** Server tests cannot prove ArrowDown on a modal that was injected after `window` load. The existing runner re-execs under a pinned Node and binds a private loopback port (`tests/browser/conditional-formsets.cjs:1-32`, port 8144). A sibling runner on 8145 is the right shape. Bootstrap in the test host is the CDN build 5.3.3 (`tests/test1/app/templates/app/base.html:13-19`), which is what the keyboard claims have to load.

**Strengths**
- Keyboard-before-click is the right assertion. A click would construct a `Tab` and hide a missed `cv:modal:loaded` handler.
- Distinct page/modal component ids exercise plan 04's hook instead of a template-only fixture.
- The native case is correctly not a second tabs implementation. It checks escaped text and resolved `prop` fields.
- Explicit untested screen-reader and non-Bootstrap visual coverage matches D-16. DOM roles are not an AT certification.

**Concerns**
- **MEDIUM:** The runner is new code with a real browser, CSRF, and process cleanup. The plan describes the cases well and does not specify the server entry point beyond "existing pytest_configure/authenticated real package view patterns". `conditional_formsets_server.py` is the analog and should be the required read for auth, SQLite, and teardown, not only the cjs file. It is in `read_first` for task 08-01. That is enough if the executor follows it.
- **LOW:** CDN failure must fail the run. The plan says that. Do not stub `bootstrap.Tab` in this runner; that would duplicate the vitest plan.
- **LOW:** `tabindex=0` on panels (plan 03) can make "Tab exits the tablist" land on the panel rather than the next page control. Assert the focused element, not only `aria-selected`.

**Suggestions**
- Record the loaded Bootstrap script URL and a hash of `tabs.js` in the JSON report so a stale static file cannot pass.
- Await modal close before opener-focus assertions, as the plan says; do not assert focus in the same turn as the hide call.

**Risk Assessment.** MEDIUM. This is new harness code, but the acceptance cases are the ones the phase actually needs, and they are not inferred from mocks.

## 06.5-09

**Summary.** Copied tabs still cannot work after plan 03 unless they consume `presentation.control_id`, `panel_id`, and `selected`. The published recipes have to be executed, not grepped. Breaking entries must land next to `docs/migrating-1.0.md`, which still documents the alias as working (`migrating-1.0.md:142,157`). Phase 7 should receive names, not a stability classification. That split is right.

**Strengths**
- Fence execution with locmem overrides matches the requirement that docs are not the proof by themselves.
- Pairing each new Breaking entry with a named migration section matches the repo rule. Semantic badge fields stay additive unless an incompatible default appears.
- The public-surface handoff is scoped: heading keys, ID formula, stock marker, badge fields, alias removal. Phase 7 still owns stable/provisional/internal.
- Re-running the existing conditional lifecycle browser case is justified because plan 05 adds a document-level listener.

**Concerns**
- **MEDIUM:** Task 09-03's `<verify>` block only runs two narrow `-k` selections. The full 4.2/5.2/6.0 `pytest tests`, vitest, mkdocs, ruff, and browser commands sit in the plan-level `<verification>` section. An executor that treats `<verify>` as the gate will mark D-15 passed without those runs. The action text says to run them; the automated block does not.
- **MEDIUM:** No plan updates `docs/reference/buttons.md`. If plan 01 put heading keys in `DEFAULT_BUTTON_CLASSES`, this plan's docs selection (`heading_docs or badge_docs or label_mode_docs`) will not catch a stale "74 keys" sentence, but `test_button_classes.py:102-106` will, and it is also not in this verify block.
- **LOW:** `keys=`-filtered `cv_sources()` callers will miss `tabs.js`. The migration note should say the new bundle key, not only "redeploy static".

**Suggestions**
- Put the full-matrix commands in task 09-03's `<verify>` block, or state that a green task verify is not phase acceptance.
- Add `buttons.md` here if plan 01 grows `DEFAULT_BUTTON_CLASSES`.

**Risk Assessment.** MEDIUM. The documentation work is well scoped. The risk is claiming preservation from the narrow verify block.

## Cross-plan

Dependency order is sound. Wave 1 (01, 06, 07) does not share files. Plan 03 waits for 01 and 02 because all three touch heading behavior and 02/03 both edit `test_heading_level.py`. Plan 04 waits for 03 and 06 because 04 and 06 both edit `resolvers.py`. Plan 05 waits for the `data-cv-od-tabs` marker from 03. Plan 08 waits for the producers. Plan 09 is last.

The phase goals are covered: heading host/size (01–02), tab selection and IDs (03–05, 08), alias removal (07), badge semantics (06), and migration/handoff (02, 06, 09). Form-leaf, auth, and conditional contracts are not reopened. No plan edits `modal.js` focus logic.

The cross-plan hole is the class table. Heading keys are a public theme surface (D-17) and `buttons.md:147` plus `test_button_classes.py:102-106` are the live guard. None of the nine plans list `docs/reference/buttons.md`.

The other cross-plan hole is class composition. Plans 01–03 all tell templates to append `host_class` to an existing literal class. `cv_heading` cannot do that with one quoted argument (`crud_views.py:349-351`).

**Overall risk: MEDIUM.** The plans are grounded in the current templates and would fix the reproduced tab, ID, alias, and badge defects. They are not safe to execute unchanged: settle the `DEFAULT_BUTTON_CLASSES` versus parallel-table choice, name the heading class joiner, and name the render-scope variable before implementation.
