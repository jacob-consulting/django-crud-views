# Architecture Research

**Domain:** How the theme surface of a reusable Django UI package (django-crud-views 0.30.0 → 1.0.0) fits together: label modes, button data, class table, icons, crispy form buttons, alert frame, JS adapters, table pagination, stability policy
**Researched:** 2026-10-25
**Confidence:** HIGH. Every claim below was checked against the source at commit `9e6b40e`. No external sources were needed because the question is about integrating with this codebase. Third-party behaviour (crispy-forms 2.6, crispy-bootstrap5 2026.3) was read from the installed packages in `.venv`.

---

## Standard Architecture

### System Overview (the theme surface only)

```
┌───────────────────────────── CONFIGURATION (read at render / check time) ──────────────────────────────┐
│ settings.py (import-time Pydantic)      button_classes.py (lazy, cached)   icons.py (lazy, cached)       │
│  CRUD_VIEWS_CONTEXT/LIST_ACTIONS_       DEFAULT_BUTTON_CLASSES (70 keys)    DEFAULT_ICONS (34 names)     │
│  LABEL_MODE  (per-key maps, whole-dict) + register_button_classes()         + register_icons()           │
│  [1A NEW] CRUD_VIEWS_LABEL_MODE_DEFAULTS + CRUD_VIEWS_BUTTON_CLASSES        + register_icon_library()    │
│           (per-key merge, lazy)         per-key merge, setting_changed      BOOTSTRAP_ICONS (sync test)  │
└──────────────┬─────────────────────────────────────┬──────────────────────────────┬────────────────────┘
               │ label-mode chain                    │ get_button_class(loc,slot,mode)│ render_icon / host class
               ▼                                     │                                │
┌──────────────────────────── RESOLUTION (Python, per request) ─────────────────────────────────────────┐
│ CrudView.cv_get_action_label_mode()  base.py:291-317   (context, list; [2] form)                        │
│ CardListView.cv_get_card_action_data() card.py:44-87  (card)                                            │
│ ContextButton / FilterContextButton.get_context()  view/buttons.py                                       │
│ cv_get_context(location=…) stamps cv_label_mode + cv_action_key   base.py:612-634                        │
│ [2 NEW] crispy Submit/Button/Reset.render() → resolve form mode                                          │
└──────────────┬────────────────────────────────────────────────────────────────────────────────────────┘
               │ raw action ctx (cv_action_label, cv_icon_action, cv_label_mode, cv_url, …)
               ▼
┌──────────────────────────── NORMALISATION: the leaf contract ─────────────────────────────────────────┐
│ cv_button_data(ctx, location, kind)  view/button_data.py:52-135                                          │
│  LOCATIONS={context,list,card} (:12)  KINDS={action,menu-item} (:14)  LEAF_KEYS (19 keys, :16-38)        │
│  label-mode default (:83), strict-mode icon-less guard (:88-101), icon_host_keys() (:41-49)              │
└──────────────┬────────────────────────────────────────────────────────────────────────────────────────┘
               │ flat dict ⊆ LEAF_KEYS
               ▼
┌──────────────────────────── PRESENTATION (theme-overridable templates) ───────────────────────────────┐
│ tags/button/action.html   menu_item.html   menu_item_label.html   container.html   [2 NEW] form.html    │
│   └─ {% cv_button_class loc variant mode %}  {% cv_button_class loc 'hidden-label' %}  {% cv_icon %}    │
│ tags/context_action_filter.html  (filter toggle: NOT a leaf; own template, hard-coded "icon") [1B]     │
│ tags/alert.html (alert_data ctx; data-bs-dismiss leak) [3A]                                              │
│ table/bootstrap5.html (django-tables2; &laquo;/&raquo; text) [3B]   snippets/pagination.html (#241)     │
└──────────────┬────────────────────────────────────────────────────────────────────────────────────────┘
               │ DOM contract: data-cv-*, cv-key, #cv-filter-toggle, #filter-collapse, #filter-button-reset
               ▼
┌──────────────────────────── CLIENT (static/crud_views/js) ────────────────────────────────────────────┐
│ adapters.js  cv.adapters.{modal,tooltip,collapse}  [3A +alert]  cv.bootstrapAdapters(ns)                │
│ viewset.js   delegated click: submit-form, cancel-url  [3A + alert-dismiss]                             │
│ list.filter.js  toggle (aria-expanded, host-class swap / span swap), reset   [1B]                       │
│ modal.js  event.submitter → FormData (works with <button>)   tooltip.js  [data-cv-tooltip]              │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
               ▲
               │ validated at startup: crud_views.E10x (settings), E36x/W362 (class table), viewset.E210/E211/W291/W292
┌──────────────┴────────────────────────────────────────────────────────────────────────────────────────┐
│ CHECKS: settings._action_settings_messages (E105/E106) [1A +E108] · button_class_check_messages (W362)  │
│ [1C] · label_mode_check E210 · cv_label_mode_checks E211/W291 · cv_icon_mode_checks W292 [2 extends]    │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
               ▲
               │ freezes all of the above
┌──────────────┴──── POLICY: docs/development/stability.md + [4 NEW] tests/test1/test_stability_doc.py ───┐
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities (theme surface)

| Component | Owns | File (verified) | Touched by |
|-----------|------|-----------------|-----------|
| Label-mode primitives | `LabelMode`, `LABEL_MODES`, `is_label_mode(_map)`, `label_mode_check` (viewset.E210) | `lib/view/label_mode.py` (35 lines) | 1A (`default_label_mode`), 2 |
| Settings | Import-time Pydantic fields: `context_actions_label_mode`, `list_actions_label_mode` (`:65-66`), E105/E106 in `_action_settings_messages` (`:98-132`) | `lib/settings.py` | 1A (E108), 2 (`form_actions_label_mode`) |
| View label-mode resolution | `cv_first_inline_keys` (view → ViewSet → setting, `:259-268`), `cv_get_action_label_mode` (`:291-317`, literal `"icon"` at **`:312` and `:317`**, not `:311`/`:318` as the plan says) | `lib/view/base.py` | 1A, 2 |
| ViewSet layer | `context_actions_label_mode`, `list_actions_label_mode` fields + validator (`:85-86`, `:105-109`) | `lib/viewset/__init__.py` | 2 (`form_actions_label_mode`) |
| Card resolution | `cv_card_actions_label_mode: str = "both"` (`:28`), resolution `label_mode → no_label → view attr` (`:46-52`), E210 on the attribute (`:112`) | `lib/views/card.py` | 1A |
| Context buttons | `ContextButton.label_mode`, `FilterContextButton` (`:298-334`, fixed label `"Filter"`, icon `"filter"`, own template), `cv_icon_mode_checks` W292 (`:368-415`) | `lib/view/buttons.py` | 1B, 2 (W292) |
| Leaf contract | `cv_button_data`, `LOCATIONS` (`:12`), `KINDS`, `LEAF_KEYS`, `icon_host_keys`; default `"both" if card else "icon"` at `:83` | `lib/view/button_data.py` | 1A, 2 |
| Leaf renderer | `_BUTTON_LEAVES` (kind → template, `:188-191`), `cv_button`, `cv_render_button` | `templatetags/crud_views.py` | 2 |
| Class table | `DEFAULT_BUTTON_CLASSES` (70 keys, test-pinned at `test_button_classes.py:84`; docs say 64 at `buttons.md:112`), `get_button_class` (mode-key-if-present, `:136-147`), `_action_key_parts` (`:207-221`, imports `LOCATIONS` from button_data), W362 loop (`:274-292`) | `lib/button_classes.py` | 1C, 2, 3B |
| Icon registry | `DEFAULT_ICONS` (34), `BOOTSTRAP_ICONS`, `register_icon_library`, `register_icons`, `render_icon`, `resolve_icon_name_class` | `lib/icons.py` | 2 (+`save`, `cancel`, `filter-reset`), 3B (uses `page-previous`/`page-next`) |
| Crispy buttons | `_TableClassMixin` sets `field_classes` from `slot` (`buttons.py:8-18`); `Submit`/`Button`/`Reset` default slots | `lib/crispy/buttons.py` (30 lines) | 2 (rewrite to adapters) |
| Crispy forms | `CrispyFormMixin.get_form_actions` → `FormActions(submit, cancel)`, cancel `name="reset"` + `data_cv_cancel_url` (`form.py:75-79`), `CrispyDeleteForm` slot `form:delete` (`:130`) | `lib/crispy/form.py` | 2 |
| Filter form helper | `ListViewFilterFormHelper` uses **`helper.add_input(...)`** for submit/reset (`list.py:70-73`) | `lib/views/list.py` | 2 (critical, see Pitfall P1) |
| Alert frame | `tags/alert.html` (6 lines, `btn-close` + `data-bs-dismiss="alert"` + `alert-dismissible fade show`); data from `lib/messages.py` (`alert_data`, `message_alerts`, `LEVELS`) | templates + `lib/messages.py` | 3A |
| JS adapters | `cv.bootstrapAdapters(ns)` → `{modal, tooltip, collapse}`; `cv.adapters = Object.assign(bootstrap, cv.adapters)` (`:43`) | `static/crud_views/js/adapters.js` | 3A |
| JS delegation | submit-form, submit-on-change, cancel-url (`viewset.js:37-44`) | `static/crud_views/js/viewset.js` | 3A |
| Filter JS | toggle via `cv.adapters.collapse`, host-class swap if `data-cv-filter-icon-open` present, else span swap via `querySelectorAll` (`list.filter.js:22-30`); reset wired by `#filter-button-reset` | `static/crud_views/js/list.filter.js` | 1B (mostly tests), 2 (must keep the id) |
| Table template | django-tables2 override; blocks `pagination.previous/.range/.next` (`bootstrap5.html:61-99`) | `templates/crud_views/table/bootstrap5.html` | 3B |
| Stability policy | Public API list; only `crud_views.lib.button_classes` from the theme surface (`stability.md:28-29`) | `docs/development/stability.md` | 4 |

