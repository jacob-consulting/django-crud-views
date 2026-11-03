# Cross-artifact fact drift — Phase 06.4 cycle 2



Status seam: `{"verdict": "uncheckable", "phase": "06.4", "stateStatus": "Ready to plan", "roadmapStatus": "Planning; initial draft", "stateRank": 0, "roadmapRank": null, "authority": "STATE.md"}`. Status vocabulary mismatch is UNCHECKABLE, not consistent and not a contradiction. STATE is authority.



## Requirements

ROADMAP authority `.planning/ROADMAP.md:539`: **Requirements**: COND-01, COND-02, COND-03, COND-04, COND-05, FSET-01, FSET-02, FSET-03, LIFE-01, LIFE-02, AUTH-02 (A19 handoff only).

The union of current plan requirement references matches all eleven IDs; AUTH-02 remains limited to A19. No contradiction.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-03-PLAN.md:14`: requirements: ["COND-05"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-10-PLAN.md:16`: requirements: ["COND-01","COND-02","COND-03","COND-04","COND-05","FSET-01","FSET-02","FSET-03","LIFE-01","LIFE-02","AUTH-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md:16`: requirements: ["FSET-01","FSET-02","COND-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-07-PLAN.md:13`: requirements: ["FSET-03","AUTH-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-PLAN.md:17`: requirements: ["COND-01","COND-02","COND-03","COND-04","FSET-01","FSET-02","FSET-03","LIFE-01"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md:14`: requirements: ["COND-04","COND-05"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:14`: requirements: ["FSET-01","LIFE-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:18`: requirements: ["COND-01","FSET-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:11`: requirements: ["COND-02","COND-03","FSET-02"]

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md:17`: requirements: ["COND-01","COND-04","COND-05","FSET-01","FSET-02","FSET-03","LIFE-02"]



## Success facts

ROADMAP is authority; each named fact matches the corresponding plan truth. Added detail is not drift.

- `.planning/ROADMAP.md:548`:   1. A1: Each conditional group binds to its own intended toggle across sibling/nested rows, shared suffixes,

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:26`: - "A prefixed rendered group follows only its exact checkbox in the same form and submitted data reaches the intended model row." — no same-fact contradiction.

- `.planning/ROADMAP.md:550`:   2. A2/A3: Baseline disabled reasons and all enclosing groups compose correctly in both nesting orders. Native

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:19`: - "Effective disabled state is independent baseline OR any inactive bound ancestor; management inputs receive no conditional owner." — no same-fact contradiction.

- `.planning/ROADMAP.md:552`:   3. A4: Inactive supported fields clear with correct persistence semantics, including existing FileField references

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md:24`: - "File references and M2M relations use Django persistence semantics; explicit False, empty collections, empty strings and None retain distinct meanings." — no same-fact contradiction.

- `.planning/ROADMAP.md:555`:   4. A5: Active `edit_only` formsets cannot create rows through forged extras, including custom control templates;

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:22`: - "Active edit-only extras with data yield a formset validation error before main/sibling/nested save hooks." — no same-fact contradiction.

- `.planning/ROADMAP.md:558`:   5. A6/A7: Formsets and toggles initialize automatically and idempotently on initial load, modal load/422 replacement

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md:24`: - "Each form has one scoped controller; repeated initialization, modal replacement and nested insertion preserve independent forms with identical prefixes." — no same-fact contradiction.

- `.planning/ROADMAP.md:562`:   6. Stock and minimal non-Bootstrap crispy/group/formset templates pass lifecycle and keyboard/focus acceptance,

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-PLAN.md:26`: - "Keyboard/focus and native reset behavior hold in stock Bootstrap and minimal non-Bootstrap rendering with two forms." — no same-fact contradiction.

- `.planning/ROADMAP.md:566`:   7. Document the usable formset template projection and any changed identity/root/visibility hooks for Phase 7.

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md:28`: - "Every Breaking note has matching migration guidance and new public names reach Phase 7." — no same-fact contradiction.



## Authoritative context decisions

CONTEXT D-01–D-19 are authority. Compared with current actions; Discretion and Deferred Ideas were excluded.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:25`: - **D-01:** Corrected toggle identity may require immediate migration of existing template overrides before 1.0.

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:112`: <action>Per D-01–D-03 emit form.add_prefix(self.toggle_field) as cv_toggle_field, retain cv_toggle_css/cv_toggle_legend/cv_toggle_inner and escaped template attributes, and resolve equality among checkbox controls owned by the group's nearest actual form. Do not concatenate an unsafe selector from a field name. Expose cv.initCon … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:28`: - **D-02:** If outdated custom markup leaves multiple possible toggle matches, do not guess. Leave the affected

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:112`: <action>Per D-01–D-03 emit form.add_prefix(self.toggle_field) as cv_toggle_field, retain cv_toggle_css/cv_toggle_legend/cv_toggle_inner and escaped template attributes, and resolve equality among checkbox controls owned by the group's nearest actual form. Do not concatenate an unsafe selector from a field name. Expose cv.initCon … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:31`: - **D-03:** Isolate ambiguous-binding handling to the affected group. Correctly bound groups, including those in

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:112`: <action>Per D-01–D-03 emit form.add_prefix(self.toggle_field) as cv_toggle_field, retain cv_toggle_css/cv_toggle_legend/cv_toggle_inner and escaped template attributes, and resolve equality among checkbox controls owned by the group's nearest actual form. Do not concatenate an unsafe selector from a field name. Expose cv.initCon … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:36`: - **D-04:** Use immediate native visibility for 1.0. No theme visibility/animation adapter is required in this phase;

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:78`: <action>Per D-02–D-04,D-06,D-07,D-14 implement per-control baseline ownership plus all currently inactive bound ancestor groups. Prove the observation mechanism first in focused failing tests, then ship it: observe disabled attribute changes with oldValue, drain pending external records before synchronous resync, disconnect only … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:38`: - **D-05:** When hiding a group would strand focus inside it, move focus to its controlling checkbox. If necessary,

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:92`: <action>Per D-05,D-13–D-15,D-19 wire form-scoped native reset once; schedule synchronization as a task/macrotask (for example setTimeout(..., 0)), after the browser's native default reset algorithm, and inspect event.defaultPrevented there, including cancellation by a later listener. A microtask-only callback is insufficient for … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:41`: - **D-06:** Preserve unsaved entries across off→on toggles before submission. Do not clear values merely because

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:78`: <action>Per D-02–D-04,D-06,D-07,D-14 implement per-control baseline ownership plus all currently inactive bound ancestor groups. Prove the observation mechanism first in focused failing tests, then ship it: observe disabled attribute changes with oldValue, drain pending external records before synchronous resync, disconnect only … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:43`: - **D-07:** Disable action buttons inside inactive groups along with their data fields, including formset Add,

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md:99`: <action>Per D-07,D-11,D-13,D-14,D-17,D-18 expose cv.initFormsets(root = document), supporting Document/Element/DocumentFragment, root matches and owning-form lookup from a row/control root. Keep jQuery. Track one private controller per form, scope XBase/controller/row/management selections and insertion to it, and use idempotent … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:49`: - **D-08:** Provide automatic field-aware clearing defaults for supported field types. Honor explicit

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md:96`: <action>Per D-08–D-10 implement one internal resolver shared by runtime and the later check task. Resolve trusted Field.disabled before suppression/clearing/explicit override. Use membership in empty_values, not truthiness. For automatic supported standard form/model pairs choose nullable text=None, blank non-null text='', non-n … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:52`: - **D-09:** Preserve fields explicitly disabled on the server even when their conditional group is off. Switching

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md:96`: <action>Per D-08–D-10 implement one internal resolver shared by runtime and the later check task. Resolve trusted Field.disabled before suppression/clearing/explicit override. Use membership in empty_values, not truthiness. For automatic supported standard form/model pairs choose nullable text=None, blank non-null text='', non-n … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:55`: - **D-10:** If no supported automatic clearing value exists and no explicit value is supplied, raise a descriptive

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-03-PLAN.md:86`: <action>Per D-08,D-10 extend the existing _ConditionalFindings/check_conditional traversal to inspect main form base_fields and the form classes reachable from all FormSet declarations, including custom native BaseInlineFormSet subclasses and descendants. Reuse resolve_conditional_empty_value; never construct arbitrary request-d … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:61`: - **D-11:** A nonblank extra row submitted to an active edit-only formset rejects the whole submission with a

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:90`: <action>Per D-11,D-18 install mandatory policy enforcement in the active XFormSet runtime validity traversal, preserving normal instance.is_valid/custom clean and the two-pass order-independent all_valid contract. Do not rely on the package InlineFormSet.clean, because declarations accept native BaseInlineFormSet subclasses. Add … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:64`: - **D-12:** A submitted existing row with a missing ID or an ID outside the formset's authorized queryset rejects

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:90`: <action>Per D-11,D-18 install mandatory policy enforcement in the active XFormSet runtime validity traversal, preserving normal instance.is_valid/custom clean and the two-pass order-independent all_valid contract. Do not rely on the package InlineFormSet.clean, because declarations accept native BaseInlineFormSet subclasses. Add … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:68`: - **D-13:** Provide a documented, repeat-safe initializer for a supplied content root, usable by themes inserting

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md:99`: <action>Per D-07,D-11,D-13,D-14,D-17,D-18 expose cv.initFormsets(root = document), supporting Document/Element/DocumentFragment, root matches and owning-form lookup from a row/control root. Keep jQuery. Track one private controller per form, scope XBase/controller/row/management selections and insertion to it, and use idempotent … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:72`: - **D-14:** Repeated initialization resynchronizes current state: retry unresolved bindings and update visibility

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:92`: <action>Per D-05,D-13–D-15,D-19 wire form-scoped native reset once; schedule synchronization as a task/macrotask (for example setTimeout(..., 0)), after the browser's native default reset algorithm, and inspect event.defaultPrevented there, including cancellation by a later listener. A microtask-only callback is insufficient for … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:79`: - **D-15:** Retain all A1–A7 roadmap acceptance: sibling/nested row identities, shared suffixes, prefixed and multiple

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-PLAN.md:119`: <action>Per D-05,D-11–D-19 create a permanent runner modeled on modal-focus.cjs's cached Playwright/Chromium discovery, own-process cleanup and occupied-port failure. Addresses A06: honor CV_FOCUS_NODE, CV_FOCUS_PYTHON, CV_FOCUS_PLAYWRIGHT and CV_FOCUS_CHROMIUM before the existing runtime-manifest/cached defaults, including Node … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:85`: - **D-16:** Repair A19's non-first sibling child-fragment indexing and prove rendered-prefix/management/POST

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-07-PLAN.md:86`: <action>Per D-16,D-17 derive the selected nested FormSet's index from its parent's ordered children declaration in get_template, using zero only for a top-level declaration. Do not change _cv_fragment_pk, ancestry grammar, incoming template/pk/num/formset_parent_prefix_key or {html, rows}. Addresses review H2: replace the stale  … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:88`: - **D-17:** Preserve fragment request coordinates and `{html, rows}` responses, row-added event detail

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md:102`: <action>Per D-01,D-08–D-10,D-13,D-15–D-19 document exact bound cv_toggle_field/marker values, console ambiguity diagnostic/isolation and migration from unprefixed copied templates; immediate native visibility; supported native action button hooks; root accepted types and cv.initConditional/cv.initFormsets repeat/late-element usa … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:91`: - **D-18:** Keep jQuery in this phase; the #210 port remains deferred. Preserve server authorization, parent denial,

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:90`: <action>Per D-11,D-18 install mandatory policy enforcement in the active XFormSet runtime validity traversal, preserving normal instance.is_valid/custom clean and the two-pass order-independent all_valid contract. Do not rely on the package InlineFormSet.clean, because declarations accept native BaseInlineFormSet subclasses. Add … No contradictory use; reviewed full action.

- `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md:94`: - **D-19:** Preserve completed form-leaf, label-mode, escaping and cancel-link contracts and the accepted modal

  ↔ `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md:102`: <action>Per D-01,D-08–D-10,D-13,D-15–D-19 document exact bound cv_toggle_field/marker values, console ambiguity diagnostic/isolation and migration from unprefixed copied templates; immediate native visibility; supported native action button hooks; root accepted types and cv.initConditional/cv.initFormsets repeat/late-element usa … No contradictory use; reviewed full action.



No judgment-axis same-fact contradiction found. No axis skipped due to absent documents. Phase status remains uncheckable. Facts found only in one artifact, additional detail, cross-plan disputes and omitted criteria are not counted as drift. Advisory results contribute to neither concern count.
