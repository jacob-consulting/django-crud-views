# One Data-Driven Alert Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every alert in the package renders through one frame, `crud_views/tags/alert.html`, fed by
`alert_data()` dicts. Themes restyle alerts through the frame, a list-body template and `alert:*` class keys.

**Architecture:** `alert_data()` in `lib/messages.py` builds an escaped, render-ready dict, including which body
template to use. `{% cv_messages %}` loops over those dicts. The new `{% cv_alert %}` renders one dict into the
caller's context. The frame includes `alert.body_template` and never branches on the body type. Colours come from
the class table.

**Tech Stack:** Django templates, pytest + pytest-django, ruff.

**Spec:** `superpowers/specs/2026-10-22-alert-template-design.md` (issue #250)

## Global Constraints

- Branch `feat/alert-template`, in place (no worktree). One commit per task. The PR closes #250.
- Levels: exactly `error`, `warning`, `success`, `info`, `debug`. Anything else becomes `info`.
- Keys and defaults: `alert:error` = `alert alert-danger`, `alert:warning` = `alert alert-warning`,
  `alert:success` = `alert alert-success`, `alert:info` = `alert alert-info`, `alert:debug` = `alert alert-secondary`.
  The table grows from 46 to 51 keys.
- Template paths: `crud_views/tags/alert.html`, `crud_views/snippets/alert/text.html`,
  `crud_views/snippets/alert/list.html`, `crud_views/tags/messages.html`.
- `ALERT_CLASSES` and `ICON_NAMES` are removed, with no compatibility keys. The message dicts drop `css_class`
  and `message`. This is a clean breaking change.
- Message output in the stock theme is unchanged apart from whitespace.
- Heading msgids are unchanged byte for byte.
- Line length 120, double quotes. Run `task format` and `task check` before each commit.
- Tests: `pytest tests -n auto`.

## Review Focus

1. **The `alert` name in the caller's context.** A host template that loops `{% for alert in my_alerts %}` and
   calls `{% cv_alert %}` inside must get its own `alert` back after the tag. The tag pushes and pops; it never
   leaks. → Task 2, `test_cv_alert_restores_the_callers_alert`.
2. **Hostile `__str__` in list items.** A protected object whose `__str__` contains `<script>` renders escaped,
   and a `SafeString` item passes through. → Task 1, `test_alert_data_escapes_items`.
3. **`{% autoescape off %}` around `{% cv_alert %}`.** Heading, items and text are still escaped. → Task 2,
   `test_cv_alert_escapes_with_autoescape_off`.
4. **A Bootstrap colour word used as the level** (`{% cv_alert "danger" %}`). It falls back to `info` and does
   not render an empty class. → Task 1, `test_alert_data_unknown_level_is_info`.
5. **German delete page.** The headings still translate after they move into tag arguments. → Task 3,
   `test_delete_alert_headings_translate`.

---

### Task 1: `alert_data()`, `LEVELS` and the `alert:*` keys

**Files:**
- Modify: `src/crud_views/lib/messages.py` (add `LEVELS` and `alert_data`; `ALERT_CLASSES`, `ICON_NAMES` and
  `message_alerts` stay for now, and Task 2 removes and rewrites them)
- Modify: `src/crud_views/lib/button_classes.py` (five rows after the `card:*` rows, with the comment
  `# alert frames (#250); the level is the slot`)
- Modify: `tests/test1/test_button_classes.py` (add the five keys to `EXPECTED_KEYS` and change the count to 51)
- Modify: `docs/reference/buttons.md` (five rows in the class table, plus one sentence saying they colour the
  alert frame, linking to `messages.md`)
- Create: `tests/test1/test_alerts.py`

**Interfaces:**
- Produces: `LEVELS: dict[int, str]`, mapping the `django.contrib.messages.constants` levels to the five words.
- Produces: `alert_data(level: str, *, heading="", text="", items=None, body_template: str | None = None,
  dismissible: bool = False, extra_tags: str = "") -> dict`, which returns the keys `level`, `icon_name`, `heading`,
  `text`, `items` (a list, `[]` when none), `body_template`, `dismissible` and `extra_tags`.
- Produces: the constants `TEXT_BODY = "crud_views/snippets/alert/text.html"` and
  `LIST_BODY = "crud_views/snippets/alert/list.html"` in `lib/messages.py`.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_alerts.py`:

```python
@pytest.mark.parametrize("level", ["error", "warning", "success", "info", "debug"])
def test_alert_data_keeps_a_known_level(level):
    data = alert_data(level, text="x")
    assert data["level"] == level
    assert data["icon_name"] == f"message-{level}"

@pytest.mark.parametrize("level", ["danger", "ERROR", "", None, 40])
def test_alert_data_unknown_level_is_info(level):
    assert alert_data(level)["level"] == "info"
    assert alert_data(level)["icon_name"] == "message-info"

def test_alert_data_picks_the_text_body_without_items():
    assert alert_data("info", text="x")["body_template"] == "crud_views/snippets/alert/text.html"
    assert alert_data("info", items=[])["body_template"] == "crud_views/snippets/alert/text.html"

def test_alert_data_picks_the_list_body_with_items():
    assert alert_data("error", items=["a"])["body_template"] == "crud_views/snippets/alert/list.html"

def test_alert_data_keeps_an_explicit_body_template():
    assert alert_data("warning", items=["a"], body_template="x.html")["body_template"] == "x.html"

def test_alert_data_escapes_heading_and_text():
    data = alert_data("info", heading="<b>h</b>", text="<i>t</i>")
    assert data["heading"] == "&lt;b&gt;h&lt;/b&gt;" and data["text"] == "&lt;i&gt;t&lt;/i&gt;"
    assert alert_data("info", text=mark_safe("<i>t</i>"))["text"] == "<i>t</i>"

def test_alert_data_escapes_items():
    class Hostile:
        def __str__(self):
            return "<script>x</script>"
    assert alert_data("error", items=[Hostile(), mark_safe("<b>ok</b>")])["items"] == [
        "&lt;script&gt;x&lt;/script&gt;", "<b>ok</b>"]

def test_alert_data_blanks_falsy_heading_and_text():
    data = alert_data("info", heading=None, text=None)
    assert data["heading"] == "" and data["text"] == ""

def test_alert_data_escapes_extra_tags_and_defaults():
    data = alert_data("info", extra_tags='">')
    assert data["extra_tags"] == "&quot;&gt;"
    assert data["dismissible"] is False and data["items"] == []
```

Add five parametrized cases to `tests/test1/test_button_classes.py`, asserting
`get_button_class("alert", "error") == "alert alert-danger"` and the same for the other four keys. Follow the
existing parametrize pattern there.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test1/test_alerts.py tests/test1/test_button_classes.py -v`
Expected: FAIL. `ImportError` on `alert_data`, and the count assertion `46 == 51`.

- [ ] **Step 3: Implement `LEVELS`, the two body constants and `alert_data`** in `lib/messages.py`, and add the
  five keys to `DEFAULT_BUTTON_CLASSES`. Escape items with `conditional_escape(item)`, which already calls `str()`
  on a non-string. Escape heading and text with `conditional_escape(value) if value else ""`, and `extra_tags`
  with `escape(extra_tags or "")`. Give `alert_data` a docstring that carries over the escaping rationale from
  `message_alerts`'s docstring.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test1/test_alerts.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/messages.py src/crud_views/lib/button_classes.py tests/test1/test_alerts.py \
  tests/test1/test_button_classes.py docs/reference/buttons.md
git commit -m "feat(alert): alert_data() and the alert:* class keys (#250)"
```

### Task 2: The frame, the body templates, `{% cv_alert %}` and `{% cv_messages %}` on top of them

**Files:**
- Create: `src/crud_views/templates/crud_views/tags/alert.html` (the frame from the spec's "Templates" section)
- Create: `src/crud_views/templates/crud_views/snippets/alert/text.html` (`{{ alert.text }}`)
- Create: `src/crud_views/templates/crud_views/snippets/alert/list.html`
  (`<ul class="mb-0 mt-2">{% for item in alert.items %}<li>{{ item }}</li>{% endfor %}</ul>`)
- Modify: `src/crud_views/templates/crud_views/tags/messages.html` (becomes the loop from the spec, with
  `{% for alert in cv_message_alerts %}{% include "crud_views/tags/alert.html" %}{% endfor %}`)
- Modify: `src/crud_views/lib/messages.py` (remove `ALERT_CLASSES` and `ICON_NAMES`; `message_alerts` becomes
  `alert_data(LEVELS.get(level, "info"), text=body, dismissible=True, extra_tags=...)` per message, keeping its
  docstring and its rules for a falsy body and a missing level)
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_alert` next to `cv_messages`)
- Modify: `tests/test1/test_messages.py`
- Modify: `tests/test1/test_alerts.py`

