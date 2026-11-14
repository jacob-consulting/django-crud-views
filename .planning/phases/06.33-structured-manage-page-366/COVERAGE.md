# Phase 06.33 — Source and UI Coverage

Planning coverage only; implementation and browser evidence are pending. Task IDs below abbreviate 06.33-NN.Task.

No external API integration: this phase reshapes existing Django diagnostic data and templates; the detector returned detected:false. No new package install, production schema change or external service.

Formal-ID spec-less edge/prohibition probe skipped because ROADMAP assigns prose requirements, not formal IDs. No IDs were invented. Approved decisions, acceptance and all 52 explicit UI criteria remain enforced by plans. Assumption-delta outcome: **no-change** to identity; explicit ViewSet/user inputs are data preparation, with request coordinates passed separately. #370 access evaluation/trace and #371 dump command remain excluded.

## Four-source audit

| Source | Item | Owning plans/tasks | Disposition |
|---|---|---|---|
| GOAL | Read permissions/configuration at a glance, responsive core/Guardian, set/default clarity | 01–07; all 52 UI truths/browser 09.3 | COVERED |
| REQ | ROADMAP prose: matrix, actor/direct grants, counts and privacy | 01.1–2, 04.2 | COVERED; no formal REQ IDs |
| REQ | ROADMAP prose: view inventory, provenance, gate descriptions and parity | 02.1–2, 03.1–2, 04.1 | COVERED |
| REQ | ROADMAP prose: checks, facts, hierarchy, relative routes, targets, ancestor policy | 05.1–2, 06.1–2 | COVERED |
| REQ | ROADMAP prose: lazy compatibility, shared Guardian overrides, authorization ordering | 01.1–2, 04.1–2 | COVERED |
| REQ | ROADMAP prose: registry, accessibility/CSP, docs/base/anchors, locales, example | 07–10 | COVERED |
| REQ | Retain existing AUTH-04–07 and Phase 06.31 constraints | 01.1, 02.1–2, 04.1–2, 10.1–2 | COVERED preservation; no reassignment of old requirement IDs |
| RESEARCH | Explicit supplied ViewSet/actor; request-free builders; route coordinates in adapter | 01 contract, 01.1, 04.2, 06.1–2 | COVERED |
| RESEARCH | Immutable constructor/pre-registration facts; registered-base MRO; class-valued diagnostics vs W280 | 03.1–2 | COVERED |
| RESEARCH | Actual gate owners; custom has_permission; inherited extension gates; custom-action operation selection | 02.1–2, 04.1 | COVERED |
| RESEARCH | Guardian configured CT/permission identity, direct-FK models, strict superuser shortcut, orphan grants | 04.2 | COVERED |
| RESEARCH | Nested routing before auth reads, warm/cold permission-map refusal, no aliases forced | 01.1, 04.2 | COVERED |
| RESEARCH | Lazy compatibility; old generic group query; no stock legacy reads | 01.2, 04.2 | COVERED |
| RESEARCH | Collector scoping without obj filtering; global deduplication/URLconf barrier | 05.1–2 | COVERED |
| RESEARCH | Static target descriptions and actual contributed URL patterns; no object sampling | 06.1–2 | COVERED |
| RESEARCH | External enhancement lifecycle, registry/asset inventories, no dependency changes | 07.1–2, 08.3 | COVERED |
| RESEARCH | Escaping/no descriptors, no false clean state on auth/DB failure | 01.1, 03.1–2, 05.1 | COVERED |
| RESEARCH | Cached 4.2/5.2/6.0; existing browser tooling; catalog compilation; matrix limitations | 09.1–3, 10.2 | COVERED; actual available combinations must be recorded |
| RESEARCH | Runtime inventory: no persistent IDs/storage/settings/model changes; asset/cache/localization consumers updated | 03.1, 07.1, 08.2–3, 09.1, 10.2 | COVERED |
| CONTEXT | All D-01–D-30 | Table below | COVERED or explicit historical/deferred disposition |

## Decision ownership

