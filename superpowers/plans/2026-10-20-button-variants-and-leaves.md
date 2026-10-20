# Button Variants, Class Table and Leaves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One button mechanism: every action button carries a semantic variant, every button class comes from a
layered table, and the rendering decisions are made once in Python and handed to three presentation-only leaf
templates that themes override without copying logic.

**Architecture:** A new module `crud_views/lib/button_classes.py` owns the flat `location:slot` class table (package
defaults, theme registrations, project setting, cached, reset on `setting_changed`) and the `{% cv_button_class %}`
tag. `crud_views/lib/view/button_data.py` turns a resolved action dict into the leaf contract (`cv_tag`, `cv_href`,
`cv_label_visible`, ...). The existing button templates become one-line logic templates that call
`{% cv_button location %}`, which normalises and renders `tags/button/action.html` or `menu_item.html`; the three
containers include `tags/button/container.html`. The crispy inputs and `formset.js` read the same table.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12+, pydantic, django-crispy-forms 2.x, pytest + pytest-django + lxml,
vitest + jsdom (Node 22), MkDocs.

**Spec:** `superpowers/specs/2026-10-19-button-variants-and-leaves-design.md` — read it alongside this plan. Its
"Builder check" and "Calls I made" sections are decisions, not suggestions.

## Global Constraints

- Baseline is `main` after PR #200 (commit 440ac55). Work on a feature branch.
- Python 3.12+, Django 4.2 / 5.2 / 6.0; the nox matrix must pass (`task test`). For iteration: `pytest tests`.
- Ruff, line length 120, double quotes (`task format`, `task check`).
- JS tests: vitest needs Node 22 on this machine:
  `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run` (plain `npx vitest run` fails on the local Node 20).
- Stock output stays unchanged except the Acceptance table of the spec (and its extension in Task 4 here). The
  goldens are regenerated once (`CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`), after the
  normaliser is extended, and the diff is reviewed line by line against that table.
- The variant vocabulary is closed: `primary`, `secondary`, `tertiary`, `danger`. Plain strings are accepted
  everywhere; a value outside the set is `viewset.E209`.
- The table holds style classes only. Structural classes stay in templates: `dropdown-toggle`, `cv-menu-toggle`,
  `d-none`, `flex-grow-1`, `active`, `visually-hidden`, `dropdown-menu`, `dropdown-menu-end`, `cv-form-ctrl-*`,
  `btn-close` (the one `btn-` token allowed in a template).
- Leaves receive only the contract keys. Custom button templates (`ContextButton.template` / `template_code`,
  whole-template overrides of the thin logic templates, `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE`) keep receiving the raw
  action dict.
- No new dependency. Table values render escaped (they go through `conditional_escape` as `simple_tag` output);
  leaves mark nothing safe.
- Check ids (verified free on the baseline): `viewset.E209`, `crud_views.E360`, `crud_views.E361`,
  `crud_views.W362`.
- Module placement decisions (spec left them to the builder): `crud_views.lib.button_classes` (table),
  `crud_views.lib.view.variant` (`Variant`), `crud_views.lib.view.button_data` (normaliser),
  `crud_views.lib.crispy.buttons` (`Submit`, `Button`, `Reset`). `cv_render_button` is a new tag; the existing
  `cv_render_context_action` / `cv_render_list_action` / `cv_render_card_action` tags stay.
- Commit after every task with a conventional message (`feat(buttons): ...`, `refactor(templates): ...`,
  `test: ...`, `docs: ...`).

## Review Focus

1. **A table entry set to `None` or `""`** (a theme switching the classes off): the element renders with structural
   classes only, never the text `None`. Tests in Task 1 (`get_button_class`) and Task 4 (leaf with an empty
   variant class renders `class="active"`-style attributes without stray tokens).
2. **`override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)` at runtime** (tests, settings reloads): the cached table
   refreshes. Test in Task 1.
3. **A project that overrides `tags/context_action.html` wholesale with 0.30.0 markup**, or uses
   `ContextButton(template_code=...)`: it still receives `cv_url`, `cv_action_label`, `cv_icon_action`, `cv_key` and
   renders inside the container next to stock buttons. Test in Task 4.
4. **A `CardAction(child_name=...)` without a `label`**: today renders the text `None`; the normaliser's card label
   chain ends in `cv_key` (the child name), so the markup never shows `None`. Test in Task 3.
5. **A project that overrides `formsets/control.html` from 0.30.0** (no `data-cv-class*` attributes): the delete
   toggle still flips the hidden `DELETE` input, throws nothing, and leaves the class list alone. Test in Task 5
   (vitest).

---

### Task 1: Button class table, `{% cv_button_class %}` and its checks

