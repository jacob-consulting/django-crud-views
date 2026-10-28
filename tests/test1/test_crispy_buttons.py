"""Crispy form buttons read the layered button class table and render through the form-button leaf (Phase 6)."""

import copy
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
    """The stock filter actions are layout leaf buttons (06-05) with their table classes and original ids."""
    html = client_user_publisher_view.get(url(cv_publisher, "list")).content.decode()
    apply_ = button(html, id="filter-button")
    assert 'class="btn btn-primary"' in apply_ and 'type="submit"' in apply_
    reset = button(html, id="filter-button-reset")
    assert 'class="btn btn-secondary"' in reset
    assert 'type="reset"' in reset
    assert "btn-inverse" not in html
    assert not re.search(r"<input\b[^>]*\bid=\"filter-button", html)


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
    assert [s.text for s in el.cssselect("span")] == ["Save"]
    assert el.get("value") == "Save"
    # the submit kind's semantic icon (save) in "both" and "icon" modes, none in "label"
    assert [i.get("class") for i in el.cssselect("i")] == ([] if mode == "label" else ["fa-regular fa-floppy-disk"])
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
    # the label span; "both" and "icon" put the kind's icon element in front of it
    assert el.cssselect("span")[0].text_content() == text
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


# --- ownership (D-09 to D-12, 06-03): which view's form map a crispy form button uses ----------------------------
#
# Each owner gets a distinct (submit, cancel) mode signature, so the rendered classes name the owner that won.

FORM_KINDS = ("submit", "cancel", "delete", "filter-submit", "filter-reset")
MODE_CLASSES = {f"form:{k}:{m}": f"m-{m}" for k in FORM_KINDS for m in ("label", "icon", "both")}

SIGNATURES = {
    "R": ("icon", "icon"),  # row / current form
    "RH": ("both", "both"),  # current helper
    "P": ("icon", "both"),  # page
    "H": ("both", "icon"),  # enclosing helper
    "OF": ("icon", "label"),  # outer form
}
S = ("label", "icon")  # the settings singleton's map: no owner, or an ordinary owner

_ABSENT = object()


class _Falsey:
    """A real, ordinary owner that is falsey."""

    def __bool__(self):
        return False

    def __len__(self):
        return 0


@pytest.fixture
def owners(monkeypatch, settings):
    """Five CrudView owners with distinct form maps, the settings map S, and classes that name the mode."""
    from crud_views.lib.settings import crud_views_settings
    from tests.test1.app.views import (
        AuthorCreateView,
        AuthorDeleteView,
        AuthorDetailView,
        AuthorListView,
        AuthorUpdateView,
        cv_author,
    )

    settings.CRUD_VIEWS_BUTTON_CLASSES = MODE_CLASSES
    monkeypatch.setattr(cv_author, "form_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submit": S[0], "cancel": S[1]})
    classes = {
        "R": AuthorCreateView,
        "RH": AuthorUpdateView,
        "P": AuthorDeleteView,
        "H": AuthorDetailView,
        "OF": AuthorListView,
    }
    for name, cls in classes.items():
        submit, cancel = SIGNATURES[name]
        monkeypatch.setattr(cls, "cv_form_actions_label_mode", {"submit": submit, "cancel": cancel})
    return SimpleNamespace(**classes)


def _owned_form(cv_view=_ABSENT) -> forms.Form:
    form = _EmptyForm()
    if cv_view is not _ABSENT:
        form.cv_view = cv_view
    return form


def _controls(tag: str):
    """Two FormActions groups and a later control, all named after ``tag``."""
    return (
        FormActions(Submit(f"{tag}-s1", "S"), Button(f"{tag}-c1", "C")),
        FormActions(Submit(f"{tag}-s2", "S"), Button(f"{tag}-c2", "C")),
        Submit(f"{tag}-s3", "S"),
    )


def _owner_helper(*fields, view=_ABSENT) -> FormHelper:
    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(*fields)
    if view is not _ABSENT:
        helper.view = view
    return helper


def _modes(markup: str) -> dict[str, tuple[str, str]]:
    """tag -> the (submit, cancel) mode signature of its controls; all controls of a tag must agree."""
    seen: dict[str, set] = {}
    for el in _buttons(markup):
        tag, _, which = el.get("name").rpartition("-")
        seen.setdefault(tag, set()).add((which[0], el.get("class").removeprefix("m-")))
    result = {}
    for tag, pairs in seen.items():
        submit = {m for w, m in pairs if w == "s"}
        cancel = {m for w, m in pairs if w == "c"}
        assert len(submit) == 1 and len(cancel) == 1, (tag, pairs)
        result[tag] = (submit.pop(), cancel.pop())
    return result


def _crispy_owned(form, helper, **page) -> str:
    context = Context({"form": form, "helper": helper, **page})
    before = [dict(d) for d in context.dicts]
    out = CRISPY.render(context)
    assert [dict(d) for d in context.dicts] == before
    return out


def _resolve_owner(owners, value):
    """A named test owner; ordinary, falsey and string owners are real objects, never a CrudView."""
    from django.views.generic import View

    special = {"ordinary": View, "falsey": _Falsey, "string": lambda: "PAGE"}
    return special[value]() if value in special else getattr(owners, value)


def _sig(name):
    return SIGNATURES.get(name, S)


@pytest.mark.parametrize(
    ("form_owner", "helper_owner", "page_owner", "winner"),
    [
        ("R", "RH", "P", "R"),
        (_ABSENT, "RH", "P", "RH"),
        (None, "RH", "P", "RH"),
        (_ABSENT, _ABSENT, "P", "P"),
        (None, None, "P", "P"),  # a helper view=None overlay never hides the page
        (_ABSENT, None, _ABSENT, "S"),
        (None, None, None, "S"),
        ("R", None, None, "R"),
        (_ABSENT, "RH", None, "RH"),
        # an explicit ordinary owner stops the lookup: settings, never a lower CrudView
        ("ordinary", "RH", "P", "S"),
        ("falsey", "RH", "P", "S"),
        (None, "ordinary", "P", "S"),
        (_ABSENT, "falsey", "P", "S"),
        (None, None, "ordinary", "S"),
        (None, None, "falsey", "S"),
        ("string", "RH", "P", "S"),
    ],
)
def test_owner_priority(owners, form_owner, helper_owner, page_owner, winner):
    def resolve(value):
        if value is _ABSENT or value is None:
            return value
        return _resolve_owner(owners, value)

    page = {} if page_owner is _ABSENT else {"view": resolve(page_owner)}
    helper = _owner_helper(*_controls("x"), view=resolve(helper_owner))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        markup = _crispy_owned(_owned_form(resolve(form_owner)), helper, **page)
    assert _modes(markup) == {"x": _sig(winner)}


def test_crud_view_instances_own_like_their_class(owners):
    helper = _owner_helper(*_controls("x"), view=None)
    assert _modes(_crispy_owned(_owned_form(owners.R()), helper, view=owners.P())) == {"x": SIGNATURES["R"]}
    assert _modes(_crispy_owned(_owned_form(), helper, view=owners.P())) == {"x": SIGNATURES["P"]}


def test_page_owner_survives_nested_context_pushes(owners):
    helper = _owner_helper(*_controls("x"), view=None)
    context = Context({"view": owners.P})
    context.push({"unrelated": 1})
    context.push({"view": None})  # page-level None above the page owner: not an owner
    context.push({"form": _owned_form(), "helper": helper})
    before = [dict(d) for d in context.dicts]
    assert _modes(CRISPY.render(context)) == {"x": SIGNATURES["P"]}
    # a nearer genuine page owner wins over a lower one
    context.push({"view": owners.H})
    assert _modes(CRISPY.render(context)) == {"x": SIGNATURES["H"]}
    context.pop()
    assert [dict(d) for d in context.dicts] == before


NESTED = Template("{% load crispy_forms_tags %}{% crispy inner_form inner_helper %}")


def test_enclosing_helper_overlays_are_never_page_layers(owners):
    from crispy_forms.layout import HTML

    inner = "{% load crispy_forms_tags %}{% crispy inner_form inner_helper %}"
    middle = "{% load crispy_forms_tags %}{% crispy middle_form middle_helper %}"
    # page P, outer helper H, a middle helper (stacked enclosing overlays) and the current helper view=None
    outer_helper = _owner_helper(*_controls("outer"), HTML(middle), *_controls("outer2"), view=owners.H)
    middle_helper = _owner_helper(*_controls("mid"), HTML(inner), view=owners.OF)
    inner_helper = _owner_helper(*_controls("in"), view=None)
    page = {
        "middle_form": _owned_form(),
        "middle_helper": middle_helper,
        "inner_form": _owned_form(None),
        "inner_helper": inner_helper,
    }
    modes = _modes(_crispy_owned(_owned_form(), outer_helper, view=owners.P, **page))
    assert modes == {
        "outer": SIGNATURES["H"],
        "outer2": SIGNATURES["H"],
        "mid": SIGNATURES["OF"],
        "in": SIGNATURES["P"],  # P, never an enclosing helper owner
    }
    # with no page owner: the settings map, never H or the middle helper
    for page_view in ({"view": None}, {}):
        modes = _modes(_crispy_owned(_owned_form(), outer_helper, **page_view, **page))
        assert modes["in"] == S
    # explicit current owners still win over P
    page["inner_form"] = _owned_form(owners.R)
    assert _modes(_crispy_owned(_owned_form(), outer_helper, view=owners.P, **page))["in"] == SIGNATURES["R"]
    page["inner_form"] = _owned_form()
    inner_helper.view = owners.RH
    assert _modes(_crispy_owned(_owned_form(), outer_helper, view=owners.P, **page))["in"] == SIGNATURES["RH"]


