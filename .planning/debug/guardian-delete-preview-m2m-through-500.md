---
status: diagnosed
trigger: "guardian-delete-preview-m2m-through-500: Guardian delete preview (GET and confirming POST) on a root with cascade/protected models lacking a view_ Permission row (e.g. auto-created M2M through models such as Genre_publishers) renders without a 500: _PermittedPks fails closed per model (empty permitted set), covered by an M2M-root Guardian delete regression."
created: 2026-10-29T14:10:00Z
updated: 2026-10-29T14:45:00Z
goal: find_root_cause_only
---

## Current Focus

bug_class: Bohrbug (deterministic; reproduces every request, every actor incl. superuser)
hypothesis: CONFIRMED - _PermittedPks.__call__ hands guardian an app-qualified permission string f"{app_label}.view_{model_name}" derived from model._meta for every collected model; guardian.get_objects_for_user resolves that string (_get_ct_cached -> ContentType.objects.get(app_label, permission__codename)) and cross-checks it against guardian.ctypes.get_content_type(klass) BEFORE its superuser short-circuit, so any model whose string does not resolve to exactly one CT equal to guardian's CT for the model raises (DoesNotExist / MixedContentTypeError / MultipleObjectsReturned) and the delete preview 500s on GET and on the confirming POST.
test: done - probe_cr01_class.py (per-kind), test_cr01_probe.py (routes at HEAD), what-if shape-B plugin over routes + 275 existing guardian/delete tests
expecting: n/a
next_action: return ROOT CAUSE FOUND to orchestrator (goal find_root_cause_only); fix belongs to the gap-closure plan for G-06.2-1
known_pattern_candidate: none

reasoning_checkpoint:
  hypothesis: "Guardian delete preview raises because _PermittedPks resolves view_ permissions by an app-qualified string built from model._meta, which guardian must map to exactly one ContentType equal to its own content type for the model; auto-created throughs and restricted-default_permissions models have no such row (DoesNotExist), proxy roots and polymorphic children under a polymorphic GUARDIAN_GET_CONTENT_TYPE have it on a different CT (MixedContentTypeError), duplicate codenames give two CTs (MultipleObjectsReturned)."
  confirming_evidence:
    - "probe_cr01_class.py: Genre_publishers, ProbeNoView, ProbeProtNoView, S3FilePermissions -> ContentType.DoesNotExist; ProbePublisherProxy, Car(polymorphic base ctype) -> MixedContentTypeError; dup codename -> MultipleObjectsReturned; all for user, user+global and superuser"
    - "guardian 3.5.2 shortcuts.py: _compute_codenames_and_ctype/_compute_queryset run before `if with_superuser and user.is_superuser` -> superuser crash explained"
    - "core DeleteView.cv_filter_related_objects (user.has_perm, no obj) OK for every kind; ModelBackend set membership, guardian backend returns False for obj=None"
    - "what-if: passing the bare codename view_<guardian ct.model> with klass=model (guardian then derives ctype via get_content_type(klass), never _get_ct_cached) -> no raise for any kind/config; routes 200/302; 275 existing guardian+delete tests pass"
  falsification_test: "A model kind with a resolvable view_ permission on guardian's CT that still raises in _PermittedPks, or a kind lacking it that does not raise, would refute; none found across 11 kinds x 3 actors x 2 ctype configs."
  fix_rationale: "Root cause is the permission-string resolution contract, not the through model; resolving against guardian's own content type (bare codename + klass) or pre-checking existence on that CT removes every raise mode at the source instead of special-casing auto_created."
  blind_spots: "Shape-B global-perm semantics for proxies check view_<concrete> not view_<proxy>; get_for_model lazily INSERTs a ContentType row for auto-created throughs on first preview (no CT row exists after migrate) - write during GET, matters for read-only DB routers; superuser visibility of no-permission models is a product decision (core shows them); multi-db (permissions on non-default DB) not probed."
  candidate_causes:
    - "code: _PermittedPks builds app-qualified perm from model._meta with no precondition and no handling (CONFIRMED)"
    - "data/environment: Permission rows missing because create_permissions did not run / stale DB (same DoesNotExist path; covered by the same fix, not the repro cause - Publisher/Contract rows exist)"
    - "config: GUARDIAN_GET_CONTENT_TYPE set to polymorphic base ctype (contributing condition for the MixedContentTypeError variant only)"
    - "dependency: guardian 3.5.2 resolution order (ctype before superuser short-circuit) - documented behavior, not a guardian bug; explains superuser crash"
  and_gate: "yes, as trigger conditions not as independent root causes: (Guardian delete view) AND (cv_show_related_objects=True) AND (collector yields a model whose view_ string is unresolvable on guardian's CT). Single code root cause in _PermittedPks."

