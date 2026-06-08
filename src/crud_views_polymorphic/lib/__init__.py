from crud_views_polymorphic.lib.create import PolymorphicCreateView, PolymorphicCreateViewPermissionRequired
from crud_views_polymorphic.lib.create_select import (
    PolymorphicCreateSelectView,
    PolymorphicCreateSelectViewPermissionRequired,
)
from crud_views_polymorphic.lib.detail import PolymorphicDetailView, PolymorphicDetailViewPermissionRequired
from crud_views_polymorphic.lib.update import PolymorphicUpdateView, PolymorphicUpdateViewPermissionRequired

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
