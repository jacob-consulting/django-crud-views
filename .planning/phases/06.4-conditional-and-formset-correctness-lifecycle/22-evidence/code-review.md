---
phase: 06.4-conditional-and-formset-correctness-lifecycle
plan: "22"
reviewed: 2026-11-01T19:42:33Z
actor: /root/execute_22/code_review
agent_type: gsd-code-reviewer
model: gpt-6-astra
reasoning_effort: high
model_attribution: dispatch configuration confirmed by executor; runtime not independently introspected
depth: deep
source_sha256: d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490
runner_sha256: dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5
packet_sha256: 717f3495fbf3a11c4a23f037bece1136727082314854ad3fd371b56ffce40ab0
files_reviewed: 2
files_reviewed_list:
  - .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py
  - .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
original_findings:
  CR-01: closed-bounded
  CR-02: closed-bounded
  CR-03: closed-bounded
  CR-04: closed-bounded
  CR-05: closed-bounded
  WR-01: closed-bounded
  WR-02: closed-bounded
  WR-03: closed-bounded
  WR-04: closed-bounded
open_findings: [WR-05]
remaining_gap: G6
human_checks:
  H1: pending
  H2: flagged-unverified
---

# Plan 22 independent code review

The original WR-03/04 counterexamples are repaired. All eight independent real CLI executions of those four mutations rejected at their intended predicates. G1–G5 and WR-01/02 retain their original bounded closures through complete source continuity, source/case inspection and the focused executions below. One additional numeric-input robustness warning remains. G6's original false-acceptance defects are closed; G6 remains open for WR-05's rejection-diagnostic defect. This does not allege that the current acceptance packet is corrupt or that the new counterexample is accepted.

This is a new independent applicability assessment by `/root/execute_22/code_review`, typed `gsd-code-reviewer`, using the dispatch-confirmed `gpt-6-astra/high` configuration. It fulfills the plan22 code-review lane. The original reviewer/source/time remain historical facts. The reviewer followed repository AGENTS.md/CLAUDE.md and the gsd-code-review guidance; reviewer-specific agent skills were empty and no project `.codex/skills` or `.agents/skills` directories were present. No structural pre-pass was supplied.

Both changed checker files were read completely. Deep analysis traced CLI parsing → strict JSON loading → aggregate/refresh validation → gate/browser/control validation, and handoff → bound packet → the same validators. Context included plan22, summaries20/21, applicability21, original19 code/security reports, canonical REVIEW, origin18 and current21 packets/manifests, and the actual conditional/modal artifact records. Selected unchanged product/test call chains were inspected for continuity; this is not a new full-source product audit. The explicit plan scope includes the checker sources under `.planning`, overriding the generic planning-file exclusion. Existing ignored browser images were inspected only as explicitly requested evidence artifacts.

The checkout root was asserted before the first write. Only this report and diagnostics under `22-evidence/code-controls/` were authored. Native Read/Write tools were unavailable; source reads used the shell and authored files used the available patch tool, with diagnostic programs writing only their owned observations/fixtures. No source, canonical report, shared tracking, handoff, original packet or screenshot was edited, staged or committed. No install, server, browser capture, full product matrix or complete 62-test rerun occurred.

## Narrative Findings (AI reviewer)

### WR-05: Oversized numeric glyph observations escape the rejection diagnostic boundary

**Classification:** WARNING  
**Disposition:** Open.  
**File:** `/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py:987`  
**Related:** `main()` exception boundary at line 1832; capture numeric regressions in `15-evidence/test_runner.py:580-602`.

**Issue:** The glyph validator allows JSON integers into `math.isfinite()`. Python converts an integer to a float there; a valid JSON integer such as `10**400` raises `OverflowError`. The CLI does not catch that exception. A copy of the actual current packet with only stock `gap-ambiguity.captures[0].icons.glyphs[0].width` set to that value causes both `--check` and `--check-handoff` to emit an uncaught traceback ending `OverflowError: int too large to convert to float`, with exit 1 and empty stdout. The expected `MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` diagnostic is absent. This degrades the explicit malformed-observation/error contract and prevents callers from distinguishing this validation rejection from a crashed checker using the promised diagnostic. It remains fail-closed: no green output or readiness bypass was observed.

**Independent proof:** `code-controls/boundaries.py` performs the one-field mutation, writes the copied packet and current sidecar, rebinds a copied pending handoff to its actual hash, then invokes the unchanged runner through both entry points. Full commands, UTC windows and both raw tracebacks are in `code-controls/boundary-outcomes.json`, records `overflow-glyph:check` and `overflow-glyph:handoff`. These observations are separate from the historical self-test gate.

