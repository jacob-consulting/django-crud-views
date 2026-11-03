# Pitfalls Research

**Domain:** Theme surface of a reusable Django UI package (django-crud-views 0.30.0 → 1.0.0): label-mode defaults,
filter toggle, class-key grammar, crispy form buttons through a leaf, alert dismiss adapter, table pagination,
stability policy
**Researched:** 2026-10-25
**Confidence:** HIGH for crispy/JS/template findings (read from the installed sources: django-crispy-forms 2.6,
the 2.0 tag on GitHub, crispy-bootstrap5 2026.3, django-tables2 3.0.0, the repo itself, and the downstream Tabler
theme in `../tabler-test/crud_views_tabler` with the `crispy_tabler` pack). MEDIUM for the Django 6.0 `format_html`
removal and jsdom `SubmitEvent.submitter` support, which are not re-verified against release notes in this pass.

The main risks are: (1) a fix that works under the stock Bootstrap 5 pack but quietly skips code paths a downstream
theme uses, and (2) names getting frozen in Phase 4 before anyone has decided on them. The ten critical pitfalls
come first. Each one lists warning signs, a prevention strategy and the phase that owns it.

---

## Critical Pitfalls

### Pitfall 1: Overriding `BaseInput.render()` does not touch the filter buttons (`helper.add_input`)

**What goes wrong:**
Phase 2 overrides `render()` on `Submit` / `Button` / `Reset`. Buttons inside a layout (`FormActions(...)` in
`CrispyFormMixin.helper` and `CrispyDeleteForm.helper`) switch to `<button>`. The two filter buttons do not.
`ListViewFilterFormHelper` adds them with `self.add_input(...)` (`lib/views/list.py:70-73`). Crispy renders
`helper.inputs` through the pack's `inputs.html`, which runs `{% include "<pack>/layout/baseinput.html" %}` for each
input and **never calls `input.render()`**. This holds for crispy-bootstrap5 (`inputs.html`, `whole_uni_formset.html`)
and for the `crispy_tabler` pack the Tabler theme uses (`CRISPY_TEMPLATE_PACK = 'crispy_tabler'`, its vendored
`inputs.html` hard-codes `crispy_tabler/layout/baseinput.html`). The filter `Apply` / `Reset` buttons stay `<input>`,
get no label mode, no icon and no `cv-key`. Acceptance criterion "both filter buttons show icon and text" fails. It
can also pass by accident if the test only renders a form, not a list page.

**Why it happens:**
People assume crispy renders every layout object through `render()`. Only layout objects take that path. Inputs added
with `add_input` take a template include.

**How to avoid:**
- In the Phase 2 spec, name both render paths and choose one design for the filter buttons:
  - **Recommended:** move them into a layout. For example, build the default layout (crispy
    `helper.build_default_layout(form)` / `Layout(*form.fields)`) and append `FormActions(Submit, Reset)` plus the
    hidden sort/order inputs. The buttons still render inside `{% crispy filter.form filter.form.helper %}`, so
    Tabler's overridden `tags/list_filter.inner.html` keeps working unchanged.
  - **Not recommended:** render the buttons from crud_views' own `list_filter` template outside `{% crispy %}`.
    Tabler overrides `crud_views/tags/list_filter.inner.html` and calls `{% crispy %}` only, so its filter would lose
    both buttons silently.
  - **Not viable:** overriding crispy pack templates (`bootstrap5/inputs.html`). That only covers one pack and fights
    the project's template-pack choice.
- Moving from `inputs` to `FormActions` changes the wrapper markup (`<div class="mb-3"><div class="{{ field_class }}">`
  becomes `formactions.html`). Golden-test it, list it under Breaking DOM, and check that a user subclass of
  `ListViewFilterFormHelper` that sets its own `layout` still works.
- Document that a project calling `helper.add_input(crud_views.lib.crispy.Submit(...))` in its own forms still gets
  `<input>`. Alternatively, make `Submit` warn or the check flag it.

**Warning signs:**
`grep -n add_input src/` still lists `Submit`/`Reset` after Phase 2. A list-page golden with a filter still contains
`<input type="submit"`. The tests pass only with `CRISPY_TEMPLATE_PACK="bootstrap5"`.

**Phase to address:** 2 (the spec must decide this before implementation)

---

### Pitfall 2: Crispy's `Template(str(self.value)).render(context)` produces SafeString, so labels are not escaped

**What goes wrong:**
`BaseInput.render()` (unchanged from crispy 2.0 to 2.6) runs `self.value = Template(str(self.value)).render(context)`.
`Template.render()` returns a `SafeString`, so `baseinput.html`'s `value="{{ input.value }}"` emits it without
escaping. Two consequences:
1. A label containing `<b>` or `"` is emitted raw today. A new leaf that copies the value from the crispy object
   inherits the SafeString and stays unescaped, even though the leaf "autoescapes".
2. The value is **evaluated as a template**. A label built from model data (`f"Delete {obj}"`, a cancel label from
   `get_cancel_button_context`) that contains `{{ ... }}` or `{% ... %}` is executed against the full page context
   (`request`, `user`, `csrf_token`, `cv_*`). That is a small server-side template injection.

**Why it happens:**
crispy wants "button value can be a variable in context". People keep calling `super().render()`, or copy that line
into the override "for compatibility".

