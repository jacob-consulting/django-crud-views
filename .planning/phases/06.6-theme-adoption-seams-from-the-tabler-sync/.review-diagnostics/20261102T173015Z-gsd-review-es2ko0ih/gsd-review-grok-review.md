I'll verify each plan against the current source, starting with the form, label-mode, class-table, and alert seams the plans depend on.
## 06.6-01

**Summary.** The ownership split matches the code: page templates already own the outer `<form>` and token (`view_create.content.html:5-10` and the update/custom/delete twins), while `cv_render_form` only flattens into `tags/form.html`, which reads `form.helper` twice (`templatetags/crud_views.py:464-466`, `tags/form.html:3-6`). Library helpers never set `form_tag` (`crispy/form.py:43-50`, `136-146`), and both installed packs emit CSRF whenever `form_method` is POST and `disable_csrf` is false, independent of `form_tag` (floor and current `whole_uni_form.html:4-7`). The tracer is the right first slice. It does not leave the suite green, and CSRF suppression is easy to bypass.

**Strengths.**
- Diagnosing the same helper instance that is rendered matches the property that allocates a new `FormHelper` on every access (`form.py:43-50`).
- Using raw `_form_action` is required: the public property calls `reverse()` (`helper.py:232-236`).
- `form_tag=True` is rejected in both strict modes, while unused wrapper settings follow strict/warn. That matches `is_strict()` and test `CRUD_VIEWS_STRICT=True` (`exceptions.py:32-36`, `conftest.py:41`).
- The stop-if-no-safe-copy rule is justified. `FormHelper` has no `__copy__`; `copy.copy` shares `layout`, `attrs`, and `inputs`.

**Concerns.**
- **HIGH:** Task 01-01 changes every `cv_render_form` caller, but goldens stay nested until plan 05. `tests/test1/golden/form_frame/create.html:1` (and update/custom/delete) still expect an inner `<form>` and a second token. `test_stock_markup_unchanged` compares them (`test_form_frame.py:71-73`). Wave 1 verify never runs that module, so the first commit is red.
- **HIGH:** Suppression lives only behind `cv_form_helper`. Workflow still calls `{% crispy form form.helper %}` (`view_workflow.action.html:15`). A copied `tags/form.html` that keeps reading `form.helper` gets `form_tag=False` from the library helper and still emits a second token. Nothing in this plan fails that template.
- **MEDIUM:** Setting `form_tag=False` on `CrispyFormMixin.helper` hits `WorkflowForm` (`forms.py:11`) immediately, while token suppression waits for plan 05. Intermediate workflow pages are one form and two tokens.
- **LOW:** `FormHelper` in the cached crispy 2.x tree has no `__bool__`/`__len__`. The falsey-helper case is only a custom helper, which the plan does test.

**Suggestions.**
- Update the four frame goldens in this plan, or make 05 a hard blocker before any 01 commit is treated as green.
- Add a negative render: a copied inner template that ignores `cv_form_helper` must still be one token, or the migration must say that path stays broken on purpose.
- Keep workflow on the old helper until 05, or route it here so `form_tag=False` and token suppression land together.

**Risk Assessment.** HIGH. The mechanism is right, but the first commit breaks existing frame goldens and does not close the CSRF hole for any render path that still reads `form.helper`.

## 06.6-02

**Summary.** The theme layer belongs in `default_label_mode()` (`label_mode.py:86-119`). Today an absent or invalid setting falls straight to `LABEL_MODE_DEFAULTS`, and `form_label_mode` / W292 already call that function (`label_mode.py:122-145`, `buttons.py:546-571`, `base.py:348-349`). Cards also call it (`card.py:54`, `119`). The public API and atomic-reject rule match D-05–D-07. The plan under-specifies the fallback so it does not recurse, and the new registry fixture is not required to be autouse.

