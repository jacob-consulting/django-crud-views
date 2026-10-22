# Configurable Heading Level Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One setting, `CRUD_VIEWS_HEADER_LEVEL`, sets the level of the view header. The package's card, workflow,
object-detail and modal headings follow it, and default output stays byte-identical.

**Architecture:** A new block tag `{% cv_heading %}` in `crud_views/templatetags/crud_views.py` renders the heading
element from the template's own level, the setting (read at render time) and an optional class. Every inventory
template switches to it. Goldens taken *before* the switch pin the default output.

**Tech Stack:** Django templates (custom `Node`), Pydantic settings, pytest + lxml goldens.

**Spec:** `superpowers/specs/2026-10-22-heading-level-design.md`

## Global Constraints

- Setting name `CRUD_VIEWS_HEADER_LEVEL`, attribute `header_level`, default `None`, valid values `None` or `int` (not
  `bool`) 1–5. Anything else is `crud_views.E107`.
- Content heading level = `header_level + 1` when set, else the template's own `level`.
- Header mode level = `header_level` when set, else `level`.
- Size class `h{level}` is prepended to `class` only when the rendered level differs from `level` (both modes).
- With the setting unset, every inventory template's output is byte-identical to today.
- No `### Breaking` CHANGELOG entry; `docs/migrating-1.0.md` unchanged.
- Line length 120, double quotes, `cv_` prefix for tags.
- Branch `feat/heading-level`, in place (no worktree), one commit per task. Run tests with `pytest tests -n auto`.

## Review Focus

- Overriding `{% block card_title %}` in a template that extends `tags/card.html` must still work once the block sits
  inside `{% cv_heading %}` (needs `child_nodelists`). Test in Task 2.
- A `class` value containing `"` or `<` must be escaped, not break the attribute. Test in Task 2.
- The setting is read at render time, not import time, so `monkeypatch.setattr(crud_views_settings, "header_level", …)`
  and a changed Django setting at startup both apply. Every Task 3 test relies on this.
- An empty `class` (e.g. `class=""` or a class key resolving to `""`) renders no `class` attribute at the template's
  own level, but `class="h5"` alone when the size rule fires. Test in Task 2.
- `level` missing or outside 1–6 in a template is a `TemplateSyntaxError` at parse time, not silent wrong markup.
  Test in Task 2.

---

### Task 1: Goldens of today's heading markup

Safety net before any template changes. These tests pass immediately.

**Files:**
- Create: `tests/test1/test_heading_level.py`
- Create: `tests/test1/golden/heading_level/*.html` (generated)

**Interfaces:**
- Produces: helpers in `tests/test1/test_heading_level.py`, reused by Task 3:
  - `_headings(markup: str) -> str`: every `h1`–`h6` element in `markup` (lxml, document order), serialized with
    `lxml_html.tostring(..., encoding="unicode")`, stripped, joined with `"\n"`.
  - `_compare(name: str, actual: str)`: same mechanism as `test_action_menus_golden._compare`, with
    `GOLDEN_DIR = Path(__file__).parent / "golden" / "heading_level"` and `CV_UPDATE_GOLDEN=1` rewriting.
  - `_render_group(layout: str) -> str`: as `tests/test1/od/test_icons.py::render_group`, with
    `ResolvedGroup(title="Test", description="Desc", properties=[], icon=None)`.
  - Surfaces (one golden each, name in brackets):
    - card list page `reverse(cv_author.get_router_name("card"))`, client with full author perms, one Author
      [`card`];
    - workflow page `/campaign/{campaign_new.pk}/workflow/` via `client_user_campaign_change` [`workflow`] (must
      contain both "Workflow Action" and "Workflow History"; create history first by running one transition if the
      history section needs `object.workflow_data`, see `tests/test1/test_workflow.py:229` for fixtures);
    - each object-detail layout `accordion`, `card-rows`, `list-group-3col`, `split-card`, `striped-rows`,
      `table-inline`, `tabs-vertical` via `_render_group` [`od_<layout>`];
    - modal partial: GET author_modal detail URL with `headers={"X-CV-Modal": "true"}`, user with view perm on
      `cv_author_modal` [`modal_detail`].

