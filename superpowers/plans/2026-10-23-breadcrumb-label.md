# Breadcrumb Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An opt-in, breadcrumb-only label for a view's own current-page item, falling back to the short action label (#271).

**Architecture:** Two `None`-default attributes and one classmethod on `CrudViewBreadcrumbMixin`; `cv_breadcrumb_get()` calls the classmethod at its three own-item sites; the mixin's `checks()` gains an optional-template check.

**Tech Stack:** Django, pytest, existing `render_snippet()` / `CheckTemplate`.

**Spec:** `superpowers/specs/2026-10-23-breadcrumb-label-design.md`

## Global Constraints

- Attribute names: `cv_breadcrumb_label_template`, `cv_breadcrumb_label_template_code`, both `str | None = None`.
- Method: `cv_get_breadcrumb_label(cls, context) -> str`, a classmethod.
- No built-in view sets the new attributes; unset → every breadcrumb renders exactly as today.
- Template variables are the flat `ViewSet.get_meta()` names (`verbose_name`, `verbose_name_plural`, `*_translate`, `viewset`, `cv`, `object`); no `cv_meta` namespace.
- Check id `E111` via `CheckTemplate` (not `CheckTemplateOrCode`).
- Not breaking: CHANGELOG `### Added` only; `docs/migrating-1.0.md` untouched.
- Ruff, line length 120, double quotes. Work on a branch (e.g. `feature/breadcrumb-label-271`), never on `main`.

## Review Focus

1. Label set on the container (list) view → no effect; it has no own action item. Test in Task 1.
2. Template code using `{{ object }}` where the object's `__str__` contains `&` → escaped exactly once (title is safe, contains `&amp;`, not `&amp;amp;`). Test in Task 1.
3. Label set on the detail view → no effect. Test in Task 1.
4. Buttons pointing to the view keep the short label. Test in Task 1.
5. Unset label on every existing `PublisherBc*` view → existing `tests/test1/test_breadcrumb.py` stays green unchanged. Verified in Task 1 step 4.

---

### Task 1: Breadcrumb label on the mixin and in the trail

**Files:**
- Modify: `src/crud_views/lib/breadcrumb.py` (attributes next to `cv_breadcrumb_container_label` ~line 90; new classmethod in the extension-points section; `cv_breadcrumb_get()` lines 152, 164, 170)
- Create: `tests/test1/app/templates/app/breadcrumb_label.html` with content `Edit {{ verbose_name }}`
- Test: `tests/test1/test_breadcrumb.py` (new class `TestBreadcrumbLabel`)

**Interfaces:**
- Consumes: `CrudView.render_snippet(data, template, template_code)`, `CrudView.cv_get_action_short_label(context)`, `ViewSet.get_meta(context)`; test helpers `make_view()`, `titles()` in `test_breadcrumb.py`.
- Produces: `CrudViewBreadcrumbMixin.cv_breadcrumb_label_template`, `.cv_breadcrumb_label_template_code`, `.cv_get_breadcrumb_label(context) -> str`.

Test views are local subclasses of the `PublisherBc*` views (from `tests.test1.app.views`) that do **not** re-declare `cv_viewset` — the metaclass registers only when `cv_viewset` is in the class body, so they do not touch the viewset. URLs/kwargs as in the existing `TestBreadcrumbTopLevel` tests.

- [ ] **Step 1: Write the failing tests** in `TestBreadcrumbLabel` (`@pytest.mark.django_db`):

```python
def test_create_uses_breadcrumb_label(self):
    class V(PublisherBcCreateView):
        cv_breadcrumb_label_template_code = "New"  # default create short label is "Create"
    bc = make_view(V, "/publisher_bc/create").cv_breadcrumb()
    assert titles(bc) == ["Publishers", "New"]

def test_update_with_detail_uses_breadcrumb_label(self, publisher_penguin):
    # PublisherBcUpdateView subclass, code "Edit"
    assert titles(bc) == ["Publishers", str(publisher_penguin), "Edit"]

def test_update_without_detail_uses_breadcrumb_label(self, publisher_penguin):
    # PublisherBcNodetailUpdateView subclass, code "Edit"
    assert titles(bc)[-1] == "Edit"; assert bc.items[1].url_name is None

def test_breadcrumb_label_template(self):
    # create subclass, cv_breadcrumb_label_template = "app/breadcrumb_label.html"
    assert titles(bc)[-1] == "Edit Publisher"

def test_code_wins_over_template(self):
    # both set: template "app/breadcrumb_label.html", code "New"
    assert titles(bc)[-1] == "New"

def test_object_in_template_code_escaped_once(self):
    publisher = Publisher.objects.create(name="A & B")
    # PublisherBcUpdateView subclass, code "Edit {{ object }}"
    title = titles(bc)[-1]
    assert title == "Edit A &amp; B"
    assert isinstance(title, SafeString)

def test_short_label_unchanged(self):
    # create subclass with code "New"
    context = ViewContext()  # same context construction the view uses for a non-object view
    assert V.cv_get_action_short_label(context=context) == PublisherBcCreateView.cv_get_action_short_label(context=context)
    assert V.cv_get_breadcrumb_label(context=context) == "New"

def test_detail_view_unaffected(self, publisher_penguin):
    # PublisherBcDetailView subclass, code "XXX"
    assert titles(bc) == ["Publishers", str(publisher_penguin)]

def test_list_view_unaffected(self):
    # PublisherBcListView subclass, code "XXX"
    assert titles(bc) == ["Publishers"]
```

