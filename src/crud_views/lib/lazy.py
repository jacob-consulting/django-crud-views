from typing import Annotated, Any

from django.utils.functional import Promise
from pydantic.functional_validators import PlainValidator


def _validate_lazy_str(v: Any) -> str | Promise:
    """Accept plain strings and Django lazy translation strings without coercion."""
    if isinstance(v, (str, Promise)):
        return v
    raise ValueError(f"Expected str or lazy string, got {type(v)}")


#: A pydantic field type for user-facing labels. Keeps ``gettext_lazy`` values lazy, so labels
#: defined at class level are translated per request rather than frozen at import time.
LazyStr = Annotated[str, PlainValidator(_validate_lazy_str)]
