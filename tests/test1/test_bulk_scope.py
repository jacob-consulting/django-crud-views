"""Request-level proofs of bulk key normalization and authorization boundaries."""

import django_tables2 as tables
import pytest
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.db import router
from django.test import Client
from django.urls import reverse

from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.table import Table
from crud_views.lib.views import CardListViewPermissionRequired, ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Author, Book, BookNote, BulkCode, Publisher
from tests.test1.app.views_bulk import (
    BulkBookMarkView,
    BulkCodeMarkView,
    BulkPublisherArchiveNowView,
    BulkPublisherArchiveView,
    BulkTenantListView,
    BulkTenantMarkView,
    BulkTenantNarrowView,
    cv_bulk_book,
)
from tests.test1.test_ancestor_authorization import _client, _user, isolated_routes
from tests.test1.test_bulk_flow import review_data, soup

pytestmark = pytest.mark.django_db


def post_selection(client, url, objects, stage="review"):
    return client.post(url, {"cv_bulk_stage": stage, "cv_bulk_ids": [str(obj.pk) for obj in objects]})


def forbidden_hook(*args, **kwargs):
    pytest.fail("Selection query or item hook must not be reached")


def test_uuid_keys_are_canonical_and_deduplicated(client_user_bulk_author_change):
    author = Author.objects.create(first_name="Ada", last_name="Lovelace")
    other = Author.objects.create(first_name="Grace", last_name="Hopper")
    key = str(author.pk)
    client = client_user_bulk_author_change
    response = client.post(
        "/bulk-author/mark/",
        {"cv_bulk_stage": "review", "cv_bulk_ids": [key.upper(), author.pk.hex, "{" + key + "}"]},
    )
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (author,)
    assert review_data(response)["cv_bulk_ids"] == [key]
    assert [item.text_content().strip() for item in soup(response).cssselect("form.cv-form li")] == [str(author)]
    assert client.post("/bulk-author/mark/", review_data(response)).status_code == 302
    author.refresh_from_db()
    other.refresh_from_db()
    assert author.pseudonym == "marked"
    assert other.pseudonym is None


def test_string_keys_preserve_leading_zeros(client_user_bulk_code_change):
    codes = [BulkCode.objects.create(code=code) for code in ("A-1", "007")]
    client = client_user_bulk_code_change
    response = post_selection(client, "/bulk-code/mark/", codes)
    assert response.status_code == 200
    assert review_data(response)["cv_bulk_ids"] == ["A-1", "007"]
    assert client.post("/bulk-code/mark/", review_data(response)).status_code == 302
    assert list(BulkCode.objects.values_list("code", "label")) == [("007", "marked"), ("A-1", "marked")]


def test_integer_keys_are_canonical_and_deduplicated(client_user_bulk_publisher_change):
    publisher = Publisher.objects.create(pk=1, name="One")
    client = client_user_bulk_publisher_change
    response = client.post("/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": ["01", " 1", "1"]})
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (publisher,)
    assert review_data(response)["cv_bulk_ids"] == ["1"]
    assert client.post("/bulk-publisher/archive/", review_data(response)).status_code == 302
    publisher.refresh_from_db()
    assert publisher.name == "One (archived)"


def test_malformed_uuid_is_bad_request(client_user_bulk_author_change):
    response = client_user_bulk_author_change.post(
        "/bulk-author/mark/", {"cv_bulk_stage": "review", "cv_bulk_ids": ["not-a-uuid"]}
    )
    assert response.status_code == 400


def assert_nul_rejected(client, monkeypatch, stage, excluded=False):
    BulkCode.objects.create(code="A-1", label="original")
    for hook in ("_selection_queryset", "cv_bulk_has_permission", "cv_bulk_check"):
        monkeypatch.setattr(BulkCodeMarkView, hook, forbidden_hook)
    data = {"cv_bulk_stage": stage, "cv_bulk_ids": ["A-1" if excluded else "A\x001"]}
    if excluded:
        data["cv_bulk_blocked_ids"] = ["A\x001"]
    assert client.post("/bulk-code/mark/", data).status_code == 400
    assert list(BulkCode.objects.values_list("code", "label")) == [("A-1", "original")]


def test_string_key_nul_character_is_bad_request_on_review(client_user_bulk_code_change, monkeypatch):
    assert_nul_rejected(client_user_bulk_code_change, monkeypatch, "review")


