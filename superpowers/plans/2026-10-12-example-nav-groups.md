# Grouped Example Navbar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The examples navbar shows four topic dropdowns (Basics / Forms / UI / Extensions) instead of 13 flat links,
and the home page groups its cards under the same four headings.

**Architecture:** `project/features.py` gains a `FeatureGroup` dataclass, an ordered `GROUPS` list, a required
`Feature.group` key and a `feature_groups()` helper that buckets `FEATURES` by group. The navbar reads it through a
new `get_feature_groups` template tag (which also works out which group the current page belongs to), and the home
view passes the same list to its template. Group titles are translated, so they also go into the `de` catalog.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12–3.14, Bootstrap 5 (via django-bootstrap5, JS bundle already loaded),
Font Awesome 6, pytest + pytest-django (Django `TestCase` style in `project/tests.py`), GNU gettext.

**Spec:** `superpowers/specs/2026-10-12-example-nav-groups-design.md` — read it before starting any task.

## Global Constraints

- Scope: `examples/bootstrap5/` and `CHANGELOG.md` only. Nothing under `src/` changes.
- Branch: create `feature/example-nav-groups` from an up-to-date `main` before Task 1. Open a PR at the end; do
  **not** merge it unless the user explicitly asks for a merge.
- All commands below run from `examples/bootstrap5/` and use the repo venv: `../../.venv/bin/python`. Run the
  examples tests with `../../.venv/bin/python -m pytest …` (the directory's `pytest.ini` sets
  `DJANGO_SETTINGS_MODULE=project.settings`).
- Groups, in this order, with exactly these keys, English titles, German titles and icons:
  - `basics` — "Basics" / "Grundlagen" — `fa-solid fa-cubes`
  - `forms` — "Forms" / "Formulare" — `fa-solid fa-pen-to-square`
  - `ui` — "UI" / "Oberfläche" — `fa-solid fa-palette`
  - `extensions` — "Extensions" / "Erweiterungen" — `fa-solid fa-puzzle-piece`
- Membership (order within a group = `FEATURES` order; `FEATURES` itself is **not** reordered):
  - basics: `library`, `nested`, `resources`
  - forms: `formsets`, `conditional`
  - ui: `showcase`, `breadcrumbs`, `context_buttons`, `action_menus`
  - extensions: `workflow`, `polymorphic_demo`, `guardian_demo`, `object_detail`
- Group titles use `gettext_lazy`; feature titles stay untranslated (unchanged).
- Line length 120, double quotes; run `ruff format` and `ruff check` on touched Python files before each commit
  (`../../.venv/bin/ruff …` from `examples/bootstrap5/`, or `task format` / `task check` from the repo root).
- The page already contains other `dropdown-toggle` / `dropdown-menu` elements (the language selector, and action
  menus on some example pages). Tests must identify navbar groups by their `id="nav-group-<key>"`, never by counting
  Bootstrap classes.

## Review Focus

1. **Pages with no `view` in the template context** (anything rendered without a class-based view): the navbar
   must render all four dropdowns with none active, not crash. Pinned in Task 2
   (`test_tag_without_view_in_context`). The login page is a CBV outside any example app, which `_feature_for`
   maps to `None`; pinned in Task 2 (`test_home_and_login_have_no_active_group`).
2. **A misspelled `group` key on a future `Feature`**: must fail loudly with a `ValueError` naming the app and the
   bad key, not silently drop the app from the menu. Pinned in Task 1 (`test_unknown_group_raises`).
3. **A group that ends up with no features** (e.g. after moving an app): no empty dropdown in the navbar and no
   empty heading on the home page. Pinned in Task 2 (`test_empty_group_not_rendered_in_nav`) and Task 3
   (`test_empty_group_has_no_heading`).
4. **Non-landing pages of an example app** (create/detail/update pages, not just the list a menu item links to):
   their group must still be the active one. Pinned in Task 2 (`test_non_landing_page_marks_its_group_active`,
   using `/library/author/create/`).
