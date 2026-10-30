"""IN-04: generic slug ViewSet routing does not imply slug support in formset row prefixes."""

import pytest
from django.core.exceptions import BadRequest
from django.db import models
from django.forms.models import inlineformset_factory
from django.test.utils import isolate_apps

from crud_views.lib.formsets import FormSet, FormSets


@pytest.mark.parametrize("grammar", [FormSet.PK.INT, FormSet.PK.UUID])
@isolate_apps()
def test_slug_parent_cannot_be_encoded_by_supported_fragment_grammars(grammar):
    class SlugParent(models.Model):
        id = models.SlugField(primary_key=True)

        class Meta:
            app_label = "test1"

    class SlugChild(models.Model):
        parent = models.ForeignKey(SlugParent, on_delete=models.CASCADE)
        title = models.CharField(max_length=40)

        class Meta:
            app_label = "test1"

    formset_class = inlineformset_factory(SlugParent, SlugChild, fields=["title"])
    formsets = FormSets(formsets={"children": FormSet(klass=formset_class, pk=grammar)})
    parent = SlugParent(pk="parent-with-hyphens")
    parent._state.adding = False
    with pytest.raises(BadRequest, match="pk does not match the declared formset primary key"):
        formsets._cv_validate_fragment_coordinates(
            key_path=["children"], pk=parent.pk, num="1", parent_prefix=None, root=parent
        )
