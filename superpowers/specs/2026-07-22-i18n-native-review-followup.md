# i18n: native-speaker review of fr/es/pt/it/zh-hans catalogs

> Draft GitHub issue body, to be opened at merge time (closing #88). Not a design spec — this
> file is the issue text itself, kept under `superpowers/specs/` because `docs/` is
> mkdocs-published and this content is not user-facing documentation.

## Summary

As part of #88 (full i18n rollout across all packages and the example app), five of the six
translated locales were machine-authored to reach complete seven-language coverage in one pass.
Only `de` (German) is human-authored. The other five need review and correction by a native
speaker before they can be considered production-quality:

- `fr` — French
- `es` — Spanish
- `pt` — Portuguese
- `it` — Italian
- `zh-hans` — Simplified Chinese (gettext directory: `zh_Hans`)

Every affected `.po` file carries a header comment flagging this:

```
# NOTE: fr/es/pt/it/zh-hans translations are machine-authored pending native review (see #88 follow-up).
```

## Why this matters

Machine translation can produce strings that are grammatically valid but stylistically off,
inconsistent in register/formality, or wrong for domain-specific UI terms (e.g. "Save",
"Confirm deletion", permission/workflow vocabulary). `de` is the baseline for what a
human-reviewed catalog should look like.

## Files to review

Each locale has one catalog per package — 5 packages × 5 locales = 25 files:

```
src/crud_views/locale/<locale>/LC_MESSAGES/django.po
src/crud_views_workflow/locale/<locale>/LC_MESSAGES/django.po
src/crud_views_polymorphic/locale/<locale>/LC_MESSAGES/django.po
src/crud_views_guardian/locale/<locale>/LC_MESSAGES/django.po
src/crud_views_object_detail/locale/<locale>/LC_MESSAGES/django.po
```

where `<locale>` is one of `fr`, `es`, `pt`, `it`, `zh_Hans`.

Plus the example app's own catalog, one per locale:

```
examples/bootstrap5/locale/<locale>/LC_MESSAGES/django.po
```

## Suggested approach

1. Recruit or assign a native speaker per language (does not need to be the same person across
   languages).
2. For each `.po` file: review every `msgstr` against its `msgid` for correctness, tone, and UI
   terminology consistency with the rest of that language's file.
3. Remove the `NOTE:` machine-authorship header comment once a locale's catalog (across all six
   files above) has been reviewed and corrected.
4. Recompile with `task msg-comp` (packages) and `task examples:msg-comp` (example app) and
   commit the updated `.po`/`.mo` pairs.
5. Add a guard, if practical, so CI catches a `NOTE:` header that has been left in place after a
   locale is marked reviewed (e.g. a tracked checklist per locale, or a marker this issue can be
   closed against once all five are done).

## Acceptance criteria

- [ ] `fr` reviewed by a native speaker, `NOTE:` header removed from all `fr` catalogs (5
      packages + example app)
- [ ] `es` reviewed and header removed
- [ ] `pt` reviewed and header removed
- [ ] `it` reviewed and header removed
- [ ] `zh-hans` reviewed and header removed
- [ ] `docs/development/i18n.md` "Machine-authored locales" section updated to drop any locale
      that has completed review

## References

- Origin: #88 (full i18n rollout)
- Guard tests: `tests/test1/test_i18n.py`, `examples/bootstrap5/test_i18n.py`
- Docs: `docs/development/i18n.md`
