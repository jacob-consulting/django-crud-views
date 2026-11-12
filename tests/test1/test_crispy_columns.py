"""Numbered columns resolve theme classes without taking ownership of custom templates."""

from copy import deepcopy
from importlib.metadata import distribution
from types import SimpleNamespace

import pytest
from crispy_forms.layout import Column, Div, Layout
from django import forms
from django.conf import settings
from django.template import Context, TemplateDoesNotExist
from django.template.loader import get_template
from django.test import override_settings
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.crispy import Column6
from crud_views.lib.crispy import table as columns


@pytest.fixture(autouse=True)
def isolate_classes():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    bc.reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    bc.reset_button_classes_cache()


class ExampleForm(forms.Form):
    crispy_field_template = None
    name = forms.CharField()
    other = forms.CharField(required=False)


def render_column(column, context=None, form=None, template_pack="bootstrap5"):
    return column.render(
        form if form is not None else ExampleForm({"name": "Ada"}),
        context if context is not None else Context({"form_show_errors": True}),
        template_pack=template_pack,
    )


def test_column6_theme_tracer():
    column = Column6("name", css_class="extra")
    original = deepcopy(vars(column))
    context = Context({"div": "outer", "fields": "outer-fields", "sentinel": object()})
    surrounding = context.flatten()
    bc.register_button_classes({"form:column-6": "span-6"})
    for _ in range(2):
        wrapper = html.fromstring(render_column(column, context=context))
        assert set(wrapper.classes) == {"span-6", "extra"}
        assert wrapper.cssselect("input[name=name]")[0].get("value") == "Ada"
        assert vars(column) == original
        assert all(context[key] == value for key, value in surrounding.items())


@pytest.mark.parametrize("width", range(1, 13))
def test_default_column_bytes(width):
    helper = getattr(columns, f"Column{width}")
    assert helper.css_class == f"col-md-{width}"
    kwargs = {"css_id": "wrapper", "data_test": "column", "css_class": "extra"}
    assert render_column(helper("name", **kwargs)) == render_column(
        Column("name", css_class=f"col-md-{width} extra", css_id="wrapper", data_test="column")
    )


@pytest.mark.parametrize("width", range(1, 13))
@pytest.mark.parametrize("value", ["span-6", "col-12 col-lg-6", "", None])
@pytest.mark.parametrize("extra", [None, "extra"])
def test_column_theme_and_project_layers(width, value, extra):
    column = getattr(columns, f"Column{width}")("name", css_class=extra)
    original = deepcopy(vars(column))
    key = f"form:column-{width}"
    bc.register_button_classes({key: value})
    expected = set((value or "").split()) | ({extra} if extra else set())
    assert set(html.fromstring(render_column(column)).classes) == expected
    other_width = width % 12 + 1
    other = getattr(columns, f"Column{other_width}")("name")
    assert set(html.fromstring(render_column(other)).classes) == {f"col-md-{other_width}"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "project"}):
        assert set(html.fromstring(render_column(column)).classes) == {"project"} | ({extra} if extra else set())
    assert set(html.fromstring(render_column(column)).classes) == expected
    bc.register_button_classes({key: "new-theme"})
    assert set(html.fromstring(render_column(column)).classes) == {"new-theme"} | ({extra} if extra else set())
    for suppressed in ("", None):
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: suppressed}):
            assert set(html.fromstring(render_column(column)).classes) == ({extra} if extra else set())
    assert vars(column) == original


@pytest.mark.parametrize("authored", ["custom", "col-md-6", "", None])
@pytest.mark.parametrize("inherited", [False, True])
@pytest.mark.parametrize("extra", [None, "extra"])
def test_authored_subclass_classes(authored, inherited, extra):
    class CustomColumn(Column6):
        css_class = authored

    class InheritedColumn(CustomColumn):
        pass

    column = (InheritedColumn if inherited else CustomColumn)("name", css_class=extra)
    bc.register_button_classes({"form:column-6": "theme"})
    assert set(html.fromstring(render_column(column)).classes) == set((authored or "").split()) | (
        {extra} if extra else set()
    )


