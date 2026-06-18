from types import SimpleNamespace

from crud_views.lib.check import CheckTemplate
from crud_views.lib.viewset import ViewSet
from tests.test1.app.views import AuthorDetailView  # registered to cv_author


def test_viewset_extends_field_defaults_to_none():
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="extends_default_probe")
    assert vs.extends is None


def test_viewset_checks_include_extends_template_check():
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="extends_check_probe", extends="app/index.html")
    template_checks = [
        c for c in vs.checks()
        if isinstance(c, CheckTemplate) and c.attribute == "extends"
    ]
    assert len(template_checks) == 1


def _resolve(view_template, viewset_extends):
    view = AuthorDetailView()
    view.cv_extends_template = view_template
    view.cv_viewset = SimpleNamespace(extends=viewset_extends)
    return view.cv_get_extends_template()


def test_resolution_falls_back_to_global_setting():
    # nothing overridden anywhere -> global CRUD_VIEWS_EXTENDS ("app/crud_views.html")
    assert _resolve(None, None) == "app/crud_views.html"


def test_resolution_uses_viewset_extends_over_global():
    assert _resolve(None, "app/index.html") == "app/index.html"


def test_resolution_view_overrides_viewset():
    assert _resolve("app/base.html", "app/index.html") == "app/base.html"


def test_view_checks_include_cv_extends_template_check():
    template_checks = [
        c for c in AuthorDetailView.checks()
        if isinstance(c, CheckTemplate) and c.attribute == "cv_extends_template"
    ]
    assert len(template_checks) == 1
