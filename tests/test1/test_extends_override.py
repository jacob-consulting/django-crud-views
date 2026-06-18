from crud_views.lib.check import CheckTemplate
from crud_views.lib.viewset import ViewSet


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
