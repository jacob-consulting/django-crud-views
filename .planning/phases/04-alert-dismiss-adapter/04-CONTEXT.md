# Phase 4: Alert dismiss adapter - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Route dismissible alert closing through `cv.adapters.alert.close(el)` instead of Bootstrap's data API
(source plan 3A; ALRT-01 through ALRT-04). The stock frame uses `data-cv-alert-dismiss`. Delegated handling
also supports alerts inserted after page load. The default adapter uses Bootstrap's `Alert` component when
available and otherwise removes the element. Document the DOM change and the theme customization contract.

No separate SPEC.md was supplied; the roadmap says this phase needs no separate research/spec. Alert focus
management, auto-dismiss, new lifecycle events, and other component changes remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Frame styling
- **D-01:** Keep the existing literal frame classes, including `btn-close` and `alert-dismissible fade show`.
  Do not introduce new alert class-table keys in Phase 4. The additional frame-class keys remain tracked
  under existing LATER-06.
- **D-02:** Add a short frame-override example in `docs/reference/theme.md`, rather than only explanatory
  prose and links. Show custom frame classes while retaining `role="alert"` on the frame and
  `data-cv-alert-dismiss` on its close control. These hooks preserve the delegated dismissal behavior.
  Keep the example focused on the existing frame contract.

### Custom adapter behavior
- **D-03:** Core calls the theme's `alert.close(el)` and lets exceptions surface. Do not catch and log a
  custom-adapter failure or force removal afterward. Core leaves the alert alone on failure; it does not
  undo any changes already made by the adapter.
- **D-04:** Plain `el.remove()` is a fallback inside the default alert adapter only when the configured
  namespace has no `Alert` component. It is not a second closing path in the delegated handler and is not
  recovery from a throwing custom adapter or Bootstrap component. The theme owns its closing behavior.

### Migration guidance
- **D-05:** Add a compact before/after example in `docs/migrating-1.0.md`, rather than a single migration
  bullet with links alone. Show replacement of `data-bs-dismiss="alert"` with `data-cv-alert-dismiss`,
  explain the required core scripts, and link to the adapter and message references for details.
- **D-06:** Recommend adopting the new hook when upgrading copied alert templates, even when retaining
  Bootstrap. Explain that legacy overrides using `data-bs-dismiss="alert"` still work through Bootstrap's
  own JavaScript; they do not gain the adapter's no-Bootstrap fallback until migrated.

### Carried-forward scope and acceptance
- **D-07:** Commit a golden of today's dismissible alert before changing the markup, so the implementation
  history shows the attribute change (ALRT-01). Preserve other output and non-dismissible behavior.
- **D-08:** Follow the source design: delegate clicks in `viewset.js`, locate the enclosing
  `role="alert"` frame, and call `cv.adapters.alert.close(alertEl)`. Newly inserted alerts, including modal
  content, must close without per-alert initialization. Keep adapter lookup at call time and the existing
  preassigned-adapter preservation and Bootstrap namespace conventions.
- **D-09:** Update `docs/reference/javascript.md`, `docs/reference/messages.md`, and
  `docs/reference/theme.md`. The adapter factory now supplies four adapters. Record the DOM attribute change
  under CHANGELOG Breaking and update the migration guide in the same change. The stock template's remaining
  `data-bs-*` uses must be limited to the dropdown templates already named in `theme.md`.
- **D-10:** Verify closing with Bootstrap, without its `Alert` component, and through a custom adapter;
  cover delegated handling of dynamically inserted alerts and the chosen error behavior. Confirm the
  example project's flash messages still close. Preserve the project's implementation quality gates.

### Agent's Discretion
- No product decision was explicitly delegated. Exact test organization, implementation details of the
  delegated handler, template whitespace, and documentation wording remain implementation choices within
  the decisions and acceptance requirements above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and acceptance
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, and relationship to the stability phase.
- `.planning/REQUIREMENTS.md` — ALRT-01 through ALRT-04, LATER-06, and excluded alert capabilities.
- `.planning/PROJECT.md` — compatibility, public-name stability, documentation rules, and quality gates.
- `superpowers/plans/2026-10-24-concept-review-followups.md` — Phase 3A design and global constraints;
  D-04 settles fallback placement inside the adapter.
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — origin of the Bootstrap alert leak.

### Public contracts and documentation
- `docs/reference/theme.md` — alert frame overrides, class-table color keys, and the Bootstrap dropdown list.
- `docs/reference/javascript.md` — adapter table, call-time replacement, namespace factory, and script ordering.
- `docs/reference/messages.md` — dismissible flash-message markup and alert frame context.
- `docs/migrating-1.0.md` — migration example and recommendation for copied templates.
- `CHANGELOG.md` — Breaking entry for the DOM attribute change.
- `CLAUDE.md` — repository conventions, including the paired Breaking/migration update rule.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crud_views/static/crud_views/js/adapters.js`: `cv.bootstrapAdapters(ns)` already resolves namespaces
  lazily through `component(ns, name)` and preserves adapters assigned before script load with a shallow
  per-adapter merge. Add the default alert adapter through this seam.
- `src/crud_views/static/crud_views/js/viewset.js`: existing document-level click handlers use an
  `Element` guard, `closest()`, and default prevention; this is the source design's integration point.
- `src/crud_views/templates/crud_views/tags/alert.html`: a single frame renders all package alerts, uses
  `role="alert"`, and currently emits `data-bs-dismiss="alert"` only for dismissible alerts.
- `tests/test1/test_alerts.py`: existing frame, escaping, class-table, body-template, and override tests.
- `tests/js/adapters.test.js` and `tests/js/viewset.test.js`: existing adapter and delegated-event coverage.

### Established Patterns
- Core resolves `cv.adapters` methods when handling the action; themes can replace an adapter before the
  user acts. Bootstrap is likewise looked up lazily, including through alternate namespace factories.
- Alert level classes already come from the class table. The remaining literal frame classes require a
  frame template override; Phase 4 documents this rather than expanding that table.
- Message templates share the alert frame and body snippets. Updating the shared frame reaches flash
  messages and the other package alert call sites without changing each one.

### Integration Points
- `tests/test1/test_messages.py`: update dismissible-message attribute assertions alongside alert tests.
- `tests/test1/golden/`: add and commit a before-change dismissible-alert baseline before implementation.
- `docs/reference/javascript.md`: add the `alert.close(el)` row and update the factory's three-adapter wording.
- `docs/reference/messages.md`: replace the old data-API example and the statement that closing requires
  Bootstrap's bundle with the adapter and core-script requirements.
- `docs/reference/theme.md`: add the short override recipe; distinguish the alert's CSS from the remaining
  Bootstrap dropdown data-API templates.

</code_context>

<specifics>
## Specific Ideas

- Use a compact frame example that changes the CSS classes while retaining `role="alert"` and
  `data-cv-alert-dismiss`; demonstrate the customization seam without inventing another public hook.
- Show the old and new dismiss attributes side by side in the migration example. Recommend the new hook
  on upgrade and explain the legacy Bootstrap path explicitly.
- Missing Bootstrap `Alert` invokes removal inside the default adapter. A custom adapter throwing must
  not trigger core removal or core error logging.

</specifics>

<deferred>
## Deferred Ideas

Additional alert frame class-table keys remain under existing LATER-06. No new deferred capability was
added. Focus management, auto-dismiss, and downstream theme implementation remain outside this phase.

</deferred>

---

*Phase: 04-alert-dismiss-adapter*
*Context gathered: 2026-10-26*
