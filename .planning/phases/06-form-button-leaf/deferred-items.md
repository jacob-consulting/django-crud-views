# Phase 06 — Deferred Items

## Deferred Items

- Pre-existing JS failure on the lock-backed jsdom 30.1.2: `tests/js/list.filter.test.js` "keeps the visible label of a both-mode toggle while its element icons flip" (line 159)
  status: resolved (06-07 task 2)
  **Found:** 06-01 task 1, first `06-js-verify.sh` run (182/183 pass; runtime/lock assertions all pass).
  **Cause:** the test calls `toggle.querySelector("#cv-filter-toggle > span:not([data-cv-filter-icon])")` on the
  toggle element itself. jsdom 30.1.2 returns null for an element-scoped selector whose leading compound matches the
  element (browsers return the child; the equivalent `:scope > span:not(...)` form works in jsdom 30.1.2). The test
  passed on the previously installed jsdom 29.1.1. No product source changed; not caused by Phase 06.
  **Impact:** every Phase 06 JS gate through `06-js-verify.sh` exits nonzero until this is resolved; the wrapper must
  not mask it. Candidate fix: rewrite the assertion with `:scope >` (test-only), owned by whichever plan first needs a
  green JS gate (06-07) or a separate quick task.
  **Resolution (06-07 task 2):** test-only. The assertion now reads
  `f.toggle.querySelector(":scope > span:not([data-cv-filter-icon])")` (same node, same meaning); no product JS,
  manifest or lockfile change. The full `06-js-verify.sh` gate is green (223/223 on node v24.21.0, jsdom 30.1.2,
  vitest 5.0.3, unchanged lock sha256). WINDOWS.md entry 5 marked fixed.

- Transitive dev-only `undici` (via jsdom) has high-severity `npm audit` advisories
  status: open
  **Found:** 06-01 task 1 `npm ci` / `npm audit`.
  **Why deferred:** the plan forbids manifest/lockfile changes; the package is only used by the JS test harness.
  Resolve with a separate dependency-update change and its own legitimacy check.
