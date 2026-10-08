from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


def seed():
    user_model = get_user_model()
    view_perm = Permission.objects.get(codename="view_s3file")
    delete_perm = Permission.objects.get(codename="delete_s3file")
    for username in ("alice", "bob"):
        user = user_model.objects.get(username=username)
        user.user_permissions.add(view_perm, delete_perm)
