import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from label_modes.models import Gadget

cv_gadget = ViewSet(model=Gadget, name="gadget", icon_header="fa-solid fa-screwdriver-wrench")


class GadgetForm(CrispyModelForm):
    class Meta:
        model = Gadget
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column12("name"))


class GadgetTable(Table):
    name = tables.Column()


class GadgetListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_gadget
    table_class = GadgetTable
    cv_list_actions = ["detail", "update", "delete"]
    # one mode per row action: text only, icon and text, icon only (hidden label, short tooltip)
    cv_list_actions_label_mode = {"detail": "label", "update": "both", "delete": "icon"}
    cv_context_actions = ["create"]


class GadgetDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_gadget
    cv_context_actions = ["list", "update", "delete"]
    # the same three modes on the toolbar; keys are the configured keys
    cv_context_actions_label_mode = {"list": "label", "update": "both", "delete": "icon"}
    cv_property_display = [
        {"title": _("Gadget"), "icon": "fas:screwdriver-wrench", "properties": ["name"]},
    ]


class GadgetCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_gadget
    form_class = GadgetForm
    cv_message_template_code = _("Created gadget “{{ object }}”")


class GadgetUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_gadget
    form_class = GadgetForm
    cv_message_template_code = _("Updated gadget “{{ object }}”")


class GadgetDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_gadget
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted gadget “{{ object }}”")
