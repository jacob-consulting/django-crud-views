# Phase 06.6 action-group pack evidence

The ordinary upstream FormActions probe below was executed before the bridge implementation,
using the checkout via PYTHONPATH=src:. Both render real layout fields. Probe exit 0 means
the observation was captured; the floor's consumes_class=false is the actual supported-pack
incompatibility, not passing class support.

The production bridge is selected only for pack bootstrap5, the real path of the installed
crispy-bootstrap5 distribution's own layout/formactions.html, and the entire exact audited
2023.10 source. Every predicate is required on each render. The bridge adds escaped class
text only to the original outer wrapper and retains attrs/flat_attrs, label_class,
field_class, blank lines and fields_output exactly. There is no hidden-input branch in
this original template. Filter trailing-input preservation is verified separately.

The library uses a render-local copy for effective classes, retaining the authored object
and its primitive registry key. No installed template, global pack override, HTML
postprocessing, capability cache or generic fallback is used.

## Upstream source contract

The installed crispy-forms 2.0 and 2.7 FormActions implementations both render their
fields, select the active pack template, and pass formactions plus fields_output.
The adapter preserves that contract and the resolved template.
[Official FormActions source](https://django-crispy-forms.readthedocs.io/en/latest/_modules/crispy_forms/bootstrap.html)
was checked alongside both installed versions. Context7 CLI was unavailable.

## Original current-pack observation

Command: PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_action_groups.py::test_pack_structure_probe -q -s

```text
{"versions": {"Django": "5.2.18", "django-crispy-forms": "2.7", "crispy-bootstrap5": "2026.9"}, "origin": "/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/formactions.html", "source": "<div\n    {% if formactions.flat_attrs %}{{ formactions.flat_attrs }}{% endif %} \n    class=\"mb-3{% if 'form-horizontal' in form_class %} row{% endif %} {{ formactions.css_class|default:'' }} {{ field_class }}\" \n    {% if formactions.id %} id=\"{{ formactions.id }}\"{% endif %}>\n    {% if label_class %}\n        <div class=\"aab {{ label_class }}\"></div>\n    {% endif %}\n    <div class=\"{{ field_class }}\">\n        {{ fields_output|safe }}\n    </div>\n</div>\n", "empty": "<div\n     \n    class=\"mb-3  fields\" \n    >\n    \n        <div class=\"aab labels\"></div>\n    \n    <div class=\"fields\">\n        <b>Control</b>\n    </div>\n</div>\n", "nonempty": "<div\n     \n    class=\"mb-3 phase066-probe fields\" \n    >\n    \n        <div class=\"aab labels\"></div>\n    \n    <div class=\"fields\">\n        <b>Control</b>\n    </div>\n</div>\n", "consumes_class": true}
.
1 passed in 0.09s
```

## Original floor-pack observation

Command: PYTHONPATH=src:. .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_theme_action_groups.py::test_pack_structure_probe -q -s

```text
{"versions": {"Django": "6.0.9", "django-crispy-forms": "2.0", "crispy-bootstrap5": "2023.10"}, "origin": "/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/formactions.html", "source": "<div{% if formactions.attrs %} {{ formactions.flat_attrs }}{% endif %} class=\"mb-3\">\n    {% if label_class %}\n        <div class=\"aab {{ label_class }}\"></div>\n    {% endif %}\n\n    <div class=\"{{ field_class }}\">\n        {{ fields_output|safe }}\n    </div>\n</div>\n", "empty": "<div class=\"mb-3\">\n    \n        <div class=\"aab labels\"></div>\n    \n\n    <div class=\"fields\">\n        <b>Control</b>\n    </div>\n</div>\n", "nonempty": "<div class=\"mb-3\">\n    \n        <div class=\"aab labels\"></div>\n    \n\n    <div class=\"fields\">\n        <b>Control</b>\n    </div>\n</div>\n", "consumes_class": false}
.
1 passed in 0.07s
```

## Scoped bridge verification

The task 03-01 ordinary/pack_structure selection passes 14 cases on current Django 5.2
and 14 on the Django 6.0 floor. It verifies exact empty-wrapper bytes, ordinary/delete
sentinels, the complete audited source, changed attrs/label/field/output/whitespace,
custom filesystem/locmem origins and a fresh selection after template override restoration.
Custom templates with even the exact floor text remain unmodified.

## Final regression results

| Runtime | Selection | Actual result |
| --- | --- | --- |
| Django 5.2.18 / crispy 2.7 / Bootstrap 2026.9 | Task 03-02 groups/filter/pinned/goldens/class checks/complete table | 577 passed in 11.02s, four workers |
| Django 6.0.9 / crispy 2.0 / Bootstrap 2023.10 | Final groups/goldens/filter | 94 passed in 6.30s, four workers |
| Django 4.2.30 / crispy 2.0 / Bootstrap 2023.10 | Same final groups/goldens/filter, after 6.0 completed | 94 passed in 4.16s, four workers |
| Django 5.2.18 / crispy 2.7 / Bootstrap 2026.9 | All final action-group tests | 36 passed in 1.22s, four workers |

Commands, from the core repository root:

```bash
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_action_groups.py tests/test1/test_filter.py tests/test1/test_filter_pinned.py tests/test1/test_form_buttons_golden.py tests/test1/test_button_classes_checks.py tests/test1/test_button_classes.py -n 4 -q
PYTHONPATH=src:. .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_theme_action_groups.py tests/test1/test_form_buttons_golden.py tests/test1/test_filter.py -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline
PYTHONPATH=src:. .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_theme_action_groups.py tests/test1/test_form_buttons_golden.py tests/test1/test_filter.py -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_theme_action_groups.py -n 4 -q
```

The two floor invocations exclude only the historical full filter-wrapper golden named in
`noxfile.py:CRISPY_FLOOR_DESELECT`, exactly as this plan permits. No group test is skipped or
excluded; each pack's own original empty wrapper is independently compared byte-for-byte.
Original floor class omission remains recorded above; no original probe or golden was changed.

The final matrix covers custom Bootstrap-name and custom-name packs that consume or ignore
classes, custom filesystem/locmem overrides, hostile strings including marked-safe inputs,
original attrs/label/field branches, repeated/deep-copied prepared filter helpers, settings
restoration, and untouched trailing sort/order/direction inputs. The actual documentation
recipe is extracted and executed for both ordinary and filter groups, retaining native
submit/button cancellation and submit/reset filter semantics. The complete live table and
documentation count are 88; utility mode suffixes still warn under W362.

## Runtime import provenance

Every runtime reported core import:
`/home/alex/projects/alex/django-crud-views/src/crud_views/__init__.py`.
Executables are the absolute paths under `/home/alex/projects/alex/django-crud-views/`:

- `.nox/tests-3-12-django-5-2/bin/python`
- `.nox/crispy_floor-3-12-django-6-0/bin/python`
- `.nox/crispy_floor-3-12-django-4-2/bin/python`

In each environment, imports were its own `lib/python3.12/site-packages/crispy_forms/__init__.py`
and `lib/python3.12/site-packages/crispy_bootstrap5/__init__.py`; the template origin is that
same pack directory plus `templates/bootstrap5/layout/formactions.html`. Actual metadata
versions are in the table above. No runtime, pack or installed source was modified.

## Boundaries and TDD

Task 03-01 RED executed the real ordinary library group: the configured sentinel was absent.
Task 03-02 RED executed the real filter helper: its independent sentinel was absent. Both
JUnit records returned RED_EVIDENCE_OK before implementation. Task 03-03 changes only tests
and this evidence; the centralized behavior-adding predicate returned false. Its new
compatibility assertions passed against the already-implemented bridge without a product change.

This resolves research A1 for the exact audited Bootstrap floor and tested current pack.
It does not establish universal pack support or real Tabler acceptance; plan 07 owns the
actual companion pack. No dependency floor was increased and no package was installed.

## Post-wave sentinel integration correction — 2026-11-02

The first full wave-2 suite reported 1 failed, 8632 passed, 1 skipped in 210.97s;
original log `/tmp/phase-06.6-wave2-pytest.log`. Failure:
`tests/test1/test_button_classes_templates.py::test_button_chain_renders_only_table_classes`.
The offending token was `mb-3` on the new sentinel-bearing filter group wrapper on `/publisher/`
and `/publisher_order/card/?order=name&dir=asc` / `dir=desc`.

Focused reproduction (serial because this is one integration test):

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_button_classes_templates.py::test_button_chain_renders_only_table_classes -q --junitxml=/tmp/phase03-wave2-red.xml
1 failed in 1.06s
```

Source tracing confirmed the installed current template owns the existing `mb-3` token;
the audited floor source above also owns it. `_ThemedFormActions` only appends the configured class.
The guard's dynamically generated sentinel map began selecting this wrapper when the two group keys
were added. This exposed a mismatch between the older guard and D-17's additive contract, not a
new hardcoded button class in product code.

The test guard now permits that single token only on the group `div` itself. Both group keys remain
scanned. Actual ordinary/filter renders assert exactly the sentinel plus `mb-3`; mutations demonstrate
that `mb-3` on controls/labels, `mt-4` on the wrapper, and wrong wrapper tags/sentinels still fail.
Before the fix, those renderer cases gave 2 failed, 3 passed, 47 deselected in 0.23s;
JUnit `/tmp/phase03-wave2-guard-red.xml`, validated record `.git/gsd-plan03-wave2-red.json`.

Verification at the same current runtime and core source root as above:

```text
PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_button_classes_templates.py tests/test1/test_theme_action_groups.py tests/test1/test_form_buttons_golden.py tests/test1/test_filter.py -n 4 -q
147 passed in 6.89s
```

No product/template, installed pack, golden baseline, floor exclusion, or original floor evidence changed.
The full-suite rerun is delegated to the parent wave orchestrator and is not represented by this focused result.