def test_plain_subclass_inherits_live_registry():
    class CustomColumn(Column6):
        pass

    bc.register_button_classes({"form:column-6": "theme"})
    assert set(html.fromstring(render_column(CustomColumn("name"))).classes) == {"theme"}


@pytest.mark.parametrize("extras", [None, "extra"])
@pytest.mark.parametrize("authored", ["authored", "col-md-6", "col-md-6 extra", "", None])
@pytest.mark.parametrize("after_render", [False, True])
def test_instance_class_assignment_is_authoritative(extras, authored, after_render):
    column = Column6("name", css_class=extras)
    bc.register_button_classes({"form:column-6": "theme"})
    if after_render:
        render_column(column)
    column.css_class = authored
    for _ in range(2):
        assert set(html.fromstring(render_column(column)).classes) == set((authored or "").split())


def test_column_nested_sibling_context_isolation():
    column = Column6("name", css_id="nested")
    sibling = Column6("other", css_id="sibling")
    layout = Layout(Div(column, css_id="outer", css_class="outer"), sibling)
    context = Context({"div": "caller-div", "fields": "caller-fields", "sentinel": object()})
    original = context.flatten()
    bc.register_button_classes({"form:column-6": "theme"})
    for _ in range(2):
        document = html.fragment_fromstring(render_column(layout, context=context), create_parent=True)
        assert document.cssselect("#outer #nested input[name=name]")
        assert document.cssselect("#sibling input[name=other]")
        assert not document.cssselect("#nested input[name=other], #sibling input[name=name]")
        assert all(context[key] == value for key, value in original.items())


def custom_templates(templates):
    return override_settings(
        TEMPLATES=[
            {
                **settings.TEMPLATES[0],
                "APP_DIRS": False,
                "OPTIONS": {
                    **settings.TEMPLATES[0].get("OPTIONS", {}),
                    "loaders": [
                        ("django.template.loaders.locmem.Loader", templates),
                        "django.template.loaders.app_directories.Loader",
                    ],
                },
            }
        ]
    )


@pytest.mark.parametrize("selection", ["constructor", "subclass", "hook", "instance", "loader", "pack"])
def test_custom_template_ownership(selection):
    source = '<section class="fixed {{ div.css_class }}">{{ fields|safe }}</section>'
    name = "bootstrap5/layout/column.html" if selection == "loader" else "custom/column.html"
    pack = "bootstrap5"
    if selection == "constructor":
        column = Column6("name", template=name)
    elif selection == "subclass":

        class CustomColumn(Column6):
            template = name

        column = CustomColumn("name")
    elif selection == "hook":

        class CustomColumn(Column6):
            def get_template_name(self, template_pack):
                return name

        column = CustomColumn("name")
    else:
        column = Column6("name")
        if selection == "instance":
            column.template = name
        elif selection == "pack":
            pack = "custom"
            name = "custom/layout/column.html"
    templates = {name: source}
    if pack == "custom":
        templates["custom/field.html"] = "{{ field }}"
    bc.register_button_classes({"form:column-6": "span-6"})
    with custom_templates(templates):
        wrapper = html.fromstring(render_column(column, template_pack=pack))
        assert wrapper.tag == "section"
        assert set(wrapper.classes) == {"fixed", "span-6"}
        assert wrapper.cssselect("input[name=name]")[0].get("value") == "Ada"
    if selection == "loader":
        assert html.fromstring(render_column(column)).tag == "div"


@pytest.mark.parametrize("selection", ["constructor", "subclass", "hook", "instance-hook"])
def test_explicit_stock_name_remains_pack_owned(selection):
    name = "bootstrap5/layout/column.html"
    if selection == "constructor":
        column = Column6("name", template=name)
    elif selection == "subclass":

        class CustomColumn(Column6):
            template = name

        column = CustomColumn("name")
    elif selection == "hook":

        class CustomColumn(Column6):
            def get_template_name(self, template_pack):
                return name

        column = CustomColumn("name")
    else:
        column = Column6("name")
        column.get_template_name = lambda template_pack: name
    bc.register_button_classes({"form:column-6": "span-6"})
    assert set(html.fromstring(render_column(column)).classes) == {"col-md", "span-6"}


