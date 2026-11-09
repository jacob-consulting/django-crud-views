---
phase: quick-261109-9rw
plan: "01"
status: complete
subsystem: examples
tags: [examples, guardian, nested, ancestor-authorization, i18n, seed]
requires: [phase 06.18 ancestor authorization (AncestorPolicy, GuardianViewSet ancestor provider, manage report)]
provides:
  - nested Guardian Note under Document in examples/bootstrap5/guardian_demo
  - seeded least-privilege note grants for alice/bob
  - non-superuser ancestor authorization tests for the core nested example
affects: [UAT 06.18 test 2 (Guardian manage page reports the ancestor policy)]
tech-stack:
  added: []
  patterns: [GuardianViewSet child via ParentViewSet, CreateViewParentMixin before Guardian create base, explicit AncestorPolicy on a top-level Guardian ViewSet]
key-files:
  created:
    - examples/bootstrap5/guardian_demo/migrations/0003_note.py
  modified:
    - examples/bootstrap5/guardian_demo/models.py
    - examples/bootstrap5/guardian_demo/views.py
    - examples/bootstrap5/guardian_demo/urls.py
    - examples/bootstrap5/guardian_demo/seed.py
    - examples/bootstrap5/guardian_demo/tests.py
    - examples/bootstrap5/nested/tests.py
    - examples/bootstrap5/project/features.py
    - examples/bootstrap5/locale/de/LC_MESSAGES/django.po
    - examples/bootstrap5/locale/de/LC_MESSAGES/django.mo
    - docs/reference/guardian.md
decisions:
  - "cv_document declares AncestorPolicy(provider=guardian, accept_global_perms=False) explicitly (equals the default) so the manage page's declared column shows it"
  - "cv_note declares no ancestor policy: the defaults (Read view/view, Write change/view) are the intended policy"
  - "Note author and document owner get view/change/delete on each note; shared document viewers get note view only"
  - "nested/views.py and nested/seed.py left unchanged: the default ancestor policy already fits the existing seed and keeps nested.md cv-sync blocks intact"
metrics:
  duration: ~10min
  completed: 2026-11-09
actuals:
  tokens: 7700
  tasks: 3
  commits: 3
plan_head_before: 50063d3d890020ecd9af37a4691efe0b9cd8118d
plan_head_after: 0cb0cb471be942090389edf04fa91f74007e6dc5
---

# Quick Task 261109-9rw: Update examples app for 06.18 ancestor authorization Summary

The examples app now has a Guardian `Note` ViewSet nested under `Document`. Its manage page reports `document (ancestor provider: guardian)` along with the Read view/view and Write change/view pairs. The seed gives alice and bob least-privilege note grants that exercise both ancestor gates. New tests also show that the core nested example (company -> department -> employee) still works for non-superusers with the existing seed.

## Tasks

| Task | Name | Commit | Key files |
| ---- | ---- | ------ | --------- |
| 1 (tracer) | Nested Guardian Note under Document end to end | fade2614 | guardian_demo/models.py, migrations/0003_note.py, views.py, urls.py, tests.py |
| 2 | Seed notes, German strings, Guardian feature text and docs table | b6a617f6 | guardian_demo/seed.py, tests.py, locale/de django.po/.mo, project/features.py, docs/reference/guardian.md |
| 3 | Core nested example under ancestor authorization | 0cb0cb47 | nested/tests.py, project/features.py |

## What was built

- **Note model** (document FK, author FK, text, created_dt, lazy translated names) with the generated `0003_note` migration. Ruff reformatted the migration file. No other edits were made to it.
- **cv_note** `GuardianViewSet(parent=ParentViewSet(name="document"))` with list, detail, create, update and delete views. `NoteForm` exposes only `text`. `CreateViewParentMixin` sets the document from the URL, and `cv_form_valid` sets the author. The author and the document owner then get view, change and delete on the note.
- **cv_document** declares `ancestor_policy=AncestorPolicy(provider="guardian", accept_global_perms=False)`. `DocumentTable` gains a `notes` child-link column.
- **Seed**: three notes, under Team Handbook and Release Checklist. The author and the document owner get full rights on each note. Shared document viewers get `view` only on that document's notes. Running the seed twice does not create duplicates.
- **Tests (+14, 409 -> 423 passed, 100 subtests)**:
  - `NoteAncestorTest` covers the Read/Write gates, server-side author/document, owner edit rights, the document and note manage pages, and a 403 on the nested manage page without a Document grant.
  - `GuardianSeedNotesTest` covers seed idempotency, bob reading but not adding notes, alice adding notes, independent note gates, and the German "Notizen" label.
  - `NestedAncestorAuthorizationTest` checks three cases: an editor passes, Department-only permissions get 403, and Company view alone reads but cannot write.
  - `NestedSeedTest.test_seeded_alice_passes_the_ancestor_gates` checks that the seeded alice passes the gates.
- **German catalog**: five new entries ("notes", "Notes" and the three note message templates). The `.mo` was recompiled with polib, and there are no untranslated or fuzzy entries.
- **Feature text and docs**: the Guardian and Nested feature texts are updated, with new DocRefs to `guardian.md#parent-viewsets` and `nested.md#ancestor-authorization`. The guardian.md Working Example has a new seeded-notes grant table.

## Verification

- `uv run pytest -c examples/bootstrap5/pytest.ini examples/bootstrap5 -q -p no:cacheprovider -n 4`: 423 passed, 100 subtests passed.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected.
- `ruff check` and `ruff format --check` are clean on the touched paths.
- `git diff --name-only HEAD -- src/` is empty, so no library code changed.
- Manual UAT for 06.18 test 2 is still pending. With the example server running (DEBUG=True), log in as alice and open `/guardian/document/manage/` and `/guardian/document/<Team Handbook pk>/note/manage/`.

## Deviations from Plan

None. The plan was executed as written.

The seed and `NoteCreateView` loop over a set `{author, document owner}`, so when the author owns the document the same grants are not assigned twice. This is the same behavior the plan describes, written compactly.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: examples/bootstrap5/guardian_demo/migrations/0003_note.py
- FOUND: fade2614, b6a617f6, 0cb0cb47 (all ancestors of HEAD)
