# Full i18n across all packages and the example app — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship correct message-catalog translations for all five `crud_views_*` packages and the example app in seven locales, with a browser-default language and a reusable language selector in the top nav.

**Architecture:** Mark user-facing strings with Django's `gettext`/`{% translate %}`, extract to `.po` and compile to `.mo` per package (Django auto-loads each app's `locale/`). A reusable `{% cv_language_selector %}` inclusion tag in `crud_views` renders a CSP-safe Bootstrap dropdown that POSTs to Django's `set_language`. The example app wires `LocaleMiddleware` (browser `Accept-Language` default) + the `i18n/` URL and ships its own catalogs.

**Tech Stack:** Django i18n (`gettext`, `makemessages`/`compilemessages`), GNU gettext toolchain, Bootstrap 5, go-task, pytest.

## Global Constraints

- **Locales (7):** `en` (base/source — msgids are English, **no `.po`**), `de` (human-authored, authoritative), `fr`, `es`, `pt`, `it`, `zh-hans`. Copy these codes verbatim.
- **Locale-directory nuance:** language code `zh-hans` ⇔ locale directory **`zh_Hans`** (underscore, capital H). `makemessages -l zh_Hans`; `LANGUAGES` entry `("zh-hans", _("Simplified Chinese"))`.
- **Never mark translations `#, fuzzy`.** `compilemessages` skips fuzzy entries, so they render as English. Author all `msgstr` as active. German stays human-authored; the five machine-authored locales get a header comment noting AI authorship pending native review.
- **Do not translate developer-facing strings** (`ValueError`/exception messages for developers, log messages, system-check messages, code identifiers like `cv_guardian_parent_permission`).
- **CSP-safe UI only:** no inline `<script>` / `on*` handlers — Bootstrap `data-bs-*` attributes only.
- **Line length 120, double quotes** (ruff). Run `ruff format` + `ruff check --fix` before every commit.
- **`.mo` files are committed** so packages work without a compile step after install.
- Package source lives under `src/`. Package tests live under `tests/test1/`. Example app lives under `examples/bootstrap5/` (its own `pytest.ini`, `DJANGO_SETTINGS_MODULE = project.settings`).

---

## File Structure

**Scaffolding / config**
- Modify `settings_i18n.py` — add all 5 packages to `INSTALLED_APPS`.
- Modify `taskfile.yaml` — replace `msg-make-crud_views`/`msg-comp-crud_views` with loop-all `msg-make`/`msg-comp`; keep vars `LOCALES`, `I18N_PACKAGES`.
- Modify `examples/bootstrap5/taskfile.yaml` — add `msg-make`/`msg-comp`.
- Create `src/{crud_views_polymorphic,crud_views_guardian,crud_views_object_detail}/locale/` (+ per-locale `.po`/`.mo`).
- Create `examples/bootstrap5/locale/` (+ per-locale `.po`/`.mo`).

**String marking**
- Modify `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html`.
- Modify `src/crud_views_polymorphic/lib/create_select.py`.
- Modify `src/crud_views_object_detail/apps.py` (+ optional `crud_views_polymorphic/apps.py`, `crud_views_guardian/apps.py`).
- Modify example templates/views (`project/templates/project/{base,nav}.html`, `project/views.py`, `project/settings.py`, `project/urls.py`, `project/templatetags/example_tags.py`).

**Reusable selector (crud_views core)**
- Create `src/crud_views/templates/crud_views/snippets/language_selector.html`.
- Modify `src/crud_views/templatetags/crud_views.py` — add `cv_language_selector` inclusion tag.

