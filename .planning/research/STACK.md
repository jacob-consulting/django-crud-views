# Stack Research

**Domain:** Theme surface of a reusable Django UI package (django-crud-views 0.30.0 → 1.0.0): label-mode defaults,
`form:*` class keys, crispy-forms buttons through a crud_views `<button>` leaf, alert dismiss through a JS adapter,
django-tables2 pagination with registry icons, stability policy.
**Researched:** 2026-10-25
**Confidence:** HIGH overall. Every library claim below was checked against the installed source in `.venv`
(the `uv.lock` versions), upstream changelogs and the upstream source at release tags. Nothing rests on training data
alone.

> Scope: this milestone adds **no new dependencies**. The research question is which behaviours of the existing
> dependencies the seven changes rely on, where those behaviours differ from what the phase plan assumes, and what not
> to reach for. The codebase map (`.planning/codebase/STACK.md`) covers the rest of the stack.

## Headline findings (read these first)

1. **Overriding `render()` on crispy's `Submit` / `Reset` does not reach the filter form's buttons.** (HIGH)
   `ListViewFilterFormHelper` adds its buttons with `helper.add_input(...)`. crispy-bootstrap5's `inputs.html` renders
   `helper.inputs` with `{% include "bootstrap5/layout/baseinput.html" %}`. It never calls `input.render()` and it
   ignores the input's `template` attribute. This is the same in crispy-bootstrap5 2023.10, 2025.6, 2026.3 and 2026.9,
   and upstream issue #775 ("layout.Submit and helper.add_input produce different results") has been open since 2018.
   Phase 2 therefore has to **move the filter Submit/Reset out of `add_input` and into a layout**
   (`FormActions(Submit, Reset)`). The `Hidden` sort/order inputs can stay in `add_input`, since they should keep
   rendering as `<input type="hidden">`. The create/update/delete forms already put their buttons in
   `Layout(..., FormActions(...))` (`crispy/form.py:47`, `:135`), so `render()` does reach those.
2. **`BaseInput.render()` treats the button value as a Django template**: `Template(str(self.value)).render(context)`.
   It has done so in every crispy release from 2.0 to 2.7. The labels it renders include `cv_action_label` and
   `submit_label`, which can be built from model data. The new `render()` must **not** do this. It should autoescape
   the value as plain text. That closes a template-injection hole and is what makes the #257 escaping acceptance test
   meaningful. Note it in the Breaking entry: a project that passed `"{{ object.name }}"` as a button value loses the
   context rendering. (HIGH)
3. **django-tables2 renders its table template with an isolated context**: `template.render(context={"table": table},
   request=request)`. The calling template's context is reachable only as `table.context`. The tags 3B needs,
   `cv_icon` and `cv_button_class`, are plain `simple_tag`s that take no context, so they work as they are. Do not add
   a `takes_context` tag that reads `view` to `table/bootstrap5.html`. (HIGH)
4. **Bootstrap 6.0.0-alpha.1 (2026-10-08) ships ESM-only JavaScript with no `window.bootstrap` global.**
   `cv.adapters` is built from `() => globalThis.bootstrap`, so on Bootstrap 6 every adapter finds no component. The
   planned `el.remove()` fallback for `alert.close` is the right default. The stability policy should freeze the
   **`cv.adapters` method names**, not any Bootstrap names (v6 also renames Modal → Dialog). (HIGH: Bootstrap blog)
5. **Django 4.2 left LTS support in April 2026, and crispy-forms 2.6+ / crispy-bootstrap5 2026.3+ require Django ≥5.2.**
   The 4.2 cell of the nox matrix therefore resolves to crispy-forms 2.5 and crispy-bootstrap5 2025.6. The crispy APIs
   Phase 2 touches are byte-identical across 2.0–2.7, so this is no blocker. It is something the stability doc (Phase 4)
   should state, and the 1.0.0 support matrix should decide on separately. (HIGH)

