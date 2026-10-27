# Phase 5: Table pagination parity - Pattern Map

**Mapped:** 2026-10-27
**Files analyzed:** 14 proposed new/modified files (two new golden paths proposed below)
**Analogs found:** 13 / 14; compiled catalog is generated

## Scope and precedence

Read `CLAUDE.md` (also the target of `AGENTS.md`), 05-CONTEXT.md, its canonical references, and PAGE-01–04.
No project-local `.codex/skills/` or `.agents/skills/` directory exists. No RESEARCH.md was supplied: research and
Nyquist validation were explicitly skipped. This map uses current tracked source rather than the older codebase map.

D-01 settles the public name as **`pagination:hidden-label`**, superseding the older source-plan/PROJECT suggestion.
D-04/D-05 require previous/next blocks to encompass disabled states, with availability guards inside the blocks.
Do not introduce pagination algorithms, filtering/sorting changes, form-button work, or the Phase 7 surface freeze.

## File Classification

Documentation and golden files use the nearest allowed role: config and test respectively.

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/crud_views/templates/crud_views/table/bootstrap5.html` | component | request-response | `src/crud_views/templates/crud_views/snippets/pagination.html` | exact |
| `src/crud_views/templates/crud_views/snippets/pagination.html` | component | request-response | same file; existing class-table utility slots in `src/crud_views/lib/button_classes.py` | exact |
| `src/crud_views/lib/button_classes.py` | config | transform | same file, hidden-label defaults and default-key validation | exact |
| `tests/test1/test_table_template.py` | test | request-response | `tests/test1/test_card_order.py` pagination tests | exact |
| `tests/test1/test_card_order.py` | test | request-response | same file, pagination tests | exact |
| `tests/test1/test_button_classes.py` | test | transform | same file, utility-slot and key-count tests | exact |
| `tests/test1/golden/table_pagination/page1.html` (new proposed path) | test | file-I/O | `tests/test1/test_card_order.py` golden helper | exact |
| `tests/test1/golden/table_pagination/page2.html` (new proposed path) | test | file-I/O | `tests/test1/test_card_order.py` golden helper | exact |
| `docs/reference/buttons.md` | config | file-I/O | same file, class table and canonical key count | exact |
| `docs/reference/list_view.md` | config | file-I/O | same file, list-view reference | exact |
| `docs/migrating-1.0.md` | config | file-I/O | same file, card pagination DOM migration | exact |
| `CHANGELOG.md` | config | file-I/O | same file, unreleased Breaking section and card pagination entry | exact |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | config | transform | same file, existing pagination msgids | exact |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | config | batch | generated compiled catalog | none |

All existing analog paths above were verified with `git ls-files -- <path>`; each is tracked, including both current
card goldens. New table golden names are proposed output paths, not existing analogs. There are five primary code
analogs: the two pagination templates, class registry, card pagination tests, and class-table tests. Documentation
and translation assignments reuse their existing sections rather than searching unrelated files.

## Pattern Assignments

### Table template: component, request-response

**Accessibility analog:** `src/crud_views/templates/crud_views/snippets/pagination.html`, lines 1–16:

```django
{% load crud_views i18n %}
{% if is_paginated %}
<nav aria-label="{% translate 'pagination' %}" class="mt-3">
    <ul class="pagination justify-content-center">
        {% if page_obj.has_previous %}
            <li class="page-item">
                <a class="page-link" href="?{% if base_qs %}{{ base_qs }}&amp;{% endif %}page={{ page_obj.previous_page_number }}">{% cv_icon "page-previous" %}<span class="visually-hidden">{% translate "previous" %}</span></a>
            </li>
        {% else %}
            <li class="page-item disabled">
                <a class="page-link" aria-disabled="true">{% cv_icon "page-previous" %}<span class="visually-hidden">{% translate "previous" %}</span></a>
            </li>
        {% endif %}
        {% for num in paginator.page_range %}
            {% if num == page_obj.number %}
                <li class="page-item active" aria-current="page"><span class="page-link">{{ num }}</span></li>
