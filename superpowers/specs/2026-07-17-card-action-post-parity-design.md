# Card action POST/modal parity — design

- **Date:** 2026-07-17
- **Issue:** [#77](https://github.com/jacob-consulting/django-crud-views/issues/77) — Card list actions cannot trigger POST (405 on POST-only actions)
- **Affects:** 0.14.0 — pure package change, needs a patch release once merged.

## Problem

Actions rendered on a card list (`CardListView` via `CardAction`) are always emitted as plain
GET `<a href>` links. A `CardAction` whose target is a POST-only view — any `ActionView`
subclass: custom actions, ordered up/down, the showcase `RecipeFavoriteView` — renders a
clickable button that **405s** when clicked, because the target view defines only `post()`.

The equivalent action on a **table list** works: the table path renders a hidden POST form plus
a JS-submit trigger button.

### Root cause

The card path is behind the table path in one specific way: `cv_card_action`
(`src/crud_views/templatetags/crud_views.py:262`) **hand-rolls its context dict**, bypassing
`cv_get_dict()` — the `CrudView` classmethod that already emits `cv_list_action_method`,
`cv_modal`, and `cv_modal_size`. Because those keys never reach the template,
`card_action.html` can only render a bare GET link.

This one root cause produces **two** symptoms:

1. **POST actions 405** (the reported bug) — no POST branch, no hidden form.
2. **Modal actions silently navigate** (a latent gap) — a `cv_modal=True` target on a card
   navigates to a full page instead of opening the modal, because the card path never emitted
   `cv_modal`/`data-cv-modal`.

### Reference implementation (table path, already correct)

- `src/crud_views/templates/crud_views/tags/list_action.html` branches on the target view's
  method/modal:
  - `cv_modal` → `href` + `data-cv-modal="true"` + `data-cv-modal-size`
  - `cv_list_action_method == "get"` → `href="{{ cv_url }}"`
  - `cv_list_action_method == "post"` → `href="#"` + `data-cv-action="submit-form"` +
    `data-cv-target="cv_form_{{ cv_oid }}"`
- `src/crud_views/templates/crud_views/tags/list_action_form.html` renders the hidden form:
  `<form id="cv_form_{{ cv_oid }}" action="{{ cv_url }}" method="post" class="d-none">{% csrf_token %}</form>`
- The submit JS already exists and loads on every page via `cv_js`
  (`src/crud_views/static/crud_views/js/viewset.js` — `[data-cv-action='submit-form']` click
  handler). **No new client code is needed.**

## Approach: reuse `cv_get_dict()`, mirror `list_action.html`

Bring the card path up to the table path's mechanism instead of bolting on a POST special
case. Chosen over a minimal POST-only patch because the divergence (hand-rolled dict) is the
real defect: reusing `cv_get_dict()` fixes POST **and** modal in one consistent change and
removes the drift permanently. No new `CardAction` field — method and modal derive
automatically from the target view, exactly as the table does.

### 1. `cv_card_action` tag — `src/crud_views/templatetags/crud_views.py`

Regular-`key` branch (after the access check, which keeps its early no-access return):

```python
view_context = view.cv_get_view_context(object=obj)
data = cls.cv_get_dict(
    context=view_context,
    cv_oid=view.cv_get_oid(action.key, obj=obj),
    cv_url=url,
    cv_access=True,
    cv_action_enabled=action_enabled,
)
data.update(
    cv_label=label,
    cv_variant=action.variant,
    cv_flex=action.flex,
    cv_no_label=action.no_label,
)
return data
```

`cv_get_dict()` supplies `cv_list_action_method`, `cv_modal`, `cv_modal_size`, and the passed-in
`cv_oid` for free. `cv_get_oid(key, obj)` returns `{viewset}_{key}_{pk}` — the same scheme the
table uses, unique per card+action on the page (a card list is an alternative to a table list,
so no collision).

`child_name` branch: children are GET navigation to a child list (no POST, no modal). Keep it
building its own small dict, but add `cv_list_action_method="get"` (and no `cv_oid`/`cv_modal`)
so the uniform template branch renders it as a plain link. Its existing `cv_access`/
`cv_action_enabled`/label/variant/flex/no_label keys stay.

### 2. `card_action.html` — `src/crud_views/templates/crud_views/tags/card_action.html`

Mirror `list_action.html`'s three-way branch while keeping card styling (btn-variant mapping,
`flex-grow-1`, `no_label`→icon vs `<span>`label). For the POST case, emit the trigger anchor
**and** an inline hidden form:

