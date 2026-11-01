"""Mandatory row policy, through isolated registered routes and the runtime tree."""

import sys
import types
import uuid
from collections import OrderedDict
from types import SimpleNamespace

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet, inlineformset_factory, modelform_factory
from django.test import Client, RequestFactory, override_settings
from django.urls import clear_url_caches, reverse

from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, InlineFormSet
from crud_views.lib.formsets.render_tree import XFormSet
from tests.lib.helper.forms import form_payload
from tests.test1.app.models import Author, Book, BookNote, Publisher, UUIDFragmentRow
from tests.test1.app.views_formset import BookFormSetForm, BookNoteFormSetForm, PublisherFormSetForm

pytestmark = pytest.mark.django_db


class PolicyQuerysetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        if self.model is Book:
            qs = qs.exclude(title="filtered")
            if self.formset.original_key == "siblings":
                return qs.filter(title__startswith="sibling")
            return qs.exclude(title__startswith="sibling")
        return qs


class PolicyPackageInlineFormSet(PolicyQuerysetMixin, InlineFormSet):
    def get_helper_layout_fields(self):
        return list(self.form._meta.fields)


class PolicyNativeInlineFormSet(PolicyQuerysetMixin, BaseInlineFormSet):
    """Native Django adapter: deliberately never inherits the package clean()."""

    def __init__(self, *args, formset, parent_form=None, **kwargs):
        self.formset = formset
        self.parent_form = parent_form
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        return {**super().get_form_kwargs(index), "cv_view": self.formset.cv_view}

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False
        helper.disable_csrf = True
        helper.render_hidden_fields = True
        helper.layout = Layout(*self.form._meta.fields, Field("DELETE", type="hidden"))
        return helper

    def clean(self):
        super().clean()
        if self.data.get("policy-custom-error"):
            raise ValidationError("Custom clean retained.", code="custom_clean")


@pytest.fixture(params=[PolicyPackageInlineFormSet, PolicyNativeInlineFormSet], ids=["package", "native"])
def policy_routes(request, django_user_model):
    from crud_views.lib import check as check_module
    from crud_views.lib.views import (
        CreateViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet

    vocab = dict(check_module._VOCAB_CACHE)
    names = []
    module_name = f"tests.test1._policy_urls_{uuid.uuid4().hex}"
    module = types.ModuleType(module_name)
    module.urlpatterns = []
    routes = {}
    try:
        for edit_only in (True, False):
            name = f"policy{uuid.uuid4().hex}"
            names.append(name)
            vs = ViewSet(model=Publisher, name=name)
            books = inlineformset_factory(
                Publisher,
                Book,
                formset=request.param,
                form=BookFormSetForm,
                fields=["title"],
                extra=1,
                can_delete=True,
                edit_only=edit_only,
            )
            notes = inlineformset_factory(
                Book,
                BookNote,
                formset=request.param,
                form=BookNoteFormSetForm,
                fields=["note"],
                extra=1,
                can_delete=True,
            )
            declarations = FormSets(
                formsets=OrderedDict(
                    books=FormSet(
                        title="Books",
                        klass=books,
                        children=OrderedDict(
                            notes=FormSet(title="Notes", klass=notes),
                        ),
                    ),
                    siblings=FormSet(title="Siblings", klass=books),
                )
            )

            class PolicyList(ListViewPermissionRequired):
                cv_viewset = vs

            class PolicyDetail(DetailViewPermissionRequired):
                cv_viewset = vs

            class PolicyCreate(CrispyViewMixin, FormSetMixin, CreateViewPermissionRequired):
                cv_viewset = vs
                form_class = PublisherFormSetForm
                cv_formsets = declarations

            class PolicyUpdate(CrispyViewMixin, FormSetMixin, UpdateViewPermissionRequired):
                cv_viewset = vs
                form_class = PublisherFormSetForm
                cv_formsets = declarations

            routes[edit_only] = SimpleNamespace(vs=vs, declarations=declarations)
            module.urlpatterns.extend(vs.urlpatterns)
        sys.modules[module_name] = module
        user = django_user_model.objects.create_superuser(username=f"policy{uuid.uuid4().hex}", password="test")
        client = Client()
        client.force_login(user)
        clear_url_caches()
        with override_settings(ROOT_URLCONF=module_name):
            clear_url_caches()
            yield SimpleNamespace(client=client, routes=routes, family=request.param)
    finally:
        sys.modules.pop(module_name, None)
        with _REGISTRY_LOCK:
            for name in names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab)
        clear_url_caches()


