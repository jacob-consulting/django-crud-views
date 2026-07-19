"""Breadcrumb models, mixin and template tag tests."""

import pytest
from django.utils.translation import gettext_lazy
from pydantic import ValidationError

from crud_views.lib.breadcrumb import Breadcrumb, BreadcrumbItem
from crud_views.lib.settings import crud_views_settings


class TestBreadcrumbItem:
    def test_plain_title_without_url(self):
        item = BreadcrumbItem(title="Home")
        assert item.title == "Home"
        assert item.url_name is None
        assert item.resolve() == {"title": "Home", "url": None}

    def test_lazy_title_is_coerced(self):
        item = BreadcrumbItem(title=gettext_lazy("Home"))
        assert isinstance(item.title, str)
        assert item.title == "Home"

    def test_args_and_kwargs_cleared_without_url_name(self):
        item = BreadcrumbItem(title="Home", args=(1,), kwargs={"pk": 1})
        assert item.args == ()
        assert item.kwargs == {}

    def test_args_and_kwargs_are_mutually_exclusive(self):
        with pytest.raises(ValidationError):
            BreadcrumbItem(title="X", url_name="author-detail", args=(1,), kwargs={"pk": 1})

    @pytest.mark.django_db
    def test_resolve_with_kwargs(self, author_douglas_adams):
        item = BreadcrumbItem(title="Douglas", url_name="author-detail", kwargs={"pk": author_douglas_adams.pk})
        resolved = item.resolve()
        assert resolved["title"] == "Douglas"
        assert str(author_douglas_adams.pk) in resolved["url"]

    @pytest.mark.django_db
    def test_resolve_with_args(self, author_douglas_adams):
        item = BreadcrumbItem(title="Douglas", url_name="author-detail", args=(author_douglas_adams.pk,))
        assert str(author_douglas_adams.pk) in item.resolve()["url"]


class TestBreadcrumb:
    def test_empty(self):
        assert Breadcrumb().resolve_items() == []

    def test_resolve_items_order(self):
        bc = Breadcrumb(items=(BreadcrumbItem(title="A"), BreadcrumbItem(title="B")))
        assert [i["title"] for i in bc.resolve_items()] == ["A", "B"]

    def test_items_coerced_to_tuple(self):
        bc = Breadcrumb(items=[BreadcrumbItem(title="A")])
        assert isinstance(bc.items, tuple)


class TestBreadcrumbPrefixSetting:
    def test_default_is_empty(self):
        assert crud_views_settings.breadcrumb_prefix == []

    def test_valid_prefix_produces_no_e102(self, monkeypatch):
        monkeypatch.setattr(crud_views_settings, "breadcrumb_prefix", [{"title": "Home", "url_name": "author-list"}])
        assert not [m for m in crud_views_settings.check_messages if m.id == "crud_views.E102"]

    def test_malformed_prefix_produces_e102(self, monkeypatch):
        monkeypatch.setattr(crud_views_settings, "breadcrumb_prefix", [{"url_name": "author-list"}])  # no title
        assert [m for m in crud_views_settings.check_messages if m.id == "crud_views.E102"]

    def test_non_dict_prefix_entry_produces_e102(self, monkeypatch):
        monkeypatch.setattr(crud_views_settings, "breadcrumb_prefix", ["not-a-dict"])
        assert [m for m in crud_views_settings.check_messages if m.id == "crud_views.E102"]
