from __future__ import annotations

from typing import Dict, Type, Iterable

from crud_views.lib.check import Check, CheckAttribute
from django.db.models import Model
from django.forms.models import ModelForm
from django.http import JsonResponse

from .formsets import FormSets


class FormSetMixinBase:
    cv_formsets_required: bool = True

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets_required")  # todo check for type

    def get_context_data(self, **kwargs):
        """
        In formset mixin formsets need to be created to be added to the context
        """
        data = super().get_context_data(**kwargs)  # noqa
        formsets = self.cv_init_formsets(data.get("form"))
        if formsets is not None:
            data["formsets"] = formsets
        return data

    def get(self, request, *args, **kwargs):
        """
        GET also handles AJAX requests for formset templates
        """
        template = request.GET.get("template", None)
        if template:
            data = self.get_template_html(request)
            return JsonResponse(data)
        return super().get(request, *args, **kwargs)  # noqa

    def get_template_html(self, request):

        key_path = request.GET.get("template").split("|")
        pk = request.GET.get("pk", "None")
        num = request.GET.get("num")
        formset_parent_prefix_key = request.GET.get("formset_parent_prefix_key")

        formsets = self.cv_get_formsets()
        data = formsets.get_template(key_path=key_path, pk=pk, num=num, parent_prefix=formset_parent_prefix_key)
        return data

    def cv_form_is_valid(self, context: dict) -> bool:
        """
        Check if the form is valid.
        Crud Views modules may extend this method with further checks.
        """

        # the main form
        form_valid = super().cv_form_is_valid(context)

        # get the formsets
        formsets = context.get("formsets", None)
        if formsets is None:
            if self.cv_formsets_required:
                raise ValueError("Formsets are required but not defined, cv_formsets_required=True")
            else:
                return form_valid

        # formsets valid?
        formsets_valid = list(formsets.is_valid())
        all_formsets_valid = all([v for fs, v in formsets_valid])

        # form and formsets valid?
        is_valid = all([form_valid, all_formsets_valid])
        return is_valid

    def cv_form_valid(self, context: dict):
        """
        Save form and formsets
        """
        # save main form
        super().cv_form_valid(context)

        # get the formsets
        formsets = context.get("formsets", None)
        if formsets is None:
            if self.cv_formsets_required:
                raise ValueError("Formsets are required but not defined, cv_formsets_required=True")

            # nothing to do here
            return

        # save formsets
        formsets.save(commit=True)

    def cv_get_formsets(self) -> FormSets:
        return self.cv_formsets.clone(cv_view=self)  # noqa

    def cv_patch_formsets(self, formsets: FormSets):
        pass

    def cv_init_formsets(self, form: ModelForm) -> FormSets | None:
        """
        Get the inline formsets instances.
        On POST the formsets are bound to the request.POST data.
        """

        # get inline formsets
        formsets = self.cv_get_formsets()

        # if no formsets are defined, return None
        if formsets is None:
            return None

        formsets.init(request=self.request, form=form, instance=self.object)

        formsets.init_js_data(self)

        # call hook to patch the formsets
        self.cv_patch_formsets(formsets)

        return formsets

    # def cv_form_valid(self, form: ModelForm, formsets: FormSets):
    #     """
    #     Use a custom form_valid method to handle formsets because the form_valid method
    #     would recreate the formsets again
    #     """
    #
    #     with transaction.atomic():
    #         # delete first
    #         # formsets.deleted()
    #
    #         self.object = form.save(commit=True)
    #         formsets.save(commit=True)
    #
    #     return HttpResponseRedirect(self.get_success_url())  # noqa


class FormSetMixin(FormSetMixinBase):
    cv_formsets: FormSets

    # todo: checks for cv_formsets: FormSets

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets")  # todo check for type

    def cv_get_formsets(self) -> FormSets:
        return self.cv_formsets.clone(cv_view=self)  # noqa


# todo: rename, because this class name collides with django polymorphic
class PolymorphicFormSetMixin(FormSetMixinBase):
    cv_polymorphic_formsets: Dict[Type[Model], FormSets]

    # todo: checks for cv_polymorphic_formsets

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckAttribute(context=cls, id="E200", attribute="cv_polymorphic_formsets")  # todo check for type

    def cv_get_formsets(self) -> FormSets | None:
        model = self.polymorphic_model

        # it is okay that a model has no formsets defined
        if model not in self.cv_polymorphic_formsets:
            raise ValueError(f"No FormSets instance found for polymorphic model {model.__class__}")
        formsets = self.cv_polymorphic_formsets.get(model, None)
        if formsets is None:
            return None
        return formsets.clone(cv_view=self)  # noqa
