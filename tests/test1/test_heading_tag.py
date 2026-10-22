"""#251: {% cv_heading %} renders the heading level from CRUD_VIEWS_HEADER_LEVEL and keeps the look."""

import pytest
from django.template import Context, Engine, Template, TemplateSyntaxError

from crud_views.lib.settings import crud_views_settings


def _render(tag: str, body: str = "X", context: dict | None = None) -> str:
    tpl = Template(f"{{% load crud_views %}}{{% cv_heading {tag} %}}{body}{{% endcv_heading %}}")
    return tpl.render(Context(context or {}))


@pytest.fixture
def level(monkeypatch):
    def set_level(value):
        monkeypatch.setattr(crud_views_settings, "header_level", value)

    return set_level


@pytest.mark.parametrize(
    ("header_level", "tag", "expected"),
    [
        # unset: the template's own level, exactly today's markup
        (None, 'level=5 class="card-title"', '<h5 class="card-title">X</h5>'),
        (None, "level=5", "<h5>X</h5>"),
        (None, 'level=5 class=""', "<h5>X</h5>"),
        # content heading: one below the header, sized like the template's own level
        (1, 'level=5 class="card-title"', '<h2 class="h5 card-title">X</h2>'),
        (2, 'level=5 class="card-title"', '<h3 class="h5 card-title">X</h3>'),
        (1, "level=5", '<h2 class="h5">X</h2>'),
        (1, 'level=2 class="accordion-header"', '<h2 class="accordion-header">X</h2>'),
        (2, 'level=2 class="accordion-header"', '<h3 class="h2 accordion-header">X</h3>'),
        # header: exactly the setting's level
        (None, '"header" level=5 class="modal-title"', '<h5 class="modal-title">X</h5>'),
        (1, '"header" level=5 class="modal-title"', '<h1 class="h5 modal-title">X</h1>'),
        (1, '"header" level=1 class="h3"', '<h1 class="h3">X</h1>'),
        (2, '"header" level=1', '<h2 class="h1">X</h2>'),
    ],
)
def test_heading_markup(level, header_level, tag, expected):
    level(header_level)
    assert _render(tag) == expected


def test_class_from_variable_is_escaped(level):
    level(None)
    assert _render("level=5 class=cls", context={"cls": 'a" onclick="x'}) == (
        '<h5 class="a&quot; onclick=&quot;x">X</h5>'
    )


def test_body_sees_caller_context(level):
    level(1)
    assert _render("level=5", body="{{ name }}", context={"name": "Jane"}) == '<h2 class="h5">Jane</h2>'


def test_block_inside_heading_can_be_overridden(level):
    level(None)
    engine = Engine(
        loaders=[
            (
                "django.template.loaders.locmem.Loader",
                {
                    "p.html": (
                        "{% load crud_views %}{% cv_heading level=5 %}{% block t %}A{% endblock %}{% endcv_heading %}"
                    ),
                    "c.html": '{% extends "p.html" %}{% block t %}B{% endblock %}',
                },
            )
        ],
        libraries={"crud_views": "crud_views.templatetags.crud_views"},
    )
    assert engine.get_template("c.html").render(Context()) == "<h5>B</h5>"


@pytest.mark.parametrize(
    "source",
    [
        "{% cv_heading %}X{% endcv_heading %}",
        "{% cv_heading level=0 %}X{% endcv_heading %}",
        "{% cv_heading level=7 %}X{% endcv_heading %}",
        '{% cv_heading level="x" %}X{% endcv_heading %}',
        "{% cv_heading level=x %}X{% endcv_heading %}",
        "{% cv_heading level=True %}X{% endcv_heading %}",
        "{% cv_heading level=5|add:1 %}X{% endcv_heading %}",
        "{% cv_heading level=5 size=5 %}X{% endcv_heading %}",
        '{% cv_heading "title" level=5 %}X{% endcv_heading %}',
        "{% cv_heading level=5 %}X",
    ],
)
def test_bad_arguments_fail_at_parse_time(source):
    with pytest.raises(TemplateSyntaxError) as exc:
        Template("{% load crud_views %}" + source)
    # the tag's own validation, not Django's "unknown tag"
    assert "Invalid block tag" not in str(exc.value)
