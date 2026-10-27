---
phase: "06"
reviewers: ["fable-review", "grok-review", "gemini-review"]
reviewed_at: "2026-10-27T17:02:15.140505+00:00"
plans_reviewed: ["06-01-PLAN.md", "06-02-PLAN.md", "06-03-PLAN.md", "06-04-PLAN.md", "06-05-PLAN.md", "06-06-PLAN.md", "06-07-PLAN.md", "06-08-PLAN.md", "06-09-PLAN.md"]
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
model_sources:
  fable-review: "pinned"
  grok-review: "pinned"
  gemini-review: "pinned"
---

> Grok and Gemini share the OpenCode adapter; their agreement is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 06

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

- [x] REVISION_CONFLICT external-prerequisite/06-01 — required_property: Phase 1 and 2 prerequisites exist on authoritative main before spec/execution | conflicts with: ROADMAP.md Phase 6 main prerequisite; main remains 38b0100 | alternatives: retain main gate and wait for maintainer merge; explicitly authorize executing-branch prerequisite and update governing requirement | resolved: User selected working-branch verification (D-18); governing roadmap/context and plans updated; retain dependency evidence, spec-first and baseline-first gates.

<!-- gsd:plan-revision-conflicts:end -->

## Reviewer execution record

Cycle 2 reviewed current committed plans at `f637f5b` using the configured defaults unchanged. All three canonical lane invocations ran concurrently with the same untrimmed prompt. Fable and Grok completed their first attempts. Gemini reached the660000ms outer timeout with no final assistant text and produced a diagnostic stub; that attempt is not a review. One same-model, same-prompt, high-effort retry through the canonical runner used a temporary in-memory timeout extension to1200000ms and completed successfully. No installed runtime/config source was modified. No third attempt occurred.

| Identity | Outcome | Plan coverage | Evidence discount |
|---|---|---|---|
| fable-review | ok=true; stubbed=false | complete9/9 | None |
| grok-review | ok=true; stubbed=false | complete9/9 | None |
| gemini-review | ok=true; stubbed=false | complete9/9 | None |

Three real source-cited reviewer sections contribute to consensus. All previous HIGHs have plan-level closure; five current actionable non-HIGHs remain. One lone existence-class HIGH is reported as unconfirmed and excluded from the count, with its separate conditional design warning assessed against current tasks. No judgment HIGH is discounted for being raised by only one reviewer. The all-discounted fail-open exception is inapplicable. The writer-owned conflict block is preserved byte-for-byte.

## Claude Review (fable-review)

# Cross-AI Plan Review, Cycle 2: Phase 6 (Form-button leaf), plans 06-01 … 06-09

Reviewed read-only against the working tree of `introduce-gsd` at HEAD `f637f5b` (`main` and `origin/main` remain `38b0100`, the merge base), the installed `django-crispy-forms 2.6`, `crispy-bootstrap5 2026.3`, Django 5.2.14, Node v20.20.2, and the committed `package-lock.json`. No repository files were modified.

Headline: the round-1 HIGH findings are resolved in the current plans, and each resolution checks out against source. What remains is one MEDIUM gate-placement problem (06-01 makes a Node acquisition a wave-1 blocker for purely Python work), two MEDIUM implementation traps the plans do not yet name (06-02 `css_class` double-fold and `flat_attrs` conditional escaping), and a set of LOW items. Overall risk: MEDIUM.

## Prerequisite and round-1 closure check

- **D-18 (was H-MAIN)**: HEAD contains both Phase 1 and Phase 2 contracts: `default_label_mode` at `src/crud_views/lib/view/label_mode.py:84`, `FORM_KINDS` / `VARIANT_LOCATIONS` at `src/crud_views/lib/button_classes.py:209-210`, and the W362 form grammar at `button_classes.py:225`. The 06-01 precondition is satisfiable on the executing branch. Resolved.
- **H-LOCATIONS**: every consumer of `LOCATIONS` is now in 06-02 Task 1's file list. Source consumers are only `label_mode.py:93-96`, `settings.py:105,158-159`, `button_data.py:58` (all generic). Test consumers: `tests/test1/test_label_mode.py:6,59,67`, `test_action_label_mode_config.py:278,323`, `test_button_classes_templates.py:16,214`, `test_button_data.py:9`, `test_label_mode_docs.py:126` (with `docs/reference/settings.md:78,90`). All are listed. Resolved.
- **H-KEYSET / H-EARLY-UTILITIES**: `tests/test1/test_button_classes.py:90` asserts 71 and `buttons.md:145` says 71 with "icon-host row for four"; 06-02 moves the two utility keys plus count 73 and "five icon-host keys" into one task. Resolved.
- **M-PAYLOAD**: `tests/test1/test_crud.py:63` posts `{"confirm": True}`; 06-01 keeps it and adds a separate confirm-plus-`delete=Delete` POST. `DeleteView.post` never reads the `delete` key (`src/crud_views/lib/views/delete.py:199-222`), so the extra key is harmless. Resolved.
- **M-NAME**: `baseinput.html:2` in the installed pack slugifies names with `wordcount > 1`; 06-02 Task 2 replicates that rule. Resolved.
- **M-OWNERS**: `FormActions.render` does `context.update({...})` after its children (`crispy_forms/bootstrap.py:309`), leaving a persistent layer; `formset.html:42` nests `{% crispy x_form.form x_form.helper %}`. 06-03 Task 2 forbids fixed stack offsets and adds both cases. Resolved.
- **H-DIAGNOSTIC-CONTRACT / H-DELETE-STATIC / M-REGISTRY-OFF / M-POLYMORPHIC**: addressed explicitly in 06-06 (details below).

---

## 06-01

**Summary.** The plan correctly sequences prerequisite verification, spec authoring, and baseline-only commits, and its spec requirements track real crispy hazards I reproduced from the installed package. Its one structural weakness is that Task 1 now also owns Node runtime acquisition and a verification wrapper, and the plan makes that wrapper pass a condition for wave 1 completion. That couples the all-Python spec and golden work to network availability and to a runtime the project has never used.

**Strengths.**
- The D-18 precondition is verifiable with the plan's own commands: `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q` exercises the Phase 1 lazy floor (`label_mode.py:84-117`), E108 (`settings.py:142-172`) and the Phase 2 grammar (`button_classes.py:209-230`).
- The spec contracts the plan demands match source mechanics: `BaseInput.render` compiles the value as a template and pushes `{"input": self}` without popping (`.venv/.../crispy_forms/layout.py:255-258`); `BaseInput.__init__` sets `self.template = template or self.template` (`layout.py:247`), so the empty-template fallback rule is correct; `FormHelper.get_attributes` copies every non-underscore instance attribute into the crispy context (`helper.py:339-347`) and `get_response_dict` forwards them (`crispy_forms_tags.py:177-180`), which is the `view=None` shadowing the research reproduced.
- Baseline-first mirrors Phases 4 and 5 (`f6982bf`, `be7daa5`), and no existing golden contains a form control: `grep -rl 'type="submit"\|type="reset"' tests/test1/golden/` returns nothing, so unrelated goldens are safe.
- Task 3's "stable nonempty sort/order/direction query values" is necessary: `ListViewFilterFormHelper.__init__` adds the `order`/`dir` hidden inputs only when non-empty (`src/crud_views/lib/views/list.py:84-87`).
- Task 1's automated verify now checks for the nine named spec sections and a 40-hex SHA, closing the round-1 LOW.

**Concerns.**
- **MEDIUM (gate placement):** Task 1 says "Run bash .planning/.../06-js-verify.sh before wave 1 completes" and the wrapper "exits nonzero" on a missing runtime. Only Node v20.20.2 exists on PATH (`which -a node`: `~/.nvm/versions/node/v20.20.2/bin/node`, `/usr/bin/node`), while the lock pins `jsdom 30.1.2` and `vitest 5.0.3` with engines `^22.22.2 || ^24.15.0 || >=26.0.0` (`package-lock.json:32-50`, 799, 1506) and the installed `node_modules` is jsdom 29.1.1 / vitest 4.1.10. Acquiring Node 22/24 via nvm needs network access. If that fails, the plan records "a blocker (H-NODE)", but it is not stated whether the blocker halts wave 1. Waves 2 to 6 contain no JS gate; the first JS gate is 06-07. Making a Node download a precondition for committing a Python spec and five Python goldens is an ordering defect, not a safety gain.
- **LOW (machine-specific artifact):** `06-JS-RUNTIME.json` records absolute Node and `npm-cli.js` paths and is committed under `.planning/`. On any other machine the wrapper exits nonzero until the record is regenerated, but only 06-01 creates it.
- **LOW (task load):** Task 1 carries the prerequisite check, the full design spec (nine sections covering contracts from 06-02 through 06-06), the Node acquisition, lock verification with npm's bundled semver, and a bash wrapper. The estimate is 22k tokens for three tasks with confidence low. The spec alone is the phase's highest-leverage artifact and deserves an undistracted task.

**Suggestions.**
- Split the JS environment work into its own task (Task 4, or a 06-01b) whose failure is recorded, not blocking, until 06-07 where it becomes a hard gate.
- State in the wrapper that a missing `06-JS-RUNTIME.json` or stale paths trigger regeneration from the same acquisition procedure, so 06-07 on a different host is not a dead end.

**Risk Assessment: MEDIUM.** The design gate is right; the runtime gate is in the wrong wave.

---

## 06-02

**Summary.** This is the right first product tracer, and the mechanism claims are accurate against crispy 2.6. The round-1 ordering defects are fixed: Task 1 owns every `LOCATIONS` / key-set consumer, so the suite can be green at the end of wave 2. Two implementation traps in the adapter are not named in the plan and will produce either duplicate classes or an escaping hole if an executor follows the obvious path.

**Strengths.**
- The early form branch before `card = location == "card"` (`src/crud_views/lib/view/button_data.py:67`) is the correct cut; the action path reads `ctx["cv_url"]` / `ctx["cv_oid"]` at lines 139-141 and would `KeyError` for forms.
- `default_label_mode` raises for a location outside `LOCATIONS` (`label_mode.py:95-96`), so adding `"form"` to `LOCATIONS` and `LABEL_MODE_DEFAULTS` together, as Task 1 does, is required, and E108 then accepts `{"form": ...}` automatically (`settings.py:158`).
- Task 1 correctly switches `test_button_classes_templates.py:214` to `VARIANT_LOCATIONS`; that loop renders `action.html` with a `location:variant` key that `form` does not have.
- Template precedence is implementable exactly as D-05 to D-08 need: `_TableClassMixin` is first in the MRO (`src/crud_views/lib/crispy/buttons.py:21-30`), `TemplateNameMixin.get_template_name` handles `%s` (`layout.py:19-25`), and generated IDs come from `BaseInput.__init__` (`layout.py:237-241`).
- The utility keys `form:hidden-label` / `form:icon-host` are two-segment keys; `_action_key_parts` only accepts `form:<FORM_KIND>:<mode>` (`button_classes.py:223-226`), so they cannot widen W362.
- `icon_host_keys(icon, "form")` → `get_icon_host_class("form", ...)` → `get_button_class("form", "icon-host")` (`button_data.py:41-49`, `button_classes.py:152-165`) is why the host key must exist in this plan, and it does.
- `cv_type` validation against `submit`/`button`/`reset` matches crispy's `input_type` values (`layout.py:322,386,507`).

**Concerns.**
- **MEDIUM (`css_class` double-fold):** `BaseInput.__init__` appends `css_class` into `field_classes` after the mixin set the table classes (`layout.py:244-245`, `buttons.py:17-18`). The leaf then calls `{% cv_button_class "form" cv_key cv_label_mode %}` and appends `cv_css_class`. If `cv_css_class` is derived from `self.field_classes` or from the post-init state, the table classes appear twice and `test_submit_and_cancel_classes` fails on `"btn btn btn-secondary" not in html` (`tests/test1/test_crispy_buttons.py:35`). The plan says "cv_css_class suffix" but never says the raw constructor `css_class` must be captured before `super().__init__()`. Also note `get_button_class(location, slot, mode)` prefers `form:<kind>:<mode>` at render time (`button_classes.py:138-149`), so `field_classes` captured at construction (no mode) must not be reused on the layout path at all.
- **MEDIUM (`flat_attrs` escaping):** `BaseInput.__init__` precomputes `self.flat_attrs = flatatt(kwargs)` (`layout.py:248`). Django's `flatatt` uses `conditional_escape`, so a `mark_safe` kwarg value passes through unescaped. Task 2 promises SafeString attribute tests and "serialized extra attrs are escaped once separately", which is correct, but the plan does not say the layout path must ignore `self.flat_attrs` and serialize from the raw kwargs captured before `super().__init__()`. Say it, because the obvious shortcut is to reuse `flat_attrs`.
- **LOW (M-SLOT breaking surface):** `get_button_class` returns `""` for an unknown key today (`button_classes.py:148-149`), so `Submit(..., slot="formset:control")` inside a layout renders fine on 0.30. After this plan it raises `ValueError` at render. 06-08 Task 3 records this as Breaking, which is the right disposition; make sure the error message names the five kinds and the legacy `add_input` escape hatch.
- **LOW:** `str()` on a `SafeString` returns a `SafeString` (its `__str__` returns self). The 06-01 spec text says "plain str that has no SafeData trust marker"; the implementation must use something like `str.__str__(value)` or `"" + value`, not `str(value)`. Worth one sentence in the spec.

**Suggestions.**
- In Task 1's action, add: "capture `css_class` and raw `kwargs` before `super().__init__()`; the layout path never reads `self.field_classes` or `self.flat_attrs`."
- Add a test with `css_class="extra"` on a layout Submit asserting the class attribute equals exactly `btn btn-primary extra` (the existing `test_project_css_class_still_appended` at `test_crispy_buttons.py:86-96` is the pattern).

**Risk Assessment: MEDIUM.** Ordering is fixed; the remaining risk is two adapter details that the real-render tests will catch but that cost a rework cycle if unstated.

---

## 06-03

**Summary.** The whole-map resolver is a faithful copy of an existing, verified pattern, and the ownership rules are now anchored to the actual `render(form, context)` argument and to overlay provenance rather than stack position. The plan is sound; residual risk is the inherent subtlety of `Context.dicts` recovery, which the plan mitigates with the right real-crispy test matrix.

**Strengths.**
- `cv_first_inline_keys` returns the first non-`None` layer (`src/crud_views/lib/view/base.py:263-272`), and the list branch uses membership before the floor (`base.py:323-328`), so copying it for `form` preserves `{}`-suppresses-lower-maps and never reads an invalid strict floor for a named kind.
- `cv_get_action_label_mode` raises for any location other than context/list (`base.py:329`), so the `form` branch is a required, additive change.
- ViewSet validation is a decorator on two named fields (`src/crud_views/lib/viewset/__init__.py:105-111`); settings fields at `settings.py:67-68`. Both files are in this plan.
- The shadowing hazard is real and the recovery plan is correct: `BasicNode.get_render` copies the context and pushes `response_dict` (`crispy_forms_tags.py:107-113`), which includes every non-underscore helper attribute (`helper.py:339-347`, `crispy_forms_tags.py:177-180`), so `ListViewFilterFormHelper.view` (`list.py:68`) lands in the top dict even when `None`. The response dict always carries `is_formset` and `template_pack` (`crispy_forms_tags.py:153-175`), which is a usable provenance marker.
- Reading `form.cv_view` from the render argument is right: `list_filter.inner.html:15` renders `{% crispy filter.form filter.form.helper %}`, so `context["form"]` is not the filter form.
- `CrispyFormMixin.helper` builds a new `FormHelper` on every access (`form.py:41-48`); forbidding re-reads prevents a second action group.
- `CrispyViewMixin.get_form_kwargs` sets `cv_view = self` (`form.py:150-156`), so for package forms the owner is the view, which keeps 06-06's static checks consistent with runtime.

**Concerns.**
- **LOW (interim None setting):** Between 06-03 and 06-06, a project that sets `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE = None` would get `None` from `cv_first_inline_keys` (settings default is `{}` but the user value wins) and `key in None` raises `TypeError`. The plan's "Invalid selected values use shared strict/log fallback rather than membership crashes" covers this if the executor applies it to the settings layer too; state that `None` at the settings layer is treated as `{}` for resolution, with E106 reporting it in 06-06.
- **LOW:** The plan references "the package's private pushed context entry" that 06-05 creates two waves later. The fallback (provenance-based recovery) is defined, so this is only a note that 06-03's tests must pass without 06-05.

**Suggestions.** None beyond the two notes; the test matrix in Task 2 is the right shape.

**Risk Assessment: MEDIUM.** Correct design against real crispy mechanics; subtle enough that the real-render tests are the actual safety net.

---

## 06-04

**Summary.** Registry and leaf-coverage work is small and well grounded. The round-1 key-set defect is gone because 06-02 now owns the utilities; this plan correctly consumes them. The `icon=` sentinel design is sound and the slot-from-kind rule matches how delete styling already works.

**Strengths.**
- `DEFAULT_ICONS` has `delete`, `workflow`, `filter` (`src/crud_views/lib/icons.py:7,11,13`) and `BOOTSTRAP_ICONS` the same (`icons.py:46,50,52`); `save`, `cancel`, `filter-reset` are absent in both. `test_bootstrap_preset_covers_exactly_default_names` (`tests/test1/test_icons_registry.py:106`) forces both registries to move together, which the plan does.
- `CrispyDeleteForm.get_delete_button` merges `{"slot": "form:delete", **self.get_delete_button_kwargs()}` (`form.py:130`), so "kwargs override slot" is already the contract and `test_delete_button_kwargs_may_choose_the_slot` (`test_crispy_buttons.py:62-73`) pins it.
- `WorkflowForm` sets `submit_label` at the class level (`src/crud_views_workflow/lib/forms.py:20`); a class-level `submit_icon = "workflow"` is the matching seam.
- `icon=` must be consumed before `super().__init__()` or it lands in `flatatt(kwargs)` (`layout.py:248`); the plan states it is never serialized.
- `test_icon_host_leaves.py` currently parametrizes only context/list/card against the action leaf (lines 46-63); extending it to the form leaf is the right place.

**Concerns.**
- **LOW (overlapping leaf ownership):** 06-02 Task 1 already implements the three bodies, hidden label, title and tooltip, and 06-04 Task 1 "ensures the leaf reads mode classes" and "label mode suppresses all icon output and host classes". Two plans owning the same template behavior invites a rework commit if 06-02's leaf is already complete. Make 06-04 Task 1 test-only on the leaf unless a real-render case fails.
- **LOW (glyph choice):** `filter-close` already maps to `fas:filter-circle-xmark` / `bi:x-circle` (`icons.py:14,53`). Pick `filter-reset` glyphs distinguishable from the toggle's close state.

**Suggestions.** Scope Task 1's template edit to "only if a new real-render case fails"; name the three glyphs in the plan so the registry diff is reviewable.

**Risk Assessment: LOW.**

---

## 06-05

**Summary.** The filter-helper lifecycle plan is the most carefully reasoned in the set and every constraint it states is verifiable against the installed crispy. Both round-1 mechanics (falsy empty `Layout`, non-underscore attribute leakage) are now named explicitly. The remaining concern is a migration edge for subclasses that used to suppress the base inputs.

**Strengths.**
- Constructor wiring is exactly as claimed: `filterset.form.helper = self.formhelper_class(request=self.request, view=self)` (`src/crud_views/lib/views/mixins.py:319`) and `def __init__(self, view, request, form=None)` (`list.py:65`).
- `FormHelper.__init__` replaces `self.layout` whenever a form is passed (`helper.py:208-214`), so "do not pass form when preserving a declared layout" is the only way to keep `PublisherFilterFormHelper.layout` (`tests/test1/app/views.py:288-289`), `AuthorFilterFormHelper` in the example (`examples/bootstrap5/library/views.py:48-49`) and the documented subclass (`docs/reference/list_view.md:143-146`).
- `LayoutObject.__len__` returns `len(self.fields)` (`layout.py:38-39`) and crispy dispatches only `if helper and helper.layout` (`crispy_forms_tags.py:116`), so the plan's private truthy `Layout` subclass is required, not optional.
- `get_attributes` copies every non-underscore attribute except `layout` and `inputs` (`helper.py:339-347`), so the underscore rule for new state is correct and Task 2's "no new non-underscore lifecycle attributes leak" assertion is the right proof.
- Hidden inputs stay on `helper.inputs`; `whole_uni_form.html` includes `inputs.html` after `display_form.html`, and `inputs.html:1-13` wraps them in the `mb-3` block. The plan pins this ordering (L-HIDDEN-WRAPPER) rather than overriding the pack, consistent with the Out of Scope row in REQUIREMENTS.md.
- `render_layout` receives `node_context`, a copy (`crispy_forms_tags.py:110`), so pushing a private owner key there cannot leak into the page.

**Concerns.**
- **LOW (suppression migration):** A subclass that previously suppressed Apply/Reset by clearing `self.inputs` after `super().__init__()` will get them back through the layout. D-04's `get_form_actions() -> None` is the replacement; 06-08's migration section should name this case.
- **LOW (deepcopy of class layouts):** `copy.deepcopy` of a class-level `Layout` is fine before any render, but `render_field` stores `bound_fields` on layout objects during render. Deep-copy from the class attribute, never from an already-rendered instance layout.

**Suggestions.** Add the `self.inputs = []` legacy case to Task 2's compatibility matrix and to 06-08's recipe list.

**Risk Assessment: MEDIUM.** Mechanics understood; lifecycle code is where executors most often regress on repeated renders, and the plan's tests target exactly that.

---

## 06-06

**Summary.** Diagnostics reuse the real owners and the plan now states an explicit, documented form-only policy instead of reusing `cv_label_mode_checks` and hoping for E210. The static-reach rules are provider-aware (delete, workflow, filter helper, concrete polymorphic maps) and the dynamic fallback mirrors the action path. This is a well-scoped plan.

**Strengths.**
- All cited owners and IDs exist: E210 in `label_mode_check` (`label_mode.py:44-51`), E211/W291 in `cv_label_mode_checks` (`action_menu.py:46-72`), W292 in `cv_icon_mode_checks` with its narrow `except ValueError` (`buttons.py:387-440`), wiring at `base.py:186-197`, E106 loop at `settings.py:128-141`.
- The decision to not call `cv_label_mode_checks` for form maps is correct: `is_label_mode_map` fails the whole map on one bad value (`label_mode.py:37-41`), so that helper can only ever yield one E211, and its E211 message hard-codes card/context hints (`action_menu.py:58-61`) and W291 says "this view's actions" (`action_menu.py:71`).
- H-DELETE-STATIC is real and handled: `CrispyDeleteForm.helper` renders `get_delete_button()` + `get_cancel_button()`, never `get_submit_button()` (`form.py:132-143`), while inheriting `submit_icon` from the mixin.
- Static-only inspection is realistic: delete views set `form_class = CrispyDeleteForm` statically (`tests/test1/app/views.py:122,340,449`), the workflow view requires `form_class` via E230 (`crud_views_workflow/lib/views.py:46`), `formhelper_class` lives on the mixin (`mixins.py:309`), and `polymorphic_forms` is a class-level dict (`crud_views_polymorphic/lib/utils.py:35`, `tests/test1/app/views.py:565,573`).
- M-REGISTRY-OFF is grounded: `resolve_icon` treats a table value of `None`/`""` as switched off (`icons.py:187-198`).
- The test suite runs with `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:41`); the plan sets strict explicitly in both branches.

**Concerns.**
- **LOW (file overlap with 06-03):** Both plans list `settings.py`, `viewset/__init__.py`, `base.py`. Waves are sequential so there is no conflict, but 06-06 Task 1 says "ViewSet construction validators reject invalid maps" including finite keys, while 06-03 adds the validator "using existing patterns" (mode values only). Say in 06-03 that finite-key rejection arrives in 06-06, so an executor does not implement it twice differently.
- **LOW:** "non-strict logs one warning per render" differs from `_invalid_label_mode`'s once-per-process register (`label_mode.py:28-30,74-81`) but matches the action path (`button_data.py:106-110`). Consistent with precedent; just document which policy applies.

**Suggestions.** Add one sentence to 06-03 deferring finite-key validation to 06-06.

**Risk Assessment: LOW to MEDIUM.**

---

## 06-07

**Summary.** The JS and floor validation targets the right seams and leaves production JS byte-identical unless a regression is demonstrated. The locked-environment gate is correct in principle; its feasibility depends on obtaining Node 22/24, which 06-01 now owns. The plan correctly rejects the old-runtime fallback, and the risk is environmental, not design.

**Strengths.**
- `modal.js:82` already uses `new FormData(form, submitter || undefined)`; `viewset.js:40` uses `closest("[data-cv-cancel-url]")`; `list.filter.js:57` binds `#filter-button-reset` by id. Nested icon/span clicks bubble to these naturally.
- `tests/js/modal.test.js:202` already dispatches `new SubmitEvent("submit", {submitter: button})`, so native submitter support is exercised on jsdom today; the plan adds the `FormData(form, button).get(name)` assertion that is currently missing.
- `list.filter.test.js:236-243` already covers encoded query retention on reset; Task 2 extends it to `type="reset"` inside a real form rather than inventing `preventDefault` semantics (`list.filter.js:42-54` has none).
- The nox pattern is simple to extend (`noxfile.py:6-19`), `uv` is on PATH (`~/.local/bin/uv`), and `.venv/bin/nox` exists. The plan keeps the matrix and skip logic.
- The Django 6 `format_html` finding is accurate: the repo's only call passes an argument (`src/crud_views/lib/icons.py:220`).

**Concerns.**
- **MEDIUM (environment):** Confirmed: lock engines `^22.22.2 || ^24.15.0 || >=26.0.0` (`package-lock.json:32-34`), installed node_modules at jsdom 29.1.1 / vitest 4.1.10, only Node 20.20.2 on PATH, `~/.nvm` present. Obtaining a compatible runtime is plausible but network-dependent. The plan's disposition (blocker, no fallback) is defensible; the gate location is the 06-01 issue above.
- **LOW:** Task 3 "same resolver transaction": the current session installs Django and the project in two `session.install` calls (`noxfile.py:13-14`). One `session.install("django~=X.0", "django-crispy-forms==2.0", "crispy-bootstrap5==2023.10", ".[polymorphic,workflow,ordered,test]")` achieves it. Whether crispy 2.0 / bootstrap5 2023.10 import cleanly under Django 6.0 is only inherited evidence (06-RESEARCH.md A1); the session is the test.

**Suggestions.** Write the single `session.install(...)` line into Task 3; record `process.version` and the two package versions in the summary table as the plan already demands.

**Risk Assessment: MEDIUM.** Environmental.

---

## 06-08

**Summary.** Documentation work is well targeted; the executable-recipe pattern exists (`tests/test1/test_pagination_docs.py:12-13,36-48` with `_section` / `TEMPLATE_FENCE`), and the doc-contract tests from Phase 1 are named so the executor can extend them rather than trip over them. The round-1 duplicate key-count edit is removed.

**Strengths.**
- `docs/reference/buttons.md:84-86` still states that crispy form buttons do not select a mode or render icons; Task 1 replaces it.
- `settings.md:78,90` are already updated in 06-02; Task 1 only verifies, resolving the double-edit concern.
- The Added-bullet guard (`test_label_mode_docs.py:367-369` requires exactly one bullet starting `- \`CRUD_VIEWS_LABEL_MODE_DEFAULTS\` sets`) is explicitly preserved.
- `action_menus.md` has per-location resolution sections (`:87,101,112`); adding a form section follows the Phase 1 "stated once per location" decision.
- Example settings have no `CRUD_VIEWS_LABEL_MODE_DEFAULTS` today (`examples/bootstrap5/project/settings.py:125-142`), so `{"form": "both"}` is a clean addition.
- `tooltip.js:5-8` and `javascript.md:95-107` list tooltip locations without `form`; both are now in the file list. The `integrity` field is for external URLs only (`src/crud_views/lib/assets.py:17-22`), so a comment-only edit to `tooltip.js` cannot break an asset hash test.
- No file overlap with same-wave 06-07.

**Concerns.**
- **LOW:** Task 1's verify runs only `test_label_mode_docs.py` and `test_button_classes.py`; the "render a documented form configuration proving both/icon output" case must live in `test_label_mode_docs.py` for the gate to see it. Say so.
- **LOW:** The migration section should include the legacy `self.inputs = []` suppression case from 06-05 and the `slot="formset:..."` layout rejection from 06-02 (the latter is already listed).

**Suggestions.** Name the test file for the configuration-recipe render; add the suppression case to the migration recipes.

**Risk Assessment: LOW.**

---

## 06-09

**Summary.** A sound closing plan: observed evidence only, unresolved items stay visible, human checks are separate, and the example gate now uses the URLconf-backed system-checks test. Its JS gate inherits 06-07's environmental dependency.

**Strengths.**
- Gates mirror `.planning/PROJECT.md` quality gates; the known `ruff format --check` redness on planning files (`STATE.md:114,130`) is anticipated rather than papered over.
- `examples/bootstrap5/project/tests.py:97-115` `SystemChecksTest` loads the URLconf before `run_checks()`, and `examples/bootstrap5/pytest.ini:2` sets `DJANGO_SETTINGS_MODULE = project.settings`, so the `cd examples/bootstrap5 && ../../.venv/bin/pytest project/tests.py::SystemChecksTest::...` command is runnable as written.
- `examples/bootstrap5/test_docs_sync.py` exists for the docs-sync gate.
- Baseline ancestry plus source-blob equality is the right proof for FORM-01; the three-way delete evidence (unchanged confirm-only POST, rendered control name/value, confirm-plus-submitter POST) is stated separately as M-PAYLOAD required.
- Browser automation is available in this environment (Playwright MCP), so the human-check row can be partially automated as the plan allows.

