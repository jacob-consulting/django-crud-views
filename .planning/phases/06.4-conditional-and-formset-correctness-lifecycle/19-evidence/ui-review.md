# Phase 06.4 — Plan 19 Independent UI Re-audit

**Audited:** 2026-11-01, 17:17–17:20 UTC.
**Actor:** delegated `gsd-ui-auditor`; independent evidence reviewer, not implementation author or human approver.
**Baseline:** approved `06.4-UI-SPEC.md`, preservation contract and CONTEXT D-01–D-19; plans 16–19 and summaries 16–18.
**Screenshots:** existing captures inspected, 3/3 current stock PNG hashes independently verified. No new capture.
**Interaction captures:** off (`interaction_capture=false`). Existing browser assertions were inspected; no fresh interaction screenshot or browser execution is claimed.
**Disposition:** 24/24 for the bounded implemented UI preservation contract. Original V1/V2/S1 fixture warnings are closed. Evidence-checker warnings, security findings and human gates remain open; this score is not phase approval.

## Pillar Scores

| Pillar | Score | Key finding |
|--------|-------|-------------|
| Copywriting | 4/4 | Generic policy errors, named controls and existing Save/Cancel contract preserved. |
| Visuals | 4/4 | Actual captures show populated icons and preserved nested hierarchy; mobile metadata repaired. |
| Color | 4/4 | Primary Save, neutral row actions and registry-driven destructive state preserved. |
| Typography | 4/4 | Native labels/legends and inherited host styles preserved without new overrides. |
| Spacing | 4/4 | Container repair eliminates recorded horizontal overflow at all three widths. |
| Experience Design | 4/4 | Optional DELETE, stable row identity and unresolved conditional ownership repairs have concrete stock/native evidence. |

**Overall: 24/24.** Scores assess the scoped UI against its approved preservation contract, not evidence-runner robustness, global security, arbitrary consuming themes or human accessibility acceptance. Positive findings below justify each 4; no lower score is averaged upward. No new demonstrated product UI blocker was found in this bounded review.

## Top 3 Priority Follow-ups

1. **WARNING WR-04 — revalidate conditional screenshots in the aggregate checker.** `15-evidence/run.py:857,890–924` trusts prior canonical-check success without validating the current conditional capture inventory/bytes. Apply the canonical screenshot contract during aggregate/handoff checks and reject missing/changed captures. This audit independently verifies the actual current files but does not repair the checker.
2. **WARNING WR-03 — validate actual corruption control records.** `15-evidence/run.py:984–985` checks summary labels without reconciling `checker_control_evidence`. Require exact record inventory, checker command, nonzero exit and rejection diagnostics; add missing/contradictory-record controls. The present 25 records really contain exit 1/rejection diagnostics; their existence does not close this robustness defect.
3. **H1 — obtain actual human stock/native review.** Human users must judge nested control discoverability, label/error readability, keyboard orientation and assistive-technology announcements. Keep H2 separately flagged-unverified; do not convert this score, screenshots or storage spies into approval.

## Detailed Findings

### 1. Copywriting — 4/4

**Positive C1:** `src/crud_views/lib/formsets/render_tree.py:246–251` retains translated `Invalid row.` and `Additions are not allowed.`; these intentionally generic strings avoid leaking row identity. `formsets/formset.html:26–27` renders nonform errors before rows, not after the collection. The current both-theme `gap-capability` records contain real 422 generic-policy responses and unchanged save-event counts, corresponding to `tests/browser/conditional-formsets.cjs:275–285`. These are response/assertion observations, not screenshots of the errors.

**Positive C2:** `formsets/control.html:5–29` preserves translated Row controls, Order, Add or delete, Move up, Move down, Add row and Delete row, with titles and accessible names on icon controls. Native override `tests/browser/templates/conditional_formsets/native_control.html:3–7` uses visible equivalent labels and native buttons. Existing Save/Cancel copy is approved; generic-label heuristics do not justify changing it. Fixture reset/isolation labels are explicitly test-host text (`page.html:42–49`).

### 2. Visuals — 4/4

**Closed WARNING V1:** `page.html:5–7` now loads the configured Font Awesome 6.7.2 stylesheet. All three images visibly show plus, deletion and directional glyphs in pale row-control surfaces. Stored observations also contain loaded Font Awesome faces and nonempty positive-size glyph boxes. This closes the original blank-icon fixture finding, not arbitrary remote-asset reliability for every host.

**Closed WARNING V2:** `page.html:4` now supplies `width=device-width, initial-scale=1`. The recorded mobile context explicitly uses `isMobile=true`, `hasTouch=true`, scale factor 1 and 375×812 CSS viewport (`conditional-formsets.cjs:339–343`). The actual mobile PNG is 375px wide; labels and controls remain within its edges. Tablet is viewport resizing, not touch-device certification.