- Guard: `{% if cv_access and cv_action_enabled is not False %}` (unchanged semantics).
- `{% if cv_modal %}` → `href="{{ cv_url }}" data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"`
- `{% elif cv_list_action_method == "post" %}` → `href="#" data-cv-action="submit-form" data-cv-target="cv_form_{{ cv_oid }}"`
  plus, alongside the anchor:
  `<form id="cv_form_{{ cv_oid }}" action="{{ cv_url }}" method="post" class="d-none">{% csrf_token %}</form>`
- `{% else %}` (GET / child) → `href="{{ cv_url }}"`

**Form placement — inline is safe here.** The table separates the form into its own loop
because a `<form>` inside a Bootstrap `.btn-group` breaks button-group border-radius/spacing.
The card container is `d-flex gap-2` (not a `btn-group`), and the form is `d-none`
(`display:none`, so it is not laid out as a flex item and `gap` does not apply to it). Emitting
the hidden form next to the anchor in the same tag output is therefore visually inert and keeps
the change to a single template + single tag function.

### 3. `CardAction` — `src/crud_views/lib/view/card.py`

No change. The issue floated an optional `CardAction.method` override; skip it (YAGNI). Deriving
method/modal from the target view keeps card and table consistent and automatic.

## Testing

New package test in `tests/` (e.g. `tests/test1/test_card_action_post.py`). Use POST-only
frontend `ActionView`s that already exist on `cv_author` — `AuthorUpView` / `AuthorDownView`
(`OrderedUpView`, POST-only) — as the motivating case (mirrors the issue's ordered up/down
example and avoids `cv_backend_only` access concerns).

To avoid disturbing existing `tests/test1/test_card.py` assertions on `AuthorCardListView`'s
exact action list, the test uses its own card view or monkeypatches `cv_card_actions` rather
than mutating the shared fixture.

Assertions on rendered markup:

- **POST action** → the anchor carries `data-cv-action="submit-form"` and
  `data-cv-target="cv_form_…"`, **and** a hidden `<form … method="post">` with a CSRF token is
  present — and it is **not** a bare GET `<a href="…/up/">`.
- **GET actions** (`detail` / `update`) → still render `href="{{ cv_url }}"`, no submit-form
  attributes, no form.
- **Modal action** (a `cv_modal=True` target, e.g. modal delete/detail) → renders
  `data-cv-modal="true"` — locks in the modal-parity fix.

Acceptance (end-to-end, from the issue): clicking a POST-only card action toggles state and
redirects (302), no 405; GET card actions and modal actions continue to work.

## Documentation

`docs/reference/card-list-view.md` currently documents `CardAction` with only GET-style
examples (`detail`/`update`/`delete`) and says nothing about POST/modal targets — exactly where
someone who hit the 405 would look. Add a short note (a couple of sentences, not a rewrite):
actions targeting POST-only views (ordered up/down, custom `ActionView`s) and modal-enabled
views render correctly — a POST submit form / modal trigger respectively — derived
automatically from the target view, the same as table lists. **In scope for this PR.**

## Follow-up (separate repo — not part of this PR)

The standalone `SKILL.md` (source in the shared skills monorepo; the plugin cache is a
read-only mirror) documents card lists with the same detail/update/delete examples. It makes no
now-false claim (there is no API change), so it is non-blocking — but because the scenario that
produced this bug was "author drops a POST action onto a card," a one-line note there
("`CardAction` targets that are POST-only or modal views work automatically") would preempt the
next occurrence. **Tracked here as a follow-up**: after the package fix merges/releases, mirror
the one-line note into `SKILL.md` in the skills monorepo.

## Scope summary

| Change | File | In this PR |
|---|---|---|
| Reuse `cv_get_dict()` in card tag | `src/crud_views/templatetags/crud_views.py` | ✅ |
| Full modal/GET/POST branch + inline hidden form | `src/crud_views/templates/crud_views/tags/card_action.html` | ✅ |
| Package test (POST + GET + modal rendering) | `tests/test1/test_card_action_post.py` | ✅ |
| Reference note on POST/modal card actions | `docs/reference/card-list-view.md` | ✅ |
| `CardAction` class | `src/crud_views/lib/view/card.py` | — (no change) |
| One-line skill note | `SKILL.md` (skills monorepo) | Follow-up |

No migration, no public API change. Reuses existing `submit-form` JS. Patch release after merge.
