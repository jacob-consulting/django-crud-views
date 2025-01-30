from crud_views.lib.view import ViewSetViewPermissionRequiredMixin
from .utils import PolymorphicViewSetViewMixin
from ..views import UpdateView


class PolymorphicUpdateView(PolymorphicViewSetViewMixin, UpdateView):
    pass


class PolymorphicUpdateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, PolymorphicUpdateView):  # this file
    cv_permission = "change"
