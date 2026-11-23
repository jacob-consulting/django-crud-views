# Keep the Acme Roasters example in step across the theme repos

Run this from time to time, after work on any of the three demo projects:

> Follow `superpowers/prompts/acme-example-sync/PROMPT.md` in django-crud-views.

Add `apply` to let the agent port unambiguous changes without waiting for a go (see "Mode").

## What this is

django-crud-views-tabler, django-crud-views-coreui and django-crud-views-adminlte each carry their own copy of the
same demo project in `example/`. They are independent copies on purpose: the maintainer decided on 2026-11-23 not to
share the code, because a demo must stay easy to read, install and deploy
(`superpowers/specs/2026-11-22-shared-acme-demo-design.md`, "Maintainer decision"). The price is drift: a model, a
page or a test added in one repo and forgotten in the other two. Your job is to find what changed in each copy since
the last sync and carry it to the others, in each theme's own markup, and to prove that every copy still works.

You are not unifying the copies. What a theme does differently because it is that theme stays different.

## Mode

- **Default, plan first:** do steps 1 to 4, present the plan, and stop. Port only after the maintainer says go.
- **`apply`:** after step 4, continue with every change the plan marks "port", and stop only where "Stop and ask"
  says so.

## The three checkouts

`drift.py` looks for `django-crud-views-tabler`, `-coreui` and `-adminlte` next to the django-crud-views checkout
that holds this file. Pass `--tabler`, `--coreui`, `--adminlte` for any other layout. If a checkout is missing, ask
for its path; do not clone anything.

Before you start: each of the three must have a clean working tree and be on the branch whose state should be
compared, normally an up-to-date `main`. `drift.py` only sees committed state. Read each repo's `CLAUDE.md` first;
its rules apply to everything you do there.

## What belongs to whom

| The same in all three: port it | The theme's own: do not port, do not "fix" |
|---|---|
| Models, migrations, managers, permissions, services | Markup and classes in templates |
| What a view does: querysets, columns, filters, actions, access rules, messages | `static/acme/acme.css` and other project static files |
| Forms: fields, validation, layout structure | `config/settings.py` apart from what a new feature needs (an app, a setting) |
| URLs and URL names; ViewSet names | The icon a semantic name maps to (`config/icons.py` values) |
| Seed data and management commands | Navigation code: `config/templatetags/acme_nav.py` (Tabler, CoreUI), `config/menu.py` (AdminLTE) |
| Tests of behaviour | Test assertions about where the theme puts things or which classes it uses |
| The *set* of pages, menu entries and semantic icon names | Colour and class vocabulary (table below) |
| What "Show code" does (`config/showcode.py`, `config/views.py`) apart from its theme constants | `showcase/views.py`: which crispy layout objects and widget attributes it uses |
| | Tabler's Render demo files (`settings_demo.py`, `boot.py`, `ratelimit.py`, their tests) |

A change in a theme-owned file can still carry something the other themes need: a menu entry for a new page, a new
semantic icon name, an app in `INSTALLED_APPS`. Port that meaning, written the target's way. Leave pure looks alone.

How the same thing is written in each theme:

| | Tabler | CoreUI | AdminLTE |
|---|---|---|---|
| Colour names in Python and seed data | Tabler palette: `green`, `lime`, `azure`, `orange`, `yellow`, `red`, `pink`, `purple`, `indigo`, `brown` | Bootstrap theme colours: `success`, `info`, `warning`, `danger`, `primary`, `secondary`, `dark` | as CoreUI |
| Badge | `badge bg-<colour>-lt` | `badge bg-<colour>-subtle text-<colour>-emphasis` | as CoreUI |
| Avatar | `avatar avatar-sm bg-<colour>-lt` | `avatar avatar-sm bg-<colour>-subtle text-<colour>-emphasis fw-semibold` | `acme-avatar` with the same colour classes |
| Data attributes in templates | `data-bs-*` | `data-coreui-*` | `data-bs-*` |
| Crispy pack objects (showcase only) | `django_tabler.crispy.layout` | `django_coreui.crispy.layout` | `crispy_bootstrap5.bootstrap5`; `Field(name, disabled=True)` for an uneditable field |
| Locating the page header in a test | from `class="page-header` to `class="page-body` | from `class="page-header` to `<main>` | `sales/tests/markup.py` |

When a ported line needs a colour or a class, write it as the lines around it in the target file do. The existing
code is the reference, this table is a reminder.

## Procedure

### 1. Report

```bash
python superpowers/prompts/acme-example-sync/drift.py report
```

It lists every path under `example/` that changed in at least one repo since the baseline and is not identical in
all three now. For each path it names the repos where it changed (the sources) and where it did not (the targets),
prints a `git diff` or `git show` command for the source's change, and the commits that made it. Paths that still
match the baseline are not listed: the last sync accepted them, identical or different.

If the report is empty, say so and stop. Do not go looking for older differences (see "Known state").

### 2. Read every change

Run the printed commands. Group paths into changes by the commits that made them: a model, its migration, the form,
the view, a template and a test usually arrive together. Read the commit messages; they say what was meant.

### 3. Decide per change

