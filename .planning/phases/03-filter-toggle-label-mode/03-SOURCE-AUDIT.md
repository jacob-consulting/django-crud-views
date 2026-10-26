# Phase 03 — Source Audit

Planning basis: current tracked source at `92bf0dc085f628939cfad323dea7ecfde23fff79`, locked 03-CONTEXT.md,
03-RESEARCH.md, 03-PATTERNS.md and FILT-01 through FILT-04. All entries below are planned coverage, not execution
results. Maintainer discussion supplies the roadmap's design clarification; no separate SPEC is needed.

## Multi-source coverage

| Source | ID | Feature/constraint | Plan/task | Status | Notes |
|--------|----|--------------------|-----------|--------|-------|
| GOAL | Phase 3 | Configured accessible filter toggle | 03-01-01/02/03, 03-02-01 | COVERED | Real render, interaction, localization and public contract |
| REQ | FILT-01 | Both/label presentation; unchanged icon default | 03-01-01/02 | COVERED | Raw pre-change strings plus unchanged normalized toolbar golden |
| REQ | FILT-02 | Icon-less collapse and persistence | 03-01-02 | COVERED | Real handler, exact request assertions and failure paths |
| REQ | FILT-03 | Constant visible text | 03-01-01/02 | COVERED | Default/Unicode custom labels, two clicks, both initial states |
| REQ | FILT-04 | Translated Filter and German catalog | 03-01-01/03 | COVERED | Runtime sentinel, PO entry, explicit compiled membership, German render |
| CONTEXT | D-01 | No target default; existing whole-map precedence | 03-01-01/02 | COVERED | Existing resolver, conflicting map/floor tests |
| CONTEXT | D-02 | Declared key and direct button override | 03-01-01/02 | COVERED | self.key/self; renamed search case |
| CONTEXT | D-03 | Usable host pair, mixed child fallback | 03-01-01/02 | COVERED | Full matrix, both mixed directions and empty/None host slot |
| CONTEXT | D-04 | Constant default/custom label | 03-01-01/02 | COVERED | DOM node/text identity through success and error paths |
| CONTEXT | D-05 | Icon accessibility/default bytes; both no title/tooltip | 03-01-01/02 | COVERED | Baseline committed before runtime edits |
| CONTEXT | D-06 | Label has no icon hooks; preserve failure semantics | 03-01-02 | COVERED | Adapter false/throw, POST rejection, out-of-order settlement |
| CONTEXT | D-07 | Labels, variants and whole templates retain control | 03-01-01/02/03 | COVERED | File/code templates get mode; custom labels still win |
| CONTEXT | D-08 | Compact docs/examples and canonical-order link | 03-02-01 | COVERED | Five reference pages; no custom-template tutorial |
| CONTEXT | D-09 | Translate seed and preserve custom labels | 03-01-01/03 | COVERED | Runtime gettext and core PO/MO |
| CONTEXT | D-10 | Visibility, IDs, collapse, persistence and reset unchanged | 03-01-01/02 | COVERED | Existing regression suites plus direct absence and POST/GET cases |
| CONTEXT | D-11 | Changelog and full quality gates | 03-02-02 | COVERED | Fixed classification; actual new Breaking change would need migration companion |
| RESEARCH | R-01 | Reuse context resolver without target argument | 03-01-01/02 | COVERED | No duplicate resolver, no cv_button_data routing |
| RESEARCH | R-02 | Resolved mode reaches class lookup | 03-01-01/02 | COVERED | Distinct per-mode classes in rendered tests |
| RESEARCH | R-03 | Server context/template owns mode, client owns toggle | 03-01-01/02 | COVERED | Architectural responsibility map retained |
| RESEARCH | R-04 | Existing JS empty icon loop already works | 03-01-01/02 | COVERED | Test-only JS scope exercises the unchanged real handler, including all failure and label-stability cases |
| RESEARCH | R-05 | Normalized golden cannot prove raw bytes | 03-01-01 | COVERED | Two exact pre-change inline raw fixtures, source HEAD/commit evidence |
| RESEARCH | R-06 | German spelling alone cannot prove translation | 03-01-03 | COVERED | Distinct Unicode gettext sentinel and compiled membership |
| RESEARCH | R-07 | Direct leaf tests need explicit resolved mode | 03-01-01 | COVERED | Update tracked test_button_leaves.py helper |
| RESEARCH | R-08 | Existing floor tests intentionally exclude filter | 03-01-02 | COVERED | Dedicated filter floor tests; correct obsolete comment |
| RESEARCH | R-09 | Lazy floor and strict short-circuit | 03-01-02 | COVERED | override_settings restore; explicit mode with invalid strict floor |
| RESEARCH | R-10 | 24 presentation combinations and unusable host slots | 03-01-02 | COVERED | 3 modes × 2 states × 4 placements plus fallback |
| RESEARCH | R-11 | Template customization and access visibility | 03-01-02 | COVERED | Both file/code hooks, variants, pinned/non-filter absence |
| RESEARCH | R-12 | Catalog compilation uses installed tooling | 03-01-03 | COVERED | Core PO/MO only; msgfmt available; no dependency change |
| RESEARCH | R-13 | Stale fixed-icon docs across references | 03-02-01 | COVERED | Compact contract, tooltip table, class and icon descriptions |
| RESEARCH | R-14 | ASVS1 encoding/CSRF/state integrity | 03-01-02, 03-02-01 | COVERED | Threats T-03-01 through T-03-05; SC reserved in both plans |
| RESEARCH | R-15 | Full gates and installed-version caveats | 03-02-02 | COVERED | Prior commands retained; baseline failures never presented green |
| RESEARCH | R-16 | No new dependencies, version bump or downstream edits | Both plans | COVERED | Scope notes and generic follow-up in execution summary |