---

## Recommended Project Structure (files added or changed by the milestone)

```
src/crud_views/
├── lib/
│   ├── settings.py              # 1A: E108 (lazy read of CRUD_VIEWS_LABEL_MODE_DEFAULTS); 2: form_actions_label_mode
│   ├── button_classes.py        # 1C: FORM_KINDS + explicit VARIANT_LOCATIONS; 2: form:hidden-label, form:icon-host;
│   │                            # 3B: one pagination hidden-label key
│   ├── icons.py                 # 2: save, cancel, filter-reset in DEFAULT_ICONS + BOOTSTRAP_ICONS
│   ├── view/
│   │   ├── label_mode.py        # 1A: LABEL_MODE_DEFAULTS, default_label_mode(location)
│   │   ├── button_data.py       # 1A: :83 → accessor; 2: "form" in LOCATIONS, form branch, LEAF_KEYS +cv_type/name/value/id/cancel_url
│   │   ├── base.py              # 1A: :312/:317 → accessor; 2: "form" branch + cv_get_form_actions_label_mode
│   │   └── buttons.py           # 1B: FilterContextButton (no code needed, see below); 2: W292 for forms
│   ├── views/card.py            # 1A: cv_card_actions_label_mode: str | None = None
│   ├── views/list.py            # 2: filter buttons out of add_input()
│   ├── viewset/__init__.py      # 2: form_actions_label_mode field + validator
│   └── crispy/{buttons,form}.py # 2: thin adapters; submit_icon / delete_icon
├── templates/crud_views/
│   ├── tags/button/form.html    # 2: NEW leaf
│   ├── tags/context_action_filter.html   # 1B: three-way branch
│   ├── tags/alert.html          # 3A: data-cv-alert-dismiss
│   └── table/bootstrap5.html    # 3B: registry arrows, #241 markup
└── static/crud_views/js/
    ├── adapters.js              # 3A: alert.close(el)
    ├── viewset.js               # 3A: delegated [data-cv-alert-dismiss] handler
    └── list.filter.js           # 1B: only if the label-only case shows a gap (it currently tolerates it)
src/crud_views_workflow/lib/forms.py   # 2: WorkflowForm.submit_icon = "workflow"
docs/development/stability.md          # 4
tests/test1/test_stability_doc.py      # 4: NEW
```

