I'll review the nine plans against the live deletion, Guardian, and lifecycle source, not only the plan prose.
The current delete path still collects through `NestedObjects` and classifies protection from tracebacks. I'll check the write lifecycle, Guardian cache, and the templates those plans change.
Repo access was used. This review does not satisfy DEL-01.

## 06.3-01

### Summary
Wave 1 correctly blocks implementation on a human design approval and a separate package-install decision. The automated checks only prove a record file exists.

### Strengths
- `depends_on: []` and later plans depend on `06.3-01`, matching DEL-01/D-16. Task type `checkpoint:decision` refuses inferred approval.
- The approval check binds `06.3-APPROVAL.md` to the SHA-256 of `06.3-DESIGN.md`, so a silent design edit fails the record check.
- Package verification stays separate from cached 4.2/6.0 use. `noxfile.py:3-14` is the real 5.2 install path, and the plan does not relabel the SUS audit.

### Concerns
- **MEDIUM:** The digest covers `06.3-DESIGN.md` only. Revising a plan after approval still passes the automated check.
- **MEDIUM:** `decision: approved` / `decision: verified` can be written without a maintainer. The plan says so, but the gate is social, not technical.
- **LOW:** 01-02 does not list the resolved nox set (`django~=5.2.0` plus `.[polymorphic,workflow,ordered,test]` from `noxfile.py:13-14`). Extra resolved packages can stay ASSUMED.

### Suggestions
Record hashes of all nine plans, or a manifest, in `06.3-APPROVAL.md`. Have 01-02 paste the dry-resolved install set before verification.

### Risk Assessment
Medium. The checkpoint is the right shape. It does not by itself freeze the executable tasks.

## 06.3-02

### Summary
The tracer targets the real CR-02 seam: `get_context_data` always calls `cv_get_related_objects` (`src/crud_views/lib/views/delete.py:309`), which builds `NestedObjects` and calls `collect` (`delete.py:212-214`). Django then runs callable `SET` inside `on_delete` (`django/db/models/deletion.py:52-56`). That diagnosis is right. The task split is not yet executable without breaking `tests/test1/test_delete.py`.

### Strengths
- Callback-event proof is required, not row survival. That matches `cv_form_valid` calling `delete_method()` with no `using` (`delete.py:371-375`) only after context collection has already run.
- Re-export of `RelatedObjects` keeps `src/crud_views_guardian/lib/views.py:49` working.
- Invalid confirmation stays on `cv_form_invalid_hook` (`delete.py:355-357`). Custom protection still returns before `cv_form_valid_process` (`delete.py:344-348`).

### Concerns
- **HIGH:** 02-01's acceptance requires the private marker as the only friendly late block, but 04 owns removal of `_cv_is_target_collection_protection` (`delete.py:97-126`). Tests still import that function (`tests/test1/test_delete.py:1143-1394`). 02's verify runs that file.
- **HIGH:** `_delete_probe` replaces `cv_get_related_objects` with an empty tuple (`tests/test1/test_delete.py:789-796`) so write-path tests can run while a protector exists. 02-02 says to stop honoring that override, but does not name a replacement seam. Real inspection would set `has_protected_objects` and return the protection response (`delete.py:344-348`) before those tests reach `cv_form_valid`.
- **HIGH:** `test_delete_success_real_commit_order` patches `delete(self)` with no `using` (`tests/test1/test_delete.py:1078-1086`). 02 calls `delete(using=...)`. The verify file goes red for a reason the action does not name.
- **MEDIUM:** The incomplete notice is tasked "outside the custom-protection branch", but `view_delete.content.html:5-12` also skips the snippet unless `related_summary or has_protected_objects`. Preview-off with no blocker never includes `related_objects.html`. A notice only in the snippet misses D-03.
- **MEDIUM:** 02-02 requires a confirmed positive call of private `bulk_related_objects` (`deletion.py:368-374`), while 02-01 only builds a CASCADE/PROTECT seam. That write behavior is 04's collector.

