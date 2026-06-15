import pytest

from tests.test1.app.views import AuthorDeleteView


def test_cv_action_enabled_default_true():
    # Default hook: every action is enabled unless a subclass overrides it.
    assert AuthorDeleteView.cv_action_enabled(user=None, obj=None) is True


def test_cv_action_enabled_can_be_overridden():
    class DisabledDelete(AuthorDeleteView):
        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            return False

    assert DisabledDelete.cv_action_enabled(user=None, obj=None) is False


@pytest.mark.django_db
def test_disabled_list_action_button_hidden(client_user_publisher_view_delete, publisher_penguin, monkeypatch):
    from tests.test1.app.views import PublisherDeleteView

    monkeypatch.setattr(
        PublisherDeleteView,
        "cv_action_enabled",
        classmethod(lambda cls, user, obj=None: False),
    )
    response = client_user_publisher_view_delete.get("/publisher/")
    html = response.content.decode()
    assert response.status_code == 200
    # Hidden entirely — neither an active NOR a greyed/disabled delete control renders.
    assert f"/publisher/{publisher_penguin.pk}/delete/" not in html
    # The row still renders other (enabled) actions, proving only delete was dropped.
    assert f"/publisher/{publisher_penguin.pk}/update/" in html


@pytest.mark.django_db
def test_enabled_list_action_button_present(client_user_publisher_view_delete, publisher_penguin):
    response = client_user_publisher_view_delete.get("/publisher/")
    assert response.status_code == 200
    assert f"/publisher/{publisher_penguin.pk}/delete/" in response.content.decode()


@pytest.mark.django_db
def test_disabled_plain_object_action_request_denied(client_user_publisher_view_delete, publisher_penguin, monkeypatch):
    # Plain view: a disabled delete must 403 on direct GET and POST.
    from tests.test1.app.views import PublisherDeleteView

    monkeypatch.setattr(
        PublisherDeleteView,
        "cv_action_enabled",
        classmethod(lambda cls, user, obj=None: False),
    )
    pk = publisher_penguin.pk
    assert client_user_publisher_view_delete.get(f"/publisher/{pk}/delete/").status_code == 403
    assert client_user_publisher_view_delete.post(f"/publisher/{pk}/delete/").status_code == 403


@pytest.mark.django_db
def test_enabled_plain_object_action_request_allowed(client_user_publisher_view_delete, publisher_penguin):
    # Regression: default hook lets the delete confirm page load.
    pk = publisher_penguin.pk
    assert client_user_publisher_view_delete.get(f"/publisher/{pk}/delete/").status_code == 200


@pytest.mark.django_db
def test_disabled_guardian_object_action_request_denied(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, monkeypatch
):
    # Guardian object view: enforcement rides get_object().
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianAuthorDeleteView

    user_guardian_object_perm(user_guardian, cv_guardian_author, "delete", author_douglas_adams)
    monkeypatch.setattr(
        GuardianAuthorDeleteView,
        "cv_action_enabled",
        classmethod(lambda cls, user, obj=None: False),
    )
    pk = author_douglas_adams.pk
    assert client_guardian.get(f"/guardian_author/{pk}/delete/").status_code == 403
    assert client_guardian.post(f"/guardian_author/{pk}/delete/").status_code == 403


@pytest.mark.django_db
def test_disabled_guardian_child_create_request_denied(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a, monkeypatch
):
    # Guardian child create: enforcement rides GuardianParentPermissionMixin.dispatch().
    from django.urls import reverse
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    monkeypatch.setattr(
        GuardianBookCreateView,
        "cv_action_enabled",
        classmethod(lambda cls, user, obj=None: False),
    )
    # Child-create URL is /guardian_publisher/<pk>/guardian_book/create/ (resolved via reverse).
    url = reverse("guardian_book-create", kwargs={"guardian_publisher_pk": publisher_a.pk})
    assert client_guardian.get(url).status_code == 403
    assert client_guardian.post(url, data={}).status_code == 403
