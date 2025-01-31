from crud_views.lib.view import CrudViewPermissionRequiredMixin
from .utils import PolymorphicCrudViewMixin
from ..views import UpdateView


class PolymorphicUpdateView(PolymorphicCrudViewMixin, UpdateView):
    pass


class PolymorphicUpdateViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicUpdateView):  # this file
    cv_permission = "change"