def test_string_key_nul_character_is_bad_request_on_execute(client_user_bulk_code_change, monkeypatch):
    assert_nul_rejected(client_user_bulk_code_change, monkeypatch, "execute")


def test_string_key_nul_character_in_excluded_ids_is_bad_request(client_user_bulk_code_change, monkeypatch):
    assert_nul_rejected(client_user_bulk_code_change, monkeypatch, "review", excluded=True)


@pytest.fixture
def instance_write_routes(monkeypatch):
    class Router:
        def db_for_read(self, model, **hints):
            return None

        def db_for_write(self, model, **hints):
            return "shard" if isinstance(hints.get("instance"), Publisher) else None

    monkeypatch.setattr(router, "routers", [Router()])
    ContentType.objects.clear_cache()
    yield
    ContentType.objects.clear_cache()


@pytest.fixture
def model_write_routes(monkeypatch):
    class Router:
        def db_for_read(self, model, **hints):
            return None

        def db_for_write(self, model, **hints):
            return "shard" if model is Publisher and hints.get("instance") is None else None

    monkeypatch.setattr(router, "routers", [Router()])
    ContentType.objects.clear_cache()
    yield
    ContentType.objects.clear_cache()


def assert_write_route_rejected(client, stage, destination, *, model_route):
    publishers = [Publisher.objects.using("default").create(name=name) for name in ("Alpha", "Beta")]
    for obj in publishers:
        Publisher.objects.using("shard").create(pk=obj.pk, name=f"Shard {obj.name}")
    assert router.db_for_read(Publisher) == "default"
    assert Publisher.objects.all().db == "default"
    assert router.db_for_write(Publisher) == ("shard" if model_route else "default")
    for obj in publishers:
        assert obj._state.db == "default"
        assert router.db_for_write(Publisher, instance=obj) == ("default" if model_route else "shard")
    with pytest.raises(ImproperlyConfigured, match="default"):
        post_selection(client, f"/bulk-publisher/{destination}/", publishers, stage)
    assert list(Publisher.objects.using("default").values_list("name", flat=True)) == ["Alpha", "Beta"]
    assert list(Publisher.objects.using("shard").values_list("name", flat=True)) == ["Shard Alpha", "Shard Beta"]


@pytest.mark.django_db(databases=["default", "shard"])
def test_instance_routed_write_review(client_user_bulk_publisher_change, instance_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "review", "archive", model_route=False)


@pytest.mark.django_db(databases=["default", "shard"])
def test_instance_routed_write_execute(client_user_bulk_publisher_change, instance_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "execute", "archive", model_route=False)


@pytest.mark.django_db(databases=["default", "shard"])
def test_instance_routed_write_skipped_confirmation(client_user_bulk_publisher_change, instance_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "review", "archive-now", model_route=False)


@pytest.mark.django_db(databases=["default", "shard"])
def test_model_routed_write_review(client_user_bulk_publisher_change, model_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "review", "archive", model_route=True)


@pytest.mark.django_db(databases=["default", "shard"])
def test_model_routed_write_execute(client_user_bulk_publisher_change, model_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "execute", "archive", model_route=True)


@pytest.mark.django_db(databases=["default", "shard"])
def test_model_routed_write_skipped_confirmation(client_user_bulk_publisher_change, model_write_routes):
    assert_write_route_rejected(client_user_bulk_publisher_change, "review", "archive-now", model_route=True)


@pytest.mark.django_db(databases=["default", "shard"])
@pytest.mark.parametrize("stage", ["review", "execute"])
def test_whole_model_route_rejected(client_user_bulk_publisher_change, database_routes, stage):
    publisher = Publisher.objects.create(name="Default")
    Publisher.objects.using("shard").create(pk=publisher.pk, name="Shard")
    # Keep authentication on default; only the selected model moves as a whole.
    with (
        database_routes("default", overrides={Publisher: "shard"}),
        pytest.raises(ImproperlyConfigured, match="default"),
    ):
        post_selection(client_user_bulk_publisher_change, "/bulk-publisher/archive/", [publisher], stage)
    assert list(Publisher.objects.using("default").values_list("name", flat=True)) == ["Default"]
    assert list(Publisher.objects.using("shard").values_list("name", flat=True)) == ["Shard"]