## Symptoms

expected: Guardian delete confirmation page (GET) and the confirming POST work for a Publisher that has a Genre (M2M) with cv_show_related_objects=True; models without a view_ permission row (auto-created M2M through models) simply contribute no permitted labels (fail closed), no 500.
actual: Code review CR-01 + verifier reproduced ContentType.DoesNotExist raised on GET and on the confirming POST, for a granted user and for a superuser, on the Guardian cascade delete route; core route returns 200 on the same shape. Pre-existing (same crash at fd25f4d), but phase 06.2 rewrote _PermittedPks and extended the lookup to protected objects.
errors: guardian.shortcuts.get_objects_for_user raises ContentType.DoesNotExist (permission app.view_<model> does not exist for auto_created through models)
reproduction: UAT Test 1. Probe script /tmp/claude-1000/-home-alex-projects-alex-django-crud-views/d63290b3-5144-443b-8488-22dcac3d5f40/scratchpad/probe_guardian_through.py (Publisher + Genre in tests/test1). See 06.2-REVIEW.md CR-01 and 06.2-VERIFICATION.md.
started: Pre-existing (reproduces at fd25f4d); discovered during code review / UAT of phase 06.2

## Eliminated

- hypothesis: crash depends on the actor's grants / the 06.2-02 inactive-actor guard
  evidence: superuser and user+global crash identically; raise occurs in guardian _compute_codenames_and_ctype before any user-specific query; inactive guard returns before the guardian call
  timestamp: 2026-10-29T14:24:00Z

- hypothesis: core (non-Guardian) delete preview shares the defect
  evidence: DeleteView.cv_filter_related_objects uses user.has_perm(perm) without obj; OK for all 11 probed kinds, user and superuser; core route 200 on Publisher+Genre
  timestamp: 2026-10-29T14:24:00Z

- hypothesis: tree crash is a 06.2 regression caused by removing the empty-tree shortcut
  evidence: tree always contains the root when cv_show_related_objects=True, so the fd25f4d shortcut never ran for real previews; verifier reproduced the GET crash at fd25f4d. Only the protected-list surface (4300f3d) is new.
  timestamp: 2026-10-29T14:28:00Z

- hypothesis: the review's proposed precheck (auto_created or no Permission on get_for_model(model, for_concrete_model=True)) covers the whole class
  evidence: probe_cr01_fixshapes.py - Car under GUARDIAN_GET_CONTENT_TYPE=polymorphic base still raises MixedContentTypeError (user and superuser); it also keeps the app-qualified string so the duplicate-codename MultipleObjectsReturned path remains (same string as current code, which raises in dup mode); proxy root is hidden even with a valid guardian grant
  timestamp: 2026-10-29T14:35:00Z

## Evidence

- timestamp: 2026-10-29T14:10:00Z
  checked: .planning/debug/knowledge-base.md
  found: does not exist; no MemPalace recall available in this session
  implication: no known-pattern candidate; proceed with open investigation

- timestamp: 2026-10-29T14:14:00Z
  checked: src/crud_views_guardian/lib/views.py:48-78 (GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects, _PermittedPks.__call__)
  found: _PermittedPks builds perm = f"{app_label}.view_{model_name}" for EVERY model met in related.tree (incl. the root) and in related.protected, and calls guardian.shortcuts.get_objects_for_user(user, perm, klass=model, accept_global_perms=...) with no precondition check and no exception handling. The only guard is the inactive-actor short-circuit.
  implication: correctness depends on an undeclared precondition: every collected model has a resolvable view_<model> Permission on the content type guardian uses for that model.

- timestamp: 2026-10-29T14:15:00Z
  checked: .venv guardian 3.5.2 shortcuts.py:48-50 (_get_ct_cached), :515-543 (_compute_codenames_and_ctype), :546-562 (_compute_queryset), :565+ (get_objects_for_user); Django 6.1.2
  found: get_objects_for_user FIRST calls _compute_codenames_and_ctype -> _get_ct_cached(app_label, codename) = ContentType.objects.get(app_label=..., permission__codename=codename) (raises DoesNotExist / MultipleObjectsReturned), THEN _compute_queryset which raises MixedContentTypeError when that ctype != guardian.ctypes.get_content_type(klass) (default ContentType.objects.get_for_model(model), for_concrete_model=True). The with_superuser short-circuit runs only AFTER both.
  implication: explains why the superuser crashes too; the failure is at permission-string resolution, before any user-specific logic. Two distinct raise sites: missing Permission row (DoesNotExist) and Permission on a different CT than guardian's model CT (MixedContentTypeError).

