from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views import CreateView

# import from the submodule, not the package: PrimaryKeys is bound late in crud_views.lib.viewset,
# so the package import fails while it is still initializing (see crud_views.lib.views.child)
from crud_views.lib.viewset import path_regs
from crud_views.lib.viewset.path_regs import PrimaryKeys

from .utils import PolymorphicCrudViewMixin


class PolymorphicCreateView(PolymorphicCrudViewMixin, CreateView):
    # not CreateView's ["home", "create"]: the "create" button can't be reversed without the content type
    cv_context_actions = crud_views_settings.polymorphic_create_context_actions

    @classmethod
    def cv_path_contribute(cls) -> str:
        """
        Here we inject the polymorphic_ctype_id path.

        The view path already ends in "/", so this adds "ct/<id>/". The optional "/?" keeps the
        double-slash URLs generated before 0.29.3 (create//ct/<id>/) resolving; reverse() omits it.
        """
        path_contribute = path_regs.get_path_pk("polymorphic_ctype_id", PrimaryKeys.INT)
        return f"/?ct/{path_contribute}/"


class PolymorphicCreateViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicCreateView):
    cv_permission = "add"