## Recommended Stack

### Core Technologies (versions as locked; no bumps required)

| Technology | Locked (`uv.lock`) | Latest upstream | Purpose in this milestone | Why / what matters | Conf. |
|---|---|---|---|---|---|
| Django | 5.2.14 | 6.1.2 | System checks (E108, E210/E211/W291/W292 extensions), `render_to_string` for the form leaf, `setting_changed` | Check ids follow `<label>.<E\|W><nnn>`. The repo already uses two namespaces: `crud_views.E1xx` for settings and `viewset.E2xx/W2xx` for views. **E108 is free**; E210/E211/W291/W292 already exist (`label_mode.py`, `action_menu.py`, `view/buttons.py`), so Phase 2 *extends* them and does not create them | HIGH |
| django-crispy-forms | 2.6 (4.2 cell: 2.5) | 2.7 (2026-07-29, Django 6.1) | `Submit` / `Button` / `Reset` adapters | `BaseInput.__init__(name, value, *, css_id, css_class, template, **kwargs)` and `render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs)` are identical in 2.0, 2.5 and 2.7 (checked at the tags). `form_style` was removed in 2.0, so do not accept it. `kwargs` are flattened to a string **inside `__init__`** (`self.flat_attrs = flatatt(kwargs)`, `_`→`-`), so pop `data_cv_cancel_url` and friends **before** `super().__init__()` | HIGH |
| crispy-bootstrap5 | 2026.3 (4.2 cell: 2025.6) | 2026.9 (Django 6.1) | Wraps layout buttons in `layout/formactions.html` | `inputs.html` hard-codes `bootstrap5/layout/baseinput.html` (finding 1). `layout/button.html` is `<button {{ button.flat_attrs }}>{{ button.content\|safe }}</button>`, the template the plan rightly bypasses | HIGH |
| django-tables2 | 3.0.0 | 3.0.1 (2026-08-29, Django 6.1, drops Py3.10) | Table pagination (3B) | 3.0.0 renamed `{% querystring %}` → `{% querystring_replace %}` so it no longer shadows Django 5.1's built-in. Keep the repo's version-agnostic `{% cv_querystring %}`. Upstream `bootstrap5.html` blocks are `pagination`, `pagination.previous`, `pagination.range`, `pagination.next`. The crud_views template is a full copy (no `{% extends %}`), so **keep those four block names** because overriding themes use them | HIGH |
| Pydantic | 2.13.4 | 2.14.1 | `CrudViewsSettings.label_mode_defaults` (1A) | Settings are read with `from_settings()` when the class body runs, and `crud_views_settings = CrudViewsSettings()` is created at module import. A strictly typed field (`dict[str, Literal[...]]`) would raise `ValidationError` **at import** and crash startup before E108 could report anything. Follow the existing convention: type the field `Any`, validate in `check_messages`, merge in the accessor | HIGH |
| Bootstrap (host-loaded, not bundled) | 5.3.3 in example | 5.3.8 (5.4.0 announced); 6.0.0-alpha.1 | Alert JS API (3A) | `Alert.getOrCreateInstance(el).close()` exists from **5.0.2** (absent in 5.0.0). `close()` fires the cancelable `close.bs.alert`, removes `.show`, and waits for the transition only if `.fade` is present, then calls `remove()`, fires `closed.bs.alert` and `dispose()`. The data API finds its target with `closest(".alert")` (a **class**), or with `data-bs-target` | HIGH |

### Supporting Libraries / Tooling (already present)

