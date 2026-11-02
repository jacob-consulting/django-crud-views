I'll verify the revised plans against current source, starting with the H1/H2 seams and the A1–A13 dispositions.
The plans are on disk. Next I’ll check the class-table, heading, ID, badge, and alias seams those revisions depend on.
H1 and H2 are fully resolved in the revised plans at `4762417`. A1–A13 are closed by executable tasks or an explicit, source-backed rejection. No new unresolved findings.

## 06.5-01

**Summary.** Size and one host/element icon go through `CvHeadingNode` (`src/crud_views/templatetags/crud_views.py:348-376`) and the class table (`src/crud_views/lib/button_classes.py:135-155`, `:301-318`). The modal site is still `{% cv_heading "header" level=5 class="modal-title" %}{% cv_header_icon %} {% cv_header %}` (`src/crud_views/templates/crud_views/modal/content.html:3`).

**Strengths.** Implicit size matches today’s `h{level}` only when the rendered level changes (`crud_views.py:348`). `icon_class` is a second filter expression, so host classes are not concatenated inside the single `class=` argument. The modal golden’s leading space (`tests/test1/golden/heading_level/modal_detail.html:1`) is the literal separator, and the plan keeps it when `inline_html` is empty. Task 01-02 owns `EXPECTED_KEYS`, `len == 74` (`tests/test1/test_button_classes.py:94-106`), the five-host guard (`:310-313`), and the one count sentence (`docs/reference/buttons.md:147`) before that verify runs. Plan 07 `depends_on: ["06.5-01"]`.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

**H1 sign-off: FULLY RESOLVED.** The guard that would fail is in the task that updates the independent expected set, host-slot count, and canonical sentence together. No future count is prescribed.

## 06.5-02

**Summary.** Host pages still nest `h5.d-flex > h3` (`tests/test1/app/templates/app/crud_views.html:13-22`) and hard-code `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`; `docs/reference/templates.md:50`). Split-card and striped-rows put the icon outside the heading (`layouts/split-card/group.html:8-9`, `layouts/striped-rows/group.html:4-5`).

**Strengths.** `data-test-page-title` replaces the `h5.d-flex` exclusion (`tests/test1/test_heading_level.py:26-27`) without matching `card-header` wrappers (`layouts/card-rows/group.html:3-4`, `layouts/striped-rows/group.html:3-5`). Consumers use `icon_class`, not string joins. Split-card `fs-5 text-default` loss is recorded for plan 09.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-03

**Summary.** Triggers use `forloop.first` and slugified titles (`layouts/tabs-vertical/object_detail.html:6-15`); panels are always `tab-pane fade` (`layouts/tabs-vertical/group.html:2-5`). The accordion root is fixed (`layouts/accordion/object_detail.html:2`). `render_object_detail` renders a fresh context with only `groups` and `layout` (`templatetags/crud_views_object_detail.py:38`), so the plan projects identity once and passes it in.

**Strengths.** `ResolvedGroup` stays free of render IDs (`resolvers.py:58-64`). Length-prefixed tokens stay injective. `{% load crud_views %}` is required on `tabs-vertical/object_detail.html:1`, which currently loads only `crud_views_object_detail`; `cv_icon` there is the local tag (`crud_views_object_detail.py:101-104`), not `cv_heading_icon`. Stock `tabindex=0` is an explicit choice, with both content shapes tested in plan 08.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-04

**Summary.** Group config has no `id` (`config.py:56-62`); `resolve_group` copies title, description, icon, and properties only (`resolvers.py:248-253`). The content template calls `render_object_detail` with no component id (`view_detail.content.html:3`).

**Strengths.** Appending `id` keeps positional `ResolvedGroup(...)` calls valid. `cv_is_modal_request` is `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:57-59`); `modal.js:140` and `:177` send that header. `AuthorModalDetailView` is `cv_modal = True` (`tests/test1/app/views.py:894-896`), so the flag alone is not the discriminator. Collision state is the earliest non-base render frame: `RenderContext.get` sees only `dicts[-1]` (Django 5.2 `django/template/context.py:200-201`). Startup checks stay out of scope; E242–E245 (`mixins.py:84-94`) are a different path.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW. The frame rule is specified and covered on 4.2/5.2/6.0.

## 06.5-05

**Summary.** Page-load `Tab` construction does not cover HTML injected after `window` load. `modal.js:23-24` and `:94-96` already dispatch `cv:modal:loaded` / `cv:modal:unload` on the modal element. `tooltip.js:32-55` is the lifecycle analog, but only queries descendants (`:27`).

**Strengths.** `register_assets` raises on any existing key (`assets.py:66-67`); the plan compares `get_registered()` (`:71-76`) and still lets a conflicting tuple raise. Root-itself matching, no `show()`, and unmarked roots with no `bootstrap` lookup are explicit. Rejecting `cv.adapters.tab` is a stated boundary: adapters today are modal, tooltip, collapse, and alert (`adapters.js:53-94`).

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-06

**Summary.** Badge CSS is one walk: `None` returns first, then callback, nonempty map, then fixed color (`resolvers.py:94-110`). `resolve_property` calls it once (`:191-204`). Template choice is `badge_css` before explicit `template` (`crud_views_object_detail.py:80-86`).

