from functools import wraps
from typing import Type


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


STRICT = False

def ignore_exception(exception_type, default_value=None, default_empty_dict:bool = False):
    """
    Ignore exception and return default value if strict is False
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                # todo: get strict from settings
                if STRICT:
                    raise e
                if default_empty_dict:
                    return dict()
                return default_value

        return wrapper

    return decorator