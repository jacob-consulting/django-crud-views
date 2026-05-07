from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ActionViewPermissionRequired,
)
from crud_views.lib.views.manage import ManageView
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianQuerysetMixin,
    GuardianParentPermissionMixin,
)

GUARDIAN_MIXINS = [
    (GuardianObjectPermissionMixin, "ObjectPermissionMixin"),
    (GuardianQuerysetMixin, "QuerysetMixin"),
    (GuardianParentPermissionMixin, "ParentMixin"),
]


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
            Returns False. GuardianQuerysetMixin.cv_get_context() handles the
            real check by resolving the parent from URL kwargs and calling
            cv_create_has_access(). This is a safe fallback for any call path
            that bypasses the list view override.

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
            return False  # was: return True — GuardianQuerysetMixin.cv_get_context handles the real check

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


class GuardianManageView(ManageView):
    template_name = "crud_views/view_guardian_manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent = self.cv_viewset.parent
        if parent is not None:
            parent_vs = parent.viewset
            perm_key = self.cv_viewset.cv_guardian_parent_permission
            perm_codename = (
                parent_vs.permissions.get(perm_key, perm_key).split(".")[-1] if perm_key is not None else None
            )
            parent_viewset_info = (
                f"{parent_vs.name} ({perm_codename} → guardian)"
                if perm_codename is not None
                else f"{parent_vs.name} (no permission)"
            )
        else:
            parent_viewset_info = None
        context["guardian_config"] = {
            "cv_guardian_parent_permission": self.cv_viewset.cv_guardian_parent_permission,
            "cv_guardian_parent_create_permission": self.cv_viewset.cv_guardian_parent_create_permission,
            "cv_guardian_accept_global_perms": self.cv_viewset.cv_guardian_accept_global_perms,
            "parent_viewset": parent_viewset_info,
        }
        return context

    def get_permission_holders(self):
        from django.contrib.contenttypes.models import ContentType
        from guardian.models import GroupObjectPermission
        from django.db.models import Count

        holders = {(r["group"], r["permission"]): r for r in super().get_permission_holders()}

        ct = ContentType.objects.get_for_model(self.cv_viewset.model)
        codename_to_key = {perm.split(".")[1]: key for key, perm in self.cv_viewset.permissions.items()}

        qs = (
            GroupObjectPermission.objects.filter(permission__content_type=ct)
            .values("group__name", "permission__codename")
            .annotate(object_count=Count("object_pk", distinct=True))
        )
        for row in qs:
            group_name = row["group__name"]
            perm_key = codename_to_key.get(row["permission__codename"])
            if perm_key is None:
                continue
            k = (group_name, perm_key)
            if k in holders:
                holders[k]["object_count"] = row["object_count"]
            else:
                holders[k] = {
                    "group": group_name,
                    "permission": perm_key,
                    "has_model_perm": False,
                    "object_count": row["object_count"],
                    "users": [],
                }

        return sorted(holders.values(), key=lambda r: (r["group"], r["permission"]))

    def get_view_data(self):
        data = super().get_view_data()
        for key, view_data in data.items():
            view_class = self.cv_viewset.get_all_views()[key]
            labels = [label for cls, label in GUARDIAN_MIXINS if issubclass(view_class, cls)]
            view_data["base"]["guardian_mixin"] = " + ".join(labels) if labels else "—"
        return data