**Files:**
- Create: `src/crud_views/lib/button_classes.py`
- Modify: `src/crud_views/templatetags/crud_views.py` (add tag next to `cv_icon`, line 421)
- Modify: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py` (add the same tag next to
  `cv_icon`, line 100)
- Modify: `src/crud_views/checks.py` (new `check_button_classes`, registered like `check_icons`, line 365)
- Test: `tests/test1/test_button_classes.py`, `tests/test1/test_button_classes_checks.py`

**Interfaces:**
- Produces (all in `crud_views.lib.button_classes`):
  - `DEFAULT_BUTTON_CLASSES: dict[str, str]` — exactly the spec's "Default table" (section 2), 30 keys:
    `context:primary|secondary|tertiary|danger` = `btn btn-outline-primary btn-lg`;
    `list:primary|secondary|tertiary|danger` = `btn btn-outline-primary btn-xs`;
    `card:primary` = `btn btn-primary btn-sm`; `card:secondary`, `card:danger` = `btn btn-secondary btn-sm`;
    `card:tertiary` = `btn btn-outline-secondary btn-sm`;
    `context:container` = `btn-group btn-group-lg`; `list:container` = `btn-group btn-group-xs`;
    `card:container` = `d-flex gap-2`;
    `context:menu-toggle` = `btn btn-outline-primary btn-lg`; `list:menu-toggle` = `btn btn-outline-primary btn-xs`;
    `card:menu-toggle` = `btn btn-secondary btn-sm`;
    `context:menu-wrapper`, `list:menu-wrapper` = `btn-group`; `card:menu-wrapper` = `dropdown`;
    `menu:item` = `dropdown-item`;
    `form:submit` = `btn btn-primary`; `form:cancel` = `btn btn-secondary`; `form:delete` = `btn btn-primary`;
    `form:filter-submit` = `btn btn-primary`; `form:filter-reset` = `btn btn-secondary`;
    `formset:control` = `btn btn-light`; `formset:container` = `btn-group`;
    `formset:control-danger` = `btn btn-danger`;
    `card-order:toggle` = `btn btn-outline-secondary`; `card-order:container` = `btn-group btn-group-sm`;
    `language:toggle` = `btn btn-outline-secondary`;
    `object-detail:property-detail` = `btn btn-link p-0 ms-1 align-baseline text-muted`.
  - `REMOVED_SETTINGS: dict[str, str]` =
    `{"CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS": 'CRUD_VIEWS_BUTTON_CLASSES["form:filter-reset"]'}`.
  - `register_button_classes(classes: dict[str, str | None]) -> None` — theme API, merges into the module-level
    `_THEME_BUTTON_CLASSES`, resets the cache.
  - `get_button_classes() -> dict[str, str | None]` — `DEFAULT_BUTTON_CLASSES ⊕ _THEME_BUTTON_CLASSES ⊕
    settings.CRUD_VIEWS_BUTTON_CLASSES` (per-key, later wins), cached in a module global; reset by
    `reset_button_classes_cache()`, which a `setting_changed` receiver calls for `CRUD_VIEWS_BUTTON_CLASSES`.
  - `get_button_class(location: str, slot: str) -> str` — the resolved value of `f"{location}:{slot}"`; `""` for
    `None`, `""`, an unknown key, or a non-str value.
  - `button_class_check_messages() -> list[CheckMessage]` — `crud_views.E360` per name in `REMOVED_SETTINGS` still
    defined in Django settings (hint names the replacement); `crud_views.E361` per resolved value that is neither
    `str` nor `None` (`Button class 'k' = v!r is not a str.`); `crud_views.W362` per key in the theme layer or in
    `CRUD_VIEWS_BUTTON_CLASSES` that is not in `DEFAULT_BUTTON_CLASSES` (`Button class 'k' is not a known key
    (typo?).`, hint lists nothing, the docs page is the reference).
- Produces: template tag `{% cv_button_class "form" "submit" %}` / `{% cv_button_class cv_location cv_variant %}` in
  both tag libraries, a `simple_tag` returning `get_button_class(location, slot)` (a plain `str`, so Django escapes
  it). Produces `check_button_classes(app_configs=None, **kwargs)` in `crud_views.checks`, `@register(TAG)`, returning
  `button_class_check_messages()`.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_classes.py`, with an autouse fixture that
  snapshots and restores `_THEME_BUTTON_CLASSES` and calls `reset_button_classes_cache()` (copy the shape of
  `_isolate_registry` in `tests/test1/test_icons_registry.py`):
  - `test_default_table_is_complete`: `set(DEFAULT_BUTTON_CLASSES) == {the 30 keys above}` and
    `get_button_class("context", "primary") == "btn btn-outline-primary btn-lg"`,
    `get_button_class("card", "danger") == "btn btn-secondary btn-sm"`, `get_button_class("menu", "item") ==
    "dropdown-item"`.
  - `test_unknown_key_renders_nothing`: `get_button_class("context", "nope") == ""`.
  - `test_none_and_empty_switch_off`: `override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": None,
    "form:cancel": ""})` → both `""`.
  - `test_theme_layer_then_settings_win`: `register_button_classes({"list:danger": "btn btn-ghost-danger"})` →
    resolved; then `override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:danger": "btn btn-x"})` → `"btn btn-x"`;
    after the `with` block the theme value is back (cache reset on `setting_changed`).
  - `test_cache_resets_on_registration`: call `get_button_classes()`, then `register_button_classes(...)`, then
    `get_button_class` sees the new value.
  - `test_tag_in_both_libraries_escapes`: `Template('{% load crud_views %}{% cv_button_class "form" "submit" %}')`
    renders `btn btn-primary`; same with `{% load crud_views_object_detail %}`; with
    `override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": '"><x'})` the output is `&quot;&gt;&lt;x`.
  - In `tests/test1/test_button_classes_checks.py` (shape of `tests/test1/test_icons_checks.py`):
    `test_default_config_has_no_messages` (`check_button_classes() == []`),
    `test_e360_removed_setting` (`override_settings(CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS="x")` → ids
    `["crud_views.E360"]`, msg names the setting, hint contains `form:filter-reset`),
    `test_e361_non_str` (`{"form:submit": 3}` → `["crud_views.E361"]`),
    `test_w362_unknown_key_in_settings` (`{"form:sumbit": "btn"}` → `["crud_views.W362"]`, msg contains
    `form:sumbit`), `test_w362_unknown_key_in_theme` (via `register_button_classes`).
- [ ] **Step 2: Run** `pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -v` —
  Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** `src/crud_views/lib/button_classes.py` (mirror `icons.py` lines 83-120 for cache, receiver
  and registration), the two tags, and `check_button_classes` in `checks.py`.
- [ ] **Step 4: Run** the two test files plus `pytest tests/test1/test_icons_checks.py tests/test1/test_expand_checks.py
  -v` — Expected: PASS (the check registry gained one function; no other check output changes).
- [ ] **Step 5: Commit** `git commit -m "feat(buttons): button class table, cv_button_class tag and checks E360/E361/W362"`

---

### Task 2: Variants on views, context buttons and card actions

**Files:**
- Create: `src/crud_views/lib/view/variant.py`
- Modify: `src/crud_views/lib/view/base.py` (class attribute after line 105; `cv_get_dict` line 361; `checks()`
  after the E207 block, line 158)
- Modify: `src/crud_views/lib/view/buttons.py` (`ContextButton` field line 23; `_apply_variant` next to
  `_apply_label` line 56; call it after every `_apply_label` call: lines 104, ~173, ~221, ~277, 315;
  `context_button_checks` line 333)
- Modify: `src/crud_views/lib/view/card.py` (`variant: str | None = None`)
- Modify: `src/crud_views/lib/views/card.py` (`cv_get_card_action_data` lines 56 and 75; `checks()` line 96)
- Modify: `src/crud_views/lib/views/create.py:26`, `src/crud_views/lib/views/delete.py:48`,
  `src/crud_views_polymorphic/lib/create_select.py:43` (add `cv_action_variant` under `cv_icon_action`)
- Modify: `src/crud_views/lib/view/__init__.py` (export `Variant`)
- Test: `tests/test1/test_variants.py`

**Interfaces:**
- Produces: `crud_views.lib.view.variant.Variant(StrEnum)` with `PRIMARY = "primary"`, `SECONDARY = "secondary"`,
  `TERTIARY = "tertiary"`, `DANGER = "danger"`; `VARIANTS: frozenset[str]` of the four values;
  `is_variant(value: object) -> bool`; `variant_check(context, owner: str, value) -> CheckExpression` returning a
  `CheckExpression(id="E209", expression=is_variant(value), msg=f"{owner} variant must be one of
  ['danger', 'primary', 'secondary', 'tertiary'], got {value!r}")`.
- Produces: `CrudView.cv_action_variant: str = "secondary"`; `CreateView`, `PolymorphicCreateSelectView` set
  `"primary"`, `DeleteView` sets `"danger"`. `cv_get_dict()` adds `"cv_variant": cls.cv_action_variant` (before
  `data.update(extra)`, so `extra` can override).