**Interfaces:**
- Consumes: `alert_data`, `LEVELS` (Task 1).
- Produces: `cv_alert(context, level, heading="", text="", items=None, body_template=None, dismissible=False,
  extra_tags="") -> SafeString`, registered with `@register.simple_tag(takes_context=True)`. It renders
  `get_template(f"{crud_views_settings.theme_path}/tags/alert.html").template.render(context)` inside
  `with context.push(alert=alert_data(...)):`. Rendering the inner `Template` against the same context is what
  lets the body template see the caller's variables. Wrap the result in `mark_safe`.

- [ ] **Step 1: Update `test_messages.py` to the new dict shape.** In the parametrize, `css_class` becomes
  `level` with the values `"debug"`, `"info"`, `"success"`, `"warning"`, `"error"`. `alert["message"]` becomes
  `alert["text"]` and `alert["css_class"]` becomes `alert["level"]`, with `"info"` for the two fallback tests.
  Add `assert alert["dismissible"] is True`. All the rendering assertions (`class="alert alert-success
  alert-dismissible fade show"`, the autoescape-off line, and so on) stay as they are.

- [ ] **Step 2: Add the `cv_alert` tests to `test_alerts.py`.** Render with
  `Template("{% load crud_views %}" + src).render(Context(ctx))` and normalize whitespace with the `_norm` from
  `test_form_frame.py` (copy it or import it).