- [ ] **Step 1: Write `test_heading_golden_default` parametrized over the surfaces above.** Each asserts
  `_compare(f"{name}", _headings(markup))`, plus a sanity assertion that the golden is non-empty.
- [ ] **Step 2: Generate goldens:** `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_heading_level.py`. Inspect the files:
  card golden shows `<h5 class="card-title">`, accordion `<h2 class="accordion-header">`, modal `<h5 class="modal-title">`,
  workflow two bare `<h5>`.
- [ ] **Step 3: Run without the env var:** `pytest tests/test1/test_heading_level.py -v`. Expected: PASS.
- [ ] **Step 4: Commit** `test(heading): goldens of today's heading markup (#251)`.

### Task 2: Setting, system check and the `cv_heading` tag

**Files:**
- Modify: `src/crud_views/lib/settings.py` (attribute next to `inaccessible_actions`; check in `check_messages`)
- Modify: `src/crud_views/templatetags/crud_views.py` (tag next to `cv_header`)
- Test: `tests/test1/test_settings_checks.py`, `tests/test1/test_heading_tag.py` (create)

**Interfaces:**
- Produces:
  - `CrudViewsSettings.header_level: Any = from_settings("CRUD_VIEWS_HEADER_LEVEL", default=None)`, commented like its
    neighbours (`# level of the host's {% cv_header %} (#251); package headings render one below; None = unchanged`).
  - Template tag `{% cv_heading ["header"] level=<int literal 1–6> [class=<expr>] %}…{% endcv_heading %}`.
    `CvHeadingNode(template.Node)` with `child_nodelists = ("nodelist",)`; renders body with the caller's context;
    reads `crud_views_settings.header_level` in `render()`.

- [ ] **Step 1: Write failing check tests** in `test_settings_checks.py`:
  `test_header_level_valid` (parametrize `None, 1, 3, 5`: `CrudViewsSettings(header_level=v).check_messages == []`) and
  `test_header_level_invalid` (parametrize `0, 6, "2", True, 2.0`: exactly one message, `id == "crud_views.E107"`,
  `"CRUD_VIEWS_HEADER_LEVEL"` in `msg`).
- [ ] **Step 2: Write failing tag tests** in `test_heading_tag.py`, rendering `Template("{% load crud_views %}…")`
  with `monkeypatch.setattr(crud_views_settings, "header_level", v)`:
  - unset, `level=5 class="card-title"` → `<h5 class="card-title">X</h5>`; unset, `level=5` → `<h5>X</h5>`;
  - `1`, `level=5 class="card-title"` → `<h2 class="h5 card-title">X</h2>`; `2` → `<h3 class="h5 card-title">X</h3>`;
  - `1`, `level=2 class="accordion-header"` → `<h2 class="accordion-header">X</h2>` (rendered equals own level);
  - `1`, `level=5` → `<h2 class="h5">X</h2>`; unset, `level=5 class=""` → `<h5>X</h5>`;
  - header mode: unset, `"header" level=5 class="modal-title"` → `<h5 class="modal-title">X</h5>`;
    `1` → `<h1 class="h5 modal-title">X</h1>`; `"header" level=1 class="h3"` at `1` → `<h1 class="h3">X</h1>`;
  - `class=cls` with context `{"cls": 'a" onclick="x'}` → the quote is escaped (`&quot;`);
  - body sees context: `{{ name }}` inside renders the context value;
  - block override: `Engine(loaders=[("django.template.loaders.locmem.Loader", {"p.html": …, "c.html": …})],
    libraries={"crud_views": "crud_views.templatetags.crud_views"})`, parent
    `{% load crud_views %}{% cv_heading level=5 %}{% block t %}A{% endblock %}{% endcv_heading %}`, child
    `{% extends "p.html" %}{% block t %}B{% endblock %}` → `<h5>B</h5>`;
  - `TemplateSyntaxError` for: no `level`, `level=0`, `level=7`, `level="x"`, unknown kwarg, positional other than
    `"header"`, missing `endcv_heading`.
