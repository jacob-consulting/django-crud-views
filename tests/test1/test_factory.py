import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from tests.lib.helper.boostrap5 import Table
from tests.test1.app.views import AuthorListView
from crud_views.lib.viewset import ViewSet

User = get_user_model()


def as_view(cls, **initkwargs):
    """Main entry point for a request-response process."""
    for key in initkwargs:
        if key in cls.http_method_names:
            raise TypeError(
                "The method name %s is not accepted as a keyword argument "
                "to %s()." % (key, cls.__name__)
            )
        if not hasattr(cls, key):
            raise TypeError(
                "%s() received an invalid keyword %r. as_view "
                "only accepts arguments that are already "
                "attributes of the class." % (cls.__name__, key)
            )

    def view(request, *args, **kwargs):
        self = cls(**initkwargs)
        self.setup(request, *args, **kwargs)
        if not hasattr(self, "request"):
            raise AttributeError(
                "%s instance has no 'request' attribute. Did you override "
                "setup() and forget to call super()?" % cls.__name__
            )
        return self

    view.view_class = cls
    view.view_initkwargs = initkwargs

    view.__doc__ = cls.__doc__
    view.__module__ = cls.__module__
    view.__annotations__ = cls.dispatch.__annotations__
    view.__dict__.update(cls.dispatch.__dict__)

    return view


@pytest.mark.django_db
def test_factory(user_author_view: User, cv_author: ViewSet, author_douglas_adams: User):

    factory = RequestFactory()

    request = factory.get("/author/")

    request.user = user_author_view
    # request.user = AnonymousUser()

    # view_cls = as_view(AuthorListView)


    view = as_view(AuthorListView)
    view_ins = view(request)

    x = view_ins.get_success_url()

    x = 1

    # response = AuthorListView.as_view()(request)

    # assert response.status_code ==  200