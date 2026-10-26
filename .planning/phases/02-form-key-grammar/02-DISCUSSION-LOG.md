# Phase 2: Form key grammar - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 02-form-key-grammar
**Areas discussed:** Kinds versus variants, validation feedback, the documented contract

## Area selection

The user selected **all** three offered areas: kinds versus variants, validation feedback, and the documented
contract. Discussion used text questions. No automatic defaults were substituted for user answers.

## Kinds versus variants

| Option | Description | Selected |
|--------|-------------|----------|
| A: Keep form kinds | Preserve the five role keys and slot= API; add optional mode suffixes | Yes |
| B: Use variants everywhere | Use form:primary/form:secondary/etc.; migrate shipped keys and the adapters' API | No |

**User's choice:** 1 (A).
**Notes:** Before choosing, the user asked for a pros/cons comparison. The comparison covered role versus visual
importance, independent styling, repeated theme CSS, compatibility, the remaining structural-slot exceptions,
and identical mode-key fallback semantics. The recommendation was A.

### Mode coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, uniformly | All five kinds accept icon, both, and label; Phase 6 handles missing icons | Yes |
| Restrict modes by kind | Specify invalid kind/mode combinations | No |

**User's choice:** 1.

### Area completion

Offered: move to validation feedback (recommended), or discuss the grammar further.
The user selected 1 after the summary: variants for context/list/card actions, kinds for forms, no mode suffix
on structural slots.

## Validation feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Keep existing feedback | Unknown keys point to docs; invalid modes name the mode and list valid modes | Yes |
| Add form-specific guidance | List valid kinds and explain why structural slots cannot take modes | No |

**User's choice:** 1.
**Notes:** Both options retained W362 warning severity and the agreed valid grammar.

### Area completion

Offered: move to documentation (recommended), or discuss validation further. The user selected 1.

## The documented contract

| Option | Description | Selected |
|--------|-------------|----------|
| Compact rule with examples | Canonical grammar table, valid/invalid examples, one form-mode fallback example | Yes |
| Minimal paragraph | State meanings and mode eligibility; rely on existing table/fallback documentation | No |

**User's choice:** 1.
**Notes:** Both options included correcting and testing the quoted default-key count, already required by KEYS-04.

## Completion

After the three-area summary, offered: write Phase 02 context (recommended), or explore another gray area.
The user selected 1, authorizing the final context and discussion log.

## Agent's Discretion

No product decisions explicitly delegated. Implementation mechanics and exact wording remain within the agreed
requirements and decisions.

## Deferred Ideas

None added. Phase 6 retains form rendering and missing-icon checks. Rejected alternatives are recorded above.
