from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailCustomView
from .utils import PolymorphicCrudViewMixin


class PolymorphicDetailView(PolymorphicCrudViewMixin, DetailCustomView):
    pass


class PolymorphicDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDetailView):
    cv_permission = "view"