**How to avoid:**
- The override must **not** call `super().render()` and must **not** template-evaluate the value. Pass
  `str(self.value)` (forcing the lazy translation at render time) as a plain `str` so autoescape applies. If
  `{{ var }}` in button values is to stay supported, document it as removed in `docs/migrating-1.0.md` (Breaking)
  rather than keep it.
- Build any HTML in Python with `format_html` / `conditional_escape`, never with `mark_safe(f"...")`.
  crispy-bootstrap5's `button.html` (`{{ button.content|safe }}`) must never be reachable.
- Tests:
  - `submit_label = "<b>x</b> \" '"` renders `&lt;b&gt;` in **both** the `value` attribute and the body.
  - A label `"{{ request.user.username }}"` renders literally.
  - A `mark_safe` label: decide explicitly whether it stays safe (recommend yes, mirroring `BreadcrumbItem`) and test
    it.

**Warning signs:**
The override contains `Template(` or `super().render(`. The escaping test only checks the body text, not the `value`
attribute. The test uses `str` labels but never `gettext_lazy` ones.

**Phase to address:** 2

---

### Pitfall 3: The leaf rendered with `context.flatten()` picks up the page's `cv_*` keys

**What goes wrong:**
crispy passes the whole page `Context` to `render()`. If the leaf is rendered with `render_to_string(leaf,
context.flatten() | data)`, or `cv_button_data(ctx, "form")` is fed the page context, the form button sees the
surrounding view's keys: `cv_label_mode`, `cv_key`, `cv_icon_action`, `cv_action_label`, `cv_variant`. Nothing in
the test project sets those at page level, so the bug stays invisible there. It shows up in a downstream project or
theme that sets them, and also inside `{% for %}` loops over context actions where the outer keys leak in. The
existing `cv_button_data` logic reads exactly those keys:
- `ctx.get("cv_label_mode") or default`
- `ctx.get("cv_action_short_label") or ctx.get("cv_action_label")`
- `if not label: label_mode = "icon"`

Passing a `Context` object instead of a dict also raises `TypeError` ("context must be a dict rather than Context")
on every supported Django.

**Why it happens:**
Crispy's own idiom is `render_to_string(template, context.flatten())`, and people copy it.

**How to avoid:**
- Build the button dict from the button object only, then render the leaf with an **isolated** dict: the output of
  `cv_button_data` plus nothing else (the Python equivalent of `{% include ... only %}`).
- Add a test that renders a form inside a context that already holds `cv_label_mode="icon"` and
  `cv_action_label="X"`, and asserts the form buttons ignore them.
- Audit `cv_button_data` for location-specific fallbacks that are wrong for `form`:
  - `if not label: label_mode = "icon"`
  - the short-label swap
  - `kind == "action"` gating W292-style degradation

  Give `form` its own branch rather than reusing the card/context fallbacks.

**Warning signs:**
`flatten()` appears in `lib/crispy/buttons.py`. Form button output differs between the create page and the same form
inside a modal partial.

**Phase to address:** 2

---

### Pitfall 4: `name`, `id` and POST data drift during `<input>` → `<button>`

**What goes wrong:**
The plan states "POST data unchanged". That only holds if the leaf reproduces several behaviours of `baseinput.html`
and `BaseInput.__init__`:
- **Name slugifying.** `name` is slugified when it has more than one word (`{% if input.name|wordcount > 1 %}`).
  `Submit("Save changes", ...)` posts `save-changes`. A leaf that writes `name="{{ cv_name }}"` raw changes the POST
  key.
- **Default id.** The id defaults to `f"{input_type}-id-{slug}"` (`submit-id-submit`, `button-id-reset`). Golden
  files, project CSS/JS and `list.filter.js` (`#filter-button-reset`, set via `css_id`) depend on ids.
- **Value.** For `<input>` the `value` is both the label and the posted value. For `<button>` they split. The leaf
  must write `value="{{ cv_value }}"` explicitly; a theme override that drops it posts `name=""`.
  `CrispyDeleteForm` tests post `{"delete": "Delete"}`.
- **Type.** `<button>` without `type` defaults to `submit`. A cancel `<button>` that loses `type="button"` in a theme
  override submits the form instead of navigating.
- **Named controls shadow form methods.** The cancel button is `name="reset"` and submit is `name="submit"`. Both
  shadow `form.reset` / `form.submit` on the `HTMLFormElement` (true for `<input>` too, so not new). New JS must not
  call `form.submit()`; use `requestSubmit()` (`viewset.js` already does; the `submit-on-change` handler at
  `viewset.js:34` calls `el.form.submit()` and breaks if such a form ever contains a submit button named `submit`).
- **flatatt underscores.** crispy's `flatatt` turns `_` into `-` (`data_cv_cancel_url` → `data-cv-cancel-url`). The
  adapter must keep that mapping for every other kwarg, or project kwargs like `data_confirm` change name.

**Why it happens:**
The new leaf is written from the rendered HTML, not from crispy's template and constructor logic.

**How to avoid:**
- Write a parametrised parity test: for each of the five kinds, with and without `css_id`, a multi-word name, extra
  kwargs and `css_class`, compare the attribute set (`name`, `id`, `value`, `type`, `class`, extras) of old
  `<input>` and new `<button>`, parsed with `html.parser`, not regex.
- Keep `test_delete` / `test_cancel_origin` untouched except for the selector, as the plan says. Tabler's
  `test_delete` posts `{"delete": "Delete"}` and must stay green unchanged.

