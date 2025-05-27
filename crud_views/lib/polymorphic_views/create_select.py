from typing import List, Type, Iterable

from django import forms
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views import generic
from polymorphic.models import PolymorphicModel

from crud_views.lib.check import CheckEitherAttribute, Check
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.polymorphic_views.utils import get_polymorphic_child_models_content_types


class PolymorphicContentTypeForm(forms.Form):
    polymorphic_ctype_id = forms.ChoiceField(label="Type", choices=[])

    def __init__(self, *args, polymorphic_ctype_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["polymorphic_ctype_id"].choices = polymorphic_ctype_choices


class PolymorphicCreateSelectView(CrudView, generic.FormView):
    template_name = "crud_views/view_create.html"
    form_class = PolymorphicContentTypeForm

    cv_key = "create_select"
    cv_object = False
    cv_path = "create/select"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.create_select_context_actions
    # todo: check, only one can be set
    cv_polymorphic_exclude: List[Type[PolymorphicModel]] | None = None
    cv_polymorphic_include: List[Type[PolymorphicModel]] | None = None

    # texts and labels
    cv_header_template: str = "crud_views/snippets/header/create_select.html"
    cv_paragraph_template: str = "crud_views/snippets/paragraph/create_select.html"
    cv_action_label_template: str = "crud_views/snippets/action/create_select.html"
    cv_action_short_label_template: str = "crud_views/snippets/action_short/create_select.html"

    cv_icon_action = "fa-regular fa-square-plus"

    #
    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckEitherAttribute(context=cls, id="E220",
                                   attribute1="cv_polymorphic_exclude",
                                   attribute2="cv_polymorphic_include",
                                   allow_none=True)

    def get_form(self, form_class=None):
        form_class = form_class if form_class else self.get_form_class()
        content_types = get_polymorphic_child_models_content_types(self.model)  # noqa
        if self.cv_polymorphic_exclude:
            content_types = {k: v for k, v in content_types.items() if k not in self.cv_polymorphic_exclude}
        elif self.cv_polymorphic_include:
            content_types = {k: v for k, v in content_types.items() if k in self.cv_polymorphic_include}
        polymorphic_ctype_choices = [(ct.id, ct.name) for ct in content_types.values()]
        form_kwargs = self.get_form_kwargs()
        form = form_class(polymorphic_ctype_choices=polymorphic_ctype_choices, **form_kwargs)
        return form

    def form_valid(self, form):
        polymorphic_ctype_id = form.cleaned_data["polymorphic_ctype_id"]
        kwargs = {"polymorphic_ctype_id": polymorphic_ctype_id}
        url = self.cv_get_url("create", extra_kwargs=kwargs)
        return HttpResponseRedirect(url)


class PolymorphicCreateSelectViewPermissionRequired(CrudViewPermissionRequiredMixin,
                                                    PolymorphicCreateSelectView):
    cv_permission = "add"
