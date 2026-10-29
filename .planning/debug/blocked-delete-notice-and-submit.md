---
status: diagnosed
trigger: "blocked-delete-notice-and-submit: When deletion is blocked by protected relationships (has_protected_objects), the confirmation page shows a complete generic notice with no dangling colon even when every protected label is hidden, the confirm/submit control cannot submit a doomed delete, and a confirmed POST on a protected object returns the documented protection response instead of a ProtectedError 500 (review WR-02 / UI-REVIEW findings 1 and 4), for core and Guardian delete views."
created: 2026-10-29T14:20:00Z
updated: 2026-10-29T14:50:00Z
goal: find_root_cause_only
---

## Current Focus

bug_class: Bohrbug (deterministic; reproduces every request; SBFL skipped - the failing behavior is pinned as PASSING tests, so the spectrum has no failing test to rank)
hypothesis: CONFIRMED - blocked state is a display-only context flag (has_protected_objects, preview-branch only) that no control-flow consumer reads; copy, submit and POST each lack a blocked-state branch
test: scratch repro (scratchpad/test_repro_blocked_delete.py) + code/history reading
expecting: n/a (diagnosed)
next_action: return ROOT CAUSE FOUND to orchestrator (goal: find_root_cause_only); fixer revises the pins listed in Evidence 14:47
candidate_causes:
  - "code: DeleteView.post ignores has_protected_objects / does not catch ProtectedError|RestrictedError (delete.py:224-247)"
  - "code/template: related_objects.html:5 single colon heading for list and empty states; view_delete.content.html renders form unconditionally"
  - "config: has_protected_objects only computed when cv_show_related_objects=True (default False) - default config has no blocked signal at all"
  - "process/data (plan decision): 06.2-01 ledger rejected catching ProtectedError and pinned the 500 in 3 tests + docs"
and_gate: "yes - the 500 needs both (a) post() not consulting any blocked state AND (b) no exception mapping; the misleading UI needs both (c) a heading written for the list case AND (d) no blocked-state gate on the form. Common upstream: blocked state lives only in template context, inside the preview branch."

## Symptoms

expected: A single complete red notice explains deletion is blocked (no trailing colon when the label list is empty); the Confirm checkbox / Delete submit cannot submit when has_protected_objects is true; a confirmed POST on an object with database PROTECT relations returns the package's documented protection response (the existing custom-protection path is 200, or 422 in the modal) instead of an uncaught ProtectedError (500). Core and Guardian delete views, full page and modal.
actual: Alert reads 'Deletion is blocked by protected relationships:' with nothing after it when all labels are hidden (alert_data() picks the text-body variant with empty text); confirm checkbox and Delete button stay enabled; submitting raises ProtectedError -> 500. Plan 06.2-01 deliberately preserved the ProtectedError-on-POST lifecycle and pinned it with test_database_protect_post_raises_and_keeps_storage.
errors: django.db.models.deletion.ProtectedError on confirmed POST
reproduction: UAT Test 3. User with delete permission on a Publisher but no view permission on its protected Contract: core /publisher_cascade/<pk>/delete/ (or Guardian cascade route without M2M).
started: Discovered during UI review / code review / UAT of phase 06.2

## Eliminated

- hypothesis: alert_data() mis-selects the body variant (bug in the alert helper)
  evidence: messages.py:43-44 documents and implements LIST_BODY if items else TEXT_BODY; with items==[] and text=="" it renders exactly what it was asked to. The caller (related_objects.html:5) supplies list-variant copy with no text for the empty case.
  timestamp: 2026-10-29T14:40:00Z

- hypothesis: Guardian (or polymorphic) has its own delete post/template path that diverges from core
  evidence: GuardianDeleteViewPermissionRequired overrides only cv_filter_related_objects; PolymorphicDeleteView is `pass`. Reproduction shows identical alert/confirm/submit markup and 500 for Guardian.
  timestamp: 2026-10-29T14:40:00Z

- hypothesis: disabling the Delete submit requires a new frozen form-leaf key (FORM_LEAF_KEYS change before Phase 7)
  evidence: extra kwargs flow through cv_attrs -> cv_flat_attrs; disabled=True is emitted and pinned by test_form_button_docs.py:459-471.
  timestamp: 2026-10-29T14:42:00Z