| Library | Version | Purpose here | When to use | Conf. |
|---|---|---|---|---|
| lxml + cssselect | 6.1.0 | Assert `button[type=submit][name=…]`, escaped labels, `aria-current`, `aria-disabled` | Rewrite `test_crispy_buttons.py`'s `tag()` helper, which matches `<input\b` only, to a CSS-selector query | HIGH |
| Vitest + jsdom | ^5.0.3 / ^30.1.2 | `adapters.test.js` (alert with/without `Alert` component), `viewset.test.js` (delegated dismiss), `list.filter.test.js` (label-only toggle) | Stub `globalThis.bootstrap = { Alert: { getOrCreateInstance } }` for the Bootstrap path, and delete it for the fallback path | HIGH |
| polib | locked | `.po` sync test | 3B: "Table navigation" becomes a translated msgid. `previous` / `next` / `pagination` / `Close` already exist in `crud_views/locale/de` | HIGH |
| pytest-django `settings` fixture / `monkeypatch` | 4.12–4.14 | 1A settings variants | `override_settings` does **not** reach `crud_views_settings` (frozen at import). Use `monkeypatch.setattr(crud_views_settings, …)` as existing tests do (`test_action_label_mode_config.py:79`), or add a `setting_changed` receiver | HIGH |

## Prescriptive implementation notes per phase

### 1A: `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (per-key merge)

- Field: `label_mode_defaults: Any = from_settings("CRUD_VIEWS_LABEL_MODE_DEFAULTS", default={})`. Keep the **raw**
  value on the model so `check_messages` can show it, as `header_level` and the label-mode maps already do.
- Package defaults live in one immutable constant next to `LabelMode`:
  `DEFAULT_LABEL_MODES = MappingProxyType({"context": "icon", "list": "icon", "card": "both"})`. Phase 2 adds
  `"form": "label"`.
- Accessor `default_label_mode(location)`: `{**DEFAULT_LABEL_MODES, **valid_items(raw)}[location]`. Merge per key at
  read time (a dict lookup costs nothing). Skip invalid entries silently because E108 reports them, the same "invalid
  counts as unset" rule `view/buttons.py:401` uses. Never mutate the constant.
- Merge semantics: this is **per-key merge** (like `get_button_classes()`:
  `{**DEFAULT, **THEME, **settings}`), not whole-dict replacement (like the per-key action maps). The docs must say
  which is which, as the plan already requires.
- E108 (`crud_views.E108`): not a dict, unknown location (not in `LOCATIONS` / known set), or a value outside
  `LABEL_MODES`. Put it in `CrudViewsSettings._action_settings_messages` next to E105/E106.
- Decide whether a theme layer is wanted (`register_label_mode_defaults`). **Recommendation: no.** Label mode is a
  project decision, not a framework decision. Adding a theme hook makes one more public name to freeze in Phase 4.

### 1C: `form:<kind>:<mode>`

- No library involvement. `get_button_class("form", kind, mode)` already prefers a mode key. Pin the docs' key count
  by test as the plan says.

### 2: crispy buttons through `tags/button/form.html`

Use this shape, which is crispy-version-agnostic across 2.0–2.7:

```python
class _LeafButtonMixin:
    kind: str                      # "submit" | "cancel" | "delete" | "filter-submit" | "filter-reset"
    input_type: str                # inherited from layout.Submit / Button / Reset

    def __init__(self, name, value, *, slot=None, icon=None, **kwargs):
        self.cv_cancel_url = kwargs.pop("data_cv_cancel_url", None)   # pop BEFORE crispy flattens kwargs
        self.cv_kind = (slot or self.slot).split(":", 1)[1]
        self.cv_icon = icon
        super().__init__(name, value, **kwargs)                       # keeps css_id / css_class / flat_attrs semantics

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        # NO Template(str(self.value)).render(context): the value is text, autoescaped by the leaf
        data = cv_button_data(context, "form", ...)                   # contract incl. cv_type/cv_name/cv_value/cv_id
        return render_to_string("crud_views/tags/button/form.html", data)   # returns SafeString
```

- **Keep the id/name rules byte-compatible with `baseinput.html`.** A multi-word name is slugified
  (`{% if input.name|wordcount > 1 %}…|slugify`). The default id is `f"{input_type}-id-{slugify(name)}"`, which
  `BaseInput.__init__` already computes. Reuse `self.id` and do not recompute it.
