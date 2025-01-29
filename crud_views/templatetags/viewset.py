from django import template
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.view import ViewSetView
from crud_views.lib.views import DetailView

User = get_user_model()

register = template.Library()


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def vs_css(context):
    return {
        "css": crud_views_settings.css
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def vs_js(context):
    return {
        "js": crud_views_settings.javascript
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/csrftoken.html", takes_context=True)
def vs_csrf_token(context):
    return {}


def vs_get_view(context) -> ViewSetView:
    view: ViewSetView = context["view"]
    assert isinstance(view, ViewSetView), f"view {view} is not ViewSetAware"
    return view


def vs_get_context(context, key, obj=None) -> dict:
    view: ViewSetView = vs_get_view(context)
    context = view.vs_get_context(key, obj=obj, user=context["request"].user, request=context["request"])
    return context


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/const.js.html", takes_context=True)
def vs_const_js(context):
    request = context["request"]
    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def vs_list_action(context, key, obj=None):
    return vs_get_context(context=context, key=key, obj=obj)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def vs_list_action_form(context, key, obj=None):
    return vs_get_context(context=context, key=key, obj=obj)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def vs_context_action(context, key, obj=None):
    ctx = vs_get_context(context=context, key=key, obj=obj)
    template = ctx.get("vs_template", f"{crud_views_settings.theme_path}/tags/context_action.html")
    return render_to_string(template, context=ctx, request=context["request"])


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/context_actions.html", takes_context=True)
def vs_context_actions(context, obj=None):
    view: ViewSetView = vs_get_view(context)
    return {
        "view": view,
        "request": context["request"],
        "object": obj
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_cancel.html", takes_context=True)
def vs_cancel_button(context, obj=None):
    view: ViewSetView = vs_get_view(context)
    context = view.get_cancel_button_context(obj=obj, user=context["request"].user, request=context["request"])
    return context


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_submit.html", takes_context=True)
def vs_submit_button(context, obj=None):
    view: ViewSetView = vs_get_view(context)
    return {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_delete.html", takes_context=True)
def vs_delete_button(context, obj=None):
    view: ViewSetView = vs_get_view(context)
    return {}


@register.simple_tag(takes_context=True)
def vs_property_label(context, obj: object, property: str):
    view: ViewSetView = vs_get_view(context)
    assert isinstance(view, DetailView)
    return property.upper()


@register.simple_tag(takes_context=True)
def vs_property_value(context, obj: object, property: str):
    view: ViewSetView = vs_get_view(context)
    assert isinstance(view, DetailView)
    return view.vs_get_property(obj, property)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def vs_header_icon(context):
    view: ViewSetView = vs_get_view(context)
    icon = view.vs_get_header_icon()
    return {"icon": icon}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def vs_filter_icon(context):
    view: ViewSetView = vs_get_view(context)
    icon = view.vs_get_filter_icon()  # noqa
    return {"icon": icon}


@register.simple_tag(takes_context=True)
def vs_filter_header(context):
    view: ViewSetView = vs_get_view(context)
    return view.vs_filter_header  # noqa


@register.simple_tag(takes_context=True)
def vs_header(context):
    view: ViewSetView = vs_get_view(context)
    return view.vs_header


@register.simple_tag(takes_context=True)
def vs_paragraph(context):
    view: ViewSetView = vs_get_view(context)
    return view.vs_paragraph


@register.simple_tag(takes_context=True)
def vs_render_form(context):
    return render_to_string(f"{crud_views_settings.theme_path}/tags/form.html", context.flatten())


@register.simple_tag(takes_context=True)
def vs_render_filter(context):
    return render_to_string(f"{crud_views_settings.theme_path}/tags/list_filter.html", context.flatten())


@register.filter
def vs_is_false(arg):
    return arg is False


@register.filter
def vs_is_true(arg):
    return arg is True
