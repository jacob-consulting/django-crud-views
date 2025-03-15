from django import template
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.view import CrudView
from crud_views.lib.views import DetailView
from crud_views.lib.views.detail import Property

User = get_user_model()

register = template.Library()


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    return {
        "css": crud_views_settings.css
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    return {
        "js": crud_views_settings.javascript
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/csrftoken.html", takes_context=True)
def cv_csrf_token(context):
    return {}


def cv_get_view(context) -> CrudView:
    view: CrudView = context["view"]
    assert isinstance(view, CrudView), f"view {view} is not ViewSetAware"
    return view


def cv_get_context(context, key, obj=None) -> dict:
    view: CrudView = cv_get_view(context)
    context = view.cv_get_context(key, obj=obj, user=context["request"].user, request=context["request"])
    return context


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/const.js.html", takes_context=True)
def cv_const_js(context):
    request = context["request"]
    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def cv_list_action(context, key, obj=None):
    return cv_get_context(context=context, key=key, obj=obj)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_list_action_form(context, key, obj=None):
    return cv_get_context(context=context, key=key, obj=obj)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_action(context, key, obj=None):
    ctx = cv_get_context(context=context, key=key, obj=obj)
    template = ctx.get("cv_template", f"{crud_views_settings.theme_path}/tags/context_action.html")
    return render_to_string(template, context=ctx, request=context["request"])


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/context_actions.html", takes_context=True)
def cv_context_actions(context, obj=None):
    view: CrudView = cv_get_view(context)
    return {
        "view": view,
        "request": context["request"],
        "object": obj
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_cancel.html", takes_context=True)
def cv_cancel_button(context, obj=None):
    view: CrudView = cv_get_view(context)
    context = view.get_cancel_button_context(obj=obj, user=context["request"].user, request=context["request"])
    return context


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_submit.html", takes_context=True)
def cv_submit_button(context, obj=None):
    view: CrudView = cv_get_view(context)
    return {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_delete.html", takes_context=True)
def cv_delete_button(context, obj=None):
    view: CrudView = cv_get_view(context)
    return {}


@register.simple_tag(takes_context=True)
def cv_property_groups(context):
    view: CrudView = cv_get_view(context)
    context["groups"] = view.cv_property_groups_show
    return render_to_string("crud_views/properties/groups.html", context.flatten())


@register.simple_tag(takes_context=True)
def cv_property_group(context, group_or_key):
    view: CrudView = cv_get_view(context)
    group = view.cv_get_property_group(group_or_key=group_or_key)
    context["group"] = group
    return render_to_string("crud_views/properties/group.html", context.flatten())


@register.simple_tag(takes_context=True)
def cv_property_label(context, obj: object, prop: Property):
    view: CrudView = cv_get_view(context)
    assert isinstance(view, DetailView)
    info = view.cv_get_property_info(obj=obj, prop=prop)
    return info.label


@register.simple_tag(takes_context=True)
def cv_property_label_tooltip(context, obj: object, prop: Property):
    view: CrudView = cv_get_view(context)
    assert isinstance(view, DetailView)
    info = view.cv_get_property_info(obj=obj, prop=prop)
    return info.label_tooltip


@register.simple_tag(takes_context=True)
def cv_property_value(context, obj: object, prop: Property):
    view: CrudView = cv_get_view(context)
    assert isinstance(view, DetailView)
    info = view.cv_get_property_info(obj=obj, prop=prop)
    return info.render()


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def cv_header_icon(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_header_icon()
    return {"icon": icon}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def cv_filter_icon(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_filter_icon()  # noqa
    return {"icon": icon}


@register.simple_tag(takes_context=True)
def cv_filter_header(context):
    view: CrudView = cv_get_view(context)
    return view.cv_filter_header  # noqa


@register.simple_tag(takes_context=True)
def cv_header(context):
    view: CrudView = cv_get_view(context)
    return view.cv_header


@register.simple_tag(takes_context=True)
def cv_paragraph(context):
    view: CrudView = cv_get_view(context)
    return view.cv_paragraph


@register.simple_tag(takes_context=True)
def cv_render_form(context):
    return render_to_string(f"{crud_views_settings.theme_path}/tags/form.html", context.flatten())


@register.simple_tag(takes_context=True)
def cv_render_filter(context):
    return render_to_string(f"{crud_views_settings.theme_path}/tags/list_filter.html", context.flatten())


@register.filter
def cv_is_false(arg):
    return arg is False


@register.filter
def cv_is_true(arg):
    return arg is True