- **Port:** it changes something from the left column. Targets are the repos where it is missing.
- **Theme's own:** it only changes looks or theme wiring. No port. Check that nothing in it needs the "meaning"
  treatment above.
- **Mixed:** split it. Port the behaviour, leave the looks.
- **Changed in two or three repos:** compare the changes. The same change in different words is a finished port:
  nothing to do. Different changes to the same thing are a conflict: stop and ask.

Never port backwards. A repo where a path is "as at the baseline" is a target, never a source, even when its
version looks nicer.

### 4. Plan

Present one table: change, source repo and commit, decision, target repos, files to touch in each target, and what
needs a human look afterwards. List separately what you will not port and why. In the default mode, stop here.

### 5. Port, one target repo at a time

- **Python:** apply the same change, not the same file. The target's file may differ from the source's in
  vocabulary (table above); keep the target's.
- **Migrations:** copy the source's new migration file unchanged, so names and dependencies stay the same in all
  three. First check that the target's latest migration of that app is the one the new file depends on. Then run
  `makemigrations --check --dry-run`: it must report no changes. If it wants another migration, the models differ:
  find out why before going on.
- **Templates:** a new or changed template is re-written in the target theme's markup. Use the target's own
  templates for the same kind of page as the model for structure and classes; never paste another theme's
  component classes. Every template you write goes on the "needs a human look" list. Follow the target repo's rule
  for theme gaps (an upstream hook, then CSS, then an override, each with a tracker entry).
- **Tests:** port every test that came with the change. Keep the behaviour assertions; re-write assertions about
  markup with the target's own way of locating things.
- **Icons:** a new semantic icon name gets an entry in the target's `config/icons.py`, with an icon the target's
  library already has. Run the system check; it flags a name without a picture. If no existing icon fits, stop and
  ask.
- **New page:** also the menu entry (in the target's navigation file), the README's page table if it has one, and
  any `docs/` page that lists the demo's pages.
- **"Show code":** port logic changes in `config/showcode.py` and `config/views.py`; keep each repo's constants
  (`THEME_DIR`, `SHELL_DIR`, `THEME_SETTINGS`, `THEME_PACKAGES`, URLs, group texts).

### 6. Verify each target repo

Use the commands from that repo's `CLAUDE.md`. At least:

```bash
uv run ruff format . && uv run ruff check .
cd example && uv run pytest -n auto
uv run python example/manage.py makemigrations --check --dry-run
uv run python example/manage.py check --fail-level WARNING
```

All four must pass. Run the source repo's example suite too if you touched it. A failing test is fixed in the port,
never skipped.

### 7. Commit

One commit per ported change in each target repo, on the branch you were told to use, otherwise
`sync/acme-example-YYYY-MM-DD`. Message: `example: port <what> from <source repo>@<short commit>`. Do not push and
do not open a pull request unless asked.

### 8. Close the sync

Run the report again. Every path it still lists must be one you can name a reason for: theme's own, or left open by
the maintainer's decision. Then, and only then:

```bash
python superpowers/prompts/acme-example-sync/drift.py accept
```

This writes `baseline.json` from the three HEAD commits. Append an entry to `LOG.md` (date, the three commits, what
was ported, what was left different and why, what needs a human look) and commit both files in django-crud-views.
Never run `accept` to make a report quiet: it declares the present state correct.

### 9. Report back

The table of step 4 with the outcome per row, the verification results per repo with the commands run, the pages a
human should look at in a browser (URL and theme), and every open question.

## Stop and ask

- The same thing was changed differently in two repos.
- A port needs a change in `src/` of a theme repo, or in django-crud-views or django-crud-views-extensions. Those
  two checkouts are read-only for this task.
- A migration cannot be copied unchanged, or `makemigrations --check` wants a new one.
- A new page needs an icon or a component the target theme does not have.
- You cannot tell whether a difference is behaviour or the theme's own.
- A test fails and the cause is not the port.

## Hard rules

- App code never imports a theme package. Do not weaken a repo's test for that.
- Nothing from the paid Tabler archives or from CoreUI PRO goes into any repository.
- You cannot see the pages. Never report a template as correct; report it as written and tested, to be looked at.
- Report what you did not do as plainly as what you did.

## Known state at the first baseline (2026-11-23)

The baseline was written from Tabler `307b9d5`, CoreUI `d67be0f`, AdminLTE `83cb1e8`: 153 paths, 76 identical in
all three, 77 accepted as different. Most of the 77 are the theme's own. Some are old drift that the baseline
accepted so that the first report starts empty. Leave them alone unless the maintainer asks for them by name:

1. Tabler's `Order.steps` (`sales/models.py`) has no `done` key; CoreUI's and AdminLTE's has.
2. Tabler's `dashboard/index.html` hard-codes the order state badge; the other two render `order.state_badge`.
3. Tabler has no page sweep test; CoreUI and AdminLTE have `test_every_page_renders`.
4. `catalog` migrations: `0003` exists in CoreUI and AdminLTE, `0004` in AdminLTE only, because the model's help
   text names the theme.
5. The semantic icon vocabulary has 31 names in Tabler and CoreUI and 44 in AdminLTE.

The evidence for all of this, file by file, is section 3 of the spec named at the top.
