# Phase 06.27 — Source Coverage

No external API integration: this phase extends local Django forms, templates, native controls and the example app. The complete plan/roadmap detector returned detected=false.

## Planning decisions and evidence

- D-01–D-10 are locked. Issue #354 was read live; CONTEXT.md captures the subsequently approved phase scheduling.
- No formal requirement IDs were assigned to Phase 06.27. Each requirements: [] is intentional; issue acceptance and D-IDs provide new-scope traceability. Existing conditional/lifecycle requirements below are preservation obligations.
- Spec-less probe visibly skipped: no requirement IDs to probe. Explicit exclusions remain task acceptance constraints, not silently dismissed predicates.
- Assumption-delta detector returned pluralization/multiple. Primary noun remains ConditionalGroup; decision no-change. ValueToggle specializes ToggleSource; no parallel engine.
- Schema capability listed ORM patterns: no matches. Django remains responsible for the real additive Customer migration, applied in disposable example tests/browser storage.
- Discovery: existing current RESEARCH.md covers external Django semantics; direct source and PATTERNS.md establish implementation seams. No new dependency or missing research input.
- No graph exists. Existing map is advisory; direct source wins.
- Estimate calibration: factor 1, applied=false, sample_count 0, confidence low. Five plans, 12 tasks, five sequential waves; only Plan 01's six-file tracer has an explicitly orchestrator-approved sizing exception.
- No product implementation or acceptance tests ran during planning; prior research baselines are not feature evidence.

## Multi-source audit

| Source | ID | Required feature / constraint | Plan/tasks | Status |
|---|---|---|---|---|
| GOAL | Phase 06.27 | Choice field activates groups through dropdown/radio, shared matches, inactive semantics and explicit/automatic clear | 01–05 | COVERED |
| REQ | Roadmap prose | Complete issue acceptance, real complex example, reciprocal docs, checkbox preservation and finding20 exclusion | 01–05 | COVERED |
| REQ | COND-01/02/03 (preserve) | Exact form ownership, independent disabled baselines, native/canceled reset | 03-01/02, 05-03 | COVERED |
| REQ | COND-04/05 (preserve) | Native default/omitted/disabled persistence, explicit unsupported diagnostics, inherited invariants | 02-01/02, 05-03 | COVERED |
| REQ | FSET-02/LIFE-01/02 (preserve) | Repeat-safe/modal/row lifecycle, actual HTTP evidence, documented contracts | 02-03, 03-01/02, 05-01/03 | COVERED |
| CONTEXT | D-01 | Multiple disjoint groups, multi-value membership and two-of-three shared group | 01-01, 02-01, 03-01/02, 04-01 | COVERED |
| CONTEXT | D-02 | Required active groups, clear inactive on save, browser retention, shared preservation, outside fields | 01-01, 02-01/02, 03-01/02, 04-01, 05-02 | COVERED |
| CONTEXT | D-03 | Single controller, explicit values, distinct controlled fields; reject conflicts | 01-02, 02-01/03 | COVERED |
| CONTEXT | D-04 | ValueToggle shared by policy/layout; legacy strings preserved | 01-01/02, 02-03 | COVERED |
| CONTEXT | D-05 | Disabled > explicit membership/falsy > bounded matrix, nullable/defaulted choice persistence | 02-02, 04-01, 05-01/02 | COVERED |
| CONTEXT | D-06 | Native Select and RadioSelect across initial/edit/change/reset/invalid/modal paths | 01-02, 03-01/02, 04-01, 05-02 | COVERED |
| CONTEXT | D-07 | API, widgets, groups, requirements, clearing, overrides, compatibility and limits docs | 05-01 | COVERED |
| CONTEXT | D-08 | Actual persisted three-option/four-group example, both controls, seeds/discovery, saved detail | 04-01/02, 05-02 | COVERED |
| CONTEXT | D-09 | Docs→real example and example→generated documentation anchor | 04-02, 05-01/02 | COVERED |
| CONTEXT | D-10 | Canonical issue handover and approved scheduling before Phase 7 | 05 objective/truths, all common contracts | COVERED |
| RESEARCH | Token boundary | Immutable normalized tokens, zero, optgroups, standard typed/native model coercion, reject ambiguous coercion | 01-01/02, 02-01 | COVERED |
| RESEARCH | Validation authority | Cleaned-only post-clean activation, invalid/removed keys, disabled trusted data; no recursive cleaning | 01-01/02, 02-01 | COVERED |
| RESEARCH | Static/runtime split | No arbitrary form construction/queries; request-added fields; E311/E312 retained and deduped E313 | 02-01/02 | COVERED |
| RESEARCH | Native choice clearing | Exact text/integer pairs, hooks, plain-form explicit-only, omitted defaults, model validation | 02-02 | COVERED |
| RESEARCH | Safe rendering | JSON attribute escaping, exact prefix/name, both wrapper branches, independent legend hook | 01-01/02, 03-02, 05-01 | COVERED |
| RESEARCH | Browser ownership | Full radio-set listeners, ambiguity/recovery, focus, disabled baselines, reset/cancel, repeat init/unload | 03-01/02 | COVERED |
| RESEARCH | Unsupported boundary | Explicit whole-formset refusal; preserve checkbox skip/purge and non-choice matrix | 02-03, 05-03 | COVERED |
| RESEARCH | Example architecture | One model/shared form/radio subclass, additive migration, permission-aware alternate actions | 04-01/02 | COVERED |
| RESEARCH | Proven evidence | Current-source Django 4.2/5.2/6.0, bounded workers, real fragment and actual app browser, JS drift disclosure | 05-02/03 | COVERED |
| RESEARCH | Security | Server tampering, overlap, metadata injection, trusted disabled policy and purge refusal | All threat models, T-06.27-01–13 | COVERED |
| RESEARCH | Release/docs | Additive changelog, copied template contract, real anchor checks; Breaking requires migration guide | 05-01 | COVERED |