- Produces: `ContextButton.variant: str | None = None`; `ContextButton._apply_variant(data: dict) -> None` sets
  `data["cv_variant"] = self.variant` when not `None`. Every `get_context` in `buttons.py` calls it right after
  `_apply_label` (the filter button included; its dict then carries `cv_variant` only when declared).
- Produces: `CardAction.variant: str | None = None`; `cv_get_card_action_data` sets
  `cv_variant = action.variant if action.variant is not None else cls.cv_action_variant` (child actions:
  `child_cls.cv_action_variant`).
- Produces: `viewset.E209` from `CrudView.checks()` (`cv_action_variant`), from `context_button_checks` (every
  configured button, defaults included, whose `variant` is not `None`), and from `CardListView.checks()` (every
  `CardAction.variant` not `None`).
- Consumes: nothing from Task 1 (the templates still map variants themselves; output is unchanged in this task).

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_variants.py`:
  - `test_view_defaults`: `CreateView.cv_action_variant == "primary"`, `PolymorphicCreateSelectView` `"primary"`,
    `DeleteView` `"danger"`, each of `UpdateView`, `DetailView`, `ListView`, `OrderedUpView`, `ManageView`,
    `CardListView` `"secondary"`; `Variant.DANGER == "danger"`.
  - `test_cv_get_dict_carries_variant` (db): render the author list with `client_user_author_all_perms` (see
    `test_card.py`), take `view = response.context["view"]`, then
    `[ctx["cv_variant"] for _, ctx in view.cv_resolved_actions(["detail", "update", "delete"], author)] ==
    ["secondary", "secondary", "danger"]`.
  - `test_context_button_override` (db): `ContextButton(key="x", key_target="update", variant="danger")
    .get_context(ctx)["cv_variant"] == "danger"`; without `variant` it is `"secondary"`; the same for
    `ChildContextButton` (publisher → book list: `"secondary"`, with `variant="primary"` → `"primary"`).
  - `test_card_action_fallback` (db): on an `AuthorCardListView` instance, `cv_get_card_action_data(CardAction(
    key="delete", no_label=True), obj, user)["cv_variant"] == "danger"`; with `variant="tertiary"` →
    `"tertiary"`; `CardAction(child_name="book", child_key="list")` on `PublisherCardListView` → `"secondary"`.
  - `test_e209_view`, `test_e209_context_button`, `test_e209_card_action`: `monkeypatch.setattr(AuthorUpdateView,
    "cv_action_variant", "huge")` → `[m.id for c in AuthorUpdateView.checks() for m in c.messages()]` contains
    `"viewset.E209"` and the message contains `'huge'`; `cv_context_buttons = [ContextButton(key="x",
    key_target="update", variant="nope")]` on `AuthorDetailView`; `cv_card_actions = [CardAction(key="detail",
    variant="loud")]` on `AuthorCardListView`. A valid value yields no E209.
  - `test_stock_card_output_unchanged` (db): the author card page still renders the delete button with
    `btn-outline-secondary` (explicit tertiary) and the update button with `btn-secondary`.
- [ ] **Step 2: Run** `pytest tests/test1/test_variants.py -v` — Expected: FAIL (`ImportError: Variant`).
- [ ] **Step 3: Implement** the module, attributes, `_apply_variant`, card fallback and the three E209 sites.
- [ ] **Step 4: Run** `pytest tests/test1/test_variants.py tests/test1/test_card.py tests/test1/test_action_menus_card.py
  tests/test1/test_context_button_check.py tests/test1/test_unknown_attribute_check.py -v` — Expected: PASS
  (`cv_action_variant` is a declared `cv_` attribute, so W280 does not fire).
- [ ] **Step 5: Commit** `git commit -m "feat(buttons): cv_action_variant, ContextButton.variant, CardAction.variant and viewset.E209"`

---

### Task 3: The normaliser `cv_button_data`

**Files:**
- Create: `src/crud_views/lib/view/button_data.py`
- Test: `tests/test1/test_button_data.py`

**Interfaces:**
- Produces: `cv_button_data(ctx: dict, location: str) -> dict` and `LEAF_KEYS: frozenset[str]` (the contract key
  names). `location` must be `"context"`, `"list"` or `"card"`; anything else raises `ValueError`. Input is a
  resolved action dict (`cv_resolve_action` output; hidden actions never reach it). Output has exactly these keys
  (absent ones are absent, not `None`):

  | Key | Rule |
  |---|---|
  | `cv_location` | `location` |
  | `cv_disabled`, `cv_disabled_reason` | `bool(ctx.get("cv_disabled"))`, `ctx.get("cv_disabled_reason", "")` |
  | `cv_tag` | `"button"` when disabled, or when `cv_list_action_method == "post"` and not `cv_modal`; else `"a"` |
  | `cv_href` | `ctx["cv_url"]` only when `cv_tag == "a"` |
  | `cv_submit_target` | `f"cv_form_{ctx['cv_oid']}"` only when `cv_tag == "button"` and not disabled |
  | `cv_modal`, `cv_modal_size` | `bool(ctx.get("cv_modal")) and not disabled`; `ctx.get("cv_modal_size", "")` |
  | `cv_active` | `bool(ctx.get("cv_is_active")) and not disabled`, every location |
  | `cv_key` | `ctx.get("cv_key", "")` |
  | `cv_label` | card: first truthy of `cv_label`, `cv_action_short_label`, `cv_action_label`, `cv_key`; context and list: `ctx.get("cv_action_label", "")` |
  | `cv_short_label` | card: same as `cv_label`; context and list: first truthy of `cv_action_short_label`, `cv_action_label` |
  | `cv_label_visible` | card: `bool(cv_label) and not ctx.get("cv_no_label")`; else `False` |
  | `cv_title` | only when not `cv_label_visible`: `cv_label` |
  | `cv_icon` | `ctx.get("cv_icon_action")` (may be `None`) |
  | `cv_variant` | `ctx.get("cv_variant") or "secondary"` |
  | `cv_flex` | card: `bool(ctx.get("cv_flex"))`; else `False` |

  Never mutates `ctx`. These keys are the public leaf contract (documented in Task 7).

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_data.py`, plain unit tests, no Django
  rendering, parametrized over the three locations where the rule is shared:
  - GET: `{"cv_url": "/u/", "cv_key": "detail", "cv_action_label": "Show", "cv_action_short_label": "Detail",
    "cv_list_action_method": "get", "cv_disabled": False, "cv_oid": "o1", "cv_icon_action": "detail",
    "cv_variant": "primary"}` → `cv_tag == "a"`, `cv_href == "/u/"`, `"cv_submit_target" not in data`,
    `cv_modal is False`, `cv_title == "Show"` (context/list) and `cv_short_label == "Detail"`.
  - POST without modal → `cv_tag == "button"`, `cv_submit_target == "cv_form_o1"`, no `cv_href`.
  - POST with modal (`cv_modal: True, cv_modal_size: "lg"`) → `cv_tag == "a"`, `cv_href`, `cv_modal is True`,
    `cv_modal_size == "lg"`, no `cv_submit_target`.
  - Disabled (`cv_disabled: True, cv_disabled_reason: "permission", cv_url: None, cv_modal: True`) → `cv_tag ==
    "button"`, no `cv_href`, no `cv_submit_target`, `cv_modal is False`, `cv_active is False`.
  - Active (`cv_is_active: True`) → `cv_active is True` for every location; with `cv_disabled: True` → `False`.
  - Card labels: `{"cv_label": "Details", "cv_no_label": False, ...}` → `cv_label == "Details"`,
    `cv_label_visible is True`, `"cv_title" not in data`; `cv_no_label: True` → `cv_label_visible is False`,
    `cv_title == "Details"`; `{"cv_label": None, "cv_key": "book"}` (child action without label) → `cv_label ==
    "book"`, no `"None"` anywhere in `data.values()`.
  - Context/list labels never visible: `cv_label_visible is False`, `cv_title == cv_action_label`.
  - `cv_flex`: `{"cv_flex": True}` → `True` for card, `False` for context and list.
  - `cv_variant` defaults to `"secondary"` when missing (the filter button's dict).
  - `cv_button_data(ctx, "toolbar")` raises `ValueError`; `ctx` is unchanged after the call
    (`copy.deepcopy` compare); `set(data) <= LEAF_KEYS`.
- [ ] **Step 2: Run** `pytest tests/test1/test_button_data.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** `cv_button_data` and `LEAF_KEYS`.
- [ ] **Step 4: Run** `pytest tests/test1/test_button_data.py -v` — Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(buttons): cv_button_data normaliser and the leaf contract"`

---

### Task 4: Leaves, thin logic templates, unified containers, regenerated goldens

**Files:**
- Create: `src/crud_views/templates/crud_views/tags/button/action.html`, `.../tags/button/menu_item.html`,
  `.../tags/button/container.html`
- Modify (thin): `.../tags/context_action.html`, `.../tags/list_action.html`, `.../tags/card_action.html`,
  `.../tags/actions_menu_item.html`
- Modify: `.../tags/actions_menu_item_label.html` (contract keys), `.../tags/actions_menu.html`,
  `.../tags/actions_menu_toggle.html` (classes from the table), `.../tags/context_action_filter.html` (line 3),
  `.../tags/context_actions.html`, `.../columns/actions.html`, `.../tags/card.html` (container include, no
  `group is None` branch)
- Modify: `src/crud_views/templatetags/crud_views.py` (`_ACTIONS_MENU_STYLE` lines 146-150 deleted;
  `cv_actions_menu` lines 153-165; new `cv_button`, `cv_render_button`)
- Modify: `src/crud_views/lib/view/base.py` (`cv_get_list_action_group` line 503, `cv_get_context_action_group`
  line 510), `src/crud_views/lib/views/card.py` (`cv_get_card_action_group` line 78)
- Modify: `tests/test1/test_action_menus_golden.py` (`_norm` line 38; canonical attribute and class order),
  `tests/test1/golden/action_menus/*.html` (regenerated), `tests/test1/test_card_action_post.py:45-50`
- Test: `tests/test1/test_button_leaves.py`

**Interfaces:**
- Consumes: `cv_button_data`, `LEAF_KEYS` (Task 3); `{% cv_button_class %}` (Task 1); `cv_variant` in every dict
  (Task 2).
- Produces: tag `{% cv_button location %}` / `{% cv_button location kind="menu-item" %}` (`simple_tag`,
  `takes_context=True`): `data = cv_button_data(context.flatten(), location)`, rendered with `render_to_string`
  of `crud_views/tags/button/action.html` (kind `"action"`, the default) or `crud_views/tags/button/menu_item.html`
  (kind `"menu-item"`) with `data` as the whole context. The leaves `{% load crud_views %}` themselves.
- Produces: tag `{% cv_render_button ctx location %}` (`simple_tag`, `takes_context=True`): renders a resolved dict
  the way the per-key tags do: `"context"` → `_render_context_action(context, ctx)` (custom `cv_template` /
  `cv_template_code` honoured); `"list"` → `render_to_string(f"{crud_views_settings.theme_path}/tags/list_action.html",
  ctx, request=context["request"])`; `"card"` → the same with `tags/card_action.html` (the request makes the
  `{% csrf_token %}` of the included hidden form work). Returns `""` for a falsy `ctx`.
- Produces: `cv_actions_menu(context, group, location)` returns `{"cv_menu_items", "cv_location", "cv_menu_icon"}`
  only (`cv_menu_wrapper_class` and `cv_toggle_class` are gone: breaking for theme overrides of
  `actions_menu_toggle.html` / `actions_menu.html`, changelog line in Task 7).
- Produces: `cv_get_list_action_group(obj) -> ActionGroup`, `cv_get_context_action_group(obj=None) -> ActionGroup`,
  `cv_get_card_action_group(obj) -> ActionGroup` — never `None`: when the inline keys are `None`,
  `ActionGroup(inline=[ctx for _, ctx in items], menu=[])`. `cv_split_actions` is unchanged (its `None` return is
  tested in `test_action_menus_split.py`).
- Produces the three leaves (presentation only; attribute order inside is the builder's, then frozen by the
  goldens):
  - `action.html`: one `<{{ cv_tag }}>` with `class="{% cv_button_class cv_location cv_variant %}{% if cv_active %}
    active{% endif %}{% if cv_flex %} flex-grow-1{% endif %}"`; `href="{{ cv_href }}"` for `a`, `type="button"` for
    `button`; `disabled data-cv-disabled="{{ cv_disabled_reason }}"` when disabled;
    `data-cv-action="submit-form" data-cv-target="{{ cv_submit_target }}"` when `cv_submit_target`;
    `data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"` when `cv_modal`; `aria-current="page"` when
    `cv_active`; `title="{{ cv_title }}"` when `cv_title`; `cv-key="{{ cv_key }}"` always. Content: when
    `cv_label_visible` → `<span>{{ cv_label }}</span>` and no icon; else `{% cv_icon cv_icon %}<span
    class="visually-hidden">{{ cv_label }}</span>`.
  - `menu_item.html`: `<{{ cv_tag }}>` with `class="{% cv_button_class "menu" "item" %}{% if cv_active %}
    active{% endif %}"`, the same attribute rules, `title` only when `cv_location == "context"`, content
    `{% include "crud_views/tags/actions_menu_item_label.html" %}`.
  - `actions_menu_item_label.html` (rewritten, same output): `{% if cv_icon %}{% cv_icon cv_icon css="cv-icon-fw" %}
    {% else %}<span class="cv-icon-fw d-inline-block" aria-hidden="true"></span>{% endif %} {{ cv_short_label }}`
    (keep the single space before the label as today).
  - `container.html`, included with `cv_buttons`, `cv_group`, `cv_location`, `cv_container_tag`:
    `<{{ cv_container_tag }} class="{% cv_button_class cv_location 'container' %}"{% if cv_container_tag == "fieldset"
    %} aria-label="Actions"{% endif %} cv-{{ cv_location }}-container="true">{% for ctx in cv_buttons %}{%
    cv_render_button ctx cv_location %}{% endfor %}{% cv_actions_menu cv_group cv_location %}</{{ cv_container_tag }}>`.
- Produces the thin logic templates: `context_action.html` = `{% load crud_views %}{% cv_button "context" %}`;
  `list_action.html` = `{% load crud_views %}{% cv_button "list" %}`; `card_action.html` = `{% load crud_views %}
  {% include "crud_views/tags/list_action_form.html" %}{% cv_button "card" %}`; `actions_menu_item.html` =
  `{% load crud_views %}{% cv_button cv_location kind="menu-item" %}`.
- Produces the containers: `context_actions.html` renders `{% for ctx in group.all %}{% cv_render_list_action_form
  ctx %}{% endfor %}` then includes the container leaf with `cv_buttons=group.inline cv_group=group
  cv_location="context" cv_container_tag="fieldset"` (inside the existing `{% if view.cv_context_actions %}`);
  `columns/actions.html` the same with `"list"`; `card.html` keeps its card markup and renders, in place of the
  `d-flex` div, the forms for `group.menu` then the container leaf with `cv_location="card"
  cv_container_tag="div"` (inline card buttons still render their own form inside `card_action.html`).
- Produces `tags/actions_menu.html` / `actions_menu_toggle.html` using `{% cv_button_class cv_location
  "menu-wrapper" %}` and `class="{% cv_button_class cv_location "menu-toggle" %} dropdown-toggle cv-menu-toggle"`;
  `context_action_filter.html` line 3 becomes `class="{% cv_button_class "context" "secondary" %}"`.
- Produces the golden canonical form: `_norm` additionally sorts each element's attributes by name and the tokens
  of every `class` attribute (apply to the lxml node before `tostring`, recursively; `_fragments` passes nodes
  through it). Order is not part of the contract.

- [ ] **Step 1: Canonicalise the goldens first, with no template change.** Extend `_norm` / `_fragments` as above,
  run `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`, check with `git diff --stat
  tests/test1/golden` that only ordering changed (`git diff -w` shows attribute reorderings only), run the golden
  test without the variable — Expected: PASS. Commit:
  `git commit -m "test(goldens): canonical attribute and class order in the action menu goldens"`.
- [ ] **Step 2: Write the failing tests** in `tests/test1/test_button_leaves.py`:
  - `test_action_leaf_renders_from_contract_only`: `render_to_string("crud_views/tags/button/action.html",
    {contract dict for a GET context button with cv_active True, cv_icon "detail"})` → one `a` with
    `href`, `class == "btn btn-outline-primary btn-lg active"`, `aria-current == "page"`, `title`, `cv-key`,
    an `<i>` and a `visually-hidden` span; a card dict with `cv_label_visible True` → `<span>Details</span>` and
    no `<i>`; a POST dict → `button[type=button][data-cv-action=submit-form][data-cv-target=cv_form_o1]` and no
    `href`; a disabled dict → `button[disabled][data-cv-disabled=permission]`, no modal attributes.
  - `test_action_leaf_with_empty_variant_class` (Review Focus 1): `override_settings(CRUD_VIEWS_BUTTON_CLASSES=
    {"context:secondary": None})`, active → `class` attribute equals `"active"` after `.strip()` and `"None"`
    not in the output.
  - `test_menu_item_leaf_title_only_for_context`: list location → no `title`; context → `title`.
  - `test_container_div_has_no_aria_label`: render the container leaf with `cv_container_tag="div"`,
    `cv_location="card"`, `cv_buttons=[]`, `cv_group=ActionGroup()` → `<div class="d-flex gap-2"
    cv-card-container="true">`, no `aria-label`; with `"fieldset"` and `"list"` → `aria-label="Actions"`.
  - `test_group_always_returned` (db): `AuthorListView` instance with `cv_list_actions_inline=None` →
    `cv_get_list_action_group(obj)` is an `ActionGroup` with 3 inline items and empty menu; the rendered list page
    has no `.cv-menu-toggle`. Same for the context toolbar and the author card.
  - `test_card_post_action_is_a_button` (db): author card page with `CardAction(key="ping", label="Ping")` added
    (see `test_action_menus_golden.py::test_cards_author_full`) → `button[data-cv-action='submit-form']` inside
    `.d-flex.gap-2`, no `a[href='#']`, the hidden form before the button, every card button has `cv-key`.
  - `test_card_menu_forms_before_row` (db): with `cv_card_actions_inline=["detail"]` and the `ping` action, the
    `form#cv_form_author_ping_*` is a preceding sibling of the `.d-flex.gap-2` div, not inside it.
  - `test_active_context_button_has_aria_current` (db): author detail toolbar → `a[cv-key=detail]` has
    `aria-current="page"` and `active`; `a[cv-key=update]` has neither.
  - `test_custom_template_button_in_container` (db, Review Focus 3): `monkeypatch` `AuthorDetailView.
    cv_context_buttons` to the defaults plus `ContextButton(key="pill", key_target="update",
    template_code='<a href="{{ cv_url }}" class="pill" cv-key="{{ cv_key }}">{% load crud_views %}{% cv_icon
    cv_icon_action %}{{ cv_action_label }}</a>')` and `cv_context_actions` including `"pill"` → the toolbar
    fieldset contains `a.pill[cv-key=pill]` with the update URL and an `<i>`, next to the stock buttons; with
    `cv_context_actions_inline=["detail"]` it is still inline (not foldable).
  - `test_theme_registration_changes_rendered_classes` (db): `register_button_classes({"list:secondary":
    "btn btn-ghost"})` → list row `a[cv-key=detail]` class is `btn btn-ghost`; with `override_settings(
    CRUD_VIEWS_BUTTON_CLASSES={"list:secondary": "btn btn-x"})` the setting wins.
  - `test_no_raw_keys_reach_leaves`: render `Template('{% load crud_views %}{% cv_button "context" %}')` with a
    raw dict that also has `cv_template_code` and `cv_oid`; patch `render_to_string` (`crud_views.templatetags.
    crud_views.render_to_string`) with a spy and assert `set(call.kwargs["context"] or call.args[1]) <= LEAF_KEYS`.
- [ ] **Step 3: Run** `pytest tests/test1/test_button_leaves.py -v` — Expected: FAIL (`TemplateDoesNotExist`).
- [ ] **Step 4: Implement** the tags, leaves, thin templates, containers, menu classes, group methods and the filter
  template class. Update `tests/test1/test_card_action_post.py` lines 45-50: select
  `button[data-cv-action='submit-form']`, assert no `href` attribute, keep the form and `csrf` assertions.
- [ ] **Step 5: Regenerate the goldens once**: `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py`,
  then review `git diff tests/test1/golden`. The only allowed differences, each matching the spec's Acceptance
  table: (a) card buttons gain `cv-key` (`cards_*`); (b) the card `ping` POST action is `<button type="button"
  data-cv-action="submit-form" data-cv-target="…">` without `href` (`cards_author_full`); (c) `a[cv-key=detail]` in
  `toolbar_detail_full` gains `aria-current="page"`; (d) the card row `div` gains `cv-card-container="true"`
  (`cards_*`); (e) nothing else — the `cards_*` goldens have no menu, so no form moves there. Any other hunk is a
  bug in a leaf: fix the leaf, regenerate, review again.
- [ ] **Step 6: Run** `pytest tests -q` — Expected: PASS, including `test_card.py`, `test_action_menus_*.py`,
  `test_context_actions_post.py`, `test_inaccessible_actions_card.py`, `test_template_a11y.py`,
  `test_icons_templates.py` and the examples project tests, all unmodified except `test_card_action_post.py`.
- [ ] **Step 7: Commit** `git commit -m "refactor(templates): button leaves, thin logic templates and one container per location"`

---

### Task 5: Remaining templates, `formset.js`, guard and completeness tests

**Files:**
- Modify: `src/crud_views/templates/crud_views/formsets/control.html` (lines 5, 7, 8, 12, 18, 19, 24),
  `.../snippets/card_order.html` (lines 12, 14, 19), `.../snippets/language_selector.html` (line 5),
  `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/card-rows/property.html` (line 6)
- Modify: `src/crud_views/static/crud_views/js/formset.js` (`set_delete`, lines 438-446)
- Modify: `tests/js/helpers/dom.js` (line 61), `tests/js/formset.test.js` (lines 101-113)
- Test: `tests/test1/test_button_classes_templates.py`

**Interfaces:**
- Consumes: `{% cv_button_class %}` and `DEFAULT_BUTTON_CLASSES` (Task 1).
- Produces: `formsets/control.html` with `class="{% cv_button_class 'formset' 'container' %}"` on the three
  fieldsets, `class="{% cv_button_class 'formset' 'control' %} cv-form-ctrl-up"` etc. on the four buttons, and on
  the delete button additionally `data-cv-class="{% cv_button_class 'formset' 'control' %}"
  data-cv-class-danger="{% cv_button_class 'formset' 'control-danger' %}"`.
- Produces: `card_order.html` fieldset `class="{% cv_button_class 'card-order' 'container' %}"`, buttons
  `class="{% cv_button_class 'card-order' 'toggle' %}{% if cv_order_dir == 'asc' %} active{% endif %}"` (and
  `desc`); `language_selector.html` `class="{% cv_button_class 'language' 'toggle' %} dropdown-toggle"`;
  `property.html` `class="{% cv_button_class 'object-detail' 'property-detail' %}"` (the template already loads
  `crud_views_object_detail`, which has the tag since Task 1).
- Produces: `XForm.set_delete(value)` in `formset.js` reads `data-cv-class` and `data-cv-class-danger` from the
  delete button; marking removes every token of `data-cv-class` and adds every token of `data-cv-class-danger`
  (jQuery `removeClass` / `addClass` accept space-separated strings); un-marking does the reverse. When either
  attribute is missing the class list is left alone; the hidden `DELETE` input toggles as before. No class literal
  remains in the file.
- Produces the guard test and the completeness test.

- [ ] **Step 1: Write the failing Python tests** in `tests/test1/test_button_classes_templates.py`:
  - `test_no_button_class_literal_in_shipped_templates_python_or_js`: scan `SRC.glob("*/templates/**/*.html")`,
    `SRC.glob("*/static/**/*.js")` and `SRC.glob("**/*.py")` (`SRC` as in `test_icons_template_names.py`), with
    `re.compile(r"(?<![\w-])btn(?:-[\w-]+)?(?![\w-])")`, ignore the token `btn-close` and the file
    `crud_views/lib/button_classes.py`; assert the set of offending `(file, token)` pairs is empty. Minified or
    vendored files under `static/*/vendor/` are excluded.
  - `test_every_literal_slot_in_templates_is_a_default_key`: regex
    `\{%\s*cv_button_class\s+(["'])([^"']+)\1\s+(["'])([^"']+)\3` over the shipped templates; every
    `f"{m.group(2)}:{m.group(4)}"` is in `DEFAULT_BUTTON_CLASSES`; assert at least 20 literal pairs were found.
  - `test_formset_controls_from_table` (render `formsets/control.html` as
    `test_template_a11y.py::test_formset_controls_have_labels_and_hidden_icons` does): the three fieldsets have
    class `btn-group`, the four buttons `btn btn-light …`, the delete button has `data-cv-class="btn btn-light"`
    and `data-cv-class-danger="btn btn-danger"`; with `override_settings(CRUD_VIEWS_BUTTON_CLASSES=
    {"formset:control": "x-ctrl", "formset:control-danger": "x-danger"})` both attributes follow.
  - `test_card_order_and_language_from_table` (db): the publisher order card page
    (`PublisherOrderCardListView`, see `test_card_order.py` for the URL and fixtures) renders the direction
    buttons with `btn btn-outline-secondary` and the active one with `active`; the language selector snippet
    rendered through `{% cv_language_selector %}` (see `test_i18n.py`) has `btn btn-outline-secondary
    dropdown-toggle`.
- [ ] **Step 2: Run** `pytest tests/test1/test_button_classes_templates.py -v` — Expected: FAIL (literals found,
  attributes missing).
- [ ] **Step 3: Write the failing JS test**: in `tests/js/helpers/dom.js` line 61 give the delete button
  `class="x-ctrl cv-form-ctrl-delete" data-cv-class="x-ctrl" data-cv-class-danger="x-danger"`; in
  `tests/js/formset.test.js` lines 101-113 assert after the first `delete()`: `classList.contains("x-danger")` and
  not `"x-ctrl"`, and `cv-form-ctrl-delete` still present; after the second: `"x-ctrl"` back, `"x-danger"` gone.
  Add `it("delete() without data-cv-class attributes only toggles the input", ...)` (Review Focus 5): remove both
  attributes from the button before calling `delete()`; the class list is unchanged, `DELETE` is `"1"`, no throw.
- [ ] **Step 4: Run** `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run tests/js/formset.test.js` —
  Expected: FAIL (`btn-danger` added instead of `x-danger`).
- [ ] **Step 5: Implement** the four templates and `set_delete`.
- [ ] **Step 6: Run** `pytest tests/test1/test_button_classes_templates.py tests/test1/test_template_a11y.py
  tests/test1/test_card_order.py tests/test1/test_formsets.py -v` and the vitest command for the whole suite
  (`... vitest.mjs run`) — Expected: PASS.
- [ ] **Step 7: Commit** `git commit -m "feat(buttons): formset, card order, language and object detail buttons from the table; btn guard test"`

---

### Task 6: Crispy buttons from the table, `CrispyDeleteForm.get_delete_button()`, removals

**Files:**
- Create: `src/crud_views/lib/crispy/buttons.py`
- Modify: `src/crud_views/lib/crispy/form.py` (lines 3, 59-82, 121-133), `src/crud_views/lib/crispy/__init__.py`
- Modify: `src/crud_views/lib/views/list.py` (lines 69-78)
- Modify: `src/crud_views/lib/settings.py` (delete lines 61-63, `filter_reset_button_css_class`)
- Modify: `src/crud_views/templatetags/crud_views.py` (delete `cv_cancel_button`, `cv_submit_button`,
  `cv_delete_button`, lines 263-280)
- Delete: `src/crud_views/templates/crud_views/tags/button_submit.html`, `button_cancel.html`, `button_delete.html`
- Modify: `tests/test1/test_cancel_origin.py` (`render_cancel_tag`, lines 32-39)
- Test: `tests/test1/test_crispy_buttons.py`

**Interfaces:**
- Consumes: `get_button_class` (Task 1).
- Produces (`crud_views.lib.crispy.buttons`, re-exported from `crud_views.lib.crispy`):
  `class Submit(crispy_forms.layout.Submit)`, `class Button(crispy_forms.layout.Button)`,
  `class Reset(crispy_forms.layout.Reset)`, each with a class attribute `slot` (`"form:submit"`, `"form:cancel"`,
  `"form:filter-reset"`) and `__init__(self, name, value, *, slot: str | None = None, **kwargs)` that sets
  `self.field_classes = get_button_class(*(slot or self.slot).split(":", 1))` **before** `super().__init__`
  (crispy's `BaseInput.__init__` appends `css_class` to `self.field_classes`, so a project `css_class` is still
  appended). `slot` is consumed, never passed on as an HTML attribute.
- Produces: `CrispyFormMixin.get_submit_button() -> Submit` (table `form:submit`), `get_cancel_button_kwargs()`
  without `css_class`, `get_cancel_button() -> Button` (table `form:cancel`);
  `CrispyDeleteForm.get_delete_button_kwargs() -> dict` = `{"name": "delete", "value": _("Delete")}`,
  `CrispyDeleteForm.get_delete_button() -> Submit` with `slot="form:delete"`, and `helper` using it;
  `ListViewFilterFormHelper` using `Submit(..., css_id="filter-button", slot="form:filter-submit")` and
  `Reset("reset", _("Reset Filter"), css_id="filter-button-reset")`.
- Removes: `CrudViewsSettings.filter_reset_button_css_class`; the three tags and templates. The view hooks
  `get_cancel_button_context()` etc. stay.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_crispy_buttons.py` (db; clients from `conftest.py`:
  `client_user_author_add`, `client_user_author_delete`, `client_user_publisher_view`):
  - `test_submit_and_cancel_classes`: author create page contains `class="btn btn-primary"` on
    `input[name=submit]` and `class="btn btn-secondary"` on `input[name=reset]`; the string `btn btn btn-secondary`
    is absent.
  - `test_delete_button_hook`: author delete page: `input[name=delete]` has `class="btn btn-primary"` and
    `value="Delete"`; with `override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:delete": "btn btn-danger"})` the
    class is `btn btn-danger`; a `CrispyDeleteForm` subclass overriding `get_delete_button_kwargs` to
    `{"name": "delete", "value": "Erase"}` (set as `form_class` via `monkeypatch` on `AuthorDeleteView`) renders
    `value="Erase"`.
  - `test_filter_buttons`: publisher list page: `#filter-button` has `class="btn btn-primary"`,
    `#filter-button-reset` has `class="btn btn-secondary"` and `type="reset"`; `btn-inverse` is absent.
  - `test_project_css_class_still_appended`: an `AuthorForm` subclass whose `get_cancel_button_kwargs` adds
    `css_class="extra"` renders `class="btn btn-secondary extra"`.
  - `test_filter_reset_setting_removed`: `not hasattr(CrudViewsSettings(), "filter_reset_button_css_class")`.
  - `test_removed_tags`: `Template("{% load crud_views %}{% cv_cancel_button %}")` raises
    `TemplateSyntaxError`; `get_template("crud_views/tags/button_cancel.html")` raises `TemplateDoesNotExist`.
- [ ] **Step 2: Run** `pytest tests/test1/test_crispy_buttons.py -v` — Expected: FAIL.
- [ ] **Step 3: Implement** the module, hooks, filter helper, removals; rewrite `render_cancel_tag` in
  `test_cancel_origin.py` to
  `view.get_cancel_button_context(obj=getattr(view, "object", None), user=request.user, request=request)["cv_url"]`
  with `view = response.context["view"]`, `request = response.context["request"]` (drop the `Template` import if
  unused).
- [ ] **Step 4: Run** `pytest tests/test1/test_crispy_buttons.py tests/test1/test_cancel_origin.py
  tests/test1/test_filter.py tests/test1/test_workflow*.py tests/test1/test_i18n.py -v` — Expected: PASS
  (`WorkflowForm` inherits the submit class through `CrispyForm`). The Delete label becomes translatable;
  `msgid "Delete"` already exists in `src/crud_views/locale/de/LC_MESSAGES/django.po` (line 171), so no catalogue
  change is needed and the German delete page now shows the translation (changelog line in Task 7).
- [ ] **Step 5: Commit** `git commit -m "feat(crispy)!: form buttons from the table, CrispyDeleteForm.get_delete_button, remove filter reset setting and unused button tags"`

---

### Task 7: Documentation, changelog and examples

**Files:**
- Create: `docs/reference/buttons.md`
- Modify: `docs/reference/index.md` (line 48, add the page after Icons), `docs/reference/theme.md` (line 17 and
  the "Worked example" lines 81-89, the "Disabled actions in overridden templates" section line 91),
  `docs/reference/card-list-view.md` (line 51), `docs/reference/context_buttons.md` (field list lines 33-50),
  `docs/reference/action_menus.md` (lines 94-133), `docs/reference/settings.md` (line 40, Icons section line 79),
  `docs/reference/delete_view.md` (after line 58), `docs/reference/formsets.md` (after line 146),
  `docs/reference/inaccessible_actions.md` ("Overridden tag templates", line 74), `docs/development/stability.md`
  (line 41), `CHANGELOG.md` (Unreleased)
- Examples: no change needed (every `CardAction` in `examples/` that targets `create` is absent, and the existing
  `variant=` values are explicit); verify with `grep -rn "CardAction(" examples/` and leave a note in the commit.

**Interfaces:**
- Consumes: every public name from Tasks 1-6.

- [ ] **Step 1: Write `docs/reference/buttons.md`** with these sections, in this order: Variants (the four values,
  the view defaults table: create and create_select `primary`, delete `danger`, everything else `secondary`;
  `cv_action_variant`; `ContextButton.variant`; `CardAction.variant` default `None` = target view's variant;
  `viewset.E209`), The class table (`location:slot` keys, the full default table copied from
  `DEFAULT_BUTTON_CLASSES`, what is structural and stays in templates), `CRUD_VIEWS_BUTTON_CLASSES` (per-key
  merge, `None` switches classes off), Registering classes from a theme (`register_button_classes` from
  `AppConfig.ready()`, precedence package → theme → settings, mirroring `icons.md` lines 181-212), Rendering
  (`{% cv_button_class %}` in both tag libraries), Logic templates and leaves (which templates are logic templates
  that must not be copied: `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html`,
  `tags/actions_menu_item.html`, `tags/context_actions.html`, `columns/actions.html`, `tags/card.html`; the three
  leaves; the leaf contract, one sentence per key, from the Task 3 table; `{% cv_button %}` and
  `{% cv_render_button %}`), Forms (`Submit` / `Button` / `Reset` with `slot`, the hooks, `get_delete_button`),
  Formsets (`formset:control`, `formset:control-danger`, `formset:container`, the two data attributes
  `formset.js` reads), A theme recipe (registration plus one `tags/button/action.html` override, e.g. a visible
  label for `primary`), System checks (`E360`, `E361`, `W362`, `E209` in the table format of `icons.md` line 214).
- [ ] **Step 2: Update the other pages**: `theme.md` replace the submit-button example with "register classes,
  override a leaf" and rewrite the disabled-actions section (the thin templates no longer carry the branch; keep
  `cv_disabled` handling when overriding `tags/button/action.html`); `action_menus.md` templates table adds the
  three leaves and drops `cv_menu_wrapper_class` / `cv_toggle_class` from the variables paragraph, the split-toggle
  example uses `{% cv_button_class cv_location "menu-toggle" %}`, "Overridden containers" says a container override
  includes `crud_views/tags/button/container.html` or renders `group.inline` / `group.menu` itself (the group is
  always an `ActionGroup` now); `settings.md` removes the filter reset row and adds `CRUD_VIEWS_BUTTON_CLASSES`
  next to `CRUD_VIEWS_ICONS`; `card-list-view.md` `variant` row: `str | None`, default `None`, falls back to the
  target view, `danger` added; `context_buttons.md` adds `variant`; `delete_view.md` documents
  `get_delete_button_kwargs()` / `get_delete_button()`; `formsets.md` one paragraph on the classes;
  `inaccessible_actions.md` points overrides at the leaf; `stability.md` adds `Submit`, `Button`, `Reset`,
  `Variant`, `crud_views.lib.button_classes`; `docs/reference/index.md` line.
