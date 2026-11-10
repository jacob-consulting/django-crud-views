# Plan 06.23-01 acceptance evidence

Executed from the repository root with `PYTHONPATH=src .venv/bin/python`.

| Requirement | Evidence | Result |
|---|---|---|
| HDRI-01 | `test_icons_registry.py::test_public_icon_constants`: public import, identity/type, generic rendering | PASS |
| HDRI-02 | `test_omitted_view_header_icon_inherits` and `test_view_header_icon_suppression`: real GET, omitted/None/VIEWSET_DEFAULT | PASS |
| HDRI-03 | `test_view_header_icon_suppression`: non-empty host inheritance control, both empty forms, title preserved | PASS |
| HDRI-04 | `test_explicit_view_header_icon_overrides_viewset`: detail/fas:pen/raw-icon/host:edit, exact title classes and child icons | PASS |
| HDRI-05 | `test_custom_header_preserves_content_and_explicit_icon_choice`: file/code × None/default/empty/suppress, real getter/property, custom span and text | PASS |
| HDRI-06 | `test_modal_view_header_icon_choice`, `test_example_theme_uses_real_header_icon_choice`, `test_standalone_header_icon_uses_real_getter`, `test_header_icon_getter_override_can_still_suppress` | PASS |
| HDRI-07 | `test_public_icon_constants_pass_existing_checks`, existing E356/W353 controls; validation predicate unchanged | PASS |
| HDRI-09 focused portion | Three-module focused command below | PASS |

Task 1 RED: the literal-empty real page request retained `icon-inherited` after its None control passed. Title remained `Authors`, and no setup/collection error occurred. `task-1-red.json` preserves the unchanged JUnit report and semantic assessment; the classifier returned `RED_EVIDENCE_OK` before implementation.

Task 1 GREEN and the required post-commit tracer rerun each passed **2 tests** with the plan's named serial selection (0.91s and 0.83s). Serial execution avoids worker startup overhead for this tiny selection.

Task 2 gate:

```text
PYTHONPATH=src .venv/bin/python -m pytest tests/test1/test_heading_icons.py tests/test1/test_icons_checks.py tests/test1/test_icons_registry.py -n 4 -q --junitxml=.planning/phases/06.23-explicit-header-icon-suppression-with-icon-constants-329/evidence/06.23-01/task-2-focused.xml
232 passed in 7.06s
```

Two test-authoring expectations were corrected before the passing run: the stock modal heading is `Author`, and the snippet metadata key is `verbose_name_plural_translate`, whose value is `Authors`. No production changes were required for these corrections.

The focused run includes existing hostile-title/class encoding guards and group None/empty behavior. Only the deliberate dynamic-override test replaces the getter among the new tests. The file-template case uses the configured backend with a locmem loader preceding its existing loaders, sets APP_DIRS=False, and clears the competing code attribute. Configuration mutations use monkeypatch/override_settings; no temporary ViewSet registration was added.

Loader reference: [Django template API](https://docs.djangoproject.com/en/5.2/ref/templates/api/#loader-types), consulted after Context7 MCP/CLI were unavailable. The explicit-loader and APP_DIRS setup follows the existing backend contract.

Full-suite/docs/version-matrix verification belongs to plan 02; none is claimed here. No new dependency, renderer/check refactor, network/auth/file-access/schema boundary, stub or skipped test was introduced.
