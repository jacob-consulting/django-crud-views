# Audit Follow-up Roadmap

*Date: 2026-06-24 · Scope: roadmap only · Audited baseline: v0.7.1 (main)*

## What this document is

A **prioritization and release-sequencing roadmap** for the open follow-up issues left
behind by the 2026-06-10 repository audit (`AUDIT.md`). It records *what order to tackle them
in and why* — it is **not** an implementation spec.

Each release named below gets its **own** brainstorm → spec → plan → implementation cycle when
work on it begins. This document is the durable decision record those per-release specs link
back to; it deliberately does not design any issue's API or enumerate its sub-tasks.

## Background

`AUDIT.md` (Phase 4) is marked **ALL MILESTONES COMPLETE** (2026-06-10). Milestones 0–3 were
delivered across PRs #20–#36, and the leftover work was triaged into GitHub issues #27–#34.
Since then #29, #30, #32 (and the related #52, #56) have shipped. What remains open from the
audit lineage, plus the formsets follow-up split out of #29:

- **#27** — Support view-level context buttons in `cv_get_context_button` (+ `FilterContextButton` polish)
- **#28** — Expand Django system checks
- **#31** — Workflow: configurable transaction behavior around transitions
- **#33** — Harden `ViewSet.default_permissions` codename parsing
- **#34** — Deprecate `CrispyModelViewMixin` alias
- **#55** — Formsets: revisit `parent_form` handling / remove placeholder parent-required validation

All six are S–M effort, low–medium risk. None are blockers; the library is healthy.

## Decisions driving this roadmap

1. **Ranking lens: user-facing value first.** Effort and risk are tie-breakers, not the
   primary sort.
2. **Output is a roadmap, not code.** No implementation this cycle.
3. **Small, focused, themed releases** — matching the project's existing cadence
   (0.6 → 0.7 → 0.7.1) and CHANGELOG-driven release flow.

## Value-first ranking

| Rank | Issue | User-facing value | Effort | Risk | Rationale |
|------|-------|-------------------|--------|------|-----------|
| 1 | **#27** view-level context buttons (+`FilterContextButton` polish) | High | M | Low-Med | Real ergonomics win — declare buttons per-view, not just per-ViewSet; completes the `lib/view/base.py:276` stub. Continues the context-button subsystem recently extended with `SiblingContextButton` and `cv_context_url`. |
| 2 | **#28** expand Django system checks | High | M-L | Low | System checks are a documented selling point; catching misconfig at startup saves adopters debugging time. Caveat: a *basket* of ~7 sub-checks — needs scoping. |
| 3 | **#55** formsets `parent_form` cleanup | Med | S | Low | Removes an always-on, untested validation and the `"Child TODO requires…"` placeholder a real formset user could hit. Direction already decided (Option 1 in the #55 issue). |
| 4 | **#34** deprecate `CrispyModelViewMixin` alias | Med | S | Low | User-facing (public name in docs/examples/downstream) but "negative" value — warns rather than delights. API hygiene before eventual removal. |
| 5 | **#31** workflow transaction config | Med (narrow) | S-M | Med | Genuine value but workflow-extension audience only, so narrower reach. The transaction-semantics + hook-placement change is the most behavior-sensitive of the six. |
| 6 | **#33** harden `default_permissions` codename parsing | Low | S | Low-Med | Mostly invisible — only bites edge-case model names where the model string appears inside an action. Pure internal robustness. |

## Release plan

Four small, themed releases, in value-first order:

| Release | Theme | Issues | Bump | Notes |
|---------|-------|--------|------|-------|
| **v0.8.0** | Context buttons | #27 | minor | Headline feature: view-level context buttons + `FilterContextButton` label/permission polish. Self-contained in the context-button subsystem. |
| **v0.9.0** | Startup safety | #28 (scoped) | minor | Scope to high-value sub-checks: `cv_extends` template check, formsets/polymorphic config checks, reactivate E203 `ContextActionCheck`, workflow dependency checks. Leave low-value items (e.g. per-theme AppConfig wiring) as stretch. Split into 0.9/0.10 only if it grows. |
| **v0.10.0** | Hardening & cleanup | #55 + #34 + #33 | minor | Bundle the three small, low-risk items: remove the `parent_form` placeholder validation (Option 1), add the `CrispyModelViewMixin` deprecation warning + docs, harden codename parsing. |
| **v0.11.0** | Workflow transactions | #31 | minor | Isolated **on purpose**: the only Medium-risk item (transaction semantics + hook placement) and workflow-only audience — gets its own focused release + CHANGELOG note rather than riding in the cleanup batch. |

### Packaging sub-decisions

- **#31 is isolated** into its own release because of its risk profile, not its size.
- **#28 ships as one scoped release**, not pre-split — with an explicit out to split if it balloons.
- **#55/#34/#33 are batched** because each is S-effort and low-risk; one cleanup release is more efficient than three.

### Alternative considered (rejected)

Collapse to **two** releases: `v0.8.0 = #27 + cleanup bundle (#55/#34/#33)`,
`v0.9.0 = #28 + #31`. Rejected: fewer cycles but larger changelogs, and it lets #31's risk
ride alongside the system-checks work instead of being isolated.

## Per-release dependencies and notes for the future specs

- **#27** — when specced, decide the precedence between view-level and ViewSet-level buttons
  (the stub at `base.py:276` currently only consults ViewSet-level), and whether
  `FilterContextButton` gains label templating + a permission check.
- **#28** — the per-release spec should enumerate exactly which checks ship and their stable
  IDs; coordinate with the existing check ID scheme (E1xx/E2xx).
- **#31** — behavior change: the per-release spec must define the config surface (setting vs.
  per-view attribute) and call the transaction-behavior change out in the CHANGELOG; re-evaluate
  whether transition logic moves from `cv_form_valid_hook` to `cv_form_valid`.
- **#34** — deprecation must use a proper `DeprecationWarning` + docs note; do not remove the
  alias in the same release.
- **#55** — direction is pre-decided (Option 1: remove the rule, keep `parent_form` as a
  documented extension point). The per-release spec just needs the doc + comment wording.
- **#33** — consider relocating the property and whether to make the cached DB lookup lazy
  (relates to audit task 3.6).

## Non-goals

- No implementation, no API design, no code in this cycle.
- Version numbers above are the *intended* sequence; they are not commitments and may absorb
  unrelated patch releases (e.g. a v0.7.x bugfix) in between.
- Issues already closed (#29/#30/#32) and non-audit work are out of scope.

## Definition of done (for this roadmap)

This document is committed, the six open issues are accounted for with a target release and
rank, and the sequence is approved by the maintainer. Execution proceeds release-by-release,
each starting its own brainstorm/spec/plan cycle.
