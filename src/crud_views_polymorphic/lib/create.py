from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import CreateView
from crud_views.lib.viewset import PrimaryKeys, path_regs

from .utils import PolymorphicCrudViewMixin


class PolymorphicCreateView(PolymorphicCrudViewMixin, CreateView):
    @classmethod
    def cv_path_contribute(cls) -> str:
        """
        Here we inject the polymorphic_ctype_id path.
        """
        path_contribute = path_regs.get_path_pk("polymorphic_ctype_id", PrimaryKeys.INT)
        return f"/ct/{path_contribute}/"


class PolymorphicCreateViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicCreateView):
    cv_permission = "add"