**Strengths.** Appending `badge_color` / `badge_pill` preserves keyword and short positional `ResolvedProperty(...)` callers (`tests/test1/od/test_templatetags.py:128`). Empty-map fallthrough stays distinct from a nonempty-map miss. Unresolved defaults are `None` / `False`, so a native template cannot pill ordinary values.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-07

**Summary.** `no_label` is still a field (`src/crud_views/lib/view/card.py:11`). The after-validator only rejects it when true beside `label_mode` (`:31-32`). Runtime treats a truthy value as icon mode (`src/crud_views/lib/views/card.py:49-52`). `no_label=True` alone still constructs (`tests/test1/test_card_action_label_mode_field.py:26-27`). Deleting the field without a before-validator would drop `no_label=False` under Pydantic’s ignore-extra default.

**Strengths.** Membership, not truthiness, matches D-09. Non-mappings return unchanged, with `model_validate` of an existing instance and a non-mapping `ValidationError` test. Plan 07 is wave 2 after plan 01 and must not rewrite the heading count. Pydantic version is recorded, not pinned.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-08

**Summary.** Server tests cannot prove ArrowDown on tabs injected after `window` load. The host loads Bootstrap 5.3.3, Font Awesome 6.7.2, and jQuery 3.7.1 from CDNs with SRI (`tests/test1/app/templates/app/base.html:13-30`).

**Strengths.** The runner reuses those versioned URLs and integrity attributes, preflights CSS/JS/font in the browser, records SHA-256, and exits 2 on DNS/TLS/SRI/font failure without stubbing or skipping. `gettext_lazy("January")` / `"February"` resolve to `Januar` / `Februar` in Django 5.2’s `django/conf/locale/de/LC_MESSAGES/django.po:991-995`. `translation.override` wraps dispatch and `TemplateResponse.render()`. Tab from the selected trigger lands on the panel, then its link or the after-tabs control.

**Concerns.** None.

**Suggestions.** None.

**Risk.** MEDIUM. New browser process code, but the asset gate is fail-closed.

**H2 sign-off: FULLY RESOLVED.** Provenance, hosts, version, SRI reuse, font response, and the network-failure policy are executable. A documented network precondition was an allowed closure; offline vendoring was not required.

## 06.5-09

**Summary.** Copied tabs still need `presentation.control_id`, `panel_id`, and `selected`. `docs/migrating-1.0.md:142` and `:157` still say `CardAction(no_label=True)` keeps working. Unreleased changelog bullets still say the template guard raises and the constructor is unaffected (`CHANGELOG.md:131-140`).

**Strengths.** Task 09-02 edits those bullets in place and executes `cv_sources("js", keys=["crud_views", "crud_views_object_detail"])` against `pipeline.py:86-90`. Task 09-01 publishes the `cv_is_modal_request` hook and the stock panel `tabindex` qualification. The 36k estimate is an explicit budget, not a cut in acceptance. Plan-level verification still requires the three full suites, vitest, mkdocs, ruff, and both browser commands; the narrow `<verify>` block is incremental only.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## Cross-plan

Wave order holds: 01/06, then 07 after 01, 02, 03, then 04/05, then 08, then 09. Shared `buttons.md` work is ordered. D-01–D-17 are unchanged. Form-leaf, auth, deletion, and conditional contracts are not reopened. Phase 7 still owns stability tiers.

## Prior-finding closure

| ID | Verdict | Why |
|---|---|---|
| H1 | CLOSED | Plan 01-02 updates registry, `EXPECTED_KEYS`, host-slot guard, and `buttons.md:147` before `-k button_classes`. Plan 07 depends on 01. |
| H2 | CLOSED | Plan 08 names the `base.html:13-30` CDN/SRI set, font response, hashes, and exit 2. No pass on missing assets. |
| A1 | CLOSED | `icon_class` joins escaped nonempty classes; modal literal space kept. |
| A2 | CLOSED | `data-test-page-title` only; card-header headings stay selected. |
| A3 | CLOSED | Stock `tabindex=0` chosen; plans 08 and 09 test and qualify focus order. |
| A4 | CLOSED | Rejected: optional diagnostics are out of scope; render-time D-07 errors remain. |
| A5 | CLOSED | `cv_is_modal_request` plus `X-CV-Modal: true` in plans 04, 08, and 09. |
| A6 | CLOSED | Rejected: stock Bootstrap ownership; no new adapter seam. |
| A7 | CLOSED | Plan 09-02 amends `CHANGELOG.md:131-140`, not only appends. |
| A8 | CLOSED | Installed Pydantic version recorded; no pin. |
| A9 | CLOSED | `translation.override` plus Django `January`/`February` catalog. |
| A10 | CLOSED | 36k budget recorded; acceptance not reduced. |
| A11 | CLOSED | Plan 03-01 loads `crud_views` and renders the tab template. |
| A12 | CLOSED | Plan 09-02 executes explicit `keys=` versus core-only omission. |
| A13 | CLOSED | Non-mappings returned unchanged; existing-instance validation tested. |

**Unresolved findings:** none.