**Concerns.**
- **LOW:** The "FORM-01/FORM-02 unclassified classifier assumption" bookkeeping adds no verification value. Harmless.
- **LOW:** The `T-06-SC` dependency-install threat row is repeated in all nine plans although only 06-01 and 06-07 install anything. Noise, not risk.

**Suggestions.** None blocking.

**Risk Assessment: LOW** (conditional on 06-07's runtime).

---

## Cross-plan assessment

**Dependency ordering.** The serial waves are correct for file ownership, and the round-1 "red suite from wave 2 to wave 7" defect is fixed: every `LOCATIONS`, `LABEL_MODE_DEFAULTS` and `DEFAULT_BUTTON_CLASSES` consumer is in 06-02 Task 1. The one remaining ordering problem is inverted: 06-01 makes a Node ≥ 22 acquisition a wave-1 completion condition although the first JS gate is in wave 7.

**Scope.** Nine plans and 22 tasks for one feature is heavy but defensible for the phase the roadmap calls "highest risk". Over-engineering candidates: the semver-verifying bash/Node wrapper in 06-01 (a `node --version` assertion plus `npm ci` under the chosen runtime would give the same evidence), and the repeated `T-06-SC` row.

**Security.** The escaping design is correct and motivated by source (`layout.py:255`, SafeString `__str__` semantics, `flatatt` conditional escaping). Two things must be written down so an executor does not take the shortcut: the layout path must never reuse `self.flat_attrs` or `self.field_classes` from `BaseInput.__init__` (`layout.py:244-248`). Attribute names remain developer-authored, which the plans state.

**Performance.** No concern. `default_label_mode` reads settings per call (`label_mode.py:97`) for a handful of buttons per page; owner recovery walks a short `Context.dicts` list per button; polymorphic traversal is check-time only.

**Do the plans achieve the phase goals?** Yes, FORM-01 to FORM-13 and D-01 to D-18 are each owned by a task with a real-render or system-check verification, and the mechanisms the plans rely on exist in the installed crispy and the current source as cited above.

**Overall risk: MEDIUM.** Three edits would bring it to LOW to MEDIUM: move the 06-01 JS runtime gate out of wave 1 and make it blocking only at 06-07; add the "capture `css_class` and raw kwargs before `super().__init__()`, never reuse `flat_attrs` / `field_classes` on the layout path" sentence to 06-02; and add a one-line deferral of finite-key ViewSet validation from 06-03 to 06-06. The residual risk then sits where it should, in the crispy context-overlay recovery (06-03) and the filter-helper lifecycle (06-05), both of which are covered by real-render tests.


---

## OpenCode Review (grok-review)

I'll verify each plan against the current source, starting with the form-button contracts the plans depend on.
The contracts the plans cite are in the tree. Next I’ll check whether the planned edits match how those functions actually behave.
## 06-01

**Summary.** The spec-then-baseline order matches the code that has to be frozen: layout buttons still render through crispy `BaseInput.render`, filter controls still go through `add_input`, and Phase 1/2 contracts are present on this branch. The plan over-specifies one recovery mechanism that crispy does not provide, and its automated gate does not enforce the Node or git evidence the action requires.

**Strengths.**
- Phase 1/2 are real: `LABEL_MODE_DEFAULTS` is the three-location floor (`src/crud_views/lib/view/label_mode.py:23`), `LOCATIONS` is still `context/list/card` (`src/crud_views/lib/view/button_data.py:12`), and `FORM_KINDS` / `VARIANT_LOCATIONS` are already split (`src/crud_views/lib/button_classes.py:209-225`). W362 uses those sets, not `LOCATIONS`.
- Delete today posts only `{"confirm": True}` (`tests/test1/test_crud.py:63`); `DeleteView.post` never reads a submitter (`src/crud_views/lib/views/delete.py:199-216`). Keeping that POST and adding a separate `delete=Delete` case matches the actual view.
- Layout values are compiled in `BaseInput.render` (`crispy_forms/layout.py:255`); helper inputs skip that and include `baseinput.html` directly (`crispy_bootstrap5/templates/bootstrap5/inputs.html:9`). A baseline of real endpoints will show `<input>`, not `<button>`.
- Locked jsdom 30.1.2 requires Node `^22.22.2 || ^24.15.0 || >=26` (`package-lock.json:826-827`) while `package.json:16` says `>=20`. Rejecting a Node 20 pass is correct.

**Concerns.**
- **HIGH.** Task 1 tells the spec to identify the crispy helper overlay by "provenance/response metadata". Installed crispy has no such field. `BasicNode.get_render` copies the context and `update`s the helper attribute dict (`crispy_forms/templatetags/crispy_forms_tags.py:110-112`); `FormHelper.get_attributes` publishes every non-underscore attribute, including `view` (`crispy_forms/helper.py:340-346`). `FormActions.render` then `context.update`s and never pops (`crispy_forms/bootstrap.py:309`; Django `ContextDict` pops only in `__exit__`). A spec written to a nonexistent provenance key cannot be implemented as written.
- **MEDIUM.** Task 1's `<verify>` checks spec headings and a SHA regex, then pytest. It does not run `06-js-verify.sh`, does not require `06-JS-RUNTIME.json`, and does not check `git diff` for a clean `src/`. A Node failure is also wired into this task, so FORM-01 baselines cannot land if the isolated Node fetch fails, even though goldens do not need Node.
- **LOW.** A 40-hex SHA anywhere in the Prerequisite section satisfies the regex. It does not prove `git rev-parse HEAD` or that the recorded pytest actually passed.

**Suggestions.**
- In the spec, define the overlay as the nearest context dict that contains crispy's response keys (`template_pack`, `inputs` from `crispy_forms_tags.py:171-174`). Take the page `view` only from dicts below that overlay that are not themselves helper overlays. Do not search for provenance.
- Split Node acquisition from the golden commits. Keep the wrapper as a wave-1 artifact, but do not block baseline commits on it. Add the wrapper run and `git diff BASELINE^ BASELINE -- src` to `<verify>`.

**Risk Assessment.** MEDIUM. Dependency and baseline intent are right; the owner-recovery sentence will stall the spec.

## 06-02

**Summary.** The leaf plan matches the two crispy paths and the live key count. It will break existing location contracts unless two unstated assertions in `test_label_mode.py` are updated, and it under-specifies how to recover kwargs that `BaseInput.__init__` already consumes.

**Strengths.**
- `{"form": "both"}` is an E108 failure today (`tests/test1/test_action_label_mode_config.py:322-323`, `E108_LOCATIONS` at line 278). Moving that case when `form` joins `LOCATIONS` is required.
- `DEFAULT_BUTTON_CLASSES` is 71 keys (`tests/test1/test_button_classes.py:90`, `docs/reference/buttons.md:145`). Adding `form:hidden-label` and `form:icon-host` is 73. E363 already validates every `*:icon-host` format string (`src/crud_views/lib/button_classes.py:257-266`).
- `test_button_classes_templates.py:214-218` loops `LOCATIONS` into `action.html`. Switching that loop to `VARIANT_LOCATIONS` is necessary once `form` is a location.
- Name slugify is template-only and conditional (`baseinput.html:2`: `wordcount > 1` then `slugify`); generated ids always slugify in Python (`layout.py:237-241`). Comparing wire names to the pack, not to the raw constructor name, is the right contract.
- `tests/test1/test_crispy_buttons.py:23` only matches `<input>`. Layout pages will fail that helper as soon as the leaf ships; the plan's instruction to update those assertions is required.

**Concerns.**
- **MEDIUM.** `test_label_mode.py:137` parametrizes `"form"` as an invalid location that must raise. `test_label_mode.py:155` asserts `len(records) == 3` because `_resolved()` queries every member of `LOCATIONS` (`test_label_mode.py:59`). Task 1's verify shard omits `test_label_mode.py`, so the producing change can look green while that file is red.
- **MEDIUM.** `BaseInput.__init__` appends `css_class` onto `field_classes` and serializes kwargs with `flatatt` (`layout.py:244-248`). There is no raw kwargs dict after `super().__init__`. A render override that prints `field_classes` and also appends `cv_css_class` will double the suffix. Boolean and hyphenated attrs cannot be recovered from the already-escaped `flat_attrs` string.
- **LOW.** `icon=` is not in this plan's reserved-attribute list, but 06-04 consumes it and must not emit it. If the spec copies only the 06-01 list, `icon` leaks as an HTML attribute the way other kwargs do today.

**Suggestions.**
- Name `test_label_mode.py:137` and `:155` in task 1, and add that file to task 1's pytest command.
- Capture `css_class` and kwargs before `super().__init__`, following the keyword-only `slot` pattern in `src/crud_views/lib/crispy/buttons.py:16-18`. Build classes as table class, then suffix, then extra class, once.
- Add `icon` to the reserved set in the spec before 06-04.

**Risk Assessment.** MEDIUM. The rendering design matches crispy; the unstated test couplings and kwargs consumption are the ways it goes wrong.

## 06-03

**Summary.** Whole-map resolution should copy `cv_first_inline_keys`, not a call-time settings read. Owner selection is the right split, but the implementation instruction still depends on the provenance key that crispy does not set.

**Strengths.**
- `cv_first_inline_keys` returns the first non-None map and does not merge (`src/crud_views/lib/view/base.py:263-272`). Empty-map-then-floor is how list keys work (`base.py:323-328`). Reusing that for form is the FORM-11 contract.
- `cv_get_action_label_mode` rejects any location other than `context` or `list` (`base.py:329`). Form needs a new branch; bolting form onto the context target-view path would be wrong.
- Context/list maps are fields on the settings singleton (`src/crud_views/lib/settings.py:67-68`, `320`) and the ViewSet (`src/crud_views/lib/viewset/__init__.py:85-86`). Adding a third field the same way will not trip W280 if it is declared on `CrudView` (`src/crud_views/lib/check.py:347-355`).
- The formset row really passes an explicit helper: `{% crispy x_form.form x_form.helper %}` (`src/crud_views/templates/crud_views/formsets/formset.html:42`). Reading `cv_view` from the `render(form, context)` argument, not `context["form"]`, is the correct fix.
- `is not None` rather than truthiness matches D-11. A boolean test would treat a falsey ordinary view as absent.

**Concerns.**
- **HIGH.** Task 2 still says to identify the current invocation from "response metadata/provenance". That string does not exist in crispy. The nearest lower `view` is not the page view: `ListViewFilterFormHelper` sets `self.view` (`src/crud_views/lib/views/list.py:68`), and `get_attributes` copies it into the overlay (`helper.py:340-346`). An inner helper with `view=None` would then inherit the outer helper's view if the walk stops at the first `view` key. That breaks D-09 for embedded forms.
- **MEDIUM.** There is no settings refresh. `from_settings(...)` runs at class body time (`settings.py:13-15`, `67-68`). `override_settings(CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE=...)` will not change `crud_views_settings`. Existing tests monkeypatch the singleton (`tests/test1/test_action_label_mode_config.py:78-80`). `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is the exception: it is read at call time (`label_mode.py:54-58`). The action's "preserve the setting refresh mechanism" describes a mechanism this module does not have. Rebuilding the whole singleton on `setting_changed` would change unrelated captured fields.

**Suggestions.**
- Specify the discriminator in the 06-01 spec, then implement only that. Skip dicts that contain `template_pack` and `inputs` when resolving the page view. Use the private pushed key only for the package filter helper.
- Resolve form maps with `getattr(crud_views_settings, "form_actions_label_mode")` via `cv_first_inline_keys`. Test with `monkeypatch.setattr`, and state in the spec that `override_settings` does not refresh this map.

**Risk Assessment.** HIGH until the overlay discriminator is written against the actual context stack. The map semantics themselves are low risk.

## 06-04

**Summary.** Icon defaults and the three missing registry names match the registries and the slot/name split already in the form hooks. Utility keys correctly stay in 06-02. The remaining risk is forwarding an explicit empty icon through hooks that today do not have an icon argument.

**Strengths.**
- `save`, `cancel`, and `filter-reset` are absent from both registries; `delete`, `filter`, and `workflow` already exist (`src/crud_views/lib/icons.py:14-49`, `51-88`). The plan adds only the missing names.
- Kind is the slot, not the submitted name: delete is `Submit(..., slot="form:delete")` with `name="delete"` (`src/crud_views/lib/crispy/form.py:123-130`); cancel is `Button` with `name="reset"` (`form.py:75-82`); filter reset is also `name="reset"` (`src/crud_views/lib/views/list.py:73`). A slot/name mismatch test is testing a real collision.
- `resolve_icon` treats a `CRUD_VIEWS_ICONS` value of `None` or `""` as off (`icons.py:187-198`). Static and dynamic checks can share that result.
- `WorkflowForm` is a `CrispyForm` with no `submit_icon` (`src/crud_views_workflow/lib/forms.py:11-20`). A class attribute does not change its constructor.
- Host vs inline is already `icon_host_keys` (`button_data.py:41-49`). Label mode clearing the host class is the action-leaf rule (`action.html:2`, `button_data.py:134-135`).

**Concerns.**
- **MEDIUM.** `get_submit_button` passes only `name` and `value` (`form.py:56-63`). If the hook adds `icon=` only when `submit_icon` is truthy, `submit_icon=None` will not suppress the kind default. The behavior section requires suppression; the action does not say to forward `None`.
- **LOW.** `icon` must be popped before `BaseInput.__init__` (`layout.py:248`) or it becomes an HTML attribute. That is the same kwargs trap as 06-02, and `icon` is still missing from 06-01's reserved list.

**Suggestions.**
- Always pass `icon=self.submit_icon` / `icon=self.delete_icon` from the package hooks, including `None`. Let an explicit button `icon=` kwarg override that, then the kind default.
- Add one render assertion that `icon=None` produces no `icon` attribute in the HTML.

**Risk Assessment.** LOW. The registry and slot facts are solid; only None-forwarding is easy to miss.

## 06-05

**Summary.** Moving stock Apply/Reset into `FormActions` while leaving hidden fields on `helper.inputs` matches both crispy templates. The truthy-layout trick is necessary, not optional. Layout replacement is specified well enough to implement.

**Strengths.**
- The documented subclass is a class-level `layout = Layout(...)` (`docs/reference/list_view.md:143-146`). `FormHelper.__init__` does not copy it (`helper.py:208-214`). Appending on that object would leak across instances. Deep-copy per instance is the right fix.
- Passing `form` replaces a declared layout (`helper.py:212-214`). The mixin calls `formhelper_class(request=..., view=self)` with no form (`src/crud_views/lib/views/mixins.py:319`). Not adding a required `form` argument preserves that call.
- Empty `Layout()` is falsy because `LayoutObject.__len__` exists (`crispy_forms/layout.py:38-39`) and crispy renders layout only when `helper.layout` is true (`crispy_forms_tags.py:116`). A private layout with `__bool__` returning True is a real requirement, not an invention.
- Hidden inputs stay on `self.inputs` (`list.py:78-86`). `whole_uni_form.html` includes the layout, then `inputs.html` (`whole_uni_form.html:9-11`), and `inputs.html:2` wraps those inputs in `mb-3`. Visible actions moving ahead of that wrapper is pack behavior, not a bug.
- `get_attributes` skips underscore names (`helper.py:340-346`). Prefixing lifecycle state keeps it out of the template context.
- `#filter-button-reset` is what `list.filter.js:57` binds. Preserving the id is sufficient for the current handler.

**Concerns.**
- **MEDIUM.** Exactly-once appending only runs if crispy calls `render_layout`. A post-construction replacement that is an empty `Layout()` is falsy, so crispy will not call the override and the action group will not appear. Task 2 tests replacements that have fields; it does not say the replacement must be forced truthy before dispatch.
- **LOW.** `onReset` keeps only `sort`, `order`, and `dir` (`list.filter.js:46-49`). The helper writes `cv_order_param` / `cv_order_dir_param` (`list.py:80-85`). Server-side preservation of renamed params does not survive the reset click. That is existing JS, and this plan does not claim to change it.

**Suggestions.**
- Before dispatch, if the selected layout is falsy, wrap or replace it with the truthy layout subclass, including after a caller assigns `helper.layout`.
- State in the migration note that reset JS still keeps only `sort`/`order`/`dir`.

**Risk Assessment.** MEDIUM. The lifecycle design matches crispy; falsy replacements are the hole.

## 06-06

**Summary.** The diagnostic split is justified by the current check helpers, and the delete/polymorphic reach matches how those forms are actually selected. The plan is implementable if the new form checker does not call the context helper unchanged.

**Strengths.**
- `cv_label_mode_checks` reports E211 for any `is_label_mode_map` failure, including a bad mode value, then W291 only for unknown keys on that view attribute (`src/crud_views/lib/view/action_menu.py:46-72`). `is_label_mode_map` accepts any string key with a valid mode (`label_mode.py:37-41`). E210 today is the scalar check (`label_mode.py:44-50`). A form-only E210-per-entry rule is a new branch, and the plan says not to change the context/list helper. That reading matches the code.
- Settings E106 uses the same open map test (`settings.py:128-140`). Unknown form kinds will not fail E106 until this plan adds a finite-key check. The action does require that addition.
- ViewSet validation is the same open validator (`viewset/__init__.py:105-111`). Finite form keys need a separate validator. 06-06 owns that file.
- `cv_icon_mode_checks` is context-only and skips custom buttons (`buttons.py:387-429`). A separate form walker is the right extension. It is wired from `CrudView.checks` (`base.py:193-197`).
- `CrispyDeleteForm.helper` renders delete plus cancel, not `get_submit_button` (`form.py:132-141`). Checking `delete_icon` and not inherited `submit_icon` matches that property.
- `polymorphic_forms` is a class dict of model to form class (`tests/test1/app/views.py:565-568`; `get_form_class` needs a request, `src/crud_views_polymorphic/lib/utils.py:64-69`). Inspecting the dict without instantiating is the only static path that will not hit the database.

**Concerns.**
- **MEDIUM.** `cv_icon_mode_checks` returns immediately when the context map is malformed (`buttons.py:398-399`). A form checker that wraps all of `checks()` in one `except ValueError` would swallow E108/E210/E211. The plan says catch only around mode resolution. That constraint has to be local; a broad try around `check_viewsets` would hide the bugs this plan is adding tests for.
- **LOW.** W292 for a registry-disabled icon must call `resolve_icon`, not merely test that the semantic name is non-empty (`icons.py:190-198`). The plan says this; a name-only check would miss `CRUD_VIEWS_ICONS = {"save": None}`.

**Suggestions.**
- Put the `ValueError` handler only around `default_label_mode("form")` / the form resolver call, then continue to the next control. Let map checks yield first.
- Deduplicate polymorphic warnings per `(form class, kind)` on that view only, as written. Do not use a process-global set; `check_viewsets` is called more than once in tests.

**Risk Assessment.** MEDIUM. The policy matches the existing IDs. The failure mode is an over-broad exception handler, which the planned tests can catch if they call `check_viewsets` with a bad floor and a missing icon together.

## 06-07

**Summary.** Browser coverage targets the handlers that will actually see `<button>` elements, and the Node pin matches the lock. The crispy floor session is right in shape, but the local nox pattern will silently upgrade crispy if copied.

**Strengths.**
- `cvModalSubmit` already does `new FormData(form, submitter || undefined)` (`src/crud_views/static/crud_views/js/modal.js:75-82`). The gap is the test, not the handler. Nested clicks work for cancel via `closest("[data-cv-cancel-url]")` (`viewset.js:38-43`) and for reset via the id (`list.filter.js:57`).
- `format_html` in this tree is called with arguments (`src/crud_views/lib/icons.py:220`). Django 6 did not remove that form. The plan's investigation target is accurate.
- The wrapper re-check is the right gate: jsdom 30.1.2 will not run on the Node 20 floor declared in `package.json:16`.

**Concerns.**
- **MEDIUM.** `noxfile.py:13-14` installs Django, then extras, in two `session.install` calls. Extras will resolve current crispy (2.6 is what this environment has). The plan says one resolver transaction but does not show a single `session.install(...)` call. Copying the existing session will upgrade past 2.0 before the pin, or fail closed only if the executor notices.
- **LOW.** `onReset` does not call `preventDefault` (`list.filter.js:42-53`). A `type="reset"` button will reset fields and then navigate. That is current behavior for `<input type="reset">`. The new test should assert both, which the plan does. Do not add `preventDefault` to make the test easier.

**Suggestions.**
- One call: `session.install(f"django~={django}.0", "django-crispy-forms==2.0", "crispy-bootstrap5==2023.10", ".[polymorphic,workflow,ordered,test]")`. Print `importlib.metadata.version` for both crispy packages before pytest.
- Keep modal.js unchanged unless a real `<button>` submitter test fails. The current `FormData` call already passes the submitter through.

**Risk Assessment.** MEDIUM. JS scope is bounded. The floor session is the part that can report a false environment.

## 06-08

**Summary.** Doc updates track real stale sentences and the executable docs harness. Publishing the form diagnostic split here is appropriate only if 06-06's messages are already fixed. The example setting is a one-key addition.

**Strengths.**
- `docs/reference/buttons.md:84-86` still says form buttons do not select a mode or render icons. That sentence has to go or the phase docs contradict the leaf.
- `javascript.md:99-107` lists tooltip locations and omits `form`. `tooltip.js:6-7` has the same inventory. Runtime dispatch is already generic (`tooltip.js:27-28`), so a comment and table update is the right change.
- `test_label_mode_docs.py:126` compares the settings table cell to `LABEL_MODE_DEFAULTS`. After 06-02 that cell must include `"form": "label"`. Task 1 verifying rather than re-editing that cell is the right split.
- The example has no `CRUD_VIEWS_LABEL_MODE_DEFAULTS` today (`examples/bootstrap5/project/settings.py`). Setting `{"form": "both"}` does not overwrite other locations.
- Breaking/migration pairing is required by the repo rule, and the input-to-button change is real.

**Concerns.**
- **MEDIUM.** Task 1 must not describe E106 as already rejecting unknown form kinds. Today it does not (`label_mode.py:37-41`, `settings.py:132`). The published text has to match the 06-06 branch, including "W291 only on the view attribute" and "settings use E106 only after the finite-key extension".
- **LOW.** `test_label_mode_docs.py:145-153` asserts an exact knob set. Adding a form row without updating that expected dict fails the docs suite. The plan says extend the assertions; the exact dict is the one that will fail.
- **LOW.** `tooltip.js` is a product file in a docs plan. A comment-only edit is fine; a logic edit would overlap the 06-07 "handlers stay byte-identical unless a test fails" rule. The plan already forbids a logic change.

**Suggestions.**
- Quote the new E210/E211/W291 sentences from the tests in 06-06, not from the old `cv_label_mode_checks` message (`action_menu.py:57-61`), which mentions card and context scalars.
- Point the migration at layout-only `ValueError` for unknown slots. Legacy `add_input` still renders through `inputs.html:9` and must stay quiet.

**Risk Assessment.** LOW. Documentation scope is tied to code that the earlier plans actually change.

## 06-09

**Summary.** Closing on full pytest, the example URLconf check, and separate delete-payload evidence matches the current tests. Acceptance still depends on 06-01 producing ancestry that its own verify command does not check.

**Strengths.**
- `SystemChecksTest` imports the URLconf before `run_checks` (`examples/bootstrap5/project/tests.py:97-114`). That is the right example gate. Bare `manage.py check` would miss unregistered view modules, and the plan no longer uses that.
- Unrelated golden drift is a real risk because later plans update only `tests/test1/golden/form_buttons/`. Requiring source-blob equality for the baseline commits is the right check.
- Human browser checks are explicitly pending until observed. That avoids sealing on vitest alone.
- The two unclassified probe rows are process noise. Keeping them visible does not weaken FORM-01 or FORM-02, which have ordinary tests.

**Concerns.**
- **MEDIUM.** Task 1 can record "baseline ancestry proved" only if 06-01 actually committed src-clean baselines. 06-01's automated verify does not check that. This plan should fail closed when the recorded SHA is not an ancestor or when `git diff SHA^ SHA -- src` is non-empty, not when the summary says it is empty.
- **LOW.** `pytest tests -n auto` will not run `crispy_floor` or the JS wrapper. Those gates are listed separately. The task text should cite their summary exits, or a green Python suite will be treated as phase acceptance.
- **LOW.** Browser checks need a running example against the example settings' `form=both`, then temporary label and icon floors. The plan says that, but it does not say to restart from the example settings rather than the test project's icon/label floors.

**Suggestions.**
- Make the ancestry check a command in `<verify>`, not a prose step: `git merge-base --is-ancestor` plus empty `git diff` for `src/` on each baseline SHA.
- Record `06-js-verify.sh` and `nox -s crispy_floor` exits in `06-VALIDATION.md` before marking FORM-06/FORM-08 accepted.

**Risk Assessment.** MEDIUM. The gate list is complete; it can still seal on summaries from earlier plans whose own verifies were narrower than their actions.

## Cross-plan

The set covers FORM-01 through FORM-13 and D-01 through D-18 without a second public rename. Verified mechanisms that the plans get right: layout versus `add_input` (`inputs.html:9` versus `BaseInput.render`), falsy empty layouts (`layout.py:38-39`, `crispy_forms_tags.py:116`), whole-map resolution (`base.py:263-272`), the 71-key table, and the Node 22 lock versus the Node 20 manifest.

The blocking gap is owner recovery. 06-01 and 06-03 both require provenance crispy does not attach. Until the spec names a discriminator based on the helper attribute dict and tells the page-view walk to skip other helper overlays, embedded `view=None` will borrow the outer helper's view (`list.py:68`, `helper.py:340-346`).

Second, form maps are not call-time settings. Copy the singleton (`settings.py:320`). Do not invent a refresh, and do not test them with `override_settings` alone.

Third, 06-02 must update `test_label_mode.py:137` and `:155` in the producing task, and capture kwargs before `layout.py:244-248`. 06-07 must pin crispy in one `session.install`, not the two-call pattern at `noxfile.py:13-14`.

Overall phase risk: **MEDIUM**, driven by one HIGH specification hole in owner recovery. The rest is executable against this tree if those three corrections are written into the spec before 06-02 starts.


---

## OpenCode Review (gemini-review)

# Cross-AI Plan Review — Phase 6 (`06-01` to `06-09`)

## 06-01

### 1. Summary
Plan `06-01` establishes the Phase 6 design specification (`06-SPEC.md`), sets up the isolated Node runtime verification wrapper (`06-js-verify.sh` and `06-JS-RUNTIME.json`) to reconcile the local Node/npm mismatch before Wave 1 completes, and captures five before-change golden baselines (`create`, `update`, `delete`, `workflow`, `filter`) in baseline-only commits prior to any `src/` edits. Against the repository state, the Phase 1 and Phase 2 prerequisites required by D-18 are already present on the working branch (`src/crud_views/lib/view/label_mode.py:23,84-117` and `src/crud_views/lib/button_classes.py:209-236`), and the plan's separation of confirmation-only delete POSTs from clicked-submitter POSTs accurately reflects `src/crud_views/lib/views/delete.py:199-223` and `tests/test1/test_crud.py:55-68`.

### 2. Strengths
- **Working-branch prerequisite verification (D-18) matches live code:** `src/crud_views/lib/view/label_mode.py:23,84-117` already implements `LABEL_MODE_DEFAULTS` and `default_label_mode(location)`, and `src/crud_views/lib/button_classes.py:209-236` already splits `VARIANT_LOCATIONS` and `FORM_KINDS` in `_action_key_parts()`. Task 1's pytest gate (`tests/test1/test_label_mode.py`, `tests/test1/test_action_label_mode_config.py`, `tests/test1/test_button_classes.py`) directly exercises those contracts.
- **Accurate crispy wire-name and ID contract in the spec:** `crispy_bootstrap5/templates/bootstrap5/layout/baseinput.html:2,6` emits `name="{% if input.name|wordcount > 1 %}{{ input.name|slugify }}{% else %}{{ input.name }}{% endif %}"` while `crispy_forms/layout.py:237-241` sets `self.id = css_id or f"{self.input_type}-id-{slugify(self.name)}"`. Task 1 explicitly requires preserving both rules in `06-SPEC.md` without calling `BaseInput.render()` (`crispy_forms/layout.py:255`, which evaluates `self.value` as a Django `Template`).
- **Truthful delete POST baseline:** `src/crud_views/lib/views/delete.py:204` (`self.cv_form_is_valid(context)`) validates `CrispyDeleteForm` (`src/crud_views/lib/crispy/form.py:121`, `confirm = BooleanField(...)`) regardless of whether `"delete": "Delete"` is in the POST dict, and `tests/test1/test_crud.py:63` currently posts `{"confirm": True}`. Task 2 preserves `test_crud.py:63` unchanged and adds a separate `{"confirm": True, "delete": "Delete"}` regression in `tests/test1/test_form_buttons_golden.py`.
- **Deterministic filter hidden-input baseline capture:** `src/crud_views/lib/views/list.py:77-87` always adds `Hidden("sort", sort)` to `self.inputs`, but only adds `Hidden(order_param, order)` and `Hidden(dir_param, direction)` when `order` and `direction` are non-empty in `request.GET`. Task 3 explicitly passes non-empty `sort`/`order`/`direction` query parameters when capturing `tests/test1/golden/form_buttons/filter.html` so all three hidden inputs are pinned.

### 3. Concerns
- **LOW — Task 1 `<verify><automated>` omits the JS wrapper gate it creates:** In `06-01-PLAN.md:76-94`, Task 1's `<action>` creates `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json` and `.planning/phases/06-form-button-leaf/06-js-verify.sh` and instructs to run `bash .planning/phases/06-form-button-leaf/06-js-verify.sh` before Wave 1 completes. However, Task 1's `<verify><automated>` block (`06-01-PLAN.md:126`) only checks `06-SPEC.md` sections and runs pytest, omitting `bash .planning/phases/06-form-button-leaf/06-js-verify.sh`. If the wrapper script has a syntax or path bug, Task 1's automated verification command would still exit 0 and defer failure until Wave 7 (`06-07`).
- **LOW — `node_modules` backup location during `npm ci`:** `06-01-PLAN.md:78-79` instructs to restore locked packages with `npm ci` under the isolated Node runtime while "preserving existing node_modules in a uniquely named backup until restoration succeeds". If that backup directory is created inside the repository root and not removed after `npm ci` succeeds, or if `npm ci` modifies tracked/untracked state unexpectedly, later cleanliness checks in `06-09` could see stray artifacts.

### 4. Suggestions
- Append `&& bash .planning/phases/06-form-button-leaf/06-js-verify.sh` to Task 1's `<verify><automated>` command (`06-01-PLAN.md:126`) so Wave 1's automated gate directly proves the JS runtime wrapper works.
- Place any temporary `node_modules` backup outside the repo root (e.g., under `/tmp`) and remove it immediately once `npm ci` and `06-js-verify.sh` succeed.

### 5. Risk Assessment
- **LOW:** `06-01` modifies no production code under `src/` and cleanly gates all subsequent waves on `06-SPEC.md`, the JS verification wrapper, and baseline-only golden commits.

---

## 06-02

### 1. Summary
Plan `06-02` delivers the core form-button rendering tracer: adding `"form"` to `LOCATIONS` and `"form": "label"` to `LABEL_MODE_DEFAULTS`, adding utility slots `form:hidden-label` and `form:icon-host` to `DEFAULT_BUTTON_CLASSES` (71 → 73 keys), updating all direct location/key consumers in the same wave, creating `src/crud_views/templates/crud_views/tags/button/form.html`, and overriding `render()` on `Submit`, `Button`, and `Reset` in `src/crud_views/lib/crispy/buttons.py` so layout-rendered buttons bypass `BaseInput.render()` template evaluation while legacy `helper.add_input()` controls continue rendering via crispy's `inputs.html`.

### 2. Strengths
- **Atomic update of `LOCATIONS`, `LABEL_MODE_DEFAULTS`, and `DEFAULT_BUTTON_CLASSES` consumers:** Adding `"form"` to `LOCATIONS` (`src/crud_views/lib/view/button_data.py:12`) and `"form": "label"` to `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23`) immediately affects `tests/test1/test_action_label_mode_config.py:278,323` (`E108_LOCATIONS` and `{"form": "both"}`), `tests/test1/test_label_mode_docs.py:126` (`ast.literal_eval(cells[3].strip("`")) == dict(label_mode.LABEL_MODE_DEFAULTS)`), and `tests/test1/test_button_classes_templates.py:214` (`for location in sorted(LOCATIONS)`). Task 1 updates all of these together along with `tests/test1/test_button_classes.py:21-91` (`EXPECTED_KEYS` count 71 → 73).
- **Eliminates SSTI/XSS in `BaseInput.render()`:** `crispy_forms/layout.py:255` executes `self.value = Template(str(self.value)).render(context)`, which both mutates `self.value` on the layout instance across renders and evaluates Django template syntax in button labels. Task 1 and Task 2 bypass `BaseInput.render()`, strip `SafeData` trust markers, and escape values/attributes once.
- **Preserves legacy `helper.add_input()` behavior (D-01/D-02):** `crispy_bootstrap5/templates/bootstrap5/inputs.html:8-10` loops `{% for input in inputs %}{% include "bootstrap5/layout/baseinput.html" %}{% endfor %}` without calling `input.render()`. Keeping `self.field_classes` and `self.flat_attrs` populated on `BaseInput` in `__init__` ensures `helper.add_input()` continues working untouched.

### 3. Concerns
- **MEDIUM — `BaseInput.__init__` mutates `self.field_classes` with `css_class` and does not store `self.css_class`:** In `src/crud_views/lib/crispy/buttons.py:16-18`, `_TableClassMixin.__init__` sets `self.field_classes = get_button_class(*(slot or self.slot).split(":", 1))` and then calls `super().__init__(name, value, **kwargs)`. In `crispy_forms/layout.py:244-245`, `BaseInput.__init__` does:
  ```python
  if css_class:
      self.field_classes += f" {css_class}"
  ```
  `BaseInput.__init__` never stores `self.css_class`, and it consumes `**kwargs` into `self.flat_attrs = flatatt(kwargs)` (`crispy_forms/layout.py:248`). If `Submit.render()` passes `self.field_classes` as `cv_css_class` into `form.html` (which already calls `{% cv_button_class "form" cv_key cv_label_mode %}`), the base classes (`btn btn-primary`) will be emitted **twice** (`class="btn btn-primary btn btn-primary extra"`), and any render-time `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)` after button instantiation would still have stale construction-time classes in `self.field_classes`. `_TableClassMixin.__init__` must explicitly store `self._cv_css_class = css_class or ""` and raw `kwargs` before delegating to `super().__init__`.
- **LOW — Specific `test_label_mode.py` assertions affected by adding `"form"` to `LOCATIONS`:** In `tests/test1/test_label_mode.py`, three places hardcode the pre-Phase-6 3-location set:
  1. Line 17: `PACKAGE = {"context": "icon", "list": "icon", "card": "both"}`
  2. Line 94: `({"form": "label", "list": "both"}, {**PACKAGE, "list": "both"})` under `# an unknown key (E108 reports it) is ignored at render`
  3. Line 137: `@pytest.mark.parametrize("location", ["toolbar", "form", "filter", "", "Context"])` in `test_default_label_mode_invalid_location`
  4. Line 155: `assert len(_records(caplog)) == 3  # one per location queried` (which queries `_resolved()` across all `LOCATIONS` and will now produce `4` records, not `3`).
  Additionally, `06-02` Task 1 modifies `tests/test1/test_label_mode.py` (`06-02-PLAN.md:86`), but `test_label_mode.py` is omitted from Task 1's `<verify><automated>` command (`06-02-PLAN.md:94`) and only run in Task 2 (`06-02-PLAN.md:116`).
- **LOW — `slot` without a colon raises `TypeError` in `__init__`:** In `src/crud_views/lib/crispy/buttons.py:17`, `get_button_class(*(slot or self.slot).split(":", 1))` raises `TypeError: get_button_class() missing 1 required positional argument: 'slot'` if a caller passes a malformed `slot="submit"` without `":"`.

### 4. Suggestions
- In `_TableClassMixin.__init__` (`src/crud_views/lib/crispy/buttons.py:16-18`), capture `css_class`, `css_id`, `template`, `slot`, and a copy of `kwargs` on private instance attributes before calling `super().__init__`, so `cv_css_class` contains only the caller's extra `css_class` while `self.field_classes` retains `"<table_classes> <css_class>"` for legacy `helper.inputs`.
- Add `tests/test1/test_label_mode.py` to `06-02` Task 1's `<verify><automated>` command (`06-02-PLAN.md:94`), and update `test_label_mode.py:17,94,137,155` when `"form"` joins `LOCATIONS`.

### 5. Risk Assessment
- **MEDIUM:** This plan introduces the new leaf contract, escaping rules, and atomic updates across 19 files. Capturing `css_class` separately from `BaseInput.field_classes` and updating all four assertions in `test_label_mode.py` are essential to keep Wave 2 green.

---

## 06-03

### 1. Summary
Plan `06-03` wires `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`, `ViewSet.form_actions_label_mode`, `CrudView.cv_form_actions_label_mode`, `CrudView.cv_get_form_actions_label_mode()`, and `CrudView.cv_get_action_label_mode("form", key)` into the form-button adapter, and implements the `form.cv_view` → helper `view` → page-context `view` ownership lookup across real `{% crispy %}` renders, multiple `FormActions`, and nested formset rows.

### 2. Strengths
- **Direct inspection of `form` argument in `render(self, form, context, ...)` avoids outer-form shadowing:** In `crispy_forms/layout.py:250` and `src/crud_views/templates/crud_views/formsets/formset.html:42` (`{% crispy x_form.form x_form.helper %}`), crispy passes the row's `actual_form` as the `form` argument to `LayoutObject.render(form, context, ...)`, while `context["form"]` may still hold the outer parent form until `BasicNode.get_render` finishes (`crispy_forms/templatetags/crispy_forms_tags.py:133`). Task 2's rule to read `getattr(form, "cv_view", None)` from the `form` parameter of `render()` rather than `context.get("form")` prevents parent-form leakage into formset rows.
- **Handles `BasicNode.get_render` and `FormActions.render` context stack mutations:** `BasicNode.get_render` (`crispy_forms/templatetags/crispy_forms_tags.py:109-112`) pushes `response_dict` (which includes `"view": helper.view` from `FormHelper.get_attributes` at `crispy_forms/helper.py:340-346`) onto `node_context`, and `FormActions.render` (`crispy_forms/bootstrap.py:276`) pushes `{"formactions": self, "fields_output": html}` onto `context` after rendering its children. Task 2 explicitly avoids fixed stack offsets when recovering the helper and page `view` from `context.dicts`.
- **Whole-map selection via `cv_first_inline_keys` matches existing `context`/`list` semantics:** `src/crud_views/lib/view/base.py:263-272` selects the first non-`None` map (`view` → `ViewSet` → `crud_views_settings`), so `{}` on a view suppresses the `ViewSet` and setting maps and falls through to `default_label_mode("form")`.

### 3. Concerns
- **MEDIUM — `CrudViewsSettings` snapshots `from_settings(...)` at import time and has no `setting_changed` refresh mechanism:** `06-03` Task 1 (`06-03-PLAN.md:53`) states: *"Add the three named map fields using existing declaration/validator patterns and preserve the setting refresh mechanism. ... standalone/ordinary owners use the current setting map then form floor."* However, in `src/crud_views/lib/settings.py:67-68,320`, `CrudViewsSettings` has **no** `setting_changed` signal receiver—`context_actions_label_mode` and `list_actions_label_mode` are evaluated once when `crud_views_settings = CrudViewsSettings()` is instantiated at module import time (which is why existing tests use `monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", ...)` at `tests/test1/test_action_label_mode_config.py:79,85`). If `06-03` tests `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` with `override_settings(CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE=...)` expecting a "setting refresh mechanism" to update `crud_views_settings.form_actions_label_mode`, the test will fail unless `crud_views_settings` either reads the setting dynamically / via `setting_changed` or tests use `monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", ...)`.
- **LOW — Coordination between `06-03` Task 1 and `06-06` Task 1 on `ViewSet.form_actions_label_mode` / `E106` key validation:** In `tests/test1/test_action_label_mode_config.py:43-60`, existing tests for `context_actions_label_mode` and `list_actions_label_mode` use action keys like `{"create": "both"}` and `{"home": "icon"}`. In `06-06` Task 1 (`06-06-PLAN.md:67`), `ViewSet` and `E106` reject keys not in `FORM_KINDS` (`{"submit", "cancel", "delete", "filter-submit", "filter-reset"}`) for `form_actions_label_mode`. If `06-03` Task 1 adds `"form_actions_label_mode"` to the existing `@pytest.mark.parametrize` blocks in `test_action_label_mode_config.py:43,56` that pass `{"create": "both"}`, those tests will break when `06-06` tightened finite-key validation lands.

### 4. Suggestions
- Clarify in `06-03` Task 1 how `crud_views_settings.form_actions_label_mode` is read and tested: keep `CrudViewsSettings.form_actions_label_mode: Any = from_settings("CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE", default={})` consistent with `context_actions_label_mode` / `list_actions_label_mode` (`src/crud_views/lib/settings.py:67-68`) and use `monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", ...)` in tests (or if `override_settings` support is desired, explicitly add a `setting_changed` handler).
- Use only valid `FORM_KINDS` keys (e.g., `{"submit": "both"}`, `{"cancel": "icon"}`) in all positive `form_actions_label_mode` tests added in `06-03` Task 1 so they remain valid after `06-06` Task 1.

### 5. Risk Assessment
- **MEDIUM:** Context-stack owner recovery under `django-crispy-forms` is the trickiest runtime mechanism in Phase 6, though the plan's design and test matrix for `Context.dicts` and formset rows are well-targeted.

---

## 06-04

### 1. Summary
Plan `06-04` adds the three new semantic icons (`save`, `cancel`, `filter-reset`) to `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` in `src/crud_views/lib/icons.py`, expands host-placed and inline icon rendering tests in `tests/test1/test_icon_host_leaves.py`, and wires semantic default icons plus `CrispyFormMixin.submit_icon`, `CrispyDeleteForm.delete_icon`, `WorkflowForm.submit_icon`, and adapter `icon=` keyword precedence.

### 2. Strengths
- **Registry parity is automatically guarded by existing tests:** `tests/test1/test_icons_registry.py:106-112` asserts `BOOTSTRAP_ICONS.keys() == DEFAULT_ICONS.keys()`, `v.startswith("bi:")`, and `v.split(":", 1)[0] in ("far", "fas")`, which immediately validates the new `save`, `cancel`, and `filter-reset` entries in `src/crud_views/lib/icons.py:14-89`.
- **Sentinel-based `icon=` parameter distinguishes omission from explicit suppression:** Using a sentinel default in `Submit`, `Button`, and `Reset` (`src/crud_views/lib/crispy/buttons.py`) allows `Submit("submit", "Save")` to default to `"save"` (from slot `"form:submit"`), while `Submit("submit", "Save", icon=None)` or `submit_icon = None` on a `CrispyFormMixin` subclass intentionally suppresses the icon and reaches the W292 / runtime missing-icon check in `icon` mode.
- **Decouples semantic kind and default icon from `name`:** `CrispyFormMixin.get_cancel_button_kwargs` (`src/crud_views/lib/crispy/form.py:76`) and `ListViewFilterFormHelper` (`src/crud_views/lib/views/list.py:73`) both use `name="reset"`. Resolving kind and default icon from `slot` (`form:cancel` → `"cancel"`, `form:filter-reset` → `"filter-reset"`) avoids colliding cancel and filter-reset icons.

### 3. Concerns
- **LOW — Concrete Font Awesome / Bootstrap Icons glyph strings are not written out in `06-04` Task 1:** `06-04-PLAN.md:57` says *"Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings"*, without naming the exact strings in the task body (whereas `superpowers/specs/2026-10-22-form-button-label-mode-design.md:125-129` specifies `save`: `far:floppy-disk` / `bi:floppy`, `cancel`: `fas:xmark` / `bi:x-lg`, `filter-reset`: `fas:rotate-left` / `bi:arrow-counterclockwise`). Pinning the exact glyph strings in `06-SPEC.md` and `06-04` prevents drift between `icons.py` and `docs/reference/icons.md` (`06-08`).
- **LOW — Interaction between `CrispyDeleteForm.delete_icon` and a custom `slot` in `get_delete_button_kwargs()`:** In `src/crud_views/lib/crispy/form.py:126-130`, `CrispyDeleteForm.get_delete_button()` currently calls `Submit(**{"slot": "form:delete", **self.get_delete_button_kwargs()})`, and `tests/test1/test_crispy_buttons.py:67-69` tests `SlotForm` overriding `get_delete_button_kwargs()` with `{**super().get_delete_button_kwargs(), "slot": "form:cancel"}`. If `get_delete_button()` passes `"icon": self.delete_icon` unconditionally before `**self.get_delete_button_kwargs()`, then `SlotForm` (which changed `slot` to `"form:cancel"` without passing `"icon"`) will receive `icon="delete"` instead of `"cancel"`'s kind default unless `delete_icon` is only defaulted when `slot` is `"form:delete"` (or `SlotForm` is expected to keep `delete_icon` unless `icon` is also overridden).
- **LOW — Stale `artifacts:` entry in `06-04` frontmatter:** `06-04-PLAN.md:27` still lists `path: src/crud_views/lib/button_classes.py` under `must_haves.artifacts`, even though `button_classes.py` was moved to `06-02` `files_modified`.

### 4. Suggestions
- State the exact glyph mappings in `06-04` Task 1 (`save`: `"far:floppy-disk"` / `"bi:floppy"`, `cancel`: `"fas:xmark"` / `"bi:x-lg"`, `filter-reset`: `"fas:rotate-left"` / `"bi:arrow-counterclockwise"`).
- Define in `06-SPEC.md` and `06-04` Task 2 whether `CrispyDeleteForm.get_delete_button()` applies `self.delete_icon` only when `slot == "form:delete"` or unconditionally unless `icon` is in `get_delete_button_kwargs()`, and assert that behavior in `test_delete_button_kwargs_may_choose_the_slot` (`tests/test1/test_crispy_buttons.py:62-74`).
- Remove the stale `src/crud_views/lib/button_classes.py` entry from `06-04-PLAN.md:27` `must_haves.artifacts`.

### 5. Risk Assessment
- **LOW:** Icon registry additions and form hook attributes follow well-established patterns in `src/crud_views/lib/icons.py` and `src/crud_views/lib/crispy/form.py`.

---

## 06-05

### 1. Summary
Plan `06-05` migrates `ListViewFilterFormHelper` (`src/crud_views/lib/views/list.py:57-87`) from `self.add_input(Submit(...))` / `self.add_input(Reset(...))` to a `get_form_actions() -> FormActions | None` hook rendered through `helper.render_layout()`, while isolating class-level `layout` declarations per instance, preserving `helper.form` when passed, keeping hidden `sort`/`order`/`dir` inputs on `self.inputs`, and leaving custom `add_input()` helpers working without warnings.

### 2. Strengths
- **Addresses `FormHelper.__init__(form)` clobbering class-level `layout`:** In `crispy_forms/helper.py:212-214`, `FormHelper.__init__` runs `if form is not None: self.form = form; self.layout = self.build_default_layout(form)`, which overwrites a subclass's class-level `layout = Layout(...)` (`tests/test1/app/views.py:288-289`). Task 1's design—initializing `FormHelper` with `None`, deep-copying any declared `layout` per instance, and setting `self.form = form` when `form is not None`—cleanly prevents layout loss and cross-request mutation.
- **Addresses `BasicNode.get_render` skipping `render_layout` when `helper.layout` is falsy:** In `crispy_forms/templatetags/crispy_forms_tags.py:116`, crispy checks `if helper and helper.layout:`, and `Layout` inherits `LayoutObject.__len__` (`crispy_forms/layout.py:38-39`) without `__bool__`, making `bool(Layout()) == False`. Using a private `Layout` subclass with `__bool__` returning `True` guarantees `helper.render_layout()` is called even when no layout was declared on the helper subclass or on a zero-field form.
- **Preserves `ListViewTableFilterMixin.get_filterset` constructor contract:** `src/crud_views/lib/views/mixins.py:319` calls `self.formhelper_class(request=self.request, view=self)` without `form`. Populating default fields from the `form` argument inside `render_layout(self, form, context, template_pack=...)` works without changing `get_filterset()` or breaking user `formhelper_class` subclasses that only accept `(self, view, request)`.

### 3. Concerns
- **MEDIUM — Post-construction `helper.layout = Layout()` assignment can bypass `render_layout` if `Layout()` is empty:** In `06-05` Task 2 (`06-05-PLAN.md:70,77`), the plan requires that replacing `helper.layout` after construction (before the first render or between renders) is respected, and that zero-field forms work. However, in `crispy_forms/templatetags/crispy_forms_tags.py:116`, crispy checks `if helper and helper.layout:` **before** calling `helper.render_layout(...)`. If a caller assigns a standard `crispy_forms.layout.Layout()` with zero fields (e.g., `helper.layout = Layout()`) after `__init__`, `bool(helper.layout)` is `False` at `crispy_forms_tags.py:116`, so `helper.render_layout(...)` will never be invoked unless `ListViewFilterFormHelper` wraps/converts assigned layouts via a `layout` property setter or inside `get_attributes()` (which runs at `crispy_forms_tags.py:109,147` just before line 116).
- **LOW — `FormHelper.get_attributes` copies non-underscore instance attributes into the template context:** In `crispy_forms/helper.py:340-346`, `get_attributes()` copies every key in `self.__dict__` not starting with `"_"` and not in `["layout", "inputs"]` into the crispy template context. Task 1 and Task 2 rightly mandate that all new helper lifecycle attributes use leading underscores (`_...`), which should be verified carefully during implementation (especially if a `@property def layout` backing field is used).

### 4. Suggestions
- Implement `layout` on `ListViewFilterFormHelper` (or normalize `self.layout` inside `get_attributes()`) so that any post-construction assignment `helper.layout = new_layout` is wrapped in the truthy `_FilterLayout` proxy before `crispy_forms_tags.py:116` checks `if helper and helper.layout:`.

### 5. Risk Assessment
- **MEDIUM:** `ListViewFilterFormHelper` interacts closely with `django-crispy-forms` internals (`FormHelper.__init__`, `get_attributes`, `BasicNode.get_render`, and `render_layout`), making the truthy layout wrapper and post-construction layout replacement important to get right.

---

## 06-06

### 1. Summary
Plan `06-06` implements static and runtime diagnostics for form buttons: extending `E106` (`CrudViewsSettings`), `ViewSet` validation, and `E210`/`E211`/`W291` (`CrudView.cv_form_actions_label_mode`), adding static `W292` missing-icon checks (`cv_form_icon_mode_checks` in `src/crud_views/lib/view/buttons.py`) across standard, delete, workflow, filter, and polymorphic views, and enforcing the runtime strict/log-and-fallback missing-icon rule in `cv_button_data()`.

### 2. Strengths
- **Resolves the `E210` / `E211` / `W291` contract cleanly without breaking existing `context` and `list` checks:** `tests/test1/test_action_label_mode_config.py:217-246` and `tests/test1/test_label_mode_docs.py:252,419-427` strictly pin the existing `E211` messages and behavior for `cv_context_actions_label_mode` and `cv_list_actions_label_mode`. Task 1 scopes the `E211` (bad map shape / non-str key) vs `E210` (invalid mode value) vs `W291` (unknown key against `FORM_KINDS`) split specifically to `cv_form_actions_label_mode`, preserving existing `context`/`list` check messages byte-for-byte.
- **Provider-first static W292 inspection avoids false positives on `CrispyDeleteForm`:** `CrispyDeleteForm` (`src/crud_views/lib/crispy/form.py:116`) inherits from `CrispyForm` → `CrispyFormMixin`, so it inherits `submit_icon = "save"`, even though `CrispyDeleteForm.helper` (`form.py:133-142`) only renders `self.get_delete_button()` (`delete_icon`) and `self.get_cancel_button()`. Checking `issubclass(form_cls, CrispyDeleteForm)` before `CrispyFormMixin` in Task 2 prevents false `W292` warnings when `submit_icon` is unset on a delete form.
- **Static polymorphic form inspection matches `PolymorphicCrudViewMixin`:** `src/crud_views_polymorphic/lib/utils.py:35` declares `polymorphic_forms: dict[Model, ModelForm] | None = None` (e.g., `VehicleCreateView` and `VehicleUpdateView` at `tests/test1/app/views.py:563-577`). Inspecting dict-valued `polymorphic_forms` values statically without calling `get_form_class()` (which accesses `self.polymorphic_model` and queries `ContentType` at `utils.py:49-55`) avoids database/request access during system checks.

### 3. Concerns
- **MEDIUM — Runtime missing-icon check in `cv_button_data` must use `resolve_icon(icon) is None`, not `render_icon(icon)`:** In `06-06` Task 2 (`06-06-PLAN.md:81`), the action states: *"Static inspection must not invoke arbitrary user renderers; determine disabled mappings through the registry resolution contract, and use actual rendered icon availability at runtime."* However, in `src/crud_views/templates/crud_views/tags/button/action.html:8` (and the new `form.html`), the template itself calls `{% cv_icon cv_icon %}` (for inline icons) or uses `cv_icon_class` from `icon_host_keys()` (for host-placed icons, where `render_icon()` is not used at all). Furthermore, `src/crud_views/lib/icons.py:187-202` `resolve_icon(value)` already resolves `CRUD_VIEWS_ICONS` mappings and returns `None` both when `value` is `None`/`""`/whitespace and when `CRUD_VIEWS_ICONS` maps a semantic name to `None`/`""`/whitespace—without invoking any library renderer. If `cv_button_data(ctx, "form")` called `render_icon(icon)` at runtime, it would invoke custom renderers twice per inline icon render and mis-handle host-only icon libraries (`placement: "host"`). Both static `W292` and runtime `cv_button_data(ctx, "form")` should use `resolve_icon(icon) is None`.
- **LOW — `CrudView.checks()` placement of `cv_form_icon_mode_checks(cls)` when `cv_viewset is None`:** In `src/crud_views/lib/view/base.py:195-197`, `cv_icon_mode_checks(cls)` is guarded by `if cls.cv_viewset is not None:` because context toolbar checks must look up target views on `cls.cv_viewset`. By contrast, `cv_form_icon_mode_checks(cls)` inspects `cls`'s own `form_class` / `polymorphic_forms` / `formhelper_class`, and `cls.cv_get_action_label_mode("form", kind)` (`base.py:268-272`) works even when `cls.cv_viewset is None`. If `test_form_button_checks.py` calls `ProbeView.checks()` on an unregistered view class where `cv_viewset is None` (like `tests/test1/test_workflow.py:540-545` does), guarding `cv_form_icon_mode_checks(cls)` behind `if cls.cv_viewset is not None:` would silently skip it.

### 4. Suggestions
- Use `resolve_icon(icon) is None` (`src/crud_views/lib/icons.py:187`) in both static `cv_form_icon_mode_checks()` and runtime `cv_button_data(ctx, "form")` to detect `None`/`""` and registry-disabled (`CRUD_VIEWS_ICONS = {"save": None}`) icons without invoking custom icon renderers inside `cv_button_data()`.
- Call `yield from cv_form_icon_mode_checks(cls)` in `CrudView.checks()` (`src/crud_views/lib/view/base.py:194-198`) even when `cls.cv_viewset is None` (or ensure all test views in `test_form_button_checks.py` bind `cv_viewset`).

### 5. Risk Assessment
- **MEDIUM:** Static inspection of view/form/helper hierarchies must carefully avoid instantiating forms or calling request-dependent methods while accurately detecting overridden hooks.

---

## 06-07

### 1. Summary
Plan `06-07` verifies browser-side JavaScript compatibility (`modal.js`, `viewset.js`, `list.filter.js`) with `<button>` elements and nested icon/label spans under the locked `jsdom@30.1.2` / `vitest@5.0.3` environment via `06-js-verify.sh`, and adds an isolated `crispy_floor` nox session (`Python 3.12` × `Django 4.2`/`6.0` with `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10`) in `noxfile.py`.

### 2. Strengths
- **Existing production JS already uses delegation and `SubmitEvent.submitter`:**
  - `src/crud_views/static/crud_views/js/modal.js:82,137` passes `event.submitter` to `new FormData(form, submitter || undefined)`.
  - `src/crud_views/static/crud_views/js/viewset.js:40` uses `e.target.closest("[data-cv-cancel-url]")`, which traverses up from nested `<i>` or `<span>` click targets inside `<button type="button" data-cv-cancel-url="...">`.
  - `src/crud_views/static/crud_views/js/list.filter.js:57` binds `addEventListener("click", onReset)` on `#filter-button-reset`, which receives clicks bubbling from nested `<i>` or `<span>` children inside `<button type="reset" id="filter-button-reset">`.
- **Single-transaction dependency pinning in `noxfile.py`:** In `noxfile.py:13-14`, existing sessions run two separate `session.install(...)` calls (`session.install(f"django~={django}.0")` followed by `session.install(".[polymorphic,workflow,ordered,test]")`), which would allow `pyproject.toml:33-34` (`django-crispy-forms (>=2.0)`, `crispy-bootstrap5 (>=2023.10)`) to upgrade to latest unless constrained in the same `session.install` invocation. Task 3 explicitly constrains `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` in the same resolver transaction.

### 3. Concerns
- **LOW — `noxfile.py` coverage report filename collision if `crispy_floor` copies `tests` session flags:** In `noxfile.py:18-19`, the `tests` session passes `--cov-report=xml:coverage-py{session.python}-dj{django}.xml`. If `crispy_floor` only runs the targeted Phase 6 test files (rather than the full suite), passing `--cov` with `pyproject.toml:154` (`fail_under = 88`) will fail the session on coverage percentage!

### 4. Suggestions
- In `noxfile.py` Task 3 (`crispy_floor` session), run `session.run("pytest", "--no-cov", ...)` (or omit `--cov`) when running the targeted subset of form-button test files so `pyproject.toml:154`'s global `fail_under = 88` coverage threshold does not fail a partial test run.

### 5. Risk Assessment
- **LOW:** Production JS files already support `<button>` and nested child click targets, and `crispy_floor` is an additive validation session in `noxfile.py`.

---

## 06-08

### 1. Summary
Plan `06-08` updates the reference documentation (`buttons.md`, `settings.md`, `action_menus.md`, `icons.md`, `theme.md`, `list_view.md`, `javascript.md`, `tutorial-5-filters-permissions.md`), adds executable documentation recipe tests in `tests/test1/test_form_button_docs.py`, updates `src/crud_views/static/crud_views/js/tooltip.js` comments, pairs the `CHANGELOG.md` `### Breaking` entry with `docs/migrating-1.0.md`, and enables `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` in `examples/bootstrap5/project/settings.py`.

### 2. Strengths
- **Preserves `cv-sync` blocks in `tutorial-5-filters-permissions.md`:** `examples/bootstrap5/test_docs_sync.py:86-92` enforces that every `<!-- cv-sync: ... -->` block in `docs/` matches the corresponding file under `examples/bootstrap5/` verbatim. Because D-03 preserves `AuthorFilterFormHelper`'s class-level `layout = Layout(Row(Column4("first_name"), Column4("last_name")))` (`docs/getting_started/tutorial-5-filters-permissions.md:26-30`), updating only the explanatory prose at lines 32–34 keeps `test_docs_sync.py` green.
- **Covers `tooltip.js` and `javascript.md` location inventory:** `src/crud_views/static/crud_views/js/tooltip.js:6-7` and `docs/reference/javascript.md:99-108` list the `data-cv-tooltip` locations (`context`, `list`, `card`, `card-order`, `formset`, `object-detail`). Task 3 updates both inventories to include `form` without unnecessary runtime JS edits (since `tooltip.js:27-29` already queries `[data-cv-tooltip]` generically).
- **Executable documentation recipes (`test_form_button_docs.py`):** Following the pattern in `tests/test1/test_pagination_docs.py:45-62`, Task 2 executes the documented `ListViewFilterFormHelper` subclass, `get_form_actions()` replacement/omission, and custom `template=` recipes under real crispy rendering.

### 3. Concerns
- **MEDIUM — Strict regex and AST assertions in `tests/test1/test_label_mode_docs.py` can easily be broken by edits to `settings.md`, `action_menus.md`, `buttons.md`, and `CHANGELOG.md`:**
  1. In `tests/test1/test_label_mode_docs.py:88-100` (`test_documented_card_floor_renders_label_only`), the test parses **every** ` ```python ` block in `docs/reference/settings.md` containing `CRUD_VIEWS_LABEL_MODE_DEFAULTS` with `ast.parse()` and `ast.literal_eval()`, and asserts that **exactly one** such assignment has `"card"` in its dict (`assert len(examples) == 1` and `assert examples[0] == {"card": "label"}`). Any new `CRUD_VIEWS_LABEL_MODE_DEFAULTS` code block in `settings.md` must be valid literal Python and must not include `"card"`.
  2. In `tests/test1/test_label_mode_docs.py:252,422-427`, the test asserts `_row(checks, "`viewset.E211`")[1].count("string or None") == 2` in `docs/reference/action_menus.md` and `e211.count("string or None") == 2` in `docs/reference/buttons.md`. When updating the `viewset.E211` row in both files for `cv_form_actions_label_mode`, the cell must still contain the substring `"string or None"` **exactly twice** (for `cv_card_actions_label_mode` and `cv_context_action_label_mode`).
  3. In `tests/test1/test_label_mode_docs.py:368-369`, the test asserts `len([b for b in added if b.startswith("- `CRUD_VIEWS_LABEL_MODE_DEFAULTS` sets")]) == 1` in `CHANGELOG.md` (`### Added`). New changelog bullets in `06-08` Task 3 must not start with `- `CRUD_VIEWS_LABEL_MODE_DEFAULTS` sets`.
- **LOW — Heading anchor checks in `examples/bootstrap5/test_doc_links.py` and `tests/test1/test_label_mode_docs.py:255-285`:** Renaming any existing markdown heading in `docs/reference/buttons.md`, `docs/reference/settings.md`, `docs/reference/action_menus.md`, or `docs/reference/list_view.md` would break `_anchors()` in `test_label_mode_docs.py:255-285` or `test_doc_ref_resolves` in `examples/bootstrap5/test_doc_links.py:119-125`.

### 4. Suggestions
- In `06-08` Task 1, when editing `docs/reference/settings.md`, `docs/reference/action_menus.md`, and `docs/reference/buttons.md`, check all assertions in `tests/test1/test_label_mode_docs.py:88-253,412-428` (especially `count("string or None") == 2` on `viewset.E211` rows and the single `"card"` literal fence in `settings.md`).
- In `06-08` Task 3's `<verify><automated>` block (`06-08-PLAN.md:100`), run `.venv/bin/pytest tests/test1/test_label_mode_docs.py examples/bootstrap5/test_docs_sync.py examples/bootstrap5/test_doc_links.py -q` alongside `.venv/bin/mkdocs build --strict` so any broken anchor or doc-sync block is caught immediately in Wave 7.

### 5. Risk Assessment
- **LOW:** Documentation and example updates are well-scoped and guarded by `test_label_mode_docs.py`, `test_form_button_docs.py`, `test_docs_sync.py`, and `mkdocs build --strict`.

---

## 06-09

### 1. Summary
Plan `06-09` performs the Wave 8 final verification and acceptance handoff: running the full Python and JavaScript test suites, lint/format checks, `mkdocs build --strict`, and example project tests; verifying git history ancestry and golden diffs; recording browser UAT observations and generic downstream theme follow-up in `06-ACCEPTANCE.md`; and updating `06-VALIDATION.md`.

### 2. Strengths
- **Uses `SystemChecksTest` instead of bare `manage.py check` for the example project:** As documented in `examples/bootstrap5/project/tests.py:98-114`, bare `manage.py check` does not import each feature app's `views.py`, whereas `SystemChecksTest::test_no_check_errors_with_every_viewset_registered` resolves `get_resolver().url_patterns` first so all example `ViewSet`s and `CrudView`s run through `check_viewsets()`.
- **Auditable golden-history andunrelated-golden invariance check:** Verifying that `tests/test1/golden/form_frame/`, `tests/test1/golden/action_menus/`, `tests/test1/golden/table_pagination/`, `tests/test1/golden/card_pagination/`, `tests/test1/golden/alerts/`, and `tests/test1/golden/heading_level/` remain untouched while `tests/test1/golden/form_buttons/*.html` trace back to the `06-01` baseline commits directly enforces `FORM-01` and D-17.

### 3. Concerns
- **LOW — Example gate runs only `SystemChecksTest` and `test_docs_sync.py` rather than the full `examples/bootstrap5` pytest suite:** In `06-09-PLAN.md:221-229`, the automated verify blocks run `project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered` and `test_docs_sync.py`, omitting the rest of the `examples/bootstrap5` test suite (`test_doc_links.py`, `test_i18n.py`, `library/tests.py`, `action_menus/tests.py`, `workflow/tests.py`, `polymorphic_demo/tests.py`, etc., which `nox -s examples` runs at `noxfile.py:33`). Notably, `examples/bootstrap5/test_i18n.py:134-135` tests `/library/author/create/` in German (`assert 'value="Sichern"' in html`) and `examples/bootstrap5/project/tests.py:45-51` renders every feature landing page after `examples/bootstrap5/project/settings.py` enables `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` in `06-08`.

### 4. Suggestions
- Expand the example verification command in `06-09-PLAN.md:221-229` to run the full example suite (`cd examples/bootstrap5 && ../../.venv/bin/pytest -q`) so all example feature pages, i18n checks (`test_i18n.py`), doc backlinks (`test_doc_links.py`), doc sync (`test_docs_sync.py`), and `SystemChecksTest` are verified with `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` enabled.

### 5. Risk Assessment
- **LOW:** `06-09` is a read-and-verify acceptance plan with clear blocking gates and single-writer documentation ownership.

---

## Overall Cross-Plan Assessment

- **Wave & Dependency Ordering:** The 8-wave dependency chain (`06-01` → `06-02` → `06-03` → `06-04` → `06-05` → `06-06` → `06-07` ∥ `06-08` → `06-09`) has no file-ownership conflicts in the only parallel wave (Wave 7: `06-07` modifies `tests/js/*`, `src/crud_views/static/crud_views/js/*`, and `noxfile.py`; `06-08` modifies `docs/*`, `CHANGELOG.md`, `examples/bootstrap5/project/settings.py`, `tooltip.js`, `test_label_mode_docs.py`, and `test_form_button_docs.py`). Moving the `LOCATIONS`, `LABEL_MODE_DEFAULTS`, and `DEFAULT_BUTTON_CLASSES` (`form:hidden-label`, `form:icon-host`) updates into `06-02` Task 1 resolved all Round 1 cross-wave breakage.
- **Top Implementation Watch-outs (all MEDIUM/LOW, no blockers):**
  1. **`06-02` (`src/crud_views/lib/crispy/buttons.py`):** Capture `css_class` and raw `kwargs` before `BaseInput.__init__` (`crispy_forms/layout.py:244-248`) appends `css_class` to `self.field_classes`, so `form.html` does not duplicate base table classes or freeze them at instantiation time.
  2. **`06-03` (`src/crud_views/lib/settings.py`):** Remember `CrudViewsSettings` snapshots `from_settings(...)` at import time (`settings.py:67-68,320`) without a `setting_changed` signal receiver; use `monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", ...)` in tests (and use valid `FORM_KINDS` keys in positive tests so they stay valid in `06-06`).
  3. **`06-05` (`src/crud_views/lib/views/list.py`):** Wrap post-construction `helper.layout = ...` assignments in the truthy `Layout` subclass before `crispy_forms_tags.py:116` (`if helper and helper.layout:`) checks truthiness.
  4. **`06-06` (`src/crud_views/lib/view/button_data.py` & `buttons.py`):** Use `resolve_icon(icon) is None` (`src/crud_views/lib/icons.py:187`) in both static `W292` and runtime `cv_button_data(ctx, "form")` so custom renderers are not invoked twice and host-placed icon libraries work identically.
  5. **`06-08` (`tests/test1/test_label_mode_docs.py`):** Preserve the exact `count("string or None") == 2` invariant in `viewset.E211` doc table rows (`test_label_mode_docs.py:252,423`) and the single `"card"` dict literal in `settings.md` (`test_label_mode_docs.py:97-100`).


---

## Consensus Summary

Cycle 2 reviews committed plan set `f637f5b`, incorporating revisions `62db7bb` and the user-authorized prerequisite decision D-18. Cycle 1's complete raw reviews remain in commit `6089258`; their historical HIGH quotations are not current findings. This is plan review, not implementation acceptance: the required property is executable coverage and valid mechanisms. A future implementation/test need not already exist for a plan revision to close a plan-level finding.

### Agreed Strengths

All three reviewers confirm the working branch contains the Phase 1 lazy-default and Phase 2 finite-kind contracts, and that the revised dependency gate honors D-18. They independently confirm the layout-vs-helper.inputs split, raw-name normalization, early location/default/key consumer updates, provider-aware diagnostics, whole-map selection, actual-form ownership, isolated helper lifecycle, baseline history, paired migration, registered example checks and locked-environment validation.

### Prior-Cycle Dispositions

| Cycle 1 concern | Current executable closure |
|---|---|
| H-MAIN | User D-18 plus ROADMAP.md:208-210 supersede main; 06-01 task1 records executing HEAD and prerequisite tests. The owned conflict slot remains resolved and unchanged. |
| H-LOCATIONS / H-KEYSET / H-EARLY-UTILITIES | 06-02 task1 owns all location/default consumers, both utilities and exhaustive keys/counts together. Fable explicitly signs off the source-grounded closure. |
| H-DIAGNOSTIC-CONTRACT | 06-06 task1 defines form-only E210-entry/E211-shape, own-view W291 and E106/constructor ownership; 06-08 task1 publishes it. All three reviewers confirm the mechanism. |
| H-DELETE-STATIC | 06-06 task2 explicitly selects delete helper before ordinary mixin and tests unused inherited submit vs actual delete/cancel. |
| M-PAYLOAD / M-NAME | 06-01/02 retain confirm-only POST, add confirm-plus-submitter, and reproduce upstream wire-name normalization separately from IDs. |
| M-OWNERS | 06-03 task2 reads the actual render form and adds multiple FormActions plus explicit-helper nested rows; no fixed stack offsets. |
| M-SLOT | 06-02 layout-only rejection tests and 06-08 paired Breaking/migration retain quiet legacy helper.inputs. |
| M-HELPER-STATE | 06-05 preserves explicit helper.form identity, replacement layout identity and exactly-once behavior. New empty-replacement edge is evaluated separately below. |
| M-REGISTRY-OFF / M-POLYMORPHIC | 06-06 task2 names effective registry-disabled icons, concrete mappings, dynamic fallback and local deduplication. |
| M-NODE-COMMANDS | 06-01 creates runtime record/wrapper before first integrated-wave gate; all later JS gates invoke it. |
| M-EXAMPLE-CHECKS | 06-09 invokes the URLconf-registering example test, source-confirmed at examples/bootstrap5/project/tests.py:97-115. |
| L-HIDDEN-WRAPPER / L-TOOLTIP-DOC | 06-05 pins wrapper behavior; 06-08 documents it and updates both tooltip inventories. |
| H-NODE (previous unconfirmed impossibility claim) | Acquisition is explicitly allowed and failure remains a blocker; 06-07 rejects older packages as acceptance. Neither completed reviewer establishes that acquisition is impossible. |

### Agreed Concerns and Current Actionable Findings

Five MEDIUM/LOW concerns remain outside executable plan coverage or explicit plan dispositions. M-SETTINGS-LIFECYCLE and M-EMPTY-REPLACEMENT are independently corroborated by Grok and Gemini; the remaining items are source-grounded solo findings and do not require corroboration under the non-HIGH contract.

- **M-SETTINGS-LIFECYCLE — MEDIUM / WARNING; 06-03 task1. Required property:** the form-map setting follows the actual existing settings lifecycle, with tests that exercise that lifecycle rather than an invented refresh. **Evidence:** 06-03-PLAN.md:79 says “preserve the setting refresh mechanism”; `settings.py:13-14,67-68,320` captures defaults at definition/instantiation and has no setting_changed refresh; existing map tests mutate `crud_views_settings` at `test_action_label_mode_config.py:78-80`. Lazy floors are deliberately separate (`label_mode.py:54-58`). **Example remedy (non-binding):** explicitly retain singleton map behavior and test map changes through the existing monkeypatch pattern, while keeping lazy floor override_settings tests. Do not add a global refresh to unrelated settings.
- **M-EMPTY-REPLACEMENT — MEDIUM / WARNING; 06-05 tasks1/2. Required property:** a caller replacing helper.layout with an empty Layout before/between renders still reaches the helper lifecycle and gets the specified one action group. **Evidence:** current task2 covers replacement fields/order but does not explicitly handle empty replacement before dispatch; installed `crispy_forms_tags.py:116` checks truthiness before calling render_layout, and `layout.py:38-39` makes empty Layout false. Constructor-only truthiness plus detection inside render_layout cannot recover a replacement that prevents entry. **Example remedy (non-binding):** make replacement normalization happen before that guard, with real crispy empty-replacement tests before first render and between renders. Keep None hook omission and caller-selected field order intact.
- **L-SUPPRESSION-MIGRATION — LOW / WARNING; 06-05/08. Required property:** consumers that previously suppressed stock actions by clearing helper.inputs have an explicit migration disposition. **Evidence:** stock actions currently enter inputs in `list.py:72-73`; moving them to layout means a subclass's later `self.inputs=[]` no longer removes Apply/Reset. 06-08-PLAN.md:99 documents new None omission and legacy add_input opt-in, but does not name this old suppression pattern or its changed behavior. **Example remedy (non-binding):** document migration from clearing inputs to get_form_actions returning None, with a targeted recipe/regression or an explicit disposition. Do not silently preserve suppression by relocating legacy controls or adding warnings.

- **M-ICON-AVAILABILITY — MEDIUM / WARNING; 06-06 task2 (Gemini). Required property:** availability checks preserve host-icon semantics and do not invoke a custom inline renderer twice. **Evidence:** 06-06-PLAN.md:112 says to use “actual rendered icon availability at runtime” but names no single-render/cache boundary. `icons.py:187-202` resolves disabled semantic mappings without invoking renderers; `icons.py:223-238` invokes the custom renderer, while the leaf separately renders inline icons and uses host classes for host placement. A probe rendering followed by leaf rendering can duplicate side effects and apply the wrong availability test to host icons. **Example remedy (non-binding):** use semantic resolution for the missing/disabled mapping policy, or explicitly preserve and reuse a rendered result with correct host handling; add custom-renderer invocation-count and host regressions. Do not weaken the required strict/log fallback for disabled icons.
- **L-EXAMPLE-COVERAGE — LOW / WARNING; 06-08/09 (Gemini). Required property:** example validation covers the form and documentation consumers affected by enabling form=both, or explicitly dispositions their omission. **Evidence:** 06-09's example commands run only SystemChecksTest and test_docs_sync; neither includes `examples/bootstrap5/test_i18n.py:134-135` (translated create submit value), `project/tests.py:45-51` (feature landing renders), or `test_doc_links.py:119-125` (documentation references). Root pytest tests excludes that separate example tree. **Example remedy (non-binding):** run the complete existing example suite under its own settings, or select the affected cases and document any deliberate omission. This extends coverage; the already-fixed URLconf registration gate remains correct.

### Divergent Views and the HIGH Consensus Gate

**H-OVERLAY-PROVENANCE — HIGH as reported by Grok; single-reviewer, unconfirmed; excluded from current_high. Neither Fable nor Gemini corroborates it; both describe the current owner-recovery design and test matrix as grounded.** Grok's existence-class premise is that the plan requires a nonexistent named provenance field. The current action says “response metadata/provenance”, not a field named provenance. Installed `BasicNode.get_response_dict` provides `inputs`, `is_formset`, and `template_pack` at `crispy_forms_tags.py:171-175`, and Fable independently identifies these as usable overlay metadata. Source-grounding therefore does not confirm the asserted missing dependency. Grok's design warning about confusing an outer helper with the page remains valid guidance, but 06-03 already requires the current invocation, actual page owner, explicit nested-row/None regressions and no fixed offsets; it does not instruct first-arbitrary-view lookup. The spec must establish a concrete discriminator and prove it through those tests. This review does not certify a future implementation. The existence premise and conditional design warning were evaluated separately: no independent non-discounted judgment HIGH was discarded merely for lacking corroboration. The suppressed reported HIGH remains visible in the final current-concern section per the consensus contract.

### Structured Current Non-HIGH Issues

```yaml
issues:
  - plan: "06-03"
    task: 1
    dimension: source_grounding
    severity: warning
    review_severity: MEDIUM
    id: M-SETTINGS-LIFECYCLE
    required_property: "Form-map configuration preserves the actual singleton settings lifecycle and distinguishes it from lazy floor reads."
    description: "The action says preserve the setting refresh mechanism, but settings.py:13-14,67-68,320 has import-time capture and no refresh; map tests monkeypatch the singleton."
    fix_hint: "State singleton lookup/test semantics explicitly; retain override_settings for the separately lazy floor."
  - plan: "06-05"
    task: 2
    dimension: task_completeness
    severity: warning
    review_severity: MEDIUM
    id: M-EMPTY-REPLACEMENT
    required_property: "Empty caller-replaced layouts reach exactly-once action initialization before crispy's truthiness guard."
    description: "Replacement tests are named, but the empty replacement can bypass render_layout at crispy_forms_tags.py:116 before the planned replacement handling runs."
    fix_hint: "Include pre-dispatch normalization and real empty replacement cases before and between renders."
  - plan: "06-08"
    task: 2
    dimension: context_compliance
    severity: warning
    review_severity: LOW
    id: L-SUPPRESSION-MIGRATION
    required_property: "Legacy helper.inputs clearing has an explicit migration disposition when stock actions move into layout."
    description: "Current stock controls live in inputs at list.py:72-73; the migration covers add_input opt-in and the new None hook but never identifies self.inputs=[] suppression changing."
    fix_hint: "Document the old suppression pattern's migration to get_form_actions returning None and verify the recipe."
  - plan: "06-06"
    task: 2
    dimension: key_links_planned
    severity: warning
    review_severity: MEDIUM
    id: M-ICON-AVAILABILITY
    required_property: "Missing-icon availability checks preserve host icons and do not duplicate custom renderer invocations."
    description: "The runtime rendered-availability instruction lacks a single-render boundary, while icons.py:223-238 invokes renderers and the leaf renders inline icons separately."
    fix_hint: "Use non-rendering semantic resolution for disabled mappings or reuse rendered results; test invocation count and host behavior."
  - plan: "06-09"
    task: 2
    dimension: verification_derivation
    severity: warning
    review_severity: LOW
    id: L-EXAMPLE-COVERAGE
    required_property: "Changed example form and documentation consumers are verified or explicitly dispositioned."
    description: "The selected example commands omit test_i18n.py translated form controls, feature landing renders and test_doc_links.py; root pytest tests excludes this tree."
    fix_hint: "Run the full example suite under its settings or the relevant cases with explicit omission rationale."
```

Remediation examples are non-binding; any mechanism satisfying the named property closes the issue.

### Findings Already Executable or Not Substantiated

| Reviewer concern | Disposition against current execution plans |
|---|---|
| Fable/Grok: move Node acquisition later | Not an invisible requirement. 06-VALIDATION.md:24-29 requires full Python/JS after every integrated wave and deliberately establishes the runtime before wave1. 06-01 explicitly records acquisition failure as a blocker; 06-07 repeats the rationale. The suggestion to treat early failure as nonblocking contradicts that active gate. No impossibility of acquisition is proved. |
| Fable: machine-specific absolute paths | Intentional fail-closed runtime evidence. 06-01 specifies acquisition/recording on the executing host; later gates reject stale paths. Portable automatic regeneration is not a phase requirement and could silently replace the recorded evidence. |
| Fable/Grok: raw css_class, kwargs and flat_attrs | 06-01 defines exactly-once class composition and a literal SafeData-free boundary. 06-02 task1 expressly retains raw value/kwargs, distinguishes legacy field_classes/flat_attrs, and task2 tests SafeString extras, exact decoded attributes, no mutation and no duplicate attributes/classes. These invariants already prohibit both shortcuts; prescribing a pre-super capture implementation is guidance, not missing executable coverage. |
| Fable: str(SafeString) remains safe | 06-01 explicitly requires an ordinary string without a SafeData marker; 06-02 tests marked-safe body/value/title/extras through parsed DOM. The precise conversion operation is implementation discretion. |
| Grok: test_label_mode.py invalid form/count | 06-02 task1's first action expressly updates this file's location/default assertions in the producing task; task2 runs that file and the integrated-wave suite must remain green. The concern is not invisible to execution. |
| Grok: icon keyword not reserved; explicit None forwarding | 06-04 artifacts explicitly consume icon= as configuration, never an HTML attr; task2 specifies a sentinel, None/empty suppression and hook/default precedence. 06-01 must carry the concrete 06-02..06 contracts into the spec. |
| Fable: None setting membership | 06-03 task1 explicitly requires malformed selected values to use strict/log fallback rather than membership crashes; 06-06 adds None/malformed coverage. No new None-as-empty public policy is silently adopted from the suggestion. |
| Fable: leaf/file overlap and finite-key double implementation | Plans are dependency-ordered. 06-04 expands library coverage after 06-02; 06-03 says full diagnostics follow06-06, which owns finite-key validation. No race or conflicting transformation is established. |
| Fable: choose distinguishable glyphs | Semantic mappings are locked; exact supported glyph choice is implementation discretion under06-04. |
| Fable: deepcopy rendered layouts | 06-05 requires class-layout isolation and replacement/repeated-render tests. The suggestion to only clone a constructor class snapshot would conflict with the explicit caller-replacement contract. |
| Fable/Grok: diagnostic narrow exception and per-render logging | 06-06 task2 already narrowly catches mode-resolution ValueError, preserves E108/E210/E211, logs once per render and deduplicates only per traversal. |
| Fable/Grok: one nox resolver transaction | 06-07 task3 explicitly constrains both crispy pins and extras in the same transaction and verifies actual versions; a preferred one-line session.install syntax adds no missing property. |
| Grok: docs must wait for finite key diagnostics | 06-08 depends on06-06 and explicitly documents its new form-only policy. Future code need not exist at review time. |
| Fable: documented config test location; Grok: exact knob dict | 06-08 task1 owns test_label_mode_docs.py, extends its assertions and renders the documented config; its task file list and verify already identify that suite. |
| Grok: baseline/history checks not all in automated XML | 06-01 tasks2/3 expressly require baseline-only commits, source diff and ancestry checks; 06-09 independently verifies actual ancestry/blob equality and rejects summary-only inherited evidence. These are executable actions, not review-only advice. |
| Grok: native reset and renamed parameters | 06-07 preserves current native reset/navigation semantics and requires real form reset tests; 06-05 preserves current server hidden values. A new configurable reset protocol is not authorized by this preservation requirement. |
| Grok: floor/JS exits absent from full pytest | 06-09 requires every additional integrated gate and actual per-task/wave evidence; no claim says pytest alone executes nox or JS. |
| Grok: browser settings | 06-09 task2 names the example and all three modes with actual observations; test-project defaults are not accepted as browser evidence. |
| Fable: task load/classifier bookkeeping/repeated threat rows | Scope-quality observations, not missing product work; task splitting and reducing audit repetition are advisory. No new acceptance work follows from these comments. |

| Gemini: new finite form map tests must use finite keys | 06-03 uses form kinds and06-06 explicitly tests finite validation; no task directs copying create/home positive values into the new form map. |
| Gemini: slot without colon | Pre-existing constructor error in buttons.py:17; current plans preserve constructor behavior and specify finite validation on the layout path. No new relaxed malformed-slot API is required. |
| Gemini: delete slot versus icon | 06-04 task2 explicitly puts custom hook overrides first, explicit form icon next, kind default last. A slot change does not silently remove an explicit form icon. Exact source-slot styling is already tested. |
| Gemini: earlier utility artifact in06-04 | The artifact's provides text expressly says delivered by06-02. It is a prerequisite, not a claim06-04 creates it. |
| Gemini: runtime backup cleanup | 06-01 says preserve the old node_modules until restoration succeeds; placement/cleanup is reversible execution housekeeping, not an omitted behavior or permission to leave tracked modifications. |
| Gemini: direct W292 on unregistered test views | 06-06 expressly drives actual check_viewsets and static provider coverage. A hypothetical fixture lacking registration is not a prescribed plan mechanism; fixtures must satisfy that existing verification contract. |
| Gemini: inherited coverage flags in crispy_floor | 06-07 copies installation extras/support constraints, not the full-suite coverage flags. Its action explicitly runs the targeted expanded suite; no task requires applying the global88% coverage gate to that subset. Omit inappropriate copied flags during implementation. |
| Gemini: doc regex/AST counts and headings | 06-08 explicitly preserves context/list message assertions, the unique Added prefix and synced fences, and runs the existing docs tests. No heading rename or duplicate card-floor fence is prescribed. Additional example link coverage is captured once in L-EXAMPLE-COVERAGE. |
| Gemini: JS wrapper not in task1 automated element | It is an explicit executable06-01 action and mandatory wave1 sampling gate in VALIDATION; current non-HIGH incorporation recognizes actions and acceptance as well as automated XML. It is not deferred to wave7. |

## Verification coverage

### Cross-artifact fact drift

- Phase-status seam returned `lag`: STATE=`Planning`, ROADMAP=`Planned`, ranks0/1. This one-step nonterminal lag is not a finding; authority STATE.md.
- ROADMAP.md:223-224 requirement IDs FORM-01..13 match plan requirements and task references; no contradictory ID claim.
- ROADMAP.md:226-237 and must_haves agree on real buttons, default payload preservation, all three modes, escaping, icons/checks and migration/example outcomes. D-18's working-branch precondition agrees across ROADMAP.md:208-210, CONTEXT and06-01/09; the superseded main gate is historical only.
- CONTEXT D-01..18 and plan terminology agree on owner, whole-map selection, finite kinds, literal values, legacy helper.inputs and prerequisites. No authority was assigned to discretion/deferred text. Research's copied context predates D-18; absence of the new decision is not a contradictory duplicate fact.
- ROADMAP.md:227's historical claim that an existing delete test posts only delete=Delete is inaccurate against tests/test1/test_crud.py:63. Current plans correctly preserve confirm=True and add a separate combined payload assertion. This source-factual clarification is already M-PAYLOAD's disposition, not a new coverage reduction or a demand to remove confirmation. It does not contribute to convergence counts.
- All four axes were inspected. No countable cross-artifact advisory; future artifacts and implementation acceptance remain pending by design.


### Source-grounding inventory

Effective authority is `intel`, resolved by `drift-guard authority --raw`. The index at `.planning/intel/API-SURFACE.md:5` declares itself incomplete and contains no API entries. Existing Python symbols/signatures, framework/browser/CLI contracts and paths below are **UNCHECKABLE** at this authority; an empty index does not establish absence. The severity seam was invoked for UNCHECKABLE at intel and returned INFO, hardBlock=false. Supplemental file/declaration observations do not upgrade the authoritative verdict or validate signatures. Proposed artifacts are excluded. No hardBlock or acknowledgement-required result was produced.

Each entry quotes a current plan line and lists every matching current-plan citation. Future references are excluded across plans as well as in their producer. Existing base methods and proposed overrides are distinguished in prose.

<details>
<summary><code>--check</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:231` — &lt;automated&gt;.venv/bin/ruff format --check&lt;/automated&gt;

Citations: 06-09-PLAN.md:231.

</details>

<details>
<summary><code>--prefix</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:108` — Then invoke that absolute Node with its recorded npm-cli.js and --prefix . test, forwarding supplied test

Citations: 06-01-PLAN.md:108.

</details>

<details>
<summary><code>--strict</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:118` — &lt;automated&gt;.venv/bin/mkdocs build --strict&lt;/automated&gt;

Citations: 06-08-PLAN.md:118, 06-09-PLAN.md:86.

</details>

<details>
<summary><code>.planning/PROJECT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:54` — @.planning/PROJECT.md

Citations: 06-01-PLAN.md:54, 06-02-PLAN.md:67, 06-03-PLAN.md:53, 06-04-PLAN.md:56, 06-05-PLAN.md:54, 06-06-PLAN.md:56, 06-07-PLAN.md:53, 06-08-PLAN.md:63, 06-09-PLAN.md:48.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/REQUIREMENTS.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:57` — @.planning/REQUIREMENTS.md

Citations: 06-01-PLAN.md:57.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/ROADMAP.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:55` — @.planning/ROADMAP.md

Citations: 06-01-PLAN.md:55, 06-02-PLAN.md:68, 06-03-PLAN.md:54, 06-04-PLAN.md:57, 06-05-PLAN.md:55, 06-06-PLAN.md:57, 06-07-PLAN.md:54, 06-08-PLAN.md:64, 06-09-PLAN.md:49.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/STATE.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:56` — @.planning/STATE.md

Citations: 06-01-PLAN.md:56, 06-02-PLAN.md:69, 06-03-PLAN.md:55, 06-04-PLAN.md:58, 06-05-PLAN.md:56, 06-06-PLAN.md:58, 06-07-PLAN.md:55, 06-08-PLAN.md:65, 06-09-PLAN.md:50.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/01-label-mode-defaults/01-CONTEXT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:79` — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

Citations: 06-01-PLAN.md:79.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/02-form-key-grammar/02-CONTEXT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:79` — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

Citations: 06-01-PLAN.md:79.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-01-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:263` — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

Citations: 06-01-PLAN.md:263.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-02-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:186` — Create .planning/phases/06-form-button-leaf/06-02-SUMMARY.md.

Citations: 06-02-PLAN.md:186.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-03-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:147` — Create .planning/phases/06-form-button-leaf/06-03-SUMMARY.md.

Citations: 06-03-PLAN.md:147.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-04-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-04-PLAN.md:147` — Create .planning/phases/06-form-button-leaf/06-04-SUMMARY.md.

Citations: 06-04-PLAN.md:147.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-05-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-05-PLAN.md:150` — Create .planning/phases/06-form-button-leaf/06-05-SUMMARY.md.

Citations: 06-05-PLAN.md:150.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-06-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-06-PLAN.md:160` — Create .planning/phases/06-form-button-leaf/06-06-SUMMARY.md.

Citations: 06-06-PLAN.md:160.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-07-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-07-PLAN.md:160` — Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md.

Citations: 06-07-PLAN.md:160.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-08-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-08-PLAN.md:161` — Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md.

Citations: 06-08-PLAN.md:161.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-09-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-09-PLAN.md:276` — Create .planning/phases/06-form-button-leaf/06-09-SUMMARY.md.

Citations: 06-09-PLAN.md:276.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-09-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

Citations: 06-09-PLAN.md:8, 06-09-PLAN.md:24, 06-09-PLAN.md:29, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:80.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-CONTEXT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:58` — @.planning/phases/06-form-button-leaf/06-CONTEXT.md

Citations: 06-01-PLAN.md:58, 06-02-PLAN.md:70, 06-03-PLAN.md:56, 06-04-PLAN.md:59, 06-05-PLAN.md:57, 06-06-PLAN.md:59, 06-07-PLAN.md:56, 06-08-PLAN.md:66, 06-09-PLAN.md:51.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:10` — - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json

Citations: 06-01-PLAN.md:10, 06-01-PLAN.md:77.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-PATTERNS.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:60` — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

Citations: 06-01-PLAN.md:60, 06-02-PLAN.md:72, 06-03-PLAN.md:58, 06-04-PLAN.md:61, 06-05-PLAN.md:59, 06-06-PLAN.md:61, 06-07-PLAN.md:58, 06-08-PLAN.md:68, 06-09-PLAN.md:53.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-RESEARCH.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:59` — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

Citations: 06-01-PLAN.md:59, 06-02-PLAN.md:71, 06-03-PLAN.md:57, 06-04-PLAN.md:60, 06-05-PLAN.md:58, 06-06-PLAN.md:60, 06-07-PLAN.md:57, 06-08-PLAN.md:67, 06-09-PLAN.md:52.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-SPEC.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-SPEC.md

Citations: 06-01-PLAN.md:8, 06-01-PLAN.md:31, 06-01-PLAN.md:77, 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-01-PLAN.md:197, 06-02-PLAN.md:73, 06-03-PLAN.md:59, 06-04-PLAN.md:62, 06-05-PLAN.md:60, 06-06-PLAN.md:62, 06-07-PLAN.md:59, 06-08-PLAN.md:69, 06-09-PLAN.md:54.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-VALIDATION.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:61` — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

Citations: 06-01-PLAN.md:61, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:65, 06-09-PLAN.md:80.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-js-verify.sh</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:9` — - .planning/phases/06-form-button-leaf/06-js-verify.sh

Citations: 06-01-PLAN.md:9, 06-01-PLAN.md:77, 06-01-PLAN.md:112, 06-07-PLAN.md:83, 06-07-PLAN.md:103, 06-09-PLAN.md:223.

</details>

<details>
<summary><code>06-01-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:263` — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

Citations: 06-01-PLAN.md:263, 06-02-PLAN.md:86, 06-02-PLAN.md:136.

</details>

<details>
<summary><code>06-07-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-07-PLAN.md:160` — Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md.

Citations: 06-07-PLAN.md:160, 06-09-PLAN.md:81.

</details>

<details>
<summary><code>06-08-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-08-PLAN.md:161` — Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md.

Citations: 06-08-PLAN.md:161, 06-09-PLAN.md:81.

</details>

<details>
<summary><code>06-RESEARCH.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:59` — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

Citations: 06-01-PLAN.md:59, 06-02-PLAN.md:71, 06-03-PLAN.md:57, 06-04-PLAN.md:60, 06-05-PLAN.md:58, 06-06-PLAN.md:60, 06-07-PLAN.md:57, 06-07-PLAN.md:71, 06-07-PLAN.md:113, 06-08-PLAN.md:67, 06-09-PLAN.md:52.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>06-SPEC.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-SPEC.md

Citations: 06-01-PLAN.md:8, 06-01-PLAN.md:31, 06-01-PLAN.md:66, 06-01-PLAN.md:77, 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-01-PLAN.md:197, 06-02-PLAN.md:73, 06-03-PLAN.md:59, 06-03-PLAN.md:71, 06-03-PLAN.md:92, 06-04-PLAN.md:62, 06-05-PLAN.md:60, 06-05-PLAN.md:72, 06-06-PLAN.md:62, 06-06-PLAN.md:99, 06-07-PLAN.md:59, 06-08-PLAN.md:69, 06-08-PLAN.md:81, 06-09-PLAN.md:54, 06-09-PLAN.md:66.

</details>

<details>
<summary><code>06-VALIDATION.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:61` — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

Citations: 06-01-PLAN.md:61, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:66, 06-09-PLAN.md:80, 06-09-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>ACCEPTANCE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

Citations: 06-09-PLAN.md:8, 06-09-PLAN.md:24, 06-09-PLAN.md:29, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:80.

</details>

<details>
<summary><code>ACCEPTANCE.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

Citations: 06-09-PLAN.md:8, 06-09-PLAN.md:24, 06-09-PLAN.md:29, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:80.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>API</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:84` — Addresses H-DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish shape from individual modes so D-16&#x27;s E210 extension has a concrete scope without adding a scalar API: non-dict or non-string keys yield one E211 and stop entry traversal; a string-keyed dict yields one E210 per invalid mode value in insertion order; unknown form keys with valid modes yield W291 on the view&#x27;s own cv_form_actions_label_mode only, naming sorted FORM_KINDS. None and {} are valid. This documented form-specific diagnostic distinction does not alter FORM-11 whole-map resolution semantics. Do not blindly invoke the old helper unchanged or change its behavior for context/list.

Citations: 06-06-PLAN.md:84, 06-08-PLAN.md:75, 06-08-PLAN.md:84, 06-09-PLAN.md:116.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:153` cv_atomic: bool = False  # a DB transaction cannot roll back S3 / API writes; `tests/test1/test_unknown_attribute_check.py:12` cv_message = "Created {{ object }}"  # dead: real API is cv_message_template_code.
</details>

<details>
<summary><code>ASCII</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:90` — - Literal markup, template syntax, empty text and non-ASCII text survive as data without injection.

Citations: 06-02-PLAN.md:90, 06-06-PLAN.md:28, 06-07-PLAN.md:97, 06-09-PLAN.md:208.

</details>

<details>
<summary><code>ASSUMED</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:257` — | T-06-SC | Tampering | runtime/package restoration | high | mitigate | Official checksum-verified isolated Node; exact npm lock restoration under the research audit; blocking human gate for any ASSUMED/SUS package and no SLOP |

Citations: 06-01-PLAN.md:257, 06-02-PLAN.md:180, 06-03-PLAN.md:141, 06-04-PLAN.md:141, 06-05-PLAN.md:144, 06-06-PLAN.md:154, 06-07-PLAN.md:154, 06-08-PLAN.md:155, 06-09-PLAN.md:270.

</details>

<details>
<summary><code>BASELINE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:184` — Verify git diff BASELINE^ BASELINE -- src is empty and baseline commit is an ancestor of HEAD.

Citations: 06-01-PLAN.md:184.

</details>

<details>
<summary><code>BOOTSTRAP_ICONS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:83` — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys through dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys and keep exhaustive class/default checks green.

Citations: 06-04-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/lib/icons.py:51` BOOTSTRAP_ICONS: dict[str, str] = {.
</details>

<details>
<summary><code>BaseInput</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

Citations: 06-02-PLAN.md:99, 06-02-PLAN.md:112, 06-02-PLAN.md:178.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:20` def get_layout_fields(self) -> LayoutObject | BaseInput | List[LayoutObject | BaseInput]:; `src/crud_views/lib/crispy/form.py:50` def get_layout_fields(self) -> LayoutObject | BaseInput | list[LayoutObject | BaseInput]:.
</details>

<details>
<summary><code>BaseInput.render</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

Citations: 06-02-PLAN.md:99, 06-02-PLAN.md:178.
 Supplemental declaration candidate: `src/crud_views/templatetags/crud_views.py:333` def render(self, context):; `src/crud_views/lib/view/base.py:109` cv_header_template: str | None = None  # template snippet to render header label.
</details>

<details>
<summary><code>BasicNode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.

</details>

<details>
<summary><code>BasicNode.get_render</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.

</details>

<details>
<summary><code>CHANGELOG</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:17` — - CHANGELOG.md

Citations: 06-08-PLAN.md:17, 06-08-PLAN.md:111, 06-08-PLAN.md:112.
 Supplemental declaration candidate: `tests/test1/test_label_mode_docs.py:21` CHANGELOG_MD = ROOT / "CHANGELOG.md".
</details>

<details>
<summary><code>CHANGELOG.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:17` — - CHANGELOG.md

Citations: 06-08-PLAN.md:17, 06-08-PLAN.md:111, 06-08-PLAN.md:112.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>CHECKS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:250` — | M-EXAMPLE-CHECKS | MEDIUM | The example gate runs the existing SystemChecksTest that resolves the full URLconf and checks registered feature ViewSets, replacing bare manage.py check. |

Citations: 06-09-PLAN.md:250.

</details>

<details>
<summary><code>CLAUDE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:53` — @CLAUDE.md

Citations: 06-01-PLAN.md:53, 06-02-PLAN.md:66, 06-03-PLAN.md:52, 06-04-PLAN.md:55, 06-05-PLAN.md:53, 06-06-PLAN.md:55, 06-07-PLAN.md:52, 06-08-PLAN.md:62, 06-09-PLAN.md:47.

</details>

<details>
<summary><code>CLAUDE.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:53` — @CLAUDE.md

Citations: 06-01-PLAN.md:53, 06-02-PLAN.md:66, 06-03-PLAN.md:52, 06-04-PLAN.md:55, 06-05-PLAN.md:53, 06-06-PLAN.md:55, 06-07-PLAN.md:52, 06-08-PLAN.md:62, 06-09-PLAN.md:47.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>COMMANDS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:95` — Before the first per-wave JS gate, complete environment-only preparation for M-NODE-COMMANDS. Inspect

Citations: 06-01-PLAN.md:95, 06-01-PLAN.md:241, 06-07-PLAN.md:79, 06-07-PLAN.md:134, 06-09-PLAN.md:251.

</details>

<details>
<summary><code>CONTEXT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:58` — @.planning/phases/06-form-button-leaf/06-CONTEXT.md

Citations: 06-01-PLAN.md:58, 06-01-PLAN.md:79, 06-01-PLAN.md:246, 06-02-PLAN.md:70, 06-03-PLAN.md:56, 06-04-PLAN.md:59, 06-05-PLAN.md:57, 06-06-PLAN.md:59, 06-07-PLAN.md:56, 06-08-PLAN.md:66, 06-09-PLAN.md:51.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>CONTRACT</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:84` — Addresses H-DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish shape from individual modes so D-16&#x27;s E210 extension has a concrete scope without adding a scalar API: non-dict or non-string keys yield one E211 and stop entry traversal; a string-keyed dict yields one E210 per invalid mode value in insertion order; unknown form keys with valid modes yield W291 on the view&#x27;s own cv_form_actions_label_mode only, naming sorted FORM_KINDS. None and {} are valid. This documented form-specific diagnostic distinction does not alter FORM-11 whole-map resolution semantics. Do not blindly invoke the old helper unchanged or change its behavior for context/list.

Citations: 06-06-PLAN.md:84, 06-06-PLAN.md:132, 06-08-PLAN.md:84, 06-08-PLAN.md:135.

</details>

<details>
<summary><code>COVERED</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:122` — | GOAL | Real buttons through leaf, shared label/class contract, template-injection safety, unchanged POST | 02–09 | COVERED |

Citations: 06-09-PLAN.md:122, 06-09-PLAN.md:123, 06-09-PLAN.md:124, 06-09-PLAN.md:125, 06-09-PLAN.md:126, 06-09-PLAN.md:127, 06-09-PLAN.md:128, 06-09-PLAN.md:129, 06-09-PLAN.md:130, 06-09-PLAN.md:131, 06-09-PLAN.md:132, 06-09-PLAN.md:133, 06-09-PLAN.md:134, 06-09-PLAN.md:135, 06-09-PLAN.md:136, 06-09-PLAN.md:137, 06-09-PLAN.md:138, 06-09-PLAN.md:139, 06-09-PLAN.md:140, 06-09-PLAN.md:141, 06-09-PLAN.md:142, 06-09-PLAN.md:143, 06-09-PLAN.md:144, 06-09-PLAN.md:145, 06-09-PLAN.md:146, 06-09-PLAN.md:147, 06-09-PLAN.md:148, 06-09-PLAN.md:149, 06-09-PLAN.md:150, 06-09-PLAN.md:151, 06-09-PLAN.md:152, 06-09-PLAN.md:153, 06-09-PLAN.md:154, 06-09-PLAN.md:155, 06-09-PLAN.md:156, 06-09-PLAN.md:157, 06-09-PLAN.md:158, 06-09-PLAN.md:159, 06-09-PLAN.md:160, 06-09-PLAN.md:161, 06-09-PLAN.md:162, 06-09-PLAN.md:163, 06-09-PLAN.md:164, 06-09-PLAN.md:165.

</details>

<details>
<summary><code>CRUD</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:191` — &lt;done&gt;CRUD form controls have reviewable before-change evidence.&lt;/done&gt;

Citations: 06-01-PLAN.md:191, 06-07-PLAN.md:115.
 Supplemental declaration candidate: `src/crud_views/management/commands/crud_views_show.py:5` help = "Show Django CRUD views".
</details>

<details>
<summary><code>CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.

</details>

<details>
<summary><code>CRUD_VIEWS_ICONS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:112` — Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF, use the effective icon after semantic registry resolution: explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty are missing. Test each with known default submit/delete/filter controls. Named-but-unregistered icons retain separate registry diagnostics; this is distinct from intentional registry disabling, which produces no registry warning and therefore needs W292. Static inspection must not invoke arbitrary user renderers; determine disabled mappings through the registry resolution contract, and use actual rendered icon availability at runtime.

Citations: 06-06-PLAN.md:112.
 Supplemental declaration candidate: `src/crud_views/lib/icons.py:131` icons = {**DEFAULT_ICONS, **_THEME_ICONS, **(getattr(settings, "CRUD_VIEWS_ICONS", None) or {})}; `tests/test1/test_button_leaves.py:570` host_icons = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS).
</details>

<details>
<summary><code>CRUD_VIEWS_LABEL_MODE_DEFAULTS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:115` — Per L-HIDDEN-WRAPPER, explain that visible filter actions now precede the pack-owned hidden-input wrapper and its retained margin/classes; hidden values/path are unchanged and no global crispy override is needed. Per L-TOOLTIP-DOC add form to the public data-cv-tooltip location inventory in javascript.md and the tooltip.js header comment, keeping runtime logic untouched because marker-value dispatch is already generic. Set CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both in the example, preserving any other configured locations; show submit/delete/cancel and filter controls per current D-17, which supersedes the older background spec&#x27;s text-only-filter example. Add public icon/helper/settings additions to the appropriate changelog section without splitting the Breaking/migration pair. Keep downstream names out of all newly authored files; detailed generic follow-up goes into 06-09 acceptance.

Citations: 06-08-PLAN.md:115.
 Supplemental declaration candidate: `tests/test1/test_label_mode.py:150` strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True); `tests/test1/test_label_mode.py:199` CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope2", "context": "nope"}, CRUD_VIEWS_STRICT=False.
</details>

<details>
<summary><code>CRUD_VIEWS_STRICT</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:113` — In cv_button_data&#x27;s form branch perform the dynamic guard after effective mode/icon resolution. For icon mode with no icon, including registry-disabled semantic names, strict raises ValueError naming form kind; non-strict logs one warning per render using the existing button-data logger, switches to label and drops generated icon-only title/tooltip/host classes. Set CRUD_VIEWS_STRICT explicitly in both test branches. With empty label as well, retain the empty literal payload and log the both-missing diagnostic; do not invent text. Validate exact FORM_LEAF_KEYS membership, cancel-only URL, invalid caller kind/type and absence of action-only fields here. Add real crispy render tests with custom hooks and concrete/dynamic polymorphic providers so static skipping cannot create a silent hole. No placement/owner conflict warnings are introduced.

Citations: 06-06-PLAN.md:113.
 Supplemental declaration candidate: `tests/test1/test_label_mode.py:150` strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True); `tests/test1/test_label_mode.py:199` CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope2", "context": "nope"}, CRUD_VIEWS_STRICT=False.
