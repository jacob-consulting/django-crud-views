from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views.delete import DeleteView


class PolymorphicDeleteView(DeleteView):
    pass


class PolymorphicDeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDeleteView):
    cv_permission = "delete"
