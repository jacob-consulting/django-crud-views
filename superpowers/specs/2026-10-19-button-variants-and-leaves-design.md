# Buttons: variants, a class table and a logic/markup split

Date: 2026-10-19 (refreshed 2026-10-20 against `main` after PR #200)
Status: reviewed with the maintainer section by section; builder check done 2026-10-20, its findings answered under
"Builder check", the one open question (formset delete toggle) decided with the maintainer the same day

## Intent

django-crud-views styles its buttons through three unrelated mechanisms: a semantic `variant` that exists only on
`CardAction`, Bootstrap class strings hard-coded in twelve templates, and class strings held in Python (the action
menu toggle dict in `templatetags/crud_views.py`, the crispy cancel button in `lib/crispy/form.py`, the setting
`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`). Context and list actions carry no variant at all.

Building the Tabler theme (`tabler-test/docs/crud_views_upstream_questions.md`, points 2, 4 and 5) showed the cost.
The theme had to hard-code `create` as the primary action and `delete` as destructive by key, override six templates
that mix rendering decisions (disabled, POST, modal, menu split) with markup, and subclass `CrispyDeleteForm` to get a
red Delete button. Every upstream change to one of those six templates has to be re-ported by hand, and nothing
detects a stale copy.

The goal is **one button mechanism** in which:

- every action button has a **variant** (`primary`, `secondary`, `tertiary`, `danger`) that comes from the target
  view by default and can be overridden per button;
- the **classes** for a variant per location come from a **layered table** (package defaults, then theme, then
  project settings), the same way icons do;
- the **decisions** about what a button is (element, href, POST hook, modal, disabled, active, label visibility) are
  made **once, in Python**, and handed to small **leaf templates** that only draw. Themes override leaves and never
  copy logic.

## Baseline

`main` after PR #200 (commit 440ac55): 0.30.0 plus the unreleased JavaScript adapters change, which ships as its own
release before this one (`2026-10-20-js-adapters-jquery-free-core-design.md`, "Release order"). State inherited
from it: the filter toggle carries `aria-expanded` / `aria-controls`, the modal shell is `crud_views/modal/shell.html`,
and the goldens were regenerated there. This spec touches neither the filter toggle nor the modal beyond a class
attribute, and regenerates the goldens once more. "Today" below means this baseline.

## Goals

- `cv_action_variant` on every `CrudView`, flowing into context, list, card and menu-item buttons.
- `ContextButton.variant` and `CardAction.variant` as per-button overrides.
- `CRUD_VIEWS_BUTTON_CLASSES` and `register_button_classes()` for themes, layered like `CRUD_VIEWS_ICONS`.
- Leaf templates `tags/button/action.html`, `tags/button/menu_item.html`, `tags/button/container.html` with a
  documented context contract.
- The three Python-held class sites (menu toggle dict, crispy buttons, filter reset setting) read the table.
- `CrispyDeleteForm` gets the missing `get_delete_button()` hook.
- A project that does nothing renders the same DOM as the baseline, up to the listed markup differences
  (see "Acceptance").

## Non-goals

- Changing the stock look. Create stays an outline icon button, delete stays blue. Opinionated defaults are a
  possible later release, not this one.
- Icons next to visible card labels. The contract carries `cv_icon` for every button; the stock leaf draws it only
  when the label is hidden, which is today's output. Drawing both later is a one-line change to the stock leaf plus
  regenerated goldens (or a `CardAction` flag if it should be per button), and a theme can do it now by overriding
  the leaf. Not an API change.
- Updating `crud_views_tabler` (in the `tabler-test` repo). That comes later; this spec includes a written check
  of what the theme would need instead.
- jQuery or the global `bootstrap` (point 3 of the upstream questions).
- The modal `btn-close` (a Bootstrap structural class, not a `btn`) and the workflow `BadgeEnum` (badges, not
  buttons).
- Non-Bootstrap CSS frameworks. The `btn-group`, `dropdown-menu`, `d-none`, `visually-hidden` and `data-bs-*`
  markup stays Bootstrap. This spec makes Bootstrap-family themes (Tabler, AdminLTE, custom builds) a registration
  plus one or two small leaf overrides; it does not make Tailwind or Bulma a class-table job.

## Anti-goals

- Any `btn-` class left in a shipped template outside the table module, except `btn-close`. If a theme still has to
  copy a logic template to change a class, this failed.
- Modelling Bootstrap's class composition (base, variant, outline, size, state) as a nested structure. The table is
  flat: one key, one class string. Structural classes stay in the leaves.
- Variant as an open string. The vocabulary is closed so a typo is a system check error, not a missing class.

## Decisions made with the maintainer

1. **Stock output stays unchanged by default.** The variant defaults exist in the data; the stock table maps all four
   context and list variants to today's `btn-outline-primary`, and `card:danger` to today's `btn-secondary`. The
   goldens and class assertions are the acceptance test, as they were for icons.
2. **Four variants with view defaults.** `primary`, `secondary`, `tertiary`, `danger`. `CreateView` and the
   polymorphic create-select view default to `primary`, `DeleteView` to `danger`, everything else to `secondary`.
   `CardAction.variant` falls back to the target view's variant when not set.
3. **Templates stay compatible, settings break cleanly.** The current template names become thin logic templates,
   so whole-template overrides keep working. `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` is removed with a system
   error while still defined. The unused tags `cv_submit_button`, `cv_cancel_button`, `cv_delete_button` and their
   templates are removed.
4. **Shared leaves with the location passed in**, not one leaf per location: one action leaf, one menu item leaf, one
   container leaf.
5. **Upstream only, with a written Tabler check** (below). The theme is migrated in a follow-up.
6. **The formset delete toggle is in scope** (builder check, item 3): the two classes `formset.js` swaps come from
   the table, so a theme restyles formset controls without touching JavaScript.

## Design

### 1. Variants

**Vocabulary.** `crud_views.lib.view.Variant`, a `StrEnum` with `PRIMARY = "primary"`, `SECONDARY = "secondary"`,
`TERTIARY = "tertiary"`, `DANGER = "danger"`. Plain strings are accepted everywhere; the enum is for
discoverability and the check.

**View default.** New class attribute on `CrudView`, next to `cv_icon_action`:

```python
cv_action_variant: str = "secondary"
```

Overrides in core: `CreateView` and `PolymorphicCreateSelectView` (`crud_views_polymorphic`) set `"primary"`,
`DeleteView` sets `"danger"`. Ordered up/down, manage, workflow, detail, update, list and card stay `"secondary"`. Projects override
it per view like any `cv_` attribute. The filter toggle button is `secondary`.

**Flow into buttons.** `CrudView.cv_get_dict()` adds `"cv_variant": cls.cv_action_variant`. That dict is the base of
every list action, menu item and context action, so they get `cv_variant` with no further change. The parent,
child and sibling buttons in `lib/view/buttons.py` also end in `cls.cv_get_dict(...)` on the target view class, so
they need no change either (their `cv_icon_action` comes from the ViewSet's `icon_header`, a separate concern).
`FilterContextButton` is the one button that builds its dict without `cv_get_dict`; it carries no `cv_variant` and
its own template renders `secondary` directly (section 3). Card action data (`cv_get_card_action_data`) already
sets `cv_variant`; it now sets `action.variant` if given, else the target view's `cv_action_variant` (for
`child_name` actions: the child view's).

**Per-button override.**

- `ContextButton` gets `variant: str | None = None`. `get_context()` applies it after the target dict is built, the
  same way the declared label is applied (`_apply_label`): a set value replaces the view default.
- `CardAction.variant` changes from `str = "secondary"` to `str | None = None`. `None` means "the target view's
  variant". The card template context key stays `cv_variant`.

**Check.** One system check, `viewset.E209` (next free id in that range; builder confirms), reported for every
`CrudView` subclass whose `cv_action_variant`, every `ContextButton` whose `variant` and every `CardAction` whose
`variant` is not `None` and not one of the four values. Message names the owner, the attribute, the value and the
allowed set.

**Known consequence.** A `CardAction` without an explicit variant now inherits `danger` for a delete target; the
stock table maps `card:danger` to today's `btn-secondary`, so output is unchanged. The one input whose stock output
changes is a card action pointing at a create view without an explicit variant, which now renders `btn-primary`
instead of `btn-secondary`. No test, doc or example does this. Changelog line, no special case.

### 2. The class table

**Module.** `crud_views/lib/button_classes.py`, built like `icons.py`:

```python
DEFAULT_BUTTON_CLASSES: dict[str, str]
_THEME_BUTTON_CLASSES: dict[str, str]

def register_button_classes(classes: dict[str, str]) -> None   # theme API, from AppConfig.ready()
def get_button_classes() -> dict[str, str]                      # defaults ⊕ theme ⊕ settings, cached
def get_button_class(location: str, slot: str) -> str           # "" for None/"" entries and unknown keys
def reset_button_classes_cache() -> None
def button_class_check_messages() -> list[CheckMessage]
```

`⊕` is a per-key dict merge, later wins. Cached on first use, reset on `setting_changed` for
`CRUD_VIEWS_BUTTON_CLASSES` and on registration, exactly like icons.

**Keys.** Flat strings `"<location>:<slot>"`. The key set is closed: the package defines every key, projects and
themes override values. The table holds style classes only. Structural classes that markup, CSS or JavaScript
depend on (`dropdown-toggle`, `cv-menu-toggle`, `d-none`, `flex-grow-1`, `active`, `visually-hidden`) stay in the
leaves.

**Default table** (reproduces today's classes; the two form-button token differences are listed under Acceptance):

| Key | Default |
|---|---|
| `context:primary`, `context:secondary`, `context:tertiary`, `context:danger` | `btn btn-outline-primary btn-lg` |
| `list:primary`, `list:secondary`, `list:tertiary`, `list:danger` | `btn btn-outline-primary btn-xs` |
| `card:primary` | `btn btn-primary btn-sm` |
| `card:secondary`, `card:danger` | `btn btn-secondary btn-sm` |
| `card:tertiary` | `btn btn-outline-secondary btn-sm` |
| `context:container` | `btn-group btn-group-lg` |
| `list:container` | `btn-group btn-group-xs` |
| `card:container` | `d-flex gap-2` |
| `context:menu-toggle` | `btn btn-outline-primary btn-lg` |
| `list:menu-toggle` | `btn btn-outline-primary btn-xs` |
| `card:menu-toggle` | `btn btn-secondary btn-sm` |
| `context:menu-wrapper`, `list:menu-wrapper` | `btn-group` |
| `card:menu-wrapper` | `dropdown` |
| `menu:item` | `dropdown-item` |
| `form:submit` | `btn btn-primary` |
| `form:cancel` | `btn btn-secondary` |
| `form:delete` | `btn btn-primary` (what crispy renders today) |
| `form:filter-submit` | `btn btn-primary` (what crispy renders today) |
| `form:filter-reset` | `btn btn-secondary` |
| `formset:control` | `btn btn-light` |
| `formset:container` | `btn-group` |
| `formset:control-danger` | `btn btn-danger` (the delete button of a row marked for deletion) |
| `card-order:toggle` | `btn btn-outline-secondary` |
| `card-order:container` | `btn-group btn-group-sm` |
| `language:toggle` | `btn btn-outline-secondary` |
| `object-detail:property-detail` | `btn btn-link p-0 ms-1 align-baseline text-muted` |

The four context variants and the four list variants are identical on purpose (decision 1). The `object-detail`
entry lives in the core table so that `crud_views_object_detail` has no `btn-` literal either; its template loads
the core tag.

**Rendering.** One template tag in `crud_views` templatetags (and re-exported in `crud_views_object_detail` tags,
as `cv_icon` is):

```django
{% cv_button_class "form" "submit" %}
{% cv_button_class cv_location cv_variant %}
```

Backed by `get_button_class(location, slot)`. An entry set to `None` or `""` renders no class (switches the
classes off, like an icon set to `None`). A non-str value renders nothing and is reported by `E361`. An unknown key
renders nothing at render time; `W362` reports it at startup.

**Python consumers.**

- `_ACTIONS_MENU_STYLE` in `templatetags/crud_views.py` is deleted. `cv_actions_menu` passes `cv_location` only;
  `tags/actions_menu.html` uses `{% cv_button_class cv_location "menu-wrapper" %}` and
  `tags/actions_menu_toggle.html` uses `{% cv_button_class cv_location "menu-toggle" %}` followed by the structural
  `dropdown-toggle cv-menu-toggle`.
- crispy: crispy's inputs carry base classes (`Submit`: `btn btn-primary`, `Button`: `btn`, `Reset`:
  `btn btn-inverse`) and **append** `css_class` rather than replacing it, so today the cancel button renders
  `btn btn btn-secondary` and the filter reset `btn btn-inverse btn btn-secondary`. The package therefore ships
  `Submit`, `Button` and `Reset` subclasses (module placement left to the builder) whose base classes come from the
  table (`form:submit` for `Submit`; the caller passes the slot for the others) and which still append a
  `css_class` given by a project. `CrispyFormMixin.get_submit_button()`, `get_cancel_button()`, the new
  `CrispyDeleteForm.get_delete_button()` and the filter form helper (`ListViewFilterFormHelper` in
  `lib/views/list.py`) use them with `form:submit`, `form:cancel`, `form:delete`, `form:filter-submit`,
  `form:filter-reset`. The `css_class` key disappears from `get_cancel_button_kwargs()`; a project that overrides
  the kwargs hooks and passes `css_class` gets it appended as before. The duplicate `btn` and the dead
  `btn-inverse` token disappear (Acceptance).
- `CrispyDeleteForm`: `get_delete_button_kwargs()` returns `{"name": "delete", "value": _("Delete")}`,
  `get_delete_button()` builds the button, `helper` uses `self.get_delete_button()` instead of the inline
  `Submit("delete", "Delete")`. The label becomes translatable as a side effect; changelog line.

- `formset.js`: `set_delete()` (lines 438-446 today) swaps the literals `btn-light` / `btn-danger` on
  `.cv-form-ctrl-delete`; they are the only class literals in the file. `formsets/control.html` renders the delete
  button with `data-cv-class="{% cv_button_class 'formset' 'control' %}"` and
  `data-cv-class-danger="{% cv_button_class 'formset' 'control-danger' %}"`; `set_delete()` removes every token of
  the attribute being left and adds every token of the one being entered, and leaves the structural
  `cv-form-ctrl-delete` alone. The script stays on jQuery as decided in the adapters spec.

**Removed.**

- `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` and `CrudViewsSettings.filter_reset_button_css_class`. `E360` while the
  setting is still defined, hint names `CRUD_VIEWS_BUTTON_CLASSES["form:filter-reset"]`.
- The tags `cv_submit_button`, `cv_cancel_button`, `cv_delete_button` and the templates `tags/button_submit.html`,
  `tags/button_cancel.html`, `tags/button_delete.html`. No shipped template uses them. The one user is the test
  helper `render_cancel_tag` in `tests/test1/test_cancel_origin.py`, which reads the cancel href through
  `{% cv_cancel_button %}`; it is rewritten to call the view hook `get_cancel_button_context()` directly. The view
  hooks `get_cancel_button_context()` etc. that the crispy mixin uses stay.

**Checks** (`crud_views/checks.py`, registered like `check_icons`):

| Id | Level | Condition |
|---|---|---|
| `crud_views.E360` | error | `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` is still defined |
| `crud_views.E361` | error | a resolved table value is neither a str nor `None` |
| `crud_views.W362` | warning | a theme or project entry uses a key that is not in `DEFAULT_BUTTON_CLASSES` (typo guard) |
| `viewset.E209` | error | a variant outside the four values (section 1) |

**Theme API.**

```python
def ready(self):
    from crud_views.lib.button_classes import register_button_classes

    register_button_classes({
        "context:primary": "btn btn-primary",
        "context:secondary": "btn btn-icon",
        "list:secondary": "btn btn-sm btn-icon btn-ghost-secondary",
        "list:danger": "btn btn-sm btn-icon btn-ghost-danger",
        "form:delete": "btn btn-danger",
    })
```

Precedence: package defaults, theme registrations (later app in `INSTALLED_APPS` wins), project settings.

### 3. Logic and markup split

**The normaliser.** `crud_views/lib/view/button_data.py`:

```python
def cv_button_data(ctx: dict, location: str) -> dict
```

Input: a resolved action dict as the tags produce it today after `cv_resolve_action` (hidden actions are already
`None` and never reach it). `location` is `"context"`, `"list"` or `"card"`. Output, the **leaf contract**:

| Key | Type | Meaning |
|---|---|---|
| `cv_location` | str | `context`, `list`, `card` |
| `cv_tag` | str | `button` when disabled or when the target is POST without modal; else `a` |
| `cv_href` | str or absent | the URL, for `a` only |
| `cv_submit_target` | str or absent | the hidden form id (`cv_form_<oid>`) for POST without modal |
| `cv_modal`, `cv_modal_size` | bool, str | modal trigger data, unchanged |
| `cv_disabled`, `cv_disabled_reason` | bool, str | disabled state, unchanged |
| `cv_active` | bool | the button targets the current view (`cv_is_active`), in every location |
| `cv_key` | str | the action key (always present; card buttons gain it, see Acceptance) |
| `cv_label` | str | card: `cv_label` if set, else the short label; context and list: the action label |
| `cv_short_label` | str | the menu item text: card: the same as `cv_label`; context and list: the short action label, else the action label |
| `cv_label_visible` | bool | true for card buttons that have a label and `no_label` is false; false otherwise |
| `cv_title` | str or absent | set whenever the label is not visible: context and list: the full action label; card: `cv_label` (today's card title) |
| `cv_icon` | str or None | the icon value (`cv_icon_action`) |
| `cv_variant` | str | section 1; `"secondary"` when the input dict carries none (dicts built without `cv_get_dict`) |
| `cv_flex` | bool | card only; false elsewhere |

These keys and the three leaf names are public API, documented on the theme page one sentence per key. Changing
them later is a breaking change. The leaves receive **only** the contract keys (plus Django's standard context),
never the raw action dict: a leaf that reads an undocumented key fails in the leaf unit tests instead of quietly
coupling a theme to internals. Custom button templates (`template`, `template_code`, whole-template overrides of
the logic templates) keep receiving the raw dict as today.

The decisions encoded today in `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` and
`tags/actions_menu_item.html` (the `cv_disabled` / `cv_access` / `cv_action_enabled` / `cv_list_action_method` /
`cv_modal` / `cv_is_active` branches) move into this function and nowhere else. The function also handles the
per-location differences that exist today: card buttons may show a label, and a card button's title and hidden
text are its card label, not the full action label.

**Leaves.** New presentation-only templates under `crud_views/tags/button/`:

- `action.html`: one element from the contract. Class attribute:
  `{% cv_button_class cv_location cv_variant %}{% if cv_active %} active{% endif %}{% if cv_flex %} flex-grow-1{% endif %}`.
  Attributes: `href` or `type="button"`, `disabled` + `data-cv-disabled`, `data-cv-action="submit-form"` +
  `data-cv-target`, `data-cv-modal` + `data-cv-modal-size`, `aria-current="page"` when active, `title`, `cv-key`.
  Content: when `cv_label_visible`, `<span>{{ cv_label }}</span>` and no icon (today's card button with a label
  draws none; a theme leaf may draw both); otherwise `{% cv_icon cv_icon %}` followed by
  `<span class="visually-hidden">{{ cv_label }}</span>`.
- `menu_item.html`: the dropdown entry from the same contract, class `{% cv_button_class "menu" "item" %}` plus
  `active`, same attributes as today's `actions_menu_item.html` (title only for the context location). Includes
  `tags/actions_menu_item_label.html`, rewritten to the contract keys (`cv_icon` with `css="cv-icon-fw"`, else the
  empty `cv-icon-fw` placeholder; then `cv_short_label`); its output is unchanged.
- `container.html`: the wrapper and the loop:

  ```django
  <fieldset class="{% cv_button_class cv_location 'container' %}" aria-label="Actions" cv-{{ cv_location }}-container="true">
      {% for ctx in cv_buttons %}{% cv_render_button ctx cv_location %}{% endfor %}
      {% cv_actions_menu cv_group cv_location %}
  </fieldset>
  ```

  `cv_render_button` renders a resolved dict exactly as the per-key tags do (custom `template` / `template_code`
  buttons included), so the loop is not logic. The card container is the same leaf with `card:container`; its
  element is a `div` today and a `fieldset` would change the DOM, so the leaf takes `cv_container_tag`
  (`fieldset` for context and list, `div` for card) from the logic template. `aria-label="Actions"` is written for
  the `fieldset` tag only (on a plain `div` it has no role to attach to); `cv-{{ cv_location }}-container="true"` is
  written for every location, so the card row gains it (Acceptance). Hidden POST forms are rendered by the logic
  template **before** the wrapper, outside it, for all three locations (a hidden child inside the `btn-group` breaks
  Bootstrap's first/last-child corner rounding; see `test_context_actions_post.py`). Today the card renders its
  menu-item forms inside the `d-flex` row, so they move (Acceptance; a `d-none` form has no layout effect either
  way).

**Thin logic templates at the old names.** A new tag `{% cv_button location %}` takes the current template context
(the resolved dict), calls `cv_button_data`, and renders `tags/button/action.html` with the result.

- `tags/context_action.html`: `{% load crud_views %}{% cv_button "context" %}`
- `tags/list_action.html`: `{% load crud_views %}{% cv_button "list" %}`
- `tags/card_action.html`: `{% load crud_views %}{% include "crud_views/tags/list_action_form.html" %}{% cv_button "card" %}`
  (card buttons render their own hidden form inline today; the existing form template has the same condition)
- `tags/actions_menu_item.html`: `{% load crud_views %}{% cv_button cv_location kind="menu-item" %}` (same
  normaliser, menu item leaf)

Whole-template overrides of these names, `ContextButton(template=...)`, `template_code`,
`CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` and `cv_context_button_foldable` keep receiving the raw dict and keep working
unchanged. A custom button template may call `{% cv_button "context" %}` itself to get the normaliser and the stock
leaf.

**Containers unified.** `cv_get_context_action_group`, `cv_get_list_action_group` and `cv_get_card_action_group`
return an `ActionGroup` **always**: when the inline feature is off (inline keys `None`) every resolved button is in
`inline` and `menu` is empty, instead of returning `None`. `cv_actions_menu` already renders nothing for an empty
menu. The `{% if group is None %}` branch disappears from `tags/context_actions.html`, `columns/actions.html` and
`tags/card.html`; each becomes: resolve the group, render the hidden forms, include the container leaf with
`cv_buttons = group.inline`, `cv_group = group`, `cv_location`, `cv_container_tag`. Context and list render the forms
for `group.all`; card renders them for `group.menu` only, because inline card buttons render their own form inside
`tags/card_action.html` (unchanged, so a theme's own card template can still call `{% cv_card_action %}` standalone).
The golden test's purpose is to prove that the `None` path renders the pre-menu markup, so it is the right guard here
too.

`tags/card.html` keeps its card markup (title, body); only its action row becomes the container leaf include.

### 4. Forms

Covered by section 2. Behavioural additions, restated: `CrispyDeleteForm.get_delete_button()` /
`get_delete_button_kwargs()` exist and `helper` uses them; the delete, submit, cancel, filter submit and filter
reset classes come from the table; `WorkflowForm` inherits the submit class through `CrispyForm` with no change
of its own.

## Acceptance

**DOM-equivalent, not byte-equal.** A shared leaf cannot reproduce three templates' attribute orders, and the golden
comparison (`tests/test1/test_action_menus_golden.py`) strips whitespace but keeps attribute order and class token
order. The goldens are therefore regenerated **once** (`CV_UPDATE_GOLDEN=1`), and the regenerated diff may contain
only these differences, each with a changelog line:

| Change | Reason |
|---|---|
| attribute order unified across the three locations | one leaf |
| `active` moves to the end of the class string | table class plus structural suffix |
| card buttons gain `cv-key` | one leaf; list and context buttons already carry it |
| card POST actions render `<button type="button">` instead of `<a href="#">` | the `data-cv-action="submit-form"` handler in `viewset.js` is attribute based and works on either; the anchor was the odd one out |
| `aria-current="page"` on the active context action | a11y; the Tabler override already does it |
| the crispy cancel button renders `btn btn-secondary` instead of `btn btn btn-secondary`; the filter reset `btn btn-secondary` instead of `btn btn-inverse btn btn-secondary` | base classes from the table instead of crispy's defaults plus an appended `css_class`; forms are not in the goldens |
| the card action row gains `cv-card-container="true"` | one container leaf; the context and list rows already carry theirs |
| the hidden forms of card **menu** items move from inside the `d-flex` row to before it | one placement rule for all three containers |

Anything else in the diff is a bug. The class assertions in `test_card.py`, `test_action_menus_*.py` and
`test_context_actions_post.py`, the a11y tests, the POST tests and the examples project tests pass **unmodified**,
with one exception: `test_card_action_post.py` asserts today's `<a href="#" data-cv-action="submit-form">` and
changes to the `<button>` (fourth row above).

The golden normaliser (`_norm`) is extended to sort attributes and class tokens, so that future leaf edits which
only reorder attributes stop churning the files. Order is not part of the contract.

## Testing

- `cv_button_data`: every branch (disabled, POST, POST + modal, modal, GET, active) for each of the three locations,
  as plain unit tests with no rendering.
- Leaves: each of the three rendered from a contract-only context (every branch), so a leaf that reads a raw key
  fails here.
- Table: defaults, theme layer, project layer, per-key merge, cache reset on `setting_changed` and on registration,
  `None` / `""` entries, each check (`E360`, `E361`, `W362`).
- Guard test like the hard-coded icon class test (`test_icons_templates.py`): no `btn-` token in any shipped template
  of any app outside `button_classes.py`, `btn-close` excepted.
- Completeness: every `(location, slot)` used by a `cv_button_class` call in shipped templates exists in
  `DEFAULT_BUTTON_CLASSES`.
- Variants: view defaults per core view, `ContextButton.variant` override, `CardAction.variant` override and
  fallback to the target view (including `child_name` actions), `viewset.E209` on a typo in each of the three places.
- crispy: submit, cancel, delete, filter submit and filter reset classes from the table; a project `css_class` still
  appended; `CrispyDeleteForm.helper` uses the hook (overriding `get_delete_button_kwargs` changes the rendered
  button).
- Containers: a view with inline keys `None` renders the same DOM as before (goldens); `ActionGroup` with empty menu
  renders no toggle.
- Theme registration: an app registering classes in `ready()` changes the rendered classes; a project setting wins
  over it.
- `render_cancel_tag` in `test_cancel_origin.py` reads the href from `get_cancel_button_context()`; the tests
  themselves stay.
- `formset.js`: the existing vitest case "delete() toggles the hidden DELETE input and button styling" in
  `tests/js/formset.test.js` gets the two data attributes in its fixture and asserts the class list follows them
  (non-Bootstrap strings in the fixture, so a leftover literal fails). Runs under Node 22 (see
  `2026-07-21-js-test-harness-design.md`).
- Goldens regenerated once with the diff reviewed against the Acceptance table.

## Tabler check

Against the 23 overrides and `forms.py` in `crud_views_tabler` (tabler-test @ e41f05c), what the theme would need
after this change:

| Outcome | Files |
|---|---|
| Override disappears; table entries suffice | `tags/actions_menu_toggle.html` (`*:menu-toggle` with `btn-icon`), `tags/actions_menu_item_label.html` (only existed for the icon mapping, obsolete since 0.30), `tags/icon.html` (removed in 0.30) |
| Override disappears; replaced by **one** action leaf override (`tags/button/action.html`) | `tags/context_action.html` (visible label for `primary`, tooltip attributes), `tags/list_action.html`, `tags/list_action.inner.html`, `tags/card_action.html` (`btn-icon` when the label is hidden, `icon-sm` when shown) |
| Override disappears; replaced by **one** container leaf override (`tags/button/container.html`) | `tags/context_actions.html`, `columns/actions.html` (`btn-list` instead of `btn-group`) |
| Table entry covers the classes; override only if tooltip attributes are wanted | `tags/context_action_filter.html` |
| `forms.py` (`TablerDeleteForm`, `DangerSubmit`) disappears | `form:delete` entry |
| Untouched by this spec | `tags/card.html`, `snippets/card_order.html`, `tags/breadcrumb.html`, `snippets/pagination.html`, `table/bootstrap5.html`, `modal/content.html`, `shared/js.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `view_card/create/update/delete.content.html` |

Net: the six templates with copied logic become two leaf overrides with no logic, plus a `ready()` registration.
The key-based hard-coding of `create` and `delete` in the theme goes away because the core now says which button is
`primary` and which is `danger`.

Not verified: whether Tabler renders a `fieldset.btn-list` like its `div.btn-list`. Bootstrap's reboot removes the
fieldset's border, padding and margin and Tabler is built on Bootstrap, so it probably does, in which case the
container leaf override is only needed for the `role="group"` attribute the theme adds. The theme migration will
tell.

## Templates to change (0.30.0 inventory)

| Template | Change |
|---|---|
| `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` | thin logic template, `{% cv_button %}` |
| `tags/actions_menu_item.html` | thin, menu item leaf |
| `tags/actions_menu_item_label.html` | contract keys (`cv_icon`, `cv_short_label`), same output |
| `tags/context_actions.html`, `columns/actions.html`, `tags/card.html` | no `group is None` branch, container leaf include |
| `tags/actions_menu.html`, `tags/actions_menu_toggle.html` | classes from the table |
| `tags/context_action_filter.html` | `{% cv_button_class "context" "secondary" %}` |
| `formsets/control.html` | `formset:control` (4 buttons), `formset:container` (3 `btn-group` wrappers), `data-cv-class` / `data-cv-class-danger` on the delete button |
| `snippets/card_order.html` | `card-order:toggle` (2 buttons, keep `active`), `card-order:container` (the `btn-group btn-group-sm` wrapper) |
| `snippets/language_selector.html` | `language:toggle` plus structural `dropdown-toggle` |
| `tags/button_submit.html`, `tags/button_cancel.html`, `tags/button_delete.html` | removed |
| `crud_views_object_detail/.../layouts/card-rows/property.html` | `object-detail:property-detail` |
| new `tags/button/action.html`, `tags/button/menu_item.html`, `tags/button/container.html` | leaves |

The builder greps `btn-` across `src/` (all five apps) to catch anything this list misses; the guard test enforces
it afterwards.

## Documentation

- New reference page `docs/reference/buttons.md`: variants and view defaults, `ContextButton.variant`,
  `CardAction.variant`, the default table, `CRUD_VIEWS_BUTTON_CLASSES`, `register_button_classes`, the leaf
  contract (one sentence per key), the three leaves, a theme recipe (registration plus leaf override).
- `docs/reference/theme.md`: replace the "restyle the submit button" example (and the `tags/button_submit.html`
  mention in its override list) with the table plus leaf recipe; a section on which templates are logic templates
  and should not be copied.
- `docs/reference/card-list-view.md` (`variant` default `None`, fallback), `docs/reference/action_menus.md`
  (containers, menu classes), `docs/reference/settings.md` (remove the filter reset setting, add
  `CRUD_VIEWS_BUTTON_CLASSES`), `docs/reference/delete_view.md` (`CrispyDeleteForm.get_delete_button()`; there is
  no separate crispy page), `docs/reference/templates.md` (removed and added template names). The checks are
  documented on the buttons page, as `icons.md` and `action_menus.md` document theirs; there is no central
  system-checks page.
- `docs/reference/formsets.md`: the row controls and the delete toggle take their classes from `formset:control`,
  `formset:control-danger` and `formset:container`.
- CHANGELOG: breaking (removed setting with snippet, removed tags, `CardAction.variant` default, the five DOM
  changes, translatable Delete label), added (variants, table, leaves, hooks, checks).
- The django-crud-views skill in the `skills` repo (`references/actions-and-buttons.md`, `settings.md`,
  `system-checks.md`) in a follow-up release, as for 0.30.0.

## Constraints

- Python 3.12+, Django 4.2 / 5.2 / 6.0, the nox matrix must pass.
- Ruff, 120 chars, double quotes.
- Rendered HTML stays safe: class strings from the table are rendered as attribute values and escaped; the leaves
  mark nothing safe.
- Rendering cost: `cv_button_data` is dict work per button; the table is resolved once and cached.
- No new dependency.

## Left to the builder

- Exact check ids within the stated ranges if `E209` or `E360`-`W362` are taken.
- The `cv_button` tag's argument form for the menu item kind.
- Attribute order inside the leaves (then fixed by the regenerated goldens).
- Module placement of the crispy `Submit` / `Button` / `Reset` subclasses.
- Whether `cv_render_button` is a new tag or `cv_render_context_action` / `cv_render_list_action` /
  `cv_render_card_action` generalised with a location argument.

## Builder check (2026-10-20)

A fresh reviewer read this document against the baseline and asked four questions.

1. **Card markup under one leaf.** As first written, the card leaf would have drawn an icon next to visible labels,
   used the full action label as the card title, put `aria-label` on the card `div` and moved the card menu forms.
   Decision 1 (stock output unchanged) settles the first two: the stock action leaf draws the icon only when the
   label is hidden, and a card button's title and hidden text are its card label (`cv_title`, `cv_label`). The other
   two are accepted DOM changes, now in the Acceptance table: `aria-label` on `fieldset` only, `cv-card-container`
   on the card row, card menu forms before the row.
2. **Leaf context.** Leaves receive only the contract keys. `cv_short_label` was added for the menu item text and
   `tags/actions_menu_item_label.html` is rewritten to the contract with the same output. Raw dicts keep going to
   custom templates only.
3. **`formset.js` hard-codes `btn-light` / `btn-danger`.** `set_delete()` swaps the two classes on
   `.cv-form-ctrl-delete` when a row is marked for deletion, so a theme that sets `formset:control` gets Bootstrap
   classes back at runtime, and the template guard test cannot see it. Decided with the maintainer the same day:
   in scope (decision 6). A `formset:control-danger` entry (default `btn btn-danger`); `formsets/control.html`
   renders both strings on the delete button as `data-cv-class` and `data-cv-class-danger`; `set_delete()` swaps
   between them (the attribute values, not literals); the existing vitest case in `tests/js/formset.test.js` asserts
   it (section 2, "Python consumers", and Testing).
4. **`active` on menu items outside the toolbar.** `cv_active` is `cv_is_active` in every location, as the menu
   item behaves today. A list or card button whose target is the current view (no stock page has one) now also
   renders `active`; a changelog line, no special case.

## Calls I made (not discussed with the maintainer)

- The key spelling `location:slot`, the slot names (`container`, `menu-toggle`, `menu-wrapper`, `item`), and the
  `form:*`, `formset:control`, `card-order:toggle`, `language:toggle`, `object-detail:property-detail` entries.
- The contract key names and the `cv_container_tag` input.
- Card POST actions becoming `<button>`, and `aria-current="page"` on the active context action.
- `ActionGroup` always returned instead of `None`.
- The Delete label becoming translatable.
- Sorting attributes and class tokens in the golden normaliser.
- `formset:container` and `card-order:container` entries, so the `btn-group` wrappers in `formsets/control.html`
  and `snippets/card_order.html` pass the guard test (refresh, 2026-10-20).
- `cv_variant` defaulting to `secondary` in the normaliser (refresh, 2026-10-20).
- Dropping crispy's duplicate `btn` and dead `btn-inverse` tokens from the cancel and filter reset buttons
  (refresh, 2026-10-20).
- Leaves get only the contract keys; `cv_short_label`; the menu label include rewritten to the contract
  (builder check 2).
- `aria-label` on `fieldset` containers only; `cv-card-container` on the card row; card menu forms before the row
  (builder check 1).
- `cv_active` = `cv_is_active` in every location (builder check 4).
