"""Bulk execution boundaries and application-owned deletion and locking recipes."""

import pytest
from django.contrib.messages import get_messages
from django.db import connection
from django.db.models import ProtectedError

from tests.test1.app.models import Contract, Publisher
from tests.test1.app.views import AuthorOriginBroadcastView
from tests.test1.app.views_bulk import BulkPublisherArchiveView, BulkPublisherRenameView
from tests.test1.test_bulk_flow import publisher_names, review_data, soup

pytestmark = pytest.mark.django_db


def post_selection(client, records, *, path="archive", stage="execute", **extra):
    return client.post(
        f"/bulk-publisher/{path}/",
        {
            "cv_bulk_stage": stage,
            "cv_bulk_ids": [obj.pk for obj in records],
            **extra,
        },
    )


@pytest.mark.parametrize(
    "path,stage,indices,expected",
    [
        ("archive", "review", (0, 1, 2), 200),
        ("archive", "execute", (0, 1), 302),
        ("archive-now", "review", (0, 1), 302),
        ("archive-now", "review", (0, 2), 200),
        ("rename", "execute", (0, 2), 200),
        ("archive", "execute", (0, 2), 200),
    ],
)
def test_item_checks_run_once_per_request(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch, path, stage, indices, expected
):
    permission_calls, check_calls = [], []
    original = BulkPublisherArchiveView.cv_bulk_check

    def permission(self, obj):
        permission_calls.append(obj.pk)
        return True

    def check(self, obj):
        check_calls.append(obj.pk)
        return original(self, obj)

    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_has_permission", permission)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_check", check)
    records = [bulk_publishers[i] for i in indices]
    response = post_selection(client_user_bulk_publisher_change, records, path=path, stage=stage)
    assert response.status_code == expected
    assert permission_calls == check_calls == [obj.pk for obj in records]


def test_permission_denial_skips_business_check(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    calls = []
    denied = bulk_publishers[1]
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_has_permission", lambda self, obj: obj.pk != denied.pk)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_bulk_check", lambda self, obj: calls.append(obj.pk) or [])
    response = post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], stage="review")
    assert calls == [bulk_publishers[0].pk]
    assert response.context["bulk_review"].blocked[0].label is None
    assert "Beta" not in soup(response).text_content()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [True, False])
@pytest.mark.parametrize(
    "path,stage,writes",
    [
        ("archive", "review", False),
        ("archive", "execute", True),
        ("archive-now", "review", True),
    ],
)
def test_check_transaction_and_on_commit(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch, atomic, path, stage, writes
):
    checks, commits = [], []
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_atomic", atomic)
    monkeypatch.setattr(
        BulkPublisherArchiveView, "cv_bulk_check", lambda self, obj: checks.append(connection.in_atomic_block) or []
    )
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_on_commit", lambda self, context: commits.append("commit"))
    response = post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], path=path, stage=stage)
    assert response.status_code == (302 if writes else 200)
    assert checks == [atomic and writes] * 2
    assert commits == (["commit"] if writes else [])
    assert publisher_names() == (
        ["Alpha (archived)", "Beta (archived)", "Locked Gamma"] if writes else ["Alpha", "Beta", "Locked Gamma"]
    )


PUBLIC_VALID = [
    "cv_post_hook",
    "cv_form_is_valid",
    "cv_form_valid",
    "cv_form_valid_hook",
    "cv_on_commit",
    "cv_form_valid_redirect",
]
PUBLIC_INVALID = ["cv_post_hook", "cv_form_is_valid", "cv_form_invalid_hook", "cv_form_invalid"]


def record_hooks(monkeypatch, cls, names, recording):
    for name in names:
        original = getattr(cls, name)

        def wrapped(self, *args, _name=name, _original=original, **kwargs):
            recording.append(_name)
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(cls, name, wrapped)


@pytest.mark.django_db(transaction=True)
def test_public_hook_order_matches_stock_form_view(
    client_user_bulk_publisher_change, user_author_origin, bulk_publishers, monkeypatch
):
    bulk, stock = [], []
    record_hooks(monkeypatch, BulkPublisherArchiveView, PUBLIC_VALID, bulk)
    record_hooks(monkeypatch, AuthorOriginBroadcastView, PUBLIC_VALID, stock)
    client = client_user_bulk_publisher_change
    assert post_selection(client, bulk_publishers[:2]).status_code == 302
    client.force_login(user_author_origin)
    assert client.post("/author_origin/broadcast/", {"subject": "Hello"}).status_code == 302
    assert bulk == stock == PUBLIC_VALID


