---
phase: 06-form-button-leaf
reviewed: 2026-10-28T09:51:51Z
depth: deep
files_reviewed: 51
files_reviewed_list:
  - CHANGELOG.md
  - docs/getting_started/tutorial-5-filters-permissions.md
  - docs/migrating-1.0.md
  - docs/reference/action_menus.md
  - docs/reference/buttons.md
  - docs/reference/icons.md
  - docs/reference/javascript.md
  - docs/reference/list_view.md
  - docs/reference/settings.md
  - docs/reference/theme.md
  - examples/bootstrap5/project/settings.py
  - noxfile.py
  - src/crud_views/lib/button_classes.py
  - src/crud_views/lib/crispy/buttons.py
  - src/crud_views/lib/crispy/form.py
  - src/crud_views/lib/formsets/layout.py
  - src/crud_views/lib/icons.py
  - src/crud_views/lib/settings.py
  - src/crud_views/lib/view/action_menu.py
  - src/crud_views/lib/view/base.py
  - src/crud_views/lib/view/button_data.py
  - src/crud_views/lib/view/buttons.py
  - src/crud_views/lib/view/label_mode.py
  - src/crud_views/lib/views/list.py
  - src/crud_views/lib/viewset/__init__.py
  - src/crud_views/static/crud_views/js/tooltip.js
  - src/crud_views/templates/crud_views/tags/button/form.html
  - src/crud_views/templatetags/crud_views.py
  - src/crud_views/templatetags/crud_views_formsets.py
  - src/crud_views_workflow/lib/forms.py
  - tests/js/list.filter.test.js
  - tests/js/modal.test.js
  - tests/js/viewset.test.js
  - tests/test1/golden/form_buttons/create.html
  - tests/test1/golden/form_buttons/delete.html
  - tests/test1/golden/form_buttons/filter.html
  - tests/test1/golden/form_buttons/update.html
  - tests/test1/golden/form_buttons/workflow.html
  - tests/test1/test_action_label_mode_config.py
  - tests/test1/test_button_classes.py
  - tests/test1/test_button_classes_templates.py
  - tests/test1/test_button_data.py
  - tests/test1/test_crispy_buttons.py
  - tests/test1/test_filter.py
  - tests/test1/test_form_button_checks.py
  - tests/test1/test_form_button_docs.py
  - tests/test1/test_form_buttons_golden.py
  - tests/test1/test_icon_host_leaves.py
  - tests/test1/test_icons_registry.py
  - tests/test1/test_label_mode.py
  - tests/test1/test_label_mode_docs.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-10-28T09:51:51Z
**Depth:** deep
**Files Reviewed:** 51
**Status:** issues_found

## Summary

Scope: the Phase 06 form-button leaf — the crispy adapters (`crud_views/lib/crispy/buttons.py`), the `"form"` branch
of `cv_button_data` (`button_data.py`), the leaf template, owner recovery across crispy's context overlays and the
formset transport, the filter-helper lifecycle rewrite (`views/list.py`), the form label-mode configuration
(`base.py`, `label_mode.py`, `action_menu.py`, `settings.py`, `viewset/__init__.py`), the icon availability
predicate (`icons.py`), the W292/E210/E211/W291 static checks (`view/buttons.py`), the nox floor session, the JS
tests and the documentation. Diffs were read against `56f4b63`, and every cross-module claim below was traced in the
installed crispy 2.7 source (`BaseInput`, `BasicNode.get_render`, `get_response_dict`, `FormActions.render`,
`FormHelper.get_attributes`) rather than assumed.

Cross-file traces performed (deep): adapter `render()` → `_cv_form_owner` tier scan → `cv_button_data(ctx, "form")`
→ `form.html`; `Formsets.render` / `cv_x_formset` page-owner transport → `_cv_page_tier`; `ListViewFilterFormHelper`
`__init__` → `_cv_prepare_layout` (deepcopy) → `get_attributes` → `render_layout` → adapters; `cv_form_icon_mode_checks`
→ `_static_form_classes` / `_static_form_controls` / `_static_filter_controls` → `_icon_available`; settings E106 /
ViewSet validator / view checks for the form map. The escaping boundary (plain-`str` normalization, Django `flatatt`
once into `cv_flat_attrs`, `{{ }}` autoescape in the leaf, `simple_tag` output escaping) holds; no injection path
was found. Import safety of the deferred imports in `buttons.py`, `formsets/layout.py` and
`crud_views_formsets.py` was confirmed by the unchanged `test_import_safety.py` shard.

