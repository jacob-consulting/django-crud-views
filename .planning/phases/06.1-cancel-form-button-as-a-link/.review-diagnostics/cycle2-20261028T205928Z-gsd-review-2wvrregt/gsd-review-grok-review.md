I'll verify the three updated plans against the source and prior review findings, starting with the files they claim to extend.
Prior H1–H3 and A1–A10 are in the phase review. Next I’ll trace those claims against the files the updated plans actually modify.
The prior HIGHs still depend on collateral tests the plans now claim to own. I’ll check those tests and the registry/docs contracts next.
Reviewed the updated plans at `af5ecdf` against the live tree. Requirements `[]` / TBD match `ROADMAP.md:314`. No plan file was edited.

## 06.1-01

**Prior HIGHs.** H1, H2, and H3 are closed as executable actions. Source still has the old collisions; that is expected before execution.

- **H1 closed.** `tests/test1/test_button_classes_templates.py:123` builds `SENTINEL_CLASSES` from every `DEFAULT_BUTTON_CLASSES` key, and `:241-265` renders cancel controls through `cv_button_data` under `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:41`). An `x-form-cancel-tag` value would raise once the key exists. Task 2 now owns that file, sets `form:cancel-tag` to `"button"`, keeps CSS sentinels separate, and runs the shard. Do not use `"a"`: `_form_contract` supplies a URL (`:195`), and `:266` requires a `button`.
- **H2 closed.** `tests/test1/test_form_button_checks.py:894-895` still forbids `cv_tag`. Task 3 owns that file, drops only that exclusion, asserts effective `"button"` on the unconfigured missing-icon cases (`:833-843` have no tag override), and runs the shard. The other exclusion, `tests/test1/test_button_data.py:484`, is Task 1's file.
- **H3 closed inside this plan, not deferred to 03.** `tests/test1/test_label_mode_docs.py:759-765` requires the `### The form leaf contract` table (`docs/reference/buttons.md:473-495`) to equal `FORM_LEAF_KEYS`. Task 3 adds the `cv_tag` row before Plan 01 finishes and runs that test. The regex at `:761` only matches a backticked `cv_*` cell.

**Summary.** The plan extends the real adapter, normalizer, and leaf, and it now owns the three collateral contracts that would otherwise fail as soon as `cv_tag` and `form:cancel-tag` exist. The validation order matches the locked decisions.

**Strengths**
- Eligibility stays `cv_key == "cancel"` and `cv_type == "button"`, matching the slot/type split at `src/crud_views/lib/crispy/buttons.py:139-164` and `FORM_TYPES` at `src/crud_views/lib/view/button_data.py:69-70`. `Submit.input_type` is `"submit"` before `super().__init__`, so a re-slotted Submit cannot become a link.
- Tag selection uses the raw table. `get_button_class()` at `src/crud_views/lib/button_classes.py:151-152` turns `None` into `""`, which D-02 treats as invalid. `is_strict()` is call-time (`src/crud_views/lib/exceptions.py:32-36`).
- E365 fits the existing chain: non-strings already take E361 (`button_classes.py:251-258`); `check_button_classes` only returns `button_class_check_messages()` (`src/crud_views/checks.py:405-407`). W362 still accepts a key only if it is in `DEFAULT_BUTTON_CLASSES` or a real mode key (`:284-302`). `cancel-tag` is not in `FORM_KINDS` (`:213`).
- A1 is an executable boundary, not a ledger claim. `helper.add_input()` never calls `render()`; `tests/test1/test_crispy_buttons.py:1636-1657` still expects pack `<input>`s. Constructor checks for explicit `tag` close that bypass. `None`/`"button"` must not call `_cv_form_kind()`, so `slot="formset:control"` stays quiet. Crispy puts leftover kwargs into `flat_attrs`, so `tag` must be popped before `super().__init__`.

**Concerns**
- **LOW:** `docs/reference/buttons.md:146-150` explains the 73-key total. Task 2 changes the count to 74 and adds a row, but it does not say to extend that arithmetic. `tests/test1/test_button_classes.py:100-104` only checks the integer, so a stale breakdown still passes.

