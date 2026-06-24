# Design: Unify action rendering — skip unregistered keys, drop greyed-out buttons

**Date:** 2026-06-24 (revised twice: after implementation surfaced the false-green/greyed-button
problem, and after the decision to apply the change consistently to list-row actions too)
**Status:** Approved (central resolver fix + drop greyed buttons across toolbar **and** list rows)
**Scope:** Single PR + a `0.8.1` patch release. First of a post-0.8.0 fix sweep
(remaining items #2–#6 tracked separately).

## Problem

Two intertwined issues span both action-rendering surfaces — the **context-action toolbar**
(`{% cv_context_actions %}`) and the **list-row actions** (`{% cv_list_action %}` /
`{% cv_list_action_form %}`):

1. **Unregistered-key 500 (the reported bug).** A ViewSet that registers only some CRUD views
   (e.g. `list` + `detail`, no `create`/`delete`) raises `ViewSetKeyFoundError` while rendering
   its own pages in **development** (`DEBUG=True`). The default context-action settings reference
   keys a ViewSet may legitimately not register (`create` in list defaults; `delete`/`update` in
   detail/update defaults). Every render tag resolves a key through `CrudView.cv_get_context` →
   `cv_get_cls_assert_object` → `ViewSet.get_view_class`, which raises for an unregistered key.
   `cv_context_action` is decorated `@ignore_exception(ViewSetKeyFoundError, default_value="")`,
   but `ignore_exception` **re-raises in strict mode**, and `CRUD_VIEWS_STRICT` *defaults to
   `DEBUG`*. So the page 500s in dev and merely logs a warning in production.

2. **Greyed-out inaccessible buttons (a burden, not a feature).** An action the user lacks
   permission for is rendered as a *disabled, greyed-out* button — in the toolbar
   (`context_action.html` `{% else %}` branch) and in bootstrap5 list rows (`list_action.html`
   `btn-outline-secondary … disabled`). Per product decision this is dropped everywhere: an
   inaccessible action is **hidden**, matching how standalone context buttons
   (`cv_context_button`, issue #27 custom loops) already behave.

### Why the narrow fixes were rejected

- Strengthening `@ignore_exception` does nothing: it is already present; the re-raise is by-design
  strict-mode behavior tied to `DEBUG`.
- Rerouting only the toolbar through `cv_get_context_buttons` fixes the toolbar but not list rows,
  which resolve keys through the same `cv_get_context` and have the identical unregistered-key
  trap. The shared cause lives in the resolver, so the fix belongs there.
- The earlier-committed guard inside `cv_get_context_buttons` (commit `6bef1a5`) addressed only the
  direct-call path and left the actual page-render paths (which use `cv_context_action` /
  `cv_list_action`) unfixed; its page tests were false-green because tests run `DEBUG=False`
  (strict off), where the old `@ignore_exception` already suppresses the error.

## Decision

Fix once, at the resolver, and render consistently:

1. **`CrudView.cv_get_context` skips unregistered keys.** When a key is neither a context button
   nor a resolvable view (including the list→card fallback), return an empty dict `{}` instead of
   raising — in all modes. An unregistered default key is normal, not a misconfiguration. This
   single change covers every consumer: `cv_context_action`, `cv_list_action`,
   `cv_list_action_form`, `cv_context_button`, `cv_context_url`, and `cv_get_context_buttons`.
   `get_view_class` itself keeps raising (URL routing relies on it); only `cv_get_context`
   softens it.

2. **All render templates hide inaccessible / disabled actions.** Render only when
   `cv_action_enabled is not False and cv_access is True`. Delete the greyed-out `{% else %}`
   branches.

The committed `cv_get_context_buttons` guard is **removed** as now-redundant: with `cv_get_context`
returning `{}`, the loop's existing `if not ctx: continue` skips unregistered keys. Single source
of truth.

### Behavior change (call out for reviewers / changelog)

Permission-restricted users previously saw greyed-out, disabled buttons for actions they could not
perform — both in the toolbar and in list rows. They now see **nothing** for those actions, on both
surfaces. This is intentional and uniform.

## Changes

### Code

`src/crud_views/lib/view/base.py`

- `cv_get_context` (~line 346): wrap the view-class resolution so an unregistered key returns `{}`:
  ```python
  context_button = self.cv_get_context_button(key)
  if context_button:
      return context_button.get_context(context)
  try:
      cls = self.cv_get_cls_assert_object(key, obj)
  except ViewSetKeyFoundError:
      return {}  # key is not a registered view (and not a context button) -> skip, not an error
  ```
  (Import `ViewSetKeyFoundError` from `crud_views.lib.exceptions` at top of module.)
- `cv_get_context_buttons` (~line 321): remove the `is_view_registered` guard line added in
  `6bef1a5`; keep the rest (the `if not ctx or … continue` filter now also skips unregistered keys).

`src/crud_views/templatetags/crud_views.py`

- `cv_context_action` (~line 74): short-circuit empty context — `if not ctx: return ""` before the
  template-code/template branches.

### Templates (drop greyed, hide inaccessible) — keep both themes in sync

- `crud_views` + `crud_views_plain` `tags/context_action.html`: guard
  `{% if cv_key and cv_action_enabled is not False and cv_access is True %}` and remove the
  `{% else %}` greyed branch.
- `crud_views` `tags/list_action.html`: render only when `cv_access is True` (and
  `cv_action_enabled is not False`); drop the `btn-outline-secondary … disabled` variant.
- `crud_views_plain` `tags/list_action.html`: add the `cv_access is True` guard (it currently
  renders the link regardless of access — make it consistent).
- `crud_views` `tags/list_action_form.html`: add `cv_access is True` to the existing guard so the
  hidden POST form is emitted only for accessible actions. (No plain-theme counterpart exists.)

### Tests

New file `tests/test1/test_context_action_unregistered_key.py`:

- **`test_get_context_buttons_skips_unregistered_keys`** (unit, RED on `main`): on `cv_contract`
  (list+detail only), `view.cv_get_context_buttons(keys=["create", "list"])` returns `list` only,
  no raise. (Already committed; keep — still passes after the guard moves to `cv_get_context`.)
- **`test_pages_render_with_unregistered_default_keys_in_strict`** (integration, RED on `main`):
  force `CRUD_VIEWS_STRICT=True` (monkeypatch — tests run `DEBUG=False`, so strict must be forced
  to reproduce the dev bug). GET `cv_contract` list and detail → 200; assert `cv-key="create"` /
  `cv-key="delete"` absent. On `main` these raise `ViewSetKeyFoundError`.
- **`test_inaccessible_actions_are_hidden`** (integration, RED on `main`): a view-only user on a
  `cv_author` list page → the toolbar has no `disabled` context-action button **and** the table
  rows have no `disabled` row action; `cv-key="create"` absent from the toolbar. On `main` the
  greyed buttons are present.

Update existing tests for the greyed-button removal:

- `tests/test1/test_permissions.py::test_author_view` — for the view-only user, the `create`
  context action and the `update`/`delete` row actions are now **hidden**, not disabled. Replace
  the `is_disabled` assertions (and the `action.href`-derived GETs) with: assert each action is
  absent from the toolbar/row, and assert the endpoints still return 403 by GETting URLs built via
  `reverse(cv_author.get_router_name(<key>), …)` directly. Keep the `detail` action assertions
  (the view-only user *can* access detail).
- `tests/test1/test_workflow.py::test_workflow_view_get_contains_campaign_name` — re-verify the
  campaign name still appears (expected via the page header / the accessible `update` action). Only
  adjust if it relied on a now-hidden disabled button.
- `tests/test1/test_filter_pinned.py::test_pinned_hides_filter_toggle_button` — re-verify selectors
  for the (accessible) filter toggle still match.

The test helper `tests/lib/helper/boostrap5.py` may need a "not present" accessor (e.g.
`get_context_action`/`get_action` returning `None` or a `has_*` predicate) so absence is assertable
cleanly; extend it minimally if required.

Run via `cd tests && pytest`; the full suite must stay green on the CI matrix.

## Release

Single PR (branch `fix/context-action-unregistered-key-strict`, already holds commit `6bef1a5`).
The remaining work — central `cv_get_context` skip, guard removal, `cv_context_action` short-circuit,
template simplification (both themes, toolbar + rows), and the test updates — lands on the same
branch. PR lifecycle: CI → fix ruff → squash-merge to `main` → wait main CI. After merge: bump
`0.8.0` → `0.8.1`, finalize CHANGELOG (note the hidden-vs-greyed behavior change), push, publish.

## Out of scope

Issues #2 (django-tables2 floor), #3 (`cv_csrf_token` upgrade note), #4 (workflow lazy imports),
#5 (workflow `0003` migration), #6 (`CRUD_VIEWS_THEME` docs + system check) — separate PRs.