def test_explicit_tag_helper_is_respected_and_form_helper_never_read(owners):
    class NoHelperForm(forms.Form):
        @property
        def helper(self):
            raise AssertionError("form.helper must not be read")

    helper = _owner_helper(*_controls("x"), view=owners.RH)
    assert _modes(_crispy_owned(NoHelperForm(), helper, view=owners.P)) == {"x": SIGNATURES["RH"]}


def test_private_helper_owner_entry_wins_for_its_invocation_only(owners):
    from crud_views.lib.crispy.buttons import _CV_HELPER_OWNER

    class PushingHelper(FormHelper):
        def render_layout(self, form, context, template_pack=None, **kwargs):
            context.push({_CV_HELPER_OWNER: self._owner})
            try:
                return super().render_layout(form, context, **kwargs)
            finally:
                context.pop()

    helper = PushingHelper()
    helper.form_tag = False
    helper.layout = Layout(*_controls("x"))
    helper.view = owners.H  # published in the overlay; the private entry is nearer
    helper._owner = owners.RH
    assert _modes(_crispy_owned(_owned_form(), helper, view=owners.P)) == {"x": SIGNATURES["RH"]}
    helper._owner = None
    assert _modes(_crispy_owned(_owned_form(), helper, view=owners.P)) == {"x": SIGNATURES["P"]}


def test_interleaved_owners_do_not_leak(owners):
    shared = _owner_helper(*_controls("x"), view=None)
    first = Context({"form": _owned_form(owners.R), "helper": shared, "view": owners.P})
    second = Context({"form": _owned_form(), "helper": shared})
    layers = ([dict(d) for d in first.dicts], [dict(d) for d in second.dicts])
    out = [CRISPY.render(c) for c in (first, second, first, second)]
    assert [_modes(o) for o in out] == [{"x": SIGNATURES["R"]}, {"x": S}] * 2
    assert ([dict(d) for d in first.dicts], [dict(d) for d in second.dicts]) == layers
    assert not hasattr(shared, "_cv_owner")


# the production formset path: Layout(Formsets()) -> formsets.html -> cv_x_formset -> formset.html -> row crispy


def _xform(form, helper, *children, prefix="row"):
    return SimpleNamespace(form=form, helper=helper, formsets=list(children), prefix=prefix, json_data="{}")


def _xformset(*rows, prefix="fs"):
    return SimpleNamespace(
        render_rows_only=True, end_at_rows=True, prefix=prefix, forms=list(rows), cv_toggle_field=None
    )


def _row(owners, tag, form_owner=_ABSENT, helper_owner=_ABSENT, *children):
    return _xform(_owned_form(form_owner), _owner_helper(*_controls(tag), view=helper_owner), *children, prefix=tag)


def _render_formsets(owners, *x_formsets, outer_form=_ABSENT, outer_helper=_ABSENT, **page) -> str:
    from crud_views.lib.formsets import Formsets

    helper = _owner_helper(Formsets(), *_controls("outer"), view=outer_helper)
    return _crispy_owned(_owned_form(outer_form), helper, formsets=SimpleNamespace(x_formsets=list(x_formsets)), **page)


@pytest.mark.parametrize(
    ("form_owner", "helper_owner", "winner"),
    [
        ("R", "RH", "R"),
        ("R", None, "R"),
        (_ABSENT, "RH", "RH"),
        (None, "RH", "RH"),
        (_ABSENT, _ABSENT, "P"),
        (None, None, "P"),  # the page survives flatten and the inclusion context.new, never H or OF
        ("ordinary", "RH", "S"),
        (None, "falsey", "S"),
    ],
)
def test_formset_rows_use_the_row_form_then_row_helper_then_page(owners, form_owner, helper_owner, winner):
    def resolve(value):
        if value is _ABSENT or value is None:
            return value
        return _resolve_owner(owners, value)

    row = _row(owners, "row", resolve(form_owner), resolve(helper_owner))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        markup = _render_formsets(owners, _xformset(row), outer_form=owners.OF, outer_helper=owners.H, view=owners.P)
    assert _modes(markup) == {"row": _sig(winner), "outer": SIGNATURES["OF"]}


@pytest.mark.parametrize(
    ("page", "expected"),
    [({"view": None}, "S"), ({}, "S"), ({"view": "ordinary"}, "S"), ({"view": "falsey"}, "S"), ({"view": "P"}, "P")],
    ids=["none", "absent", "ordinary", "falsey", "page"],
)
def test_formset_page_tier_is_transported_exactly(owners, page, expected):
    if "view" in page and isinstance(page["view"], str):
        page = {"view": _resolve_owner(owners, page["view"])}
    row = _row(owners, "row", None, None)
    child = _xformset(_row(owners, "child", _ABSENT, None), prefix="child-fs")
    parent = _row(owners, "parent", _ABSENT, _ABSENT, child)
    markup = _render_formsets(owners, _xformset(row, parent), outer_helper=owners.H, **page)
    sig = _sig(expected)
    # the recursive child inclusion propagates the same page fallback; the outer helper owns its own controls
    assert _modes(markup) == {"row": sig, "parent": sig, "child": sig, "outer": SIGNATURES["H"]}


def test_formset_child_rows_keep_their_own_owners(owners):
    child = _xformset(_row(owners, "child", owners.R, owners.H), _row(owners, "child2", None, owners.RH))
    parent = _row(owners, "parent", owners.OF, _ABSENT, child)
    markup = _render_formsets(owners, _xformset(parent), outer_helper=owners.H, view=owners.P)
    modes = _modes(markup)
    assert (modes["parent"], modes["child"], modes["child2"]) == (
        SIGNATURES["OF"],
        SIGNATURES["R"],
        SIGNATURES["RH"],
    )


def test_two_formset_pages_are_independent(owners):
    first = _xformset(_row(owners, "row", None, None))
    second = _xformset(_row(owners, "row", None, None))
    a = _render_formsets(owners, first, outer_helper=owners.H, view=owners.P)
    b = _render_formsets(owners, second, outer_helper=owners.H, view=owners.R)
    again = _render_formsets(owners, first, outer_helper=owners.H, view=owners.P)
    assert _modes(a)["row"] == _modes(again)["row"] == SIGNATURES["P"]
    assert _modes(b)["row"] == SIGNATURES["R"]


def test_standalone_cv_x_formset_derives_the_page_tier(owners):
    standalone = Template("{% load crud_views_formsets %}{% cv_x_formset xfs %}")
    xfs = _xformset(_row(owners, "row", None, None), _row(owners, "row2", _ABSENT, owners.RH))
    context = Context({"view": owners.P, "xfs": xfs})
    before = [dict(d) for d in context.dicts]
    assert _modes(standalone.render(context)) == {"row": SIGNATURES["P"], "row2": SIGNATURES["RH"]}
    assert [dict(d) for d in context.dicts] == before
    assert _modes(standalone.render(Context({"xfs": xfs}))) == {"row": S, "row2": SIGNATURES["RH"]}


def test_formset_render_failure_leaves_the_caller_context_unchanged(owners):
    from crud_views.lib.formsets import Formsets

    bad = _xformset(_xform(_owned_form(), _owner_helper(Submit("bad-s", "S", slot="formset:control"))))
    helper = _owner_helper(Formsets(), view=owners.H)
    context = Context({"form": _owned_form(), "helper": helper, "view": owners.P, "formsets": None})
    context.push({"formsets": SimpleNamespace(x_formsets=[bad])})
    before = [dict(d) for d in context.dicts]
    with pytest.raises(ValueError, match="slot"):
        CRISPY.render(context)
    assert [dict(d) for d in context.dicts] == before
    context["formsets"] = SimpleNamespace(x_formsets=[_xformset(_row(owners, "row", None, None))])
    assert _modes(CRISPY.render(context))["row"] == SIGNATURES["P"]


def test_formset_transport_key_is_private(owners):
    from crud_views.lib.crispy.buttons import _CV_PAGE_OWNER

    assert _CV_PAGE_OWNER.startswith("_") and not _CV_PAGE_OWNER.startswith("cv_")
    markup = _render_formsets(owners, _xformset(_row(owners, "row", None, None)), view=owners.P)
    assert _CV_PAGE_OWNER not in markup


