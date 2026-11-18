# Object navbar example for #381

Date: 2026-11-18
Status: discussion decisions and authorization approach approved; written design awaiting review.
Scope: the example portion of [issue #381](https://github.com/jacob-consulting/django-crud-views/issues/381).

## Intent

Provide one small example app that teaches the new object navbar and its interaction with authorization.
A developer should be able to follow the models, navbar declaration, view attachment and permissions in one app.
The domain is Tenant → Customer → (Order → Item, Address).

This supplements the object-navbar design in `2026-11-17-object-navbar-design.md`. The live issue contains
subsequent approved changes to the navbar contract and remains the reference for those changes. This document
settles the example choice in A-06: create a dedicated app rather than extending `nested`.
It does not authorize navbar implementation, phase creation or roadmap scheduling.

## Approved decisions

- Create one new app in the existing Bootstrap 5 example project, primarily for the new feature.
- The app owns its models, views, navbar, seed data and tests. No imports from, relationships to, or scenario
  links into other example apps. Do not add the navbar to an already complex example.
- Shared project login, base styling, feature index and other existing project infrastructure are suitable.
- Seed two tenants. Alice is the key account manager for Tenant A; Bob is the manager for Tenant B.
  Each has full CRUD access within their own tenant and no access to the other tenant.
- Charlie belongs to Tenant A. He can read customers, orders and items, but cannot access addresses or write.
- Customer owns the navbar, with four entries: Details, a second detail page, Orders and Addresses.
- The customer identity and links remain stable down to Item pages, where Orders is active.
- Hide inaccessible entries, retain accessible empty collections, and enforce permissions on direct requests.
- Use Guardian object permissions on Tenant and ordinary Django model permissions on the models below it.

## Approaches considered

### App structure

A dedicated app was selected explicitly. Extending `nested` or sharing its models would obscure the feature
and contradict the requested self-contained scenario. A separate Django project adds setup and infrastructure
duplication without helping this demonstration; the existing example project supplies the shell.

### Authorization

1. **Guardian on Tenant; model permissions below it — selected and approved.** Tenant grants determine which
   tenant a user can enter. Model grants determine which operations and sections are available within it.
   Existing ancestor checks combine these decisions for every descendant request. New business records need
   no per-object permission assignment.
2. **Guardian at every level — not selected.** Supports sharing individual records, but requires grants and
   grant lifecycle code for customers, orders, items and addresses. Individual-record sharing is not needed
   for this example.

## Scenario and navigation

```text
Tenant A (Alice; Charlie has restricted read access)
└── Customer
    ├── Order
    │   └── Item
    └── Address

Tenant B (Bob)
└── Customer
    ├── Order
    │   └── Item
    └── Address
```

Use one declared Customer navbar and one small project mixin pairing it with `CrudViewNavBarMixin`.
Attach that mixin explicitly to the participating Customer object views and the Order, Item and Address views.
On either Customer detail page, its own entry is active. On Order and Item pages, Orders is active.
On Address pages, Addresses is active. Other owner views follow #381's active-item contract.
Do not attach a customer navbar to Tenant pages or a Customer list/create page, which has no customer object.

Use the issue's default presentation: customer identity above the section entries, followed by the ordinary
view header and CRUD actions. Keep writes in the normal actions; no fifth Update entry is required for this
example. Existing package tests can demonstrate owner Update destinations and other navbar variants.

Every navbar URL preserves the Tenant and Customer context. An Item page must not accidentally use its own
or its Order's primary key as the customer key. Navigation into Orders and Addresses uses child collection
views; deeper links within Orders lead to Items through ordinary list/detail navigation.

The default template placement may be integrated into the shared project shell, as contemplated by #381.
Only the new app's participating views opt in. This does not enable a navbar on other example apps.

## Authorization and data boundaries

| Actor | Tenant object access | Customer / Order / Item | Address |
|---|---|---|---|
| Alice | Tenant A | Full CRUD within A | Full CRUD within A |
| Bob | Tenant B | Full CRUD within B | Full CRUD within B |
| Charlie | View Tenant A | Read within A | No access |

Use a `GuardianViewSet` for Tenant with strict object permissions, and core `ViewSet` classes with their
permission-required views for Customer, Order, Item and Address. Grant Alice and Bob the Tenant permissions
needed for their own tenant and all four ordinary model permissions on the business models. Give Charlie
only Tenant A's object view permission and the three business models' view permissions. No Address grants.
The three scenario accounts are ordinary users, not superusers.

Keep ancestor permission cascading enabled at every descendant depth. Core descendant permissions are
global by model; tenant isolation therefore depends on every business endpoint remaining nested and checking
the Tenant ancestor. Do not add alternative unscoped endpoints or bypass ancestor checks in custom views.
Use the existing Guardian filtering for the Tenant entry list so users see only their accessible tenant.

Use the existing parent-scoped querysets and create-parent mixins. Parent foreign keys are supplied from
the authorized URL context, not editable fields. Attempts to substitute a different Tenant, Customer or Order
in a URL, or to tamper with a submitted parent, must not expose or reassign another tenant's records.

Charlie sees both Customer detail entries and Orders; Addresses is absent. Write actions are absent and both
write-form GETs and write POSTs are denied. Alice sees Addresses on the same customer. Bob cannot enter it.
An accessible Orders collection remains a visible navbar entry even when it contains no orders.

The navbar itself does not recheck every ancestor: #381's child-link hook checks the destination and its
immediate parent. The current page and the destination request enforce their own ancestor policies. This
example uses consistent policies, so it must not claim that the navbar guarantees arbitrary higher-ancestor
policy parity. Do not introduce custom permission code into the navbar to strengthen that contract.

## Small implementation choices proposed by the assistant

These choices fill in presentation and integration details; they are not additional user requirements.

- Name the app `object_navbar` and give its ViewSets distinct names such as `navbar_customer` to avoid the
  registry collisions that generic `customer` and `order` names could introduce in the shared project.
- Keep Tenant as seeded context with list/detail entry navigation. Full business CRUD means Customer, Order,
  Item and Address; tenant provisioning and deletion are outside this feature demonstration.
- Label the second Customer detail page **Notes**, using a simple text field on Customer and a separate view
  key such as `detail2`. It is another view of the same object, with the same view permission, not another model.
- Keep fields minimal: names, an order reference, item description/quantity, and a short address. Avoid totals,
  catalog models, fulfillment states and business rules unrelated to navigation or permissions.
- Seed enough customers to switch context, populated orders/items and addresses in each tenant, plus an empty
  Orders collection in Tenant A so Alice and Charlie can both verify that it remains navigable.
- Reuse shared Alice/Bob accounts without changing their permissions in other apps. Add Charlie to the shared
  demo-user setup and credential hints, with grants limited to this app. Keep scenario data and grants in this
  app's seed module, following the project's idempotent seeding convention.
- Preserve the existing separate `developer` diagnostics account: explicitly add the new models to its read
  allowlist and grant view on both seeded tenants, following the project's object-grant conflict checks.
  It remains a project support account, separate from the three scenario users, with no write grants.

Exact fixture names, field lengths, icons and basic form/table arrangements are left to the builder.

## Integration and teaching material

Register the app in project settings, URLs and the feature index under UI. The landing page is its Tenant
entry list. Supply the usual about paragraph and source pointers explaining the one navbar declaration,
attachment mixin and two permission layers. Explain the Alice/Bob/Charlie comparison and how to reach
the empty Orders collection using seeded names.

Link this example to the new navbar reference and provide the reciprocal live-example link. References to
package documentation are welcome; links to another example app are not needed to complete this scenario.
Shared project navigation may continue listing the other independent examples.

The implementation depends on #381's upstream navbar API. Consume that API directly; do not build a second
navbar implementation, hand-maintained URL-name map or permission framework inside the example.
Other #381 cases (custom destination keys, template variants, state-disabled destinations, missing mixins,
modal rendering and startup diagnostics) remain package tests/documentation responsibilities unless needed
for this scenario. The example is not required to exhibit every permutation of the feature.

