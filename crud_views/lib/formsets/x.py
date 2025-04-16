from __future__ import annotations

import json
from typing import Any, List, Iterable, Tuple

from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from pydantic import BaseModel, Field

try:
    from polymorphic.formsets import BasePolymorphicInlineFormSet
except ImportError:
    BasePolymorphicInlineFormSet = None


class XForm(BaseModel, arbitrary_types_allowed=True):
    level: int
    prefix_key: str
    form: BaseForm
    parent: XFormSet | None = None
    formsets: List[XFormSet] = Field(default_factory=lambda: list())

    def __str__(self):
        return f"XForm(prefix={self.prefix},prefix_key={self.prefix_key},key={self.key},level={self.level})"

    __repr__ = __str__

    @property
    def key(self) -> str:
        """ return the formset key from the parent formset """
        return self.parent.key

    @property
    def prefix(self) -> str:
        """ return the form prefix """
        return self.form.prefix

    @property
    def data(self) -> dict:
        return dict(
            key=self.key,
            prefix=self.prefix,
            prefix_key=self.prefix_key,
            formset_prefix=self.parent.prefix,
            pk=str(self.parent.pk)
        )

    @property
    def json_data(self) -> str:
        return json.dumps(self.data)  # .replace('"', "'")

    def is_valid(self) -> Iterable[Tuple[Any, bool]]:
        for x_formset in self.formsets:
            yield from x_formset.is_valid()

    def save(self, commit: bool = True, delete: bool = False):
        for x_formset in self.formsets:
            x_formset.save(commit=commit, delete=delete)

    @property
    def helper(self):
        # in polymorphic formsets we need to get the helper from the form
        klass = self.parent.formset.klass
        if BasePolymorphicInlineFormSet and issubclass(klass, BasePolymorphicInlineFormSet):
            return self.form.helper

        # in no-polymorphic formsets we can get the helper from the formset
        return self.parent.instance.helper


class XFormSet(BaseModel, arbitrary_types_allowed=True):
    level: int
    prefix_key: str
    formset: Any
    instance: BaseFormSet
    management_form: Any
    forms: List[XForm] = Field(default_factory=lambda: list())
    parent: XForm | None = None
    start_at_rows: bool = False  # todo: bad name, improve

    def __str__(self):
        return f"XFormSet({self.prefix},{self.prefix_key},{self.level})"

    __repr__ = __str__

    @property
    def has_parent(self) -> bool:
        return self.parent is not None

    @property
    def key(self) -> str:
        """ return the formset key """
        return self.formset.key

    @property
    def pk(self) -> str:
        """ return the formset key """
        return self.formset.pk

    @property
    def prefix(self) -> str:
        """ return the formset prefix KEY-SUFFIX """
        return f"{self.key}-{self.prefix_key}"

    @property
    def parent_prefix(self) -> str:
        if self.has_parent:
            return self.parent.prefix
        return ""

    @property
    def parent_prefix_key(self) -> str:
        if self.has_parent:
            return self.parent.prefix_key
        return ""

    @property
    def hierarchy(self) -> List[str]:
        return self.formset.hierarchy

    @property
    def hierarchy_str(self) -> str:
        return "|".join(self.hierarchy)

    @property
    def title(self) -> str:
        return self.formset.title

    @property
    def key(self) -> str:
        return self.formset.key

    @property
    def has_pre_col(self) -> bool:
        return self.level > 0

    @property
    def col(self) -> int:
        return 11 if self.level > 0 else 12

    @property
    def col_pre(self) -> int:
        return 1 if self.level > 0 else 0

    @property
    def css_col(self) -> str:
        return f"col-{self.col}"

    @property
    def css_col_pre(self) -> str:
        return f"col-{self.col_pre}"

    @property
    def data(self) -> dict:
        return dict(
            key=self.key,
            prefix=self.prefix,
            prefix_key=self.prefix_key,
            hierarchy=self.hierarchy,
            parent_prefix=self.parent_prefix,
            parent_prefix_key=self.parent_prefix_key,
            can_delete=self.formset.can_delete,
            can_delete_extra=self.formset.can_delete_extra,
            can_order=self.formset.can_order,
            edit_only=self.formset.edit_only,
            path=self.formset.path,
            fields=self.formset.fields,
            pk_field=self.formset.pk_field,
            pk=self.pk.value,
        )

    @property
    def json_data(self) -> str:
        return json.dumps(self.data)

    def is_valid(self) -> Iterable[Tuple[Any, bool]]:
        yield self, self.instance.is_valid()
        for x_form in self.forms:
            yield from x_form.is_valid()

    def save(self, commit: bool = True, delete=False):
        """
        Nested save and delete
        """

        def get_x_form(form):
            for x_form in self.forms:
                if form == x_form.form:
                    return x_form
            assert Exception("not found")

        # NOTE: instance.ordered_forms DOES NOT INCLUDE DELETED FORMS ;-)
        can_order = self.formset.can_order

        # handle deleted
        delete_forms = [f for f in self.instance.forms if delete is True or f.cleaned_data.get("DELETE", False)]
        regular_forms = [f for f in self.instance.forms if f not in delete_forms]
        ordered_forms = self.instance.ordered_forms if can_order else []
        update_forms = ordered_forms if can_order else regular_forms

        # process forms to delete
        for form in delete_forms:

            # get x-form to process nested forms
            x_form = get_x_form(form)

            # delete is instance and pk
            if form.instance and form.instance.pk:
                form.instance.delete()

            # deleted nested forms
            x_form.save(commit=commit, delete=True)

        # do not continue in case of nested delete
        if delete:
            return

        for form in update_forms:
            # just make sure x-form exists for this form
            get_x_form(form)

            # check for changes
            has_changed = form.has_changed()
            if not has_changed:
                continue

            # save instance
            instance = form.save(commit=False)

            # update order
            if can_order:
                order_value = form.cleaned_data.get('ORDER')
                if order_value is not None:
                    instance.order = order_value

            # finally save instance
            instance.save()
            form.save_m2m()

        # now save the x_forms
        for x_form in self.forms:
            x_form.save(commit=commit)