def test_overlay_classification_on_stacked_invocations(owners):
    """Every {% crispy %} invocation leaves exactly one response overlay; page layers and FormActions are not."""
    from crispy_forms.layout import HTML

    from crud_views.lib.crispy.buttons import _cv_helper_tier, _cv_page_tier, _is_response_overlay

    seen = []

    class Spy(Submit):
        def render(self, form, context, *args, **kwargs):
            seen.append((list(context.dicts), _cv_helper_tier(context), _cv_page_tier(context)))
            return super().render(form, context, *args, **kwargs)

    inner = "{% load crispy_forms_tags %}{% crispy inner_form inner_helper %}"
    outer_helper = _owner_helper(FormActions(Spy("o-s", "S")), HTML(inner), view=owners.H)
    inner_helper = _owner_helper(FormActions(Spy("i-s1", "S")), FormActions(Spy("i-s2", "S")), Spy("i-s3", "S"))
    inner_helper.view = None
    _crispy_owned(_owned_form(), outer_helper, view=owners.P, inner_form=_owned_form(), inner_helper=inner_helper)
    overlays = [sum(map(_is_response_overlay, dicts)) for dicts, _, _ in seen]
    assert overlays == [1, 2, 2, 2]
    assert [(helper, page) for _, helper, page in seen] == [(owners.H, owners.P)] + [(None, owners.P)] * 3
    # the trailing control sits under more leftover FormActions layers than the first, still the same overlay
    assert len(seen[3][0]) > len(seen[1][0])
    for dicts, _, _ in seen:
        page_layers = [d for d in dicts if "view" in d and not _is_response_overlay(d)]
        assert [d["view"] for d in page_layers] == [owners.P]


def test_transported_page_owner_is_authoritative_even_when_none(owners):
    from crud_views.lib.crispy.buttons import _CV_PAGE_OWNER, _cv_page_tier

    context = Context({"view": owners.P})
    assert _cv_page_tier(context) is owners.P
    context.push({_CV_PAGE_OWNER: None})
    assert _cv_page_tier(context) is None  # an explicit transported None: no page owner, not the lower view
    context.push({_CV_PAGE_OWNER: owners.R})
    context.push({"view": owners.H})
    assert _cv_page_tier(context) is owners.R


# --- semantic icons (D-16, 06-04): kind defaults from the slot, the icon= keyword, per-form icons -----------------

# kind -> (adapter, slot keyword, Font Awesome classes of the kind's default icon)
KIND_ICONS = {
    "submit": (Submit, {}, "fa-regular fa-floppy-disk"),
    "delete": (Submit, {"slot": "form:delete"}, "fa-regular fa-trash-can"),
    "cancel": (Button, {}, "fa-solid fa-xmark"),
    "filter-submit": (Submit, {"slot": "form:filter-submit"}, "fa-solid fa-filter"),
    "filter-reset": (Reset, {}, "fa-solid fa-rotate-left"),
}
WORKFLOW_ICON = "fa-solid fa-diagram-project"


def _icon_classes(el) -> list[str]:
    """The classes of each inline icon element of a rendered button."""
    return [i.get("class") for i in el.cssselect("i")]


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
@pytest.mark.parametrize("kind", sorted(KIND_ICONS))
def test_kind_default_icons(kind, mode):
    adapter, slot, fa = KIND_ICONS[kind]
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        (el,) = _buttons(_render(_helper(adapter("go", "Go", **slot))))
    assert _icon_classes(el) == ([] if mode == "label" else [fa])
    assert el.get("icon") is None
    assert [s.text for s in el.cssselect("span")] == ["Go"]


@pytest.mark.parametrize(
    "control,fa",
    [
        (Button("submit", "Back"), "fa-solid fa-xmark"),
        (Reset("reset", "Clear"), "fa-solid fa-rotate-left"),
        (Button("reset", "Back"), "fa-solid fa-xmark"),
        (Submit("reset", "Remove", slot="form:delete"), "fa-regular fa-trash-can"),
        (Submit("delete", "Go", slot="form:submit"), "fa-regular fa-floppy-disk"),
        (Submit("reset", "Search", slot="form:filter-submit"), "fa-solid fa-filter"),
    ],
    ids=["cancel-named-submit", "reset", "cancel-named-reset", "delete-named-reset", "submit-named-delete", "filter"],
)
def test_kind_icon_follows_the_slot_not_the_name(control, fa):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
        (el,) = _buttons(_render(_helper(control)))
    assert _icon_classes(el) == [fa]


@pytest.mark.parametrize("mode", ["both", "icon"])
def test_explicit_icon_keyword(mode):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        (rocket,) = _buttons(_render(_helper(Submit("go", "Go", icon="fas:rocket"))))
        (named,) = _buttons(_render(_helper(Button("go", "Go", icon="workflow"))))
    assert _icon_classes(rocket) == ["fa-solid fa-rocket"]
    assert _icon_classes(named) == [WORKFLOW_ICON]
    assert rocket.get("icon") is None and named.get("icon") is None


@pytest.mark.parametrize("value", [None, ""])
@pytest.mark.parametrize("kind", sorted(KIND_ICONS))
def test_explicit_none_or_empty_icon_suppresses_the_kind_default(kind, value):
    from crud_views.lib.view import button_data

    adapter, slot, _ = KIND_ICONS[kind]
    control = adapter("go", "Go", icon=value, **slot)
    seen = []
    real = button_data.cv_button_data

    def spy(ctx, location, kind="action"):
        seen.append(ctx.get("cv_icon"))
        return real(ctx, location, kind)

    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
        original = button_data.cv_button_data
        button_data.cv_button_data = spy
        try:
            (el,) = _buttons(_render(_helper(control)))
        finally:
            button_data.cv_button_data = original
    # the intentional "no icon" reaches the normalizer (and so the missing-icon policy), never the kind default
    assert seen == [value]
    assert _icon_classes(el) == []
    assert el.text_content() == "Go"


def test_icon_keyword_is_configuration_not_an_attribute():
    ours = Submit("go", "Go", icon="fas:rocket", data_x="1")
    theirs_attrs = str(ours.flat_attrs)
    assert "icon" not in theirs_attrs and 'data-x="1"' in theirs_attrs
    # a legacy helper input keeps its extra attributes and never serializes icon=
    markup = _render(_helper(inputs=[Submit("go", "Go", icon="fas:rocket", data_x="1")]))
    (el,) = _fragment(markup).cssselect("input[name=go]")
    assert el.get("data-x") == "1"
    assert el.get("icon") is None
    assert "rocket" not in markup


def test_interleaved_icons_of_shared_adapters_do_not_leak():
    rocket = Submit("go", "Go", icon="fas:rocket")
    plain = Submit("go", "Go")
    seen = []
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
        for control in (rocket, plain, rocket, plain):
            (el,) = _buttons(_render(_helper(control)))
            seen.append(_icon_classes(el))
    assert seen == [["fa-solid fa-rocket"], ["fa-regular fa-floppy-disk"]] * 2


# package forms on real endpoints


def _page_buttons(client, path, *names, mode=None) -> dict:
    from django.utils import translation

    floor = {"CRUD_VIEWS_LABEL_MODE_DEFAULTS": {"form": mode}} if mode else {}
    with override_settings(**floor), translation.override("en"):
        response = client.get(path)
    assert response.status_code == 200
    doc = lxml_html.fromstring(response.content.decode())
    return {name: doc.cssselect(f'button[name="{name}"]')[0] for name in names}


def _author_pages(author):
    return {
        "create": ("/author/create/", "submit", "Create", "fa-regular fa-floppy-disk"),
        "update": (f"/author/{author.pk}/update/", "submit", "Create", "fa-regular fa-floppy-disk"),
        "delete": (f"/author/{author.pk}/delete/", "delete", "Delete", "fa-regular fa-trash-can"),
    }


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["both", "icon"])
@pytest.mark.parametrize("page", ["create", "update", "delete"])
def test_package_forms_render_their_semantic_icons(request, page, mode, author_douglas_adams):
    permission = {"create": "add", "update": "change", "delete": "delete"}[page]
    client = request.getfixturevalue(f"client_user_author_{permission}")
    path, name, value, fa = _author_pages(author_douglas_adams)[page]
    buttons = _page_buttons(client, path, name, "reset", mode=mode)
    action, cancel = buttons[name], buttons["reset"]
    assert _icon_classes(action) == [fa]
    assert _icon_classes(cancel) == ["fa-solid fa-xmark"]
    # unchanged payload: name, value, id, type and the cancel URL
    assert (action.get("name"), action.get("value"), action.get("type")) == (name, value, "submit")
    assert (cancel.get("value"), cancel.get("type"), cancel.get("data-cv-cancel-url")) == (
        "Cancel",
        "button",
        "/author/",
    )
    for el, text in ((action, value), (cancel, "Cancel")):
        hidden = [s.text for s in el.cssselect("span.visually-hidden")]
        if mode == "icon":
            assert hidden == [text]
            assert (el.get("title"), el.get("data-cv-tooltip")) == (text, "form")
        else:
            assert not hidden and [s.text for s in el.cssselect("span")] == [text]
            assert el.get("title") is None and el.get("data-cv-tooltip") is None


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["both", "icon"])
def test_workflow_form_uses_the_workflow_icon(mode, client_user_campaign_change, campaign_new):
    buttons = _page_buttons(
        client_user_campaign_change, f"/campaign/{campaign_new.pk}/workflow/", "submit", "reset", mode=mode
    )
    assert _icon_classes(buttons["submit"]) == [WORKFLOW_ICON]
    assert _icon_classes(buttons["reset"]) == ["fa-solid fa-xmark"]
    assert buttons["submit"].get("value") == "Process Workflow Step"


