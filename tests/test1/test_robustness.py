"""
Audit task 3.5 (L4): minor robustness fixes.

- malformed JSON posted to the filter-persistence endpoint returns 400, not 500
- SessionData skips the session write when the with-block raised
- cv_check_delete_protection runs exactly once per DELETE POST
"""

import pytest
from django.test.client import Client, RequestFactory

from crud_views.lib.session import SessionData
from tests.test1.app.models import Publisher


@pytest.mark.django_db
def test_filter_persistence_post_rejects_malformed_json(user_publisher_view):
    client = Client(raise_request_exception=False)
    client.force_login(user_publisher_view)

    response = client.post("/publisher/", data="{not json", content_type="application/json")
    assert response.status_code == 400


def test_session_data_not_written_when_block_raises():
    class DummyRequest:
        session = {}

    class DummyView:
        request = DummyRequest()

    view = DummyView()

    with pytest.raises(ValueError, match="boom"):
        with SessionData(view=view) as sd:  # noqa: F841
            raise ValueError("boom")

    assert view.request.session == {}


def test_session_data_written_on_clean_exit():
    class DummyRequest:
        session = {}

    class DummyView:
        request = DummyRequest()

    view = DummyView()

    with SessionData(view=view):
        pass

    assert view.request.session != {}


@pytest.mark.django_db
def test_delete_protection_checked_once_per_post(user_publisher_delete):
    from tests.test1.app.views import PublisherDeleteView

    calls = []

    class CountingDeleteView(PublisherDeleteView):
        def cv_check_delete_protection(self) -> list[str]:
            calls.append(1)
            return []

    publisher = Publisher.objects.create(name="Counted")
    request = RequestFactory().post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    request.user = user_publisher_delete
    request.session = {}
    request._messages = __import__("django.contrib.messages.storage.base", fromlist=["BaseStorage"]).BaseStorage(
        request
    )

    response = CountingDeleteView.as_view()(request, pk=publisher.pk)
    assert response.status_code == 302
    assert len(calls) == 1