@pytest.fixture
def policy_world():
    parent = Publisher.objects.create(name="Original")
    book = Book.objects.create(publisher=parent, title="book")
    sibling = Book.objects.create(publisher=parent, title="sibling original")
    note = BookNote.objects.create(book=book, note="original note")
    return SimpleNamespace(parent=parent, book=book, sibling=sibling, note=note)


def editor(routes, world, *, edit_only=True, operation="update"):
    route = routes.routes[edit_only]
    kwargs = {"pk": world.parent.pk} if operation == "update" else {}
    url = reverse(route.vs.get_router_name(operation), kwargs=kwargs)
    page = routes.client.get(url)
    assert page.status_code == 200
    return url, form_payload(page)


def runtime(routes, world, payload, *, edit_only=True):
    form = PublisherFormSetForm(cv_view=None, instance=world.parent, data=payload)
    assert form.is_valid()
    tree = routes.routes[edit_only].declarations.clone(cv_view=None)
    tree.init(RequestFactory().post("/", payload), form)
    return tree


def observe_saves(monkeypatch):
    calls = []
    for model in (Publisher, Book, BookNote):
        original = model.save

        def save(self, *args, _original=original, **kwargs):
            calls.append(type(self).__name__)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(model, "save", save)
    return calls


def observe_policy(monkeypatch):
    calls = []
    original = getattr(XFormSet, "_cv_validate_row_policy", None)
    if original is not None:

        def validate(self):
            calls.append(self.prefix)
            return original(self)

        monkeypatch.setattr(XFormSet, "_cv_validate_row_policy", validate)
    return calls


@pytest.mark.parametrize("edit_only", [True, False])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_policy_routes_accept_valid_posts(policy_routes, policy_world, edit_only, operation):
    url, payload = editor(policy_routes, policy_world, edit_only=edit_only, operation=operation)
    payload["name"] = "Accepted"
    if operation == "update":
        payload[f"books-{policy_world.parent.pk}-0-0-title"] = "edited"
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 302, response.content[:2000]
    if operation == "update":
        policy_world.book.refresh_from_db()
        assert policy_world.book.title == "edited"


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("variant", ["changed", "deleted", "nested-only"])
def test_edit_only_extras_rejected_before_any_save(policy_routes, policy_world, monkeypatch, operation, variant):
    # Prove the same route/adapter can validate and save before exercising the rejection.
    url, good = editor(policy_routes, policy_world, operation=operation)
    good["name"] = "Positive control"
    assert policy_routes.client.post(url, good).status_code == 302
    url, payload = editor(policy_routes, policy_world, operation=operation)
    payload["name"] = "Must not save"
    pk = policy_world.parent.pk if operation == "update" else "None"
    index = 1 if operation == "update" else 0
    prefix = f"books-{pk}-0"
    if operation == "update":
        payload[f"{prefix}-0-title"] = "must not edit"
        payload[f"siblings-{pk}-0-0-title"] = "sibling must not edit"
        payload[f"books-notes-{pk}-0-0-{policy_world.book.pk}-0-0-note"] = "must not edit note"
    if variant != "nested-only":
        payload[f"{prefix}-{index}-title"] = "forged extra"
    if variant == "deleted":
        payload[f"{prefix}-{index}-DELETE"] = "on"
    if variant == "nested-only":
        payload[f"books-notes-{pk}-0-{index}-None-0-0-note"] = "forged nested extra"
    saves = observe_saves(monkeypatch)
    policy = observe_policy(monkeypatch)
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 200
    tree = response.context["formsets"]
    errors = tree.x_formsets[0].instance.non_form_errors().as_data()
    assert [e.code for e in errors].count("cv_additions_not_allowed") == 1
    assert b"Additions are not allowed." in response.content
    assert tree.all_valid() is False
    assert [e.code for e in tree.x_formsets[0].instance.non_form_errors().as_data()].count(
        "cv_additions_not_allowed"
    ) == 1
    assert policy
    assert saves == []
    policy_world.book.refresh_from_db()
    policy_world.sibling.refresh_from_db()
    policy_world.note.refresh_from_db()
    assert policy_world.book.title == "book"
    assert policy_world.sibling.title == "sibling original"
    assert policy_world.note.note == "original note"
    assert not Publisher.objects.filter(name="Must not save").exists()


