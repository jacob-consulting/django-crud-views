from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any, OrderedDict as OrderedDictType, List, Iterable, Tuple, ForwardRef, Literal
from typing import Dict, Type, Self

from crud_views.lib.view import CrudView
from django.core.exceptions import ValidationError
from django.forms.forms import BaseForm
from django.forms.models import ModelForm, BaseInlineFormSet
from django.http.request import HttpRequest
from django.template.loader import render_to_string
from ordered_model.models import OrderedModel
from pydantic import BaseModel, Field, model_validator
from enum import Enum, IntEnum

from pydantic import BaseModel, ValidationError

from .x import XForm, XFormSet


class FormSet(BaseModel, arbitrary_types_allowed=True):
    class PK(str, Enum):
        INT = r"\d+"
        UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"

    key: str | None = None
    original_key: str | None = None
    title: str | None = None
    fields: List[str]  # todo: get from formset klass ?
    pk_field: str  # todo: get from formset klass ?
    cv_view: CrudView | None = None
    parent: Self | None = None
    klass: Type[BaseInlineFormSet]
    children: Dict[str, Self] = Field(default_factory=lambda: OrderedDict())
    path: str | None = None
    pk: PK = PK.INT

    def __str__(self):
        return f"FormSet({self.title})"

    __repr__ = __str__

    @model_validator(mode="after")
    def validate_formset(self) -> Self:

        from .inline_formset import BaseInlineFormSet

        if self.klass.can_order:
            if not issubclass(self.klass.model, OrderedModel):
                raise ValidationError(f"FormSet '{self.key}' model not a subclass of OrderedModel "
                                      f"but formset.can_order is True")

        if not issubclass(self.klass, BaseInlineFormSet):
            raise ValidationError(f"FormSet '{self.key}' klass not a subclass of BaseInlineFormSet")

        return self

    @property
    def can_delete(self) -> bool:
        return self.klass.can_delete

    @property
    def can_delete_extra(self) -> bool:
        return self.klass.can_delete_extra

    @property
    def can_order(self) -> bool:
        return self.klass.can_order

    @property
    def edit_only(self) -> bool:
        return self.klass.edit_only

    @property
    def hierarchy(self) -> List[Self]:
        if self.parent is None:
            return [self.original_key]
        return self.parent.hierarchy + [self.original_key]

    def init(self,
             request: HttpRequest,
             forms: List[BaseForm],
             index: int = 0,
             parent: XForm | None = None,
             parent_prefix: str | None = None,
             level: int = 0) -> Iterable[XFormSet]:
        """
        Initialize the formset and all its children.
        This will be called recursively for all children.
        While iterating over the formset hierarchy it will create
            - a XFormSet instance for each formset
            - and a XForm instance for each form
        The X-Elements can be used to render the formsets in the template.
        """

        self.path = request.path

        # get parent prefix with -
        parent_prefix_ = f"{parent_prefix}-" if parent_prefix else ""

        for i, form in enumerate(forms):

            prefix_key = f"{parent_prefix_}{form.instance.pk}-{index}"
            prefix = f"{self.key}-{prefix_key}"

            kwargs = {
                "formset": self,
                "instance": form.instance,
                "prefix": prefix,
                "parent_form": form if level > 0 else None,  # todo
                # "form_kwargs": {"cv_view": None} # TODO HACK!!
            }
            if request.POST:
                kwargs["data"] = request.POST
                kwargs["files"] = request.FILES
            formset_instance = self.klass(**kwargs)

            x_formset = XFormSet(
                level=level,
                prefix_key=prefix_key,
                instance=formset_instance,
                formset=self,
                parent=parent,
                management_form=formset_instance.management_form
            )

            for formset_instance_form_index, formset_instance_form in enumerate(formset_instance.forms):
                formset_instance_form_prefix_key = f"{prefix_key}-{formset_instance_form_index}"
                x_form = XForm(
                    level=level,
                    prefix_key=formset_instance_form_prefix_key,
                    form=formset_instance_form,
                    parent=x_formset
                )
                x_formset.forms.append(x_form)

                for index, (key, child_formset) in enumerate(self.children.items()):
                    x_formsets = child_formset.init(
                        request=request,
                        forms=[x_form.form],
                        level=level + 1,
                        parent=x_form,
                        parent_prefix=formset_instance_form_prefix_key,
                        index=index
                    )
                    x_form.formsets.extend(list(x_formsets))

            yield x_formset

    def template(self,
                 pk: int | None,
                 index: int,
                 force_form_index: int | None = None,
                 parent_prefix: str | None = None,
                 level: int = 0,
                 parent: XForm | None = None
                 ) -> Iterable[XFormSet]:
        """
        Similar to init, but this will be called to render the template.
        Yes, it's similar to init but not the same.
        """

        # get parent prefix with -
        parent_prefix_ = f"{parent_prefix}-" if parent_prefix else ""

        prefix_key = f"{parent_prefix_}{pk}-{index}"
        prefix = f"{self.key}-{prefix_key}"

        kwargs = {
            "formset": self,
            "prefix": prefix
        }
        formset_instance = self.klass(**kwargs)

        x_formset = XFormSet(
            level=level,
            prefix_key=prefix_key,
            instance=formset_instance,
            formset=self,
            parent=parent,
            management_form=formset_instance.management_form,
            start_at_rows=True if level == 0 else False
        )

        # get the forms
        forms = formset_instance.forms
        if level == 0:
            assert force_form_index is not None, "force_form_index is required"
            # in first template level we only need the first form
            form = formset_instance.forms[0]
            # hack the form prefix, so it matches the insert position
            # this is fine, we do not need to use the pk format here,
            # because we only split away the form-index which is the last value
            form_prefix = form.prefix.rsplit("-", 1)[0] + f"-{force_form_index}"
            form.prefix = form_prefix
            forms = [form]
            # todo: limit number of formset_instance.forms to 1 ?

        for formset_instance_form_index, formset_instance_form in enumerate(forms):

            # force the form index on level 0
            form_index = force_form_index if level == 0 else formset_instance_form_index
            formset_instance_form_prefix_key = f"{prefix_key}-{form_index}"

            x_form = XForm(
                level=level,
                prefix_key=formset_instance_form_prefix_key,
                form=formset_instance_form,
                formset=self,
                # instance=formset_instance,
                parent=x_formset
            )
            x_formset.forms.append(x_form)

            for index, (key, child_formset) in enumerate(self.children.items()):
                x_formsets = child_formset.template(
                    pk=None,  # all sub-forms are new, so they have no pk
                    index=index,
                    level=level + 1,
                    parent=x_form,
                    parent_prefix=formset_instance_form_prefix_key,
                )
                x_form.formsets.extend(list(x_formsets))

        yield x_formset

    def is_valid(self) -> Iterable[Tuple[Any, bool]]:
        for instance in self.instances:
            yield instance, instance.is_valid()
        for formset in self.children.values():
            yield from formset.is_valid()

    def save(self, commit: bool = True):
        for instance in self.instances:
            instance.save(commit=commit)
        for formset in self.children.values():
            formset.save(commit=commit)

    def patch(self, cv_view: CrudView):
        self.cv_view = cv_view
        for formset in self.children.values():
            formset.parent = self
            formset.patch(cv_view)


