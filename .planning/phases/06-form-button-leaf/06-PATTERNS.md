# Phase 06: Form-button leaf - Pattern Map

**Mapped:** 2026-10-27
**Scope:** Current tracked source, read after phases 1–5. Paths below include `src/`; import package names do not.
**Coverage:** All explicitly named implementation, validation and documentation surfaces from CONTEXT/RESEARCH are classified below. Proposed filenames/directories are marked new; JS source and dependency files are conditional edits, not mandatory churn.

## File Classification

| New/Modified File | Role | Data Flow | Closest Pattern | Match Quality |
|---|---|---|---|---|
| `src/crud_views/lib/crispy/buttons.py` | component | transform | Existing constructor; form hook and button-data patterns below | role-match |
| `src/crud_views/lib/crispy/form.py` | component | request-response | Existing `CrispyFormMixin` | exact |
| `src/crud_views/lib/views/list.py` | component | request-response | `CrispyFormMixin.helper/get_form_actions` | exact |
| `src/crud_views/lib/views/mixins.py` | controller | request-response | Existing filter-helper construction; preserve wiring | exact |
| `src/crud_views/lib/view/button_data.py` | utility | transform | Existing `cv_button_data` and `icon_host_keys` | exact |
| `src/crud_views/lib/view/label_mode.py` | utility | transform | Existing lazy floor resolver | exact |
| `src/crud_views/lib/button_classes.py` | config | transform | Existing finite `FORM_KINDS` and form slots | exact |
| `src/crud_views/lib/icons.py` | config | transform | Existing `DEFAULT_ICONS` / `BOOTSTRAP_ICONS` | exact |
| `src/crud_views/lib/settings.py` | config | transform | Existing context/list map fields and diagnostics | exact |
| `src/crud_views/lib/viewset/__init__.py` | config | transform | Existing context/list map fields and validators | exact |
| `src/crud_views/lib/view/base.py` | controller | transform | Existing first-map resolver | exact |
| `src/crud_views/lib/view/action_menu.py` | utility | batch | Existing E211/W291 map checks | exact |
| `src/crud_views/lib/view/buttons.py` | utility | batch | Existing W292 icon diagnostic | role-match |
| `src/crud_views/checks.py` | utility | batch | Existing check registration, only if wiring changes | exact |
| `src/crud_views/templates/crud_views/tags/button/form.html` (new) | component | transform | Action leaf | exact |
| `src/crud_views_workflow/lib/forms.py` | component | request-response | `CrispyFormMixin` submit hook | exact |
| `src/crud_views/static/crud_views/js/viewset.js` (verify/conditional) | controller | event-driven | Existing delegated cancel handler | exact |
| `src/crud_views/static/crud_views/js/modal.js` (verify/conditional) | controller | event-driven | Existing submitter-aware FormData | exact |
| `src/crud_views/static/crud_views/js/list.filter.js` (verify/conditional) | controller | event-driven | Existing reset handler | exact |
| `tests/test1/test_crispy_buttons.py` | test | request-response | Existing endpoint/fixture tests; leaf DOM assertions | exact |
| `tests/test1/test_button_data.py` | test | transform | Existing normalizer tests | exact |
| `tests/test1/test_button_leaves.py` | test | transform | Existing isolated leaf DOM tests | exact |
| `tests/test1/test_button_classes.py` | test | transform | Existing finite grammar tests | exact |
| `tests/test1/test_filter.py` | test | request-response | Existing filter endpoint tests | exact |
| `tests/test1/test_action_label_mode_config.py` | test | transform | Existing map precedence tests | exact |
| `tests/test1/test_label_mode.py` | test | transform | Existing lazy floors and malformed settings tests | exact |
| `tests/test1/test_button_classes_checks.py` | test | batch | Existing class diagnostics tests | exact |
| `tests/test1/test_icons_registry.py`, `tests/test1/test_icons_checks.py` | test | transform/batch | Existing registry/check suites | exact |
| `tests/test1/test_icon_host_leaves.py` | test | transform | Existing host/inline leaf cases | exact |
| `tests/test1/test_label_mode_docs.py` | test | file-I/O | Existing documentation guard | exact |
| `tests/test1/golden/form_buttons/` (proposed new fixtures) | test | file-I/O | Existing tracked golden directories; baseline before implementation | role-match |
| `tests/test1/test_form_buttons_golden.py` (proposed new) | test | request-response/file-I/O | Existing endpoint fixtures plus leaf DOM assertions | role-match |
| `tests/js/modal.test.js`, `tests/js/viewset.test.js`, `tests/js/list.filter.test.js` | test | event-driven | Existing corresponding handler suites | exact |
| `noxfile.py` | config | batch | Existing isolated uv-backed Django sessions | role-match |
| `package.json`, `package-lock.json` (investigate/conditional) | config | batch | Existing declarations/lockfile; reconcile runtime first | exact |
| `examples/bootstrap5/project/settings.py` | config | transform | Existing example settings; add form floor/map | exact |
| `docs/reference/buttons.md` | config (documentation) | file-I/O | Existing leaf/class contract documentation | exact |
| `docs/reference/list_view.md` | config (documentation) | file-I/O | Existing field-only helper example | exact |
| `docs/getting_started/tutorial-5-filters-permissions.md` | config (documentation) | file-I/O | Existing helper tutorial | exact |
| `docs/reference/action_menus.md` | config (documentation) | file-I/O | Existing label-mode resolution table | exact |
| `docs/reference/icons.md` | config (documentation) | file-I/O | Existing icon registry documentation | exact |
| `docs/reference/settings.md` | config (documentation) | file-I/O | Existing lazy defaults and map documentation | exact |
| `docs/reference/theme.md` | config (documentation) | file-I/O | Existing template override guidance | exact |
| `docs/migrating-1.0.md`, `CHANGELOG.md` | config (documentation) | file-I/O | Existing paired breaking-change policy | exact |
| Phase 06 design/spec and acceptance note (planner selects names) | config (documentation) | file-I/O | No product-source analog | none |