- **Always emit `type=` explicitly.** `<button>` defaults to `type="submit"`, so a cancel button without
  `type="button"` would submit the form.
- Render with a **fresh dict** (`render_to_string(name, data)`), not `context.update(...)` +
  `context.flatten()` the way crispy does. crispy pushes `input` into the shared context and relies on
  `KeepContext` in `render_field` to clean up. A fresh dict stops leaking and keeps the leaf contract (`LEAF_KEYS`)
  closed.
- `css_class` handling: `BaseInput.__init__` does `self.field_classes += f" {css_class}"`. The existing mixin sets
  `field_classes` from the table *before* `super().__init__`, so table classes plus `css_class` arrive combined.
  Pass the combined string to the leaf, or split them: keep the table class from `{% cv_button_class "form" cv_key
  cv_label_mode %}` and append `css_class`. The second is needed for the mode key to apply, because the class
  depends on the resolved mode, which is only known at render time. **Store `css_class` separately** and do not let
  `field_classes` carry it.
- Filter form: build the helper with a layout. `ListViewFilterFormHelper.__init__` gets `form=None` today
  (`mixins.py:319`). Pass `filterset.form` and append
  `FormActions(Submit(..., slot="form:filter-submit"), Reset(..., slot="form:filter-reset"))` to
  `build_default_layout(form)`. Keep `Hidden` via `add_input`. The wrapper markup changes from `inputs.html`'s
  `<div class="mb-3"><div class="">` to `formactions.html`'s near-identical `<div class="mb-3 …"><div class="">`. That
  golden diff is already allowed in Phase 2. Projects with their own `formhelper_class` that still `add_input(Submit)`
  get crispy's `<input>`; say so in `migrating-1.0.md`.
- POST data is unchanged: an activated `<button type=submit name value>` contributes `name=value` exactly like
  `<input type=submit>`. `event.submitter` and `requestSubmit()` (used by `modal.js` / `viewset.js`) work with both.

### 3A: `cv.adapters.alert`

```js
alert: {
    close(el) {
        const Alert = component(ns, "Alert");
        if (Alert) Alert.getOrCreateInstance(el).close();   // fade + close.bs.alert/closed.bs.alert preserved
        else el.remove();                                   // any non-Bootstrap page, and Bootstrap 6 without a global
    },
},
```

- Put the fallback **inside the adapter**, not only in the `viewset.js` handler. A theme that replaces
  `cv.adapters.alert` then owns the whole behaviour, and `cv.bootstrapAdapters(ns)` stays the single
  Bootstrap-aware place. This differs from the plan's wording ("without an `Alert` component the handler removes the
  element"). Either works; inside the adapter is cleaner for the stability contract.
- Delegated handler: `e.target.closest("[data-cv-alert-dismiss]")` → `btn.closest('[role="alert"]')`. Use
  `role="alert"`, not `.alert`, so non-Bootstrap frames work. Bootstrap's own data API uses `.alert`.
- Do not render both `data-bs-dismiss="alert"` and `data-cv-alert-dismiss` on the stock button. Both listeners would
  fire, and `close.bs.alert` would be dispatched twice. A theme override that keeps `data-bs-dismiss` keeps working
  through Bootstrap's data API, as the plan says.
- Accessibility: Bootstrap's docs warn that focus is lost when an alert is removed. The fallback cannot fix that
  either. Leave it documented, and do not add a new event (`cv:alert:closed`) unless a consumer needs one, because
  every event becomes a frozen name in Phase 4.

### 3B: table pagination

- Use `{% cv_icon "page-previous" %}` / `{% cv_icon "page-next" %}`, `{% cv_button_class "table" "hidden-label" %}`
  (new key, default `visually-hidden`) and `{% cv_querystring %}`. All of these are context-free, which suits
  tables2's isolated context.
