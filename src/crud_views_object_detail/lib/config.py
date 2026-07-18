from __future__ import annotations

from typing import Annotated, Any, Optional

from django.utils.functional import Promise
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.functional_validators import PlainValidator


def _validate_lazy_str(v: Any) -> str | Promise:
    """Accept plain strings and Django lazy translation strings without coercion."""
    if isinstance(v, (str, Promise)):
        return v
    raise ValueError(f"Expected str or lazy string, got {type(v)}")


LazyStr = Annotated[str, PlainValidator(_validate_lazy_str)]


class LinkConfig(BaseModel):
    """Configuration for linking a property value to a URL."""

    url: str
    args: Optional[list[str]] = None
    kwargs: Optional[dict[str, str]] = None


class BadgeConfig(BaseModel):
    """Configuration for rendering a property value as a Bootstrap badge."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    color: Optional[str] = None
    color_map: Optional[dict] = None
    color_fn: Optional[Any] = None
    label_map: Optional[dict] = None
    pill: bool = False


class PropertyConfig(BaseModel):
    """Configuration for a single property to display."""

    path: str
    title: Optional[LazyStr] = None
    detail: Optional[LazyStr] = None
    type: Optional[str] = None
    template: Optional[str] = None
    link: Optional[LinkConfig] = None
    badge: Optional[BadgeConfig] = None

    @field_validator("link", mode="before")
    @classmethod
    def normalize_link(cls, v):
        if isinstance(v, str):
            return LinkConfig(url=v)
        return v

    @field_validator("badge", mode="before")
    @classmethod
    def normalize_badge(cls, v):
        if isinstance(v, str):
            return BadgeConfig(color=v)
        return v


class PropertyGroupConfig(BaseModel):
    """Configuration for a group of properties."""

    title: LazyStr
    description: Optional[LazyStr] = None
    icon: Optional[str] = None
    properties: list[PropertyConfig]

    @field_validator("properties", mode="before")
    @classmethod
    def normalize_properties(cls, v: list) -> list:
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PropertyConfig(path=item))
            elif isinstance(item, PropertyConfig):
                result.append(item)
            elif isinstance(item, dict):
                result.append(PropertyConfig(**item))
            else:
                raise ValueError(f"Invalid property config: {item!r}")
        return result


def x(path: str, **kwargs) -> PropertyConfig:
    """Convenience constructor for PropertyConfig."""
    return PropertyConfig(path=path, **kwargs)


def parse_property_display(raw: list[dict]) -> list[PropertyGroupConfig]:
    """Parse a raw property_display list into PropertyGroupConfig objects."""
    return [PropertyGroupConfig(**group) for group in raw]
