from functools import wraps


def vs_property(foo, type=str, label:str|None = None):
    """
    Experimental property decorator for ViewSetView
    """

    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.vs_property = True
        wrapper.vs_type = type
        wrapper.vs_label = label

        return wrapper

    return actual_decorator