- tables2 renders the previous/next blocks **only** when `has_previous` / `has_next` is true. The #241 markup has a
  disabled end. Put the `{% if %}` **inside** `{% block pagination.previous %}`, so a theme that overrides the block
  sees both states. That changes the block's contract, so document it in the migration note.
- The `'...'` ellipsis items in `pagination.range` currently render `<a class="page-link">` without `href`. Render them
  as `<span class="page-link">` with no link role while you are in the file. That matches the #241 snippet's
  `<span>` for the active page.

### 4: stability doc

- Freeze **crud_views names only**: `cv.adapters.{modal,tooltip,collapse,alert}` method names,
  `cv.bootstrapAdapters(ns)`, the `data-cv-*` DOM contract, leaf templates and their context keys, and the tables2
  template's block names. State the supported dependency floors (crispy-forms ≥2.0, crispy-bootstrap5 ≥2023.10,
  django-tables2 ≥2.5.3, Bootstrap ≥5.0.2 for `getOrCreateInstance`) and say that Bootstrap's own data attributes are
  **not** part of the crud_views contract.

## Installation

```bash
# Nothing new. Existing dev setup:
task dev           # uv venv --python=3.12 + uv pip install .[all,dev,test,examples]
# Optional, not required by this milestone: refresh the lock to pick up Django 6.1-confirmed patch releases
uv lock --upgrade-package django-crispy-forms --upgrade-package crispy-bootstrap5 --upgrade-package django-tables2
```

Do **not** raise the floors in `pyproject.toml` (`django-crispy-forms>=2.0`, `crispy-bootstrap5>=2023.10`,
`django-tables2>=2.5.3`). Every API used here exists at those floors, and raising them would drop Django 4.2
mid-milestone.

## Alternatives Considered

