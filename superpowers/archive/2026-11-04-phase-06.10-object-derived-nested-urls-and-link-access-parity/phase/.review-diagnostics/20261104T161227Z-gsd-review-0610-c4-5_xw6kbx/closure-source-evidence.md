# Cycle 4 closure: supplemental source evidence

Intel does not index Python; these direct readings support adjudication without changing UNCHECKABLE verdicts.

## src/crud_views/lib/table/columns.py
47: class LinkDetailColumnMixin:
48:     @ignore_exception(ViewSetKeyFoundError)
49:     def get_url(self, table, record, **kwargs):
50:         return table.view.cv_get_url("detail", obj=record)

## src/crud_views/lib/exceptions.py
32: def is_strict() -> bool:
33:     """Strict mode: setting CRUD_VIEWS_STRICT, defaulting to DEBUG; misconfigurations raise instead of being skipped."""
34:     from django.conf import settings
35: 
36:     return bool(getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG))
37: 
38: 
39: def ignore_exception(exception_type, default_value=None, default_empty_dict: bool = False):
40:     """
41:     Ignore exception and return a default value.
42:     In strict mode (setting CRUD_VIEWS_STRICT, defaults to DEBUG) the exception
43:     is raised instead, so misconfigurations fail loudly during development.
44:     """
45: 
46:     def decorator(func):
47:         @wraps(func)
48:         def wrapper(*args, **kwargs):
49:             try:
50:                 return func(*args, **kwargs)
51:             except exception_type:
52:                 if is_strict():
53:                     raise
54:                 logger.warning("ignoring exception in %s", func.__qualname__, exc_info=True)
55:                 if default_empty_dict:
56:                     return {}
57:                 return default_value

## tests/test1/test_strict_mode.py
7: import pytest
8: from django.test import override_settings
9: 
10: from crud_views.lib.exceptions import ignore_exception, is_strict
11: 
12: 
13: @ignore_exception(KeyError, default_value="fallback")
14: def _boom():
15:     raise KeyError("k")
16: 
17: 
18: def test_ignore_exception_raises_in_strict_mode():
19:     with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(KeyError):
20:         _boom()
21: 
22: 
23: def test_ignore_exception_swallows_when_not_strict():
24:     with override_settings(CRUD_VIEWS_STRICT=False):
25:         assert _boom() == "fallback"

## tests/test1/conftest.py
43: def pytest_configure():
44:     settings.configure(
45:         BASE_DIR=Path(__file__).resolve().parent.parent,
46:         SECRET_KEY="django-testing",
47:         DEBUG=True,
48:         # pytest-django runs tests with DEBUG=False; misconfigurations must still raise (#264)
49:         CRUD_VIEWS_STRICT=True,
50:         ALLOWED_HOSTS=[],

## .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-02-PLAN.md
113:     - hook_contract proves custom cv_get_url/cv_get_router_and_args and cv_get_url_extra_kwargs run once, extra positional/route fields survive, and list-to-card fallback works.
114:     - context_isolation covers nested links, exceptions at URL/access/state/label stages, mismatched target/user/object, two threads and separate asyncio tasks including inherited ContextVar copies.
115:     - navigation_preservation keeps URL-parent cv_get_parent_object, sibling collections, captured cancel query, successful-save behavior and labels unchanged.
116:     - navigation_preservation renders LinkDetailColumnMixin and LinkChildColumn, follows RedirectChildView's redirect with its redirect/key extras, and renders FilterContextButton on a no-row collection. A missing detail key raises ViewSetKeyFoundError from LinkDetailColumnMixin.get_url under CRUD_VIEWS_STRICT=True and returns None under False, preserving the existing decorator (C3-L01).
117:     - hook_contract proves core nested create state sees selected collection parent A for row B, and a custom parent property raising ObjectDoesNotExist escapes unchanged rather than becoming False.
118:     - hook_contract preserves exact ViewSetError for absent/falsey view objects separately from ViewSetKeyFoundError and public-helper translation; hook_contract_package_import exercises normal startup/import orders after carrier wiring.
119:     - navigation_preservation_queries implements the rendering cost contract above; the existing TestBreadcrumbAncestors::test_ancestor_query_count remains 2 then 0, with independent cold breadcrumb/list measurements and stale-grandparent correctness.
120:   </behavior>
121:   <action>Add these regressions and repair only owned integration seams. Plan 02 owns core CreateView's state resolution (C1-M06): replace its independent broad ObjectDoesNotExist handling with the shared resolver's native provenance classification; matching rendering context selects the collection's parent A, callable context keeps existing explicit-parent/own-child/unresolved semantics, and no custom state hook receives an unresolved parent. Do not add core parent permissions. Plan 03 will wire Guardian's create override and consolidate its no-object correction. Preserve URL-extra parent constraints, non-parent extras and single public hook invocation. Exercise carrier misses both after custom URL overrides (matching frame: semantic page scope) and outside scopes (no page fallback); thread/async isolation tests use only in-memory sentinels and prebuilt resolutions, never share Django connections or transaction fixtures (C1-M08). Replay named column/redirect/filter consumers and original exception seams (C1-M05). Addresses review concern C3-L01: follow tests/test1/test_strict_mode.py's django.test.override_settings context-manager pattern for the missing-detail navigation_preservation cases; use CRUD_VIEWS_STRICT=True with pytest.raises(ViewSetKeyFoundError), and CRUD_VIEWS_STRICT=False with an is None assertion on LinkDetailColumnMixin.get_url. Preserve its existing ignore_exception decorator and the strict default configured in tests/test1/conftest.py. Preserve custom access vetoes, state/label counts, target labels, captions and origin/cancel/save behavior. Getter/publisher ownership checks must apply to inherited task contexts even though package rendering is synchronous.</action>
122:   <verify>
123:     <automated>PYTHONPATH="$PWD/src:$PWD" .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_nested_url_rendering.py -k 'hook_contract or context_isolation or navigation_preservation' -n 4 -q</automated>
124:     <fails_when>Exit is non-zero, no tests are collected, hook counts/arguments change, or a context survives its owner scope or appears in another execution owner.</fails_when>
125:     <automated>PYTHONPATH="$PWD/src:$PWD" .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_cancel_origin.py tests/test1/test_success_origin.py tests/test1/test_breadcrumb.py -n 4 -q</automated>
126:     <fails_when>Exit is non-zero or existing cancel, success or breadcrumb assertions regress.</fails_when>
127:   </verify>
128:   <acceptance_criteria>Override tests retain original obj identity and single access invocation; copied-context isolation and fresh-process import tests pass; ordinary request-free generation does not consume rendering state; navigation_preservation_queries commits numeric fresh/cached N=1/4 and breadcrumb URL/total budgets plus measured baseline deltas; the named ancestor-query pin stays 2 then 0; preservation suite passes. Missing-detail navigation_preservation tests assert ViewSetKeyFoundError under CRUD_VIEWS_STRICT=True and None under False, with the existing column decorator unchanged (C3-L01). The URL-free caller read here and exercised in 03-02 is the cv_context_has_permission template filter, not a separate cv_has_access tag.</acceptance_criteria>
129:   <done>Application extension hooks and navigation contracts survive destination-aware rendering.</done>

