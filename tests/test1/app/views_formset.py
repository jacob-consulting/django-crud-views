"""
Publisher viewset with nested inline formsets:

    Publisher
      └─ books (Book)
           └─ notes (BookNote)

Used by tests/test1/test_formsets*.py to exercise the formsets subsystem.
"""

from collections import OrderedDict
from typing import List

import django_tables2 as tables
from crispy_forms.layout import LayoutObject, Row
from django.forms.models import inlineformset_factory

from crud_views.lib.crispy import Column4, Column8, CrispyModelForm, CrispyModelViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

from tests.test1.app.models import Book, BookNote, Publisher

cv_publisher_formset = ViewSet(
    model=Publisher,
    name="publisher_formset",
    prefix="publisher-formset",
)


class PublisherFormSetForm(CrispyModelForm):
    class Meta:
        model = Publisher
        fields = ["name"]

    def get_layout_fields(self):
        return [Row(Column4("name")), Formsets()]


class BookFormSetForm(CrispyModelForm):
    class Meta:
        model = Book
        fields = ["title"]


class BookInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [Row(Column8("title"), self.form_control_col4)]


BookFormSet = inlineformset_factory(
    Publisher,
    Book,
    formset=BookInlineFormSet,
    form=BookFormSetForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=False,
)


class BookNoteFormSetForm(CrispyModelForm):
    class Meta:
        model = BookNote
        fields = ["note"]


class BookNoteInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self) -> List[LayoutObject]:
        return [Row(Column8("note"), self.form_control_col4)]


BookNoteFormSet = inlineformset_factory(
    Book,
    BookNote,
    formset=BookNoteInlineFormSet,
    form=BookNoteFormSetForm,
    fields=["note"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=False,
)

publisher_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        books=FormSet(
            title="Books",
            klass=BookFormSet,
            children=OrderedDict(
                notes=FormSet(
                    title="Notes",
                    klass=BookNoteFormSet,
                ),
            ),
        ),
    )
)


class PublisherFormSetTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class PublisherFormSetListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherFormSetTable
    cv_viewset = cv_publisher_formset


class PublisherFormSetCreateView(CrispyModelViewMixin, FormSetMixin, CreateViewPermissionRequired):
    form_class = PublisherFormSetForm
    cv_viewset = cv_publisher_formset
    cv_formsets: FormSets = publisher_formsets


class PublisherFormSetUpdateView(CrispyModelViewMixin, FormSetMixin, UpdateViewPermissionRequired):
    form_class = PublisherFormSetForm
    cv_viewset = cv_publisher_formset
    cv_formsets: FormSets = publisher_formsets