@pytest.mark.django_db(databases=["default", "shard"])
def test_destination_queryset_on_shard_rejected(client_user_bulk_publisher_change, monkeypatch):
    publisher = Publisher.objects.create(pk=41, name="Default")
    Publisher.objects.using("shard").create(pk=42, name="Shard")
    assert not Publisher.objects.using("shard").filter(pk=publisher.pk).exists()
    assert router.db_for_write(Publisher) == router.db_for_write(Publisher, instance=publisher) == "default"
    monkeypatch.setattr(BulkPublisherArchiveView, "get_queryset", lambda self: Publisher.objects.using("shard"))
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_has_permission", forbidden_hook)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_check", forbidden_hook)
    with pytest.raises(ImproperlyConfigured, match="unsliced querysets for the ViewSet model on the default database"):
        post_selection(client_user_bulk_publisher_change, "/bulk-publisher/archive/", [publisher])
    assert list(Publisher.objects.using("default").values_list("name", flat=True)) == ["Default"]
    assert list(Publisher.objects.using("shard").values_list("name", flat=True)) == ["Shard"]


@pytest.mark.parametrize("kind", ["sliced", "foreign_model"])
def test_unsupported_destination_queryset_rejected(client_user_bulk_publisher_change, monkeypatch, kind):
    publisher = Publisher.objects.create(name="Unchanged")
    queryset = Publisher.objects.all()[:1] if kind == "sliced" else Author.objects.all()
    monkeypatch.setattr(BulkPublisherArchiveView, "get_queryset", lambda self: queryset)
    with pytest.raises(ImproperlyConfigured, match="unsliced querysets for the ViewSet model on the default database"):
        post_selection(client_user_bulk_publisher_change, "/bulk-publisher/archive/", [publisher])
    publisher.refresh_from_db()
    assert publisher.name == "Unchanged"


UNAVAILABLE = "This item is unavailable for this action."
CHANGED = "The eligible selection changed. Review it and confirm again."


def record_item_hooks(monkeypatch, view):
    calls = {"permission": [], "check": []}
    permission = view.cv_bulk_has_permission
    check = view.cv_bulk_check

    def has_permission(self, obj):
        calls["permission"].append(obj.pk)
        return permission(self, obj)

    def eligibility(self, obj):
        calls["check"].append(obj.pk)
        return check(self, obj)

    monkeypatch.setattr(view, "cv_bulk_has_permission", has_permission)
    monkeypatch.setattr(view, "cv_bulk_check", eligibility)
    return calls


def assert_unavailable(response, obj):
    blocked = next(item for item in response.context["bulk_review"].blocked if item.pk == str(obj.pk))
    assert blocked.label is None
    assert blocked.reasons == (UNAVAILABLE,)
    assert str(obj) not in response.content.decode()


def test_nested_selection_keeps_parent_scope(client_user_bulk_book_change, cv_bulk_book):
    first = Publisher.objects.create(name="First parent")
    second = Publisher.objects.create(name="Second parent")
    own = Book.objects.create(publisher=first, title="Own book")
    foreign = Book.objects.create(publisher=second, title="Other parent's book")
    url = reverse(cv_bulk_book.get_router_name("mark"), kwargs={"bulk_publisher_pk": first.pk})
    client = client_user_bulk_book_change
    response = post_selection(client, url, [own, foreign])
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (own,)
    assert_unavailable(response, foreign)
    assert client.post(url, review_data(response)).status_code == 302
    own.refresh_from_db()
    foreign.refresh_from_db()
    assert own.title == "Own book (marked)"
    assert foreign.title == "Other parent's book"


def test_tenant_selection_cannot_be_widened_by_destination(client_user_bulk_tenant_change):
    own = Publisher.objects.create(name="Own publisher")
    foreign = Publisher.objects.create(name="Foreign publisher")
    client = client_user_bulk_tenant_change
    response = post_selection(client, "/bulk-tenant/mark/", [own, foreign])
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (own,)
    assert_unavailable(response, foreign)
    assert client.post("/bulk-tenant/mark/", review_data(response)).status_code == 302
    own.refresh_from_db()
    foreign.refresh_from_db()
    assert own.name == "Own publisher (marked)"
    assert foreign.name == "Foreign publisher"


