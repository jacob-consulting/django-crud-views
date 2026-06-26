# Conditional Field-Groups & Conditional FormSets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a checkbox toggle govern a group of form fields (or an entire first-level formset): when off, the group is hidden client-side and — server-side, authoritatively — skips validation and clears its data; when on, its required fields are enforced.

**Architecture:** Two parallel constructs over one shared `ToggleSource` abstraction. `ConditionalGroup` (a form mixin) owns field-group validation in `Form.clean()`. `ConditionalFormSet` (declared on a `FormSet`) hooks the existing `FormSets.all_valid()` / save gate to skip or purge a whole first-level formset. A bundled `toggle.js` does show/hide only — it is never the authority. New code lives in a cohesive `crud_views/lib/conditional/` package.

**Tech Stack:** Django forms/formsets, crispy-forms (`LayoutObject`), Pydantic (FormSet config models), Django system checks, jQuery (matches existing `formset.js`), pytest.

## Global Constraints

- Line length: 120 characters (ruff); quote style: double quotes.
- All `CrudView` class attributes use the `cv_` prefix.
- Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0 must all pass.
- Server-side validation is the sole authority; JavaScript is cosmetic only and must never be required for correct validation/clearing.
- Scope: main form + **first-level** formsets only. Nested (level > 0) formsets are explicitly out of scope and must remain unaffected.
- Tests run from `tests/`: `cd tests && pytest`. Test DB is in-memory SQLite synced via run-syncdb (no migration files needed for new test models).
- New runtime imports must stay lazy/safe where the existing code is (the project has `test_import_safety.py`).

---

## File Structure

**New package — `src/crud_views/lib/conditional/`:**
- `__init__.py` — public exports.
- `toggle.py` — `ToggleSource`, `ModelFieldToggle`, `UIFieldToggle`.
- `group.py` — `ConditionalGroup`, `ConditionalGroupFormMixin`, `ConditionalGroupModelForm`.
- `layout.py` — `ToggleGroup` crispy layout object.
- `formset.py` — `ConditionalFormSet`.

**Modified:**
- `src/crud_views/lib/formsets/formsets.py` — `FormSet.conditional` field; `FormSets.apply_conditional()`, skip/purge in `is_valid()`/`save()`.
- `src/crud_views/lib/formsets/render_tree.py` — `XFormSet.cv_active` flag.
- `src/crud_views/lib/formsets/mixins.py` — call `apply_conditional()` in `cv_form_is_valid`.
- `src/crud_views/checks.py` — guardrail checks.
- `src/crud_views/lib/crispy/__init__.py` — re-export conditional names for ergonomics.

**New static/template:**
- `src/crud_views/static/crud_views/js/toggle.js` — cosmetic show/hide.
- `src/crud_views/templates/crud_views/conditional/toggle_group.html` — wrapper + script include.

**Tests (in `tests/test1/`):**
- `app/models.py` — add `Profile` + `ProfileItem` test models.
- `test_conditional_toggle.py`, `test_conditional_group.py`, `test_conditional_layout.py`, `test_conditional_formset.py`, `test_conditional_checks.py`.

**Docs:** `docs/reference/conditional.md`, `mkdocs.yml` nav entry, `CHANGELOG.md`.

---

## Task 1: ToggleSource abstraction

**Files:**
- Create: `src/crud_views/lib/conditional/__init__.py`
- Create: `src/crud_views/lib/conditional/toggle.py`
- Test: `tests/test1/test_conditional_toggle.py`

**Interfaces:**
- Produces:
  - `class ToggleSource` with `name: str`, `is_on(form) -> bool`, `field_name() -> str`.
  - `class ModelFieldToggle(ToggleSource)` — reads a field already on the form.
  - `class UIFieldToggle(ToggleSource)` — same read logic; marks itself injectable via `inject: bool = True`.
- `is_on(form)` reads `form.cleaned_data[name]` when present (form already cleaned), else coerces from raw `form.data` (Django checkbox semantics: present & not in `("", "false", "0", "off")` ⇒ True; absent ⇒ False). Never reads any JS/DOM state.

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_toggle.py
from django import forms

from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle


class _ToggleForm(forms.Form):
    flag = forms.BooleanField(required=False)


def test_is_on_reads_cleaned_data_true():
    form = _ToggleForm(data={"flag": "on"})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is True


def test_is_on_reads_cleaned_data_false_when_absent():
    form = _ToggleForm(data={})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is False


def test_is_on_falls_back_to_raw_data_before_clean():
    form = _ToggleForm(data={"flag": "on"})  # not yet validated
    assert UIFieldToggle("flag").is_on(form) is True


def test_is_on_raw_data_falsey_strings():
    form = _ToggleForm(data={"flag": "false"})
    assert ModelFieldToggle("flag").is_on(form) is False


def test_ui_field_toggle_is_injectable():
    assert UIFieldToggle("flag").inject is True
    assert ModelFieldToggle("flag").inject is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_toggle.py -v`
Expected: FAIL — `ModuleNotFoundError: crud_views.lib.conditional.toggle`

- [ ] **Step 3: Write minimal implementation**

```python
# src/crud_views/lib/conditional/__init__.py
```
(empty for now; exports added in Task 7)

```python
# src/crud_views/lib/conditional/toggle.py
from __future__ import annotations

from django.forms import BaseForm

_FALSEY = {"", "false", "0", "off", "none"}


class ToggleSource:
    """Resolve a boolean toggle from a form's *submitted* data — never from JS.

    Subclasses differ only in whether the toggle field is a persisted model
    field (``ModelFieldToggle``) or a transient, injected UI field
    (``UIFieldToggle``).
    """

    inject: bool = False

    def __init__(self, name: str):
        self.name = name

    def field_name(self) -> str:
        return self.name

    def is_on(self, form: BaseForm) -> bool:
        # Prefer cleaned_data once the form has been validated.
        cleaned = getattr(form, "cleaned_data", None)
        if cleaned is not None and self.name in cleaned:
            return bool(cleaned[self.name])
        # Fall back to raw submitted data (checkbox semantics).
        raw = form.data.get(form.add_prefix(self.name)) if form.is_bound else None
        if raw is None:
            return False
        return str(raw).strip().lower() not in _FALSEY


class ModelFieldToggle(ToggleSource):
    """Toggle backed by a real field already present on the form/model."""

    inject = False


class UIFieldToggle(ToggleSource):
    """Toggle backed by a transient, non-model BooleanField.

    For field-groups (``ConditionalGroup``) the form mixin injects this field
    automatically. For conditional formsets the field must already exist on the
    parent form (declare it, or reuse the group mixin)."""

    inject = True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_toggle.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/conditional/__init__.py src/crud_views/lib/conditional/toggle.py tests/test1/test_conditional_toggle.py
