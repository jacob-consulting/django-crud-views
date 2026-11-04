"""Registry of example feature apps. Each app task appends exactly one entry."""

from dataclasses import dataclass

from django.utils.translation import pgettext_lazy

#: Read the Docs version linked from the demo. "stable" is the newest release tag, which is what the demo runs.
DOCS_BASE = "https://django-crud-views.readthedocs.io/en/stable"


@dataclass(frozen=True)
class DocRef:
    page: str  # path under docs/, e.g. "reference/nested.md"
    label: str  # English link text, deliberately not translated (like Feature.title / look_at)
    anchor: str = ""  # heading slug on that page, e.g. "creating-children"

    @property
    def url(self) -> str:
        """Read the Docs URL, following mkdocs' use_directory_urls: x/y.md -> x/y/, x/index.md -> x/."""
        path = self.page.removesuffix(".md")
        if path == "index" or path.endswith("/index"):
            path = path.removesuffix("index")
        else:
            path += "/"
        url = f"{DOCS_BASE}/{path}"
        return f"{url}#{self.anchor}" if self.anchor else url


@dataclass(frozen=True)
class FeatureGroup:
    key: str  # referenced by Feature.group
    title: str  # navbar dropdown and home page heading; page chrome, so translated (unlike Feature.title);
    # pgettext context "feature group" because e.g. "Basics" is also a fieldset title with another translation
    icon: str  # font-awesome classes


#: navbar dropdowns and home page sections, in display order
GROUPS: list[FeatureGroup] = [
    FeatureGroup(
        key="basics",
        title=pgettext_lazy("feature group", "Basics"),  # NOSONAR S1192 xgettext needs a literal msgctxt
        icon="fa-solid fa-cubes",
    ),
    FeatureGroup(key="forms", title=pgettext_lazy("feature group", "Forms"), icon="fa-solid fa-pen-to-square"),
    FeatureGroup(key="ui", title=pgettext_lazy("feature group", "UI"), icon="fa-solid fa-palette"),
    FeatureGroup(key="extensions", title=pgettext_lazy("feature group", "Extensions"), icon="fa-solid fa-puzzle-piece"),
]


@dataclass(frozen=True)
class Feature:
    app: str  # python package name of the example app, e.g. "library"
    group: str  # FeatureGroup.key this app is listed under in the navbar and on the home page
    title: str  # card/nav title; names a package feature as in the docs, so deliberately not translated
    description: str  # one-liner on the home page card (English, like about/look_at: they quote code)
    about: str  # 2-4 sentence teaching paragraph shown on every page of the app
    look_at: str  # one-sentence code pointer shown next to "The code behind this page"
    url_name: str  # URL name of the app's landing page, e.g. "author-list"
    icon: str  # font-awesome classes
    docs: tuple[DocRef, ...] = ()  # documentation sections listed under "References to documentation"


