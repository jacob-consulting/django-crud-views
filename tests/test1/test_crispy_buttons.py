"""Crispy form buttons read the layered button class table and render through the form-button leaf (Phase 6)."""

import logging
import re
import warnings
from types import SimpleNamespace

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.template import Context, Template
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.test import override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.crispy import Button, CrispyDeleteForm, Reset, Submit
from crud_views.lib.settings import CrudViewsSettings


def url(viewset, key, pk=None) -> str:
    kwargs = {"pk": pk} if pk is not None else {}
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def tag(html: str, **attrs) -> str:
    """The first <input ...> tag carrying all the given attributes."""
    for match in re.finditer(r"<input\b[^>]*>", html):
        found = match.group(0)
        if all(f'{k}="{v}"' in found for k, v in attrs.items()):
            return found
    raise AssertionError(f"no input with {attrs} in page")


def button(html: str, **attrs) -> str:
    """The first <button ...> start tag carrying all the given attributes."""
    for match in re.finditer(r"<button\b[^>]*>", html):
        found = match.group(0)
        if all(f'{k}="{v}"' in found for k, v in attrs.items()):
            return found
    raise AssertionError(f"no button with {attrs} in page")


@pytest.mark.django_db
def test_submit_and_cancel_classes(client_user_author_add, cv_author):
    html = client_user_author_add.get(url(cv_author, "create")).content.decode()
    assert 'class="btn btn-primary"' in button(html, name="submit")
    assert 'class="btn btn-secondary"' in button(html, name="reset")
    assert "btn btn btn-secondary" not in html


@pytest.mark.django_db
def test_delete_button_hook(client_user_author_delete, cv_author, author_douglas_adams, monkeypatch, settings):
    from tests.test1.app.views import AuthorDeleteView

    target = url(cv_author, "delete", author_douglas_adams.pk)
    html = client_user_author_delete.get(target).content.decode()
    delete = button(html, name="delete")
    assert 'class="btn btn-primary"' in delete
    assert 'value="Delete"' in delete

    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:delete": "btn btn-danger"}):
        html = client_user_author_delete.get(target).content.decode()
    assert 'class="btn btn-danger"' in button(html, name="delete")

    class EraseForm(CrispyDeleteForm):
        def get_delete_button_kwargs(self) -> dict:
            return {"name": "delete", "value": "Erase"}

    monkeypatch.setattr(AuthorDeleteView, "form_class", EraseForm)
    html = client_user_author_delete.get(target).content.decode()
    assert 'value="Erase"' in button(html, name="delete")


@pytest.mark.django_db
def test_delete_button_kwargs_may_choose_the_slot(
    client_user_author_delete, cv_author, author_douglas_adams, monkeypatch
):
    from tests.test1.app.views import AuthorDeleteView

    class SlotForm(CrispyDeleteForm):
        def get_delete_button_kwargs(self) -> dict:
            return {**super().get_delete_button_kwargs(), "slot": "form:cancel"}

    monkeypatch.setattr(AuthorDeleteView, "form_class", SlotForm)
    html = client_user_author_delete.get(url(cv_author, "delete", author_douglas_adams.pk)).content.decode()
    assert 'class="btn btn-secondary"' in button(html, name="delete")


@pytest.mark.django_db
def test_filter_buttons(client_user_publisher_view, cv_publisher):
    html = client_user_publisher_view.get(url(cv_publisher, "list")).content.decode()
    assert 'class="btn btn-primary"' in tag(html, id="filter-button")
    reset = tag(html, id="filter-button-reset")
    assert 'class="btn btn-secondary"' in reset
    assert 'type="reset"' in reset
    assert "btn-inverse" not in html


