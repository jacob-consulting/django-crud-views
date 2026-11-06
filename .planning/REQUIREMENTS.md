# Requirements: django-crud-views — Concept Review Follow-ups

**Defined:** 2026-10-25
**Core Value:** Every public theme name (label-mode defaults, class-table keys, icon names, leaf templates, JS adapters)
settles once, consistently, before 1.0.0 freezes it — no public name changes twice.

Sources: `superpowers/plans/2026-10-24-concept-review-followups.md`, `.planning/research/SUMMARY.md`.
Global rule for every requirement: without new configuration, goldens under `tests/test1/golden/` stay byte-identical
except where a requirement says the markup changes.

## v1 Requirements

### Label-mode defaults (plan 1A)

- [x] **LMOD-01**: Project can set `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, merged per key over `{"context": "icon", "list": "icon", "card": "both"}`; docs state per-key merge vs whole-dict replacement of the per-button maps
- [x] **LMOD-02**: `default_label_mode(location)` in `crud_views.lib.view.label_mode` is the single source of the floor default, used by `cv_button_data()`, `cv_get_action_label_mode()` and `CardListView` (no `"both" if card` / `or "icon"` / `get(key, "icon")` literals remain)
- [x] **LMOD-03**: `CardListView.cv_card_actions_label_mode` defaults to `None` (= the map); an explicit `"both"` still wins; `{"card": "label"}` restores the 0.29 card look without touching a view
- [x] **LMOD-04**: The setting is read at call time, so `override_settings` changes it in tests
- [x] **LMOD-05**: An invalid label mode outside strict mode logs and falls back instead of raising
- [x] **LMOD-06**: Check `crud_views.E108` reports an unknown location key or invalid mode; valid keys derive from `LOCATIONS`, not a literal list

### Class-key grammar (plan 1C)

- [x] **KEYS-01**: Maintainer decides the `form:*` second-segment grammar (A: `form:<kind>:<mode>`, B: variants everywhere) during phase discussion; the rule is written in `docs/reference/buttons.md#the-class-table`
- [x] **KEYS-02**: W362 accepts mode keys for form buttons per the chosen grammar and rejects malformed ones (e.g. `form:submitt:icon`, `form:container:icon`)
- [x] **KEYS-03**: `LOCATIONS` is split into explicit sets (e.g. `VARIANT_LOCATIONS`, `FORM_KINDS`) so adding `"form"` to the button-data locations cannot loosen W362
- [x] **KEYS-04**: A test parses the key count quoted in `buttons.md` and asserts it equals the size of `DEFAULT_BUTTON_CLASSES`

### Filter toggle (plan 1B, #262)

- [x] **FILT-01**: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` renders icon + "Filter" (no `title`); `"label"` renders text only; default `icon` output byte-identical (`toolbar_publisher_list.html` golden)
- [x] **FILT-02**: `list.filter.js` toggles `aria-expanded` and persists state for a toggle without icon spans (vitest label-only case)
- [x] **FILT-03**: The toggle's text stays constant; only `aria-expanded` and the icon change (WAI-ARIA toggle-button rule)
- [x] **FILT-04**: The "Filter" label is a translated msgid (German catalog updated)

### Form-button leaf (plan 2, #257)

- [x] **FORM-01**: Golden of today's form-button markup is committed before any change, so the PR shows the diff
- [x] **FORM-02**: `"form"` is a button-data location; `cv_button_data(ctx, "form")` provides `cv_type`, `cv_name`, `cv_value`, `cv_id`, `cv_cancel_url` (cancel only); `cv_key` is the kind
- [x] **FORM-03**: New leaf `crud_views/tags/button/form.html` renders the three label-mode bodies with classes from `{% cv_button_class "form" cv_key cv_label_mode %}`
- [x] **FORM-04**: Class keys `form:hidden-label` (default `visually-hidden`) and `form:icon-host` exist, so icon-only form buttons keep an accessible hidden label and host-placed icon libraries render
- [x] **FORM-05**: crispy `Submit` / `Button` / `Reset` keep their constructor signature and render through the leaf; `css_class` is still appended; extra kwargs render as attributes
- [x] **FORM-06**: With nothing configured, form buttons render as `<button type="…">` with the same text, classes, `name`, `value`, `id`; POST data unchanged
- [x] **FORM-07**: Button values/labels are rendered as autoescaped plain text, never evaluated as a Django template; a label containing `<b>` renders escaped (button text and `value` attribute tested)
- [x] **FORM-08**: List filter Apply/Reset move from `helper.add_input()` into a layout `FormActions`, so they render through the leaf; `#filter-button-reset` id preserved; hidden sort/order inputs unchanged
- [x] **FORM-09**: Icons `save`, `cancel`, `filter-reset` exist in `DEFAULT_ICONS` and `BOOTSTRAP_ICONS`; submit→`save`, delete→`delete`, cancel→`cancel`, filter-submit→`filter`, filter-reset→`filter-reset`; workflow submit uses `workflow`; per-form `submit_icon` wins
- [x] **FORM-10**: `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` shows icon + text on save, delete, cancel and both filter buttons; `{"form": "icon"}` uses the hidden label with `title` and `data-cv-tooltip="form"`
- [x] **FORM-11**: Setting → ViewSet `form_actions_label_mode` → view `cv_form_actions_label_mode` per-key maps resolve like the context/list maps
- [x] **FORM-12**: Checks E210/E211/W291 cover form label-mode maps; W292 reports icon-only form buttons without an icon; strict mode raises at render, otherwise logs and renders the label
- [x] **FORM-13**: CHANGELOG `### Breaking` (`<input>` → `<button>`, no template evaluation of values) and `docs/migrating-1.0.md` "Form buttons" section; example project enables `both` for submit, delete, cancel; Tabler follow-up written into the acceptance note