No source item is missing. Form leaves, other adapters, stability freeze, downstream implementation and dependency
upgrades belong outside this phase. Rejected always-child both placement and a full custom-template tutorial are
not planned. Source-plan literal filter-key guidance is superseded by locked D-02's declared-key rule.

## Dependency graph and sizing

| Task | Needs | Creates | Checkpoint |
|------|-------|---------|------------|
| 03-01-01 | Completed Phase 1 resolver and existing harnesses | Raw baseline; real both-mode render/toggle/POST-GET slice | No; public behavior already locked |
| 03-01-02 | Tracer context/template/tests | Label mode and full placement/customization/failure coverage | No |
| 03-01-03 | Tracer gettext call and completed mode behavior | Compiled German catalog and anti-false-positive tests | No |
| 03-02-01 | Completed implementation and its summary | Accurate compact reference contract | No |
| 03-02-02 | Completed references and behavior | Release note and full gate evidence | No |

Wave 1: 03-01 (three tasks). Wave 2: 03-02 depends on 03-01 (two tasks). Each task modifies at most five files.
Plan 03-01 modifies nine files, including the compiled MO; Plan 03-02 modifies six. The existing production filter
script remains a read/test dependency, with all browser coverage retained in tests/js/list.filter.test.js.
There are no same-wave file or mutable-resource conflicts. Calibration query returned factor 1, 0 samples, low
confidence; estimates are 36,000 and 15,000 tokens. No source omission or phase split is needed.

Research's three open-question entries are explicitly RESOLVED: Fixed classification and environment reporting
belong to 03-02-02; inline RAW_DEFAULT_FILTER baseline capture belongs to 03-01-01. No product decision remains open.

## Spec-less edge coverage

Input: `/tmp/gsd-phase03-edge-report.json`; engine reported 14 applicable, 14 initially unresolved, zero
unclassified. Every row now has an explicit scoped acceptance predicate in 03-01 must_haves.truths. The table maps
the original requirement/category pairs without dropping or dismissing any row. No backstop or unresolved product
assumption remains; request ordering tests describe existing local state behavior and add no server ordering promise.

