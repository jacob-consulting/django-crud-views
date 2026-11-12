from collections import OrderedDict

import pytest
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory
from django.test import RequestFactory
from pydantic import ValidationError

from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle, ValueToggle
from crud_views.lib.crispy import Column8, CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from tests.test1.app.models import Profile, ProfileItem

pytestmark = pytest.mark.django_db


def test_conditional_formset_defaults_to_skip():
    cond = ConditionalFormSet(toggle=ModelFieldToggle("with_items"))
    assert cond.on_off == "skip"


@pytest.mark.parametrize("on_off", ["skip", "purge"])
def test_value_formset_rejected(on_off):
    with pytest.raises(ValidationError, match=r"ValueToggle.*ConditionalGroup.*checkbox"):
        ConditionalFormSet(toggle=ValueToggle("kind", ["a"]), on_off=on_off)


@pytest.mark.parametrize("toggle_class", [ModelFieldToggle, UIFieldToggle])
@pytest.mark.parametrize("on_off", ["skip", "purge"])
@pytest.mark.parametrize("commit", [False, True])
def test_checkbox_formset_skip_purge_commit_contract(toggle_class, on_off, commit):
    profile = Profile.objects.create(name="checkbox contract")
    item = ProfileItem.objects.create(profile=profile, label="preserved unless purged")
    formsets, main, _ = _make(on_off, "", profile=profile)
    declaration = ConditionalFormSet(toggle=toggle_class("with_items"), on_off=on_off)
    formsets.x_formsets[0].formset.conditional = declaration
    formsets.apply_conditional(main)
    assert formsets.all_valid()
    formsets.save(commit=commit)
    assert ProfileItem.objects.filter(pk=item.pk).exists() is (not commit or on_off == "skip")


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


@pytest.mark.parametrize("edit_only", [False, True])
@pytest.mark.parametrize("can_delete", [False, True])
def test_purge_only_deletes_formset_queryset(edit_only, can_delete):
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
        can_delete=can_delete,
        edit_only=edit_only,
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
    formsets.init(request=request, form=main_form)
    formsets.apply_conditional(main_form)
    formsets.save(commit=True)

    remaining = list(ProfileItem.objects.filter(profile=profile))
    assert remaining == [keep]


@pytest.mark.parametrize("on_off", ["skip", "purge"])
@pytest.mark.parametrize("edit_only", [False, True])
@pytest.mark.parametrize("can_delete", [False, True])
def test_inactive_tree_skips_mandatory_row_policy(monkeypatch, on_off, edit_only, can_delete):
    from crud_views.lib.formsets.render_tree import XFormSet

    profile = Profile.objects.create(name="p", with_items=False)
    keep = ProfileItem.objects.create(profile=profile, label="keep")
    drop = ProfileItem.objects.create(profile=profile, label="drop")

    class DropOnly(_ItemInlineFormSet):
        def get_queryset(self):
            return super().get_queryset().filter(label="drop")

    klass = inlineformset_factory(
        Profile,
        ProfileItem,
        formset=DropOnly,
        form=_ItemForm,
        fields=["label"],
        extra=1,
        edit_only=edit_only,
        can_delete=can_delete,
    )
    tree = FormSets(
        formsets=OrderedDict(
            items=FormSet(
                title="Items",
                klass=klass,
                conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_items"), on_off=on_off),
            )
        )
    )
    prefix = f"items-{profile.pk}-0"
    post = {
        "name": "p",
        f"{prefix}-TOTAL_FORMS": "2",
        f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-0-id": "malformed",
        f"{prefix}-0-label": "forged edit",
        f"{prefix}-1-label": "forged addition",
        f"{prefix}-1-DELETE": "on",
    }
    main = _ProfileForm(cv_view=None, instance=profile, data=post)
    assert main.is_valid()
    tree.init(RequestFactory().post("/", post), main)
    tree.apply_conditional(main)

    def unexpected_policy(self):
        raise AssertionError("inactive tree entered active policy")

    monkeypatch.setattr(XFormSet, "_cv_validate_row_policy", unexpected_policy)
    assert tree.all_valid() is True
    tree.save()
    assert ProfileItem.objects.filter(pk=keep.pk).exists()
    assert ProfileItem.objects.filter(pk=drop.pk).exists() is (on_off == "skip")
    assert not ProfileItem.objects.filter(label__startswith="forged").exists()


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
    formsets.init(request=request, form=main_form)
    formsets.apply_conditional(main_form)
    assert formsets.all_valid() is True

    # Make the sibling's save blow up AFTER the purge deleted rows. Only active
    # x_formsets get save() called, so patching the class hits exactly "extras"
    # (the purged "items" formset is inactive and takes the purge branch instead).
    assert formsets.x_formsets[1].formset.original_key == "extras"

    def _boom(self, commit=True, delete=False):
        raise RuntimeError("sibling save failed")

    monkeypatch.setattr(XFormSet, "save", _boom)

    aliases: list[str] = []

    class _Base:
        # cv_atomic = False and no cv_get_atomic(): only the formset mixin's own inner
        # atomic() protects the purge here, which must hold regardless of the view setting
        cv_atomic = False

        def cv_get_db_alias(self):
            aliases.append("default")
            return "default"

        def cv_form_valid(self, context):
            context["form"].save()

    class _View(FormSetMixinBase, _Base):
        pass

    view = _View()
    with pytest.raises(RuntimeError):
        view.cv_form_valid({"form": main_form, "formsets": formsets})

    assert ProfileItem.objects.filter(profile=profile).count() == 2  # purge rolled back
    assert aliases == ["default"]  # the inner atomic() uses the routed database


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
    formsets.init(request=request, form=main_form)
    return formsets, main_form, profile


