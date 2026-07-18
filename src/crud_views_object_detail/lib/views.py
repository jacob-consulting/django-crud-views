from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailView
from crud_views_object_detail.lib.mixins import ObjectDetailMixin


class ObjectDetailView(ObjectDetailMixin, DetailView):
    pass


class ObjectDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, ObjectDetailView):
    cv_permission = "view"