### Suggestions
In 02, keep the legacy override callable and the old classifier in place. Add new real-preview tests beside them. Move override rejection, `delete(using=)` signature failure, and classifier deletion into the task that rewrites `test_delete.py`. Name `view_delete.content.html:8` as a required render site for the incomplete flag.

### Risk Assessment
High. The defect is real. This wave can go red or pass by leaving the unsafe override path alive.

## 06.3-03

### Summary
Graph rules match the needed split: identity checks, no handler calls, RESTRICT only after supported cascade closure, and completeness stored outside the three-field tuple that filters reconstruct (`delete.py:33-36`, `delete.py:275-302`, `views.py:48-56`).

### Strengths
- Provider merge-before-filter preserves the current rule that `has_protected_objects` is set before `cv_filter_related_objects` (`delete.py:311-313`). A filter cannot clear a block.
- Legacy collection overrides are rejected before invocation. That matches D-06 and avoids sampling an unknown override.
- Notice tests cover details on/off, both gates, both response modes, escaping, and German catalogs. `related_objects.html:4-9` already has the hidden-label blocked sentence; the plan keeps that independent.

### Concerns
- **HIGH:** Runtime `ImproperlyConfigured` on any other `cv_get_related_objects` makes every `_delete_probe` test raise once 03 lands. 03's verify does not run `test_delete.py`. 04 is the first later plan that must repair it. Wave 3 leaves the deletion suite red.
- **MEDIUM:** 03-02's `-k 'notice or count or german or template'` can pass on an unrelated match and skip the combination matrix.
- **MEDIUM:** The action does not require the provider to run when `cv_show_related_objects` is false. If it does not, a provider blocker never sets the flag that omits the form (`view_delete.content.html:12`).
- **MEDIUM:** Inspection RESTRICT lives here; write-side RESTRICT lives in 04's forked collector. Nothing forces one shared closure function, so preview and delete can disagree.
- **LOW:** `delete_protection_errors` still takes the `if` branch (`view_delete.content.html:5-7`) and hides the native snippet. D-12 is met for the incomplete notice only if that notice is outside this `if`.

### Suggestions
Add a preview-off provider call assertion. Share one RESTRICT closure helper with 04. Either keep override detection dark until `test_delete.py` is migrated, or migrate those nodes in 03.

### Risk Assessment
High, because of the suite break, not because the provider contract is wrong.

## 06.3-04

### Summary
This is the plan that can actually fix CR-03. Django catches `ProtectedError` around `on_delete` and raises a new aggregated error (`deletion.py:347-362`), so the traceback test at `delete.py:97-126` cannot tell a nested converter from native PROTECT. Replacing that with an origin marker is the right mechanism.

### Strengths
- Query evaluation stays outside the translation catch. Native SQL stays `Collector.delete()`. Custom `Model.delete`, hooks, and `on_commit` stay uncaught. That matches `mixins.py:54-57` and `delete.py:349-353`.
- Stale protection must be inserted after a real inspector, not via `_delete_probe`'s empty tuple (`test_delete.py:796`).
- Both atomic modes use `transaction=True` and external event lists. `cv_atomic` false is `nullcontext()` (`base.py:244-245`), so rollback-only assertions would lie.
- Sticky `custom_callback_entered` matches the case where a handler returns and a later native block must not become a friendly 200.

### Concerns
- **HIGH:** 04 is the third owner of `deletion.py` / `test_delete.py` after 02 and 03 have already been told to change the same contracts. Provenance tests cannot start from a green file unless 02/03 were narrowed.
- **MEDIUM:** The action never says `SET_NULL` / `DO_NOTHING` are non-sticky. `SET_NULL` is a real function (`deletion.py:69`). If it sets the sticky flag, a later native PROTECT in the same graph propagates. That regresses DEL-03.
- **MEDIUM:** No positive test that a confirmed POST still invokes `bulk_related_objects` (`deletion.py:368-374`) and deletes those rows. Inspection-only tests can pass while generic relations are skipped on write.
- **MEDIUM:** Verify is 6.0-only and `-k` filtered. 4.2/5.2 collector drift waits until 09. 5.2 is not installed yet (`noxfile.py:3-8`); comparison must use upstream source, which the action allows, but parity is not executed.
- **LOW:** `keep_parents` is in the design and in `Model.delete` (`base.py:1291-1300`) but not in 04's behavior list. The view never passes it; polymorphic upcasting is out of scope.