# page -> (logged-in client fixture, path); the client fixtures share one Client, so one page per test
ICON_PAGES = {
    "create": ("client_user_author_add", "/author/create/"),
    "workflow": ("client_user_campaign_change", "/campaign/{pk}/workflow/"),
}


def _icon_page(request, page):
    client, path = ICON_PAGES[page]
    pk = request.getfixturevalue("campaign_new").pk if page == "workflow" else None
    return request.getfixturevalue(client), path.format(pk=pk)


@pytest.mark.django_db
@pytest.mark.parametrize("page", sorted(ICON_PAGES))
def test_label_floor_keeps_package_forms_icon_free(request, page):
    for el in _page_buttons(*_icon_page(request, page), "submit", "reset").values():
        assert not el.cssselect("i, svg, span.visually-hidden")


def test_form_icon_defaults():
    from crud_views.lib.crispy.form import CrispyFormMixin
    from crud_views_workflow.lib.forms import WorkflowForm

    assert CrispyFormMixin.submit_icon == "save"
    assert CrispyDeleteForm.delete_icon == "delete"
    assert WorkflowForm.submit_icon == "workflow"


@pytest.mark.django_db
@pytest.mark.parametrize("page", sorted(ICON_PAGES))
def test_per_form_submit_icon_wins(request, page, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm, CampaignWorkflowForm, CampaignWorkflowView

    class RocketForm(AuthorForm):
        submit_icon = "fas:rocket"

    class RocketWorkflowForm(CampaignWorkflowForm):
        submit_icon = "fas:rocket"

    monkeypatch.setattr(AuthorCreateView, "form_class", RocketForm)
    monkeypatch.setattr(CampaignWorkflowView, "form_class", RocketWorkflowForm)
    buttons = _page_buttons(*_icon_page(request, page), "submit", "reset", mode="both")
    assert _icon_classes(buttons["submit"]) == ["fa-solid fa-rocket"]
    assert _icon_classes(buttons["reset"]) == ["fa-solid fa-xmark"]


@pytest.mark.django_db
def test_hook_kwargs_win_over_the_form_icon(client_user_author_add, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm

    class HookForm(AuthorForm):
        submit_icon = "fas:rocket"

        def get_submit_button_kwargs(self) -> dict:
            return {**super().get_submit_button_kwargs(), "icon": "fas:bolt"}

        def get_cancel_button_kwargs(self) -> dict:
            return {**super().get_cancel_button_kwargs(), "icon": None}

    monkeypatch.setattr(AuthorCreateView, "form_class", HookForm)
    buttons = _page_buttons(client_user_author_add, "/author/create/", "submit", "reset", mode="both")
    assert _icon_classes(buttons["submit"]) == ["fa-solid fa-bolt"]
    assert _icon_classes(buttons["reset"]) == []


@pytest.mark.django_db
def test_explicit_none_submit_icon_is_no_icon(client_user_author_add, monkeypatch):
    from tests.test1.app.views import AuthorCreateView, AuthorForm

    class NoIconForm(AuthorForm):
        submit_icon = None

    monkeypatch.setattr(AuthorCreateView, "form_class", NoIconForm)
    buttons = _page_buttons(client_user_author_add, "/author/create/", "submit", "reset", mode="both")
    assert _icon_classes(buttons["submit"]) == []
    assert buttons["submit"].text_content() == "Create"
    assert _icon_classes(buttons["reset"]) == ["fa-solid fa-xmark"]


@pytest.mark.django_db
def test_delete_form_icon_and_slot_hooks(client_user_author_delete, author_douglas_adams, monkeypatch):
    from tests.test1.app.views import AuthorDeleteView

    path = f"/author/{author_douglas_adams.pk}/delete/"

    class SubmitIconForm(CrispyDeleteForm):
        submit_icon = "fas:rocket"  # inherited, never used by the delete button

    class DeleteIconForm(CrispyDeleteForm):
        delete_icon = "fas:bomb"

    class CancelSlotForm(CrispyDeleteForm):
        def get_delete_button_kwargs(self) -> dict:
            return {**super().get_delete_button_kwargs(), "slot": "form:cancel"}

    expected = {SubmitIconForm: "fa-regular fa-trash-can", DeleteIconForm: "fa-solid fa-bomb"}
    for form_class, fa in expected.items():
        monkeypatch.setattr(AuthorDeleteView, "form_class", form_class)
        buttons = _page_buttons(client_user_author_delete, path, "delete", mode="both")
        assert _icon_classes(buttons["delete"]) == [fa]

    # a delete payload in the cancel slot: cancel styling and kind, its own name / value / type, the form's icon
    monkeypatch.setattr(AuthorDeleteView, "form_class", CancelSlotForm)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel:both": "x-cancel"}):
        delete = _page_buttons(client_user_author_delete, path, "delete", mode="both")["delete"]
    assert (delete.get("name"), delete.get("value"), delete.get("type"), delete.get("class")) == (
        "delete",
        "Delete",
        "submit",
        "x-cancel",
    )
    assert delete.get("data-cv-cancel-url") is None
    assert _icon_classes(delete) == ["fa-regular fa-trash-can"]


class _CancelOwner:
    """A minimal non-CrudView owner: the cancel hook needs a request and a cancel button context."""

    request = SimpleNamespace(user=None)

    def get_cancel_button_context(self, obj, user, request):
        from django.utils.translation import gettext_lazy

        return {"cv_url": "/back/", "cv_action_label": gettext_lazy("Cancel")}


def test_form_instances_do_not_share_icons_or_language():
    from django.utils import translation
    from django.utils.translation import gettext, gettext_lazy

    from crud_views.lib.crispy import CrispyForm

    class PlainForm(CrispyForm):
        submit_label = gettext_lazy("Save")

        def get_layout_fields(self):
            return []

    class RocketForm(PlainForm):
        submit_icon = "fas:rocket"

    template = Template("{% load crispy_forms_tags %}{% crispy form %}")
    seen = []
    instance = PlainForm(cv_view=_CancelOwner())
    instance.submit_icon = "fas:bolt"  # an instance override stays on that instance
    forms_in_order = (
        (RocketForm, "en"),
        (PlainForm, "de"),
        (RocketForm, "de"),
        (PlainForm, "en"),
        (instance, "de"),
        (PlainForm, "de"),
    )
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        for form, language in forms_in_order:
            form = form(cv_view=_CancelOwner()) if isinstance(form, type) else form
            with translation.override(language):
                markup = template.render(Context({"form": form}))
                expected = (gettext("Save"), gettext("Cancel"))
            submit, cancel = _buttons(markup)
            seen.append((_icon_classes(submit), _icon_classes(cancel)))
            assert (submit.get("title"), cancel.get("title")) == expected
    rocket, floppy, bolt, xmark = (
        ["fa-solid fa-rocket"],
        ["fa-regular fa-floppy-disk"],
        ["fa-solid fa-bolt"],
        ["fa-solid fa-xmark"],
    )
    assert seen == [(rocket, xmark), (floppy, xmark), (rocket, xmark), (floppy, xmark), (bolt, xmark), (floppy, xmark)]
    assert PlainForm.submit_icon == "save" and RocketForm.submit_icon == "fas:rocket"


# --- the filter helper lifecycle (06-05): real {% crispy form helper %} renders ----------------------------------

FILTER_CRISPY = Template("{% load crispy_forms_tags %}{% crispy form helper %}")


class _CityForm(forms.Form):
    name = forms.CharField(required=False)
    city = forms.CharField(required=False)


def _filter_helper_class(*, layout=_ABSENT, actions=_ABSENT):
    """A ListViewFilterFormHelper subclass: class-level ``layout`` and/or a ``get_form_actions`` returning ``actions``
    (a fresh object per call when given a factory)."""
    from crud_views.lib.views.list import ListViewFilterFormHelper

    attrs = {}
    if layout is not _ABSENT:
        attrs["layout"] = layout
    if actions is not _ABSENT:
        attrs["get_form_actions"] = lambda self: actions() if callable(actions) else actions
    return type("FilterHelper", (ListViewFilterFormHelper,), attrs)


def _new_filter_helper(cls, query="", **kwargs):
    from django.test import RequestFactory

    return cls(view=kwargs.pop("view", None), request=RequestFactory().get("/" + query), **kwargs)


def _filter_render(form, helper, **page) -> str:
    return FILTER_CRISPY.render(Context({"form": form, "helper": helper, **page}))


def _controls_of(markup: str) -> list[tuple]:
    """(tag, type, name, value) of every input / button in document order."""
    root = lxml_html.fragment_fromstring(markup, create_parent="div")
    return [(el.tag, el.get("type"), el.get("name"), el.get("value")) for el in root.iter("input", "button")]


def _action_groups(markup: str) -> list:
    """The FormActions groups: div.mb-3 > div[class=""] without hidden inputs (the pack's inputs wrapper has them)."""
    root = lxml_html.fragment_fromstring(markup, create_parent="div")
    return [
        div
        for div in root.iter("div")
        if (div.get("class") or "").split() == ["mb-3"]
        and div.get("id") is None
        and not div.cssselect("input[type=hidden]")
        and [child.get("class") for child in div] == [""]
    ]


DEFAULT_ACTIONS = [("button", "submit", "submit", "Apply Filter"), ("button", "reset", "reset", "Reset Filter")]
HIDDEN_SORT = [("input", "hidden", "sort", "")]
FIELD = {"name": ("input", "text", "name", None), "city": ("input", "text", "city", None)}


def _fields(*names) -> list[tuple]:
    return [FIELD[name] for name in names]


def _layout_fields(layout) -> list:
    return [getattr(field, "fields", field) for field in layout.fields]


def test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once():
    """D-03: the documented field-only subclass; two instances, explicit form=, repeated and interleaved renders."""
    helper_cls = _filter_helper_class(layout=Layout("name", "city"))
    class_layout = helper_cls.layout
    form = _CityForm()
    first = _new_filter_helper(helper_cls)
    second = _new_filter_helper(helper_cls, form=form)
    assert second.form is form
    assert first.layout is not class_layout and second.layout is not class_layout
    assert first.layout is not second.layout

    expected = _fields("name", "city") + DEFAULT_ACTIONS + HIDDEN_SORT
    for _ in range(3):
        for helper in (first, second, first):
            out = _filter_render(_CityForm(), helper)
            assert _controls_of(out) == expected
            assert len(_action_groups(out)) == 1
    # the class layout and the other instance never receive the appended actions
    assert class_layout.fields == ["name", "city"]
    assert first.layout.fields[:2] == second.layout.fields[:2] == ["name", "city"]
    assert len(first.layout.fields) == len(second.layout.fields) == 3
    assert first.layout.fields[2] is not second.layout.fields[2]
    assert second.form is form


def test_filter_explicit_form_never_overwrites_the_declared_layout():
    """crispy's FormHelper(form) would replace the layout with every form field; the declared fields stay."""
    form = _CityForm()
    helper = _new_filter_helper(_filter_helper_class(layout=Layout("city")), form=form)
    assert helper.form is form
    assert _controls_of(_filter_render(form, helper)) == _fields("city") + DEFAULT_ACTIONS + HIDDEN_SORT
    assert helper.form is form


@pytest.mark.parametrize("names", [(), ("name",), ("name", "city", "zip")])
def test_filter_helper_without_layout_renders_the_actual_form_fields(names):
    form_cls = type("NForm", (forms.Form,), {name: forms.CharField(required=False) for name in names})
    helper = _new_filter_helper(_filter_helper_class())
    for form in (form_cls(), form_cls()):
        out = _filter_render(form, helper)
        fields = [("input", "text", name, None) for name in names]
        assert _controls_of(out) == fields + DEFAULT_ACTIONS + HIDDEN_SORT
        assert len(_action_groups(out)) == 1
    # another form through the same helper renders its own fields, not the first form's
    out = _filter_render(_CityForm(), helper)
    assert _controls_of(out) == _fields("name", "city") + DEFAULT_ACTIONS + HIDDEN_SORT


@pytest.mark.parametrize("when", ["before-first-render", "between-renders"])
def test_filter_layout_replacement_is_respected_with_one_action_group(when):
    """M-HELPER-STATE: a caller-assigned layout selects the fields and order; it is isolated, never mutated, and the
    constructor snapshot is never restored over it."""
    from crispy_forms.layout import Row

    form = _CityForm()
    helper = _new_filter_helper(_filter_helper_class(layout=Layout("name", "city")), form=form)
    if when == "between-renders":
        assert _controls_of(_filter_render(form, helper)) == _fields("name", "city") + DEFAULT_ACTIONS + HIDDEN_SORT
    replacement = Layout(Row("city", "name"))
    helper.layout = replacement
    other = _new_filter_helper(_filter_helper_class(layout=Layout("name")))
    for _ in range(3):
        out = _filter_render(form, helper)
        assert _controls_of(out) == _fields("city", "name") + DEFAULT_ACTIONS + HIDDEN_SORT
        assert len(_action_groups(out)) == 1
        assert _controls_of(_filter_render(_CityForm(), other)) == _fields("name") + DEFAULT_ACTIONS + HIDDEN_SORT
    assert len(replacement.fields) == 1 and replacement.fields[0].fields == ["city", "name"]
    assert helper.layout is not replacement
    assert helper.form is form

    # a second replacement after a completed render is selected the same way
    second = Layout("name")
    helper.layout = second
    assert _controls_of(_filter_render(form, helper)) == _fields("name") + DEFAULT_ACTIONS + HIDDEN_SORT
    assert second.fields == ["name"]


_HOOKS = {
    "default": _ABSENT,
    "none": None,
    "empty": FormActions,
}


@pytest.mark.parametrize("hook", sorted(_HOOKS))
@pytest.mark.parametrize("when", ["before-first-render", "between-renders"])
def test_filter_empty_layout_replacement_dispatches_through_the_tag(monkeypatch, hook, when):
    """M-EMPTY-REPLACEMENT / H-HELPER-TRUTHINESS: ``helper.layout = Layout()`` is prepared in get_attributes, before
    crispy's ``if helper and helper.layout`` guard, so the real render_layout runs for every hook; discarded fields
    never come back, the caller's Layout stays empty and helper.form keeps its identity."""
    from crud_views.lib.views.list import ListViewFilterFormHelper

    events = []
    original_attributes = ListViewFilterFormHelper.get_attributes
    original_render_layout = ListViewFilterFormHelper.render_layout

    def spy_attributes(self, *args, **kwargs):
        result = original_attributes(self, *args, **kwargs)
        events.append(("get_attributes", self, bool(self), bool(self.layout), len(self), self.layout is caller))
        return result

    def spy_render_layout(self, form, context, *args, **kwargs):
        events.append(("render_layout", self, form))
        return original_render_layout(self, form, context, *args, **kwargs)

    monkeypatch.setattr(ListViewFilterFormHelper, "get_attributes", spy_attributes)
    monkeypatch.setattr(ListViewFilterFormHelper, "render_layout", spy_render_layout)

    caller = None
    form = _CityForm()
    helper = _new_filter_helper(_filter_helper_class(layout=Layout("name", "city"), actions=_HOOKS[hook]), form=form)
    other = _new_filter_helper(_filter_helper_class(layout=Layout("name"), actions=_HOOKS[hook]))
    if when == "between-renders":
        assert _controls_of(_filter_render(form, helper))[:2] == _fields("name", "city")
    caller = Layout()
    helper.layout = caller
    events.clear()

    for _ in range(2):
        out = _filter_render(form, helper)
        _filter_render(_CityForm(), other)  # interleaved second helper
        if hook == "default":
            assert _controls_of(out) == DEFAULT_ACTIONS + HIDDEN_SORT
            assert len(_action_groups(out)) == 1
        elif hook == "empty":
            assert _controls_of(out) == HIDDEN_SORT
            assert len(_action_groups(out)) == 1  # the explicit empty group
        else:
            # no action group; the pack's display_form.html falls back to uni_form for an empty form_html
            assert [c for c in _controls_of(out) if c[0] == "button"] == []
            assert _action_groups(out) == []
        assert not [c for c in _controls_of(out) if c[0] == "button" and c[2] not in ("submit", "reset")]

    mine = [e for e in events if e[1] is helper]
    assert [e[0] for e in mine] == ["get_attributes", "render_layout"] * 2
    first_attributes = mine[0]
    # prepared before the guard: helper and layout truthy, zero fields, no longer the caller's object
    assert first_attributes[2:] == (True, True, 0, False)
    assert all(e[2] is form for e in mine if e[0] == "render_layout")
    assert caller.fields == []
    selected = _layout_fields(helper.layout)
    assert all(not isinstance(f, str) for f in selected)  # no discarded field name is restored
    assert len(selected) == (0 if hook == "none" else 1)
    assert helper.form is form


def test_filter_action_hook_none_empty_and_equal_labels():
    """D-04: None omits the group; an empty FormActions stays an explicit empty group; a replacement group appears
    once per render and equal labels do not deduplicate distinct controls."""
    form = _CityForm()
    fields = _fields("name", "city")

    omitted = _new_filter_helper(_filter_helper_class(layout=Layout("name", "city"), actions=None))
    out = _filter_render(form, omitted)
    assert _controls_of(out) == fields + HIDDEN_SORT and _action_groups(out) == []

    empty = _new_filter_helper(_filter_helper_class(layout=Layout("name", "city"), actions=FormActions))
    out = _filter_render(form, empty)
    assert _controls_of(out) == fields + HIDDEN_SORT and len(_action_groups(out)) == 1

    def same_label_actions():
        return FormActions(
            Submit("go", "Go", css_id="go-1", slot="form:filter-submit"),
            Submit("go", "Go", css_id="go-2", slot="form:filter-submit"),
        )

    replaced = _new_filter_helper(_filter_helper_class(layout=Layout("name", "city"), actions=same_label_actions))
    for _ in range(3):
        out = _filter_render(form, replaced)
        go = ("button", "submit", "go", "Go")
        assert _controls_of(out) == [*fields, go, go, *HIDDEN_SORT]
        assert re.findall(r'id="(go-\d)"', out) == ["go-1", "go-2"]
        assert len(_action_groups(out)) == 1


def test_filter_legacy_add_input_controls_stay_quiet_inputs(caplog):
    """D-01 / D-02: a subclass add_input(Submit) stays a crispy input in the pack wrapper, with no warning, beside the
    stock layout actions; a two-argument constructor still works."""
    from crud_views.lib.views.list import ListViewFilterFormHelper

    class LegacyHelper(ListViewFilterFormHelper):
        layout = Layout("name")

        def __init__(self, view, request):
            super().__init__(view, request)
            self.add_input(Submit("legacy", "Search"))
            self.add_input(Button("custom", "Custom", slot="formset:control"))

    helper = _new_filter_helper(LegacyHelper)
    with warnings.catch_warnings(), caplog.at_level(logging.DEBUG):
        warnings.simplefilter("error")
        out = _filter_render(_CityForm(), helper)
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
    assert _controls_of(out) == _fields("name") + DEFAULT_ACTIONS + [
        ("input", "hidden", "sort", ""),
        ("input", "submit", "legacy", "Search"),
        ("input", "button", "custom", "Custom"),
    ]
    assert 'class="btn btn-primary"' in tag(out, name="legacy")
    assert len(_action_groups(out)) == 1


def test_filter_helper_private_state_is_not_published():
    """Lifecycle state is underscore-prefixed: crispy's get_attributes publishes nothing new into the context."""
    from crispy_forms.helper import FormHelper as CrispyFormHelper

    form = _CityForm()
    helper = _new_filter_helper(_filter_helper_class(layout=Layout("name")), form=form, view="VIEW")
    base = set(CrispyFormHelper().get_attributes())
    for _ in range(2):
        _filter_render(form, helper)
        helper.layout = Layout()
        attributes = helper.get_attributes()
        assert set(attributes) - base == {"inputs", "view", "form"}
        assert (attributes["view"], attributes["form"]) == ("VIEW", form)
        assert not [key for key in attributes if key.startswith("_")]


def test_filter_helper_pushes_its_owner_for_its_render_only(owners, monkeypatch):
    """render_layout pushes the private helper-owner entry for its own invocation and restores the context; the
    helper's view, not the page, selects the filter action modes."""
    from crud_views.lib.crispy.buttons import _CV_HELPER_OWNER

    monkeypatch.setattr(owners.RH, "cv_form_actions_label_mode", {"filter-submit": "icon"})
    monkeypatch.setattr(owners.P, "cv_form_actions_label_mode", {"filter-submit": "both"})

    seen = []

    class RecordingSubmit(Submit):
        def render(self, form, context, *args, **kwargs):
            seen.append([layer[_CV_HELPER_OWNER] for layer in context.dicts if _CV_HELPER_OWNER in layer])
            return super().render(form, context, *args, **kwargs)

    helper = _new_filter_helper(
        _filter_helper_class(
            layout=Layout("name"),
            actions=lambda: FormActions(RecordingSubmit("submit", "Apply", slot="form:filter-submit")),
        ),
        view=owners.RH,
    )
    context = Context({"form": _CityForm(), "helper": helper, "view": owners.P})
    layers = [dict(d) for d in context.dicts]
    out = FILTER_CRISPY.render(context)
    assert seen == [[owners.RH]]
    assert [el.get("class") for el in _buttons(out)] == ["m-icon"]
    assert [dict(d) for d in context.dicts] == layers
    assert not any(_CV_HELPER_OWNER in layer for layer in context.dicts)


def test_filter_custom_layout_class_keeps_its_behavior_while_isolated():
    """A selected custom Layout subclass keeps its own render behavior and nested nodes; only the private copy is
    made truthy, the caller's object and class are untouched."""
    from crispy_forms.layout import HTML

    class MarkedLayout(Layout):
        def render(self, form, context, template_pack=None, **kwargs):
            return "<p>marked</p>" + super().render(form, context, template_pack=template_pack, **kwargs)

    caller = MarkedLayout(HTML("<em>note</em>"), "city")
    helper = _new_filter_helper(_filter_helper_class(layout=Layout("name")))
    helper.layout = caller
    for _ in range(2):
        out = _filter_render(_CityForm(), helper)
        assert out.count("<p>marked</p>") == 1 and out.count("<em>note</em>") == 1
        assert _controls_of(out) == _fields("city") + DEFAULT_ACTIONS + HIDDEN_SORT
        assert len(_action_groups(out)) == 1
    assert isinstance(helper.layout, MarkedLayout) and helper.layout is not caller
    assert type(caller) is MarkedLayout and len(caller.fields) == 2
    assert bool(MarkedLayout()) is False  # the user's class keeps crispy's len-based truthiness


@pytest.mark.parametrize("when", ["class", "assigned"])
def test_filter_layout_that_cannot_be_deep_copied_names_the_helper(when):
    """IN-01: a layout holding a non-copyable member fails with a TypeError that names the helper class."""
    import threading

    from crispy_forms.layout import HTML

    class LockedHTML(HTML):
        def __init__(self, html):
            super().__init__(html)
            self.lock = threading.Lock()

    locked = Layout(LockedHTML("<em>note</em>"), "city")
    match = r"FilterHelper\.layout must be deep-copyable \(each helper renders its own copy\)"
    if when == "class":
        with pytest.raises(TypeError, match=match) as exc_info:
            _new_filter_helper(_filter_helper_class(layout=locked))
    else:
        helper = _new_filter_helper(_filter_helper_class(layout=Layout("name")))
        helper.layout = locked
        with pytest.raises(TypeError, match=match) as exc_info:
            _filter_render(_CityForm(), helper)
    assert isinstance(exc_info.value.__cause__, TypeError)
    assert len(locked.fields) == 2  # the caller's layout is untouched


# --- copied layouts keep their kind icons (06-10: CR-01 / WR-01) ---------------------------------------------------

# name -> (Font Awesome classes of the kind default, label) of the package controls in a copied filter layout
COPIED = {"submit": ("fa-solid fa-filter", "Go"), "reset": ("fa-solid fa-rotate-left", "Clear")}
COPIED_CONTROLS = [("button", "submit", "submit", "Go"), ("button", "reset", "reset", "Clear")]
# the semantic icon name each kind resolves to when icon= is omitted (D-16)
KIND_ICON_NAMES = {
    "submit": "save",
    "delete": "delete",
    "cancel": "cancel",
    "filter-submit": "filter",
    "filter-reset": "filter-reset",
}
# a submitted name suggesting another kind: the slot, never the name, picks the icon
MISLEADING_NAMES = {
    "submit": "delete",
    "delete": "reset",
    "cancel": "submit",
    "filter-submit": "reset",
    "filter-reset": "submit",
}


def _copied_layout() -> Layout:
    return Layout(
        "name",
        FormActions(Submit("submit", "Go", slot="form:filter-submit", css_class="x-go"), Reset("reset", "Clear")),
    )


def _copied_buttons(out: str, mode: str) -> list[tuple]:
    """Asserts the kind icon and accessible label of each copied control; returns their (id, class) pairs."""
    root = _fragment(out)
    seen = []
    for name, (fa, label) in COPIED.items():
        (el,) = root.cssselect(f"button[name={name}]")
        assert _icon_classes(el) == [fa]
        (span,) = el.cssselect("span")
        assert span.text == label
        if mode == "icon":
            assert span.get("class") == "visually-hidden"
            assert el.get("title") == label and el.get("data-cv-tooltip") == "form"
        else:
            assert span.get("class") is None
            assert el.get("title") is None and el.get("data-cv-tooltip") is None
        seen.append((el.get("id"), el.get("class")))
    return seen


@pytest.mark.parametrize("strict", [True, False], ids=["strict", "lenient"])
@pytest.mark.parametrize("mode", ["both", "icon"])
@pytest.mark.parametrize("where", ["class", "before-first-render", "between-renders"])
def test_copied_filter_layout_keeps_kind_icons(where, mode, strict, caplog):
    """CR-01 / D-03 / D-16: package buttons inside a class-level or caller-assigned filter layout are deep-copied per
    helper and still render their kind icons through the real crispy tag, with no warning and no strict error."""
    source = _copied_layout()
    source_actions = source.fields[1]
    source_buttons = list(source_actions.fields)
    form = _CityForm()
    expected = _fields("name") + COPIED_CONTROLS + HIDDEN_SORT
    attrs = set()
    settings = {"CRUD_VIEWS_LABEL_MODE_DEFAULTS": {"form": mode}, "CRUD_VIEWS_STRICT": strict}
    with override_settings(**settings), warnings.catch_warnings(), caplog.at_level(logging.DEBUG):
        warnings.simplefilter("error")
        if where == "class":
            helper_cls = _filter_helper_class(layout=source, actions=None)
            helper, other = _new_filter_helper(helper_cls, form=form), _new_filter_helper(helper_cls)
        else:
            helper_cls = _filter_helper_class(layout=Layout("city"), actions=None)
            helper, other = _new_filter_helper(helper_cls, form=form), _new_filter_helper(helper_cls)
            if where == "between-renders":
                assert _controls_of(_filter_render(form, helper)) == _fields("city") + HIDDEN_SORT
            helper.layout = source
            other.layout = source
        for _ in range(3):
            for current in (helper, other, helper):
                out = _filter_render(form if current is helper else _CityForm(), current)
                assert _controls_of(out) == expected
                assert len(_action_groups(out)) == 1
                attrs.add(tuple(_copied_buttons(out, mode)))
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
    # ids and classes are stable across helpers and renders; the project css_class is kept
    assert len(attrs) == 1
    ((submit_id, submit_class), (reset_id, _)) = attrs.pop()
    assert (submit_id, reset_id) == ("submit-id-submit", "reset-id-reset")
    assert "x-go" in submit_class.split()
    # the source layout is never rendered or mutated: each helper renders its own copy of its buttons
    assert source.fields[0] == "name" and source.fields[1] is source_actions and len(source.fields) == 2
    assert source_actions.fields == source_buttons
    copies = [current.layout.fields[1].fields for current in (helper, other)]
    assert all(len(buttons) == 2 for buttons in copies)
    assert all(b is not s for buttons in copies for b, s in zip(buttons, source_buttons, strict=True))
    assert all(a is not b for a, b in zip(*copies, strict=True))
    assert helper.form is form


@pytest.mark.parametrize("kind", sorted(KIND_ICONS))
def test_copied_adapter_keeps_icon_contract(kind):
    """CR-01 / WR-01: a copied adapter without icon= resolves its kind's named icon (a str), whatever its name."""
    from crud_views.lib.view.button_data import cv_button_data

    adapter, slot, fa = KIND_ICONS[kind]
    original = adapter(MISLEADING_NAMES[kind], "Go", **slot)
    for copier in (copy.copy, copy.deepcopy):
        copied = copier(original)
        assert copied is not original
        for mode in ("label", "both", "icon"):
            data = cv_button_data({**copied._cv_button_context(), "cv_label_mode": mode}, "form")
            assert type(data["cv_icon"]) is str and data["cv_icon"] == KIND_ICON_NAMES[kind]
    copied = copy.deepcopy(original)
    for mode in ("both", "icon"):
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}, CRUD_VIEWS_STRICT=True):
            (el,) = _buttons(_render(_helper(copied)))
        assert _icon_classes(el) == [fa]
        assert el.get("name") == MISLEADING_NAMES[kind]


