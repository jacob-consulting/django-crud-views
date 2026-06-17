"""Runnability gate for the README "this is all you write" snippet.

Proves the minimal documented ViewSet pattern actually renders. If Variant A
(no explicit ``table_class``) renders, the README uses it; otherwise the README
must ship the explicit ``Table`` of Variant B.
"""

import django_tables2 as tables
import pytest
from django.urls import path, include

from tests.test1.app.models import Author
from crud_views.lib.table import Table
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)

cv_readme = ViewSet(model=Author, name="readme")


class ReadmeAuthorTable(Table):
    first_name = tables.Column()
    last_name = tables.Column()


class ReadmeAuthorList(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_readme
    table_class = ReadmeAuthorTable


class ReadmeAuthorDetail(DetailViewPermissionRequired):
    cv_viewset = cv_readme


class ReadmeAuthorCreate(CreateViewPermissionRequired):
    cv_viewset = cv_readme
    fields = ["first_name", "last_name"]


class ReadmeAuthorUpdate(UpdateViewPermissionRequired):
    cv_viewset = cv_readme
    fields = ["first_name", "last_name"]


class ReadmeAuthorDelete(DeleteViewPermissionRequired):
    cv_viewset = cv_readme


urlpatterns = [path("", include(cv_readme.urlpatterns))]


@pytest.mark.urls("tests.test1.test_readme_snippet")
@pytest.mark.django_db
def test_readme_minimal_list_renders(client_user_author_view):
    # Author "list" view registers at the ViewSet path "readme/"
    response = client_user_author_view.get("/readme/")
    assert response.status_code == 200
