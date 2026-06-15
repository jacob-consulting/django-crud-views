import pytest

from tests.test1.app.views import AuthorDeleteView, BookCreateView


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