@pytest.mark.parametrize(
    "control,expected,fa",
    [
        (Submit("submit", "Go", icon=None), None, []),
        (Reset("reset", "Clear", icon=""), "", []),
        (Submit("delete", "Go", slot="form:filter-submit", icon=None), None, []),
        (Button("submit", "Go", icon="workflow"), "workflow", [WORKFLOW_ICON]),
        (Submit("reset", "Go", slot="form:delete", icon="fas:rocket"), "fas:rocket", ["fa-solid fa-rocket"]),
    ],
    ids=["none", "empty", "none-misnamed", "workflow", "prefixed-misnamed"],
)
def test_copied_adapter_preserves_explicit_icon(control, expected, fa):
    """D-16: an explicit icon= (a choice, or None / "" for no icon) survives copying and is never the kind default."""
    for copied in (copy.copy(control), copy.deepcopy(control)):
        raw = copied._cv_button_context()["cv_icon"]
        assert raw == expected and type(raw) is type(expected)
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}, CRUD_VIEWS_STRICT=True):
            (el,) = _buttons(_render(_helper(copied)))
        assert _icon_classes(el) == fa
    # the original keeps its own explicit choice
    assert control._cv_button_context()["cv_icon"] == expected


# --- cancel links (Phase 6.1): an eligible cancel renders as a native <a> ------------------------------------------

