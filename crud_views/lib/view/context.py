from typing import Dict, Any

from django.db.models import Model
from pydantic import BaseModel, field_validator


class ViewContext(BaseModel, arbitrary_types_allowed=True):
    """
    A container that is passed to methods of CrudView with the context:
        - views
        - object
    """
    view: 'CrudView'
    object: Model | None = None

    @field_validator('object', mode='before')
    @classmethod
    def validate_object(cls, value: Any) -> Any:
        """
        When passed from template, an empty string is passed as object
        """
        if value == "":
            return None
        else:
            return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.object
        }

    @property
    def router_name(self) -> str:
        return self.view.request.resolver_match.url_name