FEATURES: list[Feature] = [
    # example feature apps append their entry here
    Feature(
        app="library",
        group="basics",
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
            "and AuthorFilter for the table and filter; BookUpView / BookDownView for ordering; "
            "the automatic Cancel origin on AuthorUpdateView, which returns to the originating list or detail "
            "with captured query state; AuthorDeleteView demonstrates an explicit allowed-key list. "
            "cv_success_keys on AuthorUpdateView selects Save's destination without restoring Cancel query state."
        ),
        url_name="author-list",
        icon="fa-solid fa-book",
        docs=(
            DocRef(page="getting_started/index.md", label="Getting started — the tutorial builds this app"),
            DocRef(
                page="reference/list_view.md",
                label="ListView — table with django-tables2",
                anchor="table-with-django-tables2",
            ),
            DocRef(
                page="reference/list_view.md",
                label="ListView — filtering with django-filter",
                anchor="filtering-with-django-filter",
            ),
            DocRef(page="reference/ordered_view.md", label="OrderedView — manual up/down ordering"),
        ),
    ),
    Feature(
        app="card_view",
        group="basics",
        title="Card View",
        description="The Library authors as a card grid: signed ordering in one combo, paging and card actions.",
        about=(
            "The same authors as in Library, listed as cards instead of a table. A second ViewSet over the "
            "Author model uses CardListView, whose toolbar is a single ordering combo: the direction is part of "
            "each choice, so there are no ascending/descending buttons. Six cards per page, with detail, edit "
            "and delete actions on every card."
        ),
        look_at=(
            "AuthorCardListView in views.py: cv_order_fields with signed choices, cv_order_default, "
            "paginate_by and cv_card_actions; cv_author_card is a second ViewSet on library.models.Author."
        ),
        url_name="author_card-card",
        icon="fa-solid fa-table-cells-large",
        docs=(
            DocRef(page="reference/card-list-view.md", label="CardListView"),
            DocRef(
                page="reference/card-list-view.md",
                label="CardListView — signed ordering",
                anchor="signed-choices-single-combo-no-buttons",
            ),
        ),
    ),
    Feature(
        app="nested",
        group="basics",
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
        docs=(
            DocRef(page="reference/nested.md", label="Nested ViewSets (parent/child)"),
            DocRef(page="reference/nested.md", label="Nested ViewSets — creating children", anchor="creating-children"),
        ),
    ),
    Feature(
        app="formsets",
        group="forms",
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
        docs=(DocRef(page="reference/formsets.md", label="Formsets"),),
    ),
    Feature(
        app="workflow",
        group="extensions",
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
        docs=(
            DocRef(page="reference/workflow_view.md", label="WorkflowView"),
            DocRef(
                page="reference/workflow_view.md",
                label="WorkflowView — WorkflowModelMixin (audit history)",
                anchor="workflowmodelmixin",
            ),
        ),
    ),
    Feature(
        app="polymorphic_demo",
        group="extensions",
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
        docs=(
            DocRef(
                page="reference/polymorphic_view.md",
                label="PolymorphicView — two-step create flow",
                anchor="two-step-create-flow",
            ),
            DocRef(
                page="reference/polymorphic_view.md",
                label="PolymorphicView — polymorphic_forms",
                anchor="polymorphic_forms",
            ),
        ),
    ),
    Feature(
        app="guardian_demo",
        group="extensions",
        title="Guardian",
        description="Per-object permissions: alice and bob each see their own documents, plus shared ones.",
        about=(
            "Per-object permissions with django-guardian. Documents are owned by individual users: sign in as "
            "alice or bob (password same as the username) and each sees only their own documents, plus two that "
            "are shared — alice's Team Handbook with bob, view-only, and bob's Release Checklist with alice, "
            "editable but not deletable. Creating a document grants its creator full object-level rights."
        ),
        look_at=(
            "the GuardianViewSet and the Guardian*ViewPermissionRequired views, and "
            "DocumentCreateView.cv_form_valid, which assigns object permissions to the creator via "
            "cv_document.assign_perm."
        ),
        url_name="document-list",
        icon="fa-solid fa-user-lock",
        docs=(
            DocRef(page="reference/guardian.md", label="Per-object permissions (django-guardian)"),
            DocRef(
                page="reference/guardian.md",
                label="Guardian — working example and seeded permissions",
                anchor="working-example",
            ),
        ),
    ),
    Feature(
        app="resources",
        group="basics",
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
        docs=(DocRef(page="reference/resources.md", label="Resources — non-ORM data in ViewSets"),),
    ),
    Feature(
        app="object_detail",
        group="extensions",
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
        icon="fa-solid fa-box",
        docs=(
            DocRef(page="reference/object_detail_view.md", label="ObjectDetailView"),
            DocRef(page="reference/object_detail_layout_packs.md", label="Object detail — layout packs"),
            DocRef(page="reference/object_detail_badges.md", label="Object detail — badges"),
            DocRef(page="reference/object_detail_links.md", label="Object detail — links"),
        ),
    ),
    Feature(
        app="breadcrumbs",
        group="ui",
        title="Breadcrumbs",
        description="ViewSet-aware breadcrumbs, plus injecting a host application's navigation as prefix items.",
        about=(
            "Every page in these examples renders a breadcrumb via CrudViewBreadcrumbMixin and the "
            "cv_breadcrumb template tag: container › object › action, following the ViewSet parent chain. "
            "This app additionally simulates being embedded in a larger host application: "
            "HostNavBreadcrumbMixin overrides cv_breadcrumb_prefix() to inject a 'Host application' item "
            "after the global 'Home' prefix that CRUD_VIEWS_BREADCRUMB_PREFIX configures in settings.py."
        ),
        look_at=(
            "HostNavBreadcrumbMixin.cv_breadcrumb_prefix() in views.py (code-level injection), "
            "CRUD_VIEWS_BREADCRUMB_PREFIX in project/settings.py (setting-level prefix), and the "
            "{% cv_breadcrumb %} block in project/crud_views.html."
        ),
        url_name="workspace-list",
        icon="fa-solid fa-ellipsis",
        docs=(
            DocRef(page="reference/breadcrumb.md", label="Breadcrumb"),
            DocRef(
                page="reference/breadcrumb.md",
                label="Breadcrumb — hooking into your site navigation",
                anchor="hooking-into-your-site-navigation",
            ),
        ),
    ),
    Feature(
        app="conditional",
        group="forms",
        title="Conditional",
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
        docs=(
            DocRef(
                page="reference/conditional.md",
                label="Conditional field-groups",
                anchor="kind-1-conditional-field-group-in-a-form",
            ),
            DocRef(
                page="reference/conditional.md",
                label="Conditional formsets",
                anchor="kind-2-conditional-formset",
            ),
        ),
    ),
    Feature(
        app="formsets_conditional",
        group="forms",
        title="Formsets + Conditional",
        description="Nested formsets behind a toggle, plus a conditional field-group on the same form.",
        about=(
            "Formsets and conditional toggles on one form. A conference reveals its billing fields only when "
            "'Invoice a company' is ticked, and clears them on save when it is not. Its Sessions formset has a "
            "nested Speakers formset per session; 'This conference has sessions' gates the Sessions formset "
            "with on_off='purge', so untoggling deletes the sessions and, with them, their speakers. Only a "
            "first-level formset may be conditional: a ConditionalFormSet on the nested Speakers formset would "
            "fail system check crud_views.E310. Putting the toggle on the first level and letting the "
            "nested formset follow it is the supported way to combine the two."
        ),
        look_at=(
            "ConferenceForm.cv_conditional_groups (ModelFieldToggle) in views.py, and cv_conference_formsets: "
            "the ConditionalFormSet on sessions and the speakers FormSet under its children, which has none."
        ),
        url_name="conference-list",
        icon="fa-solid fa-people-group",
        docs=(
            DocRef(page="reference/formsets.md", label="Formsets"),
            DocRef(
                page="reference/conditional.md",
                label="Conditional formsets",
                anchor="kind-2-conditional-formset",
            ),
            DocRef(
                page="reference/conditional.md",
                label="Conditional formsets — scope constraint",
                anchor="scope-constraint",
            ),
        ),
    ),
    Feature(
        app="custom_form",
        group="forms",
        title="Custom Form View",
        description="A free-standing form that acts on one object, and one that needs no object at all.",
        about=(
            "Forms that are not create, update or delete. 'Remind' is an object-based custom form: it loads "
            "the contact from the URL, asks for a required note and, in cv_form_valid, stamps "
            "last_reminded_dt; MessageMixin flashes the success message. 'Invite' is a non-object custom form "
            "with no pk in its URL: it takes an email address and creates a new contact. Remind sits in the "
            "list's row actions, Invite in its context actions, because an object view cannot be linked "
            "without an object."
        ),
        look_at=(
            "ContactRemindView (CustomFormViewPermissionRequired) and ContactInviteView "
            "(CustomFormNoObjectViewPermissionRequired) in views.py: cv_key / cv_path register them, "
            "cv_form_valid does the work, and cv_list_actions vs cv_context_actions on ContactListView."
        ),
        url_name="contact-list",
        icon="fa-regular fa-address-book",
        docs=(
            DocRef(page="reference/custom_form_view.md", label="CustomFormView", anchor="basic-usage"),
            DocRef(page="reference/custom_form_view.md", label="Non-object view", anchor="non-object-view"),
        ),
    ),
    Feature(
        app="context_buttons",
        group="ui",
        title="Context Buttons",
        description="Whole-button templates and placing context buttons by hand with template tags.",
        about=(
            "Context buttons outside the standard toolbar. Two edit buttons bring their own markup — one "
            "inline via template_code, one from a template file — and the ticket detail page places buttons "
            "by hand: a custom toolbar, a tile built from just the URL, a section shown only to users who may "
            "delete, and a loop over the view's buttons. Log in as alice (may edit) and as bob (may only "
            "view): every button bob may not use disappears."
        ),
        look_at=(
            "the edit_big (template_code) and edit_pill (template=) ContextButtons on cv_ticket in views.py, "
            "and the four numbered sections of context_buttons/ticket_detail.html."
        ),
        url_name="ticket-list",
        icon="fa-solid fa-hand-pointer",
        docs=(
            DocRef(
                page="reference/context_buttons.md",
                label="Context Buttons — ContextButton",
                anchor="contextbutton",
            ),
            DocRef(
                page="reference/context_buttons.md",
                label="Context Buttons — manual placement (template tags)",
                anchor="manual-placement-template-tags",
            ),
        ),
    ),
    Feature(
        app="action_menus",
        group="ui",
        title="Action Menus",
        description="Fold the less common actions of list rows, the toolbar and cards into a ⋯ dropdown.",
        about=(
            "A chore has eight actions — too many buttons for every table row. The list keeps detail, up and "
            "down as buttons and folds the rest into a ⋯ menu; the toolbar and the cards do the same. Delete opens "
            "a modal; done / archive are POST actions in the list rows and cards (the toolbar only links). "
            "Log in as bob (may only view): archive stays visible but disabled, the other actions disappear."
        ),
        look_at=(
            "cv_list_actions_inline, cv_context_actions_inline and cv_card_actions_inline in views.py, and "
            "ChoreArchiveView.cv_inaccessible_actions; ChoreDoneView is the custom ActionView (a POST toggle)."
        ),
        url_name="chore-list",
        icon="fa-solid fa-ellipsis",
        docs=(
            DocRef(page="reference/action_view.md", label="ActionView — custom actions"),
            DocRef(page="reference/action_menus.md", label="Action menus — configuration", anchor="configuration"),
            DocRef(
                page="reference/action_menus.md", label="Action menus — hide and disable", anchor="hide-and-disable"
            ),
        ),
    ),
    Feature(
        app="label_modes",
        group="ui",
        title="Label Modes & Icons",
        description="The same actions as text only, icon and text, and icon only with a tooltip — side by side.",
        about=(
            "Every action button has one of three label modes. 'label' shows the short label as text, 'both' "
            "adds the action's icon, 'icon' shows the icon alone: its full label (\"Delete Gadget …\") stays in "
            'the page as visually hidden text for screen readers, and the short label ("Delete") becomes the '
            "hover tooltip. Labelled buttons get no tooltip, their visible text already names them. The list "
            "rows and the detail toolbar each show Detail/List as label, Update as both and Delete as icon."
        ),
        look_at=(
            "cv_list_actions_label_mode on GadgetListView and cv_context_actions_label_mode on GadgetDetailView "
            "in views.py; the icons are the package defaults (list, detail, update, delete), see the Icons reference."
        ),
        url_name="gadget-list",
        icon="fa-solid fa-tags",
        docs=(
            DocRef(page="reference/buttons.md", label="Buttons — variants", anchor="variants"),
            DocRef(page="reference/icons.md", label="Icons — default table", anchor="default-table"),
            DocRef(
                page="reference/settings.md",
                label="Settings — label-mode configuration",
                anchor="label-mode-configuration",
            ),
        ),
    ),
    Feature(
        app="flash_messages",
        group="ui",
        title="Messages",
        description="Queue a flash message at any level and see it rendered as a Bootstrap alert.",
        about=(
            "Pick a level and a text and send: the view queues it with messages.add_message and redirects back, "
            "where {% cv_messages %} in the base template renders it as a dismissible alert, coloured by level. "
            "Debug messages are queued too but never shown: Django's default MESSAGE_LEVEL is INFO, and this "
            "demo does not lower it. The blue box above the form is a single {% cv_alert %} drawn by the "
            "template itself, through the same alert frame."
        ),
        look_at=(
            "NoticeComposeView.cv_form_valid in views.py (a CustomFormNoObjectView) and the cv_alert tag in "
            "templates/flash_messages/compose.html; {% cv_messages %} sits in project/base.html."
        ),
        url_name="notice-compose",
        icon="fa-regular fa-comment-dots",
        docs=(
            DocRef(page="reference/messages.md", label="Flash messages — levels", anchor="levels"),
            DocRef(
                page="reference/messages.md",
                label="Flash messages — a single alert: cv_alert",
                anchor="a-single-alert-cv_alert",
            ),
        ),
    ),
    Feature(
        app="disabled_actions",
        group="ui",
        title="Disabled Actions",
        description="Disable an action by object state — and hide or grey it out, side by side.",
        about=(
            "A locked ticket can be neither edited nor deleted, although you have the permission: "
            "cv_action_enabled says no for its state. Update renders the action disabled (greyed out, "
            'data-cv-disabled="state"), delete hides it — the same gate, the two inaccessible-action modes. '
            "Opening the update or delete URL of a locked ticket directly answers 403. Lock / unlock is always "
            "enabled, so you can flip the state and watch both buttons change. For actions disabled by "
            "permission, see Action Menus."
        ),
        look_at=(
            "cv_action_enabled on TicketUpdateView and TicketDeleteView in views.py, and "
            'TicketUpdateView.cv_inaccessible_actions = "disable" next to the delete view\'s default "hide".'
        ),
        url_name="lockable_ticket-list",
        icon="fa-solid fa-lock",
        docs=(
            DocRef(
                page="reference/action_enabled.md",
                label="Disabling an action — signature",
                anchor="default-and-override-signature",
            ),
            DocRef(
                page="reference/inaccessible_actions.md",
                label="Hide or disable — configuration",
                anchor="configuration",
            ),
        ),
    ),
    Feature(
        app="delete_demo",
        group="basics",
        title="Delete",
        description="A delete page that previews the cascade and explains why a deletion is blocked.",
        about=(
            "What a delete page shows before anything is removed. alice has four projects: deleting Old "
            "prototype previews the two milestones that go with it. The other three are blocked: Website "
            "relaunch by her own tasks, listed by name; Office move is blocked by objects you cannot see (a "
            "task of bob's), so the page only says that other objects still reference it; and Annual report by "
            "a business rule, because it is shared. A blocked page shows no confirmation form, and the delete "
            "opens in a modal."
        ),
        look_at=(
            "ProjectDeleteView in views.py: cv_show_related_objects, cv_modal and cv_check_delete_protection; "
            "on_delete=CASCADE (Milestone) vs PROTECT (Task) in models.py; the Guardian grants in seed.py."
        ),
        url_name="project-list",
        icon="fa-solid fa-trash-can",
        docs=(
            DocRef(
                page="reference/delete_view.md",
                label="DeleteView — cascading deletes display",
                anchor="cascading-deletes-display",
            ),
            DocRef(
                page="reference/delete_view.md",
                label="DeleteView — permission filtering",
                anchor="permission-filtering",
            ),
            DocRef(page="reference/delete_view.md", label="DeleteView — protected objects", anchor="protected-objects"),
            DocRef(page="reference/delete_view.md", label="DeleteView — delete protection", anchor="delete-protection"),
            DocRef(
                page="reference/guardian.md",
                label="Guardian — cascading deletes with per-object permissions",
                anchor="cascading-deletes-with-per-object-permissions",
            ),
            DocRef(page="reference/modals.md", label="Modals"),
        ),
    ),
    Feature(
        app="theming",
        group="ui",
        title="Theme",
        description="Restyle every page by overriding templates, buttons and icons — with a second theme to try.",
        about=(
            "Everything you see is the bootstrap5 theme that ships with crud_views; a theme is just an app whose "
            "templates, button classes and icons win over the stock ones. This page has no CRUD of its own: it "
            "points to the reference pages and to the Tabler theme demo, the same views restyled by a theme app."
        ),
        look_at=(
            "ThemeIndexView in views.py: a plain TemplateView that supplies its own breadcrumb, "
            "and TABLER_DEMO_URL, the one constant that switches the placeholder to the demo link."
        ),
        url_name="theming-index",
        icon="fa-solid fa-swatchbook",
        docs=(
            DocRef(page="reference/theme.md", label="Custom themes", anchor="how-resolution-works"),
            DocRef(page="reference/templates.md", label="Base template", anchor="what-to-put-in-it"),
            DocRef(
                page="reference/buttons.md",
                label="Buttons — registering classes from a theme",
                anchor="registering-classes-from-a-theme",
            ),
            DocRef(
                page="reference/icons.md",
                label="Icons — registering icons from a theme",
                anchor="registering-icons-from-a-theme",
            ),
        ),
    ),
]


def feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]:
    """FEATURES bucketed by GROUPS: one (group, features) pair per group in GROUPS order, FEATURES order within.

    Raises ValueError for a feature naming an unknown group, so a typo fails loudly instead of hiding the app.
    """
    buckets: dict[str, list[Feature]] = {group.key: [] for group in GROUPS}
    for feature in FEATURES:
        if feature.group not in buckets:
            raise ValueError(f"Feature {feature.app!r} names unknown group {feature.group!r}")
        buckets[feature.group].append(feature)
    return [(group, buckets[group.key]) for group in GROUPS]


# validate the group keys at import time: project.views imports this module via the URLconf, so a typo
# fails runserver's startup checks instead of the first page view
feature_groups()
