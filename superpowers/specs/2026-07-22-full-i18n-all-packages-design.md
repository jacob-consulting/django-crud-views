# Full i18n across all packages and the example app

**Date:** 2026-07-22
**Issue:** [#88](https://github.com/jacob-consulting/django-crud-views/issues/88)
**Status:** Approved design, ready for implementation plan

## Problem

Only two of the five shipped packages carry translations, and only in German:

| Package | `locale/` today | Marked strings (`gettext`/`_`) |
|---|---|---|
| `crud_views` | ✅ `de` | 19 |
| `crud_views_workflow` | ✅ `de` | 3 |
| `crud_views_polymorphic` | ❌ | 2 |
| `crud_views_object_detail` | ❌ | 1 |
| `crud_views_guardian` | ❌ | 0 |

The `examples/bootstrap5` app has only `USE_I18N = True`. It is missing `LocaleMiddleware`,
`LANGUAGES`, `LOCALE_PATHS`, the i18n context processor, the `set_language` URL, and any
`locale/` directory. `nav.html` hardcodes "Log In"/"Log Out"; `base.html` hardcodes
`<html lang="en">`. The i18n documentation described infrastructure that does not exist —
the substance of issue #88.

## Goals

1. Every `crud_views_*` package correctly marks its user-facing strings and ships `.po` + `.mo`
   catalogs for all target locales.
2. The example app gets full i18n infrastructure, its own `locale/` catalogs, and translated
   templates — resolving #88.
3. Language defaults to the browser's `Accept-Language`, with a language selector in the top nav
   that persists an explicit choice.
4. `crud_views` ships the selector as a reusable component so downstream projects using the
   Bootstrap 5 theme get it for free.

## Non-goals

- RTL layout support (no RTL locale is in scope).
- Localising date/number formats beyond Django's defaults (`USE_I18N` covers message catalogs;
  `USE_L10N`/formatting is out of scope).
- Translating documentation prose or the README into other languages.

## Target locales

`en` (base/source — msgids are English, so **no `.po` is required**; the runtime falls back to the
msgid), plus catalogs for:

`de` (exists, extend), `fr`, `es`, `pt`, `it`, `zh-hans`.

### Translation authoring and the fuzzy caveat

German is already human-authored and authoritative. The five new catalogs (`fr`, `es`, `pt`,
`it`, `zh-hans`) are authored as part of this work.

**Important:** translations must **not** be marked `#, fuzzy`. `compilemessages` skips fuzzy
entries, so a fuzzy `msgstr` ships in the `.po` but renders as the English msgid at runtime —
defeating the purpose. New catalogs are therefore written as **active** translations. Each new
`.po` carries a header comment flagging that the non-German translations are machine-generated
and that native-speaker corrections are welcome. A follow-up issue tracks native review.

## Design

### 1. String audit and marking

Sweep all five packages and the example app; wrap every user-facing hardcoded string.

- **Python:** `from django.utils.translation import gettext_lazy as _` (lazy, for module-level and
  attribute strings) and wrap. Use `gettext` (non-lazy) only inside request-time functions where a
  string is needed eagerly.
- **Templates:** `{% load i18n %}` then `{% translate "..." %}` for simple strings and
  `{% blocktranslate %}...{% endblocktranslate %}` for strings with placeholders.
- Priority order by current gap: `crud_views_guardian` (0 marked) → `crud_views_object_detail` (1)
  → `crud_views_polymorphic` (2) → template strings still hardcoded in any package → example app.
- Do **not** mark developer-facing strings (log messages, exception messages for developers,
  system-check messages) unless they are already conventionally translated in the codebase.

### 2. Reusable language selector in `crud_views` core

- **Partial:** `src/crud_views/templates/crud_views/snippets/language_selector.html`
  - A Bootstrap 5 dropdown listing the project's `LANGUAGES` by their native display name.
  - Each item is a `POST` form to `set_language` including `{% csrf_token %}`, a hidden
    `language` input, and a hidden `next` input set to the current path (via
    `{{ request.get_full_path }}` / `redirect_to`), so the user returns to the same page.
  - The currently active language is marked (e.g. `active` class / check icon) using
    `{% get_current_language as LANGUAGE_CODE %}`.
  - **CSP-safe:** relies only on Bootstrap's `data-bs-*` attributes — no inline `on*` handlers or
    inline `<script>`. Consistent with the asset-registry / CSP work.
- **Template tag:** an inclusion tag `{% cv_language_selector %}` in
  `src/crud_views/templatetags/crud_views.py` that renders the partial with `LANGUAGES` and the
  active `LANGUAGE_CODE` in context (using `django.utils.translation.get_language` and
  `django.conf.settings.LANGUAGES`).
- **Project requirement (documented):** the selector needs the `set_language` view, which is
  project-level. Projects must add `path("i18n/", include("django.conf.urls.i18n"))`. The tag
  degrades gracefully (renders nothing / a disabled control) if only one language is configured.

