import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _

from app.models.poly import Poly, PolyOne, PolyTwo
from app.views.poly.one import PolyOneForm
from app.views.poly.two import PolyTwoForm
from crud_views.lib.crispy import Column4, CrispyModelViewMixin
from crud_views.lib.crispy.form import CrispyForm
from crud_views.lib.polymorphic_views import PolymorphicCreateSelectView, PolymorphicCreateViewPermissionRequired, \
    PolymorphicUpdateViewPermissionRequired, PolymorphicDetailViewPermissionRequired
from crud_views.lib.polymorphic_views.create_select import PolymorphicContentTypeForm
from crud_views.lib.polymorphic_views.delete import PolymorphicDeleteViewPermissionRequired
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewPermissionRequired
from crud_views.lib.views import ListViewTableMixin
from crud_views.lib.viewset import ViewSet, path_regs

cv_poly = ViewSet(
    model=Poly,
    name="poly",
    pk=ViewSet.PK.UUID,
    icon_header="fa-solid fa-sun"
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


class CrispyPolymorphicContentTypeForm(CrispyForm, PolymorphicContentTypeForm):
    submit_label = _("Select")

    def get_layout_fields(self):
        return Row(Column4("polymorphic_ctype_id"))


class PolyCreateSelectView(CrispyModelViewMixin, PolymorphicCreateSelectView):
    model = Poly
    form_class = CrispyPolymorphicContentTypeForm
    cv_viewset = cv_poly


class PolyCreateView(CrispyModelViewMixin, PolymorphicCreateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    cv_context_actions = ["home"]
    polymorphic_forms = {
        PolyOne: PolyOneForm,
        PolyTwo: PolyTwoForm
    }


class PolyUpdateView(CrispyModelViewMixin, PolymorphicUpdateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    polymorphic_forms = {
        PolyOne: PolyOneForm,
        PolyTwo: PolyTwoForm
    }


class PolyDeleteView(PolymorphicDeleteViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly


class PolyDetailView(PolymorphicDetailViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly
    cv_properties = ["id", "shared"]