**Fix:** Reject overflowing numeric conversion inside the observation predicate, preserving its diagnostic, for example:

```python
def positive_finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False
```

Use that helper for width/height and add a bounded real CLI regression for the oversized integer through aggregate and handoff. Do not merely turn the traceback into an unrelated generic error. A runner/test fix changes the source digest: refresh the affected checker self-test, Ruff and corruption-control evidence through plan21's bounded refresh, recheck retained gate/source continuity and current captures, and rebind current reports/handoff. The 17 product/browser gates may remain retained only if the complete two-file applicability rule still holds. No fix was applied by this reviewer. Security impact/severity belongs to the separate auditor.

## Source-cited dispositions

Paths in this section are relative to the repository root; `runner` means the reviewed `15-evidence/run.py` above.

| Finding / original classification | Current independent disposition and evidence |
|---|---|
| CR-01 / G1 — BLOCKER | **Closed, bounded; preserved.** `src/crud_views/lib/formsets/render_tree.py:202-263` reapplies authorized identity/edit-only policy after native validation and deduplicates in the current error cache. `formsets.py:365-383` performs both validity traversals; `views/mixins.py:41-57` gates the atomic save. Inspected direct reclean, valid-before-invalid HTTP and late sibling/child reclean assertions at `test_formsets_policy.py:298-338` and `test_formsets_validation_gate.py:90-146`; the 12 selected cases passed freshly. This does not cover arbitrary consuming-app mutation after final validation. |
| CR-02 / G2 — BLOCKER | **Closed, bounded; preserved.** `vitest.config.js:6` and `vitest.integration.config.js:6` separate ordinary JS and the required Python bridge. `.github/workflows/js.yml` remains Node-only. Inspected `tests/js/runtime-contract.test.js:18-104`: clean copy without `.nox`/`.venv`, Node-only PATH, exact ordinary inventory and missing/invalid bridge interpreter failures. Current retained JS347/integration2 records and all source hashes remain exact. No fresh clean-copy or hosted CI run is claimed by this reviewer. |
| CR-03 / G3 — BLOCKER | **Closed, bounded; preserved.** `formset.js:10-23,265-279,328-330` derives native DELETE eligibility from the owning bound prefix and initial count. Inspected actual-field template rule and `tests/js/formset.test.js:531-551` ordered/unordered extra Add/submit assertions. Fresh selected JS cases passed; actual stock/native `gap-capability` browser records retain native omission, Add and persisted order assertions. |
| CR-04 / G4 — BLOCKER | **Closed, bounded; preserved.** Same stable-prefix helper controls deletion; visual row position controls movement. Inspected moved/inserted initial and forged-extra direct/delegated cases at `formset.test.js:552-590`. Fresh selected JS cases passed, including the original moved-extra/initial classification boundary. No new general PK scheme is claimed. |
| CR-05 / G5 — BLOCKER | **Closed, bounded; preserved.** `toggle.js:14-17,78-112,137-167` keeps owned state separately from listeners and composes it with independent/ancestor disabled owners. Inspected native validity/FormData assertions at `toggle.test.js:47-95`, zero/two/one matches, recovery and ownership lifecycle at `:188` onward. Fresh selected JS cases passed. Human accessibility remains pending. |
| WR-01 — WARNING | **Closed for original quality selection defect; preserved.** `runner:584-616,677-735` requires exact semantic commands and collection multiplicities. Fresh dual-entry mutations of filtered JS and missing `--strict` rejected with `javascript: wrong quality command` / `strict-docs: wrong quality command`. Retained records are exactly origin-identical. |
| WR-02 — WARNING | **Closed for original current-runtime request defect; preserved.** `runner:243-350,1451-1456` preflights current intent before output writes; `can_reuse` compares effective selections. Fresh actual `--run --only strict-docs` with `CV_FOCUS_PYTHON=/missing/plan22-review-python` rejected before creating output. An actual historical `--check` with that override still passed, correctly using recorded selections. Inspected changed-valid-selection and preflight tests. |
| WR-03 — WARNING | **Closed for the original absent/contradictory-control defect.** `runner:1158-1199` requires the exact detail/summary inventories, integer exit1, five-token checker argv, exact interpreter/runner/mode and basename, empty stdout and exact predicate stderr. Strict duplicate-key parsing at `:189-198` applies to packet, sidecar, origins and handoff. Both original mutations and boolean exit, wrong command/diagnostic, extra record and duplicate key controls rejected via both CLIs. |
| WR-04 — WARNING | **Closed for the original missing/stale-capture defect.** `runner:912-1038,1090-1095` rechecks exactly three stock identities/explicit empty native, exact typed device metadata, viewport/containment, icon observations, contained distinct resolved paths, current file digests and PNG dimensions. Empty stock and stale digest rejected via both CLIs despite retained successful canonical exit. Traversal, boolean scale, absent font family and NaN glyph controls also rejected. WR-05 is a separate numeric diagnostic defect. |