def test_unavailable_records_have_identical_disclosure(client_user_bulk_tenant_change):
    foreign = Publisher.objects.create(name="Foreign secret")
    private = Publisher.objects.create(name="Private secret")
    locked = Publisher.objects.create(name="Locked visible")
    response = client_user_bulk_tenant_change.post(
        "/bulk-tenant/mark/",
        {"cv_bulk_stage": "review", "cv_bulk_ids": [999999, foreign.pk, private.pk, locked.pk]},
    )
    assert response.status_code == 200
    rows = [" ".join(row.text_content().split()) for row in soup(response).cssselect('[role="alert"] li')]
    assert rows[:3] == [UNAVAILABLE] * 3
    assert len(rows) == 4
    assert locked.name in rows[3]
    assert "Locked publishers cannot be marked." in rows[3]
    assert [item.label for item in response.context["bulk_review"].blocked[:3]] == [None] * 3
    assert foreign.name not in response.content.decode()
    assert private.name not in response.content.decode()


def narrow_records(monkeypatch):
    visible = Publisher.objects.create(name="Visible publisher")
    hidden = Publisher.objects.create(name="Hidden publisher")
    calls = record_item_hooks(monkeypatch, BulkTenantNarrowView)
    return visible, hidden, calls


def assert_hidden_untouched(response, hidden, calls):
    hidden.refresh_from_db()
    assert hidden.name == "Hidden publisher"
    assert hidden.name not in response.content.decode()
    assert hidden.pk not in calls["permission"]
    assert hidden.pk not in calls["check"]


def test_narrower_destination_review(client_user_bulk_tenant_change, monkeypatch):
    visible, hidden, calls = narrow_records(monkeypatch)
    monkeypatch.setattr(BulkTenantNarrowView, "cv_bulk_confirm", True)
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/narrow/", [visible, hidden])
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (visible,)
    assert_unavailable(response, hidden)
    assert_hidden_untouched(response, hidden, calls)
    visible.refresh_from_db()
    assert visible.name == "Visible publisher"
    assert calls == {"permission": [visible.pk], "check": [visible.pk]}


def test_narrower_destination_execute(client_user_bulk_tenant_change, monkeypatch):
    visible, hidden, calls = narrow_records(monkeypatch)
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/narrow/", [visible, hidden], "execute")
    assert response.status_code == 200
    assert CHANGED in response.content.decode()
    assert_unavailable(response, hidden)
    assert_hidden_untouched(response, hidden, calls)
    visible.refresh_from_db()
    assert visible.name == "Visible publisher"
    assert calls == {"permission": [visible.pk], "check": [visible.pk]}


def test_narrower_destination_skipped_confirmation(client_user_bulk_tenant_change, monkeypatch):
    visible, hidden, calls = narrow_records(monkeypatch)
    client = client_user_bulk_tenant_change
    response = post_selection(client, "/bulk-tenant/narrow/", [visible, hidden])
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    assert_unavailable(response, hidden)
    assert_hidden_untouched(response, hidden, calls)
    visible.refresh_from_db()
    assert visible.name == "Visible publisher"
    assert calls == {"permission": [visible.pk], "check": [visible.pk]}
    response = post_selection(client, "/bulk-tenant/narrow/", [visible])
    assert response.status_code == 302
    visible.refresh_from_db()
    assert visible.name == "Visible publisher (marked)"
    assert_hidden_untouched(response, hidden, calls)


def test_source_only_filter_is_no_authorization_gate(client_user_bulk_tenant_change):
    publisher = Publisher.objects.create(name="Unlisted publisher")
    client = client_user_bulk_tenant_change
    source = client.get("/bulk-tenant/")
    assert source.status_code == 200
    assert publisher.name not in source.content.decode()
    response = post_selection(client, "/bulk-tenant/mark/", [publisher])
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (publisher,)
    assert publisher.name in response.content.decode()
    assert client.post("/bulk-tenant/mark/", review_data(response)).status_code == 302
    publisher.refresh_from_db()
    assert publisher.name == "Unlisted publisher (marked)"


def test_pagination_is_no_authorization_gate(client_user_bulk_tenant_change, monkeypatch):
    Publisher.objects.create(name="First publisher")
    publisher = Publisher.objects.create(name="Second publisher")
    monkeypatch.setattr(BulkTenantListView, "paginate_by", 1)
    client = client_user_bulk_tenant_change
    first_page = client.get("/bulk-tenant/?page=1")
    assert first_page.status_code == 200
    assert publisher.name not in first_page.content.decode()
    assert publisher.name in client.get("/bulk-tenant/?page=2").content.decode()
    response = post_selection(client, "/bulk-tenant/mark/", [publisher])
    assert response.status_code == 200
    assert response.context["bulk_review"].objects == (publisher,)


