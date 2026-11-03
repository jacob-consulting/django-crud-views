---
phase: "06.4"
plan: "25"
actor: /root/execute_25/security_25
agent_type: gsd-security-auditor
recorded: 2026-11-01T20:58:37.009973+00:00
asvs_level: 1
block_on: high
source_sha256: 5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d
packet_sha256: 0584675c935c5d7a81043a3c412a9bb43df5072532db49682aa5604e575effbd
verdict: OPEN_THREATS
threats_total: 44
threats_closed: 40
threats_open: 4
open_high: [T-06.4-35, T-06.4-36, T-06.4-40, T-06.4-43]
accepted_risks: []
transfers: []
---

# Plan25 independent security reassessment

**OPEN_THREATS:40 closed of44 unique authored mitigations;4 high blocking obligations remain open.**
Auditor `/root/execute_25/security_25` independently assessed the current frozen checker/refresh scope and authored
this verdict. The coordinator persisted the returned result because the auditor role has a single-writer,
read-only contract. The auditor wrote no files, changed no source, installed nothing and made no index writes
or commits. This persisted report summarizes that auditor's returned findings and evidence without assigning
the executor an independent verdict. Scope fulfills the current ASVS1/high verify:post security review hook;
later canonical/handoff outcomes require their own assessment and cannot be retroactively attributed here.

The unique authored register is numbered01–43 plus SC once:29 high and15 medium, all mitigate. Closed25 high
and15 medium; open4 high, zero open medium. Historical38/41 accounting remains an earlier snapshot. No risks
were accepted or transferred. No unregistered threat surface was identified; new checker/refresh/handoff
surfaces map to T41–43 and existing boundaries. The31 fallback assumptions are not additional threat IDs.

## Actual independent observations

[independent-outcomes.json](independent-outcomes.json), `lanes.security`, contains the actual14 commands,
unmodified stdout/stderr, return codes and UTC start/finish times returned by the auditor. Observations were
recorded at2026-11-01T20:57:16.620951+00:00; execution window20:56:41.078542–20:57:16.620890 UTC.

| Probe | Entry points | Actual result |
|---|---|---|
| Clean actual24 packet | aggregate | exit0, PHASE64_MATRIX_OK20gates/current source, empty stderr |
| Clean pending24 handoff | handoff | exit0, structurally_valid:true/ready:false/not-ready, empty stderr |
| Width10**400 only | both | exit1, empty stdout, exact capture-icon diagnostic |
| Height10**400 only | both | exit1, empty stdout, exact capture-icon diagnostic |
| Missing detailed controls | both | exit1, empty stdout, Checker control evidence inventory incomplete |
| All controls rewritten to success | both | exit1, empty stdout, Checker control exit invalid: exit-code |
| Empty stock capture inventory | both | exit1, empty stdout, Conditional capture inventory invalid: stock |
| Stale stock digest | both | exit1, empty stdout, Conditional capture digest mismatch: desktop |

The four overflow rows each contain stderr exactly
`MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` plus newline. All other refusals
contain exactly `MATRIX_REJECTED: ` + their displayed diagnostic + newline. All14 exact triples matched;
no traceback, earlier stale-source/inventory error or acceptance bypass substituted for the intended result.

The executor prepared the six complete temporary packets using current test_runner.py and prior22 probe
recipes. The auditor independently checked exact mutation equality against actual24, byte-identical sidecars,
and matching-digest-only handoff changes, then executed every observation itself using
PYTHONDONTWRITEBYTECODE=1. Owned `.git/gsd-plan25-security-fixtures` transport is necessary because bound_file
confines packet references to ROOT. No validator/source patch was used. Fixture preparation is not an
independent execution claim. Owner cleanup follows recording.

Additional auditor read-only numeric capture checks:10 accepted and32 precisely rejected observations across
both dimensions. Positive integers/floats,10**300, maximum finite float and a subnormal passed. Zero, negatives,
booleans, null, strings, containers, NaN, infinities and ±10**400 raised the exact intended ValueError.

## Current source and provenance

