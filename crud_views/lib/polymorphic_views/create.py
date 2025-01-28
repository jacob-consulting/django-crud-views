from crud_views.lib.view import ViewSetViewPermissionRequiredMixin
from .utils import PolymorphicViewSetViewMixin
from ..views import CreateView
from ..viewset import path_regs


class PolymorphicCreateView(PolymorphicViewSetViewMixin, CreateView):

    @classmethod
    def vs_path_contribute(cls) -> str:
        """
        Here we inject the polymorphic_ctype_id path.
        """
        path_contribute = path_regs.get_path_pk("polymorphic_ctype_id", path_regs.INT)
        return f"/ct/{path_contribute}/"


class PolymorphicCreateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, PolymorphicCreateView):
    vs_permission = "add"