**Strengths.**
- Not merging owner maps matches `cv_get_action_label_mode`: view/button/map membership wins before the floor (`base.py:331-349`).
- E108 already validates the raw setting and does not need to know about themes (`settings.py:159-188`). W292 will follow a theme floor once the resolver does, without instantiating forms (`buttons.py:464-469`).
- Copy-then-merge is the right contrast with `register_button_classes`, which `update`s in place (`button_classes.py:135-138`).
- Package floor is a `MappingProxyType` (`label_mode.py:23-25`). Leaving it immutable is correct.

**Concerns.**
- **MEDIUM:** Invalid-setting fallbacks currently call `LABEL_MODE_DEFAULTS[location]` directly (`label_mode.py:103-118`). Pointing those lambdas at `default_label_mode()` recurses while the bad setting is still installed. The plan never names a package-then-theme helper that ignores the bad setting.
- **MEDIUM:** `isolate_label_mode_warnings` is autouse (`conftest.py:23-32`). The new theme-map fixture is not specified as autouse, so a test that registers and does not request the fixture leaks inside an xdist worker.
- **LOW:** Task 02-01 only requires a form-button render. `card` / `list` / `context` will change only if every caller goes through the same function, which they do, but the plan does not pin a non-form location.

**Suggestions.**
- Specify `_effective_floor(location)` that reads theme then package and never re-reads the setting. Use it as the invalid-setting fallback.
- Make the snapshot/restore fixture autouse, same as the warning register.
- Assert `default_label_mode("card")` under a theme registration so card cannot drift back to a literal.

**Risk Assessment.** MEDIUM. The insertion point is correct. A naive fallback loop is the main way the task fails its own strict/non-strict cases.

## 06.6-03

**Summary.** The floor failure is real. Current `formactions.html:3` prints `formactions.css_class`; the declared floor template is `class="mb-3"` and never reads it (`crispy_floor-3-12-django-6-0/.../formactions.html:1-9`). The three constructors are separate (`form.py:55-56`, `136-145`, `list.py:125-133`). A pack-scoped bridge is the only way to satisfy D-10 without raising the floor. The plan still misses the closed key set that will fail as soon as the defaults grow, and it does not say how a non-Bootstrap pack gets the classes.

**Strengths.**
- `get_template_name` uses a literal path when the template has no `%s` (`layout.py:19-23`), so a library template can be selected per group without shadowing `bootstrap5/layout/formactions.html`.
- Empty defaults are safe on the current pack: `default:''` treats `""` and `None` the same (`formactions.html:3`). Filter hidden inputs stay on `add_input` (`list.py:88-90`, `111-123`), outside the group.
- W362 already accepts any key present in `DEFAULT_BUTTON_CLASSES` and rejects a mode suffix that is not `form:<kind>:<mode>` (`button_classes.py:251-266`, `328-345`). Adding `form:actions` without putting `actions` in `FORM_KINDS` is the right grammar.
- Delete does not call `get_form_actions`, so wiring only the ordinary hook would miss it. The plan says that.

**Concerns.**
- **HIGH:** `EXPECTED_KEYS` is a closed set and `test_default_table_is_complete` asserts `len == 84` and set equality (`test_button_classes.py:21-106`). This plan never lists that file. Its verify also skips `test_button_classes.py`.
- **MEDIUM:** Capability detection is specified for Bootstrap. `FormActions.template` is `"%s/layout/formactions.html"` (`bootstrap.py:297`). A Tabler pack that also ignores `css_class` will not get the Bootstrap fallback (good) and will not get the classes (D-12). Plan 07’s adaptation list does not include pack layout templates.
- **MEDIUM:** A wrong selection rule that applies the floor wrapper to the current pack changes `flat_attrs`, `form-horizontal`, and `field_class` (`formactions.html:1-10` vs floor `:1`). The tests can catch this only if both runtimes stay in the task verify, which they do. Do not drop the current-pack empty-byte assertion.
- **LOW:** The buttons.md arithmetic sentence (`buttons.md:151-153`) is not checked beyond the integer. A new count can match `len(DEFAULT_BUTTON_CLASSES)` while the “adds six size keys…” clause is stale.