Rows grouping files share the same assignment; they are separate files for plan ownership. Documentation is classified as config only because the mapper role taxonomy has no documentation role.

## Pattern Assignments

### Crispy adapter, form, workflow and filter helper

**Primary analog:** `src/crud_views/lib/crispy/form.py` (component, request-response).

Imports at lines 1–12 use crispy layout/helper classes and package-local button adapters; retain package adapters rather than importing crispy Submit for migrated controls.

**Owner capture** (lines 37–39):
```python
def __init__(self, cv_view, *args, **kwargs):
    self.cv_view = cv_view
    super().__init__(*args, **kwargs)
```

**Action extension hook** (lines 41–54):
```python
@property
def helper(self) -> FormHelper:
    helper = FormHelper()
    fields = self.get_layout_fields()
    if not isinstance(fields, (list, tuple)):
        fields = [fields]
    helper.layout = Layout(*fields, self.get_form_actions())
    return helper

def get_layout_fields(self) -> LayoutObject | BaseInput | list[LayoutObject | BaseInput]:
    raise NotImplementedError

def get_form_actions(self) -> FormActions:
    return FormActions(self.get_submit_button(), self.get_cancel_button())
```

Copy the hook shape for `ListViewFilterFormHelper`; do not copy this property lifecycle blindly into its initializer. Isolate subclass layouts, preserve declared fields with/without an explicit form, append one action group, and specify omission in the required design. Existing helper at `list.py:65–87` stores `view` and adds visible inputs plus hidden sort/order/dir controls. Only visible default controls migrate to layout actions.

**Payload and extension seam** (lines 56–63):
```python
def get_submit_button_kwargs(self) -> dict:
    return {"name": "submit", "value": self.submit_label}

def get_submit_button(self) -> Submit:
    """
    Submit button for FormActions
    """
    return Submit(**self.get_submit_button_kwargs())
```

Use a per-form `submit_icon` override through this seam; WorkflowForm's current `submit_label` is at `src/crud_views_workflow/lib/forms.py:20`, so workflow icon selection belongs with that form default. Delete's semantic slot is independent of submitted name (`form.py:123–130`); kwargs may override slot. Cancel kwargs retain `name="reset"` and `data_cv_cancel_url` (`form.py:75–79`).

