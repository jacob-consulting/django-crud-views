# Concept review: icons, buttons and theming since 0.30.0

Prompt: `superpowers/prompts/2026-10-24-review-buttons-icons-theme-concepts.md`. Analysis only; no code changed.

## Scope

Two commit ranges, read as one body of work:

| Range | Commits | What |
|---|---|---|
| `3310379..cc095e1` | 295adc9 (#198, 99 files), 5876cba (#199), 86c39de, cc095e1 | the 0.30.0 icon registry |
| `cc095e1..19e273a` | 38 commits, 30 of them features, fixes or docs; 8 dependency bumps skipped | everything unreleased |

Read with them: `CHANGELOG.md` (`## Unreleased`, `## 0.30.0`), `docs/migrating-1.0.md`, `docs/reference/{buttons,icons,
theme,javascript,action_menus,card-list-view,context_buttons,messages,templates,settings}.md`,
`docs/development/stability.md`, the acceptance reports under `superpowers/notes/2026-10-2*`, issues #257, #259, #262,
#254, #211, and the code: `src/crud_views/lib/icons.py`, `lib/button_classes.py`, `lib/view/button_data.py`,
`lib/view/base.py`, `lib/view/buttons.py`, `lib/crispy/{buttons,form}.py`, `lib/messages.py`, `lib/breadcrumb.py`,
`templatetags/crud_views.py`, every template under `templates/crud_views/`, the seven scripts under
`static/crud_views/js/`.

The theme author's perspective is not hypothetical. Two sibling repositories were attached and read:

- `alexander-jacob/tabler-test` @ 7474883 (2026-10-22): the real `crud_views_tabler` prototype (`crud_views_tabler/`),
  its tests (`tests.py`, 75 tests), its design notes (`docs/crud_views_tabler.md`, `docs/crud_views_upstream_*.md`,
  `docs/crud_views_tooltips.md`). It is built against upstream 32a3533, nine feature commits behind HEAD.
- `jacob-consulting/crispy-tabler` @ 2f86558: the crispy template pack the theme renders forms through.

"Tabler" below means that prototype, not an imagined theme.

## Feature map

Grouped by what a reader has to understand, not by PR. Surface = settings, `cv_*` attributes, template names, context
keys, class-table keys, icon names, JS hooks, checks.

| # | Feature | Commits | Public surface | Docs |
|---|---|---|---|---|
| F1 | Semantic icon registry | 295adc9, 5876cba (0.30.0) | `CRUD_VIEWS_ICONS`, `CRUD_VIEWS_ICON_LIBRARIES`, `register_icon_library()`, `register_icons()`, `render_icon()`, `BOOTSTRAP_ICONS`, `{% cv_icon %}`, 34 icon names, checks E350 E351 E354 E355 E356 W352 W353, viewset.W246 | `icons.md` |
| F2 | Host placement (icon class on the button) | caf1761 (#258) | library keys `placement`, `standalone`; class keys `*:icon-host` (4); leaf keys `cv_icon_class`, `cv_icon_inline`; `{% cv_icon_class %}`; `cv_button_data(kind=)`; E363; filter toggle `data-cv-filter-icon-open/close` | `icons.md#host-placement`, `javascript.md#the-filter-toggle-contract` |
| F3 | JS adapters, jQuery-free core, tooltips | 440ac55 (#200), 4b62ed6 (#204), 5e36477 (#205), 5cc9240 (#208) | `cv.adapters.{modal,tooltip,collapse}`, `cv.bootstrapAdapters(ns)`, `adapters.js` first, `data-cv-tooltip="<location>"`, `cv.initTooltips()`, events `cv:modal:loaded/unload`, modal shell ids, `data-cv-modal-dismiss`, size tokens, `viewset.E250` | `javascript.md`, `modals.md` |
| F4 | Variants, class table, logic/markup leaves | e4bce00 (#201), 04bcd48 (#227) | `Variant`, `cv_action_variant`, `ContextButton.variant`, `CardAction.variant`; `CRUD_VIEWS_BUTTON_CLASSES`, `register_button_classes()`, `get_button_class()`, `{% cv_button_class %}`; 70 default keys; leaves `tags/button/{action,menu_item,menu_item_label,container}.html`; `cv_button_data()` and `LEAF_KEYS`; `{% cv_button %}`, `{% cv_render_button %}`; `Submit`/`Button`/`Reset`; `CrispyDeleteForm.get_delete_button()`; E209 E360 E361 W362 | `buttons.md`, `theme.md` |
| F5 | Label mode | 3fc4be6, 5ff9b70 (#213), 0ed6466 (#209), ca0dbe8 (#216), 43ee0c2 (#264), 556dbd4 (#269) | `CardAction.label_mode`, `cv_card_actions_label_mode`; `CRUD_VIEWS_{CONTEXT,LIST}_ACTIONS_LABEL_MODE`, ViewSet `*_actions_label_mode`, `cv_{context,list}_actions_label_mode` (dicts), `ContextButton.label_mode`, `cv_context_action_label_mode` (str); class keys `location:variant:mode`; `cv_get_context(location=)`; `CRUD_VIEWS_STRICT`; E106 E210 E211 W291 W292 | `action_menus.md#label-mode`, `card-list-view.md#label-mode`, `context_buttons.md` (Mermaid) |
| F6 | Button containers | d83c9ac (#261), 604620a (#265, #266) | class keys `*:container-{list,item,single,tag,label}` (15); `{% cv_container_layout %}`; `ContainerLayout`; E364; empty container renders nothing | `buttons.md#button-row-as-a-list` |
| F7 | Alerts and messages | 226f943 (#222), 4f78237 (#226), 32a3533 (#250) | `{% cv_messages %}`, `{% cv_alert %}`, `alert_data()`, `LEVELS`, `tags/alert.html`, `snippets/alert/{text,list}.html`, class keys `alert:*` (5), icons `message-*` (5) | `messages.md`, `theme.md#alerts` |
| F8 | Form frame and form fixes | 8fcb7f2 (#239), 2a9f5e2 (#236), c79ec22 (#191) | `snippets/form_frame.html`, blocks `cv_form_frame`, `cv_form_body`; `snippets/delete/protection_errors.html` | `theme.md#framing-the-form-pages` |
| F9 | Cards | 73b5037 (#243), 3d2ee82 (#241), 337b1f6 (#246) | blocks `card_title`, `card_content`, `card_actions`; class keys `card:{root,body,title}`; icons `page-previous`, `page-next`; accessible pagination | `card-list-view.md` |
| F10 | `hidden` instead of `d-none` | 9dde364 (#232) | filter toggle spans and POST forms carry `hidden` | `javascript.md` |
| F11 | Heading level | e383f51 (#251) | `CRUD_VIEWS_HEADER_LEVEL`, `{% cv_heading %}`, E107 | `templates.md#heading-levels` |
| F12 | Breadcrumb label | 13153c4 (#271) | `cv_breadcrumb_label_template[_code]`, `BreadcrumbItem.title` keeps `SafeData` | `breadcrumb.md` |
| F13 | Removals | 0b1c9a7 (#217), e4bce00, 226f943 | `crud_views/detail/`, `cv_is_*` filters, `cv_*_button` tags, `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`, django-bootstrap5 dependency | `migrating-1.0.md` |

Docs-only commits (4bdb0fa migration guide, 19e273a Mermaid, d1d5482 messages placement) and the test fix 5bb84c9 are
covered under the feature they describe.

---

## F1: Semantic icon registry (0.30.0)

**Consistent.** One value grammar everywhere (`name` → `prefix:name` → raw class, `icons.py:187-203`), one render
point (`render_icon`, `icons.py:223`), one precedence rule shared with the class table (defaults → theme → settings,
`icons.py:127-145`, `button_classes.py:125-133`). The view attributes (`cv_icon_action`, `cv_icon_header`,
`ViewSet.icon_header`) all take the same values. Checks follow one policy: a wrong *type* is an error (E356), an
unresolvable *value* is a warning (W352/W353). Fine.

**Easy to understand.** Three concepts (name, library, renderer) and the one-lookup rule. `icons.md` explains the
mechanism and the reasons. One trap is documented but unavoidable by design: a colon makes a value a library
reference, so a raw Tailwind class cannot be a raw value (`icons.md`, "Colons and raw classes").

**Missing.**

- Nothing in `docs/development/stability.md` lists `crud_views.lib.icons`: `register_icon_library`, `register_icons`,
  `render_icon`, `BOOTSTRAP_ICONS` and the 34 names are used by the Tabler theme (`crud_views_tabler/apps.py:24-25`,
  `icons.py:162-197`) and are not promised. Same for `crud_views.lib.messages.alert_data`, `cv_button_data` /
  `LEAF_KEYS`, the leaf template contract and `cv.adapters`. Only `crud_views.lib.button_classes` made it
  (`stability.md:29`). Issue #89 covers the symptom; this is its concrete list for the theme surface.
- An unmigrated bare group icon (`icon="truck"`) renders an invisible `<i class="truck">` and nothing flags it
  (`CHANGELOG.md` 0.30.0 Breaking, `migrating-1.0.md` Silent breaks). Opinion: a cheap heuristic check (a raw class
  with no space and no `-`, or one equal to a 0.29 Font Awesome icon name) would catch most of these.
- The renderer contract is documented as "must escape" (`icons.md#custom-renderer`), but nothing tests a third-party
  renderer's output. See Security.

**Durable.** The grammar survives a third library (Tabler proved it with an SVG renderer, no upstream change), a
non-Bootstrap framework and a sprite renderer. The one decision that is expensive to reverse after 1.0 is the set of
34 names: Tabler's `test_every_upstream_icon_name_is_mapped` (`tests.py:57-62`) and upstream's `BOOTSTRAP_ICONS`
sync test turn every new name into a theme break, which is the right loudness, but it means names are public API and
should be listed as such before 1.0.

**Security.** `font_renderer` builds the element with `format_html` (`icons.py:220`); the `css` argument and the
formatted class string are escaped. A raw-class value goes through the same path (`icons.py:231`). Values come from
settings, class attributes and templates, never from request or database content. A custom renderer is the only place
unescaped markup can enter, and that is a theme author's code; the Tabler renderer uses `format_html` and a constant
path table (`crud_views_tabler/icons.py:200-212`) and tests `css` escaping (`tests.py:51`). A broken renderer
fails soft: `_resolve_renderer` returns None on import failure (`icons.py:149-157`) and `render_icon` returns `""`,
while E351 reports it at check time. Fine.

**Improve.**

1. List the icon registry (names, the two register functions, `render_icon`, `BOOTSTRAP_ICONS`) in `stability.md`.
   Before 1.0.0.
2. A W35x warning for a bare value that looks like an icon name rather than a CSS class. Can wait.

**Tabler.** Register. Zero template copies for icons: one `register_icon_library` call and a 34-entry map. The theme
ships its own check `crud_views_tabler.W001` for a `tabler:` name without an SVG path (`checks.py:8-26`), which
reaches into private names (`_get_renderers`, `_icon_str`): the public API has no "is this prefix mine" and "strip an
icon value" helper. Minor, but it is the one place the theme imports underscores.

---

## F2: Host placement (#258)

**Consistent.** Decided per icon value, not per page; reuses the class table (`*:icon-host`) and the leaf contract
(`cv_icon_class`, `cv_icon_inline`); the menu toggle and menu items use the `menu` location (`templatetags:157`,
`button_data.py:122`). The filter toggle has its own two-form contract (`context_action_filter.html`,
`list.filter.js:22-28`), which is the price of the only button whose icon changes client-side. Fine.

**Easy to understand.** This is the hardest feature on the page for a newcomer: `placement`, `standalone`,
`{name_class}` as a format placeholder, four `icon-host` keys, `cv_icon_inline is not False`, and "the filter toggle
uses host placement only when both icons are host icons". `icons.md#host-placement` is clear but long. A reader who
does not need host placement never meets it, which is the right default.

**Missing.** Headings and modal titles are not hosts (#259, documented). Host placement requires the `font`
renderer (`icons.py:340-346`), so an SVG library can never be host-placed; that is correct (there is no class to
place) and documented.

**Durable.** Opinion: this is the feature with the narrowest audience (icon fonts painted by `::before` on the
button). It cost 30 files and added two leaf keys, two library keys, four class
keys, one tag, one check and a second filter-toggle contract. It is well isolated (a library without `placement`
renders as before, goldens unchanged per the acceptance note), so it does not endanger 1.0; but every leaf override
now has three icon branches to copy (`migrating-1.0.md`, "Host-placed icons"). Keep, do not extend further before
1.0.

**Security.** `get_icon_host_class` formats a settings string with `name_class` (`button_classes.py:150-163`); the
result lands in `class="..."` through autoescape (`action.html`) or through `data-cv-filter-icon-open` and
`classList.add` (`list.filter.js:22-27`). No user content. Fine.

**Improve.** None before 1.0. #259 can wait.

**Tabler.** Not used (SVG renderer). Zero copies.

---

## F3: JS adapters, jQuery-free core, tooltips (#200, #204, #205, #208)

**Consistent.** One lookup pattern (`cv.adapters.<name>`, resolved at call time), one factory
(`cv.bootstrapAdapters(ns)`), ids and `data-cv-*` attributes as the DOM contract, one marker (`data-cv-tooltip`)
carrying the location. Everything in `adapters.js` is defensive (`component(ns, name)` returns null, `?.` chains).
Fine.

**Easy to understand.** `javascript.md` is the best page in the set: a needs table, an adapter table, three recipes
(Tabler, bundler, `<dialog>`). The one thing it does not say is that `hide`/`dispose` exist because Bootstrap keeps a
focused button's tooltip open and accumulates modal handlers (#203); the acceptance report has it, the reference does
not.

**Missing.** `formset.js` is the last jQuery user (#210, open). `tooltip.js` initialises every marker it finds, but a
marker on a *disabled* button never shows a tooltip under Bootstrap (`pointer-events: none`), documented in
`inaccessible_actions.md`. Fine.

**Durable.** Yes. The adapter shape (three objects, named methods) is small and Tabler used it unchanged
(`tabler-adapters.js`, one `Object.assign` plus a replaced `init`). The size tokens (`""`, `sm`, `lg`, `xl`) are
Bootstrap's set under neutral names; a `<dialog>` adapter ignores them, which is acceptable.

**Security.** No inline scripts, no inline handlers, config through `data-*` on `#cv-config` (`viewset.js:1-12`),
CSRF header on the filter POST (`list.filter.js:34-38`). `data-cv-cancel-url` is navigated to verbatim
(`viewset.js:43`); the value comes from `reverse()` plus the validated origin key (`base.py:683-688` checks the
`cv_from` value against a name regex and `cv_cancel_keys`), so no user-controlled URL reaches it. Fine.

**Improve.** Add one sentence to `javascript.md#tooltips` on *why* `hide` and `dispose` exist. Can wait.

**Tabler.** Register (one asset). Zero copies; the theme's tests pin that `tabler-adapters.js` replaces only `init`
(`tests.py:223-234`).

---

## F4: Variants, class table, logic/markup leaves (#201, #227)

**Consistent, mostly.** One key grammar `location:slot[:mode]`, one resolution (`get_button_class`,
`button_classes.py:136-147`), one leaf contract (`LEAF_KEYS`, `button_data.py:16-36`), one data builder
(`cv_button_data`). Two inconsistencies:

- **Two meanings of the second segment.** For action buttons the slot is a *variant* (`context:primary`); for form
  buttons it is a *kind* (`form:submit`, `form:cancel`, `form:delete`, `form:filter-submit`, `form:filter-reset`,
  `button_classes.py:56-60`); for everything else it is a *part* (`container`, `menu-toggle`, `active`,
  `hidden-label`). The W362 shape check only accepts a mode segment when the slot is a variant
  (`_action_key_parts`, `button_classes.py:207-218`), and the test suite pins `form:submit:icon` as invalid
  (`tests/test1/test_button_classes_checks.py:79`). This is exactly what #257 wants to add. See the #257 section.
- **The docs say 64 keys, the table has 70.** `buttons.md:112` ("The default table has 64 keys") versus
  `DEFAULT_BUTTON_CLASSES` (70 entries) and `test_button_classes.py:84` (`assert len(EXPECTED_KEYS) == 70`). The count
  was bumped in the acceptance notes (43 → 46 → 51 → …) but the prose was not. Cosmetic, but it is the number a
  theme author checks against.

**Easy to understand.** The variant idea and the recipe ("register classes, override a leaf only when markup
differs") are clear and Tabler confirms the recipe works: the theme overrides **no** button template
(`docs/crud_views_tabler.md`, "Header and actions"). What is hard: the leaf contract has 19 keys, the table has 70,
and `buttons.md` is 448 lines. Most readers need the first 120.

**Missing.**

- The crispy buttons are outside the leaf model: `Submit`/`Button`/`Reset` set `field_classes` from the table
  (`crispy/buttons.py:16-18`) and crispy renders them as `<input>` through its own `baseinput.html`. No `cv-key`, no
  `data-cv-tooltip`, no location, no leaf. A theme cannot change their markup at all. #257 is the gap.
- The language selector (`snippets/language_selector.html`) and the object-detail property button have class keys
  but hard-code `dropdown-toggle`, `dropdown-item` and `active`; documented in `theme.md#templates-that-follow-bootstraps-dom`.

**Durable.** The class table is the best idea in the set: it took the Tabler theme from 19 overrides to zero button
overrides with 41 registered keys (`crud_views_tabler/buttons.py:3-44`). Bootstrap leaks through the *defaults*
(`btn`, `visually-hidden`, `active`, `dropdown`) but every one of them is a key a theme can set (#227). What leaks
through *markup* and is not a key: `dropdown-toggle`, `data-bs-toggle="dropdown"`, `dropdown-menu`, `btn-close`,
`data-bs-dismiss="alert"` (`actions_menu.html`, `actions_menu_toggle.html`, `alert.html`, `language_selector.html`).
`theme.md` names the dropdown ones. The alert close button is not named anywhere: `data-bs-dismiss` on
`tags/alert.html` bypasses `cv.adapters` and works only under Bootstrap's data API (Tabler's alert copy keeps it,
`crud_views_tabler/templates/crud_views/tags/alert.html:17`). Same pattern the modal had before `data-cv-modal-dismiss`.

**Security.** `cv_title` is the full label (`button_data.py:134`), which is a `SafeString` from `render_snippet`
(`base.py:359`, `mark_safe(result.strip())`); the snippet itself renders with autoescape on, so `{{ object }}` inside
is escaped and the string cannot break out of `title="{{ cv_title }}"`. A `label_template_code` containing a literal
`"` would, but that is developer code. `data-cv-disabled="{{ cv_disabled_reason }}"` carries a constant. The hidden
POST form (`list_action_form.html`) keeps `{% csrf_token %}`. Fine.

**Improve.**

1. Fix the key count in `buttons.md:112` (and consider generating that table from `DEFAULT_BUTTON_CLASSES` in the
   docs build, so it cannot drift again). Before 1.0.0.
2. Decide the second-segment semantics for `form:*` before #257 (see below). Before 1.0.0.
3. `data-cv-alert-dismiss` through an adapter, or at least name the alert close button in
   `theme.md#templates-that-follow-bootstraps-dom`. Can wait, but it is the same class of leak the modal fixed.

**Tabler.** Register (41 keys). Zero button copies. The theme's own test `test_every_theme_key_is_an_upstream_key`
(`tests.py:79-85`) is the W362 rule re-implemented client side, which is fine.

---

## F5: Label mode (#213, #209, #216, #264, #269)

**Consistent? No.** This is the feature that grew by accretion and it shows:

| Location | Default | Knobs (most specific first) |
|---|---|---|
| card | `both` | `CardAction.label_mode`, `no_label=True` → `icon`, `cv_card_actions_label_mode` (str) |
| context | `icon` | page's `cv_context_actions_label_mode` (dict), `ContextButton.label_mode`, ViewSet `context_actions_label_mode` (dict) → `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` (dict), target view's `cv_context_action_label_mode` (str) |
| list | `icon` | `cv_list_actions_label_mode` (dict) → ViewSet → setting; never the button, never the target |
| filter toggle | `icon`, hard-coded | none (#262) |
| form | `label`, no concept | none (#257) |

Five locations, three defaults, three knob shapes (per-button field, per-key dict, per-view string), and two
resolution rules: dicts are **replaced whole** across levels (`cv_first_inline_keys`, `action_menus.md`: "the layers
are not merged"), while the class table is **merged per key**. `cv_context_actions_label_mode` and
`cv_context_action_label_mode` differ by one letter and one type (`base.py:89-96`); the docs own this with a
two-column table (`action_menus.md`, "The two attributes differ by one letter") and the Mermaid diagram (#273) exists
because the order needed a picture. The code is correct (`base.py:291-318`, tests in
`test_context_button_label_mode.py`, `test_context_action_label_mode.py`), the acceptance notes are thorough; the
*concept* is what is hard.

**Easy to understand.** A Django developer can set one card to icon-only in a minute. Explaining why a toolbar
`create` button shows a label needs the five-step order. The W292 check and the strict-mode rule ("icon mode without
an icon raises under `CRUD_VIEWS_STRICT`", `button_data.py:88-101`) are good: they turn the most common mistake into a
message.

**Missing.**

- No single place sets the *default* mode per location. The three defaults are literals: `button_data.py:83`
  (`"both" if card else "icon"`), `context_action_filter.html` (`"icon"`), and the proposed `label` in #257.
- Row actions cannot follow the target view (`base.py:313-318`, documented). Defensible (a table row is a different
  density) but it means the same `UpdateView` is described twice.
- `CardAction.no_label` is still accepted alongside the new field (`card.py:11-30`); #254 asks for a warning on the
  old override key. Both are 0.29 compatibility; both should go at 1.0.

**Durable.** The *leaf* side is durable: `cv_label_mode` with three values is a clean contract, and Tabler's class
table keys off it (`context:secondary:icon` → `btn-icon`). The *configuration* side is not yet: with #257 the knob
count goes from 8 to 11 and the defaults from 3 to 4. After 1.0 every one of those names is frozen.

**Security.** Mode values are developer config, validated by E210/E211/E106; an invalid `ContextButton.label_mode`
with strict mode off breaks the page at render (`ValueError`, `button_data.py:84-85`) rather than failing soft. The
acceptance note for #264 lists this as a deferred minor. Not a security issue, a robustness one.

**Improve.**

1. **One default-per-location setting** (`CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"context": "icon", "list": "icon",
   "card": "both", "form": "label"}` or similar) replacing the literals, read by `cv_button_data`, the filter toggle
   and #257. This also gives W292 one source of truth. Before 1.0.0, because #257 otherwise adds a fourth literal.
2. Remove `no_label` and the `cv_no_label` `ValueError` path at 1.0.0 (they are already documented as superseded).
3. Rename or merge the one-letter pair. Opinion: `cv_context_action_label_mode` (target default) could become
   `cv_action_label_mode` next to `cv_action_variant` and `cv_action_label_template`, which it semantically belongs
   with ("how buttons pointing at me look"). Before 1.0.0 or never.

**Tabler.** Register (the `:icon` keys). The theme's doc records the one visible loss: the primary toolbar action is
icon-only because the stock default is `icon` and the theme cannot set a label mode (`docs/crud_views_tabler.md`,
"Accepted differences"). That is correct by design (a theme styles, a project decides what has text) and #269 now
gives the project a one-line way to get the label back (`cv_context_action_label_mode = "both"` on `CreateView`).

---

## F6: Button containers (#261, #265, #266)

**Consistent.** Five keys per location with one reader (`get_container_layout`, `button_classes.py:184-204`), one
tag (`{% cv_container_layout %}`), one leaf. The tag/label split (`container-tag`, `container-label`) is the right
cut: a `div` with an `aria-label` is a no-op and the docs say so. `get_container_layout` reads **raw** values
(`""` vs `None` matter for `container-list`) while `get_button_class` collapses both to `""`; documented in the
docstring and `buttons.md`, but it is a second value semantics inside one table.

**Easy to understand.** The "single item bare" rule and "an item is a button or the menu toggle" are explained with
an example. Fine.

**Missing.** Nothing a theme has asked for. The `container-label` default `gettext_noop("Actions")` is translated at
render (`button_classes.py:204`); a theme's own label must be a plain str marked with `gettext_noop`, and a
`gettext_lazy` value fails E361. Documented.

**Durable.** Yes, but these 15 keys exist for one design system (list-based button rows). Like F2, isolated and
default-neutral.

**Security.** `aria-label="{{ cv_layout.label }}"` autoescaped; `tag` is a settings string rendered as
`<{{ cv_layout.tag }}` (`container.html`) and is **not** validated: `"list:container-tag": "div onclick=x"` would
render as an attribute. Developer config, not a user vector, but E364 validates `container-single` while nothing
validates `container-tag`. A one-line check (a `[a-z][a-z0-9-]*` regex) closes it. Can wait.

**Improve.** The E36x check for `container-tag`. Can wait.

**Tabler.** Not used (Tabler's `btn-list` is a flat flex container). Zero copies.

---

## F7: Alerts and messages (#222, #226, #250)

**Consistent.** One frame, one data function, levels as class slots, icons as `message-<level>` names. The frame is
the same shape as the button leaf: Python decides, template draws. Fine.

**Easy to understand.** `messages.md` is short and complete.

**Missing.** `tags/alert.html` hard-codes `alert-dismissible fade show` and `btn-close` with `data-bs-dismiss`
(F4 above). A theme on a non-Bootstrap framework copies the frame for that alone.

**Durable.** Yes.

**Security.** The strongest part of the set. `alert_data` escapes `heading`, `text` and every item with
`conditional_escape` and `extra_tags` unconditionally (`messages.py:42-55`), so the frame is safe even under
`{% autoescape off %}`; `message_alerts` keeps `SafeString` bodies (the `cv_message_template` snippets) and escapes
everything else (`messages.py:57-84`); tests cover hostile `__str__` items and autoescape-off
(`2026-10-22-alert-template-acceptance.md`). Fine.

**Improve.** Move the close button's dismiss behind a `data-cv-alert-dismiss` adapter call, or document the leak.
Can wait.

**Tabler.** Override one leaf (`tags/alert.html`) for structure (`.alert-icon`, `.alert-heading`,
`.alert-description`). The theme's copy already removed two overrides (`messages.html`, `protection_errors.html`).
This is the intended cost.

---

## F8: Form frame and form fixes (#239, #236, #191)

**Consistent and easy.** One frame, two blocks, the modal header check in the theme's hands. The two fixes are the
textbook case for #211: Tabler carried both bugs in its copied form templates until it caught up
(`docs/crud_views_upstream_status.md`, "Two bugs inherited by copying").

**Missing.** Nothing.

**Durable.** Yes.

**Security.** `enctype="multipart/form-data"` is unconditional; the form posts to `request.get_full_path` (keeps
`cv_from`), `{% csrf_token %}` present. Fine.

**Tabler.** Override one frame (`snippets/form_frame.html`, 6 lines). Intended cost.

---

## F9: Cards (#243, #241, #246)

**Consistent and easy.** Blocks plus three class keys; footer placement stays structural by decision
(`2026-10-22-card-blocks-acceptance.md`). Pagination uses the registry.

**Missing.** The stock card heading is `{% cv_heading level=5 %}` (follows F11); Tabler's card copy hard-codes
`<h3 class="…">` (`crud_views_tabler/templates/crud_views/tags/card.html:13`), so `CRUD_VIEWS_HEADER_LEVEL` does not
reach Tabler card titles. Theme drift, not an upstream defect, but `templates.md` could say "use `{% cv_heading %}`
in a card override".

**Durable.** Yes.

**Security.** Fine.

**Tabler.** Override `tags/card.html` (structure: footer) and `view_card.content.html` (grid, empty state; upstream
closed #244 as not planned). Two copies. The card copy still passes `cv_container_tag="div"` to the container include
(`card.html:19`), a key upstream removed in #266 (`CHANGELOG.md`, Breaking); harmless today because `card:container-tag`
defaults to `div`, but it is a stale parameter nothing detects. Exactly #211.

---

## F10: `hidden` instead of `d-none` (#232)

Fine. One attribute, two templates, one JS line. The rendering guard test (every class in the button chain is a table
value or `cv-`-prefixed, exemptions `dropdown-toggle` and `d-none`) is the kind of test that keeps F4 honest.

---

## F11: Heading level (#251)

**Consistent and easy.** One setting, one tag, one rule (content headings render one below the header).

**Durable.** Yes. The `h{level}` size class is Bootstrap-specific but harmless elsewhere.

**Security.** `CvHeadingNode.render` builds the tag with `mark_safe(f"<h{rendered}{attr}>…")`
(`templatetags:347`); `rendered` is an int from a validated setting (E107), `css` is `conditional_escape`d, the body
is the already-rendered nodelist. Fine.

**Tabler.** Register (setting). Zero copies, but see F9 for the card title.

---

## F12: Breadcrumb label (#271)

**Consistent.** Mirrors `cv_action_label_template[_code]`.

**Security, worth a sentence.** `BreadcrumbItem.coerce_title` now keeps `SafeData` (`breadcrumb.py:33-37`), so a
model whose `__str__` returns `mark_safe(...)` renders as HTML in the breadcrumb where it used to be escaped
(`CHANGELOG.md`, Fixed: "now renders as HTML where it used to show as literal text"). This is the correct Django
semantics and fixes real double-escaping, but it widens what a `__str__` can do on every page with a breadcrumb.
Nothing to change; worth one line in `breadcrumb.md` so a reviewer does not rediscover it.

---

## F13: Removals (#217, #201, #222)

Fine, and the right call before 1.0. All removed settings fail a check (E350, E360). The removed tags fail loud
(`TemplateSyntaxError`). The removed `cv_get_filter_icon()` hook fails silently (`migrating-1.0.md`, Silent breaks);
#254 and #211 are the open items for the silent class.

---

## The theme author's ledger

What `crud_views_tabler` does today against upstream 32a3533, and what it would do against HEAD:

| Mechanism | Count | Items |
|---|---|---|
| Register | 3 calls | 1 icon library, 34 icons, 41 button class keys (`apps.py:24-31`) |
| Assets | 2 files | `tabler-adapters.js` (13 lines), `crud_views_tabler.css` (31 lines) |
| Leaf override (intended) | 3 | `tags/alert.html`, `snippets/form_frame.html`, `modal/shell.html` |
| Template copy (structural, decided upstream) | 5 | `tags/card.html` (footer, #243), `view_card.content.html` (#244 closed), `tags/list_filter.html` + `list_filter.inner.html` (#242 closed), `table/bootstrap5.html` (django-tables2, never filed) |

Eight overridden templates, none of them a button template. Of the five copies, one has an open upstream hook
request (`modal/shell.html` → #240 `modal:root` / `modal:dialog` class keys); two were declined (#242, #244); one is
structural by decision (#243); one is a whole third-party template (`table/bootstrap5.html`), which is the single
largest copy (105 lines) and the one most likely to drift, since it embeds django-tables2's block structure and
upstream's own `table/bootstrap5.html` still renders `&laquo;` / `&raquo;` arrows while `snippets/pagination.html`
moved to the registry (#241). That asymmetry is an upstream inconsistency: the table pagination did not get #241.

What the theme **cannot** do today: style or restructure the form buttons (F4), swap the alert close button's
dismiss mechanism (F7), set a label mode (correct: a project decision).

Drift found in the theme against HEAD, all silent: `cv_container_tag="div"` (removed key, F9), `<h3>` instead of
`{% cv_heading %}` (F11), and the five new semantic names `message-*` and two `page-*` that **are** mapped, because the
theme's own set-equality test forced it. The loud/silent ratio here (1 loud, 2 silent) is the #211 argument in
miniature.

---

## Issue #257: label mode for form buttons

Read against the code as it stands.

**Does it reuse the resolution and the class table, or add a fourth variant?** As written, a fourth variant with a
fifth default. It proposes a new setting `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` (dict of button key → mode), ViewSet
`form_actions_label_mode`, view `cv_form_actions_label_mode`, "resolved like the context / list settings". That
*is* the dict-shape knob of F5, so the resolution reuse is real. What it does not reuse: `cv_button_data` and the
leaf. Form buttons are crispy layout objects rendered by crispy's templates (`baseinput.html` for `<input>`,
`button.html` for `<button>`), outside `LOCATIONS` (`button_data.py:12`) and outside `tags/button/action.html`. The
issue says "using the same label-mode markup as `tags/button/action.html`"; the only way that is literally true is a
crispy layout object whose `template` is a crud_views leaf.

**The `label` default.** Defensible as a non-breaking transition (today's forms are text-only), indefensible as a
fourth hard-coded literal next to `both` (card), `icon` (context/list) and `icon` (filter toggle). Do F5 improvement 1
first: one defaults map, and #257 adds a `"form"` entry to it instead of a rule.

**Icon names `save`, `cancel`, `reset`.** They follow the registry's naming (verb or noun, lowercase, hyphenated).
None exists today in `DEFAULT_ICONS`, `BOOTSTRAP_ICONS` (`icons.py:13-96`) or `TABLER_ICONS`
(`crud_views_tabler/icons.py:162-197`). Upstream's sync test forces the Bootstrap entries; Tabler's
`test_every_upstream_icon_name_is_mapped` will fail on upgrade until the theme maps them, which is the desired
loudness. `delete` and `filter` are reused correctly. Opinion: `reset` is ambiguous (the filter reset is a reset; the
cancel button is also `name="reset"` in `get_cancel_button_kwargs`, `form.py:76`); name it `filter-reset` to match
the class key.

**`<input>` → `<button>`: what depends on `<input>`.**

- Upstream tests: `test_crispy_buttons.py:21-27` matches `<input\b` only; every assertion in that file breaks.
- Tabler tests: `test_delete_form_is_the_stock_crispy_delete_form` asserts `<input type="submit"[^>]*class="btn
  btn-danger"` (`tests.py:315-319`).
- `viewset.js` cancel handler uses `closest("[data-cv-cancel-url]")` (`viewset.js:37-44`): works for `<button>`.
- `modal.js` forwards `event.submitter` into `FormData(form, submitter)` (`modal.js:75-83`): works for `<button
  type="submit" name value>`; POST data unchanged as the issue claims.
- crispy's `<button>` template renders `{{ button.content|safe }}` (vendored copy in
  `crispy-tabler/.../layout/button.html:2`; I did not import `crispy_forms` itself, no venv in this container). The
  `|safe` means whatever crud_views puts into `content` is **not** escaped by the template. The cancel label is
  `context["cv_action_label"]`, a `SafeString` from an autoescaped snippet, so it is safe; `submit_label` is a
  developer string. If #257 builds `content` with icon markup plus label, it must build it with `format_html` /
  `conditional_escape`, or render through a crud_views leaf that autoescapes. This is the one security point in #257.
- The W362 shape check rejects `form:submit:icon` today (`_action_key_parts`, `button_classes.py:207-218`;
  `test_button_classes_checks.py:79`). #257 needs `_is_action_mode_key` to accept `form:<kind>:<mode>`, which means
  deciding whether `form`'s second segment is a kind (today) or a variant.

**Through `tags/button/action.html` or its own leaf?** Its own leaf, with the same contract keys. `action.html` emits
`type="button"` for `<button>`, `cv-key`, `data-cv-action`, `data-cv-modal` and `href`; a submit needs
`type="submit" name value`, a cancel `type="button" data-cv-cancel-url`. Forcing both into one leaf means more
branches for every theme override. A `tags/button/form.html` leaf fed by `cv_button_data(ctx, "form")` (extend
`LOCATIONS`, add `cv_type`, `cv_name`, `cv_value`, `cv_cancel_url` to the contract) keeps one data builder and one
label-mode rendering rule, and the Tabler theme would override nothing for it. The crispy layout object becomes a
thin adapter whose `template` is that leaf.

**What should change in #257 before implementation.**

1. Depend on a defaults map (F5.1); do not add a fourth literal.
2. Name the location `form` in `LOCATIONS` and render through a crud_views leaf, not crispy's `button.html`.
3. Settle the `form:*` second segment. Option A: keep kinds (`form:submit:icon`) and extend the W362 shape to
   `form:<kind>:<mode>`. Option B: make form buttons carry variants like every other button (`form:primary`,
   `form:secondary`, `form:danger`) with the kind only on `cv-key`. B is consistent with F4; A is less churn. Pick
   one and write it down; today the table mixes both meanings silently.
4. Rename `reset` → `filter-reset`.
5. Escaping rule for the `<button>` content (above).
6. Tabler: `cancel` → `tabler:x`, `save` → `tabler:device-floppy` (neither path is in `ICONS` yet); the two tests
   named above change.

**#262 and #259: one feature or three?** Two. #262 (filter toggle honours the label mode) is F5 unfinished: the
toggle is the only toolbar button with a hard-coded `"icon"` (`context_action_filter.html`, `FilterContextButton`
has no `label_mode` path, `buttons.py:298-330`). It should ride on the same defaults map and the same `cv_button_data`
path as #257, so they are one change in concept: "every button renders through `cv_button_data` and reads its default
mode from one map". #259 (host placement for headings) is F2, independent of both.

---

## Synthesis

### Five findings that matter most

1. **Label-mode configuration has no single default per location** (F5). Three literals today, a fourth in #257, a
   fifth implicit in the filter toggle. Fix: one defaults map read by `cv_button_data`, the filter toggle and the
   form buttons, before #257 and #262 are built. Before 1.0.0.
2. **The class table's second segment means two things** (F4): variant for action buttons, kind for `form:*`. The
   W362 shape check encodes the split and #257 collides with it. Decide A or B (above) before 1.0.0, because the key
   names are frozen after.
3. **The theme surface is not in the stability policy** (F1, F4, F7): `crud_views.lib.icons`, the 34 icon names,
   `alert_data`, `cv_button_data` / `LEAF_KEYS`, the leaf contract and `cv.adapters` are what `crud_views_tabler`
   actually imports and depends on, and `stability.md` lists only `button_classes`. Before 1.0.0.
4. **Form buttons are the one button family outside the leaf model** (F4, #257). Rendering them through a
   `tags/button/form.html` leaf with `cv_button_data(ctx, "form")` closes the last place where a theme has no lever.
   Before 1.0.0 only if #257 ships before 1.0.0; the issue is the plan, with the five changes above.
5. **Two Bootstrap leaks are still unnamed**: the alert close button (`data-bs-dismiss`, F7) and the table template's
   `&laquo;` arrows that #241 fixed only for cards (ledger). Both small; the first is the same leak the modal already
   fixed with `data-cv-modal-dismiss`. Can wait, but name them in `theme.md`.

### Settle before 1.0.0, because changing them later breaks every theme

- The 34 icon names and the `prefix:name` grammar (F1).
- The 70 class-table keys and the `location:slot[:mode]` grammar, including the `form:*` decision (F4, #257).
- `LEAF_KEYS` and the four leaf template names (F4); a `form` leaf if #257 ships.
- The label-mode knob names: `cv_context_actions_label_mode` vs `cv_context_action_label_mode` (F5.3).
- The adapter shape and the DOM contracts (`#cv-modal*` ids, `data-cv-*`, `#cv-filter-toggle`, `#filter-collapse`)
  (F3).
- Removing `CardAction.no_label` and the `cv_no_label` guard (F5.2).
- The docs key count (F4.1): trivial, but a wrong number in a reference page is what a theme author quotes.

### Fine as they are

- F1 value grammar, precedence and fail-soft renderer handling.
- F2 host placement: isolated, default-neutral, done.
- F3 adapters, tooltips, lifecycle, CSP posture, origin validation.
- F6 container keys (one optional E36x for `container-tag`).
- F7 escaping in `alert_data` / `message_alerts`: the model for how the rest should behave.
- F8, F9, F10, F11, F13.
- F12 `SafeData` breadcrumb titles: correct Django semantics; one doc sentence.
- Strict mode (`CRUD_VIEWS_STRICT`, default `DEBUG`): raise in development, log and render the label in production.
  Right trade-off; the suite runs strict (`2026-10-23-context-button-label-mode-acceptance.md`).

## Not checked

- The test suites were **not run** in this container (no virtualenv; `crispy_forms` not importable). Test counts and
  "goldens unchanged" statements are quoted from the acceptance reports, not re-verified.
- crispy-forms' own `StrictButton` / `Button` source: the `|safe` claim rests on the template vendored into
  `crispy-tabler` from crispy-bootstrap5 2026.9, not on `crispy_forms` itself.
- `formset.js` (644 lines) beyond its jQuery dependency; `toggle.js`; `crud_views_object_detail` layouts beyond their
  icon and class-key usage; the workflow, polymorphic and guardian templates beyond `grep`.
- The `superpowers/specs/*` design documents behind the features; only the acceptance notes were read.
- Rendering in a browser: Tabler's tests were read, not executed.
- Translations (`.po` files) for the new `gettext_noop` labels.
