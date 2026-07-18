from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.urls import NoReverseMatch, reverse

from crud_views_object_detail.lib.config import BadgeConfig, LinkConfig, PropertyConfig, PropertyGroupConfig

_MISSING = object()

FIELD_TYPE_MAP: dict[type[models.Field], str] = {
    models.CharField: "char",
    models.SlugField: "char",
    models.URLField: "char",
    models.EmailField: "char",
    models.TextField: "text",
    models.BooleanField: "boolean",
    models.NullBooleanField: "boolean",
    models.DateTimeField: "datetime",
    models.DateField: "date",
    models.IntegerField: "integer",
    models.SmallIntegerField: "integer",
    models.BigIntegerField: "integer",
    models.PositiveIntegerField: "integer",
    models.PositiveSmallIntegerField: "integer",
    models.PositiveBigIntegerField: "integer",
    models.AutoField: "integer",
    models.BigAutoField: "integer",
    models.SmallAutoField: "integer",
    models.FloatField: "float",
    models.DecimalField: "float",
    models.ForeignKey: "foreignkey",
    models.OneToOneField: "foreignkey",
    models.ManyToManyField: "manytomany",
    models.ManyToManyRel: "manytomany",
    models.OneToOneRel: "foreignkey",
    models.ManyToOneRel: "manytomany",
}


@dataclass
class ResolvedProperty:
    path: str
    label: str
    value: Any
    detail: str | None = None
    type: str = "default"
    template: str | None = None
    is_many: bool = False
    link_url: str | None = None
    badge_css: str | None = None
    badge_label: str | None = None


@dataclass
class ResolvedGroup:
    title: str
    description: str | None = None
    icon: str | None = None
    properties: list[ResolvedProperty] = field(default_factory=list)


def _get_field_type(field_obj: models.Field) -> str:
    """Map a Django field instance to a type string."""
    for field_class, type_name in FIELD_TYPE_MAP.items():
        if isinstance(field_obj, field_class):
            return type_name
    return "default"


def _resolve_link_url(value: Any, link: LinkConfig | None, is_many: bool) -> str | None:
    """Resolve a link URL for the property value."""
    if link is None or value is None or is_many:
        return None

    try:
        if link.args is not None:
            args = [getattr(value, attr) for attr in link.args]
            return reverse(link.url, args=args)
        elif link.kwargs is not None:
            kwargs = {k: getattr(value, attr) for k, attr in link.kwargs.items()}
            return reverse(link.url, kwargs=kwargs)
        elif isinstance(value, models.Model):
            return reverse(link.url, kwargs={"pk": value.pk})
        else:
            return None
    except (NoReverseMatch, AttributeError):
        return None


def _resolve_badge_css(value: Any, badge: BadgeConfig) -> str | None:
    """Compute Bootstrap badge CSS classes from config and value."""
    if value is None:
        return None
    color = None
    if badge.color_fn:
        color = badge.color_fn(value)
    elif badge.color_map:
        color = badge.color_map.get(value)
    else:
        color = badge.color
    if color is None:
        return None
    css = f"text-bg-{color}"
    if badge.pill:
        css += " rounded-pill"
    return css


def _resolve_badge_label(value: Any, badge: BadgeConfig) -> str | None:
    """Compute badge display label from config and value."""
    if value is None or badge.label_map is None:
        return None
    return badge.label_map.get(value)


def resolve_property(instance: models.Model, config: PropertyConfig, view=None) -> ResolvedProperty:
    """Resolve a PropertyConfig against a model instance.

    Walks the _meta chain for metadata (label, detail, type)
    and the instance chain for the runtime value.
    """
    segments = config.path.split("__")

    # Walk _meta to gather field metadata
    label = config.path
    detail = None
    field_type = "default"
    is_many = False
    current_model = type(instance)

    for i, segment in enumerate(segments):
        try:
            field_obj = current_model._meta.get_field(segment)
        except FieldDoesNotExist:
            # Could be a method/property — no further metadata to extract
            label = segment.replace("_", " ").title()
            break
        else:
            # Extract metadata from the field
            verbose = getattr(field_obj, "verbose_name", None)
            if verbose:
                v = str(verbose)
                label = v[0].upper() + v[1:]
            else:
                label = segment.replace("_", " ").title()

            help_text = getattr(field_obj, "help_text", None)
            if help_text:
                detail = str(help_text)

            field_type = _get_field_type(field_obj)

            # Navigate into related models for FK/O2O
            # OneToOneRel must be checked before ManyToOneRel (it's a subclass)
            if isinstance(field_obj, (models.ForeignKey, models.OneToOneField, models.OneToOneRel)):
                current_model = field_obj.related_model
            elif isinstance(field_obj, models.ManyToManyField):
                is_many = True
                current_model = field_obj.related_model
            elif isinstance(field_obj, (models.ManyToManyRel, models.ManyToOneRel)):
                is_many = True
                current_model = field_obj.related_model

    # Apply config overrides
    if config.title:
        label = config.title
    if config.detail is not None:
        detail = config.detail
    if config.type:
        field_type = config.type

    # Resolve the runtime value
    value = _resolve_value(instance, segments, is_many)

    if value is _MISSING:
        view_method = getattr(view, config.path, None) if view is not None else None
        value = view_method(instance) if callable(view_method) else None

    # Resolve link URL
    link_url = _resolve_link_url(value, config.link, is_many)

    # Resolve badge
    badge_css = None
    badge_label = None
    if config.badge:
        badge_css = _resolve_badge_css(value, config.badge)
        badge_label = _resolve_badge_label(value, config.badge)

    return ResolvedProperty(
        path=config.path,
        label=label,
        value=value,
        detail=detail or None,
        type=field_type,
        template=config.template,
        is_many=is_many,
        link_url=link_url,
        badge_css=badge_css,
        badge_label=badge_label,
    )


def _resolve_value(instance: models.Model, segments: list[str], is_many: bool) -> Any:
    """Walk the instance to resolve the runtime value.

    Tracks a list of current objects to handle M2M fan-out.
    Returns _MISSING if the first segment is not found on the instance.
    """
    current: list[Any] = [instance]
    first_resolved = False

    for i, segment in enumerate(segments):
        next_objects: list[Any] = []
        for obj in current:
            if obj is None:
                next_objects.append(None)
                continue

            attr = getattr(obj, segment, _MISSING)

            if attr is _MISSING:
                continue

            if i == 0:
                first_resolved = True

            # Check if it's a manager (M2M or reverse FK)
            if hasattr(attr, "all"):
                next_objects.extend(attr.all())
            elif callable(attr):
                next_objects.append(attr())
            else:
                next_objects.append(attr)

        current = next_objects

    if not first_resolved:
        return _MISSING

    if is_many:
        return current
    elif len(current) == 1:
        return current[0]
    else:
        return current


def resolve_group(instance: models.Model, config: PropertyGroupConfig, view=None) -> ResolvedGroup:
    """Resolve all properties in a group."""
    return ResolvedGroup(
        title=config.title,
        description=config.description,
        icon=config.icon,
        properties=[resolve_property(instance, prop, view=view) for prop in config.properties],
    )


def resolve_all(instance: models.Model, groups: list[PropertyGroupConfig], view=None) -> list[ResolvedGroup]:
    """Resolve all groups for an instance."""
    return [resolve_group(instance, group, view=view) for group in groups]
