"""Page-owned forms: raw nesting, enforced CSRF, and render-local helper policy."""

from html.parser import HTMLParser
from types import ModuleType, SimpleNamespace

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, LayoutObject
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext, Template
from django.test import Client, override_settings
from django.urls import path
from django.utils.safestring import mark_safe
from lxml import html as html_parser

from crud_views.templatetags.crud_views import cv_render_form
from tests.lib.helper.forms import form_payload
from tests.test1 import test_crispy_buttons as button_tests
from tests.test1.app.models import Author
from tests.test1.app.views import AuthorForm
from tests.test1.test_crispy_buttons import (
    _controls,
    _modes,
    _owned_form,
    _owner_helper,
    _resolve_owner,
    _sig,
)
from tests.test1.test_form_frame import _theme_templates

owners = button_tests.owners


class _RawForms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.forms = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            assert not self.stack, "nested raw form start tag"
            owner = {"attrs": attrs, "tokens": [], "submitters": []}
            self.forms.append(owner)
            self.stack.append(owner)
        elif self.stack:
            if tag == "input" and attrs.get("name") == "csrfmiddlewaretoken":
                self.stack[-1]["tokens"].append(attrs["value"])
            if tag == "button" and attrs.get("type") == "submit":
                self.stack[-1]["submitters"].append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            assert self.stack, "unmatched raw form end tag"
            self.stack.pop()


def assert_owned_form_markup(markup):
    """Scan raw events, before a browser can repair nested/unclassed forms."""
    parser = _RawForms()
    parser.feed(markup)
    assert not parser.stack, "unclosed raw form"
    owners = [f for f in parser.forms if "cv-form" in f["attrs"].get("class", "").split()]
    assert len(owners) == 1
    assert len(owners[0]["tokens"]) == 1
    return owners[0]


@pytest.mark.django_db
def test_create_ownership_csrf_round_trip(cv_author, user_author_add):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_author_add)
    response = client.get("/author/create/")
    assert response.status_code == 200
    sibling = '<form method="post"><input name="csrfmiddlewaretoken" value="sibling"></form>'
    owner = assert_owned_form_markup(sibling + response.content.decode() + sibling)
    assert owner["attrs"]["method"] == "post"
    assert owner["attrs"]["enctype"] == "multipart/form-data"
    assert "novalidate" in owner["attrs"]
    target = owner["attrs"]["action"]
    submitter = owner["submitters"][0]
    data = {"first_name": "Ownership", "last_name": "Tracer", submitter["name"]: submitter["value"]}
    before = Author.objects.count()
    for token in (None, "invalid"):
        payload = dict(data)
        if token is not None:
            payload["csrfmiddlewaretoken"] = token
        assert client.post(target, payload).status_code == 403
        assert Author.objects.count() == before
    response = client.post(target, {**data, "csrfmiddlewaretoken": owner["tokens"][0]})
    assert response.status_code == 302
    assert Author.objects.filter(first_name="Ownership", last_name="Tracer").exists()


def test_raw_guard_rejects_unclassed_nested_form():
    with pytest.raises(AssertionError, match="nested raw form"):
        assert_owned_form_markup('<form class="cv-form"><form></form></form>')


class NameForm(forms.Form):
    name = forms.CharField()


def _helper(cls=FormHelper):
    helper = cls()
    helper.form_tag = False
    helper.layout = Layout("name")
    return helper


def _context(form):
    return Context({"form": form, "csrf_token": "test-token", "view": None})


class AliasingHelper(FormHelper):
    def __copy__(self):
        return self


class RaisingCopyHelper(FormHelper):
    def __copy__(self):
        raise RuntimeError("copy forbidden")


class ReadOnlyHelper(FormHelper):
    __slots__ = ("extra",)

    @property
    def disable_csrf(self):
        return False


