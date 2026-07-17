from django.views import generic

from project.features import FEATURES


class HomeView(generic.TemplateView):
    template_name = "project/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["features"] = FEATURES
        return context