## Independent controls and provenance

All commands ran from `/home/alex/projects/alex/django-crud-views`. Machine-readable logs preserve exact argv, stdout/stderr, exits and UTC windows. The main probe began `2026-11-01T19:39:36.918856+00:00` and finished `19:41:44.920495+00:00`; subsequent boundary observations are individually timestamped in their log.

- `.nox/crispy_floor-3-12-django-6-0/bin/python .../22-evidence/code-controls/probe.py`: **38 real CLI executions, all 38 matched** their exact expected diagnostics/results. Three positive observations: clean aggregate, clean pending handoff, historical aggregate with an invalid current capture override. Thirty-five negative observations include the four original counterexamples through both entry points, exact control-record contracts, duplicate JSON keys, capture metadata/containment, retained timestamp rewriting, WR-01 commands, false readiness, invented human attribution and runtime preflight.
- Same interpreter with `.../22-evidence/code-controls/boundaries.py`: **12 additional real CLI executions**. Ten rejected at the intended predicates: stage-one payload failure before missing control records; stage-two malformed real payload record before missing later records; changed product digest, added source path and removed source path in hash-rebound owned origin copies, each through aggregate and handoff. Two oversized-number executions rejected by crashing and establish WR-05.
- Total: **50 independent CLI observations: 3 clean positives, 45 expected diagnostic rejections, 2 uncaught-error rejections**. No control invokes a product matrix or browser.
- `PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py -k 'test_reclean_edit_only_extra_stays_invalid or test_reclean_http_rejects_before_any_save or test_late_clean_reclean_restores_row_policy_before_http_save' -q -p no:cacheprovider`: exit0, **12 passed, 140 deselected in 5.20s**.
- `/home/alex/.nvm/versions/node/v24.21.0/bin/node node_modules/vitest/vitest.mjs run tests/js/formset.test.js tests/js/toggle.test.js -t 'native row deletion eligibility|formerly bound|unresolved conditional ownership lifecycle'`: exit0, **36 passed, 81 filtered/skipped, two files**, 1.10s. Those 81 cases are intentionally outside this probe, not new acceptance exclusions. Vite printed its existing future-native-config-loader warning.

The four original mutation packet/handoff fixtures are retained under `code-controls/shared-fixtures/` for independent auditor replay. They are explicitly corrupted diagnostic inputs authored by this code lane, never acceptance evidence. `inventory.json` binds every path/hash and the untouched inputs. The security lane's use of those fixtures does not make this lane its observer. Other temporary mutation envelopes were removed after execution; their reproduction programs and exact results remain.

Bootstrap inspection: `generate_controls` (`runner:1577-1628`) resets inventories, executes payload mutations before record mutations, validates each real child process result before adding it, then checks the uncorrupted complete packet. No successful seed is invented and no public controls-bypass mode exists. The fresh packet's 33 records satisfy the complete current contract; its original 25 controls stay in origin18. The stage-one/stage-two fresh probes above confirm rejection ordering. The clean final positive observation in21 is historical capture evidence, supported here by new clean aggregate/handoff executions; it is intentionally not a self-referential admission prerequisite.

Complete source comparison independently found **824 identical paths, 822 unchanged digests, exactly the runner and its test file changed, zero additions/deletions**. All **17 retained gate objects are JSON-identical** to origin18, including nested commands, times, revision, source digests and runtime selections. `runner:1202-1328` enforces complete-map digest consistency, confined origin references, fresh gate inventory, unchanged selections and retained object equality; product/add/remove mutations rejected through both CLIs. Fresh tests/Ruff retain current provenance; historical product gates were not relabeled current executions.