def test_direct_all_valid_rejects_extra(policy_routes, policy_world):
    _, payload = editor(policy_routes, policy_world)
    payload[f"books-{policy_world.parent.pk}-0-1-title"] = "forged"
    tree = runtime(policy_routes, policy_world, payload)
    assert tree.all_valid() is False
    assert tree.x_formsets[0].instance.non_form_errors().as_data()[0].code == "cv_additions_not_allowed"


def test_custom_clean_is_preserved(policy_routes, policy_world, monkeypatch):
    calls = []
    original = policy_routes.family.clean

    def clean(self):
        calls.append(self.prefix)
        result = original(self)
        if self.data.get("policy-custom-error"):
            raise ValidationError("Custom clean retained.", code="custom_clean")
        return result

    monkeypatch.setattr(policy_routes.family, "clean", clean)
    url, payload = editor(policy_routes, policy_world)
    payload["policy-custom-error"] = "on"
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 200
    assert calls
    assert len(calls) == len(set(calls))
    assert "custom_clean" in [
        e.code for e in response.context["formsets"].x_formsets[0].instance.non_form_errors().as_data()
    ]


@pytest.mark.parametrize("edit_only", [True, False])
@pytest.mark.parametrize("deleted", [False, True])
@pytest.mark.parametrize("identity", ["missing", "malformed", "nonexistent", "foreign", "filtered"])
def test_invalid_existing_ids_never_save(policy_routes, policy_world, monkeypatch, edit_only, deleted, identity):
    url, good = editor(policy_routes, policy_world, edit_only=edit_only)
    assert policy_routes.client.post(url, good).status_code == 302
    foreign_parent = Publisher.objects.create(name="Other parent")
    foreign = Book.objects.create(publisher=foreign_parent, title="foreign")
    filtered = Book.objects.create(publisher=policy_world.parent, title="filtered")
    url, payload = editor(policy_routes, policy_world, edit_only=edit_only)
    prefix = f"books-{policy_world.parent.pk}-0"
    payload["name"] = "Must not save"
    payload[f"{prefix}-0-title"] = "must not edit"
    payload[f"siblings-{policy_world.parent.pk}-0-0-title"] = "sibling must not edit"
    ids = {
        "missing": "",
        "malformed": "bad-pk",
        "nonexistent": "99999999",
        "foreign": str(foreign.pk),
        "filtered": str(filtered.pk),
    }
    payload[f"{prefix}-0-id"] = ids[identity]
    if identity == "missing":
        del payload[f"{prefix}-0-id"]
    if deleted:
        payload[f"{prefix}-0-DELETE"] = "on"
    saves = observe_saves(monkeypatch)
    policy = observe_policy(monkeypatch)
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 200
    errors = response.context["formsets"].x_formsets[0].instance.non_form_errors().as_data()
    assert [(e.code, e.messages) for e in errors] == [("cv_invalid_row", ["Invalid row."])]
    assert policy
    assert saves == []
    policy_world.parent.refresh_from_db()
    policy_world.book.refresh_from_db()
    policy_world.sibling.refresh_from_db()
    foreign.refresh_from_db()
    filtered.refresh_from_db()
    assert policy_world.parent.name == "Original"
    assert policy_world.book.title == "book"
    assert policy_world.sibling.title == "sibling original"
    assert foreign.title == "foreign"
    assert filtered.title == "filtered"


