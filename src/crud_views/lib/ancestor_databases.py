"""Database boundary of nested ViewSet requests.

Ancestor traversal, nested child data and their authorization records support only the ``default`` database. A
reached operation that selects another alias (a queryset's ``.using()`` or a database router) is a configuration
error: the selection is reported, never stripped, rerouted or retried on ``default``. Top-level requests never call
this guard, so their existing database behavior is unchanged.
"""

from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS


def require_default_database(alias: str, *, context: str) -> None:
    """Raise ``ImproperlyConfigured`` unless ``alias`` is the default database; ``context`` names the operation."""
    if alias != DEFAULT_DB_ALIAS:
        raise ImproperlyConfigured(
            f"{context} uses database {alias!r}: nested ViewSets support only the {DEFAULT_DB_ALIAS!r} database "
            f"for their ancestors, their data and its authorization"
        )