```

Copy the icon/label ordering and current/disabled structure; substitute the shared class tag for the literal class.
The next arrow is the inverse ordering: hidden `next` label then `{% cv_icon "page-next" %}` (lines 23–30).
Disabled links have no `href` or focus-enabling `tabindex`; the active item contains a span, not a navigation link.

**Preserve table-specific flow:** `src/crud_views/templates/crud_views/table/bootstrap5.html`, lines 65–74:

```django
            {% if table.page.has_previous %}
                {% block pagination.previous %}
                <li class="previous page-item">
                    <a href="{% cv_querystring table.prefixed_page_field=table.page.previous_page_number %}" class="page-link">
                        <span aria-hidden="true">&laquo;</span>
                        {% trans 'previous' %}
                    </a>
                </li>
                {% endblock pagination.previous %}
            {% endif %}
```

Move the `has_previous` conditional **inside** `pagination.previous`; similarly move `has_next` inside
`pagination.next` (current lines 86–95). The blocks must render on disabled ends. Calling page-number methods
without checking availability can raise: this is a real override migration, not just a visual update.

**Preserve range/query behavior:** same table file, lines 75–84:

```django
            {% if table.page.has_previous or table.page.has_next %}
            {% block pagination.range %}
            {% for p in table.page|table_page_range:table.paginator %}
                <li class="page-item{% if table.page.number == p %} active{% endif %}">
                    <a class="page-link" {% if p != '...' %}href="{% cv_querystring table.prefixed_page_field=p %}"{% endif %}>
                        {{ p }}
                    </a>
                </li>
            {% endfor %}
            {% endblock pagination.range %}
```

Keep `table_page_range`, its ellipsis handling, `table.prefixed_page_field`, and `cv_querystring`. Add the active
item's accessible structure without turning ellipses into links. Retain every existing tables2 block, including
`pagination`, `pagination.previous`, `pagination.range`, and `pagination.next`; do not replace the table template
with an include of the card template. Both templates suppress pagination when only one page exists.

### Card template and registry: component/config, request-response/transform

**Defaults analog:** `src/crud_views/lib/button_classes.py`, lines 84–86:

```python
    "context:hidden-label": "visually-hidden",
    "list:hidden-label": "visually-hidden",
    "card:hidden-label": "visually-hidden",
```

Add `"pagination:hidden-label": "visually-hidden"` alongside the utility slots. Both templates should use:

```django
<span class="{% cv_button_class 'pagination' 'hidden-label' %}">
```

This is the proposed substitution, not an existing source excerpt. Replace only the card's four literal hidden-label
classes, preserving default rendered bytes and existing card goldens. No new button location, label-mode grammar,
template tag, icon name, or settings mechanism is needed.

**Merge analog:** `src/crud_views/lib/button_classes.py`, lines 127–133:

```python
def get_button_classes() -> dict[str, str | None]:
    global _button_classes_cache
    classes = _button_classes_cache
    if classes is None:
        classes = {**DEFAULT_BUTTON_CLASSES, **_THEME_BUTTON_CLASSES, **_settings_layer()}
        _button_classes_cache = classes
    return classes
```

Use the existing default → theme → project precedence and cache invalidation. Validation already accepts a key in
`DEFAULT_BUTTON_CLASSES` (lines 279–281), so no W362 grammar expansion is required for this utility key.

### Table tests and new table goldens: test, request-response/file-I/O

**Imports and fixtures analog:** `tests/test1/test_card_order.py`, lines 1–13:

```python
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.test.client import Client
from django.utils import translation
from lxml import html

from tests.lib.helper.user import user_viewset_permission
```

Copy only imports actually used. Its lines 23–39 show a logged-in client granted ViewSet `view` permission and three
Publisher records; lines 174–186 exercise a two-item card page. Existing table integration tests in
`tests/test1/test_table_template.py`, lines 20–30, already use `client_user_author_view`, `cv_author`, and
`@override_settings(DJANGO_TABLES2_TEMPLATE="crud_views/table/bootstrap5.html")`.
This override matters: the global test settings currently select `django_tables2/bootstrap5.html`, not our template.
For isolated template tests, a small deterministic django-tables2 table plus RequestFactory is also compatible with
the Context/Template style already in that table-test module. Prefer extending the existing test file over new
application fixtures unless request integration requires them.

**Golden analog:** `tests/test1/test_card_order.py`, lines 205–227:

```python
GOLDEN_DIR = Path(__file__).parent / "golden" / "card_pagination"