@pytest.mark.parametrize(
    "variant",
    [
        "lower-initial",
        "raise-initial",
        "authorized-extra",
        "foreign-extra",
        "filtered-extra",
        "malformed-extra",
        "negative-initial",
        "negative-total",
        "initial-over-total",
        "missing-management",
        "malformed-management",
    ],
)
def test_tampered_management_or_extra_ids_never_save(policy_routes, policy_world, monkeypatch, variant):
    url, good = editor(policy_routes, policy_world, edit_only=False)
    assert policy_routes.client.post(url, good).status_code == 302
    other_parent = Publisher.objects.create(name="Other")
    foreign = Book.objects.create(publisher=other_parent, title="foreign")
    filtered = Book.objects.create(publisher=policy_world.parent, title="filtered")
    url, payload = editor(policy_routes, policy_world, edit_only=False)
    prefix = f"books-{policy_world.parent.pk}-0"
    payload["name"] = "Must not save"
    payload[f"{prefix}-0-title"] = "must not edit"
    if variant == "lower-initial":
        payload[f"{prefix}-INITIAL_FORMS"] = "0"
    elif variant == "raise-initial":
        payload[f"{prefix}-INITIAL_FORMS"] = "2"
    elif variant.endswith("-extra"):
        payload[f"{prefix}-1-id"] = {
            "authorized-extra": str(policy_world.book.pk),
            "foreign-extra": str(foreign.pk),
            "filtered-extra": str(filtered.pk),
            "malformed-extra": "bad-pk",
        }[variant]
        payload[f"{prefix}-1-title"] = "replacement"
    elif variant == "negative-initial":
        payload[f"{prefix}-INITIAL_FORMS"] = "-1"
    elif variant == "negative-total":
        payload[f"{prefix}-TOTAL_FORMS"] = "-1"
    elif variant == "initial-over-total":
        payload[f"{prefix}-INITIAL_FORMS"] = "3"
    elif variant == "missing-management":
        del payload[f"{prefix}-INITIAL_FORMS"]
    elif variant == "malformed-management":
        payload[f"{prefix}-INITIAL_FORMS"] = "invalid"
    saves = observe_saves(monkeypatch)
    policy = observe_policy(monkeypatch)
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 200
    errors = response.context["formsets"].x_formsets[0].instance.non_form_errors().as_data()
    code = "missing_management_form" if variant in {"missing-management", "malformed-management"} else "cv_invalid_row"
    assert code in [e.code for e in errors]
    assert policy
    assert saves == []
    policy_world.parent.refresh_from_db()
    policy_world.book.refresh_from_db()
    assert policy_world.parent.name == "Original"
    assert policy_world.book.title == "book"
    assert not Book.objects.filter(title="replacement").exists()


def test_identity_must_match_bound_instance(policy_routes, policy_world):
    other = Book.objects.create(publisher=policy_world.parent, title="other authorized")
    _, payload = editor(policy_routes, policy_world, edit_only=False)
    tree = runtime(policy_routes, policy_world, payload, edit_only=False)
    row = tree.x_formsets[0].forms[0].form
    # Simulate custom construction binding a different authorized row. Membership alone is insufficient.
    row.instance = other
    assert tree.all_valid() is False
    assert tree.x_formsets[0].instance.non_form_errors().as_data()[0].code == "cv_invalid_row"


def test_permitted_new_rows_save_with_blank_id(policy_routes, policy_world):
    url, payload = editor(policy_routes, policy_world, edit_only=False)
    prefix = f"books-{policy_world.parent.pk}-0"
    assert payload[f"{prefix}-1-id"] == ""
    payload[f"{prefix}-1-title"] = "legitimate new row"
    response = policy_routes.client.post(url, payload)
    assert response.status_code == 302
    assert Book.objects.get(title="legitimate new row").publisher_id == policy_world.parent.pk