@pytest.mark.django_db(transaction=True)
def test_invalid_public_hook_order_matches_stock_form_view(
    client_user_bulk_publisher_change, user_author_origin, bulk_publishers, monkeypatch
):
    bulk, stock = [], []
    record_hooks(monkeypatch, BulkPublisherRenameView, PUBLIC_INVALID, bulk)
    record_hooks(monkeypatch, AuthorOriginBroadcastView, PUBLIC_INVALID, stock)
    client = client_user_bulk_publisher_change
    assert post_selection(client, bulk_publishers[:2], path="rename").status_code == 200
    client.force_login(user_author_origin)
    assert client.post("/author_origin/broadcast/", {}).status_code == 200
    assert bulk == stock == PUBLIC_INVALID


@pytest.mark.django_db(transaction=True)
def test_nested_write_guard_and_check_run_before_public_hooks(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch
):
    calls = []
    for name in ("_cv_check_nested_write", "_review_selection", "cv_post_hook"):
        original = getattr(BulkPublisherArchiveView, name)

        def wrapped(self, *args, _name=name, _original=original, **kwargs):
            calls.append((_name, bool(args), connection.in_atomic_block))
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(BulkPublisherArchiveView, name, wrapped)
    assert post_selection(client_user_bulk_publisher_change, bulk_publishers[:2]).status_code == 302
    assert calls == [
        ("_cv_check_nested_write", False, False),
        ("_review_selection", True, True),
        ("_cv_check_nested_write", True, True),
        ("cv_post_hook", True, True),
    ]


@pytest.mark.django_db(transaction=True)
def test_cv_form_valid_process_override_is_not_called_on_bulk_destination(
    client_user_bulk_publisher_change, bulk_publishers, monkeypatch
):
    process, hooks = [], []
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_form_valid_process", lambda self, context: process.append(True))
    for name in ("cv_form_valid", "cv_form_valid_hook"):
        original = getattr(BulkPublisherArchiveView, name)

        def wrapped(self, context, _name=name, _original=original):
            hooks.append((_name, connection.in_atomic_block))
            return _original(self, context)

        monkeypatch.setattr(BulkPublisherArchiveView, name, wrapped)
    client = client_user_bulk_publisher_change
    assert post_selection(client, bulk_publishers[:1]).status_code == 302
    assert post_selection(client, bulk_publishers[1:2], path="archive-now", stage="review").status_code == 302
    assert process == []
    assert hooks == [("cv_form_valid", True), ("cv_form_valid_hook", True)] * 2
    assert publisher_names() == ["Alpha (archived)", "Beta (archived)", "Locked Gamma"]


class ActionFailed(Exception):
    """A deliberate application failure at a tested lifecycle boundary."""


def write_then_fail(self, context):
    obj = self.cv_bulk_objects[0]
    obj.name += " changed"
    obj.save(using=self.cv_get_db_alias())
    raise ActionFailed("later record failed")


@pytest.mark.django_db(transaction=True)
def test_later_failure_rolls_back_earlier_write(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_form_valid", write_then_fail)
    with pytest.raises(ActionFailed):
        post_selection(client_user_bulk_publisher_change, bulk_publishers[:2])
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]


