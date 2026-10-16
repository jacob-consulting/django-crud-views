from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import CreateView

# import from the submodule, not the package: PrimaryKeys is bound late in crud_views.lib.viewset,
# so the package import fails while it is still initializing (see crud_views.lib.views.child)
from crud_views.lib.viewset import path_regs
from crud_views.lib.viewset.path_regs import PrimaryKeys

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
