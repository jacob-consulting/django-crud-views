---
date: "2026-10-30 06:23"
promoted: false
---

Recommendation captured at the user's request ("note this") after discussing convergence versus focused follow-up phases for Phase 06.2 plans 07–09:

**I’d handle the deferred findings in focused follow-up phases, before Phase 7 freezes the affected contracts.** A convergence run could improve plans 07–09, but it would not close findings deliberately excluded from their scope.

The convergence workflow reviews and revises plans. Three cycles is a maximum, not a guarantee that the design or implementation is correct.

There are two separate concerns:

| Concern | Best treatment |
|---|---|
| Plan 08’s deletion/error-handling complexity | Resolve within 08; validate with its real-commit tests and review the implementation. |
| Deferred authorization, formset and policy findings | Give each coherent topic explicit scope, acceptance criteria and its own implementation work. |

My recommended sequence:

1. **Execute 07–09**, keeping their current scope. Plan 08 must prove that it never reports “deletion blocked” after deletion has committed. That cannot be deferred.
2. **Review the resulting implementation**, particularly plan 08. Concrete code and transaction-test evidence will be more useful than repeatedly refining detailed prose.
3. **Triage the remaining findings into focused phases before the freeze.** Group related issues—for example, parent-aware authorization/state; formset indexing and slug support; Guardian content-type consistency. Small diagnostics or constant-mutability fixes need not each become a phase.
4. **Explicitly decide policy questions.** The unfiltered aggregate policy and unclassified AUTH-06 probe need a clear decision or acceptance criterion; additional review cycles alone won’t supply that.

One qualification: the final revised plans passed the internal checker, but haven’t had another external review since those revisions. **One fresh external review is reasonable for extra assurance**, especially for 08. I wouldn’t make three more cycles a prerequisite unless that review finds concrete blockers.

Also, my earlier “no remaining issues” meant **no remaining plan-checker findings**. The tracked implementation defects and accepted deferrals are still open.
