"""Breadcrumb models, mixin and template tag tests."""

import pytest
from django.http import Http404
from django.test import RequestFactory
from django.utils.translation import gettext_lazy
from pydantic import ValidationError

from crud_views.lib.breadcrumb import Breadcrumb, BreadcrumbItem
from crud_views.lib.settings import crud_views_settings
from tests.test1.app.models import Book, BookNote, Publisher


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


def make_view(view_class, url, obj=None, **url_kwargs):
    """Instantiate a CrudView the way Django does for a GET request."""
    view = view_class()
    request = RequestFactory().get(url)
    view.setup(request, **url_kwargs)
    if obj is not None:
        view.object = obj
    return view


def titles(breadcrumb):
    return [item.title for item in breadcrumb.items]


def urls(breadcrumb):
    return [item["url"] for item in breadcrumb.resolve_items()]


@pytest.mark.django_db
class TestBreadcrumbTopLevel:
    def test_list_view_trail(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcListView

        view = make_view(PublisherBcListView, "/publisher_bc/")
        bc = view.cv_breadcrumb()
        assert titles(bc) == ["Publishers"]
        assert urls(bc) == ["/publisher_bc/"]

    def test_detail_view_trail(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcDetailView

        view = make_view(
            PublisherBcDetailView,
            f"/publisher_bc/{publisher_penguin.pk}/detail",
            publisher_penguin,
            pk=publisher_penguin.pk,
        )
        bc = view.cv_breadcrumb()
        assert titles(bc) == ["Publishers", str(publisher_penguin)]

    def test_update_view_trail_links_object_to_detail(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcUpdateView

        view = make_view(
            PublisherBcUpdateView,
            f"/publisher_bc/{publisher_penguin.pk}/update",
            publisher_penguin,
            pk=publisher_penguin.pk,
        )
        bc = view.cv_breadcrumb()
        # container, object (links to detail), action label (current page)
        assert len(bc.items) == 3
        assert titles(bc)[0] == "Publishers"
        assert titles(bc)[1] == str(publisher_penguin)
        assert f"/publisher_bc/{publisher_penguin.pk}/detail" in urls(bc)[1]

    def test_create_view_trail(self):
        from tests.test1.app.views import PublisherBcCreateView

        view = make_view(PublisherBcCreateView, "/publisher_bc/create")
        bc = view.cv_breadcrumb()
        assert titles(bc)[0] == "Publishers"
        assert len(bc.items) == 2  # container + action label
        assert bc.items[1].url_name is None  # action label (current page) is unlinked

    def test_no_detail_view_renders_object_unlinked(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcNodetailUpdateView

        view = make_view(
            PublisherBcNodetailUpdateView,
            f"/publisher_bc_nodetail/{publisher_penguin.pk}/update",
            publisher_penguin,
            pk=publisher_penguin.pk,
        )
        bc = view.cv_breadcrumb()
        object_item = bc.items[1]
        assert object_item.title == str(publisher_penguin)
        assert object_item.url_name is None

    def test_card_container_fallback(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcCardDetailView

        view = make_view(
            PublisherBcCardDetailView,
            f"/publisher_bc_card/{publisher_penguin.pk}/detail",
            publisher_penguin,
            pk=publisher_penguin.pk,
        )
        bc = view.cv_breadcrumb()
        assert bc.items[0].url_name == "publisher_bc_card-card"

    def test_memoization_returns_same_object(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcListView

        view = make_view(PublisherBcListView, "/publisher_bc/")
        assert view.cv_breadcrumb() is view.cv_breadcrumb()

    def test_context_data_contains_breadcrumb(self, client, publisher_penguin):
        response = client.get("/publisher_bc/")
        assert response.status_code == 200
        assert "cv_breadcrumb" in response.context


@pytest.mark.django_db
class TestBreadcrumbPrefix:
    def test_prefix_from_setting(self, monkeypatch, publisher_penguin):
        from tests.test1.app.views import PublisherBcListView

        monkeypatch.setattr(
            crud_views_settings, "breadcrumb_prefix", [{"title": "Home", "url_name": "publisher_bc-list"}]
        )
        view = make_view(PublisherBcListView, "/publisher_bc/")
        assert titles(view.cv_breadcrumb())[0] == "Home"

    def test_prefix_method_override(self, publisher_penguin):
        from tests.test1.app.views import PublisherBcListView
        from crud_views.lib.breadcrumb import BreadcrumbItem

        class MyView(PublisherBcListView):
            def cv_breadcrumb_prefix(self):
                return [BreadcrumbItem(title="Host"), BreadcrumbItem(title="Section")]

        view = make_view(MyView, "/publisher_bc/")
        assert titles(view.cv_breadcrumb())[:2] == ["Host", "Section"]

    def test_container_label_override(self, monkeypatch, publisher_penguin):
        from tests.test1.app.views import PublisherBcDetailView, PublisherBcListView

        # the override lives on the viewset's registered container view class; patch it there
        monkeypatch.setattr(PublisherBcListView, "cv_breadcrumb_container_label", "All publishers")
        view = make_view(
            PublisherBcDetailView,
            f"/publisher_bc/{publisher_penguin.pk}/detail",
            publisher_penguin,
            pk=publisher_penguin.pk,
        )
        assert titles(view.cv_breadcrumb())[0] == "All publishers"


@pytest.fixture
def bc_chain(db):
    publisher = Publisher.objects.create(name="Penguin BC")
    book = Book.objects.create(title="Hitchhiker BC", publisher=publisher)
    note = BookNote.objects.create(book=book, note="First note")
    return publisher, book, note


@pytest.mark.django_db
class TestBreadcrumbAncestors:
    def _note_detail_view(self, publisher, book, note):
        from tests.test1.app.views import BookNoteBcDetailView

        url = f"/publisher_bc/{publisher.pk}/book_bc/{book.pk}/booknote_bc/{note.pk}/detail"
        return make_view(
            BookNoteBcDetailView,
            url,
            note,
            publisher_bc_pk=publisher.pk,
            book_bc_pk=book.pk,
            pk=note.pk,
        )

    def test_deep_chain_titles(self, bc_chain):
        publisher, book, note = bc_chain
        bc = self._note_detail_view(publisher, book, note).cv_breadcrumb()
        assert titles(bc) == [
            "Publishers",
            str(publisher),
            "Books",
            str(book),
            "Book notes",
            str(note),
        ]

    def test_deep_chain_urls_resolve(self, bc_chain):
        publisher, book, note = bc_chain
        bc = self._note_detail_view(publisher, book, note).cv_breadcrumb()
        resolved = bc.resolve_items()
        # ancestor object items link to their detail views with full chain kwargs
        assert resolved[1]["url"] == f"/publisher_bc/{publisher.pk}/detail/"
        assert resolved[3]["url"] == f"/publisher_bc/{publisher.pk}/book_bc/{book.pk}/detail/"
        # container items carry the chain kwargs of their level
        assert resolved[2]["url"] == f"/publisher_bc/{publisher.pk}/book_bc/"
        assert resolved[4]["url"] == f"/publisher_bc/{publisher.pk}/book_bc/{book.pk}/booknote_bc/"

    def test_child_list_view_trail(self, bc_chain):
        from tests.test1.app.views import BookBcListView

        publisher, book, note = bc_chain
        view = make_view(BookBcListView, f"/publisher_bc/{publisher.pk}/book_bc/", publisher_bc_pk=publisher.pk)
        assert titles(view.cv_breadcrumb()) == ["Publishers", str(publisher), "Books"]

    def test_tampered_parent_pk_raises_404(self, bc_chain):
        publisher, book, note = bc_chain
        other = Publisher.objects.create(name="Other House")
        # note's real book under a foreign publisher pk: ancestor lookup must 404, not leak
        view = self._note_detail_view(other, book, note)
        with pytest.raises(Http404):
            view.cv_breadcrumb()

    def test_ancestor_query_count(self, bc_chain, django_assert_num_queries):
        publisher, book, note = bc_chain
        view = self._note_detail_view(publisher, book, note)
        with django_assert_num_queries(2):  # one per ancestor level: book, publisher
            view.cv_breadcrumb()
        with django_assert_num_queries(0):  # memoized
            view.cv_breadcrumb()

    def test_ancestor_without_detail_view_is_unlinked(self, monkeypatch, bc_chain):
        from tests.test1.app.views import BookBcDetailView, cv_publisher_bc

        publisher, book, note = bc_chain
        # simulate an ancestor viewset without a detail view; monkeypatch restores _views
        monkeypatch.delitem(cv_publisher_bc._views, "detail")
        view = make_view(
            BookBcDetailView,
            f"/publisher_bc/{publisher.pk}/book_bc/{book.pk}/detail",
            book,
            publisher_bc_pk=publisher.pk,
            pk=book.pk,
        )
        bc = view.cv_breadcrumb()
        publisher_item = next(item for item in bc.items if item.title == str(publisher))
        assert publisher_item.url_name is None
