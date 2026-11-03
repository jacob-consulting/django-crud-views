## Deferred Items

- Stale source references in the core German catalog outside the pagination msgids
  status: open
  **What:** `makemessages -l de` for `src/crud_views` (05-03) also wanted to add `lib/button_classes.py:46/47` to
  `Actions` (moving the entry), shift `Cancel` to `lib/view/base.py:790` and `Filter` to `lib/view/buttons.py:345`,
  and bump `POT-Creation-Date`. Translations are unaffected and the compiled catalog is current. Out of scope for
  Phase 5, which reverted that churn to keep the catalog diff to the three shared pagination msgids. A later
  catalog refresh can take it.
