"""Registry of example feature apps. Each app task appends exactly one entry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    app: str  # python package name of the example app, e.g. "library"
    title: str  # card/nav title on the home page
    description: str  # one-liner on the home page card
    url_name: str  # URL name of the app's landing page, e.g. "author-list"
    icon: str  # font-awesome classes


FEATURES: list[Feature] = [
    # example feature apps append their entry here
    Feature(
        app="library",
        title="Library",
        description="Plain CRUD — list, detail, create, update, delete — plus tables, filters and ordering.",
        url_name="author-list",
        icon="fa-solid fa-book",
    ),
    Feature(
        app="nested",
        title="Nested",
        description="Parent/child ViewSets with nested URLs: Company → Department → Employee, plus Offices.",
        url_name="company-list",
        icon="fa-solid fa-sitemap",
    ),
    Feature(
        app="formsets",
        title="Formsets",
        description="Inline formsets: edit a questionnaire with its questions and choices on one page.",
        url_name="questionnaire-list",
        icon="fa-solid fa-list-check",
    ),
    Feature(
        app="workflow",
        title="Workflow",
        description="django-fsm state machine: transitions as form actions, with audit history.",
        url_name="campaign-list",
        icon="fa-solid fa-bullhorn",
    ),
    Feature(
        app="polymorphic_demo",
        title="Polymorphic",
        description="One list over Car, Truck and Motorcycle with type-specific create and update forms.",
        url_name="vehicle-list",
        icon="fa-solid fa-car",
    ),
    Feature(
        app="guardian_demo",
        title="Guardian",
        description="Per-object permissions: alice and bob each see their own documents; one is shared.",
        url_name="document-list",
        icon="fa-solid fa-user-lock",
    ),
]
