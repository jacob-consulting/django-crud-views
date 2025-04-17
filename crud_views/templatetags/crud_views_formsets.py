from django import template
from django.contrib.auth import get_user_model

User = get_user_model()

register = template.Library()


@register.inclusion_tag(takes_context=True, filename="crud_views/formsets/formset.html")
def cv_x_formset(context, x_formset):
    data = {
        "x_formset": x_formset
    }
    return data