5. **German visitors**: group titles appear in German and the catalog has no empty or fuzzy entries. Pinned in
   Task 3 (`test_group_titles_translated_de`) plus the existing `test_i18n.py::test_no_empty_or_fuzzy_msgstr`.

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `examples/bootstrap5/project/features.py` | modify | `FeatureGroup`, `GROUPS`, `Feature.group`, `feature_groups()`; `group=` on all 13 entries |
| `examples/bootstrap5/project/templatetags/example_tags.py` | modify | replace `get_features` with `get_feature_groups` |
| `examples/bootstrap5/project/templates/project/nav.html` | modify | one dropdown per group |
| `examples/bootstrap5/project/views.py` | modify | `HomeView` passes `feature_groups` |
| `examples/bootstrap5/project/templates/project/home.html` | modify | a heading plus card grid per group |
| `examples/bootstrap5/locale/de/LC_MESSAGES/django.po` / `.mo` | modify | German group titles |
| `examples/bootstrap5/project/tests.py` | modify | new test classes |
| `CHANGELOG.md` | modify | Internal entry |

---

### Task 1: Feature groups in the registry

**Files:**
- Modify: `examples/bootstrap5/project/features.py`
- Test: `examples/bootstrap5/project/tests.py` (append a class at the end)

**Interfaces:**
- Consumes: nothing.
- Produces (in `project.features`):
  - `FeatureGroup(key: str, title: str, icon: str)` — frozen dataclass
  - `GROUPS: list[FeatureGroup]` — display order
  - `Feature.group: str` — required field, placed directly after `app`
  - `feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]` — one tuple per `GROUPS` entry, in `GROUPS`
    order, possibly with an empty list; raises `ValueError` for an unknown key. It reads the module globals
    `FEATURES` and `GROUPS` **at call time** (tests patch them).

- [ ] **Step 1: Write the failing tests**

Append to `examples/bootstrap5/project/tests.py`:

```python
class FeatureGroupsTest(SimpleTestCase):
    def test_every_feature_has_a_known_group_and_no_group_is_empty(self):
        from project.features import GROUPS, feature_groups

        keys = [group.key for group in GROUPS]
        self.assertEqual(keys, ["basics", "forms", "ui", "extensions"])
        for feature in FEATURES:
            self.assertIn(feature.group, keys, feature.app)
        for group, features in feature_groups():
            self.assertTrue(features, f"group {group.key} is empty")

    def test_grouping_matches_spec(self):
        from project.features import feature_groups

        grouped = {group.key: [f.app for f in features] for group, features in feature_groups()}
        self.assertEqual(
            grouped,
            {
                "basics": ["library", "nested", "resources"],
                "forms": ["formsets", "conditional"],
                "ui": ["showcase", "breadcrumbs", "context_buttons", "action_menus"],
                "extensions": ["workflow", "polymorphic_demo", "guardian_demo", "object_detail"],
            },
        )

    def test_unknown_group_raises(self):
        import dataclasses
        from unittest import mock

        from project.features import feature_groups

        bad = dataclasses.replace(FEATURES[0], group="nope")
        with mock.patch("project.features.FEATURES", [*FEATURES, bad]):
            with self.assertRaisesRegex(ValueError, "'library'.*'nope'"):
                feature_groups()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../../.venv/bin/python -m pytest project/tests.py -k FeatureGroupsTest -v`
Expected: 3 FAILED with `ImportError: cannot import name 'GROUPS'` / `'feature_groups'` from `project.features`.

- [ ] **Step 3: Add `FeatureGroup`, `GROUPS` and `Feature.group`**

In `examples/bootstrap5/project/features.py`, insert this between the `DocRef` class and the `Feature` class:

```python
@dataclass(frozen=True)
class FeatureGroup:
    key: str  # referenced by Feature.group
    title: str  # navbar dropdown and home page heading; page chrome, so translated (unlike Feature.title)
    icon: str  # font-awesome classes


#: navbar dropdowns and home page sections, in display order
GROUPS: list[FeatureGroup] = [
    FeatureGroup(key="basics", title=_("Basics"), icon="fa-solid fa-cubes"),
    FeatureGroup(key="forms", title=_("Forms"), icon="fa-solid fa-pen-to-square"),
    FeatureGroup(key="ui", title=_("UI"), icon="fa-solid fa-palette"),
    FeatureGroup(key="extensions", title=_("Extensions"), icon="fa-solid fa-puzzle-piece"),
]
```

In `Feature`, add the field directly after `app`:

```python
    app: str  # python package name of the example app, e.g. "library"
    group: str  # FeatureGroup.key this app is listed under in the navbar and on the home page
```

Then add `group=...` directly after `app=...` in every `Feature(...)` entry of `FEATURES`:

