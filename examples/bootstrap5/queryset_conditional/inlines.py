from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.layout import Row
from django import forms
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupModelForm, ToggleGroup
from crud_views.lib.crispy import Column8, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import (
    CompactColumn,
    CompactLayout,
    FormSet,
    FormSetMixin,
    FormSets,
    Formsets,
    InlineFormSet,
)
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from queryset_conditional.conditions import REMOTE_CONDITION, VISIT_CONDITION
from queryset_conditional.models import RequestBatch, Service, ServiceRequest

cv_service_batch = ViewSet(model=RequestBatch, name="service_batch", prefix="service-batch")
cv_service_batch_compact = ViewSet(model=RequestBatch, name="service_batch_compact", prefix="service-batch-compact")


class RequestRowForm(ConditionalGroupModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.annotate(conditional_category=F("category__code")), label=_("Service")
    )
    cv_conditional_groups = [
        ConditionalGroup(toggle=VISIT_CONDITION, fields=["visit_address"], required=["visit_address"]),
        ConditionalGroup(toggle=REMOTE_CONDITION, fields=["meeting_url"], required=["meeting_url"]),
    ]

    class Meta:
        model = ServiceRequest
        fields = ["service", "visit_address", "meeting_url"]
        # Keep the generated URLField and validators; TextInput fits the compact widget contract.
        widgets = {"meeting_url": forms.TextInput()}


class RequestInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        # Ordinary rows use the formset helper, not the individual form's helper.
        return [
            Row(Column8("service"), self.form_control_col4),
            ToggleGroup(VISIT_CONDITION, Row(Column8("visit_address")), legend=_("On-site visit")),
            ToggleGroup(REMOTE_CONDITION, Row(Column8("meeting_url")), legend=_("Remote meeting")),
        ]


RequestFormSet = inlineformset_factory(
    RequestBatch,
    ServiceRequest,
    form=RequestRowForm,
    formset=RequestInlineFormSet,
    fields=["service", "visit_address", "meeting_url"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

ORDINARY_FORMSETS = FormSets(
    formsets=OrderedDict(
        requests=FormSet(
            title=_("Service requests"),
            klass=RequestFormSet,
            fields=["service", "visit_address", "meeting_url"],
            pk_field="id",
        )
    )
)
COMPACT_FORMSETS = FormSets(
    formsets=OrderedDict(
        requests=FormSet(
            title=_("Service requests"),
            klass=RequestFormSet,
            fields=["service", "visit_address", "meeting_url"],
            pk_field="id",
            compact_layout=CompactLayout(
                columns=[
                    CompactColumn("service", span=3),
                    CompactColumn("visit_address", span=3),
                    CompactColumn("meeting_url", span=3),
                ],
                controls_span=3,
            ),
        )
    )
)


class BatchForm(CrispyModelForm):
    class Meta:
        model = RequestBatch
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]


class BatchTable(Table):
    title = tables.Column()


class BatchListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_service_batch
    table_class = BatchTable


class BatchCreateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_service_batch
    form_class = BatchForm
    cv_formsets = ORDINARY_FORMSETS
    cv_message_template_code = _("Created request batch “{{ object }}”")


class BatchUpdateView(BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_service_batch
    form_class = BatchForm
    cv_formsets = ORDINARY_FORMSETS
    cv_message_template_code = _("Updated request batch “{{ object }}”")


class CompactBatchListView(BatchListView):
    cv_viewset = cv_service_batch_compact


class CompactBatchCreateView(BatchCreateView):
    cv_viewset = cv_service_batch_compact
    cv_formsets = COMPACT_FORMSETS


class CompactBatchUpdateView(BatchUpdateView):
    cv_viewset = cv_service_batch_compact
    cv_formsets = COMPACT_FORMSETS
