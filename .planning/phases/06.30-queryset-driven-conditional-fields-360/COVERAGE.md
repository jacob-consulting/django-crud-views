# Phase 06.30 source coverage

No external API integration: this phase extends local Django form/render/JavaScript behavior and adopts it in a sibling Django application; no remote API/SDK capability is integrated.

This is planned coverage, not implementation acceptance. The roadmap Requirements field is prose; no formal phase requirement IDs exist, so all PLAN frontmatter intentionally uses requirements: []. AC-1–AC-14 are the ordered acceptance bullets from CONTEXT, not invented global IDs. API-SURFACE.md has zero symbols/stale=true and was not used as proof of absence.

## Multi-source audit

| Source | ID | Obligation | Plan/task | Status |
|---|---|---|---|---|
| GOAL | — | Native model-choice category activation on base/ordinary/compact with strict coverage and authoritative clearing | 01–03, 05, 08 | COVERED |
| REQ | prose | Upstream implementation/tests and complete focused own-model example plus verified roastery adoption | 01–09 | COVERED; no formal IDs |
| REQ | prose | Ordinary hidden vs compact visible/disabled, preserve until save, prior paths and bounded costs | 01–03, 05, 07–09 | COVERED |
| CONTEXT | D-01 | Key/label/category contract; several objects share category | 01-01, 02-01, 04-01, 06-01 | COVERED |
| CONTEXT | D-02 | ModelChoiceField native key/label, declared attribute/annotation | 01-01, 02-01, 07-01 | COVERED |
| CONTEXT | D-03 | Base and individual ordinary/compact inline rows | 02-03, 03-01/02, 05-02, 08-01 | COVERED |
| CONTEXT | D-04 | Strict default, explicit no-fields, permissive opt-in | 01-01/02, 02-01/03, 06-01 | COVERED |
| CONTEXT | D-05 | Offered render coverage including all-no-fields registered sources and validated selection on POST; safe rejection | 01-01/02, 02-03, 03-01, 08-01 | COVERED |
| CONTEXT | D-06 | Options-only coverage and bounded/query-free inspection | 01-02, 02-01/02/03, 03-01 | COVERED |
| CONTEXT | D-07 | Hide ordinary, disable compact without losing columns | 03-01/02, 05-02, 08-01/02 | COVERED |
| CONTEXT | D-08 | Browser preservation then successful-save clearing | 01-01, 02-03, 03-02, 05-02, 07–08 | COVERED |
| CONTEXT | D-09 | Verified downstream adoption included | 07-01/02, 08-02, 09-01/02 | COVERED |
| CONTEXT | D-10 | Separate focused example with own models | 04-01/02, 05-01/03 | COVERED |
| CONTEXT | D-11 | Shared definitions, separate modules, ordinary/compact/source relevance | 04-01, 05-02/03, 08-01 | COVERED |
| CONTEXT | D-12 | Reciprocal valid docs/example links | 06-01/02, 08-01, 09-01/02 | COVERED |
| CONTEXT | D-13 | Original issue handoff | Already completed as issue #360; acknowledged in 01 must_haves and all execution boundaries | COVERED; historical, no duplicate filing |
| RESEARCH | API | One shared immutable source plus memberships; existing group authority | 01-01, 02-01/03 | COVERED |
| RESEARCH | key bounds | str/int(nonbool)/UUID; unique native scalar to_field_name; reject ambiguous hooks/widgets | 02-01, 06-01 | COVERED |
| RESEARCH | admission | Label-only customization; native iterator/options; changed restricted queryset | 01-02, 02-01/03, 07-01/02 | COVERED |
| RESEARCH | projection | One render-local offered projection, native prepare_value, no label/category scan; empty ToggleGroup guard for base/ordinary and automatic compact guard | 01-02, 02-03, 03-01 | COVERED |
| RESEARCH | diagnostics | Unbound precise exception; bound visible escaped diagnostic outside hidden group including siblings/extras | 01-02, 03-01, 08-01 | COVERED |
| RESEARCH | dynamic metadata | Explicit dynamic empty list vs malformed static; layout-only disable marker | 01-02, 03-01/02, 06-02 | COVERED |
| RESEARCH | form authority | Final inherited cleaned mapping, trusted disabled precedence, model validation, explicit empty values | 02-03 | COVERED |
| RESEARCH | persistence | Empty/deleted extras, unchanged existing cleanup, row identity and atomic parent/sibling saves | 02-03, 05-02, 07-02, 08 | COVERED |
| RESEARCH | schema/checks | Query-free startup and compact schema; inspect inline classes; reject queryset whole-formset toggles | 02-02, 03-01 | COVERED |
| RESEARCH | lifecycle | Exact owner/prefix, reset/cancel, modal and row insertion, independent disabled state | 03-02, 08-01/02 | COVERED |
| RESEARCH | examples | Own app models/migration/routes in 04; coherent seed/navigation integration in 05-01; service teaching domain | 04, 05 | COVERED |
| RESEARCH | source panels | Explicit bounded app-local per-page files, preserve defaults | 05-03 | COVERED |
| RESEARCH | downstream | Preserve active+current queryset, retained retired/subscription, optional coffee, print/model safeguard | 07, 08-02, 09-02 | COVERED |
| RESEARCH | downstream findings | Update 20 and stale ProductSelect wording in 34 after corresponding evidence | 07-02, 09-02 | COVERED |
| RESEARCH | reproducibility | Locked JS tree repair; actual import/static path and runtime fingerprints | 03-02, 07-02, 08, 09 | COVERED |
| RESEARCH | supported runtimes | Core 4.2/5.2/6.0 and crispy floor distinct from 6.1.2 examples/downstream | 09-01 | COVERED |
| RESEARCH | browser isolation | Actual served routes/DB outcomes; temporary SQLite/media; cleanup/captures | 08-01/02 | COVERED |
| RESEARCH | documentation | Executable strict/permissive recipes, costs/bounds, local vs published links, release notes | 06, 09 | COVERED |
| RESEARCH | security | ASVS 4.0.3 L1; allowed queryset, row ownership, escaped metadata, bounded queries, atomicity | Threats T-06.30-01–19, task map in VALIDATION | COVERED |
| RESEARCH | no new packages | No feature dependency; existing-lock npm ci only repairs reproducible environment | 03-02 | COVERED |

