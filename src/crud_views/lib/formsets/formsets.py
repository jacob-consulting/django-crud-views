from __future__ import annotations

import re
from collections import OrderedDict
from collections import OrderedDict as OrderedDictType
from collections.abc import Iterable
from enum import Enum
from typing import Any, Self

from django.core.exceptions import BadRequest, ValidationError
from django.forms.forms import BaseForm
from django.forms.models import BaseInlineFormSet, ModelForm
from django.http.request import HttpRequest
from django.template.loader import render_to_string
from pydantic import BaseModel, Field, model_validator

from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.lazy import LazyStr
from crud_views.lib.view import CrudView

from .render_tree import XForm, XFormSet

# A row index or ``num`` in a fragment request: ASCII digits only (``str.isdigit`` would accept "²"), at most
# nine of them, so conversion never fails and no absurd index is rendered.
_FRAGMENT_INDEX = re.compile(r"[0-9]{1,9}")


def _cv_prefix_identity(instance):
    """The identity a (possibly unsaved) parent instance contributes to a formset prefix.

    An unsaved instance is ``None`` even when a default (e.g. ``uuid.uuid4``) already populated its pk, matching
    the ``None`` sentinel that ``FormSet.template`` and ``formset.js`` use for new rows. Only the prefix is
    affected; the instance keeps its pk.
    """
    if instance is None or instance._state.adding:
        return None
    return instance.pk


def _cv_fragment_index(value: str | None, name: str) -> int:
    if value is None or _FRAGMENT_INDEX.fullmatch(value) is None:
        raise BadRequest(f"{name} must be a non-negative integer")
    return int(value)


