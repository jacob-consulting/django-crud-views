# Phase 1: Label-mode defaults - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-25
**Phase:** 1-Label-mode defaults
**Areas discussed:** E108 severity & forward-compat, Bad-mode runtime fallback, Card attribute becomes None, Names
Phase 7 will freeze, Docs placement / example project

---

## E108 severity & forward-compat

| Option | Description | Selected |
|--------|-------------|----------|
| Error for both | Matches E105/E106/E210; typos fail loudly | ✓ |
| Error mode, Warning key | New W-ID for unknown keys; forward-compatible | |
| Warning for both | Most lenient | |

| Option | Description | Selected |
|--------|-------------|----------|
| Derive from LOCATIONS only | `"form"` accepted once Phase 6 adds it | ✓ |
| Pre-accept "form" now | Avoid two-step change | |

| Option | Description | Selected |
|--------|-------------|----------|
| Non-dict also E108 | Same ID for shape, like E106 | ✓ |
| Also allow None | None = package defaults | |

| Option | Description | Selected |
|--------|-------------|----------|
| One message per bad entry | Names key and value | ✓ |
| One message per setting | Lists all problems | |

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror E106 wording | No hint | ✓ |
| Add did-you-mean hint | difflib suggestion | |

Also confirmed: nested dicts are invalid modes. The accessor ignores bad setting entries at render, and only the
check reports them.

---

## Bad-mode runtime fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Package default for location | Never the (possibly broken) setting | ✓ |
| Always "label" | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Strict raises, else log | Same rule as #264 icon-less guard | ✓ |
| Always log, never raise | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Also fix cv_button_data crash | Same strict/log rule for bad stamped cv_label_mode | ✓ |
| Only the new setting | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Log once per bad value | Per process, per (location, value) | ✓ |
| Log every time | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Raise ValueError (unknown location arg) | Caller bug; matches cv_button_data :58 | ✓ |
| Return "icon" | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Configured floor (bad stamped mode fallback) | default_label_mode(location) | ✓ |
| Package default | | |

**Notes:** This clarified the earlier "checks only" answer. Bad setting *values* are handled leniently at render, but
a bad location *argument* from code always raises.

---

## Card attribute becomes None

| Option | Description | Selected |
|--------|-------------|----------|
| Add public resolver | `cv_get_card_actions_label_mode()` | ✓ |
| Inline, no new method | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Breaking entry + migration | Attribute readers now get None | ✓ |
| Changed only | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Setting first, attribute second | `{"card": "label"}` leads the recipe | ✓ |
| Attribute first | | |

| Option | Description | Selected |
|--------|-------------|----------|
| no_label untouched | LATER-01 removes it | ✓ |
| Start deprecating now | | |

---

## Names Phase 7 will freeze

| Option | Description | Selected |
|--------|-------------|----------|
| Keep pair, freeze as stable | LATER-02 → won't rename | ✓ |
| Rename before 1.0 | | |
| Freeze as provisional | | |

| Option | Description | Selected |
|--------|-------------|----------|
| no_label: remove before 1.0 | Phase 7 lists as deprecated/removed | ✓ |
| Keep as stable alias | | |

| Option | Description | Selected |
|--------|-------------|----------|
| All new names public | setting, accessor, LABEL_MODE_DEFAULTS, card resolver | ✓ |
| Constant private | | |

| Option | Description | Selected |
|--------|-------------|----------|
| CRUD_VIEWS_LABEL_MODE_DEFAULTS | | ✓ |
| CRUD_VIEWS_DEFAULT_LABEL_MODES | | |

---

## Docs placement / example project

| Option | Description | Selected |
|--------|-------------|----------|
| One merge/replace table in settings.md | Others link | ✓ |
| Table in both pages | | |

| Option | Description | Selected |
|--------|-------------|----------|
| One canonical order section (action_menus.md) | Mermaid node links there | ✓ |
| Update each page in place | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Example project untouched | | ✓ |
| Demonstrate the setting | | |

---

## Claude's Discretion

- How "log once" is implemented, and whether the merged map is cached (it must stay correct under
  `override_settings`).
- Test file split.

## Deferred Ideas

- LATER-01 (`no_label` removal): decided "remove before 1.0".
- LATER-02 (pair rename): decided "won't rename".
- The did-you-mean hint for E108 was rejected.
