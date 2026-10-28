from django import template

register = template.Library()


@register.inclusion_tag(takes_context=True, filename="crud_views/formsets/formset.html")
def cv_x_formset(context, x_formset):
    # deferred: this tag library must import before the app registry is ready
    from crud_views.lib.crispy.buttons import _CV_PAGE_OWNER, _cv_page_tier

    # the inclusion renders in context.new(): only the page owner of the rows' form buttons crosses it (the value
    # transported from Formsets or a parent formset, else the page tier of a live page context)
    return {"x_formset": x_formset, _CV_PAGE_OWNER: _cv_page_tier(context)}