| Decision | Approved behavior | Owning task(s) | Disposition |
|---|---|---|---|
| D-01 | Developer reader; existing manage access | 01.1, 01.2 | COVERED |
| D-02 | Single main/side card layout and full ancestor/Guardian facts | 01.1, 06.1, 07.2 | COVERED |
| D-03 | Stock Bootstrap and responsive tables | 01.1, 07.1, 07.2 | COVERED |
| D-04 | Holder × permission matrix, custom columns | 01.1, 01.2, 04.2 | COVERED |
| D-05 | Effective signed-in actor row with explicit user input | 01.1, 04.2 | COVERED |
| D-06 | SHOW_USERS and exactly-20 folding | 01.2, 04.2 | COVERED |
| D-07 | Generic/direct Guardian user and group grants | 04.2 | COVERED |
| D-08 | Own/parent requirement and Guardian policy summaries | 02.1, 04.1 | COVERED |
| D-09 | Closed view disclosures and stable anchors | 02.1, 07.2 | COVERED |
| D-10 | Ordered two-column curated sections | 03.2 | COVERED |
| D-11 | Project provenance and registered-base action records | 03.1, 03.2 | COVERED |
| D-12 | Shared progressive defaults switch and hidden counts | 03.2, 07.1 | COVERED |
| D-13 | Explicit-input Python builders and complete shared Guardian rendering | 01.1, 04.2, 05.1, 06.1, 06.2 | COVERED |
| D-14 | Whole-card blocks, lazy old shapes and independent getters | 01.2, 04.1, 04.2, 07.2 | COVERED |
| D-15 | Registry-backed badges/default/help | 01.3, 07.2, 08.3 | COVERED |
| D-16 | Historical handover boundary | 01.1 | INFORMATIONAL: approved handover is historical; this run creates executable plans only, no implementation/worktree implied. |
| D-17 | Scoped checks, separate collectors and silencing | 05.1, 05.2 | COVERED |
| D-18 | Effective ViewSet identity and icon | 06.1 | COVERED |
| D-19 | Full upward chain, unlinked children/Resource | 06.1 | COVERED |
| D-20 | Generated relative routes through simplify_regex | 02.1, 06.1 | COVERED |
| D-21 | Closed Presentation and all context-button targets | 06.2, 07.1 | COVERED |
| D-22 | Original constructor-field provenance | 03.1, 06.2 | COVERED |
| D-23 | Short badges, marked accessible tooltips and legend | 02.1, 07.2 | COVERED |
| D-24 | One docs page/base and tested card/section anchors | 07.2, 08.1 | COVERED |
| D-25 | Complete static Other inventory including class/annotation edges | 03.1, 03.2 | COVERED |
| D-26 | Group sizes and active-superuser count/names | 01.2, 04.2 | COVERED |
| D-27 | Owning-gate description API and real-request parity | 02.1, 02.2, 04.1 | COVERED |
| D-28 | Pinned tests/docs, both German locales and Bootstrap example | 06.1, 08.2, 09.1, 10.1 | COVERED |
| D-29 | Future #370 boundary; reusable data/description inputs only | 01.1, 02.1, 08.2 | EXCLUDED feature: another-user UI/object trace not implemented; explicit user input and description API preparation are COVERED. |
| D-30 | External assets, no inline script/style/event/url | 07.1, 07.2, 09.3 | COVERED |

## UI consideration ownership — 52/52 explicit

IDs combine UI-PROBE.requirement_id and category. Every row's exact source resolution is lifted into plan 09's must_haves.truths, after the feature dependencies exist. The listed feature task owns implementation, not an early claim of final browser/German/Guardian completion. The source resolution is the acceptance contract, not evidence of completion. Browser task 09.3 verifies every row against final pages; focused data/DOM/JS tasks own the underlying state.