class HookHelper(FormHelper):
    def get_attributes(self, *args, **kwargs):
        return {**super().get_attributes(*args, **kwargs), "hook": "kept"}

    def render_layout(self, *args, **kwargs):
        return mark_safe(super().render_layout(*args, **kwargs) + "HOOK_LAYOUT")


class FalseyHelper(HookHelper):
    def __bool__(self):
        return False


class HiddenRowForm(NameForm):
    identity = forms.IntegerField(widget=forms.HiddenInput)
    unmentioned = forms.CharField(required=False)


@pytest.mark.parametrize("helper_class", [FormHelper, HookHelper, ReadOnlyHelper])
@pytest.mark.parametrize("hidden_in_layout", [False, True])
@pytest.mark.parametrize("render_hidden_fields", [False, True])
def test_formset_hidden_fields_preserve_helper_hooks_and_flags(helper_class, hidden_in_layout, render_hidden_fields):
    helper = _helper(helper_class)
    helper.render_hidden_fields = render_hidden_fields
    if hidden_in_layout:
        helper.layout.append("identity")
    snapshot = dict(helper.__dict__)
    fields = list(helper.layout.fields)
    rows = forms.formset_factory(HiddenRowForm, extra=0)(
        initial=[{"name": "First", "identity": 42}, {"name": "Second", "identity": 73}], prefix="rows"
    )
    rows.helper = helper

    for _ in range(2):
        markup = cv_render_form(_context(rows))
        document = html_parser.fragment_fromstring(markup, create_parent=True)
        for index, identity in enumerate((42, 73)):
            hidden = document.xpath(f'.//input[@name="rows-{index}-identity"]')
            assert len(hidden) == 1
            assert hidden[0].get("type") == "hidden"
            assert hidden[0].get("value") == str(identity)
        assert not document.xpath('.//input[contains(@name, "unmentioned")]')
        assert not document.xpath('.//input[@name="csrfmiddlewaretoken"]')
        assert len(document.xpath('.//input[@name="rows-TOTAL_FORMS"]')) == 1
        if helper_class is HookHelper:
            assert markup.count("HOOK_LAYOUT") == 2
        assert helper.__dict__ == snapshot
        assert helper.layout.fields == fields

    # Crispy's formset policy must not leak into an ordinary form sharing the helper.
    single = HiddenRowForm(initial={"name": "Single", "identity": 99})
    single.helper = helper
    single_markup = cv_render_form(_context(single))
    assert ('name="identity"' in single_markup) is (hidden_in_layout or render_hidden_fields)
    assert helper.__dict__ == snapshot


def test_formset_custom_layout_hook_can_render_hidden_fields_without_super():
    calls = []

    class Row(HiddenRowForm):
        secondary = forms.IntegerField(widget=forms.HiddenInput)

    class CustomHelper(FormHelper):
        def render_layout(self, form, context, template_pack):
            assert self is helper
            calls.append((context["formset_form"], str(template_pack)))
            form.rendered_fields = {"name", "identity"}
            return mark_safe(form["name"].as_widget() + form["identity"].as_widget() + "CUSTOM_HOOK")

    helper = _helper(CustomHelper)
    helper.field_template = "custom-hidden-field.html"
    helper.template_pack = "bootstrap5"
    snapshot = dict(helper.__dict__)
    rows = forms.formset_factory(Row, extra=0)(initial=[{"name": "First", "identity": 42, "secondary": 73}])
    rows.helper = helper
    with _theme_templates({"custom-hidden-field.html": "FIELD_TEMPLATE{{ field }}"}):
        markup = cv_render_form(_context(rows))
    document = html_parser.fragment_fromstring(markup, create_parent=True)
    for name, value in (("identity", "42"), ("secondary", "73")):
        hidden = document.xpath(f'.//input[@name="form-0-{name}"]')
        assert len(hidden) == 1
        assert hidden[0].get("value") == value
    assert markup.count("CUSTOM_HOOK") == 1
    assert markup.count("FIELD_TEMPLATE") == 1
    assert calls == [(rows.forms[0], "bootstrap5")]
    assert helper.__dict__ == snapshot


