# Context Action Label Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A target view's `cv_context_action_label_mode` sets the label mode of every context toolbar button that
points at it, as the last fallback before `"icon"`.

**Architecture:** The target's value travels in the action data built by its `cv_get_dict()` (like `cv_variant`), so
plain keys, registered `ContextButton`s and the parent/child/sibling buttons all carry it. `cv_get_context(...,
location="context")` passes it into `cv_get_action_label_mode()` as an optional fallback argument; `W292` passes the
statically resolved target's value through the same argument, so render and check share one precedence.

**Tech Stack:** Django, Pydantic, pytest + pytest-django (+ xdist), lxml.

**Spec:** `superpowers/specs/2026-10-23-context-action-label-mode-design.md` (issue #269)

## Global Constraints

- Attribute name `cv_context_action_label_mode: str | None = None` on `CrudView`, kept as proposed (one letter from
  the dict `cv_context_actions_label_mode`; do not rename).
- Precedence for a context key, first non-`None` wins: calling view's own map naming the key → button `label_mode` →
  resolved map (first non-`None` of view / ViewSet / setting) naming the key → target view's
  `cv_context_action_label_mode` → `"icon"`.
- `location="list"` and cards never read the attribute.
- Nothing set anywhere → byte-identical output; goldens under `tests/test1/golden/` are never regenerated.
- `cv_get_action_label_mode(location, key, button=None, target_default=None)` keeps returning `str`.
- Action-data key: `cv_context_label_mode` (must not be the leaf input `cv_label_mode`).
- Both `base.py` comments carry "Set on" + "Meaning" from the spec's naming table.
- CHANGELOG: `### Added` only. No `### Breaking`; `docs/migrating-1.0.md` untouched.
- Never name downstream / client projects in code, docs, changelog or tests.
- Python 3.12+, line length 120, double quotes, ruff. Run tests with `pytest tests -n auto`.

## Review Focus

- A calling view map that is set but names only *other* keys must not hide the target default → Task 1
  `test_view_map_without_key_yields_to_target`.
- The same update view as a row action must stay icon-only when its toolbar mode is `"label"` → Task 1
  `test_target_mode_does_not_reach_rows`.
- A cross-ViewSet `parent` button follows the parent list view's attribute → Task 1
  `test_parent_button_follows_parent_list_view`.
- A key folded into the action menu still renders icon + short label → Task 1 `test_menu_folded_key_unaffected`.
- Someone puts a dict on the new attribute or a string on the old map: both checks point at the other name → Task 2
  `test_e210_dict_on_target_attribute_names_the_map`, `test_e211_string_on_map_names_target_attribute`.

---

### Task 1: Attribute, action data and resolution

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (attribute + comments near line 87-89; `cv_get_dict()` ~line 416;
  `cv_get_action_label_mode()` ~line 279; `cv_get_context()` ~line 610)
- Test: `tests/test1/test_context_action_label_mode.py` (new; reuse helpers from
  `tests/test1/test_action_label_mode_render.py` and `_with_viewset_buttons` / `_is_text_only` from
  `tests/test1/test_context_button_label_mode.py`)

**Interfaces:**
- Produces: `CrudView.cv_context_action_label_mode: str | None = None`; action data key `cv_context_label_mode`
  (the target's attribute value, present in every `cv_get_dict()` result);
  `cv_get_action_label_mode(cls, location: str, key: str, button: ContextButton | None = None,
  target_default: str | None = None) -> str` — `target_default` is used only for `location == "context"`, only after
  steps 1–3 found nothing, and only if it is not `None`.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_context_action_label_mode.py`

Resolution (class level, `monkeypatch` on `AuthorDetailView` / `cv_author`):
- `test_target_default_used_when_nothing_else_names_key`: `cv_get_action_label_mode("context", "update",
  target_default="label") == "label"`; without `target_default` still `"icon"`.
- `test_target_default_ignored_for_list`: `("list", "update", target_default="label") == "icon"`.
- `test_view_map_naming_key_beats_target`, `test_button_mode_beats_target`, `test_viewset_map_beats_target`,
  `test_setting_beats_target` (monkeypatch `crud_views_settings.context_actions_label_mode`): each level set to
  `"both"` for `"update"`, `target_default="label"` → `"both"`.
- `test_view_map_without_key_yields_to_target`: view map `{"detail": "both"}`, `target_default="label"` → `"label"`.

Data:
- `test_cv_get_dict_carries_target_mode`: with `AuthorUpdateView.cv_context_action_label_mode = "label"`, the
  `cv_get_context("update", obj, user, location="context")` result of a detail view has
  `cv_context_label_mode == "label"` and `cv_label_mode == "label"`.

Rendering (`@pytest.mark.django_db`, `author_douglas_adams`, `_client([AUTHOR_FULL])`):
- `test_toolbar_follows_target_mode`: `AuthorUpdateView` → `"label"`, `AuthorDeleteView` → `"both"`; on the detail
  toolbar `update` is text-only, `delete` has both an `aria-hidden` icon and visible text, `detail` keeps its `title`
  (icon-only).
- `test_target_mode_does_not_reach_rows`: `AuthorDetailView` → `"label"`; the list row `detail` button still has a
  `title` and a `visually-hidden` span.
- `test_registered_button_follows_target`: viewset button `ContextButton(key="edit", key_target="update")`,
  `AuthorDetailView.cv_context_actions = ["edit"]`, `AuthorUpdateView` → `"label"` → `edit` text-only; same with
  `label_mode="icon"` on the button → icon-only.
- `test_home_button_follows_list_view`: `AuthorListView` → `"label"` → `home` on the detail toolbar text-only.
- `test_parent_button_follows_parent_list_view`: `PublisherListView` → `"label"`; on the `BookListView` page of
  `publisher_penguin` (default toolbar `["parent", "list", "filter", "create"]`) the `parent` button is text-only.
- `test_cv_context_button_tag_follows_target`: `AuthorUpdateView` → `"label"`; `{% cv_context_button "update" %}`
  rendered via `_render(view, request, ...)` is text-only.
- `test_menu_folded_key_unaffected`: `AuthorUpdateView` → `"label"`, `AuthorDetailView.cv_context_actions_inline =
  ["detail"]`; the `update` menu item renders byte-identical to the same page without the attribute.
- `test_nothing_set_is_byte_identical`: the detail toolbar bytes equal before and after setting
  `cv_context_action_label_mode = None` explicitly on every Author view (guards against the new data key leaking into
  markup).

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_context_action_label_mode.py -n auto`
Expected: FAIL (`unexpected keyword argument 'target_default'`, missing attribute / data key).

- [ ] **Step 3: Implement in `src/crud_views/lib/view/base.py`**

- Attribute and the two comments (wording per spec "Naming"; the existing `#216` comment line stays for the list map).
- `cv_get_dict()`: add `"cv_context_label_mode": cls.cv_context_action_label_mode` next to `"cv_variant"`.
- `cv_get_action_label_mode()`: add `target_default`; replace the final `mapping.get(key, "icon")` with the
  mapping lookup, then (context only) `target_default`, then `"icon"`. Update the docstring with the new step.
- `cv_get_context()`: pass `target_default=data.get("cv_context_label_mode")` when `location == "context"`.

- [ ] **Step 4: Run to verify they pass, then the whole suite**

Run: `pytest tests/test1/test_context_action_label_mode.py -n auto` then `pytest tests -n auto`
Expected: all PASS, no golden changed (`git status tests/test1/golden` clean).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/base.py tests/test1/test_context_action_label_mode.py
git commit -m "feat(label-mode): target view's cv_context_action_label_mode for the context toolbar (#269)"
```

### Task 2: Checks E210, E211 message, W292

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (CrudView checks next to `variant_check(cls, "cv_action_variant", ...)`,
  ~line 174)
- Modify: `src/crud_views/lib/view/action_menu.py:46-61` (`cv_label_mode_checks` E211 message)
- Modify: `src/crud_views/lib/view/label_mode.py:28` only if the dict hint cannot be added at the call site
- Modify: `src/crud_views/lib/view/buttons.py:368-408` (`cv_icon_mode_checks`, W292)
- Test: `tests/test1/test_context_action_label_mode.py` (append)

**Interfaces:**
- Consumes: `cv_get_action_label_mode(..., target_default=...)` and `cv_context_action_label_mode` from Task 1.

- [ ] **Step 1: Write the failing tests** (reuse `_messages`, `_w292`, `_target` from
  `tests/test1/test_context_button_label_mode.py`)

- `test_e210_invalid_target_attribute`: `AuthorUpdateView.cv_context_action_label_mode = "text"` → one `viewset.E210`
  on `AuthorUpdateView.checks()` containing `"cv_context_action_label_mode"` and `"'text'"`.
- `test_e210_dict_on_target_attribute_names_the_map`: value `{"update": "label"}` → E210 message contains
  `"cv_context_actions_label_mode"`.
- `test_no_e210_for_valid_or_unset_target_attribute`: `None` and each of `"label"`, `"icon"`, `"both"` → no E210.
- `test_e211_string_on_map_names_target_attribute`: `AuthorDetailView.cv_context_actions_label_mode = "label"` →
  E211 message contains `"cv_context_action_label_mode"`.
- `test_w292_silent_with_target_label_mode` (parametrize `"label"`, `"both"`): `_target("update")` has
  `cv_icon_action = None` and that mode → `_w292() == []`.
- `test_w292_explicit_target_icon_still_warns`: icon `None`, target mode `"icon"` → one W292.
- `test_w292_registered_button_follows_target`: icon `None`, target `"label"`, viewset button
  `ContextButton(key="edit", key_target="update")`, `cv_context_actions = ["edit"]` → no W292.
- `test_w292_invalid_target_attribute_does_not_crash`: target value `"text"` → `AuthorDetailView.checks()` runs
  (E210 reports it on the target; W292 treats a non-mode value as unset).

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_context_action_label_mode.py -n auto -k "e210 or e211 or w292"`
Expected: FAIL.

- [ ] **Step 3: Implement**

- E210: `label_mode_check(cls, "cv_context_action_label_mode", value)` when the value is not `None`; for a dict
  value the message adds a hint like `(cv_context_actions_label_mode is the per-key dict of the calling view)`.
- E211: extend the message's parenthesis to also name `cv_context_action_label_mode` as the string-valued target
  default.
- W292: resolve the target class before the mode check (it is already resolved for the warning), then call
  `cls.cv_get_action_label_mode("context", key, target_default=...)` with the target's value if `is_label_mode()`,
  else `None`. Existing skips unchanged.

- [ ] **Step 4: Run to verify they pass, then the whole suite**

Run: `pytest tests/test1/test_context_action_label_mode.py tests/test1/test_context_button_label_mode.py -n auto`
then `pytest tests -n auto`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/base.py src/crud_views/lib/view/action_menu.py src/crud_views/lib/view/buttons.py \
  src/crud_views/lib/view/label_mode.py tests/test1/test_context_action_label_mode.py
git commit -m "feat(checks): E210/E211/W292 know cv_context_action_label_mode (#269)"
```

### Task 3: Docs and changelog

**Files:**
- Modify: `docs/reference/action_menus.md` ("Label mode", lines ~58-97; check table row `viewset.W292` ~line 208)
- Modify: `docs/reference/context_buttons.md` (`label_mode` paragraph ~lines 54-60)
- Modify: `docs/reference/buttons.md:448` (W292 row) only if its wording needs the target level
- Modify: `CHANGELOG.md` (`### Added` of the unreleased section)

- [ ] **Step 1: Write the docs**

`action_menus.md` "Label mode":
- a paragraph introducing `cv_context_action_label_mode` on the *target* view, toolbar only;
- the spec's naming table (Attribute / Type / Set on / Meaning), verbatim columns;
- the precedence list with the target level as step 4;
- qualify the `{}` sentence: a view's `{}` still overrides its ViewSet, but a key it does not name falls to the
  target view's default before `"icon"`;
- an example with generic names:

  ```python
  class ProjectUpdateView(UpdateView):
      cv_action_variant = "tertiary"
      cv_action_short_label_template_code = "Edit"
      cv_context_action_label_mode = "label"  # text in a toolbar, still icon-only in table rows

  class ProjectCreateView(CreateView):
      cv_action_variant = "primary"
      cv_action_short_label_template_code = "New project"
      cv_context_action_label_mode = "both"  # icon + text in a toolbar
  ```
- a sentence that `home`, `parent`, child and sibling buttons follow the view they open, across ViewSets.

`context_buttons.md`: after "A view's own `cv_context_actions_label_mode` that names the key still …", one sentence
that below the maps the target view's `cv_context_action_label_mode` applies, linking to the action-menus table.

`CHANGELOG.md` `### Added`: one bullet for `cv_context_action_label_mode` (#269) naming the precedence position and
the E210/W292 coverage.

- [ ] **Step 2: Verify**

Run: `task check && task format && pytest tests -n auto` and `uv run mkdocs build --strict` (or `task docs`
reachable without warnings)
Expected: clean ruff, all tests PASS, docs build without broken links.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/action_menus.md docs/reference/context_buttons.md docs/reference/buttons.md CHANGELOG.md
git commit -m "docs(label-mode): target-view default for the context toolbar (#269)"
```