| UI ID | Feature task (all final truths: plan 09) | Final evidence |
|---|---|---|
| permissions.empty | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.loading | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.error | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.populated | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.partial | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.overflow | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.zero-one-many | 01.1–2 | 04.2 data; 09.3 browser |
| permissions.long-text | 01.1–2 | 04.2 data; 09.3 browser |
| views.empty | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.loading | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.error | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.populated | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.partial | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.overflow | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.zero-one-many | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| views.long-text | 03.1–2 | 02.1, 04.1 request; 09.3 browser |
| presentation.empty | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.loading | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.error | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.populated | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.partial | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.overflow | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.zero-one-many | 06.2 | 07.1 toggle; 09.3 browser |
| presentation.long-text | 06.2 | 07.1 toggle; 09.3 browser |
| facts.empty | 06.1 | 09.3 browser |
| facts.loading | 06.1 | 09.3 browser |
| facts.error | 06.1 | 09.3 browser |
| facts.populated | 06.1 | 09.3 browser |
| facts.partial | 06.1 | 09.3 browser |
| facts.overflow | 06.1 | 09.3 browser |
| facts.zero-one-many | 06.1 | 09.3 browser |
| facts.long-text | 06.1 | 09.3 browser |
| checks.empty | 05.1–2 | 09.3 browser |
| checks.loading | 05.1–2 | 09.3 browser |
| checks.error | 05.1–2 | 09.3 browser |
| checks.populated | 05.1–2 | 09.3 browser |
| checks.partial | 05.1–2 | 09.3 browser |
| checks.overflow | 05.1–2 | 09.3 browser |
| checks.zero-one-many | 05.1–2 | 09.3 browser |
| checks.long-text | 05.1–2 | 09.3 browser |
| help.loading | 07.2 | 08.1 anchor tests; 09.3 browser |
| help.error | 07.2 | 08.1 anchor tests; 09.3 browser |
| help.overflow | 07.2 | 08.1 anchor tests; 09.3 browser |
| help.long-text | 07.2 | 08.1 anchor tests; 09.3 browser |
| defaults.empty | 07.1 | 09.3 browser |
| defaults.loading | 07.1 | 09.3 browser |
| defaults.error | 07.1 | 09.3 browser |
| defaults.populated | 07.1 | 09.3 browser |
| defaults.partial | 07.1 | 09.3 browser |
| defaults.overflow | 07.1 | 09.3 browser |
| defaults.zero-one-many | 07.1 | 09.3 browser |
| defaults.long-text | 07.1 | 09.3 browser |

## Approved exclusions and implementation boundaries

No impersonation, another-user evaluation/trace, dump command, editing, tabs, comparison grid, new settings, Resource manage route, broad permission/cv_* reference pages, downstream Tabler adoption, dependency upgrade or authorization redesign. Plain data/builders and two provenance records keep the feature developer-maintainable. Existing manage enable modes, active configured-group gate (including staff/superusers), protected ancestors, optional app boundaries and example read-only developer grants remain intact. Tests may create isolated real admitted actors; they must not weaken production access.

No unplanned in-scope item found. Plans 01–07 serialize shared manage source/template ownership; 08 and 09 can run together because they modify disjoint files; 10 consumes both. Each of 25 tasks has at most five modified files; plans 01, 04 and 07 now have three tasks to synchronize affected regression inventories within their changing plan. Calibration factor=1, sample_count=0, confidence=low; estimates are raw projections, not execution measurements.


## Review round 1 — ff2ea0c6

All five HIGH and eleven actionable findings are incorporated into PLAN task actions/acceptance, with per-plan Review Dispositions Ledgers. No implementation evidence is implied.

| Finding | Executable owner | Resolution |
|---|---|---|
| H1 | 01.2 | Own legacy core headings migration; translated new strings proved in 09.1. |
| H2 | 01.3; retained 07.2/08.3 | Nine keys and exact live/docs count guards synchronized together. |
| H3 | 07.1/07.3; 10.2 | All five asset/pipeline inventories owned and verified before dependent waves. |
| H4 | 04.3; 06.1 | Guardian fallback assertions move with table removal; ancestor-layout assertions remain 06.1. |
| H5 | 04.3; 10.2 | test_guardian and test_guardian_policy migrations preserve effective helper/policy behavior. |
| A1 | 02.1, 05.1, 06.1 | Bounded per-view display errors after admission; empty routes checked before urlpatterns. |
| A2 | 02.1, 04.1 | Nearest provider-enabled ancestor; no badge for no gate/None key. |
| A3 | 04.2 | Reuse Shelf/direct-FK fixture models. |
| A4/A5 | 06.2 | Actual context/list/card inline fields; static label-template descriptions without rendering. |
| A6/A7 | 08.3, 07.1/07.3 | javascript.md inventory and equivalent forbidden-global source test. |
| A8 | 09.2/09.3 | Pinned asset checksums/cache, literal CSP, preflight failure distinct from product behavior. |
| A9/A10 | 10.1 | Reuse existing real declarations; direct runtime/docs inventory test, no test-name matching. |
| A11 | All feature plans; 09.3 | Slice-local completion; all 52 exact UI truths lifted to final browser plan. |