### Structure Rationale

- **The accessor lives in `lib/view/label_mode.py`, not in `settings.py`.** `settings.py` must not import the view package at module level (comment at `:100`), and `label_mode.py` only imports `..check`, so it is a safe leaf that `button_data.py`, `base.py`, `card.py` and `button_classes.py` can all import.
- **The new form leaf sits next to `action.html` under `tags/button/`.** Theme authors override the leaves as one set, and Phase 4 freezes that directory.

---

## Architectural Patterns

### Pattern 1: Layered per-key merge with lazy read (copy it from the class table, not from the label-mode maps)

**What:** `get_button_classes()` builds `{**DEFAULT, **THEME, **settings}` on first use, caches it, and resets the cache on `setting_changed` (`button_classes.py:111-133`). The existing label-mode maps work differently. They are Pydantic fields evaluated **at import** (`settings.py:65-66`), which is why tests use `monkeypatch.setattr(crud_views_settings, …)` (`test_action_label_mode_config.py:79`).

**When to use:** `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (1A). The plan specifies "per-key merge like the class table". Use the class table's lazy read too, so that `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=…)` works in tests and the acceptance criteria can be checked without monkeypatching.

**Trade-offs:** This creates two setting families with different read times. The docs have to say which is which: the plan already requires "per-key merge vs whole-dict replacement", and read time belongs in the same paragraph. A dict merge per call costs nothing next to template rendering, so no cache is needed.

```python
# lib/view/label_mode.py
LABEL_MODE_DEFAULTS: dict[str, str] = {"context": "icon", "list": "icon", "card": "both"}  # 2 adds "form": "label"

