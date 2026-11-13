"""Queryset conditions through real ordinary inline and CRUD persistence paths."""

from unittest.mock import patch

import django
import pytest
from django import forms
from django.db import connection, models
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path

from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, InlineFormSet
from crud_views.lib.views import CreateView, UpdateView
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import ConditionalPersistenceRecord as Record
from tests.test1.app.models import Profile, Publisher
from tests.test1.test_conditional_persistence import inline_tree
from tests.test1.test_conditional_queryset import record_form, source_for

pytestmark = pytest.mark.django_db


def row_form():
    class Row(record_form(source_for())):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance._state.adding:
                self.initial["blank_text"] = ""
                self.initial["nullable_text"] = None

    return Row


def test_unchanged_queryset_inline_cleanup_and_empty_extra():
    option = Publisher.objects.create(name="general")
    row = Record.objects.create(
        parent=Profile.objects.create(name="parent"), reference=option, blank_text="stale", nullable_text="stale"
    )
    trees, form = inline_tree(
        row, row_form(), {"reference": str(option.pk), "blank_text": "stale", "nullable_text": "stale"}, extra=1
    )
    assert trees.all_valid()
    assert not form.has_changed()
    assert form._cv_conditional_requires_save
    extra = trees.x_formsets[0].instance.forms[1]
    assert not extra.has_changed()
    assert not extra._cv_conditional_requires_save
    with patch.object(Record, "save", autospec=True, side_effect=Record.save) as save:
        trees.save()
    assert save.call_count == 1
    row.refresh_from_db()
    assert row.blank_text == "" and row.nullable_text is None
    assert Record.objects.count() == 1


def test_deleted_queryset_row_with_unmatched_selection():
    option = Publisher.objects.create(name="unknown")
    row = Record.objects.create(parent=Profile.objects.create(name="parent"), reference=option)
    trees, form = inline_tree(row, row_form(), {"reference": str(option.pk), "DELETE": "on"}, extra=1)
    assert trees.all_valid()
    assert form.errors.as_data()["reference"][0].code == "unmatched_category"
    trees.save()
    assert not Record.objects.exists()


@pytest.mark.parametrize("kind", ["unique", "constraint"])
def test_queryset_clearing_keeps_model_validation(kind, monkeypatch):
    option = Publisher.objects.create(name="general")
    parent = Profile.objects.create(name="parent")
    row = Record.objects.create(parent=parent, reference=option)
    klass = record_form(source_for())
    if kind == "unique":
        Record.objects.create(parent=parent, unique_text="reserved")
        from crud_views.lib.conditional import ConditionalGroup

        klass = forms.modelform_factory(
            klass._meta.model, form=klass, fields=["reference", "blank_text", "nullable_text", "unique_text"]
        )
        klass.cv_conditional_groups = [
            ConditionalGroup(source_for().when("active"), ["unique_text"], empty_values={"unique_text": "reserved"})
        ]
    else:
        condition_arg = "condition" if django.VERSION >= (5, 1) else "check"
        constraint = models.CheckConstraint(
            **{condition_arg: ~models.Q(blank_text="")}, name="nonempty_conditional_detail"
        )
        monkeypatch.setattr(Record._meta, "constraints", [constraint])
    form = klass(instance=row, data={"reference": str(option.pk)})
    assert not form.is_valid()
    assert (
        "unique_text" in form.errors
        if kind == "unique"
        else "nonempty_conditional_detail" in str(form.non_field_errors())
    )
    with pytest.raises(ValueError):
        form.save()
    row.refresh_from_db()
    assert row.blank_text == "default text" and row.unique_text is None


@pytest.fixture
def editor_urls(monkeypatch):
    from crud_views.lib import viewset as viewsets

    # Registration mutates the registry directly; isolate it even when the key was absent.
    monkeypatch.setattr(viewsets, "_REGISTRY", dict(viewsets._REGISTRY))
    viewsets._REGISTRY.pop("queryset_contract_editor", None)
    rows = inlineformset_factory(Profile, Record, form=row_form(), formset=InlineFormSet, extra=1)
    declarations = FormSets(formsets={"records": FormSet(title="Records", klass=rows)})
    viewset = ViewSet(model=Profile, name="queryset_contract_editor")

    class ParentForm(CrispyModelForm):
        class Meta:
            model = Profile
            fields = ["name"]

    class Responses:
        def get_success_url(self):
            return "/done/"

        def cv_form_invalid(self, context):
            return HttpResponse(str(context["form"].errors), status=422)

    class Create(Responses, CrispyViewMixin, FormSetMixin, CreateView):
        cv_viewset = viewset
        form_class = ParentForm
        cv_formsets = declarations

    class Update(Responses, CrispyViewMixin, FormSetMixin, UpdateView):
        cv_viewset = viewset
        form_class = ParentForm
        cv_formsets = declarations

    with override_settings(
        ROOT_URLCONF=type(
            "URLs", (), {"urlpatterns": [path("create/", Create.as_view()), path("<int:pk>/update/", Update.as_view())]}
        )
    ):
        yield Client()


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("invalid", [False, True])
def test_real_formset_endpoint_atomic_rows(editor_urls, operation, invalid):
    active = Publisher.objects.create(name="active")
    general = Publisher.objects.create(name="general")
    parent = Profile.objects.create(name="original") if operation == "update" else None
    old = [Record.objects.create(parent=parent, reference=active, blank_text="old") for _ in range(2)] if parent else []
    prefix = f"records-{parent.pk if parent else None}-0"
    post = {"name": "saved", f"{prefix}-TOTAL_FORMS": "3", f"{prefix}-INITIAL_FORMS": str(len(old))}
    for index in range(2):
        post.update(
            {
                f"{prefix}-{index}-reference": str(active.pk if index == 1 else general.pk),
                f"{prefix}-{index}-blank_text": "" if invalid and index == 1 else "new",
            }
        )
        if old:
            post[f"{prefix}-{index}-id"] = str(old[index].pk)
    before = (list(Profile.objects.values()), list(Record.objects.values()))
    with CaptureQueriesContext(connection) as queries:
        response = editor_urls.post(f"/{parent.pk}/update/" if parent else "/create/", post)
    assert response.status_code == (422 if invalid else 302), response.content
    if invalid:
        assert (list(Profile.objects.values()), list(Record.objects.values())) == before
        assert not any(query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for query in queries)
    else:
        saved = Profile.objects.get(name="saved")
        assert list(Record.objects.filter(parent=saved).order_by("pk").values_list("blank_text", flat=True)) == [
            "",
            "new",
        ]


def test_forged_row_identity_is_rejected(editor_urls):
    option = Publisher.objects.create(name="general")
    parent = Profile.objects.create(name="parent")
    outsider = Record.objects.create(parent=Profile.objects.create(name="other"), reference=option, blank_text="keep")
    prefix = f"records-{parent.pk}-0"
    post = {
        "name": "forged",
        f"{prefix}-TOTAL_FORMS": "1",
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": str(outsider.pk),
        f"{prefix}-0-reference": str(option.pk),
        f"{prefix}-0-blank_text": "tamper",
    }
    assert editor_urls.post(f"/{parent.pk}/update/", post).status_code == 422
    parent.refresh_from_db()
    outsider.refresh_from_db()
    assert parent.name == "parent" and outsider.blank_text == "keep"
