I'll verify the revised N1/N2 plans against the current source, then check the other seven plans for regressions.
Reviewed at `91f93d4` against current source, read-only. Planned artifacts are not treated as missing. The parent 17/17 decision check and the existing 46-pass baseline are not implementation proof. H1, H2, H3 and A1–A18 stay closed: no regression in the revised tasks.

## 06.5-01

**Summary.** Size and one host/element icon still belong on `CvHeadingNode.render` (`src/crud_views/templatetags/crud_views.py:339-353`) and the modal line (`src/crud_views/templates/crud_views/modal/content.html:3`). This plan adds the heading keys and coordinates N1; it does not itself rewrite the sentinel guard.

**Strengths.** Implicit size matches today's `h{level}` only when the rendered level changes (`crud_views.py:348`). Unknown kwargs already raise (`crud_views.py:374-376`). Settings merge per key (`src/crud_views/lib/button_classes.py:135-139`), so a later sentinel override cannot erase unlisted heading defaults. Task 01-02 still owns `EXPECTED_KEYS`, `len == 74` (`tests/test1/test_button_classes.py:94-106`), the five-host guard (`:310-313`), and the one count sentence (`docs/reference/buttons.md:147`). W362 still accepts only default or action-mode keys (`button_classes.py:301-318`).

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-02

**Summary.** This plan owns the N1 guard-scope change and the host-title migration that would otherwise trip it. The test host still nests `h5.d-flex > h3` with no classes on the inner heading (`tests/test1/app/templates/app/crud_views.html:13-22`). The demo still hard-codes `class="h3 mb-0"` (`examples/bootstrap5/project/templates/project/crud_views.html:17`).

**Strengths.** `SENTINEL_CLASSES` is built from every `DEFAULT_BUTTON_CLASSES` key (`tests/test1/test_button_classes_templates.py:131-133`). `_styled` is any element carrying a sentinel (`:144-146`); `_offenders` then rejects other tokens on that element and its `span` descendants (`:149-159`). The six real pages run under that override (`:232-267`). Excluding only the `heading`, `heading-page`, `heading-modal`, and `heading-group` location segments stops those keys becoming sentinels, while `{**defaults, **override}` (`button_classes.py:139`) keeps their real classes. Button, menu, and form leaves stay in the override. The new regression matches the real traversal: heading `mb-0` must not be an offender, and an injected utility on the styled control and on its label span must both be reported. The source scanner (`:28-48`) is unchanged. `data-test-page-title` still cannot match `card-header` group wrappers.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

**N1 sign-off: FULLY RESOLVED.** The auto-enroll path is the sentinel value, not the heading tag. Plan 01 adds the keys; plan 02 drops only those four namespaces from the override, keeps every non-heading sentinel, and adds both the utility-preservation control and the button/span leak controls before the guard rerun. Default `header_level` is `None` (`src/crud_views/lib/settings.py:53`), so the guard's card title (`src/crud_views/templates/crud_views/tags/card.html:6`) does not also receive an implicit size token (`crud_views.py:342-348`). That combination is not a planned-gate failure.

## 06.5-03

**Summary.** This plan owns the N2 producer wiring. Triggers still use `forloop.first` and slugified titles (`layouts/tabs-vertical/object_detail.html:6-15`). Panels are always `tab-pane fade` (`layouts/tabs-vertical/group.html:2-5`). The accordion root is fixed (`layouts/accordion/object_detail.html:2`). `render_object_detail` still renders a fresh context with only `groups` and `layout` (`src/crud_views_object_detail/templatetags/crud_views_object_detail.py:32-38`), and `render_group` likewise (`:41-54`).

**Strengths.** Only accordion and tabs-vertical have `object_detail.html`. `card-rows`, `list-group-3col`, `split-card`, `striped-rows`, and `table-inline` therefore hit `crud_views_object_detail/object_detail.html:1-4`, which calls `{% render_group group layout=layout %}` with no projection. Task 03-03 changes that shipped fallback to iterate `component.groups` and pass the original entry and component into `render_group`, and it tests group-only copies of all five packs through that file. Supplied presentation skips a second allocation; bare `render_group` still gets a local projection. `{% load crud_views %}` remains required on `tabs-vertical/object_detail.html:1`.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-04

**Summary.** Stable identity still has no config field (`src/crud_views_object_detail/lib/config.py:56-62`). `resolve_group` copies title, description, icon, and properties only (`resolvers.py:246-253`). The content template calls `render_object_detail` with no component id (`view_detail.content.html:3`). `ResolvedGroup` has no render id (`resolvers.py:58-63`).

**Strengths.** Appending `id` keeps existing keyword construction valid. `cv_is_modal_request` is `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:57-59`); `modal.js:140` and `:177` send that header. Task 04-01 renders a real detail view through the unchanged shipped fallback from 03-03, with a group-only copy, resolved `PropertyGroupConfig.id`, and the request-aware hook, and requires the same targets after repeat, translation, and reorder. Default layout is split-card, which is one of the five fallback packs. Reservation stays once per component, not again in `render_group`.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

**N2 sign-off: FULLY RESOLVED.** The fallback is a real second `select_template` candidate (`crud_views_object_detail.py:32-38`) and today drops enclosing identity (`object_detail.html:2-3`). Plan 03 wires that template to the shared projection. Plan 04 proves supplied component and group tokens survive that path, including the ordinary view hook, without a full `object_detail.html` override.

