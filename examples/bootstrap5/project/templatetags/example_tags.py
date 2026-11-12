from dataclasses import replace
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import HtmlDjangoLexer, PythonLexer

register = template.Library()


@register.simple_tag(takes_context=True)
def get_feature_groups(context):
    """Navbar data: the feature groups, plus the group key and app of the current page's feature (or None)."""
    from project.features import feature_groups

    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    groups = feature_groups()
    # Checklist shares Formsets' catalog/source panels but deserves a direct navigation link.
    for _, features in groups:
        for index, item in enumerate(features):
            if item.app == "formsets":
                features.insert(index + 1, replace(item, title="Formsets Compact Checklist", url_name="checklist-list"))
                break
        for index, item in enumerate(features):
            if item.app == "conditional":
                features[index] = replace(item, title="Conditional simple")
                features.insert(index + 1, replace(item, title="Conditional complex", url_name="customer-list"))
                break
    active_url_name = feature.url_name if feature else None
    if feature and feature.app == "formsets" and view.cv_viewset.name == "checklist":
        active_url_name = "checklist-list"
    if feature and feature.app == "conditional" and view.cv_viewset.name == "customer":
        active_url_name = "customer-list"
    return {
        "groups": groups,
        "active_group": feature.group if feature else None,
        "active_app": feature.app if feature else None,
        "active_url_name": active_url_name,
    }


@register.inclusion_tag("project/example_about.html", takes_context=True)
def example_about(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    return {"feature": feature}


#: files rendered on each feature app's pages, in this order
SNIPPET_FILES = ["models.py", "views.py"]


def _highlight(source: str, lexer=None) -> str:
    formatter = HtmlFormatter(noclasses=True, style="friendly")
    return highlight(source, lexer or PythonLexer(), formatter)


def _feature_for(view):
    """The Feature a view class belongs to, or None for non-feature views."""
    from project.features import FEATURES

    app = type(view).__module__.split(".")[0]
    return next((f for f in FEATURES if f.app == app), None)


@register.inclusion_tag("project/snippet_panels.html", takes_context=True)
def snippet_panels(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    app = feature.app if feature else None
    panels = []
    if app:
        app_dir = Path(settings.BASE_DIR) / app
        # the app's own templates follow the Python files: some features live in a template
        files = [(name, PythonLexer()) for name in SNIPPET_FILES if (app_dir / name).exists()]
        files += [
            (path.relative_to(app_dir).as_posix(), HtmlDjangoLexer())
            for path in sorted((app_dir / "templates").rglob("*.html"))
        ]
        for name, lexer in files:
            panels.append(
                {
                    "id": f"snippet-{app}-{name.replace('.', '-').replace('/', '-')}",
                    "title": f"{app}/{name}",
                    "html": mark_safe(_highlight((app_dir / name).read_text(), lexer)),
                }
            )
    return {
        "panels": panels,
        "look_at": feature.look_at if feature else "",
        "docs": feature.docs if feature else (),
    }
