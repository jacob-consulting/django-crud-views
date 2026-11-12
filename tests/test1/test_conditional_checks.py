from collections import OrderedDict
from types import SimpleNamespace

import pytest
from django import forms
from django.forms.models import inlineformset_factory

from crud_views import checks
from crud_views.checks import _conditional_messages, check_conditional
from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle, ValueToggle
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from crud_views.lib.views import CreateViewPermissionRequired, UpdateViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Profile, ProfileItem

# ── one-off ViewSet + view registered at import time via metaclass ────────────
_cv_profile_check = ViewSet(model=Profile, name="profile_check")


class _AllFieldsForm(ConditionalGroupFormMixin, forms.ModelForm):
    """ModelForm with Meta.fields = '__all__' and a ModelFieldToggle group.

    Under the old check_conditional code:
        declared = set(getattr(getattr(form_class, "_meta", None), "fields", []) or [])
    set("__all__") → {'_', 'a', 'l'} so 'with_contact' was flagged missing → false-positive E311.
    """

    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_contact"),
            fields=["email", "phone"],
            required=["email"],
        )
    ]

    class Meta:
        model = Profile
        fields = "__all__"


class _ProfileCreateView(CreateViewPermissionRequired):
    cv_viewset = _cv_profile_check
    form_class = _AllFieldsForm


class _ItemInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        from crispy_forms.layout import Row

        from crud_views.lib.crispy import Column8

        return [Row(Column8("label"), self.form_control_col4)]


_ItemFormSet = inlineformset_factory(
    Profile,
    ProfileItem,
    formset=_ItemInlineFormSet,
    fields=["label"],
    extra=1,
    can_delete=True,
)


class _ProfileFormsetOnlyForm(forms.ModelForm):
    """Deliberately omits 'with_items' — the toggle used below is never declared."""

    class Meta:
        model = Profile
        fields = ["name"]


_cv_profile_formset_check = ViewSet(model=Profile, name="profile_formset_check")


class _ProfileFormsetCreateView(CreateViewPermissionRequired):
    cv_viewset = _cv_profile_formset_check
    form_class = _ProfileFormsetOnlyForm
    cv_formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=_ItemFormSet,
                fields=["label"],
                pk_field="id",
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items")),
            )
        )
    )


class _ProfileFormsetUpdateView(UpdateViewPermissionRequired):
    """Second view sharing form_class + cv_formsets with the create view above —
    the shared configuration must be reported once, not once per view."""

    cv_viewset = _cv_profile_formset_check
    form_class = _ProfileFormsetOnlyForm
    cv_formsets = _ProfileFormsetCreateView.cv_formsets


# ── UIFieldToggle on a formset: never injected unless a group on the form does it ──
_cv_profile_ui_formset_check = ViewSet(model=Profile, name="profile_ui_formset_check")


class _ProfileUIFormsetForm(forms.ModelForm):
    """No ConditionalGroupFormMixin — nothing injects 'with_ui_items'."""

    class Meta:
        model = Profile
        fields = ["name"]


class _ProfileUIFormsetCreateView(CreateViewPermissionRequired):
    cv_viewset = _cv_profile_ui_formset_check
    form_class = _ProfileUIFormsetForm
    cv_formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=_ItemFormSet,
                fields=["label"],
                pk_field="id",
                conditional=ConditionalFormSet(toggle=UIFieldToggle("with_ui_items")),
            )
        )
    )


_cv_profile_shared_toggle_check = ViewSet(model=Profile, name="profile_shared_toggle_check")


class _ProfileSharedToggleForm(ConditionalGroupFormMixin, forms.ModelForm):
    """A group's UIFieldToggle IS injected by the mixin, so a formset reusing the
    same toggle name is legitimately satisfied."""

    cv_conditional_groups = [
        ConditionalGroup(toggle=UIFieldToggle("with_shared"), fields=["email"]),
    ]

    class Meta:
        model = Profile
        fields = ["name", "email"]


