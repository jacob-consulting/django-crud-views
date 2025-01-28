def user_viewset_permission(user, viewset, perm):
    from django.contrib.auth.models import Permission

    app, codename = viewset.permissions[perm].split(".")

    permission = Permission.objects.get(codename=codename)
    user.user_permissions.add(permission)
    user.save()
