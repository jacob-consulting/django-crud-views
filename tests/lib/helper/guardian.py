def user_guardian_object_perm(user, viewset, perm, obj):
    """Assign a per-object guardian permission to a user."""
    from guardian.shortcuts import assign_perm

    assign_perm(viewset.permissions[perm], user, obj)