@pytest.mark.django_db
@pytest.mark.parametrize("helper_class", [FormHelper, HookHelper])
def test_model_formset_page_owned_csrf_post_round_trip(helper_class):
    authors = [
        Author.objects.create(first_name="First", last_name="Original"),
        Author.objects.create(first_name="Second", last_name="Original"),
    ]
    formset_class = forms.modelformset_factory(Author, fields=["first_name", "last_name"], extra=0)
    helper = helper_class()
    helper.form_tag = False
    helper.layout = Layout("first_name", "last_name")
    snapshot = dict(helper.__dict__)

    def edit_authors(request):
        rows = formset_class(
            request.POST if request.method == "POST" else None, queryset=Author.objects.order_by("order")
        )
        rows.helper = helper
        if request.method == "POST" and rows.is_valid():
            rows.save()
            return HttpResponseRedirect("/saved/")
        markup = Template(
            '{% load crud_views %}<form class="cv-form" method="post">{% csrf_token %}{% cv_render_form %}</form>'
        ).render(RequestContext(request, {"form": rows, "view": None}))
        return HttpResponse(markup, status=422 if request.method == "POST" else 200)

    urls = ModuleType("formset_ownership_urls")
    urls.urlpatterns = [path("edit/", edit_authors)]
    with override_settings(ROOT_URLCONF=urls):
        client = Client(enforce_csrf_checks=True)
        response = client.get("/edit/")
        assert response.status_code == 200
        assert_owned_form_markup(response.content.decode())
        payload = form_payload(response)
        assert [payload.get(f"form-{index}-id") for index in range(2)] == [str(author.pk) for author in authors]
        for index in range(2):
            payload[f"form-{index}-last_name"] = "Updated"
        for token in (None, "invalid"):
            rejected = {key: value for key, value in payload.items() if key != "csrfmiddlewaretoken"}
            if token is not None:
                rejected["csrfmiddlewaretoken"] = token
            assert client.post("/edit/", rejected).status_code == 403
            assert Author.objects.filter(last_name="Updated").count() == 0
        response = client.post("/edit/", payload)
        assert response.status_code == 302
        assert response.url == "/saved/"
    assert set(Author.objects.values_list("pk", flat=True)) == {author.pk for author in authors}
    assert Author.objects.filter(last_name="Updated").count() == 2
    assert helper.__dict__ == snapshot


@pytest.mark.parametrize(
    "helper_class", [FormHelper, AliasingHelper, RaisingCopyHelper, ReadOnlyHelper, HookHelper, FalseyHelper]
)
def test_helper_adaptation_contract(helper_class):
    helper = _helper(helper_class)
    form = NameForm()
    form.helper = helper
    snapshot = dict(helper.__dict__)
    fields = list(helper.layout.fields)
    context = _context(form)
    layers = list(context.dicts)
    custom = "{% load crispy_forms_tags %}{% crispy form cv_form_helper %}"
    for _ in range(2):
        with _theme_templates({"crud_views/tags/form.html": custom}):
            html = cv_render_form(context)
        assert "csrfmiddlewaretoken" not in html
        assert "<form" not in html
        assert 'name="name"' in html
        if helper_class is HookHelper:
            assert "HOOK_LAYOUT" in html
        assert helper.__dict__ == snapshot
        assert helper.layout.fields == fields
        assert context.dicts == layers


@pytest.mark.parametrize(
    ("form_owner", "helper_owner", "winner"),
    [("R", "RH", "R"), (None, "RH", "RH"), (None, None, "P"), ("falsey", "RH", "S"), (None, "falsey", "S")],
)
def test_form_button_owner_tiers_survive_render_boundary(owners, form_owner, helper_owner, winner):
    def resolve(value):
        return None if value is None else _resolve_owner(owners, value)

    form = _owned_form(resolve(form_owner))
    form.helper = _owner_helper(*_controls("owned"), view=resolve(helper_owner))
    context = Context({"view": owners.P, "csrf_token": "test-token"})
    # A real crispy-shaped enclosing response is not a page owner, even above the page.
    context.push(is_formset=False, template_pack="bootstrap5", inputs=[], form_method="post", view=owners.H)
    context.push(form=form)
    before = [dict(layer) for layer in context.dicts]
    assert _modes(cv_render_form(context)) == {"owned": _sig(winner)}
    assert context.dicts == before