def _pagination(client, page: int):
    response = client.get(f"/publisher_order/card/?page={page}")
    (ul,) = html.fromstring(response.content).cssselect("nav > ul.pagination")
    nav = ul.getparent()
    return nav


def _check_golden(name: str, nav):
    markup = re.sub(r"\s+", " ", re.sub(r">\s+<", "><", html.tostring(nav, encoding="unicode"))).strip()
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup + "\n")
    assert markup == path.read_text().strip()


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
def test_card_pagination_golden(client_publisher_order, publishers, page):
    _check_golden(f"page{page}", _pagination(client_publisher_order, page))
```

Use a separate `golden/table_pagination/` directory. PAGE-01 requires the baseline golden and its deterministic
capture test to be **committed before any product markup changes**; then update those same goldens in implementation.
Capture the table pagination fragment under English with stable data/query ordering. Keep the existing two card
goldens unchanged. Baseline-first is a sequencing constraint on plans, not permission to change source during mapping.

**Accessibility analog:** same test file, lines 238–245:

```python
@pytest.mark.django_db
@pytest.mark.parametrize("page, end", [(1, 0), (2, -1)])
def test_card_pagination_disabled_end_is_aria_disabled_link(client_publisher_order, publishers, page, end):
    item = _pagination(client_publisher_order, page).cssselect(".page-item")[end]
    assert "disabled" in item.get("class")
    (link,) = item.cssselect("a.page-link")
    assert link.get("aria-disabled") == "true"
    assert link.get("href") is None
```

Extend coverage to absence of focusability, active-item span/no href, and parity across both pagination structures.
Reuse current-page assertions (lines 230–235), translation override (248–256), and registry override (259–264).
The existing translation expectations are `Seitennavigation`, `zurück`, `weiter`.

Additional table-specific regression assertions: prefixed page fields; preserved filters/sort/query values without
duplicate page fields; a long paginator with ellipses; no controls for zero/one page; and inherited overrides for
`pagination.previous` and `pagination.next` executing on both enabled and disabled ends. Override test templates must
guard page-number calls. Keep `pagination.range` override coverage. A local in-memory template loader can keep such
override fixtures out of application source; no existing exact disabled-end block override exists to copy.

### Card tests: test, request-response

Extend `tests/test1/test_card_order.py` using its existing `_pagination` and fixtures. Test one project setting such as
`CRUD_VIEWS_BUTTON_CLASSES={"pagination:hidden-label": "sr-only"}` against both card and table arrow labels.
Assert the substituted class actually appears and the default hidden class disappears from those labels.
Retain existing icon/translation/golden assertions. Default output must remain identical, so avoid regenerating card
goldens to absorb an accidental whitespace or structure change.

### Registry tests: test, transform

**Key-count analog:** `tests/test1/test_button_classes.py`, lines 86–98:

```python
def test_default_table_is_complete():
    assert len(EXPECTED_KEYS) == 70
    assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS
    assert get_button_class("context", "primary") == "btn btn-outline-primary btn-lg"
    assert get_button_class("card", "danger") == "btn btn-secondary btn-sm"
    assert get_button_class("menu", "item") == "dropdown-item"


def test_documented_default_key_count_matches_table():
    document = (Path(__file__).resolve().parents[2] / "docs/reference/buttons.md").read_text()
    counts = re.findall(r"The default table has (\d+) keys\b", document)
    assert len(counts) == 1, "Expected exactly one canonical default-key count sentence"
    assert int(counts[0]) == len(DEFAULT_BUTTON_CLASSES)