git commit -m "feat(conditional): ToggleSource abstraction (model + UI toggles)"
```

---

## Task 2: ConditionalGroup + form mixin (Kind 1 server-side authority)

**Files:**
- Create: `src/crud_views/lib/conditional/group.py`
- Modify: `tests/test1/app/models.py` (add `Profile`, `ProfileItem`)
- Test: `tests/test1/test_conditional_group.py`

**Interfaces:**
- Consumes: `ToggleSource`, `UIFieldToggle` (Task 1).
- Produces:
  - `class ConditionalGroup` with `toggle: ToggleSource`, `fields: list[str]`, `required: list[str] | None = None`, `empty_values: dict[str, Any] | None = None`; methods `is_on(form)`, `required_fields` (property → `required` or all `fields`), `empty_value_for(name)` (→ `empty_values[name]` else `None`).
  - `class ConditionalGroupFormMixin` with class attr `cv_conditional_groups: list[ConditionalGroup] = []`; overrides `__init__` (inject UI toggles, set group fields `required=False`) and `clean()` (enforce required when on, clear when off).
  - `class ConditionalGroupModelForm(ConditionalGroupFormMixin, CrispyModelForm)`.

**Test models to add to `tests/test1/app/models.py`** (append near the other plain models):

```python
class Profile(models.Model):
    name = models.CharField(max_length=100)
    with_contact = models.BooleanField(default=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class ProfileItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="items")
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_group.py
import pytest
from django import forms

from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle
from tests.test1.app.models import Profile

pytestmark = pytest.mark.django_db


class ContactForm(ConditionalGroupFormMixin, forms.ModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_contact"),
            fields=["email", "phone"],
            required=["email"],
        ),
    ]

    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]


def test_required_enforced_when_toggle_on():
    form = ContactForm(data={"name": "a", "with_contact": "on", "email": "", "phone": ""})
    assert form.is_valid() is False
    assert "email" in form.errors
    assert "phone" not in form.errors  # phone is not in required list


def test_valid_when_toggle_on_and_required_present():
    form = ContactForm(data={"name": "a", "with_contact": "on", "email": "x@y.z", "phone": ""})
    assert form.is_valid() is True


def test_skips_required_when_toggle_off():
    form = ContactForm(data={"name": "a", "email": "", "phone": ""})  # with_contact absent => off
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None


def test_clears_smuggled_values_when_toggle_off():
    # Tampering / JS-failure: toggle off but values present => server wipes them.
    form = ContactForm(data={"name": "a", "email": "x@y.z", "phone": "123"})
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None
    assert form.cleaned_data["phone"] is None