Unsupported advice remains explicitly rejected in plans: replacing real AutoManageView with its base, broader custom-gate inference, redundant dynamic grant schema and reducing approved automated UI criteria. No writer-owned revision conflict arose.

## Review round 2 — dae8e0e9

Prior H1–H5/A1–A11 remain closed by independent review. All eleven current findings are executable dispositions; no new capability or task was added (10 plans, 25 tasks, 9 waves).

| Finding | Executable owner | Disposition |
|---|---|---|
| C2-A1 | 01.2 boundary; 06.1 deletion/test migration; 07.2 preservation | Old Properties/spacer DOM and retained assertions change together in 06.1. |
| C2-A2 | 01.1–3, 02.1, 03.2 | Early shared-template gates replay all three retained ancestor/Guardian modules. |
| C2-A3 | 02.1, 05.1 | Missing own/ancestor keys render neutral undeclared-key text without invented permission strings; original endpoint errors remain. |
| C2-A4 | 02.1, 06.1 | One shared route/error projection feeds view summaries and URL names. |
| C2-A5 | 01.1, 08.2 | Auth-reading builders without a registered manage class raise a documented error before reads; pure routes/configuration remain callable. |
| C2-A6 | 03.1, 08.2 | Normal constructor provenance supported; model_construct bypass explicitly unsupported, no extra machinery. |
| C2-A7 | 04.2–3, 08.2 | Retain legacy config_table snippet unchanged and test/document explicit project includes. |
| C2-A8 | 06.1, 10.2 | Isolated no-admin/no-admindocs import and real route builder probe on each cached series. |
| C2-A9 | 08.2 | Breaking classification settled with paired migration guidance. |
| C2-A10 | 09.2 | runtime/stopOwned import source is cancel-navigation.cjs; workflow runner remains the analog. |
| C2-A11 | 10.2 | All seven omitted retained modules added to both literal cached-series commands. |

No revision conflict arose. Explicit unsupported boundaries do not defer an approved feature or broaden Resource/manage access scope.

## Review round 3 — a909d251

| Finding | Executable owner | Resolution |
|---|---|---|
| C3-A1 | 01.1, 08.2 | A Resource-based fixture proves actual absence; mode=no preserves model AutoManageView/URLs and disabled access. No registration change or Resource feature. |
| C3-A2 | 01.1–3, 02.1, 03.2, 04.3, 05.1, 06.1–2, 07.1–2 | All 11 shared-template editing tasks run current cards/ancestor/Guardian/override regression modules at their own gates. |
| C3-A4 | 06.1; catalog owner 09.1 | Heading migration uses current gettext results before the new German catalog; identifiers remain literal and new-message translation completeness is still mandatory in 09.1. |

Counts remain 10 plans, 25 tasks, 9 waves and all 52 UI criteria. No new scope, implementation evidence, revision conflict or deferred actionable finding.

## Review round 4 — c978e95e

| Finding | Executable owner | Disposition |
|---|---|---|
| C4-A1 | 01.1 | Local Resource model/fixture follows the existing pattern, uses a unique owned registry name and teardown; no imported module-scoped fixture or reused author/t2_item name. |
| C4-A2 | 01.1–2 | Explicitly accept the presentation-only one-task test_manage verification interval; task 2 closes it before any plan/full-suite completion claim. |
| C4-A3 | 03.1, 10.2 | Existing Resource construction and Guardian vocabulary modules run in the immediate gate and both cached-series replays. |
| C4-A4 | 04.1–3 | Targeted data/override evidence in tasks 1–2; task 3 is the required retained-markup completion gate. No unnecessary duplicate full replays. |
| C4-A5 | 09.1 | Compiled catalogs must match PO translations/plurals/contexts/semantic metadata and load through Django; cross-compiler byte identity is not required. |

All five LOW findings have executable dispositions; counts remain 10 plans, 25 tasks, 9 waves. The existing Resource fixture reference in earlier coverage means the pattern, not shared pytest fixture availability. Advisory pattern-map wording is outside this revision's ownership and creates no new implementation scope.