**Warning signs:**
Rewritten tests post different data than before. Ids in goldens change. The `<input\b` helper in
`test_crispy_buttons.py` is replaced with a regex that accepts both tags, which hides attribute drift.

**Phase to address:** 2

---

### Pitfall 5: Table classes computed in `__init__`, translation frozen, instance mutated in `render()`

**What goes wrong:**
`_TableClassMixin.__init__` resolves `field_classes = get_button_class(...)` at construction time, without a mode. The
label mode is only known at render time (setting → ViewSet → view → per-key map), so mode keys
(`form:submit:icon`, enabled by 1C) never apply if classes are still resolved in `__init__`. The opposite mistakes
are just as common:
- forcing `str(self.value)` in `__init__`, which freezes the language active when a class-level helper was built;
- caching the resolved mode or label on `self` in `render()`. crispy itself mutates `self.value`; a helper defined at
  class or module level is shared across requests and threads, so state leaks between users and languages.

`css_class` must still be appended to the table classes (`test_project_css_class_still_appended`), but crispy merges
it into `field_classes` in `BaseInput.__init__`, so the override has to keep it in a separate attribute.

**How to avoid:**
- Store the raw inputs (`name`, `value` as lazy, `slot`/kind, `css_class`, `css_id`, attrs) in `__init__`.
- Resolve classes, mode, icon and label in `render()` into **locals** passed to the leaf. Never assign to `self` in
  `render()`.
- Test with a class-level helper rendered twice under two `translation.override()` languages and two label-mode
  settings.

**Warning signs:**
`self.field_classes` is still read by the leaf path. A test needs `importlib.reload`.

**Phase to address:** 2

---

### Pitfall 6: Settings read at import time, so the new defaults map cannot be tested or switched per test

**What goes wrong:**
`crud_views_settings = CrudViewsSettings()` evaluates every `from_settings()` at import (`settings.py:279`, a known
CONCERNS item). Adding `label_mode_defaults: dict = from_settings("CRUD_VIEWS_LABEL_MODE_DEFAULTS", {})` the same way
means:
- `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=...)` silently does nothing, so tests "pass" against the package
  defaults;
- the 1A acceptance ("`{"context": "both"}` turns every unmapped toolbar button into icon+text") gets verified via
  `monkeypatch` on a private object;
- a merged dict cached once (e.g. a module-level `_DEFAULTS = {**PACKAGE, **setting}`) goes stale.

**How to avoid:**
- Make `default_label_mode(location)` read the setting lazily (`getattr(settings, ...)` per call, or a cache cleared
  by a `setting_changed` receiver, as `reset_button_classes_cache()` already is for the class table).
- Write at least one test with `override_settings`, so lazy reading is pinned.
- Do not mutate the package default dict when merging. The AUDIT already fixed "mutation of settings lists"; do not
  reintroduce it.

**Warning signs:**
New tests use `monkeypatch.setattr(crud_views_settings, "label_mode_defaults", ...)`. The merged dict is built at
module scope.

**Phase to address:** 1A (Phase 2 relies on it for `"form"`)

---

### Pitfall 7: Per-key merge in one setting, whole replacement in its siblings, nobody notices

**What goes wrong:**
`CRUD_VIEWS_LABEL_MODE_DEFAULTS` merges per key over `{"context": "icon", "list": "icon", "card": "both"}`. The
neighbouring `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` / ViewSet / view maps replace the whole dict layer by layer
(`cv_first_inline_keys`). Users and theme authors expect the same semantics everywhere. Two failure modes:
- A project writes `{"context": "both"}` expecting replacement (gets merge, harmless).
- A project writes a ViewSet `context_actions_label_mode={"filter": "both"}` expecting merge with the setting-level
  map and loses every other key (silent visual regression).

Phase 2 adds a fourth per-key map (`CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`), which multiplies the confusion.

**How to avoid:**
- Add a table in `settings.md` and `action_menus.md` with one row per knob, columns "merge or replace", "layer",
  "keys".
- Use one sentence per setting docstring.
- Do not change the existing maps' semantics in this milestone (out of scope, and that would be a Breaking change).
  State it.

**Phase to address:** 1A (docs), re-checked in 2 and 4

---

### Pitfall 8: Changing `cv_card_actions_label_mode` from `"both"` to `None` breaks readers of the attribute

**What goes wrong:**
1A makes the card view default `None` ("use the map"). Code that **reads** the attribute directly now gets `None`:
- user templates (`{{ view.cv_card_actions_label_mode }}`);
- theme templates (Tabler overrides `crud_views/view_card.content.html` and `tags/card.html`);
- subclasses doing `if self.cv_card_actions_label_mode == "both"`;
- `label_mode_check(cls, "cv_card_actions_label_mode", ...)` (`card.py:112`), which must accept `None`;
- `docs/reference/card-list-view.md:71`, which documents the type as `str` with default `"both"`.

**How to avoid:**
- Grep the Tabler templates and the example project for the attribute. Change the type to `str | None` in the code,
  the docs and the E210 check together.
- Expose the resolved value through a method (`cv_get_card_actions_label_mode()`) and document that templates use the
  stamped `cv_label_mode`, not the attribute.
- Test that a subclass explicitly setting `"both"` still wins over `{"card": "label"}` (plan acceptance), **and** that
  `None` passes E210.