@pytest.mark.parametrize("stage", ["review", "execute"])
def test_destination_admission_precedes_item_hooks(client_user_bulk_publisher_view, monkeypatch, stage):
    publisher = Publisher.objects.create(name="No change permission")
    calls = record_item_hooks(monkeypatch, BulkPublisherArchiveView)
    source = client_user_bulk_publisher_view.get("/bulk-publisher/")
    assert source.status_code == 200
    assert not soup(source).cssselect("[data-cv-bulk-action], [data-cv-bulk-item]")
    response = post_selection(client_user_bulk_publisher_view, "/bulk-publisher/archive/", [publisher], stage)
    assert response.status_code == 403
    assert calls == {"permission": [], "check": []}
    publisher.refresh_from_db()
    assert publisher.name == "No change permission"


@pytest.mark.parametrize("card", [False, True], ids=["table", "card"])
@pytest.mark.parametrize("stage", ["review", "execute"])
def test_bulk_guardian_visibility_preserves_all_blocked_review(card, stage, monkeypatch):
    from types import SimpleNamespace

    from guardian.core import ObjectPermissionChecker

    from tests.test1.app.views_bulk import BulkPublisherTable

    def build(suffix):
        vs = GuardianViewSet(model=Publisher, name=f"offered_guardian_{suffix}", prefix=f"offered-guardian-{suffix}")

        # Core source admission deliberately avoids Guardian's separate queryset policy.
        class OfferedGuardianList(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
            cv_viewset = vs
            table_class = BulkPublisherTable
            cv_bulk_actions = ("mark",)
            cv_context_actions = ["home"]
            cv_list_actions = []

        class OfferedGuardianCard(BulkSelectionMixin, CardListViewPermissionRequired):
            cv_viewset = vs
            cv_bulk_actions = ("mark",)
            cv_context_actions = ["home"]
            cv_card_actions = []
            cv_order_fields = ["name"]

        class OfferedGuardianMark(BulkFormViewPermissionRequired):
            cv_viewset = vs
            cv_key = "mark"
            cv_path = "mark"
            cv_permission = "change"
            cv_cancel_keys = ["list", "card"]
            cv_success_key = "list"
            cv_action_label_template_code = "Mark selected"
            cv_action_short_label_template_code = "Mark"

            def cv_bulk_has_permission(self, obj):
                return self.request.user.has_perm("app.change_publisher", obj)

            def cv_form_valid(self, context):
                pytest.fail("All-blocked Guardian selection reached a write")

        return SimpleNamespace(vs=vs, destination=OfferedGuardianMark), [vs]

    obj = Publisher.objects.create(name="No object grant")
    actor = _user("guardian_offer", (Publisher, "view"), (Publisher, "change"))
    client = _client(actor)
    with isolated_routes(build) as fixture:
        original = PermissionsMixin.has_perm
        checker = ObjectPermissionChecker.has_perm
        selected = []

        def model_only(self, perm, obj=None):
            assert obj is None, "Bulk rendering scanned selected-object grants"
            return original(self, perm, obj)

        def selected_check(self, perm, obj):
            selected.append(obj.pk)
            return checker(self, perm, obj)

        with monkeypatch.context() as render_patch:
            render_patch.setattr(PermissionsMixin, "has_perm", model_only)
            render_patch.setattr(ObjectPermissionChecker, "has_perm", forbidden_hook)
            render_patch.setattr(fixture.destination, "cv_bulk_has_permission", forbidden_hook)
            render_patch.setattr(fixture.destination, "cv_bulk_check", forbidden_hook)
            response = client.get(reverse(fixture.vs.get_router_name("card" if card else "list")))
            assert response.status_code == 200
            button = soup(response).cssselect('[data-cv-bulk-action="mark"]')[0]
            assert soup(response).cssselect("[data-cv-bulk-item]")
            offered = button.get("formaction")
        monkeypatch.setattr(ObjectPermissionChecker, "has_perm", selected_check)
        response = post_selection(client, offered, [obj], stage)
        assert response.status_code == 200
        assert selected == [obj.pk]
        assert response.context["bulk_review"].objects == ()
        assert len(response.context["bulk_review"].blocked) == 1
        assert not soup(response).cssselect('button[type="submit"]')
        assert soup(response).cssselect("[data-cv-cancel-url]")
        obj.refresh_from_db()
        assert obj.name == "No object grant"


@pytest.mark.parametrize("card", [False, True], ids=["table", "card"])
@pytest.mark.parametrize("stage", ["review", "execute"])
@pytest.mark.parametrize("denial", ["immediate", "farther"])
def test_bulk_hidden_action_ancestor_write_denied(card, stage, denial, monkeypatch):
    from types import SimpleNamespace

    parent = Publisher.objects.create(name="Read-only publisher")
    book = Book.objects.create(publisher=parent, title="Admitted book")
    note = BookNote.objects.create(book=book, note="Unchanged note")
    actor = _user(
        "ancestor_offer",
        (Publisher, "view"),
        (Book, "view"),
        (Book, "change"),
        (BookNote, "view"),
        (BookNote, "change"),
    )
    client = _client(actor)

    def assert_denied(vs, destination, obj, kwargs):
        monkeypatch.setattr(destination, "cv_bulk_has_permission", forbidden_hook)
        monkeypatch.setattr(destination, "cv_bulk_check", forbidden_hook)
        monkeypatch.setattr(destination, "cv_form_valid", forbidden_hook)
        response = client.get(reverse(vs.get_router_name("card" if card else "list"), kwargs=kwargs))
        assert response.status_code == 200
        assert not soup(response).cssselect('[data-cv-bulk-action="mark"]')
        assert not soup(response).cssselect("[data-cv-bulk-item]")
        destination_url = reverse(vs.get_router_name(destination.cv_key), kwargs=kwargs)
        response = post_selection(client, destination_url, [obj], stage)
        assert response.status_code == 403
        assert list(Publisher.objects.values_list("name", flat=True)) == ["Read-only publisher"]
        assert list(Book.objects.values_list("title", flat=True)) == ["Admitted book"]
        assert list(BookNote.objects.values_list("note", flat=True)) == ["Unchanged note"]

    if denial == "immediate":
        assert_denied(cv_bulk_book, BulkBookMarkView, book, {"bulk_publisher_pk": parent.pk})
        return

    def build(suffix):
        root = ViewSet(model=Publisher, name=f"offered_root_{suffix}", prefix=f"offered-root-{suffix}")
        middle = ViewSet(
            model=Book,
            name=f"offered_book_{suffix}",
            prefix="book",
            parent=ParentViewSet(name=root.name, attribute="publisher"),
        )
        leaf = ViewSet(
            model=BookNote,
            name=f"offered_note_{suffix}",
            prefix="note",
            parent=ParentViewSet(name=middle.name, attribute="book"),
            ancestor_policy=AncestorPolicy(cascade=True, write=AncestorPermissions(nearest="change", higher="change")),
        )

        class OfferedNoteTable(Table):
            note = tables.Column()

        class OfferedNoteListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
            cv_viewset = leaf
            table_class = OfferedNoteTable
            cv_bulk_actions = ("mark",)
            cv_context_actions = ["home"]
            cv_list_actions = []

        class OfferedNoteCardView(BulkSelectionMixin, CardListViewPermissionRequired):
            cv_viewset = leaf
            cv_bulk_actions = ("mark",)
            cv_context_actions = ["home"]
            cv_card_actions = []
            cv_order_fields = ["note"]

        class OfferedNoteMarkView(BulkFormViewPermissionRequired):
            cv_viewset = leaf
            cv_key = "mark"
            cv_path = "mark"
            cv_permission = "change"
            cv_cancel_keys = ["list", "card"]
            cv_success_key = "list"
            cv_action_label_template_code = "Mark selected"
            cv_action_short_label_template_code = "Mark"

            def cv_form_valid(self, context):
                for selected in self.cv_bulk_objects:
                    selected.note += " (marked)"
                    selected.save(using=self.cv_get_db_alias())

        return SimpleNamespace(root=root, middle=middle, leaf=leaf, destination=OfferedNoteMarkView), [
            root,
            middle,
            leaf,
        ]

    with isolated_routes(build) as fixture:
        assert_denied(
            fixture.leaf,
            fixture.destination,
            note,
            {f"{fixture.root.name}_pk": parent.pk, f"{fixture.middle.name}_pk": book.pk},
        )


@pytest.mark.parametrize("stage", ["review", "execute"])
def test_anonymous_request_redirects_to_login(client, stage, monkeypatch):
    publisher = Publisher.objects.create(name="Login required")
    calls = record_item_hooks(monkeypatch, BulkPublisherArchiveView)
    response = post_selection(client, "/bulk-publisher/archive/", [publisher], stage)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/?next=")
    assert calls == {"permission": [], "check": []}


@pytest.mark.parametrize("stage", ["review", "execute"])
def test_parent_admission_precedes_item_hooks(client, user_bulk_book_without_parent, cv_bulk_book, monkeypatch, stage):
    parent = Publisher.objects.create(name="Denied parent")
    book = Book.objects.create(publisher=parent, title="Child")
    client.force_login(user_bulk_book_without_parent)
    calls = record_item_hooks(monkeypatch, BulkBookMarkView)
    url = reverse(cv_bulk_book.get_router_name("mark"), kwargs={"bulk_publisher_pk": parent.pk})
    response = post_selection(client, url, [book], stage)
    assert response.status_code == 403
    assert calls == {"permission": [], "check": []}
    book.refresh_from_db()
    assert book.title == "Child"


def test_only_submitted_records_reach_item_hooks(client_user_bulk_tenant_change, monkeypatch):
    selected = Publisher.objects.create(name="Selected")
    Publisher.objects.create(name="Not selected")
    calls = record_item_hooks(monkeypatch, BulkTenantMarkView)
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/mark/", [selected])
    assert response.status_code == 200
    assert calls == {"permission": [selected.pk], "check": [selected.pk]}


def test_forged_blocked_promotion_beside_eligible_writes_nothing(client_user_bulk_tenant_change):
    eligible = Publisher.objects.create(name="Eligible")
    locked = Publisher.objects.create(name="Locked publisher")
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/mark/", [eligible, locked], "execute")
    assert response.status_code == 200
    assert CHANGED in response.content.decode()
    assert list(Publisher.objects.values_list("name", flat=True)) == ["Eligible", "Locked publisher"]


def test_forged_blocked_promotion_alone_is_cancel_only(client_user_bulk_tenant_change):
    locked = Publisher.objects.create(name="Locked publisher")
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/mark/", [locked], "execute")
    assert response.status_code == 200
    assert locked.name in response.content.decode()
    assert "Locked publishers cannot be marked." in response.content.decode()
    assert CHANGED not in response.content.decode()
    assert not soup(response).cssselect('button[type="submit"]')
    assert soup(response).cssselect("[data-cv-cancel-url]")
    locked.refresh_from_db()
    assert locked.name == "Locked publisher"


def test_authorized_direct_execute_needs_no_prior_review(client_user_bulk_tenant_change):
    publisher = Publisher.objects.create(name="Direct")
    response = post_selection(client_user_bulk_tenant_change, "/bulk-tenant/mark/", [publisher], "execute")
    assert response.status_code == 302
    publisher.refresh_from_db()
    assert publisher.name == "Direct (marked)"
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["1 record processed."]


def test_skip_confirmation_still_requires_admission(client_user_bulk_publisher_view, monkeypatch):
    publisher = Publisher.objects.create(name="Denied")
    calls = record_item_hooks(monkeypatch, BulkPublisherArchiveNowView)
    response = post_selection(client_user_bulk_publisher_view, "/bulk-publisher/archive-now/", [publisher])
    assert response.status_code == 403
    assert calls == {"permission": [], "check": []}
    publisher.refresh_from_db()
    assert publisher.name == "Denied"


def test_skip_confirmation_does_not_promote_locked_candidate(client_user_bulk_publisher_change):
    publisher = Publisher.objects.create(name="Locked publisher")
    response = post_selection(client_user_bulk_publisher_change, "/bulk-publisher/archive-now/", [publisher], "execute")
    assert response.status_code == 200
    publisher.refresh_from_db()
    assert publisher.name == "Locked publisher"


@pytest.mark.parametrize("stage", ["review", "execute"])
def test_csrf_is_required(user_bulk_publisher_change, stage, monkeypatch):
    publisher = Publisher.objects.create(name="CSRF protected")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_bulk_publisher_change)
    calls = record_item_hooks(monkeypatch, BulkPublisherArchiveView)
    response = post_selection(client, "/bulk-publisher/archive/", [publisher], stage)
    assert response.status_code == 403
    assert calls == {"permission": [], "check": []}
    publisher.refresh_from_db()
    assert publisher.name == "CSRF protected"
