I'll review the three Phase 6.1 plans against the current source, starting with the form-button pipeline they claim to extend.
The form pipeline matches the plans' seams. Next I'll check diagnostics, tests, and docs the plans say they extend.
## 06.1-01

The plan extends the real adapter, normalizer, leaf, and class table in the right order. The mechanisms it depends on are already there: keyword configuration is stripped before crispy's `flatatt`, form kind and native type are already separate, and W362 already accepts any key that is in `DEFAULT_BUTTON_CLASSES`.

**Strengths**
- `tag` can follow `slot` and `icon`. `_TableClassMixin.__init__` already keeps those out of `**kwargs`, and crispy puts every remaining kwarg into `flat_attrs` (`src/crud_views/lib/crispy/buttons.py:128-137`; crispy `BaseInput.__init__`). A keyword-only `tag=None` therefore does not leak onto legacy `<input>`s.
- Eligibility via `cv_key == "cancel"` and `cv_type == "button"` matches the live split. `Button.input_type` is `button`, `Submit`/`Reset` stay `submit`/`reset`, and `slot` only changes `_cv_form_kind()` (`buttons.py:139-164`). A `Submit(..., slot="form:cancel")` cannot become a link, and a `Button` subclass still can.
- Raw table access is required. `get_button_class()` turns `None` and non-strings into `""` (`button_classes.py:141-152`), which would hide D-02. `get_button_classes()` is the correct read, and it already merges default, theme, then settings (`button_classes.py:132-138`).
- `crud_views.E365` is unused. E360/E361/E363/E364 are the live ids (`button_classes.py:248-278`). `check_button_classes()` already returns `button_class_check_messages()` (`checks.py:405-407`), so no new check registration is needed. The current `if/elif` also keeps a non-string on E361 only.
- Adding `form:cancel-tag` to `DEFAULT_BUTTON_CLASSES` makes W362 accept that exact key and nothing wider (`button_classes.py:284-285`). `form:cancel-tag:icon` is not a mode key: `_action_key_parts()` requires a `FORM_KINDS` member (`button_classes.py:212-230`). The 73 to 74 count matches `tests/test1/test_button_classes.py:92-94` and the single sentence at `docs/reference/buttons.md:146`.
- Existing callers omit `cv_tag` (`button_data.py:215-307`, `test_button_data.py:445-457`). The plan's verify command runs those files, so a `KeyError` on a missing intent cannot slip through. `tests/test1/conftest.py:41` sets `CRUD_VIEWS_STRICT=True`, so the log-and-fallback path really does need `override_settings`.

**Concerns**
- MEDIUM: Plan 01's anchor can still emit a second `href` and other button-only extras. `data-cv-cancel-url` is already popped (`button_data.py:275`) and the leaf re-emits it (`form.html:2`), so omitting that marker in the anchor branch is enough. Extra `href`, `form`, `formaction`, and `disabled` stay in `cv_flat_attrs` until Plan 02. Do not treat Plan 01 as releasable on its own.
- MEDIUM: The class-table paragraph still says the element is not configurable (`docs/reference/buttons.md:152-153`). Task 2 adds the key and the count in that same page, and the contradiction is only cleaned up in Plan 03.
- LOW: Task 1's own verify command does not include `test_form_buttons_golden.py`. The newline before `class` in `form.html:1-2` is what `tests/test1/golden/form_buttons/create.html:1-4` pins. The plan-level verification does run the goldens, so this is a task-boundary miss, not a missing gate.

**Suggestions**
- Treat a missing raw `cv_tag` the same as `None`. Do not use `ctx["cv_tag"]` or `tag or "button"`.
- In the E365 branch, require `isinstance(value, str)` before membership so `None` stays valid and `""` does not.
- Keep both branches as literal `<a>` and `<button>`. Do not emit `<{{ cv_tag }}>`.
- Name `docs/reference/buttons.md:152-158` in Task 2, or leave that paragraph untouched until Plan 03 so the page is not internally false.