**Phase to address:** 1A

---

### Pitfall 9: The alert dismiss handler is too narrow or too eager and breaks themes that keep `data-bs-dismiss`

**What goes wrong:**
- **Double close.** The stock template renders both `data-bs-dismiss="alert"` and `data-cv-alert-dismiss` "for
  compatibility". Bootstrap's data API closes the alert, then the delegated handler calls
  `Alert.getOrCreateInstance()` on a detached element, or the fallback `el.remove()` runs after a fade. The result is
  console errors or a double `closed.bs.alert`.
- **Finding the alert by role.** The target is located with `closest('[role="alert"]')`. A theme that, for
  accessibility, renders non-error levels with `role="status"`, or nests the button in a wrapper with its own role,
  makes the handler find nothing (or the wrong ancestor) and the alert never closes.
- **Theme-assigned adapters without `alert`.** Before 3A, a theme might assign `cv.adapters = {modal, tooltip,
  collapse}` wholesale or set `cv.adapters` before `adapters.js` loads. With `Object.assign(bootstrapAdapters(),
  cv.adapters)` that keeps the stock `alert`, but a theme that assigns after load with `cv.adapters = {...}` drops it.
  Then `cv.adapters.alert.close` throws a TypeError and the fallback never runs.
- **Fallback skips Bootstrap events.** The `el.remove()` fallback skips the `close.bs.alert` / `closed.bs.alert`
  events that project code may listen to. Under Tabler, `cv.bootstrapAdapters(() => globalThis.tabler)` resolves
  `Alert` on the `tabler` namespace. If the namespace does not export `Alert`, the fallback always runs and the fade
  transition is lost.
- **Handler bound per element.** Wiring the handler per element at `DOMContentLoaded` misses alerts injected into the
  modal (`cvModalInject`) and error alerts added later.

**How to avoid:**
- Render **only** `data-cv-alert-dismiss` in the stock frame.
- Locate the frame with a dedicated attribute (`closest("[data-cv-alert]")`, rendered on the frame root) and fall back
  to `role="alert"` for overrides. Document the attribute in the DOM contract (Phase 4).
- Use one delegated `document` listener in `viewset.js`. Guard it with
  `const close = cv.adapters?.alert?.close; close ? close(el) : el.remove()`.
- Vitest cases:
  - with an `Alert` component;
  - without one;
  - with `cv.adapters.alert` deleted;
  - an alert injected after load;
  - a theme template still using `data-bs-dismiss` (the handler must not fire).
