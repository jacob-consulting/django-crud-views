# Design: Context actions must not 500 on unregistered view keys (strict/DEBUG)

**Date:** 2026-06-24
**Status:** Approved
**Scope:** Single fix, shipped as one PR + a `0.8.1` patch release. First of a post-0.8.0
fix sweep (remaining items #2–#6 tracked separately).

## Problem

A ViewSet that registers only some CRUD views (e.g. `list` + `detail`, no `create`/`delete`)
raises `ViewSetKeyFoundError` while rendering its own list/detail/update pages, producing a
**500 in development**.

The default context-action settings reference keys that a ViewSet may legitimately not register:

- `CRUD_VIEWS_LIST_CONTEXT_ACTIONS` includes `create`
- `CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS` / `CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS` include `delete`

When `context_actions.html` loops over these keys and calls `{% cv_context_action key %}`,
the tag resolves the key through `CrudView.cv_get_context` → `cv_get_cls_assert_object` →
`ViewSet.get_view_class`, which calls `cv_raise(is_view_registered(key), ...)` and raises
`ViewSetKeyFoundError` for the unregistered key.

### Why it 500s in dev specifically

`cv_context_action` *is* decorated `@ignore_exception(ViewSetKeyFoundError, default_value="")`
(`crud_views/templatetags/crud_views.py`). But `ignore_exception` re-raises in strict mode:

```python
if getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG):
    raise
```

`CRUD_VIEWS_STRICT` **defaults to `DEBUG`**. So with `DEBUG=True` (normal dev server) the
exception re-raises → 500. With `DEBUG=False` (production) it degrades to `""` and the page
renders. The bug is therefore dev-only, which is why it surfaced while developing a consuming
project.

### Why the originally-reported root cause is wrong

The upstream report claimed `cv_context_action` lacks the `@ignore_exception` decorator. It does
not — the decorator has been present since the `vs`→`cv` rename. The decorator is not the issue;
strict-mode re-raise on a *legitimate* unregistered key is. The report's alternative suggestion
(iterate `view.cv_get_context_buttons()`) also does not fix it: that method calls
`cv_get_context` per key (`view/base.py:331`) **before** its access filter, so it raises on the
unregistered key just the same.

## Decision

Treat an **unregistered view key** as "skip this button," not a misconfiguration — in all modes,
including strict. Linking to `create` only when a `create` view exists is normal, expected
behavior, not a configuration error. Strict mode should still fail loudly for genuine
misconfiguration (missing templates, malformed config), but must not punish a valid ViewSet for
omitting an optional CRUD view that a *default* setting happens to mention.

This is deliberately scoped to the context-action rendering path. `cv_get_context` itself keeps
its current contract (raising for unknown keys) for callers that pass an explicit, known key.

## Approach

1. **`CrudView.cv_get_context_buttons` skips unregistered keys.**
   Before calling `cv_get_context` for a key, skip the key when it is neither a registered
   context button nor a registered view:

   ```python
   for key in keys:
       if self.cv_get_context_button(key) is None and not self.cv_viewset.is_view_registered(key):
           continue
       ctx = self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request)
       if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
           continue
       result.append(ctx)
   ```

   This makes the method's "access-filtered" promise actually hold for default key lists.

2. **`context_actions.html` renders the filtered list.**
   Replace the per-key `{% cv_context_action key object %}` loop with a single resolved list from
   `cv_get_context_buttons`, rendered via the existing `{% cv_render_context_button ctx %}` tag.
   Both theme copies of `tags/context_actions.html` (`crud_views`, `crud_views_plain`) are
   updated. The `<br>` / `btn-group` wrappers are preserved.

3. **Leave `cv_context_action` in place** (still used directly elsewhere / back-compat); its
   strict-mode behavior is unchanged. The bug is fixed by routing the default-driven loop through
   the filtered resolver, not by weakening `cv_context_action`.

### Exact symbols

- `src/crud_views/lib/view/base.py` — `cv_get_context_buttons` (~line 321)
- `src/crud_views/templates/crud_views/tags/context_actions.html`
- `src/crud_views_plain/templates/crud_views/tags/context_actions.html`
- `ViewSet.is_view_registered` (`src/crud_views/lib/viewset/__init__.py`) — existing, reused

## Testing (TDD)

RED first, against current `main`:

1. **Regression (primary):** a ViewSet registering only `list` + `detail` (no `create`/`delete`)
   renders its list page with `DEBUG=True` / `CRUD_VIEWS_STRICT=True` and returns 200 — currently
   raises `ViewSetKeyFoundError`. Add detail + update page variants (delete key).
2. **Unregistered key is omitted:** the rendered list page contains no `create` button; a
   registered key (e.g. `detail`) still renders.
3. **Strict mode still strict for real errors:** an explicitly bad context key that is neither a
   button nor a view still raises under strict mode when resolved via `cv_context_action`
   directly (guards against over-broad suppression).
4. **Access filtering unchanged:** a registered-but-inaccessible key (no permission) is still
   omitted (existing behavior preserved).

Run via `cd tests && pytest`. Verify the full suite stays green on the matrix in CI.

## Release

Single PR following the project PR lifecycle (branch → CI → fix ruff → squash-merge to `main`
→ wait main CI). After merge, bump `0.8.0` → `0.8.1`, finalize CHANGELOG (promote Unreleased),
push, and let the publish workflow run so the consuming project can upgrade.

## Out of scope

Issues #2 (django-tables2 floor), #3 (`cv_csrf_token` upgrade note), #4 (workflow lazy imports),
#5 (workflow `0003` migration), #6 (`CRUD_VIEWS_THEME` docs + system check) — separate PRs, each
its own spec, per the agreed one-by-one plan.