**Risk Assessment:** MEDIUM. The seams and the 74-key grammar are accurate. The remaining risk is the two-line leaf and shipping the anchor before attribute filtering.

## 06.1-02

This plan closes the attribute and compatibility holes that Plan 01 leaves open, and it uses the tests that already pin those contracts. It should not start a second rendering path.

**Strengths**
- Alias order is already hyphen-wins, with no case folding (`button_data.py:196-205`). An empty winning `data-cv-cancel-url` must not revive `data_cv_cancel_url`. `test_form_hyphen_spelling_wins_in_any_order` (`test_button_data.py:672-698`) is the right pattern to extend.
- `type`, `name`, and `value` are already removed from extras for every control (`button_data.py:269-270`). The leaf, not `cv_flat_attrs`, emits them. Anchor filtering only needs the remaining button-only names plus extra `href` and the cancel marker.
- `test_reserved_attributes_resolve_to_one` already checks a raw opening tag for duplicate names and expects `formnovalidate` on the button (`test_crispy_buttons.py:490-500`). That test fails if anchor filtering is applied to the default button path.
- The old custom-template fixture does not mention `cv_tag` (`test_crispy_buttons.py:346-349`), so an added context key does not break it. `render()` already passes only the normalized dict (`buttons.py:166-174`), which is the scoped-context contract to keep.
- Filter Apply/Reset are `Submit`/`Reset`, not cancel `Button`s (`list.py:130-132`). `form:cancel-tag` cannot turn them into links if eligibility stays kind plus native type. Delete stays `Submit(..., slot="form:delete")` (`form.py:130-134`).
- Goldens extract by `name=` on `<input>`/`<button>` only (`test_form_buttons_golden.py:41-65`). A cancel `<a>` has no `name`, so a separate parser is required. Leaving `_extract_controls` alone is the right call. `CRISPY_FLOOR_TESTS` already includes the three files this plan edits (`noxfile.py:28-31`).

**Concerns**
- MEDIUM: `_buttons()` and `_page_buttons()` only see `<button>` (`test_crispy_buttons.py:160-161` and `1165-1173`). `test_endpoint_layout_controls_are_buttons` requires `button[name="reset"]` (`test_crispy_buttons.py:170`). A link test that reuses those helpers fails closed, or worse, asserts "no button" and never checks the anchor.
- MEDIUM: `test_form_buttons_golden.py` has no registry snapshot. `register_button_classes()` writes the process-global theme layer (`button_classes.py:122-125`). The isolate fixture exists only on the class-table tests (`test_button_classes.py:82-89`). A leaked `"a"` makes later default goldens and `test_cancel_origin.py`'s `data-cv-cancel-url` regex fail under `pytest -n auto`.
- LOW: Task 2's action mentions CRUD submission regressions, but its verify command omits `test_crud.py` and `test_delete.py`. Plan 03 runs `test_crud.py`. The configured delete POST still needs to live in a file this wave actually executes.

**Suggestions**
- Select anchors with a raw `<a ...>` match plus `cssselect("a")`, using the same attribute-name regex as `test_crispy_buttons.py:490-492`. DOM parsing will hide a duplicate `href`.
- Drive page integration only through `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`, not `register_button_classes()`.
- Filter case-insensitively only after `cv_tag == "a"` is final. `Disabled=""`, `0`, and `"false"` must still take the button fallback, because `flatatt` emits them and HTML treats presence as true.
- Drop case variants of generated `id`, `class`, and icon-mode `title` / `data-cv-tooltip` on the anchor only. Exact `id`/`class` pops (`button_data.py:271-274`) do not catch `ID`.

**Risk Assessment:** MEDIUM. The filtering rules match the current normalizer, but the existing button-only helpers will not prove the link.

## 06.1-03

