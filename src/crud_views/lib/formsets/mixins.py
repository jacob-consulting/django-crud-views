from __future__ import annotations

from typing import Dict, Type, Iterable

from crud_views.lib.check import Check, CheckAttribute
from django.core.exceptions import BadRequest
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
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets_required")

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

        if num is None or not num.isdigit():
            raise BadRequest("num must be an integer")

        formsets = self.cv_get_formsets()
        if formsets is None:
            raise BadRequest("view has no formsets")

        # validate the key path before rendering
        node = formsets.get(key_path[0])
        for key in key_path[1:]:
            node = node.children.get(key) if node else None
        if node is None:
            raise BadRequest(f"unknown formset template {request.GET.get('template')}")

        data = formsets.get_template(key_path=key_path, pk=pk, num=int(num), parent_prefix=formset_parent_prefix_key)
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

        # Evaluate conditional formsets from the submitted main form (server authority).
        formsets.apply_conditional(context["form"])

        # order-independent: a child formset's clean() may add_error() to a parent form,
        # which a single-pass tally would miss. See FormSets.all_valid().
        # Evaluate eagerly (do not short-circuit on form_valid) so formset error state is
        # always populated for the re-rendered page, matching the prior behavior.
        all_formsets_valid = formsets.all_valid()
        return form_valid and all_formsets_valid

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


class FormSetMixin(FormSetMixinBase):
    cv_formsets: FormSets

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets")

    def cv_get_formsets(self) -> FormSets:
        return self.cv_formsets.clone(cv_view=self)  # noqa


class PolymorphicFormSetsViewMixin(FormSetMixinBase):
    cv_polymorphic_formsets: Dict[Type[Model], FormSets]

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()
        yield CheckAttribute(context=cls, id="E200", attribute="cv_polymorphic_formsets")

    def cv_get_formsets(self) -> FormSets | None:
        model = self.polymorphic_model

        # it is okay that a model has no formsets defined
        formsets = self.cv_polymorphic_formsets.get(model, None)
        if formsets is None:
            return None
        return formsets.clone(cv_view=self)  # noqa
