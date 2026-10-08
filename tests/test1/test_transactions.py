"""
Transaction boundary around POST write phases (#31).

See docs/reference/request_lifecycle.md. Tests that patch registered view classes use
monkeypatch.setattr on the class (auto-restored); they never subclass with cv_viewset in the
class body, which would re-register the view key.
"""

from contextlib import nullcontext
from unittest import mock

from django.db import DEFAULT_DB_ALIAS, router, transaction

from crud_views.lib.check import CheckUnknownAttributes
from crud_views.lib.view.base import CrudView
from tests.test1.app.models import Publisher


class Boom(Exception):
    pass


def _boom(*args, **kwargs):
    raise Boom("hook failed")


def _record_on_commit(monkeypatch, view_class) -> list[dict]:
    """Replace view_class.cv_on_commit with a recorder; returns the list of contexts it saw."""
    calls: list[dict] = []
    monkeypatch.setattr(view_class, "cv_on_commit", lambda self, context: calls.append(context))
    return calls


# --- Task 1: core API --------------------------------------------------------------------------


def test_crud_view_is_atomic_by_default():
    assert CrudView.cv_atomic is True


def test_resource_views_are_not_atomic():
    from tests.test1.app.resources import S3FileTouchView

    assert S3FileTouchView.cv_atomic is False


def test_db_alias_follows_router():
    from tests.test1.app.views import PublisherCreateView

    with mock.patch.object(router, "db_for_write", return_value="other") as db_for_write:
        assert PublisherCreateView().cv_get_db_alias() == "other"
    db_for_write.assert_called_once_with(Publisher)


def test_get_atomic_wraps_in_atomic_on_routed_alias():
    from tests.test1.app.views import PublisherCreateView

    view = PublisherCreateView()
    with mock.patch.object(view, "cv_get_db_alias", return_value=DEFAULT_DB_ALIAS):
        ctx = view.cv_get_atomic()
    assert isinstance(ctx, transaction.Atomic)
    assert ctx.using == DEFAULT_DB_ALIAS


def test_get_atomic_is_noop_when_disabled():
    from tests.test1.app.views import PublisherCreateView

    view = PublisherCreateView()
    view.cv_atomic = False
    assert isinstance(view.cv_get_atomic(), nullcontext)


def test_resource_db_alias_never_consults_router():
    from tests.test1.app.resources import S3FileTouchView

    with mock.patch.object(router, "db_for_write", side_effect=AssertionError("router consulted")):
        assert S3FileTouchView().cv_get_db_alias() == DEFAULT_DB_ALIAS


def test_cv_on_commit_default_is_noop():
    from tests.test1.app.views import PublisherCreateView

    assert PublisherCreateView().cv_on_commit({}) is None


def test_cv_atomic_is_a_known_attribute():
    class NotAtomicView(CrudView):  # bare subclass: not registered (no cv_viewset in body)
        cv_atomic = False

    assert list(CheckUnknownAttributes(context=NotAtomicView).messages()) == []