**Tests**
- Create `tests/test1/test_i18n.py` (package translations + catalog guard).
- Create `tests/test1/test_language_selector.py` (selector tag).
- Modify `tests/test1/project/urls.py` — add `i18n/` include (test support for the selector's `set_language` reverse).
- Create `examples/bootstrap5/test_i18n.py` (browser-default + selector switch).

**Docs**
- Rewrite `docs/development/i18n.md`.

---

## Task 1: Scaffolding — gettext, `settings_i18n`, taskfile pipeline, locale dirs

**Files:**
- System: install `gettext`.
- Modify: `settings_i18n.py`
- Modify: `taskfile.yaml:88-97` (the `msg-make-crud_views`/`msg-comp-crud_views` block) and `taskfile.yaml:3-4` (vars)
- Modify: `examples/bootstrap5/taskfile.yaml`
- Create (dirs): `src/crud_views_polymorphic/locale/`, `src/crud_views_guardian/locale/`, `src/crud_views_object_detail/locale/`, `examples/bootstrap5/locale/`

**Interfaces:**
- Produces: `task msg-make` (extract all packages × all locales), `task msg-comp` (compile all packages), `task examples:msg-make` / `task examples:msg-comp`. Vars `LOCALES="de fr es pt it zh_Hans"`, `I18N_PACKAGES="crud_views crud_views_workflow crud_views_polymorphic crud_views_guardian crud_views_object_detail"`.

- [ ] **Step 1: Install the gettext toolchain**

Run:
```bash
sudo apt-get update && sudo apt-get install -y gettext
```
Expected: installs; `msgfmt --version` and `xgettext --version` both print a version (GNU gettext 0.21).

- [ ] **Step 2: Verify the toolchain + add `polib` dev dep**

Run: `msgfmt --version && xgettext --version`
Expected: two version banners, exit 0. (Extraction/compilation cannot proceed without this.)

Add `polib` to the dev dependency group (the catalog-guard test parses `.po` with it). In `pyproject.toml`, add `"polib"` to the dev/test dependency group used by the test env (follow the existing group; e.g. `[dependency-groups] dev = [..., "polib"]`), then re-sync:
```bash
uv sync
python -c "import polib; print(polib.__version__)"
```
Expected: prints a version. (`test_no_empty_or_fuzzy_msgstr` uses `pytest.importorskip("polib")` as a guard, but it must actually be present so the check really runs.)

- [ ] **Step 3: Extend `settings_i18n.py` to all packages**

Set `INSTALLED_APPS` to:
```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "crud_views",
    "crud_views_workflow",
    "crud_views_polymorphic",
    "crud_views_guardian",
    "crud_views_object_detail",
]
```

- [ ] **Step 4: Create locale directories** (makemessages requires an existing `locale/` in each app dir)

Run:
```bash
mkdir -p src/crud_views_polymorphic/locale src/crud_views_guardian/locale \
         src/crud_views_object_detail/locale examples/bootstrap5/locale
```

- [ ] **Step 5: Add taskfile vars and replace the msg tasks**

In `taskfile.yaml`, under the existing `vars:` block add:
```yaml
vars:
  PYTHON: "3.12"
  LOCALES: "de fr es pt it zh_Hans"
  I18N_PACKAGES: "crud_views crud_views_workflow crud_views_polymorphic crud_views_guardian crud_views_object_detail"
```
Replace the `msg-make-crud_views` / `msg-comp-crud_views` tasks with:
```yaml
  msg-make:
    desc: Extract translatable strings for all packages and locales
    dir: src
    cmd: |
      for pkg in {{ .I18N_PACKAGES }}; do
        for loc in {{ .LOCALES }}; do
          (cd "$pkg" && PYTHONPATH=../.. python -m django makemessages -l "$loc" --settings=settings_i18n)
        done
      done

  msg-comp:
    desc: Compile all package message catalogs
    dir: src
    cmd: PYTHONPATH=.. python -m django compilemessages --settings=settings_i18n
```

- [ ] **Step 6: Add example-app msg tasks**

In `examples/bootstrap5/taskfile.yaml`, add:
```yaml
  msg-make:
    desc: Extract translatable strings for the example app
    cmds:
      - for: { var: LOCALES }
        cmd: uv run manage.py makemessages -l {{ .ITEM }}
    vars:
      LOCALES: "de fr es pt it zh_Hans"

  msg-comp:
    desc: Compile the example app message catalog
    cmds:
      - uv run manage.py compilemessages
```

- [ ] **Step 7: Verify extraction pipeline runs**

Run: `task msg-make`
Expected: exit 0; a `.po` now exists for every package × locale, e.g.:
```bash
ls src/crud_views_guardian/locale/de/LC_MESSAGES/django.po \
   src/crud_views_object_detail/locale/zh_Hans/LC_MESSAGES/django.po
```
both exist. (New-package `.po` files may currently have few/zero msgids — strings are marked in Task 2.)

- [ ] **Step 8: Commit**

```bash
ruff format . && ruff check --fix .
git add settings_i18n.py taskfile.yaml examples/bootstrap5/taskfile.yaml pyproject.toml src/*/locale examples/bootstrap5/locale
git commit -m "build(i18n): gettext pipeline, settings_i18n all packages, loop-all msg tasks (#88)"
```

---

## Task 2: Mark strings in guardian / polymorphic / object_detail

**Files:**
- Modify: `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html`
- Modify: `src/crud_views_polymorphic/lib/create_select.py:15`
- Modify: `src/crud_views_object_detail/apps.py:8`
- (Optional) Modify: `src/crud_views_polymorphic/apps.py`, `src/crud_views_guardian/apps.py`
- Test: `tests/test1/test_i18n.py` (extraction assertion)

**Interfaces:**
- Produces: msgids `"Guardian Configuration"`, `"Setting"`, `"Value"`, `"Permission Holders"`, `"Group"`, `"Permission"`, `"Model-level"`, `"Objects (guardian)"`, `"Users"`, `"No permission holders found."`, `"%(count)s object"/"%(count)s objects"` (guardian); `"Type"` (polymorphic); verbose_name `"Crud Views Object Detail"` (object_detail).

- [ ] **Step 1: Write the failing test** (msgids must be extractable)

In `tests/test1/test_i18n.py`:
```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _po(pkg: str, loc: str = "de") -> str:
    return (REPO / "src" / pkg / "locale" / loc / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")


def test_guardian_strings_extracted():
    po = _po("crud_views_guardian")
    for msgid in ["Guardian Configuration", "Permission Holders", "No permission holders found."]:
        assert f'msgid "{msgid}"' in po


def test_polymorphic_type_label_extracted():
    assert 'msgid "Type"' in _po("crud_views_polymorphic")


def test_object_detail_verbose_name_extracted():
    assert 'msgid "Crud Views Object Detail"' in _po("crud_views_object_detail")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tests && pytest test1/test_i18n.py -v`
Expected: FAIL — msgids absent (strings not yet marked / not extracted).

- [ ] **Step 3: Mark the guardian template**

Rewrite `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html` so the first line loads i18n and every prose string is wrapped. Full file:
```django
{% extends "crud_views/view_manage.html" %}
{% load i18n %}

{% block guardian_config %}
<h4>{% translate "Guardian Configuration" %}</h4>
<div class="alert alert-warning">
    <table class="table table-striped mb-0">
        <tr>
            <th scope="col">{% translate "Setting" %}</th>
            <th scope="col">{% translate "Value" %}</th>
        </tr>
        <tr>
            <td>cv_guardian_parent_permission</td>
            <td>{{ guardian_config.cv_guardian_parent_permission }}</td>
        </tr>
        <tr>
            <td>cv_guardian_parent_create_permission</td>
            <td>{{ guardian_config.cv_guardian_parent_create_permission }}</td>
        </tr>
        <tr>
            <td>cv_guardian_accept_global_perms</td>
            <td>{{ guardian_config.cv_guardian_accept_global_perms }}</td>
        </tr>
        <tr>
            <td>parent_viewset</td>
            <td>{{ guardian_config.parent_viewset }}</td>
        </tr>
    </table>
</div>
{% endblock guardian_config %}

{% block permission_holders %}
<h4>{% translate "Permission Holders" %}</h4>
{% if permission_holders %}
<table class="table table-striped">
    <tr>
        <th scope="col">{% translate "Group" %}</th>
        <th scope="col">{% translate "Permission" %}</th>
        <th scope="col">{% translate "Model-level" %}</th>
        <th scope="col">{% translate "Objects (guardian)" %}</th>
        {% if show_users %}<th scope="col">{% translate "Users" %}</th>{% endif %}
    </tr>
    {% for row in permission_holders %}
    <tr>
        <td>{{ row.group }}</td>
        <td>{{ row.permission }}</td>
        <td>{% if row.has_model_perm %}✓{% else %}—{% endif %}</td>
        <td>{% if row.object_count != None %}{% blocktranslate count count=row.object_count %}{{ count }} object{% plural %}{{ count }} objects{% endblocktranslate %}{% else %}—{% endif %}</td>
        {% if show_users %}<td>{{ row.users|join:", " }}</td>{% endif %}
    </tr>
    {% endfor %}
</table>
{% else %}
<p>{% translate "No permission holders found." %}</p>
{% endif %}
{% endblock permission_holders %}
```

- [ ] **Step 4: Mark the polymorphic form label**

In `src/crud_views_polymorphic/lib/create_select.py`, add the import near the top:
```python
from django.utils.translation import gettext_lazy as _
```
and change line 15:
```python
    polymorphic_ctype_id = forms.ChoiceField(label=_("Type"), choices=[])
```

- [ ] **Step 5: Mark the object_detail app verbose_name**

In `src/crud_views_object_detail/apps.py`, add `from django.utils.translation import gettext_lazy as _` and change:
```python
    verbose_name = _("Crud Views Object Detail")
```
(Optional consistency: add `verbose_name = _("Crud Views Polymorphic")` / `_("Crud Views Guardian")` to the other two `apps.py`.)

- [ ] **Step 6: Re-extract**

Run: `task msg-make`
Expected: exit 0; the new msgids now appear in the packages' `.po` files.

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_i18n.py -v`
Expected: PASS (all three extraction tests green).

- [ ] **Step 8: Commit**

```bash
ruff format . && ruff check --fix .
git add src/crud_views_guardian src/crud_views_polymorphic src/crud_views_object_detail src/*/locale tests/test1/test_i18n.py
git commit -m "i18n: mark user-facing strings in guardian/polymorphic/object_detail (#88)"
```

---

## Task 3: Reusable `{% cv_language_selector %}` component

**Files:**
- Create: `src/crud_views/templates/crud_views/snippets/language_selector.html`
- Modify: `src/crud_views/templatetags/crud_views.py`
- Modify: `tests/test1/project/urls.py` (add `i18n/` include so `set_language` reverses in tests)
- Test: `tests/test1/test_language_selector.py`

**Interfaces:**
- Consumes: Django `set_language` URL (name `set_language`), request in context.
- Produces: template tag `{% cv_language_selector %}` (inclusion tag, `takes_context=True`) rendering the partial with context `{"languages": settings.LANGUAGES, "current": get_language(), "next": request.get_full_path()}`. Renders nothing when fewer than 2 languages are configured.

- [ ] **Step 1: Write the failing test**

`tests/test1/test_language_selector.py`:
```python
import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import translation


def _render(langs):
    rf = RequestFactory()
    request = rf.get("/some/path/")
    tmpl = Template("{% load crud_views %}{% cv_language_selector %}")
    with translation.override("de"):
        with pytest.MonkeyPatch().context() as mp:
            from django.conf import settings

            mp.setattr(settings, "LANGUAGES", langs, raising=False)
            return tmpl.render(Context({"request": request}))


def test_selector_lists_languages_and_posts_to_set_language():
    html = _render([("en", "English"), ("de", "German"), ("zh-hans", "Simplified Chinese")])
    assert "set_language" in html or "/i18n/setlang" in html  # form action resolves
    assert "English" in html and "German" in html
    assert 'value="/some/path/"' in html  # next=current path
    assert 'value="zh-hans"' in html  # language code offered


def test_selector_hidden_for_single_language():
    html = _render([("en", "English")])
    assert html.strip() == ""
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tests && pytest test1/test_language_selector.py -v`
Expected: FAIL — tag `cv_language_selector` not registered (`TemplateSyntaxError: Invalid block tag`).

- [ ] **Step 3: Add the `i18n/` include to the test urlconf**

In `tests/test1/project/urls.py`, add to `urlpatterns`:
```python
from django.urls import include, path

urlpatterns += [path("i18n/", include("django.conf.urls.i18n"))]
```

- [ ] **Step 4: Create the selector partial**

`src/crud_views/templates/crud_views/snippets/language_selector.html`:
```django
{% load i18n %}
{% if languages|length > 1 %}
<div class="dropdown">
  <button class="btn btn-outline-secondary dropdown-toggle" type="button"
          data-bs-toggle="dropdown" aria-expanded="false">
    <i class="fa-solid fa-language"></i>
    {% for code, name in languages %}{% if code == current %}{{ name }}{% endif %}{% endfor %}
  </button>
  <ul class="dropdown-menu dropdown-menu-end">
    {% for code, name in languages %}
    <li>
      <form action="{% url 'set_language' %}" method="post" class="m-0">
        {% csrf_token %}
        <input type="hidden" name="next" value="{{ next }}">
        <input type="hidden" name="language" value="{{ code }}">
        <button type="submit" class="dropdown-item{% if code == current %} active{% endif %}">
          {{ name }}
        </button>
      </form>
    </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

- [ ] **Step 5: Register the inclusion tag**

In `src/crud_views/templatetags/crud_views.py`, add near the other imports:
```python
from django.conf import settings
from django.utils.translation import get_language
```
and add the tag (place beside the other `inclusion_tag` definitions):
```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/snippets/language_selector.html", takes_context=True)
def cv_language_selector(context):
    request = context.get("request")
    return {
        "languages": list(settings.LANGUAGES),
        "current": get_language(),
        "next": request.get_full_path() if request is not None else "/",
    }
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_language_selector.py -v`
Expected: PASS (both tests). If `LANGUAGES` monkeypatch does not propagate, set it via `django.test.override_settings` instead — the partial reads `settings.LANGUAGES` through the tag.

- [ ] **Step 7: Commit**

```bash
ruff format . && ruff check --fix .
git add src/crud_views/templates/crud_views/snippets/language_selector.html src/crud_views/templatetags/crud_views.py tests/test1/project/urls.py tests/test1/test_language_selector.py
git commit -m "feat(i18n): reusable cv_language_selector component (#88)"
```

---

## Task 4: Translate + compile the small package catalogs (guardian / polymorphic / object_detail)

**Files:**
- Modify: `src/crud_views_guardian/locale/{de,fr,es,pt,it,zh_Hans}/LC_MESSAGES/django.po` (+ `.mo`)
- Modify: `src/crud_views_polymorphic/locale/{...}/django.po` (+ `.mo`)
- Modify: `src/crud_views_object_detail/locale/{...}/django.po` (+ `.mo`)
- Test: `tests/test1/test_i18n.py` (render + catalog guard)

**Interfaces:**
- Consumes: msgids from Task 2.
- Produces: compiled `.mo` for all three packages × 6 locales with no empty/fuzzy `msgstr`.

- [ ] **Step 1: Write the failing render + guard tests**

Append to `tests/test1/test_i18n.py`:
```python
import gettext as gettext_mod
from django.utils import translation

SHIPPED = {
    "crud_views": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_workflow": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_polymorphic": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_guardian": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_object_detail": ["de", "fr", "es", "pt", "it", "zh_Hans"],
}


def _iter_po():
    for pkg, locs in SHIPPED.items():
        for loc in locs:
            yield pkg, loc, REPO / "src" / pkg / "locale" / loc / "LC_MESSAGES"


def test_no_empty_or_fuzzy_msgstr():
    polib = pytest.importorskip("polib")  # pip/uv add polib to the dev deps if missing
    for pkg, loc, d in _iter_po():
        po = polib.pofile(str(d / "django.po"))
        # polib .translated() correctly handles plurals (msgstr[0..n]) and multi-line strings:
        untranslated = [e.msgid for e in po if not e.obsolete and not e.translated()]
        assert not untranslated, f"{pkg}/{loc}: untranslated {untranslated}"
        fuzzy = [e.msgid for e in po if "fuzzy" in e.flags]
        assert not fuzzy, f"{pkg}/{loc}: fuzzy entries render as English: {fuzzy}"


def test_mo_files_load():
    for pkg, loc, d in _iter_po():
        mo = d / "django.mo"
        assert mo.exists(), f"missing {mo}"
        with mo.open("rb") as fh:
            gettext_mod.GNUTranslations(fh)  # raises if corrupt


def test_guardian_manage_renders_translated():
    from django.template import Context, Template

    tmpl = Template('{% load i18n %}{% translate "Permission Holders" %}')
    with translation.override("de"):
        assert tmpl.render(Context({})) != "Permission Holders"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tests && pytest test1/test_i18n.py -k "no_empty or mo_files or guardian_manage_renders" -v`
Expected: FAIL — empty msgstr present (translations not authored) and `.mo` not compiled.

- [ ] **Step 3: Author translations in each `.po`**

For every `src/crud_views_{guardian,polymorphic,object_detail}/locale/<loc>/LC_MESSAGES/django.po`, fill every empty `msgstr` with a real translation (non-fuzzy). Use the German values below as the authoritative anchor; author `fr/es/pt/it/zh-hans` to the same meaning. For the five machine locales, add this comment block above the header `msgid ""`:
```
# NOTE: fr/es/pt/it/zh-hans translations are machine-authored pending native review (see #88 follow-up).
```

**guardian — German (`de`) anchor:**
```
msgid "Guardian Configuration"   -> "Guardian-Konfiguration"
msgid "Setting"                  -> "Einstellung"
msgid "Value"                    -> "Wert"
msgid "Permission Holders"       -> "Berechtigungsinhaber"
msgid "Group"                    -> "Gruppe"
msgid "Permission"               -> "Berechtigung"
msgid "Model-level"              -> "Modellebene"
msgid "Objects (guardian)"       -> "Objekte (Guardian)"
msgid "Users"                    -> "Benutzer"
msgid "No permission holders found." -> "Keine Berechtigungsinhaber gefunden."
# plural block:
msgid "%(count)s object" / msgid_plural "%(count)s objects"
  msgstr[0] "%(count)s Objekt"
  msgstr[1] "%(count)s Objekte"
```
**polymorphic — `de`:** `msgid "Type" -> "Typ"`
**object_detail — `de`:** `msgid "Crud Views Object Detail" -> "Crud Views Objektdetail"`

> The plural entry in the `.po` uses `%(count)s` (Django rewrites the `{{ count }}` blocktranslate variable to a printf placeholder during extraction). Keep the placeholder verbatim in every locale. Chinese has one plural form — `makemessages -l zh_Hans` emits `nplurals=1`; provide only `msgstr[0]`.

- [ ] **Step 4: Compile**

Run: `task msg-comp`
Expected: exit 0; `.mo` files written next to each `.po`. If msgfmt reports an error, fix the offending `.po` (usually a stray placeholder mismatch) and re-run.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_i18n.py -v`
Expected: PASS. (`test_no_empty_or_fuzzy_msgstr` also covers crud_views/workflow, which are completed in Task 5 — if running Task 4 in isolation, temporarily restrict `SHIPPED` to the three packages, then restore in Task 5. Prefer running Task 5 before this assertion goes green for all.)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_guardian/locale src/crud_views_polymorphic/locale src/crud_views_object_detail/locale tests/test1/test_i18n.py
git commit -m "i18n: translations for guardian/polymorphic/object_detail, 6 locales (#88)"
```

---

## Task 5: New-locale translations for `crud_views` and `crud_views_workflow`

**Files:**
- Modify: `src/crud_views/locale/{fr,es,pt,it,zh_Hans}/LC_MESSAGES/django.po` (+ `.mo`) — `de` already complete.
- Modify: `src/crud_views_workflow/locale/{fr,es,pt,it,zh_Hans}/LC_MESSAGES/django.po` (+ `.mo`)
- Test: covered by `test_no_empty_or_fuzzy_msgstr` / `test_mo_files_load` (Task 4).

**Interfaces:**
- Consumes: existing English msgids extracted by `task msg-make`.
- Produces: complete `fr/es/pt/it/zh-hans` catalogs for both packages.

- [ ] **Step 1: Confirm the new-locale `.po` files exist with empty msgstr**

Run: `task msg-make`
Then: `grep -c 'msgstr ""' src/crud_views/locale/fr/LC_MESSAGES/django.po`
Expected: a non-zero count (empty entries to fill). `de` should already be fully translated (its count of empties is 1 — only the header).

- [ ] **Step 2: Run the guard test to verify it fails**

Run: `cd tests && pytest test1/test_i18n.py::test_no_empty_or_fuzzy_msgstr -v`
Expected: FAIL — `crud_views/fr` (etc.) has untranslated entries.

- [ ] **Step 3: Author `fr/es/pt/it/zh-hans` for both packages**

For each empty `msgstr` in the five new-locale `.po` files, author a translation of the English msgid, using the existing German `.po` (`src/crud_views/locale/de/...`) as the meaning reference. Add the machine-authorship NOTE comment (as in Task 4 Step 3) above each new-locale header. Keep every `%(...)s` / `{{ }}` placeholder and HTML fragment intact. Do **not** touch `de`.

- [ ] **Step 4: Compile**

Run: `task msg-comp`
Expected: exit 0; `.mo` regenerated for all locales of both packages.

- [ ] **Step 5: Run the full i18n suite to verify it passes**

Run: `cd tests && pytest test1/test_i18n.py -v`
Expected: PASS across all 5 packages × 6 locales (guard + mo-load + render).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/locale src/crud_views_workflow/locale
git commit -m "i18n: fr/es/pt/it/zh-hans catalogs for crud_views + workflow (#88)"
```

---

## Task 6: Example-app i18n infrastructure + string marking

**Files:**
- Modify: `examples/bootstrap5/project/settings.py`
- Modify: `examples/bootstrap5/project/urls.py`
- Modify: `examples/bootstrap5/project/templates/project/base.html`
- Modify: `examples/bootstrap5/project/templates/project/nav.html`
- Modify: `examples/bootstrap5/project/views.py` and `project/templatetags/example_tags.py` (mark visible feature titles / home strings)
- Test: `examples/bootstrap5/test_i18n.py`

**Interfaces:**
- Consumes: `{% cv_language_selector %}` (Task 3).
- Produces: `LocaleMiddleware`-backed browser default, `set_language` URL, translated nav, `<html lang>` from active language.

- [ ] **Step 1: Write the failing test**

`examples/bootstrap5/test_i18n.py`:
```python
import pytest
from django.test import Client


@pytest.mark.django_db
def test_browser_language_default_de():
    client = Client()
    resp = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_set_language_switches_and_persists():
    client = Client()
    resp = client.post("/i18n/setlang/", {"language": "de", "next": "/"}, follow=True)
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_selector_present_in_nav():
    resp = Client().get("/")
    body = resp.content.decode()
    assert 'name="language"' in body  # selector form field rendered
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd examples/bootstrap5 && uv run pytest test_i18n.py -v`
Expected: FAIL — no `LocaleMiddleware` (lang not `de`), no `/i18n/setlang/` route, no selector in nav.

- [ ] **Step 3: Wire settings**

In `examples/bootstrap5/project/settings.py`:
- Insert into `MIDDLEWARE`, immediately after `SessionMiddleware` and before `CommonMiddleware`:
  ```python
      "django.middleware.locale.LocaleMiddleware",
  ```
- Add the i18n context processor to `TEMPLATES[0]["OPTIONS"]["context_processors"]`:
  ```python
                  "django.template.context_processors.i18n",
  ```
- After `LANGUAGE_CODE = "en-us"` add:
  ```python
  from django.utils.translation import gettext_lazy as _

  LANGUAGES = [
      ("en", _("English")),
      ("de", _("German")),
      ("fr", _("French")),
      ("es", _("Spanish")),
      ("pt", _("Portuguese")),
      ("it", _("Italian")),
      ("zh-hans", _("Simplified Chinese")),
  ]
  LOCALE_PATHS = [BASE_DIR / "locale"]
  ```

- [ ] **Step 4: Wire the `set_language` URL**

In `examples/bootstrap5/project/urls.py`, add to `urlpatterns` (near the top group):
```python
    path("i18n/", include("django.conf.urls.i18n")),
```
(`include` and `path` are already imported.)

- [ ] **Step 5: Translate `base.html` `<html lang>`**

In `examples/bootstrap5/project/templates/project/base.html`, add after the existing `{% load %}` lines:
```django
{% load i18n %}
```
and replace `<html lang="en">` with:
```django
{% get_current_language as LANGUAGE_CODE %}
<html lang="{{ LANGUAGE_CODE }}">
```

- [ ] **Step 6: Add selector + translate nav**

In `examples/bootstrap5/project/templates/project/nav.html`, add `{% load i18n crud_views %}` at the top (keep `example_tags`), insert the selector before the auth block, and translate the auth strings:
```django
            <div class="me-3">{% cv_language_selector %}</div>
            {% if request.user.is_authenticated %}
                <span class="navbar-text me-3">{{ request.user.username }}</span>
                <form class="d-flex" action="{% url "logout" %}" method="post">
                    {% csrf_token %}
                    <button class="btn btn-outline-success" type="submit">{% translate "Log Out" %}</button>
                </form>
            {% else %}
                <a class="btn btn-outline-success" href="{% url "login" %}">{% translate "Log In" %}</a>
            {% endif %}
```

- [ ] **Step 7: Mark remaining visible example strings**

Grep for hardcoded prose in the example templates/views and wrap it:
```bash
cd examples/bootstrap5 && grep -rniE '>[A-Za-z].*<|"Log In"|"Log Out"|title *=' project --include='*.html' --include='*.py'
```
Wrap visible feature titles / page headings with `{% translate %}` (templates) or `_()` (Python, e.g. feature `title` strings in `example_tags.py`). Leave URLs, CSS classes, and identifiers untouched.

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest test_i18n.py -v`
Expected: PASS (browser-default `de`, set_language switch, selector present).

- [ ] **Step 9: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
ruff format . && ruff check --fix .
git add examples/bootstrap5/project examples/bootstrap5/test_i18n.py
git commit -m "feat(i18n): example-app infrastructure, selector, translated nav (#88)"
```

---

## Task 7: Example-app translation catalogs

**Files:**
- Modify: `examples/bootstrap5/locale/{de,fr,es,pt,it,zh_Hans}/LC_MESSAGES/django.po` (+ `.mo`)
- Test: `examples/bootstrap5/test_i18n.py` (extend to assert a translated nav string)

**Interfaces:**
- Consumes: example msgids marked in Task 6.
- Produces: compiled example catalogs, 6 locales, no empty/fuzzy entries.

- [ ] **Step 1: Extract**

Run: `cd examples/bootstrap5 && task -t taskfile.yaml msg-make` (or from repo root `task examples:msg-make`)
Expected: `examples/bootstrap5/locale/<loc>/LC_MESSAGES/django.po` populated with the marked strings (`Log In`, `Log Out`, feature titles, …).

- [ ] **Step 2: Write the failing assertion**

Add to `examples/bootstrap5/test_i18n.py`:
```python
@pytest.mark.django_db
def test_nav_logout_translated_de(client, django_user_model):
    user = django_user_model.objects.create_user("u", password="p")
    client.force_login(user)
    resp = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert "Abmelden" in resp.content.decode()  # "Log Out" -> German
```

- [ ] **Step 3: Run to verify it fails**

Run: `cd examples/bootstrap5 && uv run pytest test_i18n.py::test_nav_logout_translated_de -v`
Expected: FAIL — msgstr empty / not compiled, so English renders.

- [ ] **Step 4: Author + compile**

Fill every empty `msgstr` (non-fuzzy) in all 6 example locales — German anchors: `Log In -> Anmelden`, `Log Out -> Abmelden`, plus feature titles/home prose. Add the machine-authorship NOTE to fr/es/pt/it/zh-hans. Then:
```bash
cd examples/bootstrap5 && uv run manage.py compilemessages
```
Expected: exit 0.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest test_i18n.py -v`
Expected: PASS (incl. `Abmelden`).

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add examples/bootstrap5/locale examples/bootstrap5/test_i18n.py
git commit -m "i18n: example-app translation catalogs, 6 locales (#88)"
```

---

## Task 8: Documentation rewrite + issue closure

**Files:**
- Rewrite: `docs/development/i18n.md`

**Interfaces:**
- Consumes: the real infrastructure built in Tasks 1–7.

- [ ] **Step 1: Rewrite `docs/development/i18n.md`**

Replace the content so it describes the now-real setup:
- The five packages that ship catalogs and the seven locales (note `en` needs no `.po`; note `zh-hans` ⇔ `zh_Hans` dir).
- The gettext requirement.
- The `task msg-make` / `task msg-comp` (packages) and `task examples:msg-make` / `task examples:msg-comp` (example) workflow — remove the "no shortcut for workflow/example yet" notes and the `msg-make-crud_views`-only references.
- The example-app infrastructure (LocaleMiddleware, LANGUAGES, LOCALE_PATHS, i18n context processor, `i18n/` URL) — remove the "#88 not yet wired" caveat block.
- The reusable `{% cv_language_selector %}` component and the project requirement to add `path("i18n/", include("django.conf.urls.i18n"))`.
- A note that fr/es/pt/it/zh-hans are machine-authored pending native review.
- The "adding a new language" section updated to loop all packages.

- [ ] **Step 2: Verify no stale references remain**

Run:
```bash
grep -rn "msg-make-crud_views\|msg-comp-crud_views\|not yet wired\|does not yet\|no taskfile shortcut" docs/development/i18n.md
```
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add docs/development/i18n.md
git commit -m "docs(i18n): rewrite for full package + example-app coverage (#88)"
```

- [ ] **Step 4: Draft the native-review follow-up issue** (created at merge time)

Write the issue body to `superpowers/specs/2026-07-22-i18n-native-review-followup.md` (title: "i18n: native-speaker review of fr/es/pt/it/zh-hans catalogs"), listing the machine-authored locales and the files. Commit:
```bash
git add superpowers/specs/2026-07-22-i18n-native-review-followup.md
git commit -m "docs: draft native-review follow-up issue for machine-authored locales (#88)"
```

---

## Task 9: Full verification — build, wheel `.mo`, full suite, format

**Files:** none (verification only).

- [ ] **Step 1: Confirm `.mo` ship in the wheel**

Run:
```bash
uv build --wheel 2>/dev/null
python - <<'PY'
import zipfile, glob
w = sorted(glob.glob("dist/*.whl"))[-1]
mos = [n for n in zipfile.ZipFile(w).namelist() if n.endswith(".mo")]
print(f"{len(mos)} .mo in {w}")
for pkg in ["crud_views","crud_views_workflow","crud_views_polymorphic","crud_views_guardian","crud_views_object_detail"]:
    assert any(n.startswith(pkg+"/locale/") and n.endswith(".mo") for n in mos), f"no .mo for {pkg}"
print("OK: every package ships .mo")
PY
```
Expected: prints a count and `OK`. If a package's `.mo` is missing, add to `[tool.hatch.build.targets.wheel]` in `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel.force-include]
"src/crud_views/locale" = "crud_views/locale"
```
(one line per package), rebuild, re-run. Commit any `pyproject.toml` change.

- [ ] **Step 2: Run the full package test suite**

Run: `cd tests && pytest`
Expected: all pass (including `test_i18n.py`, `test_language_selector.py`).

- [ ] **Step 3: Run the example-app suite**

Run: `cd examples/bootstrap5 && uv run pytest`
Expected: all pass (incl. `test_i18n.py`, existing `test_docs_sync.py`).

- [ ] **Step 4: Lint/format clean**

Run: `ruff format --check . && ruff check .`
Expected: no changes / no errors.

- [ ] **Step 5: Full matrix (optional but recommended before PR)**

Run: `task test`
Expected: nox matrix (Py 3.12/3.13/3.14 × Django 4.2/5.2/6.0) green. `.mo` are committed, so no gettext needed in the matrix.

- [ ] **Step 6: Commit any verification fixes**

```bash
git add -A
git commit -m "chore(i18n): verify wheel .mo inclusion and full suite (#88)" || echo "nothing to commit"
```

---

## Self-Review notes

- **Spec coverage:** §1 audit → Task 2 (marking) + Tasks 4/5/7 (translations); §2 selector → Task 3; §3 example infra → Task 6; §4 settings_i18n → Task 1; §5 taskfile → Task 1; §6 packaging → Task 9 Step 1; §7 testing → tests in Tasks 2–7 + Task 9; §8 docs/#88 → Task 8. Browser-default → Task 6 (LocaleMiddleware) + test. Fuzzy caveat → Global Constraints + guard test (Task 4). All spec sections map to a task.
- **`zh-hans` vs `zh_Hans`** handled consistently: code in `LANGUAGES`, directory in `LOCALES`/paths.
- **Chicken-and-egg** for the catalog-guard test resolved by ordering (author before the assertion goes green for all packages; Task 4 Step 5 notes the temporary `SHIPPED` restriction if run in isolation).
