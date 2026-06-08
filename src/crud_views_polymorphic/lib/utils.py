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

    return list(subclasses(model))


def get_polymorphic_child_models_content_types(model: PolymorphicModel) -> Dict[Type[Model], ContentType]:
    child_models = get_polymorphic_child_models(model)
    content_types = ContentType.objects.get_for_models(*child_models, for_concrete_models=True)
    return content_types


class PolymorphicCrudViewMixin:
    """
    Polymorphic ViewSet mixin
    """

    polymorphic_forms: Dict[Model, ModelForm] = None

    @property
    def polymorphic_ctype_id(self) -> int:
        """
        Get the polymorphic content type id from the url kwargs
        """
        polymorphic_ctype_id = self.kwargs.get("polymorphic_ctype_id")
        if not polymorphic_ctype_id:
            instance = self.get_object()  # from SingleObjectMixin
            polymorphic_ctype_id = instance.polymorphic_ctype_id
        return int(polymorphic_ctype_id)

    @cached_property
    def polymorphic_model(self) -> Model:
        """
        Get the polymorphic model from polymorphic_ctype_id
        """
        polymorphic_ctype_id = self.polymorphic_ctype_id
        content_type = ContentType.objects.get(id=polymorphic_ctype_id)
        return content_type.model_class()

    @property
    def model(self) -> Model:
        """
        Override the model property from the view mixin
        """
        return self.polymorphic_model

    def get_form_class(self):
        """
        Get the form class depending on the polymorphic model
        """
        model = self.polymorphic_model
        form = self.polymorphic_forms.get(model, None)
        if not form:
            raise ValueError(f"No form found for polymorphic model {self.object.__class__}")
        return form