class _ProfileSharedToggleCreateView(CreateViewPermissionRequired):
    cv_viewset = _cv_profile_shared_toggle_check
    form_class = _ProfileSharedToggleForm
    cv_formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=_ItemFormSet,
                fields=["label"],
                pk_field="id",
                conditional=ConditionalFormSet(toggle=UIFieldToggle("with_shared")),
            )
        )
    )


# ── purge on a formset that forbids row deletion ──────────────────────────────
_PurgeNoDeleteFormSet = inlineformset_factory(
    Profile,
    ProfileItem,
    formset=_ItemInlineFormSet,
    fields=["label"],
    extra=1,
    can_delete=False,
)

_cv_profile_purge_conflict_check = ViewSet(model=Profile, name="profile_purge_conflict_check")


class _ProfilePurgeConflictForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_items"]


class _ProfilePurgeConflictCreateView(CreateViewPermissionRequired):
    cv_viewset = _cv_profile_purge_conflict_check
    form_class = _ProfilePurgeConflictForm
    cv_formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=_PurgeNoDeleteFormSet,
                fields=["label"],
                pk_field="id",
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off="purge"),
            )
        )
    )


def test_fixture_formset_helper_builds():
    """The fixture formset's crispy helper builds from its layout hook."""
    wrapper = _ProfileFormsetCreateView.cv_formsets["items"]
    assert _ItemFormSet(formset=wrapper).helper is not None


def test_missing_toggle_field_on_formset_conditional_flags_e311():
    """A ConditionalFormSet toggle absent from the parent form must be E311, not silently ignored.

    Regression test: check_conditional() used to validate ConditionalGroup toggles only,
    never ConditionalFormSet toggles, even though this was documented as covered. A typo'd
    toggle field would pass checks and then silently behave as permanently-off at runtime.
    """
    messages = check_conditional()
    e311_msgs = [m for m in messages if m.id == "crud_views.E311"]
    assert any("with_items" in m.msg and "_ProfileFormsetOnlyForm" in m.msg for m in e311_msgs), e311_msgs


def test_no_e311_with_all_fields():
    """check_conditional must NOT fire E311 when Meta.fields = '__all__'.

    This test exercises the full registry traversal (unlike the _conditional_messages
    unit tests above) and would FAIL under the old set(_meta.fields) code but PASS
    with the fix that uses base_fields.keys() instead.
    """
    messages = check_conditional()
    e311_msgs = [m for m in messages if m.id == "crud_views.E311" and "_AllFieldsForm" in m.msg]
    assert e311_msgs == [], f"False-positive E311 fired: {e311_msgs}"


def test_shared_form_class_reports_e311_once():
    """Create + Update views sharing the same form/formsets config must yield ONE
    message for the shared misconfiguration, not one per view."""
    messages = check_conditional()
    matching = [
        m
        for m in messages
        if m.id == "crud_views.E311" and "with_items" in m.msg and "_ProfileFormsetOnlyForm" in m.msg
    ]
    assert len(matching) == 1, matching


def test_ui_toggle_on_formset_without_declared_field_flags_e311():
    """A UIFieldToggle on a ConditionalFormSet is NOT auto-injected — only
    ConditionalGroupFormMixin injects group toggles. If the parent form neither
    declares the field nor injects it via a group, the toggle is permanently off
    (and with purge that means silent data loss), so E311 must fire."""
    messages = check_conditional()
    e311_msgs = [m for m in messages if m.id == "crud_views.E311"]
    assert any("with_ui_items" in m.msg and "_ProfileUIFormsetForm" in m.msg for m in e311_msgs), e311_msgs


def test_group_injected_ui_toggle_satisfies_formset_e311():
    """A formset toggle that a ConditionalGroup on the same form injects is fine."""
    messages = check_conditional()
    offending = [m for m in messages if m.id == "crud_views.E311" and "with_shared" in m.msg]
    assert offending == [], offending


def test_purge_with_can_delete_false_warns_w321():
    """purge bulk-deletes rows even when the formset itself forbids deletion
    (can_delete=False / edit_only=True) — warn about the contradiction."""
    messages = check_conditional()
    w321 = [m for m in messages if m.id == "crud_views.W321"]
    assert any("items" in m.msg for m in w321), messages


