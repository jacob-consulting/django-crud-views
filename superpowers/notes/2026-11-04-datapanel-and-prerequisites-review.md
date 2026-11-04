# DataPanel and prerequisites review — 2026-11-04

## Scope, sources, and verification boundary

This is a review, not an implementation or a replacement design. Findings distinguish reproduced behavior, source inspection, and unimplemented-plan risks. Recommendations identify decisions or acceptance criteria to settle; they do not imply that the proposed changes already exist.

Reviewed source snapshots:

- **Current tree:** branch `gsd/phase-06.10-object-derived-nested-urls-and-link-access-parity`. Review began at `7581bc0`; concurrent planning bookkeeping advanced HEAD through `9bab0a7` to `f2c271a5087eaea370c10bb4da305ae22f06c9e6`. Those later changes were review/state records. `git diff --name-only main...HEAD -- src tests docs` was empty. There is **no phase 06.10 implementation to certify**. Unrelated working-tree changes were left alone.
- **D:** [DataPanel design](https://github.com/jacob-consulting/django-crud-views/blob/8b5e8a294910143d40410d34574f55cdc196ebe1/superpowers/specs/2026-11-04-datapanel-design.md), fetched from `claude/lucid-knuth-x5ity9`. References such as “D:143” mean that document's line 143.
- **E:** [DataView exploration](https://github.com/jacob-consulting/django-crud-views/blob/8b5e8a294910143d40410d34574f55cdc196ebe1/superpowers/notes/2026-11-04-dataview-concept-exploration.md), on the same commit. The working name differs; these are the two requested documents.
- **N:** [Navigation exploration on main](https://github.com/jacob-consulting/django-crud-views/blob/716cd152df35da7199dfc5af39ccc75531c68559/superpowers/notes/2026-11-02-navigation-concept-exploration.md), especially §7 and §9, with §3.3 used to check the actual visibility matrix.
- **Issues:** [#311](https://github.com/jacob-consulting/django-crud-views/issues/311), updated `2026-11-04T12:10:38Z`, and [#312](https://github.com/jacob-consulting/django-crud-views/issues/312), updated `2026-11-04T12:01:02Z`, read using `gh issue view`.
- **P:** `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/` at reviewed commit `f2c271a5087eaea370c10bb4da305ae22f06c9e6`, now preserved in the [retired archive](../archive/2026-11-04-phase-06.10-object-derived-nested-urls-and-link-access-parity/README.md). References to `P/02:80`, for example, mean `06.10-02-PLAN.md:80`; `P/CONTEXT`, `P/RESEARCH`, and `P/VALIDATION` name the corresponding files. All six plans and the context, research, patterns, discussion, review, and validation artifacts were inspected.
- **T:** the downstream snapshot `../tabler-test` at `506ed89119feb57f70447f7ce57cd127012446b0`, read with `git show`. This is the design's cited roastery revision and the fetched `origin/main`. The sibling's actual checked-out `main` was the older `3315eef6671f502d859bba877322a5853388c508`, which lacks the roastery findings document. I did not switch its checkout. References prefixed `T/` refer to the fetched snapshot, not that older working tree.

`CLAUDE.md`, `AGENTS.md`, `docs/development/stability.md`, `docs/reference/theme.md`, and `docs/reference/nested.md` were read before the design. The relevant contract is selective: documented public names/attributes are protected; arbitrary internal methods and context shapes are not automatically protected (`stability.md:9–17,61–66`). Theme customization should use hooks before template overrides, and presentation does not replace request authorization (`theme.md:205–213,558–568`).

**Runtime used:** Python 3.12.3, Django 5.2.18, django-tables2 3.0.1, with imports bound to this repository's `src`. Full-suite and probe results are recorded below. Other Django versions, a browser, and downstream execution were not verified.

## Part 1 — DataPanel design

**Verdict: partly suitable, not ready for implementation planning.** Reusing a bound list/card view is grounded in the existing action and template machinery, and the non-goals keep the feature near the requested fixed-size dashboard lists (D:24–59; `src/crud_views/lib/views/card.py:46–104`; `src/crud_views/lib/table/table.py:15–34`). However, the proposed operations do not enforce fixed, unordered tables, several advertised instance overrides do nothing, and the visibility formula is not sufficient for Guardian or dispatch-dependent views. Those are reproduced failures, not objections to naming or style. The downstream widgets also require explicit decisions about their data scope, permissions, layouts, and limits before they can serve as acceptance examples.

### Ranked findings — verified

#### 1. High: the panel bypasses authorization that its visibility promise assumes

**What and where:** D:122–131 defines both panel and collection-link access using classmethods with `obj=None`. D:143–147 calls `setup()` and `get_queryset()` without dispatch. Guardian's list helper accepts anonymous users: `src/crud_views_guardian/lib/mixins.py:143–144` only rejects an authenticated inactive actor via `:14–21`. The request separately rejects anonymous users at `:131–139`, and nested dispatch enforces the parent at `:313–322,370–382`. Its queryset method at `:199–212` scopes child permissions, not the parent dispatch gate.

**Evidence:** P05 returned `True` for `GuardianBookListView.cv_has_access(AnonymousUser(), None)`. P15 gave a real authenticated user a child grant but no parent grant: list/detail link helpers returned `True`, while both client requests returned 403. P16 bound that nested list with its parent kwarg and called `get_queryset()` directly: the child row was returned and `cv_has_access(user, None)` remained `True`.

**Why it matters:** Calling this merely a presentation discrepancy misses that the panel itself renders data without the source view's dispatch. A host page's login check does not establish a source view's parent policy. Supplying an explicitly authorized queryset can be legitimate, but it must be a clearly separate responsibility. #312's chosen no-object fallback deliberately does not add this missing gate (`P/CONTEXT:55–60`; `P/03:80`). Navigation already acknowledges the distinction: N:269 explicitly adds authentication because the helper admits anonymous users, and N:270 checks the parent for child navigation.

**Recommendation:** Before planning, specify which source-view policies embedding executes, which policies an explicit queryset's caller owns, and how a known collection parent is checked. Require anonymous, inactive, child-granted/parent-denied, and custom dispatch-policy cases. Decide visibility before invoking source query construction that may perform work. Do not describe #312 as making the proposed `None` formula sufficient.

#### 2. High: the proposed table configuration neither disables all ordering nor guarantees the limit

**What and where:** D:143–149 slices the queryset, then calls `get_table(orderable=False, **get_table_kwargs())`. Existing `UUIDColumn` explicitly sets `orderable=True` (`src/crud_views/lib/table/columns.py:57–60`). In the installed django-tables2 implementation, `RequestConfig.configure` still reads the request's sort parameter (`django_tables2/config.py:42–44`), and table ordering filters by each bound column's orderability before calling data ordering (`django_tables2/tables.py:512–532`; `django_tables2/data.py:212–214`). Dependency paths here and below are under `.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/`.

**Evidence:** P01 constructed the repository's `AuthorListView` with exactly the proposed settings: no pagination, but `id` remained orderable. P02 added `?sort=id`; construction raised `TypeError: Cannot reorder a query once a slice has been taken.` P03 used `Author.objects.order_by("id")[:5]` without a sort query and raised the same error. P06 supplied `table_data` containing nine objects while `object_list` held two; the resulting table had nine rows. `SingleTableMixin.get_table_data()` prefers `table_data` to `object_list` (`django_tables2/views.py:122–129`). P07 used a valid `get_table_kwargs()` override containing `orderable`: the proposed call raised a duplicate-keyword `TypeError`.

**Why it matters:** These violate the central fixed-size/no-user-ordering intent, including ordinary registered table configurations. The downstream orders query already has a deliberate server-side order (`T/example/dashboard/views.py:58–64`). “Unordered” must mean no interactive reordering, not discarding the author's choice of which records are recent or urgent.

**Recommendation:** Define and test the final table data, ordering, request-parameter, pagination, and keyword precedence invariants. Include an explicitly orderable column, preordered sliced data, hostile/irrelevant dashboard sort parameters, `table_data`, and conflicting table kwargs. Preserve server-selected ordering. E:80–93's claim that the proposed settings are sufficient needs correction.

#### 3. High: `view_attrs` advertises overrides that existing classmethods ignore

**What and where:** D:160–162 explicitly offers `cv_list_actions_inline`, label modes, and analogous card options as instance overrides. List inline and label-mode resolution are classmethods (`src/crud_views/lib/view/base.py:329–341,360–395`); card inline resolution is also a classmethod (`src/crud_views/lib/views/card.py:106–109`). Card label mode has a special instance-aware branch at `:51–56`, illustrating that the behavior is not uniform.

**Evidence:** P04 assigned list inline `['detail']`, list label mode `{'detail': 'label'}`, and card inline `['detail']` to instances. The resolvers returned `None`, `"icon"`, and `None`, respectively. P11 showed that applying attributes after `setup()` also means a custom setup method sees the original values. Django's `as_view()` constructs `cls(**initkwargs)` before setup and rejects HTTP-method names as well as nonexistent attributes (`django/views/generic/base.py:82–105`). D:143 and D:160 describe a different lifecycle and weaker validation while saying “like as_view”.

**Why it matters:** A dashboard declaration can look correct, accept its configuration, and render a different action layout. This is precisely the kind of silent breakage the API is supposed to prevent.

**Recommendation:** Inventory which options are genuinely instance-aware before promising a generic attribute bag. Decide the contract for class-resolved options and setup-dependent options, and reject unsupported cases explicitly. Do not make “attribute exists” the only acceptance test. Avoid shared-class mutation as a workaround: two panels may require different settings in the same request (D:134–137).

#### 4. Medium: reusing a page content partial is not yet a durable embedding contract

**What and where:** D:54–59 forbids `get_context_data()` but D:206–218 includes `view.cv_content_template`. The stock card content works with the proposed small context: P08 rendered a card without pagination or ordering controls. However, the content partial also includes order and pagination fragments (`src/crud_views/templates/crud_views/view_card.content.html:1–17`), while full card context is normally assembled by `CardOrderMixin.get_context_data()` (`src/crud_views/lib/views/mixins.py:265–283`). Binding setup does not run arbitrary custom dispatch, `get`, or context contributions.

**Why it matters:** A future content template can legitimately require a context value supplied by its page's `get_context_data()`. A missing template variable can render blank rather than raise. The current stability policy does not establish the reduced context that DataPanel needs (`docs/development/stability.md:9–17`). This is a concrete dependency boundary, although a future regression has not happened and cannot be reported as a current failure.

**Recommendation:** State the supported source-view lifecycle and the minimum content-context contract, with compatibility tests shared by normal pages and panels. Mark incompatible source classes/templates clearly. Keep the prohibition on blindly calling the full page context if that remains the design choice, but document what reuse then excludes.

#### 5. Medium: the two downstream widgets are not drop-in demonstrations of the current proposal

**What and where:** The orders widget is customer-scoped and server-ordered, but its queryset is currently unsliced (`T/example/dashboard/views.py:32–35,58–70`); its template renders six specific columns and direct nested links (`T/example/dashboard/templates/dashboard/index.html:66–91`). The recent cuppings widget is a five-item list, gated by `roastery.view_greenlot`, with custom score/taster presentation (`T/example/dashboard/views.py:95–102`; its template `:92–113`). The existing `SessionListView` is a table view (`T/example/roastery/views.py:198–206`), not that compact card/list layout.

The Tabler table template already wraps the table in a hard-coded `.card.table-container` (`T/src/crud_views_tabler/templates/crud_views/table/bootstrap5.html:4–5`); D:193–209 adds another card frame. Tabler's card content has grid and column wrappers and its own empty-state text (`T/src/crud_views_tabler/templates/crud_views/view_card.content.html:1–20`). The card leaf also owns a card and footer (`T/src/crud_views_tabler/templates/crud_views/tags/card.html:12–20`). Five outer-frame class keys do not remove these inner wrappers.

**Why it matters:** Replacing the widgets can change the orders limit, the cupping gate, and both layouts. It is possible to configure dedicated subclasses/templates, but that is additional adoption work, not evidence that the existing two widgets are already covered. A parent-only project policy also exists in `CustomerGrantMixin.dispatch` (`T/example/sales/views/addresses.py:43–51`); the Guardian-specific prerequisite does not integrate that custom core mixin into link access.

**Recommendation:** Define acceptance for each actual widget: exact scope, chosen limit, permission rule, destination ViewSet, fields, and intended compact layout. Exercise the Tabler composition before promoting the provisional surface. Resolve wrapper composition through the existing hook-first theme policy where possible (`docs/reference/theme.md:205–213`), rather than counting a second frame template as complete theme adoption.

#### 6. Medium: action integration and the proposed tests use the wrong submission protocol

**What and where:** D:156–158 and D:289–293 refer to matching `form=` targets. Current action buttons use `data-cv-action="submit-form"` and `data-cv-target`, not a native `form` attribute (`src/crud_views/templates/crud_views/tags/button/action.html:4`; `src/crud_views/lib/view/button_data.py:200`). The delegated handler finds the target form by ID (`src/crud_views/static/crud_views/js/viewset.js:15–27`). Host pages must install the CSS/JS/config integration, including the modal shell (`docs/reference/templates.md:11–25`).

**Evidence:** P22 rendered a stock card POST action with a request: CSRF and a hidden form ID were present, but `form=` was not. P19 also showed that a bare RequestFactory request with only `user` is insufficient for action labels: `ViewContext.router_name` accesses `request.resolver_match.url_name` (`src/crud_views/lib/view/context.py:47–49`) and raised when resolver information was absent.

**Why it matters:** The proposed test can assert a nonexistent convention or miss the actual duplicate-ID bug. A non-crud page that renders the HTML without the package's client-side setup cannot be assumed to have working POST/modal controls. The downstream crud page explicitly supplies that setup (`T/src/crud_views_tabler/templates/crud_views_tabler/page.html:5,15–17`); the dashboard uses a different host template.

**Recommendation:** Test actual `data-cv-target` to hidden-form pairing, two panels with overlapping records, CSRF, and a real POST/modal interaction on a non-crud host. Document host assets/config requirements. Define uniqueness expectations for caller-supplied IDs and independently fetched fragments before claiming the lazy-load path is settled. Give RequestFactory tests resolved-request context or test through a real URL.

#### 7. Low: the shown frame does not compile as written

**What and where:** D:193 loads only `crud_views`, then D:198 uses `{% translate %}`. P13 compiled this combination and got `TemplateSyntaxError` because `i18n` was not loaded.

**Recommendation:** Correct the sketch and include template compilation/rendering in acceptance. This is small, but directly verified.

### Answers to the design questions

| Question | Verdict | Evidence and limit |
|---|---|---|
| 1. Solves the stated intent and stays within it? | **Partly.** | The selected reuse and non-goals fit (D:24–59), but table invariants and policy inheritance fail in findings 1–3. Generic `view_attrs` broadens the supported surface beyond what its current resolution machinery can honor. |
| 2. Durable against plausible list/card changes? | **Partly.** | Existing view methods provide useful reuse, but setup order, page-content context, table data selection, and class-vs-instance configuration are uncontracted seams; see the dependency table below. |
| 3. Useful for navigation and downstream work? | **Partly.** | The request-free URL helper is useful to both; DataPanel itself remains request-bound. N:269–270 has stronger Guardian visibility conditions than D:124. Registered widgets provide an endpoint shape for later lazy loading, but equivalence between embedded and dispatched behavior is unverified. Downstream adoption requires finding 5's decisions. |
| 4. Easy to understand at the dashboard call site? | **Partly.** | `from_viewset`, explicit data, limit, title, and action suppression are traceable. `view_attrs` is misleading today; registry lookup hides which class/template/policy runs; `setup` without dispatch and delayed table construction require an explicit lifecycle description (D:113–149). |
| 5. Decisions justified? | **Partly.** | Individual dispositions follow. There are both maintainer decisions to retain and unapproved behavior choices requiring correction or explicit acceptance. |
| 6. Claims verified against code? | **Partly.** | Twenty-two probes and the full suite were run. They verify current operations, not a nonexistent DataPanel implementation. The probe table distinguishes positive and negative results. |
| 7. Ready to plan unchanged? | **No.** | Settle authorization, table invariants, and configuration semantics first, then the downstream rendering contract and accurate integration tests. |

### Durability and hidden-coupling inventory

| Dependency | Verified behavior now | Plausible failure boundary / required contract |
|---|---|---|
| `View.setup` binding | Supplies request/args/kwargs; normal Django construction applies initkwargs first (`django/views/generic/base.py:54–62,82–105,126–132`; P11). | Custom initialization/dispatch prerequisites are skipped. Specify supported lifecycle, not “any list view”. |
| `paginate_by`, `table_pagination` | The proposed settings removed table pagination in P01. | Overrides of table construction/pagination can supersede them. Verify resulting table, not just attribute values (`django_tables2/views.py:21–36,111–129`). |
| `cv_order_fields` | Card order choices are controlled by this whitelist; `cv_order_default` is separate (`src/crud_views/lib/views/mixins.py:168–169,206–231`). | Suppressing the chooser is different from removing server order. Keep a documented distinction. |
| `cv_content_template` | Stock card fragment rendered with minimal context (P08). | Theme or application fragments may require page context. Shared embedding-context tests are needed; arbitrary partial compatibility is unverified. |
| `get_table_kwargs` / `get_table` | Current mixin forwards `view`; dependency gets data independently (`mixins.py:298–299`; `django_tables2/views.py:111–129`). | Duplicate keywords, alternate `table_data`, explicit column ordering already break the sketch (P02–P07). |
| `cv_get_oid` | Current ID uses ViewSet, action, and normalized PK (`src/crud_views/lib/view/base.py:698–705`). | Prefixing addresses overlapping panels only if all form/target paths consume it and caller IDs are unique. Browser behavior and future fragment allocation remain unverified. |
| Instance `cv_link_origin` | Proposed, not implemented. Current row/card action code delegates to the view's link builder (`base.py:958–976`; `views/card.py:77`). | Test every action path and preserve normal-page defaults. Custom URL overrides remain their author's responsibility. |
| Registry-based scratch subclass | Inheriting `cv_viewset` without redeclaring it does not replace registration (`src/crud_views/lib/view/meta.py:15–28`; P12). | Do not accidentally redeclare registration metadata. Explain the difference from an explicitly registered `widget_recent` source. |

### Decisions section — each call challenged

These are dispositions against stated requirements, rather than claims of implementation. “Needs a decision” identifies behavior for which the supplied maintainer decisions do not establish acceptance.

| Call in D:321–335 | Disposition | Basis |
|---|---|---|
| Maintainer 1: A now, C lazy later | **Keep, with an explicit embedding contract.** | Existing row/card methods carry the behavior B would duplicate (`views/card.py:46–104`; E:291–326). A skips dispatch and C runs it, so “same class” does not establish equivalent authorization; finding 1 must be resolved. |
| Maintainer 2: post-1.0, four preconditions, provisional | **Keep.** | Consistent with N:553 and current pending Phase 7 (`.planning/ROADMAP.md:38`). Do not treat #312 as an unconditional access certificate. The provisional tier is a prerequisite, not present policy text today. |
| Maintainer 3: `DataPanel` naming/module/tags | **Keep.** | Consistent across D:91,175–186,327; no functional contradiction found. Naming preference alone is not a finding. |
| Maintainer 4: no access renders nothing | **Keep.** | Fits the declared presentation contract (D:167–168). Require the predicate to represent the intended policy before data preparation/rendering; finding 1. |
| “All” points to registered list/card and defaults on | **Needs a decision for cross-parent panels.** | D:128–132 returns no link for nested sources without parent kwargs. Both motivating widgets are cross-parent, and downstream has a distinct top-level orders ViewSet (`T/example/sales/views/orders.py:38–49,203–216`). Decide whether absence is accepted or an explicit destination is required; do not infer one. |
| No origin on widget links | **Keep.** | D:170–173 deliberately selects static cancel/success behavior on a non-crud page. This is coherent with origin machinery being view-based (`base.py:939–976`), but document the resulting return destination rather than implying a dashboard round trip. |
| Per-widget OID prefix and automatic request counter | **Keep for initial full-page rendering; needs a lazy-fragment decision.** | Current IDs collide for the same action/object in two panels (`base.py:698–705`). Per-request counters alone do not establish uniqueness across separate fetch requests. Test the actual JS target protocol, finding 6. |
| `empty_text` in both modes | **Keep.** | A shared option should affect both modes. D:151–154 acknowledges the Tabler override must also change; verify that follow-up before claiming cross-theme behavior. |
| `view_attrs` validated “like as_view” | **Change.** | P04/P11 demonstrate ignored settings and different setup semantics. The supported option set and resolution behavior must be defined, not inferred from `hasattr`. |
| Frame title uses `level=3` | **Needs a decision about embedding hierarchy.** | The feature is for arbitrary non-crud pages. Existing heading configuration is documented in `docs/reference/templates.md:27–57`; the downstream card leaf already requests `level=3` through the configurable heading tag (`T/src/crud_views_tabler/templates/crud_views/tags/card.html:9–14`). The supplied material does not establish a universal host heading level. |
| Five class keys, Bootstrap card defaults | **Keep the hooks; change the assumption that they settle composition.** | Fits theme registration, but existing Tabler fragments own inner cards/grids (finding 5). Require a rendered composition decision before freezing the leaf. |
| `row_actions=False` removes action column / clears card actions | **Keep with defined precedence.** | Useful and consistent with the standard `actions` column (`table/table.py:28`). P18 confirmed explicit exclusion did not resurrect a `Meta.exclude` column. Still specify how caller `get_table_kwargs()['exclude']` combines with suppression and what happens for nonstandard action columns; those combinations were not verified. |

### What to change before planning, ranked

1. **Resolve access and data ownership** for bound views, explicit querysets, known parents, anonymous Guardian users, and custom dispatch policies. Reconcile D:124 with N:269–270 and D-09/D-10. This is finding 1, not a request to invent general core parent authorization.
2. **Replace assumed table controls with observable invariants** and regression cases covering the failures in finding 2.
3. **Make per-panel configuration truthful:** settle class-resolved settings, initialization timing, and the supported override set (finding 3).
4. **Establish the actual downstream acceptance cases and embedding-context/theme boundary** (findings 4–5). Decide whether both original layouts and their current permissions must be preserved.
5. **Correct action integration tests and host requirements**, then the minor template error (findings 6–7). Retain the provisional status until core and Tabler have both rendered the feature.

### Verified versus could not verify

Verified: the existing source mechanisms, the listed runtime failures and successes, and the downstream snapshot's code. Could not verify: an implemented DataPanel, future dependency compatibility, a working lazy-load endpoint, browser submission/ID isolation, rendered Tabler appearance, or the claimed “same queries as list minus pagination” budget. D:296–297 states that budget before the skipped dispatch/context work and new access policy have been measured; it should be an experiment with a fixed workload, not an assumed equality.

## Part 2 — Prerequisites #311 and #312

**Verdict: both issues identify real defects, but their universal claims and one downstream acceptance criterion are too broad.** Object-derived URLs are useful for the stated cross-parent actions; missing permission declarations and Guardian parent-blind link checks are reproduced. The issues do not establish universal link/request parity: some columns never call access helpers, no-object/unresolved fallbacks remain permissive, state can use the wrong object, and arbitrary project dispatch policies remain outside the helper. The phase correctly makes several routing choices more precise. Its integration order is sensible, but not every permission fix technically depends on every URL-builder change.

### Ranked findings — verified

#### 1. High: “everywhere links” and “then build on cv_has_access without exceptions” are not true

**Where:** #312 Summary and Acceptance; N:577–590; `src/crud_views/lib/table/columns.py:28–50`; `src/crud_views/templates/crud_views/columns/child.html:3`; `docs/reference/card-list-view.md:147–150`.

**What:** `LinkChildColumn` constructs a URL and renders an anchor without an access check. `LinkDetailColumnMixin` supplies a URL without the action permission pipeline. The current docs explicitly acknowledge the child-column exception. Guardian's no-object helper also admits anonymous users, and the proposed D-09/D-10 fallbacks intentionally leave some displayed links leading to 403 (`P/CONTEXT:55–60`).

**Why it matters:** A consumer reusing ordinary table columns cannot infer the same presentation guarantee as an action button. DataPanel's proposed panel-level `None` call is exactly a fallback call, not evidence that a source page was dispatched.

**Recommendation:** Bound the issues' acceptance to the paths and resolvable cases actually changed, and list the column/fallback/custom-policy exceptions. If universal visibility parity is required, those exceptions need separate work and tests. The request gate must remain authoritative regardless (`theme.md:558–568`).

#### 2. Medium: #311 does not by itself close downstream finding 27

**Where:** #311 Acceptance, final downstream bullet; T finding 27 at `docs/crud_views_upstream_findings_roastery.md:428–438`; `T/example/sales/views/orders.py:92–102,219–234`.

**What:** The problem is not only missing parent kwargs. The top-level `orders` ViewSet has no detail view, and the desired editor belongs to another ViewSet. A request-free helper can replace the manual `reverse` inside the custom renderer/redirect, but it does not add a column target ViewSet or a cross-ViewSet success target. #311's Related section itself calls the proposed `LinkColumn(viewset=..., key=...)` a follow-up.

**Why it matters:** Deleting both overrides after implementing only the issue's helper/builders would remove the application-specific destination selection, not preserve it.

**Recommendation:** Change acceptance to “simplifies these overrides” unless explicit cross-ViewSet targeting is added in separately agreed scope. Do not close finding 27 on the helper alone. A panel using the nested source class with a scoped cross-parent queryset is a different use case from reconfiguring the existing top-level ViewSet.

#### 3. Medium: the issue contains conflicting precedence instructions and an inaccurate M2M baseline

**Where:** #311 Proposed change §2 says explicit kwargs → page kwargs → object; §3 recommends object-over-page for object targets. Its M2M recommendation/acceptance says the delete preview already returns `None`.

**Evidence:** `DeleteView.cv_get_related_object_url` at `src/crud_views/lib/views/delete.py:192–210` dereferences `getattr(obj, parent_attr).pk` and catches only `NoReverseMatch`. P17 temporarily registered a detail view for the existing M2M Genre fixture and got `AttributeError: 'ManyRelatedManager' object has no attribute 'pk'`. The ordinary fixture's missing detail candidate is not proof that the M2M relation is safely handled. Existing view builders can use supplied page coordinates without deriving a unique M2M parent (`base.py:598–604`).

**Recommendation:** Use the phase's explicit precedence and scoped-M2M decisions as the authoritative resolution, and describe safe optional M2M handling as a fix where applicable, not preserved behavior for every existing candidate.

#### 4. Medium: the issues' parent-permission fix does not settle parent-state parity

**Where:** #312 Gap 2 proposed composition; `src/crud_views_guardian/lib/mixins.py:375–382`; `src/crud_views/lib/view/base.py:414–433`; P20.

**What:** The request checks `cv_action_enabled(user, parent)` for any nested non-object Guardian view. Rendering a list action from a child detail passes the child to the default state adapter. With all required grants present, a state hook allowing a Book but denying its Publisher produced an enabled link and a 403 request. This is not a missing permission grant.

**Recommendation:** Include state-object parity in the acceptance boundary, or explicitly narrow the promise to permission parity. The DataPanel formula and the navigation matrix both include state, so leaving this implicit transfers the mismatch to those consumers. Part 3 identifies the corresponding plan gap.

### Line-reference and “behavior today” audit

The issue references are pinned to `cf2bfc0`; the following checks are against the current source tree. “Matches” means the cited implementation supports the described behavior, not that all surrounding generalizations are valid.

| Issue reference / claim | Current check |
|---|---|
| #311 `base.py:576–609`, parent loop `598–603` | Matches. Page kwargs supply parents and falsey values raise. The loop currently reaches line 604. |
| #311 `cv_get_url:611`, `cv_get_link_url:958` | Matches delegation. Link URL also has origin behavior at `958–976`; do not bypass it while replacing URL resolution. |
| #311 child URL `985–1005`; parent object `1023–1035` | Matches: immediate child parent from `obj.pk`, higher levels from kwargs; page parent lookup remains kwargs-based. |
| #311 ViewSet walks `236–252`, `263–279`, `281–305` | Matches the chain logic. `get_queryset` continues through ordering and return at line 316; the issue's `view.kwargs[pk_name]` line 301 is correct. |
| #311 three-level fixtures `views.py:968ff` | Matches: publisher at 968, book at 1018, booknote at 1034. |
| #311 delete precedent `delete.py:186–204` | Shifted: method is `192–210`. One-level derivation and `NoReverseMatch` catch match; universal M2M-to-None claim does not (P17). |
| #311 Guardian create resolver `views.py:275–296` | Matches own-child/direct-parent handling and M2M rejection. Its broad missing-relation catch is one reason to distinguish native absence from custom errors in the shared resolver. |
| #311 callers: buttons 229, columns 42, card 57–58 | Matches URL delegation. This does not mean the column also delegates permission checking. |
| #311 M2M declaration `parentviewset.py:19`, fixture `views.py:457` | Matches ambiguity. Explicitly scoped M2M links are possible; “cannot derive one parent” is narrower than “cannot build a URL”. |
| #311 sibling button `buttons.py:287` | Matches intentional page-scoped coordinates; access is called with `None` at 301. |
| #311 Guardian dispatch `313–322,370–383` | Parent gate matches, after authentication/inactivity handling. A `None` permission key does not skip parent resolution or the non-object state check. |
| #311 core child permission `base.py:1072`; scope/queryset; create/redirect | Matches absence of a built-in parent permission policy. P14 got list/detail 200 with `view_book` but no `view_publisher`. A wrong-parent object lookup is scoped to 404. Do not infer that every collection request independently establishes parent existence: an empty filtered queryset is not a parent lookup. |
| #311 “cv_get_url is a listed public name in stability.md” | Not literally correct: that method name does not occur in the current file. `CrudView`/documented attributes are covered at `stability.md:26–27,61–66`; the issue should cite the actual documented contract rather than claim an explicit listing. |
| #311 Resource leaf rule / raw FK shortcut | Resource leaf validation exists at `src/crud_views/lib/viewset/__init__.py:216–225`; explicit context is necessary because Resource rows have no declared ORM relation chain. The proposed `attr_id` shortcut requires Django metadata for `to_field` and registered-model PK semantics; the phase research addresses this (`P/RESEARCH:259–268`). |
| #312 missing core tuple `base.py:1084–1089` | Matches. P09 returned True for anonymous with an undeclared key. This is the default backend behavior; arbitrary user/backend overrides were not tested. |
| #312 request assertion `base.py:1061–1070` | Matches; P10 raised the stated assertion. Normal exception handling makes this a server error rather than permission denial. |
| #312 empty permission cache `viewset/__init__.py:437–470` | Matches retry-while-empty behavior. Existing regression starts at `tests/test1/test_viewset.py:77`; full suite passed. A partially populated positive cache is not the same case, so avoid a broader “every new permission appears without restart” claim. |
| #312 Resource E260 `viewset/__init__.py:194–206` | The check is in the cited area (`191–205` currently). It validates configured Resource permission keys, unlike database permission-row availability. |
| #312 `_cv_get_action_context` `base.py:720–730` | Stale range: that helper is now `735–780`; access is at 772. The old range is within `cv_get_context`. |
| #312 Context/Parent/Child/Sibling button ranges | Match the intended paths: `buttons.py:109–118,174–192,237–243,296–302`. Card action range `card.py:59–93` also reaches the relevant checks. |
| #312 template filter `crud_views.py:467–473` | Stale: `cv_context_has_permission` is currently `602–607`. It calls the class helper with no instance binding. |
| #312 disable policy `visibility.py:14–20` | Matches permission/state presentation behavior. It does not add authorization to columns that never enter this pipeline. |
| #312 Guardian missing `.split` rows `mixins.py:62–72,85–97,368` | Real reachable AttributeError paths. Not unconditional: inactive checks, global-permission shortcuts, or object=None can return first. The phase appropriately specifies declaration-check ordering. Guardian list queryset permission handling at `199–212` also needs consideration beyond the issue's three sites. |
| #312 Guardian parent keys `mixins.py:333–342`, `viewset.py:38–39` | Matches create-specific key versus ordinary key and the default view policy. |
| #312 list helper `143–144`, object helper `85–97` | Parent omission matches. “Signed-in, active” is inaccurate for list `cv_has_access`; P05 and N:269 establish the anonymous exception. |
| #312 create `views.py:310–360`, resolver `275–296` | The cited range covers helpers and the beginning of access; current create `cv_has_access` continues through line 387. It is a special class-defined override, so a mixin-only change does not cover it. |
| #312 parent mixin “first in MRO of every composition” | Operationally ahead of the permission mixin, but literally false for delete: `GuardianDeleteRelatedObjectsMixin` precedes it (`views.py:230–234`). That preceding mixin does not supply the access override at issue. |
| #312 default fixture `views.py:711–717`; conftest `608–660` | Matches the listed ViewSets, users, parent/child fixtures and parent permission defaults. These defaults explain why that scenario can conceal the gap; historical reasons individual tests were omitted cannot be proven from them. |
| #312 docs Guardian heading `guardian.md:186`; stability `82–85` | Both current references match. New helper is not yet implemented/listed. |
| #312 AUTH IDs / next inserted phase bookkeeping | Historical proposal is stale: AUTH-08/09 now exist at `.planning/REQUIREMENTS.md:211–212`; Phase 6.10 is pending at `.planning/ROADMAP.md:37`. Phase 6.9 is already inserted/completed at line 36. |
| #312 query-cost assertion | Additional parent checks follow from the proposed algorithm, but “one or two queries per card” is a prediction, not a measurement made here. Grant/checker/backend conditions matter; the phase now requires numeric workload-specific measurements. |

### Are the proposed changes right, and what are the alternatives?

**#311: partly.** A public request-free URL entry point is directly useful when a row's parent differs from the hosting page. Deriving the actual parent for object destinations prevents the wrong-parent URL produced by page-first precedence (`base.py:598–604`; `P/CONTEXT:28–36`). A resolver cannot turn M2M ambiguity into a unique answer, nor can resolving a URL establish permission. D-05/D-08 state those limits correctly.

The screenshot supplied during this review asks whether the real decision is introducing object-to-URL resolution and then using it almost everywhere, despite traversal complexity and possible 403s. **Yes, those are two separable choices, with a third choice about availability checks.** The helper is request-free only when enough object or explicit parent context exists. The integration becomes more complex because existing collection links deliberately preserve page scope while custom hooks still receive their established objects (`P/02:74–82`). A generated URL and an access verdict should remain distinct outputs/responsibilities.

| Alternative | What it buys | What remains / evidence |
|---|---|---|
| Explicit destination ViewSet and parent kwargs at each caller | No inferred ancestry; the caller makes scope visible. | Repeats routing knowledge in dashboards, as the existing downstream overrides do (`T/example/sales/views/orders.py:92–102,219–234`). Explicit coordinates still do not authorize the destination. |
| Add an opt-in object URL helper first; migrate existing builders separately | Smaller immediate compatibility surface; new consumers can use request-free resolution. | Existing reused row actions still call current builders and would not automatically benefit (`base.py:761`; `views/card.py:77`). DataPanel would need an explicit adaptation step or a narrower first release. This is a scope alternative, not a complete drop-in solution. |
| Current integrated shared resolver plus rendering adapters | Existing action paths gain correct object URLs, and permission checks can use the destination actually selected. | Requires precise precedence, metadata handling, custom-hook compatibility, and scoped context tests (`P/01:83–108`; `P/02:72–86`). It cannot promise all generated links are usable. |
| Separate pure URL resolution from an explicit destination-availability operation | Makes callers choose whether they need a route or a checked presentation decision; can pass known parent evidence explicitly. | Public `cv_has_access(user, obj)` overrides still need compatibility if existing actions are migrated. Plan 02 explains why a purely explicit adapter alone does not preserve every cooperative hook (`:74,152`). No replacement implementation was tested. |
| Registered widget endpoints / Approach C | Runs the normal request lifecycle and offers a concrete later fetch endpoint (E:328–362; D:220–251). | Does not solve cross-parent row URLs or automatically supply the compact dashboard layout. Embedded A and fetched C still need equivalent data/policy behavior. |
| Independent renderer / Approach B | Owns its lifecycle without synthesizing a page view. | Must reproduce the existing view action/configuration behavior that E:291–326 identifies. The reviewed code confirms those behaviors are distributed across view/card/button methods. |

**#312: partly.** Denying an undeclared permission on the presentation side while keeping the request loud is the right targeted correction to the empty-tuple bug. Promoting the existing parent policy and reusing one relation-resolution model avoids separate create/list interpretations. However, a dictionary of PKs is not itself the permission-checkable parent object: the resolver also needs relation identity/database evidence or must load the parent (`P/03:82–84`). Keeping a legacy forwarding seam is justified by the existing overridable private entry points; the phase makes this more precise than the issue (`P/03:68`).

The dismissed fail-closed alternative for unresolved M2M access would hide otherwise valid, page-scoped controls; the phase therefore preserves the fallback. That is a compatibility decision, not proof of access. Conversely, declining to check **known** parent evidence merely because a caller supplies `obj=None` is unsuitable as DataPanel's safety argument. Preserve a legacy callable fallback if needed, but require new embedded callers to make the parent-policy decision explicitly.

### Are they prerequisites, and in that order?

| Claim | Verdict | Evidence |
|---|---|---|
| #311 is needed for the full proposed cross-parent reuse | **Yes.** | Existing nested row builders need page parent kwargs; D:307–308 and `base.py:598–604` establish the failure. A root-only or hand-adapted panel could ship without it, but would not satisfy the chosen nested-row acceptance. |
| #312 is needed before expanding the existing visibility promise | **Yes, but insufficient.** | P09/P15 reproduce defects the panel would inherit. P05/P16/P20 and column exceptions remain outside that fix's stated fallback behavior. A tightly scoped panel could reproduce today's behavior without #312, but should not advertise the stronger contract. |
| Helper → #311 builders → #312 is a necessary total dependency order | **Partly.** | Shared resolution should precede destination-aware Guardian integration. Missing core declarations do not depend on URL resolution. A parent-object helper can be tested before every builder is migrated. The combined order is practical for integration testing, not an intrinsic dependency of all #312 changes. |
| Request-free navigation is helped | **Yes.** | N:74–84 identifies missing parent context as a structural constraint. The helper addresses URLs; it does not make labels/actions request-free (`src/crud_views/lib/view/context.py:16,47–49`; N:86–106), which D:39–48 appropriately excludes. |

### Core parent-permission note

**Accuracy: partly.** The central statement is correct: core nesting supplies scope, not a built-in parent permission policy. P14 verified a child list and detail request succeeding without the parent model permission; `CreateViewParentMixin` sets a parent rather than authorizing it (`src/crud_views/lib/views/create.py:84–110`), and `RedirectChildView` adds no parent authorization (`views/child.py:12–28`). However, “only existence and the child's permission are checked” overstates universal parent-existence checking for collection queries, and “offers no hook” should mean no dedicated declarative parent policy, not no way to extend dispatch/access at all—the downstream mixin itself demonstrates extension.

**Scope decision: keep the general core-policy redesign out of #311.** A URL derivation change does not require choosing a new default parent permission for every core ViewSet. Core link/request agreement can consistently mean both ignore parent permission. **DataPanel still depends on an explicit embedding-policy boundary:** Guardian's existing parent gate and a project's existing custom dispatch gate cannot be silently skipped while claiming to reuse those views' permissions. Resolving that boundary does not require imposing a new universal core parent policy. Document the current core contract, and ensure any later opt-in policy supplies both request and presentation behavior.

### Verified versus could not verify

Verified: both central defects, relevant callers and source references, M2M delete behavior with a registered candidate, core parent scope, and downstream cross-ViewSet requirements. Could not verify: historical reasons for missing tests, the eventual helper's database/query costs, universal behavior of custom authentication backends, or closure of downstream finding 27. Neither issue is implemented in this tree.

## Part 3 — Phase 06.10 artifacts

**Verdict: substantially aligned and more precise than the issues, but incomplete and still carrying a state-parity hole.** The six plans turn contradictory issue shorthand into explicit precedence, typed failure handling, metadata-aware resolution, migration guidance, and measured-query acceptance. Those are improvements. They have not been executed: validation is draft and every task is pending (`P/VALIDATION:4–6,26`), no implementation diff exists, and the new test modules are absent. The existing full suite passes, which establishes a baseline only. The remaining findings below concern the plan contract, not bugs in code that has yet to be written.

### Ranked findings

#### 1. High, verified baseline and plan gap: non-create collection state still uses the wrong object

**Where:** `P/02:66,80,117–121`; `P/03:86`; current `src/crud_views_guardian/lib/mixins.py:375–382` and `src/crud_views/lib/view/base.py:426–433`; probe P20.

**What:** The plan makes nested create the explicit parent-state exception while preserving the established object for other state hooks. Current request enforcement uses the parent for every nested non-object view, including list/card. With parent and child permissions granted, a list link from a Book detail was enabled using the Book, then the same destination returned 403 using the Publisher. Fixing only the create adapter does not cover that case.

**Why it matters:** The plan can satisfy its opposite-grant tests while still violating the state portion of visibility. Preserving the original access/label-hook object is not a reason to feed the wrong semantic object to the separate state check.

**Recommendation:** Specify destination state-object selection for all non-object nested targets. Add paired rendered-link/direct-request tests with all permissions granted and opposite parent/child states, including page A/row B, list/card, parent buttons, and no-object paths. Preserve public access/label hook contracts separately. This extends the existing state correction rather than adding a new parent permission policy.

#### 2. Medium, verified plan limitation: the no-object fallback must not be inherited as a new consumer's access guarantee

**Where:** `P/CONTEXT:55–60`; `P/02:82`; `P/03:76–80`; `.planning/REQUIREMENTS.md:212`; D:124,309–310.

**What:** The phase explicitly checks `obj=None` before even consulting matching destination evidence, and retains current anonymous semantics. That is a more limited contract than #312's final acceptance paragraph and DataPanel's prerequisite claim.

**Why it matters:** This is not an accidental undocumented hole—the phase correctly records it—but a downstream design can still misread “#312 merged” as evidence the arbitrary embedded source has passed its parent/authentication gates. P05/P16 establish why that inference fails.

**Recommendation:** Carry this limitation into the DataPanel and navigation handoff, and require a known-parent path for new embedded callers. Do not label D-10's legacy fallback a destination-availability result. If the broader promise is retained, D-10 needs revisiting for renderers with explicit destination evidence.

#### 3. Medium, demonstrated primitive but unimplemented risk: copied context can outlive its scope on the same execution owner

**Where:** `P/02:64–78,114,124–128`; `P/03:88`.

**What:** The proposed carrier uses immutable ContextVar frames, token reset in `finally`, and target/user/object/thread/task matching. Those checks address different-owner inheritance and ordinary nesting. They do not by themselves invalidate a `copy_context()` captured inside a scope and run later on the same thread/task. P21 copied a ContextVar, reset the original token, then ran the copy on the same thread: the old value remained visible. Plan 03 also uses matching carrier ownership to avoid repeating the mandatory certified parent gate.

**Why it matters:** A same-owner copied frame can contain stale destination/ownership evidence after the producer scope has ended. This is a plan-level risk, **not a demonstrated authorization bypass in phase code**, since that code does not exist. The current test list specifically calls out threads and separate tasks, but not delayed same-owner copied contexts; its “no context survives its owner scope” criterion is broader than the proposed mechanics establish.

**Recommendation:** Add that exact delayed-copy case. Define independently checked scope liveness/invalidation, or explicitly constrain and document the supported context lifetime. Verify both resolver evidence and certified gate ownership cannot be consumed after scope exit. Do not assume immutable values plus token reset solve copied-context lifetime.

#### 4. Low, verified documentation omission: a reference page will retain contradictory Guardian guidance

**Where:** `docs/reference/card-list-view.md:144–150`; `P/05:7–15,93–95`.

**What:** The card reference says a Guardian child list's helper is always True and its buttons continue rendering because the parent is checked only on request. The planned documentation files omit this page. After the parent-access fix, that description becomes directly inconsistent with the new resolvable-parent behavior; “always” already overlooks inactive actors today.

**Recommendation:** Update the card reference with the same resolved-parent/fallback distinction as the Guardian and context-button references. Retain the separate, still-true warning about `LinkChildColumn` unless column visibility is separately changed.

### Deviations from the issues

The following are substantive contract or scope deviations found in the reviewed plans; implementation-level differences cannot be enumerated before code exists.

| Phase choice | Classification | Evidence / consequence |
|---|---|---|
| Object ancestry beats implicit page scope; explicit conflicting parent raises | **Improvement.** | Resolves #311's contradictory precedence instructions (`P/CONTEXT:D-01,D-02`; `P/RESEARCH:232–255`). Prevents silently constructing a wrong object destination. |
| Collection page scope wins, but object derivation is allowed when page scope is absent | **Improvement.** | D-03/D-04 distinguish collection navigation from object destinations, beyond the issue's “kwargs only” shorthand. |
| Scoped M2M URLs allowed; no automatic membership lookup | **Improvement.** | D-05/D-08 preserve existing scoped navigation while refusing to guess a unique relation. Requests/certified previews retain responsibility for validation. |
| Null single-parent relations cannot be replaced with an invented page parent | **Improvement.** | D-06 makes unavailable object destinations distinct from valid explicit collection scope. |
| Resource rows accept complete explicit/page context and remain leaves | **Clarification/improvement.** | D-07 and `P/01:83–106`; the issue's proposed first helper signature did not expose all required inputs. |
| Public signatures gain `obj=None`, explicit parent/kwargs and optional strict behavior | **Improvement in completeness; larger contract to document.** | `P/01:72–106`; the issue proposed a narrower `get_parent_pks(obj)` plus an optional `strict=False` possibility. |
| Metadata, registered identity, `to_field`, database context, native absence versus custom errors | **Improvement.** | `P/RESEARCH:259–268`; `P/01:83–108`. A raw `attr_id` heuristic and broad catches are not sufficient for these cases. |
| Private destination context and rendering adapters | **Added implementation scope, justified but risk-bearing.** | `P/02:64–82` preserves object arguments while selecting a different collection parent. It introduces the lifetime concern above; it is not necessary merely to offer an opt-in pure helper. |
| Create internals are adapted and the old queryset post-render correction consolidated | **Improvement over literal “untouched”, provided behavior is preserved.** | #312 asks to keep create untouched; `P/03:71,86` recognizes its class override bypasses ordinary cooperative composition. Explicit hook-count and request tests are necessary. |
| Private parent method forwards to the public rule; internal callers retain the private seam | **Improvement.** | `P/03:68` specifies compatibility for old private overrides and new public overrides without recursion; “private alias” in the issue was underspecified. |
| Declaration checks expanded to effective Guardian request/list/create paths, with actor-specific ordering | **Improvement.** | `P/03:69,76–78,103`; the issue concentrated on `.split` sites. Nested create's parent-only policy must not become a new child-add requirement. |
| Explicitly permits some displayed-link 403s and changes AUTH-09 wording | **Loss relative to the universal headline; faithful to the issue's own fallback decisions.** | D-09/D-10 and `.planning/REQUIREMENTS.md:212`. Honest limitation is preferable to an untrue parity claim; new consumers must account for it. |
| Protected preview keeps first-candidate selection and independent exact-destination certification | **Improvement/preservation.** | `P/04:67–83`; replacing the old URL method alone must not remove the existing protected-preview gate. |
| Breaking entry plus executable migration, not only Changed | **Improvement.** | D-16; `P/05:80–87`. Object precedence and invalid explicit override behavior are observable compatibility changes. Matches repository migration convention. |
| Exact query baselines, workload deltas, import/context tests, executable documentation | **Improvement.** | `P/01:108`; `P/02:86`; `P/03:84`; `P/04:104`; `P/05:69–74`. These are planned requirements, not measured successes. |
| Public handoff in stability.md, final tier classification deferred to Phase 7 | **Neutral sequencing choice.** | `P/05:71,108`; current Phase 7 remains pending. Canonical documentation is required, so this is not a summary-only API handoff. |
| No downstream cross-ViewSet column/success-target implementation | **Appropriate scope limit, but loses #311's claimed closure.** | The phase's listed source work does not add those features; finding 27 must remain open or be narrowed. |

### D-nn decision review

| Decision | Disposition | Reason grounded in the reviewed contract |
|---|---|---|
| D-01 | **Keep.** | An object target must use that object's actual ancestry; current page-only lookup is the cross-parent failure (`base.py:598–604`). |
| D-02 | **Keep.** | Explicit contradiction is a caller error; silently discarding it hides routing mistakes. The plan distinguishes implicit page context from explicit overrides (`P/RESEARCH:232–255`). |
| D-03 | **Keep.** | A collection link can intentionally mean the page's collection. The parent checked must be that same destination; see the state finding. |
| D-04 | **Keep.** | Enables request-free/cross-parent collection targets when no page scope exists, without guessing when scope does exist. |
| D-05 | **Keep.** | M2M has no unique derived parent, while explicit scope is sufficient to construct a route (`ParentViewSet` declaration and fixture at `tests/test1/app/views.py:457`). |
| D-06 | **Keep.** | An absent single-parent relation cannot support a truthful nested object URL. Optional displays can remain text. |
| D-07 | **Keep.** | Resource rows do not declare ORM ancestry; explicit context respects their separate data model (`src/crud_views/lib/resource.py:138–160`). |
| D-08 | **Keep, with its stated limit.** | URL construction need not perform a membership query. It must not be described as membership/access certification; the decision explicitly says so. |
| D-09 | **Keep for the ordinary compatibility helper; do not export it as availability.** | Preserves scoped M2M behavior. Protected previews correctly have a stricter independent gate (`P/03:88`). DataPanel needs its own explicit policy boundary. |
| D-10 | **Keep only as the legacy callable fallback; change its use as the new panel's guarantee.** | The motivating dispatched toolbar has already passed its parent gate; the panel has not. P16 proves the difference. For a new renderer with known parent evidence, require an explicit check rather than inferring approval from `None`. No global fail-closed change to all old no-object calls is required by this recommendation. |
| D-11 | **Keep.** | P09/P10 establish the undeclared-permission mismatch. `P/03:78` appropriately preserves anonymous/inactive request handling and core assertions. |
| D-12 | **Keep.** | Avoid converting custom property/manager bugs into “not available”; the existing broad create resolver catch makes provenance important (`guardian/views.py:275–296`). |
| D-13 | **Keep.** | Strict default and optional unavailable result serve ordinary actions versus optional previews. Both modes must have tests of observable results, as planned. |
| D-14 | **Keep.** | Optional display is not permission to suppress caller mistakes; conflicts/wrong model remain errors. |
| D-15 | **Keep with the planned provenance distinctions.** | Existing view-specific exceptions remain distinct from the new public helper's errors (`P/01:83–106`; `P/05:74`). Do not implement optional behavior as a blanket catch of arbitrary custom `ValueError`. |
| D-16 | **Keep.** | Correctly acknowledges changed precedence/conflict behavior and requires paired migration guidance (`P/CONTEXT:79–81`). |

No evidence requires reversing the other explicit D-nn choices. The main disagreement is treating D-10's legacy assumption as sufficient for a new non-dispatched consumer; the phase text itself warns against that inference. The non-create state mismatch and copied-context lifetime are additional plan gaps, not decisions the maintainer explicitly approved in D-01–D-16.

### Query costs, public surface, and test adequacy

**Query costs:** the latest plans do require exact numeric pins for the new work: resolver ancestry, cold/cached/preloaded list rendering, breadcrumbs, same-parent versus distinct-parent Guardian checks, and protected previews (`P/01:108`; `P/02:86`; `P/03:84,145`; `P/04:104`). I found no basis to accuse the current plan of simply leaving those introduced query paths unmeasured by design. But the counts have not been measured yet. Preserve the existing cached breadcrumb 2-query/0-repeat assertion and add independent cold fixtures, as plan 02 explicitly says; do not substitute predicted formulas for observed SQL.

**Public names:** plan 05 inventories `ViewSet.get_parent_pks`, `ViewSet.get_url`, and the owning `GuardianParentPermissionMixin` with `cv_guardian_has_parent_access` in canonical `stability.md`, leaving private resolver/context/adapter names internal (`P/05:71,108`). No new implementation name has been added without an entry because no implementation has been added. Execution must deliver this inventory; Phase 7 cannot infer it from summaries alone.

**Tests:** the planned paired href/request tests and executable documentation are useful because they exercise the claimed behavior (`P/02:95–104`; `P/03:117–125`; `P/05:82–100`). Their important missing cases are the all-grants/non-create parent-state counterexample and same-owner delayed copied context. Opposite-grant fixtures alone cannot catch the former, and different-thread/task isolation alone cannot catch the latter. Plans also deliberately preserve URL-only columns rather than promising to hide them (`P/02:116`). Browser-visible checks and supported-series gates remain pending (`P/06:77–121`; `P/VALIDATION:108–117`).

### Tests actually run

Full suite, with the exact requested target and multicore mode:

```bash
PYTHONPATH="$PWD/src:$PWD" .nox/tests-3-12-django-5-2/bin/python -m pytest tests -n auto
```

**Result: 9,506 passed, 1 skipped in 155.70 seconds; exit 0.** Eight workers were used. Log: `/tmp/datapanel-review-full-suite.log`. This ran the current baseline, including its existing nested/Guardian tests. It did not run the future phase modules, which do not exist. The skip's reason was not separately investigated.

The probes were a temporary serial script, `/tmp/datapanel-review-probes.py`, using the repository's `tests.test1.conftest.pytest_configure()`, RequestFactory, an in-memory migrated database where needed, real fixture models/views, and Django's client for request comparisons. Source imports were forced with `PYTHONPATH="$PWD/src:$PWD"`; log: `/tmp/datapanel-review-probes.log`. Serial execution was appropriate for these tiny, stateful exploratory cases. Exceptions below were deliberately captured as observations; the script's exit 0 does not mean the proposed design passed.

| Probe | Operation | Observed result |
|---|---|---|
| P01 | Bind AuthorListView; disable pagination; slice queryset; `get_table(orderable=False, **get_table_kwargs())` | No page object, but `id` still orderable. |
| P02 | P01 with `?sort=id` | `TypeError: Cannot reorder a query once a slice has been taken.` |
| P03 | P01 with preordered `order_by('id')[:5]`, no sort query | Same TypeError. |
| P04 | Set instance list/card inline and list label-mode overrides | Resolvers ignored those values: None / icon / None. |
| P05 | Guardian child list access with AnonymousUser and None | True. |
| P06 | Two-object object_list plus nine-object table_data | Nine table rows. |
| P07 | Source `get_table_kwargs()` also supplies orderable | Duplicate-keyword TypeError. |
| P08 | Render stock card content with view/request/object_list and no actions | Card rendered; no pager/order bar. |
| P09 | Core permission-required view with undeclared key; anonymous access helper | True. |
| P10 | Same view's bound request permission check | AssertionError with migration hint. |
| P11 | Custom setup records an attribute before proposed post-setup override | Setup saw the original action list; instance changed only afterward. |
| P12 | Subclass source without redeclaring cv_viewset | Inherited ViewSet; registry still points to original list class. |
| P13 | Compile proposed load/translate combination | TemplateSyntaxError; i18n not loaded. |
| P14 | Core user has child view permission, lacks parent permission; GET child list/detail | Both 200. |
| P15 | Guardian child-granted, parent-denied; helper and GET list/detail | Both helpers True; both requests 403. |
| P16 | Same Guardian user, bind nested list and call queryset without dispatch | Child row returned; None access helper True. |
| P17 | Existing M2M fixture plus temporarily registered detail candidate; delete URL method | Related-manager `.pk` AttributeError. Registry change restored. |
| P18 | Table with Meta.exclude, then explicit actions exclusion | Existing Meta-excluded field stayed absent; actions removed. This does **not** support a claim that Meta.exclude is lost. |
| P19 | Bare RequestFactory request with user but no resolver_match; action rendering | AttributeError on resolver_match.url_name. |
| P20 | Grant parent and child; state allows Book but denies Publisher; render nested list link from Book detail then GET | Access True, enabled True, render hook saw Book; GET 403, request hook saw Publisher. |
| P21 | Capture copy_context inside a ContextVar scope; reset original; run copy on same thread | Original cleared, copied value still present, same thread identity. Primitive lifetime demonstration only. |
| P22 | Render stock card with POST action and request | CSRF and hidden form ID present; no native form= target. Actual protocol is data-cv-target in source. |

The essential table reproduction was:

```python
request = RequestFactory().get("/dashboard/?sort=id")
request.user = AnonymousUser()
request.resolver_match = SimpleNamespace(url_name="dashboard", namespace="")
view = AuthorListView()
view.setup(request)
view.paginate_by = None
view.table_pagination = False
view.cv_order_fields = []
view.object_list = Author.objects.all()[:5]
view.get_table(orderable=False, **view.get_table_kwargs())
# TypeError on the tested django-tables2 3.0.1 environment.
```

### Verified versus could not verify

Verified: plan contents and deviations, current source behavior, the full current Python suite, and the exploratory results above. Could not verify: phase implementation correctness, phase-specific test results, measured new query budgets, final public inventory, supported-version matrix, JavaScript tests, strict documentation build, browser acceptance, or downstream execution. Plan-review convergence records are planning evidence, not substitutes for these execution results. No package code, design document, or phase plan was changed by this review.

## If this were mine

I would retain the request-free URL helper and the decision to keep DataPanel provisional. I would not plan DataPanel until its authorization boundary, table invariants, and instance-configuration contract were settled with the reproduced cases above. I would compare the opt-in-helper-first scope against the integrated phase explicitly: automatic reuse is valuable, but its compatibility machinery should be a conscious cost. For the current phase, I would fix non-create collection state parity, add the delayed-context test, and keep the honest fallback limitations in the handoff. I would use the two actual Tabler widgets as the acceptance examples before expanding the constructor API or promising lazy equivalence.
