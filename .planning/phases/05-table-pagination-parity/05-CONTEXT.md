# Phase 5: Table pagination parity - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring table pagination into parity with card pagination: registry arrow icons, translated hidden labels,
accessible current-page and disabled-end markup, and a shared hidden-label class key (PAGE-01 through PAGE-04;
source plan 3B). Preserve existing django-tables2 block names and document the changed block behavior.

No separate SPEC.md was supplied. This phase changes pagination markup and its theme contract, not filtering,
sorting, pagination algorithms, or form-button rendering. The theme-surface freeze remains Phase 7 work.

</domain>

<decisions>
## Implementation Decisions

### Shared class-key name
- **D-01:** Use `pagination:hidden-label`, default `visually-hidden`, for hidden labels in both table and card
  pagination. This confirms PAGE-03 and supersedes the `table:hidden-label` recommendation in the source plan
  and PROJECT.md. Do not introduce the alternative table-named key for this purpose.
- **D-02:** Both pagination templates must read the shared key through the existing class-table mechanism.
  Changing the key's configured class changes both templates. Preserve default card output.

### Navigation label
- **D-03:** Use the translated msgid `pagination` for the table navigation label, matching the existing card
  navigation label. Do not retain `Table navigation` as the stock table label.

### Override compatibility
- **D-04:** Keep `pagination.previous` and `pagination.next`, but make each block cover both its enabled and
  disabled states. Theme authors must be able to customize disabled ends through those same blocks.
- **D-05:** Existing overrides must check direction availability before calling `previous_page_number` or
  `next_page_number`. Explicitly document this compatibility change in migration guidance; retaining only the
  block names is not sufficient migration guidance. The enabled-only block alternative was rejected.

### Carried-forward scope and acceptance
- **D-06:** Commit a golden of today's paginated table before changing its markup, so history exposes the DOM
  change (PAGE-01). Update the golden with implementation and preserve unrelated/default card goldens.
- **D-07:** Use `page-previous` and `page-next` registry icons with translated hidden `previous` / `next` labels.
  Match the card accessibility structure: current item carries `aria-current="page"`; disabled ends use
  `<a class="page-link" aria-disabled="true">` without a navigable href or focusability. Preserve the existing
  tables2 pagination block names, including `pagination.range` (PAGE-02).
- **D-08:** Record the DOM change under CHANGELOG Breaking and update `docs/migrating-1.0.md` in the same change.
  Update class-key documentation, list-view guidance, and translation catalogs as required by PAGE-04. Reuse
  the existing translated navigation msgid rather than inventing a new table-specific msgid.
- **D-09:** Verify both pagination structures, shared class overrides, translated labels, registry icon
  overrides, and enabled/disabled block overrides. Preserve table query-string handling and page-range
  behavior. Carry forward the project quality gates; downstream theme implementation is outside this repo.

### Agent's Discretion
- No product choice was explicitly delegated. Helper placement, test organization, whitespace management,
  and precise documentation wording remain implementation details within the decisions above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and prior decisions
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, and dependency on settled names before Phase 7.
- `.planning/REQUIREMENTS.md` — PAGE-01 through PAGE-04, including the shared pagination key.
- `.planning/PROJECT.md` — compatibility, public-name stability, documentation rules, and quality gates;
  D-01 supersedes its older table-key recommendation.
- `.planning/phases/02-form-key-grammar/02-CONTEXT.md` — class-key grammar and live key-count documentation guard.
- `superpowers/plans/2026-10-24-concept-review-followups.md` — Phase 3B design and global constraints;
  D-01 settles its key-name choice and D-04/D-05 settle block compatibility.
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — origin of the pagination inconsistency.

### Public contracts and documentation
- `docs/reference/buttons.md` — class-table keys and configuration contract.
- `docs/reference/list_view.md` — table/card pagination guidance.
- `docs/reference/icons.md` — registry icons and standalone rendering.
- `docs/migrating-1.0.md` — DOM migration and the new override availability checks.
- `CHANGELOG.md` — Breaking entry for the pagination DOM change.
- `CLAUDE.md` — repository conventions, including paired Breaking/migration updates.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crud_views/templates/crud_views/snippets/pagination.html`: card pagination already renders registry
  arrows, hidden translated labels, disabled anchors without href, and a non-link active-page span.
- `src/crud_views/lib/button_classes.py`: shared class registry and lookup; hidden-label keys currently
  include context/list/card, while card pagination itself still uses literal `visually-hidden`.
- `src/crud_views/templatetags/crud_views.py`: existing `cv_icon`, `cv_button_class`, and `cv_querystring` seams.

### Established Patterns
- Card navigation already translates `pagination`; table navigation currently hard-codes `Table navigation`.
- Table pagination uses `table.prefixed_page_field` and `cv_querystring` for links and `table_page_range` for
  page ranges. Preserve those behaviors while changing markup.
- Current table previous/next blocks sit inside availability conditionals. The chosen contract moves state
  handling inside those blocks so disabled-end overrides can run too.

### Integration Points
- `src/crud_views/templates/crud_views/table/bootstrap5.html`: table pagination blocks, arrows, active item,
  disabled ends, and translated navigation label.
- `src/crud_views/templates/crud_views/snippets/pagination.html`: replace literal hidden-label classes with
  the shared key without changing default rendered bytes.
- `tests/test1/test_card_order.py`: existing card pagination, query preservation, accessibility, translation,
  icon override, and golden checks to reuse as a reference.
- `tests/test1/golden/card_pagination/`: existing first/second-page card baselines to preserve.
- `tests/test1/golden/`: commit table pagination baselines before implementation.
- `src/crud_views/locale/de/LC_MESSAGES/django.po`: verify existing shared msgids and update catalog references
  and translations where needed.

</code_context>

<specifics>
## Specific Ideas

- One `pagination:hidden-label` class override must affect both table and card arrow labels.
- A `pagination.previous` override runs on the first page too; it must use `table.page.has_previous` before
  obtaining a previous-page number. The equivalent next-page guard applies on the last page.
- The stock disabled arrow remains present and accessible, but cannot navigate or receive keyboard focus.

</specifics>

<deferred>
## Deferred Ideas

None added. The table-named key, separate table navigation label, and enabled-only block behavior were rejected,
not deferred. Form-button rendering and the stability policy remain in their existing later phases.

</deferred>

---

*Phase: 05-table-pagination-parity*
*Context gathered: 2026-10-27*
