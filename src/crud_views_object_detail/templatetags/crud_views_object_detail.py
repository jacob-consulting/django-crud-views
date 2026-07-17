from django import template
from django.template.loader import select_template
from django.utils.safestring import mark_safe

from crud_views_object_detail.lib.conf import (
    build_icon_class,
    build_named_icon_class,
    crud_views_object_detail_settings,
)
from crud_views_object_detail.lib.config import parse_property_display
from crud_views_object_detail.lib.resolvers import resolve_all

register = template.Library()


@register.simple_tag(takes_context=True)
def render_object_detail(context, obj, groups=None, property_display=None):
    """Render all property groups for an object.

    ``groups`` can be pre-resolved ``ResolvedGroup`` instances (from the mixin)
    or a raw ``property_display`` list that will be parsed and resolved here.
    """
    if groups is None and property_display is not None:
        configs = parse_property_display(property_display)
        view = context.get("view")
        groups = resolve_all(obj, configs, view=view)

    pack = crud_views_object_detail_settings.template_pack_layout
    tpl = select_template(
        [
            f"crud_views_object_detail/layouts/{pack}/object_detail.html",
            "crud_views_object_detail/object_detail.html",
        ]
    )
    return mark_safe(tpl.render({"groups": groups or []}, context.get("request")))


@register.simple_tag(takes_context=True)
def render_group(context, group):
    """Render a single property group using the configured layout pack."""
    pack = crud_views_object_detail_settings.template_pack_layout
    tpl = select_template(
        [
            f"crud_views_object_detail/layouts/{pack}/group.html",
        ]
    )
    return mark_safe(tpl.render({"group": group}, context.get("request")))


@register.simple_tag(takes_context=True)
def render_property(context, prop):
    """Render a single property row using the configured layout pack."""
    pack = crud_views_object_detail_settings.template_pack_layout
    tpl = select_template(
        [
            f"crud_views_object_detail/layouts/{pack}/property.html",
        ]
    )
    return mark_safe(tpl.render({"prop": prop}, context.get("request")))


@register.simple_tag(takes_context=True)
def render_property_value(context, prop):
    """Render the value of a property using its type-specific template.

    Returns the rendered HTML string.
    """
    types_pack = crud_views_object_detail_settings.template_pack_types
    if prop.badge_css:
        template_names = [
            f"crud_views_object_detail/types/{types_pack}/badge.html",
            "crud_views_object_detail/types/default/badge.html",
        ]
    elif prop.template:
        template_names = [prop.template]
    else:
        template_names = [
            f"crud_views_object_detail/types/{types_pack}/{prop.type}.html",
            f"crud_views_object_detail/types/{types_pack}/default.html",
            "crud_views_object_detail/types/default/default.html",
        ]

    tpl = select_template(template_names)
    od_settings = {
        "property_text_newline": crud_views_object_detail_settings.property_text_newline,
    }
    return tpl.render({"prop": prop, "value": prop.value, "od_settings": od_settings}, context.get("request"))


@register.filter
def icon_class(icon_name):
    """Return the full CSS class string for an icon name."""
    return build_icon_class(icon_name)


@register.filter
def named_icon_class(name):
    """Return the full CSS class string for a named icon."""
    return build_named_icon_class(name)
