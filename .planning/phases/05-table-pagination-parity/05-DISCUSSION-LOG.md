# Phase 5: Table pagination parity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27
**Phase:** 05-table-pagination-parity
**Areas discussed:** Shared class-key name, navigation label, override compatibility

The user selected all three areas. Each area had one concrete unresolved choice; existing requirements were
carried forward without re-asking. The user selected option 1 for each and then explicitly approved writing context.

## Shared class-key name

Which public class key should control hidden labels in both table and card pagination?

| Option | Description | Selected |
|--------|-------------|----------|
| `pagination:hidden-label` | Describes both uses and matches PAGE-03; recommended | Yes |
| `table:hidden-label` | Original source-plan suggestion; cards would depend on a table-named key | |

**User's choice:** 1 — `pagination:hidden-label`.
**Notes:** Both options defaulted to `visually-hidden`. This settles the discrepancy between requirements and
the older recommendation in the source plan / PROJECT.md.

## Navigation label

What should the table's translated navigation label be?

| Option | Description | Selected |
|--------|-------------|----------|
| `pagination` | Matches the existing card label; recommended | Yes |
| `Table navigation` | Preserves the table's wording and adds translation | |

**User's choice:** 1 — translated `pagination` for both.
**Notes:** Reuse the card msgid.

## Override compatibility

How should previous/next overrides work once disabled ends are displayed?

| Option | Description | Selected |
|--------|-------------|----------|
| Blocks cover both states | Customize enabled and disabled ends; document required availability checks | Yes |
| Keep blocks enabled-only | Preserve invocation behavior; disabled customization needs the outer block | |

**User's choice:** 1 — blocks cover enabled and disabled states (recommended).
**Notes:** The presented tradeoff explicitly required existing overrides to check direction availability before
calling `previous_page_number` or `next_page_number`, and to document that change in migration guidance.

## Context approval

The assistant summarized all three decisions and offered writing context or further discussion.
**User's choice:** 1 — write the context.

## Agent's Discretion

No product decisions were delegated. Routine implementation details remain within the captured contract.

## Deferred Ideas

None — discussion stayed within phase scope.
