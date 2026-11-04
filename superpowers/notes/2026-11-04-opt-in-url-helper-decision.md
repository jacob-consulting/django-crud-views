# Decision: opt-in URL helper; retire integrated phase 06.10

Date: 2026-11-04. Status: maintainer decision; no implementation authorized by this record.

The maintainer chose an opt-in, request-free URL helper, then asked to file an issue for it and remove the entire integrated phase. The maintainer also required the planning and discussion documents, including those on `claude/lucid-knuth-x5ity9`, to reach `main`.

## Reasons given by the maintainer

- A self-contained module can be understood and maintained independently.
- Adoption can proceed step by step and prove useful in downstream projects.
- Existing URL machinery already works in those projects; new traversal or permission-query costs should not be imposed on it.
- The integrated design grew beyond the complexity the maintainer wants to own. The current URL machinery was developed by the maintainer and remains explainable to them.

Maintainability by the maintainer is a constraint on the solution, including when a more general implementation could be tested successfully.

## Decision and scope

1. [Issue #314](https://github.com/jacob-consulting/django-crud-views/issues/314) tracks the smaller opt-in helper as unscheduled backlog work. It has no 1.0 or Phase 7 dependency.
2. The integrated phase 06.10 is cancelled before implementation. Its active phase directory, execution entry, requirements, dependency edges, and current-state pointers are removed.
3. Existing URL builders and rendering/permission paths retain their behavior and performance. The helper requires explicit adoption. No ambient destination-context machinery or broad migration of callers is authorized.
4. The helper's exact API, initial supported relation subset, and error contract remain undecided. The retired phase's D-01–D-16 entries and six plans are historical research, not requirements automatically inherited by #314.
5. #311's integrated proposal is superseded by #314. The confirmed permission/visibility bugs in [#312](https://github.com/jacob-consulting/django-crud-views/issues/312) remain open for separate scoping; cancellation does not mean they are fixed. They are not retained as an implicit obligation to execute the retired phase or a dependency of Phase 7.
6. Phase 7 is the next active phase. Its remaining maintainer decisions are still required; this decision does not approve its design or start its implementation.

A generated URL is not evidence of authorization or M2M membership. Explicit parent context can be required when the supported object relation cannot establish a unique route. An object also cannot select among multiple ViewSets for its model: destination selection remains explicit.

## Consequences for DataPanel and navigation

The historical DataPanel design assumes existing row actions gain object-derived URLs automatically after #311. That does not follow from an opt-in helper. Its access formula also needs the review's corrections. Reconsider these assumptions before planning DataPanel; this decision does not approve a replacement design.

The navigation exploration's prerequisite brief remains useful historical context, but it does not authorize reviving the cancelled integrated phase. Its request-free URL needs can evaluate the opt-in helper, and its permission requirements need their own explicit scope.

The helper may simplify downstream hand-written links. It does not by itself add a cross-ViewSet table-column target or success-redirect target, so it does not close tabler-test finding 27 in full.

## Preserved documents

- [Navigation concept exploration](2026-11-02-navigation-concept-exploration.md), already present on main, including its original decisions and prerequisite brief.
- [DataView concept exploration](2026-11-04-dataview-concept-exploration.md), imported from `claude/lucid-knuth-x5ity9` at `8b5e8a294910143d40410d34574f55cdc196ebe1`.
- [DataPanel design](../specs/2026-11-04-datapanel-design.md), imported from the same commit.
- [Original review request](../prompts/2026-11-04-review-datapanel-and-prerequisites.md), imported from the same commit.
- [Critical review and alternatives comparison](2026-11-04-datapanel-and-prerequisites-review.md), including actual test results and their limits.
- [Retired phase archive](../archive/2026-11-04-phase-06.10-object-derived-nested-urls-and-link-access-parity/README.md): full discussion log, context, research, patterns, six plans, reviews, validation strategy, diagnostic evidence, and pre-retirement planning snapshots.

The imported exploration and design have a status notice; their original text remains unchanged below it. Archive provenance records source commits and SHA-256 hashes. Historical statements such as “ready to execute” or “must land before Phase 7” are preserved as evidence and are superseded by this decision.
