import hashlib

import pytest
from django.test import override_settings
from django.test.client import Client


def md5(key: str) -> str:
    return hashlib.md5(key.encode()).hexdigest()


@pytest.fixture
def s3_bucket():
    """Snapshot/restore the fake bucket so mutating tests stay isolated."""
    from tests.test1.app import resources

    original = [dict(row) for row in resources.FAKE_BUCKET]
    yield resources.FAKE_BUCKET
    resources.FAKE_BUCKET[:] = original


@pytest.mark.django_db
def test_list_renders_rows(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/")
    assert response.status_code == 200
    content = response.content.decode()
    # page 1 of 2 (paginate_by=2); tables2 renders attribute access on Pydantic rows
    assert "reports/2026/q1.pdf" in content
    assert "reports/2026/q2.pdf" in content


@pytest.mark.django_db
def test_list_pagination_page2(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/?page=2")
    assert response.status_code == 200
    assert "images/logo.png" in response.content.decode()


@pytest.mark.django_db
def test_list_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get("/s3file/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_anonymous_redirects_to_login(client: Client):
    response = client.get("/s3file/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_detail_renders_object(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "reports/2026/q1.pdf" in content
    assert "111" in content


@pytest.mark.django_db
def test_detail_unknown_pk_404(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{'0' * 32}/detail/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 403


def test_session_data_app_label_shim():
    """SessionData reads view.model._meta.app_label (session.py:49) — the
    Options shim must satisfy it (spec §3 coupling point 5)."""
    from crud_views.lib.session import SessionData
    from tests.test1.app.resources import S3File

    class _StubView:
        model = S3File

    assert SessionData(view=_StubView()).app_label == "app"


@pytest.mark.django_db
def test_delete_get_renders_confirm_form(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.get(f"/s3file/{md5('images/logo.png')}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "images/logo.png" in content
    assert "<form" in content


@pytest.mark.django_db
def test_delete_post_removes_item_and_redirects(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.post(f"/s3file/{md5('images/logo.png')}/delete/", {})
    assert response.status_code == 302
    assert response.url == "/s3file/"
    assert not any(row["key"] == "images/logo.png" for row in s3_bucket)
    assert len(s3_bucket) == 2


@pytest.mark.django_db
def test_delete_requires_delete_permission(client_user_s3file_view: Client, s3_bucket):
    # view-only user: 403, bucket untouched
    response = client_user_s3file_view.post(f"/s3file/{md5('images/logo.png')}/delete/", {})
    assert response.status_code == 403
    assert len(s3_bucket) == 3


@pytest.mark.django_db
def test_touch_action_success(client_user_s3file_delete: Client, s3_bucket):
    from django.contrib.messages import get_messages

    from tests.test1.app import resources

    resources.TOUCHED.clear()
    response = client_user_s3file_delete.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/")
    assert response.status_code == 302
    assert response.url == "/s3file/"
    assert resources.TOUCHED == ["reports/2026/q1.pdf"]
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("Touched" in m for m in messages)


@pytest.mark.django_db
def test_touch_action_error_branch(client_user_s3file_delete: Client, s3_bucket):
    from django.contrib.messages import get_messages

    from tests.test1.app import resources

    resources.TOUCHED.clear()
    response = client_user_s3file_delete.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/?fail=1")
    assert response.status_code == 302
    assert resources.TOUCHED == []
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("Touch failed" in m for m in messages)


@pytest.mark.django_db
def test_touch_requires_delete_permission(client_user_s3file_view: Client, s3_bucket):
    response = client_user_s3file_view.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_touch_unknown_pk_404(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.post(f"/s3file/{'0' * 32}/touch/")
    assert response.status_code == 404


@pytest.fixture
def nested_bucket(user_s3file_view, cv_publisher):
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app import resources

    # ancestor authorization: reading the Resource leaf under a Publisher requires Publisher view
    user_viewset_permission(user_s3file_view, cv_publisher, "view")

    original = [dict(row) for row in resources.NESTED_BUCKET]
    yield resources.NESTED_BUCKET
    resources.NESTED_BUCKET[:] = original


@pytest.mark.django_db
def test_nested_list_scoped_to_parent(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p1 = Publisher.objects.create(name="Penguin")
    p2 = Publisher.objects.create(name="HarperCollins")
    nested_bucket.extend(
        [
            {"key": f"publisher-{p1.pk}/contract.pdf", "size": 10},
            {"key": f"publisher-{p2.pk}/other.pdf", "size": 20},
        ]
    )

    response = client_user_s3file_view.get(f"/publisher/{p1.pk}/publisherfile/")
    assert response.status_code == 200
    content = response.content.decode()
    # scoped: p1's file is present, p2's is not
    assert f"publisher-{p1.pk}/contract.pdf" in content
    assert f"publisher-{p2.pk}/other.pdf" not in content


@pytest.mark.django_db
def test_nested_detail_url_contains_parent_pk(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p1 = Publisher.objects.create(name="Penguin")
    key = f"publisher-{p1.pk}/contract.pdf"
    nested_bucket.append({"key": key, "size": 10})

    response = client_user_s3file_view.get(f"/publisher/{p1.pk}/publisherfile/{md5(key)}/detail/")
    assert response.status_code == 200
    assert key in response.content.decode()


@pytest.mark.django_db
def test_nested_list_empty_for_parent_without_files(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p = Publisher.objects.create(name="NoFiles")
    response = client_user_s3file_view.get(f"/publisher/{p.pk}/publisherfile/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_nested_detail_scoped_to_parent_404(client_user_s3file_view: Client, nested_bucket):
    """A file belonging to parent A must 404 when requested via parent B's URL."""
    from tests.test1.app.models import Publisher

    p1 = Publisher.objects.create(name="Penguin")
    p2 = Publisher.objects.create(name="HarperCollins")
    key = f"publisher-{p1.pk}/contract.pdf"
    nested_bucket.append({"key": key, "size": 10})

    response = client_user_s3file_view.get(f"/publisher/{p2.pk}/publisherfile/{md5(key)}/detail/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_list_sorting_via_querystring(client_user_s3file_view: Client):
    """django-tables2 column sorting must work on a Resource list (spec §6 caveat 2).

    per_page=10 is added to the querystring (django-tables2's RequestConfig honors a
    per_page GET override on top of the view's fixed paginate_by=2) so all 3 rows land
    on one page — otherwise the two rows being compared straddle a page boundary and
    the assertion below can't observe global sort order.
    """
    response = client_user_s3file_view.get("/s3file/?sort=-key&per_page=10")
    assert response.status_code == 200
    content = response.content.decode()
    # descending by key: q2 before q1 — the natural bucket order (q1, q2, logo)
    # disagrees, so a silently no-oping sort fails this assertion
    assert content.index("reports/2026/q2.pdf") < content.index("reports/2026/q1.pdf")


@pytest.mark.django_db
@override_settings(CRUD_VIEWS_STRICT=False)  # touch has no icon: a strict error since #264, rendered as its label
def test_list_action_icons(client: Client, cv_s3file):
    """Delete declares an icon; touch deliberately has none — the icon tag must
    be skipped entirely for icon-less actions, never rendered as class="None".

    Needs view (to see the list) AND delete (to see the delete/touch action
    buttons, which are permission-filtered) — granted inline because the shared
    fixtures deliberately hold exactly one permission each."""
    from django.contrib.auth.models import User

    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_s3file_icons", password="password")
    user_viewset_permission(user, cv_s3file, "view")
    user_viewset_permission(user, cv_s3file, "delete")
    client.force_login(user)

    response = client.get("/s3file/")
    content = response.content.decode()
    assert "fa-trash-can" in content
    assert 'class="None"' not in content
    assert "Touch" in content  # icon-less action button still renders its label


# ── ancestor authorization: a Resource leaf below ORM ancestors ───────────────

ANCESTOR_LOADS: list = []


def _ancestor_resource():
    """A Resource scoped by the application to the URL's Book (``*_pk`` kwargs); every loader call is recorded."""
    from crud_views.lib.resource import Resource
    from crud_views.lib.viewset.path_regs import PrimaryKeys

    class LeafFile(Resource):
        key: str
        book: int

        class Meta:
            verbose_name = "leaf file"
            verbose_name_plural = "leaf files"
            app_label = "app"
            pk_field = "key"
            pk_type = PrimaryKeys.STR

        @classmethod
        def cv_get_items(cls, request, **url_kwargs):
            ANCESTOR_LOADS.append(("items", dict(url_kwargs)))
            book_pk = next(value for name, value in url_kwargs.items() if name.startswith("ancrbook"))
            return [cls(key=f"file-{pk}", book=pk) for pk in LEAF_BOOKS if pk == int(book_pk)]

        @classmethod
        def cv_get_item(cls, request, pk, **url_kwargs):
            ANCESTOR_LOADS.append(("item", pk, dict(url_kwargs)))
            return super().cv_get_item(request, pk, **url_kwargs)

    return LeafFile


LEAF_BOOKS: list[int] = []


@pytest.mark.parametrize("variant", ["plain", "permission"])
@pytest.mark.parametrize("depth", [1, 2])
@pytest.mark.django_db
def test_resource_leaf_authorizes_before_application_loading(depth, variant):
    """Depth 1: Book → files; depth 2: Publisher → Book → files. Denied ancestry never calls the Resource loaders;
    allowed ancestry passes the unchanged URL kwargs to them, and the application's own scoping still applies."""
    from django.contrib.auth.models import Permission, User
    from django.urls import reverse

    from crud_views.lib.resource import ResourceViewMixin
    from crud_views.lib.views import DetailView, DetailViewPermissionRequired, ListView, ListViewPermissionRequired
    from crud_views.lib.viewset import ParentViewSet
    from tests.test1.ancestor_cases import FixedTemplateMixin, ancestor_scope
    from tests.test1.app.models import Book, Publisher

    publisher = Publisher.objects.create(name="Resource Publisher")
    book = Book.objects.create(title="Resource Book", publisher=publisher)
    other = Book.objects.create(title="Other Book", publisher=publisher)
    LEAF_BOOKS[:] = [book.pk, other.pk]
    ANCESTOR_LOADS.clear()
    leaf = _ancestor_resource()

    with ancestor_scope() as scope:
        parent = None
        if depth == 2:
            pub_vs = scope.viewset(model=Publisher, name=scope.name("ancrpub"))
            parent = ParentViewSet(name=pub_vs.name, attribute="publisher")
        book_vs = scope.viewset(model=Book, name=scope.name("ancrbook"), parent=parent)
        file_vs = scope.viewset(
            model=leaf,
            name=scope.name("ancrfile"),
            parent=ParentViewSet(name=book_vs.name),
            resource_permissions={"view": "app.view_s3file"},
        )
        list_base, detail_base = (
            (ListView, DetailView) if variant == "plain" else (ListViewPermissionRequired, DetailViewPermissionRequired)
        )
        attrs = {"cv_viewset": file_vs, "__module__": __name__}
        type(f"LeafList{scope.sfx}", (ResourceViewMixin, FixedTemplateMixin, list_base), dict(attrs))
        type(f"LeafDetail{scope.sfx}", (ResourceViewMixin, FixedTemplateMixin, detail_base), dict(attrs))
        scope.mount([file_vs])

        kwargs = {file_vs.parent.get_pk_name(): book.pk}
        if depth == 2:
            kwargs[book_vs.parent.get_pk_name()] = publisher.pk
        list_url = reverse(file_vs.get_router_name("list"), kwargs=kwargs)
        resolved = {name: str(value) for name, value in kwargs.items()}  # URL kwargs exactly as resolved
        detail_url = reverse(file_vs.get_router_name("detail"), kwargs={**kwargs, "pk": f"file-{book.pk}"})
        foreign_url = reverse(file_vs.get_router_name("detail"), kwargs={**kwargs, "pk": f"file-{other.pk}"})

        def client_with(*codenames):
            user = User.objects.create_user(username=f"leaf-{'-'.join(codenames) or 'none'}", password="password")
            for codename in codenames:
                user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label="app"))
            client = Client()
            client.force_login(user)
            return client

        # the local Resource permission alone never reaches the loaders
        local_only = client_with("view_s3file")
        for url in (list_url, detail_url):
            assert local_only.get(url).status_code == 403
        assert ANCESTOR_LOADS == []
        # anonymous: login redirect before any lookup or load
        response = Client().get(list_url)
        assert response.status_code == 302 and response["Location"].startswith("/accounts/login/")
        assert ANCESTOR_LOADS == []

        ancestors = ["view_book"] if depth == 1 else ["view_publisher", "view_book"]
        reader = client_with(*ancestors, "view_s3file")
        response = reader.get(list_url)
        assert response.status_code == 200
        assert response.content.decode().startswith(f"file-{book.pk};|")  # the application's scoping
        assert [("items", resolved)] == ANCESTOR_LOADS  # the original URL kwargs, unchanged

        ANCESTOR_LOADS.clear()
        assert reader.get(detail_url).status_code == 200
        item_loads = [("item", f"file-{book.pk}", resolved), ("items", resolved)]
        # the permission variant also loads the action object for its local gate (existing Resource contract)
        assert item_loads * (1 if variant == "plain" else 2) == ANCESTOR_LOADS
        assert reader.get(foreign_url).status_code == 404  # Resource membership stays the application's concern

        if variant == "permission":
            # allowed ancestry does not waive the local Resource permission
            ANCESTOR_LOADS.clear()
            assert client_with(*ancestors).get(list_url).status_code == 403
            assert ANCESTOR_LOADS == []


@pytest.mark.django_db
def test_top_level_resource_does_no_ancestor_work(client_user_s3file_view: Client, monkeypatch):
    from crud_views.lib.view import ancestors

    def fail(*args, **kwargs):
        raise AssertionError("ancestor work on a top-level Resource request")

    monkeypatch.setattr(ancestors, "authorize_ancestors", fail)
    assert client_user_s3file_view.get("/s3file/").status_code == 200
    assert client_user_s3file_view.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/").status_code == 200
