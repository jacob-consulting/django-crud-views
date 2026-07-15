from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from crud_views.lib.view.base import CrudView

from pydantic import BaseModel, field_validator


class ViewContext(BaseModel, arbitrary_types_allowed=True):
    """
    A container that is passed to methods of CrudView with the context:
        - views
        - object
    """

    view: "CrudView"
    # typed Any (not Model | Resource) to avoid a module-level import of
    # crud_views.lib.resource here: resource.py imports
    # crud_views.lib.viewset.path_regs, which forces crud_views.lib.viewset's
    # __init__ to run, which itself imports crud_views.lib.resource — whichever
    # of {this module, viewset/__init__} runs first wins and the other sees a
    # partially-initialized module. Deferring the isinstance check below to
    # call-time (well after all modules have finished importing) sidesteps the
    # cycle entirely; see validate_object.
    object: Any = None

    @field_validator("object", mode="before")
    @classmethod
    def validate_object(cls, value: Any) -> Any:
        """
        When passed from template, an empty string is passed as object.
        """
        if value == "":
            return None
        if value is not None:
            from django.db.models import Model

            from crud_views.lib.resource import Resource

            if not isinstance(value, (Model, Resource)):
                raise ValueError(f"ViewContext.object must be a Model or Resource instance, got {type(value)!r}")
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {"object": self.object}

    @property
    def router_name(self) -> str:
        return self.view.request.resolver_match.url_name
