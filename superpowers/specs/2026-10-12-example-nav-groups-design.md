# Grouped navbar for the examples project — design

- Date: 2026-10-12
- Status: approved in brainstorming, spec under review
- Scope: `examples/bootstrap5` only — no package code changes

## Goal

The examples navbar (`project/templates/project/nav.html`) renders one flat link per entry in `FEATURES` — 13 links
today. With `navbar-expand-md` they wrap onto a second line at any width below roughly 1400px, and every new example
app makes it worse.

Group the features into four topic dropdowns so the navbar has four top-level items and never wraps. The home page
uses the same groups as section headings so navbar and home page stay consistent.

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Grouping | **Four topic dropdowns**: Basics / Forms / UI / Extensions. Grouping only the extension apps (the original idea) still leaves 10 top-level items, which wrap on laptop widths. |
| Name for the extension apps | **"Extensions"** — the docs and `CLAUDE.md` call `crud_views_workflow`, `crud_views_polymorphic`, `crud_views_guardian` and `crud_views_object_detail` extension packages. |
| Home page | **Grouped too**: one heading per group with the existing cards beneath. |
| Group titles translated? | **Yes** (`gettext_lazy`): they are page chrome like "Log In". Feature titles stay untranslated, as today — they name package features as in the docs. |

## Grouping

| Key | Title (en / de) | Features, in `FEATURES` order |
|---|---|---|
| `basics` | Basics / Grundlagen | Library, Nested, Resources |
| `forms` | Forms / Formulare | Formsets, Conditional |
| `ui` | UI / Oberfläche | Showcase, Breadcrumbs, Context Buttons, Action Menus |
| `extensions` | Extensions / Erweiterungen | Workflow, Polymorphic, Guardian, Object Detail |

## Design

### Data — `project/features.py`

- New frozen dataclass `FeatureGroup`:
  - `key: str` — referenced by `Feature.group`
  - `title: str` — `gettext_lazy` string
  - `icon: str` — font-awesome classes, shown on the home page heading and the navbar toggle
- New module-level `GROUPS: list[FeatureGroup]` in display order (table above). Icons:
  - basics: `fa-solid fa-cubes`
  - forms: `fa-solid fa-pen-to-square`
  - ui: `fa-solid fa-palette`
  - extensions: `fa-solid fa-puzzle-piece`
- New **required** field `Feature.group: str` (a `GROUPS` key). It goes directly after `app`, so it must be set on
  every entry and has no default.
- New function `feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]`:
  - returns one tuple per group, in `GROUPS` order
  - features within a group keep their `FEATURES` order
  - raises `ValueError` naming the feature's `app` and the bad key if any feature's `group` is not a `GROUPS` key, so
    a typo fails at the first render and in tests instead of silently dropping a feature
  - a group with no features is still returned with an empty list; the templates skip it, and a test asserts none
    is empty today
- `FEATURES` keeps its current order and remains the single registry; the seed command, doc-link tests and
  `_feature_for()` keep using it unchanged.

### Navbar — `project/templates/project/nav.html` + `example_tags.py`

- Replace the `get_features` simple tag with `get_feature_groups`. It uses `takes_context=True` and returns
  `{"groups": feature_groups(), "active_group": <key or None>}`. `active_group` is the `group` of
  `_feature_for(context["view"])` when the context has a view, else `None`. `get_features` has no other caller and is
  removed.
- Render one Bootstrap 5 dropdown per non-empty group inside the existing `<ul class="navbar-nav me-auto …">`:

  ```html
  <li class="nav-item dropdown">
      <a class="nav-link dropdown-toggle{% if group.key == active_group %} active{% endif %}" href="#"
         role="button" data-bs-toggle="dropdown" aria-expanded="false"
         {% if group.key == active_group %}aria-current="true"{% endif %}>
          <i class="{{ group.icon }}"></i> {{ group.title }}
      </a>
      <ul class="dropdown-menu">
          <li><a class="dropdown-item" href="{% url feature.url_name %}">
              <i class="{{ feature.icon }} fa-fw"></i> {{ feature.title }}
              {% if feature.badge %}<span class="badge text-bg-success ms-1">{{ feature.badge }}</span>{% endif %}
          </a></li>
          …
      </ul>
  </li>
  ```

- Brand, language selector, username and login/logout stay unchanged. `base.html` already loads the Bootstrap JS
  bundle (`{% bootstrap_javascript %}`), so dropdowns work without new assets. In the collapsed mobile menu the dropdowns
  expand inline, which is Bootstrap's native behaviour.

### Home page — `project/views.py` + `project/templates/project/home.html`

- `HomeView.get_context_data` sets `context["feature_groups"] = feature_groups()` instead of `features`.
- The template loops over groups. For each non-empty group it renders
  `<h2 class="h4 mt-4 mb-3"><i class="{{ group.icon }}"></i> {{ group.title }}</h2>`, followed by the existing
  `row row-cols-1 row-cols-md-3 g-3` card grid for that group's features. The card markup itself is unchanged.
- The jumbotron and the demo-users alert are unchanged.

### Translations — `examples/bootstrap5/locale/de`

- Add the four group titles to `django.po` (`Grundlagen`, `Formulare`, `Oberfläche`, `Erweiterungen`) via
  `task msg-make` / `task msg-comp` in `examples/bootstrap5` (`manage.py makemessages -l de` / `compilemessages`); commit both `.po` and `.mo`.
- The existing `test_no_empty_or_fuzzy_msgstr` guards against untranslated or fuzzy entries.

### Tests — `examples/bootstrap5/project/tests.py`

New `FeatureGroupsTest` / `NavTest` cases:

1. Every feature's `group` is a `GROUPS` key, and every group has at least one feature.
2. `feature_groups()` raises `ValueError` for a feature with an unknown group key (patch `FEATURES` with one bad
   entry).
3. The home page and a feature landing page render exactly four `dropdown-toggle` elements in the nav, and the nav
   still links every feature's URL.
4. The home page shows every group title as a heading; the existing `test_home_page_links_every_feature` keeps
   passing unchanged.
5. On a feature's landing page (logged in as a superuser), that feature's group toggle carries `active`, and no other
   toggle does. On the home page no toggle is active.
6. With `HTTP_ACCEPT_LANGUAGE="de"`, the home page shows `Grundlagen` and `Erweiterungen`.

Existing tests that iterate `FEATURES` are unaffected.

### Changelog

Under `## Unreleased` → `### Internal`: "Examples: the navbar groups the example apps into Basics / Forms / UI /
Extensions dropdowns, and the home page uses the same groups as headings, so the menu no longer wraps."

## Out of scope

- Package templates and the package's own navigation: nothing in `src/` changes.
- Changing the navbar breakpoint (`navbar-expand-md`) — four items fit comfortably at `md`.
- Documentation pages under `docs/`: they don't describe the example navbar.