**Suggestions**
- Name `docs/reference/buttons.md:571-579` and `docs/migrating-1.0.md:46` in the E365 doc edit. "Class-table diagnostics reference" can be read as prose near `:249` and leave the system-check table stale. No test enumerates that table.
- Keep `tag` a `str | None`. An `object()` sentinel would break the deepcopy path that `_KIND_ICON` already had to avoid (`buttons.py:25-28`).

**Risk Assessment.** LOW. The three HIGH collisions now have owners, files, and failing commands. Residual risk is documentation arithmetic, not a broken render or check path.

## 06.1-02

**Prior actions.** A5 and A8 are closed in the task text, not only the ledger.

- **A5 closed.** Cancel id is `button-id-reset` on all four cases (`tests/test1/test_form_buttons_golden.py:97-107`, goldens such as `tests/test1/golden/form_buttons/create.html:3`). The surviving native control is `submit-id-submit` or `submit-id-delete`. Task 2 scopes to that control's form, then requires one `a#button-id-reset` and no `button#button-id-reset`. `_extract_controls` (`:46-64`) only sees `name=` on `<input>`/`<button>`, so an anchor would be invisible to it. A toolbar `<a href="/author/">` cannot satisfy the id check.
- **A8 closed.** Page tests use `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`. `setting_changed` clears the cache (`src/crud_views/lib/button_classes.py:116-119`). Theme mutation stays in Plan 01's isolated fixtures (`tests/test1/test_button_classes_checks.py:12-19`).

**Summary.** Attribute filtering and page integration are specified against the real normalizer and the real page fixtures. Default bytes stay on the existing golden path.

**Strengths**
- Filter-after-effective-tag matches `_form_attrs` (`button_data.py:196-205`), which hyphenates but does not lowercase. Case-insensitive removal is required for `HREF` / `Disabled` leaks. `flatatt` emits `disabled=""` for `""` and omits `False`/`None`, so presence-based fallback is the right rule.
- Old `CUSTOM` (`tests/test1/test_crispy_buttons.py:346-350`) does not print `cv_tag` or `cv_flat_attrs`. Extra context does not change its field list if `cv_type` / `cv_name` / `cv_value` / `cv_cancel_url` stay. That is the D-16 compatibility proof.
- Plan-level golden and import-safety commands are real. `form.html:1-2` is two fixed lines; the plan forbids regenerating goldens.

**Concerns**
- **LOW:** "Unique native action id from `CONTROL_CASES`" is ambiguous until the next sentence. Both expected controls have ids. Selecting `button-id-reset` as the native control fails once it is an anchor. The following `a#` / `button#` sentence disambiguates if the executor reads both.

**Suggestions**
- In the page test, take the expected control whose id is not `button-id-reset`, then compare `href` to that case's `data-cv-cancel-url` (`/author/` vs `/campaign/` at `:103-107`).

**Risk Assessment.** LOW. The selector and settings-isolation holes from cycle 1 are now mechanisms, not intentions.

## 06.1-03

**Prior actions.** A3, A4, A6, A7, and A10 are closed in executable text. A9 is disposed, not fixed. A1's public boundary is carried forward.

- **A3 closed.** Task 1 requires `rel="noopener"` only when the caller sets `target="_blank"`, and forbids the renderer from inventing `rel`.
- **A4 closed.** Task 2 of Plan 01 owns `tests/test1/test_button_classes_checks.py:1`; Task 3 owns `src/crud_views/checks.py:406`. This plan preserves that reference.
- **A6 closed.** Artifacts and Task 2 name `form:cancel-tag`, `Button(tag=...)`, `FORM_LEAF_KEYS.cv_tag`, and `crud_views.E365` for the Phase 7 guard.
- **A7 closed.** Insert before `tests/js/viewset.test.js:569-580`. The cancel suite is the `describe` at `:92`. The reload test must stay last because it adds a second document listener.
- **A10 closed in Plan 01 Task 2**, which this plan is told to preserve. The live sentence is still `docs/reference/buttons.md:152-153`.
- **A9 deferred, not closed.** `ROADMAP.md:332` still says `TBD (run $gsd-plan-phase 6.1 ...)`. The plan refuses a ROADMAP edit and says the line does not create a fourth plan. That is a disposition, not a product defect.
- **A1 public half closed.** Task 1 documents construction-time rejection for explicit invalid tags and non-eligible `a`, and pack-owned inputs for legacy `None`/`button`.

