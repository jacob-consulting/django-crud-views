from django import template
from django.contrib.auth import get_user_model
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.view import CrudView

User = get_user_model()

register = template.Library()


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    return {"css": crud_views_settings.css}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    return {"js": crud_views_settings.javascript}


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


def _cv_config_context(context):
    request = context["request"]
    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/cv_config.html", takes_context=True)
def cv_const_js(context):
    return _cv_config_context(context)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/cv_config.html", takes_context=True)
def cv_config(context):
    return _cv_config_context(context)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def cv_list_action(context, key, obj=None):
    return cv_get_context(context=context, key=key, obj=obj)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_list_action_form(context, key, obj=None):
    return cv_get_context(context=context, key=key, obj=obj)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_action(context, key, obj=None):
    obj = None if not obj else obj  # fix empty string from template
    ctx = cv_get_context(context=context, key=key, obj=obj)
    template = ctx.get("cv_template", f"{crud_views_settings.theme_path}/tags/context_action.html")
    return render_to_string(template, context=ctx, request=context["request"])


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/context_actions.html", takes_context=True)
def cv_context_actions(context, obj=None):
    view: CrudView = cv_get_view(context)
    return {"view": view, "request": context["request"], "object": obj}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_cancel.html", takes_context=True)
def cv_cancel_button(context, obj=None):
    view: CrudView = cv_get_view(context)
    context = view.get_cancel_button_context(obj=obj, user=context["request"].user, request=context["request"])
    return context


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_submit.html", takes_context=True)
def cv_submit_button(context, obj=None):
    cv_get_view(context)
    return {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/button_delete.html", takes_context=True)
def cv_delete_button(context, obj=None):
    cv_get_view(context)
    return {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def cv_header_icon(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_header_icon()
    return {"icon": icon}


@register.simple_tag(takes_context=True)
def cv_header_icon_class(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_header_icon()
    return icon


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/icon.html", takes_context=True)
def cv_filter_icon(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_filter_icon()  # noqa
    return {"icon": icon}


@register.simple_tag(takes_context=True)
def cv_filter_icon_class(context):
    view: CrudView = cv_get_view(context)
    icon = view.cv_get_filter_icon()  # noqa
    return icon


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


@register.filter
def cv_is_list(arg):
    return isinstance(arg, (list, tuple))


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_card_action(context, action, obj=None):
    view = cv_get_view(context)

    if action.child_name:
        url = view.cv_get_child_url(action.child_name, action.child_key, obj)
        child_viewset = view.cv_viewset.get_viewset(action.child_name)
        child_cls = child_viewset.get_view_class(action.child_key)
        return {
            "cv_access": True,
            "cv_url": url,
            "cv_label": action.label,
            "cv_icon_action": child_cls.cv_icon_action,
            "cv_variant": action.variant,
            "cv_flex": action.flex,
            "cv_no_label": action.no_label,
        }

    user = context["request"].user
    cls = view.cv_viewset.get_view_class(action.key)
    access = cls.cv_has_access(user, obj)

    if not access:
        return {"cv_access": False}

    url = view.cv_get_url(action.key, obj=obj)

    if action.label:
        label = action.label
    else:
        view_context = view.cv_get_view_context(object=obj)
        label = cls.cv_get_action_short_label(context=view_context)

    return {
        "cv_access": True,
        "cv_url": url,
        "cv_label": label,
        "cv_icon_action": cls.cv_icon_action,
        "cv_variant": action.variant,
        "cv_flex": action.flex,
        "cv_no_label": action.no_label,
    }


@register.simple_tag(takes_context=True)
def cv_user_in_group(context, group):
    if group is None:
        return False
    user = context["request"].user
    if not user.is_authenticated:
        return False
    return group.user_set.filter(pk=user.pk).exists()


@register.simple_tag(takes_context=True)
def cv_card(context, obj):
    view = cv_get_view(context)
    template_name = getattr(view, "cv_card_template", "crud_views/tags/card.html")
    t = get_template(template_name)
    card_context = {"object": obj, "view": view, "request": context["request"]}
    return mark_safe(t.render(card_context))
