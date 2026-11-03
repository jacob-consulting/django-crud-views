from collections.abc import Iterable
from urllib.parse import urlencode

from django import forms
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views import generic
from polymorphic.models import PolymorphicModel

from crud_views.lib.check import Check, CheckEitherAttribute
from crud_views.lib.exceptions import ViewSetKeyFoundError
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.view.cancel import effective_cancel_keys, encode_cancel_state, navigation_params, read_cancel_state

from .utils import get_polymorphic_child_models_content_types


class PolymorphicContentTypeForm(forms.Form):
    polymorphic_ctype_id = forms.ChoiceField(label=_("Type"), choices=[])

    def __init__(self, *args, polymorphic_ctype_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["polymorphic_ctype_id"].choices = polymorphic_ctype_choices


class PolymorphicCreateSelectView(CrudView, generic.FormView):
    template_name = "crud_views/view_create.html"
    cv_content_template = "crud_views/view_create.content.html"
    form_class = PolymorphicContentTypeForm

    cv_key = "create_select"
    cv_object = False
    cv_path = "create/select"
    cv_success_key = "list"
    cv_cancel_keys = "auto"
    cv_context_actions = crud_views_settings.create_select_context_actions
    cv_polymorphic_exclude: list[type[PolymorphicModel]] | None = None
    cv_polymorphic_include: list[type[PolymorphicModel]] | None = None

    # texts and labels
    cv_header_template: str = "crud_views/snippets/header/create_select.html"
    cv_paragraph_template: str = "crud_views/snippets/paragraph/create_select.html"
    cv_action_label_template: str = "crud_views/snippets/action/create_select.html"
    cv_action_short_label_template: str = "crud_views/snippets/action_short/create_select.html"

    cv_icon_action = "create"
    cv_action_variant = "primary"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        yield CheckEitherAttribute(
            context=cls,
            id="E220",
            attribute1="cv_polymorphic_exclude",
            attribute2="cv_polymorphic_include",
            allow_none=True,
        )

    def get_form(self, form_class=None):
        form_class = form_class if form_class else self.get_form_class()
        content_types = get_polymorphic_child_models_content_types(self.model)
        if self.cv_polymorphic_exclude:
            content_types = {k: v for k, v in content_types.items() if k not in self.cv_polymorphic_exclude}
        elif self.cv_polymorphic_include:
            content_types = {k: v for k, v in content_types.items() if k in self.cv_polymorphic_include}
        polymorphic_ctype_choices = [(ct.id, ct.name) for ct in content_types.values()]
        form_kwargs = self.get_form_kwargs()
        return form_class(polymorphic_ctype_choices=polymorphic_ctype_choices, **form_kwargs)

    def _cv_concrete_cancel_token(self, capture, allowed):
        if capture is None or capture.origin not in allowed:
            return None
        try:
            origin_cls = self.cv_get_cls(capture.origin)
        except ViewSetKeyFoundError:
            return None
        if origin_cls.cv_object:
            return None
        # Re-encode only validated state; legacy input keeps query=None.
        return encode_cancel_state(self, capture.origin, capture.query)

    def _cv_concrete_cancel_query(self):
        concrete = self.cv_get_cls("create")
        allowed = effective_cancel_keys(concrete)
        if not allowed:
            return ""
        capture = read_cancel_state(self)
        token_name = navigation_params()[1]
        token = self._cv_concrete_cancel_token(capture, allowed)
        if token is None and (capture is not None or token_name in self.request.GET):
            # Invalid input must not become trusted absent-token input downstream.
            token = "invalid"
        # Do not forward the shared success-origin key or selector form fields.
        return "?" + urlencode({token_name: token}) if token is not None else ""

    def form_valid(self, form):
        kwargs = {"polymorphic_ctype_id": form.cleaned_data["polymorphic_ctype_id"]}
        url = self.cv_get_url("create", extra_kwargs=kwargs)
        return HttpResponseRedirect(url + self._cv_concrete_cancel_query())


class PolymorphicCreateSelectViewPermissionRequired(CrudViewPermissionRequiredMixin, PolymorphicCreateSelectView):
    cv_permission = "add"
