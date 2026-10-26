# Phase 03: Filter toggle label mode - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 16 intended or conditional new/modified files
**Analogs found:** 16 / 16
**Source policy:** Current git-tracked repository files; no runtime mirrors or stale codebase maps.

## File Classification

Documentation and catalogs use the nearest permitted role (config); their data flow is file-I/O.

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/crud_views/lib/view/buttons.py` | service | request-response | Same file, FilterContextButton and ContextButton helpers | exact |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | component | transform | Same file plus `src/crud_views/templates/crud_views/tags/button/action.html` | exact |
| `tests/test1/test_filter_toggle_label_mode.py` (new, proposed) | test | request-response | `tests/test1/test_context_button_label_mode.py` | exact |
| `tests/test1/test_context_button_template.py` | test | request-response | Same file | exact |
| `tests/js/list.filter.test.js` | test | event-driven | Same file | exact |
| `tests/test1/test_i18n.py` | test | file-I/O | Same file | exact |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | config | file-I/O | Same catalog | exact |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` (generated) | config | file-I/O | Same compiled catalog | exact |
| `docs/reference/context_buttons.md` | config | file-I/O | Same document | exact |
| `docs/reference/action_menus.md` | config | file-I/O | Same document | exact |
| `docs/reference/buttons.md` | config | file-I/O | Same document | exact |
| `docs/reference/javascript.md` | config | file-I/O | Same document | exact |
| `CHANGELOG.md` | config | file-I/O | Same document | exact |
| `docs/migrating-1.0.md` (conditional on Breaking entry) | config | file-I/O | Same document | exact |
| `src/crud_views/static/crud_views/js/list.filter.js` (only if tests expose a gap) | component | event-driven | Same file | exact |
| `tests/test1/test_filter_pinned.py` (optional regression extension) | test | request-response | Same file | exact |

Existing golden `tests/test1/golden/action_menus/toolbar_publisher_list.html` and harness
`tests/test1/test_action_menus_golden.py` are verification dependencies, not intended changes.
Existing resolver `src/crud_views/lib/view/base.py` is a reuse dependency, not an implementation target.

## Pattern Assignments

### `src/crud_views/lib/view/buttons.py` (service, request-response)

**Analogs:** Same file, lines 55–85 and 298–334; resolver in
`src/crud_views/lib/view/base.py`, lines 299–328.
Both paths were verified with `git ls-files -- <path>`.

**Imports:** Existing sibling-relative imports in buttons.py lines 7–13. For translation,
base.py line 26 already establishes `from django.utils.translation import gettext_lazy as _`.
Reuse that import convention for the seeded default.

**Visibility and access pattern** (buttons.py lines 311–319):

```python
dict_kwargs = {"cv_access": False}

# if view has no filter, no button is shown
if not isinstance(context.view, ListViewTableFilterMixin):
    return dict_kwargs

# pinned filter is always visible -> no toggle button
if getattr(context.view, "cv_filter_pinned", False):
    return dict_kwargs
```

Preserve these returns. There is no target permission check to add: this button toggles
the already accessible list page.

**Core assembly pattern** (buttons.py lines 323–332):

```python
data = {"cv_access": True}  # it toggles the filter of the list page the user is already on
# no target view, so cv_key is the button's own key, not a view key like every other button (#208)
data["cv_key"] = self.key
data["cv_action_label"] = "Filter"
data["cv_icon_action"] = "filter"
data["cv_filter_expanded"] = context.view.cv_filter_expanded
data["cv_url"] = list_url
self._apply_label(data, context)
self._apply_variant(data)
self._inject_template(data)
```

Translate only the seeded default, retain the helper order, and stamp the resolved mode
before returning direct button context. Use
`context.view.cv_get_action_label_mode("context", self.key, self)`.
Do not supply a target default or hard-code the key.

**Resolver pattern** (base.py lines 312–322):

```python
if location == "context":
    if cls.cv_context_actions_label_mode is not None and key in cls.cv_context_actions_label_mode:
        return cls.cv_context_actions_label_mode[key]
    if button is None:
        button = cls._cv_find_context_button(cls.cv_context_buttons, cls.cv_viewset, key)
    if button is not None and button.label_mode is not None:
        return button.label_mode
    mapping = cls.cv_get_context_actions_label_mode()
    if key in mapping:
        return mapping[key]
    return target_default or default_label_mode("context")
```

