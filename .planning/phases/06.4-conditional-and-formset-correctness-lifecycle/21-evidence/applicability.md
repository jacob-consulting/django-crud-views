# Plan 06.4-21: evidence applicability

The schema-3 packet resolves **20 gates: 17 retained and 3 fresh**. Independent checking returned `PHASE64_MATRIX_OK 20 gates`; the prescribed exact JSON comparison returned `RETAINED_GATE_PROVENANCE_OK 17`. The final control inventory contains **33 genuine rejected corruption subprocesses** and an observed successful clean check. No product matrix or browser capture was repeated.

## Source continuity and packet bindings

The complete original and current source maps contain **824 identical paths**: **822 unchanged digests, 2 changed digests, zero additions and zero deletions**. Only the two fixed checker paths below may differ. Both complete maps are hash-bound; this comparison does not use HEAD, prose, or a caller-supplied exemption list. Planning Markdown is outside source(). Every retained gate is checked against its exact original manifest and effective selection, then against this current continuity proof. Current behavioral and artifact validators still run.

| Binding | SHA-256 |
|---|---|
| Original results file, [18-evidence](../18-evidence/results.json) | `a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674` |
| Original source-manifest file | `160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf` |
| Original logical source map | `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` |
| Original runner | `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` |
| Current [results.json](results.json) | `717f3495fbf3a11c4a23f037bece1136727082314854ad3fd371b56ffce40ab0` |
| Current [source-manifest.json](source-manifest.json) file | `61321dd218c3bfcead5d89eac5f126498ffb09123dabb3c8559f09f1214f1646` |
| Current logical source map | `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` |
| Current runner | `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5` |

| Changed input | Original digest | Current digest |
|---|---|---|
| `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py` | `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` | `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5` |
| `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py` | `2ed3c3f11dc25f054ef7b8c153db126b2bb7a3ce058ffd877bb12d9149fff345` | `530ab85446dfa9fd4c702b3c521066e07b63a2beaaf7ed4426ded142e33e8725` |

Fresh gate capture window: `2026-11-01T19:16:26.914663+00:00` to `2026-11-01T19:26:24.355085+00:00`. The actual corruption subprocesses and final positive check follow this window. Original gate execution timestamps remain unchanged; the new envelope timestamps describe fresh work only. Runtime preflight resolved the cached selections before any output writes. Full effective selections, including environment and import provenance, remain in the packets; all matched exactly. The summaries below show selected paths, versions and runtime digests.

## Gate dispositions

| Gate | Disposition | Current validation | Resolved execution window |
|---|---|---|---|
| `django4.2-focused` | retained | passed | 2026-11-01T16:16:32.341088+00:00 to 2026-11-01T16:17:24.733433+00:00 |
| `django4.2-enabled-full` | retained | passed | 2026-11-01T16:20:07.409092+00:00 to 2026-11-01T16:28:20.047930+00:00 |
| `django4.2-disabled-full` | retained | passed | 2026-11-01T16:32:17.204167+00:00 to 2026-11-01T16:40:47.822487+00:00 |
| `django4.2-missing-runtime` | retained | passed | 2026-11-01T16:20:03.640028+00:00 to 2026-11-01T16:20:04.914028+00:00 |
| `django5.2-focused` | retained | passed | 2026-11-01T16:17:24.935804+00:00 to 2026-11-01T16:18:40.347201+00:00 |
| `django5.2-enabled-full` | retained | passed | 2026-11-01T16:20:07.409309+00:00 to 2026-11-01T16:32:17.024508+00:00 |
| `django5.2-disabled-full` | retained | passed | 2026-11-01T16:40:48.027625+00:00 to 2026-11-01T16:53:07.473104+00:00 |
| `django5.2-missing-runtime` | retained | passed | 2026-11-01T16:20:04.996552+00:00 to 2026-11-01T16:20:06.123693+00:00 |
| `django6.0-focused` | retained | passed | 2026-11-01T16:18:40.580690+00:00 to 2026-11-01T16:20:03.379680+00:00 |
| `django6.0-enabled-full` | retained | passed | 2026-11-01T16:28:20.265677+00:00 to 2026-11-01T16:42:44.065553+00:00 |
| `django6.0-disabled-full` | retained | passed | 2026-11-01T16:42:44.249498+00:00 to 2026-11-01T16:56:56.488711+00:00 |
| `django6.0-missing-runtime` | retained | passed | 2026-11-01T16:20:06.185867+00:00 to 2026-11-01T16:20:07.335313+00:00 |
| `javascript` | retained | passed | 2026-11-01T16:56:57.813369+00:00 to 2026-11-01T16:57:10.126486+00:00 |
| `javascript-integration` | retained | passed | 2026-11-01T16:57:13.795043+00:00 to 2026-11-01T16:57:24.345026+00:00 |
| `strict-docs` | retained | passed | 2026-11-01T16:57:26.707806+00:00 to 2026-11-01T16:57:28.092025+00:00 |
| `ruff-check` | fresh | passed | 2026-11-01T19:26:21.953574+00:00 to 2026-11-01T19:26:22.005607+00:00 |
| `ruff-format` | fresh | passed | 2026-11-01T19:26:23.176273+00:00 to 2026-11-01T19:26:23.224446+00:00 |
| `evidence-self-tests` | fresh | passed | 2026-11-01T19:16:27.945130+00:00 to 2026-11-01T19:26:20.228990+00:00 |
| `conditional-browser` | retained | passed | 2026-11-01T16:58:16.474983+00:00 to 2026-11-01T16:59:09.258227+00:00 |
| `modal-browser` | retained | passed | 2026-11-01T16:59:11.080322+00:00 to 2026-11-01T16:59:34.610238+00:00 |

