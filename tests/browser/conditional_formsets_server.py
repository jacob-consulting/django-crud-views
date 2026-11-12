"""Disposable authenticated loopback host for conditional/formset browser acceptance.

Only temporary SQLite and media are used. ImageField coverage is stored-reference-only.
"""

# ruff: noqa: E402 -- configure Django before importing models.
import hashlib
import json
import os
import signal
import tempfile
from contextvars import ContextVar
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from wsgiref.simple_server import make_server

from tests.test1.conftest import pytest_configure

pytest_configure()
from django.conf import settings

ROOT = Path(__file__).resolve().parents[2]
temporary = tempfile.TemporaryDirectory(prefix="dcv-064-browser-")
settings.DATABASES["default"]["NAME"] = str(Path(temporary.name) / "db.sqlite3")
settings.MEDIA_ROOT = str(Path(temporary.name) / "media")
settings.ALLOWED_HOSTS = ["127.0.0.1"]
settings.ROOT_URLCONF = __name__
theme = ContextVar("browser_theme", default="stock")
from django.template import Origin
from django.template.loaders.filesystem import Loader


class ThemeLoader(Loader):
    def get_template_sources(self, template_name):
        replacements = {
            "crud_views/conditional/toggle_group.html": "native_toggle_group.html",
            "crud_views/formsets/formsets.html": "native_formsets.html",
            "crud_views/formsets/formset.html": "native_formset.html",
            "crud_views/formsets/control.html": "native_control.html",
        }
        if theme.get() == "native" and template_name in replacements:
            yield Origin(
                str(ROOT / "tests/browser/templates/conditional_formsets" / replacements[template_name]),
                template_name,
                self,
            )
        yield from super().get_template_sources(template_name)


# No cached loader: each real request selects its own theme, including recursive inclusion tags.
settings.TEMPLATES[0]["APP_DIRS"] = False
settings.TEMPLATES[0]["OPTIONS"]["loaders"] = [
    ("__main__.ThemeLoader", [str(ROOT / "tests/browser/templates")]),
    "django.template.loaders.app_directories.Loader",
]
from collections import OrderedDict

from crispy_forms.layout import Layout
from django import forms
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connection, models
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel

from crud_views.lib.conditional import (
    ConditionalFormSet,
    ConditionalGroup,
    ConditionalGroupFormMixin,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.conditional.toggle import ValueToggle
from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import (
    CompactColumn,
    CompactLayout,
    FormSet,
    FormSetMixin,
    FormSets,
    Formsets,
    InlineFormSet,
)
from crud_views.lib.view.base import cv_is_modal_request
from crud_views.lib.views import UpdateViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Book, BookNote, ConditionalPersistenceRecord, Profile, Publisher

events = []
observed = []
received = []


class BrowserMemo(OrderedModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    order_with_respect_to = "book"

    class Meta(OrderedModel.Meta):
        app_label = "app"


class BrowserConditionalRecord(models.Model):
    parent = models.ForeignKey(Profile, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="conditional/", blank=True)
    image = models.ImageField(upload_to="conditional/", blank=True)
    protected = models.FileField(upload_to="conditional/", blank=True)
    unchanged = models.FileField(upload_to="conditional/", blank=True)

    class Meta:
        app_label = "app"


class BrowserScore(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    taster = models.ForeignKey(User, on_delete=models.PROTECT)
    aroma = models.IntegerField(default=7)
    flavor = models.IntegerField(default=7)
    acidity = models.IntegerField(default=7)
    body = models.IntegerField(default=7)
    balance = models.IntegerField(default=7)
    sweetness = models.IntegerField(default=7)
    overall = models.IntegerField(default=7)

    class Meta:
        app_label = "app"


class BrowserLeaf(models.Model):
    note = models.ForeignKey(BookNote, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    class Meta:
        app_label = "app"


call_command("migrate", run_syncdb=True, verbosity=0)
with connection.schema_editor() as editor:
    for model in (BrowserMemo, BrowserConditionalRecord, BrowserScore, BrowserLeaf):
        if model._meta.db_table not in connection.introspection.table_names():
            editor.create_model(model)


def watch(model):
    original = model.save

    def save(instance, *args, **kwargs):
        events.append({"model": model.__name__, "pk": instance.pk})
        return original(instance, *args, **kwargs)

    model.save = save


class BrowserPublisherForm(ConditionalGroupFormMixin, CrispyModelForm):
    outer = forms.BooleanField(required=False, initial=True)
    inner = forms.BooleanField(required=False, initial=True)
    contact = forms.CharField(required=False, initial="default contact")
    detail = forms.CharField(required=False, initial="default detail")
    baseline = forms.CharField(required=False, initial="protected baseline", disabled=True)
    cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("outer"), ["contact", "detail"])]

    class Meta:
        model = Publisher
        fields = ["name"]

    @property
    def helper(self):
        helper = super().helper
        helper.form_tag = False
        helper.disable_csrf = True
        return helper

    def get_layout_fields(self):
        return [
            "name",
            "outer",
            ToggleGroup(
                "outer", "contact", "baseline", "inner", ToggleGroup("inner", "detail", legend="Inner"), legend="Outer"
            ),
            Formsets(),
        ]

    def get_cancel_button_kwargs(self):
        return {"name": "cancel", "value": "Cancel", "data_cv_modal_dismiss": ""}


class BrowserRowForm(CrispyModelForm):
    def get_layout_fields(self):
        return list(self.Meta.fields)

    def get_cancel_button_kwargs(self):
        return {"name": "cancel", "value": "Cancel", "data_cv_modal_dismiss": ""}


class BookForm(BrowserRowForm):
    proof = forms.CharField(required=False, widget=forms.HiddenInput, initial="retained proof")

    class Meta:
        model = Book
        fields = ["title"]

    def clean(self):
        data = super().clean()
        if data.get("title") == "REJECT":
            self.add_error("title", "Field correction required for this retained title.")
            self.add_error("proof", "Hidden proof correction required.")
            self.add_error(None, "Row correction required for this book.")
        return data


class NoteForm(BrowserRowForm):
    class Meta:
        model = BookNote
        fields = ["note"]


class MemoForm(BrowserRowForm):
    class Meta:
        model = BrowserMemo
        fields = ["text"]


class Rows(InlineFormSet):
    def get_helper_layout_fields(self):
        return [*self.form.base_fields, self.form_control]

    def clean(self):
        super().clean()
        if any(form.data.get(f"{form.prefix}-title") == "REJECT" for form in self.forms):
            raise forms.ValidationError("Formset correction required for these books.")


class ScoreForm(BrowserRowForm):
    class Meta:
        model = BrowserScore
        fields = ["taster", "aroma", "flavor", "acidity", "body", "balance", "sweetness", "overall"]
        labels = {"taster": "Verkostende Person mit ausführlicher übersetzter Bezeichnung"}
        help_texts = {"taster": "AusführlicherHinweisOhneTrennzeichenFürDieVerkostungUndBewertung"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["overall"].disabled = True
        self.fields["sweetness"].required = False


class LeafForm(BrowserRowForm):
    class Meta:
        model = BrowserLeaf
        fields = ["text"]


from crud_views.lib.formsets import CompactWidgetCompatible


class CompactCompatibleSelect(CompactWidgetCompatible, forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if str(value) == str(actor.pk):
            option["attrs"]["data-beans"] = "1"
        return option


class CompatibleScoreForm(ScoreForm):
    class Meta(ScoreForm.Meta):
        widgets = {**getattr(ScoreForm.Meta, "widgets", {}), "taster": CompactCompatibleSelect}


Scores = inlineformset_factory(Publisher, BrowserScore, form=ScoreForm, formset=Rows, extra=1)
CompatibleScores = inlineformset_factory(Publisher, BrowserScore, form=CompatibleScoreForm, formset=Rows, extra=1)
Leaves = inlineformset_factory(BookNote, BrowserLeaf, form=LeafForm, formset=Rows, extra=1)


def compact(field, span=8):
    return CompactLayout(columns=[CompactColumn(field, span=span)], controls_span=2)


class RestrictedBooks(Rows):
    def get_queryset(self):
        return super().get_queryset().exclude(title="FILTERED")


Books = inlineformset_factory(Publisher, Book, form=BookForm, formset=RestrictedBooks, extra=1, can_delete=True)
Notes = inlineformset_factory(Book, BookNote, form=NoteForm, formset=Rows, extra=1, can_delete=True)
Memos = inlineformset_factory(Book, BrowserMemo, form=MemoForm, formset=Rows, extra=1, can_delete=True, can_order=True)


class CheckboxBookForm(BookForm):
    acknowledged = forms.BooleanField(required=False)

    def get_layout_fields(self):
        return [*super().get_layout_fields(), "acknowledged"]


class CheckboxNoteForm(NoteForm):
    acknowledged = forms.BooleanField(required=False)

    def get_layout_fields(self):
        return [*super().get_layout_fields(), "acknowledged"]


class CheckboxMemoForm(MemoForm):
    acknowledged = forms.BooleanField(required=False)

    def get_layout_fields(self):
        return [*super().get_layout_fields(), "acknowledged"]


CheckboxBooks = inlineformset_factory(
    Publisher, Book, form=CheckboxBookForm, formset=RestrictedBooks, extra=1, can_delete=True
)
CheckboxNotes = inlineformset_factory(Book, BookNote, form=CheckboxNoteForm, formset=Rows, extra=1, can_delete=True)
CheckboxMemos = inlineformset_factory(
    Book, BrowserMemo, form=CheckboxMemoForm, formset=Rows, extra=1, can_delete=True, can_order=True
)
CapabilityMemos = inlineformset_factory(
    Book, BrowserMemo, form=MemoForm, formset=Rows, extra=1, can_delete=True, can_order=True, can_delete_extra=False
)


class EmptyMemos(Rows):
    def get_queryset(self):
        return super().get_queryset().none()


ExtraMemos = inlineformset_factory(
    Book,
    BrowserMemo,
    form=MemoForm,
    formset=EmptyMemos,
    extra=1,
    can_delete=True,
    can_order=True,
    can_delete_extra=False,
)
EditBooks = inlineformset_factory(
    Publisher, Book, form=BookForm, formset=RestrictedBooks, extra=0, can_delete=True, edit_only=True
)


class EmptyBooks(RestrictedBooks):
    def get_queryset(self):
        return super().get_queryset().none()


BookEdges = {
    name: inlineformset_factory(
        Publisher,
        Book,
        form=BookForm,
        formset=EmptyBooks if name in ("blank", "zero") else RestrictedBooks,
        extra=1 if name in ("blank", "delete-absent") else 0,
        can_delete=name != "no-controls",
        can_delete_extra=name != "delete-absent",
        edit_only=name == "no-controls",
    )
    for name in ("blank", "zero", "extra-zero", "no-controls", "delete-absent")
}


class RecordForm(ConditionalGroupFormMixin, BrowserRowForm):
    cv_conditional_groups = [
        ConditionalGroup(
            ModelFieldToggle("active"),
            ["attachment", "image", "protected", "unchanged"],
            empty_values={"unchanged": None},
        )
    ]

    class Meta:
        model = BrowserConditionalRecord
        fields = ["active", "attachment", "image", "protected", "unchanged"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["protected"].disabled = True


class RecordRows(Rows):
    def get_helper_layout_fields(self):
        return ["active", ToggleGroup("active", "attachment", "image", "protected", "unchanged"), self.form_control]


Records = inlineformset_factory(
    Profile, BrowserConditionalRecord, form=RecordForm, formset=RecordRows, extra=1, can_delete=True
)


class ChoiceTracerForm(ConditionalGroupFormMixin, BrowserRowForm):
    blank_text = forms.ChoiceField(
        choices=[(value, value.title()) for value in ("consumer", "wholesale", "distributor")]
    )
    choice_toggle = ValueToggle("blank_text", values=["wholesale"])
    cv_conditional_groups = [ConditionalGroup(choice_toggle, ["nullable_text"])]

    class Meta:
        model = ConditionalPersistenceRecord
        fields = ["blank_text", "nullable_text", "number", "flag", "active"]

    def __init__(
        self, *args, widgets=False, widget="select", numeric=False, disabled=False, adversarial=False, **kwargs
    ):
        self.widgets = widgets
        if widgets:
            tokens = [0, 1, 2] if numeric else ["consumer", "wholesale", "distributor"]
            if adversarial:
                tokens = ["consumer", '<img src=x onerror="window.choiceInjected=true">', "distributor"]
            self.choice_toggles = [
                ValueToggle("blank_text", values=tokens[1:]),
                ValueToggle("blank_text", values=[tokens[1]]),
                ValueToggle("blank_text", values=[tokens[0]]),
            ]
            self.cv_conditional_groups = [
                ConditionalGroup(self.choice_toggles[0], ["nullable_text"]),
                ConditionalGroup(self.choice_toggles[1], ["number"]),
                ConditionalGroup(self.choice_toggles[2], ["flag"], required=[], empty_values={"flag": False}),
            ]
        super().__init__(*args, **kwargs)
        if widgets:
            options = {
                "choices": [(value, str(value)) for value in tokens],
                "widget": forms.RadioSelect if widget == "radio" else forms.Select,
                "disabled": disabled,
            }
            self.fields["blank_text"] = (
                forms.TypedChoiceField(coerce=int, **options)
                if numeric and not adversarial
                else forms.ChoiceField(**options)
            )
            self.fields["number"].disabled = disabled
        else:
            for name in ("number", "flag", "active"):
                self.fields.pop(name)

    @property
    def helper(self):
        helper = super().helper
        helper.form_tag = False
        helper.disable_csrf = True
        return helper

    def get_layout_fields(self):
        if self.widgets:
            return [
                "blank_text",
                ToggleGroup(self.choice_toggles[0], "nullable_text", legend="Shared business details"),
                ToggleGroup(self.choice_toggles[1], "number"),
                ToggleGroup(self.choice_toggles[2], "flag", legend="Consumer details"),
                "active",
            ]
        return ["blank_text", ToggleGroup(self.choice_toggle, "nullable_text", legend="Wholesale details")]


class CheckboxRecordForm(BrowserRowForm):
    accepted = forms.BooleanField(
        required=True,
        label=_("Bestätigung der ausführlichen Teilnahmebedingungen"),
        error_messages={"required": _("Bitte bestätigen Sie die ausführlichen Teilnahmebedingungen für diese Zeile.")},
    )

    class Meta:
        model = ConditionalPersistenceRecord
        fields = ["active", "flag", "accepted"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["active"].label = str(_("Aktive Teilnahme mit ausführlicher übersetzter Beschreibung"))
        self.fields["active"].help_text = _(
            "AusführlicherHinweisOhneTrennzeichenFürDieTeilnahmeUndBestätigung <em>ordinary help</em>"
        )
        self.fields["flag"].disabled = True
        self.fields["accepted"].initial = bool(self.instance.pk)


CheckboxRecords = inlineformset_factory(
    Profile, ConditionalPersistenceRecord, form=CheckboxRecordForm, formset=Rows, extra=1, can_delete=True
)


class ProfileForm(ConditionalGroupFormMixin, BrowserRowForm):
    cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("with_contact"), ["email", "phone"])]

    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        helper = super().helper
        helper.form_tag = False
        helper.disable_csrf = True
        helper.layout = Layout("name", "with_contact", ToggleGroup("with_contact", "email", "phone"), Formsets())
        return helper


publisher_vs = ViewSet(model=Publisher, name="browser_publisher", prefix="browser-publisher")
profile_vs = ViewSet(model=Profile, name="browser_profile", prefix="browser-profile")


class BrowserEdit(CrispyViewMixin, FormSetMixin, UpdateViewPermissionRequired):
    cv_viewset = publisher_vs
    form_class = BrowserPublisherForm
    template_name = "conditional_formsets/page.html"
    cv_modal = True
    cv_modal_supported = True
    cv_context_actions = []
    cv_formsets = FormSets(
        formsets=OrderedDict(
            books=FormSet(
                title="Books",
                klass=Books,
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("outer")),
                children=OrderedDict(
                    notes=FormSet(title="Notes", klass=Notes),
                    memos=FormSet(title="Memos", klass=Memos),
                ),
            )
        )
    )

    def get_template_names(self):
        return [self.template_name]

    def cv_get_cancel_url(self, obj=None, user=None, request=None):
        # This disposable host has only its editor route, no registered list destination.
        return self.request.path

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update(theme=theme.get(), modal=cv_is_modal_request(self.request))
        data["other_form"] = self.form_class(cv_view=self, instance=self.object)
        data["compact_fixture"] = self.request.path.startswith("/compact/")
        return data

    def cv_get_formsets(self):
        result = super().cv_get_formsets()
        if self.request.path.startswith("/compact/"):
            composition = self.request.GET.get("composition", "compact-compact")
            if self.object.pk == compact_checkbox_publisher_pk and self.request.GET.get("template"):
                # The product fragment URL deliberately carries coordinates only. Recover this host's
                # presentation-only query from its editor Referer without changing product routing.
                referer = urlsplit(self.request.headers.get("Referer", ""))
                if referer.netloc == self.request.get_host() and referer.path == self.request.path:
                    composition = parse_qs(referer.query).get("composition", [composition])[0]
            books = result.formsets["books"]
            books.form_show_labels = True
            books.conditional = None
            books.compact_layout = None if composition.startswith("classic-") else compact("title")
            for key, child in books.children.items():
                child.form_show_labels = True
                child.compact_layout = (
                    None if composition.endswith("-classic") else compact("note" if key == "notes" else "text")
                )
            books.children["notes"].children = OrderedDict(
                leaves=FormSet(title="Grandchild observations", klass=Leaves, compact_layout=compact("text"))
            )
            result.formsets["scores"] = FormSet(
                title="Cupping scores",
                klass=(
                    CompatibleScores
                    if os.environ.get("CV_COMPACT_WIDGET_FIXTURE") == "1" and self.object.pk == compact_widget_pk
                    else Scores
                ),
                compact_layout=CompactLayout(
                    columns=[
                        CompactColumn(name, span=3 if name == "taster" else 1)
                        # Django 4.2 inline instances append their FK to the shared Meta.fields list.
                        # This multi-request checkbox fixture needs the original visible score schema.
                        for name in (
                            ScoreForm.base_fields
                            if self.object.pk == compact_checkbox_publisher_pk
                            else ScoreForm.Meta.fields
                        )
                    ],
                    controls_span=2,
                ),
            )
            if self.object.pk == compact_checkbox_publisher_pk:
                # Swap only this opt-in case's cloned tree; keep its bound view and refresh cached fields.
                for declaration, klass, field in (
                    (books, CheckboxBooks, "title"),
                    (books.children["notes"], CheckboxNotes, "note"),
                    (books.children["memos"], CheckboxMemos, "text"),
                ):
                    assert declaration.cv_view is self
                    declaration.klass = klass
                    declaration.fields = list(declaration.klass.form.base_fields)
                    if declaration.compact_layout:
                        declaration.compact_layout = CompactLayout(
                            columns=[CompactColumn(field, span=6), CompactColumn("acknowledged", span=4)],
                            controls_span=2,
                        )
                # A classic sibling beside compact books, independently of the child composition.
                result.formsets["classic_books"] = FormSet(
                    title="Classic sibling books", klass=CheckboxBooks, form_show_labels=True
                )
            if edge := self.request.GET.get("edge"):
                books.klass = BookEdges[edge]
                books.children = OrderedDict()
                result.formsets.pop("scores")
            result.apply_hierarchy()
        if self.request.GET.get("policy") == "edit":
            result.formsets["books"].klass = EditBooks
        if self.request.GET.get("capability"):
            result.formsets["books"].children["memos"].klass = (
                ExtraMemos if self.request.GET["capability"] == "all-extra" else CapabilityMemos
            )
        return result

    def cv_form_is_valid(self, context):
        received.append(
            {
                "post": dict(self.request.POST.lists()),
                "files": {k: {"name": f.name, "size": f.size} for k, f in self.request.FILES.items()},
            }
        )
        valid = super().cv_form_is_valid(context)
        if self.request.GET.get("reclean"):
            for tree in context["formsets"].x_formsets:
                tree.instance.full_clean()
            valid = super().cv_form_is_valid(context)
        for tree in context["formsets"].x_formsets:
            for row in tree.forms:
                observed.append(
                    {
                        "prefix": row.form.prefix,
                        "changed": row.form.has_changed(),
                        "changed_data": row.form.changed_data,
                        "pk": row.form.instance.pk,
                    }
                )
        return valid

    def cv_form_valid_redirect(self, context):
        if cv_is_modal_request(self.request):
            response = HttpResponse(status=204)
            response["X-CV-Redirect"] = self.request.path
            return response
        return JsonResponse({"saved": True})

    def cv_form_invalid(self, context):
        return self.render_to_response(context, status=422)


class BrowserFiles(BrowserEdit):
    cv_viewset = profile_vs
    form_class = ProfileForm
    cv_formsets = FormSets(formsets=OrderedDict(records=FormSet(title="Records", klass=Records)))

    def cv_get_formsets(self):
        result = super().cv_get_formsets()
        if self.object.pk == compact_checkbox_pk:
            records = result.formsets["records"]
            assert records.cv_view is self
            records.klass = CheckboxRecords
            records.fields = list(records.klass.form.base_fields)
            records.compact_layout = CompactLayout(
                columns=[
                    CompactColumn("active", span=4),
                    CompactColumn("flag", span=2),
                    CompactColumn("accepted", span=4),
                ],
                controls_span=2,
            )
            result.apply_hierarchy()
        return result

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.object.pk == compact_checkbox_pk:
            data["compact_fixture"] = True
        return data


actor = User.objects.create_superuser(username="browser", password=None, email="")
denied_actor = User.objects.create_user(username="browser-denied", password=None)
choice_record = ConditionalPersistenceRecord.objects.create(
    parent=Profile.objects.create(name="Choice tracer"),
    blank_text="wholesale",
    nullable_text="Existing wholesale detail",
)
cases = [{"theme": "stock", "id": "value-tracer", "pk": choice_record.pk, "url": f"/choice/stock/{choice_record.pk}/"}]
choice_records = [choice_record.pk]
for mode in ("stock", "native"):
    for widget in ("select", "radio"):
        for numeric in (False, True):
            record = ConditionalPersistenceRecord.objects.create(
                parent=Profile.objects.create(name=f"Choice {mode} {widget} {numeric}"),
                blank_text="1" if numeric else "wholesale",
                nullable_text="Saved shared details",
                number=42,
                flag=False,
                active=True,
            )
            choice_records.append(record.pk)
            cases.append(
                {
                    "theme": mode,
                    "id": "choice-widgets",
                    "widget": widget,
                    "numeric": numeric,
                    "pk": record.pk,
                    "url": f"/choice/{mode}/{record.pk}/?widgets=1&widget={widget}&numeric={int(numeric)}",
                }
            )
for mode in ("stock", "native"):
    for case in (
        "tracer",
        "fragment-raw-balance",
        "native-reset-user-default",
        "native-reset-user-cancelled",
        "disabled-same-value-ownership",
        "inline-file-clear-unchanged",
        "conditional-focus",
        "lifecycle",
        "tampered-post",
        "late-init",
        "gap-capability",
        "gap-ambiguity",
    ):
        parent = Publisher.objects.create(name=f"{mode} {case}")
        book = Book.objects.create(publisher=parent, title="Initial book")
        BookNote.objects.create(book=book, note="Initial note")
        BrowserMemo.objects.create(book=book, text="Initial memo")
        filtered = Book.objects.create(publisher=parent, title="FILTERED")
        foreign = Book.objects.create(publisher=Publisher.objects.create(name="foreign"), title="Foreign book")
        profile = Profile.objects.create(name=f"{mode} {case}")
        record = BrowserConditionalRecord.objects.create(parent=profile)
        references = {}
        for name in ("attachment", "image", "protected", "unchanged"):
            field = record._meta.get_field(name)
            stored = field.storage.save(f"seed/{record.pk}-{name}.bin", ContentFile(b"original fixture content"))
            setattr(record, name, stored)
            references[name] = stored
        record.save()
        empty_parent = Publisher.objects.create(name=f"{mode} {case} empty")
        empty_book = Book.objects.create(publisher=empty_parent, title="Empty memo owner")
        cases.append(
            {
                "theme": mode,
                "id": case,
                "pk": parent.pk,
                "book": book.pk,
                "filtered": filtered.pk,
                "foreign": foreign.pk,
                "profile": profile.pk,
                "record": record.pk,
                "emptyBook": empty_book.pk,
                "emptyPk": empty_parent.pk,
                "emptyUrl": f"/edit/{mode}/{empty_parent.pk}/",
                "references": references,
                "url": f"/edit/{mode}/{parent.pk}/",
                "filesUrl": f"/files/{mode}/{profile.pk}/",
            }
        )
for model in (Publisher, Profile, Book, BookNote, BrowserMemo, BrowserConditionalRecord, ConditionalPersistenceRecord):
    watch(model)
events.clear()

compact_widget_pk = None
compact_checkbox_pk = None
compact_checkbox_publisher_pk = None
if os.environ.get("CV_COMPACT_CHECKBOX_FIXTURE") == "1":
    profile = Profile.objects.create(name="compact-checkbox")
    compact_checkbox_pk = profile.pk
    record = ConditionalPersistenceRecord.objects.create(parent=profile, flag=True)
    other_record = ConditionalPersistenceRecord.objects.create(parent=profile, active=True, flag=False)
    checkbox_parent = Publisher.objects.create(name="compact-checkbox")
    compact_checkbox_publisher_pk = checkbox_parent.pk
    for index in range(2):
        checkbox_book = Book.objects.create(publisher=checkbox_parent, title=f"Checkbox book {index}")
        BookNote.objects.create(book=checkbox_book, note=f"Checkbox note {index}")
        for memo_index in range(2):
            BrowserMemo.objects.create(book=checkbox_book, text=f"Checkbox memo {index}/{memo_index}")
    BrowserScore.objects.create(publisher=checkbox_parent, taster=actor)
    cases.append(
        {
            "theme": "stock",
            "id": "compact-checkbox",
            "profile": profile.pk,
            "record": record.pk,
            "otherRecord": other_record.pk,
            "publisher": checkbox_parent.pk,
            "publisherUrl": f"/compact/stock/{checkbox_parent.pk}/",
            "nestedFields": {
                "books": list(CheckboxBookForm.base_fields),
                "classic_books": list(CheckboxBookForm.base_fields),
                "notes": list(CheckboxNoteForm.base_fields),
                "memos": list(CheckboxMemoForm.base_fields),
            },
            "url": f"/files/stock/{profile.pk}/",
            "fields": list(CheckboxRecordForm.base_fields),
        }
    )
compact_cases = ["compact-presentation", "compact-lifecycle"]
if os.environ.get("CV_COMPACT_WIDGET_FIXTURE") == "1":
    compact_cases.append("compact-widget")
for case in compact_cases:
    parent = Publisher.objects.create(name=case)
    for index in range(2):
        book = Book.objects.create(publisher=parent, title=f"Parent book {index}")
        note = BookNote.objects.create(book=book, note=f"Child note {index}")
        BrowserLeaf.objects.create(note=note, text=f"Grandchild {index}")
        BrowserMemo.objects.create(book=book, text=f"Sibling memo {index}")
    BrowserScore.objects.create(publisher=parent, taster=actor)
    cases.append({"theme": "stock", "id": case, "pk": parent.pk, "url": f"/compact/stock/{parent.pk}/"})
    if case == "compact-widget":
        compact_widget_pk = parent.pk
        cases[-1].update(taster=actor.pk, taster_label=str(actor), widget_class="CompactCompatibleSelect")
events.clear()


def edit(request, mode, pk, files=False, capability=None, edge=None):
    if capability:
        request.GET = request.GET.copy()
        request.GET["capability"] = capability
    if edge:
        request.GET = request.GET.copy()
        request.GET["edge"] = edge
    token = theme.set(mode)
    try:
        response = (BrowserFiles if files else BrowserEdit).as_view()(request, pk=pk)
        if isinstance(response, TemplateResponse):
            response.render()
        return response
    finally:
        theme.reset(token)


def choice_edit(request, mode, pk):
    if not request.user.is_superuser:
        return HttpResponse(status=403)
    instance = ConditionalPersistenceRecord.objects.get(pk=pk)
    widgets = request.GET.get("widgets") == "1"
    numeric = request.GET.get("numeric") == "1"
    if request.GET.get("harness"):
        query = request.GET.copy()
        query.pop("harness")
        return TemplateResponse(
            request,
            "conditional_formsets/page.html",
            {
                "harness": True,
                "theme": mode,
                "target": request.path + "?" + query.urlencode(),
            },
        )
    if request.GET.get("create"):
        instance = ConditionalPersistenceRecord(parent=instance.parent, blank_text="0" if numeric else "consumer")
    form = ChoiceTracerForm(
        None,
        data=request.POST if request.method == "POST" else None,
        instance=instance,
        prefix="choice[<]-0" if widgets else "choice-0",
        widgets=widgets,
        widget=request.GET.get("widget", "select"),
        numeric=numeric,
        disabled=request.GET.get("disabled") == "1",
        adversarial=request.GET.get("adversarial") == "1",
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"saved": True})
    token = theme.set(mode)
    try:
        response = TemplateResponse(
            request,
            "conditional_formsets/page.html",
            {"form": form, "theme": mode, "compact_fixture": True, "modal": cv_is_modal_request(request)},
            status=422 if request.method == "POST" else 200,
        )
        response.render()
        return response
    finally:
        theme.reset(token)


def signin(request):
    login(
        request,
        denied_actor if request.GET.get("denied") else actor,
        backend="django.contrib.auth.backends.ModelBackend",
    )
    from django.middleware.csrf import get_token

    get_token(request)
    return JsonResponse({"authenticated": True})


def state(request):
    records = list(BrowserConditionalRecord.objects.values())
    return JsonResponse(
        {
            "events": events,
            "observed": observed,
            "received": received,
            "books": list(Book.objects.values()),
            "notes": list(BookNote.objects.values()),
            "memos": list(BrowserMemo.objects.values()),
            "scores": list(BrowserScore.objects.values()),
            "leaves": list(BrowserLeaf.objects.values()),
            "records": records,
            "choice_records": list(ConditionalPersistenceRecord.objects.filter(pk__in=choice_records).values()),
            "checkbox_records": list(
                ConditionalPersistenceRecord.objects.filter(parent_id=compact_checkbox_pk).values()
            ),
            "storageContent": {
                str(p.relative_to(settings.MEDIA_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in Path(settings.MEDIA_ROOT).rglob("*")
                if p.is_file()
            },
            "storage": sorted(
                str(p.relative_to(settings.MEDIA_ROOT)) for p in Path(settings.MEDIA_ROOT).rglob("*") if p.is_file()
            ),
        }
    )


def harness(request, mode, pk):
    return TemplateResponse(
        request,
        "conditional_formsets/page.html",
        {
            "harness": True,
            "theme": mode,
            "target": f"/edit/{mode}/{pk}/",
        },
    )


urlpatterns = [
    path("signin/", signin),
    path("cases/", lambda request: JsonResponse(cases, safe=False)),
    path("state/", state),
    path("choice/<str:mode>/<int:pk>/", choice_edit),
    path("edit/<str:mode>/<int:pk>/", edit),
    path("compact/<str:mode>/<int:pk>/", edit),
    path("compact/<str:edge>/<str:mode>/<int:pk>/", edit),
    path("capability/<str:capability>/<str:mode>/<int:pk>/", edit),
    path("files/<str:mode>/<int:pk>/", lambda request, mode, pk: edit(request, mode, pk, files=True)),
    path("harness/<str:mode>/<int:pk>/", harness),
    path(
        "jquery.js",
        lambda request: HttpResponse(
            (ROOT / "node_modules/jquery/dist/jquery.js").read_text(), content_type="text/javascript"
        ),
    ),
]
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application


def main():
    port = int(os.environ.get("CV_CONDITIONAL_PORT", "8144"))
    if not 1024 <= port <= 65535 or port == 8143:
        raise ValueError("CV_CONDITIONAL_PORT must be 1024..65535 and cannot be modal-focus port 8143")
    application = StaticFilesHandler(get_wsgi_application())
    with make_server("127.0.0.1", port, application) as server:

        def stop(signum, frame):
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, stop)
        print(
            json.dumps(
                {"ready": port, "database": "disposable SQLite", "media": "temporary", "temporary": temporary.name}
            ),
            flush=True,
        )
        try:
            server.serve_forever()
        finally:
            connection.close()
            temporary.cleanup()


if __name__ == "__main__":
    main()