**Positive V3:** Viewed full-page desktop, mobile and tablet files with the image viewer. Outer/Inner legends precede their controls; Books, Notes and Memos retain nested indentation; gray disabled Baseline differs from white editable fields; blue Save remains identifiable. Desktop has generous side margins, mobile retains narrow gutters, tablet has intermediate margins. The screenshots visibly include a second isolation form and a plain test-host Save beside Reset fields in addition to the styled Save/Cancel. `page.html:44–49` explains these test-host surfaces; they are not evidence of duplicate product CTAs or final consuming-page composition. These populated captures do not depict the 422 state or inactive state reached earlier by the case.

### 3. Color — 4/4

**Positive K1:** `src/crud_views/lib/button_classes.py:56–66` retains primary submit, secondary Cancel, light row controls and danger deletion state. Four action types resolve the control registry; one has the separate destructive-state slot. Captures show restrained blue checkboxes/Save over white and neutral surfaces. No pixel-percentage measurement is claimed; the contract defines 60/30/10 as inherited semantic roles.

**Positive K2:** The relevant templates and conditional/formset scripts add no literal palette. Existing `formset.css:1–35` contains three inherited highlight animations, nine hex declarations and four distinct colors. Their presence is explicitly permitted by the preservation contract. No contrast-ratio or all-state color certification was performed.

### 4. Typography — 4/4

**Positive T1:** `formsets/formset.html:18` retains native legends; conditional wrappers retain their configured legend element. The repaired control predicate changes eligibility, not font classes. No new font-size or weight override appears in the reviewed templates/scripts. Contract reference sizes remain 14/16/20/24px and content weights 400/700, with responsive Bootstrap legends and modal-title exceptions.

**Positive T2:** The images retain a larger legend-to-label hierarchy and legible distinct control text without observed truncation in these short English fixtures. This review did not independently measure computed fonts; historical review measurements are not relabeled current. Multilingual text, long unbroken labels, zoom and human readability remain unverified, as allowed by the preservation scope and H1.

### 5. Spacing — 4/4

**Closed WARNING S1:** `page.html:34` now wraps content in `main.container`, matching the established host. Packet document `clientWidth/scrollWidth/innerWidth` are respectively 1440/1440/1440, 375/375/375 and 768/768/768. Viewed images agree with visible contained fields and controls. The old 12px overflow is absent in these recorded fixtures.

**Positive S2:** `formsets/formset.html:7–13,56–64` preserves row/column gutters and balanced wrappers; no arbitrary new px/rem spacing or new margin/padding/gap utility was added in the repaired surfaces. The contract's 4/8/16/24/32/48/64px reference scale retains native geometry exceptions. Full-page heights exceed viewport heights through normal document flow, not clipping. No new fixed-height container or ellipsis was introduced.

### 6. Experience Design — 4/4

**Positive E1 / CR-03 and CR-04:** `formset.js:10–23` computes deletion eligibility from exact owning formset prefix plus immutable bound suffix; `:265–279` only requires DELETE where eligible, and `:328–330` applies the same rule to row actions. `control.html:25` and native override `:7` use actual DELETE field presence. Inspected browser driver `:243–274` and both-theme `gap-capability` records: extra rows lack DELETE/button, Add emits once, an extra moves above an initial row, the initial row remains deletable, actual POST persists intended order, and all-extra Add/order/POST succeeds. DOM position is not substituted for bound identity.

**Positive E2 / CR-05:** `toggle.js:14–17,78–112,137–167` keeps last owned state separately from listener attachment, freezes it through missing/ambiguous binding and recovers on an exact unique match. Reviewed actual both-theme `gap-ambiguity` assertions and driver `:288–335`: off required controls remain hidden/disabled and excluded from FormData, management fields remain, obsolete listeners do not follow arbitrary checkboxes, independent/ancestor ownership survives, and the other form is unaffected. This supports closure of the original T-06.4-01 counterexample within the independently reviewed bounds.

**Positive E3:** `toggle.js:65–74,121–133` preserves usable focus recovery and queued native reset/cancellation. Stored default/cancelled reset and conditional-focus cases exist for both themes. New gap cases record Enter activation of reset and modal opener/submit, actual HTTP 422, focus on the replacement invalid name field, no later focus theft, and retained reset focus. These are inspected source-bound browser records, not fresh interaction captures or a human keyboard usability judgment.

**Positive E4:** The packet has 24 conditional cases/172 assertions plus 12 retained modal cases/133 assertions: 36/305, every assertion true, both page-error arrays empty. Modal cases include close/Escape, removed/disabled/hidden opener, repeated open, native dialog and pending-close cases. CR-01 rejection/reclean behavior and CR-02 runtime separation are independently closed in `19-evidence/code-review.md`; original linked T-07/08/09 and T-15 repairs are bounded, not a global security clearance. Original WR-01/02 are closed there, while new WR-03/04 keep G6/evidence convergence open.

