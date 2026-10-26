# Phase 02: Form key grammar - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 5 expected modified files
**Analogs found:** 5 / 5 (existing files are their own closest analogs)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/crud_views/lib/button_classes.py` | utility | transform | Same file, `_action_key_parts()` and `button_class_check_messages()` | exact |
| `tests/test1/test_button_classes.py` | test | transform, file-I/O | Same file, completeness and resolver tests | exact |
| `tests/test1/test_button_classes_checks.py` | test | transform | Same file, settings/theme acceptance and W362 tests | exact |
| `docs/reference/buttons.md` | config (reference documentation) | transform (documentation) | Same file, class-table and structure tables | exact |
| `CHANGELOG.md` | config (release documentation) | transform (documentation) | Same file, Unreleased entries | exact |

Documentation is classified as config only to fit the planner's role vocabulary; neither Markdown file executes a data flow. All named analog paths were confirmed git-tracked with `git ls-files -- <path>`.

## Pattern Assignments

### `src/crud_views/lib/button_classes.py` (utility, transform)

**Analog:** existing implementation in the same file.

**Imports and validation boundary** (lines 210–220):

```python
    # Imports remain inside _action_key_parts(), after Django setup for checks.
    from .view.button_data import LOCATIONS
    from .view.variant import VARIANTS

    if not isinstance(key, str):
        return None
    parts = key.split(":")
    if len(parts) == 3 and parts[0] in LOCATIONS and parts[1] in VARIANTS:
        return parts[0], parts[1], parts[2]
```

The comment above summarizes the existing docstring; the executable statements are verbatim. Replace the dependency on button-data `LOCATIONS` with explicit immutable class-key variant locations and the five form kinds. Keep `VARIANTS` and `LABEL_MODES` imports local. Update helper docstrings to describe variant-or-kind slots. Do not widen `button_data.LOCATIONS`, E108, or label-mode defaults.

**Separate mode-membership stage** (lines 226–229):

```python
    from .view.label_mode import LABEL_MODES

    parts = _action_key_parts(key)
    return parts is not None and parts[2] in LABEL_MODES