Publishing and acceptance are aimed at the real docs parser, the real JS handler, and a baseline that is currently clean. The plan correctly refuses to call jsdom a browser pass.

**Strengths**
- `viewset.js:37-43` calls `preventDefault()` and assigns `location.href` for any `[data-cv-cancel-url]`, including an `<a>`. The existing test at `tests/js/viewset.test.js:93-98` proves that. Omitting the marker is what makes ctrl-click and a new tab work. The plan's new event test matches that handler.
- `2a94f24b80ae451d63530369d7ef40375a1a2604` exists, is an ancestor of HEAD, and `git diff` of `viewset.js` plus `tests/test1/golden/form_buttons/` against it is empty. The invariant check is real.
- Both JS paths in the verify command exist: `tests/js/viewset.test.js` and `tests/js/list.filter.test.js`. The wrapper forwards them after `--` (`.planning/phases/06-form-button-leaf/06-js-verify.sh:134-135`).
- `_theme_recipe()` unpacks exactly one Python fence and one template fence (`test_form_button_docs.py:166-172`). The plan's warning not to drop a second example into `## Custom form-button templates` is accurate. `FENCE` is Python-only (`test_label_mode_docs.py:24`).
- An Added entry, with migration text only if a Breaking entry appears, matches the behavior. Default users still get the button in `form.html:1-2`. Extra `cv_tag` does not break the pill recipe, which never reads it (`docs/reference/theme.md:176-184`).
- `examples/bootstrap5/manage.py` exists, and the plan forbids committing example settings. That is the right UAT boundary.

**Concerns**
- MEDIUM: Plan 03 never names the sentence that will still be false after Plan 01: the table "is not configurable here: the element" (`docs/reference/buttons.md:152-153`). The form-contract exclusion of `cv_tag` (`buttons.md:473-477`) is named. The class-table claim is not.
- LOW: E365 will not appear in `checks.py:406` or the checks table at `buttons.md:575-579` unless Task 1 is read broadly. `files_modified` does not include `checks.py`. The check still runs. Only the published id list lags.
- LOW: `test_form_button_docs.py` is not in `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`). The final `pytest tests -n auto` covers it. The floor session will not.

**Suggestions**
- Put the cancel recipe in `buttons.md`, and teach the theme.md extractor to select `PillSubmit` by name if a second fence must sit in that section.
- Add an E365 row next to E364 in `buttons.md`, and extend the `checks.py:406` docstring in the same task.
- Record the browser check as pending unless a real browser was used. `viewset.test.js` cannot show a second tab or scripts-disabled navigation.
- Keep the Phase 7 handoff to the three names the freeze already expects: `form:cancel-tag`, `Button(tag=...)`, and `FORM_LEAF_KEYS` `cv_tag`.

**Risk Assessment:** LOW for code, MEDIUM for the doc contradiction and for marking the phase done before the human browser check. The automated gates match the repo.

## Cross-plan

The three plans cover the four roadmap criteria without a second registry or a JS change. Plan 01 selects the tag. Plan 02 decides what an anchor may emit. Plan 03 publishes and proves the handler stays off the link. That split matches the code: selection belongs in `_form_button_data()`, presentation in `form.html`, and navigation is already `viewset.js:40-43`.

The phase fails its own compatibility goal if Plan 01 is merged alone. Until Plan 02, `{{ cv_flat_attrs }}` can still carry a conflicting `href`. Until Plan 03, `docs/reference/buttons.md:152-153` contradicts the new key. Neither gap is a reason to reorder the waves.

No plan invents requirement ids. `REQUIREMENTS.md` still has none for 6.1. That is consistent with the roadmap, not a hole in these plans.

## Overall risk

MEDIUM. The plans track the current pipeline, the 73-key guard, the free diagnostic id, the single-fence doc parser, and the cancel click handler. The work that can still go wrong is the byte-identical button branch, anchor-only filtering, and not calling the phase accepted before the no-JS and new-tab check is actually observed.
