from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.functional import Promise

from crud_views_object_detail.lib import conf
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
    badge_color: str | None = None
    badge_pill: bool = False
    choice_label: Any | None = None


@dataclass(frozen=True)
class _ResolvedBadge:
    color: str
    pill: bool
    css: str


@dataclass
class ResolvedGroup:
    title: str
    description: str | None = None
    icon: str | None = None
    properties: list[ResolvedProperty] = field(default_factory=list)
    id: str | None = None


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


def _resolve_badge(value: Any, badge: BadgeConfig) -> _ResolvedBadge | None:
    """Resolve semantic fields and compatible Bootstrap CSS from one color evaluation."""
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
    return _ResolvedBadge(color=color, pill=badge.pill, css=css)


def _resolve_badge_label(value: Any, badge: BadgeConfig) -> str | None:
    """Compute badge display label from config and value."""
    if value is None or badge.label_map is None:
        return None
    return badge.label_map.get(value)


def _field_label(field_obj, segment: str) -> str:
    verbose = getattr(field_obj, "verbose_name", None)
    if verbose:
        v = str(verbose)
        return v[0].upper() + v[1:]
    return segment.replace("_", " ").title()


def _resolve_field_meta(model, segments: list[str], path: str):
    """Walk metadata, retaining a terminal field only for fully model-backed paths."""
    label = path
    field_type = "default"
    is_many = False
    current_model = model
    terminal_field = None
    model_path = True

    for index, segment in enumerate(segments):
        try:
            field_obj = current_model._meta.get_field(segment)
        except FieldDoesNotExist:
            # Could be a method/property — no further metadata to extract
            label = segment.replace("_", " ").title()
            terminal_field = None
            break

        terminal_field = field_obj if model_path else None
        label = _field_label(field_obj, segment)
        field_type = _get_field_type(field_obj)

        # Navigate into related models for FK/O2O
        # OneToOneRel must be checked before ManyToOneRel (it's a subclass)
        if isinstance(field_obj, (models.ForeignKey, models.OneToOneField, models.OneToOneRel)):
            current_model = field_obj.related_model
        elif isinstance(field_obj, (models.ManyToManyField, models.ManyToManyRel, models.ManyToOneRel)):
            is_many = True
            current_model = field_obj.related_model
        elif index < len(segments) - 1:
            model_path = False

    return label, getattr(terminal_field, "help_text", None), field_type, is_many, terminal_field


def _resolve_detail(config: PropertyConfig, help_text, view):
    """Select text once without evaluating lazy descriptions or mutating configuration."""
    detail = config.detail
    if isinstance(detail, Promise):
        return detail
    if isinstance(detail, str):
        return detail if detail != "" else None
    policy = detail
    if policy is None:
        policy = getattr(view, "cv_object_detail_show_help_text", None)
    if policy is None:
        policy = conf.crud_views_object_detail_settings.show_help_text
    if policy is not True:
        return None
    if isinstance(help_text, Promise):
        return help_text
    return help_text if help_text != "" else None


def resolve_property(instance: models.Model, config: PropertyConfig, view=None) -> ResolvedProperty:
    """Resolve a PropertyConfig against a model instance.

    Walks the _meta chain for metadata (label, detail, type)
    and the instance chain for the runtime value.
    """
    segments = config.path.split("__")

    # Walk _meta to gather field metadata
    label, help_text, field_type, is_many, terminal_field = _resolve_field_meta(type(instance), segments, config.path)
    detail = _resolve_detail(config, help_text, view)

    # Apply config overrides
    if config.title:
        label = config.title
    if config.type:
        field_type = config.type

    # Resolve the runtime value
    value, owner = _resolve_value_and_owner(instance, segments, is_many)

    used_view_fallback = False
    if value is _MISSING:
        view_method = getattr(view, config.path, None) if view is not None else None
        used_view_fallback = callable(view_method)
        value = view_method(instance) if used_view_fallback else None

    choice_label = None
    if (
        not is_many
        and not used_view_fallback
        and not getattr(terminal_field, "is_relation", False)
        and getattr(terminal_field, "choices", None)
    ):
        if owner is None:
            # Missing scalar relations stay empty even when their raw walk returns [].
            choice_label = ""
        elif config.choices_display:
            choice_label = getattr(owner, f"get_{terminal_field.name}_display")()

    # Resolve link URL
    link_url = _resolve_link_url(value, config.link, is_many)

    # Resolve badge
    badge = _resolve_badge(value, config.badge) if config.badge else None
    badge_label = _resolve_badge_label(value, config.badge) if config.badge else None

    return ResolvedProperty(
        path=config.path,
        label=label,
        value=value,
        detail=detail,
        type=field_type,
        template=config.template,
        is_many=is_many,
        link_url=link_url,
        badge_css=badge.css if badge else None,
        badge_label=badge_label,
        badge_color=badge.color if badge else None,
        badge_pill=badge.pill if badge else False,
        choice_label=choice_label,
    )


def _resolve_value(instance: models.Model, segments: list[str], is_many: bool) -> Any:
    """Resolve only the runtime value, preserving missing and collection results."""
    return _resolve_value_and_owner(instance, segments, is_many)[0]


def _resolve_value_and_owner(instance: models.Model, segments: list[str], is_many: bool) -> tuple[Any, Any]:
    """Walk the instance to resolve the runtime value.

    Tracks a list of current objects to handle M2M fan-out.
    Returns _MISSING if the first segment is not found on the instance.
    """
    if not segments:
        return _MISSING, None
    first = getattr(instance, segments[0], _MISSING) if instance is not None else _MISSING
    if first is _MISSING:
        return _MISSING, None

    owner = instance
    current = _expand(first)
    for segment in segments[1:]:
        owner = current[0] if not is_many and len(current) == 1 else None
        current = [value for obj in current for value in _step(obj, segment)]

    if not is_many and len(current) == 1:
        return current[0], owner
    return current, owner


def _expand(attr: Any) -> list[Any]:
    # Check if it's a manager (M2M or reverse FK)
    if hasattr(attr, "all"):
        return list(attr.all())
    if callable(attr):
        return [attr()]
    return [attr]


def _step(obj: Any, segment: str) -> list[Any]:
    """Values reached from ``obj`` via ``segment``; None propagates, a missing attribute drops out."""
    if obj is None:
        return [None]
    attr = getattr(obj, segment, _MISSING)
    return [] if attr is _MISSING else _expand(attr)


def resolve_group(instance: models.Model, config: PropertyGroupConfig, view=None) -> ResolvedGroup:
    """Resolve all properties in a group."""
    return ResolvedGroup(
        title=config.title,
        description=config.description,
        icon=config.icon,
        properties=[resolve_property(instance, prop, view=view) for prop in config.properties],
        id=config.id,
    )


def resolve_all(instance: models.Model, groups: list[PropertyGroupConfig], view=None) -> list[ResolvedGroup]:
    """Resolve all groups for an instance."""
    return [resolve_group(instance, group, view=view) for group in groups]