</details>

<details>
<summary><code>Context.dicts</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:133` — Define owner recovery from Django Context.dicts before flattening: the actual adapter render(form, context)

Citations: 06-01-PLAN.md:133, 06-03-PLAN.md:102.

</details>

<details>
<summary><code>CrispyDeleteForm</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68, 06-06-PLAN.md:110.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:116` class CrispyDeleteForm(CrispyForm):; `tests/test1/test_crispy_buttons.py:52` class EraseForm(CrispyDeleteForm):.
</details>

<details>
<summary><code>CrispyDeleteForm.delete_icon</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68.

</details>

<details>
<summary><code>CrispyFormMixin</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68, 06-04-PLAN.md:104, 06-06-PLAN.md:110.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:11` class CrispyFormMixin:; `src/crud_views/lib/crispy/form.py:85` class CrispyModelForm(CrispyFormMixin, ModelForm):.
</details>

<details>
<summary><code>CrispyFormMixin.submit_icon</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68.

</details>

<details>
<summary><code>CrudView</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65, 06-03-PLAN.md:102, 06-06-PLAN.md:110.
 Supplemental declaration candidate: `src/crud_views/templatetags/crud_views.py:72` def cv_get_view(context) -> CrudView:; `src/crud_views/templatetags/crud_views.py:73` view: CrudView = context["view"].
</details>

<details>
<summary><code>CrudView.checks</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:110` — Introduce a static form checker wired from CrudView.checks. Inspect concrete statically selected form classes only while the helper property, action provider and relevant button/kwargs hooks retain known package implementations. Select the provider before controls (H-DELETE-STATIC): check CrispyDeleteForm first, whose helper renders delete via delete_icon plus cancel, never its inherited submit_icon. Otherwise default CrispyFormMixin/workflow helpers render submit via submit_icon plus cancel. Hook/helper overrides make the affected provider dynamic rather than evidence for inherited controls. Tests set inherited submit_icon=None on a default delete form and require no submit warning, then delete_icon=None and require a delete W292; custom delete helpers also get runtime coverage.

