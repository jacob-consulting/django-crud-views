# Acceptance report — dead `crud_views/detail/` templates (#217)

Branch `feat/217-dead-detail-templates`. No spec or plan: issue #217 carried the acceptance criteria and the change is
four file deletions, three filter removals, two docs cells and one guard test (maintainer's call, 2026-10-21).

## The question the issue asked: dead or live?

**Dead.** The issue's own greps were right; what they could not show is where the consumer went.

Observed, not inferred:

- `git show 33584ff^:crud_views/lib/views/detail_layout.py` — the file removed by `33584ff` ("remve crispy property
  display draft") is the only thing that ever named these templates: `helper.field_template =
  "crud_views/detail/field.html"  # for testing only` (line 50) and `template_name =
  "crud_views/detail/widgets/{display,bool,date}.html"` (lines 17, 27, 31). `date.html` was deleted with it; the other
  four files were missed.
- `src/crud_views/lib/check.py` — the two `get_template()` calls the issue flagged as a possible caller are
  `CheckTemplateOrCode` and `CheckTemplate`. Both read a named attribute off a view or ViewSet
  (`getattr(self.context, self.attribute, None)`); neither walks an app's template directory. So the checks cannot
  reach `field.html`, and the `TemplateDoesNotExist` of Part 2 was never reachable either.
- The two later commits that touched the files, `295adc9` (icon registry) and `d653ee3` (move under `src/`), are
  mechanical sweeps, not uses.
- `crud_views_object_detail` renders detail pages today, through its own `crud_views_object_detail/...` paths.

## What was removed

| File | Why |
|---|---|
| `src/crud_views/templates/crud_views/detail/field.html` | the vendored crispy-bootstrap5 copy with the four hardcoded `bootstrap5/layout/*` includes |
| `.../detail/widgets/attrs.html`, `bool.html`, `display.html` | the widget templates of the same draft |

The `detail/` directory goes with them. Also removed, from `src/crud_views/templatetags/crud_views.py`:
`cv_is_true`, `cv_is_false` (called only from the deleted `widgets/bool.html`) and `cv_is_list` (called from nowhere
in the repo). Found by grepping the whole tree minus `.git`, `.venv`, `.nox`, `node_modules` and `site`.

Not marked breaking in `CHANGELOG.md`: the templates and the filters were undocumented internals of a removed draft.
The filters were technically loadable from `{% load crud_views %}`, which is why the entry names all three.

## Icons kept, docs corrected

`field-marker` stays in both registries (`src/crud_views/lib/icons.py:37` and `:68`) and keeps its
`test_icons_registry.py` coverage — maintainer's call, so a project template can still use it. Two usage cells in
`docs/reference/icons.md` were false after the deletion and were fixed:

- `field-marker` — "detail widgets" → "no built-in consumer, available to project templates".
- `boolean-true` / `boolean-false` — "boolean values (core widget and object detail)" → "boolean values in object
  detail". The core widget was the deleted `widgets/bool.html`; the remaining caller is
  `crud_views_object_detail/types/default/boolean.html`.

## Acceptance criteria

| Criterion (#217) | Status |
|---|---|
| The question answered | dead code; consumer removed in `33584ff`, evidence above |
| The file and any other unreferenced `detail/` templates removed | all four gone, directory empty and removed |
| A test or check that no `bootstrap5/` template name remains in the package templates | `tests/test1/test_templates_no_crispy_pack_guard.py` |

The guard walks `src/crud_views*/templates/**/*.html` and asserts no file contains a `bootstrap5/` template path, one
test case per file plus one that the file list is non-empty (so an emptied glob cannot pass silently). It follows
`tests/test1/test_js_no_jquery_guard.py`: repo-relative `Path(__file__).resolve().parents[2]`, one compiled pattern,
an assertion message naming the offending file. Deliberately **not** `get_app_template_dirs`, which would also sweep
the stale copies under `.nox/*/site-packages/crud_views/`.

The pattern is `(?<![\w-])bootstrap5/`, not a bare `bootstrap5/`: a downstream theme app named
`crud_views_bootstrap5` would otherwise trip the guard on an ordinary `{% static
"crud_views_bootstrap5/css/x.css" %}`.

Watched failing for the right reason, and watched *not* firing on the near miss. Two planted probes under
`src/crud_views/templates/crud_views/`: `__probe_bad.html` with `{% include "bootstrap5/layout/x.html" %}` failed as
`test_template_has_no_crispy_pack_path[crud_views/templates/crud_views/__probe_bad.html]`, while `__probe_ok.html`
with `{% static "crud_views_bootstrap5/css/x.css" %}` passed. Both probes were deleted and the suite went green.

## Verification

- `pytest tests -n auto` — 1694 passed, 3 skipped.
- `ruff format .` — 489 files left unchanged; `ruff check .` — all checks passed (venv ruff 0.17.1, matching the
  `ruff>=0.17,<0.18` pin).
- `grep -rn "bootstrap5/" src` — no matches.
