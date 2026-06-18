# ViewSet-level `extends` Template Override Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a whole ViewSet declare the base template its views extend, with a view → viewset → global fallback chain, validated by startup system checks and documented.

**Architecture:** Add an optional `extends` field to the `ViewSet` Pydantic model. Rewrite `CrudView.cv_get_extends_template()` to resolve view-level `cv_extends_template` → viewset `extends` → global `settings.extends`. A new optional `CheckTemplate` system check validates any set override template at startup, wired in at both view and viewset level.

**Tech Stack:** Python, Django (system checks, templates), Pydantic v2, pytest.

## Global Constraints

- Line length: 120 characters; double quotes; ruff format.
- All `CrudView` class attributes use `cv_` prefix; plain `ViewSet` fields do **not**.
- The global `CRUD_VIEWS_EXTENDS` setting stays mandatory (final fallback) — do not relax check `E100`.
- Existing behaviour must be unchanged when no override is set.
- Tests live in `tests/test1/`; run from the `tests/` directory.
- The override template MUST NOT contain `{% extends cv_extends %}` (would raise `TemplateDoesNotExist`) — this is a documentation constraint, surfaced in docs and the skill.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/crud_views/lib/check.py` | Add `CheckTemplate` — validates an optional template attribute resolves if set |
| `src/crud_views/lib/viewset/__init__.py` | Add `extends` field; yield `CheckTemplate` in `checks()` |
| `src/crud_views/lib/view/base.py` | Three-level `cv_get_extends_template()`; yield `CheckTemplate` in `checks()` |
| `tests/test1/test_check_messages.py` | Unit tests for `CheckTemplate` |
| `tests/test1/test_extends_override.py` | New: resolution-chain + check-integration tests |
| `docs/reference/templates.md` | New: base-template resolution, ViewSet `extends`, mixin pattern, caveat |
| `docs/reference/.pages` | Add `templates.md` to nav |
| `docs/reference/settings.md` | Cross-link from `CRUD_VIEWS_EXTENDS` row |
| `CHANGELOG.md` | Unreleased entry |
| `skills/django-crud-views/SKILL.md` | Document field, resolution order, mixin, caveat |

---

## Task 1: `CheckTemplate` system check

**Files:**
- Modify: `src/crud_views/lib/check.py` (add class after `CheckTemplateOrCode`, ~line 174)
- Test: `tests/test1/test_check_messages.py`

**Interfaces:**
- Produces: `CheckTemplate(context=<cls|obj>, attribute="<attr_name>")` — a `Check` whose `.messages()` yields nothing when the attribute is unset/falsy, and one `Error` (id `viewset.E111`) when the attribute is set to a template name that `get_template()` cannot resolve.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_check_messages.py`:

```python
from crud_views.lib.check import CheckTemplate


class ExtendsValid:
    extends = "app/index.html"  # exists in the test app


class ExtendsMissing:
    extends = "does-not-exist.html"


class ExtendsUnset:
    extends = None


def test_check_template_unset_emits_no_message():
    check = CheckTemplate(context=ExtendsUnset, id="E111", attribute="extends")
    assert list(check.messages()) == []


def test_check_template_existing_emits_no_message():
    check = CheckTemplate(context=ExtendsValid, id="E111", attribute="extends")
    assert list(check.messages()) == []


def test_check_template_missing_emits_error():
    check = CheckTemplate(context=ExtendsMissing, id="E111", attribute="extends")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "does-not-exist.html" in messages[0].msg
    assert messages[0].id == "viewset.E111"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_check_messages.py -v`
Expected: FAIL — `ImportError: cannot import name 'CheckTemplate'`

- [ ] **Step 3: Implement `CheckTemplate`**

In `src/crud_views/lib/check.py`, add after the `CheckTemplateOrCode` class (the file already imports `Error`, `CheckMessage`, `TemplateDoesNotExist`, `get_template`, `Iterable`):