**Suggestions.**
- Add `tests/test1/test_button_classes.py` to this plan and to 04, and update `EXPECTED_KEYS` in the same task as the new defaults.
- Detect “does this pack’s resolved `formactions` template read `css_class`?” per active pack, not by a Bootstrap version threshold. If the acquired Tabler template does not, plan 07 must patch that template in the isolated copy.
- Keep the floor fallback’s empty output byte-identical to `class="mb-3"`, including no trailing space.

**Risk Assessment.** HIGH. The bridge is necessary and the current/floor split is evidenced, but the closed key test and the unknown Tabler pack template are unowned failure modes.

## 06.6-04

**Summary.** The leaf still hard-codes the two class strings beside an existing level lookup (`alert.html:2-5`). Defaults in the golden are exactly `alert-dismissible fade show` and `btn-close` (`golden/alerts/dismissible.html:2-6`). Routing them through `cv_button_class` is autoescaped (`templatetags/crud_views.py:570-573`). Dismissal stays on `data-cv-alert-dismiss` (`viewset.js:46-49`). The plan is the smallest of the nine and still omits the key-set guard.

**Strengths.**
- W362 will accept the new base keys once they are in the default table and will still warn on `alert:close:icon` (`button_classes.py:328-345`). No grammar change is required.
- `btn-close` is already an exempt source token (`test_button_classes_templates.py:24`). Moving it into `button_classes.py` (itself exempt, `:25`) does not trip the literal scanner.
- Not regenerating the default golden is the right byte-identity check. The leading space is in the template, not in the class string (`alert.html:2`).

**Concerns.**
- **HIGH:** Same closed set as 03. Adding two keys fails `test_button_classes.py:104-106` and the doc-count parse at `:112-116`. This plan’s verify runs `test_alerts.py` and `test_button_classes_checks.py` only.
- **MEDIUM:** An empty override rendered as `{% if alert.dismissible %} {% cv_button_class "alert" "dismissible" %}{% endif %}` leaves a trailing space when the resolved class is `""`. The default golden will not catch that. `test_alerts.py:196-198` pins the unconfigured strings and must be updated in the same change, which the plan does list.
- **LOW:** `SENTINEL_CLASSES` is built from the live table (`test_button_classes_templates.py:131-136`). Full replacement of the literals keeps the button-chain guard green. A leftover `alert-dismissible` on a sentinel-styled alert would be an offender (`:153-162`).

**Suggestions.**
- Update `EXPECTED_KEYS` and the count sentence in task 04-01, before the alert tests.
- Emit the dismissible class only when the resolved string is non-empty, so omission does not add a space. Assert the raw default golden, not a normalized one.

**Risk Assessment.** MEDIUM. The template change is local, but the unlisted key-set test makes the task’s own “suite stays green” claim false.

## 06.6-05

**Summary.** Expanding the 01 boundary to workflow is required: `view_workflow.action.html:6-16` is the only stock form that does not call `cv_render_form`. Protected delete already omits the form (`view_delete.content.html:8-23`). Modal bodies include the same content template (`modal/content.html:7-8`). The request matrix is the right proof. Page-wide “one form” is stronger than the templates can support once chrome or action forms appear, and the golden update is a wave later than the markup change.

**Strengths.**
- Workflow choice omission is `has_workflow_choices` (`views.py:82`, template `:6-18`), not “every page has a form.” The plan’s exception list matches that.
- `Client(enforce_csrf_checks=True)` is meaningful: CSRF middleware is installed (`conftest.py:69`).
- Frame goldens normalize only the token value and whitespace (`test_form_frame.py:44-47`), so a raw count in the new tests is what actually sees nesting. The plan says not to hide that in the normalizer.
- Cancel and context actions on the stock create/workflow fixtures are links (`settings.py:90-95`, `views.py:617`, `632`), so a content-region count of one is realistic for those pages.

