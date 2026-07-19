"""
Object Detail example app views.

Seven ObjectDetailView subclasses render the SAME Product with the SAME
PRODUCT_DISPLAY, one per crud_views_object_detail layout pack, using the per-view
``cv_object_detail_layout`` override (see src/crud_views_object_detail/lib/mixins.py)
so all 7 themes are reachable from one project even though the project-wide default
pack (CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT, settings.py) is fixed to
"split-card".

The views are built with a small type() factory (_make_detail_view) rather than 7
hand-written classes: CrudViewMetaClass registers a CrudView with its ViewSet purely
from the class's attrs (cv_key / cv_path / cv_viewset etc.) at class-creation time,
and type() invokes that same metaclass machinery as a `class` statement would — so
each dynamically-built view registers under its own distinct cv_key/cv_path and gets
its own urlpattern, verified by `python manage.py check` and by reversing all 7 URL
names in tests.py.

A minimal, detail-only ``cv_supplier`` ViewSet (``SupplierDetailView``) is also
registered here: it exists solely so the ``supplier`` property in PRODUCT_DISPLAY has
a real, correct ``link`` target (a Supplier's own detail page), rather than pointing at
an unrelated Product page.
"""

import django_tables2 as tables
from crispy_forms.layout import Fieldset, Row
from django.urls import reverse
from django.utils.html import format_html_join

from crud_views.lib.crispy import Column4, Column6, Column12, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import BadgeConfig, ObjectDetailViewPermissionRequired, x

from object_detail.models import Product, Supplier
from project.views import BreadcrumbMixin

cv_product = ViewSet(
    model=Product,
    name="product",
    icon_header="fa-regular fa-box",
)

cv_supplier = ViewSet(
    model=Supplier,
    name="supplier",
    icon_header="fa-regular fa-truck",
)

THEMES = [
    "split-card",
    "accordion",
    "tabs-vertical",
    "card-rows",
    "list-group-3col",
    "striped-rows",
    "table-inline",
]


def detail_cv_key(theme: str) -> str:
    # cv_key must satisfy the viewset.E200 naming check (lowercase alpha/digits/underscores
    # only, no dashes), so theme names like "split-card" become "detail_split_card" here.
    # cv_path keeps the dash-separated form for a nicer URL (see _make_detail_view).
    return f"detail_{theme.replace('-', '_')}"


def detail_url_name(theme: str) -> str:
    return f"product-{detail_cv_key(theme)}"


# --------------------------------------------------------------------------- form

_LAYOUT_FIELDS = [
    Fieldset("Basics", Row(Column6("name"), Column4("sku"), Column4("price"))),
    Fieldset("Stock & status", Row(Column4("stock"), Column4("weight_kg"), Column4("is_active"))),
    Fieldset("Links & dates", Row(Column6("homepage"), Column6("release_date"))),
    Fieldset("Relations", Row(Column4("supplier"), Column4("warehouse"), Column4("tags"))),
    Fieldset("Description", Row(Column12("description"))),
]


class ProductForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "description",
            "price",
            "weight_kg",
            "stock",
            "is_active",
            "homepage",
            "release_date",
            "supplier",
            "warehouse",
            "tags",
        ]

    def get_layout_fields(self):
        return _LAYOUT_FIELDS


# --------------------------------------------------------------------------- table


class ThemeLinksColumn(tables.Column):
    """Renders one small link per layout theme for the row's detail pages.

    There is no plain "detail" cv_key here (only detail-<theme> per THEMES), so this
    replaces the usual LinkDetailColumn as the way to reach a product's detail pages
    from the list.
    """

    def __init__(self, **extra):
        extra.setdefault("orderable", False)
        extra.setdefault("verbose_name", "Themes")
        extra.setdefault("empty_values", ())
        super().__init__(**extra)

    def render(self, record):
        return format_html_join(
            " ",
            '<a class="btn btn-sm btn-outline-secondary mb-1" href="{}">{}</a>',
            ((reverse(detail_url_name(theme), kwargs={"pk": record.pk}), theme) for theme in THEMES),
        )