LINK = {"form:cancel-tag": "a"}
BUTTON_LOGGER = "crud_views.lib.view.button_data"


def _links(markup: str) -> list:
    return _fragment(markup).cssselect("a")


def _tag_warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == BUTTON_LOGGER and r.levelno >= logging.WARNING]


class _BackButton(Button):
    """A Button subclass: still the cancel kind with the native type button, so it may become a link."""


def test_configured_cancel_renders_one_native_link():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
        markup = _render(_helper(Submit("submit", "Save"), Button("reset", "Cancel", data_cv_cancel_url="/back/")))
    (link,) = _links(markup)
    (submit,) = _buttons(markup)
    assert dict(link.attrib) == {"href": "/back/", "id": "button-id-reset", "class": "btn btn-secondary"}
    assert [s.text for s in link.cssselect("span")] == ["Cancel"]
    assert (submit.get("type"), submit.get("name"), submit.get("value")) == ("submit", "submit", "Save")
    # no tag attribute, no button identity / submission attributes, no cancel-handler marker on the anchor
    assert "tag=" not in markup
    assert "data-cv-cancel-url" not in markup


def test_explicit_tag_a_renders_one_native_link_with_an_escaped_destination():
    markup = _render(_helper(Button("reset", "Cancel", tag="a", data_cv_cancel_url="/back/?a=1&b=<2>")))
    assert not _buttons(markup)
    (link,) = _links(markup)
    assert link.get("href") == "/back/?a=1&b=<2>"
    assert 'href="/back/?a=1&amp;b=&lt;2&gt;"' in markup
    assert link.text_content() == "Cancel"


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_cancel_link_keeps_the_label_mode_body(mode):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}):
        (link,) = _links(_render(_helper(Button("reset", "Cancel", tag="a", data_cv_cancel_url="/b/"))))
    assert link.text_content().strip() == "Cancel"
    assert [i.get("class") for i in link.cssselect("i")] == ([] if mode == "label" else ["fa-solid fa-xmark"])
    if mode == "icon":
        assert (link.get("title"), link.get("data-cv-tooltip")) == ("Cancel", "form")
        assert [s.text for s in link.cssselect("span.visually-hidden")] == ["Cancel"]
    else:
        assert link.get("title") is None


