"""#338: ViewSet label overrides preserve defaults and reach rendered labels."""

import pytest
from django.urls import reverse
from django.utils.functional import Promise
from lxml import html as lxml_html

from crud_views.lib.view import ViewContext
from tests.test1.app.views import BookListView, cv_book


def _meta(viewset):
    return {k: v for k, v in viewset.get_meta(ViewContext(view=BookListView())).items() if k.startswith("verbose")}


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