def test_stock_bridge_origin_source_and_pack_boundaries(tmp_path):
    template = get_template("bootstrap5/layout/column.html")
    assert template.template.source == columns._BOOTSTRAP5_COLUMN_SOURCE
    assert columns._use_bootstrap5_column_bridge("bootstrap5", template)
    installed = distribution("crispy-bootstrap5").locate_file(
        "crispy_bootstrap5/templates/bootstrap5/layout/column.html"
    )
    for origin, source, pack in [
        (str(tmp_path / "column.html"), template.template.source, "bootstrap5"),
        (str(installed), template.template.source + "\n", "bootstrap5"),
        (str(installed), template.template.source, "other"),
    ]:
        candidate = SimpleNamespace(origin=SimpleNamespace(name=origin), template=SimpleNamespace(source=source))
        assert not columns._use_bootstrap5_column_bridge(pack, candidate)
    with custom_templates({"bootstrap5/layout/column.html": template.template.source}):
        assert not columns._use_bootstrap5_column_bridge("bootstrap5", get_template("bootstrap5/layout/column.html"))


def test_plain_crispy_column_keeps_fallback():
    assert set(html.fromstring(render_column(Column("name", css_class="span-6"))).classes) == {"col-md", "span-6"}


def test_column_missing_template_raises():
    with pytest.raises(TemplateDoesNotExist):
        render_column(Column6("name", template="missing-column.html"))


def test_column_attributes_values_and_errors_are_escaped():
    hostile = '"><script data-injected="yes">bad</script>'
    column = Column6("name", css_id=hostile, data_test=hostile, aria_label="Column")
    bc.register_button_classes({"form:column-6": hostile})
    document = html.fromstring(render_column(column, form=ExampleForm({"name": hostile})))
    assert document.get("id") == hostile
    assert document.get("class") == hostile
    assert document.get("data-test") == hostile
    assert document.get("aria-label") == "Column"
    assert document.cssselect("input[name=name]")[0].get("value") == hostile
    assert not document.cssselect("script, [data-injected]")
    invalid = ExampleForm({"name": ""})
    assert not invalid.is_valid()
    rendered = html.fromstring(render_column(column, form=invalid))
    assert "This field is required." in rendered.text_content()


def test_delete_confirmation_uses_column12():
    from tests.test1.test_theme_action_groups import DeleteForm

    form = DeleteForm(None)
    form.crispy_field_template = None
    column = form.helper.layout.fields[0].fields[0]
    bc.register_button_classes({"form:column-12": "delete-width"})
    wrapper = html.fromstring(render_column(column, form=form))
    assert set(wrapper.classes) == {"delete-width"}
    assert wrapper.cssselect("input[name=confirm]")


@pytest.mark.django_db
@pytest.mark.parametrize("width", [2, 4])
def test_classic_formset_control_columns(width):
    from crud_views.lib.formsets import FormSet
    from tests.test1.app.views_formset import BookFormSet

    config = FormSet(title="Books", klass=BookFormSet)
    formset = BookFormSet(formset=config)
    column = getattr(formset, f"form_control_col{width}")
    bc.register_button_classes({f"form:column-{width}": "control-width"})
    wrapper = html.fromstring(render_column(column, form=formset.empty_form))
    assert set(wrapper.classes) == {"control-width", "text-end"}
    assert wrapper.cssselect(".cv-form-ctrl button")


@pytest.mark.django_db
def test_workflow_buttons_and_visible_comment_columns(client_user_campaign_change, campaign_new, monkeypatch):
    from tests.test1.app.views import CampaignWorkflowView

    monkeypatch.setattr(CampaignWorkflowView, "cv_transition_presentation", "buttons")
    bc.register_button_classes({"form:column-8": "workflow-width"})
    response = client_user_campaign_change.get(f"/campaign/{campaign_new.pk}/workflow/")
    assert response.status_code == 200
    document = html.fromstring(response.content)
    wrappers = document.cssselect(".workflow-width")
    assert len(wrappers) == 2
    assert all(wrapper.get("style") == "overflow-wrap: anywhere;" for wrapper in wrappers)
    assert wrappers[0].cssselect('button[name="transition"]')
    assert wrappers[1].cssselect('textarea[name="comment"]')
