"""
Transaction boundary around POST write phases (#31).

See docs/reference/request_lifecycle.md. Tests that patch registered view classes use
monkeypatch.setattr on the class (auto-restored); they never subclass with cv_viewset in the
class body, which would re-register the view key.
"""

from contextlib import nullcontext
from unittest import mock

import pytest
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


# --- Task 2: form views ------------------------------------------------------------------------


@pytest.fixture
def client_user_genre_add(client, db):
    from django.contrib.auth.models import User

    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import cv_genre

    user = User.objects.create_user(username="user_genre_add", password="password")
    user_viewset_permission(user, cv_genre, "add")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_create_hook_exception_rolls_back_save(client_user_publisher_add, monkeypatch):
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Rolled Back"})
    assert not Publisher.objects.filter(name="Rolled Back").exists()


@pytest.mark.django_db
def test_create_hook_exception_keeps_row_without_atomic(client_user_publisher_add, monkeypatch):
    """cv_atomic = False restores the pre-0.27 autocommit behaviour (guard: passes before and after)."""
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_atomic", False)
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Kept"})
    assert Publisher.objects.filter(name="Kept").exists()


@pytest.mark.django_db
def test_update_hook_exception_rolls_back_save(client_user_publisher_change, monkeypatch):
    from tests.test1.app.views import PublisherUpdateView

    publisher = Publisher.objects.create(name="Old")
    monkeypatch.setattr(PublisherUpdateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_change.post(f"/publisher/{publisher.pk}/update/", {"name": "New"})
    publisher.refresh_from_db()
    assert publisher.name == "Old"


@pytest.mark.django_db
def test_custom_form_view_write_rolls_back(client_user_author_view, monkeypatch):
    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorContactView

    author = Author.objects.create(first_name="First", last_name="Author")

    def write(self, context):
        self.object.pseudonym = "written"
        self.object.save()

    monkeypatch.setattr(AuthorContactView, "cv_form_valid", write)
    monkeypatch.setattr(AuthorContactView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_author_view.post(f"/author/{author.pk}/contact/", {"subject": "hi", "body": "there"})
    author.refresh_from_db()
    assert author.pseudonym is None


@pytest.mark.django_db
def test_on_commit_runs_once_after_success(client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_add.post("/publisher/create/", {"name": "Committed"})
    assert response.status_code == 302
    assert len(calls) == 1
    assert calls[0]["object"].name == "Committed"


@pytest.mark.django_db
def test_on_commit_not_called_for_invalid_form(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client_user_publisher_add.post("/publisher/create/", {"name": ""})
    assert response.status_code == 200
    assert calls == []
    assert callbacks == []


@pytest.mark.django_db
def test_on_commit_not_called_after_rollback(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with django_capture_on_commit_callbacks(execute=True), pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Rolled Back"})
    assert calls == []


@pytest.mark.django_db
def test_on_commit_error_keeps_committed_data(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 4: a failing side effect must not undo the committed write."""
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", _boom)
    with pytest.raises(Boom), django_capture_on_commit_callbacks(execute=True):
        client_user_publisher_add.post("/publisher/create/", {"name": "Committed"})
    assert Publisher.objects.filter(name="Committed").exists()


@pytest.mark.parametrize("atomic", [True, False])
@pytest.mark.django_db(transaction=True)
def test_on_commit_runs_before_redirect_in_autocommit(client_user_publisher_add, monkeypatch, atomic):
    """Real commits (no test transaction): cv_on_commit runs inside the view, before the redirect."""
    from tests.test1.app.views import PublisherCreateView

    order: list[str] = []
    original_redirect = PublisherCreateView.cv_form_valid_redirect

    def redirect(self, context):
        order.append("redirect")
        return original_redirect(self, context)

    monkeypatch.setattr(PublisherCreateView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", lambda self, context: order.append("commit"))
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_redirect", redirect)
    response = client_user_publisher_add.post("/publisher/create/", {"name": "Autocommit"})
    assert response.status_code == 302
    assert order == ["commit", "redirect"]


@pytest.mark.django_db(transaction=True)
def test_on_commit_deferred_to_request_commit_with_atomic_requests(client_user_publisher_add, monkeypatch):
    """Review focus 1: under ATOMIC_REQUESTS the view's atomic is a savepoint, so cv_on_commit
    waits for the request transaction, i.e. runs after the view returned."""
    from django.db import connection

    from tests.test1.app.views import PublisherCreateView

    order: list[str] = []
    original_redirect = PublisherCreateView.cv_form_valid_redirect

    def redirect(self, context):
        order.append("redirect")
        return original_redirect(self, context)

    monkeypatch.setitem(connection.settings_dict, "ATOMIC_REQUESTS", True)
    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", lambda self, context: order.append("commit"))
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_redirect", redirect)
    response = client_user_publisher_add.post("/publisher/create/", {"name": "Deferred"})
    assert response.status_code == 302
    assert order == ["redirect", "commit"]


@pytest.mark.django_db
def test_parent_fk_create_rolls_back(client_user_book_add, publisher_penguin, monkeypatch):
    from tests.test1.app.models import Book
    from tests.test1.app.views import BookCreateView

    monkeypatch.setattr(BookCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_book_add.post(f"/publisher/{publisher_penguin.pk}/book/create/", {"title": "Orphan"})
    assert not Book.objects.filter(title="Orphan").exists()


@pytest.mark.django_db
def test_m2m_parent_create_links_parent(client_user_genre_add, publisher_penguin):
    from tests.test1.app.models import Genre

    response = client_user_genre_add.post(f"/publisher/{publisher_penguin.pk}/genre/create/", {"name": "Sci-Fi"})
    assert response.status_code == 302
    assert list(publisher_penguin.genres.values_list("name", flat=True)) == ["Sci-Fi"]
    assert Genre.objects.count() == 1


@pytest.mark.django_db
def test_m2m_add_failure_leaves_no_orphan(client_user_genre_add, publisher_penguin, monkeypatch):
    """The object is saved before m2m.add(); a failure in between must roll the save back."""
    from tests.test1.app.models import Genre
    from tests.test1.app.views import GenreCreateView

    monkeypatch.setattr(GenreCreateView, "cv_parent_many_to_many_through_defaults", _boom)
    with pytest.raises(Boom):
        client_user_genre_add.post(f"/publisher/{publisher_penguin.pk}/genre/create/", {"name": "Orphan"})
    assert not Genre.objects.filter(name="Orphan").exists()


@pytest.mark.django_db
def test_polymorphic_create_goes_through_seam(client_user_vehicle_add, monkeypatch, django_capture_on_commit_callbacks):
    from django.contrib.contenttypes.models import ContentType

    from tests.test1.app.models import Car
    from tests.test1.app.views import VehicleCreateView

    calls = _record_on_commit(monkeypatch, VehicleCreateView)
    car_ct = ContentType.objects.get_for_model(Car)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_vehicle_add.post(f"/vehicle/create//ct/{car_ct.id}/", {"name": "Coupe", "doors": 2})
    assert response.status_code == 302
    assert len(calls) == 1


# --- Task 3: delete views ----------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_hook_exception_keeps_object(client_user_publisher_delete, monkeypatch):
    from tests.test1.app.views import PublisherDeleteView

    publisher = Publisher.objects.create(name="Survivor")
    monkeypatch.setattr(PublisherDeleteView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_delete.post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    assert Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_delete_runs_on_commit(client_user_publisher_delete, monkeypatch, django_capture_on_commit_callbacks):
    from tests.test1.app.views import PublisherDeleteView

    publisher = Publisher.objects.create(name="Gone")
    calls = _record_on_commit(monkeypatch, PublisherDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_delete.post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert len(calls) == 1
    assert not Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_delete_protection_skips_write_phase(
    client_user_publisher_protected_delete, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 3: a protection veto renders the form again; no delete, no cv_on_commit."""
    from tests.test1.app.views import PublisherProtectedDeleteView

    publisher = Publisher.objects.create(name="Protected")
    calls = _record_on_commit(monkeypatch, PublisherProtectedDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_protected_delete.post(
            f"/publisher_protected/{publisher.pk}/delete/", {"confirm": True}
        )
    assert response.status_code == 200
    assert calls == []
    assert Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_modal_delete_runs_on_commit_and_keeps_204(
    client_user_author_modal, author_douglas_adams, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 2: modal submits answer 204 + X-CV-Redirect and still run cv_on_commit."""
    from tests.test1.app.views import AuthorModalDeleteView

    calls = _record_on_commit(monkeypatch, AuthorModalDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_author_modal.post(
            f"/author_modal/{author_douglas_adams.pk}/delete/", {"confirm": True}, headers={"X-CV-Modal": "true"}
        )
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"
    assert len(calls) == 1


@pytest.mark.django_db
def test_guardian_delete_goes_through_seam(
    client_guardian, user_guardian, publisher_a, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    calls = _record_on_commit(monkeypatch, GuardianPublisherCascadeDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_guardian.post(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert len(calls) == 1