@pytest.mark.django_db
def test_project_css_class_still_appended(client_user_author_add, cv_author, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm

    class ExtraForm(AuthorForm):
        def get_cancel_button_kwargs(self) -> dict:
            return {**super().get_cancel_button_kwargs(), "css_class": "extra"}

    monkeypatch.setattr(AuthorCreateView, "form_class", ExtraForm)
    html = client_user_author_add.get(url(cv_author, "create")).content.decode()
    assert 'class="btn btn-secondary extra"' in button(html, name="reset")


def test_filter_reset_setting_removed():
    assert not hasattr(CrudViewsSettings(), "filter_reset_button_css_class")


def test_removed_tags():
    with pytest.raises(TemplateSyntaxError):
        Template("{% load crud_views %}{% cv_cancel_button %}")
    with pytest.raises(TemplateDoesNotExist):
        get_template("crud_views/tags/button_cancel.html")


# --- the form-button leaf (Phase 6): real {% crispy %} layout renders ------------------------------------------


class _EmptyForm(forms.Form):
    pass


CRISPY = Template("{% load crispy_forms_tags %}{% crispy form helper %}")


def _helper(*controls, inputs=()) -> FormHelper:
    helper = FormHelper()
    helper.form_tag = False
    if controls:
        helper.layout = Layout(FormActions(*controls))
    for control in inputs:
        helper.add_input(control)
    return helper


def _render(helper, **extra) -> str:
    context = {"form": _EmptyForm(), "helper": helper, **extra}
    return CRISPY.render(Context(context))


def _fragment(markup: str):
    return lxml_html.fragment_fromstring(markup, create_parent="div")


def _buttons(markup: str) -> list:
    return _fragment(markup).cssselect("button")


@pytest.mark.django_db
def test_endpoint_layout_controls_are_buttons(client_user_author_add, cv_author):
    html = client_user_author_add.get(url(cv_author, "create")).content.decode()
    doc = lxml_html.fromstring(html)
    assert not doc.cssselect('input[name="submit"], input[name="reset"]')
    (submit,) = doc.cssselect('button[name="submit"]')
    (cancel,) = doc.cssselect('button[name="reset"]')
    assert (submit.get("type"), submit.get("value"), submit.get("id"), submit.get("class")) == (
        "submit",
        "Create",
        "submit-id-submit",
        "btn btn-primary",
    )
    assert submit.text_content() == "Create"
    assert (cancel.get("type"), cancel.get("value"), cancel.get("id"), cancel.get("class")) == (
        "button",
        "Cancel",
        "button-id-reset",
        "btn btn-secondary",
    )
    assert cancel.get("data-cv-cancel-url") == "/author/"
    assert cancel.text_content() == "Cancel"
    # label mode, the form floor: no icon, no hidden text, no generated title
    for el in (submit, cancel):
        assert not el.cssselect("i, svg, span.visually-hidden")
        assert el.get("title") is None and el.get("data-cv-tooltip") is None


def test_standalone_layout_submit_is_one_button():
    (el,) = _buttons(_render(_helper(Submit("submit", "Save"))))
    assert dict(el.attrib) == {
        "type": "submit",
        "name": "submit",
        "value": "Save",
        "id": "submit-id-submit",
        "class": "btn btn-primary",
    }
    assert [s.text for s in el.cssselect("span")] == ["Save"]


@pytest.mark.parametrize(
    "adapter,kind,native,classes",
    [
        (Submit, "submit", "submit", "btn btn-primary"),
        (Button, "cancel", "button", "btn btn-secondary"),
        (Reset, "filter-reset", "reset", "btn btn-secondary"),
    ],
)
def test_adapters_keep_their_kind_type_and_classes(adapter, kind, native, classes):
    (el,) = _buttons(_render(_helper(adapter("go", "Go"))))
    assert (el.get("type"), el.get("class"), el.get("name"), el.get("id")) == (native, classes, "go", f"{native}-id-go")


def test_slot_selects_the_semantic_kind_not_the_name():
    (el,) = _buttons(_render(_helper(Submit("submit", "Delete", slot="form:delete"))))
    assert el.get("class") == "btn btn-primary"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:delete": "btn btn-danger"}):
        (el,) = _buttons(_render(_helper(Submit("submit", "Delete", slot="form:delete"))))
    assert el.get("class") == "btn btn-danger"
    # cancel and filter-reset both submit name="reset": the slot decides, never the name
    classes = {"form:cancel": "x-cancel", "form:filter-reset": "x-reset"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
        (cancel,) = _buttons(_render(_helper(Button("reset", "Back", data_cv_cancel_url="/b/"))))
        (reset,) = _buttons(_render(_helper(Reset("reset", "Clear", data_cv_cancel_url="/b/"))))
    assert (cancel.get("type"), cancel.get("class"), cancel.get("data-cv-cancel-url")) == ("button", "x-cancel", "/b/")
    assert (reset.get("type"), reset.get("class"), reset.get("data-cv-cancel-url")) == ("reset", "x-reset", "/b/")


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_floor_selects_the_body(mode):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        (el,) = _buttons(_render(_helper(Submit("submit", "Save"))))
    hidden = el.cssselect("span.visually-hidden")
    assert el.text_content() == "Save"
    assert el.get("value") == "Save"
    if mode == "icon":
        assert [s.text for s in hidden] == ["Save"]
        assert (el.get("title"), el.get("data-cv-tooltip")) == ("Save", "form")
    else:
        assert not hidden
        assert el.get("title") is None and el.get("data-cv-tooltip") is None


LITERALS = [
    "",
    "Speichern ✓ 保存 Ünïcode",
    "{{ request.user }}",
    "{% now 'Y' %}",
    '"><img src=x onerror=alert(1)>',
    "a & b < c > d ' \"",
    "&amp; &lt;b&gt;",
]


@pytest.mark.parametrize("value", LITERALS, ids=repr)
@pytest.mark.parametrize("safe", [False, True])
def test_layout_values_stay_literal(value, safe):
    from django.utils.safestring import mark_safe

    raw = mark_safe(value) if safe else value
    submit = Submit("submit", raw)
    markup = _render(_helper(submit), request=SimpleNamespace(user="LEAKED-USER"))
    doc = _fragment(markup)
    (el,) = doc.cssselect("button")
    assert el.get("value") == value
    assert el.text_content() == value
    assert set(el.attrib) == {"type", "name", "value", "id", "class"}
    assert not doc.cssselect("img, b, script")
    assert "LEAKED-USER" not in markup
    # the adapter keeps its raw value: no template rendering wrote back into it
    assert submit.value is raw


def test_layout_lazy_value_renders_active_language():
    from django.utils import translation
    from django.utils.translation import gettext_lazy

    submit = Submit("submit", gettext_lazy("Save"))
    with translation.override("en"):
        (el,) = _buttons(_render(_helper(submit)))
    assert (el.get("value"), el.text_content()) == ("Save", "Save")


def test_legacy_helper_inputs_stay_inputs_without_warnings(caplog):
    caplog.set_level(logging.DEBUG)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        markup = _render(
            _helper(
                inputs=(
                    Submit("go", "{{ request.user }}"),
                    Button("reset", "Back", data_cv_cancel_url="/b/"),
                    Submit("odd", "Odd", slot="formset:control"),
                    Submit("unknown", "Unknown", slot="form:unknown"),
                )
            ),
            request=SimpleNamespace(user="LEAKED-USER"),
        )
    assert caught == []
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
    doc = _fragment(markup)
    assert not doc.cssselect("button")
    by_name = {el.get("name"): el for el in doc.cssselect("input")}
    assert by_name["go"].get("value") == "{{ request.user }}"
    assert by_name["go"].get("class") == "btn btn-primary"
    assert by_name["reset"].get("data-cv-cancel-url") == "/b/"
    assert by_name["odd"].get("class") == "btn btn-light"
    assert "LEAKED-USER" not in markup


@pytest.mark.parametrize("slot", ["formset:control", "form:unknown", "form:", "context:primary", "form:hidden-label"])
def test_layout_render_rejects_non_form_slots(slot):
    control = Submit("go", "Go", slot=slot)  # constructing never rejects (legacy helper.inputs keep any slot)
    with pytest.raises(ValueError, match="slot"):
        _render(_helper(control))


def test_layout_render_does_not_touch_the_context_or_adapter():
    submit = Submit("Search the Site", "Go", css_class="extra", data_x="1")
    state = (submit.name, submit.value, submit.id, submit.field_classes, str(submit.flat_attrs), submit.template)
    context = Context({"form": _EmptyForm(), "helper": _helper(submit), "input": "OUTER"})
    before = [dict(d) for d in context.dicts]
    first = CRISPY.render(context)
    second = CRISPY.render(context)
    assert first == second
    assert [dict(d) for d in context.dicts] == before
    assert (submit.name, submit.value, submit.id, submit.field_classes, str(submit.flat_attrs), submit.template) == (
        state
    )
    (el,) = _buttons(first)
    assert (el.get("name"), el.get("id"), el.get("class"), el.get("data-x")) == (
        "search-the-site",
        "submit-id-search-the-site",
        "btn btn-primary extra",
        "1",
    )


# --- template precedence, attributes and repeatable rendering (FORM-05 / FORM-07) --------------------------------

CUSTOM = (
    "[{{ cv_location }}|{{ cv_key }}|{{ cv_type }}|{{ cv_name }}|{{ cv_value }}|{{ cv_label }}|{{ cv_id }}"
    "|{{ cv_label_mode }}|{{ cv_css_class }}|{{ cv_cancel_url }}|input={{ input }}|{{ input.value }}"
    "|form={{ form }}|helper={{ helper }}|outer={{ outer }}]"
)


@pytest.fixture
def custom_templates(settings):
    """An isolated locmem loader in front of the project's loaders, for the custom-template cases."""
    import copy as _copy

    templates = _copy.deepcopy(settings.TEMPLATES)
    engine = templates[0]
    engine["APP_DIRS"] = False
    engine["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.locmem.Loader",
            {
                "custom/explicit.html": "explicit" + CUSTOM,
                "custom/subclass.html": "subclass" + CUSTOM,
                "bootstrap5/custom/pack.html": "pack" + CUSTOM,
            },
        ),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    settings.TEMPLATES = templates
    yield


def _custom_fields(markup: str) -> list[str]:
    return markup[markup.index("[") + 1 : markup.rindex("]")].split("|")


def _custom_name(markup: str) -> str:
    """Which custom template rendered: the word in front of its field list (inside the FormActions wrapper)."""
    return re.search(r"(\w+)\[", markup).group(1)


@pytest.mark.parametrize("adapter", [Submit, Button, Reset])
def test_template_precedence(custom_templates, adapter):
    class Subclassed(adapter):
        template = "custom/subclass.html"

    # bundled default
    (el,) = _buttons(_render(_helper(adapter("go", "Go"))))
    assert el.get("name") == "go"
    # subclass template over the bundled default
    assert _custom_name(_render(_helper(Subclassed("go", "Go")))) == "subclass"
    # an explicit template over the subclass template
    assert _custom_name(_render(_helper(Subclassed("go", "Go", template="custom/explicit.html")))) == "explicit"
    assert _custom_name(_render(_helper(adapter("go", "Go", template="custom/explicit.html")))) == "explicit"
    # %s is the active template pack
    assert _custom_name(_render(_helper(adapter("go", "Go", template="%s/custom/pack.html")))) == "pack"
    # an empty explicit template keeps crispy's truthy fallback: the subclass template, else the bundled leaf
    assert _custom_name(_render(_helper(Subclassed("go", "Go", template="")))) == "subclass"
    (el,) = _buttons(_render(_helper(adapter("go", "Go", template=""))))
    assert el.get("value") == "Go"


def test_custom_template_gets_only_normalized_fields(custom_templates):
    control = Button("reset", "Back", template="custom/explicit.html", css_class="x", data_cv_cancel_url="/b/")
    markup = _render(_helper(control), input="OUTER-INPUT", outer="OUTER", cv_value="OUTER-VALUE")
    assert _custom_fields(markup) == [
        "form",
        "cancel",
        "button",
        "reset",
        "Back",
        "Back",
        "button-id-reset",
        "label",
        "x",
        "/b/",
        "input=",
        "",
        "form=",
        "helper=",
        "outer=",
    ]
    # no layer of the caller's context reaches a custom template, even the outermost one
    context = Context({"input": "OUTER-INPUT", "cv_label": "OUTER"})
    context.push({"form": _EmptyForm(), "helper": _helper(control)})
    fields = _custom_fields(CRISPY.render(context))
    assert fields[5] == "Back" and fields[10] == "input="


NAMES = [
    "submit",
    "reset",
    "a.b!",
    "Ünïcode",
    "Search the Site",
    "Search  the Site!",
    " leading and trailing ",
    "tab\tseparated",
    "Hello, World!",
    "Ünïcode name",
    "名前 ボタン",
]


@pytest.mark.parametrize("name", NAMES, ids=repr)
@pytest.mark.parametrize("wrap", ["plain", "safe", "lazy"])
def test_emitted_name_and_id_match_the_original_pack_input(name, wrap):
    from django.utils.functional import lazy
    from django.utils.safestring import mark_safe

    raw = {"plain": name, "safe": mark_safe(name), "lazy": lazy(lambda: name, str)()}[wrap]
    legacy = _fragment(_render(_helper(inputs=(Submit(raw, "Go"),)))).cssselect("input")[0]
    (el,) = _buttons(_render(_helper(Submit(raw, "Go"))))
    assert el.get("name") == legacy.get("name")
    assert el.get("id") == legacy.get("id")
    if len(name.split()) == 1:
        assert el.get("name") == name  # a single token is submitted literally


@pytest.mark.parametrize("order", ["underscore-first", "hyphen-first"])
@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_reserved_attributes_resolve_to_one(mode, order):
    aliases = [("data_cv_cancel_url", "/underscore/"), ("data-cv-cancel-url", "/hyphen/"), ("data_x", "u")]
    aliases.append(("data-x", "h"))
    if order == "hyphen-first":
        aliases = [aliases[1], aliases[0], aliases[3], aliases[2]]
    control = Button(
        "reset",
        "Back",
        css_id="css-id",
        css_class="c1",
        **{
            "id": "extra-id",
            "class": "c2",
            "type": "submit",
            **dict(aliases),
            "title": "extra title",
            "data_cv_tooltip": "extra",
            "aria_label": "Back to list",
            "formnovalidate": True,
            "hidden": False,
        },
    )
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        markup = _render(_helper(control))
    start = re.search(r"<button\b[^>]*>", markup).group(0)
    names = re.findall(r"""\s([\w-]+)(?==|\s|>)""", start)
    assert len(names) == len(set(names)), names
    (el,) = _buttons(markup)
    assert el.get("type") == "button"
    assert (el.get("name"), el.get("value"), el.get("id")) == ("reset", "Back", "css-id")
    assert el.get("class") == "btn btn-secondary c1 c2"
    assert el.get("data-cv-cancel-url") == "/hyphen/"
    assert el.get("data-x") == "h"
    assert el.get("aria-label") == "Back to list"
    assert el.get("formnovalidate") is not None and el.get("hidden") is None
    if mode == "icon":
        assert (el.get("title"), el.get("data-cv-tooltip")) == ("Back", "form")
    else:
        assert (el.get("title"), el.get("data-cv-tooltip")) == ("extra title", "extra")


def test_extra_id_wins_over_the_generated_id():
    (el,) = _buttons(_render(_helper(Submit("go", "Go", **{"id": "mine"}))))
    assert el.get("id") == "mine"
    assert (
        re.search(r"<button\b[^>]*>", _render(_helper(Submit("go", "Go", **{"id": "mine"})))).group(0).count(" id=")
        == 1
    )


HOSTILE = [
    '"><img src=x onerror=alert(1)>',
    "' onmouseover='alert(1)",
    "a & b < c > d",
    "&amp; &lt;b&gt; &#39;",
    "{{ request.user }}{% now 'Y' %}",
    "Ünïcode ✓ 名前",
    "",
]


@pytest.mark.parametrize("text", HOSTILE, ids=repr)
@pytest.mark.parametrize("safe", [False, True])
@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_hostile_literals_never_create_nodes_or_attributes(text, safe, mode):
    from django.utils.safestring import mark_safe

    wrap = mark_safe if safe else str
    control = Submit(
        "go",
        wrap(text),
        css_class=wrap("c"),
        title=wrap(text),
        data_note=wrap(text),
        aria_label=wrap(text),
    )
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        markup = _render(_helper(control), request=SimpleNamespace(user="LEAKED-USER"))
    doc = _fragment(markup)
    (el,) = doc.cssselect("button")
    assert not doc.cssselect("img, b, script")
    assert el.get("value") == text
    assert el.text_content() == text
    assert el.get("data-note") == text and el.get("aria-label") == text
    expected = {"type", "name", "value", "id", "class", "data-note", "aria-label"}
    if mode != "icon":
        assert el.get("title") == text  # the caller's title stays an ordinary attribute
        expected.add("title")
    elif text:
        assert el.get("title") == text  # the generated title, which drops the caller's
        expected |= {"title", "data-cv-tooltip"}
    # an empty icon-mode label renders no title and no tooltip marker, like the action leaf
    assert set(el.attrib) == expected
    assert "LEAKED-USER" not in markup


@pytest.mark.parametrize("language", ["en", "de"])
def test_lazy_text_resolves_per_render_in_the_active_language(language):
    from django.utils import translation
    from django.utils.translation import gettext, gettext_lazy

    with translation.override(language):
        expected = gettext("Save")
    assert (expected != "Save") is (language == "de")

    control = Submit("go", gettext_lazy("Save"), title=gettext_lazy("Save"), css_class=gettext_lazy("Save"))
    for active, text in (("en", "Save"), (language, expected), ("en", "Save")):
        with translation.override(active):
            (el,) = _buttons(_render(_helper(control)))
        assert (el.get("value"), el.text_content(), el.get("title")) == (text, text, text)
        assert el.get("class") == f"btn btn-primary {text}"


def test_interleaved_renders_of_one_shared_adapter_are_independent():
    shared = Submit("Search the Site", "Go", css_class="extra", data_x="1")
    state = (
        shared.name,
        shared.value,
        shared.id,
        shared.field_classes,
        str(shared.flat_attrs),
        shared.template,
        dict(shared._cv_attrs),
    )
    first = Context({"form": _EmptyForm(), "helper": _helper(shared), "input": "A"})
    second = Context({"form": _EmptyForm(), "helper": _helper(shared), "input": "B"})
    layers = ([dict(d) for d in first.dicts], [dict(d) for d in second.dicts])
    out = []
    for context, mode in ((first, "label"), (second, "icon"), (first, "label"), (second, "icon")):
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
            out.append(CRISPY.render(context))
    assert out[0] == out[2] and out[1] == out[3] and out[0] != out[1]
    (label,) = _buttons(out[0])
    (icon,) = _buttons(out[1])
    assert label.get("title") is None and icon.get("title") == "Go"
    for el in (label, icon):
        assert (el.get("name"), el.get("value"), el.get("id"), el.get("class"), el.get("data-x")) == (
            "search-the-site",
            "Go",
            "submit-id-search-the-site",
            "btn btn-primary extra",
            "1",
        )
    assert ([dict(d) for d in first.dicts], [dict(d) for d in second.dicts]) == layers
    after = (
        shared.name,
        shared.value,
        shared.id,
        shared.field_classes,
        str(shared.flat_attrs),
        shared.template,
        dict(shared._cv_attrs),
    )
    assert after == state


def test_constructor_visible_legacy_state_is_crispys():
    from crispy_forms.layout import Submit as CrispySubmit

    ours = Submit("Search the Site", "Go", css_id="cid", css_class="extra", data_x="1", formnovalidate=True)
    theirs = CrispySubmit("Search the Site", "Go", css_id="cid", css_class="extra", data_x="1", formnovalidate=True)
    assert (ours.name, ours.value, ours.id, str(ours.flat_attrs)) == (
        theirs.name,
        theirs.value,
        theirs.id,
        str(theirs.flat_attrs),
    )
    assert ours.field_classes == "btn btn-primary extra"
    assert ours.template == "crud_views/tags/button/form.html"
    assert Submit("go", "Go", template="x.html").template == "x.html"
