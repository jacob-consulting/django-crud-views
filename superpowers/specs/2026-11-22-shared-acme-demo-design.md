# Sharing the Acme Roasters demo and "Show code" across the theme repos: evaluation and design

**Date:** 2026-11-22
**Status:** evaluation complete, recommendation made. **No implementation authorized.** The maintainer decisions in
[section 11](#11-decisions-the-maintainer-has-to-make) are open; an implementation plan is written only after them.
**Scope:** the `example/` projects of django-crud-views-tabler, django-crud-views-coreui and
django-crud-views-adminlte. Nothing in `src/` of django-crud-views changes under the recommended option.
**Audience:** the maintainer, and an implementer who has not seen the discussion. Everything needed to take over is in
this file; section 13 says how to recompute every number in it.

Commits analysed (each repo's `main` on 2026-11-22):

| Short name | Repository | Commit |
|---|---|---|
| core | jacob-consulting/django-crud-views | `ee82aea` |
| ext | jacob-consulting/django-crud-views-extensions | `fd06c91` |
| T | jacob-consulting/django-crud-views-tabler | `307b9d5` |
| C | jacob-consulting/django-crud-views-coreui | `d67be0f` |
| A | jacob-consulting/django-crud-views-adminlte | `83cb1e8` |

## 1. The question

The three theme repos each carry the same demo project, Acme Roasters, in `example/`, and the same "Show code"
feature (a panel on every crud_views page that shows the app's source, and a `/theming/` page that lists the theme's
files). Evaluate ways to share (a) the app code and (b) the "Show code" feature.

Goals, as set by the maintainer:

- **G1** The projects must still be clonable and executable.
- **G2** They must stay easy to understand. A solution that is hard to explain is a no-go.
- **G3** A git submodule is acceptable if the bootstrap Taskfile handles it for users.

Added by this document, from the repos' own rules:

- **G4** One source of truth for whatever is shared: drift must be impossible or caught by a test.
- **G5** What exists today keeps working: T's sdist ships `example/`, T's nox matrix and CI install the built
  package, T's public demo deploys to Render.
- **G6** The project-wide Decision Rule in `CLAUDE.md` (developer maintainability is a hard constraint; prefer the
  simplest bounded solution; document unsupported cases).

During the evaluation the maintainer asked: *"what about adding a 4th repo based on bootstrap, just as the example
app in django-crud-views?"* That is option H5 in section 6, and it became the recommendation.

## 2. Summary

1. **The app code is already almost one code base.** Of 4,611 lines of app Python (T), 107 lines differ between the
   two most distant copies, and every one of them is a colour name, a CSS class, a mention of the theme's name, or
   drift. One copy (A's, the newest) passes the complete example test suites of T (280 tests) and C (263 tests)
   unchanged. Sharing the app Python needs no abstraction layer.
2. **Templates and tests are where the themes really differ.** No app template is identical in all three repos, and
   16% of the test lines differ between T and C. A plan that tries to share these in the first step would be the
   complex solution G2 rules out.
3. **The decision has three independent parts**, which the options below keep apart: the *seam* (what is shared,
   what stays theme-owned), the *home* (where the shared code lives) and the *transport* (how it reaches a theme
   repo).
4. **Recommendation:** a fourth repository holds the Acme apps and the "Show code" app as one installable package,
   together with a stock-Bootstrap 5 project that makes it runnable and testable on its own (the maintainer's idea).
   The theme repos consume that package the way they already consume django-crud-views and
   django-crud-views-extensions: a sibling checkout for local development, a pinned install in nox, CI and Render.
   A theme's `example/` shrinks to what a theme integration consists of: settings, templates, CSS.
5. **Honest costs:** a fourth skin to build and keep working; app sources no longer sit in the theme repo's working
   tree; until two themes have switched there is one copy more, not fewer; a theme-driven change to app code becomes
   a cross-repo change.

## 3. Findings

All paths are relative to a theme repo's root unless a repo is named. "T→C" means a diff from T's file to C's.

### 3.1 How a clone runs today

`task up` (Taskfile `install`: `uv sync --extra examples --extra test --extra dev`) only works **next to checkouts of
core and ext**, because `[tool.uv.sources]` in each `pyproject.toml` points at `../django-crud-views` and
`../django-crud-views-extensions` as editable path sources. The READMEs say so ("next to checkouts of ..."). A is
inconsistent: its sources point two levels up (`../../django-crud-views`), so in a flat directory of checkouts A's
`uv sync` fails.

nox, CI and Render cannot see sibling checkouts. They install core from GitHub: T `noxfile.py` (`CRUD_VIEWS = "... @
git+https://github.com/jacob-consulting/django-crud-views@main"`, always with `--no-sources`), T
`requirements/demo.txt` (the same line), A `noxfile.py` (a pinned commit, `PIN`).

So "clonable and executable" already means: three clones for local development, or a git install elsewhere. Any
option below is measured against this baseline, not against a self-contained repo.

Only T has `.github/workflows/`, `render.yaml` and `example/config/settings_demo.py`. C and A have none yet (C's
spec lists them as a follow-up). None of the three repos has a release tag, and T's `publish.yml` refuses to publish
until the core floor is `>=1.0.0rc1` (`scripts/check_release_floor.py`). **A restructuring now breaks no released
artefact.**

### 3.2 Size and overlap of `example/`

153 distinct tracked paths across the three repos (T 139, C 131, A 133). 76 are byte-identical in all three.

| Category | Paths | Identical in all three | Lines (T) | Changed T→C | Changed C→A | Changed T→A |
|---|---:|---:|---:|---:|---:|---:|
| App Python (models, views, forms, seed, urls, admin, ...) | 61 | 46 | 4,611 | 61 | 56 | 107 |
| App migrations | 16 | 14 | 1,182 | 19 | 19 | 38 |
| App templates | 12 | 0 | 640 | 259 | 104 | 299 |
| App static | 3 | 1 | 57 | 13 | 9 | 11 |
| Tests | 18 | 3 | 3,981 | 628 | 563 | 1,024 |
| `config/` (settings, urls, "Show code", icons, nav) | 22 | 12 | 1,018 | 198 | 315 | 437 |
| Project templates and static | 21 | 0 | 344 | 311 | 278 | 324 |
| **Total** | **153** | **76** | **11,833** | **1,489** | **1,344** | **2,240** |

"Changed" counts differing lines (a file missing on one side counts in full). Apps: `catalog`, `dashboard`,
`roastery`, `sales`, `shipping`, `showcase`.

### 3.3 Every difference in the app Python, and why it exists

Fifteen of the 61 files differ somewhere. This is the complete list.

| File | Difference | Kind |
|---|---|---|
| `catalog/seed.py` | 18 flavour-note colours: T `"red"`, `"lime"`, `"azure"`; C and A `"danger"`, `"success"`, `"info"` | colour vocabulary |
| `catalog/models.py` | `card_color`, `stock_color` values (same vocabulary split); help text "A Tabler colour name" / "A CoreUI theme colour name" / "A Bootstrap theme colour name" | colour vocabulary, theme name |
| `sales/models.py` | `AVATAR_COLORS`: T ten Tabler palette names, C and A six Bootstrap theme colours; `Order.steps` in T lacks the `done` key C and A have | colour vocabulary, **drift** |
| `showcase/models.py` | `stock_badge` values; docstring names the theme | colour vocabulary, theme name |
| `roastery/views.py`, `shipping/views.py`, `sales/views/addresses.py`, `sales/views/subscriptions.py` | badge markup: T `badge bg-{}-lt`, C and A `badge bg-{0}-subtle text-{0}-emphasis`, plus the colour names | CSS classes |
| `sales/views/customers.py` | the same badge split; avatar: T and C `avatar avatar-sm`, A `acme-avatar` (AdminLTE has no `.avatar`) | CSS classes |
| `sales/forms.py` | A replaces `<h3 class="card-title">` by `fs-6 fw-semibold mb-3` (AdminLTE floats `.card-title`, A's tracker A17) | CSS classes |
| `dashboard/views.py` | A adds three context values for its info boxes (5 lines, additive) | additive |
| `showcase/views.py` | layout objects imported from `django_tabler.crispy.layout` / `django_coreui.crispy.layout` / `crispy_bootstrap5.bootstrap5`; A sets `form-range` and `form-control-color` on widgets and uses `Field("sku", disabled=True)` for `UneditableField` | **real theme coupling** |
| `showcase/management/commands/seed_demo_showcase.py` | help text names the theme | theme name |
| `dashboard/templatetags/acme.py` | exists only in A (`initials`, `avatar_color`, `icon_class`; T and C get the first two from their shell's tag library) | A only |

Migrations: `catalog/migrations/0003_flavornote_color_help_text.py` exists in C and A, `0004_..._bootstrap.py` in A
only. Both exist **only because the help text names the theme**. Naming a CSS framework in a model's help text forced
schema migrations that differ per repo.

Two conclusions:

- Apart from `showcase/views.py`, nothing here is behaviour. It is vocabulary.
- The showcase app is different in kind. Its purpose is to exercise the theme's crispy pack ("It imports layout
  objects from `django_tabler`'s crispy pack, which this form showcase exists to exercise", T
  `templates/project/code_panel.html`).

### 3.4 Spike: one copy of the app Python runs under all three themes' test suites

Done in scratch copies (`git archive HEAD` of T, C and A next to symlinks to core and ext); the repos were not
touched. Python files of the six apps were copied from one theme's example into another's, without tests, without
`showcase/views.py` and without A's `dashboard/templatetags/`. Then `cd example && uv run pytest -n auto`.

| Example project | App Python from | Files replaced | Result |
|---|---|---:|---|
| T | T (baseline) | 0 | 280 passed, 122 subtests passed |
| T | C | 11 | 280 passed, 122 subtests passed |
| T | A | 14 | 280 passed, 122 subtests passed |
| C | C (baseline) | 0 | 263 passed, 307 subtests passed |
| C | A | 8 | 263 passed, 307 subtests passed |

What this proves: A's app Python is functionally a drop-in for T and C. What it does not prove: that the pages look
right. No test in T asserts a badge's colour class, which is itself a finding. A's own suite was not run (its path
sources need a different directory layout, see 3.1).

### 3.5 The Bootstrap 5.3 colour vocabulary works in all three CSS frameworks

C and A already use `bg-<colour>-subtle text-<colour>-emphasis` with `primary`, `success`, `info`, `warning`,
`danger`, `secondary`, `dark`. Tabler 1.6.1's stylesheet (`@tabler/core@1.6.1`, `dist/css/tabler.min.css`, fetched
from the npm registry) defines `.bg-success-subtle`, `.text-success-emphasis` and `.text-body-secondary`, and also
`.bg-success-lt`, `.bg-warning-lt`, `.bg-primary-lt`, `.bg-info-lt`, `.bg-danger-lt`, `.bg-secondary-lt`,
`.bg-dark-lt` next to its palette names (`.bg-green-lt`, `.bg-orange-lt`).

Rendered with that stylesheet (row 1: T today; row 2: semantic names with Tabler's `-lt`; row 3: the C and A markup):

![Badges under Tabler, light](2026-11-22-shared-acme-demo-badges-light.png)
![Badges under Tabler, dark](2026-11-22-shared-acme-demo-badges-dark.png)

Row 3 is readable in both modes. It is heavier than Tabler's own style and the palette shrinks from ten avatar
colours to six. Whether that is acceptable for the Tabler demo is a taste decision (D4 in section 11).

### 3.6 Templates

- Ten of the twelve app templates extend `cv_extends` or `crud_views/tags/card.html`, or are snippets. They do not
  depend on a shell. Only `dashboard/index.html` and `dashboard/user_list.html` extend the shell
  (`django_tabler/layouts/app.html`, `django_coreui/layouts/app.html`, A: `project/page.html`).
- T's markup is Tabler's own (`row-deck row-cards`, `subheader`, `card-actions`, `datagrid`). C and A are written in
  Bootstrap 5.3 utilities. Five of the twelve are byte-identical between C and A; five more differ in at most five
  lines (a comment, `border-top-3` against `border-3`, `avatar` against `acme-avatar`, the packing slip's print
  wrapper).
- Project templates (`templates/project/`, `templates/registration/`, the shell's `includes/`) and `acme.css` are
  the skin itself. None is identical anywhere.

### 3.7 Tests

- 3 of 18 test files are identical. Outside `dashboard/tests.py` the differences are small and of one kind: where
  the theme puts things. Examples: `html.index('class="page-header')` against `html.index("<main>")`;
  `cv-tabler-section-legend` against `cv-coreui-section-legend` against `class=""`.
- A already wraps this in a helper, `sales/tests/markup.py` (`header()`, `headings()`, `SUBTITLE`): a per-theme
  module that tells a test where the header is. That is a ready pattern for sharing tests later.
- `dashboard/tests.py` (T 932, C 1,113, A 1,191 lines) mixes app behaviour, "Show code" tests and the theme's own
  integration tests (`test_no_tabler_left`, `test_every_page_uses_coreui_classes_only`, layout switch, navigation).
  Coverage has drifted: C and A have page sweeps (`test_every_page_renders`) T lacks.

### 3.8 The "Show code" feature

Per repo: 361 (T), 361 (C), 380 (A) lines of Python, about 150 lines of templates, 38 lines of JavaScript.

| Piece | File | State |
|---|---|---|
| Collector (reads files, Pygments) | `config/showcode.py` | differs in constants only, except A |
| Views (`theming`, `code_panel`, `pygments_stylesheet`) | `config/views.py` | differs in constants and prose |
| Tags (`code_panel_url`, `code_panel`) | `config/templatetags/showcode.py` | identical |
| Routes | `config/urls.py` | identical |
| Panel shell | `templates/project/code_panel_shell.html` | one class differs |
| Panel content | `templates/project/code_panel.html` | icon tag, `data-*-toggle` prefix, header markup |
| Button and panel on crud pages | `templates/project/crud_views.html` | extends the theme's page; theme-owned |
| Theming page | `templates/project/theming.html` | theme markup and prose; theme-owned |
| Lazy loading | `static/acme/code-panel.js` | one event name differs |
| Tests | `dashboard/tests.py::ShowCodeTests` (16 tests in T) | in the 900 to 1,200 line file |

What actually varies between the themes:

1. Paths: `THEME_DIR` (`src/crud_views_<theme>`), `SHELL_DIR` (`src/django_<theme>`; A has no shell package and
   shows the installed `adminlte-django` version through `host_package()` instead).
2. `THEME_SETTINGS`: the `settings.py` assignments shown on `/theming/` (T and C five names, A twelve).
3. `THEME_PACKAGES`: names whose appearance in app code would mean the app knows the theme.
4. `THEME_DOC_URL`, and the prose in `GROUPS`.
5. The dark-mode attribute: `data-bs-theme` (T, A), `data-coreui-theme` (C).
6. The collapse event: `show.bs.collapse` (T, A), `show.coreui.collapse` (C); `data-bs-toggle` against
   `data-coreui-toggle`.
7. The icon tag: `{% icon "code" %}` (T), `{% icon "cil-code" %}` (C), `{% cv_icon "code" %}` (A).

Items 5 and 6 are one fact, the theme's data-attribute prefix, and **core already exposes it**: `get_data_prefix()`
in `src/crud_views/lib/data_prefix.py`, `{% cv_data_prefix %}` in `src/crud_views/templatetags/crud_views.py`, and
`data-data-prefix` on `#cv-config` (`src/crud_views/templates/crud_views/tags/cv_config.html`, read in
`static/crud_views/js/adapters.js`). Item 7 is solved by `{% cv_icon %}` with semantic names, as A does. That leaves
items 1 to 4: about ten values, which fit one settings dict.

Two properties of the collector must survive any change:

- It decides what an "example app" is by location: `Path(config.path).resolve().parent == EXAMPLE_DIR`
  (`_example_app_dir`). Any move of the apps changes this line.
- It reads `config/settings.py` with `ast` and shows whole top-level assignments (`settings_excerpt`). A
  `settings.py` that star-imports a shared base would show nothing there. **This is a reason to keep each theme's
  `settings.py` whole and local.**

Its security posture is stated in its docstring and worth keeping word for word: "The set of files is fixed here,
never taken from a request", and the app label is checked against the app registry.

Core's and ext's own examples have a different, simpler feature (`examples/bootstrap5/project/templatetags/
example_tags.py`, `snippet_panels`). It is out of scope here.

### 3.9 Drift that has already happened

- T's `Order.steps` lacks `done`; T's dashboard hard-codes `<span class="badge bg-blue-lt">` where C and A render
  `{{ order.state_badge }}`.
- T has no `catalog` migration `0003`; A has a `0004` the others lack (3.3).
- T's icon vocabulary has 31 keys, C's the same 31, A's 44.
- Bulk actions were planned and built per repo (T `superpowers/plans/2026-11-21-bulk-actions.md`, C the same file
  name, A inside its theme plan).
- The demo-deployment files exist in T only; `boot.py` is a third byte-identical copy of core's and ext's.

C's spec made the copy a conscious, temporary choice: "Sharing code with the Tabler project (no common base
package). Copy now; tracker U8 records whether a shared abstraction is worth proposing later", and its tracker says
"revisit when a third theme exists". The third theme exists.

### 3.10 Packaging, CI and deployment facts that constrain the options

- T's sdist ships `example/` (`[tool.hatch.build.targets.sdist] only-include`), and `scripts/check_dist.py` checks
  every archive member against an allowlist.
- T's Render build is `pip install ".[examples]" -r requirements/demo.txt`, and `demo.yml` deploys an exact commit.
- A PyPI upload cannot carry a git URL in its metadata. That is why T keeps the core git URL in `noxfile.py` and
  `requirements/demo.txt` and not in the `examples` extra.
- **hatchling and submodules (verified by experiment):** an sdist built from a checkout whose submodule is
  initialised contains the submodule's files. Built from a plain `git clone`, it is silently incomplete: no error,
  the files are just missing.
- **Render and submodules (not verified):** community posts say Render syncs top-level submodules automatically and
  does not recurse. No official documentation was found. Treat as unknown until a real deploy shows it.

### 3.11 Precedents in these repos

- **Semantic names with a per-theme table:** `example/config/icons.py` (`ACME_ICONS`), introduced so that "the two
  Acme copies stay identical" (C's spec, goal 4).
- **Vendoring by script with a parity test:** `scripts/vendor_templates.py`, `HAND_EDITED`, `test_pack_parity.py`
  for the crispy packs.
- **Pinned git installs of an unreleased dependency:** `CRUD_VIEWS` (T, C), `PIN` (A).
- **Template shadowing as the theme mechanism:** a theme app listed before `crud_views`; a project's `DIRS` before
  app directories.
- **Read-only upstream checkouts with a tracker** in every theme repo's `CLAUDE.md`.

## 4. The decision has three parts

| Part | Question | Options |
|---|---|---|
| Seam | Which files are shared, which stay with the theme, and how does a theme's difference get in? | section 5 |
| Home | Where does the one copy live, and can it run there? | H1 to H5, section 6 |
| Transport | How does the shared code reach a theme repo's `example/`? | T0 to T6, section 7 |

The seam is the same for every home and every transport, and it is where a design would go wrong. Home and
transport are logistics.

## 5. The seam

### 5.1 Proposed split

| Area | Owner | Why |
|---|---|---|
| App Python of `catalog`, `dashboard`, `roastery`, `sales`, `shipping`, with migrations and app static | **shared** | 3.3, 3.4: identical apart from vocabulary |
| The nine templates of those apps that do not extend a shell, written in Bootstrap 5.3 | **shared, as defaults** | 3.6: C and A nearly agree already |
| A theme's own version of one of those nine | **theme**, as an override in `example/templates/<app>/` | Django's `DIRS` wins over app directories; the mechanism the themes already rely on |
| `dashboard/index.html`, `dashboard/user_list.html` | **project** (every theme, and the Bootstrap project), in `example/templates/dashboard/` | 3.6: they extend the project's shell, so a package cannot ship them |
| "Show code" collector, views, routes, tags, script, default templates | **shared** | 3.8 |
| `showcase` app | **theme**, unchanged | 3.3: it exists to exercise that theme's crispy pack |
| `config/settings.py`, complete | **theme** | 3.8: the theming page shows it; it is the integration recipe |
| `config/icons.py`, navigation (`acme_nav.py`, `menu.py`), shell includes, `acme.css`, login page | **theme** | they are the skin |
| Tests of app behaviour | **shared**, run where the shared code lives | 3.7 |
| Tests of a theme's markup, layout and navigation | **theme** | 3.7 |

Rule for shared code, to be written into its `CLAUDE.md`: **it never names a theme and never emits a class that is
not Bootstrap 5.3 or `acme-*`.** A theme that needs something else overrides a template or styles `acme-*` in its
`acme.css`.

### 5.2 Alternatives for the colour and badge differences

| | Approach | Judgment |
|---|---|---|
| a | Bootstrap 5.3 semantic colours and `bg-*-subtle text-*-emphasis` everywhere; `acme-avatar` for avatars | **Proposed.** Zero new code. Proven by 3.4 and 3.5. Costs Tabler's ten-colour palette and its lighter badge style. |
| b | Semantic tones in app code, and a per-project table that maps tone to class, like `ACME_ICONS` | Keeps Tabler's look. Adds a helper and a setting that every badge call goes through. Worth it only if (a) is rejected on sight. |
| c | App-declared class keys through core's `crud_views_button_class_defaults` on the AppConfig (`src/crud_views/lib/button_classes.py`), overridden by `CRUD_VIEWS_BUTTON_CLASSES` | Rejected. It bends a button registry into a general CSS lookup for a demo. |

### 5.3 Why not share more in the first step

- **Settings base module:** rejected. It breaks the theming page's excerpt (3.8) and hides the one file a reader of a
  theme repo most wants to read whole.
- **Showcase:** sharing it needs a seam for three layout objects plus widget attributes that differ in substance for
  A. Fifteen differing lines do not pay for that. Documented as not shared; revisit if a fourth theme copies it.
- **All tests at once:** needs a markup contract per theme before the first shared file exists. The existing suites
  keep passing against shared app code (3.4), so they can stay where they are and be thinned later.
- **Navigation data:** T and C define the menu in `acme_nav.py` (134 and 121 lines), A in `menu.py` for
  adminlte-django's own menu format. Two formats, three consumers. Left alone.

## 6. Home: where the one copy lives

| | Home | Runs on its own | Judgment |
|---|---|---|---|
| H1 | One theme repo is canonical, the others take from it | yes | **Rejected.** Another theme's example would depend on a repo that ships a different theme. No theme is neutral: T is furthest from the other two. |
| H2 | `django-crud-views/examples/acme/` | only with a stock skin | **Rejected.** Acme needs django-crud-views-extensions (datetimepicker, typeahead). Core's `pyproject.toml` has no such dependency, and ext depends on core: core's example would depend on its own downstream. Core's sdist ships `examples/`, so it would grow by the whole demo. |
| H3 | `django-crud-views-extensions/examples/acme/` | only with a stock skin | **Rejected.** The dependency direction is right, the meaning is wrong: that repo is the incubator for `crud_views_widget_*` apps. |
| H4 | A fourth repo with only the shared package | no | **Rejected.** Code nobody can run where it lives: its tests could only run downstream, three times. |
| H5 | A fourth repo: the shared package **and** a stock-Bootstrap 5 project around it | yes | **Recommended** (the maintainer's proposal). |

### H5 in detail

A new repository, working name `django-crud-views-acme` (D2). It holds the Acme apps and "Show code" as a package,
and an `example/` project that runs them on django-crud-views' stock Bootstrap 5 theme, the way
`django-crud-views/examples/bootstrap5` runs core's feature examples: a small `base.html` that loads Bootstrap from
the CDN, a navigation, a sign-in page, `CRISPY_TEMPLATE_PACK = "bootstrap5"`.

What it buys:

- The shared code is developed and tested where it lives. A change to an app has one test run that matters first.
- No theme is special. The dependency chain reads in one direction: core, ext, acme, then a theme's example.
- It matches the vocabulary finding (3.5, 3.6): Bootstrap 5.3 is already the common denominator. A's example is
  nearly this project with AdminLTE's shell around it.
- django-crud-views gets a realistic whole-application demo on its stock theme. Core's own example is a set of
  feature mini-apps.

What it costs, judged hard:

- **It is new code.** A Bootstrap shell (base, navigation, sign-in, dashboard, users page), its CSS and its tests.
  Estimate: 600 to 900 lines of templates, mostly adapted from A, 200 lines of settings, a few hundred lines of
  tests. It replaces about 5,700 duplicated lines per theme repo (app Python and migrations without `showcase`, and
  the shared part of "Show code"), but only once the themes switch.
- **Four skins to keep working instead of three.** Every new demo page needs a Bootstrap version first.
- **One more repository** with a Taskfile, noxfile, `CLAUDE.md`, linting, and later CI.
- **Scope creep is the real risk:** its own docs site, its own Render demo, its own PyPI project. None of that is
  needed for the goal. Section 9 keeps it out.

H5 does not choose a transport. That is section 7.

## 7. Transport: how the shared code reaches a theme repo

Scores: `++` clearly good, `+` fine, `-` a cost, `--` a serious cost.

| | Transport | G1 clone and run | G2 easy to explain | G4 one source | G5 keeps CI, sdist, Render | Verdict |
|---|---|---|---|---|---|---|
| T0 | Keep three copies | ++ | ++ | -- | ++ | Rejected: 3.9 |
| T1 | Copy by script, parity test | ++ | + | - | ++ | Fallback |
| T2 | `git subtree` | ++ | - | - | ++ | Rejected |
| T3 | Git submodule | + | - | ++ | - | Viable, not recommended |
| T4 | Installed package, sibling checkout plus pin | + | ++ | ++ | + | **Recommended** |
| T5 | Monorepo of all themes | -- | + | ++ | -- | Rejected |
| T6 | Symlinks; copier or cookiecutter | -- | -- | + | -- | Rejected |

### T0. Keep three copies

Costs nothing today and needs no explanation. But 3.9 is the bill so far, and C's copy is two days old (first commit
2026-11-20), A's one day: a feature built three times, a behaviour difference in `Order.steps`, diverging migrations,
diverging test coverage. It gets worse with every feature. Rejected.

### T1. Copy by script, with a parity test (vendoring)

Each theme repo keeps real files in `example/`. A script copies them from a checkout of the home repo and writes a
manifest of hashes. A test fails when a copied file no longer matches its manifest hash. It is the crispy-pack method
(3.11) applied to the demo.

- For: nothing changes for a user, for CI, for the sdist or for Render. A theme repo stays complete by itself. This
  is the lowest-risk option.
- Against: three copies stay in three histories, so every shared change is still three commits with large diffs.
  "Do not edit these files here" is a convention, held up only by the manifest test. An agent fixing a theme bug
  will edit the copy in place and then regenerate the manifest to make the test pass. Drift is detected, not
  prevented.
- Verdict: the fallback if the maintainer weighs a self-contained theme repo above a structural single source (D1).

### T2. `git subtree`

The same outcome as T1 (real files in each repo), with git's machinery in place of a 40-line script. The merge
commits, the `--prefix` and `--squash` rules and the behaviour on a local edit are harder to explain than "a script
copies the files". No advantage over T1 here. Rejected.

### T3. Git submodule

The home repo is mounted inside each theme repo, for example at `example/acme/`. G3 allows it.

- For: one source by construction. The mounted commit is a pin that lives in git, in one place per theme repo. Files
  are on disk under `example/`.
- Against, each point checked against these repos:
  - A submodule mounts a whole repository. With H5 the mount contains the Bootstrap project as well, so `acme` is
    not importable from `example/` without a path entry or a path install of the mount. The second variant is T4
    with a submodule as the delivery vehicle.
  - T's sdist, built from a checkout without the submodule, is silently incomplete (3.10). `check_dist.py` needs a
    witness file, and every `actions/checkout` step needs `submodules: true`.
  - Render's behaviour is unverified (3.10).
  - GitHub's "Download ZIP" contains no submodule content.
  - Local work on all three themes means three working copies of the shared repo, one per mount, plus a fourth for
    its own development. "Which copy did I edit" is a new way to lose an afternoon, and the maintainer's present
    setup (one sibling checkout per upstream) does not have it.
  - It adds a second mechanism without retiring the first: core and ext remain sibling checkouts.
- Verdict: workable, and the maintainer said it is acceptable. Not recommended, because it is the more complicated
  of two options that both give one source.

### T4. Installed package: sibling checkout locally, pinned install elsewhere

The home repo builds a distribution (`django-crud-views-acme`) with one import package, `acme`. A theme repo consumes
it exactly like core and ext:

```toml
# <theme>/pyproject.toml
[project.optional-dependencies]
examples = ["django-crud-views-acme", ...]        # once it is on PyPI; until then see noxfile.py

[tool.uv.sources]
django-crud-views-acme = { path = "../django-crud-views-acme", editable = true }
```

```python
# <theme>/noxfile.py, next to CRUD_VIEWS; the same line goes into requirements/demo.txt
ACME = "django-crud-views-acme @ git+https://github.com/jacob-consulting/django-crud-views-acme@<commit>"
```

- For:
  - **No new concept.** The maintainer already runs this pattern twice per theme repo, and every theme `CLAUDE.md`
    documents it. "The demo's apps come from a package, like django-crud-views itself" is one sentence.
  - One working copy of the shared code on the machine. An edit is live in all three demos at once, because the
    install is editable.
  - The boundary is structural: there is nothing in a theme repo to edit by mistake. It fits the rule the theme
    repos already have ("both checkouts are read-only for this repo: gaps are worked around here and logged").
  - The theme repo's `example/` becomes exactly what a theme integration consists of. "The app code never imports
    the theme" is then true by construction, not by a grep test.
  - "Show code" still works: it reads the app's files from `AppConfig.path`, wherever the package is installed.
- Against:
  - **The app sources are not in the theme repo.** A reader of T on GitHub sees settings and templates, and has to
    follow a link for the models. The running demo's "Show code" panel covers the gap; a ZIP download does not.
  - A third sibling checkout for local development. A stranger's `task up` fails without it, as it already fails
    without the other two (3.1).
  - Local runs use the sibling's HEAD, nox uses the pin. "Green locally, red in the matrix" becomes possible for
    acme as it already is for core. `task test:matrix` is the guard, as today.
  - A pin to bump in three places per theme repo (`noxfile.py`, `requirements/demo.txt`, later the extra's version)
    whenever the theme wants newer app code.
  - Before a theme's first PyPI release with an `examples` extra that names acme, acme must be on PyPI too (3.10),
    or the extra leaves it out and the git line stays in `requirements/demo.txt`, which is what T does for core
    today.
- Verdict: recommended.

### T5. Monorepo of all themes

One repository, `themes/tabler`, `themes/coreui`, `themes/adminlte`, one `example/` with a settings module per
theme. It makes the problem disappear: one copy, atomic commits. It also ends "three projects that can each be
cloned", merges three histories, three release cycles and three support matrices (A needs Django 6.0 and
django-components with `APP_DIRS = False`), and puts the licence hygiene rules of C (no CoreUI PRO material) and T
(the paid Tabler archives) into one history. It contradicts G1 as stated. Rejected.

### T6. Symlinks, copier, cookiecutter

Symlinks to a sibling break in the sdist, in CI, on Render and on Windows. A copier or cookiecutter template turns
the canonical source into Jinja-templated Python that cannot run where it lives. Rejected.

## 8. "Show code": where it is shared

| | Option | Judgment |
|---|---|---|
| S1 | An app `acme.showcode` in the shared package, configured by one settings dict | **Recommended.** Same home and transport as the apps: one mechanism for both questions. |
| S2 | A new opt-in app in core (`crud_views_showcode`) | Rejected for now. It would put a view that reads source files from disk into a library every user installs, and commit core to its API before 1.0, for a feature only demos need. Under the Decision Rule it can be proposed later, once S1 has proven itself and core's and ext's examples want it. |
| S3 | An app in django-crud-views-extensions | Rejected. Not a widget, and not an extension of crud_views. |
| S4 | Three copies made byte-identical, with a parity test | The T1 variant. Only if T1 is chosen for the apps. |

Shape of S1, enough for planning (the plan fixes names):

```python
# <theme>/example/config/settings.py
INSTALLED_APPS = [..., "acme.showcode", ...]
ACME_SHOWCODE = {
    "theme_dir": BASE_DIR.parent / "src" / "crud_views_tabler",   # listed on /theming/; None: no theming page
    "shell_dir": BASE_DIR.parent / "src" / "django_tabler",       # counted, not shown; None for a third-party shell
    "host_package": None,                                         # A: ("adminlte-django", "django_adminlte4", url)
    "theme_packages": ("django_tabler", "crud_views_tabler"),     # names an app's code must not contain
    "settings": ("INSTALLED_APPS", "CRISPY_TEMPLATE_PACK", "CRUD_VIEWS_EXTENDS", ...),   # shown on /theming/
    "project_apps": ("showcase",),                                # project-local apps that also get a panel
    "docs_url": "https://django-crud-views-tabler.readthedocs.io/en/latest/theme_internals/",
}
```

- Which apps get a panel: every app inside the `acme` package except `dashboard` and `showcode`, plus
  `project_apps`. That replaces the `parent == EXAMPLE_DIR` test (3.8).
- Which templates the panel shows for an app: for each template under the app's `templates/`, the project's override
  if there is one, otherwise the app's default. That is the file Django renders.
- Dark-mode selector, toggle attributes and the collapse event come from core's data prefix (3.8). The icon comes
  from `{% cv_icon %}` with the semantic names `code` and `theming`, which T and C add to `ACME_ICONS`.
- The prose that describes a theme's file groups (`GROUPS` in `config/views.py`) moves into the theme's own
  `showcode/theming.html`.
- The docstring's guarantee stays: the file set is fixed in code and settings, never taken from a request.

## 9. Recommendation

**H5 + T4 + S1**, with seam 5.1 and colour approach 5.2 (a).

A fourth repository holds a package `acme` (five apps and `showcode`) and a stock-Bootstrap project that runs it.
The three theme repos depend on that package like they depend on core and ext, keep `showcase`, `config/` and their
templates, and override the app pages they restyle.

### 9.1 Target layout

```
django-crud-views-acme/                 # working name (D2)
  pyproject.toml                        # dist django-crud-views-acme; wheel: src/acme
  src/acme/
    catalog/ dashboard/ roastery/ sales/ shipping/
      apps.py                           # name "acme.sales"; the app label stays "sales"
      models.py views*.py forms.py seed.py urls.py admin.py migrations/ static/
      templates/<app>/*.html            # the pages in plain Bootstrap 5.3 (none for dashboard, see 5.1)
    showcode/                           # collector, views, urls, tags, code-panel.js, default templates
    login_required.py  formats/         # identical in all three config/ today
    urls.py                             # the app and showcode includes that config/urls.py repeats today
  example/                              # the stock-Bootstrap project: task up runs it
    manage.py  pytest.ini
    config/settings.py urls.py icons.py
    templates/project/base.html nav.html crud_views.html   registration/login.html
    templates/dashboard/index.html user_list.html          # extend project/base.html
    static/acme/acme.css favicon.svg
  tests/                                # behaviour tests of the apps and of showcode
  Taskfile.yaml  noxfile.py  CLAUDE.md  README.md

django-crud-views-<theme>/example/      # after the switch
  manage.py  pytest.ini
  config/settings.py urls.py icons.py   # plus acme_nav.py or menu.py; T: settings_demo.py, boot.py, ratelimit.py
  showcase/                             # theme-owned, unchanged
  templates/
    project/crud_views.html             # the theme's page plus the "Show code" button
    <shell>/includes/*.html             # branding
    registration/login.html
    dashboard/index.html user_list.html # the project's own: they extend the shell
    sales/ catalog/ ...                 # overrides, only for the pages this theme restyles
    showcode/theming.html               # the theme's own prose and markup
  static/acme/acme.css
  <tests of this theme's markup, layout and navigation>
```

Why `acme.sales` and not a top-level `sales`: an installed distribution that puts `sales`, `catalog`, `dashboard`
and `shipping` at the top of `site-packages` invites name clashes. The app label stays `sales`, so permission names
(`sales.add_order`), migration dependencies, content types and URL names do not change.

### 9.2 What changes for each goal

- **G1:** a theme repo still clones and runs with `task up`, next to three sibling checkouts where it needs two
  today. The new repo clones and runs next to two. Optional and outside this design: once core 1.0 is on PyPI, a
  `uv sync --no-sources` path could give a stranger a run with no sibling at all.
- **G2:** one sentence per repo. Acme repo: "the demo's apps, and a plain Bootstrap project to run them". Theme repo:
  "`example/` is the skin; the apps come from django-crud-views-acme".
- **G4:** one copy of app code and of "Show code". A theme cannot drift: it has no copy.
- **G5:** T's nox, CI and Render gain one pinned line each, the kind they have for core. T's sdist still ships
  `example/`, which is now the skin.

### 9.3 Where this recommendation is weakest

1. **It pays off late.** After stage 1 there are four copies. The first saving comes with the first theme's switch,
   the real saving with the second. If the work stops after stage 1, it made things worse.
2. **The fourth skin is permanent work**, justified only because the alternative is shared code that cannot run
   where it lives.
3. **Default templates with overrides can drift**, the documented weakness of copied templates. An override in T
   keeps rendering when the default gains a field. Guard: each theme keeps its page sweep (`test_every_page_renders`
   in C and A; T gets one) and a test that every override under `example/templates/<app>/` still has a default to
   shadow (the two dashboard templates are exempt: they have none).
4. **Theme-driven app changes cross a repo boundary.** A's `revenue_title` context (3.3) is the example: a theme
   needs the app to expose one more value. Today that is a local edit. Afterwards it is a change in acme plus a pin
   bump. The evidence says it is rare (107 lines after three independent ports), but it is the standing cost of
   sharing.
5. **A reader of a theme repo no longer sees the app code there.** If the maintainer wants a theme repo to be a
   complete, readable application on GitHub, T1 is the honest answer, and its costs are named in section 7.

## 10. Stages

Each stage ends in a state that works and can be stopped at. Sizes are relative.

| Stage | What | Size | Exit criterion |
|---|---|---|---|
| 0 | Decisions D1 to D5; create the repository; write its `CLAUDE.md` with the rule from 5.1 | S | repository exists and is in the theme sessions' access scope |
| 1 | Build acme from A's example (the newest, already Bootstrap 5.3, `cv_icon`, crispy `bootstrap5`): package layout, `acme.showcode`, neutral wording, one neutral `catalog` migration `0003`, the Bootstrap shell, its tests, a nox matrix Python 3.12 to 3.15 × Django 4.2, 5.2, 6.1 | L | `task up` serves every page; tests and `manage.py check --fail-level WARNING` pass on the whole matrix |
| 2 | Switch A (closest to the defaults, no CI, no Render) | M | A's example runs on `acme`; A's example tests pass; the pages look as before |
| 3 | Switch C | M | as stage 2; no `data-bs-` in any page (C's existing test) |
| 4 | Switch T: the most overrides, then nox, CI, `check_dist.py`, `requirements/demo.txt`, `render.yaml` | L | as stage 2; `uvx nox` green; a Render deploy from a branch serves the demo |
| 5 | Thin the tests: move behaviour tests that assert no theme markup into acme, delete the copies | M, optional | each behaviour test exists once |

Per-theme switch, in the order that keeps every step testable:

1. Add the dependency: path source, the pin in `noxfile.py`, the `examples` extra or the requirements line.
2. `INSTALLED_APPS`: `acme.catalog`, `acme.dashboard`, `acme.roastery`, `acme.sales`, `acme.shipping`,
   `acme.showcode` in place of the local apps; `ACME_SHOWCODE`; `config/urls.py` includes `acme.urls`.
3. Delete the five local app directories, `config/showcode.py`, `config/views.py`,
   `config/templatetags/showcode.py`, `config/login_required.py` and its test, `config/formats/`. Keep `showcase/`.
4. Move the theme's app templates from `example/<app>/templates/<app>/` to `example/templates/<app>/`. Delete those
   that equal the default. The two dashboard templates always stay.
5. Fix imports in the remaining tests (`from sales.models` becomes `from acme.sales.models`) and add the override
   guard from 9.3.
6. Run the example tests, the system check, and a browser pass in light and dark mode over every page: the visual
   check 3.4 could not make.
7. Update `README.md`, `docs/`, `CLAUDE.md`, the tracker and, for T, `scripts/check_dist.py`.

Existing local databases keep working: the migration names of the five apps stay, a help text is not stored in the
database, and A's applied `0004` becomes an unknown row Django ignores. `task reset` gives a clean state.

## 11. Decisions the maintainer has to make

| | Decision | Recommendation | If decided otherwise |
|---|---|---|---|
| D1 | Transport | T4, installed package | T1 if the theme repos must stay self-contained; T3 if the pin must live in git |
| D2 | Repository and package name | `django-crud-views-acme`, package `acme` | any name; `django-crud-views-bootstrap5` would wrongly suggest a theme package |
| D3 | Is `showcase` shared? | No, theme-owned | sharing needs a seam for the crispy layout objects (5.3) |
| D4 | May T's demo use Bootstrap's badge style and six avatar colours (3.5, row 3)? | Yes | 5.2 (b): a tone table per project |
| D5 | Does acme get its own public demo, docs site and PyPI project? | No demo, no docs site; PyPI only when a theme's first release needs it | each is a separate, later design |

## 12. Not verified, and unsupported cases

Not verified:

- **The look of any page after a switch.** 3.4 covers behaviour, 3.5 covers badges under Tabler in a static page.
  A browser pass per theme is part of every switch (stage step 6).
- **A's own example suite** against shared code. It could not be installed in a flat checkout layout (3.1).
- **Render with a submodule** (3.10). Only relevant if D1 is T3.
- **`acme-avatar` under T and C.** A defines it in `acme.css`; T and C need the same few rules or an override.
- **Django 4.2 for A's five extra lines** in `dashboard/views.py` and the other A-only deltas. A tests on Django 6.0
  and 6.1 only. Stage 1's matrix settles it.
- **That five apps is the right cut for `dashboard`.** Its two templates are always overridden, so only its views,
  seed and commands are shared. The spike supports it; the plan should confirm it file by file.

Unsupported, on purpose:

- The showcase app is not shared (D3).
- No shared settings module and no shared navigation data (5.3).
- Core's and ext's own examples do not use `acme.showcode`. Their `snippet_panels` stays.
- The demo-deployment helpers (`boot.py`, `ratelimit.py`, `settings_demo.py`), copied between core, ext and T, are
  not addressed.

## 13. How to recompute the evidence

With the five repositories checked out next to each other in `<dir>`:

```python
"""Three-way comparison of example/ in the three theme checkouts. Usage: python compare_examples.py <dir>"""

import difflib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1])
REPOS = {"T": "django-crud-views-tabler", "C": "django-crud-views-coreui", "A": "django-crud-views-adminlte"}


def tracked(repo):
    out = subprocess.run(["git", "ls-files", "example"], cwd=ROOT / repo, capture_output=True, text=True, check=True)
    return {line for line in out.stdout.splitlines() if line}


def category(path):
    parts, name = path.split("/"), path.rsplit("/", 1)[-1]
    if "/migrations/" in path:
        return "1b app migrations"
    if "/tests/" in path or name.startswith("test") or name == "tests.py":
        return "4 tests"
    if parts[1] in ("config", "manage.py", "pytest.ini"):
        return "5 config"
    if parts[1] in ("templates", "static"):
        return "6 project templates/static"
    if path.endswith(".html"):
        return "2 app templates"
    return "3 app static" if "/static/" in path else "1a app python"


def changed(a, b):
    """Lines that differ between two files (a missing file counts in full)."""
    if a is None or b is None:
        return len(a or b or [])
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in ops if tag != "equal")


files = {key: tracked(repo) for key, repo in REPOS.items()}
rows = defaultdict(lambda: defaultdict(int))
for path in sorted(set().union(*files.values())):
    text = {}
    for key, repo in REPOS.items():
        file = ROOT / repo / path
        text[key] = file.read_text(encoding="utf-8", errors="replace").splitlines() if path in files[key] else None
    row = rows[category(path)]
    row["paths"] += 1
    row["identical"] += text["T"] is not None and text["T"] == text["C"] == text["A"]
    row["lines T"] += len(text["T"] or [])
    for pair in ("TC", "CA", "TA"):
        row[f"changed {pair}"] += changed(text[pair[0]], text[pair[1]])

columns = ["paths", "identical", "lines T", "changed TC", "changed CA", "changed TA"]
print(f"{'category':28}" + "".join(f"{c:>12}" for c in columns))
for name in sorted(rows):
    print(f"{name:28}" + "".join(f"{rows[name][c]:>12}" for c in columns))
print(f"{'total':28}" + "".join(f"{sum(r[c] for r in rows.values()):>12}" for c in columns))
```

The differences of section 3.3, file by file:

```bash
diff -u django-crud-views-tabler/example/sales/models.py django-crud-views-coreui/example/sales/models.py
```

The spike of section 3.4, in a scratch directory with `git archive HEAD` copies of T, C and A and symlinks named
`django-crud-views` and `django-crud-views-extensions` beside them:

```bash
cd django-crud-views-tabler && uv sync --extra examples --extra test && cd example && uv run pytest -n auto
```

Then, for each `*.py` under A's `example/{catalog,dashboard,roastery,sales,shipping,showcase}` that is not a test,
not `showcase/views.py` and not under `dashboard/templatetags/`, copy it over the same path in T's copy and run the
suite again. The same for C.

The stylesheet check of section 3.5:

```bash
npm pack @tabler/core@1.6.1
```

Unpack `package/dist/css/tabler.min.css` from the archive and search it for `.bg-success-subtle`.

The hatchling experiment of section 3.10: a repository with `only-include = ["src", "example", "pyproject.toml"]`
and a submodule at `example/acme`; `uv build --sdist` once in that checkout and once in a plain `git clone` of it,
then compare `tar -tzf` of the two archives.

## 14. External sources

- Render and submodules, community reports only:
  [Git nested submodules not syncing](https://community.render.com/t/git-nested-submodules-not-syncing/7488),
  [feature request to disable submodule syncing](https://feedback.render.com/features/p/id-like-a-way-to-disable-git-submodules-from-being-syncd-optionally).
- hatchling file selection: [Build configuration](https://hatch.pypa.io/dev/config/build).