Empty/loading/error/destructive handling is assessed against the existing contract: configured blank rows, preserved content while loading, generic validation errors, existing diagnostics/fallback, and reversible pending Delete until Save. Invented skeletons, live regions or new confirmation dialogs are not required.

## Independent Evidence Checks

- Source digest confirmed by the read-only aggregate checker: `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601`.
- Runner independently SHA-256 hashed: `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c`.
- Packet identity in handoff/code review: `a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674`; manifest identity `160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf`.
- Executed `.nox/crispy_floor-3-12-django-6-0/bin/python .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py --check --output .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/18-evidence/results.json`: exit 0, `PHASE64_MATRIX_OK 20 gates` with the source digest above. This does not close known validator omissions.
- Independently parsed PNG IHDR dimensions and hashed every stock image with Python `struct`/`hashlib`; all three equal their packet SHA-256. Inspected each image using `view_image`, independently of green assertion summaries.
- Independently counted the browser cases/assertions and checked every assertion boolean/page-error list. Inspected all 25 control records for exit 1 and `MATRIX_REJECTED`; all satisfy that bounded observation. Did not rerun the corruption subprocesses.

| Existing file under `.planning/ui-reviews/06.4-gap-repair/` | CSS viewport | Actual PNG | SHA-256 |
|---|---|---|---|
| desktop.png | 1440×900 | 1440×3104 | `6af0369c076c37eb02a9e132e6da01fd1b04a52bc1ec428f7e2fc59f8f2b81ef` |
| mobile.png | 375×812 | 375×3052 | `314006515ef104b3a93a7b390aec27addf67733df5b37fc53752e447b731edfe` |
| tablet.png | 768×1024 | 768×3077 | `55c2ee11a8e16140abb64a9fe37f55feb07428322e5fa6a4ed9e76f33be16282` |

The native case contains zero captures. Its `.every()` screenshot assertions are vacuous for that empty array and must not be reported as native visual evidence. Native controls and behavior were reviewed through source and stored interaction records only. Screenshots are fresh page loads performed after the case interactions (`conditional-formsets.cjs:344–359`); they do not show modal 422 or ambiguous hidden-state results.

## Limits and Open Gates

**H1: pending; needs_human_review: true.** Only a human can supply the requested discoverability/readability/keyboard/assistive-technology disposition. Headless Linux Chromium 149 and mobile/touch emulation do not certify physical devices or screen readers.

**H2: flagged-unverified.** Exact prohibition: **Switching a conditional file field off must not silently authorize deletion of the stored file content.** Reference-only ImageField/native storage-delete spies and retained bytes do not provide the missing enforcement descriptor, app-hook guarantee or human judgment.

Security lane's independently reproduced open findings remain T-06.4-22/28/33/35/36 (high) and T-06.4-31 (medium), as communicated in the assignment. This UI review does not independently reproduce or close those findings. Original code repairs and a 24/24 UI score do not override them. No fabrication of the actual 25 corruption records or screenshots is alleged.

No new server detection or capture was performed under the explicit bounded reuse assignment; no browser/test suite/install was launched. Existing screenshot ignore patterns cover every specified image extension and `interaction/`; capture source also checks `git check-ignore` before writing. No capture-directory mutation was needed. No project skill directories or configured auditor skills were present. Registry audit is inapplicable: no `components.json` and no third-party registries in the design contract.

Only this owned evidence report was written; no canonical report/state, source, tests, commits or completion status changed. The runtime has no local Read/Write tools; shell reads and the available file-edit tool were used, with no heredoc file creation.

## Files Audited

- AGENTS.md; GSD ui-review workflow/ui-brand reference and agent-skills bootstrap; phase UI-SPEC, CONTEXT, original UI-REVIEW, plans 16–19 and summaries 16–18; plan-19 handoff and independent code review.
- `18-evidence/results.json`, source-manifest identity, `15-evidence/run.py` through its read-only checker and independent code-review references.
- `src/crud_views/templates/crud_views/formsets/control.html`, `formset.html`; conditional wrapper contract; `src/crud_views/static/crud_views/js/toggle.js`, relevant `formset.js` action/identity sections; `static/crud_views/css/formset.css`; `lib/button_classes.py`, `lib/formsets/render_tree.py`.
- `tests/browser/templates/conditional_formsets/page.html`, `native_control.html`; `tests/browser/conditional-formsets.cjs` capability/ambiguity/capture branches; existing conditional/modal packet records; three PNGs listed above.

**Recommendation count:** 2 open evidence-checker warnings; 1 H1 human-review follow-up; H2 separately flagged-unverified. Original priority fixture warnings closed: 3/3. New demonstrated product UI blockers: 0. Canonical verification and phase completion remain outside this report.
