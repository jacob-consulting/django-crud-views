# Queryset-driven conditional fields on base forms and inline rows

Status: approved by the maintainer on 2026-11-13. Implementation is a later GSD task.

Issue: https://github.com/jacob-consulting/django-crud-views/issues/360

## Problem / motivation

In the roastery, each order-line row selects a product. Grind and bag size apply only to coffee.
The selected product is a changing database record; its conditional category is a separate, configured
dimension. Comparing the product PK against a fixed list of matching values does not express this contract.

Origin: [finding 20 in tabler-test](https://github.com/alexander-jacob/tabler-test/blob/main/docs/crud_views_upstream_findings_roastery.md#20-formsets-have-no-per-row-conditional-fields).
The workaround lives in `example/sales/forms.py` (`ProductSelect`, `OrderLineForm`, `ORDER_FORMSETS`),
`example/sales/static/sales/sales.js`, and `example/sales/models.py` (`OrderLine.save()`).

Current upstream already prefixes `ToggleGroup` controller names and initializes toggles on
`cv:formset:row-added`. The missing contract is larger than another row event listener:
`ValueToggle` excludes model-choice controllers, and compact formsets generate their own field layout.
This extends the work from [#354](https://github.com/jacob-consulting/django-crud-views/issues/354)
without broadening or changing its existing static-choice API implicitly.

## Proposed solution

Add opt-in queryset-driven conditional field groups usable on both base forms and individual inline rows.
Keep Django's `ModelChoiceField` and its authoritative allowed queryset. Each selectable object supplies:

1. Its normal model-choice key, usually its PK.
2. Its normal model-choice display label.
3. A declared attribute or queryset annotation providing its conditional key.

Configuration maps conditional keys to field groups. Several selectable objects may share one conditional
key. A known key may explicitly activate no fields. The application owns category derivation; upstream owns
matching, browser metadata, row targeting, validation and inactive-field clearing.

### Illustrative configuration

Names below are design sketches, not existing APIs or a requirement to introduce exactly these classes.
Preserve the chosen model-choice/conditional-key/mapping contract while fitting the existing conditional API.

```python
SERVICE_CASES = {
    "on_site": ConditionalCase(fields=["visit_address"], required=["visit_address"]),
    "remote": ConditionalCase(fields=["meeting_url"], required=["meeting_url"]),
    "general": ConditionalCase(fields=[]),
}


class RequestForm(ConditionalGroupModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.annotate(conditional_category=F("category__code")),
    )

    cv_conditional_choices = [
        QuerysetConditions(
            controller="service",
            conditional_key="conditional_category",
            cases=SERVICE_CASES,
            allow_unmatched=False,  # The default; explicit here for illustration.
        ),
    ]

    class Meta:
        model = ServiceRequest
        fields = ["service", "visit_address", "meeting_url"]
```

`Service` and `ServiceRequest` are example-owned models. A direct attribute such as `category_id` needs no
annotation. The usual `label_from_instance` / model label remains available. Conditional category keys may
be dimension PKs or stable codes; they must not be inferred from human-facing option labels.

### Matching and validation

Strict matching is the default. When rendering, validate the conditional keys of every option actually
offered by this field. An unmatched key must produce a clear configuration failure identifying the
controller and key. On submission, resolve the selection through the authoritative `ModelChoiceField`
queryset, derive its current conditional key on the server, and reject unmatched selections with a form
error and no save. Never trust a client-submitted category or use raw invalid PKs to choose a group.

`allow_unmatched=True` explicitly permits unknown keys; no conditional groups for that controller activate,
and all its inactive editable fields receive the normal clearing behavior. Other controllers are unaffected.

Only offered options and the submitted selection are checked. Do not register or scan the entire category
dimension. A newly created category with no selectable products causes no failure. Likewise, configuration
may contain a known category that currently has no selectable products.

Both checks matter: the option/category assignment may change after GET, and a POST may bypass the browser.
Rendering and validation failures must be diagnosable; avoid masking a useful rejected-POST error with a
second, unhandled rendering failure. The exact integration and error presentation are planning details.

### Presentation and persistence

| Context | Inactive presentation |
| --- | --- |
| Base form | Hide its conditional field groups and disable their controls |
| Ordinary inline layout | Hide the row's conditional field groups and disable their controls |
| Compact inline layout | Keep cells and columns visible and aligned; disable the affected controls |

Use these layout-dependent defaults without adding a presentation setting in the initial scope. Each inline
row follows its own controller; changing one row must not affect another row or the parent form.

Switching away and back before submission preserves unsaved browser values. On a successful save, inactive
editable values are cleared server-side. Saving does not retain a hidden history for later restoration.
Active required fields remain enforced. Reuse existing clearing inference, explicit `empty_values` overrides,
trusted server-disabled field behavior, model validation and persistence safeguards.

### Deliverables

1. Upstream implementation, checks, tests, and changelog.
2. Migration of the roastery in the separate `tabler-test` repository, including downstream verification.
3. A dedicated upstream example app and documentation with working links in both directions.

The issue is not complete when only the upstream library is shipped.

### Focused example app

Create one separate Django app in `examples/bootstrap5/`, with its own models, forms, views, URLs, migrations,
seed data and tests. Do not extend the existing `conditional` or `formsets_conditional` apps or import their
domain code. Register a distinct feature/navigation entry.

The proposed teaching domain is service requests:

| Service | Conditional category | Required active field |
| --- | --- | --- |
| Boiler inspection | On-site | Visit address |
| Appliance installation | On-site | Visit address |
| Technical consultation | Remote | Meeting URL |
| Document review | General | None, explicitly configured |

Keep shared models and declarations small. Put the standalone editor in one module and inline forms/views
in another, with ordinary and compact variants. Demonstrate a standalone request and a batch of independent
request rows using the same conditional contract. Show only the modules relevant to the current demonstration
and its shared definitions in the code viewer: visitors must be able to connect the code to what they see.

The service domain and exact model names are the author's proposal, not separately selected API names.
Avoid unrelated business workflows. A correctly configured seeded example should support switching,
adding rows, saving and reopening. Cover strict failure and permissive behavior in tests and a documentation
recipe; do not leave the normal live demo deliberately broken.

Documentation must explain the three values, attribute/annotation configuration, strict default, explicit
empty cases, permissive opt-in, validation timing, browser preservation versus server clearing, layout
differences, supported controller bounds and query costs. Link to the runnable example and relevant source;
the example must link back to specific documentation sections using the established `Feature` / `DocRef`
conventions. Update the existing statement excluding relation-backed/per-row conditions without implying
that static `ValueToggle` now supports arbitrary querysets.

### tabler-test migration

Use the product field's existing restricted queryset, including the selected retired product where currently
allowed. Supply an explicit conditional-key attribute or annotation derived by the application from the
product category/type, and configure coffee plus the known no-fields categories. Keep the field's normal
model-choice labels and selection validation.

Replace the coffee-specific `ProductSelect` option marking, row-toggle attributes and conditional portion of
`sales.js` with upstream support. Preserve the unrelated packing-slip print handler. Replace duplicate
form-level clearing with the upstream declaration. Retain `OrderLine.save()`'s domain safeguard for writes
outside forms. Preserve compact columns and allow coffee values to survive switching away/back before save,
which intentionally differs from the old immediate-clearing script.

Keep existing coffee fields optional: introducing required grind/bag size is not a requested business change.
Account for an existing subscription or other retained product explicitly under the application's categories;
do not use permissive matching merely to conceal missing configuration. Update finding 20 with issue/PR
references and adoption status only when the corresponding work is actually verified.

## Approaches considered

- **ModelChoiceField plus a conditional-key attribute/annotation — selected by the maintainer.** Preserves
  Django's key/label/selection pipeline and queryset restrictions. Adds an explicit category mapping.
- **Explicit `(key, label, conditional_key)` projections — not selected.** Makes the three columns visible,
  but creates another representation whose keys and selected category must remain aligned with model-choice
  validation and persistence.
- **Arbitrary product predicate — superseded during discussion.** A boolean predicate does not express the
  category dimension or coverage checking when new categories enter the offered options.
- **Keep custom option attributes and a separate server rule — not selected.** Smaller library change but
  retains duplicate application plumbing and does not provide the chosen shared contract.

## gsd-handover

### Approved decisions

Carry these discussion decisions into GSD planning without reopening them absent a concrete conflict.

- **D-01 — Three-value contract:** dynamic options have a selectable key, display label and conditional key.
  Configuration matches the conditional dimension, not a hard-coded list of volatile product PKs.
- **D-02 — Model-choice approach:** use Django's `ModelChoiceField` and the normal queryset/key/label behavior;
  declare an attribute or annotation for the conditional key. The demonstrated API class names are provisional.
- **D-03 — Shared feature:** support this contract on base forms and individual inline rows, not just the roastery.
- **D-04 — Strict by default:** offered keys must have configuration; a known category may explicitly activate
  nothing. An explicit permissive option allows unknown keys and activates no groups for that controller.
- **D-05 — Check both stages:** check offered options when rendering and the validated selection on submission.
  Reject unmatched selections without saving; browser metadata is not server authority.
- **D-06 — Bounded coverage:** do not check unused categories absent from the selectable options or introduce a
  separate category-source scan. A new, unused dimension value does not fail the form.
- **D-07 — Layout-based presentation:** inactive groups hide on base forms and ordinary inlines; compact cells
  remain visible with disabled controls. No new presentation setting in the initial scope.
- **D-08 — Preserve until save:** retain unsaved browser values when switching away/back; clear inactive values
  on successful save. Apply this consistently to base forms and inlines, including the roastery migration.
- **D-09 — Downstream upgrade included:** this issue includes upgrading and verifying `tabler-test`, not merely
  shipping an API for a future downstream task.
- **D-10 — Separate focused example app:** one dedicated Django app with its own models; do not mix this feature
  into an existing example app. Keep unrelated features out of its visible source.
- **D-11 — Both contexts in that app:** shared small models/configuration, separate standalone and inline modules,
  ordinary/compact inline variants, and relevant source modules per demonstration in the code viewer.
- **D-12 — Cross-linked documentation:** include documentation and the runnable example, linked in both directions.
- **D-13 — Handoff destination:** the discussion deliverable is a GitHub issue containing these decisions in a
  `gsd-handover` section. Filing it does not implement the feature, create a phase or create a worktree.

### Design defaults and planning discretion

These author-proposed defaults were accepted in the full design approval. They support the individually
discussed decisions above; details explicitly left to the builder remain implementation choices.

- Start with model-choice controllers rendered as ordinary native single-selects. Existing static checkbox,
  select and radio controllers retain their supported behavior. AJAX/autocomplete controllers, dynamic radio
  controllers, multiselects, arbitrary widget adapters and a predicate/expression engine are outside this addition.
- A blank selector placeholder means no selection and activates nothing; the field's own required/invalid-choice
  validation still applies. An actual object with a missing/empty category is unmatched, not a placeholder.
- Preserve the usual model-choice key behavior, including supported `to_field_name` restrictions. Specify
  deterministic matching/serialization for supported conditional codes and PKs; reject ambiguous configurations.
  Choose the bounded supported key types and document them rather than inventing coercion heuristics.
- Reuse existing group semantics and clearing, including explicit empty values and server-disabled precedence.
  Detect conflicting ownership of fields/controllers rather than depending on declaration order. A shared group
  that stays active must retain its values; do not clear it merely because another category is inactive.
- The integration must be opt-in. Preserve existing static-choice and checkbox paths and the current
  whole-`ConditionalFormSet` contract. New queryset-driven whole-formset toggles are not included.
- Keep metadata/schema inspection query-free. Perform data-dependent coverage checking when options are actually
  rendered and selected objects validated, not at import, system-check startup or compact schema construction.
  Use an annotation/direct attribute to avoid per-option category queries; test query behavior and document any
  application-owned label/category access costs. No cross-request caches or background category registry.
- Use existing form ownership, exact prefixed names, row-added events, reset and modal initialization. Preserve
  independently disabled controls and management/identity/deletion fields. Do not add a document-wide observer
  as a substitute for the existing row lifecycle.
- Respect Django's empty-extra and deleted-inline handling. Keep row independence, existing atomic save behavior
  and conditional clearing for existing rows whose persisted data needs changing even when submitted fields
  otherwise look unchanged. No new concurrency/locking guarantees are requested.
- Make any page-specific source selection a small examples-only enhancement with explicit relevant files. Avoid
  a package-wide source-browser framework; preserve existing example source panels by default.
- Final public names, descriptor/layout integration, error classes and safe invalid-POST redisplay mechanics,
  metadata encoding, check IDs and exact example models are builder choices within the contract above.
- Expected release treatment is additive. Update `CHANGELOG.md`; if a breaking entry is needed, update
  `docs/migrating-1.0.md` under repository policy and explain the concrete reason.

### Acceptance criteria

- [ ] Base form, ordinary inline and compact inline all use the same queryset/category mapping contract.
  Multiple options sharing a category activate the same fields; configured no-fields categories work.
- [ ] Strict rendering detects any offered unmatched option; strict POST detects an unmatched validated selection
  even without a preceding GET. Both are diagnosable and prevent the affected operation from silently succeeding.
- [ ] Test category changes between render and submit, allowed-queryset restrictions, forged/stale selections,
  explicit permissive behavior, unused categories and configured categories with no currently offered objects.
- [ ] Blank placeholders, required controllers, invalid values and trusted server-disabled controllers behave
  consistently. Invalid controllers never lead to successful saves through raw-data/category fallback.
- [ ] Active required fields validate; inactive editable fields clear using existing inference/explicit overrides,
  including submitted invalid inactive values. Model constraints and server-disabled controlled fields are preserved.
- [ ] Each row responds only to its own controller on initial create/edit, changes, invalid redisplay, reset and
  dynamic insertion. Verify supported modal initialization and exact prefixed names.
- [ ] Ordinary groups hide; compact cells stay aligned and disabled. Preserve accessible labels, errors and
  independently disabled states. Management and identity/control fields remain functional.
- [ ] Browser values survive switching away/back before save. Save/reopen proves inactive values really cleared,
  including an existing row that needs conditional cleanup. No-JavaScript and tampered POSTs cannot bypass clearing.
- [ ] Empty extra rows and deletion follow existing formset semantics. An invalid retained row prevents partial
  parent/sibling saves. Existing checkbox/static-choice and whole-formset behavior retain regression coverage.
- [ ] Demonstrate bounded query behavior: no choice evaluation during schema/startup checks, no category N+1 for
  an annotation-based controller, and no scan of categories absent from the field's options.
- [ ] The new example app owns its models and demonstrates standalone, ordinary inline and compact inline use.
  Seed at least two selectable objects sharing a category, a different active category and an explicit no-fields one.
- [ ] Example navigation, explanatory text and page-relevant source panels work. The documentation and runnable
  example link to each other at valid destinations/anchors; strict/permissive reproduction is documented and tested.
- [ ] `tabler-test` adopts the API, removes superseded form/widget/JavaScript plumbing, preserves the print handler
  and model safeguard, and verifies coffee/non-coffee, retained products, row insertion, switching and persistence.
  Record downstream verification and update finding 20 accurately.
- [ ] Run meaningful Python, template and JavaScript/browser checks, example/docs checks and appropriate lint.
  Use multicore pytest for broad runs per repository instructions. Record both repositories' verification evidence.

### Implementation starting points

- `src/crud_views/lib/conditional/{toggle,group,layout,__init__}.py` and the conditional templates.
- `src/crud_views/lib/formsets/{compact,render_tree,formsets}.py` and `src/crud_views/checks.py`.
- `src/crud_views/static/crud_views/js/{toggle,formset}.js` and existing conditional/formset tests.
- A new app under `examples/bootstrap5/`; `project/features.py`, `project/templatetags/example_tags.py`,
  settings/URL/seed integration and existing example tests.
- `docs/reference/conditional.md`, `docs/reference/formsets.md` and the new focused example documentation.
- `tabler-test/example/sales/{forms,models}.py`, `static/sales/sales.js`, sales tests and the findings document.

### Handoff status

Approved and ready for GSD planning. Keep implementation bounded and explainable under the
project's developer-maintainability rule. Do not treat passing broader tests as justification for a general rule
engine, new shared state, unrelated refactoring or unsupported widget families.

## Affected area

`crud_views` core conditional fields and formsets; upstream examples/documentation; downstream `tabler-test`.
