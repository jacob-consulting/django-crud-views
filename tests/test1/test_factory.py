import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from tests.test1.app.views import AuthorListView
from crud_views.lib.viewset import ViewSet

User = get_user_model()


def instantiate_view(cls, request, **initkwargs):
    """Instantiate a view class via RequestFactory without dispatching."""
    view = cls(**initkwargs)
    view.setup(request)
    return view


@pytest.mark.django_db
def test_factory_success_url(user_author_view: User, cv_author: ViewSet, author_douglas_adams):
    factory = RequestFactory()
    request = factory.get("/author/")
    request.user = user_author_view

    view = instantiate_view(AuthorListView, request)
    success_url = view.get_success_url()

    assert success_url == "/author/"