**Concerns.**
- **HIGH:** Must-haves say the page response contains one form and one token. The test base includes `{% cv_context_actions %}` (`app/crud_views.html:24`). Action POST controls render hidden forms with their own tokens (see `golden/action_menus/list_full.html`). A page-wide count fails as soon as a fixture has a submit-form action. Plan 07’s Tabler chrome will fail the same way.
- **MEDIUM:** This plan depends only on 01, so it inherits 01’s copied-template bypass. Replacing the package workflow template does not fix a theme copy of `view_workflow.action.html`.
- **LOW:** Task 05-01’s verify includes `test_workflow.py` and `test_crud.py` but not `test_form_frame.py`. The golden rewrite is task 05-02. A per-task commit is red in between.

**Suggestions.**
- Count `form.cv-form` and tokens inside that form, not every `<form>` in the document. State that language and action forms are out of the one-owner claim.
- Include a formset update page: inline helpers already set `disable_csrf = True` (`inline_formset.py:56-59`), but `PublisherFormSetForm` only clears `form_tag` (`views_formset.py:44-50`). The main form must go through the render-local suppression.
- Name copied workflow templates in the 08 migration, not only `tags/form.html`.

**Risk Assessment.** MEDIUM. The stock paths are identified correctly. The acceptance wording over-counts forms and will false-fail on real pages unless the assertion is scoped.

## 06.6-06

**Summary.** The historical companions are not on this machine (`/home/alex/projects/alex` has no Tabler checkout). Pinning the core baseline to `cb26af4` is valid for product source: `cb26af4..HEAD` has no `src/`, `tests/`, or `docs/` commits. The plan correctly refuses a synthetic theme. It cannot satisfy THEME-05 by itself.

**Strengths.**
- Fail-closed on missing sources, zero collection, and mutated fingerprints matches D-13/D-18. A capture that records failures without marking them passed is the right baseline shape.
- Isolated copies plus before/after digests match D-11/D-14. Original worktrees stay read-only.
- Negative tests in `test_theme_adoption_sources.py` can land without the companions. That is the only part of THEME-05 this wave can actually execute.

**Concerns.**
- **HIGH:** Task 06-02 is an external blocker. Plans 07 and 09 depend on it. If `CV_THEME_SOURCE` / `CV_PACK_SOURCE` stay unset, the phase cannot be accepted. That is required by D-12, not a planning error, but it is the phase’s critical path.
- **MEDIUM:** “Discover from workspace metadata, never guess a similar name” is the right rule and is easy to violate in a search under `/home/alex`. The plan should fail if more than one candidate matches.
- **LOW:** The pinned core is product-equivalent to HEAD today. If product commits land before capture, the archive must be re-cut or the unrelated-failure comparison mixes later fixes into the baseline.

**Suggestions.**
- Require a single explicit revision or content hash even when discovery finds a directory. Do not accept a dirty companion as the baseline without recording the diff as part of the identity.
- Keep 06-01 mergeable when 06-02 is blocked, and make 07’s precondition check the JSON, not the env vars alone.

**Risk Assessment.** HIGH for phase completion, LOW for the utility itself. The plan does not pretend a fixture is the reference theme. Acceptance is blocked until real sources exist.

## 06.6-07

**Summary.** This is the only plan that can meet D-12/D-18, and it correctly refuses a native substitute. Browser checks for `element.form`, `FormData`, and enforced CSRF are the right proof that a token in the HTML is the token the browser will submit. The adaptation list does not include the pack layout template that research already showed can drop group classes, and a whole-document form count will not survive Tabler chrome.

**Strengths.**
- Depends on 02, 03, 04, 05, and 06, so it cannot run on a partial theme surface.
- Reusing `presentation.cjs` / owned-port cleanup is consistent with existing browser harnesses. Config rejection before launch is the right fail-closed order.
- Replay from a fresh copy of the exact base, compared to `06-companion-baseline.json`, is what makes “no new regressions” falsifiable.
- Original digest checks after replay match D-14.

