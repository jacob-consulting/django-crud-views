from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from app.views import IndexView
from app.views.author import vs_author
from app.views.book import vs_book
from app.views.foo import vs_foo
from app.views.bar import vs_bar
from app.views.baz import vs_baz
from app.views.poly import vs_poly
from app.views.detail import vs_detail


class CrispyAuthenticationForm(AuthenticationForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout("username", "password", FormActions(Submit("login", "Log In")))
        return helper


urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(form_class=CrispyAuthenticationForm), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns += (
        vs_author.urlpatterns +
        vs_book.urlpatterns +
        vs_foo.urlpatterns +
        vs_bar.urlpatterns +
        vs_baz.urlpatterns +
        vs_poly.urlpatterns +
        vs_detail.urlpatterns
)
