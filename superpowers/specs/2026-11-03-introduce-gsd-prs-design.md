# Landing `introduce-gsd` on `main` as per-phase PRs — design

Date: 2026-11-03 · Source prompt: `superpowers/prompts/2027-11-03-introduce-gsd-prs.md`

## Intent

`introduce-gsd` was branched off `main` at `38b0100` (2026-10-24) to try GSD. Phases 01–06 and 06.1–06.6 of
`superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` were built there; phase 7 is still pending.
The branch now needs to land on `main` so that:

- every change on the branch reaches `main` — **nothing gets lost** — as one squashed commit per phase;
- a human reading `main`'s history or the PR list can see what each phase delivered, in short informal prose;
- the issues each phase resolved are closed by the PR that resolved them.

## Facts this design rests on (checked 2026-11-03)

- `introduce-gsd` is 893 commits ahead of `main`; `main` has **0** commits that `introduce-gsd` lacks. Local and
  `origin/introduce-gsd` are identical. `main` is not branch-protected; merge, squash and rebase merges are all enabled.
- Along first-parent history the phases run in order 01, 02, 03, 04, 05, 06, 06.1, 06.2, 06.3, 06.4, 06.5, 06.6.
  Four merge commits exist: `204eff2` and `69e45dc` (sync with `origin/introduce-gsd`; bring in 06.2-01/02 work and
  `d749f85`), `e866318` (phase 06.4, 140 commits) and `63d43ba` (phase 06.6, 84 commits). Every side-branch commit
  is reachable from the tip, so any cut on first-parent history carries them.
- Phase 01's implementation is a single squash commit `f85a92c` on `introduce-gsd`. Its 41 original commits live on
  `origin/feat/label-mode-defaults`; the tree of that branch equals `f85a92c` (including `.planning`), so nothing
  from it is missing.
- Not every commit belongs to a phase. Known examples (the plan produces the complete list):
  - GSD bootstrap before phase 01: `b1c7480..5c7fc1c` (map codebase, init project, research, requirements, roadmap).
  - GSD/tool config: `e87a904`, `06a8b81`, `a2aaafe`, `730c7f5`, `c5205b0`.
  - Cross-AI review docs per phase (`docs: cross-AI review for phase …`) — these belong to the phase they review.
  - Notes/analysis: `8b30de0 pre-1.0` (the analysis doc), `6bef437`, `d749f85`, `dfd1fb3`, `38f49b7`, `ed5c40c`, `6089258`.
  - Example-app / dev chores: `2a6b885` (seed data for phase 05's pagination check), `d8d6653` (Cloudflare tunnel),
    `fdb0795` (example app on port 9000).
  - **Product changes outside any phase**: `26bebac`/`bd31992`/`bd9771d` (quick task `261030-csg`: nested create
    control state follows the URL parent) and `da8133d fix(test): render cascade review destinations without detail
    links`. Quick task `261030-bqk` (`491ae9c`, `2943ec8`) is docs only.
- Issues per phase, from `.planning/ROADMAP.md`: 03 → #262, 06 → #257 (both already closed), 06.1 → #275,
  06.3 → #282, 06.5 → #259, 06.6 → #277, #278, #279, #280. #286 (Guardian identity) and #89 (stability list,
  phase 7) are follow-ups and stay open. Phases 01, 02, 04, 05, 06.2 and 06.4 cite analysis sections, not issues;
  the plan confirms each against the phase's CONTEXT/VERIFICATION files.
- PR #287 (`fix/sdist-allowlist`, off `main`) is open. It edits `CHANGELOG.md` under `### Fixed`, which phase PRs
  also edit.
- Working tree of `introduce-gsd` has uncommitted files: `.codegraph/.gitignore` (modified),
  `superpowers/notes/2026-10-30-phase-6.2-completion-sequence.md`, `superpowers/prompts/2027-11-03-introduce-gsd-prs.md`,
  `.planning/phases/06.6-…/.gitkeep`, `.planning/phases/06.6-…/.review-diagnostics/`, three
  `.planning/research/.cache/*.json`.
- 12 other remote branches carry commits on neither `main` nor `introduce-gsd` (e.g. `feature/transactions-31`,
  `feature/i18n-all-packages-88`, `feat/bootstrap5-modals`, `claude/epic-goldberg-emyokg`). All predate
  `introduce-gsd`.

## Goals

1. One PR per phase (01 … 06.6), merged into `main` in phase order.
2. Each PR description: a short abstract of the phase; one short, informal bullet per plan that changed behaviour
   (skip plans that only add tests or close out the phase); the issues it resolves.
3. Issues the phase resolves are closed by that PR's merge (`Closes #N`); already-closed issues and follow-ups
   are referenced without `Closes`.
4. Administrative commits outside phases (GSD config, notes, planning, example/dev chores) land on `main` directly,
   without a PR; GitHub Action runs triggered by those pushes are cancelled.