**Summary.** Docs, release notes, JS noninterference, and browser acceptance are separated correctly. One published-recipe hole can still defeat native navigation.

**Strengths**
- `viewset.js:37-43` calls `preventDefault()` on any `[data-cv-cancel-url]`, including an `<a>`. Omitting that marker is the only way D-14 works without editing the script. The plan keeps the script and the goldens pinned to `2a94f24b80ae451d63530369d7ef40375a1a2604`; that diff is empty, and the commit is an ancestor of `af5ecdf`.
- The existing marked-anchor test at `tests/js/viewset.test.js:93-98` must keep passing. New cases are unmarked clicks only. The wrapper at `.planning/phases/06-form-button-leaf/06-js-verify.sh` exists, and `fails_when` requires both requested files in the summary.
- `_theme_recipe()` unpacks exactly one Python fence and one template fence (`tests/test1/test_form_button_docs.py:166-170`). Scoped extraction is required, and `read_first` includes that section.
- Browser acceptance is a human check. jsdom is not treated as a new tab.

**Concerns**
- **MEDIUM:** The theme recipe can reintroduce interception. `docs/reference/theme.md:187-189` says keep `data-cv-cancel-url` because `viewset.js` reads it. Task 1 says retain that guidance and add a cancel-capable template. It does not require the published `<a>` branch to omit the marker, and the docs test does not require that assertion. A copied recipe that keeps the marker hits `viewset.js:40-43` and never navigates natively. Package-leaf tests do not catch a bad fence.
- **LOW:** Layout prose still says every layout control "renders one `<button>`" (`docs/reference/buttons.md:426-427`). "Replace any remaining assertion" covers it only if the executor treats that bullet as an assertion. No test pins the sentence.

**Suggestions**
- Require the extracted cancel-capable fence to render an `<a>` with no `data-cv-cancel-url`, and amend `theme.md:187-189` so the marker is button-only.
- Add an `E365` row at `buttons.md:575` and name it beside `E361`/`W362` at `migrating-1.0.md:46`.

**Risk Assessment.** MEDIUM, only because the copy-paste recipe can undo native navigation. Automated package behavior is otherwise specified.

## Cross-plan

| ID | Verdict |
|---|---|
| H1 | Closed in 06.1-01 Task 2. Mechanism matches `:123` and strict cancel renders. |
| H2 | Closed in 06.1-01 Task 3. Only two `cv_tag` exclusions exist; both are owned. |
| H3 | Closed in 06.1-01 Task 3, before Plan 02. Equality test stays strict. |
| A1 | Closed. Construction validates explicit tags; legacy `None`/`button` stays quiet; Plan 03 documents that split. |
| A2 | Closed. Matrix is retained on purpose in 06.1-01 Task 1. |
| A3 | Closed in 06.1-03 Task 1. |
| A4 | Closed. Both docstring sites are named. |
| A5 | Closed. Form plus `button-id-reset`, not href. |
| A6 | Closed. E365 is the fourth freeze input. |
| A7 | Closed. New cases go in the cancel `describe` before `:571`. |
| A8 | Closed. Page tests use `override_settings`; cache reset is real. |
| A9 | Explicitly deferred. `ROADMAP.md:332` remains. Not a product invariant failure. |
| A10 | Closed in 06.1-01 Task 2; 06.1-03 must not revert `:152-153`. |

No prior HIGH still fails as a plan invariant. The new MEDIUM is the theme recipe versus `viewset.js`, not a reopened H1–H3. Overall risk is **MEDIUM** until that fence is required to omit the cancel marker; the rendering and registry plans themselves are LOW.
