# Expand Django system checks (#28) — Design

**Issue:** [#28 Expand Django system checks](https://github.com/jacob-consulting/django-crud-views/issues/28)
**Date:** 2026-07-17
**Status:** Approved (brainstorming complete)

## Context

`django-crud-views` validates ViewSet/CrudView configuration at startup through
Django's system-check framework. Checks are declared as `checks()` classmethods
that yield `Check` (pydantic) objects — `CheckAttribute`, `CheckAttributeReg`,
`CheckTemplateOrCode`, `CheckTemplate`, `CheckExpression` — collected via
`ViewSet.checks_all()` and surfaced by the `@register("crud_views")` functions in
`crud_views/checks.py`.

Issue #28 collects six check gaps from the 2026-06-10 audit triage. One of them
(#4) is verified already implemented; the remaining five are the scope of this
work. All items are additive dev-time tooling with no semver/runtime impact.

## Ground-truth findings

- **Gap #4 (cv_extends template) is already done.** `CheckTemplate` (E111)
  already validates the view-level `cv_extends_template` (`lib/view/base.py:98`)
  **and** the ViewSet-level `extends` (`lib/viewset/__init__.py:165`). No work
  remains — this sub-item is closed with evidence, not reimplemented.
- **`ContextActionCheck` exists but is wired nowhere** (`lib/check.py:202`) and is
  stale: its body reads `self.context.cv`, which no longer matches the current
  `cv_viewset` API. Its `viewset.has_view(action)` call *is* correct against
  today's `ViewSet.has_view(name)` API.
- **Formsets checks reuse `id="E200"`**, colliding with `cv_key`'s E200
  (`lib/formsets/mixins.py`). They only assert existence, not type.
- **Workflow dependency import names:** the optional extra `workflow` installs
  `django-fsm-2` (imports as `django_fsm`) and `django-fsm-2-admin` (imports as
  `fsm_admin`). `crud_views_workflow/apps.py:ready()` is currently a no-op `pass`.

## Scope

Originally five gaps: #1 type validation, #2 formsets checks, #3 reactivate
context-action check, #5 filter header template check, #6 workflow dependency
checks. During implementation **#3 was dropped as obsolete** (see section 3), so
the shipped work is four gaps: #1, #2, #5, #6.
Out of scope: #4 (already covered by E111), #3 (obsolete — no invariant to enforce).

## Design

### 1. `CheckAttributeType` — new check class (`lib/check.py`)

New subclass of `CheckAttribute`, mirroring `CheckAttributeReg`:

```python
class CheckAttributeType(CheckAttribute):
    id: str = "E101"
    expected_type: type | tuple[type, ...]
    msg: str = "Attribute »{attribute}» value »{value}» is not of type »{expected_type}» at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(expected_type=self.expected_type)
        return context

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()  # existence / None check
        if self.exists and self.value is not None and not isinstance(self.value, self.expected_type):
            yield Error(id=self.get_id(), msg=self.get_message())
```

Existence/None handling is inherited unchanged; the type assertion is additive
and skips when the value is absent or None (those cases are the parent's concern).

### 2. Formsets checks (`lib/formsets/mixins.py` + `lib/check.py`)

- `FormSetMixin.cv_formsets` → `CheckAttributeType(context=cls, id="E204", attribute="cv_formsets", expected_type=FormSets)`.
- `PolymorphicFormSetsViewMixin.cv_polymorphic_formsets` → new **`CheckMapping`**
  check in `check.py`:

```python
class CheckMapping(CheckAttribute):
    """Validate a dict attribute's key/value types."""
    id: str = "E205"
    key_type: type | tuple[type, ...]
    value_type: type | tuple[type, ...]
    # emits: not a dict; key not a subclass/instance of key_type; value not of value_type
```

  For `cv_polymorphic_formsets` the mapping is `Dict[Type[Model], FormSets]`:
  keys are validated as `Model` **subclasses** (`issubclass`), values as
  `FormSets` **instances** (`isinstance`). The check must handle the
  subclass-vs-instance distinction for keys explicitly, and guard the key check
  with `isinstance(key, type)` first — `issubclass` raises `TypeError` on a
  non-class key (e.g. a stray string), which must surface as an E205 error, not
  an uncaught exception during `manage.py check`.
- **Side fix:** replace the two colliding `id="E200"` declarations with the
  distinct IDs above (E204, E205). `FormSetMixinBase.cv_formsets_required` keeps
  a plain `CheckAttribute` but moves off the colliding E200 — reassign to a fresh
  id (E206) so all three formset checks are distinct.

### 3. ~~Reactivate `ContextActionCheck` as E203~~ — DROPPED as obsolete

**Decision (2026-07-17, during implementation):** gap #3 is closed as
**obsolete — no code**. Implementation revealed the check has no invariant left
to enforce:

- `CrudView.cv_get_context()` (`base.py:409`) resolves a `cv_context_actions`
  entry via **two** paths — a context button (`cv_context_buttons` /
  viewset-level `context_buttons`, e.g. `"home"`, `"parent"`, `"filter"`) or a
  registered view key (`has_view`) — and, crucially, **deliberately treats an
  entry resolving to neither as "not a misconfiguration" and silently skips
  it** (explicit code comment). This resolution logic post-dates the original
  `ContextActionCheck`, which only tested `has_view`.
- The framework's own default context-action settings all include `"home"`
  (a context button, not a view), so a `has_view`-only E203 would false-positive
  on essentially every default-configured view.
- Even a corrected two-path check contradicts the runtime's explicit
  tolerance: it fires on the common, runtime-supported pattern of a read-mostly
  partial ViewSet that doesn't register `update`/`delete` but inherits defaults
  naming them (37 such fixtures exist in the test app alone). The rare value
  (catching a typo in an explicitly-set action) is outweighed by punishing
  legitimate configs the framework intentionally supports.

The dead `ContextActionCheck` class is **removed** from `check.py` rather than
left dormant. No wiring is added. The `CampaignDetailView` test fixture keeps a
more-accurate explicit `cv_context_actions` as an incidental cleanup.

### 4. Filter header template check (`lib/views/list.py`)

`ListView` defines `cv_filter_header_template` / `cv_filter_header_template_code`
(a template-or-code pair) but no check validates them. Add to `ListView.checks()`
(overriding to call `super().checks()` then yielding one more):

```python
yield CheckTemplateOrCode(context=cls, attribute="cv_filter_header_template")
```

The default template resolves cleanly; the check catches a typo'd override.

### 5. Workflow dependency checks (new `crud_views_workflow/checks.py`)

```python
@register("crud_views_workflow")
def check_workflow_dependencies(app_configs=None, **kwargs):
    from django.apps import apps
    errors = []
    if not apps.is_installed("crud_views_workflow"):
        return errors
    if not _importable("django_fsm"):
        errors.append(Error("django-fsm-2 is required by crud_views_workflow but is not installed.",
                            hint="pip install django-crud-views[workflow]", id="crud_views_workflow.E001"))
    if not _importable("fsm_admin"):
        errors.append(Error("django-fsm-2-admin is required by crud_views_workflow but is not installed.",
                            hint="pip install django-crud-views[workflow]", id="crud_views_workflow.E002"))
    return errors
```

`_importable(name)` uses `importlib.util.find_spec` inside a try/except so a
missing dep never raises. Replace the `pass` in `apps.py:ready()` with
`import crud_views_workflow.checks  # noqa` to register it.

## Check ID summary

| ID | Check | Where |
|----|-------|-------|
| `viewset.E101` | `CheckAttributeType` default | `lib/check.py` |
| ~~`viewset.E203`~~ | ~~`ContextActionCheck`~~ — dropped as obsolete (gap #3) | — |
| `viewset.E204` | `cv_formsets` is a `FormSets` | `lib/formsets/mixins.py` |
| `viewset.E205` | `cv_polymorphic_formsets` mapping shape | `lib/formsets/mixins.py` |
| `viewset.E206` | `cv_formsets_required` exists | `lib/formsets/mixins.py` |
| `viewset.E110` | filter header template-or-code | `lib/views/list.py` |
| `crud_views_workflow.E001` | `django_fsm` importable | `crud_views_workflow/checks.py` |
| `crud_views_workflow.E002` | `fsm_admin` importable | `crud_views_workflow/checks.py` |

## Testing

TDD per gap — write the failing test first, then implement:

- **CheckAttributeType:** a view/context with a wrong-typed attribute → asserts
  E101 fires; correct type → no error; absent/None → deferred to existence check
  (no E101).
- **Formsets:** a `FormSetMixin` subclass with `cv_formsets = <not a FormSets>` →
  E204; a `PolymorphicFormSetsViewMixin` with a bad mapping (non-Model key or
  non-FormSets value) → E205; valid configs → clean.
- **ContextActionCheck:** a view whose `cv_context_actions` names a non-existent
  view key → E203; all-valid actions → clean.
- **Filter header:** a `ListView` subclass with `cv_filter_header_template =
  "does/not/exist.html"` → E110; default → clean.
- **Workflow deps:** simulate `find_spec` returning None for `django_fsm` /
  `fsm_admin` (monkeypatch) → asserts E001 / E002; both present → clean; app not
  installed → clean.

Tests live in `tests/test1/` following the existing check-test patterns. Run the
full suite (`cd tests && pytest`) to confirm zero regressions.

## Verification

- `pytest` green across the check tests and the full suite.
- `ruff format` / `ruff check --fix` clean.
- Manual: a deliberately-misconfigured test app surfaces each new error id via
  `manage.py check`.