## Acceptance and verification

1. Seed from a fresh migrated database and seed again without duplicate scenario records or broadened grants.
   Shared project user setup and developer-account checks continue working.
2. Alice and Bob can list, view, create, update and delete all four business model types within their tenant.
   Newly created records work immediately without individual Guardian grants.
3. Their Tenant lists exclude the other tenant. Direct requests at every business depth deny cross-tenant
   access. Mismatched parent paths and tampered POSTs do not change ownership or expose foreign records.
4. Charlie can read both Customer detail pages, Orders and Items in A; sees no Addresses entry or write actions;
   cannot access Address endpoints or perform any business writes; cannot enter B.
5. Both owner detail destinations use the same customer and mark their own entries active. Order and Item
   pages keep the Customer caption and Orders active; Address pages mark Addresses active.
6. Navbar links from Customer, Order and Item pages resolve to the same customer and retain the tenant key.
   Use distinct primary keys for the participating customer, order and item in these checks.
7. An accessible empty Orders collection stays visible and returns a successful empty page.
8. Browser verification covers the Alice/Charlie comparison, deep Item navigation and narrow-viewport wrapping.
   App tests cover actual HTTP access and writes as well as rendered links; hidden markup alone is insufficient.
9. The app has no imports or model relationships to other example apps. Existing example pages keep their
   behavior. Project discovery, seeding and documentation-link checks pass with the new entry.

During implementation, run focused app tests and the affected project integration checks, then the example
suite with bounded multicore pytest. Package-wide verification belongs to the encompassing #381 work.
This discussion deliverable changes documentation only; it does not claim the example has been built or tested.

## Non-goals and failure conditions

No permission editor, tenant onboarding, record sharing, checkout workflow, polymorphic models, bulk actions,
formsets or additional navbar features. Do not refactor unrelated examples to support this one.
An example that requires visiting another example, assigns grants to each new business record, or silently
relies on superuser access would fail the agreed teaching purpose even if its navbar looks correct.