| `app=` | add |
|---|---|
| `"library"` | `group="basics",` |
| `"nested"` | `group="basics",` |
| `"formsets"` | `group="forms",` |
| `"workflow"` | `group="extensions",` |
| `"polymorphic_demo"` | `group="extensions",` |
| `"guardian_demo"` | `group="extensions",` |
| `"resources"` | `group="basics",` |
| `"showcase"` | `group="ui",` |
| `"object_detail"` | `group="extensions",` |
| `"breadcrumbs"` | `group="ui",` |
| `"conditional"` | `group="forms",` |
| `"context_buttons"` | `group="ui",` |
| `"action_menus"` | `group="ui",` |

Example (the first entry):

```python
    Feature(
        app="library",
        group="basics",
        title="Library",
```

- [ ] **Step 4: Add `feature_groups()`**

Append at the end of `features.py`, after `FEATURES`:

```python
def feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]:
    """FEATURES bucketed by GROUPS: one (group, features) pair per group in GROUPS order, FEATURES order within.

    Raises ValueError for a feature naming an unknown group, so a typo fails loudly instead of hiding the app.
    """
    buckets: dict[str, list[Feature]] = {group.key: [] for group in GROUPS}
    for feature in FEATURES:
        if feature.group not in buckets:
            raise ValueError(f"Feature {feature.app!r} names unknown group {feature.group!r}")
        buckets[feature.group].append(feature)
    return [(group, buckets[group.key]) for group in GROUPS]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `../../.venv/bin/python -m pytest project/tests.py -k FeatureGroupsTest -v`
Expected: 3 passed.

Then the whole examples suite (nothing else may break; the nav still uses `get_features` at this point):
Run: `../../.venv/bin/python -m pytest -q`
Expected: all passed.

- [ ] **Step 6: Lint and commit**

```bash
../../.venv/bin/ruff format project/features.py project/tests.py
../../.venv/bin/ruff check project/features.py project/tests.py
git add project/features.py project/tests.py
git commit -m "feat(examples): group example apps into Basics/Forms/UI/Extensions"
```

---

### Task 2: Navbar dropdowns

**Files:**
- Modify: `examples/bootstrap5/project/templatetags/example_tags.py:13-17` (the `get_features` tag)
- Modify: `examples/bootstrap5/project/templates/project/nav.html:11-18` (the `<ul class="navbar-nav …">` block)
- Test: `examples/bootstrap5/project/tests.py` (append a class at the end)

**Interfaces:**
- Consumes: `feature_groups()`, `GROUPS`, `FeatureGroup`, `Feature.group` from Task 1; the existing
  `_feature_for(view)` in `example_tags.py` (returns the `Feature` whose `app` is the view class's top-level module,
  or `None`).
- Produces: template tag `{% get_feature_groups as nav_groups %}` (in the `example_tags` library), returning
  `{"groups": list[tuple[FeatureGroup, list[Feature]]], "active_group": str | None}`. Navbar toggles carry
  `id="nav-group-<key>"` and, when active, exactly the class string `nav-link dropdown-toggle active`.

- [ ] **Step 1: Write the failing tests**

Add `import re` to the imports at the top of `examples/bootstrap5/project/tests.py` (keep imports sorted:
standard library first, so it goes above `from django.contrib.auth import get_user_model`), then append:

```python
NAV_GROUP_ID = re.compile(r'id="nav-group-([a-z]+)"')
ACTIVE_NAV_GROUP = re.compile(r'id="nav-group-([a-z]+)" class="nav-link dropdown-toggle active"')


def navbar_html(resp) -> str:
    """Only the top navbar: the breadcrumb is another <nav>, and some pages add their own dropdowns."""
    body = resp.content.decode()
    start = body.index('<nav class="navbar')
    return body[start : body.index("</nav>", start)]


class NavGroupsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="nav-admin", password="pw")

    def test_four_group_dropdowns_on_home_and_feature_page(self):
        self.assertEqual(NAV_GROUP_ID.findall(navbar_html(self.client.get(reverse("home")))), ["basics", "forms", "ui", "extensions"])
        self.client.force_login(self.admin)
        nav = navbar_html(self.client.get(reverse("author-list")))
        self.assertEqual(NAV_GROUP_ID.findall(nav), ["basics", "forms", "ui", "extensions"])

    def test_nav_links_every_feature(self):
        nav = navbar_html(self.client.get(reverse("home")))
        for feature in FEATURES:
            self.assertIn(f'href="{reverse(feature.url_name)}"', nav, feature.app)

    def test_feature_page_marks_its_group_active(self):
        self.client.force_login(self.admin)
        for feature in FEATURES:
            with self.subTest(app=feature.app):
                nav = navbar_html(self.client.get(reverse(feature.url_name)))
                self.assertEqual(ACTIVE_NAV_GROUP.findall(nav), [feature.group])
                self.assertEqual(nav.count('aria-current="true"'), 1)

    def test_non_landing_page_marks_its_group_active(self):
        self.client.force_login(self.admin)
        nav = navbar_html(self.client.get(reverse("author-create")))
        self.assertEqual(ACTIVE_NAV_GROUP.findall(nav), ["basics"])

    def test_home_and_login_have_no_active_group(self):
        for name in ("home", "login"):
            with self.subTest(page=name):
                nav = navbar_html(self.client.get(reverse(name)))
                self.assertEqual(ACTIVE_NAV_GROUP.findall(nav), [])
                self.assertNotIn('aria-current="true"', nav)

    def test_tag_without_view_in_context(self):
        from project.templatetags.example_tags import get_feature_groups

        result = get_feature_groups({})
        self.assertIsNone(result["active_group"])
        self.assertEqual([group.key for group, _ in result["groups"]], ["basics", "forms", "ui", "extensions"])

    def test_badges_shown_in_dropdown(self):
        nav = navbar_html(self.client.get(reverse("home")))
        with_badge = [f for f in FEATURES if f.badge]
        self.assertTrue(with_badge, "no feature has a badge any more; drop this test")
        self.assertEqual(nav.count('class="badge text-bg-success ms-1"'), len(with_badge))

    def test_empty_group_not_rendered_in_nav(self):
        from unittest import mock

        from project.features import GROUPS, FeatureGroup

        empty = FeatureGroup(key="empty", title="Empty", icon="fa-solid fa-ban")
        with mock.patch("project.features.GROUPS", [*GROUPS, empty]):
            nav = navbar_html(self.client.get(reverse("home")))
        self.assertNotIn('id="nav-group-empty"', nav)
        self.assertEqual(len(NAV_GROUP_ID.findall(nav)), 4)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../../.venv/bin/python -m pytest project/tests.py -k NavGroupsTest -v`
Expected: all FAILED. The rendering tests fail because no `id="nav-group-…"` exists yet (`[] != ['basics', …]`), and
`test_tag_without_view_in_context` fails with `ImportError: cannot import name 'get_feature_groups'`.
`test_home_and_login_have_no_active_group` may already pass (nothing is active yet); that is fine — it is a
regression guard.

- [ ] **Step 3: Replace the template tag**

In `examples/bootstrap5/project/templatetags/example_tags.py`, replace the whole `get_features` function:

```python
@register.simple_tag
def get_features():
    from project.features import FEATURES

    return FEATURES
```

with:

```python
@register.simple_tag(takes_context=True)
def get_feature_groups(context):
    """Navbar data: the feature groups, plus the key of the group the current page's view belongs to (or None)."""
    from project.features import feature_groups

    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    return {"groups": feature_groups(), "active_group": feature.group if feature else None}
```

(`_feature_for` is defined further down in the same module; that is fine, it is looked up at call time.)
Confirm nothing else uses the old tag: `grep -rn "get_features" .` must print nothing.

- [ ] **Step 4: Render one dropdown per group**

In `examples/bootstrap5/project/templates/project/nav.html`, replace:

```html
            <ul class="navbar-nav me-auto mb-2 mb-md-0">
                {% get_features as features %}
                {% for feature in features %}
                    <li class="nav-item">
                        <a class="nav-link" href="{% url feature.url_name %}">{{ feature.title }}</a>
                    </li>
                {% endfor %}
            </ul>
```

with (keep the `<a id=… class=…>` attributes in exactly this order and on one line — the tests match
`id="nav-group-<key>" class="nav-link dropdown-toggle active"`):

```html
            <ul class="navbar-nav me-auto mb-2 mb-md-0">
                {% get_feature_groups as nav_groups %}
                {% for group, features in nav_groups.groups %}
                    {% if features %}
                        <li class="nav-item dropdown">
                            <a id="nav-group-{{ group.key }}" class="nav-link dropdown-toggle{% if group.key == nav_groups.active_group %} active{% endif %}" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false"{% if group.key == nav_groups.active_group %} aria-current="true"{% endif %}>
                                <i class="{{ group.icon }}"></i> {{ group.title }}
                            </a>
                            <ul class="dropdown-menu" aria-labelledby="nav-group-{{ group.key }}">
                                {% for feature in features %}
                                    <li>
                                        <a class="dropdown-item" href="{% url feature.url_name %}">
                                            <i class="{{ feature.icon }} fa-fw"></i> {{ feature.title }}
                                            {% if feature.badge %}<span class="badge text-bg-success ms-1">{{ feature.badge }}</span>{% endif %}
                                        </a>
                                    </li>
                                {% endfor %}
                            </ul>
                        </li>
                    {% endif %}
                {% endfor %}
            </ul>