| Binding | SHA-256 |
|---|---|
| Logical source map |5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d|
|15-evidence/run.py|75f8057f55d869ccb9591a0a9868e57d606f9e65f2f0eebffa5fca8d5313ad66|
|15-evidence/test_runner.py|a37d5e636ad612d9e4b3a330392bd61e31ca6290c04ba6f3fa0692a09903e7bf|
|24-evidence/results.json|0584675c935c5d7a81043a3c412a9bb43df5072532db49682aa5604e575effbd|
|24-evidence/source-manifest.json file|7dc2541183e999d8709d4c173a9db50f21a0bab52312e22767db896b80a0bf9b|
|24-evidence/applicability.md|98e2af40d6ca6f45a9bec45c5e6da2f0e40b51b9e1593a830e324d128758713d|
|24-evidence/handoff.json at audit|0f473ba6090ffb7b2e4efa691d534448f2a8cce6fbcb4aa8dca8bf4e97057753|
|Unchanged06.4-VERIFICATION.md|5048486226b2d48556280f99f5ae12a24d4ef581c9585ff8c4a4da7e1d9b3ced|
|18-evidence/results.json|a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674|
|18-evidence/source-manifest.json file|160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf|

Independently recomputed maps contain824 paths each, no additions/deletions,822 unchanged digests, exactly
runner/test changed. Live source equals24 manifest. All17 retained gate objects and effective runtime
selections are exactly equal to origin18, including commands, outputs, environments, times and provenance.
Fresh24 evidence has67 exact discovered/observed passing checker identities, two successful Ruff gates,
35 complete exact control records and an ordinary clean positive. Self-tests ran20:37:34.134784–20:48:05.433651
UTC, exit0,67 tests in631.064s. Full identity/diagnostic lists in hash-bound applicability were compared to
actual packet/discovery; width/height tests, numeric contract, overflow-control tests and mandatory WR05 test
are present. The full product/browser/self-test suites were not rerun. Historical48,220 Python passes,
JS347/integration2 and browser36cases/305assertions retain their actual earlier execution attribution.

## Closed authored mitigations

All entries below are CLOSED only within their declared bounds, disposition mitigate. Paths `lib` and `js`
refer to src/crud_views/lib and src/crud_views/static/crud_views/js; runner/tests mean15-evidence/run.py and
test_runner.py. These are the independent auditor's per-ID implementation findings, preserved here.

| ID | Severity | Current evidence |
|---|---|---|
|01|medium|js/toggle.js:23,88,152 exact owner/name, retained state, obsolete listener detachment|
|02|medium|lib/conditional/layout.py:29 and toggle_group.html:5,10 escaped attributes|
|03|high|lib/conditional/group.py:163,181,195 native persistence/trusted disabled precedence|
|04|high|group.py:69,181 and persistence tests:276,285,291,333 native reference clearing/storage spies; H2 separate|
|05|high|group.py:74,140 and checks.py:155,163 unsupported clearing refusal/configuration checks|
|06|high|group.py:142,153,184,195 inherited cleaning/model validation/disabled preservation|
|07|high|lib/formsets/render_tree.py:202,247,253 policy after native validation, extra rejection|
|08|high|render_tree.py:223,227,234,238 authorized queryset/native PK/bound instance agreement|
|09|medium|render_tree.py:245,260 generic deduplicated Invalid row error|
|10|high|lib/formsets/formsets.py:359,385,392 and mixins.py:114 inactive skip/scoped purge/routed atomic saves|
|11|medium|js/toggle.js:31,78,99 external baseline/all enclosing owners|
|12|medium|js/toggle.js:68,124 focus recovery/cancellation-aware native reset|
|13|high|js/formset.js:77,507,515,590 owning-form lookup/controller/actions|
|14|high|js/formset.js:536 and modal.js:227 reorder/cancellation before serialization|
|15|medium|js/formset.js:10,20,267,329,517,529 immutable identity/DELETE capability/disabled checks|
|16|high|lib/formsets/mixins.py:49,71; Guardian mixins.py:68; formsets.py:455,492 authorization/ancestry|
|17|high|formsets.py:455,467,528 and retained real second/deeper fragment→POST/database evidence|
|18|medium|conditional-formsets.cjs:80 and runner:1052,1087 source/case/assertion/runtime/outcomes|
|19|high|conditional-formsets.cjs:243,534,550,555 both-theme capability/forged POST zero-save checks|
|20|medium|test_conditional_migration_docs.py:42,67,92,114,137,184 executable examples/migration|
|21|medium|migration docs tests:92, actual projection/retained round trips; PUBLIC-SURFACE:64,89,96|
|22|high|runner:675,734,1099,1172,1296 source/selection/outcome/control/capture enforcement; eight current preservation refusals|
|23|high|lib/views/mixins.py:37,41,54 and formsets/mixins.py:104,114 authorization/validation before atomic writes|
|24|high|render_tree.py:202; formsets.py:379,381; validation_gate tests:90,140 reclean zero-save|
|25|high|separate Vitest configurations; js-integration/formset.test.js:94,104,108 interpreter controls/retained bridge|
|26|medium|js/formset.js:10,20,329 immutable bound index/native deletion eligibility|
|27|medium|js/toggle.js:17,88,152 unresolved state retention/obsolete detachment|
|28|high|runner:675,1152,1172 exact commands/inventories/integer exit1/diagnostics|
|29|high|runner:236,256,355,1275 preflight before writes/exact selection reuse|
|30|high|conditional-formsets.cjs:243,261,274,285 capability/ordered persistence/reclean zero-save|
|31|medium|runner:932,1045,1099 capture provenance/pending human markers/current exact capture refusals|
|32|medium|migration docs tests:114,137,173,184 capability/reclean recipes/reference-only H2 limits|
|33|high|runner:1193,1240,1296 exact source/17 retained/67 fresh/35 controls|
|34|high|preserved authorization/queryset/atomic/skip-purge paths and exact retained full suites; A19-only AUTH02|
|37|high|runner:194,1152,1172,1584,1618 strict duplicate loader/staged controls/actual clean positive|
|38|medium|runner:932–1048 inventories/confined distinct paths/PNG bytes and digests/device/containment/glyph observations|
|39|high|runner:1193,1206,1240,1296 two-file exemption/complete maps/bound origins/exact retained/fresh evidence|
|41|medium|runner:923,999,1367,1648,1656; tests:509,548,551,554,586,1015 local overflow refusal/both dimensions/controls/mandatory WR05|
|42|high|runner:1193,1240,1296 exact824/822/2,17 retained/runtime equality/67–35 fresh/history preservation|
|SC|high|runner:236,256 existing runtime paths/unchanged dependency-lock inputs/no install; future gate unexercised|

