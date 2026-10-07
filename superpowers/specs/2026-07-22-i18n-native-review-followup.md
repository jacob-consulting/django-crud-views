# i18n: native-speaker review follow-up — superseded

> Originally drafted as the GitHub issue body for a native-speaker review of machine-authored
> `fr`/`es`/`pt`/`it`/`zh-hans` catalogs (#99).

**Superseded (2026-10-06).** For the first major release the packages ship `en` (source) and
`de` (human-authored) only. The five machine-authored locales were removed rather than reviewed:

- No native reviewer was available for any of them.
- `fr`/`es`/`pt`/`it` defaulted to masculine agreement in strings that interpolate a runtime
  `verbose_name` (`… créé`, `tous les %(plural)s`), which is wrong for feminine model names and
  needs reworded translations, not just a review.
- Several technical terms were mistranslated or inconsistent across catalogs (e.g. "Workflow"
  kept in one catalog and translated in another; `pt` mixed European and Brazilian forms).

New locales are welcome as contributions under the requirements in
`docs/development/i18n.md` → "Requirements for a new package locale".