```

Leave the rest of `nav.html` (brand, toggler, language selector, username, login/logout) untouched.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `../../.venv/bin/python -m pytest project/tests.py -k NavGroupsTest -v`
Expected: 8 passed.

Then the whole examples suite:
Run: `../../.venv/bin/python -m pytest -q`
Expected: all passed (in particular `test_i18n.py::test_selector_present_in_nav` and
`test_nav_logout_translated_de`).

- [ ] **Step 6: Lint and commit**

```bash
../../.venv/bin/ruff format project/templatetags/example_tags.py project/tests.py
../../.venv/bin/ruff check project/templatetags/example_tags.py project/tests.py
git add project/templatetags/example_tags.py project/templates/project/nav.html project/tests.py
git commit -m "feat(examples): navbar shows one dropdown per feature group"
```

---

### Task 3: Grouped home page, German titles, changelog

**Files:**
- Modify: `examples/bootstrap5/project/views.py` (`HomeView`)
- Modify: `examples/bootstrap5/project/templates/project/home.html` (the card grid)
- Modify: `examples/bootstrap5/locale/de/LC_MESSAGES/django.po`, regenerate `django.mo`
- Modify: `CHANGELOG.md`
- Test: `examples/bootstrap5/project/tests.py` (append a class at the end)

**Interfaces:**
- Consumes: `feature_groups()`, `GROUPS`, `FeatureGroup` from Task 1.
- Produces: home page headings `<h2 id="group-<key>" …>` in `GROUPS` order, each followed by that group's cards;
  template context variable `feature_groups` (the `features` context variable is removed).

- [ ] **Step 1: Write the failing tests**

Append to `examples/bootstrap5/project/tests.py`:

```python
class HomeGroupsTest(TestCase):
    def test_home_has_a_heading_per_group_in_order(self):
        from project.features import GROUPS

        body = self.client.get(reverse("home")).content.decode()
        positions = [body.index(f'id="group-{group.key}"') for group in GROUPS]
        self.assertEqual(positions, sorted(positions))

    def test_cards_sit_under_their_group_heading(self):
        from project.features import feature_groups

        body = self.client.get(reverse("home")).content.decode()
        # everything after the first heading, cut into one chunk per group (the navbar sits before it)
        sections = dict(chunk.split('"', 1) for chunk in body.split('<h2 id="group-')[1:])
        for group, features in feature_groups():
            for feature in features:
                self.assertIn(f'href="{reverse(feature.url_name)}">Open</a>', sections[group.key], feature.app)

    def test_empty_group_has_no_heading(self):
        from unittest import mock

        from project.features import GROUPS, FeatureGroup

        empty = FeatureGroup(key="empty", title="Empty", icon="fa-solid fa-ban")
        with mock.patch("project.features.GROUPS", [*GROUPS, empty]):
            resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, 'id="group-empty"')

    def test_group_titles_translated_de(self):
        resp = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="de")
        for title in ("Grundlagen", "Formulare", "Oberfläche", "Erweiterungen"):
            self.assertContains(resp, title)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../../.venv/bin/python -m pytest project/tests.py -k HomeGroupsTest -v`
Expected: `test_home_has_a_heading_per_group_in_order` and `test_cards_sit_under_their_group_heading` FAIL
(`ValueError: substring not found` / `KeyError`), `test_group_titles_translated_de` FAILS (the navbar now shows
"Basics" etc., not German). `test_empty_group_has_no_heading` passes already — regression guard.

- [ ] **Step 3: Pass the groups from the home view**

In `examples/bootstrap5/project/views.py`, change the import and the context line:

```python
from project.features import feature_groups
```

```python
        context["feature_groups"] = feature_groups()
```

(`FEATURES` is no longer imported here; ruff will flag it if left behind.)

- [ ] **Step 4: Group the cards on the home page**

In `examples/bootstrap5/project/templates/project/home.html`, replace:

```html
    <div class="row row-cols-1 row-cols-md-3 g-3">
        {% for feature in features %}