## 06.5-05

**Summary.** `loadScript` still reads only core static (`tests/js/helpers/load.js:8,32-33`). `runtime-contract.test.js:17-32` still discovers every `tests/js/**/*.test.js` and copies only core JS; `:69-82` requires every discovered file to pass. `apps.py` has no `ready()` (`src/crud_views_object_detail/apps.py:5-9`). `register_assets` still raises on an existing key (`src/crud_views/lib/assets.py:66-67`).

**Strengths.** Tasks 05-01/05-02 still own the package-aware loader, extension-static sandbox copy, `requiredFiles` entry, and the Node-only negatives. No N1/N2 edit weakens that. Direct `bootstrap.Tab` remains the stated stock-only boundary. `modal.js:23-24` still names the lifecycle events.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-06

**Summary.** Badge CSS is still one walk: `None` first, then callback, nonempty map, then fixed color (`resolvers.py:94-110`). Template choice is still `badge_css` before explicit `template` (`crud_views_object_detail.py:80-86`).

**Strengths.** Appending `badge_color` / `badge_pill` after `badge_label` (`resolvers.py:44-55`) stays positional-safe and does not collide with plan 04 appending `ResolvedGroup.id`. Unresolved defaults remain `None` / `False`. Plan 04 depends on this plan, so the resolver edit is ordered.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-07

**Summary.** `no_label` is still a field (`src/crud_views/lib/view/card.py:11`). The after-validator rejects it only when true beside `label_mode` (`:31-32`). The template guard still raises on `cv_no_label` in context (`src/crud_views/lib/view/button_data.py:126-130`). The app fixture still constructs `no_label=True` (`tests/test1/app/views.py:80`).

**Strengths.** Membership rejection, non-mapping passthrough, and the plan-01 dependency for `buttons.md` are unchanged. N1's heading-key work does not rewrite this plan's alias prose or the canonical count.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## 06.5-08

**Summary.** The host still loads Bootstrap 5.3.3, Font Awesome 6.7.2, and jQuery 3.7.1 with SRI (`tests/test1/app/templates/app/base.html:13-30`). The analog still rejects port 8143 (`tests/browser/conditional_formsets_server.py:485-487`).

**Strengths.** The preflight, exit 2, reserved-port checks in both entry points, keyboard-before-click, and `cv_is_modal_request` page/modal tokens are unchanged. N1/N2 do not alter this harness.

**Concerns.** None.

**Suggestions.** None.

**Risk.** MEDIUM. New browser process code, with a fail-closed network precondition. That is harness risk, not an open N1/N2 defect.

## 06.5-09

**Summary.** Unreleased changelog bullets still say the template guard raises and `CardAction(no_label=True)` is unaffected (`CHANGELOG.md:131-139`). `render_to_string` in formset layout still starts a fresh context (`src/crud_views/lib/formsets/layout.py:16-19,29-30`). Ordinary Vitest still includes only `tests/js` (`vitest.config.js:6`).

**Strengths.** Task 09-02 still amends those bullets in place. Tasks 09-01/02 still distinguish transported library renders from untransported fresh backend renders. Task 09-03 still runs the integration config and inventories retained `cv_header_icon` (`src/crud_views/templatetags/crud_views.py:312-315`) separately from the new heading recipe. The N2 fallback recipe is covered by the executed copied-layout fences, not by a second documentation location.

**Concerns.** None.

**Suggestions.** None.

**Risk.** LOW.

## Cross-plan conclusions

Wave order holds: 01/06, then 02/07, 03, 04/05, 08, 09. Shared `buttons.md` stays 01 before 07. `test_heading_level.py` stays 02 before 03. `resolvers.py` stays 06 before 04. `presentation.py` stays 03 before 04. D-01–D-17 are unchanged. Form-leaf, auth, deletion, and conditional contracts are not reopened.

N1 is closed by registry exclusion plus controls, not by skipping the guard. Plan 01's `-k button_classes` still runs `test_button_classes_templates` before host titles use heading keys; the modal partial is not one of the six guard URLs (`test_button_classes_templates.py:232-239`). Plan 02 migrates those titles and the guard together.

N2 is closed by wiring the actual fallback consumer, then proving supplied identity through group-only copies of the five packs that select it. Interactive packs keep their own `object_detail.html` and are migrated in 03-01/02.

## N1/N2 closure

| ID | Severity | Verdict | Why |
|---|---|---|---|
| N1 | MEDIUM | FULLY RESOLVED | `test_button_classes_templates.py:131-159,250-267` enrolls every default key as a sentinel and flags other classes on styled elements and label spans. Plan 02 excludes only the four heading location namespaces, preserves non-heading sentinels and the source scanner, and requires both a retained `mb-0` non-failure and positive button/span leak detection. Plan 01 coordinates and does not weaken `test_button_classes.py:94-106,310-313`. |
| N2 | LOW | FULLY RESOLVED | `object_detail.html:1-4` is the fallback selected at `crud_views_object_detail.py:32-38` for the five packs with no pack `object_detail.html`. Plan 03 passes the original component and entry into `render_group`. Plan 04 checks that path with resolved group ids and `cv_is_modal_request` (`base.py:57-59`) across repeated page/modal renders. |

## Genuinely unresolved findings

None.
