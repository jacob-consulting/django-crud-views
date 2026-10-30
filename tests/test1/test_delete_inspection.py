"""Real request regressions for read-only deletion inspection and confirmed writes."""

import pytest
from django.db import connection, models
from django.db.models.signals import post_delete

from tests.test1.app.models import Book, BookNote, Contract, Publisher
from tests.test1.app.views import PublisherCascadeDeleteView


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("outcome", ["invalid", "native-blocked", "business-blocked", "permitted"])
def test_tracer_real_preview_confirmation_and_commit(
    client_user_publisher_cascade_delete, publisher_penguin, monkeypatch, outcome
):
    events = []
    survivor = Publisher.objects.create(name="Survivor")
    survivor_book = Book.objects.create(title="Retained book", publisher=survivor)
    book = Book.objects.create(title="Cascade book", publisher=publisher_penguin)
    note = BookNote.objects.create(book=book, note="Reassign on confirmed delete")
    target_pk, book_pk = publisher_penguin.pk, book.pk

    def replacement():
        events.append("SET")
        Publisher.objects.create(name="Callback side effect")
        return survivor_book.pk

    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(replacement))
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_form_valid_hook", lambda self, context: events.append("hook"))

    def committed(self, context):
        assert not connection.in_atomic_block
        events.append("commit")

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_on_commit", committed)
    monkeypatch.setattr(
        PublisherCascadeDeleteView,
        "cv_check_delete_protection",
        lambda self: ["Business blocker"] if outcome == "business-blocked" else [],
    )
    blocker = Contract.objects.create(publisher=publisher_penguin, title="Hidden blocker")
    url = f"/publisher_cascade/{target_pk}/delete/"
    response = client_user_publisher_cascade_delete.get(url)
    assert events == [], "GET must describe relationships without running deletion callbacks"
    assert response.status_code == 200
    assert response.context["delete_preview_incomplete"] is True
    assert response.context["has_protected_objects"] is True
    assert response.context["related_summary"] == {"book": 1}
    assert response.context["protected_objects"] == []
    assert "Hidden blocker" not in response.content.decode()
    assert "This preview is incomplete." in response.content.decode()
    assert not Publisher.objects.filter(name="Callback side effect").exists()

    if outcome != "native-blocked":
        blocker.delete()

    def deleted(sender, instance, origin, **kwargs):
        assert type(origin) is Publisher
        assert origin.pk == target_pk
        events.append("delete-signal")

    post_delete.connect(deleted, sender=Book, weak=False)
    try:
        response = client_user_publisher_cascade_delete.post(url, {} if outcome == "invalid" else {"confirm": True})
    finally:
        post_delete.disconnect(deleted, sender=Book)
    if outcome == "permitted":
        assert response.status_code == 302
        assert events == ["SET", "delete-signal", "hook", "commit"]
        assert not Publisher.objects.filter(pk=target_pk).exists()
        assert not Book.objects.filter(pk=book_pk).exists()
        note.refresh_from_db()
        assert note.book_id == survivor_book.pk
        assert Publisher.objects.filter(name="Callback side effect").count() == 1
    else:
        assert response.status_code == 200
        assert events == []
        assert Publisher.objects.filter(pk=target_pk).exists()
        assert Book.objects.filter(pk=book_pk).exists()
        assert not Publisher.objects.filter(name="Callback side effect").exists()
