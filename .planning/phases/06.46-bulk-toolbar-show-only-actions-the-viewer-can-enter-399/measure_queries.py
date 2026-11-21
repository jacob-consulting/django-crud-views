"""Planning diagnostic only: baseline rendering plus in-memory entry-gate probes.

Run with pytest -p tests.test1.conftest explicitly; no product files are changed.
The injected gate loop is a cost probe, not the proposed effective-list implementation.
"""
import json
from collections import Counter

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from crud_views.lib.view.base import _cancel_target_available
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views_bulk import BulkBookListView, BulkBookMarkView, BulkPublisherCardView, BulkPublisherListView

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("rows", [1, 5])
@pytest.mark.parametrize("action_count", [0, 1, 4])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("card", [False, True])
def test_measure(request, monkeypatch, rows, action_count, nested, card):
    from django.urls import path, reverse, clear_url_caches
    from django.conf import settings
    from importlib import import_module
    urls = import_module(settings.ROOT_URLCONF)
    from tests.test1.app.views_bulk import cv_bulk_book

    if nested:
        parent = Publisher.objects.create(name="Probe parent")
        for i in range(rows):
            Book.objects.create(title=f"Probe {i}", publisher=parent)
        client = request.getfixturevalue("client_user_bulk_book_change")
        source = BulkBookListView
        url = reverse(cv_bulk_book.get_router_name("list"), kwargs={"bulk_publisher_pk": parent.pk})
        if card:
            # Temporarily adapt existing card fixture; URL remains a planning-only route.
            source = BulkPublisherCardView
            monkeypatch.setattr(source, "cv_viewset", cv_bulk_book)
            monkeypatch.setattr(source, "cv_order_fields", ["title"])
            monkeypatch.setattr(source, "paginate_by", 20)
            parent_arg = cv_bulk_book.get_parent_url_args(first_only=True)
            monkeypatch.setattr(urls, "urlpatterns", [path(f"probe/<int:{parent_arg}>/", source.as_view()), *urls.urlpatterns])
            clear_url_caches()
            url = f"/probe/{parent.pk}/"
        keys = ("mark",) * action_count
    else:
        for i in range(rows):
            Publisher.objects.create(name=f"Probe {i}")
        source = BulkPublisherCardView if card else BulkPublisherListView
        monkeypatch.setattr(source, "paginate_by", 20)
        client = request.getfixturevalue("client_user_bulk_publisher_delete")
        url = "/bulk-publisher/card/" if card else "/bulk-publisher/"
        keys = ("archive", "archive_now", "rename", "bulk_delete")[:action_count]
    monkeypatch.setattr(source, "cv_bulk_actions", keys)
    client.get(url)  # warm URL/template caches, fresh actor still loaded per HTTP request
    with CaptureQueriesContext(connection) as baseline:
        response = client.get(url)
    assert response.status_code == 200
    calls = Counter()
    original_context = source.get_context_data
    original_access = BulkBookMarkView.cv_has_access
    if nested:
        def access(cls, user, obj):
            calls["access"] += 1
            assert obj is None
            return original_access(user, obj)
        def state(cls, user, obj):
            calls["state"] += 1
            assert obj.pk == parent.pk
            return True
        monkeypatch.setattr(BulkBookMarkView, "cv_has_access", classmethod(access))
        monkeypatch.setattr(BulkBookMarkView, "cv_action_enabled", classmethod(state))
    def context(self, **kwargs):
        for key in keys:
            assert _cancel_target_available(self.cv_viewset.get_view_class(key), self.request.user, None, self)
        return original_context(self, **kwargs)
    monkeypatch.setattr(source, "get_context_data", context)
    with CaptureQueriesContext(connection) as gated:
        response = client.get(url)
    assert response.status_code == 200
    print("MEASURE " + json.dumps({"nested": nested, "card": card, "rows": rows, "actions": action_count,
          "baseline": len(baseline), "gate_probe": len(gated), "calls": dict(calls)}))
