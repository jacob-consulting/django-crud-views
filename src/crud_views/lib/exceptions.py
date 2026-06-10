import logging
from functools import wraps
from typing import Type

logger = logging.getLogger(__name__)


class ViewSetNotFoundError(Exception):
    pass


class ViewSetKeyFoundError(Exception):
    pass


class ViewSetError(Exception):
    pass


class CrudViewError(Exception):
    pass


class ParentViewSetError(Exception):
    pass


def cv_raise(expression: bool, msg: str, exception: Type[Exception] = ViewSetError):
    if not expression:
        raise exception(msg)


def ignore_exception(exception_type, default_value=None, default_empty_dict: bool = False):
    """
    Ignore exception and return a default value.
    In strict mode (setting CRUD_VIEWS_STRICT, defaults to DEBUG) the exception
    is raised instead, so misconfigurations fail loudly during development.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type:
                from django.conf import settings

                if getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG):
                    raise
                logger.warning("ignoring exception in %s", func.__qualname__, exc_info=True)
                if default_empty_dict:
                    return dict()
                return default_value

        return wrapper

    return decorator