Current adapter constructor at `src/crud_views/lib/crispy/buttons.py:16–18` is the compatibility boundary:
```python
def __init__(self, name, value, *, slot: str | None = None, **kwargs):
    self.field_classes = get_button_class(*(slot or self.slot).split(":", 1))
    super().__init__(name, value, **kwargs)
```
Preserve signature, generated IDs and appended CSS. The new renderer must bypass inherited value template evaluation while retaining explicit/subclass/default template selection and `%s` pack substitution. No existing package analog solves the full crispy owner-overlay lifecycle; use the design and real crispy integration tests.

### Form normalization, classes, icons and diagnostics

**Primary analog:** `src/crud_views/lib/view/button_data.py` (utility, transform).

**Imports and logger** (lines 3–10):
```python
import logging

from ..button_classes import get_icon_host_class
from ..exceptions import is_strict
from ..icons import resolve_icon_name_class
from .label_mode import LABEL_MODES, _invalid_label_mode, default_label_mode, is_label_mode

logger = logging.getLogger(__name__)
```

**Host icon resolution** (lines 47–49):
```python
if resolve_icon_name_class(icon) is None:
    return "", True
return get_icon_host_class(location, icon), False
```

Reuse `icon_host_keys(icon, "form")`; add the form class slots without widening variant locations. Keep finite kinds from `button_classes.py:209–225`. Existing slots at lines 56–60 preserve all five default class values.

**Mode validation** (lines 85–94):
```python
label_mode = ctx.get("cv_label_mode")
if not label_mode:
    label_mode = default_label_mode(location)
elif not is_label_mode(label_mode):
    label_mode = _invalid_label_mode(
        f"cv_label_mode must be one of {sorted(LABEL_MODES)}",
        location,
        label_mode,
        lambda: default_label_mode(location),
    )
```

Adapt strict/log-and-label missing-icon behavior from lines 97–110. Introduce the form branch before action URL/object logic at lines 116–144. Preserve action `LEAF_KEYS`; the design must settle separate form keys and cancel-only URL omission. No form result should inherit action modal/target/href fields.

### Lazy defaults and whole-map selection

**Primary analog:** `src/crud_views/lib/view/label_mode.py` (utility, transform).

**Lazy setting access** (lines 54–58):
```python
def _raw_label_mode_defaults() -> object:
    """The raw CRUD_VIEWS_LABEL_MODE_DEFAULTS, read at call time (override_settings applies); _UNSET if absent."""
    from django.conf import settings

    return getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)
```

Add `form: label` to the immutable defaults at line 23. Reuse runtime validation in `default_label_mode` (84–117) and existing E210 helper (44–51). Its strict branch raises before fallback (`71–73`); non-strict warnings are guarded once per location/value (`74–81`).

The distinct whole-map pattern is `src/crud_views/lib/view/base.py:263–272`:
```python
@classmethod
def cv_first_inline_keys(cls, view_value, viewset_field: str):
    """First inline-keys value that is not None: view, then ViewSet, then setting (#174).

    Also resolves the label-mode maps, which share the three layers and their names (#216).
    """
    if view_value is not None:
        return view_value
    if cls.cv_viewset is not None and getattr(cls.cv_viewset, viewset_field) is not None:
        return getattr(cls.cv_viewset, viewset_field)
    return getattr(crud_views_settings, viewset_field)
```

Extend settings fields (`settings.py:62–68`), ViewSet fields/validator (`viewset/__init__.py:84–110`) and CrudView map/resolver/check seams together. Empty maps select that layer; missing kinds use the form floor. Extend E211/W291 where they actually live, `view/action_menu.py:46–69`; W292 lives in `view/buttons.py:388–434`. `checks.py` is registration, not the owner of all these diagnostics.

### New form leaf

**Primary analog:** `src/crud_views/templates/crud_views/tags/button/action.html` (component, transform).

**Title/tooltip** (line 7):
```django
{% if cv_title %}title="{{ cv_title }}" data-cv-tooltip="{{ cv_location }}"{% endif %}
```

**Accessible body branches** (excerpt from line 8):
```django
{% if cv_label_mode == "icon" %}{% if cv_icon_inline is not False %}{% cv_icon cv_icon %}{% endif %}<span class="{% cv_button_class cv_location 'hidden-label' %}">{{ cv_label }}</span>{% elif cv_label_mode == "both" %}{% if cv_icon and cv_icon_inline is not False %}{% cv_icon cv_icon %} {% endif %}<span>{{ cv_label }}</span>{% else %}<span>{{ cv_label }}</span>{% endif %}
```

