from functools import wraps
from typing import Callable


def cv_property(type=str,
                label: str | None = None,
                label_tooltip: str | None = None,
                renderer: Callable | None = None):
    """
    Experimental property decorator for CrudView
    """

    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.cv_property = True
        wrapper.cv_type = type
        wrapper.cv_label = label
        wrapper.cv_label_tooltip = label_tooltip
        wrapper.cv_renderer = renderer

        return wrapper

    return actual_decorator