### Suggestions
Add one mixed `SET_NULL`+`PROTECT` friendly case and one confirmed generic-relation deletion. Make 04 the only plan that deletes `_cv_has_native_collection_graph` and rewrites `test_delete.py:1143-1394`.

### Risk Assessment
High. The design is sound and the fork of `Collector.collect` is the phase's real maintenance hazard.

## 06.3-05

### Summary
CR-04 is visible in source. Preview routes with `router.db_for_write(self.object._meta.model)` and no instance (`delete.py:212`). The write phase uses `router.db_for_write(self.cv_viewset.model)` (`base.py:233-235`). `Model.delete` uses the instance hint (`base.py:1297-1299`). Guardian caches permitted PKs by model only (`views.py:72-93`) and loads auto-created rows through `_default_manager` (`views.py:81`).

### Strengths
- `shard` must be added in `pytest_configure` before `django.setup()` (`tests/test1/conftest.py:91-121`). No `TEST.MIRROR`.
- Asymmetric colliding PKs, one selector call after PK clear, and commit timing on both connections match the pin design.
- Fail-closed labels if Guardian cannot enforce co-located auth is safer than implying cross-database grants.
- Create/update routing stays on `base.py:233-246`. The plan forbids solving this by editing the shared mixin.

### Concerns
- **MEDIUM:** Acceptance says two-alias requests prove label authorization. The action allows fail-closed instead. An executor can satisfy the action and miss DEL-05.
- **MEDIUM:** No router restore. `DATABASE_ROUTERS` is process-global. 07 and 09 (`pytest -n auto` in `noxfile.py:19`) then inherit a leaked router.
- **MEDIUM:** 05 depends on 06, then edits `src/crud_views_guardian/lib/views.py`. A GUA-01 scope escalation does not stop that edit.
- **LOW:** No negative test that a request parameter cannot choose the alias.
- **LOW:** Unclassified DEL-04 stays flagged. Correct. Do not treat this topology as general multi-database Guardian support.

### Suggestions
Require a same-alias reveal and an other-alias non-reveal, and return to the orchestrator if Guardian cannot do that. Restore routers in `finally`. Do not start 05-02 while `06.3-GUARDIAN-REVIEW.md` has an open redesign.

### Risk Assessment
Medium. The routing bug is correctly scoped. The Guardian topology is the part most likely to be waived.

## 06.3-06

### Summary
IN-02 and IN-03 match the code. `STRICT_HELPER_POLICY` is a mutable dict (`viewset.py:11`) read on each call (`viewset.py:106-107`). `get_objects_for_user` returns `qs.none()` before the key lookup (`viewset.py:99-104`). `assign_perm` / `remove_perm` already index `self.permissions[perm]` first (`viewset.py:81-87`). Manage copies the mapping with `dict(...)` (`views.py:296`), which still works for a proxy.

### Strengths
- Validate configured keys, not a hardcoded CRUD list. `ViewSet.permissions` can be customized (`viewset.py:473-476`).
- Inactive valid queries stay empty. Invalid keys raise before assign/remove. That is D-09–D-11.
- `MappingProxyType` must not expose the backing dict. The action states the real pitfall: a proxy is a view, not a copy.
- Residual AUTH-06 stays open until a scenario ledger exists. Passing the existing 47 policy tests is explicitly not closure.

