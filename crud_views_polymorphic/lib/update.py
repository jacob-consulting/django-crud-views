from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import UpdateView
from .utils import PolymorphicCrudViewMixin


class PolymorphicUpdateView(PolymorphicCrudViewMixin, UpdateView):
    pass


class PolymorphicUpdateViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicUpdateView):
    cv_permission = "change"