- [ ] **Step 3: CHANGELOG** under `## Unreleased`: **Breaking** — `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` removed
  (`crud_views.E360`, snippet `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "..."}`); the tags
  `cv_submit_button`, `cv_cancel_button`, `cv_delete_button` and their templates removed; `CardAction.variant`
  defaults to `None` (the target view's variant: a card action on a create view without an explicit variant now
  renders `btn-primary`); `cv_actions_menu` no longer passes `cv_menu_wrapper_class` / `cv_toggle_class` (theme
  overrides of `actions_menu.html` / `actions_menu_toggle.html` use `{% cv_button_class %}`);
  `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html`, `tags/actions_menu_item.html` are
  one-line logic templates (overrides from 0.30 keep working, new overrides go to `tags/button/*.html`); the DOM
  changes: unified attribute order, card buttons carry `cv-key`, card POST actions render `<button type="button">`,
  `aria-current="page"` on the active toolbar action, the card row carries `cv-card-container`, card menu forms
  render before the row, crispy cancel renders `btn btn-secondary` (was `btn btn btn-secondary`) and the filter
  reset `btn btn-secondary` (was `btn btn-inverse btn btn-secondary`); the Delete label is translatable;
  `formsets/control.html` overrides without `data-cv-class` / `data-cv-class-danger` no longer recolour the delete
  toggle; a list or card button whose target is the current view now renders `active`. **Added** — variants,
  `CRUD_VIEWS_BUTTON_CLASSES`, `register_button_classes`, `{% cv_button_class %}`, the leaves and the contract,
  `CrispyDeleteForm.get_delete_button()`, `Submit` / `Button` / `Reset`, checks `viewset.E209`,
  `crud_views.E360`, `E361`, `W362`; link `docs/reference/buttons.md`.