Excluded by approved scope: finding20 product-dependent per-row conditions; new whole-formset value triggers; multiselect/relation/custom-widget controllers; arbitrary predicates/multiple-controller expressions/dependency graphs; broad refactoring; downstream Tabler/model changes. These are exclusions, not unplanned gaps.

## Dependencies and ownership

| Plan | Needs | Produces | Wave | Checkpoint |
|---|---|---|---|---|
| 01 | Existing conditional stack/browser host | Shared descriptor + runnable Select tracer | 1 | None; public API already approved D-04 |
| 02 | 01 descriptor | Conflicts, choice-clear persistence, unsupported boundary | 2 | None |
| 03 | 01 metadata/tracer + completed 02 hashed Python/model inputs | Native radio/shared lifecycle + browser acceptance | 3 | None |
| 04 | 02 server + 03 browser | Real Customer example/migration/seeds/discovery | 4 | None |
| 05 | 04 runnable example | Docs, reciprocal links, real-example evidence, compatibility | 5 | End-of-phase human-check only |

02 and 03 have disjoint writes but shared browser hash inputs. Review R3 therefore serializes Plan 03 after Plan 02; no task-level scheduling or new isolation mechanism is needed. Within each plan tasks remain sequential. R1 adds valid defaults to shared fixture fields so old browser seeds remain compatible.

## Round 1 review incorporation — 66738f9f

R1: required shared-fixture defaults and omitted-field regression (02-02). R2: explicit evidence filename on every existing-runner checker command (01-01, 03-02, 05-03). R3: five sequential waves with stable hash inputs (02→03→04→05). R4: valid persisted wholesale tracer seed and selected-versus-DB assertions initially/reopened (01-01). R5: native blank placeholders remain inactive and excluded from coercion checks, with generated integer-choice regression and docs (01-01/02, 05-01). All five findings are incorporated; no decision or issue acceptance was removed.