- timestamp: 2026-10-29T14:17:00Z
  checked: ran scratchpad test_cr01_probe.py at HEAD 196a6d3 (PYTHONPATH=repo, -p tests.test1.conftest)
  found: 4 passed - GET and confirming POST on /guardian_publisher_cascade/<pk>/delete/ raise ContentType.DoesNotExist for a user with a delete object grant (Publisher persists after POST); superuser GET raises too; core /publisher_cascade/<pk>/delete/ returns 200 on the same Publisher+Genre shape.
  implication: defect reproduced deterministically (Bohrbug). Core has_perm path is safe for the auto-created through model.

- timestamp: 2026-10-29T14:20:00Z
  checked: django/contrib/auth/management/__init__.py create_permissions; guardian backends.py has_perm/check_support
  found: create_permissions iterates app_config.get_models() (include_auto_created=False, include_swapped=False) and stores proxy perms on the proxy's own CT (get_for_models(for_concrete_models=False)); _get_all_permissions honours Meta.default_permissions. Guardian ObjectPermissionBackend.has_perm(obj=None) returns False via check_support; ModelBackend.has_perm is set membership (superuser -> True for any string).
  implication: auto-created throughs and restricted default_permissions models never get a view_ row; the core path (user.has_perm(perm), no obj) never resolves a Permission/ContentType row and cannot raise for any model kind.

- timestamp: 2026-10-29T14:24:00Z
  checked: scratchpad probe_cr01_class.py (runtime-defined models, in-memory DB) - _PermittedPks vs core has_perm per model kind, user / user+global / superuser
  found: RAISE ContentType.DoesNotExist (all three actors): Genre_publishers (auto_created through), ProbeNoView (default_permissions=("add","change","delete")), ProbeProtNoView (default_permissions=(), PROTECT -> protected list), S3FilePermissions (default_permissions=() + custom view_s3file; model_name-derived codename view_s3filepermissions absent). RAISE guardian.exceptions.MixedContentTypeError: ProbePublisherProxy (proxy root; view_ perm exists but on proxy CT, guardian default ctype is concrete CT); Car under GUARDIAN_GET_CONTENT_TYPE=polymorphic.contrib.guardian.get_polymorphic_base_content_type. OK: Publisher, Contract, explicit through, unmanaged (managed=False still gets perms), Vehicle, Car (default ctype), MTI parent. Core path OK for every kind (user False, superuser True).
  implication: the failing class is wider than "auto-created throughs": any model whose f"{app_label}.view_{model_name}" does not resolve, via guardian's _get_ct_cached, to exactly one CT equal to guardian.ctypes.get_content_type(model).

- timestamp: 2026-10-29T14:26:00Z
  checked: probe_cr01_class.py dup mode (ProbeDup with Meta.permissions=[("view_contract", ...)] in the same app)
  found: _PermittedPks(Contract) raises ContentType.MultipleObjectsReturned for user/global/superuser; core OK.
  implication: third raise mode from the same resolution step (exotic but legal: no Django check forbids it).

- timestamp: 2026-10-29T14:27:00Z
  checked: probe full hook on real collector output for Publisher(+Genre, ProbeNoView, ProbeUnmanaged, ProbeExplicitThrough, Contract, ProbeProtNoView)
  found: guardian hook raises on tree-only AND on protected-only input (user and superuser); core hook returns filtered tree/protected for both.
  implication: both projections (tree and protected) are affected.

- timestamp: 2026-10-29T14:28:00Z
  checked: git show fd25f4d:src/crud_views_guardian/lib/views.py; git log fd25f4d..HEAD (4300f3d feat(06.2-01) filter Guardian protected labels)
  found: pre-phase had `if not related.tree: return related` and passed protected unfiltered. With cv_show_related_objects the tree always contains the root, so the shortcut never prevented the tree crash. 4300f3d removed the shortcut and routed related.protected through the same _PermittedPks.
  implication: tree crash pre-existing since the guardian filter was introduced; protected crash (models with PROTECT/RESTRICT FKs and no view_ perm) is new surface from 06.2-01. Auto-created throughs cannot appear in protected (their FKs are CASCADE).

- timestamp: 2026-10-29T14:35:00Z
  checked: probe_cr01_fixshapes.py - review shape R vs guardian-ctype shape G, default and polymorphic-base GUARDIAN_GET_CONTENT_TYPE
  found: R: no raise under default ctype (proxy root fails closed even with a grant; superuser hidden for throughs); under polymorphic base ctype Car RAISES MixedContentTypeError. G (app-qualified perm derived from guardian.ctypes.get_content_type(model) + existence precheck): no raise in either config, proxy and polymorphic grants resolve.
  implication: the fix must resolve the permission against guardian's own content type for the model, not model._meta.

