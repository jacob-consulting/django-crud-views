from django import template
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe
from django_tables2.templatetags import django_tables2 as _dt2

from crud_views.lib import assets
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.view import CrudView

register = template.Library()

# django-tables2 3.0.0 renamed the ``querystring`` tag to ``querystring_replace`` (to avoid shadowing
# Django 5.1's built-in tag). Resolve whichever the installed version provides; both share the same
# ``(parser, token)`` signature and pop/ignore their own tag name.
_querystring_impl = getattr(_dt2, "querystring_replace", None) or _dt2.querystring


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = list(crud_views_settings.css.values())
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.css)
    return {"css": [{"url": assets.resolve_url(entry)} for entry in entries]}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = list(crud_views_settings.javascript().values())
    for bundle in assets.get_registered(only_emitting=True):
        entries.extend(bundle.js)
    return {"js": [{"url": assets.resolve_url(entry)} for entry in entries]}


def cv_get_view(context) -> CrudView:
    view: CrudView = context["view"]
    assert isinstance(view, CrudView), f"view {view} is not ViewSetAware"
    return view


def cv_get_context(context, key, obj=None) -> dict:
    view: CrudView = cv_get_view(context)
    context = view.cv_get_context(key, obj=obj, user=context["request"].user, request=context["request"])
    return context


def _render_context_button(view, ctx) -> str:
    if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
        return ""
    if ctx.get("cv_template_code"):
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return view.render_snippet(ctx, template=template)


def _cv_config_context(context):
    request = context["request"]
    from django.middleware.csrf import get_token

    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
        "csrf_token": get_token(request),
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
    if not ctx:
        return ""
    if ctx.get("cv_template_code"):
        view = cv_get_view(context)
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return render_to_string(template, context=ctx, request=context["request"])


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_button(context, key, obj=None):
    obj = None if not obj else obj  # fix empty string from template
    view = cv_get_view(context)
    if obj is None:
        obj = getattr(view, "object", None)
    ctx = cv_get_context(context=context, key=key, obj=obj)
    return _render_context_button(view, ctx)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value=None)
def cv_context_url(context, key, obj=None):
    obj = None if not obj else obj  # fix empty string from template
    view = cv_get_view(context)
    if obj is None:
        obj = getattr(view, "object", None)
    ctx = cv_get_context(context=context, key=key, obj=obj)
    if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
        return None
    return ctx.get("cv_url")


@register.simple_tag(takes_context=True)
def cv_render_context_button(context, ctx) -> str:
    view = cv_get_view(context)
    return _render_context_button(view, ctx)


@register.tag(name="cv_querystring")
def cv_querystring(parser, token):
    """Version-agnostic django-tables2 querystring tag.

    Delegates to ``querystring_replace`` (django-tables2 >= 3.0) or ``querystring`` (< 3.0), so a single
    table template renders across both versions. Both implementations pop and ignore the tag name, so
    the token passes through unchanged.
    """
    return _querystring_impl(parser, token)


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


@register.inclusion_tag(f"{crud_views_settings.theme_path}/snippets/pagination.html", takes_context=True)
def cv_pagination(context):
    request = context.get("request")
    params = request.GET.copy() if request is not None else {}
    if hasattr(params, "pop"):
        params.pop("page", None)
    base_qs = params.urlencode() if hasattr(params, "urlencode") else ""
    return {
        "page_obj": context.get("page_obj"),
        "paginator": context.get("paginator"),
        "is_paginated": context.get("is_paginated", False),
        "base_qs": base_qs,
    }


@register.filter
def cv_is_false(arg):
    return arg is False


@register.filter
def cv_is_true(arg):
    return arg is True


@register.filter
def cv_is_list(arg):
    return isinstance(arg, (list, tuple))


@register.filter
def cv_context_has_permission(view, key) -> bool:
    try:
        cls = view.cv_viewset.get_view_class(key)
    except Exception:
        return False
    return bool(cls.cv_has_access(view.request.user, getattr(view, "object", None)))


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_card_action(context, action, obj=None):
    view = cv_get_view(context)

    if action.child_name:
        url = view.cv_get_child_url(action.child_name, action.child_key, obj)
        child_viewset = view.cv_viewset.get_viewset(action.child_name)
        child_cls = child_viewset.get_view_class(action.child_key)
        return {
            "cv_access": True,
            "cv_action_enabled": child_cls.cv_action_enabled(context["request"].user, obj),
            "cv_url": url,
            "cv_label": action.label,
            "cv_icon_action": child_cls.cv_icon_action,
            "cv_variant": action.variant,
            "cv_flex": action.flex,
            "cv_no_label": action.no_label,
            "cv_list_action_method": "get",
        }

    user = context["request"].user
    cls = view.cv_viewset.get_view_class(action.key)
    access = cls.cv_has_access(user, obj)
    action_enabled = cls.cv_action_enabled(user, obj)

    if not access:
        return {"cv_access": False, "cv_action_enabled": action_enabled}

    url = view.cv_get_url(action.key, obj=obj)
    view_context = view.cv_get_view_context(object=obj)

    if action.label:
        label = action.label
    else:
        label = cls.cv_get_action_short_label(context=view_context)

    data = cls.cv_get_dict(
        context=view_context,
        cv_oid=view.cv_get_oid(action.key, obj=obj),
        cv_url=url,
        cv_access=True,
        cv_action_enabled=action_enabled,
    )
    data.update(
        cv_label=label,
        cv_variant=action.variant,
        cv_flex=action.flex,
        cv_no_label=action.no_label,
    )
    return data


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
    request = context["request"]
    card_context = {"object": obj, "view": view, "request": request}
    # Pass request= explicitly so Template.render() builds a RequestContext (not a plain Context).
    # Without it, built-in context processors (e.g. csrf) never run, so {% csrf_token %} in any
    # template included from here (e.g. card_action.html's hidden POST form) silently renders empty.
    return mark_safe(t.render(card_context, request=request))
