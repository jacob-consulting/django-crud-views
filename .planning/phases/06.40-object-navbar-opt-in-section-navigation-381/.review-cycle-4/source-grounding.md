# Source-grounding coverage — cycle 4

Effective authority: intel. Python, template and CLI/signature references are UNCHECKABLE under the empty JS-only index. New artifacts/API references are skipped, not missing. Supplemental direct reads are distinct from adapter verification.

Counts: {'UNCHECKABLE': 4339, 'SKIPPED': 398}. Full exact quotes, current line provenance and per-reference reasons are in source-grounding.json.

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:6
> depends_on: []

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:7
> files_modified: ["src/crud_views/lib/navbar.py","src/crud_views/templatetags/crud_views.py","src/crud_views/templates/crud_views/tags/navbar.html","tests/test1/test_navbar.py","tests/test1/test_navbar_checks.py","src/crud_views/checks.py"]

check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; files_modified — UNCHECKABLE; navbar.html — UNCHECKABLE; navbar.py — UNCHECKABLE; navbar_ — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; tag — UNCHECKABLE; tags/navbar.html — UNCHECKABLE; template — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED; tests/test1/test_navbar_checks.py — SKIPPED; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:12
>   raw_tokens: 30000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:17
>     - "A single declaration renders owner identity and the exact registered GET destination (AC1)."

declaration — UNCHECKABLE; identity — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:18
>     - "Owner identity and target URLs remain stable through descendants and nested owners (AC2)."

identity — UNCHECKABLE; owners — UNCHECKABLE; stable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:19
>     - "Invalid attachment or destinations fail at startup without database work (AC6)."

Invalid — UNCHECKABLE; fail — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:20
>     - "Cold URLconf completion safely includes late views on existing and new ViewSets in the same completed system-check pass (R20)."

ViewSet — UNCHECKABLE; ViewSets — UNCHECKABLE; check — UNCHECKABLE; complete — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:22
>     - path: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:23
>       provides: "NEW public NavBar, NavItem, CrudViewNavBarMixin; private builder/resolver/check implementation in this one module."

CrudViewNavBarMixin — SKIPPED; NavBar — SKIPPED; NavItem — SKIPPED; check — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:24
>     - path: "src/crud_views/templates/crud_views/tags/navbar.html"

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:25
>       provides: "NEW guarded layout-B wrapper; later plan 02 extracts its identity/items leaves."

guarded — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; layout — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:26
>     - path: "tests/test1/test_navbar.py"

test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:27
>       provides: "NEW real-request declaration/routing fixtures and tests."

declaration — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:28
>     - path: "tests/test1/test_navbar_checks.py"

test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_checks.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:29
>       provides: "NEW startup-check matrix."

check — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:30
>     - path: "src/crud_views/templatetags/crud_views.py"

crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; src/crud_views/templatetags/crud_views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:31
>       provides: "EXISTING module: add public cv_navbar template tag."

add — UNCHECKABLE; cv_navbar — SKIPPED; tag — UNCHECKABLE; template — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:32
>     - path: "src/crud_views/checks.py"

check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; crud_views — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:33
>       provides: "EXISTING system-check entry point completes URLconf before registry iteration; shared readiness helper supports an import-free probe."

before — UNCHECKABLE; check — UNCHECKABLE; complete — UNCHECKABLE; help — UNCHECKABLE; helper — UNCHECKABLE; probe — UNCHECKABLE; registry — UNCHECKABLE; up — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:34
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:35
>     - from: "src/crud_views/templatetags/crud_views.py"

crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; src/crud_views/templatetags/crud_views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:36
>       to: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:37
>       via: "Consume one view-local lazy cv_navbar value."

cv_navbar — SKIPPED; value — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:38
>     - from: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:39
>       to: "src/crud_views/lib/ancestors.py"

ancestors.py — UNCHECKABLE; crud_views — UNCHECKABLE; src/crud_views/lib/ancestors.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:40
>       via: "_resolved_ancestor and _walk_ancestors reuse resolved identity."

_resolved_ancestor — UNCHECKABLE; _walk_ancestors — UNCHECKABLE; identity — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:41
>     - from: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:42
>       to: "src/crud_views/lib/viewset/__init__.py"

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; crud_views — UNCHECKABLE; src/crud_views/lib/viewset/__init__.py — UNCHECKABLE; viewset — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:43
>       via: "Literal registration then target-specific reverse."

-s — UNCHECKABLE; get — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:44
>     - from: "src/crud_views/checks.py"

check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; crud_views — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:45
>       to: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:46
>       via: "check_viewsets preflight precedes checks_all snapshot; cooperative navbar checks only probe cached URLconf readiness."

all — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; probe — UNCHECKABLE; set — UNCHECKABLE; snapshot — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:50
> Establish the opt-in object-navbar path, exact destinations and startup diagnostics.

-n — UNCHECKABLE; up — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:51
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:52
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:53
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:56
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:57
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:58
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:59
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:61
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:62
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:63
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:64
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:65
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:66
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:67
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:68
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:69
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:70
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:71
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:75
> - `src/crud_views/lib/navbar.py`: NEW public NavBar, NavItem, CrudViewNavBarMixin; private builder/resolver/check implementation in this one module.

CrudViewNavBarMixin — SKIPPED; NavBar — SKIPPED; NavItem — SKIPPED; check — UNCHECKABLE; crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:76
> - `src/crud_views/templates/crud_views/tags/navbar.html`: NEW guarded layout-B wrapper; later plan 02 extracts its identity/items leaves.

crud_views — UNCHECKABLE; guarded — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; layout — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:77
> - `tests/test1/test_navbar.py`: NEW real-request declaration/routing fixtures and tests.

declaration — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:78
> - `tests/test1/test_navbar_checks.py`: NEW startup-check matrix.

check — UNCHECKABLE; matrix — UNCHECKABLE; test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_checks.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:79
> - `src/crud_views/templatetags/crud_views.py`: EXISTING module: add public cv_navbar template tag.

add — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; cv_navbar — SKIPPED; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:80
> - `src/crud_views/checks.py`: EXISTING startup integration: complete URLconf before collecting checks and expose an import-free readiness mode; preserve existing ancestor-check defaults.

before — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; complete — UNCHECKABLE; crud_views — UNCHECKABLE; default — UNCHECKABLE; mode — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; up — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:82
> Discovery level 0: source-grounded existing Django/Pydantic/registry patterns; existing research verifies library details. A-01/A-03/A-04 adopted with literal-key and structural-kwargs refinements. The initial wrapper is the production path; plan 02 extracts the approved override leaves without changing this data contract. New stable surface is already authorized by D-16; no new decision checkpoint.

data — UNCHECKABLE; key — UNCHECKABLE; kwargs — UNCHECKABLE; level — UNCHECKABLE; registry — UNCHECKABLE; source — UNCHECKABLE; stable — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:86
>   <name>06.40-01-01: Render one declared owner link through a real request</name>

link — UNCHECKABLE; name — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:87
>   <files>src/crud_views/lib/navbar.py, src/crud_views/templatetags/crud_views.py, src/crud_views/templates/crud_views/tags/navbar.html, tests/test1/test_navbar.py</files>

crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; navbar.html — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; tags/navbar.html — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:88
>   <read_first>src/crud_views/lib/breadcrumb.py; src/crud_views/lib/view/base.py; src/crud_views/lib/view/context.py; src/crud_views/templatetags/crud_views.py; tests/test1/test_ancestor_authorization.py; tests/test1/test_breadcrumb.py</read_first>

base — UNCHECKABLE; base.py — UNCHECKABLE; breadcrumb.py — UNCHECKABLE; context — UNCHECKABLE; context.py — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; read_first — UNCHECKABLE; src/crud_views/lib/breadcrumb.py — UNCHECKABLE; src/crud_views/lib/view/base.py — UNCHECKABLE; src/crud_views/lib/view/context.py — UNCHECKABLE; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; test_ancestor_authorization — UNCHECKABLE; test_ancestor_authorization.py — UNCHECKABLE; test_breadcrumb — UNCHECKABLE; test_breadcrumb.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_ancestor_authorization.py — UNCHECKABLE; tests/test1/test_breadcrumb.py — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:89
>   <behavior>Real owner GET -> identity and owner URL; SafeString caption/label -> escaped text; no configuration -> no output.</behavior>

SafeString — UNCHECKABLE; caption — UNCHECKABLE; identity — UNCHECKABLE; label — UNCHECKABLE; owner — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:90
>   <action>Per D-01/D-03/D-05/D-07/D-09/D-11/D-13/D-14, create the single navbar module, its Pydantic NavItem(key: str | None = None, child: str | None = None, label=None, icon=None), NavBar(viewset: str, items: list[NavItem], template: str | None = None), and cooperative CrudViewNavBarMixin.cv_navbar=None. Keep declarations configuration-only and all resolution/building helpers private. Use Pydantic features available at 2.2.1; accept lazy translated labels without preserving HTML safety. Add one view-instance SimpleLazyObject in get_context_data without evaluating it, with None for modal requests (X-CV-Modal: true). Add the context-taking cv_navbar tag and guarded layout-B wrapper. Wire one real owner detail GET, declaration, lazy context, access then existing state helper, registered reverse and escaped identity/link HTML. Reuse the existing icon renderer. Addresses review concern R17 per D-05/D-11: call the destination's cv_get_action_short_label with a request-local ViewContext whose view is the rendering view and whose object is the resolved navbar owner. Do not mutate the rendering view's object/context or shared declarations. Only perform this label work after access and state pass. Add an object-dependent short-label template regression on the real owner request; Task02 extends the same assertion to descendants with distinct object captions. Addresses review concern R1: normalize only the already-rendered result of cv_get_action_short_label with one stdlib html.unescape pass, then remove SafeData by coercing to an exact built-in str (str.__str__(str(value))). This preserves its rendered ampersands/apostrophes without carrying HTML trust into navbar data. For raw str(owner), explicit NavItem.label, and child plural labels, remove SafeData the same way but never entity-decode them: literal entity-looking input must remain literal. Keep any markup characters as text, without stripping tags or adding an HTML parser/sanitizer. Ordinary Django autoescape then escapes the normalized text exactly once in text and attribute contexts; do not force-escape the rendered default a second time. Test default template literals and interpolated values, explicit labels and owner captions with ampersands, apostrophes, literal entity sequences, safe markup and lazy translations; assert both serialized escaping and parsed visible text, with no created markup. The tag selects bar.template or theme-path tags/navbar.html and returns exactly empty output with absent/None/falsy data. Keep base.py, router, ancestor policy and context-button implementation untouched. Addresses review concerns R7/R9: own the real-request harness inside test_navbar.py using a test-local locmem template loader prepended to normal loaders and cv_extends_template selecting that base. Derive the local base from the unchanged app/crud_views.html layout and insert the tag with whitespace-neutral delimiters immediately before its existing header/card; keep an otherwise identical tag-free base for paired comparisons. Do not edit the shared test base. Import tests.test1.project.urls before taking registry snapshots, matching isolated_routes in test_ancestor_authorization.py; reuse that context manager or preserve its ordering exactly. Restore registry and check_module._VOCAB_CACHE snapshots, temporary URLconf module, URL caches and ContentType cache in finally; snapshot/restore any existing ViewSet._default_permissions values touched by tests. First tests prove this real path, not only builder return dictionaries. Addresses review concern R13: viewset and child remain string names throughout declaration; no ViewSet object, callable resolver or registration-time lookup is accepted. Prove a declaration can precede registration of its owner and child, then renders after they register. Pydantic handles field-type errors at construction. Addresses review concern R11: items=[] is valid and renders nothing; NavItem() is structurally representable but an attached item with neither a nonempty owner key nor a nonempty child name is a named startup error. This keeps destination-shape diagnostics in the same cooperative check pipeline as A-04. Empty supplied names/keys are invalid selections, not aliases for an omitted key.</action>

ContentType — UNCHECKABLE; CrudViewNavBarMixin — SKIPPED; CrudViewNavBarMixin.cv_navbar — SKIPPED; First — UNCHECKABLE; NavBar — SKIPPED; NavBar(viewset: str, items: list[NavItem], template: str | None = None) — UNCHECKABLE; NavItem — SKIPPED; NavItem() — UNCHECKABLE; NavItem(key: str | None = None, child: str | None = None, label=None, icon=None) — UNCHECKABLE; NavItem.label — SKIPPED; Ordinary — UNCHECKABLE; SafeData — UNCHECKABLE; SimpleLazyObject — UNCHECKABLE; ViewContext — UNCHECKABLE; ViewSet — UNCHECKABLE; ViewSet._default_permissions — UNCHECKABLE; _VOCAB_CACHE — UNCHECKABLE; __str__ — UNCHECKABLE; _default_permissions — UNCHECKABLE; action — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; app/crud_views.html — UNCHECKABLE; available — UNCHECKABLE; bar.template — UNCHECKABLE; base — UNCHECKABLE; base.py — UNCHECKABLE; before — UNCHECKABLE; button — UNCHECKABLE; check — UNCHECKABLE; check_module — UNCHECKABLE; check_module._VOCAB_CACHE — UNCHECKABLE; child — UNCHECKABLE; context — UNCHECKABLE; create — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; cv_extends_template — UNCHECKABLE; cv_get_action_short_label — UNCHECKABLE; cv_navbar — SKIPPED; data — UNCHECKABLE; declaration — UNCHECKABLE; default — UNCHECKABLE; detail — UNCHECKABLE; edit — UNCHECKABLE; error — UNCHECKABLE; errors — UNCHECKABLE; get_context_data — UNCHECKABLE; guarded — UNCHECKABLE; harness — UNCHECKABLE; helper — UNCHECKABLE; helpers — UNCHECKABLE; html.unescape — UNCHECKABLE; identity — UNCHECKABLE; invalid — UNCHECKABLE; isolated_routes — UNCHECKABLE; item — UNCHECKABLE; items — UNCHECKABLE; key — UNCHECKABLE; keys — UNCHECKABLE; label — UNCHECKABLE; labels — UNCHECKABLE; layout — UNCHECKABLE; link — UNCHECKABLE; lookup — UNCHECKABLE; mutate — UNCHECKABLE; name — UNCHECKABLE; navbar.html — UNCHECKABLE; owner — UNCHECKABLE; project — UNCHECKABLE; project.urls — UNCHECKABLE; register — UNCHECKABLE; registry — UNCHECKABLE; rendered — UNCHECKABLE; snapshot — UNCHECKABLE; state — UNCHECKABLE; str(owner) — UNCHECKABLE; str(value) — UNCHECKABLE; str.__str__ — UNCHECKABLE; tag — UNCHECKABLE; tags/navbar.html — UNCHECKABLE; template — UNCHECKABLE; test_ancestor_authorization — UNCHECKABLE; test_ancestor_authorization.py — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests.test1.project.urls — UNCHECKABLE; text — UNCHECKABLE; translated — UNCHECKABLE; unchanged — UNCHECKABLE; urls — UNCHECKABLE; value — UNCHECKABLE; values — UNCHECKABLE; view — UNCHECKABLE; viewset — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:91
>   <acceptance_criteria>AC1: a real participating owner GET renders one clickable Details item, plain owner identity above it, and its unchanged page header. Nonparticipating and unconfigured mixin views emit no navbar. The public import path is crud_views.lib.navbar; request data never enters shared declarations.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.lib.navbar — UNCHECKABLE; data — UNCHECKABLE; emit — UNCHECKABLE; identity — UNCHECKABLE; item — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; unchanged — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:92
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:93
>   <fails_when>Owner GET fails, link resolves to the wrong owner, plain text becomes markup, absent context emits HTML, or any new test is uncollected.</fails_when>

context — UNCHECKABLE; fails_when — UNCHECKABLE; link — UNCHECKABLE; owner — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:94
>   <done>AC1: a real participating owner GET renders one clickable Details item, plain owner identity above it, and its unchanged page header. Nonparticipating and unconfigured mixin views emit no navbar. The public import path is crud_views.lib.navbar; request data never enters shared declarations.</done>

crud_views — UNCHECKABLE; crud_views.lib.navbar — UNCHECKABLE; data — UNCHECKABLE; emit — UNCHECKABLE; identity — UNCHECKABLE; item — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; unchanged — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:98
>   <name>06.40-01-02: Carry the same owner through every supported section</name>

name — UNCHECKABLE; owner — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:99
>   <files>src/crud_views/lib/navbar.py, tests/test1/test_navbar.py</files>

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:100
>   <read_first>src/crud_views/lib/ancestors.py; src/crud_views/lib/viewset/__init__.py; src/crud_views/lib/viewset/parentviewset.py; src/crud_views/lib/view/buttons.py</read_first>

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; ancestors.py — UNCHECKABLE; buttons — UNCHECKABLE; buttons.py — UNCHECKABLE; crud_views — UNCHECKABLE; parentviewset.py — UNCHECKABLE; read_first — UNCHECKABLE; src/crud_views/lib/ancestors.py — UNCHECKABLE; src/crud_views/lib/view/buttons.py — UNCHECKABLE; src/crud_views/lib/viewset/__init__.py — UNCHECKABLE; src/crud_views/lib/viewset/parentviewset.py — UNCHECKABLE; view — UNCHECKABLE; viewset — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:101
>   <behavior>Parameterized real requests cover owner keys, five child page kinds, grandchild editing, omitted intermediate mixin, literal/default destination selection and custom higher-ancestor names. An object-dependent owner short-label template displays the same owner text on owner, child and grandchild requests despite distinct rendering objects.</behavior>

child — UNCHECKABLE; custom — UNCHECKABLE; default — UNCHECKABLE; keys — UNCHECKABLE; label — UNCHECKABLE; objects — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:102
>   <action>Expand the traced path per D-04/D-05/D-06/D-12. Resolve owner pages from self.object and descendants with _resolved_ancestor(view, owner_name), never a new object fetch; missing resolved state is a clear configuration/lifecycle error. Use bounded _walk_ancestors metadata to find the owner's direct child even across intermediate views without the mixin. Require literal registration before get_view_class/get_router_name for explicit keys; omitted child key selects registered list, then registered card only if list is absent. Do not substitute because a selected list is invalid or denied. Build kwargs from target ancestry names, resolved owner PK and only required higher-ancestor values from rendering kwargs. Addresses review concern R18: for owner links use owner_viewset.pk_name as the route argument name and owner.pk as its value; for child links use child.parent.get_pk_name() as the argument name with the same owner.pk value. Preserve cv_get_url_extra_kwargs for supported custom captures while structural PK values remain authoritative. Do not infer arbitrary dynamic route captures. Mark visible matching owner key or direct-child section active, retain active href, otherwise no active item. Keep item order and label/icon defaults: child plural/header icon, owner short action label; explicit overrides including empty icon win. Addresses review concern R17: extend Task01's object-dependent short-label test across real child and grandchild requests with distinct captions, asserting the same resolved owner's text at every depth and ViewContext.object identity with that owner.</action>

PK — UNCHECKABLE; ViewContext — UNCHECKABLE; ViewContext.object — UNCHECKABLE; _resolved_ancestor — UNCHECKABLE; _resolved_ancestor(view, owner_name) — UNCHECKABLE; _walk_ancestors — UNCHECKABLE; action — UNCHECKABLE; ancestry — UNCHECKABLE; before — UNCHECKABLE; bounded — UNCHECKABLE; child — UNCHECKABLE; child.parent.get_pk_name — UNCHECKABLE; child.parent.get_pk_name() — UNCHECKABLE; clear — UNCHECKABLE; custom — UNCHECKABLE; cv_get_url_extra_kwargs — UNCHECKABLE; error — UNCHECKABLE; get_pk_name — UNCHECKABLE; get_router_name — UNCHECKABLE; get_view_class — UNCHECKABLE; href — UNCHECKABLE; identity — UNCHECKABLE; invalid — UNCHECKABLE; item — UNCHECKABLE; key — UNCHECKABLE; keys — UNCHECKABLE; kwargs — UNCHECKABLE; label — UNCHECKABLE; links — UNCHECKABLE; missing — UNCHECKABLE; name — UNCHECKABLE; owner — UNCHECKABLE; owner.pk — UNCHECKABLE; owner_name — UNCHECKABLE; owner_viewset — UNCHECKABLE; owner_viewset.pk_name — UNCHECKABLE; pages — UNCHECKABLE; parent — UNCHECKABLE; pk_name — UNCHECKABLE; route — UNCHECKABLE; section — UNCHECKABLE; selected — UNCHECKABLE; self.object — UNCHECKABLE; state — UNCHECKABLE; text — UNCHECKABLE; use — UNCHECKABLE; value — UNCHECKABLE; values — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:103
>   <acceptance_criteria>AC2: unequal owner/child/grandchild PKs, alternate parent PK names and nested Tenant URLs give identical section hrefs at each depth; object-dependent default owner short labels show the resolved owner's text at every depth. Owner Update opens the owner's form and is active; Notes is separately active; unlisted owner views have no active item. Child list/detail/create/update/custom views and Item edit highlight Orders; explicit child Create/custom and card-only defaults open the exact selected destination.</acceptance_criteria>

Child — UNCHECKABLE; Create — UNCHECKABLE; Item — UNCHECKABLE; PK — UNCHECKABLE; Update — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; child — UNCHECKABLE; create — UNCHECKABLE; custom — UNCHECKABLE; default — UNCHECKABLE; detail — UNCHECKABLE; edit — UNCHECKABLE; hrefs — UNCHECKABLE; item — UNCHECKABLE; labels — UNCHECKABLE; open — UNCHECKABLE; owner — UNCHECKABLE; parent — UNCHECKABLE; section — UNCHECKABLE; selected — UNCHECKABLE; text — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:104
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:105
>   <fails_when>Any owner identity/href differs by rendering depth, explicit list silently becomes card, an invalid/denied list selects another page, extra kwargs replace structural identity, or active selection falls back to an unrelated item.</fails_when>

fails_when — UNCHECKABLE; href — UNCHECKABLE; identity — UNCHECKABLE; invalid — UNCHECKABLE; item — UNCHECKABLE; kwargs — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; replace — UNCHECKABLE; unrelated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:106
>   <done>AC2: unequal owner/child/grandchild PKs, alternate parent PK names and nested Tenant URLs give identical section hrefs at each depth; object-dependent default owner short labels show the resolved owner's text at every depth. Owner Update opens the owner's form and is active; Notes is separately active; unlisted owner views have no active item. Child list/detail/create/update/custom views and Item edit highlight Orders; explicit child Create/custom and card-only defaults open the exact selected destination.</done>

Child — UNCHECKABLE; Create — UNCHECKABLE; Item — UNCHECKABLE; PK — UNCHECKABLE; Update — UNCHECKABLE; child — UNCHECKABLE; create — UNCHECKABLE; custom — UNCHECKABLE; default — UNCHECKABLE; detail — UNCHECKABLE; edit — UNCHECKABLE; hrefs — UNCHECKABLE; item — UNCHECKABLE; labels — UNCHECKABLE; open — UNCHECKABLE; owner — UNCHECKABLE; parent — UNCHECKABLE; section — UNCHECKABLE; selected — UNCHECKABLE; text — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:110
>   <name>06.40-01-03: Reject invalid navbar configurations at startup</name>

invalid — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:111
>   <files>src/crud_views/lib/navbar.py, tests/test1/test_navbar_checks.py, src/crud_views/checks.py</files>

check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; navbar_ — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; test_navbar — UNCHECKABLE; test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_checks.py — SKIPPED; view — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:112
>   <read_first>src/crud_views/lib/check.py; src/crud_views/checks.py; src/crud_views/lib/viewset/__init__.py; src/crud_views/lib/breadcrumb.py; tests/test1/test_breadcrumb.py; installed supported Django django/urls/resolvers.py URLResolver.url_patterns and django/utils/functional.py cached_property</read_first>

