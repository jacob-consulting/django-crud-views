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
        for index, item in enumerate(features):
            if item.app == "queryset_conditional":
                features[index : index + 1] = [
                    replace(item, title="Queryset conditional standalone"),
                    replace(item, title="Queryset conditional ordinary rows", url_name="service_batch-list"),
                    replace(item, title="Queryset conditional compact rows", url_name="service_batch_compact-list"),
                ]
                break
    active_url_name = feature.url_name if feature else None
    if feature and feature.app == "formsets" and view.cv_viewset.name == "checklist":
        active_url_name = "checklist-list"
    if feature and feature.app == "conditional" and view.cv_viewset.name == "customer":
        active_url_name = "customer-list"
    if feature and feature.app == "queryset_conditional":
        active_url_name = f"{view.cv_viewset.name}-list"
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
    """Render each example's source selection.

    ``example_source_files`` deliberately has no ``cv_`` prefix: it belongs only
    to these example views, not the package CrudView API. An explicit selection
    completely replaces the default Python and template panels. Paths are
    developer-specified, app-relative files; request data never selects source.
    """
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    app = feature.app if feature else None
    panels = []
    if app:
        app_dir = (Path(settings.BASE_DIR) / app).resolve()
        selection = getattr(view, "example_source_files", None)
        if selection is None:
            # The app's own templates follow the Python files: some features live in a template.
            files = [(name, PythonLexer()) for name in SNIPPET_FILES if (app_dir / name).exists()]
            files += [
                (path.relative_to(app_dir).as_posix(), HtmlDjangoLexer())
                for path in sorted((app_dir / "templates").rglob("*.html"))
            ]
        else:
            files = []
            for name in selection:
                path = Path(name)
                resolved = (app_dir / path).resolve()
                if path.is_absolute() or ".." in path.parts or not resolved.is_relative_to(app_dir):
                    raise ValueError("example_source_files must stay within the example app directory")
                if not resolved.is_file():
                    raise ValueError("example_source_files must name existing files")
                files.append((path.as_posix(), HtmlDjangoLexer() if path.suffix == ".html" else PythonLexer()))
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
