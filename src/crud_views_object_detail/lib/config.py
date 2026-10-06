from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from crud_views.lib.lazy import LazyStr


class LinkConfig(BaseModel):
    """Configuration for linking a property value to a URL."""

    url: str
    args: list[str] | None = None
    kwargs: dict[str, str] | None = None


class BadgeConfig(BaseModel):
    """Configuration for rendering a property value as a Bootstrap badge."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    color: str | None = None
    color_map: dict | None = None
    color_fn: Any | None = None
    label_map: dict | None = None
    pill: bool = False


class PropertyConfig(BaseModel):
    """Configuration for a single property to display."""

    path: str
    title: LazyStr | None = None
    detail: LazyStr | None = None
    type: str | None = None
    template: str | None = None
    link: LinkConfig | None = None
    badge: BadgeConfig | None = None

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
    description: LazyStr | None = None
    icon: str | None = None
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
