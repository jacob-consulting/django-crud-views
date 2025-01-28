from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from app.views import IndexView
from app.views.author import vs_author
from app.views.book import vs_book
from app.views.bar import vs_bar
from app.views.baz import vs_baz
from app.views.foo import vs_foo
from app.views.poly import vs_poly

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns += (
        vs_author.urlpatterns +
        vs_book.urlpatterns +
        vs_baz.urlpatterns + vs_bar.urlpatterns + vs_foo.urlpatterns +
        vs_poly.urlpatterns
)