```python
def test_cv_alert_renders_the_frame_with_a_list():
    html = _norm(_render('{% cv_alert "error" heading="H" items=errs %}', {"errs": ["a", "b"]}))
    assert html == ('<div class="alert alert-danger" role="alert"><i class="fa-solid fa-circle-exclamation me-2" '
                    'aria-hidden="true"></i><strong>H</strong><ul class="mb-0 mt-2"><li>a</li><li>b</li></ul></div>')

def test_cv_alert_body_template_sees_the_callers_context():
    # locmem override (the _theme_templates pattern from test_form_frame.py) with "body.html": "{{ outer }}"
    assert "OUTER" in _render('{% cv_alert "info" body_template="body.html" %}', {"outer": "OUTER"})

def test_cv_alert_restores_the_callers_alert():
    html = _render('{% for alert in xs %}{% cv_alert "info" text="t" %}[{{ alert }}]{% endfor %}', {"xs": ["mine"]})
    assert "[mine]" in html

def test_cv_alert_escapes_with_autoescape_off():
    html = _render('{% autoescape off %}{% cv_alert "error" heading=h items=i text=t %}{% endautoescape %}',
                   {"h": "<h>", "i": ["<i>"], "t": "<t>"})
    assert "<h>" not in html and "<i>" not in html

def test_cv_alert_is_not_dismissible_by_default():
    html = _render('{% cv_alert "warning" text="t" %}', {})
    assert "btn-close" not in html and "alert-dismissible" not in html

@pytest.mark.parametrize("override", ["crud_views/tags/alert.html", "crud_views/snippets/alert/list.html"])
def test_each_alert_template_is_overridable_on_its_own(override):
    # override one template with '<x-theme>{{ alert.level }}</x-theme>'; the other keeps stock markup
    ...

def test_alert_colours_follow_the_class_table(settings):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"alert:error": "notification is-danger"}
    assert 'class="notification is-danger"' in _render('{% cv_alert "error" text="t" %}', {})
```

The overridable-on-its-own test asserts two things. When `alert.html` is overridden, the output is
`<x-theme>error</x-theme>` and contains no `<ul`. When `list.html` is overridden, the output still starts with
`<div class="alert alert-danger"` and contains `<x-theme>`.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `pytest tests/test1/test_messages.py tests/test1/test_alerts.py -v`
Expected: FAIL. `KeyError 'text'` in the message tests, and `Invalid block tag 'cv_alert'` in the new ones.

