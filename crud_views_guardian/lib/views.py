from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ActionViewPermissionRequired,
)
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianQuerysetMixin,
    GuardianParentPermissionMixin,
)


class GuardianDetailViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailViewPermissionRequired
):
    pass


class GuardianUpdateViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired
):
    pass


class GuardianDeleteViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DeleteViewPermissionRequired
):
    pass


class GuardianActionViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, ActionViewPermissionRequired
):
    pass


class GuardianListViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianQuerysetMixin, ListViewPermissionRequired
):
    pass


class GuardianCreateViewPermissionRequired(GuardianParentPermissionMixin, CreateViewPermissionRequired):
    """
    For top-level creates: GuardianParentPermissionMixin is a no-op (no parent).
    Django's PermissionRequiredMixin checks model-level add_<model> permission.

    For child creates: GuardianParentPermissionMixin checks per-object permission
    on the parent instance using cv_guardian_parent_create_permission (falls back
    to cv_guardian_parent_permission). No model-level add_<child> check is made.
    """

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Three-case permission check for create button visibility.

        Case 1 — Top-level create (cv_viewset.parent is None):
            Falls through to the base class, which checks the model-level
            add_<model> permission. Top-level creates intentionally require a
            model-level grant; there is no parent object to check against.

        Case 2 — Child create, no object (obj=None, e.g. book list page):
            Returns True unconditionally. The list page has no single object, so
            we cannot check the parent permission here. The real enforcement
            happens in dispatch() via GuardianParentPermissionMixin, which checks
            the parent object permission and raises 403 if denied. A user without
            the required grant will be stopped on click — the button showing is
            correct UX.

        Case 3 — Child create, parent object available (e.g. author detail page):
            When obj is an instance of the parent model, checks
            cv_guardian_parent_create_permission (falling back to
            cv_guardian_parent_permission) on that specific parent object via
            guardian's ObjectPermissionChecker. This gives precise per-object
            button visibility: "add book" only appears for parent objects the user
            is actually allowed to create children under.

            If obj is provided but is not an instance of the parent model
            (unexpected; wrong type passed by some other render path), falls back
            to True — cannot determine access without the right object type.
        """
        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None:
            return True

        parent_vs = cls.cv_viewset.parent.viewset
        if isinstance(obj, parent_vs.model):
            perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None) or getattr(
                cls.cv_viewset, "cv_guardian_parent_permission", "view"
            )
            perm = parent_vs.permissions.get(perm_key)
            accept_global = getattr(cls, "cv_guardian_accept_global_perms", False)
            if accept_global and user.has_perm(perm):
                return True
            from guardian.core import ObjectPermissionChecker

            return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], obj)

        return True
