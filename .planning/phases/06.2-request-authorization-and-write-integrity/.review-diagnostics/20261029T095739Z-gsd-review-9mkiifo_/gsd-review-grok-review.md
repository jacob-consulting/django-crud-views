I'll verify H03 and A18–A21 against the revised plans and the current source, without treating unfixed code as a plan defect.
Plans are at `bb2b609`. I'll read the caller, DELETE, fragment, and manage seams the remedies claim to close.
## 06.2-01

Summary: DELETE rejection and protected-preview projection stay owned here, including the restored-method Allow/OPTIONS fix.

Strengths: `01:101` filters DELETE out of Django's shared `_allowed_methods` (`django/views/generic/base.py:147`, `:166`, `:181`), so a restored `delete` name cannot advertise DELETE while `delete()` still rejects it. `01:131` patches a fresh `http_method_names` list on already-registered classes and restores it with pytest teardown, so the subclass assertion does not mutate the inherited list or register a second route. Both preview templates remain owned (`view_delete.content.html:8`, `related_objects.html:4`).

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Header truthfulness and handler rejection are one hook; pre-dispatch gates stay first.

## 06.2-02

Summary: H03 is closed for the FK caller contract. Guardian create resolves an actual parent or an own-child's configured FK, and denies unrelated types, on both permission and state paths.

Strengths: `02:107` resolves `cls.cv_viewset.model` through `ParentViewSet.get_attribute()` (`parentviewset.py:62-66`) and keeps `cv_has_access(None)` false so the list override (`mixins.py:145-155`) still checks the URL parent. `02:136` adds `_cv_action_enabled_for_context`, defaulting to `cv_action_enabled`, and routes `_cv_get_action_context` (`base.py:707`), ContextButton sites (`buttons.py:109`, `:234`), and both card branches (`card.py:66`, `:89`) through the target class. The tag (`crud_views.py:473`) stays permission-only and picks up the helper. Direct create already passes the URL parent (`mixins.py:239-244`). The Book case at `test_guardian.py:337-341` is an own-child, and the plan treats it that way.

Concerns: LOW — an M2M own-child is an instance of the child model, but `get_attribute()` is the M2M name (`views.py:458`, `parentviewset.py:19`). `getattr` yields a manager, not a parent instance (`create.py:53-58`), so the new resolver fail-closes while URL dispatch can still allow create. No Guardian M2M fixture exists; this does not reopen the FK H03 contract.

Suggestions: Bound the resolver to forward FKs, or defer Guardian M2M child-page controls in `02` and `06`.

Risk Assessment: Low for the specified FK path. The M2M case hides a control; it does not grant access.

## 06.2-03

Summary: Ancestry validation stays; the non-first-child output-index bug is an explicit deferral, not a claimed fix.

Strengths: `03:81` and `03:108` match the source: `FormSet.init` enumerates sibling declarations (`formsets.py:159`), while `FormSets.get_template` passes `index=0` (`formsets.py:379`). Positives are limited to top-level and first-child paths. Both sibling declarations still require authorization and forged-parent failure. The mismatch is characterized, not counted as a round trip.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Deferral does not drop locked ancestry checks.

## 06.2-04

Summary: Removed-flag diagnostics, strict helper, and per-view manage policy remain as signed off. Manage-mode tests now patch the cached singleton.

Strengths: `04:108` uses `monkeypatch.setattr` on `crud_views_settings.manage_views_enabled` and `manage_group` (`settings.py:27-28`, singleton `:337`). Manage reads those fields live (`manage.py:31-39`); `override_settings` is reserved for `DEBUG` and `ROOT_URLCONF`. Existing precedent is `test_manage.py:122`. Negative 302/403 rows cannot be satisfied by the import snapshot. Manage URLs are registered even when the flag is `"no"` (`viewset/__init__.py:153-156`).

Concerns: None. AUTH-06/unclassified at `04:80` stays a flagged assumption with no acceptance predicate. It is not a missing plan action.

Suggestions: None.

Risk Assessment: Low. The assumption is carried forward, not waived.

## 06.2-05

Summary: Replay owns the child-page create matrix and the same cached manage-mode seam.

Strengths: `05:110` and `05:123` separate page access, create-parent permission, state, the permission filter, and toolbar/alias/card output, and require direct GET/POST agreement. `05:108` and `05:139` repeat the singleton patch, live `DEBUG`, teardown on failure, and exact group-mode negatives. Fragment positives inherit `03`'s coordinate boundary.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. This wave is post-fix replay, not a second implementation of the gates.

## 06.2-06

Summary: Migration and reference text follow the revised helper, method, fragment, and protected-filter contracts.

Strengths: `06:95` documents parent and own-child resolution, unrelated denial, permission-only `cv_context_has_permission`, and False on a None list object, matching `crud_views.py:473` and `context_buttons.md:531`. `06:97` and `06:115` require custom `cv_filter_related_objects` to filter `RelatedObjects.protected`, keep the pre-hook blocked flag (`delete.py:174-184`), and state that the delete view's `cv_guardian_accept_global_perms` feeds `_PermittedPks` (`views.py:45`, `:67`). `06:99` and `06:131` record the A19 deferral separately from security acceptance. Restored-method Allow/OPTIONS is documented from `01`.

Concerns: None.

Suggestions: If `02` defers M2M child-page create, say so here so migration does not imply every own-child relation is an FK.

Risk Assessment: Low. Docs are tied to named tests; strict mkdocs is not treated as semantic proof.

## Prior-item closure ledger

| ID | Disposition |
| --- | --- |
| H03 | Signed off. FK own-child, actual parent, and unrelated types are distinguished in helpers and the state adapter; default non-create behavior is unchanged; `05`/`06` own replay and wrapper docs. No remaining plan gap. |
| A18 | Closed. Shared `_allowed_methods` filter plus teardown-safe class patch. |
| A19 | Closed by explicit proposed-6.3 deferral. Ancestry validation kept. |
| A20 | Closed. Singleton monkeypatch and live `DEBUG` in `04` and `05`. |
| A21 | Closed. Custom protected-filter duty and per-view related-label fallback are executable doc actions. |
| H01, H02, A01–A17 | No regression. Outer preview gate, test ownership, and prior ledgers remain; H02's blanket denial is superseded only for own-child inputs. |

AUTH-06/unclassified remains a flagged assumption (`04:80`, `06:131`), not a new defect and not silently accepted.

## Unresolved plan concerns

- LOW (new, not H03): Guardian M2M own-child create controls fail closed under the FK resolver while URL dispatch can still authorize the parent. Bound or defer that composition.
