# Plan 06.34-10 executed evidence

The final release receipt is `../../06.34-10-release-evidence.json`. Each named command has a JSON record and
unchanged transcript here. The complete normal/recorded and supported-series suites also have JUnit reports.
`command-recorder.txt` and `receipt-assembler.txt` preserve the exact temporary scripts used to collect and
validate those records; they are evidence, not installed project tooling.

Source manifests cover the sorted union of tracked and untracked nonignored `src`, `tests`, `docs`,
`noxfile.py`, `pyproject.toml`, and `mkdocs.yml` files. Values hash current bytes, not index contents. The manifest
identity hashes sorted-key JSON before its final newline; the release receipt additionally hashes the raw
manifest file. Generated receipts, captures, build output and temporary databases are excluded from inputs.

The browser receipt independently binds 240 source/harness inputs, observed assets, 63 exact cases and 63
captures. Run `node tests/browser/access-trace.cjs --verify <receipt>` to check all current source paths/bytes,
complete observations, assets, cleanup and screenshot hashes. Only the canonical receipt's sibling
`../../06.34-browser-captures/` images are retained acceptance captures. `browser-attempts/` contains unmodified
development receipts; their scratch screenshot paths were overwritten during iteration and are not current
capture evidence. Failures exposed hidden-text inspection, fixture redirect rendering, native navigation
timing, registry cache configuration and one browser-context termination. The final run retains every case
and uses the actual production forms, traces and registry settings.

The two ordered tests in `alias-order-red.*` fail before the test fixture correction. The probe observes Book
ContentType IDs 55 on default versus 17 on shard, then demonstrates equal regenerated identities. The change
resets both fixture databases before creating deliberately colliding rows. Existing request, permission,
query-count and ordering assertions are unchanged. `alias-order-green`, `alias-order-4-2`, `alias-order-6-0`
and `fixture-isolation` record the corresponding passes. Serial execution is necessary only for that tiny
two-test ordering reproduction; broad suites use four workers and the affected module selection uses two.

`full-normal-initial.log` and `full-normal-wrapper-terminated.*` contain complete passing pytest output, but
the tool shells returned signal-derived exit 143. The second pytest child continued after its wrapper was
terminated; its final exit code was not retained. Neither run certifies the final release gate. Final long
commands instead run under detached file-backed supervisors, recording their actual child return codes and
source hashes. No test was excluded or assertion weakened to work around the tool lifecycle.

Seven declared-compatible Python/Django combinations lack cached usable dependency environments and remain
unverified. Python 3.15.0rc2 exists but has no Django, pytest or Guardian; Python 3.13/3.14 are not on PATH.
No dependency installation, runtime upgrade, CI dispatch or publication occurred. Existing feature-dependent
skips are identified in JUnit and the final receipt. The pre-existing Vite native-config warning is retained
in `javascript.log`; it does not fail the ten JavaScript regressions. Human visual assessment remains pending.