T38's bounded capture-integrity closure is retained; the former diagnostic defect did not demonstrate an
acceptance bypass. T41 independently closes the overflow rejection contract. Reviewed24 incorrectly labels
T41 high;23PLAN authors it medium. Correct the current binding while preserving historical snapshots. This
metadata error requires no source change or evidence recapture.

## Open blocking mitigations

| ID | Severity/category | Missing outcome and searched evidence |
|---|---|---|
|T-06.4-35|high/Repudiation|Genuine H1/H2/final independent acceptance absent despite attribution/readiness guards; runner:1669,1707,1793,24 human/review fields and canonical report inspected.|
|T-06.4-36|high/Tampering|No H2 enforcement descriptor/RED–GREEN route or genuine human disposition; group.py:69,181, persistence tests, handoff H2 and runner:1798–1821 inspected.|
|T-06.4-40|high/Repudiation|Final current canonical verification/report-hash rebind pending;24 reports/history/canonical_reverification, prior canonical,22/25 obligations inspected.|
|T-06.4-43|high/Repudiation|Independent observations supplied; stable final binding, immutable pre-replacement replay, successor canonical and post-summary rebind/check absent at snapshot;25/26 plans,24 handoff and unchanged canonical inspected.|

No open nonblocking threat. Schema1 requires overall passed security before machine status verified. Keep
actual partial independent_disposition=closed while machine states remain pending under OPEN_THREATS.

## Acceptance boundaries

All19 decisions remain present; all31 fallback IDs remain flagged-unresolved and exactly equal to the prior
handoff. Complete22 history is preserved. H1/H2 remain unchanged pending records with no invented person,
time or response. H1 requires actual corrected stock/native usability/accessibility judgment. H2 remains
descriptor-less flagged-unverified, exactly: **Switching a conditional file field off must not silently
authorize deletion of the stored file content.**

Scope remains Python3.12.3/Django4.2.30,5.2.18,6.0.9/cached Chromium149.0.7827.55. Original four CSP skip events
and four crispy-floor golden deselections remain historical. ImageField is reference-only; image decoding,
general storage/application-hook guarantees are not established. A8/A25/#210, broader Guardian/custom-PK/
backend/theme expansion and generic concurrency guarantees remain excluded. No source change, install,
accepted risk, human approval, readiness, phase completion or Phase7 advancement follows from this review.
