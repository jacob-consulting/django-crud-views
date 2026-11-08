## Deferred Items

- `isolated_routes` registry snapshot can drop the shared app ViewSets (found during 06.18-05)
  status: open
  **What:** `tests/test1/test_ancestor_authorization.py::isolated_routes` snapshots `_REGISTRY` before it builds the temporary URLconf, which includes `tests.test1.project.urls`. If that URLconf (and with it `tests.test1.app.views`) is imported for the first time inside the isolated block, the restore drops the shared ViewSets (`publisher`, `book`, ...) while the modules stay cached in `sys.modules`, so later tests in the same worker fail with `ViewSetNotFoundError: publisher`.
  **Reproduce:** `pytest tests/test1/test_ancestor_helpers.py tests/test1/test_nested_viewset.py -p no:randomly` (serial) at `d398706b`: 16 failed. Under xdist/random order it is usually masked.
  **Scope:** pre-existing shared test helper outside 06.18-05's file list; 06.18-05's new modules import the project URLconf before the snapshot (`test_ancestor_resolution._register_project_viewsets`). Proper fix: do the same inside `isolated_routes` (import the project URLconf before taking the snapshot).

- Filtered nested lists skip the parent scoping of `_scope_child_queryset` (found during 06.18-06)
  status: resolved
  **Resolved in 06.18-07** (Rule 1 deviation): `CrudView.get_context_data` now scopes a keyword `object_list` as well as `self.object_list` (the same scoped queryset when the keyword is `self.object_list`, so tables render the same rows); plan 06's default-database check on the consumed collection is unchanged. Test-first: `620852bf` (12 failing cases in `test_ancestor_resolution.py::test_filtered_child_collection_is_scoped_to_the_resolved_parent`), fix `1442363c`.
  **What:** `CrudView.get_context_data` scopes `object_list` only when it is not passed as a keyword. django-filter's `BaseFilterView.get` calls `get_context_data(filter=..., object_list=self.object_list)`, so a nested `ListViewTableFilterMixin` list whose `get_queryset` omits the parent filter renders other parents' rows (probe at `8b02d12d`: parent `a` listed `['foreign', 'own']`). The default ViewSet queryset already filters, so shipped default lists are unaffected.
  **Scope:** ANCE-05 collection seam owned by 06.18-05; not caused by 06.18-06. 06.18-06's default-database check reads the collection from the keyword too, so the alias boundary itself covers filtered lists (`test_filtered_list_collection_is_checked_where_it_is_consumed`). Proper fix: scope `kwargs["object_list"]` as well (and keep `self.object_list` in sync) plus a filtered-list case in `test_ancestor_resolution.py`.

- Core `ViewSet.default_permissions` reads one ContentType per permission row on a cold ViewSet (found during 06.18-10)
  status: open
  **What:** the core vocabulary loop (`src/crud_views/lib/viewset/__init__.py`, `default_permissions`) accesses `permission.content_type` per row, so a cold core ViewSet costs one `get_for_model` + one Permission query + one ContentType read per row (ct 5 for a four-permission model). Measured in `06.18-COSTS.md`: full cascade at depth 3 shows ct 15 cold. `GuardianViewSet.default_permissions` uses the single resolved content type (ct 1).
  **Scope:** pre-existing, once per ViewSet per process, vocabulary only (no access state). Outside 06.18-10's file list (tests/COSTS only). Possible fix: reuse the resolved `content_type` (as the Guardian override does) or `select_related("content_type")`.

- A filter list without `formhelper_class` cannot render on crispy-forms before 2.7 (found during 06.18-12)
  status: open
  **What:** `list_filter.inner.html` renders `{% crispy filter.form filter.form.helper %}`. `ListViewTableFilterMixin` sets `filter.form.helper` only when `formhelper_class` is declared. crispy-forms 2.7 swallows the failed `helper` lookup; 2.5 (cached Django 4.2 env) and 2.0 (the 6.0 crispy floor) raise `VariableDoesNotExist`. The documented examples always declare `formhelper_class`.
  **Scope:** pre-existing package behavior, not caused by phase 06.18. It surfaced because `test_ancestor_resolution.py`'s filtered fixtures omitted the helper; 06.18-12 gave them the documented helper (`5829cae7`). Possible fix: render without the helper argument when none is set, or document `formhelper_class` as required.

- Django 4.2 error emails evaluate refused nested querysets (found during 06.18-12)
  status: open
  **What:** a nested default-database refusal is an `ImproperlyConfigured` 500. Django 4.2's `AdminEmailHandler` builds an `ExceptionReporter` even without `ADMINS` (5.x returns early), and the report's frame-local `repr()` runs the refused queryset (one read on the refused alias, after the refusal and after no package work). Observed by `test_ancestor_databases.py` on Django 4.2.30 only.
  **Scope:** Django's error reporting, outside the package's request work. 06.18-12 no-ops the handler in that test module (`5829cae7`) so its "no shard SQL" captures measure the package. Not fixed in the package; a deployment with `ADMINS` on Django 4.2 can see that read in its error report.