### Alert dismiss (plan 3A)

- [x] **ALRT-01**: Golden of today's dismissible alert is committed before the change
- [x] **ALRT-02**: `tags/alert.html` renders `data-cv-alert-dismiss` instead of `data-bs-dismiss="alert"`; one delegated click handler calls `cv.adapters.alert.close(el)`
- [x] **ALRT-03**: `cv.adapters.alert.close` uses Bootstrap's `Alert` when present and falls back to `el.remove()` inside the adapter; vitest covers both
- [x] **ALRT-04**: `grep -rn 'data-bs-' src/crud_views/templates` lists only the dropdown templates named in `theme.md`; docs (`javascript.md`, `messages.md`, `theme.md`), CHANGELOG Breaking and migration bullet updated

### Table pagination (plan 3B)

- [x] **PAGE-01**: Golden of today's paginated table is committed before the change
- [x] **PAGE-02**: `table/bootstrap5.html` renders `page-previous` / `page-next` registry icons with translated hidden labels, `aria-current="page"`, disabled ends as `<a class="page-link" aria-disabled="true">`, translated `<nav>` label; existing tables2 block names kept
- [x] **PAGE-03**: One shared `pagination:hidden-label` class key (default `visually-hidden`) is read by both table and card pagination
- [x] **PAGE-04**: Both paginations produce the same accessible structure; CHANGELOG Breaking (DOM), migration bullet, `.po` files updated

### Request authorization and write integrity (inserted Phase 6.2)

Source: `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` B1–B7; locked decisions in
`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-CONTEXT.md`.

- [x] **AUTH-01**: All package delete views reject HTTP DELETE with 405 while the validated POST protection, form, hook and transaction lifecycle remains intact.
- [x] **AUTH-02**: Formset fragments authorize the target and validate root/parent/fragment ancestry before rendering; valid persisted and unsaved nested rows retain the request and {html, rows} protocol.
- [x] **AUTH-03**: Core and Guardian delete previews expose only permitted protected-object labels and an independent generic blocked notice, including when every label is hidden.
- [x] **AUTH-04**: Parent permission None preserves actual parent resolution and action-state enforcement; create controls/helpers and direct GET/POST agree without adding child-add requirements.
- [x] **AUTH-05**: Inactive actors receive no unauthorized rows or object access through Guardian request and callable helper paths, including when authentication permits inactive sessions; active-superuser behavior is preserved.
- [x] **AUTH-06**: Global fallback remains per view; the inert ViewSet flag is removed with clear diagnostics/migration; get_objects_for_user stays strict and manage shows effective policy per view and the strict helper policy.
- [x] **AUTH-07**: Direct-request actor and native-template regressions preserve parent/global, aggregate purge and form/cancel contracts; changed method/access/config/context behavior is documented with paired Breaking and migration guidance.

#### Acceptance ownership split (2026-10-30)

The AUTH wording above is retained. Historical Phase 6.2 evidence remains in
[06.2-ACCEPTANCE](phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md).
Phase 6.2 retained-scope verification/UAT passed on 2026-10-30; Phase 6.3 now completes the transferred
AUTH-01/03/07 and bounded GUA-01 obligations (2026-11-01, verification 91/91). The table records current
ownership outcomes; the original transfer history remains in the phase artifacts.

| Requirement | Retained Phase 6.2 evidence | Outstanding obligation / owner |
| --- | --- | --- |
| AUTH-01 | HTTP DELETE rejection and named POST form/hook/atomic controls | Complete; deletion/write repairs and scoped owner acceptance verified in Phase 6.3 |
| AUTH-02 | Fragment authorization/ancestry and nested round trips | A19 sibling/deeper int/UUID round trips verified in 06.4-10; IN-04 remains the documented unsupported custom-PK boundary |
| AUTH-03 | Permitted protected labels, independent notice, fixed CR-01/WR-02 response scope | Complete; authorization/projection and repaired modal focus verified in Phase 6.3 |
| AUTH-04 | Parent-None dispatch and Guardian helper/state regressions | WR-01 core rendered-state agreement fixed by quick 261030-csg (bd31992); 25 core and 86 preservation cases pass on both supported cached versions; retained-scope verification and UAT passed on 2026-10-30 |
| AUTH-05 | Named inactive-actor request/helper regressions | Retain recorded evidence; no new result or broader certification |
| AUTH-06 | Named per-view configuration, helper and manage regressions | Complete within reconciled scope; CT-01 fixed, detector flag dismissed; broader identity compatibility → issue #286 |
| AUTH-07 | Recorded actor/native-template replay and paired documentation | Complete; recorded three-series evidence, migrations and scoped acceptance verified |

### Delete protection remediation and bounded Guardian policy review (Phase 6.3)

**Scope reconciliation — 2026-11-01:** The four detector fallbacks are dismissed with recovered-source
evidence. GUA-01 precision acceptance is limited to the explicitly tested integer/UUID, exact configured-key,
queryset/model/type and same-alias identity predicates. Broader custom-PK/backend-cast/collation work is
unverified follow-up under issue #286, outside this phase's gate. See
[scope reconciliation](phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-SCOPE-RECONCILIATION.md).
Formal re-verification passed 91/91 with no overrides; Phase 6.3 completed on 2026-11-01.

