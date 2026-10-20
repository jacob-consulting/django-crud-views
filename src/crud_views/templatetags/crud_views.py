from django import template
from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import get_language, get_language_info
from django_tables2.templatetags import django_tables2 as _dt2

from crud_views.lib import assets
from crud_views.lib.button_classes import get_button_class
from crud_views.lib.exceptions import ViewSetKeyFoundError, ignore_exception
from crud_views.lib.icons import render_icon
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView
from crud_views.lib.view.button_data import cv_button_data
from crud_views.lib.view.visibility import cv_resolve_action

register = template.Library()

# django-tables2 3.0.0 renamed the ``querystring`` tag to ``querystring_replace`` (to avoid shadowing
# Django 5.1's built-in tag). Resolve whichever the installed version provides; both share the same
# ``(parser, token)`` signature and pop/ignore their own tag name.
_querystring_impl = getattr(_dt2, "querystring_replace", None) or _dt2.querystring


def _resolve_nonce(context) -> str | None:
    """CSP nonce auto-detect: request attribute (django-csp convention), Django 6's
    built-in middleware, then a csp_nonce context variable. Checks existence and
    force-evaluates via str() — Django 6's LazyNonce is falsy until first evaluated."""
    request = context.get("request")
    if request is not None:
        nonce = getattr(request, crud_views_settings.csp_nonce_attr, None)
        if nonce is None:
            try:
                from django.middleware.csp import get_nonce  # Django >= 6.0 only
            except ImportError:
                pass
            else:
                nonce = get_nonce(request)
        if nonce is not None:
            return str(nonce) or None
    nonce = context.get("csp_nonce")
    if nonce is not None:
        return str(nonce) or None
    return None


def _asset_items(entries) -> list:
    items = []
    for asset in entries:
        crossorigin = asset.crossorigin
        if asset.integrity and crossorigin is None:
            crossorigin = "anonymous"  # required for cross-origin SRI fetches
        items.append({"url": assets.resolve_url(asset.path), "integrity": asset.integrity, "crossorigin": crossorigin})
    return items


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/css.html", takes_context=True)
def cv_css(context):
    entries = [entry.asset for entry in assets.tag_entries("css")]
    return {"css": _asset_items(entries), "nonce": _resolve_nonce(context)}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/js.html", takes_context=True)
def cv_js(context):
    entries = [entry.asset for entry in assets.tag_entries("js")]
    return {"js": _asset_items(entries), "nonce": _resolve_nonce(context)}


def cv_get_view(context) -> CrudView:
    view: CrudView = context["view"]
    assert isinstance(view, CrudView), f"view {view} is not ViewSetAware"
    return view


def cv_get_context(context, key, obj=None) -> dict:
    view: CrudView = cv_get_view(context)
    context = view.cv_get_context(key, obj=obj, user=context["request"].user, request=context["request"])
    return context