class FormSets(BaseModel, arbitrary_types_allowed=True):
    formsets: OrderedDictType[str, FormSet]
    cv_view: CrudView | None = None
    x_formsets: List[XFormSet] = Field(default_factory=lambda: list())
    js_data: dict = Field(default_factory=lambda: dict())
    scripts: bool = True

    @model_validator(mode='before')
    @classmethod
    def check_keys(cls, data: Any) -> Any:
        formsets = data.get("formsets", dict())
        for key in formsets.keys():
            if re.match(r"^[a-z\-]+$", key) is None:
                raise ValueError(f"Formset key must contain only lowercase letters and slashes, got {key}")
        return data

    @model_validator(mode='after')
    def apply_hierarchy(self) -> Self:
        # todo: check this
        def apply_key(formset: FormSet, key: str, original_key: str, parent: FormSet | None = None):
            formset.original_key = original_key
            if formset.key is None:
                formset.key = key
                if parent:
                    formset.parent = parent
            for child_key, child_formset in formset.children.items():
                apply_key(child_formset, key=f"{key}-{child_key}", original_key=child_key, parent=formset)

        for key, formset in self.formsets.items():
            apply_key(formset, key=key, original_key=key)

        return self

    # Expose dict-like methods for convenience
    def items(self):
        return self.formsets.items()

    def keys(self):
        return self.formsets.keys()

    def values(self):
        return self.formsets.values()

    def get(self, key, default=None):
        return self.formsets.get(key, default)

    def __getitem__(self, key):
        return self.formsets[key]

    def __iter__(self):
        return iter(self.formsets)

    def is_valid(self) -> Iterable[Tuple[Any, bool]]:
        for x_formset in self.x_formsets:
            yield from x_formset.is_valid()

    def save(self, commit: bool = True):
        for x_formset in self.x_formsets:
            x_formset.save(commit=commit)

    def init(self, request: HttpRequest, form: ModelForm, instance, with_template: bool = True):
        for key, formset in self.items():
            x_formsets = list(formset.init(request=request, forms=[form]))
            self.x_formsets.extend(x_formsets)

    def init_js_data(self, view):
        data = dict(
            path=view.request.path,
        )
        self.js_data = data

    def get_template(self, key_path: List[str], pk: int, num: int, parent_prefix=None):
        formset = None
        for level, key in enumerate(key_path):
            if level == 0:
                formset = self.get(key)
            else:
                formset = formset.children[key]

        x_formsets = list(formset.template(index=0, parent_prefix=parent_prefix, force_form_index=num, pk=pk))
        assert len(x_formsets) == 1
        x_formset = x_formsets[0]
        data = dict(x_formset=x_formset)

        rows = [form.prefix for form in x_formset.forms]
        html = render_to_string("crud_views/formsets/formset.html", data)
        data = dict(rows=rows, html=html)
        return data

    def clone(self, cv_view: CrudView) -> Self:
        formsets = self.model_copy(deep=True)
        formsets.cv_view = cv_view
        for key, formset in formsets.items():
            formset.patch(cv_view)
        return formsets