URLResolver.url_patterns — UNCHECKABLE; __init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; all — UNCHECKABLE; breadcrumb.py — UNCHECKABLE; check — UNCHECKABLE; check.py — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; crud_views — UNCHECKABLE; functional.py — UNCHECKABLE; install — UNCHECKABLE; read_first — UNCHECKABLE; resolve — UNCHECKABLE; resolvers.py — UNCHECKABLE; set — UNCHECKABLE; src/crud_views/checks.py — UNCHECKABLE; src/crud_views/lib/breadcrumb.py — UNCHECKABLE; src/crud_views/lib/check.py — UNCHECKABLE; src/crud_views/lib/viewset/__init__.py — UNCHECKABLE; test_breadcrumb — UNCHECKABLE; test_breadcrumb.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_breadcrumb.py — UNCHECKABLE; up — UNCHECKABLE; url — UNCHECKABLE; urls — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:113
>   <behavior>Each A-04 invalid declaration -> named error; valid/None configurations -> no navbar error; startup -> zero queries and hook calls. Cold URLconf imports add invalid configured views to an existing ViewSet and a newly registered ViewSet -> the first completed check_viewsets call reports every distinct late diagnostic without RuntimeError. Failed/in-progress completion -> no retry/import during live view iteration, local errors still reported, registry-dependent errors deferred; a later completed call reports the late errors.</behavior>

ViewSet — UNCHECKABLE; add — UNCHECKABLE; all — UNCHECKABLE; calls — UNCHECKABLE; check — UNCHECKABLE; complete — UNCHECKABLE; configure — UNCHECKABLE; declaration — UNCHECKABLE; error — UNCHECKABLE; errors — UNCHECKABLE; hook — UNCHECKABLE; invalid — UNCHECKABLE; name — UNCHECKABLE; register — UNCHECKABLE; registry — UNCHECKABLE; set — UNCHECKABLE; up — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:114
>   <action>Per D-04/D-12/D-13 and AC6 add cooperative mixin checks, only for participating configured views; super checks still run. Search current check IDs and allocate unused IDs in navbar.py, documenting them in tests; no global registry or forgotten-mixin check. Validate malformed configured declaration safely; unknown owner/child, nondirect child, absent explicit target key (including explicit list where only card exists), owner target lacking object, child target requiring object, duplicate owner keys, repeated child ViewSets even with distinct keys, every owner attachment with cv_object=False (list, card, create and custom no-object pages), and unrelated attachment. A target must both allow get in http_method_names and have a callable get method; include registered POST-only ActionView, GET-excluded and noncallable-get cases. Diagnostics name attachment class, navbar owner and item index/key; bar-level errors explicitly identify the bar rather than pretending an item exists. Check before render and do no database/access/state work. Tests invoke the actual Django/system-check pipeline with isolated registrations and verify zero queries and super-check retention. Addresses review concerns R8/R20 per D-13: in the existing check_viewsets entry point, call _url_configuration_loaded before starting ViewSet.checks_all, so URLconf imports finish before both the ViewSet registry snapshot and any live per-ViewSet view iteration. Extend that existing helper with keyword-only load=True, preserving current default behavior for ancestor checks. With load=False, traverse the same resolver tree and bounded seen set using only each resolver's already-cached __dict__["url_patterns"]; return false if any resolver lacks that cached property. Presence, not truthiness, determines readiness: an empty cached pattern list is complete. Never access uncached url_patterns or urlconf_module properties in this mode. Django URLResolver.url_patterns is a cached_property whose cache is written only after successful evaluation; inspect the installed supported source and test this dependency in the existing supported matrix. The navbar mixin locally imports the helper and calls only load=False during registry validation, so even a failed preflight cannot retry imports and mutate an active iterator. Keep all navbar-specific validation in navbar.py and preserve ViewSet iterators, base.py, ancestor policy, helper default behavior and request paths. Do not cache a completion flag, add context-local/global pass state, register another collector, or introduce a registry work queue. If readiness is false, defer owner/child/key/ancestry-dependent diagnostics only; preserve local declaration/attachment checks, then re-evaluate on a later completed check. Add a genuinely cold temporary ROOT_URLCONF/import fixture: pre-register one participating view on an existing ViewSet, then let URLconf import register multiple invalid configured views on that same ViewSet and another invalid configured view on a new ViewSet, with distinguishable attachment/item diagnostics. Call check_viewsets directly before any other registered check can warm the resolver and assert every late diagnostic in that first completed result; repeat through Django run_checks. A no-exception-only assertion is insufficient. Test a failed/in-progress preflight with an import-attempt counter proving no retry during iteration, preserved local errors, and successful later completion reporting all late registrations; also test an unloaded included URLconf, cached empty urlpatterns, early direct mixin checks, forward declarations, and a truly missing completed name. Restore the temporary modules, resolver caches and registry state in finally using Task01's isolation ordering. Addresses review concerns R10/R11/R14: validate nonempty configured NavBar.template using Django get_template and catch only TemplateDoesNotExist for a named startup diagnostic, following CheckTemplate semantics; None uses the default. Include valid custom template and missing-template cases. Pin NavItem() and empty supplied name/key as startup errors, empty items as a valid no-output bar, and card/custom owner no-object attachment failures. Wrong field types fail Pydantic construction; malformed cv_navbar attachment values fail safely at checks. No check performs database/access/state work.</action>

-s — UNCHECKABLE; ActionView — UNCHECKABLE; Check — UNCHECKABLE; CheckTemplate — UNCHECKABLE; Item — UNCHECKABLE; NavBar — SKIPPED; NavBar.template — SKIPPED; NavItem — SKIPPED; NavItem() — UNCHECKABLE; Never — UNCHECKABLE; Task — UNCHECKABLE; TemplateDoesNotExist — UNCHECKABLE; URLResolver.url_patterns — UNCHECKABLE; ViewSet — UNCHECKABLE; ViewSet.checks_all — UNCHECKABLE; ViewSets — UNCHECKABLE; __dict__ — UNCHECKABLE; _url_configuration_loaded — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; ancestry — UNCHECKABLE; base — UNCHECKABLE; base.py — UNCHECKABLE; before — UNCHECKABLE; bound — UNCHECKABLE; bounded — UNCHECKABLE; calls — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; child — UNCHECKABLE; collector — UNCHECKABLE; complete — UNCHECKABLE; configure — UNCHECKABLE; context — UNCHECKABLE; count — UNCHECKABLE; create — UNCHECKABLE; custom — UNCHECKABLE; cv_navbar — SKIPPED; cv_object — UNCHECKABLE; data — UNCHECKABLE; declaration — UNCHECKABLE; default — UNCHECKABLE; error — UNCHECKABLE; errors — UNCHECKABLE; exclude — UNCHECKABLE; exists — UNCHECKABLE; fail — UNCHECKABLE; failed — UNCHECKABLE; failure — UNCHECKABLE; get — UNCHECKABLE; get_template — UNCHECKABLE; help — UNCHECKABLE; helper — UNCHECKABLE; http_method_names — UNCHECKABLE; inspect — UNCHECKABLE; install — UNCHECKABLE; invalid — UNCHECKABLE; invoke — UNCHECKABLE; item — UNCHECKABLE; items — UNCHECKABLE; key — UNCHECKABLE; keys — UNCHECKABLE; level — UNCHECKABLE; load — UNCHECKABLE; malformed — UNCHECKABLE; matrix — UNCHECKABLE; missing — UNCHECKABLE; mode — UNCHECKABLE; mutate — UNCHECKABLE; name — UNCHECKABLE; navbar.py — UNCHECKABLE; now — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; pages — UNCHECKABLE; register — UNCHECKABLE; registry — UNCHECKABLE; render — UNCHECKABLE; repeated — UNCHECKABLE; resolve — UNCHECKABLE; run — UNCHECKABLE; semantic — UNCHECKABLE; set — UNCHECKABLE; snapshot — UNCHECKABLE; source — UNCHECKABLE; state — UNCHECKABLE; success — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE; text — UNCHECKABLE; unknown — UNCHECKABLE; unrelated — UNCHECKABLE; up — UNCHECKABLE; url — UNCHECKABLE; urlpatterns — UNCHECKABLE; use — UNCHECKABLE; validate — UNCHECKABLE; value — UNCHECKABLE; values — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:115
>   <acceptance_criteria>Every A-04 error produces actionable startup messages; valid owner/deep-descendant declarations pass. Cold completion reports every late configured view on existing and new ViewSets in the first completed pass without mutation errors. Failed/in-progress imports are not retried inside iteration and later completion supplies deferred diagnostics. Configuration errors do not crash attribute access, and None/forgotten-mixin controls add no navbar checks.</acceptance_criteria>

ViewSet — UNCHECKABLE; ViewSets — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; complete — UNCHECKABLE; configure — UNCHECKABLE; control — UNCHECKABLE; declaration — UNCHECKABLE; error — UNCHECKABLE; errors — UNCHECKABLE; messages — UNCHECKABLE; owner — UNCHECKABLE; up — UNCHECKABLE; view — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:116
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_checks.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_checks.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:117
>   <fails_when>Any listed invalid configuration passes, diagnostics omit attachment/bar/item identity or a late registered view, URLconf loading occurs during live view iteration, a cold completed pass crashes or needs a second pass for late diagnostics, POST-only target is accepted, valid descendants fail, or checks query/authorize.</fails_when>

check — UNCHECKABLE; checks — UNCHECKABLE; complete — UNCHECKABLE; fail — UNCHECKABLE; fails_when — UNCHECKABLE; get — UNCHECKABLE; identity — UNCHECKABLE; invalid — UNCHECKABLE; item — UNCHECKABLE; load — UNCHECKABLE; register — UNCHECKABLE; view — UNCHECKABLE; when — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:118
>   <done>Every A-04 error produces actionable startup messages; valid owner/deep-descendant declarations pass. The first completed check_viewsets pass reports all late configured views without registry mutation errors; failed/in-progress readiness defers only registry-dependent errors and later completion reports them. None/forgotten-mixin controls add no navbar checks, and existing ancestor readiness defaults and request behavior remain unchanged.</done>

action — UNCHECKABLE; add — UNCHECKABLE; all — UNCHECKABLE; change — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; complete — UNCHECKABLE; configure — UNCHECKABLE; control — UNCHECKABLE; declaration — UNCHECKABLE; default — UNCHECKABLE; error — UNCHECKABLE; errors — UNCHECKABLE; fail — UNCHECKABLE; failed — UNCHECKABLE; main — UNCHECKABLE; messages — UNCHECKABLE; owner — UNCHECKABLE; registry — UNCHECKABLE; set — UNCHECKABLE; unchanged — UNCHECKABLE; up — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:122
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:127
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:128
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:134
> | T-06.40-01 | Tampering | navbar route kwargs | high | mitigate | Task 02 tests unequal PKs and authoritative structural kwargs; uses registered reverse. |

Task — UNCHECKABLE; kwargs — UNCHECKABLE; route — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:135
> | T-06.40-02 | Tampering | caption/label HTML | high | mitigate | Task 01 normalizes rendered defaults once, removes SafeData from raw text and escapes once at the template boundary; tests parsed text and markup. |

SafeData — UNCHECKABLE; Task — UNCHECKABLE; boundary — UNCHECKABLE; caption — UNCHECKABLE; label — UNCHECKABLE; rendered — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:136
> | T-06.40-03 | Denial of service | startup/ancestry resolution | medium | mitigate | Task 03 completes URLconf before registry iteration, probes readiness without imports during iteration, checks every late registration, and preserves bounded ancestry traversal and zero database work. |

Task — UNCHECKABLE; ancestry — UNCHECKABLE; base — UNCHECKABLE; before — UNCHECKABLE; bound — UNCHECKABLE; bounded — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; complete — UNCHECKABLE; data — UNCHECKABLE; gate — UNCHECKABLE; probe — UNCHECKABLE; registry — UNCHECKABLE; up — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:137
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:138
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:141
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:144
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:145
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:146
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:149
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:153
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:156
> | R1 — plain-text normalization | HIGH | Task01: decode rendered default entities once; raw values remain literal; strip SafeData then autoescape; parsed-text and injection cases. |

SafeData — UNCHECKABLE; default — UNCHECKABLE; rendered — UNCHECKABLE; text — UNCHECKABLE; values — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:157
> | R7 — real-request placement harness | MEDIUM | Task01: owned locmem/cv_extends_template tag-free and tag-present bases; shared fixture untouched. |

cv_extends_template — UNCHECKABLE; harness — UNCHECKABLE; tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:158
> | R8 — completed-registry diagnostics | MEDIUM | Task03: reuse URLconf readiness barrier; early/failed/completed cases; no global cache/collector. |

collector — UNCHECKABLE; failed — UNCHECKABLE; registry — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:159
> | R9 — fixture/cache isolation | MEDIUM | Task01: preimport project URLs and restore registry/vocabulary/ViewSet/URL/ContentType state. |

ContentType — UNCHECKABLE; ViewSet — UNCHECKABLE; project — UNCHECKABLE; registry — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:160
> | R10 — missing custom wrapper | MEDIUM | Task03: named TemplateDoesNotExist startup diagnostic and valid/None controls. |

TemplateDoesNotExist — UNCHECKABLE; custom — UNCHECKABLE; missing — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:161
> | R11 — declaration validation boundary | MEDIUM | Tasks01/03: Pydantic types at construction; missing/empty target selections at startup; empty bar valid. |

boundary — UNCHECKABLE; declaration — UNCHECKABLE; missing — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:162
> | R13 — late-bound string references | MEDIUM | Task01: explicit string types and declaration-before-registration regression. |

before — UNCHECKABLE; bound — UNCHECKABLE; declaration — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:163
> | R14 — all no-object owner attachments | LOW | Task03: cv_object=False capability check includes card and custom collections. |

all — UNCHECKABLE; check — UNCHECKABLE; custom — UNCHECKABLE; cv_object — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:165
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:168
> | A-01 is locked | Rejected classification: A-01 remains a proposal; Task01 adopts its late-bound strings under D-03/D-13 with explicit rationale. |

bound — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:169
> | Shorter URL names / merging URL tasks | Rejected preference: structural owner kwargs and current bounded request slices preserve D-05/D-06; no demonstrated defect. |

bounded — UNCHECKABLE; kwargs — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:173
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:176
> | R17 — owner-bound short-label context | MEDIUM | Tasks01/02: bind ViewContext.object to the resolved navbar owner; test object-dependent short labels on real owner, child and grandchild requests with distinct captions. |

ViewContext — UNCHECKABLE; ViewContext.object — UNCHECKABLE; bound — UNCHECKABLE; child — UNCHECKABLE; context — UNCHECKABLE; label — UNCHECKABLE; labels — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:177
> | R18 — owner route PK metadata | LOW | Task02: owner_viewset.pk_name supplies the route argument name; owner.pk supplies the model instance value. |

PK — UNCHECKABLE; model — UNCHECKABLE; name — UNCHECKABLE; owner — UNCHECKABLE; owner.pk — UNCHECKABLE; owner_viewset — UNCHECKABLE; owner_viewset.pk_name — UNCHECKABLE; pk_name — UNCHECKABLE; route — UNCHECKABLE; value — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:179
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:182
> | None | All current findings assigned to this plan are addressed; prior round dispositions remain unchanged. |

unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:186
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:189
> | R20 — URLconf completion mutates a live view registry (L520@e0f09daa) | MEDIUM | Task03: existing check_viewsets completes imports before checks_all snapshots; navbar checks use the existing helper's import-free load=False mode. Cold imports into existing and new ViewSets must yield all late diagnostics in the first completed pass; failed/in-progress imports cannot retry during iteration. Own checks.py explicitly; preserve shared iterator/default readiness and request behavior. |

Task — UNCHECKABLE; ViewSet — UNCHECKABLE; ViewSets — UNCHECKABLE; all — UNCHECKABLE; before — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; checks.py — UNCHECKABLE; complete — UNCHECKABLE; default — UNCHECKABLE; fail — UNCHECKABLE; failed — UNCHECKABLE; help — UNCHECKABLE; helper — UNCHECKABLE; load — UNCHECKABLE; mode — UNCHECKABLE; mutate — UNCHECKABLE; registry — UNCHECKABLE; set — UNCHECKABLE; snapshot — UNCHECKABLE; use — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; viewset — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:191
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:194
> | None | R20 is addressed with startup-only ordering and a bounded readiness probe; no locked decision changes or additional task/wave is required. |

add — UNCHECKABLE; bound — UNCHECKABLE; bounded — UNCHECKABLE; change — UNCHECKABLE; probe — UNCHECKABLE; require — UNCHECKABLE; up — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:197
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:6
> depends_on: ["06.40-01"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:7
> files_modified: ["src/crud_views/lib/navbar.py","src/crud_views/templates/crud_views/tags/navbar.html","src/crud_views/templates/crud_views/tags/navbar_identity.html","src/crud_views/templates/crud_views/tags/navbar_items.html","tests/test1/test_navbar_templates.py","src/crud_views/locale/de/LC_MESSAGES/django.po","src/crud_views/locale/de/LC_MESSAGES/django.mo"]

LC_MESSAGES — UNCHECKABLE; crud_views — UNCHECKABLE; django.mo — UNCHECKABLE; django.po — UNCHECKABLE; files_modified — UNCHECKABLE; navbar.html — UNCHECKABLE; navbar.py — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; src/crud_views/locale/de/LC_MESSAGES/django.mo — UNCHECKABLE; src/crud_views/locale/de/LC_MESSAGES/django.po — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED; tags/navbar.html — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:12
>   raw_tokens: 20000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:17
>     - "Global wrapper and leaf overrides, split placement and per-bar template selection use one shared request-local result (AC7)."

template — UNCHECKABLE; use — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:18
>     - "Omitted consumers and modal direct includes perform zero navbar work; all-hidden output is exactly empty (AC4)."

all — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:19
>     - "UI navbar empty/loading/error/populated/partial/zero-one-many states have ordinary links and no async/retry UI."

error — UNCHECKABLE; links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:20
>     - "UI identity empty/loading/error/populated states preserve plain text, optional decorative icon and no independent loader."

error — UNCHECKABLE; identity — UNCHECKABLE; independent — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:21
>     - "Labels/captions are escaped even when marked safe; current section remains a clickable anchor with an accessible name."

name — UNCHECKABLE; section — UNCHECKABLE; when — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:23
>     - path: "src/crud_views/templates/crud_views/tags/navbar_identity.html"

crud_views — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:24
>       provides: "NEW identity partial with public cv_navbar context."

context — UNCHECKABLE; cv_navbar — SKIPPED; identity — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:25
>     - path: "src/crud_views/templates/crud_views/tags/navbar_items.html"

crud_views — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:26
>       provides: "NEW items partial with independent labelled landmark."

independent — UNCHECKABLE; items — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:27
>     - path: "src/crud_views/locale/de/LC_MESSAGES/django.po"

LC_MESSAGES — UNCHECKABLE; crud_views — UNCHECKABLE; django.po — UNCHECKABLE; src/crud_views/locale/de/LC_MESSAGES/django.po — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:29
>     - path: "src/crud_views/locale/de/LC_MESSAGES/django.mo"

LC_MESSAGES — UNCHECKABLE; crud_views — UNCHECKABLE; django.mo — UNCHECKABLE; src/crud_views/locale/de/LC_MESSAGES/django.mo — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:30
>       provides: "Compiled German navigation landmark shipped with package."

package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:31
>     - path: "tests/test1/test_navbar_templates.py"

test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:32
>       provides: "NEW override/lazy/no-output/semantic/escaping tests."

semantic — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:33
>     - path: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:34
>       provides: "Refine private lazy builder and final documented data fields."

data — UNCHECKABLE; fields — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:35
>     - path: "src/crud_views/templates/crud_views/tags/navbar.html"

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:37
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:38
>     - from: "src/crud_views/templates/crud_views/tags/navbar.html"

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:39
>       to: "src/crud_views/templates/crud_views/tags/navbar_identity.html"

crud_views — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:40
>       via: "Layout B identity first."

identity — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:41
>     - from: "src/crud_views/templates/crud_views/tags/navbar.html"

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:42
>       to: "src/crud_views/templates/crud_views/tags/navbar_items.html"

crud_views — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:43
>       via: "Ordered visible items after identity."

after — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:44
>     - from: "src/crud_views/templates/crud_views/tags/navbar_items.html"

crud_views — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:45
>       to: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:46
>       via: "Shared cv_navbar.items contains admitted URLs; no template permission work."

cv_navbar — SKIPPED; cv_navbar.items — SKIPPED; items — UNCHECKABLE; permission — UNCHECKABLE; template — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:50
> Deliver the stable template override contract and lazy, accessible default layout.

default — UNCHECKABLE; layout — UNCHECKABLE; stable — UNCHECKABLE; template — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:51
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:52
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:53
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:56
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:57
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:58
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:59
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:61
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:62
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:63
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:64
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:65
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:66
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:67
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:68
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:69
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:70
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:71
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:75
> - `src/crud_views/templates/crud_views/tags/navbar_identity.html`: NEW identity partial with public cv_navbar context.

context — UNCHECKABLE; crud_views — UNCHECKABLE; cv_navbar — SKIPPED; identity — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:76
> - `src/crud_views/templates/crud_views/tags/navbar_items.html`: NEW items partial with independent labelled landmark.

crud_views — UNCHECKABLE; independent — UNCHECKABLE; items — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:77
> - `tests/test1/test_navbar_templates.py`: NEW override/lazy/no-output/semantic/escaping tests.

semantic — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:78
> - `src/crud_views/lib/navbar.py`: Refine private lazy builder and final documented data fields.

crud_views — UNCHECKABLE; data — UNCHECKABLE; fields — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:79
> - `src/crud_views/templates/crud_views/tags/navbar.html`: Compose the approved two leaves.

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; tags/navbar.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:81
> A-02 adopted with explicit wrapper identity preservation; A-05 refined to aria-current=true per approved UI-SPEC. No new class registry or global style inclusion. The public context fields above are stable at 1.0 per D-16; helpers remain internal.

context — UNCHECKABLE; fields — UNCHECKABLE; helpers — UNCHECKABLE; identity — UNCHECKABLE; preservation — UNCHECKABLE; registry — UNCHECKABLE; stable — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:85
>   <name>06.40-02-01: Expose global, split and per-bar rendering with one lazy result</name>

name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:86
>   <files>src/crud_views/lib/navbar.py, src/crud_views/templates/crud_views/tags/navbar.html, src/crud_views/templates/crud_views/tags/navbar_identity.html, src/crud_views/templates/crud_views/tags/navbar_items.html, tests/test1/test_navbar_templates.py</files>

crud_views — UNCHECKABLE; navbar.html — UNCHECKABLE; navbar.py — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; src/crud_views/templates/crud_views/tags/navbar.html — SKIPPED; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED; tags/navbar.html — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:87
>   <read_first>src/crud_views/lib/views/manage.py; src/crud_views/lib/breadcrumb.py; src/crud_views/templatetags/crud_views.py; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; breadcrumb.py — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; manage — UNCHECKABLE; manage.py — UNCHECKABLE; read_first — UNCHECKABLE; section — UNCHECKABLE; src/crud_views/lib/breadcrumb.py — UNCHECKABLE; src/crud_views/lib/views/manage.py — UNCHECKABLE; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:88
>   <behavior>Parameterize all three leaves and override modes; assert same lazy identity, build count, exact empty output and per-request isolation.</behavior>

all — UNCHECKABLE; build — UNCHECKABLE; count — UNCHECKABLE; identity — UNCHECKABLE; modes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:89
>   <action>Per D-08/D-10/D-11/D-16 extract identity and items leaves from the working wrapper. Settle the stable template context exactly as UI-SPEC: cv_navbar.object, label, icon, items; item.label, icon, url, active. Use private data carriers, not additional public resolver classes. Each of the three templates independently guards the same named cv_navbar value before any HTML/spacing. The mixin stores one lazy wrapper using an existence sentinel, exposes that same wrapper on repeated get_context_data calls, and builds no owner/access/state/route data merely constructing context. Modal requests expose None even when a custom modal template includes leaves directly. No shared-declaration or cross-request data cache. The wrapper uses theme-selected leaves; tag per-bar template selection receives the same named context. Loader-override tests prove global wrapper, identity-only override, items-only override, per-bar custom wrapper, and split placement with default wrapper omitted. Test tag/leaf reuse across repeated contexts and copied template context paths; only add a private cached-build sentinel if a real copy path requires it. Pin zero builder, permission and state calls when templates omit all navbar consumers and on modal direct-leaf renders. Pin exact empty string from tag/all leaves when zero items visible or absent; guard template whitespace too.</action>

action — UNCHECKABLE; add — UNCHECKABLE; all — UNCHECKABLE; before — UNCHECKABLE; build — UNCHECKABLE; calls — UNCHECKABLE; context — UNCHECKABLE; custom — UNCHECKABLE; cv_navbar — SKIPPED; cv_navbar.object — SKIPPED; data — UNCHECKABLE; declaration — UNCHECKABLE; default — UNCHECKABLE; get_context_data — UNCHECKABLE; guard — UNCHECKABLE; identity — UNCHECKABLE; item — UNCHECKABLE; item.label — UNCHECKABLE; items — UNCHECKABLE; label — UNCHECKABLE; owner — UNCHECKABLE; permission — UNCHECKABLE; repeated — UNCHECKABLE; route — UNCHECKABLE; selected — UNCHECKABLE; sentinel — UNCHECKABLE; stable — UNCHECKABLE; state — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE; url — UNCHECKABLE; value — UNCHECKABLE; when — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:90
>   <acceptance_criteria>AC4/AC7: omitted consumers and modals build/check zero times; global/leaf/per-bar/split overrides work; split placement and repeated contexts build exactly once per view/request. No output or spacing survives all-hidden/absent bars. Separate requests/users cannot reuse another result.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; all — UNCHECKABLE; build — UNCHECKABLE; check — UNCHECKABLE; repeated — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:91
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_templates.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:92
>   <fails_when>Split rendering or repeated context builds more than once, context construction calls a hook, modal direct includes render output, empty leaves emit whitespace, or one request leaks data to another.</fails_when>

calls — UNCHECKABLE; context — UNCHECKABLE; data — UNCHECKABLE; emit — UNCHECKABLE; fails_when — UNCHECKABLE; hook — UNCHECKABLE; render — UNCHECKABLE; repeated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:93
>   <done>AC4/AC7: omitted consumers and modals build/check zero times; global/leaf/per-bar/split overrides work; split placement and repeated contexts build exactly once per view/request. No output or spacing survives all-hidden/absent bars. Separate requests/users cannot reuse another result.</done>

all — UNCHECKABLE; build — UNCHECKABLE; check — UNCHECKABLE; repeated — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:97
>   <name>06.40-02-02: Render accessible wrapping links and plain owner identity</name>

identity — UNCHECKABLE; links — UNCHECKABLE; name — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:98
>   <files>src/crud_views/templates/crud_views/tags/navbar_identity.html, src/crud_views/templates/crud_views/tags/navbar_items.html, tests/test1/test_navbar_templates.py, src/crud_views/locale/de/LC_MESSAGES/django.po, src/crud_views/locale/de/LC_MESSAGES/django.mo</files>

LC_MESSAGES — UNCHECKABLE; crud_views — UNCHECKABLE; django.mo — UNCHECKABLE; django.po — UNCHECKABLE; navbar_identity — UNCHECKABLE; navbar_identity.html — UNCHECKABLE; navbar_items — UNCHECKABLE; navbar_items.html — UNCHECKABLE; src/crud_views/locale/de/LC_MESSAGES/django.mo — UNCHECKABLE; src/crud_views/locale/de/LC_MESSAGES/django.po — UNCHECKABLE; src/crud_views/templates/crud_views/tags/navbar_identity.html — SKIPPED; src/crud_views/templates/crud_views/tags/navbar_items.html — SKIPPED; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:99
>   <read_first>src/crud_views/lib/icons.py; src/crud_views/templates/crud_views/tags/button/action.html; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-PROBE.json</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-PROBE.json — UNCHECKABLE; PROBE.json — UNCHECKABLE; action — UNCHECKABLE; action.html — UNCHECKABLE; button — UNCHECKABLE; crud_views — UNCHECKABLE; icons.py — UNCHECKABLE; read_first — UNCHECKABLE; section — UNCHECKABLE; src/crud_views/lib/icons.py — UNCHECKABLE; src/crud_views/templates/crud_views/tags/button/action.html — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:100
>   <behavior>Render normal/zero/one/many/partial/iconless cases; parse landmark, anchor order/current marker, full labels, escaped caption/attributes and zero output.</behavior>

caption — UNCHECKABLE; labels — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:101
>   <action>Implement D-07/D-10/D-11/D-12 and all template-level UI criteria. Identity remains ordinary escaped text, never a second heading or inferred anchor; owner icon is decorative via existing renderer, including supported host/element icon placement and empty-string suppression. Items partial owns a translated navigation landmark Sections for %(object)s using the plain owner caption; it works independently of the identity leaf. Use a list of anchors in declaration order, Bootstrap nav/nav-pills/flex-wrap, naturally sized links, mw-100 and text-break utilities on caption/list items/labels as needed. Retain full labels at small widths and scope every added class to navbar output. Adopt UI-SPEC's aria-current="true" for the active section (refines A-05's page marker because Item pages still activate Orders). Active anchors remain focusable/clickable; other items have no current marker. Do not introduce dynamic-tab semantics, write actions or a navigation script. Existing Bootstrap text-break wrapping is the bounded initial CSS choice: it avoids a new global stylesheet/link changing nonparticipant HTML; live reflow in plan 08 must prove unbroken text wraps. If existing utilities cannot satisfy that evidence, use a navbar-scoped asset loaded only by opted-in rendering and extend split/no-output parity tests before acceptance. Test zero/one/many, hidden first/middle/matching items, missing icons, SafeString/ordinary markup-bearing captions and labels including accessible-name attribute escaping, configured label/icon overrides and unchanged header placement. Addresses review concerns R1/R15: consume the exact built-in-str data normalized by plan01; templates autoescape once and never apply force_escape to a pre-escaped short-action result. Assert parsed owner/anchor/aria-label text for ordinary ampersands/apostrophes, entity-looking raw overrides and SafeString markup, as well as absence of injected nodes. Add msgid Sections for %(object)s with German msgstr Abschnitte für %(object)s to the existing core django.po and compile the owned django.mo using the installed polib.pofile(...).save_as_mofile(...) under .nox/tests-3-12-django-5-2/bin/python, as existing locale plans do (msgfmt is absent). Preserve the interpolation key and existing entries; do not sweep unrelated catalogs. Under translation.override('de'), render the real items partial and assert its accessible name equals Abschnitte für plus the plain owner caption, including punctuation/markup-bearing captions; English remains correct. Compare against the literal German text so a missing catalog cannot pass via an English fallback.</action>

.nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; Identity — UNCHECKABLE; Item — UNCHECKABLE; SafeString — UNCHECKABLE; action — UNCHECKABLE; actions — UNCHECKABLE; activate — UNCHECKABLE; all — UNCHECKABLE; before — UNCHECKABLE; bounded — UNCHECKABLE; caption — UNCHECKABLE; data — UNCHECKABLE; declaration — UNCHECKABLE; django.mo — UNCHECKABLE; django.po — UNCHECKABLE; entries — UNCHECKABLE; fallback — UNCHECKABLE; force_escape — UNCHECKABLE; heading — UNCHECKABLE; host — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; key — UNCHECKABLE; label — UNCHECKABLE; labels — UNCHECKABLE; level — UNCHECKABLE; link — UNCHECKABLE; links — UNCHECKABLE; missing — UNCHECKABLE; name — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; pages — UNCHECKABLE; polib.pofile — UNCHECKABLE; polib.pofile(...) — UNCHECKABLE; render — UNCHECKABLE; save_as_mofile — UNCHECKABLE; save_as_mofile(...) — UNCHECKABLE; scoped — UNCHECKABLE; section — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE; text — UNCHECKABLE; translated — UNCHECKABLE; translation.override — UNCHECKABLE; translation.override('de') — UNCHECKABLE; unchanged — UNCHECKABLE; unrelated — UNCHECKABLE; use — UNCHECKABLE; wrap — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:102
>   <acceptance_criteria>UI navbar empty/loading/error/populated/partial/zero-one-many and identity empty/loading/error/populated have rendered assertions: no asynchronous loaders or retry UI; denied items disappear; surviving text/links remain ordered; zero items emit nothing; one has identity and one natural link. Full normal labels remain visible, there is at most one current anchor, caption/icons add no Tab stops, and raw safe markup never executes.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; add — UNCHECKABLE; caption — UNCHECKABLE; emit — UNCHECKABLE; error — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; labels — UNCHECKABLE; link — UNCHECKABLE; links — UNCHECKABLE; rendered — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:103
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_templates.py tests/test1/test_i18n.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_i18n — UNCHECKABLE; test_i18n.py — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_i18n.py — UNCHECKABLE; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:104
>   <fails_when>Markup-bearing values create elements/attributes, hidden items leave gaps/wrappers, empty icon removes text, active anchor loses href, current marker count exceeds one, or dynamic tabs/loading/retry UI appears.</fails_when>

count — UNCHECKABLE; create — UNCHECKABLE; fails_when — UNCHECKABLE; href — UNCHECKABLE; items — UNCHECKABLE; text — UNCHECKABLE; values — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:105
>   <done>UI navbar empty/loading/error/populated/partial/zero-one-many and identity empty/loading/error/populated have rendered assertions: no asynchronous loaders or retry UI; denied items disappear; surviving text/links remain ordered; zero items emit nothing; one has identity and one natural link. Full normal labels remain visible, there is at most one current anchor, caption/icons add no Tab stops, and raw safe markup never executes.</done>

add — UNCHECKABLE; caption — UNCHECKABLE; emit — UNCHECKABLE; error — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; labels — UNCHECKABLE; link — UNCHECKABLE; links — UNCHECKABLE; rendered — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:109
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:114
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:115
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:121
> | T-06.40-04 | Information disclosure | lazy result lifetime | high | mitigate | Task 01 proves one request-local result and cross-user isolation; no shared declaration cache. |

Task — UNCHECKABLE; declaration — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:122
> | T-06.40-05 | Tampering | template labels and accessible name | high | mitigate | Task 02 tests single-pass escaped normalized caption/labels and German accessible-name attribute boundaries. |

Task — UNCHECKABLE; caption — UNCHECKABLE; labels — UNCHECKABLE; name — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:123
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:124
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:127
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:130
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:131
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:132
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:135
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:139
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:142
> | R1 — escaping consumers | HIGH | Task02 consumes plan01's plain data and tests serialized/parsed text without double escaping. |

data — UNCHECKABLE; tests — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:143
> | R15 — German landmark | MEDIUM | Task02 owns .po/.mo, exact German translation and real rendered aria-label assertion. |

label — UNCHECKABLE; rendered — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:145
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:148
> | Percent-bearing caption interpolation | Rejected: one named interpolation does not interpolate caption contents recursively. |

caption — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:149
> | Extra lazy caches / all-hidden/icon/wrapping claims | No new mechanism: Tasks01/02 already test copied contexts, empty output, host icons and flex wrapping; add a sentinel only on reproduced need. |