def _render_context_button(view, ctx) -> str:
    ctx = cv_resolve_action(ctx)
    if ctx is None:
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
    return cv_resolve_action(cv_get_context(context=context, key=key, obj=obj)) or {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_list_action_form(context, key, obj=None):
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    # a disabled button never submits: no hidden POST form for it (#149)
    if ctx is None or ctx["cv_disabled"]:
        return {}
    return ctx


@register.simple_tag(takes_context=True)
def cv_list_action_group(context, obj):
    """Row actions split into inline buttons and menu items (#174)."""
    return cv_get_view(context).cv_get_list_action_group(obj)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def cv_render_list_action(context, ctx):
    """Render already-resolved row action data (#174)."""
    return ctx or {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_render_list_action_form(context, ctx):
    """Hidden POST form for already-resolved action data; nothing for a disabled action (#174)."""
    if not ctx or ctx.get("cv_disabled"):
        return {}
    return ctx


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/actions_menu.html", takes_context=True)
def cv_actions_menu(context, group, location):
    """The dropdown for a group's menu items; renders nothing when there are none (#174)."""
    if group is None or not group.menu:
        return {}
    return {"cv_menu_items": group.menu, "cv_location": location, "cv_menu_icon": "actions-menu"}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/actions_menu_item.html")
def cv_render_menu_item(ctx, location):
    """One dropdown item from resolved action data (#174)."""
    return {**ctx, "cv_location": location}


def _render_context_action(context, ctx) -> str:
    """Render resolved context-button data: its template_code, its template, or the default button template."""
    if ctx.get("cv_template_code"):
        view = cv_get_view(context)
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return render_to_string(template, context=ctx, request=context["request"])


_BUTTON_LEAVES = {
    "action": f"{crud_views_settings.theme_path}/tags/button/action.html",
    "menu-item": f"{crud_views_settings.theme_path}/tags/button/menu_item.html",
}

_BUTTON_TEMPLATES = {
    "list": f"{crud_views_settings.theme_path}/tags/list_action.html",
    "card": f"{crud_views_settings.theme_path}/tags/card_action.html",
}


@register.simple_tag(takes_context=True)
def cv_button(context, location, kind="action"):
    """The action data in context as one button (kind "action") or menu item (kind "menu-item").

    The leaf template receives only the flat leaf contract of cv_button_data; hidden actions render nothing.
    """
    ctx = cv_resolve_action(context.flatten())
    if ctx is None:
        return ""
    return render_to_string(_BUTTON_LEAVES[kind], cv_button_data(ctx, location))


@register.simple_tag(takes_context=True)
def cv_render_button(context, ctx, location):
    """Render resolved action data for a container the way the per-key tags do; nothing for empty data."""
    if not ctx:
        return ""
    if location == "context":
        return _render_context_action(context, ctx)
    # render on the bound context like an inclusion tag: context processors run once per page, not per button
    template = context.template.engine.get_template(_BUTTON_TEMPLATES[location])
    new_context = context.new(ctx)
    if (token := context.get("csrf_token")) is not None:
        new_context["csrf_token"] = token
    return template.render(new_context)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_action(context, key, obj=None):
    obj = obj if obj else None  # fix empty string from template
    # gate here, not only in the default template: per-button template / template_code must not show a
    # button the user may not use (#147); in disable mode they get cv_disabled data instead (#149)
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    if ctx is None:
        return ""
    return _render_context_action(context, ctx)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_empty_dict=True)
def cv_context_action_form(context, key, obj=None):
    """Hidden POST form for a context action; nothing for GET, hidden or disabled actions (#178)."""
    obj = obj if obj else None  # fix empty string from template
    if obj is None:
        obj = getattr(cv_get_view(context), "object", None)
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    if ctx is None or ctx["cv_disabled"]:
        return {}
    return ctx


@register.simple_tag(takes_context=True)
def cv_render_context_action(context, ctx) -> str:
    """Render already-resolved context-button data exactly like cv_context_action does (#174)."""
    return _render_context_action(context, ctx)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_button(context, key, obj=None):
    obj = obj if obj else None  # fix empty string from template
    view = cv_get_view(context)
    if obj is None:
        obj = getattr(view, "object", None)
    ctx = cv_get_context(context=context, key=key, obj=obj)
    return _render_context_button(view, ctx)


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value=None)
def cv_context_url(context, key, obj=None):
    obj = obj if obj else None  # fix empty string from template
    view = cv_get_view(context)
    if obj is None:
        obj = getattr(view, "object", None)
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    # a bare URL cannot say "disabled": None for every unusable action, in both modes (#149)
    if ctx is None or ctx["cv_disabled"]:
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
    group = view.cv_get_context_action_group(obj if obj else None)
    return {"view": view, "request": context["request"], "object": obj, "group": group}


@register.simple_tag(takes_context=True)
def cv_header_icon(context):
    view: CrudView = cv_get_view(context)
    return render_icon(view.cv_get_header_icon())


@register.simple_tag(takes_context=True)
def cv_filter_header(context):
    view: CrudView = cv_get_view(context)
    return view.cv_filter_header


@register.simple_tag(takes_context=True)
def cv_header(context):
    view: CrudView = cv_get_view(context)
    return view.cv_header


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/breadcrumb.html", takes_context=True)
def cv_breadcrumb(context):
    breadcrumb = context.get("cv_breadcrumb")
    return {"items": breadcrumb.resolve_items() if breadcrumb else []}


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


def _language_name_local(code, fallback):
    """A language's name in that language ("Deutsch"), so the selector stays readable whatever is active."""
    try:
        return capfirst(get_language_info(code)["name_local"])
    except KeyError:
        return fallback


@register.inclusion_tag(f"{crud_views_settings.theme_path}/snippets/language_selector.html", takes_context=True)
def cv_language_selector(context):
    request = context.get("request")
    return {
        "languages": [(code, _language_name_local(code, name)) for code, name in settings.LANGUAGES],
        "current": get_language(),
        "next": request.get_full_path() if request is not None else "/",
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
    return cv_resolve_action(view.cv_get_card_action_data(action, obj, context["request"].user)) or {}


@register.simple_tag(takes_context=True)
def cv_card_action_group(context, obj):
    """Card actions split into inline buttons and menu items (#174); None for a view without card actions."""
    get_group = getattr(cv_get_view(context), "cv_get_card_action_group", None)
    return get_group(obj) if get_group else None


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_render_card_action(context, ctx):
    """Render already-resolved card action data (#174)."""
    return ctx or {}


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


@register.simple_tag
def cv_icon(value, css=""):
    """Render a semantic icon name, library-prefixed name or raw class string as an <i> element."""
    return render_icon(value, css)


@register.simple_tag
def cv_button_class(location, slot):
    """Resolved CSS classes for the button slot ``location:slot`` (autoescaped)."""
    return get_button_class(location, slot)