| Recommended | Alternative | When the alternative makes sense |
|---|---|---|
| Subclass `layout.Submit/Button/Reset`, override `render()` | Set `template = "crud_views/tags/button/form.html"` on the input (crispy's own hook) | Only for buttons that always sit in a Layout and need no computed context. It gets `input` but not the `cv_button_data` contract, still runs the value through `Template()`, and `add_input` ignores it anyway |
| Move filter buttons into `FormActions` | Ship a custom `helper.template` (a copy of `bootstrap5/whole_uni_form.html` that loops `{{ input.render }}`) | If the filter form must keep crispy's `inputs.html` wrapper byte-for-byte. Cost: one more template copied from crispy-bootstrap5, which drifts when it changes |
| Raw setting value (`Any`) + accessor merge + check | `pydantic.field_validator(mode="before")` that merges defaults on the model | If settings were validated lazily. Here the model is built at import, so a validator that raises crashes startup instead of producing E108 |
| Adapter-internal `el.remove()` fallback | Hard dependency on `bootstrap.Alert` (throw `missing("Alert")` like `modal.show`) | Never for alerts. A missing dismiss is cosmetic, unlike a missing modal, so failing soft is right |
| Keep the copied `crud_views/table/bootstrap5.html` | `{% extends "django_tables2/bootstrap5.html" %}` and override only the pagination blocks | Would shrink the file, but upstream's `table` block uses `querystring_replace` (3.x only) and would break the 2.x floor. Keep the copy |

## What NOT to Use

| Avoid | Why | Use instead |
|---|---|---|
| `crispy_forms.bootstrap.StrictButton` as the base for form buttons | Renders `layout/button.html` → `{{ button.content\|safe }}` (unescaped). Runs `content` through `Template()`. Has no `name`/`value` semantics, so POST data changes. Defaults `type="button"` | Subclass `layout.Submit/Button/Reset` + own `render()` |
| `HTML('<button …>')` layout objects | The string is a template rendered with full context, with no escaping of interpolated labels and no class table or label mode | The leaf template |
| Overriding `bootstrap5/layout/baseinput.html` or `bootstrap5/inputs.html` from crud_views' template dir | Global: it changes **every** crispy form in the host project, including non-crud_views forms, and fights other apps for the same path | Leaf template under `crud_views/tags/button/` |
| Calling `Template(str(value)).render(context)` in the new `render()` | Template injection from model-derived labels. It also defeats the #257 escaping test | Pass `value` as plain text and let autoescape handle it |
| `mark_safe` / `\|safe` on `cv_label`, `cv_value`, `cv_title` | Same XSS class crispy 2.0 itself removed ("widespread use of `\|safe` … removed") | Autoescape; `render_to_string` already returns `SafeString` for the whole leaf |
| `<button>` without explicit `type` | Defaults to `submit`, so cancel/reset would submit the form | Always `type="{{ cv_type }}"` |
| `pydantic-settings` (`BaseSettings`) | It is only a transitive lock entry, not a dependency. It reads env vars and dotenv, not `django.conf.settings`. It would add a runtime dependency for nothing | Existing `BaseModel` + `from_settings()` |
| Strict Pydantic typing on new settings fields | `ValidationError` at import time beats the system-check framework to it, giving the user a traceback instead of `crud_views.E108` | `Any` + `check_messages` |
| `django.test.override_settings` in 1A tests for `crud_views_settings` fields | The model snapshot is taken at import, so the override has no effect and tests pass for the wrong reason | `monkeypatch.setattr(crud_views_settings, …)`, or add a `setting_changed` receiver that rebuilds the field |
| `data-bs-dismiss="alert"` in stock templates | A Bootstrap data-API leak, the last one outside the dropdown templates | `data-cv-alert-dismiss` + `cv.adapters.alert.close` |
| `bootstrap.Alert` via `globalThis.bootstrap` anywhere outside `cv.bootstrapAdapters` | Bootstrap 6 has no global, and themes cannot swap it | `cv.adapters.alert` |
| `{% querystring %}` in table templates | Means Django's built-in in 5.1+ but tables2's in <3.0, with different semantics | `{% cv_querystring %}` (existing shim) |
| A `takes_context` crud_views tag inside `table/bootstrap5.html` that reads `view` | tables2 renders with `{"table": table}` only, so `view` is missing | Context-free `cv_icon` / `cv_button_class`, or `table.context.view` |
| Adding Bootstrap 6 support in this milestone | Alpha. Prefix-style classes (`md:d-none`), Dialog instead of Modal, ESM-only. It would reopen every class-table default | Keep 5.3. Make sure the adapter contract is the only JS coupling and say so in `stability.md` |

## Stack Patterns by Variant

**If a page loads Bootstrap 5 JS (stock case):**
- `cv.adapters` = `cv.bootstrapAdapters(() => globalThis.bootstrap)`. The alert fades and fires
  `close.bs.alert` / `closed.bs.alert`.

**If a page uses Bootstrap 6 (ESM) or another framework (e.g. a Tabler theme without a global):**
- The theme assigns `cv.adapters = cv.bootstrapAdapters(importedNamespace)` or its own object. Without it, alerts
  still close through the fallback, but modal/collapse throw `missing(...)` by design.

**If a project renders crispy buttons via its own `FormHelper.add_input(Submit(...))`:**
- It gets crispy's `<input>` even with crud_views' `Submit`, because `inputs.html` bypasses `render()`. Document this
  limitation, and advise moving the buttons into `FormActions`.

## Version Compatibility

| Package | Compatible with | Notes |
|---|---|---|
| django-crispy-forms 2.0–2.5 | Django 4.2 | 2.6 (2026-03) dropped 4.2/5.0/5.1. BaseInput API unchanged 2.0→2.7 |
| django-crispy-forms 2.6–2.7 | Django 5.2, 6.0, 6.1 | 2.7 confirms 6.1 |
| crispy-bootstrap5 2023.10–2025.6 | Django 4.2 | 2026.3 dropped 4.2. Needs crispy-forms ≥2.3 from 2024.10 on. `inputs.html` include unchanged throughout |
| django-tables2 3.0.x | Django ≥4.2 (metadata), 5.2/6.0/6.1 declared | `querystring` → `querystring_replace`. 3.0.1 drops Python 3.10 (irrelevant, floor is 3.12) |
| django-tables2 2.5.3–2.8 | Django 4.2 | Old `{% querystring %}` name; `cv_querystring` handles both |
| Pydantic 2.2.1–2.14.1 | Python 3.12–3.15 | Only `BaseModel` / `field_validator` used; no v2-minor-specific APIs needed |
| Bootstrap ≥5.0.2 | `Alert.getOrCreateInstance` | 5.0.0/5.0.1 lack `getOrCreateInstance`. 5.3.8 is the last 5.3 patch, 5.4.0 announced |
| Bootstrap 6.0.0-alpha.1 | Not supported | ESM-only, no global; adapters need an explicit namespace |
| Django 4.2 | **EOL since April 2026** | Still in the nox matrix and classifiers. Decide before 1.0.0 (out of scope here, but the stability doc must name the supported range) |

## Sources

- Installed source, `.venv/lib/python3.12/site-packages` (versions from `uv.lock`): `crispy_forms/layout.py`
  (`BaseInput`, `Submit`, `Button`, `Reset`), `crispy_forms/bootstrap.py` (`StrictButton`, `FormActions`),
  `crispy_forms/helper.py` (`add_input`, `render_layout`), `crispy_forms/templatetags/crispy_forms_tags.py`,
  `crispy_forms/utils.py` (`flatatt`), `crispy_bootstrap5/templates/bootstrap5/{inputs,layout/baseinput,layout/button,
  layout/formactions}.html`, `django_tables2/templatetags/django_tables2.py` (`RenderTableNode.render`),
  `django_tables2/templates/django_tables2/bootstrap5.html`. HIGH
- Upstream source at tags 2.0 / 2.5 / 2.7 (crispy-forms `layout.py`) and 2023.10 / 2025.6 / 2026.9 (crispy-bootstrap5
  `inputs.html`), fetched from raw.githubusercontent.com. HIGH
- Changelogs: django-crispy-forms `CHANGELOG.md` (2.7 / 2.6 / 2.0 breaking notes), crispy-bootstrap5 `CHANGELOG.md`,
  django-tables2 `CHANGELOG.md` (3.0.0 `querystring_replace`, 1.21 isolated context). HIGH
- crispy-forms issue #775 (add_input vs layout rendering, open). HIGH
- PyPI JSON API (latest versions and `requires_dist`, 2026-10-25); npm registry (`bootstrap` dist-tags: 5.3.8 latest,
  6.0.0-alpha.1 next). HIGH
- Bootstrap 5.3 Alerts docs (getbootstrap.com/docs/5.3/components/alerts/), `js/src/alert.js` and
  `js/src/util/component-functions.js` at 5.3.8 (jsDelivr), bundle grep for `getOrCreateInstance` at 5.0.0/5.0.2. HIGH
- Bootstrap blog, "Bootstrap 6 Alpha" (2026-10-08): ESM-only, no `window.bootstrap`, Dialog, prefix classes. HIGH
- Repository: `src/crud_views/lib/settings.py`, `lib/button_classes.py`, `lib/crispy/{buttons,form}.py`,
  `lib/views/{list,mixins}.py`, `static/crud_views/js/{adapters,viewset}.js`, `templates/crud_views/{tags/alert.html,
  table/bootstrap5.html,snippets/pagination.html}`, `locale/de/LC_MESSAGES/django.po`, existing check ids. HIGH

---
*Stack research for: django-crud-views theme surface (concept review follow-ups)*
*Researched: 2026-10-25*