def test_actual_enclosing_crispy_overlay_is_not_a_page_owner(owners):
    inner = _owned_form(None)
    inner.helper = _owner_helper(*_controls("inner"), view=None)

    class InnerRender(LayoutObject):
        def render(self, form, context, **kwargs):
            before = [dict(layer) for layer in context.dicts]
            with context.push(form=inner):
                html = cv_render_form(context)
            assert context.dicts == before
            return html

    helper = _owner_helper(InnerRender(), view=owners.H)
    context = Context({"form": _owned_form(owners.OF), "helper": helper, "view": owners.P})
    before = [dict(layer) for layer in context.dicts]
    html = Template("{% load crispy_forms_tags %}{% crispy form helper %}").render(context)
    assert _modes(html) == {"inner": _sig("P")}
    assert context.dicts == before


@pytest.mark.parametrize("hook", ["get_attributes", "render_layout"])
def test_custom_hook_exception_and_context_preserved(hook):
    error = RuntimeError("original hook error")

    def fail(*args, **kwargs):
        raise error

    helper = _helper(type("BrokenHookHelper", (FormHelper,), {hook: fail}))
    form = NameForm()
    form.helper = helper
    snapshot = dict(helper.__dict__)
    context = _context(form)
    layers = [dict(layer) for layer in context.dicts]
    with pytest.raises(RuntimeError) as exc:
        cv_render_form(context)
    assert exc.value is error
    assert helper.__dict__ == snapshot
    assert context.dicts == layers


@pytest.mark.parametrize("helper_class", [HookHelper, FalseyHelper])
def test_helper_custom_template_preserves_attributes_hook(helper_class):
    helper = _helper(helper_class)
    helper.template = "custom-helper.html"
    form = NameForm()
    form.helper = helper
    custom = "{{ hook }}|{{ disable_csrf }}|{{ form.form_html }}"
    with _theme_templates({"custom-helper.html": custom}):
        html = cv_render_form(_context(form))
    assert html.lstrip().startswith("kept|True|")
    assert ("HOOK_LAYOUT" in html) is (helper_class is HookHelper)
    assert helper.disable_csrf is False


@pytest.mark.parametrize("kind", ["missing", "none", "computed", "inherited"])
def test_helper_selected_once(kind):
    selected = _helper()

    class ComputedForm(NameForm):
        calls = 0

        @property
        def helper(self):
            self.calls += 1
            return selected

    class ParentForm(NameForm):
        helper = selected

    class ChildForm(ParentForm):
        pass

    form = ComputedForm() if kind == "computed" else ChildForm() if kind == "inherited" else NameForm()
    if kind == "none":
        form.helper = None
    html = cv_render_form(_context(form))
    assert 'name="name"' in html
    assert "<form" not in html
    assert "csrfmiddlewaretoken" not in html
    if kind == "computed":
        assert form.calls == 1
    assert selected.disable_csrf is False


@pytest.mark.parametrize("strict", [False, True])
def test_wrapping_helper_is_always_rejected(strict):
    form = NameForm()
    form.helper = FormHelper()
    original = dict(form.helper.__dict__)
    context = _context(form)
    layers = list(context.dicts)
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ImproperlyConfigured, match="form_tag=False"):
        cv_render_form(context)
    assert form.helper.__dict__ == original
    assert context.dicts == layers


def _library_form():
    view = SimpleNamespace(
        request=SimpleNamespace(user=None),
        get_cancel_button_context=lambda **kw: {"cv_url": "/", "cv_action_label": "Cancel"},
    )
    return AuthorForm(cv_view=view)