@pytest.mark.django_db(transaction=True)
def test_success_message_after_rollback(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    client = client_user_bulk_publisher_change
    client.raise_request_exception = False
    original_write = BulkPublisherArchiveView.cv_form_valid
    original_hook = BulkPublisherArchiveView.cv_form_valid_hook
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_form_valid", write_then_fail)
    assert post_selection(client, bulk_publishers[:2]).status_code == 500
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert list(client.get("/bulk-publisher/").context["messages"]) == []

    def hook_then_fail(self, context):
        original_hook(self, context)
        raise ActionFailed("after message")

    monkeypatch.setattr(BulkPublisherArchiveView, "cv_form_valid", original_write)
    monkeypatch.setattr(BulkPublisherArchiveView, "cv_form_valid_hook", hook_then_fail)
    assert post_selection(client, bulk_publishers[:2]).status_code == 500
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert [str(message) for message in client.get("/bulk-publisher/").context["messages"]] == ["2 records processed."]


@pytest.mark.django_db(transaction=True)
def test_on_commit_failure_keeps_writes(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    def fail(self, context):
        raise ActionFailed("commit callback")

    monkeypatch.setattr(BulkPublisherArchiveView, "cv_on_commit", fail)
    with pytest.raises(ActionFailed):
        post_selection(client_user_bulk_publisher_change, bulk_publishers[:2])
    assert publisher_names() == ["Alpha (archived)", "Beta (archived)", "Locked Gamma"]


@pytest.mark.parametrize(
    "path,stage,count",
    [("archive", "execute", 1), ("archive", "execute", 2), ("archive-now", "review", 1), ("archive-now", "review", 2)],
)
def test_success_message_counts_processed_records(
    client_user_bulk_publisher_change, bulk_publishers, path, stage, count
):
    response = post_selection(client_user_bulk_publisher_change, bulk_publishers[:count], path=path, stage=stage)
    assert response.status_code == 302
    noun = "record" if count == 1 else "records"
    assert [str(message) for message in get_messages(response.wsgi_request)] == [f"{count} {noun} processed."]


def test_delete_recipe_deletes_eligible_records(
    client_user_bulk_publisher_change, user_bulk_publisher_change, cv_bulk_publisher, bulk_publishers
):
    from tests.test1.conftest import user_viewset_permission

    user_viewset_permission(user_bulk_publisher_change, cv_bulk_publisher, "delete")
    response = post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], path="bulk-delete")
    assert response.status_code == 302
    assert publisher_names() == ["Locked Gamma"]


def test_delete_recipe_blocks_protection_without_related_labels(client_user_bulk_publisher_delete, bulk_publishers):
    contract = Contract.objects.create(publisher=bulk_publishers[1], reference="Confidential contract")
    client = client_user_bulk_publisher_delete
    response = post_selection(client, bulk_publishers, path="bulk-delete", stage="review")
    assert response.status_code == 200
    assert "Deletion is blocked by related records." in soup(response).text_content()
    assert "Locked publishers cannot be deleted." in soup(response).text_content()
    assert str(contract) not in response.content.decode()
    assert client.post("/bulk-publisher/bulk-delete/", review_data(response)).status_code == 302
    assert publisher_names() == ["Beta", "Locked Gamma"]


@pytest.mark.django_db(transaction=True)
def test_delete_recipe_late_protection_rolls_back(client_user_bulk_publisher_delete, bulk_publishers, monkeypatch):
    original = Publisher.delete

    def delete(self, *args, **kwargs):
        if self.pk == bulk_publishers[1].pk:
            raise ProtectedError("late protection", {self})
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Publisher, "delete", delete)
    with pytest.raises(ProtectedError):
        post_selection(client_user_bulk_publisher_delete, bulk_publishers[:2], path="bulk-delete")
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]


def test_locked_archive_processes_unchanged_selection(client_user_bulk_publisher_change, bulk_publishers):
    response = post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], path="archive-locked")
    assert response.status_code == 302
    assert publisher_names() == ["Alpha (archived)", "Beta (archived)", "Locked Gamma"]


@pytest.mark.django_db(transaction=True)
def test_locked_archive_rejects_missing_row(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    from tests.test1.app.views_bulk import BulkPublisherLockedArchiveView, PublisherChanged

    deleted_pk = bulk_publishers[1].pk
    monkeypatch.setattr(
        BulkPublisherLockedArchiveView,
        "cv_post_hook",
        lambda self, context: Publisher.objects.filter(pk=deleted_pk).delete(),
    )
    with pytest.raises(PublisherChanged):
        post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], path="archive-locked")
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
    assert Publisher.objects.filter(pk=deleted_pk).exists()


@pytest.mark.django_db(transaction=True)
def test_locked_archive_rejects_newly_blocked_row(client_user_bulk_publisher_change, bulk_publishers, monkeypatch):
    from tests.test1.app.views_bulk import BulkPublisherLockedArchiveView, PublisherChanged

    monkeypatch.setattr(
        BulkPublisherLockedArchiveView,
        "cv_post_hook",
        lambda self, context: Publisher.objects.filter(pk=bulk_publishers[1].pk).update(name="Locked Beta"),
    )
    with pytest.raises(PublisherChanged):
        post_selection(client_user_bulk_publisher_change, bulk_publishers[:2], path="archive-locked")
    assert publisher_names() == ["Alpha", "Beta", "Locked Gamma"]
