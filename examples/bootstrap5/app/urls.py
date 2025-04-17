from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from app.views import IndexView
from app.views.author import cv_author
from app.views.book import cv_book
from app.views.foo import cv_foo
from app.views.bar import cv_bar
from app.views.baz import cv_baz
from app.views.poly import cv_poly
from app.views.detail import cv_detail
from app.views.group import cv_group
from app.views.group_members import cv_person
from app.views.formset import cv_poly_formset
from app.views.formset.parent import cv_poly_parent_formset
from app.views.formset.question import cv_question


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
        cv_author.urlpatterns +
        cv_book.urlpatterns +
        cv_foo.urlpatterns +
        cv_bar.urlpatterns +
        cv_baz.urlpatterns +
        cv_poly.urlpatterns +
        cv_detail.urlpatterns +
        cv_group.urlpatterns +
        cv_person.urlpatterns +
        cv_poly_formset.urlpatterns +
        cv_poly_parent_formset.urlpatterns +
        cv_question.urlpatterns
)
