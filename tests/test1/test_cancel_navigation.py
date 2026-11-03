"""Request-level cancel navigation, following the links actually rendered to users."""

from html import unescape
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core import signing
from django_filters import FilterSet

from crud_views.lib.session import SessionData
from crud_views.lib.views.mixins import ListViewTableFilterMixin
from tests.test1.app.models import Author


def emitted_link(response, path):
    links = [unescape(link) for link in re.findall(r'href="([^"]+)"', response.content.decode())]
    return next(link for link in links if urlsplit(link).path == path)


def rendered_cancel(response):
    node = re.search(r'data-cv-cancel-url="([^"]+)"', response.content.decode())
    assert node is not None, "resolved Cancel must be rendered"
    return unescape(node.group(1))


@pytest.mark.django_db
def test_emitted_list_update_round_trip(
    client_user_author_origin, cv_author_origin, author_douglas_adams, author_terry_pratchett, monkeypatch
):
    from django.test import override_settings
    from django.urls import path

    original = cv_author_origin.get_view_class("list")

    class AuthorFilter(FilterSet):
        class Meta:
            model = Author
            fields = ["last_name"]

    class FilteredAuthors(ListViewTableFilterMixin, original):
        cv_viewset = None
        filterset_class = AuthorFilter

    monkeypatch.setattr(FilteredAuthors, "cv_viewset", cv_author_origin)
    monkeypatch.setattr(cv_author_origin.get_view_class("update"), "cv_cancel_keys", "auto")
    from tests.test1.app.urls import urlpatterns
    from django.urls import reverse

    before = list(Author.objects.order_by("pk").values())
    list_url = reverse(cv_author_origin.get_router_name("list"))
    with override_settings(ROOT_URLCONF=type("URLs", (), {"urlpatterns": [path(list_url.lstrip("/"), FilteredAuthors.as_view()), *urlpatterns]})):
        response = client_user_author_origin.get(list_url + "?last_name=Adams")
        assert response.status_code == 200
        view = response.context["view"]
        update = emitted_link(response, view.cv_get_url("update", author_douglas_adams))
        query = parse_qs(urlsplit(update).query)
        assert "cv_from_cancel" in query, "rendered Update link must own its captured query"
        payload = signing.Signer(salt="crud_views.cancel.v1").unsign_object(query["cv_from_cancel"][0])
        assert payload["query"] == "last_name=Adams", "decoded capture"
        form = client_user_author_origin.get(update)
        cancel = rendered_cancel(form)
        assert parse_qs(urlsplit(cancel).query) == {"last_name": ["Adams"], "cv_from_restore": ["1"]}
        client_user_author_origin.get(list_url + "?last_name=Pratchett")
        returned = client_user_author_origin.get(cancel)
        assert list(returned.context["object_list"]) == [author_douglas_adams], "returned records"
        assert SessionData.from_view(returned.context["view"]).get("filter_query_string") == "last_name=Adams"
    assert list(Author.objects.order_by("pk").values()) == before, "Cancel performs no model writes"