- hypothesis: the modal path already maps database PROTECT to 422
  evidence: scratch repro with X-CV-Modal: true -> 500; 422 is only produced for cv_check_delete_protection errors and invalid forms.
  timestamp: 2026-10-29T14:36:00Z

## Evidence

- timestamp: 2026-10-29T14:22:00Z
  checked: Phase 0 knowledge base (.planning/debug/knowledge-base.md)
  found: does not exist; no prior resolved sessions. Only other active session is guardian-delete-preview-m2m-through-500 (CR-01, separate gap).
  implication: no known-pattern candidate; proceed normally.

- timestamp: 2026-10-29T14:24:00Z
  checked: src/crud_views/lib/views/delete.py get_context_data (197-219) and post (224-244)
  found: has_protected_objects = bool(related.protected) is computed ONLY inside `if self.cv_show_related_objects:` (202-205). post() consults only context["delete_protection_errors"] (from cv_check_delete_protection(), default []), never has_protected_objects, then calls cv_form_valid_process -> cv_form_valid -> self.object.delete() (247), which raises ProtectedError uncaught.
  implication: (a) write path ignores the blocked state the read path already computed; (b) when cv_show_related_objects=False there is no blocked-state signal at all, so a PROTECT-only object still 500s on POST even after a has_protected_objects-based fix.

- timestamp: 2026-10-29T14:25:00Z
  checked: src/crud_views/lib/messages.py alert_data (20-54), tags/alert.html, snippets/alert/text.html, list.html
  found: body_template = LIST_BODY if items else TEXT_BODY. related_objects.html:5 calls cv_alert "error" heading=_("Deletion is blocked by protected relationships:") items=protected_objects with no text=. When protected_objects==[] (all hidden), TEXT_BODY renders alert.text == "" -> markup is `<strong>Deletion is blocked by protected relationships:</strong>` + empty body.
  implication: dangling colon is a template-copy defect in related_objects.html (heading literal written for the list variant, reused for the empty case); alert_data() itself behaves as designed.

- timestamp: 2026-10-29T14:26:00Z
  checked: view_delete.content.html, crispy/form.py CrispyDeleteForm (118-146)
  found: when delete_protection_errors is truthy the template renders ONLY protection_errors.html (no form). When only has_protected_objects is true, the template still includes related_objects.html AND unconditionally renders <form> + {% cv_render_form %}. CrispyDeleteForm.helper always builds Row(Column4("confirm")) + FormActions(Submit delete, cancel Button); no input reads view/context blocked state. No context key or template block exists for a disabled/blocked state.
  implication: the custom-protection path already has a "no form" UX; the database-PROTECT path was never wired to it. Nothing in form or template consumes has_protected_objects for the submit control.

- timestamp: 2026-10-29T14:27:00Z
  checked: Guardian GuardianDeleteViewPermissionRequired (guardian/lib/views.py:39-100), PolymorphicDeleteView (polymorphic/lib/delete.py)
  found: neither overrides post(), get_context_data(), cv_check_delete_protection() or templates; Guardian overrides only cv_filter_related_objects. Both inherit core DeleteView post/get_context_data/template.
  implication: a single fix in core DeleteView (post + get_context_data + template/form) covers core, Guardian and polymorphic; Guardian label filtering (CR-01 area) is orthogonal.

- timestamp: 2026-10-29T14:28:00Z
  checked: 06.2-CONTEXT.md D-07/D-08, 06.2-01-PLAN.md (line 101, 103, 119, 186, 196), 06.2-01-SUMMARY.md (166, 244), 06.2-ACCEPTANCE.md (116, 230), 06.2-REVIEW.md WR-02, 06.2-UI-REVIEW.md findings 1/4
  found: D-07: "Show one generic blocked-deletion notice, plus only protected-object labels the user may view. Do not emit one placeholder for each hidden object." D-08: "The generic notice must remain visible even when every protected-object label is hidden. Filtering display data must never make deletion appear unblocked or weaken actual deletion protection." Plan 01 alternatives ledger line 196: "Catch database ProtectedError as a new response | Rejected as a lifecycle change outside this phase; 01-01/02 pin existing exception and storage preservation." A01 risk row (186) and task actions (103, 119) pin pytest.raises(ProtectedError). ACCEPTANCE 116 lists test_database_protect_post_raises_and_keeps_storage as the evidence for the retained contract; ACCEPTANCE 230 documents the 500 as retained on purpose.
  implication: no locked decision (D-01..D-14) mandates the 500; D-07 forbids only per-object placeholders, so one generic explanatory sentence is allowed; D-08 arguably requires the blocked state not look deletable. The 500 is a plan-01-level deferral (ledger "Rejected ... outside this phase"), pinned by tests and documented in ACCEPTANCE — those are what the fix must revise.

