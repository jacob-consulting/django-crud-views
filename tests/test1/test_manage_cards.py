"""Prepared core manage diagnostics and their real request adapter."""

import re
from html.parser import HTMLParser
from uuid import uuid4

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test.utils import CaptureQueriesContext
from lxml import html as html_parser

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


@pytest.mark.parametrize("single_column", [False, True])
def test_core_permission_card_real_request(client, cv_author, developer, monkeypatch, single_column):
    if single_column:
        permission = cv_author.permissions["view"]
        monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {"view": permission}))
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
    assert {row["key"] for row in view.get_manage_views(cv_publisher, developer)} == set(cv_publisher.get_all_views())


@pytest.mark.parametrize("method", ["get_manage_permissions", "get_manage_actor_row"])
def test_absent_manage_fails_before_queries(no_manage_viewset, developer, django_assert_num_queries, method):
    assert "manage" not in no_manage_viewset.get_all_views()
    assert callable(getattr(ManageView(), method, None)), "Explicit builder must exist"
    with (
        django_assert_num_queries(0),
        pytest.raises(ImproperlyConfigured, match=r"^Manage diagnostics require a registered manage view$"),
    ):
        getattr(ManageView(), method)(no_manage_viewset, developer)
    with django_assert_num_queries(0):
        assert ManageView().get_manage_views(no_manage_viewset, developer) == []


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