def test_standalone_library_and_custom_policy():
    standalone = Template("{% load crispy_forms_tags %}{% crispy form %}")
    form = _library_form()
    html = standalone.render(_context(form))
    assert "<form" not in html
    assert html.count('name="csrfmiddlewaretoken"') == 1
    assert 'name="first_name"' in html
    caller = Template('{% load crispy_forms_tags %}<form class="cv-form" method="post">{% crispy form %}</form>')
    assert_owned_form_markup(caller.render(_context(form)))
    custom = NameForm()
    custom.helper = FormHelper()
    html = standalone.render(_context(custom))
    assert html.count("<form") == 1
    assert html.count('name="csrfmiddlewaretoken"') == 1
    custom.helper.form_method = "get"
    html = standalone.render(_context(custom))
    assert html.count("<form") == 1
    assert "csrfmiddlewaretoken" not in html


@pytest.mark.parametrize("migrated", [False, True])
def test_copied_inner_template_must_use_selected_helper(migrated):
    template = (
        "{% load crispy_forms_tags %}{% crispy form cv_form_helper %}"
        if migrated
        else "{% load crispy_forms_tags %}{% crispy form form.helper %}"
    )
    form = NameForm()
    form.helper = _helper()
    with _theme_templates({"crud_views/tags/form.html": template}):
        html = Template(
            '{% load crud_views %}<form class="cv-form">{% csrf_token %}{% cv_render_form %}</form>'
        ).render(_context(form))
    if migrated:
        assert_owned_form_markup(html)
    else:
        assert html.count('name="csrfmiddlewaretoken"') == 2


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("form_action", "missing-route:secret"),
        ("form_id", "private-id"),
        ("attrs", {"data-private": "secret"}),
        ("form_class", "private-class"),
        ("form_method", "get"),
    ],
)
def test_helper_wrapper_diagnostics(strict, option, value, caplog):
    helper = _helper()
    setattr(helper, option, value)
    form = NameForm()
    form.helper = helper
    snapshot = dict(helper.__dict__)
    layout_fields = list(helper.layout.fields)
    context = _context(form)
    layers = [dict(layer) for layer in context.dicts]
    with override_settings(CRUD_VIEWS_STRICT=strict):
        if strict:
            with pytest.raises(ImproperlyConfigured, match=option) as error:
                cv_render_form(context)
            message = str(error.value)
        else:
            for _ in range(2):
                html = cv_render_form(context)
                assert 'name="name"' in html
                assert "csrfmiddlewaretoken" not in html
                assert "<form" not in html
            message = caplog.text
            assert option in message
    assert "FormHelper" in message
    assert "page template" in message
    assert "ignored" in message
    assert "secret" not in message
    assert helper.__dict__ == snapshot
    assert helper.layout.fields == layout_fields
    assert context.dicts == layers


@pytest.mark.parametrize("strict", [False, True])
def test_ordinary_helper_defaults_and_field_options_are_quiet(strict, caplog):
    helper = _helper()
    helper.field_class = "col-8"
    helper.label_class = "col-4"
    helper.include_media = False
    helper.form_show_labels = False
    helper.form_method = "POST"  # normalized default cannot be diagnosed as explicit configuration
    form = NameForm()
    form.helper = helper
    with override_settings(CRUD_VIEWS_STRICT=strict):
        cv_render_form(_context(form))
    assert not caplog.records


def test_wrapper_diagnosis_does_not_resolve_action(monkeypatch):
    import crispy_forms.helper

    from crud_views.templatetags.crud_views import _diagnose_form_wrapper

    def forbidden(*args, **kwargs):
        raise AssertionError("diagnostics must not resolve the action")

    helper = _helper()
    helper.form_action = "not-a-route:private"
    monkeypatch.setattr(crispy_forms.helper, "reverse", forbidden)
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ImproperlyConfigured, match="form_action"):
        _diagnose_form_wrapper(helper)