def test_tag_keyword_is_configuration_not_an_attribute():
    control = Button("reset", "Cancel", tag="a", data_cv_cancel_url="/b/")
    assert "tag" not in str(control.flat_attrs)
    assert "tag" not in control._cv_attrs
    assert control._cv_button_context()["cv_tag"] == "a"
    assert Button("reset", "Cancel")._cv_button_context()["cv_tag"] is None


def test_unconfigured_cancel_stays_the_original_button():
    markup = _render(_helper(Button("reset", "Cancel", data_cv_cancel_url="/b/")))
    assert not _links(markup)
    (el,) = _buttons(markup)
    assert (el.get("type"), el.get("data-cv-cancel-url")) == ("button", "/b/")


def test_explicit_none_inherits_and_table_none_selects_button():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
        assert _links(_render(_helper(Button("reset", "Back", tag=None, data_cv_cancel_url="/b/"))))
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": None}):
        markup = _render(_helper(Button("reset", "Back", data_cv_cancel_url="/b/")))
    assert not _links(markup) and len(_buttons(markup)) == 1


INVALID_TAGS = ["", " a", "a ", "A", "Button", "BUTTON", "link", "anchor", 0, 1, True, False, ["a"], {"a": 1}, b"a"]


@pytest.mark.parametrize("value", INVALID_TAGS, ids=repr)
@pytest.mark.parametrize("adapter", [Submit, Button, Reset])
@pytest.mark.parametrize("path", ["layout", "input"])
def test_invalid_explicit_tag_raises_at_construction(path, adapter, value):
    """D-01/D-03: only exactly "button", "a" or None; raised before either the layout or the legacy path renders."""
    with pytest.raises(ValueError, match="tag"):
        control = adapter("go", "Go", tag=value, data_cv_cancel_url="/b/")
        _render(_helper(control) if path == "layout" else _helper(inputs=[control]))


NONELIGIBLE = [
    (Submit, None),  # ordinary submit
    (Reset, None),  # ordinary reset
    (Submit, "form:cancel"),  # native submit re-slotted to cancel stays a submit
    (Reset, "form:cancel"),  # native reset re-slotted to cancel stays a reset
    (Button, "form:submit"),  # a Button re-slotted away from cancel
    (Button, "form:filter-reset"),
    (Button, "formset:control"),
]
NONELIGIBLE_IDS = ["submit", "reset", "submit-as-cancel", "reset-as-cancel", "button-as-submit", "button-as-reset", "x"]


