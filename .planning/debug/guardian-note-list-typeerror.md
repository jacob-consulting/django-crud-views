---
status: resolved
trigger: "guardian-note-list-typeerror: The nested Guardian Note example (/guardian/document/<pk>/note/) renders, and its manage page shows the declared ancestor policy (Guardian provider, fallback) without the removed cv_guardian_parent_* fields. User reported: TypeError at /guardian/document/1/note/ 'NoneType' object is not iterable"
created: 2026-11-09T09:15:00Z
updated: 2026-11-09T09:42:00Z
---

## Current Focus

bug_class: Bohrbug (deterministic; reproduces every time on the unmigrated DB copy)
hypothesis: CONFIRMED H1 — the user's examples/bootstrap5/db.sqlite3 has guardian_demo.0003_note unapplied, so no auth_permission rows exist for guardian_demo.note; GuardianViewSet.default_permissions returns an empty OrderedDict, GuardianQuerysetMixin.get_queryset does permissions.get("view") -> None and passes None to guardian get_objects_for_user, which iterates it -> TypeError.
test: done — (a) 0 note permission rows; (b) 200 after migrate+seed; (c) deleting only view_note on a migrated copy reproduces the TypeError, restoring gives 200
expecting: n/a
next_action: return ROOT CAUSE FOUND (goal: find_root_cause_only)
candidate_causes:
  - "environment/data: live example DB not migrated after 0003_note (confirmed)"
  - "code: unguarded vocabulary lookup in Guardian local gates turns a missing key into None (confirmed)"
  - "code: 8b11572a default_permissions change (eliminated)"
  - "code: 06.18 ancestor guard on nested Guardian list (eliminated)"
and_gate: "yes — the opaque TypeError needs both the missing Note permission rows (trigger) and the unguarded permissions.get(...) -> get_objects_for_user(None) (mechanism); with the DB migrated the page is 200, with a guard the stale DB would raise a named configuration error instead"

## Symptoms

expected: Start the example app (examples/bootstrap5) logged in as alice. /guardian/document/<pk>/note/ lists the document's notes; /guardian/document/manage/ and /guardian/document/<Team Handbook pk>/note/manage/ show the declared ancestor policy.
actual: User reported: "I cannot check that because in the example app nested guardian example is broken: TypeError at /guardian/document/1/note/ 'NoneType' object is not iterable"
errors: TypeError at /guardian/document/1/note/ — 'NoneType' object is not iterable
reproduction: UAT test 2. Example added by quick task 261109-9rw (fade2614, b6a617f6, 0cb0cb47). Example tests passed (423). Reproduce with Django test client or dev server against examples/bootstrap5.
started: Discovered during UAT of phase 06.18 after quick tasks 261109-9rw, 261109-bf5 (8b11572a default_permissions change), 261109-bvq (docs only).

## Eliminated

- hypothesis: H3 — commit 8b11572a (core ViewSet.default_permissions content_type read) returns None / a wrong vocabulary for the Guardian Note viewset
  evidence: cv_note is a GuardianViewSet whose default_permissions override (crud_views_guardian/lib/viewset.py:120) does not call the core implementation; the bf5 diff only swaps permission.content_type for the identical local content_type; the page returns 200 on a migrated DB with 8b11572a in place
  timestamp: 2026-11-09T09:34:00Z

- hypothesis: H2 — 06.18 ancestor-authorization code (guard, _check_nested_auth, Note policy wiring) breaks the nested Guardian list on any DB
  evidence: migrated + seeded copy returns 200 for every Note/Document page as alice; ancestor gate succeeds on the unmigrated DB (traceback is past dispatch, inside the local get_queryset); unguarded line predates 06.18 (0942186e, 2026-04-24)
  timestamp: 2026-11-09T09:34:00Z

## Evidence

- timestamp: 2026-11-09T09:20:00Z
  checked: .planning/debug/knowledge-base.md
  found: does not exist; no prior pattern match
  implication: no known-pattern candidate

- timestamp: 2026-11-09T09:22:00Z
  checked: running processes; examples/bootstrap5/db.sqlite3 (copied to scratchpad, read-only for the original)
  found: user's dev server is `manage.py runserver 9000` (pid 8574, started 08:59) on the main checkout against examples/bootstrap5/db.sqlite3. Migration plan on that DB lists unapplied guardian_demo.0003_note (plus custom_form/delete_demo/disabled_actions/flash_messages/formsets_conditional/label_modes 0001). Table guardian_demo_note does not exist. Documents 1 Roadmap 2027 (alice), 2 Team Handbook (alice), 3 Meeting Notes (bob), 4 Release Checklist (bob).
  implication: the live server runs the new Note code against a DB without Note's migration/permissions

- timestamp: 2026-11-09T09:25:00Z
  checked: Django test client GET /guardian/document/1/note/ as alice against scratchpad copy of the user's DB (raise_request_exception=True)
  found: reproduced. TypeError: 'NoneType' object is not iterable at guardian/shortcuts.py:526 _compute_codenames_and_ctype `for perm in perms`, called from crud_views_guardian/lib/mixins.py:251 get_queryset -> get_objects_for_user(self.request.user, perm, qs, ...), where perm = self.cv_viewset.permissions.get(self.cv_permission) (line 250). /guardian/document/ returns 200.
  implication: ancestor gate (Document) passed; the failure is in the local Note list filter with perm=None