- timestamp: 2026-10-29T14:34:00Z
  checked: Pinned tests: uv run pytest tests/test1/test_delete.py tests/test1/test_guardian_delete.py tests/test1/test_authorization_matrix.py::test_granted_database_protect_delete_reraises
  found: 51 passed. Pins of the 500 contract: test_delete.py::test_database_protect_post_raises_and_keeps_storage (L246-259), test_guardian_delete.py::test_guardian_database_protect_post_raises_and_keeps_storage (L315-330), test_authorization_matrix.py::test_granted_database_protect_delete_reraises (L727-741, parametrized core/strict/global). Matrix MxDelete (L151-162) does NOT set cv_show_related_objects (defaults False) and sets cv_modal=True. BLOCKED_HEADING constant with trailing colon is asserted in test_delete.py:142 and test_guardian_delete.py:127.
  implication: three test pins must be revised, and the matrix pin covers the cv_show_related_objects=False path, which has_protected_objects never reaches.

- timestamp: 2026-10-29T14:36:00Z
  checked: Scratch reproduction (scratchpad/test_repro_blocked_delete.py) with production-like Client(raise_request_exception=False), Publisher + PROTECT Contract, user lacking view_contract
  found: |
    CORE GET 200, danger alert inner = '<i ...></i><strong>Deletion is blocked by protected relationships:</strong> ' (no body);
    confirm = <input type="checkbox" name="confirm" ... required id="id_confirm"> (no disabled);
    submit = <button type="submit" name="delete" value="Delete" ... class="btn btn-primary"> (no disabled);
    CORE POST full page -> 500; CORE POST modal -> 500 (not 422);
    cv_show_related_objects=False: GET has no has_protected_objects key, no alert, form present; POST -> 500;
    GUARDIAN GET identical alert/confirm/submit; GUARDIAN POST -> 500;
    differential CUSTOM protection (cv_check_delete_protection -> ['Custom block.']): GET renders protection_errors alert and NO confirm/submit; POST full 200, modal 422.
  implication: all three symptoms confirmed for core and Guardian, full page and modal. The documented 200/422 protection response exists only for cv_check_delete_protection; database PROTECT never reaches it.

- timestamp: 2026-10-29T14:42:00Z
  checked: crispy/buttons.py _TableClassMixin (cv_attrs passthrough), lib/view/button_data.py FORM_LEAF_KEYS + _form_button_data, tests/test1/test_form_button_docs.py:459-471, tags/button/form.html
  found: FORM_LEAF_KEYS has no cv_disabled, but any extra kwarg (e.g. disabled=True) flows _cv_attrs -> cv_attrs -> flatatt -> cv_flat_attrs and is emitted on <button>; a disabled cancel stays a native disabled button (pinned test). CrispyDeleteForm has self.cv_view; helper is a property evaluated at render time (after get_context_data), so view-level blocked state set during get_context_data is visible to get_delete_button_kwargs().
  implication: a disabled Delete submit needs NO new frozen form-leaf key; a theme overriding tags/button/form.html already receives `disabled` via cv_flat_attrs. The missing seam is a view/context-level blocked flag that exists independently of cv_show_related_objects.

- timestamp: 2026-10-29T14:44:00Z
  checked: Django 6.1.2 django.contrib.admin.utils.NestedObjects.collect; ProtectedError/RestrictedError MRO
  found: NestedObjects catches both ProtectedError and RestrictedError and adds both to .protected; both subclass IntegrityError.
  implication: has_protected_objects is also True for on_delete=RESTRICT, whose POST raises RestrictedError (same 500 class). A write-path fix must cover both exceptions.

- timestamp: 2026-10-29T14:45:00Z
  checked: src/crud_views/static/crud_views/js/modal.js cvModalSubmit (75-104)
  found: modal swaps content only on 422 (or follows X-CV-Redirect); any other status (incl. 500) -> location.assign(fallback).
  implication: modal users today get a silent full-page reload to the same blocked page; returning 422 on a blocked POST plugs into the existing modal contract with no JS change.

