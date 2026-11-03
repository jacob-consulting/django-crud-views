# Phase 04: Alert dismiss adapter - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 13 planned new/modified files
**Analogs found:** 13 / 13 (existing-file extensions or explicit golden precedent)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/crud_views/static/crud_views/js/adapters.js` | service | request-response | same file, modal/collapse methods | exact |
| `src/crud_views/static/crud_views/js/viewset.js` | controller | event-driven | same file, delegated cancel handler | exact |
| `src/crud_views/templates/crud_views/tags/alert.html` | component | transform | same file | exact |
| `tests/js/adapters.test.js` | test | request-response | same file, fakeNamespace and lazy-resolution tests | exact |
| `tests/js/viewset.test.js` | test | event-driven | same file, delegated click tests | exact |
| `tests/test1/test_alerts.py` | test | transform | same file, _render and frame assertions | exact |
| `tests/test1/test_messages.py` | test | request-response | same file, render and real create response | exact |
| `tests/test1/golden/alerts/dismissible.html` (proposed destination) | test | file-I/O | `tests/test1/test_form_frame.py`, _check_golden | role-match |
| `docs/reference/javascript.md` | config (documentation) | transform | same file, adapter table and namespace recipe | exact |
| `docs/reference/messages.md` | config (documentation) | transform | same file, dismissible output example | exact |
| `docs/reference/theme.md` | config (documentation) | transform | existing frame plus adapter override recipe below | role-match |
| `docs/migrating-1.0.md` | config (documentation) | transform | existing migration guide | exact |
| `CHANGELOG.md` | config (documentation) | transform | existing Breaking entries | exact |

Golden destination is an implementation choice; no example application product edit is implied by the required browser smoke.
All existing paths above were verified through `git ls-files -- <path>`; no runtime mirrors are analogs.
Documentation uses the closest allowed role label, not an assertion that these Markdown files are runtime configuration.

## Pattern Assignments

### Adapter factory and its tests

**Files:** adapters.js and tests/js/adapters.test.js from the table.

**Analog:** `src/crud_views/static/crud_views/js/adapters.js:4-8,12-16,30-43`.
Classic script: no imports, global namespace initialized once, component resolved at method invocation:

~~~javascript
globalThis.cv = globalThis.cv || {};
(function (cv) {
    const SIZE_CLASSES = Object.freeze({sm: "modal-sm", lg: "modal-lg", xl: "modal-xl"});
    function resolve(ns) { return (typeof ns === "function" ? ns() : ns) || null; }
    function component(ns, name) { const n = resolve(ns); return n && n[name] ? n[name] : null; }
~~~

Factory methods use `Component.getOrCreateInstance(el).method()` (modal.show line 15; collapse.toggle line 37).
Preserve the shallow per-adapter assignment at line 43 exactly:

~~~javascript
cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
~~~

Add alert to the factory return. Resolve Alert through component(ns, "Alert"); invoke its instance close when present;
otherwise remove inside this default adapter. Do not copy modal/collapse's missing-component error for alert.
Do not catch component or custom-adapter errors and do not remove after a present component's close.

**Test imports:** `tests/js/adapters.test.js:1-2`:

~~~javascript
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";
~~~

**Test core:** lines 4-18 fake component namespace and reset globals; lines 26-34 assert exact element and count;
115-130 cover function namespace and late global; 133-139 preserve preassigned adapter identity.
Extend that fixture with Alert and close spy. Assert a present no-op/throwing component does not trigger removal.
Include other-components-present-but-no-Alert, object/function namespaces, and preassigned custom alert identity.

### Delegated handler and its tests

**Files:** viewset.js and tests/js/viewset.test.js.

**Analog:** `src/crud_views/static/crud_views/js/viewset.js:37-44`:

~~~javascript
document.addEventListener("click", function (e) {
    if (!(e.target instanceof Element)) return;
    const el = e.target.closest("[data-cv-cancel-url]");
    if (!el) return;
    e.preventDefault();
    globalThis.location.href = el.getAttribute("data-cv-cancel-url");
});
~~~

Copy Element guard, document delegation, closest lookup and preventDefault. Adapt marker to data-cv-alert-dismiss,
find the nearest enclosing role="alert" and call the current `cv.adapters.alert.close(alertEl)`.
Missing marker/frame is a no-op. No per-alert initialization, logging, catch, or second removal path.
Call-time lookup is required; do not capture adapter at load.

**Test imports/setup:** `tests/js/viewset.test.js:1-3,26-33` loads once in beforeAll and resets body before each case.
**Concrete click pattern:** lines 59-64:

~~~javascript
const { form, button } = actionForm();
const event = new MouseEvent("click", { bubbles: true, cancelable: true });
button.dispatchEvent(event);
expect(form.requestSubmit).toHaveBeenCalledTimes(1);
expect(event.defaultPrevented).toBe(true);
~~~

Reuse event construction and mock observations for descendant clicks, dynamic/modal-contained markup,
nearest semantic frame, ignored targets, and adapter replacement. New cases must precede the final
no-jQuery reload test (lines 91-101), which installs duplicate listeners. Clean cv globals/spies between cases.
For throwing listeners observe the window error event and original error identity; dispatchEvent itself does not throw.
Assert no core log/removal and retained custom mutation; remove temporary error listener in finally.

### Shared alert frame and Python regressions

**Files:** alert.html, test_alerts.py, test_messages.py, proposed golden.

**Analog:** `src/crud_views/templates/crud_views/tags/alert.html:1-6`:

~~~django
{% load crud_views i18n %}
<div class="{% cv_button_class "alert" alert.level %}{% if alert.dismissible %} alert-dismissible fade show{% endif %}{% if alert.extra_tags %} {{ alert.extra_tags }}{% endif %}"
     role="alert">
    {% cv_icon alert.icon_name "me-2" %}{% if alert.heading %}<strong>{{ alert.heading }}</strong>{% if alert.text %} {% endif %}{% endif %}{% include alert.body_template %}
    {% if alert.dismissible %}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>{% endif %}
</div>
~~~

Change only dismiss attribute; retain conditional control, literal classes, role, escaping, included body and translated label.

**Render/import precedent:** `tests/test1/test_alerts.py:3-11,70-79`:

~~~python
def _render(source, context=None):
    return Template("{% load crud_views %}" + source).render(Context(context or {}))
~~~

Use same renderer for deterministic dismissible golden; preserve nondismissible assertions at 104-107.
Override seam tests at 110-127 demonstrate isolated frame/body overrides and existing color class table.
Keep escaping regressions at 41-54,93-101.

**Golden file-I/O precedent:** `tests/test1/test_form_frame.py:7-17,50-55`:

~~~python
def _check_golden(name: str, markup: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_norm(markup) + "\n")
    assert _norm(markup) == path.read_text().strip()
~~~

Adapt to an alert-specific directory; raw deterministic render with fixed locale is preferable for detecting whitespace drift.
Existing _norm strips whitespace (lines 44-47), so do not claim it verifies byte-identical output.
Capture and commit the legacy golden/test BEFORE editing template; later golden diff should show only the attribute change.
Never regenerate unrelated fixtures.

**Flash-message regression:** `tests/test1/test_messages.py:130-141,164-170`:
renderer uses `Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))`.
Update legacy attribute assertions at 139 and 169; preserve role/classes/body checks.
Real create response uses:

~~~python
response = client_publisher_add_view.post("/publisher/create/", {"name": "Penguin"}, follow=True)
html = response.content.decode()
~~~

No new auth behavior: existing logged-in publisher fixture (13-20) grants add and view permissions.

### Public documentation and migration

**Files:** all five Markdown files in the classification.

**Adapter reference analog:** `docs/reference/javascript.md:25-58,120-139` documents method table,
call-time replacement, shallow merge, namespace factories and a short shell+adapter override.
Concrete existing namespace example at 63-65:

~~~javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
~~~

Add alert.close row, describe absent-Alert removal and surfaced exceptions, change factory count to four, and
update viewset.js use-time requirement. Do not change “All three” at line 179: that counts lifecycle events.

**Message output analog:** `docs/reference/messages.md:27-33` is the rendered alert frame example using
the same stock classes and legacy dismiss attribute; replace hook and explain core-script requirements.

**Theme recipe:** copy the frame excerpt above as the structural analog, use custom frame/control classes,
retain role="alert", data-cv-alert-dismiss, conditional control and accessible label. Keep class-table scope unchanged.
Follow existing short HTML + adapter customization recipe in javascript.md:120-139.
Clarify remaining Bootstrap data-API use is limited to the dropdown templates already listed in theme.md.

**Migration/changelog:** preserve existing documents' organization; paired updates are mandatory per CLAUDE.md.
Add compact before/after attribute example, required core scripts and relative links to JavaScript/message references.
Recommend migration even with Bootstrap; legacy copied templates continue through Bootstrap's own data API
and gain no absent-Alert fallback until converted. Record DOM change under Breaking in CHANGELOG.md.

## Shared Patterns

- **Lazy public seams:** component(ns, name) and per-adapter Object.assign preserve alternate namespaces,
  late loading and theme ownership. Apply to adapter factory and click integration.
- **Semantic delegated targets:** Element guard + closest + document listener supports dynamic markup.
  role="alert" identifies frame independent of CSS.
- **Error handling:** alert phase deliberately has no recovery wrapper. Missing Alert removal belongs only
  to the default adapter; all present-component/custom errors surface.
- **Validation/security:** fixed selectors, existing conditional template output and escaping tests; no new
  server endpoint, authorization logic, inline handler or lifecycle event.
- **Verification:** reuse existing JS/Python suites. Browser smoke of the example's real flash message remains
  execution acceptance; server-render tests alone cannot establish actual dismissal.

## No Analog Found

None for structural organization. The absent-Alert removal policy and custom-adapter failure contract are
new alert-specific behavior defined by CONTEXT decisions D-03/D-04; do not copy other adapters' recovery policy.

## Metadata

**Analog search scope:** tracked core JS/template files, existing JS/Python suites, golden helper and public docs.
**Strong implementation analogs:** adapter factory, delegated cancel handler, shared alert frame,
JS test harnesses and Python golden helper; stopped without broadening to unrelated components.
**Pattern extraction date:** 2026-10-26.
**Repository edits:** only this pattern map; no tests or product edits performed.
