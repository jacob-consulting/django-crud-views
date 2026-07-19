"""Registry of example feature apps. Each app task appends exactly one entry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    app: str  # python package name of the example app, e.g. "library"
    title: str  # card/nav title on the home page
    description: str  # one-liner on the home page card
    about: str  # 2-4 sentence teaching paragraph shown on every page of the app
    look_at: str  # one-sentence code pointer shown next to "The code behind this page"
    url_name: str  # URL name of the app's landing page, e.g. "author-list"
    icon: str  # font-awesome classes
    badge: str = ""  # optional small badge shown next to the title on the home page card


FEATURES: list[Feature] = [
    # example feature apps append their entry here
    Feature(
        app="library",
        title="Library",
        description="Plain CRUD — list, detail, create, update, delete — plus tables, filters and ordering.",
        about=(
            "The starting point: a plain CRUD interface built from a ViewSet. Authors and books each get a "
            "list, detail, create, update and delete view that link to one another and respect Django's "
            "permissions. The author list adds a django-tables2 table with a django-filter search box; books "
            "show manual up/down ordering."
        ),
        look_at=(
            "the cv_author and cv_book ViewSets and their List/Detail/Create/Update/Delete views; AuthorTable "
            "and AuthorFilter for the table and filter; BookUpView / BookDownView for ordering."
        ),
        url_name="author-list",
        icon="fa-solid fa-book",
    ),
    Feature(
        app="nested",
        title="Nested",
        description="Parent/child ViewSets with nested URLs: Company → Department → Employee, plus Offices.",
        about=(
            "ViewSets that nest inside a parent. A Company owns Departments, a Department owns Employees, and "
            "a Company also owns Offices. Each child list is automatically scoped to its parent, and creating "
            "a child fills in the parent link for you — notice how the URLs stack the parent keys "
            "(company → department → employee)."
        ),
        look_at=(
            "parent=ParentViewSet(...) on the cv_department / cv_employee / cv_office ViewSets, and "
            "CreateViewParentMixin in the create views (it sets the parent foreign key); the stacked "
            "company_pk / department_pk URL kwargs."
        ),
        url_name="company-list",
        icon="fa-solid fa-sitemap",
    ),
    Feature(
        app="formsets",
        title="Formsets",
        description="Inline formsets: edit a questionnaire with its questions and choices on one page.",
        about=(
            "Editing a record together with its children on one page. A Questionnaire is edited alongside its "
            "Questions, and each Question alongside its Choices, using Django inline formsets wired through "
            "crud_views' supported FormSetMixin. Add and remove rows without leaving the form."
        ),
        look_at=(
            "the QuestionInlineFormSet / ChoiceInlineFormSet definitions and the cv_formsets = FormSets(...) "
            "tree in views.py, plus FormSetMixin on QuestionnaireCreateView / QuestionnaireUpdateView."
        ),
        url_name="questionnaire-list",
        icon="fa-solid fa-list-check",
    ),
    Feature(
        app="workflow",
        title="Workflow",
        description="django-fsm state machine: transitions as form actions, with audit history.",
        about=(
            "A state machine driving the UI. A Campaign moves through draft → active → complete (or "
            "cancelled) using django-fsm transitions, which crud_views renders as action buttons — only the "
            "transitions valid from the current state appear. Every transition is recorded as audit history."
        ),
        look_at=(
            "the FSMField state and the @transition-decorated wf_activate / wf_complete / wf_cancel methods "
            "on Campaign in models.py; WorkflowModelMixin for the audit trail; CampaignWorkflowView in "
            "views.py."
        ),
        url_name="campaign-list",
        icon="fa-solid fa-bullhorn",
    ),
    Feature(
        app="polymorphic_demo",
        title="Polymorphic",
        description="One list over Car, Truck and Motorcycle with type-specific create and update forms.",
        about=(
            "One ViewSet over several concrete model types. Vehicle is a django-polymorphic base; Car, Truck "
            "and Motorcycle each add their own fields. The list shows all three together, and 'Add' first "
            "asks which type you want, then shows that type's own form."
        ),
        look_at=(
            "the create-select flow — VehicleCreateSelectView (pick a type) → VehicleCreateView — and the "
            "polymorphic_forms mapping (POLYMORPHIC_FORMS = {Car: CarForm, Truck: TruckForm, "
            "Motorcycle: MotorcycleForm}) in views.py."
        ),
        url_name="vehicle-list",
        icon="fa-solid fa-car",
    ),
    Feature(
        app="guardian_demo",
        title="Guardian",
        description="Per-object permissions: alice and bob each see their own documents; one is shared.",
        about=(
            "Per-object permissions with django-guardian. Documents are owned by individual users: sign in as "
            "alice or bob (password same as the username) and each sees only their own documents, except one "
            "that is explicitly shared. Creating a document grants its creator full object-level rights."
        ),
        look_at=(
            "the GuardianViewSet and the Guardian*ViewPermissionRequired views, and "
            "DocumentCreateView.cv_form_valid, which assigns object permissions to the creator via "
            "cv_document.assign_perm."
        ),
        url_name="document-list",
        icon="fa-solid fa-user-lock",
    ),
    Feature(
        app="resources",
        title="Resources",
        description="A ViewSet over non-ORM data: a fake S3 bucket listing with delete and touch actions.",
        about=(
            "A ViewSet over data that isn't in the database at all. Here the 'records' are entries in a fake "
            "S3 bucket held in memory, exposed through crud_views' Resource abstraction — the same list, "
            "detail and action UI, with no model or queryset behind it. Useful for external APIs, config "
            "trees or object stores."
        ),
        look_at=(
            "the S3File(Resource) class and its cv_get_items() reading FAKE_BUCKET in views.py; "
            "ResourceViewMixin on the views; and the delete and touch actions."
        ),
        url_name="s3file-list",
        icon="fa-solid fa-cloud",
    ),
    Feature(
        app="showcase",
        title="Showcase",
        description="Presentation extras: card list, detail fieldsets, modal delete, custom actions.",
        about=(
            "Presentation building blocks gathered in one place. Recipes are shown as a grid of cards instead "
            "of a table, the detail page groups fields into labelled fieldsets, deletion happens in a modal, "
            "and a custom 'favorite' action toggles a flag straight from the list. Mix these into your own "
            "views as needed."
        ),
        look_at=(
            "RecipeCardListView (the card grid), the cv_property_display fieldset groups on RecipeDetailView, "
            "cv_modal on RecipeDeleteView, and the RecipeFavoriteView custom action in views.py."
        ),
        url_name="recipe-card",
        icon="fa-solid fa-wand-magic-sparkles",
    ),
    Feature(
        app="object_detail",
        title="Object Detail",
        description="Seven detail-page layout themes, side by side, over the same product data.",
        about=(
            "django-object-detail's fieldset-based detail pages, integrated as crud_views_object_detail. A "
            "Product's detail page is rendered once per layout pack — split-card, accordion, tabs-vertical, "
            "card-rows, list-group-3col, striped-rows, table-inline — using a per-view "
            "cv_object_detail_layout override, alongside badges, links, a custom star-rating template, FK "
            "and O2O traversal, M2M fan-out, a model method and a view-computed property."
        ),
        look_at=(
            "PRODUCT_DISPLAY and the _make_detail_view() factory (cv_object_detail_layout=theme) in "
            "views.py; the ThemeLinksColumn on ProductTable links to all 7 detail pages from the list."
        ),
        url_name="product-list",
        icon="fa-regular fa-box",
    ),
    Feature(
        app="conditional",
        title="Conditional",
        badge="NEW",
        description="A checkbox toggle reveals a field-group or an entire formset, enforced server-side.",
        about=(
            "Two ways a checkbox can govern what's on the form. Registration reveals a fieldset of company "
            "billing details only when 'I represent a company' is ticked, validated and cleared server-side "
            "regardless of JavaScript; a second, transient 'Add a note' checkbox (UIFieldToggle — not a model "
            "field) reveals an optional note. Event gates two formsets: Sessions with on_off='purge', which "
            "deletes existing rows when untoggled, and Speakers with on_off='skip' (the safe default), which "
            "merely hides them and leaves the rows untouched."
        ),
        look_at=(
            "RegistrationForm.cv_conditional_groups (ModelFieldToggle + UIFieldToggle) and its "
            "ToggleGroup(..., legend=...) layout; cv_event_formsets' two ConditionalFormSet declarations "
            "contrasting on_off='purge' vs on_off='skip'."
        ),
        url_name="registration-list",
        icon="fa-solid fa-toggle-on",
    ),
]
