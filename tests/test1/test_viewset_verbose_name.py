"""#338: ViewSet label overrides preserve defaults and reach rendered labels."""

import pytest
from django.urls import reverse
from django.utils import translation
from django.utils.functional import Promise, lazy
from django.utils.translation import gettext_lazy
from lxml import html as lxml_html
from pydantic import ValidationError

from crud_views.lib.view import ViewContext
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.app.resources import cv_s3file
from tests.test1.app.views import BookListView, cv_book


def _meta(viewset):
    return {k: v for k, v in viewset.get_meta(ViewContext(view=BookListView())).items() if k.startswith("verbose")}


def _explode():
    raise AssertionError("lazy label evaluated at construction")


@pytest.fixture(scope="module")
def guardian_probe():
    # Registry names are process-global: register once, remove on teardown.
    vs = GuardianViewSet(
        model=Publisher,
        name="guardian_verbose_name_probe",
        verbose_name="house",
        verbose_name_plural="houses",
    )
    try:
        yield vs
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(vs.name, None)


def test_unset_reproduces_model_values():
    assert _meta(cv_book) == {
        "verbose_name": "Book",
        "verbose_name_plural": "Books",
        "verbose_name_translate": "Book",
        "verbose_name_plural_translate": "Books",
    }
    assert isinstance(cv_book.get_meta(ViewContext(view=BookListView()))["verbose_name_plural"], Promise)


@pytest.mark.django_db
def test_list_header_follows_plural_override(client_user_book_view, publisher_penguin, monkeypatch):
    monkeypatch.setattr(cv_book, "verbose_name_plural", "volumes")
    response = client_user_book_view.get(
        reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    )
    assert response.status_code == 200
    title = lxml_html.fromstring(response.content).cssselect("[data-test-page-title]")[0]
    assert " ".join(title.text_content().split()) == "Volumes"
    assert response.context["view"].cv_header == "Volumes"


def test_unset_reproduces_resource_values():
    assert _meta(cv_s3file) == {
        "verbose_name": "S3 file",
        "verbose_name_plural": "S3 files",
        "verbose_name_translate": "S3 file",
        "verbose_name_plural_translate": "S3 files",
    }


def test_resource_override_beats_resource_meta(monkeypatch):
    monkeypatch.setattr(cv_s3file, "verbose_name", "object")
    assert _meta(cv_s3file)["verbose_name"] == "Object"
    assert _meta(cv_s3file)["verbose_name_plural"] == "S3 files"


def test_singular_only_changes_only_singular_keys(monkeypatch):
    monkeypatch.setattr(cv_book, "verbose_name", "volume")
    assert _meta(cv_book) == {
        "verbose_name": "Volume",
        "verbose_name_plural": "Books",
        "verbose_name_translate": "Volume",
        "verbose_name_plural_translate": "Books",
    }


def test_plural_only_changes_only_plural_keys(monkeypatch):
    monkeypatch.setattr(cv_book, "verbose_name_plural", "volumes")
    assert _meta(cv_book) == {
        "verbose_name": "Book",
        "verbose_name_plural": "Volumes",
        "verbose_name_translate": "Book",
        "verbose_name_plural_translate": "Volumes",
    }


def test_lazy_override_translates_at_call_time(monkeypatch):
    monkeypatch.setattr(cv_book, "verbose_name", gettext_lazy("Delete"))
    assert _meta(cv_book)["verbose_name"] == "Delete"
    with translation.override("de"):
        meta = _meta(cv_book)
        assert meta["verbose_name"] == "Löschen"
        assert meta["verbose_name_translate"] == "Löschen"
        assert meta["verbose_name_plural"] == "Books"
    assert _meta(cv_book)["verbose_name"] == "Delete"


@pytest.mark.parametrize("value", ["", "  "])
@pytest.mark.parametrize("field", ["verbose_name", "verbose_name_plural"])
def test_blank_plain_str_rejected(field, value):
    try:
        with pytest.raises(ValidationError, match=field):
            ViewSet(model=Book, name="verbose_name_blank_probe", **{field: value})
    finally:
        # Validation fails before register(); this no-op also isolates the RED run.
        with _REGISTRY_LOCK:
            _REGISTRY.pop("verbose_name_blank_probe", None)


def test_lazy_value_is_not_evaluated_or_blank_checked():
    probe = lazy(_explode, str)()
    assert isinstance(probe, Promise)
    assert ViewSet.check_verbose_name(probe) is probe
    assert ViewSet.check_verbose_name(None) is None
    assert ViewSet.check_verbose_name(" volume ") == " volume "
    try:
        vs = ViewSet(model=Book, name="verbose_name_lazy_probe", verbose_name=probe)
        assert vs.verbose_name is probe
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop("verbose_name_lazy_probe", None)
    try:
        vs = ViewSet(model=Book, name="verbose_name_padded_probe", verbose_name=" volume ")
        assert vs.verbose_name == " volume "
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop("verbose_name_padded_probe", None)


def test_guardian_viewset_accepts_the_fields(guardian_probe):
    assert guardian_probe.verbose_name == "house"
    assert guardian_probe.verbose_name_plural == "houses"
    assert _meta(guardian_probe) == {
        "verbose_name": "House",
        "verbose_name_plural": "Houses",
        "verbose_name_translate": "House",
        "verbose_name_plural_translate": "Houses",
    }
