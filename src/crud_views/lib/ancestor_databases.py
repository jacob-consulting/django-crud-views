"""Database boundary of nested ViewSet requests.

Ancestor traversal, nested child data and their authorization records support only the ``default`` database. A
reached operation that selects another alias (a queryset's ``.using()`` or a database router) is a configuration
error: the selection is reported, never stripped, rerouted or retried on ``default``. Top-level requests never call
these guards, so their existing database behavior is unchanged.

The guards inspect selections (``QuerySet.db``, ``Model._state.db``, ``router.db_for_read/write``); they never run a
query and never intercept SQL. They are bounded to the Django auth and Guardian tables the shipped providers read.
"""

from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models import Model


def require_default_database(alias: str, *, context: str) -> None:
    """Raise ``ImproperlyConfigured`` unless ``alias`` is the default database; ``context`` names the operation."""
    if alias != DEFAULT_DB_ALIAS:
        raise ImproperlyConfigured(
            f"{context} uses database {alias!r}: nested ViewSets support only the {DEFAULT_DB_ALIAS!r} database "
            f"for their ancestors, their data and its authorization"
        )


def validate_authorization_databases(user, *, provider: str, model: type[Model] | None = None) -> None:
    """Before a nested permission gate reads authorization records: they and the actor must be on ``default``.

    Called at the gate that is about to use them (never as a preflight of deeper gates). It checks routes, not cached
    results, so a warm permission vocabulary or content-type cache cannot hide a newly nondefault route.

    - the actor: a saved user loaded from another database (its ``_state.db``); anonymous actors have no row
    - ``"model"``: the user, group, permission and content-type tables (Django's model backend)
    - ``"guardian"``: those plus Guardian's configured user/group object-permission models and, when ``model`` is
      given, its enabled direct-foreign-key grant models (found from metadata, without a content-type lookup)
    - ``"none"``: nothing; such a gate reads no authorization records
    """
    if provider == "none":
        return
    if isinstance(user, Model):
        require_default_database(user._state.db, context="the request actor")
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    tables = [get_user_model(), Group, Permission, ContentType]
    if provider == "guardian":
        tables.extend(_guardian_grant_models(model))
    for table in tables:
        require_default_database(router.db_for_read(table), context=f"authorization records {table._meta.label}")


def _guardian_grant_models(model: type[Model] | None) -> list[type[Model]]:
    from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
    from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

    grants = [get_user_obj_perms_model(), get_group_obj_perms_model()]
    if model is not None:
        for field in model._meta.get_fields():
            table = field.related_model if field.auto_created and (field.one_to_many or field.one_to_one) else None
            if (
                table is not None
                and issubclass(table, (UserObjectPermissionBase, GroupObjectPermissionBase))
                and getattr(table, "enabled", True)
                and not table.objects.is_generic()
            ):
                grants.append(table)
    return grants