- Tabler follow-up note: its own `tags/alert.html` keeps `data-bs-dismiss` and its test
  `assertNotIn("data-bs-dismiss", html)` is only on the modal. Decide whether Tabler migrates to
  `data-cv-alert-dismiss` (recommended, so its frame stops relying on Bootstrap's data API).

**Phase to address:** 3A

---

### Pitfall 10: Freezing names in Phase 4 that nobody decided on, or freezing too broadly

**What goes wrong:**
The stability doc turns every listed name into semver API. Common mistakes:
- **Implicit freeze of undecided names.** The `cv_context_actions_label_mode` / `cv_context_action_label_mode`
  one-letter pair is "tracked separately". If Phase 4 lists `cv_*` view attributes wholesale, or the reference docs
  already list them (stability.md says "the same names shown in the reference documentation"), the pair freezes
  without a decision. The same applies to `CardAction.no_label` / `cv_no_label`, which are scheduled for removal at
  1.0.0 and must **not** appear as stable.
- **Wildcards.** Writing "`data-cv-*` attributes" or "the leaf templates and their context" without an explicit list
  freezes internal attributes such as `data-cv-filter-icon-open/close` (which 1B makes optional) and every incidental
  context key a leaf happens to receive.
- **Freezing helpers instead of contracts.** Listing `cv_button_data` (its signature) and `LEAF_KEYS` (as an exact
  set) blocks adding keys or parameters in a minor release. The plan's rule "adding an icon name is minor" must also be
  written for: leaf context keys, `LOCATIONS`, class-table keys, JS events, adapter methods and check IDs.
  Otherwise each addition is arguably a break.
- **Freezing values.** Default class strings (`"btn btn-primary"`) and icon glyph mappings should be explicitly
  **not** frozen; only key names are.
- **Private imports in the reference consumer.** Tabler imports `_get_renderers` and `_icon_str` (`checks.py:3`). The
  plan calls a public `is_library_renderer()` "optional". If it is not added, the reference consumer depends on
  private API from day one of 1.0 and any minor release can break it.
- **Check IDs and setting names left out.** Projects put `crud_views.E108`, `viewset.W292` and similar in
  `SILENCED_SYSTEM_CHECKS`. Renumbering or rescoping them breaks projects. Phase 2 also **reuses** E210/E211/W291/W292
  for form buttons, so a project that silenced W292 for toolbars now silences form warnings too. Say so in the
  CHANGELOG.

**How to avoid:**
- Make it a precondition of Phase 4 that the pair rename and the `no_label` removal are either done or explicitly
  listed as "deprecated, removed in 1.0.0" or "provisional".
- Define three tiers in `stability.md`: **Stable** (semver), **Provisional** (may change in a minor release with a
  CHANGELOG note; use it for adapter method extra arguments like Tabler's `tooltip.init(el, {location})` and for the
  form leaf context until the Tabler theme has used it for one release), and **Internal**.
- Enumerate DOM attributes and leaf keys explicitly. State the "adding is minor, renaming/removing is major" rule once
  for every set.
- Add `is_library_renderer` (or an equivalent public helper) before 1.0, and move Tabler to it in the Tabler
  follow-up.
- List system-check IDs and `CRUD_VIEWS_*` setting names as public.

**Warning signs:**
`stability.md` contains `*` globs. The guard test passes while the doc mentions `no_label`. Tabler's `checks.py`
still imports underscore names.

**Phase to address:** 4. The decisions it depends on (pair rename, `no_label`) must be raised at the 1A discussion,
because the 1A docs page is open then.

---

## Moderate Pitfalls

### Filter toggle (1B): host-placed icon classes combined with text

- **What goes wrong:** the toggle supports two icon placements. With host placement (#258), icon classes such as
  `bi bi-funnel` or `fa fa-filter` sit on the `<button>` itself, and `list.filter.js` swaps them via
  `data-cv-filter-icon-open/close`. With element placement, two `<span data-cv-filter-icon>` are hidden alternately.
  In `both`/`label` mode:
  - Host classes on a button with text can restyle the **label**. Font Awesome 4/5's `.fa` sets `font-family` on
    the element, so the word "Filter" renders in the icon font. Bootstrap Icons only style `::before`, so the default
    theme hides the bug.
  - In `label` mode the template must emit **no** host classes, **no** data-icon attributes and no spans, or an icon
    appears anyway, or the JS swap adds one on first click.
  - `title` and `data-cv-tooltip` must disappear outside `icon` mode (match `action.html`). Otherwise a tooltip
    duplicates visible text, and the accessible name ends up with the hidden-label span plus visible text, both
    "Filter".
  - The template branch has 3 modes × 2 placements × 2 expanded states = 12 renderings. Testing 3 misses the bugs.
- **Prevention:**
  - Parametrise a Python render test over the full 12-case matrix. Add vitest cases for `label` (no icons, click
    flips `aria-expanded` and POSTs) and for `both` with host placement (the swap touches only icon classes, never
    text).
  - Keep the default byte-identical (the `toolbar_publisher_list.html` golden).
  - Resolve the mode with `cv_get_action_label_mode("context", "filter")`, but decide explicitly what "target view
    default" (#269) means for a button with no target view. It must not pick up the list view's own
    `cv_context_action_label_mode` by accident, or, if it should, say so.
- **Phase:** 1B

### Class-key grammar (1C): accepting too much, or a count test that drifts

- **What goes wrong:**
  - Relaxing `_action_key_parts()` to "any `form:x:mode`" lets typos like `form:submitt:icon` pass W362.
  - The mode-key fallback reads `form:submit:icon` only if `get_button_class("form", kind, mode)` is called with the
    resolved mode. In Phase 2 a leaf that calls `{% cv_button_class "form" cv_key %}` without `cv_label_mode` makes
    the mode keys dead config, and nothing warns.
  - The docs-count test (parse "70 keys" from `buttons.md`) and 3B's new `table:hidden-label` key collide when 1C and
    3B merge in parallel: whichever merges second must update the number. CI catches it only if the second branch is
    rebased and re-run.
  - Option B (variants) renames `form:delete`, which Tabler registers in `TABLER_BUTTON_CLASSES` and asserts in its
    tests.
- **Prevention:**
  - Keep `FORM_KINDS` as the closed set, with reject tests for unknown kinds and for parts (`form:container:icon`).
  - In Phase 2, add a test that `{"form:submit:icon": "x"}` actually appears on an icon-mode submit.
  - Rebase 3B on 1C, or merge 3B after 1C, and re-run.
  - Choose A (no renames before freeze).
- **Phase:** 1C, verified again in 2 and 3B

### E108: unknown location keys and forward compatibility

- **What goes wrong:**
  - In 1A, `{"form": "label"}` is an *unknown key* until Phase 2 adds `"form"`. A project or the example settings
    that pre-set it fails E108 in between.
  - After 1.0, a setting written for 1.1 (a new location) hard-fails on 1.0 startup.
  - Invalid values crash renders in non-strict mode: `cv_button_data` raises `ValueError` for a bad mode even in
    production (CONCERNS, Known Bugs). Adding the defaults map without fixing this keeps the crash path.
- **Prevention:**
  - Error for invalid modes. Consider a Warning (W-level) for unknown location keys, and decide this in 1A.
  - Validate the location against `LOCATIONS` (single source), not a literal tuple, so Phase 2's addition updates
    the check automatically.
  - Fix the non-strict crash in 1A: log and fall back to `default_label_mode(location)`.
- **Phase:** 1A

### Golden files regenerated wholesale

- **What goes wrong:**
  - `CV_UPDATE_GOLDEN=1` regenerates every golden in the module. A phase whose rule is "only the form buttons change"
    rewrites unrelated goldens too, and the reviewer approves a large diff.
  - The `form_frame/*` and `action_menus/{list_full,cards_author_full}` goldens contain `<input`; card-pagination and
    action-menu goldens are separate modules.
- **Prevention:**
  - Per phase, assert the list of changed golden files in the PR description and with `git diff --stat
    tests/test1/golden`:
    - 1A, 1B, 1C and 4: zero;
    - 2: form-containing goldens only;
    - 3A: alert-containing;
    - 3B: table pagination.
  - Regenerate per test node id, not per module.
- **Phase:** all, especially 2

### Table pagination (3B): breaking tables2 block overrides and inconsistent a11y

- **What goes wrong:**
  - `crud_views/table/bootstrap5.html` mirrors django-tables2's template, including the override blocks
    `pagination.previous`, `pagination.range` and `pagination.next`. Projects (and the tables2 docs) override those
    blocks. Moving the `{% if has_previous %}` inside the block to render a disabled end changes what an existing block
    override renders: it now appears in the disabled state with a dead link. Renaming the blocks breaks overrides
    silently.
  - Card pagination (#241) hard-codes `visually-hidden` and puts `aria-current="page"` on the `<li>`. If 3B adds
    `table:hidden-label` but leaves card pagination on the literal, the "same markup" goal fails and two conventions
    remain.
  - The ellipsis `'...'` item renders as `<a class="page-link">` with no `href`: focusable in some ATs, announced as
    a link. It should be a non-interactive `<span>`.
  - An icon that resolves to empty (a theme without `page-previous`) leaves an empty link with only hidden text, so
    sighted users cannot see the control.
  - New msgids: reuse the card pagination msgids (`"previous"`, `"next"`, `"pagination"`, or one shared nav label)
    rather than inventing new ones, so one translation serves both. Translate "Table navigation" and add `.po`
    entries.
- **Prevention:**
  - Keep the block names. Put the disabled end in a new block or outside the existing ones, and document it in
    migrating-1.0.
  - Decide in 3B whether card pagination also moves to the new key (that changes the card goldens) and record the
    decision.
  - Render the ellipsis as `<span class="page-link">`.
  - Fall back to visible text when the icon is empty (or use a W29x-style check).
  - Tabler overrides `table/bootstrap5.html` itself, so it is unaffected, but the acceptance note should say whether
    Tabler adopts `table:hidden-label`.
- **Phase:** 3B

### Django-version traps in the new rendering code

- **What goes wrong:**
  - `format_html()` called with no args/kwargs (e.g. `format_html("<span>")`) is deprecated since Django 5.0 and
    removed in 6.0 (raises `TypeError`). It passes on 4.2 locally and fails on the 6.0 nox session. (MEDIUM: verify
    against the 6.0 release notes.)
  - `render_to_string(name, Context(...))` raises `TypeError` on all versions.
  - Django 4.2 is past end of support. Code written against 5.2+ APIs fails only in the 4.2 cell.
- **Prevention:** run the full nox matrix before pushing Phase 2, not just `pytest tests`. Use `format_html` only with
  arguments, and `mark_safe` for static strings.
- **Phase:** 2

### crispy version spread (floor `>=2.0`, tested only at 2.6)

- **What goes wrong:**
  - The override assumes `render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs)`. That signature has
    been stable from 2.0 to 2.6 (crispy 1.x had `form_style`), but the floor is untested (CONCERNS: no
    lowest-direct session).
  - `template_pack` may be a custom pack (Tabler's `crispy_tabler`). The leaf ignores it. Good, but then a project
    that relied on `Submit(..., template="my/baseinput.html")` loses its template override silently.
- **Prevention:**
  - Accept and ignore `template_pack` / `**kwargs`. Honour or reject (with a check or warning) an explicit
    `template=` kwarg, and document it in migrating-1.0.
  - Either add a lowest-direct nox session or raise the crispy floor to a tested version in the same PR.
- **Phase:** 2

---

## Minor Pitfalls

- **Icon names colliding with semantics.** `reset` would collide with the cancel button's `name="reset"`
  (`form.py:76`); the plan chooses `filter-reset`. Also keep `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` in sync (the sync
  test enforces it), and update the "34 names" sentence in docs, or better, stop quoting the count (Phase 2 makes
  37). *Phase 2, 4.*
- **vitest / jsdom `event.submitter`.** Modal-submit tests that rely on `SubmitEvent.submitter` need a jsdom version
  that implements it. Otherwise the test passes with `submitter === undefined` and `FormData(form, undefined)` drops
  the button's name/value without failing. Assert the posted body contains `delete=Delete`. *Phase 2.* (MEDIUM)
- **Icon-mode form buttons and tooltips in modals.** `data-cv-tooltip="form"` on a submit inside `#cv-modal-content`
  must be disposed on `cv:modal:unload` (it already is, via the delegated tooltip code). A test should check that a
  422 re-render leaves no orphan tooltip. *Phase 2.*
- **Label-in-name (WCAG 2.5.3).** In `both` mode do not add an `aria-label` that differs from the visible text. In
  `icon` mode the hidden-label span is the accessible name; the icon must be `aria-hidden` (`render_icon` does that
  for `<i>`; check SVG renderers such as Tabler's too). *Phases 1B, 2, 3B.*
- **Parallel branches conflicting in shared docs.** 1B, 3A and 3B touch `CHANGELOG.md` and `docs/migrating-1.0.md`;
  2 and 3A both touch `theme.md`. Rebase before merge and re-run `mkdocs build --strict`. *All.*
- **No downstream names in files.** Tabler follow-ups go in the acceptance note. It is easy to write "Tabler" into
  `theme.md` or a test docstring by accident; grep before pushing. *All.*

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep `add_input` for filter buttons and just restyle `<input>` | No wrapper-markup change | Filter buttons stay outside the leaf model forever; label modes don't apply; theme can't restyle | Never (it's the point of #257) |
| Call `super().render()` and post-process the HTML | Reuses crispy | SafeString value, SSTI, `<input>` survives in some packs | Never |
| Read `CRUD_VIEWS_LABEL_MODE_DEFAULTS` at import like other settings | Consistent with existing settings | `override_settings` dead; tests use monkeypatch on internals | Never for new settings; existing ones tracked in CONCERNS |
| Render stock alert with both `data-bs-dismiss` and `data-cv-alert-dismiss` | "Safe" migration | Double close, console errors, leak not actually fixed | Never |
| Stability doc as a hand-written list plus substring test | Quick | Doc drifts from code; substrings match wrong names | Only if the test also introspects code (see checklist) |
| Reuse E210/E211/W291/W292 for form buttons | No new IDs | Silencing toolbar warnings silences form warnings | Acceptable if documented in CHANGELOG |
| Hard-code `visually-hidden` in table pagination like card pagination | Matches #241 exactly | A non-Bootstrap theme copies the template again | Only if 3B is dropped |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| crispy `FormHelper.inputs` | Assuming `render()` is called | `inputs.html` includes `baseinput.html` directly; use a layout (`FormActions`) |
| crispy template packs (`crispy_tabler`) | Testing only `bootstrap5` | Run the form-button tests once with a non-bootstrap5 `CRISPY_TEMPLATE_PACK` (a minimal vendored pack in tests) |
| crispy `BaseInput.render` | Copying `Template(str(value)).render(context)` | Plain `str(value)`, autoescaped |
| crispy `flatatt` | Using Django's `flatatt` (no `_` → `-`) | Keep crispy's underscore→dash mapping for kwargs |
| Bootstrap data API | Keeping `data-bs-*` next to `data-cv-*` | One attribute; the adapter decides |
| `cv.adapters` theme merge | Assuming every entry exists | Optional-chain the new `alert` entry; fall back to `el.remove()` |
| django-tables2 template blocks | Renaming or restructuring `pagination.*` blocks | Keep the names; add new blocks for new parts |
| `gettext_lazy` labels | `str()` at construction | Force at render time |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Template-evaluating button values (crispy idiom) | Template injection from model-derived labels into page context (`request`, `user`, `csrf_token`) | Never `Template(value)`; escaping and literal-`{{` tests |
| Passing a SafeString label through the leaf | XSS via `value` attribute / body | Test with `"><script>` in `submit_label` and cancel label |
| Unvalidated extra kwargs rendered as attributes | Attribute injection if kwargs ever come from data | Escape values (`flatatt` does); keep names from code only |
| Alert dismiss handler removing `closest()` of arbitrary element | Clicking a crafted `data-cv-alert-dismiss` in user HTML (e.g. rendered markdown) removes page parts | Scope to `[data-cv-alert]` ancestors only |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Icon-only form buttons by default | Users can't tell Save from Cancel | Form default stays `label`; example project shows `both` |
| Tooltip + visible text in `both` mode | Duplicate announcement, visual noise | No `title`/`data-cv-tooltip` outside `icon` mode |
| Disabled pagination end as a focusable link | Keyboard focus lands on a dead control | `aria-disabled="true"`, no `href`, or a `<span>` |
| Alert fallback `el.remove()` without focus management | Focus is lost to `<body>` after closing | Move focus to a sensible target (or document as theme responsibility) |
| Host icon font on labelled buttons | Label renders in the icon font | Element placement for `both`/`label`, or document the limitation |

## "Looks Done But Isn't" Checklist

- [ ] **Form buttons (2):** the filter `Apply`/`Reset` on a *list page* are `<button>`. Verify with a list-page golden,
  not just a form render.
- [ ] **Form buttons (2):** the same output under a non-bootstrap5 `CRISPY_TEMPLATE_PACK`.
- [ ] **Form buttons (2):** `<b>` and `{{ x }}` labels escaped/literal in the `value` attribute **and** the body.
- [ ] **Form buttons (2):** POST body from a modal submit (vitest) contains the clicked button's `name=value`.
- [ ] **Form buttons (2):** a `form:submit:icon` class key actually lands on an icon-mode submit.
- [ ] **Form buttons (2):** the leaf is rendered with an isolated dict, and page-level `cv_*` keys do not leak.
- [ ] **Defaults (1A):** at least one test uses `override_settings`, not monkeypatch.
- [ ] **Defaults (1A):** `cv_card_actions_label_mode = None` passes E210, and docs/types say `str | None`.
- [ ] **Filter toggle (1B):** the 12-case render matrix, plus vitest for `label` and host-placed `both`.
- [ ] **Alert (3A):** `grep -rn 'data-bs-' src/crud_views/templates` lists only the dropdown templates. The handler
  works with `cv.adapters.alert` deleted and on modal-injected alerts.
- [ ] **Pagination (3B):** the `pagination.previous/range/next` block names are unchanged, the ellipsis is not a link,
  and the `.po` files are updated.
- [ ] **Stability (4):** the guard test checks both directions:
  - every documented dotted name resolves (`importlib` plus `getattr`), so the doc cannot list dead names;
  - every name in each public module's `__all__` (or the explicit theme set: `DEFAULT_ICONS` keys,
    `DEFAULT_BUTTON_CLASSES` keys, `LEAF_KEYS`, `LOCATIONS`, JS events grepped from `static/`, leaf template files on
    disk) is documented.

  Match backtick-delimited tokens with a regex, not substrings (`register_icons` must not match
  `register_icons_extra`).
- [ ] **Stability (4):** `no_label`/`cv_no_label` absent or marked "removed in 1.0.0", the label-mode pair decided,
  and Tabler's underscore imports replaced or explicitly called out.
- [ ] **Every phase:** `git diff --stat tests/test1/golden` matches the phase's allowed list.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Filter buttons still `<input>` after 2 ships | MEDIUM | Follow-up PR that moves them to `FormActions`; second Breaking DOM note (avoid by catching in the spec) |
| Name frozen in 4 that should change | HIGH after 1.0 (needs 2.0 or a deprecation alias cycle) | Before 1.0: rename plus alias; after: deprecate with alias for one major |
| Template-evaluated labels shipped | MEDIUM | Security patch release; Breaking note; escaping test |
| Alert double close | LOW | Remove `data-bs-dismiss` from stock frame; patch release |
| Golden regenerated wholesale hiding a regression | MEDIUM | `git log -p tests/test1/golden`, bisect, restore unrelated goldens |
| Import-time settings for the defaults map | LOW | Swap to lazy accessor plus `setting_changed` receiver; tests switch to `override_settings` |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 6 Import-time setting | 1A | An `override_settings` test changes rendered output |
| 7 Merge vs replace confusion | 1A (docs), 2, 4 | Docs table exists; `mkdocs build --strict` |
| 8 `cv_card_actions_label_mode` → `None` | 1A | E210 accepts `None`; explicit `"both"` wins; Tabler templates grepped |
| E108 forward-compat / non-strict crash | 1A | Bad mode logs and falls back in non-strict; strict raises |
| Undecided names (pair rename, `no_label`) raised | 1A discussion → 4 | Decision recorded in PROJECT.md Key Decisions before Phase 4 |
| Host-icon + text, 12-case matrix | 1B | Parametrised render test plus vitest label-only and host-both |
| Grammar too permissive / dead mode keys / count drift | 1C, 2, 3B | Reject tests; mode-key application test; count test after rebase |
| 1 `add_input` path skipped | 2 (spec) | List-page golden shows `<button>`; non-bootstrap5 pack test |
| 2 SafeString / template-evaluated value | 2 | Escaping and literal-`{{` tests on attribute and body |
| 3 Context leakage into leaf | 2 | Polluted-context test |
| 4 name/id/value/type parity | 2 | Parametrised attribute-parity test; `test_delete` unchanged |
| 5 Resolve at render, no instance mutation | 2 | Two-language, two-setting render of a shared helper |
| Django 6.0 `format_html` / crispy floor | 2 | Full nox matrix green; lowest-direct session or raised floor |
| 9 Alert dismiss double close / role / missing adapter | 3A | Vitest matrix (with/without Alert, deleted adapter, injected alert) |
| Pagination blocks / ellipsis / card consistency | 3B | Block-override test; golden; `.po` updated |
| 10 Premature / wildcard freeze, private imports | 4 | Bidirectional guard test; no globs; tiers defined; Tabler underscore imports addressed |

## Sources

- Repo: `src/crud_views/lib/crispy/{buttons,form}.py`, `lib/views/list.py:57-87` (`add_input` filter buttons),
  `lib/view/button_data.py:70-105`, `lib/view/base.py:280-318`, `lib/settings.py:279`, `static/crud_views/js/{adapters,
  viewset,modal,list.filter}.js`, `templates/crud_views/tags/{alert,context_action_filter}.html`,
  `templates/crud_views/table/bootstrap5.html`, `templates/crud_views/snippets/pagination.html`,
  `tests/test1/test_action_menus_golden.py` (`CV_UPDATE_GOLDEN`), `.planning/codebase/CONCERNS.md` (HIGH)
- django-crispy-forms 2.6 installed `crispy_forms/layout.py` (`BaseInput.render`, `flatatt`) and the 2.0 tag on
  GitHub (`raw.githubusercontent.com/django-crispy-forms/django-crispy-forms/2.0/crispy_forms/layout.py`): identical
  `BaseInput` (HIGH)
- crispy-bootstrap5 2026.3 `inputs.html`, `whole_uni_formset.html`, `layout/baseinput.html` (HIGH)
- django-tables2 3.0.0 `templates/django_tables2/bootstrap5.html` pagination blocks (HIGH)
- Downstream reference consumer `../tabler-test/crud_views_tabler` (`apps.py`, `checks.py` private imports,
  `tests.py` `<input type="submit"` and `data-bs-dismiss` assertions, overridden `tags/alert.html`,
  `tags/list_filter.inner.html`, `table/bootstrap5.html`, `tabler-adapters.js`) and `../crispy-tabler` vendored
  `inputs.html`/`baseinput.html` (HIGH)
- Django 5.0 deprecation of `format_html()` without arguments, removed in 6.0 (MEDIUM, from memory; verify in the
  Phase 2 spec)
- WCAG 2.5.3 Label in Name; WAI-ARIA `aria-current`/`aria-disabled` usage for pagination (MEDIUM, community standard)

---
*Pitfalls research for: django-crud-views theme surface before 1.0.0*
*Researched: 2026-10-25*
