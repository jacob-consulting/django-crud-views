from django import template

register = template.Library()


@register.simple_tag
def get_features():
    from project.features import FEATURES

    return FEATURES
