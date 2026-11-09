"""#338: ViewSet overrides reach default labels without registering new views.

Breadcrumb coverage uses cv_book_bc because only its views carry the breadcrumb mixin.
Message coverage asserts cv_get_message() because Book views do not carry MessageMixin.
"""

import pytest
from django.urls import reverse
from lxml import html as lxml_html

from tests.test1.app.models import Book
from tests.test1.app.views import BookCreateView, BookListView, cv_book
from tests.test1.test_breadcrumb import make_view


def _override(monkeypatch):
    monkeypatch.setattr(cv_book, "verbose_name", "volume")
    monkeypatch.setattr(cv_book, "verbose_name_plural", "volumes")


def _page_title(response):
    return " ".join(
        lxml_html.fromstring(response.content).cssselect("[data-test-page-title]")[0].text_content().split()
    )


def _page_paragraph(response):
    # cv_paragraph is direct header text; the heading and toolbar labels are nested in the d-flex div.
    header = lxml_html.fromstring(response.content).cssselect("div.card-header")[0]
    return " ".join("".join(header.xpath("text()")).split())


@pytest.mark.django_db
def test_list_header_and_paragraph_follow_override(client_user_book_view, publisher_penguin, monkeypatch):
    _override(monkeypatch)
    response = client_user_book_view.get(
        reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    )
    assert response.status_code == 200
    view = response.context["view"]
    assert _page_title(response) == "Volumes"
    assert _page_paragraph(response) == "List of all Volumes"
    assert view.cv_header == "Volumes"
    assert view.cv_paragraph == "List of all Volumes"


@pytest.mark.django_db
def test_create_header_and_paragraph_follow_override(client_user_book_add, publisher_penguin, monkeypatch):
    _override(monkeypatch)
    response = client_user_book_add.get(
        reverse(cv_book.get_router_name("create"), kwargs={"publisher_pk": publisher_penguin.pk})
    )
    assert response.status_code == 200
    view = response.context["view"]
    assert _page_title(response) == "Volume"
    assert _page_paragraph(response) == "Create new Volume"
    assert view.cv_header == "Volume"
    assert view.cv_paragraph == "Create new Volume"


@pytest.mark.django_db
def test_view_header_template_code_beats_override(client_user_book_view, publisher_penguin, monkeypatch):
    _override(monkeypatch)
    monkeypatch.setattr(BookListView, "cv_header_template_code", "Custom header")
    response = client_user_book_view.get(
        reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    )
    assert response.status_code == 200
    view = response.context["view"]
    assert _page_title(response) == "Custom header"
    assert view.cv_header == "Custom header"
    assert _page_paragraph(response) == "List of all Volumes"
    assert view.cv_paragraph == "List of all Volumes"


@pytest.mark.django_db
def test_success_message_follows_override(publisher_penguin, monkeypatch):
    """Assert the producer string MessageMixin.cv_form_valid_hook would post.

    BookCreateView has no MessageMixin: message delivery is not exercised for Book views
    in this phase. test_nested_viewset.py::test_child_create_book covers the POST, not a message.
    """
    _override(monkeypatch)
    book = Book.objects.create(title="1984", publisher=publisher_penguin)
    view = make_view(
        BookCreateView,
        f"/publisher/{publisher_penguin.pk}/book/create/",
        obj=book,
        publisher_pk=publisher_penguin.pk,
    )
    assert view.cv_get_message() == "Created Volume <strong>1984</strong>"
