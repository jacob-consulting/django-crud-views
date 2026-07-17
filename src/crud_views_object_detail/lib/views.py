from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import DetailCustomView  # Task 7 switches this to the renamed DetailView
from crud_views_object_detail.lib.mixins import ObjectDetailMixin


class ObjectDetailView(ObjectDetailMixin, DetailCustomView):
    pass


class ObjectDetailViewPermissionRequired(CrudViewPermissionRequiredMixin, ObjectDetailView):
    cv_permission = "view"