5. Non-administrative commits outside phases get their own PR with the same description rules.
6. After the last step, `main`'s tree equals `introduce-gsd`'s tip tree (plus #287), and after each step `main`'s
   tree equals the tree of that step's cut commit on `introduce-gsd`.
7. The per-commit history stays available on `introduce-gsd`, which remains on `origin`.

## Non-goals

- Phase 7 — it isn't built. Work continuing on `introduce-gsd` after the cut-off lands later, by whatever process.
- The 12 older side branches: report them, don't touch them.
- `origin/feat/label-mode-defaults`: its 41 commits are not ancestors of `introduce-gsd` and won't reach `main`;
  their content does, via `f85a92c`. Left alone and listed in the final report with the other side branches
  (my call — their content is on `introduce-gsd`, so it reaches `main` like everything else).
- Rewriting, re-ordering or editing any commit on `introduce-gsd`.
- Making the individual branch commits part of `main`'s history, or adding an archive tag for them (decided against).
- Cleaning up or shrinking `.planning/` (it stays in the repo; #287 keeps it out of published packages).

## Anti-goals (would be failure even if every PR merges)

- Any file content on `main` that differs from the corresponding cut on `introduce-gsd` (other than #287 at the end):
  a lost change, a hand-resolved conflict, or a later step silently reverting something.
- Deleting `introduce-gsd` from `origin` — it is the only place the individual commits live.
- An issue closed by the wrong PR, or a follow-up issue (#286, #89) closed.
- PR descriptions that read like GSD output: plan IDs, gate names, review cycles, evidence paths.

## How it works (decided)

**One squashed commit per segment, built from a cut.** A cut is an existing commit on `introduce-gsd`'s
first-parent history: the last commit of a phase (or of an admin segment). For each segment, the PR branch holds a
single new commit whose parent is the current `origin/main` and whose tree is exactly the cut's tree
(`git commit-tree <cut>^{tree} -p origin/main`). The PR therefore shows exactly that segment's changes, cannot
conflict, and its CI tests the same files as the cut. The PR merges with "Squash and merge"; the squash commit message
is the PR title plus its description.

**Precondition for every step: `main`'s tree equals the previous cut's tree** (`git diff --quiet origin/main
<previous cut>`). Because each new commit takes the cut's whole tree, anything else that landed on `main` in between
would be silently reverted. If the check fails, stop and report. So nothing else merges into `main` during the
landing — that includes the open dependabot PRs and #287.

**Per-commit history stays on `introduce-gsd`.** Each PR description links the original commits of its segment as a
GitHub compare range `<previous cut>...<cut>` on `introduce-gsd`. The branch must not be deleted afterwards
(consequence of having no archive tag).

**Strictly sequential.** Build the next segment's commit only after the previous one merged, on top of the new `main`.

**Direct landing of admin segments**: the same squashed commit (parent `origin/main`, tree of the cut), message
`chore: <what the segment is>` with a link to its compare range, pushed straight to `main`; then cancel the workflow
runs that push started (`gh run list --branch main` → `gh run cancel`).

**Admin and non-phase commits that sit *inside* a phase's run** (between two commits of the same phase on
first-parent history) cannot land separately without splitting the phase or rewriting history. Known cases:
`2a6b885` inside 05, `6089258` inside 06, the `261030-csg` fix and `261030-bqk` docs inside 06.2,
`d8d6653`/`fdb0795`/`da8133d` inside 06.3. They ride along in the phase PR (decision 1 below).

**Admin commits at a boundary** (after phase N's last commit, before phase N+1's first) form their own segment and
land directly, e.g. `b1c7480..5c7fc1c` before phase 01.

**Phase 06.2 / 06.3 overlap.** `5055bff docs(06.3): scope bounded Guardian policy review` sits inside the 06.2 run;
it's planning-only and rides in the 06.2 PR, noted in that PR.

**Working-tree leftovers** are committed to `introduce-gsd` (one admin commit) before the final cut, except the
`.planning/research/.cache/*.json` files, which the plan checks: if they are tool caches they go in `.gitignore`
rather than the repo.

**The cut-off** is `introduce-gsd`'s tip at the time the final segment lands. No new commits go to `introduce-gsd`
while the landing runs; if some do, they become one more segment at the end.

**#287 lands last** (my call, now required). Merged earlier, the next squashed commit — carrying the cut's tree —
would silently undo it. At the end it is updated by merging `main` into `fix/sdist-allowlist` (one `CHANGELOG.md`
conflict, resolved by keeping both sides), then squash-merged like any other PR. No release happens in between, so
nothing ships the bloated sdist meanwhile.

**PR description shape:**

```
## <Phase name>

<2–4 sentence abstract: what changed for a user of the package and why.>

### What's in it
- <one line per behaviour-changing plan, informal, no plan IDs>

### Also in this PR
- <any non-phase commits riding along, one line each — omit when empty>

Closes #A, closes #B · Related: #C

Original commits: <compare link previous-cut...cut>
```

Content comes from each plan's `*-SUMMARY.md`, the phase `CONTEXT.md`/`VERIFICATION.md`, and the commits
themselves, not from memory. PR titles: `Phase <n>: <phase name>`.

**Verification before calling it done:**
- after each merge: `git diff --quiet origin/main <cut>`;
- at the end: `git diff introduce-gsd main` shows only #287's changes;
- every issue in a `Closes` line is closed; #286 and #89 are still open;
- a short report listing the 12 untouched side branches.

## Decided with Alex (2026-11-03)

0. **Squash, one commit per segment; no archive tag.** The individual commits stay only on `introduce-gsd`.
1. **Non-phase commits inside a phase run ride along** in that phase's squashed commit, one line each under
   "Also in this PR". No phase is split. This also applies to the product fixes `261030-csg` (in 06.2) and `da8133d`
   (in 06.3); goal 5 ("own PR") applies only to non-admin commits at a boundary, if any.
2. **Claude merges** each PR once its CI is green, and pushes admin segments to `main` itself. One supervised run.
3. **Red CI stops the landing.** Wait for every check on every PR. If one fails, don't merge, don't add commits:
   pause and report the failure (job, log excerpt, whether it also fails locally at that cut) to Alex, who decides.
   CI has never run on `introduce-gsd` (tests, lint and JS workflows trigger only on PRs to `main` and pushes to
   `main`), so this is the first test of every cut.

## Left to the builder

- Exact cut commits and the full classification of every first-parent commit (phase / admin / product).
- Branch names for the PR heads.
- Wording of each PR description, within the shape above.
