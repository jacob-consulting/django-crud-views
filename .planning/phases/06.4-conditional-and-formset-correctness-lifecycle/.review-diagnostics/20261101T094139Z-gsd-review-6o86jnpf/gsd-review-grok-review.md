I'll review the ten current plans against source and the prior H1–H3/A-item ledger, read-only.
Source confirms the unfixed defects. Next I’ll trace the save, fragment, and fixture paths the plans claim to close.
The same-value disabled case is the one claimed closure that may not be observable. I'll check that against jsdom before signing it off.
## 06.4-01

Summary: Exact owning-form checkbox identity is an executable repair of the suffix lookup in `src/crud_views/static/crud_views/js/toggle.js:15-20` and the unprefixed marker in `src/crud_views/lib/conditional/layout.py:29`. Wrapper binding is assigned to `FormSet.init` and `XFormSet.cv_toggle_field` (`src/crud_views/templates/crud_views/formsets/formsets.html:4-5`).

Strengths: The tracer binds rendered HTML through shipped `toggle.js` and real `FormData` into the intended ModelForm. Ambiguity stays local, and the new Pydantic field is declared rather than assigned ad hoc.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Automatic page/modal startup is explicitly deferred to 05, which depends on this plan.

## 06.4-02

Summary: H1 is closed. `XFormSet.save` skips unchanged forms at `src/crud_views/lib/formsets/render_tree.py:256-260`, and `FileField.has_changed` is false when no upload is present (Django `forms/fields.py:703-704`). The plan forces that path with `_cv_conditional_requires_save` after validation, and applies `False` through `save_form_data` before `ModelForm._post_clean`. Django `ModelForm.save` does not reconstruct the instance (`forms/models.py:558-579`), so a pre-validation clear survives `commit=False`.

Strengths: File/image proof uses the real tree save, asserts `has_changed()` is false, and keeps disabled fields and blank extras out of the signal. A01 storage is isolated to `tmp_path` / `MEDIA_ROOT`, with teardown outside the deletion spy. `None` remains no-change and `False` clears (`db/models/fields/files.py:360-368`).

Concerns: None.

Suggestions: None.

Risk Assessment: Low for the remedy. Persistence is still unlanded, which is expected.

## 06.4-03

Summary: A02 is closed. Checks currently reuse the main form namespace for every formset (`src/crud_views/checks.py:164-176`). Task 03-01 recomputes declared and injected names per inline form class and tests crossed main/inline E311/E312 cases.

Strengths: The same resolver feeds static E312 and runtime `ImproperlyConfigured`. Request-dependent forms are not constructed at startup. Inherited nonfield and model invariants stay authoritative.

Concerns: LOW — retiring W320 will fail existing assertions at `tests/test1/test_conditional_checks.py:298` and `:373`. The verify command forces an update, so this does not block the remedy.

Suggestions: Name those two assertions as expected edits when replacing W320 with E312.

Risk Assessment: Low.

## 06.4-04

Summary: H3 is closed. `FormSet.init` always passes `formset` and `parent_form` (`src/crud_views/lib/formsets/formsets.py:148-160`); Django `BaseInlineFormSet` does not accept them, while package `InlineFormSet.__init__` does (`src/crud_views/lib/formsets/inline_formset.py:21-43`). The plan owns a test-local route fixture, a direct subclass that strips those kwargs, a helper, and a policy-call spy so a constructor `TypeError` cannot masquerade as a rejection.

Strengths: Policy sits in the active `XFormSet` validity traversal, not `InlineFormSet.clean`, and both passes of `all_valid` are preserved (`src/crud_views/lib/formsets/formsets.py:354-369`). H1’s save signal is retained. Invalid IDs share one generic error and use `get_queryset()`.

Concerns: None.

Suggestions: Pass `edit_only` to `inlineformset_factory`; `FormSet.edit_only` is only a property (`formsets.py:112-113`).

Risk Assessment: Low. The positive GET/POST gate makes a missing factory flag fail the task.

## 06.4-05

Summary: A04 is closed: resync is a post-default macrotask, including a later listener’s `preventDefault()`. A10 is closed: Chromium records a second `disabled = true` as an attribute mutation even when the value is already empty, so the mandated observer can see it if library writes are disconnected.

Strengths: Composition is baseline OR inactive ancestors, management inputs are excluded, and buttons are added to the set that `toggle.js:26-30` currently skips. Focus moves only when hiding strands the active control, and modal replacement ownership stays in `modal.js`.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. The observer must actually disconnect around its own writes; the acceptance tests require that.

## 06.4-06

Summary: A11 and A12 stay closed. Stock Add is unconditional (`src/crud_views/templates/crud_views/formsets/control.html:18-22`), and lookups interpolate prefixes (`src/crud_views/static/crud_views/js/formset.js:130`, `:165`, `:173`). The plan renders the shipped template in pytest and switches dynamic lookups to owning-form attribute equality, including a punctuation prefix.

Strengths: One controller per form, capability checks at activation, and modal submit must honor an earlier `defaultPrevented` (`src/crud_views/static/crud_views/js/modal.js:227-232`). The jQuery `.each` false return at `formset.js:600-610` is called out so a failed reorder cannot still return true.