```

**Diagnostic pattern** (lines 277–282 and 285–290):

```python
        if (parts := _action_key_parts(key)) is not None:
            messages.append(
                DjangoWarning(
                    f"Button class {key!r} has an unknown label mode {parts[2]!r}.",
                    hint=f"Use one of {sorted(LABEL_MODES)}.",
                    id="crud_views.W362",
```

```python
        else:
            messages.append(
                DjangoWarning(
                    f"Button class {key!r} is not a known key (typo?).",
                    hint="See the buttons documentation page for the list of keys.",
                    id="crud_views.W362",
```

Retain both branches and warning severity: a known form kind with a bad mode takes the first branch; an unknown kind or structural slot takes the second. Existing value validation at lines 241–249 remains independent of key validation. No auth/guard applies to developer configuration checks.

### `tests/test1/test_button_classes.py` (test, transform/file-I/O)

**Analog:** same file, lines 73–85 (registry isolation and complete default-table contract).

```python
@pytest.fixture(autouse=True)
def _isolate_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    reset_button_classes_cache()
```

```python
def test_default_table_is_complete():
    assert len(EXPECTED_KEYS) == 70
    assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS
```

Extend existing resolver cases at lines 167–193 for form-mode override, missing-key fallback, explicit `None`/empty suppression, and theme-mode versus settings-base precedence. Preserve the import-boundary guard at lines 212–223. Add the narrowly scoped canonical count guard here: read `docs/reference/buttons.md`, require exactly one `The default table has (\d+) keys` match, and compare the captured integer with `len(DEFAULT_BUTTON_CLASSES)`. The current table has 70 entries; do not add mode-key combinations to defaults.

The repository-root read-path convention is already documented by the research from tracked `tests/test1/test_label_mode_docs.py:13–17`:

```python
ROOT = Path(__file__).resolve().parents[2]
```

Use `ROOT / "docs" / "reference" / "buttons.md"`; add standard-library `re`/`Path` imports ahead of existing pytest/Django imports. No broad prose-contract framework is needed.

### `tests/test1/test_button_classes_checks.py` (test, transform)

**Analog:** same file: registry fixture at lines 11–18; acceptance test at lines 63–68; invalid-key and invalid-mode cases at lines 71–109.

Copy its existing settings/theme dual-source arrangement for all five independently specified kinds × three modes. Remove `form:submit:icon` from the invalid-key cases. Keep non-string key/value safety coverage and assert the two W362 diagnostic branches separately. Include unknown kinds, structural/utility suffixes, form variants, malformed segment counts, invalid/empty modes, and valid form-mode values of `None`/empty string. Simulate a future button-data location and assert that it does not expand class-key acceptance.

Use the unchanged production diagnostic strings quoted above as assertion targets; do not introduce form-specific warning text. Continue using fixture snapshot/restore and cache reset, rather than leaving registrations behind.

### `docs/reference/buttons.md` (reference documentation)

**Analog:** same file's compact key/default table, lines 88–92:

```markdown
| `form:submit` | `btn btn-primary` |
| `form:cancel` | `btn btn-secondary` |
| `form:delete` | `btn btn-primary` |
| `form:filter-submit` | `btn btn-primary` |
| `form:filter-reset` | `btn btn-secondary` |
```

Follow the table style at lines 138–143 for the compact grammar table. Distinguish context/list/card variants, the five form kinds, and structural/utility slots with no mode suffix. Add the locked valid/invalid examples and one `form:submit:icon` → `form:submit` fallback example under `#the-class-table`.

The two stale numeric claims are at lines 115 and 118:

```text
The default table has 64 keys
```

```text
and the like) are addressable but not shipped: none is in the default table, and the count stays 64.
```

Correct the canonical count to 70 and remove the redundant numeric claim. Document key addressability without implying that form rendering or form label-mode defaults are implemented in this phase.

### `CHANGELOG.md` (release documentation)

**Analog:** same file's current release header, lines 1–7:

```markdown
# Django CRUD Views - Changelog

## Unreleased

Upgrading from 0.29.x? See [Migrating to 1.0.0](docs/migrating-1.0.md).

### Breaking
```

Add a concise bullet under the appropriate existing Unreleased subsection describing acceptance of form-kind mode keys and corrected grammar documentation. This is compatible validation expansion with unchanged rendering/default entries. If implementation introduces a Breaking entry, the repository rule also requires updating `docs/migrating-1.0.md`; that is a conditional scope expansion, not a currently expected sixth file.

## Shared Patterns

### Presence-based mode fallback

**Source:** `src/crud_views/lib/button_classes.py:142–147`
**Apply to:** resolver regression tests and documentation example; preserve implementation.

```python
    classes = get_button_classes()
    key = f"{location}:{slot}"
    if mode and f"{key}:{mode}" in classes:
        key = f"{key}:{mode}"
    value = classes.get(key)
    return value if isinstance(value, str) else ""
```

### Layer merging and test isolation

**Source:** `src/crud_views/lib/button_classes.py:127–133`
**Apply to:** both test modules; use existing fixtures and `override_settings` conventions.

```python
    if classes is None:
        classes = {**DEFAULT_BUTTON_CLASSES, **_THEME_BUTTON_CLASSES, **_settings_layer()}
        _button_classes_cache = classes
    return classes
```

### Scope and validation boundaries

Keep rendering, crispy adapters, templates, goldens, defaults, button-data locations, and E108 unchanged. No new authentication, logging, transaction, migration, or request-handling patterns apply. No tests were run during pattern mapping.

## No Analog Found

None. Each expected modified file already contains the appropriate pattern. The canonical numeric count parser is a small new assertion using existing repository documentation-read conventions, not a new subsystem.

## Metadata

**Analog search scope:** targeted five expected files plus existing documentation-contract tests.
**Files scanned:** 6 tracked implementation/test/documentation candidates; phase context, research, and project instructions also consulted.
**Primary analogs:** 5 (self-matches); one supplementary tracked test supplies the repository-root path convention.
**Project skills:** no project-local `.agents/skills/` or `.codex/skills/` entries found.
**Pattern extraction date:** 2026-10-26.