class ProductTable(Table):
    name = tables.Column()
    sku = tables.Column()
    price = tables.Column()
    stock = tables.Column()
    supplier = tables.Column()
    themes = ThemeLinksColumn()


# --------------------------------------------------------------------------- list / create


class ProductListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_product
    table_class = ProductTable
    # no plain "detail"/"update"/"delete" keys are registered on this viewset
    # (only detail-<theme> and create) — the ThemeLinksColumn on the table covers
    # navigation to detail pages instead of the default row action buttons.
    cv_list_actions = []


class ProductCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_product
    form_class = ProductForm
    cv_message = "Created product »{object}«"


# --------------------------------------------------------------------------- supplier (minimal detail-only)

# Read-only detail page so the product's "supplier" property can `link` to the
# supplier's OWN detail page (see PRODUCT_DISPLAY below). No list/create/update/delete
# views are registered here — this ViewSet exists solely as a correct link target.


class SupplierDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_supplier
    cv_property_display = [
        {
            "title": "Supplier",
            "icon": "truck",
            "properties": [
                "name",
                "website",
                # plain BadgeConfig.color variant (distinct from color_map/color_fn above)
                x("rating", badge=BadgeConfig(color="info")),
            ],
        },
    ]


# --------------------------------------------------------------------------- detail (one per theme)

# shared property_display showing default rendering of many field types + traversal + methods
PRODUCT_DISPLAY = [
    {
        "title": "Basics",
        "icon": "box",
        "properties": [
            "name",
            "sku",
            "description",
            x("price"),
            x(
                "price",
                title="Price tier",
                badge=BadgeConfig(color_fn=lambda p: "success" if p >= 100 else "secondary"),
            ),
            x("weight_kg", title="Weight (kg)"),
            "stock",
            x(
                "is_active",
                badge=BadgeConfig(
                    color_map={True: "success", False: "secondary"},
                    label_map={True: "Active", False: "Inactive"},
                    pill=True,
                ),
            ),
            "homepage",
            "release_date",
            "created_at",
        ],
    },
    {
        "title": "Supplier (FK traversal)",
        "icon": "truck",
        "properties": [
            # value is a Supplier instance -> links to that supplier's OWN detail page
            # (default LinkConfig branch: reverse(url, kwargs={"pk": value.pk})).
            x("supplier", link="supplier-detail"),
            x("supplier__name", title="Supplier name"),
            x("supplier__website", title="Supplier website"),
            x("supplier__rating", title="Supplier rating"),
            x("supplier__rating", title="Supplier rating (stars)", template="object_detail/star_rating.html"),
        ],
    },
    {
        "title": "Warehouse (O2O traversal)",
        "icon": "warehouse",
        "properties": [
            x("warehouse__code", title="Warehouse code"),
            x("warehouse__city", title="City"),
            x("warehouse__country", title="Country"),
        ],
    },
    {
        "title": "Tags (M2M) & computed",
        "icon": "tags",
        "properties": [
            "tags",
            x("margin_label", title="Margin"),
            x("stock_status", title="Stock status"),
            x("view_summary", title="Summary (view-computed)"),
        ],
    },
]


def _make_detail_view(theme: str):
    attrs = {
        "cv_viewset": cv_product,
        "cv_key": detail_cv_key(theme),
        "cv_path": f"detail-{theme}",
        "cv_object_detail_layout": theme,
        "cv_property_display": PRODUCT_DISPLAY,
    }

    def view_summary(self, instance):
        return f"{instance.name} — {instance.stock_status()} ({instance.margin_label})"

    attrs["view_summary"] = view_summary
    class_name = f"Product{theme.title().replace('-', '')}DetailView"
    return type(class_name, (BreadcrumbMixin, ObjectDetailViewPermissionRequired), attrs)


PRODUCT_DETAIL_VIEWS = [_make_detail_view(theme) for theme in THEMES]