Source: [issue #282](https://github.com/jacob-consulting/django-crud-views/issues/282), revised analysis addendum/§8,
and [06.2-REVIEW](phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW.md) CR-02–CR-04.
These remediate the existing AUTH promises; deferral leaves them unresolved and does not reopen fixed CR-01/WR-02.

- [x] **DEL-01**: Maintainer reviews detailed design/plan for safe protection inspection, supported custom behavior, exception translation, routing and override compatibility before implementation; architecture is not selected here.
- [x] **DEL-02**: Real-preview GET, invalid confirmation and custom-protected POST execute no deletion callbacks, including SET/default factories; failed valid POST preserves the write boundary. Database rollback alone is insufficient for external effects (CR-02; AUTH-01/03/07).
- [x] **DEL-03**: Established native PROTECT/RESTRICT retains friendly handling; unknown custom handlers, converters, model methods, hooks and commit callbacks propagate. Nested cascades/stale previews and real commit/rollback evidence cover both atomic settings (CR-03; AUTH-01/07).
- [x] **DEL-04**: Two-database tests with colliding PKs and protection on only one alias prove instance-aware inspection/deletion routing and alignment with transaction/commit hooks (CR-04; AUTH-01/03/07).
- [x] **DEL-05**: Core, Guardian and polymorphic authorization, filtered protected labels, independent blocked notice and coherent full-page/modal responses remain enforced (AUTH-03/07 preservation).
- [x] **DEL-06**: Reproduce fixes on Django 4.2/6.0, add supported Django 5.2 coverage, rerun deletion/transaction/authorization suites, update deletion/override docs and changelog (Breaking paired with migrating-1.0.md), and re-review affected 6.2 acceptance before closure.

- [x] **GUA-01**: Perform a bounded review of AUTH-06 policy boundaries and findings IN-02 (mutable strict-helper policy) / IN-03 (unknown permission-key diagnostics). Record a concrete scenario and expected outcome for each actionable gap; fix and test confirmed defects, preserving named AUTH-06 behaviors. If no additional gap supports the unclassified detector flag, close that flag with a documented rationale. Record explicit dispositions for IN-02/IN-03 and replay the policy tests on cached Django 4.2/6.0. This task transfers unresolved review work, not completed AUTH-06 implementation; any substantial policy redesign requires a separate scope decision.

GUA-01 was added by explicit user decision on 2026-10-30 as a bounded continuation of 6.2, alongside the
deletion work; it does not change issue #282 itself. IN-02/IN-03 are deferred here and remain unresolved.
WR-01 is **fixed** by quick 261030-csg (bd31992), outside this transfer. IN-01 is explicitly closed as intentional D-13 aggregate
policy, IN-04 as a documented unsupported slug-fragment boundary, and IN-05 is fixed with composition checks. See
[06.2-REVIEW-DISPOSITION](phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md).
The revised analysis schedules conditional/formset work in proposed 6.4, presentation cleanup in proposed 6.5,
and Tabler adoption seams in proposed 6.6. These proposals are not inserted by this task; Phase 7 stays last.

### Conditional and formset correctness/lifecycle (Phase 6.4)

Source: A1–A7 and the AUTH-02/A19 handoff; locked decisions D-01–D-19 in
`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md`.
Implementation/verification progress is tracked below; A8, A25, jQuery removal and broader Guardian #286 are excluded.

- [x] **COND-01**: Each group uses its exact bound checkbox name in its owning form, across prefixes, sibling/nested rows and injected content; ambiguous markup is diagnosed locally without changing that group's own state or bypassing a bound ancestor.
- [x] **COND-02**: Immediate native visibility composes every inactive ancestor with independently changed disabled reasons, includes native action buttons, preserves unsaved values and management controls, and recovers stranded focus without disrupting accepted modal focus.
- [x] **COND-03**: Native reset resynchronizes only its owning form after default reset, respects cancellation including later listeners, and preserves dynamic rows and management POST/re-render behavior.
- [x] **COND-04**: Inactive supported fields persist field-aware empty values including defaulted/omitted scalar fields, Boolean, FileField/ImageField and M2M; explicit values retain native meaning and server-disabled fields retain trusted values.
- [x] **COND-05**: Unsupported clearing shapes require explicit values and produce descriptive group/field configuration errors at static checks where detectable and at runtime otherwise; inherited form/model invariants remain authoritative.
- [x] **FSET-01**: All accepted active formset classes reject nonblank edit-only extras and missing/malformed/unauthorized existing-row IDs before any main/sibling/nested save, with generic identity errors and valid ordinary edits/new rows retained.
- [x] **FSET-02**: Documented root initializers automatically and repeatedly initialize page, modal/422 and added/nested content, include roots and late scripts/toggles, scope controllers per form, and preserve add/delete/order/submit/widget and event contracts.
- [x] **FSET-03**: A19 non-first sibling and deeper child fragments preserve authorized request coordinates, rendered prefixes, management totals and successful POST/database round trips; retain AUTH-02 ancestry and access gates.
- [x] **LIFE-01**: Real HTTP/browser evidence covers stock and minimal non-Bootstrap crispy/group/formset rendering, keyboard/focus, two forms, native reset, dynamic rows, 422 replacement, management payloads, and JS-off/tampered validation.
- [x] **LIFE-02**: Publish tested DOM, initializer, template projection, clearing and validation contracts with paired Breaking/migration guidance and Phase 7 inventory; preserve authorization, parent denial, restricted querysets, rollback, skip/purge, form-leaf, escaping, label and cancel contracts.

### Remaining presentation contracts and decided cleanup (Phase 6.5)

Source: Phase 06.5 CONTEXT.md D-01–D-17. Completed 2026-11-02: canonical verification passed and UAT 28/28 accepted, including the T22 human confirmation.

- [x] **PRES-01**: Heading sizing is theme-configurable with Bootstrap defaults, semantic levels, shared and page/modal/group icon styling, escaped classes and correct host/element icon placement with immediate custom-template migration.
- [x] **PRES-02**: Object-detail components and groups have collision-free generated IDs and optional stable supplied identities; rendering detects supplied collisions within its operation and documents separate-response uniqueness.
- [x] **PRES-03**: Vertical tabs initially select the first tab and visible panel for one or two groups; mouse and keyboard automatic activation work on page and freshly injected modal content with component isolation.
- [x] **PRES-04**: CardAction rejects any supplied no_label keyword including False with a label_mode migration error, removes the Python alias and obsolete cv_no_label template guard, and preserves unrelated extra handling and accepted label-mode APIs.
- [x] **PRES-05**: Badges expose resolved semantic color and pill alongside unchanged default CSS; arbitrary colors, one callback evaluation, ordinary-value fallbacks and badge-before-explicit-template precedence are preserved.
- [x] **PRES-06**: Executed copied/native template migrations preserve escaped titles, values and resolved context; real browser acceptance and preservation gates report their limits, paired Breaking migration entries and Phase 7 public-surface handoff.

### Theme-adoption seams (Phase 06.6)

Source: Phase 06.6 CONTEXT.md D-01–D-19 and issues #277–#280. These IDs transcribe the accepted scope;
the initial spec-less fallback was skipped while IDs were TBD, and generated no probe predicates.

- [x] **THEME-01**: Page templates own actionable create/update/custom/delete/workflow forms and CSRF, including page/modal POST; library helpers are nonwrapping, incompatible application helpers always reject, and detectable unused wrapper settings warn normally/raise strict without mutating caller helpers. Preserve accepted controls, escaping, authorization, deletion and conditional/formset/focus behavior.
- [x] **THEME-02**: register_label_mode_defaults validates atomically and merges per key with later registration winning; package → theme → live project setting resolves below explicit owner modes, invalid settings warn/fall back theme→package or raise strict, and E108/W292 reflect the effective contract.
- [x] **THEME-03**: Empty-default form:actions and form:filter-actions independently style ordinary/delete versus filter default groups, supplement current/floor pack structure, preserve custom layouts with tested opt-in, and update W362/key inventory.
- [x] **THEME-04**: alert:dismissible and alert:close replace or omit classes while preserving byte-identical Bootstrap defaults, escaping, accessible names, semantic markup and dismissal behavior.
- [x] **THEME-05**: Real reference theme/pack revisions have an unmodified baseline, all required automated/real-browser scenarios pass with no new regressions, required overrides do not grow, and a tested exact-base adaptation patch/replay/migration handoff is retained and delivered to the companion under the 2026-11-02 D-11/D-14 amendment; unrelated work and coverage limits remain explicit.
- [x] **THEME-06**: Executable migration examples document ownership, diagnostics, registration/precedence and group opt-in; nested-form/token DOM correction and every intentional compatibility change are recorded, Breaking entries pair with migrating-1.0.md, and Phase 7 receives the exact settled surface.

### Dynamic cancel navigation and origin query state (Phase 06.7)

Source: issue #302 and Phase 06.7 CONTEXT.md D-01–D-16. These are pending implementation requirements.

- [x] **CAN-01**: Standard create/update/delete and object/no-object custom forms use automatic eligible sibling origins by default; explicit None/empty lists remain static, explicit lists allow custom keys, list-to-card fallback survives, and detail origins use only the current saved form object. Detail-to-create restores no source object.
- [x] **CAN-02**: Emitted sibling links capture bounded query state with repeated/blank values, filters, ordering and pagination; validated captures remain independent across tabs and parent contexts, bind to the same ViewSet/current parent coordinates, and strip internal navigation fields without accepting return URLs.
- [x] **CAN-03**: Cancel restores nonempty or explicitly empty list state before session fallback; enabled persistence remembers the restored query or clears old filters, disabled persistence never writes or clears memory, and ordinary bare-list behavior remains intact.
- [x] **CAN-04**: Invalid submissions retain the original capture across create/update/delete and both custom-form families, supported modal replacements and polymorphic selector-to-create forwarding.
- [x] **CAN-05**: Allowed usable accessible origin wins, then accessible configured fallback, then omission; malformed/disallowed input falls back safely, missing configured fallback produces an actionable configuration diagnostic, and core/Guardian object, queryset, parent and state policies remain authoritative.
- [x] **CAN-06**: Crispy buttons, native anchors and a documented cancel URL helper share destination and omission; copied key-only cancel templates migrate immediately, with dynamic/static examples, settings/limits and paired Breaking/migration guidance.
- [x] **CAN-07**: Real request/browser acceptance proves all five issue flows without writes on Cancel and preserves save/delete success redirects, form ownership/CSRF/escaping, conditional/formset/modal contracts and existing protected-delete omission; no cross-ViewSet/history, browser-state capture or additional modal support is introduced.

### Action tooltips (Phase 06.8, #304)

Source: Phase 06.8 CONTEXT.md D-01–D-11 and issue #304. The confirmed observation is long icon-only
list captions in the stock example and an unspecified other application; a separate visible-label defect
has not been reproduced. External-application verification is outside this phase's completion gate.

- [x] **TIP-01**: Context/list icon-only actions use the existing nonempty short caption with full-caption fallback, retain the full hidden accessible label, and emit neither generated title nor marker for empty tooltip text; no new caption API or action renaming.
- [x] **TIP-02**: Effective label/both modes and non-strict missing-icon visible fallbacks have no generated tooltip. Every visibly labelled overflow item in context/list/card omits automatic title and marker regardless of inline mode, retaining short menu text and toggle behavior.
- [x] **TIP-03**: Preserve card-caption precedence, resolved form captions, custom ContextButton labels and app-owned tooltip attributes; retain lazy translations, escaping, permissions, disabled/active state, links, POST/modal hooks, label-mode precedence and tooltip initialization, hover/focus, hide/disposal behavior.
- [x] **TIP-04**: Require immediate copied action/menu template migration through executable documented recipes; describe changed cv_title semantics and removed menu titles in paired Breaking changelog and migrating-1.0.md guidance while retaining unrelated full-caption/helper APIs.
- [x] **TIP-05**: Real-browser stock Bootstrap and migrated custom-template fixtures prove short icon tooltips, full accessible labels and absent generated tooltips on visible actions/menus; record mixed-mode investigation outcomes honestly and report actual runtime/browser limits without requiring the affected external application.

### Delete-preview simplification (Phase 06.10, #316)

Decisions: `phases/06.10-simplify-protected-object-previews-and-cap-total-displayed-o/06.10-CONTEXT.md`.

- [x] **DPV-01**: Remove protected destination certification; preserve ordered escaped obj/url entries with null URLs and existing cascade hook behavior.
- [x] **DPV-02**: Default 50; explicit per-view then project setting; explicit None unlimited, unset inherits; reject invalid raw values.
- [x] **DPV-03**: One protected-first budget, depth-first cascade order, every occurrence/root counts; promote visible descendants of hidden rows; select before URLs.
- [x] **DPV-04**: Keep full summaries and redaction, truthful single translated overflow notice, separate incomplete warning, no empty cascade detail frame.
- [x] **DPV-05**: Preserve complete inspection/provider/filter/write contracts, visibility and whole-form blocking across core/Guardian/preview-off/page/modal.
- [x] **DPV-06**: Execute measurements and stock/copied page/modal acceptance; publish paired Breaking/migration guidance, examples and Phase 7 surface handoff.

### Protected delete-preview object links (Phase 06.9, #307)

Source: Phase 06.9 CONTEXT.md D-01–D-08 and issue #307. Immediate copied-template migration is approved.
The initial spec-less probe skipped visibly while IDs were TBD; planning reruns it against these assigned IDs.

- [x] **PDL-01**: Visible blockers link only to inspectable local registered detail destinations permitted by the target's access/state, queryset, parent and same-row/database policy; missing or inaccessible destinations remain text. The actual destination request remains authoritative for application middleware, dispatch and custom object lookup.
- [x] **PDL-02**: Filter protected model instances before URL work; preserve hidden notices, preview-disabled limited context, visible order, unfiltered blocking and whole-form omission without changing deletion or success redirects.
- [x] **PDL-03**: Every enabled preview exposes one ordered protected_objects collection of obj/url entries, including url=None with linking disabled; an independently overridable escaped blocker body uses the shared translated alert frame. Collector/provider/filter inputs remain model instances.
- [x] **PDL-04**: Protected names use ordinary full-page navigation from pages and delete modals, including modal-capable detail targets; preserve the shared URL override hook and existing cascade behavior.
- [x] **PDL-05**: Require immediate copied-template migration with an executable documented recipe, paired Breaking/migration guidance, updated delete reference and existing example guidance, and an exact Phase 7 surface inventory.
- [x] **PDL-06**: Core/Guardian, target denial, escaping, database identity and blocked-write regressions plus stock/custom browser acceptance prove the complete contract; report actual supported-series/runtime evidence and coverage limits.

### Opt-in workflow permissions (Phase 06.13, #320)

Source: `phases/06.13-workflow-permissions-document-and-test-opt-in-per-transition/06.13-CONTEXT.md`,
decisions D-01–D-15 captured from the corrected issue on 2026-11-05. These decisions supersede the older
roadmap's no-steps wording. All requirements below remain pending execution and verification.

- [x] **WFP-01**: Preserve the default workflow change gate and Campaign behavior. An isolated recipe explicitly uses the view page gate and two same-source transitions with ordinary change and dedicated step permissions. View plus step permission permits the appropriate GET/POST and history write; step permission alone cannot bypass page or applicable object/parent access checks.
- [x] **WFP-02**: Prove both no-step configurations separately: the basic recipe returns GET 200 with the existing empty message; the optional `cv_action_enabled` hook with disable policy renders a disabled sibling-page action and returns authenticated direct GET/POST 403 when false. A permitted actor succeeds through the hook.
- [x] **WFP-03**: Prove same-source permission-filtered choices reject forged POSTs and a valid offered choice independently reaches the real execution-time recheck, whose denial returns the existing 400. Every rejected attempt preserves persisted object state and object-scoped history.
- [x] **WFP-04**: Publish a complete basic model/permissions/transitions/form/ViewSet/views/URLs recipe before the separate optional hook variant. Explain all authorization layers, migration/grant prerequisites, navigation destinations, and the distinction between rendering and server enforcement without adding a public API or changing production behavior.
- [x] **WFP-05**: Deliver bounded regression tests and a documentation changelog entry; validate the recipe and strict docs, run focused and broader multicore regressions plus available supported-series checks, and report actual runtimes and coverage limits. Preserve repository hygiene and the phase exclusions.

### Workflow validation and execution (Phase 06.13.1, #322)

Source: `phases/06.13.1-workflow-validation-and-execution-business-blockers-transiti/06.13.1-CONTEXT.md`,
locked D-01–D-17 and issue #322 acceptance criteria. IDs assigned during planning from that existing scope;
WFP-01–WFP-05 remain completed prior-phase regression obligations. Initial spec-less fallback skipped visibly
because phase IDs were absent at intake; no fallback predicates were fabricated.

- [ ] **WFX-01**: Add the exact model-data-only business hook, ordered message/list blockers, correct transition/comment field errors and usable `clean()` return while preserving default radio/custom-form behavior (D-01–D-03, D-06, D-08).
- [ ] **WFX-02**: Export the exact actor-required standalone helper and share execution with the view: normalize/enforce comments, recheck state/conditions/permissions before business validation or dispatch, and persist complete state/history identity on one supported database (D-05, D-07, D-11, D-14).
- [ ] **WFX-03**: Distinguish expected refusal origin, roll back before bound redisplay with protected-FSM-safe persisted context, suppress every success effect, propagate unexpected errors, and preserve `on_transition`/commit semantics with outer atomic enabled or disabled (D-09, D-10, D-15).
- [ ] **WFX-04**: Deliver per-view opt-in native transition buttons in the shared page/modal form: exact clicked-name ownership, visible ordered blockers, separate help, required-comment semantics, escaped translated accessible text, unique descriptions, custom-form compatibility, all 25 UI considerations and real no-JS page/browser acceptance (D-04, D-12, D-13).
- [ ] **WFX-05**: Publish helper/hook/presentation/theme/lifecycle contracts and supported routing/direct-call limits; add release and any paired migration notes; record bounded regression, matrix, docs/lint/JS/browser evidence without overstating guarantees (D-16, D-17).

### Polymorphic labels and per-model detail groups (Phase 06.15, #326)

Source: Phase 06.15 CONTEXT.md D-01–D-19 and settled issue #326. These five bounded IDs are assigned
at planning; the initial spec-less probe visibly skipped because phase_req_ids were null/TBD and generated
no predicates. The plans preserve the context's exact-type, validation and deferred-scope boundaries.

- [x] **POLY-01**: Capitalize default selector labels with capfirst while preserving remaining case/translation, IDs/order/filtering, custom forms, permissions and redirect/cancel behavior without added label queries (D-01–D-02).
- [x] **POLY-02**: Accept existing group lists and exact-model mappings through one parser/resolver; preserve raw/typed/mixed lists and dynamic overrides, raise clear actual-model/view errors for absent entries, and keep selections request-local (D-03–D-07).
- [ ] **POLY-03**: Check every declared mapping key/value with model/location-aware structural/icon diagnostics, preserve existing and inherited checks, and avoid object queries, runtime hook evaluation and optional polymorphic imports for ordinary models; document structural limits (D-08–D-12).
- [ ] **POLY-04**: Publish complete generic list/mapping and supported-composition recipes, exact-type/errors/check limits/dynamic escape-hatch guidance, and release notes with paired migration guidance if classified Breaking; keep changes bounded (D-17–D-18).
- [ ] **POLY-05**: Deliver required downstream workaround removal with retained form/layout/groups, all catalog types and permission regressions, verified changed-checkout imports, passing catalog and warning-level checks, scoped findings 10–11 resolution and attributable two-repository evidence (D-13–D-16, D-19).

### Stability policy (plan 4)

- [ ] **STAB-01**: `docs/development/stability.md` lists the theme surface (icons, buttons, alerts, JavaScript adapters/events/DOM contract, theme hooks, leaf templates) with explicit names, no wildcards
- [ ] **STAB-02**: Names are classified into stable / provisional / internal tiers
- [ ] **STAB-03**: `tests/test1/test_stability_doc.py` checks both directions: every documented name exists, and every public theme name is documented
- [ ] **STAB-04**: A public `is_library_renderer(prefix, callable)` (or equivalent) helper replaces the theme's need for `_get_renderers` / `_icon_str`
- [ ] **STAB-05**: The stability doc lists dependency floors (crispy-forms, crispy-bootstrap5, django-tables2, Bootstrap)
- [ ] **STAB-06**: `theme.md` cross-references "what a theme may rely on"; theme part of #89 closed

## Deferred URL and visibility work

The withdrawn NURL-01–04 and AUTH-08–09 entries are preserved in the
[pre-retirement requirements snapshot](../superpowers/archive/2026-11-04-phase-06.10-object-derived-nested-urls-and-link-access-parity/planning-before-retirement/REQUIREMENTS.md).
They are not active v1 requirements and their identifiers are reserved for historical traceability.
The smaller opt-in helper is backlog [#314](https://github.com/jacob-consulting/django-crud-views/issues/314); the confirmed visibility bugs remain in
[#312](https://github.com/jacob-consulting/django-crud-views/issues/312) for separate scoping.
Neither is scheduled by this document. See the [maintainer decision](../superpowers/notes/2026-11-04-opt-in-url-helper-decision.md).

## v2 Requirements

Deferred; tracked for 1.0.0 outside this milestone.

- **LATER-01**: Promoted to PRES-04 in Phase 6.5; alias/guard removal remains pending verification.
- **LATER-02**: Decided in Phase 1: retain both `cv_context_actions_label_mode` / `cv_context_action_label_mode`; no rename.
- **LATER-03**: E36x check for `container-tag`
- **LATER-04**: Promoted to PRES-01 in Phase 6.5; #259 heading contract remains pending verification.
- **LATER-05**: #211 stale-override detection
- **LATER-06**: Promoted to THEME-04 in Phase 06.6; selected alert utility keys are required before the freeze.
- **LATER-07**: Lowest-version crispy test session / Django 4.2 support decision for 1.0.0

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-view / per-variant entries in the defaults map | Per-ViewSet/view knobs already exist; the map is the project-wide floor |
| Themes replacing explicit owner label-mode choices | THEME-02 permits a theme floor only; explicit view/button modes and project settings retain precedence |
| Using crispy `StrictButton` / `HTML()` for buttons | Unescaped content |
| Overriding crispy-bootstrap5 templates globally | Breaks other template packs (crispy-tabler) |
| Alert focus management / auto-dismiss | Beyond the leak fix |
| Pagination extras beyond matching card pagination | Scope is consistency only |
| Bootstrap 6 support | Alpha; adapters fallback covers absence of global `bootstrap` |
| Publishing or pushing companion changes | THEME-05 authorizes verified source/test delivery and scoped local commits under amended D-11/D-14; publication is outside this phase |
| The 1.0.0 version bump | Follows after the stability phase |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| POLY-01 | Phase 06.15 (plan 02) | Complete |
| POLY-02 | Phase 06.15 (plan 01) | Complete |
| POLY-03 | Phase 06.15 (plan 01) | Pending |
| POLY-04 | Phase 06.15 (plan 03) | Pending |
| POLY-05 | Phase 06.15 (plans 03–04) | Pending |
| WFX-01 | Phase 06.13.1 | Pending |
| WFX-02 | Phase 06.13.1 | Pending |
| WFX-03 | Phase 06.13.1 | Pending |
| WFX-04 | Phase 06.13.1 | Pending |
| WFX-05 | Phase 06.13.1 | Pending |
| WFP-01 | Phase 6.13 | Complete |
| WFP-02 | Phase 6.13 | Complete |
| WFP-03 | Phase 6.13 | Complete |
| WFP-04 | Phase 6.13 | Complete |
| WFP-05 | Phase 6.13 | Complete |
| PDL-01 | Phase 6.9 | Complete |
| PDL-02 | Phase 6.9 | Complete |
| PDL-03 | Phase 6.9 | Complete |
| PDL-04 | Phase 6.9 | Complete |
| PDL-05 | Phase 6.9 | Complete |
| PDL-06 | Phase 6.9 | Complete |
| DPV-01 | Phase 6.10 | Complete |
| DPV-02 | Phase 6.10 | Complete |
| DPV-03 | Phase 6.10 | Complete |
| DPV-04 | Phase 6.10 | Complete |
| DPV-05 | Phase 6.10 | Complete |
| DPV-06 | Phase 6.10 | Complete |
| TIP-01 | Phase 6.8 | Complete |
| TIP-02 | Phase 6.8 | Complete |
| TIP-03 | Phase 6.8 | Complete |
| TIP-04 | Phase 6.8 | Complete |
| TIP-05 | Phase 6.8 | Complete |
| CAN-01 | Phase 6.7 | Complete |
| CAN-02 | Phase 6.7 | Complete |
| CAN-03 | Phase 6.7 | Complete |
| CAN-04 | Phase 6.7 | Complete |
| CAN-05 | Phase 6.7 | Complete |
| CAN-06 | Phase 6.7 | Complete |
| CAN-07 | Phase 6.7 | Complete |
| THEME-01 | Phase 6.6 | Complete |
| THEME-02 | Phase 6.6 | Complete |
| THEME-03 | Phase 6.6 | Complete |
| THEME-04 | Phase 6.6 | Complete |
| THEME-05 | Phase 6.6 | Complete |
| THEME-06 | Phase 6.6 | Complete |
| PRES-01 | Phase 6.5 | Complete |
| PRES-02 | Phase 6.5 | Complete |
| PRES-03 | Phase 6.5 | Complete |
| PRES-04 | Phase 6.5 | Complete |
| PRES-05 | Phase 6.5 | Complete |
| PRES-06 | Phase 6.5 | Complete |
| LMOD-01 | Phase 1 (plan 1A) | Complete |
| LMOD-02 | Phase 1 (plan 1A) | Complete |
| LMOD-03 | Phase 1 (plan 1A) | Complete |
| LMOD-04 | Phase 1 (plan 1A) | Complete |
| LMOD-05 | Phase 1 (plan 1A) | Complete |
| LMOD-06 | Phase 1 (plan 1A) | Complete |
| KEYS-01 | Phase 2 (plan 1C) | Complete |
| KEYS-02 | Phase 2 (plan 1C) | Complete |
| KEYS-03 | Phase 2 (plan 1C) | Complete |
| KEYS-04 | Phase 2 (plan 1C) | Complete |
| FILT-01 | Phase 3 (plan 1B) | Complete |
| FILT-02 | Phase 3 (plan 1B) | Complete |
| FILT-03 | Phase 3 (plan 1B) | Complete |
| FILT-04 | Phase 3 (plan 1B) | Complete |
| ALRT-01 | Phase 4 (plan 3A) | Complete |
| ALRT-02 | Phase 4 (plan 3A) | Complete |
| ALRT-03 | Phase 4 (plan 3A) | Complete |
| ALRT-04 | Phase 4 (plan 3A) | Complete |
| PAGE-01 | Phase 5 (plan 3B) | Complete |
| PAGE-02 | Phase 5 (plan 3B) | Complete |
| PAGE-03 | Phase 5 (plan 3B) | Complete |
| PAGE-04 | Phase 5 (plan 3B) | Complete |
| FORM-01 | Phase 6 (plan 2) | Complete |
| FORM-02 | Phase 6 (plan 2) | Complete |
| FORM-03 | Phase 6 (plan 2) | Complete |
| FORM-04 | Phase 6 (plan 2) | Complete |
| FORM-05 | Phase 6 (plan 2) | Complete |
| FORM-06 | Phase 6 (plan 2) | Complete |
| FORM-07 | Phase 6 (plan 2) | Complete |
| FORM-08 | Phase 6 (plan 2) | Complete |
| FORM-09 | Phase 6 (plan 2) | Complete |
| FORM-10 | Phase 6 (plan 2) | Complete |
| FORM-11 | Phase 6 (plan 2) | Complete |
| FORM-12 | Phase 6 (plan 2) | Complete |
| FORM-13 | Phase 6 (plan 2) | Complete |
| AUTH-01 | Phase 6.2 + 6.3 | Complete; deletion/write repairs and scoped owner acceptance verified in Phase 6.3 |
| AUTH-02 | Phase 6.2 + 6.4 | Named 6.2 evidence retained; A19 successful sibling/deeper round trips source-bound in 06.4-10; IN-04 int/UUID-only boundary and other exclusions unchanged |
| AUTH-03 | Phase 6.2 + 6.3 | Complete; authorization/projection and repaired modal focus verified in Phase 6.3 |
| AUTH-04 | Phase 6.2 | Complete; WR-01 fixed; verification/UAT passed |
| AUTH-05 | Phase 6.2 | Complete |
| AUTH-06 | Phase 6.2 + 6.3 | Complete within reconciled scope; CT-01 fixed, detector flag dismissed; broader identity compatibility → issue #286 |
| AUTH-07 | Phase 6.2 + 6.3 | Complete; recorded three-series evidence, migrations and scoped acceptance verified |
| DEL-01 | Phase 6.3 | Complete; actual bound approvals and prohibition-01 acceptance retained; detector fallback dismissed |
| DEL-02 | Phase 6.3 | Complete; callback-safe inspection, repaired joins and scoped human dispositions verified |
| DEL-03 | Phase 6.3 | Complete; native/custom provenance verified; detector fallback dismissed |
| DEL-04 | Phase 6.3 | Complete; selected native row/parent identity verified; detector fallback dismissed |
| DEL-05 | Phase 6.3 | Complete; authorization, partial notices and repaired focus verified |
| DEL-06 | Phase 6.3 | Complete; recorded three-series evidence, migrations, repairs and scoped human acceptance verified |
| GUA-01 | Phase 6.3 | Complete within explicit bounded identity scope; IN-02/03 and CT-01 fixed; broader compatibility unverified in issue #286 |
| COND-01 | Phase 6.4 | Complete — exact binding and ambiguous ownership/recovery verified; scoped fallback assessment passed. |
| COND-02 | Phase 6.4 | Complete — external baseline, ancestor composition and frozen ownership verified. |
| COND-03 | Phase 6.4 | Complete — cancellable owning-form native reset and management behavior verified. |
| COND-04 | Phase 6.4 | Complete — native reference-only persistence verified; exact bounded H2 prohibition explicitly accepted; application hooks remain excluded. |
| COND-05 | Phase 6.4 | Complete — E312/runtime configuration refusal and inherited invariants verified. |
| FSET-01 | Phase 6.4 | Complete — edit-only and row identity policy survives native/sibling/nested recleaning before writes. |
| FSET-02 | Phase 6.4 | Complete — optional DELETE, stable bound identity and repeat-safe page/modal/dynamic lifecycle verified. |
| FSET-03 | Phase 6.4 | Complete — scoped A19 sibling/deeper round trips and authorization verified; broader AUTH-02 exclusions retained. |
| LIFE-01 | Phase 6.4 | Complete — source-bound browser evidence plus actual Chrome/Orca stock/native and modal acceptance; versions/distribution unspecified. |
| LIFE-02 | Phase 6.4 | Complete — executable contracts/docs, paired migration, independent WR-05 closure, security44/44 and canonical10/10 passed. |
| STAB-01 | Phase 7 (plan 4) | Pending |
| STAB-02 | Phase 7 (plan 4) | Pending |
| STAB-03 | Phase 7 (plan 4) | Pending |
| STAB-04 | Phase 7 (plan 4) | Pending |
| STAB-05 | Phase 7 (plan 4) | Pending |
| STAB-06 | Phase 7 (plan 4) | Pending |

**Coverage:**

- v1 requirements: 116 total
- Mapped to phases: 116
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-25*
*Last updated: 2026-11-06 — added five bounded Phase 06.15 requirements and traceability; recounted 116 active v1 requirements including existing WFX requirements*
