I'll review all ten current plans against source, starting with the A15–A17 closure points and the integration paths those plans depend on.
Source is available. Next I’ll read the binding, clearing, formset, and runtime paths the ten plans claim to change.
A15 hinges on whether reference-only ImageField saves still import Pillow. I’ll check the installed Django field path and the plan’s fixture setup.
## 06.4-01

Summary: Exact owning-form bound names plus an inline tracer Node resolver. Executable against current suffix lookup at `src/crud_views/static/crud_views/js/toggle.js:15-20` and unprefixed `cv_toggle_field` at `src/crud_views/lib/conditional/layout.py:29`.

Strengths: `form.add_prefix` matches Django hyphen prefixes. `Profile` exists at `tests/test1/app/models.py:202`. A17 is owned in `06.4-01-PLAN.md:84,113`: `_resolve_tracer_node` stays in `tests/test1/test_conditional_layout.py`, `CV_FOCUS_NODE` precedes `06-JS-RUNTIME.json` `node.path`, matching `tests/browser/modal-focus.cjs:12`, and missing runtimes fail pytest.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Binding and tracer startup are specified tightly enough to execute.

## 06.4-02

Summary: Field-aware clearing through `_post_clean` and a real `XFormSet.save` signal. Current clear is always `None` at `src/crud_views/lib/conditional/group.py:36-37,84`; save still requires `has_changed()` at `src/crud_views/lib/formsets/render_tree.py:259`.

Strengths: A15 is a reference-only ImageField bound with real FileField upload discard at `06.4-02-PLAN.md:79,111`. `FileField.clean` returns `False` before `ImageField.to_python` imports PIL (`django/forms/fields.py:687-689,720-729`). No `width_field`/`height_field` skips `update_dimension_fields` (`django/db/models/fields/files.py:490-492`). `migrate` defaults `skip_checks=True`, so E210 at `files.py:439-451` is not invoked. H1 remains on the save predicate.

Concerns: None.

Suggestions: None.

Risk Assessment: Low for the Pillow bound. Persistence still depends on applying empties before `construct_instance` skips omitted defaults (`django/forms/models.py:75-82`); the plan states that order.

## 06.4-03

Summary: Shared resolver becomes static `E312` and runtime `ImproperlyConfigured`. `E312` is unused. `W320` still assumes null/blank only at `src/crud_views/checks.py:79-84`.

Strengths: Per-form namespaces and E310/E311 preservation match `checks.py:59-77`. A02 stays incorporated at `06.4-03-PLAN.md:86`.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Check traversal can reuse declared `base_fields` without request forms.

## 06.4-04

Summary: Mandatory active-row policy before `cv_form_valid`. `all_valid` is two-pass at `src/crud_views/lib/formsets/formsets.py:354-369`; save is later at `src/crud_views/lib/formsets/mixins.py:114-128`.

Strengths: H3 stays executable. `klass` is Django `BaseInlineFormSet` (`formsets.py:12,60,77-89`), while `FormSet.init` passes `formset`/`parent_form` (`formsets.py:148-160`). The native adapter and positive GET/POST are required at `06.4-04-PLAN.md:90-91`. H1's save signal is retained.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Factory `edit_only` plus the adapter covers both class families.

## 06.4-05

Summary: Baseline plus ancestor owners, macrotask reset, and stranded-focus recovery. Current JS writes `disabled` unconditionally and does not observe reset (`toggle.js:23-31`).

Strengths: A04/A10 unit timing stays here; Chromium proof stays in 08. Management names match `toggle.js:13`. Modal focus ownership stays in `modal.js`.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. jsdom can prove observer mechanics; browser proof is sequenced later.

## 06.4-06

Summary: One controller per form, stock Add gating, and attribute equality instead of prefix interpolation. Current lookups interpolate prefixes at `src/crud_views/static/crud_views/js/formset.js:165,172-181`; Add is unconditional at `src/crud_views/templates/crud_views/formsets/control.html:19-22`.

Strengths: A16 is closed at `06.4-06-PLAN.md:98-100`. Supported keys are `^[a-z\-]+$` (`formsets.py:294-298`); `line-items` passes, `line.items:detail` is only a rejection control. UUID and deep hyphenated prefixes are DOM identities, not declaration keys. `FormControl` receives the declaration, which exposes `edit_only` (`src/crud_views/lib/formsets/layout.py:29`, `formsets.py:112-113`).

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Selector repair no longer depends on expanding key grammar.