class FormSet(BaseModel, arbitrary_types_allowed=True):
    # str+Enum (not StrEnum): StrEnum changes str(member) from "PK.INT" to the value, which would
    # alter the rendered cv-data-formset-form payload — see render_tree.py:67 (str(self.parent.pk)).
    class PK(str, Enum):  # noqa: UP042
        INT = r"\d+"
        UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    key: str | None = None
    original_key: str | None = None
    title: LazyStr | None = None
    fields: list[str] | None = None
    pk_field: str | None = None
    cv_view: CrudView | None = None
    parent: Self | None = None
    klass: type[BaseInlineFormSet]
    children: dict[str, Self] = Field(default_factory=lambda: OrderedDict())
    path: str | None = None
    pk: PK = PK.INT
    form_show_labels: bool = False
    conditional: ConditionalFormSet | None = None

    def __str__(self):
        return f"FormSet({self.title})"

    __repr__ = __str__

    @model_validator(mode="after")
    def validate_formset(self) -> Self:

        from crud_views.lib.ordered import get_ordered_model

        from .inline_formset import BaseInlineFormSet

        if self.klass.can_order:
            ordered_model = get_ordered_model()
            # If django-ordered-model is not installed, skip the subclass check here;
            # crud_views.checks.check_ordered_model_installed reports the missing extra at startup.
            if ordered_model is not None and not issubclass(self.klass.model, ordered_model):
                raise ValidationError(
                    f"FormSet '{self.key}' model not a subclass of OrderedModel but formset.can_order is True"
                )

        if not issubclass(self.klass, BaseInlineFormSet):
            raise ValidationError(f"FormSet '{self.key}' klass not a subclass of BaseInlineFormSet")

        # issue #29: derive fields/pk_field from the klass when not explicitly given
        if self.fields is None:
            self.fields = list(self.klass.form.base_fields.keys())
        if self.pk_field is None:
            self.pk_field = self.klass.model._meta.pk.name

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
    def hierarchy(self) -> list[Self]:
        if self.parent is None:
            return [self.original_key]
        return [*self.parent.hierarchy, self.original_key]

    def init(
        self,
        request: HttpRequest,
        forms: list[BaseForm],
        index: int = 0,
        parent: XForm | None = None,
        parent_prefix: str | None = None,
        level: int = 0,
    ) -> Iterable[XFormSet]:
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

        for _i, form in enumerate(forms):
            prefix_key = f"{parent_prefix_}{_cv_prefix_identity(form.instance)}-{index}"
            prefix = f"{self.key}-{prefix_key}"

            kwargs = {
                "formset": self,
                "instance": form.instance,
                "prefix": prefix,
                # nested formsets (level > 0) carry their parent row's form so
                # InlineFormSet.clean() can enforce parent-presence; top-level
                # formsets attach to the view object and get None.
                "parent_form": form if level > 0 else None,
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
                management_form=formset_instance.management_form,
            )

            for formset_instance_form_index, formset_instance_form in enumerate(formset_instance.forms):
                formset_instance_form_prefix_key = f"{prefix_key}-{formset_instance_form_index}"
                x_form = XForm(
                    level=level,
                    prefix_key=formset_instance_form_prefix_key,
                    form=formset_instance_form,
                    parent=x_formset,
                )
                x_formset.forms.append(x_form)

                for child_index, (_key, child_formset) in enumerate(self.children.items()):
                    x_formsets = child_formset.init(
                        request=request,
                        forms=[x_form.form],
                        level=level + 1,
                        parent=x_form,
                        parent_prefix=formset_instance_form_prefix_key,
                        index=child_index,
                    )
                    x_form.formsets.extend(list(x_formsets))

            yield x_formset

    def template(
        self,
        pk: int | None,
        index: int,
        force_form_index: int | None = None,
        parent_prefix: str | None = None,
        level: int = 0,
        parent: XForm | None = None,
    ) -> Iterable[XFormSet]:
        """
        Similar to init, but this will be called to render the template.
        Yes, it's similar to init but not the same.
        """

        # get parent prefix with -
        parent_prefix_ = f"{parent_prefix}-" if parent_prefix else ""

        prefix_key = f"{parent_prefix_}{pk}-{index}"
        prefix = f"{self.key}-{prefix_key}"

        kwargs = {"formset": self, "prefix": prefix}
        formset_instance = self.klass(**kwargs)

        x_formset = XFormSet(
            level=level,
            prefix_key=prefix_key,
            instance=formset_instance,
            formset=self,
            parent=parent,
            management_form=formset_instance.management_form,
            render_rows_only=level == 0,
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

        for formset_instance_form_index, formset_instance_form in enumerate(forms):
            # force the form index on level 0
            form_index = force_form_index if level == 0 else formset_instance_form_index
            formset_instance_form_prefix_key = f"{prefix_key}-{form_index}"

            x_form = XForm(
                level=level,
                prefix_key=formset_instance_form_prefix_key,
                form=formset_instance_form,
                formset=self,
                parent=x_formset,
            )
            x_formset.forms.append(x_form)

            for child_index, (_key, child_formset) in enumerate(self.children.items()):
                x_formsets = child_formset.template(
                    pk=None,  # all sub-forms are new, so they have no pk
                    index=child_index,
                    level=level + 1,
                    parent=x_form,
                    parent_prefix=formset_instance_form_prefix_key,
                )
                x_form.formsets.extend(list(x_formsets))

        yield x_formset

    def is_valid(self) -> Iterable[tuple[Any, bool]]:
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
    x_formsets: list[XFormSet] = Field(default_factory=lambda: [])
    js_data: dict = Field(default_factory=lambda: {})
    scripts: bool = True

    @model_validator(mode="before")
    @classmethod
    def check_keys(cls, data: Any) -> Any:
        formsets = data.get("formsets", {})
        for key in formsets:
            if re.match(r"^[a-z\-]+$", key) is None:
                raise ValueError(f"Formset key must contain only lowercase letters and slashes, got {key}")
        return data

    @model_validator(mode="after")
    def apply_hierarchy(self) -> Self:
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

    def apply_conditional(self, main_form) -> None:
        """Set cv_active on each top-level x_formset from its conditional toggle.

        Reads the toggle from the *submitted* main form only. Nested formsets
        are out of scope and always remain active."""
        for x_formset in self.x_formsets:
            conditional = x_formset.formset.conditional
            if conditional is None:
                x_formset.cv_active = True
            else:
                x_formset.cv_active = conditional.toggle.is_on(main_form)

    def is_valid(self) -> Iterable[tuple[Any, bool]]:
        for x_formset in self.x_formsets:
            if x_formset.cv_active is False:
                continue
            yield from x_formset.is_valid()

    def all_valid(self) -> bool:
        """Return True only if every form and formset in the hierarchy is valid.

        Two-phase and order-independent: a child formset's clean() may add_error() to a
        parent form, but in a single traversal the parent's validity is collected before
        the child's clean() runs. Phase 1 triggers every clean(); phase 2 re-derives
        validity from the now-complete (shared) error state. Django's is_valid() runs
        full_clean only once, so phase 2 re-runs no clean() and does no DB work, and it
        delegates to Django's own per-formset validity (which already skips DELETE-marked
        and empty extra forms).
        """
        # Phase 1: trigger every formset's clean() (where cross-form add_error happens).
        # Discard results — collected in hierarchy order, before later cleans ran.
        list(self.is_valid())
        # Phase 2: re-collect; reflects errors added to any form during phase 1.
        return all(valid for _, valid in self.is_valid())

    def save(self, commit: bool = True):
        for x_formset in self.x_formsets:
            if x_formset.cv_active is False:
                conditional = x_formset.formset.conditional
                # purge is a destructive write — only run it when committing, and
                # delete exactly the rows the formset manages (its queryset),
                # never every child of the parent.
                if commit and conditional is not None and conditional.on_off == "purge":
                    fs = x_formset.instance  # bound model/inline formset
                    if fs.instance.pk:
                        fs.get_queryset().delete()
                continue
            x_formset.save(commit=commit)

    def init(self, request: HttpRequest, form: ModelForm):
        for _key, formset in self.items():
            x_formsets = list(formset.init(request=request, forms=[form]))
            self.x_formsets.extend(x_formsets)

    def init_js_data(self, view):
        data = {
            "path": view.request.path,
        }
        self.js_data = data

    def _cv_validate_fragment_coordinates(
        self, key_path: list[str], pk: str, num: str | None, parent_prefix: str | None, root
    ) -> tuple[str, int, str | None]:
        """Validate a fragment request against the declaration and the persisted ancestry; raise BadRequest.

        ``root`` is the endpoint's authorized object (``None`` for create). The selected formset at nesting depth
        ``n`` is owned by the row identified by ``pk`` (the immediate inline parent; the root itself at depth 0).
        Its parent prefix is the owning row's form prefix key, as rendered by ``FormSet.init``::

            {root}-0-{r0}[-{id_j}-{child_index_j}-{r_j} for j in 1..n-1]

        Each identity is ``None`` or matches its declaration's ``FormSet.PK`` grammar and converts with the owning
        model's pk field. The root must be the endpoint's own object, ``0`` is the only top-level formset index,
        every child index must be the declared position, and each saved identity must be a row of its
        declaration's model whose foreign key points at the previous identity; once an identity is ``None`` all
        deeper ones must be ``None``. Row indices are any non-negative integers (client-added rows exist only in
        the browser). A top-level formset takes no parent prefix. Read-only: ancestry is checked with ``exists()``
        on every request.

        Returns the canonical ``(pk, num, parent_prefix)`` passed to ``get_template``.

        Note: ``get_template`` still emits index 0 for the selected formset itself, so a fragment of a non-first
        child declaration does not extend that formset's initialized prefix (known limitation, A19).
        """
        chain: list[FormSet] = []
        node = None
        for level, key in enumerate(key_path):
            node = self.get(key) if level == 0 else node.children.get(key)
            if node is None:
                raise BadRequest(f"unknown formset template {'|'.join(key_path)}")
            chain.append(node)
        num_ = _cv_fragment_index(num, "num")
        depth = len(chain) - 1

        # parent prefix structure: identities, declared child indices and row indices
        tokens: list[str] = []
        child_indices: list[int] = []
        rows: list[int] = []
        if depth == 0:
            if parent_prefix:
                raise BadRequest("a top-level formset takes no formset parent prefix")
        else:
            if not parent_prefix:
                raise BadRequest("a nested formset requires its formset parent prefix")
            match = self._cv_parent_prefix_pattern(chain).fullmatch(parent_prefix)
            if match is None:
                raise BadRequest("formset parent prefix does not match the declared formset path")
            groups = match.groups()
            for j in range(depth):
                identity_token, child, row = groups[3 * j : 3 * j + 3]
                declared = 0 if j == 0 else list(chain[j - 1].children).index(key_path[j])
                if _cv_fragment_index(child, "formset index") != declared:
                    raise BadRequest("formset parent prefix does not match the declared formset path")
                tokens.append(identity_token)
                child_indices.append(declared)
                rows.append(_cv_fragment_index(row, "row index"))
        if re.fullmatch(rf"None|{chain[depth].pk.value}", pk or "", re.ASCII) is None:
            raise BadRequest("pk does not match the declared formset primary key")
        tokens.append(pk)

        # identities: the endpoint root, then persisted foreign-key ancestry
        values: list = []
        for j, token in enumerate(tokens):
            if j == 0:
                expected = _cv_prefix_identity(root)
                if token == "None":
                    value = None
                elif expected is None:
                    raise BadRequest("formset root does not match the requested object")
                else:
                    value = self._cv_fragment_pk(type(root), token)
                if value != expected:
                    raise BadRequest("formset root does not match the requested object")
            elif token == "None":
                value = None
            elif values[j - 1] is None:
                raise BadRequest("a saved formset parent cannot belong to an unsaved one")
            else:
                owner = chain[j - 1].klass
                value = self._cv_fragment_pk(owner.model, token)
                ancestry = {"pk": value, f"{owner.fk.name}__pk": values[j - 1]}
                if not owner.model._default_manager.filter(**ancestry).exists():
                    raise BadRequest("formset parent does not belong to the requested ancestry")
            values.append(value)

        def canonical(value) -> str:
            return "None" if value is None else str(value)

        prefix_out = None
        if depth:
            prefix_out = "-".join(f"{canonical(values[j])}-{child_indices[j]}-{rows[j]}" for j in range(depth))
        return canonical(values[-1]), num_, prefix_out

    @staticmethod
    def _cv_parent_prefix_pattern(chain: list[FormSet]) -> re.Pattern:
        """``{root}-{index}-{row}`` then ``-{identity}-{child index}-{row}`` per intermediate level; each identity
        is ``None`` or its declaration's pk grammar (UUID hyphens are part of the grammar, never a separator)."""
        parts = []
        for formset in chain[:-1]:
            parts.append(rf"(None|{formset.pk.value})-([0-9]+)-([0-9]+)")
        return re.compile("-".join(parts), re.ASCII)

    @staticmethod
    def _cv_fragment_pk(model, token: str):
        field = model._meta.pk
        try:
            value = field.to_python(token)
            field.run_validators(value)
        except ValidationError as exc:
            raise BadRequest("invalid formset parent identity") from exc
        return value

    def get_template(self, key_path: list[str], pk: int, num: int, parent_prefix=None):
        formset = None
        for level, key in enumerate(key_path):
            formset = self.get(key) if level == 0 else formset.children[key]

        x_formsets = list(formset.template(index=0, parent_prefix=parent_prefix, force_form_index=num, pk=pk))
        assert len(x_formsets) == 1
        x_formset = x_formsets[0]
        data = {"x_formset": x_formset}

        rows = [form.prefix for form in x_formset.forms]
        html = render_to_string("crud_views/formsets/formset.html", data)
        data = {"rows": rows, "html": html}
        return data

    def clone(self, cv_view: CrudView) -> Self:
        formsets = self.model_copy(deep=True)
        formsets.cv_view = cv_view
        for _key, formset in formsets.items():
            formset.patch(cv_view)
        return formsets
