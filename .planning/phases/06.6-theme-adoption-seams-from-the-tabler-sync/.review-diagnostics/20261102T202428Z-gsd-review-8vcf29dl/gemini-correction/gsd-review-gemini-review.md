# Focused Cycle 8 Review Addendum & Factual Correction

## 1. Executive Summary and Verdict Impact

- **Factual Correction Confirmed:** There is **no `C7-A03` finding, disposition, or shared-checkout sequential-routing amendment** in `06.6-10-PLAN.md` or anywhere in Phase `06.6`. In `06.6-10-PLAN.md`, the Round 7 Review Dispositions Ledger (`06.6-10-PLAN.md:293-309`) contains only two entries: `C7-A01` (`line 299`) and `C7-A02` (`line 300`).
- **Verdict Impact:** Removing the erroneous `C7-A03` / sequential-routing reference **does not change the `no-unresolved-gap` (`LOW` risk) verdict**. All ten plans (`06.6-01` through `06.6-10`) remain preserved from the prior review with **0 unresolved gaps**.

---

## 2. Specific Corrections to the Prior Cycle 8 Review

In the prior Cycle 8 review (which remains preserved in full for Plans `06.6-01` through `06.6-10`), the only reference to `C7-A03` appeared in **`## Cross-Plan Comparison and Overall Risk Assessment` → `### Verification of Cycle 8 Focus Areas` (Item 2)**:

- **Prior Text (to be corrected):**
  > `2. **C5-A01 & C7-A03 (Bounded shared companion commit for 10-01/10-02, core evidence commit for 10-03, temporary-index preservation, and authorized companion write routing):** Verified against the installed gsd-executor contract and 06.6-10-PLAN.md:83-135.`
- **Corrected Text:**
  > `2. **C5-A01, C6-A02, & C6-A03 (Bounded shared companion commit for 10-01/10-02, core evidence commit for 10-03, temporary-index preservation, and recorded companion-root resolution under amended D-11/D-14):** Verified against the installed gsd-executor contract (lines 438-678) and 06.6-10-PLAN.md:72-137, 255, 270, 282-283. No C7-A03 disposition or forced sequential-dispatch mode exists or is required.`

---

## 3. Critical Evaluation of Cycle 7 Adjudication (`06.6-10-PLAN.md` vs. `gsd-executor` Source)

The Cycle 7 adjudication held that `06.6-10-PLAN.md` names a verified external root and uses explicit `git -C` / temporary-index operations under user authorization, so neither an extra permission gate nor forced sequential dispatch is needed. Independently evaluating that claim against `06.6-10-PLAN.md` (`lines 1-313`) and the embedded `gsd-executor` source (`lines 430-750`) confirms the adjudication is sound for six concrete technical reasons:

### 3.1. Recorded Absolute `companion_root` Eliminates Worktree-Relative Sibling Drift (`C6-A03`)
- **Risk under worktree isolation:** When `gsd-executor` runs in an isolated git worktree (`[ -f .git ]`, embedded executor `lines 125-130, 446-461`), its `cwd` is the worktree directory rather than the primary checkout. Resolving `../tabler-test` relative to the worktree's `cwd` would target a nonexistent or wrong sibling path.
- **How `06.6-10-PLAN.md` resolves this without sequential dispatch:**
  - `06.6-10-PLAN.md:72-76`: Every delivery command passes `--delivered-source recorded`, which reads `06-companion-baseline.json` beneath the script's own core root and resolves the canonical absolute `companion_root` plus recorded source hashes. *"No cwd-relative companion operand or inherited shell root variable is required."*
  - `06.6-10-PLAN.md:85-88`: Explicitly instructs the executor that `../tabler-test` is the supplied checkout's relative spelling and that *"an isolated core worktree must resolve the same recorded companion root, not infer a different sibling."*
- **Evaluation:** Because discovery of the companion checkout is anchored to the absolute `companion_root` recorded in `06-companion-baseline.json`, dispatching `06.6-10` in a standard isolated core worktree resolves the exact same external companion directory as dispatching it in the main checkout.

