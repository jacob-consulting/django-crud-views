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


def test_purge_respects_commit_false(profile_with_items_purge_off):
    # purge is a destructive write; with commit=False nothing must be deleted.
    formsets, main_form, profile = profile_with_items_purge_off
    assert ProfileItem.objects.filter(profile=profile).count() == 2
    formsets.apply_conditional(main_form)
    formsets.save(commit=False)
    assert ProfileItem.objects.filter(profile=profile).count() == 2


def test_purge_only_deletes_formset_queryset():
    # A formset that narrows its queryset must purge only the rows it manages,
    # never every child of the parent.
    profile = Profile.objects.create(name="p", with_items=False)
    keep = ProfileItem.objects.create(profile=profile, label="keep")
    ProfileItem.objects.create(profile=profile, label="drop")

    class _DropOnlyInlineFormSet(_ItemInlineFormSet):
        def get_queryset(self):
            return ProfileItem.objects.filter(profile=self.instance, label="drop")

    ItemFormSet = inlineformset_factory(
        Profile,
        ProfileItem,
        formset=_DropOnlyInlineFormSet,
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
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off="purge"),
            )
        )
    )
    post = {"name": "p", "with_items": ""}  # toggle off
    request = RequestFactory().post("/", data=post)
    main_form = _ProfileForm(cv_view=None, data=post, instance=profile)
    main_form.is_valid()
    formsets = formsets.clone(cv_view=None)
    formsets.init(request=request, form=main_form, instance=profile)
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)

    remaining = list(ProfileItem.objects.filter(profile=profile))
    assert remaining == [keep]


def test_purge_rolls_back_when_sibling_formset_save_fails(monkeypatch):
    """Purge is destructive, so the whole save flow must be atomic: if a sibling
    formset's save raises after the purge DELETE ran, the deletion must roll back
    instead of leaving the parent updated and the children irrecoverably gone."""
    from crud_views.lib.formsets.mixins import FormSetMixinBase
    from crud_views.lib.formsets.render_tree import XFormSet

    profile = Profile.objects.create(name="p", with_items=False)
    ProfileItem.objects.create(profile=profile, label="a")
    ProfileItem.objects.create(profile=profile, label="b")

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
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off="purge"),
            ),
            extras=FormSet(
                title="Extras",
                klass=ItemFormSet,
                fields=["label"],
                pk_field="id",
            ),
        )
    )
    extras_prefix = f"extras-{profile.pk}-0"  # top-level formset prefix: <key>-<parent pk>-<index>
    post = {
        "name": "p",
        "with_items": "",  # toggle off => purge on save
        f"{extras_prefix}-TOTAL_FORMS": "0",
        f"{extras_prefix}-INITIAL_FORMS": "0",
        f"{extras_prefix}-MIN_NUM_FORMS": "0",
        f"{extras_prefix}-MAX_NUM_FORMS": "1000",
    }
    request = RequestFactory().post("/", data=post)
    main_form = _ProfileForm(cv_view=None, data=post, instance=profile)
    assert main_form.is_valid() is True
    formsets = formsets.clone(cv_view=None)
    formsets.init(request=request, form=main_form, instance=profile)
    formsets.apply_conditional(main_form)
    assert formsets.all_valid() is True

    # Make the sibling's save blow up AFTER the purge deleted rows. Only active
    # x_formsets get save() called, so patching the class hits exactly "extras"
    # (the purged "items" formset is inactive and takes the purge branch instead).
    assert formsets.x_formsets[1].formset.original_key == "extras"

    def _boom(self, commit=True, delete=False):
        raise RuntimeError("sibling save failed")

    monkeypatch.setattr(XFormSet, "save", _boom)

    class _Base:
        def cv_form_valid(self, context):
            context["form"].save()

    class _View(FormSetMixinBase, _Base):
        pass

    with pytest.raises(RuntimeError):
        _View().cv_form_valid({"form": main_form, "formsets": formsets})

    assert ProfileItem.objects.filter(profile=profile).count() == 2  # purge rolled back


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
    # toggle.js is served by the cv_js registry (settings.javascript), not inlined here
    assert "<script" not in html
    assert "formset.js" not in html


def test_off_formset_without_management_form_does_not_crash():
    """The browser disables an off formset's inputs, so its management-form
    hidden fields are not submitted. The server must still init, validate and
    render that ignored formset without raising ManagementForm errors."""
    from django.template.loader import render_to_string

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
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off="skip"),
            )
        )
    )
    # Toggle off and NO items-* management keys (disabled inputs are not submitted).
    post = {"name": "p", "with_items": ""}
    request = RequestFactory().post("/", data=post)
    main_form = _ProfileForm(cv_view=None, data=post)
    main_form.is_valid()
    formsets = formsets.clone(cv_view=None)

    # init must not raise even though the formset's management form is absent
    formsets.init(request=request, form=main_form, instance=None)

    formsets.apply_conditional(main_form)
    assert all(x.cv_active is False for x in formsets.x_formsets)
    assert formsets.all_valid() is True

    # re-rendering the ignored formset must not raise either
    html = render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
    assert 'cv-data-toggle-field="with_items"' in html
