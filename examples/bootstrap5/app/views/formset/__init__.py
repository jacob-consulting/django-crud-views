from collections import OrderedDict
from datetime import date
from typing import List, Dict, Type

import django_tables2 as tables
from crispy_forms.layout import Row, LayoutObject
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from app.models.poly import Poly, PolyOne, PolyTwo, PolyTwoChoice, PolyThree, PolyAnswerText, PolyAnswerNumber
from crud_views.lib.crispy import Column4, CrispyModelViewMixin, Column8
from crud_views.lib.crispy.form import CrispyForm, CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from crud_views.lib.formsets.mixins import PolymorphicFormSetMixin
from crud_views.lib.polymorphic_views import PolymorphicCreateSelectView, PolymorphicCreateViewPermissionRequired, \
    PolymorphicUpdateViewPermissionRequired, PolymorphicDetailViewPermissionRequired
from crud_views.lib.polymorphic_views.create_select import PolymorphicContentTypeForm
from crud_views.lib.polymorphic_views.delete import PolymorphicDeleteViewPermissionRequired
from crud_views.lib.table import Table, UUIDLinkDetailColumn, ActionColumn
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin, CreateViewParentMixin
from crud_views.lib.viewset import ViewSet, path_regs, ParentViewSet
from .answer import PolyAnswerFormSet
from .one import PolyOneForm
from .three import PolyThreeForm
from .two import PolyTwoForm

cv_poly_formset = ViewSet(
    model=Poly,
    name="poly",
    pk=ViewSet.PK.UUID,
    icon_header="fa-solid fa-sun",
    parent=ParentViewSet(
        name="parent",
        many_to_many_through_attribute="polys",
        attribute="parents"  # related_name of many2many field
    )
)


class PolyTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    shared = tables.Column(attrs=Table.ca.w80)


class PolyListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Poly
    table_class = PolyTable
    cv_viewset = cv_poly_formset
    cv_list_actions = [
        "detail",
        "update",
        "delete"
    ]
    cv_context_actions = ["parent", "create_select", ]


class ChoiceForm(CrispyModelForm):
    class Meta:
        model = PolyTwoChoice
        fields = [
            "choice",
        ]


class ChoiceInlineFormSet(InlineFormSet):

    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [
            Row(
                Column8("choice"),
                self.form_control_col4
            )
        ]


ChoiceFormSet = inlineformset_factory(
    PolyTwo,
    PolyTwoChoice,
    formset=ChoiceInlineFormSet,
    form=ChoiceForm,
    fields=[
        "choice",
    ],
    extra=1,
    # this adds fields to the form
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)

formset_answers = FormSet(  # noqa
    title="Answers",
    klass=PolyAnswerFormSet,
    fields=["choice", "help_text"],
    pk_field="id",
)

cv_formsets_one_update: FormSets = FormSets(
    scripts=True,  # we have no controls, therefore no scripts
    formsets=OrderedDict(
        answers=formset_answers
    )
)

formset_choices = FormSet(  # noqa
    title="Choices",
    klass=ChoiceFormSet,
    fields=["choice", ],
    pk_field="id",
    pk=FormSet.PK.UUID,
)

cv_formsets_two_create: FormSets = FormSets(
    scripts=True,  # we have no controls, therefore no scripts
    formsets=OrderedDict(
        choices=formset_choices
    )
)

cv_formsets_two_update: FormSets = FormSets(
    scripts=True,  # we have no controls, therefore no scripts
    formsets=OrderedDict(
        choices=formset_choices,
        answers=formset_answers,
    )
)


class CrispyPolymorphicContentTypeForm(CrispyForm, PolymorphicContentTypeForm):
    submit_label = _("Select")

    def get_layout_fields(self):
        return Row(Column4("polymorphic_ctype_id"))


class PolyCreateSelectView(CrispyModelViewMixin, PolymorphicCreateSelectView):
    model = Poly
    form_class = CrispyPolymorphicContentTypeForm
    cv_viewset = cv_poly_formset


class PolyCreateView(CrispyModelViewMixin, CreateViewParentMixin, PolymorphicFormSetMixin,
                     PolymorphicCreateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly_formset
    cv_context_actions = ["home"]
    cv_formsets_required: bool = False
    cv_polymorphic_formsets: Dict[Type[Model], FormSets] = {
        PolyOne: None,
        PolyTwo: cv_formsets_two_create,
        PolyThree: None  # this model has explicitly no formsets
    }
    polymorphic_forms = {
        PolyOne: PolyOneForm,
        PolyTwo: PolyTwoForm,
        PolyThree: PolyThreeForm
    }

    def cv_parent_many_to_many_through_defaults(self, instance, parent_instance, m2m) -> dict:
        defaults = super().cv_parent_many_to_many_through_defaults(instance, parent_instance, m2m)
        defaults.update({"date_joined": date.today()})
        return defaults

    def cv_form_valid_hook(self, context: dict):
        ct = ContentType.objects.get(id=context["polymorphic_ctype_id"])
        if ct.model_class() in [PolyOne, PolyTwo]:
            PolyAnswerText.objects.create(poly=self.object)
            PolyAnswerNumber.objects.create(poly=self.object)


class PolyUpdateView(CrispyModelViewMixin, PolymorphicFormSetMixin, PolymorphicUpdateViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly_formset
    cv_formsets_required: bool = False
    cv_polymorphic_formsets: Dict[Type[Model], FormSets] = {
        PolyOne: cv_formsets_one_update,
        PolyTwo: cv_formsets_two_update,
        PolyThree: None  # this model has explicitly no formsets
    }
    polymorphic_forms = {
        PolyOne: PolyOneForm,
        PolyTwo: PolyTwoForm,
        PolyThree: PolyThreeForm
    }


class PolyDeleteView(PolymorphicDeleteViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly_formset


class PolyDetailView(PolymorphicDetailViewPermissionRequired):
    model = Poly
    cv_viewset = cv_poly_formset
    cv_properties = ["id", "shared"]
