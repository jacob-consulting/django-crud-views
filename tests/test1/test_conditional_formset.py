import pytest
from collections import OrderedDict

from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory
from django.test import RequestFactory

from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.toggle import ModelFieldToggle
from crud_views.lib.crispy import Column8, CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from tests.test1.app.models import Profile, ProfileItem

pytestmark = pytest.mark.django_db


def test_conditional_formset_defaults_to_skip():
    cond = ConditionalFormSet(toggle=ModelFieldToggle("with_items"))
    assert cond.on_off == "skip"


def test_apply_conditional_marks_top_level_inactive_when_off(profile_formsets_off):
    formsets, main_form = profile_formsets_off
    formsets.apply_conditional(main_form)
    assert all(x.cv_active is False for x in formsets.x_formsets)


def test_all_valid_true_when_off_even_with_blank_required_rows(profile_formsets_off):
    # An off formset must NOT fail validation even though its row's field is required.
    formsets, main_form = profile_formsets_off
    formsets.apply_conditional(main_form)
    assert formsets.all_valid() is True


def test_purge_deletes_existing_rows_when_off(profile_with_items_purge_off):
    formsets, main_form, profile = profile_with_items_purge_off
    assert ProfileItem.objects.filter(profile=profile).count() == 2
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)
    assert ProfileItem.objects.filter(profile=profile).count() == 0


def test_skip_leaves_existing_rows_when_off(profile_with_items_skip_off):
    formsets, main_form, profile = profile_with_items_skip_off
    assert ProfileItem.objects.filter(profile=profile).count() == 2
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)
    assert ProfileItem.objects.filter(profile=profile).count() == 2


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _ProfileForm(CrispyModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_items"]

    def get_layout_fields(self):
        return [Row(Column8("name"))]


class _ItemForm(CrispyModelForm):
    class Meta:
        model = ProfileItem
        fields = ["label"]


class _ItemInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("label"), self.form_control_col4)]


def _make(on_off, with_contact_value, profile=None, items=()):
    # Add a transient model field for the toggle on Profile via a UI toggle would
    # require a form field; here we reuse a real BooleanField "with_items".
    ItemFormSet = inlineformset_factory(
        Profile,
        ProfileItem,
        formset=_ItemInlineFormSet,
        form=_ItemForm,
        fields=["label"],
        extra=1,
        can_delete=True,
    )
    formsets = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=ItemFormSet,
                fields=["label"],
                pk_field="id",
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off=on_off),
            )
        )
    )
    rf = RequestFactory()
    post = {
        "name": "p",
        "with_items": with_contact_value,
        "items-TOTAL_FORMS": "1",
        "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "0",
        "items-MAX_NUM_FORMS": "1000",
        "items-0-label": "",  # blank required row
    }
    request = rf.post("/", data=post)
    main_form = _ProfileForm(cv_view=None, data=post, instance=profile)
    main_form.is_valid()
    formsets = formsets.clone(cv_view=None)
    formsets.init(request=request, form=main_form, instance=profile)
    return formsets, main_form, profile


@pytest.fixture
def profile_formsets_off():
    formsets, main_form, _ = _make("skip", "")  # with_items off
    return formsets, main_form


@pytest.fixture
def profile_with_items_purge_off():
    profile = Profile.objects.create(name="p", with_items=False)
    ProfileItem.objects.create(profile=profile, label="a")
    ProfileItem.objects.create(profile=profile, label="b")
    formsets, main_form, _ = _make("purge", "", profile=profile)
    return formsets, main_form, profile


@pytest.fixture
def profile_with_items_skip_off():
    profile = Profile.objects.create(name="p", with_items=False)
    ProfileItem.objects.create(profile=profile, label="a")
    ProfileItem.objects.create(profile=profile, label="b")
    formsets, main_form, _ = _make("skip", "", profile=profile)
    return formsets, main_form, profile


def test_formsets_html_marks_conditional_block():
    from django.template.loader import render_to_string

    formsets, main_form, _ = _make("skip", "")
    html = render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
    assert 'cv-data-toggle-field="with_items"' in html
    assert "crud_views/js/toggle.js" in html