**Concerns.**
- **HIGH:** “Raw response counts” of one form and one token will fail on a real theme page that has a language form, search form, or action POST form. The test app base happens to be clean (`app/base.html` has no language form). Tabler will not. Scope the count to `form.cv-form` or the case is either red or quietly waived.
- **HIGH:** Temporary adaptations listed are registrations, copied inner templates, helpers, and class keys. They do not include the pack’s `layout/formactions.html`. Floor Bootstrap ignores `css_class`. If crispy-tabler does too, D-12’s action-group case cannot pass without a pack patch the plan never authorizes.
- **MEDIUM:** Eight case families on one long browser run have no per-case artifact name until the run writes JSON. A mid-run crash can leave an owned server. The plan says cleanup on every path; that has to be `finally`, not only the success path.
- **LOW:** Reusing 07 evidence in plan 09 is only valid if source hashes match. The plan says that. Keep the hash check in 09, not as a comment here.

**Suggestions.**
- Assert association (`element.form`, submitter, cookie token) for the package form. Treat other forms as out of scope and record their counts, do not require zero.
- Add an explicit pack-template adaptation step when the acquired `formactions` template does not contain `css_class`. Put that diff in `07-tabler-adaptation.patch`.
- Record browser, asset, and AT limits in the JSON the human check will cite. Do not infer them in 09.

**Risk Assessment.** HIGH. This plan is the acceptance gate, and two of its checks are aimed at the wrong DOM scope or the wrong template.

## 06.6-08

**Summary.** Author-facing docs can be executable without the companions, and the plan correctly forbids claiming Tabler passed. The contracts to document are the ones 01–05 actually implement: `register_label_mode_defaults`, `cv_form_helper`, the detectable wrapper set, and the two group keys. Pairing Breaking notes with `docs/migrating-1.0.md` matches the repo rule. The recipes will be wrong if they describe a helper-copy strategy 01 has not yet locked.

**Strengths.**
- Existing doc tests execute fenced snippets (`test_heading_docs.py:31-37`, `test_label_mode_docs.py`). Reusing that pattern makes a stale recipe fail.
- Distinguishing Fixed nested-form/token removal from Breaking helper rejection matches D-01 versus the DOM bugfix. `form_tag=True` always errors; unused wrappers warn unless strict (`exceptions.py:32-36`).
- Leaving singular/plural label-mode names alone matches the Phase 1 decision. Settings prose that says the floor is package-only (`settings.py:64-66`, `72`) does need the rewrite this plan assigns.
- Strict `mkdocs build` is an existing gate and is in the verify list.

**Concerns.**
- **MEDIUM:** The plan can run in parallel with 07. A recipe that says “the render boundary copies the helper and sets `disable_csrf`” may not match the strategy 01 actually accepted. Docs must be written from `01-ownership-evidence.md`, not from the research probe.
- **MEDIUM:** Copied workflow templates are not named. The only package bypass is `view_workflow.action.html:15`. A theme copy of that file is the same hole.
- **LOW:** Product docs must not name the downstream theme repo. The plan says that. Keep the Tabler patch in the phase handoff only.

**Suggestions.**
- Make 08 depend on the 01 evidence file’s chosen strategy, and quote the detectable attribute set from the tests rather than from research.
- Add a workflow-template migration snippet: replace `{% crispy form form.helper %}` with `{% cv_render_form %}`.
- Run the doc recipes once under the floor interpreter in 09, as the plan already asks, because the group opt-in is the piece that differs by pack.

**Risk Assessment.** MEDIUM. Documentation structure is sound. It will drift if it is written against the research candidate instead of the recorded helper strategy.

## 06.6-09

**Summary.** The handoff inventory is the right close for D-19, and refusing to mark the phase accepted without companion replay or the human check matches D-18. The integrated command list does not match the repo’s own floor contract, and it never runs Django 6.0 with the current crispy pin.

**Strengths.**
- `--check-final` rejecting stale hashes, zero collection, and skipped required cases is the right evidence gate. Historical `CRISPY_FLOOR_DESELECT` is one named test (`noxfile.py:54-57`), and the plan keeps that name.
- Preservation commands for modal focus and conditional formsets are existing scripts, not new product behavior. That matches the exclusion of reopening 6.4/6.5.
- The human check is explicitly pending until a person writes it. Automation cannot fill it.
- Private bridge symbols are called out as non-public. That keeps Phase 7 from freezing `_ThemedFormActions`.