This is an existing public resolver to call, not duplicate. A missing key reaches the live
floor lazily, and a selected empty or unrelated view map must retain replacement semantics.

**Customization pattern** (buttons.py lines 69–72):

```python
cv_action_label = self.render_label(data, context)
if cv_action_label:
    data["cv_action_label"] = cv_action_label
    data["cv_action_short_label"] = cv_action_label
```

Custom labels remain authoritative. Existing validation is shared by context buttons:
buttons.py lines 357–361 validate `variant` and `label_mode`. Add no parallel validator.

### `src/crud_views/templates/crud_views/tags/context_action_filter.html` (component, transform)

**Analogs:** Existing filter leaf and `src/crud_views/templates/crud_views/tags/button/action.html`.
Both are tracked. Use the action leaf for the three label bodies and title/tooltip convention;
retain the filter leaf for IDs, collapse hooks, state, whitespace, and two-icon placement.

The filter leaf currently requests literal icon-mode classes and obtains open/close host
classes. Pass the resolved mode to the class lookup. For icon-bearing modes, retain the
rule requiring usable host classes for both icons; mixed or unusable host placements
continue through the existing standalone children. Label mode must skip icon classes,
spans, and icon data hooks entirely.

The icon-only default must retain its exact rendered bytes. Keep a raw pre-change render:
the existing normalized golden is useful but does not prove whitespace equality. Both
mode retains a constant visible label without title or tooltip marker. Label mode retains
the same disclosure attributes and constant visible label.

### Python rendering tests (test, request-response)

**Primary analog:** `tests/test1/test_context_button_label_mode.py`.
**Related existing targets:** `tests/test1/test_context_button_template.py`,
`tests/test1/test_i18n.py`, and optionally `tests/test1/test_filter_pinned.py`.
All were confirmed tracked.

**Precedence pattern** (test_context_button_label_mode.py lines 50–53):

```python
def test_view_map_naming_key_beats_button(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    _with_viewset_buttons(monkeypatch, _update_button("label"))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "both"
```

Adapt this to the filter-bearing publisher list, including renamed `search`, a direct
FilterContextButton instance, no target singular default, whole-map replacement and
live floor behavior. Use monkeypatch and override_settings to avoid cross-test leakage.
Existing template tests lines 46–64 build the publisher list view from the logged-in
client response and call `get_context(view.cv_get_view_context())`; reuse that route
instead of making a new fixture framework.

The dedicated module should cover modes × initial expansion × element/host/mixed
placements, class-table variants, custom label and whole-template hooks, plus raw default
compatibility. Existing pinned/no-filter tests remain regression gates.

**Localization import pattern** (test_i18n.py lines 1–6):

```python
import gettext as gettext_mod
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import translation
```

**Compiled catalog pattern** (test_i18n.py lines 76–81):

```python
def test_mo_files_load():
    for _pkg, _loc, d in _iter_po():
        mo = d / "django.mo"
        assert mo.exists(), f"missing {mo}"
        with mo.open("rb") as fh:
            gettext_mod.GNUTranslations(fh)  # raises if corrupt
```

Extend with extraction and actual compiled-entry assertions, active-language rendering,
and a distinct translation sentinel: German "Filter" alone cannot prove gettext ran.
Existing custom labels must still win.

### `tests/js/list.filter.test.js` (test, event-driven)

**Analog:** Same tracked file; reuse its jsdom fixtures, `loadScript`, mocked fetch,
and collapse adapter rather than introduce a browser harness.

**Setup pattern** (lines 38–43):

```javascript
beforeEach(() => {
    fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    toggle = vi.fn();
    window.cv = { ...window.cv, adapters: { collapse: { toggle } } };
    nav.href = "";
});
```

**Disclosure/persistence assertions** (lines 69–81):

```javascript
const f = fixture();
await loadScript("list.filter");
f.toggle.click();
expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
expect(toggle).toHaveBeenCalledWith(document.getElementById("filter-collapse"));
expect(fetchMock).toHaveBeenCalledWith("/books/", {
    method: "POST",
    headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
    body: JSON.stringify({ filter_expanded: true }),
});
f.toggle.click();
expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ filter_expanded: false }));
```

Extend fixtures with no icon hooks and with constant visible labels. Exercise two clicks
from both starting states. Preserve existing throw/false adapter coverage (lines 98–123),
failed-POST coverage (125–133), host class swaps (46–54), and reset cases (135–145).