def test_purge_conflict_message_formatting():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[],
        unsupported_clears=[],
        purge_conflicts=[("items", "can_delete=False")],
    )
    assert any(m.id == "crud_views.W321" for m in msgs)


def test_nested_conditional_formset_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[("child", ConditionalFormSet(toggle=ModelFieldToggle("x")))],
        missing_toggles=[],
        unsupported_clears=[],
    )
    assert any(m.id == "crud_views.E310" for m in msgs)


def test_missing_toggle_field_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[("SomeForm", "with_x")],
        unsupported_clears=[],
    )
    assert any(m.id == "crud_views.E311" for m in msgs)


def test_unsupported_clear_is_configuration_error():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[],
        unsupported_clears=[("SomeForm", "enabled", "email")],
    )
    assert any(m.id == "crud_views.E312" and "empty_values" in m.hint for m in msgs)


# ── registry-level branches, run against an isolated fake registry ────────────
# Real ViewSets register globally at import time; these scenarios would leak
# warnings into other tests, so check_conditional() walks a stand-in registry.


def _fake_formset(conditional=None, children=None, can_delete=True, edit_only=False):
    return SimpleNamespace(
        conditional=conditional,
        children=children or {},
        klass=SimpleNamespace(can_delete=can_delete, edit_only=edit_only),
    )


def _run_check_with(monkeypatch, form_class, formsets=None):
    view = SimpleNamespace(form_class=form_class, cv_formsets=formsets)
    viewset = SimpleNamespace(get_all_views=lambda: {"create": view})
    monkeypatch.setattr(checks, "_REGISTRY", {"fake": viewset})
    return check_conditional()


class _NameWithItemsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_items"]


def test_conditional_on_nested_child_formset_flags_e310(monkeypatch):
    child = _fake_formset(conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items")))
    top = _fake_formset(children={"sub": child})
    messages = _run_check_with(monkeypatch, _NameWithItemsForm, {"items": top})
    e310 = [m for m in messages if m.id == "crud_views.E310"]
    assert len(e310) == 1, messages
    assert "items-sub" in e310[0].msg, messages


def test_purge_with_edit_only_warns_w321(monkeypatch):
    fs = _fake_formset(
        conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off="purge"),
        edit_only=True,
    )
    messages = _run_check_with(monkeypatch, _NameWithItemsForm, {"items": fs})
    w321 = [m for m in messages if m.id == "crud_views.W321"]
    assert len(w321) == 1, messages
    assert "edit_only=True" in w321[0].msg, messages


class _UndeclaredModelToggleGroupForm(forms.ModelForm):
    cv_conditional_groups = [ConditionalGroup(toggle=ModelFieldToggle("not_on_form"), fields=["email"])]

    class Meta:
        model = Profile
        fields = ["name", "email"]


def test_group_model_toggle_missing_from_form_flags_e311(monkeypatch):
    messages = _run_check_with(monkeypatch, _UndeclaredModelToggleGroupForm)
    e311 = [m for m in messages if m.id == "crud_views.E311"]
    assert len(e311) == 1, messages
    assert "not_on_form" in e311[0].msg, messages


class _NonNullableClearGroupForm(forms.ModelForm):
    cv_conditional_groups = [
        ConditionalGroup(toggle=ModelFieldToggle("with_contact"), fields=["name", "email", "no_such_field"])
    ]

    class Meta:
        model = Profile
        fields = ["name", "email", "with_contact"]


def test_unsupported_nonblank_text_errors_and_skips_unknown_fields(monkeypatch):
    messages = _run_check_with(monkeypatch, _NonNullableClearGroupForm)
    errors = [m for m in messages if m.id == "crud_views.E312"]
    assert len(errors) == 1, messages
    assert "name" in errors[0].msg and "with_contact" in errors[0].msg, messages
    assert not any(m.id == "crud_views.W320" for m in messages)


def test_group_field_with_empty_value_does_not_warn_w320(monkeypatch):
    class _Form(forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(toggle=ModelFieldToggle("with_contact"), fields=["name"], empty_values={"name": "-"})
        ]

        class Meta:
            model = Profile
            fields = ["name", "with_contact"]

    messages = _run_check_with(monkeypatch, _Form)
    assert not [m for m in messages if m.id == "crud_views.W320"], messages