Concerns: None.

Suggestions: Read `defaultPrevented` before this listener’s own `preventDefault()`.

Risk Assessment: Low.

## 06.4-07

Summary: H2 is closed. Opening uses `render_rows_only` and closing uses absent `end_at_rows` (`src/crud_views/templates/crud_views/formsets/formset.html:4`, `:56`; `src/crud_views/lib/formsets/render_tree.py:102`). The plan requires a raw tag stack before parsing, a stray-close negative control, and parsed POST proof. `get_template` still passes `index=0` (`formsets.py:513`); the selected child’s declaration index replaces it, and the stale note at `formsets.py:417-418` is updated.

Strengths: Denied-editor and forged-ancestry assertions stay in the same case. Deeper non-first and UUID/unsaved parents are included without changing request keys.

Concerns: LOW — `06.4-07-PLAN.md:100` says align the close with the opening predicate, “not x_formset.render_rows_only”, while the ledger says align both with `render_rows_only`. The raw-balance criteria reject a wrong predicate, so this is not an open H2.

Suggestions: Change the close condition to `{% if not x_formset.render_rows_only %}`.

Risk Assessment: Low.

## 06.4-08

Summary: Browser evidence names the H1, H2, A04, and A10 assertions for both themes. A06 matches `tests/browser/modal-focus.cjs:12` and `:81-83`. A07 uses port 8144 instead of 8143 (`modal-focus.cjs:21`) and refuses an occupied port.

Strengths: The inline file case must reach `XFormSet.save` with `has_changed()` false. Raw fragment HTML is checked before insertion. Reset uses a real `type=reset` click and keyboard activation.

Concerns: None.

Suggestions: None.

Risk Assessment: Medium only because the fixture is new and unrun, not because a required case is unspecified.

## 06.4-09

Summary: A08 and A13 are preserved. The stale universal-None/W320 comment is at `examples/bootstrap5/conditional/models.py:8` and is in this plan’s files. `XFormSet.data.pk` is the grammar (`render_tree.py:188`); `XForm.data.pk` is `str(self.parent.pk)` (`render_tree.py:67`), the enum spelling. The plan documents and executes both.

Strengths: Breaking notes are paired with `docs/migrating-1.0.md`. The first-child limitation is removed only after 07/08 evidence. A8 and internal render-tree classes stay out of the public inventory.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Docs are gated on the prior evidence plans.

## 06.4-10

Summary: Final evidence requires the plan 08 assertion IDs, the inline tree-save regressions, native-subclass HTTP cases, and the Django-rendered control tests on the three cached Django series. Browser runners are sequential, 8144 then 8143, with owned-process cleanup.

Strengths: A19 is reconciled only after a successful round trip. A8, A25, and broader Guardian exclusions stay out. The checker is tested by corrupting required assertions and hashes.

Concerns: None.

Suggestions: None.

Risk Assessment: Medium operationally, because the gate is large. The required proof is specified.

## Prior-item closure ledger

| Item | Verdict |
|---|---|
| H1 | Closed. Plans 02, 04, 08, and 10 force `XFormSet.save` when conditional resolution differs and `has_changed()` is false, including file/image and browser evidence. |
| H2 | Closed. Plan 07 repairs the close unconditionally and proves raw balance before parse; 08 and 10 require that assertion. Wording at `06.4-07-PLAN.md:100` is only a LOW clarity note. |
| H3 | Closed. Plan 04 owns registered routes, `edit_only` declarations, and `PolicyNativeInlineFormSet` that accepts `formset`/`parent_form` without package `clean`. |
| A01 | Closed in 02-02 (`MEDIA_ROOT`, isolated storage, teardown outside the spy). |
| A02 | Closed in 03-01 (per-form namespaces and crossed E311/E312 cases). |
| A03 | No open 6.4 item. No regression. |
| A04 | Closed in 05-02, 08-02, and 10-01 (macrotask plus click/keyboard reset and later cancellation). |
| A05 | No open 6.4 item. No regression. |
| A06 | Closed in 08-01 (`CV_FOCUS_*` honored, invalid overrides fail, paths/versions recorded). |
| A07 | Closed in 08-01 and 10-01 (8144 vs 8143, sequential owned processes). |
| A08 | Preserved in 09-01. No regression. |
| A09 | No open 6.4 item. No regression. |
| A10 | Closed. Chromium emits an attribute record for a second `disabled = true`; 05 disconnects around library writes, and 08/10 name the assertions. |
| A11 | Closed in 06-01 (Django-rendered `control.html` plus pytest). |
| A12 | Preserved in 06-01 (exact attribute equality, punctuation prefix). No regression. |
| A13 | Preserved in 09-01 (grammar vs enum spelling vs request pk). No regression. |

## Unresolved concerns

No unresolved HIGH. No unresolved actionable prior item. The only fresh note is LOW: `06.4-07-PLAN.md:100` should say the closing predicate is `{% if not x_formset.render_rows_only %}`, matching the opening tag and the ledger. Acceptance criteria already reject a wrong predicate, so no further revision is required.
