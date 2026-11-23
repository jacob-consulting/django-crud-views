# Acme example sync log

One entry per sync, newest first. Written at the end of a run of `PROMPT.md`, together with `baseline.json`.

## 2026-11-23: first sync

- Commits: Tabler `ba777c9` (`main`), CoreUI `11bf5b0` (`sync/acme-example-2026-11-23`), AdminLTE `ccc4947`
  (`chore/sibling-checkouts`, which changes nothing under `example/`; `example/` is as on `main` at `93a4fd2`).
- Ported: the class-based compact formset heading asserts from AdminLTE `f2e6e46` to CoreUI
  (`example/roastery/tests.py`, `example/sales/tests/test_orders.py`). Tabler already had them.
  `roastery/tests.py` is now identical in all three.
- Left different:
  - `config/views.py` (static group text), `dashboard/tests.py` (Show code file list), `templates/project/theming.html`:
    Tabler `9bf8b26` and CoreUI `429949e` describe their own `src/` after dropping the adapter JS (#398). Theme's own;
    AdminLTE never shipped adapter JS.
  - `sales/views/order_bulk.py`, `sales/tests/test_bulk.py`: #399/#400 already in all three (Tabler `911972a` +
    `5f81010`, CoreUI `847cafc`, AdminLTE `f2e6e46`), in each theme's words: AdminLTE's tracker tag `C11` in a comment,
    the theme's button table import, test order.
  - `sales/tests/test_orders.py`: older accepted drift and each theme's markup asserts.
- Also: AdminLTE now uses the sibling checkouts one directory up (`ccc4947`), and step 6 of `PROMPT.md` says so.
- Needs a human look: nothing (only tests changed).
- Baseline: 153 paths, 76 identical in all three, 77 accepted as different.

## 2026-11-23: first baseline

- Commits: Tabler `307b9d5`, CoreUI `d67be0f`, AdminLTE `83cb1e8`.
- Ported: nothing. This entry only records the state from which later reports start.
- Baseline: 153 paths under `example/`, 76 identical in all three, 77 accepted as different.
- Left different: everything that differed on this day, including the old drift listed under "Known state at the
  first baseline" in `PROMPT.md`.
- Needs a human look: nothing.