def test_inline_namespaces_and_nested_custom_classes_are_independent(monkeypatch):
    class Main(ConditionalGroupFormMixin, forms.Form):
        main_only = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("main_injected"), ["main_only"])]

        def __init__(self, *args, **kwargs):
            raise AssertionError("startup must not instantiate forms")

    class ValidInline(ConditionalGroupFormMixin, forms.Form):
        inline_toggle = forms.BooleanField(required=False)
        inline_only = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ModelFieldToggle("inline_toggle"), ["inline_only"])]

    class InvalidInline(ConditionalGroupFormMixin, forms.Form):
        unsupported = forms.JSONField()
        cv_conditional_groups = [
            ConditionalGroup(ModelFieldToggle("main_only"), ["unsupported"]),
            ConditionalGroup(ModelFieldToggle("main_injected"), []),
            ConditionalGroup(ModelFieldToggle("inline_toggle"), []),
        ]

    def declaration(form_class, children=None):
        # A real native custom formset subclass, not the library's InlineFormSet.
        class Custom(forms.BaseInlineFormSet):
            form = form_class
            can_delete = True
            edit_only = False

        return SimpleNamespace(klass=Custom, children=children or {}, conditional=None)

    first = declaration(ValidInline, {"nested": declaration(InvalidInline)})
    second = declaration(InvalidInline)
    for declarations in ({"first": first, "second": second}, {"second": second, "first": first}):
        messages = _run_check_with(monkeypatch, Main, declarations)
        e311 = [m for m in messages if m.id == "crud_views.E311"]
        assert len(e311) == 3, messages
        assert all("InvalidInline" in m.msg for m in e311)
        assert all(any(name in m.msg for m in e311) for name in ("main_only", "main_injected", "inline_toggle"))
        e312 = [m for m in messages if m.id == "crud_views.E312"]
        assert len(e312) == 1, messages
        assert all(name in e312[0].msg for name in ("InvalidInline", "main_only", "unsupported"))


@pytest.mark.parametrize("empty", [False, None, "", []])
def test_custom_field_explicit_falsy_override_resolves_static_error(monkeypatch, empty):
    class Custom(forms.CharField):
        pass

    class CustomForm(ConditionalGroupFormMixin, forms.Form):
        value = Custom()
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("enabled"), ["value"])]

    messages = _run_check_with(monkeypatch, CustomForm)
    assert len([m for m in messages if m.id == "crud_views.E312"]) == 1
    CustomForm.cv_conditional_groups[0].empty_values["value"] = empty
    assert _run_check_with(monkeypatch, CustomForm) == []


def test_supported_model_pairs_and_disabled_custom_field_have_no_warning(monkeypatch):
    from tests.test1.app.models import ConditionalPersistenceRecord

    class Supported(ConditionalGroupFormMixin, forms.ModelForm):
        protected = forms.JSONField(disabled=True)
        cv_conditional_groups = [
            ConditionalGroup(UIFieldToggle("enabled"), ["flag", "blank_text", "tags", "protected"])
        ]

        class Meta:
            model = ConditionalPersistenceRecord
            fields = ["flag", "blank_text", "tags"]

    assert _run_check_with(monkeypatch, Supported) == []