```

Add the new key to `EXPECTED_KEYS`, change 70 to 71, and add the pagination utility slot to the parametrization at
lines 101–117. The module's autouse fixture snapshots theme registrations and resets the cache (76–83); reuse it.
Theme/project precedence is already tested at lines 150–155, and the tag's attribute escaping at 164–169.

### Documentation: config, file-I/O

- `docs/reference/buttons.md`: add the shared key beside the hidden-label row (line 133); update the one canonical
  count sentence (line 144) from 70 to 71. Explain that the utility styles both pagination components and is separate
  from action-button hidden labels. Existing utility semantics are documented at lines 154–155.
- `docs/reference/list_view.md`: add table/card pagination guidance to the existing list-view reference: registry
  arrow names, translated hidden labels, shared class override, and the block contract with links to migration.
- `docs/migrating-1.0.md`: follow the existing **Card list pagination** migration at line 187 and removable arrow-only
  override guidance at line 255. Add table DOM changes and an explicit guarded override example. State that previous
  and next blocks now also run on unavailable directions, so old unconditional page-number calls must be guarded.
- `CHANGELOG.md`: add a table pagination DOM change under the existing unreleased `### Breaking` at line 7;
  the existing card pagination entry begins at line 36. Pair it with migration changes in the same implementation.

These are modifications to existing documentation, not new reference pages. Preserve the generic repository naming
rule: downstream-theme follow-up belongs in the phase acceptance note; do not add downstream project names to product
documentation. Phase 7 stability policy remains out of scope.

### Translation catalogs: config, transform/batch

**Reuse existing catalog:** `src/crud_views/locale/de/LC_MESSAGES/django.po`, lines 277–290:

```po
#: templates/crud_views/snippets/pagination.html:3
msgid "pagination"
msgstr "Seitennavigation"
```

The same section already translates `previous` as `zurück` and `next` as `weiter`. Add/refesh table source references
through the project's message-extraction workflow; do not invent `Table navigation` or another table-specific msgid.
The tracked `.mo` catalog is generated from `.po`; refresh it if extraction/compilation changes its compiled content.
Source-reference-only changes may leave the compiled bytes unchanged. Translation tests must exercise rendered German
output using the existing `translation.override("de")` pattern.

## Shared Patterns

### Registry rendering and safe class lookup

Apply `cv_icon` and `cv_button_class` from the existing `crud_views` tag library in both components. Existing classes
and icons already support settings overrides; use these seams instead of direct settings reads or a new resolver.
No authentication change is needed; request tests retain existing permission-granted clients. Availability guards
handle page-number errors before they occur; no exception wrapper belongs in these templates.

### Django-tables2 query compatibility

Keep table links routed through the existing `cv_querystring` tag and the table's prefixed page field. The current
table tests already assert replacement and preservation, and the wrapper delegates to the installed django-tables2
version. Card pagination retains its `base_qs` convention; parity concerns accessibility and rendering contracts,
not replacing either component's pagination data flow.

### Verification and sequencing

1. Commit current table pagination baseline first; only then implement the DOM change and update table goldens.
2. Add semantic coverage for both components, shared class settings, icon settings, translations, prefixed queries,
   range ellipses, and inherited block overrides on both ends.
3. Keep existing card goldens unchanged and synchronize default-key test/documentation counts at 71.
4. Carry forward project gates: `pytest tests -n auto`,
   `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`, `mkdocs build --strict`, `ruff check`, and
   `ruff format --check`. Skipping research/Nyquist does not skip these implementation gates.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | config | batch | Binary generated from its tracked `.po`; compile rather than copying/editing an excerpt |

No existing pagination block override test covers disabled ends: write that regression around the preserved block
names and D-04/D-05 guards using the existing template test style. No RESEARCH.md fallback is needed for the small
template change.

## Metadata

**Analog search scope:** current tracked pagination templates, class registry, Django template tags, existing table
and card tests, fixture configuration, German locale, and canonical project/docs references.
**Primary code analogs extracted:** 5; documentation/catalog files use their existing sections.
**Tracked-source gate:** verified every existing file named in the classification table with `git ls-files`.
**Pattern extraction date:** 2026-10-27.
**Source edits:** none. This pattern map is the only file written.