### `src/crud_views/static/crud_views/js/list.filter.js` (component, event-driven; conditional)

**Analog:** Same tracked file. Prefer tests only unless a demonstrated gap needs a change.

**Error/state ordering** (lines 15–18):

```javascript
if (globalThis.cv.adapters.collapse.toggle(panel) === false) {
    return;
}
button.setAttribute("aria-expanded", String(next));
```

**Optional icon pattern** (line 29):

```javascript
button.querySelectorAll("[data-cv-filter-icon]").forEach((icon) => (icon.hidden = !icon.hidden));
```

An empty NodeList already supports label-only markup. No label mutation is needed.
A thrown adapter aborts the handler; a false return aborts before state changes.
The existing fetch rejection handler at line 38 intentionally preserves a successful toggle.

### Catalogs and documentation (config, file-I/O)

**Analogs:** Each existing tracked destination; these are narrow extensions to current
contracts, not new document structures.

Core German PO lines 19–25 establish source-reference/msgid/msgstr entries:

```po
#: lib/crispy/form.py:35
msgid "Save"
msgstr "Speichern"
```

Add the extracted default Filter entry and regenerate the tracked MO using the existing
compilemessages workflow. Do not hand-edit binary output or unrelated package catalogs.

In `docs/reference/context_buttons.md`, lines 77–82 already discuss resolved
`cv_label_mode` and class lookup; replace the claim that the bundled filter is necessarily
icon-only. Add compact examples for settings-map and button-level configuration, all
three modes, declared key, and absence of a target default. Link canonical resolution
in `docs/reference/action_menus.md` rather than repeat precedence.

Correct the filter exception in `docs/reference/buttons.md`. Update
`docs/reference/javascript.md` under "The filter toggle contract" (lines 187–199)
to describe optional icon hooks, unchanged disclosure/persistence, and constant labels.
Keep the existing host-versus-child documentation.

`CHANGELOG.md` uses `## Unreleased` (line 3) and categorized bullets.
Lines 32–34 show an existing filter change explaining the affected template and practical
upgrade consequence. Record the configured-mode behavior change similarly. If classified
under `### Breaking`, also update `docs/migrating-1.0.md` per project instructions.

## Shared Patterns

### Resolved context and declared keys

**Source:** `src/crud_views/lib/view/base.py`, lines 640–645.
**Apply to:** Filter builder and custom-template tests.

```python
data = self._cv_get_action_context(key, obj, user)
if location is not None and data:
    button = self.cv_get_context_button(key) if location == "context" else None
    mode = self.cv_get_action_label_mode(location, key, button, data.get("cv_context_label_mode"))
    # cv_action_key: the configured key, which a button's cv_key (its target) may differ from (#264)
    data = {**data, "cv_label_mode": mode, "cv_action_key": key}
```

The outer view stamps context for normal rendering, but direct FilterContextButton context
must also receive the mode. Its resolver call intentionally omits the target default.

### Access, validation and escaping

Reuse the early filter/pinned returns and existing context-button validation above.
Keep normal Django interpolation and trusted template hooks; do not add safe-marked labels.
There is no new authentication, database transaction, or logging pattern in this phase.

### Failure semantics and request formatting

**Source:** `src/crud_views/static/crud_views/js/list.filter.js`, lines 15–38.
**Apply to:** Label-only and both-mode interaction tests.

Collapse succeeds before ARIA/icon mutation. POST retains the CSRF header and
`{"filter_expanded": next}` payload; rejection does not roll back successful UI state.
Preserve reset handling and all DOM IDs.

## No Analog Found

None. The combined mode × placement matrix is new coverage, but existing rendering,
resolution, translation, and interaction tests provide matching scaffolding.

## Metadata

**Analog search scope:** `src/crud_views/lib/view/`, core button templates and JavaScript,
`tests/test1/`, `tests/js/`, core German catalogs, reference docs and release notes.
**Primary pattern families:** 5 (context builder/resolver, template leaf, Python tests,
JavaScript interaction/tests, catalogs/docs).
**Tracked-source verification:** All named analogs verified through git ls-files; actual
toolbar golden is in `tests/test1/golden/action_menus/`.
**Pattern extraction date:** 2026-10-26.
**Verification status:** Mapping only; no source changes or test runs performed.