```python
class CheckTemplate(Check):
    """
    Validate that an optional template attribute, if set, resolves.

    Unlike CheckTemplateOrCode this emits no error when the attribute is unset —
    it only guards against a configured-but-missing template (e.g. an overridden
    cv_extends_template or a ViewSet extends).
    """

    id: str = "E111"
    attribute: str | None = None
    msg_template_not_found: str = "Template »{template}» not found at »{context}»"

    def messages(self) -> Iterable[CheckMessage]:
        template = getattr(self.context, self.attribute, None)
        if template:
            try:
                get_template(template)
            except TemplateDoesNotExist:
                msg = self.msg_template_not_found.format(template=template, context=self.context)
                yield Error(id=self.get_id(), msg=msg)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_check_messages.py -v`
Expected: PASS (all, including the three new tests)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/check.py tests/test1/test_check_messages.py
git commit -m "feat(checks): add optional CheckTemplate for override templates"
```

---

## Task 2: ViewSet `extends` field + viewset-level check

**Files:**
- Modify: `src/crud_views/lib/viewset/__init__.py` (field ~line 79-83; `checks()` ~line 141)
- Test: `tests/test1/test_extends_override.py` (new)

**Interfaces:**
- Consumes: `CheckTemplate` from Task 1.
- Produces: `ViewSet(..., extends="<template>")` — optional `str | None = None` field. `ViewSet.checks()` additionally yields `CheckTemplate(context=self, attribute="extends")`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_extends_override.py`:

```python
from crud_views.lib.check import CheckTemplate
from crud_views.lib.viewset import ViewSet


def test_viewset_extends_field_defaults_to_none():
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="extends_default_probe")
    assert vs.extends is None


def test_viewset_checks_include_extends_template_check():
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="extends_check_probe", extends="app/index.html")
    template_checks = [
        c for c in vs.checks()
        if isinstance(c, CheckTemplate) and c.attribute == "extends"
    ]
    assert len(template_checks) == 1
```

> Note: each `ViewSet(...)` must use a unique `name` — names are registered in a
> module-global registry and duplicates raise at construction time.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_extends_override.py -v`
Expected: FAIL — `AttributeError`/validation: `ViewSet` has no field `extends`

- [ ] **Step 3: Add the field**

In `src/crud_views/lib/viewset/__init__.py`, add the field alongside the other optional ViewSet fields (after `icon_header: str | None = None`, ~line 82):

```python
    extends: str | None = None  # base template all views in this viewset extend
```

- [ ] **Step 4: Wire the viewset-level check**

In the same file, import `CheckTemplate` (extend the existing `from ..check import CheckAttributeReg, Check` on line 19):

```python
from ..check import CheckAttributeReg, Check, CheckTemplate
```

Then in `ViewSet.checks()` (after the `prefix` check, before the `for view in self._views.values()` loop, ~line 147):

```python
        yield CheckTemplate(context=self, id="E111", attribute="extends")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_extends_override.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/viewset/__init__.py tests/test1/test_extends_override.py
git commit -m "feat(viewset): add extends field and validating check"
```

---

## Task 3: Three-level resolution + view-level check

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (`cv_get_extends_template` ~line 100; `checks()` ~line 69; imports line 11)
- Test: `tests/test1/test_extends_override.py` (append)

**Interfaces:**
- Consumes: `ViewSet.extends` (Task 2), `CheckTemplate` (Task 1).
- Produces: `CrudView.cv_get_extends_template()` resolves view `cv_extends_template` → `cv_viewset.extends` → `crud_views_settings.extends`. `CrudView.checks()` yields `CheckTemplate(context=cls, attribute="cv_extends_template")`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_extends_override.py`:

```python
from types import SimpleNamespace

from tests.test1.app.views import AuthorDetailView  # registered to cv_author


def _resolve(view_template, viewset_extends):
    view = AuthorDetailView()
    view.cv_extends_template = view_template
    view.cv_viewset = SimpleNamespace(extends=viewset_extends)
    return view.cv_get_extends_template()


def test_resolution_falls_back_to_global_setting():
    # nothing overridden anywhere -> global CRUD_VIEWS_EXTENDS ("app/crud_views.html")
    assert _resolve(None, None) == "app/crud_views.html"


def test_resolution_uses_viewset_extends_over_global():
    assert _resolve(None, "app/index.html") == "app/index.html"


def test_resolution_view_overrides_viewset():
    assert _resolve("app/base.html", "app/index.html") == "app/base.html"


def test_view_checks_include_cv_extends_template_check():
    template_checks = [
        c for c in AuthorDetailView.checks()
        if isinstance(c, CheckTemplate) and c.attribute == "cv_extends_template"
    ]
    assert len(template_checks) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_extends_override.py -v`
Expected: FAIL — `test_resolution_uses_viewset_extends_over_global` returns the global template (viewset not consulted yet); `test_view_checks_*` finds 0 checks.

- [ ] **Step 3: Rewrite the resolver**

In `src/crud_views/lib/view/base.py`, replace `cv_get_extends_template` (lines 100-103):

```python
    def cv_get_extends_template(self) -> str:
        if self.cv_extends_template:
            return self.cv_extends_template
        if self.cv_viewset.extends:
            return self.cv_viewset.extends
        return crud_views_settings.extends
```

- [ ] **Step 4: Wire the view-level check**

In the same file, extend the check import on line 11:

```python
from crud_views.lib.check import Check, CheckAttributeReg, CheckAttribute, CheckTemplateOrCode, CheckTemplate
```

Then in `CrudView.checks()`, after the `cv_path` check (~line 75, before the `is_frontend` block):

```python
        yield CheckTemplate(context=cls, id="E111", attribute="cv_extends_template")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_extends_override.py -v`
Expected: PASS (all)

- [ ] **Step 6: Run the full suite to confirm no regressions**

Run: `cd tests && pytest -q`
Expected: PASS (no failures; existing behaviour unchanged when no override set)

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/view/base.py tests/test1/test_extends_override.py
git commit -m "feat(view): resolve extends template view -> viewset -> global"
```

---

## Task 4: Documentation

**Files:**
- Create: `docs/reference/templates.md`
- Modify: `docs/reference/.pages` (add to nav before `settings.md`)
- Modify: `docs/reference/settings.md` (cross-link the `CRUD_VIEWS_EXTENDS` row)
- Modify: `CHANGELOG.md` (Unreleased entry)

- [ ] **Step 1: Write the reference page**

Create `docs/reference/templates.md`:

````markdown
# Base template

Every crud_views frontend template renders `{% extends cv_extends %}`, where
`cv_extends` is resolved per view. This lets you control which base template
your CRUD pages extend — globally, per ViewSet, or per view.

## Resolution order

`cv_extends` is resolved from the first of these that is set:

1. **View** — `cv_extends_template` on the `CrudView` subclass
2. **ViewSet** — `extends` on the `ViewSet`
3. **Global** — the `CRUD_VIEWS_EXTENDS` setting (required; final fallback)

### Per ViewSet

Set it once and every view in the ViewSet inherits it:

```python
cv_author = ViewSet(
    model=Author,
    name="author",
    extends="myapp/author_base.html",
)
```

### Per view

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_extends_template = "myapp/author_list_base.html"
```

### Shared base via a mixin

To share a base across several ViewSets (or vary it within one), put it on a
mixin and inherit:

```python
class MySpecialBase(CrudView):
    cv_extends_template = "myapp/special_base.html"

class FooListView(MySpecialBase, ListView):
    ...
```

!!! warning "The override template must be a real base template"
    The template named by `cv_extends_template` / ViewSet `extends` is itself
    the base that crud_views extends. It **MUST NOT** contain
    `{% extends cv_extends %}` (nor otherwise re-extend `cv_extends`) — that
    makes the template extend itself and raises
    `django.template.exceptions.TemplateDoesNotExist`.

    Point the override at a normal base template — one that extends your own
    site base (e.g. `{% extends "base.html" %}`) or none at all.

## Validation

If a ViewSet `extends` or a view `cv_extends_template` names a template that
cannot be loaded, Django's system checks report it at startup
(`crud_views.viewset.E111`).
````

