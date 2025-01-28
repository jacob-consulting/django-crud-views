from crud_views.lib.polymorphic_views.create import PolymorphicCreateView, PolymorphicCreateViewPermissionRequired
from crud_views.lib.polymorphic_views.create_select import PolymorphicCreateSelectView, \
    PolymorphicCreateSelectViewPermissionRequired
from crud_views.lib.polymorphic_views.detail import PolymorphicDetailView, PolymorphicDetailViewPermissionRequired
from crud_views.lib.polymorphic_views.update import PolymorphicUpdateView, PolymorphicUpdateViewPermissionRequired

__all__ = [
    "PolymorphicDetailView",
    "PolymorphicDetailViewPermissionRequired",
    "PolymorphicCreateSelectView",
    "PolymorphicCreateSelectViewPermissionRequired",
    "PolymorphicCreateView",
    "PolymorphicCreateViewPermissionRequired",
    "PolymorphicUpdateView",
    "PolymorphicUpdateViewPermissionRequired",
]