- timestamp: 2026-10-29T14:46:00Z
  checked: git show eda7018 (06.2-01 GREEN) for related_objects.html and view_delete.content.html
  found: before eda7018 the notice was gated `{% if protected_objects %}` on the UNFILTERED list, so the colon heading was always followed by a non-empty <ul>. eda7018 changed only the guard to has_protected_objects; heading literal unchanged.
  implication: the dangling colon is a regression introduced by 06.2-01: it made the empty-list state reachable (D-08) without giving that state its own copy. The enabled submit and the 500 predate the phase; the phase made the block visible and pinned the 500.

- timestamp: 2026-10-29T14:47:00Z
  checked: every pin of the heading string and of the 500 (grep tests/ docs/ src/ .planning/)
  found: |
    Heading "Deletion is blocked by protected relationships:" pinned in tests/test1/test_delete.py:142, tests/test1/test_guardian_delete.py:127, tests/test1/test_authorization_templates.py:42 (BLOCKED_HEADING), src/crud_views/locale/de/LC_MESSAGES/django.po:225, docs/reference/theme.md:345-347 (copyable recipe), docs/reference/delete_view.md:174.
    500 contract pinned/documented in tests/test1/test_delete.py:246-259, tests/test1/test_guardian_delete.py:315-330, tests/test1/test_authorization_matrix.py:727-741; docs/reference/delete_view.md:186-187 and 280-284; 06.2-ACCEPTANCE.md:116 and 230 (open item) and settled contract #3 wording ("With cv_show_related_objects ..."); 06.2-01-PLAN.md:196 ledger + A01 (186).
  implication: this is the complete revision list the fix must touch.

## Resolution

root_cause: |
  One structural cause, three conditions (AND-gate: yes). The blocked-deletion state exists only as a display-only
  context flag, `has_protected_objects`, computed inside the `cv_show_related_objects` preview branch of
  DeleteView.get_context_data (delete.py:202-205). No control-flow consumer reads it:
  (1) Copy: related_objects.html:5 reuses one heading written for the list variant ("...relationships:") for the
      all-hidden case that eda7018 (06.2-01) made reachable. With items == [] alert_data() correctly selects TEXT_BODY
      with empty text, so the alert is heading + dangling colon + nothing.
  (2) Submit: view_delete.content.html:12-18 renders the confirm form unconditionally outside the
      delete_protection_errors branch, and CrispyDeleteForm.helper (crispy/form.py:136-146) never disables
      confirm/delete. No view-level blocked state reaches the form.
  (3) POST 500: DeleteView.post (delete.py:224-244) treats only cv_check_delete_protection() errors as protection.
      It ignores has_protected_objects and lets cv_form_valid -> self.object.delete() raise ProtectedError (or
      RestrictedError for RESTRICT, also in NestedObjects.protected) through cv_form_valid_process. Result: 500 on full
      page AND modal (modal.js then silently reloads). Worse in the DEFAULT config (cv_show_related_objects=False):
      no flag, no notice, enabled form, 500.
  Why it was kept: not a locked CONTEXT decision. It is a plan-level deferral in 06.2-01-PLAN.md (alternatives ledger
  line 196 "Catch database ProtectedError as a new response | Rejected as a lifecycle change outside this phase", risk
  A01 line 186, task actions 103/119). It is pinned by test_delete.py::test_database_protect_post_raises_and_keeps_storage,
  test_guardian_delete.py::test_guardian_database_protect_post_raises_and_keeps_storage and
  test_authorization_matrix.py::test_granted_database_protect_delete_reraises, and documented in delete_view.md:186-187,
  280-284 and ACCEPTANCE 116/230.
  Locked decisions bearing on the fix: D-07 forbids only per-hidden-object placeholders, so one generic explanatory
  sentence is allowed. D-08 says the notice must survive full hiding and display filtering must never make deletion
  appear unblocked; today's enabled submit contradicts "appear". D-12 says server enforcement belongs in the library,
  not hidden controls, so disabling the button alone is insufficient and post() must enforce. D-14: pair the
  CHANGELOG entry with migrating-1.0.md.
fix: (diagnosis only — not applied)
verification: (diagnosis only)
files_changed: []