- [ ] **Step 4: Implement the four templates, the `message_alerts` rewrite and `cv_alert`.** The frame loads
  `crud_views i18n`. The heading renders as `<strong>{{ alert.heading }}</strong>` only when it is set. The close
  button renders only when `alert.dismissible` is true. Keep the frame's line layout close to the current
  `messages.html`, so that the existing message assertions match byte for byte (they check whole `class="…"`
  strings, not whitespace between tags).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests -n auto`
Expected: PASS. `test_button_classes_templates.py` scans only `btn`-prefixed tokens and already exempts
`btn-close`.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/alert.html src/crud_views/templates/crud_views/snippets/alert \
  src/crud_views/templates/crud_views/tags/messages.html src/crud_views/lib/messages.py \
  src/crud_views/templatetags/crud_views.py tests/test1/test_messages.py tests/test1/test_alerts.py
git commit -m "feat(alert): one alert frame; cv_messages loops it and cv_alert renders one (#250)"
```

### Task 3: The delete page alerts go through `{% cv_alert %}`

**Files:**
- Modify: `src/crud_views/lib/views/delete.py` (`get_context_data`: add
  `context["related_summary_items"] = [f"{name}: {count}" for name, count in related.summary.items()]` next to
  `related_summary`)
- Modify: `src/crud_views/templates/crud_views/snippets/delete/protection_errors.html`
- Modify: `src/crud_views/templates/crud_views/snippets/delete/related_objects.html` (keep the
  `.cv-related-objects mb-3` wrapper and its `{% if %}`s; the three alerts become the spec's calls, and the tree
  alert sits inside `{% with items=related_objects %}`)
- Modify: `tests/test1/test_form_frame.py` (`test_theme_frame_wraps_the_protection_alert` now asserts
  `startswith('<div class="theme-card"><div class="alert alert-danger" role="alert">')`)
- Regenerate: `tests/test1/golden/form_frame/delete_protection.html`
- Modify: `tests/test1/test_delete.py`

**Interfaces:**
- Consumes: `{% cv_alert %}` (Task 2).
- Produces: the delete context key `related_summary_items: list[str]`.

- [ ] **Step 1: Write the failing tests** in `test_delete.py`. Reuse the existing cascade fixtures, and
  copy the permission setup from `test_related_objects_rendered_in_template`.

```python
def test_related_summary_items_are_ready_strings(...):
    # two Books on publisher_penguin
    assert response.context["related_summary_items"] == ["book: 2"]  # same key text as related_summary

def test_delete_alerts_render_through_the_frame(...):
    # one Book (view permissions granted) + one Contract (protected)
    content = response.content.decode()
    assert content.count('role="alert"') == 3          # protected, summary, tree
    assert 'class="alert alert-danger" role="alert"' in content
    assert content.count('class="alert alert-warning" role="alert"') == 2
    assert "<li>book: 1</li>" in content

def test_delete_alert_headings_translate(...):
    # render protection_errors.html under translation.override("de") with delete_protection_errors=["x"]
    assert "Dieses Objekt kann nicht gelöscht werden:" in html
```

Use whatever the summary key actually is: check what `related.summary` holds in
`test_related_objects_shown_when_enabled` (`summary["book"]`) and write the expected string from that.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test1/test_delete.py tests/test1/test_form_frame.py -v`
Expected: FAIL. `KeyError 'related_summary_items'`, the `role="alert"` counts, and the golden mismatch.

- [ ] **Step 3: Implement the context key and the two snippets.** Both snippets `{% load crud_views i18n %}`.

- [ ] **Step 4: Regenerate the golden and inspect it.** Run
  `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_form_frame.py`, then `git diff tests/test1/golden`. The only
  changes should be `role="alert"` and the `<i class="fa-solid fa-circle-exclamation me-2" aria-hidden="true"></i>`
  icon before `<strong>`.

- [ ] **Step 5: Run the full suite**

Run: `pytest tests -n auto`
Expected: PASS. `test_protection_alert_overridable_on_its_own` passes unchanged.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/views/delete.py src/crud_views/templates/crud_views/snippets/delete \
  tests/test1/test_delete.py tests/test1/test_form_frame.py tests/test1/golden/form_frame
git commit -m "feat(alert): the delete page's alerts render through the alert frame (#250)"
```

### Task 4: The guardian manage page, and the guard across all apps

**Files:**
- Create: `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html` (the `<table>`
  moved over verbatim, with `{% load i18n %}`)
- Modify: `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html` (`{% load crud_views i18n %}`,
  then the `<h4>` stays and the alert becomes
  `{% cv_alert "warning" body_template="crud_views/snippets/guardian/config_table.html" %}`)
- Modify: `tests/test1/test_guardian.py`
- Modify: `tests/test1/test_alerts.py`