- timestamp: 2026-10-29T14:38:00Z
  checked: probe_cr01_bare.py - get_objects_for_user(user, f"view_{get_content_type(model).model}", klass=model) (bare codename; documented when klass is given), incl. dup-codename mode
  found: no raise for any kind under either ctype config, nor for the duplicate codename; non-superuser gets [] for no-permission models (fail closed), superuser gets all pks (parity with core has_perm), inactive superuser gets all (already pre-empted by _PermittedPks inactive guard).
  implication: a bare codename lets guardian derive ctype from klass and skips _get_ct_cached entirely - removes all three raise modes at the source.

- timestamp: 2026-10-29T14:40:00Z
  checked: probe_cr01_ct.py - ContentType rows for auto-created through after migrate
  found: no CT row exists for Genre_publishers after migrate; guardian.ctypes.get_content_type (ContentType.objects.get_for_model) creates it on first call.
  implication: any get_for_model-based fix (review R and shape B/G) performs a ContentType INSERT on the first preview per through model; benign get_or_create but a write on GET (read-only router consideration). Short-circuiting opts.auto_created before any CT lookup avoids it.

- timestamp: 2026-10-29T14:43:00Z
  checked: what-if scratchpad pytest plugin cr01plug/cr01_shape_b_plugin.py (monkeypatch only, no repo change) over test_cr01_shape_b_routes.py and tests/test1/test_*guardian*.py + test_*delete*.py
  found: routes - granted GET 200 with has_protected_objects True, protected_objects [] and no Contract/through label; POST without PROTECT 302 + Publisher deleted; superuser GET 200. Existing suites: 275 passed.
  implication: fix direction is compatible with the 06.2 protected/notice contract and existing Guardian behavior.

- timestamp: 2026-10-29T14:44:00Z
  checked: src/crud_views_guardian/lib/mixins.py:182-195 (GuardianQuerysetMixin.get_queryset), lib/viewset.py:89-108 (GuardianViewSet.get_objects_for_user)
  found: both call guardian with cv_viewset.permissions[...] (app-qualified, the ViewSet's own model), not arbitrary collected models.
  implication: outside the CR-01 class; would only share the MixedContentTypeError risk for a proxy-model (or polymorphic-base-ctype child) GuardianViewSet. Note for Phase 7, not part of this fix.

## Resolution

root_cause: "crud_views_guardian _PermittedPks.__call__ (src/crud_views_guardian/lib/views.py:68-78) resolves view permissions for EVERY model in the delete collector's tree and protected list by passing the app-qualified string f\"{app_label}.view_{model_name}\" (built from model._meta) to guardian.shortcuts.get_objects_for_user. Guardian 3.5.2 resolves that string via _get_ct_cached -> ContentType.objects.get(app_label=..., permission__codename=...) and then requires the result to equal guardian.ctypes.get_content_type(klass), both BEFORE its superuser short-circuit. Models that do not satisfy that hidden precondition raise and the Guardian delete preview 500s on GET and on the confirming POST (DeleteView.post calls get_context_data first) for every actor: (1) no view_ Permission row -> ContentType.DoesNotExist: auto-created M2M through models (Django's create_permissions skips auto_created), models whose Meta.default_permissions omits 'view' (incl. ()), or DBs where permissions were never created; (2) view_ row on a different CT than guardian uses -> MixedContentTypeError: proxy-model roots (perm on proxy CT, guardian default ctype is concrete), polymorphic child models when GUARDIAN_GET_CONTENT_TYPE is the polymorphic base ctype; (3) duplicate codename in the app -> MultipleObjectsReturned. Tree path pre-existing (fd25f4d); 06.2-01 (4300f3d) extended it to the protected list. Core path (user.has_perm without obj) never resolves rows and is safe for all kinds."
fix: ""
verification: ""
files_changed: []
suggested_fix_direction: "In _PermittedPks, resolve against guardian's own content type: ct = guardian.ctypes.get_content_type(model); call get_objects_for_user(user, f\"view_{ct.model}\", klass=model, ...) with the BARE codename (documented when klass is given; guardian then skips _get_ct_cached), which removes all three raise modes; non-superusers get an empty set for no-permission models (fail closed), superusers get parity with core. Optionally short-circuit opts.auto_created before any ContentType lookup to avoid the lazy ContentType INSERT on GET (decide superuser visibility for that branch explicitly). Regression: Guardian cascade delete of a Publisher with a Genre (GET, modal GET, confirming POST without Contract; user with delete grant and superuser) plus a protected model without a view_ permission if the fixture set allows."