- [ ] **Step 3: Run:** `pytest tests/test1/test_settings_checks.py tests/test1/test_heading_tag.py -v`. Expected: FAIL.
- [ ] **Step 4: Implement the setting and the E107 check.** Message:
  `f"setting CRUD_VIEWS_HEADER_LEVEL must be None or an int from 1 to 5, got {self.header_level!r}"`.
- [ ] **Step 5: Implement the tag.** Output exactly `<h{n}>` when the class list is empty, else
  `<h{n} class="{classes}">`, where classes is `"h{level}"` (when the rule fires) followed by the escaped `class`
  value, joined with one space, empty parts dropped; close with `</h{n}>`. No whitespace added around the body.
- [ ] **Step 6: Run** the two test files. Expected: PASS. Then `pytest tests -n auto`: all PASS.
- [ ] **Step 7: Commit** `feat(heading): CRUD_VIEWS_HEADER_LEVEL and {% cv_heading %} (#251)`.

### Task 3: Inventory templates use `cv_heading`

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/card.html:6`
- Modify: `src/crud_views/templates/crud_views/modal/content.html:3`
- Modify: `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:7`,
  `view_workflow.history.html:4`
- Modify: `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/{accordion,card-rows,list-group-3col,split-card,striped-rows,table-inline,tabs-vertical}/group.html`
- Test: `tests/test1/test_heading_level.py`

**Interfaces:**
- Consumes: `{% cv_heading %}` and `crud_views_settings.header_level` from Task 2; helpers from Task 1.

- [ ] **Step 1: Write failing level tests** in `test_heading_level.py`, parametrized over `header_level` `1` and `2`
  (`n = header_level + 1`), same surfaces as Task 1:
  - card: every `.card-title` element is tag `h{n}`, class starts with `h5 card-title`, `card_title` text intact;
  - workflow: the "Workflow Action" and "Workflow History" headings are `h{n}` with `class="h5"`;
  - each object-detail layout: the group heading (text `Test`) is `h{n}`; for the six `h5` layouts the class starts
    with `h5` followed by today's classes; accordion is `h{n}` with class `accordion-header` at `1`, `h2 accordion-header`
    at `2`;
  - modal partial: `.modal-title` is `h{header_level}`, class `h5 modal-title`; the object-detail group headings in
    the partial are `h{n}`.
- [ ] **Step 2: Run:** `pytest tests/test1/test_heading_level.py -v`. Expected: level tests FAIL, goldens PASS.
- [ ] **Step 3: Convert the templates.** Each keeps its current level as `level` and its current classes as `class`:
  - card: `{% cv_button_class "card" "title" as cv_card_title_class %}` then
    `{% cv_heading level=5 class=cv_card_title_class %}{% block card_title %}…{% endblock card_title %}{% endcv_heading %}`;
  - modal: `{% cv_heading "header" level=5 class="modal-title" %}{% cv_header_icon %} {% cv_header %}{% endcv_heading %}`;
  - workflow: `{% cv_heading level=5 %}{% translate "…" %}{% endcv_heading %}` (add `crud_views` to `{% load %}`);
  - object-detail: add `{% load crud_views %}`; the `mb-{% if group.description %}1{% else %}0{% endif %}` classes
    become `class=group.description|yesno:"card-title mb-1,card-title mb-0"`; accordion `level=2 class="accordion-header"`.
- [ ] **Step 4: Run** `pytest tests/test1/test_heading_level.py -v`: all PASS, goldens unchanged (do **not** set
  `CV_UPDATE_GOLDEN`). Then `pytest tests -n auto`: all PASS, including the existing card/action-menu/od goldens.
- [ ] **Step 5: Commit** `feat(heading): card, modal, workflow and object-detail headings follow the setting (#251)`.

### Task 4: Example project shows the intended setup

**Files:**
- Modify: `examples/bootstrap5/project/templates/project/crud_views.html:16-30`
- Modify: `examples/bootstrap5/project/settings.py` (next to `CRUD_VIEWS_EXTENDS`)
- Modify: `examples/bootstrap5/project/templates/project/example_about.html:6`
- Modify: `examples/bootstrap5/project/templates/project/snippet_panels.html:4,11,24`

- [ ] **Step 1: Base template.** Replace the `h5` > `div` > `h3` nest with a `div class="d-flex justify-content-between
  align-items-center"` holding `{% cv_heading "header" level=1 class="h3" %}…icon/header blocks…{% endcv_heading %}`
  and the `cv_context` block. Blocks `cv_header_icon`, `cv_header`, `cv_context` keep their names.
- [ ] **Step 2: Setting.** `CRUD_VIEWS_HEADER_LEVEL = 1`.
- [ ] **Step 3: Stray headings.** `example_about.html` sits before the `h1`: its `h6` becomes
  `<p class="h6 mb-1">` (an aside, not part of the outline). `snippet_panels.html` follows the content: section
  headings `h5` → `<h2 class="h5 …">`, accordion `h2` → `<h3 class="h2 accordion-header">`.
- [ ] **Step 4: Verify.** Run the example (`run` skill or `python examples/bootstrap5/manage.py runserver`), open an
  author detail, card list and workflow page; check the outline is `h1` → `h2` (→ `h3` in the snippet accordion) and
  the look is unchanged against `main`. Run `python examples/bootstrap5/manage.py check`: no issues.
- [ ] **Step 5: Commit** `docs(example): view title is the h1, CRUD_VIEWS_HEADER_LEVEL = 1 (#251)`.

### Task 5: Docs, CHANGELOG, acceptance note

**Files:**
- Modify: `docs/reference/settings.md` (new row; the closest existing section, or a new "Headings" section)
- Modify: `docs/reference/templates.md` (new section `## Heading levels` after "What to put in it")
- Modify: `CHANGELOG.md` (`### Added` under Unreleased)
- Create: `superpowers/notes/2026-10-22-heading-level-acceptance.md`

- [ ] **Step 1: settings.md row:** `CRUD_VIEWS_HEADER_LEVEL` | the level of your `{% cv_header %}` (1–5); package
  headings render one below and keep their look; `None` leaves them as they are. Invalid values raise
  `crud_views.E107`. | `int \| None` | `None`. Link to the templates.md section.
- [ ] **Step 2: templates.md section:** the table from the spec's Goals, both tag modes, the size-class rule, the
  modal note, and the base-template snippet from Task 4 Step 1.
- [ ] **Step 3: CHANGELOG** `### Added` entry naming the setting, the tag, E107, and that default output is unchanged.
- [ ] **Step 4: Verify:** `task check`, `task format`, `pytest tests -n auto` all clean; `mkdocs build --strict` (or
  `task docs` and open the two pages) renders.
- [ ] **Step 5: Acceptance note** mapping each spec Goal and Test bullet to the test or file that proves it, in the
  format of `superpowers/notes/2026-10-22-form-frame-acceptance.md`.
- [ ] **Step 6: Commit** `docs(heading): CRUD_VIEWS_HEADER_LEVEL and {% cv_heading %} (#251)`.

Hand-over (not a task): draft the updated issue #251 body (setting name and meaning, 1–5, accordion, modal in scope)
and the PR text per `.github/PULL_REQUEST_TEMPLATE.md`; the maintainer approves both in one answer.
