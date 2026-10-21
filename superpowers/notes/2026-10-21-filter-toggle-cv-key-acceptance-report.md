# Acceptance report — filter toggle `cv-key` (#208)

Branch `fix/filter-toggle-cv-key`. No spec or plan: issue #208 carried the acceptance criteria and the change is one
assignment, one test pair, one golden and one docs paragraph (maintainer's call, 2026-10-21).

## What `cv-key` means, checked before deciding

The issue offered two values and one removal. The deciding fact is that `cv-key` in a context toolbar is the key of
the view a button *targets*, not the button's own key: every other `ContextButton.get_context()` ends in
`cls.cv_get_dict()`, which seeds `cv_key` from the target view class (`src/crud_views/lib/view/base.py:354`).

Observed, not inferred:

- `tests/test1/golden/action_menus/toolbar_publisher_list.html` — the first entry is `cv-key="list"` and it is the
  **home** button, `ContextButton(key="home", key_target="list")` from `context_buttons_default()`.
- `tests/test1/test_button_leaves.py::test_custom_template_button_in_container` — `ContextButton(key="pill",
  key_target="update")` renders `cv-key="update"`, with a comment already saying so.

So `context.view.cv_key` was rejected: it would render a second `cv-key="list"` inside the same `fieldset` and break
every `[cv-key=list]` selector. `self.key` was chosen because the toggle has no target view for the rule to consume.

Also checked, because the one-line fix depends on it: a context button with its own `template` is rendered with the
raw `get_context()` dict (`render_to_string(template, context=ctx)`, `src/crud_views/templatetags/crud_views.py:167`),
not through `cv_button_data()`. The assignment therefore reaches the template directly.

## Acceptance criteria

| Criterion (#208) | Status |
|---|---|
| The stock filter toggle renders `cv-key="filter"` | `test_filter_toggle_carries_its_own_key` |
| A test asserts every `a`/`button` in `[cv-context-container]` has a non-empty `cv-key` | `test_every_context_button_has_a_key` |
| Golden HTML updated | `toolbar_publisher_list.html`, the single changed line |
| `docs/reference/buttons.md` mentions the toggle's `cv-key` | paragraph after the `LEAF_KEYS` table |

Both tests were watched failing first, for the right reason (`assert '' == 'filter'` and
`[('a', 'list'), ('button', ''), ('a', 'manage')]`), then passing.

## Scope checks from the issue

- Other hand-built button contexts: `FilterContextButton` is the only `ContextButton` subclass with its own
  `template` default (`src/crud_views/lib/view/buttons.py:301`); the rest render through the leaf, which takes
  `cv_key` from `cv_button_data()`. Nothing else omits a key a template renders.
- Pinned filter: `get_context()` returns `{"cv_access": False}` before the assignment, so no toggle and no key.
- Goldens with a toolbar: three. Only the publisher list has a toggle; the two detail goldens are unchanged, which the
  regeneration confirmed (`git diff --stat` shows one file).

## Verification

- `pytest tests` — 1513 passed, 3 skipped.
- `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py` — 8 passed, one golden line changed.
- `uvx "ruff>=0.16,<0.17" format --check .` — 483 files already formatted; `ruff check .` — all checks passed.

## Noted, not fixed

While answering "why is this context hand-built", a separate upstream concern came up and is **not** part of this
branch: `tags/button/action.html` renders label *or* icon, never both, so a card button with a label drops its
computed `cv_icon`. That "buttons with text never have an icon" rule came from one downstream project's designer and
is baked into the shared leaf. It deserves its own issue.
