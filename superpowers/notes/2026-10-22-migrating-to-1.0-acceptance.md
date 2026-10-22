# Acceptance: Migrating to 1.0.0 guide (#253)

Spec: `superpowers/specs/2026-10-22-migrating-to-1.0-design.md`. Plan: `superpowers/plans/2026-10-22-migrating-to-1.0.md`.

## Inventory

Every user-visible change from `## 0.30.0` and `## Unreleased`, checked against `main` (net state at 1.0), with the
guide section that covers it. Sections: 2 step zero, 3 app on stock bootstrap5, 4 downstream theme, 5 silent breaks.
Loud = a system check or an exception; silent = renders wrong and raises nothing.

| # | Rel. | Change | Net state at 1.0 (verified in) | Reader | Loud / silent | Sec. |
|---|---|---|---|---|---|---|
| 1 | 0.30 | Icon registry; `CRUD_VIEWS_ACTIONS_MENU_ICON`, `CRUD_VIEWS_FILTER_ICON` removed | `CRUD_VIEWS_ICONS["actions-menu"]` / `["filter"]` (`lib/icons.py` removed-settings map) | app | E350 | 2, 3 |
| 2 | 0.30 | `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*`, `_NAMED_ICONS` removed; object detail on Font Awesome | `BOOTSTRAP_ICONS` recipe (`lib/icons.py`) | app | E350 | 2, 3 |
| 3 | 0.30 | Object-detail group icons no longer auto-prefixed | bare value = raw CSS class; `W246` only for an unregistered prefix (`crud_views_object_detail/lib/mixins.py`) | app | silent | 3, 5 |
| 4 | 0.30 | `tags/icon.html`, `cv_header_icon_class`, `cv_filter_icon_class`, `{% cv_filter_icon %}`, `cv_get_filter_icon()` removed; OD filters `icon_class`, `named_icon_class` removed | gone (template list, tag diff 0.29.4..HEAD) | theme, app | TemplateSyntaxError / TemplateDoesNotExist | 3, 4 |
| 5 | 0.30 | Boolean widget icons | overtaken: `detail/widgets/bool.html` deleted in #217; OD `types/default/boolean.html` uses `boolean-true` / `boolean-false` | theme | — | 4 |
| 6 | 0.30 | Table sort icons FA6, ascending points up | `table-sort-asc` / `-desc` (`lib/icons.py`, `table/bootstrap5.html`) | app, theme | silent (markup) | 3, 4 |
| 7 | 0.30 | `cv_icon_action`, `cv_icon_header`, `cv_menu_icon` carry icon values | stock values are names (`card`, `detail`…); a raw CSS class set on a view still renders | theme | silent | 4, 5 |
| 8 | 0.30 | `aria-hidden="true"` on icons | `render_icon` | app | markup | 3 |
| 9 | 0.30 | `fa-fw` → `cv-icon-fw`; `css/icons.css` new core asset | `static/crud_views/css/icons.css` | app, theme | silent for hand-listed CSS | 3, 4 |
| 10 | unrel. | Alerts through `tags/alert.html`; message dicts `level`/`text` | `tags/messages.html` is a loop over `tags/alert.html`; `ALERT_CLASSES`, `ICON_NAMES` gone | theme | silent | 4, 5 |
| 11 | unrel. | Pagination markup, `page-previous` / `page-next` icons | `snippets/pagination.html`, `lib/icons.py` | app, theme | silent (markup) | 3, 4, 5 |
| 12 | unrel. | Filter toggle `hidden` instead of `d-none` | `tags/context_action_filter.html`, `list.filter.js` | theme | silent | 4, 5 |
| 13 | unrel. | `cv_get_context()` keyword-only `location` | `lib/view/base.py:579` | app | TypeError | 2, 3 |
| 14 | unrel. | `django-bootstrap5` dropped | `pyproject.toml`; `{% cv_messages %}` | app | TemplateSyntaxError (`{% load django_bootstrap5 %}`) | 3 |
| 15 | unrel. | Card buttons render icon + label | `cv_card_actions_label_mode = "both"` (`lib/views/card.py:28`) | app | markup | 3 |
| 16 | unrel. | `cv_label_visible` → `cv_label_mode` in the leaf contract | `lib/view/button_data.py` | theme | silent for a 0.30-era `tags/button/action.html` copy | 4 |
| 17 | unrel. | `cv_no_label` not a `cv_button_data()` input | ValueError (`lib/view/button_data.py:38`) | app | ValueError | 2, 3 |
| 18 | unrel. | `viewset.E210` for `label_mode` | `lib/view/label_mode.py` | app | E210 | 2 |
| 19 | unrel. | `cv_modal_size` tokens | `viewset.E250` (`lib/view/base.py:140`) | app | E250 | 2, 3 |
| 20 | unrel. | Modal close `data-cv-modal-dismiss`; `modal/shell.html` | `modal/content.html`, `modal.js` | theme | keeps working under Bootstrap adapter | 4 |
| 21 | unrel. | `cvModalOpen(url, "modal-lg")`, `data-cv-modal-size="modal-lg"` | default size | app, theme | silent | 3, 5 |
| 22 | unrel. | `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` removed | E360 (`lib/button_classes.py:71`) | app | E360 | 2, 3 |
| 23 | unrel. | `cv_submit_button`, `cv_cancel_button`, `cv_delete_button` removed | tags and `tags/button_{submit,cancel,delete}.html` gone; crispy `Submit` / `Button` / `Reset` | app, theme | TemplateSyntaxError for the tags; a theme's copies of the three templates are silently unused | 3, 4, 5 |
| 24 | unrel. | `CardAction.variant` defaults to target view's variant | `lib/view/card.py:13` | app | markup | 3 |
| 25 | unrel. | `cv_menu_wrapper_class`, `cv_toggle_class` gone | not in any context | theme | silent (empty class) | 4, 5 |
| 26 | unrel. | Logic templates `tags/context_action.html`, `list_action.html`, `card_action.html`, `actions_menu_item.html`; `tags/context_actions.html` and `columns/actions.html` include `tags/button/container.html` | one line each, `{% cv_button %}` | theme | old overrides still render (see row 40) | 4 |
| 27 | unrel. | `tags/actions_menu_item_label.html` no longer used by stock menu | `tags/button/menu_item_label.html` | theme | silent | 4, 5 |
| 28 | unrel. | DOM: attribute order, `cv-key`, card POST `<button>`, `aria-current`, `cv-card-container`, crispy cancel / reset classes | leaves under `tags/button/` | app, theme | markup | 3 |
| 29 | unrel. | Delete label translatable | — | app | markup | 3 |
| 30 | unrel. | Tooltips `data-cv-tooltip`; formset control titles; OD property-detail `title` | `formsets/control.html`, OD templates, `tooltip.js` | app, theme | markup | 3, 4 |
| 31 | unrel. | `formsets/control.html` without `data-cv-class` | delete toggle not recoloured | theme | silent | 4, 5 |
| 32 | unrel. | Active current-view button | `cv_active` | app | markup | 3 |
| 33 | unrel. | `crud_views/detail/` templates and `cv_is_true` / `cv_is_false` / `cv_is_list` removed (#217) | gone | theme | TemplateSyntaxError | 4 |
| 34 | unrel. | Delete-page / guardian alerts through `tags/alert.html` | `snippets/delete/protection_errors.html`, `snippets/guardian/config_table.html` | theme | markup | 4 |
| 35 | unrel. | `tags/list_action_form.html` `hidden` | template | app | markup | 3 |
| 36 | unrel. | jQuery only for formsets; `adapters.js` first core script | `static/crud_views/js/adapters.js` | app | silent for hand-listed JS | 3 |
| 37 | unrel. | Filter toggle `aria-expanded` / `aria-controls`, `#filter-collapse` contract | `tags/context_action_filter.html` | theme | degrades | 4 |
| 38 | unrel. | Button class utility slots, card / alert keys, `form_frame`, card blocks | `lib/button_classes.py`, templates | theme | — (new hooks) | 4 |
| 39 | unrel. | Form pages: `view_{create,update,custom_form,delete}.content.html` extend `snippets/form_frame.html`; create / custom-form post `multipart/form-data` (#236); create renders media once (#191) | templates | theme | silent: a 0.29 copy keeps the old `<form>` without `enctype`, so file fields upload nothing | 4, 5 |
| 40 | **gap** | A 0.29/0.30 override of `tags/card_action.html` that branches on `cv_no_label` | the card action context carries `cv_label_mode`, no `cv_no_label` (`lib/views/card.py:44-87`), so the override always shows the label; the CHANGELOG says such overrides "keep working" | theme | silent | 4, 5 |

New checks that only fire on a misconfigured new feature (table rows in step zero, no migration step): `E351`,
`E354`, `E355`, `E356`, `W352`, `W353` (icon libraries), `E361`, `W362` (button classes), `E106`, `viewset.E209`,
`E211`, `W291` (variants, label modes).

## Private downstream scan

A read-only scan of the maintainer's downstream projects was run against this inventory. It found one unrecorded break
(row 40) and confirmed hits for rows 1, 3, 4, 6, 7, 9, 11, 12, 14, 17, 19, 21, 22, 23, 26 and 39. Details stay outside the
repository.

## Result

- Every inventory row is cited in the guide: section 2 (step zero), 3 (`An app on the stock bootstrap5 theme`),
  4 (`A downstream theme`) or 5 (`Silent breaks`), as its "Sec." column says. Row 16 (`cv_label_visible`) is the one
  exception by design: the key existed in neither 0.29.4 nor 0.30.0, so it is not part of the net change.
- Every row marked silent appears in the `Silent breaks` checklist.
- No *[0.30]* step describes an overtaken state: the boolean widget, `actions_menu_item_label.html` and
  `tags/messages.html` are described at their 1.0 state.
- CHANGELOG/code mismatch: `### Breaking` says the 0.30 overrides of the logic templates "keep working". For
  `tags/card_action.html` that is not true when the override branches on `cv_no_label` (row 40). A new
  `### Breaking` bullet records it; the original line is left as it is.
- CHANGELOG additions: the row-40 bullet under `### Breaking`, the guide under `### Added`, and a pointer under
  `## Unreleased`.
- Reference pages fixed: none needed. Every linked page and anchor matched the code; `mkdocs build --strict` passes.
- `CLAUDE.md` carries the keep-current rule under Conventions.
- `git diff main...` contains no downstream project or client name (guard grep, run before every commit).
