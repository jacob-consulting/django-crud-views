# Phase 4: Alert dismiss adapter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 04-alert-dismiss-adapter
**Areas discussed:** Frame styling, custom adapter behavior, migration guidance

## Area selection

Offered frame styling, custom adapter behavior, and migration guidance. The user selected **all**.

## Frame styling

### Frame classes

| Option | Description | Selected |
|--------|-------------|----------|
| Keep classes; document override | Limit this phase to dismissal; keys stay under LATER-06. Recommended. | Yes |
| Add class-table keys now | Replace literal frame classes through an expanded public table. | |

**User's choice:** 1 — keep classes and document the override.

### Theme documentation depth

| Option | Description | Selected |
|--------|-------------|----------|
| Short override example | Show custom classes, preserving both dismissal hooks. Recommended. | Yes |
| Brief explanation with links | Describe required hooks and link to the existing frame documentation. | |

**User's choice:** 1 — short override example retaining `role="alert"` and `data-cv-alert-dismiss`.

**Area gate:** Offered moving to custom adapter behavior or discussing frame styling further.
The user selected 1 — move to custom adapter behavior.

## Custom adapter behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Let the error surface | Theme owns closing; no core recovery. Recommended. | Yes |
| Log the error | Core catches the failure, reports it through `console.error`, and leaves the alert in place. | |

**User's choice:** 1 — let the error surface without a core catch, log, or forced removal.
Removal is only the default adapter's fallback when its namespace has no Bootstrap `Alert` component.

**Area gate:** Offered moving to migration guidance or discussing custom adapter behavior further.
The user selected 1 — move to migration guidance.

## Migration guidance

### Migration example

| Option | Description | Selected |
|--------|-------------|----------|
| Compact before/after example | Show new attribute, required scripts, and legacy compatibility. Recommended. | Yes |
| One migration bullet with links | Put detailed guidance only in the JavaScript and messages references. | |

**User's choice:** 1 — compact before/after example.

### Recommendation for copied templates

| Option | Description | Selected |
|--------|-------------|----------|
| Adopt the new hook on upgrade | Explain adapter fallback and legacy compatibility. Recommended. | Yes |
| Change only when needed | Keep the old attribute for Bootstrap; change when switching frameworks. | |

**User's choice:** 1 — recommend adopting the new hook when upgrading.

## Completion gate

Summarized the decisions from all three areas. Offered saving phase context or exploring more gray areas.
The user selected **1 — ready to save the phase context**.

## Agent's Discretion

No product decision was explicitly delegated. Implementation details, test organization, and documentation
wording remain within the locked decisions and existing phase acceptance criteria.

## Deferred Ideas

Additional alert frame class-table keys remain tracked under existing LATER-06. No new deferred idea was added.
