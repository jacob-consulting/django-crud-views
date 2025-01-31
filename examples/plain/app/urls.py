from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from app.views import IndexView
from app.views.author import cv_author
from app.views.book import cv_book
from app.views.bar import cv_bar
from app.views.baz import cv_baz
from app.views.foo import cv_foo
from app.views.poly import cv_poly

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns += (
        cv_author.urlpatterns +
        cv_book.urlpatterns +
        cv_baz.urlpatterns + cv_bar.urlpatterns + cv_foo.urlpatterns +
        cv_poly.urlpatterns
)
