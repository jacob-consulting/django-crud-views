# Plan 06.23-02 acceptance evidence

## Published-source comparison

The task's source-review checks were performed against the canonical issue snapshot in
`06.23-CONTEXT.md`; they are not a new product approval gate or a claim of human visual acceptance.

- The complete `CustomerDetailView` Python fence, five explicit attribute assignments and dynamic getter fence
  in `docs/reference/icons.md` have identical Python ASTs to their canonical snapshot counterparts. Comments
  retain the same intent with repository formatting.
- The selection table has exactly six data rows: omitted, None, VIEWSET_DEFAULT, empty string, NONE and explicit
  icon. The two primitive alias pairs are distinct. Fallback occurs only for None.
- The full customer example retains both public imports, `cv_viewset = cv_customer`, the Customer/name property
  group, `sales/customer_header.html` and `Icon.NONE`.
- All six new Python fences across icons/migration references parse and pass `ruff format --check` via stdin.
- The actual published customer class is executed by
  `test_heading_docs.py::test_published_custom_header_suppression_recipe`. A temporary Publisher-backed ViewSet
  supplies `fas:book`, a real Publisher supplies the name, and the configured Django backend loads the file
  snippet. The actual published page-title recipe retains avatar markup and the name under both NONE and
  VIEWSET_DEFAULT; only the latter renders the inherited icon. Registry cleanup runs in finally.
- Custom file/code snippets explicitly preserve normal inheritance. The getter override's None suppresses the
  resolved icon; the None attribute inherits. Generic resolved icons, group icons and registry None still draw
  no icon.
- Both release surfaces state that empty strings previously inherited and now suppress, name both None and
  VIEWSET_DEFAULT inheritance replacements, publish the Icon import and retain intentional NONE suppression.
  The changelog links the migration anchor; migration links the canonical reference. Strict MkDocs passed.

## Nine acceptance rows

| Requirement | Evidence |
|---|---|
| HDRI-01 | Plan 01 public constant identity test; public import in executed documentation fence |
| HDRI-02 | Plan 01 omitted/None/default real-header tests; documentation inheritance control |
| HDRI-03 | Plan 01 empty/NONE actual markup tests; documentation suppression control |
| HDRI-04 | Plan 01 semantic/prefix/raw overrides; icons reference supported-format wording |
| HDRI-05 | Plan 01 file/code snippet tests; real file snippet in published customer class |
| HDRI-06 | Plan 01 dynamic/modal/example/standalone coverage; canonical dynamic override recipe |
| HDRI-07 | Plan 01 unchanged E356/W353 acceptance and invalid controls |
| HDRI-08 | Exact canonical AST comparisons, six rows, context wording, paired release guidance and executed fence |
| HDRI-09 | Final four-module gate: 317 passed in 9.06s; strict MkDocs and scoped Ruff pass; full suite: 12,301 passed in 543.44s (full-suite.log) |

## Decision coverage

| Decisions | Evidence |
|---|---|
| D-01, D-02 | Plain primitive constants and exact six-row selection table; real inheritance/suppression controls |
| D-03, D-04 | Independent snippet content/icon wording; Plan 01 supported page/modal/shared-theme rendering |
| D-05, D-06 | Supported string forms, exact dynamic recipe and Plan 01 diagnostics coverage |
| D-07 | Explicit restriction of inheritance to cv_icon_header; generic/group None retains no-icon meaning |
| D-08 | Breaking changelog plus actionable before/after migration with both replacements |
| D-09 | Full issue examples, public import and snippet-reference cross-link; heading recipe anchors preserved |
| D-10 | Five scoped plan files changed, no runtime change, dependency, flag, redesign or downstream release |
| D-11 | Multicore focused and full-suite gates plus strict docs and scoped lint/format evidence |

## Evidence limits

Local Python 3.12.3 / Django 6.1.2 only. No additional version matrix, external downstream installation,
browser appearance or assistive-technology evaluation is claimed. No added package, stub, skipped test,
authentication gate or new runtime trust boundary was introduced by this plan.

The full suite exited zero with four pre-existing `RemovedInDjango2028Warning` occurrences from
`tests/test1/test_delete.py::test_delete_collection_loader_error_propagates_unchanged`: Book.from_db() should
accept fetch_mode. The warning is unrelated to this documentation change and was not modified.
