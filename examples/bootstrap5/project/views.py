from django.views import generic

from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin

from project.features import FEATURES


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    """Project-wide breadcrumb adoption point: every example view inherits this first."""


class HomeView(generic.TemplateView):
    template_name = "project/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["features"] = FEATURES
        return context
