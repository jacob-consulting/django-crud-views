# Modal adapter: event names follow the data prefix

**Date:** 2026-11-22
**Status:** design approved by the maintainer on 2026-11-22; implementation authorized in the same session.
**Issue:** [#403](https://github.com/jacob-consulting/django-crud-views/issues/403).
**Scope:** a small follow-up to phase 06.45 / #398. The stock modal adapter's event names and the wording of its
missing-component error. Nothing else in `cv.adapters`.

## Intent

A theme on a Bootstrap fork should run on startup registrations alone, without an adapter script. #398 delivered
that for the namespace and tooltip placements. The stock modal adapter still listens to literal `hide.bs.modal` /
`hidden.bs.modal`, and CoreUI dispatches `hide.coreui.modal` / `hidden.coreui.modal`. On CoreUI the modal opens,
but its close is never observed: the session is not released, focus does not return to the opener, and the
replacement-open and prevented-hide paths are never reached.

The CoreUI theme (`django-crud-views-coreui` at `d67be0f`) has no modal override and seven modal views in its
example, so the gap is live there. Tabler keeps Bootstrap's event names and is unaffected.

| Library | Global | Data attributes | Modal events |
|---|---|---|---|
| Bootstrap 5.3.3 | `bootstrap` | `data-bs-*` | `hide.bs.modal` / `hidden.bs.modal` |
| Tabler 1.6.1 | `tabler` | `data-bs-*` | `hide.bs.modal` / `hidden.bs.modal` |
| CoreUI 5.9.1 | `coreui` | `data-coreui-*` | `hide.coreui.modal` / `hidden.coreui.modal` |

## Goals, non-goals, anti-goals

- **Goal:** the stock modal adapter observes a CoreUI modal's hide and hidden events when the theme has registered
  its data prefix. The CoreUI theme needs no change.
- **Goal:** the missing-component error no longer claims Bootstrap when another library is selected.
- **Non-goals:** a new registration function, a new `#cv-config` attribute, a new argument on
  `cv.bootstrapAdapters()`, any Python or template change, the other adapter entries, a dropdown adapter (U3),
  `register_theme()` (U8), a dev dependency on a real UI bundle.
- **Anti-goal:** any change to what stock Bootstrap or Tabler pages listen to.

## Constraints

- Developer maintainability (CLAUDE.md): the smallest bounded change, unsupported cases documented explicitly.
- Existing call-time guarantees stay: `#cv-config` may follow the script, and theme-assigned adapter entries keep
  ownership.

## Approaches

1. **Derive the event names from the data prefix — selected by the maintainer.** `#cv-config` already carries
   `data-data-prefix` (#391). In all three libraries the event key and the data prefix are the same token, while
   the global name differs; Tabler (`tabler` / `bs`) shows the namespace would be the wrong key. No new API.
2. **A separate `register_event_namespace()` — not selected.** Explicit, but a fourth registration call, config
   attribute and module global that would repeat the prefix for every known library.
3. **Listen to both `*.bs.modal` and `*.{prefix}.modal` — not selected.** Doubles the listeners and hides which
   contract is in force.
4. **Docs only — not selected.** The lifecycle logic is private to `adapters.js`; a theme would copy about 50
   lines and keep a script that #398 set out to remove.

## Decisions

### D-01 — Bounded scope

The event names of the stock modal adapter and the wording of the missing-component error. See non-goals.

### D-02 — Event names follow the data prefix (maintainer)

`modalLifecycle()` in `src/crud_views/static/crud_views/js/adapters.js` listens to `hide.{prefix}.modal` and
`hidden.{prefix}.modal`. The prefix comes from `data-data-prefix` on `#cv-config`; an absent element or attribute
means `bs`, the rule `tooltip.init` and object-detail `tabs.js` already use. Only the prefixed names are bound.

### D-03 — Read once per modal shell

The prefix is read when the adapter first attaches its listeners to a shell (first `onHidden` or `show`). Config
inserted after script load but before the first modal call is honoured. A prefix that changes afterwards is not
followed and nothing is re-bound. Documented as startup configuration.

### D-04 — Factory wiring, ownership, unsupported case

- Adapters built by `cv.bootstrapAdapters(ns)` use the D-02 rule whatever `ns` is. No new argument.
- A theme-assigned `cv.adapters.modal` keeps ownership.
- Unsupported and documented: a library whose event name differs from its data prefix assigns its own `modal`
  entry. A separate registration is revisited only when such a library exists.

### D-05 — Library-neutral error

`missing()` no longer claims "Bootstrap 5". It still names the missing component and the remedy (load the
library's bundle or assign `cv.adapters`). The "legacy Bootstrap wording" sentences in `theme.md` and
`javascript.md` are removed.

### D-06 — Acceptance and documentation (proof chosen by the maintainer)

- **Defaults:** without config, or with prefix `bs`, the adapter listens to exactly today's names. Existing Python,
  golden and JS tests pass.
- **vitest:** the modal lifecycle tests in `tests/js/adapters.test.js` run for `bs` and `coreui`. With `coreui`,
  `*.bs.modal` events trigger nothing. Late config and a preassigned modal adapter are covered. The error-text
  assertions are updated.
- **Browser check, once, real CoreUI 5.9.1:** run the CoreUI theme's example against this change, before and
  after. Closing a modal returns focus to its opener; a replacement opened during the fade-out is shown. Repeat
  both on the stock Bootstrap example to confirm no change. Record the result with the upstream commit and CoreUI
  version.
- **Docs:** replace "fixed modal events" and "does not certify" in `docs/reference/javascript.md`, `theme.md` and
  `modals.md` with the concrete rule from D-02 to D-04. CHANGELOG `### Fixed`. Not breaking, so
  `docs/migrating-1.0.md` is untouched.
- **Downstream note, not upstream work:** the CoreUI theme already registers `coreui` and needs no change; it gets
  a tracker entry pointing to #403. Tabler is unaffected.

## Left to the builder

The exact error text, test layout, doc wording, and how the CoreUI example is pointed at the working branch (the
theme installs this package editable from the sibling checkout, while this work lives in a separate worktree).