- [ ] **Step 4: Verify** `mkdocs build --strict` (or `task docs` and open the page) — Expected: no warnings; and
  run `uvx ruff@latest format --check docs/` as the repo's CI formats Markdown code blocks (venv ruff is older).
- [ ] **Step 5: Commit** `git commit -m "docs(buttons): variants, class table, leaves; changelog"`

---

### Task 8: Verification against the spec's acceptance list

**Files:**
- Read-only, plus a note at `superpowers/notes/2026-10-20-buttons-acceptance-report.md` (same shape as the
  JS adapters acceptance report in that directory).

- [ ] **Step 1: Full suites**: `pytest tests -q`; the vitest command; `task format` and `task check` (no diff, no
  findings); `uv run nox -p` if time allows (at least one Django 4.2 and one 6.0 session).
- [ ] **Step 2: Grep gates**: `grep -rn "btn" src/ --include=*.html --include=*.js --include=*.py | grep -v
  button_classes.py | grep -v btn-close` is empty; `grep -rn "FILTER_RESET_BUTTON_CSS_CLASS" src docs examples` hits
  only the changelog, the `REMOVED_SETTINGS` entry and the settings doc migration note;
  `grep -rn "cv_toggle_class\|cv_menu_wrapper_class\|_ACTIONS_MENU_STYLE" src docs` is empty.
- [ ] **Step 3: Golden diff review**: `git diff 440ac55 -- tests/test1/golden` shows, beyond the canonical ordering
  commit of Task 4 step 1, only the four changes listed in Task 4 step 5. Record the hunks in the note.
- [ ] **Step 4: Spec walk**: tick every row of the spec's "Templates to change" table against `git diff 440ac55
  --stat -- src/*/templates`; every check id of its table against `grep -rn "E209\|E360\|E361\|W362" src`; every
  contract key of section 3 against `LEAF_KEYS`; the Tabler check section needs no code (the theme migration is a
  follow-up) — note that `fieldset.btn-list` remains unverified.
- [ ] **Step 5: Manual browser check** (examples project, `examples/bootstrap5`): list toolbar, list rows with and
  without the overflow menu, author cards with a POST action, create form (submit, cancel), delete form, filter
  form reset, a formset page (mark a row for deletion: red button, un-mark: light), card order direction toggle.
  Record what was checked in the note.
- [ ] **Step 6: Commit** `git commit -m "docs: buttons acceptance report"`
