from crud_views.lib.view import ViewSetViewPermissionRequiredMixin

from ..views.delete import DeleteView


class PolymorphicDeleteView(DeleteView):
    pass


class PolymorphicDeleteViewPermissionRequired(ViewSetViewPermissionRequiredMixin, PolymorphicDeleteView):  # this file
    vs_permission = "delete"
