from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views import generic
from project.features import DocRef
from project.views import BreadcrumbMixin

from crud_views.lib.breadcrumb import Breadcrumb, BreadcrumbItem

#: the public Tabler theme demo (an onrender.com app); set this one constant when it is live
TABLER_DEMO_URL: str = ""


DOC_LINKS = [
    (_("Custom themes"), "reference/theme.md"),
    (_("Base template"), "reference/templates.md"),
    (_("Buttons"), "reference/buttons.md"),
    (_("Icons"), "reference/icons.md"),
]


class ThemeIndexView(BreadcrumbMixin, LoginRequiredMixin, generic.TemplateView):
    """A pointer page, not a CRUD view: it has no ViewSet, so it supplies its own breadcrumb trail."""

    template_name = "theming/index.html"

    def cv_breadcrumb_get(self) -> Breadcrumb:
        return Breadcrumb(items=(*self.cv_breadcrumb_prefix(), BreadcrumbItem(title=_("Theme"))))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cv_breadcrumb"] = self.cv_breadcrumb()
        context["doc_links"] = [(title, DocRef(page=page, label=page).url) for title, page in DOC_LINKS]
        context["tabler_demo_url"] = TABLER_DEMO_URL
        return context