Imports needed: `SafeString` from `django.utils.safestring`; `ViewContext` from wherever `cv_get_view_context()` builds it (`crud_views.lib.view` — use `view.cv_get_view_context()` on a `make_view` instance if constructing it directly is awkward).

- [ ] **Step 2: Run to verify RED**

Run: `pytest tests/test1/test_breadcrumb.py::TestBreadcrumbLabel -v`
Expected: the five label-using tests and `test_object_in_template_code_escaped_once` FAIL (title is the default short label, "Create" / "Update"); `test_short_label_unchanged` fails with `AttributeError: cv_get_breadcrumb_label`; detail/list tests pass.

- [ ] **Step 3: Implement** the two attributes and `cv_get_breadcrumb_label(cls, context) -> str` exactly as in the spec's "Attributes and method" section; replace `self.cv_get_action_short_label(context=context)` with `self.cv_get_breadcrumb_label(context=context)` at the three own-item sites in `cv_breadcrumb_get()`.

- [ ] **Step 4: Verify GREEN and no regression**

Run: `pytest tests/test1/test_breadcrumb.py -v` → all pass. Then `pytest tests -q` → no failures. `task check && task format` → clean.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/breadcrumb.py tests/test1/test_breadcrumb.py tests/test1/app/templates/app/breadcrumb_label.html superpowers/specs/2026-10-23-breadcrumb-label-design.md superpowers/plans/2026-10-23-breadcrumb-label.md
git commit -m "feat(breadcrumb): breadcrumb label separate from the short label (#271)"
```

### Task 2: E111 check, docs, changelog

**Files:**
- Modify: `src/crud_views/lib/breadcrumb.py` (`CrudViewBreadcrumbMixin.checks()`, ~line 93)
- Modify: `docs/reference/breadcrumb.md` (members table ~line 63; short example section)
- Modify: `CHANGELOG.md` (`## Unreleased` → `### Added`, ~line 161)
- Test: `tests/test1/test_breadcrumb.py`

**Interfaces:**
- Consumes: Task 1's attributes; `CheckTemplate` from `crud_views.lib.check` (`CheckTemplate(context=..., id="E111", attribute=...)`, `.messages()` yields `Error` with id `"viewset.E111"`).

- [ ] **Step 1: Write the failing tests** (no DB needed):

```python
def test_check_missing_breadcrumb_label_template():
    class V(PublisherBcCreateView):
        cv_breadcrumb_label_template = "does-not-exist.html"
    msgs = [m for c in V.checks() for m in c.messages() if m.id == "viewset.E111"]
    assert len(msgs) == 1 and "does-not-exist.html" in msgs[0].msg

def test_check_unset_breadcrumb_label_template():
    msgs = [m for c in PublisherBcCreateView.checks() for m in c.messages() if m.id == "viewset.E111"]
    assert msgs == []
```

- [ ] **Step 2: Run to verify RED** — `pytest tests/test1/test_breadcrumb.py -k check_ -v`: the missing-template test FAILS (no E111), the unset test passes.

- [ ] **Step 3: Implement** — in `checks()` after the existing `CheckBreadcrumbKeyObject`, yield `CheckTemplate(context=cls, id="E111", attribute="cv_breadcrumb_label_template")`.

- [ ] **Step 4: Verify GREEN** — `pytest tests -q` all pass; `task check && task format` clean.

- [ ] **Step 5: Docs** — in `docs/reference/breadcrumb.md` add table rows for `cv_breadcrumb_label_template` / `cv_breadcrumb_label_template_code` (`None`; current-page item label, falls back to the short action label; no effect on detail and container views; template variables `verbose_name`, `verbose_name_plural`, `object`, …; a missing template triggers `viewset.E111`) and `cv_get_breadcrumb_label(context)`; add the `NoteCreateView` example from the spec. CHANGELOG `### Added`: one entry referencing #271. Run `uv run mkdocs build --strict` (or `task docs` build equivalent) → no warnings.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/breadcrumb.py tests/test1/test_breadcrumb.py docs/reference/breadcrumb.md CHANGELOG.md
git commit -m "feat(breadcrumb): check, docs and changelog for the breadcrumb label (#271)"
```
