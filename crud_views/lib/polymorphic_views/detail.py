from crud_views.lib.view import CrudViewPermissionRequiredMixin
from .utils import PolymorphicCrudViewMixin
from ..views import DetailView


class PolymorphicDetailView(PolymorphicCrudViewMixin, DetailView):
    pass


class PolymorphicDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDetailView):  # this file
    cv_permission = "view"
