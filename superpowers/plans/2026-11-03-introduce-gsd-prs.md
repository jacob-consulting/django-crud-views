# Landing `introduce-gsd` on `main` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land everything on `introduce-gsd` on `main` as one squashed commit per phase (via PR) or per admin segment
(direct push), closing the right issues, with `main`'s files ending identical to `introduce-gsd` plus #287.

**Architecture:** Every segment ends at a fixed "cut" commit on `introduce-gsd`'s first-parent history. For each
segment a single new commit is built with `git commit-tree <cut>^{tree} -p origin/main`, so it carries exactly the
cut's files on top of the current `main`. Phase segments go through a PR that is squash-merged after green CI; admin
segments are pushed to `main` directly and their workflow runs cancelled. A tree-equality check runs before and after
every segment.

**Tech Stack:** git, GitHub CLI (`gh`), bash.

**Spec:** `superpowers/specs/2026-11-03-introduce-gsd-prs-design.md`

## Global Constraints

- Repo: `jacob-consulting/django-crud-views`; base `main`; source branch `introduce-gsd`; fork point `38b0100`.
- Never rewrite, rebase, cherry-pick or delete anything on `introduce-gsd`; never delete `introduce-gsd` from `origin`.
- Precondition of every segment: `git diff --quiet origin/main <previous cut>`. Postcondition: `git diff --quiet origin/main <cut>`. Either failing → stop and report to Alex.
- Nothing else merges into `main` during the landing (open dependabot PRs and #287 stay open until Task 6).
- PR merges: squash only, subject `<PR title> (#<n>)`, body = PR description.
- Red or failing CI on a PR → do not merge, add no commits; stop and report job name, failing log excerpt, and whether `pytest tests -n auto` also fails locally at that cut.
- Admin direct pushes: cancel every workflow run started by that push.
- Push over HTTPS with gh credentials (SSH has no key in this environment):
  `git -c credential.helper= -c credential.helper='!gh auth git-credential' push https://github.com/jacob-consulting/django-crud-views.git <refspec>`
- Commits Claude creates end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; PR descriptions end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- PR prose: short, informal, for human devs. No plan IDs (`06.3-07`), no gate/review-cycle/evidence vocabulary, no `.planning` paths.
- Only these issues get `Closes`: #275 (06.1), #282 (06.3), #259 (06.5), #277 #278 #279 #280 (06.6). #286 and #89 must stay open.

## Review Focus

1. Something lands on `main` between segments (a dependabot merge, a manual push) → the next squashed commit would silently revert it; the precondition check in `land.sh` must refuse (Task 2 test pins this).
2. A new commit appears on `introduce-gsd` mid-landing (another machine, a hook) → cut table goes stale; Task 1 records the frozen tip and Task 7 checks `introduce-gsd` still points at it.
3. A PR body that accidentally contains `closes #286`/`fixes #89` or a keyword inside prose → wrong issue closed; Task 3's lint greps every body for closing keywords and allows only the listed numbers.
4. GitHub's default squash title (first commit subject) instead of ours → `land.sh pr` passes `--subject` and `--body-file` explicitly; Task 4 verifies the subject of the resulting `main` commit.
5. `gh pr checks --watch` returning before all checks are registered (green with zero checks) → `land.sh` waits until at least one check exists and none is pending.

---

## Segment table (frozen 2026-11-03; first-parent history of `introduce-gsd`)

Range = commits after the previous cut up to and including the cut. "Also" = non-phase commits riding along.

| # | Kind | Cut | Title | Issues | Also in this segment |
|---|------|-----|-------|--------|----------------------|
| S00 | admin | `5c7fc1c` | chore: GSD project bootstrap (codebase map, requirements, roadmap) | – | – |
| P01 | PR | `f85a92c` | Phase 01: Label-mode defaults | related #264 | `06a8b81`, `e87a904` GSD config |
| P02 | PR | `4157643` | Phase 02: Form key grammar | – | `a2aaafe` GSD config |
| P03 | PR | `aab452c` | Phase 03: Filter toggle label mode | related #262 | – |
| P04 | PR | `68d4b30` | Phase 04: Alert dismiss adapter | – | – |
| S04 | admin | `730c7f5` | chore(gsd): disable auto_advance, drop a default reviewer | – | – |
| P05 | PR | `56f4b63` | Phase 05: Table pagination parity | – | `2a6b885` example seed data |
| P06 | PR | `e443376` | Phase 06: Form-button leaf | related #257 | `6089258` review note |
| S06 | admin | `8b30de0` | docs: pre-1.0 before-theme-freeze analysis | – | – |
| P061 | PR | `0c5e816` | Phase 06.1: Cancel form button as a link | closes #275 | – |
| P062 | PR | `6653df0` | Phase 06.2: Request authorization and write integrity | related #282 | `69e45dc`/`204eff2` sync merges (incl. `d749f85`), `491ae9c`/`2943ec8` docs, `5055bff` 06.3 scoping doc, `26bebac`/`bd31992`/`bd9771d` nested-create fix |
| P063 | PR | `76ff1a6` | Phase 06.3: Delete protection and write-boundary integrity | closes #282, related #286 | `d8d6653` Cloudflare tunnel, `fdb0795` example port 9000, `da8133d` test fix |
| P064 | PR | `e866318` | Phase 06.4: Conditional and formset correctness | related #210 (stays open) | – |
| S064 | admin | `6bef437` | docs: update pre-1.0 analysis and phase sequence | – | – |
| P065 | PR | `649d3fe` | Phase 06.5: Remaining presentation contracts and cleanup | closes #259 | `dfd1fb3`, `38f49b7`, `ed5c40c` docs/planning |
| P066 | PR | `17d4aa1` | Phase 06.6: Theme-adoption seams from the Tabler sync | closes #277, #278, #279, #280 | `c5205b0` GSD config |
| S99 | admin | tip after Task 1 | chore: commit planning leftovers, landing spec and plan | – | – |
| #287 | PR | – | existing PR, landed last (Task 6) | – | – |

Previous cut of S00 is `38b0100`. Compare link for a segment:
`https://github.com/jacob-consulting/django-crud-views/compare/<previous cut>...<cut>`.

---

### Task 1: Freeze `introduce-gsd` and commit the leftovers

**Files:**
- Commit on `introduce-gsd`: `.codegraph/.gitignore`, `superpowers/notes/2026-10-30-phase-6.2-completion-sequence.md`, `superpowers/prompts/2027-11-03-introduce-gsd-prs.md`, `superpowers/specs/2026-11-03-introduce-gsd-prs-design.md`, `superpowers/plans/2026-11-03-introduce-gsd-prs.md`, `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/.gitkeep`, `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/.review-diagnostics/`, `.planning/research/.cache/*.json` (siblings of these cache files are already tracked, so they are committed too)

**Interfaces:**
- Produces: `FROZEN_TIP` = the new `introduce-gsd` tip hash (cut of S99), written to `$SCRATCH/land/frozen-tip`.

- [ ] **Step 1:** `git status --porcelain -uall` lists exactly the files above (plus nothing else). If anything else appears, stop and ask.
- [ ] **Step 2:** Verify the cut table is still correct: `git log --first-parent --format=%h 38b0100..17d4aa1` contains every cut in the table, in table order.
- [ ] **Step 3:** Commit: `git add <files above>` then `git commit -m "chore: commit planning leftovers, landing spec and plan"` (with the Co-Authored-By line).
- [ ] **Step 4:** Push `introduce-gsd` (HTTPS helper from Global Constraints); expect `17d4aa1..<new> introduce-gsd -> introduce-gsd`.
- [ ] **Step 5:** `git rev-parse --short introduce-gsd > $SCRATCH/land/frozen-tip`; from here on nobody commits to `introduce-gsd`.

### Task 2: `land.sh` helper (scratchpad, not committed)

**Files:**
- Create: `$SCRATCH/land/land.sh` (`$SCRATCH` = this session's scratchpad directory)

**Interfaces:**
- Produces:
  - `land.sh build <prev_cut> <cut> <msgfile>` → fetches `origin`, checks precondition, prints the hash of `git commit-tree <cut>^{tree} -p origin/main -F <msgfile>`, and checks `git diff --quiet <new> <cut>`. Exit 3 on precondition failure, with message `main differs from <prev_cut>`.
  - `land.sh direct <prev_cut> <cut> <msgfile>` → `build`, push `<new>:refs/heads/main`, then `gh run list --commit <new> --json databaseId -q '.[].databaseId'` (poll up to 60 s for runs to appear) and `gh run cancel` each; postcondition.
  - `land.sh pr <prev_cut> <cut> <branch> <title> <bodyfile>` → `build` (message = title + body), push `<new>:refs/heads/<branch>`, `gh pr create --base main --head <branch> --title <title> --body-file <bodyfile>`, wait for checks (loop on `gh pr checks <n> --json state`: ≥1 check, none `PENDING`/`QUEUED`/`IN_PROGRESS`), exit 4 if any check is not `SUCCESS`/`SKIPPED`/`NEUTRAL`; else `gh pr merge <n> --squash --subject "<title> (#<n>)" --body-file <bodyfile> --delete-branch`; postcondition; prints PR number.
  - `DRY=1` env: `build` only, nothing pushed.

- [ ] **Step 1: Test the precondition refuses a drifted `main`.** In a throwaway clone (`git clone -q . $SCRATCH/land/t && cd $SCRATCH/land/t`), make `origin/main` drift: `git update-ref refs/remotes/origin/main $(git commit-tree 38b0100^{tree} -p 38b0100 -m drift)` and skip fetching via `NOFETCH=1`. Run `NOFETCH=1 DRY=1 land.sh build 38b0100 5c7fc1c msg`. Expected: exit 3, `main differs from 38b0100`.
- [ ] **Step 2: Test the happy path builds the right tree.** In the same clone, reset `refs/remotes/origin/main` to `38b0100`; `NOFETCH=1 DRY=1 land.sh build 38b0100 5c7fc1c msg` exits 0 and `git diff --quiet <printed hash> 5c7fc1c` and `git rev-parse <printed hash>^` = `38b0100`.
- [ ] **Step 3:** Write `land.sh` until both pass. Remove the throwaway clone.

### Task 3: Draft all PR descriptions and admin messages

**Files:**
- Create: `$SCRATCH/land/msg/<segment>.md` for every row of the segment table (S00 … P066, S99).

**Interfaces:**
- Consumes: segment table.
- Produces: one file per segment; for PR segments the file is the PR body; for admin segments it is the commit message.

- [ ] **Step 1:** For each phase segment, read the phase's `*-CONTEXT.md`, every `*-SUMMARY.md` and `*-VERIFICATION.md` under `.planning/phases/<phase dir>/`, and `git log --format='%h %s' <prev>..<cut>` for the ride-alongs. Write the body in the shape below; one "What's in it" bullet per plan that changed behaviour (skip test-only and phase-closing plans); "Also in this PR" from the table's last column, one plain line each, omitted when empty.

```
## <Phase name>

<2–4 sentences: what changed for a user of the package, and why.>

### What's in it
- …

### Also in this PR
- …

Closes #A, closes #B · Related: #C

Original commits: https://github.com/jacob-consulting/django-crud-views/compare/<prev>...<cut>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

- [ ] **Step 2:** Admin messages: subject = table title; body = one sentence on what the segment is, the compare link, and the Co-Authored-By line.
- [ ] **Step 3: Lint all drafts.**
  - `grep -niE '\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b *#[0-9]+' $SCRATCH/land/msg/*.md` → every hit is in a P061/P063/P065/P066 file and names only that row's "closes" issues.
  - `grep -nE '[0-9]{2}(\.[0-9])?-[0-9]{2}\b|\.planning/|cross-AI|gate|cycle [0-9]' $SCRATCH/land/msg/*.md` → no hits outside the compare link.
- [ ] **Step 4:** Show Alex the P01 draft as a sample before Task 4 starts; adjust all drafts if Alex asks for a different tone.

### Task 4: Land S00 … P066 in table order

**Interfaces:**
- Consumes: `land.sh` (Task 2), drafts (Task 3), frozen tip (Task 1).

For each row, in order, with `prev` = previous row's cut (`38b0100` for S00):

- [ ] **Step 1 (admin rows S00, S04, S06, S064):** `land.sh direct <prev> <cut> msg/<row>.md`. Expected: exit 0; `gh run list --commit <new>` shows only `cancelled` runs.
- [ ] **Step 2 (PR rows P01 … P066):** `land.sh pr <prev> <cut> land/<row> "<title>" msg/<row>.md`. Branch names: `land/phase-01`, `land/phase-02`, …, `land/phase-06.6`. Expected: exit 0, PR merged, `git log -1 --format=%s origin/main` = `<title> (#<n>)`. Exit 3/4 → stop, report to Alex, wait.
- [ ] **Step 3 (after each PR row with "closes"):** `gh issue view <n> --json state -q .state` = `CLOSED` for each listed issue; if GitHub didn't auto-close, close it with `gh issue close <n> --comment "Done in #<pr>."`.
- [ ] **Step 4:** Tick the row in this plan.

Rows: S00 · P01 · P02 · P03 · P04 · S04 · P05 · P06 · S06 · P061 · P062 · P063 · P064 · S064 · P065 · P066

### Task 5: Land S99 (leftovers commit)

- [ ] **Step 1:** `test "$(git rev-parse --short origin/introduce-gsd)" = "$(cat $SCRATCH/land/frozen-tip)"`; if not, stop and ask (new work arrived).
- [ ] **Step 2:** `land.sh direct 17d4aa1 $(cat $SCRATCH/land/frozen-tip) msg/S99.md`. Expected: exit 0; `git diff --quiet origin/main introduce-gsd`.

### Task 6: Land #287 last

**Files:**
- Modify (on `fix/sdist-allowlist`, worktree `../django-crud-views-sdist`): `CHANGELOG.md` conflict only.

- [ ] **Step 1:** In the worktree: `git fetch origin && git merge origin/main`. Expected: conflict in `CHANGELOG.md` only; resolve by keeping both sides (our `### Fixed` bullet placed first under the existing `### Fixed`). Any other conflicted file → stop and ask.
- [ ] **Step 2:** `git diff origin/main -- . ':!CHANGELOG.md'` equals the original #287 diff for those files (`git diff 38b0100 738ab3f -- . ':!CHANGELOG.md'`), and the CHANGELOG diff adds only our three lines.
- [ ] **Step 3:** Rebuild and guard: `uv build -o $SCRATCH/land/dist && python3 scripts/check_dist.py $SCRATCH/land/dist` → both `ok`.
- [ ] **Step 4:** Commit the merge (Co-Authored-By line), push the branch, wait for #287's checks green (red → stop and report), then `gh pr merge 287 --squash --subject "fix(packaging): ship only an allowlist in the sdist and guard both distributions (#287)" --delete-branch`.
- [ ] **Step 5:** `git worktree remove ../django-crud-views-sdist`.

### Task 7: Final verification and report

- [ ] **Step 1:** `git fetch origin`; `git diff --stat introduce-gsd origin/main` lists exactly `.github/workflows/lint.yml`, `.github/workflows/publish.yml`, `CHANGELOG.md`, `noxfile.py`, `pyproject.toml`, `scripts/check_dist.py`, `taskfile.yaml`.
- [ ] **Step 2:** `origin/introduce-gsd` still exists and equals the frozen tip.
- [ ] **Step 3:** Issues: #275, #282, #259, #277, #278, #279, #280 `CLOSED`; #286 and #89 `OPEN`.
- [ ] **Step 4:** `pytest tests -n auto` on `origin/main` (fresh checkout in `$SCRATCH/land/final`) passes.
- [ ] **Step 5:** Report to Alex: list of merged PRs and direct commits (hash, title), cancelled runs, and the untouched side branches: `origin/feat/label-mode-defaults` (content landed via `f85a92c`; its 41 commits are not on `main`) and the 12 older branches with unmerged commits (`git for-each-ref` + `git rev-list --count introduce-gsd..<b>`, re-run at report time).
