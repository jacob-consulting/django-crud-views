# Drop django-bootstrap5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `django-bootstrap5` from the distribution by shipping a themed `{% cv_messages %}` tag plus five message-level icons, and by writing Bootstrap's own CSS/JS as explicit CDN tags in the two host base templates.

**Architecture:** `crud_views` already *produces* flash messages (`CrudViewMessageMixin.cv_form_valid_hook` → `messages.success()` with the rendered `cv_message_template` snippet; `ActionView` for success and error) but hands the *rendering* to django-bootstrap5's `{% bootstrap_messages %}`. A new `crud_views.lib.messages.message_alerts()` turns a message queue into render-ready dicts, a new `{% cv_messages %}` inclusion tag feeds `{theme_path}/tags/messages.html`, and the level → icon mapping uses five new names in the existing icon registry. Once both base templates stop calling `{% bootstrap_* %}`, the dependency leaves `pyproject.toml` entirely — not relocated to an extra.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12–3.15, pytest + pytest-django (+ `-n auto`), the existing `crud_views` icon registry and theme-path template resolution, Bootstrap 5.3.3 from jsDelivr.

**Spec:** GitHub issue [#221](https://github.com/jacob-consulting/django-crud-views/issues/221). No design doc: the issue is the spec, extended by the decisions below, which were settled in brainstorming on 2026-10-21 and are binding.

### Decisions settled in brainstorming (treat as spec)

1. `{% cv_messages %}` is **host-placed**, like `{% cv_breadcrumb %}` — the host drops it into their own base template, typically at the top of the content area. crud_views does not place it anywhere automatically.
2. Alerts are **dismissible**, via Bootstrap's declarative `data-bs-dismiss="alert"`. **No new JS file and no new `cv.adapters` entry.** The X is inert without Bootstrap's JS bundle — exactly as true today with `{% bootstrap_messages %}`. This follows the dominant pattern in shipped templates (`data-bs-toggle` in `actions_menu_toggle.html`, `language_selector.html`, the object-detail accordion and tabs layouts); the modal's `data-cv-modal-dismiss` is the exception, needed only because crud_views' own JS opens modals.
3. Message **icons ship in this change**, not as a follow-up, as five new semantic names in the icon registry.
4. The level → (`alert-*` class, icon name) mapping lives in **Python**, not assembled in the template with `|add:`, and reaches the template as a prepared list.
5. Bootstrap's CSS/JS become **plain `<link>`/`<script>` CDN tags** in the two base templates — chosen for legibility in a demo over routing them through `register_assets` + `{% cv_css %}`/`{% cv_js %}`.
6. Where `{% cv_messages %}` is documented is the implementer's call; this plan places it at `docs/reference/messages.md` under the **Theming** nav section.

## Global Constraints

- Line length 120, double quotes, ruff (`task format`, `task check`); pre-commit runs `ruff-format`.
- Python ≥ 3.12; Django 4.2 / 5.2 / 6.0 (the nox matrix). No new runtime dependency may be introduced.
- Template tags carry the `cv_` prefix; theme templates resolve through `f"{crud_views_settings.theme_path}/..."`, never a hardcoded `crud_views/` path.
- Bootstrap is pinned to **5.3.3 on jsDelivr** with these exact values, copied verbatim (they are django-bootstrap5's current defaults from `django_bootstrap5/core.py`, so the rendered HTML is unchanged):
  - CSS `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css`, `integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"`
  - JS `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js`, `integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"`
  - both with `crossorigin="anonymous"`, matching the Font-Awesome line already in both templates.
- `DEFAULT_ICONS.keys() == BOOTSTRAP_ICONS.keys()` is asserted by the existing `test_bootstrap_preset_covers_exactly_default_names`: every new icon name goes in **both** dicts.
- No new msgid: `msgid "Close"` already exists in `src/crud_views/locale/de/LC_MESSAGES/django.po` (`msgstr "Schließen"`), so `test_no_empty_or_fuzzy_msgstr` and `test_mo_files_load` stay green with no catalog work. Do not run `task msg-make` as part of this change.
- One commit per task. Every task that changes behaviour adds its own bullet under `## Unreleased` in `CHANGELOG.md`.
- A new reference page must be listed in `docs/reference/.pages`.
- Tests: `pytest tests -n auto` from the repo root; the example project has its own suite (`cd examples/bootstrap5 && pytest`).

## Review Focus

Input classes the spec implies that need a test, each assigned to the task that owns the code:

1. **`messages` absent from the template context** (host without the context processor, or a bare `Template(...).render(Context({}))`) → renders nothing, raises nothing. *(Task 2)*
2. **A message with no `.level`** (a plain string pushed into the context) → falls back to `alert-info` instead of raising; this is django-bootstrap5's documented "defaults to `info`" behaviour. *(Task 2)*
3. **An unknown or custom level number** (e.g. a project-defined level `50`) → `alert-info`, never `alert-None`. *(Task 2)*
4. **`extra_tags` on a message** → appended as extra CSS classes, as django-bootstrap5 did (`extra_classes=message.extra_tags`); dropping them silently restyles hosts' alerts. *(Task 2)*
5. **Markup in the message text** → crud_views' own messages are `SafeString` (`render_snippet` returns `mark_safe(result.strip())`) and must not be escaped, while a plain unsafe string must stay escaped. *(Task 2)*

## File Structure

| File | Responsibility |
|---|---|
| `src/crud_views/lib/messages.py` *(new)* | level → alert class / icon name maps, and `message_alerts()` turning a queue into render-ready dicts. Unit-testable without a template context. |
| `src/crud_views/templatetags/crud_views.py` | adds the thin `cv_messages` inclusion tag (two lines, like `cv_breadcrumb`). |
| `src/crud_views/templates/crud_views/tags/messages.html` *(new)* | the Bootstrap 5 alert markup; the override point for a downstream theme. |
| `src/crud_views/lib/icons.py` | five new names in `DEFAULT_ICONS` and `BOOTSTRAP_ICONS`. |
| `tests/test1/test_no_django_bootstrap5.py` *(new)* | packaging/host guard: no `django_bootstrap5` reference survives. |
| `examples/bootstrap5/project/templates/project/base.html`, `tests/test1/app/templates/app/base.html` | the two host base templates: CDN tags + `{% cv_messages %}`. |
| `docs/reference/messages.md` *(new)*, `docs/reference/.pages`, `docs/reference/icons.md`, `docs/getting_started/tutorial-1-setup.md` | docs. |

---

### Task 1: Message-level icons in the registry

**Files:**
- Modify: `src/crud_views/lib/icons.py:14-41` (`DEFAULT_ICONS`), `src/crud_views/lib/icons.py:43-76` (`BOOTSTRAP_ICONS`)
- Modify: `docs/reference/icons.md:48-67` (icon table)
- Test: `tests/test1/test_icons_registry.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the semantic icon names `message-success`, `message-info`, `message-warning`, `message-error`, `message-debug`, resolvable by `render_icon()` and `{% cv_icon %}`.

- [ ] **Step 1: Write the failing test**

In `tests/test1/test_icons_registry.py` (imports for `DEFAULT_ICONS`, `BOOTSTRAP_ICONS`, `render_icon` and `override_settings` are already in that file):

```python
MESSAGE_ICONS = {
    "message-success": ("fas:circle-check", "bi:check-circle-fill"),
    "message-info": ("fas:circle-info", "bi:info-circle-fill"),
    "message-warning": ("fas:triangle-exclamation", "bi:exclamation-triangle-fill"),
    "message-error": ("fas:circle-exclamation", "bi:exclamation-octagon-fill"),
    "message-debug": ("fas:bug", "bi:bug-fill"),
}


@pytest.mark.parametrize("name,fa,bi", [(name, *values) for name, values in MESSAGE_ICONS.items()])
def test_message_icon_defaults(name, fa, bi):
    assert DEFAULT_ICONS[name] == fa
    assert BOOTSTRAP_ICONS[name] == bi


def test_message_icon_renders_font_awesome_by_default():
    assert render_icon("message-success") == '<i class="fa-solid fa-circle-check" aria-hidden="true"></i>'


def test_message_icon_can_be_switched_off():
    with override_settings(CRUD_VIEWS_ICONS={"message-info": ""}):
        assert render_icon("message-info") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test1/test_icons_registry.py -k message -v`
Expected: FAIL with `KeyError: 'message-success'`

- [ ] **Step 3: Add the five entries to both dicts in `src/crud_views/lib/icons.py`**

Exact values as in the test table: `DEFAULT_ICONS` gets the `fas:` values, `BOOTSTRAP_ICONS` the bare names (`check-circle-fill`, `info-circle-fill`, `exclamation-triangle-fill`, `exclamation-octagon-fill`, `bug-fill`) in its comprehension source dict. Keep each dict's existing ordering style — append the five at the end of the literal.

- [ ] **Step 4: Run the whole icons suite to verify it passes**

Run: `pytest tests/test1/test_icons_registry.py -v`
Expected: PASS, including the pre-existing `test_bootstrap_preset_covers_exactly_default_names` and `test_defaults_are_font_awesome_only`

- [ ] **Step 5: Document the five names**

Append to the table in `docs/reference/icons.md`, matching the existing row style:

```markdown
| `message-success` / `message-info` | `fas:circle-check` / `fas:circle-info` | [flash messages](messages.md) |
| `message-warning` / `message-error` | `fas:triangle-exclamation` / `fas:circle-exclamation` | [flash messages](messages.md) |
| `message-debug` | `fas:bug` | [flash messages](messages.md) |
```

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/icons.py docs/reference/icons.md tests/test1/test_icons_registry.py
git commit -m "feat(icons): message-level semantic icons (#221)"
```

---

### Task 2: `{% cv_messages %}` tag, helper and theme template

**Files:**
- Create: `src/crud_views/lib/messages.py`
- Modify: `src/crud_views/templatetags/crud_views.py` (add the tag next to `cv_breadcrumb`, around line 306)
- Create: `src/crud_views/templates/crud_views/tags/messages.html`
- Create: `docs/reference/messages.md`
- Modify: `docs/reference/.pages` (Theming section), `CHANGELOG.md`
- Test: `tests/test1/test_messages.py`

**Interfaces:**
- Consumes: the icon names from Task 1; `crud_views_settings.theme_path`; `{% cv_icon %}` (a `simple_tag`, signature `cv_icon(value, css="")`).
- Produces:

```python
# src/crud_views/lib/messages.py
ALERT_CLASSES: dict[int, str]   # messages.constants level -> Bootstrap contextual class
ICON_NAMES: dict[int, str]      # messages.constants level -> semantic icon name

def message_alerts(messages: Iterable[object] | None) -> list[dict]
    # one dict per message: {"message": object, "css_class": str, "icon_name": str, "extra_tags": str}
```

and the tag `{% cv_messages %}`, rendering `f"{crud_views_settings.theme_path}/tags/messages.html"` with the single context key `cv_message_alerts`.

- [ ] **Step 1: Write the failing unit tests for `message_alerts`**

Test functions are appended to `tests/test1/test_messages.py`, but every `import` shown in this task goes at the **top** of that file beside its existing imports: ruff selects `E`, and a mid-file import fails `E402`, which `--fix` will not repair.

```python
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message

from crud_views.lib.messages import message_alerts


@pytest.mark.parametrize(
    "level,css_class,icon_name",
    [
        (constants.DEBUG, "secondary", "message-debug"),
        (constants.INFO, "info", "message-info"),
        (constants.SUCCESS, "success", "message-success"),
        (constants.WARNING, "warning", "message-warning"),
        (constants.ERROR, "danger", "message-error"),
    ],
)
def test_message_alerts_maps_every_level(level, css_class, icon_name):
    (alert,) = message_alerts([Message(level, "hello")])
    assert alert["message"] == "hello"
    assert alert["css_class"] == css_class
    assert alert["icon_name"] == icon_name
    assert alert["extra_tags"] == ""


def test_message_alerts_keeps_extra_tags():
    (alert,) = message_alerts([Message(constants.INFO, "hello", extra_tags="mb-0 shadow")])
    assert alert["extra_tags"] == "mb-0 shadow"


def test_message_alerts_falls_back_to_info_for_unknown_level():
    (alert,) = message_alerts([Message(50, "hello")])
    assert alert["css_class"] == "info"
    assert alert["icon_name"] == "message-info"


def test_message_alerts_falls_back_to_info_without_a_level():
    (alert,) = message_alerts(["a plain string"])
    assert alert["message"] == "a plain string"
    assert alert["css_class"] == "info"


@pytest.mark.parametrize("messages", [None, []])
def test_message_alerts_without_messages(messages):
    assert message_alerts(messages) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test1/test_messages.py -k message_alerts -v`
Expected: FAIL at collection with `ModuleNotFoundError: No module named 'crud_views.lib.messages'`

- [ ] **Step 3: Implement `message_alerts()` in `src/crud_views/lib/messages.py`**

`ALERT_CLASSES` maps `DEBUG → "secondary"`, `INFO → "info"`, `SUCCESS → "success"`, `WARNING → "warning"`, `ERROR → "danger"`; `ICON_NAMES` maps the same five levels to the Task 1 names. `message_alerts()` iterates the queue once (iterating is what consumes it, as today), reads `level`, `message` and `extra_tags` with `getattr` defaults so a non-`Message` object cannot raise, and falls back to the `INFO` entry for a missing or unknown level. Take the **raw `message` attribute**, not `str(message)`: that is what preserves a `SafeString` body, and it is what django-bootstrap5's template does (`message.message|default:""`). `extra_tags` becomes `""` when absent or `None`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test1/test_messages.py -k message_alerts -v`
Expected: PASS

- [ ] **Step 5: Write the failing render tests for the tag**

Append to `tests/test1/test_messages.py`:

```python
from django.template import Context, Template
from django.utils.safestring import mark_safe


def _render(messages):
    return Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))


def test_cv_messages_renders_a_dismissible_alert():
    html = _render([Message(constants.SUCCESS, "Saved")])
    assert 'class="alert alert-success alert-dismissible fade show"' in html
    assert 'role="alert"' in html
    assert '<i class="fa-solid fa-circle-check' in html
    assert 'data-bs-dismiss="alert"' in html
    assert 'class="btn-close"' in html
    assert "Saved" in html


def test_cv_messages_appends_extra_tags_to_the_class_list():
    html = _render([Message(constants.INFO, "Note", extra_tags="mb-0")])
    assert 'class="alert alert-info alert-dismissible fade show mb-0"' in html


def test_cv_messages_keeps_safe_markup_unescaped():
    html = _render([Message(constants.SUCCESS, mark_safe("Created <strong>Penguin</strong>"))])
    assert "Created <strong>Penguin</strong>" in html


def test_cv_messages_escapes_unsafe_markup():
    html = _render([Message(constants.ERROR, "<script>x</script>")])
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_cv_messages_renders_nothing_without_messages_in_the_context():
    assert Template("{% load crud_views %}{% cv_messages %}").render(Context({})).strip() == ""
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/test1/test_messages.py -k cv_messages -v`
Expected: FAIL with `Invalid block tag ... 'cv_messages'`

- [ ] **Step 7: Implement the tag and the theme template**

In `src/crud_views/templatetags/crud_views.py`, beside `cv_breadcrumb`:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/messages.html", takes_context=True)
def cv_messages(context):
    return {"cv_message_alerts": message_alerts(context.get("messages"))}
```

`src/crud_views/templates/crud_views/tags/messages.html` — the markup is fixed by the spec, so it is given here in full:

```html
{% load crud_views i18n %}
{% for alert in cv_message_alerts %}
    <div class="alert alert-{{ alert.css_class }} alert-dismissible fade show{% if alert.extra_tags %} {{ alert.extra_tags }}{% endif %}"
         role="alert">
        {% cv_icon alert.icon_name "me-2" %}{{ alert.message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>
    </div>
{% endfor %}
```

- [ ] **Step 8: Run the file to verify it passes**

Run: `pytest tests/test1/test_messages.py -v`
Expected: PASS, the four pre-existing queue tests included

- [ ] **Step 9: Document the tag**

Create `docs/reference/messages.md` covering: what crud_views already emits (`cv_message_template` / `cv_message_template_code` on create, update, delete and the ordered up/down views, plus `ActionView` errors); `{% cv_messages %}` placed by the host in their own base template, next to `{% cv_breadcrumb %}`; the level → class table (`debug → secondary`, `info → info`, `success → success`, `warning → warning`, `error → danger`), noting `debug → secondary` as a deliberate difference from django-bootstrap5's `debug → warning`; the five icons and `CRUD_VIEWS_ICONS = {"message-info": ""}` to switch one off; that `extra_tags` land as extra CSS classes; that the X needs Bootstrap's JS bundle; and the override path `crud_views/tags/messages.html` for a theme app. Add `- messages.md` to the **Theming** group in `docs/reference/.pages`, after `templates.md`. Add a CHANGELOG bullet under `## Unreleased` → `### Added`.

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/lib/messages.py src/crud_views/templatetags/crud_views.py \
        src/crud_views/templates/crud_views/tags/messages.html \
        docs/reference/messages.md docs/reference/.pages CHANGELOG.md tests/test1/test_messages.py
git commit -m "feat(messages): themed {% cv_messages %} tag for django.contrib.messages (#221)"
```

---

### Task 3: Drop the dependency from the package and both host projects

**Files:**
- Modify: `pyproject.toml:33` (remove `"django-bootstrap5 (>=21.3)"`)
- Modify: `tests/test1/app/templates/app/base.html:2,14-16,44`
- Modify: `examples/bootstrap5/project/templates/project/base.html:2,16-18,53`
- Modify: `tests/test1/conftest.py:36` and `examples/bootstrap5/project/settings.py:25` (drop `"django_bootstrap5"` from both `INSTALLED_APPS`)
- Modify: `docs/getting_started/tutorial-1-setup.md:20-25,36`, `CHANGELOG.md`
- Create: `tests/test1/test_no_django_bootstrap5.py`
- Test: `tests/test1/test_messages.py` (one integration test)

**Interfaces:**
- Consumes: `{% cv_messages %}` from Task 2.
- Produces: nothing for later tasks.

Deliberate narrowing of #221's acceptance grep: the guard scans the shipped package, the packaging metadata and the two host projects, but **not** `docs/` or `CHANGELOG.md`. Both legitimately name the package in migration prose — Task 2's `docs/reference/messages.md` compares `debug → secondary` with django-bootstrap5's `debug → warning`, and Task 3 Step 7 adds a breaking-change bullet. A guard over `docs/` would contradict those. Removing the tutorial's mention is still required, and Step 7 covers it.

Note on the nox matrix: the `tests` session installs `.[polymorphic,workflow,ordered,test]` and the `examples` session `.[all,test,examples]`, so `django_bootstrap5` currently reaches both environments *only* through the core dependency. After `pyproject.toml` is edited, any surviving `{% load django_bootstrap5 %}` or `INSTALLED_APPS` entry fails in CI. Locally the dev venv keeps the package installed (removing a dependency does not uninstall it), so the guard test — not an `ImportError` — is what proves the removal.

- [ ] **Step 1: Write the failing guard test**

Create `tests/test1/test_no_django_bootstrap5.py`, modelled on `tests/test1/test_templates_no_crispy_pack_guard.py`:

```python
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
# The shipped package, the packaging metadata and both host projects that used the tags (#221).
ROOTS = [
    REPO / "src",
    REPO / "pyproject.toml",
    REPO / "tests" / "test1",
    REPO / "examples" / "bootstrap5",
]
# collectstatic output and caches live under examples/bootstrap5 on a developer machine.
SKIP = {"__pycache__", "staticfiles", "node_modules"}


def _scan(root: Path):
    for path in [root] if root.is_file() else root.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".html", ".toml"} or path == SELF:
            continue
        if any(part in SKIP or part.startswith(".") for part in path.relative_to(REPO).parts):
            continue
        yield path


FILES = sorted({path for root in ROOTS for path in _scan(root)})


def test_files_are_discovered():
    assert FILES, "no files found to scan"


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(REPO)))
def test_no_django_bootstrap5_reference(path):
    source = path.read_text(encoding="utf-8")
    for needle in ("django_bootstrap5", "django-bootstrap5"):
        assert needle not in source, (
            f"{path.relative_to(REPO)} references {needle}; crud_views renders messages with "
            "{% cv_messages %} and loads Bootstrap from a CDN tag (#221)"
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test1/test_no_django_bootstrap5.py -v`
Expected: FAIL for `pyproject.toml`, both `base.html` files, `tests/test1/conftest.py` and `examples/bootstrap5/project/settings.py`

- [ ] **Step 3: Remove the dependency and rewrite both base templates**

Drop the `pyproject.toml` dependency line and the `"django_bootstrap5"` entry from **both** `INSTALLED_APPS` — `tests/test1/conftest.py:36` and `examples/bootstrap5/project/settings.py:25`. Missing the conftest one is the one way this change passes locally and fails every CI `tests` session at `django.setup()` with `ModuleNotFoundError`. In both base templates: delete `{% load django_bootstrap5 %}`; replace the two `{% bootstrap_css %}` / `{% bootstrap_javascript %}` lines with the pinned CDN `<link>` and `<script>` from Global Constraints, keeping the surrounding `<!-- Bootstrap CSS and JS -->` comment and matching the attribute layout of the Font-Awesome `<link>` directly below; replace `{% bootstrap_messages %}` with `{% cv_messages %}` at the same position. Both templates already `{% load crud_views %}`.

- [ ] **Step 4: Run the guard to verify it passes**

Run: `pytest tests/test1/test_no_django_bootstrap5.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing end-to-end test**

Append to `tests/test1/test_messages.py`, reusing the file's existing `client_publisher_add_view` fixture:

```python
@pytest.mark.django_db
def test_create_message_renders_as_an_alert(client_publisher_add_view: Client, cv_publisher):
    response = client_publisher_add_view.post("/publisher/create/", {"name": "Penguin"}, follow=True)
    html = response.content.decode()
    assert 'class="alert alert-success alert-dismissible fade show"' in html
    assert 'data-bs-dismiss="alert"' in html
    assert "<strong>Penguin</strong>" in html
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test1/test_messages.py -v`
Expected: PASS — the message snippet's `<strong>` survives because `render_snippet` marks it safe and `message_alerts` passes the raw body through

- [ ] **Step 7: Fix the tutorial and the CHANGELOG**

In `docs/getting_started/tutorial-1-setup.md`: remove `"django_bootstrap5"` from the `INSTALLED_APPS` snippet (line 36) and correct the dependency paragraph (lines 20-25), which currently credits that app with "Bootstrap 5 widgets and pagination" — widgets come from crispy-forms with `crispy-bootstrap5`, pagination from django-tables2 via `crud_views/table/bootstrap5.html`. Say that the tutorial loads Bootstrap itself from a CDN in its base template. Add a CHANGELOG bullet under `## Unreleased` → `### Breaking`: `django-bootstrap5` is no longer a dependency; a project that used `{% bootstrap_css %}`, `{% bootstrap_javascript %}` or `{% bootstrap_messages %}` must install it itself, and should prefer `{% cv_messages %}`.

- [ ] **Step 8: Run both suites**

Run: `pytest tests -n auto`
Expected: PASS (the `test_action_menus_golden.py` goldens extract individual action containers with lxml and are unaffected by base-template chrome)
Run: `cd examples/bootstrap5 && pytest`
Expected: PASS — `test_i18n.py::test_demo_pages_render_german` and `test_demo_chrome_renders_german` render the rewritten base template

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml tests/test1/app/templates/app/base.html \
        examples/bootstrap5/project/templates/project/base.html examples/bootstrap5/project/settings.py \
        docs/getting_started/tutorial-1-setup.md CHANGELOG.md \
        tests/test1/test_no_django_bootstrap5.py tests/test1/test_messages.py
git commit -m "chore(deps)!: drop django-bootstrap5 (#221)"
```

---

### Task 4: Acceptance verification

**Files:**
- Create: `superpowers/notes/2026-10-21-drop-django-bootstrap5-acceptance.md`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: the acceptance record the PR links.

- [ ] **Step 1: Confirm the dependency is gone from the built wheel**

Run: `task build && python -c "import glob, zipfile; w = sorted(glob.glob('dist/*.whl'))[-1]; m = [n for n in zipfile.ZipFile(w).namelist() if n.endswith('METADATA')][0]; print('\n'.join(l for l in zipfile.ZipFile(w).read(m).decode().splitlines() if l.startswith('Requires-Dist')))"`
Expected: `Requires-Dist` lines include `crispy-bootstrap5` and `django-crispy-forms`, and **no** `django-bootstrap5`

- [ ] **Step 2: Lint**

Run: `task check && task format`
Expected: no findings, no reformatting of the new files

- [ ] **Step 3: Confirm i18n is untouched**

Run: `pytest tests/test1/test_i18n.py -v`
Expected: PASS without any `.po`/`.mo` edit — `{% translate 'Close' %}` reuses the existing `msgid "Close"` → `"Schließen"`

- [ ] **Step 4: Full suite one more time, then write the acceptance note**

Run: `pytest tests -n auto`
Write `superpowers/notes/2026-10-21-drop-django-bootstrap5-acceptance.md`: each acceptance criterion from #221 with the command and its result, the two deliberate deviations (`debug → secondary` rather than django-bootstrap5's `warning`; `data-bs-dismiss` rather than a new `cv.adapters` entry, with the reason), and the note that the local dev venv still has `django_bootstrap5` installed so the guard test is the contract.

- [ ] **Step 5: Commit**

```bash
git add superpowers/notes/2026-10-21-drop-django-bootstrap5-acceptance.md
git commit -m "docs: acceptance note for #221"
```