**Interfaces:**
- Consumes: `{% cv_alert %}` (Task 2).

- [ ] **Step 1: Write the failing tests**

In `test_guardian.py`, next to `test_guardian_manage_context_has_guardian_config`:

```python
def test_guardian_manage_config_renders_in_an_alert(client_guardian, cv_guardian_author):
    content = client_guardian.get("/guardian_author/manage/").content.decode()
    assert re.search(r'class="alert alert-warning" role="alert">.*?<table class="table table-striped mb-0">',
                     content, re.S)
    assert "cv_guardian_parent_permission" in content
```

In `test_alerts.py`:

```python
def test_only_the_alert_templates_write_alert_markup():
    # walk every src/crud_views*/templates/**/*.html
    offenders = [p for p in files if 'class="alert' in p.read_text()
                 and p.as_posix().split("/templates/")[1] not in ALLOWED]
    assert offenders == []
# ALLOWED = {"crud_views/tags/alert.html"} plus anything under "crud_views/snippets/alert/"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test1/test_guardian.py -k config_renders tests/test1/test_alerts.py -k only_the -v`
Expected: FAIL. No `role="alert"` on the manage page, and the guard lists `view_guardian_manage.html`.

- [ ] **Step 3: Move the table and switch the page to `{% cv_alert %}`**

- [ ] **Step 4: Run the full suite**

Run: `pytest tests -n auto`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_guardian/templates tests/test1/test_guardian.py tests/test1/test_alerts.py
git commit -m "feat(alert): the guardian manage page's config alert goes through the frame (#250)"
```

### Task 5: Docs, CHANGELOG, translations and acceptance note

**Files:**
- Modify: `docs/reference/messages.md`. In the "Levels" table, the "Alert class" column becomes "Class key"
  (`alert:debug` … `alert:error`), with its default next to it. A new section, "A single alert:
  `{% cv_alert %}`", gives the signature, the escaping rule, the default body choice, and the fact that the body
  template sees the caller's context. A short `alert_data` paragraph covers use from Python.
- Modify: `docs/reference/theme.md`. Replace the paragraph on `protection_errors.html` at lines 128–130 with an
  "Alerts" section covering the frame, the text body and the list body. It says what each is for, that
  `messages.html` is a loop not meant to be overridden, that colours come from `alert:*`, and that the three
  delete snippets and the guardian page only call `{% cv_alert %}`.
- Modify: `docs/reference/delete_view.md` (around line 141: mention `related_summary_items` and that the alerts
  render through `tags/alert.html`)
- Modify: `CHANGELOG.md` under `## Unreleased`.
  - `### Breaking`: the message dicts' `css_class` and `message` become `level` and `text`, and `ALERT_CLASSES`
    and `ICON_NAMES` are removed. Migration: replace a `tags/messages.html` override with a `tags/alert.html`
    override.
  - `### Added`: `{% cv_alert %}`, `alert_data()`, the three templates, the `alert:*` keys, and
    `related_summary_items`.
  - `### Changed`: the delete and guardian alerts gain `role="alert"` and the level icon.
- Modify: `src/crud_views/locale/de/LC_MESSAGES/django.po` and `src/crud_views_guardian/locale/de/LC_MESSAGES/django.po`
  (run `task msg-make`, then `task msg-comp`)
- Create: `superpowers/notes/2026-10-22-alert-template-acceptance.md` (each acceptance criterion from #250 and
  the spec, the test that proves it, and the crud_views_tabler follow-up: its `tags/alert.html` override, and
  deleting its `tags/messages.html` and `protection_errors.html` overrides)

- [ ] **Step 1: Write the docs and the CHANGELOG entries**

- [ ] **Step 2: Refresh the catalogs.** Run `task msg-make && task msg-comp`, then `git diff src/*/locale`. Only
  `#:` reference lines should change, and no msgid should become `#~` obsolete or fuzzy.

- [ ] **Step 3: Verify.** Run `pytest tests -n auto && task check && task format`, then
  `mkdocs build`. Expected: everything passes, and the docs build shows no warnings that are not already on
  `main`.

- [ ] **Step 4: Write the acceptance note**

- [ ] **Step 5: Commit**

```bash
git add docs CHANGELOG.md src/crud_views/locale src/crud_views_guardian/locale superpowers/notes
git commit -m "docs(alert): cv_alert, the alert templates and the alert:* keys (#250)"
```
