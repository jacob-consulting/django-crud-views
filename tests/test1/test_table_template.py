import pytest
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.test.client import Client

from tests.lib.helper.boostrap5 import Table


def test_cv_querystring_preserves_and_replaces_params():
    """cv_querystring delegates to the installed django-tables2 tag (2.x or 3.x)."""
    request = RequestFactory().get("/?page=1&q=foo")
    template = Template('{% load crud_views %}{% cv_querystring "page"="2" %}')

    rendered = template.render(Context({"request": request}))

    assert "page=2" in rendered
    assert "q=foo" in rendered


@pytest.mark.django_db
@override_settings(DJANGO_TABLES2_TEMPLATE="crud_views/table/bootstrap5.html")
def test_list_renders_with_crud_views_table_template(
    client_user_author_view: Client, cv_author, author_douglas_adams, author_terry_pratchett
):
    """The crud_views list table template renders end-to-end via the cv_querystring wrapper."""
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2