## 06.4-07

Summary: Declaration index replaces fixed `index=0`, and fragment wrappers balance before parsing. `get_template` still passes `index=0` at `formsets.py:513`; close uses absent `end_at_rows` at `src/crud_views/templates/crud_views/formsets/formset.html:56` while open uses `render_rows_only` at `:4`.

Strengths: H2 remains unconditional: match the opening predicate, raw token stack, stray-close negative control (`06.4-07-PLAN.md:86,100`). Child indices already exist at `formsets.py:181-188`. Auth keys stay unchanged.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. A wrong close predicate fails the raw-stack check.

## 06.4-08

Summary: Real HTTP/Chromium acceptance, including the image bound and prior regression IDs. No runner exists yet; that absence is expected.

Strengths: A15 is mirrored at `06.4-08-PLAN.md:81,119,133`: reference-only ImageField, no dimension hooks, FileField assertions `file-upload-received`, `off-file-upload-discarded`, `uploaded-file-not-stored` in both themes. A06/A07/A04/A10 remain named and required. Modal listener still ignores `defaultPrevented` at `modal.js:227-232`; 06 owns that fix before this wave.

Concerns: None.

Suggestions: None.

Risk Assessment: Low for the revised image contract. Browser evidence is still future execution, not a plan hole.

## 06.4-09

Summary: Docs and executable recipes publish the proved matrix and Phase 7 names. Current conditional docs still describe generic clearing.

Strengths: A15 publication is explicit at `06.4-09-PLAN.md:101-103`: ImageField reference rows stay, image-byte validation is unexercised, upload discard is FileField-only, no Pillow install or skip. A08/A13 remain in the same task.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Recipes are gated on 02/03/07/08 evidence.

## 06.4-10

Summary: Three-series, JS, docs, lint, and browser evidence, then scoped A19 handoff. Evidence files are planned outputs, not missing inputs.

Strengths: H1/H2/A04/A10 assertion IDs are mandatory at `06.4-10-PLAN.md:96`. A15's browser set is inherited from 08. A8/A25/#286 stay excluded. Checker corruption controls are specified.

Concerns: None.

Suggestions: None.

Risk Assessment: Low as a gate plan. It correctly refuses to mark unrun Python versions or the file-deletion prohibition green from ordinary pytest alone.

## Prior-item closure ledger

| Item | Verdict | Evidence |
|---|---|---|
| H1 | CLOSED, no regression | `06.4-02-PLAN.md:96,111`; `06.4-04-PLAN.md:90,107`; `06.4-08-PLAN.md:107,119,133`; `06.4-10-PLAN.md:96`. Save still gated by `render_tree.py:259`. |
| H2 | CLOSED, no regression | `06.4-07-PLAN.md:86,100`; `06.4-08-PLAN.md:108,119`; `06.4-10-PLAN.md:96`. Mismatch is `formset.html:4` vs `:56`. |
| H3 | CLOSED, no regression | `06.4-04-PLAN.md:90-91`. Django `BaseInlineFormSet` is accepted at `formsets.py:60,88-89`; extra kwargs are adapted. |
| A01–A14 | CLOSED, no regression | Prior dispositions remain in the owning tasks. A12's selector repair remains; its bad fixture is replaced by A16. |
| A15 | CLOSED | Reference-only ImageField, no Pillow, no image bytes, no dimension fields, no E210 silencing; FileField upload discard required in 02, 08, and 09. Clear path does not import PIL (`fields.py:687-729`). |
| A16 | CLOSED | Supported `line-items` / UUID / deep hyphenated / two-form identities; punctuation key is a rejection control only (`06.4-06-PLAN.md:99-100` vs `formsets.py:294-298`). |
| A17 | CLOSED | Inline `_resolve_tracer_node`, `CV_FOCUS_NODE` then manifest `node.path`, explicit failure, no extra helper file (`06.4-01-PLAN.md:84,113`; `modal-focus.cjs:12`). |

## Unresolved concerns

None. No new HIGH. A15, A16, and A17 are executable and sufficient. No further plan revision is required.
