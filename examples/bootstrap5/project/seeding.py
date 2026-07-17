from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

#: username, password, is_superuser — shown on the home and login pages
DEMO_USERS = [
    ("admin", "admin", True),
    ("alice", "alice", False),
    ("bob", "bob", False),
]


def ensure_demo_users() -> dict:
    """Create (or reset the password of) the demo users. Idempotent."""
    User = get_user_model()
    users = {}
    for username, password, superuser in DEMO_USERS:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"is_superuser": superuser, "is_staff": superuser},
        )
        user.set_password(password)
        user.save()
        users[username] = user
    return users


def grant_model_perms(user, model, actions=("view", "add", "change", "delete")) -> None:
    """Grant model-level permissions on `model` to `user`. Idempotent."""
    ct = ContentType.objects.get_for_model(model)
    for action in actions:
        perm = Permission.objects.get(content_type=ct, codename=f"{action}_{model._meta.model_name}")
        user.user_permissions.add(perm)