```

…through the matching closing `{% endfor %}` and `</div>` of the card grid, with:

```html
    {% for group, features in feature_groups %}
        {% if features %}
            <h2 id="group-{{ group.key }}" class="h4 mt-4 mb-3"><i class="{{ group.icon }}"></i> {{ group.title }}</h2>
            <div class="row row-cols-1 row-cols-md-3 g-3">
                {% for feature in features %}
                    <div class="col">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="{{ feature.icon }}"></i> {{ feature.title }}
                                    {% if feature.badge %}
                                        <span class="badge text-bg-success ms-2">{{ feature.badge }}</span>
                                    {% endif %}
                                </h5>
                                <p class="card-text">{{ feature.description }}</p>
                            </div>
                            <div class="card-footer">
                                <a class="btn btn-sm btn-outline-primary" href="{% url feature.url_name %}">{% translate "Open" %}</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endfor %}
```

The card markup is unchanged apart from indentation. The jumbotron above and the demo-users alert below stay as
they are.

Run: `../../.venv/bin/python -m pytest project/tests.py -k HomeGroupsTest -v`
Expected: 3 passed, `test_group_titles_translated_de` still FAILS (no translations yet).

- [ ] **Step 5: Add the German titles**

Append these four entries to the end of `examples/bootstrap5/locale/de/LC_MESSAGES/django.po` (hand-added to keep
the diff small; a later `task msg-make` will just refresh the location comments):

```po

#: project/features.py
msgid "Basics"
msgstr "Grundlagen"

#: project/features.py
msgid "Forms"
msgstr "Formulare"

#: project/features.py
msgid "UI"
msgstr "Oberfläche"

#: project/features.py
msgid "Extensions"
msgstr "Erweiterungen"
```

First check none of the four msgids already exists: `grep -nE '^msgid "(Basics|Forms|UI|Extensions)"$'
locale/de/LC_MESSAGES/django.po` must print nothing (a duplicate msgid makes `msgfmt` fail). If one does exist,
set its `msgstr` instead of appending.

Compile:

```bash
../../.venv/bin/python manage.py compilemessages -l de
```

Expected: `processing file django.po in …/examples/bootstrap5/locale/de/LC_MESSAGES`, no errors.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `../../.venv/bin/python -m pytest project/tests.py -k HomeGroupsTest -v`
Expected: 4 passed.

Run: `../../.venv/bin/python -m pytest -q`
Expected: all passed, including `test_i18n.py::test_no_empty_or_fuzzy_msgstr`, `test_mo_files_load` and
`project/tests.py::HomePageTest::test_home_page_links_every_feature`.

- [ ] **Step 7: Changelog**

In `CHANGELOG.md`, under `## Unreleased` → `### Internal` (create the `### Internal` heading below the other
`## Unreleased` sections if it does not exist), add:

```markdown
- Examples: the navbar groups the example apps into Basics / Forms / UI / Extensions dropdowns, and the home page
  uses the same groups as headings, so the menu no longer wraps.
```

- [ ] **Step 8: Look at it in a browser**

```bash
../../.venv/bin/python manage.py migrate && ../../.venv/bin/python manage.py seed
../../.venv/bin/python manage.py runserver 8000
```

Check at a wide window (~1400px), at ~800px and at phone width (navbar collapsed):
- the navbar is one line with four dropdowns and none wraps; each opens and lists its apps with icons and the NEW
  badges;
- in the collapsed (hamburger) menu each dropdown still opens;
- on `/library/author/create/` the "Basics" toggle is highlighted;
- `/` shows four headings with their cards; switching the language selector to Deutsch shows the German titles.

Stop the server afterwards.

- [ ] **Step 9: Lint and commit**

```bash
../../.venv/bin/ruff format project/views.py project/tests.py
../../.venv/bin/ruff check project/views.py project/tests.py
git add project/views.py project/templates/project/home.html project/tests.py \
    locale/de/LC_MESSAGES/django.po locale/de/LC_MESSAGES/django.mo ../../CHANGELOG.md
git commit -m "feat(examples): group home page cards by feature group, German group titles"
```

- [ ] **Step 10: Push and open the PR**

```bash
git push -u origin feature/example-nav-groups
gh pr create --title "Examples: group the navbar into topic dropdowns" --body "Implements superpowers/specs/2026-10-12-example-nav-groups-design.md: the examples navbar shows Basics / Forms / UI / Extensions dropdowns instead of 13 wrapping links; the home page uses the same groups as headings; German group titles."
```

Wait for CI (if no runs start, close and reopen the PR), fix any ruff failures, and check the codecov check-runs via
the API (`gh pr checks` omits them). Do **not** merge unless the user asked for it.