**Concerns.**
- **HIGH:** The floor gate is `pytest tests` on `.nox/crispy_floor-3-12-django-6-0` with one deselect. The repo’s floor session only runs `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`, `96-106`) because pack wrapper bytes differ and the full tree was never certified at crispy-bootstrap5 2023.10. The plan forbids new waivers. Pre-existing floor failures outside that list will block the phase or force a waiver the plan itself rejects.
- **HIGH:** Final Python evidence is Django 4.2, Django 5.2, and floor Django 6.0. There is no `.nox/tests-3-12-django-6-0` venv, and no command runs Django 6.0 with the current pack. `DJANGO_VERSIONS` includes 6.0 (`noxfile.py:3`). CSRF ownership was only probed on 6.0 at the floor.
- **MEDIUM:** “Required phase cases all pass on the floor” plus “do not invent a waiver” conflicts with the single allowed deselect if a new group assertion is accidentally placed inside `test_filter_form_baseline`. The plan says not to do that. Keep group assertions in `test_theme_action_groups.py`.
- **LOW:** Three Python 3.12 runs are not the 3.12–3.15 matrix. The plan already says not to claim that. Keep the wording in the acceptance file.

**Suggestions.**
- Run the existing `CRISPY_FLOOR_TESTS` list plus the new theme modules on the floor interpreter. Run `pytest tests` on the current-pack 4.2 and 5.2 venvs. Add a current-pack Django 6.0 run, or record that the cached matrix has no such interpreter and do not call 6.0 current-pack covered.
- Do not let `--check-final` pass when `07-tabler-replay.json` is absent. The plan says this. Make the utility test fail a fixture that omits that file.
- Bind the human observations to the same source hash as `09-final-evidence.json`.

**Risk Assessment.** HIGH. Automated preservation is well scoped. The floor command as written is a likely false gate, and Django 6.0 current-pack is simply not in the evidence set.

## Cross-plan

The wave split is mostly right. 01, 02, 04, and 06 do not share product files. 03 waits for 01 (`form.py`) and 04 (`button_classes.py`, `buttons.md`). 05 waits for 01. 07 waits for the theme surface and the baseline. 08 can document without Tabler. 09 waits for both.

The ordering bug is evidence, not code. Plan 01 changes markup that `test_form_frame.py:71-73` pins, and plan 05 is the first plan allowed to rewrite those goldens. Between those waves the suite is red. Plans 03 and 04 add default keys and never edit `EXPECTED_KEYS` (`test_button_classes.py:104-106`), so they are red even against their own unstated guards.

CSRF is one mechanism in three places. Page templates own the outer token. Pack templates emit another unless `disable_csrf` is set (`whole_uni_form.html:4-7`). Only the selected helper inside `cv_render_form` is planned to clear that flag. Workflow (`view_workflow.action.html:15`) and any copied inner template that still reads `form.helper` skip it. 05 fixes the package workflow file only.

Action-group styling is proven only for Bootstrap. Current pack reads `css_class`; the floor pack does not. Tabler is unknown and not on disk. 03’s bridge must not be applied to a pack that already works, and 07 must be allowed to patch a pack template that does not.

Companion acceptance is a hard external dependency. 06-02, 07, and 09 cannot be marked done without authoritative checkouts. That is consistent with D-11–D-14. A fixture-only run must stay a blocker, which those plans do say.

## Overall risk

**HIGH.** The four product seams are aimed at the right source, and the decisions D-01–D-19 are not contradicted by the code I read. The plans are not safe to execute as acceptance criteria until three gaps are closed: frame goldens and `EXPECTED_KEYS` move into the plans that change them; one-form/one-token assertions are scoped to `form.cv-form`; the floor gate stays the existing limited list, with a separate current-pack Django 6.0 run. Tabler remains a blocking acquisition, not a review uncertainty.
