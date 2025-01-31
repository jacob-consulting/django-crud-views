from crud_views.lib.view import CrudViewPermissionRequiredMixin

from ..views.delete import DeleteView


class PolymorphicDeleteView(DeleteView):
    pass


class PolymorphicDeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicDeleteView):  # this file
    cv_permission = "delete"
