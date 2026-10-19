from django.template import Context, Template

EXPECTED = '<i class="fa-regular fa-eye me-2" aria-hidden="true"></i>'


def _render(lib: str, value, tag="{% cv_icon v css='me-2' %}") -> str:
    return Template("{% load " + lib + " %}" + tag).render(Context({"v": value}))


def test_cv_icon_crud_views():
    assert _render("crud_views", "detail") == EXPECTED


def test_cv_icon_object_detail():
    assert _render("crud_views_object_detail", "detail") == EXPECTED


def test_cv_icon_empty():
    assert _render("crud_views", None) == ""
    assert _render("crud_views_object_detail", None) == ""


def test_cv_icon_no_css():
    assert _render("crud_views", "detail", "{% cv_icon v %}") == '<i class="fa-regular fa-eye" aria-hidden="true"></i>'


def test_cv_css_includes_icons_css():
    html = Template("{% load crud_views %}{% cv_css %}").render(Context({}))
    assert "crud_views/css/icons.css" in html


def test_cv_icon_tag_non_str_context_value_renders_nothing():
    assert _render("crud_views", 5, "{% cv_icon v %}") == ""