## Acceptance audit

| AC | Concrete planned evidence | Tasks | Status |
|---|---|---|---|
| AC-1 | Same mapping in three layouts, shared categories/no-fields | 01-01, 03-01, 04-01, 05-02, 08-01 | COVERED |
| AC-2 | Strict offered and no-GET selected checks, including base/ordinary/compact sources with no controlled fields; safe diagnosable rejected response | 01-02, 02-03, 03-01, 08-01 | COVERED |
| AC-3 | Changed category, restricted/forged/stale key, permissive/unused/no-offered categories | 01-02, 02-01/03, 07-02 | COVERED |
| AC-4 | Blank/required/invalid/disabled controller; no raw fallback | 01-01/02, 02-01/03 | COVERED |
| AC-5 | Active required and inactive invalid clearing, empty overrides, disabled/model constraints | 02-03, 04-01 | COVERED |
| AC-6 | Exact row scope on initial/change/redisplay/reset/insertion/modal | 03-01/02, 05-02, 08 | COVERED |
| AC-7 | Ordinary hide, compact alignment/disabled and focused-control recovery, labels/errors/control identities | 03, 05-02, 08 | COVERED |
| AC-8 | Away/back preserve and actual save/reopen/no-JS/unchanged cleanup | 01-01, 02-03, 03-02, 05-02, 07–08 | COVERED |
| AC-9 | Empty/deleted/atomic rows; static/checkbox/whole-formset regressions | 02-02/03, 03-02, 05-02, 07-02, 09-01 | COVERED |
| AC-10 | Zero schema/check queries; 2-vs-20 annotated options, 1-vs-20 ordinary/compact/downstream rows with native baseline/total SQL, and no category scan | 01-02, 02, 03-01 | COVERED |
| AC-11 | Own app, all three demos and required seed categories | 04–05, 08-01 | COVERED |
| AC-12 | Navigation/relevant source panels/reciprocal links/executable recipes | 05-03, 06, 08-01, 09 | COVERED |
| AC-13 | Verified roastery migration, retained products, optional coffee, print/model preservation | 07, 08-02, 09-02 | COVERED |
| AC-14 | Meaningful Python/templates/JS/browser/docs/lint; both repositories' evidence | all task checks, 08–09 | COVERED |

## Dependency and file ownership audit

| Wave | Plans | Needs → creates |
|---|---|---|
| 1 | 01 | Existing group/save seams → real render/save tracer, source API and safe rendering |
| 2 | 02 | 01 → structural bounds/checks and authoritative row/query proofs |
| 3 | 03 | 02 → compact rendering and complete JS lifecycle |
| 4 | 04, 07 | 03 → independent upstream own-model routed/migrated standalone editor; independent downstream adoption |
| 5 | 05 | 04 → seeded/navigation-integrated demo, ordinary/compact routes and source panels |
| 6 | 06 | 05 → documentation anchors and reciprocal Feature DocRefs |
| 7 | 08 | 05+06+07 → focused harness self-tests, then complete browser evidence |
| 8 | 09 | 06+08 → final source-bound acceptance and reconciled findings |

Same-wave files_modified intersections are empty. All 20 tasks have an automated command followed immediately by fails_when; all tasks except 04-01 modify at most five files. Task 04-01 includes two trivial package/AppConfig scaffold files alongside its five behavior files, a bounded seven-file exception for runnable first-use imports. The first executable task is the single tracer. Later plans expand that proven path; they do not invent independent tracers.

Plan 08 explicitly depends on 06 so documentation anchors and Feature DocRefs exist before browser link acceptance. Final 09 still refreshes any browser target whose recorded runtime/config/source hashes changed. Plan 04 has eleven files/two tasks with package/AppConfig scaffold before app installation; complete seed/navigation integration stays in 05-01, leaving plan 05 at eight files/three tasks. No task or scope obligation is removed.