def label_mode_defaults() -> dict[str, str]:
    from django.conf import settings
    return {**LABEL_MODE_DEFAULTS, **(getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", None) or {})}

def default_label_mode(location: str) -> str:
    mode = label_mode_defaults().get(location)
    return mode if is_label_mode(mode) else LABEL_MODE_DEFAULTS[location]  # E108 reports the bad value
```

### Pattern 2: One floor, many layers (the label-mode resolution chain)

**What:** Every location resolves through a sequence of overrides. The defaults map from 1A becomes the single floor under all of them. This is the full chain after 1A + 2:

```
context:  view map (own key)   → ContextButton.label_mode → resolved map (view→ViewSet→setting)
          → target view's cv_context_action_label_mode → default_label_mode("context")
list:     resolved map (view→ViewSet→setting)                         → default_label_mode("list")
card:     CardAction.label_mode → CardAction.no_label ("icon") → view cv_card_actions_label_mode (now None)
          → default_label_mode("card")
form [2]: resolved map (view cv_form_actions_label_mode → ViewSet form_actions_label_mode
          → CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE)                        → default_label_mode("form") = "label"
leaf:     cv_button_data: ctx["cv_label_mode"] or default_label_mode(location); "" label → "icon"; icon-less
          "icon" → strict raise / "label" fallback (#264)
```

**When to use:** Any new location. The floor is never per-ViewSet or per-view. Those layers already exist.

**Trade-offs:** `cv_button_data` keeps its own fallback (`:83`) for callers that pass raw context through `{% cv_button %}` without stamping a mode. After 1A it must call the same accessor so that the two cannot disagree.

### Pattern 3: Flat leaf contract (decisions in Python, markup in templates)

**What:** `cv_button_data()` takes every decision (tag, disabled, modal, title, label mode, host icon). The leaf receives only keys in `LEAF_KEYS`, and this is enforced by `test_button_leaves.py:504` and `test_button_data.py:176`.

**When to use:** Phase 2. The form leaf gets its own contract branch and does not grow `action.html`. Recommendation: implement the form branch as a separate private builder (`_form_button_data`) that `cv_button_data` dispatches to when `location == "form"`. The action branch then stays line-for-line unchanged, which is the cheapest way to keep the action goldens byte-identical. Two details from the current code matter here. The action branch reads `ctx["cv_url"]` and `ctx["cv_oid"]` unconditionally (`:129-132`). Its `card` / non-card label logic (`:74-81`, `:102-105`) does not fit a form button either: a form button has one label, the crispy `value`.

**Trade-offs:** `LEAF_KEYS` becomes the union of two contracts. Phase 4 should document which keys apply to which leaf. Alternatively, split it into `LEAF_KEYS` and `FORM_LEAF_KEYS` before 1.0.0 freezes the name. This is a decision for the Phase 2 spec.

### Pattern 4: The adapter seam (JS touches UI libraries only through `cv.adapters`)

**What:** Templates emit `data-cv-*`. Delegated handlers in `viewset.js` / `modal.js` call `cv.adapters.X.method(el)`. Only `adapters.js` names Bootstrap. `cv.adapters = Object.assign(bootstrapAdapters(...), cv.adapters || {})` (`adapters.js:43`), so a theme's pre-assigned adapters win entry by entry.

**When to use:** 3A. Put the "no Bootstrap `Alert`" fallback **inside** `bootstrapAdapters().alert.close` (`Alert ? Alert.getOrCreateInstance(el).close() : el.remove()`), not in the `viewset.js` handler. The handler then stays library-agnostic (`cv.adapters.alert.close(el.closest('[role="alert"]'))`). A theme that pre-assigned `modal/tooltip/collapse` but not `alert` still gets the Bootstrap entry, and that entry degrades to `el.remove()`. The plan puts the fallback in the handler. That works, but the handler then has to know what Bootstrap is, which is the leak 3A is supposed to remove.

---

## Data Flow

### Flow A: Context / list button (unchanged by the milestone, except the floor)

```
{% cv_context_actions %} / {% cv_list_action key obj %}
  → view.cv_get_context(key, obj, location=…)                       base.py:612
      → _cv_get_action_context → ContextButton.get_context / sibling cls.cv_get_dict
      → cv_get_action_label_mode(location, key, button, target_default)   ← [1A] floor = default_label_mode
      → {…, cv_label_mode, cv_action_key}
  → cv_resolve_action (hide / disable)                              visibility.py
  → cv_split_actions (inline vs menu)                               action_menu.py:88
  → container.html → cv_render_button → context_action.html / list_action.html
  → {% cv_button loc %} → cv_button_data(ctx, loc, kind)            ← [1A] :83 → accessor
  → action.html: {% cv_button_class loc variant mode %}             → get_button_class → "loc:variant[:mode]"
                 {% cv_icon cv_icon %}                              → icons.render_icon
                 {% cv_button_class loc 'hidden-label' %}
```

### Flow B: Filter toggle (1B)

```
FilterContextButton.get_context → {cv_key:"filter", cv_action_label:"Filter", cv_icon_action:"filter",
                                   cv_filter_expanded, cv_template: tags/context_action_filter.html}
cv_get_context(location="context") ALREADY stamps cv_label_mode via cv_get_action_label_mode("context","filter")
  → _render_context_action renders cv_template with the raw ctx (NOT through cv_button_data)
  → template today ignores cv_label_mode and hard-codes "icon" (class mode "icon", title, hidden label)
```

Finding: the plan says "`FilterContextButton` resolves its mode through `cv_get_action_label_mode`". In practice this already happens. `cv_get_context()` stamps `cv_label_mode` for every context key, including `filter` (`base.py:629-633`), so 1B needs no Python resolution code. The work is:

1. A three-way branch in `context_action_filter.html` on `cv_label_mode` (class mode argument, `title` / `data-cv-tooltip` only for `icon`, hidden label vs visible `<span>`).
2. The host-class vs icon-span placements in each mode. For `label`: no host class and no `data-cv-filter-icon-open/close`.
3. Tests, including vitest for the label-only toggle.

`list.filter.js` already copes with a toggle that has neither data attributes nor spans: the `else` branch is a `querySelectorAll` that does nothing on an empty list (`:28-30`). Expect a test and no code change there, unless the spec decides `both` should keep swapping the visible label. The rule at `buttons.md:188` ("with `context:icon-host` off it falls back to its two icon spans") has to hold in all three modes.

Two side effects to plan for:

- If the toggle stops being hard-coded to `icon`, W292 (`cv_icon_mode_checks`) can start covering it. Today it skips it because the button has its own template (`buttons.py:390-395`).
- The `"Filter"` label is an untranslated literal (`buttons.py:326`). It becomes visible text in `both`/`label` mode, so 1B should wrap it in `gettext_lazy` and add a `.po` entry.

### Flow C: Form buttons today vs after Phase 2

Today there are two paths, and Phase 2 has to catch both:

```
(1) Layout path:  CrispyFormMixin.helper → Layout(…, FormActions(Submit, Button))
                  {% crispy form %} → FormActions.render → field.render(form, context)  ← BaseInput.render()
                  → bootstrap5/layout/baseinput.html  → <input type=… class=field_classes …>
(2) Inputs path:  ListViewFilterFormHelper.add_input(Submit/Reset/Hidden)                 list.py:70-73
                  {% crispy filter.form helper %} → bootstrap5/inputs.html
                  → {% include "bootstrap5/layout/baseinput.html" %} per input          ← render() NEVER called
```

After Phase 2:

```
Submit/Button/Reset.render(form, context, template_pack, **kw)
  → view = getattr(form, "cv_view", None) or context.get("view")   (None: a plain crispy form → floor only)
  → kind = slot.split(":")[1]  (submit | cancel | delete | filter-submit | filter-reset)
  → mode = view.cv_get_action_label_mode("form", kind) if CrudView else default_label_mode("form")
  → ctx = {cv_label_mode, cv_icon_action (form.submit_icon / delete_icon / filter icons), cv_action_label=value,
           type, name, value, id, cancel_url, flat attrs, css_class}
  → cv_button_data(ctx, "form") → render_to_string("crud_views/tags/button/form.html", data)
  → form.html: {% cv_button_class "form" cv_key cv_label_mode %} → "form:<kind>[:<mode>]"   ← needs 1C
               hidden label class → "form:hidden-label"   host icon → "form:icon-host"        ← keys needed (P2)
```

Path (2) bypasses `render()`, so the filter buttons have to leave `add_input()`. There are two options:

- **Recommended:** put them in a layout object at the end of the helper layout, a crud_views `FormActions`-like `Div`. The wrapper changes from crispy's `inputs.html` `<div class="mb-3"><div class="">` to the layout wrapper. That is a DOM change, and it belongs in the same Breaking entry.
- **Fallback:** render the two buttons to strings in the helper and pass them as `HTML(...)`.

Do **not** override `bootstrap5/inputs.html`. It is the host project's template-pack file, and the Tabler theme uses its own pack.

Side effect: form buttons stop following the crispy template pack, because the leaf replaces `baseinput.html` for every pack. This is intended (the theme owns the leaf), but `theme.md` should say so.

### Flow D: Alert dismiss (3A)

```
alert_data()/message_alerts() → tags/alert.html  <button … data-cv-alert-dismiss aria-label=Close>
click (document-delegated, viewset.js) → el.closest('[role="alert"]') → cv.adapters.alert.close(alertEl)
   bootstrapAdapters: Alert ? Alert.getOrCreateInstance(el).close() : el.remove()
```

Delegation on `document` covers alerts that arrive inside modal content injected later (`modal.js` → `cvModalInject`). The frame still hard-codes `btn-close` and `alert-dismissible fade show`. Those are Bootstrap classes that are not in the class table. 3A as planned only removes the data-API leak, so Phase 4 would freeze a frame that still has class literals (see Open Questions).

### Flow E: Table pagination (3B)

django-tables2 → `crud_views/table/bootstrap5.html` `{% block pagination %}`. Replace the `&laquo;` + `{% trans 'previous' %}` markup with the `snippets/pagination.html` #241 structure: `{% cv_icon "page-previous" %}`, a hidden label, `aria-current="page"` on the active `<li>`, disabled ends rendered as `<a class="page-link" aria-disabled="true">`, and a translated `<nav aria-label>`.

Keep the block names `pagination.previous`, `pagination.range` and `pagination.next`. Themes extend them. The `'...'` entries from `table_page_range` must not get `aria-current`.

Today the disabled ends are not rendered at all: `{% if table.page.has_previous %}` wraps the whole `<li>`. Adding them is part of the DOM change.

### Flow F: Check flow (startup)

```
crud_views.E108 [1A]   settings._action_settings_messages → keys ⊆ label-mode locations, values ∈ LABEL_MODES
crud_views.W362 [1C]   button_class_check_messages → _action_key_parts / _is_action_mode_key
viewset.E210/E211/W291 [2]  label_mode_check / cv_label_mode_checks for cv_form_actions_label_mode (keys = FORM_KINDS)
viewset.W292 [2]       cv_icon_mode_checks extended: view.form_class is CrispyFormMixin and resolved form mode is
                       "icon" while submit_icon / delete_icon is empty
```

E108 is free (E100–E107 are taken). E210/E211/W291/W292 are **existing** `viewset.*` ids, so Phase 2 extends them and does not create new ones.

---

## Seams and Cross-Phase Couplings (the important part for the roadmap)

| # | Seam | Phases | What couples them | Resolution |
|---|------|--------|-------------------|------------|
| S1 | **`LOCATIONS` has three meanings** | 1A, 1C, 2, 4 | (a) the locations `cv_button_data` accepts (`button_data.py:12`); (b) the locations whose second class-key segment is a *variant* (`_action_key_parts` imports `LOCATIONS`, `button_classes.py:213-219`); (c) the keys of the new label-mode defaults map (E108's valid set). They are the same set today. Phase 2 adds `"form"` to (a) and (c) but not to (b): with `"form"` in `LOCATIONS` and nothing else changed, `form:primary:icon` would become a *valid* W362 key, and `test_button_classes_templates.py:214` would render `action.html` for `location="form"`. | **1C** introduces an explicit set for (b), e.g. `VARIANT_LOCATIONS = {"context","list","card"}` in `button_classes.py`, alongside `FORM_KINDS`, and makes `_action_key_parts` dispatch `form` → `FORM_KINDS`, variant locations → `VARIANTS`. **1A** makes the label-mode map keys the source for (c). **2** then adds `"form"` to (a) and (c) without touching W362. **4** documents `LOCATIONS` as (a) only. |
| S2 | `form:*` mode keys | 1C → 2 | The leaf reads `{% cv_button_class "form" cv_key cv_label_mode %}` → `form:submit:icon`, which `test_button_classes_checks.py:79` currently pins as invalid. `get_button_class` already prefers a present mode key. | 1C only changes the checks and docs. No runtime change. |
| S3 | **Missing `form:hidden-label` / `form:icon-host`** | 1C/2, 3B, 4 | The plan says Phase 2 adds "no new keys". But a leaf that mirrors `action.html` renders `{% cv_button_class cv_location 'hidden-label' %}`, and `icon_host_keys(icon, "form")` reads `form:icon-host`. Without those keys, `icon` mode shows the "hidden" label visibly, and a host-placed icon library (`placement: "host"`) renders **no icon** on form buttons: an empty class and `cv_icon_inline=False`. | Add `form:hidden-label = "visually-hidden"` and `form:icon-host = "{name_class}"` in Phase 2 (70 → 72, plus one for 3B). The 1C count test catches the docs. `test_icon_host_default_slots` (`test_button_classes.py:232`) gains `"form"`. |
| S4 | Key count pinned by test | 1C → 2, 3B | 1C pins the number quoted in `buttons.md:112` (64 → 70). 2 (+2) and 3B (+1) change it. | Merge order does not matter because the test reads the docs number. Every PR that adds a key updates `buttons.md` in the same PR. |
| S5 | Label-mode floor | 1A → 1B, 2 | 1B relies on the context floor. 2 adds `"form": "label"` to the package map and to E108's valid keys. | 1A lands the map with a location set that can be extended. Phase 2 adds one entry. |
| S6 | Card default becomes `None` | 1A | `label_mode_check(cls, "cv_card_actions_label_mode", …)` (`card.py:112`) would fail on `None`. The type is `str`. | Guard with `if … is not None` and type it `str | None`. The `migrating-1.0.md` recipe gains the `{"card": "label"}` alternative. |
| S7 | Two crispy render paths | 2 | `add_input()` bypasses `BaseInput.render()` (Flow C). | Move the filter buttons into the layout in Phase 2. Keep `id="filter-button"` / `id="filter-button-reset"`: `list.filter.js:57` depends on the second. |
| S8 | View lookup from a crispy object | 2 | Constructor signature frozen (`name, value, slot=, css_class=, css_id=, **kwargs`). The view is not a constructor argument. | Resolve in `render()` from `form.cv_view` (CrispyFormMixin), `helper.view` (filter helper) or `context["view"]`, and fall back to the floor. A plain crispy form outside crud_views must keep working (the example login form uses crispy's own `Submit`, `examples/bootstrap5/project/urls.py:17`). |
| S9 | crispy `value` is a template | 2 | `BaseInput.render` does `Template(str(self.value)).render(context)`. Overriding `render()` drops that, so `{{ }}` in a label no longer expands. | Treat dropping it as a deliberate decision: it removes a template-injection path. Record it in the Breaking entry. The escaping test from #257 covers the autoescape half. |
| S10 | DOM contract additions | 2, 3A, 3B → 4 | New or confirmed names: `data-cv-alert-dismiss`, `data-cv-cancel-url`, `data-cv-tooltip="form"`, `#filter-button`, `#filter-button-reset`. Plan Phase 4 lists `#cv-filter-toggle` and `#filter-collapse` but not the filter-form ids. | Phase 4 lists them all. `test_stability_doc.py` asserts them. |
| S11 | `data-bs-` grep acceptance | 3A | Remaining after 3A: `actions_menu_toggle.html` and `snippets/language_selector.html` (verified). That matches the plan's acceptance (`actions_menu*.html`, `language_selector.html`). | None needed. |
| S12 | Docs location of the Mermaid chain | 1A | The plan says `action_menus.md`. The `MICON["icon"]` node is actually in **`docs/reference/context_buttons.md:256`**. | Add `context_buttons.md` to the 1A file list. |

---

## Suggested Build Order

```
            ┌──────── 1A label-mode defaults (label_mode.py, button_data.py:83, base.py:312/317, card.py:28, E108)
            │            └─► 1B filter toggle (template + tests; list.filter.js likely unchanged)
 wave 1 ────┤
            └──────── 1C key grammar (FORM_KINDS + VARIANT_LOCATIONS split, W362, buttons.md count test)
                         │
 wave 2 ── 1B ∥ 3A ∥ 3B  │   (3A: alert.html/adapters.js/viewset.js; 3B: table/bootstrap5.html + 1 key)
                         ▼
 wave 3 ── 2  form leaf (needs 1A floor "form", 1C mode keys + location split; adds form:hidden-label/icon-host,
              icons save/cancel/filter-reset, LOCATIONS+form, crispy adapters, filter helper off add_input)
                         ▼
 wave 4 ── 4  stability.md theme surface + test_stability_doc.py (after every name above is final)
```

Rationale:

1. **1A and 1C first, in parallel.** They touch disjoint files. 1A: `label_mode.py`, `button_data.py`, `base.py`, `card.py`, `settings.py`. 1C: `button_classes.py`, `test_button_classes*.py`, `buttons.md`. Each removes a precondition of Phase 2. Splitting the location sets (S1) belongs in 1C because 1C is already editing `_action_key_parts`. Doing it there means Phase 2 adds `"form"` without a check regression.
2. **1B after 1A.** The context floor must exist before the toggle stops hard-coding `"icon"`. The golden `action_menus/toolbar_publisher_list.html` must stay byte-identical (it is the only golden containing `cv-filter-toggle`).
3. **3A and 3B are independent.** No shared files with 1B or 2. 3B adds one class key, which conflicts with Phase 2's two keys only in the `buttons.md` count line. Rebase whichever merges second.
4. **Phase 2 last among the code phases.** It consumes S1, S2, S5 and touches the most files. Start its spec only after 1A and 1C are on `main`, as the plan says. The spec must settle P1/S7 (the add_input path), S3 (keys), S8 (view lookup), S9 (value templating) and the `LEAF_KEYS` split.
5. **Phase 4 last.** It freezes names: `default_label_mode`, `LABEL_MODE_DEFAULTS`, `FORM_KINDS`, `LOCATIONS`, `LEAF_KEYS`, the form leaf, `cv.adapters.alert`, the pagination key. If Phase 3 is dropped, Phase 4 has to list `tags/alert.html` as a Bootstrap-DOM template in `theme.md`.

**Golden-test prerequisite (affects every DOM-changing phase).** No current golden contains a form button, a dismissible alert or a table pagination. The `form_frame/*` goldens render a bare form without `FormActions`, `delete_protection.html` renders a non-dismissible alert, and only `card_pagination/*` covers pagination. "Goldens change only where a phase says so" therefore protects nothing for Phases 2, 3A and 3B. Each of those phases should first commit a golden of the *current* markup (form actions of create/delete/filter, a dismissible flash message, a paginated table) and then make the change, so the diff shows up in review.

---

## Anti-Patterns

### Anti-Pattern 1: Adding `"form"` to `LOCATIONS` without splitting the set

**What people do:** Append `"form"` to `button_data.LOCATIONS` in Phase 2 because the plan says "`form` joins `LOCATIONS`".
**Why it's wrong:** `_action_key_parts` silently starts accepting `form:<variant>:<mode>`. The template sentinel test renders `action.html` for `form`. `LOCATIONS` then means three things when Phase 4 freezes it.
**Do this instead:** Split the sets in 1C (S1).

### Anti-Pattern 2: Overriding only `render()` on the crispy buttons

**What people do:** Implement design point 3 of the plan literally.
**Why it's wrong:** The filter Submit/Reset are added with `helper.add_input()`, and crispy-bootstrap5's `inputs.html` includes `baseinput.html` directly. The filter buttons would stay `<input>` while every other form button becomes `<button>`.
**Do this instead:** Move them into the layout (S7). Assert in a test that no `<input type="submit|reset|button">` remains on the list page.

### Anti-Pattern 3: Putting Bootstrap knowledge in `viewset.js`

**What people do:** Write `if (bootstrap?.Alert) … else el.remove()` in the delegated handler.
**Why it's wrong:** It reintroduces the coupling that 3A removes. A theme replacing `cv.adapters.alert` gets dead code.
**Do this instead:** Put the fallback in `bootstrapAdapters().alert.close`.

### Anti-Pattern 4: A second hard-coded default

**What people do:** In 1B or 2, write `ctx.get("cv_label_mode") or "label"` in the form builder or the filter template.
**Why it's wrong:** It recreates the problem 1A solves. The plan's acceptance grep only covers `lib/view/*.py`.
**Do this instead:** Always call `default_label_mode(location)`. Extend the acceptance grep to `lib/crispy/*.py` and `templates/crud_views/tags/`.

### Anti-Pattern 5: Freezing names in Phase 4 that Phase 2 still renames

**What people do:** Write `stability.md` in parallel with Phase 2 "to save time".
**Why it's wrong:** The Core Value is that no public name changes twice.
**Do this instead:** Merge Phase 4 only after Phase 2. The guard test makes a missing name fail loudly.

---

## Scaling Considerations

The relevant scale here is the number of theme names and downstream themes, not users.

| Scale | Adjustment |
|-------|------------|
| 1 theme (Bootstrap) | The current layering is enough. |
| 2 themes (Bootstrap + Tabler) | Every phase writes its Tabler follow-up into its acceptance note. Phase 4's "every name the theme imports is documented" check is the contract test. |
| N third-party themes | `test_stability_doc.py` plus the key-count test are what stop silent drift. Consider a public `is_library_renderer(prefix, callable)` so themes stop importing `_get_renderers` / `_icon_str` (plan Phase 4, optional). |

---

## Integration Points

### External libraries

| Library | Integration | Gotchas (verified in `.venv`) |
|---------|-------------|-------------------------------|
| django-crispy-forms 2.6 | `BaseInput.render(form, context, template_pack, **kw)`; `__init__(name, value, *, css_id, css_class, template, **kwargs)`; `field_classes` + `flat_attrs` | `render()` template-renders `value` (S9). `helper.add_input` inputs skip `render()` (S7). The default id is `f"{input_type}-id-{slugify(name)}"`: preserve it for buttons without `css_id` so selectors and goldens stay stable. |
| crispy-bootstrap5 2026.3 | `bootstrap5/layout/baseinput.html`, `bootstrap5/inputs.html` | Never override these from the package. They belong to the host project and theme. |
| django-tables2 | Table template set by the package; `table_page_range` yields `'...'` | Keep the block names. |
| Bootstrap 5 JS | Only via `cv.adapters` | `Alert.getOrCreateInstance(el).close()` needs the `fade show` classes for the animation and removes the element itself. |

### Internal boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `button_classes` ↔ `view.*` | Local imports inside functions (`button_classes.py:210-214`) | Keep it that way. The module must stay importable with bare settings. `FORM_KINDS` / `VARIANT_LOCATIONS` can live in `button_classes.py` itself, which avoids the import. |
| `settings.py` ↔ `view.label_mode` | Deferred import inside `_action_settings_messages` | E108 goes there. Do not import at module level. |
| crispy adapters ↔ `CrudView` | Duck-typed (`getattr(form, "cv_view")`, `context.get("view")`) | `crud_views.lib.crispy` must keep working without a CrudView. |
| Python ↔ JS | DOM contract only (`data-cv-*`, ids, `cv-key`) | Every attribute Phase 2/3A adds becomes public in Phase 4. |
| core ↔ `crud_views_workflow` | Subclass (`WorkflowForm.submit_icon = "workflow"`) | Core never imports extensions. Phase 2 sets the icon in the extension. |

---

## Verified Plan References

| Plan reference | Status |
|----------------|--------|
| `button_data.py:83` default, `:12` LOCATIONS | ✓ exact |
| `base.py:311`, `:318` `"icon"` fallbacks | ✗ off by one: **`:312`** (`return target_default or "icon"`) and **`:317`** (`mapping.get(key, "icon")`). The acceptance grep still matches. |
| `card.py` `cv_card_actions_label_mode = "both"` | ✓ `lib/views/card.py:28` |
| `button_classes.py:207-218` `_action_key_parts` | ✓ `:207-221` |
| `test_button_classes_checks.py:79` `form:submit:icon` rejected | ✓ |
| `buttons.md:112` "64 keys" vs actual 70 | ✓ (the test already asserts 70, `test_button_classes.py:84`) |
| `form.py:76` cancel `name="reset"` | ✓ |
| `viewset.js:37-44` cancel handler, `modal.js:75-83` submitter | ✓ both |
| `stability.md:29` lists only button_classes | ✓ (`:28` heading, `:29` names) |
| `action_menus.md` Mermaid `MICON` node | ✗ it is in `docs/reference/context_buttons.md:256` |
| "goldens that contain a form" (Phase 2) | ✗ none contain form buttons (see Golden-test prerequisite) |
| "`button_classes.py` (no new keys)" (Phase 2) | ✗ `form:hidden-label` and `form:icon-host` are needed (S3) |
| 34 icon names | ✓ `DEFAULT_ICONS` has 34; `save`, `cancel`, `filter-reset` absent; `delete`, `filter`, `workflow`, `page-previous/next` present |
| All listed docs/tests files exist | ✓ (`docs/reference/{settings,action_menus,card-list-view,buttons,icons,theme,javascript,messages,list_view}.md`, `docs/migrating-1.0.md`, all named tests, vitest files in `tests/js/`) |
| E108 free | ✓ (E100–E107 used) |

## Open Questions (for phase discussions)

1. **Pagination hidden-label key name (3B).** `snippets/pagination.html` hard-codes `visually-hidden` and uses no key at all. One `pagination:hidden-label` key read by *both* paginations would be more consistent than `table:hidden-label` (table only) and costs the same one key. Recommended, but it is the maintainer's naming call before Phase 4 freezes it.
2. **Alert frame class literals (3A scope).** `btn-close` and `alert-dismissible fade show` stay hard-coded. Either add `alert:close` / `alert:dismissible` keys in 3A, or have `theme.md` state that a non-Bootstrap theme overrides the frame for those classes. Decide before Phase 4.
3. **`LEAF_KEYS` as one set or two (2).** Freezing a union means `cv_href` and `cv_type` are "leaf keys" for leaves that never get them.
4. **The filter `"Filter"` label is untranslated** (`buttons.py:326`). It becomes visible in 1B's `both`/`label` modes.
5. **The `CardAction.no_label` step stays in the card chain** (out of scope, #254). 1A has to keep it between `CardAction.label_mode` and the view attribute.

## Sources

- Source files read directly: `src/crud_views/lib/view/{button_data,label_mode,base,buttons}.py`, `lib/views/{card,list}.py`, `lib/{button_classes,icons,settings,messages}.py`, `lib/crispy/{buttons,form}.py`, `templatetags/crud_views.py`, `templates/crud_views/tags/{button/*,alert,context_action_filter}.html`, `templates/crud_views/{table/bootstrap5,snippets/pagination}.html`, `static/crud_views/js/{adapters,viewset,list.filter,modal,tooltip}.js`. Confidence: HIGH.
- Tests: `tests/test1/test_button_classes{,_checks,_templates}.py`, `test_action_label_mode_config.py`, `tests/test1/golden/**`. Confidence: HIGH.
- Docs: `docs/reference/{buttons,action_menus,context_buttons,theme,javascript}.md`, `docs/development/stability.md`. Confidence: HIGH.
- Third-party, read from the installed packages: `crispy_forms/layout.py` (`BaseInput`), `crispy_bootstrap5/templates/bootstrap5/{inputs,layout/baseinput}.html`. Confidence: HIGH.
- Planning inputs: `.planning/PROJECT.md`, `superpowers/plans/2026-10-24-concept-review-followups.md`, `.planning/codebase/ARCHITECTURE.md`.

---
*Architecture research for: django-crud-views theme surface (concept-review follow-ups milestone)*
*Researched: 2026-10-25*