The phase's Python shard (14 test files, 1314 tests) passes in this environment, and the pre-existing jsdom
`querySelector` failure noted in the SPEC is fixed (`:scope >`). All 23 files named in `noxfile.CRISPY_FLOOR_TESTS`
exist. The CHANGELOG `Breaking` entry has its paired `docs/migrating-1.0.md` section, as CLAUDE.md requires.

One correctness defect was proven at runtime and is a blocker: the `icon=` "not given" sentinel is a bare
`object()`, which `copy.deepcopy` does not preserve, so the filter helper's per-instance layout copy silently strips
the kind-default icon from any package button placed in a class-level or assigned layout, and makes it an
icon-availability failure in `"icon"` mode. No test covers that path.

## Critical Issues

### CR-01: `_KIND_ICON` sentinel does not survive `copy.deepcopy`, so deep-copied layout buttons lose their kind icon

**File:** `src/crud_views/lib/crispy/buttons.py:26`, `:127-128`, `:159`; `src/crud_views/lib/views/list.py:152-153`
**Issue:** `_KIND_ICON = object()` is compared by identity in `_cv_button_context`
(`_KIND_ICONS[kind] if self._cv_icon is _KIND_ICON else self._cv_icon`). `ListViewFilterFormHelper._cv_prepare_layout`
deep-copies every layout that is not the prepared instance (`prepared = copy.deepcopy(current)`), i.e. a class-level
`layout` on every helper construction (every request) and any layout a caller assigns to `helper.layout` —
both documented as supported in `docs/reference/list_view.md` ("a layout you assign to `helper.layout` later is
copied the same way") and the migration recipe tells users to move `add_input` buttons into a layout `FormActions`.
`copy.deepcopy(object())` returns a *new* object (verified: `copy.deepcopy(o) is o` → `False`), so every copied
`Submit`/`Button`/`Reset` constructed without `icon=` ends up with `_cv_icon` = a fresh `object()`, which is truthy and
not the sentinel. Runtime probe with `CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}` and a helper declaring
`layout = Layout("name", FormActions(Submit("submit", "Go", slot="form:filter-submit")))`:

- `"both"`: the hook-built button renders `<i class="fa-solid fa-filter" …></i> <span>Go</span>`; the deep-copied
  button renders `> <span>Go</span>` — the icon is silently gone (the leaf's `{% if cv_icon %}` is truthy, `cv_icon`
  renders to `""`).
- `"icon"`, non-strict: `WARNING … form button 'filter-submit' renders icon-only but its icon <object object at 0x…>
  is not available; rendered with its label instead`, on every request.
- `"icon"`, strict (`CRUD_VIEWS_STRICT`, default `DEBUG`): `ValueError` at render — a 500 for a configuration the
  static check `cv_form_icon_mode_checks` reports as fine, because it reads `_KIND_ICONS[kind]`, never the copied
  instance.

The leaf contract is also violated: `cv_icon` is documented as "the resolved icon value or `None`" but receives a
Python object. The example project ships `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`, so any project that
follows it and declares a filter layout with a package button hits the silent variant.

**Fix:** Make "icon not given" survive copying. Either store a boolean instead of relying on sentinel identity:

```python
def __init__(self, name, value, *, slot: str | None = None, icon=_KIND_ICON, **kwargs):
    self._cv_slot = slot or self.slot
    self._cv_kind_icon = icon is _KIND_ICON   # a bool deep-copies as itself
    self._cv_icon = None if self._cv_kind_icon else icon
    ...

def _cv_button_context(self) -> dict:
    kind = self._cv_form_kind()
    return {
        ...,
        "cv_icon": _KIND_ICONS[kind] if self._cv_kind_icon else self._cv_icon,
    }
```

or make the sentinel copy-stable:

```python
class _KindIcon:
    """icon= not given; identity survives copy / deepcopy so per-instance layout copies keep the kind icon."""
    __slots__ = ()
    def __copy__(self): return self
    def __deepcopy__(self, memo): return self
    def __reduce__(self): return "_KIND_ICON"

_KIND_ICON = _KindIcon()
```

Pair either with the regression test in WR-01.

## Warnings

### WR-01: No test renders a deep-copied adapter in `"icon"` or `"both"` mode

**File:** `tests/test1/test_crispy_buttons.py:715`, `:873`, `:1640-1641`; `tests/test1/test_filter.py:267-283`
**Issue:** The suite (1314 tests) passes with CR-01 present. The tests that put package adapters into a deep-copied
layout (`helper.layout = Layout(*fields)` at 715, `Layout(*_controls("x"))` at 873, the class-level
`LegacyHelper.layout` at 1641) render only under the `"label"` floor, where `cv_icon` is never consulted; the tests
that do switch the filter kinds to `icon`/`both` (`test_filter_actions_honor_the_list_view_form_modes`,
`test_filter_helper_pushes_its_owner_for_its_render_only`) build their buttons inside `get_form_actions()`, which
runs after the copy. The SPEC's "No mutation / interleaved renders" regressions cover the shared-adapter case but not
the copied-adapter case.
**Fix:** Add a test that declares a class-level `layout = Layout("name", FormActions(Submit(..., slot="form:filter-submit"), Reset(...)))`
on a `ListViewFilterFormHelper` subclass with `get_form_actions` returning `None`, renders it through
`{% crispy form helper %}` under `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"})` and again
`{"form": "icon"}` with `CRUD_VIEWS_STRICT=True`, and asserts the kind icons (`fa-filter`, `fa-rotate-left`) are
present, no warning is logged and nothing raises; also assert `cv_button_data` output `cv_icon` is a `str` for a
`copy.deepcopy(Submit("submit", "Go"))`.

### WR-02: The form normalizer admits any truthy non-`str` `cv_icon` into the leaf contract

**File:** `src/crud_views/lib/view/button_data.py:244`, `:281`, `:293`
**Issue:** `icon = ctx.get("cv_icon") or None` keeps any truthy object. It is then passed to `_icon_available`
(returns `False` for non-`str`, so `"icon"` mode takes the missing-icon path with a message that prints a Python
`repr`), to `icon_host_keys` (`resolve_icon` returns `None` → `("", True)`), and finally stored as
`data["cv_icon"]`, where the leaf's `{% if cv_icon and cv_icon_inline is not False %}` is truthy and `{% cv_icon %}`
emits `""`. The documented contract (`docs/reference/buttons.md`, "the resolved icon value or `None`") and the
`FORM_LEAF_KEYS` presence tests both assume `str | None`. This is the hole CR-01 fell through; closing it also makes
the strict error and the non-strict warning name something a developer can act on.
**Fix:**

```python
icon = ctx.get("cv_icon")
if not isinstance(icon, str) or not icon.strip():
    icon = None
```

placed before the `label_mode == "icon"` availability check, so a non-string icon is "no icon" everywhere (message:
`its icon None is not available`), and `cv_icon` is always `str | None`.

## Info

### IN-01: Per-request `deepcopy` of arbitrary user layout objects is a new failure surface that the docs do not state

**File:** `src/crud_views/lib/views/list.py:152`; `docs/reference/list_view.md` ("Custom filter helpers")
**Issue:** Before this phase a class-level `layout` was used by reference; now every helper construction runs
`copy.deepcopy(current)` over whatever the project put into the layout. Any layout object holding a non-copyable
member (a lock, an open resource, a bound C object, a custom `LayoutObject` with `__slots__` and no `__dict__` —
the `__class__` reassignment in `_cv_prepare_layout` would also fail for the latter) now raises `TypeError` at
`get_filterset()` on every request instead of rendering as before. The reference page says the layout is copied but
not that it must be deep-copyable.
**Fix:** State the deep-copy requirement in `docs/reference/list_view.md` next to "Each helper instance renders its
own copy", and consider catching `TypeError`/`copy.Error` around the deepcopy to raise a `ValueError` naming the
helper class and the offending layout.

### IN-02: Extra attributes are emitted in sorted order, not insertion order

**File:** `src/crud_views/lib/view/button_data.py:276`; `docs/migrating-1.0.md` ("Markup and submitted data")
**Issue:** Django's `flatatt` sorts key/value attributes and boolean attributes; crispy's `flatatt` preserved keyword
order. A custom `Submit(..., data_b="1", data_a="2")` therefore now renders `data-a` before `data-b`. Harmless for
browsers and the package's own buttons (which pass only `data_cv_cancel_url`, consumed), but a byte-level change for
projects with goldens on custom buttons. The migration page only says "the attribute order must match `button`
instead", which does not say the extra attributes are reordered.
**Fix:** Add one sentence to the "Markup and submitted data" list: extra attributes render in sorted order (Django's
`flatatt`), after `type`/`name`/`value`/`id`/`class`.

---

_Reviewed: 2026-10-28T09:51:51Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