The actual fresh self-test gate has **62 selected identities and exactly 62 individual `... ok` outcomes**, equal to current AST-discovered identities, no omissions/skips, exit0 and `Ran 62 tests in 592.063s / OK`. Its actual command was the configured `-m unittest discover -s .../15-evidence -p test_runner.py -v`, captured `19:16:27.945130`–`19:26:20.228990` UTC. It was inspected, not rerun. The three fresh gate windows sit inside the refresh window. Explicitly synthetic unit fixtures remain labeled in `test_runner.py`; no test-only mock replaces validation in the reported independent CLI observations.

Actual stock images remain regular, nonsymlink files with matching SHA-256: desktop PNG1440×3104/CSS viewport1440×900; mobile PNG375×3052/viewport375×812; tablet PNG768×3077/viewport768×1024. Full-page height correctly differs from viewport height. Recorded client/inner/scroll widths match; each capture has 44 nonempty positive-size glyph observations with `"Font Awesome 6 Free"` family and loaded=true. Inspected capture-time font loading in `tests/browser/conditional-formsets.cjs:347-355`. Native captures are explicitly empty. Source inspection and the current62-test observations cover resolved symlink escape and owned changed/deleted/non-PNG byte controls; this reviewer did not create new files in the screenshot subtree. Current aggregate runs also rechecked referenced modal screenshot hashes. These are artifact integrity/record consistency facts, not fresh rendering or human readability judgments.

## Bindings and limits

| Artifact / logical binding | SHA-256 |
|---|---|
| Current logical source | `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` |
| Current runner | `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5` |
| Current checker tests | `530ab85446dfa9fd4c702b3c521066e07b63a2beaaf7ed4426ded142e33e8725` |
| Current21 results | `717f3495fbf3a11c4a23f037bece1136727082314854ad3fd371b56ffce40ab0` |
| Current21 manifest file | `61321dd218c3bfcead5d89eac5f126498ffb09123dabb3c8559f09f1214f1646` |
| Original18 results | `a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674` |
| Original18 manifest file | `160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf` |
| Original logical source | `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` |
| Original runner | `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` |
| Starting22 handoff, unchanged in this lane | `7f838769155c2cc2257c1f46a40225cda0bbbc8dd8730905a29d202e788d4a08` |
| Historical19 code review | `1e4e1384618101b31fafb8f24b5c50fa045baa594a35630cf4f57020de4822e4` |
| Historical19 security review | `9b68043dfa5eb54bc351c28b5dcc0dfa52fe2b52d655e24ca883dad5f9d4984b` |
| Main independent outcomes | `d9c9aa32aa0aac768118594801491a040bd0e3e7dcfbc3f761cecdbd9487336a` |
| Boundary independent outcomes | `a89837d0fcca4f4b6dfec0c9b4ba0546ad1e74f6044634ef00546f305f977d8c` |
| Shared fixture inventory | `4a13a94748d47e35d50bbbfae561c9cf253b35869c90c95a4468e4ee75d96395` |

The protected-file comparison passed after the main controls. Historical19 code attribution remains `2026-11-01T17:13:39Z` on original source `bc68...`; this report supplies current applicability under a different actor/time rather than rewriting that record. Historical48,220 Python passes, JS347/integration2 and browser36/305 remain historical totals. Demonstrated runtime bounds remain Python3.12.3; Django4.2.30/5.2.18/6.0.9; Chromium149.0.7827.55. Preserve the exact four CSP skip and four crispy-floor golden deselection events, A19-only AUTH-02, request authorization/ancestry/querysets, routed atomic/rollback and inactive skip/explicit managed purge boundaries. Preserve A8, A25, #210/jQuery, broader Guardian#286/custom-PK/backend/field/theme exclusions and Phase7 stability limits.

All19 decisions and all31 flagged-unresolved fallback assumptions remain in the handoff. **H1 is pending. H2 remains flagged-unverified:** **Switching a conditional file field off must not silently authorize deletion of the stored file content.** Native False-clear/None-no-change, trusted server-disabled precedence, unchanged-inline/storage-spy/retained-byte cases establish bounded reference behavior. ImageField remains reference-only; image decoding, application hooks/signals and broader storage guarantees are unclaimed. The historical UI24/24 result and stock screenshots do not settle stock/native human review. No actor/time/response, descriptor or approval was invented.

T-06.4-35/36 remain pending; linked threat severity/closures belong to the independent security lane. The six previously open threats and five-high blocking count must remain separately accounted for by that lane. This code report cannot claim SECURED. Canonical VERIFICATION and final digest rebinding remain orchestrator/independent-verifier owned; the handoff must stay excluded from the canonical fingerprint it embeds. No phase completion, Phase7 advancement, ready=true, merge or release is authorized by this result.
