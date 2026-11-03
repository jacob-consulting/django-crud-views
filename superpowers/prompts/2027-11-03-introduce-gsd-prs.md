At some point I've branched `introduce-gsd` off `main`.
This was due to experimentally introduce gsd-code to my workflow.

With that then I've implemented most of `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md`
in phases 01 to 06, and 06-01 to 06.06 with phase 7 from the doc still pending.

You can distinguish work the phases by their commits.

There may be commits in between phases to `introduce-gsd` which also matter.

What I want you to do: create a spec, then a plan to
- create a PR for each phase to land on main
- for each PR
  - create a good PR message containing
    - an abstract about the phase
    - details that have been implemented for the plans
      - the audience is human devs, so keep each item short and informal
      - skip if a plan is only for testing or finishing a phase
    - add issues that were done to the PR
  - close associated issues
- do not miss commits to `introduce-gsd` that do not match a phase
  - if that is administrative or informal work then just merge it to main
    - if so you can cancel any GH actions triggered by that
  - if not, also create a PR for that following the same rules for PR content

Objectives:
- nothing on the branch must get lost
- so check for features that a re not on `introduce-gsd`

Judge my idea. What are pros/cons over just squashing the whole branch to main vs doing the PR cleanup.
Find any gaps. Nothing must geet lost.
Be honest, don't guess.