| Requirement | Category | Predicate / evidence owner | Resolution |
|-------------|----------|----------------------------|------------|
| FILT-01 | empty | None/empty/unrelated mode maps and live floor, direct instance; 03-01-02 | resolved / explicit |
| FILT-01 | encoding | Exact raw default render strings, both states; 03-01-01 | resolved / explicit |
| FILT-02 | adjacency | Shared host class tokens survive swaps; 03-01-02 | resolved / explicit |
| FILT-02 | empty | No icon hooks still toggles; absent toggle safe; 03-01-02 | resolved / explicit |
| FILT-02 | encoding | Exact boolean JSON/request headers; 03-01-01/02 | resolved / explicit |
| FILT-02 | ordering | Collapse before DOM/POST; refusal and rejection behavior; 03-01-02 | resolved / explicit |
| FILT-02 | idempotency | Two accepted clicks restore state, one POST each; 03-01-02 | resolved / explicit |
| FILT-02 | concurrency | Deferred responses never roll back latest DOM state; 03-01-02 | resolved / explicit |
| FILT-03 | empty | Empty custom result preserves translated seed; 03-01-02/03 | resolved / explicit |
| FILT-03 | encoding | Unicode textContent stable; raw label escaping; 03-01-02 | resolved / explicit |
| FILT-03 | idempotency | Same label node/text after two clicks; 03-01-02 | resolved / explicit |
| FILT-03 | concurrency | Adapter/network outcomes never mutate label; 03-01-02 | resolved / explicit |
| FILT-04 | empty | Required non-fuzzy PO and explicit MO entry; 03-01-03 | resolved / explicit |
| FILT-04 | encoding | Unicode translation sentinel and active German render; 03-01-03 | resolved / explicit |

No-silent-drop equality: 14 surfaced = 14 authored edge truths + 0 flagged unresolved assumptions.
The larger-than-usual truth list is deliberate: each deterministic probe row retains its own predicate.

## Prohibition recall and precision

The two-stage prose recall ran per requirement; no compiled recall engine was assumed. Raw candidates:

| Requirement | Ten recalled must-NOT candidates | Precision outcome |
|-------------|----------------------------------|-------------------|
| FILT-01 | ignore map; borrow target; hard-code key; change default bytes; lose name; retain visible-mode tooltip; force child placement; leak host icons in label mode; discard custom template; inject unescaped label | First nine are ordinary correctness already covered; injection is canon security |
| FILT-02 | require icons; omit ARIA; rename panel ID; skip persistence; duplicate per-click POST; persist refused state; roll back successful toggle on network failure; drop reset keys; break no-button pages; remove CSRF | First nine are ordinary interaction correctness; CSRF is canon security |
| FILT-03 | replace label by state; change custom text; normalize Unicode; append icon names to text; replace label node; alter text on rejected request; alter text on adapter throw; lose empty-label fallback; let late response overwrite text; interpret raw label as HTML | First nine are ordinary text/state correctness; injection is canon security |
| FILT-04 | bypass gettext; translate at import time; omit PO entry; omit MO key; leave fuzzy entry; allow missing entry to pass via identical spelling; overwrite custom label; leak active language between tests; corrupt non-ASCII catalog text; inject translated raw markup | First nine are ordinary localization correctness; injection is canon security |

Injection and CSRF are canon — covered by the phase threat models and `$gsd-secure-phase`, not minted as bespoke
prohibitions. Zero bespoke values/safety/ethics candidates survive precision for this presentation utility.
Both plans therefore carry `prohibitions: []`; there is no retained item requiring projection/check descriptors,
no fabricated wired check and no auto-dismissed unresolved prohibition. Equality: 0 kept = 0 authored + 0 flagged.

## Discovery, detectors and known limits

- Discovery Level 0: existing tracked resolver, template/icon/class seams, JS handler, tests and translation tooling
  fully cover the change. Research already verified external framework details; no new library lookup is required.
- Graph status: `exists: false`; no graph context was inferred. API-SURFACE.md's empty symbol inventory is not
  authoritative; file paths and interfaces were grounded in live tracked source.
- Assumption-delta scan for 03: `detected: false`, no signals. No modeling decision checkpoint is created.
- API-coverage detector ran on the roadmap section and both complete plans: `detected: true` for existing template
  API adoption wording. COVERAGE.md records the required reasoned no-external-integration declaration; the signal
  names the package's existing configuration/template interface, not an external service capability.
- Schema scan: no scoped path matches the contribution's ORM/schema patterns; no schema-push task applies.
- UI gate: frontend=false for this existing template branch; no UI-SPEC is required.
- No package installs: package-legitimacy install gating is dormant; T-03-SC remains present in each plan.
- Raw baseline creation is execution work and must precede runtime edits. Planning does not claim the fixture exists.
- Observed Ruff 0.16.10, Vitest 4.1.10 and jsdom 29.1.1 differ from manifest ranges; existing focused runs passed in
  research. Plans retain all full gates and report actual versions/failures. No environment upgrade is authorized here.
- No broad product suites were run during planning. Structure/frontmatter/path checks validate plans, not behavior.