@pytest.mark.parametrize("adapter,slot", NONELIGIBLE, ids=NONELIGIBLE_IDS)
@pytest.mark.parametrize("path", ["layout", "input"])
def test_explicit_link_on_a_noneligible_control_raises(path, adapter, slot):
    """D-09: only the cancel kind with the native type button may become a link; native actions stay native."""
    with pytest.raises(ValueError, match="cancel"):
        control = adapter("reset", "Back", slot=slot, tag="a", data_cv_cancel_url="/b/")
        _render(_helper(control) if path == "layout" else _helper(inputs=[control]))


@pytest.mark.parametrize("adapter,slot", NONELIGIBLE[:6], ids=NONELIGIBLE_IDS[:6])
@pytest.mark.parametrize("config", ["a", "bogus"])
def test_noneligible_controls_ignore_the_inherited_cancel_tag(adapter, slot, config, caplog):
    """D-11: configuration never turns a native action into a link, and its value is never read for one."""
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": config}, CRUD_VIEWS_STRICT=True):
        for tag_value in (None, "button"):
            markup = _render(_helper(adapter("reset", "Back", slot=slot, tag=tag_value, data_cv_cancel_url="/b/")))
            assert not _links(markup)
            (el,) = _buttons(markup)
            assert el.get("type") == adapter.input_type
    assert _tag_warnings(caplog) == []


@pytest.mark.parametrize("adapter", [Submit, Button, Reset])
def test_explicit_button_is_valid_everywhere(adapter):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
        markup = _render(_helper(adapter("reset", "Back", tag="button", data_cv_cancel_url="/b/")))
    assert not _links(markup)
    (el,) = _buttons(markup)
    assert el.get("type") == adapter.input_type
    assert el.get("tag") is None


def test_button_subclass_is_eligible():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
        (link,) = _links(_render(_helper(_BackButton("reset", "Back", data_cv_cancel_url="/b/"))))
    assert link.get("href") == "/b/"
    (link,) = _links(_render(_helper(_BackButton("reset", "Back", tag="a", data_cv_cancel_url="/b/"))))
    assert link.get("href") == "/b/"


INVALID_CONFIG = ["", " a", "A", "Button", "link", 0, True, False, ["a"], {"a": 1}]


@pytest.mark.parametrize("value", INVALID_CONFIG, ids=repr)
@pytest.mark.parametrize("state", ["url", "no-url", "disabled"])
def test_selected_invalid_configuration_raises_in_strict_mode(value, state):
    """D-01/D-04: a selected invalid table value is never hidden by the missing-URL or disabled fallback."""
    extras = {"url": {"data_cv_cancel_url": "/b/"}, "no-url": {}, "disabled": {"data_cv_cancel_url": "/b/"}}[state]
    if state == "disabled":
        extras["disabled"] = True
    config = override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": value}, CRUD_VIEWS_STRICT=True)
    with config, pytest.raises(ValueError, match="form:cancel-tag"):
        _render(_helper(Button("reset", "Back", **extras)))


@pytest.mark.parametrize("value", INVALID_CONFIG, ids=repr)
@pytest.mark.parametrize("state", ["url", "no-url", "disabled"])
def test_selected_invalid_configuration_warns_and_renders_a_button_when_lenient(value, state, caplog):
    extras = {"url": {"data_cv_cancel_url": "/b/"}, "no-url": {}, "disabled": {"data_cv_cancel_url": "/b/"}}[state]
    if state == "disabled":
        extras["disabled"] = True
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": value}, CRUD_VIEWS_STRICT=False):
        markup = _render(_helper(Button("reset", "Back", **extras)))
    assert not _links(markup)
    (el,) = _buttons(markup)
    assert el.get("type") == "button"
    (message,) = _tag_warnings(caplog)
    assert "form:cancel-tag" in message and repr(value) in message


@pytest.mark.parametrize("explicit", ["button", "a"])
@pytest.mark.parametrize("value", ["bogus", "", ["a"]], ids=repr)
def test_valid_explicit_tag_bypasses_invalid_configuration(explicit, value, caplog):
    """D-12: the overridden table value is not read during this render, so it cannot fail it."""
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": value}, CRUD_VIEWS_STRICT=True):
        markup = _render(_helper(Button("reset", "Back", tag=explicit, data_cv_cancel_url="/b/")))
    assert len(_links(markup)) == (explicit == "a")
    assert len(_buttons(markup)) == (explicit == "button")
    assert _tag_warnings(caplog) == []


@pytest.mark.parametrize(
    "extras",
    [{}, {"data_cv_cancel_url": None}, {"data_cv_cancel_url": False}, {"data_cv_cancel_url": ""}],
    ids=["missing", "none", "false", "empty"],
)
def test_missing_or_empty_destination_keeps_the_button(extras):
    """D-08: no href="" and no link without a destination; the original button output is kept."""
    expected = _render(_helper(Button("reset", "Back", **extras)))
    for control in (Button("reset", "Back", tag="a", **extras), Button("reset", "Back", **extras)):
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
            markup = _render(_helper(control))
        assert markup == expected
        assert not _links(markup) and "href" not in markup


@pytest.mark.parametrize("order", ["underscore-first", "hyphen-first"])
def test_hyphenated_destination_alias_wins_in_either_order(order):
    pairs = [("data_cv_cancel_url", "/u/"), ("data-cv-cancel-url", "/h/")]
    if order == "hyphen-first":
        pairs.reverse()
    (link,) = _links(_render(_helper(Button("reset", "Back", tag="a", **dict(pairs)))))
    assert link.get("href") == "/h/"
    # an empty winning alias never resurrects the losing one
    pairs = [("data_cv_cancel_url", "/u/"), ("data-cv-cancel-url", "")]
    if order == "hyphen-first":
        pairs.reverse()
    markup = _render(_helper(Button("reset", "Back", tag="a", **dict(pairs))))
    assert not _links(markup)
    (el,) = _buttons(markup)
    assert el.get("data-cv-cancel-url") == ""


@pytest.mark.parametrize(
    "name,value,emitted",
    [
        # lxml reports a bare boolean attribute with its own name as the value
        ("disabled", True, "disabled"),
        ("disabled", "", ""),
        ("disabled", 0, "0"),
        ("disabled", "false", "false"),
        ("disabled", "disabled", "disabled"),
        ("DISABLED", True, "disabled"),
        ("Disabled", "", ""),
    ],
    ids=repr,
)
def test_emitted_disabled_keeps_the_native_button(name, value, emitted):
    """D-06: any emitted disabled attribute (HTML presence, not Python truth) keeps a native disabled button."""
    for control in (
        Button("reset", "Back", tag="a", data_cv_cancel_url="/b/", **{name: value}),
        Button("reset", "Back", data_cv_cancel_url="/b/", **{name: value}),
    ):
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=LINK):
            markup = _render(_helper(control))
        assert not _links(markup)
        (el,) = _buttons(markup)
        assert el.get("disabled") == emitted
        assert el.get("data-cv-cancel-url") == "/b/"


@pytest.mark.parametrize("value", [False, None])
def test_omitted_disabled_still_renders_the_link(value):
    (link,) = _links(_render(_helper(Button("reset", "Back", tag="a", data_cv_cancel_url="/b/", disabled=value))))
    assert link.get("href") == "/b/"
    assert "disabled" not in link.attrib


def test_legacy_helper_inputs_with_valid_tags_stay_quiet_pack_inputs(caplog):
    """D-17: a legacy helper input never renders the leaf, so its tag is never resolved, warned about or emitted."""
    caplog.set_level(logging.DEBUG)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": "bogus"}, CRUD_VIEWS_STRICT=True):
            markup = _render(
                _helper(
                    inputs=(
                        Button("reset", "Back", tag="a", data_cv_cancel_url="/b/"),
                        Submit("go", "Go", tag="button"),
                        Submit("odd", "Odd", slot="formset:control", tag=None),
                        Submit("unknown", "Unknown", slot="form:unknown", tag="button"),
                        Reset("clear", "Clear", tag=None),
                    )
                )
            )
    assert caught == []
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
    doc = _fragment(markup)
    assert not doc.cssselect("button, a")
    by_name = {el.get("name"): el for el in doc.cssselect("input")}
    assert set(by_name) == {"reset", "go", "odd", "unknown", "clear"}
    assert by_name["reset"].get("data-cv-cancel-url") == "/b/"
    assert all(el.get("tag") is None for el in by_name.values())
    assert "tag=" not in markup


def test_tag_choice_is_resolved_per_render():
    shared = Button("reset", "Back", data_cv_cancel_url="/b/")
    copied = copy.deepcopy(shared)
    seen = []
    for config in ({}, LINK, {}, LINK):
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=config):
            for control in (shared, copied):
                seen.append(len(_links(_render(_helper(control)))))
    assert seen == [0, 0, 1, 1, 0, 0, 1, 1]
    assert shared._cv_tag is None and copied._cv_tag is None
