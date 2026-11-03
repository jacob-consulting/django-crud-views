# Plan 09 evidence index

The authoritative final artifacts are **one directory above this folder**:

- `09-final-evidence.json`: final matrix/quality/lifecycle gates and exact canonical artifact hashes.
- `07-browser-results.json`: current candidate browser run.
- `07-tabler-replay.json`: current independently applied exact-patch replay, with refresh history.
- `10-companion-delivery.json`: current committed companion probes and repository-qualified receipts.
- `09-REGRESSION.md`, `06.6-ACCEPTANCE.md`, `06.6-09-SUMMARY.md`: results and explicit acceptance limits.

The final candidate/replay captures in this folder are `candidate-accepted-source.json` and
`replay-accepted-source.json`. They bind strict core inventory
`b2a7911ff5764f5323dee75fc9cef3f6bec4186fc25a57a331516d6902825cd0`, matching the human fixture and
the canonical replay. Source agreement does not supply human approval.

**All other candidate/replay filenames here are historical attempts**, including names containing `final`,
`settled`, or `verified`. Those names describe an execution attempt, not current acceptance. They retain
actual source hashes and results from before later review repairs. Never substitute them for canonical reports.
`prior-gates.json` and `prior-gates-*.json` similarly retain older matrix results and raw failures; only final
source-bound gates in `../09-final-evidence.json` certify current automatic results.

Gate `.log` and `.xml` files hold the latest full execution; older complete log/JUnit bytes remain embedded
in the historical gate reports. `red.*`, `shrink-red.*`, `asset-order-failure.txt`, dependency-install/provenance,
and the rejected `denied-post-regression.log` document actual failures/repairs rather than passing gates.
`denied-write-review.json` is a real eight-family regression run before the final helper freeze; the same
denied-write assertions are re-executed in the final canonical candidate and replay.

`cr01-*-green.*` retain the helper repair's focused current/floor checks. `human-fixture.json` identifies the
prepared loopback fixture at port8160; human visual/AT observations remain pending until separately supplied.
The temporary fixture is not a prerequisite for validating retained automatic evidence. Its cleanup is owned
by the orchestrator after human review.
