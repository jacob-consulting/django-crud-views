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
from ordered_model.models import OrderedModel

from crud_views.lib.conditional import (
    ConditionalFormSet,
    ConditionalGroup,
    ConditionalGroupFormMixin,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
from crud_views.lib.view.base import cv_is_modal_request
from crud_views.lib.views import UpdateViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Book, BookNote, Profile, Publisher

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


call_command("migrate", run_syncdb=True, verbosity=0)
with connection.schema_editor() as editor:
    for model in (BrowserMemo, BrowserConditionalRecord):
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
    class Meta:
        model = Book
        fields = ["title"]


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


class RestrictedBooks(Rows):
    def get_queryset(self):
        return super().get_queryset().exclude(title="FILTERED")


Books = inlineformset_factory(Publisher, Book, form=BookForm, formset=RestrictedBooks, extra=1, can_delete=True)
Notes = inlineformset_factory(Book, BookNote, form=NoteForm, formset=Rows, extra=1, can_delete=True)
Memos = inlineformset_factory(Book, BrowserMemo, form=MemoForm, formset=Rows, extra=1, can_delete=True, can_order=True)
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


class ProfileForm(ConditionalGroupFormMixin, BrowserRowForm):
    cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("with_contact"), ["email", "phone"])]

    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        helper = super().helper
        helper.form_tag = False
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

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update(theme=theme.get(), modal=cv_is_modal_request(self.request))
        data["other_form"] = self.form_class(cv_view=self, instance=self.object)
        return data

    def cv_get_formsets(self):
        result = super().cv_get_formsets()
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


actor = User.objects.create_superuser(username="browser", password=None, email="")
cases = []
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
for model in (Publisher, Profile, Book, BookNote, BrowserMemo, BrowserConditionalRecord):
    watch(model)
events.clear()


def edit(request, mode, pk, files=False, capability=None):
    if capability:
        request.GET = request.GET.copy()
        request.GET["capability"] = capability
    token = theme.set(mode)
    try:
        response = (BrowserFiles if files else BrowserEdit).as_view()(request, pk=pk)
        if isinstance(response, TemplateResponse):
            response.render()
        return response
    finally:
        theme.reset(token)


def signin(request):
    login(request, actor, backend="django.contrib.auth.backends.ModelBackend")
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
            "records": records,
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
    path("edit/<str:mode>/<int:pk>/", edit),
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
        print(json.dumps({"ready": port, "database": "disposable SQLite", "media": "temporary"}), flush=True)
        try:
            server.serve_forever()
        finally:
            connection.close()
            temporary.cleanup()


if __name__ == "__main__":
    main()