add — UNCHECKABLE; all — UNCHECKABLE; host — UNCHECKABLE; sentinel — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:152
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:6
> depends_on: ["06.40-02"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:7
> files_modified: ["src/crud_views/lib/navbar.py","tests/test1/test_navbar_permissions.py","tests/test1/test_navbar_costs.py",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md"]

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; COST.md — UNCHECKABLE; crud_views — UNCHECKABLE; files_modified — UNCHECKABLE; navbar.py — UNCHECKABLE; section — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_costs.py — SKIPPED; tests/test1/test_navbar_permissions.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:12
>   raw_tokens: 20000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:17
>     - "Denied destinations are hidden before state; child helper runs once with the navbar owner, and real endpoint authorization remains authoritative (AC3)."

before — UNCHECKABLE; child — UNCHECKABLE; helper — UNCHECKABLE; owner — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:18
>     - "Empty accessible core and Guardian collections remain visible and return 200."

main — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:19
>     - "Reached configuration failures propagate, and nested destination ancestor denial can still return 403."

fail — UNCHECKABLE; failure — UNCHECKABLE; gate — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:20
>     - "Nonparticipants keep exact HTML/query behavior and existing context buttons coexist unchanged (AC5)."

buttons — UNCHECKABLE; context — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:21
>     - "Measured navbar costs distinguish hook counts, permission SQL and owner/collection reads."

counts — UNCHECKABLE; hook — UNCHECKABLE; owner — UNCHECKABLE; permission — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:23
>     - path: "tests/test1/test_navbar_permissions.py"

test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_permissions.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:24
>       provides: "NEW real-endpoint permission/state/provider/error regressions."

error — UNCHECKABLE; permission — UNCHECKABLE; provider — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:25
>     - path: "tests/test1/test_navbar_costs.py"

test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_costs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:26
>       provides: "NEW query accounting, laziness and byte-preservation tests."

preservation — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:27
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; COST.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:28
>       provides: "NEW measured cost receipt, not a promised fixed budget."

receipt — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:29
>     - path: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:31
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:32
>     - from: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:33
>       to: "src/crud_views/lib/view/base.py"

base — UNCHECKABLE; base.py — UNCHECKABLE; crud_views — UNCHECKABLE; src/crud_views/lib/view/base.py — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:34
>       via: "Existing child-link and rendering-state helpers called in that order."

child — UNCHECKABLE; helpers — UNCHECKABLE; link — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:35
>     - from: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:36
>       to: "src/crud_views_guardian/lib/views.py"

crud_views_guardian — UNCHECKABLE; src/crud_views_guardian/lib/views.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:37
>       via: "Guardian collection/create admission consumed once."

create — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:41
> Close access/state integration and cost-preservation obligations.

preservation — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:42
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:43
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:44
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:47
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:48
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:49
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:50
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:52
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:53
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:54
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:55
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:56
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:57
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:58
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:59
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:60
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:61
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:62
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:66
> - `tests/test1/test_navbar_permissions.py`: NEW real-endpoint permission/state/provider/error regressions.

error — UNCHECKABLE; permission — UNCHECKABLE; provider — UNCHECKABLE; state — UNCHECKABLE; test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_permissions.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:67
> - `tests/test1/test_navbar_costs.py`: NEW query accounting, laziness and byte-preservation tests.

preservation — UNCHECKABLE; test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_costs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:68
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md`: NEW measured cost receipt, not a promised fixed budget.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; COST.md — UNCHECKABLE; receipt — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:69
> - `src/crud_views/lib/navbar.py`: Bounded admission refinements only.

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:71
> Needs the stable rendering seam from plan 02. Produces endpoint and measured-cost evidence consumed by documentation. Only navbar.py overlaps prior core plans, so it follows them; it can run beside independent example plan 04.

independent — UNCHECKABLE; navbar.py — UNCHECKABLE; run — UNCHECKABLE; stable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:75
>   <name>06.40-03-01: Prove admission order against real core and Guardian endpoints</name>

name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:76
>   <files>src/crud_views/lib/navbar.py, tests/test1/test_navbar_permissions.py</files>

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_permissions.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:77
>   <read_first>src/crud_views/lib/view/base.py; src/crud_views_guardian/lib/mixins.py; src/crud_views_guardian/lib/views.py; tests/test1/test_guardian_child_link_visibility.py; tests/test1/test_action_enabled.py; tests/test1/test_navbar.py</read_first>

base — UNCHECKABLE; base.py — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views_guardian — UNCHECKABLE; mixins.py — UNCHECKABLE; read_first — UNCHECKABLE; src/crud_views/lib/view/base.py — UNCHECKABLE; src/crud_views_guardian/lib/mixins.py — UNCHECKABLE; src/crud_views_guardian/lib/views.py — UNCHECKABLE; test_action_enabled — UNCHECKABLE; test_action_enabled.py — UNCHECKABLE; test_guardian_child_link_visibility — UNCHECKABLE; test_guardian_child_link_visibility.py — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_action_enabled.py — UNCHECKABLE; tests/test1/test_guardian_child_link_visibility.py — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:78
>   <behavior>Spies assert once(user, owner) per child admission; allowed -> one state call; denied -> zero; actual GET results distinguish visibility from authority.</behavior>

child — UNCHECKABLE; once(user, owner) — UNCHECKABLE; owner — UNCHECKABLE; state — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:79
>   <action>Per D-06/D-09/D-14, expand navbar admission and integration regressions without changing those existing helpers. Every owner item calls target.cv_has_access(user, owner); every child item calls target._cv_child_link_has_access(user, owner) exactly once. Only an allowed target calls _cv_action_enabled_for_rendering(user, owner, rendering_view), once with the identical owner; denial skips state and URL/label work. Include real plain/Guardian collection and create compositions, so Guardian's parent-aware create is never rechecked. Test allowed, denied and state-disabled targets with exact arguments, mixed visible/hidden items, owner detail state denial with actual GET 403, child state denial hidden, and allowed empty plain/Guardian collection GET 200. Assert no collection count/exists query controls admission. Cover nested-owner immediate-parent boundary with a reachable current page and visible link whose separately configured destination ancestor policy returns 403, plus project queryset restrictions; no farther ancestor gate is added to rendering. Propagate reached missing permission-key, operation-requirement and off-default authorization-routing ImproperlyConfigured failures; do not turn them into invisible items or an empty bar. Include anonymous/inactive/protected-provider controls using existing helper behavior rather than duplicating policy. Keep existing regression files and base/policy/router/button code unchanged.</action>

ImproperlyConfigured — UNCHECKABLE; _cv_action_enabled_for_rendering — UNCHECKABLE; _cv_action_enabled_for_rendering(user, owner, rendering_view) — UNCHECKABLE; _cv_child_link_has_access — UNCHECKABLE; action — UNCHECKABLE; base — UNCHECKABLE; boundary — UNCHECKABLE; button — UNCHECKABLE; calls — UNCHECKABLE; child — UNCHECKABLE; count — UNCHECKABLE; create — UNCHECKABLE; cv_has_access — UNCHECKABLE; default — UNCHECKABLE; detail — UNCHECKABLE; disabled — UNCHECKABLE; exists — UNCHECKABLE; expand — UNCHECKABLE; gate — UNCHECKABLE; helper — UNCHECKABLE; helpers — UNCHECKABLE; item — UNCHECKABLE; items — UNCHECKABLE; key — UNCHECKABLE; label — UNCHECKABLE; link — UNCHECKABLE; missing — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; parent — UNCHECKABLE; permission — UNCHECKABLE; project — UNCHECKABLE; provider — UNCHECKABLE; queryset — UNCHECKABLE; rendering_view — UNCHECKABLE; requirement — UNCHECKABLE; state — UNCHECKABLE; target._cv_child_link_has_access — UNCHECKABLE; target._cv_child_link_has_access(user, owner) — UNCHECKABLE; target.cv_has_access — UNCHECKABLE; target.cv_has_access(user, owner) — UNCHECKABLE; unchanged — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:80
>   <acceptance_criteria>AC3: exact once-only hooks and access-before-state are proven in rendered integration cases for both permission outcomes; every item uses the resolved navbar owner. Actual destination responses prove state denial, empty permitted collections, and higher-ancestor/queryset limitations independently of link visibility.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; before — UNCHECKABLE; item — UNCHECKABLE; limitations — UNCHECKABLE; link — UNCHECKABLE; owner — UNCHECKABLE; permission — UNCHECKABLE; queryset — UNCHECKABLE; rendered — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:81
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_permissions.py tests/test1/test_guardian_child_link_visibility.py tests/test1/test_action_enabled.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_action_enabled — UNCHECKABLE; test_action_enabled.py — UNCHECKABLE; test_guardian_child_link_visibility — UNCHECKABLE; test_guardian_child_link_visibility.py — UNCHECKABLE; test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_action_enabled.py — UNCHECKABLE; tests/test1/test_guardian_child_link_visibility.py — UNCHECKABLE; tests/test1/test_navbar_permissions.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:82
>   <fails_when>Denied items invoke state, child hooks run twice, owner argument changes, empty permitted collection disappears, reached configuration error is swallowed, destination authorization is bypassed, or established helper regressions fail.</fails_when>

child — UNCHECKABLE; error — UNCHECKABLE; fail — UNCHECKABLE; fails_when — UNCHECKABLE; helper — UNCHECKABLE; invoke — UNCHECKABLE; items — UNCHECKABLE; owner — UNCHECKABLE; run — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:83
>   <done>AC3: exact once-only hooks and access-before-state are proven in rendered integration cases for both permission outcomes; every item uses the resolved navbar owner. Actual destination responses prove state denial, empty permitted collections, and higher-ancestor/queryset limitations independently of link visibility.</done>

before — UNCHECKABLE; item — UNCHECKABLE; limitations — UNCHECKABLE; link — UNCHECKABLE; owner — UNCHECKABLE; permission — UNCHECKABLE; queryset — UNCHECKABLE; rendered — UNCHECKABLE; state — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:87
>   <name>06.40-03-02: Measure cost and preserve existing page output</name>

name — UNCHECKABLE; page — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:88
>   <files>tests/test1/test_navbar_costs.py, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md</files>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; COST.md — UNCHECKABLE; section — UNCHECKABLE; test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_costs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:89
>   <read_first>tests/test1/test_guardian_child_link_visibility.py; tests/test1/test_navbar.py; tests/test1/test_navbar_templates.py; tests/test1/test_breadcrumb.py; docs/reference/context_buttons.md</read_first>

context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; test_breadcrumb — UNCHECKABLE; test_breadcrumb.py — UNCHECKABLE; test_guardian_child_link_visibility — UNCHECKABLE; test_guardian_child_link_visibility.py — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_breadcrumb.py — UNCHECKABLE; tests/test1/test_guardian_child_link_visibility.py — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:90
>   <behavior>Paired requests -> identical nonparticipant bytes/query counts; participating cache cases -> one build and one hook per item; SQL category reports identify zero owner/collection reads.</behavior>

build — UNCHECKABLE; category — UNCHECKABLE; counts — UNCHECKABLE; hook — UNCHECKABLE; item — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:91
>   <action>Per D-02/D-08/D-13/D-14 and A-07, add cost/preservation cases using isolated fixtures from plan 01 (reuse via explicit imports/pytest_plugins only where needed, without permanent registry edits). Measure builder, each admission hook, each permitted state hook, owner-row queries and total SQL separately for owner/deep-descendant, plain/Guardian/mixed bars, cold/warm vocabulary and actor permission caches, tag/split/repeated context, omitted consumers, modal and no-mixin/no-declaration controls. Compare equivalent requests and capture navbar-only work after ordinary request object loading; do not count unrelated breadcrumb work as navbar cost. No owner reload or collection probe is allowed. Record observed totals, environment and fixture composition in COST.md; do not promise all Guardian/custom checks are query-free. Assert untouched existing goldens byte-for-byte and pair equivalent nonparticipant pages before/after tag placement; preserve context buttons alone and alongside a bar, including their existing order/behavior. For shared page template placement later, use whitespace-neutral Django block delimiters so unconfigured pages remain byte-identical. Count only the navbar's isolated work, not duplicate context-button hooks on a coexistence page. Addresses review concerns R7/R9: reuse plan01's owned locmem/cv_extends_template harness for paired complete response.content comparisons with the tag-free and tag-present bases; freeze CSRF and other request-varying inputs identically or exclude them through the fixture configuration, never normalize away navbar/header output. Cover no-mixin and configured-mixin-with-None pages, not only component goldens. Preimport project URL registrations before snapshotting. A cold-vocabulary cell clears both check_module._VOCAB_CACHE and each participating ViewSet._default_permissions plus ContentType.objects.clear_cache(). Addresses review concern R19: also call guardian.shortcuts.clear_ct_cache() in the cold-vocabulary reset, matching reset_discovery in test_guardian_child_link_visibility.py; record this separate Guardian content-type cache reset explicitly in COST.md's cold/warm conditions. A cold-actor cell uses a fresh actor or removes _perm_cache/_user_perm_cache/_group_perm_cache and any exercised Guardian checker cache. Warm cells explicitly prewarm only the named caches outside measurement. Snapshot and restore pre-existing ViewSet cache values in finally and record the exact cold/warm definitions in COST.md.</action>

COST.md — UNCHECKABLE; ContentType — UNCHECKABLE; ContentType.objects.clear_cache — UNCHECKABLE; ContentType.objects.clear_cache() — UNCHECKABLE; ViewSet — UNCHECKABLE; ViewSet._default_permissions — UNCHECKABLE; _VOCAB_CACHE — UNCHECKABLE; _default_permissions — UNCHECKABLE; _group_perm_cache — UNCHECKABLE; _perm_cache — UNCHECKABLE; _user_perm_cache — UNCHECKABLE; action — UNCHECKABLE; actor — UNCHECKABLE; add — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; before — UNCHECKABLE; button — UNCHECKABLE; buttons — UNCHECKABLE; cell — UNCHECKABLE; check_module — UNCHECKABLE; check_module._VOCAB_CACHE — UNCHECKABLE; checks — UNCHECKABLE; clear_cache — UNCHECKABLE; clear_ct_cache — UNCHECKABLE; complete — UNCHECKABLE; context — UNCHECKABLE; count — UNCHECKABLE; custom — UNCHECKABLE; cv_extends_template — UNCHECKABLE; declaration — UNCHECKABLE; environment — UNCHECKABLE; exclude — UNCHECKABLE; guardian.shortcuts.clear_ct_cache — UNCHECKABLE; harness — UNCHECKABLE; hook — UNCHECKABLE; objects — UNCHECKABLE; observed — UNCHECKABLE; owner — UNCHECKABLE; page — UNCHECKABLE; pages — UNCHECKABLE; pair — UNCHECKABLE; permission — UNCHECKABLE; preservation — UNCHECKABLE; probe — UNCHECKABLE; project — UNCHECKABLE; pytest_plugins — UNCHECKABLE; record — UNCHECKABLE; registry — UNCHECKABLE; repeated — UNCHECKABLE; reset — UNCHECKABLE; reset_discovery — UNCHECKABLE; response — UNCHECKABLE; response.content — UNCHECKABLE; row — UNCHECKABLE; state — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; test_guardian_child_link_visibility — UNCHECKABLE; test_guardian_child_link_visibility.py — UNCHECKABLE; unrelated — UNCHECKABLE; use — UNCHECKABLE; values — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:92
>   <acceptance_criteria>AC4/AC5: no-mixin, None, omitted-consumer and modal cases add zero navbar queries/builds/hooks; existing golden bytes remain unchanged. Rendered bars have measured, reproducible costs and no owner/collection reload; context-button coexistence preserves original control HTML and behavior.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; add — UNCHECKABLE; button — UNCHECKABLE; context — UNCHECKABLE; control — UNCHECKABLE; owner — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:93
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_costs.py tests/test1/test_guardian_child_link_visibility.py tests/test1/test_action_enabled.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_action_enabled — UNCHECKABLE; test_action_enabled.py — UNCHECKABLE; test_guardian_child_link_visibility — UNCHECKABLE; test_guardian_child_link_visibility.py — UNCHECKABLE; test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_action_enabled.py — UNCHECKABLE; tests/test1/test_guardian_child_link_visibility.py — UNCHECKABLE; tests/test1/test_navbar_costs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:94
>   <fails_when>Nonparticipant golden bytes or SQL change, omitted/modal hooks execute, deep owner fetch appears, measurements conflate hook calls and SQL, or coexistence reorders/changes context buttons.</fails_when>

buttons — UNCHECKABLE; calls — UNCHECKABLE; change — UNCHECKABLE; context — UNCHECKABLE; execute — UNCHECKABLE; fails_when — UNCHECKABLE; hook — UNCHECKABLE; owner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:95
>   <done>AC4/AC5: no-mixin, None, omitted-consumer and modal cases add zero navbar queries/builds/hooks; existing golden bytes remain unchanged. Rendered bars have measured, reproducible costs and no owner/collection reload; context-button coexistence preserves original control HTML and behavior.</done>

add — UNCHECKABLE; button — UNCHECKABLE; context — UNCHECKABLE; control — UNCHECKABLE; owner — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:99
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:104
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:105
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:111
> | T-06.40-06 | Elevation of privilege | navbar admission versus destination | high | mitigate | Task 01 proves real denied GETs and full request gates independently of visible links. |

Task — UNCHECKABLE; links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:112
> | T-06.40-07 | Information disclosure | policy errors | high | mitigate | Task 01 propagates reached missing-key/operation/router errors. |

Task — UNCHECKABLE; errors — UNCHECKABLE; key — UNCHECKABLE; missing — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:113
> | T-06.40-08 | Denial of service | permission and ORM work | medium | mitigate | Task 02 measures cold/warm calls and SQL; no duplicate hook, owner reload or collection scan. |

Task — UNCHECKABLE; calls — UNCHECKABLE; hook — UNCHECKABLE; owner — UNCHECKABLE; permission — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:114
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:115
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:118
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:121
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:122
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:123
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:126
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:130
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:133
> | R7 — whole-page parity evidence | MEDIUM | Task02 compares full paired response bytes with the owned harness and deterministic request inputs. |

harness — UNCHECKABLE; page — UNCHECKABLE; response — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:134
> | R9 — complete cold-cache definition | MEDIUM | Task02 resets ViewSet vocabulary, check cache, ContentType and actor/provider caches; records warm/cold conditions. |

ContentType — UNCHECKABLE; ViewSet — UNCHECKABLE; actor — UNCHECKABLE; check — UNCHECKABLE; complete — UNCHECKABLE; provider — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:136
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:139
> | Relax byte parity | Rejected: AC5 explicitly requires byte-for-byte preservation; R7 now supplies concrete whole-page evidence. |

now — UNCHECKABLE; page — UNCHECKABLE; preservation — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:143
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:146
> | R19 — cold Guardian content-type discovery | LOW | Task02: reset guardian.shortcuts.clear_ct_cache() alongside Django ContentType and ViewSet vocabulary caches; record the separate reset in COST.md's measurement conditions. |

COST.md — UNCHECKABLE; ContentType — UNCHECKABLE; ViewSet — UNCHECKABLE; clear_ct_cache — UNCHECKABLE; guardian.shortcuts.clear_ct_cache — UNCHECKABLE; record — UNCHECKABLE; reset — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:148
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:151
> | None | All current findings assigned to this plan are addressed; prior round dispositions remain unchanged. |

unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:154
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:6
> depends_on: ["06.40-02"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:7
> files_modified: ["examples/bootstrap5/navbar_demo/__init__.py","examples/bootstrap5/navbar_demo/models.py","examples/bootstrap5/navbar_demo/views.py","examples/bootstrap5/navbar_demo/urls.py","examples/bootstrap5/navbar_demo/tests.py","examples/bootstrap5/navbar_demo/migrations/__init__.py","examples/bootstrap5/navbar_demo/migrations/0001_initial.py","examples/bootstrap5/project/settings.py","examples/bootstrap5/project/urls.py"]

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/__init__.py — SKIPPED; examples/bootstrap5/navbar_demo/migrations/0001_initial.py — SKIPPED; examples/bootstrap5/navbar_demo/migrations/__init__.py — SKIPPED; examples/bootstrap5/navbar_demo/models.py — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; examples/bootstrap5/project/settings.py — UNCHECKABLE; examples/bootstrap5/project/urls.py — UNCHECKABLE; files_modified — UNCHECKABLE; migrations/__init__.py — UNCHECKABLE; models.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; settings.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:12
>   raw_tokens: 20000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:17
>     - "The navbar example owns Tenant and Customer models and routes; it does not import another scenario's business data."

Customer — UNCHECKABLE; business — UNCHECKABLE; data — UNCHECKABLE; routes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:18
>     - "Tenant Guardian object grants and core Customer permissions govern actual requests with cascading enabled."

Customer — UNCHECKABLE; enabled — UNCHECKABLE; permissions — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:19
>     - "Details and Notes are two GET views of one Customer, with stable identity and distinct active sections."

Customer — UNCHECKABLE; identity — UNCHECKABLE; stable — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:21
>     - path: "examples/bootstrap5/navbar_demo/__init__.py"

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/__init__.py — SKIPPED; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:22
>       provides: "NEW app package."

package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:23
>     - path: "examples/bootstrap5/navbar_demo/models.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/models.py — SKIPPED; models.py — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:24
>       provides: "NEW Tenant and Customer with notes; plan 05 expands approved hierarchy."

Customer — UNCHECKABLE; hierarchy — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:25
>     - path: "examples/bootstrap5/navbar_demo/views.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; navbar_demo — SKIPPED; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:26
>       provides: "NEW app-local forms/tables, protected ViewSets, Notes view, NavbarMixin and landing entry view."

NavbarMixin — SKIPPED; ViewSets — UNCHECKABLE; tables — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:27
>     - path: "examples/bootstrap5/navbar_demo/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:28
>       provides: "NEW navbar-demo-home plus unique navbar_* routes under object-navbar/."

navbar_ — UNCHECKABLE; routes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:29
>     - path: "examples/bootstrap5/navbar_demo/tests.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:30
>       provides: "NEW endpoint/identity/tenant-boundary tests."

boundary — UNCHECKABLE; identity — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:31
>     - path: "examples/bootstrap5/navbar_demo/migrations/__init__.py"

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/__init__.py — SKIPPED; migrations/__init__.py — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:32
>       provides: "NEW migration package."

package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:33
>     - path: "examples/bootstrap5/navbar_demo/migrations/0001_initial.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0001_initial.py — SKIPPED; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:34
>       provides: "NEW Tenant/Customer migration."

Customer — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:35
>     - path: "examples/bootstrap5/project/settings.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/settings.py — UNCHECKABLE; project — UNCHECKABLE; settings.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:36
>       provides: "Register independent navbar_demo app."

independent — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:37
>     - path: "examples/bootstrap5/project/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/urls.py — UNCHECKABLE; project — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:38
>       provides: "Include object-navbar routes."

routes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:39
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:40
>     - from: "examples/bootstrap5/project/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/urls.py — UNCHECKABLE; project — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:41
>       to: "examples/bootstrap5/navbar_demo/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:42
>       via: "Public object-navbar/ route."

route — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:43
>     - from: "examples/bootstrap5/navbar_demo/views.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; navbar_demo — SKIPPED; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:44
>       to: "src/crud_views_guardian/lib/viewset.py"

crud_views_guardian — UNCHECKABLE; src/crud_views_guardian/lib/viewset.py — UNCHECKABLE; viewset — UNCHECKABLE; viewset.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:45
>       via: "Tenant GuardianViewSet and strict object-grant ancestor policy."

GuardianViewSet — UNCHECKABLE; grant — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:46
>     - from: "examples/bootstrap5/navbar_demo/views.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; navbar_demo — SKIPPED; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:47
>       to: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:48
>       via: "One project mixin carries the configured Customer bar."

Customer — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:52
> Add the independent example's protected Tenant and Customer navigation path.

Customer — UNCHECKABLE; independent — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:53
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:54
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:55
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:58
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:59
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:60
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:61
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:63
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:64
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:65
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:66
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:67
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:68
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:69
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:70
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:71
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:72
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:73
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:77
> - `examples/bootstrap5/navbar_demo/__init__.py`: NEW app package.

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/__init__.py — SKIPPED; navbar_demo — SKIPPED; package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:78
> - `examples/bootstrap5/navbar_demo/models.py`: NEW Tenant and Customer with notes; plan 05 expands approved hierarchy.

Customer — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/models.py — SKIPPED; hierarchy — UNCHECKABLE; models.py — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:79
> - `examples/bootstrap5/navbar_demo/views.py`: NEW app-local forms/tables, protected ViewSets, Notes view, NavbarMixin and landing entry view.

NavbarMixin — SKIPPED; ViewSets — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; navbar_demo — SKIPPED; tables — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:80
> - `examples/bootstrap5/navbar_demo/urls.py`: NEW navbar-demo-home plus unique navbar_* routes under object-navbar/.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_ — UNCHECKABLE; navbar_demo — SKIPPED; routes — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:81
> - `examples/bootstrap5/navbar_demo/tests.py`: NEW endpoint/identity/tenant-boundary tests.

boundary — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; identity — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:82
> - `examples/bootstrap5/navbar_demo/migrations/__init__.py`: NEW migration package.

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/__init__.py — SKIPPED; migrations/__init__.py — UNCHECKABLE; navbar_demo — SKIPPED; package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:83
> - `examples/bootstrap5/navbar_demo/migrations/0001_initial.py`: NEW Tenant/Customer migration.

Customer — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0001_initial.py — SKIPPED; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:84
> - `examples/bootstrap5/project/settings.py`: Register independent navbar_demo app.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/settings.py — UNCHECKABLE; independent — UNCHECKABLE; navbar_demo — SKIPPED; project — UNCHECKABLE; settings.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:85
> - `examples/bootstrap5/project/urls.py`: Include object-navbar routes.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/urls.py — UNCHECKABLE; project — UNCHECKABLE; routes — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:87
> Independent of core permission-test edits in plan 03; no shared files in wave 3. The example is developed through working request slices, with normal migrations per slice. New package installs are not introduced; the existing example Nox dependency set is reused. Migration rating: reversible, isolated example tables only.

Migration — UNCHECKABLE; package — UNCHECKABLE; permission — UNCHECKABLE; set — UNCHECKABLE; tables — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:91
>   <name>06.40-04-01: Open a protected Tenant-to-Customer example path</name>

Customer — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:92
>   <files>examples/bootstrap5/navbar_demo/__init__.py, examples/bootstrap5/navbar_demo/models.py, examples/bootstrap5/navbar_demo/views.py, examples/bootstrap5/project/settings.py, examples/bootstrap5/navbar_demo/tests.py</files>

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/__init__.py — SKIPPED; examples/bootstrap5/navbar_demo/models.py — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; examples/bootstrap5/project/settings.py — UNCHECKABLE; models.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; settings.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:93
>   <read_first>examples/bootstrap5/nested/models.py; examples/bootstrap5/nested/views.py; examples/bootstrap5/guardian_demo/views.py; examples/bootstrap5/project/settings.py; examples/bootstrap5/nested/tests.py</read_first>

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/guardian_demo/views.py — UNCHECKABLE; examples/bootstrap5/nested/models.py — UNCHECKABLE; examples/bootstrap5/nested/tests.py — UNCHECKABLE; examples/bootstrap5/nested/views.py — UNCHECKABLE; examples/bootstrap5/project/settings.py — UNCHECKABLE; guardian_demo — UNCHECKABLE; models.py — UNCHECKABLE; project — UNCHECKABLE; read_first — UNCHECKABLE; settings.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:94
>   <behavior>Owned Customer/Notes GET -> 200; valid other-Tenant URL -> 403; Notes shows text; navbar identity stable; no per-Customer object grants.</behavior>

Customer — UNCHECKABLE; Owned — UNCHECKABLE; identity — UNCHECKABLE; stable — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:95
>   <action>Per D-15 create an independent navbar_demo app and add it to INSTALLED_APPS. Own Tenant and Customer models (Customer has name, notes and Tenant FK) with explicit ordering/verbose names; imports never reach another example's business model. Keep app-local form/table classes in views.py following nested conventions, avoiding a needless module hierarchy. Register uniquely prefixed ViewSets navbar_tenant and navbar_customer to prevent global registry collisions. Tenant is GuardianViewSet with AncestorPolicy(provider="guardian", accept_global_perms=False); protected Tenant list/detail views filter to object grants. Customer uses core ViewSet with ParentViewSet(name="navbar_tenant", attribute="tenant"), normal protected CRUD compositions and CreateViewParentMixin. Retain ancestor cascading. Add Customer detail and Notes detail with separate literal key/path, Notes displaying the Customer notes field, plus a project NavbarMixin pairing declaration and mixin on object views only. At this slice the declaration contains the existing Details/Notes destinations; plan 05 extends the same declaration with Orders/Addresses once their routes exist. Navbar attachment is never added to Customer list/create. Add tests with ordinary users and actual requests through a test-local URLconf built from these ViewSets, prove owned Tenant/Customer reads and cross-Tenant denial, and evaluate the view's navbar context using the existing tag harness. Initial unmigrated app can be synchronized by Django's test runner until Task 02 adds the normal migration. Do not add a new dependency or auth mechanism. Addresses review concern R2: the registry prefix is not a model field. Test the Tenant-to-Customer edge through system checks, queryset filtering, actual GETs and parent-bound creation using attribute="tenant"; never infer the FK from navbar_tenant.</action>

AncestorPolicy — UNCHECKABLE; AncestorPolicy(provider="guardian", accept_global_perms=False) — UNCHECKABLE; CreateViewParentMixin — UNCHECKABLE; Customer — UNCHECKABLE; GuardianViewSet — UNCHECKABLE; INSTALLED_APPS — UNCHECKABLE; NavbarMixin — SKIPPED; ParentViewSet — UNCHECKABLE; ParentViewSet(name="navbar_tenant", attribute="tenant") — UNCHECKABLE; Task — UNCHECKABLE; ViewSet — UNCHECKABLE; ViewSets — UNCHECKABLE; accept_global_perms — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; bound — UNCHECKABLE; business — UNCHECKABLE; checks — UNCHECKABLE; context — UNCHECKABLE; create — UNCHECKABLE; declaration — UNCHECKABLE; detail — UNCHECKABLE; harness — UNCHECKABLE; hierarchy — UNCHECKABLE; independent — UNCHECKABLE; key — UNCHECKABLE; model — UNCHECKABLE; name — UNCHECKABLE; navbar_customer — SKIPPED; navbar_demo — SKIPPED; navbar_tenant — SKIPPED; parent — UNCHECKABLE; prefix — UNCHECKABLE; project — UNCHECKABLE; provider — UNCHECKABLE; queryset — UNCHECKABLE; registry — UNCHECKABLE; routes — UNCHECKABLE; runner — UNCHECKABLE; table — UNCHECKABLE; tag — UNCHECKABLE; tests — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:96
>   <acceptance_criteria>Tenant object grants bound access to Customer routes; model permission alone cannot enter the other Tenant. Details and Notes return the same Customer identity with distinct active owner keys. Models and tests belong exclusively to navbar_demo.</acceptance_criteria>

Customer — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; bound — UNCHECKABLE; identity — UNCHECKABLE; keys — UNCHECKABLE; model — UNCHECKABLE; navbar_demo — SKIPPED; owner — UNCHECKABLE; permission — UNCHECKABLE; routes — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:97
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:98
>   <fails_when>Copied Customer URL bypasses Tenant object grants, tests depend on a superuser, another example model is imported, or Notes is not a second detail view of the same Customer.</fails_when>

Customer — UNCHECKABLE; detail — UNCHECKABLE; fails_when — UNCHECKABLE; model — UNCHECKABLE; tests — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:99
>   <done>Tenant object grants bound access to Customer routes; model permission alone cannot enter the other Tenant. Details and Notes return the same Customer identity with distinct active owner keys. Models and tests belong exclusively to navbar_demo.</done>

Customer — UNCHECKABLE; bound — UNCHECKABLE; identity — UNCHECKABLE; keys — UNCHECKABLE; model — UNCHECKABLE; navbar_demo — SKIPPED; owner — UNCHECKABLE; permission — UNCHECKABLE; routes — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:103
>   <name>06.40-04-02: Publish reversible example routes and the initial migration</name>

name — UNCHECKABLE; routes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:104
>   <files>examples/bootstrap5/navbar_demo/urls.py, examples/bootstrap5/project/urls.py, examples/bootstrap5/navbar_demo/migrations/__init__.py, examples/bootstrap5/navbar_demo/migrations/0001_initial.py, examples/bootstrap5/navbar_demo/tests.py</files>

__init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0001_initial.py — SKIPPED; examples/bootstrap5/navbar_demo/migrations/__init__.py — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; examples/bootstrap5/project/urls.py — UNCHECKABLE; migrations/__init__.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:105
>   <read_first>examples/bootstrap5/nested/urls.py; examples/bootstrap5/nested/migrations/0001_initial.py; examples/bootstrap5/project/urls.py</read_first>

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/nested/migrations/0001_initial.py — UNCHECKABLE; examples/bootstrap5/nested/urls.py — UNCHECKABLE; examples/bootstrap5/project/urls.py — UNCHECKABLE; project — UNCHECKABLE; read_first — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:106
>   <behavior>Exercise real project urlpatterns and parent create behavior; migration state equals models; no imported business-model dependency.</behavior>

business — UNCHECKABLE; create — UNCHECKABLE; model — UNCHECKABLE; parent — UNCHECKABLE; project — UNCHECKABLE; state — UNCHECKABLE; urlpatterns — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:107
>   <action>Wire app-local urlpatterns into project.urls under /object-navbar/ and give the landing route the name navbar-demo-home. Its view in views.py initially uses the authenticated Tenant entry flow and is extended with the final explanatory page in plan 05; no selected Tenant PK is accepted from an untrusted shortcut. Include both ViewSet URL sets. Generate 0001_initial for this app using the supported example environment and include migrations/__init__.py; its business dependencies are app-local. Extend actual project-URL tests to reverse and GET all declared links with noncolliding PKs and to verify inherited create/update/delete permissions and tenant-bound parent assignment. Do not add FEATURES until the seed module exists in plan 05. Use the exact Nox example session to provision dependencies (the cached core runner lacks whitenoise); Nox handles package install using existing declared dependencies. After provisioning, migration generation/checks use the interpreter under .nox/examples-3-12-django-5-2/bin/python from examples/bootstrap5, with PYTHONPATH=../../src:. for source work. Preserve this cwd distinction in the summary. Addresses review concern R16: run the explicit makemigrations navbar_demo --check --dry-run gate below after provisioning and after writing 0001_initial; require zero exit status. Record its exit separately from pytest, so a passing endpoint suite cannot mask migration drift.</action>

--check — UNCHECKABLE; --dry-run — UNCHECKABLE; ../../src — UNCHECKABLE; .nox/examples-3-12-django-5-2/bin/python — UNCHECKABLE; PK — UNCHECKABLE; ViewSet — UNCHECKABLE; __init__ — UNCHECKABLE; __init__.py — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; bound — UNCHECKABLE; business — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; create — UNCHECKABLE; delete — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; exists — UNCHECKABLE; gate — UNCHECKABLE; install — UNCHECKABLE; links — UNCHECKABLE; migrations/__init__.py — UNCHECKABLE; name — UNCHECKABLE; navbar_demo — SKIPPED; package — UNCHECKABLE; page — UNCHECKABLE; parent — UNCHECKABLE; permissions — UNCHECKABLE; project — UNCHECKABLE; project.urls — UNCHECKABLE; require — UNCHECKABLE; route — UNCHECKABLE; run — UNCHECKABLE; runner — UNCHECKABLE; seed — UNCHECKABLE; selected — UNCHECKABLE; session — UNCHECKABLE; source — UNCHECKABLE; tests — UNCHECKABLE; urlpatterns — UNCHECKABLE; urls — UNCHECKABLE; use — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:108
>   <acceptance_criteria>Public local example URLs resolve; valid cross-tenant requests remain denied; initial migration describes only navbar_demo models and makemigrations --check --dry-run reports no drift. Parent fields cannot be supplied to create a Customer in an unauthorized Tenant.</acceptance_criteria>

--check — UNCHECKABLE; --dry-run — UNCHECKABLE; Customer — UNCHECKABLE; Parent — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; check — UNCHECKABLE; create — UNCHECKABLE; fields — UNCHECKABLE; navbar_demo — SKIPPED; resolve — UNCHECKABLE; run — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:109
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:110
> (cd examples/bootstrap5 && PYTHONPATH=../../src:. ../../.nox/examples-3-12-django-5-2/bin/python manage.py makemigrations navbar_demo --check --dry-run)</automated></verify>

--check — UNCHECKABLE; --dry-run — UNCHECKABLE; ../../ — UNCHECKABLE; ../../.nox/examples-3-12-django-5-2/bin/python — UNCHECKABLE; ../../src — UNCHECKABLE; .nox/examples-3-12-django-5-2/bin/python — UNCHECKABLE; check — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; manage — UNCHECKABLE; manage.py — UNCHECKABLE; navbar_demo — SKIPPED; run — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:111
>   <fails_when>Project URL include is absent, reverse uses ambiguous names, migration drift exists, parent assignment escapes the selected Tenant, or direct unauthorized CRUD requests succeed.</fails_when>

Project — UNCHECKABLE; exists — UNCHECKABLE; fails_when — UNCHECKABLE; parent — UNCHECKABLE; selected — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:112
>   <done>Public local example URLs resolve; valid cross-tenant requests remain denied; initial migration describes only navbar_demo models and makemigrations --check --dry-run reports no drift. Parent fields cannot be supplied to create a Customer in an unauthorized Tenant.</done>

--check — UNCHECKABLE; --dry-run — UNCHECKABLE; Customer — UNCHECKABLE; Parent — UNCHECKABLE; check — UNCHECKABLE; create — UNCHECKABLE; fields — UNCHECKABLE; navbar_demo — SKIPPED; resolve — UNCHECKABLE; run — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:116
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:121
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:122
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:128
> | T-06.40-09 | Elevation of privilege | Tenant/Customer request boundary | high | mitigate | Task 01 uses strict Tenant Guardian grants and actual copied Customer URL tests. |

Customer — UNCHECKABLE; Task — UNCHECKABLE; boundary — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:129
> | T-06.40-10 | Tampering | Customer parent creation | high | mitigate | Task 02 proves server-bound Tenant assignment and unauthorized CRUD rejection. |

Customer — UNCHECKABLE; Task — UNCHECKABLE; bound — UNCHECKABLE; parent — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:130
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:131
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:134
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:137
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:138
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:139
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:142
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:146
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:149
> | R2 — prefixed parent/FK mapping | HIGH | Task01 explicitly maps navbar_tenant to tenant and tests actual parent filtering/creation. |

navbar_tenant — SKIPPED; parent — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:150
> | R16 — executable migration drift gate | MEDIUM | Task02 runs supported-env makemigrations navbar_demo --check --dry-run with a separate exit result. |

--check — UNCHECKABLE; --dry-run — UNCHECKABLE; check — UNCHECKABLE; gate — UNCHECKABLE; navbar_demo — SKIPPED; run — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:152
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:155
> | Example environment not provisioned | Already covered by Task02's Nox provisioning before migration commands; no unsupported core/6.1 shortcut. |

Example — UNCHECKABLE; before — UNCHECKABLE; environment — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:158
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:6
> depends_on: ["06.40-04"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:7
> files_modified: ["examples/bootstrap5/navbar_demo/models.py","examples/bootstrap5/navbar_demo/views.py","examples/bootstrap5/navbar_demo/urls.py","examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py","examples/bootstrap5/navbar_demo/tests.py","examples/bootstrap5/navbar_demo/seed.py","examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html","examples/bootstrap5/project/seeding.py","examples/bootstrap5/project/management/commands/seed.py","examples/bootstrap5/project/features.py","examples/bootstrap5/project/templates/project/crud_views.html","examples/bootstrap5/project/tests.py"]

crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py — SKIPPED; examples/bootstrap5/navbar_demo/models.py — SKIPPED; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/project/management/commands/seed.py — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; examples/bootstrap5/project/tests.py — UNCHECKABLE; features.py — UNCHECKABLE; files_modified — UNCHECKABLE; home.html — UNCHECKABLE; models.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE; seeding.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:12
>   raw_tokens: 30000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:17
>     - "Alice and Bob can perform business-model CRUD only under their granted Tenant; copied descendant URLs cannot bypass it."

business — UNCHECKABLE; model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:18
>     - "Charlie can read Customer/Order/Item in Alice's Tenant, but Address GETs and all write POSTs fail without database mutations."

Customer — UNCHECKABLE; Item — UNCHECKABLE; all — UNCHECKABLE; fail — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:19
>     - "Item pages retain Customer identity/hrefs and active clickable Orders; empty Orders remain visible and return 200."

Customer — UNCHECKABLE; Item — UNCHECKABLE; hrefs — UNCHECKABLE; identity — UNCHECKABLE; pages — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:20
>     - "The example index reaches a dedicated introduction listing Alice/Bob/Charlie credentials, usable through the existing login flow."

usable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:21
>     - "UI populated/partial states show four or three ordered links with identity above unchanged page header/actions; zero permitted data does not disclose other tenants."

actions — UNCHECKABLE; data — UNCHECKABLE; identity — UNCHECKABLE; links — UNCHECKABLE; page — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:23
>     - path: "examples/bootstrap5/navbar_demo/models.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/models.py — SKIPPED; models.py — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:24
>       provides: "Add Order, Item, Address to the independent hierarchy."

Item — UNCHECKABLE; hierarchy — UNCHECKABLE; independent — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:25
>     - path: "examples/bootstrap5/navbar_demo/views.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; navbar_demo — SKIPPED; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:26
>       provides: "Add all descendant CRUD views and final four-item Customer bar; render landing."

Customer — UNCHECKABLE; all — UNCHECKABLE; item — UNCHECKABLE; render — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:27
>     - path: "examples/bootstrap5/navbar_demo/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:28
>       provides: "Add descendant routes."

routes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:29
>     - path: "examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py — SKIPPED; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:31
>     - path: "examples/bootstrap5/navbar_demo/seed.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; navbar_demo — SKIPPED; seed — UNCHECKABLE; seed.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:32
>       provides: "NEW idempotent named-user scenario and bounded permissions."

bounded — UNCHECKABLE; permissions — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:33
>     - path: "examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html — SKIPPED; home.html — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:34
>       provides: "NEW discoverable landing/CTA and scenario explanations."

discover — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:35
>     - path: "examples/bootstrap5/navbar_demo/tests.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:36
>       provides: "Expand named-user/direct-write/deep-link/example rendering coverage."

link — UNCHECKABLE; user — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:37
>     - path: "examples/bootstrap5/project/seeding.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; project — UNCHECKABLE; seeding.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:38
>       provides: "Add Charlie credentials without changing developer grant policy."

developer — UNCHECKABLE; grant — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:39
>     - path: "examples/bootstrap5/project/management/commands/seed.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/management/commands/seed.py — UNCHECKABLE; project — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:40
>       provides: "Include Charlie in printed account help."

help — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:41
>     - path: "examples/bootstrap5/project/tests.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/tests.py — UNCHECKABLE; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:43
>     - path: "examples/bootstrap5/project/features.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; features.py — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:44
>       provides: "Register navbar_demo after its seed exists."

after — UNCHECKABLE; exists — UNCHECKABLE; navbar_demo — SKIPPED; seed — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:45
>     - path: "examples/bootstrap5/project/templates/project/crud_views.html"

crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:46
>       provides: "Whitespace-neutral opt-in navbar block before existing card."

before — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:47
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:48
>     - from: "examples/bootstrap5/navbar_demo/seed.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; navbar_demo — SKIPPED; seed — UNCHECKABLE; seed.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:49
>       to: "examples/bootstrap5/project/seeding.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; project — UNCHECKABLE; seeding.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:50
>       via: "Shared user/model-grant utilities with app-local data."

data — UNCHECKABLE; grant — UNCHECKABLE; model — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:51
>     - from: "examples/bootstrap5/project/features.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; features.py — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:52
>       to: "examples/bootstrap5/navbar_demo/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:54
>     - from: "examples/bootstrap5/project/templates/project/crud_views.html"

crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:55
>       to: "src/crud_views/templatetags/crud_views.py"

crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; src/crud_views/templatetags/crud_views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:56
>       via: "Explicit cv_navbar placement only."

cv_navbar — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:60
> Complete and seed the dedicated tenant-aware four-section navbar example.

section — UNCHECKABLE; seed — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:61
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:62
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:63
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:66
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:67
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:68
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:69
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:71
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:72
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:73
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:74
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:75
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:76
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:77
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:78
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:79
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:80
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:81
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:85
> - `examples/bootstrap5/navbar_demo/models.py`: Add Order, Item, Address to the independent hierarchy.

Item — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/models.py — SKIPPED; hierarchy — UNCHECKABLE; independent — UNCHECKABLE; models.py — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:86
> - `examples/bootstrap5/navbar_demo/views.py`: Add all descendant CRUD views and final four-item Customer bar; render landing.

Customer — UNCHECKABLE; all — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/views.py — SKIPPED; item — UNCHECKABLE; navbar_demo — SKIPPED; render — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:87
> - `examples/bootstrap5/navbar_demo/urls.py`: Add descendant routes.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; routes — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:88
> - `examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py`: NEW app-local descendant migration.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py — SKIPPED; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:89
> - `examples/bootstrap5/navbar_demo/seed.py`: NEW idempotent named-user scenario and bounded permissions.

bounded — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; navbar_demo — SKIPPED; permissions — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:90
> - `examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html`: NEW discoverable landing/CTA and scenario explanations.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html — SKIPPED; home.html — UNCHECKABLE; navbar_demo — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:91
> - `examples/bootstrap5/navbar_demo/tests.py`: Expand named-user/direct-write/deep-link/example rendering coverage.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; link — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE; user — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:92
> - `examples/bootstrap5/project/seeding.py`: Add Charlie credentials without changing developer grant policy.

developer — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; grant — UNCHECKABLE; project — UNCHECKABLE; seeding.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:93
> - `examples/bootstrap5/project/management/commands/seed.py`: Include Charlie in printed account help.

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/management/commands/seed.py — UNCHECKABLE; help — UNCHECKABLE; project — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:94
> - `examples/bootstrap5/project/features.py`: Register navbar_demo after its seed exists.

after — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; exists — UNCHECKABLE; features.py — UNCHECKABLE; navbar_demo — SKIPPED; project — UNCHECKABLE; seed — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:95
> - `examples/bootstrap5/project/templates/project/crud_views.html`: Whitespace-neutral opt-in navbar block before existing card.

before — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:97
> Plan 04 supplies the app and first migration. All business-model permissions remain model-level; Tenant is the sole Guardian grant boundary. Landing/index registration follows seed creation so the shared dispatcher never imports an absent seed.

boundary — UNCHECKABLE; business — UNCHECKABLE; grant — UNCHECKABLE; level — UNCHECKABLE; model — UNCHECKABLE; permissions — UNCHECKABLE; seed — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:101
>   <name>06.40-05-01: Navigate Customer sections through Order and Item requests</name>

Customer — UNCHECKABLE; Item — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:102
>   <files>examples/bootstrap5/navbar_demo/models.py, examples/bootstrap5/navbar_demo/views.py, examples/bootstrap5/navbar_demo/urls.py, examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py, examples/bootstrap5/navbar_demo/tests.py</files>

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py — SKIPPED; examples/bootstrap5/navbar_demo/models.py — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; models.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE; urls — UNCHECKABLE; urls.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:103
>   <read_first>examples/bootstrap5/nested/models.py; examples/bootstrap5/nested/views.py; examples/bootstrap5/nested/tests.py; src/crud_views/lib/ancestor_policy.py</read_first>

ancestor_policy — UNCHECKABLE; ancestor_policy.py — UNCHECKABLE; crud_views — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/nested/models.py — UNCHECKABLE; examples/bootstrap5/nested/tests.py — UNCHECKABLE; examples/bootstrap5/nested/views.py — UNCHECKABLE; models.py — UNCHECKABLE; read_first — UNCHECKABLE; src/crud_views/lib/ancestor_policy.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:104
>   <behavior>Read/write matrix for all business models; cross-Tenant valid IDs at every depth; unchanged row assertions after denied create/update/delete; Item navbar equality.</behavior>

Item — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; business — UNCHECKABLE; create — UNCHECKABLE; delete — UNCHECKABLE; matrix — UNCHECKABLE; row — UNCHECKABLE; unchanged — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:105
>   <action>Finish D-15's hierarchy with app-owned Order(customer), Item(order) and Address(customer), ordinary core protected ViewSets named navbar_order/navbar_item/navbar_address and full business-model CRUD pages. Add their app-local forms/tables in views.py, parent creation mixins, URLs and a normal second migration. Customer's one bar becomes exactly Details, Notes, Orders, Addresses, in that order; labels are explicit where defaults differ. Attach NavbarMixin to selected Customer object, Order collection/object/create/update and Item object/update pages, leaving one intermediate Order view without it to demonstrate independent ancestry resolution. Keep existing cascading behavior enabled explicitly through the available AncestorPolicy setting. Test actual URLs for Customer Details/Notes, Order list/detail/create/update and Item editing with deliberately different PKs. Item links preserve Customer and Tenant and activate Orders. Add full CRUD success tests for account-manager test users and all denied direct Address GETs and business-model write POSTs for read-only test users. Assert no rows are created/changed/deleted after denied POST, not merely status. Test copied valid Item and Address URLs across Tenants in both directions and no per-record Guardian grants below Tenant. Addresses review concern R2: declare Order and Address parents as ParentViewSet(name="navbar_customer", attribute="customer") and Item's parent as ParentViewSet(name="navbar_order", attribute="order"). Retain Customer's explicit tenant mapping from plan04. System checks plus real list/object/create requests exercise every edge and its assigned parent, using unequal PKs. Add a call_command('makemigrations', 'navbar_demo', check=True, dry_run=True) regression after 0002 is written, so this expansion also cannot leave migration drift.</action>

Address(customer) — UNCHECKABLE; AncestorPolicy — UNCHECKABLE; Customer — UNCHECKABLE; Item — UNCHECKABLE; Item(order) — UNCHECKABLE; NavbarMixin — SKIPPED; Order(customer) — UNCHECKABLE; ParentViewSet — UNCHECKABLE; ParentViewSet(name="navbar_customer", attribute="customer") — UNCHECKABLE; ParentViewSet(name="navbar_order", attribute="order") — UNCHECKABLE; ViewSets — UNCHECKABLE; action — UNCHECKABLE; activate — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; ancestry — UNCHECKABLE; available — UNCHECKABLE; business — UNCHECKABLE; call_command — UNCHECKABLE; call_command('makemigrations', 'navbar_demo', check=True, dry_run=True) — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; create — UNCHECKABLE; deleted — UNCHECKABLE; detail — UNCHECKABLE; dry_run — UNCHECKABLE; enabled — UNCHECKABLE; hierarchy — UNCHECKABLE; independent — UNCHECKABLE; labels — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; name — UNCHECKABLE; navbar_address — SKIPPED; navbar_customer — SKIPPED; navbar_demo — SKIPPED; navbar_item — SKIPPED; navbar_order — SKIPPED; pages — UNCHECKABLE; parent — UNCHECKABLE; record — UNCHECKABLE; rows — UNCHECKABLE; selected — UNCHECKABLE; success — UNCHECKABLE; tables — UNCHECKABLE; tests — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:106
>   <acceptance_criteria>AC2/AC3/AC9: full five-model hierarchy works; all four Customer sections are reachable; Item edit preserves caption/hrefs and active Orders even across omitted intermediate mixin. Cross-tenant descendant requests and Charlie-like direct Address/write requests fail without writes; manager CRUD succeeds.</acceptance_criteria>

Customer — UNCHECKABLE; Item — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; all — UNCHECKABLE; caption — UNCHECKABLE; edit — UNCHECKABLE; fail — UNCHECKABLE; hierarchy — UNCHECKABLE; hrefs — UNCHECKABLE; model — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:107
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:108
>   <fails_when>Any deep href changes Customer/Tenant, copied Item URL crosses tenants, a denied POST mutates rows, full-CRUD users cannot perform an operation, or business-record object grants are necessary.</fails_when>

Customer — UNCHECKABLE; Item — UNCHECKABLE; business — UNCHECKABLE; fails_when — UNCHECKABLE; href — UNCHECKABLE; record — UNCHECKABLE; rows — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:109
>   <done>AC2/AC3/AC9: full five-model hierarchy works; all four Customer sections are reachable; Item edit preserves caption/hrefs and active Orders even across omitted intermediate mixin. Cross-tenant descendant requests and Charlie-like direct Address/write requests fail without writes; manager CRUD succeeds.</done>

Customer — UNCHECKABLE; Item — UNCHECKABLE; all — UNCHECKABLE; caption — UNCHECKABLE; edit — UNCHECKABLE; fail — UNCHECKABLE; hierarchy — UNCHECKABLE; hrefs — UNCHECKABLE; model — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:113
>   <name>06.40-05-02: Seed Alice, Bob and Charlie with discoverable bounded grants</name>

bounded — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:114
>   <files>examples/bootstrap5/navbar_demo/seed.py, examples/bootstrap5/project/seeding.py, examples/bootstrap5/project/management/commands/seed.py, examples/bootstrap5/navbar_demo/tests.py</files>

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; examples/bootstrap5/navbar_demo/tests.py — SKIPPED; examples/bootstrap5/project/management/commands/seed.py — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE; seeding.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:115
>   <read_first>examples/bootstrap5/nested/seed.py; examples/bootstrap5/guardian_demo/seed.py; examples/bootstrap5/project/seeding.py; examples/bootstrap5/project/management/commands/seed.py</read_first>

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/guardian_demo/seed.py — UNCHECKABLE; examples/bootstrap5/nested/seed.py — UNCHECKABLE; examples/bootstrap5/project/management/commands/seed.py — UNCHECKABLE; examples/bootstrap5/project/seeding.py — UNCHECKABLE; guardian_demo — UNCHECKABLE; project — UNCHECKABLE; read_first — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE; seeding.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:116
>   <behavior>Two seeds -> same scenario/counts/grants; actual alice/bob/charlie login and endpoint matrix; empty collection -> visible link and 200.</behavior>

counts — UNCHECKABLE; link — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:117
>   <action>Seed D-15 idempotently: Tenant A/B, separate customer/order/item/address data, noncolliding descendant PKs, a second Alice-owned Customer with zero Orders, and simple Customer notes. Use ensure_demo_users and grant_model_perms; add charlie/charlie to DEMO_USERS before developer and to printed seed help, preserving developer as the last listed account. Correct the DEMO_USERS comment to distinguish seeded accounts from the static shared notices. Addresses review concern R6: the approved discoverability path is this example's own introduction (Task03) and demo reference (plan06), not an assumed dynamic change to shared home/login/banner notices. Preserve those existing translated notices and their catalogs. Alice/Bob get ordinary view/add/change/delete permissions for Customer/Order/Item/Address and view/change object grants on only their Tenant as required by read/write ancestor policy. Charlie receives only Customer/Order/Item view permissions and view on Tenant A; no Address or write grants. Do not silently expand the developer account's explicit read list, grant cross-tenant access, or remove unrelated app/user grants. Seed only app-owned data. Tests call seed twice and assert stable rows/grants, usable passwords through the real login route, actual named-user access matrices, empty Orders link visible plus GET 200, and no Address/write permissions for Charlie. Run existing shared seed/developer/i18n tests to retain their exact notice and developer-last invariants; no speculative shared notice or catalog rewrite is required.</action>

Customer — UNCHECKABLE; DEMO_USERS — UNCHECKABLE; Item — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; before — UNCHECKABLE; change — UNCHECKABLE; data — UNCHECKABLE; delete — UNCHECKABLE; developer — UNCHECKABLE; ensure_demo_users — UNCHECKABLE; expand — UNCHECKABLE; get — UNCHECKABLE; grant — UNCHECKABLE; grant_model_perms — UNCHECKABLE; help — UNCHECKABLE; item — UNCHECKABLE; link — UNCHECKABLE; permissions — UNCHECKABLE; reference — UNCHECKABLE; route — UNCHECKABLE; rows — UNCHECKABLE; seed — UNCHECKABLE; seeded — UNCHECKABLE; stable — UNCHECKABLE; tests — UNCHECKABLE; translated — UNCHECKABLE; unrelated — UNCHECKABLE; usable — UNCHECKABLE; user — UNCHECKABLE; view — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:118
>   <acceptance_criteria>The seeded named users reproduce the intended comparison: Alice/Bob full business CRUD in their own Tenant; Charlie reads only Customer/Order/Item in Tenant A; no per-business-record grants. Repeat seeding is safe and all three credentials are discoverable and usable.</acceptance_criteria>

Customer — UNCHECKABLE; Item — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; all — UNCHECKABLE; business — UNCHECKABLE; record — UNCHECKABLE; seeded — UNCHECKABLE; usable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:119
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:120
>   <fails_when>Seed duplicates data, grants Charlie write/Address or either manager the other Tenant, changes unrelated grants/developer policy, hides empty Orders, or listed credentials cannot log in.</fails_when>

data — UNCHECKABLE; developer — UNCHECKABLE; fails_when — UNCHECKABLE; unrelated — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:121
>   <done>The seeded named users reproduce the intended comparison: Alice/Bob full business CRUD in their own Tenant; Charlie reads only Customer/Order/Item in Tenant A; no per-business-record grants. Repeat seeding is safe and all three credentials are discoverable and usable.</done>

Customer — UNCHECKABLE; Item — UNCHECKABLE; all — UNCHECKABLE; business — UNCHECKABLE; record — UNCHECKABLE; seeded — UNCHECKABLE; usable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:125
>   <name>06.40-05-03: Expose the example from the index and place the bar above unchanged headers</name>

headers — UNCHECKABLE; name — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:126
>   <files>examples/bootstrap5/navbar_demo/views.py, examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html, examples/bootstrap5/project/features.py, examples/bootstrap5/project/templates/project/crud_views.html, examples/bootstrap5/project/tests.py</files>

crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; examples/bootstrap5/project/tests.py — UNCHECKABLE; features.py — UNCHECKABLE; home.html — UNCHECKABLE; navbar_demo — SKIPPED; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:127
>   <read_first>examples/bootstrap5/project/features.py; examples/bootstrap5/project/templates/project/home.html; examples/bootstrap5/project/templates/project/crud_views.html; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.html — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/project/templates/project/crud_views.html — UNCHECKABLE; examples/bootstrap5/project/templates/project/home.html — UNCHECKABLE; features.py — UNCHECKABLE; home.html — UNCHECKABLE; project — UNCHECKABLE; read_first — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:128
>   <behavior>Client follows actual index/landing/customer links for all named users; assert caption/nav/header order, exact controls, no-bar HTML parity and zero navbar work.</behavior>

all — UNCHECKABLE; caption — UNCHECKABLE; links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:129
>   <action>Turn navbar-demo-home into the dedicated authenticated landing page using the new local template. Show the approved account explanation, empty-Orders explanation and a real Explore object navigation link into the logged-in user's allowed Tenant/Customer path; derive permitted choices through existing Guardian queryset access, never from a hard-coded username gate. Link to Object navbar reference using Feature.docs/DocRef, registered in plan 06 after the documentation exists. Register navbar_demo in FEATURES now that its seed exists; use ui group, unique landing name and app-local code pointer. Add the cv_navbar tag in an example-owned cv_navbar block immediately after breadcrumb and before the existing card; use whitespace-neutral delimiters so nonparticipant rendered bytes remain unchanged. Do not move the existing heading/icon/actions or auto-attach bars. Test index -> landing -> permitted Customer -> Notes/Orders/Item navigation, normal and Charlie bars, normal page header order and coexistence with context actions. Preserve cross-app independence. The landing remains useful with an empty permitted Tenant queryset without leaking other tenants, using ordinary existing empty-state copy. Load no new global styles/scripts. Addresses review concerns R3/R4/R6: use the existing project.views.BreadcrumbMixin with LoginRequiredMixin and TemplateView, implementing cv_breadcrumb_get with cv_breadcrumb_prefix plus the Object navigation item and exposing cv_breadcrumb in context as ThemeIndexView does. The home template extends project/base.html, loads crud_views/example_tags/i18n, renders example_about and cv_breadcrumb before its content, and snippet_panels afterward; it must return 200 with no seeded Tenant for an authenticated superuser. Render all three literal credentials alice/alice, bob/bob and charlie/charlie together in this example intro, with the approved Charlie explanation and an ordinary link to the existing login route for switching users; the index already provides discovery via Alice/Bob's existing notices. Add navbar_demo at the end of FEATURES' ui group, and update the matching ordered list in project/tests.py::FeatureGroupsTest.test_grouping_matches_spec. In that owned shared module add bounded new-landing assertions for credential text/login href, no-data response, standard panels/breadcrumb and index-to-permitted Customer traversal; the app's role/deep-link/write tests remain in navbar_demo/tests.py from Tasks01/02. The documentation panel's data is supplied by plan06's DocRef task; run all other shared feature contracts now, then the complete shared suite in plan06 once that dependency exists. Do not weaken an existing shared assertion.</action>

BreadcrumbMixin — UNCHECKABLE; Customer — UNCHECKABLE; DocRef — UNCHECKABLE; Feature — UNCHECKABLE; Feature.docs — UNCHECKABLE; FeatureGroupsTest — UNCHECKABLE; FeatureGroupsTest.test_grouping_matches_spec — UNCHECKABLE; Item — UNCHECKABLE; LoginRequiredMixin — UNCHECKABLE; TemplateView — UNCHECKABLE; ThemeIndexView — UNCHECKABLE; action — UNCHECKABLE; actions — UNCHECKABLE; add — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; base — UNCHECKABLE; base.html — UNCHECKABLE; before — UNCHECKABLE; bounded — UNCHECKABLE; choices — UNCHECKABLE; complete — UNCHECKABLE; context — UNCHECKABLE; crud_views — UNCHECKABLE; cv_breadcrumb — UNCHECKABLE; cv_breadcrumb_get — UNCHECKABLE; cv_breadcrumb_prefix — UNCHECKABLE; cv_navbar — SKIPPED; data — UNCHECKABLE; docs/DocRef — UNCHECKABLE; example_about — UNCHECKABLE; example_tags — UNCHECKABLE; exists — UNCHECKABLE; gate — UNCHECKABLE; heading — UNCHECKABLE; href — UNCHECKABLE; item — UNCHECKABLE; link — UNCHECKABLE; name — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; now — UNCHECKABLE; page — UNCHECKABLE; project — UNCHECKABLE; project.views.BreadcrumbMixin — UNCHECKABLE; project/base.html — UNCHECKABLE; project/tests.py — UNCHECKABLE; queryset — UNCHECKABLE; reference — UNCHECKABLE; rendered — UNCHECKABLE; response — UNCHECKABLE; route — UNCHECKABLE; run — UNCHECKABLE; seed — UNCHECKABLE; seeded — UNCHECKABLE; snippet_panels — UNCHECKABLE; state — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; test_grouping_matches_spec — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; text — UNCHECKABLE; unchanged — UNCHECKABLE; use — UNCHECKABLE; user — UNCHECKABLE; views — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:130
>   <acceptance_criteria>AC1/AC5/AC9: feature is discoverable and its scenario can be followed after login; four links/Notes/empty Orders appear as specified, Charlie sees three. Layout is identity/items then unchanged header/actions. Nonparticipating example page bytes and behavior match the pre-placement baseline.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; actions — UNCHECKABLE; after — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; links — UNCHECKABLE; page — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:131
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py project/tests.py test_i18n.py -k 'not DocRefsPanelTest'</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; DocRefsPanelTest — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; test_i18n — UNCHECKABLE; test_i18n.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:132
>   <fails_when>Landing leaks unauthorized tenants, index cannot open it, documentation-link data is fabricated, header/actions move, no-bar pages gain whitespace/markup, or scenario requires another app's data.</fails_when>

actions — UNCHECKABLE; data — UNCHECKABLE; fails_when — UNCHECKABLE; link — UNCHECKABLE; open — UNCHECKABLE; pages — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:133
>   <done>AC1/AC5/AC9: feature is discoverable and its scenario can be followed after login; four links/Notes/empty Orders appear as specified, Charlie sees three. Layout is identity/items then unchanged header/actions. Nonparticipating example page bytes and behavior match the pre-placement baseline.</done>

actions — UNCHECKABLE; after — UNCHECKABLE; identity — UNCHECKABLE; items — UNCHECKABLE; links — UNCHECKABLE; page — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:137
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:142
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:143
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:149
> | T-06.40-11 | Elevation of privilege | descendant direct requests | high | mitigate | Task 01 proves copied valid URLs and all denied write POSTs leave rows unchanged. |

Task — UNCHECKABLE; all — UNCHECKABLE; rows — UNCHECKABLE; unchanged — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:150
> | T-06.40-12 | Elevation of privilege | demo grants and seeds | high | mitigate | Task 02 asserts exact Tenant/model grants after repeated seeding and ordinary named-user logins. |

Task — UNCHECKABLE; after — UNCHECKABLE; model — UNCHECKABLE; repeated — UNCHECKABLE; user — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:151
> | T-06.40-13 | Information disclosure | landing choices | high | mitigate | Task 03 lists only Guardian-authorized Tenant choices and tests empty allowed sets. |

Task — UNCHECKABLE; choices — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:152
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:153
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:156
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:159
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:160
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:161
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:164
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:168
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:171
> | R2 — descendant parent/FK mappings | HIGH | Task01 explicitly maps Customer and Order parent attributes and exercises every edge. |

Customer — UNCHECKABLE; parent — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:172
> | R3 — exact feature membership | HIGH | Task03 owns project/tests.py, ui ordering assertion and shared integration run. |

project — UNCHECKABLE; project/tests.py — UNCHECKABLE; run — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:173
> | R4 — standalone landing composition | HIGH | Task03 follows ThemeIndexView's breadcrumb/about/panel composition and unseeded 200 contract; final DocRef data verified in06. |

DocRef — UNCHECKABLE; ThemeIndexView — UNCHECKABLE; data — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:174
> | R6 — actual credential discovery | HIGH | Tasks02/03 select approved own-example intro, render all three credentials/login link, preserve shared translated notices/developer-last policy. |

all — UNCHECKABLE; developer — UNCHECKABLE; link — UNCHECKABLE; render — UNCHECKABLE; select — UNCHECKABLE; translated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:176
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:179
> | Change every shared credential notice/catalog | Rejected as unnecessary expansion: approved UI-SPEC permits own-example intro; R6 delivers and tests that path. |

tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:180
> | ALLOWED_HOSTS / asserted seed-output string failure | Rejected: cited settings permit local development hosts and current seed tests do not assert the claimed exact output string. |

ALLOWED_HOSTS — UNCHECKABLE; failure — UNCHECKABLE; seed — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:183
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:6
> depends_on: ["06.40-03","06.40-05"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:7
> files_modified: ["docs/reference/navbar.md","docs/reference/index.md","docs/reference/nested.md","docs/reference/context_buttons.md","docs/reference/breadcrumb.md","docs/development/stability.md","docs/reference/templates.md","docs/reference/theme.md","CHANGELOG.md","tests/test1/test_navbar_docs.py","examples/bootstrap5/project/features.py","examples/bootstrap5/test_doc_links.py","docs/getting_started/demo.md"]

CHANGELOG.md — UNCHECKABLE; breadcrumb.md — UNCHECKABLE; context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; demo.md — UNCHECKABLE; docs/development/stability.md — UNCHECKABLE; docs/getting_started/demo.md — UNCHECKABLE; docs/reference/breadcrumb.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; docs/reference/index.md — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; docs/reference/nested.md — UNCHECKABLE; docs/reference/templates.md — UNCHECKABLE; docs/reference/theme.md — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/test_doc_links.py — UNCHECKABLE; features.py — UNCHECKABLE; files_modified — UNCHECKABLE; getting_started — UNCHECKABLE; index.md — UNCHECKABLE; navbar.md — UNCHECKABLE; nested.md — UNCHECKABLE; project — UNCHECKABLE; reference — UNCHECKABLE; stability.md — UNCHECKABLE; templates.md — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar_docs.py — SKIPPED; theme.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:12
>   raw_tokens: 30000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:17
>     - "Readers can use declarations, per-view mixin, exact destinations and all three override levels with working documented examples."

all — UNCHECKABLE; examples — UNCHECKABLE; use — UNCHECKABLE; view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:18
>     - "The stable-at-1.0 inventory explicitly includes declarations, attachment, tag, templates and documented context; private helpers stay internal."

context — UNCHECKABLE; helpers — UNCHECKABLE; inventory — UNCHECKABLE; stable — UNCHECKABLE; tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:19
>     - "Reference and example contain reciprocal clickable URLs validated through Feature.docs/DocRef (AC9)."

DocRef — UNCHECKABLE; Feature — UNCHECKABLE; Feature.docs — UNCHECKABLE; docs/DocRef — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:20
>     - "Authorization limits, propagation and actual measured costs are stated without promising link/request equivalence."

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:22
>     - path: "docs/reference/navbar.md"

docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:23
>       provides: "NEW complete navbar reference."

complete — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:24
>     - path: "docs/reference/index.md"

docs/reference/index.md — UNCHECKABLE; index.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:25
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:26
>     - path: "docs/reference/nested.md"

docs/reference/nested.md — UNCHECKABLE; nested.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:27
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:28
>     - path: "docs/reference/context_buttons.md"

context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:29
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:30
>     - path: "docs/reference/breadcrumb.md"

breadcrumb.md — UNCHECKABLE; docs/reference/breadcrumb.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:31
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:32
>     - path: "docs/development/stability.md"

docs/development/stability.md — UNCHECKABLE; stability.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:33
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:34
>     - path: "docs/reference/templates.md"

docs/reference/templates.md — UNCHECKABLE; reference — UNCHECKABLE; templates.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:35
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:36
>     - path: "docs/reference/theme.md"

docs/reference/theme.md — UNCHECKABLE; reference — UNCHECKABLE; theme.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:37
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:38
>     - path: "CHANGELOG.md"

CHANGELOG.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:39
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:40
>     - path: "tests/test1/test_navbar_docs.py"

test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar_docs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:41
>       provides: "NEW executable documentation/public-surface checks."

checks — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:42
>     - path: "examples/bootstrap5/project/features.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; features.py — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:43
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:44
>     - path: "examples/bootstrap5/test_doc_links.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/test_doc_links.py — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:45
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:46
>     - path: "docs/getting_started/demo.md"

demo.md — UNCHECKABLE; docs/getting_started/demo.md — UNCHECKABLE; getting_started — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:47
>       provides: "Update existing consumer documentation or example-link integration."

Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:48
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:49
>     - from: "examples/bootstrap5/project/features.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; features.py — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:50
>       to: "docs/reference/navbar.md"

docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:51
>       via: "DocRef page maps to actual reference and reciprocal live URL."

DocRef — UNCHECKABLE; page — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:52
>     - from: "docs/development/stability.md"

docs/development/stability.md — UNCHECKABLE; stability.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:53
>       to: "src/crud_views/lib/navbar.py"

crud_views — UNCHECKABLE; navbar.py — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:54
>       via: "D-16 exact public inventory."

inventory — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:55
>     - from: "docs/reference/navbar.md"

docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:56
>       to: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; COST.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:57
>       via: "Measured costs with stated fixture/cache conditions."

state — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:61
> Publish consumer guidance, reciprocal example links and the stable-at-1.0 surface.

links — UNCHECKABLE; stable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:62
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:63
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:64
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:67
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:68
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:69
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:70
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:72
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:73
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:74
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:75
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:76
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:77
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:78
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:79
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:80
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:81
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:82
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:86
> - `docs/reference/navbar.md`: NEW complete navbar reference.

complete — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:87
> - `docs/reference/index.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; docs/reference/index.md — UNCHECKABLE; index.md — UNCHECKABLE; link — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:88
> - `docs/reference/nested.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; docs/reference/nested.md — UNCHECKABLE; link — UNCHECKABLE; nested.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:89
> - `docs/reference/context_buttons.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; link — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:90
> - `docs/reference/breadcrumb.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; breadcrumb.md — UNCHECKABLE; docs/reference/breadcrumb.md — UNCHECKABLE; link — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:91
> - `docs/development/stability.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; docs/development/stability.md — UNCHECKABLE; link — UNCHECKABLE; stability.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:92
> - `docs/reference/templates.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; docs/reference/templates.md — UNCHECKABLE; link — UNCHECKABLE; reference — UNCHECKABLE; templates.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:93
> - `docs/reference/theme.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; docs/reference/theme.md — UNCHECKABLE; link — UNCHECKABLE; reference — UNCHECKABLE; theme.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:94
> - `CHANGELOG.md`: Update existing consumer documentation or example-link integration.

CHANGELOG.md — UNCHECKABLE; Update — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:95
> - `tests/test1/test_navbar_docs.py`: NEW executable documentation/public-surface checks.

checks — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar_docs.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:96
> - `examples/bootstrap5/project/features.py`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; features.py — UNCHECKABLE; link — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:97
> - `examples/bootstrap5/test_doc_links.py`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/test_doc_links.py — UNCHECKABLE; link — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:98
> - `docs/getting_started/demo.md`: Update existing consumer documentation or example-link integration.

Update — UNCHECKABLE; demo.md — UNCHECKABLE; docs/getting_started/demo.md — UNCHECKABLE; getting_started — UNCHECKABLE; link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:100
> A-06/A-07 adopted; D-16 resolves the source's historical stability question. Public-contract reversibility is one-way at release and already settled by D-16, so no new approval gate. Companion delivery is separately owned by plan 07.

gate — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:104
>   <name>06.40-06-01: Document the complete declaration, behavior and override contract</name>

Document — UNCHECKABLE; complete — UNCHECKABLE; declaration — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:105
>   <files>docs/reference/navbar.md, docs/reference/index.md, docs/reference/nested.md, docs/reference/context_buttons.md, docs/reference/breadcrumb.md</files>

breadcrumb.md — UNCHECKABLE; context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; docs/reference/breadcrumb.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; docs/reference/index.md — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; docs/reference/nested.md — UNCHECKABLE; index.md — UNCHECKABLE; navbar.md — UNCHECKABLE; nested.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:106
>   <read_first>docs/reference/breadcrumb.md; docs/reference/context_buttons.md; docs/reference/nested.md; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md; src/crud_views/lib/navbar.py; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; COST.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; breadcrumb.md — UNCHECKABLE; context_buttons — UNCHECKABLE; context_buttons.md — UNCHECKABLE; crud_views — UNCHECKABLE; docs/reference/breadcrumb.md — UNCHECKABLE; docs/reference/context_buttons.md — UNCHECKABLE; docs/reference/nested.md — UNCHECKABLE; navbar.py — UNCHECKABLE; nested.md — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; section — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:107
>   <action>Write docs/reference/navbar.md covering D-01–D-14 and D-16: exact public imports/signatures, one project mixin, per-view attachment, owner object rule, descendant owner reuse, same-owner links with higher ancestors, active rules, GET eligibility, child default versus explicit keys, owner Update/second detail and child Create/custom collection examples. Document defaults/overrides for labels/icons, plain identity, all-hidden empty output, modal/omitted-template zero work, no row-count semantics, existing context-button coexistence, and unsupported cases/exclusions. Explain access-before-state and once-only child helper, reached configuration-error propagation and immediate-parent visibility limitation versus full destination authorization/querysets; navbar visibility never guarantees a destination response. Give working global wrapper, individual leaf, split placement and per-bar template examples using the finalized context fields, plus layout A solely as an application wrapper override. List exact wrapper/identity/items paths and independent empty guards. Quote actual measured cost table from COST.md with conditions, not a universal zero-query promise. Add reference-index entry and reciprocal related-reference links. The strict MkDocs configuration currently relies on generated navigation (nav is commented), so no speculative nav config edit. Include the exact live landing URL https://django-crud-views-demo.onrender.com/object-navbar/ in a Try it live admonition and normal account/reset guidance. Document the plan01 normalization boundary: the rendered default short-action label is entity-decoded once into plain text; raw caption/explicit label entity sequences remain literal. Markup is displayed as text and private normalization helpers are not public API. Explain construction-time type validation versus cooperative startup destination checks, valid empty items, missing custom-wrapper diagnostics, late-bound string owner/child names and the cv_object capability attachment rule.</action>

COST.md — UNCHECKABLE; Create — UNCHECKABLE; Document — UNCHECKABLE; List — UNCHECKABLE; MkDocs — UNCHECKABLE; Update — UNCHECKABLE; action — UNCHECKABLE; all — UNCHECKABLE; application — UNCHECKABLE; before — UNCHECKABLE; bound — UNCHECKABLE; boundary — UNCHECKABLE; button — UNCHECKABLE; caption — UNCHECKABLE; checks — UNCHECKABLE; child — UNCHECKABLE; context — UNCHECKABLE; count — UNCHECKABLE; custom — UNCHECKABLE; cv_object — UNCHECKABLE; default — UNCHECKABLE; demo.onrender.com — UNCHECKABLE; detail — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; edit — UNCHECKABLE; error — UNCHECKABLE; examples — UNCHECKABLE; fields — UNCHECKABLE; helper — UNCHECKABLE; helpers — UNCHECKABLE; identity — UNCHECKABLE; independent — UNCHECKABLE; items — UNCHECKABLE; keys — UNCHECKABLE; label — UNCHECKABLE; labels — UNCHECKABLE; layout — UNCHECKABLE; links — UNCHECKABLE; missing — UNCHECKABLE; navbar.md — UNCHECKABLE; owner — UNCHECKABLE; parent — UNCHECKABLE; project — UNCHECKABLE; reference — UNCHECKABLE; rendered — UNCHECKABLE; reset — UNCHECKABLE; response — UNCHECKABLE; row — UNCHECKABLE; state — UNCHECKABLE; table — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE; view — UNCHECKABLE; views — UNCHECKABLE; wrapper — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:108
>   <acceptance_criteria>AC7/AC9: a reader can configure and override the actual API without additional hidden project code. All approved behavior/limits and measured costs are documented; live example link is clickable and exact.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; configure — UNCHECKABLE; link — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:109
>   <verify><automated>.venv/bin/mkdocs build --strict</automated></verify>

--strict — UNCHECKABLE; .venv/bin/mkdocs — UNCHECKABLE; build — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:110
>   <fails_when>Docs fail strict build, describe unimplemented fields, promise universal authorization/query costs, omit an override mode or use a fabricated demo URL.</fails_when>

build — UNCHECKABLE; describe — UNCHECKABLE; fail — UNCHECKABLE; fails_when — UNCHECKABLE; fields — UNCHECKABLE; mode — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:111
>   <done>AC7/AC9: a reader can configure and override the actual API without additional hidden project code. All approved behavior/limits and measured costs are documented; live example link is clickable and exact.</done>

configure — UNCHECKABLE; link — UNCHECKABLE; project — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:115
>   <name>06.40-06-02: Inventory the stable surface and announce the additive feature</name>

Inventory — UNCHECKABLE; name — UNCHECKABLE; stable — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:116
>   <reversibility rating="one-way">Stable public declarations/tag/templates at 1.0 are already approved in D-16; release changes follow the existing major-version/deprecation policy.</reversibility>

tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:117
>   <files>docs/development/stability.md, docs/reference/templates.md, docs/reference/theme.md, CHANGELOG.md, tests/test1/test_navbar_docs.py</files>

CHANGELOG.md — UNCHECKABLE; docs/development/stability.md — UNCHECKABLE; docs/reference/templates.md — UNCHECKABLE; docs/reference/theme.md — UNCHECKABLE; reference — UNCHECKABLE; stability.md — UNCHECKABLE; templates.md — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; tests — UNCHECKABLE; tests/test1/test_navbar_docs.py — SKIPPED; theme.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:118
>   <read_first>docs/development/stability.md; docs/reference/templates.md; docs/reference/theme.md; CHANGELOG.md; src/crud_views/lib/navbar.py; src/crud_views/templatetags/crud_views.py</read_first>

CHANGELOG.md — UNCHECKABLE; crud_views — UNCHECKABLE; crud_views.py — UNCHECKABLE; docs/development/stability.md — UNCHECKABLE; docs/reference/templates.md — UNCHECKABLE; docs/reference/theme.md — UNCHECKABLE; navbar.py — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; src/crud_views/lib/navbar.py — SKIPPED; src/crud_views/templatetags/crud_views.py — UNCHECKABLE; stability.md — UNCHECKABLE; templates.md — UNCHECKABLE; theme.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:119
>   <behavior>Documented declaration and all override snippets instantiate/render; final inventory resolves existing public symbols and templates.</behavior>

all — UNCHECKABLE; declaration — UNCHECKABLE; inventory — UNCHECKABLE; render — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:120
>   <action>Per D-16 explicitly inventory NavBar, NavItem, CrudViewNavBarMixin, cv_navbar attachment, cv_navbar tag, three template paths and documented cv_navbar/item context fields as stable at 1.0 under the existing major-version/deprecation/migration policy. State private builders/resolvers/check carriers are internal. Add the template paths/contract to existing template/theme reference tables, with no new button-class keys or provisional exception. Add an Unreleased feature entry linked to navbar reference. The intended change is additive; if a real breaking change is discovered, treat it as a concrete scope finding and pair its Breaking entry with docs/migrating-1.0.md under repository policy. Add test_navbar_docs.py that imports the documented classes, constructs declarations using translated labels, compiles/renders documented tag/override examples against the real loaders, and checks that the inventoried templates/context expressions exist and match usable render data. Do not write brittle tests that merely count prose tokens. Include Pydantic-floor execution of these cases in plan 08. Addresses review concern R5 (conditional schema hazard): put navbar template-context documentation under a separate level-two Object navbar context heading before the existing Snippet variables heading, preserving that existing section's exact eight-row schema and prose. Navbar view-context fields do not become snippet variables. Include the existing test_snippet_docs.py in this task's focused command; keep its assertions unchanged.</action>

CrudViewNavBarMixin — SKIPPED; NavBar — SKIPPED; NavItem — SKIPPED; action — UNCHECKABLE; before — UNCHECKABLE; button — UNCHECKABLE; change — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; command — UNCHECKABLE; context — UNCHECKABLE; count — UNCHECKABLE; cv_navbar — SKIPPED; data — UNCHECKABLE; docs/migrating-1.0.md — UNCHECKABLE; examples — UNCHECKABLE; fields — UNCHECKABLE; heading — UNCHECKABLE; inventory — UNCHECKABLE; item — UNCHECKABLE; keys — UNCHECKABLE; labels — UNCHECKABLE; level — UNCHECKABLE; pair — UNCHECKABLE; reference — UNCHECKABLE; render — UNCHECKABLE; repository — UNCHECKABLE; row — UNCHECKABLE; section — UNCHECKABLE; stable — UNCHECKABLE; tables — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; test_snippet_docs — UNCHECKABLE; test_snippet_docs.py — UNCHECKABLE; tests — UNCHECKABLE; translated — UNCHECKABLE; unchanged — UNCHECKABLE; usable — UNCHECKABLE; view — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:121
>   <acceptance_criteria>Stable inventory covers exactly the final public declarations/tag/templates/context; private helpers remain internal. Documented examples execute against the actual package and there is an additive release entry with no undocumented public surface.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; context — UNCHECKABLE; examples — UNCHECKABLE; execute — UNCHECKABLE; helpers — UNCHECKABLE; inventory — UNCHECKABLE; package — UNCHECKABLE; tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:122
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_docs.py tests/test1/test_snippet_docs.py -n 4 -q</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; test_snippet_docs — UNCHECKABLE; test_snippet_docs.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar_docs.py — SKIPPED; tests/test1/test_snippet_docs.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:123
>   <fails_when>Documented imports/templates/examples fail, listed context cannot render, an actual public field is omitted, or provisional wording contradicts D-16.</fails_when>

context — UNCHECKABLE; examples — UNCHECKABLE; fail — UNCHECKABLE; fails_when — UNCHECKABLE; render — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:124
>   <done>Stable inventory covers exactly the final public declarations/tag/templates/context; private helpers remain internal. Documented examples execute against the actual package and there is an additive release entry with no undocumented public surface.</done>

context — UNCHECKABLE; examples — UNCHECKABLE; execute — UNCHECKABLE; helpers — UNCHECKABLE; inventory — UNCHECKABLE; package — UNCHECKABLE; tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:128
>   <name>06.40-06-03: Connect example and documentation in both directions</name>

name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:129
>   <files>examples/bootstrap5/project/features.py, examples/bootstrap5/test_doc_links.py, docs/getting_started/demo.md</files>

demo.md — UNCHECKABLE; docs/getting_started/demo.md — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/test_doc_links.py — UNCHECKABLE; features.py — UNCHECKABLE; getting_started — UNCHECKABLE; project — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:130
>   <read_first>examples/bootstrap5/project/features.py; examples/bootstrap5/test_doc_links.py; docs/getting_started/demo.md; docs/reference/navbar.md</read_first>

demo.md — UNCHECKABLE; docs/getting_started/demo.md — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/project/features.py — UNCHECKABLE; examples/bootstrap5/test_doc_links.py — UNCHECKABLE; features.py — UNCHECKABLE; getting_started — UNCHECKABLE; navbar.md — UNCHECKABLE; project — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:131
>   <action>Per D-15 and AC9 add navbar reference DocRef to navbar_demo's FEATURES entry, preserving its exact navbar-demo-home route. Limit additional DocRefs to pages that receive reciprocal Try it live URLs; related prose links alone need no DocRef. Update live-demo guidance for this scenario and Charlie's credentials without changing other examples' authorization descriptions. Existing test_doc_links.py already enumerates Feature.docs; extend only assertions genuinely needed for the new landing/anchor reciprocal contract. Run its actual tests with new example endpoint tests. Verify rendered landing contains the exact docs URL and reference admonition contains DEMO_BASE + reverse(feature.url_name), and links to heading anchors resolve in the built site. Addresses review concerns R3/R4/R6: after attaching the real navbar DocRef, run the entire project/tests.py shared feature suite as well as test_i18n.py and navbar_demo/tests.py, with no exclusion. Prove the standalone landing's snippet_panels now renders References to documentation and the real navbar URL, its standard about/Home breadcrumb survives, and the exact ui membership includes navbar_demo. State that all three scenario credentials are listed in the object-navbar introduction and here; do not promise Charlie appears in the unchanged shared translated login/home/banner notices. German landmark rendering/catalog delivery is owned and tested by plan02 (R15).</action>

DEMO_BASE — UNCHECKABLE; DocRef — UNCHECKABLE; DocRefs — UNCHECKABLE; Feature — UNCHECKABLE; Feature.docs — UNCHECKABLE; Update — UNCHECKABLE; action — UNCHECKABLE; add — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; examples — UNCHECKABLE; feature.url_name — UNCHECKABLE; heading — UNCHECKABLE; links — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; now — UNCHECKABLE; pages — UNCHECKABLE; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; reference — UNCHECKABLE; rendered — UNCHECKABLE; resolve — UNCHECKABLE; reverse(feature.url_name) — UNCHECKABLE; route — UNCHECKABLE; run — UNCHECKABLE; snippet_panels — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE; test_i18n — UNCHECKABLE; test_i18n.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE; translated — UNCHECKABLE; unchanged — UNCHECKABLE; url_name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:132
>   <acceptance_criteria>AC9: example landing links to the navbar reference; reference links to the live landing URL; DocRef page/anchor/reciprocal checks and strict docs pass.</acceptance_criteria>

DocRef — UNCHECKABLE; acceptance_criteria — UNCHECKABLE; checks — UNCHECKABLE; links — UNCHECKABLE; page — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:133
>   <verify><automated>.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py project/tests.py test_i18n.py test_doc_links.py</automated></verify>

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; examples — UNCHECKABLE; navbar_demo — SKIPPED; navbar_demo/tests.py — SKIPPED; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; test_doc_links — UNCHECKABLE; test_doc_links.py — UNCHECKABLE; test_i18n — UNCHECKABLE; test_i18n.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:134
>   <fails_when>Either direction lacks a real URL, a DocRef/anchor fails resolution, or new example documentation checks are not collected.</fails_when>

DocRef — UNCHECKABLE; checks — UNCHECKABLE; fails_when — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:135
>   <done>AC9: example landing links to the navbar reference; reference links to the live landing URL; DocRef page/anchor/reciprocal checks and strict docs pass.</done>

DocRef — UNCHECKABLE; checks — UNCHECKABLE; links — UNCHECKABLE; page — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:139
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:144
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:145
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:151
> | T-06.40-14 | Elevation of privilege | consumer authorization guidance | high | mitigate | Task 01 explicitly separates bounded visibility from full request enforcement and real tenant example. |

Task — UNCHECKABLE; bounded — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:152
> | T-06.40-15 | Tampering | override contract | medium | mitigate | Task 02 executes docs examples and tests template/context inventory against actual renders. |

Task — UNCHECKABLE; context — UNCHECKABLE; examples — UNCHECKABLE; inventory — UNCHECKABLE; template — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:153
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:154
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:157
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:160
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:161
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:162
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:165
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:169
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:172
> | R3/R4 — final shared feature contracts | HIGH | Task03 runs full project/tests.py after DocRef exists; no final test exclusion. |

DocRef — UNCHECKABLE; after — UNCHECKABLE; exists — UNCHECKABLE; project — UNCHECKABLE; project/tests.py — UNCHECKABLE; tests — UNCHECKABLE; tests.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:173
> | R5 — conditional snippet schema hazard | HIGH | Task02 isolates navbar context under a distinct level-two heading and runs unchanged test_snippet_docs.py. |

context — UNCHECKABLE; heading — UNCHECKABLE; level — UNCHECKABLE; test_snippet_docs — UNCHECKABLE; test_snippet_docs.py — UNCHECKABLE; unchanged — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:174
> | R6 — truthful credential documentation | HIGH | Tasks01/03 link the own-example credential introduction and document Charlie without promising shared-notice changes. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:175
> | R15 — locale delivery cross-reference | MEDIUM | Task03 explicitly relies on plan02's shipped .po/.mo and German landmark render test. |

reference — UNCHECKABLE; render — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:177
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:180
> | Temporary absent DocRef / speculative separate tag page | Already bounded: Task03 supplies real DocRef after docs exist and runs all shared contracts; Task02 updates actual existing references. |

DocRef — UNCHECKABLE; after — UNCHECKABLE; all — UNCHECKABLE; bounded — UNCHECKABLE; page — UNCHECKABLE; tag — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:181
> | Cost/reference-link coverage absent | Already covered by Tasks01/03: measured cache conditions and reciprocal actual URLs remain executable. |

link — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:184
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:6
> depends_on: ["06.40-06"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:7
> files_modified: ["../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md","../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md","../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md","../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md"]

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; CHANGELOG.md — UNCHECKABLE; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; SKILL.md — UNCHECKABLE; files_modified — UNCHECKABLE; navigation.md — UNCHECKABLE; reference — UNCHECKABLE; reference.md — UNCHECKABLE; section — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:12
>   raw_tokens: 20000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:17
>     - "Packaged guidance is updated in jacob-consulting/skills source, with the same stable declarations and template contract as product docs."

source — UNCHECKABLE; stable — UNCHECKABLE; template — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:18
>     - "Companion local instructions and native validation are applied; a separate scoped local commit records delivery."

commit — UNCHECKABLE; native — UNCHECKABLE; scoped — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:19
>     - "No installed mirror edit or publication substitutes for the required companion deliverable."

edit — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:21
>     - path: "../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md — SKIPPED; SKILL.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:22
>       provides: "EXTERNAL tracked source target; checkout is acquired by Task 01."

Task — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:23
>     - path: "../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md — SKIPPED; navigation.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:24
>       provides: "EXTERNAL tracked source target; checkout is acquired by Task 01."

Task — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:25
>     - path: "../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md — SKIPPED; reference — UNCHECKABLE; reference.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:26
>       provides: "EXTERNAL tracked source target; checkout is acquired by Task 01."

Task — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:27
>     - path: "../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md — SKIPPED; CHANGELOG.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:28
>       provides: "EXTERNAL tracked source target; checkout is acquired by Task 01."

Task — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:29
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:30
>       provides: "NEW companion acquisition/check/commit receipt."

check — UNCHECKABLE; commit — UNCHECKABLE; receipt — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:31
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:32
>     - from: "docs/reference/navbar.md"

docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; reference — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:33
>       to: "../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md — SKIPPED; navigation.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:34
>       via: "Companion recipes track the final documented navbar contract."

recipes — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:35
>     - from: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:36
>       to: "../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md"

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md — SKIPPED; SKILL.md — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:37
>       via: "Receipt identifies exact repository/base/commit and validator result."

base — UNCHECKABLE; commit — UNCHECKABLE; repository — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:41
> Update and verify the packaged skill in its verified companion source repository.

Update — UNCHECKABLE; repository — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:42
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:43
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:44
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:47
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:48
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:49
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:50
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:52
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:53
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:54
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:55
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:56
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:57
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:58
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:59
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:60
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:61
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:62
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:66
> - `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md`: EXTERNAL tracked source target; checkout is acquired by Task 01.

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md — SKIPPED; SKILL.md — UNCHECKABLE; Task — UNCHECKABLE; source — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:67
> - `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md`: EXTERNAL tracked source target; checkout is acquired by Task 01.

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md — SKIPPED; Task — UNCHECKABLE; navigation.md — UNCHECKABLE; source — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:68
> - `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md`: EXTERNAL tracked source target; checkout is acquired by Task 01.

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md — SKIPPED; Task — UNCHECKABLE; reference — UNCHECKABLE; reference.md — UNCHECKABLE; source — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:69
> - `../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md`: EXTERNAL tracked source target; checkout is acquired by Task 01.

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md — SKIPPED; CHANGELOG.md — UNCHECKABLE; Task — UNCHECKABLE; source — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:70
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md`: NEW companion acquisition/check/commit receipt.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; check — UNCHECKABLE; commit — UNCHECKABLE; receipt — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:72
> External-file paths are intentionally outside the product repository and are relative to the executing checkout, never installed mirrors. The authoritative remote and four target files are in COMPANION-GUIDANCE. Native validator path/workflow were independently inspected during planning. No new package install is required. Can run beside plan 08 after final docs settle.

after — UNCHECKABLE; install — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; run — UNCHECKABLE; workflow — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:76
>   <name>06.40-07-01: Deliver navbar guidance into the actual companion source checkout</name>

name — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:77
>   <files>../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md, ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md, ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md, ../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md</files>

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md — SKIPPED; ../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; CHANGELOG.md — UNCHECKABLE; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; SKILL.md — UNCHECKABLE; navigation.md — UNCHECKABLE; reference — UNCHECKABLE; reference.md — UNCHECKABLE; section — UNCHECKABLE; views — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:78
>   <read_first>.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-GUIDANCE.md; docs/development/index.md; docs/reference/navbar.md; docs/development/stability.md</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-GUIDANCE.md — UNCHECKABLE; GUIDANCE.md — UNCHECKABLE; docs/development/index.md — UNCHECKABLE; docs/development/stability.md — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; index.md — UNCHECKABLE; navbar.md — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; section — UNCHECKABLE; stability.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:79
>   <action>Fulfil A-06/AC9 companion delivery and D-16 using https://github.com/jacob-consulting/skills. Acquire an isolated source checkout at ../skills-navbar-06-40 with git clone if absent; if the path exists verify its Git top-level and exact remote identity before reuse. Never overwrite a foreign/dirty checkout: preserve it and use an isolated worktree from the verified source, recording the resulting path and adjusting this plan's companion commands accordingly. Use a local docs/navbar-06.40 branch for delivery; do not switch this product repository. Read companion AGENTS.md/CLAUDE.md if present, discover its local skills/rules, inspect its README and validation workflow, and confirm all four target paths are tracked with git ls-files before editing. Update the four listed companion files only: entry-point discoverability, declarations/mixin/GET destination rules, stable template/tag/context contract, split/global/per-bar recipes, lazy/no-item/modal behavior, access-before-state once-only child hook, nested-owner URL and immediate-parent limits, plain escaping, no-count scope and link to upstream navbar reference/live example. Keep implementation helpers internal; do not transplant downstream experiment code or edit installed skill mirrors. Write COMPANION-DELIVERY.md recording repository/checkout/base SHA, loaded local instructions, tracked targets, bounded changes and the comparison to final product docs. The upstream source repository and these targets were verified during planning; the checkout is an execution creation target, not an existing local file claim.</action>

../skills-navbar-06-40 — SKIPPED; AGENTS.md — UNCHECKABLE; CLAUDE.md — UNCHECKABLE; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; Never — UNCHECKABLE; Update — UNCHECKABLE; action — UNCHECKABLE; all — UNCHECKABLE; base — UNCHECKABLE; before — UNCHECKABLE; bounded — UNCHECKABLE; child — UNCHECKABLE; clone — UNCHECKABLE; context — UNCHECKABLE; count — UNCHECKABLE; discover — UNCHECKABLE; docs/navbar-06.40 — UNCHECKABLE; edit — UNCHECKABLE; exists — UNCHECKABLE; git — UNCHECKABLE; github.com — UNCHECKABLE; helpers — UNCHECKABLE; hook — UNCHECKABLE; identity — UNCHECKABLE; inspect — UNCHECKABLE; item — UNCHECKABLE; level — UNCHECKABLE; link — UNCHECKABLE; owner — UNCHECKABLE; parent — UNCHECKABLE; recipes — UNCHECKABLE; recording — UNCHECKABLE; reference — UNCHECKABLE; repository — UNCHECKABLE; source — UNCHECKABLE; stable — UNCHECKABLE; state — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; use — UNCHECKABLE; workflow — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:80
>   <acceptance_criteria>The actual companion source files carry the final navbar usage contract and correct public stability boundary; acquisition/instruction provenance and exact changed targets are recorded. No publication is claimed.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; boundary — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:81
>   <verify><automated>.venv/bin/python ../skills-navbar-06-40/scripts/validate.py</automated></verify>

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/scripts/validate.py — SKIPPED; .venv/bin/python — UNCHECKABLE; scripts/validate.py — UNCHECKABLE; validate — UNCHECKABLE; validate.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:82
>   <fails_when>Checkout is wrong or installed mirror, local instructions are unread, tracked targets are missing, validator fails, guidance differs from shipped API, or no actual source edits exist.</fails_when>

fails_when — UNCHECKABLE; missing — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:83
>   <done>The actual companion source files carry the final navbar usage contract and correct public stability boundary; acquisition/instruction provenance and exact changed targets are recorded. No publication is claimed.</done>

boundary — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:87
>   <name>06.40-07-02: Validate and commit the companion changes separately</name>

commit — UNCHECKABLE; name — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:88
>   <files>.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md</files>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:89
>   <read_first>../skills-navbar-06-40/scripts/validate.py; ../skills-navbar-06-40/.github/workflows/validate.yml; docs/reference/navbar.md; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md</read_first>

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/.github/workflows/validate.yml — SKIPPED; ../skills-navbar-06-40/scripts/validate.py — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; docs/reference/navbar.md — SKIPPED; navbar.md — UNCHECKABLE; read_first — UNCHECKABLE; reference — UNCHECKABLE; scripts/validate.py — UNCHECKABLE; section — UNCHECKABLE; validate — UNCHECKABLE; validate.py — UNCHECKABLE; validate.yml — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:90
>   <action>Run the companion's native python validator and any additional checks mandated by its inspected local instructions. The verified workflow runs python3 scripts/validate.py with PyYAML; the main project .venv Python has PyYAML and can execute that file without installing a new package. Review all four diffs against the final reference, including literal explicit-list behavior, owner-preserving URLs, permission/state sequencing and exact template fields. Stage only the four owned companion targets and make a separate local commit in that repository; preserve unrelated edits. Record source base, commit SHA, changed paths, exact commands/results and any failures in COMPANION-DELIVERY.md, then record product repository evidence separately through normal plan summary/commit handling. Do not push, tag, publish or alter package versions. A missing checkout/failed test leaves this required delivery unmet rather than deferred or substituted by an upstream note.</action>

COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; PyYAML — UNCHECKABLE; action — UNCHECKABLE; all — UNCHECKABLE; base — UNCHECKABLE; checks — UNCHECKABLE; commit — UNCHECKABLE; execute — UNCHECKABLE; failed — UNCHECKABLE; fields — UNCHECKABLE; main — UNCHECKABLE; make — UNCHECKABLE; missing — UNCHECKABLE; native — UNCHECKABLE; note — UNCHECKABLE; owner — UNCHECKABLE; package — UNCHECKABLE; permission — UNCHECKABLE; project — UNCHECKABLE; record — UNCHECKABLE; reference — UNCHECKABLE; repository — UNCHECKABLE; scripts/validate.py — UNCHECKABLE; source — UNCHECKABLE; state — UNCHECKABLE; tag — UNCHECKABLE; template — UNCHECKABLE; unrelated — UNCHECKABLE; validate — UNCHECKABLE; validate.py — UNCHECKABLE; workflow — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:91
>   <acceptance_criteria>Companion native checks pass and all four scoped guidance changes exist in a separate local commit with a recorded SHA; no unrelated files or publication are included.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; all — UNCHECKABLE; checks — UNCHECKABLE; commit — UNCHECKABLE; native — UNCHECKABLE; scoped — UNCHECKABLE; unrelated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:92
>   <verify><automated>.venv/bin/python ../skills-navbar-06-40/scripts/validate.py

../skills-navbar-06-40 — SKIPPED; ../skills-navbar-06-40/scripts/validate.py — SKIPPED; .venv/bin/python — UNCHECKABLE; scripts/validate.py — UNCHECKABLE; validate — UNCHECKABLE; validate.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:93
>  git -C ../skills-navbar-06-40 show --check --oneline HEAD</automated></verify>

--check — UNCHECKABLE; --oneline — UNCHECKABLE; ../skills-navbar-06-40 — SKIPPED; check — UNCHECKABLE; git — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:94
>   <fails_when>Native checks fail, commit lacks intended files, includes unrelated edits, receipt lacks reproducible SHA/results, or work is reported complete without actual local delivery.</fails_when>

checks — UNCHECKABLE; commit — UNCHECKABLE; complete — UNCHECKABLE; fail — UNCHECKABLE; fails_when — UNCHECKABLE; receipt — UNCHECKABLE; unrelated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:95
>   <done>Companion native checks pass and all four scoped guidance changes exist in a separate local commit with a recorded SHA; no unrelated files or publication are included.</done>

all — UNCHECKABLE; checks — UNCHECKABLE; commit — UNCHECKABLE; native — UNCHECKABLE; scoped — UNCHECKABLE; unrelated — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:99
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:104
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:105
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:111
> | T-06.40-16 | Tampering | companion repository provenance | high | mitigate | Task 01 verifies remote/tracked files and reads local instructions; Task 02 makes scoped local commit only. |

Task — UNCHECKABLE; commit — UNCHECKABLE; repository — UNCHECKABLE; scoped — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:112
> | T-06.40-17 | Elevation of privilege | companion guidance | medium | mitigate | Task 02 compares once-only visibility policy and destination authority to tested product docs. |

Task — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:113
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:114
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:117
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:120
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:121
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:122
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:125
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:129
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:132
> | Existing companion contract retained | INFO | Tasks01/02 already satisfy delivery; review-only dispositions below record rejected claims. |

record — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:134
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:137
> | Sibling-checkout sandbox HIGH | Rejected for this runner: unrestricted sibling access is established; Task01 still verifies path/provenance and failed acquisition leaves delivery unmet. |

failed — UNCHECKABLE; runner — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:138
> | Companion validator cwd | Rejected: scripts/validate.py derives REPO_ROOT from __file__, verified blob aa3207740dd95efc3ce36497503229486169eb53; no cwd workaround needed. |

REPO_ROOT — UNCHECKABLE; __file__ — UNCHECKABLE; scripts/validate.py — UNCHECKABLE; validate — UNCHECKABLE; validate.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:139
> | Companion path / SSH fallback / archive cleanup | No demonstrated access failure: existing relative acquisition, dirty-checkout isolation and actual-path receipt remain required; no speculative extra machinery. |

failure — UNCHECKABLE; fallback — UNCHECKABLE; receipt — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:142
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:2
> phase: 06.40-object-navbar-opt-in-section-navigation-381

section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:4
> type: execute

execute — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:6
> depends_on: ["06.40-06"]

depends_on — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:7
> files_modified: [".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png",".pytest_cache/navbar_browser_settings.py",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md",".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md"]

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png — SKIPPED; .pytest_cache/navbar_browser_settings.py — SKIPPED; ACCEPTANCE.md — UNCHECKABLE; BROWSER-CHECK.js — UNCHECKABLE; BROWSER.json — UNCHECKABLE; CHECK.js — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; desktop.png — UNCHECKABLE; files_modified — UNCHECKABLE; focus.png — UNCHECKABLE; navbar_browser_settings — SKIPPED; navbar_browser_settings.py — UNCHECKABLE; pytest_cache — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:9
> requirements: []

requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:12
>   raw_tokens: 20000

raw_tokens — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:15
> must_haves:

must_haves — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:17
>     - "UI navbar overflow/long-text and identity overflow/long-text wrap at 320px and 200% reflow without horizontal page scrolling or hidden/clipped text."

identity — UNCHECKABLE; page — UNCHECKABLE; text — UNCHECKABLE; wrap — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:18
>     - "Ordinary links retain normal full-document navigation, visible keyboard focus, accessible naming, declaration order and clickable current section."

Ordinary — UNCHECKABLE; declaration — UNCHECKABLE; links — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:19
>     - "Every supported source/installed/example matrix result is source-bound; explicit declared skips and unavailable cells are never called passing."

bound — UNCHECKABLE; matrix — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:20
>     - "Overall delivery is not accepted until companion source edits and separate local commit are evidenced."

commit — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:22
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; BROWSER-CHECK.js — UNCHECKABLE; CHECK.js — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:23
>       provides: "NEW reusable live Playwright assertion routine; executed through existing tool."

execute — UNCHECKABLE; usable — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:24
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json — SKIPPED; BROWSER.json — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:25
>       provides: "NEW measured live-browser result with URLs/dimensions/runtime/revision."

runtime — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:26
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png — SKIPPED; desktop.png — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:28
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png — SKIPPED; focus.png — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:29
>       provides: "NEW live narrow wrapping/focus screenshot."

row — UNCHECKABLE; wrap — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:30
>     - path: ".pytest_cache/navbar_browser_settings.py"

.pytest_cache/navbar_browser_settings.py — SKIPPED; navbar_browser_settings — SKIPPED; navbar_browser_settings.py — UNCHECKABLE; pytest_cache — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:31
>       provides: "NEW transient isolated-db browser settings, never committed."

committed — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:32
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; ACCEPTANCE.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:33
>       provides: "NEW source/installed/floor/package acceptance ledger."

package — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:34
>     - path: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:35
>       provides: "Finalize actual task/threat/UI evidence after execution."

after — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:36
>   key_links:

key_links — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:37
>     - from: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; BROWSER-CHECK.js — UNCHECKABLE; CHECK.js — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:38
>       to: "examples/bootstrap5/navbar_demo/urls.py"

examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/urls.py — SKIPPED; navbar_demo — SKIPPED; urls — UNCHECKABLE; urls.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:39
>       via: "Exercise real served endpoints and actual hrefs."

hrefs — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:40
>     - from: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; ACCEPTANCE.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:41
>       to: "noxfile.py"

noxfile.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:42
>       via: "Exact supported matrix and floor sessions."

matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:43
>     - from: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; ACCEPTANCE.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:44
>       to: ".planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md"

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md — SKIPPED; COMPANION-DELIVERY.md — UNCHECKABLE; DELIVERY.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:45
>       via: "Overall sign-off additionally requires parallel companion receipt."

receipt — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:49
> Obtain live UI evidence and final supported-source/installed acceptance results.

source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:50
> Purpose: Deliver the approved object-navbar contract without changing established request policy or context buttons.

buttons — UNCHECKABLE; context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:51
> Output: The artifacts listed below and task-specific passing evidence.

-s — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:52
> No formal requirement IDs exist for this phase: requirements is deliberately empty. AC1–AC9 are issue acceptance labels. Spec-less requirement probing was skipped, not interpreted as missing product constraints.

labels — UNCHECKABLE; missing — UNCHECKABLE; requirement — UNCHECKABLE; requirements — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:55
> <execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:56
> @/home/alex/.codex/gsd-core/workflows/execute-plan.md

/home/alex/.codex/gsd-core/workflows/execute-plan.md — UNCHECKABLE; execute — UNCHECKABLE; plan.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:57
> @/home/alex/.codex/gsd-core/templates/summary.md

/home/alex/.codex/gsd-core/templates/summary.md — UNCHECKABLE; summary.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:58
> </execution_context>

execution_context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:60
> <context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:61
> @CLAUDE.md

CLAUDE.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:62
> @.planning/PROJECT.md

.planning/PROJECT.md — UNCHECKABLE; PROJECT.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:63
> @.planning/ROADMAP.md

.planning/ROADMAP.md — UNCHECKABLE; ROADMAP.md — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:64
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md — UNCHECKABLE; CONTEXT.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:65
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:66
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md — UNCHECKABLE; RESEARCH.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:67
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md — UNCHECKABLE; PATTERNS.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:68
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; SPEC.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:69
> @.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:70
> </context>

context — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:74
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js`: NEW reusable live Playwright assertion routine; executed through existing tool.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; BROWSER-CHECK.js — UNCHECKABLE; CHECK.js — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:75
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json`: NEW measured live-browser result with URLs/dimensions/runtime/revision.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json — SKIPPED; BROWSER.json — UNCHECKABLE; runtime — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:76
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png`: NEW live desktop/header-placement screenshot.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png — SKIPPED; desktop.png — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:77
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png`: NEW live narrow wrapping/focus screenshot.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png — SKIPPED; focus.png — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:78
> - `.pytest_cache/navbar_browser_settings.py`: NEW transient isolated-db browser settings, never committed.

.pytest_cache/navbar_browser_settings.py — SKIPPED; committed — UNCHECKABLE; navbar_browser_settings — SKIPPED; navbar_browser_settings.py — UNCHECKABLE; pytest_cache — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:79
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md`: NEW source/installed/floor/package acceptance ledger.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; ACCEPTANCE.md — UNCHECKABLE; package — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:80
> - `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md`: Finalize actual task/threat/UI evidence after execution.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; after — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:82
> Final wave can run beside companion plan07: no shared task files. Acceptance ledger may be drafted before companion finishes, but its overall sign-off waits for that receipt. Browser assertions are automated tool calls, not a shell substitute; native browser availability is required for AC8. Full matrix is deliberately a longer final gate; focused tasks earlier provide sub-minute feedback.

before — UNCHECKABLE; calls — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE; native — UNCHECKABLE; receipt — UNCHECKABLE; run — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:86
>   <name>06.40-08-01: Measure live wrapping, long text and keyboard navigation</name>

name — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:87
>   <files>.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png, .pytest_cache/navbar_browser_settings.py</files>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png — SKIPPED; .pytest_cache/navbar_browser_settings.py — SKIPPED; BROWSER-CHECK.js — UNCHECKABLE; BROWSER.json — UNCHECKABLE; CHECK.js — UNCHECKABLE; desktop.png — UNCHECKABLE; focus.png — UNCHECKABLE; navbar_browser_settings — SKIPPED; navbar_browser_settings.py — UNCHECKABLE; pytest_cache — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:88
>   <read_first>.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-PROBE.json; examples/bootstrap5/project/settings.py; examples/bootstrap5/navbar_demo/seed.py; examples/bootstrap5/navbar_demo/views.py</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-PROBE.json — UNCHECKABLE; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md — UNCHECKABLE; PROBE.json — UNCHECKABLE; SPEC.md — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; examples/bootstrap5/navbar_demo/seed.py — SKIPPED; examples/bootstrap5/navbar_demo/views.py — SKIPPED; examples/bootstrap5/project/settings.py — UNCHECKABLE; navbar_demo — SKIPPED; project — UNCHECKABLE; read_first — UNCHECKABLE; section — UNCHECKABLE; seed — UNCHECKABLE; seed.py — UNCHECKABLE; settings.py — UNCHECKABLE; views — UNCHECKABLE; views.py — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:89
>   <action>After the supported example Nox environment exists, create a transient navbar_browser_settings module under .pytest_cache that imports project.settings and replaces only DATABASES default NAME with an isolated temporary SQLite file; preserve auth, templates and static configuration. From examples/bootstrap5 run the .nox/examples-3-12-django-5-2/bin/python interpreter via ../../ path with PYTHONPATH=../../src:.:../../.pytest_cache, --settings=navbar_browser_settings: migrate, seed, then runserver 127.0.0.1:8765 --noreload. Do not mutate a developer/demo database. Write BROWSER-CHECK.js as the reusable body for the available Playwright browser_run_code tool (uses its page argument; no npm install). Assert and record on the real served example: login Alice, follow landing/Customer/Notes/Orders/Item links; repeat Charlie for hidden Addresses and correct three-link order; normal full bar has four ordered links. At 1280px and 320px and a real 200% zoom/reflow-equivalent CSS viewport, measure document.scrollWidth <= document.clientWidth + 1 and every link bounding box within its parent. Record exact viewport/zoom method rather than claiming deviceScaleFactor is zoom. Exercise normal copy plus a >=120-character caption with an unbroken >=80-character token and a long multiword label, changing text in the isolated fixture/DOM without changing navbar classes and recording stress setup. Confirm at least two item rows in narrow stress state, no clipped/ellipsized text, hidden links or horizontal strip. Tab/Shift+Tab reaches visible links in order, including active; Enter follows exact href, and caption/icons are not extra focus stops. Verify accessible landmark name/current marker, absent tab roles, visible focus and normal-text contrast against actual Bootstrap styles. Capture desktop layout and narrow focused wrapped state; write JSON with source revision, browser/runtime, assertions, URLs, dimensions and screenshots. Test browser-native full document navigation with no navbar fetch/spinner/retry machinery. If CSS utilities fail reflow, fix only navbar templates/styles through the owning plan and rerun its no-output/nonparticipant tests before continuing. Browser inability remains an unmet human-check item; HTML snapshots cannot close it. Addresses review concern R12: the orchestration that creates the temporary settings/database and starts runserver must own a try/finally cleanup across setup, browser success, assertion failure and interruption. Reserve the settings path only if absent (do not overwrite another run's file), allocate the SQLite database in a unique temporary directory, record exact created paths and the launched process/session PID, and fail on an occupied port rather than stopping an existing process. In finally, stop and await only this run's server, remove only its settings file/bytecode and temporary database directory, and retain JSON/screenshots and failure evidence. Record cleanup results in BROWSER.json. The browser JS routine is executed inside this outer lifecycle; merely adding a JS finally cannot clean up a separately launched server. Exercise a deliberate failing assertion once, then verify server exit, released owned port and deleted owned transient paths before the successful run.</action>

--noreload — UNCHECKABLE; --settings — UNCHECKABLE; ../../ — UNCHECKABLE; ../../.pytest_cache — UNCHECKABLE; ../../src — UNCHECKABLE; .nox/examples-3-12-django-5-2/bin/python — UNCHECKABLE; BROWSER-CHECK.js — UNCHECKABLE; BROWSER.json — UNCHECKABLE; CHECK.js — UNCHECKABLE; Customer — UNCHECKABLE; Item — UNCHECKABLE; action — UNCHECKABLE; available — UNCHECKABLE; before — UNCHECKABLE; browser_run_code — UNCHECKABLE; caption — UNCHECKABLE; check — UNCHECKABLE; clean — UNCHECKABLE; clientWidth — UNCHECKABLE; create — UNCHECKABLE; default — UNCHECKABLE; deleted — UNCHECKABLE; developer — UNCHECKABLE; deviceScaleFactor — UNCHECKABLE; document.clientWidth — UNCHECKABLE; document.scrollWidth — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; exists — UNCHECKABLE; fail — UNCHECKABLE; failure — UNCHECKABLE; href — UNCHECKABLE; install — UNCHECKABLE; item — UNCHECKABLE; label — UNCHECKABLE; layout — UNCHECKABLE; link — UNCHECKABLE; links — UNCHECKABLE; measure — UNCHECKABLE; mutate — UNCHECKABLE; name — UNCHECKABLE; native — UNCHECKABLE; navbar_browser_settings — SKIPPED; page — UNCHECKABLE; parent — UNCHECKABLE; process — UNCHECKABLE; project — UNCHECKABLE; project.settings — UNCHECKABLE; pytest_cache — UNCHECKABLE; record — UNCHECKABLE; recording — UNCHECKABLE; rows — UNCHECKABLE; run — UNCHECKABLE; runtime — UNCHECKABLE; scrollWidth — UNCHECKABLE; seed — UNCHECKABLE; session — UNCHECKABLE; setup — UNCHECKABLE; source — UNCHECKABLE; state — UNCHECKABLE; stop — UNCHECKABLE; success — UNCHECKABLE; tests — UNCHECKABLE; text — UNCHECKABLE; up — UNCHECKABLE; write — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:90
>   <acceptance_criteria>AC8 and UI navbar overflow/long-text plus identity overflow/long-text: real 320px/1280px/200% reflow passes width/bounds/wrapping checks with all text visible. Keyboard navigation, focus, accessible naming, active links and header placement are evidenced on the live example.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; all — UNCHECKABLE; checks — UNCHECKABLE; identity — UNCHECKABLE; links — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:91
>   <verify><automated>Playwright browser_run_code executes the async page routine in .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js; all its live assertions must pass and return the measured result saved in .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json.</automated></verify>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json. — UNCHECKABLE; BROWSER-CHECK.js — UNCHECKABLE; BROWSER.json — UNCHECKABLE; CHECK.js — UNCHECKABLE; all — UNCHECKABLE; browser_run_code — UNCHECKABLE; page — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:92
>   <fails_when>Document/link bounds overflow, long text clips, links are hidden to fit, keyboard cannot activate current/other links, actual zoom/reflow is untested, assets fail to load, or screenshots/measurements are missing, or the owned server/transient paths survive either successful or failed verification.</fails_when>

Document — UNCHECKABLE; activate — UNCHECKABLE; fail — UNCHECKABLE; failed — UNCHECKABLE; fails_when — UNCHECKABLE; link — UNCHECKABLE; links — UNCHECKABLE; load — UNCHECKABLE; missing — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:93
>   <done>AC8 and UI navbar overflow/long-text plus identity overflow/long-text: real 320px/1280px/200% reflow passes width/bounds/wrapping checks with all text visible. Keyboard navigation, focus, accessible naming, active links and header placement are evidenced on the live example.</done>

all — UNCHECKABLE; checks — UNCHECKABLE; identity — UNCHECKABLE; links — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:97
>   <name>06.40-08-02: Run supported source and installed acceptance gates</name>

name — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:98
>   <files>.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md, .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md</files>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md — SKIPPED; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; ACCEPTANCE.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:99
>   <read_first>noxfile.py; pyproject.toml; package.json; scripts/check_dist.py; .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md</read_first>

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md — UNCHECKABLE; VALIDATION.md — UNCHECKABLE; check_dist — UNCHECKABLE; check_dist.py — UNCHECKABLE; noxfile.py — UNCHECKABLE; package — UNCHECKABLE; package.json — UNCHECKABLE; pyproject.toml — UNCHECKABLE; read_first — UNCHECKABLE; scripts/check_dist.py — UNCHECKABLE; section — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:100
>   <action>After all product/docs source is final, record exact Git revision plus uncommitted input hashes and actual Python/Django/Pydantic/Guardian versions. Run full source tests with four workers on cached Python3.12 Django4.2/5.2/6.0 interpreters using explicit PYTHONPATH=src:.; do not run the root venv's observed Django6.1 as supported evidence. Run the existing Nox tests/examples matrix (Python3.12/3.13/3.14/3.15 x Django4.2/5.2/6.0), preserving installed-origin assertions and both normal/request-recorder passes; pass -n 4 last through posargs for bounded workers, including examples. Nox's Django4.2 + Python3.14/3.15 skips are declared skips, not passes. Probe uv-managed runtimes before calling a missing PATH interpreter unavailable. Run existing crispy_floor sessions and manage_report_floor with a fresh CV_MANAGE_SCHEMA_EXPORT_DIR and append all six navbar test modules plus test_navbar_docs.py, proving Pydantic2.2.1 through its existing version/import-origin assertions. Run strict docs, Ruff check/format, npm test and package build/allowlist session. Existing Nox package installs use declared dependencies; no new package is authorized. Save per-cell counts/skips/failure reason, source-versus-installed provenance and input fingerprint; package assets/templates must exist in wheel. Fix actionable failures in their owning slice and repeat affected gates, then final-source gates if inputs changed. Update validation statuses only from actual results; record browser evidence from Task01 and companion receipt as a separate final dependency (plan07 can run in parallel). Do not mark phase acceptance complete until companion local delivery and all required available checks pass; unavailable cells/browser checks remain explicit limitations requiring closure, never silently passing AC9.</action>

-n — UNCHECKABLE; CV_MANAGE_SCHEMA_EXPORT_DIR — UNCHECKABLE; Probe — UNCHECKABLE; Update — UNCHECKABLE; action — UNCHECKABLE; all — UNCHECKABLE; available — UNCHECKABLE; before — UNCHECKABLE; bounded — UNCHECKABLE; build — UNCHECKABLE; cell — UNCHECKABLE; check — UNCHECKABLE; checks — UNCHECKABLE; complete — UNCHECKABLE; counts — UNCHECKABLE; crispy_floor — UNCHECKABLE; examples — UNCHECKABLE; failure — UNCHECKABLE; limitations — UNCHECKABLE; manage_report_floor — UNCHECKABLE; matrix — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; package — UNCHECKABLE; receipt — UNCHECKABLE; record — UNCHECKABLE; run — UNCHECKABLE; session — UNCHECKABLE; source — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; tests — UNCHECKABLE; tests/examples — UNCHECKABLE; use — UNCHECKABLE; x — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:101
>   <acceptance_criteria>AC9: final-source, installed normal/recorder, example, declared-floor, docs, lint, JS and package gates have honest evidence, with declared skips separated from unavailable/failing cells. Validation maps every task/UI/threat to actual evidence and companion delivery before overall sign-off.</acceptance_criteria>

acceptance_criteria — UNCHECKABLE; before — UNCHECKABLE; package — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:102
>   <verify><automated>PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests -n 4 -q

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-5-2/bin/python — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:103
> PYTHONPATH=src:. .nox/tests-3-12-django-4-2/bin/python -m pytest tests -n 4 -q

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-4-2/bin/python — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:104
> PYTHONPATH=src:. .nox/tests-3-12-django-6-0/bin/python -m pytest tests -n 4 -q

-n — UNCHECKABLE; -q — UNCHECKABLE; .nox/tests-3-12-django-6-0/bin/python — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:105
> .venv/bin/nox -s tests examples crispy_floor -- -n 4 -q

-n — UNCHECKABLE; -q — UNCHECKABLE; -s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; crispy_floor — UNCHECKABLE; examples — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:106
> CV_MANAGE_SCHEMA_EXPORT_DIR="$(mktemp -d)" .venv/bin/nox -s manage_report_floor -- tests/test1/test_navbar.py tests/test1/test_navbar_checks.py tests/test1/test_navbar_templates.py tests/test1/test_navbar_permissions.py tests/test1/test_navbar_costs.py tests/test1/test_navbar_docs.py

-s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; CV_MANAGE_SCHEMA_EXPORT_DIR — UNCHECKABLE; manage_report_floor — UNCHECKABLE; test_navbar — UNCHECKABLE; test_navbar.py — SKIPPED; test_navbar_checks — UNCHECKABLE; test_navbar_checks.py — UNCHECKABLE; test_navbar_costs — UNCHECKABLE; test_navbar_costs.py — UNCHECKABLE; test_navbar_docs — UNCHECKABLE; test_navbar_docs.py — SKIPPED; test_navbar_permissions — UNCHECKABLE; test_navbar_permissions.py — UNCHECKABLE; test_navbar_templates — UNCHECKABLE; test_navbar_templates.py — UNCHECKABLE; tests — UNCHECKABLE; tests/test1/test_navbar.py — SKIPPED; tests/test1/test_navbar_checks.py — SKIPPED; tests/test1/test_navbar_costs.py — SKIPPED; tests/test1/test_navbar_docs.py — SKIPPED; tests/test1/test_navbar_permissions.py — SKIPPED; tests/test1/test_navbar_templates.py — SKIPPED

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:107
> .venv/bin/mkdocs build --strict

--strict — UNCHECKABLE; .venv/bin/mkdocs — UNCHECKABLE; build — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:108
> .venv/bin/ruff check src tests examples

.venv/bin/ruff — UNCHECKABLE; check — UNCHECKABLE; examples — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:109
> .venv/bin/ruff format --check src tests examples

--check — UNCHECKABLE; .venv/bin/ruff — UNCHECKABLE; check — UNCHECKABLE; examples — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:111
> .venv/bin/nox -s package</automated></verify>

-s — UNCHECKABLE; .venv/bin/nox — UNCHECKABLE; package — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:112
>   <fails_when>Any required assertion/test/build fails, installed checks import checkout source, requested tests are uncollected, source changes after receipt, unsupported/unavailable cells are reported as passes, or browser/companion obligations lack evidence.</fails_when>

after — UNCHECKABLE; build — UNCHECKABLE; checks — UNCHECKABLE; fails_when — UNCHECKABLE; receipt — UNCHECKABLE; source — UNCHECKABLE; tests — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:113
>   <done>AC9: final-source, installed normal/recorder, example, declared-floor, docs, lint, JS and package gates have honest evidence, with declared skips separated from unavailable/failing cells. Validation maps every task/UI/threat to actual evidence and companion delivery before overall sign-off.</done>

before — UNCHECKABLE; package — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:117
> <threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:122
> | Configuration/request/template | Declarations and request identity drive links; model text crosses into HTML. |

identity — UNCHECKABLE; links — UNCHECKABLE; model — UNCHECKABLE; template — UNCHECKABLE; text — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:123
> | Visibility/destination | A link never grants authority; existing destination authorization remains authoritative. |

link — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:129
> | T-06.40-18 | Information disclosure | browser fixture database | medium | mitigate | Task 01 uses isolated SQLite/local server and finally cleans its own process and paths on all exits; never modifies developer/demo data. |

Task — UNCHECKABLE; all — UNCHECKABLE; data — UNCHECKABLE; developer — UNCHECKABLE; process — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:130
> | T-06.40-19 | Tampering | verification provenance | high | mitigate | Task 02 binds results to source hashes/versions and installed-origin assertions; never counts skips/unavailable as passing. |

Task — UNCHECKABLE; counts — UNCHECKABLE; source — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:131
> | T-06.40-SC | Tampering | Existing dependency tooling | high | mitigate | No new runtime packages. Existing declared dependency installs use current Nox sessions and repository pins. Any newly introduced package requires a legitimacy audit and blocking review for ASSUMED/SUS; SLOP forbidden. |

audit — UNCHECKABLE; forbidden — UNCHECKABLE; package — UNCHECKABLE; repository — UNCHECKABLE; runtime — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:132
> </threat_model>

threat_model — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:135
> Run every task command from the repository root unless an explicit cwd is specified. New tests are created by their task before verification; zero collection, wrong interpreter or missing prerequisites are failures. Focused core runner is the existing Django 5.2 environment. Example runner uses the verified Nox session (its cwd changes to examples/bootstrap5); do not use the project venv's observed Django 6.1.2 as supported-series evidence. Record versions, commands and failures in the summary. Broad runs use four workers.

Example — UNCHECKABLE; before — UNCHECKABLE; command — UNCHECKABLE; environment — UNCHECKABLE; examples — UNCHECKABLE; examples/bootstrap5 — UNCHECKABLE; missing — UNCHECKABLE; observed — UNCHECKABLE; project — UNCHECKABLE; repository — UNCHECKABLE; runner — UNCHECKABLE; session — UNCHECKABLE; tests — UNCHECKABLE; use — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:138
> <success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:139
> All listed truths and acceptance criteria have actual passing evidence; preserve nonparticipating output and policy. An unavailable external/browser/matrix check remains an explicit unmet gate, never a pass or silent deferral.

check — UNCHECKABLE; gate — UNCHECKABLE; matrix — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:140
> </success_criteria>

success_criteria — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:143
> ## Review Dispositions Ledger

Ledger — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:147
> ### Review Feedback Addressed

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:150
> | R12 — browser process/path cleanup | MEDIUM | Task01 owns server/temporary paths and finally cleanup across success/failure/interruption, including a deliberate failure-path check. |

check — UNCHECKABLE; failure — UNCHECKABLE; process — UNCHECKABLE; success — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:152
> ### Review Feedback Deferred

view — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:155
> | Stale installed example package | Rejected: existing Nox examples session installs .[all,test,examples] before running pytest; no skip-install is planned. |

all — UNCHECKABLE; before — UNCHECKABLE; examples — UNCHECKABLE; install — UNCHECKABLE; package — UNCHECKABLE; session — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:156
> | Missing companion dependency / excess workers | Already covered by Task02: final acceptance awaits07 receipt and bounded workers are last posargs. |

bounded — UNCHECKABLE; receipt — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:157
> | Runtime/browser availability or format_html floor assumed | Already covered by Task02 runtime/floor probes and Task01 actual browser gate; unavailable evidence remains unmet. |

format_html — UNCHECKABLE; gate — UNCHECKABLE; runtime — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:158
> | Transient settings would be committed | Rejected: settings artifact explicitly remains uncommitted, now removed by R12 cleanup. |

committed — UNCHECKABLE; now — UNCHECKABLE

## .planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:161
> Create `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-SUMMARY.md` with changes, exact verification results, source revisions and remaining limitations.

.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-SUMMARY.md — UNCHECKABLE; Create — UNCHECKABLE; SUMMARY.md — UNCHECKABLE; limitations — UNCHECKABLE; section — UNCHECKABLE; source — UNCHECKABLE