### 3.2. Wave 4 Concurrency Has No Shared-Target Contention on `../tabler-test`
- **Risk under parallel wave dispatch:** If two plans in the same wave mutated `../tabler-test` concurrently, parallel worktree executors would race on the external repository.
- **How `06.6-10-PLAN.md` resolves this:**
  - `06.6-10-PLAN.md:4-6`: Plan `06.6-10` runs in `wave: 4` with `depends_on: ["06.6-07"]`.
  - Upstream Plan `06.6-06` (Wave 2) and Plan `06.6-07` (Wave 3) treat `../tabler-test` as read-only and have already completed before Wave 4 begins.
  - The only other Wave 4 plan (`06.6-08`) touches core documentation and doc tests (`docs/*`, `CHANGELOG.md`, `tests/test1/test_*_docs.py`) and never accesses `../tabler-test`.
  - Downstream Plan `06.6-09` runs in Wave 5 after `06.6-10` finishes (`06.6-10-PLAN.md:229-230`).
- **Evaluation:** `06.6-10` is the sole writer to `../tabler-test` in Wave 4. Forced sequential execution of Wave 4 would provide zero additional concurrency protection for `../tabler-test`.

### 3.3. Executor Step `0a` (`cwd-drift assertion`, `#3097`) Is Preserved
- **Executor contract (`lines 441-462`):** In worktree mode (`*.git/worktrees/*`), Step `0a` verifies `git rev-parse --show-toplevel` matches `$WT_GIT_DIR/gsd-spawn-toplevel` before staging, failing if a prior `Bash` call `cd`'d out of the core worktree.
- **Plan 10 behavior (`06.6-10-PLAN.md:85-86, 105-114, 174, 196-197, 224`):**
  - `06.6-10-PLAN.md:85-86` keeps the executor's `cwd` in core throughout execution.
  - All companion git commands use `git -C "$COMPANION_ROOT"` (`lines 105-114`), and all four `<verify><automated>` commands (`lines 174, 196, 197, 224`) execute from the core root.
- **Evaluation:** Step `0a` never trips in worktree mode because `cwd` never leaves the core worktree.

### 3.4. Executor Step `0b` (`absolute-path safety`, `#3099`) vs. User-Authorized External Delivery
- **Executor contract (`lines 464-480`):** Step `0b` is a worktree anti-drift guard stating: *"Absolute paths constructed from prior `pwd` output (orchestrator's cwd) will resolve to the **main repo**, not the worktree — silently writing files to the wrong location"* (`lines 466-467`), checking `[[ "$ABS_PATH" != "$WT_ROOT" && "$ABS_PATH" != "$WT_ROOT/"* ]]` (`line 473`).
- **Critical evaluation of why forced sequential routing was a false remedy and why Plan 10 has no gap:**
  1. **Sequential routing would not put `../tabler-test` inside `$WT_ROOT`:** Even in the main core checkout, `WT_ROOT` (`git rev-parse --show-toplevel`) is `/home/alex/projects/alex/django-crud-views`, whereas the sibling companion is `/home/alex/projects/alex/tabler-test`. Thus `$ABS_PATH != "$WT_ROOT/"*` is true in *both* worktree and main-checkout modes.
  2. **Explicit user authorization and patch materialization (`06.6-10-PLAN.md:36-38, 42, 80-81, 104-122, 145-153`):** The user explicitly amended `D-11`/`D-14` (`lines 16, 42, 145, 255`) to authorize modifying and locally committing the sibling `../tabler-test` repository in Plan 10, which takes precedence over generic skill heuristics aimed at preventing accidental main-repo drift. Moreover, `06.6-10-PLAN.md` materializes the verified companion changes from `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/07-tabler-adaptation.patch` (`lines 36-38, 105-108, 145-152`) and commits them via `git -C "$COMPANION_ROOT"` with a private `GIT_INDEX_FILE` (`lines 104-122`), while all core-owned files (`10-companion-delivery.json`, `07-TABLER-HANDOFF.md`, `06.6-10-SUMMARY.md`) live inside `$WT_ROOT` under relative `.planning/...` paths (`lines 142, 181, 202, 311`).

