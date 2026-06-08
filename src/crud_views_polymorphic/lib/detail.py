from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailView
from .utils import PolymorphicCrudViewMixin


class PolymorphicDetailView(PolymorphicCrudViewMixin, DetailView):
    pass


class PolymorphicDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDetailView):
    cv_permission = "view"
