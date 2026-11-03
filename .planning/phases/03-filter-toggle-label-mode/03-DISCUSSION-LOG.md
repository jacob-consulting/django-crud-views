# Phase 3: Filter toggle label mode - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 03-filter-toggle-label-mode
**Areas discussed:** Default inheritance, icon placement, customization contract

## Area selection

Offered default inheritance, icon placement, and customization contract. The user selected **all**.
Existing requirements were carried forward rather than re-asked: three modes, unchanged default markup,
constant translated label, and persisted expanded state.

## Default inheritance

### Target-view default

| Option | Description | Selected |
|--------|-------------|----------|
| No target-view default | Existing maps/button override, then context floor; toggle has no navigation target | Yes |
| Use the current view as target | Also use its singular action default before the floor | No |

**User's choice:** 1 — no target-view default.

### Declared key

| Option | Description | Selected |
|--------|-------------|----------|
| Use the declared key | `FilterContextButton(key="search")` resolves the `search` entry | Yes |
| Always use filter | All filter buttons share the `filter` mode entry | No |

**User's choice:** 1 — use the declared key.

**Area completion:** Offered next area or further inheritance discussion; user selected next area.

## Icon placement

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing placement rule | Both host-compatible icons use button classes; mixed placements use children | Yes |
| Always use child icons in both mode | Uniform child structure, changing host-placement behavior | No |

**User's choice:** 1 — preserve the existing rule in both mode, with a constant visible label.
**Notes:** Label-only mode's absence of icons and icon-swap attributes was carried from the source plan.

**Area completion:** Offered next area or further icon discussion; user selected customization.

## Customization contract

Existing label templates, variants, and whole-button overrides were carried forward. Custom templates receive
resolved `cv_label_mode` and control their markup.

| Option | Description | Selected |
|--------|-------------|----------|
| Compact contract and examples | Configuration, no-target default, three modes, and optional icon hooks | Yes |
| Full template walkthrough | Also supply a complete custom template covering modes and placements | No |

**User's choice:** 1 — compact contract and examples.

## Completion

Summarized the decisions and offered writing the phase context or exploring remaining questions.
**User's choice:** 1 — write the phase context.

## Agent's Discretion

No product decisions explicitly delegated. Routine implementation and test organization remain open within
the chosen behavior and existing requirements.

## Deferred Ideas

None. Rejected alternatives are not backlog items.
