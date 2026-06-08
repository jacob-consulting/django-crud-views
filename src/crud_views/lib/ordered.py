"""Lazy access to the optional django-ordered-model dependency.

`django-ordered-model` is an optional extra (`crud_views[ordered]`). Core code
must never import it at module top level, or the extra stops being optional.
Use this helper to resolve the class on demand.
"""

from __future__ import annotations

from typing import Type


def get_ordered_model() -> Type | None:
    """Return the ``OrderedModel`` class, or ``None`` if the package is absent.

    Setting ``sys.modules['ordered_model'] = None`` (as tests do to simulate a
    missing install) makes the import raise ``ImportError``, which we treat the
    same as the package not being installed.
    """
    try:
        from ordered_model.models import OrderedModel
    except ImportError:
        return None
    return OrderedModel