- timestamp: 2026-11-09T09:27:00Z
  checked: git show 8b11572a; GuardianViewSet.default_permissions (src/crud_views_guardian/lib/viewset.py:120)
  found: 8b11572a only edits core ViewSet.default_permissions (reads content_type.model/app_label from the local content_type instead of permission.content_type — same object, same values). GuardianViewSet overrides default_permissions entirely (guardian.ctypes.get_content_type) and was not touched. Both implementations return an empty OrderedDict (not cached, #151) when no Permission rows exist.
  implication: 8b11572a is not on the Note request path and cannot produce None; the None comes from dict.get on an empty vocabulary

- timestamp: 2026-11-09T09:30:00Z
  checked: fresh copy of the user's DB — django_content_type / auth_permission / django_migrations for guardian_demo
  found: ContentType guardian_demo.note exists (id 41, created lazily by a get_for_model call from the running server), but auth_permission has only add/change/delete/view_document — zero rows for note. django_migrations has guardian_demo 0001, 0002 only.
  implication: GuardianViewSet.default_permissions for cv_note is an empty OrderedDict -> permissions.get("view") is None (H1 prediction (a) confirmed)

- timestamp: 2026-11-09T09:33:00Z
  checked: scratchpad copy migrated (`manage.py migrate` applied custom_form/delete_demo/disabled_actions/flash_messages/formsets_conditional 0001, guardian_demo.0003_note, label_modes 0001) and seeded; GET as alice
  found: /guardian/document/1/note/, /guardian/document/2/note/, /guardian/document/4/note/, /guardian/document/manage/, /guardian/document/2/note/manage/ all 200. User's original db.sqlite3 mtime unchanged (09:00:14).
  implication: H1 prediction (b) confirmed; nothing in the 06.18 code breaks the page on a migrated DB

- timestamp: 2026-11-09T09:36:00Z
  checked: single-variable isolation on the migrated copy — delete only Permission view_note (table and 3 note rows present), fresh process, GET /guardian/document/2/note/; then restore the migrated copy and repeat
  found: without view_note -> identical TypeError 'NoneType' object is not iterable; restored -> 200
  implication: the TypeError is produced by the missing "view" vocabulary key alone (not the missing table): code mechanism = unguarded `permissions.get(cv_permission)` -> None passed to guardian.shortcuts.get_objects_for_user

- timestamp: 2026-11-09T09:38:00Z
  checked: unmigrated copy — other Note pages as alice
  found: /guardian/document/manage/, /guardian/document/2/note/manage/, /guardian/document/2/note/create/ return 200; only the note list (local Guardian queryset filter) fails
  implication: the list's local gate is the first code that needs the Note vocabulary

- timestamp: 2026-11-09T09:40:00Z
  checked: git blame src/crud_views_guardian/lib/mixins.py; other `permissions.get(` sites
  found: mixins.py:250 (GuardianQuerysetMixin.get_queryset), :100 (GuardianObjectPermissionMixin.get_object) and :113 (cv_has_access) all date from 0942186e (2026-04-24) and pass a possibly-None perm onward (get_objects_for_user / perm.split). By contrast core CrudViewPermissionRequiredMixin.cv_has_access (view/base.py:1221) returns False on a missing key, and the 06.18 ancestor guard `_permission_name` (ancestors.py:385) raises ImproperlyConfigured naming the key and ViewSet. GuardianViewSet._resolve_permission_key raises ValueError listing valid keys.
  implication: latent, pre-06.18 defect in the Guardian local gates — not introduced by 06.18 or 9rw/bf5 — newly exposed because 9rw added a model whose migration the live DB never received

- timestamp: 2026-11-09T09:41:00Z
  checked: process list; examples/bootstrap5/taskfile.yaml; 261109-9rw SUMMARY; guardian_demo/tests.py
  found: running server was started 08:59 as `uv run .venv/bin/python manage.py runserver 9000` (not `task run`, which runs migrate + seed first and binds 0.0.0.0:9000). The 9rw SUMMARY / UAT test 2 never instruct migrate + seed. Example tests (NoteAncestorTest lines 96/107, GuardianSeedNotesTest) GET note-list on a pytest-django test DB built from all migrations, where post_migrate creates the Note permissions -> 200.
  implication: tests cannot see a stale developer DB; the defect is environmental trigger + unguarded code

## Resolution

root_cause: "AND-gate (two contributing causes): (1) environment/data — the user's running example server (manage.py runserver 9000 started without `task run`) uses examples/bootstrap5/db.sqlite3 on which guardian_demo.0003_note (added by 9rw fade2614) was never applied, so post_migrate never created auth_permission rows for guardian_demo.note; (2) code — GuardianQuerysetMixin.get_queryset (src/crud_views_guardian/lib/mixins.py:250) does `perm = self.cv_viewset.permissions.get(self.cv_permission)` without checking the result, so an empty Guardian vocabulary yields perm=None, which is passed to guardian.shortcuts.get_objects_for_user and fails as an opaque TypeError ('NoneType' object is not iterable at guardian/shortcuts.py:526) instead of a clear configuration error. Same unguarded pattern at mixins.py:100 and :113. Pre-existing since 0942186e (2026-04-24); not caused by 06.18, 9rw view code, or 8b11572a."
fix: (diagnose-only)
verification: (diagnose-only)
files_changed: []