Citations: 06-06-PLAN.md:110.
 Supplemental declaration candidate: `src/crud_views_object_detail/lib/mixins.py:54` def checks(cls) -> Iterable[Check]:; `src/crud_views_workflow/lib/views.py:43` def checks(cls) -> Iterable[Check]:.
</details>

<details>
<summary><code>CrudView.cv_form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.

</details>

<details>
<summary><code>CrudView.cv_get_form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.

</details>

<details>
<summary><code>CrudViewsSettings</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.
 Supplemental declaration candidate: `src/crud_views/lib/settings.py:17` class CrudViewsSettings(BaseModel):; `src/crud_views/lib/settings.py:320` crud_views_settings = CrudViewsSettings().
</details>

<details>
<summary><code>CrudViewsSettings.form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.

</details>

<details>
<summary><code>DEFAULT_ICONS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:83` — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys through dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys and keep exhaustive class/default checks green.

Citations: 06-04-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/lib/icons.py:14` DEFAULT_ICONS: dict[str, str] = {; `src/crud_views/lib/icons.py:131` icons = {**DEFAULT_ICONS, **_THEME_ICONS, **(getattr(settings, "CRUD_VIEWS_ICONS", None) or {})}.
</details>

<details>
<summary><code>DELETE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:110` — Introduce a static form checker wired from CrudView.checks. Inspect concrete statically selected form classes only while the helper property, action provider and relevant button/kwargs hooks retain known package implementations. Select the provider before controls (H-DELETE-STATIC): check CrispyDeleteForm first, whose helper renders delete via delete_icon plus cancel, never its inherited submit_icon. Otherwise default CrispyFormMixin/workflow helpers render submit via submit_icon plus cancel. Hook/helper overrides make the affected provider dynamic rather than evidence for inherited controls. Tests set inherited submit_icon=None on a default delete form and require no submit warning, then delete_icon=None and require a delete W292; custom delete helpers also get runtime coverage.

Citations: 06-06-PLAN.md:110, 06-06-PLAN.md:133.
 Supplemental declaration candidate: `src/crud_views/lib/formsets/render_tree.py:244` delete_forms = [f for f in self.instance.forms if delete is True or f.cleaned_data.get("DELETE", False)]; `src/crud_views/static/crud_views/js/formset.js:236` del = this.assert_def(inputs.toArray().find((el) => el.name.endsWith("-DELETE"))),.
</details>

<details>
<summary><code>DIAGNOSTIC</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:84` — Addresses H-DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish shape from individual modes so D-16&#x27;s E210 extension has a concrete scope without adding a scalar API: non-dict or non-string keys yield one E211 and stop entry traversal; a string-keyed dict yields one E210 per invalid mode value in insertion order; unknown form keys with valid modes yield W291 on the view&#x27;s own cv_form_actions_label_mode only, naming sorted FORM_KINDS. None and {} are valid. This documented form-specific diagnostic distinction does not alter FORM-11 whole-map resolution semantics. Do not blindly invoke the old helper unchanged or change its behavior for context/list.

Citations: 06-06-PLAN.md:84, 06-06-PLAN.md:132, 06-08-PLAN.md:84, 06-08-PLAN.md:135.

</details>

<details>
<summary><code>DOC</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:115` — Per L-HIDDEN-WRAPPER, explain that visible filter actions now precede the pack-owned hidden-input wrapper and its retained margin/classes; hidden values/path are unchanged and no global crispy override is needed. Per L-TOOLTIP-DOC add form to the public data-cv-tooltip location inventory in javascript.md and the tooltip.js header comment, keeping runtime logic untouched because marker-value dispatch is already generic. Set CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both in the example, preserving any other configured locations; show submit/delete/cancel and filter controls per current D-17, which supersedes the older background spec&#x27;s text-only-filter example. Add public icon/helper/settings additions to the appropriate changelog section without splitting the Breaking/migration pair. Keep downstream names out of all newly authored files; detailed generic follow-up goes into 06-09 acceptance.

Citations: 06-08-PLAN.md:115, 06-08-PLAN.md:137.

</details>

<details>
<summary><code>EARLY</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:97` — Add form:hidden-label=&#x27;visually-hidden&#x27; and form:icon-host now, before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key never accepts a mode suffix. Test hidden-label/title/form-tooltip and host class behavior with an already registered icon; new semantic icon names/hooks remain 06-04 work.

Citations: 06-02-PLAN.md:97, 06-02-PLAN.md:158, 06-04-PLAN.md:82, 06-04-PLAN.md:123.

</details>

<details>
<summary><code>EXAMPLE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:250` — | M-EXAMPLE-CHECKS | MEDIUM | The example gate runs the existing SystemChecksTest that resolves the full URLconf and checks registered feature ViewSets, replacing bare manage.py check. |

Citations: 06-09-PLAN.md:250.

</details>

<details>
<summary><code>EXISTING</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68.

</details>

<details>
<summary><code>EXPECTED_KEYS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:97` — Add form:hidden-label=&#x27;visually-hidden&#x27; and form:icon-host now, before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key never accepts a mode suffix. Test hidden-label/title/form-tooltip and host class behavior with an already registered icon; new semantic icon names/hooks remain 06-04 work.

Citations: 06-02-PLAN.md:97, 06-02-PLAN.md:158, 06-04-PLAN.md:82.
 Supplemental declaration candidate: `tests/test1/test_button_classes.py:21` EXPECTED_KEYS = {.
</details>

<details>
<summary><code>FLAGGED</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:181` — | FORM-01 | unclassified | FLAGGED unresolved | 06-01 | History requirement covered; classifier shape remains unknown |

Citations: 06-09-PLAN.md:181, 06-09-PLAN.md:182.

</details>

<details>
<summary><code>FORM_KINDS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:89` — contracts at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS /

Citations: 06-01-PLAN.md:89, 06-02-PLAN.md:96, 06-02-PLAN.md:97, 06-02-PLAN.md:98, 06-04-PLAN.md:25, 06-06-PLAN.md:39, 06-06-PLAN.md:84.
 Supplemental declaration candidate: `src/crud_views/lib/button_classes.py:210` FORM_KINDS: frozenset[str] = frozenset({"submit", "cancel", "delete", "filter-submit", "filter-reset"}); `tests/test1/test_button_classes_checks.py:111` FORM_KINDS = ("submit", "cancel", "delete", "filter-submit", "filter-reset").
</details>

<details>
<summary><code>FORM_LEAF_KEYS</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:116` — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

Citations: 06-01-PLAN.md:116, 06-02-PLAN.md:79, 06-02-PLAN.md:98, 06-06-PLAN.md:113, 06-08-PLAN.md:83, 06-09-PLAN.md:155.

</details>

<details>
<summary><code>FormActions</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:140` — helper overlay by its provenance/response metadata, never a fixed stack offset: FormActions leaves extra

Citations: 06-01-PLAN.md:140, 06-01-PLAN.md:141, 06-01-PLAN.md:145, 06-01-PLAN.md:239, 06-02-PLAN.md:88, 06-03-PLAN.md:27, 06-03-PLAN.md:92, 06-03-PLAN.md:98, 06-03-PLAN.md:102, 06-03-PLAN.md:103, 06-03-PLAN.md:107, 06-03-PLAN.md:122, 06-05-PLAN.md:24, 06-05-PLAN.md:40, 06-05-PLAN.md:66, 06-05-PLAN.md:70, 06-05-PLAN.md:76, 06-05-PLAN.md:98, 06-05-PLAN.md:104, 06-08-PLAN.md:31, 06-08-PLAN.md:99, 06-09-PLAN.md:194.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:53` def get_form_actions(self) -> FormActions:.
</details>

<details>
<summary><code>FormActions.render</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92, 06-03-PLAN.md:102.
 Supplemental declaration candidate: `src/crud_views/templatetags/crud_views.py:333` def render(self, context):; `src/crud_views/lib/view/base.py:109` cv_header_template: str | None = None  # template snippet to render header label.
</details>

<details>
<summary><code>FormData</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:152` — jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded

Citations: 06-01-PLAN.md:152, 06-07-PLAN.md:27, 06-07-PLAN.md:36, 06-07-PLAN.md:74, 06-07-PLAN.md:80, 06-07-PLAN.md:84, 06-07-PLAN.md:135, 06-07-PLAN.md:152, 06-09-PLAN.md:162, 06-09-PLAN.md:190.

</details>

<details>
<summary><code>FormHelper</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92, 06-05-PLAN.md:66, 06-05-PLAN.md:81, 06-08-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/views/list.py:57` class ListViewFilterFormHelper(FormHelper):; `src/crud_views/lib/crispy/form.py:42` def helper(self) -> FormHelper:.
</details>

<details>
<summary><code>FormHelper.get_attributes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.

</details>

<details>
<summary><code>GOAL</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:122` — | GOAL | Real buttons through leaf, shared label/class contract, template-injection safety, unchanged POST | 02–09 | COVERED |

Citations: 06-09-PLAN.md:122, 06-09-PLAN.md:123.

</details>

<details>
<summary><code>HELPER</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:81` — Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form argument when supplied, preserving upstream association without rebuilding its fields (M-HELPER-STATE). Keep a truthy instance layout before crispy dispatch even for no-layout or None actions; a private Layout subclass with __bool__ returning True is a concrete option. All new lifecycle/owner state uses underscore-prefixed attributes so get_attributes does not publish it. Populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper&#x27;s configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged.

Citations: 06-05-PLAN.md:81, 06-05-PLAN.md:104, 06-05-PLAN.md:123.

</details>

<details>
<summary><code>HIDDEN</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:82` — Per L-HIDDEN-WRAPPER and D-01, retain the installed pack&#x27;s hidden-input wrapper and margin after the visible layout actions; this ordering is accepted pack-owned behavior. Extend the filter golden harness to capture the deterministic visible-action/hidden-wrapper region, excluding CSRF, and compare existing hidden names/values independently from this expected ordering change. Pin wrapper classes/order and the absence of visible duplicate actions. Update only filter expectations and its phase-owned golden after comparison to 06-01; 06-08 documents the accepted wrapper behavior rather than globally overriding inputs.html.

Citations: 06-05-PLAN.md:82, 06-05-PLAN.md:124, 06-08-PLAN.md:115, 06-08-PLAN.md:137.

</details>

<details>
<summary><code>HTML</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:172` — | Form data to HTML | Literal text must not become templates or markup |

Citations: 06-02-PLAN.md:172, 06-04-PLAN.md:68.

</details>

<details>
<summary><code>IDs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:123` — single-word names literal and upstream generated IDs unchanged. Compare old/new wire names for whitespace,

Citations: 06-01-PLAN.md:123, 06-02-PLAN.md:39, 06-02-PLAN.md:99, 06-02-PLAN.md:118, 06-02-PLAN.md:122, 06-02-PLAN.md:159, 06-05-PLAN.md:25, 06-05-PLAN.md:74, 06-05-PLAN.md:81, 06-06-PLAN.md:46, 06-06-PLAN.md:68, 06-06-PLAN.md:90, 06-06-PLAN.md:92, 06-08-PLAN.md:114.

</details>

<details>
<summary><code>JSON</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:173` — The source JSON reports applicable=30 and unclassified=2; its items array has exactly 30 entries. Thus 28

Citations: 06-09-PLAN.md:173.

</details>

<details>
<summary><code>KEYSET</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:97` — Add form:hidden-label=&#x27;visually-hidden&#x27; and form:icon-host now, before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key never accepts a mode suffix. Test hidden-label/title/form-tooltip and host class behavior with an already registered icon; new semantic icon names/hooks remain 06-04 work.

Citations: 06-02-PLAN.md:97, 06-02-PLAN.md:158, 06-04-PLAN.md:82, 06-04-PLAN.md:123, 06-08-PLAN.md:83, 06-08-PLAN.md:134, 06-09-PLAN.md:253.

</details>

<details>
<summary><code>LABEL_MODE_DEFAULTS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:95` — Update test_label_mode.py and test_button_data.py location/default assertions in this producing task, preserving set(LABEL_MODE_DEFAULTS) == LOCATIONS, before running the tracer shard.

Citations: 06-02-PLAN.md:95, 06-02-PLAN.md:96, 06-08-PLAN.md:115.
 Supplemental declaration candidate: `src/crud_views/lib/view/label_mode.py:23` LABEL_MODE_DEFAULTS: Mapping[str, str] = MappingProxyType({"context": "icon", "list": "icon", "card": "both"}).
</details>

<details>
<summary><code>LEAF_KEYS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:116` — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

Citations: 06-01-PLAN.md:116, 06-02-PLAN.md:79, 06-02-PLAN.md:98, 06-06-PLAN.md:113, 06-08-PLAN.md:83, 06-09-PLAN.md:155.
 Supplemental declaration candidate: `src/crud_views/lib/view/button_data.py:16` LEAF_KEYS = frozenset(.
</details>

<details>
<summary><code>LOCATIONS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Citations: 06-01-PLAN.md:90, 06-02-PLAN.md:95, 06-02-PLAN.md:96, 06-02-PLAN.md:97, 06-02-PLAN.md:157, 06-03-PLAN.md:123, 06-08-PLAN.md:83, 06-08-PLAN.md:134, 06-09-PLAN.md:253.
 Supplemental declaration candidate: `src/crud_views/lib/settings.py:159` allowed = sorted(LOCATIONS); `src/crud_views/lib/view/button_data.py:12` LOCATIONS = frozenset({"context", "list", "card"}).
</details>

<details>
<summary><code>Layout</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:146` — Deep-copy declared layouts per helper instance. A no-layout helper gets a truthy instance Layout so crispy

Citations: 06-01-PLAN.md:146, 06-02-PLAN.md:88, 06-05-PLAN.md:81, 06-05-PLAN.md:125.
 Supplemental declaration candidate: `tests/test1/app/views.py:289` layout = Layout(Row(Column4("name"))).
</details>

<details>
<summary><code>ListViewFilterFormHelper</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:66` — NEW public method: ListViewFilterFormHelper.get_form_actions() -&gt; FormActions | None. NEW render_layout override and private instance layout/action initialization state. No new test files; only existing phase-owned filter golden changes.

Citations: 06-05-PLAN.md:66, 06-08-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/views/list.py:57` class ListViewFilterFormHelper(FormHelper):; `tests/test1/app/views.py:288` class PublisherFilterFormHelper(ListViewFilterFormHelper):.
</details>

<details>
<summary><code>ListViewFilterFormHelper.get_form_actions</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:66` — NEW public method: ListViewFilterFormHelper.get_form_actions() -&gt; FormActions | None. NEW render_layout override and private instance layout/action initialization state. No new test files; only existing phase-owned filter golden changes.

Citations: 06-05-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:53` def get_form_actions(self) -> FormActions:.
</details>

<details>
<summary><code>ListViewTableFilterMixin</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:81` — Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form argument when supplied, preserving upstream association without rebuilding its fields (M-HELPER-STATE). Keep a truthy instance layout before crispy dispatch even for no-layout or None actions; a private Layout subclass with __bool__ returning True is a concrete option. All new lifecycle/owner state uses underscore-prefixed attributes so get_attributes does not publish it. Populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper&#x27;s configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged.

Citations: 06-05-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/mixins.py:299` class ListViewTableFilterMixin(FilterView):; `tests/test1/app/views.py:300` class PublisherListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):.
</details>

<details>
<summary><code>MAIN</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:246` — | H-MAIN | Resolved by explicit user decision D-18 after cycle 1: verify completed Phase 1/2 contracts on the executing working branch, recording HEAD and test evidence before the spec. ROADMAP.md and CONTEXT.md now carry this requirement. No claim that main changed; no merge or branch switch. Dependency verification, spec-first and baseline-first gates remain. |

Citations: 06-01-PLAN.md:246.

</details>

<details>
<summary><code>NAME</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:124` — punctuation and Unicode multi-word names without evaluating them as templates (review M-NAME, D-15/D-17).

Citations: 06-01-PLAN.md:124, 06-01-PLAN.md:239, 06-02-PLAN.md:122, 06-02-PLAN.md:159.

</details>

<details>
<summary><code>NODE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:95` — Before the first per-wave JS gate, complete environment-only preparation for M-NODE-COMMANDS. Inspect

Citations: 06-01-PLAN.md:95, 06-01-PLAN.md:101, 06-01-PLAN.md:241, 06-07-PLAN.md:79, 06-07-PLAN.md:134, 06-07-PLAN.md:140, 06-09-PLAN.md:251.

</details>

<details>
<summary><code>OFF</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:112` — Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF, use the effective icon after semantic registry resolution: explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty are missing. Test each with known default submit/delete/filter controls. Named-but-unregistered icons retain separate registry diagnostics; this is distinct from intentional registry disabling, which produces no registry warning and therefore needs W292. Static inspection must not invoke arbitrary user renderers; determine disabled mappings through the registry resolution contract, and use actual rendered icon availability at runtime.

Citations: 06-06-PLAN.md:112, 06-06-PLAN.md:134.

</details>

<details>
<summary><code>OWNERS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:142` — a later button, nested row forms with explicit helpers, and None at the page layer (review M-OWNERS).

Citations: 06-01-PLAN.md:142, 06-01-PLAN.md:239, 06-03-PLAN.md:102, 06-03-PLAN.md:122.

</details>

<details>
<summary><code>PATH</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:105` — Node directory to PATH, uses the selected Node to assert process.execPath/version and unchanged lock hash,

Citations: 06-01-PLAN.md:105.
 Supplemental declaration candidate: `src/crud_views/management/commands/cv_assets.py:27` lines = [("KEY", "KIND", "DELIVERY", "PATH")].
</details>

<details>
<summary><code>PATTERNS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:60` — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

Citations: 06-01-PLAN.md:60, 06-02-PLAN.md:72, 06-03-PLAN.md:58, 06-04-PLAN.md:61, 06-05-PLAN.md:59, 06-06-PLAN.md:61, 06-07-PLAN.md:58, 06-08-PLAN.md:68, 06-09-PLAN.md:53.

</details>

<details>
<summary><code>PATTERNS.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:60` — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

Citations: 06-01-PLAN.md:60, 06-02-PLAN.md:72, 06-03-PLAN.md:58, 06-04-PLAN.md:61, 06-05-PLAN.md:59, 06-06-PLAN.md:61, 06-07-PLAN.md:58, 06-08-PLAN.md:68, 06-09-PLAN.md:53.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>PAYLOAD</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:181` — submitter regression, not a pre-existing submitter-only payload assertion (review M-PAYLOAD, D-17).

Citations: 06-01-PLAN.md:181, 06-01-PLAN.md:238, 06-09-PLAN.md:68, 06-09-PLAN.md:252.

</details>

<details>
<summary><code>POLYMORPHIC</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:111` — For filter helpers inspect the configured helper class only when default get_form_actions is inherited. For a concrete dict-valued polymorphic_forms mapping inspect each distinct form class using the same provider rules, without selecting a request/model instance; identify form class and kind in warnings and deduplicate identical repeated class/kind entries locally per traversal (M-POLYMORPHIC). Missing/custom mapping providers skip static inference and get actual polymorphic create/update runtime tests. Never instantiate forms/helpers, call request-dependent get_form_class, or execute custom action hooks during checks.

Citations: 06-06-PLAN.md:111, 06-06-PLAN.md:135.

</details>

<details>
<summary><code>PROJECT</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:54` — @.planning/PROJECT.md

Citations: 06-01-PLAN.md:54, 06-02-PLAN.md:67, 06-03-PLAN.md:53, 06-04-PLAN.md:56, 06-05-PLAN.md:54, 06-06-PLAN.md:56, 06-07-PLAN.md:53, 06-08-PLAN.md:63, 06-09-PLAN.md:48.

</details>

<details>
<summary><code>PROJECT.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:54` — @.planning/PROJECT.md

Citations: 06-01-PLAN.md:54, 06-02-PLAN.md:67, 06-03-PLAN.md:53, 06-04-PLAN.md:56, 06-05-PLAN.md:54, 06-06-PLAN.md:56, 06-07-PLAN.md:53, 06-08-PLAN.md:63, 06-09-PLAN.md:48.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>REGISTRY</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:112` — Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF, use the effective icon after semantic registry resolution: explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty are missing. Test each with known default submit/delete/filter controls. Named-but-unregistered icons retain separate registry diagnostics; this is distinct from intentional registry disabling, which produces no registry warning and therefore needs W292. Static inspection must not invoke arbitrary user renderers; determine disabled mappings through the registry resolution contract, and use actual rendered icon availability at runtime.

Citations: 06-06-PLAN.md:112, 06-06-PLAN.md:134.

</details>

<details>
<summary><code>REQ</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:124` — | REQ | FORM-01 | 01 | COVERED |

Citations: 06-09-PLAN.md:124, 06-09-PLAN.md:125, 06-09-PLAN.md:126, 06-09-PLAN.md:127, 06-09-PLAN.md:128, 06-09-PLAN.md:129, 06-09-PLAN.md:130, 06-09-PLAN.md:131, 06-09-PLAN.md:132, 06-09-PLAN.md:133, 06-09-PLAN.md:134, 06-09-PLAN.md:135, 06-09-PLAN.md:136.

</details>

<details>
<summary><code>REQUIREMENTS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:57` — @.planning/REQUIREMENTS.md

Citations: 06-01-PLAN.md:57.

</details>

<details>
<summary><code>REQUIREMENTS.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:57` — @.planning/REQUIREMENTS.md

Citations: 06-01-PLAN.md:57.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>RESEARCH</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:59` — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

Citations: 06-01-PLAN.md:59, 06-02-PLAN.md:71, 06-03-PLAN.md:57, 06-04-PLAN.md:60, 06-05-PLAN.md:58, 06-06-PLAN.md:60, 06-07-PLAN.md:57, 06-07-PLAN.md:71, 06-07-PLAN.md:113, 06-08-PLAN.md:67, 06-09-PLAN.md:52, 06-09-PLAN.md:155, 06-09-PLAN.md:156, 06-09-PLAN.md:157, 06-09-PLAN.md:158, 06-09-PLAN.md:159, 06-09-PLAN.md:160, 06-09-PLAN.md:161, 06-09-PLAN.md:162, 06-09-PLAN.md:163, 06-09-PLAN.md:164, 06-09-PLAN.md:165.

</details>

<details>
<summary><code>RESEARCH.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:59` — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

Citations: 06-01-PLAN.md:59, 06-02-PLAN.md:71, 06-03-PLAN.md:57, 06-04-PLAN.md:60, 06-05-PLAN.md:58, 06-06-PLAN.md:60, 06-07-PLAN.md:57, 06-07-PLAN.md:71, 06-07-PLAN.md:113, 06-08-PLAN.md:67, 06-09-PLAN.md:52.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>ROADMAP</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:55` — @.planning/ROADMAP.md

Citations: 06-01-PLAN.md:55, 06-01-PLAN.md:246, 06-02-PLAN.md:68, 06-03-PLAN.md:54, 06-04-PLAN.md:57, 06-05-PLAN.md:55, 06-06-PLAN.md:57, 06-07-PLAN.md:54, 06-08-PLAN.md:64, 06-09-PLAN.md:49.

</details>

<details>
<summary><code>ROADMAP.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:55` — @.planning/ROADMAP.md

Citations: 06-01-PLAN.md:55, 06-01-PLAN.md:246, 06-02-PLAN.md:68, 06-03-PLAN.md:54, 06-04-PLAN.md:57, 06-05-PLAN.md:55, 06-06-PLAN.md:57, 06-07-PLAN.md:54, 06-08-PLAN.md:64, 06-09-PLAN.md:49.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>RUNTIME</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:10` — - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json

Citations: 06-01-PLAN.md:10, 06-01-PLAN.md:69, 06-01-PLAN.md:77, 06-01-PLAN.md:102, 06-07-PLAN.md:65.

</details>

<details>
<summary><code>RUNTIME.json</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:10` — - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json

Citations: 06-01-PLAN.md:10, 06-01-PLAN.md:69, 06-01-PLAN.md:77, 06-01-PLAN.md:102, 06-07-PLAN.md:65.
 Supplemental declaration candidate: `src/crud_views/lib/vendor.py:59` data = json.loads(stamp.read_text()); `src/crud_views/lib/views/mixins.py:345` data = json.loads(request.body.decode("utf-8")).
</details>

<details>
<summary><code>SHA</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:157` — Under Prerequisite evidence record the executing branch HEAD SHA, completed-contract/test evidence and verification date.

Citations: 06-01-PLAN.md:157, 06-01-PLAN.md:160, 06-01-PLAN.md:163, 06-01-PLAN.md:183, 06-01-PLAN.md:240.

</details>

<details>
<summary><code>SHAs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:202` — Commit these test additions and fixtures alone while src is still unchanged. Record both baseline commit SHAs,

Citations: 06-01-PLAN.md:202.

</details>

<details>
<summary><code>SLOP</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:257` — | T-06-SC | Tampering | runtime/package restoration | high | mitigate | Official checksum-verified isolated Node; exact npm lock restoration under the research audit; blocking human gate for any ASSUMED/SUS package and no SLOP |

Citations: 06-01-PLAN.md:257, 06-02-PLAN.md:180, 06-03-PLAN.md:141, 06-04-PLAN.md:141, 06-05-PLAN.md:144, 06-06-PLAN.md:154, 06-07-PLAN.md:154, 06-08-PLAN.md:155, 06-09-PLAN.md:270.

</details>

<details>
<summary><code>SLOT</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:98` — Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

Citations: 06-02-PLAN.md:98, 06-02-PLAN.md:160, 06-08-PLAN.md:114, 06-08-PLAN.md:136.

</details>

<details>
<summary><code>SPEC</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-SPEC.md

Citations: 06-01-PLAN.md:8, 06-01-PLAN.md:31, 06-01-PLAN.md:66, 06-01-PLAN.md:77, 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-01-PLAN.md:197, 06-02-PLAN.md:73, 06-03-PLAN.md:59, 06-03-PLAN.md:71, 06-03-PLAN.md:92, 06-04-PLAN.md:62, 06-05-PLAN.md:60, 06-05-PLAN.md:72, 06-06-PLAN.md:62, 06-06-PLAN.md:99, 06-07-PLAN.md:59, 06-08-PLAN.md:69, 06-08-PLAN.md:81, 06-09-PLAN.md:54, 06-09-PLAN.md:66.

</details>

<details>
<summary><code>SPEC.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-SPEC.md

Citations: 06-01-PLAN.md:8, 06-01-PLAN.md:31, 06-01-PLAN.md:66, 06-01-PLAN.md:77, 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-01-PLAN.md:197, 06-02-PLAN.md:73, 06-03-PLAN.md:59, 06-03-PLAN.md:71, 06-03-PLAN.md:92, 06-04-PLAN.md:62, 06-05-PLAN.md:60, 06-05-PLAN.md:72, 06-06-PLAN.md:62, 06-06-PLAN.md:99, 06-07-PLAN.md:59, 06-08-PLAN.md:69, 06-08-PLAN.md:81, 06-09-PLAN.md:54, 06-09-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>STATE</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:56` — @.planning/STATE.md

Citations: 06-01-PLAN.md:56, 06-02-PLAN.md:69, 06-03-PLAN.md:55, 06-04-PLAN.md:58, 06-05-PLAN.md:56, 06-05-PLAN.md:81, 06-05-PLAN.md:104, 06-05-PLAN.md:123, 06-06-PLAN.md:58, 06-07-PLAN.md:55, 06-08-PLAN.md:65, 06-09-PLAN.md:50.

</details>

<details>
<summary><code>STATE.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:56` — @.planning/STATE.md

Citations: 06-01-PLAN.md:56, 06-02-PLAN.md:69, 06-03-PLAN.md:55, 06-04-PLAN.md:58, 06-05-PLAN.md:56, 06-06-PLAN.md:58, 06-07-PLAN.md:55, 06-08-PLAN.md:65, 06-09-PLAN.md:50.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>STATIC</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:110` — Introduce a static form checker wired from CrudView.checks. Inspect concrete statically selected form classes only while the helper property, action provider and relevant button/kwargs hooks retain known package implementations. Select the provider before controls (H-DELETE-STATIC): check CrispyDeleteForm first, whose helper renders delete via delete_icon plus cancel, never its inherited submit_icon. Otherwise default CrispyFormMixin/workflow helpers render submit via submit_icon plus cancel. Hook/helper overrides make the affected provider dynamic rather than evidence for inherited controls. Tests set inherited submit_icon=None on a default delete form and require no submit warning, then delete_icon=None and require a delete W292; custom delete helpers also get runtime coverage.

Citations: 06-06-PLAN.md:110, 06-06-PLAN.md:133.

</details>

<details>
<summary><code>SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:263` — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

Citations: 06-01-PLAN.md:263, 06-02-PLAN.md:86, 06-02-PLAN.md:136, 06-02-PLAN.md:186, 06-03-PLAN.md:147, 06-04-PLAN.md:147, 06-05-PLAN.md:150, 06-06-PLAN.md:160, 06-07-PLAN.md:160, 06-08-PLAN.md:161, 06-09-PLAN.md:66, 06-09-PLAN.md:81, 06-09-PLAN.md:276.

</details>

<details>
<summary><code>SUS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:257` — | T-06-SC | Tampering | runtime/package restoration | high | mitigate | Official checksum-verified isolated Node; exact npm lock restoration under the research audit; blocking human gate for any ASSUMED/SUS package and no SLOP |

Citations: 06-01-PLAN.md:257, 06-02-PLAN.md:180, 06-03-PLAN.md:141, 06-04-PLAN.md:141, 06-05-PLAN.md:144, 06-06-PLAN.md:154, 06-07-PLAN.md:154, 06-08-PLAN.md:155, 06-09-PLAN.md:270.

</details>

<details>
<summary><code>SafeData</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:118` — Normalize text to a plain str that has no SafeData trust marker before exactly one Django escaping boundary;

Citations: 06-01-PLAN.md:118, 06-02-PLAN.md:99.

</details>

<details>
<summary><code>SafeString</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:37` — - &quot;D-15: Empty, Unicode, lazy, SafeString and template-looking values remain exact literal DOM text and values; none evaluates template syntax or creates injected nodes/attributes.&quot;

Citations: 06-02-PLAN.md:37, 06-02-PLAN.md:116, 06-02-PLAN.md:122, 06-02-PLAN.md:177, 06-09-PLAN.md:157, 06-09-PLAN.md:192.
 Supplemental declaration candidate: `src/crud_views/lib/icons.py:205` def font_renderer(name: str, *, css: str, config: dict) -> SafeString:; `src/crud_views/lib/icons.py:223` def render_icon(value: str | None, css: str = "") -> SafeString:.
</details>

<details>
<summary><code>SubmitEvent</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:152` — jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded

Citations: 06-01-PLAN.md:152, 06-07-PLAN.md:27, 06-07-PLAN.md:36, 06-07-PLAN.md:73, 06-07-PLAN.md:80, 06-09-PLAN.md:162.

</details>

<details>
<summary><code>SubmitEvent.submitter</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:27` — - &quot;The native SubmitEvent.submitter and FormData contract is tested on exact locked JS packages under a compatible isolated runtime, without hiding failure through mocks/polyfills.&quot;

Citations: 06-07-PLAN.md:27, 06-07-PLAN.md:73.
 Supplemental declaration candidate: `src/crud_views/static/crud_views/js/modal.js:75` function cvModalSubmit(form, submitter) {.
</details>

<details>
<summary><code>SystemChecksTest</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:235` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt;

Citations: 06-09-PLAN.md:235, 06-09-PLAN.md:250.

</details>

<details>
<summary><code>TOOLTIP</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:115` — Per L-HIDDEN-WRAPPER, explain that visible filter actions now precede the pack-owned hidden-input wrapper and its retained margin/classes; hidden values/path are unchanged and no global crispy override is needed. Per L-TOOLTIP-DOC add form to the public data-cv-tooltip location inventory in javascript.md and the tooltip.js header comment, keeping runtime logic untouched because marker-value dispatch is already generic. Set CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both in the example, preserving any other configured locations; show submit/delete/cancel and filter controls per current D-17, which supersedes the older background spec&#x27;s text-only-filter example. Add public icon/helper/settings additions to the appropriate changelog section without splitting the Breaking/migration pair. Keep downstream names out of all newly authored files; detailed generic follow-up goes into 06-09 acceptance.

Citations: 06-08-PLAN.md:115, 06-08-PLAN.md:137.

</details>

<details>
<summary><code>TemplateNameMixin</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:112` — &lt;read_first&gt;The spec literal/attribute rules; crispy BaseInput and TemplateNameMixin in the declared-floor environment; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:112.

</details>

<details>
<summary><code>URLconf</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:236` — &lt;fails_when&gt;The URLconf does not register feature ViewSets, the registered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt;

Citations: 06-09-PLAN.md:236, 06-09-PLAN.md:250.

</details>

<details>
<summary><code>UTILITIES</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:97` — Add form:hidden-label=&#x27;visually-hidden&#x27; and form:icon-host now, before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key never accepts a mode suffix. Test hidden-label/title/form-tooltip and host class behavior with an already registered icon; new semantic icon names/hooks remain 06-04 work.

Citations: 06-02-PLAN.md:97, 06-02-PLAN.md:158, 06-04-PLAN.md:82, 06-04-PLAN.md:123.

</details>

<details>
<summary><code>VALIDATION</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:61` — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

Citations: 06-01-PLAN.md:61, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:66, 06-09-PLAN.md:68, 06-09-PLAN.md:80, 06-09-PLAN.md:81.

</details>

<details>
<summary><code>VALIDATION.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:61` — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

Citations: 06-01-PLAN.md:61, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:66, 06-09-PLAN.md:80, 06-09-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>VARIANT_LOCATIONS</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Citations: 06-01-PLAN.md:90, 06-02-PLAN.md:96, 06-02-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/button_classes.py:209` VARIANT_LOCATIONS: frozenset[str] = frozenset({"context", "list", "card"}).
</details>

<details>
<summary><code>ValueError</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:98` — Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

Citations: 06-02-PLAN.md:98, 06-06-PLAN.md:26, 06-06-PLAN.md:112, 06-06-PLAN.md:113, 06-08-PLAN.md:114.

</details>

<details>
<summary><code>ViewSet</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:23` — - &quot;D-13: Form mode maps select view, else ViewSet, else setting as whole maps; an empty selected map and missing kind fall directly to the live form floor.&quot;

Citations: 06-03-PLAN.md:23, 06-03-PLAN.md:65, 06-03-PLAN.md:73, 06-03-PLAN.md:85, 06-06-PLAN.md:78, 06-06-PLAN.md:80, 06-06-PLAN.md:85, 06-06-PLAN.md:92, 06-08-PLAN.md:83, 06-08-PLAN.md:84, 06-09-PLAN.md:206, 06-09-PLAN.md:236, 06-09-PLAN.md:250.
 Supplemental declaration candidate: `src/crud_views/checks.py:392` owner = f"ViewSet {viewset.name!r} view {key!r}"; `src/crud_views/lib/session.py:23` views: dict[str, ViewData] = Field(default_factory=default_dict)  # ViewSet name to ViewData.
</details>

<details>
<summary><code>ViewSet.form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65.

</details>

<details>
<summary><code>ViewSets</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:236` — &lt;fails_when&gt;The URLconf does not register feature ViewSets, the registered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt;

Citations: 06-09-PLAN.md:236, 06-09-PLAN.md:250.

</details>

<details>
<summary><code>WRAPPER</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:82` — Per L-HIDDEN-WRAPPER and D-01, retain the installed pack&#x27;s hidden-input wrapper and margin after the visible layout actions; this ordering is accepted pack-owned behavior. Extend the filter golden harness to capture the deterministic visible-action/hidden-wrapper region, excluding CSRF, and compare existing hidden names/values independently from this expected ordering change. Pin wrapper classes/order and the absence of visible duplicate actions. Update only filter expectations and its phase-owned golden after comparison to 06-01; 06-08 documents the accepted wrapper behavior rather than globally overriding inputs.html.

Citations: 06-05-PLAN.md:82, 06-05-PLAN.md:124, 06-08-PLAN.md:115, 06-08-PLAN.md:137.

</details>

<details>
<summary><code>WorkflowForm</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68.
 Supplemental declaration candidate: `src/crud_views_workflow/lib/forms.py:11` class WorkflowForm(CrispyForm):; `tests/test1/test_workflow.py:556` form_class = WorkflowForm.
</details>

<details>
<summary><code>WorkflowForm.submit_icon</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68.

</details>

<details>
<summary><code>_action_settings_messages</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:74` — &lt;read_first&gt;src/crud_views/lib/view/action_menu.py; src/crud_views/lib/view/base.py (checks); src/crud_views/lib/settings.py (_action_settings_messages); src/crud_views/lib/viewset/__init__.py (map validator); tests/test1/test_action_label_mode_config.py&lt;/read_first&gt;

Citations: 06-06-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/settings.py:100` def _action_settings_messages(self) -> list[CheckMessage]:.
</details>

<details>
<summary><code>action_menu</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:11` — - src/crud_views/lib/view/action_menu.py

Citations: 06-06-PLAN.md:11, 06-06-PLAN.md:38, 06-06-PLAN.md:73, 06-06-PLAN.md:74, 06-08-PLAN.md:10, 06-08-PLAN.md:44, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:83, 06-08-PLAN.md:84.

</details>

<details>
<summary><code>action_menus</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:10` — - docs/reference/action_menus.md

Citations: 06-08-PLAN.md:10, 06-08-PLAN.md:44, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:83, 06-08-PLAN.md:84.
 Supplemental declaration candidate: `tests/test1/test_label_mode_docs.py:16` ACTION_MENUS_MD = DOCS / "reference" / "action_menus.md"; `tests/test1/test_card_blocks.py:2` class keys. The stock markup itself is pinned by the action_menus card goldens.""".
</details>

<details>
<summary><code>action_menus.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:10` — - docs/reference/action_menus.md

Citations: 06-08-PLAN.md:10, 06-08-PLAN.md:44, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>add_input</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:22` — - &quot;D-01, D-02: Custom add_input controls remain legacy inputs quietly; hidden sort/order/direction inputs keep their current path and values.&quot;

Citations: 06-05-PLAN.md:22, 06-05-PLAN.md:101, 06-05-PLAN.md:104, 06-08-PLAN.md:99, 06-08-PLAN.md:114.

</details>

<details>
<summary><code>button_classes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:10, 06-02-PLAN.md:13, 06-02-PLAN.md:16, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:97, 06-02-PLAN.md:102, 06-04-PLAN.md:32, 06-04-PLAN.md:41, 06-04-PLAN.md:74, 06-04-PLAN.md:86, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `tests/test1/test_button_leaves.py:281` saved = dict(button_classes._THEME_BUTTON_CLASSES); `tests/test1/test_button_classes_templates.py:24` EXEMPT_FILES = {"crud_views/lib/button_classes.py"}.
</details>

<details>
<summary><code>button_data</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Citations: 06-01-PLAN.md:83, 06-01-PLAN.md:160, 06-02-PLAN.md:8, 06-02-PLAN.md:21, 06-02-PLAN.md:36, 06-02-PLAN.md:45, 06-02-PLAN.md:49, 06-02-PLAN.md:51, 06-02-PLAN.md:79, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:95, 06-02-PLAN.md:98, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:14, 06-06-PLAN.md:41, 06-06-PLAN.md:68, 06-06-PLAN.md:98, 06-06-PLAN.md:99, 06-06-PLAN.md:113, 06-06-PLAN.md:116.

</details>

<details>
<summary><code>button_data.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Citations: 06-01-PLAN.md:83, 06-01-PLAN.md:160, 06-02-PLAN.md:8, 06-02-PLAN.md:21, 06-02-PLAN.md:45, 06-02-PLAN.md:49, 06-02-PLAN.md:51, 06-02-PLAN.md:79, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:95, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:14, 06-06-PLAN.md:41, 06-06-PLAN.md:68, 06-06-PLAN.md:98, 06-06-PLAN.md:99, 06-06-PLAN.md:116.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>check_viewsets</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:28` — - &quot;Empty and non-ASCII invalid keys/values yield deterministic diagnostics; malformed floor/map errors survive check_viewsets and are never hidden by W292.&quot;

Citations: 06-06-PLAN.md:28, 06-06-PLAN.md:76, 06-06-PLAN.md:86.
 Supplemental declaration candidate: `src/crud_views/checks.py:20` def check_viewsets(app_configs=None, **kwargs):; `tests/test1/test_context_button_label_mode.py:291` messages = check_viewsets().
</details>

<details>
<summary><code>checks.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:12` — - tests/test1/test_form_button_checks.py

Citations: 06-06-PLAN.md:12, 06-06-PLAN.md:32, 06-06-PLAN.md:68, 06-06-PLAN.md:73, 06-06-PLAN.md:89, 06-06-PLAN.md:98, 06-06-PLAN.md:116, 06-07-PLAN.md:113, 06-09-PLAN.md:33.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>crispy_floor</code> — SKIPPED: declared phase output / execution summary</summary>

`06-07-PLAN.md:65` — NEW nox session: crispy_floor, Python 3.12 with Django 4.2 and 6.0 variants and exact crispy 2.0/bootstrap5 2023.10 pins. Existing JS source files are conditional bug-fix ownership only; leave them byte-identical if the new regression tests pass. Runtime prerequisites: 06-01 task 1 creates 06-js-verify.sh and 06-JS-RUNTIME.json before per-wave JS sampling; every JS command below reasserts that selected runtime and exact lock-backed environment, including in fresh shells.

Citations: 06-07-PLAN.md:65, 06-07-PLAN.md:115, 06-07-PLAN.md:118, 06-07-PLAN.md:157.

</details>

<details>
<summary><code>crud_views</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:81` — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

Citations: 06-01-PLAN.md:81, 06-01-PLAN.md:82, 06-01-PLAN.md:83, 06-02-PLAN.md:8, 06-02-PLAN.md:9, 06-02-PLAN.md:10, 06-02-PLAN.md:17, 06-02-PLAN.md:18, 06-02-PLAN.md:43, 06-02-PLAN.md:45, 06-02-PLAN.md:48, 06-02-PLAN.md:49, 06-02-PLAN.md:51, 06-02-PLAN.md:52, 06-02-PLAN.md:79, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:111, 06-03-PLAN.md:8, 06-03-PLAN.md:9, 06-03-PLAN.md:10, 06-03-PLAN.md:11, 06-03-PLAN.md:29, 06-03-PLAN.md:31, 06-03-PLAN.md:34, 06-03-PLAN.md:35, 06-03-PLAN.md:37, 06-03-PLAN.md:38, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-03-PLAN.md:91, 06-03-PLAN.md:92, 06-04-PLAN.md:8, 06-04-PLAN.md:9, 06-04-PLAN.md:11, 06-04-PLAN.md:12, 06-04-PLAN.md:13, 06-04-PLAN.md:30, 06-04-PLAN.md:32, 06-04-PLAN.md:34, 06-04-PLAN.md:37, 06-04-PLAN.md:38, 06-04-PLAN.md:40, 06-04-PLAN.md:41, 06-04-PLAN.md:73, 06-04-PLAN.md:74, 06-04-PLAN.md:95, 06-04-PLAN.md:96, 06-05-PLAN.md:8, 06-05-PLAN.md:30, 06-05-PLAN.md:35, 06-05-PLAN.md:36, 06-05-PLAN.md:38, 06-05-PLAN.md:39, 06-05-PLAN.md:71, 06-05-PLAN.md:72, 06-05-PLAN.md:94, 06-06-PLAN.md:8, 06-06-PLAN.md:9, 06-06-PLAN.md:10, 06-06-PLAN.md:11, 06-06-PLAN.md:13, 06-06-PLAN.md:14, 06-06-PLAN.md:34, 06-06-PLAN.md:37, 06-06-PLAN.md:38, 06-06-PLAN.md:40, 06-06-PLAN.md:41, 06-06-PLAN.md:73, 06-06-PLAN.md:74, 06-06-PLAN.md:98, 06-06-PLAN.md:99, 06-07-PLAN.md:9, 06-07-PLAN.md:12, 06-07-PLAN.md:13, 06-07-PLAN.md:34, 06-07-PLAN.md:70, 06-07-PLAN.md:71, 06-07-PLAN.md:92, 06-07-PLAN.md:93, 06-08-PLAN.md:21, 06-08-PLAN.md:111.
 Supplemental declaration candidate: `src/crud_views/checks.py:16` TAG = "crud_views"; `src/crud_views/checks.py:64` id="crud_views.E310",.
</details>

<details>
<summary><code>crud_views_workflow</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:12` — - src/crud_views_workflow/lib/forms.py

Citations: 06-04-PLAN.md:12, 06-04-PLAN.md:34, 06-04-PLAN.md:95, 06-04-PLAN.md:96.
 Supplemental declaration candidate: `src/crud_views_workflow/checks.py:6` TAG = "crud_views_workflow"; `src/crud_views_workflow/checks.py:28` id="crud_views_workflow.E001",.
</details>

<details>
<summary><code>css_class</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:117` — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Citations: 06-01-PLAN.md:117, 06-01-PLAN.md:126, 06-02-PLAN.md:79, 06-02-PLAN.md:99, 06-08-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1"; `src/crud_views/lib/crispy/table.py:9` css_class = "col-md-2".
</details>

<details>
<summary><code>css_id</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:125` — css_id wins over extra id,

Citations: 06-01-PLAN.md:125.

</details>

<details>
<summary><code>cv_button_class</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

Citations: 06-02-PLAN.md:99, 06-04-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108` def cv_button_class(location, slot, mode=None):; `src/crud_views/templatetags/crud_views.py:525` def cv_button_class(location, slot, mode=None):.
</details>

<details>
<summary><code>cv_button_data</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:36` — - &quot;D-13, D-14: A standalone package Submit renders a real button through cv_button_data(ctx, &#x27;form&#x27;), with label as the lazy form floor and finite kind semantics.&quot;

Citations: 06-02-PLAN.md:36, 06-02-PLAN.md:98, 06-06-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/view/button_data.py:52` def cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict:; `tests/test1/test_button_data.py:30` data = cv_button_data(base(), location).
</details>

<details>
<summary><code>cv_cancel_url</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:127` — once; data_cv_cancel_url/data-cv-cancel-url become one cancel-only URL; generated icon-mode title and tooltip

Citations: 06-01-PLAN.md:127, 06-02-PLAN.md:79.

</details>

<details>
<summary><code>cv_css_class</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:117` — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Citations: 06-01-PLAN.md:117, 06-02-PLAN.md:79, 06-02-PLAN.md:99, 06-08-PLAN.md:83.

</details>

<details>
<summary><code>cv_first_inline_keys</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:39` — via: cv_first_inline_keys selects one map

Citations: 06-03-PLAN.md:39, 06-03-PLAN.md:71, 06-03-PLAN.md:79.
 Supplemental declaration candidate: `src/crud_views/lib/view/base.py:263` def cv_first_inline_keys(cls, view_value, viewset_field: str):.
</details>

<details>
<summary><code>cv_flat_attrs</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:117` — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Citations: 06-01-PLAN.md:117, 06-02-PLAN.md:79, 06-08-PLAN.md:83, 06-08-PLAN.md:99.

</details>

<details>
<summary><code>cv_form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65, 06-06-PLAN.md:81, 06-06-PLAN.md:84, 06-06-PLAN.md:85.

</details>

<details>
<summary><code>cv_form_icon_mode_checks</code> — SKIPPED: declared phase output / execution summary</summary>

`06-06-PLAN.md:68` — NEW test file: tests/test1/test_form_button_checks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only coverage; no new generic diagnostic framework.

Citations: 06-06-PLAN.md:68.

</details>

<details>
<summary><code>cv_get_action_label_mode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65, 06-03-PLAN.md:71, 06-03-PLAN.md:79.
 Supplemental declaration candidate: `src/crud_views/lib/view/base.py:299` def cv_get_action_label_mode(; `src/crud_views/lib/view/base.py:647` mode = self.cv_get_action_label_mode(location, key, button, data.get("cv_context_label_mode")).
</details>

<details>
<summary><code>cv_get_form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65, 06-03-PLAN.md:79.

</details>

<details>
<summary><code>cv_icon_mode_checks</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:99` — &lt;read_first&gt;src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; 06-SPEC.md static-check reach&lt;/read_first&gt;

Citations: 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/view/buttons.py:387` def cv_icon_mode_checks(cls):.
</details>

<details>
<summary><code>cv_id</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:79` — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package.

Citations: 06-02-PLAN.md:79.

</details>

<details>
<summary><code>cv_key</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:98` — Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

Citations: 06-02-PLAN.md:98, 06-02-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views_workflow/lib/views.py:24` cv_key = "workflow"; `src/crud_views/lib/session.py:13` data: dict[str, Any] = Field(default_factory=default_dict)  # cv_key to Any.
</details>

<details>
<summary><code>cv_label_mode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

Citations: 06-02-PLAN.md:99, 06-06-PLAN.md:84.
 Supplemental declaration candidate: `src/crud_views/lib/view/button_data.py:85` label_mode = ctx.get("cv_label_mode"); `src/crud_views/lib/view/base.py:644` mode = data["cv_label_mode"].
</details>

<details>
<summary><code>cv_label_mode_checks</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:84` — Addresses H-DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish shape from individual modes so D-16&#x27;s E210 extension has a concrete scope without adding a scalar API: non-dict or non-string keys yield one E211 and stop entry traversal; a string-keyed dict yields one E210 per invalid mode value in insertion order; unknown form keys with valid modes yield W291 on the view&#x27;s own cv_form_actions_label_mode only, naming sorted FORM_KINDS. None and {} are valid. This documented form-specific diagnostic distinction does not alter FORM-11 whole-map resolution semantics. Do not blindly invoke the old helper unchanged or change its behavior for context/list.

Citations: 06-06-PLAN.md:84.
 Supplemental declaration candidate: `src/crud_views/lib/view/action_menu.py:46` def cv_label_mode_checks(cls, attribute: str, known_keys: Iterable[str] | None) -> Iterator[Check]:.
</details>

<details>
<summary><code>cv_name</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:79` — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package.

Citations: 06-02-PLAN.md:79, 06-02-PLAN.md:122.

</details>

<details>
<summary><code>cv_type</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:79` — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package.

Citations: 06-02-PLAN.md:79, 06-02-PLAN.md:98.

</details>

<details>
<summary><code>cv_value</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:79` — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package.

Citations: 06-02-PLAN.md:79, 06-08-PLAN.md:99.

</details>

<details>
<summary><code>cv_view</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:134` — argument&#x27;s cv_view first, never an outer context form; current helper view

Citations: 06-01-PLAN.md:134, 06-03-PLAN.md:94, 06-03-PLAN.md:99, 06-03-PLAN.md:102.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:37` def __init__(self, cv_view, *args, **kwargs):; `src/crud_views/lib/crispy/form.py:66` request = self.cv_view.request.
</details>

<details>
<summary><code>data_cv_cancel_url</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:127` — once; data_cv_cancel_url/data-cv-cancel-url become one cancel-only URL; generated icon-mode title and tooltip

Citations: 06-01-PLAN.md:127.

</details>

<details>
<summary><code>default_label_mode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:89` — contracts at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS /

Citations: 06-01-PLAN.md:89, 06-03-PLAN.md:79.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:56` label_mode = default_label_mode("card"); `src/crud_views/lib/view/button_data.py:87` label_mode = default_label_mode(location).
</details>

<details>
<summary><code>delete_icon</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:68` — EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

Citations: 06-04-PLAN.md:68, 06-04-PLAN.md:104, 06-06-PLAN.md:105, 06-06-PLAN.md:110.

</details>

<details>
<summary><code>dicts</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:133` — Define owner recovery from Django Context.dicts before flattening: the actual adapter render(form, context)

Citations: 06-01-PLAN.md:133, 06-02-PLAN.md:123, 06-03-PLAN.md:102.

</details>

<details>
<summary><code>docs/example</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:34` — - &quot;Documentation recipes render successfully and repeated docs/example checks do not modify generated sources or shared settings.&quot;

Citations: 06-08-PLAN.md:34, 06-09-PLAN.md:21, 06-09-PLAN.md:209.

</details>

<details>
<summary><code>docs/getting_started/tutorial-5-filters-permissions.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:95` — &lt;read_first&gt;docs/getting_started/tutorial-5-filters-permissions.md; tests/test1/test_filter.py; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-05-PLAN.md:95, 06-08-PLAN.md:15, 06-08-PLAN.md:96, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/migrating-1.0.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:18` — - docs/migrating-1.0.md

Citations: 06-08-PLAN.md:18, 06-08-PLAN.md:37, 06-08-PLAN.md:111, 06-08-PLAN.md:112, 06-09-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/action_menus.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:10` — - docs/reference/action_menus.md

Citations: 06-08-PLAN.md:10, 06-08-PLAN.md:44, 06-08-PLAN.md:80, 06-08-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/buttons.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:11` — - docs/reference/buttons.md

Citations: 06-02-PLAN.md:11, 06-02-PLAN.md:85, 06-08-PLAN.md:8, 06-08-PLAN.md:80, 06-08-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/icons.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:12` — - docs/reference/icons.md

Citations: 06-08-PLAN.md:12, 06-08-PLAN.md:96, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/javascript.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:20` — - docs/reference/javascript.md

Citations: 06-08-PLAN.md:20, 06-08-PLAN.md:111.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/list_view.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:72` — &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt;

Citations: 06-05-PLAN.md:72, 06-08-PLAN.md:14, 06-08-PLAN.md:96, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/settings.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:12` — - docs/reference/settings.md

Citations: 06-02-PLAN.md:12, 06-02-PLAN.md:85, 06-08-PLAN.md:9, 06-08-PLAN.md:45, 06-08-PLAN.md:80, 06-08-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>docs/reference/theme.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:13` — - docs/reference/theme.md

Citations: 06-08-PLAN.md:13, 06-08-PLAN.md:47, 06-08-PLAN.md:96, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>examples/bootstrap5</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:235` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt;

Citations: 06-09-PLAN.md:235, 06-09-PLAN.md:239.

</details>

<details>
<summary><code>examples/bootstrap5/project/settings.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:19` — - examples/bootstrap5/project/settings.py

Citations: 06-08-PLAN.md:19, 06-08-PLAN.md:41, 06-08-PLAN.md:111, 06-08-PLAN.md:112, 06-09-PLAN.md:81.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>examples/bootstrap5/test_docs_sync.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:112` — &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt;

Citations: 06-08-PLAN.md:112.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>field_classes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

Citations: 06-02-PLAN.md:99, 06-02-PLAN.md:123.

</details>

<details>
<summary><code>flat_attrs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:117` — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Citations: 06-01-PLAN.md:117, 06-02-PLAN.md:79, 06-02-PLAN.md:99, 06-08-PLAN.md:83, 06-08-PLAN.md:99.

</details>

<details>
<summary><code>form_actions_label_mode</code> — SKIPPED: declared phase output / execution summary</summary>

`06-03-PLAN.md:65` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Citations: 06-03-PLAN.md:65, 06-03-PLAN.md:79, 06-06-PLAN.md:81, 06-06-PLAN.md:84, 06-06-PLAN.md:85.

</details>

<details>
<summary><code>format_html</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:151` — Record accurate dependency findings: Django 6 removed zero-argument format_html calls, not the function;

Citations: 06-01-PLAN.md:151, 06-07-PLAN.md:115, 06-09-PLAN.md:161.

</details>

<details>
<summary><code>get_attributes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92, 06-05-PLAN.md:81.

</details>

<details>
<summary><code>get_filterset</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:72` — &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt;

Citations: 06-05-PLAN.md:72.
 Supplemental declaration candidate: `src/crud_views/lib/views/mixins.py:315` def get_filterset(self, filterset_class):.
</details>

<details>
<summary><code>get_form_actions</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:145` — Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained.

Citations: 06-01-PLAN.md:145, 06-03-PLAN.md:65, 06-03-PLAN.md:79, 06-05-PLAN.md:24, 06-05-PLAN.md:66, 06-05-PLAN.md:81, 06-05-PLAN.md:98, 06-06-PLAN.md:111, 06-08-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:53` def get_form_actions(self) -> FormActions:.
</details>

<details>
<summary><code>get_form_class</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:111` — For filter helpers inspect the configured helper class only when default get_form_actions is inherited. For a concrete dict-valued polymorphic_forms mapping inspect each distinct form class using the same provider rules, without selecting a request/model instance; identify form class and kind in warnings and deduplicate identical repeated class/kind entries locally per traversal (M-POLYMORPHIC). Missing/custom mapping providers skip static inference and get actual polymorphic create/update runtime tests. Never instantiate forms/helpers, call request-dependent get_form_class, or execute custom action hooks during checks.

Citations: 06-06-PLAN.md:111.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:152` form_class = self.get_form_class(); `src/crud_views_polymorphic/lib/utils.py:64` def get_form_class(self):.
</details>

<details>
<summary><code>get_render</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.

</details>

<details>
<summary><code>get_response_dict</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.

</details>

<details>
<summary><code>helper</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:134` — argument&#x27;s cv_view first, never an outer context form; current helper view

Citations: 06-01-PLAN.md:134, 06-01-PLAN.md:136, 06-01-PLAN.md:137, 06-01-PLAN.md:138, 06-01-PLAN.md:140, 06-01-PLAN.md:142, 06-01-PLAN.md:146, 06-02-PLAN.md:79, 06-02-PLAN.md:91, 06-02-PLAN.md:98, 06-02-PLAN.md:99, 06-02-PLAN.md:160, 06-03-PLAN.md:24, 06-03-PLAN.md:25, 06-03-PLAN.md:27, 06-03-PLAN.md:65, 06-03-PLAN.md:90, 06-03-PLAN.md:94, 06-03-PLAN.md:95, 06-03-PLAN.md:97, 06-03-PLAN.md:99, 06-03-PLAN.md:102, 06-03-PLAN.md:103, 06-03-PLAN.md:107, 06-03-PLAN.md:122, 06-04-PLAN.md:104, 06-05-PLAN.md:23, 06-05-PLAN.md:25, 06-05-PLAN.md:26, 06-05-PLAN.md:27, 06-05-PLAN.md:37, 06-05-PLAN.md:72, 06-05-PLAN.md:75, 06-05-PLAN.md:77, 06-05-PLAN.md:81, 06-05-PLAN.md:100, 06-05-PLAN.md:101, 06-05-PLAN.md:104, 06-05-PLAN.md:108, 06-05-PLAN.md:110, 06-05-PLAN.md:123, 06-05-PLAN.md:137, 06-05-PLAN.md:142, 06-05-PLAN.md:148, 06-06-PLAN.md:84, 06-06-PLAN.md:85, 06-06-PLAN.md:105, 06-06-PLAN.md:110, 06-06-PLAN.md:111, 06-06-PLAN.md:133, 06-07-PLAN.md:71, 06-08-PLAN.md:31, 06-08-PLAN.md:40, 06-08-PLAN.md:49, 06-08-PLAN.md:75, 06-08-PLAN.md:95, 06-08-PLAN.md:114, 06-08-PLAN.md:115, 06-08-PLAN.md:136, 06-08-PLAN.md:149, 06-08-PLAN.md:159, 06-09-PLAN.md:156, 06-09-PLAN.md:197.
 Supplemental declaration candidate: `src/crud_views/lib/crispy/form.py:42` def helper(self) -> FormHelper:; `src/crud_views/lib/crispy/form.py:43` helper = FormHelper().
</details>

<details>
<summary><code>home/alex/.codex/gsd-core/templates/summary.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:49` — @/home/alex/.codex/gsd-core/templates/summary.md

Citations: 06-01-PLAN.md:49, 06-02-PLAN.md:62, 06-03-PLAN.md:48, 06-04-PLAN.md:51, 06-05-PLAN.md:49, 06-06-PLAN.md:51, 06-07-PLAN.md:48, 06-08-PLAN.md:58, 06-09-PLAN.md:43.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>home/alex/.codex/gsd-core/workflows/execute-plan.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:48` — @/home/alex/.codex/gsd-core/workflows/execute-plan.md

Citations: 06-01-PLAN.md:48, 06-02-PLAN.md:61, 06-03-PLAN.md:47, 06-04-PLAN.md:50, 06-05-PLAN.md:48, 06-06-PLAN.md:50, 06-07-PLAN.md:47, 06-08-PLAN.md:57, 06-09-PLAN.md:42.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>label_mode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Citations: 06-01-PLAN.md:83, 06-01-PLAN.md:89, 06-01-PLAN.md:90, 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:9, 06-02-PLAN.md:14, 06-02-PLAN.md:15, 06-02-PLAN.md:20, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:95, 06-02-PLAN.md:96, 06-02-PLAN.md:99, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-03-PLAN.md:12, 06-03-PLAN.md:65, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-03-PLAN.md:79, 06-03-PLAN.md:82, 06-03-PLAN.md:106, 06-06-PLAN.md:74, 06-06-PLAN.md:81, 06-06-PLAN.md:84, 06-06-PLAN.md:85, 06-06-PLAN.md:89, 06-08-PLAN.md:11, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:50` label_mode = action.label_mode; `src/crud_views/lib/views/card.py:52` label_mode = "icon".
</details>

<details>
<summary><code>list_view</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-05-PLAN.md:72` — &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt;

Citations: 06-05-PLAN.md:72, 06-08-PLAN.md:14, 06-08-PLAN.md:96, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `tests/test1/test_manage.py:97` list_view = views["list"]; `tests/test1/test_action_menus_groups.py:30` def list_view(client_user_author_view, author_douglas_adams):.
</details>

<details>
<summary><code>m.group</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160.
 Supplemental declaration candidate: `src/crud_views/checks.py:141` def _non_nullable_clears(model, group):; `src/crud_views/checks.py:155` tname = group.toggle.field_name().
</details>

<details>
<summary><code>modal.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:9` — - src/crud_views/static/crud_views/js/modal.js

Citations: 06-07-PLAN.md:9, 06-07-PLAN.md:34, 06-07-PLAN.md:70, 06-07-PLAN.md:71, 06-07-PLAN.md:80.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>noxfile.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Citations: 06-01-PLAN.md:84, 06-07-PLAN.md:14, 06-07-PLAN.md:31, 06-07-PLAN.md:37, 06-07-PLAN.md:112, 06-07-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>override_settings</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:121` — Retain the location/default assertions updated in task 1 and expand lazy override_settings coverage in test_label_mode.py and test_button_data.py. Existing action contracts and location-independent finite class grammar remain unchanged.

Citations: 06-02-PLAN.md:121, 06-06-PLAN.md:86, 06-09-PLAN.md:68.
 Supplemental declaration candidate: `tests/test1/test_label_mode.py:150` strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True); `tests/test1/test_label_mode.py:219` strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": value}, CRUD_VIEWS_STRICT=True).
</details>

<details>
<summary><code>p.read_text</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160.
 Supplemental declaration candidate: `src/crud_views/lib/vendor.py:59` data = json.loads(stamp.read_text()); `tests/test1/test_vendor.py:32` stamp = json.loads((spec.target / STAMP_NAME).read_text()).
</details>

<details>
<summary><code>package-lock.json</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Citations: 06-01-PLAN.md:84, 06-07-PLAN.md:71.
 Supplemental declaration candidate: `src/crud_views/lib/vendor.py:59` data = json.loads(stamp.read_text()); `src/crud_views/lib/views/mixins.py:345` data = json.loads(request.body.decode("utf-8")).
</details>

<details>
<summary><code>package.json</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Citations: 06-01-PLAN.md:84, 06-07-PLAN.md:71.
 Supplemental declaration candidate: `src/crud_views/lib/vendor.py:59` data = json.loads(stamp.read_text()); `src/crud_views/lib/views/mixins.py:345` data = json.loads(request.body.decode("utf-8")).
</details>

<details>
<summary><code>push</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:137` — helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push

Citations: 06-01-PLAN.md:137, 06-03-PLAN.md:95, 06-03-PLAN.md:102, 06-05-PLAN.md:81, 06-09-PLAN.md:117.

</details>

<details>
<summary><code>pyproject.toml</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Citations: 06-01-PLAN.md:84, 06-07-PLAN.md:113.

</details>

<details>
<summary><code>re.escape</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160.
 Supplemental declaration candidate: `tests/test1/test_label_mode_docs.py:76` found = re.findall(rf"^{re.escape(heading)}\n(.*?)(?=^### |\Z)", release, re.MULTILINE | re.DOTALL).
</details>

<details>
<summary><code>re.search</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160.
 Supplemental declaration candidate: `tests/test1/test_form_enctype.py:27` outer_form_tag = re.search(r"<form\b[^>]*>", html).group(0); `tests/test1/test_assets.py:350` match = re.search(r'nonce="([^"]+)"', rendered["html"]).
</details>

<details>
<summary><code>read_bytes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:176` — tests compare render bytes to read_bytes with no update-on-test behavior. Pin default text, name, value,

Citations: 06-01-PLAN.md:176.

</details>

<details>
<summary><code>render</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:38` — via: Raw rendered control bytes captured before production changes

Citations: 06-01-PLAN.md:38, 06-01-PLAN.md:71, 06-01-PLAN.md:75, 06-01-PLAN.md:119, 06-01-PLAN.md:122, 06-01-PLAN.md:133, 06-01-PLAN.md:137, 06-01-PLAN.md:141, 06-01-PLAN.md:147, 06-01-PLAN.md:161, 06-01-PLAN.md:164, 06-01-PLAN.md:176, 06-01-PLAN.md:179, 06-01-PLAN.md:238, 06-01-PLAN.md:239, 06-01-PLAN.md:240, 06-01-PLAN.md:253, 06-02-PLAN.md:36, 06-02-PLAN.md:39, 06-02-PLAN.md:41, 06-02-PLAN.md:50, 06-02-PLAN.md:91, 06-02-PLAN.md:96, 06-02-PLAN.md:97, 06-02-PLAN.md:98, 06-02-PLAN.md:99, 06-02-PLAN.md:106, 06-02-PLAN.md:110, 06-02-PLAN.md:117, 06-02-PLAN.md:122, 06-02-PLAN.md:127, 06-02-PLAN.md:160, 06-02-PLAN.md:178, 06-02-PLAN.md:183, 06-02-PLAN.md:184, 06-03-PLAN.md:25, 06-03-PLAN.md:26, 06-03-PLAN.md:27, 06-03-PLAN.md:79, 06-03-PLAN.md:92, 06-03-PLAN.md:97, 06-03-PLAN.md:99, 06-03-PLAN.md:102, 06-03-PLAN.md:103, 06-03-PLAN.md:122, 06-03-PLAN.md:140, 06-04-PLAN.md:25, 06-04-PLAN.md:28, 06-04-PLAN.md:68, 06-04-PLAN.md:77, 06-04-PLAN.md:82, 06-04-PLAN.md:83, 06-04-PLAN.md:87, 06-04-PLAN.md:89, 06-04-PLAN.md:98, 06-04-PLAN.md:110, 06-04-PLAN.md:135, 06-04-PLAN.md:144, 06-04-PLAN.md:145, 06-05-PLAN.md:23, 06-05-PLAN.md:26, 06-05-PLAN.md:27, 06-05-PLAN.md:33, 06-05-PLAN.md:66, 06-05-PLAN.md:75, 06-05-PLAN.md:81, 06-05-PLAN.md:97, 06-05-PLAN.md:100, 06-05-PLAN.md:104, 06-05-PLAN.md:108, 06-05-PLAN.md:123, 06-05-PLAN.md:143, 06-06-PLAN.md:26, 06-06-PLAN.md:33, 06-06-PLAN.md:103, 06-06-PLAN.md:107, 06-06-PLAN.md:110, 06-06-PLAN.md:112, 06-06-PLAN.md:113, 06-06-PLAN.md:134, 06-06-PLAN.md:147, 06-06-PLAN.md:157, 06-06-PLAN.md:158, 06-07-PLAN.md:100, 06-08-PLAN.md:34, 06-08-PLAN.md:75, 06-08-PLAN.md:83, 06-08-PLAN.md:84, 06-08-PLAN.md:88, 06-08-PLAN.md:95, 06-08-PLAN.md:99, 06-08-PLAN.md:114, 06-09-PLAN.md:20, 06-09-PLAN.md:68, 06-09-PLAN.md:75, 06-09-PLAN.md:101, 06-09-PLAN.md:102, 06-09-PLAN.md:109, 06-09-PLAN.md:163, 06-09-PLAN.md:187, 06-09-PLAN.md:196, 06-09-PLAN.md:198, 06-09-PLAN.md:202, 06-09-PLAN.md:203, 06-09-PLAN.md:217, 06-09-PLAN.md:252.
 Supplemental declaration candidate: `src/crud_views/templatetags/crud_views.py:333` def render(self, context):; `src/crud_views/lib/view/base.py:109` cv_header_template: str | None = None  # template snippet to render header label.
</details>

<details>
<summary><code>render_layout</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:137` — helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push

Citations: 06-01-PLAN.md:137, 06-01-PLAN.md:147, 06-05-PLAN.md:66, 06-05-PLAN.md:81.

</details>

<details>
<summary><code>sections.values</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160.
 Supplemental declaration candidate: `src/crud_views/checks.py:41` viewsets = list(_REGISTRY.values()); `src/crud_views/checks.py:188` viewsets = list(_REGISTRY.values()).
</details>

<details>
<summary><code>settings.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:12` — - docs/reference/settings.md

Citations: 06-02-PLAN.md:12, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-08-PLAN.md:9, 06-08-PLAN.md:45, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>slot</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:41` — - &quot;D-17: Multi-word submitted names retain crispy wordcount/slugify semantics; strict finite slot rejection applies only to the new layout render path.&quot;

Citations: 06-02-PLAN.md:41, 06-02-PLAN.md:97, 06-02-PLAN.md:98, 06-02-PLAN.md:99, 06-02-PLAN.md:160, 06-04-PLAN.md:101, 06-04-PLAN.md:104, 06-04-PLAN.md:140, 06-08-PLAN.md:35, 06-08-PLAN.md:114, 06-08-PLAN.md:136, 06-09-PLAN.md:160.
 Supplemental declaration candidate: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108` def cv_button_class(location, slot, mode=None):; `src/crud_views/lib/button_classes.py:138` def get_button_class(location: str, slot: str, mode: str | None = None) -> str:.
</details>

<details>
<summary><code>src/crud_views/lib/button_classes.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:10` — - src/crud_views/lib/button_classes.py

Citations: 06-02-PLAN.md:10, 06-02-PLAN.md:85, 06-04-PLAN.md:32, 06-04-PLAN.md:41, 06-04-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/crispy/buttons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:81` — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

Citations: 06-01-PLAN.md:81, 06-02-PLAN.md:17, 06-02-PLAN.md:48, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:111, 06-03-PLAN.md:11, 06-03-PLAN.md:31, 06-03-PLAN.md:34, 06-03-PLAN.md:70, 06-03-PLAN.md:91, 06-04-PLAN.md:13, 06-04-PLAN.md:38, 06-04-PLAN.md:95, 06-05-PLAN.md:39.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/crispy/form.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:81` — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

Citations: 06-01-PLAN.md:81, 06-04-PLAN.md:11, 06-04-PLAN.md:37, 06-04-PLAN.md:95, 06-04-PLAN.md:96, 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/icons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:8` — - src/crud_views/lib/icons.py

Citations: 06-04-PLAN.md:8, 06-04-PLAN.md:30, 06-04-PLAN.md:73, 06-04-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/settings.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:8` — - src/crud_views/lib/settings.py

Citations: 06-03-PLAN.md:8, 06-03-PLAN.md:38, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-06-PLAN.md:8, 06-06-PLAN.md:73, 06-06-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/view/action_menu.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:11` — - src/crud_views/lib/view/action_menu.py

Citations: 06-06-PLAN.md:11, 06-06-PLAN.md:38, 06-06-PLAN.md:73, 06-06-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/view/base.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:10` — - src/crud_views/lib/view/base.py

Citations: 06-03-PLAN.md:10, 06-03-PLAN.md:29, 06-03-PLAN.md:35, 06-03-PLAN.md:37, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-06-PLAN.md:10, 06-06-PLAN.md:37, 06-06-PLAN.md:73, 06-06-PLAN.md:74, 06-06-PLAN.md:98.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/view/button_data.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Citations: 06-01-PLAN.md:83, 06-02-PLAN.md:8, 06-02-PLAN.md:45, 06-02-PLAN.md:49, 06-02-PLAN.md:51, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:111, 06-06-PLAN.md:14, 06-06-PLAN.md:41, 06-06-PLAN.md:98, 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/view/buttons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:13` — - src/crud_views/lib/view/buttons.py

Citations: 06-06-PLAN.md:13, 06-06-PLAN.md:34, 06-06-PLAN.md:40, 06-06-PLAN.md:98, 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/view/label_mode.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Citations: 06-01-PLAN.md:83, 06-02-PLAN.md:9, 06-02-PLAN.md:85, 06-02-PLAN.md:86.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/views/list.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:82` — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

Citations: 06-01-PLAN.md:82, 06-05-PLAN.md:8, 06-05-PLAN.md:30, 06-05-PLAN.md:36, 06-05-PLAN.md:38, 06-05-PLAN.md:71, 06-05-PLAN.md:72, 06-05-PLAN.md:94, 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/views/mixins.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:82` — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

Citations: 06-01-PLAN.md:82, 06-05-PLAN.md:35, 06-05-PLAN.md:72.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/lib/viewset/__init__.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:9` — - src/crud_views/lib/viewset/__init__.py

Citations: 06-03-PLAN.md:9, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-06-PLAN.md:9, 06-06-PLAN.md:73, 06-06-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/list.filter.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:13` — - src/crud_views/static/crud_views/js/list.filter.js

Citations: 06-07-PLAN.md:13, 06-07-PLAN.md:92, 06-07-PLAN.md:93.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/modal.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:9` — - src/crud_views/static/crud_views/js/modal.js

Citations: 06-07-PLAN.md:9, 06-07-PLAN.md:34, 06-07-PLAN.md:70, 06-07-PLAN.md:71.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/tooltip.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:21` — - src/crud_views/static/crud_views/js/tooltip.js

Citations: 06-08-PLAN.md:21, 06-08-PLAN.md:111.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/viewset.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:12` — - src/crud_views/static/crud_views/js/viewset.js

Citations: 06-07-PLAN.md:12, 06-07-PLAN.md:92, 06-07-PLAN.md:93.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>src/crud_views/templates/crud_views/formsets/formset.html</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-03-PLAN.md:92` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Citations: 06-03-PLAN.md:92.
 Supplemental declaration candidate: `src/crud_views_object_detail/lib/mixins.py:19` template_name = "crud_views/view_detail.html"; `src/crud_views_object_detail/lib/mixins.py:20` cv_content_template = "crud_views_object_detail/view_detail.content.html".
</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/action.html</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:86, 06-04-PLAN.md:74.
 Supplemental declaration candidate: `src/crud_views_object_detail/lib/mixins.py:19` template_name = "crud_views/view_detail.html"; `src/crud_views_object_detail/lib/mixins.py:20` cv_content_template = "crud_views_object_detail/view_detail.content.html".
</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/form.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-02-PLAN.md:18` — - src/crud_views/templates/crud_views/tags/button/form.html

Citations: 06-02-PLAN.md:18, 06-02-PLAN.md:43, 06-02-PLAN.md:52, 06-02-PLAN.md:79, 06-02-PLAN.md:85, 06-04-PLAN.md:9, 06-04-PLAN.md:40, 06-04-PLAN.md:73.

</details>

<details>
<summary><code>src/crud_views_workflow/lib/forms.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:12` — - src/crud_views_workflow/lib/forms.py

Citations: 06-04-PLAN.md:12, 06-04-PLAN.md:34, 06-04-PLAN.md:95, 06-04-PLAN.md:96.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>submit_icon</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:28` — - &quot;Repeated renders with different icon settings, forms and languages do not mutate shared class/icon defaults or retain another form&#x27;s submit_icon.&quot;

Citations: 06-04-PLAN.md:28, 06-04-PLAN.md:68, 06-04-PLAN.md:99, 06-04-PLAN.md:104, 06-06-PLAN.md:105, 06-06-PLAN.md:110, 06-06-PLAN.md:133, 06-09-PLAN.md:199.

</details>

<details>
<summary><code>superpowers/plans/2026-10-24-concept-review-followups.md</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:80` — superpowers/plans/2026-10-24-concept-review-followups.md (source Phase 2);

Citations: 06-01-PLAN.md:80.
 Supplemental declaration candidate: `src/crud_views/lib/views/card.py:31` cv_card_container_class: str = "col-md-6"; `src/crud_views/lib/crispy/table.py:5` css_class = "col-md-1".
</details>

<details>
<summary><code>template</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:27` — - &quot;D-05, D-06, D-07, D-08: The spec fixes template precedence, pack substitution and the cv_* context before implementation.&quot;

Citations: 06-01-PLAN.md:27, 06-01-PLAN.md:49, 06-01-PLAN.md:119, 06-01-PLAN.md:124, 06-02-PLAN.md:16, 06-02-PLAN.md:18, 06-02-PLAN.md:37, 06-02-PLAN.md:38, 06-02-PLAN.md:43, 06-02-PLAN.md:52, 06-02-PLAN.md:57, 06-02-PLAN.md:62, 06-02-PLAN.md:79, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:89, 06-02-PLAN.md:90, 06-02-PLAN.md:91, 06-02-PLAN.md:96, 06-02-PLAN.md:99, 06-02-PLAN.md:102, 06-02-PLAN.md:110, 06-02-PLAN.md:114, 06-02-PLAN.md:118, 06-02-PLAN.md:123, 06-02-PLAN.md:129, 06-02-PLAN.md:172, 06-02-PLAN.md:173, 06-02-PLAN.md:184, 06-03-PLAN.md:48, 06-03-PLAN.md:92, 06-03-PLAN.md:103, 06-03-PLAN.md:109, 06-04-PLAN.md:9, 06-04-PLAN.md:40, 06-04-PLAN.md:51, 06-04-PLAN.md:73, 06-04-PLAN.md:74, 06-05-PLAN.md:49, 06-05-PLAN.md:104, 06-05-PLAN.md:125, 06-06-PLAN.md:51, 06-07-PLAN.md:48, 06-08-PLAN.md:31, 06-08-PLAN.md:40, 06-08-PLAN.md:49, 06-08-PLAN.md:58, 06-08-PLAN.md:75, 06-08-PLAN.md:95, 06-08-PLAN.md:99, 06-08-PLAN.md:103, 06-08-PLAN.md:114, 06-08-PLAN.md:149, 06-08-PLAN.md:153, 06-08-PLAN.md:159, 06-09-PLAN.md:21, 06-09-PLAN.md:43, 06-09-PLAN.md:83, 06-09-PLAN.md:122, 06-09-PLAN.md:216.
 Supplemental declaration candidate: `src/crud_views_object_detail/lib/resolvers.py:51` template: str | None = None; `src/crud_views_object_detail/lib/resolvers.py:200` template=config.template,.
</details>

<details>
<summary><code>test_action_label_mode_config</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:14, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:102, 06-03-PLAN.md:12, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-03-PLAN.md:82, 06-03-PLAN.md:106, 06-06-PLAN.md:74, 06-06-PLAN.md:89.

</details>

<details>
<summary><code>test_action_label_mode_config.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:14, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:102, 06-03-PLAN.md:12, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-03-PLAN.md:82, 06-03-PLAN.md:106, 06-06-PLAN.md:74, 06-06-PLAN.md:89.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_button_classes</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:13, 06-02-PLAN.md:16, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:97, 06-02-PLAN.md:102, 06-04-PLAN.md:86, 06-08-PLAN.md:87.

</details>

<details>
<summary><code>test_button_classes.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:13, 06-02-PLAN.md:85, 06-02-PLAN.md:97, 06-02-PLAN.md:102, 06-04-PLAN.md:86, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_button_classes_templates.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:16` — - tests/test1/test_button_classes_templates.py

Citations: 06-02-PLAN.md:16, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:102.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_button_data</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-02-PLAN.md:21, 06-02-PLAN.md:85, 06-02-PLAN.md:95, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:68, 06-06-PLAN.md:116.

</details>

<details>
<summary><code>test_button_data.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-02-PLAN.md:21, 06-02-PLAN.md:85, 06-02-PLAN.md:95, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:68, 06-06-PLAN.md:116.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_button_leaves</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:86, 06-02-PLAN.md:112.

</details>

<details>
<summary><code>test_button_leaves.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:86, 06-02-PLAN.md:112.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_cancel_origin</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:136` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.

</details>

<details>
<summary><code>test_cancel_origin.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:136` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_crispy_buttons</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-02-PLAN.md:19, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:126, 06-03-PLAN.md:13, 06-03-PLAN.md:82, 06-03-PLAN.md:91, 06-03-PLAN.md:92, 06-03-PLAN.md:106, 06-04-PLAN.md:14, 06-04-PLAN.md:95, 06-04-PLAN.md:96, 06-04-PLAN.md:107, 06-05-PLAN.md:10, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:38, 06-07-PLAN.md:113.

</details>

<details>
<summary><code>test_crispy_buttons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-02-PLAN.md:19, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:126, 06-03-PLAN.md:13, 06-03-PLAN.md:82, 06-03-PLAN.md:91, 06-03-PLAN.md:92, 06-03-PLAN.md:106, 06-04-PLAN.md:14, 06-04-PLAN.md:95, 06-04-PLAN.md:96, 06-04-PLAN.md:107, 06-05-PLAN.md:10, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:38, 06-07-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_crud</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-01-PLAN.md:177, 06-01-PLAN.md:187, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.

</details>

<details>
<summary><code>test_crud.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-01-PLAN.md:177, 06-01-PLAN.md:187, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_docs_sync</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:112` — &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt;

Citations: 06-08-PLAN.md:112, 06-09-PLAN.md:239.

</details>

<details>
<summary><code>test_docs_sync.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:112` — &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt;

Citations: 06-08-PLAN.md:112, 06-09-PLAN.md:239.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_filter</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-05-PLAN.md:9, 06-05-PLAN.md:32, 06-05-PLAN.md:71, 06-05-PLAN.md:72, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:113.

</details>

<details>
<summary><code>test_filter.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-05-PLAN.md:9, 06-05-PLAN.md:32, 06-05-PLAN.md:71, 06-05-PLAN.md:72, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_form_button_baselines</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:67` — tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

Citations: 06-01-PLAN.md:67.

</details>

<details>
<summary><code>test_form_button_checks</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:12` — - tests/test1/test_form_button_checks.py

Citations: 06-06-PLAN.md:12, 06-06-PLAN.md:32, 06-06-PLAN.md:68, 06-06-PLAN.md:73, 06-06-PLAN.md:89, 06-06-PLAN.md:98, 06-06-PLAN.md:116, 06-07-PLAN.md:113, 06-09-PLAN.md:33.

</details>

<details>
<summary><code>test_form_button_checks.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-06-PLAN.md:12` — - tests/test1/test_form_button_checks.py

Citations: 06-06-PLAN.md:12, 06-06-PLAN.md:32, 06-06-PLAN.md:68, 06-06-PLAN.md:73, 06-06-PLAN.md:89, 06-06-PLAN.md:98, 06-06-PLAN.md:116, 06-07-PLAN.md:113, 06-09-PLAN.md:33.

</details>

<details>
<summary><code>test_form_button_docs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-08-PLAN.md:16` — - tests/test1/test_form_button_docs.py

Citations: 06-08-PLAN.md:16, 06-08-PLAN.md:39, 06-08-PLAN.md:48, 06-08-PLAN.md:75, 06-08-PLAN.md:96, 06-08-PLAN.md:102.

</details>

<details>
<summary><code>test_form_button_docs.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-08-PLAN.md:16` — - tests/test1/test_form_button_docs.py

Citations: 06-08-PLAN.md:16, 06-08-PLAN.md:39, 06-08-PLAN.md:48, 06-08-PLAN.md:75, 06-08-PLAN.md:96, 06-08-PLAN.md:102.

</details>

<details>
<summary><code>test_form_buttons_golden</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:11` — - tests/test1/test_form_buttons_golden.py

Citations: 06-01-PLAN.md:11, 06-01-PLAN.md:33, 06-01-PLAN.md:36, 06-01-PLAN.md:66, 06-01-PLAN.md:169, 06-01-PLAN.md:187, 06-01-PLAN.md:196, 06-01-PLAN.md:208, 06-02-PLAN.md:22, 06-02-PLAN.md:135, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-05-PLAN.md:11, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-09-PLAN.md:30.

</details>

<details>
<summary><code>test_form_buttons_golden.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:11` — - tests/test1/test_form_buttons_golden.py

Citations: 06-01-PLAN.md:11, 06-01-PLAN.md:33, 06-01-PLAN.md:36, 06-01-PLAN.md:66, 06-01-PLAN.md:169, 06-01-PLAN.md:187, 06-01-PLAN.md:196, 06-01-PLAN.md:208, 06-02-PLAN.md:22, 06-02-PLAN.md:135, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-05-PLAN.md:11, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-09-PLAN.md:30.

</details>

<details>
<summary><code>test_icon_host_leaves</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:10` — - tests/test1/test_icon_host_leaves.py

Citations: 06-04-PLAN.md:10, 06-04-PLAN.md:73, 06-04-PLAN.md:74, 06-04-PLAN.md:86.

</details>

<details>
<summary><code>test_icon_host_leaves.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:10` — - tests/test1/test_icon_host_leaves.py

Citations: 06-04-PLAN.md:10, 06-04-PLAN.md:73, 06-04-PLAN.md:74, 06-04-PLAN.md:86.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_icons_registry</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:74` — &lt;read_first&gt;src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html&lt;/read_first&gt;

Citations: 06-04-PLAN.md:74, 06-04-PLAN.md:86, 06-04-PLAN.md:107.
 Supplemental declaration candidate: `tests/test1/test_icons_registry.py:96` CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "tests.test1.test_icons_registry.xy_renderer"}}; `tests/test1/test_icons_registry.py:140` CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "tests.test1.test_icons_registry.xy_renderer"}}.
</details>

<details>
<summary><code>test_icons_registry.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:74` — &lt;read_first&gt;src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html&lt;/read_first&gt;

Citations: 06-04-PLAN.md:74, 06-04-PLAN.md:86, 06-04-PLAN.md:107.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_label_mode</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Citations: 06-01-PLAN.md:90, 06-01-PLAN.md:160, 06-02-PLAN.md:15, 06-02-PLAN.md:20, 06-02-PLAN.md:85, 06-02-PLAN.md:95, 06-02-PLAN.md:96, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:89, 06-08-PLAN.md:11, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:87.

</details>

<details>
<summary><code>test_label_mode.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Citations: 06-01-PLAN.md:90, 06-01-PLAN.md:160, 06-02-PLAN.md:20, 06-02-PLAN.md:85, 06-02-PLAN.md:95, 06-02-PLAN.md:111, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-06-PLAN.md:89.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_label_mode_docs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:15` — - tests/test1/test_label_mode_docs.py

Citations: 06-02-PLAN.md:15, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:102, 06-08-PLAN.md:11, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:87.

</details>

<details>
<summary><code>test_label_mode_docs.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:15` — - tests/test1/test_label_mode_docs.py

Citations: 06-02-PLAN.md:15, 06-02-PLAN.md:85, 06-02-PLAN.md:96, 06-02-PLAN.md:102, 06-08-PLAN.md:11, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_no_check_errors_with_every_viewset_registered</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-09-PLAN.md:235` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt;

Citations: 06-09-PLAN.md:235.

</details>

<details>
<summary><code>test_pagination_docs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-08-PLAN.md:97.

</details>

<details>
<summary><code>test_pagination_docs.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>test_workflow</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-04-PLAN.md:96, 06-04-PLAN.md:107.

</details>

<details>
<summary><code>test_workflow.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-04-PLAN.md:96, 06-04-PLAN.md:107.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/docs</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:123` — | H-KEYSET / H-EARLY-UTILITIES | HIGH | Utility defaults and exhaustive tests/docs move together to 06-02 task 1; this plan consumes them and expands real icon/host coverage without a second key addition. |

Citations: 06-04-PLAN.md:123, 06-06-PLAN.md:132.

</details>

<details>
<summary><code>tests/js/helpers/setup.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:71` — &lt;read_first&gt;package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt;

Citations: 06-07-PLAN.md:71.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>tests/js/list.filter.test.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:11` — - tests/js/list.filter.test.js

Citations: 06-07-PLAN.md:11, 06-07-PLAN.md:92, 06-07-PLAN.md:93, 06-07-PLAN.md:103.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>tests/js/modal.test.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:8` — - tests/js/modal.test.js

Citations: 06-07-PLAN.md:8, 06-07-PLAN.md:29, 06-07-PLAN.md:35, 06-07-PLAN.md:70, 06-07-PLAN.md:71, 06-07-PLAN.md:83.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>tests/js/viewset.test.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:10` — - tests/js/viewset.test.js

Citations: 06-07-PLAN.md:10, 06-07-PLAN.md:92, 06-07-PLAN.md:93, 06-07-PLAN.md:103.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>

<details>
<summary><code>tests/test1/app/views.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/conftest.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/golden/form_buttons/*.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:67` — tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

Citations: 06-01-PLAN.md:67.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/create.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:12` — - tests/test1/golden/form_buttons/create.html

Citations: 06-01-PLAN.md:12, 06-01-PLAN.md:37, 06-01-PLAN.md:169, 06-02-PLAN.md:23, 06-02-PLAN.md:135.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/delete.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:14` — - tests/test1/golden/form_buttons/delete.html

Citations: 06-01-PLAN.md:14, 06-01-PLAN.md:169, 06-02-PLAN.md:25, 06-02-PLAN.md:135.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/filter.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:16` — - tests/test1/golden/form_buttons/filter.html

Citations: 06-01-PLAN.md:16, 06-01-PLAN.md:196, 06-05-PLAN.md:12, 06-05-PLAN.md:71.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/update.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:13` — - tests/test1/golden/form_buttons/update.html

Citations: 06-01-PLAN.md:13, 06-01-PLAN.md:169, 06-02-PLAN.md:24, 06-02-PLAN.md:135.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/workflow.html</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:15` — - tests/test1/golden/form_buttons/workflow.html

Citations: 06-01-PLAN.md:15, 06-01-PLAN.md:196, 06-02-PLAN.md:26, 06-02-PLAN.md:135.

</details>

<details>
<summary><code>tests/test1/test_action_label_mode_config.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:14, 06-02-PLAN.md:85, 06-02-PLAN.md:102, 06-03-PLAN.md:12, 06-03-PLAN.md:70, 06-03-PLAN.md:71, 06-03-PLAN.md:82, 06-03-PLAN.md:106, 06-06-PLAN.md:74, 06-06-PLAN.md:89.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_button_classes.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Citations: 06-01-PLAN.md:91, 06-01-PLAN.md:160, 06-02-PLAN.md:13, 06-02-PLAN.md:85, 06-02-PLAN.md:102, 06-04-PLAN.md:86, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_button_classes_templates.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:16` — - tests/test1/test_button_classes_templates.py

Citations: 06-02-PLAN.md:16, 06-02-PLAN.md:85, 06-02-PLAN.md:102.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_button_data.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-02-PLAN.md:21, 06-02-PLAN.md:85, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:126, 06-06-PLAN.md:116.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_button_leaves.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:86, 06-02-PLAN.md:112.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_cancel_origin.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:136` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt;

Citations: 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_crispy_buttons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:160` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Citations: 06-01-PLAN.md:160, 06-01-PLAN.md:170, 06-02-PLAN.md:19, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:102, 06-02-PLAN.md:111, 06-02-PLAN.md:126, 06-03-PLAN.md:13, 06-03-PLAN.md:82, 06-03-PLAN.md:91, 06-03-PLAN.md:92, 06-03-PLAN.md:106, 06-04-PLAN.md:14, 06-04-PLAN.md:95, 06-04-PLAN.md:96, 06-04-PLAN.md:107, 06-05-PLAN.md:10, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:38, 06-07-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_crud.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-01-PLAN.md:177, 06-01-PLAN.md:187, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-09-PLAN.md:66.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_filter.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-05-PLAN.md:9, 06-05-PLAN.md:32, 06-05-PLAN.md:71, 06-05-PLAN.md:72, 06-05-PLAN.md:85, 06-05-PLAN.md:94, 06-05-PLAN.md:95, 06-05-PLAN.md:107, 06-07-PLAN.md:113.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_form_button_checks.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-06-PLAN.md:12` — - tests/test1/test_form_button_checks.py

Citations: 06-06-PLAN.md:12, 06-06-PLAN.md:32, 06-06-PLAN.md:68, 06-06-PLAN.md:73, 06-06-PLAN.md:89, 06-06-PLAN.md:98, 06-06-PLAN.md:116, 06-07-PLAN.md:113, 06-09-PLAN.md:33.

</details>

<details>
<summary><code>tests/test1/test_form_button_docs.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-08-PLAN.md:16` — - tests/test1/test_form_button_docs.py

Citations: 06-08-PLAN.md:16, 06-08-PLAN.md:39, 06-08-PLAN.md:48, 06-08-PLAN.md:75, 06-08-PLAN.md:96, 06-08-PLAN.md:102.

</details>

<details>
<summary><code>tests/test1/test_form_buttons_golden.py</code> — SKIPPED: declared phase output / execution summary</summary>

`06-01-PLAN.md:11` — - tests/test1/test_form_buttons_golden.py

Citations: 06-01-PLAN.md:11, 06-01-PLAN.md:33, 06-01-PLAN.md:36, 06-01-PLAN.md:66, 06-01-PLAN.md:169, 06-01-PLAN.md:187, 06-01-PLAN.md:196, 06-01-PLAN.md:208, 06-02-PLAN.md:22, 06-02-PLAN.md:135, 06-02-PLAN.md:136, 06-02-PLAN.md:141, 06-05-PLAN.md:11, 06-05-PLAN.md:71, 06-05-PLAN.md:85, 06-09-PLAN.md:30.

</details>

<details>
<summary><code>tests/test1/test_icon_host_leaves.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:10` — - tests/test1/test_icon_host_leaves.py

Citations: 06-04-PLAN.md:10, 06-04-PLAN.md:73, 06-04-PLAN.md:74, 06-04-PLAN.md:86.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_icons_registry.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-04-PLAN.md:74` — &lt;read_first&gt;src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html&lt;/read_first&gt;

Citations: 06-04-PLAN.md:74, 06-04-PLAN.md:86, 06-04-PLAN.md:107.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_label_mode.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Citations: 06-01-PLAN.md:90, 06-01-PLAN.md:160, 06-02-PLAN.md:20, 06-02-PLAN.md:85, 06-02-PLAN.md:111, 06-02-PLAN.md:126, 06-06-PLAN.md:89.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_label_mode_docs.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-02-PLAN.md:15` — - tests/test1/test_label_mode_docs.py

Citations: 06-02-PLAN.md:15, 06-02-PLAN.md:85, 06-02-PLAN.md:102, 06-08-PLAN.md:11, 06-08-PLAN.md:80, 06-08-PLAN.md:81, 06-08-PLAN.md:87.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_pagination_docs.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:170` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:170, 06-08-PLAN.md:97.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>tests/test1/test_workflow.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-01-PLAN.md:197` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Citations: 06-01-PLAN.md:197, 06-01-PLAN.md:208, 06-04-PLAN.md:96, 06-04-PLAN.md:107.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>view/buttons.py</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-06-PLAN.md:13` — - src/crud_views/lib/view/buttons.py

Citations: 06-06-PLAN.md:13, 06-06-PLAN.md:34, 06-06-PLAN.md:40, 06-06-PLAN.md:68, 06-06-PLAN.md:98, 06-06-PLAN.md:99.
 Supplemental declaration candidate: `src/crud_views/lib/resource.py:27` app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py); `tests/test1/test_pipeline_sources.py:36` sources = cv_sources("js")  # created before the bundle exists, like in settings.py.
</details>

<details>
<summary><code>vitest.config.js</code> — UNCHECKABLE / INFO: unsupported or absent from the empty intel index</summary>

`06-07-PLAN.md:71` — &lt;read_first&gt;package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt;

Citations: 06-07-PLAN.md:71.
 Supplemental declaration candidate: `src/crud_views/checks.py:293` hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",; `src/crud_views/lib/assets.py:34` js: tuple = ().
</details>
