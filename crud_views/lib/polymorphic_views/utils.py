from functools import cached_property
from typing import List, Dict, Generator, Type

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.forms import ModelForm
from polymorphic.models import PolymorphicModel


def get_polymorphic_child_models(model: PolymorphicModel) -> List[Type[PolymorphicModel]]:
    """
    Get all child models of a polymorphic model.
    """
    assert issubclass(model, PolymorphicModel), "not a polymorphic model"
    def subclasses(m: Type[PolymorphicModel]) -> Generator[Type[PolymorphicModel], None, None]:
        for sm in m.__subclasses__():
            yield sm
            yield from subclasses(sm)

    child_models = list(subclasses(model))
    return child_models


def get_polymorphic_child_models_content_types(model: PolymorphicModel) -> Dict[Type[Model], ContentType]:
    child_models = get_polymorphic_child_models(model)
    content_types = ContentType.objects.get_for_models(*child_models, for_concrete_models=True)
    return content_types


class PolymorphicCrudViewMixin:
    """
    Polymorphic ViewSet mixin
    """

    # todo: rename to cv_polymorphic_forms
    polymorphic_forms: Dict[Model, ModelForm] = None

    # polymorphic_inline_formsets: Dict[Model, Dict[str, Any]] = None

    # todo: rename to cv_~
    @property
    def polymorphic_ctype_id(self) -> int:
        """
        Get the polymorphic content type id from the url kwargs
        """
        # is there a polymorphic_ctype_id from the url in the create view?
        polymorphic_ctype_id = self.kwargs.get("polymorphic_ctype_id")
        if not polymorphic_ctype_id:
            # no, get it from the object
            instance = self.get_object()  # from SingleObjectMixin
            polymorphic_ctype_id = instance.polymorphic_ctype_id
        return int(polymorphic_ctype_id)

    # todo: rename to cv_~
    @cached_property
    def polymorphic_model(self) -> Model:
        """
        Get the polymorphic model from polymorphic_ctype_id
        """
        polymorphic_ctype_id = self.polymorphic_ctype_id
        content_type = ContentType.objects.get(id=polymorphic_ctype_id)
        model = content_type.model_class()
        return model

    @property
    def model(self) -> Model:
        """
        Override the model property from the view mixin
        """
        return self.polymorphic_model

    def get_form_class(self):
        """
        Get the form class depending on the polymorphic model
        Note: this implies that object has already been set
        """

        model = self.polymorphic_model
        form = self.polymorphic_forms.get(model, None)
        if not form:
            raise ValueError(f"No form found for polymorphic model {self.object.__class__}")
        # todo: assert self.object is set
        return form

    # def get_polymorphic_inline_formsets(self):
    #     return getattr(self, "polymorphic_inline_formsets", None)
    #
    # def get_inline_formsets(self) -> Optional[Dict[str, Any]]:
    #     """
    #     Get the inline formsets with polymorphic model.
    #     Therefore, we to override the polymorphic model property.
    #     """
    #
    #     # no formsets defined?
    #     inline_formsets = self.get_polymorphic_inline_formsets()
    #     if inline_formsets is None:
    #         return None
    #
    #     if not isinstance(inline_formsets, dict):
    #         raise ValueError(f"Formsets for {self.__class__.__name__} must be a dict")
    #
    #     # get formsets for model
    #     formsets = inline_formsets.get(self.polymorphic_model)
    #     if not formsets:
    #         return None
    #
    #     # check config
    #     if not isinstance(formsets, dict):
    #         raise ValueError(f"Formsets for {self.__class__.__name__}.{self.polymorphic_model} must be a dict")
    #     for key, value in formsets.items():
    #         if not isinstance(key, str):
    #             raise ValueError(f"Formset key {key} "
    #                              f"for {self.__class__.__name__}.{self.polymorphic_model} "
    #                              f"must be a string")
    #         if not issubclass(value, forms.BaseFormSet):
    #             raise ValueError(f"Formset {key} "
    #                              f"for {self.__class__.__name__}.{self.polymorphic_model} "
    #                              f"must be a Formset")
    #
    #     # everything is fine
    #     return formsets