def test_direct_holders_are_pivoted_by_pk(cv_author, developer, django_user_model, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    shared = Group.objects.create(name="Shared label")
    other = Group.objects.create(name="Other holder")
    user = django_user_model.objects.create_user(username=shared.name)
    member = django_user_model.objects.create_user(username="Only inherited")
    member.groups.add(shared)
    grant(shared, cv_author, "view")
    grant(shared, cv_author, "change")
    grant(other, cv_author, "add")
    user.user_permissions.add(*shared.permissions.all())
    view = cv_author.get_view_class("manage")()
    matrix = view.get_manage_permissions(cv_author, developer)
    assert len(matrix["groups"]) == 2, "Direct group grants must form holder rows"
    rows = {row["id"]: row for row in matrix["groups"]}
    assert set(rows) == {shared.pk, other.pk}
    assert rows[shared.pk]["member_count"] == 1
    assert {c["key"] for c in rows[shared.pk]["cells"] if c["model"]} == {"view", "change"}
    assert all(c["object_count"] is None for row in rows.values() for c in row["cells"])
    assert [(row["id"], row["label"]) for row in matrix["users"]] == [(user.pk, shared.name)]
    before_cells = rows[shared.pk]["cells"]
    shared.name = "Renamed holder"
    shared.save(update_fields=["name"])
    user.username = "Renamed user"
    user.save(update_fields=["username"])
    renamed = view.get_manage_permissions(cv_author, developer)
    assert next(row for row in renamed["groups"] if row["id"] == shared.pk)["cells"] == before_cells
    assert renamed["users"][0]["id"] == user.pk
    assert renamed["users"][0]["cells"] == matrix["users"][0]["cells"]
    assert renamed["users"][0]["label"] == "Renamed user"


@pytest.mark.parametrize("count", [0, 1, 20, 21])
def test_users_fold_after_twenty(client, cv_author, developer, django_user_model, monkeypatch, count):
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    app, codename = cv_author.permissions["view"].split(".")
    perm = Permission.objects.get(content_type__app_label=app, codename=codename)
    for i in range(count):
        holder = django_user_model.objects.create_user(username=f"Direct {i:02}")
        holder.user_permissions.add(perm)
    client.force_login(developer)
    response = client.get("/author/manage/")
    doc = html_parser.fromstring(response.content)
    rows = doc.cssselect("[data-manage-users] tbody tr[data-holder-id]")
    assert len(rows) == min(count, 20)
    overflow = doc.cssselect("[data-manage-users-overflow]")
    assert bool(overflow) == (count > 20)
    if overflow:
        assert overflow[0].cssselect("summary")[0].text_content().strip() == "+ 1 more"
        assert len(overflow[0].cssselect("table thead th")) == len(cv_author.permissions) + 1
        assert len(overflow[0].cssselect("tbody tr")) == 1
        assert not overflow[0].get("open")
    assert not doc.cssselect("tbody > details")
    assert all(TableWrappers(response.content.decode()).tables)
    if count == 0:
        assert "No users hold these permissions directly." in doc.text_content()


def test_hidden_users_and_active_superuser_counts(client, cv_author, developer, django_user_model, monkeypatch):
    active = django_user_model.objects.create_user(username="Secret superuser", is_superuser=True)
    django_user_model.objects.create_user(username="Inactive root", is_superuser=True, is_active=False)
    direct = django_user_model.objects.create_user(username="Secret direct")
    direct.user_permissions.add(Permission.objects.get(codename="view_author", content_type__app_label="app"))
    client.force_login(developer)
    for show in [False, True]:
        monkeypatch.setattr(crud_views_settings, "manage_show_users", show)
        response = client.get("/author/manage/")
        html = response.content.decode()
        matrix = response.context["manage_permissions"]
        assert matrix["superusers"]["count"] == 1
        assert matrix["superusers"]["names"] == ([active.username] if show else [])
        assert ("Secret superuser" in html) is show
        assert ("Secret direct" in html) is show
        assert ("data-manage-users" in html) is show
        assert "Inactive root" not in html
        assert "1 active superuser holds every permission" in html


@pytest.mark.parametrize("holder_count", [1, 21])
@pytest.mark.parametrize("column_count", [1, 4])
def test_holder_queries_are_batched(cv_author, developer, monkeypatch, django_user_model, holder_count, column_count):
    permissions = dict(list(cv_author.permissions.items())[:column_count])
    monkeypatch.setattr(ViewSet, "permissions", property(lambda self: permissions))
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    for i in range(holder_count):
        group = Group.objects.create(name=f"Batch {i:02}")
        holder = django_user_model.objects.create_user(username=f"Batch {i:02}")
        for key in permissions:
            grant(group, cv_author, key)
        holder.groups.add(group)
        holder.user_permissions.add(*group.permissions.all())
    # Warm only actor backend caches; holder lookups and aggregates remain measured.
    developer.get_all_permissions()
    with CaptureQueriesContext(connection) as captured:
        matrix = ManageView().get_manage_permissions(cv_author, developer)
    assert len(matrix["groups"]) == holder_count
    assert len(matrix["users"]) + len(matrix["users_overflow"]) == holder_count
    assert len(captured) == 5  # groups, users, member aggregate, superuser count, superuser names
    assert sum("COUNT(" in query["sql"].upper() for query in captured) == 2


def test_empty_and_custom_vocabulary(client, cv_author, developer, monkeypatch):
    perm = Permission.objects.create(
        content_type=Permission.objects.get(codename="view_author", content_type__app_label="app").content_type,
        codename="audit_author",
        name="Audit author",
    )
    group = Group.objects.create(name="Auditors")
    group.permissions.add(perm)
    monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {"audit": "app.audit_author"}))
    matrix = ManageView().get_manage_permissions(cv_author, developer)
    assert matrix["columns"] == [{"key": "audit", "permission": "app.audit_author", "codename": "audit_author"}]
    assert matrix["groups"][0]["cells"] == [{"key": "audit", "model": True, "object_count": None}]
    monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {}))
    client.force_login(developer)
    response = client.get("/author/manage/")
    assert "No permissions configured." in response.content.decode()
    assert response.context["manage_permissions"]["groups"] == []


def test_stock_render_does_not_evaluate_legacy_getters(client, cv_author, developer, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Stock core rendering must not evaluate a legacy getter")

    cls = cv_author.get_view_class("manage")
    monkeypatch.setattr(cls, "get_view_data", forbidden)
    monkeypatch.setattr(cls, "get_permission_holders", forbidden)
    client.force_login(developer)
    response = client.get("/author/manage/")
    assert response.status_code == 200
    rows = response.context["manage_views"]
    assert {row["key"] for row in rows} == set(cv_author.get_all_views())
    for row in rows:
        view = cv_author.get_view_class(row["key"])
        assert row["class_path"] == f"{view.__module__}.{view.__qualname__}"