### 3. Example app infrastructure (resolves #88)

- **`project/settings.py`:**
  - `MIDDLEWARE`: insert `django.middleware.locale.LocaleMiddleware` **after**
    `SessionMiddleware` and **before** `CommonMiddleware`.
  - Add `LANGUAGES` (the 7 locales, native names via `gettext_lazy`).
  - Add `LOCALE_PATHS = [BASE_DIR / "locale"]`.
  - Add `django.template.context_processors.i18n` to the template `context_processors`.
  - Keep `USE_I18N = True`; leave `LANGUAGE_CODE` as the ultimate fallback.
- **`project/urls.py`:** add `path("i18n/", include("django.conf.urls.i18n"))`.
- **`templates/project/nav.html`:** include `{% cv_language_selector %}` (right side of navbar);
  wrap "Log In"/"Log Out" and any other visible strings with `{% translate %}`.
- **`templates/project/base.html`:** `{% get_current_language as LANGUAGE_CODE %}` →
  `<html lang="{{ LANGUAGE_CODE }}">`.
- **Feature titles / views:** audit `example_tags`, `HomeView`, and example templates; mark
  visible strings.
- **`examples/bootstrap5/locale/`:** new directory with all 7 catalogs (`de`, `fr`, `es`, `pt`,
  `it`, `zh-hans`; `en` needs none).
- **Browser default:** provided automatically by `LocaleMiddleware` reading `Accept-Language`.
  The selector's `set_language` POST sets the `django_language` cookie, which takes precedence on
  subsequent requests. No custom middleware or view code.

### 4. `settings_i18n.py`

Extend `INSTALLED_APPS` to include all five packages so `makemessages` discovers strings in every
package:

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

### 5. Taskfile

- **Root `taskfile.yaml`:** replace the two `*-crud_views`-specific tasks with loop-all tasks that
  iterate every package × every locale:
  - `msg-make` — `makemessages` for all packages, all locales (via `settings_i18n`).
  - `msg-comp` — `compilemessages` for all packages.
  - Keep `msg-make-crud_views` / `msg-comp-crud_views` as thin aliases if convenient, or remove and
    update docs. (Decision at implementation: prefer the loop-all tasks as canonical.)
- **`examples/bootstrap5/taskfile.yaml`:** add `msg-make` and `msg-comp` using
  `uv run manage.py makemessages -l <locale>` / `compilemessages`.

### 6. Packaging

Verify the new `.mo` files ship in the wheel. hatchling's `[tool.hatch.build.targets.wheel]
packages = [...]` already bundles non-`.py` files under each package directory (the existing German
`.mo` ships today), so new `.mo` under the same `locale/` trees ride along with no `pyproject`
change. Confirm with a `uv build` + wheel-listing check as an implementation verification step;
add `force-include`/`artifacts` config only if the listing shows `.mo` missing.

### 7. Testing

- **Per package:** a test that activates a non-`en` locale and asserts a known string translates
  (e.g. `with translation.override("de"): assert str(_("Save")) == "Speichern"`), covering each
  package that now ships a catalog.
- **Catalog guard:** for each shipped `locale/<lang>/LC_MESSAGES/django.po`, assert there are no
  empty `msgstr` for non-obsolete entries, and that the sibling `.mo` exists and loads
  (`gettext.GNUTranslations`). This catches a half-authored locale before release.
- **Example app:** a request test that the selector switches language — POST to `set_language`
  then assert a translated nav string appears; and that `Accept-Language` alone selects a locale.
- Tests read the committed `.mo`, so **CI needs no gettext toolchain** at test time. gettext is
  only needed by contributors running `msg-make`/`msg-comp`.

### 8. Documentation

- Rewrite `docs/development/i18n.md` to reflect the now-real infrastructure: five packages, seven
  locales, the `{% cv_language_selector %}` component, the example-app setup, and the loop-all
  taskfile tasks. Remove the "#88 not yet wired" caveat and the missing-task notes.
- Note that non-German translations are machine-authored pending native review.
- Close issue #88 on merge; open a follow-up issue tracking native-speaker review of `fr`/`es`/
  `pt`/`it`/`zh-hans`.

## Risks and mitigations

- **Fuzzy translations rendering as English** — mitigated by authoring active (non-fuzzy) entries
  and the catalog-guard test.
- **`.mo` omitted from the wheel** — mitigated by the build-listing verification step.
- **CSP violation from the selector** — mitigated by using Bootstrap data-attributes only, no
  inline JS.
- **Machine-translation quality** — mitigated by the header comment and a native-review follow-up
  issue; German (the primary translated locale) remains human-authored.

## Out of scope / follow-ups

- Native-speaker review of the five machine-authored locales (follow-up issue).
- RTL locales and layout.
- Locale-aware date/number formatting.
