import django_tables2 as tables
from django.forms import modelform_factory

from app.models import Poly, PolyOne, PolyTwo
from crud_views.lib.polymorphic_views import PolymorphicCreateSelectView, PolymorphicCreateViewPermissionRequired, \
    PolymorphicUpdateViewPermissionRequired, PolymorphicDetailViewPermissionRequired
from crud_views.lib.views import ListViewPermissionRequired
from crud_views.lib.polymorphic_views.delete import PolymorphicDeleteViewPermissionRequired
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewTableMixin
from crud_views.lib.viewset import ViewSet, path_regs

cv_poly = ViewSet(
    model=Poly,
    name="poly",
    pk=path_regs.UUID,
)


class PolyTable(Table):
    id = tables.Column()
    shared = tables.Column()


class PolyListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Poly
    table_class = PolyTable
    cv_viewset = cv_poly
    cv_list_actions = [
        "detail",
        "update",
        "delete"
    ]
    cv_context_actions = ["create_select", ]


class PolyCreateSelectView(PolymorphicCreateSelectView):
    model = Poly
    # fields = ["shared"]
    cv_viewset = cv_poly


PolyOneFormCreate = modelform_factory(
    PolyOne,
    fields=[
        "shared",
        "one",
    ],
)

PolyTwoFormCreate = modelform_factory(
    PolyTwo,
    fields=[
        "shared",
        "two",
    ],
)


class PolyCreateView(PolymorphicCreateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    polymorphic_forms = {
        PolyOne: PolyOneFormCreate,
        PolyTwo: PolyTwoFormCreate
    }


PolyOneFormUpdate = modelform_factory(
    PolyOne,
    fields=[
        "shared",
        "one",
    ],
)

PolyTwoFormUpdate = modelform_factory(
    PolyTwo,
    fields=[
        "shared",
        "two",
    ],
)


class PolyUpdateView(PolymorphicUpdateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    polymorphic_forms = {
        PolyOne: PolyOneFormUpdate,
        PolyTwo: PolyTwoFormUpdate
    }


class PolyDeleteView(PolymorphicDeleteViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly


class PolyDetailView(PolymorphicDetailViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    cv_properties = ["id", "shared"]