def uuid_runtime(family, author, payload, *, queryset=None):
    class UUIDFormSet(family):
        def get_queryset(self):
            return super().get_queryset() if queryset is None else queryset

    klass = inlineformset_factory(
        Author,
        UUIDFragmentRow,
        formset=UUIDFormSet,
        form=CrispyModelForm,
        fields=["text"],
        extra=1,
    )
    main_class = modelform_factory(Author, form=CrispyModelForm, fields=["first_name", "last_name"])
    main = main_class(cv_view=None, instance=author, data=payload)
    assert main.is_valid()
    tree = FormSets(formsets=OrderedDict(rows=FormSet(title="Rows", klass=klass)))
    tree.init(RequestFactory().post("/", payload), main)
    return tree


@pytest.mark.parametrize("family", [PolicyPackageInlineFormSet, PolicyNativeInlineFormSet], ids=["package", "native"])
@pytest.mark.parametrize("identity", ["missing", "malformed", "nonexistent", "valid"])
def test_uuid_existing_identity_and_unsaved_default_are_distinct(family, identity):
    author = Author.objects.create(first_name="Ursula", last_name="Le Guin")
    row = UUIDFragmentRow.objects.create(author=author, text="original")
    prefix = f"rows-{author.pk}-0"
    payload = {
        "first_name": "Ursula",
        "last_name": "Le Guin",
        f"{prefix}-TOTAL_FORMS": "2",
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": {
            "missing": "",
            "malformed": "bad-pk",
            "nonexistent": str(uuid.uuid4()),
            "valid": str(row.pk),
        }[identity],
        f"{prefix}-0-text": "edited",
        f"{prefix}-1-id": "",
        f"{prefix}-1-text": "new default UUID",
    }
    tree = uuid_runtime(family, author, payload)
    extra = tree.x_formsets[0].forms[1].form.instance
    assert isinstance(extra.pk, uuid.UUID)
    assert extra._state.adding is True
    assert tree.all_valid() is (identity == "valid")
    if identity == "valid":
        tree.save()
        row.refresh_from_db()
        assert row.text == "edited"
        assert UUIDFragmentRow.objects.get(text="new default UUID").author_id == author.pk
    else:
        errors = tree.x_formsets[0].instance.non_form_errors().as_data()
        assert [(e.code, e.messages) for e in errors] == [("cv_invalid_row", ["Invalid row."])]


@pytest.mark.django_db(databases=["default", "shard"])
@pytest.mark.parametrize("family", [PolicyPackageInlineFormSet, PolicyNativeInlineFormSet], ids=["package", "native"])
def test_authorized_membership_uses_queryset_database(family, database_routes, django_assert_num_queries):
    author = Author.objects.using("shard").create(first_name="Shard", last_name="Author")
    row = UUIDFragmentRow.objects.using("shard").create(author=author, text="authorized only on shard")
    prefix = f"rows-{author.pk}-0"
    payload = {
        "first_name": "Shard",
        "last_name": "Author",
        f"{prefix}-TOTAL_FORMS": "1",
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": str(row.pk),
        f"{prefix}-0-text": "edited on shard",
    }
    # Construction follows the selected shard; subsequent policy must retain
    # the explicitly selected queryset even after the ambient router changes.
    with database_routes("shard"):
        tree = uuid_runtime(
            family, author, payload, queryset=UUIDFragmentRow.objects.using("shard").filter(author=author)
        )
        assert tree.x_formsets[0].instance.is_valid()
        assert tree.x_formsets[0].instance.get_queryset().db == "shard"
    with database_routes("default"), django_assert_num_queries(0, using="default"):
        assert tree.all_valid() is True
    assert not UUIDFragmentRow.objects.using("default").filter(pk=row.pk).exists()