### Concerns
- **HIGH:** 06-02's automated command never reads `06.3-GUARDIAN-REVIEW.md`. Pytest can pass with no IN-02, IN-03, or AUTH-06 disposition. GUA-01's deliverable is that ledger.
- **MEDIUM:** The precision truth is a YAML mapping inside a string list. A plan parser can drop the only backstop for lossy key/PK coercion.
- **MEDIUM:** `KeyError` becomes `ValueError`. Callers of `assign_perm` that catch `KeyError` change behavior. 08 is not told to mark that as Breaking.
- **LOW:** `permissions` may query `auth.Permission` (`viewset.py:448-467`). Validating before the inactive shortcut adds that query. Acceptable, but it is a behavior change for the invalid inactive path.

### Suggestions
Assert the review file contains separate IN-02, IN-03, and AUTH-06 entries with `disposition:` before pytest is treated as done. Fix the precision YAML. Name the exception-type change in 08's Breaking list.

### Risk Assessment
Medium for the helper fix. High for false closure of the residual flag if the ledger gate stays prose-only.

## 06.3-07

### Summary
Authorization preservation is aimed at the right seams: method guard before object lookup (`delete.py:139-141`), label filtering after projection, and polymorphic deletion that is not `Model.delete`. Installed `PolymorphicModel.delete` accepts `using` and calls `super().delete(using=using)` (`polymorphic/models.py:244-276`).

### Strengths
- Existing `test_delete_vehicle` (`tests/test1/test_polymorphic.py:163-174`) only checks 302 and row absence. `Model.delete` would also remove parent and child rows, so that test cannot detect a bypass. 07-02 requires a spy and signal origin.
- Context inspection, not only HTML, blocks a custom template from recovering hidden instances.
- HTTP DELETE replay stays on the guard. The 405 test at `test_polymorphic.py:178-191` is necessary and not sufficient, which the plan says.

### Concerns
- **MEDIUM:** Native PROTECT on a polymorphic target is friendly only at preview time. The write path calls `PolymorphicModel.delete`, which builds Django's `Collector` (`base.py:1297-1300`) and raises aggregated `ProtectedError`. The design says that exception propagates. A stale protector added after inspection becomes a 500, not the 200/422 backstop. 07 does not lock that outcome. A later catch around the custom call would reopen CR-03.
- **MEDIUM:** `-k delete` already selects `test_delete_vehicle`. The verify command can pass without the new transaction/spy nodes.
- **LOW:** `test_authorization_matrix.py` is in the verify command and not in `files_modified`. It currently only asserts `has_protected_objects` (`test_authorization_matrix.py:738`). Low conflict risk.

### Suggestions
Add one polymorphic stale-PROTECT test that expects propagation, not a friendly block. Point the verify command at the new node ids.

### Risk Assessment
Medium. Preservation is well aimed. The polymorphic/native split needs an explicit locked outcome so it is not "fixed" later.

## 06.3-08

### Summary
Docs still prescribe the unsafe contract: `NestedObjects` on every context (`docs/reference/delete_view.md:195-203`) and the same override story in `docs/migrating-1.0.md:487-489`. Replacing those claims and executing the published fences is required for DEL-06 and D-08.

### Strengths
- Recipes must be extracted from the published pages and executed, not copied into the test. That is the right bar.
- Copied-template cases include preview-off and hidden labels, which is where `view_delete.content.html:8` drops the snippet.
- Breaking notes are paired with `docs/migrating-1.0.md`. Guardian topology must be described as limited.

### Concerns
- **MEDIUM:** "Extract the fences from these pages" will also pick up the existing filter sample at `delete_view.md:221-231`, which calls `obj.is_archived` and is not a migration recipe. A naive extractor fails or skips real recipes.
- **MEDIUM:** Replacing the collection section can drop the cost warning at `delete_view.md:193-198`. The new inspector still materializes rows. The action does not require that warning to survive.
- **LOW:** Invalid-key `ValueError` is documented, but not explicitly as Breaking relative to today's `KeyError` at `viewset.py:104`.