def test_fixture_helpers_build():
    """The fixture form/formset layout hooks produce crispy layouts."""
    assert _ProfileForm(cv_view=None).get_layout_fields()
    ItemFormSet = inlineformset_factory(
        Profile,
        ProfileItem,
        formset=_ItemInlineFormSet,
        form=_ItemForm,
        fields=["label"],
        extra=1,
        can_delete=True,
    )
    wrapper = FormSet(title="Items", klass=ItemFormSet, fields=["label"], pk_field="id")
    assert ItemFormSet(formset=wrapper).helper is not None


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

    formsets, _main_form, _ = _make("skip", "")
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
    formsets.init(request=request, form=main_form)

    formsets.apply_conditional(main_form)
    assert all(x.cv_active is False for x in formsets.x_formsets)
    assert formsets.all_valid() is True

    # re-rendering the ignored formset must not raise either
    html = render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
    assert 'cv-data-toggle-field="with_items"' in html


@pytest.mark.parametrize("saved", [False, True], ids=["create", "update"])
@pytest.mark.parametrize("invalid", [False, True], ids=["initial", "invalid-rerender"])
@pytest.mark.parametrize("toggle_field", ["with_items", "with_contact"])
def test_prefixed_conditional_wrapper_preserves_management_payload(saved, invalid, toggle_field):
    from html.parser import HTMLParser

    from django.template.loader import render_to_string

    class MainForm(_ProfileForm):
        class Meta(_ProfileForm.Meta):
            fields = ["name", "with_items", "with_contact"]

    class Inputs(HTMLParser):
        def __init__(self):
            super().__init__()
            self.values = {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and "name" in attrs:
                self.values[attrs["name"]] = attrs.get("value", "")

    profile = Profile.objects.create(name="p", with_items=True, with_contact=True) if saved else Profile()
    if saved:
        ProfileItem.objects.create(profile=profile, label="existing")
    item_formset = inlineformset_factory(
        Profile, ProfileItem, formset=_ItemInlineFormSet, form=_ItemForm, fields=["label"], extra=1, can_delete=True
    )
    declaration = FormSets(
        formsets={
            "items": FormSet(
                title="Items",
                klass=item_formset,
                conditional=ConditionalFormSet(toggle=ModelFieldToggle(toggle_field)),
            ),
        }
    )
    main_form = MainForm(cv_view=None, instance=profile, prefix="account")
    formsets = declaration.clone(cv_view=None)
    formsets.init(request=RequestFactory().get("/"), form=main_form)
    x_formset = formsets.x_formsets[0]
    management = {field.html_name: str(field.value()) for field in x_formset.management_form}
    if invalid:
        post = {**management, "account-name": "", f"account-{toggle_field}": "on"}
        if saved:
            row = x_formset.forms[0].form
            post.update({row.add_prefix("id"): str(row.instance.pk), row.add_prefix("label"): "existing"})
        main_form = MainForm(cv_view=None, instance=profile, prefix="account", data=post)
        assert not main_form.is_valid()
        formsets = declaration.clone(cv_view=None)
        formsets.init(request=RequestFactory().post("/", data=post), form=main_form)
        formsets.apply_conditional(main_form)
        assert formsets.x_formsets[0].cv_active

    html = render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
    assert f'cv-data-toggle-field="account-{toggle_field}"' in html
    assert formsets.x_formsets[0].cv_toggle_field == main_form.add_prefix(toggle_field)
    parsed = Inputs()
    parsed.feed(html)
    assert len(management) == 4
    assert {name: parsed.values[name] for name in management} == management


def test_unconditional_formset_projection_has_no_toggle():
    from django.template.loader import render_to_string

    formsets, main_form, _ = _make("skip", "")
    formsets["items"].conditional = None
    formsets.x_formsets.clear()
    formsets.init(request=RequestFactory().get("/"), form=main_form)
    assert formsets.x_formsets[0].cv_toggle_field == ""
    assert "cv-data-toggle-group" not in render_to_string("crud_views/formsets/formsets.html", {"formsets": formsets})