Copy presentation conventions only. Form is always a real button with normalized type/name/value/ID, kind-based class lookup and optional cancel attribute. Keep host classes on the button. Define one unconditional literal-escape boundary for SafeString, lazy strings and extra attrs; plain autoescape alone does not establish the required literal trust boundary. Custom templates consume normalized `cv_*` fields without an `input` alias.

### Render, security and payload tests

**Primary analog:** `tests/test1/test_button_leaves.py` (test, transform).

**Imports** (lines 6–10):
```python
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html
```

**One-element DOM assertion** (lines 56–60):
```python
def _one(markup: str, selector: str):
    doc = lxml_html.fromstring(f"<div>{markup}</div>")
    nodes = doc.cssselect(selector)
    assert len(nodes) == 1, markup
    return nodes[0]
```

Copy DOM assertions from lines 63–85 for icon/hidden text/title and both/label modes. Assert decoded literal text/value, no injected attributes/nodes, no Django-template expansion, and malicious SafeString handling. Add real `{% crispy %}` rendering for owner precedence, template overrides, legacy input placement, helper layout isolation and omission.

Existing `tests/test1/test_crispy_buttons.py:30–96` provides endpoint fixtures, override_settings and monkeypatch patterns. Its `tag()` helper deliberately matches only input tags (21–27): preserve before-change baselines, then update assertions for buttons. Baseline fixtures cover create/update/delete/workflow/filter before production edits; do not regenerate unrelated goldens.

JS tests extend existing handler suites with native button and nested icon/span clicks, real SubmitEvent submitter and FormData payload assertions. Existing production seams already use `closest("[data-cv-cancel-url]")` (`viewset.js:40`), `new FormData(form, submitter || undefined)` (`modal.js:82`), and the stable reset ID (`list.filter.js:57`); edit production JS only for demonstrated incompatibility.

## Shared Patterns

- **Authorization/CSRF:** Preserve current endpoint and permission fixtures; form presentation does not add a new auth mechanism or bypass endpoint checks.
- **Validation/errors:** Finite kinds/modes, existing CheckExpression IDs, strict exception policy and non-strict fallback remain shared. No warning for legacy helper placement or differing owners.
- **Ownership:** First non-None form, helper, page owner; select identity before inspecting configuration. An ordinary owner blocks fallback to another view. Crispy overlays can hide page ownership: design capture/recovery explicitly and test it through crispy.
- **Documentation:** Update the leaf contract/key-count guard and settings/resolution tables together. Pair Breaking changelog with migration guide. Show field-only helper compatibility, FormActions opt-in for legacy inputs, and custom template migration from `input.value` to `cv_value`.
- **Environment:** Extend uv-backed nox sessions following existing `noxfile.py:6–19`, preserving its matrix and Django/Python skips. Verify floor crispy dependencies and reconcile installed JS packages against the lockfile without silently raising dependency floors.

## No Analog Found

| Proposed responsibility | Role | Data Flow | Reason |
|---|---|---|---|
| Crispy owner capture/recovery and literal adapter render | component | transform | Existing wrappers only set CSS; no package renderer proves ownership under crispy context overlays. Follow required design and research, then integration tests. |
| Phase design/spec and acceptance note | config | file-I/O | Planning artifacts, not product-source patterns. Include generic downstream-theme follow-up without downstream project names. |

## Metadata

**Primary analogs extracted:** 5 (`form.py`, `button_data.py`, `label_mode.py`, action leaf, leaf tests).
**Search scope:** Current `src/crud_views`, workflow forms, Python and JS tests, examples, docs and nox/dependency configuration.
**Tracked-source gate:** Primary analogs and quoted secondary source paths verified with `git ls-files`; no install/runtime mirrors are assigned.
**Pattern extraction date:** 2026-10-27.
**Runtime verification:** No implementation or tests run; this is a read-only pattern map. Required design/spec remains a planning deliverable. Artifact created with apply_patch because this runtime exposes no dedicated Write tool.
