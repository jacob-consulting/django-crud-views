from django import template

register = template.Library()


@register.inclusion_tag(takes_context=True, filename="crud_views/formsets/formset.html")
def cv_x_formset(context, x_formset):
    data = {"x_formset": x_formset}
    return data
