from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import HtmlDjangoLexer, PythonLexer

register = template.Library()


@register.simple_tag
def get_features():
    from project.features import FEATURES

    return FEATURES


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
