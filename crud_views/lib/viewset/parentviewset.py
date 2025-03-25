import re
from typing import Any

from pydantic import BaseModel, field_validator

REG_PK_NAME = re.compile(r"[a-z_]+_pk")
REG_ATTRIBUTE = re.compile(r"[a-z][a-z_]*")


class ParentViewSet(BaseModel):
    name: str  # the name of the parent ViewSet
    attribute: str | None = None  # the model attribute with the ForeignKey to the parent model
    pk_name: str | None = None  # the name of the primary key in the url pattern with _pk suffix, defaults to parent ViewSet name plus "_pk"
    many_to_many_through_attribute: str | None = None  # the name of the parent's manay to many attribute that points to the child

    @field_validator("attribute", mode="plain")  # noqa
    @classmethod
    def validate_attribute(cls, value: Any) -> Any:
        """
        attribute must be lowercase alpha with underscores
        """
        if value is None:
            return value
        if not REG_ATTRIBUTE.match(value):
            raise ValueError(f"attribute must be lowercase alpha with underscores at {cls}")
        return value

    @field_validator("pk_name", mode="plain")  # noqa
    @classmethod
    def validate_pk_name(cls, value: Any) -> Any:
        """
        pk_name must be lowercase alpha with underscores ending with _p
        """
        if value is None:
            return value
        if not REG_PK_NAME.match(value):
            raise ValueError(f"pk_name must be lowercase alpha with underscores ending with _pk at {cls}")
        return value

    @property
    def viewset(self) -> 'ViewSet':
        """
        Get parent ViewSet from registry
        """
        from crud_views.lib.viewset import ViewSet

        return ViewSet.get_viewset(self.name)

    def get_pk_name(self) -> str:
        """
        The make of the parent's primary key in the url pattern
        """
        return self.pk_name if self.pk_name else f"{self.viewset.name}_pk"

    def get_attribute(self) -> str:
        """
        The model attribute with the ForeignKey to the parent model, defaults to the parent's ViewSet name
        """
        return self.attribute if self.attribute else self.viewset.name
