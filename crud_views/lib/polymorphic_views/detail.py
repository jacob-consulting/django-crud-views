from crud_views.lib.view import ViewSetViewPermissionRequiredMixin
from .utils import PolymorphicViewSetViewMixin
from ..views import DetailView


class PolymorphicDetailView(PolymorphicViewSetViewMixin, DetailView):
    pass


class PolymorphicDetailViewPermissionRequired(ViewSetViewPermissionRequiredMixin, PolymorphicDetailView):  # this file
    vs_permission = "view"
