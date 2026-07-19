from django import forms

from crud_views.checks import _conditional_messages, check_conditional
from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.group import ConditionalGroup, ConditionalGroupFormMixin
from crud_views.lib.conditional.toggle import ModelFieldToggle
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import CreateViewPermissionRequired
from tests.test1.app.models import Profile

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


def test_no_e311_with_all_fields():
    """check_conditional must NOT fire E311 when Meta.fields = '__all__'.

    This test exercises the full registry traversal (unlike the _conditional_messages
    unit tests above) and would FAIL under the old set(_meta.fields) code but PASS
    with the fix that uses base_fields.keys() instead.
    """
    messages = check_conditional()
    e311_msgs = [m for m in messages if m.id == "crud_views.E311"]
    assert e311_msgs == [], f"False-positive E311 fired: {e311_msgs}"


def test_nested_conditional_formset_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[("child", ConditionalFormSet(toggle=ModelFieldToggle("x")))],
        missing_toggles=[],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E310" for m in msgs)


def test_missing_toggle_field_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[("SomeForm", "with_x")],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E311" for m in msgs)


def test_non_nullable_clear_warned():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[],
        non_nullable_clears=[("SomeForm", "email")],
    )
    assert any(m.id == "crud_views.W320" for m in msgs)
