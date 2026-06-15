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