def test_ui_field_toggle_is_injected_and_not_a_model_field():
    class UIForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(toggle=UIFieldToggle("has_contact"), fields=["email"]),
        ]

        class Meta:
            model = Profile
            fields = ["name", "email"]

    form = UIForm(data={"name": "a"})
    assert "has_contact" in form.fields
    assert form.fields["email"].required is False
    assert form.is_valid() is True
    assert form.cleaned_data["email"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_group.py -v`
Expected: FAIL — `ModuleNotFoundError: crud_views.lib.conditional.group` (and missing `Profile`)

- [ ] **Step 3a: Add test models**

Append the `Profile` and `ProfileItem` classes (shown in Interfaces above) to `tests/test1/app/models.py`.

- [ ] **Step 3b: Write minimal implementation**

```python
# src/crud_views/lib/conditional/group.py
from __future__ import annotations

from typing import Any

from django.forms import BooleanField

from .toggle import ToggleSource


class ConditionalGroup:
    """A group of form fields governed by a single boolean toggle.

    When the toggle is on, ``required`` fields are enforced. When off, every
    field in the group is cleared to its empty value and never validated.
    """

    def __init__(
        self,
        toggle: ToggleSource,
        fields: list[str],
        required: list[str] | None = None,
        empty_values: dict[str, Any] | None = None,
    ):
        self.toggle = toggle
        self.fields = list(fields)
        self.required = list(required) if required is not None else None
        self.empty_values = empty_values or {}

    @property
    def required_fields(self) -> list[str]:
        return self.required if self.required is not None else self.fields

    def is_on(self, form) -> bool:
        return self.toggle.is_on(form)

    def empty_value_for(self, name: str) -> Any:
        return self.empty_values.get(name, None)


class ConditionalGroupFormMixin:
    """Server-side authority for conditional field-groups.

    Mix in *before* the concrete Form/ModelForm. JS is irrelevant to the
    outcome: an off group is always cleared, an on group always enforces its
    required fields, regardless of what the client submitted.
    """

    cv_conditional_groups: list[ConditionalGroup] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for group in self.cv_conditional_groups:
            # Inject transient UI toggle fields that are not model fields.
            tname = group.toggle.field_name()
            if group.toggle.inject and tname not in self.fields:
                self.fields[tname] = BooleanField(required=False)
            # Disarm Django's premature field-level required check; clean() owns it.
            for name in group.fields:
                if name in self.fields:
                    self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        for group in self.cv_conditional_groups:
            if group.is_on(self):
                for name in group.required_fields:
                    if cleaned.get(name) in self.fields[name].empty_values:
                        self.add_error(name, self.fields[name].error_messages["required"])
            else:
                for name in group.fields:
                    cleaned[name] = group.empty_value_for(name)
        return cleaned
```

Note: `ConditionalGroupModelForm` is added in Task 7 (it imports `CrispyModelForm`; keeping it out of `group.py` here avoids a crispy import in the core mixin and keeps Task 2 dependency-free). Tests in this task use a plain `ModelForm` + the mixin.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_group.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/conditional/group.py tests/test1/app/models.py tests/test1/test_conditional_group.py
git commit -m "feat(conditional): ConditionalGroup form mixin with server-side authority"
```

---

## Task 3: ToggleGroup layout object + toggle.js (Kind 1 cosmetic)

**Files:**
- Create: `src/crud_views/lib/conditional/layout.py`
- Create: `src/crud_views/templates/crud_views/conditional/toggle_group.html`
- Create: `src/crud_views/static/crud_views/js/toggle.js`
- Test: `tests/test1/test_conditional_layout.py`

**Interfaces:**
- Consumes: crispy `LayoutObject`, `Div`/`Layout`.
- Produces: `class ToggleGroup(LayoutObject)` — `__init__(self, toggle_field: str, *fields, css_class: str | None = None)`; `render()` wraps the inner fields in `<div class="cv-toggle-group" cv-data-toggle-field="<name>">…</div>` and includes `toggle.js` once.

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_layout.py
import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row
from crispy_forms.utils import render_crispy_form
from django import forms

from crud_views.lib.conditional.layout import ToggleGroup
from crud_views.lib.crispy import Column6
from tests.test1.app.models import Profile

pytestmark = pytest.mark.django_db


class _LayoutForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        h = FormHelper()
        h.layout = Layout(
            Row(Column6("name"), Column6("with_contact")),
            ToggleGroup("with_contact", Row(Column6("email"), Column6("phone"))),
        )
        return h


def test_toggle_group_renders_marker_attributes():
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert 'cv-data-toggle-field="with_contact"' in html
    assert "cv-data-toggle-group" in html
    assert "email" in html and "phone" in html


def test_toggle_group_includes_toggle_js():
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "crud_views/js/toggle.js" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_layout.py -v`
Expected: FAIL — `ModuleNotFoundError: crud_views.lib.conditional.layout`

- [ ] **Step 3a: Write the layout object**

```python
# src/crud_views/lib/conditional/layout.py
from __future__ import annotations

from crispy_forms.layout import Div, Layout, LayoutObject
from django.template.loader import render_to_string


class ToggleGroup(LayoutObject):
    """Crispy layout wrapper for a conditional field-group.

    Renders the wrapped fields inside a marker div that ``toggle.js`` keys off.
    Cosmetic only — validation/clearing is enforced server-side by
    ``ConditionalGroupFormMixin``.
    """

    template = "crud_views/conditional/toggle_group.html"

    def __init__(self, toggle_field: str, *fields, css_class: str | None = None):
        self.toggle_field = toggle_field
        self.css_class = css_class
        self.inner = Layout(*fields)

    def render(self, form, context, **kwargs):
        inner_html = self.inner.render(form, context, **kwargs)
        context.update(
            {
                "cv_toggle_field": self.toggle_field,
                "cv_toggle_css": self.css_class or "",
                "cv_toggle_inner": inner_html,
            }
        )
        return render_to_string(self.template, context.flatten())
```

- [ ] **Step 3b: Write the template**

```django
{# src/crud_views/templates/crud_views/conditional/toggle_group.html #}
{% load static %}
<div class="cv-toggle-group {{ cv_toggle_css }}" cv-data-toggle-group cv-data-toggle-field="{{ cv_toggle_field }}">
    {{ cv_toggle_inner }}
</div>
<script src="{% static 'crud_views/js/toggle.js' %}"></script>
```

- [ ] **Step 3c: Write toggle.js (cosmetic, idempotent)**

```javascript
// src/crud_views/static/crud_views/js/toggle.js
(function () {
    if (window.__cvToggleInit) {
        return;
    }
    window.__cvToggleInit = true;

    function findCheckbox(scope, name) {
        // Match the toggle checkbox within the nearest form/row scope.
        return scope.querySelector(
            'input[type="checkbox"][name="' + name + '"], input[type="checkbox"][name$="-' + name + '"]'
        );
    }

    function apply(group, checkbox) {
        var on = checkbox.checked;
        group.style.display = on ? "" : "none";
        group.querySelectorAll("input, select, textarea").forEach(function (el) {
            el.disabled = !on;
        });
    }

    function wireGroups(root) {
        root.querySelectorAll("[cv-data-toggle-group]").forEach(function (group) {
            var name = group.getAttribute("cv-data-toggle-field");
            var scope = group.closest("form") || document;
            var checkbox = findCheckbox(scope, name);
            if (!checkbox) {
                return;
            }
            apply(group, checkbox);
            checkbox.addEventListener("change", function () {
                apply(group, checkbox);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        wireGroups(document);
    });
})();
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_layout.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/conditional/layout.py src/crud_views/templates/crud_views/conditional/toggle_group.html src/crud_views/static/crud_views/js/toggle.js tests/test1/test_conditional_layout.py
git commit -m "feat(conditional): ToggleGroup layout object + cosmetic toggle.js"
```

---

## Task 4: ConditionalFormSet + gate/save integration (Kind 2 server-side authority)

**Files:**
- Create: `src/crud_views/lib/conditional/formset.py`
- Modify: `src/crud_views/lib/formsets/render_tree.py` (add `cv_active`)
- Modify: `src/crud_views/lib/formsets/formsets.py` (`FormSet.conditional`, `FormSets.apply_conditional`, skip/purge)
- Modify: `src/crud_views/lib/formsets/mixins.py` (`cv_form_is_valid` calls `apply_conditional`)
- Test: `tests/test1/test_conditional_formset.py`

**Interfaces:**
- Consumes: `ToggleSource` (Task 1), `FormSet`/`FormSets`/`XFormSet` (existing).
- Produces:
  - `class ConditionalFormSet` (Pydantic `BaseModel`, `arbitrary_types_allowed=True`) with `toggle: ToggleSource`, `on_off: Literal["skip", "purge"] = "skip"`.
  - `FormSet.conditional: ConditionalFormSet | None = None`.
  - `XFormSet.cv_active: bool = True`.
  - `FormSets.apply_conditional(main_form) -> None` — sets `cv_active` on each top-level x_formset from its `formset.conditional.toggle.is_on(main_form)`; nested x_formsets stay active.
  - `FormSets.is_valid()` skips x_formsets where `cv_active is False`.
  - `FormSets.save()` for inactive x_formset: `on_off == "purge"` deletes related rows, else does nothing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_formset.py
import pytest

from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.toggle import ModelFieldToggle

from tests.test1.app.models import Profile, ProfileItem

pytestmark = pytest.mark.django_db


def test_conditional_formset_defaults_to_skip():
    cond = ConditionalFormSet(toggle=ModelFieldToggle("with_items"))
    assert cond.on_off == "skip"


def test_apply_conditional_marks_top_level_inactive_when_off(profile_formsets_off):
    formsets, main_form = profile_formsets_off
    formsets.apply_conditional(main_form)
    assert all(x.cv_active is False for x in formsets.x_formsets)


def test_all_valid_true_when_off_even_with_blank_required_rows(profile_formsets_off):
    # An off formset must NOT fail validation even though its row's field is required.
    formsets, main_form = profile_formsets_off
    formsets.apply_conditional(main_form)
    assert formsets.all_valid() is True


def test_purge_deletes_existing_rows_when_off(profile_with_items_purge_off):
    formsets, main_form, profile = profile_with_items_purge_off
    assert ProfileItem.objects.filter(profile=profile).count() == 2
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)
    assert ProfileItem.objects.filter(profile=profile).count() == 0


def test_skip_leaves_existing_rows_when_off(profile_with_items_skip_off):
    formsets, main_form, profile = profile_with_items_skip_off
    assert ProfileItem.objects.filter(profile=profile).count() == 2
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)
    assert ProfileItem.objects.filter(profile=profile).count() == 2
```

Add these fixtures to `tests/test1/test_conditional_formset.py` (self-contained; they build a `FormSets` the same way the example app does). **Place all of these `import` statements at the very top of the file with the other imports — not below the test functions — or ruff's E402 will fail CI. Run `ruff format` on the file before committing.**

```python
from collections import OrderedDict

from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory
from django.test import RequestFactory

from crud_views.lib.crispy import Column8, CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet


class _ProfileForm(CrispyModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_items"]

    def get_layout_fields(self):
        return [Row(Column8("name"))]


class _ItemForm(CrispyModelForm):
    class Meta:
        model = ProfileItem
        fields = ["label"]


class _ItemInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("label"), self.form_control_col4)]


def _make(on_off, with_contact_value, profile=None, items=()):
    # Add a transient model field for the toggle on Profile via a UI toggle would
    # require a form field; here we reuse a real BooleanField "with_items".
    ItemFormSet = inlineformset_factory(
        Profile, ProfileItem, formset=_ItemInlineFormSet, form=_ItemForm,
        fields=["label"], extra=1, can_delete=True,
    )
    formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items", klass=ItemFormSet, fields=["label"], pk_field="id",
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off=on_off),
            )
        )
    )
    rf = RequestFactory()
    post = {
        "name": "p", "with_items": with_contact_value,
        "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
        "items-0-label": "",  # blank required row
    }
    request = rf.post("/", data=post)
    main_form = _ProfileForm(cv_view=None, data=post, instance=profile)
    main_form.is_valid()
    formsets = formsets.clone(cv_view=None)
    formsets.init(request=request, form=main_form, instance=profile)
    return formsets, main_form, profile


@pytest.fixture
def profile_formsets_off():
    formsets, main_form, _ = _make("skip", "")  # with_items off
    return formsets, main_form


@pytest.fixture
def profile_with_items_purge_off():
    profile = Profile.objects.create(name="p", with_items=False)
    ProfileItem.objects.create(profile=profile, label="a")
    ProfileItem.objects.create(profile=profile, label="b")
    formsets, main_form, _ = _make("purge", "", profile=profile)
    return formsets, main_form, profile


@pytest.fixture
def profile_with_items_skip_off():
    profile = Profile.objects.create(name="p", with_items=False)
    ProfileItem.objects.create(profile=profile, label="a")
    ProfileItem.objects.create(profile=profile, label="b")
    formsets, main_form, _ = _make("skip", "", profile=profile)
    return formsets, main_form, profile
```

Also add `with_items = models.BooleanField(default=False)` to the `Profile` model from Task 2.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_formset.py -v`
Expected: FAIL — `ModuleNotFoundError: crud_views.lib.conditional.formset`

- [ ] **Step 3a: Add `with_items` to Profile**

In `tests/test1/app/models.py`, add to `Profile`:

```python
    with_items = models.BooleanField(default=False)
```

- [ ] **Step 3b: Create ConditionalFormSet model**

```python
# src/crud_views/lib/conditional/formset.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .toggle import ToggleSource


class ConditionalFormSet(BaseModel, arbitrary_types_allowed=True):
    """Governs whether an entire first-level formset is shown/validated.

    Declared on a ``FormSet`` via ``conditional=``. When the parent-form toggle
    is off, the formset is excluded from the validity gate; on save, ``skip``
    leaves existing rows untouched while ``purge`` deletes them.
    """

    toggle: ToggleSource
    on_off: Literal["skip", "purge"] = "skip"
```

- [ ] **Step 3c: Add `cv_active` to XFormSet**

`XFormSet` is a Pydantic `BaseModel` (`class XFormSet(BaseModel, arbitrary_types_allowed=True)`). Add a typed field with a default near the other attributes (after `formset: Any`):

```python
    cv_active: bool = True
```

- [ ] **Step 3d: Wire FormSet/FormSets**

In `src/crud_views/lib/formsets/formsets.py`:

Add the import and field on `FormSet`:

```python
from crud_views.lib.conditional.formset import ConditionalFormSet
```
```python
    conditional: ConditionalFormSet | None = None
```

Add to `FormSets` the `apply_conditional` method and skip/purge logic:

```python
    def apply_conditional(self, main_form) -> None:
        """Set cv_active on each top-level x_formset from its conditional toggle.

        Reads the toggle from the *submitted* main form only. Nested formsets
        are out of scope and always remain active."""
        for x_formset in self.x_formsets:
            conditional = x_formset.formset.conditional
            if conditional is None:
                x_formset.cv_active = True
            else:
                x_formset.cv_active = conditional.toggle.is_on(main_form)
```

Update `is_valid` to skip inactive top-level formsets:

```python
    def is_valid(self) -> Iterable[Tuple[Any, bool]]:
        for x_formset in self.x_formsets:
            if x_formset.cv_active is False:
                continue
            yield from x_formset.is_valid()
```

Update `save` to honor skip/purge:

```python
    def save(self, commit: bool = True):
        for x_formset in self.x_formsets:
            if x_formset.cv_active is False:
                conditional = x_formset.formset.conditional
                if conditional is not None and conditional.on_off == "purge":
                    fs = x_formset.instance  # bound BaseInlineFormSet
                    if fs.instance.pk:  # safety: never filter on a null parent FK
                        fk_name = fs.fk.name
                        fs.model.objects.filter(**{fk_name: fs.instance}).delete()
                continue
            x_formset.save(commit=commit)
```

- [ ] **Step 3e: Call apply_conditional in the gate**

In `src/crud_views/lib/formsets/mixins.py`, inside `cv_form_is_valid`, before `formsets.all_valid()`:

```python
        # Evaluate conditional formsets from the submitted main form (server authority).
        formsets.apply_conditional(context["form"])
        all_formsets_valid = formsets.all_valid()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_formset.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Run the full formset suite for regressions**

Run: `cd tests && pytest test1/test_formsets.py test1/test_formsets_parent_required.py test1/test_formsets_validation_gate.py -q`
Expected: PASS (no regressions; conditional defaults to None ⇒ all formsets active)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/conditional/formset.py src/crud_views/lib/formsets/render_tree.py src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/mixins.py tests/test1/app/models.py tests/test1/test_conditional_formset.py
git commit -m "feat(conditional): ConditionalFormSet skip/purge gate integration"
```

---

## Task 5: Cosmetic JS + template wiring for conditional formsets

**Files:**
- Modify: `src/crud_views/static/crud_views/js/toggle.js` (target formset blocks)
- Modify: `src/crud_views/templates/crud_views/formsets/formsets.html` (mark block + include toggle.js)
- Modify: `src/crud_views/lib/formsets/formsets.py` (`init_js_data` exposes conditional toggle field names per top-level key)
- Test: `tests/test1/test_conditional_formset.py` (render assertion appended)

**Interfaces:**
- Consumes: `FormSets.x_formsets`, `FormSet.conditional`.
- Produces: each top-level `cv-formset-content` block carries `cv-data-toggle-field="<name>"` when its formset is conditional; `toggle.js` hides/shows the block by the parent checkbox. Cosmetic only.

- [ ] **Step 1: Write the failing test (append to test_conditional_formset.py)**

```python
def test_formsets_html_marks_conditional_block():
    from django.template.loader import render_to_string

    formsets, main_form, _ = _make("skip", "")
    html = render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
    assert 'cv-data-toggle-field="with_items"' in html
    assert "crud_views/js/toggle.js" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_formset.py::test_formsets_html_marks_conditional_block -v`
Expected: FAIL — marker / script not present

- [ ] **Step 3a: Expose toggle field per top-level formset**

In `src/crud_views/lib/formsets/formsets.py`, extend `XFormSet` rendering data. Simplest path: add a property on `XFormSet` (render_tree.py) that returns its formset's conditional toggle field name or empty string:

```python
    @property
    def cv_toggle_field(self) -> str:
        conditional = self.formset.conditional
        return conditional.toggle.field_name() if conditional is not None else ""
```

- [ ] **Step 3b: Mark the block + include script in formsets.html**

Edit `src/crud_views/templates/crud_views/formsets/formsets.html`. Wrap each top-level formset render with a marker div and add the toggle.js include:

```django
{% load crud_views_formsets %}
{% load static %}

<link rel="stylesheet" href="{% static 'crud_views/css/formset.css' %}">
{% for x_formset in formsets.x_formsets %}
    {% if x_formset.cv_toggle_field %}
    <div cv-data-toggle-group cv-data-toggle-field="{{ x_formset.cv_toggle_field }}">
        {% cv_x_formset x_formset %}
    </div>
    {% else %}
    {% cv_x_formset x_formset %}
    {% endif %}
{% endfor %}

{% if formsets.scripts %}
    <script src="{% static "crud_views/js/formset.js" %}"></script>
    <script src="{% static "crud_views/js/toggle.js" %}"></script>
{% endif %}
```

Note: this also corrects the pre-existing wrong path `crud_views_fieldsets/js/formset.js` → `crud_views/js/formset.js` (the actual static location). Verify the static file path with `ls src/crud_views/static/crud_views/js/`.

- [ ] **Step 3c: toggle.js already handles `[cv-data-toggle-group]`**

No change needed — the formset block uses the same `cv-data-toggle-group` / `cv-data-toggle-field` markers `toggle.js` already wires (Task 3). Confirm `wireGroups` finds the checkbox in the enclosing `<form>` scope (parent toggle lives in the main form, same `<form>`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_formset.py::test_formsets_html_marks_conditional_block -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/static/crud_views/js/toggle.js src/crud_views/templates/crud_views/formsets/formsets.html src/crud_views/lib/formsets/render_tree.py tests/test1/test_conditional_formset.py
git commit -m "feat(conditional): cosmetic show/hide wiring for conditional formsets"
```

---

## Task 6: System checks (guardrails)

**Files:**
- Modify: `src/crud_views/checks.py`
- Test: `tests/test1/test_conditional_checks.py`

**Interfaces:**
- Consumes: `ViewSet` registry, `FormSet.conditional`, `ConditionalGroup`.
- Produces: a registered check function `check_conditional` returning Django `Error`/`Warning` messages with ids:
  - `crud_views.E310` — a `ConditionalFormSet` is declared on a **nested** formset (out of scope).
  - `crud_views.E311` — a `ConditionalFormSet`/`ConditionalGroup` toggle field is not present on the relevant form (and not injectable).
  - `crud_views.W320` — a `ConditionalGroup` clears a model field that is not `null=True`/`blank=True` (clear-on-off would fail at DB write).

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_checks.py
from crud_views.checks import _conditional_messages
from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.toggle import ModelFieldToggle


def test_nested_conditional_formset_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[("child", ConditionalFormSet(toggle=ModelFieldToggle("x")))],
        missing_toggles=[],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E310" for m in msgs)


def test_missing_toggle_field_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[("SomeForm", "with_x")],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E311" for m in msgs)


def test_non_nullable_clear_warned():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[],
        non_nullable_clears=[("SomeForm", "email")],
    )
    assert any(m.id == "crud_views.W320" for m in msgs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_checks.py -v`
Expected: FAIL — `ImportError: cannot import name '_conditional_messages'`

- [ ] **Step 3: Implement the check helper + registration**

In `src/crud_views/checks.py` add:

```python
from django.core.checks import Error, Warning as DjangoWarning


def _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears):
    """Pure formatter — turns collected findings into Django check messages.

    Kept separate from registry traversal so it is unit-testable without the
    full app registry."""
    messages = []
    for key, _conditional in nested_conditionals:
        messages.append(
            Error(
                f"ConditionalFormSet declared on nested formset '{key}'; only first-level formsets are supported.",
                hint="Move the conditional to the top-level formset or remove it.",
                id="crud_views.E310",
            )
        )
    for form_name, field in missing_toggles:
        messages.append(
            Error(
                f"Conditional toggle field '{field}' is not present on form '{form_name}'.",
                hint="Add the field to the form (model field) or use UIFieldToggle so it is injected.",
                id="crud_views.E311",
            )
        )
    for form_name, field in non_nullable_clears:
        messages.append(
            DjangoWarning(
                f"ConditionalGroup clears '{field}' on '{form_name}' but the model field is not null/blank.",
                hint="Set null=True, blank=True on the field, or provide empty_values for it.",
                id="crud_views.W320",
            )
        )
    return messages
```

Then add a registered traversal that collects findings and calls `_conditional_messages`:

```python
@register(TAG)
def check_conditional(app_configs=None, **kwargs):
    """Validate ConditionalGroup / ConditionalFormSet declarations."""
    nested_conditionals: list = []
    missing_toggles: list = []
    non_nullable_clears: list = []

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            formsets = getattr(view, "cv_formsets", None)
            if formsets is not None:
                # top-level only are allowed to carry a conditional
                def _walk(formset, key, is_top):
                    if formset.conditional is not None and not is_top:
                        nested_conditionals.append((key, formset.conditional))
                    for ckey, child in formset.children.items():
                        _walk(child, f"{key}-{ckey}", False)

                for key, fs in formsets.items():
                    _walk(fs, key, True)

            form_class = getattr(view, "form_class", None)
            groups = getattr(form_class, "cv_conditional_groups", None) if form_class else None
            if groups:
                model = getattr(getattr(form_class, "_meta", None), "model", None)
                declared = set(getattr(getattr(form_class, "_meta", None), "fields", []) or [])
                for group in groups:
                    tname = group.toggle.field_name()
                    if not group.toggle.inject and tname not in declared:
                        missing_toggles.append((form_class.__name__, tname))
                    if model is not None:
                        for fname in group.fields:
                            try:
                                mf = model._meta.get_field(fname)
                            except Exception:
                                continue
                            if not (getattr(mf, "null", False) and getattr(mf, "blank", False)):
                                if fname not in group.empty_values:
                                    non_nullable_clears.append((form_class.__name__, fname))

    return _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_checks.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Run full check + import-safety suite**

Run: `cd tests && pytest test1/test_import_safety.py -q && cd .. && python -c "import django; from tests.test1 import conftest" 2>/dev/null; echo done`
Expected: import-safety PASS.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/checks.py tests/test1/test_conditional_checks.py
git commit -m "feat(conditional): system checks for groups and conditional formsets"
```

---

## Task 7: Public exports, ConditionalGroupModelForm, docs, CHANGELOG

**Files:**
- Modify: `src/crud_views/lib/conditional/__init__.py`
- Modify: `src/crud_views/lib/conditional/group.py` (add `ConditionalGroupModelForm`)
- Create: `docs/reference/conditional.md`
- Modify: `mkdocs.yml` (nav)
- Modify: `docs/faq.md`
- Modify: `skills/django-crud-views/SKILL.md`
- Modify: `skills/django-crud-views/references/api-reference.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test1/test_conditional_exports.py`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: `ConditionalGroupModelForm(ConditionalGroupFormMixin, CrispyModelForm)`; importable public names from `crud_views.lib.conditional`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test1/test_conditional_exports.py
def test_public_exports():
    from crud_views.lib.conditional import (
        ToggleSource,
        ModelFieldToggle,
        UIFieldToggle,
        ConditionalGroup,
        ConditionalGroupFormMixin,
        ConditionalGroupModelForm,
        ToggleGroup,
        ConditionalFormSet,
    )

    assert issubclass(ConditionalGroupModelForm, ConditionalGroupFormMixin)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_exports.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3a: Add ConditionalGroupModelForm**

Append to `src/crud_views/lib/conditional/group.py`:

```python
from crud_views.lib.crispy import CrispyModelForm  # noqa: E402  (placed at end to avoid cycle)


class ConditionalGroupModelForm(ConditionalGroupFormMixin, CrispyModelForm):
    """CrispyModelForm with conditional field-group support."""

    pass
```

If a circular import arises (crispy importing conditional), keep the import inside the class module bottom as shown, or move `ConditionalGroupModelForm` to a new `group_form.py`. Verify with `cd tests && pytest test1/test_import_safety.py -q`.

- [ ] **Step 3b: Populate package exports**

```python
# src/crud_views/lib/conditional/__init__.py
from .toggle import ToggleSource, ModelFieldToggle, UIFieldToggle
from .group import (
    ConditionalGroup,
    ConditionalGroupFormMixin,
    ConditionalGroupModelForm,
)
from .layout import ToggleGroup
from .formset import ConditionalFormSet

__all__ = [
    "ToggleSource",
    "ModelFieldToggle",
    "UIFieldToggle",
    "ConditionalGroup",
    "ConditionalGroupFormMixin",
    "ConditionalGroupModelForm",
    "ToggleGroup",
    "ConditionalFormSet",
]
```

- [ ] **Step 3c: (Do NOT re-export from crispy)**

Do not add conditional names to `src/crud_views/lib/crispy/__init__.py`. `formsets.py` imports `ConditionalFormSet`, which triggers the `conditional` package `__init__` → `group` → `crud_views.lib.crispy`; if crispy also imported `conditional`, that is a guaranteed circular import. The canonical (and only) public path is `crud_views.lib.conditional`. This step is intentionally a no-op — leave `crispy/__init__.py` unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_exports.py -v`
Expected: PASS

- [ ] **Step 5a: Write docs reference page**

Create `docs/reference/conditional.md` documenting: the two constructs, `ToggleSource` (model vs UI), the off ⇒ skip-validation + clear contract, server-authority guarantee, `on_off="skip"|"purge"` for formsets, the first-level-only scope, and the system-check ids (E310/E311/W320). Link to the runnable bootstrap5 examples added in Task 8 (`cv_registration`, `cv_event`).

- [ ] **Step 5b: Add to mkdocs nav**

In `mkdocs.yml`, add `- Conditional groups: reference/conditional.md` under the existing Reference section (match indentation of sibling entries).

- [ ] **Step 5b-ii: Update the bundled skill — `SKILL.md`**

In `skills/django-crud-views/SKILL.md`, add a new section immediately after the `## Formsets (Inline Child Records)` section:

````markdown
## Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields (or an entire **first-level** formset). When off, the group/formset is hidden client-side and — authoritatively **server-side** — skips validation and clears its data. JS is cosmetic only; the server enforces the contract on every submit (tampered/JS-off POSTs included).

Import from `crud_views.lib.conditional`.

**Kind 1 — field-group in a form** (`ConditionalGroupModelForm` + `ToggleGroup`):

```python
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),   # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],                  # subset required when toggle is on
        ),
    ]
    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [Row(Column6("name"), Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")))]
```

Off ⇒ group fields are cleared (must be `null=True, blank=True`, or pass `empty_values=`). On ⇒ `required` fields enforced.

**Kind 2 — an entire first-level formset** (`ConditionalFormSet` on a `FormSet`):

```python
from crud_views.lib.conditional import ConditionalFormSet, ModelFieldToggle

sessions=FormSet(
    title="Sessions", klass=SessionFormSet, fields=["title"], pk_field="id",
    conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="skip"),
)
```

The parent-form toggle (`with_sessions`) governs the whole formset. `on_off="skip"` (default) leaves existing rows untouched when off; `on_off="purge"` deletes them on save. Only **first-level** formsets may be conditional (nested ⇒ check error `crud_views.E310`).

System checks: `E310` (conditional on nested formset), `E311` (toggle field missing from form), `W320` (cleared field not null/blank).
````

- [ ] **Step 5b-iii: Update the skill API reference**

In `skills/django-crud-views/references/api-reference.md`, add a `## Conditional Field-Groups` section after the `## Formsets` section documenting `ToggleSource`/`ModelFieldToggle`/`UIFieldToggle`, `ConditionalGroup` (with `fields`, `required`, `empty_values`), `ConditionalGroupFormMixin`/`ConditionalGroupModelForm`, `ToggleGroup`, and `ConditionalFormSet` (`toggle`, `on_off`). Then add to the **Import Paths Cheatsheet** at the end of that file:

```python
# Conditional field-groups / formsets
from crud_views.lib.conditional import (
    ToggleSource, ModelFieldToggle, UIFieldToggle,
    ConditionalGroup, ConditionalGroupFormMixin, ConditionalGroupModelForm,
    ToggleGroup, ConditionalFormSet,
)
```

- [ ] **Step 5b-iv: Add an FAQ entry**

In `docs/faq.md`, append a new question-style section (matching the existing `## How to…` format):

````markdown
## How do I make a group of fields required only when a checkbox is on?

When a group of fields should be editable and (some of them) required only while a
checkbox is ticked — and must **not** fail validation when the checkbox is off and the
group is hidden — use a [conditional field-group](reference/conditional.md). The rule is
enforced server-side, so an off group never fails validation even if its fields are
declared required; JavaScript only hides the group.

```python
from crispy_forms.layout import Row
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)
from crud_views.lib.crispy import Column6

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),  # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],                 # only this is required when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [Row(Column6("name"), Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")))]
```

When the checkbox is off the group fields are cleared on save (they must be
`null=True, blank=True`). To toggle an **entire first-level formset** instead of a
field-group, use `ConditionalFormSet` — see the
[reference page](reference/conditional.md).
````

- [ ] **Step 5c: Add CHANGELOG entry**

In `CHANGELOG.md`, add an `Added` bullet under the next unreleased version:

```markdown
### Added
- Conditional field-groups and conditional formsets: a checkbox toggle can hide a group of fields (or an entire first-level formset). When off, validation is skipped and values are cleared (formsets: `skip` keeps rows, `purge` deletes them). Enforced server-side; bundled `toggle.js` handles show/hide only. See `docs/reference/conditional.md`.
```

- [ ] **Step 6: Run the full suite**

Run: `cd tests && pytest -q`
Expected: all pass (existing + new).

- [ ] **Step 7: Lint**

Run: `task check && task format`
Expected: clean.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/conditional/__init__.py src/crud_views/lib/conditional/group.py docs/reference/conditional.md mkdocs.yml docs/faq.md skills/django-crud-views/SKILL.md skills/django-crud-views/references/api-reference.md CHANGELOG.md tests/test1/test_conditional_exports.py
git commit -m "feat(conditional): public exports, ConditionalGroupModelForm, docs, skill & changelog"
```

---

## Task 8: Worked examples in the bootstrap5 example app (Kind 1 + Kind 2)

**Files:**
- Create: `examples/bootstrap5/app/models/conditional.py`
- Modify: `examples/bootstrap5/app/models/__init__.py` (re-export new models)
- Create: `examples/bootstrap5/app/views/conditional.py`
- Modify: `examples/bootstrap5/app/urls.py` (register viewsets)
- Create: `examples/bootstrap5/app/migrations/0011_conditional_examples.py` (via makemigrations)

**Interfaces:**
- Consumes: `ConditionalGroupModelForm`, `ConditionalGroup`, `ToggleGroup`, `ModelFieldToggle`, `ConditionalFormSet` (Tasks 1–7); `ViewSet`, `FormSetMixin`, `FormSet`/`FormSets`/`InlineFormSet`, crispy columns (existing).
- Produces: `cv_registration` (Kind 1) and `cv_event` (Kind 2) ViewSets, added to `urlpatterns`.

This is a demo/wiring task — no new TDD test file; verification is `makemigrations --check`, a Django system check pass, and the dev server rendering both forms.

- [ ] **Step 1: Create the example models**

```python
# examples/bootstrap5/app/models/conditional.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class Registration(models.Model):
    """Kind 1: a conditional field-group governed by `with_company`."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    with_company = models.BooleanField(default=False, verbose_name=_("I represent a company"))
    company_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Company name"))
    vat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("VAT ID"))

    class Meta:
        verbose_name = _("Registration")
        verbose_name_plural = _("Registrations")

    def __str__(self):
        return self.name


class Event(models.Model):
    """Kind 2: a parent whose entire `sessions` formset is governed by `with_sessions`."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    with_sessions = models.BooleanField(default=False, verbose_name=_("This event has sessions"))

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.name


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200, verbose_name=_("Title"))

    class Meta:
        ordering = ["title"]
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

    def __str__(self):
        return self.title
```

- [ ] **Step 2: Re-export the models**

In `examples/bootstrap5/app/models/__init__.py`, add near the other imports:

```python
from .conditional import Registration as Registration, Event as Event, Session as Session
```

- [ ] **Step 3: Create the example views (both kinds)**

```python
# examples/bootstrap5/app/views/conditional.py
from collections import OrderedDict
from typing import List

import django_tables2 as tables
from crispy_forms.layout import Row, LayoutObject
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from app.models.conditional import Registration, Event, Session
from crud_views.lib.conditional import (
    ConditionalGroup,
    ConditionalGroupModelForm,
    ConditionalFormSet,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.crispy import Column4, Column6, Column8, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.formsets import FormSets, FormSet, FormSetMixin, InlineFormSet
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

# ---------------- Kind 1: conditional field-group ----------------

cv_registration = ViewSet(model=Registration, name="registration", icon_header="fa-solid fa-user-plus")


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),
            fields=["company_name", "vat_id"],
            required=["company_name"],  # vat_id stays optional even when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("with_company")),
            ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id"))),
        ]


class RegistrationTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_company = tables.Column()


class RegistrationListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Registration
    table_class = RegistrationTable
    cv_viewset = cv_registration


class RegistrationDetailView(DetailViewPermissionRequired):
    model = Registration
    cv_viewset = cv_registration
    cv_property_display = [
        {
            "title": _("Registration"),
            "icon": "user-plus",
            "description": _("Registration details"),
            "properties": ["id", "name", "with_company", "company_name", "vat_id"],
        },
    ]


class RegistrationCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Registration
    form_class = RegistrationForm
    cv_viewset = cv_registration


class RegistrationUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Registration
    form_class = RegistrationForm
    cv_viewset = cv_registration


class RegistrationDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Registration
    form_class = CrispyDeleteForm
    cv_viewset = cv_registration


# ---------------- Kind 2: conditional first-level formset ----------------

cv_event = ViewSet(model=Event, name="event", icon_header="fa-solid fa-calendar")


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["name", "with_sessions"]

    def get_layout_fields(self):
        from crud_views.lib.formsets import Formsets

        return [Row(Column6("name"), Column6("with_sessions")), Formsets()]


class SessionForm(CrispyModelForm):
    class Meta:
        model = Session
        fields = ["title"]


class SessionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [Row(Column8("title"), self.form_control_col4)]


SessionFormSet = inlineformset_factory(
    Event,
    Session,
    formset=SessionInlineFormSet,
    form=SessionForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

cv_event_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        sessions=FormSet(
            title=_("Sessions"),
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Off => formset hidden & never validated. "skip" keeps existing rows;
            # switch to on_off="purge" to delete them on save when toggled off.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="skip"),
        ),
    )
)


class EventTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_sessions = tables.Column()


class EventListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Event
    table_class = EventTable
    cv_viewset = cv_event


class EventDetailView(DetailViewPermissionRequired):
    model = Event
    cv_viewset = cv_event
    cv_property_display = [
        {
            "title": _("Event"),
            "icon": "calendar",
            "description": _("Event details"),
            "properties": ["id", "name", "with_sessions"],
        },
    ]


class EventCreateView(CrispyModelViewMixin, FormSetMixin, CreateViewPermissionRequired):
    model = Event
    form_class = EventForm
    cv_viewset = cv_event
    cv_formsets: FormSets = cv_event_formsets


class EventUpdateView(CrispyModelViewMixin, FormSetMixin, UpdateViewPermissionRequired):
    model = Event
    form_class = EventForm
    cv_viewset = cv_event
    cv_formsets: FormSets = cv_event_formsets


class EventDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Event
    form_class = CrispyDeleteForm
    cv_viewset = cv_event
```

Note: the example app's detail views use `cv_property_display` (a list of section dicts with `title`/`icon`/`description`/`properties`), as shown above — confirmed against `app/views/foo.py`.

- [ ] **Step 4: Register the viewsets in urls**

In `examples/bootstrap5/app/urls.py`, add imports and extend `urlpatterns`:

```python
from app.views.conditional import cv_registration, cv_event
```
```python
    + cv_registration.urlpatterns
    + cv_event.urlpatterns
```

- [ ] **Step 5: Make the migration**

Run (from `examples/bootstrap5`, using its manage.py / settings):

```bash
cd examples/bootstrap5 && python manage.py makemigrations app
```
Expected: creates `app/migrations/0011_*.py` with `Registration`, `Event`, `Session`.

- [ ] **Step 6: Verify migrations are complete and checks pass**

Run:
```bash
cd examples/bootstrap5 && python manage.py makemigrations --check --dry-run && python manage.py check
```
Expected: "No changes detected" and system check reports no errors (E310/E311/W320 not triggered — `with_company`/`with_sessions` are real model fields on their forms, and the cleared fields are `null=True, blank=True`).

- [ ] **Step 7: Smoke-test rendering (manual)**

Run `cd examples/bootstrap5 && python manage.py runserver`, then load the Registration create form and the Event create form. Confirm: toggling `with_company` shows/hides the company group; toggling `with_sessions` shows/hides the Sessions formset; submitting each with the toggle off succeeds even with empty group/rows. (Cosmetic JS is a bonus; the server accepts the off-state regardless.)

- [ ] **Step 8: Commit**

```bash
git add examples/bootstrap5/app/models/conditional.py examples/bootstrap5/app/models/__init__.py examples/bootstrap5/app/views/conditional.py examples/bootstrap5/app/urls.py examples/bootstrap5/app/migrations/0011_*.py
git commit -m "docs(examples): conditional field-group and conditional formset demos (bootstrap5)"
```

---

## Self-Review (completed during plan authoring)

**Spec coverage:**
- Toggle pluggable (model/UI) → Task 1. ✓
- Off ⇒ skip validation + clear (field-group) → Task 2. ✓
- Kind 1 in main form & first-level formset rows (per-form `clean()`) → Task 2 (mixin works on any form). ✓
- Kind 2 whole first-level formset, gate authority → Task 4. ✓
- skip vs purge configurable per formset, default non-destructive → Task 4. ✓
- Batteries-included JS, cosmetic only → Tasks 3 & 5. ✓
- Server-side enforcement independent of JS (tampering tests) → Task 2 (`test_clears_smuggled_values_when_toggle_off`), Task 4 (`test_all_valid_true_when_off...`). ✓
- ToggleSource shared abstraction → Task 1, reused by Tasks 2 & 4. ✓
- System checks (non-null clear warn, unknown toggle error, nested-formset note) → Task 6 (E310/E311/W320). ✓
- Nested formsets out of scope / unaffected → Task 4 (apply_conditional top-level only) + Task 6 E310 guard. ✓
- Public API names match spec (`ConditionalGroup`, `ConditionalFormSet`, `ToggleGroup`, `ModelFieldToggle`, `UIFieldToggle`) → Task 7. ✓
- Worked bootstrap5 examples, one Kind 1 (`cv_registration`) and one Kind 2 (`cv_event`/`with_sessions`) → Task 8. ✓
- Documentation everywhere: mkdocs reference page (`docs/reference/conditional.md` + nav), FAQ entry (`docs/faq.md`), bundled skill (`SKILL.md` section + `api-reference.md` + import cheatsheet), CHANGELOG → Task 7 (steps 5a, 5b, 5b-ii, 5b-iii, 5b-iv, 5c). ✓

**Type consistency:** `is_on(form)`, `field_name()`, `inject`, `cv_active`, `apply_conditional(main_form)`, `on_off ∈ {"skip","purge"}`, `required_fields`, `empty_value_for` are used identically across tasks.

**Placeholder scan:** no TBD/TODO; every code step contains full code.

**Verified structural facts:** `XFormSet` and `XForm` are Pydantic `BaseModel`s (`render_tree.py`), so `cv_active`/`cv_toggle_field` are added as a typed field / property. `CHANGELOG.md` and `mkdocs.yml` exist. The bundled static dir is `src/crud_views/static/crud_views/js/` (formset.js, list.filter.js, viewset.js) — toggle.js joins it.