Focused browser feedback is node tests/browser/queryset-conditional.cjs --self-test --target upstream in 08-01 and the downstream target in 08-02. These run the runner's actual positive/negative evidence checks and exception-path cleanup offline, reject zero assertions, and never create acceptance JSON. Complete browser/HTTP/DB acceptance commands remain mandatory in both tasks.

## Review round 1 coverage — 2b09a61c

| Finding | Executable task coverage | Disposition |
|---|---|---|
| H1 | 01-01, 02-01/02/03 | Category-aware is_on plus all five ValueToggle-gated seams explicitly named/tested |
| R1 | 01-02, 03-01, 06-01 | No-fields declaration/guard retained; rejection alternative explicitly rejected |
| R2 | 01-02, 02-01 | Native prepared values converted to HTML text; UUID regression |
| R3 | 02-03, 03-01, 06-01, 07-02 | Baseline/total row and option costs measured/documented; cross-form cache rejected |
| R4 | 02-02 | E313 hint covers both static/queryset admission |
| R5 | 02-01 | Mixed-kind ownership conflicts in both orders |
| R6 | 03-02, 08-01 | Visible disabled compact focus recovery tested in unit/browser layers |
| R7 | 04-01 | Name-only Service labels and query slope |
| R8 | 05-03 | One bounded navigation case with rationale/default preservation |
| R9 | 04-01, 05-02 | URLField validation preserved; row widget is admitted exact TextInput |
| R10 | 06-01 | Separate formsets compact exclusion explicitly rewritten |
| R11 | 07-02, 09-01 | Normal behavior tests run without binding; acceptance always requires binding |
| R12 | 08-01/02 | Focused negative/cleanup proof retained with finite local-helper scope |
| R13 | 08-01/02 | Explicit target interpreter/import paths and startup checks |
| R14 | 08-01, 09-01/02 | Runtime hashes and docs/link hashes distinguished; explicit reconciliation exclusions |

Raw-review advisories are also dispositioned in affected PLAN ledgers: first-use app scaffolding, historical JS provenance, compact marker location, standalone mixin order, source override ownership, adoption wording timing, polymorphic retention/SQL, static serving and extra crispy-floor selections. No implementation or runtime pass is claimed. Waves and task IDs are unchanged; source authority remains the approved context/design.

## Review round 2 coverage — d8dd7b82

| Finding | Executable task coverage | Disposition |
|---|---|---|
| C2-01 | 05-01/03, 06-02 | Existing valid DocRef at registration; expected forms catalog updated before project gate; new references follow headings/backlinks |
| C2-02 | 04-01 | Temporary URLConf preserves all project routes and appends current standalone ViewSet patterns directly |
| C2-03 | 08-01/02 | Served toggle.js bytes must equal the explicit current upstream source file, independently of import identity |
| C2-04 | 01-01 | Query-free native validate_field protocol exists before the tracer invokes the widened group loop |
| C2-05 | 02-01 | Existing unique_text fixture proves non-PK rendered option/metadata/prepared-token equality and native POST |
| C2-06 | 06-01/02 | Markdown-owning 06-01 adds required admonition backlinks; 06-02 wires references and checks them |
| C2-07 | 08-01/02 | Mutation scenarios restore fixture state in finally and verify it before continuing |
| C2-08 | 09-01 | Both available Django 4.2/6.0 crispy-floor selections are mandatory with distinct actual results |

Prior Round 1 ledgers and scope remain intact. The absent-category semantic change is rejected against the approved unmatched/permissive contract; the unmigrated-table objection is rejected by the installed Django run_syncdb test setup. Other cycle-two advisory observations retain their already specified no-container guards, exact cell markers/geometry, repeat-safe focus, native/query-free admission, ordinary helpers, dynamic-empty documentation and bounded tooling. No new feature or task is introduced; 9 plans, 20 tasks and 8 waves remain.

## Discovery and exclusions

Existing RESEARCH/PATTERNS supplied current live-code and official Django/crispy discovery; no new library research was needed. Graph status returned exists=false. Agent-skills mapping was empty and no project skill directory was found. Relevant prior 06.27/06.24 summary contracts were read for static/checkbox ownership, crispy schema and persistence preservation.

Assumption-delta detected=false; no identity decision checkpoint. Schema-push contribution's listed non-Django ORMs do not apply: the example uses normal Django migration/test-database execution. No SPEC/UI-SPEC or AI integration was supplied/needed; frontend gate returned false/nonblocking. Spec-less edge probe was visibly skipped due to absent formal IDs; this audit preserves every concrete accepted edge instead.

Excluded exactly as approved: AJAX/autocomplete, dynamic radios, multiselect, arbitrary widget adapters, predicate engine, queryset whole-formset toggles, general source browser and new concurrency guarantees. No category-dimension scan, new business requirement for coffee fields, real-data bulk migration, push or deploy is planned. D-13 handoff is historical.

No unplanned source item remains. This audit does not claim implementation, tests or browser acceptance has already passed.

