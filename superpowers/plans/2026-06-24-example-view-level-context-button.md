# Bootstrap5 Example: View-level Context Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a view-only context button ("Bazzes") to `BarDetailView` in the bootstrap5 example so the example demonstrates the `cv_context_buttons` feature (#27), with a smoke test proving it renders on the detail page and not on the list page.

**Architecture:** Single example file change (`examples/bootstrap5/app/views/bar.py`): declare `cv_context_buttons` on `BarDetailView` with a `ChildContextButton` to the bar's `baz` collection, and list its key in that view's `cv_context_actions`. A Django `TestCase` in the example app renders the Bar detail and list pages and asserts the button's presence/absence.

**Tech Stack:** Django, crud_views (`ChildContextButton`), Django test client. The example runs on the repo's root venv (no local `.venv`).

**Spec:** `superpowers/specs/2026-06-24-example-view-level-context-button-design.md` (issue #27, example demo).

## Global Constraints

- Example-only change. NO library/source edits under `src/`, NO new model, NO migration.
- The button is `ChildContextButton(key="bazzes", child_name="baz", label_template_code="Bazzes")`, declared in `BarDetailView.cv_context_buttons`.
- `BarDetailView.cv_context_actions = ["home", "detail", "update", "delete", "bazzes"]` (the inherited default detail actions `["home", "detail", "update", "delete"]` plus `"bazzes"`).
- The button must render ONLY on the Bar detail page, never on the Bar list page (which keeps its ViewSet-level `"Quxes"` button).
- Line length 120, double quotes, ruff-formatted.
- The example test runs from `examples/bootstrap5/` via `uv run python manage.py test app`. It is NOT part of the nox CI matrix (which only runs `tests/test1`); it is a runnable, repeatable artifact for local verification.
- Additive / backwards compatible: no change to other example views or existing Bar pages beyond the added detail-view button.

---

### Task 1: View-only "Bazzes" button on BarDetailView + smoke test

**Files:**
- Modify: `examples/bootstrap5/app/views/bar.py` (import line 17; `BarDetailView` at lines 57-70)
- Test: `examples/bootstrap5/app/tests.py` (replace the empty placeholder)

**Interfaces:**
- Consumes: `ChildContextButton` from `crud_views.lib.view`; `cv_bar` (`app.views.bar`), `cv_baz` (`app.views.baz`); models `Foo`, `Bar`, `Baz` (`app.models`); ViewSet router names via `cv_bar.get_router_name("list"|"detail")` and `cv_baz.get_router_name("list")`. URL kwargs: bar list `{"foo_pk": foo.pk}`, bar detail `{"foo_pk": foo.pk, "pk": bar.pk}`, baz list `{"foo_pk": foo.pk, "bar_pk": bar.pk}`.
- Produces: a rendered `"Bazzes"` button on the Bar detail page linking to that bar's baz list.

- [ ] **Step 1: Write the failing test**

Replace the contents of `examples/bootstrap5/app/tests.py` with:

```python
"""Smoke test for the view-level context button on BarDetailView (issue #27 example)."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Foo, Bar, Baz
from app.views.bar import cv_bar
from app.views.baz import cv_baz


class ViewLevelContextButtonTest(TestCase):
    def setUp(self):
        self.foo = Foo.objects.create(name="Foo1")
        self.bar = Bar.objects.create(foo=self.foo, name="Bar1")
        self.baz = Baz.objects.create(bar=self.bar, name="Baz1")
        user = User.objects.create_superuser(username="admin", password="pw")
        self.client.force_login(user)

    def test_bazzes_button_on_bar_detail(self):
        url = reverse(cv_bar.get_router_name("detail"), kwargs={"foo_pk": self.foo.pk, "pk": self.bar.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # the view-level "Bazzes" button appears on the detail page...
        self.assertContains(resp, "Bazzes")
        # ...and links to this bar's baz collection
        baz_url = reverse(cv_baz.get_router_name("list"), kwargs={"foo_pk": self.foo.pk, "bar_pk": self.bar.pk})
        self.assertContains(resp, baz_url)

    def test_bazzes_absent_on_bar_list(self):
        url = reverse(cv_bar.get_router_name("list"), kwargs={"foo_pk": self.foo.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # the view-level button does NOT leak onto the list view...
        self.assertNotContains(resp, "Bazzes")
        # ...which still shows the ViewSet-level sibling button
        self.assertContains(resp, "Quxes")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd examples/bootstrap5 && uv run python manage.py test app -v 2`
Expected: `test_bazzes_button_on_bar_detail` FAILS on `self.assertContains(resp, "Bazzes")` — the button does not exist yet (the detail page renders 200 but contains no "Bazzes"). `test_bazzes_absent_on_bar_list` already passes (the button was never on the list).

- [ ] **Step 3: Add the import**

In `examples/bootstrap5/app/views/bar.py`, extend the existing button import (line 17):

```python
from crud_views.lib.view import SiblingContextButton, ChildContextButton
```

- [ ] **Step 4: Declare the view-level button on BarDetailView**

In `examples/bootstrap5/app/views/bar.py`, update `BarDetailView` (lines 57-70) to add `cv_context_buttons` and `cv_context_actions` (leave `cv_property_display` as-is):

```python
class BarDetailView(DetailViewPermissionRequired):
    model = Bar
    cv_viewset = cv_bar
    # View-level button: declared on this view only, so it renders on the Bar
    # detail page but not on bar's list/update/etc. Contrast with the ViewSet-level
    # "Quxes" sibling button (cv_bar.context_buttons), which the list view shows.
    cv_context_buttons = [
        ChildContextButton(key="bazzes", child_name="baz", label_template_code="Bazzes"),
    ]
    cv_context_actions = ["home", "detail", "update", "delete", "bazzes"]
    cv_property_display = [
        {
            "title": _("Properties"),
            "icon": "bone",
            "description": _("Bar attributes"),
            "properties": [
                "id",
                "name",
            ],
        },
    ]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd examples/bootstrap5 && uv run python manage.py test app -v 2`
Expected: PASS (2 tests OK).

- [ ] **Step 6: Format**

Run: `uv run ruff format examples/bootstrap5/app/views/bar.py examples/bootstrap5/app/tests.py`
Then: `uv run ruff check examples/bootstrap5/app/views/bar.py examples/bootstrap5/app/tests.py`
Expected: formatted / "All checks passed!"

- [ ] **Step 7: Commit**

```bash
git add examples/bootstrap5/app/views/bar.py examples/bootstrap5/app/tests.py
git commit -m "docs(example): demo view-level context button on BarDetailView (#27)"
```

---

### Task 2: Verification

**Files:** none (verification only).

- [ ] **Step 1: Re-run the example test**

Run: `cd examples/bootstrap5 && uv run python manage.py test app -v 2`
Expected: 2 tests pass — confirms the Bar detail page renders 200 with the "Bazzes" button linking to the baz list, and the list page renders without it.

- [ ] **Step 2: Confirm the library suite is unaffected**

The change is example-only, but confirm nothing in the package regressed:
Run: `cd tests && uv run pytest -q`
Expected: 416 passed, 1 skipped (unchanged from before — the example is not part of this suite, so this is a sanity check that no shared file was touched).

- [ ] **Step 3: Confirm clean tree**

Run: `git status --short`
Expected: empty (Task 1 committed everything).

---

## Notes for the implementer

- Do NOT touch anything under `src/` — the `cv_context_buttons` feature already shipped; this is purely an example demonstrating it.
- The `"bazzes"` key is registered by being declared in `cv_context_buttons`, so listing it in `cv_context_actions` is safe (no unregistered-key 500 like issue #56). Every other key in the list (`home`/`detail`/`update`/`delete`) is a standard registered view.
- `ChildContextButton` needs the current object to build the child URL — that is why it belongs on the detail view (an object view) and is the natural reason to scope it per-view.
- If `uv run` from `examples/bootstrap5/` fails to find the environment, run from the repo root with the venv active: `python examples/bootstrap5/manage.py test app` (cwd must let `app` and `project` import — prefer running from inside `examples/bootstrap5/`).
