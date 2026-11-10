"""
Render tree for (nested) inline formsets.

When a view with formsets renders, the declarative FormSet hierarchy
(crud_views.lib.formsets.formsets.FormSet) is instantiated into a tree of
runtime nodes that the templates iterate over:

- ``XFormSet`` wraps one bound/unbound Django formset instance: it knows its
  unique prefix within the nested hierarchy, its level, layout helpers
  (columns), and the JSON payload the JavaScript needs to add/remove rows.
- ``XForm`` wraps one form (row) of an XFormSet and holds the child
  XFormSets nested under that row.

``FormSet.init()`` builds this tree for a request (recursively for all
children); ``FormSet.template()`` builds a single-branch tree used to render
the empty-row template returned by the AJAX endpoint. ``save()``/``is_valid()``
walk the tree depth-first, handling deletes before updates.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from functools import cached_property
from typing import Any

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, Field

from crud_views.lib.exceptions import CrudViewError

from .compact import _compact_helper, _compact_projection

try:
    from polymorphic.formsets import BasePolymorphicInlineFormSet
except ImportError:
    BasePolymorphicInlineFormSet = None


class XForm(BaseModel, arbitrary_types_allowed=True):
    level: int
    prefix_key: str
    form: BaseForm
    parent: XFormSet | None = None
    formsets: list[XFormSet] = Field(default_factory=lambda: [])

    def __str__(self):
        return f"XForm(prefix={self.prefix},prefix_key={self.prefix_key},key={self.key},level={self.level})"

    __repr__ = __str__

    @property
    def key(self) -> str:
        """return the formset key from the parent formset"""
        return self.parent.key

    @property
    def prefix(self) -> str:
        """return the form prefix"""
        return self.form.prefix

    @property
    def data(self) -> dict:
        return {
            "key": self.key,
            "prefix": self.prefix,
            "prefix_key": self.prefix_key,
            "formset_prefix": self.parent.prefix,
            "pk": str(self.parent.pk),
        }

    @property
    def json_data(self) -> str:
        return json.dumps(self.data)  # .replace('"', "'")

    def is_valid(self) -> Iterable[tuple[Any, bool]]:
        for x_formset in self.formsets:
            yield from x_formset.is_valid()

    def save(self, commit: bool = True, delete: bool = False):
        for x_formset in self.formsets:
            x_formset.save(commit=commit, delete=delete)

    @property
    def helper(self):
        if self.parent.formset.compact_layout is not None:
            return _compact_helper(self)
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
    cv_active: bool = True
    cv_bound_toggle_field: str = ""
    instance: BaseFormSet
    management_form: Any
    forms: list[XForm] = Field(default_factory=lambda: [])
    parent: XForm | None = None
    render_rows_only: bool = False  # True for the AJAX row template: skip the fieldset wrapper

    @cached_property
    def compact_columns(self):
        if self.formset.compact_layout is None:
            return ()
        if BasePolymorphicInlineFormSet and issubclass(self.formset.klass, BasePolymorphicInlineFormSet):
            raise ImproperlyConfigured(f"FormSet '{self.key}': compact polymorphic formsets are unsupported")
        return _compact_projection(self)

    def __str__(self):
        return f"XFormSet({self.prefix},{self.prefix_key},{self.level})"

    __repr__ = __str__

    @property
    def has_parent(self) -> bool:
        return self.parent is not None

    @property
    def key(self) -> str:
        """return the formset key"""
        return self.formset.key

    @property
    def pk(self) -> str:
        """return the formset key"""
        return self.formset.pk

    @property
    def prefix(self) -> str:
        """return the formset prefix KEY-SUFFIX"""
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
    def hierarchy(self) -> list[str]:
        return self.formset.hierarchy

    @property
    def hierarchy_str(self) -> str:
        return "|".join(self.hierarchy)

    @property
    def title(self) -> str:
        return self.formset.title

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
        return {
            "key": self.key,
            "prefix": self.prefix,
            "prefix_key": self.prefix_key,
            "hierarchy": self.hierarchy,
            "parent_prefix": self.parent_prefix,
            "parent_prefix_key": self.parent_prefix_key,
            "can_delete": self.formset.can_delete,
            "can_delete_extra": self.formset.can_delete_extra,
            "can_order": self.formset.can_order,
            "edit_only": self.formset.edit_only,
            "path": self.formset.path,
            "fields": self.formset.fields,
            "pk_field": self.formset.pk_field,
            "pk": self.pk.value,
        }

    @property
    def json_data(self) -> str:
        return json.dumps(self.data)

    @property
    def cv_toggle_field(self) -> str:
        return self.cv_bound_toggle_field

    def is_valid(self) -> Iterable[tuple[Any, bool]]:
        valid = self.instance.is_valid()
        self._cv_validate_row_policy()
        yield self, valid and not self.instance.non_form_errors()
        for x_form in self.forms:
            yield from x_form.is_valid()

    def _cv_validate_row_policy(self):
        """Enforce row capabilities for every accepted inline formset class.

        Run after normal Django/custom cleaning on every traversal, including
        on DELETE-marked rows: full_clean() can replace the native error cache.
        Inactive top-level trees never enter this validation traversal.
        """
        if not self.instance.is_bound:
            return
        if not self.instance.management_form.is_valid():
            return
        initial = self.instance.initial_form_count()
        total = self.instance.management_form.cleaned_data["TOTAL_FORMS"]
        invalid_row = not 0 <= initial <= total
        pk_field = self.instance.model._meta.pk
        queryset = self.instance.get_queryset()
        # Evaluate the managed queryset on its own selected alias. Never consult
        # the PK ModelChoiceField, whose queryset may include unrelated rows.
        authorized_ids = set(queryset.values_list("pk", flat=True))
        for index, row in enumerate(self.forms):
            form = row.form
            raw_pk = form.data.get(form.add_prefix(pk_field.name))
            persisted = not form.instance._state.adding
            if index < initial or raw_pk not in (None, "") or persisted:
                try:
                    submitted_pk = pk_field.to_python(raw_pk)
                except (ValidationError, ValueError, TypeError):
                    invalid_row = True
                    continue
                if (
                    submitted_pk is None
                    or submitted_pk not in authorized_ids
                    or not persisted
                    or submitted_pk != form.instance.pk
                ):
                    invalid_row = True
        if invalid_row:
            self._cv_add_policy_error("cv_invalid_row", _("Invalid row."))
        if self.formset.edit_only:
            extras = self.forms[initial:]
            if any(self._cv_row_has_data(row) for row in extras):
                self._cv_add_policy_error("cv_additions_not_allowed", _("Additions are not allowed."))

    @staticmethod
    def _cv_row_has_data(row):
        # A nested-only addition is still an addition to this extra parent.
        # has_changed includes DELETE even where Django ignores deleted forms.
        return row.form.has_changed() or any(
            XFormSet._cv_row_has_data(child_row) for child in row.formsets for child_row in child.forms
        )

    def _cv_add_policy_error(self, code, message):
        errors = self.instance.non_form_errors()
        if not any(error.code == code for error in errors.as_data()):
            errors.append(ValidationError(message, code=code))

    def _get_x_form(self, form):
        for x_form in self.forms:
            if form == x_form.form:
                return x_form
        raise CrudViewError(f"no XForm found for form with prefix {form.prefix} at {self}")

    def _delete_form(self, form, commit: bool):
        # get x-form to process nested forms
        x_form = self._get_x_form(form)

        # delete is instance and pk
        if form.instance and form.instance.pk:
            form.instance.delete()

        # deleted nested forms
        x_form.save(commit=commit, delete=True)

    @staticmethod
    def _save_changed_form(form, can_order: bool):
        # save instance
        instance = form.save(commit=False)

        # update order
        order_value = form.cleaned_data.get("ORDER") if can_order else None
        if order_value is not None:
            instance.order = order_value

        # finally save instance
        instance.save()
        form.save_m2m()

    def save(self, commit: bool = True, delete=False):
        """
        Nested save and delete
        """
        # NOTE: instance.ordered_forms DOES NOT INCLUDE DELETED FORMS ;-)
        can_order = self.formset.can_order

        # handle deleted
        delete_forms = [f for f in self.instance.forms if delete is True or f.cleaned_data.get("DELETE", False)]
        regular_forms = [f for f in self.instance.forms if f not in delete_forms]
        update_forms = self.instance.ordered_forms if can_order else regular_forms

        # process forms to delete
        for form in delete_forms:
            self._delete_form(form, commit)

        # do not continue in case of nested delete
        if delete:
            return

        for form in update_forms:
            # just make sure x-form exists for this form
            self._get_x_form(form)
            conditional_change = (
                not form.instance._state.adding
                and not form.errors
                and getattr(form, "_cv_conditional_requires_save", False)
            )
            if form.has_changed() or conditional_change:
                self._save_changed_form(form, can_order)

        # now save the x_forms
        for x_form in self.forms:
            x_form.save(commit=commit)
