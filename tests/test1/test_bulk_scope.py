"""Request-level proofs of bulk key normalization and authorization boundaries."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import router

from tests.test1.app.models import Author, BulkCode, Publisher
from tests.test1.app.views_bulk import BulkCodeMarkView, BulkPublisherArchiveView
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