The historical **48,220 Python passes**, **JavaScript 347 / integration 2**, and **browser 36 cases / 305 assertions** remain original executions. Their commands, timestamps, revisions, counts, selections, source digests and all nested gate fields are JSON-identical. Original runner self-tests37 and original Ruff outcomes are historical only and are replaced in this envelope by fresh checker gates. Original25 corruption outcomes remain in the immutable origin and are not promoted into the new control inventory.

Fresh checker self-tests executed all **62** selected identities with no omission/failure/skip. They include the existing bounded ordinary JS, integration, strict-docs and synthetic-envelope/control checks. This is fresh runner-test activity, not another product matrix. Synthetic test metadata stays labeled in owned temporary fixtures; it is not emitted as acceptance evidence. The two fresh Ruff gates use their actual unchanged 23-file phase command scope.

## Original provenance and fresh executions

### django4.2-focused

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_conditional_group.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_bugs.py tests/test1/test_formset_pk_boundary.py tests/test1/test_fragment_authorization.py tests/test1/test_conditional_migration_docs.py -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-4.2-focused-83y1iqee/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:16:32.341088+00:00` to `2026-11-01T16:17:24.733433+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django4.2-enabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-4.2-enabled-full-e3zkatkp/junit.xml -o junit_family=legacy -ra --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:20:07.409092+00:00` to `2026-11-01T16:28:20.047930+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django4.2-disabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-4.2-disabled-full-uomji_vz/junit.xml -o junit_family=legacy -ra --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:32:17.204167+00:00` to `2026-11-01T16:40:47.822487+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django4.2-missing-runtime

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_conditional_layout.py::test_tracer_rendered_conditional_round_trip -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-4.2-missing-runtime-1j4yv6wx/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:20:03.640028+00:00` to `2026-11-01T16:20:04.914028+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django5.2-focused

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_conditional_group.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_bugs.py tests/test1/test_formset_pk_boundary.py tests/test1/test_fragment_authorization.py tests/test1/test_conditional_migration_docs.py -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-5.2-focused-tuvev59q/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:17:24.935804+00:00` to `2026-11-01T16:18:40.347201+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django5.2-enabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-5.2-enabled-full-j7nb3ohl/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:20:07.409309+00:00` to `2026-11-01T16:32:17.024508+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django5.2-disabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-5.2-disabled-full-tg0wzw87/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:40:48.027625+00:00` to `2026-11-01T16:53:07.473104+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django5.2-missing-runtime

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_conditional_layout.py::test_tracer_rendered_conditional_round_trip -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-5.2-missing-runtime-9ov22q0r/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:20:04.996552+00:00` to `2026-11-01T16:20:06.123693+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django6.0-focused

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_conditional_group.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_bugs.py tests/test1/test_formset_pk_boundary.py tests/test1/test_fragment_authorization.py tests/test1/test_conditional_migration_docs.py -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-6.0-focused-0o6_5mvo/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:18:40.580690+00:00` to `2026-11-01T16:20:03.379680+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django6.0-enabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-6.0-enabled-full-nd44dz1m/junit.xml -o junit_family=legacy -ra --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:28:20.265677+00:00` to `2026-11-01T16:42:44.065553+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django6.0-disabled-full

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-6.0-disabled-full-qiy13fak/junit.xml -o junit_family=legacy -ra --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:42:44.249498+00:00` to `2026-11-01T16:56:56.488711+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### django6.0-missing-runtime

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_conditional_layout.py::test_tracer_rendered_conditional_round_trip -q -p no:cacheprovider -p phase64_capture --junitxml /tmp/cv64-6.0-missing-runtime-2oa26pol/junit.xml -o junit_family=legacy -ra`.

Original runtime summary: `{"python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"}}`.

Original execution: `2026-11-01T16:20:06.185867+00:00` to `2026-11-01T16:20:07.335313+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### javascript

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/.nvm/versions/node/v24.21.0/bin/node node_modules/vitest/vitest.mjs run --reporter=default --reporter=json --outputFile.json /tmp/cv64-quality-3gf_fsf_/vitest.json`.

Original runtime summary: `{"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"vitest":{"path":"/home/alex/projects/alex/django-crud-views/node_modules/vitest/vitest.mjs","version":"5.0.3","sha256":"df72ec137c86d8454d129967ed88c640012fa8db7950d58f79cee8a94df437f1"}}`.

Original execution: `2026-11-01T16:56:57.813369+00:00` to `2026-11-01T16:57:10.126486+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### javascript-integration

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/.nvm/versions/node/v24.21.0/bin/node node_modules/vitest/vitest.mjs run --config vitest.integration.config.js --reporter=default --reporter=json --outputFile.json /tmp/cv64-quality-iil_vo80/vitest.json`.

Original runtime summary: `{"fragment_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"vitest":{"path":"/home/alex/projects/alex/django-crud-views/node_modules/vitest/vitest.mjs","version":"5.0.3","sha256":"df72ec137c86d8454d129967ed88c640012fa8db7950d58f79cee8a94df437f1"}}`.

Original execution: `2026-11-01T16:57:13.795043+00:00` to `2026-11-01T16:57:24.345026+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### strict-docs

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.venv/bin/mkdocs build --strict`.

Original runtime summary: `{"executable":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/mkdocs","version":"mkdocs, version 1.6.1 from /home/alex/projects/alex/django-crud-views/.venv/lib/python3.12/site-packages/mkdocs (Python 3.12)","sha256":"9cd0971a7454c0d04f77c0c11ca0cee5152878e2d26cfdd594b79d341f5ca73d"}}`.

Original execution: `2026-11-01T16:57:26.707806+00:00` to `2026-11-01T16:57:28.092025+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### ruff-check

Disposition: **fresh**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.venv/bin/ruff check .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py examples/bootstrap5/conditional/models.py src/crud_views/checks.py src/crud_views/lib/conditional/group.py src/crud_views/lib/conditional/layout.py src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/inline_formset.py src/crud_views/lib/formsets/render_tree.py tests/browser/conditional_formsets_server.py tests/test1/app/models.py tests/test1/test_button_classes_templates.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_group.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_migration_docs.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_fragment_authorization.py tests/test1/test_template_a11y.py`.

Original runtime summary: `{"executable":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"}}`.

Original execution: `2026-11-01T16:57:29.090463+00:00` to `2026-11-01T16:57:29.250260+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

Fresh command: `/home/alex/projects/alex/django-crud-views/.venv/bin/ruff check .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py examples/bootstrap5/conditional/models.py src/crud_views/checks.py src/crud_views/lib/conditional/group.py src/crud_views/lib/conditional/layout.py src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/inline_formset.py src/crud_views/lib/formsets/render_tree.py tests/browser/conditional_formsets_server.py tests/test1/app/models.py tests/test1/test_button_classes_templates.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_group.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_migration_docs.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_fragment_authorization.py tests/test1/test_template_a11y.py`.

Fresh runtime summary: `{"executable":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"}}`.

Fresh execution: `2026-11-01T19:26:21.953574+00:00` to `2026-11-01T19:26:22.005607+00:00`, 0.052 seconds. Current source `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` and runner `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5`. The original record remains available in the immutable origin; these fresh observations are distinct.

### ruff-format

Disposition: **fresh**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.venv/bin/ruff format --check .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py examples/bootstrap5/conditional/models.py src/crud_views/checks.py src/crud_views/lib/conditional/group.py src/crud_views/lib/conditional/layout.py src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/inline_formset.py src/crud_views/lib/formsets/render_tree.py tests/browser/conditional_formsets_server.py tests/test1/app/models.py tests/test1/test_button_classes_templates.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_group.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_migration_docs.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_fragment_authorization.py tests/test1/test_template_a11y.py`.

Original runtime summary: `{"executable":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"}}`.

Original execution: `2026-11-01T16:57:30.316213+00:00` to `2026-11-01T16:57:30.373135+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

Fresh command: `/home/alex/projects/alex/django-crud-views/.venv/bin/ruff format --check .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py examples/bootstrap5/conditional/models.py src/crud_views/checks.py src/crud_views/lib/conditional/group.py src/crud_views/lib/conditional/layout.py src/crud_views/lib/formsets/formsets.py src/crud_views/lib/formsets/inline_formset.py src/crud_views/lib/formsets/render_tree.py tests/browser/conditional_formsets_server.py tests/test1/app/models.py tests/test1/test_button_classes_templates.py tests/test1/test_conditional_checks.py tests/test1/test_conditional_formset.py tests/test1/test_conditional_group.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_migration_docs.py tests/test1/test_conditional_persistence.py tests/test1/test_formsets_controls.py tests/test1/test_formsets_policy.py tests/test1/test_formsets_validation_gate.py tests/test1/test_fragment_authorization.py tests/test1/test_template_a11y.py`.

Fresh runtime summary: `{"executable":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"}}`.

Fresh execution: `2026-11-01T19:26:23.176273+00:00` to `2026-11-01T19:26:23.224446+00:00`, 0.048 seconds. Current source `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` and runner `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5`. The original record remains available in the immutable origin; these fresh observations are distinct.

### evidence-self-tests

Disposition: **fresh**; current complete-packet validation: **passed**.

Original command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m unittest discover -s .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence -p test_runner.py -v`.

Original runtime summary: `{"chromium":{"path":"/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome","version":"Google Chrome for Testing 149.0.7827.55","sha256":"2d18db9d8608b052b6a552ee00ec1e830f93692e928b65ecc67d693bd33fe801"},"focus_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"fragment_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"mkdocs":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/mkdocs","version":"mkdocs, version 1.6.1 from /home/alex/projects/alex/django-crud-views/.venv/lib/python3.12/site-packages/mkdocs (Python 3.12)","sha256":"9cd0971a7454c0d04f77c0c11ca0cee5152878e2d26cfdd594b79d341f5ca73d"},"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"playwright":{"path":"/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright","version":"1.64.1","sha256":"313d23ce667d93962d3a1ab4be80908cefe840e4d9e48f1cd5863b91f65e8e39"},"port":8144,"python4.2":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"python5.2":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"python6.0":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"ruff":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"},"vitest":{"path":"/home/alex/projects/alex/django-crud-views/node_modules/vitest/vitest.mjs","version":"5.0.3","sha256":"df72ec137c86d8454d129967ed88c640012fa8db7950d58f79cee8a94df437f1"}}`.

Original execution: `2026-11-01T16:57:31.421909+00:00` to `2026-11-01T16:58:14.903134+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

Fresh command: `/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python -m unittest discover -s .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence -p test_runner.py -v`.

Fresh runtime summary: `{"chromium":{"path":"/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome","version":"Google Chrome for Testing 149.0.7827.55","sha256":"2d18db9d8608b052b6a552ee00ec1e830f93692e928b65ecc67d693bd33fe801"},"focus_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"fragment_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"mkdocs":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/mkdocs","version":"mkdocs, version 1.6.1 from /home/alex/projects/alex/django-crud-views/.venv/lib/python3.12/site-packages/mkdocs (Python 3.12)","sha256":"9cd0971a7454c0d04f77c0c11ca0cee5152878e2d26cfdd594b79d341f5ca73d"},"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"playwright":{"path":"/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright","version":"1.64.1","sha256":"313d23ce667d93962d3a1ab4be80908cefe840e4d9e48f1cd5863b91f65e8e39"},"port":8144,"python4.2":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-4-2/bin/python","version":{"python":"3.12.3","django":"4.2.30"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"python5.2":{"path":"/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-5-2/bin/python","version":{"python":"3.12.3","django":"5.2.18"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"python6.0":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"ruff":{"path":"/home/alex/projects/alex/django-crud-views/.venv/bin/ruff","version":"ruff 0.17.3","sha256":"6761c67c2b307be3905473b165eb5af0fb2f083836b04f9e4a8cdd0caee37833"},"vitest":{"path":"/home/alex/projects/alex/django-crud-views/node_modules/vitest/vitest.mjs","version":"5.0.3","sha256":"df72ec137c86d8454d129967ed88c640012fa8db7950d58f79cee8a94df437f1"}}`.

Fresh execution: `2026-11-01T19:16:27.945130+00:00` to `2026-11-01T19:26:20.228990+00:00`, 592.284 seconds. Current source `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` and runner `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5`. The original record remains available in the immutable origin; these fresh observations are distinct.

### conditional-browser

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/.nvm/versions/node/v24.21.0/bin/node tests/browser/conditional-formsets.cjs --case all --output /tmp/cv64-browser-gaclj75y/browser.json`.

Original runtime summary: `{"chromium":{"path":"/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome","version":"Google Chrome for Testing 149.0.7827.55","sha256":"2d18db9d8608b052b6a552ee00ec1e830f93692e928b65ecc67d693bd33fe801"},"focus_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"playwright":{"path":"/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright","version":"1.64.1","sha256":"313d23ce667d93962d3a1ab4be80908cefe840e4d9e48f1cd5863b91f65e8e39"},"port":8144}`.

Original execution: `2026-11-01T16:58:16.474983+00:00` to `2026-11-01T16:59:09.258227+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

### modal-browser

Disposition: **retained**; current complete-packet validation: **passed**.

Original command: `/home/alex/.nvm/versions/node/v24.21.0/bin/node tests/browser/modal-focus.cjs --case all --output /tmp/cv64-browser-09qa_3kl/browser.json`.

Original runtime summary: `{"chromium":{"path":"/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome","version":"Google Chrome for Testing 149.0.7827.55","sha256":"2d18db9d8608b052b6a552ee00ec1e830f93692e928b65ecc67d693bd33fe801"},"focus_python":{"path":"/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","version":{"python":"3.12.3","django":"6.0.9"},"sha256":"e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"},"node":{"path":"/home/alex/.nvm/versions/node/v24.21.0/bin/node","version":"v24.21.0","sha256":"7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c"},"playwright":{"path":"/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright","version":"1.64.1","sha256":"313d23ce667d93962d3a1ab4be80908cefe840e4d9e48f1cd5863b91f65e8e39"},"port":8143}`.

Original execution: `2026-11-01T16:59:11.080322+00:00` to `2026-11-01T16:59:34.610238+00:00`. Original source `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` and runner `cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c` remain the provenance of this historical record.

## Fresh corruption observations

Every row is an actual current-runner `--check --output` subprocess. Each returned integer exit1, empty stdout and its exact predicate-specific rejection stderr. Both payload and control-record stages ran; none is an origin outcome or invented bootstrap record. Aggregate and handoff checks require the complete detailed and summary inventories. There is no CLI controls-bypass acceptance mode.

| Case | Actual command argv | Exit | Actual stderr |
|---|---|---:|---|
| `capture-digest` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/capture-digest.json"]` | 1 | `MATRIX_REJECTED: Conditional capture digest mismatch: desktop` |
| `capture-missing` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/capture-missing.json"]` | 1 | `MATRIX_REJECTED: Conditional capture inventory invalid: stock` |
| `capture-observation` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/capture-observation.json"]` | 1 | `MATRIX_REJECTED: Conditional capture icon observations invalid: desktop` |
| `control-missing-evidence` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/control-missing-evidence.json"]` | 1 | `MATRIX_REJECTED: Checker control evidence inventory incomplete` |
| `control-missing-summary` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/control-missing-summary.json"]` | 1 | `MATRIX_REJECTED: Checker control summary inventory incomplete` |
| `control-success-outcome` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/control-success-outcome.json"]` | 1 | `MATRIX_REJECTED: Checker control exit invalid: exit-code` |
| `control-wrong-command` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/control-wrong-command.json"]` | 1 | `MATRIX_REJECTED: Checker control command invalid: exit-code` |
| `control-wrong-diagnostic` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/control-wrong-diagnostic.json"]` | 1 | `MATRIX_REJECTED: Checker control diagnostic mismatch: exit-code` |
| `disabled-node-absence` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/disabled-node-absence.json"]` | 1 | `MATRIX_REJECTED: django4.2-disabled-full: forged Node-free environment` |
| `disabled-opt-in` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/disabled-opt-in.json"]` | 1 | `MATRIX_REJECTED: django4.2-disabled-full: forged Node-free environment` |
| `docs-non-strict` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/docs-non-strict.json"]` | 1 | `MATRIX_REJECTED: strict-docs: wrong quality command` |
| `exit-code` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/exit-code.json"]` | 1 | `MATRIX_REJECTED: django4.2-focused: green suite failed/empty` |
| `inline-clear-assertion` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/inline-clear-assertion.json"]` | 1 | `MATRIX_REJECTED: Missing/false assertion inline-file-clear-unchanged` |
| `integration-missing` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/integration-missing.json"]` | 1 | `MATRIX_REJECTED: Missing/extra matrix gates` |
| `js-duplicate-case` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-duplicate-case.json"]` | 1 | `MATRIX_REJECTED: JS missing/duplicate case selection` |
| `js-duplicate-file` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-duplicate-file.json"]` | 1 | `MATRIX_REJECTED: JS missing/duplicate file` |
| `js-failed-case` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-failed-case.json"]` | 1 | `MATRIX_REJECTED: JS failed/skipped required case` |
| `js-false-counts` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-false-counts.json"]` | 1 | `MATRIX_REJECTED: JS inconsistent counts` |
| `js-filtered-command` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-filtered-command.json"]` | 1 | `MATRIX_REJECTED: javascript: wrong quality command` |
| `js-missing-case` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-missing-case.json"]` | 1 | `MATRIX_REJECTED: JS missing/duplicate case selection` |
| `js-missing-file` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-missing-file.json"]` | 1 | `MATRIX_REJECTED: JS missing/duplicate file` |
| `js-skipped-case` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-skipped-case.json"]` | 1 | `MATRIX_REJECTED: JS failed/skipped required case` |
| `js-wrong-executable` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/js-wrong-executable.json"]` | 1 | `MATRIX_REJECTED: javascript: wrong quality command` |
| `negative-control-setup-error` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/negative-control-setup-error.json"]` | 1 | `MATRIX_REJECTED: django4.2-missing-runtime: setup/collection failure is not runtime proof` |
| `raw-balance-assertion` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/raw-balance-assertion.json"]` | 1 | `MATRIX_REJECTED: Missing/false assertion fragment-raw-balance` |
| `required-case-list` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/required-case-list.json"]` | 1 | `MATRIX_REJECTED: Corrupted required-case list` |
| `ruff-format-missing-check` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/ruff-format-missing-check.json"]` | 1 | `MATRIX_REJECTED: ruff-format: wrong quality command` |
| `ruff-wrong-subcommand` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/ruff-wrong-subcommand.json"]` | 1 | `MATRIX_REJECTED: ruff-check: wrong quality command` |
| `source-hash` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/source-hash.json"]` | 1 | `MATRIX_REJECTED: Missing/stale source manifest` |
| `tracer-absent` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/tracer-absent.json"]` | 1 | `MATRIX_REJECTED: django4.2-focused: required tracer missing/skipped/failed` |
| `tracer-failed` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/tracer-failed.json"]` | 1 | `MATRIX_REJECTED: django4.2-focused: green suite failed/empty` |
| `tracer-skipped` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/tracer-skipped.json"]` | 1 | `MATRIX_REJECTED: django4.2-focused: unexpected skip/reason` |
| `tracer-zero-selected` | `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/tmp/cv64-checker-controls-huupb1gl/tracer-zero-selected.json"]` | 1 | `MATRIX_REJECTED: django4.2-focused: inconsistent/empty counts` |

Clean positive observation: command `["/home/alex/projects/alex/django-crud-views/.nox/crispy_floor-3-12-django-6-0/bin/python","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","--check","--output","/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/21-evidence/results.json"]`, exit 0, stdout `"PHASE64_MATRIX_OK 20 gates source=d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490\n"`, stderr `""`. This records an observed complete check; it is not a self-referential admission prerequisite. The separately invoked prescribed checker also passed; see [check log](../.review-diagnostics/21-02-check.log) and [retained comparison](../.review-diagnostics/21-02-provenance.log).

## Immutable historical files and capture validation

All five orchestrator baseline hashes still match after the fresh self-tests and final checks. Current screenshot validators rechecked the exact desktop/mobile/tablet stock PNG bytes, digests and observed viewport/icon contracts, plus referenced modal screenshots. Native conditional captures remain explicitly empty. There was no Chromium recapture, new native screenshot requirement or product repair.

| Historical file | Unchanged SHA-256 |
|---|---|
| `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/18-evidence/results.json` | `a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674` |
| `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/18-evidence/source-manifest.json` | `160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf` |
| `.planning/ui-reviews/06.4-gap-repair/tablet.png` | `55c2ee11a8e16140abb64a9fe37f55feb07428322e5fa6a4ed9e76f33be16282` |
| `.planning/ui-reviews/06.4-gap-repair/mobile.png` | `314006515ef104b3a93a7b390aec27addf67733df5b37fc53752e447b731edfe` |
| `.planning/ui-reviews/06.4-gap-repair/desktop.png` | `6af0369c076c37eb02a9e132e6da01fd1b04a52bc1ec428f7e2fc59f8f2b81ef` |

## Retained limits and acceptance

- Historical environment bounds remain Python3.12.3; Django4.2.30,5.2.18,6.0.9; Chromium149.0.7827.55. Python3.13–3.15 and other browsers/devices remain unclaimed.
- Exactly four full-suite CSP skip events retain `tests/test1/test_assets.py::test_django6_builtin_csp_nonce_roundtrip` and reason `built-in CSP middleware requires Django 6.0`. Exactly four crispy-floor golden deselections retain `tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`. No exclusion changed.
- AUTH-02 remains A19-only: int/UUID non-first/deeper fragment/management/POST/database round trips with authorization and ancestry preserved. Broader Guardian #286/custom-PK/backend guarantees remain outside this proof.
- Native False-clear/None-no-change, trusted server-disabled precedence, stored-byte retention, default inactive skip, explicit managed-queryset purge, authorized querysets and routed atomic/rollback boundaries remain source-bound. ImageField is reference-only; image-byte decoding/dimensions and broader storage guarantees remain unclaimed.
- Preserve A8 commit=False, A25, #210/jQuery, broader field/theme/backend exclusions and Phase7 stability limits. All31 fallback assumptions remain flagged-unresolved; no generic concurrency/precision guarantee is inferred.
- H1 remains pending actual corrected stock/native discoverability, readability, keyboard, focus and assistive-technology judgment. H2 remains pending: **Switching a conditional file field off must not silently authorize deletion of the stored file content.** Its canonical status remains **flagged-unverified**. No actor/time/response or human approval is invented.
- The complete refreshed matrix and shared handoff validation are evidence enforcement, not independent acceptance. The actual handoff rebind, code/security reassessment, canonical verification and human dispositions belong to plan22/orchestrator. G6/WR-03/04 and linked threats await those dispositions. No phase completion, Phase7 advancement, release, merge or ready=true claim is made.

