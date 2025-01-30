from functools import wraps


def cv_property(foo, type=str, label:str|None = None):
    """
    Experimental property decorator for ViewSetView
    """

    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.cv_property = True
        wrapper.cv_type = type
        wrapper.cv_label = label

        return wrapper

    return actual_decorator
