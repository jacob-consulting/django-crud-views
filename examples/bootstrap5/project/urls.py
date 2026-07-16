from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from project.views import HomeView


class CrispyAuthenticationForm(AuthenticationForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout("username", "password", FormActions(Submit("login", "Log In")))
        return helper


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginView.as_view(form_class=CrispyAuthenticationForm), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    # example feature apps append their include() here
]

urlpatterns += [path("library/", include("library.urls"))]
urlpatterns += [path("nested/", include("nested.urls"))]
urlpatterns += [path("formsets/", include("formsets.urls"))]
urlpatterns += [path("workflow/", include("workflow.urls"))]
urlpatterns += [path("polymorphic/", include("polymorphic_demo.urls"))]
urlpatterns += [path("guardian/", include("guardian_demo.urls"))]
