from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

#: username, password, is_superuser — shown on the home and login pages
DEMO_USERS = [
    ("alice", "alice", False),
    ("bob", "bob", False),
    ("developer", "developer", False),
]


def ensure_demo_users() -> dict:
    """Create (or reset the password of) the demo users. Idempotent."""
    user_model = get_user_model()
    users = {}
    for username, password, superuser in DEMO_USERS:
        user, _ = user_model.objects.get_or_create(
            username=username,
            defaults={"is_superuser": superuser, "is_staff": superuser},
        )
        if username == "developer":
            from django.core.management.base import CommandError

            for flag, expected in (("is_active", True), ("is_staff", False), ("is_superuser", False)):
                if getattr(user, flag) != expected:
                    raise CommandError(f"developer has conflicting {flag}; leaving the account unchanged.")
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


def ensure_developer_read_access(user) -> None:
    """Grant only the example's explicit reads; report customized privileges rather than removing them."""
    from django.apps import apps
    from django.contrib.auth.models import Group
    from django.core.management.base import CommandError

    from crud_views.lib.settings import crud_views_settings

    # Deliberately explicit: adding an app must not silently expand this account's permissions.
    model_names = {
        "library": ("Author", "Book", "Contract"),  # card_view also uses Author
        "nested": ("Company", "Department", "Employee", "Office"),
        "formsets": ("Questionnaire", "Question", "Choice", "Checklist", "ChecklistItem"),
        "workflow": ("Campaign",),
        "polymorphic_demo": ("Vehicle", "Car", "Truck", "Motorcycle"),
        "guardian_demo": ("Document", "Note"),
        "object_detail": ("Supplier", "Warehouse", "Tag", "Product"),
        "breadcrumbs": ("Workspace", "Board"),
        "conditional": ("Registration", "Event", "Session", "Speaker", "Customer"),
        "formsets_conditional": ("Conference", "Session", "Speaker"),
        "custom_form": ("Contact",),
        "context_buttons": ("Ticket",),
        "action_menus": ("Chore", "Step"),
        "label_modes": ("Gadget",),
        "flash_messages": ("Notice",),
        "disabled_actions": ("Ticket",),
        "delete_demo": ("Project", "Task", "Milestone"),
    }
    models = [apps.get_model(app, name) for app, names in model_names.items() for name in names]
    resource_perm = Permission.objects.get(content_type__app_label="resources", codename="view_s3file")
    allowed = {(ContentType.objects.get_for_model(model).pk, f"view_{model._meta.model_name}") for model in models}
    allowed.add((resource_perm.content_type_id, resource_perm.codename))
    group, _ = Group.objects.get_or_create(name=crud_views_settings.manage_group)

    # Fresh relation queries avoid both prefetched data and Django's user permission caches.
    def check(permissions, source):
        for permission in permissions.select_related("content_type"):
            if (permission.content_type_id, permission.codename) not in allowed:
                name = f"{permission.content_type.app_label}.{permission.codename}"
                raise CommandError(f"{source} has conflicting permission {name}; leaving the grant unchanged.")

    check(Permission.objects.filter(user=user), f"developer {user.username}")
    for membership in Group.objects.filter(user=user) | Group.objects.filter(pk=group.pk):
        check(Permission.objects.filter(group=membership), f"group {membership.name}")

    user.groups.add(group)
    for model in models:
        grant_model_perms(user, model, actions=("view",))
    user.user_permissions.add(resource_perm)
