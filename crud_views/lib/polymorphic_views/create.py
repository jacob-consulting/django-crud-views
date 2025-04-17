from crud_views.lib.view import CrudViewPermissionRequiredMixin
from .utils import PolymorphicCrudViewMixin
from ..views import CreateView
from ..viewset import path_regs, PrimaryKeys


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