- [ ] **Step 2: Add to the reference nav**

In `docs/reference/.pages`, add `templates.md` immediately before `settings.md`:

```yaml
    - context_buttons.md
    - guardian.md
    - ordered_view.md
    - templates.md
    - settings.md
    - ...
```

- [ ] **Step 3: Cross-link from settings**

In `docs/reference/settings.md`, update the `CRUD_VIEWS_EXTENDS` description (line 10) to point at the new page:

```markdown
| CRUD_VIEWS_EXTENDS              | Base template that crud_views templates extend (required; can be overridden per ViewSet/view — see [Base template](templates.md))     | `str` | `None`       |
```

- [ ] **Step 4: Add CHANGELOG entry**

In `CHANGELOG.md`, under the `Unreleased` section's `Added` list, add:

```markdown
- ViewSet-level `extends` field to override the base template for all views in a ViewSet; resolution order is view (`cv_extends_template`) → ViewSet (`extends`) → global (`CRUD_VIEWS_EXTENDS`). Override templates are validated at startup (`crud_views.viewset.E111`).
```

(If no `Unreleased`/`Added` section exists, create `## [Unreleased]` with an `### Added` subsection at the top, matching the file's existing heading style.)

- [ ] **Step 5: Verify docs build**

Run: `cd /home/alex/projects/alex/django-crud-views && task docs` (or `mkdocs build -s`)
Expected: build succeeds; `templates.md` appears in the Reference nav. Stop the server.

- [ ] **Step 6: Commit**

```bash
git add docs/reference/templates.md docs/reference/.pages docs/reference/settings.md CHANGELOG.md
git commit -m "docs: document ViewSet/view extends template override"
```

---

## Task 5: Update the inline skill

**Files:**
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Add a base-template override section**

In `skills/django-crud-views/SKILL.md`, add a short section near the existing
`cv_extends` mention (line ~74). Insert:

````markdown
### Base template override

The base template each view extends (`cv_extends` in templates) resolves:
view `cv_extends_template` → ViewSet `extends` → global `CRUD_VIEWS_EXTENDS`.

```python
# all views in this ViewSet extend a custom base:
cv_author = ViewSet(model=Author, name="author", extends="myapp/author_base.html")

# or a single view:
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_extends_template = "myapp/author_list_base.html"
```

**Caveat:** the override template MUST NOT contain `{% extends cv_extends %}`
— it is itself the base being extended, so re-extending `cv_extends` makes it
extend itself and raises `TemplateDoesNotExist`. Point it at a real base
template instead. Misconfigured templates are caught at startup as
`crud_views.viewset.E111`.
````

- [ ] **Step 2: Verify the edit reads cleanly**

Run: `grep -n "extends" skills/django-crud-views/SKILL.md`
Expected: the new section appears with the field, resolution order, and caveat.

- [ ] **Step 3: Commit**

```bash
git add skills/django-crud-views/SKILL.md
git commit -m "docs(skill): document extends override field and caveat"
```

---

## Self-Review (completed)

**Spec coverage:**
- ViewSet `extends` field → Task 2 ✓
- view → viewset → global chain → Task 3 ✓
- global setting stays mandatory → unchanged (E100 untouched); noted in constraints ✓
- view-level + viewset-level checks → Tasks 2 & 3 (shared `CheckTemplate`, Task 1) ✓
- mixin pattern documented → Task 4 + Task 5 ✓
- `{% extends cv_extends %}` caveat → Task 4 (warning admonition) + Task 5 ✓
- tests for chain + checks → Tasks 1-3 ✓
- changelog → Task 4 ✓
- inline skill → Task 5 ✓

**Placeholder scan:** none — all code/test/doc steps contain literal content.

**Type consistency:** `CheckTemplate(context=, id=, attribute=)` used identically in Tasks 1-3; `extends` field and `cv_extends_template` attribute names consistent across resolver, checks, tests, and docs; global fallback string `"app/crud_views.html"` matches `conftest.py`.