### 3.5. Executor Step `0` (`Pre-commit HEAD safety assertion`, `#2924` / `#3819` / `#4799`) and Step `0c` (`#3968` Ledger)
- **Executor contract (`lines 482-516, 540-548, 636-647`):**
  - Step `0` checks that the core repository `HEAD` is not detached (`lines 485-490`), not on a protected branch (`lines 492-504`), and (when `[ -f .git ] && [ "$SEQUENTIAL" != "true" ]`) is on a per-agent worktree branch matching `^((worktree-)?agent-|worktree-wf_)[A-Za-z0-9._/-]+$` (`lines 508-515`).
  - Step `0c` and `<summary_creation>` record `_GSD_LEDGER="$(git rev-parse --git-dir)/gsd-plan-head-before-{phase}-{plan}"` (`line 543`) and require `COMMITS_ACTUAL=$(git rev-list --count ${PLAN_HEAD_BEFORE}..HEAD)` (`line 640`) to be non-zero when task work is committed.
- **How `06.6-10-PLAN.md` aligns with both:**
  - In standard worktree dispatch, core `HEAD` is already on the per-agent worktree branch, so Step `0` passes on core commits (`10-03` and the final metadata commit) with `SEQUENTIAL=false` (`lines 508-515`).
  - Tasks `10-01` and `10-02` form a single shared companion commit boundary (`06.6-10-PLAN.md:93-98`, parallel to `01-01`/`01-02`), executed via `GIT_INDEX_FILE=... git -C "$COMPANION_ROOT" commit -m "feat(06.6-10): deliver verified Tabler theme adoption"` (`lines 104-114`) without changing branches in either repo (`line 91`).
  - Task `10-03` creates the core commit containing `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json` and `07-TABLER-HANDOFF.md` (`lines 97-100, 127-129, 231-233`), advancing core `HEAD` from `gsd-plan-head-before-06.6-10` so `actuals.commits` (`lines 132-135`) and `gsd_run check evaluation-scope --plan 06.6-10 --commits-only --raw` (`lines 133-135, 232-233`) both succeed.

### 3.6. Temporary-Index Isolation and Prohibitions (`<destructive_git_prohibition>`, Executor `lines 559-605`)
- **Executor contract (`lines 559-605`):** Strictly prohibits `git clean`, blanket `git checkout -- .` / `git restore .`, `git reset --hard`, and `git stash` (`lines 567-588`).
- **How `06.6-10-PLAN.md` complies (`lines 102-125`):**
  - Uses a private temporary `GIT_INDEX_FILE` initialized via `git -C "$COMPANION_ROOT" read-tree "$COMPANION_HEAD_BEFORE"` (`line 105`), stages only the verified patch hunks via `git -C "$COMPANION_ROOT" apply --cached` (`lines 106-107`), checks the staged diff against the 5-file (+1 conditional `formactions.html`) allowlist (`lines 108-111`), commits with the temporary index (`lines 113-114`), and reconciles the live index via a second temporary copy with `git apply --cached --3way` installed atomically under `index.lock` (`lines 116-120`).
  - Explicitly forbids resetting or stashing user work (`lines 121-122`: *"never reset or stash someone else's work"*), preserving dirty `example/config/settings.py` (`lines 17, 146-147`) and any unrelated staged/unstaged changes byte-for-byte.

---

## 4. Updated Unresolved Concern Count and Final Verdict

### Unresolved Executable Gaps
- **HIGH:** 0
- **MEDIUM:** 0
- **LOW:** 0

### Final Verdict
**NO UNRESOLVED GAPS (`LOW` overall risk)** — Correcting the nonexistent `C7-A03` / sequential-routing assertion leaves the full ten-plan review intact and confirms `06.6-10-PLAN.md` is executable as written under the installed `gsd-executor` contract.