### Suggestions
Mark migration fences with stable headings and extract only those. Keep a "no large-cascade bound" paragraph. Add the `KeyError` to `ValueError` Breaking bullet.

### Risk Assessment
Medium. The documentation task is fit. Extraction scope is the likely false failure or false pass.

## 06.3-09

### Summary
The matrix plan is the right close: cached 4.2/6.0, a real 5.2 session, docs, JS, ruff, and a fresh acceptance map. It must not treat this review or old green suites as DEL-06 evidence.

### Strengths
- Main-venv Django 6.1.2 is excluded. The 5.2 session name matches `noxfile.py:6-8`.
- Full `tests/test1` on cached envs keeps only the existing crispy-floor deselection.
- Unclassified probes and descriptor-less prohibitions stay unresolved until a human review. That matches the design's spec-less flags.
- Defects found here are sent back to owning plans instead of being patched in the evidence files.

### Concerns
- **HIGH:** The automated command is `nox -r --no-install -s "tests-3.12(django='5.2')"`. `--no-install` does not provision. The action's install command is not the verify command. If only the verify block runs, 5.2 never appears and the gate fails for the wrong reason, or a pre-existing env is reused without the 01-02 check.
- **MEDIUM:** 09-02's pytest command does not read `06.3-ACCEPTANCE.md` or `06.3-MATRIX.md`. The handoff can be missing while the command is green. The human-check is the only control.
- **MEDIUM:** `nox -r` plus `pytest -n auto` (`noxfile.py:19`) will amplify a router or signal leak from 04/05. The matrix truth says jobs must not clobber each other, but the plan does not isolate xdist workers from process-global routers.
- **LOW:** 09 re-runs mkdocs and the policy module already run in 06 and 08. Harmless, not proof of the new deletion nodes on 4.2 until the full loop is actually recorded.

### Suggestions
Split verify into "session exists and Django version is 5.2" after an explicit install step that refuses to run without `decision: verified`. Assert required headings in `06.3-MATRIX.md` and `06.3-ACCEPTANCE.md`.

### Risk Assessment
Medium as a gate, high if `--no-install` is treated as the provisioning step.

## Cross-plan conclusions

The design matches the code. CR-02 is `NestedObjects.collect` during `get_context_data` (`delete.py:212-214`, `delete.py:309`) before confirmation. CR-03 is aggregated `ProtectedError` (`deletion.py:347-362`) plus the traceback classifier (`delete.py:97-126`). CR-04 is three routers: preview without instance (`delete.py:212`), lifecycle without instance (`base.py:233-235`), and `Model.delete` with instance (`base.py:1297`). IN-02/IN-03 match `viewset.py:11` and `viewset.py:99-104`. Guardian label identity is model-only at `views.py:77-93`.

The package is not ready to execute as sequenced.

1. **HIGH — one file, three incompatible contracts.** `tests/test1/test_delete.py` still depends on the override, the classifier, and `delete(self)`. 02 removes the first two in acceptance text, 03 raises on the override, and 04 is the plan that can honestly replace them. Collapse that migration into 04, or rewrite the file once in 02 and stop later plans from assuming the old helpers exist.
2. **HIGH — false closure gates.** 06-02 and 09-02 do not assert their evidence files. GUA-01 and DEL-06 can look automated while the ledger is absent.
3. **MEDIUM — notice placement.** `view_delete.content.html:5-12` will hide an incomplete notice placed only in the snippet whenever there is no summary and no blocker. 02 and 03 must name that predicate.
4. **MEDIUM — collector fork.** 02, 03, and 04 each write `deletion.py`. SET_NULL must stay non-sticky. Private bulk relations must still delete on confirmed POST (`deletion.py:368-374`). Polymorphic stale PROTECT will propagate; lock that, do not catch it.
5. **MEDIUM — 5.2 and approval scope.** Install is human-gated, then the verify command skips install. Approval hashes the design, not the plans.

No production code should change until a maintainer records approval against the revised package. This review is not that approval.