@pytest.mark.parametrize("name", ["parent", "number", "blank_text"])
def test_unsupported_model_pair_uses_shared_resolver(monkeypatch, name):
    from tests.test1.app.models import ConditionalPersistenceRecord

    class CustomModelField(forms.CharField):
        pass

    class Unsupported(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("enabled"), [name])]

        class Meta:
            model = ConditionalPersistenceRecord
            fields = [name]

    if name == "number":
        monkeypatch.setattr(ConditionalPersistenceRecord._meta.get_field(name), "null", False)
    elif name == "blank_text":
        Unsupported.base_fields[name] = CustomModelField()
    messages = _run_check_with(monkeypatch, Unsupported)
    assert len([m for m in messages if m.id == "crud_views.E312" and name in m.msg]) == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_value_group_checks_conflicts_deduplicated(monkeypatch, reverse):
    class Conflicting(ConditionalGroupFormMixin, forms.Form):
        kind = forms.ChoiceField(choices=[("a", "A")])
        detail = forms.CharField()
        cv_conditional_groups = [
            ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"]),
            ConditionalGroup(UIFieldToggle("enabled"), ["detail"]),
        ][:: -1 if reverse else 1]

        def __init__(self, *args, **kwargs):
            raise AssertionError("startup must not construct forms")

    view = SimpleNamespace(form_class=Conflicting, cv_formsets=None)
    monkeypatch.setattr(
        checks, "_REGISTRY", {"fake": SimpleNamespace(get_all_views=lambda: {"create": view, "update": view})}
    )
    messages = check_conditional()
    errors = [message for message in messages if message.id == "crud_views.E313"]
    assert len(errors) == 1, messages
    assert all(name in errors[0].msg for name in ("Conflicting", "kind", "detail"))
    assert errors[0].hint


@pytest.mark.parametrize("unsupported", ["callable", "relation", "widget", "coercion", "token"])
@pytest.mark.django_db
def test_value_group_checks_unsupported_without_queries(monkeypatch, django_assert_num_queries, unsupported):
    def no_choices():
        raise AssertionError("startup must not evaluate callable choices")

    fields = {
        "callable": forms.ChoiceField(choices=no_choices),
        "relation": forms.ModelChoiceField(queryset=Profile.objects.all()),
        "widget": forms.ChoiceField(choices=[("a", "A")], widget=forms.SelectMultiple),
        "coercion": forms.TypedChoiceField(choices=[("a", "A")], coerce=lambda value: value),
        "token": forms.ChoiceField(choices=[("b", "B")]),
    }

    class Unsupported(ConditionalGroupFormMixin, forms.Form):
        kind = fields[unsupported]
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

        def __init__(self, *args, **kwargs):
            raise AssertionError("startup must not construct forms")

    with django_assert_num_queries(0):
        errors = _run_check_with(monkeypatch, Unsupported)
    assert len(errors) == 1 and errors[0].id == "crud_views.E313", errors
    assert "kind" in errors[0].msg


def test_value_group_checks_missing_dynamic_controller_keeps_e311(monkeypatch):
    class Dynamic(ConditionalGroupFormMixin, forms.Form):
        detail = forms.CharField()
        cv_conditional_groups = [ConditionalGroup(ValueToggle("kind", ["a"]), ["detail"])]

    errors = _run_check_with(monkeypatch, Dynamic)
    assert [error.id for error in errors] == ["crud_views.E311"]


@pytest.mark.parametrize(
    "name,supported",
    [
        ("nullable_text_choice", True),
        ("blank_text_choice", True),
        ("nullable_integer_choice", True),
        ("required_text_choice", False),
        ("required_integer_choice", False),
    ],
)
def test_choice_clear_matrix_static_admission(monkeypatch, name, supported):
    from tests.test1.app.models import ConditionalPersistenceRecord

    class ChoiceForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("enabled"), [name])]

        class Meta:
            model = ConditionalPersistenceRecord
            fields = [name]

    errors = _run_check_with(monkeypatch, ChoiceForm)
    assert [error.id for error in errors] == ([] if supported else ["crud_views.E312"])
    ChoiceForm.cv_conditional_groups[0].empty_values[name] = None
    assert _run_check_with(monkeypatch, ChoiceForm) == []


def test_choice_clear_plain_form_requires_explicit_value(monkeypatch):
    class ChoiceForm(ConditionalGroupFormMixin, forms.Form):
        value = forms.ChoiceField(choices=[("A", "A")])
        cv_conditional_groups = [ConditionalGroup(UIFieldToggle("enabled"), ["value"])]

    assert [error.id for error in _run_check_with(monkeypatch, ChoiceForm)] == ["crud_views.E312"]
    ChoiceForm.cv_conditional_groups[0].empty_values["value"] = ""
    assert _run_check_with(monkeypatch, ChoiceForm) == []
    form = ChoiceForm(data={"value": "forged"})
    assert form.is_valid() and form.cleaned_data["value"] == ""
