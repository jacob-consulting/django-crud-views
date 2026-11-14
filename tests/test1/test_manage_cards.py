"""Prepared core manage diagnostics and their real request adapter."""

import re
from html.parser import HTMLParser
from uuid import uuid4

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured

from crud_views.lib.resource import Resource
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys

pytestmark = pytest.mark.django_db


class TableWrappers(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.divs = []
        self.tables = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            self.divs.append(dict(attrs).get("class", "").split())
        if tag == "table":
            self.tables.append(any("table-responsive" in classes for classes in self.divs))

    def handle_endtag(self, tag):
        if tag == "div":
            self.divs.pop()


class ManageResource(Resource):
    key: str

    class Meta:
        verbose_name = "manage resource"
        verbose_name_plural = "manage resources"
        pk_field = "key"
        pk_type = PrimaryKeys.HEX


@pytest.fixture
def no_manage_viewset():
    name = "manage_no_class_" + uuid4().hex
    viewset = ViewSet(model=ManageResource, name=name, resource_permissions={"view": "app.view_author"})
    try:
        yield viewset
    finally:
        with _REGISTRY_LOCK:
            assert _REGISTRY[name] is viewset
            del _REGISTRY[name]


@pytest.fixture
def developer(django_user_model):
    actor = django_user_model.objects.create_user(username="<script>developer</script>")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return actor


def grant(group, viewset, key="view"):
    app, codename = viewset.permissions[key].split(".")
    group.permissions.add(Permission.objects.get(content_type__app_label=app, codename=codename))


def test_core_permission_card_real_request(client, cv_author, developer):
    readers = Group.objects.create(name="Card readers")
    grant(readers, cv_author)
    developer.groups.add(readers)
    client.force_login(developer)
    response = client.get("/author/manage/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="cv-manage-permissions"' in html, "The admitted request must render the Permissions card"
    actor = re.search(r"<tr data-manage-actor.*?</tr>", html, re.S).group()
    assert "(you)" in actor
    assert re.search(r'data-permission="view".*?class="badge[^\"]*">model</span>', actor, re.S)
    assert "<script>developer</script>" not in html
    assert "&lt;script&gt;developer&lt;/script&gt;" in html
    assert '#permissions"' in html and 'rel="noopener"' in html
    assert 'class="row g-3"' in html
    assert 'class="col-12 col-lg-8"' in html and 'class="col-12 col-lg-4"' in html
    assert all(TableWrappers(html).tables)


@pytest.mark.parametrize("staff,superuser", [(False, False), (True, False), (True, True)])
def test_card_admission_still_requires_membership(client, cv_author, django_user_model, staff, superuser):
    user = django_user_model.objects.create_user(username="outside", is_staff=staff, is_superuser=superuser)
    client.force_login(user)
    assert client.get("/author/manage/").status_code == 403


def test_builders_use_supplied_viewset_without_request(cv_author, cv_publisher, developer, monkeypatch):
    def poison(self):
        raise AssertionError("Presentation builders must not read request")

    monkeypatch.setattr(ManageView, "request", property(poison), raising=False)
    calls = []
    monkeypatch.setattr("crud_views.lib.views.manage._check_nested_auth", lambda cls, **kw: calls.append((cls, kw)))
    view = cv_author.get_view_class("manage")()
    assert callable(getattr(view, "get_manage_permissions", None)), "Explicit builder must exist"
    data = view.get_manage_permissions(cv_publisher, developer)
    assert [c["permission"] for c in data["columns"]] == list(cv_publisher.permissions.values())
    assert calls and all(cls is cv_publisher.get_view_class("manage") for cls, _ in calls)
    assert all(kw["model"] is cv_publisher.model for _, kw in calls)
    assert data["actor"] == view.get_manage_actor_row(cv_publisher, developer)


@pytest.mark.parametrize("method", ["get_manage_permissions", "get_manage_actor_row"])
def test_absent_manage_fails_before_queries(no_manage_viewset, developer, django_assert_num_queries, method):
    assert "manage" not in no_manage_viewset.get_all_views()
    assert callable(getattr(ManageView(), method, None)), "Explicit builder must exist"
    with (
        django_assert_num_queries(0),
        pytest.raises(ImproperlyConfigured, match=r"^Manage diagnostics require a registered manage view$"),
    ):
        getattr(ManageView(), method)(no_manage_viewset, developer)


def test_disabled_model_still_registers_manage(monkeypatch, cv_author, developer):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    name = "manage_disabled_" + uuid4().hex
    viewset = ViewSet(model=cv_author.model, name=name)
    try:
        assert viewset.get_view_class("manage").__name__ == "AutoManageView"
        assert name + "-manage" in [pattern.name for pattern in viewset.urlpatterns]
        assert not viewset.get_view_class("manage").cv_has_access(developer)
    finally:
        with _REGISTRY_LOCK:
            del _REGISTRY[name]
